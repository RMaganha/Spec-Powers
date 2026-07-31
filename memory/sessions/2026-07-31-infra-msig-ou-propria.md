# 2026-07-31 — infra MSIG ou própria: o kit pergunta em vez de assumir (v0.18.0)

## Conversamos
Segundo assunto da mesma janela, aberto por decisão explícita do owner ("podemos fazer aqui") depois
que o ciclo do mapa neural fechou e foi publicado. Nasceu de duas pontas que se encontraram: a
anotação de **28/07** no to-dolist (perguntar na constituição se o projeto segue a arquitetura de
rede MSIG) e o comentário dele ao fechar o mapa — *"tem 2 projetos que não são MSS, então não entra
certs, compose office e algumas partes de arquitetura da MSS"*.

## Pivôs
- **Meu jargão travou a conversa.** Eu vinha chamando isso de *"a chave MSIG × arquitetura própria"*
  e o owner respondeu: *"que abrir chave msig é essa? confuso essas definições suas"*. "Chave" não
  existe no kit — era palavra minha. Só destravou quando troquei a abstração por **tabela do que
  acontece hoje e em que arquivo**. Lição prática: nomear um mecanismo que ainda não existe soa como
  se ele existisse, e o owner passa a caçar algo que não está lá.
- **O escopo veio dele, cravado:** *"a única coisa que se não for MSIG não deve seguir é proxy, CA,
  docker office e getconnection"*. Não ampliei — mas **declarei uma consequência necessária antes de
  implementar**: o `docker-compose.yml` **base** também é MSIG (pendura o serviço na rede externa
  `mitiai_network`), então em infra própria ele sai sem essa rede, senão a entrega fica quebrada (o
  serviço não sobe). Aceito.
- **Onde a resposta mora foi a decisão de design.** Nada de arquivo de configuração novo: uma linha
  no **`CLAUDE.md`** (Contexto), que já está em contexto em toda sessão — coerente com o corte que
  ele mesmo fez na rodada anterior ([[feedback_regra_unica_em_vez_de_config]]).
- **Achado ao escrever (não estava no pedido):** sem freio, a **categoria 1 do `upgrade`**
  reintroduziria CA e compose office a cada rodada, desfazendo o kickoff em silêncio — é a mesma
  categoria que a 0.14.0 já teve que frear pro brownfield. E projeto anterior a esta versão precisa
  receber a linha **perguntando** (`<MSIG | própria — a confirmar>`), nunca com MSIG assumido: seria
  repetir o erro que a feature conserta.
- **Teste é wiring, não unit:** comando-prosa não se testa como código (regra da casa) — 5 casos no
  smoke cobrindo kickoff/molde/ambiente/banco/doctor/upgrade.

## Rejeitado
- **Detectar** a infra sozinho (por nome de projeto/pasta) — adivinhação, justamente o que o kit
  proíbe.
- Transformar o `docs/AMBIENTE.md` em documento da infra própria — fica como referência MSIG, com
  nota no topo de que aquelas seções não se aplicam.
- Mexer em ODBC e Azure — já condicionais a "usa SQL Server"/"é Azure", independentes da rede.
- `/mss-spec:compliance` deixar de cobrar itens MSIG — não veio no escopo; entra se aparecer no uso.

## Fizemos
`templates/CLAUDE.md` (linha `**Infra:**`) · `kickoff` (pergunta na entrevista + o que muda no
scaffolding) · `ambiente` e `banco` (passo 0 lendo a linha) · `doctor` (checks 4/5/6 **pulados**, não
✗) · `upgrade` (freio da categoria 1 + a linha nova entra perguntando). Spec nova
`docs/superpowers/specs/2026-07-31-infra-msig-ou-propria-design.md` + linha no INDEX; 5 testes de
wiring → suíte **116 verde** (era 111); bump **0.18.0**. Item saiu do to-dolist.

## Próximo
Push da 0.18.0 e, nos **2 projetos que não são MSS**, rodar o `/mss-spec:upgrade` pra a linha chegar
lá — ele pergunta; respondendo "própria", o `doctor` para de cobrar proxy/CA/rede e o upgrade para de
reintroduzir CA e compose office.
