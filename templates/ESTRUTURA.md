<!-- MODELO de estrutura de pastas — copie para `docs/ESTRUTURA.md` no projeto novo (todo projeto,
     com ou sem UI; apague o que não se aplicar). Nasceu de incidente real: um projeto novo saiu com
     todos os arquivos achatados dentro de app/ — este doc existe pra isso nunca se repetir. -->

# Estrutura de pastas — padrão MSIG

**Regra-mãe: uma pasta por camada, nunca tudo achatado numa pasta só.** Os nomes das pastas são o
padrão; o que varia por projeto é o domínio dos arquivos dentro delas.

```
app/
├── main.py                       # entrypoint FastAPI: monta /static, inclui routers, config Jinja
├── config/settings.py            # pydantic-settings lendo o .env (conn strings, SSL_VERIFY, proxy) — AMBIENTE §2
├── utils/get_connection.py       # conexão a banco no padrão AMBIENTE §3/§4 (gerada por /mss-spec:banco)
├── models/<dominio>.py           # Pydantic: modelos de entrada/saída, um arquivo por domínio
├── services/<dominio>_service.py # regra de negócio (numeração, gravação, orquestração)
└── routers/<area>.py             # rotas FINAS: validam, chamam o service, devolvem template/JSON
templates/                        # Jinja: base.html + partials/ (macros/includes) + pages/ (views que estendem o base)
static/
├── css/                          # input.css (fonte Tailwind) → app.css (compilado, versionado)
├── js/                           # vanilla, um arquivo por página/área (layout.js, <pagina>.js)
└── img/                          # logo.png etc.
tests/                            # espelha app/: test_<area>.py (TestClient + ACs + validação)
sql/                              # DDL versionada NN_*.sql — revisada e rodada FORA do app
logs/                             # runtime (.gitkeep versionado; conteúdo no .gitignore)
Dockerfile · docker-compose.yml · docker-compose.office.yml · .env.example ·
requirements.txt · package.json (Tailwind) · CLAUDE.md · projeto.md · docs/ · memory/
```

## Regras de camada
- **Router não contém regra de negócio** — só valida entrada, chama o service e monta a resposta.
- **Service não conhece HTTP** — recebe/devolve modelos Pydantic, não `Request`/`Response`.
- **Imports só "pra baixo"**: `routers → services → models/utils/config`. Nunca o contrário
  (um service importando router é sinal de camada errada).
- **`tests/` espelha `app/`**: a regra do service se testa direto; a rota, via `TestClient`.

## Adaptação por tipo de projeto
- **Sem UI web**: apague `templates/`, `static/` e `package.json`; o resto fica igual.
- **CLI/cron/worker**: mesmo esqueleto sem `routers/` — o `main.py` chama os services direto.
- **Projeto minúsculo** (1-2 arquivos de lógica): pode colapsar `services/` e `models/` em módulos
  únicos (`service.py`, `models.py`), mas **nunca** misturar rota+regra+conexão num arquivo só.
