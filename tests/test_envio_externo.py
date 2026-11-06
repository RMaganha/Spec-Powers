"""Envio externo nasce em modo de teste — benchmark MSIG_Agentes (2026-11-06), item 12.

Lá: `--dry-run` só mostra o resumo, `--enviar` usa um destino de teste e só `--enviar-real` manda ao destinatário
real; num envio com fallback, nunca pule um item em silêncio. Aqui a regra entra no baseline de segurança
(`templates/SEGURANCA.md`, seção 14), numa regra path-scoped que carrega ao tocar código de envio
(`templates/rules/envio-externo.md`) e na auditoria do `/mss-spec:seguranca`.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_baseline_de_seguranca_tem_a_secao_de_envio_externo():
    seg = (REPO / "templates" / "SEGURANCA.md").read_text(encoding="utf-8")
    assert "## 14. Envio externo" in seg
    for flag in ("--dry-run", "--enviar", "--enviar-real"):
        assert flag in seg, f"seção 14 sem a flag {flag}"
    assert "(padrão)" in seg.split("## 14.")[1].split("## Modelo")[0], "o dry-run não é declarado como padrão"
    assert "fallback nunca é silencioso" in seg.lower()
    assert "envio em massa" in seg.lower() and "idempotente" in seg.lower()


def test_regra_path_scoped_de_envio_externo():
    regra = REPO / "templates" / "rules" / "envio-externo.md"
    assert regra.exists(), "falta templates/rules/envio-externo.md"
    txt = regra.read_text(encoding="utf-8")
    fm = re.match(r"\A---\r?\n(.*?)\r?\n---", txt, re.S)
    assert fm and "paths:" in fm.group(1)
    globs = re.findall(r'-\s+"([^"]+)"', fm.group(1))
    assert any("email" in g for g in globs) and any("webhook" in g for g in globs), globs
    assert "--dry-run" in txt and "--enviar-real" in txt and "docs/SEGURANCA.md" in txt


def test_auditoria_de_seguranca_procura_envio_sem_modo_de_teste():
    cmd = (REPO / "commands" / "seguranca.md").read_text(encoding="utf-8")
    assert "envio externo" in cmd.lower() and "--enviar-real" in cmd and "fallback silencioso" in cmd
