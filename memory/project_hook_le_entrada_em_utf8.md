---
name: project_hook_le_entrada_em_utf8
description: Os hooks do kit leem o evento só por hooks/_entrada.py (bytes do stdin em UTF-8); teste de hook com acento manda bytes UTF-8 crus, sem PYTHONIOENCODING, e o vermelho se prova contra os hooks da main
gatilho: quando escrever ou mexer em hook que lê o evento, ou no teste dele com texto acentuado
conferida: 2026-11-17 — confirmada — fonte: hooks/_entrada.py:20
metadata:
  type: project
---

Desde a 0.64.0 (2026-11-16), os 18 hooks leem o evento com `ler_evento()` de `hooks/_entrada.py`, que faz
`json.loads(sys.stdin.buffer.read().decode("utf-8"))`. Hook novo usa o mesmo — nunca `json.load(sys.stdin)`: o
`tests/test_hook_entrada_utf8.py` acusa pelo nome o hook registrado em `hooks/hooks.json` que lê `sys.stdin` em texto.

**Why:** lido como texto, o Python filho no Windows (sem `PYTHONIOENCODING`) decodificava o pipe como cp1252, e
"Já decidido — não reabrir:" virava `J\xc3\xa1 decidido \xe2€”…`: o `passagem_de_conversa.py` devolvia
"falta no bloco `Já decidido…`" num bloco que tinha o título, e nenhum gatilho com acento casava nos outros hooks.
Os testes antigos mandavam `json.dumps(evento)` — ASCII puro (`á`) — e nunca viram o problema.

**How to apply:**
- Teste de hook com acento: rode o hook por subprocess com `json.dumps(evento, ensure_ascii=False).encode("utf-8")`
  e o ambiente **sem** `PYTHONIOENCODING`/`PYTHONUTF8`. No Linux do CI o pipe já é UTF-8 e o teste só passa; quem
  discrimina é o Windows.
- Prove o vermelho contra o código antigo: `git archive main hooks | tar -x -C <rascunho>` e rode o hook de lá. E leia
  a mensagem do vermelho, não só o FAILED — caso F-070 (teste que falhava por comparar bytes com texto).
- Texto que não é UTF-8 (inclusive com a marca `\xef\xbb\xbf` no começo) faz o hook sair calado (falha aberta):
  ver [[project_hook_pelo_powershell_chega_com_marca]].
