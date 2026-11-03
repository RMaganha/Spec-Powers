# Teto fala só com o assistente · medida sem comentário · upgrade sem refazer infra — plano

> Plano datado/efêmero (nível médio: execução inline, TDD, verificação). A spec viva é `docs/specs/partida-no-orcamento.md`
> (itens 9 e 10) e `docs/specs/upgrade.md`. Branch `feature/teto-avisa-uma-vez-e-upgrade-sem-refazer-infra`.

**Objetivo:** o kit para de falar com o owner sobre o teto do MAPA/INDEX (fala só com o assistente, uma vez por
sessão), o teto desses dois conta só conteúdo, e o `/mss-spec:upgrade` nunca reescreve os 4 arquivos do Docker que
já existem.

**Prova fora da suíte:** os scripts do scratchpad (`sim/simular.py`, `sim/simular_antigo.py`, `sim/simular_vivo.py`)
rodados com rótulo `depois` nas mesmas cópias do Whats e do MSS-SSC — a tabela antes/depois vai na resposta ao owner.

## Tarefa 1 — `hooks/teto_ao_gravar.py`: só assistente, uma vez por sessão
- Testes (`tests/test_hook_teto_ao_gravar.py`): `test_dentro_do_teto_fechada_sai_e_avisa_sem_falar_em_teto` ganha
  `"avise o owner" not in txt.lower()` e `"systemMessage" not in saida`; `test_mapa_com_bloco_atual_gigante_pede_o_resumo`
  idem; novos `test_bloco_vivo_pede_o_resumo_uma_vez_por_sessao` (2º Edit na sessão `s1` → `None`; sessão `s2` → pede de novo)
  e `test_claude_md_acima_avisa_o_owner_uma_vez_por_sessao` (1º Edit → "Avise o owner" + `systemMessage`; 2º → `None`).
- Código: `_ja_avisou(sessao, rel)` / `_marcar_avisado(sessao, rel)` na chave `_avisados` do estado por sessão
  (`mss_teto_<sessão>.json`); `_agir(evento, raiz, alvos, sessao)`: MAPA/INDEX → passos + problemas sempre, avisos
  ("ainda acima … conteúdo vivo") uma vez por sessão por arquivo, texto termina em "Não é assunto pro owner: não o
  avise", sem `systemMessage`; `CLAUDE.md` > 10 KB → uma vez por sessão, com "Avise o owner em 1 linha" e `systemMessage`.
- Rodar: `python -m pytest tests/test_hook_teto_ao_gravar.py -q`.

## Tarefa 2 — `hooks/orcamento_partida.py`: só assistente pra MAPA/INDEX; medida sem comentário
- Testes (`tests/test_hook_orcamento_partida.py`): `test_aviso_manda_nao_ler_inteiro_e_nao_avisa_o_owner` (mapa=20000 →
  "inteiro" sim; "avise o owner" não; `/mss-spec:doctor` não; sem `systemMessage`); `test_owner_e_doctor_so_quando_estoura_memory`;
  `test_system_message_so_com_claude_ou_memory`; `test_comentario_nao_conta_no_mapa_e_no_index` (5.000 B de texto + 1.805 B
  de `<!-- -->` → `None`; 6.100 B de texto → avisa); `test_medida_igual_no_hook_e_no_rodizio`.
- Código: `_bytes_de_conteudo(texto)` (cópia da do rodízio); `estouros()` usa a medida pra MAPA/INDEX; `conserto()` só
  pra `CLAUDE.md` e `MEMORY.md`; `texto_do_aviso()` sem "avise o owner" quando só MAPA/INDEX; `systemMessage` só com
  `CLAUDE.md`/`MEMORY.md`. Texto ≤ 1.000 B com os 4 estourados (teste existente).
- Rodar: `python -m pytest tests/test_hook_orcamento_partida.py -q`.

## Tarefa 3 — `templates/rodizio_partida.py` + `tests/test_orcamento_contexto.py` + `templates/anatomia.py`
- Testes: `tests/test_rodizio_partida.py::test_comentario_nao_conta_no_teto` (MAPA 5.000 B de texto + 1.805 B de comentário →
  `enxugar` dry-run sem aviso, `bytes_antes` = conteúdo); `tests/test_orcamento_contexto.py` mede MAPA/INDEX com `_conteudo(p)`.
- Código: `bytes_de_conteudo(texto)` público; `_bytes` passa a ser ela; `rel.bytes_antes/depois` em conteúdo; avisos dizem
  "de conteúdo"; `anatomia.py` mede MAPA/INDEX do mesmo jeito.
- Rodar: `python -m pytest tests/test_rodizio_partida.py tests/test_orcamento_contexto.py tests/test_anatomia.py -q`.

## Tarefa 4 — `commands/upgrade.md`: infra que existe nunca é reescrita
- Teste (`tests/test_smoke_kit.py::test_upgrade_nao_reescreve_infra_que_existe`): o texto diz que `docker-compose.yml`,
  `docker-compose.office.yml`, `Dockerfile` e `.dockerignore` que existem **nunca** são reescritos (diff + "revise à mão");
  `docs/AMBIENTE.md` que existe não ganha seção; `docs/AMBIENTES.md` nasce "sem questionário". Os testes de infra própria
  e brownfield seguem verdes.
- Código: linha dos arquivos do Docker na categoria 1 + parágrafo "Freio do que já roda" + caso do `AMBIENTE.md` na
  categoria 2 + frase do `AMBIENTES.md`.

## Tarefa 5 — docs, memória, versão
- `docs/specs/partida-no-orcamento.md` (itens 9 e 10, Histórico) · `docs/specs/upgrade.md` (novo) · `docs/superpowers/INDEX.md` ·
  `docs/superpowers/MAPA.md` · `hooks/README.md` (linhas dos dois hooks) · `commands/doctor.md` (check 9: "de conteúdo") ·
  `templates/MAPA.md:1` e `templates/INDEX.md:1` · `memory/project_upgrade_categoria1_sobrescreve.md` (Docker sai da lista
  "só molde") · `.claude-plugin/plugin.json` + `marketplace.json` = 0.52.0 · `CHANGELOG.md`.

## Tarefa 6 — suíte inteira e prova nas cópias
- `python -m pytest tests/ -q` (saída colada) · scripts do scratchpad com rótulo `depois` (tabela antes/depois colada).
