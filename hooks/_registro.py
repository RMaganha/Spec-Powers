"""Registro local do que os hooks do mss-spec FIZERAM — uma linha JSON por vez que um hook agiu.

Por que existe: os hooks decidem calados e ninguém consegue dizer quanto eles valem — quantas
vezes a cerca de publicação barrou um push, se o recall aponta a memória certa, se o alerta de
contexto calcula a janela certa (caso F-027: o hook dizia 92% onde o app mostrava 18%, e só
apareceu porque o owner comparou com o print). Com o registro, isso vira número.

Contrato:
- grava só quando o hook AGE (negou · bloqueou · avisou · injetou · lembrou); passar calado não
  gera linha;
- cada linha: `quando`, `hook`, `decisao`, `detalhe` (código curto escolhido pelo hook, ≤ 240
  caracteres), `projeto` (só o nome da pasta) e `sessao` (8 primeiros caracteres do id);
- **NUNCA** grava o texto do prompt nem a linha de comando — o `detalhe` é sempre montado pelo
  hook a partir de rótulos dele (`git push`, `faixa=85 …`, ponteiros do recall);
- **nunca levanta exceção**: registro que não grava não muda decisão nenhuma (inclusive a da
  cerca de publicação, que falha FECHADA);
- arquivo acima de `TETO_BYTES` → rodízio pra `.1` (o `.1` anterior é descartado);
- fica em `~/.claude/mss-spec/registro-hooks.jsonl` (um por máquina, fora de qualquer repo);
  `MSS_REGISTRO_ARQUIVO` troca o caminho (a suíte usa pra não sujar o do owner).

Escape consciente, só do owner: `MSS_REGISTRO_OFF=1`.

Leitura: `python hooks/_registro.py resumo [--dias N]` — contagem por hook e decisão.
"""
import argparse
import datetime
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ENV_DESLIGA = "MSS_REGISTRO_OFF"
ENV_ARQUIVO = "MSS_REGISTRO_ARQUIVO"
TETO_BYTES = 1_000_000
TETO_DETALHE = 240


def caminho(ambiente=None):
    ambiente = os.environ if ambiente is None else ambiente
    escolhido = str(ambiente.get(ENV_ARQUIVO) or "").strip()
    if escolhido:
        return Path(escolhido)
    return Path.home() / ".claude" / "mss-spec" / "registro-hooks.jsonl"


def _projeto(evento, ambiente):
    raiz = ambiente.get("CLAUDE_PROJECT_DIR") or (evento or {}).get("cwd") or ""
    return os.path.basename(os.path.normpath(str(raiz))) if str(raiz).strip() else ""


def registrar(hook, decisao, detalhe="", evento=None, ambiente=None):
    """Anexa uma linha. Qualquer defeito → não grava, calado."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA) or "").strip():
            return
        evento = evento if isinstance(evento, dict) else {}
        linha = {
            "quando": datetime.datetime.now().isoformat(timespec="seconds"),
            "hook": str(hook),
            "decisao": str(decisao),
            "detalhe": " ".join(str(detalhe or "").split())[:TETO_DETALHE],
            "projeto": _projeto(evento, ambiente),
            "sessao": str(evento.get("session_id") or "")[:8],
        }
        alvo = caminho(ambiente)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if alvo.exists() and alvo.stat().st_size > TETO_BYTES:
            os.replace(alvo, alvo.with_name(alvo.name + ".1"))
        with open(alvo, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except Exception:                                # noqa: BLE001 — registro nunca derruba hook
        return


def ler(ambiente=None):
    """Linhas do `.1` e do atual, em ordem; linha ilegível é pulada."""
    alvo = caminho(ambiente)
    linhas = []
    for arquivo in (alvo.with_name(alvo.name + ".1"), alvo):
        try:
            texto = arquivo.read_text(encoding="utf-8")
        except OSError:
            continue
        for bruto in texto.splitlines():
            try:
                item = json.loads(bruto)
            except ValueError:
                continue
            if isinstance(item, dict):
                linhas.append(item)
    return linhas


def resumo(linhas, dias=None):
    if dias:
        corte = (datetime.datetime.now() - datetime.timedelta(days=dias)).isoformat(timespec="seconds")
        linhas = [l for l in linhas if str(l.get("quando", "")) >= corte]
    if not linhas:
        return "Nenhum registro de hook" + (f" nos últimos {dias} dias." if dias else ".")
    vezes = Counter((l.get("hook", "?"), l.get("decisao", "?")) for l in linhas)
    ultima = {}
    detalhes = defaultdict(Counter)
    for l in linhas:
        chave = (l.get("hook", "?"), l.get("decisao", "?"))
        ultima[chave] = max(ultima.get(chave, ""), str(l.get("quando", "")))
        if l.get("detalhe"):
            detalhes[chave][l["detalhe"]] += 1
    saida = [f"Registro dos hooks — {len(linhas)} ações"
             + (f" nos últimos {dias} dias" if dias else "") + ":", ""]
    for chave, n in vezes.most_common():
        hook, decisao = chave
        saida.append(f"{hook:<22} {decisao:<9} {n:>5}×   última: {ultima[chave]}")
        for detalhe, m in detalhes[chave].most_common(3):
            saida.append(f"{'':<22}   {m:>4}×  {detalhe}")
    return "\n".join(saida)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="Registro local do que os hooks do mss-spec fizeram.")
    ap.add_argument("modo", choices=["resumo"])
    ap.add_argument("--dias", type=int, default=None, help="só os últimos N dias")
    args = ap.parse_args(argv)
    print(f"Arquivo: {caminho()}")
    print(resumo(ler(), args.dias))
    return 0


if __name__ == "__main__":
    sys.exit(main())
