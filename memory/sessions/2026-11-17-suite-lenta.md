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

- Virada do fim da conversa: o owner cobrou que rodar o teste do bpmn quando a mudança foi na memória não faz
  sentido. Na máquina, os testes passam a ser escolhidos pelo `templates/testes_do_que_mudou.py`; a suíte inteira
  roda no GitHub Actions (`.github/workflows/testes.yml`), que substituiu o GitLab CI nunca ativado.
- No Linux do GitHub a suíte inteira levou 25 a 32 s (na máquina do owner, 517 a 2379 s). O CI achou 2 testes que
  só passavam na máquina do owner (caminho `C:/...`; citação de `~/...` e de arquivo gerado fora do git);
  consertados, CI verde no commit `b3c2b2d`.
- Rejeitado: login no navegador embutido para ler o log do CI (o painel não ficou logado); o CI publica a lista das
  falhas numa anotação, que a API pública mostra.

- Revisão arquivo por arquivo (56 arquivos, cerca de 900 pastas por rodada) aprovada pelo owner: grupo 1 (travas)
  e grupo 2 (ferramentas) a reescrever; grupo 3 cortado — 108 testes de frase em `.md`. Ficaram os que pegam quebra
  real e os 15 que guardam caso do `docs/EVALS.md` (rejeitado: cortá-los, deixaria os casos sem guarda). Merge
  `a5549da` na `main`, CI da `main` verde.
- Escopo seguinte, definido pelo owner, cada um em conversa nova com o texto pronto: Parte 3 (suíte em camadas),
  molde de CI padrão para os projetos grandes, custo dos hooks num projeto grande (ele tem como testar).

## Próximo
Merge na `main` com a aprovação do owner; push é do owner. Reescrever os ~50 arquivos de teste antigos (a regra
testada em memória, sem pasta; disco só no teste da leitura) — até lá eles não rodam na máquina, só no CI. Em cada
projeto, o `/mss-spec:upgrade` leva o molde, e a suíte de cada projeto grande se reorganiza na conversa dele.
