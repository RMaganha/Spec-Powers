# frontend/ — front moderno MSIG (React + TS + Mantine)

Scaffold do **Nível 2** do `docs/FRONTEND.md`. Use para telas densas (grids, muitos campos,
date pickers). Telas simples continuam no Nível 1 (Jinja + Tailwind).

## Rodar
```bash
cd frontend
npm install          # atrás do FortiGate: ver "Atrito corporativo" abaixo
npm run dev          # dev server Vite (http://localhost:5173)
npm run build        # gera o bundle em ../static/js/frontend.js (+ .css)
npm run typecheck    # checagem de tipos
```

## Montar no app (dois modos)
O `main.tsx` monta no elemento `#mantine-root` — se ele não existir, a página segue 100% Jinja.

- **Ilha** (um pedaço de uma página Jinja): ponha `<div id="mantine-root"></div>` onde entra o
  componente e carregue o bundle:
  ```html
  <div id="mantine-root"></div>
  <link rel="stylesheet" href="/static/js/frontend.css?v={{ asset_v }}">
  <script type="module" src="/static/js/frontend.js?v={{ asset_v }}"></script>
  ```
- **Rota SPA** (tela inteira em React): uma rota do FastAPI devolve um HTML-casca com o mesmo
  `#mantine-root` + o bundle; todo o conteúdo é React.

## Dados
O React consome **JSON** de endpoints do FastAPI (a camada Python vira API/BFF). Não lê HTML
renderizado. Ex.: `GET /apolice/mssc.json` → `{ "registros": [...] }` (ver `ExemploGrid.tsx`).

## Componentes
- **Grid:** `mantine-datatable` (estável no Mantine 7). Grid "parruda" (menu de coluna, densidade):
  `mantine-react-table` é opt-in, mas **no Mantine 7 é beta** — ver `docs/FRONTEND.md`.
- **Datas:** `DatePickerInput` (`@mantine/dates`) em pt-BR (`DatesProvider locale="pt-br"`). **Nunca**
  `<input type="date">` nativo (fica cru e depende do locale do navegador).

## Atrito corporativo (proxy / Docker)
- `npm install` atrás do FortiGate sofre o mesmo que pip/apt (ver `docs/AMBIENTE.md` §2): registry
  npm interno/proxy, **ou** rode num ambiente com rede (casa/VPN) e versione o bundle.
- **Docker: multi-stage.** Estágio Node só builda o bundle; a imagem final Python **copia o
  `static/js/` pronto** — sem Node em runtime. Ou builde o bundle no host e versione (como o
  `app.css` do Tailwind) — aí o container nem toca em `npm`.
