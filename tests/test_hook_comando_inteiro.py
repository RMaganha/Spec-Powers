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

Camadas (2026-11-17): a REGRA (`regra` deste módulo, chamada pela `regra` do `regra_antes_de_gravar.py`) é testada em
memória — o conteúdo de cada arquivo do projeto, as regras e o CLAUDE.md, e os arquivos já avisados de cada conversa
ficam num objeto do teste e entram como dado; os caminhos não existem. O disco de verdade (ler o arquivo antes do
Edit, gravar e ler o já avisado) fica num teste só. O processo é o do `regra_antes_de_gravar.py`, no teste dele.
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
PROJ = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco" / "proj"
CERCA = "```"


def _carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ci():
    return _carregar("_comando_inteiro_teste", MODULO)


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
def test_detector_acha_comando_ou_sql_com_reticencias(ci, texto):
    assert ci.trechos_cortados(texto), texto


@pytest.mark.parametrize("texto", INTEIROS)
def test_detector_deixa_passar_o_que_nao_e_corte(ci, texto):
    assert ci.trechos_cortados(texto) == [], texto


def test_detector_devolve_a_linha_do_comando(ci):
    achados = ci.trechos_cortados(CORTADOS[0])
    assert len(achados) == 1 and achados[0].startswith("UPDATE mensagens SET status")


def test_detector_nao_levanta_com_entrada_estranha(ci):
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
def test_so_anotacao_e_diario_sao_conferidos(ci, rel, esperado):
    assert ci.e_anotacao_ou_diario(rel) is esperado


# --- a conferência ao gravar (dentro do regra_antes_de_gravar.py) -----------------------------------

class Maquina:
    """O que as duas conferências leem e gravam, em memória: o conteúdo de cada arquivo do projeto, o CLAUDE.md e
    as regras, as regras já mostradas e os arquivos já avisados de cada conversa. `responder` chama a regra do
    `regra_antes_de_gravar.py` com a deste módulo dentro, e faz o papel das duas cascas."""

    def __init__(self, ci):
        self.ci = ci
        self.hook = _carregar("regra_antes_de_gravar_teste", HOOK)
        self.arquivos, self.claude, self.regras, self.mostradas, self.avisados = {}, None, {}, {}, {}

    def comando_cortado(self, evento, rel, raiz, ambiente):
        texto, chave = self.ci.regra(evento, rel, ambiente, lambda: self.arquivos.get(rel),
                                     lambda sessao: self.avisados.get(sessao, set()))
        if chave:
            self.avisados.setdefault(evento.get("session_id"), set()).add(chave)
        return texto

    def responder(self, evento, ambiente=None):
        saida, mudancas = self.hook.regra(
            evento, ambiente or {}, lambda raiz: self.claude, lambda raiz: dict(self.regras),
            lambda sessao: self.mostradas.get(sessao, set()), self.comando_cortado)
        if mudancas.get("mostradas"):
            self.mostradas.setdefault(evento.get("session_id"), set()).update(mudancas["mostradas"])
        return saida


@pytest.fixture()
def maq(ci):
    return Maquina(ci)


def _evento(rel, tool="Write", sessao="s1", **entrada):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(PROJ), "session_id": sessao,
            "tool_input": {"file_path": str(PROJ / rel), **entrada}}


def _motivo(saida):
    assert saida["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert saida["hookSpecificOutput"]["permissionDecision"] == "deny"
    return saida["hookSpecificOutput"]["permissionDecisionReason"]


def test_write_de_anotacao_com_sql_cortado_nega_uma_vez_e_a_repeticao_passa(maq):
    ev = _evento("memory/project_reenvio.md", content=CORTADOS[0])
    motivo = _motivo(maq.responder(ev))
    assert "UPDATE mensagens SET status" in motivo and "INTEIRO" in motivo and "*****" in motivo
    assert "memory/project_reenvio.md" in motivo
    assert maq.responder(ev) is None                                       # repetiu: passa


def test_write_de_diario_com_comando_cortado_nega(maq):
    ev = _evento("memory/sessions/2026-11-12-reenvio.md", content=CORTADOS[3])
    assert "sqlcmd -S servidor" in _motivo(maq.responder(ev))


def test_uma_vez_por_arquivo_e_por_conversa(maq):
    a = _evento("memory/a.md", content=CORTADOS[0])
    assert maq.responder(a) is not None and maq.responder(a) is None
    assert maq.responder(_evento("memory/b.md", content=CORTADOS[0])) is not None       # outro arquivo
    assert maq.responder(_evento("memory/a.md", sessao="s2", content=CORTADOS[0])) is not None   # outra conversa


@pytest.mark.parametrize("texto", INTEIROS)
def test_write_de_anotacao_sem_corte_passa_calado(maq, texto):
    assert maq.responder(_evento("memory/a.md", content=texto)) is None


@pytest.mark.parametrize("rel", ["docs/specs/assunto.md", "memory/MEMORY.md", "memory/indice/x.md", "README.md"])
def test_arquivo_que_nao_e_anotacao_nem_diario_nao_e_conferido(maq, rel):
    assert maq.responder(_evento(rel, content=CORTADOS[0])) is None


def test_edit_dentro_de_bloco_que_ja_existe_e_pego_pelo_arquivo_resultante(maq):
    """O texto novo do Edit vem sem a cerca (ela está fora do trecho trocado): confere-se o arquivo como vai ficar."""
    maq.arquivos["memory/project_reenvio.md"] = _bloco("UPDATE mensagens SET status = 'enviada' WHERE id = 42;")
    ev = _evento("memory/project_reenvio.md", tool="Edit", old_string="status = 'enviada' WHERE id = 42;",
                 new_string="status = 'enviada', tentativas = 0 ...")
    assert "UPDATE mensagens SET status = 'enviada', tentativas = 0 ..." in _motivo(maq.responder(ev))


def test_corte_que_ja_estava_no_arquivo_nao_e_cobrado_de_quem_edita_outro_trecho(maq):
    """Anotação antiga com comando cortado: o comando se perdeu; editar outra linha dela não é cobrado."""
    maq.arquivos["memory/antiga.md"] = "# Antiga\n\nNota velha.\n\n" + CORTADOS[0]
    ev = _evento("memory/antiga.md", tool="Edit", old_string="Nota velha.", new_string="Nota revista em 2026-11-12.")
    assert maq.responder(ev) is None
    reescreve = _evento("memory/antiga.md", content="# Antiga\n\nNota reescrita.\n\n" + CORTADOS[0])
    assert maq.responder(reescreve) is None                                # Write com o mesmo corte de antes


def test_multiedit_soma_as_trocas(maq):
    maq.arquivos["memory/a.md"] = "# A\n\nlinha um\n\nlinha dois\n"
    ev = _evento("memory/a.md", tool="MultiEdit", edits=[
        {"old_string": "linha um", "new_string": "linha 1"},
        {"old_string": "linha dois", "new_string": "Rode `DELETE FROM fila WHERE id IN (1, 2, ...)`."}])
    assert "DELETE FROM fila" in _motivo(maq.responder(ev))


def test_edit_cujo_trecho_antigo_nao_existe_confere_so_o_texto_novo(maq):
    maq.arquivos["memory/a.md"] = "# A\n"
    ev = _evento("memory/a.md", tool="Edit", old_string="não está no arquivo", new_string=CORTADOS[5])
    assert maq.responder(ev) is not None


def test_escape_do_owner_desliga_so_esta_conferencia(maq):
    ev = _evento("memory/a.md", content=CORTADOS[0])
    assert maq.responder(ev, {"MSS_COMANDO_INTEIRO_OFF": "1"}) is None
    assert maq.responder(ev, {"MSS_REGRA_OFF": "1"}) is not None           # o escape da outra cerca não desliga esta


def test_sem_numero_de_conversa_nao_age(maq):
    assert maq.responder(_evento("memory/a.md", sessao=None, content=CORTADOS[0])) is None


def test_defeito_na_conferencia_nao_trava_a_gravacao(maq, ci, monkeypatch):
    def _quebra(*_a, **_k):
        raise RuntimeError("defeito")

    monkeypatch.setattr(ci, "trechos_cortados", _quebra)
    assert maq.responder(_evento("memory/a.md", content=CORTADOS[0])) is None


def test_regra_por_tipo_de_arquivo_e_comando_cortado_saem_numa_negacao_so(maq):
    maq.claude = "# Proj\n\n<!-- mss-spec:regras-do-kit -->\n"
    maq.regras = {"memoria.md": '---\npaths:\n  - "memory/**"\n---\n\nREGRA-DA-MEMORIA\n'}
    ev = _evento("memory/a.md", content=CORTADOS[0])
    motivo = _motivo(maq.responder(ev))
    assert "REGRA-DA-MEMORIA" in motivo and "UPDATE mensagens SET status" in motivo
    assert maq.responder(ev) is None


# --- o disco de verdade (o arquivo antes do Edit e o já avisado) --------------------------------------

def test_disco_le_o_arquivo_antes_do_edit_e_guarda_o_avisado(tmp_path, monkeypatch):
    raiz, temp = tmp_path / "proj", tmp_path / "temp"
    (raiz / "memory").mkdir(parents=True)
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    ci = _carregar("_comando_inteiro", MODULO)
    (raiz / "memory" / "a.md").write_text(_bloco("UPDATE mensagens SET status = 'enviada' WHERE id = 42;"),
                                          encoding="utf-8")
    ev = {"tool_name": "Edit", "session_id": "d1", "tool_input": {
        "file_path": str(raiz / "memory" / "a.md"), "old_string": "status = 'enviada' WHERE id = 42;",
        "new_string": "status = 'enviada', tentativas = 0 ..."}}
    assert "tentativas = 0 ..." in ci.conferir(ev, "memory/a.md", str(raiz), {}), "o arquivo do disco não foi lido"
    assert ci.conferir(ev, "memory/a.md", str(raiz), {}) is None, "o já avisado não foi gravado ou lido"


# --- a regra escrita na captura (comando-prosa: só a presença da frase) ------------------------------

def test_modo_capturar_manda_gravar_o_comando_inteiro():
    texto = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    capturar = texto.split("## Modo: capturar", 1)[1].split("## Modo: buscar", 1)[0]
    assert "comando ou SQL" in capturar and "inteiro" in capturar.lower()
    assert "reticências" in capturar and "*****" in capturar


def test_readme_dos_hooks_fala_da_conferencia():
    texto = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "_comando_inteiro.py" in texto and "MSS_COMANDO_INTEIRO_OFF" in texto


# --- anotações antigas: o verificar só conta (memoria_indice.py; uma pasta, montada uma vez) ----------

def test_verificar_lista_e_avisa_as_antigas_sem_alterar_nenhuma(tmp_path, capsys):
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
    indice = _carregar("memoria_indice", INDICE)

    assert indice.com_comando_cortado(mem) == ["project_reenvio.md", "sessions/2026-11-01-reenvio.md"]
    antes = {p: p.read_bytes() for p in mem.rglob("*.md")}
    assert indice.main(["verificar", "--proj", str(mem.parent)]) == 0      # aviso não vira problema
    saida = capsys.readouterr().out
    assert "2 anotação(ões) ou diário(s) com comando ou SQL com reticências" in saida
    assert "project_reenvio.md" in saida and "NÃO complete" in saida
    assert {p: p.read_bytes() for p in mem.rglob("*.md")} == antes

    (mem / "project_reenvio.md").write_text(
        (mem / "project_reenvio.md").read_text(encoding="utf-8").replace(" ...", " WHERE id = 42;"), encoding="utf-8")
    (mem / "sessions" / "2026-11-01-reenvio.md").unlink()
    assert indice.main(["verificar", "--proj", str(mem.parent)]) == 0
    assert "reticências" not in capsys.readouterr().out, "sem corte, o verificar ainda avisou"
