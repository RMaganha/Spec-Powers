"""Comando guardado inteiro — decisão 23 de `docs/specs/memoria-em-tabela.md` (spec `comando-guardado-inteiro.md`).

Por que existe: no Whats uma anotação guardou o começo de um UPDATE, sem o WHERE, e o owner precisou reconstituir
(`docs/analise/2026-11-10-memoria-em-tabela-e-ci.md`, seção 4.7). Na mesma medição, 7 das 8 anotações com
reticências em SQL eram legítimas (exemplo de sintaxe, senha escondida) — por isso a conferência nega UMA vez e a
repetição passa.

Propriedades:
- o detector (`hooks/_comando_inteiro.py`) acha comando ou SQL com reticências em bloco de código e entre crases;
  `*****`, intervalo do git e marcador entre `<` e `>` não contam;
- a conferência roda dentro do `regra_antes_de_gravar.py` (PreToolUse Write|Edit|MultiEdit), só em `memory/*.md` e
  `memory/sessions/*.md`, só no que a gravação traz de novo, uma vez por arquivo e por conversa;
- falha ABERTA; escape `MSS_COMANDO_INTEIRO_OFF=1`;
- o `verificar` do `memoria_indice.py` só conta as antigas.

Os casos cortados foram escritos a partir da descrição da seção 4.7; o texto da anotação do Whats não foi lido.
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "regra_antes_de_gravar.py"
MODULO = REPO / "hooks" / "_comando_inteiro.py"
INDICE = REPO / "templates" / "memoria_indice.py"
CERCA = "```"


def _carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ci():
    return _carregar("_comando_inteiro", MODULO)


def _hook():
    return _carregar("regra_antes_de_gravar", HOOK)


@pytest.fixture(autouse=True)
def _temp_isolado(tmp_path, monkeypatch):
    """O estado "já avisei" vai pro temp do SO — a suíte usa um temp só dela."""
    pasta = tmp_path / "_temp"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))


def _bloco(corpo, lingua="sql"):
    return f"Rodar de novo:\n\n{CERCA}{lingua}\n{corpo}\n{CERCA}\n"


# --- detector: o que é comando cortado --------------------------------------------------------------

CORTADOS = [
    # o caso do Whats: o começo de um UPDATE, sem o WHERE
    _bloco("UPDATE mensagens SET status = 'enviada', tentativas = 0 ..."),
    # SQL de várias linhas com a linha de reticências no meio
    _bloco("SELECT id, telefone\nFROM mensagens\n...\nORDER BY criado_em DESC;"),
    # lista cortada dentro do comando
    _bloco("DELETE FROM fila WHERE id IN (101, 102, …);"),
    # comando de terminal cortado, em bloco de shell
    _bloco('sqlcmd -S servidor -d banco -Q "EXEC dbo.reprocessa @lote = 7, ..."', lingua="bash"),
    # bloco sem língua declarada, reconhecido pelo começo da linha
    _bloco("az containerapp update --name app --resource-group rg ...", lingua=""),
    # entre crases, no meio da frase
    "Para reenviar rode `UPDATE mensagens SET status = 'pendente' ...` e confira.\n",
    "Depois `git push origin feature/x ...` no terminal.\n",
    # continuação de linha no shell
    _bloco("docker run --rm \\\n  -e MODO=teste \\\n  ...", lingua="bash"),
]

INTEIROS = [
    # senha escondida não é corte
    _bloco('sqlcmd -S servidor -U usuario -P ***** -Q "SELECT 1"', lingua="bash"),
    # os três pontos são do git
    _bloco("git diff main...HEAD", lingua="bash"),
    "Compare com `git log origin/main...feature/x --oneline`.\n",
    # marcador entre < e >: exemplo de sintaxe
    _bloco("SELECT <colunas> FROM <tabela> WHERE <...>;"),
    "Formato: `UPDATE <tabela> SET <coluna> = <valor> WHERE <...>`.\n",
    # comando inteiro
    _bloco("UPDATE mensagens SET status = 'enviada' WHERE id = 42;"),
    # reticências em prosa, fora de código
    "Rodei o UPDATE e esperei... demorou, mas passou.\n",
    # saída do programa depois do comando não é o comando
    _bloco("python -m pytest tests/ -q\n........................ [100%]\n24 passed", lingua="bash"),
    # bloco de outra língua não é comando nem SQL
    _bloco("def f(*args):\n    ...\n", lingua="python"),
    _bloco("Já decidido — não reabrir:\n1. ...\n", lingua="text"),
    # reticências entre crases que não é comando
    "O campo `...` do molde fica como está.\n",
    # caminho relativo
    _bloco("cd ../..", lingua="bash"),
]


@pytest.mark.parametrize("texto", CORTADOS)
def test_detector_acha_comando_ou_sql_com_reticencias(texto):
    assert _ci().trechos_cortados(texto), texto


@pytest.mark.parametrize("texto", INTEIROS)
def test_detector_deixa_passar_o_que_nao_e_corte(texto):
    assert _ci().trechos_cortados(texto) == [], texto


def test_detector_devolve_a_linha_do_comando():
    achados = _ci().trechos_cortados(CORTADOS[0])
    assert len(achados) == 1 and achados[0].startswith("UPDATE mensagens SET status")


def test_detector_nao_levanta_com_entrada_estranha():
    ci = _ci()
    assert ci.trechos_cortados("") == [] and ci.trechos_cortados(None) == []
    assert ci.trechos_cortados(CERCA + "sql\nUPDATE x SET a = 1 ...") != []      # cerca sem fechar ainda conta


# --- quais arquivos são anotação ou diário ----------------------------------------------------------

@pytest.mark.parametrize("rel,esperado", [
    ("memory/feedback_x.md", True),
    ("memory/sessions/2026-11-12-assunto.md", True),
    ("Memory\\Sessions\\2026-11-12-assunto.md", True),
    ("memory/MEMORY.md", False),
    ("memory/DIARIO.md", False),
    ("memory/indice/ao-testar.md", False),
    ("memory/feedback_x.txt", False),
    ("docs/specs/assunto.md", False),
    ("outra/memory/feedback_x.md", False),
])
def test_so_anotacao_e_diario_sao_conferidos(rel, esperado):
    assert _ci().e_anotacao_ou_diario(rel) is esperado


# --- a conferência ao gravar (dentro do regra_antes_de_gravar.py) -----------------------------------

def _projeto(tmp_path):
    raiz = tmp_path / "proj"
    (raiz / "memory" / "sessions").mkdir(parents=True)
    return raiz


def _evento(raiz, alvo, tool="Write", sessao="s1", **entrada):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(raiz), "session_id": sessao,
            "tool_input": {"file_path": str(alvo), **entrada}}


def _motivo(saida):
    assert saida["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert saida["hookSpecificOutput"]["permissionDecision"] == "deny"
    return saida["hookSpecificOutput"]["permissionDecisionReason"]


def test_write_de_anotacao_com_sql_cortado_nega_uma_vez_e_a_repeticao_passa(tmp_path):
    raiz = _projeto(tmp_path)
    ev = _evento(raiz, raiz / "memory" / "project_reenvio.md", content=CORTADOS[0])
    hook = _hook()
    motivo = _motivo(hook.responder(ev, {}))
    assert "UPDATE mensagens SET status" in motivo and "INTEIRO" in motivo and "*****" in motivo
    assert "memory/project_reenvio.md" in motivo
    assert hook.responder(ev, {}) is None                                  # repetiu: passa


def test_write_de_diario_com_comando_cortado_nega(tmp_path):
    raiz = _projeto(tmp_path)
    ev = _evento(raiz, raiz / "memory" / "sessions" / "2026-11-12-reenvio.md", content=CORTADOS[3])
    assert "sqlcmd -S servidor" in _motivo(_hook().responder(ev, {}))


def test_uma_vez_por_arquivo_e_por_conversa(tmp_path):
    raiz = _projeto(tmp_path)
    hook = _hook()
    a = _evento(raiz, raiz / "memory" / "a.md", content=CORTADOS[0])
    b = _evento(raiz, raiz / "memory" / "b.md", content=CORTADOS[0])
    assert hook.responder(a, {}) is not None and hook.responder(a, {}) is None
    assert hook.responder(b, {}) is not None                               # outro arquivo: avisa de novo
    outra = _evento(raiz, raiz / "memory" / "a.md", sessao="s2", content=CORTADOS[0])
    assert hook.responder(outra, {}) is not None                           # outra conversa: avisa de novo


@pytest.mark.parametrize("texto", INTEIROS)
def test_write_de_anotacao_sem_corte_passa_calado(tmp_path, texto):
    raiz = _projeto(tmp_path)
    assert _hook().responder(_evento(raiz, raiz / "memory" / "a.md", content=texto), {}) is None


@pytest.mark.parametrize("rel", ["docs/specs/assunto.md", "memory/MEMORY.md", "memory/indice/x.md", "README.md"])
def test_arquivo_que_nao_e_anotacao_nem_diario_nao_e_conferido(tmp_path, rel):
    raiz = _projeto(tmp_path)
    assert _hook().responder(_evento(raiz, raiz / rel, content=CORTADOS[0]), {}) is None


def test_edit_dentro_de_bloco_que_ja_existe_e_pego_pelo_arquivo_resultante(tmp_path):
    """O texto novo do Edit vem sem a cerca (ela está fora do trecho trocado): confere-se o arquivo como vai ficar."""
    raiz = _projeto(tmp_path)
    alvo = raiz / "memory" / "project_reenvio.md"
    alvo.write_text(_bloco("UPDATE mensagens SET status = 'enviada' WHERE id = 42;"), encoding="utf-8")
    ev = _evento(raiz, alvo, tool="Edit", old_string="status = 'enviada' WHERE id = 42;",
                 new_string="status = 'enviada', tentativas = 0 ...")
    assert "UPDATE mensagens SET status = 'enviada', tentativas = 0 ..." in _motivo(_hook().responder(ev, {}))


def test_corte_que_ja_estava_no_arquivo_nao_e_cobrado_de_quem_edita_outro_trecho(tmp_path):
    """Anotação antiga com comando cortado: o comando se perdeu; editar outra linha dela não é cobrado."""
    raiz = _projeto(tmp_path)
    alvo = raiz / "memory" / "antiga.md"
    alvo.write_text("# Antiga\n\nNota velha.\n\n" + CORTADOS[0], encoding="utf-8")
    ev = _evento(raiz, alvo, tool="Edit", old_string="Nota velha.", new_string="Nota revista em 2026-11-12.")
    assert _hook().responder(ev, {}) is None
    reescreve = _evento(raiz, alvo, content="# Antiga\n\nNota reescrita.\n\n" + CORTADOS[0])
    assert _hook().responder(reescreve, {}) is None                        # Write com o mesmo corte de antes


def test_multiedit_soma_as_trocas(tmp_path):
    raiz = _projeto(tmp_path)
    alvo = raiz / "memory" / "a.md"
    alvo.write_text("# A\n\nlinha um\n\nlinha dois\n", encoding="utf-8")
    ev = _evento(raiz, alvo, tool="MultiEdit", edits=[
        {"old_string": "linha um", "new_string": "linha 1"},
        {"old_string": "linha dois", "new_string": "Rode `DELETE FROM fila WHERE id IN (1, 2, ...)`."}])
    assert "DELETE FROM fila" in _motivo(_hook().responder(ev, {}))


def test_edit_cujo_trecho_antigo_nao_existe_confere_so_o_texto_novo(tmp_path):
    raiz = _projeto(tmp_path)
    alvo = raiz / "memory" / "a.md"
    alvo.write_text("# A\n", encoding="utf-8")
    ev = _evento(raiz, alvo, tool="Edit", old_string="não está no arquivo", new_string=CORTADOS[5])
    assert _hook().responder(ev, {}) is not None


def test_escape_do_owner_desliga_so_esta_conferencia(tmp_path):
    raiz = _projeto(tmp_path)
    ev = _evento(raiz, raiz / "memory" / "a.md", content=CORTADOS[0])
    assert _hook().responder(ev, {"MSS_COMANDO_INTEIRO_OFF": "1"}) is None
    assert _hook().responder(ev, {"MSS_REGRA_OFF": "1"}) is not None       # o escape da outra cerca não desliga esta


def test_sem_numero_de_conversa_nao_age(tmp_path):
    raiz = _projeto(tmp_path)
    ev = _evento(raiz, raiz / "memory" / "a.md", sessao=None, content=CORTADOS[0])
    assert _hook().responder(ev, {}) is None


def test_defeito_na_conferencia_nao_trava_a_gravacao(tmp_path, monkeypatch):
    raiz = _projeto(tmp_path)
    hook = _hook()

    def _quebra(*_a, **_k):
        raise RuntimeError("defeito")

    monkeypatch.setattr(sys.modules["_comando_inteiro"], "trechos_cortados", _quebra)
    ev = _evento(raiz, raiz / "memory" / "a.md", content=CORTADOS[0])
    assert hook.responder(ev, {}) is None


def test_regra_por_tipo_de_arquivo_e_comando_cortado_saem_numa_negacao_so(tmp_path):
    raiz = _projeto(tmp_path)
    (raiz / "CLAUDE.md").write_text("# Proj\n\n<!-- mss-spec:regras-do-kit -->\n", encoding="utf-8")
    regras = raiz / ".claude" / "rules"
    regras.mkdir(parents=True)
    (regras / "memoria.md").write_text('---\npaths:\n  - "memory/**"\n---\n\nREGRA-DA-MEMORIA\n', encoding="utf-8")
    ev = _evento(raiz, raiz / "memory" / "a.md", content=CORTADOS[0])
    hook = _hook()
    motivo = _motivo(hook.responder(ev, {}))
    assert "REGRA-DA-MEMORIA" in motivo and "UPDATE mensagens SET status" in motivo
    assert hook.responder(ev, {}) is None


# --- a regra escrita na captura (comando-prosa: só a presença da frase) ------------------------------

def test_modo_capturar_manda_gravar_o_comando_inteiro():
    texto = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    capturar = texto.split("## Modo: capturar", 1)[1].split("## Modo: buscar", 1)[0]
    assert "comando ou SQL" in capturar and "inteiro" in capturar.lower()
    assert "reticências" in capturar and "*****" in capturar


def test_readme_dos_hooks_fala_da_conferencia():
    texto = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "_comando_inteiro.py" in texto and "MSS_COMANDO_INTEIRO_OFF" in texto


# --- anotações antigas: o verificar só conta --------------------------------------------------------

def _memoria(tmp_path):
    mem = tmp_path / "proj" / "memory"
    (mem / "indice").mkdir(parents=True)
    (mem / "sessions").mkdir()
    (mem / "MEMORY.md").write_text("# Memória\n\n- **Família** → [subíndice](indice/familia.md) — 2 memórias · quando: x\n",
                                   encoding="utf-8")
    (mem / "indice" / "familia.md").write_text(
        "# Família\n\n- **quando rodar o reenvio de mensagens** → [Reenvio](../project_reenvio.md) — como reenviar\n"
        "- **quando conferir a fila de mensagens** → [Fila](../project_fila.md) — como conferir\n", encoding="utf-8")
    frente = "---\nname: {n}\ndescription: {d}\ngatilho: quando {g}\nmetadata:\n  type: project\n---\n\n"
    (mem / "project_reenvio.md").write_text(
        frente.format(n="project_reenvio", d="como reenviar as mensagens paradas", g="rodar o reenvio de mensagens")
        + CORTADOS[0], encoding="utf-8")
    (mem / "project_fila.md").write_text(
        frente.format(n="project_fila", d="consulta que mostra a fila do dia", g="conferir a fila de mensagens")
        + INTEIROS[5], encoding="utf-8")
    (mem / "sessions" / "2026-11-01-reenvio.md").write_text("# Diário\n\n" + CORTADOS[3], encoding="utf-8")
    return mem


def test_com_comando_cortado_lista_anotacoes_e_diarios(tmp_path):
    mem = _memoria(tmp_path)
    indice = _carregar("memoria_indice", INDICE)
    assert indice.com_comando_cortado(mem) == ["project_reenvio.md", "sessions/2026-11-01-reenvio.md"]


def test_verificar_avisa_quantas_sao_e_nao_altera_nenhuma(tmp_path, capsys):
    mem = _memoria(tmp_path)
    antes = {p: p.read_bytes() for p in mem.rglob("*.md")}
    indice = _carregar("memoria_indice", INDICE)
    codigo = indice.main(["verificar", "--proj", str(mem.parent)])
    saida = capsys.readouterr().out
    assert codigo == 0, saida                                              # aviso não vira problema
    assert "2 anotação(ões) ou diário(s) com comando ou SQL com reticências" in saida
    assert "project_reenvio.md" in saida and "NÃO complete" in saida
    assert {p: p.read_bytes() for p in mem.rglob("*.md")} == antes


def test_verificar_sem_corte_nao_avisa(tmp_path, capsys):
    mem = _memoria(tmp_path)
    (mem / "project_reenvio.md").write_text(
        (mem / "project_reenvio.md").read_text(encoding="utf-8").replace(" ...", " WHERE id = 42;"), encoding="utf-8")
    (mem / "sessions" / "2026-11-01-reenvio.md").unlink()
    indice = _carregar("memoria_indice", INDICE)
    assert indice.main(["verificar", "--proj", str(mem.parent)]) == 0
    assert "reticências" not in capsys.readouterr().out
