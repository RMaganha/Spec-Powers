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
9. loja interna (marketplace no git) — publicar pro time — **por último**

## À parte
- documentação — CHANGELOG + seção de instalação do HTML

## Novos — specs geradas (da análise GPT v2; implementar em OUTRO chat)
- log — padrão de logging MSIG (stdout + arquivo rotativo em dev, toggle no `.env`) — **fechada** (`/mss-spec:log` + `templates/logging.py`; kickoff monta infra; instrumentação opt-in por-arquivo) — spec: `docs/superpowers/specs/2026-07-16-log-design.md`
- release — checklist de pré-publicação (versão · CHANGELOG · testes · segurança · docs) — **fechada** (`/mss-spec:release`; só reporta, gate antes do finishing) — spec: `docs/superpowers/specs/2026-07-16-release-design.md`
- compliance — aderência do projeto às convenções do mss-spec — **fechada** (`/mss-spec:compliance`; checklist fixo, só reporta; audita × upgrade conserta) — spec: `docs/superpowers/specs/2026-07-16-compliance-design.md`
- [regras de branch e escopo](../specs/2026-07-17-regras-branch-e-escopo-design.md) — branch sempre da principal + alerta "um assunto por janela" (só doc/comandos, sem hook) — **fechada**

## Fora de escopo (não fazer)
Key Vault direto (escolhemos variável de ambiente) · profiles multi-nuvem · generators no lugar de templates · knowledge-graph · registry / capabilities / catálogo de arquiteturas / dependency-graph · policies como camada nova · feature matrix · hooks pre-commit bloqueantes · `modo` mexendo no `effortLevel`
