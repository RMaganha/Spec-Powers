import { Group, Text } from "@mantine/core";
import { StatusBadge, type StatusTone } from "./StatusBadge";

// Legenda de status ACIMA da grid — SEMPRE que a grid tiver etiquetas de status, mostre a legenda
// explicando o que cada uma significa. Os itens são POR-PROJETO (cada tela tem os seus; o ATM-TRP,
// por exemplo, tem bem mais que o MSS-SSC) — por isso a lista vem de fora, não é fixa no componente.
export type LegendaItem = { tone: StatusTone; label: string; descricao?: string };

/** Ex.:
 *  <StatusLegend itens={[
 *    { tone: "ok",    label: "Processado" },
 *    { tone: "aviso", label: "Sem registro", descricao: "não achou no sistema de origem" },
 *    { tone: "erro",  label: "Falha" },
 *  ]} />
 */
export function StatusLegend({ itens }: { itens: LegendaItem[] }) {
  return (
    <Group gap="md" wrap="wrap">
      {itens.map((it) => (
        <Group key={it.label} gap={6}>
          <StatusBadge tone={it.tone}>{it.label}</StatusBadge>
          {it.descricao && (
            <Text size="xs" c="dimmed">
              {it.descricao}
            </Text>
          )}
        </Group>
      ))}
    </Group>
  );
}
