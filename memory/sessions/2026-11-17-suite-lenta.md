# 2026-11-17 — suíte lenta: só o teste do que mudou, pasta por projeto, uma rodada por vez (0.65.0)

## Conversamos
O owner abriu `/mss-spec:bug`: a suíte do kit deixava a máquina lenta, travava o Claude Desktop e deixava algo
rodando depois de interrompida. A mesma suíte levou 2379.61s e 517.74s; uma rodada interrompida deixou o pytest
vivo (PID 31512). O kit é usado em todos os projetos do owner (ATM Transporte, Atendimento WhatsApp, mss-utils e
outros), e o mesmo comportamento se repete neles, pior por serem maiores.

## Pivôs
- **A máquina está OK.** O assistente atribuiu a lentidão à máquina, ao antivírus e a uma instalação da Dell. O
  owner: a TI e o suporte da Dell não acharam nada anormal, e a Dell foi coincidência. O foco passou para a suíte.
- **O lixo do pytest só acumula.** Toda rodada, de qualquer projeto, grava na mesma pasta do usuário
  (`pytest-of-<usuário>`); a rodada interrompida deixa `.lock` e o pytest só apaga essa pasta depois de 3 dias.
  Havia 6 pastas travadas (cerca de 3 mil pastas); apagar levou 991s.
- **"Você não está vendo como um todo."** O assistente focou no git dos testes do kit; o owner cobrou a visão
  geral. A causa geral: a regra 9 do kit, somada ao TDD, rodava a suíte inteira a cada ajuste em todo projeto, e o
  kit não levava configuração de pytest nenhuma aos projetos.
- **12 mil arquivos:** não são arquivos dos projetos; são os projetos de mentira que cada um dos 1211 testes monta.
  Um repositório de teste com 1 commit cria 41 itens, ou 23 com `git init --template=`.

## Rejeitado
Pasta temporária dentro do repositório (o editor e o Claude Desktop acompanham a pasta do projeto); marker `lento`
para separar a suíte (a regra "só o teste do que mudou" já resolve); rodar a suíte inteira só para medir o antes.

## Fizemos
- Regra 9 e os comandos `bug`, `nova-feature`, `plano-teste`: durante o trabalho só o teste do que mudou; a suíte
  inteira uma vez, antes do merge, nunca antes do OK; uma rodada de pytest por vez.
- `templates/pytest/conftest.py` e `pytest.ini`, levados pelo `kickoff` e pelo `upgrade`: pasta
  `<temp>/pytest-<projeto>` e trava do sistema operacional que morre com o processo. O kit usa o próprio molde.
- Suíte do kit em camadas: `test_hook_outro_projeto_shell.py` ~422s → 13.74s; `test_converter_to_dolist.py`
  ~231s → 70.65s; repositório montado uma vez por arquivo onde só se lê; todo `git init` com `--template=`.
- 2 linhas em `docs/decisoes.md`; `tests/test_pytest_mss.py` (9) e `tests/test_smoke_kit.py` (+1).

## Próximo
Suíte inteira verde, commit da parte 3 e merge com a aprovação do owner; push é do owner. Em cada projeto, o
`/mss-spec:upgrade` leva o molde, e a suíte de cada projeto grande se reorganiza na conversa dele.
