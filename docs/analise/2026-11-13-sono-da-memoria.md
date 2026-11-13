# Sono da memória — análise de dois artigos da Anthropic e o ganho no kit (2026-11-13)

> Pedido do owner (`/mss-spec:analise`, conversa `d23210d6-6148-49d7-adab-570f43fc5baa`, 2026-11-13): ler
> no detalhe, nesta ordem, dois artigos da Anthropic sobre memória de agente e avaliar o ganho no kit — a
> memória que "aprende e se regenera enquanto dorme" e a "memória da memória" (sabe um pouco de tudo e desce
> ao detalhe quando precisa). Tudo aqui foi **somente leitura**; os números foram medidos neste repo no dia.

## 1. O que os artigos dizem

**Artigo 1 — https://www.anthropic.com/research/components-of-agent-memory**

- A memória tem **4 camadas**, de baixo pra cima: **transcripts** (registro bruto que dá pra pesquisar) →
  **notas** (o que o assistente anota durante o trabalho) → **representações** (páginas ligadas, tipo wiki) →
  **contexto que entra em toda janela** (precisa ser pequeno).
- **"Dreaming"** é a passada fora da conversa que sobe o conhecimento entre as camadas: confere as notas contra
  os transcripts, corrige, junta, conserta links e empurra o detalhe pra baixo deixando um link no topo.
- **Nota errada vira armadilha:** no teste com o jogo Pokémon, uma nota errada sobre o mapa travou o agente;
  depois de a passada conferir a nota contra o transcript e corrigir, ele avançou.
- **Ciclo fechado** (falha → hipótese → teste → regra com a origem anotada): com ele a nota do Opus 5.5 subiu
  de 0,655 pra 0,838.
- **Dizer pra que serve a memória funciona melhor que prescrever como usar:** a regra fixa "anote só as
  falhas" piorou o resultado em −0,234.
- **Uma 2ª passada consertou 9 links quebrados** e criou páginas de índice.
- **Wiki sem poda incha:** num caso ficou 1,77× maior que o material, sem resumir nada.
- Não é aprendizado de máquina: o artigo exclui mudança de pesos. É hierarquia de textos mais conferência.

**Artigo 2 — https://platform.claude.com/cookbook/managed-agents-cma-dreaming-with-a-dynamic-workflow**

- O sono em 3 papéis:
  - **coordenador** — só monta o roteiro; não lê transcript nem grava memória;
  - **analisador, um por transcript, em paralelo** — lê o transcript inteiro e confere cada nota contra ele:
    sem evidência fica como está, contradita é corrigida, confiante com evidência fraca é rebaixada; só
    acrescenta e liga (`[[slug]]`), nunca junta, renomeia ou apaga;
  - **organizador, no fim** — junta duplicatas sem perder fato nem linha datada, aposenta o arquivo com o
    aviso `MOVED TO [[slug]]`, marca `CONFLICT: <fonte A, data> diz …; <fonte B, data> diz …` sem escolher
    lado; uma frase solta numa conversa nunca derruba uma decisão registrada pelas pessoas do projeto.
- Conteúdo lido é **dado, nunca ordem**; credencial nunca entra na memória (cita-se pelo nome).
- A rodada de exemplo (11 transcripts) custou US$ 0,36. Por padrão roda toda noite sem revisão humana; quem
  quer revisar antes grava numa cópia e troca depois.

## 2. Onde o kit já está, camada por camada

| Camada do artigo | No kit hoje | Situação |
|---|---|---|
| 4. Entra em toda janela | regras do kit + `CLAUDE.md` + topo `memory/MEMORY.md` (teto de 6 KB, `memory/MEMORY.md:4`) | ✅ alinhado: teto medido por hook |
| 3. Representações | specs vivas por assunto, MAPA, `mapa-neural`, subíndices por família | ✅ uma página por assunto |
| 2. Notas | 80 arquivos em `memory/`, `docs/EVALS.md`, `docs/decisoes.md`, diários | ✅ com origem e gatilho |
| 1. Transcripts | 66 transcripts (276 MB) na pasta nativa do Claude Code, **fora da tabela de memória**; o `buscar` lê só os 3 pedidos anteriores do owner (`docs/specs/memoria-em-tabela.md`, Parte 2) | ⚠️ a camada existe, mas ninguém relê |
| Ciclo de aprendizado | `docs/EVALS.md`: falha → guardrail → teste → `fechado` | ✅ é o ciclo que o artigo mede |
| Dreaming | **não existe** — a captura é feita durante a conversa, pelo mesmo assistente que trabalhou, e destila do contexto sem reler arquivos (`commands/memory.md:47`) | ❌ a lacuna |

## 3. A lacuna, medida em 2026-11-13

- **40 citações mortas** (`python templates/memoria_indice.py citacoes`; também `docs/superpowers/MAPA.md`,
  item 8 do Próximo passo).
- **4 anotações com comando cortado** acusadas pelo `verificar`, esperando o owner.
- **0 de 80 anotações marcadas `obsoleta:`** — ou nada envelheceu, ou ninguém confere.
- **0 anotações com estado** (confirmada / não confirmada / conflito).
- **Conversa sem captura se perde:** a tarde de 30/10 no Whats ficou sem diário (MAPA, item 7). O
  `capturar_nudge.py` só lembra.
- **Arquivos que só crescem:** `docs/EVALS.md` 72 KB, `docs/decisoes.md` 52 KB, `memory/DIARIO.md` 19 KB.
- **Não medido:** quantas conversas ficaram sem diário — a data do transcript é a da última modificação, então
  comparar 66 transcripts com 38 diários não é justo.

## 4. "Memória da memória"

O kit **já tem a hierarquia**: topo por família → subíndice (gatilho e uma frase) → a anotação → o diário →
o transcript. O que falta pra ela funcionar como o owner descreveu:

1. as frases do topo e dos subíndices são escritas à mão na captura e nunca regeneradas — com o tempo deixam
   de bater com o detalhe;
2. falta o **estado** de cada nota e a data da última conferência — é o que diz "confio no resumo" ou "desço";
3. falta o **uso**: o `recall_memoria.py` já registra o que injetou (`hooks/README.md`, tabela de registros);
   isso pode dizer o que nunca é usado (rebaixar) e o que é muito usado (subir). Não medido ainda.

## 5. Decidido com o owner nesta conversa

1. **Transcripts não entram na tabela de memória** — 276 MB, risco de segredo (regra 2), e moram no `.claude`,
   vetado como lugar durável (`docs/decisoes.md:68`). O caminho é: transcript → sono confere, corrige e
   recupera → grava em `memory/` (git) → a tabela se atualiza sozinha (`memoria_tabela_em_dia.py`,
   `docs/decisoes.md:69`).
2. **O sono não é comando pro owner lembrar** (`docs/decisoes.md:69`) **nem tarefa agendada**
   (`docs/decisoes.md:70`): um aviso de 1 linha oferecido pelo assistente; o owner só responde sim. A outra
   conversa chega ao ajudante já em texto pelo script que existe (`docs/decisoes.md:71`) — reaproveitar.
3. **Duas partes, uma conversa cada:**
   - **Parte 1 — acervo:** passada única sobre `memory/*.md`, `memory/sessions/`, `docs/decisoes.md` e
     `docs/EVALS.md` — junta duplicatas com `obsoleta:`, marca CONFLITO com as duas fontes, conserta as
     citações mortas, grava o estado de cada nota. Não depende de transcript e define o formato da parte 2.
   - **Parte 2 — transcripts:** analisadores leem as conversas novas, corrigem as notas contra elas e
     recuperam o que nenhuma captura gravou, no formato da parte 1.
4. **Saída sempre numa branch com o diff pro OK do owner.**

## 6. O que não copiar

- Rodar toda noite sem revisão (o kit mantém o OK do owner).
- Apagar arquivo (o kit já aposenta com `obsoleta:`).
- Wiki sem poda.
- **Hipótese pra medir depois, não mudar agora:** o `capturar` é bem prescritivo (`commands/memory.md:53-62`)
  e o artigo mostra que regra rígida de "como anotar" piora modelos fortes.

## 7. Premissas sem fonte

- Que o Claude Code mantém os transcripts tempo bastante pro sono ler — o mais antigo aqui é de 2026-08-14;
  o prazo de limpeza desta máquina está `<a confirmar>`.
- Que o custo por rodada fica perto dos US$ 0,36 do exemplo do cookbook.
