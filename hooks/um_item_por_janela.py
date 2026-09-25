"""Hook do mss-spec: UM ITEM POR JANELA — um chat não abre uma 2ª feature enquanto a dele estiver aberta.

Nasceu do mesmo acidente do F-022 (`docs/EVALS.md`, 2026-09): a janela aberta pra UMA feature
absorveu um 2º e um 3º assunto, misturou branches e a homologação quebrou inteira. A regra
"um assunto por janela" existia como ALERTA ("é alerta, não trava") e ficou muda. Virou trava na
0.26.0 contando por PROJETO — e aí o chat NOVO também não abria nada enquanto outro chat tivesse
feature aberta (6 abertas no Whats, 2026-09-24), e o owner passou a tirar o comando do prompt.
Desde a 0.34.0 conta por CHAT (o `session_id` do evento).

Contrato:
- evento `UserPromptSubmit`; só age quando o prompt é o comando de abrir feature
  (`/mss-spec:nova-feature <nome>` ou `/nova-feature <nome>`) — qualquer outro texto passa calado;
- o nome é o resto da LINHA do comando (as de baixo são contexto);
- lembra qual feature cada chat abriu em `~/.claude/mss-spec/um-item-janelas.json`
  (`session_id|projeto → feature` + quantas linhas estavam fechadas; um por máquina, fora de
  qualquer repo; parado há mais de 30 dias sai, retomar renova; `MSS_UM_ITEM_ESTADO` troca o caminho);
- **bloqueia** o prompt quando ESTE chat já abriu a feature Y, Y não foi encerrada e o pedido é
  outra. A linha de Y (INDEX + `INDEX-historico.md`) é achada SÓ pelo nome, por PALAVRA INTEIRA,
  e a que casa melhor é a de retomar. Encerrada = TODA linha que casa `fechada`/`pausada:
  <motivo>` (a v1 fechada não encerra a v2 aberta). Sem linha pelo nome (título do passo 3
  diferente, ou ela ainda não nasceu): encerrada só se nada está aberto e alguma linha fechou desde
  a abertura — senão bloqueia dizendo que não achou a linha;
- **passa com aviso** quando o INDEX tem feature `aberta`/`em andamento` de outro assunto (outro
  chat) — lista-as e lembra do worktree: duas features na mesma pasta trocam a branch uma da outra;
- **passa** calado no resto: retomar a própria (casa por nome ou pelo slug da spec, sem
  acento/caixa), sem nome, sem `session_id`, projeto sem INDEX;
- **falha ABERTA**: entrada malformada, estado ilegível ou bug aqui → libera e sai 0 (apagar o
  prompt do owner por defeito do hook seria pior que a regra não disparar uma vez).

Escape consciente, só do owner: `MSS_UM_ITEM_OFF=1`.
"""
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão: sem o módulo,
# ou com qualquer defeito dele, o hook segue exatamente igual.
try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("um_item_por_janela", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass

ENV_DESLIGA = "MSS_UM_ITEM_OFF"
ENV_ESTADO = "MSS_UM_ITEM_ESTADO"
ESTADO_PADRAO = os.path.join("~", ".claude", "mss-spec", "um-item-janelas.json")
VALIDADE = timedelta(days=30)
INDEX_REL = ("docs", "superpowers", "INDEX.md")
HISTORICO_REL = ("docs", "superpowers", "INDEX-historico.md")

# O nome é o resto da linha do comando; linhas de baixo são contexto (não viram nome).
RE_COMANDO = re.compile(r"^\s*/(?:mss-spec:)?nova-feature(?:[ \t]+([^\n]*))?\s*(?:\n.*)?$", re.S)
RE_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
RE_SEPARADOR = re.compile(r"\s+[—–]\s+")
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
RE_CABECALHO = re.compile(r"^\s*(#{1,6})\s+(.*\S)\s*$")
ABERTOS = ("aberta", "em andamento")
FECHADOS = ("fechada", "pausada")
PALAVRAS_VAZIAS = frozenset("a o as os e de da do das dos em no na nos nas um uma pra para por com".split())

MOTIVO = (
    "[mss-spec] BLOQUEADO — um item por janela: este chat já é da feature `{dele}` ({onde}).\n"
    "Feature nova vai num CHAT NOVO — lá este mesmo comando passa. Misturar assuntos numa janela "
    "foi o que quebrou a homologação (caso F-022). Saídas: (1) abra um chat novo e rode "
    "`/mss-spec:nova-feature {pedida}`; (2) continuar a deste chat: `/mss-spec:nova-feature {dele}`; "
    "(3) a deste chat terminou ou parou: feche pelo fecho normal ou troque o status dela no INDEX "
    "por `pausada: <motivo>` (ato do owner, não do assistente) — aí este chat abre a nova; "
    "(4) guardar pra depois: `/mss-spec:to-dolist adicionar {pedida}`. "
    "Escape consciente (só o owner): {env}=1."
)

AVISO = (
    "[mss-spec] Aviso — um item por janela: este chat fica com `{pedida}`, e há outra(s) feature(s) "
    "aberta(s) neste projeto (docs/superpowers/INDEX.md):\n{lista}\n"
    "Se outro chat está trabalhando numa delas NESTA MESMA pasta, as branches se trocam por baixo "
    "uma da outra (caso F-022) — abra esta num worktree (superpowers:using-git-worktrees). Linha "
    "parada há tempo? O owner troca o status dela por `pausada: <motivo>` à mão."
)
PRO_ASSISTENTE = "Abra a resposta repassando este aviso ao owner, antes do passo 1:\n"


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def normalizar(texto):
    """Comparável: sem acento, minúsculo, só letras/dígitos separados por 1 espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).split())


def _marcas(item):
    """(aberto, fechado) pelos segmentos após ` — `: algum começa por aberta/em andamento ·
    algum começa por fechada/pausada."""
    aberto = fechado = False
    for seg in RE_SEPARADOR.split(item)[1:]:
        s = seg.strip().strip("*").strip().lower()
        if s.startswith(ABERTOS):
            aberto = True
        if s.startswith(FECHADOS):
            fechado = True
    return aberto, fechado


def _status(item):
    """Aberto se algum segmento diz aberta/em andamento e nenhum fechada/pausada (pausada vence —
    é a saída honesta de quem parou)."""
    aberto, fechado = _marcas(item)
    return aberto and not fechado


def _secao_ignorada(titulo):
    """Backlog e 'Fora de escopo' não são feature aberta: backlog é o que ainda não começou (F-030 —
    34 itens `aberta` de backlog travavam o nova-feature pra sempre)."""
    t = normalizar(titulo)
    return t.startswith("backlog") or "fora de escopo" in t


def _itens_por_secao(texto):
    """(item, de_feature) de cada linha de lista; de_feature = fora das seções Backlog e 'Fora de
    escopo'. Subseção (`###`…) herda a seção `##` de cima; `#` e `##` redefinem."""
    ignorar = pai_ignorado = False
    for linha in texto.splitlines():
        cabecalho = RE_CABECALHO.match(linha)
        if cabecalho:
            nivel, titulo = len(cabecalho.group(1)), cabecalho.group(2)
            if nivel <= 2:
                ignorar = pai_ignorado = _secao_ignorada(titulo)
            else:
                ignorar = pai_ignorado or _secao_ignorada(titulo)
            continue
        m = RE_ITEM.match(linha)
        if m:
            yield m.group(1), not ignorar


def abertas(texto_index):
    """Itens (linha de lista, sem o marcador) com status aberto, fora das seções Backlog e 'Fora de
    escopo'."""
    return [item for item, de_feature in _itens_por_secao(texto_index) if de_feature and _status(item)]


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


def _palavras(texto):
    return frozenset(p for p in normalizar(texto).split() if p not in PALAVRAS_VAZIAS)


def grau(argumento, item):
    """Quanto o argumento casa com o item, por PALAVRA INTEIRA (`ui` não casa com `guia`):
    2 = mesmo nome (texto do link, slug da spec ou 1º segmento) · 1 = um contém o outro e o menor tem
    2+ palavras (`exportar pdf` ⊂ `exportar relatório em pdf`) · 0 = outro assunto."""
    arg = _palavras(argumento)
    if not arg:
        return 0
    melhor = 0
    for nome in nomes_de(item):
        n = _palavras(nome)
        if not n:
            continue
        if n == arg:
            return 2
        if min(len(n), len(arg)) >= 2 and (n <= arg or arg <= n):
            melhor = 1
    return melhor


def mesmo_assunto(argumento, item):
    return grau(argumento, item) > 0


def linhas_do_chat(dele, itens):
    """As linhas (INDEX + histórico) da feature do chat, SÓ pelo nome: a que casa melhor vence (a
    `v2` aberta ganha da `v1` fechada). Linha nova sem nome em comum NÃO é atribuída ao chat — o
    INDEX não diz qual chat a escreveu, e adivinhar (2ª revisão) prendia o chat pela linha do vizinho
    ou deixava o chat assumir a feature do vizinho."""
    graus = [(grau(dele, item), item) for item, _ in itens]
    topo = max((g for g, _ in graus), default=0)
    return [item for g, item in graus if g == topo] if topo else []


def _fechadas(itens):
    return sum(1 for item, de_feature in itens if de_feature and _marcas(item)[1])


def _chave_projeto(cwd):
    return os.path.normcase(os.path.abspath(cwd))


def _caminho_estado(ambiente):
    return os.path.expanduser(_texto(ambiente.get(ENV_ESTADO)) or ESTADO_PADRAO)


def _ler_estado(caminho):
    """{"<session_id>|<projeto>": {projeto, feature, quando, fechadas}}; ausente ou ilegível → vazio."""
    try:
        with open(caminho, encoding="utf-8") as f:
            estado = json.load(f)
        return estado if isinstance(estado, dict) else {}
    except Exception:                                # noqa: BLE001
        return {}


def _gravar_estado(caminho, estado, agora):
    """Descarta chat com mais de VALIDADE e grava atômico. Defeito aqui não muda a decisão."""
    try:
        vivos = {}
        for sessao, reg in estado.items():
            try:
                if agora - datetime.fromisoformat(reg["quando"]) <= VALIDADE:
                    vivos[sessao] = reg
            except Exception:                        # noqa: BLE001 — registro torto sai
                pass
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        temporario = f"{caminho}.{os.getpid()}.tmp"
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(vivos, f, ensure_ascii=False, indent=1)
        os.replace(temporario, caminho)
    except Exception:                                # noqa: BLE001 — no Windows, outro chat lendo
        try:                                         # faz o replace falhar: não deixa .tmp órfão
            os.remove(temporario)
        except Exception:                            # noqa: BLE001
            pass


def _ler(caminho):
    if not os.path.isfile(caminho):
        return ""
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def avaliar(evento, ambiente=None):
    """("libera", None) · ("avisa", texto) · ("bloqueia", motivo). Qualquer defeito → libera."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)) or not isinstance(evento, dict):
            return "libera", None
        prompt = evento.get("prompt")
        m = RE_COMANDO.match(prompt) if isinstance(prompt, str) else None
        cwd = _texto(evento.get("cwd"))
        if not m or cwd is None:
            return "libera", None
        texto_index = _ler(os.path.join(cwd, *INDEX_REL))
        if not texto_index:
            return "libera", None
        # O nome é só o resto da linha do comando; as linhas de baixo são contexto.
        pedida = (m.group(1) or "").strip()
        if not pedida:
            return "libera", None
        abertas_agora = abertas(texto_index)

        sessao = _texto(evento.get("session_id"))
        if sessao is not None:
            caminho = _caminho_estado(ambiente)
            estado = _ler_estado(caminho)
            projeto = _chave_projeto(cwd)
            chave = f"{sessao}|{projeto}"            # voltar a um projeto mantém a trava de lá
            reg = estado.get(chave)
            reg = reg if isinstance(reg, dict) else {}
            dele = _texto(reg.get("feature"))
            itens = (list(_itens_por_secao(texto_index))
                     + [(item, True) for item, _ in
                        _itens_por_secao(_ler(os.path.join(cwd, *HISTORICO_REL)))])
            agora = datetime.now()
            quando = agora.isoformat(timespec="seconds")
            if dele is None:
                retomando = False
            else:
                linhas = linhas_do_chat(dele, itens)
                retomando = grau(pedida, dele) > 0 or any(grau(pedida, item) > 0 for item in linhas)
                if linhas:
                    # Encerrada olha TODA linha que casa pelo nome, não só a melhor: a v1 fechada
                    # (nome exato) não encerra a linha aberta do chat (`busca vetorial hibrida`).
                    encerrada = all(_marcas(item)[1] for item, _ in itens if grau(dele, item) > 0)
                else:
                    # Sem linha pelo nome (o passo 3 escolhe o título pelo tema; ou ela ainda não
                    # nasceu): só é encerrada se nada está aberto E algo fechou desde a abertura.
                    antes = reg.get("fechadas")
                    encerrada = (not abertas_agora and isinstance(antes, int)
                                 and _fechadas(itens) > antes)
                if not retomando and not encerrada:
                    onde = "ainda aberta" if linhas else (
                        "não achei a linha dela no INDEX pelo nome — o passo 3 pode ter gravado outro "
                        "título, ou ela ainda não nasceu; se ela já fechou, abra um chat novo")
                    _anotar("bloqueou", f"abertas={len(abertas_agora)}", evento)
                    return "bloqueia", MOTIVO.format(dele=dele, onde=onde, pedida=pedida, env=ENV_DESLIGA)
            if retomando:                            # renova a validade de feature longa
                estado[chave] = {**reg, "quando": quando}
            else:                                    # chat novo, ou a dele encerrou: passa a ser da pedida
                estado[chave] = {"projeto": projeto, "feature": pedida, "quando": quando,
                                 "fechadas": _fechadas(itens)}
            _gravar_estado(caminho, estado, agora)

        outras = [item for item in abertas_agora if not mesmo_assunto(pedida, item)]
        if not outras:
            return "libera", None
        _anotar("avisou", f"abertas={len(outras)}", evento)
        lista = "\n".join(f"  - {item}" for item in outras)
        return "avisa", AVISO.format(pedida=pedida, lista=lista)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return "libera", None


def decidir(evento, ambiente=None):
    """None = libera (com ou sem aviso); str = motivo do bloqueio."""
    decisao, texto = avaliar(evento, ambiente)
    return texto if decisao == "bloqueia" else None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    decisao, texto = avaliar(evento)
    if decisao == "bloqueia":
        print(json.dumps({"decision": "block", "reason": texto}))
        print(texto, file=sys.stderr)
        sys.exit(2)
    if decisao == "avisa":
        # No app Desktop o systemMessage não aparece: o additionalContext faz o assistente repassar.
        print(json.dumps({
            "systemMessage": texto,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                   "additionalContext": PRO_ASSISTENTE + texto},
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
