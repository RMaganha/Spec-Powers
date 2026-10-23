---
paths:
  - "**/*.py"
---

# Logging

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

7. **Logging — estado misto, declarado.** O padrão **atual e majoritário** do projeto é logger inline por módulo: `logging.getLogger("mitiai.<feature>")` com handler próprio e nível por `MITIAI_LOG_LEVEL`. O `config/logging.py` do kit foi instalado em 2026-07-28 (`setup_logging()` → stdout sempre + arquivo rotativo em `logs/` só em dev, chaves `LOG_ATIVO`/`LOG_LEVEL`/`LOG_ICONES`), mas **nenhum módulo o chama ainda** — a migração é tarefa `aberta` no INDEX. Enquanto ela não acontecer: **código novo** usa `setup_logging()`/`getLogger(__name__)`; **código existente** mantém o padrão inline (não converta de passagem). Em qualquer caso: **nunca `print` em módulo novo** (o `chat_server.py` usa `print` largamente — é o legado, não o alvo) e **nunca logar PII nem segredo** — máscara no que tocar credencial, e cuidado especial com o `actions_trace`, que carrega texto de conversa.
