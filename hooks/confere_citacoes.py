"""Hook do mss-spec: CONFERE CITAÇÕES — o que a resposta cita tem de existir no disco.

Por que existe (caso F-035, `docs/EVALS.md`): "não inventar fatos concretos" era só prosa. A doc da
Anthropic sobre alucinação (Reduce hallucinations) manda duas coisas que dá pra fazer sem LLM: permitir o
"não sei" e verificar cada afirmação contra a fonte, retirando a que não se sustenta. Este hook faz a parte
verificável: antes de a resposta sair, confere no disco o que ela CITA.

Contrato:
- evento `Stop`; lê `last_assistant_message` (ou, na falta, a última resposta no `transcript_path`);
- confere, fora de bloco de código cercado: caminho de arquivo em `crase` ou em link markdown — com
  `:linha` a linha tem de existir —, `/mss-spec:<comando>` (comando ou skill do kit) e `F-0NN` (só se o
  projeto tem `docs/EVALS.md`). Caminho relativo vale no projeto (`CLAUDE_PROJECT_DIR` › `cwd`) ou no kit;
  nome solto (`MAPA.md`) casa com qualquer arquivo de mesmo nome no projeto;
- não confere URL, glob, placeholder (`<x>`, `${X}`, `{x}`) nem texto com espaço (é comando, não citação);
- achou citação inexistente → **devolve a resposta UMA vez** pelo contrato do `Stop`: JSON
  `{"decision": "block", "reason": <motivo>}` no stdout e **exit 0** (o Claude continua e corrige); com
  `stop_hook_active` verdadeiro, deixa sair — nunca laço;
- **falha ABERTA**: defeito → exit 0 calado.

**Por que JSON e exit 0, e não exit 2 + stderr (F-048):** até a 0.49.0 este hook devolvia com `exit 2` e o
motivo no stderr. Nesta máquina o Git Bash imprime `setlocale: LC_ALL: cannot change locale (enu): No such
file or directory` no stderr de TODO hook, e o Claude Code lê esse "No such file or directory" com exit 2
como "Hook script appears to be missing": a devolução virou erro não-bloqueante. Medido nas transcrições do
Whats e do kit de 2026-09-25 a 2026-10-30: pelo menos 40 devoluções, nenhuma entregue ao assistente. Os
hooks com exit 0 + JSON (recall, regras do kit) sempre chegaram, com o mesmo stderr — por isso o contrato.

Escape consciente, só do owner: `MSS_CITACOES_OFF=1`.
"""
import json
import os
import re
import subprocess
import sys


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
            _registrar("confere_citacoes", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_CITACOES_OFF"
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTENSOES = ("py", "md", "json", "yml", "yaml", "sql", "html", "js", "ts", "toml", "txt", "ps1", "bat", "sh",
             "css", "cs", "csproj", "ini", "cfg", "env", "example", "jsonl", "bpmn")
RE_CERCADO = re.compile(r"```.*?```", re.S)
RE_CRASE = re.compile(r"`([^`\n]+)`")
RE_LINK = re.compile(r"\]\(([^)\s]+)\)")
RE_CAMINHO = re.compile(r"^(?P<arq>[\w./\\:~-]+\.(?:" + "|".join(EXTENSOES) + r"))(?::(?P<linha>\d+)(?:-\d+)?)?$", re.I)
RE_COMANDO = re.compile(r"(?<![\w/])/mss-spec:([a-z0-9-]+)")
RE_CASO = re.compile(r"\bF-(\d{3})\b")
MAX_ARQUIVOS = 50000
# linha que propõe (arquivo a criar, destino de movimento) — citação ali não é afirmação de que já existe
RE_FUTURO = re.compile(r"→|->|\bcri(?:ar|a|o|amos|ado|ada)\b|\bnov[oa]s?\b|\bv(?:ai|ão|ao) (?:pra|para)\b"
                       r"|\bmov(?:er|ido|ida|e|o)\b|\bpropost[oa]s?\b|\bgerar\b|\bpassa(?:r)? a existir\b"
                       r"|\bvir(?:a|ar|ou)\b"
                       # linha que NEGA a existência ("não existe `x.md`") também não afirma que existe
                       r"|\bn[ãa]o (?:existe|h[áa]|tem)\b|\bnunca (?:houve|existiu)\b|\binexistente\b", re.I)

MOTIVO = (
    "[mss-spec] Antes de entregar — fonte ou não sei (caso F-035): a resposta cita o que NÃO existe no disco:\n"
    "{lista}\n"
    "Corrija só esses trechos: aponte a citação certa, diga que é arquivo novo/proposto, ou troque por "
    "\"não sei\". Não reescreva o resto da resposta."
)


def _texto(valor):
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _ultima_resposta(transcript):
    """Texto da última mensagem do assistente (fora de subagente) no transcript, ou None."""
    try:
        ultimo = None
        with open(transcript, encoding="utf-8") as f:
            for linha in f:
                try:
                    reg = json.loads(linha)
                except ValueError:
                    continue
                if reg.get("type") != "assistant" or reg.get("isSidechain"):
                    continue
                partes = [b.get("text", "") for b in (reg.get("message") or {}).get("content") or []
                          if isinstance(b, dict) and b.get("type") == "text"]
                if any(p.strip() for p in partes):
                    ultimo = "\n".join(partes)
        return ultimo
    except Exception:                                # noqa: BLE001
        return None


def _arquivos_de(raiz):
    """Caminhos relativos (com `/`) dos arquivos de uma raiz: git ls-files, ou varredura com teto."""
    try:
        proc = subprocess.run(["git", "-C", raiz, "ls-files", "-co", "--exclude-standard"],
                              capture_output=True, text=True, timeout=5, encoding="utf-8")
        if proc.returncode == 0:
            return [l.strip() for l in proc.stdout.splitlines() if l.strip()]
    except Exception:                                # noqa: BLE001
        pass
    saida = []
    for base, pastas, arquivos in os.walk(raiz):
        pastas[:] = [p for p in pastas if p not in (".git", "node_modules", ".venv", "__pycache__")]
        rel = os.path.relpath(base, raiz).replace("\\", "/")
        saida += [a if rel == "." else f"{rel}/{a}" for a in arquivos]
        if len(saida) > MAX_ARQUIVOS:
            break
    return saida


def _conhecidos(raiz):
    """Tudo contra o que uma citação parcial pode casar: arquivos do projeto e do kit, e os moldes do kit
    pelo nome (o `docs/SEGURANCA.md` de um projeto nasce de `templates/SEGURANCA.md`)."""
    todos = set(_arquivos_de(raiz)) | set(_arquivos_de(KIT))
    moldes = os.path.join(KIT, "templates")
    nomes_molde = set(os.listdir(moldes)) if os.path.isdir(moldes) else set()
    return todos, nomes_molde


def _linhas(caminho):
    with open(caminho, "rb") as f:
        dados = f.read()
    return dados.count(b"\n") + (0 if dados.endswith(b"\n") or not dados else 1)


def _para_windows(p):
    m = re.match(r"^/([a-zA-Z])(/|$)", p)
    return f"{m.group(1).upper()}:/" + p[3:] if os.name == "nt" and m else p


def _confere_caminho(bruto, raiz, nomes):
    """None se existe; senão o motivo curto."""
    m = RE_CAMINHO.match(bruto)
    if not m:
        return None
    arq, linha = _para_windows(os.path.expanduser(m.group("arq"))), m.group("linha")
    if arq.startswith("/") and not re.match(r"^[A-Za-z]:", arq):
        arq = arq.lstrip("/")                         # `/arquivo` = raiz do projeto (link do app)
    if os.path.isabs(arq):
        candidatos = [arq]
    else:
        candidatos = [os.path.join(raiz, arq), os.path.join(KIT, arq)]
    achado = next((c for c in candidatos if os.path.isfile(c)), None)
    if achado is None:
        rel = arq.replace("\\", "/").lstrip("./")
        todos, nomes_molde = nomes()
        if any(t == rel or t.endswith("/" + rel) for t in todos) or os.path.basename(rel) in nomes_molde:
            return None                               # caminho parcial/nome solto que existe, ou molde do kit
        return "arquivo não encontrado"
    if linha:
        total = _linhas(achado)
        if int(linha) > total:
            return f"o arquivo tem {total} linhas"
    return None


def _linhas_de_fato(texto):
    """Linhas que AFIRMAM (não propõem): fora dela, a citação é de arquivo a criar/mover — não se confere.
    Medido nas respostas reais: 8 de 24 seriam devolvidas por citar o destino de um plano ("→ `BACKLOG.md`")."""
    return [l for l in texto.split("\n") if not RE_FUTURO.search(l)]


def citacoes_invalidas(texto, raiz):
    """[(citação, motivo)] — só o que dá pra conferir no disco."""
    sem_codigo = "\n".join(_linhas_de_fato(RE_CERCADO.sub(" ", texto)))
    cache = {}

    def nomes():
        if "n" not in cache:
            cache["n"] = _conhecidos(raiz)
        return cache["n"]

    saida, vistos = [], set()
    candidatos = RE_CRASE.findall(sem_codigo) + RE_LINK.findall(sem_codigo)
    for bruto in candidatos:
        c = bruto.strip()
        if c in vistos or " " in c or re.search(r"[<>*{}$?]", c) or re.match(r"^[a-z]+://", c, re.I) \
                or c.startswith(("#", "mailto:")):
            continue
        vistos.add(c)
        motivo = _confere_caminho(c, raiz, nomes)
        if motivo:
            saida.append((c, motivo))
    for nome in dict.fromkeys(RE_COMANDO.findall(sem_codigo)):
        if not (os.path.isfile(os.path.join(KIT, "commands", nome + ".md"))
                or os.path.isdir(os.path.join(KIT, "skills", nome))):
            saida.append((f"/mss-spec:{nome}", "comando/skill que o kit não tem"))
    evals = os.path.join(raiz, "docs", "EVALS.md")
    if os.path.isfile(evals):
        with open(evals, encoding="utf-8") as f:
            existentes = set(RE_CASO.findall(f.read()))
        for n in dict.fromkeys(RE_CASO.findall(sem_codigo)):
            if n not in existentes:
                saida.append((f"F-{n}", "caso que não está no docs/EVALS.md"))
    return saida


# F-033: rota alternativa que ninguém pediu. Medido em 211 respostas reais: ≥ 2 marcadores numa resposta de mais
# de 300 palavras, sem o pedido falar em opção, só pega a resposta do caso ("Rota 1 / Rota 2" num passo a passo).
RE_ROTA = re.compile(r"\b(?:Rota|Op[çc][ãa]o|Caminho|Alternativa)\s+[1-9A-C]\b", re.I)
RE_PEDIU_OPCOES = re.compile(r"(?i)\bop[çc](?:[ãa]o|[õo]es)\b|\balternativ|\brotas?\b|\bcaminhos\b|\bcompar")
MIN_PALAVRAS_ROTA = 300
MOTIVO_ROTAS = (
    "[mss-spec] Antes de entregar — resposta do tamanho do pedido (caso F-033): a resposta oferece rotas "
    "alternativas que o pedido não pediu. Se falta um fato que decide a rota, troque as rotas por 1–2 perguntas "
    "curtas; se não falta, entregue só a rota certa. O que não foi pedido cabe em 1 linha."
)
MOTIVO_MEMORIA = (
    "[mss-spec] Antes de entregar — há memória que cobre o que a resposta afirma (caso F-034):\n{lista}\n"
    "Confira a resposta contra ela; se ela estiver certa e a memória não se aplicar, entregue como está."
)


# F-047: a memória que veta um desenho casa com o que o assistente PROPÕE, não com o pedido do owner (o recall só
# vê o pedido). No Whats a busca com o texto inteiro da proposta não trouxe nenhuma das memórias que a vetavam;
# com o termo curto do tema (`build`, `arquivo novo`) trouxe as duas. Só resposta que propõe: relato passa.
# Medido em 2.285 respostas reais: marca solta ("plano", "desenho") e tema solto ("build", "arquivo") devolviam
# 314 — quase todo relato fala de arquivo. Só marca forte de proposta + frase de MUDANÇA no tema.
RE_PROPOSTA = re.compile(r"(?i)\bcomo ficaria\b|\bminha recomenda|\brecomendo\b|\bproponho\b|\bsugiro\b"
                         r"|\bpremissas\b|\bcrit[ée]rios de aceite\b")
_PECA = r"(?:arquivos?|m[óo]dulos?|scripts?|bibliotecas?|depend[êe]ncias?|pacotes?|ferramentas?|etapas?)"
TEMAS = (   # (nome do tema, termos curtos que vão pra busca do kit, a frase que mostra a mudança proposta)
    ("build", ("build",), re.compile(r"(?i)\betapas? nov[ao]s?\b[^.\n]{0,60}\b(?:build|imagem|dockerfile)\b"
                                     r"|\b(?:no|ao|do) (?:build|dockerfile)\b"
                                     r"|\b(?:build|dockerfile)\b[^.\n]{0,30}\bganha\b")),
    # "biblioteca nova", "etapa nova", "ferramenta nova" — a memória do owner fala em "arquivos novos" (Whats)
    ("peça nova", ("arquivos novos", "biblioteca nova"),
     re.compile(rf"(?i)\b{_PECA} nov[oa]s?\b|\bnov[oa]s? {_PECA}\b|\b(?:npm|pip) install\b")),
    ("variável de ambiente", ("variavel de ambiente",),
     re.compile(r"(?i)\bvari[áa]ve(?:l|is) (?:de ambiente )?nova|\bnovas? vari[áa]ve"
                r"|\b(?:chave|flag) nova\b|\bnova (?:chave|flag)\b")),
    ("rede/proxy", ("proxy",), re.compile(r"(?i)\bproxy\b|\bcertificado da\b|\bCA (?:da|corporativa)\b")),
)
POR_TEMA = 3
MOTIVO_PROPOSTA = (
    "[mss-spec] Antes de entregar — memória na hora da proposta (caso F-047): a resposta propõe mudança em "
    "{temas} e não cita estas memórias do projeto sobre o tema:\n{lista}\n"
    "Abra cada uma. Se alguma veta ou muda o desenho, refaça a proposta dizendo o que mudou; se nenhuma se "
    "aplica, cite-as em 1 linha e entregue."
)


def _motor():
    """`templates/memoria_indice.py` — o mesmo motor do recall (hooks/ e templates/ são irmãos)."""
    import importlib.util
    caminho = os.path.join(KIT, "templates", "memoria_indice.py")
    spec = importlib.util.spec_from_file_location("memoria_indice", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _citada(ponteiro, texto_norm, norm):
    """A resposta cita o ponteiro: pelo nome do arquivo (sem extensão), pelo `arquivo:linha` ou pelo título."""
    onde, _, titulo = ponteiro.partition(" — ")
    arquivo = onde.split(":")[0]
    nome = os.path.splitext(os.path.basename(arquivo))[0]
    if nome not in ("decisoes", "EVALS", "DIARIO") and norm(nome) in texto_norm:
        return True
    if ":" in onde and norm(onde) in texto_norm:
        return True
    return bool(titulo) and "indice/" in arquivo and norm(titulo) in texto_norm


def memorias_da_proposta(texto, raiz, ja_vistas=()):
    """[(tema, ponteiro)] — memória/subíndice/decisão do tema que a resposta propõe e não cita."""
    if not os.path.isdir(os.path.join(raiz, "memory")):
        return []
    sem_codigo = RE_CERCADO.sub(" ", texto)
    if not RE_PROPOSTA.search(sem_codigo):
        return []
    temas = [(nome, termos) for nome, termos, rx in TEMAS if rx.search(sem_codigo)]
    if not temas:
        return []
    from pathlib import Path
    motor = _motor()
    norm = lambda s: " ".join(re.sub(r"[^a-z0-9]+", " ", motor._norm(s)).split())   # noqa: E731
    texto_norm = norm(texto)
    saida, vistos = [], set(ja_vistas)
    for nome, termos in temas:
        n = 0
        for termo in termos:
            minimo = len(motor.tokens(termo)[0])       # todas as palavras: "arquivos novos" não casa só "novos"
            achados = [p for p in motor.casar(Path(raiz), termo, limite=POR_TEMA * 3, minimo=minimo, diario=False)
                       if p.prio in (motor.PRIO["memoria"], motor.PRIO["indice"], motor.PRIO["decisao"])]
            for p in achados:
                chave = p.ponteiro.split(" — ")[0]
                if n >= POR_TEMA or chave in vistos:
                    continue
                vistos.add(chave)
                if _citada(p.ponteiro, texto_norm, norm):
                    continue
                saida.append((nome, p.ponteiro))
                n += 1
    return saida


def _ultimo_prompt(transcript):
    """Último prompt de texto do owner no transcript (não resultado de ferramenta), ou ''."""
    if not _texto(transcript):
        return ""
    try:
        ultimo = ""
        with open(transcript, encoding="utf-8") as f:
            for linha in f:
                try:
                    reg = json.loads(linha)
                except ValueError:
                    continue
                c = (reg.get("message") or {}).get("content") if reg.get("type") == "user" else None
                if isinstance(c, str) and c.strip():
                    ultimo = c
        return ultimo
    except Exception:                                # noqa: BLE001
        return ""


def rotas_nao_pedidas(texto, prompt):
    sem_codigo = RE_CERCADO.sub(" ", texto)
    return (len(set(m.lower() for m in RE_ROTA.findall(sem_codigo))) >= 2
            and len(sem_codigo.split()) > MIN_PALAVRAS_ROTA and not RE_PEDIU_OPCOES.search(prompt or ""))


def decidir(evento, ambiente=None):
    """None = deixa sair; str = motivo pra devolver a resposta. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if _texto(ambiente.get(ENV_DESLIGA)) or not isinstance(evento, dict):
            return None
        if evento.get("stop_hook_active"):
            return None                               # já devolveu uma vez neste turno
        raiz = _texto(ambiente.get("CLAUDE_PROJECT_DIR")) or _texto(evento.get("cwd"))
        if raiz is None or not os.path.isdir(raiz):
            return None
        texto = evento.get("last_assistant_message")
        if not isinstance(texto, str):
            texto = _ultima_resposta(evento.get("transcript_path")) if _texto(evento.get("transcript_path")) else None
        if not _texto(texto):
            return None
        partes, detalhes = [], []
        invalidas = citacoes_invalidas(texto, raiz)
        if invalidas:
            partes.append(MOTIVO.format(lista="\n".join(f"- `{c}` — {m}" for c, m in invalidas[:10])))
            detalhes.append(f"citacoes={len(invalidas)}")
        prompt = _ultimo_prompt(evento.get("transcript_path"))
        if rotas_nao_pedidas(texto, prompt):
            partes.append(MOTIVO_ROTAS)
            detalhes.append("rotas")
        try:
            import _memoria_de_acao as mem
            sessao = evento.get("session_id")
            achadas = mem.casar(texto, "resposta", raiz, sessao)
            if achadas:
                mem.marcar(sessao, [m[0] for m in achadas])
                partes.append(MOTIVO_MEMORIA.format(lista="\n".join(
                    f"- `{n}` ({a}): {d}" for n, a, d, _ in achadas[:3])))
                detalhes.append("memoria=" + ",".join(m[0] for m in achadas[:3]))
        except Exception:                            # noqa: BLE001 — memória quebrada não muda o resto
            pass
        try:
            if not _texto(ambiente.get("MSS_MEMORIA_ACAO_OFF")):
                import _memoria_de_acao as mem
                sessao = evento.get("session_id")
                da_proposta = memorias_da_proposta(texto, raiz, mem.ja_mostradas(sessao))
                if da_proposta:
                    mem.marcar(sessao, [p.split(" — ")[0] for _, p in da_proposta])
                    temas = ", ".join(dict.fromkeys(t for t, _ in da_proposta))
                    partes.append(MOTIVO_PROPOSTA.format(temas=temas, lista="\n".join(
                        f"- {p}" for _, p in da_proposta)))
                    detalhes.append(f"proposta={len(da_proposta)}")
        except Exception:                            # noqa: BLE001 — busca quebrada não muda o resto
            pass
        if not partes:
            return None
        _anotar("devolveu", " ".join(detalhes)[:200], evento)
        return "\n\n".join(partes)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    motivo = decidir(evento)
    if motivo is None:
        sys.exit(0)
    # Contrato do Stop: JSON no stdout e exit 0. `json.dumps` sem `ensure_ascii=False` deixa o texto em
    # ASCII puro (acentos escapados), então a página de código do console não importa.
    print(json.dumps({"decision": "block", "reason": motivo}))
    sys.exit(0)


if __name__ == "__main__":
    main()
