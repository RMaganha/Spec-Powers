---
name: project_parse_md_do_kit_descartar_comentario
description: Ler .md do kit por código — descarte os comentários HTML antes de parsear (é onde vivem os placeholders) e filtre `<placeholder>` só em campo curto, nunca na linha inteira
gatilho: quando escrever código que parseia .md do kit
metadata:
  type: project
---

Extrator que lê os `.md` do kit (`decisoes.md`, `MEMORY.md`, `DIARIO.md`, `INDEX.md`) tem duas
armadilhas, as duas já cobradas em produção:

1. **Descarte os comentários HTML antes de parsear.** Todo molde do kit traz um comentário-guia no topo
   — e ele é cheio de bullets (`- <data> — decidimos <X> em vez de <Y>`, `- Só ponteiros de 1 linha…`).
   Sem descartar, um arquivo **recém-copiado do molde** produz "decisões" e "memórias" que o projeto
   nunca teve. Mapa que inventa fato é pior que mapa vazio.
2. **Filtro de `<placeholder>` só em campo curto e estruturado** (o assunto de uma entrada, o alvo de
   uma conexão) — **nunca na linha inteira**. Texto de verdade cita `<algo>` com naturalidade: a 1ª
   versão desse filtro engoliu a memória real cujo gancho fala de `~/.claude/projects/<proj>/memory/`.
   Placeholder em prosa é problema do item 1, não deste.

**Why:** os dois lares do placeholder são diferentes — o molde planta em **comentário** (some com o
descarte), e só o `DIARIO.md` tem uma linha-exemplo **viva** fora de comentário (é ela que precisa do
filtro estreito).

**How to apply:** ao escrever/alterar extrator de `.md`, use o helper de linhas úteis (comentário fora)
e reserve o teste de placeholder pro campo capturado por regex, com um caso de não-regressão de texto
real que contém `<…>`.

Relacionado: [[feedback_nao_inventar_fatos_concretos]] (a regra que isso protege, na versão automática) e
[[project_dogfood_gerador_diff_antes_depois]] (foi o diff no repo real que pegou o falso positivo).
