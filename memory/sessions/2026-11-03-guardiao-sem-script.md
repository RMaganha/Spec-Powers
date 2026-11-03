# 2026-11-03 (manhã) — guardião sem script (0.51.1)

## Conversamos
O owner: *"ao rodar fui contactado pela minha infra e segurança da informação, esses scripts não são permitidos! … não pode
mais executar esses comandos"*. O guardião da 0.51.0 (script `.ps1` por hook `SessionStart` + tarefa agendada) virou
problema de conformidade no primeiro uso.

## Pivôs
- **Primeiro tirar do ar, depois pensar.** O hook que rodava o `.ps1` a cada conversa saiu do `~/.claude/settings.json` antes
  de qualquer desenho (cópia `settings.json.bak-20261103-085929`).
- **Não era só o sandbox, era política.** A memória do dia 30 dizia "o comando vai pro owner em passo a passo"; agora diz
  "nem pro owner" e o `gatilho_comando` barra `.ps1`, tarefa agendada, COM do agendador e criação de junção.
- **Premissa não-dita de novo (F-003 → F-050):** o que a máquina corporativa permite é pergunta à SI, não suposição.

## Rejeitado
- Atalho na pasta Inicializar como fallback — também é persistência; superado no to-dolist.
- Manter o `.ps1` no kit "sem usar" — molde que a SI não permite não pode existir no kit (teste `test_o_kit_nao_carrega_script_powershell`).

## Fizemos
Branch `fix/guardiao-sem-script`: `.ps1` e seus testes removidos; `hooks/README.md`, check 1 do `doctor` e `LEIA-ME` sem a receita;
memórias da junção, da pendência e do sandbox revisadas; decisão de 2026-11-03; CHANGELOG 0.51.1; F-050;
`tests/test_memoria_sem_script_na_maquina.py` (regex + nenhum `.ps1` no kit + docs sem receita).

## Próximo
Owner escolhe a alternativa pra junção que some: (A) instalar o kit pelo marketplace local, sem junção e sem script — o app
cuida; depois de mudar o kit, `marketplace update`; ou (B) hook Python só de conferência no `settings.json` do usuário
(mesma classe dos hooks Python que o kit já roda). Qualquer uma passa pela SI antes. E apagar a tarefa agendada se chegou
a ser criada (Agendador de Tarefas → Biblioteca → "mss-spec guardiao da juncao" → Excluir), sem comando.
