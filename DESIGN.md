---
name: iFood Order Tracker
description: Painel local e escuro que transforma o histórico de delivery de um casal em um número que dá para agir.
colors:
  dinheiro: "#ea1d2c"
  pedidos: "#3987e5"
  economia: "#199e70"
  surface-base: "#0e1117"
  surface-raised: "#161b24"
  surface-sidebar: "#0b0e14"
  border-hairline: "#242a35"
  border-sidebar: "#1e242e"
  ink-primary: "#e6e8ec"
  ink-muted: "#8b8f9a"
  chart-grid: "#22252e"
  chart-axis: "#3a3f4b"
  link: "#5b9df0"
  scrollbar-thumb: "#2b323e"
  scrollbar-thumb-hover: "#3a4250"
typography:
  display:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: "52.8px"
    letterSpacing: "normal"
  headline:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: "24px"
    letterSpacing: "-0.1px"
  title:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: "21.6px"
    letterSpacing: "-0.09px"
  metric:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "26.4px"
    fontWeight: 700
    lineHeight: "normal"
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "22.4px"
    letterSpacing: "normal"
  label:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "22.4px"
    letterSpacing: "normal"
  icon:
    fontFamily: "Material Symbols Rounded"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: "1"
    letterSpacing: "normal"
rounded:
  md: "8px"
  chrome-scrollbar: "6px"
  chrome-focus: "4px"
spacing:
  section-above: "2.5rem"
  section-below: "0.75rem"
  block-above: "1.75rem"
  block-below: "0.5rem"
  page-top: "2.25rem"
components:
  button-primary:
    backgroundColor: "{colors.dinheiro}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "4px 12px"
    typography: "{typography.body}"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-primary}"
    rounded: "{rounded.md}"
    padding: "4px 12px"
    typography: "{typography.body}"
  input-select:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-primary}"
    rounded: "{rounded.md}"
  metric-tile:
    backgroundColor: "{colors.surface-base}"
    textColor: "{colors.ink-primary}"
    typography: "{typography.metric}"
---

# Design System: iFood Order Tracker

## Overview

**Creative North Star: "O Extrato Honesto"**

A tela é um extrato que não poupa quem olha. O número grande existe porque
precisa doer, não porque é bonito: a razão de ser do produto é fazer um casal
pedir menos, e nada na interface pode competir com a quantia. Tudo o que não é
dado recua — a grade dos gráficos fica a um passo do fundo, os eixos não
repetem o que o título já disse, e o cromo do navegador (seleção, rolagem,
foco) é tingido para não parecer peça de outro sistema.

O caráter é contido e preciso. A marca não aparece em blocos nem em faixas:
ela vive no logo do canto, no anel de foco, no rastro da seleção de texto e na
única ação preenchida da tela. Os controles, por outro lado, se declaram —
borda visível em cada campo, ação principal em vermelho cheio — porque este é
um painel para agir, não para contemplar. A tensão é deliberada: superfícies
quietas, controles presentes.

Escuro não por moda, mas pela cena de uso: duas pessoas em casa, à noite,
sentadas na mesma tela, decidindo se pedem ou cozinham.

**Key Characteristics:**
- Fundo quase preto em três camadas tonais; zero sombra
- Três matizes com papel fixo — cor significa grandeza, nunca posição
- Cromo recessivo: grade, eixos e rótulos sempre abaixo do dado
- Vermelho da marca raro, alto impacto: uma ação por tela
- Rótulo recua (72% de opacidade), valor avança (700, −0.02em)

## Colors

Uma paleta escura de três camadas com exatamente três matizes de dado, cada
uma amarrada a uma grandeza — validada em conjunto para daltonismo e contraste
contra a superfície real, não escolhida a olho.

### Primary
- **Dinheiro** (`{colors.dinheiro}`): o vermelho do próprio logo do iFood.
  Marca tudo que é valor pago — gasto por ano, mês, dia, faixa, categoria,
  ticket médio, valor por restaurante — e é também a única cor de ação
  preenchida da interface, o anel de foco e o rastro da seleção de texto.

### Secondary
- **Pedidos** (`{colors.pedidos}`): contagem. Quantos pedidos, quantos itens,
  frequência por restaurante. Nunca dinheiro.

### Tertiary
- **Economia** (`{colors.economia}`): o contrafactual — economia estimada por
  prato e o custo de cozinhar em casa. É a cor da pergunta que o produto faz.

### Neutral
- **Superfície Base** (`{colors.surface-base}`): o plano do conteúdo e a
  superfície contra a qual toda a paleta foi validada. Trocar este valor
  invalida a paleta.
- **Superfície Elevada** (`{colors.surface-raised}`): campos, botões
  secundários, blocos de controle.
- **Superfície Lateral** (`{colors.surface-sidebar}`): a sidebar, um passo
  mais escura que o conteúdo — é o que separa filtro de dado, sem moldura.
- **Fio de Borda** (`{colors.border-hairline}`) e **Fio Lateral**
  (`{colors.border-sidebar}`): 1px, a separação quando o tom sozinho não basta.
- **Tinta Primária** (`{colors.ink-primary}`): todo o texto de leitura (15,4:1
  sobre a base).
- **Tinta Recuada** (`{colors.ink-muted}`): rótulos de eixo, texto de gráfico,
  tudo que acompanha sem disputar.
- **Grade** (`{colors.chart-grid}`) e **Eixo** (`{colors.chart-axis}`): o cromo
  dos gráficos, deliberadamente a um passo do fundo.

### Named Rules

**A Regra do Papel.** Cor segue a grandeza, nunca a posição do gráfico nem o
ranking da série. Dinheiro é sempre vermelho, contagem é sempre azul,
contrafactual é sempre verde — em todos os painéis, em todos os filtros. Um
gráfico que inverta isso está errado, mesmo que fique bonito.

**A Regra das Três Matizes.** O teto é três, e é medido, não estético: com o
vermelho da marca fixo, todo quarto matiz reprovou na separação para
daltonismo (amarelo↔vermelho ΔE 4.4; violeta↔azul 1.9). Mais de três
categorias vira barra, não fatia de pizza.

**A Regra do Zero que Recua.** Em escala sequencial sobre fundo escuro, o passo
do zero vai para perto da superfície, nunca para o claro. O contrário
transforma uma matriz quase vazia num bloco branco gritando na tela.

## Typography

**Fonte única:** Source Sans (fallback `system-ui`, `-apple-system`,
`sans-serif`) — a sans do próprio Streamlit, mantida de propósito.

**Character:** Sem voz de display, sem serifa, sem monoespaçada de fantasia. A
personalidade vem do peso e do tamanho, não da escolha de família: num painel
de leitura, uma fonte que chama atenção para si rouba do número.

### Hierarchy
- **Display** (700, 44px/52.8px): o título da tela, uma vez por página.
- **Headline** (600, 20px/24px, −0.1px): título de seção ("Análise temporal").
- **Title** (600, 18px/21.6px, −0.09px): título de bloco dentro da seção.
- **Metric** (700, 26.4px, −0.02em): o valor do KPI. O tracking negativo
  aperta os dígitos para o número ler como uma unidade, não como uma fileira.
- **Body** (400, 14px/22.4px): texto corrido, legendas, ajuda.
- **Label** (400, 14px, opacidade 0.72): rótulo de KPI e de campo.
- **Icon** (Material Symbols Rounded, 22px): o ícone é uma fonte, não tipo de
  leitura. É o mesmo conjunto que o Streamlit carrega para o parâmetro
  `icon=`; num trecho de HTML próprio, a família vai declarada à mão.

### Named Rules

**A Regra do Rótulo que Recua.** No par rótulo/valor, o rótulo vai a 72% de
opacidade e o valor fica em 700. Se os dois saem no mesmo tom, o olho tem que
escolher — e a varredura para.

**A Regra da Moeda.** Dinheiro sai em formato brasileiro — ponto no milhar,
vírgula no decimal (`R$ 1.724,05`). Vale para texto, rótulo de barra, tick de
eixo e hover: os três últimos são formatados pelo Plotly, que precisa de
`separators=",."` no layout. O padrão do Python é o americano, e uma tela em
português com `R$ 1,724.05` denuncia que ninguém olhou.

**A Regra do Dígito.** `tabular-nums` só onde números se alinham na vertical
(tabela, ticks de eixo). No valor grande e solto do KPI, figuras
proporcionais: dígitos de largura fixa fazem `121` parecer frouxo em corpo
grande.

## Layout

Coluna única larga (`layout="wide"`) com sidebar fixa de filtros. Um único
grupo de filtros governa tudo abaixo — nunca filtro dentro de card.

Ritmo assimétrico e deliberado: 2.5rem acima de um título de seção contra
0.75rem abaixo (1.75rem / 0.5rem no nível de bloco). O cabeçalho gruda no
próprio conteúdo em vez de flutuar no meio do vão. O topo da página respira
2.25rem.

Densidade segue a prioridade, não a simetria: três KPIs primários com valor
cheio em colunas iguais, e as duas grandezas de apoio (cupons, taxas) descem
para uma linha de legenda. Cinco tiles iguais numa linha é default de
framework — e no espaço disponível truncava o próprio número.

Painéis de análise são um seletor + um painel montado sob demanda, nunca todos
de uma vez: painel oculto tem container de largura zero, e gráfico renderizado
ali calcula área negativa.

No estreito a sidebar recolhe sozinha (`initial_sidebar_state="auto"`);
expandida ela cobriria a tela e a primeira coisa visível seriam filtros, não
dados.

## Elevation & Depth

**Sem sombra alguma.** A profundidade é inteiramente tonal: três superfícies
(`surface-sidebar` → `surface-base` → `surface-raised`) mais um fio de 1px onde
o tom sozinho não separa. Gráficos são transparentes sobre a página — o Plotly
não desenha superfície própria.

### Named Rules

**A Regra do Tom, não da Sombra.** Elevação se expressa por camada de cor e fio
de 1px. Nenhum elemento ganha `box-shadow` — nem em repouso, nem em hover. Se
dois blocos precisam se separar, o caminho é tom ou espaço, nunca profundidade
simulada.

## Shapes

Um único raio para tudo: 8px (`{rounded.md}`) em botões, campos, seletores e
blocos. Não há escala de raio, e a ausência é a decisão — variar curvatura
entre controles do mesmo peso inventa hierarquia onde não existe.

A exceção é o cromo que o navegador desenha e o design system só tinge: o
polegar da barra de rolagem (`{rounded.chrome-scrollbar}`) e o anel de foco
(`{rounded.chrome-focus}`) seguem a curvatura da própria peça do navegador, não
a do sistema. São dois valores, ambos fora do conteúdo.

Marcas de dado têm respiro de 2px na cor da superfície entre vizinhas (barras
adjacentes, células de heatmap, fatias de rosca). É separação por vão, não por
borda desenhada.

## Components

Caráter geral: **táteis e presentes**. Todo controle tem borda visível
(`showWidgetBorder`), e a ação principal é a única superfície preenchida em
vermelho. A interface se anuncia sem gritar.

### Buttons
- **Shape:** cantos suavemente curvos (8px)
- **Primary:** preenchimento Dinheiro (`#ea1d2c`) com texto branco, borda de
  1px da mesma cor, padding 4px 12px. Reservado para a ação que busca dados
  novos ("Coletar / atualizar pedidos"). **Uma por tela.**
- **Secondary:** superfície elevada (`{colors.surface-raised}`) com tinta
  primária. Todo o resto — Recarregar, Limpar filtros, Salvar nome. O fio segue
  a superfície em que o botão está: `{colors.border-sidebar}` na sidebar,
  `{colors.border-hairline}` no conteúdo.
- **Ícone:** Material Symbols pelo parâmetro `icon=`, nunca glifo dentro do
  rótulo.
- **Focus:** anel de 2px em Dinheiro com 2px de deslocamento.

### Inputs / Fields
- **Style:** superfície elevada, fio de 1px, raio 8px.
- **Chips de seleção:** preenchimento Dinheiro — o mesmo vermelho da ação,
  porque um filtro ativo também é estado assumido pelo usuário.
- **Focus:** o mesmo anel de 2px em Dinheiro.

### Navigation
Seletor segmentado (`st.segmented_control`) escolhe qual painel de análise
montar. O segmento ativo vem em Dinheiro; os demais, em superfície elevada.
Só o painel escolhido é construído.

### Metric Tile
O componente que carrega o propósito do produto. Sem caixa, sem borda, sem
fundo: rótulo em 14px a 72% de opacidade sobre o valor em 700/26.4px com
tracking −0.02em. A ausência de moldura é intencional — o número é a figura, e
uma borda em volta o transformaria em cartão.

### Signal Line
A primeira frase da tela, acima dos KPIs: responde "gastamos demais este mês?"
antes que alguém precise ler um gráfico. Não é cartão nem tile — é uma frase em
Headline com a sua nota de rodapé em Body recuado, sem fundo e sem moldura.

A cor fica **só no veredito** ("10% acima da média"): acima é Dinheiro, abaixo é
Economia, e o patamar normal não recebe cor nenhuma — é o estado que não pede
ação. A ressalva que vem depois ("dentro da faixa dos outros meses") sai em
tinta de leitura; pintar a frase inteira faz o vermelho parar de significar
alguma coisa.

Ícone de tendência em Material Symbols, na cor do veredito, colado na frase.
Nenhum número deste bloco se repete no bloco de KPIs logo abaixo — o que ele
traz é a comparação, não o total.

### Chart Frame
Todo gráfico compartilha o mesmo cromo: fundo transparente, grade
`{colors.chart-grid}`, eixo `{colors.chart-axis}`, texto `{colors.ink-muted}`,
título em 15px `#e6e8ec`, e **nenhum título de eixo** — o título do gráfico já
nomeia a grandeza. Rótulo direto na marca só até 8 marcas; acima disso, eixo e
hover carregam o valor.

## Do's and Don'ts

### Do:
- **Do** amarrar cada matiz a uma grandeza e mantê-la em todos os painéis:
  Dinheiro `#ea1d2c`, Pedidos `#3987e5`, Economia `#199e70`.
- **Do** rodar o validador de paleta contra `#0e1117` antes de introduzir
  qualquer cor de dado nova.
- **Do** dar mais espaço acima de um título (2.5rem) do que abaixo (0.75rem).
- **Do** usar Material Symbols pelo parâmetro `icon=` dos componentes.
- **Do** escapar `R\$` em texto markdown — dois cifrões na mesma string viram
  delimitador de LaTeX e o Streamlit engole o trecho entre eles.
- **Do** montar só o painel selecionado; painel oculto tem largura zero e
  quebra o cálculo de área do gráfico.
- **Do** declarar na tela quando o número é estimativa.
- **Do** comparar períodos como-por-como: o mês parcial vai contra o mesmo
  recorte de dias dos meses anteriores, nunca contra meses cheios.

### Don't:
- **Don't** introduzir um quarto matiz de dado. Acima de três categorias,
  o formato muda (barra), não a paleta.
- **Don't** usar sombra em lugar nenhum. Separação é tom ou espaço.
- **Don't** trocar `backgroundColor` do tema sem revalidar a paleta inteira —
  o contraste e a separação para daltonismo foram medidos contra `#0e1117`.
- **Don't** pôr emoji no lugar de ícone.
- **Don't** desenhar borda em volta de marca de dado; o respiro de 2px na cor
  da superfície faz esse trabalho.
- **Don't** rotular toda barra de uma série longa nem toda fatia de uma rosca:
  acima de 8 marcas, ou abaixo de 8% de uma fatia, o rótulo é recortado.
- **Don't** deixar mais de uma ação preenchida em vermelho por tela.
- **Don't** repetir num painel um valor que o bloco de KPIs já mostra.
- **Don't** emitir a mesma legenda dentro de cada coluna de um par: a nota que
  vale para a linha inteira sai uma vez, antes de abrir as colunas.
