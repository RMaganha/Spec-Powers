"""Teto ao gravar — depois de gravar MAPA/INDEX, o excesso sai na hora (move, nunca apaga).

Caso F-030: o `doctor` media o orçamento e o hook de abertura avisava, mas quem MOVIA era gente — e o Whats
chegou a 160 KB de partida. Hook `PostToolUse` roda o `rodizio_partida.enxugar` quando a gravação deixou o
arquivo acima do teto e conta o que foi pra onde. `CLAUDE.md` acima de 10 KB: só avisa (escolher o destino de
um bloco de regra é julgamento — F-029).

Propriedades:
- só age em gravação de `docs/superpowers/MAPA.md`, `docs/superpowers/INDEX.md` ou `CLAUDE.md` do projeto
  (Write/Edit/MultiEdit pelo caminho; Bash/PowerShell quando o comando cita o arquivo);
- dentro do teto → silêncio; acima → move e avisa; conteúdo vivo que não cabe → pede o resumo;
- nunca bloqueia; falha ABERTA; escape `MSS_TETO_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — a versão e o texto de cada arquivo, o estado da
conversa e o resultado do motor (`rodizio_partida.enxugar`) ficam num objeto do teste e entram como dado; os
caminhos não existem. O que o motor move (conflito de merge, `fechada` pro histórico, parar quando cabe, aviso de
conteúdo vivo) é provado em `tests/test_rodizio_partida.py`. O disco de verdade, com o motor de verdade, fica num
teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "teto_ao_gravar.py"
LONGO = "detalhe " * 120
MARCA = "<!-- mss-spec:regras-do-kit -->"
PROJ = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco" / "proj"
AGORA = 1_800_000_000.0


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("teto_ao_gravar", HOOK)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _chave(caminho):
    return os.path.normcase(os.path.abspath(str(caminho)))


def _rel(qual):
    return {"mapa": SimpleNamespace(bytes_antes=0, bytes_depois=0, passos=[], problemas=[], avisos=[]),
            "index": SimpleNamespace(bytes_antes=0, bytes_depois=0, passos=[], problemas=[], avisos=[])}[qual]


class Maquina:
    """O que o hook lê e grava, em memória: o texto e o mtime de cada arquivo, o estado de cada conversa e o
    resultado que o motor devolve. `responder` chama a regra com isso como dado e faz o papel da casca."""

    def __init__(self, mod):
        self.mod, self.arquivos, self.estados, self.anotacoes = mod, {}, {}, []
        self.resultado = {"mapa": _rel("mapa"), "index": _rel("index")}
        self.motor_chamado = 0

    # o disco
    def gravar(self, rel, texto, idade=0):
        self.arquivos[_chave(PROJ / rel)] = (texto.encode("utf-8"), int((AGORA - idade) * 1e9))

    def eh_pasta(self, caminho):
        return _chave(caminho) == _chave(PROJ)

    def versao(self, caminho):
        achado = self.arquivos.get(_chave(caminho))
        return None if achado is None else [len(achado[0]), achado[1]]

    def ler_claude(self, raiz):
        achado = self.arquivos.get(_chave(Path(raiz) / "CLAUDE.md"))
        return None if achado is None else achado[0].decode("utf-8", errors="replace")

    # o motor
    def motor(self):
        def enxugar(raiz, aplicar):
            self.motor_chamado += 1
            return self.resultado
        return SimpleNamespace(TETO_MAPA=6000, TETO_INDEX=7000, enxugar=enxugar)

    def responder(self, evento, ambiente=None):
        sessao = evento.get("session_id") if isinstance(evento, dict) else None
        estado = self.estados.setdefault(sessao, {})
        saida, mudancas = self.mod.regra(evento, ambiente or {}, self, lambda: estado, self.motor, AGORA)
        for nome in mudancas["avisados"]:
            estado.setdefault("_avisados", []).append(nome)
        for caminho in mudancas["vistos"]:
            estado[_chave(caminho)] = self.versao(caminho)
        self.anotacoes += mudancas["anotacoes"]
        return saida


@pytest.fixture()
def maq(mod):
    return Maquina(mod)


def _edit(rel="docs/superpowers/INDEX.md", tool="Edit", sessao="s1"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(PROJ), "session_id": sessao,
            "tool_input": {"file_path": str(PROJ / rel)}}


def _shell(comando, tool="Bash"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(PROJ), "session_id": "s1",
            "tool_input": {"command": comando}}


def _ctx(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


def _moveu_index(maq, antes=9000, depois=6500, passos=("Backlog → BACKLOG.md",)):
    maq.resultado["index"] = SimpleNamespace(bytes_antes=antes, bytes_depois=depois, passos=list(passos),
                                             problemas=[], avisos=[])


# --- AC1: move na hora ------------------------------------------------------------------------

def test_index_acima_do_teto_conta_o_que_foi_pra_onde(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    saida = maq.responder(_edit())
    txt = _ctx(saida)
    assert "BACKLOG.md" in txt and "nada foi apagado" in txt.lower() and "9,0 KB → 6,5 KB" in txt
    assert "releia" in txt.lower(), "não avisou pra reler antes do próximo Edit (o texto mudou de lugar)"
    assert "teto da partida" in txt
    assert saida["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_nada_a_mover_fica_calado(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    assert maq.responder(_edit()) is None
    assert maq.motor_chamado == 1


def test_dentro_do_teto_a_forma_move_e_avisa_sem_falar_em_teto(maq):
    """0.44.0: a forma vale em toda gravação — `fechada` sai do INDEX mesmo com o arquivo pequeno."""
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq, antes=900, depois=700, passos=("fechada → INDEX-historico.md",))
    saida = maq.responder(_edit())
    txt = _ctx(saida)
    assert "INDEX-historico.md" in txt and "releia" in txt.lower()
    assert "teto" not in txt.lower(), "abaixo do teto, o aviso não pode dizer que estourou"
    assert "avise o owner" not in txt.lower(), "abaixo do teto não é assunto pro owner (0.52.0)"
    assert "systemMessage" not in saida, "linha de sistema só quando o ato é do owner (0.52.0)"


def test_gravacao_de_outro_arquivo_nao_dispara(maq):
    _moveu_index(maq)
    assert maq.responder(_edit(rel="src/app.py")) is None
    assert maq.motor_chamado == 0


def test_bash_que_cita_o_index_gravado_agora_dispara(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    assert maq.responder(_shell("cat >> docs/superpowers/INDEX.md <<'EOF'\n- x\nEOF")) is not None


def test_bash_que_nao_cita_nao_dispara(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    assert maq.responder(_shell("git status")) is None


def test_bloco_vivo_pede_o_resumo_uma_vez_por_sessao(maq):
    """0.52.0: o Whats recebia o mesmo pedido em TODA edição (36× em 7 conversas). Uma vez por sessão basta;
    sessão nova pede de novo. Resumir o bloco vivo é tarefa do assistente, não do owner."""
    maq.gravar("docs/superpowers/MAPA.md", "x")
    maq.resultado["mapa"] = SimpleNamespace(bytes_antes=9000, bytes_depois=9000, passos=[], problemas=[],
                                            avisos=["MAPA.md ainda acima: resuma o bloco vivo na spec"])
    ev = _edit(rel="docs/superpowers/MAPA.md", tool="Write")
    saida = maq.responder(ev)
    txt = _ctx(saida)
    assert "resuma" in txt.lower() and "spec" in txt.lower()
    assert "avise o owner" not in txt.lower() and "não é assunto pro owner" in txt.lower()
    assert "systemMessage" not in saida, "linha de sistema só quando o ato é do owner (0.52.0)"
    assert maq.responder(ev) is None, "2ª gravação na mesma sessão, ainda acima e nada a mover: silêncio"
    assert "resuma" in _ctx(maq.responder(_edit(rel="docs/superpowers/MAPA.md", tool="Write", sessao="s2"))).lower()


def test_conflito_ou_problema_do_motor_chega_no_aviso(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    maq.resultado["index"] = SimpleNamespace(bytes_antes=9000, bytes_depois=9000, passos=[], avisos=[],
                                             problemas=["INDEX.md com conflito de merge: não mexi"])
    assert "conflito" in _ctx(maq.responder(_edit())).lower()


def test_claude_md_acima_avisa_o_owner_uma_vez_por_sessao(maq):
    """0.52.0: CLAUDE.md acima é ato do owner (upgrade ou mover bloco): avisa com linha de sistema, uma vez por sessão."""
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * 10500)
    saida = maq.responder(_edit(rel="CLAUDE.md"))
    assert "avise o owner" in _ctx(saida).lower() and "CLAUDE.md" in saida["systemMessage"]
    assert maq.motor_chamado == 0, "gravar só o CLAUDE.md não roda o enxugar"
    maq.gravar("CLAUDE.md", MARCA + "\n" + "y" * 10800)
    assert maq.responder(_edit(rel="CLAUDE.md")) is None, "mesma sessão: já avisou"
    assert maq.responder(_edit(rel="CLAUDE.md", sessao="s2")) is not None


def test_claude_md_com_marca_teto_10000_so_avisa(maq):
    maq.gravar("CLAUDE.md", "# Proj\n\n" + MARCA + "\n\n" + ("- **Regra**: " + LONGO + "\n") * 14)
    txt = _ctx(maq.responder(_edit(rel="CLAUDE.md")))
    assert "CLAUDE.md" in txt and ".claude/rules/" in txt and "nunca comprima" in txt.lower()
    assert "/mss-spec:upgrade" not in txt, "projeto já migrado não precisa de upgrade"


def test_claude_md_sem_marca_acima_do_teto_manda_upgrade(maq):
    maq.gravar("CLAUDE.md", "# Proj\n\n" + ("- **Regra**: " + LONGO + "\n") * 14)
    txt = _ctx(maq.responder(_edit(rel="CLAUDE.md")))
    assert "/mss-spec:upgrade" in txt
    assert ".claude/rules/" not in txt, "mandou mover bloco num projeto que ainda não migrou"


def test_claude_md_dentro_do_teto_fica_calado(maq):
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * 100)
    assert maq.responder(_edit(rel="CLAUDE.md")) is None


def test_kb_com_uma_casa(maq):
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * (10500 - len(MARCA) - 1))
    txt = _ctx(maq.responder(_edit(rel="CLAUDE.md")))
    assert "10,5 KB" in txt and "teto 10,0 KB" in txt


def test_kb_perto_do_teto_mostra_bytes(maq):
    """10.020 B arredondaria pra '10,0 KB (teto 10,0 KB)': mostra bytes quando o arredondado empata."""
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * (10020 - len(MARCA) - 1))
    txt = _ctx(maq.responder(_edit(rel="CLAUDE.md")))
    assert re.search(r"10\.020 B \(teto 10\.000 B\)", txt) and "10,0 KB" not in txt


def test_git_add_e_commit_do_claude_md_nao_contam_como_gravacao(maq):
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * 10500)              # mtime recente, versão nunca vista
    assert maq.responder(_shell("git add CLAUDE.md")) is None
    assert maq.responder(_shell('git commit -m "x" CLAUDE.md', "PowerShell")) is None
    assert maq.responder(_shell("  git diff CLAUDE.md")) is None
    assert maq.responder(_shell("echo x >> CLAUDE.md")) is not None   # gravação de verdade segue valendo


# --- leitura pelo shell não é gravação -------------------------------------------------------

def test_wc_c_em_claude_md_antigo_nao_dispara(maq):
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * 10500, idade=3600)
    assert maq.responder(_shell("wc -c CLAUDE.md")) is None


def test_cat_do_index_antigo_nao_roda_enxugar(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x", idade=3600)
    _moveu_index(maq)
    assert maq.responder(_shell("cat docs/superpowers/INDEX.md")) is None
    assert maq.motor_chamado == 0


def test_mesma_versao_nao_dispara_duas_vezes(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    assert maq.responder(_edit()) is not None
    assert maq.responder(_shell("wc -c docs/superpowers/INDEX.md")) is None


def test_mesma_versao_do_claude_md_nao_avisa_duas_vezes(maq):
    maq.gravar("CLAUDE.md", MARCA + "\n" + "x" * 10500)
    assert maq.responder(_edit(rel="CLAUDE.md")) is not None
    assert maq.responder(_shell("wc -c CLAUDE.md")) is None


def test_nova_gravacao_depois_da_leitura_dispara_de_novo(maq):
    """A versão vista não trava a seguinte: gravação nova pelo shell roda o enxugar de novo (0.52.0: no INDEX —
    o CLAUDE.md passou a avisar uma vez por sessão)."""
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    assert maq.responder(_edit()) is not None
    maq.gravar("docs/superpowers/INDEX.md", "xy")
    assert maq.responder(_shell("echo y >> docs/superpowers/INDEX.md")) is not None


def test_mudou_agora_janela_e_estado(mod):
    assert mod.JANELA_S == 120
    versao = [1, int(AGORA * 1e9)]
    assert mod._mudou(versao, None, AGORA) is True
    assert mod._mudou(versao, None, AGORA + 3600) is False       # fora da janela
    assert mod._mudou(versao, versao, AGORA) is False             # a mesma versão já vista
    assert mod._mudou(None, None, AGORA) is False                 # não existe


# --- AC2: escape, falha aberta ----------------------------------------------------------------

def test_escape_do_owner(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    assert maq.responder(_edit(), {"MSS_TETO_OFF": "1"}) is None


def test_entrada_malformada_libera(maq):
    for ruim in (None, [], "x", {}, {"tool_name": "Edit"}, {"tool_name": "Edit", "tool_input": "x", "cwd": "."}):
        assert maq.responder(ruim) is None


def test_motor_quebrado_fica_calado_e_ainda_marca_o_visto(maq, mod):
    maq.gravar("docs/superpowers/INDEX.md", "x")

    def quebrado():
        raise ImportError("motor")

    saida, mudancas = mod.regra(_edit(), {}, maq, lambda: {}, quebrado, AGORA)
    assert saida is None and mudancas["vistos"], "defeito no motor fez a mesma versão disparar de novo"


def test_registro_diz_o_que_moveu_sem_o_texto(maq):
    maq.gravar("docs/superpowers/INDEX.md", "x")
    _moveu_index(maq)
    maq.responder(_edit())
    assert maq.anotacoes == [("moveu", "INDEX.md=9000->6500")]


# --- o disco de verdade, com o motor de verdade, e o processo (pasta montada uma vez) -----------------

def _index_gordo():
    return ("# Índice de tarefas\n\n## Em andamento\n\n- [a](../specs/a.md) — curta — aberta\n\n## Backlog\n\n"
            + "".join(f"- ideia-{i} — {LONGO} — aberta\n" for i in range(12)))


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("teto")
    raiz, temp = base / "proj", base / "temp"
    (raiz / "docs" / "superpowers").mkdir(parents=True)
    temp.mkdir()
    (raiz / "docs" / "superpowers" / "INDEX.md").write_text(_index_gordo(), encoding="utf-8")
    (raiz / "CLAUDE.md").write_bytes((MARCA + "\nSão Paulo\n" + "x" * 10500).encode("cp1252"))   # fora de UTF-8
    return raiz, temp


def test_casca_com_o_motor_le_move_e_marca_o_visto(mod, pasta, monkeypatch):
    raiz, temp = pasta
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(temp))    # o estado da conversa vai pro temp do SO
    sp = raiz / "docs" / "superpowers"
    ev = {"hook_event_name": "PostToolUse", "tool_name": "Edit", "cwd": str(raiz), "session_id": "disco",
          "tool_input": {"file_path": str(sp / "INDEX.md")}}
    txt = _ctx(mod.responder(ev, {}))
    assert len((sp / "INDEX.md").read_bytes()) <= 7000, "o motor não moveu o excesso"
    assert "ideia-11" in (sp / "BACKLOG.md").read_text(encoding="utf-8") and "BACKLOG.md" in txt
    leitura = dict(ev, tool_name="Bash", tool_input={"command": "wc -c docs/superpowers/INDEX.md"})
    assert mod.responder(leitura, {}) is None, "a versão vista não foi gravada no estado"
    antigo = time.time() - 3600
    os.utime(sp / "INDEX.md", (antigo, antigo))
    assert mod.responder(dict(ev, session_id="outra", tool_name="Bash",
                              tool_input={"command": "cat docs/superpowers/INDEX.md"}), {}) is None, \
        "ler um INDEX antigo pelo shell contou como gravação"
    claude = _ctx(mod.responder(dict(ev, tool_input={"file_path": str(raiz / "CLAUDE.md")}), {}))
    assert ".claude/rules/" in claude and "/mss-spec:upgrade" not in claude, "o CLAUDE.md em cp1252 perdeu a marca"


def test_processo_sai_zero_com_json(pasta):
    raiz, temp = pasta
    (raiz / "docs" / "superpowers" / "MAPA.md").write_text(
        "# Mapa\n\n## Onde estamos\n\n" + ("📍 " + LONGO + "\n") * 12 + "\n## Próximo passo\n\n1. x\n", encoding="utf-8")
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_TETO_OFF", "CLAUDE_PROJECT_DIR")}
    amb.update({"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)})
    ev = {"hook_event_name": "PostToolUse", "tool_name": "Write", "cwd": str(raiz), "session_id": "proc",
          "tool_input": {"file_path": str(raiz / "docs" / "superpowers" / "MAPA.md")}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(ev), capture_output=True,
                       text=True, encoding="utf-8", env=amb, timeout=60)
    assert r.returncode == 0 and "resuma" in _ctx(json.loads(r.stdout)).lower()


def test_hook_registrado_no_post_tool_use():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    grupos = cfg["hooks"].get("PostToolUse", [])
    assert any("teto_ao_gravar.py" in h["command"] for g in grupos for h in g["hooks"])
