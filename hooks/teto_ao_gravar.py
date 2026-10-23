"""Hook do mss-spec: TETO AO GRAVAR — o excesso da partida sai na hora em que entra.

Por que existe (caso F-030, `docs/EVALS.md`): quem escreve no MAPA/INDEX (`/mss-spec:mapa`, `nova-feature`,
`memory capturar`) só acrescenta, e ninguém tirava. O `doctor` media, o hook de abertura avisava, e o Whats
chegou a 160 KB de partida mesmo assim — porque o conserto dependia de alguém lembrar de rodar o rodízio.
Aqui o conserto roda na própria gravação.

Contrato:
- evento `PostToolUse`; age só quando a ferramenta gravou `docs/superpowers/MAPA.md`,
  `docs/superpowers/INDEX.md` ou o `CLAUDE.md` da raiz (`CLAUDE_PROJECT_DIR` › `cwd`): Write/Edit/MultiEdit
  pelo `file_path`; Bash/PowerShell quando o comando cita o nome do arquivo **e** o arquivo mudou agora
  (`mudou_agora`: mtime dentro de `JANELA_S` e `(tamanho, mtime_ns)` diferente do último visto nesta sessão) —
  ler (`wc -c CLAUDE.md`, `cat INDEX.md`) cita o arquivo mas não é gravação;
- MAPA/INDEX acima do teto → `templates/rodizio_partida.py enxugar --aplicar` (move, nunca apaga, com
  conservação conferida; para assim que cabe) + `additionalContext` dizendo o que foi pra onde e pra
  reler antes do próximo Edit; se o que sobra é conteúdo vivo, pede o resumo pra spec;
- `CLAUDE.md` acima de 10,0 KB → só avisa (F-029: nunca comprimir): com a marca das regras do kit, manda
  mover um bloco inteiro com ponteiro; sem a marca, manda rodar `/mss-spec:upgrade` (migração);
- arquivo com conflito de merge → não toca e avisa;
- **nunca bloqueia**; **falha ABERTA**: defeito → exit 0 calado.

Escape consciente, só do owner: `MSS_TETO_OFF=1`.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path


try:
    _PASTA_HOOKS = os.path.dirname(os.path.abspath(__file__))
    if _PASTA_HOOKS not in sys.path:
        sys.path.insert(0, _PASTA_HOOKS)
    from _registro import registrar as _registrar
except Exception:                                    # noqa: BLE001
    _registrar = None


def _anotar(decisao, detalhe, evento):
    try:
        if _registrar is not None:
            _registrar("teto_ao_gravar", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass


ENV_DESLIGA = "MSS_TETO_OFF"
TETO_CLAUDE_MD = 10000
JANELA_S = 120                       # gravação "agora" = mtime de até 2 min atrás
# cópia de hooks/regras_do_kit.py (hooks não importam um do outro; um teste trava a igualdade)
MARCA = "<!-- mss-spec:regras-do-kit -->"
ALVOS = ("docs/superpowers/MAPA.md", "docs/superpowers/INDEX.md", "CLAUDE.md")
TOOLS_DE_ARQUIVO = ("Write", "Edit", "MultiEdit")
TOOLS_DE_SHELL = ("Bash", "PowerShell")


def _motor():
    caminho = Path(__file__).resolve().parent.parent / "templates" / "rodizio_partida.py"
    spec = importlib.util.spec_from_file_location("rodizio_partida", caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _norm(p):
    return os.path.normcase(os.path.abspath(p))


def tocados(evento, raiz):
    """Quais dos ALVOS esta gravação pode ter mexido (relativos à raiz)."""
    entrada = evento.get("tool_input")
    if not isinstance(entrada, dict):
        return []
    tool = evento.get("tool_name")
    if tool in TOOLS_DE_ARQUIVO:
        caminho = entrada.get("file_path")
        if not isinstance(caminho, str) or not caminho.strip():
            return []
        alvo = _norm(caminho if os.path.isabs(caminho) else os.path.join(raiz, caminho))
        return [rel for rel in ALVOS if alvo == _norm(os.path.join(raiz, *rel.split("/")))]
    if tool in TOOLS_DE_SHELL:
        comando = entrada.get("command")
        if not isinstance(comando, str):
            return []
        if _e_git(comando):                          # `git add/commit/diff CLAUDE.md` cita o arquivo, não o grava
            return []
        return [rel for rel in ALVOS if rel.rsplit("/", 1)[-1] in comando]
    return []


def _e_git(comando):
    """True se a 1ª palavra do comando é `git` (ou `git.exe`): comando de git nunca conta como gravação."""
    palavras = comando.split()
    return bool(palavras) and re.sub(r"\.exe$", "", palavras[0].replace("\\", "/").rsplit("/", 1)[-1].lower()) == "git"


def _kb(n):
    return f"{n / 1000:.1f} KB".replace(".", ",")


def _medida(n, teto):
    """'10,5 KB (teto 10,0 KB)'; quando o arredondado empata com o teto mas passou dele, mostra bytes."""
    if n > teto and _kb(n) == _kb(teto):
        return f"{n:,} B (teto {teto:,} B)".replace(",", ".")
    return f"{_kb(n)} (teto {_kb(teto)})"


def _tem_marca(raiz):
    """True se o `CLAUDE.md` da raiz tem a linha-marca (depois de tirar o BOM; `strip()` leva o CR)."""
    try:
        with open(os.path.join(raiz, "CLAUDE.md"), encoding="utf-8", errors="replace") as f:
            texto = f.read().lstrip("\ufeff")
    except (OSError, UnicodeError):
        return False
    return any(linha.strip() == MARCA for linha in texto.splitlines())


def _arquivo_de_estado(sessao):
    seguro = re.sub(r"[^\w-]", "_", str(sessao or "sem-sessao"))[:80]
    return os.path.join(tempfile.gettempdir(), f"mss_teto_{seguro}.json")


def _ler_estado(sessao):
    try:
        with open(_arquivo_de_estado(sessao), encoding="utf-8") as f:
            dado = json.load(f)
        return dado if isinstance(dado, dict) else {}
    except Exception:                                # noqa: BLE001
        return {}


def _versao(caminho):
    """[tamanho, mtime_ns] do arquivo, ou None se não existe."""
    try:
        st = os.stat(caminho)
        return [st.st_size, st.st_mtime_ns]
    except OSError:
        return None


def marcar_visto(caminho, sessao):
    """Guarda a versão (tamanho, mtime_ns) que o hook acabou de ver, pra não tratar a mesma de novo."""
    try:
        versao = _versao(caminho)
        if versao is None:
            return
        estado = _ler_estado(sessao)
        estado[_norm(caminho)] = versao
        with open(_arquivo_de_estado(sessao), "w", encoding="utf-8") as f:
            json.dump(estado, f)
    except Exception:                                # noqa: BLE001
        pass


def mudou_agora(caminho, sessao, agora=None):
    """True se `caminho` foi gravado agora: mtime dentro de `JANELA_S` E versão diferente da última vista
    nesta sessão. Só confere; quem grava o estado é `marcar_visto`."""
    try:
        agora = time.time() if agora is None else agora
        versao = _versao(caminho)
        if versao is None or not (0 <= agora - versao[1] / 1e9 <= JANELA_S):
            return False
        return _ler_estado(sessao).get(_norm(caminho)) != versao
    except Exception:                                # noqa: BLE001
        return False


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip() or not isinstance(evento, dict):
            return None
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        if not isinstance(raiz, str) or not raiz.strip() or not os.path.isdir(raiz):
            return None
        alvos = tocados(evento, raiz)
        sessao = evento.get("session_id")
        if evento.get("tool_name") in TOOLS_DE_SHELL:
            # citar o arquivo no comando não é gravar: só conta o que mudou agora e ainda não foi visto
            alvos = [a for a in alvos if mudou_agora(os.path.join(raiz, *a.split("/")), sessao)]
        if not alvos:
            return None
        try:
            return _agir(evento, raiz, alvos)
        finally:
            for a in alvos:                          # a versão que o hook viu (já enxugada) não dispara de novo
                marcar_visto(os.path.join(raiz, *a.split("/")), sessao)
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


def _agir(evento, raiz, alvos):
    """O que fazer com os ALVOS gravados: enxugar MAPA/INDEX e avisar do CLAUDE.md."""
    partes, detalhes = [], []
    if any(a != "CLAUDE.md" for a in alvos):
        motor = _motor()
        for qual, r in motor.enxugar(Path(raiz), aplicar=True).items():
            nome = "MAPA.md" if qual == "mapa" else "INDEX.md"
            if r.passos:
                partes.append(f"{nome} {_kb(r.bytes_antes)} → {_kb(r.bytes_depois)}: " + " · ".join(r.passos))
                detalhes.append(f"{nome}={r.bytes_antes}->{r.bytes_depois}")
            partes += r.problemas + r.avisos
    if "CLAUDE.md" in alvos:
        caminho = os.path.join(raiz, "CLAUDE.md")
        n = os.path.getsize(caminho) if os.path.isfile(caminho) else 0
        if n > TETO_CLAUDE_MD:
            medida = f"CLAUDE.md com {_medida(n, TETO_CLAUDE_MD)}"
            if _tem_marca(raiz):
                partes.append(f"{medida}: mova um bloco INTEIRO com ponteiro — regra de tipo de arquivo pra "
                              "`.claude/rules/<x>.md` com `paths:`, procedimento pra `docs/` — e nunca comprima a "
                              "redação de uma regra (F-029). Não movi nada aqui: é julgamento.")
            else:
                partes.append(f"{medida}: rode `/mss-spec:upgrade` pra migrar o CLAUDE.md (as regras do kit passam "
                              "a vir do plugin). Não movi nada aqui; nunca comprima a redação de uma regra (F-029).")
            detalhes.append(f"CLAUDE.md={n}")
    if not partes:
        return None
    moveu = any("→" in p for p in partes)
    texto = ("[mss-spec] teto da partida (F-030): " + " | ".join(partes)
             + (". Nada foi apagado (o `git diff` mostra). Releia o arquivo antes do próximo Edit nele — o texto "
                "mudou de lugar." if moveu else "")
             + " Avise o owner em 1 linha.")
    _anotar("moveu" if moveu else "avisou", " ".join(detalhes)[:200], evento)
    return {
        "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": texto},
        "systemMessage": "[mss-spec] teto da partida: " + " | ".join(p[:120] for p in partes)[:300],
    }


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)
    saida = responder(evento)
    if saida is not None:
        print(json.dumps(saida))
    sys.exit(0)                                      # SEMPRE 0 — não bloqueia


if __name__ == "__main__":
    main()
