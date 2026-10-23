---
paths:
  - "Dockerfile"
  - "docker-compose*.yml"
  - "azure-pipelines*.yml"
  - "docs/deploy-*"
  - "docs/homologacao-azure.md"
  - "docs/AMBIENTE.md"
  - "config/**"
---

# Deploy, runtime e pré-vôo

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

- **Pré-vôo de ambiente (doctor)**: no **início da 1ª tarefa de código da sessão** (antes de build/run), rode um pré-vôo rápido e **reporte ✓/✗ antes de começar** — pega erro de ambiente cedo, não no build. **Não bloqueia**, só avisa. Checks (só os que se aplicam ao projeto): **o mss-spec resolve (acha os templates)** · superpowers habilitado · `.env` tem as chaves do `.env.example` · proxy corporativo alcançável · `certs/corp-ca.pem` presente · rede `mitiai_network` existe · ODBC Driver 17 (se usa SQL Server). Valores esperados vêm do `docs/AMBIENTE.md` (nada hardcode). O `/mss-spec:doctor` roda o mesmo, disparado por você quando quiser.

- **Como roda:** em contêiner o processo é **gunicorn na porta 8000** (`CMD` do Dockerfile: `-w 1 --threads 8 --timeout 180 chat_server:app`) — o `app.run()` no fim do `chat_server.py` é só o caminho de desenvolvimento fora de contêiner, e o gunicorn **não executa** o `if __name__ == "__main__"`. O compose publica `5000:8000`, então a UI local segue em `http://localhost:5000/v2`. Subida: `docker compose up -d` (em casa/VPN) ou `docker compose -f docker-compose.yml -f docker-compose.office.yml up -d` (na empresa, com proxy + CA da MSIG) — atalhos `subir-CASA.bat` / `subir-EMPRESA.bat`. O **`-w 1` é requisito, não tuning**: o estado (cache de menu, memória de sessão, token) vive em memória de processo. O `WORKDIR` do container é `/app/api/_opcao4` **de propósito** (o código calcula `LOGS_DIR` por `parents[2]`; ajustá-lo é a fase 5, adiada).

- **Homologação (Azure):** a **mesma imagem** roda local e na nuvem, sem nenhum `if` de ambiente. Web App `mss-miti-ai-agent-bot-webwhats-dev-br` (`RG-MSSAI-DEV`), imagem no ACR `mssaicontainerregistry`, `WEBSITES_PORT=8000`, probe `GET /health`, pipeline `azure-pipelines.yml` disparado por push na branch `dev`. **Checklist: [docs/deploy-azure-dev.md](docs/deploy-azure-dev.md)** · roteiro detalhado: [docs/deploy-azure-dev.html](docs/deploy-azure-dev.html).

- **Versionamento:** **há repositório git próprio** desde 2026-07-28, na branch `main` — o vizinho `V2 - IA Bot Agent` é histórico (dele vêm só as `.claude/worktrees/`, que se ignora). ✅ **Remoto configurado em 2026-08-03**: `azure` → `agent-bot-webwhats` em `mitsui-mssdigital/MSS-AI` (Azure DevOps), com **`main` e `dev` publicadas** (87 commits). O 1º push da `main` foi `--force`, porque a interface do DevOps havia criado README e um Starter pipeline no remoto. A `dev` é a branch de deploy: push nela dispara o pipeline de homologação.
