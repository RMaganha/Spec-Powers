# upgrade — sincroniza projeto com a evolução dos templates (design)

Data: 2026-07-16 · feature do próprio kit mss-spec.

## Objetivo
Comando `/mss-spec:upgrade` que traz um projeto existente pra versão atual do kit com o **mínimo de interação** — atualiza os arquivos de referência sozinho e **mescla** o `CLAUDE.md`/`AMBIENTE.md` sem perder o do owner; só conflito real pergunta.

## Problema
O kit evolui rápido (0.1→0.7 em duas semanas). Projetos feitos antes ficam pra trás. Na 0.7.0 isso já apareceu (o `/mss-spec:frontend` passou a re-sincronizar o `FRONTEND.md` a cada run). Falta generalizar pra todos os arquivos, **sem destruir a customização do projeto**.

## Critérios de aceite
- DADO um `docs/SEGURANCA.md` desatualizado, QUANDO rodo `/mss-spec:upgrade`, ENTÃO ele é atualizado pra versão do template, sem me perguntar.
- DADO uma regra nova no kit que falta no `CLAUDE.md` do projeto, QUANDO rodo o upgrade, ENTÃO a regra é ACRESCENTADA e o resto do meu `CLAUDE.md` fica intacto.
- DADO uma regra que diverge (kit diz A, projeto editou pra B), QUANDO rodo o upgrade, ENTÃO ele PERGUNTA qual fica (único caso que interage).
- DADO um `get_connection.py` (código) desatualizado, QUANDO rodo o upgrade, ENTÃO ele só mostra o diff e avisa — NÃO aplica sozinho.

## Design
Comando `commands/upgrade.md` (`disable-model-invocation`). Três categorias:
1. **Referência (só-do-kit):** SEGURANCA · ESTRUTURA · FRONTEND · Docker · gitignore → atualiza sozinho.
2. **`CLAUDE.md` + `AMBIENTE.md`:** mescla por seção/regra — acrescenta o que falta do kit, mantém o do owner, conflito → pergunta.
3. **Código (`get_connection.py`):** só avisa (diff), não aplica.

Não commita — deixa no working tree pro owner revisar via `git diff`.
**Limite:** sem a versão antiga do template, a mescla é por seção/regra (não 3-way); na dúvida, mantém o do owner.

## Fora de escopo
Merge automático de código · rollback (o git já faz) · guardar histórico de versões de template.

## Arquivos tocados
- novo `commands/upgrade.md`

## Histórico
- 2026-07-16 — criado: design do upgrade (aprovado no chat).
