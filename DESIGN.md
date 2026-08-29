---
name: iFood Order Tracker
description: Painel local e escuro que transforma o histórico de delivery de um casal em um número que dá para agir.
colors:
  dinheiro: "#ea1d2c"
  dinheiro-acao: "#c9101d"
  dinheiro-texto: "#f0787f"
  pedidos: "#3987e5"
  economia: "#199e70"
  economia-texto: "#3fbf90"
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
    fontSize: "clamp(40px, 3.5vw, 50px)"
    fontWeight: 700
    lineHeight: "1.1"
    letterSpacing: "-0.025em"
  section:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: "normal"
    letterSpacing: "-0.14px"
  headline:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: "28px"
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
    letterSpacing: "0.01em"
    maxWidth: "72ch"
  label:
    fontFamily: "Source Sans, system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "22.4px"
    letterSpacing: "0.01em"
  icon:
    fontFamily: "Material Symbols Rounded"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: "1"
    letterSpacing: "normal"
motion:
  feedback: "120ms"
  estado: "220ms"
  chegada: "160ms"
  curva: "cubic-bezier(0.16, 1, 0.3, 1)"
rounded:
  md: "8px"
  chrome-scrollbar: "6px"
  chrome-focus: "4px"
spacing:
  section-above: "2.5rem"
  section-below: "0.75rem"
  block-above: "1.75rem"
  block-below: "0.5rem"
  page-top: "calc(60px + 2.25rem)"
  cola: "8px"
  base: "16px"
  solta: "28px"
  abaixo-do-titulo: "20px"
components:
  button-primary:
    backgroundColor: "{colors.dinheiro-acao}"
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
  alert-state:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-primary}"
    rounded: "{rounded.md}"
    borderColor: "{colors.border-hairline}"
    typography: "{typography.body}"
  metric-tile:
    backgroundColor: "{colors.surface-base}"
    textColor: "{colors.ink-primary}"
    typography: "{typography.metric}"
  ledger-head:
    backgroundColor: "{colors.surface-base}"
    textColor: "{colors.ink-primary}"
    typography: "{typography.display}"
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
ela vive no wordmark da placa, no anel de foco, no rastro da seleção de texto e na
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
  ticket médio, valor por restaurante — e é também o anel de foco e o rastro
  da seleção de texto.
- **Dinheiro Ação** (`{colors.dinheiro-acao}`): o mesmo vermelho um passo mais
  escuro, e só onde há **texto branco por cima** — botão primário, chips de
  filtro. O vermelho do logo dá 4,46:1 com branco e reprova o AA de texto por
  0,04; este dá 5,87:1, e ainda 3,22:1 contra a superfície, então o botão
  continua lendo como forma cheia.
- **Dinheiro Texto** (`{colors.dinheiro-texto}`): o vermelho **claro**, para
  vermelho que é *texto* sobre superfície escura — o veredito do sinal do mês,
  o segmento ativo do seletor, o valor do slider. Como texto, `#ea1d2c` dá
  4,24:1 e `#c9101d` dá 3,22:1; ambos reprovam. Este dá 6,93:1.

### Secondary
- **Pedidos** (`{colors.pedidos}`): contagem. Quantos pedidos, quantos itens,
  frequência por restaurante. Nunca dinheiro.

### Tertiary
- **Economia** (`{colors.economia}`): o contrafactual — economia estimada por
  prato e o custo de cozinhar em casa. É a cor da pergunta que o produto faz.
- **Economia Texto** (`{colors.economia-texto}`): o par claro, mesma regra —
  verde que é texto sobre superfície escura (8,16:1).

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

**A Regra do Limiar Certo.** Cada matiz tem **três** papéis e três limiares, e
usar o tom errado no papel errado reprova:

| papel | limiar | vermelho | verde |
|---|---|---|---|
| marca de dado | 3:1 | `#ea1d2c` | `#199e70` |
| fundo de ação (texto branco) | 4,5:1 | `#c9101d` | — |
| texto sobre superfície escura | 4,5:1 | `#f0787f` | `#3fbf90` |

A escolha é pelo papel, nunca pela aparência. O erro que essa tabela existe
para evitar já foi cometido duas vezes aqui: primeiro texto em `#ea1d2c`
(4,24:1), depois texto em `#c9101d` (3,22:1), cada um parecendo o certo.

**A Regra do Estado.** Info, aviso, erro e sucesso **não ganham matiz
própria**. Eles pegam emprestado das três que já existem, e a escolha é pelo
que a mensagem diz, não pela convenção de cor do framework:

| estado | cor | por quê |
|---|---|---|
| nada a mostrar | nenhuma | "não há dado" não é alarme nem grandeza; cor gasta aqui é cor que para de significar |
| algo errado | Dinheiro Texto | os avisos desta tela são sobre a conta não fechar ou o dado não carregar — é do dinheiro que falam |
| deu certo | Economia Texto | a mesma leitura do chip de delta: verde é o desfecho bom |

A cor vive no **fio de 1px e no ícone**, nunca no preenchimento: o estado não
pode ser a superfície mais forte da tela, que é da única ação preenchida. E
não depende da cor — o Streamlit já emite `role="alert"` contra `role="status"`,
e as chamadas coloridas levam ícone.

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
- **Display** (700, `clamp(40px, 3.5vw, 50px)`, −0.025em): **a quantia**, uma
  vez por página. O degrau já serviu ao nome da tela; hoje serve ao número,
  porque o produto falha se o número não doer e o topo da escala não pode
  estar num rótulo. O teto de 50px é deliberado: acima disso a quantia vira
  cartaz e a placa some do lado dela. O piso de 40px também — `R$ 10.201,76`
  a 50px não cabe em 375px, e número cortado é pior do que número menor.
- **Section** (600, `clamp(22px, 2.2vw + 12px, 28px)`, −0.14px): título de
  seção na coluna de conteúdo ("E se você tivesse cozinhado em casa?"), como
  `h2`, e o `h1` da placa. O `clamp` existe pela placa: a 28px em 375px o nome
  da tela quebra em duas linhas e o wordmark ao lado fica centrado contra o
  vão.
- **Headline** (600, 20px/28px, −0.1px): título de seção da sidebar
  ("Filtros"), o veredito do mês e a linha do contrafactual. A entrelinha é
  1.4 e vai **explícita**: o veredito herdava 1.6 do corpo e ficava com
  entrelinha diferente da linha do contrafactual, que tem o mesmo tamanho e
  mora dois blocos abaixo.
- **Title** (600, 18px/21.6px, −0.09px): título de bloco dentro da seção, `h3`.
  Degrau **reservado**: nenhuma seção usa hoje, e a regra existe para que o
  primeiro `st.subheader` dentro de uma seção caia na escala em vez do default
  do framework.
- **Metric** (700, 26.4px, −0.02em): o valor do KPI. O tracking negativo
  aperta os dígitos para o número ler como uma unidade, não como uma fileira.
- **Body** (400, 14px/22.4px, +0.01em, medida 72ch): texto corrido, legendas,
  ajuda.
- **Label** (400, 14px, +0.01em, opacidade 0.72): rótulo de KPI e de campo.
- **Icon** (Material Symbols Rounded, 22px): o ícone é uma fonte, não tipo de
  leitura. É o mesmo conjunto que o Streamlit carrega para o parâmetro
  `icon=`; num trecho de HTML próprio, a família vai declarada à mão.

### Named Rules

**A Regra da Medida.** Prosa da coluna de conteúdo tem teto de **72ch**. Numa
coluna de 1140px o texto de 14px corria 166 caracteres por linha — mais que o
dobro do que o olho volta a achar sozinho, e a única coisa que o leitor não
podia consertar: fonte e cor estavam certas, e a legenda ainda era uma
travessia.

A medida vai em `ch`, não em pixels, porque ela é do texto e não do container:
a linha de 20px fica fisicamente mais larga que a de 14px, e é isso mesmo —
corpo maior carrega linha maior. O seletor pega só a prosa de primeiro nível
(`> .stElementContainer > .stMarkdown`); rótulo de widget, título de gráfico e
célula de tabela moram mais fundo e não têm medida a defender.

**A Regra do Texto Claro.** Fonte clara sobre fundo quase preto sangra: o traço
engorda e o miolo das letras fecha. A compensação é nos três eixos — entrelinha,
tracking e peso. Este painel já tinha a entrelinha generosa (1.6 no corpo de
14px) e o peso resolvido pelo par rótulo/valor, então o que faltava era o
tracking: **+0.01em** em tudo que é 14px sobre a superfície escura. São 0,14px
por letra — não se vê, se lê.

**A Regra do Rótulo que Recua.** No par rótulo/valor, o rótulo vai a 72% de
opacidade e o valor fica em 700. Se os dois saem no mesmo tom, o olho tem que
escolher — e a varredura para.

**A Regra do Nível.** Seção é `h2`, bloco é `h3`, e o CSS de ritmo mira os
dois. Uma seção escrita como `h3` herda o ritmo de bloco e o ritmo de seção
vira regra que não casa com nada — foi o que aconteceu com as seis seções
originais, todas em `st.subheader`.

**A Regra da Moeda.** Dinheiro sai em formato brasileiro — ponto no milhar,
vírgula no decimal (`R$ 1.724,05`). Vale para texto, rótulo de barra, tick de
eixo e hover: os três últimos são formatados pelo Plotly, que precisa de
`separators=",."` no layout. O padrão do Python é o americano, e uma tela em
português com `R$ 1,724.05` denuncia que ninguém olhou.

O espaço entre o `R$` e o número é **inquebrável** (`\u00a0`). Com a medida em
72ch a legenda quebrava entre os dois, e quantia partida em duas linhas não é
quantia. Pelo mesmo motivo o separador dos runs de fato é
`\u3000\u2060·\u3000`: o *word joiner* proíbe a quebra antes do marcador, para
a linha nova começar com o próximo fato e não com o `·`.

**A Regra do Dígito.** `tabular-nums` só onde números se alinham na vertical
(tabela, ticks de eixo). No valor grande e solto do KPI, figuras
proporcionais: dígitos de largura fixa fazem `121` parecer frouxo em corpo
grande.

### Named Rules — números

**A Regra da Base.** Existe **uma** fonte de verdade para o que foi pago:
`total`. Toda composição — fatias de rosca, economia por prato, custo em casa —
é derivada dela, nunca remontada a partir do preço de tabela dos itens. O preço
de tabela não reconstrói o total: promoção do restaurante e benefício de clube
abatem por fora e não aparecem em `coupon_discount`. Em 120 de 259 pedidos a
conta não fechava, e a tela chegou a afirmar num título um total que as próprias
fatias contradiziam em R$ 1.002,74.

**A Regra do que Não Chegou.** Pedido cancelado, recusado ou de status
desconhecido não é gasto e não entra em soma de dinheiro. Quando o recorte os
contém, a tela diz quantos são e quanto somam, em vez de escondê-los.

**A Regra do Estimado e do Apurado.** Num bloco que mistura os dois, a tela
diz qual é qual. A economia nos pratos é estimativa e responde ao controle de
otimismo; a taxa de entrega e serviço é valor apurado e não se move com ele —
e a legenda declara isso, para o controle não parecer governar a conta inteira.

## Layout

Coluna única larga (`layout="wide"`) com sidebar fixa de filtros. Um único
grupo de filtros governa tudo abaixo — nunca filtro dentro de card.

Ritmo assimétrico e deliberado: 2.5rem acima de um título de seção contra
0.75rem abaixo (1.75rem / 0.5rem no nível de bloco). O cabeçalho gruda no
próprio conteúdo em vez de flutuar no meio do vão. O topo da página respira
2.25rem — medidos **depois** do cabeçalho do Streamlit, que tem 60px e fica por
cima do conteúdo; daí `calc(60px + 2.25rem)`, e não 2.25rem crus.

### A escala de espaço

O Streamlit empilha tudo num flex column com `gap: 16px`. Sozinho, isso deixa
a coluna sem cadência: a nota de rodapé fica tão longe do número quanto o
número fica do próximo assunto, e espaço igual é hierarquia nenhuma. Fora o
título de seção, a página inteira tinha um valor de espaço só.

Três degraus, e um papel para cada:

| degrau | valor | papel |
|---|---|---|
| **cola** | `{spacing.cola}` | mesmo assunto: a legenda e o que ela anota; dois controles do mesmo grupo; os botões de exportar e a tabela em que agem |
| **base** | `{spacing.base}` | irmãos comuns — o padrão do framework, mantido |
| **solta** | `{spacing.solta}` | troca de sub-bloco dentro da seção: depois do grupo de controle, depois de uma corrida de legendas |

Abaixo de um título de seção os `{spacing.section-below}` dele entram na
conta: **`{spacing.abaixo-do-titulo}`** para o que pertence ao título
(subtítulo da seção, seletor de painel) e **`{spacing.solta}`** para o conteúdo
que começa depois dele.

O gap do framework não tem API, então cada degrau é escrito como um delta de
`margin-top` sobre os 16px. Os seletores usam `:has()` e miram **papel**, não
posição — "legenda", "controle", "conteúdo" — então reordenar a página não os
quebra.

Densidade segue a prioridade, não a simetria, e a prioridade aqui é uma só: o
topo é **um** número em Display com os dois veredictos pendurados nele, e todo
o resto do recorte — pedidos, ticket médio, cupons, taxas — desce para duas
linhas de legenda. Cinco tiles iguais numa linha era default de framework;
três tiles iguais era a mesma democracia com menos itens, e nenhuma delas diz
qual dos números é o que importa.

A escala desce em degraus visíveis: quantia (Display) → veredito e
contrafactual (Headline) → recorte (Body). Antes os dois veredictos saíam em
legenda de 14px, com o mesmo peso da linha de cupons.

Quatro seções, não seis. O topo — sinal do mês, KPIs, linha do contrafactual —
responde as duas perguntas com que a sessão começa, e um único fio separa esse
resumo da análise. Entre as seções o trabalho é do espaço e do degrau de
título: fio em toda troca de assunto vira grade.

Assunto que não sustenta o peso de uma seção vira painel de um seletor que já
existe (faixa de valor entrou em "Quando e quanto"). O critério é o conteúdo,
não a arrumação.

Painéis de análise são um seletor + um painel montado sob demanda, nunca todos
de uma vez: painel oculto tem container de largura zero, e gráfico renderizado
ali calcula área negativa.

No estreito a sidebar recolhe sozinha (`initial_sidebar_state="auto"`);
expandida ela cobriria a tela e a primeira coisa visível seriam filtros, não
dados. Recolhida, ela é uma gaveta de 300px sobre uma tela de 375 — o naco de
conteúdo que sobra ao lado é o que diz que aquilo é uma camada, e por isso ela
não vira largura cheia.

### Tela estreita e dedo

O desktop é a cena de uso e nada nele muda. O que existe são duas fronteiras
de largura, as duas tiradas do próprio Streamlit, e um eixo separado para o
ponteiro:

| fronteira | o que é |
|---|---|
| **864px** | onde o Streamlit troca o padding lateral de 80px por 16px |
| **640px** | onde ele para de pôr as colunas lado a lado |
| `pointer: coarse` | dedo, em qualquer largura |

**A Regra das Duas Perguntas.** Largura decide layout; ponteiro decide alvo.
São perguntas diferentes e não se respondem uma pela outra: um tablet em
paisagem tem 1024px e continua sendo dedo; uma janela estreita no desktop
continua sendo mouse.

**Abaixo de 864px** o sangramento da capa vale 16px, não 80 — o cancelamento
acompanha o padding que existe de fato, senão a capa fica 128px mais larga que
a janela e a página inteira desliza de lado. O título de seção entra na mesma
escala fluida da placa (`clamp(22px, 2.2vw + 12px, 28px)`). Gráfico e tabela
ganham rolagem lateral **por dentro da própria caixa**, e a coluna de conteúdo
deixa de rolar de lado: rolagem horizontal de página é sempre defeito; a de
dentro de um gráfico ou de uma tabela, não.

**Entre 640 e 864px** — o tablet em retrato — é onde o layout do desktop se
desfaz sem avisar: o trio de gráficos cai para 235px cada e os quatro KPIs
para 172px. Ali o par e o trio passam a ocupar a largura inteira, um debaixo
do outro, e os KPIs viram grade de dois.

**Abaixo de 640px** o KPI fica um por linha, como o Streamlit já faz. Numa
coluna de 163px, `R$ 10.201,76` a 26,4px não cabe — e o produto falha se o
número não couber.

**No dedo** o alvo é 44×44 (WCAG 2.5.8 AAA): polegar do slider, seta de campo,
botão, cabeçalho de expansor, linha de checkbox e os dois controles da gaveta
de filtros, que no celular é o gesto mais frequente da tela. A área cresce por
padding com margem negativa do mesmo tamanho — o desenho não muda **enquanto o
elemento não carrega tinta**. Onde ele carrega, a técnica pinta o alvo inteiro:
o polegar do slider tem fundo e raio de 100%, e o padding de 6px transformava
uma bolinha de 12 numa de 24, com a margem negativa tirando ela do centro da
trilha. Elemento com tinta cresce por `::after` transparente
(`position: absolute; inset: -6px`, e `-16px` no dedo): a área cresce, o
desenho fica onde estava. O ✕ do chip
é a exceção declarada: 44 não cabe num chip sem transformar o filtro numa
fileira de botões, então ele vai a 36 e o chip cresce junto, para o alvo não
vazar por cima do vizinho. E onde não há hover, a barra de ferramentas da
tabela deixa de ser invisível: sem mouse não há descoberta.

## Elevation & Depth

**Sem sombra alguma.** A profundidade é inteiramente tonal: três superfícies
(`surface-sidebar` → `surface-base` → `surface-raised`) mais um fio de 1px onde
o tom sozinho não separa. Gráficos são transparentes sobre a página — o Plotly
não desenha superfície própria.

### Named Rules

**A Regra do Papel do Espaço.** O intervalo entre dois blocos diz o que eles
são um do outro, e por isso é escolhido pelo papel, nunca pela aparência: cola
se andam juntos, base se são irmãos, solta se muda o assunto. Um valor novo
fora dos três é sinal de que o papel não foi decidido.

**A Regra da Legenda que Cola.** Legenda é a letra miúda do bloco acima, nunca
um bloco novo — 8px, sempre. A única exceção documentada é o cabeçalho-extrato,
onde as duas frases da sessão andam juntas e a letra miúda começa depois do
vão de 28px.

**A Regra do Controle que Pertence.** Um seletor de painel logo abaixo de um
título é do título — é ele que escolhe o que a seção mostra. A 28px do título
e 16px do gráfico, o controle lia como legenda do gráfico, que é o oposto do
que ele faz.

**A Regra do Tom, não da Sombra.** Elevação se expressa por camada de cor e fio
de 1px. Nenhum elemento ganha `box-shadow` — nem em repouso, nem em hover. Se
dois blocos precisam se separar, o caminho é tom ou espaço, nunca profundidade
simulada.

**A Regra das Três Superfícies.** A escada tem **exatamente** três degraus, e o
framework insiste em inventar no meio: o botão secundário saía em `#10151e` na
sidebar e `#131720` no conteúdo, a caixa do checkbox em `#10151e` e a barra
flutuante da tabela em `#131720` — quatro cinzas quase iguais que ninguém
escolheu. Todo degrau novo é fixado no valor documentado. Cinco cinzas a um
passo um do outro não são hierarquia; são ruído que ninguém consegue nomear.

## Shapes

Um único raio para tudo: 8px (`{rounded.md}`) em botões, campos, seletores e
blocos. Não há escala de raio, e a ausência é a decisão — variar curvatura
entre controles do mesmo peso inventa hierarquia onde não existe.

A exceção é o cromo que o navegador desenha e o design system só tinge: o
polegar da barra de rolagem (`{rounded.chrome-scrollbar}`) e o anel de foco
(`{rounded.chrome-focus}`) seguem a curvatura da própria peça do navegador, não
a do sistema. São dois valores, ambos fora do conteúdo. O terceiro é o polegar
do slider, redondo por ser uma alça e não uma superfície.

Tudo o mais é 8px, inclusive o que o Streamlit entrega com outra medida: chip
de filtro (6,08px de fábrica), chip de `código` e caixa de checkbox (4px) e o
chip de delta do KPI (pílula). O framework não decide a forma do sistema.

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
montar. O ativo **não é superfície preenchida**: é texto `{colors.dinheiro-texto}`
em peso 600 sobre uma tinta de 10% do vermelho, com fio da mesma cor. Os demais
ficam na superfície base com fio de borda. O peso é deliberado — sem ele o
estado dependeria só da cor.

O estado também sai no atributo (`aria-pressed`), que o Streamlit não emite:
sem isso, quem não enxerga cor não sabe qual painel está aberto.

Só o painel escolhido é construído, e o painel que **abre** é o primeiro com
conteúdo no filtro corrente — não o primeiro da lista.

### Metric Tile
A unidade de leitura de número, hoje nos quatro tiles da seção de cozinhar.
Sem caixa, sem borda, sem fundo: rótulo em 14px a 72% de opacidade sobre o
valor em 700/26.4px com tracking −0.02em. A ausência de moldura é intencional
— o número é a figura, e uma borda em volta o transformaria em cartão.

O **Ledger Head** é este mesmo componente na escala de display; a anatomia é a
mesma e a única diferença é o degrau de tipo.

### Capa
Uma fotografia de largura inteira no topo da coluna de conteúdo, no feitio das
capas do Notion: sangra pelos dois lados e **some por baixo do conteúdo em vez
de terminar num corte**.

**Só na coluna de conteúdo.** A sidebar não recebe capa — ali estão os filtros,
e foto atrás de controle é ruído atrás de trabalho.

A transição suave é `mask-image`, não uma faixa de gradiente por cima: a
máscara dissolve a própria foto no fundo da página, então funciona sobre
qualquer superfície e não inventa uma quinta camada de cor. A imagem começa a
ceder aos 45% e chega a zero em 100% — a metade de baixo é asfalto, e é ela que
precisa sumir.

Altura em `30vh` com piso e teto, a mesma proporção do Notion. Capa é
**recorte**, não a foto inteira: numa coluna de 1140px a imagem renderiza com
~760px de altura e a janela mostra uns 35% dela. O `object-position` prende a
faixa opaca no sujeito — nesta proporção não cabem o rosto do entregador e o
farol da moto ao mesmo tempo, e o rosto é quem conta a cena.

O sangramento cancela o padding horizontal do `.block-container` (80px, 16px no
estreito) com margem negativa. Na vertical são **dois cancelamentos com donos
diferentes**: o container zera o gap de 16px que o bloco vertical põe antes do
primeiro elemento visível (o bloco do `<style>` conta como irmão de altura
zero), e a capa zera o respiro de 2.25rem do topo. Os 60px do cabeçalho ficam,
de propósito: aquela barra é **opaca e da cor da página**, então a capa passaria
por baixo dela sem aparecer. Assim ela começa onde o conteúdo começa a ser
visível, e rola para trás do cabeçalho como a do Notion.

### Placa
O wordmark e o nome da tela na mesma linha, no topo: `<img>` de 38px de altura
ao lado de um `h1` no degrau de Section, alinhados pelo centro com 0.7rem de
respiro.

A marca **não** fica no slot de `st.logo`. Lá ela mora num canto acima da
sidebar, longe do título e some quando a sidebar recolhe; nas duas posições ao
mesmo tempo seriam duas marcas na mesma tela.

38px de imagem contra um `h1` de 28px não é descompasso: o wordmark é aparado
sem margem, mas as letras ocupam ~60% da caixa (o resto é o traço acima), então
casar a altura da imagem com a do texto deixa a marca menor do que ele.

O `h1` é escrito à mão — `st.title` não aceita nada ao lado — e o `alt` sai de
verdade daqui, sem depender de conserto no DOM. O bloco que o `localize.html`
mantinha para trocar o `alt="Logo"` genérico do `st.logo` foi removido junto.

**Nenhuma imagem vai embutida.** Logo e capa saem os dois de `static/`,
porque o markdown é reenviado pelo websocket a cada rerun: em `data:` URI o
wordmark eram 63 KB em toda mexida de filtro, contra ~90 bytes de URL. O `?v=`
com o hash do arquivo é a saída da armadilha de cache — `/app/static/` é
servido com cache longo, e sem ele trocar a imagem não trocaria o que se vê.
O hash é cacheado: ele lê o arquivo inteiro, e a capa eram 176 KB relidos e
digeridos a cada rerun.

**A versão servida é dimensionada para a tela.** O wordmark original tem
2093px e aparece a 38px de altura — 55 vezes maior do que precisa. `static/`
leva um WebP de 240px (5,6 KB, três vezes o tamanho de tela, para DPR alto);
`assets/` continua com o original de 47 KB. `assets/` guarda as marcas;
`static/` guarda o que é servido.

### Ledger Head
O topo da tela, e o único lugar onde o degrau de Display aparece. Um bloco só
responde as duas perguntas com que a sessão começa — "gastamos demais este
mês?" e "dava para ter cozinhado?" — penduradas na quantia que as motiva, em
vez de três blocos empilhados no mesmo peso.

É o **Metric Tile na escala de display**: a mesma anatomia — rótulo em 14px a
72% de opacidade sobre o valor em 700 com tracking negativo, sem caixa, sem
borda, sem fundo — só que grande o bastante para ser a primeira coisa lida. O
rótulo nomeia o recorte junto da grandeza ("Total gasto · Agosto de 2026"),
para o número não ficar solto quando o filtro muda.

**O veredito do mês** encosta na quantia na mesma linha de base: é atributo do
número, não um parágrafo acima dele. Responde "gastamos demais este mês?" e a
cor fica **só no veredito** ("16% acima da média") — acima é Dinheiro Texto,
abaixo é Economia Texto, e o patamar normal não recebe cor nenhuma, que é o
estado que não pede ação. A ressalva que vem depois ("dentro da faixa dos
outros meses") sai em tinta recuada e peso normal: pintar a frase inteira faz
o vermelho parar de significar alguma coisa, e tirar a ressalva daqui perde a
frase mais forte que a tela sabe dizer ("e acima de todo mês anterior").

**O veredito nomeia o mês quando o recorte não é ele.** O veredito é sempre do
mês de referência; a quantia ao lado é do filtro da barra lateral. No recorte
de abertura os dois coincidem e o rótulo da quantia já diz "Agosto de 2026" —
repetir seria ruído. Com o filtro de mês limpo, "12% acima da média" encostado
num total de dez meses lê como se fosse dos dez, e a nota que declarava o
escopo morava dois blocos abaixo, no fim de uma legenda de 14px. Então o
escopo entra na frente da frase — "Em agosto de 2026, 12% acima da média" —
em tinta recuada, porque a cor continua sendo só do veredito.

O veredito é **texto corrido**, não `inline-flex`: como flex, ao quebrar em
duas linhas o ícone e a ressalva viravam colunas e a frase se desmontava no
estreito. O ícone de tendência é Material Symbols alinhado pelo baseline, e o
respiro dele vai na própria margem — num `gap` de flex ele cai também antes da
vírgula.

**A linha do contrafactual** vem logo abaixo, em Headline de peso normal com o
valor evitável em Economia Texto e peso 600. Responde a segunda pergunta sem
obrigar a rolar até a seção; o valor sai como "cerca de", acompanha o controle
de otimismo da seção e diz que é estimativa.

Depois, duas legendas e não uma: a primeira é o recorte filtrado (pedidos,
ticket médio, cupons, taxas, e o que ficou fora do total), a segunda é o
histórico completo (média, faixa, projeção). Emendadas numa linha só, os dois
escopos viram um — e o sinal roda sobre o histórico inteiro enquanto a quantia
roda sobre o filtro.

Nenhum número do bloco se repete abaixo: o que o veredito traz é a comparação,
não o total.

Toda regra de `<p>` do bloco vai prefixada por `.block-container`. O Streamlit
estiliza `.stMarkdown p` e ganha da classe sozinha — sem o prefixo, a linha do
contrafactual saía em 16px, no meio do caminho entre o degrau que pedia e a
legenda de onde ela veio.

### Alert State
`st.info`, `st.warning`, `st.error` e `st.success` com a anatomia da casa:
superfície elevada, fio de 1px, raio 8px, texto em tinta de leitura. A cor do
estado fica no fio e no ícone, seguindo **A Regra do Estado**.

De fábrica o Streamlit os entrega como **bloco preenchido de raio 0** em quatro
matizes de outro sistema — um azul quase igual, mas não igual, ao de contagem;
um **amarelo**, exatamente a quarta matiz que esta paleta mediu e rejeitou
(ΔE 4.4 contra o vermelho para daltonismo); e um vermelho e um verde fora dos
pares de texto validados. E não é um caso de canto: o recorte de abertura é um
mês, metade dos painéis abre sem série, e cada um deles emite um `st.info`.

O `st.info` é o **estado neutro** e é o mais comum da tela. Note que ele não
substitui o **Empty Panel** — aquele é uma frase que diz o que há e para onde
ir; o `st.info` é o aviso curto de um painel que não tem o que desenhar.

### Empty Panel
O estado que a tela mais produz — o recorte de abertura é um mês só, e metade
dos painéis não tem série para desenhar nele. Não é `st.info("Sem dados")`: é
uma frase que diz **o que há** ("Só Agosto no filtro atual"), **onde está o
número** ("o total está nos indicadores acima") e **dois caminhos nomeados**
("use *Dia da semana* ou *Heatmap*"). A saída sugerida muda com a dimensão que
esvaziou o painel.

Vale também para o seletor: o painel que abre é o primeiro **com conteúdo** no
filtro corrente, não o primeiro da lista.

E a nota sai **uma vez**, antes de abrir as colunas — emitida dentro de cada
uma, a mesma frase aparecia duas vezes lado a lado.

### Chart Frame
Todo gráfico compartilha o mesmo cromo: fundo transparente, grade
`{colors.chart-grid}`, eixo `{colors.chart-axis}`, texto `{colors.ink-muted}`,
título em 15px `#e6e8ec`, e **nenhum título de eixo** — o título do gráfico já
nomeia a grandeza.

**Toda marca leva o seu valor**, seja dinheiro, contagem ou quantidade: barra,
ponto de linha, fatia de rosca e célula de heatmap com pedido. O rótulo é o
padrão do helper, não um argumento que cada chamada precisa lembrar de passar —
`_bar` e `_line` formatam sozinhos a partir da série, e `text=` só existe para
quando o rótulo **não** é o valor.

O formato sai do dtype: grandeza inteira é contagem (`1.234`), fracionária é
dinheiro (`R$ 1.234`). Nesta base a regra é limpa — todo inteiro é contagem
(pedidos, itens, quantidade) e todo fracionário é dinheiro (total, ticket,
economia, custo em casa).

Na barra horizontal o rótulo é `auto`, não `outside`: a maior barra empurra o
número para fora da área de plotagem e ele sai recortado no estreito. Com
`auto`, barra larga leva o número por dentro, em tinta da superfície; barra
curta escreve do lado de fora, em tinta recuada.

O corpo do rótulo é **fixo em 11px** e o Plotly é proibido de encolher
(`constraintext="none"`). Sem isso ele espreme o número para caber dentro da
barra, e a barra mais curta acaba definindo o corpo da série inteira. Com
`auto` + `constraintext` livre, o número que não cabe dentro simplesmente sai
para fora, no mesmo corpo.

`cliponaxis=False` em toda marca rotulada: o rótulo da maior barra encosta na
borda da área de plotagem e, sem isso, é recortado ali em vez de invadir a
margem.

**A alternativa que não serviu:** `uniformtext` com `mode="show"` iguala o
corpo de todos os rótulos pelo **menor** deles, e a série inteira encolhia por
causa de uma barra curta. `mode="hide"` é pior ainda — esconder rótulo é
exatamente o comportamento que saiu daqui.

A barra de ferramentas do Plotly não aparece (`displayModeBar: False`). Zoom e
lasso não servem a um painel de agregados, e em 375px a barra pousa por cima do
título do próprio gráfico.

### Named Rules — o que o framework emite

**A Regra da Costura.** O Streamlit emite coisas que não têm API e não
pertencem a design system nenhum: `lang="en"`, ARIA em inglês, estado de
seleção só na cor, ausência de marco `main`. O projeto não convive com isso —
`static/localize.html` roda no documento pai e corrige idioma, atributos,
`aria-pressed`, marco e atalho de teclado.

**Limitação conhecida — o gráfico não segue a janela.** Redimensionar sem
recarregar deixa o gráfico na largura anterior. A largura pertence ao
componente do Streamlit, que a mede uma vez e grava `layout.width` na figura.
Quatro caminhos foram testados e nenhum vence:

| tentativa | resultado |
|---|---|
| `Plotly.Plots.resize(el)` | roda sem erro, não move o SVG |
| `Plotly.relayout(el, {width})` | obedece só quando o container encolhe |
| apagar `layout.width` à mão | o componente reescreve ao redesenhar |
| `config: {responsive: true}` | o autosize nunca vale, com `layout.width` posto |
| componente devolvendo a largura, para provocar rerun | o rerun não re-mede |

Recarregar corrige. Fica registrado para ninguém gastar a tarde de novo.

**No celular quem dispara isso não é arrastar a janela — é girar o aparelho**,
e aí o caso deixa de ser raro. Medido em 29/08/2026: girando de 812×375 para
375×812 sem recarregar, o container vai a 343px e o SVG fica em 780. As duas
consequências foram contidas, não corrigidas — o gráfico rola por dentro da
própria caixa em vez de empurrar a página, e a tabela é presa à coluna
(`stDataFrameResizable`, `max-width: 100% !important`), com o que a grade se
remede sozinha e o canvas volta a acompanhar a coluna. O gráfico continua
desenhado na largura antiga até o próximo rerun.

Sobre a medição: tudo foi verificado com viewport emulada, mas a ressalva de
antes perdeu força — no mesmo giro as media queries do Streamlit trocaram o
padding e as colunas se re-empilharam, ou seja, o layout do navegador reagiu.
Só `layout.width` do Plotly não. `Plotly.Plots.resize` e `Plotly.relayout`
foram chamados de novo, na figura viva, e nenhum dos dois moveu o SVG.

Duas pegadinhas de cache mordem quem editar esse arquivo: o servidor estático
do Streamlit **fixa o tamanho no start** (editar com o servidor no ar serve o
conteúdo novo truncado no tamanho velho, e o script quebra no meio sem erro
visível), e o navegador guarda `/app/static/` com cache longo. Por isso a URL
do iframe leva `?v=<hash do arquivo>` — e por isso reiniciar o Streamlit faz
parte de editar o arquivo.

## Motion

**Não há momento focal, e isso é decisão.** É um painel local que alguém abre
de propósito, e o Streamlit **remonta a página inteira a cada rerun** — uma
entrada autoral viraria coreografia em toda mexida de filtro, que é
exatamente o que um painel de operação não pode fazer. O movimento aqui tem
dois trabalhos, os dois de feedback, e nenhum de expressão.

Antes desta passagem a tela tinha movimento **nenhum**: toda transição que o
Streamlit entrega vem com duração zero, e cada troca de estado era corte seco.

### O que está obsoleto recua

Uma troca de painel leva **~985ms medidos**, e nesse intervalo a tela mostrava
o painel *anterior* como se fosse o atual. O único sinal era o spinner do
framework no canto superior direito — longe de onde a pessoa acabou de clicar.

Enquanto o servidor recalcula, a coluna de conteúdo cai para 55%. A **sidebar
não recua**: é onde estão os controles que a pessoa está segurando, e apagar o
próprio controle lê como app quebrado. Recua o que está velho; fica aceso o que
está na mão.

O gatilho é o `stStatusWidget`, que só existe no documento enquanto há rerun em
voo — é o sinal que o próprio framework emite, e usá-lo evita inventar um
estado paralelo que possa dessincronizar.

A assimetria carrega o sentido: descer espera **220ms** antes de começar
(rerun mais rápido que isso termina antes de a opacidade andar, e não pisca) e
leva `{motion.estado}`; subir não espera nada e leva `{motion.chegada}`. Descer
é um aviso que pode esperar, subir é o dado chegando.

### O controle reconhece o clique

`{motion.feedback}` de cor — fundo, fio e tinta — em botão, chip e caixa de
seleção. O bastante para o estado não ser um corte, pouco o bastante para não
virar latência.

### Named Rules

**A Regra da Curva Única.** Uma curva na tela inteira,
`{motion.curva}` — desaceleração natural, sem repique. Bounce e elástico não
entram: são voz, e a voz deste painel é o número.

**A Regra do Movimento que Significa.** O sistema inteiro é opacidade e cor. O
único deslocamento espacial da tela é o atalho de teclado, que entra deslizando
de 8px acima — e é por isso que `prefers-reduced-motion` quase não muda nada
aqui: só ele perde o transform. Se ligar a preferência mudasse muito, seria
sinal de que havia movimento decorativo.

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
- **Do** declarar na tela quando o número é estimativa, e separar na legenda
  o que a estimativa move do que é valor apurado.
- **Do** derivar toda composição de dinheiro do `total`, e conferir que a soma
  fecha antes de desenhar.
- **Do** comparar períodos como-por-como: o mês parcial vai contra o mesmo
  recorte de dias dos meses anteriores, nunca contra meses cheios.
- **Do** manter o veredito das perguntas da sessão no topo, em uma frase cada,
  com a profundidade nas seções abaixo.
- **Do** gastar o degrau de Display na quantia — um degrau acima da placa.
- **Do** manter a marca num lugar só. Ela está na placa; o slot de logo do
  Streamlit (`st.logo`) fica vazio de propósito.
- **Do** prefixar `.block-container` em regra de `<p>` própria, senão o
  `.stMarkdown p` do Streamlit ganha.
- **Do** escolher o intervalo pelo papel — cola, base ou solta — e conferir no
  render que nenhum valor fora dos três apareceu.
- **Do** conferir se o elemento tem fundo antes de crescer o alvo com padding.
  Com tinta, o padding pinta junto e a margem negativa desloca — a área vai num
  `::after` transparente.
- **Do** limitar o curso de um slider (30rem). Na largura inteira da coluna,
  arrastar de 50% a 150% vira travessia e o controle lê como régua da seção.
- **Do** medir a linha em caracteres no render, não a olho: a coluna larga do
  `layout="wide"` deixa qualquer parágrafo passar de 150ch sem parecer errado.
- **Do** medir quanto dura um rerun antes de decidir se ele precisa de
  feedback. ~985ms pede; 100ms não.
- **Do** fechar uma seção num `@st.fragment` quando os widgets dela só mexem
  nela. Sem isso o Streamlit reexecuta a página inteira: marcar "Crescente" na
  tabela custava ~900ms remontando KPIs, contrafactual e gráficos; dentro do
  fragmento custa ~140ms. São quatro fronteiras, uma por alcance de controle:
  a tabela, "Quando e quanto", "Restaurantes e itens", e o par
  resumo + contrafactual, que dividem o controle de otimismo.
- **Do** cachear o que o rerun monta e quase ninguém consome. O
  `st.download_button` exige os bytes na mão para desenhar o botão, então a
  planilha do export era montada em todo rerun: 137ms de openpyxl por mexida
  de filtro, contra 1,7ms no cache.
- **Do** atrasar o estado de espera. Sem atraso, todo rerun barato vira um
  pisca.
- **Do** varrer a tela inteira contra a paleta antes de dar cor por encerrada:
  o que o framework desenha sozinho — estado, chip de `código`, caixa de
  checkbox, barra de hover da tabela, ícone de multiselect — passou anos fora
  da paleta sem ninguém ver, porque metade só aparece em hover ou em estado
  vazio.
- **Do** deixar o helper rotular. Passar `text=` à mão é o caminho de esquecer
  num gráfico novo, e foi assim que metade dos painéis ficou sem número.
- **Do** declarar `line-height` em todo papel de texto. O que fica em `normal`
  herda coisa diferente em cada contexto e o mesmo corpo sai com duas
  entrelinhas na mesma tela.

### Don't:
- **Don't** introduzir um quarto matiz de dado. Acima de três categorias,
  o formato muda (barra), não a paleta. Isso vale para **estado** também: a
  matiz de aviso e de sucesso sai das três, não de uma quinta e uma sexta.
- **Don't** animar a entrada de elementos do conteúdo. O Streamlit remonta
  tudo a cada rerun, e uma animação de entrada dispararia na página inteira a
  cada mexida de filtro.
- **Don't** recuar a sidebar junto com o conteúdo durante um rerun: ali está o
  controle que a pessoa está segurando.
- **Don't** deixar um estado sair como bloco preenchido. A superfície mais
  forte da tela é da única ação preenchida, não de um "sem dados".
- **Don't** usar sombra em lugar nenhum. Separação é tom ou espaço.
- **Don't** trocar `backgroundColor` do tema sem revalidar a paleta inteira —
  o contraste e a separação para daltonismo foram medidos contra `#0e1117`.
- **Don't** pôr emoji no lugar de ícone.
- **Don't** desenhar borda em volta de marca de dado; o respiro de 2px na cor
  da superfície faz esse trabalho.
- **Don't** deixar uma marca sem o seu valor. O teto de 8 rótulos que existia
  aqui apagava o número justamente nos painéis mais densos — "Top 15/30", "Por
  mês" —, que são os que mais custam para ler no eixo.
- **Don't** deixar mais de uma ação preenchida em vermelho por tela.
- **Don't** somar em dinheiro pedido que não foi entregue.
- **Don't** pôr texto branco sobre `{colors.dinheiro}`: para fundo de texto o
  tom é `{colors.dinheiro-acao}`.
- **Don't** usar `{colors.dinheiro}` ou `{colors.dinheiro-acao}` como cor de
  texto sobre a superfície escura: os dois reprovam. O tom é
  `{colors.dinheiro-texto}`.
- **Don't** comunicar estado só por cor. Junto vai peso, ícone ou atributo.
- **Don't** interpolar valor em `str.contains` sem `regex=False` — nome de
  restaurante e de prato traz parêntese, `+` e `*` o tempo todo.
- **Don't** repetir num painel um valor que o bloco de KPIs já mostra.
- **Don't** emitir a mesma legenda dentro de cada coluna de um par: a nota que
  vale para a linha inteira sai uma vez, antes de abrir as colunas.
- **Don't** pintar de vermelho um desfecho bom. O chip de delta da economia
  saía em vermelho com seta para cima — alarme onde não há alarme. Ele diz a
  **queda no gasto**, então é negativo, e com `delta_color="inverse"` sai em
  Economia com a seta para baixo.
- **Don't** usar o menos tipográfico (`−`, U+2212) num delta de `st.metric`: o
  Streamlit não reconhece o número como negativo, trata como alta e inverte a
  cor e a seta. O sinal ali é o hífen ASCII.
- **Don't** deixar a barra de ferramentas do Plotly visível.
- **Don't** deixar o veredito do mês sem escopo ao lado de uma quantia que
  não é daquele mês. A nota de rodapé não resolve: quem lê a linha do topo não
  chega até ela.
- **Don't** montar a frase do veredito com `inline-flex`: ao quebrar em duas
  linhas o ícone e a ressalva viram colunas.
- **Don't** dar tamanho fixo à quantia: ela vai de três a seis dígitos, e o
  recorte de um ano inteiro corta em 375px.
- **Don't** embutir imagem em `data:` URI: o markdown vai pelo websocket a
  cada rerun, e o custo se paga em toda mexida de filtro. Imagem mora em
  `static/`, servida, dimensionada para a tela e com `?v=` do conteúdo.
- **Don't** cortar um fragmento entre um controle e quem lê o valor dele. O
  otimismo mora na seção do contrafactual e alimenta o veredito do topo: em
  fragmentos separados, o número de cima congelaria enquanto o de baixo anda.
  Os dois vão no mesmo fragmento — a fronteira é o alcance do controle, não o
  desenho da seção.
- **Don't** reativar o `st.logo`: a marca está na placa, e nos dois lugares ao
  mesmo tempo vira duas marcas na mesma tela.
- **Don't** deixar o gap de 16px do Streamlit governar sozinho uma coluna
  longa: sem os três degraus, legenda, controle e conteúdo saem no mesmo peso.
- **Don't** estreitar um slider sem conferir o valor flutuante: ele é
  posicionado acima da trilha e, com o curso curto, cai em cima do rótulo.
- **Don't** deixar a coluna inteira governar a medida do texto. Largura de
  layout e largura de leitura são duas coisas.
- **Don't** juntar `R$` e valor com espaço comum, nem separar fatos com espaço
  que aceite quebra: a medida curta expõe os dois na hora.
