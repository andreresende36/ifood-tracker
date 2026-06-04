# iFood Order Tracker

Extrai o histórico completo de pedidos da sua conta iFood e exibe um dashboard interativo.

---

## Como funciona

1. **Scraper** (`scraper.py`) — abre o Chrome com o seu perfil existente (você já está logado), navega para `/pedidos`, intercepta as respostas da API do iFood e persiste tudo em SQLite.
2. **Dashboard** (`dashboard.py`) — Streamlit + Plotly com filtros globais, KPIs e 10+ gráficos interativos.

> **Por que Streamlit?** Filtros reativos nativos, zero boilerplate de routing, dataframes com export built-in e hot-reload. Para uso pessoal supera Next.js em velocidade de entrega.

---

## Instalação

```bash
# 1. Crie e ative um virtualenv
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Instale o browser do Playwright
playwright install chromium
```

---

## Pré-requisito: estar logado no iFood

O scraper **reutiliza** o perfil do seu Chrome — não é necessário colocar senha no código.

1. Abra o Chrome **normalmente** (não via scraper ainda)
2. Acesse [ifood.com.br/pedidos](https://www.ifood.com.br/pedidos) e confirme que está logado
3. Feche o Chrome completamente antes de rodar o scraper (o Playwright precisa de acesso exclusivo ao perfil)

---

## Coletando os pedidos

```bash
python scraper.py
```

Opções:
```
--profile /caminho/perfil   Diretório do perfil Chrome (auto-detectado se omitido)
--headless                  Rodar sem janela visível
```

### Onde está o perfil Chrome?

| SO | Caminho padrão |
|----|----------------|
| macOS | `~/Library/Application Support/Google/Chrome/Default` |
| Linux | `~/.config/google-chrome/Default` |
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data\Default` |

### O que acontece durante a coleta

```
2024-01-15 19:30:01 [INFO] Launching browser with profile: ~/Library/.../Chrome/Default
2024-01-15 19:30:03 [INFO] Navigating to https://www.ifood.com.br/pedidos
2024-01-15 19:30:06 [INFO] Scrolling / clicking to load full order history…
2024-01-15 19:30:08 [INFO]   Round 1: 12 orders captured
2024-01-15 19:30:10 [INFO]   Round 2: 24 orders captured
...
2024-01-15 19:31:42 [INFO]   Round 18: 183 orders captured
2024-01-15 19:31:44 [INFO] Loading complete. 183 orders captured via API.
2024-01-15 19:31:44 [INFO] Saved 183 new orders from API interception
2024-01-15 19:31:44 [INFO] ✅ Done! Total orders in database: 183
```

Os dados ficam em `data/orders.db`. Re-executar o scraper **só adiciona pedidos novos** (sem duplicatas).

---

## Abrindo o dashboard

```bash
streamlit run dashboard.py
```

Acesse [http://localhost:8501](http://localhost:8501).

---

## Estrutura dos dados

```
data/
└── orders.db          SQLite com 2 tabelas:
    ├── orders         Um registro por pedido (15 campos)
    └── order_items    Itens de cada pedido (5 campos)
```

### Tabela `orders`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | TEXT | ID único do pedido |
| `restaurant_name` | TEXT | Nome do restaurante |
| `ordered_at` | TEXT | Timestamp ISO completo |
| `status` | TEXT | ENTREGUE / CANCELADO / etc. |
| `subtotal` | REAL | Valor dos itens |
| `delivery_fee` | REAL | Taxa de entrega |
| `service_fee` | REAL | Taxa de serviço |
| `coupon_discount` | REAL | Desconto de cupom |
| `total` | REAL | Valor final pago |
| `year` | INT | Ano (derivado) |
| `month` | INT | Mês 1–12 (derivado) |
| `day_of_week` | INT | 0=Segunda … 6=Domingo (derivado) |
| `hour` | INT | Hora 0–23 (derivado) |
| `time_slot` | TEXT | Manhã / Tarde / Noite / Madrugada |
| `price_range` | TEXT | Faixa de valor do pedido |

---

## Troubleshooting

**"You are not logged in"**
→ Feche o Chrome, abra normalmente, logue no iFood, feche novamente, rode o scraper.

**"Failed to launch with Chrome"**
→ Passe o caminho do perfil explicitamente: `python scraper.py --profile "/caminho/perfil"`

**0 pedidos capturados**
→ O iFood pode ter mudado a estrutura da API. Abra o Chrome com DevTools (F12 → Network), filtre por "order", role os pedidos e veja a URL das chamadas. Abra uma issue com a URL encontrada.

**Erro de permissão no perfil Chrome**
→ Feche **todas** as janelas do Chrome antes de rodar o scraper.
