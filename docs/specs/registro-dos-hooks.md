# Registro dos hooks — o que as cercas e as redes fizeram, em número

## Estado atual
**`hooks/_registro.py`** (módulo, não é hook): os seis hooks o chamam **só quando agem** e ele anexa
uma linha JSON em `~/.claude/mss-spec/registro-hooks.jsonl` — um arquivo por máquina, fora de
qualquer repo, com `quando`, `hook`, `decisao` (`negou` · `bloqueou` · `avisou` · `injetou` ·
`lembrou`), `detalhe` (rótulo do próprio hook, ≤ 240 caracteres), `projeto` (só o nome da pasta) e
`sessao` (8 caracteres do id). Detalhe por hook: `git_publicacao` → o verbo (`git push`…), `pytest em
pipe antes do git commit` ou `defeito da cerca` · `projeto_ativo` → o tool, **não** o caminho ·
`um_item_por_janela` → `abertas=N` · `recall_memoria` → os ponteiros `arquivo:linha` ·
`alerta_contexto` → `faixa pct janela modelo` · `capturar_nudge` → nada.

Leitura: `python hooks/_registro.py resumo [--dias N]` (contagem por hook × decisão + os 3 detalhes
mais comuns). O painel `anatomia` ainda **não** lê o registro.

Garantias, todas travadas em `tests/test_hook_registro.py`: **nunca** grava prompt nem linha de
comando (segredo falso no comando, no prompt e no caminho); registro que não grava **não muda
decisão nenhuma** (saída byte a byte igual nos seis, inclusive a cerca de publicação, que segue
falhando FECHADA); passar calado não grava; > 1 MB → rodízio pra `.1`; escape do owner
`MSS_REGISTRO_OFF=1`; `MSS_REGISTRO_ARQUIVO` troca o caminho (o `tests/conftest.py` desvia a suíte
inteira, pra nunca sujar o registro real). Custo: < 1 ms por linha, contra ~190–260 ms que cada hook
já gasta na partida do Python.

Fora de escopo: mostrar no `anatomia` (depois de haver dado acumulado) · telemetria enviada pra
fora da máquina · registrar o que passou calado · tabela central de políticas dos hooks.

## Histórico
- 2026-09-23 — criado: nasceu da avaliação de duas análises externas do kit (ChatGPT e Gemini). Das
  quatro melhorias levantadas, o registro foi a que se sustentou com caso real: os hooks decidem
  calados e não havia como dizer se o `git_publicacao` já barrou algo desde 2026-09-14, nem se o
  recall acerta (nesta mesma sessão ele injetou uma decisão pouco relevante pra um prompt de
  avaliação). Decisões do owner: o arquivo fica em `~/.claude/mss-spec/` (não no TEMP, que o Windows
  limpa; não em cada projeto, que exigiria `.gitignore` distribuído pelo `upgrade`) e entra na mesma
  branch da cerca do pipe. Dogfood: o canário `git push --dry-run` foi negado ao vivo e gerou a linha
  `git_publicacao · negou · git push · Spec-Powers`.
