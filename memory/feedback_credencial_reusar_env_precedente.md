---
name: credencial-reusar-env-precedente
description: Padrão canônico de conexão SQL = get_connection.py multi-ambiente do Transportes V2 — credencial cifrada NO CÓDIGO, .env só com o seletor de ambiente; nunca pedir credencial digitada
metadata:
  type: feedback
---

Dois feedbacks do owner na mesma frente (2026-07-08, sessões MSS-SSC):
1. O assistente criou `.env` e pediu usuário/senha digitados — mas a credencial já existia na
   máquina. "Lá já tem tudo!!!"
2. Pior: credencial **não era pra estar no `.env`** de jeito nenhum. "Eu no `.env` no máximo coloco
   o ambiente!" O padrão canônico da casa é
   `C:\Ronaldo\_Mitsui\Python\Transportes\V2\get_connection.py`: par Fernet KEY/CIPHERTEXT **por
   base e por ambiente** (DEV/D0 · HML/HI · PROD) embutido no próprio arquivo; `.env` só carrega
   `CONEXAO_SQL` (D0|HML|PRD) + `CONEXAO_SQL_PORTA` (opcional; vazio = porta padrão). Comentário
   no `.env` SEMPRE em linha própria — inline o Docker Compose passa junto do valor e quebra.

**Why:** credencial em texto plano no `.env` circula e vaza; pedir digitação é atrito e erro. O
arquivo do Transportes já tem os pares prontos das bases corporativas (SSC, MS10=`tkgs_corp`, TRP,
OnBase) e os helpers (mask_password, Encrypt/timeout, logging). Fatos verificados por decriptação
local: SSC dev `10.170.210.36,1435`; `tkgs_corp`/`MSS_TRP` dev sem porta explícita; SSC prod
`10.170.210.48`; instâncias 1434/1435 (owner). E o AMBIENTE.md afirmava "porta 1433" sem verificar
— [[nao-inventar-fatos-concretos]].

**How to apply:** conexão SQL nova = copiar `templates/get_connection.py` do kit (v0.4.0) e
preencher pares: base conhecida → apontar as constantes no Transportes V2 pro owner colar (copiar
credencial entre projetos é decisão DELE — classifier bloqueia e com razão); base nova → gerar par
localmente por script, sem ecoar segredo no chat. Nunca deixar conn string em texto plano em .env,
código ou chat (usar mask_password). Erro 53/timeout fora da rede corporativa é rede, não
credencial. Codificado em: banco.md, AMBIENTE §4, precedentes, templates/get_connection.py.
