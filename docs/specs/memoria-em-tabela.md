# Memória em tabela — tudo o que é memória do projeto numa tabela local, cópia para busca

## Estado atual
**Parte 1 (a tabela) — entregue na 0.55.0** (`/mss-spec:memory tabela`). `templates/memoria_tabela.py`
(só lê o projeto; grava só a tabela) monta, a partir dos arquivos do projeto, uma tabela SQLite local **única**
(`memoria`, com a coluna `tipo`): anotações (`memory/*.md`, com a frase do subíndice), diários
(`memory/sessions/`, com a linha do `DIARIO.md`), decisões (`docs/decisoes.md`, uma por linha datada), falhas
(`docs/EVALS.md`, uma por caso) e todo `.md`/`.html` de `docs/` mais `to-dolist.md` e o projeto.md da raiz (quando existe), divididos por
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

## Tudo o que o owner decidiu sobre a memória (2026-11-10 e 11) — o registro que vale

> Quem abrir este assunto numa conversa nova lê **esta seção primeiro**. Cada linha é decisão do owner ou medição
> feita com ele; nenhuma é sugestão. Se uma regra, decisão antiga ou hook do kit parecer proibir algo daqui,
> **não responda "o plugin não aceita"**: mostre a regra com `arquivo:linha` e pergunte ao owner.

**Princípios (valem pra tudo)**
1. **Nada do MSIG_Agentes é usado, copiado ou ligado ao kit.** Serviu só de ideia. Tudo é escrito do zero aqui.
2. **O arquivo no git é o original; a tabela é cópia pra busca.** Grava-se no arquivo e a tabela acompanha.
3. **Sem comando pro owner lembrar.** O que depende de ele chamar não serve (*"vai fazer se perder"*).
4. **Uma medição não é conclusão.** Antes de afirmar: mais de um caso com resposta conhecida, alternativa medida
   ao lado, e rever. Régua e números: `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`.
5. **Conversa em português simples:** resultado na primeira linha, um tópico por vez, pergunta só no texto.
6. **Decisões antigas que NÃO vetam a tabela:** a de 2026-07-21 (memória curada, não-serviço, não busca
   vetorial) e a de 2026-11-06 (não adotar o banco do MSIG_Agentes como fonte). A tabela é um **arquivo**
   SQLite local, cópia, sem servidor — as duas seguem valendo (`docs/decisoes.md`, linhas de 2026-11-10 e 11).

**A tabela — parte 1, entregue na 0.55.0**
7. SQLite local. **Sem Docker, sem servidor, sem banco da empresa.**
8. **Uma tabela só**, com a coluna "tipo". Várias tabelas foram medidas e não ganharam.
9. **Tudo o que é memória entra:** anotações (com a frase do subíndice), diários, decisões, falhas (`EVALS`),
   specs, planos, MAPA, INDEX, `to-dolist.md` e os demais documentos. Documento grande, uma linha por seção.
10. **Mora em `~/mss-spec/memoria.sqlite3`** — fora do `.claude` (*"qualquer alteração perde"*) e fora da pasta
    do kit. Se não achar a tabela, avisa e remonta; nunca segue calado.
11. **Um projeto não lê o outro**; cada um alimenta a tabela na janela dele. Trocou de máquina: remonta (passo a
    passo na memória do kit).
12. Só `.md` e `.html` que o git enxerga; `.env`, `.txt` e trecho privado nunca. Dono e data vêm do git.

**A busca — parte 2, AINDA NÃO construída (é o próximo trabalho)**
13. **Gravar:** no arquivo; a tabela se atualiza **sozinha** logo depois.
14. **Buscar:** na tabela primeiro; se precisar, nos arquivos.
15. A tabela se atualiza sozinha **quando a conversa abre** no projeto e é **montada na hora** se não existir.
16. O modo `tabela` do `/mss-spec:memory` **some da vista do owner** (fica interno e no procedimento de troca
    de máquina).
17. A busca usa o **contexto da conversa** (os pedidos anteriores), não só a última frase. Medido: 32% → 41%.
18. A busca devolve **30 linhas curtas**, com anotações e documentos **separados**, e **o assistente escolhe**
    quais abrir. Medido em 60 casos: 27 → 32 acertos (ideia do owner).
19. **Não resumir o pedido** antes de buscar (medido: piora). **Não reordenar por contagem de palavras**
    (medido: não ganha).
20. As portas `tarefa`, `bug`, `duvida` e o `/mss-spec:memory buscar` passam a usar a tabela.
21. O aviso automático de até 3 anotações por mensagem só troca pro motor da tabela **depois de medido**: no
    MSS-UTILS o jeito de hoje ainda ganha entre os 3 primeiros.
22. **Aceite da parte 2:** arquivo certo entre os 10 em pelo menos 41% dos pedidos reais, sem piorar os outros
    dois gabaritos; teste pra cada item de 13 a 20.

**Os outros itens de memória (fila, depois da parte 2)**
23. **Comando guardado inteiro:** comando ou SQL que o owner vai rodar de novo é gravado completo na anotação;
    senha continua escondida. (Origem: o UPDATE cortado no Whats.)
24. **Consultar pela ação antes de agir:** antes de fazer algo, o assistente busca pelo que vai fazer.
    **PENDENTE — o owner ainda não disse sim nem não.** Só se prova em uso real.
25. **Ajudante pesquisador:** lê muito e devolve só o resumo; usado só nesse papel, escrito do zero no kit.

**Ordem que o owner fixou:** tabela (feita) → busca (parte 2) → comando guardado inteiro → consultar pela ação
(se ele aprovar) → ajudante pesquisador. **Depois** vem a conferência antes de entregar
(`docs/specs/conferencia-antes-de-entregar.md`).

**Em aberto, dito ao owner:** mais da metade dos pedidos reais ainda não acha o arquivo certo; cruzar projetos
não foi medido; busca por significado não foi testada; dono e data só foram conferidos no kit.

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
