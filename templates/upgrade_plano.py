"""upgrade_plano.py — a abertura do /mss-spec:upgrade: o que o projeto precisa, em que ordem, e o que o git tem
pendente (0.54.0). SÓ LÊ — não grava arquivo nem mexe no git.

Por que: até a 0.53.0 o upgrade rodava em até 3 passes separados (migração do CLAUDE.md · conversão do to-dolist
· categorias 1-3), cada um terminando sozinho e exigindo árvore limpa e branch nova. No Transportes V2
(2026-11-09) isso virou 3 conversas, todas paradas na mesma pergunta sobre 3 arquivos modificados sem commit em
outra branch. Agora o upgrade trata tudo numa rodada: este script diz, na abertura, o status de cada passe, a
ordem dos que se aplicam e a situação do git — e o trabalho pendente do owner é guardado UMA vez (stash) e
devolvido no fim, nunca commitado. Spec: docs/superpowers/specs/2026-07-16-upgrade-design.md ("Estado atual").

O que ele olha:
- migração do CLAUDE.md  → a marca `<!-- mss-spec:regras-do-kit -->` (a mesma do `migrar_claude_md.py`);
- to-dolist              → `converter_to_dolist.checar` (os achados do formato antigo, com as palavras dele);
- categorias 1-3         → sempre se aplicam;
- git                    → branch atual, principal (`main`/`master`), remoto, modificados e não rastreados.

Uso:  python upgrade_plano.py checar [--proj DIR]
      (exit 0 sempre; o relatório é pro assistente abrir a conversa do upgrade com ele)
"""
import argparse
import importlib.util
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PASTA = Path(__file__).resolve().parent
MARCA = "<!-- mss-spec:regras-do-kit -->"
PRINCIPAIS = ("main", "master")
BRANCH_DO_UPGRADE = "chore/upgrade-kit"

NOME_MIGRACAO = "migração do CLAUDE.md"
NOME_TO_DOLIST = "to-dolist"
NOME_CATEGORIAS = "categorias 1-3"


@dataclass
class Passe:
    nome: str
    motivos: list = field(default_factory=list)


@dataclass
class SituacaoGit:
    branch: str
    principal: str            # "" quando nenhuma das conhecidas existe
    remoto: bool
    modificados: list
    nao_rastreados: list

    @property
    def suja(self) -> bool:
        return bool(self.modificados or self.nao_rastreados)


@dataclass
class Plano:
    migracao: str             # "falta" · "feita" · "sem CLAUDE.md"
    achados_to_dolist: list
    passes: list
    git: object               # SituacaoGit ou None (fora de git)

    def status(self) -> str:
        if self.migracao == "sem CLAUDE.md":
            mig = f"{NOME_MIGRACAO} — (sem CLAUDE.md)"
        else:
            mig = f"{NOME_MIGRACAO} {'⬜' if self.migracao == 'falta' else '✓'}"
        todo = f"{NOME_TO_DOLIST} {'⬜' if self.achados_to_dolist else '✓'}"
        return f"{mig} · {todo} · categorias ⬜"


# ------------------------------------------------------------------ leitura do projeto

def _conversor():
    caminho = PASTA / "converter_to_dolist.py"
    spec = importlib.util.spec_from_file_location("converter_to_dolist", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _migracao(proj: Path) -> str:
    p = proj / "CLAUDE.md"
    if not p.is_file():
        return "sem CLAUDE.md"
    texto = p.read_bytes().decode("utf-8", errors="replace")
    return "feita" if any(l.strip() == MARCA for l in texto.splitlines()) else "falta"


def _git(proj: Path, *args):
    """Saída de um comando git SÓ DE LEITURA; None se o git não respondeu (fora de repo, sem git no PATH)."""
    try:
        r = subprocess.run(["git", *args], cwd=proj, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def situacao_git(proj: Path):
    if _git(proj, "rev-parse", "--is-inside-work-tree") is None:
        return None
    branch = (_git(proj, "branch", "--show-current") or "").strip()
    principal = next((b for b in PRINCIPAIS if _git(proj, "rev-parse", "--verify", "-q", "refs/heads/" + b)), "")
    remoto = bool((_git(proj, "remote") or "").strip())
    modificados, nao_rastreados = [], []
    for linha in (_git(proj, "status", "--porcelain", "--untracked-files=normal") or "").splitlines():
        if len(linha) < 4:
            continue
        caminho = linha[3:].strip().strip('"')
        if linha.startswith("??"):
            nao_rastreados.append(caminho)
        else:
            modificados.append(caminho)
    return SituacaoGit(branch, principal, remoto, sorted(modificados), sorted(nao_rastreados))


def montar(proj) -> Plano:
    proj = Path(proj)
    migracao = _migracao(proj)
    achados = _conversor().checar(proj)
    passes = []
    if migracao == "falta":
        passes.append(Passe(NOME_MIGRACAO, ["o CLAUDE.md não tem a marca " + MARCA]))
    if achados:
        passes.append(Passe(NOME_TO_DOLIST, list(achados)))
    passes.append(Passe(NOME_CATEGORIAS, ["sempre: referência · mescla do CLAUDE.md/AMBIENTE.md/MAPA.md · código"]))
    return Plano(migracao, list(achados), passes, situacao_git(proj))


# ------------------------------------------------------------------ relatório

def _linha_git(g) -> str:
    if g is None:
        return "Git: sem git neste projeto — o upgrade não abre branch nem commita; mostre o diff ao owner no fim."
    partes = [f"Git: branch `{g.branch or '(HEAD destacado)'}`"]
    if g.principal:
        partes.append(f"principal `{g.principal}`" + (" (com remoto: `git pull --ff-only` antes)" if g.remoto
                                                      else " (sem remoto: não há o que puxar)"))
    else:
        partes.append("principal: não sei (não há `main` nem `master`) — pergunte ao owner qual é")
    if g.suja:
        partes.append(f"{len(g.modificados)} modificado(s): " + (", ".join(g.modificados) or "—"))
        partes.append(f"{len(g.nao_rastreados)} não rastreado(s): " + (", ".join(g.nao_rastreados) or "—"))
        partes.append("→ guardar uma vez (`git stash push` dos modificados, com o OK do owner) antes de abrir a "
                      f"`{BRANCH_DO_UPGRADE}`; devolver no fim (`git stash pop`), nunca commitar")
    else:
        partes.append("árvore limpa — nada a guardar")
    if g.branch and g.principal and g.branch != g.principal:
        partes.append(f"no fim, a principal volta pra `{g.branch}` (`git merge --ff-only`) e o owner fica nela")
    return " · ".join(partes)


def relatorio(plano: Plano) -> str:
    linhas = [plano.status(), "", "Passes, nesta ordem, na mesma conversa (um commit por passe):"]
    for i, p in enumerate(plano.passes, 1):
        linhas.append(f"{i}. {p.nome}")
        for m in p.motivos:
            linhas.append(f"   - {m}")
    linhas += ["", _linha_git(plano.git)]
    return "\n".join(linhas)


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="modo", required=True)
    c = sub.add_parser("checar", help="status dos passes, ordem e situação do git (só lê)")
    c.add_argument("--proj", default=".", help="raiz do projeto (padrão: pasta atual)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(relatorio(montar(a.proj)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
