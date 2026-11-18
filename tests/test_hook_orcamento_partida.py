"""Orçamento da partida — avisa, na abertura da janela, quando os arquivos da partida estouram o teto.

Caso F-030: no Whats a partida lia `CLAUDE.md` 28 KB + `MAPA.md` 60 KB + `INDEX.md` 71 KB (tetos
10 · 6 · 7 KB). A janela passou de 73 mil pra 139 mil tokens antes da 1ª resposta, e item velho de
backlog (n8n, cotação) virou "fato" no plano de deploy. O `doctor` media e ninguém rodava.
Hook `SessionStart` mede na hora em que a leitura acontece.

Propriedades:
- dentro do teto (ou arquivo ausente) → silêncio;
- acima → `additionalContext` que nomeia SÓ os arquivos estourados, com bytes e teto, e diz o que
  ler de cada um (MAPA → "Onde estamos"; INDEX → "Em andamento") + backlog não é estado atual;
- texto ≤ 1.000 bytes mesmo com os quatro estourados;
- tetos = os do `tests/test_orcamento_contexto.py` e do `templates/rodizio_partida.py`;
- nunca bloqueia; falha ABERTA; escape `MSS_ORCAMENTO_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — os arquivos da partida de cada projeto ficam num
dicionário (caminho → bytes) e entram como dado; os caminhos não existem. O disco de verdade (CLAUDE.md em cp1252,
MAPA com comentário) fica num teste só, numa pasta montada uma vez; o processo python, num teste só.
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
HOOK = REPO / "hooks" / "orcamento_partida.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
MARCA = "<!-- mss-spec:regras-do-kit -->"


def _carregar(caminho=HOOK, nome="orcamento_partida"):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mod():
    return _carregar()


class Disco:
    """Os arquivos da partida, em memória: caminho → bytes. Os 4 métodos do `DiscoReal`."""

    def __init__(self):
        self.arquivos, self.pastas = {}, set()

    def projeto(self, nome="proj", claude=0, mapa=0, index=0, memory=0, marca=False):
        """Projeto com os arquivos da partida no tamanho pedido (0 = arquivo ausente).
        `marca=True`: o CLAUDE.md leva a linha-marca (projeto já migrado) e ainda tem `claude` bytes."""
        raiz = BASE / nome
        self.pastas.add(os.path.normcase(str(raiz)))
        for rel, n in (("CLAUDE.md", claude), ("docs/superpowers/MAPA.md", mapa),
                       ("docs/superpowers/INDEX.md", index), ("memory/MEMORY.md", memory)):
            if n:
                corpo = b"x" * n
                if rel == "CLAUDE.md" and marca:
                    cab = (MARCA + "\n").encode()
                    corpo = cab + b"x" * (n - len(cab))
                self.gravar(raiz / rel, corpo)
        return raiz

    def gravar(self, caminho, dados):
        self.arquivos[os.path.normcase(os.path.normpath(str(caminho)))] = dados

    def _de(self, caminho):
        return self.arquivos.get(os.path.normcase(os.path.normpath(str(caminho))))

    def eh_pasta(self, caminho):
        return os.path.normcase(str(caminho)) in self.pastas

    def eh_arquivo(self, caminho):
        return self._de(caminho) is not None

    def texto(self, caminho):
        dados = self._de(caminho)
        return None if dados is None else dados.decode("utf-8", errors="replace")

    def tamanho(self, caminho):
        return len(self._de(caminho))


@pytest.fixture()
def disco():
    return Disco()


def _evento(raiz, **extra):
    return {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(raiz), "session_id": "s1", **extra}


def _responder(mod, disco, raiz, ambiente=None):
    return mod.regra(_evento(raiz), ambiente or {}, disco)[0]


def _contexto(saida):
    return saida["hookSpecificOutput"]["additionalContext"]


# --- AC1: silêncio dentro do orçamento --------------------------------------------------------

def test_dentro_do_teto_fica_calado(mod, disco):
    raiz = disco.projeto(claude=8000, mapa=3000, index=5000, memory=3000)
    assert _responder(mod, disco, raiz) is None


def test_projeto_sem_os_arquivos_fica_calado(mod, disco):
    assert _responder(mod, disco, disco.projeto()) is None


# --- AC2: acima do teto avisa, só do que estourou ---------------------------------------------

def test_numeros_do_whats_avisam_mapa_index_e_claude(mod, disco):
    """Os tamanhos reais da janela do F-030."""
    raiz = disco.projeto(claude=27933, mapa=60098, index=70720, memory=1661)
    txt = _contexto(_responder(mod, disco, raiz))
    for nome in ("CLAUDE.md", "MAPA.md", "INDEX.md"):
        assert nome in txt, f"não citou {nome} estourado"
    assert "MEMORY.md" not in txt, "citou o índice de memória, que está dentro do teto"
    assert "60,1 KB" in txt and "teto 6,0 KB" in txt, "não deu bytes e teto do MAPA"


def test_mapa_estourado_manda_ler_so_onde_estamos(mod, disco):
    txt = _contexto(_responder(mod, disco, disco.projeto(mapa=20000)))
    assert "Onde estamos" in txt
    assert "INDEX.md" not in txt, "citou o INDEX, que nem existe"


def test_index_estourado_manda_ler_so_em_andamento(mod, disco):
    assert "Em andamento" in _contexto(_responder(mod, disco, disco.projeto(index=20000)))


def test_aviso_diz_que_backlog_nao_e_estado_atual(mod, disco):
    """O n8n e a cotação do F-030 vieram do backlog lido como fato."""
    txt = _contexto(_responder(mod, disco, disco.projeto(index=20000))).lower()
    assert "backlog" in txt and "não" in txt and "fato" in txt


def test_aviso_manda_nao_ler_inteiro_e_nao_avisa_o_owner(mod, disco):
    """0.52.0: MAPA/INDEX acima é tarefa do assistente (resumir o bloco vivo pra spec), não assunto pro owner."""
    saida = _responder(mod, disco, disco.projeto(mapa=20000))
    txt = _contexto(saida)
    assert "inteiro" in txt, "não disse pra não ler o arquivo inteiro"
    assert "avise o owner" not in txt.lower() and "/mss-spec:doctor" not in txt, "MAPA acima não é assunto pro owner"
    assert "resum" in txt.lower() and "spec" in txt.lower(), "não lembrou o assistente de resumir o bloco vivo pra spec"
    assert "systemMessage" not in saida, "linha de sistema só quando o ato é do owner"


def test_comentario_nao_conta_no_mapa_e_no_index(mod, disco):
    """0.52.0: o molde traz 1.805 B de comentário no MAPA (30% do teto) — comentário não é conteúdo da partida."""
    raiz = disco.projeto()
    coment = "<!-- " + "guia " * 360 + "-->\n"              # ~1.800 B, como o molde
    disco.gravar(raiz / "docs/superpowers/MAPA.md", (coment + "x" * 5000).encode())
    disco.gravar(raiz / "docs/superpowers/INDEX.md", ("﻿" + coment + "y" * 6000).encode())
    assert _responder(mod, disco, raiz) is None, "6,8 KB no disco mas 5,0 KB de conteúdo: dentro do teto"
    disco.gravar(raiz / "docs/superpowers/MAPA.md", b"x" * 6100)
    assert "MAPA.md" in _contexto(_responder(mod, disco, raiz)), "6,1 KB de conteúdo: avisa"


def test_medida_igual_no_hook_e_no_rodizio(mod):
    """Hooks não importam do rodízio: a medida 'só conteúdo' é copiada, e este teste trava a cópia."""
    rod = _carregar(REPO / "templates" / "rodizio_partida.py", "rodizio_partida_ref")
    for t in ("abc", "a<!-- x -->b", "<!-- a\nb -->c<!-- d -->", "sem fim <!-- aberto", "ação ✓ — ≤"):
        assert mod._bytes_de_conteudo(t) == rod.bytes_de_conteudo(t), t


def test_texto_cabe_em_mil_bytes_com_tudo_estourado(mod, disco):
    for marca in (False, True):
        raiz = disco.projeto(str(marca), claude=99999, mapa=99999, index=99999, memory=99999, marca=marca)
        txt = _contexto(_responder(mod, disco, raiz))
        assert len(txt.encode("utf-8")) <= 1000, f"aviso com {len(txt.encode('utf-8'))} bytes (marca={marca})"


def test_kb_com_uma_casa_decimal(mod, disco):
    """10.096 B não pode sair 'CLAUDE.md 10 KB (teto 10 KB)' — contradiz a si mesmo."""
    assert "10,1 KB (teto 10,0 KB)" in _contexto(_responder(mod, disco, disco.projeto(claude=10096)))


def test_kb_perto_do_teto_mostra_bytes(mod, disco):
    """10.020 B não pode sair '10,0 KB (teto 10,0 KB)': quando o arredondado empata, mostra bytes."""
    txt = _contexto(_responder(mod, disco, disco.projeto(claude=10020)))
    assert "10.020 B (teto 10.000 B)" in txt and "10,0 KB" not in txt


def test_claude_sem_marca_acima_do_teto_manda_upgrade(mod, disco):
    saida = _responder(mod, disco, disco.projeto(claude=10500))
    txt = _contexto(saida)
    assert "/mss-spec:upgrade" in txt
    assert "/mss-spec:doctor" not in txt
    assert "/mss-spec:doctor" not in saida["systemMessage"]


def test_claude_com_marca_acima_do_teto_manda_mover_bloco(mod, disco):
    txt = _contexto(_responder(mod, disco, disco.projeto(claude=10500, marca=True)))
    assert "mover bloco" in txt and "/mss-spec:upgrade" not in txt
    assert "/mss-spec:doctor" not in txt


def test_owner_e_doctor_so_quando_estoura_memory(mod, disco):
    """0.52.0: do trio MAPA/INDEX/MEMORY só o MEMORY pede ato do owner (OK pro `memoria_indice.py dividir`)."""
    saida = _responder(mod, disco, disco.projeto("m", memory=20000))
    txt = _contexto(saida)
    assert "avise o owner" in txt.lower() and "/mss-spec:doctor" in txt and "dividir" in txt
    assert "MEMORY.md" in saida["systemMessage"]
    for kw in ({"mapa": 20000}, {"index": 20000}):
        saida = _responder(mod, disco, disco.projeto(next(iter(kw)), **kw))
        assert "/mss-spec:doctor" not in _contexto(saida) and "systemMessage" not in saida, kw


def test_marca_igual_nos_hooks(mod):
    """Hooks não importam um do outro: a constante é copiada, e este teste trava as cópias."""
    ref = _carregar(REPO / "hooks" / "regras_do_kit.py", "regras_do_kit_ref").MARCA
    assert mod.MARCA == ref
    assert _carregar(REPO / "hooks" / "teto_ao_gravar.py", "teto_ao_gravar_ref").MARCA == ref
    assert _carregar(REPO / "hooks" / "regra_antes_de_gravar.py", "regra_antes_de_gravar_ref").MARCA == ref


def test_saida_e_do_evento_session_start_com_system_message(mod, disco):
    """A linha de sistema existe só quando o ato é do owner (0.52.0): aqui, o MEMORY.md; MAPA junto não entra nela."""
    saida = _responder(mod, disco, disco.projeto(mapa=20000, memory=20000))
    assert saida["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "MEMORY.md" in saida["systemMessage"] and "MAPA.md" not in saida["systemMessage"]


def test_prefere_claude_project_dir_ao_cwd(mod, disco):
    proj = disco.projeto("proj", mapa=20000)
    saida = mod.regra(_evento(BASE / "outro"), {"CLAUDE_PROJECT_DIR": str(proj)}, disco)[0]
    assert saida is not None and "MAPA.md" in _contexto(saida)


def test_registro_diz_os_tamanhos_sem_o_texto(mod, disco):
    _, anotacoes = mod.regra(_evento(disco.projeto(mapa=20000)), {}, disco)
    assert anotacoes == [("avisou", "MAPA.md=20000")]


# --- AC3: escape e falha aberta ---------------------------------------------------------------

def test_escape_do_owner(mod, disco):
    assert _responder(mod, disco, disco.projeto(mapa=20000), {"MSS_ORCAMENTO_OFF": "1"}) is None


def test_entrada_malformada_libera(mod, disco):
    for ruim in (None, [], "texto", {}, {"cwd": 42}, {"cwd": ""}):
        assert mod.regra(ruim, {}, disco)[0] is None


# --- AC4: tetos numa fonte só -----------------------------------------------------------------

def test_tetos_batem_com_o_teste_de_orcamento_e_o_rodizio(mod):
    orc = _carregar(REPO / "tests" / "test_orcamento_contexto.py", "test_orcamento_contexto_ref")
    rod = _carregar(REPO / "templates" / "rodizio_partida.py", "rodizio_partida_ref")
    tetos = dict(mod.ARQUIVOS)
    assert tetos["CLAUDE.md"] == orc.TETO_CLAUDE_MD
    assert tetos["docs/superpowers/MAPA.md"] == orc.TETO_MAPA == rod.TETO_MAPA
    assert tetos["docs/superpowers/INDEX.md"] == orc.TETO_INDEX == rod.TETO_INDEX
    assert tetos["memory/MEMORY.md"] == orc.TETO_MEMORY_TOPO


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("orcamento")
    (raiz / "docs" / "superpowers").mkdir(parents=True)
    (raiz / "CLAUDE.md").write_bytes((MARCA + "\nSão Paulo\n" + "x" * 10500).encode("cp1252"))   # fora de UTF-8
    (raiz / "docs" / "superpowers" / "MAPA.md").write_text("<!-- " + "guia " * 360 + "-->\n" + "x" * 6100,
                                                            encoding="utf-8")
    return raiz


def test_casca_le_tamanho_texto_e_marca_do_disco(mod, proj):
    txt = _contexto(mod.responder(_evento(proj), {}))
    assert "mover bloco" in txt and "/mss-spec:upgrade" not in txt, "o CLAUDE.md em cp1252 perdeu a marca"
    assert "MAPA.md 6,1 KB" in txt, "o MAPA do disco não foi medido sem o comentário"


def test_processo_avisa_com_json_e_sai_zero(proj):
    amb = {**os.environ}
    amb.pop("MSS_ORCAMENTO_OFF", None)
    amb.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_evento(proj)), text=True,
                       capture_output=True, env=amb, encoding="utf-8", timeout=30)
    assert r.returncode == 0 and "MAPA.md" in _contexto(json.loads(r.stdout))


def test_hook_registrado_no_session_start():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupo in cfg["hooks"].get("SessionStart", []) for h in grupo["hooks"]]
    assert any("orcamento_partida.py" in c for c in comandos), "orcamento_partida.py fora do SessionStart"
