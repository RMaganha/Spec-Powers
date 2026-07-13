import { useEffect, useState } from "react";
import { Group, Stack, TextInput, Title } from "@mantine/core";
import { DatePickerInput } from "@mantine/dates";
import { DataTable } from "mantine-datatable";

// EXEMPLO ilustrativo do padrão: grid consumindo um endpoint JSON do FastAPI.
// Troque a URL, o tipo e as colunas pelo caso real (ex.: /apolice/mssc.json).
type Registro = { id: number; numero: number; data: string; anexos: number };

export function ExemploGrid() {
  const [dados, setDados] = useState<Registro[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [filtro, setFiltro] = useState("");
  // Mantine 8+ (inclui a 9): DatePickerInput trabalha com STRING de data (não Date).
  // Se você fixar uma versão diferente, confirme o tipo do value no primeiro typecheck.
  const [data, setData] = useState<string | null>(null);

  useEffect(() => {
    fetch("/apolice/mssc.json")
      .then((r) => r.json())
      .then((j) => setDados(j.registros ?? []))
      .catch(() => setDados([]))
      .finally(() => setCarregando(false));
  }, []);

  const visiveis = dados.filter((d) => String(d.numero).includes(filtro.trim()));

  return (
    <Stack gap="sm">
      <Group justify="space-between">
        <Title order={3} c="navy.9">Cotações</Title>
        <Group gap="xs">
          <TextInput
            placeholder="Buscar Nº"
            value={filtro}
            onChange={(e) => setFiltro(e.currentTarget.value)}
          />
          {/* DatePickerInput (calendário em popover, pt-BR) — NUNCA <input type="date"> nativo. */}
          <DatePickerInput
            placeholder="Data"
            valueFormat="DD/MM/YYYY"
            clearable
            value={data}
            onChange={setData}
          />
        </Group>
      </Group>
      <DataTable
        withTableBorder
        borderRadius="md"
        striped
        highlightOnHover
        fetching={carregando}
        records={visiveis}
        idAccessor="id"
        columns={[
          { accessor: "numero", title: "Nº MSSC", sortable: true },
          { accessor: "data", title: "Data" },
          { accessor: "anexos", title: "Anexos", textAlign: "right" },
        ]}
        noRecordsText="Nenhum registro."
      />
    </Stack>
  );
}
