---
name: project_kit_nao_assume_ambiente_de_origem
description: O kit nasceu na MSIG e tratava a infra corporativa como universal — a correção é PERGUNTAR na constituição e gravar a resposta no CLAUDE.md, não detectar
gatilho: quando o kit for gravar algo sobre infra (rede, proxy, CA, banco corporativo)
metadata:
  type: project
---

Todo molde que nasce dentro de um ambiente tende a **confundir "onde nasci" com "como é"**. O
mss-spec fazia isso com a infra MSIG: copiava a CA do FortiGate, o `docker-compose.office.yml` e o
proxy pro `.env` de **qualquer** projeto, oferecia o `get_connection.py` das bases corporativas, e o
`doctor` cobrava proxy/CA/rede `mitiai_network` — que num projeto de fora simplesmente não existem.
O owner tem projetos que não são MSS; lá isso era editado à mão a cada rodada, e o `upgrade`
reintroduzia.

**Why:** o custo não é só ruído. Check que cobra infra inexistente **treina o owner a ignorar o
doctor** (o ✗ perde significado), e molde reintroduzido a cada `upgrade` desfaz a decisão do
projeto em silêncio.

**How to apply:** quando uma parte do kit depende do ambiente (rede, proxy, certificado, banco
corporativo, nuvem), a resposta é **perguntar uma vez na constituição** (`/mss-spec:kickoff`) e
gravar a declaração na linha `**Infra:**` do Contexto do `CLAUDE.md` — que já está em contexto em
toda sessão, então os comandos leem sem procurar e **nenhum formato de configuração novo** entra.
Duas contrapartidas obrigatórias, aprendidas nesta rodada:
1. **quem sobrescreve tem que respeitar a declaração** — a categoria 1 do `upgrade` reintroduziria
   tudo; e
2. **projeto anterior à mudança recebe a linha PERGUNTANDO** (`<MSIG | própria — a confirmar>`),
   nunca com o default antigo assumido em silêncio — assumir é o erro que se está consertando.

Nunca **detectar** o ambiente por heurística (nome do projeto/pasta): é pergunta ao owner.

Relacionado: [[feedback_regra_unica_em_vez_de_config]] (declaração no que já existe, em vez de
formato novo), [[project_upgrade_categoria1_sobrescreve]] (a categoria que precisa do freio) e
[[feedback_brownfield_entender_nao_aplicar]] (não aplicar molde por cima do que o projeto já é).
