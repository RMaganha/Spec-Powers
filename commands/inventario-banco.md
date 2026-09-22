---
description: Inventário somente-leitura do banco vivo (SQL Server) — catálogo, corpo das procedures/functions/views/triggers, jobs e linked servers, cruzado com o código; o /mss-spec:analise dispara sozinho, este comando regenera
argument-hint: "[base] (vazio: usa o ponteiro da seção Dados do docs/ARQUITETURA.md)"
---

**Responda sempre em português (pt-BR).**

Regenera o **inventário do banco vivo** deste projeto. Na primeira vez quem dispara é o `/mss-spec:analise` (passo *Dados — banco vivo*); aqui é o atalho pra rodar de novo quando o banco mudou, sem reanalisar o código.

1. **Credencial — nunca peça senha digitada.** Leia o ponteiro na seção *Dados* do `docs/ARQUITETURA.md` (servidor · base · ambiente · qual `get_connection.py` emprestou o par). Sem ponteiro, pergunte **qual base** e **qual projeto MSIG já alcança esse servidor**. Alternativa: a variável `MSS_INVENTARIO_CONN` com a conn string (serve `Trusted_Connection=yes`).

2. **Rode o gerador** (somente-leitura, só catálogo):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/inventario_banco.py" --proj . --fonte <get_connection.py> --ambiente D0 --base <base>
   ```

   `--par <BASE>` quando a fonte tem mais de um par (sem ele o script para e lista os nomes) · `--porta N` · `--max-objetos N` (default 2000) · `--out <dir>`. Se `${CLAUDE_PLUGIN_ROOT}` não resolver, ache o script nos locais padrão (`~/.claude/plugins/cache/.../mss-spec/templates/inventario_banco.py` ou o clone apontado pelo junction/skills-dir). Não achou → **PARE com erro claro**; nunca invente caminho. O `--fonte` é **lido por `ast`**, nunca importado: o código do outro projeto não roda.

3. **Saídas:**
   - `docs/banco.md` — retrato em texto, **pro assistente**; **fora do git** (linha ancorada `/docs/banco.md`). O script avisa se ela falta no `.gitignore`: **pergunte** antes de acrescentar (em projeto que já existia o `.gitignore` é do projeto).
   - `docs/banco/<esquema>.<objeto>.sql` — corpo de cada objeto, **versionado**, UTF-8 com BOM, segredo mascarado antes de gravar. É documentação, não script executável.
   - O script só sobrescreve ou remove arquivo com a marca `[inventario-banco]`: um `docs/banco.md` do time faz ele parar; `.sql` alheio em `docs/banco/` fica e é listado.

4. **Reporte** o que o script imprimiu: objetos, segredos mascarados (objeto + tipo — **nunca o valor**), lacunas (corpo criptografado, falta de `VIEW DEFINITION`, `msdb`), arquivos removidos. Atualize as contagens na seção *Dados* do `docs/ARQUITETURA.md`.

**"Sem citação" não significa "pode apagar"** — significa "não encontrei citação textual"; SQL montado em runtime não aparece na busca. Nunca proponha `DROP` a partir deste inventário.

Erro de conexão vem classificado: **REDE** (53/timeout — fora da rede corporativa nada responde), **TLS** (o servidor respondeu, mas a criptografia falhou — SQL Server antigo sem TLS 1.2 ou certificado não confiável), **CREDENCIAL** (login recusado) ou **PERMISSÃO** (o login não abre a base — conserto do owner).
