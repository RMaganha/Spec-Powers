import type { ReactNode } from "react";
import { Badge } from "@mantine/core";

// Etiqueta de status colorida (o "✓ verde" / "Sem registro" amarelo dos painéis).
// tone = cor semântica; o texto (children) é livre.
export type StatusTone = "ok" | "aviso" | "erro" | "neutro";

const COR: Record<StatusTone, string> = {
  ok: "green",
  aviso: "yellow",
  erro: "red",
  neutro: "gray",
};

/** Ex.: <StatusBadge tone="ok">Processado</StatusBadge> · <StatusBadge tone="aviso">Sem registro</StatusBadge> */
export function StatusBadge({ tone, children }: { tone: StatusTone; children: ReactNode }) {
  return (
    <Badge color={COR[tone]} variant="light" radius="sm">
      {children}
    </Badge>
  );
}
