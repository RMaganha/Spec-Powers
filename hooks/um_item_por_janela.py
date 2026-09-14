"""Hook do mss-spec: UM ITEM POR JANELA — feature nova só quando não há feature aberta.

Nasceu do mesmo acidente do F-022 (`docs/EVALS.md`, 2026-09): a janela aberta pra UMA feature
absorveu um 2º e um 3º assunto, misturou branches e a homologação quebrou inteira. A regra
"um assunto por janela" existia como ALERTA ("é alerta, não trava") e ficou muda. Agora trava.

Contrato:
- evento `UserPromptSubmit`; só age quando o prompt é o comando de abrir feature
  (`/mss-spec:nova-feature <nome>` ou `/nova-feature <nome>`) — qualquer outro texto passa calado;
- lê `<cwd>/docs/superpowers/INDEX.md` (o índice de tarefas do projeto) e considera ABERTA a
  linha de item cujo status é `aberta` ou `em andamento`; `fechada` e `pausada: <motivo>` não contam;
- **bloqueia** o prompt (apaga e mostra o motivo) se há feature aberta de OUTRO assunto;
- **passa** quando não há aberta, quando o nome pedido é a própria feature aberta (retomar não é
  misturar — casa por nome ou pelo slug da spec, sem acento/caixa) ou quando o projeto não tem INDEX;
- **falha ABERTA**: entrada malformada ou bug aqui → libera e sai 0 (apagar o prompt do owner por
  defeito do hook seria pior que a regra não disparar uma vez).

Escape consciente, só do owner: `MSS_UM_ITEM_OFF=1`.
"""
import json
import os
import re
import sys
import unicodedata

ENV_DESLIGA = "MSS_UM_ITEM_OFF"
INDEX_REL = ("docs", "superpowers", "INDEX.md")

RE_COMANDO = re.compile(r"^\s*/(?:mss-spec:)?nova-feature(?:\s+(.*?))?\s*$", re.S)
RE_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
RE_SEPARADOR = re.compile(r"\s+[—–]\s+")
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ABERTOS = ("aberta", "em andamento")
FECHADOS = ("fechada", "pausada")

MOTIVO = (
    "[mss-spec] BLOQUEADO — um item por janela: já existe feature ABERTA neste projeto.\n"
    "Abertas em docs/superpowers/INDEX.md:\n{lista}\n\n"
    "Feature nova só quando não houver aberta — misturar assuntos numa janela foi o que quebrou "
    "a homologação (caso F-022). Saídas: (1) terminar a aberta: retome com "
    "`/mss-spec:nova-feature <nome dela>` (o mesmo nome passa) e feche pelo fecho normal; "
    "(2) parar sem terminar: edite o INDEX à mão e troque o status por `pausada: <motivo>` — ato "
    "do owner, não do assistente; (3) o assunto novo vai pro `/mss-spec:to-dolist adicionar "
    "<assunto>` e ganha janela própria depois. Escape consciente (só o owner): {env}=1."
)


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def normalizar(texto):
    """Comparável: sem acento, minúsculo, só letras/dígitos separados por 1 espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).split())


def _status(item):
    """Casa o status pelos segmentos após ` — `: aberto se algum começa por aberta/em andamento
    e nenhum por fechada/pausada (pausada vence — é a saída honesta de quem parou)."""
    aberto = fechado = False
    for seg in RE_SEPARADOR.split(item)[1:]:
        s = seg.strip().strip("*").strip().lower()
        if s.startswith(ABERTOS):
            aberto = True
        if s.startswith(FECHADOS):
            fechado = True
    return aberto and not fechado


def abertas(texto_index):
    """Itens (linha de lista, sem o marcador) com status aberto, fora da seção 'Fora de escopo'."""
    saida = []
    ignorar = False
    for linha in texto_index.splitlines():
        if linha.lstrip().startswith("#"):
            ignorar = "fora de escopo" in linha.lower()
            continue
        if ignorar:
            continue
        m = RE_ITEM.match(linha)
        if m and _status(m.group(1)):
            saida.append(m.group(1))
    return saida


def nomes_de(item):
    """Formas pelas quais o owner pode se referir ao item: texto do link, slug da spec, 1º segmento."""
    nomes = []
    link = RE_LINK.search(item)
    if link:
        nomes.append(link.group(1))
        slug = link.group(2).rsplit("/", 1)[-1]
        nomes.append(slug[:-3] if slug.endswith(".md") else slug)
    primeiro = RE_SEPARADOR.split(item)[0]
    nomes.append(RE_LINK.sub(r"\1", primeiro))
    return [normalizar(n) for n in nomes if normalizar(n)]


def mesmo_assunto(argumento, item):
    arg = normalizar(argumento)
    if not arg:
        return False
    for nome in nomes_de(item):
        if arg == nome:
            return True
        if len(arg) >= 4 and (nome in arg or (len(nome) >= 4 and arg in nome)):
            return True
    return False


def decidir(evento, ambiente=None):
    """None = libera; str = motivo do bloqueio. Qualquer defeito aqui → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)):
            return None
        if not isinstance(evento, dict):
            return None
        prompt = evento.get("prompt")
        if not isinstance(prompt, str):
            return None
        m = RE_COMANDO.match(prompt)
        if not m:
            return None
        cwd = _texto(evento.get("cwd"))
        if cwd is None:
            return None
        index = os.path.join(cwd, *INDEX_REL)
        if not os.path.isfile(index):
            return None
        with open(index, encoding="utf-8") as f:
            itens = abertas(f.read())
        if not itens:
            return None
        argumento = m.group(1) or ""
        if argumento and any(mesmo_assunto(argumento, item) for item in itens):
            return None
        lista = "\n".join(f"  - {item}" for item in itens)
        return MOTIVO.format(lista=lista, env=ENV_DESLIGA)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    motivo = decidir(evento)
    if motivo is None:
        sys.exit(0)                                  # libera, calado
    print(json.dumps({"decision": "block", "reason": motivo}))
    print(motivo, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
