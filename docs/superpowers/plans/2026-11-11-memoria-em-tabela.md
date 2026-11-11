# Memória em tabela — parte 1 (a tabela) — plano curto

> Nível **médio** do kit: plano em tópicos, execução inline com TDD (teste → vermelho → código → verde), sem
> subagentes. Spec: `docs/specs/memoria-em-tabela.md`. Dossiê e régua:
> `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`.

**Objetivo:** um comando do kit que monta, a partir dos arquivos do projeto, uma tabela SQLite local única —
cópia para busca; o arquivo no git segue sendo o original.

**Arquitetura:** um script novo, `templates/memoria_tabela.py`, só com a stdlib (`sqlite3`, FTS5), que reusa o
parse de `templates/memoria_indice.py` (`frontmatter`, `corpo`, `RE_ITEM`, `RE_LINHA_DIARIO`). Uma tabela FTS5
`memoria`; a assinatura de cada arquivo fica na própria linha (sem tabela de controle). Chamado pelo
`/mss-spec:memory tabela`.

## Restrições
- Só stdlib; nada de dependência nova. Chamada ao git em **bytes** com `-z` (memória
  `project_subprocess_texto_windows_quebra_git`), sempre com `timeout`, e falha do git nunca derruba o `montar`.
- Só lê o projeto; grava só no arquivo da tabela. Nunca grava dentro de `.claude` nem de um repo.
- Arquivos do kit são CRLF; texto com acento vai por Write/Edit, nunca por heredoc.
- Versão igual nos dois manifestos (`.claude-plugin/plugin.json` e `marketplace.json`): 0.55.0.

## Interface (`templates/memoria_tabela.py`)
- `caminho_tabela() -> Path` — `MSS_MEMORIA_TABELA` ou `Path.home() / "mss-spec" / "memoria.sqlite3"`.
- `nome_projeto(raiz: Path) -> str` — título do `CLAUDE.md` antes de " — "; senão o nome da pasta.
- `arquivos_do_projeto(raiz: Path, usar_git: bool = True) -> list[Path]` — `.md`/`.html` de `memory/`, `docs/`,
  `to-dolist.md`, `projeto.md`; com git, só o que `git ls-files -z --cached --others --exclude-standard` lista.
- `linhas_do_projeto(raiz: Path, usar_git: bool = True) -> list[dict]` — chaves `projeto, raiz, tipo, classe, arq,
  ponteiro, data, dono, assinatura, titulo, quando, resumo, texto`. `tipo` ∈ `anotacao, diario, decisao, falha,
  spec, plano, mapa, documento`.
- `montar(raiz: Path, tabela: Path | None = None, usar_git: bool = True) -> Resultado` — `Resultado(tabela,
  projeto, por_tipo: dict, novos: int, refeitos: int, removidos: int, iguais: int, pendencias: list[str])`
  (contagens em **arquivos**).
- `status(raiz: Path, tabela: Path | None = None, usar_git: bool = True) -> Situacao` — `Situacao(existe: bool,
  linhas: int, mudaram: int, mensagem: str)`.
- CLI: `memoria_tabela.py montar|status|onde [--proj DIR] [--tabela ARQ] [--sem-git]`; exit 1 quando a tabela
  falta ou está desatualizada no `status`.
- Esquema: `PRAGMA user_version = 1`; versão diferente → apaga e refaz (é cópia).

## Tarefas
1. **Onde fica + esquema** — testes: caminho padrão fora de `.claude`; variável troca; `montar` cria a pasta; versão
   de esquema diferente refaz. Código: `caminho_tabela`, abrir/criar a tabela.
2. **Ler o projeto** — testes: cada fonte vira linha com o tipo certo; frase do subíndice em `quando`; linha do
   `DIARIO.md` em `resumo`; documento por seção com `arquivo:linha`; `.html` sem tags; `<private>` fora; `.env`,
   `.txt` e ignorado pelo git fora; nome do projeto pelo `CLAUDE.md`. Código: `arquivos_do_projeto`,
   `linhas_do_projeto`.
3. **Montar e remontar** — testes: mudar um arquivo refaz só ele; apagar tira; dois projetos na mesma tabela;
   mudar o subíndice refaz a anotação; `SELECT` por projeto/tipo/data e `MATCH` funcionam. Código: `montar`.
4. **Git: dono, data e pendências** — testes com `git init` de verdade em `tmp_path`: data e dono da criação;
   arquivo não commitado aparece em `pendencias`; projeto sem git segue sem erro. Código: leitura do `git log`.
5. **`status` e CLI** — testes: tabela ausente → exit 1 com o comando de remontar; desatualizada → conta os
   arquivos; `onde` imprime o caminho; rodar a CLI **com os padrões** (memória
   `project_rode_a_peca_com_os_padroes_antes_de_dizer_pronto`).
6. **Ligar ao kit** — `commands/memory.md` (modo `tabela`), `docs/LEIA-ME.md`, `CHANGELOG.md`, versão 0.55.0 nos
   dois manifestos, procedimento na memória do kit (trocar de máquina) + subíndice, smoke de wiring.
7. **Conferência real** — `montar --sem-git --tabela <temporária>` nos 4 projetos, só leitura; comparar com os
   3.046 trechos do teste de mesa. Suíte inteira; baseline.

## O que os testes não cobrem sozinhos (atenção na revisão)
- Arquivo com bytes fora de UTF-8 → lê com substituição, nunca levanta.
- Dois projetos com o mesmo nome de pasta → a chave é a `raiz`, não o nome.
- Tabela aberta em outro programa (DBeaver) durante o `montar` → erro claro, sem corromper.
- Projeto enorme: documento acima de 1,5 MB é pulado e listado.
- Caminho com espaço e acento (`IA Bot Agent - Whats`).
