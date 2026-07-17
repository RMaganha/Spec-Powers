---
description: Monta o padrão de logging MSIG (stdout + arquivo rotativo em dev) e instrumenta os arquivos escolhidos com logger
argument-hint: "[arquivo(s) alvo, opcional]"
disable-model-invocation: true
---

**Responda sempre em português (pt-BR).**

Você vai montar/estender o **padrão de logging MSIG** neste projeto. Mostre o que vai fazer e **confirme antes de gravar**. Nunca invente caminhos: use só o que existe no repo.

## Padrão (o "porquê")
- **stdout SEMPRE** — em Azure Web App o arquivo dentro do container é efêmero (some no restart/deploy/scale); quem pega o log em prod é o **stdout**. Em dev, o mesmo stdout aparece no terminal.
- **arquivo rotativo SÓ em dev** — `logs/app.log` (5 MB × 5), conveniência local. Em Azure não é criado.
- **ícone por nível SÓ em dev** — leitura rápida no terminal (🐛 DEBUG · ℹ️ INFO · ⚠️ WARNING · ❌ ERROR · 🔥 CRITICAL). Em Azure sai texto limpo (o log stream não renderiza emoji).
- Dev × Azure é detectado por `WEBSITE_SITE_NAME` (o App Service sempre define; dev local nunca tem) — zero config.
- **Nunca logar PII nem segredo** (casa com `docs/SEGURANCA.md §8`): ao logar algo que toque credencial/connection string, passe por `mask_password` (de `utils/get_connection.py`).

## Passos

1. **Monte a infra (uma vez por projeto).** Se ainda não existe, copie `${CLAUDE_PLUGIN_ROOT}/templates/logging.py` → `config/logging.py` (ou `utils/logger.py`, conforme a estrutura do projeto — ver `docs/ESTRUTURA.md`). **Antes de copiar, ache o template:** confirme que existe em `${CLAUDE_PLUGIN_ROOT}/templates/`; se a variável não resolveu, procure em `~/.claude/plugins/cache/*/mss-spec/*/templates/` ou `~/.claude/skills/mss-spec/templates/`. Não achou em nenhum → **PARE com erro claro** (o plugin não está resolvendo), nunca invente caminho.
2. **`.env.example`** — garanta as três chaves (crie o arquivo se faltar; comentário em **linha própria**, nunca inline — o Docker Compose `env_file` quebra com comentário inline):
   ```env
   LOG_ATIVO=true      # false → só WARNING+ (não silencia problema grave)
   LOG_LEVEL=INFO      # DEBUG|INFO|WARNING|ERROR|CRITICAL
   LOG_ICONES=true     # ícone por nível; efetivo só em dev (ignorado em Azure)
   ```
   Nunca grave um `.env` real com valores; só o `.env.example`.
3. **`.gitignore`** — garanta `/logs/` (ancorado na raiz; sem a barra pegaria uma pasta `logs/` em qualquer nível).
4. **Arranque** — em `main.py` (ou entrypoint), chame `setup_logging()` **uma vez** no topo, antes de criar clients/conexões.
5. **Instrumente os arquivos — PROTOCOLO (pergunte antes de escrever):**
   - **Liste os arquivos-alvo** (os passados em `$ARGUMENTS`, ou os módulos de domínio do projeto) com **resumo de 1 linha cada**, numerados. Ex.:
     ```
     1 - services/banco.py   — conexão e queries no SQL Server
     2 - services/regras.py  — regras de negócio do pedido
     3 - routers/api.py      — endpoints de integração
     ```
   - **Pergunte: "logs em todos, ou em quais? (números)"**. Regra de bolso: **banco, API e regras de negócio → sim**; script/util simples → geralmente não precisa.
   - Nos arquivos escolhidos, adicione no topo `import logging` + `logger = logging.getLogger(__name__)` e insira chamadas nos pontos úteis (início/fim de operação, ramo de erro com `logger.error`/`logger.exception`). O `__name__` faz cada linha **identificar o arquivo de origem** — não hardcode o nome do módulo.
   - **Não** instrumente arquivo que o dev não escolheu.

Alvo(s) informado(s): $ARGUMENTS
