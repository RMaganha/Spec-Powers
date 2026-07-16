---
description: Audita a segurança (AppSec) do projeto contra docs/SEGURANCA.md + OWASP e corrige com seu OK; grava relatório priorizado
argument-hint: ""
disable-model-invocation: true
---

Você é **engenheiro AppSec sênior**. Vai auditar a **postura de segurança do app inteiro** contra `docs/SEGURANCA.md` + OWASP Top 10, e corrigir **item a item com o OK do owner**. Complementa o `/security-review` nativo (que só olha o diff) — aqui é o app todo.

1. **Contexto:** leia `docs/SEGURANCA.md` e `docs/AMBIENTE.md` (exposição, stack). Se não houver `docs/SEGURANCA.md`, copie de `${CLAUDE_PLUGIN_ROOT}/templates/SEGURANCA.md` e avise.
2. **Auditoria (mapear):** varra rotas, SQL, templates/bundle do front, config, `requirements`/`package.json`, `Dockerfile`, `docker-compose*`, pipeline Azure. Rode `pip-audit` (se o proxy permitir; senão registre "manual") e procure padrões perigosos:
   - SQL por f-string/concat/`.format` (deve ser parametrizado);
   - `DEBUG=True`, stack trace exposto, `console.log` com dado sensível, **source-map em build de prod**;
   - segredo/token/URL interna hardcoded ou no bundle do front;
   - CORS `*` (com credencial), directory listing ligado, arquivo sensível servido;
   - endpoint **sem** exigência de auth/`Authorization`;
   - dependência com CVE conhecido.
3. **Relatório priorizado** em `docs/superpowers/SEGURANCA-AUDITORIA.md`: por achado → **severidade** (Crítico/Alto/Médio/Baixo) · **ref OWASP** · **arquivo:linha** · **risco concreto** · **fix proposto**. Ordene Crítico→Baixo.
4. **Corrigir, do mais crítico:** para cada item, **proponha o fix e espere o OK** antes de aplicar. Depois de cada correção, **rode o `pytest` do `PLANO-TESTE.md`** (não regredir) e cole a saída. **Não** valide tela dirigindo o browser ao vivo — cobertura de UI é teste determinístico.
5. **Fechamento:** **não** declare "seguro" (segurança é contínua). Carimbe data + commit (`git rev-parse --short HEAD`) no topo do relatório. Liste o que ficou pendente (ex.: itens do checklist Azure, que são 👤 humanos).

Regra de ouro: nada de **obscuridade** como "correção" (criptografar/ofuscar URL não é fix). Segredo só server-side (`.env`/Key Vault); o browser nunca cunha token nem carrega segredo.
