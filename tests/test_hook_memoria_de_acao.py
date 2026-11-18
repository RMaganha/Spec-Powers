"""Memória na hora da ação (F-034) e resposta com rotas não pedidas (F-033).

F-034: o recall casa o prompt do owner; memória cujo gatilho é uma AÇÃO do assistente não chegava — o heredoc
com acento quebrou 3 vezes com a memória existindo, e "falta atualizar o plugin" foi dito com a memória da
junction dizendo o contrário. Memória declara `gatilho_comando:`/`gatilho_resposta:` (regex); o comando que
casa é negado UMA vez por sessão com a memória no motivo; a resposta que casa volta UMA vez por sessão.

F-033: o owner pediu um passo a passo e recebeu "Rota 1 / Rota 2", "dia definitivo", pendências. Medido em 211
respostas reais: ≥ 2 marcadores de rota alternativa numa resposta de mais de 300 palavras, sem o pedido falar
em opções, só pega a resposta do caso.

Camadas (2026-11-17): a REGRA (`memorias_de`, `casar_em`) é testada em memória — as memórias do projeto de teste
e as do kit (lidas do repositório) entram como texto, e as já mostradas de cada conversa ficam num dicionário.
Dentro do `git_publicacao.py` e do `confere_citacoes.py`, as leituras do módulo `_memoria_de_acao` são trocadas
pelas de memória, como no `test_hook_outro_projeto_shell.py`. O disco de verdade (ler `memory/` do projeto e do
kit, gravar e ler as já mostradas) fica num teste só, numa pasta montada uma vez. O processo é dos dois hooks,
nos testes deles.
"""
import functools
import importlib
import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROJ = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco" / "proj"
OUTRO = PROJ.parent / "outro"

DO_PROJETO = {
    "feedback_nao_rodar_seed.md": (
        "---\nname: feedback_nao_rodar_seed\ndescription: o seed apaga a base de homologação\n"
        "gatilho: quando for popular a base\ngatilho_comando: \\bseed\\.py\\b\n"
        "gatilho_resposta: (?i)rode o seed\nmetadata:\n  type: feedback\n---\n"),
    "velha.md": "---\nname: velha\nobsoleta: 2026-01-01\ngatilho_comando: \\bls\\b\n---\n",
    "quebrada.md": "---\nname: quebrada\ngatilho_comando: ([\n---\n",
}


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, REPO / "hooks" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@functools.lru_cache(maxsize=1)
def _do_kit():
    """As memórias do kit, como texto (o repositório é lido, nada é criado)."""
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((REPO / "memory").glob("*.md"))}


def _fontes(raiz):
    projeto = DO_PROJETO if str(raiz) == str(PROJ) else {}
    return [("", projeto), ("(kit) ", _do_kit())]


@pytest.fixture()
def mem(monkeypatch):
    """O `_memoria_de_acao` que os hooks importam pelo `sys.path`, com as leituras trocadas pelas de memória: as
    memórias vêm de `_fontes` e as já mostradas de cada conversa ficam num dicionário."""
    _carregar("git_publicacao")                       # põe a pasta dos hooks no sys.path
    m = importlib.import_module("_memoria_de_acao")
    mostradas = {}
    monkeypatch.setattr(m, "memorias", lambda raiz, qual: m.memorias_de(_fontes(raiz), qual))
    monkeypatch.setattr(m, "ja_mostradas", lambda sessao: set(mostradas.get(sessao, set())))
    monkeypatch.setattr(m, "marcar", lambda sessao, nomes: mostradas.setdefault(sessao, set()).update(nomes))
    return m


# --- a regra: quais memórias valem e quais casam ---------------------------------------------------

def test_obsoleta_e_regex_quebrado_nao_contam():
    m = _carregar("_memoria_de_acao")
    nomes = [n for n, _, _, _ in m.memorias_de([("", DO_PROJETO)], "comando")]
    assert nomes == ["feedback_nao_rodar_seed"]


def test_a_do_projeto_vence_a_do_kit_de_mesmo_nome():
    m = _carregar("_memoria_de_acao")
    kit = {"feedback_nao_rodar_seed.md": DO_PROJETO["feedback_nao_rodar_seed.md"].replace("seed", "outro")}
    achadas = m.memorias_de([("", DO_PROJETO), ("(kit) ", kit)], "comando")
    assert [(n, onde) for n, onde, _, _ in achadas] == [("feedback_nao_rodar_seed", "memory/feedback_nao_rodar_seed.md")]


def test_ja_mostrada_nao_casa_de_novo():
    m = _carregar("_memoria_de_acao")
    lista = m.memorias_de([("", DO_PROJETO)], "comando")
    assert [x[0] for x in m.casar_em("python seed.py", lista, set())] == ["feedback_nao_rodar_seed"]
    assert m.casar_em("python seed.py", lista, {"feedback_nao_rodar_seed"}) == []


# --- F-034, lado do comando (dentro do git_publicacao.py) -----------------------------------------------

def _cmd(raiz, comando, sessao="s1", **amb):
    ev = {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(raiz)}
    if sessao:
        ev["session_id"] = sessao
    ambiente = {"CLAUDE_PROJECT_DIR": str(raiz), "MSS_ANCORA_OFF": "1", "MSS_PASTA_BRANCH_OFF": "1", **amb}
    return _carregar("git_publicacao").avaliar(ev, ambiente, git_destino=lambda p: ("feature/x", None))


def test_comando_que_casa_a_memoria_e_negado_com_ela_no_motivo(mem):
    tipo, motivo = _cmd(PROJ, "python seed.py --tudo")
    assert tipo == "deny"
    assert "feedback_nao_rodar_seed" in motivo and "apaga a base" in motivo
    assert "repita" in motivo.lower(), "o motivo não diz que repetir o comando passa"


def test_so_uma_vez_por_sessao(mem):
    assert _cmd(PROJ, "python seed.py")[0] == "deny"
    assert _cmd(PROJ, "python seed.py")[0] is None, "negou de novo na mesma sessão"
    assert _cmd(PROJ, "python seed.py", sessao="s2")[0] == "deny", "outra sessão não viu a memória"


def test_comando_que_nao_casa_passa(mem):
    assert _cmd(PROJ, "python app.py")[0] is None
    assert _cmd(PROJ, "ls -la")[0] is None, "a memória obsoleta valeu"


def test_escape_do_owner(mem):
    assert _cmd(PROJ, "python seed.py", MSS_MEMORIA_ACAO_OFF="1")[0] is None


def test_sem_numero_de_sessao_a_memoria_nao_age(mem):
    """Sem `session_id` não há como garantir "uma vez por sessão": o estado caía num arquivo único
    (`…_sem-sessao.json`), dividido por toda conversa e por toda rodada da suíte. Com os 26 gatilhos do kit
    (0.57.0), `git checkout -b` num teste da cerca de publicação era negado na 1ª rodada e passava na 2ª."""
    assert _cmd(PROJ, "python seed.py", sessao=None)[0] is None
    assert _cmd(PROJ, "python seed.py")[0] == "deny", "o evento sem sessão gastou a vez de uma sessão de verdade"


def test_memoria_do_kit_vale_em_qualquer_projeto(mem):
    """O heredoc com acento é memória da MÁQUINA: mora no kit e vale no Whats também."""
    tipo, motivo = _cmd(OUTRO, "python - <<'PYEOF'\nprint('ação')\nPYEOF")
    assert tipo == "deny" and "project_heredoc_grande_com_acento_quebra_no_git_bash" in motivo


def test_heredoc_sem_acento_passa(mem):
    assert _cmd(OUTRO, "python - <<'PYEOF'\nprint('ok')\nPYEOF")[0] is None


# --- lado da resposta (F-034, dentro do confere_citacoes.py) e rotas (F-033) ---------------------------

def _resposta(mem, raiz, texto, sessao="s1"):
    partes = _carregar("confere_citacoes")._memorias(texto, str(raiz), sessao, {})
    return "\n\n".join(p for p, _ in partes) or None


def test_resposta_que_casa_a_memoria_volta_uma_vez(mem):
    motivo = _resposta(mem, PROJ, "Pronto. Agora rode o seed pra popular.")
    assert motivo and "feedback_nao_rodar_seed" in motivo
    assert _resposta(mem, PROJ, "Pronto. Agora rode o seed pra popular.") is None, "voltou 2× na mesma sessão"


def test_frase_real_do_plugin_casa_a_memoria_da_junction(mem):
    frase = "Para o hook novo valer nas próximas janelas, falta atualizar o plugin nesta máquina para a 0.32.0."
    motivo = _resposta(mem, OUTRO, frase)
    assert motivo and "project_mss_spec_instalado_por_junction" in motivo


# F-052 (2026-11-06): "a atualização do marketplace local" foi dita como passo pós-push com a junção ainda viva —
# a decisão de 2026-11-03 (marketplace local, execução em conversa nova) foi lida como estado. O regex da memória
# não casava "marketplace": agora casa update/atualização do marketplace, e não casa o `marketplace.json` nem o `add`.
@pytest.mark.parametrize("frase", [
    "Depois do push, a atualização do marketplace local no app é o que leva o kit novo pros outros projetos.",
    "Owner: atualizar o marketplace local no app (decisão 2026-11-03).",
    "Pronto. Agora rode `/plugin marketplace update mss-local` pra os outros projetos receberem a 0.53.0.",
])
def test_frases_do_marketplace_casam_a_memoria_da_junction(mem, frase):
    motivo = _resposta(mem, OUTRO, frase)
    assert motivo and "project_mss_spec_instalado_por_junction" in motivo, frase


@pytest.mark.parametrize("frase", [
    "A versão vive nos dois manifestos: `plugin.json` e `marketplace.json`, ambos em 0.53.0.",
    "Atualizei o MAPA e o CHANGELOG; a suíte segue verde.",
    "Pra instalar noutra máquina: `/plugin marketplace add C:/ferramentas/mss-spec`.",
])
def test_frases_sem_atualizacao_do_kit_passam(mem, frase):
    motivo = _resposta(mem, OUTRO, frase)
    assert not (motivo and "project_mss_spec_instalado_por_junction" in motivo), frase


LONGA = " ".join(["passo"] * 320)


def test_rotas_nao_pedidas_numa_resposta_longa_voltam():
    cc = _carregar("confere_citacoes")
    texto = f"{LONGA}\n**Rota 1 — direto do servidor**\n...\n**Rota 2 — pela sua máquina**\n..."
    assert cc.rotas_nao_pedidas(texto, "me passa o passo a passo")
    assert "F-033" in cc.MOTIVO_ROTAS and "pergunt" in cc.MOTIVO_ROTAS.lower()


def test_rotas_pedidas_passam():
    texto = f"{LONGA}\n**Opção A**\n...\n**Opção B**\n..."
    assert not _carregar("confere_citacoes").rotas_nao_pedidas(texto, "quais as opções pra fazer o restore?")


def test_resposta_curta_com_duas_opcoes_passa():
    assert not _carregar("confere_citacoes").rotas_nao_pedidas("Rota 1: servidor. Rota 2: sua máquina. Qual vale?",
                                                                "me passa o passo a passo")


def test_devolucao_sai_pelo_contrato_do_stop_nao_pelo_stderr():
    """0.35.0 → 0.49.0: o motivo saía por `print` no stderr com exit 2. F-048 mostrou que nesta máquina isso
    era lido como "Hook script appears to be missing" (o `setlocale` do Git Bash põe "No such file or
    directory" no stderr de todo hook) e a devolução nunca chegava. Agora: JSON no stdout, exit 0, ASCII puro
    (`json.dumps` escapa os acentos, então a página de código do console não importa)."""
    src = (REPO / "hooks" / "confere_citacoes.py").read_text(encoding="utf-8")
    assert "sys.stderr.buffer.write" not in src
    assert "print(motivo, file=sys.stderr)" not in src
    assert 'json.dumps({"decision": "block", "reason": motivo})' in src


# --- o disco de verdade (pasta montada uma vez) ----------------------------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("memoria_acao")
    raiz, temp = base / "proj", base / "temp"
    (raiz / "memory").mkdir(parents=True)
    temp.mkdir()
    for nome, texto in DO_PROJETO.items():
        (raiz / "memory" / nome).write_text(texto, encoding="utf-8")
    (raiz / "memory" / "binaria.md").write_bytes(b"\xff\xfe---\ngatilho_comando: x\n---\n")   # ilegível
    return raiz, temp


def test_disco_le_memory_do_projeto_e_do_kit_e_guarda_as_mostradas(pasta, monkeypatch):
    raiz, temp = pasta
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    m = _carregar("_memoria_de_acao")
    nomes = [n for n, _, _, _ in m.memorias(str(raiz), "comando")]
    assert "feedback_nao_rodar_seed" in nomes and "project_heredoc_grande_com_acento_quebra_no_git_bash" in nomes
    assert "velha" not in nomes and "quebrada" not in nomes and "binaria" not in nomes
    assert [x[0] for x in m.casar("python seed.py", "comando", str(raiz), "d1")] == ["feedback_nao_rodar_seed"]
    m.marcar("d1", ["feedback_nao_rodar_seed"])
    assert m.casar("python seed.py", "comando", str(raiz), "d1") == [], "a já mostrada não foi gravada ou lida"
    assert m.casar("python seed.py", "comando", str(raiz), "d2"), "outra conversa herdou a já mostrada"
