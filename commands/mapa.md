---
description: Lê e reconcilia o mapa de contexto do projeto (docs/superpowers/MAPA.md) — onde estamos · próximo passo · conexões com outros projetos MSIG
argument-hint: "(sem argumento — lê e atualiza o mapa)"
---

**Responda sempre em português (pt-BR).**

Você vai **ler e reconciliar** o **mapa de contexto** do projeto — `docs/superpowers/MAPA.md`, o ponto de partida anti-amnésia (curto, 1 tela). Este comando cuida **só do mapa local deste projeto**; a visualização agregada entre projetos (mapa neural HTML) é outra capacidade.

**Nunca invente fatos concretos.** Conexões, endpoints, filas, tabelas — declare só o que está no código/repo ou o que o owner confirmar. Na dúvida, deixe genérico ou marque `<a confirmar>`. Uma conexão errada é pior que uma lacuna.

1. **Localize o mapa.** Se `docs/superpowers/MAPA.md` **não existe**, avise e ofereça criá-lo a partir de `${CLAUDE_PLUGIN_ROOT}/templates/MAPA.md` (se a variável não resolveu, procure em `~/.claude/plugins/cache/*/mss-spec/*/templates/`). Se existe, leia-o.
2. **Reconcilie "Onde estamos"** com as fontes vivas: `git` (branch atual + tipo pelo prefixo `feature/`|`fix/`|`refactor/`) e o `docs/superpowers/INDEX.md` (qual tarefa está **em andamento**). Regenere esta seção em 1 linha — é derivada, então sobrescreva sem cerimônia.
3. **Reconcilie "Conexões"** relendo o **código de integração** deste projeto (routers/endpoints que outro sistema chama, clients HTTP para outros serviços, filas, banco/tabela compartilhados). **Proponha** adições/remoções ao que está no mapa e confirme com o owner — **não apague** à revelia uma conexão que o owner declarou, nem invente uma nova. Formato: `→ <projeto>: envia/consome (ponto)` / `← <projeto>: expõe/recebe (ponto)`.
   **Se existe `docs/superpowers/CONEXOES.md`** (o rodízio da partida já tirou o detalhe do MAPA): reconcilie as linhas detalhadas **lá**, nesse formato. No MAPA, a seção Conexões fica com **só os nomes**, numa linha só, no formato do rodízio: `- Detalhe em [CONEXOES.md](CONEXOES.md) (contratos, tokens, topologia). Conexões: <nome> · <nome> · <nome>.` Nunca devolva ao MAPA rota, arquivo, variável ou host: é isso que o faz estourar o teto a cada integração nova (Whats, 2026-10-23). Linha detalhada que ainda estiver no MAPA vai pro `CONEXOES.md` (mover, nunca apagar) e o nome entra na lista.
4. **Confirme/edite "Próximo passo"** comigo: qual é a próxima ação concreta pra retomar. Se eu não disser, proponha a partir do estado (tarefa em andamento no INDEX + spec aberta). **Uma linha curta por item, com o título em negrito**: `N. ⬜ **título** — detalhe em [PROXIMO-PASSO.md](PROXIMO-PASSO.md)`; o detalhe (comando, número, arquivo, condição) vai pro `docs/superpowers/PROXIMO-PASSO.md`, no topo, com a data. Item de mais de 300 bytes que ficar no MAPA o hook `teto_ao_gravar.py` move sozinho ao gravar (mesmo abaixo do teto) — escreva já na forma pra ele não reescrever o que você acabou de escrever.
5. **Grave** o `MAPA.md` atualizado e ajuste a data do rodapé (`Atualizado em <data>`). Mostre o mapa final.

**Não inche o mapa:** só as 3 seções (Onde estamos · Próximo passo · Conexões). Detalhe de tarefa vive na spec viva; aprendizado, na `memory/`. Se uma seção crescer demais, é sinal de que o conteúdo pertence a outro lugar.
