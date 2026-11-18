"""memoria_indice.py — índice de memória em dois níveis (topo por família + memory/indice/).

Por que existe: o índice plano do Whats chegou a 25.421 bytes (~6.355 tokens em TODA janela) e o kit
mandou PODAR — contra a própria decisão "mover, nunca apagar". O topo passa a ter 1 linha por família
(teto 6 KB) e as memórias vivem em subíndices lidos só quando a família bate.

Camadas (2026-11-18, `docs/decisoes.md`): o script lê e grava por um objeto de disco; aqui ele é um dicionário
{caminho: bytes} (`Disco`, sem git), e a linha de comando lê o mesmo dicionário com a leitura trocada por
`monkeypatch`. O disco e o git de verdade (gravar o `dividir` com CRLF, a anotação nova sem commit, o kit nas
citações) ficam num teste só, numa pasta montada uma vez; o processo python, num teste só. O teste do acervo do kit
lê o repositório como ele está (só leitura).
"""
import importlib.util
import re
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_indice.py"
FIXTURE = REPO / "tests" / "fixtures" / "memoria_whats_2026-09-14" / "MEMORY.md"
WHATS = FIXTURE.read_text(encoding="utf-8")                  # o índice REAL do Whats, lido uma vez
RAIZ = REPO.parent / "projeto-que-nao-existe-indice"         # absoluto, nunca criado
MEM = RAIZ / "memory"

FRONT_COM_GATILHO = "---\nname: {name}\ndescription: {desc}\ngatilho: quando {gat}\nmetadata:\n  type: project\n---\n\ncorpo\n"
FRONT_SEM_GATILHO = "---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: project\n---\n\ncorpo\n"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m          # dataclasses (3.14) resolve anotações via sys.modules
    spec.loader.exec_module(m)
    return m


class Disco:
    """O projeto em memória, com os métodos do `DiscoReal`: {caminho: bytes}, pasta = prefixo de algum arquivo, glob
    de um nível só (`*.md`), e sem git (devolve None, como pasta fora de repositório)."""

    def __init__(self):
        self.dados = {}

    def gravar(self, p, texto):
        self.dados[Path(p)] = texto.encode("utf-8") if isinstance(texto, str) else texto

    def apagar_pasta(self, pasta):
        for p in [p for p in self.dados if Path(pasta) in p.parents]:
            del self.dados[p]

    def ler(self, p):
        return self.ler_bytes(p).decode("utf-8")

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


def _projeto_whats(com_gatilho=("app-setting-faltando-cai-no-default.md", "chatwoot-deduplica-contato-por-telefone.md")):
    """Projeto sintético: o índice REAL do Whats + um stub por arquivo apontado (2 com gatilho)."""
    d = Disco()
    d.gravar(MEM / "MEMORY.md", WHATS)
    for arq in re.findall(r"\]\(([^)/]+\.md)\)", WHATS):
        if arq == "<arquivo>.md":
            continue
        molde = FRONT_COM_GATILHO if arq in com_gatilho else FRONT_SEM_GATILHO
        d.gravar(MEM / arq, molde.format(name=arq[:-3], desc=f"desc de {arq}",
                                         gat=f"a situação de {arq[:-3].replace('-', ' ')}"))
    return d


# --- parse ---------------------------------------------------------------------------

def test_le_5_familias_e_93_itens_do_indice_do_whats(mod):
    fams = mod.ler_indice_plano(WHATS)
    assert [f.titulo for f in fams] == ["Como trabalhar neste projeto", "Ambiente e build", "Integrações",
                                        "Padrões e ferramentas", "Como eu devo trabalhar (correções do owner)"]
    assert sum(len(f.itens) for f in fams) == 93
    assert fams[1].itens[0].titulo == "Build quebra por CA desatualizada"
    assert fams[1].itens[0].arquivo == "build-quebra-por-ca-desatualizada.md"


def test_slug_sem_acento_sem_parenteses(mod):
    assert mod.slug("Como eu devo trabalhar (correções do owner)") == "como-eu-devo-trabalhar"
    assert mod.slug("Integrações") == "integracoes"


def test_relink_so_muda_link_local(mod):
    assert mod.relink("- [T](arquivo.md) — g") == "- [T](../arquivo.md) — g"
    assert mod.relink("- **quando x** → [T](arquivo.md) — veja [[outra]] e https://a.b/c.md") == \
        "- **quando x** → [T](../arquivo.md) — veja [[outra]] e https://a.b/c.md"
    assert mod.relink("- [T](../arquivo.md) — g") == "- [T](../arquivo.md) — g"


# --- dividir ---------------------------------------------------------------------------

def test_dividir_dry_run_nao_escreve_nada(mod):
    d = _projeto_whats()
    antes = dict(d.dados)
    rel = mod.dividir(MEM, aplicar=False, disco=d)
    assert rel.ok, rel.problemas
    assert d.dados == antes
    assert len(rel.familias) == 5 and rel.bytes_topo < 6000


def test_dividir_aplicar_conserva_toda_linha_byte_a_byte(mod):
    d = _projeto_whats()
    linhas_antes = [l for l in WHATS.splitlines() if l.startswith("- [")]
    rel = mod.dividir(MEM, aplicar=True, disco=d)
    assert rel.ok, rel.problemas
    subs = sorted(d.glob(MEM / "indice", "*.md"))
    assert [p.name for p in subs] == ["ambiente-e-build.md", "como-eu-devo-trabalhar.md",
                                      "como-trabalhar-neste-projeto.md", "integracoes.md", "padroes-e-ferramentas.md"]
    linhas_depois = [l for p in subs for l in d.ler(p).splitlines() if l.startswith("- ")]
    assert len(linhas_depois) == len(linhas_antes) == 93
    assert sorted(linhas_depois) == sorted(mod.relink(l) for l in linhas_antes)
    topo = d.ler(MEM / "MEMORY.md")
    assert "<!-- MODELO" not in topo, "o comentário-modelo não é memória: sai do topo"
    assert topo.count("→ [subíndice](indice/") == 5
    assert "— 22 memórias" in topo  # Ambiente e build


def test_topo_usa_frases_do_gatilho_e_nao_palavras_raspadas(mod):
    d = _projeto_whats()
    mod.dividir(MEM, aplicar=True, disco=d)
    topo = d.ler(MEM / "MEMORY.md")
    linha_amb = next(l for l in topo.splitlines() if "indice/ambiente-e-build.md" in l)
    assert "a situação de app setting faltando cai no default" in linha_amb
    linha_padroes = next(l for l in topo.splitlines() if "indice/padroes-e-ferramentas.md" in l)
    assert "quando:" not in linha_padroes, "família sem nenhum gatilho: sai só com título e N"
    for lixo in ("Esta", ".md ·", "GET"):
        assert lixo not in topo


def test_dividir_recusa_quando_ponteiro_quebrado(mod):
    d = _projeto_whats()
    del d.dados[MEM / "build-quebra-por-ca-desatualizada.md"]
    rel = mod.dividir(MEM, aplicar=True, disco=d)
    assert not rel.ok
    assert any("build-quebra-por-ca-desatualizada.md" in p for p in rel.problemas)
    assert not d.eh_pasta(MEM / "indice"), "conservação falhou: NADA se grava"


def test_dividir_recusa_linha_solta_dentro_de_secao(mod):
    """Linha que não é item nem vazia dentro de uma seção seria perdida em silêncio: o script recusa."""
    d = _projeto_whats()
    d.gravar(MEM / "MEMORY.md", WHATS.replace("## Integrações\n", "## Integrações\nNota solta que não é item.\n"))
    rel = mod.dividir(MEM, aplicar=True, disco=d)
    assert not rel.ok and any("linha solta" in x and "Integrações" in x for x in rel.problemas)
    assert not d.eh_pasta(MEM / "indice")


def test_dividir_preserva_crlf(mod):
    d = _projeto_whats()
    d.gravar(MEM / "MEMORY.md", WHATS.replace("\n", "\r\n").encode("utf-8"))
    mod.dividir(MEM, aplicar=True, disco=d)
    assert b"\r\n" in d.ler_bytes(MEM / "MEMORY.md")
    assert b"\r\n" in d.ler_bytes(MEM / "indice" / "integracoes.md")


# --- verificar / fila ------------------------------------------------------------------

def _dividido(mod):
    d = _projeto_whats()
    assert mod.dividir(MEM, aplicar=True, disco=d).ok
    return d


def test_verificar_limpo_depois_de_dividir(mod):
    assert mod.verificar(MEM, disco=_dividido(mod)) == []


def test_verificar_acusa_memoria_sem_linha_e_ponteiro_quebrado(mod):
    d = _dividido(mod)
    d.gravar(MEM / "nova-memoria.md", FRONT_SEM_GATILHO.format(name="nova-memoria", desc="x"))
    del d.dados[MEM / "crm-www4-dois-nomes.md"]
    probs = mod.verificar(MEM, disco=d)
    assert any("nova-memoria.md" in p and "sem linha" in p for p in probs)
    assert any("crm-www4-dois-nomes.md" in p and "quebrado" in p for p in probs)


def test_verificar_ignora_obsoleta(mod):
    d = _dividido(mod)
    d.gravar(MEM / "velha.md", "---\nname: velha\ndescription: x\nobsoleta: 2026-09-01 — superada por [[nova]]\n---\n")
    assert mod.verificar(MEM, disco=d) == []


def test_verificar_corrige_n_do_topo_com_aplicar(mod):
    d = _dividido(mod)
    sub = MEM / "indice" / "integracoes.md"
    d.gravar(sub, d.ler(sub) + "- [Extra](../crm-www4-dois-nomes.md) — dup de teste\n")
    probs = mod.verificar(MEM, disco=d)
    assert any("N do topo" in p and "integracoes" in p for p in probs)
    assert any("mais de uma linha" in p for p in probs)
    mod.verificar(MEM, aplicar=True, disco=d)
    assert "— 27 memórias" in d.ler(MEM / "MEMORY.md")


def test_verificar_acusa_topo_acima_do_teto(mod):
    d = _dividido(mod)
    d.gravar(MEM / "MEMORY.md", d.ler(MEM / "MEMORY.md") + "x" * 6000)
    assert any("teto" in pr for pr in mod.verificar(MEM, disco=d))


# --- qualidade do que foi gravado (benchmark MSIG_Agentes 2026-11-06, itens 7, 8 e 9) ------------------

def _mem(d, nome, desc, gatilho=None, corpo="corpo\n", name=None, mem=MEM):
    fm = f"---\nname: {name or nome[:-3]}\ndescription: {desc}\n"
    if gatilho:
        fm += f"gatilho: {gatilho}\n"
    fm += "metadata:\n  type: project\n---\n\n"
    d.gravar(mem / nome, fm + corpo)


def test_gatilho_fraco_curto_ou_generico_e_bom_passa(mod):
    """Item 7: lá o `agente-criar` recusa `quando_usar` curto/genérico porque é por ele que o roteador escolhe;
    aqui o gatilho é o roteamento do recall. Curto (< 15 chars sem o 'quando') ou com < 2 palavras úteis → fraco."""
    assert mod.gatilho_fraco("quando precisar")                       # 8 chars
    assert mod.gatilho_fraco("sempre que for necessário fazer isso")  # só stopwords/curtas → 0-1 útil
    assert mod.gatilho_fraco("quando bumpar a versão do kit") == ""
    assert mod.gatilho_fraco("quando gerar HTML com JS inline") == ""
    assert mod.gatilho_fraco("quando editar HTML, CSS ou JS de aplicação") == ""


def test_verificar_acusa_gatilho_fraco_e_ignora_obsoleta(mod):
    d = _dividido(mod)
    _mem(d, "app-setting-faltando-cai-no-default.md", "desc", gatilho="quando precisar")
    d.gravar(MEM / "chatwoot-deduplica-contato-por-telefone.md",
             "---\nname: chatwoot\ndescription: desc\ngatilho: quando x\nobsoleta: 2026-11-06 — superada\n---\n")
    fracos = [p for p in mod.verificar(MEM, disco=d) if p.startswith("gatilho fraco")]
    assert len(fracos) == 1 and "app-setting-faltando-cai-no-default.md" in fracos[0] and "recall nunca vai casar" in fracos[0]


def test_verificar_acusa_duplicata_por_name_e_por_descricao(mod):
    """Item 8: lá o `gravar` avisa 'mesma tag, título diferente' (a duplicata que mais aconteceu). Aqui: mesmo
    `name:` em dois arquivos, ou descrições com ≥ 80% das palavras em comum."""
    d = _dividido(mod)
    _mem(d, "app-setting-faltando-cai-no-default.md",
         "App Setting ausente no Azure cai no valor default do settings sem avisar", gatilho="quando faltar App Setting")
    _mem(d, "chatwoot-deduplica-contato-por-telefone.md",
         "App Setting ausente no Azure cai no valor default do settings sem avisar ninguém",
         gatilho="quando faltar App Setting no Azure", name="app-setting-faltando-cai-no-default")
    probs = mod.verificar(MEM, disco=d)
    dups = [p for p in probs if p.startswith("possível duplicata")]
    assert any("mesmo `name:" in p for p in dups), probs
    assert any("descrições quase iguais" in p for p in dups), probs
    assert all("obsoleta" in p for p in dups)


def test_verificar_sem_falso_positivo_nas_memorias_do_kit(mod):
    """As 69+ memórias deste repo são o corpus real: nenhuma tem gatilho fraco nem duplicata. Só leitura;
    `sem_commit` vazio porque o git não muda o que este teste olha."""
    probs = mod.verificar(REPO / "memory", sem_commit=set())
    assert not [p for p in probs if p.startswith(("gatilho fraco", "possível duplicata"))], probs


def test_citacoes_mortas_lista_so_o_que_nao_existe(mod):
    """Item 9: lá o `doctor` lista script citado no KB que não existe em nenhum `tools/` do kit (código que ficou
    só na máquina de alguém). Aqui: caminho em crase, fora de bloco de código, que não existe no projeto nem no
    kit. Placeholder, exemplo de uma letra, molde do kit e memória obsoleta ficam de fora."""
    d = Disco()
    d.gravar(RAIZ / "app" / "main.py", "x")
    d.gravar(mod.KIT / "hooks" / "regras_do_kit.py", "x")           # o kit, como o dicionário o vê
    d.gravar(mod.KIT / "templates" / "ARQUITETURA.md", "x")         # molde do kit
    _mem(d, "viva.md", "d", gatilho="quando rodar o serviço local", corpo=(
        "cite `app/main.py:12` (existe) e `app/sumiu.py` (não) e `NOTAS-ANTIGAS.md` (nome solto, não existe)\n"
        "placeholder `<arquivo>.py`, `${X}/a.py`, exemplo `x.sql`, molde `docs/ARQUITETURA.md`\n"
        "```\n`dentro/de/cerca.py`\n```\n"))
    d.gravar(MEM / "velha.md", "---\nname: velha\ndescription: d\nobsoleta: 2026-11-06 — superada\n---\n`tambem/sumiu.py`\n")
    d.gravar(RAIZ / "docs" / "specs" / "s.md", "# s\n`hooks/regras_do_kit.py` (do kit, existe) · `docs/nada.md`\n")
    mortas = mod.citacoes_mortas(RAIZ, disco=d)
    assert sorted(c for _, c in mortas) == ["NOTAS-ANTIGAS.md", "app/sumiu.py", "docs/nada.md"], mortas
    # frontmatter de 7 linhas + 1 em branco: o corpo começa na linha 9 (com gatilho)
    assert ("memory/viva.md:9", "app/sumiu.py") in mortas and ("docs/specs/s.md:2", "docs/nada.md") in mortas


def test_citacoes_cli_lista_e_sai_1(mod, monkeypatch, capsys):
    d = Disco()
    _mem(d, "m.md", "d", corpo="`nao/existe.py`\n")
    original = mod.citacoes_mortas
    monkeypatch.setattr(mod, "citacoes_mortas", lambda proj: original(proj, disco=d))
    assert mod.main(["citacoes", "--proj", str(RAIZ)]) == 1
    saida = capsys.readouterr().out
    assert "citações mortas (1)" in saida and "memory/m.md:8: `nao/existe.py`" in saida and "obsoleta:" in saida
    d.gravar(MEM / "m.md", "---\nname: m\ndescription: d\n---\nsem citação\n")
    assert mod.main(["citacoes", "--proj", str(RAIZ)]) == 0


# --- procedimento (benchmark MSIG_Agentes 2026-11-06, item 1) -------------------------------------------

PROC_OK = ("**Passos:**\n"
           "1. conferir a planilha — quem: assistente — como: `tools/ler_planilha.py` — para se: houver linha sem apólice\n"
           "2. gerar os `.sql` — quem: assistente — como: `tools/gerar_cancelamento.py`\n"
           "3. executar em homologação — quem: owner — como: SSMS\n"
           "**Ferramentas:** `tools/gerar_cancelamento.py`\n"
           "**Saída:** um `.sql` por lote em `Scripts/`, pro owner executar\n")


def _proc(d, nome="cancelar-apolices-da-planilha.md", corpo=PROC_OK,
          gatilho="quando pedirem para cancelar apólices de uma planilha"):
    fm = f"---\nname: {nome[:-3]}\ndescription: cancelamento em lote a partir de planilha\n"
    if gatilho:
        fm += f"gatilho: {gatilho}\n"
    fm += "metadata:\n  type: procedimento\n---\n\n"
    d.gravar(MEM / nome, fm + corpo)


def test_frontmatter_le_type_aninhado_em_metadata(mod):
    d = Disco()
    d.gravar(MEM / "m.md", "---\nname: m\nmetadata:\n  type: procedimento\n---\ncorpo\n")
    assert mod.frontmatter(MEM / "m.md", d)["type"] == "procedimento"
    assert mod.corpo(MEM / "m.md", d) == "\ncorpo\n"


def test_validar_procedimento_formato(mod):
    """Lá o `gravar --procedimento` recusa se faltar Gatilho/Passos/Ferramentas/Saída. Aqui o gatilho é o do
    frontmatter; o corpo precisa das 3 marcas e de ≥ 2 passos numerados."""
    assert mod.validar_procedimento(PROC_OK) == []
    erros = mod.validar_procedimento("**Passos:**\n1. só um passo\n**Saída:** x\n")
    assert any("Ferramentas" in e for e in erros) and any("menos de 2 passos" in e for e in erros)
    assert mod.validar_procedimento("texto solto sem nada") and len(mod.validar_procedimento("texto solto sem nada")) == 3


def test_verificar_acusa_procedimento_fora_do_formato_e_sem_gatilho(mod):
    d = _dividido(mod)
    _proc(d, "app-setting-faltando-cai-no-default.md", corpo="**Passos:**\n1. um\n", gatilho=None)
    probs = mod.verificar(MEM, disco=d)
    assert any(p.startswith("procedimento sem `gatilho:`") for p in probs), probs
    assert any(p.startswith("procedimento fora do formato") and "Ferramentas" in p for p in probs), probs
    _proc(d, "app-setting-faltando-cai-no-default.md")
    assert not [p for p in mod.verificar(MEM, disco=d) if p.startswith("procedimento")]


def test_recall_aponta_procedimento_com_prefixo_prioridade_e_instrucao(mod):
    """O ponteiro vem com `PROCEDIMENTO`, ganha o desempate sobre memória comum, e a injeção traz a instrução
    de ler inteiro e seguir 'passo k/N' — sem passar do teto de 600 bytes."""
    d = Disco()
    d.gravar(MEM / "MEMORY.md", "# topo\n")
    _proc(d)
    _mem(d, "planilha-de-apolices-tem-zero-a-esquerda.md",
         "cancelar apólices de uma planilha: o número vem com zero à esquerda",
         gatilho="quando ler apólices de uma planilha para cancelar")
    ponteiros = mod.casar(RAIZ, "cancelar as apólices da planilha que a Luciana mandou", limite=3, disco=d)
    assert ponteiros and ponteiros[0].ponteiro.startswith("PROCEDIMENTO memory/cancelar-apolices-da-planilha.md"), ponteiros
    texto = mod.formatar_injecao(ponteiros)
    assert "PROCEDIMENTO memory/cancelar-apolices-da-planilha.md" in texto
    assert "passo k/N" in texto and "feitos × pendentes" in texto
    assert len(texto.encode("utf-8")) <= 600
    # sem procedimento entre os ponteiros, a instrução não aparece
    assert "passo k/N" not in mod.formatar_injecao([mod.Ponteiro(3, 0, "memory/x.md — y")])


def test_fila_lista_memorias_sem_gatilho(mod):
    fila = mod.fila(MEM, disco=_dividido(mod))
    assert len(fila["sem_gatilho"]) == 91          # 93 stubs − 2 com gatilho
    assert "padroes-e-ferramentas" in fila["familias_sem_frase"]
    assert "ambiente-e-build" not in fila["familias_sem_frase"]


# --- casar / buscar --------------------------------------------------------------------

def _projeto_recall():
    """Projeto pequeno com as 5 fontes do recall."""
    d = Disco()
    d.gravar(MEM / "resolvedor-de-token-prefere-processo-ao-header.md",
             "---\nname: resolvedor-de-token-prefere-processo-ao-header\n"
             "description: validar_corretor resolve a credencial pelo cache de processo antes do header\n"
             "gatilho: quando chamar `validar_corretor` numa rota que atende mais de um corretor\n"
             "metadata:\n  type: project\n---\n")
    d.gravar(MEM / "dns-search-inerte-sem-ndots.md",
             "---\nname: dns-search-inerte-sem-ndots\ndescription: nome curto resolve no host e falha no contêiner\n"
             "gatilho: quando nome curto resolve no host e falha só no contêiner (Docker injeta ndots:0)\n---\n")
    d.gravar(MEM / "sem-gatilho.md", "---\nname: sem-gatilho\ndescription: proxy do Docker em minúsculas\n---\n")
    d.gravar(MEM / "MEMORY.md", "# topo\n- **Integrações** → [subíndice](indice/integracoes.md) — 2 memórias\n")
    d.gravar(MEM / "indice" / "integracoes.md",
             "# Integrações\n"
             "- **quando chamar `validar_corretor` com 2 corretores** → [Resolvedor de token prefere processo ao header](../resolvedor-de-token-prefere-processo-ao-header.md) — passe token= explícito\n"
             "- **quando o nome curto falha no contêiner** → [dns_search inerte sem ndots](../dns-search-inerte-sem-ndots.md) — dns_opt ndots:1\n")
    d.gravar(MEM / "DIARIO.md",
             "# Diário\n- [handoff-chatwoot] handoff pro Chatwoot: contato deduplicado por telefone, e-mail não vai → sessions/2026-07-30-handoff-chatwoot.md\n")
    d.gravar(RAIZ / "docs" / "decisoes.md",
             "# Decisões\n- 2026-09-11 — **token explícito por corretor** em vez de cache de processo no validar_corretor\n")
    d.gravar(RAIZ / "docs" / "EVALS.md",
             "| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
             "| F-005 | 2026-09-14 | quando confiar que a memória do repo já está no contexto | memória não carregou | ponteiro | fechado |\n")
    return d


def test_tokens_normaliza_e_marca_identificadores(mod):
    t, ids = mod.tokens("O `validar_corretor` do corretor B saiu com o COD_CORR do A, não é?")
    assert "validar_corretor" in t and "cod_corr" in t and "corretor" in t
    assert "validar_corretor" in ids and "cod_corr" in ids
    assert "não" not in t and "com" not in t          # curtas/stopwords fora


def test_casar_acha_memoria_por_gatilho_e_prefere_o_arquivo_a_linha_do_indice(mod):
    r = mod.casar(RAIZ, "o corretor B saiu validado com o token do A na rota que chama validar_corretor",
                  disco=_projeto_recall())
    assert r, "nada casou"
    assert r[0].ponteiro.startswith("memory/resolvedor-de-token-prefere-processo-ao-header.md")
    assert sum("resolvedor-de-token" in x.ponteiro for x in r) == 1, "arquivo e linha do índice não podem sair em dobro"
    assert any(x.ponteiro.startswith("docs/decisoes.md:2") for x in r)


def test_casar_exige_dois_tokens_distintos(mod):
    assert mod.casar(RAIZ, "fala sobre corretor", disco=_projeto_recall()) == []


def test_casar_sem_acento_e_caixa(mod):
    r = mod.casar(RAIZ, "NOME CURTO resolve no host mas falha no CONTEINER", disco=_projeto_recall())
    assert r and "dns-search-inerte-sem-ndots.md" in r[0].ponteiro


def test_casar_le_diario_e_evals(mod):
    d = _projeto_recall()
    r = mod.casar(RAIZ, "o contato do Chatwoot está sendo deduplicado pelo telefone?", limite=5, disco=d)
    assert any(x.ponteiro.startswith("memory/sessions/2026-07-30-handoff-chatwoot.md") for x in r)
    r2 = mod.casar(RAIZ, "confiar que a memória do repo já está no contexto", limite=5, disco=d)
    assert any("docs/EVALS.md — F-005" in x.ponteiro for x in r2)


def test_casar_funciona_com_indice_plano_antes_da_divisao(mod):
    d = _projeto_recall()
    d.apagar_pasta(MEM / "indice")
    d.gravar(MEM / "MEMORY.md",
             "## Integrações\n- [dns_search inerte sem ndots](dns-search-inerte-sem-ndots.md) — nome curto falha no contêiner\n")
    for p in ("resolvedor-de-token-prefere-processo-ao-header.md", "dns-search-inerte-sem-ndots.md"):
        d.gravar(MEM / p, "---\nname: x\n---\n")   # sem gatilho: só a linha do índice casa
    r = mod.casar(RAIZ, "nome curto falha no contêiner e no host resolve", disco=d)
    assert r and "memory/MEMORY.md:2" in r[0].ponteiro


def test_formatar_injecao_respeita_600_bytes_sem_cortar_linha(mod):
    # cada linha ≈ 259 B: cabeçalho (64 B) + 2 linhas = 582 ≤ 600; a 3ª estouraria e fica fora inteira
    ponteiros = [mod.Ponteiro(9, 0, "memory/" + "a" * 240 + ".md — g"), mod.Ponteiro(8, 0, "memory/" + "b" * 240 + ".md — g"),
                 mod.Ponteiro(7, 0, "memory/" + "c" * 240 + ".md — g")]
    txt = mod.formatar_injecao(ponteiros)
    assert len(txt.encode("utf-8")) <= 600
    assert txt.count("\n- ") == 2 and "ccc" not in txt


def test_buscar_cli_lista_ponteiros(mod, monkeypatch, capsys):
    d = _projeto_recall()
    original = mod.casar
    monkeypatch.setattr(mod, "casar", lambda proj, termo, **kw: original(proj, termo, disco=d, **kw))
    assert mod.main(["buscar", "validar_corretor corretor", "--proj", str(RAIZ)]) == 0
    assert "memory/resolvedor-de-token-prefere-processo-ao-header.md" in capsys.readouterr().out


# --- o que o recall (`hooks/recall_memoria.py`) pede ao motor: casar(…, limite=3, diario=False) --------------
# Vieram de `tests/test_hook_recall_memoria.py` (2026-11-18): lá o motor entra falso; o que ele casa é provado aqui.

def _recall(mod, d, prompt):
    return mod.formatar_injecao(mod.casar(RAIZ, prompt, limite=3, diario=False, disco=d))


def test_recall_sem_diario_nao_casa_diario_de_sessao(mod):
    """F-030: no pedido de deploy de produção o hook injetou diários antigos (Blip, Evolution Go) e o assistente
    tratou o passado como estado atual. Com `diario=False` o diário fica de fora; o buscar do owner ainda acha."""
    d = _projeto_recall()
    d.gravar(MEM / "DIARIO.md",
             "# Diário\n- [evolution-go-em-homologacao] evolution go em homologação na azure, deploy do webhook do whatsapp"
             " → sessions/2026-08-04-evolution-go-em-homologacao.md\n")
    prompt = "preciso publicar no azure de produção o webhook do whatsapp, deploy da main"
    assert "memory/sessions/" not in _recall(mod, d, prompt), "o recall injetou diário de sessão"
    assert any(x.ponteiro.startswith("memory/sessions/2026-08-04") for x in mod.casar(RAIZ, prompt, limite=10, disco=d))


def test_recall_nao_cita_fora_de_escopo_sozinho(mod):
    """0.47.0: fora de escopo é "não agora" e só aparece quando o owner pede ao to-dolist. A busca rodava a cada
    mensagem e repetia o item como se fosse proibição — não lê o to-dolist nem o `FORA-DE-ESCOPO.md` antigo."""
    d = _projeto_recall()
    d.gravar(RAIZ / "docs" / "superpowers" / "FORA-DE-ESCOPO.md",
             "# Fora de escopo\n\n- **Redis para o handoff no WhatsApp** — descartado em 2026-07-30: a memória de "
             "sessão do servidor já resolve o handoff\n")
    d.gravar(RAIZ / "to-dolist.md",
             "- Redis para o handoff no WhatsApp #fora-de-escopo (decidido: 2026-07-30, a memória de sessão do "
             "servidor já resolve o handoff)\n")
    texto = _recall(mod, d, "vamos colocar redis pra guardar o handoff do whatsapp")
    assert "FORA-DE-ESCOPO.md" not in texto and "to-dolist.md" not in texto, texto


def test_recall_pula_decisao_obsoleta(mod):
    d = _projeto_recall()
    d.gravar(RAIZ / "docs" / "decisoes.md",
             "# Decisões\n- 2026-07-01 — cotação via n8n com callback no whatsapp — obsoleta: n8n saiu da produção\n")
    texto = _recall(mod, d, "a cotação via n8n com callback no whatsapp funciona?")
    assert "decisoes.md" not in texto, "o recall injetou uma decisão marcada obsoleta"


def test_busca_da_proposta_acha_pelo_termo_curto_do_tema_no_formato_do_whats(mod):
    """F-047: as memórias que vetavam a etapa nova de build não tinham `gatilho:`; a busca com o termo curto do tema
    (como o `confere_citacoes.memorias_da_proposta` chama) acha as duas e não a fora do tema. Veio de
    `tests/test_hook_memoria_da_proposta.py` (2026-11-18), onde o motor entra falso."""
    d = Disco()
    for nome, desc in (
            ("subida-nao-pode-depender-de-build", "Acrescentei --build ao atalho de subida para proteger de imagem "
                                                  "defasada, e transformei falha de rede em nada sobe"),
            ("contar-arquivos-novos-antes-de-propor", "propus 4 módulos novos onde 1 bastava; arquivo novo só se "
                                                      "justifica por capacidade que não existe"),
            ("fluxo-do-turno", "o fluxo do turno é a base do diagnóstico de conversa")):
        d.gravar(MEM / f"{nome}.md", FRONT_SEM_GATILHO.format(name=nome, desc=desc))
    d.gravar(MEM / "indice" / "como-eu-devo-trabalhar.md",
             "# Como eu devo trabalhar\n\n"
             "- [Subida não pode depender de build](../subida-nao-pode-depender-de-build.md) — proteção que cria modo "
             "de falha novo é regressão\n"
             "- [Contar arquivos novos antes de propor](../contar-arquivos-novos-antes-de-propor.md) — arquivo novo só "
             "por capacidade que não existe\n")
    d.gravar(MEM / "MEMORY.md",
             "- **Como eu devo trabalhar** → [subíndice](indice/como-eu-devo-trabalhar.md) — 2 memórias\n")

    def achados(termo):
        minimo = len(mod.tokens(termo)[0])
        return " ".join(p.ponteiro for p in mod.casar(RAIZ, termo, limite=9, minimo=minimo, diario=False, disco=d))
    build, novos = achados("build"), achados("arquivos novos")
    # o ponteiro é o da anotação ou o da linha do subíndice que aponta pra ela (o título): os dois levam à memória
    assert "subida-nao-pode-depender-de-build" in build or "Subida não pode depender de build" in build, build
    assert "contar-arquivos-novos-antes-de-propor" in novos or "Contar arquivos novos antes de propor" in novos, novos
    assert "fluxo-do-turno" not in build + novos


# ---- o disco e o git de verdade, e o processo (pasta montada uma vez) ------------------

REGRA = "---\nname: {n}\ndescription: descrição longa o bastante de {n}\ngatilho: quando acontecer {n}\nmetadata:\n  type: feedback\n---\n\ncorpo\n"


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("memoria_indice") / "proj"
    d = _projeto_whats()
    d.gravar(MEM / "MEMORY.md", WHATS.replace("\n", "\r\n").encode("utf-8"))          # repo Windows: CRLF
    d.gravar(MEM / "regra-velha.md", REGRA.format(n="regra-velha"))                  # já commitada
    d.gravar(MEM / "citacoes.md", "---\nname: citacoes\ndescription: d\n---\n"
                                  "`hooks/regras_do_kit.py` (do kit) e `app/sumiu.py` (não existe)\n")
    for p, dados in d.dados.items():
        alvo = raiz / p.relative_to(RAIZ)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(dados)
    if shutil.which("git"):
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t.t", "-c", "core.autocrlf=false"]
        subprocess.run(["git", "init", "-q", "--template="], cwd=raiz, capture_output=True)
        subprocess.run([*git, "add", "memory"], cwd=raiz, capture_output=True)
        subprocess.run([*git, "commit", "-q", "-m", "base"], cwd=raiz, capture_output=True)
    return raiz


def test_disco_e_git_de_verdade(mod, pasta, capsys):
    """O disco de verdade: o `dividir --aplicar` grava os subíndices mantendo o CRLF, o `verificar` pergunta ao git o
    que ainda não tem commit (só a anotação nova é cobrada pelo nome), as citações conferem o kit de verdade."""
    if not shutil.which("git"):
        pytest.skip("git não disponível")
    assert mod.main(["dividir", "--proj", str(pasta), "--aplicar"]) == 0 and "GRAVADO." in capsys.readouterr().out
    assert b"\r\n" in (pasta / "memory" / "indice" / "integracoes.md").read_bytes()
    assert b"\r\n" in (pasta / "memory" / "MEMORY.md").read_bytes()
    (pasta / "memory" / "regra-nova.md").write_text(REGRA.format(n="regra-nova"), encoding="utf-8")
    cobradas = [p for p in mod.verificar(pasta / "memory") if p.startswith("regra de ação sem gatilho de ação")]
    assert len(cobradas) == 1 and "regra-nova.md" in cobradas[0], cobradas
    assert [c for _, c in mod.citacoes_mortas(pasta)] == ["app/sumiu.py"]
    assert any("app-setting-faltando-cai-no-default.md" in p.ponteiro
               for p in mod.casar(pasta, "app setting faltando cai no default", limite=3))


def test_processo_buscar(pasta):
    r = subprocess.run([sys.executable, str(SCRIPT), "buscar", "app setting faltando no default", "--proj", str(pasta)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert "memory/app-setting-faltando-cai-no-default.md" in r.stdout
