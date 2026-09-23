# 2026-09-23 — cerca de publicação por destino e teto do CLAUDE.md (0.31.0 · 0.31.1)

**Conversamos:** logo depois da 0.30.0, o owner disse que negar todo merge/push estava travando o dia
a dia — *"eu só preciso ser alertado dos comandos git, mas você poderia rodar"*; push em
homologação/produção continua dele. No fecho, perguntou por que o `CLAUDE.md` tem teto e se mexer
ali pode quebrar algo.

**Pivôs:**
1. de "negar tudo" (0.26.0) para "por destino": só o push que faz deploy segue negado — o registro
   da 0.30.0 já tinha mostrado o `git merge-base` (só leitura) negado como `git merge`;
2. "alerta" virou `ask`, o único canal que aparece no Desktop (o `systemMessage` não aparece; o
   `additionalContext` depende de relato) — validado ao vivo, o owner viu e aprovou;
3. o falso positivo do heredoc (mensagem de commit citando `docker push`) ficou de propósito: pular o
   corpo do heredoc abriria um furo numa cerca que falha fechada — commit vai por `-F arquivo`;
4. o teto de 8 KB tinha me feito espremer a linha de Git palavra por palavra, e a 1ª tentativa
   apagou duas frases que o smoke test exige; o owner escolheu subir pra 10 KB e, acima disso, só
   mover bloco — com as frases-chave de cada regra travadas por teste (F-029).

**Rejeitado:** "só avisar" (dependeria de eu relatar — prosa, como antes do F-022) · configuração de
branches protegidas por projeto (regra única) · pular heredoc na cerca · tirar o teto.

**Fizemos:** 0.31.0 (`2a2cf71`, merge `ebff839`) e 0.31.1 (`6d57013`, merge `edda6f3`) — os merges
feitos por mim com a aprovação do owner (a própria cerca nova), os pushes pelo owner. Suíte
530 → 572. MAPA reconciliado em `af15eb3`. Tropeço meu: depois de a regra mudar, ainda dei os
comandos de merge pro owner rodar na mão — hábito da regra antiga.

**Próximo:** atualizar a branch `docs/catalogo-do-kit` com a `main` e pôr o `CATALOGO.html` em dia
(janela nova); `python hooks/_registro.py resumo` depois de algumas sessões.
