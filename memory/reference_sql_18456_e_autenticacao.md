---
name: reference_sql_18456_e_autenticacao
description: Erro 18456 do SQL Server = a conexão chegou ao servidor e só a autenticação falhou — mexer em porta ou rede não resolve; confira usuário e senha
gatilho: quando a conexão com o SQL Server falhar com o erro 18456
conferida: 2026-11-16 — confirmada — fonte: memory/sessions/2026-07-08-review-do-kit-banco-e-front-mantine.md:20
metadata:
  type: reference
---

O erro **18456** ("Login failed for user") só sai quando a conexão **já chegou** ao SQL Server: rede, porta e
servidor estão certos; falhou a autenticação. Trocar porta ou mexer em rede não resolve — confira usuário, senha e
base com o owner.

**Por que está aqui:** no MSS-SSC (2026-07-10) o assistente testou outras portas mesmo com o owner dizendo "porta
padrão"; a causa era a credencial (memory/sessions/2026-07-08-review-do-kit-banco-e-front-mantine.md:20). Erro 53 ou
timeout, ao contrário, é rede ([[credencial-reusar-env-precedente]]). Fato dito pelo owner não se re-litiga
([[feedback_diagnostico_disciplinado]]).
