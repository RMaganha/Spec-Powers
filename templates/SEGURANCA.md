<!-- MODELO — copie para docs/SEGURANCA.md. Apague seções que não se aplicam (ex.: sem Azure, sem React). -->

# Segurança de aplicação (AppSec) — baseline MSIG

Stack-alvo: FastAPI + Jinja (server-rendered) e/ou React+TS (SPA), banco SQL Server (pyodbc) /
Postgres (psycopg), deploy Azure Web App. Modelo de ameaça: app **exposto na internet pública** com
**login** (varia por projeto — alguns são só uso interno); **dev local é aberto e sem HTTPS** por
design (ver `docs/AMBIENTE.md`).

## 0. Princípios (leia primeiro)

- **Segurança ≠ obscuridade**: esconder/renomear/criptografar URL de asset não protege — o HTML
  entrega a URL ao browser (`Ctrl+U` / DevTools) e a chave de descriptografia viaja junto do código.
  Não segura nem contra júnior.
- **Frontend é público**: assuma que o atacante lê 100% do bundle (JS/TS compilado). Nada de
  segredo, URL interna ou lógica-de-confiança no browser; o servidor sempre re-decide.
- **Kerckhoffs**: saber nome de função/endpoint não pode abrir brecha — a defesa está no servidor
  validando, não no atacante ignorar que o endpoint existe.
- **Gate por ambiente**: dev aberto / prod fechado, via flag (mesmo espírito do `CONEXAO_SQL`).

## 1. Autorização (OWASP A01)

**Risco**: usuário autenticado acessa recurso que não é dele, ou rota sensível sem checagem de
permissão (broken access control é o topo do OWASP Top 10).

**Regra MSIG**: default-deny em produção — toda rota sensível nasce bloqueada e é liberada
explicitamente; a permissão é checada **no backend**, a cada request (nunca confie em "o front não
mostra o botão"). IDOR: antes de retornar/alterar um recurso por id, pergunte "esse recurso é do
usuário logado (ou ele tem permissão sobre ele)?" — não só "o id existe?".

**Como fica no stack**: dependency do FastAPI (`Depends(...)`) na assinatura de cada rota sensível,
que resolve o usuário da sessão/token e valida posse/permissão antes do handler rodar; o handler não
reimplementa a checagem.

**Como verificar**: toda rota que mexe em dado sensível tem a dependency de auth na assinatura
(grep por `def <rota>` sem `Depends` de auth por perto); teste de integração que loga como usuário A
e tenta ler/alterar recurso do usuário B — espera **403** (não 200, não 404 mascarando dado).

## 2. Autenticação & sessão (A07)

Ver seção **"Modelo de auth — dois baldes"** mais abaixo — cobre autenticação de usuário vs.
integração server-to-server, e o que está em escopo hoje vs. seam futuro. Não duplicar aqui.

## 3. Injeção (A03)

**Risco**: SQL injection (pyodbc/psycopg), payload malformado quebrando regra de negócio, upload
disfarçado de outro tipo de arquivo, path traversal em nome de arquivo.

**Regra MSIG**: SQL **sempre** parametrizado — nunca monte a query concatenando/formatando entrada
do usuário. Payload de entrada validado com Pydantic (tipo, tamanho, formato) antes de qualquer uso.
Upload checado de verdade: tipo de conteúdo real (não só extensão), tamanho máximo, e — relevante
pros apps que sobem PDF — validação de que o arquivo é de fato do tipo esperado. Nome de arquivo
nunca vira caminho de disco sem sanitizar (path traversal via `../../`).

```python
# ✅ parametrizado — driver trata escaping, valor nunca vira parte do SQL
cursor.execute("SELECT * FROM pedidos WHERE id = ?", [pedido_id])

# ❌ concatenação/format — entrada do usuário vira SQL literal
cursor.execute(f"SELECT * FROM pedidos WHERE id = {pedido_id}")
cursor.execute("SELECT * FROM pedidos WHERE id = %s" % pedido_id)
cursor.execute("SELECT * FROM pedidos WHERE id = {}".format(pedido_id))
```

**Como verificar**: grep por f-string/`%`/`.format` perto de `execute(` — qualquer ocorrência é
suspeita e merece revisão linha a linha:
```
grep -rn "execute(f" --include=*.py .
grep -rnE "execute\(.*(%|\.format\()" --include=*.py .
```

## 4. XSS / saída (A03)

**Risco**: conteúdo do usuário (ou de terceiro) renderizado como HTML/JS executável na página de
outro usuário.

**Regra MSIG**: autoescape do Jinja fica **ligado** (é o default — não desligue com `| safe` sem
sanitizar o conteúdo antes). React escapa por padrão ao renderizar `{variavel}`; evite
`dangerouslySetInnerHTML` — se for realmente necessário, sanitize (ex. DOMPurify) antes de passar.

**Como verificar**:
```
grep -rn "| safe" templates/
grep -rn "dangerouslySetInnerHTML" src/
```
Toda ocorrência precisa de justificativa explícita (por que o conteúdo é confiável) no código ou
review.

## 5. Frontend & assets estáticos

**Risco**: build de produção vazando estrutura interna (source-map reconstrói nomes de variável e
comentários do `.tsx` original), `console.log` esquecido expondo dado sensível, directory listing
expondo arquivos que não deveriam ser públicos, `.env`/`.git`/backup servidos por engano.

**Regra MSIG**: build de PROD com minify **e sem source-map**; sem `console.log` de dado sensível
(revisar antes do build); directory listing **desligado**; `StaticFiles` do FastAPI aponta só pra
pasta de assets públicos (nunca a raiz do projeto) — assim `.env`/`.git`/backup nunca ficam
alcançáveis por URL; nada de segredo ou URL interna hardcoded no bundle (volta ao princípio 0 —
frontend é público).

**Como verificar**: abrir DevTools → Sources em produção e confirmar que não há `.map` nem código
legível fonte-a-fonte; conferir config do bundler (`sourcemap: false` no Vite/webpack/etc.); tentar
acessar `/../.env` ou listar um diretório estático sem `index` — espera 403/404.

## 6. Headers & HTTPS (A05)

**Risco**: sem HSTS/CSP/anti-clickjacking, o browser fica mais exposto a MITM, injeção de conteúdo
externo e embutimento malicioso em iframe.

**Regra MSIG**: middleware FastAPI aplicando `Strict-Transport-Security`, `Content-Security-Policy`,
`X-Content-Type-Options: nosniff`, `X-Frame-Options`/`frame-ancestors`, `Referrer-Policy`; HTTPS-only
em **produção**. Nota: HTTPS é regra de PROD — dev local e homolog podem rodar em HTTP (ver
`docs/AMBIENTE.md`, TLS é resolvido em outra camada nesses ambientes).

**Como verificar**: `curl -I` na URL de produção e conferir os headers presentes; middleware
registrado no `main.py` (não opcional/comentado).

## 7. Config & segredos (A02/A05)

**Risco**: segredo commitado, `.env` versionado, TLS desligado "temporariamente" e esquecido,
`DEBUG=True` vazando detalhe de execução em produção.

**Regra MSIG**: `.env` fora do commit (`.gitignore`); **segredo via variável de ambiente** — `.env` (gitignored) em dev,
**Azure App Settings** em prod; o código lê do ambiente (`os.getenv`), nunca do repo. Credencial de
banco segue a mesma regra (a alternativa **Fernet-no-código** do `get_connection.py` é só ofuscação —
a chave vai junto no repo — reservada a **continuidade**; escolha no `/mss-spec:banco`); `SSL_VERIFY=true`
sempre (o `false` é só fallback temporário de diagnóstico, nunca fica); sem `DEBUG=True` em
produção. Em Azure: segredo vive em App Settings / Key Vault, nunca no repo.

**Como verificar**: `git log -p -- .env` (nunca deveria ter entrado); grep por padrão de segredo
hardcoded:
```
grep -rniE "(password|secret|token|api_key)\s*=\s*['\"]" --include=*.py .
```

## 8. Erros & vazamento de informação

**Risco**: stack trace do FastAPI/Python vazando caminho de arquivo, versão de lib, ou query SQL
pro cliente; log gravando senha/PII em texto plano.

**Regra MSIG**: handler de exceção genérico em produção — cliente recebe mensagem curta e um id de
correlação, nunca o traceback; detalhe completo vai só pro log interno. Logs nunca gravam PII nem
segredo (usar o helper `mask_password` do padrão de conexão pra qualquer log que toque credencial).

## 9. Dependências / CVE (A06)

**Risco**: lib com CVE conhecida rodando em produção sem ninguém notar.

**Regra MSIG**: `pip-audit` no lado Python e `npm audit` no front, rodados periodicamente (idealmente
no pipeline); imagem base do Docker atualizada; versões pinadas (não `latest`/sem teto) pra builds
reprodutíveis.

**Como verificar**: rodar as ferramentas e checar saída:
```
pip-audit
npm audit
```

## 10. CORS & rate limit (A04/A05)

**Risco**: CORS aberto demais permite que qualquer site chame a API usando a sessão do usuário;
sem rate limit, login e rotas caras ficam expostas a força bruta/DoS.

**Regra MSIG**: CORS fechado — lista explícita de origens conhecidas; **nunca** `allow_origins=["*"]`
junto com `allow_credentials=True` (essa combinação é insegura por definição). Rate limit em rotas
caras e no login. Teto de tamanho de payload/upload (evita esgotar memória/disco com request gigante).

**Como verificar**: conferir a config de `CORSMiddleware` no `main.py`; testar burst de requests no
login e confirmar que passa a bloquear/atrasar.

## 11. CSRF

**Risco**: form que usa cookie de sessão pode ser submetido a partir de outro site (o browser envia
o cookie automaticamente).

**Regra MSIG**: token CSRF em todo form que dependa de cookie de sessão — relevante quando há login
por cookie no Jinja (server-rendered). Não se aplica a APIs stateless autenticadas só por Bearer
token (sem cookie, sem CSRF).

## 12. LGPD / dados pessoais

Minimizar coleta (só o dado necessário pro fluxo); nunca logar PII (CPF, e-mail, nome completo) em
texto plano; dado sensível cifrado em repouso quando aplicável (ex. documento de identificação).
Isto é um lembrete, não um tratado — para exigência formal, consultar o time jurídico/compliance.

## 13. Checklist Azure/infra (👤 humano — não é código do app)

- [ ] HTTPS Only ligado no App Service
- [ ] TLS mínimo 1.2
- [ ] Autenticação configurada no App Service / App Gateway (quando aplicável)
- [ ] Secrets em Key Vault (não em App Settings em texto plano quando o dado for muito sensível)
- [ ] Restrição de rede (IP allowlist / VNet integration conforme exposição do app)
- [ ] Managed identity para acesso ao banco, quando possível (evita credencial estática)

## Modelo de auth — dois baldes

| Balde | Quem chama | Proteção | Hoje (local) |
|---|---|---|---|
| **Consumo próprio** | o front do app → o backend do próprio app | auth de **usuário** (login) — **nunca** o bearer de integração (viraria público no browser) | **aberto** |
| **Integração** | **outro sistema** (servidor) → seu backend | **Bearer `TOKEN_API`** (server-to-server) | token off/descartável |

Regras:
- `AUTH_TOKEN_ATIVO`: `false` em dev/homolog (não exige token); `true` em prod (exige Bearer).
- `TOKEN_API` só server-side — nunca commit, nunca browser; idealmente um token por sistema
  consumidor (facilita revogar um sem afetar os outros).
- HTTPS só em prod: o token de PROD nunca trafega em HTTP. Se homolog ligar `AUTH_TOKEN_ATIVO`, use
  um valor diferente e descartável (nunca reaproveitar o de prod).
- `valida_token()` é uma dependency do FastAPI que roda **antes** das rotas de integração: confere o
  Bearer contra o `.env` e devolve 401 sem explicar o motivo. É o *seam* onde no futuro entra também
  a validação de token de usuário — as rotas de integração não mudam quando isso acontecer.

```env
AUTH_TOKEN_ATIVO=          # false em dev/homolog (não exige token); true em prod (exige Bearer)
TOKEN_API=                 # segredo server-to-server; SÓ backend, nunca commit/browser; ideal 1 por sistema consumidor
```

**Nota curta**: login de usuário no browser (JWT/sessão, idle/teto absoluto) está **fora de escopo**
por enquanto — é um seam futuro. Em produção, "é meu próprio app que chama" **não é proteção** — o
atacante replica a chamada por fora do front via DevTools/curl; por isso o consumo próprio ficará
atrás do login assim que o app expuser dado a usuários finais.

## Anti-padrões (não faça)

- **Ofuscar/criptografar URL de asset** (`/static/...` → `/x/y/z.css`): zero segurança — o HTML
  entrega a URL ao browser, e o arquivo em si não tem segredo nenhum pra proteger.
  **Faça em vez disso**: directory listing off, não servir arquivo sensível, sem source-map em prod.
- **Browser cunhar o próprio token** (segredo/algoritmo de geração de token no JS): é público — o
  atacante lê o bundle e gera tokens válidos exatamente igual.
  **Faça em vez disso**: tokens só se validam contra chave/segredo que mora no servidor.
- **Token único como login de usuário**: um `TOKEN_API` compartilhado serve só pra
  server-to-server; exposto no browser vira público e não identifica nem revoga ninguém
  individualmente.
  **Faça em vez disso**: login por usuário (seam futuro) para o consumo próprio; `TOKEN_API`
  fica reservado à integração.
