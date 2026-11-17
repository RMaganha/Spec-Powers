"""F-050 (2026-11-03): a Segurança da Informação não permite script PowerShell nem tarefa agendada na máquina
do owner — ao registrar a tarefa do guardião da 0.51.0 ele foi contactado pela infra. O kit não pode carregar
`.ps1`, e o assistente não pode executar nem propor esses comandos. A cerca é a memória
`project_sandbox_do_claude_nao_registra_tarefa_agendada` com `gatilho_comando`, que o `git_publicacao.py`
aplica (F-034): o comando é negado uma vez por sessão com a memória no motivo.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MEMORIA = REPO / "memory" / "project_sandbox_do_claude_nao_registra_tarefa_agendada.md"


def _regex():
    fm = MEMORIA.read_text(encoding="utf-8")
    m = re.search(r"^gatilho_comando: (.+)$", fm, re.M)
    assert m, "a memória perdeu o gatilho_comando"
    return re.compile(m.group(1))


@pytest.mark.parametrize("comando", [
    "Register-ScheduledTask -TaskName 'mss-spec guardiao da juncao' -Action $acao",
    "schtasks /Create /SC HOURLY /MO 1 /TN x /TR y",
    "$svc = New-Object -ComObject Schedule.Service",
    'powershell -NoProfile -ExecutionPolicy Bypass -File "C:/x/guardiao-da-juncao.ps1" -Sessao',
    "powershell.exe -File C:\\a\\b.ps1",
    "New-Item -ItemType Junction -Path $l -Target $t",
])
def test_comando_proibido_casa_a_memoria(comando):
    assert _regex().search(comando), f"a memória não barra: {comando}"


@pytest.mark.parametrize("comando", [
    "Get-ScheduledTask 'mss-spec guardiao da juncao'",
    "schtasks /Query /TN x",
    "git status --short",
    "python -m pytest tests/ -q",
    'powershell -NoProfile -Command "Get-Content x.log -Tail 3"',
    "python templates/memoria_indice.py verificar",
])
def test_leitura_e_python_passam(comando):
    assert not _regex().search(comando), f"a memória barra o que é só leitura: {comando}"
