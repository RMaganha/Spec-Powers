import { useEffect, useState } from "react";
import { Stack, TextInput, Title } from "@mantine/core";
import { DataTable } from "mantine-datatable";

// EXEMPLO: grid com BUSCA NA COLUNA (funil no cabeçalho, estilo Excel) — recurso `filter`/`filtering`
// da mantine-datatable. A busca fica DENTRO da grid, não numa barra separada acima.
// (Para filtrar por data, use um DatePickerInput dentro do `filter` de uma coluna de data.)
type Registro = { id: number; numero: number; data: string; anexos: number };

export function ExemploGrid() {
  const [dados, setDados] = useState<Registro[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [buscaNumero, setBuscaNumero] = useState("");

  useEffect(() => {
    fetch("/apolice/mssc.json")
      .then((r) => r.json())
      .then((j) => setDados(j.registros ?? []))
      .catch(() => setDados([]))
      .finally(() => setCarregando(false));
  }, []);

  // A grid mostra só os records que passam nos filtros das colunas (client-side, bom p/ poucas
  // linhas; p/ milhares, filtre no servidor via ?busca=). Cada funil de coluna = um estado aqui.
  const termo = buscaNumero.trim().toLowerCase();
  const visiveis = dados.filter(
    (d) => !termo || String(d.numero).toLowerCase().includes(termo),
  );

  return (
    <Stack gap="sm">
      <Title order={3} c="navy.9">Cotações</Title>
      <DataTable
        withTableBorder
        borderRadius="md"
        striped
        highlightOnHover
        fetching={carregando}
        records={visiveis}
        idAccessor="id"
        columns={[
          {
            accessor: "numero",
            title: "Nº MSSC",
            sortable: true,
            // Funil de busca no cabeçalho DESTA coluna (aparece porque `filter` está definido);
            // `filtering` deixa o funil "aceso" quando há termo. A filtragem em si é o records.filter acima.
            filter: (
              <TextInput
                label="Buscar Nº MSSC"
                placeholder="Digite o número…"
                value={buscaNumero}
                onChange={(e) => setBuscaNumero(e.currentTarget.value)}
              />
            ),
            filtering: termo !== "",
          },
          { accessor: "data", title: "Data" },
          { accessor: "anexos", title: "Anexos", textAlign: "right" },
        ]}
        noRecordsText="Nenhum registro."
      />
    </Stack>
  );
}
