# Fonte ou não sei — resposta ancorada no que foi aberto, e citação conferida no disco

## Estado atual
**(1) Regra no `templates/CLAUDE.md`** (frase-chave travada): fato do projeto sai do que foi **aberto nesta janela** (`arquivo:linha`) ou do que o owner disse; sem fonte, **"não sei"** e abrir ou perguntar. Junto das que já existiam: "Não inventar fatos concretos", "PERGUNTE, não vasculhe", "Responda só o que eu pedi".

**(2) `hooks/confere_citacoes.py`** — `Stop`, ligado, sem LLM. Confere no disco, fora de bloco de código: caminho em crase ou link (com `:linha`), `/mss-spec:<x>` (comando ou skill do kit) e `F-0NN` (se há `docs/EVALS.md`). Vale no projeto ou no kit, inteiro ou como final de caminho existente; molde do kit conta. Pula URL, glob, placeholder, texto com espaço e linha que propõe ("→", "criar", "novo", "vai para", "vira") ou nega ("não existe"). Inválida → devolve **uma vez** (exit 2, stderr UTF-8); `stop_hook_active` evita laço. Falha aberta; `MSS_CITACOES_OFF=1`; registro `devolveu citacoes=N` (nunca o texto).

**Fonte das práticas:** doc da Anthropic *Reduce hallucinations* (permitir "não sei", citações, restringir ao fornecido) e o guia de prompting do Claude 4 (investigar antes de responder: não especular sobre código não aberto); doc de hooks do Claude Code (Stop: `last_assistant_message`, `stop_hook_active`, exit 2).

Fora de escopo: verificação por LLM (best-of-N, auto-verificação — custo de token em toda resposta) · conferir afirmação sem citação (não há o que conferir no disco — fica na regra) · conferir `[[memória]]` (link pendente é permitido na memória) · host/porta/variável (não há fonte única no disco).

## Histórico
- 2026-09-25 — criado a pedido do owner ("regra de não alucinar"), depois de o caso F-033 (resposta gigante no Whats). Medido em 121 respostas reais antes de ligar: 16 → 7 devoluções tirando 3 classes de falso positivo; o hook não achou invenção real no histórico. Achado no caminho: o stderr do Python no Windows sai em cp1252 e corrompia o travessão do motivo — gravado em UTF-8.
