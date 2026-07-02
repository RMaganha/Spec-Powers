<!-- MODELO de CLAUDE.md — copie para a RAIZ do projeto novo como `CLAUDE.md` e preencha os <...>.
     Regra de ouro: ENXUTO. Só o que o Claude NÃO infere do código (visão, como roda, convenções, regras).
     Detalhe de feature vai na spec; histórico/memória NÃO entram aqui. -->

# <Projeto> — <objetivo em 1 frase>

## Modo de trabalho (nunca violar)
- **Base do projeto (ler PRIMEIRO)**: se existir um `projeto.md` na raiz, leia-o antes de qualquer outra coisa — é a base/contexto fundamental do projeto. Se não existir, siga normalmente.
- **Não codar antes do meu OK explícito**: diagnosticar → plano curto → esperar OK → verificar no real (nada de "análise de memória").
- **Siga as skills do superpowers à risca** (brainstorming, test-driven-development, verification-before-completion, systematic-debugging, requesting-code-review). Precisão acima de velocidade.
- **Índices do projeto**: no início, leia `memory/MEMORY.md` (aprendizados) e `docs/superpowers/INDEX.md` (tarefas). Ambos são só índices (1 linha por item). Abra o arquivo individual só quando o índice apontar relevância; nunca leia a pasta inteira. Fallback: Grep/Glob sobre `docs/`.

## Contexto
- **Stack/runtime:** <ex.: Python 3.x / Node / ...>
- **Como roda:** <CLI | serviço/porta | container | cron>
- **UI:** <não | FastAPI + Jinja — descreva guias e ações>   <!-- se houver HTML, padrão = FastAPI -->
- **Integrações externas:** <sites / APIs / filas, ou "nenhuma">
- **Banco:** <não | qual> — DDL versionada em `sql/NN_*.sql`, revisada por mim e rodada **FORA** do app; acesso isolado por fonte; credenciais só em `.env` (nunca commit/hardcode).

## Mapa de arquivos
- `projeto.md` — base/contexto fundamental do projeto (lido primeiro; pode não existir)
- `docs/AMBIENTE.md` — referência de ambiente corporativo MSIG (rede Docker, proxy, Postgres, SQL Server, Azure)
- `docs/superpowers/INDEX.md` — índice das tarefas (specs/planos)
- `<arquivo>` — <responsabilidade>

## Regras críticas (nunca violar) — cada uma nasce de um bug ou decisão real
1. **Registro/memória/notas NUNCA em um arquivo `CLAUDE.md`** (ele é instrução sempre-ativa e polui o contexto). Memória persistente = pasta `memory/` deste projeto (dentro do repo, versionada com `MEMORY.md` como índice — NÃO em `~/.claude/projects/<proj>/memory/`); estado/handoff = plan files do superpowers.
2. Nunca commitar `.env` nem segredos; nunca hardcode de credencial.
3. <regra específica do seu projeto…>

<!-- Mantenha este arquivo curto. Se uma seção crescer demais, mova o detalhe para a spec da feature
     (docs/superpowers/specs/) ou para um doc em docs/, e deixe aqui só um ponteiro. -->
