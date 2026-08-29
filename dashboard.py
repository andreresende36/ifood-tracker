"""
iFood Order History Dashboard
─────────────────────────────
Run: streamlit run dashboard.py
"""

import hashlib
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
STATIC = Path(__file__).parent / "static"
# Nada de imagem embutida em `data:` URI: o markdown é reenviado pelo websocket
# a CADA rerun, e o wordmark em base64 são 63 KB em toda mexida de filtro.
# Servida de /app/static/, a imagem sai uma vez e o navegador guarda.
#
# O original de 2093px continua em assets/ (fonte da verdade); static/ leva a
# versão servida, dimensionada para o tamanho de tela — o wordmark aparece a
# 38px de altura, e 240px cobre 3x de DPR com folga. Regerar com:
#   cwebp -q 90 -resize 240 0 assets/ifood-logo.png -o static/ifood-logo.webp
LOGO = STATIC / "ifood-logo.webp"     # wordmark aparado, 5,6 KB
CAPA = STATIC / "capa-avenida.jpg"
ICONE = ASSETS / "ifood-icon.png"     # símbolo vazado em tile — legível a 16px


@st.cache_data(show_spinner=False)
def _static_url(nome: str) -> str:
    """
    URL de um arquivo de static/ com `?v=` do conteúdo.

    O `?v=` é a saída da armadilha de cache: /app/static/ é servido com cache
    longo, e sem ele trocar a imagem não trocaria o que se vê. Cacheado porque
    o hash exige ler o arquivo inteiro — a capa são 176 KB, e sem cache eles
    eram lidos e digeridos de novo a cada rerun.
    """
    caminho = STATIC / nome
    versao = hashlib.sha1(caminho.read_bytes()).hexdigest()[:8]
    return f"/app/static/{nome}?v={versao}"


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
    /* 6rem e não 2.25rem: o cabeçalho do Streamlit tem 60px e fica POR CIMA
       do conteúdo, então o respiro de 2.25rem do topo é o que sobra depois
       dele. Enquanto o h1 carregava o padding de fábrica isso passava raspando;
       com o h1 em placa, sem o padding, a primeira linha entrava debaixo dele. */
    .block-container { padding-top: calc(60px + 2.25rem); }
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
                                             letter-spacing: -0.02em; line-height: 1.2; }
    /* sem prefixo de tag: o rótulo é um <label>, não um <div> — com
       "div[...]" a regra nunca casava e rótulo e valor saíam no mesmo tom */
    [data-testid="stMetricLabel"] { opacity: 0.72; }

    /* ── Capa ──────────────────────────────────────────────────────────────
       Uma fotografia de largura inteira no topo da coluna de conteúdo, no
       feitio das capas do Notion. Ela sangra pelos dois lados e some por baixo
       do conteúdo em vez de terminar num corte.

       **Só na coluna de conteúdo.** A sidebar não recebe capa: ali estão os
       filtros, e uma foto atrás de controle é ruído atrás de trabalho.

       O sangramento cancela o padding horizontal do `.block-container`
       (80px, 16px no estreito) com margem negativa, e o vertical desconta só
       os 2.25rem do respiro — os 60px do cabeçalho do Streamlit ficam, porque
       aquela barra é OPACA e da cor da página: a capa passaria por baixo dela
       sem aparecer. Assim ela começa exatamente onde o conteúdo começa a ser
       visível, e rola para trás do cabeçalho como a do Notion faz.

       A transição suave é `mask-image`, não uma faixa de gradiente por cima:
       a máscara dissolve a própria foto no fundo da página, então funciona
       sobre qualquer superfície e não inventa uma quinta camada de cor. A
       imagem vai a zero em 100% e começa a ceder aos 55% — a parte de baixo é
       asfalto, e é ela que precisa sumir. O começo do esmaecimento é o que
       decide se o logo da bolsa ainda se lê: aos 45% ele saía a ~65% de
       opacidade; aos 55%, a ~80%.

       Altura em `36vh` com piso e teto — um quinto a mais que os 30vh do
       Notion, para caber a bolsa inteira e o topo do capacete. Numa coluna de
       1140px a foto renderiza com ~760px de altura e a janela mostra uns 43%
       dela; capa é recorte, não a foto inteira.

       O `min(36vh, 66vw)` existe pelo estreito: em 375px a foto renderiza com
       ~250px de altura, e uma caixa mais alta que isso faria o `cover`
       AMPLIAR a imagem para preencher — aí ela passa a ser cortada nas
       laterais, o `object-position` vertical deixa de ter efeito e o céu volta
       ao quadro. 66vw é a altura que a própria imagem tem naquela largura.

       O recorte (`object-position: center 31%`) prende a faixa opaca no
       capacete e na bolsa e mantém o CÉU fora do quadro — numa página quase
       preta, uma faixa de céu claro no topo seria a maior área de luz da tela.
       O que cede para a máscara é o asfalto. */
    /* Dois cancelamentos, e cada um tem dono: o container zera o gap de 16px
       que o bloco vertical põe antes do primeiro elemento visível (o bloco do
       <style> conta como irmão de altura zero), e a capa zera o respiro de
       2.25rem do topo da página. Sobram os 60px do cabeçalho, que é o que a
       gente quer manter. */
    .stElementContainer:has(.capa) { margin-top: -16px; }
    .capa {
        margin: -2.25rem -80px 0;
        height: clamp(180px, min(36vh, 66vw), 360px);
        overflow: hidden;
    }
    .capa img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 31%;
        -webkit-mask-image: linear-gradient(to bottom,
                            #000 0%, #000 55%, transparent 100%);
        mask-image: linear-gradient(to bottom,
                    #000 0%, #000 55%, transparent 100%);
    }
    /* 864px é a fronteira do próprio Streamlit: abaixo dela o padding lateral
       do `.block-container` cai de 80px para 16px. A capa continuava
       cancelando 80px de cada lado, então em 768px ela ficava 128px mais larga
       que a janela e a PÁGINA INTEIRA deslizava de lado — a rolagem
       horizontal que nenhum leitor de tablet pediu. O cancelamento acompanha
       o padding que existe de fato. */
    @media (max-width: 863.98px) {
        .capa { margin-left: -1rem; margin-right: -1rem; }
    }

    /* ── Cabeçalho-extrato ────────────────────────────────────────────────
       O degrau de Display deixou de servir ao nome da tela e passou a servir
       ao número. O logo já diz "iFood" e o h1 já dizia só qual tela é esta:
       gastar 44px nele era gastar o topo da escala num rótulo. A quantia
       ocupa o lugar — é o Metric Tile na escala de display, com a mesma
       anatomia (rótulo a 72% sobre valor em 700 com tracking negativo, sem
       moldura), grande o bastante para ser a primeira coisa lida. */
    /* A placa: o wordmark ao lado do nome da tela, no degrau de Section. A
       marca saiu do slot de logo do Streamlit — lá ela ficava sozinha num
       canto acima da sidebar, e repetida ao lado do título viraria duas
       marcas na mesma tela. */
    .placa { display: flex; align-items: center; gap: 0.7rem; margin: 0 0 0.15rem; }
    /* 38px contra um h1 de 28px: o wordmark é aparado sem margem, mas as
       letras ocupam ~60% da caixa (o resto é o traço acima), então casar a
       altura da imagem com a do texto deixa a marca menor do que ele. */
    .placa img { height: 38px; width: auto; display: block; }
    /* clamp no h1: em 375px "Histórico de pedidos" a 28px quebra em duas
       linhas e a marca ao lado fica centrada contra o vão. A 22px cabe numa
       linha só, e a placa continua sendo uma linha. */
    .block-container .placa h1 { font-size: clamp(22px, 2.2vw + 12px, 28px);
                                 font-weight: 600; letter-spacing: -0.14px;
                                 padding: 0; margin: 0; }
    .ledger { margin: 0.25rem 0 0; }
    /* Prefixo .block-container em toda regra de <p>: o Streamlit estiliza
       ".stMarkdown p" e ganha da classe sozinha — a linha do contrafactual
       saía em 16px, no meio do caminho entre o degrau que pedia e o caption
       de onde ela veio. */
    .block-container .ledger-rotulo { font-size: 14px; line-height: 22.4px;
                                      color: #e6e8ec; opacity: 0.72; margin: 0; }
    /* O veredito encosta na quantia na mesma linha de base: é atributo do
       número, não um parágrafo acima dele. No estreito a linha quebra e o
       veredito desce inteiro. */
    .ledger-linha { display: flex; flex-wrap: wrap; align-items: baseline;
                    column-gap: 1.5rem; row-gap: 0.25rem; margin: 0.1rem 0 0; }
    /* Figuras proporcionais: tabular-nums só onde há coluna para alinhar.
       O clamp segura o piso: "R$ 10.201,76" a 50px não cabe em 375px. */
    .ledger-valor { font-size: clamp(40px, 3.5vw, 50px); font-weight: 700;
                    letter-spacing: -0.025em; line-height: 1.1; color: #e6e8ec;
                    font-variant-numeric: proportional-nums; }
    /* Texto corrido, não inline-flex: como flex, ao quebrar em duas linhas o
       ícone e a ressalva viravam colunas e a frase se desmontava no estreito.
       O ícone se alinha pelo baseline como qualquer glifo, e o respiro vai na
       margem dele — num "gap" de flex ele caía também antes da vírgula
       ("acima da média , dentro da faixa"). */
    /* line-height explícito: sem ele o veredito herdava 1.6 do corpo e ficava
       com entrelinha diferente da linha do contrafactual, que é do mesmo
       tamanho e mora dois blocos abaixo. Um corpo, uma entrelinha. */
    .ledger-veredito { font-size: 20px; font-weight: 600; letter-spacing: -0.1px;
                       line-height: 1.4; }
    .ledger-icone { font-family: "Material Symbols Rounded"; font-size: 22px;
                    line-height: 1; vertical-align: -4px; margin-right: 0.35rem; }
    .ledger-ressalva { color: #8b8f9a; font-weight: 400; }
    /* A pergunta que é a razão de ser do produto saía em caption de 14px, com
       o mesmo peso da linha de cupons. Sobe para Headline; a cor fica só no
       valor evitável. */
    .block-container .ledger-casa { font-size: 20px; font-weight: 400;
                                    letter-spacing: -0.1px; line-height: 1.4;
                                    color: #8b8f9a; margin: 0.7rem 0 0.4rem; }
    .block-container .ledger-casa b { color: #3fbf90; font-weight: 600; }

    /* ── Escala de espaço ──────────────────────────────────────────────────
       O Streamlit empilha tudo num flex column com `gap: 16px`, e o resultado
       é uma coluna sem cadência: a nota de rodapé fica tão longe do número
       quanto o número fica do próximo assunto. Só o título de seção tinha
       ritmo próprio (2.5rem acima, 0.75rem abaixo); no resto da página havia
       um valor de espaço só, e espaço igual é hierarquia nenhuma.

       Três degraus, um papel para cada. O gap do framework não tem API, então
       cada degrau é escrito como um delta de `margin-top` sobre os 16px:

         cola   8px   (−8)   mesmo assunto: legenda e o que ela anota,
                             dois controles do mesmo grupo
         base  16px   ( 0)   irmãos comuns
         solta 28px   (+12)  troca de sub-bloco dentro da seção

       Abaixo de um título de seção os 0.75rem dele entram na conta: 20px para
       o que pertence ao título (subtítulo, seletor de painel) e 28px para o
       conteúdo que começa depois dele.

       Os seletores miram papel, não posição — "legenda", "controle",
       "conteúdo" — então reordenar a página não os quebra. */

    /* cola: a legenda é a letra miúda do bloco acima, nunca um bloco novo. */
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stCaptionContainer"]) {
        margin-top: -8px;
    }
    /* solta: o que vem depois de uma corrida de legendas começa assunto novo.
       Título e fio ficam de fora — os dois já trazem o próprio espaço. */
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stCaptionContainer"])
      + *:not(:has([data-testid="stCaptionContainer"])):not(:has([data-testid="stHeading"])):not(:has(hr)) {
        margin-top: 12px;
    }
    /* cola: o seletor de painel pertence ao título da seção — é ele que
       escolhe o que a seção mostra. A 28px do título e 16px do gráfico, o
       controle lia como legenda do gráfico, que é o oposto do que ele faz. */
    .block-container [data-testid="stVerticalBlock"] > *:has(> .stHeading)
      + *:has([data-testid="stButtonGroup"]),
    .block-container [data-testid="stVerticalBlock"] > *:has(> .stHeading)
      + *:has([data-testid="stTextInput"]) {
        margin-top: -8px;
    }
    /* cola: dois controles seguidos são um grupo de controle, não dois blocos. */
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stButtonGroup"]) + *:has([data-testid="stSlider"]),
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stTextInput"]) + *:has([data-testid="stSelectbox"]) {
        margin-top: -8px;
    }
    /* solta: depois do grupo de controle vem o conteúdo que ele governa. */
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stSlider"]) + *:not(:has([data-testid="stCaptionContainer"])),
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stButtonGroup"]) + *:not(:has([data-testid="stSlider"])),
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stSelectbox"]) + *:has([data-testid="stDataFrame"]) {
        margin-top: 12px;
    }
    /* Curso do slider: 11 paradas não precisam de 1280px. Na largura inteira
       da coluna, arrastar de 50% a 150% vira uma travessia, e o controle lê
       como régua da seção em vez de campo. 30rem é o mesmo teto do "top N". */
    .block-container [data-testid="stSlider"] { max-width: 30rem; }
    /* O valor flutuante do slider é posicionado ACIMA da trilha, e num curso
       de 30rem ele cai em cima do rótulo — que na largura inteira ficava bem
       à esquerda do polegar. O rótulo abre espaço para ele. */
    .block-container [data-testid="stSlider"] [data-testid="stWidgetLabel"] {
        margin-bottom: 1.25rem;
    }

    /* cola: os botões de exportar agem sobre a tabela logo acima. */
    .block-container [data-testid="stVerticalBlock"]
      > *:has([data-testid="stDataFrame"]):not(:has([data-testid="stExpander"])) + * {
        margin-top: -8px;
    }
    /* O cabeçalho-extrato tem cadência própria: as duas frases que respondem
       as perguntas da sessão andam juntas, e a letra miúda começa depois de um
       vão. É o único lugar da página em que a legenda não anota a linha
       imediatamente acima dela, então a regra geral é sobrescrita aqui —
       depois dela, para ganhar no desempate. */
    .block-container .stElementContainer:has(.ledger-casa) { margin-top: -8px; }
    .block-container .stElementContainer:has(.ledger-casa)
      + *:has([data-testid="stCaptionContainer"]) { margin-top: 12px; }

    /* ── Medida ────────────────────────────────────────────────────────────
       Numa coluna de 1140px o texto de 14px corria 166 caracteres por linha —
       mais que o dobro do que o olho volta a achar sozinho. A quebra de linha
       é a única coisa que o leitor não podia consertar: fonte e cor estavam
       certas, e ainda assim a legenda era uma travessia.

       72ch, medido em caracteres e não em pixels, porque a medida é do texto,
       não do container: a linha de 20px fica fisicamente mais larga que a de
       14px, e é isso mesmo — corpo maior carrega linha maior.

       O seletor pega só a prosa da coluna (`> .stElementContainer > .stMarkdown`).
       Rótulo de widget, título de gráfico, célula de tabela e texto de botão
       moram mais fundo e não têm medida a defender. */
    .block-container [data-testid="stVerticalBlock"]
      > .stElementContainer > .stMarkdown p {
        max-width: 72ch;
    }

    /* ── Texto claro sobre superfície escura ───────────────────────────────
       Fonte clara sobre fundo quase preto "sangra": o traço engorda e o miolo
       das letras fecha. A compensação é nos três eixos, e a entrelinha deste
       painel já era generosa (1.6), então falta o tracking. 0.01em em 14px é
       0,14px por letra — não se vê, se lê. */
    .block-container [data-testid="stCaptionContainer"] p,
    .block-container [data-testid="stMetricLabel"],
    .block-container [data-testid="stWidgetLabel"] p {
        letter-spacing: 0.01em;
    }

    /* ── Estados semânticos ────────────────────────────────────────────────
       O Streamlit pinta info/warning/error/success com quatro matizes que não
       são deste sistema: um azul quase igual — mas não igual — ao de contagem,
       um AMARELO (a quarta matiz que a paleta mediu e rejeitou, ΔE 4.4 contra
       o vermelho para daltonismo), e um vermelho e um verde fora dos pares de
       texto validados. Pior: os quatro saem como bloco preenchido de raio 0,
       a superfície mais barulhenta da tela — mais forte que a única ação
       preenchida que a página se permite. E eles aparecem o tempo todo: o
       recorte de abertura é um mês, e metade dos painéis abre sem série.

       Aqui o estado herda a anatomia da casa — superfície elevada, fio de 1px,
       raio 8px, texto de leitura — e a cor fica no fio, vinda das três matizes
       que já existem:

         nada a mostrar  neutro. "Não há dado" não é alarme nem grandeza, e cor
                         gasta aqui é cor que para de significar.
         algo errado     Dinheiro. Os avisos desta tela são sobre a conta não
                         fechar ou o dado não carregar — é do dinheiro que
                         falam.
         deu certo       Economia. A mesma leitura do chip de delta: verde é o
                         desfecho bom.

       O estado não depende da cor: o Streamlit já emite role="alert" para
       aviso e erro contra role="status" para info e sucesso, e as chamadas que
       carregam cor levam ícone. */
    [data-testid="stAlertContainer"] {
        /* o container ainda carregava a matiz do Streamlit no próprio `color`;
           nada herda dela hoje, e é uma matiz de fora esperando herdeiro */
        color: #e6e8ec;
        background: #161b24;
        border: 1px solid #242a35;
        border-radius: 8px;
    }
    [data-testid^="stAlertContent"] { color: #e6e8ec; }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
        border-color: #f0787f;
    }
    [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
        border-color: #3fbf90;
    }
    /* O ícone vem do parâmetro `icon=` e herda a cor do texto; aqui ele volta
       para a cor do estado, que é o que ele está anunciando. */
    [data-testid="stAlertContentWarning"] [data-testid="stAlertDynamicIcon"],
    [data-testid="stAlertContentError"] [data-testid="stAlertDynamicIcon"] {
        color: #f0787f;
    }
    [data-testid="stAlertContentSuccess"] [data-testid="stAlertDynamicIcon"] {
        color: #3fbf90;
    }

    /* ── Movimento ─────────────────────────────────────────────────────────
       A tela não tinha nenhum: toda transição do Streamlit vem com duração
       zero, e cada troca de estado era um corte seco.

       Não há momento focal aqui, e isso é decisão. É um painel local aberto de
       propósito, e o Streamlit **remonta a página inteira a cada rerun** — uma
       entrada autoral viraria coreografia em toda mexida de filtro, que é
       exatamente o que um painel de operação não pode fazer. O movimento aqui
       tem dois trabalhos, os dois de feedback.

       **1. O que está obsoleto recua.** Uma troca de painel leva ~985ms
       medidos, e durante esse tempo a tela mostrava o painel ANTERIOR como se
       fosse o atual — o único sinal era um spinner no canto superior direito,
       longe de onde a pessoa acabou de clicar. Enquanto o servidor recalcula,
       a coluna de conteúdo cai para 55%.

       A sidebar **não** recua: é onde estão os controles que a pessoa está
       segurando, e apagar o próprio controle lê como app quebrado. Recua o que
       está velho; fica aceso o que está na mão.

       O atraso de 220ms na descida é o que impede o pisca-pisca: rerun mais
       rápido que isso termina antes de a opacidade começar a andar. Na volta
       não há atraso — a chegada é imediata.

       **2. O controle reconhece o clique.** 120ms de cor, o bastante para o
       estado não ser um corte e pouco o bastante para não virar latência.

       Curva única, `cubic-bezier(0.16, 1, 0.3, 1)`: desaceleração natural,
       sem repique. */
    :root {
        --mov-feedback: 120ms;
        --mov-estado: 220ms;
        --mov-curva: cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* A volta é mais rápida que a ida e sem atraso nenhum: descer é um aviso
       que pode esperar, subir é o dado chegando. O `0ms` vai explícito para a
       assimetria não depender de sutileza de shorthand. */
    [data-testid="stMain"] {
        transition: opacity 160ms var(--mov-curva) 0ms;
    }
    /* O stStatusWidget só existe no documento enquanto há rerun em voo — é o
       sinal de "trabalhando" que o próprio framework emite, e usá-lo evita
       inventar um estado paralelo que possa dessincronizar. */
    body:has([data-testid="stStatusWidget"]) [data-testid="stMain"] {
        opacity: 0.55;
        transition-duration: var(--mov-estado);
        transition-delay: 220ms;
    }

    .block-container button, [data-testid="stSidebar"] button,
    [data-baseweb="tag"], label[data-baseweb="checkbox"] > span:first-child {
        transition: background-color var(--mov-feedback) var(--mov-curva),
                    border-color var(--mov-feedback) var(--mov-curva),
                    color var(--mov-feedback) var(--mov-curva);
    }

    /* O único movimento espacial da tela: o atalho de teclado entra deslizando
       de 8px acima. Ele salta de -9999px (a técnica de esconder acessível não
       muda), e o que anima é transform e opacidade. */
    #pular-para-conteudo {
        transform: translateY(-8px);
        opacity: 0;
        transition: transform var(--mov-estado) var(--mov-curva),
                    opacity var(--mov-estado) var(--mov-curva);
    }
    #pular-para-conteudo:focus { transform: none; opacity: 1; }

    /* Movimento reduzido tira o deslocamento e mantém o que significa. Como o
       sistema inteiro é opacidade e cor, sobra só o atalho de teclado — e é
       essa a prova de que aqui não há movimento decorativo: com a preferência
       ligada, quase nada muda. */
    @media (prefers-reduced-motion: reduce) {
        #pular-para-conteudo { transform: none; }
    }

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

    /* Atalho de teclado, criado pelo localize.html. Fica fora da tela até
       receber foco — a sidebar tem ~340 nós antes do primeiro número. */
    #pular-para-conteudo {
        position: absolute; left: -9999px; top: 0; z-index: 9999;
        background: #161b24; color: #e6e8ec; border: 1px solid #242a35;
        border-radius: 8px; padding: 8px 12px; font-size: 14px; text-decoration: none;
    }
    #pular-para-conteudo:focus { left: 8px; top: 8px; }

    /* O segmento ativo do seletor é TEXTO vermelho sobre uma tinta de 10% —
       não é superfície preenchida. Com o tom de ação (#c9101d) dava 3,09:1;
       com o tom de texto, 6,7:1. E ganha peso 600, para o estado não depender
       só da cor. */
    [data-testid="stBaseButton-segmented_controlActive"] { color: #f0787f !important; }
    [data-testid="stBaseButton-segmented_controlActive"] p { font-weight: 600; }

    /* O verde do delta do KPI é o do Streamlit; a paleta da casa tem o seu.
       O texto e a seta já vinham corrigidos — a TINTA DE FUNDO do chip não, e
       ela ainda era `rgba(61,213,109,.2)`, um verde de fora da paleta atrás de
       um texto da paleta. */
    [data-testid="stMetricDelta"] svg { fill: #3fbf90; }
    [data-testid="stMetricDelta"] { color: #3fbf90;
                                    background: rgba(25, 158, 112, 0.18); }

    /* O chip de `código` saía no verde de sucesso do Streamlit (#5ce488) sobre
       um cinza que não é dos três. Verde aqui significa o contrafactual — a
       Regra do Papel vale para o cromo também, e um nome de arquivo não é
       grandeza nenhuma. Fica em tinta de leitura sobre a superfície elevada. */
    .block-container code, [data-testid="stSidebar"] code {
        color: #e6e8ec;
        background: #161b24;
    }

    /* A escada de elevação diz três superfícies e o render tinha cinco: o
       botão secundário saía em #10151e na sidebar e #131720 no conteúdo, dois
       cinzas quase iguais entre a base e a elevada, e nenhum dos dois é da
       paleta. Um valor só, o documentado. */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    .block-container button[data-testid="stBaseButton-secondary"] {
        background-color: #161b24;
    }

    /* O valor do slider flutua sobre a superfície, não sobre o polegar — em
       #c9101d dava 3,22:1 como texto. */
    [data-testid="stSliderThumbValue"] { color: #f0787f; }

    /* Texto e placeholder do campo de data vinham a 40% e 60% de opacidade:
       3,32:1 e 4,79:1. Placeholder é texto para a WCAG 1.4.3. */
    [data-testid="stDateInputField"] { color: rgba(230, 232, 236, 0.72) !important; }
    [data-testid="stDateInputField"]::placeholder { color: rgba(230, 232, 236, 0.72); }

    /* A superfície do campo. O token do sistema (`input-select`) manda
       `surface-raised`, e o BaseWeb entregava `surface-base`: preenchimento a
       1,02:1 contra a sidebar e borda a 1,21:1 — o campo não era uma forma,
       era um contorno que quase não existia. */
    [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        background-color: #161b24;
    }
    /* Entrelinha: o campo saía em 19,6px enquanto o menu dele saía em 22,4 —
       a mesma tipografia com dois valores, e nenhum dos dois escolhido. */
    [data-baseweb="select"], [data-baseweb="select"] input { line-height: 22.4px; }

    /* O foco pousava no <input> de 2px, não no campo: o anel de 2px do sistema
       virava uma lasca de ~6×24 colada no nome, dentro de um alvo de 260×40 —
       o mesmo lugar, e quase o mesmo desenho, do cursor de texto que já tinha
       sido apagado dali. Vai para a caixa inteira, com o raio da caixa. */
    [data-testid="stSelectbox"] input:focus-visible,
    [data-testid="stMultiSelect"] input:focus-visible { outline: none; }
    [data-testid="stSelectbox"]:has(input:focus-visible) [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"]:has(input:focus-visible) [data-baseweb="select"] > div {
        outline: 2px solid #ea1d2c; outline-offset: 2px; border-radius: 8px;
    }
    /* Clicar em qualquer ponto do campo abre o menu, mas o ponteiro virava
       I-beam: o sistema operacional anunciando "digite aqui" num escolhedor. */
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSelectbox"] [data-baseweb="select"] * { cursor: pointer; }
    /* Hover não mudava nada — nem fundo, nem fio, nem chevron. */
    [data-baseweb="select"] > div:hover { border-color: #3a4250; }

    /* O menu: sem sombra, como o resto do sistema. Ela existia porque o
       popover saía em `surface-base` sobre a sidebar `surface-sidebar` —
       1,02:1 — e a sombra fazia o trabalho que o tom deveria fazer. Sobe para
       `surface-raised` com fio de 1px e a separação passa a ser tonal. */
    [data-baseweb="popover"] {
        background-color: #161b24; box-shadow: none;
        border: 1px solid #242a35; border-radius: 8px;
    }
    /* A lista interna vinha com superfície própria (`surface-base`) e passava
       por cima da do popover; transparente, quem manda é a caixa. */
    [data-baseweb="popover"] ul { background-color: transparent; }
    /* A opção escolhida saía numa pílula `#95a4c1` — cinza-azulado default do
       Streamlit, fora da paleta, marcando a escolha a 1,26:1. Vai para a mesma
       anatomia do segmento ativo: tinta de 10% do vermelho, texto em Dinheiro
       Texto e peso 600, para o estado não depender só de cor. */
    [data-baseweb="popover"] li[role="option"] { padding-left: 14px; }
    /* A pílula é um <div> DENTRO do <li>, e é ela que carregava o cinza fora
       da paleta. Apagada, o estado passa a ser do próprio <li>. */
    [data-baseweb="popover"] li[role="option"] > div { background-color: transparent; }
    [data-baseweb="popover"] li[role="option"]:hover { background-color: #1e242e; }
    [data-baseweb="popover"] li[aria-selected="true"] {
        background-color: rgba(234, 29, 44, 0.10);
        color: #f0787f; font-weight: 600;
    }

    /* O seletor de perfil é um escolhedor, não um campo de digitar — mas o
       BaseWeb o monta como combobox: o valor sai num <div> e sobra um <input>
       de 2px logo depois dele. Focado com o menu fechado, o cursor de texto
       piscava colado no "é" de "André", parecendo traço solto da letra (no
       multiselect isso não acontece: lá o input tem 18px e o cursor cai em
       espaço livre).

       Some em todo estado, inclusive de menu aberto: enquanto nada foi
       digitado o input continua com 2px e o cursor continua colado no nome,
       e é justamente com o menu aberto que se olha para ele. Quem digitar
       para filtrar vê as letras aparecerem — o que se perde é só o traço
       piscando, e ele aqui custa mais do que entrega. No multiselect não se
       mexe: lá o input tem 18px, o cursor cai em espaço livre e digitar é o
       caminho normal com dezenas de restaurantes. */
    [data-testid="stSelectbox"] input { caret-color: transparent; }

    /* Raio dos chips de filtro: o BaseWeb entrega 6.08px, fora da escala.
       O sistema tem um raio só. */
    [data-baseweb="tag"] { border-radius: 8px; }

    /* Mesma correção no chip de código e na caixa do checkbox, que vinham
       com 4px de fábrica. */
    .block-container code, [data-testid="stSidebar"] code { border-radius: 8px; }
    label[data-baseweb="checkbox"] > span:first-child { border-radius: 8px; }
    /* O chip de delta do KPI vem em pílula (9999px) — fora da escala também. */
    [data-testid="stMetricDelta"] { border-radius: 8px; }

    /* A proibição de sombra vale para o que o Streamlit desenha sozinho: a
       barra flutuante de ferramentas da tabela vem com box-shadow de fábrica,
       e era a única sombra viva na tela inteira. */
    [data-testid="stElementToolbarButtonContainer"],
    [data-testid="stElementToolbar"] { box-shadow: none; }
    /* A barra da tabela só aparece no hover, e por isso escapou de toda
       revisão de cor até agora: superfície #131720 e ícones #fafafa, dois
       valores que não são da paleta. Estado de hover também é estado. */
    [data-testid="stElementToolbarButtonContainer"] { background: #161b24; }
    [data-testid="stElementToolbar"] svg { color: #e6e8ec; }
    /* Os ícones do multiselect (limpar tudo, abrir a lista) vinham em
       rgba(250,250,250,.6) — um branco de fora da paleta atrás de opacidade.
       Cromo que acompanha vai em tinta recuada, como o resto. */
    [data-testid="stMultiSelect"] svg { color: #8b8f9a; }
    /* A caixa do checkbox vinha em #10151e — o mesmo cinza intermediário que
       saiu dos botões. */
    label[data-baseweb="checkbox"] > span:first-child { background-color: #161b24; }

    /* Alvos de toque, o piso. O ✕ de um chip de filtro nasce com 8,8×8,8 e os
       ícones de "limpar tudo" com 21×21 — a área que a WCAG 2.5.8 (AA) exige
       é 24×24. Este é o valor do PONTEIRO FINO: com mouse, 24 basta e o
       widget não precisa ser redesenhado. O dedo tem outro tamanho, e o que
       ele pede está no bloco `pointer: coarse` lá embaixo. */
    [data-baseweb="tag"] { min-height: 26px; }
    /* O polegar do slider nasce com 12x12 e é ELE que carrega a tinta. Padding
       no próprio elemento pinta o círculo inteiro: a bolinha saía com 24 de
       diâmetro, e a margem negativa que devolvia o espaço tirava o polegar do
       centro da trilha — ficava 6px acima dela. A área cresce num ::after
       transparente, que não pinta e não desloca: o polegar fica no lugar que o
       baseweb calculou, com 12 de desenho e 24 de alvo. */
    [data-testid="stSlider"] [role="slider"]::after {
        content: ""; position: absolute; inset: -6px;
    }
    [data-baseweb="tag"] span[role="presentation"] {
        min-width: 24px; min-height: 24px;
        display: inline-flex; align-items: center; justify-content: center;
        margin: -6px -4px -6px 0;   /* cresce a área sem crescer o desenho */
    }
    /* O chevron do campo: `svg[role="button"]` NÃO casa com o que o BaseWeb
       emite — o ícone sai como `svg[data-baseweb="icon"]`, sem role, dentro de
       um pai sem role. A regra antiga media `padding: 0px` no render: era CSS
       morto desde sempre. */
    [data-baseweb="select"] svg[data-baseweb="icon"] {
        box-sizing: content-box; padding: 4px; margin: -4px;
    }

    /* ── Tela estreita e dedo ─────────────────────────────────────────────
       A cena de uso continua sendo o casal na mesma tela em casa, e o
       desktop é onde ela acontece — nada aqui muda o que já está resolvido lá.
       O que muda é que a mesma tela agora é aberta no celular e no tablet, e
       nesses dois o painel tinha três problemas de verdade, todos medidos no
       render: a página deslizava de lado, o par de gráficos ficava com 360px
       por gráfico (e o trio, com 235px), e todo alvo de toque era do tamanho
       do mouse.

       As duas fronteiras não são de catálogo, são do que existe aqui:

         864px  onde o próprio Streamlit troca o padding lateral de 80px por
                16px — a tela deixa de ter margem para gastar.
         640px  onde ele para de empilhar as colunas lado a lado. Abaixo
                disso, o layout já é uma coluna só e não há par a desfazer.

       E o dedo entra por `pointer: coarse`, não por largura: um tablet em
       paisagem tem 1024px e continua sendo dedo, enquanto uma janela estreita
       no desktop continua sendo mouse. Largura decide layout; ponteiro decide
       alvo. */

    @media (max-width: 863.98px) {
        /* A tabela guarda a largura que tinha antes de o aparelho girar, e uma
           tabela de 746px numa coluna de 343px é a página inteira deslizando
           de lado. Presa à coluna, a grade se remede sozinha (o canvas volta
           a 341px) e volta a rolar por dentro, que é onde a rolagem lateral
           pode existir. O `!important` é contra a largura em linha que o
           próprio componente escreve. */
        [data-testid="stDataFrame"] { max-width: 100%; }
        [data-testid="stDataFrameResizable"] { max-width: 100% !important; }
        /* O gráfico guarda a largura em que foi desenhado (`layout.width`, a
           limitação documentada no DESIGN.md), e no celular quem dispara isso
           não é arrastar a janela — é GIRAR o aparelho. Voltando de paisagem
           para retrato, um gráfico de 780px fica dentro de uma coluna de
           343px. Ele rola por dentro da própria caixa; o que não pode é a
           página inteira deslizar de lado atrás dele. */
        [data-testid="stPlotlyChart"] { overflow-x: auto; }
        /* Trava de segurança para o resto: o rótulo que o Plotly escreve fora
           da área de plotagem (`cliponaxis=False`) invade a margem, e aqui a
           margem é de 16px. No desktop sobra respiro para isso; aqui, sem a
           trava, alguns pixels de um número empurram a página inteira.
           Rolagem lateral de página é sempre defeito — a de dentro de um
           gráfico ou de uma tabela, não. */
        [data-testid="stMain"] { overflow-x: hidden; }
        /* O título de seção entra na mesma escala fluida da placa. A 28px em
           375px, "E se você tivesse cozinhado em casa?" ocupa três linhas. */
        .block-container h2 { font-size: clamp(22px, 2.2vw + 12px, 28px); }
    }

    /* Entre 640 e 864 — o tablet em retrato — o Streamlit ainda põe tudo lado
       a lado, e é aí que o layout do desktop se desfaz: três gráficos com
       235px cada, quatro KPIs com 172px. O par e o trio de gráficos passam a
       ocupar a largura inteira, um debaixo do outro; os KPIs viram grade de
       dois, que é o formato em que o rótulo ainda cabe em cima do valor. */
    @media (min-width: 641px) and (max-width: 863.98px) {
        [data-testid="stHorizontalBlock"]
          > [data-testid="stColumn"]:has([data-testid="stPlotlyChart"]),
        [data-testid="stHorizontalBlock"]
          > [data-testid="stColumn"]:has([data-testid="stDataFrame"]) {
            flex: 1 1 100%;
            min-width: 100%;
        }
        /* 0.5rem é metade do gap de 16px do bloco horizontal: dois por linha
           com o vão entre eles descontado uma vez só. */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
          > [data-testid="stColumn"] {
            flex: 1 1 calc(50% - 0.5rem);
            min-width: calc(50% - 0.5rem);
        }
    }

    /* No celular o KPI fica um por linha, como o Streamlit já faz: numa coluna
       de 163px, "R$ 10.201,76" a 26,4px não cabe, e o produto falha se o
       número não couber. Uma coluna, o número inteiro. */

    @media (pointer: coarse) {
        /* 44×44 é o alvo do AAA (WCAG 2.5.8) e é o que o dedo pede. Onde o
           controle é solto — polegar do slider, seta de um campo, botão —
           a área vai a 44 sem o desenho crescer: padding com margem negativa
           do mesmo tamanho. */
        [data-testid="stSlider"] [role="slider"]::after { inset: -16px; }
        [data-baseweb="select"] svg[data-baseweb="icon"] {
            padding: 11px; margin: -11px;
        }
        /* O campo do escolhedor nascia com 40px enquanto os dois botões logo
           abaixo dele já tinham 44: a regra de altura mira `button` e
           `summary`, e o BaseWeb não usa nenhum dos dois. */
        [data-baseweb="select"] > div, [data-baseweb="input"] > div {
            min-height: 44px;
        }
        /* Botão, seletor de painel e cabeçalho de expansor: altura mínima de
           44px. O desenho não muda no desktop — nenhuma destas regras existe
           lá. */
        .block-container button, [data-testid="stSidebar"] button,
        [data-testid="stExpander"] summary {
            min-height: 44px;
        }
        /* O "?" da ajuda nasce com 16×16 e é a única maneira de ler a nota
           que ele guarda — no mouse ela aparece no hover, no dedo só no
           toque. A área vai a 24 sem o ícone crescer. */
        [data-testid="stTooltipHoverTarget"] {
            box-sizing: content-box; padding: 4px; margin: -4px;
        }
        /* A caixa do checkbox tem 16px; quem recebe o toque é a linha inteira
           do rótulo. */
        label[data-baseweb="checkbox"] { min-height: 44px; align-items: center; }
        /* O ✕ do chip é a exceção, e é uma exceção de forma: 44 não cabe num
           chip sem transformar o filtro numa fileira de botões. Ele cresce o
           quanto o chip permite — 36 no lugar de 24 —, e o chip cresce junto
           para o alvo não vazar por cima do vizinho. */
        [data-baseweb="tag"] { min-height: 36px; }
        [data-baseweb="tag"] span[role="presentation"] {
            min-width: 36px; min-height: 36px;
            margin: -6px -6px -6px 0;
        }
        /* Abrir e fechar a barra de filtros é o gesto mais frequente do
           celular — ali a barra nasce recolhida — e o controle nasce com
           28×28 dentro de um cabeçalho de 56px. */
        /* Um é botão, o outro é a caixa em volta de um botão — os dois
           seletores existem porque o Streamlit pendura o `data-testid` em
           lugares diferentes de cada lado do gesto. */
        button[data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapseButton"] button {
            width: 44px; height: 44px;
        }
    }

    /* Sem hover não há descoberta: a barra de ferramentas da tabela (buscar,
       baixar, tela cheia) vive em opacidade 0 até o mouse chegar, e no dedo
       o mouse nunca chega. Onde não há hover, ela fica visível. */
    @media (hover: none) {
        [data-testid="stElementToolbar"] { opacity: 1; }
    }

    /* iframe utilitário do localize.html — carrega e roda, mas não ocupa espaço */
    .st-key-localize_iframe { display: none; }
</style>
""", unsafe_allow_html=True)


LOCALIZE = Path(__file__).parent / "static" / "localize.html"
def _localize_widgets():
    """
    Costura de idioma e acessibilidade sobre o que o Streamlit emite e não
    expõe por API: texto interno de widget, atributos ARIA, `lang` do
    documento, estado do seletor segmentado, marco `main` e atalho de teclado.
    Roda no DOM pai via MutationObserver.

    O script vive em static/localize.html porque st.components.v1.html está
    depreciado e st.iframe recebe URL, não HTML inline. Servido pelo Streamlit
    na mesma origem, o iframe alcança window.parent.document — o que um data:
    URI (origem opaca) não permitiria.

    DUAS PEGADINHAS DE CACHE, as duas custaram uma sessão de depuração:

    1. O servidor estático do Streamlit fixa o tamanho do arquivo no start.
       Editar o .html com o servidor no ar faz ele servir o conteúdo novo
       TRUNCADO no tamanho antigo — o script quebra na metade, sem erro
       visível no console da página. Reinicie o Streamlit após editar.
    2. O navegador guarda /app/static/ com cache longo. Daí o `?v=` com o
       hash do arquivo: mudou o script, muda a URL, e nem o usuário nem o
       desenvolvedor ficam com a versão velha rodando.
    """
    # st.iframe recusa height=0 (o components.html antigo aceitava), então o
    # iframe vai com 1px dentro de um container escondido por CSS. display:none
    # não impede o iframe de carregar nem o script de rodar.
    if not LOCALIZE.exists():
        return
    with st.container(key="localize_iframe"):
        # A barra inicial é obrigatória: sem ela o st.iframe não reconhece
        # como URL e embute o caminho como se fosse HTML cru.
        st.iframe(_static_url(LOCALIZE.name), height=1)

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
# O mesmo vermelho tem três papéis e três limiares de contraste, e usar o tom
# errado no papel errado reprova:
#   marca de dado   → #ea1d2c sobre #0e1117 = 4,24:1, e o limiar é 3:1  (ok)
#   fundo de ação   → #c9101d com texto branco = 5,87:1                 (config.toml)
#   texto de ênfase → #ea1d2c como TEXTO = 4,24:1, e o limiar é 4,5:1   (reprova)
# Daí este terceiro tom, só para texto vermelho sobre superfície escura.
DINHEIRO_TEXTO = "#f0787f"   # 6,93:1 sobre #0e1117
PEDIDOS  = "#3987e5"   # contagem de pedidos/itens
ECONOMIA = "#199e70"   # economia e custo cozinhando em casa
ECONOMIA_TEXTO = "#3fbf90"   # o par do DINHEIRO_TEXTO: 8,0:1 sobre #0e1117
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

# Toda marca leva o seu valor. O teto de 8 rótulos que existia aqui apagava o
# número justamente nos painéis mais densos — "Top 15/30", "Por mês" — onde
# ler no eixo custa mais.
#
# O corpo do rótulo é FIXO, e o Plotly é proibido de encolher (constraintext
# "none"): com "auto", o número que não cabe dentro da barra sai para fora no
# mesmo tamanho, em vez de espremer a série inteira até o pior caso. Foi por
# isso que `uniformtext` não serviu aqui — ele iguala todos pelo menor.
ROTULO_CORPO = 11

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
    # \u00a0 e não espaço comum: com a medida em 72ch a legenda quebrava entre
    # o "R$" e o número, e uma quantia partida em duas linhas não é quantia.
    return ("R\\$\u00a0" if md else "R$\u00a0") + corpo


# ── Data loading ──────────────────────────────────────────────────────────────

# Sem ttl: o banco é um arquivo local que só muda quando alguém coleta, e tanto
# "Coletar" quanto "Recarregar" chamam load_data.clear(). O ttl de 60s não
# protegia de nada e criava uma janela em que "Recarregar" podia não recarregar.
# O perfil conjunto não é um banco: é a leitura dos dois. A chave não pode
# colidir com nome de arquivo em data/, daí os underscores.
CASAL = "__casal__"


@st.cache_data
def load_data(profile: str = "default"):
    if profile == CASAL:
        return _load_casal()
    db = Database(profile=profile)
    if not db.db_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    db.init()
    orders = db.get_orders_df()
    items  = db.get_items_df()
    if not orders.empty and "status" in orders.columns:
        orders["status"] = orders["status"].map(_translate_status)
    return orders, items


def _load_casal():
    """
    Os dois bancos lidos juntos, com o dono de cada pedido preservado.

    A restrição do produto nunca foi "não somar": é que **nenhum pedido mude
    de dono**. Por isso a coluna `pessoa` nasce aqui, na leitura, e não é
    opcional — sem ela a soma seria um número sem procedência, que é o que a
    decisão de 28/08 temia.

    Os `id` são prefixados pela chave do perfil porque as duas bases numeram a
    partir de 1: sem isso o pedido 7 da Carol casaria com os itens do pedido 7
    do André, e a tela mostraria o prato de um no gasto do outro. É o único
    lugar do código onde um id vira texto, e é de propósito.
    """
    ordens, itens = [], []
    for chave in [p for p in list_profiles() if p != CASAL]:
        o, i = load_data(chave)
        if o.empty:
            continue
        o = o.copy()
        o["pessoa"] = profile_display_name(chave)
        o["id"] = chave + "#" + o["id"].astype(str)
        if not i.empty:
            i = i.copy()
            i["order_id"] = chave + "#" + i["order_id"].astype(str)
            itens.append(i)
        ordens.append(o)
    if not ordens:
        return pd.DataFrame(), pd.DataFrame()
    orders = pd.concat(ordens, ignore_index=True)
    items = pd.concat(itens, ignore_index=True) if itens else pd.DataFrame()
    return orders, items


def reload():
    """
    Relê o banco DENTRO desta execução, sem `st.rerun()`.

    O rerun era o que apagava os filtros. O Streamlit descarta o estado de
    widget que não foi montado na execução em curso, e `st.rerun()` aqui
    interrompe o script ANTES da barra lateral existir: na execução seguinte
    os filtros voltavam vazios — a tela pulava do mês corrente para o
    histórico inteiro. E o rerun não comprava nada: `_acoes_do_perfil` roda
    antes de `load_data(sel_profile)`, então limpar o cache aqui já faz a
    leitura desta mesma execução pegar o banco novo. Uma execução em vez de
    duas.
    """
    load_data.clear()


# ── Sidebar filters ───────────────────────────────────────────────────────────

FILTER_NAMES = [
    "flt_years", "flt_months", "flt_use_range", "flt_date_range",
    "flt_pessoa", "flt_cats", "flt_status", "flt_dow", "flt_pr", "flt_rest",
]


def _clear_filters():
    """
    Limpa os filtros REMONTANDO os widgets: incrementa um nonce que entra na
    key de cada widget. Como a key muda, o Streamlit cria instâncias novas
    (estado vazio) — só assim os chips somem da tela. Apenas zerar o
    session_state não força o re-render visual do multiselect.
    """
    n = st.session_state.get("flt_nonce", 0)
    espelho = st.session_state.setdefault("flt_espelho", {})
    for name in FILTER_NAMES:
        st.session_state.pop(f"{name}_{n}", None)  # descarta estado antigo
        espelho.pop(f"{name}_{n}", None)           # e o espelho junto
    st.session_state["flt_nonce"] = n + 1


def _filter_default(key: str, options: list, wanted=()) -> list:
    """
    Estado inicial de um multiselect de filtro.

    Faz três coisas:
    1. Descarta seleções que não existem mais nas opções — acontece ao trocar
       de perfil (ex.: 'Ago' selecionado no André, mas a Carol não tem pedidos
       em agosto). Sem isso o Streamlit quebra com valor fora da lista.
    2. Espelha a seleção fora do estado de widget, e restaura dali quando ele
       some. O Streamlit descarta o estado de todo widget que não foi montado
       numa execução, e `st.rerun()` chamado antes da barra lateral existir
       (renomear perfil, e antes também recarregar e coletar) fazia
       exatamente isso: a tela voltava sem filtro nenhum, do mês corrente
       para o histórico inteiro, com os chips ainda pintados na tela. O
       espelho é uma chave comum de session_state, que rerun não apaga.
    3. Só na PRIMEIRA renderização da sessão, pré-seleciona `wanted`. Depois
       disso devolve vazio, senão o botão 'Limpar filtros' remontaria os
       widgets já preenchidos de novo e nunca limparia nada. O espelho não
       atrapalha isso: limpar troca o nonce, e a chave nova não tem espelho.
    """
    espelho = st.session_state.setdefault("flt_espelho", {})

    atual = st.session_state.get(key)
    if isinstance(atual, list):
        mantidos = [v for v in atual if v in options]
        if len(mantidos) != len(atual):
            st.session_state[key] = mantidos
        espelho[key] = mantidos
        return []  # com a key viva, o Streamlit ignora o default de qualquer jeito

    if key in espelho:
        return [v for v in espelho[key] if v in options]

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

    # Pessoa — só existe no perfil conjunto, e vem primeiro: dentro da visão
    # dos dois, "de quem" é o recorte mais grosso que existe, acima de
    # categoria e de status.
    if "pessoa" in df.columns:
        pessoas = sorted(df["pessoa"].dropna().unique().tolist())
        sel_pessoa = st.sidebar.multiselect(
            "Pessoa", pessoas, placeholder="Os dois", key=k("flt_pessoa"),
            default=_filter_default(k("flt_pessoa"), pessoas),
        )
        if sel_pessoa:
            df = df[df["pessoa"].isin(sel_pessoa)]

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




# ── Sinal do mês ──────────────────────────────────────────────────────────────

# Separador dos runs de fato nas legendas. O U+2060 (word joiner) proíbe a
# quebra entre o espaço da esquerda e o "·": sem ele, com a medida em 72ch, a
# linha nova começava com o marcador em vez de com o próximo fato.
SEP = "\u3000\u2060·\u3000"

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
        return "trending_up", DINHEIRO_TEXTO, f"{pct:.0f}% acima da média", " — e acima de todo mês anterior"
    if s["realizado"] < s["minimo"]:
        return "trending_down", ECONOMIA_TEXTO, f"{pct:.0f}% abaixo da média", " — e abaixo de todo mês anterior"
    if s["delta"] >= 0.02:
        return "trending_up", DINHEIRO_TEXTO, f"{pct:.0f}% acima da média", ", dentro da faixa dos outros meses"
    if s["delta"] <= -0.02:
        return "trending_down", ECONOMIA_TEXTO, f"{pct:.0f}% abaixo da média", ", dentro da faixa dos outros meses"
    return "trending_flat", INK_MUTE, "no mesmo patamar dos meses anteriores", ""




# ── Chart helpers ─────────────────────────────────────────────────────────────

# A barra de ferramentas do Plotly (zoom, lasso, "download plot as png") é
# cromo de outro sistema: não serve a um painel de agregados, e em 375px ela
# pousa POR CIMA do título do gráfico. Some — o dado fica.
#
# "responsive": True foi tentado aqui para o gráfico seguir a janela e NÃO
# funciona neste arranjo: o componente do Streamlit grava layout.width na
# figura, e o autosize do Plotly nunca chega a valer. Ver a limitação
# registrada no DESIGN.md.
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


def _rotulos(valores, fmt: str = "auto"):
    """
    O texto que vai na marca.

    "auto" decide pelo dtype, e nesta base a decisão é limpa: toda grandeza
    inteira é contagem (pedidos, itens, quantidade) e toda grandeza fracionária
    é dinheiro (total, ticket médio, economia, custo em casa). Contagem também
    sai em formato brasileiro — `1.234`, não `1234` nem `1,234`.
    """
    if fmt == "auto":
        fmt = "int" if pd.api.types.is_integer_dtype(valores) else "brl"
    if fmt == "int":
        return valores.map(lambda v: f"{int(v):,}".replace(",", "."))
    return valores.map(lambda v: _brl(v, 0))


def _bar(df, x, y, title, color=DINHEIRO, text=None, xtype=None, orient=None,
         fmt="auto"):
    # O rótulo é o padrão, não um extra que cada chamada precisa lembrar de
    # passar: sem valor na marca, o gráfico manda o leitor ao eixo para toda
    # leitura. `text=` continua aceito para quando o rótulo não é o valor.
    if text is None:
        text = _rotulos(df[x] if orient == "h" else df[y], fmt)
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
        textfont=dict(color=INK_MUTE, size=ROTULO_CORPO),
        insidetextfont=dict(color=SURFACE, size=ROTULO_CORPO),
        # Sem isto o Plotly encolhe o número para caber dentro da barra, e a
        # barra mais curta define o corpo de toda a série.
        constraintext="none",
        # O rótulo da maior barra encosta na borda da área de plotagem; sem
        # isto ele é recortado ali em vez de invadir a margem.
        cliponaxis=False,
        # 2px de respiro entre barras vizinhas em vez de borda desenhada
        marker_line_color=SURFACE, marker_line_width=2,
    )
    if xtype:
        fig.update_xaxes(type=xtype)
    fig.update_layout(showlegend=False)
    return _cromo(fig)


def painel_vazio(df, x, saida: str = "para ver o padrão dentro do mês, "
                 "use *Dia da semana* ou *Heatmap*") -> bool:
    """
    O estado vazio da casa — um componente, não um `st.info("Sem dados")`.

    Um período só no filtro (o recorte padrão, mês corrente): nenhum dos dois
    gráficos do par é gráfico — são duas barras gigantes repetindo valores que
    o bloco de KPIs já mostra. A nota diz o que HÁ, onde está o número, e um
    caminho nomeado — `saida` muda com a dimensão que esvaziou o painel, para
    não sugerir "Dia da semana" a quem esbarrou numa categoria única.

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
        f"indicadores acima. Para comparar, amplie o filtro; {saida}."
    )
    return True


def _barra(alvo, df, x, y, title, color=DINHEIRO, text=None, **kw):
    """Uma barra do par lado a lado, dentro da coluna que a recebe."""
    alvo.plotly_chart(
        _bar(df, x, y, title, color=color, text=text, **kw),
        width="stretch", config=PLOT_CONFIG,
    )


def _line(df, x, y, title, fmt="auto"):
    fig = px.line(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE, markers=True,
                  text=_rotulos(df[y], fmt))
    fig.update_traces(line_color=DINHEIRO, line_width=2,
                      marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                      # acima do ponto: ao lado, o rótulo cavalga a própria
                      # linha no trecho em que ela sobe.
                      textposition="top center",
                      textfont=dict(color=INK_MUTE, size=ROTULO_CORPO),
                      cliponaxis=False)
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


# Fragmento: o seletor de painel e o modo de visualização não saem daqui.
# Trocar de aba reexecutava a página inteira só para desenhar outro gráfico.
@st.fragment
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
        if painel_vazio(by_year, "year"):
            return
        c1, c2 = st.columns(2)
        _barra(c1, by_year, "year", "total", "Gasto por ano (R$)",
               xtype="category")
        _barra(c2, by_year, "year", "pedidos", "Pedidos por ano",
               color=PEDIDOS, xtype="category")

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
            if painel_vazio(by_period, "period"):
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
        if painel_vazio(by_p, "period"):
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
             color=PEDIDOS),
        width="stretch", config=PLOT_CONFIG,
    )
    c2.plotly_chart(
        _bar(pr_data, "price_range", "total", "Gasto total por faixa (R$)"),
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


# Cacheado porque tem dois consumidores no MESMO rerun — a linha do topo e a
# seção — com os mesmos argumentos: sem isto, os 437 itens são classificados
# duas vezes por render.
@st.cache_data(show_spinner=False)
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




def _periodo_label(df: pd.DataFrame) -> str:
    """Nomeia o recorte que a quantia cobre, para o número não ficar solto."""
    if "ordered_at" not in df or df.empty:
        return ""
    dt = pd.to_datetime(df["ordered_at"], errors="coerce").dropna()
    if dt.empty:
        return ""
    ini, fim = dt.min(), dt.max()
    if (ini.year, ini.month) == (fim.year, fim.month):
        return f"{MESES_EXTENSO[fim.month]} de {fim.year}"
    return (f"{MESES_EXTENSO[ini.month][:3]}/{ini.year} – "
            f"{MESES_EXTENSO[fim.month][:3]}/{fim.year}")


def ledger_head(orders_df: pd.DataFrame, df: pd.DataFrame, items_df: pd.DataFrame,
                pessoa: str = ""):
    """
    O topo da tela é o número, não o nome da tela.

    Um bloco só responde as duas perguntas com que a sessão começa — "gastamos
    demais este mês?" e "dava para ter cozinhado?" — penduradas na quantia que
    as motiva, em vez de três blocos empilhados no mesmo peso.

    A hierarquia desce em degraus visíveis: quantia (display) → veredito e
    contrafactual (20px) → o resto do recorte (14px). Antes os dois veredictos
    saíam em caption, com o mesmo peso da linha de cupons.

    O sinal do mês roda sobre o histórico INTEIRO e a quantia sobre o filtro
    da barra lateral; a nota de rodapé declara isso, senão limpar o filtro de
    mês deixa a frase falando de agosto ao lado de um total do ano.
    """
    entregues, fora = _entregues(df)
    total  = entregues["total"].sum()
    n      = len(entregues)
    ticket = entregues["total"].mean() if n else 0

    # No conjunto, quem o rótulo nomeia sai do DADO, não do perfil escolhido:
    # com o filtro de pessoa em uma só, "Casal" ao lado de um total que é de
    # uma pessoa é exatamente a troca de dono que o produto proíbe. O nome do
    # perfil volta quando o recorte contém todo mundo que ele contém.
    if "pessoa" in entregues.columns and not entregues.empty:
        quem = sorted(entregues["pessoa"].dropna().unique().tolist())
        todos = sorted(orders_df["pessoa"].dropna().unique().tolist())
        if quem and quem != todos:
            pessoa = " e ".join(quem)

    periodo = _periodo_label(entregues)
    # O nome entra no rótulo da quantia, e não só na gaveta: o dinheiro na
    # tela é de UMA pessoa por vez, e no celular a gaveta abre recolhida — sem
    # isto o número mais importante do produto é anônimo, e quem senta do lado
    # lê o gasto do outro como se fosse da casa.
    # O separador leva word joiner pelo mesmo motivo do SEP das legendas: se o
    # rótulo quebrar no estreito, a linha nova começa pelo próximo fato e não
    # pelo "·". Aqui o espaço é o normal, não o ideográfico — este é um rótulo
    # curto, não uma fileira de fatos.
    rotulo = " \u2060· ".join(p for p in ("Total gasto", pessoa, periodo) if p)

    s = month_signal(orders_df)
    veredito_html = ""
    ressalva = ""
    if s and not s["sem_base"]:
        icone, cor, veredito, ressalva = _veredito(s)
        # O veredito é sempre do mês de referência; a quantia ao lado é do
        # recorte da barra lateral. Quando os dois coincidem — o filtro de
        # abertura — o rótulo da quantia já nomeia o mês e repeti-lo seria
        # ruído. Quando não coincidem, "12% acima da média" encostado num
        # total de dez meses lê como se fosse dos dez: aí o escopo vai na
        # frente da frase, não na nota de rodapé dois blocos abaixo.
        mes_ref = f"{MESES_EXTENSO[s['ref'].month]} de {s['ref'].year}"
        escopo = "" if periodo == mes_ref else f"Em {mes_ref.lower()}, "
        # A cor fica só no veredito; escopo e ressalva vão na mesma linha, em
        # tinta recuada e peso normal. Pintar a frase inteira faz o vermelho
        # parar de significar alguma coisa — e tirar a ressalva daqui perde
        # justamente a frase mais forte que a tela sabe dizer.
        veredito_html = (
            f'<span class="ledger-veredito" style="color:{cor}">'
            f'<span class="ledger-icone">{icone}</span>'
            f'<span class="ledger-ressalva">{escopo}</span>{veredito}'
            f'<span class="ledger-ressalva">{ressalva}</span></span>'
        )

    st.markdown(
        f'<div class="ledger">'
        f'<p class="ledger-rotulo">{rotulo}</p>'
        f'<div class="ledger-linha">'
        f'<span class="ledger-valor">{_brl(total)}</span>{veredito_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    if n and not items_df.empty:
        _, total_saved, _, _, _, total_pago = _economia_evitavel(df, items_df, _escala_atual())
        if total_pago > 0:
            pct = total_saved / total_pago * 100
            st.markdown(
                f'<p class="ledger-casa">Cerca de <b>{_brl(total_saved, 0)}</b> disso '
                f'era evitável cozinhando em casa — {pct:.0f}% do que foi pago. '
                f'Estimativa; a conta está logo abaixo.</p>',
                unsafe_allow_html=True,
            )

    # Duas notas, e não uma: a primeira é o recorte filtrado, a segunda é o
    # histórico completo. Emendadas numa linha só, os dois escopos viram um.
    plural = "s" if n != 1 else ""
    recorte = (
        f"**{n}** pedido{plural} entregue{plural}"
        f"{SEP}Ticket médio **{_brl(ticket, md=True)}**"
        f"{SEP}Economizado em cupons **{_brl(entregues['coupon_discount'].sum(), md=True)}**"
        f"{SEP}Taxas de entrega e serviço "
        f"**{_brl(entregues['delivery_fee'].sum() + entregues['service_fee'].sum(), md=True)}**"
    )
    if not fora.empty:
        recorte += (
            f"{SEP}{len(fora)} pedido{'s' if len(fora) > 1 else ''} cancelado, recusado ou "
            f"sem status somando {_brl(fora['total'].sum(), md=True)} ficaram fora do total"
        )
    st.caption(recorte)

    if s is None:
        return
    nome = f"{MESES_EXTENSO[s['ref'].month]} de {s['ref'].year}"
    if s["sem_base"]:
        st.caption(
            f"Ainda não dá para dizer se {nome} está caro: são precisos pelo menos "
            f"{MIN_MESES_BASE} meses anteriores para formar uma média, e há {s['meses']}."
        )
        return

    ate = f"até o dia {s['corte']}" if s["parcial"] else "no mês fechado"
    nota = (
        f"Média dos {s['meses']} meses anteriores {ate}: "
        f"**{_brl(s['media'], md=True)}** · faixa de **{_brl(s['minimo'], md=True)}** a "
        f"**{_brl(s['maximo'], md=True)}**"
    )
    if s["projecao"]:
        nota += f"{SEP}No ritmo atual o mês fecha em **{_brl(s['projecao'], md=True)}** — estimativa"
    nota += SEP + "Comparação sobre o histórico completo, sem os filtros da barra lateral"
    st.caption(nota)


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

    c1, c2, c3, c4 = st.columns(4)
    # O chip diz a queda no GASTO, não a alta na economia: por isso é negativo,
    # e com delta_color="inverse" o negativo sai em verde com seta para baixo —
    # economizar é o desfecho bom.
    #
    # O sinal tem que ser o hífen ASCII. Com o "−" tipográfico (U+2212) o
    # Streamlit não reconhece o número como negativo, trata como alta e pinta
    # de vermelho com seta para CIMA: era esse o chip que anunciava a economia
    # como se fosse alarme.
    queda = -(total_saved / total_pago * 100) if total_pago else 0
    c1.metric("Economia total",      _brl(total_saved),
              f"{queda:.0f}% no gasto", delta_color="inverse")
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
              orient="h")
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
    fig2.update_traces(textposition="outside",
                       textfont=dict(color=INK_MUTE, size=ROTULO_CORPO),
                       marker_line_color=SURFACE, marker_line_width=2,
                       cliponaxis=False, constraintext="none")
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

# Fragmento: o seletor de painel e os dois "Mostrar top N" são desta seção.
# Arrastar o top N repintava o dashboard inteiro a cada passo do slider.
@st.fragment
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
            if painel_vazio(
                by_cat, "category",
                saida="para ver onde o dinheiro foi, use *Top restaurantes* "
                      "ou *Itens mais pedidos*",
            ):
                return
            c1, c2 = st.columns(2)
            c1.plotly_chart(
                _bar(by_cat, "category", "total", "Gasto por categoria (R$)"),
                width="stretch", config=PLOT_CONFIG,
            )
            c2.plotly_chart(
                _bar(by_cat, "category", "pedidos", "Nº de pedidos por categoria",
                     color=PEDIDOS),
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
                  "Por frequência", color=PEDIDOS, orient="h")
        f1.update_layout(yaxis_title="")
        c1.plotly_chart(f1, width="stretch", config=PLOT_CONFIG)

        por_valor = by_rest.sort_values("total")
        f2 = _bar(por_valor, "total", "restaurant_name", "Por valor gasto (R$)",
                  orient="h")
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
                   color=PEDIDOS, orient="h")
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

        # O invariante na tela, e não só no comentário: a composição TEM que
        # somar o total. Hoje soma por construção; se alguém trocar a base de
        # novo, quem olha descobre aqui em vez de somando de cabeça.
        if abs(sum(values) - total_paid) > 0.01:
            st.warning(
                f"A composição soma {_brl(sum(values), md=True)} e o total pago é "
                f"{_brl(total_paid, md=True)}. As fatias abaixo não fecham — trate o "
                "gráfico como aproximação até isto ser corrigido.",
                icon=":material/warning:",
            )

        fig = go.Figure(
            go.Pie(
                labels=labels, values=values,
                # As 3 matizes validadas; identidade vem da legenda, não da cor
                # sozinha. O âmbar antigo (#f59e0b) reprovava na faixa de
                # luminosidade para fundo escuro.
                marker=dict(colors=[DINHEIRO, PEDIDOS, ECONOMIA],
                            line=dict(color=SURFACE, width=2)),
                hole=0.55,
                # Toda fatia leva o seu valor, inclusive as lascas de 2-4%: a
                # identidade continua vindo da legenda, e o número deixa de
                # depender do hover. Valor e não porcentagem — a porcentagem
                # está no hover e o produto é sobre quanto foi pago.
                text=[_brl(v, 0) for v in values],
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

    # Sem `st.rerun()` pela mesma razão do reload(): ele interrompe o script
    # antes dos filtros existirem e o Streamlit descarta o estado deles.
    load_data.clear()
    st.toast("Dados atualizados!" if ok else "Coleta finalizada com avisos.")


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

# max_entries: uma planilha por combinação de filtro, ordenação e busca, e a
# busca é texto livre — sem teto, o cache cresceria uma entrada por tecla.
@st.cache_data(show_spinner=False, max_entries=8)
def _to_excel(display: pd.DataFrame) -> bytes:
    """
    A planilha do botão de export.

    `st.download_button` exige os bytes na mão para desenhar o botão, então a
    planilha era montada em TODO rerun — 122 ms de openpyxl por mexida de
    filtro, de aba, de slider, para um arquivo que quase nunca é baixado.
    Cacheada pelo recorte, ela é montada uma vez por combinação de filtro,
    ordenação e busca, e os reruns seguintes só reaproveitam os bytes.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        display.to_excel(writer, index=False, sheet_name="Pedidos")
    return buf.getvalue()


# Fragmento: os widgets desta seção — busca, ordenação e sentido — só mexem
# nesta tabela. Sem o fragmento, marcar "Crescente" reexecutava a página
# inteira (KPIs, contrafactual e os painéis de gráfico) e o navegador
# remontava tudo. Com ele, o rerun para na fronteira da seção.
@st.fragment
def orders_table(df: pd.DataFrame):
    st.header(":material/table_rows: Tabela de pedidos")
    if df.empty:
        st.info("Nenhum pedido encontrado com os filtros atuais.")
        return

    cols = ["ordered_at", "restaurant_name"]
    if "pessoa" in df.columns:
        cols.append("pessoa")
    if "category" in df.columns:
        cols.append("category")
    cols += [
        "status", "total", "subtotal", "delivery_fee", "service_fee",
        "coupon_discount", "year", "month_name", "day_name", "time_slot", "price_range",
    ]
    display = df[cols].copy()
    names = ["Data/hora", "Restaurante"]
    if "pessoa" in df.columns:
        names.append("Pessoa")
    if "category" in df.columns:
        names.append("Categoria")
    names += [
        "Status", "Total (R$)", "Subtotal", "Entrega", "Serviço", "Desconto",
        "Ano", "Mês", "Dia", "Turno", "Faixa",
    ]
    display.columns = names

    # O rótulo promete exatamente as colunas que a busca varre — foi por
    # prometer demais que "10" já casou com um valor de desconto.
    campos_busca = ("restaurante, pessoa, categoria ou status"
                    if "pessoa" in df.columns
                    else "restaurante, categoria ou status")
    search = st.text_input(f"Buscar {campos_busca}", "")
    if search:
        # regex=False: o nome do item traz "(", "+" e "*" o tempo todo, e um
        # parêntese solto derrubava a metade de baixo da tela com um traceback
        # do pyarrow no lugar da tabela e dos botões de export.
        # E só as colunas que o rótulo promete: o apply varria as 14, inclusive
        # as numéricas, então "10" casava com um valor de desconto.
        alvos = [c for c in ("Restaurante", "Pessoa", "Categoria", "Status") if c in display]
        # Rede de segurança: a busca é a única entrada de texto livre da tela e
        # já derrubou a metade de baixo uma vez. Se algo nela falhar, a tabela
        # continua de pé e quem digitou lê um aviso, não um traceback.
        try:
            mask = (
                display[alvos]
                .apply(lambda col: col.astype(str).str.contains(search, case=False, regex=False))
                .any(axis=1)
            )
            display = display[mask]
        except Exception:
            st.warning(
                "Não consegui aplicar essa busca; mostrando todos os pedidos do filtro.",
                icon=":material/warning:",
            )
        else:
            if display.empty:
                st.caption(
                    f"Nenhum pedido com “{search}” em {campos_busca}."
                )

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

    col2.download_button(
        "Excel", _to_excel(display),
        "ifood_pedidos.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

# Largura útil da gaveta e custo de um segmento vazio (padding interno + o vão
# entre segmentos), medidos no render a 1440px.
SIDEBAR_UTIL = 260
SEG_VAO, SEG_PADDING, SEG_CHAR = 8, 24, 8.0


def _cabe_em_segmentos(nomes: list[str]) -> bool:
    """
    O escolhedor vira segmentado quando os nomes cabem lado a lado.

    Trocar de pessoa é uso normal, não manutenção: com os nomes à vista o
    gesto é um só e ninguém precisa abrir um menu para descobrir que a outra
    pessoa existe. Mas o nome é editável em "Renomear este perfil", e nada
    impede alguém digitar trinta caracteres — aí o segmento trunca e o
    escolhedor passa a esconder justamente o que deveria mostrar. Quando não
    couber, o menu volta: é a forma que aguenta nome de qualquer tamanho.

    A conta **soma** as larguras em vez de dividir a barra em partes iguais,
    porque o segmento se dimensiona pelo próprio texto: medido no render,
    "André" dá 70px e "Carolina" 83, não 130 cada. Dividir igual reprovava
    três nomes que cabem com folga.
    """
    if len(nomes) < 2:
        return False
    largura = sum(len(n) * SEG_CHAR + SEG_PADDING for n in nomes)
    return largura + SEG_VAO * (len(nomes) - 1) <= SIDEBAR_UTIL


AJUDA_PERFIL = ("Cada perfil é uma pessoa, com banco de dados separado. "
                "O conjunto lê os dois, sem misturar de quem é cada pedido.")


def _nome_do_perfil(chave: str) -> str:
    """O conjunto não tem banco, então também não tem nome em profiles.json."""
    return "Casal" if chave == CASAL else profile_display_name(chave)


def _acoes_do_perfil(sel_profile: str, profiles: list[str]):
    """
    Coletar, recarregar e renomear — as ações que agem sobre UM banco.

    No conjunto não há banco para coletar nem nome para renomear, e botão
    cinza que não faz nada ocupa espaço sem dizer o que fazer. Sobra
    "Recarregar", que relê os dois, e uma linha dizendo onde a coleta mora.
    Coleta continua sendo um ato de uma pessoa, com o Chrome à vista.
    """
    if sel_profile == CASAL:
        if st.sidebar.button(
            "Recarregar", icon=":material/refresh:", width="stretch",
            help="Relê os bancos locais, sem ir ao iFood.",
        ):
            reload()
        pessoas = [_nome_do_perfil(p) for p in profiles if p != CASAL]
        st.sidebar.caption(
            "A coleta é feita em cada pessoa: escolha "
            + " ou ".join(f"**{n}**" for n in pessoas)
            + " para atualizar os pedidos dela."
        )
        return

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
            st.success("Nome atualizado!", icon=":material/check_circle:")
            st.rerun()
        st.caption(f"Banco: `{sel_profile}` (chave fixa, não muda)")


def _seletor_de_perfil(profiles: list[str], index: int) -> str:
    """A pessoa cujo dinheiro a tela mostra. Segmentado quando cabe."""
    nomes = [_nome_do_perfil(p) for p in profiles]
    if not _cabe_em_segmentos(nomes):
        return st.sidebar.selectbox(
            "Perfil", profiles, index=index,
            format_func=_nome_do_perfil, help=AJUDA_PERFIL,
        )
    escolha = st.sidebar.segmented_control(
        "Perfil", profiles,
        default=profiles[index],
        format_func=_nome_do_perfil,
        key="perfil_seg",
        help=AJUDA_PERFIL,
    )
    # segmented_control permite desmarcar; sem pessoa não há tela
    return escolha or profiles[index]


@st.fragment
def resumo_e_contrafactual(orders_df: pd.DataFrame, filtered: pd.DataFrame,
                           filtered_items: pd.DataFrame, pessoa: str):
    """O topo da tela e a seção que ele anuncia, no mesmo fragmento.

    Uma linha só separa o resumo da análise. Entre as seções o trabalho é do
    espaço e do degrau de título — fio em toda troca de assunto vira grade.
    """
    ledger_head(orders_df, filtered, filtered_items, pessoa)
    st.divider()
    cooking_savings(filtered, filtered_items)


def main():
    # A capa vem antes de tudo, na largura inteira da coluna.
    if CAPA.exists():
        st.markdown(
            f'<div class="capa"><img src="{_static_url(CAPA.name)}" '
            f'alt="Entregador do iFood numa moto, visto de trás, atravessando uma '
            f'avenida da cidade com a bolsa térmica nas costas">'
            f'</div>',
            unsafe_allow_html=True,
        )

    # A marca fica ao lado do nome da tela, não no slot de logo do Streamlit:
    # lá ela mora num canto acima da sidebar, longe do título, e nas duas
    # posições ao mesmo tempo seriam duas marcas na mesma tela.
    #
    # O h1 é escrito à mão porque st.title não aceita nada ao lado; o alt sai
    # de verdade aqui, sem depender do conserto que o localize.html fazia no
    # alt="Logo" genérico do st.logo.
    if LOGO.exists():
        st.markdown(
            f'<div class="placa"><img src="{_static_url(LOGO.name)}" '
            f'alt="iFood"><h1>Histórico de pedidos</h1></div>',
            unsafe_allow_html=True,
        )
    else:
        st.title("Histórico de pedidos")
    _localize_widgets()  # idioma, ARIA, estado do seletor, marco e atalho

    # Seletor de perfil — um banco por pessoa, mais a leitura conjunta
    profiles = list_profiles() or ["default"]
    # default sempre primeiro → abre por padrão ao iniciar o dashboard
    if "default" in profiles:
        profiles = ["default"] + [p for p in profiles if p != "default"]
    # O conjunto vai por último, e só existe quando há o que somar. Ele nunca
    # é o padrão de abertura: a sessão começa em quem abriu o painel.
    if len(profiles) > 1:
        profiles = profiles + [CASAL]
    # run.sh passa o perfil escolhido por aqui; sem ele, abre no primeiro
    initial = os.environ.get("IFOOD_PROFILE", "")
    index = profiles.index(initial) if initial in profiles else 0
    sel_profile = _seletor_de_perfil(profiles, index)

    _acoes_do_perfil(sel_profile, profiles)

    st.sidebar.divider()

    orders_df, items_df = load_data(sel_profile)

    if orders_df.empty:
        # No conjunto não há o que coletar: o vazio ali significa que nenhuma
        # das pessoas tem pedido, e a saída é coletar em cada uma.
        if sel_profile == CASAL:
            st.warning(
                "Nenhum pedido em nenhuma das pessoas. Escolha uma delas na "
                "barra lateral e clique em **Coletar / atualizar pedidos**.",
                icon=":material/inbox:",
            )
        else:
            st.warning(
                f"Nenhum pedido no perfil **{_nome_do_perfil(sel_profile)}**. "
                "Clique em **Coletar / atualizar pedidos** na barra lateral "
                f"ou rode `python scraper.py -p {sel_profile}`.",
                icon=":material/inbox:",
            )
        # Aqui o rerun é necessário: o banco já foi lido acima nesta execução,
        # e sem ele a tela continuaria mostrando o vazio até o próximo clique.
        # É seguro: o espelho de `_filter_default` sobrevive a rerun.
        if st.button("Recarregar", icon=":material/refresh:"):
            reload()
            st.rerun()
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
    # O resumo e o contrafactual vão no MESMO fragmento, e não em dois: o
    # controle de otimismo mora na seção de baixo mas alimenta o veredito de
    # cima, então separá-los congelaria o número do topo enquanto o de baixo
    # anda. Juntos, arrastar o otimismo repinta só estes dois blocos — antes
    # repintava também os gráficos e a tabela, que o controle não toca.
    resumo_e_contrafactual(orders_df, filtered, filtered_items,
                           _nome_do_perfil(sel_profile))
    temporal_charts(filtered)
    restaurant_item_charts(filtered, filtered_items)
    orders_table(filtered)


if __name__ == "__main__":
    main()
