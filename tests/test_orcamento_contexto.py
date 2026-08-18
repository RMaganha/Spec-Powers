"""Orçamento de contexto: o que o kit enfia na janela em TODA sessão.

Medido em 2026-08-18, antes desta feature: `templates/CLAUDE.md` custava 17.920 bytes (~4.343
tokens) em toda sessão de todo projeto, e o ritual de partida (MAPA + MEMORY + INDEX + EVALS)
somava ~8.899 tokens — ~13.200 tokens antes de qualquer trabalho útil. 79% do MAPA eram blocos
`<!-- histórico -->` relidos toda vez. A doc da Anthropic é direta: janela é recurso finito, e
arquivo de instrução inchado faz o modelo ignorar a regra que importa.

Estes testes são o teto. Guardrail não se apaga — se move pra onde carrega quando importa.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# 8.000 bytes (~2.000 tokens) NÃO é número redondo escolhido antes: é o que sobrou depois de mover
# todo procedimento pro seu lar (comando, `.claude/rules/`, spec) — o resto é guardrail com ponteiro,
# e cada um nasceu de falha real. Baixar mais significaria APAGAR regra, não movê-la. Se este teto
# apertar de novo, a pergunta certa é 'o que ainda é procedimento aqui?', não 'quanto posso cortar?'.
TETO_CLAUDE_MD = 8000       # bytes — o molde que entra em toda sessão
TETO_LINHA = 600            # bytes — linha gigante é procedimento disfarçado de regra
TETO_MAPA = 6000            # bytes — mapa é 1 tela, não arquivo morto
TETO_INDEX = 7000           # bytes — índice de tarefas ABERTAS


def _b(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").encode("utf-8"))


def test_claude_md_dentro_do_orcamento():
    """H — o molde do CLAUDE.md entra em toda sessão de todo projeto: é o token mais caro do kit."""
    p = REPO / "templates" / "CLAUDE.md"
    n = _b(p)
    assert n <= TETO_CLAUDE_MD, f"templates/CLAUDE.md tem {n} bytes (teto {TETO_CLAUDE_MD})"


def test_claude_md_sem_linha_gigante():
    """H — linha de 1.600 bytes não é regra, é procedimento: mora no comando/rule, não aqui."""
    p = REPO / "templates" / "CLAUDE.md"
    gordas = [(i, len(l.encode("utf-8")))
              for i, l in enumerate(p.read_text(encoding="utf-8").split("\n"), 1)
              if len(l.encode("utf-8")) > TETO_LINHA]
    assert not gordas, "linhas acima do teto em templates/CLAUDE.md: " + str(gordas)


def test_poda_moveu_e_nao_apagou():
    """H — cada guardrail podado continua alcançável: o CLAUDE.md aponta o novo lar."""
    txt = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    destinos = {
        "front-end (Tailwind/arquivos separados)": ".claude/rules/",
        "segurança (secure-by-default)": "docs/SEGURANCA.md",
        "estrutura em camadas": "docs/ESTRUTURA.md",
        "plano de teste anti-regressão": "/mss-spec:plano-teste",
        "pré-vôo de ambiente": "/mss-spec:doctor",
        "log padronizado": "/mss-spec:log",
        "memória por gatilho": "memory/MEMORY.md",
        "corpus de falhas": "docs/EVALS.md",
    }
    faltando = [nome for nome, alvo in destinos.items() if alvo not in txt]
    assert not faltando, "guardrail sem ponteiro no CLAUDE.md (foi apagado?):\n" + "\n".join(faltando)


def test_regras_sempre_ativas_sobreviveram():
    """H — as regras que NÃO podem sair (nasceram de falha registrada) seguem literais no molde."""
    low = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    for marca, porque in [
        ("não vasculhe", "F-001 — varri o disco 2×"),
        ("âncora", "F-004 — adotei o projeto B e quebrei o B"),
        ("não inventar fatos", "chute de caminho/host"),
        ("ok", "não codar antes do OK"),
        ("pt-br", "idioma"),
    ]:
        assert marca in low, f"regra sempre-ativa sumiu do CLAUDE.md: {marca!r} ({porque})"


def test_mapa_carrega_um_estado_anterior():
    """I — 79% do MAPA eram blocos de histórico relidos em toda partida. Fica 1; o resto sai."""
    txt = (REPO / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8")
    blocos = txt.count("<!-- histórico do estado anterior -->")
    assert blocos <= 1, f"MAPA.md tem {blocos} blocos de histórico (limite 1 — o resto vai pro arquivo)"
    n = len(txt.encode("utf-8"))
    assert n <= TETO_MAPA, f"MAPA.md tem {n} bytes (teto {TETO_MAPA})"
    assert (REPO / "docs" / "superpowers" / "MAPA-historico.md").exists(), \
        "falta docs/superpowers/MAPA-historico.md (onde o histórico passa a viver, lido sob demanda)"


def test_index_so_com_tarefa_viva():
    """I — o índice lido na partida é o das tarefas ABERTAS; o histórico de fechadas sai."""
    p = REPO / "docs" / "superpowers" / "INDEX.md"
    n = _b(p)
    assert n <= TETO_INDEX, f"INDEX.md tem {n} bytes (teto {TETO_INDEX})"
    assert (REPO / "docs" / "superpowers" / "INDEX-historico.md").exists(), \
        "falta docs/superpowers/INDEX-historico.md (tarefas fechadas, lidas sob demanda)"
    txt = p.read_text(encoding="utf-8")
    assert "Fora de escopo" in txt, "a seção anti-re-litígio 'Fora de escopo' TEM que ficar no índice vivo"


def test_moldes_documentam_o_teto():
    """I — a regra viaja pros outros projetos, não fica só neste repo."""
    mapa = (REPO / "templates" / "MAPA.md").read_text(encoding="utf-8")
    assert "MAPA-historico.md" in mapa, "templates/MAPA.md não ensina pra onde vai o histórico"
    idx = (REPO / "templates" / "INDEX.md").read_text(encoding="utf-8")
    assert "INDEX-historico.md" in idx, "templates/INDEX.md não ensina pra onde vão as tarefas fechadas"


def test_doctor_mede_o_orcamento():
    """G — o que não se mede, não se poda: o doctor reporta o custo de partida contra o teto."""
    txt = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    low = txt.lower()
    assert "orçamento de contexto" in low, "doctor não tem o check de orçamento de contexto"
    for alvo in ("CLAUDE.md", "MAPA.md", "MEMORY.md", "INDEX.md", "docs/EVALS.md"):
        assert alvo in txt, f"doctor não mede {alvo} no orçamento de partida"
    assert "bytes" in low or "kb" in low, "doctor não reporta o custo em bytes"


def test_diretiva_de_compactacao():
    """J — sessão longa compacta; sem diretiva, o que importa evapora."""
    txt = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    low = txt.lower()
    assert "compact" in low, "CLAUDE.md não instrui o que preservar na compactação"
    for alvo in ("branch", "premissa"):
        assert alvo in low, f"a diretiva de compactação não preserva {alvo}"


def test_higiene_de_janela():
    """K — /clear entre assuntos e investigação ampla por subagente: a janela principal fica limpa."""
    low = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "/clear" in low, "CLAUDE.md não manda /clear entre assuntos (janela-cesto-de-lixo)"
    assert "subagente" in low, "CLAUDE.md não manda investigação ampla ir por subagente"
