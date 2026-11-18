"""conversa_texto.py — outra conversa do projeto em texto, pro ajudante pesquisador ler.

Por que existe: a conversa que o app grava é um `.jsonl` com resultado de ferramenta, raciocínio e fala de
ajudante no meio — linhas de centenas de milhares de letras. O ajudante `mss-spec:pesquisador` só lê arquivo
(`agents/pesquisador.md`); sem um texto limpo ele não tira dali o que foi dito
(`docs/specs/ajudante-pesquisador.md`, decisão 25 de `docs/specs/memoria-em-tabela.md`).

Contrato:
- **só lê** a conversa; grava apenas o texto, em `~/mss-spec/conversas/<id>.txt` — fora do repositório e fora
  do `.claude`, ao lado da tabela de memória. `MSS_CONVERSAS_DIR` troca a pasta (a suíte usa pra não tocar a
  do owner). O texto é cópia: apagar não perde nada;
- entram só as falas do **owner** e do **assistente**. Ficam de fora: resultado de ferramenta, raciocínio,
  fala de ajudante, aviso do sistema (notificação de tarefa, resumo de compactação, "interrompido", erro de
  API), retorno de hook e trecho `<private>` — fechado ou não: sem `</private>`, sai tudo até o fim da fala;
- a fala que o owner digitou **enquanto o assistente trabalhava** entra (o app a grava como anexo de fila, não
  como registro `user`): são as correções de rumo;
- o filtro da fala do owner é próprio, não o da busca na memória: lá, cortar qualquer `<tag>…</tag>` ajuda a
  buscar; aqui cortaria o que o owner escreveu (`<StatusBadge>`, `git switch -c <nome>`). Só saem os blocos
  que o app põe (`<system-reminder>`, `<command-…>`, `<task-notification>`…);
- o turno do assistente (tudo o que ele disse até o owner falar de novo) vira uma fala, com os arquivos que
  ele gravou;
- só as conversas **deste projeto**: a pasta é a da conversa em curso, ou a que o app dá ao caminho do projeto;
- linha torta ou arquivo que não abre nunca derruba: sai o que deu pra ler.

Uso: `python conversa_texto.py listar [--pasta DIR] [--quantas N]`
     `python conversa_texto.py texto <começo do id | caminho | palavras do primeiro pedido> [--pasta DIR] [--saida DIR]`
     `python conversa_texto.py lote [--desde AAAA-MM-DD] --saida DIR [--pasta DIR]` — o sono da memória, parte 2:
     todas as conversas mudadas depois do dia (sem data: todas), menos a em curso; 1 = nenhuma.
Saída: 0 = feito · 1 = nenhuma conversa casa, mais de uma casa, ou a conversa não tem fala · 2 = não achei a
pasta das conversas (ou a linha de comando veio errada).
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

LARGURA = 160                 # letras por linha do texto: o ajudante lê por linha e cita `arquivo:linha`
QUANTAS = 15                  # conversas que o `listar` mostra
TETO_PEDIDO_NA_LISTA = 80     # letras do primeiro pedido na lista
FERRAMENTAS_DE_ESCRITA = ("Write", "Edit", "MultiEdit", "NotebookEdit")
AJUDANTE = "mss-spec:pesquisador"
RE_COMANDO = re.compile(r"<command-name>\s*(.*?)\s*</command-name>", re.S)
RE_ARGUMENTOS = re.compile(r"<command-args>(.*?)</command-args>", re.S)
RE_PRIVADO_ABERTO = re.compile(r"(?is)<private>.*")       # sem `</private>`: sai tudo até o fim (o lado seguro)
RE_COLADO = re.compile(r"</?pasted_content[^>]*>")         # o texto colado pelo owner fica; só a marca sai
BLOCOS_DO_APP = ("system-reminder", "command-message", "command-name", "command-args", "local-command-stdout",
                 "local-command-stderr", "local-command-caveat", "task-notification", "user-prompt-submit-hook",
                 "ide_opened_file", "ide_selection", "bash-input", "bash-stdout", "bash-stderr")
RE_BLOCO_DO_APP = re.compile(r"(?is)<(" + "|".join(BLOCOS_DO_APP) + r")\b[^>]*>.*?</\1>")
# Começos de registro `user` que não são fala do owner (somam-se aos da busca, `memoria_tabela.NAO_E_PEDIDO`).
NAO_E_FALA = ("[Request interrupted", "The app was quit", "[mss-spec]", "[SYSTEM NOTIFICATION")
VIZINHAS = 5                  # falas do owner olhadas pra não repetir a que veio pela fila e pelo registro


@dataclass
class Fala:
    quem: str                 # OWNER | ASSISTENTE
    quando: str               # "2026-11-10 13:00" (como está na conversa) ou ""
    texto: str
    gravou: list = field(default_factory=list)


@dataclass
class Resumo:
    arquivo: Path
    ident: str
    quando: str               # última gravação do arquivo
    tamanho: int
    pedido: str
    esta: bool = False        # é a conversa em curso


def _busca():
    """`memoria_tabela.py` (irmão desta pasta): o filtro do pedido do owner e o caminho da conversa em curso."""
    if "memoria_tabela" in sys.modules:
        return sys.modules["memoria_tabela"]
    spec = importlib.util.spec_from_file_location("memoria_tabela", Path(__file__).resolve().parent / "memoria_tabela.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses (3.14) resolve anotações via sys.modules
    spec.loader.exec_module(mod)
    return mod


class DiscoReal:
    """O que o script lê e grava — a única parte que toca arquivo. Em teste, entra no lugar um objeto com os mesmos
    métodos, sobre um dicionário de arquivos."""

    @staticmethod
    def linhas(arquivo):
        """As linhas do arquivo, uma por vez (a conversa pode ter centenas de MB); levanta OSError/TypeError."""
        with open(arquivo, encoding="utf-8", errors="replace") as f:
            yield from f

    @staticmethod
    def jsonl(pasta) -> list:
        """Os `*.jsonl` (arquivos) da pasta; levanta OSError se não dá pra listar."""
        return [p for p in Path(pasta).glob("*.jsonl") if p.is_file()]

    @staticmethod
    def marca(p) -> tuple:
        """(data em segundos, tamanho) do arquivo; levanta OSError."""
        st = Path(p).stat()
        return st.st_mtime, st.st_size

    @staticmethod
    def eh_arquivo(p) -> bool:
        return Path(p).is_file()

    @staticmethod
    def eh_pasta(p) -> bool:
        return Path(p).is_dir()

    @staticmethod
    def pastas_em(base) -> list:
        return list(Path(base).iterdir())

    @staticmethod
    def ler_texto(p) -> str:
        return Path(p).read_text(encoding="utf-8")

    @staticmethod
    def gravar(destino, conteudo: str) -> None:
        """Grava num provisório e troca: quem lê nunca vê o texto pela metade."""
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        provisorio = destino.with_suffix(".txt.parcial")
        provisorio.write_text(conteudo, encoding="utf-8")
        os.replace(provisorio, destino)


def _registros(arquivo, disco=DiscoReal):
    """Os registros de fala da conversa, um por vez (o arquivo pode ter centenas de MB)."""
    try:
        for bruto in disco.linhas(arquivo):
            if '"user"' not in bruto and '"assistant"' not in bruto and '"queued_command"' not in bruto:
                continue
            try:
                reg = json.loads(bruto)
            except ValueError:
                continue
            if isinstance(reg, dict) and not reg.get("isSidechain"):
                yield reg
    except (OSError, TypeError):
        return


def _quando(reg) -> str:
    ts = reg.get("timestamp")
    return ts[:16].replace("T", " ") if isinstance(ts, str) and len(ts) >= 16 else ""


def _sem_privado(texto: str) -> str:
    """Tira o trecho `<private>…</private>` — antes de qualquer outro corte, pra tag dentro dele não o abrir."""
    return RE_PRIVADO_ABERTO.sub(" ", _busca().RE_PRIVADO.sub(" ", texto))


def _limpar_fala(bruto: str) -> str:
    """O texto que o owner escreveu, sem o que o app pôs em volta. "" quando não sobra fala."""
    t = _sem_privado(bruto)
    comando = ""
    if t.lstrip().startswith("<command-"):           # o registro É uma chamada de comando do kit
        nome = RE_COMANDO.search(t)
        args = RE_ARGUMENTOS.search(t)
        comando = nome.group(1).strip() if nome else ""
        t = args.group(1) if args else ""
    t = RE_COLADO.sub(" ", RE_BLOCO_DO_APP.sub(" ", t))
    linhas = [" ".join(l.split()) for l in t.split("\n")]
    t = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()
    if t.startswith(_busca().NAO_E_PEDIDO + NAO_E_FALA) or "hook feedback" in t[:60]:
        t = ""
    return f"{comando} {t}".strip()


def _fala_do_owner(reg) -> str:
    """O que o owner escreveu neste registro, ou "". Comando do kit sai com o nome na frente
    (`/mss-spec:duvida como…`); sem argumento, sai só o nome. A fala digitada enquanto o assistente
    trabalhava vem como anexo de fila (`queued_command` de origem humana)."""
    if reg.get("type") == "attachment":
        anexo = reg.get("attachment")
        if not isinstance(anexo, dict) or anexo.get("type") != "queued_command" or anexo.get("commandMode") != "prompt":
            return ""
        origem = anexo.get("origin")
        if isinstance(origem, dict) and origem.get("kind") not in (None, "human"):
            return ""
        return _limpar_fala(anexo["prompt"]) if isinstance(anexo.get("prompt"), str) else ""
    if (reg.get("type") != "user" or reg.get("isMeta") or reg.get("isCompactSummary")
            or reg.get("isVisibleInTranscriptOnly") or reg.get("promptSource") == "system"):
        return ""
    origem = reg.get("origin")
    if isinstance(origem, dict) and origem.get("kind") not in (None, "human"):
        return ""                                     # notificação de tarefa, mensagem de outro ajudante
    conteudo = (reg.get("message") or {}).get("content")
    partes = [conteudo] if isinstance(conteudo, str) else [
        b.get("text", "") for b in (conteudo or []) if isinstance(b, dict) and b.get("type") == "text"]
    return _limpar_fala("\n".join(p for p in partes if isinstance(p, str)))


def _do_assistente(reg):
    """(texto, [arquivos gravados]) de um registro do assistente — sem raciocínio e sem chamada de ferramenta.
    Resposta que o app fabricou (erro de API, "No response requested.") não é fala."""
    mensagem = reg.get("message") or {}
    if reg.get("isApiErrorMessage") or mensagem.get("model") == "<synthetic>":
        return "", []
    textos, gravou = [], []
    for bloco in mensagem.get("content") or []:
        if not isinstance(bloco, dict):
            continue
        if bloco.get("type") == "text" and isinstance(bloco.get("text"), str):
            limpo = _sem_privado(bloco["text"]).strip()
            if limpo:
                textos.append(limpo)
        elif bloco.get("type") == "tool_use" and bloco.get("name") in FERRAMENTAS_DE_ESCRITA:
            entrada = bloco.get("input")
            caminho = entrada.get("file_path") if isinstance(entrada, dict) else None
            if isinstance(caminho, str) and caminho.strip():
                gravou.append(caminho.strip())
    return "\n\n".join(textos), gravou


def falas(arquivo, disco=DiscoReal) -> list:
    """As falas da conversa, na ordem: cada pedido do owner e, entre dois pedidos, o turno do assistente."""
    saida, turno = [], None
    da_fila, do_registro = [], []      # a mesma fala pode vir pela fila E como registro `user`: entra uma vez

    def fechar():
        nonlocal turno
        if turno and (turno.texto or turno.gravou):
            saida.append(turno)
        turno = None

    for reg in _registros(arquivo, disco):
        if reg.get("type") in ("user", "attachment"):
            texto = _fala_do_owner(reg)
            if not texto:
                continue
            meus, outros = (da_fila, do_registro) if reg.get("type") == "attachment" else (do_registro, da_fila)
            if texto in outros[-VIZINHAS:]:
                outros.remove(texto)
                continue
            meus.append(texto)
            fechar()
            saida.append(Fala("OWNER", _quando(reg), texto))
        elif reg.get("type") == "assistant":
            texto, gravou = _do_assistente(reg)
            if not texto and not gravou:
                continue
            if turno is None:
                turno = Fala("ASSISTENTE", _quando(reg), "")
            if texto:
                turno.texto = f"{turno.texto}\n\n{texto}" if turno.texto else texto
            turno.gravou.extend(g for g in gravou if g not in turno.gravou)
    fechar()
    return saida


def _quebrar(texto: str) -> list:
    """Linhas de até `LARGURA` letras, sem perder texto; linha em branco fica."""
    linhas = []
    for linha in texto.split("\n"):
        linha = linha.rstrip()
        linhas.extend(textwrap.wrap(linha, width=LARGURA, break_long_words=True, break_on_hyphens=False) or [""])
    return linhas


def pasta_de_saida(ambiente=None) -> Path:
    ambiente = os.environ if ambiente is None else ambiente
    informada = str(ambiente.get("MSS_CONVERSAS_DIR") or "").strip()
    return Path(informada) if informada else Path.home() / "mss-spec" / "conversas"


def texto_da_conversa(ident: str, lista: list) -> str:
    """O texto das falas numeradas, sem disco: cabeçalho, uma fala por bloco, linhas de até `LARGURA` letras."""
    datas = [f.quando for f in lista if f.quando]
    periodo = f" — {datas[0]} a {datas[-1]}" if datas else ""
    linhas = [f"# Conversa {ident}{periodo} — {len(lista)} falas",
              "# Só as falas do owner e do assistente; resultado de ferramenta e fala de ajudante ficaram de fora.",
              "# Horários como estão na conversa (UTC).",
              ""]
    for n, fala in enumerate(lista, 1):
        linhas.append(f"[{n:03d}] {fala.quem}" + (f" ({fala.quando})" if fala.quando else ""))
        linhas.extend(_quebrar(fala.texto))
        if fala.gravou:
            linhas.extend(textwrap.wrap("(gravou: " + ", ".join(fala.gravou) + ")", width=LARGURA,
                                        break_long_words=True, break_on_hyphens=False))
        linhas.append("")
    return "\n".join(linhas)


def gravar_texto(arquivo, pasta_saida=None, lista=None, disco=DiscoReal):
    """Grava `<pasta_saida>/<id>.txt` com as falas numeradas e devolve o caminho; `None` se a conversa não tem
    fala nenhuma (nada é gravado). `lista`: as falas já lidas (o `lote` não relê o arquivo)."""
    arquivo = Path(arquivo)
    lista = falas(arquivo, disco) if lista is None else lista
    if not lista:
        return None
    destino = (Path(pasta_saida) if pasta_saida else pasta_de_saida()) / f"{arquivo.stem}.txt"
    disco.gravar(destino, texto_da_conversa(arquivo.stem, lista))
    return destino


def primeiro_pedido(arquivo, disco=DiscoReal) -> str:
    for reg in _registros(arquivo, disco):
        if reg.get("type") == "user":
            texto = _fala_do_owner(reg)
            if texto:
                return texto
    return ""


def _conversas(pasta, disco=DiscoReal) -> list:
    """Os `.jsonl` de conversa da pasta, da mais nova pra mais velha (arquivo de ajudante não é conversa)."""
    try:
        arquivos = [p for p in disco.jsonl(pasta) if not p.name.startswith("agent-")]
    except OSError:
        return []

    def data(p):
        try:
            return disco.marca(p)[0]
        except OSError:
            return 0.0
    return sorted(arquivos, key=data, reverse=True)


def listar(pasta, quantas: int = QUANTAS, ambiente=None, disco=DiscoReal) -> list:
    ambiente = os.environ if ambiente is None else ambiente
    em_curso = str(ambiente.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    resumos = []
    for arq in _conversas(pasta, disco)[:max(quantas, 0)]:
        try:
            data, tamanho = disco.marca(arq)
        except OSError:
            continue
        quando = datetime.fromtimestamp(data).strftime("%Y-%m-%d %H:%M")
        resumos.append(Resumo(arq, arq.stem, quando, tamanho, primeiro_pedido(arq, disco)[:TETO_PEDIDO_NA_LISTA],
                              esta=bool(em_curso) and arq.stem == em_curso))
    return resumos


def achar(pasta, pedaco: str, disco=DiscoReal) -> list:
    """As conversas que casam com `pedaco`: um caminho de `.jsonl`; senão as que começam por ele no id MAIS as
    que têm todas as palavras no primeiro pedido (sem ligar pra maiúscula) — as duas juntas, porque uma palavra
    como `cafe` também é começo de id."""
    pedaco = str(pedaco or "").strip().strip('"')
    if not pedaco:
        return []
    direto = _caminho_direto(pedaco, disco)
    if direto:
        return [direto]
    palavras = pedaco.casefold().split()
    achadas = []
    for p in _conversas(pasta, disco) if pasta else []:
        if p.stem.casefold().startswith(pedaco.casefold()):
            achadas.append(p)
            continue
        pedido = primeiro_pedido(p, disco).casefold()
        if pedido and all(w in pedido for w in palavras):
            achadas.append(p)
    return achadas


@dataclass
class ItemDoLote:
    ident: str
    quando: str               # última gravação do arquivo
    periodo: str              # "<primeira fala> a <última fala>" ou ""
    falas: int
    letras: int
    pedido: str
    texto: Path = None        # None = a conversa não tem fala (nada gravado)


def _dia_do_arquivo(p: Path, disco=DiscoReal) -> str:
    return datetime.fromtimestamp(disco.marca(p)[0]).strftime("%Y-%m-%d")


def lote(pasta, desde: str, pasta_saida, ambiente=None, disco=DiscoReal) -> list:
    """Grava o texto de todas as conversas da pasta mudadas DEPOIS do dia `desde` ('' = todas), menos a conversa em
    curso e as de ajudante, e devolve um item por conversa, da mais nova pra mais velha (o sono da memória, parte 2,
    `docs/specs/sono-da-memoria.md`). O dia é o da última gravação do arquivo, como na conta do aviso de sono."""
    ambiente = os.environ if ambiente is None else ambiente
    em_curso = str(ambiente.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    itens = []
    for arq in _conversas(pasta, disco):
        try:
            dia = _dia_do_arquivo(arq, disco)
        except OSError:
            continue
        if arq.stem == em_curso or (desde and dia <= desde):
            continue
        lista = falas(arq, disco)
        datas = [f.quando for f in lista if f.quando]
        destino = gravar_texto(arq, pasta_saida, lista, disco) if lista else None
        letras = len(disco.ler_texto(destino)) if destino else 0
        pedido = next((f.texto for f in lista if f.quem == "OWNER"), "")
        itens.append(ItemDoLote(arq.stem, datetime.fromtimestamp(disco.marca(arq)[0]).strftime("%Y-%m-%d %H:%M"),
                                f"{datas[0]} a {datas[-1]}" if datas else "", len(lista), letras,
                                pedido[:TETO_PEDIDO_NA_LISTA], destino))
    return itens


def _caminho_direto(pedaco: str, disco=DiscoReal):
    """O próprio `.jsonl`, quando `pedaco` é o caminho de um arquivo que existe; senão `None`."""
    try:
        direto = Path(pedaco)
        return direto if direto.suffix == ".jsonl" and disco.eh_arquivo(direto) else None
    except (OSError, ValueError):
        return None


def apelido_da_pasta(raiz) -> str:
    """O nome que o app dá à pasta de conversas de um projeto: o caminho com tudo o que não é letra nem número
    trocado por `-` (`C:\\Ronaldo\\_Mitsui` → `C--Ronaldo--Mitsui`)."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(raiz))


def pasta_das_conversas(ambiente=None, raiz=None, disco=DiscoReal):
    """A pasta das conversas deste projeto: a da conversa em curso; senão a que o app dá ao caminho do projeto.
    `None` quando não dá pra saber — nunca um palpite."""
    ambiente = os.environ if ambiente is None else ambiente
    em_curso = _busca().arquivo_da_conversa(ambiente, disco)
    if em_curso:
        return Path(em_curso).parent
    base = Path(ambiente.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    pasta = base / apelido_da_pasta(Path(raiz) if raiz else Path.cwd())
    return pasta if disco.eh_pasta(pasta) else None


def _linha(r: Resumo) -> str:
    kb = f"{max(r.tamanho // 1024, 1):,}".replace(",", ".")
    marca = " (esta conversa)" if r.esta else ""
    return f"{r.quando}  {kb:>7} KB  {r.ident}{marca}  {r.pedido or '(sem pedido do owner)'}"


def main(argv=None, disco=DiscoReal) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="modo", required=True)
    p_listar = sub.add_parser("listar", help="as conversas deste projeto, da mais nova pra mais velha")
    p_listar.add_argument("--quantas", type=int, default=QUANTAS)
    p_texto = sub.add_parser("texto", help="grava uma conversa em texto e imprime o caminho")
    p_texto.add_argument("pedaco", nargs="+", help="começo do id, caminho do .jsonl ou palavras do primeiro pedido")
    p_texto.add_argument("--saida", help="pasta do texto (padrão: ~/mss-spec/conversas)")
    p_lote = sub.add_parser("lote", help="grava em texto todas as conversas mudadas depois de um dia (sono da memória)")
    p_lote.add_argument("--desde", default="", help="AAAA-MM-DD: só as gravadas depois deste dia (padrão: todas)")
    p_lote.add_argument("--saida", required=True, help="pasta dos textos (use uma pasta temporária: pode haver senha)")
    for p in (p_listar, p_texto, p_lote):
        p.add_argument("--pasta", help="pasta das conversas (padrão: a deste projeto)")
    a = ap.parse_args(argv)
    if a.modo == "lote" and a.desde and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.desde):
        print(f"--desde tem de ser AAAA-MM-DD; veio {a.desde!r}.")
        return 2

    pasta = Path(a.pasta) if a.pasta else pasta_das_conversas(disco=disco)
    sem_pasta = pasta is None or not disco.eh_pasta(pasta)
    if sem_pasta and a.modo == "texto" and _caminho_direto(" ".join(a.pedaco).strip().strip('"'), disco):
        pasta, sem_pasta = None, False                # o caminho do `.jsonl` basta
    if sem_pasta:
        print("não achei a pasta das conversas deste projeto. Informe com `--pasta <pasta>` "
              "(fica em `<pasta do app>/projects/<projeto>/`).")
        return 2

    if a.modo == "listar":
        resumos = listar(pasta, a.quantas, disco=disco)
        if not resumos:
            print(f"nenhuma conversa em {pasta}")
            return 1
        print(f"conversas em {pasta} (mais nova primeiro):")
        for r in resumos:
            print(_linha(r))
        print("pra pôr uma em texto: `conversa_texto.py texto <começo do id>`")
        return 0

    if a.modo == "lote":
        itens = lote(pasta, a.desde, a.saida, disco=disco)
        if not itens:
            print(f"nenhuma conversa em {pasta}" + (f" gravada depois de {a.desde}" if a.desde else "") + ".")
            return 1
        print(f"textos em {a.saida} (mais nova primeiro) — id · período das falas · falas · letras · primeiro pedido:")
        for i in itens:
            letras = f"{i.letras:,}".replace(",", ".")
            print(f"{i.ident}  {i.periodo or i.quando}  {i.falas} falas  {letras} letras  "
                  + (i.pedido or "(sem fala do owner)") + ("" if i.texto else "  — sem fala, nada gravado"))
        total = f"{sum(i.letras for i in itens):,}".replace(",", ".")
        print(f"{len(itens)} conversas, {total} letras — passe os textos ao ajudante {AJUDANTE}.")
        return 0

    pedaco = " ".join(a.pedaco)
    achadas = achar(pasta, pedaco, disco)
    if not achadas:
        print(f"nenhuma conversa casa com {pedaco!r}. Rode `conversa_texto.py listar` e escolha pelo começo do id.")
        return 1
    if len(achadas) > 1:
        print(f"mais de uma conversa casa com {pedaco!r} — rode de novo com o começo do id de uma delas:")
        for r in listar(pasta, len(_conversas(pasta, disco)), disco=disco):
            if r.arquivo in achadas:
                print(_linha(r))
        return 1
    if achadas[0].name.startswith("agent-"):
        print(f"{achadas[0].name} é a gravação de um ajudante, não uma conversa do owner; nada foi gravado.")
        return 1
    destino = gravar_texto(achadas[0], a.saida, disco=disco)
    if destino is None:
        print(f"a conversa {achadas[0].stem} não tem fala do owner nem do assistente; nada foi gravado.")
        return 1
    texto = disco.ler_texto(destino)
    contagem = re.search(r"— (\d+) falas$", texto.split("\n", 1)[0])
    print(f"texto: {destino}")
    print(f"{contagem.group(1) if contagem else '?'} falas, " + f"{len(texto):,} letras".replace(",", ".")
          + f" — passe este caminho ao ajudante {AJUDANTE}; ele lê em pedaços e cita `arquivo:linha`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
