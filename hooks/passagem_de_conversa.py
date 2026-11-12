"""Hook do mss-spec: CONVERSA NOVA NÃO SE PERDE — o que o owner decidiu chega como decidido.

Por que existe (item CRÍTICO do `to-dolist.md`, casos F-058 e F-053 do `docs/EVALS.md`): em 2026-11-11, na
memória em tabela, duas conversas abertas com o texto pronto se perderam (*"respondendo completamente errado,
dizendo que o plugin não aceita isso ou aquilo"*) e a terceira, com 6 itens decididos no pedido, respondeu "Os
tópicos, na ordem em que quero fechar com você" e "Tópico 1 — …". O próprio texto pronto pedia "um tópico por
vez" e não dizia para não reabrir. A regra existia em prosa (memória `feedback_decidir_por_topicos_um_de_cada_vez`);
o owner pediu cobrança por hook, para todos os projetos.

Contrato — três conferências e uma busca, sem LLM:
1. **Quem recebe** (`UserPromptSubmit` + `Stop`): pedido com o título `Já decidido` / `O que eu já decidi` /
   `Decisões já tomadas` seguido de itens → guarda os itens desta conversa (temp do SO,
   `mss_passagem_<conversa>.json`) e entrega a regra ao assistente (`additionalContext`; nunca `systemMessage` — o
   owner não tem nada a fazer). Daí em diante a resposta **volta** se anunciar "Tópico N", se uma pergunta repetir
   um item decidido (palavras em comum) ou se as perguntas estiverem espalhadas pelo meio. Cada uma dessas age
   **uma vez por conversa** (e a de repetir, uma vez por item).
2. **Quem entrega** (`Stop`, toda conversa): a resposta fala de outra conversa + colar/texto pronto e traz um bloco
   de texto de 5 linhas ou mais → o bloco tem de ter `Já decidido — não reabrir:`, `Falta decidir:` e `Regras desta
   conversa:`, e não pode pedir "um tópico por vez". Senão **volta** com o molde.
3. **"O kit não aceita"** (`Stop`, toda conversa): a resposta diz que o kit, o plugin ou uma trava não aceita,
   negou ou bloqueou algo → só sai com um `arquivo:linha` e uma pergunta ao owner. Fora de bloco de código, de
   citação (`>`) e de aspas; "nada no kit proíbe" e descrição no presente ("a cerca nega push") não contam.
4. **A conversa nova acha sozinha** (0.61.0 — o owner, 2026-11-12: "sem eu colar texto nem digitar comando"):
   no `Stop`, o bloco de texto pronto que está no molde fica guardado (temp do SO, `mss_passagens_<projeto>.json`,
   7 dias, os 10 últimos; nada no git). No **1º** `UserPromptSubmit` de uma conversa, sem lista colada, a frase é
   casada com o assunto do texto guardado e com o nome/título da spec que tem `## O que o owner decidiu`; casou →
   os itens chegam como `additionalContext` (teto de 2.000 bytes). Casa pelo termo curto do tema
   (`docs/decisoes.md:54`), nunca pelo texto dos itens; empate → só os nomes. **Só informa**: o que foi achado
   sozinho não entra nas devoluções do item 1 (o casamento pode errar de assunto).
- devolve pelo contrato do `Stop`: JSON `{"decision": "block", "reason": …}` no stdout e **exit 0** (decisão de
  2026-10-30: exit 2 + stderr se perde nesta máquina); com `stop_hook_active`, deixa sair — nunca laço;
- **falha ABERTA**: qualquer defeito → sai calado;
- registra `devolveu`/`entregou`/`guardou`/`achou` no registro local (`hooks/_registro.py`), nunca o texto.

Escape consciente, só do owner: `MSS_PASSAGEM_OFF=1`. Spec: `docs/specs/conversa-nova-nao-se-perde.md`.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import unicodedata


try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None

try:
    from _prompt import texto_do_pedido as _pedido
except Exception:                                    # noqa: BLE001 — sem o módulo, vale o pedido como veio
    def _pedido(prompt):
        return prompt if isinstance(prompt, str) else ""


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("passagem_de_conversa", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_PASSAGEM_OFF"
MAX_ITENS = 40
TETO_ITEM = 300

# ------------------------------------------------------------------ o pedido: itens que chegam decididos
_PREFIXO = r"^[ \t>*#_-]*"
RE_TITULO_DECIDIDO = re.compile(
    r"(?im)" + _PREFIXO + r"(?:j[áa] decidido|o que (?:eu )?j[áa] decidi|decis[õo]es j[áa] tomadas)\b[^\n]*$")
RE_FALTA = re.compile(r"(?im)" + _PREFIXO + r"falta decidir\b")
RE_REGRAS = re.compile(r"(?im)" + _PREFIXO + r"regras desta conversa\b")
RE_ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+(\S.*)$")
RE_ROTULO = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^:.\n]{0,40}:")       # "Como provar: …", "Falta decidir:" — fim da lista
_FIM_DE_FRASE = (".", "!", "?", ";", ":")

REGRA = (
    "[mss-spec] Passagem de conversa — este pedido traz {n} item(ns) do owner como DECIDIDOS (a lista sob "
    "\"{titulo}\"). Regras desta conversa (caso F-058):\n"
    "- O que está decidido não se reabre nem se confirma de novo. Nada de \"tópico 1 de N\": o formato tópico a "
    "tópico vale só para o que ainda não foi decidido.\n"
    "- Mostre em lista única só as SUAS escolhas (uma linha cada, com o motivo) e pergunte de uma vez, no fim, o "
    "que só o owner decide; siga depois do OK dele.\n"
    "- Se alguma regra, decisão antiga ou trava do kit parecer proibir algo do que está decidido, mostre a regra "
    "com arquivo e linha e pergunte ao owner ANTES de qualquer desenho — nunca \"o kit não aceita\"."
)

MOLDE = (
    "/mss-spec:<comando> <assunto em uma linha>\n"
    "Leia antes de qualquer desenho: <arquivos, na ordem>.\n"
    "Já decidido — não reabrir:\n"
    "1. <decisão do owner, com arquivo:linha quando houver>\n"
    "Falta decidir:\n"
    "1. <o que só o owner decide> (ou: nada)\n"
    "Regras desta conversa: o que está decidido não se reabre — mostre em lista única só as SUAS escolhas e "
    "pergunte de uma vez, no fim, o que só eu decido; siga depois do meu OK. Se alguma regra do kit parecer "
    "proibir, mostre a regra com arquivo e linha e me pergunte."
)


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def decididos(pedido, teto=TETO_ITEM):
    """Os itens sob o título de decididos, na ordem. Lista vazia se o pedido não traz a lista. `teto=None` = o
    item inteiro (o que é guardado para outra conversa não é cortado: cortar frase pode inverter o sentido)."""
    texto = _pedido(pedido)
    if not texto:
        return []
    itens = []
    for m in RE_TITULO_DECIDIDO.finditer(texto):
        itens = _lista(texto[m.end():].split("\n")[1:])
        if itens:
            break                                     # a 1ª lista com itens é a que vale
    return [i[:teto] for i in itens[:MAX_ITENS]]


def _lista(linhas):
    """Os itens da lista que começa em `linhas` (as linhas logo depois do título), até o fim dela."""
    itens, em_branco = [], False
    for linha in linhas:
        if not linha.strip():
            em_branco = True
            continue
        item = RE_ITEM.match(linha)
        if item:
            itens.append(item.group(1).strip())
            em_branco = False
            continue
        continua = itens and not em_branco and (
            linha[:1] in " \t" or (not itens[-1].rstrip().endswith(_FIM_DE_FRASE) and not RE_ROTULO.match(linha)))
        if not continua:
            break
        itens[-1] += " " + linha.strip()
    return itens


# ------------------------------------------------------------------ estado por conversa
def _pasta_temp(ambiente):
    return _texto(ambiente.get("TEMP")) or _texto(ambiente.get("TMP")) or _texto(ambiente.get("TMPDIR")) \
        or tempfile.gettempdir()


def _estado(sessao, ambiente):
    seguro = re.sub(r"[^\w-]", "_", str(sessao))[:80]
    return os.path.join(_pasta_temp(ambiente), f"mss_passagem_{seguro}.json")


def _ler_estado(sessao, ambiente):
    try:
        with open(_estado(sessao, ambiente), encoding="utf-8") as f:
            estado = json.load(f)
        return estado if isinstance(estado, dict) else {}
    except Exception:                                # noqa: BLE001
        return {}


def _gravar_estado(sessao, ambiente, estado):
    try:
        with open(_estado(sessao, ambiente), "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False)
    except Exception:                                # noqa: BLE001
        pass


# ------------------------------------------------------------------ a resposta
RE_CERCADO = re.compile(r"(?ms)^[ \t]*```([\w-]*)[ \t]*\n(.*?)^[ \t]*```[ \t]*$")
RE_ASPAS = re.compile(r"\"[^\"\n]{1,300}\"|“[^”\n]{1,300}”|`[^`\n]{1,200}`")
RE_PERGUNTA = re.compile(r"\?[ \t*_)]*$")


def _sem_blocos(texto):
    """Fora de bloco de código e de linha de citação (`>`)."""
    sem = RE_CERCADO.sub(" ", texto)
    return "\n".join(l for l in sem.split("\n") if not l.lstrip().startswith(">"))


def _perguntas(linhas):
    return [i for i, l in enumerate(linhas) if RE_PERGUNTA.search(l)]


# --- 1. quem recebe
RE_TOPICO = re.compile(r"(?i)\bt[óo]pico\s+\d+\b")
ESPALHADAS = 12               # linhas com texto entre a primeira e a última pergunta
PALAVRAS_VAZIAS = frozenset(
    "a o as os e de da do das dos em no na nos nas um uma pra para por com que se ou ao aos mais como seu sua "
    "meu minha eu voce ele ela isso esse essa este esta nao sim ja so the".split())
MIN_COMUNS = 3
MIN_FATIA = 0.6

MOTIVO_TOPICO = (
    "[mss-spec] Antes de entregar — o que está decidido não se reabre (caso F-058): este pedido trouxe {n} "
    "item(ns) do owner como DECIDIDOS e a resposta anuncia tópico a tópico. Esse formato vale só para o que ainda "
    "não foi decidido. Refaça: lista única só com as SUAS escolhas (uma linha cada, com o motivo), o que só o "
    "owner decide perguntado de uma vez, no fim, e siga depois do OK dele."
)
MOTIVO_REABRE = (
    "[mss-spec] Antes de entregar — o que está decidido não se reabre (caso F-058): a resposta pergunta de novo o "
    "que chegou decidido:\n{lista}\n"
    "Tire a pergunta. Se o item bate de frente com uma regra do kit, mostre a regra com arquivo e linha e pergunte "
    "isso. Se a pergunta é sobre outra coisa, diga em uma linha o que ela pergunta de diferente e entregue."
)
MOTIVO_ESPALHADAS = (
    "[mss-spec] Antes de entregar — pergunte de uma vez, no fim (caso F-058): as perguntas estão espalhadas pela "
    "resposta. Junte o que só o owner decide num bloco só, no fim; o resto é escolha sua, em lista única."
)


def _radicais(texto):
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return frozenset(p[:5] for p in re.findall(r"[a-z0-9]+", sem_acento)
                     if len(p) >= 3 and p not in PALAVRAS_VAZIAS)


def _repete(pergunta, item):
    p, i = _radicais(pergunta), _radicais(item)
    comuns = len(p & i)
    return comuns >= MIN_COMUNS and comuns / max(1, min(len(p), len(i))) >= MIN_FATIA


def _quem_recebe(texto, estado):
    """([motivos], [marcas a gravar]) — só o que ainda não agiu nesta conversa."""
    itens = estado.get("decididos") or []
    if not itens:
        return [], []
    feitas = set(estado.get("feitas") or [])
    limpo = _sem_blocos(texto)
    linhas = [l for l in limpo.split("\n") if l.strip()]
    motivos, marcas = [], []
    if "topico" not in feitas and RE_TOPICO.search(RE_ASPAS.sub(" ", limpo)):
        motivos.append(MOTIVO_TOPICO.format(n=len(itens)))
        marcas.append("topico")
    perguntas = _perguntas(linhas)
    reabertos = []
    for p in perguntas:
        for n, item in enumerate(itens, 1):
            marca = f"reabre:{n}"
            if marca not in feitas and marca not in marcas and _repete(linhas[p], item):
                reabertos.append(f"- pergunta: «{linhas[p].strip()[:160]}» → item {n} decidido: «{item[:160]}»")
                marcas.append(marca)
    if reabertos:
        motivos.append(MOTIVO_REABRE.format(lista="\n".join(reabertos[:5])))
    if "espalhadas" not in feitas and len(perguntas) >= 2:
        entre = [i for i in range(perguntas[0] + 1, perguntas[-1]) if i not in perguntas]
        if len(entre) > ESPALHADAS:
            motivos.append(MOTIVO_ESPALHADAS)
            marcas.append("espalhadas")
    return motivos, marcas


# --- 2. quem entrega
RE_OUTRA_CONVERSA = re.compile(r"(?i)\b(?:conversa nova|nova conversa|outra conversa|outra janela|janela nova"
                               r"|nova janela|outro chat|chat novo|novo chat)\b")
RE_COLAR = re.compile(r"(?i)\bcol(?:e|a|ar|ando)\b|\btexto pronto\b")
RE_TOPICO_POR_VEZ = re.compile(r"(?i)\bum t[óo]pico (?:por|de cada) vez\b|\bt[óo]pico a t[óo]pico\b")
LINGUAGENS_DE_TEXTO = ("", "text", "txt", "md", "markdown")
MIN_LINHAS_DO_TEXTO = 5

MOTIVO_ENTREGA = (
    "[mss-spec] Antes de entregar — texto pronto para outra conversa (caso F-058): {problema}. A conversa que "
    "recebe só trata como decidido o que vier sob o título fixo, e o texto de 2026-11-11 que pedia \"um tópico por "
    "vez\" fez a conversa nova reabrir 6 itens decididos. Refaça o bloco neste molde, com os fatos conferidos "
    "agora. Se o bloco é só um recado para uma conversa que já está em curso (não abre conversa), entregue como "
    "está.\n\n{molde}"
)


def _quem_entrega(texto):
    """Motivo (str) ou None."""
    fora = RE_CERCADO.sub(" ", texto)
    if not (RE_OUTRA_CONVERSA.search(fora) and RE_COLAR.search(fora)):
        return None
    blocos = [corpo for linguagem, corpo in RE_CERCADO.findall(texto)
              if linguagem.lower() in LINGUAGENS_DE_TEXTO
              and len([l for l in corpo.split("\n") if l.strip()]) >= MIN_LINHAS_DO_TEXTO]
    if not blocos:
        return None
    problemas = []
    for corpo in blocos:
        faltam = [nome for nome, rx in (("`Já decidido — não reabrir:`", RE_TITULO_DECIDIDO),
                                        ("`Falta decidir:`", RE_FALTA),
                                        ("`Regras desta conversa:`", RE_REGRAS)) if not rx.search(corpo)]
        if faltam:
            problemas.append("falta no bloco " + ", ".join(faltam))
        elif RE_TOPICO_POR_VEZ.search(corpo):
            problemas.append("o bloco pede \"um tópico por vez\"")
        else:
            return None                               # um bloco no molde basta
    return MOTIVO_ENTREGA.format(problema=problemas[0], molde=MOLDE)


# --- 3. "o kit não aceita"
_QUEM = r"(?:kit|plugin|mss-spec|hook|trava|cerca|regra)"
_NEGA_HOJE = r"(?:pro[íi]be|impede|bloqueia|nega|veta|n[ãa]o\s+(?:aceita|permite|deixa))"
RE_RECUSAS = (
    re.compile(r"(?i)\b(?:kit|plugin|mss-spec)\b[^.\n]{0,40}\bn[ãa]o\s+(?:aceita|permite|deixa|suporta)\b"),
    # "nunca bloqueou" / "não negou" não é recusa (medido: 1 das 10 respostas reais pegas era essa)
    re.compile(r"(?i)\b" + _QUEM + r"\b[^.\n]{0,80}\b(?<!nunca )(?<!n[ãa]o )"
               r"(?:negou|bloqueou|barrou|vetou|recusou|impediu|proibiu)\b"),
    re.compile(r"(?i)\b(?:foi|foram|fui|ficou|est[áa])\s+(?:negad|bloquead|barrad|recusad|proibid|vetad)[oa]s?\b"
               r"[^.\n]{0,80}\b" + _QUEM + r"\b"),
    re.compile(r"(?i)\bn[ãa]o\s+(?:posso|consigo|vou|d[áa]|pude|consegui)\b[^.\n]{0,100}\b" + _QUEM
               + r"\b[^.\n]{0,60}\b" + _NEGA_HOJE + r"\b"),
    re.compile(r"(?i)\b" + _QUEM + r"\b[^.\n]{0,60}\b" + _NEGA_HOJE
               + r"\b[^.\n]{0,100}\bn[ãa]o\s+(?:posso|consigo|vou|d[áa])\b"),
)
RE_ARQUIVO_LINHA = re.compile(r"[\w./\\-]+\.[A-Za-z0-9]{1,8}:\d+")

MOTIVO_RECUSA = (
    "[mss-spec] Antes de entregar — \"o kit não aceita\" só com a regra à vista (item CRÍTICO de 2026-11-11): a "
    "resposta diz que o kit, o plugin ou uma trava não aceita, negou ou bloqueou algo, e {falta}. Mostre a regra "
    "com arquivo e linha (o `arquivo:linha` do hook, da decisão ou da memória) e pergunte ao owner se ele mantém ou "
    "revê. Se a frase só descreve como o kit funciona, e não recusa nada do que o owner pediu, entregue como está."
)


def _recusa(texto):
    """Motivo (str) ou None."""
    limpo = _sem_blocos(texto)
    sem_aspas = RE_ASPAS.sub(" ", limpo)
    if not any(rx.search(sem_aspas) for rx in RE_RECUSAS):
        return None
    faltas = []
    if not RE_ARQUIVO_LINHA.search(limpo):
        faltas.append("não mostra a regra com arquivo e linha")
    if not _perguntas(limpo.split("\n")):
        faltas.append("não pergunta ao owner")
    if not faltas:
        return None
    return MOTIVO_RECUSA.format(falta=" e ".join(faltas))


# --- 4. a conversa nova acha sozinha o que o owner já decidiu
# O owner (2026-11-12): abre a conversa com uma frase comum; o kit acha o assunto e traz o que já foi decidido —
# sem colar texto, sem comando novo e sem travar. Duas fontes, nesta ordem: o texto pronto que outra conversa
# entregou (guardado aqui, na hora, fora do git) e a seção `## O que o owner decidiu` da spec do assunto.
ACHADO_TETO = 2000             # bytes de itens entregues à conversa nova
PASSAGENS_MAX = 10             # textos prontos guardados por projeto
PASSAGEM_DIAS = 7              # depois disso o texto guardado não é mais procurado
SPECS_MAX = 200
SPEC_TETO = 200_000            # caracteres lidos de cada spec
FRASE_TETO = 600               # caracteres do pedido usados como "frase de abertura"
MIN_COMUNS_ASSUNTO = 3
MIN_FATIA_ASSUNTO = 0.5
EMPATADOS_MAX = 3
RE_SECAO_DECIDIDO = re.compile(
    r"(?i)^##+\s*(?:o que o owner (?:j[áa] )?decidiu|o que (?:eu )?j[áa] decidi|j[áa] decidido"
    r"|decis[õo]es j[áa] tomadas)\b")
RE_COMANDO_NA_FRENTE = re.compile(r"^\s*/[\w:.-]+[ \t]*")
RE_FIM_DO_NOME = re.compile(r"\s+[—–-]\s+|[:.;]\s")       # "Memória em tabela — parte 2" → "Memória em tabela"
RE_PRIVADO = re.compile(r"(?i)<private\b")
RE_VAGA = re.compile(r"<[^<>\n]{3,}>")                     # "<assunto em uma linha>" — o molde, não um assunto

ACHADO = (
    "[mss-spec] O que o owner já decidiu sobre este assunto — o kit achou sozinho, pela frase de abertura desta "
    "conversa. Assunto: {assunto}. Fonte: {fonte}.\n"
    "{lista}\n"
    "{resto}"
    "Regras desta conversa: o que está nesta lista chega como DECIDIDO — não reabra nem confirme de novo; mostre em "
    "lista única só as SUAS escolhas (uma linha cada, com o motivo) e pergunte de uma vez, no fim, o que só o owner "
    "decide. Diga ao owner, em uma linha, que assunto o kit achou e de onde veio. Se o assunto desta conversa for "
    "outro, ignore a lista e diga isso em uma linha."
)
ACHADO_TAMBEM = "A spec do assunto também guarda decisões do owner: `{fonte}` — abra antes do desenho.\n"
ACHADO_RESTO = "(+{n} item(ns) que não couberam aqui — abra {fonte})\n"
ACHADO_EMPATE = (
    "[mss-spec] A frase de abertura desta conversa casa com mais de um assunto que tem decisões do owner "
    "guardadas:\n{lista}\n"
    "O kit não escolheu por você: pergunte ao owner qual é o assunto e abra a fonte dele antes de qualquer desenho."
)


def _raiz(evento, ambiente):
    return _texto(ambiente.get("CLAUDE_PROJECT_DIR")) or _texto(evento.get("cwd"))


def _chave(raiz):
    return hashlib.sha1(os.path.normcase(os.path.abspath(raiz)).encode("utf-8")).hexdigest()[:12]


def _arquivo_das_passagens(raiz, ambiente):
    return os.path.join(_pasta_temp(ambiente), f"mss_passagens_{_chave(raiz)}.json")


def _passagens(raiz, ambiente):
    """Os textos prontos guardados deste projeto que ainda valem, do mais antigo ao mais novo."""
    try:
        with open(_arquivo_das_passagens(raiz, ambiente), encoding="utf-8") as f:
            guardadas = json.load(f).get("passagens")
    except Exception:                                # noqa: BLE001
        return []
    limite = time.time() - PASSAGEM_DIAS * 86400
    return [p for p in guardadas if isinstance(p, dict) and _texto(p.get("assunto"))
            and isinstance(p.get("itens"), list) and p["itens"]
            and isinstance(p.get("quando"), (int, float)) and p["quando"] >= limite] \
        if isinstance(guardadas, list) else []


def _texto_entregue(texto):
    """O bloco de texto pronto que está no molde (o corpo dele), ou None."""
    for linguagem, corpo in RE_CERCADO.findall(texto):
        if linguagem.lower() not in LINGUAGENS_DE_TEXTO:
            continue
        if len([l for l in corpo.split("\n") if l.strip()]) < MIN_LINHAS_DO_TEXTO:
            continue
        if RE_TITULO_DECIDIDO.search(corpo) and RE_FALTA.search(corpo) and RE_REGRAS.search(corpo) \
                and not RE_TOPICO_POR_VEZ.search(corpo):
            return corpo
    return None


def _guardar_se_entregou(texto, evento, ambiente, sessao):
    """Guarda o texto pronto que esta resposta entregou. Nunca muda a decisão do `Stop`; defeito → calado."""
    try:
        raiz = _raiz(evento, ambiente)
        corpo = _texto_entregue(texto)
        if raiz is None or corpo is None or RE_PRIVADO.search(corpo):
            return
        primeira = next((l.strip() for l in corpo.split("\n") if l.strip()), "")
        assunto = RE_COMANDO_NA_FRENTE.sub("", primeira).strip()[:TETO_ITEM]
        itens = decididos(corpo, teto=None)
        if not assunto or not itens or RE_TITULO_DECIDIDO.match(assunto) or RE_VAGA.search(assunto) \
                or not _radicais(assunto):
            return
        outras = [p for p in _passagens(raiz, ambiente) if _radicais(p["assunto"]) != _radicais(assunto)]
        outras.append({"assunto": assunto, "itens": itens, "quando": time.time(), "conversa": sessao})
        with open(_arquivo_das_passagens(raiz, ambiente), "w", encoding="utf-8") as f:
            json.dump({"passagens": outras[-PASSAGENS_MAX:]}, f, ensure_ascii=False)
        _anotar("guardou", f"decididos={len(itens)}", evento)
    except Exception:                                # noqa: BLE001
        pass


def _specs_com_decisoes(raiz):
    """As specs do projeto que têm a seção do que o owner decidiu, com os itens dela."""
    pasta = os.path.join(raiz, "docs", "specs")
    try:
        nomes = sorted(n for n in os.listdir(pasta) if n.endswith(".md"))[:SPECS_MAX]
    except OSError:
        return []
    achadas = []
    for nome in nomes:
        try:
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                linhas = f.read(SPEC_TETO).split("\n")
        except Exception:                            # noqa: BLE001
            continue
        titulo = next((l.lstrip("# ").strip() for l in linhas if l.startswith("# ")), "")
        for n, linha in enumerate(linhas):
            if not RE_SECAO_DECIDIDO.match(linha):
                continue
            secao = []
            for seguinte in linhas[n + 1:]:
                if seguinte.startswith("#"):
                    break
                secao.append(seguinte)
            while secao and not RE_ITEM.match(secao[0]):
                secao.pop(0)
            itens = _lista(secao)[:MAX_ITENS]              # inteiros: quem limita é o teto da entrega
            if itens:
                achadas.append({"origem": "spec", "assunto": titulo or nome[:-3], "curto": nome[:-3].replace("-", " "),
                                "longo": titulo, "itens": itens, "fonte": f"docs/specs/{nome}:{n + 1}"})
            break
    return achadas


def _pontos(frase, curto, longo):
    """Quanto a frase casa com o assunto (0 = não casa). Casa pelo termo curto do tema (`docs/decisoes.md:54`):
    o nome inteiro do assunto está na frase, ou 3 palavras do nome + título e pelo menos metade do menor lado."""
    todos = curto | longo
    comuns = len(frase & todos)
    if curto and curto <= frase and (len(curto) >= 2 or all(len(r) >= 4 for r in curto)):
        return 100 + comuns
    if comuns >= MIN_COMUNS_ASSUNTO and comuns / max(1, min(len(frase), len(todos))) >= MIN_FATIA_ASSUNTO:
        return comuns
    return 0


def escolher(frase, candidatos):
    """(vencedor, []) · (None, [empatados]) · (None, []). Texto guardado ganha de spec com os mesmos pontos."""
    radicais = _radicais(RE_COMANDO_NA_FRENTE.sub("", frase or "")[:FRASE_TETO])
    if not radicais:
        return None, []
    pontuados = []
    for c in candidatos:
        pontos = _pontos(radicais, _radicais(c.get("curto") or ""), _radicais(c.get("longo") or ""))
        if pontos:
            pontuados.append(((pontos, c.get("origem") == "passagem"), c))
    if not pontuados:
        return None, []
    pontuados.sort(key=lambda par: par[0], reverse=True)
    topo = [c for nota, c in pontuados if nota == pontuados[0][0]]
    return (topo[0], []) if len(topo) == 1 else (None, topo[:EMPATADOS_MAX])


def _achar(frase, evento, ambiente, sessao):
    """O contexto a entregar no 1º pedido da conversa, ou None. Só informa: nada daqui entra na devolução."""
    raiz = _raiz(evento, ambiente)
    if raiz is None:
        return None
    candidatos = []
    for p in _passagens(raiz, ambiente):
        if p.get("conversa") == sessao:
            continue
        quando = time.strftime("%d/%m/%Y %H:%M", time.localtime(p["quando"]))
        candidatos.append({"origem": "passagem", "assunto": p["assunto"],
                           "curto": RE_FIM_DO_NOME.split(p["assunto"], 1)[0], "longo": p["assunto"],
                           "itens": [str(i) for i in p["itens"][:MAX_ITENS]],
                           "fonte": f"texto pronto entregue por outra conversa em {quando}",
                           "onde": _arquivo_das_passagens(raiz, ambiente)})
    specs = _specs_com_decisoes(raiz)
    vencedor, empatados = escolher(frase, candidatos + specs)
    if empatados:
        _anotar("achou", f"empate={len(empatados)}", evento)
        return ACHADO_EMPATE.format(lista="\n".join(f"- {c['assunto'][:120]} — {c['fonte']}" for c in empatados))
    if vencedor is None:
        return None
    linhas, usados = [], 0
    for n, item in enumerate(vencedor["itens"], 1):
        linha = f"{n}. {item}"
        usados += len(linha.encode("utf-8")) + 1
        if usados > ACHADO_TETO:
            break
        linhas.append(linha)
    faltam = len(vencedor["itens"]) - len(linhas)
    resto = ACHADO_RESTO.format(n=faltam, fonte=vencedor.get("onde") or vencedor["fonte"]) if faltam else ""
    if vencedor["origem"] == "passagem":
        da_spec, _ = escolher(frase, specs)
        if da_spec is not None:
            resto += ACHADO_TAMBEM.format(fonte=da_spec["fonte"])
    _anotar("achou", f"fonte={vencedor['origem']} decididos={len(linhas)}", evento)
    return ACHADO.format(assunto=vencedor["assunto"][:160], fonte=vencedor["fonte"], lista="\n".join(linhas),
                         resto=resto)


# ------------------------------------------------------------------ decisão
def _ultima_resposta(evento):
    texto = evento.get("last_assistant_message")
    if isinstance(texto, str):
        return texto
    caminho = _texto(evento.get("transcript_path"))
    if caminho is None:
        return None
    try:
        from confere_citacoes import _ultima_resposta as ler
        return ler(caminho)
    except Exception:                                # noqa: BLE001
        return None


def avaliar(evento, ambiente=None):
    """("contexto", regra) no envio do pedido · ("devolve", motivo) no fim da resposta · (None, None)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)) or not isinstance(evento, dict):
            return None, None
        sessao = _texto(evento.get("session_id"))
        nome = evento.get("hook_event_name")
        if nome == "UserPromptSubmit":
            pedido = evento.get("prompt")
            itens = decididos(pedido)
            estado = _ler_estado(sessao, ambiente) if sessao is not None else {}
            if not itens:
                # sem lista colada: no 1º pedido da conversa, o kit procura sozinho o que já foi decidido
                if sessao is None or estado.get("procurou"):
                    return None, None
                _gravar_estado(sessao, ambiente, {**estado, "procurou": True})
                achado = _achar(_pedido(pedido), evento, ambiente, sessao)
                return ("contexto", achado) if achado else (None, None)
            if sessao is not None:
                _gravar_estado(sessao, ambiente,
                               {"decididos": itens, "feitas": estado.get("feitas") or [], "procurou": True})
            titulo = RE_TITULO_DECIDIDO.search(_pedido(pedido)).group(0).strip(" \t>*#_-:")[:80]
            _anotar("entregou", f"decididos={len(itens)}", evento)
            return "contexto", REGRA.format(n=len(itens), titulo=titulo)
        if nome != "Stop":
            return None, None
        texto = _ultima_resposta(evento)
        if not _texto(texto):
            return None, None
        _guardar_se_entregou(texto, evento, ambiente, sessao)     # antes do `stop_hook_active`: a refeita é a que vale
        if evento.get("stop_hook_active"):
            return None, None
        motivos, detalhes = [], []
        estado = _ler_estado(sessao, ambiente) if sessao is not None else {}
        do_recebe, marcas = _quem_recebe(texto, estado)
        if do_recebe:
            motivos += do_recebe
            detalhes.append("recebe=" + ",".join(marcas))
            estado["feitas"] = sorted(set(estado.get("feitas") or []) | set(marcas))
            _gravar_estado(sessao, ambiente, estado)
        entrega = _quem_entrega(texto)
        if entrega:
            motivos.append(entrega)
            detalhes.append("entrega")
        recusa = _recusa(texto)
        if recusa:
            motivos.append(recusa)
            detalhes.append("recusa")
        if not motivos:
            return None, None
        _anotar("devolveu", " ".join(detalhes)[:200], evento)
        return "devolve", "\n\n".join(motivos)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None, None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    tipo, texto = avaliar(evento)
    # `json.dumps` sem `ensure_ascii=False`: ASCII puro, a página de código do console não importa.
    if tipo == "contexto":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": texto}}))
    elif tipo == "devolve":
        print(json.dumps({"decision": "block", "reason": texto}))
    sys.exit(0)


if __name__ == "__main__":
    main()
