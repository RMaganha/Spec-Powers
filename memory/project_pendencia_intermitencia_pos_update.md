---
name: project_pendencia_intermitencia_pos_update
description: PENDÊNCIA ABERTA — o mss-spec (junction skills-dir) às vezes para de funcionar DEPOIS de o app Claude Code atualizar, e sessão nova NÃO resolve; causa-raiz ainda não achada (falta capturar o estado quebrado)
gatilho: quando o mss-spec parar de responder depois de o app atualizar
metadata:
  type: project
---

**Status: ABERTA / investigando (2026-07-25).** Causa-raiz **ainda não confirmada** — não fingir que está resolvida.

## O sintoma (relato do owner)
Os comandos `/mss-spec:*` no projeto (ex.: Energy) **"hora rodam, hora não"**. O owner marcou:
- "aparece mas dá erro" · "assistente diz que não tem" · **"some depois de atualizar" (o app)** · **"nem sessão nova resolve"**.

**Separação importante:** "dá erro" e "diz que não tem" são as **4 faces da família de guardrail** já consertadas (v0.13.0–0.13.2 — [[project_mss_spec_instalado_por_junction]]); somem quando o projeto pega o `/mss-spec:upgrade`. O **genuinamente em aberto** é o **"some depois de atualizar + nem sessão nova resolve"** — isso é loading/infra, não percepção do assistente.

## O que já se sabe
- A junction é frágil por ser feita à mão (`~/.claude/skills/mss-spec` → clone de dev), fora do que o app rastreia — a doc do kit já alertava que `~/.claude` é volátil.
- No baseline saudável (2026-07-25) tudo OK: `claude plugin list` → `mss-spec@skills-dir` v0.13.2 `√ loaded`, junction intacta, mesmo já na app `2.1.219` (o update **nem sempre** quebra). Versões do claude-code coexistindo: `2.1.217` e `2.1.219`.
- Contradiz a memória [[project_mss_spec_instalado_por_junction]], que dizia "recarregar a sessão" resolve — no caso pós-update, **não resolve**.

## Próximo passo (o que destrava)
Capturar o **estado QUEBRADO** (não o bom) — rodar no PowerShell **no momento da falha**:
```powershell
$c = Get-ChildItem "$env:APPDATA\Claude\claude-code" -Recurse -Filter claude.exe -EA SilentlyContinue | Sort FullName -Desc | Select -First 1 -Exp FullName; & $c plugin list; Get-Item "$env:USERPROFILE\.claude\skills\mss-spec" -Force -EA SilentlyContinue | Select LinkType, Target
```
Discriminador: **junction sumida/quebrada** → é infra (recriar); **`loaded` mas comando erra** → é outra coisa (ver `${CLAUDE_PLUGIN_ROOT}` / versão nova sem re-scan).

Restaurar na hora (se a junction sumiu):
```powershell
$l="$env:USERPROFILE\.claude\skills\mss-spec"; if(Test-Path $l){(Get-Item $l -Force).Delete()}; New-Item -ItemType Junction -Path $l -Target "C:\Ronaldo\_Mitsui\Python\Spec-Powers"
```

Hipótese candidata a testar quando houver captura: update do app troca a versão ativa do claude-code e o re-scan de skills-dir não repega a junction até ela ser recriada. **Não cravar sem a evidência.**

**2026-11-03 — guardião RETIRADO (0.51.1).** O guardião da 0.51.0 (script `.ps1` por hook `SessionStart` + tarefa agendada) foi removido no mesmo dia útil: ao registrar a tarefa, o owner foi contactado pela infra e pela Segurança da Informação — **scripts PowerShell e tarefas agendadas não são permitidos na máquina**. Nada do kit pode rodar `.ps1` nem criar tarefa, e o assistente não executa mais esses comandos ([[project_sandbox_do_claude_nao_registra_tarefa_agendada]]). A pendência segue aberta; a alternativa sem script (instalar pelo marketplace local, sem junção, ou hook Python só de conferência) é decisão do owner (`docs/superpowers/MAPA.md`).
