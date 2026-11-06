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
- Pós-merge: "a atualização do marketplace local" foi dita como passo pós-push (no MAPA e em 2 respostas) com a
  junção ainda viva — a decisão de 03/11 foi lida como estado; o owner perguntou *"com o comando upgrade ou
  doctor?"*, o disco (`ls -ld ~/.claude/skills/mss-spec`) mostrou a junção, MAPA refeito 2× (`f416353`,
  `05dd0b9`). Caso F-052; regex da memória da junção ampliado + teste.
- O fecho depois do merge falou só dos merges e do push; o owner: *"você não tocou só as tarefas com esforço
  baixo, ainda faltam a média e alta"* — estava tudo feito. Resposta virou tabela item → commit por esforço;
  memória `feedback_fecho_de_entrega_lista_os_itens`.

## Rejeitado
- KB em banco + cache + outbox + sync por checksum; multi-agente por domínio; lembrete pós-compactação em
  texto à parte; auto-reparo de ambiente (a SI vetou automação em 03/11); apresentação HTML.
- "Junte todas as dúvidas numa pergunta só" (regra de lá): registrada como diferença, não absorvida.
- Item 10 (BOM nos `.sql`): já existia no `inventario_banco.py`, com teste.

## Fizemos
- 10 commits na branch: item 2 (bug.md, com o dossiê — o commit só do dossiê foi barrado pelo hook do
  heredoc com acento e entrou aqui) · itens 13/6/11 (regras do kit) · itens 7/8/9 (`verificar` +
  `citacoes`) · item 3 (`decisao_junto.py`) · item 1 (procedimento) · regeneração das linhas do kit ·
  item 4 (dicionário/conceitos) · item 12 (envio externo + regra + memória) · item 5 (`banco_producao.py`)
  · fecho (CHANGELOG 0.53.0, manifestos, decisões, MAPA, diário). Suíte: 1.225 verdes.
- Merges `--no-ff` na `main` (owner: *"Pode fazer os merges e tudo mais eu só rodo o git push"*): 0.52.0
  (`62e5239`) antes da 0.53.0 (`51b2160`); conflitos mantendo os dois lados — `CHANGELOG.md` mais novo em
  cima, `docs/decisoes.md` cronológico, `MAPA-historico.md` mais novo em cima; manifestos e MAPA na 0.53.0.
  Suíte na `main`: 1.231 verdes. Push do owner (`fd2d7fb`); MAPA reconciliado depois (`f416353`, `05dd0b9`,
  `e25de49`).
- Segurança reportada ao owner, sem valores: senha em texto em `config.json`, `.mcp.json`, numa decisão do
  KB e dentro do `trp/agent.md` de lá; `settings.json` em `auto` com `Write/Edit` liberados.

## Próximo
- Owner: `git push origin main` (captura + correções do MAPA); apagar a tarefa agendada se chegou a existir.
- Conversa nova: trocar a junção pelo marketplace local (decisão 2026-11-03, receita no `PROXIMO-PASSO.md`);
  só depois disso "marketplace update" vira passo pós-publicação (e a memória da junção vira `obsoleta:`).
- `/mss-spec:upgrade` no Whats, no Transportes e no Energy quando abrir cada um — escrever a linha
  **Hosts de produção (cerca)** no `AMBIENTES.md` de cada um; `doctor` só mede.
- Dogfood: as 40 citações mortas do próprio kit (`memoria_indice.py citacoes`) — corrigir caminho ou
  marcar `obsoleta:`.
- Autoria do kit de lá segue `<a confirmar>` (owner disse "outra empresa"; os arquivos apontam Rafael
  Formenton, MSIG).
