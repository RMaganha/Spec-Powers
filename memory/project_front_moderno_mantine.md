---
name: front-moderno-mantine
description: Padrão de front em dois níveis — Jinja+Tailwind (simples) × React+TS+Mantine (denso); Mantine escolhida, Next/Remix fora de propósito; decisão por-tela
metadata:
  type: project
---

Decisão de front do kit (2026-07-13, branch `plugin-v2`), a partir da avaliação dos sistemas legados
MSIG (MS10/MSS Digital, telas ASP.NET WebForms densas de campos/grids):

- **Dois níveis, decisão por-tela** (não por-projeto): **Nível 1** = Jinja + Tailwind (+ HTMX/Alpine)
  para telas simples/server-rendered; **Nível 2** = React + TypeScript + Mantine (SPA via Vite) para
  telas densas (grids sort/filtro, muitos campos, date pickers). Regra: comece no 1, suba pro 2 só
  quando a tela pedir componentes que doeria fazer à mão.
- **Stack estável (verificado no npm em 2026-07-13):** Mantine **9.4.1** + React **19** (o Mantine 9
  exige React 19; `@mantine/dates` peer `react ^19.2`) + `mantine-datatable` **9.3.1** (peer core `>=9`,
  `react >=19`, `clsx`). Os `@mantine/*` ficam na MESMA versão (peer exato entre si). **Lição:** o
  scaffold estava pinado em Mantine 7/React 18 (de cabeça) — errado; sempre **conferir o `latest` no
  npm**, versão envelhece. Instância de [[nao-inventar-fatos-concretos]] (mesmo padrão do trixie/bookworm
  no Docker). O scaffold pina o estável do dia + manda `typecheck`/refresh no install.
- **Mantine** escolhida (não MUI/Chakra); **`mantine-datatable`** para grids (default, estável no
  Mantine 9). **`mantine-react-table` (MRT)** é a "parruda" mas **não tem estável pro Mantine atual**
  (latest 1.3.4 = Mantine antigo; v2 só alpha/beta) → **fica de fora** pela regra
  [[so-dependencia-estavel]]. **Datas: sempre `DatePickerInput` (`@mantine/dates`, pt-BR)** — nunca
  `<input type="date">` nativo (o "amador" do 1º piloto, por faltar `@mantine/dates`; corrigido).
  **Next/Remix ficaram de fora de propósito**: app interno autenticado não precisa de SSR/SEO — SPA
  Vite é mais simples (um bundle estático servido pelo FastAPI). Ver [[docker-build-fortigate]] p/ o
  atrito de Node/npm no proxy (build multi-stage; runtime Python sem Node; ou bundle versionado).
- **Tailwind × Mantine NÃO se misturam** no mesmo app: a Mantine já traz tema/espaçamento/dark mode;
  onde ela entra, o Tailwind sai. Tailwind fica nas telas Nível 1.
- **Ilha × rota SPA**: um pedaço de página → ilha React (`#mantine-root` + bundle); tela inteira →
  rota SPA. React consome JSON do FastAPI (API/BFF), nunca HTML renderizado.
- **Onde fica**: padrão codificado no plugin (`/mss-spec:frontend` + `templates/frontend/` +
  `templates/FRONTEND.md` Nível 2). A implementação por-projeto roda na sessão DO projeto (ex.:
  modernizar a tela de apólice do MSS-SSC via `/mss-spec:nova-feature`), não editando de outro repo.
- **Estratégia de modernização do legado**: strangler-fig (o MSS-SSC é o 1º galho novo) + FastAPI
  como BFF sobre o SQL Server. O front é os ~30% fáceis; desacoplar o monólito via APIs é o resto.
- **Busca na grid = FUNIL NA COLUNA** (props `filter`/`filtering` da `mantine-datatable`; um
  `TextInput` no popover do cabeçalho — Data pode ter `DatePickerInput`), **NÃO** barra de busca solta
  acima da grid (escolha do owner, 2026-07-14). Filtragem client-side (`records.filter`) p/ poucas
  linhas; server-side `?busca=` p/ muitas.
- **Trade-off aceito (nota honesta):** a `mantine-datatable` (estável) é **menos "parruda"** que a
  `mantine-react-table` (MRT) — a busca no funil e o visual ficam mais modestos que a toolbar integrada
  da MRT. O owner registrou que "não ficou tão bom" quanto com a MRT. Aceito **por causa do "só
  estável"** [[so-dependencia-estavel]] (MRT sem release estável pro Mantine atual). **Reavaliar a MRT
  quando houver 2.x estável** — o grid é 1 componente isolado, trocar depois é barato. A jornada do
  front teve MUITO vaivém (MRT↔datatable, versões 7→9, busca, badges) — a maior parte por eu cravar
  fato de versão de cabeça; a régua agora é: conferir npm/template oficial, não a memória do assistente.
- **Status na grid — componentes `StatusBadge`/`StatusLegend`, MAS com julgamento (regra dura):**
  tons `ok`/`aviso`/`erro`/`neutro` = verde/amarelo/vermelho/cinza; ex.: `<StatusBadge tone="ok">
  Processado</StatusBadge>`. **SÓ usar quando a tela tem estado REAL e múltiplo** (ex. ATM-TRP:
  Processado/Sem registro/Erro) — aí **legenda obrigatória acima** (`StatusLegend itens={[...]}`).
  **NÃO INVENTAR status:** se é contagem ou sim/não já visível noutra coluna, NÃO cria badge/legenda.
  Erro real (2026-07-14): o exemplo do plugin trazia status falso "Com anexos/Sem anexos" e a sessão
  do MSS-SSC copiou pra tela de cotação (que NÃO tem status) → ficou redundante/feio. Correção:
  os componentes **NÃO ficam no `ExemploGrid`** (não é peça de toda grid); status é opcional/sob
  julgamento. **Por-projeto, não generalizar** (cotação MSSC não tem status; ATM-TRP tem vários).
  Lição-mãe: exemplo de scaffold não pode ser copiável-como-lixo → [[nao-inventar-fatos-concretos]].
