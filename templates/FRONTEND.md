<!-- MODELO de design system MSIG — copie para `docs/FRONTEND.md` no projeto novo (só se tiver UI web).
     É o padrão visual/estrutural do front-end. Extraído do painel Atas Teams (2026-07). O nome/subtítulo
     do sistema e o rótulo do rodapé são por-projeto; o resto (tokens, layout, ícones, JS) é o padrão MSIG. -->

# Front-end MSIG — design system

Padrão visual e estrutural para UIs de aplicação. Objetivo: minimalista, profissional, consistente
entre os sistemas MSIG. **Regra-mãe:** componentizado, com HTML/CSS/JS em arquivos e pastas separadas —
nunca tudo embolado num arquivo (ver Regra crítica de front-end no `CLAUDE.md`).

## Dois níveis de front (escolha por tela, não por projeto)

O mesmo projeto pode ter os dois — a decisão é **por tela**, pela densidade de interação:

| | **Nível 1 — Jinja + Tailwind** | **Nível 2 — React + TS + Mantine** |
|---|---|---|
| Quando | Páginas simples/institucionais, formulários leves, conteúdo, telas 80% estáticas | Telas **densas de dados/interação**: grids com sort/filtro/paginação, muitos campos, date pickers, máscaras, seleção múltipla, wizard |
| Render | Servidor (FastAPI + Jinja) | SPA React servida pelo FastAPI (bundle estático) |
| Interatividade extra | HTMX/Alpine (sem build pesado) | Componentes Mantine prontos |
| Custo | Baixo (1 runtime) | Build JS (Vite/Node) — atrito no proxy/Docker (ver §Nível 2) |

**Regra de decisão:** comece no Nível 1. Suba pro Nível 2 **só** quando a tela pedir componentes que doeria construir à mão (DataTable, DatePicker, Select com busca, forms complexos). Não misture Tailwind e Mantine **no mesmo app/tela** — a Mantine já traz tema, espaçamento, dark mode e responsivo; onde ela entra, o Tailwind sai.

---

# Nível 1 — Jinja + Tailwind (painel admin server-rendered)

## Stack e build
- **Tailwind CSS v4** + plugin **`@tailwindcss/typography`**.
- `static/css/input.css` é a fonte; compila para `static/css/app.css` (o HTML linka o `app.css`).
- `input.css` mínimo:
  ```css
  @import "tailwindcss";
  @plugin "@tailwindcss/typography";

  @theme {
    --color-navy: #0E1A3A;        /* sidebar */
    --color-navy-800: #1B294F;    /* hover/borda na sidebar */
    --color-brand: #E63329;       /* vermelho MSIG — ação/ativo */
    --color-brand-indigo: #2A2A6A;
    --color-canvas: #F1F1F1;      /* fundo da página */
  }
  ```

## Paleta (tokens `@theme`)
| Token | Hex | Uso |
|---|---|---|
| `navy` | `#0E1A3A` | fundo da sidebar, títulos, avatar |
| `navy-800` | `#1B294F` | hover de item de menu, bordas internas da sidebar |
| `brand` | `#E63329` | botões de ação, item de menu ativo (vermelho MSIG) |
| `brand-indigo` | `#2A2A6A` | acento secundário |
| `canvas` | `#F1F1F1` | fundo da área de conteúdo |
| (Tailwind) `slate-*`, `white` | — | texto, cards brancos, bordas neutras |

## Anatomia do layout (`templates/base.html`)
- **Sidebar** `w-60 bg-navy text-slate-100`, fixa e **colapsável** (`-translate-x-full` + overlay no mobile; `lg:ml-60` no conteúdo quando aberta).
  - **Topo:** logo num quadrado branco arredondado (`h-10 w-10 rounded-lg bg-white` com `logo.png`) + nome do sistema (`MSIG` em `text-sm font-medium`, subtítulo em `text-xs text-slate-400`).
  - **Nav:** itens `flex items-center gap-3 rounded-lg px-3 py-2 text-sm`; **ativo** = `bg-brand text-white` + `aria-current="page"`; inativo = `text-slate-300 hover:bg-navy-800`; cada item com ícone SVG inline `h-4 w-4`.
  - **Rodapé (canto inferior esquerdo):** `mt-auto ... border-t border-navy-800 px-4 py-3 text-xs text-slate-400` com ícone + **rótulo do sistema** (ex.: "Painel ATA's").
- **Header** `h-14 bg-white border-b px-4`: botão hambúrguer (`data-sidebar-toggle`), título da página (`text-navy`), e à direita avatar redondo (`h-8 w-8 rounded-full bg-navy text-white` com iniciais).
- **Conteúdo** `p-4 lg:p-6` sobre `bg-canvas`, organizado em **cards brancos** arredondados com borda sutil.

## Ícones
SVG **inline**, estilo Lucide/Feather: `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"`, tamanho `h-4 w-4` (nav) ou `h-5 w-5` (header). Minimalista, monocromático (herda `currentColor`). **Não** usar icon-font.

## Badges/estado
Pills pequenas: estado positivo (ex.: "ativo") em verde suave; neutro/negativo (ex.: "inativo") em cinza. Discretas, arredondadas.

## JavaScript
- **Vanilla**, sem framework. Um arquivo por área (`static/js/layout.js`, `static/js/<pagina>.js`), carregados com `defer`.
- Padrão: **IIFE** + hooks via atributos `data-*` (ex.: `[data-sidebar]`, `[data-sidebar-toggle]`), sem acoplar em classes de estilo. Estado leve em `localStorage` quando fizer sentido (ex.: sidebar aberta/fechada).

## Componentização (Jinja)
- `templates/base.html` = layout (sidebar + header + `{% block content %}`).
- Uma página por arquivo (`templates/<area>/list.html`) estendendo o base.
- Partes reutilizáveis (tabela, modal, form) viram `include`/`macro` — não repetir marcação.

## Assets
- Logo MSIG: `static/img/logo.png` (o `/mss-spec:kickoff` copia do plugin quando o projeto tem UI).

---

# Nível 2 — React + TypeScript + Mantine (telas densas)

Para telas de dados/back-office (o grosso da modernização dos sistemas legados). Instale com
`/mss-spec:frontend` — ele copia o scaffold de `${CLAUDE_PLUGIN_ROOT}/templates/frontend/` e aplica o tema MSIG.

## Stack (versões envelhecem — confirme o estável atual no npm ao instalar)
- **React 19 + TypeScript**, build com **Vite** (bundle estático servido pelo FastAPI). O Mantine 9 **exige React 19** (`@mantine/dates` peer `react ^19.2`).
- **Mantine 9** (`@mantine/core`, `@mantine/hooks`, **mesma versão exata** nos três) para os componentes; **`@mantine/dates`** para datas.
- **Grid: `mantine-datatable`** (estável no Mantine 9 — peer `@mantine/core >=9`, `react >=19`, `clsx`; sort/paginação/seleção prontos) — o **default** do scaffold. A MRT ("parruda") fica de fora enquanto não tiver estável no Mantine atual — ver *Regra: só estável* e *Grid parruda* abaixo.
- **Números exatos rot** (o Mantine passou de 7→9, React 18→19 sem a gente ver): o scaffold pina o estável do dia; no install, **confira o `latest` no npm** e rode `npm run typecheck`.
- **Datas: SEMPRE `DatePickerInput`** do `@mantine/dates` (calendário em popover, pt-BR via `DatesProvider locale="pt-br"` + `dayjs/locale/pt-br`). **Nunca** `<input type="date">` nativo — fica cru e refém do locale do navegador.
- **TypeScript centraliza a lógica** — vale desde cedo: o ganho é na manutenção/refactor conforme cresce.

## Regra: só dependências ESTÁVEIS (nada de beta/rc/pre-release)
Todo componente/lib do front é **release estável** — nada de `beta`, `rc`, `alpha` ou `next`. Beta em
padrão de plugin vira dívida herdada por todos os projetos (breaking changes, abandono, vulnerabilidades).
Se a lib "parruda" que você quer só existe em beta, **ela fica fora até sair estável** — use a alternativa
estável enquanto isso.

## Grid parruda — `mantine-react-table` (MRT): SEM estável pro Mantine atual, NÃO usar
A **MRT** (menu de coluna, densidade, colunas escondíveis, header fixo) seria a opção mais parruda —
**mas não tem release estável compatível com o Mantine atual**: o `latest` estável é `1.3.4` (Mantine
antigo, peer `>=5.7`) e a v2 só existe em `alpha`/`beta` (`2.0.0-beta.*`). Pela regra acima, **não
entra**. **Grid = `mantine-datatable`** (estável no Mantine 9). Reavaliar só quando a MRT tiver `2.x`
estável pro Mantine em uso.

## Ilha × Rota SPA (decida pelo tamanho da mudança)
- **Ilha React:** monta **um** componente React num `<div>` de uma página Jinja (o resto segue Jinja). Bom para introduzir Mantine em **um pedaço** (ex.: só a grid) com risco mínimo.
- **Rota SPA:** a página **inteira** vira React (Jinja só serve o HTML-casca + o bundle). Certo quando a tela toda moderniza (campos, botões, date pickers, grid juntos).
- Regra: um pedaço → ilha; tela inteira → rota SPA. Ilha é passo de transição; não espalhe muitas ilhas na mesma tela.

## Tema MSIG na Mantine
Os mesmos tokens do Nível 1, mapeados no tema Mantine (ver `templates/frontend/src/theme.ts`):
`brand` (#E63329) como `primaryColor`, `navy` (#0E1A3A) para chrome/sidebar. Não reimplemente com Tailwind — a Mantine é a fonte de estilo no app React.

## Componentização
- Um componente por arquivo, tipado, em `frontend/src/components/`.
- Dados vêm do FastAPI como **JSON** (endpoints dedicados) — o React **não** lê HTML renderizado; a camada Python vira API/BFF sobre o banco.
- Estado local com hooks; nada de framework de estado global até doer (YAGNI).

## Build e o atrito corporativo (leia antes de containerizar)
- Dev local: `npm install` + `npm run dev` (Vite). Build: `npm run build` → bundle em `static/js/` (versionado, igual o `app.css`).
- **Atrás do FortiGate**, `npm install` sofre o mesmo que pip/apt (ver `AMBIENTE.md` §2): resolva com registry npm interno/proxy **ou** rode o `npm ci` num estágio de build que tenha rede. No Docker, use **multi-stage** (estágio Node só pra buildar o bundle; a imagem final Python só copia o `static/js/` pronto — sem Node em runtime).
- Regra prática: **buildar o bundle e versioná-lo** (como o Tailwind) mantém a imagem de runtime sem Node e evita `npm` no build do container.
