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

from _texto_kit import BLOCOS

REPO = Path(__file__).resolve().parent.parent

# Desde a 0.42.0 o `templates/CLAUDE.md` é SÓ a parte do projeto: as regras do kit vivem em dois blocos em
# `templates/regras-do-kit/`, que o hook `regras_do_kit.py` injeta em toda janela (cada bloco ≤ 9.000
# caracteres, margem de 10% sob o limite de 10.000 do hook). Os 10.000 bytes do molde são ORÇAMENTO da parte
# do projeto, não trava: passou, o doctor/hook AVISA e o conserto é mover um bloco inteiro pro
# comando/rules/spec deixando ponteiro — nunca comprimir a redação de uma regra (as frases-chave abaixo são
# travadas por teste, agora nos blocos). O que nunca pode sair do molde é a seção `## Contexto`.
TETO_CLAUDE_MD = 10000      # bytes — a parte do projeto (orçamento + aviso), entra em toda sessão
TETO_BLOCO = 9000           # caracteres — cada bloco do kit (o hook limita a string em 10.000)
TETO_LINHA = 600            # bytes — linha gigante é procedimento disfarçado de regra
TETO_MAPA = 6000            # bytes — mapa é 1 tela, não arquivo morto
TETO_INDEX = 7000           # bytes — índice de tarefas ABERTAS
TETO_MEMORY_TOPO = 6000     # bytes — o TOPO do índice de memória; lido por test_hook_orcamento_partida.py


def _b(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").encode("utf-8"))


def _conteudo(p: Path) -> int:
    """Bytes sem os comentários `<!-- -->` (0.52.0: comentário do molde não é conteúdo da partida — a mesma medida do
    `rodizio_partida.bytes_de_conteudo` e do hook `orcamento_partida.py`)."""
    return len(re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S).encode("utf-8"))


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
    "Fonte ou não sei",
    "PERGUNTE, não vasculhe",
    "Responda só o que eu pedi",
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


def test_blocos_do_kit_cabem_no_limite_do_hook():
    """H — o hook entrega cada bloco numa string só (limite 10.000): bloco ≤ 9.000 caracteres."""
    for p in BLOCOS:
        n = len(p.read_text(encoding="utf-8"))
        assert n <= TETO_BLOCO, f"{p.name} tem {n} caracteres (teto {TETO_BLOCO})"


def test_frases_chave_estao_nos_blocos():
    """H — teto não justifica apagar regra: cada regra mantém sua frase-chave, agora nos blocos do kit
    (e não no molde do projeto)."""
    blocos = "\n".join(p.read_text(encoding="utf-8") for p in BLOCOS)
    molde = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    faltam = [f for f in FRASES_CHAVE_CLAUDE_MD if f not in blocos]
    assert not faltam, f"poda apagou regra de templates/regras-do-kit/: {faltam}"
    duplicadas = [f for f in FRASES_CHAVE_CLAUDE_MD if f in molde]
    assert not duplicadas, f"regra do kit ficou também no molde do projeto: {duplicadas}"


def test_regras_criticas_numeradas_no_bloco_2():
    """H — comandos citam "regra 8": as regras críticas seguem numeradas 1..11 no bloco 2."""
    txt = BLOCOS[1].read_text(encoding="utf-8")
    numeros = [int(n) for n in re.findall(r"^(\d+)\. ", txt, re.M)]
    assert numeros == list(range(1, 12)), f"regras críticas renumeradas: {numeros}"


def test_claude_md_sem_linha_gigante():
    """H — linha de 1.600 bytes não é regra, é procedimento: mora no comando/rule, não aqui."""
    p = REPO / "templates" / "CLAUDE.md"
    gordas = [(i, len(l.encode("utf-8")))
              for i, l in enumerate(p.read_text(encoding="utf-8").split("\n"), 1)
              if len(l.encode("utf-8")) > TETO_LINHA]
    assert not gordas, "linhas acima do teto em templates/CLAUDE.md: " + str(gordas)


def test_mapa_carrega_um_estado_anterior():
    """I — 79% do MAPA eram blocos de histórico relidos em toda partida. Fica 1; o resto sai."""
    p = REPO / "docs" / "superpowers" / "MAPA.md"
    txt = p.read_text(encoding="utf-8")
    blocos = txt.count("<!-- histórico do estado anterior -->")
    assert blocos <= 1, f"MAPA.md tem {blocos} blocos de histórico (limite 1 — o resto vai pro arquivo)"
    n = _conteudo(p)
    assert n <= TETO_MAPA, f"MAPA.md tem {n} bytes de conteúdo (teto {TETO_MAPA}; comentário não conta)"
    assert (REPO / "docs" / "superpowers" / "MAPA-historico.md").exists(), \
        "falta docs/superpowers/MAPA-historico.md (onde o histórico passa a viver, lido sob demanda)"


def test_index_so_com_tarefa_viva():
    """I — o índice lido na partida é o das tarefas ABERTAS; o histórico de fechadas sai."""
    p = REPO / "docs" / "superpowers" / "INDEX.md"
    n = _conteudo(p)
    assert n <= TETO_INDEX, f"INDEX.md tem {n} bytes de conteúdo (teto {TETO_INDEX}; comentário não conta)"
    assert (REPO / "docs" / "superpowers" / "INDEX-historico.md").exists(), \
        "falta docs/superpowers/INDEX-historico.md (tarefas fechadas, lidas sob demanda)"
    txt = p.read_text(encoding="utf-8")
    assert "## Fora de escopo" not in txt, "fora de escopo mora no to-dolist com a tag #fora-de-escopo (0.47.0)"


def test_moldes_nao_dizem_que_o_indice_do_repo_nao_carrega():
    """L — 'acima de 25 KB o excedente não carrega' vale só pra pasta NATIVA do Claude Code. O índice do repo
    entra pelo Read (2.000 linhas). Copiar o teto da nativa pro repo mandou PODAR um índice de 93 memórias."""
    for rel in ("templates/MEMORY.md", "commands/memory.md", "commands/doctor.md"):
        low = (REPO / rel).read_text(encoding="utf-8").lower()
        for frase in ("excedente nem carrega", "excedente não carrega", "200 linhas / 25 kb", "200 linhas e 25 kb"):
            assert frase not in low, f"{rel} ainda repete a premissa falsa: {frase!r}"
        assert "orçamento" in low, f"{rel} não explica que o teto é orçamento de partida"


def test_doctor_aponta_o_conserto_mecanico():
    """G — o doctor só reporta, mas agora o conserto é UMA linha que o owner manda rodar."""
    txt = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    # desde a 0.33.0 o conserto do MAPA e do INDEX é um comando só: `enxugar` (roda `mapa` + `index` + a 2ª etapa)
    for script, modo in (("rodizio_partida", "enxugar"),
                         ("memoria_indice", "dividir"), ("memoria_indice", "verificar")):
        # aceita `…/rodizio_partida.py" mapa` (caminho entre aspas) e `rodizio_partida.py mapa`
        assert re.search(rf'{script}\.py"?\s+{modo}\b', txt), f"doctor não aponta `{script}.py {modo}` como conserto"
