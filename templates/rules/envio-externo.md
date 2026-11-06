---
paths:
  - "**/*email*.py"
  - "**/*mail*.py"
  - "**/*webhook*.py"
  - "**/*notific*.py"
  - "**/*envio*.py"
  - "**/*sms*.py"
  - "**/*whatsapp*.py"
---

# Envio externo (e-mail, webhook, mensagem)

- **Nasce em modo de teste.** Três flags separadas, padrão o mais seguro: `--dry-run` (padrão: mostra o
  resumo, nada sai) · `--enviar` (só pro destino de teste de variável de ambiente, ex. `EMAIL_TESTE`) ·
  `--enviar-real` (destino de produção, também por variável). Detalhe em `docs/SEGURANCA.md`, seção 14.
- **Fallback nunca silencioso**: item que caiu no caminho alternativo aparece no log e no resumo, com o motivo.
- **Envio em massa** pede o OK do owner com a contagem e 3 exemplos de destinatário antes do `--enviar-real`.
- **Id idempotente** por envio (chave do registro + data): reexecutar não duplica.
- Destinatário e conteúdo **nunca em log com PII**; URL/segredo do canal só por variável de ambiente.

Memória de origem: `memory/project_envio_externo_nasce_em_teste.md` (benchmark MSIG_Agentes, 2026-11-06 —
regra aprendida lá com envio real disparado em teste).
