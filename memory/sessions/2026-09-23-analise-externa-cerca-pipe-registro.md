# 2026-09-23 — análise externa do kit → cerca do pipe e registro dos hooks (0.30.0)

**Conversamos:** o owner trouxe duas análises do kit feitas por outras IAs (ChatGPT e Gemini, só a
partir do catálogo) e pediu levantamento, sem mexer em nada: o que é bom ou ruim nos nossos cenários.

**Pivôs:**
1. de 25 sugestões para uma tabela de veredito — cruzadas com `decisoes.md`, o "Fora de escopo" e o
   código, metade já existia ou contrariava decisão tomada (runtime YAML, recall semântico,
   `doctor --fix-safe`, tokens, stack genérica);
2. "qual o ganho hoje, em caso real?" → as 4 recomendadas viraram exemplo concreto do próprio repo;
3. "precisamos ter certeza que agrega e não prejudica" → a 2ª checagem derrubou o release em script
   (o F-025 é na hora do commit; o release em prosa pegou o `63b1de3`) e o `divergir` em escada (já
   são 3-5 subagentes; parar quando concordam lê âncora compartilhada como consenso) — caso **F-028**.
   O release em script foi trocado pela cerca do pipe, que a própria linha do EVALS já prescrevia;
4. o registro entrou com 4 salvaguardas escritas como teste antes do código (sem prompt/comando,
   registro quebrado não muda decisão, só quando age, latência).

**Rejeitado:** release em script · `divergir` em escada · runtime declarativo · tabela central de
políticas · recall semântico · `doctor --fix-safe` · contexto em tokens · stack genérica · to-do em
Jira/Boards. O 3 do owner ("poucos fluxos") saiu por decisão dele: projeto interno, o time pergunta.

**Fizemos:** 0.30.0 em 2 commits (`2c65166` cerca do pipe, `538d5fd` registro + release), suíte
472 → 530, nenhum teste existente alterado; as duas cercas negaram comandos meus ao vivo e o registro
gravou a 1ª linha real. Tropeços: heredoc com acento e regex não-raw (backspace no hook) e o teste de
orçamento do MAPA (2 blocos de histórico — movido pro `MAPA-historico.md`, não apagado).

**Próximo:** merge/push pelo owner; `python hooks/_registro.py resumo` depois de algumas sessões
(o recall acerta? alguma cerca deu falso bloqueio?); CATALOGO quando `docs/catalogo-do-kit` entrar.
