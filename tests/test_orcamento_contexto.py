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

# 8.000 bytes (~2.000 tokens) foi o que sobrou em 2026-08-18 depois de mover todo procedimento pro seu
# lar (comando, `.claude/rules/`, spec). Em 2026-09-23 o owner subiu pra 10.000: no teto de 8 KB a
# regra de Git precisou ser espremida palavra por palavra pra caber — e a 1ª tentativa apagou duas
# frases que o smoke test exige. Espremer redação de regra é o que quebra em silêncio; com a janela de
# 1M, 2 KB (~500 tokens) custam menos que isso. Passou de 10 KB, o procedimento é o de sempre, sem
# exceção: MOVER um bloco inteiro de procedimento pro comando/rules/spec, deixando ponteiro — nunca
# comprimir a redação de uma regra (as frases-chave abaixo são travadas por teste).
TETO_CLAUDE_MD = 10000      # bytes — o molde que entra em toda sessão
TETO_LINHA = 600            # bytes — linha gigante é procedimento disfarçado de regra
TETO_MAPA = 6000            # bytes — mapa é 1 tela, não arquivo morto
TETO_INDEX = 7000           # bytes — índice de tarefas ABERTAS
TETO_MEMORY_TOPO = 6000     # bytes — o TOPO do índice de memória (famílias); os subíndices carregam sob demanda


def _b(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").encode("utf-8"))


def test_claude_md_dentro_do_orcamento():
    """H — o molde do CLAUDE.md entra em toda sessão de todo projeto: é o token mais caro do kit."""
    p = REPO / "templates" / "CLAUDE.md"
    n = _b(p)
    assert n <= TETO_CLAUDE_MD, f"templates/CLAUDE.md tem {n} bytes (teto {TETO_CLAUDE_MD})"


# Uma frase por regra — o que não pode sumir numa poda. Poda que precise tirar uma destas está
# APAGANDO regra: mova o bloco inteiro pro comando/rules/spec em vez de comprimir a redação.
FRASES_CHAVE_CLAUDE_MD = (
    "sempre em pt-BR",
    "Não codar antes do meu OK explícito",
    "Declare as premissas antes do OK",
    "Não inventar fatos concretos",
    "PERGUNTE, não vasculhe",
    "Falha ao executar a habilidade",
    "a partir da principal atualizada",
    "nunca a partir de outra branch",
    "Stage **nominal**",
    "`git push` em dev/homologação/produção e deploy: nunca você",
    "o hook pede a minha aprovação",
    "Um assunto por janela",
    "Bola de neve",
    "Comando pra eu rodar = passo a passo",
    "Pedido com várias partes",
    "Relate o que está no disco",
    "`<private>`",
    "NUNCA num `CLAUDE.md`",
    "Nunca commitar `.env`",
    "Tailwind",
    "Estrutura de pastas em camadas",
    "secure-by-default",
    "Spec viva não pode mentir",
    "nunca `print`",
    "outro projeto é SOMENTE-LEITURA",
    "rode o teste e cole a saída",
    "Pré-vôo de ambiente",
    "Diagnóstico disciplinado",
)


def test_claude_md_mantem_as_frases_chave_das_regras():
    """H — teto não justifica apagar regra: cada regra do molde mantém sua frase-chave, e as regras
    críticas seguem numeradas 1..11 (comandos citam "regra 8")."""
    txt = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    faltam = [f for f in FRASES_CHAVE_CLAUDE_MD if f not in txt]
    assert not faltam, f"poda apagou regra do templates/CLAUDE.md: {faltam}"
    criticas = txt.split("## Regras críticas", 1)[1]
    numeros = [int(n) for n in re.findall(r"^(\d+)\. ", criticas, re.M)]
    assert numeros[:11] == list(range(1, 12)), f"regras críticas renumeradas: {numeros}"


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


def test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega():
    """L — 'acima de 25 KB o excedente não carrega' vale só pra pasta NATIVA do Claude Code. O índice do repo
    entra pelo Read (2.000 linhas). Copiar o teto da nativa pro repo mandou PODAR um índice de 93 memórias."""
    for rel in ("templates/MEMORY.md", "commands/memory.md", "commands/doctor.md"):
        low = (REPO / rel).read_text(encoding="utf-8").lower()
        for frase in ("excedente nem carrega", "excedente não carrega", "200 linhas / 25 kb", "200 linhas e 25 kb"):
            assert frase not in low, f"{rel} ainda repete a premissa falsa: {frase!r}"
        assert "orçamento" in low, f"{rel} não explica que o teto é orçamento de partida"


def test_molde_de_memoria_ensina_o_topo_e_o_subindice():
    txt = (REPO / "templates" / "MEMORY.md").read_text(encoding="utf-8")
    assert "indice/" in txt and "subíndice" in txt.lower(), "templates/MEMORY.md não ensina os dois níveis"
    assert "6 KB" in txt, "templates/MEMORY.md não documenta o teto do topo"
    assert "memoria_indice.py" in txt, "templates/MEMORY.md não aponta o script que divide/verifica"


def test_claude_md_manda_abrir_o_subindice_quando_a_familia_bate():
    low = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "memory/indice/" in low, "CLAUDE.md não diz onde estão os subíndices"
    assert "antes de agir" in low, "CLAUDE.md não manda abrir o subíndice ANTES de agir"


def test_anatomia_usa_o_teto_do_topo():
    src = (REPO / "templates" / "anatomia.py").read_text(encoding="utf-8")
    assert '"memory/MEMORY.md": 6000' in src, "anatomia.py ainda mede o índice contra 25 KB"


def test_doctor_aponta_o_conserto_mecanico():
    """G — o doctor só reporta, mas agora o conserto é UMA linha que o owner manda rodar."""
    txt = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    # desde a 0.33.0 o conserto do MAPA e do INDEX é um comando só: `enxugar` (roda `mapa` + `index` + a 2ª etapa)
    for script, modo in (("rodizio_partida", "enxugar"),
                         ("memoria_indice", "dividir"), ("memoria_indice", "verificar")):
        # aceita `…/rodizio_partida.py" mapa` (caminho entre aspas) e `rodizio_partida.py mapa`
        assert re.search(rf'{script}\.py"?\s+{modo}\b', txt), f"doctor não aponta `{script}.py {modo}` como conserto"
