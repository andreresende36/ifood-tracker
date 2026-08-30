# Wake-up — iFood Order Tracker

Estado em **29/08/2026**, fim da sessão de performance, polimento e crítica do
seletor de perfil. Última linha do `git log`: `39313e0`. Working tree limpo,
tudo em `main` e no remoto.

Leia junto: `PRODUCT.md` (verdade de produto), `DESIGN.md` (sistema visual e
as regras nomeadas), `.impeccable/critique/` (a auditoria de UX que originou
metade do trabalho abaixo).

---

## Onde estamos

Em 30/08 saiu o que estava represado: cinco commits locais nunca tinham sido
empurrados, entre eles o conserto da capa e do wordmark na réplica hospedada —
o defeito da captura do André não era código, era código que a nuvem não
tinha. `publish.sh` passou a mandar os `raw_sample*.json` junto com os bancos.

Em 29/08, depois da coleta, entraram **optimize**, **polish** e uma
**critique** de componente único — o seletor de perfil, que o André apontou
três vezes como feio e que acabou trocando de forma. Antes delas, na mesma
data, a rodada de **adapt** — celular e tablet, com o desktop intocado. Antes dela, o painel passou por três rodadas do `/impeccable`: **shape**
(reordenação da tela), **critique** (15/40) e **audit** (14/20). O que os dois
últimos apontaram está corrigido, exceto um item documentado como limitação e
um encerrado por decisão.

Nove commits, todos em `main` e no remoto:

| Commit | O quê |
|---|---|
| `3881e1a` | Sinal do mês, moeda pt-BR, legenda duplicada |
| `688c38e` | Tela reordenada: 6 seções → 4, títulos em `h2` |
| `426e28d` | Aritmética do contrafactual, crashes, estados vazios |
| `f956503` | Volta a barra de otimismo (revert pedido) |
| `38a7e3e` | Voltam os quatro tiles (revert pedido) |
| `217006b` | Acessibilidade: idioma, ARIA, `aria-pressed`, contraste |
| `8b9f51e` · `9938f06` | Reflow de gráfico: tentado, removido, documentado |
| `e59df2b` | Visão conjunta descartada, PRODUCT.md ajustado |
| `924ce57` · `e833b24` | Chip de delta em verde; raios uniformizados |
| `5a1086f` | `/impeccable bolder`: cabeçalho-extrato e placa |
| `95e2a99` | `/impeccable layout`: escala de espaço de três degraus |
| `ec48645` | remove o conserto morto do alt do st.logo |
| `db8d777` | `/impeccable typeset` + rótulo em toda marca + cor dos estados + movimento |
| `92c630c` | Capa no topo da coluna de conteúdo, no feitio do Notion |
| `2f8ef53` | `/impeccable adapt`: celular e tablet, desktop intocado (29/08) |
| `b8bd037` | Coleta de 29/08/2026, 260 pedidos |
| `d710f6d` | `/impeccable optimize`: quatro fragmentos, planilha cacheada, logo servido |
| `90d9d8f` | `/impeccable polish`: o veredito do mês nomeia o mês (29/08) |
| `3605721` | polegar do slider volta a 12px e ao centro da trilha |
| `0fa6b51` | cursor de texto some do seletor de perfil |
| `39313e0` | perfil vira segmentado, nome entra na quantia, furos de sistema |
| `d1c8edc` | Logo e capa em base64 na nuvem — só chegou lá em 30/08 |
| `b61f625` | `publish.sh` publica os `raw_sample*.json` junto (30/08) |

---

## O que fazer a seguir

**Nada está pendente e não há backlog aberto.** Ficam duas ressalvas, nenhuma
delas trabalho parado:

- **Verificar num aparelho de verdade.** Toda a medição da rodada de celular e
  tablet foi feita com viewport emulada. Layout, alvo de toque e ausência de
  rolagem lateral estão medidos; o que emulação não prova é o toque de fato, a
  rolagem por dentro do gráfico e da tabela com o dedo, e a barra do navegador
  comendo a altura. Ver [[verificar-no-ambiente-certo]] — nesta base já houve
  três "funciona" que eram falsos por ambiente errado.
- **A rotação continua contida, não corrigida.** O gráfico permanece desenhado
  na largura antiga até o próximo rerun; o que a rodada garantiu é que isso não
  desliza mais a página nem esconde a tabela. Não há conserto conhecido — ver a
  tabela de tentativas no `DESIGN.md`.

Abaixo, o que cada leva entregou, para quem precisar do porquê.

**1. Reflow de gráfico: confirmado (29/08/2026).** Girando 812×375 → 375×812
sem recarregar, o container do gráfico foi a 343px e o SVG ficou em 780. No
mesmo giro o Streamlit trocou o padding lateral e re-empilhou as colunas — o
layout do navegador reagiu, só o `layout.width` do Plotly não. `Plotly.Plots.
resize` e `Plotly.relayout` foram chamados na figura viva e nenhum moveu o SVG.
A tabela do `DESIGN.md` fica onde está.

O que mudou é o alcance: no celular o gatilho é a **rotação**, não o arrasto de
janela. As duas consequências foram contidas na rodada de `adapt` (o gráfico
rola por dentro, a tabela é presa à coluna e se remede). O gráfico continua
desenhado na largura antiga até o próximo rerun — não há conserto, só
contenção.

**1b. `/impeccable adapt`** (commit `2f8ef53`). Celular e tablet,
desktop intocado (verificado a 1440: ponteiro fino, padding 80px, capa −80px,
h2 28px, 4 KPIs lado a lado, nenhuma regra nova ativa).

- Fronteiras: 864px (onde o Streamlit troca o padding lateral) e 640px (onde
  ele para de empilhar colunas lado a lado); `pointer: coarse` para o dedo.
- Corrigido um defeito real: abaixo de 864px a capa cancelava 80px de padding
  que não existiam mais e a página deslizava de lado (832px de conteúdo numa
  janela de 768).
- Tablet em retrato: par e trio de gráficos passam a ocupar a largura inteira
  (eram 360px e 235px por gráfico); KPIs viram grade de dois.
- Dedo: 44×44 em slider, campos, botões, expansor, checkbox e nos dois
  controles da gaveta de filtros; ✕ do chip a 36 (exceção declarada); barra de
  ferramentas da tabela visível onde não há hover.
- `DESIGN.md`: subseção "Tela estreita e dedo" em Layout, mais a Regra das
  Duas Perguntas.

**2. O cabeçalho-extrato** (commit `5a1086f`). Rodada de
`/impeccable bolder` sobre a tela inteira. O movimento é um só: o degrau de
Display deixou de servir ao nome da tela e passou a servir à quantia.

- `show_month_signal`, `show_kpis` e `show_savings_line` viraram `ledger_head`.
- O `h1` virou **placa**: wordmark de 38px ao lado do nome da tela em
  `clamp(22px, 2.2vw + 12px, 28px)`. O `st.logo` saiu — a marca fica num
  lugar só. A quantia ficou em `clamp(40px, 3.5vw, 50px)`/700/−0.025em
  — meio termo pedido pelo André entre os 68px da primeira rodada e os 32px
  da segunda.
- Os três tiles de KPI viraram duas linhas de legenda; nenhum número sumiu.
- `padding-top` do `.block-container` virou `calc(60px + 2.25rem)` — o
  cabeçalho do Streamlit tem 60px e fica por cima; sem isso a placa entrava
  debaixo dele.
- `DESIGN.md`: componentes **Placa** e **Ledger Head** (este substitui Signal
  Line e Savings Line); tokens de `display`, `section`, `page-top` e as regras
  novas.

Verificado a 1440 e a 375, com filtro de abertura e com "Limpar filtros"
(R$ 10.201,76, recorte "Nov/2025 – Ago/2026"). Detector limpo sobre o bloco
`<style>` extraído.

**3. A escala de espaço** (commit `95e2a99`). Rodada de
`/impeccable layout`. O Streamlit empilha tudo com `gap: 16px` e a coluna não
tinha cadência nenhuma fora do título de seção.

- Três degraus com papel: cola 8px, base 16px, solta 28px. Abaixo de um título,
  20px para o que pertence a ele e 28px para conteúdo novo.
- Escritos como deltas de `margin-top` sobre os 16px, com seletores `:has()`
  que miram papel (legenda, controle, conteúdo), não posição.
- Slider limitado a 30rem, e o rótulo abre 1.25rem para o valor flutuante não
  cair em cima dele.
- `DESIGN.md`: a escala em Layout, mais as regras do Papel do Espaço, da
  Legenda que Cola e do Controle que Pertence.

Medido no render: todo intervalo da coluna caiu em 8, 16, 20 ou 28 — nenhum
valor solto. Detector limpo (geral e `--scope layout`).

**4. A tipografia** (commit `db8d777`). Rodada de
`/impeccable typeset`.

- **Medida 72ch** na prosa da coluna. Media 166 caracteres por linha a 1440px
  — mais que o dobro do confortável. É a maior correção da rodada.
- **+0.01em** em tudo que é 14px: compensação de texto claro sobre fundo
  quase preto, o eixo que faltava (entrelinha e peso já estavam).
- **Entrelinha explícita** no veredito (1.4) e no valor do KPI (1.2). O 20px
  tinha três entrelinhas diferentes na mesma tela.
- **`R$\u00a0valor`** e separador `\u3000\u2060·\u3000`: com a medida curta a
  quantia quebrava entre o cifrão e o número.

Medido no render a 1440 (72ch) e a 375 (49ch), os dois dentro da faixa.
Detector limpo, geral e `--scope type`.

**5. Toda marca leva o seu valor** (commit `db8d777`). Pedido do André
olhando o gráfico de economia por tipo de prato: o padrão de rótulo daquele
gráfico vale para todos, qualquer que seja a grandeza.

- O teto `MAX_ROTULOS = 8` saiu. Ele apagava o número justamente nos painéis
  mais densos ("Top 15/30", "Por mês"), que são os que mais custam de ler no
  eixo.
- `_bar` e `_line` rotulam sozinhos a partir da série; `text=` sobra só para
  quando o rótulo não é o valor. Formato pelo dtype: inteiro é contagem
  (`1.234`), fracionário é dinheiro (`R$ 1.234`).
- Corpo fixo em 11px com `constraintext="none"` e `cliponaxis=False`.
- A rosca mostrava porcentagem só nas fatias ≥8%; agora toda fatia leva o
  valor.
- Heatmap já rotulava as células com pedido.

`uniformtext` foi tentado e **não serve**: com `mode="show"` iguala todos pelo
menor rótulo e a série inteira encolhia por causa de uma barra curta.

Verificado com filtros limpos nos casos densos: 10 meses, 12 meses sazonais,
top 15 horizontal, linha de ticket médio, rosca e 375px.

**6. A cor dos estados** (commit `db8d777`). Rodada de
`/impeccable colorize`. A tela parecia disciplinada porque eu nunca tinha visto
um alerta — e eles aparecem o tempo todo, já que o recorte de abertura é um mês
e metade dos painéis abre sem série.

- `st.info/warning/error/success` saíam como **bloco preenchido de raio 0** em
  quatro matizes de fora, incluindo o **amarelo** que a paleta mede e rejeita.
  Agora herdam a anatomia da casa e a cor vem das três matizes: neutro para
  "nada a mostrar", Dinheiro para "algo errado", Economia para "deu certo".
- Outros achados fora da paleta, todos corrigidos: a tinta de fundo do chip de
  delta (`rgba(61,213,109,.2)`), o chip de `código` em verde de sucesso, a
  barra de hover da tabela, a caixa do checkbox, os ícones do multiselect, e
  **dois cinzas de botão secundário** que faziam a escada de três superfícies
  virar cinco.

**Como medir isso de novo:** varredura no navegador comparando todo
`color`/`backgroundColor` renderado contra a paleta. Antes: 11 valores de fora.
Depois: **zero**. Metade só aparecia em hover ou em estado vazio — a olho, não
se acha.

**7. Movimento** (commit `db8d777`). Rodada de `/impeccable animate`.
A tela não tinha movimento nenhum — toda transição do Streamlit vem com
duração zero.

- **Medido:** uma troca de painel leva ~985ms, e nesse intervalo a tela mostra
  o painel anterior sem sinal nenhum além do spinner do canto.
- Enquanto o rerun está em voo (gatilho: o `stStatusWidget` existir), a coluna
  de conteúdo cai para 55%. A sidebar não — é onde está o controle na mão.
- Assimetria: descer espera 220ms e leva 220ms; subir não espera e leva 160ms.
- 120ms de cor em botão, chip e checkbox. Curva única
  `cubic-bezier(0.16, 1, 0.3, 1)`.
- Sem momento focal, por decisão: o Streamlit remonta tudo a cada rerun, então
  animar entrada de conteúdo viraria coreografia a cada filtro.

**Limitação da verificação:** com o painel do navegador ESCONDIDO o Chrome não
avança transição nenhuma (`visibilityState: hidden`), então não dá para ver o
efeito. O que dá para provar é o objeto `CSSTransition` que o browser criou —
`getAnimations()` devolve prop, duração, atraso, curva e keyframes. Confirmado
assim: ida 1→0.55 em 220ms com 220ms de atraso, volta em 160ms sem atraso,
sidebar em 1. O *feel* continua não verificado; abra o painel e troque de
painel de análise para julgar.

**8. Capa no topo** (commit `92c630c`). Pedido do André: a foto que ele largou em
`assets/` vai no topo do corpo principal, no feitio das capas do Notion, com
transição suave para o conteúdo.

- A foto escolhida foi a **diurna** (`static/capa-avenida.jpg`), depois de
  comparar com uma noturna na tela. Redimensionada de 2172px para 1600 e
  reencodada: 424 KB → 176 KB. **Servida, não embutida** — o markdown vai pelo
  websocket a cada rerun.
- Os originais ficam em `assets/`: `capa-avenida-original.jpg` (master) e
  `capa-noturna.jpg` (a descartada, guardada a pedido de ninguém — apagar se
  não for usar).
- Altura `clamp(180px, min(36vh, 66vw), 360px)`: 36vh é um quinto a mais que os
  30vh do Notion, pedido do André para caber a bolsa e o topo do capacete.
- Sangra os 80px de padding do `.block-container` (16px no estreito) e some por
  `mask-image`, não por faixa de gradiente por cima.
- `object-position: center 31%` e o esmaecimento começando aos 55% (e não
  45%): é o que decide se o logo da bolsa ainda se lê — a 45% ele saía a ~65%
  de opacidade, a 55% sai a ~80%.
- **O `min(36vh, 66vw)` é o conserto do estreito:** em 375px a foto renderiza
  com ~250px de altura, e caixa mais alta que isso faz o `cover` AMPLIAR a
  imagem — aí ela é cortada nas laterais, o `object-position` vertical perde o
  efeito e o céu volta ao quadro. 66vw é a altura que a imagem tem naquela
  largura.
- Começa em y=60, embaixo do cabeçalho do Streamlit, que é **opaco e da cor da
  página** — a capa passaria por baixo dele sem aparecer.
- Dois cancelamentos verticais com donos diferentes: o container zera o gap de
  16px (o bloco do `<style>` conta como irmão de altura zero) e a capa zera o
  respiro de 2.25rem.

**10. Performance** (commit `d710f6d`). Rodada de `/impeccable optimize`.
O Streamlit reexecutava a página inteira a cada widget.

- **Medido antes:** marcar "Crescente" na tabela custava 818–1007ms, com 585ms
  de main thread bloqueada, remontando KPIs, contrafactual e gráficos.
- **Quatro `@st.fragment`, um por alcance de controle:** a tabela, "Quando e
  quanto", "Restaurantes e itens", e o par resumo+contrafactual. Este último é
  um fragmento só porque o slider de otimismo mora embaixo e alimenta o
  veredito de cima — separá-los congelaria o número do topo.
- Depois: ordenar a tabela ~140ms, trocar de painel ~400ms, passo do otimismo
  ~500ms. Gráficos e tabela fora do fragmento provados intactos (marca em nó
  DOM + `isConnected`).
- `_to_excel` cacheado: a planilha do export era montada em todo rerun (137ms
  de openpyxl) porque o `download_button` exige os bytes para desenhar o
  botão. Agora 1,7ms no cache, com `max_entries=8` porque a busca é texto
  livre.
- O wordmark saiu do `data:` URI (63 KB por rerun) para `static/
  ifood-logo.webp`, 240px para os 38px em que aparece. O hash do `?v=` é
  cacheado — a capa eram 176 KB relidos e digeridos a cada rerun.
- **Medido e descartado:** mover o bloco de CSS de 35 KB para arquivo estático.
  O nó `<style>` e a `<img>` sobrevivem a um rerun completo (provado com marca
  em nó DOM) — o React não os reinsere, então não há custo de reinserção a
  cortar, e o ganho não pagaria a armadilha de truncamento do servidor
  estático.
- O que sobra dos ~500ms do slider é Plotly redesenhando os dois gráficos da
  seção. O lado Python é ~15ms. Não há mais o que cortar sem mexer no que a
  tela mostra.

**11. Polimento** (commit `90d9d8f`). Rodada de `/impeccable polish` sobre as
pendências da crítica de 28/08.

- Confirmados **já resolvidos** no render, não no changelog: o classificador
  de pratos (parmegiana não sai mais como bebida), os quatro painéis
  tautológicos (`painel_vazio` cobre os quatro), os alvos de toque, zero
  `box-shadow` computada na página, nenhum raio fora do sistema, medida em
  72ch.
- Corrigido o que sobrou, e é estado enganoso: o veredito do mês roda sobre o
  histórico inteiro e a quantia ao lado é do filtro. Com o filtro de mês
  limpo, "12% acima da média" encostava num total de dez meses e nada na linha
  dizia que os 12% eram de agosto — a declaração existia, mas no fim de uma
  legenda de 14px dois blocos abaixo. Agora o escopo entra na frente da frase
  ("Em agosto de 2026, 12% acima da média") e só quando os dois não coincidem.
- `DESIGN.md`: a regra do escopo no componente Ledger Head, mais o `Don't`.

**12. O seletor de perfil** (commits `3605721`, `0fa6b51`, `39313e0`). Começou
como "essa bolinha está desalinhada" e terminou trocando a forma de um
controle. Vale ler inteiro porque **duas correções minhas seguidas trataram
sintoma**:

- **A bolinha do slider** (`3605721`). A área de toque crescia por `padding`
  com margem negativa — técnica certa para elemento sem tinta, errada para
  este: o polegar tem fundo e raio de 100%, então o padding pintava a bolinha
  em 24 e a margem a puxava 6px acima do centro da trilha. No dedo era 44 de
  padding e 44 de bolinha. A área agora vai num `::after` transparente.
- **O cursor de texto** (`0fa6b51`). `caret-color: transparent` no input do
  `stSelectbox`. Primeiro condicionei ao menu fechado — errado, é com o menu
  aberto que se olha para o campo.
- **`/impeccable critique` no seletor: 14/36** (dois agentes, snapshot em
  `.impeccable/critique/2026-08-29T15-53-48Z__dashboard-py-seletor-de-perfil.md`).
  O diagnóstico: a feiura era **derivada da forma**. Um combobox de busca, com
  filtragem por digitação e estado "Nenhum resultado", para escolher entre
  duas pessoas. E o meu conserto anterior foi o pior dos três — apaguei o
  caret e o `outline` de 2px foi pousar no mesmo `<input>` de 2px, virando uma
  lasca vermelha de ~6×24 colada no nome. Mesmo pixel, outra cor.
- **A troca de forma** (`39313e0`). `st.segmented_control`, o mesmo componente
  do seletor de painel, com o estado ativo que o DESIGN.md já especificava.
  Volta a ser menu quando os nomes não couberem: ≤3 perfis **e** o nome mais
  longo cabendo no segmento, medido, porque o nome é editável.
- **O nome saiu da gaveta:** o rótulo da quantia leva a pessoa. No celular a
  gaveta abre recolhida, e sem isso o número que o produto existe para fazer
  doer é anônimo.
- **Dez furos de sistema no mesmo passe:** anel de foco na caixa e não no
  input; campo em `surface-raised` (era `surface-base`, 1,02:1 contra a
  gaveta); menu sem sombra, subindo para `surface-raised` com fio; pílula da
  opção escolhida saindo de `#95a4c1` para tinta de 10% do vermelho com peso
  600; `line-height` 19,6 → 22,4; `cursor: pointer`; hover mudando o fio;
  `<title>open</title>` e `<title>Delete</title>` traduzidos; alvo do chevron
  (era CSS morto: `svg[role="button"]` não casa com o que o BaseWeb emite);
  campo em 44px no dedo.

**13. Nada mais está pendente.** Não há backlog aberto — as duas ressalvas
abertas estão no topo desta seção.

---

## Decisões que NÃO devem ser reabertas

- **Visão conjunta dos dois perfis: descartada** (28/08). Um perfil por vez,
  também na leitura. O `/impeccable critique` chamou isso de "a metade
  faltante do produto" — está errado, é escolha. Ver `PRODUCT.md`,
  "Capabilities and Constraints".
- **Barra de otimismo: fica.** Foi trocada por uma faixa e o André mandou
  voltar. A faixa não volta.
- **Quatro tiles na seção de cozinhar: ficam.** Mesma história.
- **Os três tiles do topo viraram legenda** (28/08, no `bolder`). Não é a
  mesma decisão dos quatro tiles da seção de cozinhar: aqueles continuam
  tiles. Aqui o que substituiu os três foi um número em Display, não um
  corte — pedidos e ticket médio seguem na tela, uma linha abaixo.
- **Erros `<rect> negative width` no console: não são pendência.** Provado em
  29/08 com viewport fixado antes do load: aba nova a 1280×800 e a 375×812,
  inclusive no painel "Top restaurantes" (o de maior `automargin`, 212px) —
  **zero erros**. O gatilho é a aba do painel carregar com `innerWidth` 0, e aí
  todo `st.columns` fica com largura 0, o filho herda os 16px de `min-width` do
  Streamlit e o Plotly faz `16 − automargin`. Contagem de console em aba com
  viewport zerado não vale nada: eu já reportei essa contagem como bug do app,
  e não era.
- **Coleta manual, perfis isolados, tudo local.** As três restrições
  invioláveis do `PRODUCT.md`, já testadas contra uma tentativa de deploy.

---

## Armadilhas que vão morder de novo

**Defeito na réplica hospedada pode ser commit parado.** O Streamlit
Community Cloud só redeploya no push; um conserto commitado e não empurrado
deixa a nuvem rodando o código velho, com o sintoma idêntico ao do bug
original. Confira `git status -sb` contra `origin/main` ANTES de reinvestigar
um bug já corrigido. E leia o `-sb` do git de verdade: a contagem de "ahead"
da saída filtrada disse 1 quando eram 5.

**`aria-selected` do BaseWeb segue o item REALÇADO, não o escolhido.** Numa
lista de opções, quem marca a escolha é uma pílula que é um `<div>` DENTRO do
`<li>` — e ela vinha com `#95a4c1`, cor que não existe na paleta. Quem
estilizar por `aria-selected` sem olhar o DOM pinta a linha errada. Confira o
atributo real antes de escrever a regra.

**A técnica de crescer alvo com `padding` + margem negativa só serve para
elemento sem tinta.** Onde o elemento tem fundo, o padding pinta o alvo
inteiro e a margem negativa o desloca. Com tinta, a área vai num `::after`
transparente.

**O detector do impeccable não lê `.py`.** `detect.mjs dashboard.py` devolve
`[]` porque a extensão não está na lista de varríveis — vazio por construção,
não limpo. Para ter sinal, extraia o bloco `<style>` para um `.html` e varra
isso. O motor de URL exige `puppeteer`, que não está instalado.

**Uma observação contra a pegadinha do tamanho fixo.** O bloco morto do
`alt="Logo"` foi removido do `localize.html` **com o servidor no ar**, e o
`curl` do `/app/static/localize.html` voltou byte a byte igual ao arquivo
(6553, mesmo md5) — sem truncar. Um ponto só, e a favor: a pegadinha
documentada abaixo custou uma sessão e fica onde está. Se for editar, o
caminho seguro continua sendo com o Streamlit parado.

**Medir com o painel do navegador escondido dá zero.** `innerWidth` volta 0,
o `.block-container` mede 32px e todo `clamp` cai no piso — a tela parece
quebrada e não está. Confira `innerWidth` antes de acreditar em qualquer
medida. Mordeu duas vezes: na rodada de `bolder` e de novo em 29/08, onde
produziu um bug inexistente com contagem e tudo. **O conserto é
`resize_window` ANTES de navegar** — a emulação sobrevive ao reload, e o
painel não segura viewport sozinho entre chamadas de ferramenta.

**Screenshot exige o painel do navegador visível.** Com ele escondido a página
não compõe frames e a captura estoura em 5s; leitura de texto, estilo
computado e geometria continuam funcionando. Dá para verificar quase tudo sem
pixel — menos julgar o desenho.

**O `.stMarkdown p` do Streamlit ganha de classe sozinha.** Regra de `<p>`
própria precisa do prefixo `.block-container`, senão o tamanho não aplica e o
sintoma é um texto no meio do caminho entre o degrau pedido e o default.

**O cabeçalho do Streamlit tem 60px e fica POR CIMA do conteúdo.** Qualquer
mexida no topo da página tem que descontar isso.

**Editar `static/localize.html` exige reiniciar o Streamlit.** O servidor
estático fixa o tamanho do arquivo no start: com o servidor no ar, ele serve o
conteúdo novo **truncado no tamanho antigo**, o script quebra no meio e o erro
não aparece no console da página (fica no do iframe). Sintoma: nada aplica.
Diagnóstico: `curl <url> | wc -c` contra `wc -c <arquivo>`.

**O navegador cacheia `/app/static/`.** Resolvido: a URL do iframe leva
`?v=<hash do arquivo>`. Não remova.

**`st.metric` e o cifrão.** Dois `$` na mesma string viram LaTeX e o Streamlit
engole o trecho. Use `_brl(..., md=True)` em markdown, e um `R$` só quando o
valor for uma faixa.

**`st.metric` e o menos.** No `delta`, o sinal tem que ser o hífen ASCII. Com
`−` (U+2212) o Streamlit não reconhece como negativo e inverte cor e seta.

**`st.logo` (1.58) não aceita `alt_text`.** Quebra com `TypeError`. O `alt` é
corrigido no `localize.html`.

**Console do navegador só dá veredito em aba nova e em primeiro plano.** O
buffer persiste entre navegações na mesma aba, e aba em segundo plano renderiza
em container de largura zero e enche o console de erros que não existem no uso
real.

---

## Invariantes que o código sustenta

Se você mexer no dinheiro, estes precisam continuar verdadeiros — teste com
`data/orders.db` real, não com amostra:

- `itens + entrega + serviço == total` em qualquer recorte. A fatia de itens
  sai de `total − taxas`, nunca de `subtotal − cupom`: o preço de tabela **não**
  reconstrói o total (promoção e clube abatem por fora, em 120 dos 259 pedidos).
- `sav["paid"].sum() == total − taxas`. Cada item é rateado até o que o pedido
  custou de fato.
- Pedido não entregue nunca entra em soma de dinheiro.
- O sinal do mês compara o mesmo recorte de dias, e roda sobre o histórico
  inteiro, não sobre o filtrado.
