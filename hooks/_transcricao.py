"""Leitura do transcript (`.jsonl`) pelos hooks do mss-spec: o que o assistente GRAVOU nesta conversa.

Usado pelo `diario_junto.py` (memória sem diário) e pelo `capturar_nudge.py` (captura recente). Só lê;
qualquer defeito devolve lista vazia — quem chama decide o que fazer com o vazio (os dois liberam).
"""
import json

FERRAMENTAS_DE_ESCRITA = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def gravacoes(transcript_path):
    """[(timestamp_iso, ferramenta, caminho)] de cada Write/Edit/MultiEdit/NotebookEdit do assistente,
    fora de subagente (`isSidechain`), na ordem do transcript. Lista vazia se não der pra ler."""
    saida = []
    if not isinstance(transcript_path, str) or not transcript_path.strip():
        return saida
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for linha in f:
                if '"tool_use"' not in linha:
                    continue
                try:
                    reg = json.loads(linha)
                except ValueError:
                    continue
                if not isinstance(reg, dict) or reg.get("type") != "assistant" or reg.get("isSidechain"):
                    continue
                ts = reg.get("timestamp") if isinstance(reg.get("timestamp"), str) else ""
                for bloco in (reg.get("message") or {}).get("content") or []:
                    if not isinstance(bloco, dict) or bloco.get("type") != "tool_use":
                        continue
                    nome = bloco.get("name")
                    if nome not in FERRAMENTAS_DE_ESCRITA:
                        continue
                    entrada = bloco.get("input") or {}
                    caminho = entrada.get("file_path") if isinstance(entrada, dict) else None
                    if isinstance(caminho, str) and caminho.strip():
                        saida.append((ts, nome, caminho))
    except Exception:                                # noqa: BLE001
        return []
    return saida
