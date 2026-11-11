# 2026-11-11 — memória em tabela, parte 1: a tabela (0.55.0)

Branch `feature/memoria-em-tabela` (da `main` em `4bd3baf`). Spec: `docs/specs/memoria-em-tabela.md`. Plano:
`docs/superpowers/plans/2026-11-11-memoria-em-tabela.md`. Mesma conversa da análise de 2026-11-10 (o owner
preferiu seguir nela: a janela nova "bloqueou um monte de coisa").

## Conversamos
- O owner escolheu começar pela tabela ("é o mais óbvio") e pediu pra tocar nesta janela.
- Perguntou se o desenho proposto era "realmente o melhor/ideal": separei o que está medido (uma tabela, tudo
  dentro, por seção) das escolhas do assistente que não passaram por teste, e medi na hora a de entrar só
  `.md`/`.html` (cobre praticamente tudo nos 4 projetos).
- Onde mora a tabela: o owner vetou o `~/.claude` (*"qualquer alteração perde"*) e sugeriu a pasta do kit ou um
  lugar definido e obrigatório. Ficou `~/mss-spec/memoria.sqlite3`, com aviso quando não acha.

## Pivôs
- **`~/.claude/mss-spec/` (precedente do registro dos hooks) → `~/mss-spec/`**, por decisão do owner.
- **Pasta do kit descartada**: o kit é publicado e a tabela guarda o conteúdo de todos os projetos; a junção
  vai virar instalação normal (a "pasta do kit" passa a ser cópia dentro do `.claude`); um projeto não grava em
  outro.
- **11 s → 1,5 s no Whats**: o tempo estava em abrir cada arquivo várias vezes; cada arquivo passou a ser lido
  uma vez (sem mudar comportamento, sob os mesmos testes).
- **No fim, o owner recusou o comando novo como coisa a lembrar**: *"vai fazer se perder quando eu perguntar"*.
  Quer gravar no arquivo e a tabela se atualizar sozinha; buscar na tabela e, se precisar, nos arquivos. Vira o
  desenho da parte 2 (é o padrão do caso F-014: mecanismo que depende de o owner lembrar de chamar).

## Rejeitado
- Tabela dentro do `.claude` e dentro da pasta do kit.
- Tabela de controle separada (a assinatura do arquivo fica na própria linha: é uma tabela só).
- Rodar o git nos outros projetos a partir desta janela (regra 8): a conferência real usou `--sem-git`.

## Fizemos
- `templates/memoria_tabela.py` (`montar` · `status` · `onde`) + `tests/test_memoria_tabela.py` (39) ·
  `commands/memory.md` (modo `tabela`) · procedimento `project_remontar_a_tabela_de_memoria` · spec, plano,
  LEIA-ME, CHANGELOG, PLANO-TESTE, decisão de 2026-11-11, 0.55.0 nos dois manifestos.
- Conferência real: 3.000 linhas nos 4 projetos (tabela temporária, só leitura); tabela do kit montada com os
  padrões (169 arquivos, 791 linhas). Suíte: 1289 verdes.
- Três testes (tabela presa, arquivo grande, pasta com acento) passaram de primeira: cobrem tratamento de erro
  escrito antes do teste.

## Próximo
- Merge na `main` (aprovação do owner); `git push` é dele.
- Parte 2: a busca usa a tabela e a tabela se atualiza sozinha (sem comando pra lembrar); as outras máquinas e
  projetos entram quando cada um abrir.
- `/mss-spec:memory capturar` das falhas da sessão de 2026-11-10 (seção 6 do dossiê) ainda não foi feito.
