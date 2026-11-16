---
name: feedback-frontend-tailwind-arquivos-separados
description: "Front-end/HTML de aplicação — sempre Tailwind CSS + plugin @tailwindcss/typography, e JS/CSS/estilos em arquivos e pastas separadas, nunca tudo inline"
gatilho: quando criar ou editar HTML, CSS ou JS de aplicação
sem_gatilho_de_acao: já tem cerca própria — regra por tipo de arquivo `.claude/rules/frontend.md`
conferida: 2026-11-13 — conflito — fonte: .claude/rules/frontend.md:11
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db2be446-fcee-4afe-88da-ad226447067e
---

Ao construir HTML/front-end de **aplicação**: usar sempre **Tailwind CSS** com o plugin
**`@tailwindcss/typography`**, e **separar** JS, CSS e estilos em arquivos e pastas próprias
(ex.: `static/js/`, `static/css/`) — nunca tudo inline dentro de um único HTML.

**Why:** preferência de organização/manutenção do owner (engenheiro sênior). Código de front tudo
num arquivo só é o que ele quer evitar.

**How to apply:** vale para UIs de aplicação (ex.: painéis FastAPI + Jinja). **Exceção**: doc/relatório
standalone de arquivo único e portável (que se abre direto no navegador, sem servidor/build) — esse
mantém-se self-contained, senão perde a portabilidade. Já embutido no `templates/CLAUDE.md` do plugin (hoje mora em `templates/regras-do-kit/2-regras-criticas.md`)
mss-spec (linha da UI + Regra crítica de front-end). Relacionado a [[project-memoria-local-ao-repo]] e
[[feedback-nao-inventar-fatos-concretos]] (mesmo plugin).

CONFLITO: `templates/regras-do-kit/2-regras-criticas.md:6` (sem data) diz "Front-end sempre Tailwind"; `templates/FRONTEND.md:22` (decisão de 2026-07-13, [[project_front_moderno_mantine]]) diz que onde a Mantine entra o Tailwind sai. O lado a manter é do owner.
