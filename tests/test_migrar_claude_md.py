"""migrar_claude_md.py — monta e confere (dry-run) a migração do CLAUDE.md pro formato com as regras do kit no plugin.

Por que: o CLAUDE.md do Whats (10.096 B) trazia uma cópia velha das regras do kit e os FATOS de infra atrás de
gatilho de arquivo em `.claude/rules/` (F-040). A migração tira o que é do kit, traz os fatos de volta por extenso
pro `## Contexto` e só segue se nenhuma linha sumir sem destino conferido. Fala do owner: "o projeto não pode se
perder e eu ter que passar tudo de novo".

Fixture: cópia LIDA do Whats em 2026-10-23 (`tests/fixtures/whats-2026-10-23/`), byte a byte. Cada teste copia a
fixture pra `tmp_path`, faz `git init` + commit ali (é o ponto de volta que o `conferir` exige) e só então monta.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "migrar_claude_md.py"
LINHAS_KIT = REPO / "templates" / "regras-do-kit" / "linhas-do-kit.txt"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "whats-2026-10-23"
REGRAS_WHATS = ("banco.md", "deploy-e-ambiente.md", "estrutura-em-camadas.md", "logging.md", "seguranca.md",
                "testes.md", "ui-propria.md")
MARCA = "<!-- mss-spec:regras-do-kit -->"


def _mod():
    spec = importlib.util.spec_from_file_location("migrar_claude_md", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- helpers ---------------------------------------------------------------------------------------

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _commitar(proj: Path) -> None:
    """Repo git LOCAL do teste (nunca o do owner): init + identidade local + commit de tudo."""
    _git(proj, "init", "-q")
    _git(proj, "config", "user.name", "Teste mss-spec")
    _git(proj, "config", "user.email", "teste@exemplo.invalid")
    _git(proj, "config", "commit.gpgsign", "false")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "fixture")


def _projeto_whats(tmp_path, claude_md=None, git=True) -> Path:
    """Cópia da fixture do Whats em tmp_path (CLAUDE.md + 7 regras), commitada num repo git próprio."""
    proj = tmp_path / "whats"
    (proj / ".claude" / "rules").mkdir(parents=True)
    if claude_md is None:
        shutil.copyfile(FIXTURE / "CLAUDE.md", proj / "CLAUDE.md")
    else:
        (proj / "CLAUDE.md").write_bytes(claude_md.encode("utf-8"))
    for nome in REGRAS_WHATS:
        shutil.copyfile(FIXTURE / ".claude" / "rules" / nome, proj / ".claude" / "rules" / nome)
    if git:
        _commitar(proj)
    return proj


def _projeto(tmp_path, claude_md: str, regras: dict, git=True) -> Path:
    proj = tmp_path / "proj"
    (proj / ".claude" / "rules").mkdir(parents=True)
    (proj / "CLAUDE.md").write_bytes(claude_md.encode("utf-8"))
    for nome, texto in regras.items():
        (proj / ".claude" / "rules" / nome).write_bytes(texto.encode("utf-8"))
    if git:
        _commitar(proj)
    return proj


def _linhas_kit(m):
    return m.carregar_linhas_do_kit()


def _montar_whats(tmp_path, **kw):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    return m, proj, m.montar(proj, _linhas_kit(m), **kw)


def _secao(texto: str, titulo: str) -> list:
    """Linhas do corpo da seção `## <titulo…>` (sem o cabeçalho), até a próxima `## `."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    ini = next(i for i, l in enumerate(linhas) if l.startswith("## " + titulo))
    fim = next((j for j in range(ini + 1, len(linhas)) if linhas[j].startswith("## ")), len(linhas))
    return linhas[ini + 1:fim]


def _ler(p: Path) -> str:
    return p.read_bytes().decode("utf-8").replace("\r\n", "\n")


# --- normalizar / linhas do kit ----------------------------------------------------------------------

def test_normalizar_ignora_bom_cr_marcador_numeracao_e_espacos():
    m = _mod()
    assert m.normalizar("﻿-   **Idioma**:  responda   em pt-BR\r") == "**Idioma**: responda em pt-BR"
    assert m.normalizar("12. **Regra**  x") == "**Regra** x"
    assert m.normalizar("  * item") == "item"
    assert m.normalizar("   ") == ""


def test_linhas_do_kit_em_dia():
    if not (REPO / ".git").exists():
        pytest.skip("sem .git no kit: o histórico do molde não está disponível")
    raso = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO, capture_output=True, text=True)
    if raso.stdout.strip() == "true":
        pytest.skip("clone raso: o histórico do molde está incompleto")
    m = _mod()
    gravado = [l for l in LINHAS_KIT.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n") if l]
    assert m.gerar_linhas_do_kit(REPO) == gravado, \
        "linhas-do-kit.txt desatualizado: rode `python templates/migrar_claude_md.py historico`"


# --- Whats -------------------------------------------------------------------------------------------

def test_whats_contexto_sem_ponteiro_para_rules(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    contexto = _secao(mig.claude_novo, "Contexto")
    assert not [l for l in contexto if ".claude/rules/" in l]
    corpo = "\n".join(contexto)
    for rotulo in ("**Como roda:**", "**Homologação (Azure):**", "**Versionamento:**", "**Banco:**",
                   "**Testes:**", "**UI:**", "**Infra:**"):
        assert rotulo in corpo, rotulo
    assert "gunicorn na porta 8000" in corpo
    assert "mss-miti-ai-agent-bot-webwhats-dev-br" in corpo


def test_whats_fatos_saem_do_arquivo_de_regra(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    assert "**Como roda:**" not in mig.regras_novas["deploy-e-ambiente.md"]
    assert "**Homologação (Azure):**" not in mig.regras_novas["deploy-e-ambiente.md"]
    assert "**Versionamento:**" not in mig.regras_novas["deploy-e-ambiente.md"]
    assert "**Pré-vôo de ambiente (doctor)**" in mig.regras_novas["deploy-e-ambiente.md"]
    assert "**Banco:**" not in mig.regras_novas["banco.md"]
    assert "psycopg2.connect" not in mig.regras_novas["banco.md"]       # o item inteiro foi
    assert "Nunca tocar o que é do RAG em produção" in mig.regras_novas["banco.md"]
    assert "paths:" in mig.regras_novas["banco.md"]                     # frontmatter intacto
    assert set(mig.regras_novas) == {"deploy-e-ambiente.md", "banco.md", "testes.md", "ui-propria.md"}
    assert any(de == ".claude/rules/deploy-e-ambiente.md" and "**Como roda:**" in linha
               for linha, de, _ in mig.moveu)


def test_whats_regras_novas_mantem_crlf(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    assert "\r\n" in mig.regras_novas["banco.md"]
    assert "\n" not in mig.regras_novas["banco.md"].replace("\r\n", "")
    assert "\n" not in mig.claude_novo.replace("\r\n", "")


def test_whats_linhas_do_kit_saem(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    assert "Não codar antes do meu OK explícito" not in mig.claude_novo
    assert any("Não codar antes do meu OK explícito" in l for l in mig.saiu_do_kit)
    assert "## Modo de trabalho" not in mig.claude_novo
    assert "## Regras críticas" not in mig.claude_novo


def test_whats_ponteiro_para_doc_do_projeto_fica(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    regras = _secao(mig.claude_novo, "Regras obrigatórias do projeto")
    com_doc = [l for l in regras if "docs/MODO-DE-TRABALHO.md" in l]
    assert len(com_doc) == 4
    corpo = "\n".join(regras)
    for titulo in ("**Comando `/mss-spec:<x>` referenciado NÃO é inexistente", "**Nível de cerimônia**",
                   "**Git — branch da principal + local-only**", "**Plano de teste base (anti-regressão)**"):
        assert titulo in corpo, titulo


def test_whats_seta_no_meio_da_frase_nao_e_ponteiro(tmp_path):
    """`família bateu → abra memory/indice/<f>.md` não é linha-ponteiro (a seta não vem logo depois do título):
    é regra do kit com redação do projeto — fica, mas entra na dúvida pro owner conferir."""
    _, _, mig = _montar_whats(tmp_path)
    indices = next(l for l in _secao(mig.claude_novo, "Regras obrigatórias do projeto")
                   if "**Índices do projeto**" in l)
    assert indices in mig.ficou_por_duvida
    assert not [l for l in mig.ficou_por_duvida if "docs/MODO-DE-TRABALHO.md" in l]


def test_whats_regras_do_projeto_ficam(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    corpo = "\n".join(_secao(mig.claude_novo, "Regras obrigatórias do projeto"))
    assert "`.env` desta pasta **nunca**" in corpo
    assert "Nunca tocar o que é do RAG" in corpo
    assert "**A UI deste projeto é PRÓPRIA e INTOCÁVEL**" in corpo


def test_whats_indice_cada_regra_uma_vez(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    indice = _secao(mig.claude_novo, "Índice de regras por tipo de arquivo")
    corpo = "\n".join(indice)
    for nome in REGRAS_WHATS:
        assert corpo.count(f"`.claude/rules/{nome}`") == 1, nome
    linha_banco = next(l for l in indice if "banco.md" in l)
    assert linha_banco == ("- `.claude/rules/banco.md` — Banco e RAG de produção — carrega ao tocar "
                           "`**/*.sql`, `sql/**`, `persistencia/**`")


def test_whats_marca_e_titulo(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    linhas = mig.claude_novo.replace("\r\n", "\n").split("\n")
    assert MARCA in linhas
    assert linhas.index(MARCA) < next(i for i, l in enumerate(linhas) if l.startswith("# IA Bot Agent - Whats"))
    ordem = [l for l in linhas if l.startswith("## ")]
    assert ordem == ["## Regras obrigatórias do projeto", "## Contexto", "## Mapa de arquivos",
                     "## Índice de regras por tipo de arquivo"]
    assert mig.ja_migrado is False


def test_whats_conservacao(tmp_path):
    m, proj, mig = _montar_whats(tmp_path)
    assert m.conferir(proj, mig) == []
    kit = set(_linhas_kit(m))
    assert set(mig.saiu_do_kit) <= kit
    indice = "\n".join(_secao(mig.claude_novo, "Índice de regras por tipo de arquivo"))
    depois_textos = [mig.claude_novo] + [mig.regras_novas.get(n, _ler(proj / ".claude" / "rules" / n))
                                         for n in REGRAS_WHATS]
    depois = {m.normalizar(l) for t in depois_textos for l in t.replace("\r\n", "\n").split("\n")}
    contexto_antes = _secao(_ler(proj / "CLAUDE.md"), "Contexto")
    antes = [l for t in [_ler(proj / "CLAUDE.md")] + [_ler(proj / ".claude" / "rules" / n) for n in REGRAS_WHATS]
             for l in t.split("\n") if l.strip()]
    sem_destino = []
    for l in antes:
        n = m.normalizar(l)
        if n in depois or n in mig.saiu_do_kit:
            continue
        alvo = re.search(r"`(\.claude/rules/[^`]+)`", l)
        if l in contexto_antes and "→" in l and alvo and f"`{alvo.group(1)}`" in indice:
            continue
        sem_destino.append(l)
    assert sem_destino == []


def test_conferir_pega_linha_que_sumiria(tmp_path):
    """A conservação é do `conferir`, independente do `montar`: tirar uma linha do resultado reprova."""
    m, proj, mig = _montar_whats(tmp_path)
    estado = next(l for l in mig.claude_novo.split("\r\n") if l.startswith("- **Estado:**"))
    mig.claude_novo = mig.claude_novo.replace(estado + "\r\n", "")
    falhas = m.conferir(proj, mig)
    assert any("conservação" in f and "**Estado:**" in f for f in falhas), falhas


def test_conferir_pega_linha_do_projeto_disfarcada_de_kit(tmp_path):
    m, proj, mig = _montar_whats(tmp_path)
    linha = next(l for l in mig.claude_novo.split("\r\n") if "Segredo e ambiente" in l)
    mig.claude_novo = mig.claude_novo.replace(linha + "\r\n", "")
    mig.saiu_do_kit.append(m.normalizar(linha))
    falhas = m.conferir(proj, mig)
    assert any("linhas-do-kit.txt" in f for f in falhas), falhas
    assert any("conservação" in f and "Segredo e ambiente" in f for f in falhas), falhas


def test_conferir_pega_item_tirado_da_regra_sem_voltar(tmp_path):
    m, proj, mig = _montar_whats(tmp_path)
    linhas = mig.claude_novo.split("\r\n")
    mig.claude_novo = "\r\n".join(l for l in linhas if not l.startswith("- **Banco:**"))
    falhas = m.conferir(proj, mig)
    assert any("**Banco:**" in f for f in falhas), falhas


def test_whats_tamanho_vira_aviso_nao_falha(tmp_path):
    m, proj, mig = _montar_whats(tmp_path, teto=5000)
    assert any("5000" in a or "5.000" in a for a in mig.avisos), mig.avisos
    tamanho = len(mig.claude_novo.encode("utf-8"))
    assert any(str(tamanho) in a or f"{tamanho:,}".replace(",", ".") in a for a in mig.avisos), mig.avisos
    assert m.conferir(proj, mig) == []


def test_whats_dentro_do_teto_padrao_sem_aviso_de_tamanho(tmp_path):
    _, _, mig = _montar_whats(tmp_path)
    assert len(mig.claude_novo.encode("utf-8")) <= 10000
    assert not [a for a in mig.avisos if "teto" in a]


# --- casos de falha e de dúvida ----------------------------------------------------------------------

PONTEIRO_COMO_RODA = ("- **Como roda:** → texto inteiro em `.claude/rules/deploy-e-ambiente.md` "
                      "(carrega sozinho ao tocar `Dockerfile`).")


def test_rotulo_inexistente_reprova(tmp_path):
    m = _mod()
    claude = f"# Proj — teste\n\n## Contexto\n- **Infra:** própria.\n{PONTEIRO_COMO_RODA}\n"
    regra = "---\npaths:\n  - \"Dockerfile\"\n---\n\n# Deploy\n\n- **Pré-vôo:** rode o doctor.\n"
    proj = _projeto(tmp_path, claude, {"deploy-e-ambiente.md": regra})
    mig = m.montar(proj, _linhas_kit(m))
    falhas = m.conferir(proj, mig)
    assert falhas
    assert any(PONTEIRO_COMO_RODA in f for f in falhas), falhas


def test_regra_com_acento_no_nome_e_reconhecida_pelo_git(tmp_path):
    m = _mod()
    claude = ("# Proj — x\n\n## Contexto\n- **Segurança:** → texto inteiro em `.claude/rules/segurança.md` "
              "(carrega sozinho ao tocar `apis/**`).\n")
    regra = "---\npaths:\n  - \"apis/**\"\n---\n\n# Segurança\n\n- **Segurança:** token Bearer.\n\n- Nunca logar PII.\n"
    proj = _projeto(tmp_path, claude, {"segurança.md": regra})
    mig = m.montar(proj, _linhas_kit(m))
    assert "- **Segurança:** token Bearer." in mig.claude_novo
    assert mig.regras_novas["segurança.md"].endswith("# Segurança\n\n- Nunca logar PII.\n")
    assert m.conferir(proj, mig) == []


# --- projeto nascido do último molde antes da marca (7b0809b) -----------------------------------------

MOLDE_PRE_MARCA = Path(__file__).resolve().parent / "fixtures" / "molde-7b0809b" / "CLAUDE.md"
PREENCHER = [
    ("# <Projeto> — <objetivo em 1 frase>", "# Cotador — calcula prêmio de seguro auto pra corretor"),
    ("- **Infra:** <**MSIG** | **própria**> —", "- **Infra:** **MSIG** —"),
    ("- **Stack/runtime:** <ex.: Python 3.x / Node> · **Como roda:** <CLI | serviço/porta | container | cron>",
     "- **Stack/runtime:** Python 3.12 · **Como roda:** container, gunicorn na porta 8000"),
    ("- **UI:** <não | web — ex.: FastAPI + Jinja; ver `.claude/rules/frontend.md`>",
     "- **UI:** web — FastAPI + Jinja; ver `.claude/rules/frontend.md`"),
    ("- **Integrações externas:** <sites / APIs / filas, ou \"nenhuma\">",
     "- **Integrações externas:** API de tarifas da MSIG"),
    ("- **Banco:** <não | qual> — ver `.claude/rules/banco-e-segredo.md`",
     "- **Banco:** PostgreSQL 16 — ver `.claude/rules/banco-e-segredo.md`"),
    ("- `<arquivo>` — <responsabilidade>", "- `tarifas/calculo.py` — regra de cálculo do prêmio"),
    ("12. <regra específica do seu projeto…>", "12. **Nunca alterar a tabela `tarifa_base`** — é da atuária."),
]
SECOES_DO_KIT_PRE_MARCA = ("## Modo de trabalho", "## Contexto de janela", "## Regras críticas")


def _molde_pre_marca_preenchido() -> str:
    texto = MOLDE_PRE_MARCA.read_bytes().decode("utf-8").replace("\r\n", "\n")
    for de, para in PREENCHER:
        assert de in texto, de
        texto = texto.replace(de, para)
    return texto


def _projeto_molde_pre_marca(tmp_path, texto=None) -> Path:
    regras = {p.name: p.read_bytes().decode("utf-8") for p in (REPO / "templates" / "rules").glob("*.md")}
    return _projeto(tmp_path, texto or _molde_pre_marca_preenchido(), regras)


def test_molde_pre_marca_preenchido_migra(tmp_path):
    m = _mod()
    texto = _molde_pre_marca_preenchido()
    proj = _projeto_molde_pre_marca(tmp_path, texto)
    mig = m.montar(proj, _linhas_kit(m))
    assert m.conferir(proj, mig) == []
    contexto = _secao(mig.claude_novo, "Contexto")
    assert not [l for l in contexto if ".claude/rules/" in l]
    assert "- **UI:** web — FastAPI + Jinja" in contexto
    assert "- **Banco:** PostgreSQL 16" in contexto
    assert any(de == "CLAUDE.md › ## Contexto" and "banco-e-segredo.md" in linha and "ponteiro" in para
               for linha, de, para in mig.moveu)
    # toda linha das seções do kit e dos comentários do molde saiu como do kit
    secao = None
    do_kit = []
    for l in texto.split("\n"):
        if l.startswith("## "):
            secao = l
        dentro = secao is None or secao.startswith(SECOES_DO_KIT_PRE_MARCA)
        if l.strip() and dentro and not l.startswith("# ") and not l.startswith("12. "):
            do_kit.append(l)
    assert do_kit
    for l in do_kit:
        assert m.normalizar(l) in mig.saiu_do_kit, l
        assert l not in mig.claude_novo.split("\n"), l
    # as linhas do projeto ficam
    for _, para in PREENCHER:
        if ".claude/rules/" not in para:
            assert para in mig.claude_novo, para
    assert "12. **Nunca alterar a tabela `tarifa_base`**" in "\n".join(
        _secao(mig.claude_novo, "Regras obrigatórias do projeto"))
    indice = "\n".join(_secao(mig.claude_novo, "Índice de regras por tipo de arquivo"))
    for nome in ("banco-e-segredo.md", "frontend.md", "rota-e-endpoint.md"):
        assert indice.count(f"`.claude/rules/{nome}`") == 1


def test_fragmento_ver_rules_sem_arquivo_reprova(tmp_path):
    m = _mod()
    linha = "- **Banco:** PostgreSQL 16 — ver `.claude/rules/banco-e-segredo.md`"
    proj = _projeto(tmp_path, f"# Proj — x\n\n## Contexto\n{linha}\n", {})
    mig = m.montar(proj, _linhas_kit(m))
    falhas = m.conferir(proj, mig)
    assert any(linha in f for f in falhas), falhas


def test_conferir_so_aceita_o_fragmento_registrado(tmp_path):
    """Tirar o fragmento sem registrar em `moveu` (ou tirar mais que o fragmento) reprova."""
    m = _mod()
    proj = _projeto_molde_pre_marca(tmp_path)
    mig = m.montar(proj, _linhas_kit(m))
    mig.moveu = [x for x in mig.moveu if "ponteiro" not in x[2]]
    falhas = m.conferir(proj, mig)
    assert any("conservação" in f and "banco-e-segredo.md" in f for f in falhas), falhas


# --- seções de título parecido; linhas repetidas ------------------------------------------------------

def test_secoes_de_titulo_parecido_nao_se_perdem(tmp_path):
    m = _mod()
    claude = ("# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n\n## Contexto do negocio\n- X\n\n"
              "## Mapa de arquivos\n- `a.py` — faz A\n\n## Mapa de arquivos extra\n- `b.py`\n")
    proj = _projeto(tmp_path, claude, {})
    mig = m.montar(proj, _linhas_kit(m))
    novo = mig.claude_novo.split("\n")
    for l in ("## Contexto", "- **Infra:** MSIG", "## Contexto do negocio", "- X", "## Mapa de arquivos",
              "- `a.py` — faz A", "## Mapa de arquivos extra", "- `b.py`"):
        assert l in novo, l
    assert novo.index("## Contexto do negocio") < novo.index("## Mapa de arquivos extra")
    assert m.conferir(proj, mig) == []


def test_mesmo_titulo_duas_vezes_e_concatenado(tmp_path):
    m = _mod()
    claude = "# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n\n## Mapa de arquivos\n- `a.py`\n\n## Contexto\n- **Banco:** PG\n"
    proj = _projeto(tmp_path, claude, {})
    mig = m.montar(proj, _linhas_kit(m))
    contexto = _secao(mig.claude_novo, "Contexto")
    assert "- **Infra:** MSIG" in contexto and "- **Banco:** PG" in contexto
    assert mig.claude_novo.count("## Contexto\n") == 1
    assert m.conferir(proj, mig) == []


DUPLICADA = "- Toda alteração de tarifa passa pela atuária antes do deploy."


def test_linha_repetida_em_duas_secoes_sobrevive(tmp_path):
    m = _mod()
    claude = (f"# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n{DUPLICADA}\n\n"
              f"## Notas da equipe\n{DUPLICADA}\n")
    proj = _projeto(tmp_path, claude, {})
    mig = m.montar(proj, _linhas_kit(m))
    assert mig.claude_novo.split("\n").count(DUPLICADA) == 2
    assert m.conferir(proj, mig) == []
    # mutante: some uma das duas → a conservação por contagem pega
    linhas = mig.claude_novo.split("\n")
    linhas.remove(DUPLICADA)
    mig.claude_novo = "\n".join(linhas)
    falhas = m.conferir(proj, mig)
    assert any("conservação" in f and "atuária" in f for f in falhas), falhas


def test_linha_desconhecida_fica_por_duvida(tmp_path):
    m = _mod()
    original = (FIXTURE / "CLAUDE.md").read_bytes().decode("utf-8")
    inventada = "- **Idioma**: responda em latim nas sextas-feiras, inclusive nos commits."
    sem_titulo = "- Toda sexta, rode o backup do Chatwoot antes de abrir branch."
    alterado = original.replace("## Modo de trabalho (nunca violar)\r\n",
                                f"## Modo de trabalho (nunca violar)\r\n{inventada}\r\n{sem_titulo}\r\n", 1)
    assert alterado != original
    proj = _projeto_whats(tmp_path, claude_md=alterado)
    mig = m.montar(proj, _linhas_kit(m))
    regras = _secao(mig.claude_novo, "Regras obrigatórias do projeto")
    assert inventada in regras and sem_titulo in regras
    assert inventada in mig.ficou_por_duvida
    assert sem_titulo not in mig.ficou_por_duvida
    assert m.conferir(proj, mig) == []


def test_sem_git_reprova(tmp_path, monkeypatch):
    m = _mod()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    proj = _projeto_whats(tmp_path, git=False)
    mig = m.montar(proj, _linhas_kit(m))
    falhas = m.conferir(proj, mig)
    assert any("sem git não há ponto de volta" in f for f in falhas), falhas


def test_working_tree_sujo_reprova(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    alvo = proj / ".claude" / "rules" / "banco.md"
    alvo.write_bytes(alvo.read_bytes() + b"\r\n- linha nova sem commit\r\n")
    mig = m.montar(proj, _linhas_kit(m))
    falhas = m.conferir(proj, mig)
    assert any("banco.md" in f for f in falhas), falhas


def test_arquivo_nao_tocado_sujo_nao_reprova(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    (proj / "outro.txt").write_text("sujo", encoding="utf-8")
    alvo = proj / ".claude" / "rules" / "logging.md"                   # a migração não toca logging.md
    alvo.write_bytes(alvo.read_bytes() + b"\r\n")
    mig = m.montar(proj, _linhas_kit(m))
    assert "logging.md" not in mig.regras_novas
    assert m.conferir(proj, mig) == []


def test_conferir_nao_escreve_nada(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    antes = {p: p.read_bytes() for p in proj.rglob("*") if p.is_file() and ".git" not in p.parts}
    mig = m.montar(proj, _linhas_kit(m))
    m.conferir(proj, mig)
    depois = {p: p.read_bytes() for p in proj.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert antes == depois


def test_ja_migrado_nada_muda(tmp_path):
    m = _mod()
    claude = f"<!-- topo -->\n{MARCA}\n\n# Proj — x\n\n## Contexto\n{PONTEIRO_COMO_RODA}\n"
    proj = _projeto(tmp_path, claude, {"deploy-e-ambiente.md": "# Deploy\n\n- **Como roda:** porta 8000.\n"})
    mig = m.montar(proj, _linhas_kit(m))
    assert mig.ja_migrado is True
    assert mig.claude_novo == claude
    assert mig.regras_novas == {} and mig.saiu_do_kit == [] and mig.moveu == []
    assert m.conferir(proj, mig) == []


def test_comentario_html_so_sai_inteiro_quando_e_do_kit(tmp_path):
    m = _mod()
    claude = ("<!-- comentário do projeto, linha 1\n     linha 2 do projeto -->\n\n# Proj — x\n\n"
              "## Contexto\n- **Infra:** própria.\n")
    proj = _projeto(tmp_path, claude, {})
    mig = m.montar(proj, _linhas_kit(m))
    assert "<!-- comentário do projeto, linha 1" in mig.claude_novo
    assert "linha 2 do projeto -->" in mig.claude_novo
    assert m.conferir(proj, mig) == []


def test_linha_de_molde_no_contexto_fica(tmp_path):
    """Linha do molde no `## Contexto`/`## Mapa de arquivos` é do projeto (o molde novo também as tem): fica."""
    m = _mod()
    molde = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").split("\n")
    stack = next(l for l in molde if l.startswith("- **Stack/runtime:**"))
    mapa = next(l for l in molde if l.startswith("- `docs/decisoes.md`"))
    claude = f"# Proj — x\n\n## Contexto\n{stack}\n\n## Mapa de arquivos\n{mapa}\n"
    proj = _projeto(tmp_path, claude, {})
    mig = m.montar(proj, _linhas_kit(m))
    assert stack in mig.claude_novo and mapa in mig.claude_novo
    assert m.conferir(proj, mig) == []


# --- gravar, CLI e relatório (Task 6) -----------------------------------------------------------------

def _cli(proj: Path, *args):
    """Roda o script de verdade, como o `/mss-spec:upgrade` roda. Saída decodificada como UTF-8."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--proj", str(proj), *args], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")


def _arquivos(proj: Path) -> dict:
    return {p.relative_to(proj).as_posix(): p.read_bytes()
            for p in sorted(proj.rglob("*")) if p.is_file() and ".git" not in p.parts}


def _n_commits(proj: Path) -> int:
    return int(_git(proj, "rev-list", "--count", "HEAD").stdout.strip())


def _porcelain(proj: Path) -> set:
    saida = _git(proj, "status", "--porcelain").stdout
    return {l[3:] for l in saida.split("\n") if l.strip()}


def test_dry_run_nao_grava(tmp_path):
    proj = _projeto_whats(tmp_path)
    antes = _arquivos(proj)
    codigo, saida, _ = _cli(proj)
    assert codigo == 0, saida
    assert saida.startswith("Prévia"), saida[:80]
    assert _arquivos(proj) == antes
    assert _git(proj, "status", "--porcelain").stdout == ""


def test_aplicar_grava_e_nao_toca_no_git(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    commits = _n_commits(proj)
    esperado = {"CLAUDE.md"} | {f".claude/rules/{n}" for n in m.montar(proj, _linhas_kit(m)).regras_novas}
    codigo, saida, _ = _cli(proj, "--aplicar")
    assert codigo == 0, saida
    assert MARCA in _ler(proj / "CLAUDE.md")
    assert _n_commits(proj) == commits
    assert _porcelain(proj) == esperado
    assert _git(proj, "branch", "--show-current").stdout.strip() in ("master", "main")


def test_aplicar_com_falha_nao_grava_nada(tmp_path):
    claude = f"# Proj — teste\n\n## Contexto\n- **Infra:** própria.\n{PONTEIRO_COMO_RODA}\n"
    regra = "---\npaths:\n  - \"Dockerfile\"\n---\n\n# Deploy\n\n- **Pré-vôo:** rode o doctor.\n"
    proj = _projeto(tmp_path, claude, {"deploy-e-ambiente.md": regra})
    antes = _arquivos(proj)
    codigo, saida, _ = _cli(proj, "--aplicar")
    assert codigo == 1, saida
    assert PONTEIRO_COMO_RODA in saida
    assert "Nada foi gravado" in saida
    assert _arquivos(proj) == antes


def test_working_tree_sujo_reprova_na_cli(tmp_path):
    proj = _projeto_whats(tmp_path)
    (proj / "CLAUDE.md").write_bytes((proj / "CLAUDE.md").read_bytes() + b"\r\n- linha nova sem commit\r\n")
    antes = _arquivos(proj)
    codigo, saida, _ = _cli(proj, "--aplicar")
    assert codigo == 1, saida
    assert "working tree" in saida and "git restore" in saida
    assert _arquivos(proj) == antes


def test_crlf_preservado_no_whats(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    tocados = ["CLAUDE.md"] + [f".claude/rules/{n}" for n in m.montar(proj, _linhas_kit(m)).regras_novas]
    assert _cli(proj, "--aplicar")[0] == 0
    assert len(tocados) > 1
    for rel in tocados:
        bruto = (proj / rel).read_bytes()
        assert b"\r\n" in bruto, rel
        assert b"\n" not in bruto.replace(b"\r\n", b""), f"{rel}: sobrou \n sozinho"
    assert m.montar(proj, _linhas_kit(m)).ja_migrado is True


def test_bom_e_crlf_preservados(tmp_path):
    m = _mod()
    claude = ("﻿# Proj — x\r\n\r\n## Contexto\r\n- **Infra:** própria.\r\n- **Banco:** PostgreSQL.\r\n"
              "\r\n## Mapa de arquivos\r\n- `app.py` — entrada\r\n")
    proj = _projeto(tmp_path, claude, {})
    assert _cli(proj, "--aplicar")[0] == 0
    bruto = (proj / "CLAUDE.md").read_bytes()
    assert bruto.startswith("﻿".encode("utf-8")), bruto[:20]
    assert bruto.count("﻿".encode("utf-8")) == 1
    assert b"\n" not in bruto.replace(b"\r\n", b"")
    assert m.montar(proj, _linhas_kit(m)).ja_migrado is True


def test_projeto_sem_rules_so_ganha_marca_e_secoes(tmp_path):
    m = _mod()
    original = ("# Proj — calcula prêmio\n\n## Contexto\n- **Infra:** própria.\n- **Banco:** PostgreSQL 16.\n\n"
                "## Regras obrigatórias do projeto\n1. **Nunca alterar a tabela `tarifa_base`** — é da atuária.\n\n"
                "## Observações\n- A planilha de tarifas chega toda segunda.\n")
    proj = _projeto(tmp_path, original, {})
    codigo, saida, _ = _cli(proj, "--aplicar")
    assert codigo == 0, saida
    novo = _ler(proj / "CLAUDE.md")
    assert MARCA in novo
    depois = {m.normalizar(l) for l in novo.split("\n")}
    for l in original.split("\n"):
        if l.strip():
            assert m.normalizar(l) in depois, l
    assert "Índice de regras" not in novo
    assert list((proj / ".claude" / "rules").iterdir()) == []


def test_segunda_rodada_ja_migrado(tmp_path):
    proj = _projeto_whats(tmp_path)
    assert _cli(proj, "--aplicar")[0] == 0
    depois_da_1a = _arquivos(proj)
    codigo, saida, _ = _cli(proj, "--aplicar")
    assert codigo == 0, saida
    assert "já migrado" in saida
    assert _arquivos(proj) == depois_da_1a


def test_aplicar_recusa_montagem_com_falha(tmp_path):
    m = _mod()
    claude = f"# Proj — teste\n\n## Contexto\n- **Infra:** própria.\n{PONTEIRO_COMO_RODA}\n"
    regra = "---\npaths:\n  - \"Dockerfile\"\n---\n\n# Deploy\n\n- **Pré-vôo:** rode o doctor.\n"
    proj = _projeto(tmp_path, claude, {"deploy-e-ambiente.md": regra})
    antes = _arquivos(proj)
    mig = m.montar(proj, _linhas_kit(m))
    with pytest.raises(RuntimeError):
        m.aplicar(proj, mig)
    assert _arquivos(proj) == antes


def test_aplicar_nao_grava_se_o_projeto_mudou_depois_da_montagem(tmp_path):
    m = _mod()
    proj = _projeto_whats(tmp_path)
    mig = m.montar(proj, _linhas_kit(m))
    (proj / "CLAUDE.md").write_bytes((proj / "CLAUDE.md").read_bytes() + b"\r\n- mexi agora\r\n")
    antes = _arquivos(proj)
    with pytest.raises(RuntimeError):
        m.aplicar(proj, mig)
    assert _arquivos(proj) == antes


def test_relatorio_curto(tmp_path):
    m = _mod()
    original = (FIXTURE / "CLAUDE.md").read_bytes().decode("utf-8")
    inventada = "- **Idioma**: responda em latim nas sextas-feiras, inclusive nos commits."
    alterado = original.replace("## Modo de trabalho (nunca violar)\r\n",
                                f"## Modo de trabalho (nunca violar)\r\n{inventada}\r\n", 1)
    proj = _projeto_whats(tmp_path, claude_md=alterado)
    mig = m.montar(proj, _linhas_kit(m), teto=100)
    assert mig.saiu_do_kit and mig.moveu and mig.ficou_por_duvida and mig.avisos
    texto = m.relatorio(mig, [])
    assert f"Saíram como do kit (o plugin já entrega): {len(mig.saiu_do_kit)}" in texto
    assert f"Mudaram de lugar: {len(mig.moveu)}" in texto
    assert texto.split("Ficaram por dúvida")[1].split("\n")[0].endswith(f": {len(mig.ficou_por_duvida)}")
    assert inventada in texto
    for aviso in mig.avisos:
        assert aviso in texto
    assert len(texto.split("\n")) <= 40


def test_relatorio_com_falha_diz_que_nada_foi_gravado():
    m = _mod()
    texto = m.relatorio(m.Migracao(), ["conservação: linha sem destino (CLAUDE.md): x"])
    assert "Nada foi gravado" in texto and "linha sem destino" in texto


def test_relatorio_limita_lista_de_duvidas():
    m = _mod()
    mig = m.Migracao(ficou_por_duvida=[f"- **Regra {i}**: texto {i}" for i in range(60)])
    texto = m.relatorio(mig, [])
    assert len(texto.split("\n")) <= 40
    assert "Ficaram por dúvida" in texto and ": 60" in texto and "e mais 50" in texto


def test_historico_continua_funcionando(tmp_path, monkeypatch):
    m = _mod()
    chamadas = []
    monkeypatch.setattr(m, "gravar_linhas_do_kit", lambda repo: chamadas.append(repo) or 7)
    assert m.main(["historico"]) == 0
    assert len(chamadas) == 1
