# Plano — comando guardado inteiro (2026-11-12, nível médio)

Spec: `docs/specs/comando-guardado-inteiro.md`. Execução nesta conversa, uma tarefa por vez, teste antes do código.

1. **Detector** (critérios 1 e 2) — `hooks/_comando_inteiro.py`: acha comando ou SQL com reticências em bloco de
   código e em trecho entre crases; não conta `*****`, intervalo do git nem marcador entre `<` e `>`.
   Teste: `tests/test_hook_comando_inteiro.py`.
2. **Conferência ao gravar** (critérios 1 e 3) — chamada de dentro do `hooks/regra_antes_de_gravar.py`; só
   `memory/*.md` e `memory/sessions/*.md`; só o que a gravação traz de novo (o que já estava cortado no arquivo
   não conta); nega uma vez por arquivo e por conversa; falha aberta; escape `MSS_COMANDO_INTEIRO_OFF=1`.
3. **Medição antes de ligar** — rodar o detector nas anotações e diários deste projeto e conferir cada achado à mão.
4. **Regra na captura** (critério 4) — uma frase no passo 2 do modo capturar de `commands/memory.md`; teste de
   presença da frase.
5. **Anotações antigas** (critério 5) — `templates/memoria_indice.py verificar` avisa quantas têm comando com
   reticências, sem alterar nenhuma e sem mudar o código de saída.
6. **Fecho** — `hooks/README.md`, `CHANGELOG.md`, versão 0.60.0 nos dois manifestos, "Estado atual" da spec,
   decisão 23 apontando para a spec, suíte inteira.
