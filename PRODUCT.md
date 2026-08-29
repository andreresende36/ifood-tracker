# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

André e Carol, o casal, **juntos na mesma tela**. Sentam para olhar e alternam
entre os dois perfis para ver o gasto de cada um, um de cada vez. Não é um
painel administrativo com um dono e um convidado: os dois perfis são de
primeira classe, e trocar de perfil é uso normal, não manutenção.

Contexto de uso: máquina local do André, em casa, sessão deliberada — alguém
abriu o terminal e rodou `./run.sh` porque quis olhar. Nunca é uma aba que
ficou aberta o dia inteiro.

## Product Purpose

Cortar o gasto com delivery.

O produto existe para transformar um extrato disperso do iFood em um número
que doa o bastante para mudar comportamento. A seção **"E se você tivesse
cozinhado em casa?"** é o coração do produto, não um enfeite: é ela que
converte "gastei R$ 18 mil" em "R$ 9,7 mil disso era evitável".

Sucesso é o casal olhar, reconhecer um padrão que não enxergava (o dia da
semana, o restaurante recorrente, o peso das taxas) e pedir menos.

## Positioning

O extrato do próprio iFood mostra pedidos; não mostra padrão nem
contrafactual. Este produto extrai o histórico **completo** da conta — anos,
não as últimas páginas — e o cruza consigo mesmo: por hora do dia, por dia da
semana, por restaurante, por prato, e contra uma estimativa de quanto o mesmo
prato custaria feito em casa.

Dois perfis com bancos isolados é a outra metade: cada conta tem o próprio
histórico completo, e trocar de perfil é um gesto de uma tela.

## Operating Context

- Rodado por `./run.sh`, que pergunta o perfil e se deve coletar antes de abrir.
- A coleta abre uma janela **visível** do Chrome com perfil dedicado por pessoa.
  Login é manual na primeira vez; captcha é resolvido a olho, na hora.
- Cada pessoa tem seu banco SQLite em `data/` e seu diretório de sessão do
  Chrome em `profiles/`.
- O dashboard abre já filtrado no mês corrente, categoria Restaurante e status
  Entregue — o recorte que responde "quanto já gastamos neste mês".

## Capabilities and Constraints

Faz: coleta o histórico via interceptação da API do iFood; guarda em SQLite por
pessoa; filtra por período, categoria, status, dia da semana, faixa de valor e
restaurante; mostra KPIs, análise temporal, heatmap hora × dia, top
restaurantes e itens, composição do que foi pago; estima a economia de cozinhar
em casa; exporta CSV e Excel.

Restrições que trabalho futuro **não pode violar**:

- **Nunca sai da máquina local.** Sem deploy remoto, sem nuvem. Isso já foi
  tentado (Railway) e foi exatamente o que quebrou o isolamento entre os
  perfis. É decisão, não limitação técnica.
- **Perfis sempre isolados, inclusive na leitura.** Um banco por pessoa, e a
  tela mostra **um perfil por vez**. Pedido de um jamais pode aparecer no outro
  — é propriedade de correção, não preferência. Somar os dois numa visão
  conjunta foi considerado e **descartado por decisão do André** (28/08/2026):
  a soma exigiria ler os dois bancos no mesmo lugar, e o isolamento vale mais
  do que o número agregado.
- **Coleta sempre manual.** Sem agendamento, sem cron, sem coleta automática ao
  abrir. Roda quando alguém manda, com o Chrome à vista.

Limitação conhecida: a API do iFood devolve só uma janela do histórico. Pedidos
mais antigos que ela permanecem no banco como foram gravados e não são
reverificados por coletas novas.

## Brand Commitments

Identidade visual do iFood, por escolha explícita do usuário: logo em
`assets/ifood-logo.png` (wordmark) e `assets/ifood-icon.png` (símbolo em tile,
para favicon), vermelho `#ea1d2c` amostrado do próprio logo.

Uso é pessoal e local — a ferramenta consome a conta do próprio usuário e nunca
é publicada. Não é um produto do iFood nem se apresenta como tal.

Idioma: português do Brasil, em toda a interface.

## Evidence on Hand

Dados reais, não amostra: 259 pedidos do André (nov/2025 a ago/2026) e 131 da
Carol, em `data/orders.db` e `data/carol.db`.

**A economia é estimativa, não medição.** Os percentuais de "quanto sai mais
barato em casa" são heurísticos por tipo de prato, definidos no código, e o
dashboard tem um controle de otimismo que os escala. Trabalho futuro não pode
apresentar esses números como valor apurado, e a interface precisa continuar
dizendo que são estimativa.

Não existem: benchmark de mercado, dados de outros usuários, integração com
banco ou cartão, nem qualquer fonte além da própria conta do iFood.

## Product Principles

1. **O número precisa doer.** O produto falha se o casal olha, acha
   interessante e não muda nada. Contrafactual acima de contemplação.
2. **Isolamento entre pessoas é correção, não configuração.** Qualquer mudança
   que possa misturar os perfis está errada por construção.
3. **Local por decisão.** Conveniência de acesso remoto não vale o custo que já
   foi pago uma vez.
4. **Coleta é um ato, não um processo.** Automatizar a coleta foi o que
   produziu dados inconsistentes; ela continua sendo algo que alguém faz.
5. **Estimativa se declara.** Onde o dado é inferido, a tela diz que é.
