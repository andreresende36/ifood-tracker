"""
iFood Order History Dashboard
─────────────────────────────
Run: streamlit run dashboard.py
"""

import io
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import (
    Database, DAY_NAMES, MONTH_NAMES,
    list_profiles, profile_display_name, set_profile_display_name,
)

# ── Page config ───────────────────────────────────────────────────────────────

ASSETS = Path(__file__).parent / "assets"
LOGO = ASSETS / "ifood-logo.png"      # wordmark aparado
ICONE = ASSETS / "ifood-icon.png"     # símbolo vazado em tile — legível a 16px

st.set_page_config(
    page_title="iFood — Histórico de Pedidos",
    page_icon=str(ICONE) if ICONE.exists() else "🛵",
    layout="wide",
    # "auto" e não "expanded": no desktop abre igual, mas no celular a sidebar
    # expandida cobre a tela inteira e a primeira coisa que se vê são filtros,
    # não os dados. Em "auto" o Streamlit a recolhe sozinho no estreito.
    initial_sidebar_state="auto",
)

# ── CSS tweaks ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Ritmo: respiro generoso ANTES do título de seção e apertado depois dele,
       para o cabeçalho grudar no próprio conteúdo em vez de flutuar no meio. */
    .block-container { padding-top: 2.25rem; }
    /* Seção é h2 e bloco é h3 — e o CSS mira os dois. Antes toda seção saía
       como h3 e herdava o ritmo de bloco: a regra de h2 nunca casava com
       nada na coluna de conteúdo, e o ritmo de seção era letra morta. */
    .block-container h2 { margin-top: 2.5rem; margin-bottom: 0.75rem;
                          font-size: 28px; font-weight: 600; letter-spacing: -0.14px; }
    .block-container h3 { margin-top: 1.75rem; margin-bottom: 0.5rem;
                          font-size: 18px; font-weight: 600; letter-spacing: -0.09px; }
    .block-container h1 + div [data-testid="stCaptionContainer"] { margin-top: -0.35rem; }

    /* O valor do KPI é o que se lê na varredura; o rótulo recua. */
    div[data-testid="stMetricValue"] > div { font-size: 1.65rem; font-weight: 700;
                                             letter-spacing: -0.02em; }
    /* sem prefixo de tag: o rótulo é um <label>, não um <div> — com
       "div[...]" a regra nunca casava e rótulo e valor saíam no mesmo tom */
    [data-testid="stMetricLabel"] { opacity: 0.72; }

    /* Superfícies que o navegador desenha por padrão e não pertencem a
       design system nenhum — seleção, barra de rolagem e anel de foco. */
    ::selection { background: rgba(234, 29, 44, 0.32); }
    * { scrollbar-width: thin; scrollbar-color: #2b323e transparent; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-thumb { background: #2b323e; border-radius: 6px;
                                border: 2px solid transparent; background-clip: content-box; }
    ::-webkit-scrollbar-thumb:hover { background: #3a4250; background-clip: content-box; }
    ::-webkit-scrollbar-track { background: transparent; }
    :focus-visible { outline: 2px solid #ea1d2c; outline-offset: 2px; border-radius: 4px; }

    /* Números da tabela alinhados na vertical pedem largura fixa de dígito;
       o valor do KPI (grande e solto) não — ali fica proporcional. */
    div[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }

    /* A proibição de sombra vale para o que o Streamlit desenha sozinho: a
       barra flutuante de ferramentas da tabela vem com box-shadow de fábrica,
       e era a única sombra viva na tela inteira. */
    [data-testid="stElementToolbarButtonContainer"],
    [data-testid="stElementToolbar"] { box-shadow: none; }

    /* Alvos de toque. O ✕ de um chip de filtro nasce com 8,8×8,8 e os ícones
       de "limpar tudo" com 21×21 — a área que a WCAG 2.5.8 (AA) exige é
       24×24. Os 44×44 do AAA não cabem num chip de 28px sem redesenhar o
       widget do Streamlit, e a cena de uso é desktop com mouse; 24 é o alvo. */
    [data-baseweb="tag"] { min-height: 26px; }
    [data-baseweb="tag"] span[role="presentation"] {
        min-width: 24px; min-height: 24px;
        display: inline-flex; align-items: center; justify-content: center;
        margin: -6px -4px -6px 0;   /* cresce a área sem crescer o desenho */
    }
    [data-baseweb="select"] svg[role="button"],
    [data-baseweb="select"] [role="button"] > svg {
        box-sizing: content-box; padding: 4px; margin: -4px;
    }

    /* iframe utilitário do localize.html — carrega e roda, mas não ocupa espaço */
    .st-key-localize_iframe { display: none; }
</style>
""", unsafe_allow_html=True)


def _localize_widgets():
    """
    Traduz textos internos dos widgets do Streamlit que não têm API
    (ex.: 'Select all' do multiselect). Roda no DOM pai via MutationObserver.

    O script vive em static/localize.html porque st.components.v1.html está
    depreciado e st.iframe recebe URL, não HTML inline. Servido pelo Streamlit
    na mesma origem, o iframe alcança window.parent.document — o que um data:
    URI (origem opaca) não permitiria.
    """
    # st.iframe recusa height=0 (o components.html antigo aceitava), então o
    # iframe vai com 1px dentro de um container escondido por CSS. display:none
    # não impede o iframe de carregar nem o script de rodar.
    with st.container(key="localize_iframe"):
        # A barra inicial é obrigatória: sem ela o st.iframe não reconhece
        # como URL e embute o caminho como se fosse HTML cru.
        st.iframe("/app/static/localize.html", height=1)

PRICE_RANGE_ORDER = [
    "Até R$30", "R$30–50", "R$50–80", "R$80–120", "Acima de R$120", "Desconhecido"
]
PLOTLY_TEMPLATE = "plotly_dark"

# ── Paleta dos gráficos ───────────────────────────────────────────────────────
# Três matizes, cada uma com UM papel fixo no dashboard inteiro — cor segue a
# grandeza, não a posição do gráfico. Validadas juntas contra a superfície real
# do Streamlit dark (#0e1117), em todos os pares:
#   faixa de luminosidade OK · croma OK · pior par CVD ΔE 8.3 (deutan) ·
#   visão normal ΔE 20.9 · contraste >= 3:1
# Teto de 3 é deliberado: com o vermelho da marca fixo, um 4º matiz sempre
# reprovava (amarelo↔vermelho ΔE 4.4, violeta↔azul 1.9). Mais que 3 categorias
# vira barra, não fatia.
DINHEIRO = "#ea1d2c"   # gasto, ticket, valor pago  (vermelho iFood, do logo)
PEDIDOS  = "#3987e5"   # contagem de pedidos/itens
ECONOMIA = "#199e70"   # economia e custo cozinhando em casa
ACCENT = DINHEIRO      # compat: usado como cor padrão das barras

# Cromo recessivo: grade e eixos a um passo da superfície, nunca competindo
# com os dados.
SURFACE  = "#0e1117"   # fundo real do Streamlit dark
GRID     = "#22252e"
AXIS     = "#3a3f4b"
INK_MUTE = "#8b8f9a"

# Sequencial de uma matiz só para o heatmap. Em fundo escuro o passo do zero
# tem que RECUAR para a superfície — a escala "Reds" do Plotly fazia o oposto,
# deixando as células vazias claras e o gráfico virava um bloco branco.
HEAT_SCALE = [
    [0.00, "#141b28"], [0.25, "#1c4a86"],
    [0.55, "#256abf"], [0.80, "#3987e5"], [1.00, "#86b6ef"],
]

# Acima de ~8 barras um número em cada uma vira ruído e começa a colidir.
MAX_ROTULOS = 8

# Tradução defensiva de status (caso o iFood retorne um valor não mapeado pelo scraper)
STATUS_PT = {
    "CONCLUDED": "Entregue", "DELIVERED": "Entregue", "ENTREGUE": "Entregue",
    "CANCELLED": "Cancelado", "CANCELED": "Cancelado", "CANCELADO": "Cancelado",
    "PENDING": "Pendente", "PENDENTE": "Pendente",
    "PLACED": "Confirmado", "CONFIRMED": "Confirmado", "CONFIRMADO": "Confirmado",
    "IN_PREPARATION": "Preparando", "PREPARANDO": "Preparando",
    "DISPATCHED": "A caminho", "A CAMINHO": "A caminho",
    "WAITING": "Aguardando", "AGUARDANDO": "Aguardando",
    "UNKNOWN": "Desconhecido",
}


def _translate_status(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return s
    return STATUS_PT.get(str(s).upper(), str(s).capitalize())


# Offset fixo em vez de "America/Sao_Paulo": o Brasil não tem mais horário de
# verão, então -3 é constante — e assim não dependemos do tzdata instalado.
BRASILIA = timezone(timedelta(hours=-3))


def _fmt_coleta(valor) -> str:
    """
    Formata o scraped_at para dd-mm-aaaa HH:MM:SS em horário de Brasília.

    O SQLite grava com datetime('now'), que é UTC — sem converter, a tela
    mostrava 3 horas à frente do horário real da coleta.
    """
    ts = pd.to_datetime(valor, errors="coerce", utc=True)
    if pd.isna(ts):
        return "–"
    return ts.tz_convert(BRASILIA).strftime("%d-%m-%Y %H:%M:%S")


def _brl(valor: float, casas: int = 2, md: bool = False) -> str:
    """
    Dinheiro no formato do país da interface: ponto no milhar, vírgula no
    decimal. O f-string do Python faz o oposto (1,724.05) e a tela inteira
    saía com pontuação americana.

    `md=True` escapa o cifrão: em markdown, dois `$` na mesma string viram
    delimitador de LaTeX e o Streamlit engole o trecho entre eles.
    """
    corpo = f"{valor:,.{casas}f}".translate(str.maketrans({",": ".", ".": ","}))
    return ("R\\$ " if md else "R$ ") + corpo


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_data(profile: str = "default"):
    db = Database(profile=profile)
    if not db.db_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    db.init()
    orders = db.get_orders_df()
    items  = db.get_items_df()
    if not orders.empty and "status" in orders.columns:
        orders["status"] = orders["status"].map(_translate_status)
    return orders, items


def reload():
    load_data.clear()
    st.rerun()


# ── Sidebar filters ───────────────────────────────────────────────────────────

FILTER_NAMES = [
    "flt_years", "flt_months", "flt_use_range", "flt_date_range",
    "flt_cats", "flt_status", "flt_dow", "flt_pr", "flt_rest",
]


def _clear_filters():
    """
    Limpa os filtros REMONTANDO os widgets: incrementa um nonce que entra na
    key de cada widget. Como a key muda, o Streamlit cria instâncias novas
    (estado vazio) — só assim os chips somem da tela. Apenas zerar o
    session_state não força o re-render visual do multiselect.
    """
    n = st.session_state.get("flt_nonce", 0)
    for name in FILTER_NAMES:
        st.session_state.pop(f"{name}_{n}", None)  # descarta estado antigo
    st.session_state["flt_nonce"] = n + 1


def _filter_default(key: str, options: list, wanted=()) -> list:
    """
    Estado inicial de um multiselect de filtro.

    Faz duas coisas:
    1. Descarta seleções que não existem mais nas opções — acontece ao trocar
       de perfil (ex.: 'Ago' selecionado no André, mas a Carol não tem pedidos
       em agosto). Sem isso o Streamlit quebra com valor fora da lista.
    2. Só na PRIMEIRA renderização da sessão, pré-seleciona `wanted`. Depois
       disso devolve vazio, senão o botão 'Limpar todos os filtros' remontaria
       os widgets já preenchidos de novo e nunca limparia nada.
    """
    atual = st.session_state.get(key)
    if isinstance(atual, list):
        mantidos = [v for v in atual if v in options]
        if len(mantidos) != len(atual):
            st.session_state[key] = mantidos

    if st.session_state.get("flt_seeded"):
        return []
    return [w for w in wanted if w in options]


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header(":material/filter_alt: Filtros")

    if df.empty:
        return df

    # Sufixo versionado nas keys — muda ao limpar, forçando widgets vazios.
    n = st.session_state.setdefault("flt_nonce", 0)
    def k(name: str) -> str:
        return f"{name}_{n}"

    # Botão de limpar — on_click roda antes do rerender, resetando os widgets
    st.sidebar.button(
        "Limpar filtros",
        icon=":material/backspace:",
        on_click=_clear_filters,
        width="stretch",
    )

    # ── Filtro temporal: Ano + Mês (multiselects, não conflitam) ──────────────
    st.sidebar.subheader(":material/calendar_month: Período")

    hoje = pd.Timestamp.now()

    years = sorted(df["year"].dropna().unique().astype(int).tolist())
    sel_years = st.sidebar.multiselect(
        "Ano", years, placeholder="Todos", key=k("flt_years"),
        default=_filter_default(k("flt_years"), years, [hoje.year]),
    )
    if sel_years:
        df = df[df["year"].isin(sel_years)]

    # Mês por nome (Jan–Dez), preservando ordem cronológica
    month_pairs = sorted(df["month"].dropna().unique().astype(int).tolist())
    month_labels = [MONTH_NAMES[m] for m in month_pairs]
    sel_month_labels = st.sidebar.multiselect(
        "Mês", month_labels, placeholder="Todos", key=k("flt_months"),
        default=_filter_default(
            k("flt_months"), month_labels, [MONTH_NAMES[hoje.month]]
        ),
    )
    if sel_month_labels:
        sel_months = [MONTH_NAMES.index(lbl) for lbl in sel_month_labels]
        df = df[df["month"].isin(sel_months)]

    # Intervalo de datas exato — opcional, recolhido por padrão (não trava a UI)
    valid_dates = df["ordered_at"].dropna()
    if not valid_dates.empty:
        with st.sidebar.expander("Intervalo de datas exato (opcional)"):
            min_d = valid_dates.min().date()
            max_d = valid_dates.max().date()
            use_range = st.checkbox("Filtrar por intervalo", value=False, key=k("flt_use_range"))
            date_range = st.date_input(
                "De / até",
                value=(min_d, max_d),
                min_value=min_d, max_value=max_d,
                disabled=not use_range,
                key=k("flt_date_range"),
            )
            # Só aplica quando ativado E com as DUAS datas escolhidas
            if use_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start, end = date_range
                df = df[
                    (df["ordered_at"].dt.date >= start)
                    & (df["ordered_at"].dt.date <= end)
                ]

    st.sidebar.divider()

    # Categoria (Restaurante / Mercado / Farmácia / …)
    if "category" in df.columns:
        cats = sorted(df["category"].dropna().unique().tolist())
        sel_cats = st.sidebar.multiselect(
            "Categoria", cats, placeholder="Todas", key=k("flt_cats"),
            default=_filter_default(k("flt_cats"), cats, ["Restaurante"]),
        )
        if sel_cats:
            df = df[df["category"].isin(sel_cats)]

    # Status
    statuses = sorted(df["status"].dropna().unique().tolist())
    sel_status = st.sidebar.multiselect(
        "Status", statuses, placeholder="Todos", key=k("flt_status"),
        # "Entregue", não "ENTREGUE": load_data() já passou pelo STATUS_PT
        default=_filter_default(k("flt_status"), statuses, ["Entregue"]),
    )
    if sel_status:
        df = df[df["status"].isin(sel_status)]

    # Day of week
    dow_options = DAY_NAMES
    sel_dow = st.sidebar.multiselect(
        "Dia da semana", dow_options, placeholder="Todos", key=k("flt_dow"),
        default=_filter_default(k("flt_dow"), dow_options),
    )
    if sel_dow:
        sel_dow_idx = [DAY_NAMES.index(d) for d in sel_dow]
        df = df[df["day_of_week"].isin(sel_dow_idx)]

    # Price range
    pr_options = [p for p in PRICE_RANGE_ORDER if p in df["price_range"].values]
    sel_pr = st.sidebar.multiselect(
        "Faixa de valor", pr_options, placeholder="Todas", key=k("flt_pr"),
        default=_filter_default(k("flt_pr"), pr_options),
    )
    if sel_pr:
        df = df[df["price_range"].isin(sel_pr)]

    # Restaurant
    restaurants = sorted(df["restaurant_name"].dropna().unique().tolist())
    sel_rest = st.sidebar.multiselect(
        "Restaurante", restaurants,
        placeholder="Todos",
        key=k("flt_rest"),
        default=_filter_default(k("flt_rest"), restaurants),
    )
    if sel_rest:
        df = df[df["restaurant_name"].isin(sel_rest)]

    st.sidebar.divider()
    st.sidebar.caption(
        f"{len(df)} pedidos selecionados  ·  "
        "deixe vazio = mostra todos; selecione = filtra só os escolhidos"
    )

    # Widgets já montados uma vez: daqui pra frente nenhum default é reaplicado
    st.session_state["flt_seeded"] = True

    return df


# ── KPI cards ─────────────────────────────────────────────────────────────────

def _entregues(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa o que foi entregue do que não foi.

    Comida que nunca chegou não é gasto: com o filtro de status limpo, os 9
    pedidos cancelados, recusados e de status desconhecido somavam R$ 333,60
    dentro do "Total gasto". A regra já existia no sinal do mês e não alcançava
    os KPIs.

    Se o recorte NÃO tem nenhum entregue, quem filtrou pediu para ver os
    cancelados — aí o corte não se aplica e o df volta inteiro.
    """
    if "status" not in df:
        return df, df.iloc[0:0]
    ok = df[df["status"] == "Entregue"]
    if ok.empty:
        return df, df.iloc[0:0]
    return ok, df[df["status"] != "Entregue"]


def show_kpis(df: pd.DataFrame):
    df, fora = _entregues(df)
    total_spent    = df["total"].sum()
    n_orders       = len(df)
    avg_ticket     = df["total"].mean() if n_orders else 0
    total_savings  = df["coupon_discount"].sum()
    total_delivery = df["delivery_fee"].sum()
    total_service  = df["service_fee"].sum()

    # Os cinco não têm o mesmo peso. Cinco tiles iguais numa linha era default
    # de framework — e, no espaço que sobra, truncava justamente o número
    # ("R$ 18,1…"). Três primários com valor cheio; cupons e taxas são leitura
    # de apoio e descem para uma linha discreta.
    c1, c2, c3 = st.columns(3)
    c1.metric("Total gasto",  _brl(total_spent))
    c2.metric("Pedidos",      f"{n_orders}")
    c3.metric("Ticket médio", _brl(avg_ticket))
    nota = (
        f"Economizado em cupons **{_brl(total_savings, md=True)}**"
        f"　·　Taxas de entrega e serviço **{_brl(total_delivery + total_service, md=True)}**"
    )
    if not fora.empty:
        nota += (
            f"　·　{len(fora)} pedido{'s' if len(fora) > 1 else ''} cancelado, recusado ou "
            f"sem status somando {_brl(fora['total'].sum(), md=True)} ficaram fora do total"
        )
    st.caption(nota)


# ── Sinal do mês ──────────────────────────────────────────────────────────────

MESES_EXTENSO = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Abaixo de dois meses fechados não existe média: existe o mês passado com
# outro nome. O bloco diz que não há base em vez de inventar comparação.
MIN_MESES_BASE = 2


def month_signal(orders_df: pd.DataFrame) -> dict | None:
    """
    Compara o mês corrente com a média dos meses anteriores, dia a dia.

    Duas decisões carregam o número:

    1. Roda sobre o histórico INTEIRO, nunca sobre o df filtrado — o dashboard
       abre filtrado no mês corrente e a baseline sairia vazia.
    2. Compara como-por-como: o realizado até o dia N contra o gasto dos meses
       anteriores ATÉ O MESMO DIA N. Contra meses cheios agosto aparece 0,2%
       acima; contra o mesmo recorte, 9,8%. A comparação ingênua esconde o
       sinal inteiro.

    Só pedido entregue entra: cancelado não é gasto.
    """
    if orders_df.empty or "ordered_at" not in orders_df:
        return None

    df = orders_df
    if "status" in df:
        df = df[df["status"] == "Entregue"]
    df = df.assign(_dt=pd.to_datetime(df["ordered_at"], errors="coerce")).dropna(subset=["_dt"])
    if df.empty:
        return None

    df = df.assign(_mes=df["_dt"].dt.to_period("M"))
    ref = df["_mes"].max()

    # Mês em curso só é "em curso" no calendário de verdade; se a última coleta
    # parou num mês passado, aquele mês está fechado e não cabe projeção.
    hoje = datetime.now(BRASILIA)
    parcial = ref == pd.Period(hoje, freq="M")
    dias_no_mes = ref.days_in_month
    corte = min(hoje.day, dias_no_mes) if parcial else dias_no_mes

    ref_df = df[df["_mes"] == ref]
    realizado = ref_df.loc[ref_df["_dt"].dt.day <= corte, "total"].sum()

    anteriores = df[df["_mes"] < ref]
    recorte = anteriores.loc[anteriores["_dt"].dt.day <= corte].groupby("_mes")["total"].sum()

    if len(recorte) < MIN_MESES_BASE or recorte.mean() <= 0:
        return {"ref": ref, "parcial": parcial, "corte": corte, "realizado": realizado,
                "sem_base": True, "meses": len(recorte)}

    media = recorte.mean()
    return {
        "ref": ref,
        "parcial": parcial,
        "corte": corte,
        "dias_no_mes": dias_no_mes,
        "realizado": realizado,
        "media": media,
        "minimo": recorte.min(),
        "maximo": recorte.max(),
        "meses": len(recorte),
        "delta": realizado / media - 1,
        "projecao": realizado / corte * dias_no_mes if parcial and corte else None,
        "sem_base": False,
    }


def _veredito(s: dict) -> tuple[str, str, str, str]:
    """
    Ícone, cor, o trecho que leva a cor e o trecho que não leva.

    Sem matiz nova: acima é Dinheiro, abaixo é Economia, e o patamar normal
    não tem cor nenhuma — é justamente o estado que não pede ação. A cor fica
    só no veredito; a ressalva sai em tinta de leitura, senão a frase inteira
    vira vermelho e o vermelho para de significar alguma coisa.
    """
    pct = abs(s["delta"]) * 100
    if s["realizado"] > s["maximo"]:
        return "trending_up", DINHEIRO, f"{pct:.0f}% acima da média", " — e acima de todo mês anterior"
    if s["realizado"] < s["minimo"]:
        return "trending_down", ECONOMIA, f"{pct:.0f}% abaixo da média", " — e abaixo de todo mês anterior"
    if s["delta"] >= 0.02:
        return "trending_up", DINHEIRO, f"{pct:.0f}% acima da média", ", dentro da faixa dos outros meses"
    if s["delta"] <= -0.02:
        return "trending_down", ECONOMIA, f"{pct:.0f}% abaixo da média", ", dentro da faixa dos outros meses"
    return "trending_flat", INK_MUTE, "no mesmo patamar dos meses anteriores", ""


def show_month_signal(orders_df: pd.DataFrame):
    """
    A primeira frase da tela responde "gastamos demais este mês?".

    Não é cartão nem tile: é uma frase e a sua nota de rodapé. E não repete
    nenhum número do bloco de KPIs logo abaixo — o que ele traz é a
    comparação, não o total.
    """
    s = month_signal(orders_df)
    if s is None:
        return

    nome = f"{MESES_EXTENSO[s['ref'].month]} de {s['ref'].year}"

    if s["sem_base"]:
        st.caption(
            f"Ainda não dá para dizer se {nome} está caro: são precisos pelo menos "
            f"{MIN_MESES_BASE} meses anteriores para formar uma média, e há {s['meses']}."
        )
        return

    icone, cor, veredito, ressalva = _veredito(s)
    st.markdown(
        f'<p style="font-size:20px;font-weight:600;letter-spacing:-0.1px;margin:0 0 .25rem">'
        f'<span style="font-family:Material Symbols Rounded;color:{cor};'
        f'font-size:22px;line-height:1;vertical-align:-4px;margin-right:.4rem">{icone}</span>'
        f'{nome} está <span style="color:{cor}">{veredito}</span>{ressalva}.</p>',
        unsafe_allow_html=True,
    )

    ate = (f"até o dia {s['corte']}" if s["parcial"] else "no mês fechado")
    # O sinal roda sobre o histórico inteiro e os KPIs logo abaixo rodam sobre
    # o filtro. Sem dizer isso, limpar o filtro de mês deixa a frase falando de
    # agosto ao lado de um total do ano inteiro, e a tela parece se contradizer.
    nota = (
        f"Média dos {s['meses']} meses anteriores {ate}: "
        f"**{_brl(s['media'], md=True)}** · faixa de **{_brl(s['minimo'], md=True)}** a "
        f"**{_brl(s['maximo'], md=True)}**"
    )
    if s["projecao"]:
        nota += f"　·　No ritmo atual o mês fecha em **{_brl(s['projecao'], md=True)}** — estimativa"
    nota += "　·　Comparação sobre o histórico completo, sem os filtros da barra lateral"
    st.caption(nota)


# ── Chart helpers ─────────────────────────────────────────────────────────────

# A barra de ferramentas do Plotly (zoom, lasso, "download plot as png") é
# cromo de outro sistema: não serve a um painel de agregados, e em 375px ela
# pousa POR CIMA do título do gráfico. Some — o dado fica.
PLOT_CONFIG = {"displayModeBar": False}


def _cromo(fig):
    """Grade/eixos em fio recessivo e fundo transparente sobre o tema."""
    fig.update_layout(
        # ponto no milhar, vírgula no decimal — vale para tick de eixo e hover,
        # que são formatados pelo próprio Plotly, fora do alcance do _brl()
        separators=",.",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK_MUTE),
        title_font=dict(color="#e6e8ec", size=15),
        margin=dict(t=44, b=0, l=0, r=0),
    )
    # title="": o eixo herdava o nome cru da coluna ("total", "category",
    # "pedidos"). O título do gráfico já diz a grandeza — o eixo repetindo
    # em jargão de banco só polui.
    eixo = dict(gridcolor=GRID, gridwidth=1, linecolor=AXIS,
                zerolinecolor=AXIS, ticks="", title="")
    fig.update_xaxes(**eixo)
    fig.update_yaxes(**eixo)
    return fig


def _bar(df, x, y, title, color=DINHEIRO, text=None, xtype=None, orient=None):
    # Rótulo só quando cabe: acima de MAX_ROTULOS barras o número em cada uma
    # colide e é ilegível (era o caso dos "Top 15/30", que saíam recortados).
    n = len(df)
    if text is not None and n > MAX_ROTULOS:
        text = None
    fig = px.bar(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE,
                 text=text, orientation=orient)
    fig.update_traces(
        marker_color=color,
        # "auto" e não "outside": na barra horizontal, a maior barra empurra o
        # rótulo para fora da área de plotagem e ele sai recortado no estreito
        # ("R$ 1…"). Com auto, quem tem barra larga leva o número por dentro e
        # só as curtas escrevem do lado de fora.
        textposition="auto" if orient == "h" else "outside",
        # O Plotly gira o rótulo para caber quando a barra é estreita, e o
        # número sai deitado dentro da barra. Travado na horizontal, ele vai
        # para fora quando não couber dentro.
        textangle=0,
        textfont=dict(color=INK_MUTE),
        insidetextfont=dict(color=SURFACE),
        # 2px de respiro entre barras vizinhas em vez de borda desenhada
        marker_line_color=SURFACE, marker_line_width=2,
    )
    if xtype:
        fig.update_xaxes(type=xtype)
    fig.update_layout(showlegend=False)
    return _cromo(fig)


def _nota_periodo_unico(df, x) -> bool:
    """
    Um período só no filtro (o recorte padrão, mês corrente): nenhum dos dois
    gráficos do par é gráfico — são duas barras gigantes repetindo valores que
    o bloco de KPIs já mostra.

    A nota sai UMA vez, na largura inteira, e por isso é chamada ANTES de abrir
    as colunas: emitida dentro de cada uma, a mesma frase aparecia duas vezes
    lado a lado.

    (df[col].iloc[0] e não df.iloc[0][col]: a segunda forma vira Series com
    dtype comum e o ano inteiro saía "2026.0".)
    """
    if len(df) != 1:
        return False
    st.caption(
        f"Só **{df[x].iloc[0]}** no filtro atual — o total está nos "
        "indicadores acima. Para comparar períodos, amplie o filtro; para "
        "ver o padrão dentro do mês, use *Dia da semana* ou *Heatmap*."
    )
    return True


def _barra(alvo, df, x, y, title, color=DINHEIRO, text=None, **kw):
    """Uma barra do par lado a lado, dentro da coluna que a recebe."""
    alvo.plotly_chart(
        _bar(df, x, y, title, color=color, text=text, **kw),
        width="stretch", config=PLOT_CONFIG,
    )


def _line(df, x, y, title):
    fig = px.line(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE, markers=True)
    fig.update_traces(line_color=DINHEIRO, line_width=2,
                      marker=dict(size=8, line=dict(color=SURFACE, width=2)))
    return _cromo(fig)


# ── Temporal analysis ─────────────────────────────────────────────────────────

def _abas(opcoes: list, key: str, default: str | None = None) -> str:
    """
    Seletor de painel que monta SÓ o escolhido.

    Com st.tabs o Streamlit monta todos os painéis de uma vez; os inativos
    ficam com container de largura 0 e o Plotly calcula área de plotagem
    negativa (o console enchia de '<rect> attribute width: A negative value
    is not valid'). Renderizando um painel por vez a causa some — e ainda
    sobra menos trabalho por rerun.

    `default` existe porque o primeiro da lista nem sempre tem o que dizer: no
    recorte de abertura do produto (mês corrente), "Por ano" e "Por mês" caem
    num período único e a seção de análise abria vazia.
    """
    padrao = default if default in opcoes else opcoes[0]
    escolha = st.segmented_control(
        "Visualização", opcoes,
        default=padrao, key=key, label_visibility="collapsed",
    )
    return escolha or padrao  # segmented_control permite desmarcar → None


def temporal_charts(df: pd.DataFrame):
    # "Quando e quanto" e não "Análise temporal": a faixa de valor entrou como
    # painel, e ela não é um recorte de tempo — é de tamanho de pedido.
    st.header(":material/insights: Quando e quanto")

    # Um recorte de um mês só não tem série temporal: "Por ano" e "Por mês"
    # viram uma barra só. Nesse caso abre no padrão DENTRO do mês.
    meses = df["ordered_at"].dt.to_period("M").nunique() if "ordered_at" in df else 0
    aba = _abas(
        ["Por ano", "Por mês", "Dia da semana", "Heatmap", "Ticket médio",
         "Faixa de valor"],
        key="aba_temporal",
        default="Por ano" if meses > 1 else "Dia da semana",
    )

    if aba == "Faixa de valor":
        _painel_faixa(df)
        return

    if aba == "Por ano":
        if df["year"].isna().all():
            st.info("Sem dados de data.")
            return
        by_year = (
            df.groupby("year")
            .agg(total=("total", "sum"), pedidos=("id", "count"))
            .reset_index()
            .sort_values("year")
        )
        by_year["year"] = by_year["year"].astype(int)
        if _nota_periodo_unico(by_year, "year"):
            return
        c1, c2 = st.columns(2)
        _barra(c1, by_year, "year", "total", "Gasto por ano (R$)",
               text=by_year["total"].apply(lambda v: _brl(v, 0)),
               xtype="category")
        _barra(c2, by_year, "year", "pedidos", "Pedidos por ano",
               color=PEDIDOS, text=by_year["pedidos"], xtype="category")

    elif aba == "Por mês":
        mode = st.radio("Visualização", ["Série histórica (mês/ano)", "Sazonal (Jan–Dez)"],
                        horizontal=True, key="month_mode")
        has_date = df["year"].notna() & df["month"].notna()
        dfd = df[has_date].copy()
        if dfd.empty:
            st.info("Sem dados de data.")
        elif mode == "Série histórica (mês/ano)":
            dfd["period"] = dfd.apply(
                lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
            )
            by_period = (
                dfd.groupby("period")
                .agg(total=("total", "sum"), pedidos=("id", "count"))
                .reset_index()
                .sort_values("period")
            )
            if _nota_periodo_unico(by_period, "period"):
                return
            c1, c2 = st.columns(2)
            _barra(c1, by_period, "period", "total", "Gasto por mês (R$)")
            _barra(c2, by_period, "period", "pedidos", "Pedidos por mês",
                   color=PEDIDOS)
        else:
            by_month = (
                dfd.groupby("month")
                .agg(total=("total", "mean"), pedidos=("id", "count"))
                .reset_index()
                .sort_values("month")
            )
            by_month["month_name"] = by_month["month"].map(
                lambda m: MONTH_NAMES[int(m)]
            )
            c1, c2 = st.columns(2)
            c1.plotly_chart(
                _bar(by_month, "month_name", "total", "Gasto médio por mês do ano (R$)"),
                width="stretch", config=PLOT_CONFIG,
            )
            c2.plotly_chart(
                _bar(by_month, "month_name", "pedidos", "Total de pedidos por mês do ano",
                     color=PEDIDOS),
                width="stretch", config=PLOT_CONFIG,
            )

    elif aba == "Dia da semana":
        dfd = df[df["day_of_week"].notna()].copy()
        if dfd.empty:
            st.info("Sem dados de dia da semana.")
            return
        dfd["day_name"] = dfd["day_of_week"].apply(lambda x: DAY_NAMES[int(x)])
        by_dow = (
            dfd.groupby(["day_of_week", "day_name"])
            .agg(total=("total", "sum"), pedidos=("id", "count"),
                 ticket=("total", "mean"))
            .reset_index()
            .sort_values("day_of_week")
        )
        c1, c2, c3 = st.columns(3)
        c1.plotly_chart(
            _bar(by_dow, "day_name", "total", "Gasto total por dia (R$)"),
            width="stretch", config=PLOT_CONFIG,
        )
        c2.plotly_chart(
            _bar(by_dow, "day_name", "pedidos", "Pedidos por dia", color=PEDIDOS),
            width="stretch", config=PLOT_CONFIG,
        )
        c3.plotly_chart(
            _bar(by_dow, "day_name", "ticket", "Ticket médio por dia (R$)", color=DINHEIRO),
            width="stretch", config=PLOT_CONFIG,
        )

    elif aba == "Heatmap":
        dfd = df[df["day_of_week"].notna() & df["hour"].notna()].copy()
        if dfd.empty:
            st.info("Sem dados de hora.")
            return
        pivot = (
            dfd.groupby(["day_of_week", "hour"])
            .size()
            .reset_index(name="pedidos")
            .pivot(index="day_of_week", columns="hour", values="pedidos")
            .reindex(index=range(7), columns=range(24))
            .fillna(0)
        )
        z = pivot.values
        fig = go.Figure(
            go.Heatmap(
                z=z,
                x=[f"{h:02d}h" for h in range(24)],
                y=DAY_NAMES,
                # Uma matiz só, e o zero RECUANDO para o fundo. Com "Reds" as
                # células vazias ficavam quase brancas: a maior parte da grade
                # é zero, então o gráfico virava um bloco claro gritando numa
                # tela escura — o oposto do que a escala deve fazer.
                colorscale=HEAT_SCALE,
                hoverongaps=False,
                # Número só nas células com pedido; zero não precisa de rótulo.
                text=[[str(int(v)) if v else "" for v in linha] for linha in z],
                texttemplate="%{text}",
                textfont=dict(size=10),
                xgap=2, ygap=2,          # respiro de 2px em vez de borda
                colorbar=dict(title="", thickness=10, outlinewidth=0,
                              tickfont=dict(color=INK_MUTE)),
            )
        )
        fig.update_layout(title="Pedidos por dia da semana × hora",
                          template=PLOTLY_TEMPLATE)
        st.plotly_chart(_cromo(fig), width="stretch", config=PLOT_CONFIG)

    elif aba == "Ticket médio":
        dfd = df[df["ordered_at"].notna()].copy()
        if dfd.empty:
            st.info("Sem dados de data.")
            return
        dfd["period"] = dfd["ordered_at"].dt.to_period("M").astype(str)
        by_p = (
            dfd.groupby("period")["total"]
            .mean()
            .reset_index()
            .rename(columns={"total": "ticket_medio"})
            .sort_values("period")
        )
        # Sem a guarda, um mês só desenhava um ponto solitário com o eixo x em
        # milissegundos (23:59:59.999 Jul 31 → 00:00:00.0005 Aug 1).
        if _nota_periodo_unico(by_p, "period"):
            return
        st.plotly_chart(
            _line(by_p, "period", "ticket_medio", "Evolução do ticket médio (R$)"),
            width="stretch", config=PLOT_CONFIG,
        )


# ── Price distribution ────────────────────────────────────────────────────────

def _painel_faixa(df: pd.DataFrame):
    """
    Faixa de valor como painel do seletor, não como seção própria.

    Era a menor seção da tela e carregava um nível de título igual ao do
    contrafactual — peso de estrutura que o conteúdo não sustentava. Como
    painel, divide o seletor com os recortes de tempo e some da rolagem
    quando ninguém pediu.
    """
    if df.empty:
        return

    pr_data = (
        df.groupby("price_range")
        .agg(pedidos=("id", "count"), total=("total", "sum"))
        .reset_index()
    )
    # Sort by defined order
    pr_data["order"] = pr_data["price_range"].apply(
        lambda x: PRICE_RANGE_ORDER.index(x) if x in PRICE_RANGE_ORDER else 99
    )
    pr_data = pr_data.sort_values("order")

    c1, c2 = st.columns(2)
    c1.plotly_chart(
        _bar(pr_data, "price_range", "pedidos", "Pedidos por faixa",
             color=PEDIDOS, text=pr_data["pedidos"]),
        width="stretch", config=PLOT_CONFIG,
    )
    c2.plotly_chart(
        _bar(pr_data, "price_range", "total", "Gasto total por faixa (R$)",
             text=pr_data["total"].apply(lambda v: _brl(v, 0))),
        width="stretch", config=PLOT_CONFIG,
    )


# ── Cooking savings (what-if, por prato) ──────────────────────────────────────

# Quanto mais barato sai CADA TIPO de prato feito em casa vs. pedido no delivery.
# Ex.: estrogonofe pago a R$50 sai ~R$20 em casa → economia de 60%.
# Margens maiores em comida processada/montada (pizza, lanche, açaí); menores em
# carnes nobres e itens de mercado (que já são quase o preço de ingrediente).
# Fontes: delivery 20–40% mais caro em média (Exame, Engenharia é:), com variação
# forte por tipo de prato.
DISH_CATEGORIES = [
    # (rótulo,            economia%,  palavras-chave no nome do item)
    ("Pizza",            0.60, ["pizza", "calzone"]),
    ("Açaí / Sobremesa", 0.65, ["açaí", "acai", "sorvete", "sobremesa", "doce",
                                 "brownie", "pudim", "milkshake", "petit"]),
    ("Lanche / Burger",  0.55, ["burger", "hamb", "lanche", "x-", "cheddar",
                                 "hot dog", "hotdog", "sanduí", "sandui"]),
    ("Bebida",           0.70, ["refri", "coca", "guaraná", "guarana", "suco",
                                 "água", "agua", "cerveja", "bebida", "lata"]),
    ("Massa / Italiana", 0.55, ["macarr", "massa", "lasanha", "nhoque", "talharim",
                                 "espaguete", "spaghetti", "penne", "ravioli"]),
    ("Comida caseira",   0.55, ["estrogonofe", "estrogonoff", "strogonoff", "marmita",
                                 "feijoada", "executiv", "prato feito", "pf ",
                                 "caseir", "feijão", "feijao", "arroz", "tutu",
                                 "virado", "parmegiana", "parmigiana"]),
    ("Japonesa / Sushi", 0.50, ["sushi", "temaki", "sashimi", "combinado", "uramaki",
                                 "hot roll", "yakisoba", "guioza", "japon"]),
    ("Salada / Saudável", 0.45, ["salada", "salad", "fit", "wrap", "bowl", "vegano",
                                 "vegetar"]),
    ("Carne / Churrasco", 0.35, ["picanha", "costela", "churrasc", "carne", "frango",
                                 "filé", "file ", "espetinho", "parrilla", "bife"]),
    ("Mercado / Farmácia", 0.08, ["mercado", "farm", "remédio", "remedio", "papel",
                                   "sabão", "sabao", "shampoo", "detergente"]),
]
_DEFAULT_DISH = ("Outros", 0.35)  # margem média conservadora


def _classify_dish(name: str) -> tuple[str, float]:
    """
    Mapeia o nome do item → (categoria, economia% estimada em casa).

    Vence a categoria com MAIS evidência no nome, não a primeira da lista.
    Com first-match-wins, "Bebida" (a segunda maior taxa, e a primeira da
    lista a casar) engolia todo combo que mencionasse um refrigerante:
    "Parmegiana de Baby Beef Angus + Refrigerante 600ml" saía como bebida a
    70%. Empate vai para a categoria mais conservadora — na dúvida, a
    estimativa erra para menos.
    """
    n = str(name).lower()
    # Um combo não é o refrigerante que vem dentro dele. "Combo 6 Esfihas +
    # 1 Refri Lata" só casa em "refri" — nenhuma categoria conhece "esfiha" —
    # e sairia como bebida a 70%. Nome montado cai no padrão conservador.
    montado = any(t in n for t in ("+", "combo", "oferta", "kit"))
    melhor = None
    for label, pct, keys in DISH_CATEGORIES:
        acertos = sum(1 for k in keys if k in n)
        if not acertos:
            continue
        # mais palavras-chave batidas vence; empate, menor economia vence
        chave = (acertos, -pct)
        if melhor is None or chave > melhor[0]:
            melhor = (chave, (label, pct))
    if melhor is None:
        return _DEFAULT_DISH
    if montado and melhor[1][0] == "Bebida":
        return _DEFAULT_DISH
    return melhor[1]


def _items_savings(items_df: pd.DataFrame, scale: float,
                   orders_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Economia estimada por item, classificando cada prato por tipo.
    `scale` (0.5–1.5) ajusta o otimismo global dos percentuais.
    Y = valor pago no item × economia%(tipo) × scale.

    O preço que vem do iFood no item é o de TABELA. O que o pedido custou de
    fato é menor: cupom, promoção do restaurante e benefício de clube abatem
    por fora, e nem todos aparecem em `coupon_discount` — em 120 dos 259
    pedidos, `subtotal − cupom + taxas` não bate com `total`. Somar preço de
    tabela e chamar de "pago" inflava a base da economia em 11,4%.

    Por isso cada item é rateado até o que o pedido efetivamente custou em
    comida: `total − entrega − serviço`. Com `orders_df`, a soma de `paid`
    fecha com o KPI da tela; sem ele (chamada antiga), continua no preço de
    tabela.
    """
    if items_df.empty:
        return items_df
    out = items_df.copy()
    cls = out["item_name"].apply(_classify_dish)
    out["dish_cat"] = cls.apply(lambda c: c[0])
    out["save_pct"] = cls.apply(lambda c: min(c[1] * scale, 0.95))
    tabela = out["subtotal"].where(out["subtotal"] > 0, out["unit_price"] * out["quantity"])
    out["paid"] = tabela.fillna(0)

    if orders_df is not None and not orders_df.empty:
        pago_em_comida = (
            orders_df["total"] - orders_df["delivery_fee"] - orders_df["service_fee"]
        )
        alvo = out["order_id"].map(dict(zip(orders_df["id"], pago_em_comida)))
        bruto = out.groupby("order_id")["paid"].transform("sum")
        # fator 1 onde não dá para ratear: pedido sem itens somando, ou item de
        # um pedido que não está no recorte.
        fator = (alvo / bruto).where(bruto > 0).fillna(1).clip(lower=0)
        out["paid"] = out["paid"] * fator

    out["home_cost"] = out["paid"] * (1 - out["save_pct"])
    out["saved"] = out["paid"] - out["home_cost"]
    return out


# Escala padrão dos percentuais por tipo de prato: 100% do valor tabelado em
# DISH_CATEGORIES. O controle de otimismo da seção move este número entre 50%
# e 150%.
ESCALA_CENTRAL = 1.0

# Chave do controle de otimismo. A linha do topo é desenhada ANTES da seção que
# tem o slider, então lê o valor pela session_state e cai no padrão na primeira
# renderização da sessão.
OTIMISMO_KEY = "otimismo_estimativa"


def _escala_atual() -> float:
    """O otimismo escolhido na seção, como fator. 100% na primeira carga."""
    return st.session_state.get(OTIMISMO_KEY, 100) / 100


def _economia_evitavel(df: pd.DataFrame, items_df: pd.DataFrame,
                       escala: float = ESCALA_CENTRAL):
    """
    A conta do contrafactual, isolada porque tem dois consumidores: a linha do
    topo e a seção inteira.

    Devolve (itens classificados, economia total, economia nos pratos, taxas,
    custo em casa, total pago).

    Taxa de entrega e serviço entram por inteiro e SEM estimativa — cozinhar em
    casa não tem entregador. A economia dos pratos é estimativa por tipo.

    O que fecha a conta: `sav["paid"]` é rateado até `total − taxas`, então
    itens + taxas == o mesmo total que o KPI do topo mostra.
    """
    df, _ = _entregues(df)          # comida que não chegou não tem contrafactual
    items_df = items_df[items_df["order_id"].isin(df["id"])] if not items_df.empty else items_df
    sav = _items_savings(items_df, escala, df)
    food_saved = sav["saved"].sum()
    fees = df["delivery_fee"].sum() + df["service_fee"].sum()
    total_saved = food_saved + fees
    total_pago = df["total"].sum()
    return sav, total_saved, food_saved, fees, total_pago - total_saved, total_pago


def show_savings_line(df: pd.DataFrame, items_df: pd.DataFrame):
    """
    A segunda pergunta da sessão — "dava para ter cozinhado?" — respondida no
    topo, em uma frase.

    A seção inteira fica onde está, com os gráficos e o prato a prato; o que
    sobe é só o veredito, porque duas telas de rolagem é longe demais para a
    pergunta que é a razão de ser do produto.
    """
    if df.empty or items_df.empty:
        return
    _, total_saved, _, _, _, total_pago = _economia_evitavel(df, items_df, _escala_atual())
    if total_pago <= 0:
        return
    pct = total_saved / total_pago * 100
    # Caption puro deixaria o veredito do contrafactual com o mesmo peso da
    # linha de cupons e taxas logo acima — a pergunta que é a razão de ser do
    # produto lida como nota de rodapé. Fica em corpo de texto, com o valor em
    # Economia: pesa mais que a legenda, menos que o sinal do mês.
    st.markdown(
        f'<p style="font-size:14px;line-height:22.4px;color:{INK_MUTE};margin:.35rem 0 0">'
        f'Desse total, <span style="color:{ECONOMIA};font-weight:600">'
        f'cerca de {_brl(total_saved, 0)} era evitável</span> — {pct:.0f}% do que '
        f'foi pago, cozinhando em casa. Estimativa; a conta está logo abaixo.</p>',
        unsafe_allow_html=True,
    )


def cooking_savings(df: pd.DataFrame, items_df: pd.DataFrame):
    st.header(":material/skillet: E se você tivesse cozinhado em casa?")
    if df.empty:
        st.info("Sem dados.")
        return
    if items_df.empty:
        st.info("Sem dados de itens (re-colete os pedidos para detalhar por prato).")
        return

    st.caption(
        "Economia estimada **prato a prato**: cada item é classificado por tipo "
        "(pizza, lanche, comida caseira…) e recebe um % de economia típico de fazer "
        "em casa. Ex.: estrogonofe pago a R\\$50 sai ~R\\$20 em casa → você economiza R\\$30. "
        "**Taxas de entrega + serviço** são 100% evitáveis e entram por cima."
    )

    scale = st.slider(
        "Otimismo da estimativa (ajusta todos os percentuais)",
        min_value=50, max_value=150, value=100, step=10, format="%d%%",
        key=OTIMISMO_KEY,
        help="100% = percentuais padrão por tipo de prato. 150% = mais otimista.",
    )
    sav, total_saved, food_saved, fees, home_total, total_pago = _economia_evitavel(
        df, items_df, scale / 100
    )
    home_food = sav["home_cost"].sum()

    # Sem chip de delta no primeiro tile: economizar é o desfecho bom, e o chip
    # saía em vermelho com seta para cima — alarme onde não há alarme.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Economia total",      _brl(total_saved))
    c2.metric("Custo cozinhando",    _brl(home_total))
    c3.metric("Economia nos pratos", _brl(food_saved))
    c4.metric("Taxas evitadas",      _brl(fees))
    # Os quatro tiles não têm o mesmo estatuto e a fileira não mostra isso:
    # três respondem ao controle de otimismo, um é valor apurado.
    st.caption(
        "**Economia nos pratos** é estimativa e segue o controle acima; "
        "**taxas evitadas** é valor apurado e não se move."
    )

    # Economia agregada por tipo de prato
    by_cat = (
        sav.groupby("dish_cat")
        .agg(pago=("paid", "sum"), economia=("saved", "sum"),
             itens=("item_name", "count"))
        .reset_index()
        .sort_values("economia", ascending=False)
    )
    c1, c2 = st.columns(2)
    por_econ = by_cat.sort_values("economia")
    f1 = _bar(por_econ, "economia", "dish_cat",
              "Economia estimada por tipo de prato (R$)", color=ECONOMIA,
              text=por_econ["economia"].apply(lambda v: _brl(v, 0)), orient="h")
    f1.update_layout(yaxis_title="")
    c1.plotly_chart(f1, width="stretch", config=PLOT_CONFIG)

    comp = pd.DataFrame({
        "cenário": ["Pago no iFood", "Cozinhando em casa"],
        "valor":   [total_pago, home_total],
    })
    fig2 = px.bar(
        comp, x="cenário", y="valor", title="Pago no delivery × custo em casa (R$)",
        template=PLOTLY_TEMPLATE,
        text=comp["valor"].apply(lambda v: _brl(v, 0)),
        color="cenário", color_discrete_sequence=[DINHEIRO, ECONOMIA],
    )
    fig2.update_traces(textposition="outside", textfont=dict(color=INK_MUTE),
                       marker_line_color=SURFACE, marker_line_width=2)
    fig2.update_layout(showlegend=False, xaxis_title="")
    c2.plotly_chart(_cromo(fig2), width="stretch", config=PLOT_CONFIG)

    # Top pratos: o que mais te custou X e quanto seria o Y
    with st.expander("Ver economia prato a prato (top 30)",
                     icon=":material/receipt_long:"):
        top = (
            sav.groupby(["item_name", "dish_cat"])
            .agg(qtd=("quantity", "sum"), pago=("paid", "sum"),
                 custo_casa=("home_cost", "sum"), economia=("saved", "sum"),
                 pct=("save_pct", "first"))
            .reset_index()
            .sort_values("economia", ascending=False)
            .head(30)
        )
        disp = top.copy()
        disp["pct"] = (disp["pct"] * 100).round(0).astype(int).astype(str) + "%"
        for col in ("pago", "custo_casa", "economia"):
            disp[col] = disp[col].apply(_brl)
        disp.columns = ["Prato", "Tipo", "Qtd", "Pago (X)",
                        "Custo em casa", "Economia (Y)", "% economia"]
        st.dataframe(disp, width="stretch", hide_index=True)

    st.caption(
        f"Fazer esses pratos em casa teria custado ~{_brl(home_food, md=True)} em "
        f"ingredientes, contra {_brl(sav['paid'].sum(), md=True)} que os mesmos pratos "
        f"custaram no delivery — economia de **{_brl(food_saved, md=True)}** só na comida, "
        f"mais {_brl(fees, md=True)} de taxas. O valor dos pratos é o que foi de fato "
        "pago: cupom e promoção já descontados."
    )


# ── Restaurants & items ───────────────────────────────────────────────────────

def restaurant_item_charts(df: pd.DataFrame, items_df: pd.DataFrame):
    st.header(":material/storefront: Restaurantes e itens")
    aba = _abas(
        ["Por categoria", "Top restaurantes", "Itens mais pedidos", "Distribuição de custos"],
        key="aba_restaurantes",
        # Uma categoria só (o filtro de abertura) não faz gráfico de categoria.
        default="Por categoria" if ("category" in df and df["category"].nunique() > 1)
                else "Top restaurantes",
    )

    if aba == "Por categoria":
        if df.empty or "category" not in df.columns:
            st.info("Sem dados de categoria.")
        else:
            by_cat = (
                df.groupby("category")
                .agg(pedidos=("id", "count"), total=("total", "sum"),
                     ticket=("total", "mean"))
                .reset_index()
                .sort_values("total", ascending=False)
            )
            # Barra, não rosca: com mais de uma categoria o par "gasto |
            # pedidos" fica igual ao resto do dashboard. Com UMA categoria —
            # que é o filtro de abertura — as duas barras só repetiam os dois
            # KPIs do topo, contra a própria regra da casa.
            if _nota_periodo_unico(by_cat, "category"):
                return
            c1, c2 = st.columns(2)
            c1.plotly_chart(
                _bar(by_cat, "category", "total", "Gasto por categoria (R$)",
                     text=by_cat["total"].apply(lambda v: _brl(v, 0))),
                width="stretch", config=PLOT_CONFIG,
            )
            c2.plotly_chart(
                _bar(by_cat, "category", "pedidos", "Nº de pedidos por categoria",
                     color=PEDIDOS, text=by_cat["pedidos"]),
                width="stretch", config=PLOT_CONFIG,
            )

            disp = by_cat.copy()
            disp.columns = ["Categoria", "Pedidos", "Total (R$)", "Ticket médio (R$)"]
            st.dataframe(disp, width="stretch", hide_index=True)

    elif aba == "Top restaurantes":
        if df.empty:
            return
        top_n = st.slider("Mostrar top N", 5, 30, 15, key="top_rest")
        by_rest = (
            df.groupby("restaurant_name")
            .agg(pedidos=("id", "count"), total=("total", "sum"),
                 ticket=("total", "mean"))
            .reset_index()
            .sort_values("pedidos", ascending=False)
            .head(top_n)
        )
        c1, c2 = st.columns(2)
        # As cores estavam trocadas aqui: frequência (contagem) saía vermelha e
        # valor gasto saía azul — o inverso do resto do dashboard.
        f1 = _bar(by_rest.sort_values("pedidos"), "pedidos", "restaurant_name",
                  "Por frequência", color=PEDIDOS, text="pedidos", orient="h")
        f1.update_layout(yaxis_title="")
        c1.plotly_chart(f1, width="stretch", config=PLOT_CONFIG)

        por_valor = by_rest.sort_values("total")
        f2 = _bar(por_valor, "total", "restaurant_name", "Por valor gasto (R$)",
                  text=por_valor["total"].apply(lambda v: _brl(v, 0)), orient="h")
        f2.update_layout(yaxis_title="")
        c2.plotly_chart(f2, width="stretch", config=PLOT_CONFIG)

    elif aba == "Itens mais pedidos":
        if items_df.empty:
            st.info("Sem dados de itens.")
            return
        top_n_i = st.slider("Mostrar top N", 5, 30, 15, key="top_items")
        by_item = (
            items_df.groupby("item_name")
            .agg(total_qty=("quantity", "sum"), n_orders=("order_id", "nunique"))
            .reset_index()
            .sort_values("total_qty", ascending=False)
            .head(top_n_i)
        )
        # quantidade é contagem → azul, não vermelho
        fig = _bar(by_item.sort_values("total_qty"), "total_qty", "item_name",
                   f"Top {top_n_i} itens mais pedidos (quantidade)",
                   color=PEDIDOS, text="total_qty", orient="h")
        fig.update_layout(yaxis_title="")
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)

    elif aba == "Distribuição de custos":
        df, _ = _entregues(df)      # mesma base do bloco de KPIs
        if df.empty:
            return
        total_subtotal = df["subtotal"].sum()
        total_delivery = df["delivery_fee"].sum()
        total_service  = df["service_fee"].sum()
        total_discount = df["coupon_discount"].sum()
        total_paid     = df["total"].sum()

        # A fatia dos itens sai do TOTAL menos as taxas, e não de
        # "subtotal − cupom". O preço de tabela dos itens não reconstrói o
        # total: promoção do restaurante e benefício de clube abatem por fora
        # e não aparecem em coupon_discount — em 120 de 259 pedidos a conta
        # não fechava, e a rosca afirmava no título um total que as fatias
        # contradiziam (R$ 1.002,74 de diferença em 2026). Assim a soma é o
        # total por construção.
        items_net = total_paid - total_delivery - total_service
        abatido = total_subtotal - items_net

        labels = ["Itens (líq.)", "Taxa entrega", "Taxa serviço"]
        values = [items_net, total_delivery, total_service]

        fig = go.Figure(
            go.Pie(
                labels=labels, values=values,
                # As 3 matizes validadas; identidade vem da legenda, não da cor
                # sozinha. O âmbar antigo (#f59e0b) reprovava na faixa de
                # luminosidade para fundo escuro.
                marker=dict(colors=[DINHEIRO, PEDIDOS, ECONOMIA],
                            line=dict(color=SURFACE, width=2)),
                hole=0.55,
                # Rótulo só na fatia em que ele cabe. As taxas são ~2-4% cada:
                # com label+valor por fora eles se sobrepunham, e por dentro
                # não cabem na lasca. Ficam na legenda, no hover e no texto
                # abaixo — nenhum valor depende só do tooltip.
                text=[f"{v / sum(values):.0%}" if v / sum(values) >= 0.08 else ""
                      for v in values],
                textinfo="text",
                # Fora da fatia: dentro, o rótulo ficava em #0e1117 sobre o
                # vermelho da marca — 4,24:1, abaixo do AA de texto. Fora, ele
                # cai na tinta recuada sobre a superfície, com 5,84:1.
                textposition="outside",
                outsidetextfont=dict(color=INK_MUTE, size=13),
                hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>",
                sort=False,
            )
        )
        fig.update_layout(
            title=f"Distribuição do que você pagou (total {_brl(total_paid)})",
            template=PLOTLY_TEMPLATE,
            showlegend=True,
            legend=dict(orientation="h", y=-0.05, font=dict(color=INK_MUTE)),
        )
        st.plotly_chart(_cromo(fig), width="stretch", config=PLOT_CONFIG)
        outros = abatido - total_discount
        nota = (
            f"Preço de tabela dos itens: {_brl(total_subtotal, md=True)}  ·  "
            f"abatido: −{_brl(abatido, md=True)}  →  "
            f"pago em comida: {_brl(items_net, md=True)}. "
            "Desconto **não** é custo — por isso não tem fatia."
        )
        if outros > 0.01:
            nota += (
                f" Do abatido, {_brl(total_discount, md=True)} veio de cupom; "
                f"os outros {_brl(outros, md=True)} são promoção do restaurante "
                "e benefício de clube, que o iFood não discrimina no histórico."
            )
        st.caption(nota)


# ── Scraper runner ────────────────────────────────────────────────────────────

def run_scraper(profile: str):
    """
    Dispara o scraper em modo --auto para o perfil e mostra status ao vivo.
    Bloqueia a UI enquanto roda, lendo o log em tempo real. Ao terminar,
    limpa o cache e recarrega o dashboard com os dados novos.
    """
    log_path = Path(f"data/scrape_{profile}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "scraper.py",
        "--profile-name", profile,
        "--auto",
    ]

    with st.status(f"Coletando pedidos de **{profile}**…", expanded=True) as status:
        st.caption(
            "Uma janela do Chrome vai abrir. Se aparecer captcha "
            "('Não sou um robô'), resolva nela — a coleta continua sozinha."
        )
        box = st.empty()
        with open(log_path, "w", encoding="utf-8") as logf:
            proc = subprocess.Popen(
                cmd, stdout=logf, stderr=subprocess.STDOUT, cwd=str(Path.cwd())
            )

        # Poll do processo, atualizando o tail do log
        while proc.poll() is None:
            _render_log_tail(box, log_path)
            time.sleep(1.5)
        _render_log_tail(box, log_path)

        ok = proc.returncode == 0 and "FIM_SCRAPER_OK" in _read_log(log_path)
        if ok:
            status.update(label="Coleta concluída", state="complete")
        else:
            status.update(label="Coleta encerrou com avisos — confira o log abaixo.",
                          state="error")

    load_data.clear()
    st.toast("Dados atualizados!" if ok else "Coleta finalizada com avisos.")
    time.sleep(1)
    st.rerun()


def _read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _render_log_tail(box, path: Path, n: int = 14):
    lines = _read_log(path).splitlines()
    # Esconde marcadores internos e mostra as últimas linhas relevantes
    lines = [ln for ln in lines if "FIM_SCRAPER_OK" not in ln]
    box.code("\n".join(lines[-n:]) or "Iniciando…", language="log")


# ── Orders table ──────────────────────────────────────────────────────────────

def orders_table(df: pd.DataFrame):
    st.header(":material/table_rows: Tabela de pedidos")
    if df.empty:
        st.info("Nenhum pedido encontrado com os filtros atuais.")
        return

    cols = ["ordered_at", "restaurant_name"]
    if "category" in df.columns:
        cols.append("category")
    cols += [
        "status", "total", "subtotal", "delivery_fee", "service_fee",
        "coupon_discount", "year", "month_name", "day_name", "time_slot", "price_range",
    ]
    display = df[cols].copy()
    names = ["Data/hora", "Restaurante"]
    if "category" in df.columns:
        names.append("Categoria")
    names += [
        "Status", "Total (R$)", "Subtotal", "Entrega", "Serviço", "Desconto",
        "Ano", "Mês", "Dia", "Turno", "Faixa",
    ]
    display.columns = names

    search = st.text_input("Buscar restaurante, categoria ou status", "")
    if search:
        # regex=False: o nome do item traz "(", "+" e "*" o tempo todo, e um
        # parêntese solto derrubava a metade de baixo da tela com um traceback
        # do pyarrow no lugar da tabela e dos botões de export.
        # E só as colunas que o rótulo promete: o apply varria as 14, inclusive
        # as numéricas, então "10" casava com um valor de desconto.
        alvos = [c for c in ("Restaurante", "Categoria", "Status") if c in display]
        mask = (
            display[alvos]
            .apply(lambda col: col.astype(str).str.contains(search, case=False, regex=False))
            .any(axis=1)
        )
        display = display[mask]
        if display.empty:
            st.caption(f"Nenhum pedido com “{search}” no restaurante, categoria ou status.")

    # Ordenação num terço da largura: solto, o selectbox esticava por ~1200px
    # de coluna de conteúdo para listar 14 nomes curtos.
    c_ord, c_dir, _ = st.columns([2, 1, 3])
    sort_col = c_ord.selectbox("Ordenar por", display.columns.tolist(), index=0)
    asc = c_dir.checkbox("Crescente", value=False)
    display = display.sort_values(sort_col, ascending=asc)

    # A tela mostra dinheiro e data formatados; o export leva os tipos crus,
    # senão a planilha recebe texto e ninguém soma nada nela.
    vis = display.copy()
    for col in ("Total (R$)", "Subtotal", "Entrega", "Serviço", "Desconto"):
        if col in vis:
            vis[col] = vis[col].apply(_brl)
    if "Data/hora" in vis:
        vis["Data/hora"] = pd.to_datetime(vis["Data/hora"], errors="coerce").dt.strftime(
            "%d-%m-%Y %H:%M"
        )
    # hide_index: o índice do pandas vinha com furos (0,1,2,4,6,9…) porque o
    # recorte preserva a numeração do banco. Na tela isso lê como linha faltando.
    st.dataframe(vis, width="stretch", height=400, hide_index=True)

    # Export
    col1, col2 = st.columns([1, 5])
    csv = display.to_csv(index=False).encode("utf-8-sig")
    col1.download_button("CSV", csv, "ifood_pedidos.csv", "text/csv",
                         icon=":material/download:")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        display.to_excel(writer, index=False, sheet_name="Pedidos")
    col2.download_button(
        "Excel", buf.getvalue(),
        "ifood_pedidos.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # A marca vive no slot de logo do Streamlit (canto superior esquerdo, fica
    # acima da sidebar). Com o wordmark ali, repetir "iFood" no h1 seria dizer
    # a mesma coisa duas vezes — o título passa a nomear só a tela.
    if LOGO.exists():
        st.logo(str(LOGO), icon_image=str(ICONE), size="large")
    st.title("Histórico de pedidos")
    _localize_widgets()  # traduz textos internos dos widgets (ex.: 'Select all')

    # Seletor de perfil (pessoa) — bancos isolados, sem misturar pedidos
    profiles = list_profiles() or ["default"]
    # default sempre primeiro → abre por padrão ao iniciar o dashboard
    if "default" in profiles:
        profiles = ["default"] + [p for p in profiles if p != "default"]
    # run.sh passa o perfil escolhido por aqui; sem ele, abre no primeiro
    initial = os.environ.get("IFOOD_PROFILE", "")
    index = profiles.index(initial) if initial in profiles else 0
    sel_profile = st.sidebar.selectbox(
        "Perfil", profiles,
        index=index,
        format_func=profile_display_name,
        help="Cada perfil é uma pessoa, com banco de dados separado.",
    )

    # Botão de coletar/atualizar pedidos deste perfil (roda o scraper)
    if st.sidebar.button(
        "Coletar / atualizar pedidos",
        icon=":material/download:",
        width="stretch",
        type="primary",
        help="Roda o scraper para este perfil. Abre o Chrome; resolva o "
             "captcha na janela se aparecer.",
    ):
        run_scraper(sel_profile)  # bloqueia, mostra status e dá rerun ao fim

    # Mesma família da ação acima: atualizar os dados. Coletar busca no iFood;
    # Recarregar só relê o banco (barato, sem abrir o Chrome).
    if st.sidebar.button(
        "Recarregar", icon=":material/refresh:", width="stretch",
        help="Relê o banco local, sem ir ao iFood.",
    ):
        reload()

    # Editor de nome de exibição (não renomeia arquivos/sessões)
    with st.sidebar.expander("Renomear este perfil"):
        new_name = st.text_input(
            "Nome de exibição",
            value=profile_display_name(sel_profile),
            key=f"rename_{sel_profile}",
        )
        if st.button("Salvar nome", width="stretch"):
            set_profile_display_name(sel_profile, new_name)
            st.success("Nome atualizado!")
            st.rerun()
        st.caption(f"Banco: `{sel_profile}` (chave fixa, não muda)")

    st.sidebar.divider()

    orders_df, items_df = load_data(sel_profile)

    if orders_df.empty:
        st.warning(
            f"Nenhum pedido no perfil **{sel_profile}**. "
            "Clique em **Coletar / atualizar pedidos** na barra lateral "
            f"ou rode `python scraper.py -p {sel_profile}`."
        )
        if st.button("Recarregar", icon=":material/refresh:"):
            reload()
        return

    # A procedência do dado é legenda do título, não uma linha com botão ao
    # lado: espremido numa coluna estreita o rótulo quebrava em "Recar/regar".
    # "Recarregar" subiu para a sidebar, junto de "Coletar" — são a mesma
    # família de ação (atualizar os dados), e lá têm largura inteira.
    st.caption(
        f"Base de dados: **{len(orders_df)}** pedidos · "
        f"Última coleta: {_fmt_coleta(orders_df['scraped_at'].max()) if 'scraped_at' in orders_df else '–'}"
    )

    filtered = sidebar_filters(orders_df)
    filtered_items = items_df[items_df["order_id"].isin(filtered["id"])] if not items_df.empty else pd.DataFrame()

    st.divider()

    # O topo responde as duas perguntas com que a sessão começa: "gastamos
    # demais este mês?" e "dava para ter cozinhado?". A primeira vem do
    # histórico INTEIRO (orders_df, não filtered) — dentro do recorte do
    # próprio mês ela não tem resposta. A segunda é o veredito da seção que
    # vem logo abaixo, que sozinha ficava a duas telas de rolagem.
    show_month_signal(orders_df)
    show_kpis(filtered)
    show_savings_line(filtered, filtered_items)

    st.divider()

    # Uma linha só separa o resumo da análise. Entre as seções o trabalho é do
    # espaço e do degrau de título — fio em toda troca de assunto vira grade.
    cooking_savings(filtered, filtered_items)
    temporal_charts(filtered)
    restaurant_item_charts(filtered, filtered_items)
    orders_table(filtered)


if __name__ == "__main__":
    main()
