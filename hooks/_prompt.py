"""O pedido do owner como ele o escreveu — sem a marca que o app põe em volta do texto COLADO.

Por que existe (caso F-053, `docs/EVALS.md`): o pedido colado chega ao hook como
`<pasted_content id="6303">` + quebra de linha + o texto + `</pasted_content>` (forma lida na conversa real do
caso). Quem procurava o comando do kit no COMEÇO do pedido (`kit_primeiro.py`, `um_item_por_janela.py`) via a
marca, não o comando: o `superpowers:brainstorming` do `nova-feature` foi negado com "nenhum comando do kit rodou
ainda" e o um-item-por-janela não soube de que feature era o chat.

Só tira a marca; o texto do owner fica inteiro. Qualquer coisa que não seja texto → "".
"""
import re

RE_MARCA_DO_COLADO = re.compile(r"</?pasted_content\b[^>]*>[ \t]*\r?\n?")


def texto_do_pedido(prompt):
    """O pedido sem as marcas `<pasted_content …>` (abertura e fecho), em qualquer ponto do texto."""
    if not isinstance(prompt, str):
        return ""
    return RE_MARCA_DO_COLADO.sub("", prompt)
