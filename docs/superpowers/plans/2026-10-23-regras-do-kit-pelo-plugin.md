# Regras do kit pelo plugin — Plano de construção

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** as regras do kit passam a vir do plugin a cada janela; o `CLAUDE.md` do projeto fica só com o que é do projeto (fatos sempre carregados); regra por tipo de arquivo é lida antes de criar arquivo; projetos existentes migram por um script que confere tudo antes de gravar.

**Architecture:** dois blocos de texto em `templates/regras-do-kit/` entregues por um hook `SessionStart` (uma entrada por bloco, por causa do limite de 10.000 caracteres por string); um hook `PreToolUse` que nega uma vez por sessão a gravação de arquivo que casa com `.claude/rules/*.md` não lido; um script determinístico `templates/migrar_claude_md.py` (dry-run por padrão) chamado pelo `/mss-spec:upgrade`.

**Tech Stack:** Python 3 só stdlib (hooks e script, como o resto do kit), pytest, comandos em markdown.

**Spec:** `docs/specs/regras-do-kit-pelo-plugin.md` (commit `0b8f9e7`).

## Global Constraints

- Versão **0.42.0** em `.claude-plugin/plugin.json` **e** `.claude-plugin/marketplace.json`.
- Marca do projeto do kit: a linha exata `<!-- mss-spec:regras-do-kit -->`.
- Cada bloco do kit **≤ 9.000 caracteres** (`len(texto)`, não bytes), travado por teste.
- Parte do projeto (`templates/CLAUDE.md` e `CLAUDE.md` migrado): teto **10.000 B**, como **aviso** — nunca reprova a migração.
- Texto das regras do kit muda de **lugar**, nunca de redação (F-029). As `FRASES_CHAVE_CLAUDE_MD` continuam todas presentes.
- Hooks: só stdlib; `exit 0` sempre; registro via `hooks/_registro.py`; documentados em `hooks/README.md` com o escape.
- `regras_do_kit.py` falha **visível** (`systemMessage` de 1 linha); `regra_antes_de_gravar.py` falha **aberta** (silêncio).
- Escapes: `MSS_REGRAS_KIT_OFF=1`, `MSS_REGRA_OFF=1`.
- O script de migração **nunca** roda git e **nunca** apaga linha sem destino conferido; na dúvida, a linha fica no `CLAUDE.md`.
- `## Contexto` migrado: nenhuma linha com ponteiro `→ … .claude/rules/`.
- Testes: `python -m pytest -q`; nunca encadear pytest com `git commit` no mesmo comando (F-025). Stage nominal.
- Projeto de outra pasta (o Whats) é **só leitura** nesta janela: só dry-run, nunca `--aplicar`.

## Review Focus

1. **`CLAUDE.md` com CRLF e BOM** (Windows): o script e os hooks devem ler e casar a marca e os rótulos igual; o arquivo gravado mantém o fim de linha original. → teste em Task 6.
2. **Projeto sem `.claude/rules/`** ou com `CLAUDE.md` que nunca foi do kit: a migração não inventa seção nem tira linha; só põe a marca e reorganiza o que reconhece. → teste em Task 6.
3. **Ponteiro de `## Contexto` cujo rótulo não existe no arquivo de regra** (renomeado à mão): reprova com a linha nomeada, não grava. → teste em Task 5.
4. **Caminho do `Write` em Windows** (`C:\…\sql\x.sql`, barra invertida, maiúscula diferente): casa com `sql/**` igual. → teste em Task 3.
5. **Rodar a migração duas vezes**: a 2ª vez não muda nada (idempotente) e diz "já migrado". → teste em Task 6.

---

### Task 1: Blocos do kit saem do molde; molde vira só do projeto

**Files:**
- Create: `templates/regras-do-kit/1-modo-de-trabalho.md`, `templates/regras-do-kit/2-regras-criticas.md`
- Create: `tests/_texto_kit.py`
- Modify: `templates/CLAUDE.md` (reescrito), `templates/anatomia.py:26,161-193`
- Modify: `tests/test_orcamento_contexto.py`, `tests/test_smoke_kit.py` (17 leituras), `tests/test_hook_alerta_contexto.py:247`, `tests/test_hook_git_publicacao.py:341`, `tests/test_hook_um_item_por_janela.py:590`

**Interfaces:**
- Produces: `templates/regras-do-kit/1-modo-de-trabalho.md` e `2-regras-criticas.md`; em `tests/_texto_kit.py`: `texto_do_kit() -> str` (molde + bloco 1 + bloco 2 concatenados, `\n` entre eles) e `BLOCOS: tuple[Path, Path]`.

- [ ] **Step 1: Testes que falham** — em `tests/test_orcamento_contexto.py`:
  - `test_blocos_do_kit_cabem_no_limite_do_hook`: para cada arquivo de `BLOCOS`, `len(texto) <= 9000`.
  - `test_frases_chave_estao_nos_blocos`: toda frase de `FRASES_CHAVE_CLAUDE_MD` aparece em bloco 1 ou bloco 2 (e **não** em `templates/CLAUDE.md`).
  - `test_regras_criticas_numeradas_no_bloco_2`: em `2-regras-criticas.md`, números `1..11` em ordem.
  - `test_molde_do_projeto_tem_marca_e_secoes`: `templates/CLAUDE.md` contém a marca e, nesta ordem, `## Regras obrigatórias do projeto`, `## Contexto`, `## Mapa de arquivos`, `## Índice de regras por tipo de arquivo`; contém `**Infra:**`, `**Stack/runtime:**`, `**Como roda:**`, `**Ambientes:**`, `**Banco:**`, `**Versionamento:**`.
  - `test_cada_bloco_abre_com_desempate`: a 1ª linha não vazia de cada bloco contém `vem do plugin mss-spec` e `regra do CLAUDE.md do projeto vence`.
  - Troque `TETO_CLAUDE_MD = 10000` pelo comentário novo (parte do projeto, aviso) e mantenha os testes de teto/linha gigante sobre o molde.
- [ ] **Step 2:** `python -m pytest tests/test_orcamento_contexto.py -q` → FAIL (blocos não existem).
- [ ] **Step 3: Mover o texto.** Bloco 1 = `templates/CLAUDE.md:6-32` verbatim (seções "Modo de trabalho" e "Contexto de janela"); bloco 2 = `templates/CLAUDE.md:47-58` verbatim (regras 1–11). Cada bloco abre com uma linha: `<!-- Regras do kit — vem do plugin mss-spec em toda janela. Quando uma regra do CLAUDE.md do projeto conflitar com esta, a regra do CLAUDE.md do projeto vence. -->`. O molde novo, na ordem da spec ("Camada 2"): comentário de 2-3 linhas no topo, marca, `# <Projeto> — <objetivo>`, `## Regras obrigatórias do projeto` (com `1. <regra só deste projeto…>`), `## Contexto` (um rótulo por linha, por extenso, com `<…>`; a linha `**Infra:**` atual mantida verbatim), `## Mapa de arquivos` (linhas 42-45 atuais), `## Índice de regras por tipo de arquivo` (`- <arquivo> — <assunto> — carrega ao tocar <padrões>`).
- [ ] **Step 4: Testes de fiação** — crie `tests/_texto_kit.py` e troque, nos 5 arquivos de teste listados, `(REPO / "templates" / "CLAUDE.md").read_text(...)` por `texto_do_kit()` **só** onde a asserção procura texto de regra do kit (as do Contexto/Infra continuam no molde). Em `templates/anatomia.py`, a peça "Molde do CLAUDE.md" passa a listar `templates/regras-do-kit/1-modo-de-trabalho.md` e `2-regras-criticas.md` e a dizer "regras do kit entram pelo hook `regras_do_kit.py`".
- [ ] **Step 5:** `python -m pytest -q` → **792+ passed, 0 failed**.
- [ ] **Step 6: Commit** — `git add` dos arquivos listados; `git commit -m "refactor(regras-do-kit): regras do kit em dois blocos; molde so do projeto"`.

### Task 2: Hook `regras_do_kit.py` entrega os blocos

**Files:**
- Create: `hooks/regras_do_kit.py`, `tests/test_hook_regras_do_kit.py`
- Modify: `hooks/hooks.json` (SessionStart), `hooks/README.md`

**Interfaces:**
- Consumes: os dois arquivos de `templates/regras-do-kit/` (Task 1).
- Produces: `MARCA = "<!-- mss-spec:regras-do-kit -->"`, `BLOCOS = {1: "1-modo-de-trabalho.md", 2: "2-regras-criticas.md"}`, `LIMITE = 9000`, `tem_marca(raiz: str) -> bool`, `responder(evento: dict, ambiente=None, bloco: int = 1) -> dict | None`. CLI: `python hooks/regras_do_kit.py --bloco N`.

- [ ] **Step 1: Testes que falham** (padrão de `tests/test_hook_orcamento_partida.py`):
  - `test_projeto_com_marca_recebe_bloco_1` / `_bloco_2`: `additionalContext` == texto do arquivo; `hookEventName == "SessionStart"`.
  - `test_projeto_sem_marca_fica_calado`: `None`.
  - `test_marca_com_crlf_e_bom_vale`: `CLAUDE.md` gravado com `\ufeff` e `\r\n` → recebe o bloco.
  - `test_prefere_claude_project_dir_ao_cwd`, `test_escape_MSS_REGRAS_KIT_OFF`.
  - `test_bloco_ilegivel_avisa_visivel`: com `BLOCOS` apontando arquivo inexistente → saída tem `systemMessage` contendo `regras do kit não carregaram` e `/mss-spec:doctor`, sem `additionalContext`.
  - `test_bloco_acima_do_limite_avisa_visivel`: texto > 9000 → mesmo `systemMessage`, não injeta truncado.
  - `test_hooks_json_tem_duas_entradas_no_session_start`: comandos com `regras_do_kit.py" --bloco 1` e `--bloco 2`.
  - `test_processo_sai_zero_com_entrada_malformada`.
- [ ] **Step 2:** `python -m pytest tests/test_hook_regras_do_kit.py -q` → FAIL.
- [ ] **Step 3: Implementar** `hooks/regras_do_kit.py` no molde de `hooks/orcamento_partida.py` (registro, escape, `CLAUDE_PROJECT_DIR` › `cwd`). Marca: procurar a linha exata depois de tirar BOM e `\r`. Qualquer exceção **depois** de confirmar a marca → `{"systemMessage": "[mss-spec] regras do kit não carregaram — rode /mss-spec:doctor"}`; antes da marca → `None`. Registro `entregou`/`falhou`. Duas entradas em `hooks/hooks.json` → `SessionStart`, sem `matcher` (vale pra todos). README: o que faz, a marca, o escape, por que falha visível.
- [ ] **Step 4:** `python -m pytest -q` → tudo verde.
- [ ] **Step 5: Commit** — `feat(regras-do-kit): hook entrega as regras do kit em toda janela`.

### Task 3: Hook `regra_antes_de_gravar.py`

**Files:**
- Create: `hooks/regra_antes_de_gravar.py`, `tests/test_hook_regra_antes_de_gravar.py`
- Modify: `hooks/hooks.json` (PreToolUse `Write|Edit|MultiEdit`), `hooks/README.md`

**Interfaces:**
- Produces: `casa_glob(rel: str, padrao: str) -> bool`; `regras_do_projeto(raiz: str) -> list[tuple[str, list[str], str]]` (nome do arquivo, padrões do `paths:`, texto); `responder(evento: dict, ambiente=None) -> dict | None`. Estado em `tempfile.gettempdir()/mss_regra_antes_<sessao>.json` (lista de regras já mostradas), como `hooks/_memoria_de_acao.py:64-81`.

- [ ] **Step 1: Testes que falham**:
  - `test_casa_glob_padroes_do_whats` (parametrizado): `("sql/setup/14a.sql", "**/*.sql") → True`, `("x.sql", "**/*.sql") → True`, `("sql/carga/README.md", "sql/**") → True`, `("persistencia/a.py", "persistencia/**") → True`, `("tests/test_a.py", "tests/**") → True`, `("web/chat.html", "web/**") → True`, `("docker-compose.office.yml", "docker-compose*.yml") → True`, `("Dockerfile", "Dockerfile") → True`, `("app/Dockerfile", "Dockerfile") → False`, `("services/a.py", "apis/**") → False`.
  - `test_write_de_sql_novo_nega_com_o_texto_da_regra`: `.claude/rules/banco.md` com `paths: ["**/*.sql"]`; evento `Write` em `<raiz>\sql\novo.sql` (barra invertida) → `permissionDecision == "deny"`, motivo contém o texto de `banco.md` e `repita a gravação`.
  - `test_segunda_gravacao_na_mesma_sessao_passa`: mesmo evento 2× → 2ª `None`.
  - `test_outra_sessao_nega_de_novo`.
  - `test_arquivo_que_nao_casa_passa`, `test_regra_sem_paths_ignorada`, `test_projeto_sem_rules_passa`, `test_arquivo_fora_da_raiz_passa`.
  - `test_duas_regras_casam_nega_uma_vez_com_as_duas` (ex.: `**/*.py` de `logging.md` e `estrutura-em-camadas.md`).
  - `test_escape_MSS_REGRA_OFF`, `test_defeito_libera` (frontmatter quebrado → `None`).
  - `test_hooks_json_pretooluse_write_edit_multiedit`.
- [ ] **Step 2:** rodar o arquivo → FAIL.
- [ ] **Step 3: Implementar.** `casa_glob`: normaliza `\` → `/`, compara em minúsculas (Windows), converte o padrão em regex: `**/` → `(?:.*/)?`, `**` → `.*`, `*` → `[^/]*`, `?` → `[^/]`, resto escapado, ancorado nos dois lados. Frontmatter `paths:` lido como em `templates/rules/*.md` (lista YAML de strings entre aspas). Saída de deny no formato do `hooks/projeto_ativo.py`. Motivo: `[mss-spec] antes de gravar <rel>, leia a regra deste tipo de arquivo (.claude/rules/<nome>):\n\n<texto sem frontmatter>\n\nDepois repita a gravação.` Registro `negou` com o nome da regra.
- [ ] **Step 4:** `python -m pytest -q` → verde.
- [ ] **Step 5: Commit** — `feat(regras): regra por tipo de arquivo lida antes de gravar`.

### Task 4: Correções dos hooks de teto

**Files:**
- Modify: `hooks/teto_ao_gravar.py:65-123`, `hooks/orcamento_partida.py:57-89`, `tests/test_hook_teto_ao_gravar.py`, `tests/test_hook_orcamento_partida.py`

**Interfaces:**
- Consumes: `MARCA` (Task 2) — copie a constante (hooks não importam um do outro), e um teste confere que as duas são iguais.
- Produces: em `teto_ao_gravar.py`, `JANELA_S = 120` e `mudou_agora(caminho: str, sessao: str, agora: float | None = None) -> bool`.

- [ ] **Step 1: Testes que falham**:
  - `test_wc_c_em_claude_md_antigo_nao_dispara`: `CLAUDE.md` com 10.500 B e `os.utime` 1 hora atrás; evento `Bash` `wc -c CLAUDE.md` → `None`.
  - `test_cat_do_index_antigo_nao_roda_enxugar`: INDEX gordo com mtime antigo; `Bash` `cat docs/superpowers/INDEX.md` → `None` e o arquivo não muda.
  - `test_gravacao_por_shell_recente_dispara`: INDEX gordo com mtime agora; `PowerShell` `Set-Content docs/superpowers/INDEX.md …` → move e avisa (comportamento atual).
  - `test_mesma_versao_nao_dispara_duas_vezes`: Edit dispara; logo depois `Bash wc -c` no mesmo arquivo sem mudança → `None`.
  - `test_claude_md_com_marca_teto_10000_so_avisa`; `test_kb_com_uma_casa` → mensagem contém `10,5 KB` e `teto 10,0 KB`.
  - Em `test_hook_orcamento_partida.py`: `test_kb_com_uma_casa_decimal` (10.096 B → `10,1 KB (teto 10,0 KB)`); `test_claude_sem_marca_acima_do_teto_manda_upgrade` (texto contém `/mss-spec:upgrade` e **não** contém `/mss-spec:doctor`); `test_claude_com_marca_acima_do_teto_manda_mover_bloco`; `test_marca_igual_nos_hooks`.
- [ ] **Step 2:** rodar os dois arquivos → FAIL.
- [ ] **Step 3: Implementar.** `teto_ao_gravar`: para `Bash`/`PowerShell`, o alvo citado só conta se `mudou_agora` — mtime dentro de `JANELA_S` **e** `(tamanho, mtime_ns)` diferente do último visto nesta sessão (estado no temp do SO, como `_memoria_de_acao.py`); `Write`/`Edit`/`MultiEdit` continuam pelo caminho e também gravam o estado. `orcamento_partida`: `_kb` com `:.1f` e vírgula; aviso do `CLAUDE.md` sem marca → "rode `/mss-spec:upgrade` pra migrar o CLAUDE.md (regras do kit passam a vir do plugin)"; o "ofereça `/mss-spec:doctor`" só fica quando o estouro é MAPA/INDEX/MEMORY. Texto continua ≤ 1.000 B.
- [ ] **Step 4:** `python -m pytest -q` → verde.
- [ ] **Step 5: Commit** — `fix(teto): leitura pelo shell nao conta como gravacao; KB com uma casa`.

### Task 5: Migração — montar e conferir (dry-run)

**Files:**
- Create: `templates/migrar_claude_md.py`, `templates/regras-do-kit/linhas-do-kit.txt`, `tests/test_migrar_claude_md.py`
- Create: `tests/fixtures/whats-2026-10-23/CLAUDE.md` e `tests/fixtures/whats-2026-10-23/.claude/rules/*.md` (cópia **lida** do Whats hoje: `CLAUDE.md` e os 7 arquivos de `.claude/rules/`)

**Interfaces:**
- Produces:
  - `normalizar(linha: str) -> str` (tira BOM, `\r`, espaços das pontas, marcador de lista `- `/`* `/`N. `; colapsa espaços).
  - `gerar_linhas_do_kit(repo: Path) -> list[str]` — linhas normalizadas não vazias de **todas** as versões de `templates/CLAUDE.md` no `git log` + dos dois blocos atuais; subcomando `python templates/migrar_claude_md.py historico` grava `templates/regras-do-kit/linhas-do-kit.txt` (ordenado, sem repetição).
  - `@dataclass Migracao`: `claude_novo: str`, `regras_novas: dict[str, str]` (nome → texto; só as alteradas), `saiu_do_kit: list[str]`, `moveu: list[tuple[str, str, str]]` (linha, de, para), `ficou_por_duvida: list[str]`, `falhas: list[str]`, `avisos: list[str]`, `ja_migrado: bool`.
  - `montar(proj: Path, linhas_kit: set[str]) -> Migracao`
  - `conferir(proj: Path, m: Migracao) -> list[str]` (devolve falhas; vazio = ok).

- [ ] **Step 1: Testes que falham** (com a fixture do Whats):
  - `test_linhas_do_kit_em_dia`: `gerar_linhas_do_kit(REPO)` == conteúdo de `linhas-do-kit.txt` (o arquivo foi regenerado depois da última mudança do molde/blocos).
  - `test_whats_contexto_sem_ponteiro_para_rules`: na `## Contexto` de `m.claude_novo`, nenhuma linha contém `.claude/rules/`; os rótulos `**Como roda:**`, `**Homologação (Azure):**`, `**Versionamento:**`, `**Banco:**`, `**Testes:**`, `**UI:**`, `**Infra:**` aparecem por extenso.
  - `test_whats_fatos_saem_do_arquivo_de_regra`: `m.regras_novas["deploy-e-ambiente.md"]` não tem mais `**Como roda:**`; `m.regras_novas["banco.md"]` não tem mais `**Banco:**` (item inteiro foi).
  - `test_whats_linhas_do_kit_saem`: `Não codar antes do meu OK explícito` não está em `m.claude_novo` e está em `m.saiu_do_kit`.
  - `test_whats_ponteiro_para_doc_do_projeto_fica`: as 4 linhas com `docs/MODO-DE-TRABALHO.md` estão em `## Regras obrigatórias do projeto`.
  - `test_whats_regras_do_projeto_ficam`: `.env` desta pasta **nunca** e `Nunca tocar o que é do RAG` estão em `## Regras obrigatórias do projeto`.
  - `test_whats_indice_cada_regra_uma_vez`: `## Índice de regras por tipo de arquivo` cita cada um dos 7 arquivos exatamente 1 vez.
  - `test_whats_conservacao`: `conferir(...) == []`; e toda linha normalizada do antes (CLAUDE.md + 7 regras) está no depois **ou** em `saiu_do_kit` (⊂ `linhas-do-kit.txt`) **ou** é linha-ponteiro de `## Contexto`/repetida com alvo listado no índice.
  - `test_whats_tamanho_vira_aviso_nao_falha`: força teto 5.000 via parâmetro → `m.avisos` tem a medida, `conferir` == `[]`.
  - `test_rotulo_inexistente_reprova` (Review Focus 3): fixture com `**Como roda:** → … deploy-e-ambiente.md` e o arquivo sem esse rótulo → `conferir` devolve falha citando a linha.
  - `test_linha_desconhecida_fica_por_duvida`: linha inventada dentro de `## Modo de trabalho` → vai pra `## Regras obrigatórias do projeto` e pra `ficou_por_duvida`.
- [ ] **Step 2:** `python -m pytest tests/test_migrar_claude_md.py -q` → FAIL.
- [ ] **Step 3: Implementar `montar`.** Seções por `## `. Classificação (ordem): (a) dentro de `## Contexto`, linha com `→` e `` `.claude/rules/<x>.md` `` → procura em `<x>.md` a linha que começa com o mesmo rótulo em negrito (mais as linhas seguintes indentadas) e põe no lugar, tirando-a do arquivo de regra; rótulo não achado → falha; (b) fora do Contexto, linha com `→` apontando arquivo que **não** é `.claude/rules/` → projeto (fica); (c) `normalizar(linha) in linhas_kit` → `saiu_do_kit`; (d) o resto → fica (o que veio de "Modo de trabalho"/"Regras críticas" vai pra `## Regras obrigatórias do projeto`; outras seções ficam com o título original, depois de `## Mapa de arquivos`); o que veio de (d) a partir de "Modo de trabalho" entra em `ficou_por_duvida` só se tem título em negrito igual a uma regra do kit. Índice gerado de `.claude/rules/*.md`: `- \`.claude/rules/<nome>\` — <1º título # do arquivo> — carrega ao tocar <padrões separados por vírgula>`. Arquivo com a marca → `ja_migrado = True`, nada muda. Comentários HTML do molde antigo saem só se `normalizar` casar em `linhas_kit`.
- [ ] **Step 4: Implementar `conferir`** com as conferências da spec (etapa 3): conservação, Contexto sem ponteiro e rótulos preservados, marca presente, índice com cada regra uma vez e arquivos existentes, working tree limpo nos arquivos tocados (`git status --porcelain -- <arquivos>` só leitura; sem git no projeto → falha "sem git não há ponto de volta"). Teto acima de 10.000 B → `avisos`, nunca falha.
- [ ] **Step 5:** `python templates/migrar_claude_md.py historico` e `python -m pytest -q` → verde.
- [ ] **Step 6: Commit** — inclua a fixture; `feat(migrar): monta e confere a migracao do CLAUDE.md (dry-run)`.

### Task 6: Migração — gravar, CLI e relatório

**Files:**
- Modify: `templates/migrar_claude_md.py`, `tests/test_migrar_claude_md.py`

**Interfaces:**
- Consumes: `montar`, `conferir`, `Migracao` (Task 5).
- Produces: `aplicar(proj: Path, m: Migracao) -> None`; `relatorio(m: Migracao, falhas: list[str]) -> str`; CLI `python templates/migrar_claude_md.py [--proj P] [--aplicar]` — exit **0** sem falhas, **1** com falhas (nada gravado), **0** com `já migrado`.

- [ ] **Step 1: Testes que falham** (projeto em `tmp_path` com `git init` + commit da fixture):
  - `test_dry_run_nao_grava`: CLI sem `--aplicar` → arquivos idênticos byte a byte; saída começa com `Prévia`.
  - `test_aplicar_grava_e_nao_toca_no_git`: depois de `--aplicar`, `CLAUDE.md` tem a marca; `git log` com o mesmo nº de commits; `git status --porcelain` lista só `CLAUDE.md` e as regras alteradas.
  - `test_aplicar_com_falha_nao_grava_nada`: fixture do rótulo inexistente → exit 1, arquivos intactos.
  - `test_working_tree_sujo_reprova`: `CLAUDE.md` modificado e não commitado → exit 1, falha cita `git restore`/working tree.
  - `test_crlf_e_bom_preservados` (Review Focus 1): fixture com CRLF → gravado continua CRLF; marca reconhecida.
  - `test_projeto_sem_rules_so_ganha_marca_e_secoes` (Review Focus 2): `CLAUDE.md` só com linhas de projeto → nenhuma linha some; marca presente.
  - `test_segunda_rodada_ja_migrado` (Review Focus 5): rodar `--aplicar` 2× → 2ª saída `já migrado`, nada muda.
  - `test_relatorio_curto`: contém as contagens de `saiu_do_kit`, `moveu`, `ficou_por_duvida` e os avisos; ≤ 40 linhas.
- [ ] **Step 2:** rodar → FAIL.
- [ ] **Step 3: Implementar** `aplicar` (grava com o fim de linha original de cada arquivo, como `_gravar` em `templates/rodizio_partida.py:66`), `relatorio` e o `main`. `--aplicar` roda `montar` + `conferir` de novo antes de gravar.
- [ ] **Step 4:** `python -m pytest -q` → verde.
- [ ] **Step 5: Commit** — `feat(migrar): grava so com tudo conferido, sem git`.

### Task 7: Comandos — upgrade, kickoff, analise, doctor

**Files:**
- Modify: `commands/upgrade.md`, `commands/kickoff.md:19-20`, `commands/analise.md:67`, `commands/doctor.md` (checks 3, 4, 9), `tests/test_smoke_kit.py`

- [ ] **Step 1: Testes de fiação que falham** em `tests/test_smoke_kit.py`:
  - `test_upgrade_migra_primeiro_e_sozinho`: `upgrade.md` cita `migrar_claude_md.py`, `<!-- mss-spec:regras-do-kit -->`, "primeiro", "nenhuma outra categoria", "regra de git do projeto"; diz que com a marca a categoria 2 não reacrescenta seção do kit.
  - `test_kickoff_grava_marca_sem_regra_do_kit`: `kickoff.md` cita a marca e não manda copiar regras do kit.
  - `test_analise_contexto_por_extenso`: `analise.md` contém "nunca ponteiro" junto de `## Contexto`.
  - `test_doctor_checks_3_4_9`: check 3 só chave vazia e `ℹ`; check 4 com "a verificar (fora do escritório/VPN)"; check 9 cita a marca, `10.000` e "regras do kit".
- [ ] **Step 2:** `python -m pytest tests/test_smoke_kit.py -q` → FAIL.
- [ ] **Step 3: Editar os comandos** conforme a spec ("Migração", "No `/mss-spec:upgrade`", "Correções que entram junto"). No `upgrade.md`: passo da migração = rodar o script em dry-run, mostrar o relatório, rodar `--aplicar` só sem falhas, e então branch + commit **conforme a regra de git do projeto** (padrão do kit: o assistente abre `chore/migrar-claude-md` a partir da principal e commita com stage nominal; projeto que reserva o git ao owner: entregar os comandos passo a passo).
- [ ] **Step 4:** `python -m pytest -q` → verde.
- [ ] **Step 5: Commit** — `feat(comandos): upgrade migra o CLAUDE.md; doctor sem ruido de ambiente`.

### Task 8: Fecho — versão, registro e dogfood no Whats (só leitura)

**Files:**
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `CHANGELOG.md`, `docs/EVALS.md` (F-040), `docs/decisoes.md`, `docs/specs/regras-do-kit-pelo-plugin.md` ("Estado atual" + "Histórico")

- [ ] **Step 1: Dogfood em dry-run** (o Whats é outro projeto: só leitura):

```bash
python templates/migrar_claude_md.py --proj "C:/Ronaldo/_Mitsui/Python/IA Bot Agent/IA Bot Agent - Whats"
```

Esperado: exit 0, `Prévia`, nenhuma falha; tamanho do `CLAUDE.md` novo na casa de ~9.000 B. Cole a saída no relatório pro owner. Confira com `git -C "<Whats>" status --porcelain` que nada mudou lá.
- [ ] **Step 2:** versão `0.42.0` nos dois manifestos; entrada no `CHANGELOG.md` no formato de `## 0.41.0`; F-040 no `docs/EVALS.md` (o que falhou: fatos de infra atrás de gatilho de arquivo + cópia velha das regras do kit; guardrail: Contexto por extenso conferido pela migração + regras pelo plugin); decisão datada em `docs/decisoes.md` ("regras do kit pelo plugin em vez de copiadas no CLAUDE.md — porque…"); "Estado atual" da spec descrevendo o que foi construído.
- [ ] **Step 3:** `python -m pytest -q` → verde, com a contagem final.
- [ ] **Step 4: Commit** — `chore(release): 0.42.0 -- regras do kit pelo plugin`.
- [ ] **Step 5:** relatório ao owner: saída do dogfood, o que muda na próxima janela de cada projeto, e o comando pra ele rodar `/mss-spec:upgrade` **na janela do Whats**. Integração (merge/push) segue a cerca de publicação: o owner aprova.
