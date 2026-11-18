"""migrar_claude_md.py — monta e confere (dry-run) a migração do CLAUDE.md pro formato com as regras do kit no plugin.

Por que: o CLAUDE.md do Whats (10.096 B) trazia uma cópia velha das regras do kit e os FATOS de infra atrás de
gatilho de arquivo em `.claude/rules/` (F-040). A migração tira o que é do kit, traz os fatos de volta por extenso
pro `## Contexto` e só segue se nenhuma linha sumir sem destino conferido. Fala do owner: "o projeto não pode se
perder e eu ter que passar tudo de novo".

Fixture: cópia LIDA do Whats em 2026-10-23 (`tests/fixtures/whats-2026-10-23/`), byte a byte.

Camadas (2026-11-18, `docs/decisoes.md`): `montar` e `conferir` são testados em memória — o projeto é um dicionário
{caminho: bytes} (o `disco`) e o ponto de volta do git (`git_status`) entra como função; o `main`, com o `aplicar`
falso. O disco e o git de verdade (git status, troca atômica e restauração, CRLF gravado, segunda rodada) ficam num
teste só, num repositório montado uma vez com `git init --template=`; o processo python, num teste só.
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
PROJ = REPO.parent / "projeto-que-nao-existe-migrar"          # absoluto, nunca criado


@pytest.fixture(scope="module")
def m():
    spec = importlib.util.spec_from_file_location("migrar_claude_md", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def kit(m):
    return set(m.carregar_linhas_do_kit())


# --- o projeto em memória ----------------------------------------------------------------------------

class Disco:
    """O que `montar` e `conferir` leem, num dicionário {caminho: bytes} — os 3 métodos do `DiscoReal`."""

    def __init__(self, arquivos):
        self.arquivos = {Path(p): b for p, b in arquivos.items()}

    def eh_arquivo(self, p):
        return Path(p) in self.arquivos

    def ler_bytes(self, p):
        try:
            return self.arquivos[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def regras(self, pasta):
        saida = []
        for p in sorted(self.arquivos):
            try:
                rel = p.relative_to(Path(pasta))
            except ValueError:
                continue
            if p.suffix == ".md":
                saida.append(rel.as_posix())
        return saida

    def texto(self, rel):
        return self.arquivos[PROJ / rel].decode("utf-8").replace("\r\n", "\n")


def _projeto(claude_md, regras=None):
    """`claude_md` e as regras ({nome: texto}) como o projeto os teria no disco (UTF-8)."""
    arquivos = {PROJ / "CLAUDE.md": claude_md.encode("utf-8") if isinstance(claude_md, str) else claude_md}
    for nome, texto in (regras or {}).items():
        arquivos[PROJ / ".claude" / "rules" / nome] = texto.encode("utf-8") if isinstance(texto, str) else texto
    return Disco(arquivos)


def _whats(claude_md=None):
    """A fixture do Whats (CLAUDE.md + 7 regras), lida do kit."""
    return _projeto(claude_md if claude_md is not None else (FIXTURE / "CLAUDE.md").read_bytes(),
                    {n: (FIXTURE / ".claude" / "rules" / n).read_bytes() for n in REGRAS_WHATS})


def _sem_falha_no_git(_proj, _tocados):
    return []


def _montar(m, kit, disco, **kw):
    return m.montar(PROJ, kit, disco=disco, **kw)


def _conferir(m, kit, disco, mig):
    return m.conferir(PROJ, mig, kit, disco=disco, git_status=_sem_falha_no_git)


def _montar_whats(m, kit, **kw):
    disco = _whats()
    return disco, _montar(m, kit, disco, **kw)


def _secao(texto: str, titulo: str) -> list:
    """Linhas do corpo da seção `## <titulo…>` (sem o cabeçalho), até a próxima `## `."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    ini = next(i for i, l in enumerate(linhas) if l.startswith("## " + titulo))
    fim = next((j for j in range(ini + 1, len(linhas)) if linhas[j].startswith("## ")), len(linhas))
    return linhas[ini + 1:fim]


# --- normalizar / linhas do kit ----------------------------------------------------------------------

def test_normalizar_ignora_bom_cr_marcador_numeracao_e_espacos(m):
    assert m.normalizar("﻿-   **Idioma**:  responda   em pt-BR\r") == "**Idioma**: responda em pt-BR"
    assert m.normalizar("12. **Regra**  x") == "**Regra** x"
    assert m.normalizar("  * item") == "item"
    assert m.normalizar("   ") == ""


def test_linhas_do_kit_em_dia(m):
    """Lê o histórico do molde no git do próprio kit (só leitura)."""
    if not (REPO / ".git").exists():
        pytest.skip("sem .git no kit: o histórico do molde não está disponível")
    raso = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO, capture_output=True, text=True)
    if raso.stdout.strip() == "true":
        pytest.skip("clone raso: o histórico do molde está incompleto")
    gravado = [l for l in LINHAS_KIT.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n") if l]
    assert m.gerar_linhas_do_kit(REPO) == gravado, \
        "linhas-do-kit.txt desatualizado: rode `python templates/migrar_claude_md.py historico`"


# --- Whats -------------------------------------------------------------------------------------------

def test_whats_contexto_sem_ponteiro_para_rules(m, kit):
    _, mig = _montar_whats(m, kit)
    contexto = _secao(mig.claude_novo, "Contexto")
    assert not [l for l in contexto if ".claude/rules/" in l]
    corpo = "\n".join(contexto)
    for rotulo in ("**Como roda:**", "**Homologação (Azure):**", "**Versionamento:**", "**Banco:**",
                   "**Testes:**", "**UI:**", "**Infra:**"):
        assert rotulo in corpo, rotulo
    assert "gunicorn na porta 8000" in corpo
    assert "mss-miti-ai-agent-bot-webwhats-dev-br" in corpo


def test_whats_fatos_saem_do_arquivo_de_regra(m, kit):
    _, mig = _montar_whats(m, kit)
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


def test_whats_regras_novas_mantem_crlf(m, kit):
    _, mig = _montar_whats(m, kit)
    assert "\r\n" in mig.regras_novas["banco.md"]
    assert "\n" not in mig.regras_novas["banco.md"].replace("\r\n", "")
    assert "\n" not in mig.claude_novo.replace("\r\n", "")


def test_whats_linhas_do_kit_saem(m, kit):
    _, mig = _montar_whats(m, kit)
    assert "Não codar antes do meu OK explícito" not in mig.claude_novo
    assert any("Não codar antes do meu OK explícito" in l for l in mig.saiu_do_kit)
    assert "## Modo de trabalho" not in mig.claude_novo
    assert "## Regras críticas" not in mig.claude_novo


def test_whats_ponteiro_para_doc_do_projeto_fica(m, kit):
    _, mig = _montar_whats(m, kit)
    regras = _secao(mig.claude_novo, "Regras obrigatórias do projeto")
    assert len([l for l in regras if "docs/MODO-DE-TRABALHO.md" in l]) == 4
    corpo = "\n".join(regras)
    for titulo in ("**Comando `/mss-spec:<x>` referenciado NÃO é inexistente", "**Nível de cerimônia**",
                   "**Git — branch da principal + local-only**", "**Plano de teste base (anti-regressão)**"):
        assert titulo in corpo, titulo


def test_whats_seta_no_meio_da_frase_nao_e_ponteiro(m, kit):
    """`família bateu → abra memory/indice/<f>.md` não é linha-ponteiro (a seta não vem logo depois do título):
    é regra do kit com redação do projeto — fica, mas entra na dúvida pro owner conferir."""
    _, mig = _montar_whats(m, kit)
    indices = next(l for l in _secao(mig.claude_novo, "Regras obrigatórias do projeto")
                   if "**Índices do projeto**" in l)
    assert indices in mig.ficou_por_duvida
    assert not [l for l in mig.ficou_por_duvida if "docs/MODO-DE-TRABALHO.md" in l]


def test_whats_regras_do_projeto_ficam(m, kit):
    _, mig = _montar_whats(m, kit)
    corpo = "\n".join(_secao(mig.claude_novo, "Regras obrigatórias do projeto"))
    assert "`.env` desta pasta **nunca**" in corpo
    assert "Nunca tocar o que é do RAG" in corpo
    assert "**A UI deste projeto é PRÓPRIA e INTOCÁVEL**" in corpo


def test_whats_indice_cada_regra_uma_vez(m, kit):
    _, mig = _montar_whats(m, kit)
    indice = _secao(mig.claude_novo, "Índice de regras por tipo de arquivo")
    corpo = "\n".join(indice)
    for nome in REGRAS_WHATS:
        assert corpo.count(f"`.claude/rules/{nome}`") == 1, nome
    linha_banco = next(l for l in indice if "banco.md" in l)
    assert linha_banco == ("- `.claude/rules/banco.md` — Banco e RAG de produção — carrega ao tocar "
                           "`**/*.sql`, `sql/**`, `persistencia/**`")


def test_whats_marca_e_titulo(m, kit):
    _, mig = _montar_whats(m, kit)
    linhas = mig.claude_novo.replace("\r\n", "\n").split("\n")
    assert MARCA in linhas
    assert linhas.index(MARCA) < next(i for i, l in enumerate(linhas) if l.startswith("# IA Bot Agent - Whats"))
    ordem = [l for l in linhas if l.startswith("## ")]
    assert ordem == ["## Regras obrigatórias do projeto", "## Contexto", "## Mapa de arquivos",
                     "## Índice de regras por tipo de arquivo"]
    assert mig.ja_migrado is False


def test_whats_conservacao(m, kit):
    disco, mig = _montar_whats(m, kit)
    assert _conferir(m, kit, disco, mig) == []
    assert set(mig.saiu_do_kit) <= kit
    indice = "\n".join(_secao(mig.claude_novo, "Índice de regras por tipo de arquivo"))
    regras = {n: disco.texto(f".claude/rules/{n}") for n in REGRAS_WHATS}
    depois_textos = [mig.claude_novo] + [mig.regras_novas.get(n, regras[n]) for n in REGRAS_WHATS]
    depois = {m.normalizar(l) for t in depois_textos for l in t.replace("\r\n", "\n").split("\n")}
    claude = disco.texto("CLAUDE.md")
    contexto_antes = _secao(claude, "Contexto")
    antes = [l for t in [claude, *regras.values()] for l in t.split("\n") if l.strip()]
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


def test_conferir_pega_linha_que_sumiria(m, kit):
    """A conservação é do `conferir`, independente do `montar`: tirar uma linha do resultado reprova."""
    disco, mig = _montar_whats(m, kit)
    estado = next(l for l in mig.claude_novo.split("\r\n") if l.startswith("- **Estado:**"))
    mig.claude_novo = mig.claude_novo.replace(estado + "\r\n", "")
    falhas = _conferir(m, kit, disco, mig)
    assert any("conservação" in f and "**Estado:**" in f for f in falhas), falhas


def test_conferir_pega_linha_do_projeto_disfarcada_de_kit(m, kit):
    disco, mig = _montar_whats(m, kit)
    linha = next(l for l in mig.claude_novo.split("\r\n") if "Segredo e ambiente" in l)
    mig.claude_novo = mig.claude_novo.replace(linha + "\r\n", "")
    mig.saiu_do_kit.append(m.normalizar(linha))
    falhas = _conferir(m, kit, disco, mig)
    assert any("linhas-do-kit.txt" in f for f in falhas), falhas
    assert any("conservação" in f and "Segredo e ambiente" in f for f in falhas), falhas


def test_conferir_pega_item_tirado_da_regra_sem_voltar(m, kit):
    disco, mig = _montar_whats(m, kit)
    mig.claude_novo = "\r\n".join(l for l in mig.claude_novo.split("\r\n") if not l.startswith("- **Banco:**"))
    assert any("**Banco:**" in f for f in _conferir(m, kit, disco, mig))


def test_conferir_junta_a_falha_do_ponto_de_volta(m, kit):
    disco, mig = _montar_whats(m, kit)
    vistos = []

    def sujo(proj, tocados):
        vistos.append((proj, tocados))
        return ["working tree sujo nos arquivos que a migração toca"]
    assert m.conferir(PROJ, mig, kit, disco=disco, git_status=sujo) == \
        ["working tree sujo nos arquivos que a migração toca"]
    assert vistos == [(PROJ, ["CLAUDE.md"] + [f".claude/rules/{n}" for n in sorted(mig.regras_novas)])]


def test_whats_tamanho_vira_aviso_nao_falha(m, kit):
    disco, mig = _montar_whats(m, kit, teto=5000)
    assert any("5000" in a or "5.000" in a for a in mig.avisos), mig.avisos
    tamanho = len(mig.claude_novo.encode("utf-8"))
    assert any(str(tamanho) in a or f"{tamanho:,}".replace(",", ".") in a for a in mig.avisos), mig.avisos
    assert _conferir(m, kit, disco, mig) == []


def test_whats_dentro_do_teto_padrao_sem_aviso_de_tamanho(m, kit):
    _, mig = _montar_whats(m, kit)
    assert len(mig.claude_novo.encode("utf-8")) <= 10000
    assert not [a for a in mig.avisos if "teto" in a]


# --- casos de falha e de dúvida ----------------------------------------------------------------------

PONTEIRO_COMO_RODA = ("- **Como roda:** → texto inteiro em `.claude/rules/deploy-e-ambiente.md` "
                      "(carrega sozinho ao tocar `Dockerfile`).")
REGRA_PRE_VOO = "---\npaths:\n  - \"Dockerfile\"\n---\n\n# Deploy\n\n- **Pré-vôo:** rode o doctor.\n"


def test_rotulo_inexistente_reprova(m, kit):
    disco = _projeto(f"# Proj — teste\n\n## Contexto\n- **Infra:** própria.\n{PONTEIRO_COMO_RODA}\n",
                     {"deploy-e-ambiente.md": REGRA_PRE_VOO})
    falhas = _conferir(m, kit, disco, _montar(m, kit, disco))
    assert any(PONTEIRO_COMO_RODA in f for f in falhas), falhas


def test_regra_com_acento_no_nome_e_reconhecida(m, kit):
    claude = ("# Proj — x\n\n## Contexto\n- **Segurança:** → texto inteiro em `.claude/rules/segurança.md` "
              "(carrega sozinho ao tocar `apis/**`).\n")
    regra = "---\npaths:\n  - \"apis/**\"\n---\n\n# Segurança\n\n- **Segurança:** token Bearer.\n\n- Nunca logar PII.\n"
    disco = _projeto(claude, {"segurança.md": regra})
    mig = _montar(m, kit, disco)
    assert "- **Segurança:** token Bearer." in mig.claude_novo
    assert mig.regras_novas["segurança.md"].endswith("# Segurança\n\n- Nunca logar PII.\n")
    assert _conferir(m, kit, disco, mig) == []


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


def _projeto_molde_pre_marca(texto=None):
    regras = {p.name: p.read_bytes() for p in (REPO / "templates" / "rules").glob("*.md")}
    return _projeto(texto or _molde_pre_marca_preenchido(), regras)


def test_molde_pre_marca_preenchido_migra(m, kit):
    texto = _molde_pre_marca_preenchido()
    disco = _projeto_molde_pre_marca(texto)
    mig = _montar(m, kit, disco)
    assert _conferir(m, kit, disco, mig) == []
    contexto = _secao(mig.claude_novo, "Contexto")
    assert not [l for l in contexto if ".claude/rules/" in l]
    assert "- **UI:** web — FastAPI + Jinja" in contexto
    assert "- **Banco:** PostgreSQL 16" in contexto
    assert any(de == "CLAUDE.md › ## Contexto" and "banco-e-segredo.md" in linha and "ponteiro" in para
               for linha, de, para in mig.moveu)
    # toda linha das seções do kit e dos comentários do molde saiu como do kit
    secao, do_kit = None, []
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


def test_fragmento_ver_rules_sem_arquivo_reprova(m, kit):
    linha = "- **Banco:** PostgreSQL 16 — ver `.claude/rules/banco-e-segredo.md`"
    disco = _projeto(f"# Proj — x\n\n## Contexto\n{linha}\n")
    falhas = _conferir(m, kit, disco, _montar(m, kit, disco))
    assert any(linha in f for f in falhas), falhas


def test_conferir_so_aceita_o_fragmento_registrado(m, kit):
    """Tirar o fragmento sem registrar em `moveu` (ou tirar mais que o fragmento) reprova."""
    disco = _projeto_molde_pre_marca()
    mig = _montar(m, kit, disco)
    mig.moveu = [x for x in mig.moveu if "ponteiro" not in x[2]]
    falhas = _conferir(m, kit, disco, mig)
    assert any("conservação" in f and "banco-e-segredo.md" in f for f in falhas), falhas


# --- seções de título parecido; linhas repetidas ------------------------------------------------------

def test_secoes_de_titulo_parecido_nao_se_perdem(m, kit):
    disco = _projeto("# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n\n## Contexto do negocio\n- X\n\n"
                     "## Mapa de arquivos\n- `a.py` — faz A\n\n## Mapa de arquivos extra\n- `b.py`\n")
    mig = _montar(m, kit, disco)
    novo = mig.claude_novo.split("\n")
    for l in ("## Contexto", "- **Infra:** MSIG", "## Contexto do negocio", "- X", "## Mapa de arquivos",
              "- `a.py` — faz A", "## Mapa de arquivos extra", "- `b.py`"):
        assert l in novo, l
    assert novo.index("## Contexto do negocio") < novo.index("## Mapa de arquivos extra")
    assert _conferir(m, kit, disco, mig) == []


def test_mesmo_titulo_duas_vezes_e_concatenado(m, kit):
    disco = _projeto("# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n\n## Mapa de arquivos\n- `a.py`\n\n"
                     "## Contexto\n- **Banco:** PG\n")
    mig = _montar(m, kit, disco)
    contexto = _secao(mig.claude_novo, "Contexto")
    assert "- **Infra:** MSIG" in contexto and "- **Banco:** PG" in contexto
    assert mig.claude_novo.count("## Contexto\n") == 1
    assert _conferir(m, kit, disco, mig) == []


DUPLICADA = "- Toda alteração de tarifa passa pela atuária antes do deploy."


def test_linha_repetida_em_duas_secoes_sobrevive(m, kit):
    disco = _projeto(f"# Proj — x\n\n## Contexto\n- **Infra:** MSIG\n{DUPLICADA}\n\n## Notas da equipe\n{DUPLICADA}\n")
    mig = _montar(m, kit, disco)
    assert mig.claude_novo.split("\n").count(DUPLICADA) == 2
    assert _conferir(m, kit, disco, mig) == []
    # mutante: some uma das duas → a conservação por contagem pega
    linhas = mig.claude_novo.split("\n")
    linhas.remove(DUPLICADA)
    mig.claude_novo = "\n".join(linhas)
    falhas = _conferir(m, kit, disco, mig)
    assert any("conservação" in f and "atuária" in f for f in falhas), falhas


INVENTADA = "- **Idioma**: responda em latim nas sextas-feiras, inclusive nos commits."


def _whats_com(*linhas):
    original = (FIXTURE / "CLAUDE.md").read_bytes().decode("utf-8")
    extra = "".join(f"{l}\r\n" for l in linhas)
    alterado = original.replace("## Modo de trabalho (nunca violar)\r\n", f"## Modo de trabalho (nunca violar)\r\n{extra}", 1)
    assert alterado != original
    return _whats(alterado.encode("utf-8"))


def test_linha_desconhecida_fica_por_duvida(m, kit):
    sem_titulo = "- Toda sexta, rode o backup do Chatwoot antes de abrir branch."
    disco = _whats_com(INVENTADA, sem_titulo)
    mig = _montar(m, kit, disco)
    regras = _secao(mig.claude_novo, "Regras obrigatórias do projeto")
    assert INVENTADA in regras and sem_titulo in regras
    assert INVENTADA in mig.ficou_por_duvida
    assert sem_titulo not in mig.ficou_por_duvida
    assert _conferir(m, kit, disco, mig) == []


def test_ja_migrado_nada_muda(m, kit):
    claude = f"<!-- topo -->\n{MARCA}\n\n# Proj — x\n\n## Contexto\n{PONTEIRO_COMO_RODA}\n"
    disco = _projeto(claude, {"deploy-e-ambiente.md": "# Deploy\n\n- **Como roda:** porta 8000.\n"})
    mig = _montar(m, kit, disco)
    assert mig.ja_migrado is True
    assert mig.claude_novo == claude
    assert mig.regras_novas == {} and mig.saiu_do_kit == [] and mig.moveu == []
    assert _conferir(m, kit, disco, mig) == []


def test_sem_claude_md_e_falha(m, kit):
    mig = _montar(m, kit, Disco({}))
    assert mig.falhas == [f"não existe {PROJ / 'CLAUDE.md'}"]


def test_comentario_html_so_sai_inteiro_quando_e_do_kit(m, kit):
    disco = _projeto("<!-- comentário do projeto, linha 1\n     linha 2 do projeto -->\n\n# Proj — x\n\n"
                     "## Contexto\n- **Infra:** própria.\n")
    mig = _montar(m, kit, disco)
    assert "<!-- comentário do projeto, linha 1" in mig.claude_novo
    assert "linha 2 do projeto -->" in mig.claude_novo
    assert _conferir(m, kit, disco, mig) == []


def test_linha_de_molde_no_contexto_fica(m, kit):
    """Linha do molde no `## Contexto`/`## Mapa de arquivos` é do projeto (o molde novo também as tem): fica."""
    molde = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").split("\n")
    stack = next(l for l in molde if l.startswith("- **Stack/runtime:**"))
    mapa = next(l for l in molde if l.startswith("- `docs/decisoes.md`"))
    disco = _projeto(f"# Proj — x\n\n## Contexto\n{stack}\n\n## Mapa de arquivos\n{mapa}\n")
    mig = _montar(m, kit, disco)
    assert stack in mig.claude_novo and mapa in mig.claude_novo
    assert _conferir(m, kit, disco, mig) == []


# --- BOM, CRLF e projeto sem rules ----------------------------------------------------------------------

def test_bom_e_crlf_preservados(m, kit):
    disco = _projeto("﻿# Proj — x\r\n\r\n## Contexto\r\n- **Infra:** própria.\r\n- **Banco:** PostgreSQL.\r\n"
                     "\r\n## Mapa de arquivos\r\n- `app.py` — entrada\r\n")
    novo = _montar(m, kit, disco).claude_novo
    assert novo.startswith("﻿") and novo.count("﻿") == 1
    assert "\n" not in novo.replace("\r\n", "")


def test_regra_com_bom_mantem_bom_no_comeco(m, kit):
    regra = ("﻿---\r\npaths:\r\n  - \"Dockerfile\"\r\n---\r\n\r\n# Deploy\r\n\r\n"
             "- **Como roda:** gunicorn na porta 8000.\r\n\r\n- Nunca publicar a porta do banco.\r\n")
    disco = _projeto(f"# Proj — teste\r\n\r\n## Contexto\r\n- **Infra:** própria.\r\n{PONTEIRO_COMO_RODA}\r\n",
                     {"deploy-e-ambiente.md": regra})
    mig = _montar(m, kit, disco)
    assert _conferir(m, kit, disco, mig) == []
    nova = mig.regras_novas["deploy-e-ambiente.md"]
    assert nova.startswith("﻿") and nova.count("﻿") == 1
    assert "\n" not in nova.replace("\r\n", "")
    assert "gunicorn" not in nova and "Nunca publicar" in nova
    assert "gunicorn na porta 8000" in mig.claude_novo


def test_projeto_sem_rules_so_ganha_marca_e_secoes(m, kit):
    original = ("# Proj — calcula prêmio\n\n## Contexto\n- **Infra:** própria.\n- **Banco:** PostgreSQL 16.\n\n"
                "## Regras obrigatórias do projeto\n1. **Nunca alterar a tabela `tarifa_base`** — é da atuária.\n\n"
                "## Observações\n- A planilha de tarifas chega toda segunda.\n")
    disco = _projeto(original)
    mig = _montar(m, kit, disco)
    assert _conferir(m, kit, disco, mig) == [] and mig.regras_novas == {}
    assert MARCA in mig.claude_novo
    depois = {m.normalizar(l) for l in mig.claude_novo.split("\n")}
    for l in original.split("\n"):
        if l.strip():
            assert m.normalizar(l) in depois, l
    assert "Índice de regras" not in mig.claude_novo


@pytest.mark.parametrize("arquivo", ["CLAUDE.md", ".claude/rules/banco.md"])
def test_arquivo_fora_de_utf8_para_e_diz_qual(m, kit, arquivo):
    disco = _whats()
    disco.arquivos[PROJ / arquivo] = "# São Paulo\n".encode("cp1252")
    with pytest.raises(m.NaoEhUtf8) as erro:
        _montar(m, kit, disco)
    assert m._msg_nao_utf8(PROJ, erro.value) == \
        f"{arquivo} não está em UTF-8: salve em UTF-8 e rode de novo. Nada foi gravado."


# --- relatório ------------------------------------------------------------------------------------------

def test_relatorio_curto(m, kit):
    mig = _montar(m, kit, _whats_com(INVENTADA), teto=100)
    assert mig.saiu_do_kit and mig.moveu and mig.ficou_por_duvida and mig.avisos
    texto = m.relatorio(mig, [])
    assert f"Saíram como do kit (o plugin já entrega): {len(mig.saiu_do_kit)}" in texto
    assert f"Mudaram de lugar: {len(mig.moveu)}" in texto
    assert texto.split("Ficaram por dúvida")[1].split("\n")[0].endswith(f": {len(mig.ficou_por_duvida)}")
    assert INVENTADA in texto
    for aviso in mig.avisos:
        assert aviso in texto
    assert len(texto.split("\n")) <= 40


def test_relatorio_com_falha_diz_que_nada_foi_gravado(m):
    texto = m.relatorio(m.Migracao(), ["conservação: linha sem destino (CLAUDE.md): x"])
    assert "Nada foi gravado" in texto and "linha sem destino" in texto


def test_relatorio_limita_lista_de_duvidas(m):
    texto = m.relatorio(m.Migracao(ficou_por_duvida=[f"- **Regra {i}**: texto {i}" for i in range(60)]), [])
    assert len(texto.split("\n")) <= 40
    assert "Ficaram por dúvida" in texto and ": 60" in texto and "e mais 50" in texto


# --- o main, com o projeto em memória e o aplicar falso ---------------------------------------------------

@pytest.fixture()
def cli(m, kit, monkeypatch, capsys):
    """`cli(disco, *flags, aplicar=None)` → (código, saída, chamadas do aplicar): o `main` com `montar`/`conferir`
    sobre o disco em memória e o `aplicar` trocado (por padrão, só anota)."""
    montar, conferir = m.montar, m.conferir

    def rodar(disco, *flags, aplicar=None, git_status=_sem_falha_no_git):
        chamadas = []
        monkeypatch.setattr(m, "montar", lambda proj, linhas, **kw: montar(PROJ, linhas, disco=disco, **kw))
        monkeypatch.setattr(m, "conferir", lambda proj, mig, linhas=None: conferir(PROJ, mig, linhas, disco=disco,
                                                                                   git_status=git_status))
        monkeypatch.setattr(m, "aplicar", aplicar or (lambda proj, mig, linhas=None: chamadas.append(mig)))
        codigo = m.main(["--proj", str(PROJ), *flags])
        return codigo, capsys.readouterr().out, chamadas
    return rodar


def test_main_previa_nao_aplica(cli):
    codigo, saida, chamadas = cli(_whats())
    assert codigo == 0 and saida.startswith("Prévia") and chamadas == []


def test_main_aplica_e_diz_como_desfazer(cli):
    codigo, saida, chamadas = cli(_whats(), "--aplicar")
    assert codigo == 0 and len(chamadas) == 1
    assert "Migração gravada. Nada foi feito no git." in saida
    assert "Pra desfazer: git restore CLAUDE.md .claude/rules/banco.md" in saida


def test_main_com_falha_nao_aplica(cli):
    disco = _projeto(f"# Proj — teste\n\n## Contexto\n- **Infra:** própria.\n{PONTEIRO_COMO_RODA}\n",
                     {"deploy-e-ambiente.md": REGRA_PRE_VOO})
    codigo, saida, chamadas = cli(disco, "--aplicar")
    assert codigo == 1 and chamadas == []
    assert PONTEIRO_COMO_RODA in saida and "Nada foi gravado" in saida


def test_main_working_tree_sujo_reprova(cli):
    def sujo(_proj, _tocados):
        return ["working tree sujo nos arquivos que a migração toca — commite ou descarte (`git restore`) antes: x"]
    codigo, saida, chamadas = cli(_whats(), "--aplicar", git_status=sujo)
    assert codigo == 1 and chamadas == [] and "working tree" in saida and "git restore" in saida


def test_main_ja_migrado(cli):
    codigo, saida, chamadas = cli(_projeto(f"{MARCA}\n\n# Proj — x\n"), "--aplicar")
    assert codigo == 0 and "já migrado" in saida and chamadas == []


@pytest.mark.parametrize("flags", [(), ("--aplicar",)])
@pytest.mark.parametrize("arquivo", ["CLAUDE.md", ".claude/rules/banco.md"])
def test_main_arquivo_fora_de_utf8_mensagem_curta(cli, flags, arquivo):
    disco = _whats()
    disco.arquivos[PROJ / arquivo] = "# São Paulo\n".encode("cp1252")
    codigo, saida, chamadas = cli(disco, *flags)
    assert codigo == 1 and chamadas == [] and "Traceback" not in saida
    assert f"{arquivo} não está em UTF-8: salve em UTF-8 e rode de novo. Nada foi gravado." in saida


def test_main_arquivo_em_uso_mensagem_curta(m, cli):
    def em_uso(proj, mig, linhas=None):
        raise m.GravacaoFalhou(PROJ / ".claude" / "rules" / "banco.md", PermissionError(13, "arquivo em uso"))
    codigo, saida, _ = cli(_whats(), "--aplicar", aplicar=em_uso)
    assert codigo == 1 and "Traceback" not in saida
    assert "Nada foi gravado: .claude/rules/banco.md estava em uso. Feche e rode de novo." in saida


def test_main_restauracao_que_falha_manda_git_restore(m, cli):
    def parcial(proj, mig, linhas=None):
        raise m.GravacaoFalhou(PROJ / ".claude" / "rules" / "banco.md", PermissionError(13, "em uso"),
                               [PROJ / "CLAUDE.md"])
    codigo, saida, _ = cli(_whats(), "--aplicar", aplicar=parcial)
    assert codigo == 1 and "migração parcial" in saida.lower() and "git restore CLAUDE.md" in saida


def test_main_projeto_que_mudou_reprova(cli):
    def mudou(proj, mig, linhas=None):
        raise RuntimeError("o projeto mudou depois da montagem — rode de novo")
    codigo, saida, _ = cli(_whats(), "--aplicar", aplicar=mudou)
    assert codigo == 1 and "Migração reprovada — nada foi gravado." in saida and "mudou depois da montagem" in saida


def test_historico_continua_funcionando(m, monkeypatch):
    chamadas = []
    monkeypatch.setattr(m, "gravar_linhas_do_kit", lambda repo: chamadas.append(repo) or 7)
    assert m.main(["historico"]) == 0
    assert len(chamadas) == 1


# --- o disco e o git de verdade (repositório montado uma vez) ----------------------------------------------

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _commitar(proj: Path) -> None:
    """Repo git LOCAL do teste (nunca o do owner): init + identidade local + commit de tudo."""
    _git(proj, "init", "-q", "--template=")
    _git(proj, "config", "user.name", "Teste mss-spec")
    _git(proj, "config", "user.email", "teste@exemplo.invalid")
    _git(proj, "config", "commit.gpgsign", "false")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "fixture")


def _copiar_whats(proj: Path) -> Path:
    (proj / ".claude" / "rules").mkdir(parents=True)
    shutil.copyfile(FIXTURE / "CLAUDE.md", proj / "CLAUDE.md")
    for nome in REGRAS_WHATS:
        shutil.copyfile(FIXTURE / ".claude" / "rules" / nome, proj / ".claude" / "rules" / nome)
    return proj


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("migrar_claude_md")
    _commitar(_copiar_whats(base / "whats"))
    _copiar_whats(base / "sem-git")
    cli = base / "cli"
    (cli / ".claude" / "rules").mkdir(parents=True)
    (cli / "CLAUDE.md").write_bytes(
        f"# Proj — teste\r\n\r\n## Contexto\r\n- **Infra:** própria.\r\n{PONTEIRO_COMO_RODA}\r\n".encode("utf-8"))
    (cli / ".claude" / "rules" / "deploy-e-ambiente.md").write_bytes(
        ("﻿---\r\npaths:\r\n  - \"Dockerfile\"\r\n---\r\n\r\n# Deploy\r\n\r\n"
         "- **Como roda:** gunicorn na porta 8000.\r\n\r\n- Nunca publicar a porta do banco.\r\n").encode("utf-8"))
    _commitar(cli)
    return base


def _arquivos(proj: Path) -> dict:
    return {p.relative_to(proj).as_posix(): p.read_bytes()
            for p in sorted(proj.rglob("*")) if p.is_file() and ".git" not in p.parts}


def _replace_que_falha_na_2a(m, monkeypatch):
    real = os.replace
    chamadas = []

    def falho(origem, destino):
        chamadas.append(str(destino))
        if len(chamadas) == 2:
            raise PermissionError(13, "arquivo em uso", str(destino))
        return real(origem, destino)
    monkeypatch.setattr(m.os, "replace", falho)
    return chamadas


def test_disco_e_git_de_ponta_a_ponta(m, kit, pasta, monkeypatch, capsys):
    whats = pasta / "whats"
    antes = _arquivos(whats)
    # conferir lê o disco e o git, e não escreve nada
    assert m.conferir(whats, m.montar(whats, kit), kit) == [] and _arquivos(whats) == antes
    # working tree sujo no arquivo que a migração toca reprova; fora dele, não
    banco = whats / ".claude" / "rules" / "banco.md"
    banco.write_bytes(antes[".claude/rules/banco.md"] + b"\r\n- linha nova sem commit\r\n")
    assert any("working tree" in f and "banco.md" in f for f in m.conferir(whats, m.montar(whats, kit), kit))
    banco.write_bytes(antes[".claude/rules/banco.md"])
    logging_md = whats / ".claude" / "rules" / "logging.md"
    logging_md.write_bytes(antes[".claude/rules/logging.md"] + b"\r\n")
    (whats / "outro.txt").write_text("sujo", encoding="utf-8")
    mig = m.montar(whats, kit)
    assert "logging.md" not in mig.regras_novas and m.conferir(whats, mig, kit) == []
    logging_md.write_bytes(antes[".claude/rules/logging.md"])
    (whats / "outro.txt").unlink()
    # sem git não há ponto de volta
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(pasta))
    sem_git = pasta / "sem-git"
    assert any("sem git não há ponto de volta" in f for f in m.conferir(sem_git, m.montar(sem_git, kit), kit))
    # aplicar recusa a montagem com falha e o projeto que mudou depois da montagem — nada gravado
    mig = m.montar(whats, kit)
    mig.claude_novo = "\r\n".join(l for l in mig.claude_novo.split("\r\n") if not l.startswith("- **Estado:**"))
    with pytest.raises(RuntimeError):
        m.aplicar(whats, mig, kit)
    assert _arquivos(whats) == antes
    mig = m.montar(whats, kit)
    claude = whats / "CLAUDE.md"
    claude.write_bytes(antes["CLAUDE.md"] + b"\r\n- mexi agora\r\n")
    mexido = _arquivos(whats)
    with pytest.raises(RuntimeError):            # o git status pega antes (o CLAUDE.md ficou sujo)
        m.aplicar(whats, mig, kit)
    assert _arquivos(whats) == mexido
    claude.write_bytes(antes["CLAUDE.md"])
    # a troca falha no meio: o que já foi trocado volta, nenhum .mss-tmp sobra
    replace_real, restaurar_real = os.replace, m._restaurar
    chamadas = _replace_que_falha_na_2a(m, monkeypatch)
    with pytest.raises(m.GravacaoFalhou) as erro:
        m.aplicar(whats, m.montar(whats, kit), kit)
    assert len(chamadas) == 2 and not erro.value.parcial
    assert _arquivos(whats) == antes and not list(whats.rglob("*.mss-tmp"))
    # ...e se a restauração também falha: fica parcial, e o git restore desfaz
    _replace_que_falha_na_2a(m, monkeypatch)

    def nao_restaura(destino, bruto):
        raise PermissionError(13, "em uso", str(destino))
    monkeypatch.setattr(m, "_restaurar", nao_restaura)
    with pytest.raises(m.GravacaoFalhou) as erro:
        m.aplicar(whats, m.montar(whats, kit), kit)
    assert erro.value.parcial == [whats / "CLAUDE.md"] and not list(whats.rglob("*.mss-tmp"))
    monkeypatch.setattr(m.os, "replace", replace_real)
    monkeypatch.setattr(m, "_restaurar", restaurar_real)
    _git(whats, "restore", "CLAUDE.md")
    assert _arquivos(whats) == antes
    # grava de verdade: só os arquivos tocados mudam, nenhum commit, CRLF preservado
    mig = m.montar(whats, kit)
    esperado = {"CLAUDE.md"} | {f".claude/rules/{n}" for n in mig.regras_novas}
    commits = _git(whats, "rev-list", "--count", "HEAD").stdout.strip()
    m.aplicar(whats, mig, kit)
    assert {l[3:] for l in _git(whats, "status", "--porcelain").stdout.split("\n") if l.strip()} == esperado
    assert _git(whats, "rev-list", "--count", "HEAD").stdout.strip() == commits
    for rel in esperado:
        bruto = (whats / rel).read_bytes()
        assert b"\r\n" in bruto and b"\n" not in bruto.replace(b"\r\n", b""), rel
    assert MARCA in (whats / "CLAUDE.md").read_text(encoding="utf-8") and m.montar(whats, kit).ja_migrado
    # segunda rodada: já migrado, nada muda
    depois = _arquivos(whats)
    assert m.main(["--proj", str(whats), "--aplicar"]) == 0
    assert "já migrado" in capsys.readouterr().out and _arquivos(whats) == depois


def test_processo_aplica_e_preserva_o_bom_da_regra(pasta):
    """Roda o script de verdade, como o `/mss-spec:upgrade` roda."""
    proj = pasta / "cli"
    r = subprocess.run([sys.executable, str(SCRIPT), "--proj", str(proj), "--aplicar"], capture_output=True)
    saida = r.stdout.decode("utf-8")
    assert r.returncode == 0, saida + r.stderr.decode("utf-8", "replace")
    assert "Migração gravada" in saida
    bruto = (proj / ".claude" / "rules" / "deploy-e-ambiente.md").read_bytes()
    assert bruto.startswith("﻿".encode("utf-8")) and bruto.count("﻿".encode("utf-8")) == 1
    assert b"\n" not in bruto.replace(b"\r\n", b"")
    assert b"gunicorn" not in bruto and b"Nunca publicar" in bruto
    assert "gunicorn na porta 8000" in (proj / "CLAUDE.md").read_bytes().decode("utf-8")
