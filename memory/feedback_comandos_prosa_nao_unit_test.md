---
name: feedback_comandos_prosa_nao_unit_test
description: comandos do kit são prosa markdown, não código — testar por wiring no smoke, nunca por unit test de comportamento
gatilho: quando for escrever teste pra um comando ou skill do kit (.md)
sem_gatilho_de_acao: a ação é gravar arquivo de teste, que o gatilho de comando e de resposta não enxerga
conferida: 2026-11-17 — confirmada — fonte: docs/decisoes.md:83
metadata:
  type: feedback
---

Os comandos do mss-spec (`doctor`, `upgrade`, `nova-feature`, etc.) são **prosa markdown** que o
assistente executa — não há script Python do doctor nem do upgrade. Logo, **não** se escreve pytest de
"idempotência do doctor" ou "merge do upgrade": não há função com entrada/saída pra exercitar, e a
idempotência do doctor é verdadeira por construção (ele é read-only, "só reporta"). O nível certo de
teste pra comando-prosa é o que o `tests/test_smoke_kit.py` faz: o caminho e o template citados existem e o
manifesto é coerente. Frase presente no `.md` só quando é guarda de caso do `docs/EVALS.md`. Unit test de
comportamento de prosa = teste teatral.

substituiu: "wiring = a regra está presente" (revisão da suíte, 2026-11-17: 108 testes de frase cortados — `docs/decisoes.md`).

**Why:** análise externa sugeriu esses testes duas vezes; a resposta correta foi declinar as duas —
modelar comando-prosa como código é category-error e levaria a um refactor grande (transformar prosa em
código) contra o design do kit.

**How to apply:** ao pedirem "teste pro comando X", pergunte se X é código ou prosa. Prosa → oferecer no
máximo um teste-contrato (grep garantindo que o .md não mande escrever arquivo / diga "não mexe em
código"), avisando que é baixo valor. Relacionado: [[feedback_validacao_ui_deterministica]] (o que se
testa e como), [[feedback_nao_inventar_fatos_concretos]].
