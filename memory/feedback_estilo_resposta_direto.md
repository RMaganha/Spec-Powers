---
name: feedback-estilo-resposta-direto
description: Estilo de resposta direto (sem enrolação) virou regra no CLAUDE.md global — 5 regras extraídas da skill caveman, que foi avaliada e NÃO instalada
metadata:
  node_type: memory
  type: feedback
---

O owner adotou (2026-08-14) um bloco "Estilo de resposta — direto, sem enrolação" no **CLAUDE.md
global** (`~/.claude/CLAUDE.md`), com 5 regras: (1) resposta direta, sem preâmbulo nem hedging;
(2) **nunca** cortar negações ao encurtar; (3) código/comandos/erros/números sempre verbatim;
(4) sem abreviações inventadas (não economizam tokens e pioram leitura); (5) exceções que voltam ao
estilo completo — avisos de segurança, ações irreversíveis e sequências multi-etapa.

**Why:** as regras vieram da avaliação da skill [caveman](https://github.com/juliusbrussee/caveman)
(2026-08-14), que promete −65% de tokens de output mas admite no próprio README +1–1,5k tokens de
*input por turno* via hooks em `SessionStart`/`UserPromptSubmit` + edição do `settings.json` — custo
que anularia o ganho e conflitaria com superpowers/mss-spec. Decisão: **não instalar**; extrair só os
princípios como texto no CLAUDE.md (custo ~150 tokens 1x/sessão, zero hook). Segundo precedente da
regra [[feedback-avaliar-tool-externa-ideia-vs-stack]] (ideia sim, stack não).

**How to apply:** as regras já chegam pelo CLAUDE.md global — não duplicar em CLAUDE.md de projeto
nem reinstalar como skill/hook. Ao encurtar resposta, checar as regras 2–4 (negação, verbatim,
abreviação); nos casos da regra 5, ignorar a compressão e ser explícito. Alinha com
[[feedback-nivel-cerimonia-velocidade]] e [[feedback-nao-encerrar-com-pergunta]].
