import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MantineProvider } from "@mantine/core";
import { DatesProvider } from "@mantine/dates";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "mantine-datatable/styles.css";
import "dayjs/locale/pt-br"; // registra o locale pt-BR do dayjs (usado pelo @mantine/dates)
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
        {/* DatesProvider em pt-BR: DatePickerInput sai localizado (nada de type="date" nativo). */}
        <DatesProvider settings={{ locale: "pt-br" }}>
          <ExemploGrid />
        </DatesProvider>
      </MantineProvider>
    </StrictMode>,
  );
}
