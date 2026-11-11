# Ajudante pesquisador — plano curto (cerimônia média)

**Objetivo:** um ajudante do kit que lê muito na janela dele e devolve só o resumo.
**Spec:** `docs/specs/ajudante-pesquisador.md`. **Execução:** nesta conversa, uma tarefa por vez, teste antes do código.
**Regras que valem em tudo:** nada do MSIG_Agentes; o ajudante só lê; nada de comando para o owner lembrar;
versão igual nos dois manifestos; suíte inteira verde antes de dizer pronto.

## Tarefa 1 — o ajudante e onde a regra aparece (critérios 2, 3 e 5)
- Teste: `tests/test_ajudante_pesquisador.py`
  - `agents/pesquisador.md` existe; cabeçalho com `name: pesquisador`, `description`, `tools: Read, Grep, Glob`,
    `model: inherit`; sem `hooks`, `mcpServers`, `permissionMode`, `initialPrompt`;
  - a descrição diz os três casos e que não é para toda tarefa; o corpo traz o formato da resposta
    (primeira linha, `arquivo:linha`, o que não leu, 3.000 letras, não grava);
  - a linha "Bola de neve" de `templates/regras-do-kit/1-modo-de-trabalho.md`, `commands/to-dolist.md`,
    `commands/nova-feature.md` e o aviso de `hooks/alerta_contexto.py` nomeiam `mss-spec:pesquisador` (e mantêm
    a palavra "subagente", que outros testes cobram);
  - as portas `tarefa`, `bug` e `duvida` têm o passo **1b** com os três casos e o comando do script.
- Código: criar `agents/pesquisador.md`; editar os cinco textos e as três portas; regenerar
  `templates/regras-do-kit/linhas-do-kit.txt` com `python templates/migrar_claude_md.py historico`.
- Conferir: o teste novo, `tests/test_orcamento_contexto.py`, `tests/test_migrar_claude_md.py`,
  `tests/test_hook_alerta_contexto.py`, `tests/test_smoke_kit.py`.

## Tarefa 2 — outra conversa em texto (critério 4)
- Teste: `tests/test_conversa_texto.py`, com uma conversa de exemplo gravada em `tmp_path`.
  - `falas(arquivo) -> list[Fala]` (`quem` = `OWNER` ou `ASSISTENTE`, `quando`, `texto`, `gravou`): fora o
    resultado de ferramenta, a fala de ajudante (`isSidechain`), o registro `isMeta`, o raciocínio do assistente
    e o trecho `<private>`; o texto colado pelo owner fica; arquivo gravado pelo assistente vira `gravou`;
  - `gravar_texto(arquivo, pasta_saida) -> Path`: `<pasta>/<id>.txt`, cabeçalho + falas numeradas;
    conversa sem fala nenhuma não grava e devolve `None`;
  - `listar(pasta, quantas) -> list[Resumo]`: mais nova primeiro, com data, tamanho, id e o primeiro pedido;
  - `achar(pasta, pedaco) -> list[Path]`: pelo começo do id, por caminho, ou por palavra do primeiro pedido;
  - linha de comando: `listar` e `texto <id|caminho|palavra>`; mais de uma conversa casando → lista e sai com 1;
    nenhuma → sai com 1; pasta das conversas não achada → sai com 2 e pede `--pasta`;
  - a pasta de saída vem de `MSS_CONVERSAS_DIR` (padrão `~/mss-spec/conversas`), e a suíte desvia no `conftest.py`;
  - linha torta no `.jsonl` e arquivo que não abre não derrubam.
- Código: `templates/conversa_texto.py`.

## Tarefa 3 — versão e documentos
- `0.58.0` em `.claude-plugin/plugin.json` e `marketplace.json`; `CHANGELOG.md`; `docs/LEIA-ME.md`;
  spec ("Estado atual" como ficou); `docs/superpowers/INDEX.md` e `MAPA.md`.

## Tarefa 4 — conferir
- Suíte inteira; conferência no real (o ajudante aparece numa conversa nova — só o owner vê; nesta conversa, uma
  pesquisa por caso com o texto do ajudante entregue a um ajudante genérico, dita como aproximação).

## Onde olhar com mais cuidado na revisão
- conversa com fala só de comando do kit (`<command-args>`): o pedido tem de aparecer;
- `.jsonl` com linha de centenas de milhares de letras (resultado de ferramenta): ler linha a linha, sem carregar tudo;
- duas conversas com o mesmo começo de id; conversa em curso (a própria) aparecendo na lista;
- segredo digitado pelo owner numa conversa: o texto fica só na máquina, fora do repositório;
- descrição do ajudante vaga a ponto de o assistente chamá-lo em toda tarefa.
