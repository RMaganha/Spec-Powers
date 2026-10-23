---
paths:
  - "tests/**"
  - "docs/superpowers/PLANO-TESTE.md"
---

# Testes

<!-- Movido do CLAUDE.md em 2026-09-23 (teto de 10 KB; F-029/F-030 do kit): texto VERBATIM. A regra continua valendo — o CLAUDE.md mantém a frase-chave e aponta pra cá. -->

- **Testes:** há **10 suítes** em `tests/` e o baseline formal está em [`docs/superpowers/PLANO-TESTE.md`](docs/superpowers/PLANO-TESTE.md) — o comando de cada uma está lá. **Não há pytest** (deliberado: o `requirements.txt` é enxuto e não existe Python no host, só Docker); cada suíte é script Python puro com exit code, rodado por `docker compose run --rm --no-deps -T agent_bot python tests/<arquivo>.py`. O canário é o `tests/smoke_rotas.py`, de **estrutura**, não de comportamento. As lacunas (conversa real, handoff, cotação, financeiro) estão declaradas no próprio `PLANO-TESTE.md`.
