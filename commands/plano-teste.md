---
description: Roda o plano de teste base (pytest) e, se passar 100%, grava/atualiza o baseline em docs/superpowers/PLANO-TESTE.md
argument-hint: ""
disable-model-invocation: true
---

Você vai rodar/atualizar o **plano de teste base** deste projeto — a rede anti-regressão ("se isso passa 100%, nada quebrou"). O baseline vive em `docs/superpowers/PLANO-TESTE.md`.

1. **Se não existir suíte (`tests/`) nem `docs/superpowers/PLANO-TESTE.md`:** crie um plano MÍNIMO (smoke) com pytest — ex.: o app importa/sobe, os endpoints-chave respondem 200, a conexão de banco abre (use os padrões do projeto; consulte `docs/AMBIENTE.md`). **UI entra como teste de rota** (`TestClient`: a rota renderiza 200 com os elementos esperados), nunca como clique ao vivo. Siga `superpowers:test-driven-development` e **confirme comigo antes de gravar testes novos**.
2. **Rode a suíte:** `pytest -q` (ou o runner do projeto). **Cole a saída real** — `superpowers:verification-before-completion`, nunca afirme sem a saída.
3. **Se 100% verde:** grave/atualize `docs/superpowers/PLANO-TESTE.md` como o novo baseline, contendo:
   - o comando para rodar (ex.: `pytest -q`);
   - a lista do que o baseline cobre (1 linha por área/teste);
   - o carimbo do último 100%: data + commit (`git rev-parse --short HEAD`).
   O conteúdo anterior é **substituído** (o git guarda o histórico). Commit: `test: atualiza plano de teste base (baseline verde)`.
4. **Se NÃO passar 100%:** reporte exatamente o que falhou e **NÃO** atualize o baseline — o `PLANO-TESTE.md` anterior continua sendo a base válida. Corrija (ou me traga o diagnóstico) antes de regravar.

Regra de ouro: o baseline só é atualizado com a suíte **100% verde**. Nunca promova a base algo que não passou inteiro.

## Validação de UI/tela — SÓ determinística (nunca o agente clicando ao vivo)
Tela se valida por **teste automatizado**, não mandando o assistente dirigir o browser:
- **Rotas via `TestClient`** (parte do `pytest`): a rota responde 200 e o HTML traz os elementos esperados (dropdown, botão, tabela). É o padrão e cobre a maioria dos casos.
- **E2e real (só se indispensável):** um **teste Playwright roteirizado com asserts**, também dentro do `pytest` — alvo por **`data-*`/nome acessível** (nunca coordenada), com asserção explícita de resultado. É código versionado e repetível, não uma sessão de cliques.
- **PROIBIDO:** o assistente validar tela clicando/tirando screenshot ao vivo em loop. Foi o que travou o MSS-SSC — sem seletor estável ele **clica errado**; em fluxo destrutivo (criar→excluir→recriar) **desfaz e refaz**; e sem critério observável **julga como falha algo que passou**, entrando em loop.
- **"Smoke manual"** no `PLANO-TESTE.md` é roteiro para **👤 humano** (marque-o assim explicitamente) — descreve passos e o que conferir no banco/tela; **não é tarefa do assistente**. O assistente só o cita, não o executa.

## Sobre invocação
Este comando é **`disable-model-invocation`**: só **você** o dispara (`/mss-spec:plano-teste`), pra (re)gravar o baseline. O assistente, quando precisa **verificar** antes de declarar algo pronto, **roda o comando de teste do `PLANO-TESTE.md` direto** (ex.: `python -m pytest -q`) e cola a saída — ele **não** tenta invocar este comando (dá erro de invocação).
