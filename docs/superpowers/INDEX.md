<!-- Índice de tarefas do próprio kit mss-spec (dogfood). 1 linha por tarefa, mantido à mão.
     Nomes em linguagem simples (os do owner) — nada de apelido-código.
     Base: análise Gemini/GPT em docs/analise/ + discussão de jul/2026.
     Review de 2026-07-08 fica em memory/project_review_2026-07_pendencias.md (histórico). -->

# Índice de tarefas — mss-spec

## Feito
1. superpowers como dependência — **revertido** (a dep cross-marketplace quebrava o load via skills-dir/symlink; superpowers segue habilitado no `settings.json`). Reentra com o **item 9** (marketplace git), onde a allowlist funciona.
2. tirar C:\Ronaldo dos arquivos — caminhos portáveis (precedentes/banco) — fechada (7cda347)
3. to-dolist — captura rápida visível em qualquer branch — fechada (97c28cb)
4. doctor — pré-vôo do ambiente MSIG (manual + auto na 1ª tarefa) — **feito, sem commit** (feature/doctor)

## A fazer (ordem)
5. upgrade — sincroniza projeto existente com a evolução dos templates — **em andamento** (sem commit)
6. robustez do ${CLAUDE_PLUGIN_ROOT} — virou **checagem no doctor** (acha os templates: variável → locais padrão → falha alta) + **guard no kickoff** — feito (sem commit)
7. regra de senhas — segredo via variável de ambiente (`.env` dev → Azure App Settings prod); no `banco`, env-var **recomendado** + Fernet como opção; regra no SEGURANCA/CLAUDE — feito (sem commit)
8. anotar decisões (grandes e médias) — `docs/decisoes.md` (só transversais); mantido no fecho do `nova-feature`; kickoff cria skeleton — feito (sem commit)
9. [distribuição por git](../specs/2026-07-20-distribuicao-por-git-design.md) — instalar/atualizar o kit por URL git (mantendo a via de pasta local); prepara o mecanismo, desbloqueia o 12 — **fechada** (0.8.4)
10. [`upgrade --dry-run`](specs/2026-07-16-upgrade-design.md) — modo que mostra o diff que *seria* aplicado antes de tocar em arquivo (prevenção do merge silencioso dos arquivos de referência que o upgrade atualiza sozinho) — **fechada**
11. documentar "o git é o rollback" — 1-2 linhas no `upgrade`/`kickoff` + HTML: como ambos só mexem em arquivos versionados sob working tree limpo, `git restore`/descartar a branch já desfaz; sem comando de rollback dedicado (YAGNI) — **fechada** (2dc06f5, na master; dobrado na feature [redes de segurança](specs/2026-07-20-documentar-redes-de-seguranca-design.md))
12. [CI com artefatos de teste](../specs/2026-07-20-ci-artefatos-teste-design.md) — JUnit XML + cobertura + tendência de duração num CI (não commitar saída de run no repo — anti-padrão); **depende do item 9** (distribuição por git interno) — **fechada** (0.8.5)

## À parte
- documentação — CHANGELOG + seção de instalação do HTML — **fechada** (0.8.6: HTML de instalação em dia com a via git; CHANGELOG mantido a cada release)

## Novos — specs geradas (da análise GPT v2; implementar em OUTRO chat)
- log — padrão de logging MSIG (stdout + arquivo rotativo em dev, toggle no `.env`) — **fechada** (`/mss-spec:log` + `templates/logging.py`; kickoff monta infra; instrumentação opt-in por-arquivo) — spec: `docs/superpowers/specs/2026-07-16-log-design.md`
- release — checklist de pré-publicação (versão · CHANGELOG · testes · segurança · docs) — **fechada** (`/mss-spec:release`; só reporta, gate antes do finishing) — spec: `docs/superpowers/specs/2026-07-16-release-design.md`
- compliance — aderência do projeto às convenções do mss-spec — **fechada** (`/mss-spec:compliance`; checklist fixo, só reporta; audita × upgrade conserta) — spec: `docs/superpowers/specs/2026-07-16-compliance-design.md`
- [regras de branch e escopo](../specs/2026-07-17-regras-branch-e-escopo-design.md) — branch sempre da principal + alerta "um assunto por janela" (só doc/comandos, sem hook) — **fechada**
- [redes de segurança](specs/2026-07-20-documentar-redes-de-seguranca-design.md) — documenta as redes já existentes (auto-teste, git-rollback [item 11], changelog); fecha os falsos-negativos da análise — **fechada**

## Fora de escopo (não fazer)
Key Vault direto (escolhemos variável de ambiente) · profiles multi-nuvem · generators no lugar de templates · knowledge-graph · registry / capabilities / catálogo de arquiteturas / dependency-graph · policies como camada nova · feature matrix · hooks pre-commit bloqueantes · `modo` mexendo no `effortLevel`
