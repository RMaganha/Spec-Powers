---
name: so-dependencia-estavel
description: Regra do owner — só dependências ESTÁVEIS em todos os componentes; nada de beta/rc/alpha/next, mesmo que a versão beta seja mais "parruda"
metadata:
  type: feedback
---

O owner decidiu (2026-07-13): **só dependências estáveis** — "eu quero o estável nada de beta para
todos os componentes". Vale pro plugin e pros projetos.

**Why:** beta/rc/pre-release num padrão herdado por todos os projetos vira dívida (breaking changes,
lib abandonada, vulnerabilidades transitivas). O caso que disparou: `mantine-react-table` (MRT) é mais
parruda que `mantine-datatable`, mas no **Mantine 7 só existe em beta** (`2.0.0-beta.*`; o estável 1.x
é Mantine 6). O ganho de features não paga o risco de beta num default.

**How to apply:** ao escolher lib/componente, checar o canal — se a versão compatível com a stack só
existe em beta/rc, **não usar**; ficar na alternativa estável e reavaliar quando sair estável. No front:
grid = `mantine-datatable` (estável), NÃO `mantine-react-table` enquanto beta. Codificado no
`templates/FRONTEND.md` e no scaffold `templates/frontend/`. Relacionado: [[front-moderno-mantine]].
