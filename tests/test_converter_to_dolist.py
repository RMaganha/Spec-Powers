"""Conversor do to-dolist e do fora de escopo pro desenho do kit (0.48.0) — chamado pelo /mss-spec:upgrade.

Spec: docs/specs/fora-de-escopo-no-to-dolist.md. Os exemplos imitam o formato real (lido, sem gravar) do Whats,
do Energy e do Transportes em 2026-10-28: recado numerado que continua na linha de baixo, título de seção com
data, item riscado/FEITA, data DD/MM/AAAA, fora de escopo com motivo de um parágrafo.
"""
import importlib.util
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "converter_to_dolist.py"
HOJE = "2026-11-05"


def _mod():
    spec = importlib.util.spec_from_file_location("converter_to_dolist", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TODO_WHATS = """# to-dolist — Projeto

> Caixa pessoal, **fora do git** (`.gitignore`). Recado para a próxima janela.

---

# 🔨 Depois do deploy de G1+G2+G3 (2026-09-15) — 3 recados

1. **Rodar a régua no dia seguinte ao deploy**: `tests/regua.py --dias 1` (comando na spec
   `docs/specs/regua.md`). Conferir: linha "atividade real" aparece.
2. **Olhar o id 63 do `agent_bot_log`** — o único erro real.

# ✅ ~~Postgres caindo~~ — CONCLUÍDO em 2026-07-30

- reiniciar o pool

## Revisar depois

- trocar o nome da fila em 23/10
- item sem data nenhuma

```
python -m pytest
```
"""

INDEX_ENERGY = """# Índice de tarefas

## Em andamento
- [login](../specs/login.md) — entrar — aberta

## Fora de escopo (decidido — não repropor)
- **Key Vault direto** — descartado em 2026-07-30: escolhemos variável de ambiente.
- Multi-nuvem
- ~~**Dashboard por região**~~ — **FEITA 2026-07-25** (feature #3).

## Backlog
- relatório mensal — aberta
"""

FORA_WHATS = """# Fora de escopo

<!-- Movido da partida pelo rodizio_partida.py (caso F-030 do kit): texto VERBATIM, lido sob demanda. Nada foi apagado — só saiu do que toda janela lê. -->

## 2026-10-27 — movido do INDEX.md

- **PySocks para o psycopg2** — descartado em 2026-08-03: o `psycopg2` usa a libpq, em C, que ignora proxy do Python.
- **Redis para o handoff** — decidido em 04/08/2026: a memória de sessão já resolve.
"""


def _git(proj, *args):
    subprocess.run(["git", *args], cwd=proj, check=True, capture_output=True)


def _projeto(tmp_path, todo=TODO_WHATS, index=INDEX_ENERGY, fora=FORA_WHATS, ignorado=True, commit=True):
    proj = tmp_path / "proj"
    sp = proj / "docs" / "superpowers"
    sp.mkdir(parents=True)
    if todo is not None:
        (proj / "to-dolist.md").write_text(todo, encoding="utf-8")
    if index is not None:
        (sp / "INDEX.md").write_text(index, encoding="utf-8")
    if fora is not None:
        (sp / "FORA-DE-ESCOPO.md").write_text(fora, encoding="utf-8")
    gi = "# Caixa de captura pessoal do /mss-spec:to-dolist — local, não versionada.\n/to-dolist.md\n\n.env\n"
    (proj / ".gitignore").write_text(gi if ignorado else ".env\n", encoding="utf-8")
    if commit:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "inicio")
    return proj


def _linhas_novas(res):
    """As linhas convertidas (antes da lista do fim)."""
    return [l for l in res.todo_novo.split(_mod().MARCA_LISTA)[0].splitlines() if l.startswith("- ")]


# ------------------------------------------------------------------ checar (o doctor usa)

def test_checar_aponta_tudo_que_esta_no_formato_antigo(tmp_path):
    achados = _mod().checar(_projeto(tmp_path))
    texto = " ".join(achados)
    assert "INDEX.md" in texto and "FORA-DE-ESCOPO.md" in texto and ".gitignore" in texto
    assert any("fora do formato" in a for a in achados)


def test_checar_projeto_no_desenho_do_kit_nao_aponta_nada(tmp_path):
    todo = "- algo (add: 2026-10-01)\n- outro #fora-de-escopo (decidido: 2026-10-02, motivo)\n"
    proj = _projeto(tmp_path, todo=todo, index="# Índice\n\n## Em andamento\n", fora=None, ignorado=False)
    assert _mod().checar(proj) == []


def test_o_kit_esta_no_proprio_desenho():
    assert _mod().checar(REPO) == []


# ------------------------------------------------------------------ tempo 1: liberar

def test_liberar_tira_o_to_dolist_do_gitignore_e_o_comentario_dele(tmp_path):
    proj = _projeto(tmp_path)
    m = _mod()
    previa = m.liberar(proj, aplicar=False)
    assert "/to-dolist.md" in previa and (proj / ".gitignore").read_text(encoding="utf-8").count("to-dolist") == 2
    m.liberar(proj, aplicar=True)
    gi = (proj / ".gitignore").read_text(encoding="utf-8")
    assert "to-dolist" not in gi and ".env" in gi


# ------------------------------------------------------------------ tempo 2: converter

def test_recado_numerado_vira_uma_linha_com_o_titulo_e_a_data_da_secao(tmp_path):
    res = _mod().converter(_projeto(tmp_path), hoje=HOJE)
    regua = [l for l in _linhas_novas(res) if "Rodar a régua" in l]
    assert regua == ['- Depois do deploy de G1+G2+G3 — 3 recados: **Rodar a régua no dia seguinte ao deploy**: '
                     '`tests/regua.py --dias 1` (comando na spec `docs/specs/regua.md`). Conferir: linha '
                     '"atividade real" aparece. (add: 2026-09-15)']


def test_fora_de_escopo_mantem_o_texto_inteiro(tmp_path):
    linhas = _linhas_novas(_mod().converter(_projeto(tmp_path), hoje=HOJE))
    assert ('- PySocks para o psycopg2 #fora-de-escopo (decidido: 2026-08-03, descartado em 2026-08-03: o '
            '`psycopg2` usa a libpq, em C, que ignora proxy do Python.)') in linhas
    assert ('- Key Vault direto #fora-de-escopo (decidido: 2026-07-30, descartado em 2026-07-30: escolhemos '
            'variável de ambiente.)') in linhas


def test_negrito_no_meio_da_frase_o_que_vai_ate_o_separador():
    m = _mod()
    assert m._o_que_e_motivo("**Ramificação condicional** entre perguntas (x) — fora de escopo: linear.") == \
        ("Ramificação condicional entre perguntas (x)", "fora de escopo: linear.")
    assert m._o_que_e_motivo("**Reprocessar as recusas** (`Sem Resultado`): **não fazer.** São 25 — mesma recusa") == \
        ("Reprocessar as recusas (`Sem Resultado`)", "**não fazer.** São 25 — mesma recusa")
    assert m._o_que_e_motivo("Multi-nuvem") == ("Multi-nuvem", "")


def test_data_dd_mm_aaaa_vira_aaaa_mm_dd(tmp_path):
    linhas = _linhas_novas(_mod().converter(_projeto(tmp_path), hoje=HOJE))
    assert any(l.startswith("- Redis para o handoff #fora-de-escopo (decidido: 2026-08-04, ") for l in linhas)


def test_sem_data_recebe_a_data_do_upgrade_e_sem_motivo_diz_isso(tmp_path):
    linhas = _linhas_novas(_mod().converter(_projeto(tmp_path), hoje=HOJE))
    assert "- Revisar depois: item sem data nenhuma (add: 2026-11-05)" in linhas
    assert "- Multi-nuvem #fora-de-escopo (decidido: 2026-11-05, motivo não registrado)" in linhas


def test_riscado_feito_e_data_incompleta_vao_pra_lista_sem_mudar(tmp_path):
    res = _mod().converter(_projeto(tmp_path), hoje=HOJE)
    lista = res.todo_novo.split(_mod().MARCA_LISTA, 1)[1]
    assert "- ~~**Dashboard por região**~~ — **FEITA 2026-07-25** (feature #3)." in lista
    assert "- reiniciar o pool" in lista, "item embaixo de título CONCLUÍDO não é decidido pela conversão"
    assert "- trocar o nome da fila em 23/10" in lista, "data sem ano: não adivinha"
    assert "python -m pytest" in lista and "> Caixa pessoal" in lista
    assert not any("Dashboard por região" in l for l in _linhas_novas(res))


def test_ordem_pela_data_mais_antiga_em_cima(tmp_path):
    datas = [re.search(r"\((?:add|decidido): (\d{4}-\d{2}-\d{2})", l).group(1)
             for l in _linhas_novas(_mod().converter(_projeto(tmp_path), hoje=HOJE))]
    assert datas == sorted(datas) and datas[0] == "2026-07-30"


def test_linha_ja_no_formato_fica_igual(tmp_path):
    todo = "- já certo (add: 2026-10-01)\n- velho #fora-de-escopo (decidido: 2026-01-02, motivo)\n- novo sem data\n"
    linhas = _linhas_novas(_mod().converter(_projeto(tmp_path, todo=todo, index=None, fora=None), hoje=HOJE))
    assert linhas == ["- velho #fora-de-escopo (decidido: 2026-01-02, motivo)", "- já certo (add: 2026-10-01)",
                      "- novo sem data (add: 2026-11-05)"]


def test_nenhuma_linha_some_a_soma_bate(tmp_path):
    res = _mod().converter(_projeto(tmp_path), hoje=HOJE)
    c = res.contagem
    assert c["total"] == c["convertidas"] + c["titulos"] + c["lista"] + c["marcacao"]
    assert not res.problemas


def test_index_perde_so_a_secao_e_o_arquivo_antigo_sai(tmp_path):
    res = _mod().converter(_projeto(tmp_path), hoje=HOJE)
    assert res.index_novo == ("# Índice de tarefas\n\n## Em andamento\n- [login](../specs/login.md) — entrar — "
                              "aberta\n\n## Backlog\n- relatório mensal — aberta\n")
    assert res.apagar_fora


def test_exemplos_mostram_tres_linhas_reais_antes_e_depois(tmp_path):
    res = _mod().converter(_projeto(tmp_path), hoje=HOJE)
    assert len(res.exemplos) == 3
    assert all(antes and depois.startswith("- ") for antes, depois in res.exemplos)


# ------------------------------------------------------------------ nunca perder nada

def test_aplicar_recusa_to_dolist_que_ainda_nao_esta_no_git(tmp_path):
    proj = _projeto(tmp_path)  # to-dolist ignorado: não entrou no commit
    antes = (proj / "to-dolist.md").read_text(encoding="utf-8")
    res = _mod().converter(proj, hoje=HOJE, aplicar=True)
    assert res.problemas and not res.gravou
    assert (proj / "to-dolist.md").read_text(encoding="utf-8") == antes


def test_aplicar_grava_depois_do_tempo_1(tmp_path):
    proj = _projeto(tmp_path)
    m = _mod()
    m.liberar(proj, aplicar=True)
    _git(proj, "add", ".gitignore", "to-dolist.md")
    _git(proj, "commit", "-q", "-m", "tempo 1")
    res = m.converter(proj, hoje=HOJE, aplicar=True)
    assert res.gravou and not res.problemas
    assert not (proj / "docs" / "superpowers" / "FORA-DE-ESCOPO.md").exists()
    assert "Fora de escopo" not in (proj / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    assert m.checar(proj) == [] or all("fora do formato" in a for a in m.checar(proj))
    # o antes ficou no git
    velho = subprocess.run(["git", "show", "HEAD:to-dolist.md"], cwd=proj, capture_output=True, text=True,
                           encoding="utf-8").stdout
    assert "Rodar a régua no dia seguinte" in velho and velho.startswith("# to-dolist")


def test_aplicar_recusa_arvore_suja(tmp_path):
    proj = _projeto(tmp_path, ignorado=False)
    (proj / "docs" / "superpowers" / "INDEX.md").write_text(INDEX_ENERGY + "\n- mexido\n", encoding="utf-8")
    res = _mod().converter(proj, hoje=HOJE, aplicar=True)
    assert res.problemas and not res.gravou


def test_crlf_do_to_dolist_e_preservado(tmp_path):
    proj = _projeto(tmp_path, ignorado=False)
    (proj / "to-dolist.md").write_bytes(TODO_WHATS.replace("\n", "\r\n").encode("utf-8"))
    _git(proj, "add", "to-dolist.md")
    _git(proj, "commit", "-q", "--allow-empty", "-m", "crlf")  # com core.autocrlf o git pode não ver mudança
    res = _mod().converter(proj, hoje=HOJE, aplicar=True)
    assert res.gravou, res.problemas
    b = (proj / "to-dolist.md").read_bytes()
    assert b.count(b"\r\n") == b.count(b"\n")


def test_cli_previa_nao_grava(tmp_path):
    proj = _projeto(tmp_path)
    antes = (proj / "to-dolist.md").read_text(encoding="utf-8")
    out = subprocess.run(["python", str(SCRIPT), "converter", "--proj", str(proj), "--hoje", HOJE],
                         capture_output=True, text=True, encoding="utf-8")
    assert "Prévia" in out.stdout and "antes:" in out.stdout and "depois:" in out.stdout
    assert (proj / "to-dolist.md").read_text(encoding="utf-8") == antes


def test_upgrade_e_doctor_chamam_o_conversor():
    up = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    assert "converter_to_dolist.py" in up and "liberar" in up and "converter" in up
    assert "3 linhas" in up, "o owner vê 3 linhas reais antes de gravar"
    doc = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    assert "converter_to_dolist.py\" checar" in doc
