---
target: seletor de perfil (dashboard.py)
total_score: 14
max_score: 36
na_heuristics: 9
p0_count: 0
p1_count: 2
timestamp: 2026-08-29T15-53-48Z
slug: dashboard-py-seletor-de-perfil
---
Method: dual-agent (A: aae7d3d794d5ab1b6 · B: a7f960e6576e4fa9e)

# Crítica — o seletor de perfil

## Design Health Score

| # | Heurística | Nota | Achado principal |
|---|---|---|---|
| 1 | Visibilidade do estado | 1 | Zero ocorrências de "André"/"Carol" no conteúdo principal; no celular a gaveta abre recolhida |
| 2 | Correspondência com o mundo real | 2 | "Perfil" é palavra de sistema para "pessoa"; a legenda expõe `Banco: default` |
| 3 | Controle e liberdade | 3 | Reversível em um gesto; desconto: digitar "zz" apaga "André" e só Escape volta |
| 4 | Consistência e padrões | 1 | Dois tratamentos de foco no mesmo componente; chevron em ink-primary; sombra; `<title>open</title>` |
| 5 | Prevenção de erro | 2 | Alcança "Nenhum resultado", estado sem razão de existir com duas pessoas |
| 6 | Reconhecimento vs. memória | 1 | Duas pessoas, e a segunda está atrás de um clique |
| 7 | Flexibilidade e eficiência | 1 | Dois cliques + rerun para escolha binária; busca por digitação para conjunto de 2 |
| 8 | Estética e minimalismo | 1 | Preenchimento 1,02:1 contra a sidebar, borda 1,21:1; rótulo e valor idênticos |
| 9 | Recuperação de erro | n/a | Escolhedor de duas opções não produz erro |
| 10 | Ajuda e documentação | 2 | Tooltip é o único lugar que explica o isolamento, em alvo de 16x16 a 209px do rótulo |
| **Total** | | **14/36** | Bem abaixo da faixa típica |

## Veredito de especificidade

É o combobox do BaseWeb com demão fina de tinta. Autorado: cor da borda, raio 8px, `caret-color: transparent`, texto do tooltip. O bloco do perfil é byte a byte idêntico aos seis multiselects de filtro abaixo dele — "quem é a pessoa" tem o mesmo desenho que "Faixa de valor".

Varredura determinística: `detect.mjs` devolveu `[]` para `dashboard.py`, vazio POR CONSTRUÇÃO (`.py` não está em SCANNABLE_EXTENSIONS, detector/node/file-system.mjs:26). CSS extraído para `.html` e varrido: `[]` real, validado com canário que devolveu 3 achados. Nenhum anti-padrão estático; tudo abaixo veio de medição no render. Sem overlay: painel do navegador escondido na sessão.

## Impressão geral

O conserto anterior apagou o caret e deixou um sósia vermelho no mesmo pixel: com foco de teclado, o `outline: 2px solid #ea1d2c` pousa no `<input>` de 2px, produzindo anel de ~6x24px colado no "é" de André dentro de um campo de 260x40. Causa raiz anterior: um combobox de busca para escolher entre duas pessoas.

## O que está funcionando

1. Texto do tooltip: "Cada perfil é uma pessoa, com banco de dados separado" resolve a ambiguidade do rótulo em nove palavras.
2. `aria-label="André selecionado. Perfil"` diz estado e função numa frase.
3. Centragem perfeita: valor e chevron com delta 0,00px do centro do campo nos dois breakpoints.

## Problemas prioritários

**[P1] O anel de foco virou o caret.** Outline de 2px num input de 2x19,6px = anel de ~6x24px, folga 0,00px do nome. O "?" ao lado usa outro tratamento (box-shadow 3.2px rgba(201,16,29,.5)) porque o `:focus-visible` perde para `outline: none` do emotion. Borda do `:focus-within` dá 2,5:1 contra o campo (WCAG 1.4.11 pede 3:1). Fix: anel em `[data-baseweb="select"] > div` via `:has(input:focus-visible)`, e `cursor: pointer` no lugar de `text`. Command: /impeccable polish

**[P1] A forma está errada.** `role="combobox"` com autocomplete e filtragem para conjunto de dois. O sistema já tem segmented control documentado (ativo #f0787f, peso 600, tinta 10%, fio, `aria-pressed` à mão) — gasto em "qual painel" e não em "qual pessoa". Fix: `st.segmented_control` para o perfil. Custo: em 260px, 2 nomes ~126px, 3 ~82px, 4 truncam; nomes são editáveis. Regra: segmentado enquanto <=3 perfis e o nome mais longo couber. Command: /impeccable shape

**[P2] O campo mal existe como forma.** Preenchimento #0e1117 contra sidebar #0b0e14 = 1,02:1; borda #1e242e = 1,21:1. O token `components.input-select.backgroundColor` aponta para surface-raised (#161b24), não surface-base. Hover não muda nada. Command: /impeccable polish

**[P2] A tela não diz de quem é o dinheiro.** Zero "André"/"Carol" no conteúdo principal; em 375px a sidebar carrega recolhida. Fix: nome como legenda da quantia ou na caption de procedência. Command: /impeccable clarify

**[P3] Quatro furos de sistema.** Sombra no popover num sistema de sombra zero (existe porque menu sobre sidebar dá 1,02:1). Pílula do item em #95a4c1, fora da paleta, marcando a escolha a 1,26:1. `line-height: 19.6px` no campo contra 22,4px do token, e o menu usa 22,4 — divergem entre si. `<title>open</title>` em inglês. Regra de alvo do chevron é CSS morto (`svg[role="button"]` não casa; padding 0px medido). Campo em 40px no dedo contra 44 dos botões vizinhos. Command: /impeccable polish

## Red flags por persona

**Carol (não roda ./run.sh):** senta na frente dos números do André sem nada dizer isso; precisa reconhecer que um campo idêntico a "Faixa de valor" decide de quem é a vida na tela; não sabe que existe uma segunda opção; no celular a gaveta abre fechada; nunca abre o "?" de 16px a 209px do rótulo, logo nunca lê a garantia de isolamento.

**André (noite, cansado):** I-beam num controle sem digitação; traço vermelho de 10px grudado no nome, lendo como bug de render; dois cliques + rerun para escolha binária; a coisa mais alta da gaveta é manutenção.

**Teclado/leitor de tela:** tabulação skip-link → "?" → campo (a ajuda antes do que explica); foco ocupando 3,8% da área do alvo.

## Observações menores

- B corrigiu A: o menu MARCA a escolha (pílula 15%, 1,26:1). E `aria-selected` do BaseWeb segue o cursor, não a escolha — quem auditar por ele conclui errado.
- Assimetria óptica de 5px: 14px à esquerda do texto, 9px à direita do chevron.
- Rótulo e valor tipograficamente iguais (14px/400/#e6e8ec); a regra do rótulo que recua não chegou aqui.
- `Banco: default (chave fixa, não muda)` expõe implementação; a chave do André é `default` e é ordenada em primeiro.
- O bloco do perfil não é um bloco: Perfil → Coletar → Recarregar → Renomear.
- Armadilha nova: com `initial_sidebar_state="auto"` o Streamlit decide "recolhida" no primeiro paint com viewport 0 e não remonta ao redimensionar; é preciso reload DEPOIS do resize, senão a sidebar não existe no DOM.

## Perguntas a considerar

1. Se isolamento é correção e não configuração, por que só uma palavra de 14px em 1,02:1 nomeia a pessoa, e nenhum número carrega esse nome?
2. Por que "qual painel de análise" ganhou o segmented control autorado e "qual pessoa" não?
3. A única ação preenchida em vermelho é manutenção. Deveria estar acima do controle que diz de quem é a conta?
4. O caret era o problema — ou o combobox era?
