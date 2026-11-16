# Sono da memória — conferir, juntar e marcar o estado das notas

## Estado atual
**Parte 1 (acervo) — 0.62.0, na branch `feature/sono-da-memoria-acervo`, aguardando o OK do owner.** Cada anotação de
`memory/` carrega `conferida: <data> — <confirmada|não confirmada|conflito> — fonte: <arquivo:linha>`; conflito leva
no corpo `CONFLITO: <fonte A, data> diz …; <fonte B, data> diz …`, sem escolher lado. O `memoria_indice.py verificar`
cobra o formato; o `memoria_indice.py sono` dá o roteiro; o passo a passo da passada mora em `commands/memory.md`
("Uso interno: sono"), com ajudantes pesquisadores que só leem. A tabela de memória copia o campo na coluna `estado`
e guarda na linha de controle a data do último sono e o "agora não" do owner (`memoria_tabela.py adiar-sono`). Na
abertura, o `hooks/memoria_tabela_em_dia.py` conta só nome e data das conversas do projeto desde o último sono; com 10
ou mais, pede ao assistente que ofereça o sono em 1 linha.

Fora de escopo: ler as conversas (parte 2), completar os 4 comandos cortados (esperam o owner), regenerar as frases dos
subíndices e medir o uso das notas (itens 4.1 e 4.3 de `docs/analise/2026-11-13-sono-da-memoria.md`).

## O que o owner decidiu
> Quem abrir este assunto numa conversa nova lê esta seção primeiro. Nada aqui se reabre.

1. O sono é em duas partes, uma conversa cada: parte 1 = acervo (esta); parte 2 = ler as conversas novas e corrigir
   ou recuperar memória, no formato que a parte 1 define (`docs/analise/2026-11-13-sono-da-memoria.md`, seção 5).
2. A parte 1 é uma passada única que (a) junta duplicatas aposentando com `obsoleta: <data> — superada por [[slug]]`
   (nunca apaga arquivo nem fato), (b) marca CONFLITO com as duas fontes e datas sem escolher lado, (c) conserta as
   citações mortas (`python templates/memoria_indice.py citacoes`), (d) grava o estado de cada nota.
3. As conversas (transcripts) não entram na tabela de memória (`docs/decisoes.md:68`); o caminho é conversa → sono →
   `memory/` → a tabela se atualiza sozinha (`docs/decisoes.md:69`).
4. Sem comando pro owner lembrar e sem tarefa agendada: o gatilho é um aviso de 1 linha oferecido pelo assistente; o
   owner só responde sim.
5. Saída: uma branch com o diff pro OK do owner antes de qualquer merge.
6. Medição de partida (2026-11-13): 40 citações mortas; 0 de 78 anotações com `obsoleta:`; 0 com estado; 4 anotações
   com comando cortado (aguardam o owner). Meta: 40 → 0 citações mortas e o número de duplicatas e conflitos achados.
7. Credencial nunca entra em nota: `*****` e onde o valor vive.
8. **Estado no frontmatter:** `conferida: <data> — <confirmada|não confirmada|conflito> — fonte: <arquivo:linha>`.
9. **A tabela de memória ganha a coluna de estado**, copiada desse campo (o arquivo é o original, a tabela a cópia —
   `docs/specs/memoria-em-tabela.md:12`); a mudança é no `templates/memoria_tabela.py`.
10. **Aviso com 10 conversas sem sono.** Quem conta é o `hooks/memoria_tabela_em_dia.py` na abertura; a data do último
    sono fica na linha de controle da tabela (`tipo = 'controle'`). Nada de hook novo.
11. Nota mais velha que a conversa mais antiga (2026-08-14) fica com o estado da conferência contra o repositório —
    não vira "não confirmada" pela idade.
12. Só as anotações de `memory/` ganham estado; diários, decisões e casos do EVALS servem de fonte e recebem só a marca
    de conflito ou duplicata.
13. Ajudantes pesquisadores autorizados nesta conversa (uns 6, famílias pequenas agrupadas), como exceção ao "sem
    subagentes" do nível médio (`commands/nova-feature.md:14`), porque `docs/decisoes.md:71` prevê o pesquisador para
    muitos arquivos. Eles só leem; quem grava é a conversa principal.

14. **Correção posterior clara não é conflito** (critério do cookbook, revisão do owner em 2026-11-13): fica o
    valor atual, a nota fica **confirmada** contra a fonte nova e ganha a linha `substituiu: <velho> (<fonte, data>)`.
    Dois números de momentos diferentes também não: ficam os dois, cada um com a data. `CONFLITO` só quando duas
    fontes discordam e nenhuma diz qual vale.
15. Antes do merge, conferir que o recall não devolve o que o sono aposenta (`obsoleta:`/`pausada:`), porque o sono
    vai gerar mais `obsoleta:`.

## Escolhas do assistente (o owner pode trocar)
- **O que vale cada estado:** confirmada = há fonte no repositório hoje que diz o mesmo (código, spec, decisão, caso
  do EVALS ou diário), citada como `arquivo:linha`; não confirmada = nenhuma fonte achada; conflito = duas fontes
  discordam — o corpo da nota ganha `CONFLITO: <fonte A, data> diz …; <fonte B, data> diz …`, sem escolher lado; frase
  solta nunca derruba decisão registrada.
- **Duplicata só se funde entre anotações de `memory/`**: fatos e linhas datadas vão pra que fica; a outra ganha
  `obsoleta:` e sai do subíndice (`commands/memory.md:64`). Em `docs/decisoes.md` e `docs/EVALS.md` nada é fundido nem
  reescrito.
- **Citação morta, uma de três saídas:** caminho mudou → corrige; exemplo de outro projeto → `<projeto>/arquivo` (o
  verificador já pula `<`); arquivo que existiu e saiu → aponta o sucessor e o nome antigo sai da crase. A regra do
  verificador não muda.
- **Data do último sono:** a conferência mais nova entre as anotações, copiada pra linha de controle no `montar`
  (tabela apagada e remontada não perde a data). "Agora não" do owner também fica na linha de controle e a conta
  recomeça dali.
- **O aviso conta só nome e data** dos arquivos de conversa do projeto, nunca o conteúdo; vai pro assistente, que
  oferece 1 linha uma vez por conversa.
- **A captura não carimba estado:** anotação nova nasce "nunca conferida" e entra no próximo sono.
- **O roteiro do sono mora em `commands/memory.md`, "Uso interno: sono"** — não é modo do owner (`docs/decisoes.md:69`).

## Critérios de aceite
1. DADO uma anotação com `conferida:` fora do formato (data, estado ou fonte), QUANDO rodo `verificar`, ENTÃO ela é
   acusada pelo nome; no formato certo, passa; sem o campo, passa (nunca conferida não é erro).
2. DADO anotações com e sem `conferida:`, QUANDO rodo `memoria_indice.py sono`, ENTÃO sai o roteiro: contagem por
   estado, as nunca conferidas, as citações mortas e as duplicatas pelo método de hoje.
3. DADO uma anotação com `conferida:`, QUANDO rodo `montar`, ENTÃO a linha dela na tabela tem a coluna `estado` com o
   estado e a data; a linha de controle guarda a data do último sono (a conferência mais nova).
4. DADO a data do último sono e 10 ou mais arquivos de conversa do projeto mudados depois dela, QUANDO a conversa
   abre, ENTÃO o hook devolve ao assistente 1 recado de sono atrasado; com 9 ou menos, nada; o hook não lê o conteúdo
   das conversas.
5. DADO o owner respondeu "agora não", QUANDO rodo `memoria_tabela.py adiar-sono`, ENTÃO a data fica na linha de
   controle e a conta recomeça dali; remontar a tabela não perde o adiamento.
6. DADO o kit depois da passada, QUANDO rodo `citacoes`, ENTÃO 0 citações mortas; toda anotação não obsoleta tem
   `conferida:` válido; nenhuma duplicata fica sem `obsoleta:`.

## Conferido no real (2026-11-13, a passada no kit)
- **Leitura:** 6 ajudantes pesquisadores (só leitura), famílias pequenas agrupadas; um deles só para decisões, EVALS
  e diários. Quem gravou foi a conversa principal, por scripts idempotentes fora do repositório.
- **Estado das 78 anotações:** 75 confirmadas · 1 não confirmada (`project_troca_por_script_em_arquivo_crlf`) ·
  2 em conflito, que o owner decide depois:
  - `feedback_frontend_tailwind_arquivos_separados` — "sempre Tailwind" (regra crítica) × "onde a Mantine entra, o
    Tailwind sai" (`templates/FRONTEND.md:22`);
  - `project_hook_stop_devolve_por_json_nao_por_exit_2` — `UserPromptSubmit` com exit 0 × exit 2 no hook real
    (`hooks/um_item_por_janela.py:359`) — precisa de teste no app real.
- **Correção posterior (revisão do owner, decisão 14):** a passada marcou 9 conflitos; 7 eram correção posterior
  clara e ficaram confirmadas com `substituiu:` — `feedback_feature_a_partir_da_master` (fica `--no-ff`,
  `CLAUDE.md:21`); `feedback_publicacao_e_ato_do_owner` e `project_memoria_local_ao_repo` (fica nunca worktree,
  `docs/decisoes.md:50`); `feedback_testar_js_gerado_node_check` (fica `tests/test_bpmn.py:564`);
  `project_mss_spec_instalado_por_junction` (fica `docs/AMBIENTES.md:20`); `project_pendencia_intermitencia_pos_update`
  (fica F-050); `feedback_medir_a_partida_inteira_nao_o_arquivo_acusado` (dois números de momentos diferentes, os
  dois com data).
- **O recall e o que o sono aposenta (decisão 15):** a anotação `obsoleta:` não volta (`templates/memoria_indice.py`,
  `fontes`) e a linha com status `obsoleta:`/`pausada:` também não (teste `test_recall_pula_linha_pausada_ou_obsoleta`).
  **Brecha achada e fechada:** anotação `obsoleta:` que ficasse com linha no subíndice voltava pelo recall, e o
  `verificar` não acusava — agora o `verificar` acusa e o recall pula a linha (teste
  `test_obsoleta_que_ficou_no_subindice_e_acusada_e_nao_volta_pelo_recall`).
- **Duplicatas de anotação: 0.** Um parágrafo repetido (o guardião retirado) em duas anotações da junção virou
  link pra `project_sandbox_do_claude_nao_registra_tarefa_agendada`, que já tinha o fato inteiro.
- **Citações mortas: 40 → 0** (17 em `memory/`, 23 em `docs/specs/`): exemplo de outro projeto virou
  `<projeto>/…` ou `<Whats>/…`; arquivo que saiu ficou fora da crase com o sucessor.
- **Endereço velho:** 6 anotações diziam que a regra sempre-ativa mora em `templates/CLAUDE.md`; hoje mora em
  `templates/regras-do-kit/` (o molde só leva a marca) — corrigido.
- **`docs/EVALS.md`:** 4 correções posteriores marcadas com `substituiu` (F-022 e F-032: nunca worktree; F-030: o
  recall não lê mais fora de escopo, e pular `obsoleta:`/`pausada:` segue valendo; F-036: fechado em 2026-10-20,
  título do bloco acertado) e 2 duplicatas possíveis (F-051 × F-028; F-060 × F-047). **`docs/decisoes.md`:** a de
  2026-07-30 marcada como substituída (revertida em 2026-10-30).
- **Credencial:** nenhuma, nas anotações, nos diários, nas decisões nem no EVALS.
- **Observado, sem mexer:** `docs/decisoes.md:62` cita uma decisão de 2026-07-22 que não está no arquivo; os 4
  comandos cortados seguem esperando o owner.

## Histórico
- 2026-11-13 — revisão do owner: correção posterior clara não é conflito (7 dos 9 viraram confirmadas com
  `substituiu:`; 2 ficam pra ele); conferido que o recall não devolve o que o sono aposenta, e fechada a brecha da
  linha de subíndice esquecida (motivo: critério do cookbook; o sono vai gerar mais `obsoleta:`).
- 2026-11-13 — criado: parte 1 do sono (acervo) — estado no frontmatter e na tabela, aviso de 10 conversas no hook de
  abertura, passada com ajudantes pesquisadores (motivo: análise `docs/analise/2026-11-13-sono-da-memoria.md`; nota
  errada vira armadilha e ninguém relia o acervo — 40 citações mortas, 0 notas conferidas).
