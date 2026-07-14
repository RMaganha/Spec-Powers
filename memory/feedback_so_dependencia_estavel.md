---
name: so-dependencia-estavel
description: Regra do owner — só dependências ESTÁVEIS em todos os componentes; nada de beta/rc/alpha/next, mesmo que a versão beta seja mais "parruda"
metadata:
  type: feedback
---

O owner decidiu (2026-07-13): **só dependências estáveis** — "eu quero o estável nada de beta para
todos os componentes". Vale pro plugin e pros projetos.

**Why:** beta/rc/pre-release num padrão herdado por todos os projetos vira dívida (breaking changes,
lib abandonada, vulnerabilidades transitivas). O caso que disparou: `mantine-react-table` (MRT) é mais
parruda que `mantine-datatable`, mas no **Mantine 7 só existe em beta** (`2.0.0-beta.*`; o estável 1.x
é Mantine 6). O ganho de features não paga o risco de beta num default.

**How to apply:** ao escolher lib/componente, checar o canal — se a versão compatível com a stack só
existe em beta/rc, **não usar**; ficar na alternativa estável e reavaliar quando sair estável. No front:
grid = `mantine-datatable` (estável), NÃO `mantine-react-table` enquanto beta. Codificado no
`templates/FRONTEND.md` e no scaffold `templates/frontend/`. Relacionado: [[front-moderno-mantine]].

**Refinamento (2026-07-13): "só estável" = usar o mais novo ESTÁVEL, inclusive major novo.** A régua é
contra **beta/rc/alpha**, NÃO contra release GA recém-saído. Eu (assistente) errei tentando barrar o
**TypeScript 7** (GA) como "bleeding-edge, esperar" — isso foi cautela minha sem dado verificado, o mesmo
erro do Mantine 7/vite 6. Correção do owner: se é **estável (GA)**, usa. Build tools no último estável:
**vite 8 + @vitejs/plugin-react 6 + TypeScript 7**. Rede de segurança p/ major novo de ferramenta: é
**empírico e instantâneo** — o `tsc` só roda no `npm run typecheck` (o build vite/esbuild não usa tsc);
se o typecheck do TS 7 reclamar, cai pra `typescript ^5.6` numa linha. Adotar > adiar por medo não
verificado. (Beta continua fora, sempre.)

**Confirmado na fonte (2026-07-13):** o template oficial `mantinedev/vite-template` (GitHub) ship
**TypeScript 7.0.2**, Mantine 9.4.1, React 19.2, vite 8, plugin-react 6 — idêntico ao nosso scaffold.
Ou seja, o "risco de tooling do TS 7" era infundado; o próprio Mantine usa. **Fonte da verdade de
versão do front = `mantinedev/vite-template` `package.json`** (não a memória do assistente).
