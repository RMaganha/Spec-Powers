# doctor — pré-vôo do ambiente MSIG (design)

Data: 2026-07-16 · feature do próprio kit mss-spec (branch `feature/doctor`).

## Objetivo
Comando `/mss-spec:doctor` **+ gatilho automático** que checa os pré-requisitos do ambiente MSIG e reporta ✓/✗, pra pegar erro de ambiente CEDO (não no build).

## Problema
Metade dos bugs do CHANGELOG são de ambiente (proxy/FortiGate, CA desatualizada, ODBC ausente, base `-bookworm`, rede docker). Descobrir isso só no build é frustrante. Falta um pré-vôo barato que avise antes.

## Critérios de aceite
- DADO um projeto com `docker-compose.yml`, QUANDO rodo `/mss-spec:doctor`, ENTÃO vejo ✓/✗ de: superpowers, `.env`×`.env.example`, proxy, `corp-ca.pem`, rede `mitiai_network`, ODBC 17 — só dos que se aplicam.
- DADO um projeto sem SQL Server (sem `pyodbc`), QUANDO rodo o doctor, ENTÃO o check de ODBC é PULADO (não vira ✗).
- DADO o início da 1ª tarefa de código da sessão, QUANDO o assistente começa, ENTÃO ele roda o pré-vôo e reporta ✓/✗ ANTES de codar (via regra do `CLAUDE.md`), sem bloquear.
- DADO qualquer check ✗, ENTÃO o doctor só REPORTA (não conserta, não bloqueia).

## Design
- **Dois pontos de entrada, mesma checagem:**
  - Manual: `/mss-spec:doctor` (`commands/doctor.md`, `disable-model-invocation`) — o humano dispara.
  - Auto: regra no `templates/CLAUDE.md` — o assistente roda o pré-vôo no início da 1ª tarefa de código da sessão e reporta antes de começar (mesmo espírito do plano-teste: o comando é do humano, mas a checagem o assistente roda direto). Não bloqueia.
- **Checks (condicionais — só o que se aplica):** **mss-spec acha os próprios templates** (alicerce, sempre — `${CLAUDE_PLUGIN_ROOT}` → locais padrão → falha alta) · superpowers habilitado (sempre) · `.env` tem as chaves do `.env.example` (se houver) · proxy corporativo alcançável (se rede corporativa) · `certs/corp-ca.pem` presente (se Docker) · rede `mitiai_network` existe (se `docker-compose.yml`) · ODBC Driver 17 (se `pyodbc`/SQL Server).
- **Valores esperados** (IP do proxy, nome da rede…) lidos de `docs/AMBIENTE.md` — nada hardcode.
- **Saída:** lista ✓/✗ só dos itens aplicáveis + veredito de 1 linha.

## Fora de escopo
Consertar o ambiente (só reporta) · checar dentro de container · virar hook ou script · bloquear o trabalho.

## Arquivos tocados
- novo `commands/doctor.md`
- `templates/CLAUDE.md` — regra do pré-vôo na 1ª tarefa
- `docs/superpowers/INDEX.md` — status
- `tests/test_smoke_kit.py` — checa que o `CLAUDE.md` referencia o pré-vôo

## Histórico
- 2026-07-16 — criado: design do doctor (aprovado no chat).
- 2026-07-16 — + checagem de resolução do plugin `${CLAUDE_PLUGIN_ROOT}` (→ locais padrão → falha alta) e guard no kickoff (feature "robustez", dobrada aqui por decisão: check no doctor, não comando à parte).
