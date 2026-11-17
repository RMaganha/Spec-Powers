"""Ajudante pesquisador (0.58.0) — decisão 25 de `docs/specs/memoria-em-tabela.md`.

Um ajudante do kit que lê muito na janela dele e devolve só o resumo. O arquivo `agents/pesquisador.md` é
prosa (o Claude Code o carrega como `mss-spec:pesquisador`), então o que se testa aqui é o que quebra de
verdade: o arquivo existe com nome e descrição, e só dá ao ajudante as ferramentas de leitura (critério 2).
As conferências de frase nos comandos saíram na revisão da suíte de 2026-11-17.
Que ele aparece na lista de ajudantes de uma conversa nova só se prova no real (critério 1).
"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
AJUDANTE = REPO / "agents" / "pesquisador.md"


def _partes():
    """(campos do cabeçalho, corpo). O cabeçalho é lido como YAML de verdade — é assim que o Claude Code o lê:
    um `: ` solto na descrição quebraria o ajudante, e um parse por `split(":")` não veria."""
    texto = AJUDANTE.read_text(encoding="utf-8")
    assert texto.startswith("---\n"), "agents/pesquisador.md sem cabeçalho"
    _, cabecalho, corpo = texto.split("---\n", 2)
    campos = yaml.safe_load(cabecalho)
    assert isinstance(campos, dict), "o cabeçalho do ajudante não é um YAML de chave e valor"
    return {k: str(v) for k, v in campos.items()}, corpo


# --- critério 2: só leitura --------------------------------------------------------------------------

def test_ajudante_existe_com_nome_e_descricao():
    assert AJUDANTE.is_file(), "falta agents/pesquisador.md"
    campos, corpo = _partes()
    assert campos.get("name") == "pesquisador", "o nome tem de ser `pesquisador` (vira mss-spec:pesquisador)"
    assert len(campos.get("description", "")) > 80, "descrição curta demais pra dizer quando chamar"
    assert corpo.strip(), "ajudante sem texto"


def test_ajudante_so_tem_ferramentas_de_leitura():
    campos, _ = _partes()
    ferramentas = {f.strip() for f in campos.get("tools", "").split(",") if f.strip()}
    assert ferramentas == {"Read", "Grep", "Glob"}, (
        f"ferramentas do ajudante: {sorted(ferramentas)} — sem a linha `tools` ele herdaria todas, "
        "inclusive gravar arquivo e rodar comando")
    assert "disallowedTools" not in campos, "a lista de permitidas basta; duas listas se contradizem"


# --- critério 3: quando chamar e o que devolve -------------------------------------------------------


# --- critério 5: onde a regra aparece ----------------------------------------------------------------
