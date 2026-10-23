<!-- CLAUDE.md do PROJETO: entra em toda sessão (orçamento 10 KB; passou, o hook avisa). As regras do kit NÃO ficam aqui —
     vêm do plugin mss-spec em toda janela (hook SessionStart). Fato do projeto, por extenso, na seção Contexto; regra de como
     escrever cada tipo de arquivo em `.claude/rules/`. Passou do teto? Mova um bloco pro comando/rules/spec com ponteiro; nunca comprima. -->
<!-- mss-spec:regras-do-kit -->

# <Projeto> — <objetivo em 1 frase>

## Regras obrigatórias do projeto
1. <regra só deste projeto — o que nunca violar (ex.: o que nunca abrir, o que é intocável)…>

## Contexto
- **Infra:** <**MSIG** | **própria**> — MSIG = rede `mitiai_network`, proxy, CA do FortiGate, SQL corporativo (`docs/AMBIENTE.md`). Própria = nada disso (sem proxy no `.env`, sem `docker-compose.office.yml`, sem `get_connection.py`); o doctor pula esses checks. Definido no `/mss-spec:kickoff`; é esta linha que os comandos leem.
- **Stack/runtime:** <ex.: Python 3.x / Node>
- **Como roda:** <CLI | serviço/porta | container | cron>
- **UI:** <não | web — ex.: FastAPI + Jinja>
- **Ambientes:** <homologação/produção: onde roda e o nome de cada um, ou "só local">
- **Banco:** <não | qual — ex.: PostgreSQL + pgvector>
- **Integrações externas:** <sites / APIs / filas, ou "nenhuma">
- **Versionamento:** <ex.: branch por tarefa a partir da `main`; quem faz push/deploy>

## Mapa de arquivos (só o que não se infere lendo o repo)
- `projeto.md` — base/contexto fundamental (lido primeiro; pode não existir)
- `docs/ESTRUTURA.md` **prescreve** onde arquivo novo nasce; `docs/ARQUITETURA.md` **descreve** o projeto como é hoje e lista **o que não nasceu do kit** (intocável)
- `docs/decisoes.md` — decisões **transversais** ("X em vez de Y — porque Z")
- `<arquivo>` — <responsabilidade>

## Índice de regras por tipo de arquivo
- <arquivo de `.claude/rules/`> — <assunto> — carrega ao tocar <padrões>
