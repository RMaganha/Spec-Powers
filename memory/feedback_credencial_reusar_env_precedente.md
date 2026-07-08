---
name: credencial-reusar-env-precedente
description: Nunca pedir ao owner credencial que já existe no .env local de projeto precedente — copiar de lá; e porta do SQL Server real é 1435 (jedai), não 1433
metadata:
  type: feedback
---

O owner reclamou (2026-07-08, sessão MSS-SSC): o assistente criou `.env` e pediu usuário/senha do
SQL digitados — mas o jedai (`C:\Ronaldo\_Mitsui\Python\IA Jeday Cosseguro\Azure\.env`,
`SQL_CONNECTION_STRING_SSC`) já conecta no mesmo servidor há muito tempo. "Lá já tem tudo!!!"

**Why:** a credencial já existe na máquina, local e funcionando; pedir digitação é atrito inútil e
convida erro de digitação. Além disso o AMBIENTE.md afirmava "porta 1433" sem verificação — o jedai
real usa `Server=10.170.210.36,1435`. Fato não-verificado no doc = [[nao-inventar-fatos-concretos]].

**How to apply:** antes de pedir credencial, procurar projeto precedente que conecta no mesmo
servidor (precedentes/referencia-*.md) e propor copiar o valor do `.env` local ajustando só
`Database=`. Nunca ecoar o valor no chat, nunca commitar. Confirmar host/porta com o `.env` que
funciona, não com suposição. Fora da rede corporativa (sem VPN), erro 53/timeout é rede — não mexer
em credencial por causa disso. Codificado em: commands/banco.md, templates/AMBIENTE.md §4, skill
precedentes-msig (v0.3.2).
