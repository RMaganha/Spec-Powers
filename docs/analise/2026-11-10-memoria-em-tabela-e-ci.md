# Memória em tabela e conferência antes de entregar — análise e teste de mesa (2026-11-10)

> Tarefa do owner (`/mss-spec:tarefa`, 2026-11-10): entender o que o kit de agentes da equipe
> (`C:\Ronaldo\_Mitsui\Python\MSIG_Agentes`) faz de melhor em **memória**, **agentes** e **revisão de código**,
> e resumir como melhorar o mss-spec. Tudo aqui foi **somente leitura** nos outros projetos; as medições
> rodaram em pasta temporária; os roteiros estão guardados em `docs/analise/2026-11-10-teste-de-mesa/`.
> **Nada de lá é usado, copiado ou ligado ao kit** (owner, nesta conversa; `docs/decisoes.md`, linha de
> 2026-11-06 "sem misturar"): o outro projeto serviu só de inspiração.

## 1. O que o owner viu no outro projeto

Conversa "Design system do menu Análise de Contratos" (MSIG_Agentes, 2026-11-09/10). Três coisas chamaram a
atenção dele:

1. **Memória em banco**: o agente acha o que precisa gastando pouco. Lá o conhecimento vive numa tabela
   (agente, tipo, tag, título, conteúdo, autor, datas, versão, arquivado); a busca roda numa cópia SQLite local,
   devolve 15 linhas (nota · agente · tipo · tag · título · resumo) e o agente puxa 1 a 3 seções inteiras.
   Motivo registrado no código de lá: o índice de um agente chegou a 56 KB lidos a cada ativação
   (`.msig-agents/tools/kb.py`, bloco "Busca ranqueada"; `.claude/commands/agentes_msig.md`, Passo 1).
2. **"Sabe tudo dos projetos"**: persona de domínio por agente + um arquivo geral lido sempre + busca que
   cruza agentes; e grava no fechamento de **toda** demanda, sem perguntar.
3. **Revisão antes do PR ("CI")**: não é pipeline. É um ciclo: coletar os comentários dos revisores nos PRs →
   uma seção por PR no conhecimento → cada apontamento vira item de um checklist (75 itens, com revisor, PR e
   data) → procedimento de 7 passos que dispara em "abrir PR" (gate automático, checklist, revisão independente
   no formato do revisor, lint e testes locais). O próprio agente avisou que o fluxo **ainda não rodou numa
   entrega real**.

Sobre velocidade: naquela conversa foram **2 subagentes** (revisão independente do diff; consolidar 75
apontamentos) contra 266 comandos de shell. A rapidez vem de agir e gravar sem pedir OK e de rodar em modo
automático — e teve custo: na mesma conversa o owner reclamou de mudança feita sem permissão e de demora.

## 2. Decisões do owner nesta conversa

| # | Item | Decisão |
|---|---|---|
| 1 | Achar anotações por busca, em vez de ler as listas | entra |
| 2 | Conferência do código antes de entregar | entra |
| 3 | Tudo o que é memória numa tabela SQLite local | entra |
| 4 | Dois ajudantes de tarefa fixa (pesquisador e revisor), escritos do zero no kit | entra |
| 5 | Teste automático do próprio kit a cada publicação | entra, **pendente**: a decisão de 2026-07-20 escolheu GitLab CI "em vez de GitHub Actions" e o kit hoje é publicado no GitHub — o owner ainda não disse se revê |
| 6 | Comando guardado inteiro na anotação | entra (nasceu do teste de mesa) |

Regras que o owner fixou:

- **Arquivo é o original; a tabela é cópia para busca.** Grava-se no arquivo, procura-se na tabela. A tabela
  nunca é gravada à mão.
- **SQLite local, sem Docker e sem servidor.** Conferido nesta máquina: Python 3.14.5, SQLite 3.50.4, com a
  busca por palavras embutida (FTS5).
- **Não se perde ao trocar de máquina**: os originais estão no git de cada projeto; **um comando do kit
  remonta a tabela**, e o passo a passo fica gravado na memória do projeto (procedimento).
- **Uma tabela só**, com a coluna "tipo". Várias tabelas foram medidas e não ganharam (seção 4.5).
- **Ordem** — Memória: 6 → 3 → 1 → consultar pela ação → 4a (pesquisador). Entrega: 2 → 4b (revisor) → 5.
  A tabela vem antes da busca para a busca ser escrita uma vez só.

## 3. O que as falhas já registradas mostram

As 172 falhas registradas (`docs/EVALS.md` do kit, do Whats e do Transportes) são o resumo dos apontamentos do
owner. Classificação por palavra-chave (aproximada):

| Tema | Casos |
|---|---|
| Afirmar sem medir: concluir de premissa ou de amostra pequena | 52 (30%) |
| A regra ou anotação já existia e não foi usada | 35 (20%) |
| Forma da resposta: longa, confusa, roteiro ruim | 26 (15%) |
| Defeito silencioso no que foi entregue | 13 (7%) |
| Outros | 46 (26%) |

Os três primeiros temas se repetiram **nesta conversa** (seção 6). Conclusão: a dor principal não é "a busca é
fraca"; é o assistente **não consultar na hora de agir** e **não rever**. Só 15 das 359 anotações dos 4 projetos
têm gatilho por ação (`gatilho_comando`/`gatilho_resposta`).

## 4. Teste de mesa

### 4.1 Acervo e gabaritos

- **Projetos**: mss-spec (kit), IA Bot Agent - Whats, Transportes V2, MSS-UTILS.
- **Acervo**: 3.046 trechos — 359 anotações (com a frase do subíndice), 108 diários (com a linha do
  `DIARIO.md`), 199 decisões datadas, 172 falhas, e todo `.md`/`.html` de `docs/` (specs, planos, MAPA, INDEX,
  históricos, demais) mais o `to-dolist.md`, divididos por seção. Ficaram fora de propósito `.txt` e `.env`
  (podem ter segredo).
- **Pedidos reais**: 2.854 pedidos do owner em 171 conversas.
- **Gabaritos** (944 casos):
  - **K1 situação → regra** (61): a pergunta é a situação da falha; o certo é a anotação que a falha cita.
    Otimista: muitas anotações nasceram da própria falha, com palavras parecidas.
  - **K2 descrição → anotação** (228): a pergunta é a frase de "quando usar", escondida da busca.
  - **K3 pedido real → arquivo** (655): o certo é o arquivo aberto ou citado na resposta, tirando o que foi
    gravado na mesma rodada e os índices lidos por rotina. Inclui 249 perguntas e apontamentos. Tem ruído: o
    arquivo mais frequente é o `to-dolist.md`; sem os arquivos de rotina sobram 480 casos.

### 4.2 A régua (arquivo certo entre os N primeiros)

| Gabarito | Jeito | 1º | até 3 | até 10 |
|---|---|---|---|---|
| K1 (61) | hoje (`memoria_indice.casar`) | 54% | 75% | 78% |
| K1 (61) | tabela só com anotações | 70% | 81% | 91% |
| K1 (61) | tabela com tudo | 67% | 78% | 86% |
| K2 (228) | tabela só com anotações | 56% | 84% | 95% |
| K2 (228) | tabela com tudo, misturado | 52% | 76% | 88% |
| K2 (228) | tabela com tudo, 5 vagas só de anotações | 58% | 83% | 90% |
| K3 (223, amostra) | hoje | 6% | 9% | 12% |
| K3 (223, amostra) | hoje, com o contexto da conversa | 9% | 14% | 21% |
| K3 (655) | tabela só com anotações | 3% | 6% | 13% |
| K3 (655) | tabela com tudo | 6% | 15% | 32% |
| K3 (655) | tabela com tudo + contexto (3 pedidos anteriores) | 8% | 22% | 41% |
| K3 (655) | busca direta nos arquivos (sem tabela), tudo + contexto | 4% | 9% | 23% |
| K3 perguntas e apontamentos (249) | tabela com tudo + contexto | 8% | 22% | 38% |
| K3 perguntas e apontamentos (88) | hoje, com contexto | 11% | 17% | 21% |
| K3 sem arquivos de rotina (480) | tabela com tudo + contexto | 11% | 28% | 46% |

Caso a caso, até 10 (hoje com contexto × tabela com tudo e contexto): K1 — os dois 47, só a tabela 6, só o de
hoje 1, nenhum 7. K3 (223) — os dois 29, só a tabela 65, só o de hoje 19, nenhum 110.

Por projeto (K3, tabela com tudo + contexto, até 10): kit 39% (hoje 17%), Whats 41% (hoje 7%), MSS-UTILS 52%
(hoje 44% — e **entre os 3 primeiros o de hoje ganha**: 35% × 20%), Transportes só 4 casos (não conclui).

### 4.3 Custo e tempo

| Projeto | Leitura por consulta hoje (`MEMORY.md` + subíndice médio + anotação) | Com a busca (10 linhas + anotação) |
|---|---|---|
| Whats | 16.693 bytes | 3.926 bytes |
| Kit | 6.796 bytes | 3.563 bytes |
| Transportes | 6.523 bytes | 3.206 bytes |
| MSS-UTILS | 5.300 bytes | 3.535 bytes |

Tabela dos 4 projetos: 3.046 linhas, 10,6 MB, gravada em 0,9 s (mais a leitura dos arquivos: poucos segundos).
Busca: 13 ms por projeto, 22 ms na tabela inteira. Filtro por projeto + tipo + mês, sem índice: 3 ms.

### 4.4 Estruturas testadas (quase todas empataram)

Rodada com o acervo só de anotações (224 casos de descrição / 232 pedidos reais, até 10): uma linha por anotação
94% / 37% · pesos iguais 94% / 37% · palavra exata 92% / 37% · pedaços de 3 letras 91% / 32% · uma linha por
trecho 93% / 36% · coluna extra de nomes técnicos 93% / 36%. Com o acervo completo: frase do subíndice não muda
(13% com e sem), diário por seção não muda (40% × 41%).

**O que muda o acerto**: pôr todos os documentos (13% → 32%), usar o contexto da conversa (32% → 41%) e separar
anotações de documentos na resposta (K2: 76% → 83% entre os 3).

### 4.5 Uma tabela × várias

| Jeito (K3, 655) | 10 resultados | ~20 resultados | tempo |
|---|---|---|---|
| 1 tabela, coluna "tipo" | 41% | 57% | 13 ms |
| 2 tabelas (anotações · documentos) | 43% | 58% | 15 ms |
| 8 tabelas, uma por tipo | 36% | 53% | 26 ms |

Várias tabelas não ganham. Fica uma.

### 4.6 Buscar 30 e ficar com 10 (ideia do owner)

- **Teto**: o arquivo certo está entre os 30 em 63% dos casos (K3, 655), contra 41% entre os 10.
- **Reordenar por contagem de palavras** (5 jeitos): 33% a 43%; o ganho não se repete nas duas metades dos
  casos. Não funciona.
- **Alguém lendo as 30 linhas e escolhendo 10** (60 pedidos sorteados, 3 ajudantes sem a resposta): busca
  direta 27 de 60 · escolha 32 de 60 · teto 37. Entre os 3 primeiros: 16 → 19. Caso a caso: só a escolha 8, só
  a busca 3. Mesma direção nos 3 projetos (kit 8 → 10, Whats 15 → 17, MSS-UTILS 4 → 5). **Melhora**, com a
  ressalva de que 60 casos é pouco para medir o tamanho do ganho.
- Custo de devolver 30 linhas: cerca de 4,7 KB por busca (10 linhas: 1,6 KB).

### 4.7 Outras medições

- **Dono e data**: nenhuma das 359 anotações tem esses campos. No kit, o histórico do git dá data e autor de
  criação das 70 (100%). Nos outros projetos não foi medido (regra 8: não se roda git fora do projeto da janela).
- **O que os pedidos citam** (2.852): ambiente 23% · nome técnico 20% · comando ou SQL 8% · outro projeto ou
  conversa 7% · tempo 5%.
- **Comando cortado**: 8 das 35 anotações com SQL têm reticências; quase todas legítimas (exemplo de sintaxe,
  senha escondida). Caso claro: 1 (Whats) — a anotação guardou o começo de um UPDATE, sem o `WHERE`, e o owner
  precisou reconstituir.
- **Reforços**: 53 pedidos com sinal de reforço ("já falei", "como eu disse"); só 15 com arquivo certo
  conhecido — pouco para concluir sozinho.

## 5. O que o teste não prova

- **Mais da metade dos pedidos reais continua sem achar** (41% entre 10; 57% entre 20; 63% entre 30). Parte é
  ruído do gabarito; parte é relevância por **ação** e não por palavra.
- **Consultar pela ação** só se prova em uso real. No papel, perguntar pela situação acha a regra em 78% a 91%
  — nos dois motores; o que falta é o assistente perguntar na hora de agir.
- **Cruzar projetos** não foi medido (não há gabarito).
- **Busca por significado** e **catálogo curto lido pelo assistente** não foram testados: as três soluções
  comparadas (hoje, tabela, busca direta) buscam por palavras. Cabe o `/mss-spec:divergir` no desenho.
- **O que nunca foi anotado** nenhuma tabela acha.
- **O ganho de escolher 10 entre 30** vem de 60 casos.

## 6. O que caiu no caminho (falhas do assistente nesta conversa)

| O que foi afirmado | O que aconteceu |
|---|---|
| "Resumir o pedido em poucas palavras acha melhor" | Concluído de 1 caso em que o assistente escolheu as palavras sabendo a resposta. Com 310 casos, piorou (83% → 73%; 24% → 19%) |
| "40% das anotações do Whats e 67% do Transportes não têm 'quando usar'" | Errado: todas têm a frase no subíndice (190 de 190; 83 de 83). Os subíndices não tinham sido lidos |
| "Muitos pedidos são curtos" como explicação do erro | O gabarito cobria 8% dos pedidos e quase nenhum questionamento do owner |
| Estrutura da tabela dada como certa | Era rascunho; nenhuma alternativa tinha sido comparada |
| Tópico 5 proposto no GitHub | Sem mostrar a decisão de 2026-07-20 (GitLab CI) |
| Partida | `docs/EVALS.md` e os subíndices não foram lidos antes de propor |
| Forma | Respostas longas, com jargão, e pergunta repetida na caixa do fim da rodada |

O owner precisou pedir quatro vezes para o teste ser refeito com mais casos e com todas as fontes. É o padrão
dos temas 1 a 3 da seção 3.

## 7. Escopo fechado

### Passo 1 — Memória

| Ordem | Item | O que é | Como se confere |
|---|---|---|---|
| 1º | Comando guardado inteiro | Comando ou SQL que o owner vai rodar de novo é gravado completo; senha continua escondida | o caso do Whats não se repete |
| 2º | Tabela SQLite única | Tudo o que é memória numa tabela (coluna "tipo"); documentos grandes por seção; dono e data; comando que remonta + procedimento na memória do projeto | acervo completo; remontar em segundos |
| 3º | Busca | Usa o contexto da conversa; devolve 30 linhas curtas, anotações e documentos separados; o assistente escolhe quais abrir | régua da seção 4.2: não piorar; alvo K3 ≥ 41% entre 10 |
| 4º | Consultar pela ação | Antes de agir, o assistente busca pelo que vai fazer | **owner ainda não disse sim ou não**; só se prova em uso |
| 5º | Ajudante pesquisador | Lê muito e devolve só o resumo | — |

### Passo 2 — Conferência antes de entregar

| Ordem | Item |
|---|---|
| 1º | Lista de conferência do projeto, alimentada pelos apontamentos do revisor (cada item com origem) |
| 2º | Ajudante revisor (confere a mudança pela lista, com olhos de quem não escreveu) |
| 3º | Teste automático do kit — depende da decisão GitLab × GitHub |

Princípio que o owner cobrou e vale para os dois passos: **uma medição não é conclusão** — antes de afirmar,
mais de um caso, e rever.

## 8. Como reproduzir

Roteiros em `docs/analise/2026-11-10-teste-de-mesa/` (código de teste, descartável; **não** é o código do kit):

- `mesa2.py garimpar` — lê as conversas dos 4 projetos e grava `casos2.json`;
- `mesa2.py medir 80` — a régua da seção 4.2 e os custos da 4.3;
- `varias.py` (4.5) · `reordenar.py` e `lotes.py` (4.6) · `situacao.py` (seção 3) · `estruturas.py` e
  `avaliar.py` (4.4, rodadas anteriores) · `mesa.py` e `minerar.py` (apoio).

Os dados gerados (`*.json`, `*.sqlite3`, `lote*.md`) **não estão no repositório**: contêm os pedidos reais do
owner em outros projetos. Ficaram na pasta temporária da conversa de 2026-11-10 e se regeneram com
`mesa2.py garimpar` enquanto as conversas existirem em `~/.claude/projects/`; as escolhas dos 3 ajudantes
(seção 4.6) não se regeneram iguais. O `.gitignore` barra esses arquivos nesta pasta, para o caso de os
roteiros rodarem aqui. Os caminhos dos 4 projetos e das conversas estão fixos no `mesa.py`.

## 9. Textos prontos para as próximas janelas

Uma janela por item, na ordem da seção 7. O owner abre a conversa pelo **+** e cola.

**Item 2 do passo 1 (tabela):**

```text
/mss-spec:nova-feature Memória em tabela — parte 1: a tabela. Escopo, medições e régua em
docs/analise/2026-11-10-memoria-em-tabela-e-ci.md (leia a seção 7 e a 4 antes de qualquer desenho).
Fazer só isto: um comando do kit que monta, a partir dos arquivos do projeto, uma tabela SQLite local
(uma tabela só, coluna "tipo") com tudo o que é memória — anotações com a frase do subíndice, diários,
decisões, falhas, specs, planos, MAPA, INDEX, to-dolist e documentos por seção — com projeto, dono e data.
Arquivo continua sendo o original; a tabela é cópia e fica fora do git. O mesmo comando remonta tudo na
máquina nova e avisa o que ainda não foi publicado; o passo a passo vira procedimento na memória do projeto.
Nada do MSIG_Agentes é usado ou copiado. A busca é a parte 2, em outra janela. Antes de fechar o desenho,
compare caminhos diferentes (/mss-spec:divergir) e meça na régua — uma medição não é conclusão.
```

**Item 1 do passo 1 (comando inteiro):**

```text
/mss-spec:tarefa Comando guardado inteiro: quando uma anotação ou diário citar um comando ou SQL que eu vou
rodar de novo, ele é gravado completo (nunca cortado com reticências); senha e credencial continuam
escondidas. Origem e medição: docs/analise/2026-11-10-memoria-em-tabela-e-ci.md, seção 4.7.
```

**Item 3 do passo 1 (parte 2: a busca usa a tabela e a tabela se atualiza sozinha)** — texto revisto em
2026-11-11, depois da parte 1 (0.55.0) e da decisão do owner de não ter comando pra lembrar. **Como abrir sem ser
bloqueado:** na conversa nova, **digite** `/mss-spec:nova-feature` e um espaço, e só então cole o resto (texto
colado inteiro pode não ser reconhecido como comando do kit — caso F-053).

```text
Memória em tabela — parte 2: a busca usa a tabela e a tabela se atualiza sozinha.
Leia antes de qualquer desenho, nesta ordem: docs/specs/memoria-em-tabela.md — a seção "Tudo o que o owner
decidiu sobre a memória" é o registro que vale (25 decisões; a parte 1 já foi entregue);
docs/analise/2026-11-10-memoria-em-tabela-e-ci.md, seções 4.2, 4.6, 5 e 7 (a régua e o que não está provado);
memory/sessions/2026-11-11-memoria-em-tabela-parte-1.md (como chegamos aqui); e docs/EVALS.md, casos F-054 a
F-057 (o que eu não aceito de novo). Se alguma regra, decisão antiga ou trava do kit parecer proibir algo do
que está decidido, não me responda "o plugin não aceita": mostre a regra com arquivo e linha e me pergunte.
O que eu já decidi (resumo; o registro completo está na spec):
1. Gravar continua sendo no arquivo, e a tabela se atualiza sozinha logo depois. Sem comando pra eu lembrar.
2. Buscar é na tabela primeiro e, se precisar, nos arquivos.
3. A tabela se atualiza sozinha quando a conversa abre no projeto, e é montada na hora se não existir.
4. O modo "tabela" do /mss-spec:memory some da minha vista: fica interno e no procedimento de troca de máquina.
5. A busca usa o contexto da conversa, devolve 30 linhas curtas com anotações e documentos separados, e o
   assistente escolhe quais abrir.
6. As portas tarefa, bug e duvida e o /mss-spec:memory buscar passam a usar a tabela.
Como provar: teste para cada item acima, e a régua — arquivo certo entre os 10 em pelo menos 41% dos pedidos
reais, sem piorar os outros dois gabaritos. No MSS-UTILS o jeito de hoje ganha entre os 3 primeiros: meça antes
de trocar o aviso automático de 3 anotações. Os dados da régua não estão no repositório: regenere com
docs/analise/2026-11-10-teste-de-mesa/mesa2.py garimpar.
Como trabalhar comigo: português simples, resultado na primeira linha, um tópico por vez, pergunta só no texto.
Uma medição não é conclusão: mais de um caso, e rever. Nada do MSIG_Agentes é usado ou copiado.
Não abra outra frente: o resto da fila está em docs/superpowers/INDEX.md (itens 8 a 15).
```

**Passo 2, item 1 (conferência antes de entregar):**

```text
/mss-spec:nova-feature Conferência antes de entregar: cada projeto ganha uma lista de conferência que cresce
a cada apontamento de revisor (item com origem: quem, onde, quando), e o assistente passa a mudança por ela
antes de dizer "pronto para entregar". Origem: docs/analise/2026-11-10-memoria-em-tabela-e-ci.md, seções 1 e 7.
O ajudante revisor é a janela seguinte. Nada do MSIG_Agentes é usado ou copiado.
```

## 10. Lacunas

- Não li o corpo inteiro do `kb.py` de lá (só a busca e a criação da cópia local) nem os outros agentes além do
  roteador e do `mssai`.
- O gabarito K3 depende de as conversas ainda estarem em `~/.claude/projects/` (pasta volátil).
- A classificação das 172 falhas é por palavra-chave.
- Energy e DeRe não entraram no teste.
