# Regras do kit pelo plugin — o `CLAUDE.md` do projeto só com o que é do projeto

## Estado atual
**Desenho aprovado pra plano; nada construído.** Versão-alvo **0.42.0**. Caso novo **F-040** (`docs/EVALS.md`).

## Por quê
O owner rodou o `/mss-spec:doctor` no Whats e o assistente se perdeu no `CLAUDE.md` "que sempre bate no limite",
achando que o problema já estava corrigido. A 0.31.1 subiu o teto do **modelo** pra 10 KB
(`docs/decisoes.md:38`), mas o mesmo teto vale pro `CLAUDE.md` **do projeto**, que é o modelo copiado + o que é
do projeto. Medido em 2026-10-23:

- o modelo sozinho tem **9.757 B** → sobram **243 B** pro projeto. Todo projeto que preenche a parte dele estoura;
- a cópia é feita **uma vez**, no `kickoff` (`commands/kickoff.md:20`). O Whats tem uma versão velha das regras do
  kit: não tem "Fonte ou não sei", nem as regras 8 a 11, e ainda diz "um assunto por janela é alerta, não trava"
  (`CLAUDE.md:17` do Whats), o contrário do kit atual. Regra nova do kit não chega a projeto existente;
- o Whats já usa índice: 7 arquivos em `.claude/rules/` desde 2026-09-23. Mesmo assim tem **10.096 B**, porque
  a cópia velha das regras do kit ocupa ~6,4 KB e o mesmo ponteiro aparece 4 vezes;
- **o "perdeu a memória" (F-040):** em 2026-09-23 os **fatos** de infra do Whats ("Como roda", "Homologação (Azure)",
  "Versionamento") foram para `.claude/rules/deploy-e-ambiente.md`, que só carrega ao tocar `Dockerfile`,
  `docker-compose*.yml`, `azure-pipelines*.yml`… Nas 76 conversas do Whats essa regra entrou em **4**. Numa conversa
  sobre infra sem abrir esses arquivos, o assistente não sabia o nome do Web App nem a porta, e o owner repetia;
- **regra por tipo de arquivo funciona ao LER, falha ao CRIAR:** nas conversas depois de 2026-09-23, toda leitura de
  arquivo existente carregou a regra (deploy, camadas, logging, segurança, tela: 0 falhas). Criar arquivo novo ou
  editar sem ler antes não carregou: `banco.md` faltou em 5 conversas que criaram arquivos `sql/`, `testes.md` em 2.
  (Script de medição: lê os `nested_memory` dos transcripts × os `Read`/`Edit`/`Write` que casam com o `paths:`.)

## Objetivos
1. Teto do `CLAUDE.md` deixa de estourar por causa do kit: a parte do kit sai do arquivo do projeto.
2. Regra nova do kit chega a **todo** projeto na próxima janela, sem copiar nada.
3. Fato de projeto que o owner citaria numa conversa (infra, como roda, ambiente) está **sempre** carregado.
4. Regra por tipo de arquivo é lida **antes** de o assistente criar ou editar um arquivo daquele tipo.
5. Os projetos existentes migram por um script que confere tudo sozinho e só grava se fechar.

## Não-objetivos
- Mudar o conteúdo das regras do kit. Elas mudam de **lugar**, não de redação (F-029: nunca comprimir regra).
- Recall de regra pela palavra do pedido. O `recall_memoria.py` já cobre memória; regra por assunto que não se liga a
  arquivo fica pra quando houver caso.
- Migrar todos os projetos de uma vez. Cada projeto migra na sua janela, quando o owner rodar o `upgrade`.

## Anti-objetivos (falhou mesmo que funcione)
- **O projeto se perder depois da migração** e o owner ter que passar tudo de novo (fala do owner). Qualquer linha
  que some sem destino conferido é falha.
- Fato de infra atrás de gatilho de arquivo (o F-040 de novo).
- Regra do kit que não carrega e ninguém percebe.
- Projeto sem o kit recebendo as regras do kit.

## Restrições (fatos da documentação do Claude Code, conferidos em 2026-10-23)
- Plugin **não** carrega um `CLAUDE.md` próprio; o caminho documentado pra texto sempre-ativo é hook
  (code.claude.com/docs/en/plugins/components.md).
- `additionalContext` de hook é limitado a **10.000 caracteres por string**, medido separadamente mesmo com vários
  hooks no mesmo evento. Acima disso vira arquivo e o Claude recebe só os 2.000 primeiros caracteres, sem ser mandado
  ler o resto (code.claude.com/docs/en/hooks.md).
- `SessionStart` roda em `startup`, `resume`, `clear`, `compact` e `fork`; depois de compactar, a saída do hook é
  reinjetada (code.claude.com/docs/en/context-window.md).
- `@import` no `CLAUDE.md` pra fora do projeto pede aprovação na 1ª vez em cada projeto, e o caminho do plugin muda a
  cada versão — **rejeitado**.
- `.claude/rules/*.md` com `paths:` carrega quando um arquivo que casa é **lido**; sem `paths:`, carrega sempre.

## Desenho

### Camada 1 — regras do kit, entregues pelo plugin
- O texto sai do `templates/CLAUDE.md` e vai para **`templates/regras-do-kit/`**, em **dois blocos** (o limite é por
  string):
  - `1-modo-de-trabalho.md`: "Modo de trabalho" + "Contexto de janela" (`templates/CLAUDE.md:6-32` hoje, ~5.400
    caracteres);
  - `2-regras-criticas.md`: regras críticas 1 a 11 (`templates/CLAUDE.md:47-58` hoje, ~2.700 caracteres).
- Hook novo **`hooks/regras_do_kit.py`** (`SessionStart`, todos os matchers), **duas entradas** no `hooks/hooks.json`,
  uma por bloco (`--bloco 1` e `--bloco 2`), cada uma com a sua string.
- Cada bloco abre com uma linha dizendo o que é e a regra de desempate: **regra do `CLAUDE.md` do projeto vence a do
  kit quando as duas conflitarem** (ex.: "UI própria e intocável" do Whats contra a regra de Tailwind do kit). É
  assim que entram as exceções.
- **Só age em projeto do kit:** o `CLAUDE.md` da raiz tem a marca `<!-- mss-spec:regras-do-kit -->`. Sem a marca,
  silêncio. O `kickoff` e a migração gravam a marca.
- **Falha visível, não calada:** é o único hook do kit em que falhar calado custa caro (a janela abre sem regra
  nenhuma). Defeito → `systemMessage` de 1 linha ("regras do kit não carregaram — rode `/mss-spec:doctor`") e exit 0.
- Teste trava: cada bloco **≤ 9.000 caracteres** (margem de 10% sob o limite); as `FRASES_CHAVE_CLAUDE_MD` passam a
  ser conferidas nos blocos; o `hooks.json` tem as duas entradas.

### Camada 2 — `CLAUDE.md` do projeto, sempre carregado
Novo `templates/CLAUDE.md`, nesta ordem:
1. Comentário de 2-3 linhas no topo: o que é o arquivo, que as regras do kit vêm do plugin, onde fica o quê, o teto.
   Sem comentário em cada seção (não inflar).
2. A marca `<!-- mss-spec:regras-do-kit -->`.
3. `# <Projeto> — <objetivo>`.
4. `## Regras obrigatórias do projeto` — as "nunca violar" que são só deste projeto (no Whats: `.env` nunca aberto,
   RAG de produção intocável, UI própria).
5. `## Contexto` — **um fato por linha, sempre por extenso, nunca ponteiro pra `.claude/rules/`**: Infra (MSIG ou
   própria; proxy sim/não), Stack, Como roda, Ambientes (homologação/produção: onde e nome), Banco, Integrações,
   Versionamento.
6. `## Mapa de arquivos` — só o que não se infere.
7. `## Índice de regras por tipo de arquivo` — uma linha por arquivo de `.claude/rules/`: assunto → arquivo → quando
   carrega. Cada arquivo aparece **uma** vez.

**Teto da parte do projeto: 10.000 B, e ele é orçamento, não trava.** Estimativa pro Whats depois da migração:
~4.200 B da parte do projeto − ~900 B de ponteiros + ~3.800 B dos itens que voltam pro `## Contexto` (Como roda 874,
Versionamento 561, Homologação 466 de `deploy-e-ambiente.md`; Banco 997 de `banco.md`; Testes 613 de `testes.md`;
UI 263 de `ui-propria.md`) + ~800 B das linhas-ponteiro pra `docs/MODO-DE-TRABALHO.md` + ~1.100 B de índice,
comentário e marca ≈ **9.000 B**. O Whats é o maior projeto; os outros cabem com folga. Passou do teto → aviso, e o
conserto continua sendo mover bloco com ponteiro, nunca comprimir; o que nunca pode sair é a seção `## Contexto`.
Total sempre-ativo por janela: ~8 KB do kit + até 10 KB do projeto (~4.500 tokens; hoje o Whats tem 10 KB, mas com os
fatos de infra escondidos).

### Camada 3 — regra por tipo de arquivo, lida antes de criar
- O que vai pra `.claude/rules/` é só **como escrever** aquele tipo de arquivo (SQL, teste, tela, rota). Fato do
  projeto não vai.
- Hook novo **`hooks/regra_antes_de_gravar.py`** (`PreToolUse` em `Write|Edit|MultiEdit`): se o arquivo-alvo casa com o
  `paths:` de algum `.claude/rules/*.md` do projeto, **nega uma vez por sessão por regra**, com o texto da regra no
  motivo ("leia isto antes; repita a gravação"). Mesmo mecanismo da memória no comando (`docs/decisoes.md:43`).
  Estado por sessão em `~/.claude/mss-spec/`, como o `um_item_por_janela.py`. Falha **aberta** (é rede: bug aqui não
  pode travar gravação). Escape `MSS_REGRA_OFF=1`. Registro em `hooks/_registro.py`.
- Custo aceito: 1 negação a mais na 1ª gravação de cada tipo por sessão, mesmo quando a regra já tinha carregado
  pela leitura (o hook não enxerga o contexto).

### Migração dos projetos existentes — `templates/migrar_claude_md.py`
Chamado pelo `/mss-spec:upgrade`. Dry-run por padrão; `--aplicar` grava. Etapas:
1. **Monta em memória** o `CLAUDE.md` novo e os arquivos de regra alterados. Não grava nada.
2. **Classifica cada linha não vazia** do `CLAUDE.md` antigo:
   - **do kit** → sai (o plugin entrega). Reconhecida comparando com **todas as versões** do `templates/CLAUDE.md` no
     histórico do kit (40 commits hoje). Como o plugin instalado pode não ter `.git`, as linhas normalizadas dessas
     versões ficam num arquivo versionado em `templates/regras-do-kit/`, gerado por script e travado por teste;
   - **ponteiro de `## Contexto` para `.claude/rules/`** → troca pelo item de mesmo rótulo em negrito do arquivo de
     regra (ex.: `**Como roda:**` de `deploy-e-ambiente.md`), que **sai** do arquivo de regra. Vale pra **todo**
     rótulo do `## Contexto`, não só os de infra. Item que mistura fato e regra de escrita (o `**Banco:**` do Whats
     traz PostgreSQL/pgvector **e** "nunca `psycopg2.connect` inline") volta **inteiro**: sempre carregado, a regra
     de escrita segue coberta;
   - **ponteiro repetido** → fica uma linha no índice;
   - **linha com título de regra do kit + ponteiro pra um documento do projeto** (no Whats, `CLAUDE.md:12,15,16,22` →
     `docs/MODO-DE-TRABALHO.md`, onde mora "o assistente não executa nada que escreva no git") → **é do projeto,
     fica** em `## Regras obrigatórias do projeto`. É por ela que a exceção do projeto vence a regra do kit. A
     migração não toca no documento apontado;
   - **o resto** → fica no `CLAUDE.md`, na seção correspondente.
   - **Na dúvida, fica.** Linha que parece do kit mas não bate com segurança fica no projeto e entra no relatório.
3. **Confere sozinho, e só segue se tudo passar:**
   - **conservação:** toda linha do antes (CLAUDE.md + arquivos de regra) está no depois (CLAUDE.md + arquivos de
     regra) **ou** na lista de linhas do kit. Nenhuma linha sem destino;
   - **fatos sempre carregados:** a seção `## Contexto` não tem nenhum ponteiro pra `.claude/rules/`, e os rótulos que
     existiam antes (Infra, Stack, Como roda…) continuam lá;
   - **marca** presente; índice com cada arquivo de regra uma vez só; todo arquivo de regra citado existe;
   - **working tree limpo** nos arquivos que a migração toca (é o ponto de volta).
   - O teto **não** reprova: acima de 10.000 B sai como aviso no relatório. Recusar deixaria o projeto no formato
     velho, que é o problema.
4. **Falhou alguma conferência** → não grava nada e lista o que não fechou.
5. **Passou** → com `--aplicar`, grava os arquivos e **para aí**: o script não faz nada no git. Desfazer é
   `git restore` nos arquivos tocados, porque o working tree estava limpo. Branch e commit seguem a regra de git **do
   projeto**: no padrão do kit, o assistente abre `chore/migrar-claude-md` a partir da principal e commita com stage
   nominal; no Whats, onde o assistente não escreve no git (`memory/git-e-do-owner.md` do Whats), ele entrega os
   comandos passo a passo pro owner.
6. Relatório pro owner, curto: quantas linhas saíram como do kit, quantas mudaram de lugar, quais ficaram por dúvida.

**No `/mss-spec:upgrade`:** projeto **sem** a marca → a migração roda **primeiro e sozinha** (nenhuma outra categoria
na mesma rodada) e o `upgrade` termina pedindo o commit. Projeto **com** a marca → a categoria 2 deixa de reacrescentar
seções do kit no `CLAUDE.md` (elas vêm do plugin); a categoria 1 já só acrescenta regra que falta
(`commands/upgrade.md:28`) e continua assim — nunca sobrescreve arquivo de regra do projeto.

Prova antes de qualquer projeto: testes com **cópias** do `CLAUDE.md` e do `.claude/rules/` do Whats (versão de
2026-10-23) e com o modelo atual preenchido, + dogfood no Whats real com diff antes × depois
(`memory/project_dogfood_gerador_diff_antes_depois.md`).

### Correções que entram junto
- **`hooks/teto_ao_gravar.py`**: comando de shell que só **lê** (`wc -c CLAUDE.md`, `cat`, `grep`) não conta como
  gravação. Só age se o arquivo mudou de verdade.
- **`hooks/orcamento_partida.py`**: tamanho com uma casa decimal ("10,1 KB", nunca "10 KB (teto 10 KB)"). Projeto
  **ainda sem a marca** e acima do teto → o aviso diz "rode `/mss-spec:upgrade` pra migrar", não "mova um bloco", e
  não manda oferecer o doctor.
- **`commands/doctor.md`**: check 3 conta só chave vazia do `.env.example` e como ℹ, nunca ✗; check 4 com proxy
  inalcançável vira "a verificar (fora do escritório/VPN)", como o check 6 com o Docker parado; check 9 com o teto
  novo, e confere se o projeto tem a marca e se os dois blocos do kit cabem.
- **`commands/kickoff.md`**: grava o modelo novo (com a marca), sem copiar regra do kit.
- **`commands/analise.md`**: ao preencher `## Contexto`, fato por extenso, nunca ponteiro.
- **`tests/test_orcamento_contexto.py`**: os tetos novos nos três lugares (teste, hooks, `rodizio_partida.py`).
- Versão **0.42.0** nos dois manifestos; `CHANGELOG`; F-040 no `docs/EVALS.md`; decisão em `docs/decisoes.md`.

## Decidido pelo owner
- Regras do kit vêm do plugin; não precisa vê-las escritas no `CLAUDE.md`, "desde que funcione".
- Regras obrigatórias primeiro, índice abaixo, organizado, com comentário só no topo.
- Vale pra todos os projetos; há raras exceções sem o kit.
- Cada projeto tem infra diferente (proxy ou não, Azure ou não) — isso não pode se perder.
- Migração automática que compara, valida e só então grava.

## Decisões minhas (o owner confere)
- Teto da parte do projeto: **10.000 B**, como aviso (não reprova a migração); cada bloco do kit: **≤ 9.000
  caracteres**, travado por teste.
- Desempate: regra do projeto vence a do kit.
- Marca `<!-- mss-spec:regras-do-kit -->` pra o hook só agir em projeto do kit.
- Hook das regras do kit falha **visível**; hook da regra antes de gravar falha **aberta**.
- Nega uma vez por sessão por regra, com o texto no motivo, em vez de só lembrar.
- Todo rótulo do `## Contexto` volta por extenso, inclusive Banco, Testes e UI; item que mistura fato e regra volta
  inteiro.
- Linha de regra do kit que aponta pra documento do projeto é do projeto e fica.
- O script de migração não faz nada no git; branch e commit seguem a regra de git de cada projeto.

## Deixado pro construtor
- A biblioteca de casamento de glob, desde que case como o Claude Code (`**/*.sql` casa `sql/x.sql` e `x.sql`), com
  testes dos padrões reais do Whats.
- Como o `teto_ao_gravar.py` detecta "mudou de verdade" (tamanho + data de modificação guardados por arquivo, ou
  outro jeito), desde que `wc -c CLAUDE.md` não dispare e uma gravação por shell dispare.
- A normalização das linhas (espaços, marcação) e o limiar de semelhança pra "linha do kit", desde que a dúvida
  fique no projeto.

## Histórico
- 2026-10-23 — criado. Doctor no Whats: `CLAUDE.md` 10.096 B; o assistente puxado pra mexer no `CLAUDE.md` e no MAPA
  pelo `teto_ao_gravar.py` disparando em comando de leitura. Medição nas 76 conversas do Whats mostrou a cópia velha
  das regras do kit, os fatos de infra atrás de gatilho de arquivo (F-040) e a regra por tipo falhando ao criar.
