---
name: project_app_desktop_sem_painel_plugin
description: Nesta máquina o app Desktop não abre o painel do /plugin e o comando claude não está no PATH — passo que pede um dos dois não roda; o registro do plugin foi pelo settings.json
gatilho: quando um passo pedir `/plugin` ou o comando `claude` nesta máquina
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-11-03-guardiao-sem-script.md:35
metadata:
  type: project
---

No app Desktop do owner o painel do `/plugin` não aparece (*"o autocomplete do `/plu` nem oferece"*, 2026-07-24 —
memory/sessions/2026-07-24-kit-diz-que-o-frontend-nao-existe.md:15) e o comando `claude` não está no PATH. Em
2026-11-03 o registro do plugin pelo marketplace local foi feito no `settings.json`
(memory/sessions/2026-11-03-guardiao-sem-script.md:35).

**How to apply:** não mande o owner digitar comando do `/plugin` nem do `claude` sem antes conferir que existe ali; o caminho
que funcionou foi o `settings.json`. O app muda: confira de novo se o fato for de muito tempo atrás. Parentes:
[[project_mss_spec_instalado_por_junction]] e `docs/decisoes.md:62` (marketplace local).
