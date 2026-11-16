# 2026-11-16 — sono da memória, parte 2: as conversas

conversas lidas até: 2026-11-15

> O dia da rodada fica de fora de propósito: as conversas de 2026-11-16 (esta inclusa) ainda podem mudar, e a próxima
> rodada as relê (`conversa_texto.py lote --desde 2026-11-15`).

## Conversamos
A parte 2 do sono: ler as conversas gravadas do projeto e corrigir, rebaixar ou recuperar memória no formato da
parte 1. Desenho aprovado pelo owner com 2 ajustes: só rebaixa com fala que mostra falha ou dúvida (ausência de
prova nunca rebaixa); decisão do owner achada só na conversa vai para `memory/` e para `docs/decisoes.md`, marcada
"recuperada no sono".

## Pivôs
- **"Enfraquece" dos ajudantes era, na maioria, reincidência.** A 1ª leva marcou como "enfraquece" o assistente
  descumprindo uma regra logo depois de ela nascer. Isso mostra que a regra foi violada, não que o conteúdo está
  errado — a instrução das levas seguintes separou `reincidência` de `enfraquece`. Resultado: **0 rebaixadas**.
- **Achado conferido na fala antes de gravar.** Os 7 "enfraquece" viraram: 2 correções (credencial; infra que o
  repositório já mostra), 2 parágrafos novos em notas confirmadas (texto pronto curto; colunas da tabela do fecho),
  1 nota em conflito que fica fora (Tailwind × Mantine), 1 sem mudança (screenshot único no bpmn, sem fala do owner)
  e 1 reincidência.
- **Fonte nunca no `.jsonl`:** a evidência entrou antes no diário — 27 diários retroativos e 17 blocos
  "Acrescentado no sono" — e as notas citam o diário.

## Rejeitado
Rebaixar nota por reincidência do assistente; gravar decisão a partir de relato do assistente sem fala do owner
(Fernet "só para ciência"); gravar como decisão a fala única do owner sobre não rodar a suíte inteira (fica como
evidência do item aberto no `to-dolist.md`).

## Fizemos
**Código (0.63.0):** `conversa_texto.py lote`; `conversas lidas até:` no roteiro do `sono` e como último sono no
`montar`; o `verificar` acusa fonte em `.jsonl`; passo a passo da parte 2 em `commands/memory.md`.

**A rodada:**

| Medida | Número |
|---|---|
| Conversas lidas | 67 gravações (66 conversas: 1 gravada duas vezes), 3.083.103 letras |
| Ajudantes | 14 `mss-spec:pesquisador`, em levas; 2.402.331 tokens, 559 leituras |
| Notas corrigidas pela conversa (confirmada + `substituiu:`) | 4 — `feedback_credencial_reusar_env_precedente`, `project_marketplace_relative_path_serve_git_e_local`, `feedback_visualizacao_usa_lib_consagrada`, `project_kit_nao_assume_ambiente_de_origem` |
| Não confirmada → confirmada | 1 — `project_troca_por_script_em_arquivo_crlf` |
| Notas confirmadas com aprendizado acrescentado | 2 — `feedback_texto_pronto_pra_colar`, `feedback_fecho_de_entrega_lista_os_itens` |
| Rebaixadas | 0 |
| Anotações novas | 14 (1 user, 2 reference, 3 project, 8 feedback) |
| Decisões recuperadas | 1 (correção do kit vale pro kit todo) + 2 linhas velhas de `docs/decisoes.md` marcadas como substituídas (`:11`, `:19`) |
| Diários recuperados | 27 retroativos (30 conversas sem diário) + 17 blocos em diários que cobriam só parte da conversa |
| Credencial | senha dita em texto em 4 falas de uma conversa de 2026-07-10 — não copiada (`*****`) |
| Uso da conversa principal | 445 mil tokens de janela (45%) ao fim da gravação |

**Reincidências vistas, sem mexer nas notas** (o sono não reescreve o EVALS) — as mais repetidas:
`feedback_nao_encerrar_com_pergunta`, `feedback_resposta_do_tamanho_do_pedido`, `feedback_feature_a_partir_da_master`
e `project_mss_spec_instalado_por_junction` (estas anteriores ao F-034). Duas não estão no `docs/EVALS.md`: o F-065
(dois textos prontos de uma vez) em 2026-11-12 e 2026-11-13, e o F-067 (MAPA com dois blocos) pela 3ª vez em 2026-11-16.

## Próximo
- Owner: OK do diff e merge da `feature/sono-da-memoria-conversas`.
- Vistos, sem mexer: `commands/upgrade.md` ainda manda perguntar a infra quando falta a linha; suspeita de o hook da
  passagem não reconhecer o título com acento; o aviso da passagem disparou num texto que o owner colou só para
  reclamar; o `Stop` do F-035 acusa padrão do `.gitignore` como arquivo; `project_mss_spec_instalado_por_junction`
  diz "ao mesclar na main", e a conversa de 2026-10-27 mostra que com a junção o plugin segue a branch aberta na pasta
  do kit (conversa mais velha que a linha: não corrigi).
