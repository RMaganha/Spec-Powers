# doctor — check de versão do kit contra o remoto (2026-07-21)

**Conversamos** — o owner trouxe 2 dúvidas: (1) como ver, de outro projeto, se o
spec-powers está atualizado lá; (2) como retomar um assunto num chat que não é
`nova-feature`. Esclarecido: o plugin é **global** (não há versão por projeto);
retomar assunto já funciona por padrão (SessionStart + CLAUDE.md manda ler
`memory/MEMORY.md` — foi o que rolou aqui). Da dúvida (1) nasceu a feature.

**Pivôs**
- doctor × upgrade: o owner achou que os dois "fariam um trecho cada". Repensado →
  são **dois níveis**: doctor **diagnostica o plugin** (global), upgrade **conserta
  os arquivos do projeto** (local, contra a versão já instalada, nunca olha o
  remoto). Ajustou pra feature 100% no **doctor**.
- commit × semver: o owner inclinou por **commit** ("sou o dono"). Repensado →
  **semver**: legível ("0.11.0 → 0.12.0" vs hash) e sem falso-desatualizado nos
  muitos commits que não mexem no plugin (docs, memory/, MAPA); alinha com release.

**Rejeitado** — comparar por commit · HTTP raw pro remoto (git fetch reusa o canal
do `marketplace update`) · viver no upgrade · rodar `marketplace update` sozinho
(só reporta) · híbrido versão+commit.

**Fizemos** — check 8 no `doctor.md` (instalada via `plugin.json`; publicada via
`git fetch` + `git show origin/<ref>`); degrada gracioso offline/dev (nunca ✗);
smoke `test_doctor_check_versao_wiring`; spec + plano; release **0.12.0** (bump nos
2 manifestos + CHANGELOG). Suíte **63 verde**.

**Próximo** — merge `--no-ff` na `main` (finishing); `git push` a pedido.

## Acrescentado no sono de 2026-11-16

> A partir do texto da conversa `8a576c2d-082a-4837-8ed5-21cee3792d0a` (só falas; sem saída de ferramenta).

O trecho de 2026-07-22 (falas 023-040) ficou fora deste diário:
- **Conversamos:** como atualizar outro projeto.
- **Pivôs:** o assistente mandou `/plugin marketplace update mss-local` duas vezes; o owner: "eu avisei que está
  errado!!!" (fala 027); o disco mostrou a junção. No app Desktop do owner o `/plugin` não existe (fala 028).
- **Rejeitado:** marketplace para o owner (naquela data). **Fizemos:** nada gravado.
- **Próximo:** corrigir o COMO-FUNCIONA (`/plugin` × app Desktop).
