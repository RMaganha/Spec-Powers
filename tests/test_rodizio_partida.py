"""rodizio_partida.py — MAPA com 2 blocos por seção, INDEX só com tarefa viva; o resto vai pro histórico.

Por que: o MAPA do Whats tinha 89.651 bytes (teto 6.000) e o INDEX 61.399 (teto 7.000) — relidos em toda
janela. O template já prometia "atual + 1 anterior" e "fechada sai"; faltava quem MOVESSE. Move, nunca apaga;
dry-run por padrão; conservação byte a byte antes de gravar.

Camadas (2026-11-18, `docs/decisoes.md`): o script lê e grava por um objeto de disco; aqui ele é um dicionário
{caminho: bytes} (`Disco`). O `enxugar` sem `--aplicar` roda num rascunho em memória por cima dele (`Rascunho`).
O disco de verdade (a gravação com CRLF, o rascunho sobre o disco real) fica num teste só, numa pasta montada uma
vez; o processo python, num teste só.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "rodizio_partida.py"
RAIZ = REPO.parent / "projeto-que-nao-existe-rodizio"          # absoluto, nunca criado
SPD = RAIZ / "docs" / "superpowers"

MAPA = """# Mapa de contexto — Proj

## Onde estamos

📍 **Branch atual: `feature/x`** — estado atual, linha 1.
linha 2 do atual.

---

✅ **2026-09-13 — anterior 1** verificado.

---

✅ **2026-09-10 — anterior 2** coisa velha.
detalhe do anterior 2.

---

⚠️ **2026-09-01 — anterior 3** mais velho ainda.

## Próximo passo

1. passo atual.

---

1. passo anterior.

---

1. passo velho.

## Conexões

- outro projeto — não mexer.
"""

INDEX = """# Índice de tarefas

## Em andamento
- [formatação](../specs/formatacao.md) — juntar linhas — aberta
- [relatório](../specs/relatorio.md) — PDF — fechada
- [importador](../specs/importador.md) — CSV — pausada: aguardando layout
5. upgrade — sincroniza — **em andamento** (sem commit)

## Backlog
- [alerta](../specs/alerta.md) — e-mail — fechada

## Fora de escopo — decidido NÃO fazer (2026-07-28)
- login social — fechada de propósito, fica aqui pra não re-litigar
"""


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("rodizio_partida", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class Disco:
    """O projeto em memória, com os métodos do `DiscoReal`: {caminho: bytes}."""

    def __init__(self):
        self.dados = {}

    def gravar(self, p, texto):
        self.dados[Path(p)] = texto.encode("utf-8") if isinstance(texto, str) else texto

    def ler(self, p):
        return self.ler_bytes(p).decode("utf-8")

    def ler_bytes(self, p):
        try:
            return self.dados[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def gravar_bytes(self, p, dados):
        self.dados[Path(p)] = dados

    def eh_arquivo(self, p):
        return Path(p) in self.dados


def _projeto(mapa=MAPA, index=INDEX):
    d = Disco()
    d.gravar(SPD / "MAPA.md", mapa)
    d.gravar(SPD / "INDEX.md", index)
    return d


def _todas(d):
    return "\n".join(d.ler(p) for p in sorted(d.dados) if p.parent == SPD and p.suffix == ".md")


# --- mapa -------------------------------------------------------------------------------

def test_mapa_mantem_dois_blocos_por_secao_e_move_o_resto(mod):
    d = _projeto()
    rel = mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert rel.ok, rel.problemas
    mapa = d.ler(SPD / "MAPA.md")
    assert "anterior 1" in mapa and "anterior 2" not in mapa and "anterior 3" not in mapa
    assert "passo anterior." in mapa and "passo velho." not in mapa
    assert "outro projeto — não mexer." in mapa
    assert mapa.count("\n---\n") == 2
    hist = d.ler(SPD / "MAPA-historico.md")
    assert '## 2026-09-15 — rodízio de "Onde estamos"' in hist and "anterior 2" in hist and "anterior 3" in hist
    assert '## 2026-09-15 — rodízio de "Próximo passo"' in hist and "passo velho." in hist
    assert hist.index("anterior 2") < hist.index("anterior 3"), "ordem original preservada (mais novo em cima)"
    assert rel.movidas == 4           # linhas de conteúdo movidas (anterior 2 ×2, anterior 3, passo velho); `---` não conta
    assert rel.bytes_depois < rel.bytes_antes


def test_mapa_dry_run_nao_escreve(mod):
    d = _projeto()
    antes = dict(d.dados)
    rel = mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=False, disco=d)
    assert rel.ok and rel.movidas == 4
    assert d.dados == antes


def test_mapa_bloco_unico_e_intocado_e_nada_a_mover(mod):
    curto = "# Mapa\n\n## Onde estamos\n\nsó um bloco.\n\n## Próximo passo\n\n1. só um.\n\n## Conexões\n\n- x\n"
    d = _projeto(mapa=curto)
    rel = mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert rel.ok and rel.movidas == 0
    assert d.ler(SPD / "MAPA.md") == curto
    assert not d.eh_arquivo(SPD / "MAPA-historico.md")


def test_mapa_historico_existente_recebe_prepend_depois_do_titulo(mod):
    d = _projeto()
    d.gravar(SPD / "MAPA-historico.md", "<!-- comentário -->\n\n# Histórico do mapa — Proj\n\n## 2026-08-01 — antigo\n\nvelho.\n")
    mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    t = d.ler(SPD / "MAPA-historico.md")
    assert t.startswith("<!-- comentário -->\n\n# Histórico do mapa — Proj\n")
    assert t.index("2026-09-15") < t.index("2026-08-01")


def test_mapa_avisa_quando_ainda_acima_do_teto(mod):
    d = _projeto(mapa=MAPA.replace("linha 2 do atual.", "linha 2 do atual. " + "x" * 7000))
    rel = mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert rel.ok and any("ainda acima do teto" in a and "conteúdo" in a for a in rel.avisos)
    assert "x" * 7000 in d.ler(SPD / "MAPA.md"), "bloco atual NUNCA se corta"


def test_mapa_preserva_crlf(mod):
    d = _projeto(mapa=MAPA.replace("\n", "\r\n"))
    mod.rodizio_mapa(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert b"\r\n" in d.ler_bytes(SPD / "MAPA.md")
    assert b"\r\n" in d.ler_bytes(SPD / "MAPA-historico.md")


# --- index ------------------------------------------------------------------------------

def test_index_move_so_fechada_e_preserva_fora_de_escopo(mod):
    d = _projeto()
    rel = mod.rodizio_index(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert rel.ok, rel.problemas
    idx = d.ler(SPD / "INDEX.md")
    assert "[formatação]" in idx and "pausada: aguardando layout" in idx and "**em andamento**" in idx
    assert "[relatório]" not in idx and "[alerta]" not in idx
    assert "login social — fechada de propósito" in idx, "'Fora de escopo' NUNCA se move"
    assert "## Backlog" in idx, "cabeçalho fica mesmo esvaziado"
    hist = d.ler(SPD / "INDEX-historico.md")
    assert "## 2026-09-15 — fechadas" in hist and "[relatório]" in hist and "[alerta]" in hist
    assert rel.movidas == 2


def test_index_dry_run_nao_escreve(mod):
    d = _projeto()
    antes = dict(d.dados)
    rel = mod.rodizio_index(RAIZ, hoje="2026-09-15", aplicar=False, disco=d)
    assert rel.ok and rel.movidas == 2
    assert d.dados == antes


def test_index_reusa_a_regra_de_status_do_hook(mod):
    """`pausada` não é fechada; `fechada` em negrito também conta — a mesma leitura do um_item_por_janela."""
    assert mod.fechada("- [x](../specs/x.md) — obj — **fechada** (2026-09-01)")
    assert not mod.fechada("- [x](../specs/x.md) — obj — pausada: espera")
    assert not mod.fechada("- [x](../specs/x.md) — obj — aberta")


def test_index_avisa_abertas_que_nao_cabem(mod):
    muitas = "# Índice\n\n## Em andamento\n" + "".join(
        f"- [tarefa {i}](../specs/t{i}.md) — {'objetivo ' * 30} — aberta\n" for i in range(40))
    d = _projeto(index=muitas)
    rel = mod.rodizio_index(RAIZ, hoje="2026-09-15", aplicar=True, disco=d)
    assert rel.ok and rel.movidas == 0
    assert any("aberta" in a and "owner" in a for a in rel.avisos)


# --- enxugar: a 2ª etapa (F-030) — o que o owner moveu à mão no Whats, agora mecânico ----------

def _index_gordo():
    longo = "detalhe " * 120
    return ("# Índice de tarefas\n\n"
            "## Assuntos existentes (levantados do código)\n\n"
            + "".join(f"- assunto-{i} — o código já faz {longo} — existente\n" for i in range(4)) +
            "\n## Em andamento\n\n"
            f"- [painel](../specs/painel.md) — tela {longo} — em andamento: fila construída dentro dele\n"
            "- [curta](../specs/curta.md) — cabe — aberta\n"
            "\n## Backlog\n\n"
            + "".join(f"- ideia-{i} — {longo} — aberta\n" for i in range(4)) +
            "\n### Crítico\n- identidade — global de processo — aberta\n"
            "\n## Fora de escopo — decidido NÃO fazer\n\n"
            + "".join(f"- **Recusado {i}** — {longo}\n" for i in range(4)))


def _mapa_gordo():
    longo = "contrato " * 80
    return ("# Mapa de contexto — Proj\n\n## Onde estamos\n\n📍 estado atual curto.\n\n"
            "## Próximo passo\n\n1. passo.\n\n## Conexões\n\n"
            + "".join(f"- → Serviço {i} (`svc{i}`): {longo}\n  continuação da linha {i}\n" for i in range(8)))


def test_enxugar_index_move_secoes_e_fica_abaixo_do_teto(mod):
    original = _index_gordo()
    d = _projeto(index=original)
    rels = mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    assert all(r.ok for r in rels.values()), rels
    idx = d.ler(SPD / "INDEX.md")
    assert len(idx.encode()) <= mod.TETO_INDEX
    assert "[BACKLOG.md](BACKLOG.md)" in idx and "[FORA-DE-ESCOPO.md](FORA-DE-ESCOPO.md)" in idx
    assert "ideia-0" in d.ler(SPD / "BACKLOG.md")
    assert "### Crítico" in d.ler(SPD / "BACKLOG.md"), "subseção do backlog se perdeu"
    todas = _todas(d)
    perdidas = [l for l in original.split("\n") if l.strip() and l not in todas]
    assert not perdidas, f"linha apagada: {perdidas[:2]}"


def test_enxugar_linha_longa_de_em_andamento_vira_curta_com_o_status(mod):
    longo = "detalhe " * 120
    so_andamento = ("# Índice de tarefas\n\n## Em andamento\n\n"
                    f"- [painel](../specs/painel.md) — tela {longo} — em andamento: fila construída dentro dele\n"
                    "- [curta](../specs/curta.md) — cabe — aberta\n"
                    + "".join(f"- [outra-{i}](../specs/o{i}.md) — {longo} — pausada: espera\n" for i in range(8)))
    d = _projeto(index=so_andamento)
    mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    idx = d.ler(SPD / "INDEX.md")
    assert len(idx.encode()) <= mod.TETO_INDEX
    curta = [l for l in idx.split("\n") if l.startswith("- [painel]")][0]
    assert "EM-ANDAMENTO.md" in curta and curta.endswith("em andamento: fila construída dentro dele")
    assert "- [curta](../specs/curta.md) — cabe — aberta" in idx, "mexeu em linha que já era curta"
    assert "tela detalhe" in d.ler(SPD / "EM-ANDAMENTO.md")
    assert len(mod._hook_um_item().abertas(idx)) == 2, "a trava parou de enxergar as abertas"


def test_enxugar_para_assim_que_cabe(mod):
    """Só o necessário: com o INDEX pequeno, nenhuma seção sai."""
    d = _projeto()
    mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    assert not d.eh_arquivo(SPD / "BACKLOG.md")


def test_enxugar_de_novo_acrescenta_sem_sobrescrever(mod):
    """2ª vez: o BACKLOG.md já existe — o item novo entra e o antigo continua lá."""
    d = _projeto(index=_index_gordo())
    mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    novo = "- ideia-nova — " + "x " * 3000 + "— aberta"
    d.gravar(SPD / "INDEX.md", d.ler(SPD / "INDEX.md").replace("## Backlog\n", "## Backlog\n\n" + novo + "\n", 1))
    mod.enxugar(RAIZ, hoje="2026-09-24", aplicar=True, disco=d)
    backlog = d.ler(SPD / "BACKLOG.md")
    assert "ideia-nova" in backlog and "ideia-0" in backlog
    assert d.ler(SPD / "INDEX.md").count("[BACKLOG.md](BACKLOG.md)") == 1


def test_enxugar_mapa_move_conexoes_e_deixa_os_nomes(mod):
    original = _mapa_gordo()
    d = _projeto(mapa=original)
    mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    mapa = d.ler(SPD / "MAPA.md")
    assert len(mapa.encode()) <= mod.TETO_MAPA
    assert "[CONEXOES.md](CONEXOES.md)" in mapa and "→ Serviço 0" in mapa and "→ Serviço 7" in mapa
    assert "📍 estado atual curto." in mapa
    todas = _todas(d)
    assert not [l for l in original.split("\n") if l.strip() and l not in todas]


def test_enxugar_dry_run_nao_escreve(mod):
    d = _projeto(index=_index_gordo(), mapa=_mapa_gordo())
    antes = dict(d.dados)
    rels = mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=False, disco=d)
    assert d.dados == antes and not any(r.gravou for r in rels.values())
    assert rels["index"].bytes_depois <= mod.TETO_INDEX


def test_rascunho_le_de_baixo_e_guarda_a_gravacao_so_nele(mod):
    d = _projeto()
    r = mod.Rascunho(d)
    r.gravar_bytes(SPD / "NOVO.md", b"novo")
    r.gravar_bytes(SPD / "MAPA.md", b"trocado")
    assert r.ler_bytes(SPD / "NOVO.md") == b"novo" and r.ler_bytes(SPD / "MAPA.md") == b"trocado"
    assert r.ler_bytes(SPD / "INDEX.md") == INDEX.encode("utf-8") and r.eh_arquivo(SPD / "INDEX.md")
    assert not d.eh_arquivo(SPD / "NOVO.md") and d.ler(SPD / "MAPA.md") == MAPA


def test_enxugar_nao_mexe_em_arquivo_com_conflito_de_merge(mod):
    d = _projeto(index="<<<<<<< HEAD\n" + _index_gordo() + "=======\n>>>>>>> x\n")
    rels = mod.enxugar(RAIZ, hoje="2026-09-23", aplicar=True, disco=d)
    assert not rels["index"].ok and not rels["index"].gravou


# --- forma em toda gravação (0.44.0): mesmo ABAIXO do teto -----------------------------------

def _mapa_whats():
    """Molde do MAPA real do Whats (2026-10-27): perto do teto, mas abaixo — antes nada se movia."""
    longo = "medir de novo com tráfego real " * 12
    return ("# Mapa de contexto — Proj\n\n## Onde estamos\n\n📍 **2026-10-27 — retomada** validada.\n\n"
            "## Próximo passo\n\n"
            "1. ⬜ **Pendências de 23/10** (`to-dolist.md`): opção A.\n"
            f"2. ⬜ **AC5 do pool**: com ≥ 30 respostas, {longo}\n"
            f"3. ⬜ sem título em negrito {longo}\n\n"
            "## Conexões\n\n"
            "- → Chatwoot: abre a conversa de handoff (`services/chatwoot.py`)\n"
            "- ← n8n: recebe o anexo (`POST /whatsapp/anexo`)\n"
            "- Detalhe (contratos, tokens, topologia local × Azure): [CONEXOES.md](CONEXOES.md)\n\n"
            "---\nAtualizado em 2026-10-27 (V15.2 em produção).\n")


def _com_conexoes(d):
    d.gravar(SPD / "CONEXOES.md", "# Conexões — Proj\n\n- detalhe antigo\n")
    return d


def test_forma_item_longo_do_proximo_passo_vira_titulo_com_ponteiro(mod):
    original = _mapa_whats()
    d = _projeto(mapa=original)
    assert len(original.encode()) < mod.TETO_MAPA
    rels = mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    assert rels["mapa"].ok, rels["mapa"].problemas
    mapa = d.ler(SPD / "MAPA.md")
    assert "2. ⬜ **AC5 do pool** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)\n" in mapa
    assert "1. ⬜ **Pendências de 23/10** (`to-dolist.md`): opção A.\n" in mapa, "mexeu em item curto"
    assert "3. ⬜ sem título em negrito" in mapa, "item sem título em negrito não tem o que deixar"
    detalhe = d.ler(SPD / "PROXIMO-PASSO.md")
    assert "**AC5 do pool**: com ≥ 30 respostas" in detalhe and "2026-10-27" in detalhe
    todas = _todas(d)
    assert not [l for l in original.split("\n") if l.strip() and l not in todas]


def test_forma_conexoes_so_nomes_quando_ha_conexoes_md(mod):
    original = _mapa_whats()
    d = _com_conexoes(_projeto(mapa=original))
    rels = mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    assert rels["mapa"].ok, rels["mapa"].problemas
    mapa = d.ler(SPD / "MAPA.md")
    assert ("- Detalhe em [CONEXOES.md](CONEXOES.md) (contratos, tokens, topologia), movido em 2026-10-27. "
            "Conexões: → Chatwoot · ← n8n.") in mapa
    assert "services/chatwoot.py" not in mapa
    assert mapa.rstrip("\n").endswith("---\nAtualizado em 2026-10-27 (V15.2 em produção)."), "rodapé saiu do MAPA"
    conexoes = d.ler(SPD / "CONEXOES.md")
    assert "services/chatwoot.py" in conexoes and "- detalhe antigo" in conexoes
    todas = _todas(d)
    assert not [l for l in original.split("\n") if l.strip() and l not in todas]


def test_forma_conexoes_sem_conexoes_md_e_abaixo_do_teto_nao_mexe(mod):
    d = _projeto(mapa=_mapa_whats())
    mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    assert "services/chatwoot.py" in d.ler(SPD / "MAPA.md")
    assert not d.eh_arquivo(SPD / "CONEXOES.md")


def test_forma_conexoes_do_molde_nao_move_comentario_nem_nenhuma(mod):
    molde = (REPO / "templates" / "MAPA.md").read_text(encoding="utf-8")          # o molde do kit, só leitura
    d = _com_conexoes(_projeto(mapa=molde))
    mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    assert d.ler(SPD / "MAPA.md") == molde


def test_forma_index_fechada_sai_mesmo_abaixo_do_teto(mod):
    d = _projeto()
    assert len(INDEX.encode()) < mod.TETO_INDEX
    rels = mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    assert rels["index"].ok and rels["index"].gravou
    idx = d.ler(SPD / "INDEX.md")
    assert "relatório" not in idx and "- [formatação](../specs/formatacao.md) — juntar linhas — aberta" in idx
    assert "pausada: aguardando layout" in idx and "login social" in idx
    assert "relatório" in d.ler(SPD / "INDEX-historico.md")


def test_forma_ja_aplicada_nao_muda_nada(mod):
    d = _com_conexoes(_projeto(mapa=_mapa_whats()))
    mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    antes = dict(d.dados)
    rels = mod.enxugar(RAIZ, hoje="2026-10-28", aplicar=True, disco=d)
    assert d.dados == antes and not any(r.gravou for r in rels.values())


def test_forma_preserva_crlf(mod):
    d = _projeto(mapa=_mapa_whats().replace("\n", "\r\n"))
    mod.enxugar(RAIZ, hoje="2026-10-27", aplicar=True, disco=d)
    bruto = d.ler_bytes(SPD / "MAPA.md")
    assert b"PROXIMO-PASSO.md" in bruto and b"\n" not in bruto.replace(b"\r\n", b"")


def test_comentario_nao_conta_no_teto(mod):
    """0.52.0: comentário `<!-- -->` do molde não é conteúdo da partida — 5,0 KB de texto + 1,8 KB de guia cabem no
    teto de 6 KB; o relatório mede conteúdo, e o aviso 'ainda acima' só sai pelo conteúdo."""
    coment = "<!-- " + "guia " * 360 + "-->\n"                      # ~1.800 B, como o molde
    corpo = "# Mapa de contexto — Proj\n\n## Onde estamos\n\n📍 " + "x" * 4900 + "\n\n## Próximo passo\n\n1. passo atual.\n"
    rel = mod.enxugar(RAIZ, hoje="2026-11-03", aplicar=False, disco=_projeto(mapa=coment + corpo))["mapa"]
    assert rel.ok and not rel.avisos, rel.avisos
    assert rel.bytes_antes == mod.bytes_de_conteudo(coment + corpo) < mod.TETO_MAPA
    assert mod.bytes_de_conteudo("a<!-- x\ny -->b") == 2


# ---- o disco de verdade e o processo (pasta montada uma vez) ------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("rodizio_partida") / "proj"
    sp = raiz / "docs" / "superpowers"
    sp.mkdir(parents=True)
    (sp / "MAPA.md").write_bytes(_mapa_gordo().replace("\n", "\r\n").encode("utf-8"))      # repo Windows: CRLF
    (sp / "INDEX.md").write_bytes(_index_gordo().encode("utf-8"))
    return raiz


def test_disco_de_verdade(mod, pasta):
    """O disco de verdade: o `enxugar` sem `--aplicar` não muda nem cria arquivo (o rascunho por cima do disco real);
    com `--aplicar` grava os destinos ao lado, mantendo o CRLF de cada arquivo."""
    sp = pasta / "docs" / "superpowers"
    antes = {p.name: p.read_bytes() for p in sp.iterdir()}
    rels = mod.enxugar(pasta, hoje="2026-11-18", aplicar=False)
    assert {p.name: p.read_bytes() for p in sp.iterdir()} == antes and not any(r.gravou for r in rels.values())
    rels = mod.enxugar(pasta, hoje="2026-11-18", aplicar=True)
    assert all(r.ok and r.gravou for r in rels.values()), rels
    assert (sp / "BACKLOG.md").is_file() and (sp / "CONEXOES.md").is_file()
    assert b"\n" not in (sp / "MAPA.md").read_bytes().replace(b"\r\n", b"")
    assert b"\r\n" in (sp / "CONEXOES.md").read_bytes()
    assert mod.bytes_de_conteudo((sp / "INDEX.md").read_bytes().decode("utf-8")) <= mod.TETO_INDEX


def test_processo_dry_run(pasta):
    r = subprocess.run([sys.executable, str(SCRIPT), "index", "--proj", str(pasta)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert "DRY-RUN" in r.stdout
