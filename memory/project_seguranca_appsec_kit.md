---
name: project-seguranca-appsec-kit
description: Capacidade de segurança do kit — baseline SEGURANCA.md, /mss-spec:seguranca, e os princípios decididos (obscuridade≠segurança, frontend público, auth 2 baldes)
metadata:
  type: project
---

O kit ganhou frente de segurança (spec `specs/2026-07-16-seguranca-appsec-design.md`): baseline
`templates/SEGURANCA.md` (OWASP-adaptado ao stack), regra secure-by-default no `CLAUDE.md`, e comando
`/mss-spec:seguranca` (audita o app inteiro, relatório priorizado, corrige com OK; complementa o
`/security-review` nativo que só vê o diff).

Princípios cravados com o owner (valem em decisões futuras): **obscuridade não é segurança** — não
criptografar/ofuscar URL de asset (o HTML entrega a URL; a chave viaja no código). **Frontend é
público** — nada de segredo/URL interna no bundle; higiene de build (minify, sem source-map, sem
console sensível). **Auth em dois baldes**: consumo próprio (front→backend do próprio app) = login de
usuário (seam futuro), nunca o bearer de integração; **integração** (outro sistema→backend) = Bearer
`TOKEN_API` server-to-server no `.env`, ligado por `AUTH_TOKEN_ATIVO` (false dev / true prod). HTTPS só
em prod (o token de prod nunca trafega em HTTP). Login de usuário no browser (JWT/sessão) ficou **fora
de escopo** agora. Ver [[feedback-validacao-ui-deterministica]].
