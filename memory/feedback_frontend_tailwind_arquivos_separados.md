---
name: feedback-frontend-tailwind-arquivos-separados
description: "Front-end/HTML de aplicação — Tailwind + @tailwindcss/typography ou Mantine conforme o projeto (nunca os dois no mesmo app), e JS/CSS/estilos em arquivos e pastas separadas, nunca tudo inline"
gatilho: quando criar ou editar HTML, CSS ou JS de aplicação
sem_gatilho_de_acao: já tem cerca própria — regra por tipo de arquivo `.claude/rules/frontend.md`
conferida: 2026-11-16 — confirmada — fonte: templates/FRONTEND.md:22
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db2be446-fcee-4afe-88da-ad226447067e
---

Ao construir HTML/front-end de **aplicação**: o nível é **do projeto** (linha **UI:** do `CLAUDE.md`) —
Nível 1 = **Tailwind CSS** com o plugin **`@tailwindcss/typography`**; Nível 2 = **Mantine** (React + TS);
nunca os dois no mesmo app. Nos dois, **separar** JS, CSS e estilos em arquivos e pastas próprias
(ex.: `static/js/`, `static/css/`) — nunca tudo inline dentro de um único HTML.

**Why:** preferência de organização/manutenção do owner (engenheiro sênior). Código de front tudo
num arquivo só é o que ele quer evitar.

**How to apply:** vale para UIs de aplicação (ex.: painéis FastAPI + Jinja). **Exceção**: doc/relatório
standalone de arquivo único e portável (que se abre direto no navegador, sem servidor/build) — esse
mantém-se self-contained, senão perde a portabilidade. Já embutido no `templates/CLAUDE.md` do plugin (hoje mora em `templates/regras-do-kit/2-regras-criticas.md`)
mss-spec (linha da UI + Regra crítica de front-end). Relacionado a [[project-memoria-local-ao-repo]] e
[[feedback-nao-inventar-fatos-concretos]] (mesmo plugin).

substituiu: "sempre Tailwind" (decisão do owner, 2026-11-16) — Tailwind ou Mantine conforme o projeto, nunca os dois no mesmo app (`templates/regras-do-kit/2-regras-criticas.md:6`, [[project_front_moderno_mantine]]).
