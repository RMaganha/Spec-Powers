---
name: feedback-brownfield-entender-nao-aplicar
description: Em projeto que já existe, entender e registrar primeiro — nunca aplicar molde/padrão por cima de infra, log ou UI própria que já funciona
gatilho: quando trabalhar num projeto que já existia antes do kit
metadata:
  node_type: memory
  type: feedback
  originSessionId: 127bdd9e-5b6d-47c6-a6e9-52d60cfd691a
---

Em projeto **que já existe** (brownfield), a ordem é **entender → registrar → parar**. Nunca aplicar o
molde/padrão da casa por cima do que já está lá: infra (`docker-compose`, `Dockerfile`, deploy), padrão
de log, módulo de conexão, e **principalmente a UI/UX própria** (HTML/CSS/JS feitos à mão) são
**intocáveis** por padrão. Divergência em relação ao padrão se **registra** (com a divergência descrita)
e a decisão fica com o owner — o padrão é **manter o do projeto**.

**Why:** o owner tem projeto real (RAG/pgvector) com infra montada e **UI/UX própria em `.html` que não
pode ser alterada**. Nas palavras dele, tentar implementar "coisa que o kit tem" ali "pode parar tudo e
termos que ajustar" — o retrabalho de desfazer um molde aplicado é maior que o ganho de padronizar. Isso
deixou de ser detalhe e virou o **eixo** do `/mss-spec:analise` (regra "não-destrutiva").

**How to apply:** ao entrar num projeto pronto, produza **levantamento**, não conserto: dossiê descritivo
(`docs/ARQUITETURA.md`) + tabela "não nasceu do kit" com as divergências. Não proponha o design system
como correção de uma tela que já existe. Não reorganize pastas. Se for irresistível sugerir, sugira
**depois** do levantamento, como pergunta, uma vez. Vale além do kit: qualquer entrada em código de
outro time. Relacionado a [[project-front-moderno-mantine]] (os 2 níveis de front só valem pra tela
nova) e [[feedback-nao-inventar-fatos-concretos]] (o que não foi lido é lacuna, não suposição).
