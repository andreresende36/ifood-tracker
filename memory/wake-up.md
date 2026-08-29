# Wake-up — iFood Order Tracker

Estado em **28/08/2026**, fim da sessão de design. Última linha do `git log`:
`e833b24`.

Leia junto: `PRODUCT.md` (verdade de produto), `DESIGN.md` (sistema visual e
as regras nomeadas), `.impeccable/critique/` (a auditoria de UX que originou
metade do trabalho abaixo).

---

## Onde estamos

O painel passou por três rodadas do `/impeccable` nesta sessão: **shape**
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

---

## O que fazer a seguir

**1. Confirmar se o reflow de gráfico é bug de verdade.** É a única coisa
esperando alguém.

Abra com `./run.sh`, role até um gráfico e **arraste a borda da janela**.

- Se o gráfico redesenhar na largura nova → **não há bug.** Apague a tabela
  "Limitação conhecida — o gráfico não segue a janela" do `DESIGN.md`.
- Se ficar na largura antiga até recarregar → está confirmado, e a tabela com
  as cinco tentativas fica onde está.

Tudo foi medido com viewport emulada, que pode não disparar o `ResizeObserver`
do Streamlit. Por isso a dúvida.

**2. Nada mais está pendente.** Não há backlog aberto.

---

## Decisões que NÃO devem ser reabertas

- **Visão conjunta dos dois perfis: descartada** (28/08). Um perfil por vez,
  também na leitura. O `/impeccable critique` chamou isso de "a metade
  faltante do produto" — está errado, é escolha. Ver `PRODUCT.md`,
  "Capabilities and Constraints".
- **Barra de otimismo: fica.** Foi trocada por uma faixa e o André mandou
  voltar. A faixa não volta.
- **Quatro tiles na seção de cozinhar: ficam.** Mesma história.
- **Erros `<rect> negative width` no console: não são pendência.** O gatilho é
  container de largura zero (aba em segundo plano). Carga normal é limpa.
- **Coleta manual, perfis isolados, tudo local.** As três restrições
  invioláveis do `PRODUCT.md`, já testadas contra uma tentativa de deploy.

---

## Armadilhas que vão morder de novo

**O detector do impeccable não lê `.py`.** `detect.mjs dashboard.py` devolve
`[]` porque a extensão não está na lista de varríveis — vazio por construção,
não limpo. Para ter sinal, extraia o bloco `<style>` para um `.html` e varra
isso. O motor de URL exige `puppeteer`, que não está instalado.

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
