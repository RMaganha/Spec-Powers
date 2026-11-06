---
name: project-envio-externo-nasce-em-teste
description: Código que envia pra fora (e-mail, webhook, mensagem) nasce com 3 modos em flags separadas — dry-run padrão, destino de teste, real — e fallback nunca silencioso
gatilho: quando escrever ou revisar código que envia e-mail, webhook, SMS ou mensagem pra fora do app
metadata:
  type: project
---

Todo envio externo nasce com **três modos, em flags separadas, e o padrão é o mais seguro**: `--dry-run`
(padrão: monta e mostra o resumo, nada sai) · `--enviar` (só pro destino de teste de variável de ambiente,
ex. `EMAIL_TESTE`) · `--enviar-real` (destino de produção, também por variável). **Fallback nunca é
silencioso**: o item que caiu no caminho alternativo aparece no log e no resumo, com o motivo. Envio em
massa pede o OK do owner com a contagem e 3 exemplos de destinatário. Id idempotente por envio.

**Why:** benchmark do kit de agentes da equipe MSIG (2026-11-06, `docs/analise/2026-11-06-benchmark-msig-agentes.md`,
item 12): a regra de lá nasceu de e-mail real disparado durante um teste e de item pulado em silêncio num
envio com fallback (pedido do usuário de lá em 09/2026). Aqui ela entra antes do primeiro incidente.

**How to apply:** a regra path-scoped `.claude/rules/envio-externo.md` carrega sozinha ao tocar
`*email*.py`, `*webhook*.py`, `*notific*.py`…; o baseline está em `docs/SEGURANCA.md`, seção 14, e o
`/mss-spec:seguranca` audita envio sem os 3 modos. Relacionado: [[feedback-brownfield-entender-nao-aplicar]]
(a regra se aplica a código novo; envio que já existe se registra, não se reescreve).
