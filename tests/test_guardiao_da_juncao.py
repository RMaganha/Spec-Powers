"""Guardião da junção — `templates/guardiao-da-juncao.ps1` recria `~/.claude/skills/mss-spec` quando ela some
ou aponta pra outro lugar, captura a evidência antes e nunca apaga pasta real (pendência "intermitência
pós-update": o app se atualiza sozinho e já derrubou a junção; quando ela some, o kit inteiro some).

O guarda vive FORA do kit: hook `SessionStart` no `settings.json` do usuário e tarefa do Agendador (logon +
hora em hora). Estes testes rodam o script de verdade, no PowerShell, contra pastas temporárias.
"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="junção é coisa do Windows")

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "guardiao-da-juncao.ps1"


def _rodar(alvo, link, log, sessao=False):
    args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT),
            "-Alvo", str(alvo), "-Link", str(link), "-Log", str(log)]
    if sessao:
        args.append("-Sessao")
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)


def _kit(tmp_path, nome="kit"):
    alvo = tmp_path / nome
    (alvo / "hooks").mkdir(parents=True)
    (alvo / "hooks" / "hooks.json").write_text("{}", encoding="utf-8")
    return alvo


def _juncao(link, destino):
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f'New-Item -ItemType Junction -Path "{link}" -Target "{destino}" | Out-Null'],
                   check=True, capture_output=True, timeout=60)


def _e_juncao(p):
    return bool(os.lstat(p).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _mesmo(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


@pytest.fixture()
def cenario(tmp_path):
    alvo = _kit(tmp_path)
    skills = tmp_path / "skills"
    skills.mkdir()
    return alvo, skills / "mss-spec", tmp_path / "guardiao.log"


# --- AC1: sumiu → recria, com evidência antes e aviso ao owner ------------------------------

def test_juncao_ausente_e_recriada_com_evidencia(cenario):
    alvo, link, log = cenario
    r = _rodar(alvo, link, log, sessao=True)
    assert r.returncode == 0, r.stderr
    assert _e_juncao(link) and _mesmo(link, alvo), "a junção não foi criada apontando pro kit"
    texto = log.read_text(encoding="utf-8")
    assert "evidencia estado=ausente" in texto, "não capturou a evidência antes de mexer"
    assert "recriou" in texto
    saida = json.loads(r.stdout.strip().splitlines()[-1])
    assert "refeita" in saida["systemMessage"] and "reabra" in saida["systemMessage"]


def test_tudo_certo_fica_calado(cenario):
    alvo, link, log = cenario
    _rodar(alvo, link, log)
    r = _rodar(alvo, link, log, sessao=True)
    assert r.returncode == 0 and not r.stdout.strip(), "avisou com a junção certa"
    assert log.read_text(encoding="utf-8").strip().splitlines()[-1].split(" ")[1] == "ok"


# --- AC2: nunca apaga; só o atalho é trocado -------------------------------------------------

def test_pasta_real_e_renomeada_nunca_apagada(cenario):
    alvo, link, log = cenario
    link.mkdir()
    (link / "coisa-do-owner.txt").write_text("nao apague", encoding="utf-8")
    r = _rodar(alvo, link, log)
    assert r.returncode == 0, r.stderr
    baks = list(link.parent.glob("mss-spec.bak-*"))
    assert len(baks) == 1 and (baks[0] / "coisa-do-owner.txt").read_text(encoding="utf-8") == "nao apague"
    assert _e_juncao(link) and _mesmo(link, alvo)
    assert "renomeou" in log.read_text(encoding="utf-8")


def test_juncao_errada_e_trocada_sem_tocar_o_destino(cenario, tmp_path):
    alvo, link, log = cenario
    outro = _kit(tmp_path, "outro-clone")
    (outro / "marca.txt").write_text("intacto", encoding="utf-8")
    _juncao(link, outro)
    r = _rodar(alvo, link, log)
    assert r.returncode == 0, r.stderr
    assert _mesmo(link, alvo), "a junção não passou a apontar pro kit"
    assert (outro / "marca.txt").read_text(encoding="utf-8") == "intacto", "o destino antigo foi tocado"
    texto = log.read_text(encoding="utf-8")
    assert "aponta-errado" in texto and "removeu" in texto and "recriou" in texto


def test_juncao_sem_hooks_e_refeita(cenario, tmp_path):
    """Junção que aponta pro lugar certo mas o kit não está lá inteiro (ex.: clone pela metade) conta como quebrada."""
    alvo, link, log = cenario
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    _juncao(link, vazio)
    _rodar(alvo, link, log)
    assert _mesmo(link, alvo)


# --- AC3: alvo ausente não cria nada; exit 0 sempre; script legível pelo PowerShell 5.1 ------

def test_alvo_ausente_nao_cria_e_avisa(tmp_path):
    alvo = tmp_path / "nao-existe"
    link = tmp_path / "skills" / "mss-spec"
    link.parent.mkdir()
    r = _rodar(alvo, link, tmp_path / "g.log", sessao=True)
    assert r.returncode == 0
    assert not link.exists(), "criou junção pra um alvo que não existe"
    assert "alvo-ausente" in (tmp_path / "g.log").read_text(encoding="utf-8")
    assert "clone do kit" in json.loads(r.stdout.strip().splitlines()[-1])["systemMessage"]


def test_sem_alvo_usa_o_clone_onde_o_script_mora(tmp_path):
    """A 1ª rodada de verdade falhou aqui: `$PSScriptRoot` vazio no default do param (PowerShell 5.1 com -File).
    Sem `-Alvo`, o alvo tem de ser o repo acima de templates/ — este clone."""
    link = tmp_path / "skills" / "mss-spec"
    link.parent.mkdir()
    log = tmp_path / "g.log"
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT),
                        "-Link", str(link), "-Log", str(log)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=90)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr
    assert _e_juncao(link) and _mesmo(link, REPO), "sem -Alvo o guardião não apontou pro clone do kit"
    assert "recriou" in log.read_text(encoding="utf-8")


def test_script_e_ascii_puro():
    """PowerShell 5.1 lê .ps1 sem BOM como ANSI: acento no script viraria lixo. Mensagens sem acento, de propósito."""
    texto = SCRIPT.read_text(encoding="utf-8")
    fora = sorted({c for c in texto if ord(c) > 127})
    assert not fora, f"caracteres fora do ASCII no .ps1: {fora}"


def test_documentado_e_apontado_pelo_doctor():
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    assert "guardiao-da-juncao.ps1" in doc and "Register-ScheduledTask" in doc, \
        "hooks/README.md não documenta o guardião nem como registrar a tarefa"
    doctor = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    assert "guardiao-da-juncao.ps1" in doctor, "o check 1 do doctor não aponta o guardião quando o kit não resolve"
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "guardiao-da-juncao.ps1" in leiame, "LEIA-ME não ensina a ligar o guardião numa máquina nova"
