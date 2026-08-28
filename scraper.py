"""
iFood Order History Scraper
────────────────────────────
Na primeira execução abre um Chromium e pede para você fazer login no iFood.
A sessão fica salva em ./chrome_profile/ — execuções seguintes já estão logadas.

Usage:
    python scraper.py          # abre janela, faz login na 1ª vez, scrapa
    python scraper.py --headless  # sem janela (só funciona após login salvo)
"""

import argparse
import asyncio
import json
import logging
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import Page, async_playwright

from database import Database

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

IFOOD_ORDERS_URL  = "https://www.ifood.com.br/pedidos"
REQUEST_DELAY     = 1.5   # segundos entre ações de scroll/clique
MAX_STALL_ROUNDS  = 5     # para após N rodadas sem pedidos novos
CDP_PORT          = 9222  # porta de debug do Chrome real

# Perfil local dedicado — sessão fica salva entre execuções
LOCAL_PROFILE = Path("./chrome_profile").resolve()


def chrome_profile_for(name: str) -> Path:
    """Diretório de perfil do Chrome por pessoa. 'default' usa ./chrome_profile."""
    if not name or name.lower() == "default":
        return LOCAL_PROFILE
    safe = "".join(c for c in name if c.isalnum() or c in "-_").lower()
    return (Path("./profiles") / safe).resolve()

# Caminhos do Chrome REAL por sistema (necessário p/ passar no Cloudflare)
_CHROME_BINARIES = {
    "darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ],
    "linux": [
        "google-chrome", "google-chrome-stable",
        "chromium-browser", "chromium",
    ],
    "win32": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
}

DAY_LABELS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


# ── Scraper ───────────────────────────────────────────────────────────────────

class IFoodScraper:
    def __init__(self, profile_path: str = None, headless: bool = False,
                 profile_name: str = "default", auto: bool = False):
        self.profile_name = profile_name or "default"
        self.db = Database(profile=self.profile_name)
        self.headless = headless
        self.auto = auto  # modo não-interativo (disparado pelo dashboard)
        # Perfil de navegador isolado por pessoa (sessão iFood separada)
        self.profile_path = (
            Path(profile_path).resolve() if profile_path
            else chrome_profile_for(self.profile_name)
        )
        self._api_orders: dict[str, dict] = {}  # id → raw API data
        self._seen_endpoints: dict[str, int] = {}  # url → nº pedidos extraídos (debug)
        self._chrome_proc: subprocess.Popen | None = None
        self.chrome_binary: str | None = None  # override opcional via --chrome

    # ── Browser setup ────────────────────────────────────────────────────────

    def _find_chrome_binary(self) -> str | None:
        if self.chrome_binary and Path(self.chrome_binary).exists():
            return self.chrome_binary
        for candidate in _CHROME_BINARIES.get(sys.platform, []):
            if Path(candidate).exists():
                return candidate
            found = shutil.which(candidate)
            if found:
                return found
        return None

    def _start_real_chrome(self) -> bool:
        """
        Sobe o Chrome REAL com porta de debug. Como NÃO é o Playwright que
        lança o browser, navigator.webdriver fica false → passa no Cloudflare.
        """
        chrome = self._find_chrome_binary()
        if not chrome:
            log.error(
                "❌ Google Chrome não encontrado. Instale o Chrome ou passe "
                "--chrome /caminho/para/chrome"
            )
            return False

        self.profile_path.mkdir(parents=True, exist_ok=True)
        args = [
            chrome,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={self.profile_path}",
            "--no-first-run",
            "--no-default-browser-check",
            "--lang=pt-BR",
            IFOOD_ORDERS_URL,
        ]
        if self.headless:
            args.insert(1, "--headless=new")

        log.info(f"Iniciando Chrome real: {chrome}")
        self._chrome_proc = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return self._wait_for_cdp()

    @staticmethod
    def _wait_for_cdp(timeout: float = 30.0) -> bool:
        """Aguarda o endpoint CDP do Chrome ficar disponível."""
        import time
        deadline = time.time() + timeout
        url = f"http://localhost:{CDP_PORT}/json/version"
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                time.sleep(0.5)
        log.error(f"❌ Chrome não respondeu na porta {CDP_PORT}.")
        return False

    async def _connect(self, playwright):
        """Conecta o Playwright ao Chrome real já em execução (via CDP)."""
        if not self._start_real_chrome():
            return None
        browser = await playwright.chromium.connect_over_cdp(
            f"http://localhost:{CDP_PORT}"
        )
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        log.info("✅ Playwright conectado ao Chrome real via CDP.")
        return ctx

    def _cleanup_chrome(self):
        if self._chrome_proc and self._chrome_proc.poll() is None:
            self._chrome_proc.terminate()
            try:
                self._chrome_proc.wait(timeout=5)
            except Exception:
                self._chrome_proc.kill()

    # ── Network interception ─────────────────────────────────────────────────

    async def _on_response(self, response):
        """Intercept JSON responses that look like order data."""
        try:
            ct = response.headers.get("content-type", "")
            if response.status != 200 or "json" not in ct:
                return
            url = response.url
            data = await response.json()

            before = len(self._api_orders)
            self._parse_api_response(data, url)
            added = len(self._api_orders) - before

            # Debug: registra todo endpoint JSON e quantos pedidos rendeu
            short = url.split("?")[0]
            if short not in self._seen_endpoints:
                self._seen_endpoints[short] = added
                marker = f"  ⭐ +{added} pedidos" if added else ""
                log.debug(f"  [JSON] {short}{marker}")
            elif added:
                self._seen_endpoints[short] += added
        except Exception:
            pass

    def _parse_api_response(self, data, url: str, depth: int = 0):
        """Percorre recursivamente o JSON procurando objetos que pareçam pedidos."""
        if depth > 6:
            return
        if isinstance(data, list):
            for item in data:
                self._parse_api_response(item, url, depth + 1)
            return
        if not isinstance(data, dict):
            return
        # Este dict é um pedido?
        self._try_ingest(data)
        # Continua descendo (pode haver pedidos aninhados em qualquer chave)
        for val in data.values():
            if isinstance(val, (list, dict)):
                self._parse_api_response(val, url, depth + 1)

    @staticmethod
    def _looks_like_order(raw: dict) -> bool:
        """Heurística: tem id E (restaurante OU itens OU valores de pedido)."""
        has_id = any(k in raw for k in ("id", "orderId", "uuid", "orderUuid"))
        if not has_id:
            return False
        signals = (
            "merchant", "restaurant", "merchantName", "restaurantName",
            "items", "orderItems", "products",
            "total", "pricing", "orderAmount", "createdAt", "orderedAt",
            "lastStatus", "orderStatus",
        )
        return any(k in raw for k in signals)

    def _try_ingest(self, raw: dict):
        if not isinstance(raw, dict) or not self._looks_like_order(raw):
            return
        oid = (
            raw.get("id") or raw.get("orderId")
            or raw.get("uuid") or raw.get("orderUuid")
        )
        if not oid:
            return
        oid = str(oid)
        existing = self._api_orders.get(oid)
        if existing is None:
            self._api_orders[oid] = raw
        else:
            # Mescla: prefere a versão com mais campos (detalhe > resumo)
            if len(raw) > len(existing):
                existing.update(raw)

    # ── Page interactions ────────────────────────────────────────────────────

    async def _safe_eval(self, page: Page, expr: str, default=None):
        """
        page.evaluate() que não derruba a coleta.

        Duas falhas reais já aconteceram aqui: a página navegar no meio da
        avaliação ("Execution context was destroyed") e a janela do Chrome ser
        fechada ("Target page, context or browser has been closed"). A primeira
        é transitória e basta repetir; a segunda não tem o que tentar — devolve
        o default para o scraper seguir e gravar o que já coletou.
        """
        for tentativa in (1, 2):
            try:
                return await page.evaluate(expr)
            except Exception as e:
                motivo = str(e).splitlines()[0]
                if "closed" in motivo.lower():
                    log.warning("⚠ Janela do Chrome fechada — seguindo com o que já foi coletado.")
                    return default
                if tentativa == 1:
                    log.warning(f"⚠ Contexto perdido (navegação?); tentando de novo: {motivo}")
                    await asyncio.sleep(1.5)
                    continue
                log.warning(f"⚠ Persistiu o erro, seguindo sem este passo: {motivo}")
        return default

    async def _scroll_and_wait(self, page: Page) -> bool:
        # default 0 nos dois lados: se a página sumiu, new > old é falso e o
        # laço de scroll encerra em vez de estourar exceção.
        old = await self._safe_eval(page, "document.body.scrollHeight", 0)
        await self._safe_eval(page, "window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(REQUEST_DELAY)
        new = await self._safe_eval(page, "document.body.scrollHeight", 0)
        return new > old

    async def _click_load_more(self, page: Page) -> bool:
        selectors = [
            "button:has-text('Ver mais pedidos')",
            "button:has-text('Carregar mais')",
            "button:has-text('Ver mais')",
            "button:has-text('Load more')",
            "[data-test-id='load-more']",
            "[class*='load-more']",
            "[class*='loadMore']",
        ]
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=800):
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await asyncio.sleep(REQUEST_DELAY)
                    return True
            except Exception:
                continue
        return False

    async def _load_all_orders(self, page: Page):
        log.info("Scrolling / clicking to load full order history…")
        stall = 0
        iteration = 0
        while stall < MAX_STALL_ROUNDS:
            iteration += 1
            before = len(self._api_orders)
            await self._click_load_more(page)
            await self._scroll_and_wait(page)
            after = len(self._api_orders)
            log.info(f"  Round {iteration}: {after} orders captured")
            if after > before:
                stall = 0
            else:
                stall += 1
        log.info(f"Loading complete. {len(self._api_orders)} orders captured via API.")

    # ── Enriquecimento de detalhe (preventivo) ────────────────────────────────

    def _is_incomplete(self, raw: dict) -> bool:
        """Pedido sem itens ou sem total → precisa buscar detalhe."""
        n = self._normalize(raw)
        if not n:
            return True
        return n["total"] <= 0 or len(n["items"]) == 0

    async def _enrich_details(self, page: Page):
        """
        Rede de segurança: para cada pedido cujo payload da listagem veio
        incompleto, abre a página de detalhe do pedido. A navegação dispara a
        chamada de API de detalhe, que o listener (_on_response) captura e
        mescla em _api_orders pelo mesmo id.
        """
        incomplete = [
            oid for oid, raw in self._api_orders.items()
            if self._is_incomplete(raw)
        ]
        if not incomplete:
            log.info("Todos os pedidos vieram completos na listagem — sem detalhe extra.")
            return

        log.info(f"🔎 {len(incomplete)} pedidos incompletos — buscando detalhe individual…")
        for i, oid in enumerate(incomplete, 1):
            for url in (
                f"https://www.ifood.com.br/pedido/{oid}",
                f"https://www.ifood.com.br/pedidos/{oid}",
            ):
                try:
                    await page.goto(url, wait_until="networkidle", timeout=20_000)
                    await asyncio.sleep(REQUEST_DELAY)
                    if not self._is_incomplete(self._api_orders.get(oid, {})):
                        break  # já completou
                except Exception:
                    continue
            status = "ok" if not self._is_incomplete(self._api_orders.get(oid, {})) else "ainda incompleto"
            log.info(f"  [{i}/{len(incomplete)}] {oid} → {status}")
            await asyncio.sleep(REQUEST_DELAY)

    # ── DOM fallback ─────────────────────────────────────────────────────────

    async def _dom_order_ids(self, page: Page) -> list[str]:
        # Fallback opcional: se falhar, a coleta via API já foi persistida.
        return await self._safe_eval(page, """
        () => {
            const ids = new Set();
            document.querySelectorAll('a[href*="/pedidos/"]').forEach(a => {
                const m = a.href.match(/\\/pedidos\\/([\\w-]{8,})/i);
                if (m) ids.add(m[1]);
            });
            document.querySelectorAll('[data-order-id],[data-id],[data-testid*="order"]').forEach(el => {
                const id = el.dataset.orderId || el.dataset.id;
                if (id && id.length > 6) ids.add(id);
            });
            return [...ids];
        }
        """, []) or []

    async def _dom_scrape_detail(self, page: Page, order_id: str) -> dict | None:
        url = f"https://www.ifood.com.br/pedidos/{order_id}"
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await asyncio.sleep(1.2)
        except Exception as e:
            log.warning(f"  Could not load {url}: {e}")
            return None

        result = await page.evaluate("""
        () => {
            const tx = sel => {
                const els = [...document.querySelectorAll(sel)];
                return els.map(e => e.textContent.trim()).filter(Boolean);
            };
            const first = sel => tx(sel)[0] || '';
            const num = s => {
                const m = s.replace(/\\./g,'').replace(',','.').match(/[\\d.]+/);
                return m ? parseFloat(m[0]) : 0;
            };

            // Restaurant name
            const restaurant =
                first('[class*="merchant-name"],[class*="restaurant-name"],h1,h2');

            // Date/time
            const date = first('[class*="date"],[class*="data-hora"],time');

            // Status
            const status = first('[class*="status"],[class*="label"][class*="order"]');

            // Items: try various list item patterns
            const itemEls = document.querySelectorAll(
                '[class*="order-item"],[class*="item-row"],[class*="dish"],[class*="product-item"]'
            );
            const items = [...itemEls].map(el => ({
                name:      (el.querySelector('[class*="name"],[class*="title"]') || el)
                               .textContent.replace(/\\d+x/,'').trim(),
                quantity:  (() => {
                    const q = el.querySelector('[class*="qty"],[class*="quantity"],[class*="amount"]');
                    return q ? parseInt(q.textContent) || 1 : 1;
                })(),
                unit_price: num(
                    (el.querySelector('[class*="price"],[class*="valor"]') || { textContent: '0' })
                    .textContent
                ),
                subtotal: 0,
            })).filter(i => i.name.length > 1);

            // Pricing rows
            const priceRows = {};
            document.querySelectorAll('[class*="summary-row"],[class*="price-row"],[class*="total-row"]')
                .forEach(row => {
                    const label = (row.querySelector('[class*="label"],[class*="title"]') || row)
                        .textContent.toLowerCase();
                    const val = num(
                        (row.querySelector('[class*="value"],[class*="price"]') || row).textContent
                    );
                    if (label.includes('entrega') || label.includes('delivery')) priceRows.delivery = val;
                    else if (label.includes('serviço') || label.includes('service')) priceRows.service = val;
                    else if (label.includes('cupom') || label.includes('desconto')) priceRows.discount = val;
                    else if (label.includes('total')) priceRows.total = val;
                    else if (label.includes('subtotal')) priceRows.subtotal = val;
                });

            return { restaurant, date, status, items, ...priceRows };
        }
        """)

        if not result or not result.get("restaurant"):
            return None
        return result

    # ── Normalization ────────────────────────────────────────────────────────

    def _normalize(self, raw: dict) -> dict | None:
        """
        Normaliza um pedido no schema REAL da API do iFood.
        Valores monetários da API vêm em CENTAVOS → divididos por 100.
        Estrutura: {id, merchant{name}, createdAt, lastStatus,
                    bag{subTotal, deliveryFee, total, items[], benefits[]},
                    fees[], payments{total}}
        """
        oid = raw.get("id") or raw.get("orderId") or raw.get("uuid")
        if not oid:
            return None
        oid = str(oid)

        restaurant = _dig(raw, "merchant.name") or "Desconhecido"
        category = _category(_dig(raw, "merchant.type"))
        ordered_at = _parse_ts(raw.get("createdAt") or raw.get("closedAt"))
        status = _norm_status(raw.get("lastStatus") or "UNKNOWN")

        bag = raw.get("bag") if isinstance(raw.get("bag"), dict) else {}

        # ── Valores (centavos → reais) ──────────────────────────────────────
        subtotal = _cents(_dig(bag, "subTotal.value"))

        # Entrega: o que foi efetivamente pago (valueWithDiscount)
        delivery_full = _cents(_dig(bag, "deliveryFee.value"))
        delivery_paid = _dig(bag, "deliveryFee.valueWithDiscount")
        delivery_fee = _cents(delivery_paid) if delivery_paid is not None else delivery_full

        # Taxa de serviço: soma das fees cujo título menciona "serviço"
        service_fee = 0.0
        for fee in raw.get("fees") or []:
            if not isinstance(fee, dict):
                continue
            title = (fee.get("title") or "").lower()
            if "serviç" in title or "service" in title:
                service_fee += _cents(_dig(fee, "amount.value"))

        # Total pago: payments.total é autoritativo; fallback bag.total
        total = _cents(_dig(raw, "payments.total.value"))
        if total == 0:
            total = _cents(
                _dig(bag, "total.valueWithDiscount") or _dig(bag, "total.value")
            )

        # Desconto de cupom = vouchers aplicados ao carrinho.
        # (O frete grátis NÃO entra aqui — já reflete em delivery_fee=0,
        #  caso contrário a economia de entrega seria contada em dobro e a
        #  reconciliação subtotal-cupom+entrega+serviço=total quebraria.)
        coupon_discount = 0.0
        for ben in bag.get("benefits") or []:
            if not isinstance(ben, dict):
                continue
            if (ben.get("type") or "").upper() == "VOUCHER":
                coupon_discount += _cents(ben.get("value"))

        # ── Itens ───────────────────────────────────────────────────────────
        items = []
        for it in bag.get("items") or []:
            if not isinstance(it, dict):
                continue
            name = it.get("name") or it.get("description") or "Item"
            qty  = int(it.get("quantity") or 1)
            unit = _cents(it.get("unitPrice") or it.get("unitPriceWithDiscount"))
            sub  = _cents(
                it.get("totalPriceWithDiscount")
                if it.get("totalPriceWithDiscount") is not None
                else it.get("totalPrice")
            )
            if sub == 0 and unit:
                sub = unit * qty
            items.append({"name": name, "quantity": qty, "unit_price": unit, "subtotal": sub})

        # ── Campos derivados ────────────────────────────────────────────────
        year = month = dow = hour = time_slot = None
        if ordered_at:
            year, month = ordered_at.year, ordered_at.month
            dow, hour = ordered_at.weekday(), ordered_at.hour
            time_slot = _time_slot(hour)
        price_range = _price_range(total)

        return {
            "id": oid,
            "restaurant_name": restaurant,
            "category": category,
            "ordered_at": ordered_at.isoformat() if ordered_at else None,
            "status": status,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "service_fee": service_fee,
            "coupon_discount": coupon_discount,
            "total": total,
            "year": year,
            "month": month,
            "day_of_week": dow,
            "hour": hour,
            "time_slot": time_slot,
            "price_range": price_range,
            "items": items,
        }

    def _from_dom(self, oid: str, d: dict) -> dict:
        ordered_at = _parse_ts(d.get("date"))
        total = d.get("total", 0)
        year = month = dow = hour = None
        if ordered_at:
            year, month, dow, hour = (
                ordered_at.year, ordered_at.month,
                ordered_at.weekday(), ordered_at.hour,
            )
        return {
            "id": oid,
            "restaurant_name": d.get("restaurant") or "Unknown",
            "ordered_at": ordered_at.isoformat() if ordered_at else None,
            "status": _norm_status(d.get("status") or "UNKNOWN"),
            "subtotal": d.get("subtotal", 0),
            "delivery_fee": d.get("delivery", 0),
            "service_fee": d.get("service", 0),
            "coupon_discount": d.get("discount", 0),
            "total": total,
            "year": year,
            "month": month,
            "day_of_week": dow,
            "hour": hour,
            "time_slot": _time_slot(hour) if hour is not None else None,
            "price_range": _price_range(total),
            "items": [
                {"name": i["name"], "quantity": i["quantity"],
                 "unit_price": i["unit_price"], "subtotal": i["unit_price"] * i["quantity"]}
                for i in d.get("items", [])
            ],
        }

    # ── Main ─────────────────────────────────────────────────────────────────

    @staticmethod
    async def _wait_for_enter(prompt: str):
        """Pausa o loop async aguardando ENTER no terminal, sem travar o event loop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: input(prompt))

    async def _auto_wait_ready(self, page: Page, timeout: float = 240.0):
        """
        Modo automático (dashboard): aguarda os pedidos carregarem por polling,
        sem ENTER. Se houver captcha, espera o humano resolver na janela do Chrome.
        Pronto quando: fora de captcha/login E pedidos capturados (ou DOM com IDs).
        """
        import time
        deadline = time.time() + timeout
        warned_block = False
        while time.time() < deadline:
            url = page.url.lower()
            blocked = any(x in url for x in ("login", "entrar", "captcha", "challenge"))
            if blocked:
                if not warned_block:
                    log.info("⏳ Aguardando você resolver captcha/login na janela do Chrome…")
                    warned_block = True
                await asyncio.sleep(2)
                continue
            # Fora de bloqueio: rola um pouco para disparar as chamadas de API
            await self._scroll_and_wait(page)
            if self._api_orders:
                log.info(f"✅ Pedidos detectados ({len(self._api_orders)}). Iniciando coleta…")
                return True
            dom_ids = await self._dom_order_ids(page)
            if dom_ids:
                log.info(f"✅ {len(dom_ids)} pedidos no DOM. Iniciando coleta…")
                return True
            await asyncio.sleep(2)
        log.warning("⏰ Tempo esgotado aguardando pedidos. Seguindo com o que houver.")
        return False

    async def run(self):
        self.db.init()
        async with async_playwright() as p:
            ctx = await self._connect(p)
            if ctx is None:
                return
            try:
                await self._scrape(ctx)
            finally:
                self._cleanup_chrome()

    async def _scrape(self, ctx):
            # O Chrome real já abriu em /pedidos. Pega a aba ativa.
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            # Interceptação ATIVA desde o início — captura tudo que rolar na sessão
            page.on("response", self._on_response)
            await asyncio.sleep(2)

            # ── Espera os pedidos carregarem ──────────────────────────────────
            if self.auto:
                # Modo dashboard: aguarda automaticamente (humano resolve captcha na janela)
                log.info("Modo automático: aguardando pedidos carregarem…")
                log.info("(Se aparecer captcha, resolva na janela do Chrome que abriu.)")
                await self._auto_wait_ready(page)
            else:
                # Modo terminal: pausa manual
                log.info("\n" + "=" * 64)
                log.info("👋 AÇÃO MANUAL NECESSÁRIA na janela do navegador:")
                log.info("   1. Se aparecer captcha ('Não sou um robô'), resolva.")
                log.info("   2. Se pedir login, faça login normalmente.")
                log.info("   3. Confirme que a LISTA DE PEDIDOS está visível na tela.")
                log.info("   4. Volte AQUI no terminal e pressione ENTER.")
                log.info("=" * 64 + "\n")
                await self._wait_for_enter(">>> Pressione ENTER quando os pedidos estiverem na tela… ")
                if any(x in page.url.lower() for x in ("login", "entrar", "captcha", "challenge")):
                    log.warning(f"⚠ Ainda em página de bloqueio: {page.url}")
                    await self._wait_for_enter(">>> Resolva e pressione ENTER de novo… ")

            await self._load_all_orders(page)

            # Enriquecimento preventivo: busca detalhe de pedidos incompletos
            await self._enrich_details(page)

            # Dump de amostra crua para diagnóstico de mapeamento de campos
            if self._api_orders:
                sample = list(self._api_orders.values())[:5]
                dump_path = Path(f"data/raw_sample_{self.profile_name}.json")
                dump_path.write_text(
                    json.dumps(sample, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                log.info(f"🔍 Amostra crua salva em {dump_path} ({len(sample)} pedidos)")

            # Diagnóstico: se nada veio da API, mostra os endpoints vistos
            if not self._api_orders:
                log.warning("\n⚠ Nenhum pedido capturado via API. Endpoints JSON vistos:")
                for ep, n in sorted(self._seen_endpoints.items(), key=lambda x: -x[1]):
                    log.warning(f"     {n:>4} pedidos  ←  {ep}")
                log.warning(
                    "\n   Se algum endpoint acima parece ter os pedidos, me mande a URL.\n"
                    "   Tentando fallback por DOM…"
                )

            # Salva/atualiza todos os pedidos (upsert — corrige existentes).
            # ANTES do fallback de DOM de propósito: aquele passo depende da
            # página continuar viva, e uma janela fechada ali já fez perder
            # 81 pedidos que estavam só na memória.
            saved = updated = 0
            for raw in self._api_orders.values():
                order = self._normalize(raw)
                if not order:
                    continue
                if self.db.order_exists(order["id"]):
                    updated += 1
                else:
                    saved += 1
                self.db.save_order(order)
            log.info(f"Persistidos: {saved} novos, {updated} atualizados")

            # DOM fallback for IDs missed by API interception
            dom_ids = await self._dom_order_ids(page)
            missing = [
                oid for oid in dom_ids
                if oid not in self._api_orders and not self.db.order_exists(oid)
            ]
            log.info(f"DOM encontrou {len(dom_ids)} IDs; {len(missing)} precisam de detalhe")

            # DOM fallback scraping
            if missing:
                log.info(f"Raspando detalhe de {len(missing)} pedidos restantes…")
                for i, oid in enumerate(missing, 1):
                    log.info(f"  [{i}/{len(missing)}] {oid}")
                    dom_data = await self._dom_scrape_detail(page, oid)
                    if dom_data:
                        self.db.save_order(self._from_dom(oid, dom_data))
                    await asyncio.sleep(REQUEST_DELAY)

            total = self.db.count_orders()
            log.info(f"\n✅ Concluído! Total de pedidos no banco: {total}")
            if total:
                log.info("   Rode `streamlit run dashboard.py` para abrir o dashboard.")
            else:
                log.info("   Nenhum pedido salvo — me mande os endpoints JSON acima.")

            if not self.auto:
                await self._wait_for_enter("\n>>> Pressione ENTER para fechar o navegador… ")
            else:
                log.info("FIM_SCRAPER_OK")  # marcador para o dashboard detectar conclusão


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dig(d: dict, path: str):
    """Safely traverse dot-separated path."""
    for key in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def _category(merchant_type) -> str:
    """Mapeia merchant.type do iFood para categoria em PT-BR."""
    if not merchant_type:
        return "Restaurante"
    t = str(merchant_type).upper()
    if any(k in t for k in ("PHARMAC", "DRUGSTORE", "FARMAC", "SAUDE", "HEALTH")):
        return "Farmácia"
    if any(k in t for k in ("GROCER", "MARKET", "SUPERMARKET", "CONVENIENCE", "MERCADO")):
        return "Mercado"
    if any(k in t for k in ("PET", "PETSHOP")):
        return "Pet"
    if any(k in t for k in ("LIQUOR", "DRINK", "BEVER", "BEBIDA", "ADEGA")):
        return "Bebidas"
    if "RESTAURANT" in t or "FOOD" in t:
        return "Restaurante"
    # Tipo desconhecido — preserva legível
    return merchant_type.title()


def _cents(value) -> float:
    """Converte valor em centavos (int) para reais. None/inválido → 0.0."""
    if value is None:
        return 0.0
    try:
        return round(float(value) / 100.0, 2)
    except (TypeError, ValueError):
        return 0.0


# Brasil não tem mais horário de verão, então -3 é constante o ano todo.
BRASILIA = timezone(timedelta(hours=-3))


def _parse_ts(ts) -> datetime | None:
    """
    Converte o timestamp do iFood para hora de parede de Brasília (naive).

    ATENÇÃO: o iFood manda os dois formatos NO MESMO campo createdAt —
    uns em UTC ("2026-07-31T23:27:12.815Z"), outros já em local
    ("2026-08-26T21:38:43-03:00"). Antes o tzinfo era simplesmente
    descartado, então os que vinham em UTC ficavam 3h adiantados e um
    jantar das 20h era classificado como "Madrugada".
    """
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        if ts > 1e10:
            ts /= 1000
        # tz explícito: não depender do fuso da máquina que roda o scraper
        return datetime.fromtimestamp(ts, BRASILIA).replace(tzinfo=None)
    if not isinstance(ts, str):
        return None
    # ISO 8601 com timezone (ex.: "...-03:00" ou "...Z")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        pass
    else:
        if dt.tzinfo is not None:
            dt = dt.astimezone(BRASILIA)
        return dt.replace(tzinfo=None)
    for fmt, utc in [
        ("%Y-%m-%dT%H:%M:%S.%fZ", True), ("%Y-%m-%dT%H:%M:%SZ", True),
        ("%Y-%m-%dT%H:%M:%S.%f", False), ("%Y-%m-%dT%H:%M:%S", False),
        ("%Y-%m-%d %H:%M:%S", False), ("%Y-%m-%d", False),
        ("%d/%m/%Y %H:%M:%S", False), ("%d/%m/%Y %H:%M", False),
        ("%d/%m/%Y", False),
    ]:
        try:
            dt = datetime.strptime(ts, fmt)
        except ValueError:
            continue
        # o sufixo Z destes formatos também é UTC — precisa converter igual
        if utc:
            dt = dt.replace(tzinfo=timezone.utc).astimezone(BRASILIA).replace(tzinfo=None)
        return dt
    return None


def _price(d: dict, keys: list[str]) -> float:
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            clean = re.sub(r"[^\d,.]", "", v).replace(",", ".")
            try:
                return float(clean)
            except ValueError:
                pass
    return 0.0


def _norm_status(s: str) -> str:
    mapping = {
        "CONCLUDED": "ENTREGUE", "DELIVERED": "ENTREGUE",
        "CANCELLED": "CANCELADO", "CANCELED": "CANCELADO",
        "PENDING": "PENDENTE", "PLACED": "CONFIRMADO",
        "CONFIRMED": "CONFIRMADO", "IN_PREPARATION": "PREPARANDO",
        "DISPATCHED": "A CAMINHO", "WAITING": "AGUARDANDO",
    }
    return mapping.get(s.upper(), s)


def _time_slot(hour: int) -> str:
    if 5 <= hour < 12:
        return "Manhã (5h–12h)"
    elif 12 <= hour < 18:
        return "Tarde (12h–18h)"
    elif 18 <= hour < 23:
        return "Noite (18h–23h)"
    else:
        return "Madrugada (23h–5h)"


def _price_range(total: float) -> str:
    if total <= 0:
        return "Desconhecido"
    elif total <= 30:
        return "Até R$30"
    elif total <= 50:
        return "R$30–50"
    elif total <= 80:
        return "R$50–80"
    elif total <= 120:
        return "R$80–120"
    else:
        return "Acima de R$120"


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description=(
            "iFood scraper — na 1ª execução abre janela para login manual. "
            f"Sessão salva em {LOCAL_PROFILE}"
        )
    )
    ap.add_argument(
        "--profile-name", "-p", default="default",
        help="Nome da pessoa/perfil. Cada perfil tem banco e sessão isolados "
             "(ex.: -p joao → data/joao.db + profiles/joao/). Padrão: default",
    )
    ap.add_argument(
        "--profile",
        help="Diretório do perfil Chrome (override manual; normalmente use --profile-name)",
    )
    ap.add_argument(
        "--chrome",
        help="Caminho do binário do Google Chrome (auto-detectado se omitido)",
    )
    ap.add_argument(
        "--headless",
        action="store_true",
        help="Sem janela (só funciona após login já salvo no perfil)",
    )
    ap.add_argument(
        "--auto",
        action="store_true",
        help="Modo não-interativo (usado pelo dashboard): espera pedidos por "
             "polling em vez de ENTER. Captcha é resolvido na janela do Chrome.",
    )
    args = ap.parse_args()

    scraper = IFoodScraper(
        profile_path=args.profile,
        headless=args.headless,
        profile_name=args.profile_name,
        auto=args.auto,
    )
    if args.chrome:
        scraper.chrome_binary = args.chrome
    log.info(f"Perfil: '{scraper.profile_name}'  →  banco: {scraper.db.db_path}")
    asyncio.run(scraper.run())
