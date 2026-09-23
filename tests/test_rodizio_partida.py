"""rodizio_partida.py — MAPA com 2 blocos por seção, INDEX só com tarefa viva; o resto vai pro histórico.

Por que: o MAPA do Whats tinha 89.651 bytes (teto 6.000) e o INDEX 61.399 (teto 7.000) — relidos em toda
janela. O template já prometia "atual + 1 anterior" e "fechada sai"; faltava quem MOVESSE. Move, nunca apaga;
dry-run por padrão; conservação byte a byte antes de gravar.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "rodizio_partida.py"

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


def _mod():
    spec = importlib.util.spec_from_file_location("rodizio_partida", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path, mapa=MAPA, index=INDEX):
    raiz = tmp_path / "proj"
    sp = raiz / "docs" / "superpowers"
    sp.mkdir(parents=True)
    (sp / "MAPA.md").write_text(mapa, encoding="utf-8")
    (sp / "INDEX.md").write_text(index, encoding="utf-8")
    return raiz


# --- mapa -------------------------------------------------------------------------------

def test_mapa_mantem_dois_blocos_por_secao_e_move_o_resto(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok, rel.problemas
    mapa = (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8")
    assert "anterior 1" in mapa and "anterior 2" not in mapa and "anterior 3" not in mapa
    assert "passo anterior." in mapa and "passo velho." not in mapa
    assert "outro projeto — não mexer." in mapa
    assert mapa.count("\n---\n") == 2
    hist = (raiz / "docs" / "superpowers" / "MAPA-historico.md").read_text(encoding="utf-8")
    assert '## 2026-09-15 — rodízio de "Onde estamos"' in hist and "anterior 2" in hist and "anterior 3" in hist
    assert '## 2026-09-15 — rodízio de "Próximo passo"' in hist and "passo velho." in hist
    assert hist.index("anterior 2") < hist.index("anterior 3"), "ordem original preservada (mais novo em cima)"
    assert rel.movidas == 4           # linhas de conteúdo movidas (anterior 2 ×2, anterior 3, passo velho); `---` não conta
    assert rel.bytes_depois < rel.bytes_antes


def test_mapa_dry_run_nao_escreve(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    antes = (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes()
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=False)
    assert rel.ok and rel.movidas == 4
    assert (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes() == antes
    assert not (raiz / "docs" / "superpowers" / "MAPA-historico.md").exists()


def test_mapa_bloco_unico_e_intocado_e_nada_a_mover(tmp_path):
    mod = _mod()
    curto = "# Mapa\n\n## Onde estamos\n\nsó um bloco.\n\n## Próximo passo\n\n1. só um.\n\n## Conexões\n\n- x\n"
    raiz = _projeto(tmp_path, mapa=curto)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok and rel.movidas == 0
    assert (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8") == curto
    assert not (raiz / "docs" / "superpowers" / "MAPA-historico.md").exists()


def test_mapa_historico_existente_recebe_prepend_depois_do_titulo(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    hist = raiz / "docs" / "superpowers" / "MAPA-historico.md"
    hist.write_text("<!-- comentário -->\n\n# Histórico do mapa — Proj\n\n## 2026-08-01 — antigo\n\nvelho.\n", encoding="utf-8")
    mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    t = hist.read_text(encoding="utf-8")
    assert t.startswith("<!-- comentário -->\n\n# Histórico do mapa — Proj\n")
    assert t.index("2026-09-15") < t.index("2026-08-01")


def test_mapa_avisa_quando_ainda_acima_do_teto(tmp_path):
    mod = _mod()
    gordo = MAPA.replace("linha 2 do atual.", "linha 2 do atual. " + "x" * 7000)
    raiz = _projeto(tmp_path, mapa=gordo)
    rel = mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok and any("ainda acima do teto" in a and "conteúdo" in a for a in rel.avisos)
    assert "x" * 7000 in (raiz / "docs" / "superpowers" / "MAPA.md").read_text(encoding="utf-8"), "bloco atual NUNCA se corta"


def test_mapa_preserva_crlf(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path, mapa=MAPA.replace("\n", "\r\n"))
    mod.rodizio_mapa(raiz, hoje="2026-09-15", aplicar=True)
    assert b"\r\n" in (raiz / "docs" / "superpowers" / "MAPA.md").read_bytes()
    assert b"\r\n" in (raiz / "docs" / "superpowers" / "MAPA-historico.md").read_bytes()


# --- index ------------------------------------------------------------------------------

def test_index_move_so_fechada_e_preserva_fora_de_escopo(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=True)
    assert rel.ok, rel.problemas
    idx = (raiz / "docs" / "superpowers" / "INDEX.md").read_text(encoding="utf-8")
    assert "[formatação]" in idx and "pausada: aguardando layout" in idx and "**em andamento**" in idx
    assert "[relatório]" not in idx and "[alerta]" not in idx
    assert "login social — fechada de propósito" in idx, "'Fora de escopo' NUNCA se move"
    assert "## Backlog" in idx, "cabeçalho fica mesmo esvaziado"
    hist = (raiz / "docs" / "superpowers" / "INDEX-historico.md").read_text(encoding="utf-8")
    assert "## 2026-09-15 — fechadas" in hist and "[relatório]" in hist and "[alerta]" in hist
    assert rel.movidas == 2


def test_index_dry_run_nao_escreve(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path)
    antes = (raiz / "docs" / "superpowers" / "INDEX.md").read_bytes()
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=False)
    assert rel.ok and rel.movidas == 2
    assert (raiz / "docs" / "superpowers" / "INDEX.md").read_bytes() == antes


def test_index_reusa_a_regra_de_status_do_hook():
    """`pausada` não é fechada; `fechada` em negrito também conta — a mesma leitura do um_item_por_janela."""
    mod = _mod()
    assert mod.fechada("- [x](../specs/x.md) — obj — **fechada** (2026-09-01)")
    assert not mod.fechada("- [x](../specs/x.md) — obj — pausada: espera")
    assert not mod.fechada("- [x](../specs/x.md) — obj — aberta")


def test_index_avisa_abertas_que_nao_cabem(tmp_path):
    mod = _mod()
    muitas = "# Índice\n\n## Em andamento\n" + "".join(
        f"- [tarefa {i}](../specs/t{i}.md) — {'objetivo ' * 30} — aberta\n" for i in range(40))
    raiz = _projeto(tmp_path, index=muitas)
    rel = mod.rodizio_index(raiz, hoje="2026-09-15", aplicar=True)
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


def _todas(raiz):
    sp = raiz / "docs" / "superpowers"
    return "\n".join(p.read_text(encoding="utf-8") for p in sp.glob("*.md"))


def test_enxugar_index_move_secoes_e_fica_abaixo_do_teto(tmp_path):
    mod = _mod()
    original = _index_gordo()
    raiz = _projeto(tmp_path, index=original)
    rels = mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    assert all(r.ok for r in rels.values()), rels
    sp = raiz / "docs" / "superpowers"
    idx = (sp / "INDEX.md").read_text(encoding="utf-8")
    assert len(idx.encode()) <= mod.TETO_INDEX
    assert "[BACKLOG.md](BACKLOG.md)" in idx and "[FORA-DE-ESCOPO.md](FORA-DE-ESCOPO.md)" in idx
    assert "ideia-0" in (sp / "BACKLOG.md").read_text(encoding="utf-8")
    assert "### Crítico" in (sp / "BACKLOG.md").read_text(encoding="utf-8"), "subseção do backlog se perdeu"
    todas = _todas(raiz)
    perdidas = [l for l in original.split("\n") if l.strip() and l not in todas]
    assert not perdidas, f"linha apagada: {perdidas[:2]}"


def test_enxugar_linha_longa_de_em_andamento_vira_curta_com_o_status(tmp_path):
    mod = _mod()
    longo = "detalhe " * 120
    so_andamento = ("# Índice de tarefas\n\n## Em andamento\n\n"
                    f"- [painel](../specs/painel.md) — tela {longo} — em andamento: fila construída dentro dele\n"
                    "- [curta](../specs/curta.md) — cabe — aberta\n"
                    + "".join(f"- [outra-{i}](../specs/o{i}.md) — {longo} — pausada: espera\n" for i in range(8)))
    raiz = _projeto(tmp_path, index=so_andamento)
    mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    sp = raiz / "docs" / "superpowers"
    idx = (sp / "INDEX.md").read_text(encoding="utf-8")
    assert len(idx.encode()) <= mod.TETO_INDEX
    curta = [l for l in idx.split("\n") if l.startswith("- [painel]")][0]
    assert "EM-ANDAMENTO.md" in curta and curta.endswith("em andamento: fila construída dentro dele")
    assert "- [curta](../specs/curta.md) — cabe — aberta" in idx, "mexeu em linha que já era curta"
    assert "tela detalhe" in (sp / "EM-ANDAMENTO.md").read_text(encoding="utf-8")
    hook = mod._hook_um_item()
    assert len(hook.abertas(idx)) == 2, "a trava parou de enxergar as abertas"


def test_enxugar_para_assim_que_cabe(tmp_path):
    """Só o necessário: com o INDEX pequeno, nenhuma seção sai."""
    mod = _mod()
    raiz = _projeto(tmp_path)
    mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    assert not (raiz / "docs" / "superpowers" / "BACKLOG.md").exists()


def test_enxugar_de_novo_acrescenta_sem_sobrescrever(tmp_path):
    """2ª vez: o BACKLOG.md já existe — o item novo entra e o antigo continua lá."""
    mod = _mod()
    raiz = _projeto(tmp_path, index=_index_gordo())
    mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    sp = raiz / "docs" / "superpowers"
    idx = (sp / "INDEX.md").read_text(encoding="utf-8")
    novo = "- ideia-nova — " + "x " * 3000 + "— aberta"
    idx = idx.replace("## Backlog\n", "## Backlog\n\n" + novo + "\n", 1)
    (sp / "INDEX.md").write_text(idx, encoding="utf-8")
    mod.enxugar(raiz, hoje="2026-09-24", aplicar=True)
    backlog = (sp / "BACKLOG.md").read_text(encoding="utf-8")
    assert "ideia-nova" in backlog and "ideia-0" in backlog
    assert (sp / "INDEX.md").read_text(encoding="utf-8").count("[BACKLOG.md](BACKLOG.md)") == 1


def test_enxugar_mapa_move_conexoes_e_deixa_os_nomes(tmp_path):
    mod = _mod()
    original = _mapa_gordo()
    raiz = _projeto(tmp_path, mapa=original)
    mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    sp = raiz / "docs" / "superpowers"
    mapa = (sp / "MAPA.md").read_text(encoding="utf-8")
    assert len(mapa.encode()) <= mod.TETO_MAPA
    assert "[CONEXOES.md](CONEXOES.md)" in mapa and "→ Serviço 0" in mapa and "→ Serviço 7" in mapa
    assert "📍 estado atual curto." in mapa
    todas = _todas(raiz)
    assert not [l for l in original.split("\n") if l.strip() and l not in todas]


def test_enxugar_dry_run_nao_escreve(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path, index=_index_gordo(), mapa=_mapa_gordo())
    antes = _todas(raiz)
    rels = mod.enxugar(raiz, hoje="2026-09-23", aplicar=False)
    assert _todas(raiz) == antes and not any(r.gravou for r in rels.values())
    assert rels["index"].bytes_depois <= mod.TETO_INDEX


def test_enxugar_nao_mexe_em_arquivo_com_conflito_de_merge(tmp_path):
    mod = _mod()
    raiz = _projeto(tmp_path, index="<<<<<<< HEAD\n" + _index_gordo() + "=======\n>>>>>>> x\n")
    rels = mod.enxugar(raiz, hoje="2026-09-23", aplicar=True)
    assert not rels["index"].ok and not rels["index"].gravou
