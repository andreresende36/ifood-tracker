# 🛵 iFood Order Tracker

Extrai o histórico completo de pedidos da sua conta iFood e exibe um dashboard
interativo com KPIs, análise temporal e estimativa de economia cozinhando em casa.

---

## Como funciona

1. **Scraper** (`scraper.py`) — abre uma janela do Chrome com um perfil **dedicado**
   (não mexe no seu Chrome do dia a dia). Na 1ª execução você loga no iFood
   manualmente; a sessão fica salva e as próximas coletas já entram logadas.
   Navega para `/pedidos`, intercepta as respostas da API do iFood e persiste em SQLite.
2. **Dashboard** (`dashboard.py`) — Streamlit + Plotly: filtros globais, KPIs,
   10+ gráficos e a seção **"E se eu cozinhasse em casa?"**.

> **Por que Streamlit?** Filtros reativos nativos, zero boilerplate de routing,
> dataframes com export built-in e hot-reload. Para uso pessoal, entrega mais rápido.

---

## Stack

| Componente | Tecnologia |
|------------|------------|
| Scraper    | Python + Playwright (Chromium), intercepta API |
| Storage    | SQLite (`data/*.db`) |
| Dashboard  | Streamlit + Plotly |
| Export     | CSV / Excel (openpyxl) |

---

## Instalação

```bash
# 1. Virtualenv
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependências
pip install -r requirements.txt

# 3. Browser do Playwright
playwright install chromium
```

---

## Uso

### 1. Coletar pedidos

```bash
python scraper.py
```

Na **1ª execução**: abre o Chrome → faça login no iFood na janela → pressione ENTER
no terminal. A sessão fica salva em `chrome_profile/`; nas próximas vezes já está logado.

Se aparecer captcha ("Não sou um robô"), resolva na própria janela — a coleta continua.

Re-executar **só adiciona pedidos novos** (sem duplicatas). Dados em `data/orders.db`.

#### Flags

| Flag | Atalho | Descrição |
|------|--------|-----------|
| `--profile-name NOME` | `-p` | Pessoa/perfil isolado → `data/NOME.db` + `profiles/NOME/`. Padrão: `default` |
| `--profile DIR` | | Diretório de perfil Chrome manual (override; normalmente use `-p`) |
| `--chrome CAMINHO` | | Binário do Google Chrome (auto-detectado se omitido) |
| `--headless` | | Sem janela (só funciona após login já salvo no perfil) |
| `--auto` | | Modo não-interativo (usado pelo dashboard): espera por polling, não por ENTER |

```bash
# Coletar para outra pessoa (banco e sessão separados)
python scraper.py -p joao        # → data/joao.db + profiles/joao/

# Atualizar em background, sem interação (após login já salvo)
python scraper.py -p joao --auto
```

### 2. Abrir o dashboard

```bash
streamlit run dashboard.py
```

Acesse [http://localhost:8501](http://localhost:8501).

No dashboard você pode trocar de **perfil** (cada pessoa = banco separado), renomear
o perfil e disparar a coleta pelo botão **⬇️ Coletar / atualizar pedidos** (roda o
scraper em modo `--auto`).

---

## Multi-perfil (várias pessoas)

Cada perfil é totalmente isolado:

```
data/orders.db        # perfil "default"  (você)
data/joao.db          # perfil "joao"
profiles/joao/        # sessão Chrome do joao
chrome_profile/       # sessão Chrome do default
data/profiles.json    # nomes de exibição (alias editável no dashboard)
```

---

## Dashboard — o que tem

- **KPIs**: total gasto, nº de pedidos, ticket médio, economia em cupons, taxas.
- **Análise temporal**: por ano, mês (série e sazonal), dia da semana, heatmap
  dia×hora, evolução do ticket médio.
- **Distribuição por faixa de valor**.
- **🍳 E se eu cozinhasse em casa?** — economia estimada **prato a prato**: cada
  item é classificado por tipo (pizza, lanche, comida caseira…) e recebe um % de
  economia típico de fazer em casa. Taxas de entrega + serviço contam como 100%
  evitáveis. Slider de "otimismo" escala todos os percentuais.
- **Restaurantes e itens**: por categoria, top restaurantes, itens mais pedidos,
  distribuição de custos.
- **Tabela de pedidos** com busca, ordenação e export **CSV / Excel**.

### Como a economia por prato é estimada

Classificação por palavra-chave no nome do item (`DISH_CATEGORIES` em `dashboard.py`).
Nome que não bate nenhuma palavra cai no genérico **"Outros" = 35%**. Não há predição
por IA — é match de palavra-chave.

| Tipo | Economia base |
|------|---------------|
| Bebida / Açaí | 65–70% |
| Pizza | 60% |
| Lanche / Massa / Comida caseira | 55% |
| Japonesa | 50% |
| Salada | 45% |
| Carne / Churrasco | 35% |
| Mercado / Farmácia | 8% |
| Outros (fallback) | 35% |

Base estatística: delivery custa em média **20–40% mais** que cozinhar em casa,
com variação forte por tipo de prato (margens maiores em comida montada/processada).

---

## Estrutura dos dados (SQLite)

### Tabela `orders` (1 registro por pedido)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | TEXT | ID único do pedido |
| `restaurant_name` | TEXT | Nome do restaurante |
| `category` | TEXT | Restaurante / Mercado / Farmácia / … |
| `ordered_at` | TEXT | Timestamp ISO |
| `status` | TEXT | ENTREGUE / CANCELADO / … |
| `subtotal` | REAL | Valor dos itens |
| `delivery_fee` | REAL | Taxa de entrega |
| `service_fee` | REAL | Taxa de serviço |
| `coupon_discount` | REAL | Desconto de cupom |
| `total` | REAL | Valor final pago |
| `year` / `month` / `day_of_week` / `hour` | INT | Derivados da data |
| `time_slot` | TEXT | Manhã / Tarde / Noite / Madrugada |
| `price_range` | TEXT | Faixa de valor do pedido |
| `scraped_at` | TEXT | Quando foi coletado |

### Tabela `order_items` (itens de cada pedido)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `order_id` | TEXT | FK → orders.id |
| `item_name` | TEXT | Nome do item |
| `quantity` | INT | Quantidade |
| `unit_price` | REAL | Preço unitário |
| `subtotal` | REAL | Subtotal do item |

---

## ⚠️ Segurança — o que NUNCA versionar

O `.gitignore` já bloqueia, mas atenção:

- **`chrome_profile/` e `profiles/`** contêm a sessão de login do Chrome
  (cookies, `Login Data`, tokens). **Subir isso = entregar acesso às suas contas.**
  Nunca commite, nem em repo privado.

Os bancos `data/*.db` são versionados de propósito (só seus dados de pedido).

### Versionar o histórico após uma coleta

```bash
git add data/*.db && git commit -m "update pedidos" && git push
```

`git add -A` é seguro — o `.gitignore` impede que as sessões do Chrome vazem.

---

## Troubleshooting

| Sintoma | Solução |
|---------|---------|
| "You are not logged in" | Rode `python scraper.py`, logue na janela do Chrome e pressione ENTER |
| "Failed to launch Chrome" | Passe o binário: `python scraper.py --chrome "/caminho/Google Chrome"` |
| Erro de perfil em uso | Feche outras janelas que usem o mesmo perfil dedicado |
| 0 pedidos capturados | O iFood pode ter mudado a API. Abra DevTools (F12 → Network), filtre por "order", role os pedidos e veja a URL das chamadas |
| Chips de filtro não somem ao limpar | Já corrigido (remontagem por nonce). Force refresh: `Cmd/Ctrl+Shift+R` |

---

## Estrutura do projeto

```
ifood-tracker/
├── scraper.py            # Coleta via Playwright + interceptação da API
├── dashboard.py          # Dashboard Streamlit
├── database.py           # Camada SQLite (orders + order_items, multi-perfil)
├── requirements.txt
├── data/                 # Bancos *.db (versionados) + raw_sample*.json + logs
├── chrome_profile/       # Sessão Chrome do perfil default (NÃO versionado)
└── profiles/             # Sessões Chrome dos demais perfis (NÃO versionado)
```
