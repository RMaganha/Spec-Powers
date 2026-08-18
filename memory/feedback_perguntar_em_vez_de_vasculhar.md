---
name: feedback-perguntar-em-vez-de-vasculhar
description: Falta um fato concreto que o owner tem na cabeça (caminho, nome de container/variável, qual arquivo é o compose)? Perguntar na hora — nunca varrer o disco
gatilho: quando faltar um fato concreto que o owner tem na cabeça
metadata:
  node_type: memory
  type: feedback
---

Quando falta um fato concreto que **o owner tem na cabeça** — onde vive um projeto/pasta/container, o
nome exato de uma variável de ambiente ou chave, qual arquivo é o compose de tal serviço — a ação é
**perguntar, curto e na hora**. Nunca varrer o disco (`find`/`ls`/`Glob` entrando em repositório atrás
de repositório, `grep` em `C:\`). Busca só **depois** que ele não souber, ou pra confirmar algo que ele
já apontou. Vale igual pra fato que estaria na web ou num sistema.

**Why:** ele sabe o caminho na hora, e procurar é o pior dos mundos: lento, ruidoso, queima tokens e
ainda termina em chute. Reclamado **duas vezes**, com as palavras dele: *"não deveria ficar pesquisando
e sim perguntar!!!"* (2026-07-24, o projeto de leads estava em `Energy`, não onde eu procurava) e
*"estava a 5 minutos gastando tokens a toa para tentar achar!!"* + *"não é para investigar, me
pergunte"* (2026-07-30, procurando o `evolution-go` e o compose dele em outro projeto). A segunda vez
aconteceu porque este aprendizado morava **só** na pasta volátil `~/.claude/projects/<proj>/memory/` —
não viajava pra outro projeto. Por isso a regra virou item do **`templates/CLAUDE.md`** (que o kit copia
pra todo projeto): memória de um projeto não protege os outros.

**How to apply:** uma linha, direta: "onde fica X nesta máquina?" / "qual o nome exato da variável?" —
e espere. Não encadeie três comandos de busca "só pra tentar". Se o assunto é outro projeto, junte as
perguntas numa só mensagem (caminho + nome do container + qual compose) em vez de descobrir aos poucos.
Parente de [[feedback-nao-inventar-fatos-concretos]] (não chutar o valor) e de
[[feedback-projeto-ativo-read-only]] (achar o outro projeto é só o começo: lá dentro, só leitura).
