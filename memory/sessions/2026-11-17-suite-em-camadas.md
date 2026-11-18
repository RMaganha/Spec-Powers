# 2026-11-17 — suíte em camadas: a regra do hook testada em memória, sem pasta (34 de 34; rodada única verde)

## Conversamos
O owner abriu `/mss-spec:tarefa` com o texto pronto da conversa anterior (`2026-11-17-suite-lenta.md`): reescrever
a suíte do kit em camadas, na ordem das pastas que cada arquivo cria por rodada. Já decidido no pedido: teste não
cria pasta nem arquivo; disco só num teste por hook e processo python só num; o hook passa a receber o estado como
dado sem mudar o comportamento; na máquina só `templates/testes_do_que_mudou.py --rodar`; um commit por arquivo.

## Pivôs
- O nome da função sem disco começou como `decidir` no `passagem_de_conversa`; virou `regra` em todos porque
  `decidir` já era a casca pública em 7 hooks (commit separado, `ce25bd3`).
- No `confere_citacoes` a regra recebe o disco como objeto (`DiscoReal`, 6 métodos); em teste, um dicionário de
  arquivos com o pedaço do kit que os textos citam. O kit de verdade fica só no teste de disco.
- Uma rodada levou 13h03 de relógio: a máquina suspendeu no meio (a data virou). Rodada longa vai em segundo plano.
- No `rodizio_partida` o dry-run do `enxugar` trocou a pasta temporária por um `Rascunho` em memória: grava só
  nele e lê do disco de baixo o que não gravou (OK do owner, 2026-11-18).

## Rejeitado
- Ler o kit de verdade nos testes em memória do `confere_citacoes` (seria disco fora do teste de disco).
- Ler `docs/specs` e o INDEX a cada pedido para passar como dado: a regra recebe funções que leem só quando
  precisa — hoje o hook só lê no 1º pedido ou só quando o comando casa.

## Fizemos
- Decisão em `docs/decisoes.md` (2026-11-17, hook = `regra` sem disco + casca), com o OK do owner.
- Reescritos, um commit cada: `passagem_de_conversa` (`1c19046`, `ce25bd3`), `um_item_por_janela` (`fb22400`),
  `confere_citacoes` (`1c78682`), `banco_producao` (`ac74dcc`). Em cada um, os testes antigos passaram com o hook
  novo antes da troca do teste.
- 2026-11-18: mais 14 — `regra_antes_de_gravar`, `pasta_e_branch`, `conversa_nova_acha_sozinha`, `kit_primeiro`,
  `teto_ao_gravar`, `regras_do_kit`, `orcamento_partida`, `memoria_de_acao`, `comando_inteiro`, `diario_junto`,
  `decisao_junto`, `registro`, `ancora_projeto_ativo`, `alerta_contexto` (18 de 34). Contagem do
  `test_memoria_gatilho_de_acao.py` corrigida pra 28 (a captura da suite lenta criou a 28ª memória com gatilho).
- Pivô do owner (2026-11-18): rodar a suíte a cada arquivo era o gargalo (15 a 25 min por rodada, arrastando
  arquivos antigos) — agora um commit por arquivo, sem rodada no meio, e UMA rodada no fim. Isso também cumpre
  `memory/feedback_suite_inteira_so_no_ci.md`: teste não reescrito não roda na máquina.
- Escolhas aprovadas pelo owner: no `teto_ao_gravar` o motor `rodizio_partida` entra falso em memória; módulo
  (`_memoria_de_acao`, `_comando_inteiro`) sem teste de processo; dentro de outro hook, as leituras do módulo são
  trocadas por `monkeypatch`; no `registro` a matriz de 12 hooks × processos saiu.
- Última rodada: `882 passed` depois do `conversa_nova_acha_sozinha`. Do `kit_primeiro` em diante, sem rodada.
- 2026-11-18 (3ª conversa): mais 10, um commit cada, sem rodada — grupo 1: `memoria_tabela_em_dia` (`57c388e`),
  `capturar_nudge` (`187702d`), `sem_worktree` (`67a3a8a`), `recall_memoria` (`35b2d89`, nome do F-030 de volta em
  `67d9717`), `memoria_da_proposta` (`ef7bd15`); grupo 2: `inventario_banco` (`81954e6`, processo em `0c55fe3`),
  `migrar_claude_md` (`ff871a5`), `mapa_neural` (`aa96347`), `memoria_tabela` (`ffb055b`), `memoria_tabela_busca`
  (`48fbc4b`), `conversa_texto` (`1650236`). 28 de 34.
- Decisão nova com o OK do owner (`docs/decisoes.md`, 2026-11-18): script do kit se divide como hook. O owner
  escolheu, para os extratores (`mapa_neural`, `bpmn`, `memoria_indice`, a leitura do projeto no `memoria_tabela`),
  disco por objeto à risca — e mandou mostrar com arquivo e linha, antes de gravar, todo ponto que não dê pra passar
  por objeto sem mudar comportamento. Até aqui nenhum: o `mapa_neural._py_files` reconhece a raiz pela 1ª volta da
  varredura (o `os.walk` começa nela) em vez de comparar `resolve()`; a conversa segue lida linha a linha.
- Padrão dos scripts: `DiscoReal` (ou `BancoReal` pra tabela SQLite) com métodos estáticos; as funções públicas
  ganham `disco=DiscoReal` no fim (assinatura de antes vale); no teste, um `Disco` sobre dicionário. Banco de teste:
  SQLite `:memory:` com conexão que não fecha. Testes que o `docs/EVALS.md` cita: nome igual E o mesmo sentido (o
  `test_camada_no_gitignore_fica_fora` do F-005 virou o teste de disco do `mapa_neural`, com git de verdade).
- Rejeitado pelo owner: pasta montada uma vez com o script intocado nos extratores (a opção leve).

- 2026-11-18 (4ª conversa): os 5 últimos, um commit cada, sem rodada: `sono_da_memoria` (`49a9826`, disco por
  objeto no `memoria_indice.py`), `memoria_indice` (`1e33e9d`), `rodizio_partida` (`dcf7579`), `bpmn` (`cda2c9c`,
  24 processos viraram 1), `memoria_gatilho_de_acao` (`030fb61`). A conta "faltam 6" estava errada: a 3ª
  conversa reescreveu 11, não 10.
- Rodada única (`python templates/testes_do_que_mudou.py --rodar`): `5 failed, 1479 passed in 654.80s`.
  Conserto em `23a96e1`; as 5 de novo: `14 passed`. 4 eram o ajudante com `evento=None` significando "use o
  padrão", que engolia o caso `None` da entrada malformada — agora a sentinela `PADRAO = object()`
  (`memory/project_ajudante_de_teste_sentinela_em_vez_de_none.md`); 1 era o teste do F-047, que perdeu o "ou o
  título" ao sair do `test_hook_memoria_da_proposta.py` (`ef7bd15`) — caso F-074 no `docs/EVALS.md`.
- O item do `testes_do_que_mudou.py` (não escolhe teste que carrega módulo por nome entre aspas nem teste que
  varre `memory/` com glob) foi para o `to-dolist.md` como `#fora-de-escopo` (`f29a4ea`).

## Próximo
O owner envia a branch (`git push -u origin refactor/suite-em-camadas`) → a suíte inteira roda no CI → merge
`--no-ff` na `main`, com a aprovação dele.
