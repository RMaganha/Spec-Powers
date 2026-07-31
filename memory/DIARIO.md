<!-- Índice do diário de sessão do próprio kit mss-spec (dogfood). Ver templates/DIARIO.md.
     1 linha por captura, mais recentes em cima; o detalhe vive em memory/sessions/. -->

# Diário de sessão — mss-spec

## 2026-07-31
- [mapa-neural-limite-e-camadas] 2ª rodada (0.17.0): fim do corte silencioso (limite 200 + `… (+N)`) e regra única "se está no repo, está no mapa" (camada por conteúdo, árvore descendo, exceções = ferramenta · docs/memory · `.gitignore` · `--ignorar`); pivôs: o owner cortou minha seção declarativa por complexidade e corrigiu 2 premissas (n8n entra; subpasta com código tem que ser mapeada); bug silencioso meu: `text=True` no Windows mandou `backup/\r` pro git e matou o filtro sem erro → sessions/2026-07-31-mapa-neural-limite-e-camadas.md
- [mapa-neural-descritivo] o gerador virou descritivo (0.16.0): `.claude/` fora, rota Flask, camadas detectadas pelo conteúdo, placeholder ≠ fato; o owner perguntou "isso trará benefícios?" e a resposta que fechou foi *o mapa é o destilado que o assistente lê no lugar da fonte*; pivô meu = filtro de placeholder na linha inteira engoliu memória real → estreitado pro campo do assunto; o dogfood no próprio kit pegou `hooks/` invisível e `GET /x` vindo de comentário → sessions/2026-07-31-mapa-neural-descritivo.md

## 2026-07-28
- [analise-projeto-existente] `/mss-spec:analise` — porta de entrada do brownfield (2 fases de leitura → dossiê `ARQUITETURA.md`); pivôs: a restrição "não pode ajustar / pode parar tudo" virou o **eixo** (regra não-destrutiva), UI própria intocável, spec retroativa só com evidência lida; achados: `upgrade` sobrescrevia infra de brownfield (freio) e eu mesmo escrevi em arquivo de categoria 1 (fronteira prescritivo × descritivo); release 0.14.0 → sessions/2026-07-28-analise-projeto-existente.md

## 2026-07-21
- [doctor-check-versao] check de versão do kit no doctor (instalada × publicada no remoto via git fetch no clone); pivôs: doctor≠upgrade (diagnostica plugin × conserta arquivos), semver≠commit; release 0.12.0 → sessions/2026-07-21-doctor-check-versao.md
- [mapa-neural-v0.11.0] datas (mtime) + camada associativa (só no hover, bojando à direita, com setas/realce) + layout tidy-tree horizontal; SOM descartado; fix tela branca (`})` a mais, parse-time) → guarda node --check → sessions/2026-07-21-mapa-neural-datas-associacoes-layout.md
- [mapa-neural-abrir-md] clique num balão-folha .md abre o arquivo renderizado em nova aba; escolha: nova aba + markdown vanilla inline (sem CDN, self-contained) → sessions/2026-07-21-mapa-neural-abrir-md.md
- [captura-de-memoria] avaliação do claude-mem → não integrar (bate nos pilares); nasceu o modo `capturar` + diário de sessão em 3 camadas, foco nos pivôs → sessions/2026-07-21-captura-de-memoria.md
- [ancora-projeto-ativo] acidente real ("olha como o projeto B fez" → assistente adotou o B e quebrou o B) → 3 camadas: regra crítica 8 (âncora não migra, outro projeto é read-only) + read-only no precedentes + hook PreToolUse ligado por padrão; pivôs: owner escolheu bloquear (inverteu a política de hook opt-in do kit), Bash fora, sonda de worktree fail-CLOSED na revisão; canário do hook por junction pendente; **emenda 0.15.1** = a face de leitura ("PERGUNTE, não vasculhe"), cujo repeteco veio de a regra morar só na pasta volátil do ~/.claude → sessions/2026-07-30-ancora-projeto-ativo.md
