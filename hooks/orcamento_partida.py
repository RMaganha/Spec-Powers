"""Hook do mss-spec: ORÇAMENTO DA PARTIDA — avisa, ao abrir a janela, o que estourou o teto.

Por que existe (caso F-030, `docs/EVALS.md`): no Whats a partida lia `CLAUDE.md` 28 KB + `MAPA.md`
60 KB + `INDEX.md` 71 KB, com tetos de 10 · 6 · 7 KB. A janela saiu de 73 mil pra 139 mil tokens
antes da 1ª resposta, e item velho de backlog (n8n, cotação) entrou no plano de deploy como se fosse
o estado atual. O `doctor` (check 9) media e mandava rodar o `rodizio_partida.py` — só que ninguém
roda o doctor antes de cada janela. O guardrail vai pra onde a leitura acontece: a abertura.

Contrato:
- evento `SessionStart` (startup, resume, clear, compact); **nunca bloqueia** (rede, não cerca);
- mede em bytes, na raiz (`CLAUDE_PROJECT_DIR` › `cwd`), os quatro arquivos de `ARQUIVOS` — os
  mesmos tetos do `tests/test_orcamento_contexto.py` e do `templates/rodizio_partida.py` (teste trava);
- tudo dentro do teto (ou ausente) → silêncio; algum acima → `additionalContext` (≤ 1.000 bytes) que
  nomeia só o que estourou (KB com uma casa: `10,1 KB (teto 10,0 KB)`), diz o que ler de cada um e que
  backlog não é estado atual, + `systemMessage` de 1 linha pro terminal;
- o conserto que o aviso manda depende do que estourou: `CLAUDE.md` SEM a marca das regras do kit →
  `/mss-spec:upgrade` (migração: as regras do kit passam a vir do plugin); `CLAUDE.md` COM a marca → mover
  bloco com ponteiro; `/mss-spec:doctor` só quando o estouro é MAPA/INDEX/MEMORY;
- **falha ABERTA**: qualquer defeito → exit 0 calado.

Escape consciente, só do owner: `MSS_ORCAMENTO_OFF=1`.
"""
import json
import os
import sys


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
            _registrar("orcamento_partida", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_ORCAMENTO_OFF"
TETO_TEXTO = 1000
# cópia de hooks/regras_do_kit.py (hooks não importam um do outro; um teste trava a igualdade)
MARCA = "<!-- mss-spec:regras-do-kit -->"

# (caminho relativo à raiz, teto em bytes) — a ordem é a da partida
ARQUIVOS = (
    ("CLAUDE.md", 10000),
    ("docs/superpowers/MAPA.md", 6000),
    ("docs/superpowers/INDEX.md", 7000),
    ("memory/MEMORY.md", 6000),
)

# o que ler de cada arquivo estourado (o resto: grep quando o assunto pedir)
LEIA = {
    "CLAUDE.md": "CLAUDE.md já entrou inteiro — não releia",
    "docs/superpowers/MAPA.md": "MAPA → só `## Onde estamos` até o 1º `---`",
    "docs/superpowers/INDEX.md": "INDEX → só `## Em andamento`",
    "memory/MEMORY.md": "MEMORY → só o topo; subíndice quando o gatilho bater",
}


def _kb(n):
    return f"{n / 1000:.1f} KB".replace(".", ",")


def _medida(n, teto):
    """'10,5 KB (teto 10,0 KB)'; quando o arredondado empata com o teto mas passou dele, mostra bytes."""
    if n > teto and _kb(n) == _kb(teto):
        return f"{n:,} B (teto {teto:,} B)".replace(",", ".")
    return f"{_kb(n)} (teto {_kb(teto)})"


def tem_marca(raiz):
    """True se o `CLAUDE.md` da raiz tem a linha-marca (depois de tirar o BOM; `strip()` leva o CR)."""
    try:
        with open(os.path.join(raiz, "CLAUDE.md"), encoding="utf-8", errors="replace") as f:
            texto = f.read().lstrip("\ufeff")
    except (OSError, UnicodeError):
        return False
    return any(linha.strip() == MARCA for linha in texto.splitlines())


def estouros(raiz):
    """[(caminho relativo, bytes, teto)] dos arquivos acima do teto, na ordem de ARQUIVOS."""
    saida = []
    for rel, teto in ARQUIVOS:
        p = os.path.join(raiz, *rel.split("/"))
        if os.path.isfile(p):
            n = os.path.getsize(p)
            if n > teto:
                saida.append((rel, n, teto))
    return saida


def conserto(lista, com_marca):
    """O que o owner faz, conforme o que estourou (CLAUDE.md migrado ou não; o resto é com o doctor)."""
    claude = any(rel == "CLAUDE.md" for rel, _, _ in lista)
    outros = any(rel != "CLAUDE.md" for rel, _, _ in lista)
    passos = []
    if claude and not com_marca:
        passos.append("rode `/mss-spec:upgrade` pra migrar o CLAUDE.md (regras do kit passam a vir do plugin)")
    if claude and com_marca:
        passos.append("CLAUDE.md: mover bloco com ponteiro, nunca apagar")
    if outros:
        passos.append("ofereça `/mss-spec:doctor` (conserto: mover bloco com ponteiro, nunca apagar)")
    return "; ".join(passos)


def _comando(lista, com_marca):
    """Fecho curto do `systemMessage` (terminal)."""
    claude = any(rel == "CLAUDE.md" for rel, _, _ in lista)
    outros = any(rel != "CLAUDE.md" for rel, _, _ in lista)
    partes = []
    if claude:
        partes.append("mova um bloco do CLAUDE.md" if com_marca else "rode /mss-spec:upgrade")
    if outros:
        partes.append("rode /mss-spec:doctor")
    return " · ".join(partes)


def texto_do_aviso(lista, com_marca=False):
    medidas = " · ".join(f"{rel.rsplit('/', 1)[-1]} {_medida(n, t)}" for rel, n, t in lista)
    leia = "; ".join(LEIA[rel] for rel, _, _ in lista)
    return (
        f"[mss-spec] partida ACIMA do orçamento: {medidas}. "
        f"Não leia esses arquivos inteiros (nada de `cat`): {leia}; o resto por `grep` quando o assunto "
        "pedir. Item de backlog, fora de escopo ou diário antigo NÃO é o estado atual: não cite como "
        "fato sem conferir no código ou perguntar ao owner. "
        f"Avise o owner em 1 linha: {conserto(lista, com_marca)}."
    )


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None
        if not isinstance(evento, dict):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip() or not os.path.isdir(raiz):
            return None
        lista = estouros(raiz)
        if not lista:
            return None
        com_marca = tem_marca(raiz)
        texto = texto_do_aviso(lista, com_marca)
        if len(texto.encode("utf-8")) > TETO_TEXTO:
            return None                              # nunca injetar mais do que prometemos
        nomes = ", ".join(rel.rsplit("/", 1)[-1] for rel, _, _ in lista)
        _anotar("avisou", " ".join(f"{rel.rsplit('/', 1)[-1]}={n}" for rel, n, _ in lista), evento)
        return {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto},
            "systemMessage": f"[mss-spec] partida acima do orçamento: {nomes} — {_comando(lista, com_marca)}",
        }
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is not None:
        print(json.dumps(saida))
    sys.exit(0)                                      # SEMPRE 0 — não bloqueia


if __name__ == "__main__":
    main()
