<!-- MODELO de índice de memória — copie para `memory/MEMORY.md` (dentro do repo do projeto).
     Regras deste índice:
     - Só ponteiros de 1 linha, NUNCA o conteúdo da memória em si.
     - Mantenha enxuto (até ~150-200 linhas); quando crescer demais, rode a skill
       `anthropic-skills:consolidate-memory` para mesclar duplicatas e podar entradas mortas.
     - Cada linha aponta para um arquivo em `memory/` com frontmatter:
         ---
         name: slug-curto
         description: 1 linha objetiva — usada pra decidir relevância
         metadata:
           type: user | feedback | project | reference
         ---
       e corpo curto (para feedback/project: regra/fato + **Why:** + **How to apply:**).
     - Linke memórias relacionadas com [[slug-do-outro-arquivo]].
     - Organize por tópico, não por data. Apague/atualize entradas que ficaram erradas. -->

# Memória do projeto — índice

<!-- Formato de cada linha: - [Título](<arquivo>.md) — gancho de uma frase -->

## Como trabalhar neste projeto

- [UI própria é intocável](ui-propria-intocavel.md) — `chat.html`/`chat_v2.html` são autorais; o design system do kit não se aplica nem se sugere
- [Esta pasta é a que evolui](esta-pasta-e-a-que-evolui.md) — o vizinho `V2 - IA Bot Agent` é histórico; mudança de código nasce aqui, e desde 2026-07-28 há git próprio

## Ambiente e build

- [Build quebra por CA desatualizada](build-quebra-por-ca-desatualizada.md) — `CERTIFICATE_VERIFY_FAILED` no pypi.org não é proxy: copie o `certs/corp-ca.pem` de um projeto MSIG que buildou esta semana
- [CA corporativa no binário Go](ca-corporativa-no-binario-go.md) — `x509: unknown authority` em app Go: monte o `corp-ca.pem` dentro de `/etc/ssl/certs/` (soma às raízes); no evolution-go o sintoma se disfarçava de "QR code limit reached"
- [Proxy do Docker quebra chamada entre containers](proxy-do-docker-quebra-chamada-entre-containers.md) — 504 de container para container por nome é `no_proxy` incompleto; e o `wget` do busybox ignora `no_proxy`, dando falso-negativo no teste
- [PowerShell quebra argumento nativo](powershell-quebra-argumento-nativo.md) — commit, SQL e `python -c` com aspas falham no PS 5.1, e heredoc do Bash com `python -` mangla `\n`; passe por arquivo (`git commit -F`, `.sql` via stdin, script `.py` no scratchpad)
- [`.dockerignore` não aceita comentário inline](dockerignore-nao-aceita-comentario-inline.md) — comentário no fim da linha vira parte do padrão: o arquivo parece proteger e não protege, e foi assim que o `.env` com segredos entrou na imagem que iria ao ACR
- [`print` não aparece em contêiner sem `PYTHONUNBUFFERED`](print-em-container-sem-pythonunbuffered.md) — stdout fica preso no buffer; o `logging` (stderr) aparecer dá a falsa impressão de log completo, e o sintoma imita bug de lógica
- [Contêiner sem `TZ` roda em UTC](container-sem-tz-roda-em-utc.md) — teste que compara hora local com UTC vira falso-negativo: passa pelo compose (que define `TZ`) e falha no `docker run` puro
- [Docker Desktop injeta proxy em minúsculas](docker-desktop-injeta-proxy-em-minusculas.md) — `http_proxy` vem de fora do repo em **todo** contêiner, e Python/axios priorizam as minúsculas: declarar só as MAIÚSCULAS no compose não vence. Funciona na empresa, quebra em casa
- [Clientes HTTP divergem no `no_proxy`](clientes-http-divergem-no-no-proxy.md) — `fetch` do Node ignora proxy (falso-positivo), `wget` do busybox ignora `no_proxy` (falso-negativo): teste com o cliente que o app usa, ou com dois de comportamento oposto
- [Erro de infra esconde erro de aplicação](erro-de-infra-esconde-erro-de-aplicacao.md) — conserte a camada de baixo e espere o **próximo erro**, não o sucesso; e compare logs de datas diferentes para saber se o problema é novo
- [DNS não viaja com a aplicação](dns-nao-viaja-com-a-aplicacao.md) — integrar VNet faz o Web App herdar o DNS dela e perder `*.azurewebsites.net`/`api.openai.com` (`ENOTFOUND`): o conserto é `WEBSITE_DNS_ALT_SERVER=168.63.129.16` **com restart**, e mesma VNet resolve rota, não nome
- [Sufixo do Web App e token morrem juntos](sufixo-do-webapp-e-token-morrem-juntos.md) — recriar o recurso troca o hostname (sufixo aleatório) **e** invalida o token da instância; o 401 só aparece depois de consertar o `ENOTFOUND`
- [VNet não torna a chamada privada](vnet-nao-torna-a-chamada-privada.md) — `403` + página `Web App - Unavailable` é Restrição de Acesso da plataforma: sem Private Endpoint só existe a porta pública, e mesma VNet é rota possível, não caminho usado
- [Cold start estoura timeout de vizinho](cold-start-estoura-timeout-de-vizinho.md) — o Chatwoot boota em 1min40 e o `timeout=15` do cliente (dimensionado para rede Docker) morre: ligue Always On **antes** do 1º teste de integração
- [Endereço truncado com reticências](endereco-truncado-com-reticencias.md) — o Portal abrevia o hostname e o `...` vira **valor literal** ao copiar; 3ª ocorrência no projeto, e num campo de texto se detecta com `Ctrl+A`
- [pyodbc.drivers() não prova carga](pyodbc-drivers-nao-prova-carga.md) — só lê o registro, sem dlopen: "Can't open lib ... file not found" pode ser dependência ausente com o arquivo existindo; a prova é um connect que falhe por REDE, e o diagnóstico é `ldd`
- [autoremove leva dependência de runtime](autoremove-leva-dependencia-de-runtime.md) — purge+autoremove no Dockerfile removeu a libgssapi que o msodbcsql17 usa sem declarar; limpeza de imagem só com prova de carga depois
- [App Setting faltando cai no default](app-setting-faltando-cai-no-default.md) — chave ausente não dá erro: vale o `os.getenv(...) or "<default>"`, e os defaults daqui apontam pra **produção**; confira a lista contra o código, nunca contra ela mesma
- [Conn string da Azure vem de App Setting](conn-string-da-azure-vem-de-app-setting.md) — nome curto (MSSQLD0) cifrado no código não resolve da VNet; padrão Jedai: string inteira com `Server=<IP>` via env vencendo o embutido, e o log dizendo a fonte
- [dns_search inerte sem ndots](dns-search-inerte-sem-ndots.md) — nome curto que resolve no host e falha só no contêiner: o Docker injeta `ndots:0` e a lista de search nunca é aplicada; o par é `dns_search` + `dns_opt: ndots:1`, e o disfarce é "Login timeout" do ODBC
- [Rota Azure→on-prem é por faixa](rota-azure-onprem-e-por-faixa.md) — timeout de IP interno a partir de Web App/VNet: 10.170.x alcança e 10.64.x não; a prova que convence é comparativa (destino que funciona do mesmo lugar) e o pedido à infra leva subnet+IP+porta
- [Mount de código no Docker pelo Git Bash](mount-de-codigo-no-docker-pelo-git-bash.md) — ao montar a fonte com `-v` no bash do Windows: `${PWD}` vira `/c/...` e o mount cai em silêncio ("No such file" no teste novo); use `$(pwd -W)`, ou o PowerShell do `PLANO-TESTE.md`

## Integrações

- [Workflow n8n vive no banco](n8n-workflow-vive-no-banco.md) — está no Postgres (`workflow_entity`), não em arquivo: "o fluxo sumiu" é o esperado sem export; liste por SQL antes de recriar. **E há mais de uma instância n8n na máquina** — a deste projeto é o container `n8n` em :5678
- [apikey da Evolution sai no export do n8n](apikey-da-evolution-sai-no-export-do-n8n.md) — importar o JSON troca o token por placeholder e cria nós duplicados: o envio que funcionava dá 401. Avise o checklist da UI **antes** da explicação; na Evolution 401 é credencial, 404 é rota
- [Executions vazia no n8n engana](n8n-executions-vazia-engana.md) — sem *Save successful executions* o workflow roda sem deixar registro; confirme pelo destino da chamada, não pela aba do n8n
- [Quota da OpenAI com /v1/models 200](openai-quota-com-models-200.md) — `429 insufficient_quota` com models respondendo = cobrança, não rede; "spend limit" no painel **não** é saldo
- [Marcação de canal em campo livre](marcacao-de-canal-em-campo-livre.md) — `*` no nome vindo do Chatwoot vira negrito que nunca fecha no WhatsApp; e exibir um campo que só ia pro banco transforma "injetar texto" em "escolher a identidade exibida"
- [API pública do Chatwoot não consulta contato](chatwoot-api-publica-nao-consulta-contato.md) — ela é de **escrita**: `GET .../contacts?identifier=` dá 404 e isso é o esperado, não erro de config; prove o inbox e o time pela Platform API
- [Contrato para terceiro declara o limite](contrato-para-terceiro-declara-o-limite.md) — doc de integração que só descreve o caminho feliz faz o parceiro desenhar errado; e o que **não** entra: numeração de revisão, changelog e stack (linguagem, framework, nº de processos)
- [Doc gerada mente sobre a rota](doc-gerada-mente-sobre-a-rota.md) — o nome do endpoint vem da tabela de rotas do fonte, não do swagger: 3 fontes da doc do evolution-go concordavam e as 3 estavam erradas (todas derivadas da mesma anotação velha); numa API, **404 é rota, 401 é credencial**
- [Mídia do WhatsApp não tem `conversation`](midia-do-whatsapp-nao-tem-conversation.md) — filtro "tem texto não-vazio" descarta **todo** PDF e foto em silêncio; a legenda vive dentro do `imageMessage`, e o arquivo chega criptografado
- [Chave por função, não por sistema](chave-por-funcao-nao-por-sistema.md) — reusar o token do vizinho não é economia, é acoplamento: girar um derruba o outro, e a chave com nome da outra feature faz a sua parecer dependente dela
- [Resolvedor de token prefere processo ao header](resolvedor-de-token-prefere-processo-ao-header.md) — ao chamar `validar_corretor` (ou função que "resolve" credencial sozinha) numa rota que atende mais de um corretor: a ordem é cache de processo → header, então o par do corretor B sai validado com o token do A; passe `token=` explícito
- [Perfil do WhatsApp não é identidade](perfil-do-whatsapp-nao-e-identidade.md) — ao exibir/saudar pelo `user_name` de sessão whatsapp: a .Blip manda o **nome de perfil** (campo livre; chegou "Maganha"); identidade vem do cadastro pelo telefone, e o cadastro VENCE o declarado
- [Sessão do WhatsApp vive até o restart](sessao-whatsapp-vive-ate-o-restart.md) — ao cachear algo "uma vez por sessão" no canal whatsapp: a sessão é `wa_<telefone>` em memória de processo, sem expiração — "por sessão" = "até o restart"; todo cache ali precisa de TTL (J4: 20 min resultado / 5 min falha, relógio injetável no teste)
- [Chatwoot deduplica contato por telefone](chatwoot-deduplica-contato-por-telefone.md) — ao criar contato pela API pública: mandar `phone_number` (E.164) é o que evita contato novo a cada sessão; **e-mail não vai** (fundiria pessoas); 4xx com telefone → refazer sem
- [COD_CORR não identifica a pessoa](cod-corr-nao-identifica-a-pessoa.md) — ao saudar/personalizar a partir de lista por `COD_CORR`/CNPJ: é a corretora inteira (20 pessoas no mesmo código), a 1ª linha não é quem está na tela; identidade por pessoa só do que a sessão forneceu (nome digitado, telefone do WhatsApp)
- [Código do Portal é login, não COD_CORR](codigo-do-portal-e-login-nao-cod-corr.md) — ao usar o `codigoCorretor` da credencial (Portal, modal dev, `PORTAL_CODIGO`) como chave do TKGS_CORP: é **login** da `ALC_USUARIO` (vários por corretor); o `COD_CORR` resolve-se pela `cod_externo` dentro do CNPJ. O `GerarToken` aceita os dois e o `ValidarCorretor` só o `COD_CORR` — por isso a confusão passa verde
- [Estado do WhatsApp precisa de Postgres no App Service](estado-do-whatsapp-precisa-de-postgres-no-app-service.md) — sem `POSTGRES_AUTH_DB` o device do whatsmeow vive em disco efêmero e morre no restart: o sintoma é loop de QR, e o manager exibe "Conectado" enquanto o log diz `LoggedOut`
- [Entrega assíncrona não é entrega](entrega-assincrona-nao-e-entrega.md) — `202` com corpo `{}` e nó verde no n8n é **aceito**, não entregue: a falha vem depois e só o parceiro vê; o `msg_id` é a chave pra cobrar, e confira antes o **valor** dos campos derivados do payload dele
- [Identificador de sessão é o contrato](identificador-de-sessao-e-o-contrato.md) — sem `session_id` o `/chat` inventa um uuid **por mensagem**: cada turno vira conversa nova, sem memória, sem handoff e sem endereço de volta
- [Mídia do parceiro chega como texto](midia-do-parceiro-chega-como-texto.md) — a .Blip hospeda o arquivo no storage dela e entrega `{"type","uri"}` no campo de texto: o anexo já viajava e o especialista via o JSON cru
- [URL com redirect não serve para terceiro](url-com-redirect-nao-serve-para-terceiro.md) — o Active Storage responde 302 para endereço que expira em 5 min; e ausência de `GET` no log da app é "barrado antes da aplicação", nunca "chegou e falhou"
- [Quem baixa a mídia é a Meta](quem-baixa-a-midia-e-a-meta.md) — o parceiro só repassa: quem faz o `GET` na URL é a Meta, que **não publica faixa de IP** — "liberar o IP deles" é via inexistente, e nenhum log de app mostra IP de origem em App Service
- [Nome do header não é o apelido da credencial](nome-do-header-nao-e-apelido-da-credencial.md) — no n8n o campo *Name* do Header Auth é o cabeçalho HTTP (`Authorization`); o apelido ali dá `Header name must be a valid HTTP token`, e `Bearer` ≠ `Key` dá 401
- [CRM www4 tem dois nomes](crm-www4-dois-nomes.md) — `ms-seg.com.br` é só interno, `msig.com.br` é o público (Cloudflare); mesmo IP por dentro (split DNS), e o D0 (`www4-d0k`) não tem nome público
- [Token de D0 vale em produção](token-d0-vale-em-producao.md) — a direção contrária não vale; não generalizar regra bidirecional de medição unidirecional
- [2ª via: o caminho do PDF vem de tabela](documento-2avia-caminho-vem-de-tabela.md) — "Documento não encontrado" com arquivo no share = `DS_PATH_ARQUIVO` na `TB_EMS_DOC_IMPRESSOES`, não rede

## Padrões e ferramentas

- [Mapa neural é o atalho do todo](mapa-neural-e-o-atalho-do-todo.md) — `docs/mapa-neural.md` indexa as 4 dimensões do projeto (arquitetura · 24 rotas · memórias/decisões/diário · conexões) + as relações entre memórias; derivado e gitignorado, regenere com `/mss-spec:mapa-neural`
- [Denylist de linguagem natural não segura](denylist-de-linguagem-natural-nao-segura.md) — proibir "famílias de frase" do LLM vaza na rodada seguinte com outra família e o mesmo defeito; em texto **decorativo** o que resolve é texto **fixo no servidor**
- [Log por sessão é melhor que o do kit](log-por-sessao-melhor-que-o-do-kit.md) — 1 arquivo por conversa + truncamento de payload; candidato a virar melhoria no `mss-spec`
- [Wrapper de módulo esconde parâmetro novo](wrapper-de-modulo-esconde-parametro-novo.md) — classe ganha param, wrapper não, `except` do chamador engole: a `historico_chat` ficou **um mês** sem gravar em silêncio; case os kwargs por `inspect`
- [Hora ingênua em timestamptz](hora-ingenua-em-timestamptz.md) — `datetime.now()` sem fuso em coluna `timestamptz` = 3 h de erro calado; o sintoma é assimetria entre tabelas, porque quem usa `DEFAULT now()` escapa
- [Webhook reentrega, e idempotência é do serviço](webhook-reentrega-e-idempotencia.md) — entrega dupla é a **mesma URL cadastrada 2×** (global + instância), não 2 eventos: conte os `webhook sent successfully` por dispatch. E reserve a mensagem **antes** de processar, sob lock
- [Teste sequencial não prova concorrência](teste-sequencial-nao-prova-concorrencia.md) — idempotência verificada com `curl` em sequência ficou verde um dia inteiro sem nunca funcionar; teste de corrida precisa de threads largando juntas e de processamento lento no meio
- [gunicorn não executa o `if __name__ == "__main__"`](gunicorn-nao-executa-o-if-name-main.md) — o app é importado, não executado: banner e setup que vivem ali desaparecem. Detecte por `sys.modules`, **não** por `SERVER_SOFTWARE`, que não existe no processo
- [Estado em memória limita a 1 worker](estado-em-memoria-limita-a-um-worker.md) — cache de menu, memória de sessão e token vivem em `dict` de processo; com 2+ workers quebram **em silêncio**, e o `-w 1` é requisito, não tuning
- [Ausência de log é sinal](ausencia-de-log-e-sinal.md) — a linha que **não** apareceu discrimina: "recebeu e não tentou entregar" é estado perdido, "tentou e falhou" é rede — sintoma externo idêntico, camadas diferentes
- [Rodou sem erro não é prova](rodou-sem-erro-nao-e-prova.md) — um `.sql` executou só parte das instruções, sem erro, por 3 rodadas (causa não identificada); o sinal é **um** aviso `already exists` num arquivo com 10 instruções, e a garantia é a consulta que olha o estado
- [`CREATE IF NOT EXISTS` não migra](create-if-not-exists-nao-migra.md) — em tabela que já existe ele relata sucesso e **não acrescenta coluna**; preparar ambiente é `CREATE` **+** `ALTER`, um por coluna, e a garantia é a consulta que olha o banco
- [Postgres da Azure só pelo proxy SOCKS](postgres-da-azure-so-pelo-proxy-socks.md) — TCP 5432 dá timeout do host e do contêiner; o DBeaver chega por `10.170.200.1:8080`, e a `libpq` em C ignora proxy do Python — a saída é encaminhador TCP
- [DDL versionada não cobre o esquema todo](ddl-versionada-nao-cobre-o-esquema-todo.md) — em banco compartilhado, `sql/` cobria 2 das 6 tabelas; e a ordem dos scripts só se valida **rodando** num Postgres limpo, porque `LIKE <tabela do outro sistema>` não aparece na leitura
- [Rewrite de host no código quebra em contêiner](rewrite-de-host-no-codigo-quebra-em-container.md) — "override pra dev local" que troca `rails:` por `localhost:` é `if` de ambiente escondido, e em contêiner aponta pro próprio contêiner: a integração ficou meses morta em silêncio
- [Config lazy que congela vazia](config-lazy-que-congela-vazia.md) — marcar "carregado" sem achar nada desliga a feature pelo resto da vida do processo; só congele quando a config estiver completa
- [Booleano de config não diz QUAL config](booleano-de-config-nao-diz-qual-config.md) — `configurado: True` confirma que há chaves, não que apontam pro lugar certo; logue base/conta/id (prefixo), nunca token
- [Erro HTTP não serve de controle de fluxo](erro-http-nao-serve-de-controle-de-fluxo.md) — 4xx para o nó do n8n "parar sozinho" o faz **falhar**: o workflow morre ali e o efeito já aplicado (o "digitando") nunca é desfeito. "Não fazer nada" é 200 com corpo que diz isso
- [Critério de leitura virando ação](criterio-de-leitura-virando-acao.md) — filtro frouxo inofensivo num caminho que só exibe passa a **enviar** coisa errada quando reusado num caminho que age; reveja cláusula por cláusula na promoção, e teste com o caso hostil
- [Confirmar a branch na hora do commit](confirmar-a-branch-na-hora-do-commit.md) — a branch lida na partida é foto, não fato: ela muda quando é apagada OU quando **o owner opera o git no mesmo diretório** (2 reincidências); leia a saída do `git commit` e confira `--show-current` antes de todo add/commit em sessão com git compartilhado
- [Teste que lê arquivo fora da imagem](teste-que-le-arquivo-fora-da-imagem.md) — `n8n/` e `.env.example` não entram na imagem: verde/vermelho **inverte conforme onde a cópia velha mora** (inclusive o "verde de mentira": TDD sem o override dev roda a suíte antiga de dentro da imagem). Pule dizendo que pulou, e rode nos dois modos antes de fechar
- [`hidden` depende do preflight da CDN](hidden-depende-do-preflight-da-cdn.md) — ao esconder por `el.hidden` elemento cuja classe define `display`: sem regra `[hidden]` própria, quem esconde é o Tailwind da CDN — bloqueada na rede corporativa, a peça "escondida por flag" aparece; regra explícita `#id[hidden]{display:none !important}`
- [Rebuild derruba estado de sessão](rebuild-derruba-estado-de-sessao.md) — `up -d --build` apaga o `_sessions` e a aba aberta traduz isso como "encerrado pelo especialista": parece regressão, e a prova de que não é está no access log (requisição que não aparece nunca chegou)

## Como eu devo trabalhar (correções do owner)

- [Provar que não foi a sua mudança](provar-que-nao-foi-a-sua-mudanca.md) — quando o owner atribui uma quebra ao seu deploy: medir, não argumentar. Diff do arquivo do sintoma → **reverter e republicar** → comparar dependências → probe isolando camadas; e o contêiner que não reiniciou é testemunha (`docker inspect` + `docker logs` desde o boot)
- [Fonte viva antes do documento](fonte-viva-antes-do-documento.md) — chutei o modelo do LLM 2× lendo README (dois 403); `models.list()` respondia em 10s. Havendo API/banco/config que responde, pergunte a ela antes de decidir por texto
- [Owner NÃO executa comando contra a Azure](owner-nao-executa-comando-contra-azure.md) — diagnóstico de nuvem é Portal, Log Stream, DBeaver e navegador; se a informação só existe por API, faça o app **logar** e peça a leitura

- [Não investigar infra vizinha — perguntar](nao-investigar-infra-vizinha-perguntar.md) — configuração de outro projeto (Evolution, n8n, Chatwoot) não se descobre por `docker inspect`/banco: pergunte ao owner, senão a dedução parcial vira "evidência" errada. O `evolution-go` vive em `C:\Ronaldo\_Mitsui\Python\evolution-go`
- [Perguntar como o owner acessa o ambiente](perguntar-como-o-owner-acessa-o-ambiente.md) — `<a confirmar>` não substitui pergunta: deduzi obstáculo de VPN/firewall para um banco que ele acessa pelo DBeaver, e o roteiro acabou apontando para a ferramenta errada
- [Subida não pode depender de build](subida-nao-pode-depender-de-build.md) — acrescentei `--build` ao atalho de subida "para proteger" e transformei falha de rede em "nada sobe"; proteção que cria modo de falha novo é regressão
- [Memória antiga pode já ter sido consertada](memoria-antiga-pode-ja-ter-sido-consertada.md) — usei uma memória como diagnóstico de um problema que o código já resolvia e escrevi log duplicado: memória levanta hipótese, o `grep` confirma
- [Resposta curta e ação primeiro](resposta-curta-e-acao-primeiro.md) — em turno de depuração, entregue o valor/comando nas 2 primeiras linhas e o porquê depois; e quando ele já decidiu, execute em vez de oferecer alternativas
- [Severidade exige incidência medida](severidade-exige-incidencia-medida.md) — ler o código prova que algo **pode** acontecer, nunca com que frequência: chamei de "bug vivo, conserte primeiro" o que o `agent_bot_log` mostrou ser 2 em 100 turnos
- [Permissão de janela não vira regra](permissao-de-janela-nao-vira-regra.md) — exceção pontual que o owner libera vale só naquela janela: execute sem re-litigar, não grave como padrão em `.md` e não a estenda depois por conta própria
- [Roteiro de tela precisa ser executado](roteiro-de-tela-precisa-ser-executado.md) — o que eu escrevo sem clicar é o fluxo ideal, não o possível: a interface do DevOps **forçou** exatamente o que o roteiro proibia, e o erro só aparece pra quem executa
- [Doc operacional envelhece por decisão](doc-operacional-envelhece-por-decisao.md) — roteiro apodrece pela decisão revogada, não pelo código: valide contra o `INDEX.md`/decisões, não contra o código, e "já existe" ≠ "está certo"
- [Contar arquivos novos antes de propor](contar-arquivos-novos-antes-de-propor.md) — propus 4 módulos novos onde 1 bastava e o owner cortou; arquivo novo só se justifica por **capacidade que não existe**, não por "testabilidade" ou "fica mais limpo"
- [Não gravar diagnóstico antes da prova](nao-gravar-diagnostico-antes-da-prova.md) — escrevi causa e conserto em 5 `.md` com evidência que provava a **camada**, não a causa; hipótese vive na conversa até o sintoma sumir
- [Assunto encerrado não se reabre](assunto-encerrado-nao-se-reabre.md) — o owner fechou "rede/IP" e eu voltei 3×; quando ele declara um fato do ambiente, ele tem informação que eu não tenho
- [Conferir a data do artefato](conferir-data-do-artefato.md) — li print de véspera como se fosse do teste do dia e conclui que ele não havia aplicado o passo; data/versão antes da conclusão, e "você não fez" é a última hipótese
- [O parceiro tem o registro da falha](parceiro-tem-o-registro-da-falha.md) — em transporte assíncrono a razão exata do erro fica **no lado dele** (`code 81`, `403 Forbidden`): pedir a notificação é o 1º passo, não o último — passei o dia cercando por eliminação com o dado a um pedido de distância
- [Teste só vale se exercitou o caminho](teste-so-vale-se-exercitou-o-caminho.md) — "rodei e não chegou" tem dois significados, e o segundo (o caminho não foi percorrido) produz conclusão **invertida** com cara de evidência
- [Planejamento e código em janelas separadas](planejamento-e-codigo-em-janelas-separadas.md) — reunião com N pontos vira **uma** janela de planejamento (tabela + 1 prompt pronto por janela, em `plans/`) e N janelas de código; nunca "aproveitar" pra começar o item 1 ali — foi o que deixou as últimas janelas improdutivas (2026-09-10)
- [Dizer como voltar à versão anterior](dizer-como-voltar-a-versao-anterior.md) — ao fechar uma feature/pedir merge: declare onde a versão anterior está (`main` intocada + hash, tag `antes-<feature>`, imagem publicada na Azure) e o comando de voltar, antes que o owner pergunte — "pronto" só tranquiliza junto com "e dá para voltar" (2026-09-11)
