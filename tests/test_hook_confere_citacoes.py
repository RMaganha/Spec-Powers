"""Confere citações — antes de a resposta sair, o que ela CITA tem de existir no disco.

Caso F-035: a regra "não inventar fatos concretos" era prosa, e a doc da Anthropic ("Reduce
hallucinations") manda verificar com citação e retirar o que não se sustenta. Hook `Stop` lê a resposta
final (`last_assistant_message`) e confere, sem LLM, as citações verificáveis: caminho de arquivo em
`crase` ou em link (com `:linha` — a linha tem de existir), `/mss-spec:<comando>` e `F-0NN` do EVALS.
Achou o que não existe → devolve a resposta UMA vez (JSON `decision: block`, `stop_hook_active` evita laço).

Propriedades:
- citação que existe (no projeto ou no kit) → silêncio; nome solto (`MAPA.md`) casa em qualquer pasta;
- não confere: bloco de código cercado, URL, glob, placeholder (`<x>`, `${X}`), texto com espaço;
- nunca devolve duas vezes; falha ABERTA; escape `MSS_CITACOES_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o disco que ela consulta é um dicionário de
arquivos (o projeto de mentira e o pedaço do kit que os textos citam), com os mesmos métodos do `DiscoReal`. O
disco de verdade (projeto numa pasta montada uma vez, o kit deste repositório e um transcript) fica num teste só;
o processo python, num teste só. A busca na memória do projeto tem os testes dela
(`test_hook_memoria_de_acao.py`, `test_hook_memoria_da_proposta.py`); aqui ela entra vazia.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "confere_citacoes.py"
PROJ = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco" / "proj"

DO_PROJETO = {
    "services/agent_bot_core.py": "a\nb\nc\n",
    "docs/superpowers/MAPA.md": "# mapa\n",
    "docs/EVALS.md": "| F-001 | x |\n| F-012 | y |\n",
}
DO_KIT = {   # o pedaço do kit que os textos citam
    "hooks/git_publicacao.py": "x\n",
    "templates/memoria_indice.py": "x\n",
    "templates/SEGURANCA.md": "x\n",
    "commands/mapa.md": "x\n",
    "skills/precedentes-msig/SKILL.md": "x\n",
}


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("confere_citacoes", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _chave(caminho):
    return os.path.normcase(os.path.normpath(str(caminho)))


class DiscoNaMemoria:
    """O disco que a regra consulta, num dicionário {caminho: texto} — os 6 métodos do `DiscoReal`, sem arquivo."""

    def __init__(self, arquivos):
        self.arquivos = {_chave(c): t for c, t in arquivos.items()}
        self.originais = {_chave(c): os.path.normpath(str(c)) for c in arquivos}   # a caixa de cada nome

    def eh_arquivo(self, caminho):
        return _chave(caminho) in self.arquivos

    def eh_pasta(self, caminho):
        pasta = _chave(caminho) + os.sep
        return any(c.startswith(pasta) for c in self.arquivos)

    def linhas(self, caminho):
        dados = self.arquivos[_chave(caminho)]
        return dados.count("\n") + (0 if dados.endswith("\n") or not dados else 1)

    def ler(self, caminho):
        try:
            return self.arquivos[_chave(caminho)]
        except KeyError:
            raise OSError(caminho) from None

    def listar(self, raiz):
        pasta = _chave(raiz) + os.sep
        return [o[len(pasta):].replace(os.sep, "/") for c, o in self.originais.items() if c.startswith(pasta)]

    def nomes(self, pasta):
        return sorted({c.split(os.sep)[0] for c in self.listar(pasta)})


def _disco(mod, sem=(), **extra):
    arquivos = {PROJ / c: t for c, t in DO_PROJETO.items() if c not in sem}
    arquivos.update({Path(mod.KIT) / c: t for c, t in DO_KIT.items()})
    arquivos.update(extra)
    return DiscoNaMemoria(arquivos)


def _ev(texto, raiz=PROJ, **extra):
    return {"hook_event_name": "Stop", "cwd": str(raiz), "session_id": "s1", "stop_hook_active": False,
            "last_assistant_message": texto, **extra}


def _sem_memoria(*_):
    return []


def _motivo(mod, evento, ambiente=None, disco=None, memorias=_sem_memoria):
    return mod.regra(evento, ambiente or {}, disco or _disco(mod), memorias)[0]


# --- AC1: o que existe passa calado -----------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "O loop fica em `services/agent_bot_core.py`.",
    "Veja [agent_bot_core.py:2](services/agent_bot_core.py:2).",
    "Linha `services/agent_bot_core.py:3` faz isso.",
    "O `MAPA.md` diz onde estamos.",
    "Rode `/mss-spec:mapa` e `/mss-spec:precedentes-msig`.",
    "Isso é o caso F-012.",
    "Link do app: [MAPA.md](/docs/superpowers/MAPA.md).",
    "O índice fica em `superpowers/MAPA.md`.",
    "O motor é o `memoria_indice.py` do kit.",
    "Revise contra `docs/SEGURANCA.md`.",
    "O hook do kit fica em `hooks/git_publicacao.py`.",
])
def test_citacao_que_existe_passa(mod, texto):
    assert _motivo(mod, _ev(texto)) is None, f"barrou: {texto}"


# --- AC2: o que não existe devolve ------------------------------------------------------------

@pytest.mark.parametrize("texto, citado", [
    ("A regra está em `services/agent_bot_regras.py`.", "services/agent_bot_regras.py"),
    ("Veja `services/agent_bot_core.py:99`.", "services/agent_bot_core.py:99"),
    ("Abra [x](docs/NAO-EXISTE.md).", "docs/NAO-EXISTE.md"),
    ("O `CONFIG-GERAL.md` tem a chave.", "CONFIG-GERAL.md"),
    ("Rode `/mss-spec:deploy-producao`.", "/mss-spec:deploy-producao"),
    ("Isso já aconteceu no F-099.", "F-099"),
])
def test_citacao_inexistente_devolve(mod, texto, citado):
    motivo = _motivo(mod, _ev(texto))
    assert motivo is not None, f"passou: {texto}"
    assert citado in motivo, "o motivo não diz qual citação falhou"
    assert "não sei" in motivo.lower(), "o motivo não oferece o 'não sei'"


def test_linha_alem_do_fim_diz_quantas_o_arquivo_tem(mod):
    assert "3 linhas" in _motivo(mod, _ev("Veja `services/agent_bot_core.py:99`."))


# --- AC3: o que não se confere --------------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "```bash\npython services/nao_existe.py\n```",
    "Veja https://exemplo.com/docs/nao_existe.md e `https://x.io/a.py`.",
    "Qualquer `**/*.py` casa.",
    "Crie `<assunto>.md` em `docs/specs/<assunto>.md`.",
    "Use `${CLAUDE_PLUGIN_ROOT}/templates/x.py`.",
    "Rode `python services/nao_existe.py --aplicar`.",
    "| Backlog | → `docs/superpowers/BACKLOG.md` |",
    "Vou criar `hooks/confere_novo.py` com o verificador.",
    "O detalhe vai para `EM-ANDAMENTO.md`, com ponteiro.",
    "Arquivo novo: `tests/test_proposto.py`.",
    "O túnel vira um arquivo do projeto (`sql/setup/tunel-azure.py`).",
    "Não existe nenhum arquivo `indice.md` no repositório.",
])
def test_o_que_nao_e_citacao_verificavel_passa(mod, texto):
    assert _motivo(mod, _ev(texto)) is None, f"barrou: {texto}"


def test_sem_evals_no_projeto_o_caso_nao_e_conferido(mod):
    disco = _disco(mod, sem=("docs/EVALS.md",))
    assert _motivo(mod, _ev("Sem EVALS no projeto o F-777 não é conferido."), disco=disco) is None


# --- AC4: uma vez só, escape, falha aberta ----------------------------------------------------

def test_nunca_devolve_duas_vezes(mod):
    assert _motivo(mod, _ev("Veja `services/nao.py`.", stop_hook_active=True)) is None


def test_escape_do_owner(mod):
    assert _motivo(mod, _ev("Veja `services/nao.py`."), {"MSS_CITACOES_OFF": "1"}) is None


def test_pasta_do_projeto_que_nao_existe_libera(mod):
    assert _motivo(mod, _ev("Veja `services/nao.py`.", raiz=PROJ.parent / "outro")) is None


def test_entrada_malformada_libera(mod):
    for ruim in (None, [], "x", {}, {"last_assistant_message": 3}, {"cwd": "", "last_assistant_message": "`a/b.py`"}):
        assert _motivo(mod, ruim) is None


def test_le_o_transcript_quando_falta_o_texto_final(mod):
    transcript = PROJ.parent / "t.jsonl"
    linha = json.dumps({"type": "assistant", "isSidechain": False, "message": {
        "content": [{"type": "text", "text": "Veja `services/nao.py`."}]}}) + "\n"
    ev = {"hook_event_name": "Stop", "cwd": str(PROJ), "stop_hook_active": False, "transcript_path": str(transcript)}
    assert _motivo(mod, ev, disco=_disco(mod, **{str(transcript): linha})) is not None


def test_o_que_a_memoria_achou_entra_no_motivo(mod):
    """A busca na memória do projeto (testada nos arquivos dela) só soma partes ao motivo e ao registro."""
    motivo, anotacoes = mod.regra(_ev("Feito."), {}, _disco(mod), lambda *_: [("parte da memória", "memoria=x")])
    assert motivo == "parte da memória"
    assert anotacoes == [("devolveu", "memoria=x")]


# --- AC5: registro e contrato de saída ---------------------------------------------------------

def test_registro_guarda_que_devolveu_sem_o_texto(mod):
    _, anotacoes = mod.regra(_ev("Veja `services/nao.py`."), {}, _disco(mod), _sem_memoria)
    assert anotacoes == [("devolveu", "citacoes=1")]


def test_saida_pelo_contrato_do_stop(mod):
    """F-048: exit 2 + stderr era lido como "Hook script appears to be missing" nesta máquina (o `setlocale`
    do Git Bash põe "No such file or directory" no stderr de todo hook) — 40+ devoluções, nenhuma entregue.
    O contrato do Stop é JSON `{"decision": "block", "reason": …}` no stdout com exit 0."""
    assert json.loads(mod.saida("cita `x.py`")) == {"decision": "block", "reason": "cita `x.py`"}
    assert mod.saida(None) is None


def test_fonte_nao_devolve_por_exit_2():
    src = HOOK.read_text(encoding="utf-8")
    assert "sys.exit(2)" not in src, "voltou o exit 2 — a devolução deixa de chegar (F-048)"
    assert '"decision": "block"' in src


def test_hook_registrado_no_stop():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert any("confere_citacoes.py" in h["command"] for g in cfg["hooks"].get("Stop", []) for h in g["hooks"])


# --- o disco de verdade: projeto numa pasta montada uma vez, o kit deste repositório, um transcript ---------

@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("confere") / "proj"
    for caminho, texto in DO_PROJETO.items():
        (raiz / caminho).parent.mkdir(parents=True, exist_ok=True)
        (raiz / caminho).write_text(texto, encoding="utf-8")
    return raiz


def test_disco_real_confere_projeto_kit_e_transcript(mod, proj):
    assert mod.decidir(_ev("Veja `services/agent_bot_core.py:3`, o `MAPA.md` e o caso F-012.", proj), {}) is None
    assert mod.decidir(_ev("Kit: `hooks/git_publicacao.py`, `docs/SEGURANCA.md` e `/mss-spec:mapa`.", proj), {}) is None
    motivo = mod.decidir(_ev("Veja `services/agent_bot_core.py:9`, `CONFIG.md` e F-099.", proj), {})
    assert "3 linhas" in motivo and "CONFIG.md" in motivo and "F-099" in motivo
    transcript = proj.parent / "t.jsonl"
    transcript.write_text(json.dumps({"type": "assistant", "message": {
        "content": [{"type": "text", "text": "Veja `services/nao.py`."}]}}) + "\n", encoding="utf-8")
    ev = {"hook_event_name": "Stop", "cwd": str(proj), "stop_hook_active": False, "transcript_path": str(transcript)}
    assert "services/nao.py" in mod.decidir(ev, {})


def test_processo_devolve_pelo_contrato_do_stop(proj):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_CITACOES_OFF", "CLAUDE_PROJECT_DIR")}
    amb["PYTHONIOENCODING"] = "utf-8"   # o hook usa `print`; o teste só precisa ler o motivo
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_ev("Veja `services/nao.py`.", proj)),
                       capture_output=True, text=True, encoding="utf-8", env=amb, timeout=30)
    assert r.returncode == 0, r.stderr
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert saida["decision"] == "block" and "services/nao.py" in saida["reason"]
    assert not r.stderr.strip() or "setlocale" in r.stderr, "o motivo não pode ir pro stderr (vira 'script ausente')"
