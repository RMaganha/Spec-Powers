# Memória em tabela, parte 2 — plano (2026-11-11)

**Objetivo:** a busca usa a tabela e a tabela se atualiza sozinha, sem comando pra lembrar.
**Spec:** `docs/specs/memoria-em-tabela.md` (decisões 13 a 22; critérios de aceite 10 a 19).
**Nível:** médio — execução nesta conversa, um teste antes de cada pedaço de código.
**Branch:** `feature/memoria-em-tabela-parte-2`. **Versão:** 0.56.0 nos dois manifestos.

## Regras que valem para todas as tarefas
- O script só lê o projeto e só grava a tabela. A suíte nunca toca a tabela real (`MSS_MEMORIA_TABELA` desviado
  no `tests/conftest.py`).
- Hook nunca bloqueia e falha aberta (defeito → sai calado, código 0). Nada de PowerShell, tarefa agendada ou
  processo solto (`docs/decisoes.md`, 2026-11-03).
- Os hooks só entram no `hooks/hooks.json` na tarefa 4, com a suíte verde: o kit vale ao vivo nos outros
  projetos pela junção.
- Dado gerado a partir de outros projetos fica fora do repositório (roteiros copiados pra pasta temporária).

## Arquivos
| Arquivo | O que muda |
|---|---|
| `templates/memoria_tabela.py` | esquema 2 (linha de controle); `atualizar`; `buscar`; `pedidos_da_conversa`; `formatar`; modo `buscar` na linha de comando |
| `hooks/memoria_tabela_em_dia.py` (novo) | abertura da conversa e depois de gravar → `atualizar` |
| `hooks/hooks.json` | registra o hook novo em `SessionStart` e `PostToolUse` (tarefa 4) |
| `tests/test_memoria_tabela.py` · `tests/test_hook_memoria_tabela_em_dia.py` (novo) · `tests/conftest.py` | os testes |
| `commands/tarefa.md` · `bug.md` · `duvida.md` · `memory.md` | passo de memória usa o `buscar`; modo `tabela` some da descrição |
| `docs/analise/2026-11-10-teste-de-mesa/regua_parte2.py` (novo) | a régua medindo o código entregue |
| `hooks/README.md` · `docs/LEIA-ME.md` · `CHANGELOG.md` · `docs/decisoes.md` · `docs/EVALS.md` · manifestos · `memory/project_remontar_a_tabela_de_memoria.md` | documentação e versão |

## Tarefas

- [x] **1. Conferência rápida e `atualizar`** (critérios 12 e 18)
  - `assinatura_do_disco(raiz) -> str`: nome, tamanho e data de cada `.md`/`.html` de `memory/`, `docs/` e dos
    soltos, sem ler conteúdo e sem git.
  - Esquema 2: uma linha `tipo = 'controle'` por projeto guarda essa assinatura (dentro da mesma tabela; a
    busca e a contagem por tipo a ignoram).
  - `atualizar(raiz, tabela=None, usar_git=True) -> Resultado | None`: `None` quando nada mudou; senão `montar`.
  - `montar` deixa de chamar o `git log` quando não há arquivo novo (reaproveita dono e data das linhas
    antigas) e só calcula pendências quando pedido.
  - Testes: nada mudou → não lê arquivo nem chama git (contador); arquivo mudado, novo e apagado → atualiza;
    tabela ausente → monta; linha de controle não aparece em `por_tipo`.

- [x] **2. `buscar` e `formatar`** (critérios 11, 15, 16)
  - `buscar(raiz, texto, contexto=(), tabela=None, limite=30, sem_tipos=()) -> list[dict]` — palavras pela
    regra do teste de mesa (palavra de mais de 6 letras casa pelo começo; pesos título 3, quando usar 4,
    resumo 2, texto 1), só as linhas da raiz, um arquivo por linha.
  - `formatar(achados) -> str`: blocos "Anotações" e "Documentos"; linha = `tipo | ponteiro | título (80) | trecho (170)`.
  - Testes: 40 arquivos → 30 linhas de 30 arquivos; dois blocos; outro projeto não aparece; pedido sem palavra
    útil → lista vazia; tabela ausente → erro tratado.

- [x] **3. Contexto da conversa e modo `buscar` da linha de comando** (critérios 11, 14, 18)
  - `pedidos_da_conversa(arquivo, quantos=4, teto=600) -> list[str]`: os últimos pedidos do owner, do mais
    antigo pro mais novo, com o mesmo filtro do garimpo do teste de mesa.
  - `arquivo_da_conversa(ambiente) -> Path | None`: pelo `CLAUDE_CODE_SESSION_ID`, em `<pasta do app>/projects/*/`.
  - `python memoria_tabela.py buscar [texto] [--conversa ARQ] [--sem-contexto] [--limite 30]`: atualiza, busca,
    imprime. Sem texto → último pedido + 3 anteriores. Com texto → só o texto. Códigos: 0 achou · 1 nada (diz o
    caminho dos arquivos) · 2 tabela indisponível (idem).
  - Testes: conversa com 5 pedidos → usa os 4 últimos, cortados em 600; sem arquivo de conversa → só o texto;
    códigos de saída; arquivo mudado por fora aparece na busca.

- [x] **4. Hook `memoria_tabela_em_dia.py`** (critérios 10 e 12)
  - `SessionStart`: `atualizar`; tabela montada do zero → uma linha só pro assistente; em dia → silêncio.
  - `PostToolUse` (Write/Edit/MultiEdit): age só se o arquivo gravado é `.md`/`.html` de `memory/`, `docs/`,
    `to-dolist.md` ou o arquivo de base da raiz do projeto da janela; silêncio sempre.
  - Projeto sem `memory/` → nada. Escape: `MSS_MEMORIA_TABELA_OFF=1`.
  - Testes: os dois eventos, o silêncio, arquivo fora do alcance, falha aberta (tabela presa), escape.
  - Por último: registrar no `hooks/hooks.json` + teste que confere o registro.

- [x] **5. Portas, `memory` e documentos** (critérios 13 e 17)
  - `commands/tarefa.md`, `bug.md`, `duvida.md`: o passo de memória manda rodar o `buscar`, ler as linhas e
    abrir só o que serve; reserva = `MEMORY.md` → subíndice e procura nos arquivos.
  - `commands/memory.md`: `buscar` usa a tabela; `tabela` sai da descrição e do `argument-hint` (texto fica
    como uso interno).
  - Testes de prosa (um por comando) + `hooks/README.md`, `docs/LEIA-ME.md`, procedimento de troca de máquina.

- [x] **6. Régua** (critério 19)
  - `regua_parte2.py`: monta uma tabela temporária com os 4 projetos (`--sem-git`, só leitura neles) e mede,
    com o `buscar` entregue, K1, K2 e K3 (1º, até 3, até 10, até 30), ao lado do jeito de hoje nos mesmos casos;
    e, por projeto, "entre os 3 primeiros" hoje × tabela (o aviso automático).
  - Rodar `mesa2.py garimpar` numa cópia na pasta temporária; colar a saída; registrar os números na spec
    ("Conferido no real") e no dossiê.

- [x] **7. Fecho**
  - Suíte inteira (`python -m pytest tests/ -q`), `CHANGELOG.md`, 0.56.0 nos dois manifestos, decisão em
    `docs/decisoes.md`, F-057 fechado no `docs/EVALS.md`, revisão do código, `plano-teste`, `release`, captura
    (com o OK do owner), MAPA e INDEX.

## O que olhar na revisão
- Duas conversas no mesmo projeto ao mesmo tempo: a tabela presa por uma não pode travar nem derrubar a outra.
- Arquivo ignorado pelo git muda a assinatura do disco mas não entra na tabela: não pode virar remontagem a
  cada conferência.
- Pedido só com palavras curtas ou só com símbolos: busca vazia, sem erro de sintaxe na consulta.
- Conversa sem arquivo (variável ausente, pasta do app em outro lugar): busca só com o texto, sem erro.
- Projeto sem `memory/` ou fora do git: o hook não cria linha nenhuma e não fala.
