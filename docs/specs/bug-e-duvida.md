# Bug e dúvida pelo kit — porta de entrada que chama o superpowers por baixo

## Estado atual
**0.50.0 (F-048):** a entrada pelo kit deixou de ser prosa — o hook `hooks/kit_primeiro.py` **nega**
qualquer skill `superpowers:*` enquanto nenhum comando do kit tiver entrado na conversa (digitado, invocado
por `Skill` ou lido em `commands/<x>.md`), apontando a porta certa. E o passo 1 dos três comandos passou a
ler **`memory/DIARIO.md`** (últimos 7 dias) e, quando o sintoma cita um ambiente, a seção dele em
**`docs/AMBIENTES.md`** (nomes, valores, quem acessa o quê). Motivo: na conversa do Whats de 2026-10-30 o
bug entrou direto no `systematic-debugging`, o diário nunca foi aberto e o nome do servidor foi chutado.

**0.50.0 — a 5ª porta, `/mss-spec:tarefa`** (`commands/tarefa.md`, sem a trava): o dia a dia — ajuste pequeno,
operação, consulta, documentação, comando git — que não é bug, dúvida, feature nova nem análise, e que sem porta
entrava direto pelo superpowers ou por nada. Trilho curto: é tarefa mesmo? → lê só o que a tarefa toca (MAPA,
memória, spec, `AMBIENTES.md`, diário 7 dias) → plano em até 5 linhas e OK (só leitura não espera) → faz no nível
mínimo/médio → prova real antes de "pronto" → fecho em 1 linha, to-dolist e captura só oferecidos. O hook
`kit_primeiro.py` a aponta na negativa e a aceita como entrada; o `LEIA-ME` ganhou a tabela "por qual porta entrar".

Bug e dúvida entram **pelo kit**, não direto pelo superpowers. Três comandos **sem a trava**
`disable-model-invocation` — o assistente os chama sozinho quando o owner descreve um erro ou faz uma
pergunta, e o owner também pode digitá-los:
- **`/mss-spec:bug`** (`commands/bug.md`): mostra em até 5 linhas, com `arquivo:linha`, o que a
  memória já diz **antes da 1ª hipótese** → `superpowers:systematic-debugging` → 2 rodadas sem causa
  (ou o owner diz que está perdido) → `mss-spec:diagnostico` → causa + OK → branch `fix/…`, teste que
  reproduz, suíte → virou feature? `/mss-spec:nova-feature`. Fecho só oferece captura/caso, não roda.
- **`/mss-spec:duvida`** (`commands/duvida.md`): lê o destilado, responde com fonte ou "não sei", não
  edita arquivo, encaminha pro `bug`/`nova-feature`/`to-dolist` em 1 linha.
- **`/mss-spec:diagnostico`**: o mesmo trilho de antes, agora destravado e chamado pelo `bug`.

Nas regras do kit (injetadas em toda janela pelo `hooks/regras_do_kit.py`): a **regra 11** aponta o
`/mss-spec:bug` e o `/mss-spec:duvida` (antes mandava direto à `systematic-debugging`); regra nova no
modo de trabalho — **owner contestou algo que a memória diz → mostre a memória antes de mudar código ou
desenho**. Chega aos projetos sem `upgrade` (vem do plugin).

Fora de escopo: hook que detecta bug sozinho · destravar outros comandos · mudar o superpowers. Prova
que falta (do owner): numa janela nova do Whats, descrever um erro sem digitar comando e o assistente
entrar pelo `mss-spec:bug`.

## Histórico
- 2026-10-27 — criado: nasce da análise das 4 últimas conversas do Whats. Os 3 incidentes foram direto
  à `systematic-debugging` (a regra 11 mandava) e o `/mss-spec:diagnostico` (travado) nunca entrou, nem
  com o owner dizendo "novamente perdido"; no `nova-feature` de 26/10 o assistente leu
  `memory/codigo-do-portal-e-login-nao-cod-corr.md`, desenhou certo e abandonou a memória quando o owner
  contestou — retrabalho de 4 mensagens. A memória do repo foi lida nas 4 (106 leituras, 0 da pasta
  nativa): o furo era a porta de entrada, não a memória.
