# Memória em tabela — tudo o que é memória do projeto numa tabela local, cópia para busca

## Estado atual
**Parte 1 (a tabela) — entregue na 0.55.0** (`/mss-spec:memory tabela`). `templates/memoria_tabela.py`
(só lê o projeto; grava só a tabela) monta, a partir dos arquivos do projeto, uma tabela SQLite local **única**
(`memoria`, com a coluna `tipo`): anotações (`memory/*.md`, com a frase do subíndice), diários
(`memory/sessions/`, com a linha do `DIARIO.md`), decisões (`docs/decisoes.md`, uma por linha datada), falhas
(`docs/EVALS.md`, uma por caso) e todo `.md`/`.html` de `docs/` mais `to-dolist.md` e `projeto.md`, divididos por
seção (specs, planos, MAPA/INDEX e demais). Cada linha guarda projeto, tipo, arquivo e ponteiro
(`arquivo:linha`), título, quando usar, resumo, texto, data e dono.

- **O arquivo no git é o original; a tabela é cópia.** Nunca se grava na tabela à mão; apagar a tabela não
  perde nada — `montar` refaz.
- **Onde fica:** `~/mss-spec/memoria.sqlite3` (pasta do usuário, **fora do `.claude` e de qualquer repo**; uma
  por máquina, todos os projetos juntos). `MSS_MEMORIA_TABELA` troca o caminho.
- **`montar`** relê só o que mudou (assinatura por arquivo), tira o que foi apagado do projeto, nunca toca as
  linhas de outro projeto, e no fim mostra linhas por tipo e o que ainda não foi commitado/publicado.
- **`status`** diz se a tabela existe e se está em dia; tabela ausente → avisa e diz como remontar (exit 1).
- **O que entra:** só `.md` e `.html` que o git do projeto enxerga (rastreado ou novo não ignorado); `.env`,
  `.txt` e trecho `<private>…</private>` nunca.
- **Dono e data:** do histórico do git do próprio projeto (criação do arquivo); decisão, diário e falha usam a
  data que já trazem.
- **Um projeto não lê o outro:** cada projeto alimenta a tabela quando o comando roda nele. Máquina nova =
  rodar `montar` em cada projeto (procedimento na memória do kit).

Fora de escopo desta parte: a busca (parte 2 — as portas seguem lendo `MEMORY.md`/subíndice), a atualização
automática na abertura da conversa e o aviso de "tabela ausente" no `/mss-spec:doctor`.

## Critérios de aceite
1. DADO um projeto com anotação, diário, decisão, falha, spec, plano, MAPA, to-dolist e documento, QUANDO rodo
   `montar`, ENTÃO cada um vira linha com o `tipo` certo, e documento grande vira uma linha por seção com
   `arquivo:linha`.
2. DADO a tabela montada, QUANDO mudo um arquivo e rodo de novo, ENTÃO só as linhas daquele arquivo são refeitas.
3. DADO a tabela montada, QUANDO apago um arquivo do projeto e rodo de novo, ENTÃO as linhas dele saem.
4. DADO dois projetos, QUANDO rodo `montar` em cada um, ENTÃO os dois ficam na mesma tabela e remontar um não
   toca o outro.
5. DADO `.env`, `.txt`, arquivo ignorado pelo git e trecho `<private>`, QUANDO rodo `montar`, ENTÃO nada disso
   entra.
6. DADO nenhuma configuração, QUANDO pergunto onde fica a tabela, ENTÃO é `~/mss-spec/memoria.sqlite3`, nunca
   dentro de `.claude`; com `MSS_MEMORIA_TABELA`, é o caminho informado.
7. DADO a tabela ausente ou desatualizada, QUANDO rodo `status`, ENTÃO ele avisa e diz como remontar.
8. DADO a tabela, QUANDO filtro por projeto, tipo e data num cliente SQLite, ENTÃO vejo as linhas.
9. DADO os 4 projetos reais, QUANDO rodo `montar --sem-git` numa tabela de teste (só leitura neles), ENTÃO a
   contagem fica na ordem da do teste de mesa (3.046 trechos).

## Conferido no real (2026-11-11)
- Tabela temporária, só leitura, `--sem-git`: kit 826 linhas · Whats 1.521 · Transportes V2 509 · MSS-UTILS 144 =
  3.000 (teste de mesa: 3.046). Montar: 1,5 s no Whats, menos de 1 s nos outros; remontar sem mudança não refaz nada.
- Tabela do kit com os padrões (com git): 169 arquivos, 791 linhas, `status` em dia; 70 das 71 anotações com dono
  e data (a que falta ainda não tinha commit).
- Não conferido: dono e data nos outros 3 projetos (o `montar` com git só roda na janela de cada um).

## Escolhas do assistente (o owner pode trocar)
- Um projeto não lê o outro; o nome do projeto vem do título do `CLAUDE.md` (cai pro nome da pasta).
- Dono e data pelo `git log`; conferido só no kit (70 de 70 anotações).
- Modo novo `tabela` no `/mss-spec:memory`; script novo em `templates/`.

## Histórico
- 2026-11-11 — criado: parte 1, a tabela (motivo: teste de mesa de 2026-11-10 — tabela com tudo acha 41% entre
  os 10 contra 12% do jeito de hoje; `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`). O lugar da tabela foi
  decisão do owner: fora do `.claude` ("qualquer alteração perde") e fora da pasta do kit.
