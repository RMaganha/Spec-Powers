# 2026-11-06 — benchmark MSIG_Agentes: o que o kit da equipe tem de melhor entra no mss-spec

Branch `feature/absorver-msig-agentes` (da `main` em `4d28026`), 0.53.0. Dossiê:
`docs/analise/2026-11-06-benchmark-msig-agentes.md`.

## Conversamos
- O owner abriu o `/mss-spec:analise` apontando o kit de agentes que a equipe MSIG usa
  (`C:\Ronaldo\_Mitsui\Python\MSIG_Agentes`): "capturar o máximo de conteúdo útil que podemos implementar
  no meu plugin", "que fique claro: não quero misturá-los".
- Levantamento somente-leitura (âncora no kit): 6 arquivos do núcleo inteiros ou nas seções que importam
  (`CLAUDE.md`, `AGENTS.md`, 2 commands, `settings.json`, `kb.py` por estrutura) + hooks de rotina; os 24
  `agent.md` lidos inteiros (21 por subagente) depois que o owner perguntou "não é melhor ler todos?".
- Tabela de 13 melhorias por esforço e ganho; o owner pediu a coluna "quanto eu ganharia", depois
  "vamos implementar, tudo aqui, baixo → médio → alto, deixando o que temos separado pra voltar com git".

## Pivôs
- O comando `analise` grava `docs/ARQUITETURA.md` do projeto analisado; aqui o projeto é de fora e já
  tinha o dossiê de 04/11 → o benchmark foi pra `docs/analise/` do kit (onde já viviam as análises de
  outros modelos), sem tocar em `ARQUITETURA.md`.
- A cerca de produção de lá tem lista de hosts embutida; aqui os hosts saem do `docs/AMBIENTES.md` de cada
  projeto (linha explícita vence, heurística cobre quem não a escreveu).
- Decisão de comportamento: cogitado estender o `capturar_nudge.py` (por tempo); ficou um hook próprio
  por arquivo gravado (`decisao_junto.py`), no contrato do `diario_junto.py`.
- O modo `citacoes` do `memoria_indice.py` achou 63 citações no próprio kit; 23 eram ruído (`~/`, exemplos
  `x.sql`, moldes que o kit gera em outros projetos) → filtros; as 40 restantes são dívida real do kit.
- `hooks/banco_producao.py`: a 1ª gravação foi barrada pelo `regra_antes_de_gravar` (nome casa a regra de
  banco) — regravado igual, como a regra manda.

## Rejeitado
- KB em banco + cache + outbox + sync por checksum; multi-agente por domínio; lembrete pós-compactação em
  texto à parte; auto-reparo de ambiente (a SI vetou automação em 03/11); apresentação HTML.
- "Junte todas as dúvidas numa pergunta só" (regra de lá): registrada como diferença, não absorvida.
- Item 10 (BOM nos `.sql`): já existia no `inventario_banco.py`, com teste.

## Fizemos
- 14 commits: dossiê · item 2 (bug.md) · itens 13/6/11 (regras do kit) · itens 7/8/9 (`verificar` +
  `citacoes`) · item 3 (`decisao_junto.py`) · item 1 (procedimento) · regeneração das linhas do kit ·
  item 4 (dicionário/conceitos) · item 12 (envio externo + regra + memória) · item 5 (`banco_producao.py`)
  · fecho (CHANGELOG 0.53.0, manifestos, decisões, MAPA, diário).
- Segurança reportada ao owner, sem valores: senha em texto em `config.json`, `.mcp.json`, numa decisão do
  KB e dentro do `trp/agent.md` de lá; `settings.json` em `auto` com `Write/Edit` liberados.

## Próximo
- Owner: ordem de merge entre esta branch (0.53.0) e a `feature/teto-avisa-uma-vez-e-upgrade-sem-refazer-infra`
  (0.52.0); `--no-ff` na `main` com a aprovação dele; push é dele; depois a atualização do marketplace local.
- Autoria do kit de lá segue `<a confirmar>` (owner disse "outra empresa"; os arquivos apontam Rafael
  Formenton, MSIG).
- Dogfood: as 40 citações mortas do próprio kit (`memoria_indice.py citacoes`) — corrigir caminho ou
  marcar `obsoleta:`; e escrever a linha **Hosts de produção (cerca)** no `AMBIENTES.md` do Whats, do
  Transportes e do Energy quando abrir cada um.
