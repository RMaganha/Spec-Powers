---
name: project_dogfood_gerador_diff_antes_depois
description: Gerador/CLI do kit — antes de fechar, rode no repo REAL e faça diff da saída antiga × nova; teste com fixture não vê o que só o projeto de verdade tem
gatilho: quando fechar mudança em gerador ou CLI do kit
metadata:
  type: project
---

Ao mexer num **gerador** do kit (`templates/mapa_neural.py` e afins), o teste com fixture **não é o
fim**: antes de fechar, rode o gerador **no repositório real** e compare a saída **antes × depois**
(`git show <principal>:<script> > /tmp/antes.py`, roda os dois com `--out` separados, `diff`).

**Why:** fixture só contém o que eu imaginei; o repo real contém o que eu não imaginei. Nos 4 consertos
da 0.16.0, o diff no próprio kit destampou **dois bugs que nenhum teste pegaria**:
- a pasta **`hooks/` estava invisível** no mapa do kit — ela não está na lista de camadas do molde, e
  ninguém tinha percebido porque o mapa "parecia completo";
- um endpoint fantasma **`GET /x`** vindo de um decorator citado **dentro de um comentário** do próprio
  código (documentação virando API) — daí os regex de rota passarem a exigir o decorator no **início da
  linha**.

**How to apply:** gerou saída derivada (mapa, dossiê, relatório)? O gate é *diff no repo real*, não só
suíte verde. Leia **cada linha** do diff e explique cada uma: linha que você não sabe explicar é bug.
O que o diff revelar vira teste antes de fechar.

Relacionado: [[feedback_testar_js_gerado_node_check]] (suíte verde ≠ saída correta — lá o parse do JS,
aqui o conteúdo do que foi extraído) e [[project_parse_md_do_kit_descartar_comentario]] (o outro achado
da mesma rodada).
