"""Memória na hora da proposta e sintoma do owner é fato (F-047).

No Whats (2026-10-29) o desenho propôs uma etapa nova de build com Node sem abrir as duas memórias que o vetavam:
"Subida não pode depender de build" e "Contar arquivos novos antes de propor". As duas não tinham `gatilho:`
(114 de 150 memórias de lá não têm), e o recall casa as palavras do PEDIDO, não as da PROPOSTA. Medido: a busca
do kit com o texto inteiro da proposta não traz nenhuma; com o termo curto do tema (`build`, `arquivo novo`)
traz as duas. O `Stop` passa a buscar pelo tema do que a resposta propõe e devolve UMA vez o que ela não citou.

Na conversa do kit que diagnosticou o caso, a resposta disse "o assistente não se perdeu" contra o relato do
owner: memória do kit com `gatilho_resposta` devolve essa frase uma vez.

A amostra abaixo reproduz as frases-chave da proposta real (o texto da conversa do Whats não vem pro repo).

Camadas (2026-11-17): a regra do `confere_citacoes.py` é testada em memória — o disco é um dicionário de arquivos
(o projeto no formato do Whats), o motor da busca (`templates/memoria_indice.py`) entra falso com o que a busca do
kit acha pra cada termo do tema, e as leituras do `hooks/_memoria_de_acao.py` (memórias com gatilho e o "já
mostrada" da sessão) são trocadas por `monkeypatch`. Que a busca de verdade acha as duas memórias pelo termo curto
e não a fora do tema é provado em `tests/test_memoria_indice.py`; o disco e o processo do hook, em
`tests/test_hook_confere_citacoes.py`.
"""
import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parent.parent
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"          # nunca criado
WHATS, OUTRO, VAZIO = BASE / "whats", BASE / "outro", BASE / "vazio"

PROPOSTA = """Segue como ficaria. Ainda não codei nada nem gravei spec.

| Etapa | Onde | O que acontece |
|---|---|---|
| Você edita | `web/chat_v2.html` | Nada muda. |
| A imagem é montada | `Dockerfile`, numa etapa nova só de montagem | Uma ferramenta de minificação lê o arquivo e grava uma cópia enxuta. Se ela falhar, o build falha. |

- **B. Minificar no build da imagem, com Terser — minha recomendação.** O Dockerfile ganha uma etapa com Node.
- **A. Limpar na hora de servir, em Python.** Exige uma biblioteca nova no `requirements.txt`.
"""

RELATO = "O build passou e os 12 testes estão verdes. A imagem nova está no registro."


def _memoria(nome, descricao):
    return f"---\nname: {nome}\ndescription: {descricao}\nmetadata:\n  type: feedback\n---\n\ncorpo\n"


MEMORIAS_WHATS = {   # o formato do Whats: memórias sem `gatilho:`, listadas num subíndice sem frase "quando…"
    "subida-nao-pode-depender-de-build.md": _memoria(
        "subida-nao-pode-depender-de-build",
        "Acrescentei --build ao atalho de subida para proteger de imagem defasada, e transformei falha de rede em "
        "nada sobe"),
    "contar-arquivos-novos-antes-de-propor.md": _memoria(
        "contar-arquivos-novos-antes-de-propor",
        "propus 4 módulos novos onde 1 bastava; arquivo novo só se justifica por capacidade que não existe"),
    "fluxo-do-turno.md": _memoria("fluxo-do-turno", "o fluxo do turno é a base do diagnóstico de conversa"),
}


def _chave(caminho):
    return os.path.normcase(os.path.normpath(str(caminho)))


class DiscoNaMemoria:
    """O disco que a regra consulta, num dicionário {caminho: texto} — os 6 métodos do `DiscoReal`, sem arquivo."""

    def __init__(self, arquivos):
        self.arquivos = {_chave(c): t for c, t in arquivos.items()}
        self.originais = {_chave(c): os.path.normpath(str(c)) for c in arquivos}

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


DISCO = DiscoNaMemoria({
    WHATS / "web" / "chat_v2.html": "<html></html>\n",
    WHATS / "Dockerfile": "FROM python:3.12\n",
    WHATS / "requirements.txt": "flask\n",
    **{WHATS / "memory" / n: t for n, t in MEMORIAS_WHATS.items()},
    WHATS / "memory" / "indice" / "como-eu-devo-trabalhar.md": "# Como eu devo trabalhar\n",
    OUTRO / "README.md": "# outro\n",
    VAZIO / "README.md": "# vazio\n",
})


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("confere_citacoes", REPO / "hooks" / "confere_citacoes.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def indice():
    spec = importlib.util.spec_from_file_location("memoria_indice", REPO / "templates" / "memoria_indice.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def stop(mod, indice, monkeypatch):
    """`stop(raiz, texto, sessao, ambiente)` → o motivo da regra, com a memória em memória: o motor da busca falso
    (o que a busca do kit acha pra cada termo, no formato do Whats), as memórias com gatilho e o "já mostrada" de
    cada sessão num dicionário."""
    P = indice.Ponteiro
    achados = {   # termo do tema → o que a busca do kit acha no Whats (provado em tests/test_memoria_indice.py)
        "build": [P(9, indice.PRIO["memoria"], "memory/subida-nao-pode-depender-de-build.md — Acrescentei --build"),
                  P(8, indice.PRIO["diario"], "memory/sessions/2026-10-01-build.md — diário fica de fora")],
        "arquivos novos": [P(9, indice.PRIO["memoria"],
                             "memory/contar-arquivos-novos-antes-de-propor.md — propus 4 módulos novos")],
    }

    def casar(proj, termo, limite, minimo, diario):
        assert diario is False, "a busca da proposta não pede diário"
        return achados.get(termo, []) if proj == WHATS else []

    motor = SimpleNamespace(_norm=indice._norm, tokens=indice.tokens, PRIO=indice.PRIO, casar=casar)
    monkeypatch.setattr(mod, "_motor", lambda: motor)
    mem = importlib.import_module("_memoria_de_acao")          # o confere_citacoes pôs hooks/ no sys.path
    kit = (REPO / "memory" / "feedback_sintoma_do_owner_e_fato.md").read_text(encoding="utf-8")
    monkeypatch.setattr(mem, "_ler_fontes", lambda raiz: [
        ("", dict(MEMORIAS_WHATS) if Path(raiz) == WHATS else {}),
        ("(kit) ", {"feedback_sintoma_do_owner_e_fato.md": kit})])
    mostradas = {}
    monkeypatch.setattr(mem, "ja_mostradas", lambda sessao: set(mostradas.get(sessao, set())))
    monkeypatch.setattr(mem, "marcar", lambda sessao, nomes: mostradas.setdefault(sessao, set()).update(nomes))

    def rodar(raiz, texto, sessao="s1", ambiente=None):
        ev = {"hook_event_name": "Stop", "cwd": str(raiz), "session_id": sessao, "stop_hook_active": False,
              "last_assistant_message": texto}
        return mod.regra(ev, ambiente or {}, DISCO,
                         lambda t, r, s, a: mod._memorias(t, r, s, a, DISCO))[0]
    return rodar


# --- critério 1: a proposta real volta com as duas memórias que a vetavam -----------------------------------

def test_proposta_de_build_volta_com_as_memorias_que_a_vetam(stop):
    motivo = stop(WHATS, PROPOSTA)
    assert motivo and "F-047" in motivo
    assert "subida-nao-pode-depender-de-build" in motivo or "Subida não pode depender de build" in motivo
    assert "contar-arquivos-novos-antes-de-propor" in motivo or "Contar arquivos novos antes de propor" in motivo


def test_memoria_fora_do_tema_nao_entra(stop):
    motivo = stop(WHATS, PROPOSTA)
    assert "fluxo-do-turno" not in motivo and "memory/sessions/" not in motivo


# --- critério 2: a proposta que já cita as memórias passa ----------------------------------------------------

def test_proposta_que_cita_as_memorias_passa(stop):
    texto = PROPOSTA + ("\nLi `memory/subida-nao-pode-depender-de-build.md` e "
                        "`memory/contar-arquivos-novos-antes-de-propor.md` antes de propor.\n")
    assert stop(WHATS, texto) is None


def test_volta_so_uma_vez_por_sessao(stop):
    assert stop(WHATS, PROPOSTA)
    assert stop(WHATS, PROPOSTA) is None, "voltou 2× na mesma sessão"
    assert stop(WHATS, PROPOSTA, sessao="s2"), "outra sessão não viu as memórias"


# --- critério 3 (parte de teste; a medição em respostas reais fica no histórico da spec) --------------------

def test_relato_que_so_menciona_build_passa(stop):
    """Resposta que relata (não propõe) não dispara: 'o build passou' não é desenho."""
    assert stop(WHATS, RELATO) is None


def test_projeto_sem_memoria_passa(stop):
    motivo = stop(VAZIO, PROPOSTA)
    assert motivo is None or "F-047" not in motivo, "sem memory/ não há o que buscar"


def test_escape_do_owner(stop):
    assert stop(WHATS, PROPOSTA, ambiente={"MSS_MEMORIA_ACAO_OFF": "1"}) is None


# --- critério 4: "não se perdeu" contra o relato do owner volta uma vez --------------------------------------

@pytest.mark.parametrize("frase", [
    "Até onde consegui ver, o assistente não se perdeu.",
    "Pelo que li, ele não se perdeu: seguiu o roteiro.",
    "O plugin não errou aqui, o aviso é o comportamento previsto.",
])
def test_resposta_que_contraria_o_relato_volta(stop, frase):
    motivo = stop(OUTRO, frase)
    assert motivo and "feedback_sintoma_do_owner_e_fato" in motivo


def test_frase_sobre_outra_coisa_passa(stop):
    assert stop(OUTRO, "Para não se perder no meio, o comando mostra a etapa atual.") is None
