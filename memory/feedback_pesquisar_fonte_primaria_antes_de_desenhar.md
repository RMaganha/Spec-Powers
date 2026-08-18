---
name: feedback-pesquisar-fonte-primaria-antes-de-desenhar
description: Desenho que depende de como uma ferramenta/plataforma funciona exige a documentação PRIMÁRIA dela antes do design — não memória, não terceiro
gatilho: quando o desenho depender de como uma ferramenta ou plataforma funciona de verdade
metadata:
  node_type: memory
  type: feedback
---

Quando a feature depende de **como a ferramenta funciona de verdade** (Claude Code, uma API, um
runtime), abra a **documentação primária do fabricante** antes de desenhar — e não a sua memória nem
um artigo de terceiro. O artigo de terceiro serve pra dar a **ideia**; o mecanismo vem da fonte.

**Why:** nesta feature (2026-08-18) o desenho inicial era prosa genérica porque eu desenhei de
memória. O owner mandou pesquisar **na doc da Anthropic, não em terceiros** — e a leitura destampou
**quatro mecanismos que o kit não usava**: `.claude/rules/` com `paths:` (regra que carrega sozinha
quando um arquivo casa com o glob), o teto de **200 linhas / 25 KB** do índice de auto-memory, o fato
de que só o índice da pasta **nativa** é auto-carregado, e a orientação de que arquivo de instrução
inchado faz o modelo **ignorar** a regra que importa. Nada disso é dedutível; o desenho sem isso
resolvia o sintoma errado. O item do to-dolist tinha nascido de um artigo da OpenAI — a ideia veio de
lá, o mecanismo veio da fonte certa.

**How to apply:** antes de escrever a spec, liste as **2-4 perguntas de mecanismo** que o desenho
assume respondidas ("como isso carrega?", "qual o limite?", "o que roda sozinho?") e responda cada
uma com a doc primária, citando a frase. Se não achar, isso vira **premissa `sem fonte`** declarada
ao owner — não vira "eu acho que funciona assim". Parente de
[[feedback-nao-inventar-fatos-concretos]] e de [[feedback-item-de-backlog-nao-e-design]]; o mesmo
princípio aplicado a ferramenta externa está em [[feedback-avaliar-tool-externa-ideia-vs-stack]].
