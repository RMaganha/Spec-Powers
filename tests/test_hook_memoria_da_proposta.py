"""Memória na hora da proposta e sintoma do owner é fato (F-047).

No Whats (2026-10-29) o desenho propôs uma etapa nova de build com Node sem abrir as duas memórias que o vetavam:
"Subida não pode depender de build" e "Contar arquivos novos antes de propor". As duas não tinham `gatilho:`
(114 de 150 memórias de lá não têm), e o recall casa as palavras do PEDIDO, não as da PROPOSTA. Medido: a busca
do kit com o texto inteiro da proposta não traz nenhuma; com o termo curto do tema (`build`, `arquivo novo`)
traz as duas. O `Stop` passa a buscar pelo tema do que a resposta propõe e devolve UMA vez o que ela não citou.

Na conversa do kit que diagnosticou o caso, a resposta disse "o assistente não se perdeu" contra o relato do
owner: memória do kit com `gatilho_resposta` devolve essa frase uma vez.

A amostra abaixo reproduz as frases-chave da proposta real (o texto da conversa do Whats não vem pro repo).
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

PROPOSTA = """Segue como ficaria. Ainda não codei nada nem gravei spec.

| Etapa | Onde | O que acontece |
|---|---|---|
| Você edita | `web/chat_v2.html` | Nada muda. |
| A imagem é montada | `Dockerfile`, numa etapa nova só de montagem | Uma ferramenta de minificação lê o arquivo e grava uma cópia enxuta. Se ela falhar, o build falha. |

- **B. Minificar no build da imagem, com Terser — minha recomendação.** O Dockerfile ganha uma etapa com Node.
- **A. Limpar na hora de servir, em Python.** Exige uma biblioteca nova no `requirements.txt`.
"""

RELATO = "O build passou e os 12 testes estão verdes. A imagem nova está no registro."


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, REPO / "hooks" / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _temp_isolado(tmp_path, monkeypatch):
    pasta = tmp_path / "temp"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))


def _memoria(pasta, nome, descricao):
    (pasta / f"{nome}.md").write_text(
        f"---\nname: {nome}\ndescription: {descricao}\nmetadata:\n  type: feedback\n---\n\ncorpo\n", encoding="utf-8")


@pytest.fixture()
def whats(tmp_path):
    """Projeto com o formato do Whats: memórias sem `gatilho:`, listadas num subíndice sem frase "quando…"."""
    raiz = tmp_path / "whats"
    mem = raiz / "memory"
    (mem / "indice").mkdir(parents=True)
    (raiz / "web").mkdir()
    (raiz / "web" / "chat_v2.html").write_text("<html></html>\n", encoding="utf-8")
    (raiz / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (raiz / "requirements.txt").write_text("flask\n", encoding="utf-8")
    _memoria(mem, "subida-nao-pode-depender-de-build",
             "Acrescentei --build ao atalho de subida para proteger de imagem defasada, e transformei falha de rede "
             "em nada sobe")
    _memoria(mem, "contar-arquivos-novos-antes-de-propor",
             "propus 4 módulos novos onde 1 bastava; arquivo novo só se justifica por capacidade que não existe")
    _memoria(mem, "fluxo-do-turno", "o fluxo do turno é a base do diagnóstico de conversa")
    (mem / "indice" / "como-eu-devo-trabalhar.md").write_text(
        "# Como eu devo trabalhar\n\n"
        "- [Subida não pode depender de build](../subida-nao-pode-depender-de-build.md) — proteção que cria modo "
        "de falha novo é regressão\n"
        "- [Contar arquivos novos antes de propor](../contar-arquivos-novos-antes-de-propor.md) — arquivo novo só "
        "por capacidade que não existe\n", encoding="utf-8")
    (mem / "MEMORY.md").write_text(
        "- **Como eu devo trabalhar** → [subíndice](indice/como-eu-devo-trabalhar.md) — 2 memórias\n",
        encoding="utf-8")
    return raiz


def _stop(raiz, texto, tmp_path, sessao="s1", ambiente=None):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "user", "message": {"content": "me mostra como ficaria"}}) + "\n",
                 encoding="utf-8")
    ev = {"hook_event_name": "Stop", "cwd": str(raiz), "session_id": sessao, "stop_hook_active": False,
          "last_assistant_message": texto, "transcript_path": str(t)}
    return _carregar("confere_citacoes").decidir(ev, ambiente or {})


# --- critério 1: a proposta real volta com as duas memórias que a vetavam -----------------------------------

def test_proposta_de_build_volta_com_as_memorias_que_a_vetam(whats, tmp_path):
    motivo = _stop(whats, PROPOSTA, tmp_path)
    assert motivo and "F-047" in motivo
    assert "subida-nao-pode-depender-de-build" in motivo or "Subida não pode depender de build" in motivo
    assert "contar-arquivos-novos-antes-de-propor" in motivo or "Contar arquivos novos antes de propor" in motivo


def test_memoria_fora_do_tema_nao_entra(whats, tmp_path):
    motivo = _stop(whats, PROPOSTA, tmp_path)
    assert "fluxo-do-turno" not in motivo


# --- critério 2: a proposta que já cita as memórias passa ----------------------------------------------------

def test_proposta_que_cita_as_memorias_passa(whats, tmp_path):
    texto = PROPOSTA + ("\nLi `memory/subida-nao-pode-depender-de-build.md` e "
                        "`memory/contar-arquivos-novos-antes-de-propor.md` antes de propor.\n")
    assert _stop(whats, texto, tmp_path) is None


def test_volta_so_uma_vez_por_sessao(whats, tmp_path):
    assert _stop(whats, PROPOSTA, tmp_path)
    assert _stop(whats, PROPOSTA, tmp_path) is None, "voltou 2× na mesma sessão"
    assert _stop(whats, PROPOSTA, tmp_path, sessao="s2"), "outra sessão não viu as memórias"


# --- critério 3 (parte de teste; a medição em respostas reais fica no histórico da spec) --------------------

def test_relato_que_so_menciona_build_passa(whats, tmp_path):
    """Resposta que relata (não propõe) não dispara: 'o build passou' não é desenho."""
    assert _stop(whats, RELATO, tmp_path) is None


def test_projeto_sem_memoria_passa(tmp_path):
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    motivo = _stop(vazio, PROPOSTA, tmp_path)
    assert motivo is None or "F-047" not in motivo, "sem memory/ não há o que buscar"


def test_escape_do_owner(whats, tmp_path):
    assert _stop(whats, PROPOSTA, tmp_path, ambiente={"MSS_MEMORIA_ACAO_OFF": "1"}) is None


# --- critério 4: "não se perdeu" contra o relato do owner volta uma vez --------------------------------------

@pytest.mark.parametrize("frase", [
    "Até onde consegui ver, o assistente não se perdeu.",
    "Pelo que li, ele não se perdeu: seguiu o roteiro.",
    "O plugin não errou aqui, o aviso é o comportamento previsto.",
])
def test_resposta_que_contraria_o_relato_volta(tmp_path, frase):
    outro = tmp_path / "outro"
    outro.mkdir()
    motivo = _stop(outro, frase, tmp_path)
    assert motivo and "feedback_sintoma_do_owner_e_fato" in motivo


def test_frase_sobre_outra_coisa_passa(tmp_path):
    outro = tmp_path / "outro"
    outro.mkdir()
    assert _stop(outro, "Para não se perder no meio, o comando mostra a etapa atual.", tmp_path) is None
