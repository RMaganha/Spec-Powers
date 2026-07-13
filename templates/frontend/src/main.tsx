import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MantineProvider } from "@mantine/core";
import "@mantine/core/styles.css";
import "mantine-datatable/styles.css";
import { theme } from "./theme";
import { ExemploGrid } from "./components/ExemploGrid";

// Monta no #mantine-root da página — funciona tanto como ILHA (um <div> numa página
// Jinja) quanto como casca de ROTA SPA servida pelo FastAPI. Se o elemento não existir,
// não faz nada (a página segue 100% Jinja).
const el = document.getElementById("mantine-root");
if (el) {
  createRoot(el).render(
    <StrictMode>
      <MantineProvider theme={theme} defaultColorScheme="light">
        <ExemploGrid />
      </MantineProvider>
    </StrictMode>,
  );
}
