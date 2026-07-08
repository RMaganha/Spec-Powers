---
name: feedback-nao-inventar-fatos-concretos
description: Nunca chutar caminhos/hosts/nomes de recurso concretos — usar só o que está no repo/projeto.md ou o que o owner confirmar
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c2de51e1-1688-4cbf-a01e-3947b1d77c12
---

Ao propor opções, rascunhos de contexto ou qualquer detalhe de infraestrutura, NUNCA inventar fatos
concretos: caminhos de deploy, paths, hosts, portas, nomes de container/recurso, estrutura de pastas.
Usar só o que está no repositório, no `projeto.md`, ou o que o owner disser explicitamente.

**Why:** no `/mss-spec:kickoff` do projeto do painel de atas, o comando chutou o path
`/mnt/f/Deploy/IaBotAgent` numa opção (A) — caminho que não existia. O owner (engenheiro sênior,
avesso a vibecoding) teve que corrigir na mão e reclamou ("ficou bem fora"). Um valor concreto errado
é pior que uma lacuna, porque parece verdade.

**How to apply:** quando não tiver o valor verificado, deixe genérico ("um diretório de deploy", "o
host do Postgres"), marque `<a confirmar>`, ou pergunte. Vale pra entrevistas de kickoff, specs, e
qualquer resposta. Já embutido como regra no `commands/kickoff.md` e no `templates/CLAUDE.md` do plugin
mss-spec. Relacionado a [[project-memoria-local-ao-repo]] (mesmo repo/plugin).
