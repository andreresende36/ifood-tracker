# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

André e Carol, o casal, **juntos na mesma tela**. Sentam para olhar e alternam
entre os perfis: o dela, o dele e o dos dois somados. Não é um painel
administrativo com um dono e um convidado: os dois perfis são de primeira
classe, e trocar de perfil é uso normal, não manutenção.

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

- **A verdade do dado é sempre local.** Coleta, login no iFood e escrita nos
  bancos SQLite acontecem só na máquina local, com o Chrome à vista. Nenhum
  processo remoto autentica na conta de ninguém, nenhum processo remoto grava
  em `data/*.db`. Isso é decisão, não limitação técnica, e não muda com a
  réplica hospedada abaixo.

  **Revisão de 29/08/2026:** até aqui a regra era "nunca sai da máquina
  local — sem deploy remoto, sem nuvem", depois de uma tentativa no Railway
  ter subido tudo: bancos, dashboard, scraper e o login das duas contas do
  iFood rodando remoto. Foi rodar coleta e login remotos que consumiu recurso
  demais e misturou os bancos — não o fato de existir uma cópia na internet.
  André pediu uma réplica só de leitura, alimentada pelo mesmo backend local,
  e a regra foi reescrita para o que ela de fato protegia: onde o dado é
  ESCRITO, não onde ele pode ser LIDO.

  A réplica existe em `IFOOD_CLOUD_MODE` (`dashboard.py`, `CLOUD_MODE`): lá
  "Coletar" e "Renomear" desaparecem da gaveta — sem Chrome ali, e escrever em
  `data/profiles.json` no disco da nuvem se perderia no próximo deploy — e
  "Recarregar" também some, porque é redundante: publicar já reinicia o app
  inteiro com o arquivo novo. `data/*.db` chega lá do jeito mais simples que
  existia: ele já é rastreado neste mesmo repo, de propósito, e o repo já é
  privado. `publish.sh` é o único caminho de escrita — um script que o André
  roda à mão, pede confirmação, e só toca em `data/*.db` e
  `data/profiles.json`. Nada disso dá à réplica hospedada permissão para
  coletar, logar ou escrever; ela só lê o que a máquina local publicou.
- **Nenhum pedido muda de dono.** Um banco por pessoa, e cada pedido carrega
  quem o fez em qualquer lugar que o mostre. Esta é a propriedade de correção,
  e ela não se negocia.

  **Revisão de 29/08/2026:** até aqui a regra era mais forte — "a tela mostra
  um perfil por vez", e somar os dois tinha sido descartado em 28/08 porque
  exigiria ler os dois bancos no mesmo lugar. O André pediu a soma, e a regra
  foi reescrita para o que ela de fato protege: o risco nunca foi ler junto,
  foi **atribuir errado**. O perfil conjunto lê os dois bancos, e por isso:
  cada pedido leva a coluna **Pessoa**, existe filtro por pessoa dentro da
  visão conjunta, o rótulo da quantia nomeia quem o recorte contém (e não o
  perfil escolhido), e os `id` das duas bases são prefixados na leitura —
  as duas numeram a partir de 1, e sem prefixo o pedido 7 de uma casaria com
  os itens do pedido 7 da outra.

  O conjunto **não é um banco**: não coleta e não se renomeia. Coletar
  continua sendo um ato de uma pessoa.
- **Coleta sempre manual.** Sem agendamento, sem cron, sem coleta automática ao
  abrir. Roda quando alguém manda, com o Chrome à vista.

Limitação conhecida: a API do iFood devolve só uma janela do histórico. Pedidos
mais antigos que ela permanecem no banco como foram gravados e não são
reverificados por coletas novas.

## Brand Commitments

Identidade visual do iFood, por escolha explícita do usuário: logo em
`assets/ifood-logo.png` (wordmark) e `assets/ifood-icon.png` (símbolo em tile,
para favicon), vermelho `#ea1d2c` amostrado do próprio logo.

Capa em `static/capa-avenida.jpg`: um entregador de moto atravessando uma
avenida, visto de trás, com a bolsa térmica nas costas — também por escolha
explícita do usuário, que comparou com uma alternativa noturna e ficou com
esta. É a outra metade da cena de uso: a entrega que acontece enquanto o casal
decide se pede ou cozinha.

Os originais ficam em `assets/` (`capa-avenida-original.jpg`, 2172px, e
`capa-noturna.jpg`, a alternativa descartada); `static/` guarda só a versão
servida, redimensionada para 1600px.

Uso é pessoal e local — a ferramenta consome a conta do próprio usuário e nunca
é publicada. Não é um produto do iFood nem se apresenta como tal.

Idioma: português do Brasil, em toda a interface.

## Evidence on Hand

Dados reais, não amostra: 260 pedidos do André (nov/2025 a ago/2026) e 131 da
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
