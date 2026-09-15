"""memoria_indice.py — índice de memória em dois níveis (topo por família + memory/indice/).

Por que existe: o índice plano do Whats chegou a 25.421 bytes (~6.355 tokens em TODA janela) e o kit
mandou PODAR — contra a própria decisão "mover, nunca apagar". O topo passa a ter 1 linha por família
(teto 6 KB) e as memórias vivem em subíndices lidos só quando a família bate.
"""
import importlib.util
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_indice.py"
FIXTURE = REPO / "tests" / "fixtures" / "memoria_whats_2026-09-14" / "MEMORY.md"

FRONT_COM_GATILHO = "---\nname: {name}\ndescription: {desc}\ngatilho: quando {gat}\nmetadata:\n  type: project\n---\n\ncorpo\n"
FRONT_SEM_GATILHO = "---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: project\n---\n\ncorpo\n"


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses (3.14) resolve anotações via sys.modules
    spec.loader.exec_module(mod)
    return mod


def _projeto_whats(tmp_path, com_gatilho=("app-setting-faltando-cai-no-default.md",
                                          "chatwoot-deduplica-contato-por-telefone.md")):
    """Projeto sintético: o índice REAL do Whats + um stub por arquivo apontado (2 com gatilho)."""
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    mem.mkdir(parents=True)
    shutil.copy(FIXTURE, mem / "MEMORY.md")
    for arq in re.findall(r"\]\(([^)/]+\.md)\)", FIXTURE.read_text(encoding="utf-8")):
        if arq == "<arquivo>.md":
            continue
        molde = FRONT_COM_GATILHO if arq in com_gatilho else FRONT_SEM_GATILHO
        (mem / arq).write_text(molde.format(name=arq[:-3], desc=f"desc de {arq}",
                                            gat=f"a situação de {arq[:-3].replace('-', ' ')}"),
                               encoding="utf-8")
    return raiz


# --- parse ---------------------------------------------------------------------------

def test_le_5_familias_e_93_itens_do_indice_do_whats():
    mod = _mod()
    fams = mod.ler_indice_plano(FIXTURE.read_text(encoding="utf-8"))
    assert [f.titulo for f in fams] == ["Como trabalhar neste projeto", "Ambiente e build", "Integrações",
                                        "Padrões e ferramentas", "Como eu devo trabalhar (correções do owner)"]
    assert sum(len(f.itens) for f in fams) == 93
    assert fams[1].itens[0].titulo == "Build quebra por CA desatualizada"
    assert fams[1].itens[0].arquivo == "build-quebra-por-ca-desatualizada.md"


def test_slug_sem_acento_sem_parenteses():
    mod = _mod()
    assert mod.slug("Como eu devo trabalhar (correções do owner)") == "como-eu-devo-trabalhar"
    assert mod.slug("Integrações") == "integracoes"


def test_relink_so_muda_link_local():
    mod = _mod()
    assert mod.relink("- [T](arquivo.md) — g") == "- [T](../arquivo.md) — g"
    assert mod.relink("- **quando x** → [T](arquivo.md) — veja [[outra]] e https://a.b/c.md") == \
        "- **quando x** → [T](../arquivo.md) — veja [[outra]] e https://a.b/c.md"
    assert mod.relink("- [T](../arquivo.md) — g") == "- [T](../arquivo.md) — g"


# --- dividir ---------------------------------------------------------------------------

def test_dividir_dry_run_nao_escreve_nada(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    antes = (raiz / "memory" / "MEMORY.md").read_bytes()
    rel = mod.dividir(raiz / "memory", aplicar=False)
    assert rel.ok, rel.problemas
    assert not (raiz / "memory" / "indice").exists()
    assert (raiz / "memory" / "MEMORY.md").read_bytes() == antes
    assert len(rel.familias) == 5 and rel.bytes_topo < 6000


def test_dividir_aplicar_conserva_toda_linha_byte_a_byte(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    linhas_antes = [l for l in FIXTURE.read_text(encoding="utf-8").splitlines() if l.startswith("- [")]
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert rel.ok, rel.problemas
    subs = sorted((raiz / "memory" / "indice").glob("*.md"))
    assert [p.name for p in subs] == ["ambiente-e-build.md", "como-eu-devo-trabalhar.md",
                                      "como-trabalhar-neste-projeto.md", "integracoes.md", "padroes-e-ferramentas.md"]
    linhas_depois = [l for p in subs for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    assert len(linhas_depois) == len(linhas_antes) == 93
    assert sorted(linhas_depois) == sorted(mod.relink(l) for l in linhas_antes)
    topo = (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    assert "<!-- MODELO" not in topo, "o comentário-modelo não é memória: sai do topo"
    assert topo.count("→ [subíndice](indice/") == 5
    assert "— 22 memórias" in topo  # Ambiente e build


def test_topo_usa_frases_do_gatilho_e_nao_palavras_raspadas(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    mod.dividir(raiz / "memory", aplicar=True)
    topo = (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    linha_amb = next(l for l in topo.splitlines() if "indice/ambiente-e-build.md" in l)
    assert "a situação de app setting faltando cai no default" in linha_amb
    linha_padroes = next(l for l in topo.splitlines() if "indice/padroes-e-ferramentas.md" in l)
    assert "quando:" not in linha_padroes, "família sem nenhum gatilho: sai só com título e N"
    for lixo in ("Esta", ".md ·", "GET"):
        assert lixo not in topo


def test_dividir_recusa_quando_ponteiro_quebrado(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    (raiz / "memory" / "build-quebra-por-ca-desatualizada.md").unlink()
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert not rel.ok
    assert any("build-quebra-por-ca-desatualizada.md" in p for p in rel.problemas)
    assert not (raiz / "memory" / "indice").exists(), "conservação falhou: NADA se grava"


def test_dividir_recusa_linha_solta_dentro_de_secao(tmp_path):
    """Linha que não é item nem vazia dentro de uma seção seria perdida em silêncio: o script recusa."""
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("## Integrações\n", "## Integrações\nNota solta que não é item.\n"), encoding="utf-8")
    rel = mod.dividir(raiz / "memory", aplicar=True)
    assert not rel.ok and any("linha solta" in x and "Integrações" in x for x in rel.problemas)
    assert not (raiz / "memory" / "indice").exists()


def test_dividir_preserva_crlf(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_bytes(p.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    mod.dividir(raiz / "memory", aplicar=True)
    assert b"\r\n" in p.read_bytes()
    assert b"\r\n" in (raiz / "memory" / "indice" / "integracoes.md").read_bytes()


# --- verificar / fila ------------------------------------------------------------------

def _dividido(tmp_path):
    mod = _mod()
    raiz = _projeto_whats(tmp_path)
    assert mod.dividir(raiz / "memory", aplicar=True).ok
    return mod, raiz


def test_verificar_limpo_depois_de_dividir(tmp_path):
    mod, raiz = _dividido(tmp_path)
    assert mod.verificar(raiz / "memory") == []


def test_verificar_acusa_memoria_sem_linha_e_ponteiro_quebrado(tmp_path):
    mod, raiz = _dividido(tmp_path)
    (raiz / "memory" / "nova-memoria.md").write_text(FRONT_SEM_GATILHO.format(name="nova-memoria", desc="x"), encoding="utf-8")
    (raiz / "memory" / "crm-www4-dois-nomes.md").unlink()
    probs = mod.verificar(raiz / "memory")
    assert any("nova-memoria.md" in p and "sem linha" in p for p in probs)
    assert any("crm-www4-dois-nomes.md" in p and "quebrado" in p for p in probs)


def test_verificar_ignora_obsoleta(tmp_path):
    mod, raiz = _dividido(tmp_path)
    (raiz / "memory" / "velha.md").write_text(
        "---\nname: velha\ndescription: x\nobsoleta: 2026-09-01 — superada por [[nova]]\n---\n", encoding="utf-8")
    assert mod.verificar(raiz / "memory") == []


def test_verificar_corrige_n_do_topo_com_aplicar(tmp_path):
    mod, raiz = _dividido(tmp_path)
    sub = raiz / "memory" / "indice" / "integracoes.md"
    sub.write_text(sub.read_text(encoding="utf-8") + "- [Extra](../crm-www4-dois-nomes.md) — dup de teste\n", encoding="utf-8")
    probs = mod.verificar(raiz / "memory")
    assert any("N do topo" in p and "integracoes" in p for p in probs)
    assert any("mais de uma linha" in p for p in probs)
    mod.verificar(raiz / "memory", aplicar=True)
    assert "— 27 memórias" in (raiz / "memory" / "MEMORY.md").read_text(encoding="utf-8")


def test_verificar_acusa_topo_acima_do_teto(tmp_path):
    mod, raiz = _dividido(tmp_path)
    p = raiz / "memory" / "MEMORY.md"
    p.write_text(p.read_text(encoding="utf-8") + "x" * 6000, encoding="utf-8")
    assert any("teto" in pr for pr in mod.verificar(raiz / "memory"))


def test_fila_lista_memorias_sem_gatilho(tmp_path):
    mod, raiz = _dividido(tmp_path)
    fila = mod.fila(raiz / "memory")
    assert len(fila["sem_gatilho"]) == 91          # 93 stubs − 2 com gatilho
    assert "padroes-e-ferramentas" in fila["familias_sem_frase"]
    assert "ambiente-e-build" not in fila["familias_sem_frase"]


# --- casar / buscar --------------------------------------------------------------------

def _projeto_recall(tmp_path):
    """Projeto pequeno com as 5 fontes do recall."""
    raiz = tmp_path / "proj"
    mem = raiz / "memory"
    (mem / "indice").mkdir(parents=True)
    (mem / "sessions").mkdir()
    (raiz / "docs").mkdir()
    (mem / "resolvedor-de-token-prefere-processo-ao-header.md").write_text(
        "---\nname: resolvedor-de-token-prefere-processo-ao-header\n"
        "description: validar_corretor resolve a credencial pelo cache de processo antes do header\n"
        "gatilho: quando chamar `validar_corretor` numa rota que atende mais de um corretor\n"
        "metadata:\n  type: project\n---\n", encoding="utf-8")
    (mem / "dns-search-inerte-sem-ndots.md").write_text(
        "---\nname: dns-search-inerte-sem-ndots\ndescription: nome curto resolve no host e falha no contêiner\n"
        "gatilho: quando nome curto resolve no host e falha só no contêiner (Docker injeta ndots:0)\n---\n", encoding="utf-8")
    (mem / "sem-gatilho.md").write_text("---\nname: sem-gatilho\ndescription: proxy do Docker em minúsculas\n---\n", encoding="utf-8")
    (mem / "MEMORY.md").write_text("# topo\n- **Integrações** → [subíndice](indice/integracoes.md) — 2 memórias\n", encoding="utf-8")
    (mem / "indice" / "integracoes.md").write_text(
        "# Integrações\n"
        "- **quando chamar `validar_corretor` com 2 corretores** → [Resolvedor de token prefere processo ao header](../resolvedor-de-token-prefere-processo-ao-header.md) — passe token= explícito\n"
        "- **quando o nome curto falha no contêiner** → [dns_search inerte sem ndots](../dns-search-inerte-sem-ndots.md) — dns_opt ndots:1\n",
        encoding="utf-8")
    (mem / "DIARIO.md").write_text(
        "# Diário\n- [handoff-chatwoot] handoff pro Chatwoot: contato deduplicado por telefone, e-mail não vai → sessions/2026-07-30-handoff-chatwoot.md\n",
        encoding="utf-8")
    (raiz / "docs" / "decisoes.md").write_text(
        "# Decisões\n- 2026-09-11 — **token explícito por corretor** em vez de cache de processo no validar_corretor\n",
        encoding="utf-8")
    (raiz / "docs" / "EVALS.md").write_text(
        "| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
        "| F-005 | 2026-09-14 | quando confiar que a memória do repo já está no contexto | memória não carregou | ponteiro | fechado |\n",
        encoding="utf-8")
    return raiz


def test_tokens_normaliza_e_marca_identificadores():
    mod = _mod()
    t, ids = mod.tokens("O `validar_corretor` do corretor B saiu com o COD_CORR do A, não é?")
    assert "validar_corretor" in t and "cod_corr" in t and "corretor" in t
    assert "validar_corretor" in ids and "cod_corr" in ids
    assert "não" not in t and "com" not in t          # curtas/stopwords fora


def test_casar_acha_memoria_por_gatilho_e_prefere_o_arquivo_a_linha_do_indice(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "o corretor B saiu validado com o token do A na rota que chama validar_corretor")
    assert r, "nada casou"
    assert r[0].ponteiro.startswith("memory/resolvedor-de-token-prefere-processo-ao-header.md")
    assert sum("resolvedor-de-token" in x.ponteiro for x in r) == 1, "arquivo e linha do índice não podem sair em dobro"
    assert any(x.ponteiro.startswith("docs/decisoes.md:2") for x in r)


def test_casar_exige_dois_tokens_distintos(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    assert mod.casar(raiz, "fala sobre corretor") == []


def test_casar_sem_acento_e_caixa(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "NOME CURTO resolve no host mas falha no CONTEINER")
    assert r and "dns-search-inerte-sem-ndots.md" in r[0].ponteiro


def test_casar_le_diario_e_evals(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    r = mod.casar(raiz, "o contato do Chatwoot está sendo deduplicado pelo telefone?", limite=5)
    assert any(x.ponteiro.startswith("memory/sessions/2026-07-30-handoff-chatwoot.md") for x in r)
    r2 = mod.casar(raiz, "confiar que a memória do repo já está no contexto", limite=5)
    assert any("docs/EVALS.md — F-005" in x.ponteiro for x in r2)


def test_casar_funciona_com_indice_plano_antes_da_divisao(tmp_path):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    shutil.rmtree(raiz / "memory" / "indice")
    (raiz / "memory" / "MEMORY.md").write_text(
        "## Integrações\n- [dns_search inerte sem ndots](dns-search-inerte-sem-ndots.md) — nome curto falha no contêiner\n",
        encoding="utf-8")
    for p in ("resolvedor-de-token-prefere-processo-ao-header.md", "dns-search-inerte-sem-ndots.md"):
        (raiz / "memory" / p).write_text("---\nname: x\n---\n", encoding="utf-8")   # sem gatilho: só a linha do índice casa
    r = mod.casar(raiz, "nome curto falha no contêiner e no host resolve")
    assert r and "memory/MEMORY.md:2" in r[0].ponteiro


def test_formatar_injecao_respeita_600_bytes_sem_cortar_linha(tmp_path):
    mod = _mod()
    # cada linha ≈ 259 B: cabeçalho (64 B) + 2 linhas = 582 ≤ 600; a 3ª estouraria e fica fora inteira
    ponteiros = [mod.Ponteiro(9, 0, "memory/" + "a" * 240 + ".md — g"), mod.Ponteiro(8, 0, "memory/" + "b" * 240 + ".md — g"),
                 mod.Ponteiro(7, 0, "memory/" + "c" * 240 + ".md — g")]
    txt = mod.formatar_injecao(ponteiros)
    assert len(txt.encode("utf-8")) <= 600
    assert txt.count("\n- ") == 2 and "ccc" not in txt


def test_buscar_cli_lista_ponteiros(tmp_path, capsys):
    mod = _mod()
    raiz = _projeto_recall(tmp_path)
    assert mod.main(["buscar", "validar_corretor corretor", "--proj", str(raiz)]) == 0
    out = capsys.readouterr().out
    assert "memory/resolvedor-de-token-prefere-processo-ao-header.md" in out
