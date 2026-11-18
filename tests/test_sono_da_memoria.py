"""Sono da memória — parte 1, o acervo (docs/specs/sono-da-memoria.md, 0.62.0).

Por que existe: nota errada vira armadilha (`docs/analise/2026-11-13-sono-da-memoria.md`) e ninguém relia o acervo —
40 citações mortas e 0 de 78 anotações conferidas em 2026-11-13. Decisões do owner (2026-11-13): o estado vai no
frontmatter (`conferida: <data> — <estado> — fonte: <arquivo:linha>`), a tabela de memória ganha a coluna copiada
desse campo, e o hook de abertura avisa com 10 conversas sem sono, guardando a data do último sono na linha de
controle da tabela — sem hook novo.

Camadas (2026-11-18, `docs/decisoes.md`): aqui fica o lado do `templates/memoria_indice.py` (o formato do campo, o
roteiro do sono, o recall sem a obsoleta), com o projeto num dicionário {caminho: bytes} (`Disco`). O lado da tabela
(a coluna de estado, o último sono na linha de controle, a conta das conversas, o "agora não") está em
`tests/test_memoria_tabela.py`; o do hook de abertura, em `tests/test_hook_memoria_tabela_em_dia.py`. O disco de
verdade e o processo do `memoria_indice` ficam em `tests/test_memoria_indice.py`. Os dois testes do acervo do kit
leem o repositório como ele está (só leitura).
"""
import importlib.util
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_indice.py"
RAIZ = REPO.parent / "projeto-que-nao-existe-sono"          # absoluto, nunca criado
MEM = RAIZ / "memory"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m          # dataclasses resolvem anotações via sys.modules
    spec.loader.exec_module(m)
    return m


class Disco:
    """O projeto em memória, com os métodos do `DiscoReal` do `memoria_indice`: {caminho: bytes}, pasta = prefixo de
    algum arquivo, glob de um nível só (`*.md`), e sem git (devolve None, como pasta fora de repositório)."""

    def __init__(self):
        self.dados = {}

    def gravar(self, p, texto):
        self.dados[Path(p)] = texto.encode("utf-8") if isinstance(texto, str) else texto

    def ler_bytes(self, p):
        try:
            return self.dados[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def ler_texto(self, p):
        return self.ler_bytes(p).decode("utf-8", "replace").replace("\r\n", "\n")

    def gravar_bytes(self, p, dados):
        self.dados[Path(p)] = dados

    def eh_arquivo(self, p):
        return Path(p) in self.dados

    def eh_pasta(self, p):
        return any(Path(p) in a.parents for a in self.dados)

    def existe(self, p):
        return self.eh_arquivo(p) or self.eh_pasta(p)

    def glob(self, base, padrao):
        return [a for a in self.dados if a.parent == Path(base) and fnmatch(a.name, padrao)]

    def nomes(self, raiz):
        raiz = Path(raiz)
        return {p.name for a in self.dados if raiz in a.parents for p in [a, *a.parents] if raiz in p.parents}

    def git(self, pasta, *args):
        return None


def _anotacao(disco, nome, conferida=None, corpo="corpo\n"):
    linha = f"conferida: {conferida}\n" if conferida is not None else ""
    disco.gravar(MEM / f"{nome}.md",
                 f"---\nname: {nome}\ndescription: descrição longa o bastante de {nome}\n"
                 f"gatilho: quando acontecer a situação observável de {nome}\n{linha}metadata:\n  type: project\n---\n\n{corpo}")


@pytest.fixture()
def proj():
    d = Disco()
    d.gravar(MEM / "MEMORY.md",
             "# Memória\n\n- **Geral** → [subíndice](indice/geral.md) — 3 memórias · quando: qualquer coisa\n")
    d.gravar(MEM / "indice" / "geral.md",
             "# Geral\n\n- **quando a** → [A](../nota_a.md) — a\n- **quando b** → [B](../nota_b.md) — b\n"
             "- **quando c** → [C](../nota_c.md) — c\n")
    _anotacao(d, "nota_a", "2026-11-13 — confirmada — fonte: hooks/x.py:12")
    _anotacao(d, "nota_b", "2026-11-10 — não confirmada — fonte: nenhuma achada")
    _anotacao(d, "nota_c")
    return d


def _conferida_probs(mod, disco):
    return [p for p in mod.verificar(MEM, sem_commit=set(), disco=disco) if "conferida" in p]


def _sono_em_memoria(mod, disco, monkeypatch):
    """A linha de comando `sono` lendo o projeto em memória: a leitura do roteiro é trocada (a CLI só imprime)."""
    original = mod.roteiro_do_sono
    monkeypatch.setattr(mod, "roteiro_do_sono", lambda proj: original(proj, disco=disco))


# ------------------------------------------------------------------ AC1 — formato do campo no `verificar`

def test_conferida_no_formato_e_sem_o_campo_passam(mod, proj):
    assert _conferida_probs(mod, proj) == []


@pytest.mark.parametrize("valor", [
    "13/11/2026 — confirmada — fonte: hooks/x.py:12",          # data fora do formato
    "2026-11-13 — certa — fonte: hooks/x.py:12",               # estado que não existe
    "2026-11-13 — confirmada",                                  # sem fonte
    "2026-11-13 — confirmada — fonte: hooks/x.py",              # confirmada sem arquivo:linha
])
def test_conferida_fora_do_formato_e_acusada_pelo_nome(mod, proj, valor):
    _anotacao(proj, "nota_c", valor)
    probs = _conferida_probs(mod, proj)
    assert len(probs) == 1 and "nota_c.md" in probs[0]


def test_conflito_sem_a_linha_conflito_no_corpo_e_acusado(mod, proj):
    _anotacao(proj, "nota_c", "2026-11-13 — conflito — fonte: docs/decisoes.md:25")
    assert len(_conferida_probs(mod, proj)) == 1
    _anotacao(proj, "nota_c", "2026-11-13 — conflito — fonte: docs/decisoes.md:25",
              corpo="CONFLITO: docs/decisoes.md:25 (2026-07-30) diz A; docs/decisoes.md:34 (2026-09-23) diz B\n")
    assert _conferida_probs(mod, proj) == []


def test_ler_conferida_devolve_data_estado_e_fonte(mod):
    assert mod.ler_conferida("2026-11-13 — não confirmada — fonte: nenhuma achada") == \
        ("2026-11-13", "não confirmada", "nenhuma achada")
    assert mod.ler_conferida("qualquer coisa") is None


# ------------------------------------------------------------------ AC2 — o roteiro do sono

def test_roteiro_do_sono_conta_por_estado_e_lista_as_nunca_conferidas(mod, proj):
    r = mod.roteiro_do_sono(RAIZ, disco=proj)
    assert r["por_estado"] == {"confirmada": 1, "não confirmada": 1, "conflito": 0, "nunca conferida": 1}
    assert r["nunca"] == ["nota_c.md"]
    assert r["ultimo_sono"] == "2026-11-13"
    assert "citacoes" in r and "duplicatas" in r


def _aposenta(disco, nome, sucessor="nota_a"):
    p = MEM / f"{nome}.md"
    disco.gravar(p, disco.ler_texto(p).replace(
        "metadata:", f"obsoleta: 2026-11-13 — superada por [[{sucessor}]]\nmetadata:"))


def test_obsoleta_fica_fora_do_roteiro(mod, proj):
    _aposenta(proj, "nota_c")
    r = mod.roteiro_do_sono(RAIZ, disco=proj)
    assert r["nunca"] == [] and r["por_estado"]["nunca conferida"] == 0


def test_cli_sono_imprime_o_roteiro(mod, proj, monkeypatch, capsys):
    _sono_em_memoria(mod, proj, monkeypatch)
    assert mod.main(["sono", "--proj", str(RAIZ)]) == 0
    saida = capsys.readouterr().out
    assert "nunca conferida" in saida and "nota_c.md" in saida and "2026-11-13" in saida


# ------------------------------------------------------------------ o recall não devolve o que o sono aposentou (F-030)

def test_recall_nao_injeta_anotacao_obsoleta(mod, proj):
    pedido = "a situação observável de nota_b"
    assert any("nota_b" in p.ponteiro for p in mod.casar(RAIZ, pedido, limite=10, disco=proj))
    _aposenta(proj, "nota_b")
    proj.gravar(MEM / "indice" / "geral.md",
                "# Geral\n\n- **quando a** → [A](../nota_a.md) — a\n- **quando c** → [C](../nota_c.md) — c\n")
    assert not any("nota_b" in p.ponteiro for p in mod.casar(RAIZ, pedido, limite=10, disco=proj))


def test_obsoleta_que_ficou_no_subindice_e_acusada_e_nao_volta_pelo_recall(mod, proj):
    def achou_b():
        return any("nota_b" in p.ponteiro or "— B" in p.ponteiro
                   for p in mod.casar(RAIZ, "nota_b", minimo=1, limite=10, disco=proj))
    assert achou_b()
    _aposenta(proj, "nota_b")
    probs = mod.verificar(MEM, sem_commit=set(), disco=proj)
    assert any("nota_b.md" in p and "obsoleta" in p and "subíndice" in p for p in probs), probs
    assert not achou_b()


# ------------------------------------------------------------------ parte 2 (conversas) — AC8: até onde as conversas foram lidas

def _diario(disco, nome, corpo):
    disco.gravar(MEM / "sessions" / f"{nome}.md", corpo)


def test_roteiro_sem_diario_de_leitura_diz_primeira_rodada_todas(mod, proj, monkeypatch, capsys):
    assert mod.roteiro_do_sono(RAIZ, disco=proj)["conversas_lidas_ate"] == ("", "")
    _sono_em_memoria(mod, proj, monkeypatch)
    assert mod.main(["sono", "--proj", str(RAIZ)]) == 0
    saida = capsys.readouterr().out
    assert "1ª rodada: todas" in saida and "conversa_texto.py" in saida and "lote --saida" in saida


def test_roteiro_mostra_a_leitura_mais_nova_e_o_comando_do_lote(mod, proj, monkeypatch, capsys):
    _diario(proj, "2026-11-16-sono-conversas", "# Sono\n\n- **conversas lidas até:** 2026-11-16\n")
    _diario(proj, "2026-11-20-sono-conversas", "# Sono\n\nconversas lidas até: 2026-11-20\n")
    _diario(proj, "2026-11-21-outro", "# Outro\n\nfalou de conversas lidas até ontem, sem data\n")
    r = mod.roteiro_do_sono(RAIZ, disco=proj)
    assert r["conversas_lidas_ate"] == ("2026-11-20", "memory/sessions/2026-11-20-sono-conversas.md")
    _sono_em_memoria(mod, proj, monkeypatch)
    assert mod.main(["sono", "--proj", str(RAIZ)]) == 0
    saida = capsys.readouterr().out
    assert "conversas lidas até: 2026-11-20" in saida and "lote --desde 2026-11-20" in saida


# ------------------------------------------------------------------ parte 2 — AC10: fonte nunca aponta pro `.jsonl`

def test_fonte_que_cita_jsonl_da_conversa_e_acusada_pelo_nome(mod, proj):
    _anotacao(proj, "nota_c", "2026-11-16 — confirmada — fonte: C:/Users/x/.claude/projects/p/abc.jsonl:120")
    probs = _conferida_probs(mod, proj)
    assert len(probs) == 1 and "nota_c.md" in probs[0] and ".jsonl" in probs[0]
    _anotacao(proj, "nota_c", "2026-11-16 — confirmada — fonte: memory/sessions/2026-11-16-sono-conversas.md:12")
    assert _conferida_probs(mod, proj) == []


def test_rebaixada_com_fonte_no_diario_passa(mod, proj):
    _anotacao(proj, "nota_c", "2026-11-16 — não confirmada — fonte: memory/sessions/2026-10-02-x.md:12",
              corpo="corpo\n\nrebaixada: a conversa mostrou que o aviso não disparou "
                    "(memory/sessions/2026-10-02-x.md:12, 2026-10-02)\n")
    assert _conferida_probs(mod, proj) == []


# ------------------------------------------------------------------ AC6 — citação fora do repositório

def test_citacao_fora_do_repositorio_nao_e_conferida(mod):
    """CI de 2026-11-17: `~/.claude/settings.json` (a pasta pessoal de quem roda) e `docs/anatomia.html` (gerado,
    no `.gitignore`) não existem num clone e não são citação morta. O caminho do repositório continua conferido."""
    d = Disco()
    d.gravar(RAIZ / ".gitignore", "# gerado\n/docs/relatorio-gerado-fora-do-git.html\n")
    d.gravar(MEM / "nota.md",
             "Veja `~/.claude/arquivo-da-casa-que-nao-existe.json`, `docs/relatorio-gerado-fora-do-git.html`, o nome "
             "solto `relatorio-gerado-fora-do-git.html` e `docs/arquivo-que-sumiu-de-verdade.md`.\n")
    mortas = [c for _, c in mod.citacoes_mortas(RAIZ, pastas=("memory",), disco=d)]
    assert mortas == ["docs/arquivo-que-sumiu-de-verdade.md"]


# ------------------------------------------------------------------ AC6 — o acervo do kit depois da passada (só leitura)

def test_kit_sem_citacao_morta(mod):
    assert mod.citacoes_mortas(REPO) == []


def test_acervo_do_kit_foi_conferido_no_formato(mod):
    """As 78 anotações da passada de 2026-11-13 têm `conferida:` válido; anotação gravada depois pode nascer sem ele
    (a captura não carimba — entra no próximo sono). `sem_commit` vazio: o git não muda o que este teste olha."""
    r = mod.roteiro_do_sono(REPO)
    conferidas = sum(n for e, n in r["por_estado"].items() if e != mod.NUNCA)
    assert conferidas >= 78, f"só {conferidas} anotações conferidas; nunca conferidas: {r['nunca']}"
    assert [p for p in mod.verificar(REPO / "memory", sem_commit=set()) if "conferida" in p] == []


# ------------------------------------------------------------------ fecho: a suíte só quando a rodada muda código

def test_fecho_do_sono_so_roda_a_suite_quando_a_rodada_muda_codigo():
    """A 1ª rodada da parte 2 levou 1:50:48 de suíte sem mudar código (owner, 2026-11-16): diff só em `memory/**`
    e `docs/decisoes.md` fecha com `verificar` e `citacoes` limpos; qualquer outro arquivo → suíte inteira."""
    texto = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    fecho = texto[texto.index("8. **Feche:**"):texto.index("### Parte 2")]
    assert "`memory/**`" in fecho and "`docs/decisoes.md`" in fecho, fecho
    assert "sem a suíte" in fecho and "suíte inteira" in fecho, fecho
    assert "a suíte do projeto verde" not in fecho, "o fecho ainda cobra a suíte em toda rodada"
