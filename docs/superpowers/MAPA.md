# Mapa de contexto — mss-spec

## Onde estamos
`main` — **v0.24.1** (`e14a0f1..`, merges `--no-ff` de `feature/bpmn` e `fix/bpmn-desenho-invisivel`; **à frente do `origin` — `git push` pendente, só quando o owner pedir**). Suíte **201 verde** (era 160). **`/mss-spec:bpmn`**: 3º gerador determinístico do kit (`templates/bpmn.py`) — lê o código por `ast` e desenha os processos, um por porta de entrada, raias por pasta, na notação do infográfico do Bizagi. Duas saídas em `docs/`, fora do git: `bpmn.md` (texto, o assistente lê) + `bpmn.html` (SVG self-contained, o humano vê). **Rodar no projeto real (MSS-SSC, 24 rotas FastAPI) pagou por si: 8 bugs que a suíte verde não pegava** — 3 no dogfood daqui (título vazio com `--proj .`, zero processo fora da raiz, `gerar` homônimo desenhando o módulo errado) e 5 no MSS-SSC (desenho dependendo do JS pra existir — o owner abriu e não viu nada; ordem abrindo no processo de 2 nós; SDK de LLM não virando piscina; piscina sem seta; `return servico(x)` perdendo a tarefa). Casos F-016 e F-017. Spec: `docs/specs/bpmn.md`.

<!-- histórico do estado anterior -->
`main` — **v0.23.0 publicada no GitHub** (`85c4428..cb3e678`, em sincronia com o `origin`; merge `--no-ff` de `feature/diagnostico`; suíte **160 verde**). **Trilho disciplinado de diagnóstico (F-015)**, nascido da análise do PDF da sessão de deploy do MSS-SSC (6 rodadas de owner num 503 + 2 re-litigando App Setting correta). 4 camadas: regra crítica 11 no molde (sempre-ativa; o CLAUDE.md ficou em 7.938/8.000 bytes via compressão mover-não-apagar) · `/mss-spec:diagnostico` (alavanca do owner) · memória `feedback_diagnostico_disciplinado` + F-015 no EVALS · propagação via `upgrade` (mescla + renumera). Spec: `docs/specs/diagnostico.md`.

## Próximo passo
**Podar os comandos**: **109.560 bytes em 24 comandos** (remedido em 2026-09-02, depois do `bpmn`; eram 103.815 em 22 na 0.22.0). Leitura certa: a soma é tendência, **não** taxa por sessão (comando `disable-model-invocation` só custa quando invocado) — o alvo real são os **5 grandes** (`nova-feature` 11,8 KB · `analise` 9,3 · `kickoff` 8,3 · `upgrade` 7,8 · `memory` 7,7 ≈ 45 KB), onde instrução demais vira instrução ignorada. Mesmo tratamento do `CLAUDE.md`: teto por bytes travado por teste, mover nunca apagar. Depois, na ordem: fecho com os 3 artefatos garantidos + `git push` de fato (o item 4 do to-dolist; nesta janela a contagem do `COMO-FUNCIONA.html` estava defasada em 4 comandos e foi consertada **à mão**, que é exatamente o sintoma) · consolidar os 68 KB dos arquivos de memória · validar o kit com o modelo Fable.

<!-- histórico do próximo passo anterior -->
**Sentir a 0.19.0 em uso, em sessão nova** — é o único teste que importa aqui: numa janela recarregada, o índice do repo tem que entrar sozinho (pelo ponteiro da nativa) e as regras de `.claude/rules/` têm que acender quando eu tocar um `.html`/`.sql`/`routes/`. Se o owner ainda precisar lembrar de algo que está na memória, isso vira caso novo em `docs/EVALS.md`. Depois: **1 caso aberto** (F-010, jargão inventado ao explicar desenho) e o **item 5 do to-dolist** (garantir COMO-FUNCIONA/MAPA/mapa-neural no fecho), em janela própria. `git push` só quando o owner pedir.

## Conexões
<!-- Integrações de RUNTIME com outros projetos. O mss-spec é um plugin de scaffolding (comandos-prosa),
     não um serviço — logo não chama nem é chamado por outro sistema em runtime. Declarado honestamente. -->
- nenhuma integração de runtime — o mss-spec é o **kit de scaffolding** (comandos-prosa que o assistente executa). A relação com os projetos MSIG é de **consumo** (eles instalam o kit) e de **catálogo de precedentes** (skill `precedentes-msig`), não de integração "o que vai pra onde".

<!-- Atualizado em 2026-07-21 · regenerável com /mss-spec:mapa -->
