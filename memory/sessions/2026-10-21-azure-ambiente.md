# 2026-10-15 a 21 — azure-ambiente: homologação e produção Azure pelo pipeline

**Conversamos.** O owner perguntou se o "TerraForm" resolveria o gargalo de produção (prestador montando à mão,
errando a documentação, rodadas de ajuste) ou se havia algo mais simples pro Azure. Virou o
`/mss-spec:azure-prd` (0.37.0), testado no MSS-UTILS, que foi **ao ar em produção em 2026-10-20** (`/health`
200) pelo pipeline `MSS-UTILS-INFRA`, com aprovação de Marco ou Leandro. Depois, 0.40.0 (lições) e 0.41.0
(renomeado `azure-ambiente`, cria também a homologação).

**Pivôs.**
1. **Terraform → Bicep**: nativo do Azure, sem arquivo de estado; multi-nuvem já era fora de escopo.
2. **Prestador roda um comando → pipeline com botão de aprovação**: o owner preferiu o caminho 2; mesma receita.
3. **Simulação na máquina do owner → simulação no pipeline** (F-036): o MSS-UTILS não tinha `az` e o owner não
   roda comando contra o Azure. No mesmo caso: nome de variável na receita apagaria a senha (`appSettings`
   substitui tudo) → variáveis pelo `app_settings.py`; imagem fixa → lida do Web App; pipeline de código de
   produção suposto → conferido.
4. **Variáveis**: o owner exigiu todas, senha como `*****`; eu alertei que `*****` na receita sobrescreveria a
   senha real numa 2ª execução → `*****` só se não existe, por mescla, e variável fora da lista trava.
5. **Dados de produção perguntados → mapeados no kit**: plano, VNet/subnet e DNS lidos do Whats (já em produção);
   grupo da VNet (`RG-MSSD-PRD`) e do plano (`RG-MSSAI-PRD`) conferidos pelo owner no portal.
6. **"Não está no documento" → "não existe"** (F-037): recomendei não levar a `WEBSITE_DNS_SERVER`; o portal
   mostrou que produção tem, com o mesmo IP.
7. **1ª criação sem imagem de produção → imagem da homologação**; `.bicepparam` sem imagem padrão.
8. **Pedidos aos pedaços → condução em 6 etapas** (F-038): o owner se perdeu na janela do MSS-UTILS; depois
   "mensagem curta, sem linguagem técnica", "sem a fonte", pendência em palavras simples; 22 pontos anotados
   ao longo da execução e corrigidos na 0.40.0.
9. **Export do portal real**: caminho `⋯ → Exportar modelo → Exportar como Bicep → Download`, aviso amarelo
   esperado e quatro armadilhas da homologação na receita (endereço gerado, código da rede, "rotear todo o
   tráfego" ligado, regra de acesso da subnet).
10. **Permissões no escuro → documentação e evidência** (F-039): três rodadas (papel de ligar na subnet, `Reader`
    na VNet) sem efeito; eu ia propor uma 4ª; o owner exigiu pesquisa. A documentação mostrou que bastavam; o
    erro com `networkConfig` trouxe o `object id` do pipeline (`ecab5b96-…`), diferente do que recebeu as
    permissões (`77c5b924-…`, do "Manage App registration"). `networkConfig` desfeito (exige `subnets/write`).
11. **Senha do registro vazia em produção** → o Azure não entrega na leitura; agora vem do próprio registro, e
    cópia vazia nunca é gravada.
12. **Só produção → também a homologação**: o owner monta a de cada desenvolvedor à mão; receita-base do kit,
    `hml` cria só se não existe. Nome: o owner disse "ambiente-azure", eu perguntei se era comando ou branch, li
    errado a resposta, e ele fechou: `azure-ambiente` pros dois.
13. **Branch fora da `main` (quase)**: abri a `feature/azure-ambiente` com a pasta na branch da 0.40.0, ainda não
    integrada; peguei antes de gravar, desfiz e pedi o merge.

**Rejeitado.** Terraform · `az` ou qualquer comando contra o Azure na máquina do owner · variáveis no Bicep ·
`networkConfig` · Network Contributor / `subnets/write` · aviso de capacidade do plano no kit (o owner: *"a
Infra cuida disso não os desenvolvedores"*) · estágio pulado por `condition:` · nova permissão sem documentação
(4ª rodada) · etapa de aprovação manual dentro do arquivo do pipeline (o owner preferiu o administrador cadastrar
os aprovadores no ambiente `producao`).

**Fizemos.** 0.37.0 → 0.41.0 (oito versões); casos F-036, F-037, F-039 fechados e F-038 aberto; F-033 reincidiu
no chat do kit; chamado-modelo `templates/azure-ambiente/permissoes-infra.md` com o código real da conexão;
permissões de produção feitas pela infra e registradas no `templates/AMBIENTE.md` §5; precedente do Whats no
`precedentes-msig`; MSS-UTILS em produção com todas as variáveis preenchidas pelo owner (o `CONEXAO_SQL` sem
prefixo não é lido pelo app — quem decide o banco é a `CADASTROCORRETOR_SQL_CONNECTION_STRING_TKGS_CORP`).

**Próximo.**
- **No MSS-UTILS (janela de lá):** testar o sistema em produção (roteiro §10: `/nfcomissao/docs`, `/importar`,
  um PDF real); fechar a `feature/azure-prd` na `main`; criar `CADASTROCORRETOR_CONEXAO_SQL=PRD` em produção
  (sem ela, se a conexão ficar vazia, o app cai no par de desenvolvimento); o pipeline de código de produção
  (`MSS-UTILS-PROD`, push na `main`) segue pendente.
- **Projeto novo sem homologação (o "Pipeline de deploy em HTML"):** 1º uso real do caminho "homologação nova";
  se o pipeline parar por permissão, vai a seção 4 do chamado, uma vez só.
- **Kit:** o F-033 reincidiu → reavaliar o item adiado "hook `Stop` medindo a resposta contra o pedido";
  o F-038 fecha quando um projeto for do zero à produção sem reclamação de condução.
