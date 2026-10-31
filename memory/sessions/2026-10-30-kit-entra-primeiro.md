# 2026-10-30 (noite) — kit entra primeiro (0.50.0)

## Conversamos
O owner mandou olhar a conversa "Validar mensagens WhatsApp em produção" (Whats, 30/10): *"está péssimo
novamente, se perdeu todo, não lê memória, não lê diário, fica chutando nomes de servidores"*, *"não sei mais se
faz sentido usar isso"*. Depois: *"tenho quase certeza de que memória e muitas outras coisas ele não gravou na
pasta do projeto"*, *"estou com vontade de chorar e apagar tudo"*. Entramos pelo `/mss-spec:bug` do próprio kit
(memória do kit antes da hipótese), lemos a transcrição inteira pelo `.jsonl` e cruzamos com o registro local dos
hooks e com o git do Whats.

## Pivôs
- **Da prosa pra cerca.** O `bug.md` (27/10) já dizia que o kit ficava de fora; reincidiu em 30/10 (15:14,
  `superpowers:systematic-debugging` direto). O owner: *"tem que ajustar o hook pra sempre usar o plugin"*. Virou
  `hooks/kit_primeiro.py`: `superpowers:*` negado sem comando do kit na conversa (digitado, invocado ou lido).
- **A rede de segurança nunca funcionou.** Medindo as transcrições pra entender a devolução das 15:50, apareceu
  que TODA devolução do `confere_citacoes.py` desde 25/09 (40+) foi gravada como `hook_non_blocking_error` "Hook
  script appears to be missing": o `setlocale` do Git Bash põe "No such file or directory" no stderr, e exit 2 com
  isso é lido como script ausente. F-034, F-035 e F-047 nunca agiram ao vivo. Explica o "cada vez pior". O Stop
  passou a devolver por JSON com exit 0.
- **"Não gravou" era a data do Explorer.** 649 gravações desde 15/10, todas na pasta do projeto, 10 de 11
  conversas com diário em `memory/sessions/` e commit no dia; o merge do owner às 17:18 reescreveu 31 arquivos e
  91 de 190 memórias mostram no Explorer data diferente do commit. Uma falta real: a conversa da tarde (token +
  n8n) encerrou sem diário → `hooks/diario_junto.py` (memória sem diário não sai) e lembrete ligado por sessão.
- **Diário fora de todo caminho.** O passo 1 de `bug`/`duvida`/`diagnostico` não o listava e o recall o exclui
  (F-030). Entrou a leitura explícita dos últimos 7 dias; o recall segue sem ele.
- **Ambientes num lugar só.** `-dev-br`/`-prod-br`, `BANCO_HML`/`BANCO_PRD`, "owner não acessa o RG de
  produção" estavam em 4 arquivos. O owner: *"deve ter um arquivo independente que guarde ambientes, variáveis e
  valores"*, e depois: *"todos os arquivos nas pastas dos seus projetos, nada em pasta aleatória"*. Virou
  `docs/AMBIENTES.md` por projeto (segredo `*****`), lido pelo recall por seção e pelo passo 1.

## Rejeitado
- Arquivo de ambientes fora dos repositórios (decisão do owner: tudo dentro do repo).
- Recall voltar a casar o diário (F-030: entrada velha vira estado atual) — a leitura é explícita, 7 dias.
- Bloquear no lembrete de captura — só avisa o owner (`systemMessage`); a cerca é do `diario_junto`.
- Uma branch por item — o owner pediu uma branch só, atualizada no fim.

## Fizemos
Branch `feature/kit-entra-primeiro`, 6 commits: `kit_primeiro.py` (+25 testes) · `confere_citacoes.py` por JSON
· `diario_junto.py` + `_transcricao.py` (+29) · `capturar_nudge.py` ligado por sessão (+14) · `templates/AMBIENTES.md`
+ `kickoff`/`upgrade`/`doctor` + `memoria_indice.fontes_ambientes` + passo 1 dos três comandos (+11) · 0.50.0,
CHANGELOG, EVALS F-048, 4 decisões, esta memória e este diário · depois do OK do owner, a 5ª porta
`/mss-spec:tarefa` (`commands/tarefa.md`): o dia a dia, que ele disse que "provavelmente será o mais usado" — na
negativa do hook, na regra 11, na lista de invocáveis e na tabela "por qual porta entrar" do `LEIA-ME`.

## Próximo
Owner: merge da branch na `main` e push; `/mss-spec:upgrade` no Whats (nasce o `docs/AMBIENTES.md`, o owner
preenche os valores — só ele os tem), depois Transportes e Energy; remover `LC_ALL=enu` das variáveis do Windows;
no Whats, capturar a conversa da tarde de 30/10 (`/mss-spec:memory capturar` nela) — o problema do push do n8n em
produção não está escrito em lugar nenhum.

## Depois do merge — o guardião da junção (0.51.0)
O owner perguntou o que é "refazer a junção" e pediu algo automático ("o aplicativo atualiza constantemente"). O guarda não pode ser hook do kit (se a junção some, o kit some): virou `templates/guardiao-da-juncao.ps1`, chamado pelo hook `SessionStart` do `~/.claude/settings.json` do usuário (gravado, com cópia) e por tarefa agendada que só o owner consegue registrar (o sandbox negou `Register-ScheduledTask`, `schtasks` e o COM). **Pivô:** a 1ª rodada de verdade falhou com os 8 testes verdes — `$PSScriptRoot` vazio no default do param; os testes passavam `-Alvo`. Lição: teste que passa o parâmetro não prova o padrão; entrou o teste sem `-Alvo` e o cálculo foi pro corpo. **Próximo:** owner registra a tarefa (comando no `hooks/README.md`) e confere o log; na próxima atualização do app, a linha `evidencia estado=…` do log é a captura que a pendência pedia.
