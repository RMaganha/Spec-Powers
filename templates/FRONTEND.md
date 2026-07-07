<!-- MODELO de design system MSIG — copie para `docs/FRONTEND.md` no projeto novo (só se tiver UI web).
     É o padrão visual/estrutural do front-end. Extraído do painel Atas Teams (2026-07). O nome/subtítulo
     do sistema e o rótulo do rodapé são por-projeto; o resto (tokens, layout, ícones, JS) é o padrão MSIG. -->

# Front-end MSIG — design system (painel admin)

Padrão visual e estrutural para UIs de aplicação. Objetivo: minimalista, profissional, consistente
entre os sistemas MSIG. **Regra-mãe:** componentizado, com HTML/CSS/JS em arquivos e pastas separadas —
nunca tudo embolado num arquivo (ver Regra crítica de front-end no `CLAUDE.md`).

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
