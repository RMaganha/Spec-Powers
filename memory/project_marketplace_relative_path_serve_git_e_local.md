---
name: marketplace-relative-path-serve-git-e-local
description: marketplace.json com source relative-path serve tanto add por pasta local quanto por URL git — o Code clona o repo e resolve o plugin dentro do clone; não precisa source separado
metadata:
  type: project
---

No `.claude-plugin/marketplace.json`, um plugin com `source` **relative-path** (ex.: `path: "."`, plugin
na raiz do próprio repo do marketplace) resolve **igual** nas duas vias de distribuição: quando o
marketplace é adicionado por **pasta local** (`/plugin marketplace add ./pasta`) **e** quando é
adicionado por **URL git** (`/plugin marketplace add <url>#ref`). No caso git, o Claude Code **clona o
repo** e resolve o `relative-path` **relativo ao clone** — então o **mesmo manifesto serve às duas vias,
sem source separado**.

**Why:** economiza manter dois manifestos/branches e foi o que permitiu "distribuição por git" (item 9)
não trocar o `source` — só reescrever a doc de instalação. Confirmado nos docs oficiais do Code
(plugin-marketplaces): relative-path resolve contra a cópia local do marketplace.

**How to apply:** para publicar o kit num git interno, basta `git remote add` + `push` e trocar o
`<URL-do-git-interno>` do `LEIA-ME.md` pela URL real — nenhum ajuste no `source`. **Pegadinha:** só
quebra se alguém apontar o marketplace direto pro **arquivo** `marketplace.json` cru (aí só o arquivo é
baixado, e o relative-path não resolve) — tem que apontar pro **repo**. Relacionado:
[[plugin-load-cross-marketplace]] (por que a dependência superpowers ainda não é declarada).
