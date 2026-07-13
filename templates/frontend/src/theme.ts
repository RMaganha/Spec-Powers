import { createTheme, type MantineColorsTuple } from "@mantine/core";

// Tokens MSIG (os mesmos do Nível 1 do docs/FRONTEND.md), mapeados no tema Mantine.
// Rampas 0→9 aproximadas a partir das cores-base; ajuste fino é bem-vindo.
const brand: MantineColorsTuple = [
  "#ffeae7", "#ffd4cf", "#f6a8a0", "#ee7a6f", "#e75446",
  "#e33d2d", "#e63329", "#c8291f", "#b2231a", "#9b1a12",
]; // base MSIG = #E63329 (índice 6)

const navy: MantineColorsTuple = [
  "#eef1f8", "#d3d8ea", "#a7b0d3", "#7987bd", "#5566ab",
  "#3f52a1", "#33489d", "#26398a", "#1b294f", "#0e1a3a",
]; // navy-800 = #1B294F (8), navy = #0E1A3A (9)

export const theme = createTheme({
  primaryColor: "brand",
  primaryShade: 6,
  colors: { brand, navy },
  fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  defaultRadius: "md",
});
