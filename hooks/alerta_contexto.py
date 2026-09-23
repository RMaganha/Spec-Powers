"""Hook do mss-spec: ALERTA DE CONTEXTO — avisa quando a janela passa de 75%.

Por que existe: a janela aberta pra UM assunto vira bola de neve — "pra fechar A preciso entender B",
B puxa C — e ninguém percebe o contexto enchendo até a compactação automática, que só dispara perto
do limite e resume o que não devia. A regra "um assunto por janela" é prosa; a % da janela é número.

Contrato:
- eventos `UserPromptSubmit` (antes de cada prompt do owner) e `PostToolUse` (no meio de uma rodada
  longa sem prompt); **nunca bloqueia** (rede, não cerca);
- a % sai do transcript (`transcript_path`): a ÚLTIMA mensagem do assistente fora de subagente
  (`isSidechain` falso) traz `message.usage`; contexto = `input_tokens` + `cache_read_input_tokens` +
  `cache_creation_input_tokens`. Hook não recebe a % pronta — só a statusline recebe;
- tamanho da janela (hook não o recebe): `MSS_JANELA_TOKENS` › `CLAUDE_CODE_AUTO_COMPACT_WINDOW` ›
  `[1m]` no id ou uso acima de 200 mil → 1.000.000 › família 5 (Opus/Sonnet/Fable, id sem `[1m]`) →
  1.000.000 › 200.000 (4.x, Haiku). O id `claude-opus-5-5` é 1M e assumir 200 mil deu 92% onde a
  janela mostrava 18% (F-027);
- limiar: `MSS_ALERTA_CONTEXTO_PCT` (padrão 75 — escolha do owner; a doc da Anthropic não fixa
  número). Avisa UMA vez por faixa (75 · 85 · 95) por sessão, somando os dois eventos; a % caiu
  abaixo do limiar (depois de `/compact`) → rearma;
- saída: `additionalContext` (o assistente abre a resposta com o aviso — `systemMessage` não aparece
  no app Desktop) + `systemMessage` (aparece no terminal);
- ignora evento de subagente (`agent_id`): a janela dele não é a do owner;
- **falha ABERTA**: qualquer defeito → exit 0 calado.

Escape consciente, só do owner: `MSS_ALERTA_CONTEXTO_OFF=1`.
"""
import json
import os
import re
import sys
import tempfile


# Registro local do que este hook FEZ (`hooks/_registro.py`). Nunca muda a decisão: sem o módulo,
# ou com qualquer defeito dele, o hook segue exatamente igual.
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
            _registrar("alerta_contexto", decisao, detalhe, evento)
    except Exception:                                # noqa: BLE001
        pass

ENV_DESLIGA = "MSS_ALERTA_CONTEXTO_OFF"
ENV_PCT = "MSS_ALERTA_CONTEXTO_PCT"
ENV_JANELA = "MSS_JANELA_TOKENS"
ENV_COMPACTA = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"   # a janela onde a compactação mira (doc do Claude Code)
PCT_PADRAO = 75
JANELA_PADRAO = 200_000
JANELA_1M = 1_000_000
PASSO_FAIXA = 10            # 75 → 85 → 95: reaviso escalonado, não a cada mensagem
CAUDA_BYTES = 512 * 1024    # só a cauda do transcript: a última mensagem do assistente está no fim
EVENTOS = ("UserPromptSubmit", "PostToolUse")


def _inteiro(valor, padrao, minimo, maximo):
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        return padrao
    return n if minimo <= n <= maximo else padrao


def _linhas_da_cauda(caminho):
    """Linhas completas do fim do arquivo (a 1ª, possivelmente cortada, é descartada)."""
    with open(caminho, "rb") as f:
        f.seek(0, os.SEEK_END)
        tamanho = f.tell()
        inicio = max(0, tamanho - CAUDA_BYTES)
        f.seek(inicio)
        bruto = f.read()
    linhas = bruto.decode("utf-8", errors="replace").splitlines()
    return linhas[1:] if inicio > 0 else linhas


def uso_atual(caminho):
    """(tokens de contexto, modelo) da última resposta do assistente na janela principal, ou None."""
    for linha in reversed(_linhas_da_cauda(caminho)):
        linha = linha.strip()
        if not linha:
            continue
        try:
            entrada = json.loads(linha)
        except ValueError:
            continue
        if not isinstance(entrada, dict) or entrada.get("type") != "assistant":
            continue
        if entrada.get("isSidechain"):
            continue
        msg = entrada.get("message")
        uso = msg.get("usage") if isinstance(msg, dict) else None
        if not isinstance(uso, dict):
            continue
        total = sum(int(uso.get(k) or 0) for k in
                    ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if total <= 0:
            continue
        return total, str(msg.get("model") or "")
    return None


RE_FAMILIA = re.compile(r"claude-(opus|sonnet|fable)-(\d+)", re.I)


def janela_de(tokens, modelo, ambiente):
    """Hook não recebe o tamanho da janela (doc do Claude Code): sai do owner ou do id do modelo."""
    for env in (ENV_JANELA, ENV_COMPACTA):
        override = _inteiro(ambiente.get(env), 0, 1_000, 100_000_000)
        if override:
            return override
    if re.search(r"\[1m\]", modelo, re.I) or tokens > JANELA_PADRAO:
        return JANELA_1M
    familia = RE_FAMILIA.search(modelo)
    if familia and int(familia.group(2)) >= 5:
        return JANELA_1M             # família 5 (Opus/Sonnet/Fable): 1M, e o id vem sem `[1m]` (F-027)
    return JANELA_PADRAO


def faixa_de(pct, limiar):
    """Faixa atingida (75, 85, 95…) ou None abaixo do limiar."""
    if pct < limiar:
        return None
    return limiar + ((int(pct) - limiar) // PASSO_FAIXA) * PASSO_FAIXA


def _estado(sessao):
    nome = re.sub(r"[^A-Za-z0-9_-]", "_", str(sessao))[:120]
    return os.path.join(tempfile.gettempdir(), f"mss_alerta_contexto_{nome}.txt")


def _ler_faixa(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _gravar_faixa(caminho, faixa):
    try:
        if faixa is None:
            if os.path.exists(caminho):
                os.remove(caminho)
            return
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(str(faixa))
    except OSError:
        pass


def _mil(n):
    return f"{round(n / 1000):,}".replace(",", ".") + " mil"


def mensagens(pct, tokens, janela, limiar):
    """(additionalContext pro assistente, systemMessage pro terminal)."""
    numero = f"{pct:.0f}% ({_mil(tokens)} de {_mil(janela)} tokens)"
    pro_assistente = (
        f"[mss-spec] JANELA DE CONTEXTO EM {numero} — passou do limiar de {limiar}%.\n"
        "Avise o owner disso em UMA linha, no início da sua próxima mensagem a ele, antes de qualquer "
        "outra coisa. Daqui em diante: não abra assunto novo nem frente paralela nesta janela; feche o "
        "passo em curso; anote o estado em `docs/superpowers/MAPA.md` (onde parou, próximo passo); "
        "o que sobrar — inclusive o 'pra fechar isto preciso entender aquilo' — vai pro "
        "`/mss-spec:to-dolist adicionar <assunto>`; e recomende `/clear` (ou janela nova) antes do "
        "próximo assunto. Entender algo ainda necessário = subagente, que devolve só o resumo."
    )
    pro_owner = (f"[mss-spec] Janela em {numero}. Feche o assunto, anote o estado e rode /clear "
                 f"antes do próximo.")
    return pro_assistente, pro_owner


def responder(evento, ambiente=None):
    """dict pra imprimir, ou None = silêncio. Qualquer defeito → None (falha aberta)."""
    try:
        ambiente = os.environ if ambiente is None else ambiente
        if str(ambiente.get(ENV_DESLIGA, "")).strip():
            return None
        if not isinstance(evento, dict):
            return None
        nome_evento = evento.get("hook_event_name")
        if nome_evento not in EVENTOS or evento.get("agent_id"):
            return None
        transcript = evento.get("transcript_path")
        if not isinstance(transcript, str) or not os.path.isfile(transcript):
            return None
        uso = uso_atual(transcript)
        if uso is None:
            return None
        tokens, modelo = uso
        janela = janela_de(tokens, modelo, ambiente)
        limiar = _inteiro(ambiente.get(ENV_PCT), PCT_PADRAO, 1, 99)
        pct = min(100.0, tokens * 100.0 / janela)
        faixa = faixa_de(pct, limiar)
        estado = _estado(evento.get("session_id") or transcript)
        anterior = _ler_faixa(estado)
        if faixa is None:
            if anterior is not None:
                _gravar_faixa(estado, None)          # caiu abaixo (compactou): rearma
            return None
        if anterior is not None and faixa <= anterior:
            return None                              # já avisou nesta faixa
        _gravar_faixa(estado, faixa)
        _anotar("avisou", f"faixa={faixa} pct={pct:.0f} janela={janela} modelo={modelo}", evento)
        pro_assistente, pro_owner = mensagens(pct, tokens, janela, limiar)
        return {
            "systemMessage": pro_owner,
            "hookSpecificOutput": {
                "hookEventName": nome_evento,
                "additionalContext": pro_assistente,
            },
        }
    except Exception:                                # noqa: BLE001 — falha ABERTA
        return None


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
