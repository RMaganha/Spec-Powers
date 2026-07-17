# log — padrão de logging MSIG (design)

Data: 2026-07-16 · feature do kit mss-spec. **Spec gerada nesta sessão; brainstorming aprovado — implementação em OUTRO chat.**

## Objetivo
Padrão único de logging pros projetos MSIG: `logging` da stdlib com um setup central, saída pro **stdout** (que o Azure captura) **+** arquivo **rotativo** local em `logs/` (conveniência de dev), ligado/desligado pelo `.env`.

## Problema
Hoje não há logging padronizado (uso de `print`, ou nada). Em **Azure Web App** o arquivo dentro do container é **efêmero** (some no restart/deploy/scale) — quem "pega" o log em prod é o **stdout**. Falta um padrão que sirva nos dois mundos (dev local com arquivo, prod Azure com stdout) sem o dev decidir isso a cada projeto.

## Critérios de aceite
- DADO `LOG_ATIVO=true`, QUANDO o app roda, ENTÃO loga pro **stdout** no nível de `LOG_LEVEL` (default INFO).
- DADO dev local com `LOG_ATIVO=true`, ENTÃO também grava um arquivo **rotativo** em `logs/` (por tamanho ou por dia).
- DADO `LOG_ATIVO=false`, ENTÃO não emite log de aplicação (ou só WARNING+ — decidir na implementação).
- DADO qualquer log, ENTÃO **nunca** grava PII/segredo (usa `mask_password` — casa com `SEGURANCA.md §8`).
- DADO o repo, ENTÃO `logs/` está no `.gitignore` (ancorado `/logs/`).

## Design
- **`templates/logging.py`** → copiado pra `config/logging.py` (ou `utils/logger.py`): função `setup_logging()` que configura o logger:
  - `StreamHandler` → **stdout**, sempre (dev vê no terminal; Azure captura).
  - `RotatingFileHandler`/`TimedRotatingFileHandler` → `logs/app.log`, só quando `LOG_ATIVO` e em dev; com rotação (ex.: 5 MB × 5 backups, ou diário) pra não encher o disco.
  - Formatter: timestamp · nível · módulo · mensagem. Nível vem de `LOG_LEVEL`.
  - No código: `logger = logging.getLogger(__name__)` → `logger.info/warning/error/critical`.
- **`.env.example`**: `LOG_ATIVO=true` · `LOG_LEVEL=INFO` (convenção `*_ATIVO` da casa).
- **`.gitignore`**: `/logs/` (ancorado na raiz).
- **Regra** curta no doc (AMBIENTE ou SEGURANCA): em prod o que vale é o stdout; o arquivo é dev.

## Decisões (fechadas na implementação 2026-07-17)
- **Gatilho = híbrido.** O `kickoff` monta só a **infra** (`config/logging.py` + `.env`/`.gitignore`) — barata, não gera log sozinha. A **instrumentação é opt-in por-arquivo**: comando `/mss-spec:log` (avulso/retroativo) **e** um **protocolo transversal** — todo comando que gera arquivos lista os alvos (resumo de 1 linha cada) e pergunta "logs em todos ou em quais?" (banco/API/regras sim; script simples não).
- **Identificação da origem:** `logging.getLogger(__name__)` + `%(name)s` no formatter — cada linha mostra o módulo (mapeia 1:1 pro arquivo). Sem hardcode.
- **Ícone por nível** (🐛/ℹ️/⚠️/❌/🔥) **só em dev** — Azure = texto limpo (o log stream não renderiza emoji). Dev × Azure detectado por `WEBSITE_SITE_NAME` (o App Service sempre define). Toggle `LOG_ICONES` (efetivo só em dev).
- **`LOG_ATIVO=false` → só WARNING+** (não silencia problema grave).
- **Formatter texto** (não JSON) — JSON fica como evolução se for pra App Insights/Log Analytics.

## Fora de escopo
Sink externo (App Insights / Log Analytics) — evolução futura · métricas/tracing (isto é logging, não observabilidade completa) · retenção/rotação em prod (responsabilidade do Azure).

## Histórico
- 2026-07-16 — criado: design aprovado no chat (stdout + arquivo rotativo em dev, toggle no `.env`). Implementar em outro chat.
- 2026-07-17 — implementado: `templates/logging.py` (`setup_logging()`), comando `/mss-spec:log`, kickoff monta a infra, `/logs/` no gitignore, regra 7 no `CLAUDE.md`. Decisões fechadas: gatilho híbrido (infra no kickoff + instrumentação opt-in por-arquivo via protocolo transversal), ícone por nível só em dev (`WEBSITE_SITE_NAME`), `LOG_ATIVO=false`→WARNING+. Testado: `tests/test_logging_template.py` (7 ACs de comportamento) + wiring no smoke. 21/21 verde.
