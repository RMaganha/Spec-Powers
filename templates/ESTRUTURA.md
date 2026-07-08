<!-- MODELO de estrutura de pastas — copie para `docs/ESTRUTURA.md` no projeto novo (todo projeto,
     com ou sem UI; apague o que não se aplicar e ajuste os nomes de domínio pro projeto). Nasceu de
     incidente real: um scaffolding saiu com todos os arquivos achatados dentro de app/ — este doc
     existe pra isso nunca se repetir. Padrão consolidado do MSS-SSC (estilo jedai). -->

# Estrutura de pastas — padrão MSIG (camadas na raiz)

**Regra-mãe: uma pasta por camada, nunca tudo achatado numa pasta só.** Todo arquivo novo nasce na
pasta da sua camada. Os nomes das pastas são o padrão; o que varia por projeto é o domínio dos
arquivos dentro delas.

```
main.py                       # entrypoint FastAPI: monta /static, inclui routers, Jinja com ChoiceLoader(templates, pages)
config/settings.py            # pydantic-settings lendo o .env (conn strings, SSL_VERIFY, proxy) — AMBIENTE §2
utils/get_connection.py       # conexão a banco no padrão AMBIENTE (gerada por /mss-spec:banco)
models/<dominio>.py           # Pydantic: modelos de entrada/saída, um arquivo por domínio
services/<dominio>_service.py # regra de negócio (numeração, gravação, orquestração)
routers/<area>.py             # rotas FINAS: validam, chamam o service, devolvem template/JSON
templates/                    # Jinja: layout base + partials/macros (design system MSIG — docs/FRONTEND.md)
pages/                        # telas que ESTENDEM o base (2º dir do ChoiceLoader no main.py — estilo jedai)
static/
├── css/                      # input.css (fonte Tailwind) → app.css (compilado, versionado)
├── js/                       # vanilla, um arquivo por página/área (layout.js, <pagina>.js)
└── img/                      # logo.png etc.
tests/                        # espelha as camadas: test_<area>.py (TestClient + ACs)
sql/                          # DDL versionada NN_*.sql — revisada e rodada FORA do app
logs/                         # runtime (.gitkeep versionado; conteúdo no .gitignore)
Dockerfile · docker-compose.yml · docker-compose.office.yml · .env.example ·
requirements.txt · package.json (Tailwind) · CLAUDE.md · projeto.md · docs/ · memory/
```

O `ChoiceLoader` no `main.py` (torna `pages/` visível pro Jinja junto de `templates/`):
```python
templates = Jinja2Templates(directory="templates")
templates.env.loader = ChoiceLoader(
    [FileSystemLoader("templates"), FileSystemLoader("pages")]
)
```

## Regras de camada
- **Router não contém regra de negócio** — só valida entrada, chama o service e monta a resposta.
- **Service não conhece HTTP** — recebe/devolve modelos Pydantic, não `Request`/`Response`.
- **Imports só "pra baixo"**: `routers → services → models/utils/config`. Nunca o contrário
  (um service importando router é sinal de camada errada).
- **Template novo**: layout/partial em `templates/`; tela em `pages/`.
- **`tests/` espelha as camadas**: a regra do service se testa direto; a rota, via `TestClient`.

## Adaptação por tipo de projeto
- **Sem UI web**: apague `templates/`, `pages/`, `static/` e `package.json`; o resto fica igual.
- **CLI/cron/worker**: mesmo esqueleto sem `routers/` — o `main.py` chama os services direto.
- **Projeto minúsculo** (1-2 arquivos de lógica): pode colapsar `services/` e `models/` em módulos
  únicos (`service.py`, `models.py`), mas **nunca** misturar rota+regra+conexão num arquivo só.
- **Projeto legado com pacote `app/`**: mantenha o layout que já existe — a regra-mãe (camadas,
  nunca achatado) vale igual; só não misture os dois estilos no mesmo repo.
