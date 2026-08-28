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
from datetime import timedelta, timezone
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

st.set_page_config(
    page_title="iFood — Histórico de Pedidos",
    page_icon="🛵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS tweaks ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 4px;
    }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] > div { font-size: 1.6rem; font-weight: 700; }
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
DINHEIRO = "#ef4444"   # gasto, ticket, valor pago  (vermelho iFood)
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
    st.sidebar.header("🔎 Filtros")

    if df.empty:
        return df

    # Sufixo versionado nas keys — muda ao limpar, forçando widgets vazios.
    n = st.session_state.setdefault("flt_nonce", 0)
    def k(name: str) -> str:
        return f"{name}_{n}"

    # Botão de limpar — on_click roda antes do rerender, resetando os widgets
    st.sidebar.button(
        "🧹 Limpar todos os filtros",
        on_click=_clear_filters,
        width="stretch",
    )

    # ── Filtro temporal: Ano + Mês (multiselects, não conflitam) ──────────────
    st.sidebar.subheader("📅 Período")

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

def show_kpis(df: pd.DataFrame):
    total_spent    = df["total"].sum()
    n_orders       = len(df)
    avg_ticket     = df["total"].mean() if n_orders else 0
    total_savings  = df["coupon_discount"].sum()
    total_delivery = df["delivery_fee"].sum()
    total_service  = df["service_fee"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total gasto",       f"R$ {total_spent:,.2f}")
    c2.metric("🛵 Pedidos",           f"{n_orders}")
    c3.metric("🎯 Ticket médio",      f"R$ {avg_ticket:,.2f}")
    c4.metric("🏷️ Economizado (cupons)", f"R$ {total_savings:,.2f}")
    c5.metric("📦 Taxas (entrega+serviço)", f"R$ {(total_delivery + total_service):,.2f}")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _cromo(fig):
    """Grade/eixos em fio recessivo e fundo transparente sobre o tema."""
    fig.update_layout(
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
        textposition="outside",
        textfont=dict(color=INK_MUTE),
        # 2px de respiro entre barras vizinhas em vez de borda desenhada
        marker_line_color=SURFACE, marker_line_width=2,
    )
    if xtype:
        fig.update_xaxes(type=xtype)
    fig.update_layout(showlegend=False)
    return _cromo(fig)


def _barra_ou_numero(alvo, df, x, y, title, color=DINHEIRO, text=None, **kw):
    """
    Uma barra só não é gráfico — é um número.

    Com o filtro padrão (ano + mês corrente) os painéis "Por ano" e "Por mês"
    reduziam a uma barra gigante ocupando meia tela para repetir um valor que
    já está no KPI do topo. Nesse caso mostra o número direto.
    """
    if len(df) == 1:
        # df[col].iloc[0], não df.iloc[0][col]: a segunda forma vira uma Series
        # com dtype comum e o ano inteiro saía como "2026.0".
        periodo, valor = df[x].iloc[0], df[y].iloc[0]
        texto = f"R$ {valor:,.2f}" if "R$" in title else f"{valor:,.0f}"
        alvo.metric(f"{title.replace(' (R$)', '')} · {periodo}", texto)
        return
    alvo.plotly_chart(
        _bar(df, x, y, title, color=color, text=text, **kw), width="stretch"
    )


def _line(df, x, y, title):
    fig = px.line(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE, markers=True)
    fig.update_traces(line_color=DINHEIRO, line_width=2,
                      marker=dict(size=8, line=dict(color=SURFACE, width=2)))
    return _cromo(fig)


# ── Temporal analysis ─────────────────────────────────────────────────────────

def _abas(opcoes: list, key: str) -> str:
    """
    Seletor de painel que monta SÓ o escolhido.

    Com st.tabs o Streamlit monta todos os painéis de uma vez; os inativos
    ficam com container de largura 0 e o Plotly calcula área de plotagem
    negativa (o console enchia de '<rect> attribute width: A negative value
    is not valid'). Renderizando um painel por vez a causa some — e ainda
    sobra menos trabalho por rerun.
    """
    escolha = st.segmented_control(
        "Visualização", opcoes,
        default=opcoes[0], key=key, label_visibility="collapsed",
    )
    return escolha or opcoes[0]  # segmented_control permite desmarcar → None


def temporal_charts(df: pd.DataFrame):
    st.subheader("📅 Análise temporal")

    aba = _abas(
        ["Por ano", "Por mês", "Dia da semana", "Heatmap", "Ticket médio"],
        key="aba_temporal",
    )

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
        c1, c2 = st.columns(2)
        _barra_ou_numero(c1, by_year, "year", "total", "Gasto por ano (R$)",
                         text=by_year["total"].apply(lambda v: f"R${v:,.0f}"),
                         xtype="category")
        _barra_ou_numero(c2, by_year, "year", "pedidos", "Pedidos por ano",
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
            c1, c2 = st.columns(2)
            _barra_ou_numero(c1, by_period, "period", "total", "Gasto por mês (R$)")
            _barra_ou_numero(c2, by_period, "period", "pedidos", "Pedidos por mês",
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
                width="stretch",
            )
            c2.plotly_chart(
                _bar(by_month, "month_name", "pedidos", "Total de pedidos por mês do ano",
                     color=PEDIDOS),
                width="stretch",
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
            width="stretch",
        )
        c2.plotly_chart(
            _bar(by_dow, "day_name", "pedidos", "Pedidos por dia", color=PEDIDOS),
            width="stretch",
        )
        c3.plotly_chart(
            _bar(by_dow, "day_name", "ticket", "Ticket médio por dia (R$)", color=DINHEIRO),
            width="stretch",
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
        st.plotly_chart(_cromo(fig), width="stretch")

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
        st.plotly_chart(
            _line(by_p, "period", "ticket_medio", "Evolução do ticket médio (R$)"),
            width="stretch",
        )


# ── Price distribution ────────────────────────────────────────────────────────

def price_distribution(df: pd.DataFrame):
    st.subheader("💵 Distribuição por faixa de valor")
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
        width="stretch",
    )
    c2.plotly_chart(
        _bar(pr_data, "price_range", "total", "Gasto total por faixa (R$)",
             text=pr_data["total"].apply(lambda v: f"R${v:,.0f}")),
        width="stretch",
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
    """Mapeia o nome do item → (categoria, economia% estimada em casa)."""
    n = str(name).lower()
    for label, pct, keys in DISH_CATEGORIES:
        if any(k in n for k in keys):
            return label, pct
    return _DEFAULT_DISH


def _items_savings(items_df: pd.DataFrame, scale: float) -> pd.DataFrame:
    """
    Economia estimada por item, classificando cada prato por tipo.
    `scale` (0.5–1.5) ajusta o otimismo global dos percentuais.
    Y = preço pago no item × economia%(tipo) × scale.
    """
    if items_df.empty:
        return items_df
    out = items_df.copy()
    cls = out["item_name"].apply(_classify_dish)
    out["dish_cat"] = cls.apply(lambda c: c[0])
    out["save_pct"] = cls.apply(lambda c: min(c[1] * scale, 0.95))
    paid = out["subtotal"].where(out["subtotal"] > 0, out["unit_price"] * out["quantity"])
    out["paid"] = paid.fillna(0)
    out["home_cost"] = out["paid"] * (1 - out["save_pct"])
    out["saved"] = out["paid"] - out["home_cost"]
    return out


def cooking_savings(df: pd.DataFrame, items_df: pd.DataFrame):
    st.subheader("🍳 E se você tivesse cozinhado em casa?")
    if df.empty:
        st.info("Sem dados.")
        return
    if items_df.empty:
        st.info("Sem dados de itens (re-colete os pedidos para detalhar por prato).")
        return

    st.caption(
        "Economia estimada **prato a prato**: cada item é classificado por tipo "
        "(pizza, lanche, comida caseira…) e recebe um % de economia típico de fazer "
        "em casa. Ex.: estrogonofe pago a R$50 sai ~R$20 em casa → você economiza R$30. "
        "**Taxas de entrega + serviço** são 100% evitáveis e entram por cima."
    )

    scale = st.slider(
        "Otimismo da estimativa (ajusta todos os percentuais)",
        min_value=50, max_value=150, value=100, step=10, format="%d%%",
        help="100% = percentuais padrão por tipo de prato. 150% = mais otimista.",
    )
    sav = _items_savings(items_df, scale / 100)

    food_saved = sav["saved"].sum()
    home_food  = sav["home_cost"].sum()
    fees       = df["delivery_fee"].sum() + df["service_fee"].sum()
    total_saved = food_saved + fees
    total_pago = df["total"].sum()
    home_total = total_pago - total_saved

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💸 Economia total",      f"R$ {total_saved:,.2f}",
              f"−{(total_saved/total_pago*100) if total_pago else 0:.0f}% do que pagou",
              delta_color="inverse")
    c2.metric("🍳 Custo cozinhando",    f"R$ {home_total:,.2f}")
    c3.metric("🥡 Economia nos pratos", f"R$ {food_saved:,.2f}")
    c4.metric("📦 Taxas evitadas",      f"R$ {fees:,.2f}")

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
              text=por_econ["economia"].apply(lambda v: f"R${v:,.0f}"), orient="h")
    f1.update_layout(yaxis_title="")
    c1.plotly_chart(f1, width="stretch")

    comp = pd.DataFrame({
        "cenário": ["Pago no iFood", "Cozinhando em casa"],
        "valor":   [total_pago, home_total],
    })
    fig2 = px.bar(
        comp, x="cenário", y="valor", title="Pago no delivery × custo em casa (R$)",
        template=PLOTLY_TEMPLATE,
        text=comp["valor"].apply(lambda v: f"R${v:,.0f}"),
        color="cenário", color_discrete_sequence=[DINHEIRO, ECONOMIA],
    )
    fig2.update_traces(textposition="outside", textfont=dict(color=INK_MUTE),
                       marker_line_color=SURFACE, marker_line_width=2)
    fig2.update_layout(showlegend=False, xaxis_title="")
    c2.plotly_chart(_cromo(fig2), width="stretch")

    # Top pratos: o que mais te custou X e quanto seria o Y
    with st.expander("🔎 Ver economia prato a prato (top 30)"):
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
            disp[col] = disp[col].apply(lambda v: f"R$ {v:,.2f}")
        disp.columns = ["Prato", "Tipo", "Qtd", "Pago (X)",
                        "Custo em casa", "Economia (Y)", "% economia"]
        st.dataframe(disp, width="stretch", hide_index=True)

    st.caption(
        f"Com os percentuais atuais, fazer esses pratos em casa teria custado "
        f"~R$ {home_food:,.2f} em ingredientes vs. R$ {sav['paid'].sum():,.2f} pagos "
        f"no delivery — economia de **R$ {food_saved:,.2f}** só nos pratos, mais "
        f"R$ {fees:,.2f} de taxas evitadas."
    )


# ── Restaurants & items ───────────────────────────────────────────────────────

def restaurant_item_charts(df: pd.DataFrame, items_df: pd.DataFrame):
    st.subheader("🍔 Restaurantes e itens")
    aba = _abas(
        ["Por categoria", "Top restaurantes", "Itens mais pedidos", "Distribuição de custos"],
        key="aba_restaurantes",
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
            c1, c2 = st.columns(2)
            # Barra, não rosca: com o filtro padrão (Categoria = Restaurante)
            # a rosca virava uma fatia só marcando 100% — não dizia nada. Em
            # barra o par "gasto | pedidos" fica igual ao resto do dashboard.
            c1.plotly_chart(
                _bar(by_cat, "category", "total", "Gasto por categoria (R$)",
                     text=by_cat["total"].apply(lambda v: f"R${v:,.0f}")),
                width="stretch",
            )
            c2.plotly_chart(
                _bar(by_cat, "category", "pedidos", "Nº de pedidos por categoria",
                     color=PEDIDOS, text=by_cat["pedidos"]),
                width="stretch",
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
        c1.plotly_chart(f1, width="stretch")

        por_valor = by_rest.sort_values("total")
        f2 = _bar(por_valor, "total", "restaurant_name", "Por valor gasto (R$)",
                  text=por_valor["total"].apply(lambda v: f"R${v:,.0f}"), orient="h")
        f2.update_layout(yaxis_title="")
        c2.plotly_chart(f2, width="stretch")

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
        st.plotly_chart(fig, width="stretch")

    elif aba == "Distribuição de custos":
        if df.empty:
            return
        total_subtotal = df["subtotal"].sum()
        total_delivery = df["delivery_fee"].sum()
        total_service  = df["service_fee"].sum()
        total_discount = df["coupon_discount"].sum()
        total_paid     = df["total"].sum()

        # A pizza mostra apenas o que foi EFETIVAMENTE PAGO (soma = total).
        # Itens líquidos = subtotal − cupom (o cupom reduz o custo, não é custo).
        items_net = total_subtotal - total_discount

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
                textposition="inside",
                insidetextfont=dict(color="#0e1117", size=13),
                hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>",
                sort=False,
            )
        )
        fig.update_layout(
            title=f"Distribuição do que você pagou (total R$ {total_paid:,.2f})",
            template=PLOTLY_TEMPLATE,
            showlegend=True,
            legend=dict(orientation="h", y=-0.05, font=dict(color=INK_MUTE)),
        )
        st.plotly_chart(_cromo(fig), width="stretch")
        st.caption(
            f"💰 Itens (bruto): R$ {total_subtotal:,.2f}  ·  "
            f"🏷️ Economia em cupons: −R$ {total_discount:,.2f}  →  "
            f"Itens líquidos: R$ {items_net:,.2f}. "
            "O cupom **não** é custo — abate o valor dos itens."
        )


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

    with st.status(f"🛵 Coletando pedidos de **{profile}**…", expanded=True) as status:
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
            status.update(label="✅ Coleta concluída!", state="complete")
        else:
            status.update(label="⚠️ Coleta encerrou com avisos — confira o log abaixo.",
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
    st.subheader("📋 Tabela de pedidos")
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

    search = st.text_input("🔍 Buscar restaurante / status", "")
    if search:
        mask = display.apply(
            lambda col: col.astype(str).str.contains(search, case=False), axis=1
        ).any(axis=1)
        display = display[mask]

    sort_col = st.selectbox("Ordenar por", display.columns.tolist(), index=0)
    asc = st.checkbox("Crescente", value=False)
    display = display.sort_values(sort_col, ascending=asc)

    st.dataframe(display, width="stretch", height=400)

    # Export
    col1, col2 = st.columns([1, 5])
    csv = display.to_csv(index=False).encode("utf-8-sig")
    col1.download_button("⬇️ CSV", csv, "ifood_pedidos.csv", "text/csv")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        display.to_excel(writer, index=False, sheet_name="Pedidos")
    col2.download_button(
        "⬇️ Excel", buf.getvalue(),
        "ifood_pedidos.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.title("🛵 iFood — Histórico de Pedidos")
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
        "👤 Perfil", profiles,
        index=index,
        format_func=profile_display_name,
        help="Cada perfil é uma pessoa, com banco de dados separado.",
    )

    # Botão de coletar/atualizar pedidos deste perfil (roda o scraper)
    if st.sidebar.button(
        "⬇️ Coletar / atualizar pedidos",
        width="stretch",
        type="primary",
        help="Roda o scraper para este perfil. Abre o Chrome; resolva o "
             "captcha na janela se aparecer.",
    ):
        run_scraper(sel_profile)  # bloqueia, mostra status e dá rerun ao fim

    # Editor de nome de exibição (não renomeia arquivos/sessões)
    with st.sidebar.expander("✏️ Renomear este perfil"):
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
            "Clique em **⬇️ Coletar / atualizar pedidos** na barra lateral "
            f"ou rode `python scraper.py -p {sel_profile}`."
        )
        if st.button("🔄 Recarregar"):
            reload()
        return

    col_r, col_info = st.columns([1, 6])
    if col_r.button("🔄 Recarregar"):
        reload()
    col_info.caption(
        f"Base de dados: **{len(orders_df)}** pedidos · "
        f"Última coleta: {_fmt_coleta(orders_df['scraped_at'].max()) if 'scraped_at' in orders_df else '–'}"
    )

    filtered = sidebar_filters(orders_df)
    filtered_items = items_df[items_df["order_id"].isin(filtered["id"])] if not items_df.empty else pd.DataFrame()

    st.divider()
    show_kpis(filtered)
    st.divider()
    temporal_charts(filtered)
    st.divider()
    price_distribution(filtered)
    st.divider()
    cooking_savings(filtered, filtered_items)
    st.divider()
    restaurant_item_charts(filtered, filtered_items)
    st.divider()
    orders_table(filtered)


if __name__ == "__main__":
    main()
