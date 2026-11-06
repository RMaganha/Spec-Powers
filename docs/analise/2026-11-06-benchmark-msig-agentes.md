# Benchmark — MSIG_Agentes × mss-spec (2026-11-06)

> Levantamento **somente-leitura** do kit de agentes da equipe (`C:\Ronaldo\_Mitsui\Python\MSIG_Agentes`),
> feito pelo `/mss-spec:analise` com a âncora no mss-spec. Objetivo do owner: *"trazer o que ele tem de
> melhor para cá"*, **sem misturar** os dois. Nenhum arquivo de lá foi tocado; nenhum valor de credencial
> foi lido, impresso ou copiado. Autoria do kit de lá: `<a confirmar>` — o owner disse "outra empresa";
> o `leiame.txt` e as decisões do KB apontam Rafael Formenton (MSIG).

## 1. O que o MSIG_Agentes é

- **Kit de agentes de prosa pro Claude Code**, não um MCP nem um serviço: 2 comandos em
  `.claude/commands/` (`/agentes_msig` roteia e ativa; `/criar_agente_msig` cria agente pelo script),
  hooks Python registrados em `.claude/settings.json`, 24 agentes de domínio (cob, trp, ssc, sinistro,
  digital, mssai…) + `geral` (conhecimento sem dono) + `consolidador` (manutenção do KB).
- **Cada agente** = `agent.md` (persona de negócio) + `conexao.md` + arquivos de conhecimento **gerados**
  (`exemplos.md`, `troubleshooting.md`, `dicionario.md`, `conceitos.md`, `procedimentos.md`,
  `INDICE.md`) + `tools/` (scripts Python, datados em `scripts_kb/<data>_<agente>/`).
- **Coração: `.msig-agents/tools/kb.py`** (178 KB). O conhecimento da equipe vive no SQL Server
  (`TKGS_CORP`, schema `msig_kb`, no MSSQLHI); cada máquina lê de um cache SQLite
  (`.msig-agents/.cache/kb_cache.sqlite3`), grava direto no banco com fila local (outbox) se a rede
  cair, e os `.md` são cópia regenerada 1×/dia. Busca ranqueada sem embedding (tag 4 · título 3 ·
  resumo 2 · conteúdo 1; arquivado ×0,6).
- **Sincronização sem git**: identidade (`agent.md`, `AGENTS.md`, `CLAUDE.md`, commands, hooks,
  `conexao.py`, `msig_paths.py`, `settings.json`) e tools sincronizam entre máquinas pelo próprio banco,
  com detecção de conflito por checksum (`kb.py` → `sync_tools_diario`). Só `USER.md` fica de fora.
- **Hooks**: `SessionStart` → `kb.py auto` (refresh, sync, reparo do MCP, publicação dos `.sql`) +
  `kb_backup.py`; `compact|resume` → `lembrete_regras.py`; `UserPromptSubmit` → `refresh_periodico.py`
  (a cada 2 h) + `lembrar_procedimento.py` (gatilho de procedimento); `PreToolUse` →
  `guarda_producao.py` (produção, MCP só SELECT, `.md` gerado não se edita); `PostToolUse` →
  `organizar_scripts.py` (move versões substituídas, BOM em `.sql`).
- **Integrações**: MCP `hml-corp` (SQL Server de homologação) e MCP `databricks` (`.mcp.json`);
  webhook n8n de e-mail; Jenkins.
- **Nesta máquina**: a pasta já tem a camada local do mss-spec (dossiê de 04/11 em
  `docs/ARQUITETURA.md` de lá, `CLAUDE.local.md`, `memory/`), decisão do owner de 2026-11-04:
  o mss-spec ali é pessoal e nunca toca o que o `kb.py` sincroniza.

## 2. O que trazer (13 itens, por esforço)

| # | Melhoria | Esforço | Ganho | O que deixa de acontecer | Fonte lá |
|---|---|---|---|---|---|
| 2 | Solução conhecida vem primeiro | baixo | alto | contorno já registrado enterrado no fim de uma análise longa | `AGENTS.md:94` (item 5, 05/11/2026) |
| 13 | PII e credencial fora da memória | baixo | alto | dado pessoal ou senha versionado via memória/diário/spec | `kakushin/agent.md:42`, `digital/agent.md:35` |
| 3 | Decisão cobrada ao mudar o kit | baixo | médio | ninguém saber daqui a 2 meses por que um hook age assim | `AGENTS.md:205`, `kb.py:2127` |
| 6 | Reputação antes de instalar | baixo | médio | instalar pacote/MCP falso sugerido pelo assistente | `AGENTS.md:282` (anti-"AgentBaiting") |
| 7 | Gatilho fraco acusado | baixo | médio | memória gravada que o recall nunca casa | `kb.py:2582` (`validar_textos_roteamento`) |
| 9 | Citação morta na memória | baixo | médio | memória/spec apontando arquivo que não existe mais | `kb.py:2982` (`_doctor_scripts_citados`) |
| 8 | Duplicata antes de gravar | baixo | baixo | duas memórias pro mesmo achado | `kb.py:1189` (`cmd_gravar`) |
| 10 | BOM nos `.sql` com acento | — | — | **já existia**: `templates/inventario_banco.py` grava com BOM (`tests/test_inventario_banco.py:498`) | `organizar_scripts.py` |
| 11 | Não narrar o que leu | baixo | baixo | resposta que começa listando o que foi lido | `AGENTS.md:135`, `agentes_msig.md` Passo 1 |
| 1 | Procedimento como tipo de memória | médio | alto | passo a passo ensinado e esquecido; agente lê 1–3 seções e pula | `AGENTS.md:113`, `procedimentos.py`, `lembrar_procedimento.py` |
| 4 | Dicionário de dados e conceitos | médio | médio | tentativa e erro de nome de coluna a cada consulta nova | `AGENTS.md:167`, `AGENTS.md:188` |
| 12 | Envio externo nasce em teste | médio | médio | e-mail/webhook real disparado num teste; fallback silencioso | `ativomesauw/agent.md:31`, `prioridade_cotacao/agent.md:21` |
| 5 | Guarda de produção pra banco | alto | alto | consulta/DML em produção sem o owner saber | `AGENTS.md:309`, `guarda_producao.py`, `trp/agent.md:77` |

Caminhos da coluna "Fonte lá" são relativos a `C:\Ronaldo\_Mitsui\Python\MSIG_Agentes\.msig-agents\`.

Detalhe de cada um:

1. **Procedimento**: seção com `Gatilho` (frases de como o pedido chega), `Passos` (quem · como · para
   se), `Ferramentas`, `Saída`; o `gravar` recusa formato errado; um hook casa o pedido com o gatilho e
   injeta o aviso; o agente anuncia `Seguindo [#proc] — passo k/N` e, no fim, lista passos feitos ×
   pendentes (inclusive os de terceiros). "Um modelo/gerador, nunca um script por apólice."
2. **Solução conhecida primeiro**: seção lida descreve o mesmo sintoma e traz contorno → a resposta
   abre com ele em 1–3 linhas; diagnóstico depois. Incidente `corporate`, 05/11/2026.
3. **Decisão**: toda alteração de comportamento (AGENTS, agent.md, hook, roteador, `kb.py`) gera decisão
   no mesmo fechamento (quem pediu · por quê · rejeitado · como reverter); o `auto` avisa se publicou
   arquivo de comportamento sem decisão hoje/ontem. Aviso, não bloqueio.
4. **Dicionário por assunto**: `Tabelas:` · `Chaves:` · `Query "x":` · `Armadilhas:`, tudo confirmado
   no catálogo. **Conceito**: `Definição:` · `No dado:` · `Armadilhas:` · `Relacionados:`.
5. **Guarda de produção**: PreToolUse classifica alias/host (lista embutida + acréscimo local),
   responde `ask` com motivo; PostToolUse carimba a aprovação (janela de 2 h, vale pra tarefa); rotinas
   agendadas numa lista autorizada; MCP só SELECT/WITH; rótulo 🟨 HML / 🟥 PRODUÇÃO em toda consulta;
   escrita em produção: OK por execução, pré-condição refeita a cada tentativa, flag explícita.
6. **Reputação**: idade, stars × atividade, registro oficial com o mesmo mantenedor, contribuidores,
   instalação arriscada (`curl | bash`, binário externo) → 🟢🟡🔴; nunca bloqueia, nunca instala sozinho.
7. **Roteamento fraco**: `dominio` ≥ 40 chars, `quando_usar` ≥ 60 chars e 6 palavras significativas;
   `agente-criar` recusa; `doctor` lista os fracos.
8. **Duplicata**: mesma tag já usada em título diferente → aviso; reusar o título exato atualiza.
9. **Citação morta**: `.py`/`.sql` citado no KB que não existe no kit → o doctor lista.
10. **BOM**: `.sql` com acento sem BOM vira mojibake no SSMS/sqlcmd; o hook garante.
11. **Ativação**: sem demanda, só as 2 linhas; "contexto carregado é meio, não resultado".
12. **Envio externo**: `--dry-run` (resumo) → `--enviar` (destino de teste) → `--enviar-real`;
    fallback nunca silencioso (o item que caiu nele aparece no log/corpo).
13. **PII/credencial**: payload real com dado pessoal não vai pro KB; credencial de produção nunca no
    kit, no config nem no KB (só na máquina do usuário); não repetir credencial na resposta.

## 3. O que NÃO trazer

- KB em banco + cache SQLite + outbox + sync multi-máquina por checksum, histórico com autor e poda:
  o mss-spec é git; o repositório já faz isso (histórico, autor, conflito, rollback).
- Multi-agente por domínio, roteador, `USER.md` por máquina: o mss-spec é um assistente por projeto.
- Lembrete pós-compactação em texto à parte (`lembrete_regras.py`): o mss-spec reinjeta os blocos-fonte
  (`templates/regras-do-kit/`) em todo `SessionStart`, inclusive `compact`; o deles divergiu da fonte
  (incidente 09/2026 citado no próprio script).
- Auto-reparo de ambiente (instala `pyodbc`, conserta `.mcp.json`): o `/mss-spec:doctor` só reporta por
  decisão, e a Segurança da Informação vetou automação de ambiente (2026-11-03).
- Apresentação HTML gerada do estado real: `docs/anatomia.html` e `docs/COMO-FUNCIONA.html` já cobrem.
- Regras de domínio (rastro em `ems_historico_acao`, backup de tabela, `USE <banco>` + `GO`,
  `Scripts/AAAA-MM-DD_<agente>/`): seguros, não plugin.

## 4. Diferenças a registrar (decisão do owner, não absorvidas)

| Lá | Aqui | Observação |
|---|---|---|
| "Junte todas as dúvidas numa pergunta só" (`cob/agent.md:13`, 14/10/2026) | `/mss-spec:analise` pergunta uma coisa por vez | preferência de ritmo |
| "Nunca perguntar antes de gravar" no KB | "Não codar antes do meu OK"; captura de memória com OK | o mss-spec grava no git do projeto, não num banco compartilhado |
| Doctor instala e conserta | Doctor só reporta | SI vetou automação (2026-11-03) |

## 5. O que os `agent.md` confirmam sobre o desenho do mss-spec

Os 24 `agent.md` foram lidos inteiros (21 por subagente). `trp` e `vida` ainda mandam ler o conhecimento
inteiro e repetem o fluxo global; `prioridade_cotacao`, `kakushin` e `jedai_cosseguro_aceito` têm caminho
fixo de máquina; `prioridade_cotacao/agent.md:12` ensina a contornar a guarda de produção. É o incidente
que o próprio `AGENTS.md:135` de lá descreve, repetido: **regra global copiada em arquivo local diverge**.
Reforça a escolha do mss-spec de injetar as regras por hook (`regras_do_kit.py`) e deixar no `CLAUDE.md`
só a marca.

## 6. Segurança (reportar à equipe; valores não impressos)

- `.msig-agents/config.json` e `.mcp.json`: usuário e senha de homologação em texto puro, numa pasta
  copiada entre máquinas e com backup em OneDrive (`backup_kb_dest`). O `leiame.txt` chama de
  "descartável"; é o mesmo usuário em 7 aliases.
- `geral/decisoes.md`, seção `[#alias-qa]`: a senha está dentro do conhecimento sincronizado a toda a
  equipe (e regenerado a cada refresh).
- `trp/agent.md:255`, `:313`, `:447`: senha em texto num arquivo de identidade sincronizado pelo banco.
- `.claude/settings.json`: `defaultMode: auto`, `Write(./**)`/`Edit(./**)` liberados e
  `enableAllProjectMcpServers: true`.

## 7. Lacunas (o que não li)

- Corpo do `conexao.py` e do `guarda_producao.py` (só docstrings, constantes e assinaturas); ~80% do
  `kb.py`; conteúdo de `exemplos.md`/`troubleshooting.md`; `gerar_apresentacao.py`; `.cache/`;
  `USER.md` (pessoal, pulado de propósito); `memory/sessions/` de lá.
- Inventário do banco vivo **não rodou**: há evidência de SQL Server, mas o projeto é somente-leitura e o
  dossiê de 04/11 já decidiu que o acesso ali é o do agente.
- Premissa `sem fonte`: a cópia nesta máquina é a versão que a equipe usa (arquivos sincronizados em
  2026-11-06 09:20).

## 8. Decisão de implementação (owner, 2026-11-06)

Implementar os 13 itens **nesta conversa**, na ordem baixo → médio → alto, um commit por item na branch
`feature/absorver-msig-agentes` (a partir da `main` em `4d28026`), pra reverter item a item ou a branch
inteira. Passa por cima da regra "um assunto por janela" por decisão explícita do owner.

**Feito em 2026-11-06 (0.53.0):** os 12 itens implementáveis entraram, um commit cada (o 10 já existia).
Onde cada um mora: 2 → `commands/bug.md` (1b) · 13/6/11 → `templates/regras-do-kit/` · 7/8/9 →
`templates/memoria_indice.py` (`verificar`, `citacoes`) + `doctor` check 8 · 3 → `hooks/decisao_junto.py` ·
1 → `templates/MEMORY.md`, `memoria_indice.py`, `commands/memory.md`/`tarefa.md`/`bug.md` · 4 →
`templates/ARQUITETURA.md` (5.1 e 9) · 12 → `templates/SEGURANCA.md` (14), `templates/rules/envio-externo.md`,
`memory/project_envio_externo_nasce_em_teste.md` · 5 → `hooks/banco_producao.py`,
`templates/rules/banco-e-segredo.md`, `templates/AMBIENTES.md`. Detalhe por item no `CHANGELOG.md`, 0.53.0.
