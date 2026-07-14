import { useEffect, useState } from "react";
import { Group, Stack, TextInput, Title } from "@mantine/core";
import { DatePickerInput } from "@mantine/dates";
import { DataTable } from "mantine-datatable";

// EXEMPLO ilustrativo do padrão: grid enxuta consumindo um endpoint JSON do FastAPI.
// Troque a URL, o tipo e as colunas pelo caso real (ex.: /apolice/mssc.json).
// NÃO inventar coluna de "status": só use StatusBadge/StatusLegend se a tela tiver estados
// REAIS e múltiplos (ex.: Processado / Sem registro / Erro). Ver docs/FRONTEND.md.
type Registro = { id: number; numero: number; data: string; anexos: number };

export function ExemploGrid() {
  const [dados, setDados] = useState<Registro[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [busca, setBusca] = useState("");
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

  // Busca NA GRID: filtra os records por um termo em VÁRIAS colunas (client-side, bom p/ dezenas/
  // centenas de linhas). Estenda os campos conforme as colunas (ex.: apólice, caixa). Para milhares
  // de linhas, faça a busca no servidor (parâmetro no endpoint) em vez de client-side.
  const termo = busca.trim().toLowerCase();
  const visiveis = dados.filter(
    (d) =>
      !termo ||
      String(d.numero).includes(termo) ||
      d.data.toLowerCase().includes(termo),
  );

  return (
    <Stack gap="sm">
      <Group justify="space-between">
        <Title order={3} c="navy.9">Cotações</Title>
        <Group gap="xs">
          <TextInput
            placeholder="Buscar (Nº, data…)"
            value={busca}
            onChange={(e) => setBusca(e.currentTarget.value)}
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
