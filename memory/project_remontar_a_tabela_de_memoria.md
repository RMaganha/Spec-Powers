---
name: project-remontar-a-tabela-de-memoria
description: Passo a passo pra remontar a tabela local de memória (cópia SQLite em ~/mss-spec/) quando trocar de máquina, a tabela sumir ou o status acusar
gatilho: quando trocar de máquina, reinstalar o Windows ou o app, a tabela de memória sumir, ou o `memoria_tabela.py status` disser que ela não existe ou está desatualizada
metadata:
  type: procedimento
---

A tabela de memória (`~/mss-spec/memoria.sqlite3`) é **cópia pra busca**; os originais são os arquivos de cada
projeto, no git. Por isso ela nunca precisa de backup: some, remonta. Decisão do owner em 2026-11-11: fora do
`.claude` ("qualquer alteração perde") e fora da pasta do kit (o kit é publicado; a tabela guarda o conteúdo de
todos os projetos). Spec: `docs/specs/memoria-em-tabela.md`.

**Desde a 0.56.0 a tabela se atualiza sozinha** (abertura da conversa, depois de gravar e antes de cada busca):
no dia a dia não há nada pra rodar, e numa máquina nova basta **abrir uma conversa em cada projeto** — a tabela é
montada na hora. Os passos abaixo ficam pra quando isso não bastar (tabela que não se monta, conferência à mão) e
pra tratar as pendências de publicação, que só o `montar` mostra.

**Passos:**
1. Baixar (clonar) cada projeto na máquina nova — quem: owner — como: `git clone` de cada um, como sempre; sem os
   projetos não há o que montar.
2. Conferir onde a tabela vai morar — quem: assistente — como:
   `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_tabela.py" onde`; tem de ser fora do `.claude` e fora de
   repositório. Outro disco ou pasta → o owner define a variável `MSS_MEMORIA_TABELA` no Windows.
3. Em **cada** projeto, na janela dele, montar — quem: assistente (ou o owner no terminal) — como:
   `python "${CLAUDE_PLUGIN_ROOT}/templates/memoria_tabela.py" montar`; um projeto não lê o outro, então é um
   `montar` por projeto. Para se a saída trouxer erro de abrir/gravar a tabela.
4. Colar a saída de cada `montar` — quem: assistente — como: tabela, arquivos novos, linhas por tipo e pendências.
5. Tratar as pendências — quem: owner — como: "arquivo ainda não commitado" e "commit ainda não publicado" são
   memória que **só existe naquela máquina**; commit é do assistente com o OK dele, publicar é ato do owner.

**Ferramentas:** `templates/memoria_tabela.py` (`onde` · `status` · `montar` · `buscar`); o texto "Uso interno:
tabela" do `commands/memory.md` (não é modo do owner); hook `hooks/memoria_tabela_em_dia.py`.

**Saída:** a tabela com as linhas de todos os projetos montados; a lista de projetos feitos × pendentes; e as
pendências de publicação de cada um.
