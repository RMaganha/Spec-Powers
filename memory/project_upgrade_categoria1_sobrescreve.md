---
name: project-upgrade-categoria1-sobrescreve
description: Nunca gravar conteúdo levantado do projeto em arquivo que o /mss-spec:upgrade sobrescreve sozinho (categoria 1) — é apagado no próximo upgrade
gatilho: quando gravar conteúdo levantado do projeto num arquivo de doc
metadata:
  node_type: memory
  type: project
  originSessionId: 127bdd9e-5b6d-47c6-a6e9-52d60cfd691a
---

No kit `mss-spec`, a **categoria 1 do `/mss-spec:upgrade`** substitui arquivos pelo molde **sem
perguntar**: `docs/SEGURANCA.md`, `docs/ESTRUTURA.md`, `docs/FRONTEND.md`, os `docker-compose*`/
`Dockerfile`/`.dockerignore` e o `.gitignore`. Logo: **nada específico do projeto pode morar neles** —
seria apagado no próximo upgrade. Conteúdo levantado/escrito pelo projeto vai em doc que o kit **não**
sincroniza (ex.: `docs/ARQUITETURA.md`) ou em arquivo de **categoria 2** (mescla: `CLAUDE.md`,
`AMBIENTE.md`, `MAPA.md`).

**Why:** na feature do `/mss-spec:analise` (0.14.0) eu fiz o comando escrever as **camadas reais** do
projeto no `docs/ESTRUTURA.md` — que é categoria 1. O levantamento seria silenciosamente apagado no
primeiro `upgrade`. A revisão de código pegou antes de integrar. Disso nasceu a fronteira: **`ESTRUTURA.md`
= prescritivo do kit** (dono: `upgrade`) × **`ARQUITETURA.md` = descritivo do projeto** (dono: `analise`).

**How to apply:** antes de fazer um comando gravar em algum doc, verifique em qual categoria do
`commands/upgrade.md` esse arquivo cai. Categoria 1 = **só molde**, nada de projeto. E a recíproca virou
regra: arquivo **pré-existente** do projeto listado como "não nasceu do kit" no `ARQUITETURA.md` faz a
categoria 1 **perguntar** em vez de sobrescrever. Relacionado a
[[feedback-brownfield-entender-nao-aplicar]].
