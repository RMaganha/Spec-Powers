"""Ajudante pesquisador (0.58.0) — decisão 25 de `docs/specs/memoria-em-tabela.md`.

Um ajudante do kit que lê muito na janela dele e devolve só o resumo. O arquivo `agents/pesquisador.md` é
prosa (o Claude Code o carrega como `mss-spec:pesquisador`), então o que se testa aqui é a ligação:
- o arquivo existe e só dá ao ajudante as ferramentas de leitura (critério 2);
- o texto traz o formato da resposta e a descrição diz quando chamar — e quando não (critério 3);
- as regras do kit, as portas e os comandos nomeiam o ajudante e os três casos (critério 5).
Que ele aparece na lista de ajudantes de uma conversa nova só se prova no real (critério 1).
"""
import importlib.util
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
AJUDANTE = REPO / "agents" / "pesquisador.md"
NOME = "mss-spec:pesquisador"
CASOS = ("outra conversa", "muitos arquivos", "outro assunto")
# O Claude Code ignora estes campos em ajudante de plugin (code.claude.com/docs/en/sub-agents): escrevê-los
# daria a impressão de uma trava que não existe.
IGNORADOS_EM_PLUGIN = ("hooks", "mcpServers", "permissionMode", "initialPrompt")


def _partes():
    """(campos do cabeçalho, corpo). O cabeçalho é lido como YAML de verdade — é assim que o Claude Code o lê:
    um `: ` solto na descrição quebraria o ajudante, e um parse por `split(":")` não veria."""
    texto = AJUDANTE.read_text(encoding="utf-8")
    assert texto.startswith("---\n"), "agents/pesquisador.md sem cabeçalho"
    _, cabecalho, corpo = texto.split("---\n", 2)
    campos = yaml.safe_load(cabecalho)
    assert isinstance(campos, dict), "o cabeçalho do ajudante não é um YAML de chave e valor"
    return {k: str(v) for k, v in campos.items()}, corpo


def _texto(rel):
    return (REPO / rel).read_text(encoding="utf-8")


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


def test_ajudante_usa_o_modelo_da_conversa_e_nao_traz_campo_ignorado():
    campos, _ = _partes()
    assert campos.get("model") == "inherit", "escolha aprovada: mesmo modelo da conversa (mais barato não foi medido)"
    usados = [c for c in IGNORADOS_EM_PLUGIN if c in campos]
    assert not usados, f"campo que o Claude Code ignora em ajudante de plugin: {usados}"
    assert "isolation" not in campos, "o owner não usa worktree (hooks/sem_worktree.py nega)"


# --- critério 3: quando chamar e o que devolve -------------------------------------------------------

def test_descricao_diz_os_tres_casos_e_que_nao_e_pra_toda_tarefa():
    campos, _ = _partes()
    desc = campos["description"].lower()
    faltam = [c for c in CASOS if c not in desc]
    assert not faltam, f"a descrição não diz quando chamar: faltam {faltam}"
    assert re.search(r"\b(não|nunca)\b[^.;—]{0,15}\btoda tarefa\b", desc), \
        "a descrição não diz que o ajudante NÃO é pra toda tarefa — é ela que o assistente lê pra decidir"
    assert re.search(r"\bsó\b[^.;—]{0,20}\btrês casos\b", desc), "a descrição não limita o uso aos três casos"
    assert len(campos["description"]) <= 600, "a descrição entra em toda conversa: até 600 letras"


def test_corpo_traz_o_formato_da_resposta():
    _, corpo = _partes()
    low = corpo.lower()
    for marca in ("primeira linha", "`arquivo:linha`", "não li", "não achei", "3.000 letras"):
        assert marca in low, f"o texto do ajudante não fala de {marca!r}"
    assert re.search(r"nunca (cole|copie)", low), "o texto não proíbe colar o arquivo na resposta"
    assert re.search(r"(não|nunca) (grava|gravar|grave)", low), "o texto não diz que o ajudante não grava"
    assert "conversa_texto.py" in corpo, "o texto não diz de onde vem a outra conversa em texto"


# --- critério 5: onde a regra aparece ----------------------------------------------------------------

def test_regra_bola_de_neve_nomeia_o_ajudante():
    bloco = _texto("templates/regras-do-kit/1-modo-de-trabalho.md")
    linha = next(l for l in bloco.splitlines() if "Bola de neve" in l)
    assert NOME in linha and "subagente" in linha, "a linha da bola de neve não nomeia o ajudante do kit"
    low = linha.lower()
    assert "outra conversa" in low and "muitos arquivos" in low, "a linha não diz os outros dois casos"
    assert "toda tarefa" in low, "a linha não diz que o ajudante não é pra toda tarefa"
    assert len(linha.encode("utf-8")) <= 600, "linha gigante é procedimento disfarçado de regra"


def test_comandos_e_aviso_de_janela_nomeiam_o_ajudante():
    for rel in ("commands/to-dolist.md", "commands/nova-feature.md"):
        assert NOME in _texto(rel), f"{rel} fala em subagente sem nomear o ajudante do kit"
    spec = importlib.util.spec_from_file_location("alerta_contexto_ajudante", REPO / "hooks" / "alerta_contexto.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pro_assistente, _ = mod.mensagens(76.0, 152_000, 200_000, 75)
    assert NOME in pro_assistente and "subagente" in pro_assistente


def test_portas_tem_o_passo_do_ajudante_com_o_comando_do_script():
    titulo = "Leitura grande vai pelo ajudante pesquisador"
    for rel in ("commands/tarefa.md", "commands/bug.md", "commands/duvida.md"):
        texto = _texto(rel)
        assert texto.count(titulo) == 1, f"{rel}: o passo do ajudante tem de aparecer uma vez"
        passo = texto.split(titulo, 1)[1].split("\n\n", 1)[0]
        low = passo.lower()
        assert NOME in passo, f"{rel}: o passo não nomeia o ajudante"
        faltam = [c for c in CASOS if c not in low]
        assert not faltam, f"{rel}: o passo não diz {faltam}"
        assert '"${CLAUDE_PLUGIN_ROOT}/templates/conversa_texto.py"' in passo, \
            f"{rel}: sem o comando que põe a outra conversa em texto"
        assert re.search(r"\bnão é pra toda tarefa\b", low), f"{rel}: o passo não diz que não é pra toda tarefa"
        numeros = re.findall(r"^\*\*(\d+[a-z]?)\. ", texto, flags=re.M)
        repetidos = sorted({n for n in numeros if numeros.count(n) > 1})
        assert not repetidos, f"{rel}: passo com número repetido: {repetidos}"


def test_leia_me_apresenta_o_ajudante():
    leia = _texto("docs/LEIA-ME.md")
    assert NOME in leia and "agents/pesquisador.md" in leia
