"""memoria_tabela.py — tudo o que é memória do projeto numa tabela SQLite local (cópia para busca).

Por que existe: no teste de mesa de 2026-11-10 (4 projetos, 944 casos) a tabela com tudo o que é memória achou
o arquivo certo entre os 10 em 41% dos pedidos reais, contra 12% do jeito de hoje, lendo 4 vezes menos no
Whats. Decisão do owner: o arquivo no git é o original, a tabela é cópia, e ela mora FORA do `.claude`
("qualquer alteração perde") e fora de qualquer repo. Spec: docs/specs/memoria-em-tabela.md.
"""
import importlib.util
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_tabela.py"

NOTA = ("---\nname: project-boleto\ndescription: O boleto vem do CRM e nao do portal\n"
        "gatilho: quando emitir segunda via\nmetadata:\n  type: project\n---\n\n"
        "A segunda via usa a tabela TB_BOLETO.\n\n<private>segredo-xyz</private>\n")
EVALS = ("# Falhas\n\n| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
         "| F-001 | 2026-09-29 | quando emitir boleto sem conferir | premissa não-dita | conferir o CRM antes | aberto |\n")
HTML = ("<html><head><style>p{color:red}</style></head><body><h2>Deploy</h2>"
        "<p>Publicar no ambiente <b>orquidea</b>.</p><script>var x=1</script></body></html>")


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_tabela", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _grava(raiz, rel, texto):
    p = raiz / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")
    return p


def _projeto(tmp_path, pasta="alfa", titulo="Projeto Alfa"):
    raiz = tmp_path / pasta
    if titulo:
        _grava(raiz, "CLAUDE.md", f"# {titulo} — objetivo em uma frase\n")
    _grava(raiz, "memory/MEMORY.md", "- **Geral** → [subíndice](indice/geral.md) — 1 memórias\n")
    _grava(raiz, "memory/indice/geral.md",
           "# Geral\n\n- **quando mexer no boleto do corretor** → [Boleto vem do CRM](../project_boleto.md) — gancho do indice\n")
    _grava(raiz, "memory/project_boleto.md", NOTA)
    _grava(raiz, "memory/DIARIO.md",
           "# Diário\n\n## 2026-10-01\n\n- [boleto-no-crm] Sessao sobre o boleto no CRM → sessions/2026-10-01-boleto-no-crm.md\n")
    _grava(raiz, "memory/sessions/2026-10-01-boleto-no-crm.md",
           "# 2026-10-01 — boleto\n\n## Conversamos\n- falamos do boleto zebra\n\n## Pivôs\n- trocamos de rota\n")
    _grava(raiz, "docs/decisoes.md", "# Decisões\n\n- 2026-09-30 — **usar a fila X em vez de Y** — porque Z.\n")
    _grava(raiz, "docs/EVALS.md", EVALS)
    _grava(raiz, "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nA rota /boleto devolve o PDF.\n\n## Histórico\n- 2026-09-01 — criado.\n")
    _grava(raiz, "docs/superpowers/plans/2026-09-01-boleto.md", "# Plano\n\n## Tarefas\n1. fazer a rota girafa\n")
    _grava(raiz, "docs/superpowers/MAPA.md", "# Mapa\n\n## Onde estamos\nna branch do boleto hipopotamo\n")
    _grava(raiz, "docs/ARQUITETURA.md", "# Arquitetura\n\n## Visão\ntexto da visao do sistema.\n\n## Banco\ntabela TB_BOLETO fica no schema dbo.\n")
    _grava(raiz, "docs/guia.html", HTML)
    _grava(raiz, "to-dolist.md", "# To-do\n\n- comprar o dominio tartaruga\n")
    _grava(raiz, ".env", "SENHA=abc123\n")
    _grava(raiz, "docs/variaveis.txt", "TOKEN=zzz999\n")
    return raiz


def _linhas(raiz, **kw):
    return _mod().linhas_do_projeto(raiz, usar_git=False, **kw)


def _por_arq(linhas, arq):
    return [l for l in linhas if l["arq"] == arq]


def _sql(tabela, consulta, args=()):
    c = sqlite3.connect(str(tabela))
    try:
        return c.execute(consulta, args).fetchall()
    finally:
        c.close()


# ------------------------------------------------------------------ onde fica + esquema

def test_caminho_padrao_fica_na_pasta_do_usuario_fora_do_claude(tmp_path, monkeypatch):
    monkeypatch.delenv("MSS_MEMORIA_TABELA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    p = _mod().caminho_tabela()
    assert p == tmp_path / "mss-spec" / "memoria.sqlite3"
    assert ".claude" not in p.parts, "o owner vetou o .claude: qualquer alteração perde"


def test_variavel_troca_o_caminho(tmp_path, monkeypatch):
    monkeypatch.setenv("MSS_MEMORIA_TABELA", str(tmp_path / "outro" / "t.sqlite3"))
    assert _mod().caminho_tabela() == tmp_path / "outro" / "t.sqlite3"


def test_montar_cria_a_pasta_da_tabela(tmp_path):
    tabela = tmp_path / "nova" / "sub" / "t.sqlite3"
    _mod().montar(_projeto(tmp_path), tabela, usar_git=False)
    assert tabela.is_file()


def test_esquema_de_outra_versao_e_refeito(tmp_path):
    tabela = tmp_path / "t.sqlite3"
    c = sqlite3.connect(str(tabela))
    c.execute("CREATE TABLE memoria (lixo TEXT)")
    c.execute("PRAGMA user_version = 99")
    c.commit()
    c.close()
    mod = _mod()
    mod.montar(_projeto(tmp_path), tabela, usar_git=False)
    assert _sql(tabela, "PRAGMA user_version")[0][0] == mod.VERSAO_ESQUEMA
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo = 'anotacao'")[0][0] == 1


# ------------------------------------------------------------------ ler o projeto

def test_cada_fonte_vira_linha_com_o_tipo_certo(tmp_path):
    linhas = _linhas(_projeto(tmp_path))
    tipo = {l["arq"]: l["tipo"] for l in linhas}
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


def test_anotacao_leva_a_frase_do_subindice_e_a_classe(tmp_path):
    (l,) = _por_arq(_linhas(_projeto(tmp_path)), "memory/project_boleto.md")
    assert "segunda via" in l["quando"] and "boleto do corretor" in l["quando"]
    assert l["classe"] == "project"
    assert "CRM" in l["resumo"]
    assert l["titulo"] == "project boleto"
    assert "TB_BOLETO" in l["texto"]


def test_diario_leva_a_linha_do_diario_e_a_data(tmp_path):
    (l,) = _por_arq(_linhas(_projeto(tmp_path)), "memory/sessions/2026-10-01-boleto-no-crm.md")
    assert "Sessao sobre o boleto" in l["resumo"]
    assert l["data"] == "2026-10-01"
    assert "zebra" in l["texto"]


def test_decisao_vira_uma_linha_por_item_datado(tmp_path):
    (l,) = _por_arq(_linhas(_projeto(tmp_path)), "docs/decisoes.md")
    assert (l["ponteiro"], l["data"], l["titulo"]) == ("docs/decisoes.md:3", "2026-09-30", "usar a fila X em vez de Y")


def test_falha_vira_uma_linha_por_caso(tmp_path):
    (l,) = _por_arq(_linhas(_projeto(tmp_path)), "docs/EVALS.md")
    assert l["ponteiro"] == "docs/EVALS.md:5"
    assert "emitir boleto" in l["quando"]
    assert l["classe"] == "premissa não-dita"
    assert l["data"] == "2026-09-29"
    assert l["titulo"].startswith("F-001")


def test_documento_vira_uma_linha_por_secao_com_arquivo_e_linha(tmp_path):
    secoes = _por_arq(_linhas(_projeto(tmp_path)), "docs/ARQUITETURA.md")
    assert [(l["ponteiro"], l["titulo"]) for l in secoes] == [
        ("docs/ARQUITETURA.md:3", "ARQUITETURA › Visão"),
        ("docs/ARQUITETURA.md:6", "ARQUITETURA › Banco"),
    ]


def test_html_entra_sem_tags_nem_script(tmp_path):
    (l,) = _por_arq(_linhas(_projeto(tmp_path)), "docs/guia.html")
    assert "orquidea" in l["texto"] and "Deploy" in l["titulo"]
    for lixo in ("<b>", "var x", "color:red"):
        assert lixo not in l["texto"]


def test_private_env_e_txt_ficam_fora(tmp_path):
    linhas = _linhas(_projeto(tmp_path))
    tudo = " ".join(" ".join(str(v) for v in l.values()) for l in linhas)
    for segredo in ("segredo-xyz", "abc123", "zzz999"):
        assert segredo not in tudo
    assert not [l["arq"] for l in linhas if l["arq"].endswith((".env", ".txt"))]


def test_secao_gigante_e_dividida_em_pedacos(tmp_path):
    raiz = _projeto(tmp_path)
    _grava(raiz, "docs/grande.md", "# Grande\n\n## Tudo\n" + ("palavra " * 1700) + "\n")
    pedacos = _por_arq(_linhas(raiz), "docs/grande.md")
    assert len(pedacos) == 3 and all(len(l["texto"]) <= 6000 for l in pedacos)
    assert {l["ponteiro"] for l in pedacos} == {"docs/grande.md:3"}


def test_arquivo_fora_de_utf8_nao_derruba(tmp_path):
    raiz = _projeto(tmp_path)
    (raiz / "docs" / "ruim.md").write_bytes(b"# Ruim\n\n## Parte\n\xff\xfe texto cru\n")
    assert _por_arq(_linhas(raiz), "docs/ruim.md")


def test_nome_do_projeto_vem_do_claude_md_e_cai_pro_nome_da_pasta(tmp_path):
    mod = _mod()
    assert mod.nome_projeto(_projeto(tmp_path)) == "Projeto Alfa"
    assert mod.nome_projeto(_projeto(tmp_path, pasta="beta", titulo=None)) == "beta"


# ------------------------------------------------------------------ montar e remontar

def test_montar_grava_e_conta_por_tipo(tmp_path):
    tabela = tmp_path / "t.sqlite3"
    r = _mod().montar(_projeto(tmp_path), tabela, usar_git=False)
    assert r.projeto == "Projeto Alfa" and r.tabela == tabela
    assert r.por_tipo == {"anotacao": 1, "diario": 1, "decisao": 1, "falha": 1, "spec": 2, "plano": 1,
                          "mapa": 2, "documento": 3}
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (10, 0, 0, 0)
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo <> 'controle'")[0][0] == sum(r.por_tipo.values())


def test_remontar_sem_mudanca_nao_refaz_nada(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    r = mod.montar(raiz, tabela, usar_git=False)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 0, 10)


def test_mudar_um_arquivo_refaz_so_ele(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    r = mod.montar(raiz, tabela, usar_git=False)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 1, 0, 9)
    textos = [t for (t,) in _sql(tabela, "SELECT texto FROM memoria WHERE arq = 'docs/specs/boleto.md'")]
    assert len(textos) == 1 and "jacare" in textos[0]


def test_apagar_um_arquivo_tira_as_linhas(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    (raiz / "docs" / "superpowers" / "plans" / "2026-09-01-boleto.md").unlink()
    r = mod.montar(raiz, tabela, usar_git=False)
    assert (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 1, 9)
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo = 'plano'")[0][0] == 0


def test_mudar_o_subindice_refaz_a_anotacao(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "memory/indice/geral.md",
           "# Geral\n\n- **quando o corretor pedir o carne** → [Boleto vem do CRM](../project_boleto.md) — gancho\n")
    r = mod.montar(raiz, tabela, usar_git=False)
    assert r.refeitos == 1
    assert "carne" in _sql(tabela, "SELECT quando FROM memoria WHERE tipo = 'anotacao'")[0][0]


def test_dois_projetos_ficam_na_mesma_tabela_sem_um_tocar_o_outro(tmp_path):
    tabela, mod = tmp_path / "t.sqlite3", _mod()
    a, b = _projeto(tmp_path, "alfa", "Projeto Alfa"), _projeto(tmp_path, "beta", "Projeto Beta")
    mod.montar(a, tabela, usar_git=False)
    mod.montar(b, tabela, usar_git=False)
    antes = _sql(tabela, "SELECT count(*) FROM memoria WHERE projeto = 'Projeto Beta'")[0][0]
    (a / "to-dolist.md").unlink()
    mod.montar(a, tabela, usar_git=False)
    assert {p for (p,) in _sql(tabela, "SELECT DISTINCT projeto FROM memoria")} == {"Projeto Alfa", "Projeto Beta"}
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE projeto = 'Projeto Beta'")[0][0] == antes


def test_pastas_de_mesmo_nome_nao_se_misturam(tmp_path):
    tabela, mod = tmp_path / "t.sqlite3", _mod()
    a = _projeto(tmp_path / "um", "V2", titulo=None)
    b = _projeto(tmp_path / "dois", "V2", titulo=None)
    mod.montar(a, tabela, usar_git=False)
    r = mod.montar(b, tabela, usar_git=False)
    assert r.novos == 10, "a chave é a raiz do projeto, não o nome da pasta"
    assert _sql(tabela, "SELECT count(DISTINCT raiz) FROM memoria")[0][0] == 2


def test_trocar_o_nome_do_projeto_atualiza_as_linhas(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "CLAUDE.md", "# Projeto Gama — outro objetivo\n")
    mod.montar(raiz, tabela, usar_git=False)
    assert {p for (p,) in _sql(tabela, "SELECT DISTINCT projeto FROM memoria")} == {"Projeto Gama"}


def test_filtro_por_projeto_tipo_e_data_e_busca_por_palavra(tmp_path):
    tabela = tmp_path / "t.sqlite3"
    _mod().montar(_projeto(tmp_path), tabela, usar_git=False)
    assert _sql(tabela, "SELECT ponteiro FROM memoria WHERE projeto = ? AND tipo = 'decisao' AND data >= '2026-09-01'",
                ("Projeto Alfa",)) == [("docs/decisoes.md:3",)]
    assert _sql(tabela, "SELECT arq FROM memoria WHERE memoria MATCH 'girafa'") == [("docs/superpowers/plans/2026-09-01-boleto.md",)]


# ------------------------------------------------------------------ git: dono, data e pendências

def _git(raiz, *args, autor="Fulana Teste", data="2026-08-15T10:00:00"):
    env = dict(os.environ, GIT_AUTHOR_NAME=autor, GIT_AUTHOR_EMAIL="fulana@exemplo.test", GIT_AUTHOR_DATE=data,
               GIT_COMMITTER_NAME=autor, GIT_COMMITTER_EMAIL="fulana@exemplo.test", GIT_COMMITTER_DATE=data)
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")


def _repo(tmp_path):
    raiz = _projeto(tmp_path)
    _grava(raiz, ".gitignore", ".env\ndocs/escondido.md\n")
    _grava(raiz, "docs/escondido.md", "# Escondido\n\n## Parte\nconteudo ignorado pelo git papagaio\n")
    _git(raiz, "init", "-q")
    _git(raiz, "add", ".gitignore", "CLAUDE.md", "memory", "docs", "to-dolist.md")
    _git(raiz, "commit", "-q", "-m", "inicio")
    return raiz


def test_dono_e_data_vem_da_criacao_no_git(tmp_path):
    (l,) = _por_arq(_mod().linhas_do_projeto(_repo(tmp_path)), "memory/project_boleto.md")
    assert (l["dono"], l["data"]) == ("Fulana Teste", "2026-08-15")


def test_ignorado_pelo_git_fica_fora(tmp_path):
    linhas = _mod().linhas_do_projeto(_repo(tmp_path))
    assert not _por_arq(linhas, "docs/escondido.md")
    assert _por_arq(linhas, "docs/ARQUITETURA.md")


def test_arquivo_novo_ainda_nao_commitado_entra_e_vira_pendencia(tmp_path):
    raiz = _repo(tmp_path)
    _grava(raiz, "memory/feedback_novo.md", "---\nname: feedback-novo\ndescription: nota nova\nmetadata:\n  type: feedback\n---\n\ncorpo novo\n")
    r = _mod().montar(raiz, tmp_path / "t.sqlite3")
    assert r.novos == 11
    assert any("1 arquivo" in p and "commit" in p for p in r.pendencias), r.pendencias


def test_projeto_sem_git_segue_sem_erro(tmp_path):
    r = _mod().montar(_projeto(tmp_path), tmp_path / "t.sqlite3", usar_git=True)
    assert r.novos == 10 and r.pendencias == []


# ------------------------------------------------------------------ status e CLI

def test_status_sem_tabela_avisa_como_remontar(tmp_path):
    s = _mod().status(_projeto(tmp_path), tmp_path / "nao-existe.sqlite3", usar_git=False)
    assert s.existe is False and "montar" in s.mensagem


def test_status_em_dia(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    s = mod.status(raiz, tabela, usar_git=False)
    assert (s.existe, s.mudaram) == (True, 0) and s.linhas == 12


def test_status_desatualizada_conta_os_arquivos(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "to-dolist.md", "# To-do\n\n- outro item\n")
    (raiz / "docs" / "guia.html").unlink()
    s = mod.status(raiz, tabela, usar_git=False)
    assert s.mudaram == 2 and "montar" in s.mensagem


def _cli(args, cwd, casa):
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8")
    env.pop("MSS_MEMORIA_TABELA", None)
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(cwd), env=env, capture_output=True, timeout=120)


def test_cli_com_os_padroes_monta_na_pasta_do_usuario(tmp_path):
    raiz, casa = _projeto(tmp_path), tmp_path / "casa"
    casa.mkdir()
    r = _cli(["montar"], raiz, casa)
    saida = r.stdout.decode("utf-8", "ignore")
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")
    assert (casa / "mss-spec" / "memoria.sqlite3").is_file()
    assert "Projeto Alfa" in saida and "anotacao" in saida


def test_cli_status_sem_tabela_sai_com_1(tmp_path):
    raiz, casa = _projeto(tmp_path), tmp_path / "casa"
    casa.mkdir()
    r = _cli(["status"], raiz, casa)
    assert r.returncode == 1 and "montar" in r.stdout.decode("utf-8", "ignore")


def test_cli_onde_imprime_o_caminho(tmp_path):
    raiz, casa = _projeto(tmp_path), tmp_path / "casa"
    casa.mkdir()
    r = _cli(["onde"], raiz, casa)
    assert r.stdout.decode("utf-8", "ignore").strip() == str(casa / "mss-spec" / "memoria.sqlite3")


def test_tabela_presa_por_outro_programa_da_erro_claro_e_sai_com_2(tmp_path, capsys):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "to-dolist.md", "# To-do\n\n- item novo\n")
    outro = sqlite3.connect(str(tabela))
    outro.execute("BEGIN EXCLUSIVE")
    try:
        codigo = mod.main(["montar", "--proj", str(raiz), "--tabela", str(tabela), "--sem-git"])
    finally:
        outro.rollback()
        outro.close()
    assert codigo == 2
    assert "outro programa" in capsys.readouterr().out
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo <> 'controle'")[0][0] == 12, "a tabela ficou como estava"


def test_arquivo_grande_demais_fica_fora_e_vira_pendencia(tmp_path, monkeypatch):
    raiz, mod = _projeto(tmp_path), _mod()
    monkeypatch.setattr(mod, "TETO_ARQUIVO", 200)
    _grava(raiz, "docs/enorme.md", "# Enorme\n\n## Parte\n" + ("texto " * 100) + "\n")
    r = mod.montar(raiz, tmp_path / "t.sqlite3", usar_git=False)
    assert not _sql(tmp_path / "t.sqlite3", "SELECT 1 FROM memoria WHERE arq = 'docs/enorme.md'")
    assert any("docs/enorme.md" in p for p in r.pendencias), r.pendencias


def test_pasta_com_espaco_e_acento(tmp_path):
    raiz, casa = _projeto(tmp_path, pasta="IA Bot Agent - Açaí"), tmp_path / "casa"
    casa.mkdir()
    r = _cli(["montar", "--proj", str(raiz), "--sem-git"], tmp_path, casa)
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")
    assert _sql(casa / "mss-spec" / "memoria.sqlite3", "SELECT count(DISTINCT raiz) FROM memoria")[0][0] == 1


# ------------------------------------------------------------------ ligação ao kit (prosa e memória)

def test_comando_memory_oferece_o_modo_tabela():
    mem = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    assert "tabela" in mem.split("---")[1], "memory.md: argument-hint não oferece o modo tabela"
    assert 'memoria_tabela.py" montar' in mem and 'memoria_tabela.py" status' in mem
    assert "~/mss-spec/" in mem and "fora do `.claude`" in mem, "memory.md não diz onde a tabela mora"
    assert "nunca grave na tabela" in mem.lower(), "memory.md não diz que o arquivo é o original"


def test_procedimento_de_troca_de_maquina_esta_na_memoria_do_kit():
    mi = _mod()._motor()
    p = REPO / "memory" / "project_remontar_a_tabela_de_memoria.md"
    assert mi.frontmatter(p).get("type") == "procedimento"
    assert mi.validar_procedimento(mi.corpo(p)) == []
    indice = (REPO / "memory" / "indice" / "ambiente-desta-maquina-e-pendencias.md").read_text(encoding="utf-8")
    assert "project_remontar_a_tabela_de_memoria.md" in indice, "procedimento fora do subíndice: o recall não acha"
