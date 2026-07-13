import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build gera UM bundle em ../static/js (versionado, servido pelo FastAPI) — sem HTML,
// porque a casca vem do Jinja (ilha) ou de uma rota servida pelo FastAPI (SPA).
// Caminhos relativos ao diretório deste config (evita __dirname, que não existe em ESM).
export default defineConfig({
  plugins: [react()],
  base: "/static/",
  build: {
    outDir: "../static/js",
    emptyOutDir: false, // não apaga layout.js / app.css já existentes em static/js
    rollupOptions: {
      input: "src/main.tsx",
      output: {
        entryFileNames: "frontend.js",
        assetFileNames: "frontend.[ext]",
        chunkFileNames: "frontend-[name].js",
      },
    },
  },
  server: { port: 5173 },
});
