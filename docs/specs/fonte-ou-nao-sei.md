# Fonte ou não sei — resposta ancorada no que foi aberto, e citação conferida no disco

## Estado atual
**(1) Regra no `templates/CLAUDE.md`** (frase-chave travada): fato do projeto sai do que foi **aberto nesta janela** (`arquivo:linha`) ou do que o owner disse; sem fonte, **"não sei"** e abrir ou perguntar. Junto das que já existiam: "Não inventar fatos concretos", "PERGUNTE, não vasculhe", "Responda só o que eu pedi".

**(2) `hooks/confere_citacoes.py`** — `Stop`, ligado, sem LLM. Confere no disco, fora de bloco de código: caminho em crase ou link (com `:linha`), `/mss-spec:<x>` (comando ou skill do kit) e `F-0NN` (se há `docs/EVALS.md`). Vale no projeto ou no kit, inteiro ou como final de caminho existente; molde do kit conta. Pula URL, glob, placeholder, texto com espaço e linha que propõe ("→", "criar", "novo", "vai para", "vira") ou nega ("não existe"). Inválida → devolve **uma vez** (exit 2, stderr UTF-8); `stop_hook_active` evita laço. Falha aberta; `MSS_CITACOES_OFF=1`; registro `devolveu citacoes=N` (nunca o texto).

**(3) Memória na hora da ação (0.36.0, F-034)** — memória com `gatilho_comando:` (regex do comando) ou `gatilho_resposta:` (regex da resposta), lida do projeto e do kit (`hooks/_memoria_de_acao.py`). Comando que casa: o `git_publicacao.py` nega **uma vez por sessão**, com a memória no motivo; repetir passa. Resposta que casa: o `confere_citacoes.py` devolve uma vez. As duas memórias do caso ganharam gatilho (heredoc de Python com acento; "atualizar o plugin/kit"). Escape `MSS_MEMORIA_ACAO_OFF=1`.

**(4) Rotas não pedidas (0.36.0, F-033)** — no mesmo `Stop`: ≥ 2 marcadores de rota alternativa ("Rota 1", "Opção A", "Caminho 2"…), resposta acima de 300 palavras, pedido sem "opção/alternativa/rota/comparar" → volta uma vez pedindo 1–2 perguntas ou só a rota certa.

**Fonte das práticas:** doc da Anthropic *Reduce hallucinations* (permitir "não sei", citações, restringir ao fornecido) e o guia de prompting do Claude 4 (investigar antes de responder: não especular sobre código não aberto); doc de hooks do Claude Code (Stop: `last_assistant_message`, `stop_hook_active`, exit 2).

Fora de escopo: verificação por LLM (best-of-N, auto-verificação — custo de token em toda resposta) · conferir afirmação sem citação (não há o que conferir no disco — fica na regra) · conferir `[[memória]]` (link pendente é permitido na memória) · host/porta/variável (não há fonte única no disco).

## Histórico
- 2026-09-25 — criado a pedido do owner ("regra de não alucinar"), depois de o caso F-033 (resposta gigante no Whats). Medido em 121 respostas reais antes de ligar: 16 → 7 devoluções tirando 3 classes de falso positivo; o hook não achou invenção real no histórico. Achado no caminho: o stderr do Python no Windows sai em cp1252 e corrompia o travessão do motivo — gravado em UTF-8.
- 2026-09-25 — 0.36.0: o UTF-8 forçado voltou atrás (a doc não diz como o Claude Code lê o stderr, e o `print` comum dos outros hooks aparece certo ao vivo). F-033 e F-034 ganharam mecanismo, medido antes de ligar em 201 respostas e 957 comandos reais; o 1º gatilho do plugin pegava `plugin.json` e `catalogo-do-kit` e foi apertado. O próprio patch das memórias reproduziu o F-034 — heredoc estragou o regex com caractere de controle.
