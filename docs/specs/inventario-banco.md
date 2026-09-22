# inventário do banco vivo — o que a `analise` não alcança

## Estado atual (implementado na 0.28.0 — **não validado contra banco real**; ver Histórico)

O `/mss-spec:analise` sabe ler `.sql` **que está no repositório**. Num sistema legado, a regra de
negócio não está lá: está **dentro do banco**, em procedure, function, trigger e job do Agent. O kit
já tem o conector (`templates/get_connection.py`, Fernet multi-ambiente, usado em Transportes V2 e
Jedai Cosseguro), mas **nenhum comando manda a análise usá-lo** — o inventário do banco é a lacuna.

Entra o **4º gerador determinístico**, no padrão já provado três vezes (`mapa_neural.py`,
`anatomia.py`, `bpmn.py`): script testável + comando-prosa fino + saída fora do git.

| peça | o que é |
|---|---|
| `templates/inventario_banco.py` | o gerador: conecta somente-leitura, lê o catálogo, cruza com o código, grava |
| `commands/inventario-banco.md` | comando fino, para **regenerar** sem reanalisar |
| passo *Dados (banco vivo)* na fase 2 do `commands/analise.md` | a **entrada real** — quem dispara na prática |

### 1. O gatilho: a `analise` decide sozinha

O owner não deve precisar saber o nome do comando (*"eu não vou saber quando usar... o analise vai
ter que ser inteligente o suficiente"*). O passo dispara por **evidência lida no código**:

- `web.config`/`app.config` com `<connectionStrings>`, `SqlConnection`/`SqlCommand`/`SqlDataAdapter`
  nos `.cs`, `.edmx`, Dapper, EF
- `utils/get_connection.py`, `pyodbc`, `psycopg`, SQLAlchemy, `.sql` no repo (o que a fase 2 já vê)

Achou → **anuncia e age**, sem menu: diz qual evidência achou e pergunta só **qual base** e **como
chegar na credencial**. Essa pergunta é o próprio portão da conexão — não existe um "posso conectar?"
separado, porque sem o dado do owner não há conexão. Owner disse "pula" → linha nomeada em
*Lacunas* do `ARQUITETURA.md`, nunca silêncio.

Ler `<connectionStrings>` pra **detectar** não é ler pra **usar**: o gatilho olha se a seção existe e
qual o `Server=`/`Initial Catalog=`; senha que esteja ali não vira credencial nem é ecoada.

A detecção por `web.config`/`SqlConnection` é uma **fatia de C#** entrando já aqui, pelo mínimo
necessário pro gatilho disparar num projeto .NET. A cobertura C# completa (`Program`/`Startup`,
controllers, `.csproj`, rotas) é item separado do INDEX.

### 2. Credencial: reusar o que já conecta, sem persistir nada

Regra que vem da memória `credencial-reusar-env-precedente`: **nunca pedir credencial digitada;
reusar o que já conecta** (origem: *"Lá já tem tudo!!!"*, 2026-07-08).

Cadeia de resolução, para no primeiro caminho que resolver (`--fonte` passado **ganha** da variável — a
flag é a intenção mais específica; a variável ignorada é avisada):

1. **Par Fernet reaproveitado** (padrão) — `--fonte <get_connection.py de um projeto MSIG que alcança
   o servidor>` + `--ambiente D0|HML|PRD` + `--base <nome>` + `--porta` (opcional) + `--par <BASE>` quando a fonte
   tem mais de uma base (sem ele, o script **para e lista os nomes** — nunca escolhe sozinho). O caso que
   motivou: base **nova**, **não mapeada** em `get_connection.py` nenhum, mas no **mesmo servidor com
   o mesmo login** — o que já está mapeado. O `--base` sobrescreve `Database=`/`Initial Catalog=` da
   conn string decriptada (acrescenta se não houver); sem `--base`, usa a que veio e **diz qual**
   antes de conectar.
2. **`MSS_INVENTARIO_CONN`** — conn string completa em variável de ambiente. Cobre o caso sem projeto
   de referência e o `Trusted_Connection=yes`, que dispensa senha.
3. Nada resolveu → **para com erro que nomeia o que faltou**. Nunca chuta host, porta ou base.

Três mecânicas:

- **Leitura estática, nunca `import`.** O par `*_KEY`/`*_CIPHERTEXT` sai por `ast.literal_eval` sobre
  o arquivo da fonte; o módulo do outro projeto **não é importado nem executado** (mesmo princípio do
  `bpmn.py` e da regra "a análise não executa o código do projeto"). Ler outro projeto não esbarra na
  cerca da âncora: `hooks/projeto_ativo.py` só vigia `Write|Edit|NotebookEdit`.
- **Nada de segredo sai.** `KEY`/`CIPHERTEXT` nunca impressos; toda conn string em tela ou log passa
  pelo `mask_password` que o template já tem. Nenhum par é copiado pro projeto analisado.
- **Nenhum arquivo de configuração novo**, em lugar nenhum. O ponteiro pra não repetir na regeneração
  (servidor, base, ambiente e **qual projeto teve o par reaproveitado** — caminho, nunca valor) fica
  na seção *Dados* do `docs/ARQUITETURA.md`, que já existe e já é o dossiê descritivo versionado.

Premissa do owner que o kit não verifica: "as credenciais são as mesmas" pressupõe que o login tem
leitura **na base nova**. Se não tiver, o erro é de **permissão** do SQL Server (não de rede, não de
credencial) e o script diz isso em pt-BR; o conserto é do owner. O erro de conexão sai em quatro
classes: **REDE**, **TLS** (SQL Server antigo sem TLS 1.2, ou certificado — o script sempre pede
`Encrypt=yes`), **CREDENCIAL** e **PERMISSÃO**; par Fernet que não decripta e `--fonte` ilegível
viram mensagem clara, nunca traceback.

### 3. Coleta: só catálogo

**Nenhum dado de negócio é lido** — nada de `SELECT *` em tabela da aplicação nem amostra de linha.
Numa seguradora isso não é detalhe, e é garantido pela **ausência** de query de dados no gerador,
travada por teste.

- **Estrutura** — `sys.tables` + `sys.columns` (tipo, nullability, identity, default) · PK/unique
  (`sys.key_constraints`) e FK (`sys.foreign_keys`), que é o que reconstrói o modelo de dados de um
  sistema sem documentação · índices (nome, colunas, único/clustered) · **contagem de linhas** por
  `sys.dm_db_partition_stats` (estimativa de partição, custo ~zero — não `COUNT(*)`; exige `VIEW
  DATABASE STATE` e, sem ela, degrada pra lacuna), que responde "o que era usado × o que nasceu
  morto".
- **Código dentro do banco** — procedures, functions, views e **triggers**: nome, parâmetros
  (`sys.parameters`) e **corpo** (`sys.sql_modules.definition`) · dependências
  (`sys.sql_expression_dependencies`: proc→tabela, proc→proc) · `create_date`/`modify_date` de
  `sys.objects`, que num sistema parado há 6 anos diz **quando ele parou** e o que foi mexido por
  último.
- **Fronteira do sistema**, degradando com elegância se faltar permissão — `sys.servers` (**linked
  servers** revelam integração, e alimentam as *Conexões* do `MAPA.md`) · `msdb.dbo.sysjobs` (**jobs
  do Agent**; em legado, metade do sistema costuma ser job agendado que ninguém lembra — o texto do
  passo **não** vai pra saída, pode ter segredo: só job, passo e objetos do inventário que ele chama).

Honestidades obrigatórias: procedure `WITH ENCRYPTION` devolve `definition` **NULL** e vai listada
como lacuna nomeada (`<objeto> — corpo criptografado, não extraído`); corpo `NULL` **sem** criptografia
é falta de `VIEW DEFINITION` e vira lacuna com esse nome (`OBJECTPROPERTY(..., 'IsEncrypted')` separa
os dois casos). Silêncio lido como "cobri tudo" é o pior resultado — mesma regra que a `analise` já aplica ao
código.

Teto: corpo vai **inteiro** pros `.sql` (é a fonte, não se trunca); o `banco.md` é só listas e
tabelas, nunca corpo. `--max-objetos` (default 2000) **para e diz** em vez de despejar um warehouse.

### 4. Cruzamento: "citado no código" × "sem citação"

Busca textual do nome de cada objeto nos arquivos do projeto — **funciona em qualquer linguagem**, que
é o que faz isso servir pro C# antes da feature de C#.

Casa sem diferenciar caixa, com fronteira de palavra, nas três formas da vida real: `ConsultaApolice`,
`dbo.ConsultaApolice`, `[dbo].[ConsultaApolice]` (a busca é por **token**, então as três caem no mesmo
nome). Procura nos arquivos de **código** do projeto (`.md` fica fora: doc não é código, e
`ARQUITETURA.md`/`banco.md` repetem os nomes), menos `bin`, `obj`, `packages`, `.vs`, `.git`,
`node_modules` — **e menos a própria saída em `docs/banco/`**: sem essa exclusão o inventário se
autoconfirma, porque os `.sql` que ele acabou de gravar contêm todos os nomes.

Três classificações, não duas — e uma quarta, de honestidade:

- **citado no código** — com `arquivo:linha` das 3 primeiras ocorrências
- **citado só no banco** — chamado por outra procedure, trigger ou job (`sys.sql_expression_dependencies`,
  `sysjobs`), mas não pelo C#. Não é morto; é chamado por dentro
- **sem citação** — não apareceu em lugar nenhum
- **não cruzado** — nome fora do padrão de identificador (`[Minha Proc]`, com espaço ou acento): a
  busca por token não o enxerga, e isso é dito em vez de virar *sem citação*

Os dois erros do método, declarados na saída: *falso positivo* de nome genérico (`Cliente`, `Status`,
`Log`, `Usuario`) casando com variável ou classe C# sem relação → sai marcado **casamento fraco,
conferir**; e *falso negativo*, o grave — SQL montado em runtime por concatenação
(`"sp_" + ramo + "_Consulta"`), nome vindo de tabela de parâmetros ou `.config`, mapeamento por ORM
que nunca escreve o nome literal.

Daí a frase que vai **na primeira linha da seção**, no `banco.md` e no `ARQUITETURA.md`:

> **"Sem citação" não significa "pode apagar"** — significa "não encontrei citação textual". Nome
> montado em runtime não aparece nesta busca.

Existe porque o próximo leitor desse arquivo provavelmente é um assistente, e assistente que lê
"órfão" sem essa frase propõe `DROP PROCEDURE`.

### 5. Saída e segredo

| destino | o que é | git |
|---|---|---|
| `docs/banco.md` | retrato em texto: listas, tabelas, contagens, cruzamento, lacunas — o que o **assistente** lê | **fora** (`/docs/banco.md` ancorado no `.gitignore`) |
| `docs/banco/<schema>.<objeto>.sql` | os corpos, um arquivo por objeto, **UTF-8 com BOM** (base brasileira de 2019: comentário com acento; sem BOM o SSMS antigo e o VS embaralham) | **versionado** |
| `docs/ARQUITETURA.md` (seção *Dados*) + `MAPA.md` (*Conexões*) | o destilado: contagens, modelo em prosa, linked servers e jobs | versionado |

**Sem HTML na v1** (corte consciente): os outros geradores têm par texto/HTML porque o desenho *é*
visual; aqui o visual é do `/mss-spec:documentacao`, alimentado pelo `banco.md`.

**Varredura de segredo antes de gravar cada `.sql`** — não é opcional, porque corpo versionado que
leva segredo fica no histórico pra sempre. Varre o **corpo inteiro** (não linha a linha: `EXEC
sp_addlinkedsrvlogin` com os argumentos na linha de baixo é estilo comum) e cobre: `PWD=`/`Password=`
em conn string, qualquer `PASSWORD = '...'` (`WITH PASSWORD`, `ENCRYPTION BY PASSWORD`,
`OLD_PASSWORD`), variáveis `@senha`/`@pwd`/`@password` recebendo literal, `sp_addlinkedsrvlogin`
(nomeado e posicional, com argumentos estruturados pra não invadir a instrução seguinte),
`sp_addlogin`, `sp_password`, `IDENTITY=`/`SECRET=`, senha no provider string do `OPENROWSET`, e
`-P senha` quando há `bcp`/`sqlcmd`/`osql`/`isql`/`xp_cmdshell` por perto. Falso positivo é aceitável;
falso negativo vai pro git. Achou → grava o corpo **com o valor mascarado**
(`PWD=***REMOVIDO PELO INVENTARIO***`), põe comentário de cabeçalho dizendo que houve remoção e em
que linha, e **lista no relatório** o objeto e o tipo — nunca o valor. Mascarar em vez de pular
porque a regra de negócio é o que se quer preservar; mascarar em vez de gravar cru porque o arquivo
vai pro git. O arquivo é documentação, não script executável, e o cabeçalho diz isso.

**Regeneração:** `banco.md` sobrescrito inteiro (é retrato); os `.sql` sobrescritos, e o `git diff`
passa a mostrar **o que mudou no banco** entre duas rodadas. Objeto que sumiu do catálogo tem o
`.sql` removido e o fato reportado — arquivo velho que fica pra trás mente, e o histórico do git é o
rollback (mesma regra da `analise`).

**Brownfield — só mexe no que é seu.** Todo `.sql` gerado começa com a marca
`-- [inventario-banco]` e o `banco.md` com `<!-- [inventario-banco] ... -->`. Só arquivo com a marca é
sobrescrito ou removido: um `docs/banco.md` que o time já tinha faz o script **parar sem gravar**
(use `--out`), e `.sql` alheio em `docs/banco/` fica intocado e listado no relatório.

**O que o script não faz:** `git add`/commit (ato do owner; `hooks/git_publicacao.py` já barra push) e
editar o `.gitignore` sozinho — ele imprime a linha e a `analise` pergunta uma vez antes de
acrescentar, porque em brownfield o `.gitignore` é arquivo pré-existente do projeto.

### 6. Testes (`tests/test_inventario_banco.py`)

Testável **sem banco**: camada fina de conexão, e o resto funções puras alimentadas por **cursor
falso**. Carregador por `importlib` como o `test_bpmn.py` — com `sys.modules[spec.name] = mod` antes
do `exec_module` e **sem** `from __future__ import annotations` no gerador, senão a 1ª `@dataclass`
estoura no Python 3.14 (memória `project_importlib_dataclass_precisa_de_sys_modules`).

- **importável sem `pyodbc` nem `cryptography`** (import tardio, como o `get_connection.py` já faz)
- **somente-leitura travado**: nenhuma constante de query contém `INSERT`, `UPDATE`, `DELETE`, `DROP`,
  `ALTER`, `CREATE`, `TRUNCATE`, `MERGE` ou `EXEC`
- **nenhum dado de negócio**: toda query referencia só `sys.*`, `INFORMATION_SCHEMA.*`, `msdb.dbo.sys*`
- **credencial**: `--fonte` ganha da variável quando os dois existem, com aviso · `--fonte` + `--base` troca o
  `Database=` (e acrescenta quando não havia) · **leitura estática provada** — fixture de
  `get_connection.py` com `raise` no topo é lida normalmente (se importasse, quebraria) · nada
  resolvido → erro nomeia o que faltou e **não contém** host/porta/base inventados · senha da fixture
  nunca aparece no relatório
- **varredura de segredo**: corpo com `PWD=<senha da fixture>` → o `.sql` tem `***REMOVIDO` e **não**
  tem a senha; o relatório nomeia o objeto, não o valor
- **cruzamento**: citado no `.cs` → *citado no código* com `arquivo:linha` · chamado só por outra
  procedure → *citado só no banco* · nenhuma citação → *sem citação* · **anti-autoconfirmação** —
  fixture cuja única ocorrência está no próprio `docs/banco/*.sql` gerado tem que sair *sem citação* ·
  nome genérico → *casamento fraco* · nome fora do padrão de identificador → *não cruzado*
- **honestidade travada**: `definition` nulo vira lacuna nomeada, e o rótulo separa criptografado de
  falta de `VIEW DEFINITION` · contagem de linhas sem `VIEW DATABASE STATE` degrada pra lacuna ·
  erro de permissão em `msdb` degrada e vira lacuna (falha **aberta**, como o `bpmn` faz com arquivo
  que não parseia) · presença da frase *"sem citação não significa pode apagar"* no `banco.md`
  (mecanismo do `test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega`)
- **teto e regeneração**: acima de `--max-objetos` para sem gravar nada · objeto sumido tem o `.sql`
  removido e reportado
- **marca de autoria**: `banco.md` alheio → para sem gravar · `.sql` alheio preservado e listado ·
  `--proj .` sai com o nome do projeto no título (`Path(".").name` é vazio — caso F-016)
- **wiring**: o comando novo entra no `test_smoke_kit.py` como os outros; a `analise` tem teste de que
  o passo *Dados (banco vivo)* cita o gerador e a pergunta de credencial
- **contagem de comandos travada** (pedido do owner nesta sessão): teste novo prende o número escrito
  no `docs/COMO-FUNCIONA.html` ao número real de arquivos em `commands/`. O MAPA registra que essa
  contagem já ficou **4 comandos defasada** e foi consertada à mão; o 25º comando repetiria isso.

## Fora de escopo
Ler dado de negócio (amostra de linha, `SELECT *` em tabela da aplicação) · `COUNT(*)` real em vez da
estimativa de partição · gerar par Fernet novo ou gravar credencial em qualquer arquivo do projeto
analisado · arquivo de configuração próprio pro inventário (`docs/banco.md` como config, ponteiro no
`CLAUDE.md`, subcomando do `/mss-spec:banco`) — o ponteiro vive no `ARQUITETURA.md` · HTML na v1 (o
visual é do `/mss-spec:documentacao`) · `/mss-spec:banco` virar porta de credencial do inventário (ele
é **prescritivo**, o inventário é **descritivo** — mesma fronteira de `ESTRUTURA.md` × `ARQUITETURA.md`)
· executar o código do projeto analisado · escrever no banco, em qualquer hipótese · Postgres e
Oracle na v1 (a cadeia de credencial já cabe; o catálogo é outro) · decidir o que é morto e propor
`DROP` · cobertura C# completa (`Program`/`Startup`, controllers, `.csproj`, rotas) — **item separado
do INDEX**, esta feature só traz a detecção mínima pro gatilho.

## Histórico
- 2026-09-22 — desenhado: o owner precisa documentar um sistema C# parado há 6 anos com os dados num
  SQL Server D0, e perguntou qual comando usar. A `analise` era a resposta certa e **incompleta** — o
  kit tem o conector (`get_connection.py`, usado em Transportes V2 e Jedai), mas nenhum comando manda
  a análise usá-lo. Desenho **A** (gerador próprio + comando fino, entrada automática pela `analise`)
  aprovado contra **B** (fase em prosa dentro da `analise`: não-determinística, engorda o 2º maior
  comando, que já está na fila de poda) e **C** (subcomando do `/mss-spec:banco`: mistura prescritivo
  com descritivo). Escopo dividido a pedido da regra "um assunto por janela": banco vivo primeiro, C#
  completo depois. Decisão de credencial fechada pela memória `credencial-reusar-env-precedente`
  quando o owner respondeu "não sei" — base nova **não mapeada**, mesmo servidor e mesmo login.
- 2026-09-22 — plano de implementação (`docs/superpowers/plans/2026-09-22-inventario-banco.md`)
  fechou 7 detalhes que o desenho deixou abertos: `--par`, precedência flag > variável (o § 6 dizia
  o contrário do § 2), linhas como opcional, `.md` fora do cruzamento, classe *não cruzado*,
  criptografado × falta de `VIEW DEFINITION`, marca de autoria nos arquivos gerados (brownfield).
- 2026-09-22 — implementado (0.28.0): `templates/inventario_banco.py` + `tests/test_inventario_banco.py`
  (91 testes, cursor falso), `/mss-spec:inventario-banco`, passo *Dados — banco vivo* na `analise`,
  `COMO-FUNCIONA.html` com os 5 cards que faltavam e contagem travada nos 3 lugares onde aparece. A
  revisão por tarefa mudou o gerador em relação ao plano: `mask_password` respeita valor entre
  `{chaves}` (vazava o fim da senha), erro de conexão ganhou a classe **TLS**, e a varredura de segredo
  foi refeita pra varrer o corpo inteiro — 5 formas de segredo vazavam, provadas por teste. **Falta o
  dogfood** no projeto C# contra o D0: conferir o regex do par (`<DEV|HML|PROD>_<BASE>_<KEY|CIPHERTEXT>`,
  tirado do molde do kit) e valor montado com `+`/`.encode()` no `get_connection.py` real (hoje some
  em silêncio), e se o cursor do pyodbc segue usável depois de falta de permissão no `msdb`.
