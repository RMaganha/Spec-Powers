"""memoria_tabela.py — tudo o que é memória do projeto numa tabela SQLite local (cópia para busca).

Por que existe: no teste de mesa de 2026-11-10 (4 projetos, 944 casos) a tabela com tudo o que é memória achou
o arquivo certo entre os 10 em 41% dos pedidos reais, contra 12% do jeito de hoje, lendo 4 vezes menos no
Whats. Decisão do owner: o arquivo no git é o original, a tabela é cópia, e ela mora FORA do `.claude`
("qualquer alteração perde") e fora de qualquer repo. Spec: docs/specs/memoria-em-tabela.md.

Camadas (2026-11-18, `docs/decisoes.md`): o projeto é um dicionário {caminho: bytes} (`Disco`, sem git) e a tabela
é um SQLite `:memory:` que sobrevive entre as conexões (`BancoNaMemoria`). O disco e o git de verdade (dono e data
do commit, o que o git ignora, pendência, a pasta da tabela criada, a tabela presa por outro programa) ficam num
teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_tabela.py"
BASE = REPO.parent / "memoria-tabela-que-nao-existe"          # absoluto, nunca criado

NOTA = ("---\nname: project-boleto\ndescription: O boleto vem do CRM e nao do portal\n"
        "gatilho: quando emitir segunda via\nmetadata:\n  type: project\n---\n\n"
        "A segunda via usa a tabela TB_BOLETO.\n\n<private>segredo-xyz</private>\n")
EVALS = ("# Falhas\n\n| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
         "| F-001 | 2026-09-29 | quando emitir boleto sem conferir | premissa não-dita | conferir o CRM antes | aberto |\n")
HTML = ("<html><head><style>p{color:red}</style></head><body><h2>Deploy</h2>"
        "<p>Publicar no ambiente <b>orquidea</b>.</p><script>var x=1</script></body></html>")


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("memoria_tabela", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ o projeto e a tabela em memória

class Disco:
    """O projeto em memória, com os métodos do `DiscoReal`: sem git (`git` devolve None, como pasta fora de
    repositório), a "data" de cada arquivo é um contador que sobe a cada gravação, e conta o que foi lido."""

    def __init__(self):
        self.dados, self.versao, self.lidos, self.gits, self.lidas = {}, {}, 0, 0, ""
        self.jsonl = []                    # as conversas da máquina: [(nome, data em segundos)]

    def gravar(self, p, texto):
        self.dados[Path(p)] = texto.encode("utf-8") if isinstance(texto, str) else texto
        self.versao[Path(p)] = self.versao.get(Path(p), 0) + 1

    def apagar(self, p):
        del self.dados[Path(p)]

    def eh_arquivo(self, p):
        return Path(p) in self.dados

    def ler_bytes(self, p):
        self.lidos += 1
        try:
            return self.dados[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def arquivos(self, raiz, pasta):
        base = Path(raiz) / pasta
        return [p.relative_to(raiz).as_posix() for p in self.dados if base in p.parents]

    def marca(self, p):
        return (len(self.dados[Path(p)]), self.versao[Path(p)]) if Path(p) in self.dados else None

    def git(self, raiz, *args):
        self.gits += 1
        return None

    def conversas(self, pasta):
        return list(self.jsonl)

    def lidas_ate(self, raiz):
        return self.lidas


class _SemFechar:
    """A conexão do banco em memória: `close` não fecha (senão a tabela some)."""

    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass

    def __getattr__(self, nome):
        return getattr(self._conn, nome)


class BancoNaMemoria:
    """A tabela num SQLite `:memory:` — os métodos do `BancoReal`."""

    def __init__(self):
        self.conn, self.criado = sqlite3.connect(":memory:"), False

    def __str__(self):
        return "(tabela em memória)"

    def existe(self):
        return self.criado

    def preparar(self):
        pass

    def conectar(self, timeout):
        self.criado = True
        return _SemFechar(self.conn)

    def sql(self, consulta, args=()):
        return self.conn.execute(consulta, args).fetchall()


def _projeto(disco, pasta="alfa", titulo="Projeto Alfa", base=BASE):
    raiz = base / pasta
    arquivos = {
        "memory/MEMORY.md": "- **Geral** → [subíndice](indice/geral.md) — 1 memórias\n",
        "memory/indice/geral.md": ("# Geral\n\n- **quando mexer no boleto do corretor** → [Boleto vem do CRM]"
                                   "(../project_boleto.md) — gancho do indice\n"),
        "memory/project_boleto.md": NOTA,
        "memory/DIARIO.md": ("# Diário\n\n## 2026-10-01\n\n- [boleto-no-crm] Sessao sobre o boleto no CRM → "
                             "sessions/2026-10-01-boleto-no-crm.md\n"),
        "memory/sessions/2026-10-01-boleto-no-crm.md": ("# 2026-10-01 — boleto\n\n## Conversamos\n"
                                                        "- falamos do boleto zebra\n\n## Pivôs\n- trocamos de rota\n"),
        "docs/decisoes.md": "# Decisões\n\n- 2026-09-30 — **usar a fila X em vez de Y** — porque Z.\n",
        "docs/EVALS.md": EVALS,
        "docs/specs/boleto.md": "# Boleto\n\n## Estado atual\nA rota /boleto devolve o PDF.\n\n## Histórico\n- 2026-09-01 — criado.\n",
        "docs/superpowers/plans/2026-09-01-boleto.md": "# Plano\n\n## Tarefas\n1. fazer a rota girafa\n",
        "docs/superpowers/MAPA.md": "# Mapa\n\n## Onde estamos\nna branch do boleto hipopotamo\n",
        "docs/ARQUITETURA.md": ("# Arquitetura\n\n## Visão\ntexto da visao do sistema.\n\n## Banco\n"
                                "tabela TB_BOLETO fica no schema dbo.\n"),
        "docs/guia.html": HTML,
        "to-dolist.md": "# To-do\n\n- comprar o dominio tartaruga\n",
        ".env": "SENHA=abc123\n",
        "docs/variaveis.txt": "TOKEN=zzz999\n",
    }
    if titulo:
        arquivos["CLAUDE.md"] = f"# {titulo} — objetivo em uma frase\n"
    for rel, texto in arquivos.items():
        disco.gravar(raiz / rel, texto)
    return raiz


@pytest.fixture()
def disco():
    return Disco()


@pytest.fixture()
def banco():
    return BancoNaMemoria()


def _linhas(mod, disco, raiz):
    return mod.linhas_do_projeto(raiz, usar_git=False, disco=disco)


def _por_arq(linhas, arq):
    return [l for l in linhas if l["arq"] == arq]


def _montar(mod, disco, banco, raiz, **kw):
    return mod.montar(raiz, banco, usar_git=kw.pop("usar_git", False), disco=disco, **kw)


# ------------------------------------------------------------------ onde fica + esquema

def test_caminho_padrao_fica_na_pasta_do_usuario_fora_do_claude(mod, monkeypatch):
    monkeypatch.delenv("MSS_MEMORIA_TABELA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: BASE / "casa")
    p = mod.caminho_tabela()
    assert p == BASE / "casa" / "mss-spec" / "memoria.sqlite3"
    assert ".claude" not in p.parts, "o owner vetou o .claude: qualquer alteração perde"


def test_variavel_troca_o_caminho(mod, monkeypatch):
    monkeypatch.setenv("MSS_MEMORIA_TABELA", str(BASE / "outro" / "t.sqlite3"))
    assert mod.caminho_tabela() == BASE / "outro" / "t.sqlite3"


def test_esquema_de_outra_versao_e_refeito(mod, disco, banco):
    banco.criado = True
    banco.conn.execute("CREATE TABLE memoria (lixo TEXT)")
    banco.conn.execute("PRAGMA user_version = 99")
    _montar(mod, disco, banco, _projeto(disco))
    assert banco.sql("PRAGMA user_version")[0][0] == mod.VERSAO_ESQUEMA
    assert banco.sql("SELECT count(*) FROM memoria WHERE tipo = 'anotacao'")[0][0] == 1


# ------------------------------------------------------------------ ler o projeto

def test_cada_fonte_vira_linha_com_o_tipo_certo(mod, disco):
    tipo = {l["arq"]: l["tipo"] for l in _linhas(mod, disco, _projeto(disco))}
    assert tipo == {
        "memory/project_boleto.md": "anotacao",
        "memory/sessions/2026-10-01-boleto-no-crm.md": "diario",
        "docs/decisoes.md": "decisao",
        "docs/EVALS.md": "falha",
        "docs/specs/boleto.md": "spec",
        "docs/superpowers/plans/2026-09-01-boleto.md": "plano",
        "docs/superpowers/MAPA.md": "mapa",
        "to-dolist.md": "mapa",
        "docs/ARQUITETURA.md": "documento",
        "docs/guia.html": "documento",
    }


def test_anotacao_leva_a_frase_do_subindice_e_a_classe(mod, disco):
    (l,) = _por_arq(_linhas(mod, disco, _projeto(disco)), "memory/project_boleto.md")
    assert "segunda via" in l["quando"] and "boleto do corretor" in l["quando"]
    assert l["classe"] == "project"
    assert "CRM" in l["resumo"]
    assert l["titulo"] == "project boleto"
    assert "TB_BOLETO" in l["texto"]


def test_anotacao_fora_de_utf8_entra_sem_frontmatter(mod, disco):
    raiz = _projeto(disco)
    disco.gravar(raiz / "memory" / "torta.md", b"---\nname: torta\n---\n\n\xff\xfe texto cru\n")
    (l,) = _por_arq(_linhas(mod, disco, raiz), "memory/torta.md")
    assert (l["tipo"], l["titulo"], l["texto"]) == ("anotacao", "torta", "")


def test_diario_leva_a_linha_do_diario_e_a_data(mod, disco):
    (l,) = _por_arq(_linhas(mod, disco, _projeto(disco)), "memory/sessions/2026-10-01-boleto-no-crm.md")
    assert "Sessao sobre o boleto" in l["resumo"]
    assert l["data"] == "2026-10-01"
    assert "zebra" in l["texto"]


def test_decisao_vira_uma_linha_por_item_datado(mod, disco):
    (l,) = _por_arq(_linhas(mod, disco, _projeto(disco)), "docs/decisoes.md")
    assert (l["ponteiro"], l["data"], l["titulo"]) == ("docs/decisoes.md:3", "2026-09-30", "usar a fila X em vez de Y")


def test_falha_vira_uma_linha_por_caso(mod, disco):
    (l,) = _por_arq(_linhas(mod, disco, _projeto(disco)), "docs/EVALS.md")
    assert l["ponteiro"] == "docs/EVALS.md:5"
    assert "emitir boleto" in l["quando"]
    assert l["classe"] == "premissa não-dita"
    assert l["data"] == "2026-09-29"
    assert l["titulo"].startswith("F-001")


def test_documento_vira_uma_linha_por_secao_com_arquivo_e_linha(mod, disco):
    secoes = _por_arq(_linhas(mod, disco, _projeto(disco)), "docs/ARQUITETURA.md")
    assert [(l["ponteiro"], l["titulo"]) for l in secoes] == [
        ("docs/ARQUITETURA.md:3", "ARQUITETURA › Visão"),
        ("docs/ARQUITETURA.md:6", "ARQUITETURA › Banco"),
    ]


def test_html_entra_sem_tags_nem_script(mod, disco):
    (l,) = _por_arq(_linhas(mod, disco, _projeto(disco)), "docs/guia.html")
    assert "orquidea" in l["texto"] and "Deploy" in l["titulo"]
    for lixo in ("<b>", "var x", "color:red"):
        assert lixo not in l["texto"]


def test_private_env_e_txt_ficam_fora(mod, disco):
    linhas = _linhas(mod, disco, _projeto(disco))
    tudo = " ".join(" ".join(str(v) for v in l.values()) for l in linhas)
    for segredo in ("segredo-xyz", "abc123", "zzz999"):
        assert segredo not in tudo
    assert not [l["arq"] for l in linhas if l["arq"].endswith((".env", ".txt"))]


def test_secao_gigante_e_dividida_em_pedacos(mod, disco):
    raiz = _projeto(disco)
    disco.gravar(raiz / "docs" / "grande.md", "# Grande\n\n## Tudo\n" + ("palavra " * 1700) + "\n")
    pedacos = _por_arq(_linhas(mod, disco, raiz), "docs/grande.md")
    assert len(pedacos) == 3 and all(len(l["texto"]) <= 6000 for l in pedacos)
    assert {l["ponteiro"] for l in pedacos} == {"docs/grande.md:3"}


def test_arquivo_fora_de_utf8_nao_derruba(mod, disco):
    raiz = _projeto(disco)
    disco.gravar(raiz / "docs" / "ruim.md", b"# Ruim\n\n## Parte\n\xff\xfe texto cru\n")
    assert _por_arq(_linhas(mod, disco, raiz), "docs/ruim.md")


def test_nome_do_projeto_vem_do_claude_md_e_cai_pro_nome_da_pasta(mod, disco):
    assert mod.nome_projeto(_projeto(disco), disco) == "Projeto Alfa"
    assert mod.nome_projeto(_projeto(disco, pasta="beta", titulo=None), disco) == "beta"


# ------------------------------------------------------------------ montar e remontar

def test_montar_grava_e_conta_por_tipo(mod, disco, banco):
    r = _montar(mod, disco, banco, _projeto(disco))
    assert r.projeto == "Projeto Alfa" and r.tabela is banco
    assert r.por_tipo == {"anotacao": 1, "diario": 1, "decisao": 1, "falha": 1, "spec": 2, "plano": 1,
                          "mapa": 2, "documento": 3}
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (10, 0, 0, 0)
    assert banco.sql("SELECT count(*) FROM memoria WHERE tipo <> 'controle'")[0][0] == sum(r.por_tipo.values())


def test_remontar_sem_mudanca_nao_refaz_nada(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    r = _montar(mod, disco, banco, raiz)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 0, 10)


def test_atualizar_em_dia_nao_le_arquivo_nem_chama_o_git(mod, disco, banco):
    raiz = _projeto(disco)
    assert mod.atualizar(raiz, banco, disco=disco) is not None, "tabela ausente: monta na hora"
    disco.lidos = disco.gits = 0
    assert mod.atualizar(raiz, banco, disco=disco) is None
    assert (disco.lidos, disco.gits) == (0, 0), "tabela em dia: a conferência é só nome, tamanho e data"
    disco.gravar(raiz / "to-dolist.md", "# To-do\n\n- outro item\n")
    assert mod.atualizar(raiz, banco, disco=disco).refeitos == 1


def test_mudar_um_arquivo_refaz_so_ele(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    disco.gravar(raiz / "docs" / "specs" / "boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    r = _montar(mod, disco, banco, raiz)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 1, 0, 9)
    textos = [t for (t,) in banco.sql("SELECT texto FROM memoria WHERE arq = 'docs/specs/boleto.md'")]
    assert len(textos) == 1 and "jacare" in textos[0]


def test_apagar_um_arquivo_tira_as_linhas(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    disco.apagar(raiz / "docs" / "superpowers" / "plans" / "2026-09-01-boleto.md")
    r = _montar(mod, disco, banco, raiz)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 1, 9)
    assert banco.sql("SELECT count(*) FROM memoria WHERE tipo = 'plano'")[0][0] == 0


def test_mudar_o_subindice_refaz_a_anotacao(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    disco.gravar(raiz / "memory" / "indice" / "geral.md",
                 "# Geral\n\n- **quando o corretor pedir o carne** → [Boleto vem do CRM](../project_boleto.md) — gancho\n")
    assert _montar(mod, disco, banco, raiz).refeitos == 1
    assert "carne" in banco.sql("SELECT quando FROM memoria WHERE tipo = 'anotacao'")[0][0]


def test_dois_projetos_ficam_na_mesma_tabela_sem_um_tocar_o_outro(mod, disco, banco):
    a, b = _projeto(disco, "alfa", "Projeto Alfa"), _projeto(disco, "beta", "Projeto Beta")
    _montar(mod, disco, banco, a)
    _montar(mod, disco, banco, b)
    antes = banco.sql("SELECT count(*) FROM memoria WHERE projeto = 'Projeto Beta'")[0][0]
    disco.apagar(a / "to-dolist.md")
    _montar(mod, disco, banco, a)
    assert {p for (p,) in banco.sql("SELECT DISTINCT projeto FROM memoria")} == {"Projeto Alfa", "Projeto Beta"}
    assert banco.sql("SELECT count(*) FROM memoria WHERE projeto = 'Projeto Beta'")[0][0] == antes


def test_pastas_de_mesmo_nome_nao_se_misturam(mod, disco, banco):
    a = _projeto(disco, "V2", titulo=None, base=BASE / "um")
    b = _projeto(disco, "V2", titulo=None, base=BASE / "dois")
    _montar(mod, disco, banco, a)
    assert _montar(mod, disco, banco, b).novos == 10, "a chave é a raiz do projeto, não o nome da pasta"
    assert banco.sql("SELECT count(DISTINCT raiz) FROM memoria")[0][0] == 2


def test_trocar_o_nome_do_projeto_atualiza_as_linhas(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    disco.gravar(raiz / "CLAUDE.md", "# Projeto Gama — outro objetivo\n")
    _montar(mod, disco, banco, raiz)
    assert {p for (p,) in banco.sql("SELECT DISTINCT projeto FROM memoria")} == {"Projeto Gama"}


def test_filtro_por_projeto_tipo_e_data_e_busca_por_palavra(mod, disco, banco):
    _montar(mod, disco, banco, _projeto(disco))
    assert banco.sql("SELECT ponteiro FROM memoria WHERE projeto = ? AND tipo = 'decisao' AND data >= '2026-09-01'",
                     ("Projeto Alfa",)) == [("docs/decisoes.md:3",)]
    assert banco.sql("SELECT arq FROM memoria WHERE memoria MATCH 'girafa'") == \
        [("docs/superpowers/plans/2026-09-01-boleto.md",)]


def test_linha_de_controle_guarda_a_assinatura_e_a_ultima_leitura_de_conversas(mod, disco, banco):
    disco.lidas = "2026-11-12"
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    ((assinatura, data),) = banco.sql("SELECT assinatura, data FROM memoria WHERE tipo = 'controle'")
    assert assinatura == mod.assinatura_do_disco(raiz, disco) and data == "2026-11-12"


def test_projeto_sem_git_segue_sem_erro(mod, disco, banco):
    r = _montar(mod, disco, banco, _projeto(disco), usar_git=True)
    assert r.novos == 10 and r.pendencias == [] and disco.gits > 0


def test_arquivo_grande_demais_fica_fora_e_vira_pendencia(mod, disco, banco, monkeypatch):
    raiz = _projeto(disco)
    monkeypatch.setattr(mod, "TETO_ARQUIVO", 200)
    disco.gravar(raiz / "docs" / "enorme.md", "# Enorme\n\n## Parte\n" + ("texto " * 100) + "\n")
    r = _montar(mod, disco, banco, raiz)
    assert not banco.sql("SELECT 1 FROM memoria WHERE arq = 'docs/enorme.md'")
    assert any("docs/enorme.md" in p for p in r.pendencias), r.pendencias


# ------------------------------------------------------------------ sono da memória (docs/specs/sono-da-memoria.md)
# Vieram de `tests/test_sono_da_memoria.py` (2026-11-18): o lado da tabela — a coluna de estado, o último sono na
# linha de controle, a conta das conversas e o "agora não". O hook que leva o aviso ao assistente é provado em
# `tests/test_hook_memoria_tabela_em_dia.py`; o formato do `conferida:` e a leitura do diário, no `memoria_indice`.

def _anotacao(disco, raiz, nome, conferida=None, corpo="corpo\n"):
    linha = f"conferida: {conferida}\n" if conferida is not None else ""
    disco.gravar(raiz / "memory" / f"{nome}.md",
                 f"---\nname: {nome}\ndescription: descrição longa o bastante de {nome}\n"
                 f"gatilho: quando acontecer a situação observável de {nome}\n{linha}metadata:\n  type: project\n---\n\n"
                 f"{corpo}")


CONVERSAS = BASE / "conversas"


def _conversas(disco, n, idade_dias=0.0):
    quando = time.time() - idade_dias * 86400
    disco.jsonl += [(f"sessao-{i:03d}.jsonl", quando) for i in range(n)]


def _aviso(mod, disco, banco, raiz):
    return mod.aviso_de_sono(raiz, banco, CONVERSAS, CONVERSAS / "atual.jsonl", disco=disco)


def test_montar_copia_o_estado_e_guarda_o_ultimo_sono_no_controle(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", "2026-11-12 — confirmada — fonte: hooks/x.py:12")
    _anotacao(disco, raiz, "nota_b", "2026-11-13 — conflito — fonte: docs/decisoes.md:1", corpo="CONFLITO: a; b\n")
    _montar(mod, disco, banco, raiz)
    estados = dict(banco.sql("SELECT arq, estado FROM memoria WHERE tipo = 'anotacao'"))
    assert estados["memory/nota_a.md"] == "2026-11-12 — confirmada — fonte: hooks/x.py:12"
    assert estados["memory/project_boleto.md"] == "", "nunca conferida: coluna vazia"
    assert banco.sql("SELECT data FROM memoria WHERE tipo = 'controle'") == [("2026-11-13",)]
    assert mod.ultimo_sono(raiz, banco) == "2026-11-13"


def test_busca_continua_achando_depois_da_coluna_nova(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    assert any("project_boleto" in str(a.get("ponteiro")) for a in mod.buscar(raiz, "boleto corretor", tabela=banco))


def test_dez_conversas_depois_do_ultimo_sono_dao_o_aviso_ao_assistente(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", "2026-01-01 — confirmada — fonte: hooks/x.py:12")
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 10)
    texto = _aviso(mod, disco, banco, raiz)
    assert "sono" in texto and "10" in texto and "2026-01-01" in texto
    assert "adiar-sono" in texto, "o assistente precisa saber o que rodar quando o owner disser agora não"


def test_nove_conversas_nao_dao_aviso(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", "2026-01-01 — confirmada — fonte: hooks/x.py:12")
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 9)
    assert _aviso(mod, disco, banco, raiz) is None


def test_conversa_anterior_ao_ultimo_sono_nao_conta_e_a_atual_tambem_nao(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", f"{time.strftime('%Y-%m-%d')} — confirmada — fonte: hooks/x.py:12")
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 15, idade_dias=3)
    disco.jsonl.append(("atual.jsonl", time.time()))
    assert _aviso(mod, disco, banco, raiz) is None


def test_projeto_que_nunca_dormiu_conta_todas_as_conversas(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 12, idade_dias=40)
    texto = _aviso(mod, disco, banco, raiz)
    assert "sono" in texto and "nunca" in texto


def test_aviso_nao_le_o_conteudo_das_conversas(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 12)
    lidos = disco.lidos
    assert "sono" in _aviso(mod, disco, banco, raiz)
    assert disco.lidos == lidos, "o aviso conta nome e data; nunca lê arquivo"


def test_adiar_guarda_a_data_no_controle_e_a_conta_recomeca(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    _conversas(disco, 12, idade_dias=2)
    hoje = time.strftime("%Y-%m-%d")
    assert mod.adiar_sono(raiz, banco, usar_git=False, disco=disco) == hoje
    assert mod.ultimo_sono(raiz, banco) == hoje
    assert _aviso(mod, disco, banco, raiz) is None
    _montar(mod, disco, banco, raiz)                                          # remontar não perde o adiamento
    assert mod.ultimo_sono(raiz, banco) == hoje


def test_leitura_mais_nova_que_a_conferencia_vira_o_ultimo_sono(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", "2026-11-13 — confirmada — fonte: hooks/x.py:12")
    disco.lidas = "2026-11-16"                    # o diário `conversas lidas até: 2026-11-16` (memoria_indice)
    _montar(mod, disco, banco, raiz)
    assert mod.ultimo_sono(raiz, banco) == "2026-11-16"


def test_conferencia_mais_nova_que_a_leitura_continua_valendo(mod, disco, banco):
    raiz = _projeto(disco)
    _anotacao(disco, raiz, "nota_a", "2026-11-20 — confirmada — fonte: hooks/x.py:12")
    disco.lidas = "2026-11-16"
    _montar(mod, disco, banco, raiz)
    assert mod.ultimo_sono(raiz, banco) == "2026-11-20"


# ------------------------------------------------------------------ status e linha de comando

def test_status_sem_tabela_avisa_como_remontar(mod, disco, banco):
    s = mod.status(_projeto(disco), banco, usar_git=False, disco=disco)
    assert s.existe is False and "montar" in s.mensagem


def test_status_em_dia(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    s = mod.status(raiz, banco, usar_git=False, disco=disco)
    assert (s.existe, s.mudaram) == (True, 0) and s.linhas == 12


def test_status_desatualizada_conta_os_arquivos(mod, disco, banco):
    raiz = _projeto(disco)
    _montar(mod, disco, banco, raiz)
    disco.gravar(raiz / "to-dolist.md", "# To-do\n\n- outro item\n")
    disco.apagar(raiz / "docs" / "guia.html")
    s = mod.status(raiz, banco, usar_git=False, disco=disco)
    assert s.mudaram == 2 and "montar" in s.mensagem


def test_cli_onde_imprime_o_caminho(mod, monkeypatch, capsys):
    monkeypatch.setenv("MSS_MEMORIA_TABELA", str(BASE / "casa" / "t.sqlite3"))
    assert mod.main(["onde"]) == 0
    assert capsys.readouterr().out.strip() == str(BASE / "casa" / "t.sqlite3")


def test_cli_status_sem_tabela_sai_com_1(mod, capsys):
    assert mod.main(["status", "--proj", str(BASE / "alfa"), "--tabela", str(BASE / "nao-existe.sqlite3")]) == 1
    assert "montar" in capsys.readouterr().out
    assert not BASE.exists()


def test_cli_tabela_presa_da_erro_claro_e_sai_com_2(mod, monkeypatch, capsys):
    def presa(*_a, **_k):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(mod, "montar", presa)
    assert mod.main(["montar", "--proj", str(BASE / "alfa"), "--tabela", str(BASE / "t.sqlite3"), "--sem-git"]) == 2
    assert "outro programa" in capsys.readouterr().out


# ------------------------------------------------------------------ ligação ao kit (prosa e memória)

def test_comando_memory_guarda_o_modo_tabela_fora_da_vista_do_owner():
    """Parte 2 (decisão 16, caso F-057): o modo `tabela` some da descrição e da ajuda — a tabela se atualiza
    sozinha. O texto do modo continua no comando, como uso interno e pro procedimento de troca de máquina."""
    mem = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    assert "tabela" not in mem.split("---")[1], "memory.md: a descrição/ajuda ainda oferece o modo tabela ao owner"
    abertura = mem.split("## Modo")[0]
    assert "**`tabela`**" not in abertura, "memory.md: a lista de modos do owner ainda traz o tabela"
    assert "## Uso interno: tabela" in mem, "memory.md: o texto do modo tabela sumiu (o procedimento precisa dele)"
    assert 'memoria_tabela.py" montar' in mem and 'memoria_tabela.py" status' in mem
    assert "~/mss-spec/" in mem and "fora do `.claude`" in mem, "memory.md não diz onde a tabela mora"
    assert "nunca grave na tabela" in mem.lower(), "memory.md não diz que o arquivo é o original"


def test_procedimento_de_troca_de_maquina_esta_na_memoria_do_kit(mod):
    mi = mod._motor()
    p = REPO / "memory" / "project_remontar_a_tabela_de_memoria.md"
    assert mi.frontmatter(p).get("type") == "procedimento"
    assert mi.validar_procedimento(mi.corpo(p)) == []
    indice = (REPO / "memory" / "indice" / "ambiente-desta-maquina-e-pendencias.md").read_text(encoding="utf-8")
    assert "project_remontar_a_tabela_de_memoria.md" in indice, "procedimento fora do subíndice: o recall não acha"


# ------------------------------------------------------------------ o disco e o git de verdade (pasta montada uma vez)

def _grava(raiz, rel, texto):
    p = raiz / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")


def _git(raiz, *args, autor="Fulana Teste", data="2026-08-15T10:00:00"):
    env = dict(os.environ, GIT_AUTHOR_NAME=autor, GIT_AUTHOR_EMAIL="fulana@exemplo.test", GIT_AUTHOR_DATE=data,
               GIT_COMMITTER_NAME=autor, GIT_COMMITTER_EMAIL="fulana@exemplo.test", GIT_COMMITTER_DATE=data)
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")


def _copiar(disco_memoria, raiz_memoria, raiz):
    for p, bruto in disco_memoria.dados.items():
        alvo = raiz / p.relative_to(raiz_memoria)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(bruto)


def _sql(tabela, consulta, args=()):
    c = sqlite3.connect(str(tabela))
    try:
        return c.execute(consulta, args).fetchall()
    finally:
        c.close()


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("memoria_tabela")
    for pasta in ("alfa", "IA Bot Agent - Açaí"):
        em_memoria = Disco()
        _copiar(em_memoria, _projeto(em_memoria, pasta=pasta), base / pasta)
    raiz = base / "alfa"
    _grava(raiz, ".gitignore", ".env\ndocs/escondido.md\n")
    _grava(raiz, "docs/escondido.md", "# Escondido\n\n## Parte\nconteudo ignorado pelo git papagaio\n")
    _git(raiz, "init", "-q", "--template=")
    _git(raiz, "add", ".gitignore", "CLAUDE.md", "memory", "docs", "to-dolist.md")
    _git(raiz, "commit", "-q", "-m", "inicio")
    (base / "casa").mkdir()
    return base


def test_disco_e_git_de_verdade(mod, pasta, capsys):
    raiz, tabela = pasta / "alfa", pasta / "nova" / "sub" / "t.sqlite3"
    # dono e data vêm da criação no git; o que o git ignora fica fora
    linhas = mod.linhas_do_projeto(raiz)
    (l,) = _por_arq(linhas, "memory/project_boleto.md")
    assert (l["dono"], l["data"]) == ("Fulana Teste", "2026-08-15")
    assert not _por_arq(linhas, "docs/escondido.md") and _por_arq(linhas, "docs/ARQUITETURA.md")
    # arquivo novo ainda não commitado entra e vira pendência; a pasta da tabela é criada
    _grava(raiz, "memory/feedback_novo.md",
           "---\nname: feedback-novo\ndescription: nota nova\nmetadata:\n  type: feedback\n---\n\ncorpo novo\n")
    r = mod.montar(raiz, tabela)
    assert tabela.is_file() and r.tabela == tabela and r.novos == 11
    assert any("1 arquivo" in p and "commit" in p for p in r.pendencias), r.pendencias
    # em dia pelo tamanho e data de verdade; mudou um arquivo → atualiza
    assert mod.atualizar(raiz, tabela) is None
    _grava(raiz, "to-dolist.md", "# To-do\n\n- item novo\n")
    # a tabela presa por outro programa: erro claro, sai com 2, e a tabela fica como estava
    antes = _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo <> 'controle'")[0][0]
    outro = sqlite3.connect(str(tabela))
    outro.execute("BEGIN EXCLUSIVE")
    try:
        codigo = mod.main(["montar", "--proj", str(raiz), "--tabela", str(tabela), "--sem-git"])
    finally:
        outro.rollback()
        outro.close()
    assert codigo == 2 and "outro programa" in capsys.readouterr().out
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo <> 'controle'")[0][0] == antes
    assert mod.atualizar(raiz, tabela) is not None
    # as conversas do sono: só nome e data dos .jsonl, sem contar a atual
    conversas = pasta / "conversas"
    conversas.mkdir()
    for nome in ("a.jsonl", "b.jsonl", "atual.jsonl", "nota.txt"):
        (conversas / nome).write_text("{}\n", encoding="utf-8")
    assert mod.conversas_desde(conversas, "", conversas / "atual.jsonl") == 2
    assert mod.conversas_desde(pasta / "nao-existe", "") == 0


def test_processo_com_os_padroes_monta_na_pasta_do_usuario(mod, pasta):
    raiz, casa = pasta / "IA Bot Agent - Açaí", pasta / "casa"
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8")
    env.pop("MSS_MEMORIA_TABELA", None)
    r = subprocess.run([sys.executable, str(SCRIPT), "montar", "--proj", str(raiz), "--sem-git"], cwd=str(pasta),
                       env=env, capture_output=True, timeout=120)
    saida = r.stdout.decode("utf-8", "ignore")
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")
    assert "Projeto Alfa" in saida and "anotacao" in saida
    assert _sql(casa / "mss-spec" / "memoria.sqlite3", "SELECT count(DISTINCT raiz) FROM memoria")[0][0] == 1
