---
description: Roda o plano de teste base (pytest) e, se passar 100%, grava/atualiza o baseline em docs/superpowers/PLANO-TESTE.md
argument-hint: ""
disable-model-invocation: true
---

Você vai rodar/atualizar o **plano de teste base** deste projeto — a rede anti-regressão ("se isso passa 100%, nada quebrou"). O baseline vive em `docs/superpowers/PLANO-TESTE.md`.

1. **Se não existir suíte (`tests/`) nem `docs/superpowers/PLANO-TESTE.md`:** crie um plano MÍNIMO (smoke) com pytest — ex.: o app importa/sobe, os endpoints-chave respondem 200, a conexão de banco abre (use os padrões do projeto; consulte `docs/AMBIENTE.md`). Siga `superpowers:test-driven-development` e **confirme comigo antes de gravar testes novos**.
2. **Rode a suíte:** `pytest -q` (ou o runner do projeto). **Cole a saída real** — `superpowers:verification-before-completion`, nunca afirme sem a saída.
3. **Se 100% verde:** grave/atualize `docs/superpowers/PLANO-TESTE.md` como o novo baseline, contendo:
   - o comando para rodar (ex.: `pytest -q`);
   - a lista do que o baseline cobre (1 linha por área/teste);
   - o carimbo do último 100%: data + commit (`git rev-parse --short HEAD`).
   O conteúdo anterior é **substituído** (o git guarda o histórico). Commit: `test: atualiza plano de teste base (baseline verde)`.
4. **Se NÃO passar 100%:** reporte exatamente o que falhou e **NÃO** atualize o baseline — o `PLANO-TESTE.md` anterior continua sendo a base válida. Corrija (ou me traga o diagnóstico) antes de regravar.

Regra de ouro: o baseline só é atualizado com a suíte **100% verde**. Nunca promova a base algo que não passou inteiro.
