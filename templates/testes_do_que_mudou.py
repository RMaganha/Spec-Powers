"""Testes do que mudou — escolhe, pelo que mudou na branch, quais arquivos de teste rodar na máquina.

Regra 9 do kit (2026-11-17): na máquina roda só o teste do que mudou; a suíte inteira roda no CI. Quem escolhe os
testes é este script, não o assistente no olho.

Uso (na raiz do projeto):
    python "${CLAUDE_PLUGIN_ROOT}/templates/testes_do_que_mudou.py"            # mostra os testes e o comando
    python "${CLAUDE_PLUGIN_ROOT}/templates/testes_do_que_mudou.py" --rodar    # roda o pytest só com eles

O que mudou = commits da branch desde a principal (`main`/`master`) + o que está por commitar (inclusive arquivo
novo). Um arquivo de teste entra quando: ele mesmo mudou; cita o nome do arquivo mudado (`memoria_tabela.py`,
`bug.md`); ou importa o módulo dele (`from app.services.pedido import …`, `import memoria_tabela`). Mudou a
configuração do pytest (`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`) → todos.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

CONFIG_DO_PYTEST = {"conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"}
PASTAS_FORA = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "site-packages", ".tox"}


def _e_teste(caminho):
    nome = Path(caminho).name
    return nome.endswith(".py") and (nome.startswith("test_") or nome.endswith("_test.py"))


def _cita(texto, caminho):
    """O teste cita o arquivo. `.py`: o nome inteiro basta (`memoria_tabela.py`). Outro tipo (`.md`, `.json`): a
    pasta vem junto do nome (`commands/bug.md` ou `"commands" / "bug.md"`) — o nome solto costuma ser só texto."""
    p = Path(caminho)
    nome = re.escape(p.name)
    if p.suffix == ".py" or len(p.parts) == 1:
        padrao = r"(?<![\w.-])" + nome + r"(?![\w-])"
    else:
        padrao = r"(?<![\w.-])" + re.escape(p.parent.name) + r"""["']?\s*/\s*["']?""" + nome + r"(?![\w-])"
    return re.search(padrao, texto) is not None


def _vale_para(config, teste):
    """Configuração do pytest vale para os testes da pasta dela (e de baixo); a da raiz, para todos."""
    pasta = Path(config).parent
    return pasta == Path(".") or pasta in Path(teste).parents


def _importa(texto, caminho):
    """`import x` / `from x import` / `from a.b.x import`, com x = o módulo do arquivo .py."""
    p = Path(caminho)
    if p.suffix != ".py":
        return False
    pontilhado = ".".join(p.with_suffix("").parts)
    modulo = re.escape(p.stem)
    padrao = (r"^\s*(?:from|import)\s+(?:[\w.]+\.)?" + modulo + r"\b"
              + "|" + r"(?<![\w.])" + re.escape(pontilhado) + r"\b")
    return re.search(padrao, texto, re.M) is not None


def escolher(mudados, testes):
    """{arquivo de teste: [motivos]} — `testes` é {caminho do teste: texto}."""
    escolhidos = {}

    def marcar(teste, motivo):
        escolhidos.setdefault(teste, []).append(motivo)

    for mudado in mudados:
        mudado = mudado.replace("\\", "/")
        nome = Path(mudado).name
        if nome in CONFIG_DO_PYTEST:
            for teste in testes:
                if _vale_para(mudado, teste):
                    marcar(teste, f"a configuração do pytest mudou ({mudado})")
        if mudado in testes:
            marcar(mudado, "o próprio teste mudou")
            continue
        for teste, texto in testes.items():
            if _cita(texto, mudado):
                marcar(teste, f"cita {nome}")
            elif _importa(texto, mudado):
                marcar(teste, f"importa {Path(mudado).stem}")
    return escolhidos


def achar_testes(proj):
    proj = Path(proj)
    testes = {}
    for p in proj.rglob("*.py"):
        rel = p.relative_to(proj)
        if PASTAS_FORA & set(rel.parts[:-1]) or not _e_teste(p):
            continue
        try:
            testes[rel.as_posix()] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return testes


def _git(proj, *args):
    r = subprocess.run(["git", "-C", str(proj), *args], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def _principal(proj):
    for nome in ("main", "master"):
        if _git(proj, "rev-parse", "--verify", "--quiet", nome)[0] == 0:
            return nome
    return None


def mudados(proj, base=None):
    """Arquivos mudados: commits desde a principal + o que está por commitar (inclui arquivo novo)."""
    base = base or _principal(proj)
    nomes = set()
    if base:
        codigo, saida = _git(proj, "diff", "--name-only", f"{base}...HEAD")
        if codigo == 0:
            nomes.update(l.strip() for l in saida.splitlines() if l.strip())
    codigo, saida = _git(proj, "status", "--porcelain", "--untracked-files=all")
    for linha in saida.splitlines():
        caminho = linha[3:].strip()
        if " -> " in caminho:
            caminho = caminho.split(" -> ", 1)[1]
        if caminho:
            nomes.add(caminho.strip('"'))
    return sorted(nomes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Escolhe os testes pelo que mudou na branch.")
    ap.add_argument("--proj", default=".")
    ap.add_argument("--base", default=None, help="branch principal (padrão: main ou master)")
    ap.add_argument("--rodar", action="store_true", help="roda o pytest só com os testes escolhidos")
    args = ap.parse_args(argv)
    proj = Path(args.proj).resolve()
    lista = mudados(proj, args.base)
    testes = achar_testes(proj)
    escolhidos = escolher(lista, testes)
    print(f"Mudou: {len(lista)} arquivo(s). Testes escolhidos: {len(escolhidos)} de {len(testes)}.")
    for teste in sorted(escolhidos):
        print(f"  {teste} — {'; '.join(dict.fromkeys(escolhidos[teste]))}")
    sem = [m for m in lista if m.endswith(".py") and not _e_teste(m) and not escolher([m], testes)]
    if sem:
        print("Sem teste que cite: " + ", ".join(sem))
    if not escolhidos:
        print("Nenhum teste cobre o que mudou.")
        return 0
    comando = [sys.executable, "-m", "pytest", *sorted(escolhidos), "-q"]
    print("Comando: python -m pytest " + " ".join(sorted(escolhidos)) + " -q")
    if not args.rodar:
        return 0
    sys.stdout.flush()
    return subprocess.run(comando, cwd=proj).returncode


if __name__ == "__main__":
    sys.exit(main())
