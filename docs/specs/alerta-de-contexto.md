# Alerta de contexto e bola de neve — a janela avisa antes de encher

## Estado atual
**(1) `hooks/alerta_contexto.py`** — `UserPromptSubmit` + `PostToolUse`, ligado por padrão
(`hooks/hooks.json`), **não bloqueia**. Calcula a % da janela pelo `message.usage` da última resposta
do assistente fora de subagente no transcript (`input_tokens` + `cache_read_input_tokens` +
`cache_creation_input_tokens`; lê só a cauda de 512 KB). Janela: `MSS_JANELA_TOKENS` ›
`CLAUDE_CODE_AUTO_COMPACT_WINDOW` › `[1m]` no id ou uso acima de 200 mil → 1M › família 5 (Opus/Sonnet/
Fable; o id vem sem `[1m]`) → 1M › 200 mil (4.x, Haiku). No limiar (`MSS_ALERTA_CONTEXTO_PCT`, padrão **75**)
injeta `additionalContext` mandando o assistente avisar o owner na abertura da próxima mensagem e
fechar a janela (estado no `MAPA.md`, sobra no `to-dolist`, `/clear`) + `systemMessage` pro terminal.
Uma vez por faixa (75 · 85 · 95) por sessão; abaixo do limiar rearma. Ignora `agent_id`. Falha aberta;
escape `MSS_ALERTA_CONTEXTO_OFF=1`.

**(2) Bola de neve em prosa** — "pra fechar A preciso entender B": **entender** B = subagente (volta só
o resumo); **mexer** em B = `/mss-spec:to-dolist adicionar <B> (trava: <A>)`, nunca na janela de A.
Vive em `templates/CLAUDE.md` (seção "Contexto de janela", 8.000/8.000 bytes), `commands/to-dolist.md`
e no bloco "um assunto por janela" do `commands/nova-feature.md`.

**Fatos da fonte (doc do Claude Code, 2026-09-23):** nenhum hook recebe a % da janela — só a statusline
(`context_window.used_percentage`); o `systemMessage` não é exibido no app Desktop; a Anthropic **não**
documenta um limiar "saudável" — os 75% são escolha do owner.

Fora de escopo: detectar mecanicamente "o assunto mudou" (sem assinatura confiável; fica na prosa) ·
bloquear o prompt no limiar (rede, não cerca) · depender da statusline (exigiria o owner configurá-la).

## Histórico
- 2026-09-23 — criado: o owner relatou a janela de um assunto virando bola de neve ("pra fechar um
  assunto preciso entender outro") e pediu o reforço do to-dolist + janela nova e o alerta em 75%.
  Caso F-026.
- 2026-09-23 — fix (0.29.1): o owner mostrou o app com `184,8k / 1M (18%)` enquanto eu dizia 92% —
  o padrão fixo de 200 mil era premissa minha. A família 5 passa a ser 1M e a janela de compactação
  do owner (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`) entra antes do modelo. Caso F-027.
