"""Sono da memória — parte 1, o acervo (docs/specs/sono-da-memoria.md, 0.62.0).

Por que existe: nota errada vira armadilha (`docs/analise/2026-11-13-sono-da-memoria.md`) e ninguém relia o acervo —
40 citações mortas e 0 de 78 anotações conferidas em 2026-11-13. Decisões do owner (2026-11-13): o estado vai no
frontmatter (`conferida: <data> — <estado> — fonte: <arquivo:linha>`), a tabela de memória ganha a coluna copiada
desse campo, e o hook de abertura avisa com 10 conversas sem sono, guardando a data do último sono na linha de
controle da tabela — sem hook novo.
"""
import importlib.util
import os
import sys
import time
from pathlib import Path

import pytest

from test_memoria_tabela import _grava, _projeto, _sql

REPO = Path(__file__).resolve().parent.parent


def _carrega(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _indice():
    return _carrega("memoria_indice", REPO / "templates" / "memoria_indice.py")


def _tabela_mod():
    return _carrega("memoria_tabela", REPO / "templates" / "memoria_tabela.py")


def _hook():
    return _carrega("memoria_tabela_em_dia", REPO / "hooks" / "memoria_tabela_em_dia.py")


def _anotacao(raiz, nome, conferida=None, corpo="corpo\n"):
    linha = f"conferida: {conferida}\n" if conferida is not None else ""
    _grava(raiz, f"memory/{nome}.md",
           f"---\nname: {nome}\ndescription: descrição longa o bastante de {nome}\n"
           f"gatilho: quando acontecer a situação observável de {nome}\n{linha}metadata:\n  type: project\n---\n\n{corpo}")


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "proj"
    _grava(raiz, "memory/MEMORY.md",
           "# Memória\n\n- **Geral** → [subíndice](indice/geral.md) — 3 memórias · quando: qualquer coisa\n")
    _grava(raiz, "memory/indice/geral.md",
           "# Geral\n\n- **quando a** → [A](../nota_a.md) — a\n- **quando b** → [B](../nota_b.md) — b\n"
           "- **quando c** → [C](../nota_c.md) — c\n")
    _anotacao(raiz, "nota_a", "2026-11-13 — confirmada — fonte: hooks/x.py:12")
    _anotacao(raiz, "nota_b", "2026-11-10 — não confirmada — fonte: nenhuma achada")
    _anotacao(raiz, "nota_c")
    return raiz


def _conferida_probs(mod, raiz):
    return [p for p in mod.verificar(raiz / "memory", sem_commit=set()) if "conferida" in p]


# ------------------------------------------------------------------ AC1 — formato do campo no `verificar`

def test_conferida_no_formato_e_sem_o_campo_passam(proj):
    assert _conferida_probs(_indice(), proj) == []


@pytest.mark.parametrize("valor", [
    "13/11/2026 — confirmada — fonte: hooks/x.py:12",          # data fora do formato
    "2026-11-13 — certa — fonte: hooks/x.py:12",               # estado que não existe
    "2026-11-13 — confirmada",                                  # sem fonte
    "2026-11-13 — confirmada — fonte: hooks/x.py",              # confirmada sem arquivo:linha
])
def test_conferida_fora_do_formato_e_acusada_pelo_nome(proj, valor):
    _anotacao(proj, "nota_c", valor)
    probs = _conferida_probs(_indice(), proj)
    assert len(probs) == 1 and "nota_c.md" in probs[0]


def test_conflito_sem_a_linha_conflito_no_corpo_e_acusado(proj):
    _anotacao(proj, "nota_c", "2026-11-13 — conflito — fonte: docs/decisoes.md:25")
    assert len(_conferida_probs(_indice(), proj)) == 1
    _anotacao(proj, "nota_c", "2026-11-13 — conflito — fonte: docs/decisoes.md:25",
              corpo="CONFLITO: docs/decisoes.md:25 (2026-07-30) diz A; docs/decisoes.md:34 (2026-09-23) diz B\n")
    assert _conferida_probs(_indice(), proj) == []


def test_ler_conferida_devolve_data_estado_e_fonte():
    mod = _indice()
    assert mod.ler_conferida("2026-11-13 — não confirmada — fonte: nenhuma achada") == \
        ("2026-11-13", "não confirmada", "nenhuma achada")
    assert mod.ler_conferida("qualquer coisa") is None


# ------------------------------------------------------------------ AC2 — o roteiro do sono

def test_roteiro_do_sono_conta_por_estado_e_lista_as_nunca_conferidas(proj):
    r = _indice().roteiro_do_sono(proj)
    assert r["por_estado"] == {"confirmada": 1, "não confirmada": 1, "conflito": 0, "nunca conferida": 1}
    assert r["nunca"] == ["nota_c.md"]
    assert r["ultimo_sono"] == "2026-11-13"
    assert "citacoes" in r and "duplicatas" in r


def test_obsoleta_fica_fora_do_roteiro(proj):
    _anotacao(proj, "nota_c")
    p = proj / "memory" / "nota_c.md"
    p.write_text(p.read_text(encoding="utf-8").replace("metadata:", "obsoleta: 2026-11-13 — superada por [[nota_a]]\nmetadata:"),
                 encoding="utf-8")
    r = _indice().roteiro_do_sono(proj)
    assert r["nunca"] == [] and r["por_estado"]["nunca conferida"] == 0


def test_cli_sono_imprime_o_roteiro(proj, capsys):
    assert _indice().main(["sono", "--proj", str(proj)]) == 0
    saida = capsys.readouterr().out
    assert "nunca conferida" in saida and "nota_c.md" in saida and "2026-11-13" in saida


# ------------------------------------------------------------------ AC3 — coluna de estado e último sono na tabela

def test_montar_copia_o_estado_e_guarda_o_ultimo_sono_no_controle(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _tabela_mod()
    _anotacao(raiz, "nota_a", "2026-11-12 — confirmada — fonte: hooks/x.py:12")
    _anotacao(raiz, "nota_b", "2026-11-13 — conflito — fonte: docs/decisoes.md:1", corpo="CONFLITO: a; b\n")
    mod.montar(raiz, tabela, usar_git=False)
    estados = dict(_sql(tabela, "SELECT arq, estado FROM memoria WHERE tipo = 'anotacao'"))
    assert estados["memory/nota_a.md"] == "2026-11-12 — confirmada — fonte: hooks/x.py:12"
    assert estados["memory/project_boleto.md"] == "", "nunca conferida: coluna vazia"
    assert _sql(tabela, "SELECT data FROM memoria WHERE tipo = 'controle'") == [("2026-11-13",)]
    assert mod.ultimo_sono(raiz, tabela) == "2026-11-13"


def test_busca_continua_achando_depois_da_coluna_nova(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _tabela_mod()
    mod.montar(raiz, tabela, usar_git=False)
    assert any("project_boleto" in str(a.get("ponteiro")) for a in mod.buscar(raiz, "boleto corretor", tabela=tabela))


# ------------------------------------------------------------------ AC4 — o aviso de 10 conversas na abertura

def _conversas(pasta: Path, n: int, idade_dias: float = 0):
    pasta.mkdir(parents=True, exist_ok=True)
    quando = time.time() - idade_dias * 86400
    for i in range(n):
        p = pasta / f"sessao-{i:03d}.jsonl"
        p.write_text("{}\n", encoding="utf-8")
        os.utime(p, (quando, quando))


def _abertura(raiz, atual: Path, source="startup"):
    return {"hook_event_name": "SessionStart", "source": source, "cwd": str(raiz), "transcript_path": str(atual)}


def _pronta(raiz, tabela):
    """Tabela já em dia (montada sem git): o hook só confere a assinatura e não chama o git — o caso de toda abertura."""
    _tabela_mod().montar(raiz, tabela, usar_git=False)


def _texto(saida):
    return (saida or {}).get("hookSpecificOutput", {}).get("additionalContext", "")


def test_dez_conversas_depois_do_ultimo_sono_dao_o_aviso_ao_assistente(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    _anotacao(raiz, "nota_a", "2026-01-01 — confirmada — fonte: hooks/x.py:12")
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 10)
    saida = _hook().responder(_abertura(raiz, conversas / "atual.jsonl"), {"MSS_MEMORIA_TABELA": str(tabela)})
    texto = _texto(saida)
    assert "sono" in texto and "10" in texto and "2026-01-01" in texto
    assert "adiar-sono" in texto, "o assistente precisa saber o que rodar quando o owner disser agora não"
    assert "systemMessage" not in (saida or {})


def test_nove_conversas_nao_dao_aviso(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    _anotacao(raiz, "nota_a", "2026-01-01 — confirmada — fonte: hooks/x.py:12")
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 9)
    mod = _hook()
    mod.responder(_abertura(raiz, conversas / "atual.jsonl"), {"MSS_MEMORIA_TABELA": str(tabela)})   # monta
    assert "sono" not in _texto(mod.responder(_abertura(raiz, conversas / "atual.jsonl"),
                                              {"MSS_MEMORIA_TABELA": str(tabela)}))


def test_conversa_anterior_ao_ultimo_sono_nao_conta_e_a_atual_tambem_nao(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    hoje = time.strftime("%Y-%m-%d")
    _anotacao(raiz, "nota_a", f"{hoje} — confirmada — fonte: hooks/x.py:12")
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 15, idade_dias=3)
    atual = conversas / "atual.jsonl"
    atual.write_text("{}\n", encoding="utf-8")
    assert "sono" not in _texto(_hook().responder(_abertura(raiz, atual), {"MSS_MEMORIA_TABELA": str(tabela)}))


def test_projeto_que_nunca_dormiu_conta_todas_as_conversas(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 12, idade_dias=40)
    texto = _texto(_hook().responder(_abertura(raiz, conversas / "atual.jsonl"), {"MSS_MEMORIA_TABELA": str(tabela)}))
    assert "sono" in texto and "nunca" in texto


def test_retomar_ou_compactar_nao_repete_o_aviso(tmp_path):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 12)
    for source in ("resume", "compact"):
        assert "sono" not in _texto(_hook().responder(_abertura(raiz, conversas / "atual.jsonl", source),
                                                      {"MSS_MEMORIA_TABELA": str(tabela)}))


def test_hook_nao_le_o_conteudo_das_conversas(tmp_path, monkeypatch):
    raiz, tabela = _projeto(tmp_path), tmp_path / "t.sqlite3"
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 12)
    original = Path.read_text

    def vigiado(self, *a, **k):
        if self.suffix == ".jsonl":
            raise AssertionError("o aviso conta nome e data; nunca lê a conversa")
        return original(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", vigiado)
    assert "sono" in _texto(_hook().responder(_abertura(raiz, conversas / "atual.jsonl"),
                                              {"MSS_MEMORIA_TABELA": str(tabela)}))


# ------------------------------------------------------------------ AC5 — "agora não" recomeça a conta

def test_adiar_guarda_a_data_no_controle_e_a_conta_recomeca(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _tabela_mod()
    _pronta(raiz, tabela)
    conversas = tmp_path / "conversas"
    _conversas(conversas, 12, idade_dias=2)
    hoje = time.strftime("%Y-%m-%d")
    assert mod.main(["adiar-sono", "--proj", str(raiz), "--tabela", str(tabela), "--sem-git"]) == 0
    assert mod.ultimo_sono(raiz, tabela) == hoje
    assert mod.aviso_de_sono(raiz, tabela, conversas, conversas / "atual.jsonl") is None
    mod.montar(raiz, tabela, usar_git=False)                                  # remontar não perde o adiamento
    assert mod.ultimo_sono(raiz, tabela) == hoje


# ------------------------------------------------------------------ o recall não devolve o que o sono aposentou (F-030)

def _aposenta(raiz, nome, sucessor="nota_a"):
    p = raiz / "memory" / f"{nome}.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "metadata:", f"obsoleta: 2026-11-13 — superada por [[{sucessor}]]\nmetadata:"), encoding="utf-8")


def test_recall_nao_injeta_anotacao_obsoleta(proj):
    mod = _indice()
    pedido = "a situação observável de nota_b"
    assert any("nota_b" in p.ponteiro for p in mod.casar(proj, pedido, limite=10))
    _aposenta(proj, "nota_b")
    (proj / "memory" / "indice" / "geral.md").write_text(
        "# Geral\n\n- **quando a** → [A](../nota_a.md) — a\n- **quando c** → [C](../nota_c.md) — c\n", encoding="utf-8")
    assert not any("nota_b" in p.ponteiro for p in mod.casar(proj, pedido, limite=10))


def test_obsoleta_que_ficou_no_subindice_e_acusada_e_nao_volta_pelo_recall(proj):
    mod = _indice()
    assert any("nota_b" in p.ponteiro or "— B" in p.ponteiro for p in mod.casar(proj, "nota_b", minimo=1, limite=10))
    _aposenta(proj, "nota_b")
    probs = mod.verificar(proj / "memory", sem_commit=set())
    assert any("nota_b.md" in p and "obsoleta" in p and "subíndice" in p for p in probs), probs
    assert not any("nota_b" in p.ponteiro or "— B" in p.ponteiro for p in mod.casar(proj, "nota_b", minimo=1, limite=10))


# ------------------------------------------------------------------ parte 2 (conversas) — AC8: até onde as conversas foram lidas

def _diario(raiz, nome, corpo):
    _grava(raiz, f"memory/sessions/{nome}.md", corpo)


def test_roteiro_sem_diario_de_leitura_diz_primeira_rodada_todas(proj, capsys):
    r = _indice().roteiro_do_sono(proj)
    assert r["conversas_lidas_ate"] == ("", "")
    assert _indice().main(["sono", "--proj", str(proj)]) == 0
    saida = capsys.readouterr().out
    assert "1ª rodada: todas" in saida and "conversa_texto.py" in saida and "lote --saida" in saida


def test_roteiro_mostra_a_leitura_mais_nova_e_o_comando_do_lote(proj, capsys):
    _diario(proj, "2026-11-16-sono-conversas", "# Sono\n\n- **conversas lidas até:** 2026-11-16\n")
    _diario(proj, "2026-11-20-sono-conversas", "# Sono\n\nconversas lidas até: 2026-11-20\n")
    _diario(proj, "2026-11-21-outro", "# Outro\n\nfalou de conversas lidas até ontem, sem data\n")
    r = _indice().roteiro_do_sono(proj)
    assert r["conversas_lidas_ate"] == ("2026-11-20", "memory/sessions/2026-11-20-sono-conversas.md")
    assert _indice().main(["sono", "--proj", str(proj)]) == 0
    saida = capsys.readouterr().out
    assert "conversas lidas até: 2026-11-20" in saida and "lote --desde 2026-11-20" in saida


# ------------------------------------------------------------------ parte 2 — AC9: a leitura conta como último sono

def test_leitura_mais_nova_que_a_conferencia_vira_o_ultimo_sono(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _tabela_mod()
    _anotacao(raiz, "nota_a", "2026-11-13 — confirmada — fonte: hooks/x.py:12")
    _diario(raiz, "2026-11-16-sono-conversas", "# Sono\n\nconversas lidas até: 2026-11-16\n")
    mod.montar(raiz, tabela, usar_git=False)
    assert mod.ultimo_sono(raiz, tabela) == "2026-11-16"


def test_conferencia_mais_nova_que_a_leitura_continua_valendo(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _tabela_mod()
    _anotacao(raiz, "nota_a", "2026-11-20 — confirmada — fonte: hooks/x.py:12")
    _diario(raiz, "2026-11-16-sono-conversas", "# Sono\n\nconversas lidas até: 2026-11-16\n")
    mod.montar(raiz, tabela, usar_git=False)
    assert mod.ultimo_sono(raiz, tabela) == "2026-11-20"


# ------------------------------------------------------------------ parte 2 — AC10: fonte nunca aponta pro `.jsonl`

def test_fonte_que_cita_jsonl_da_conversa_e_acusada_pelo_nome(proj):
    _anotacao(proj, "nota_c", "2026-11-16 — confirmada — fonte: C:/Users/x/.claude/projects/p/abc.jsonl:120")
    probs = _conferida_probs(_indice(), proj)
    assert len(probs) == 1 and "nota_c.md" in probs[0] and ".jsonl" in probs[0]
    _anotacao(proj, "nota_c", "2026-11-16 — confirmada — fonte: memory/sessions/2026-11-16-sono-conversas.md:12")
    assert _conferida_probs(_indice(), proj) == []


def test_rebaixada_com_fonte_no_diario_passa(proj):
    _anotacao(proj, "nota_c", "2026-11-16 — não confirmada — fonte: memory/sessions/2026-10-02-x.md:12",
              corpo="corpo\n\nrebaixada: a conversa mostrou que o aviso não disparou "
                    "(memory/sessions/2026-10-02-x.md:12, 2026-10-02)\n")
    assert _conferida_probs(_indice(), proj) == []


# ------------------------------------------------------------------ AC6 — o acervo do kit depois da passada

def test_kit_sem_citacao_morta():
    assert _indice().citacoes_mortas(REPO) == []


def test_citacao_fora_do_repositorio_nao_e_conferida(tmp_path):
    """CI de 2026-11-17: `~/.claude/settings.json` (a pasta pessoal de quem roda) e `docs/anatomia.html` (gerado,
    no `.gitignore`) não existem num clone e não são citação morta. O caminho do repositório continua conferido."""
    (tmp_path / "memory").mkdir()
    (tmp_path / ".gitignore").write_text("# gerado\n/docs/relatorio-gerado-fora-do-git.html\n", encoding="utf-8")
    (tmp_path / "memory" / "nota.md").write_text(
        "Veja `~/.claude/arquivo-da-casa-que-nao-existe.json`, `docs/relatorio-gerado-fora-do-git.html` e "
        "`docs/arquivo-que-sumiu-de-verdade.md`.\n",
        encoding="utf-8")
    mortas = [c for _, c in _indice().citacoes_mortas(tmp_path, pastas=("memory",))]
    assert mortas == ["docs/arquivo-que-sumiu-de-verdade.md"]


def test_acervo_do_kit_foi_conferido_no_formato():
    """As 78 anotações da passada de 2026-11-13 têm `conferida:` válido; anotação gravada depois pode nascer sem ele
    (a captura não carimba — entra no próximo sono)."""
    mod = _indice()
    r = mod.roteiro_do_sono(REPO)
    conferidas = sum(n for e, n in r["por_estado"].items() if e != mod.NUNCA)
    assert conferidas >= 78, f"só {conferidas} anotações conferidas; nunca conferidas: {r['nunca']}"
    assert [p for p in mod.verificar(REPO / "memory") if "conferida" in p] == []


# ------------------------------------------------------------------ fecho: a suíte só quando a rodada muda código

def test_fecho_do_sono_so_roda_a_suite_quando_a_rodada_muda_codigo():
    """A 1ª rodada da parte 2 levou 1:50:48 de suíte sem mudar código (owner, 2026-11-16): diff só em `memory/**`
    e `docs/decisoes.md` fecha com `verificar` e `citacoes` limpos; qualquer outro arquivo → suíte inteira."""
    texto = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    fecho = texto[texto.index("8. **Feche:**"):texto.index("### Parte 2")]
    assert "`memory/**`" in fecho and "`docs/decisoes.md`" in fecho, fecho
    assert "sem a suíte" in fecho and "suíte inteira" in fecho, fecho
    assert "a suíte do projeto verde" not in fecho, "o fecho ainda cobra a suíte em toda rodada"
