---
name: project_hook_ask_aparece_no_desktop
description: Pra um hook ALERTAR o owner no app Desktop, o único canal que aparece é o `permissionDecision: "ask"` do PreToolUse (exit 0) — systemMessage não aparece e additionalContext depende do assistente relatar
gatilho: quando desenhar hook que precisa alertar o owner ou pedir confirmação antes de uma ação
metadata:
  type: project
---

2026-09-23 (0.31.0): o owner pediu *"só preciso ser alertado dos comandos git, mas você poderia
rodar"*. Canais de um hook, no app Desktop:
- `systemMessage` — **não aparece** no Desktop (achado do `alerta_contexto.py`, 0.29.0);
- `additionalContext` — vai pro assistente; o owner só vê se o assistente relatar (é prosa de novo);
- `hookSpecificOutput.permissionDecision: "ask"` + `permissionDecisionReason` — **aparece**: o app
  mostra o comando e o motivo, o owner aprova ou recusa. Validado ao vivo com `git push --dry-run`
  de feature (*"apareceu sim, aprovei"*).

**Why:** a doc (code.claude.com/docs/en/hooks.md e permissions.md) diz o formato e que regra de
permissão `ask` ainda pede aprovação mesmo com o hook liberando; o comportamento no modo de
permissão desta máquina só se provou no dogfood — o agente-guia chegou a deduzir além da doc.

**How to apply:** alerta que o owner PRECISA ver → `ask` com exit **0** (exit 2 é bloqueio e ignora
o JSON); bloqueio → `deny` + exit 2 + motivo no stderr. Prove no dogfood antes de prometer.
Relacionado: [[feedback_publicacao_e_ato_do_owner]].
