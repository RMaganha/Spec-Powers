# Travas de publicação e um item por janela — cercas mecânicas contra a janela sequestrada

## Estado atual
Duas cercas **mecânicas** (hooks ligados por padrão, registrados em `hooks/hooks.json`) e uma regra
dura de conduta, nascidas do caso **F-022** (`docs/EVALS.md`): a janela de UMA feature absorveu dois
outros assuntos, mesclou branches e o assistente disparou `git push` — o gatilho do deploy
automático — várias vezes; a homologação quebrou inteira.

**(1) `hooks/git_publicacao.py`** — `PreToolUse` em `Bash|PowerShell`. **Nega** publicar (`git push`),
integrar (`git merge`, `git rebase` menos `--abort`, `gh pr merge`) e fazer deploy (`docker push`,
`az acr build`, `az webapp <escrita>`, `az containerapp update|create|revision`). Casa o **verbo no
início de um comando simples** (após `;` `&&` `|` `(` quebra de linha ou prefixo `VAR=x`), não a
palavra solta. Libera o resto do git (abrir a branch da feature continua livre). **Falha FECHADA**:
com comando e avaliação estourada, nega. Escape só do owner: `MSS_PUBLICACAO_OFF=1`. O assistente,
no lugar, roda `/mss-spec:release` e **pede**; o owner publica do terminal dele.

**(2) `hooks/um_item_por_janela.py`** — `UserPromptSubmit`. Só age em `/mss-spec:nova-feature <nome>`
(ou `/nova-feature`). Lê `<cwd>/docs/superpowers/INDEX.md`; linha de item com status `aberta` ou
`em andamento` conta como aberta (`fechada`/`pausada: <motivo>` não; seção "Fora de escopo" ignorada).
Outra aberta → **bloqueia o prompt** listando-as e as três saídas (terminar a aberta; o owner marcar
`pausada` à mão; `to-dolist adicionar`). A mesma (nome ou slug da spec, sem acento/caixa) → passa.
Sem INDEX → passa. **Falha ABERTA**. Escape só do owner: `MSS_UM_ITEM_OFF=1`.

**(3) Prosa que virou trava**: `templates/CLAUDE.md` (linha "Um assunto por janela" deixa de ser
"alerta, não trava": 2º assunto → **não aja**, anote no MAPA, `to-dolist`, janela nova; linha Git:
push/merge/rebase/deploy "nunca você") · `commands/nova-feature.md` **passo 0** (gate de feature
aberta — 2ª camada do hook 2) e fecho (o owner executa merge/PR/push) · `commands/diagnostico.md`
passo 3 (**F-023**: saúde de endpoint só com a matriz de variantes do chamador; diff do deploy
inteiro). O molde ficou em **7.991/8.000 bytes** via compressão de prosa (mover/encurtar, nunca apagar).

**Custo aceito:** o assistente não faz mais `git merge` nem `push` — o `finishing-a-development-branch`
vira "apresente as opções; o owner executa". `git pull` segue livre (não publica).

Fora de escopo: detectar mecanicamente "2º assunto no meio da conversa" (não há assinatura de tool;
fica na prosa + no gate de abertura) · tirar a credencial git do assistente (configuração da máquina,
não do kit — complemento opcional do owner) · escape por argumento do assistente (só env do owner).

## Histórico
- 2026-09-14 — criado: análise da sessão "lixo" do projeto MITI (feature de formatação do WhatsApp
  que virou diagnóstico de 400 pra .Blip + flags + merge + pushes). Casos F-022 e F-023. Decisão do
  owner: "regra extremamente dura, 1 item por janela, nova feature somente quando não tiver mais
  features abertas" e "tem que ter outra trava que funcione" — por isso hook, não prosa (F-014 e
  F-015 já eram prosa e não seguraram).
