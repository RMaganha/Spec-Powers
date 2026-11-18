# Próximo passo — detalhe

## 2026-11-17 — as 3 conversas depois da 0.65.0 (texto pronto para colar pelo +)

Escopo do owner, nesta ordem; as três são independentes (a 3ª pode correr junto, no projeto grande que ele indicar).

**1. Parte 3 — suíte do kit em camadas (pasta do kit)** — ✅ feita em 2026-11-18 (branch `refactor/suite-em-camadas`; diário `memory/sessions/2026-11-17-suite-em-camadas.md`)

```
/mss-spec:tarefa Reescrever a suíte do kit em camadas: a regra testada em memória, sem pasta.

Leia antes: memory/sessions/2026-11-17-suite-lenta.md, as linhas de 2026-11-17 em docs/decisoes.md, memory/feedback_teste_nao_cria_pasta.md e tests/test_hook_outro_projeto_shell.py (o modelo já reescrito).

Já decidido — não reabrir:
1. Teste não cria pasta nem arquivo. A regra é testada em memória (entra dado, sai decisão). Disco: 1 teste por hook, o da leitura e gravação de verdade. Processo python: 1 por hook. Git de verdade só no teste que conversa com o git, montado uma vez por arquivo, com git init --template=.
2. Onde o hook lê ou grava estado direto em arquivo, o código do hook muda para receber o estado como dado; o comportamento do hook não muda.
3. Na máquina roda só python templates/testes_do_que_mudou.py --rodar, uma rodada por vez, nunca a suíte inteira. A suíte inteira roda no GitHub Actions a cada push do owner.
4. Ordem, pelas pastas que cada arquivo cria por rodada — grupo 1: passagem_de_conversa 46, um_item_por_janela 39, confere_citacoes 36, banco_producao 30, regra_antes_de_gravar 29, pasta_e_branch 27, conversa_nova_acha_sozinha 26, kit_primeiro 26, teto_ao_gravar 25, regras_do_kit 22, orcamento_partida 20, memoria_de_acao 20, comando_inteiro 19, diario_junto 19, decisao_junto 18, registro 17, ancora_projeto_ativo 14, alerta_contexto 14, memoria_tabela_em_dia 14, capturar_nudge 13, sem_worktree 13 (leve: 12 testes usam a pasta só como texto do caminho), recall_memoria 12, memoria_da_proposta 11. Grupo 2: inventario_banco 56 (enxugar), migrar_claude_md 49, mapa_neural 41, memoria_tabela 37 e memoria_tabela_busca 32 (SQLite :memory:), conversa_texto 29, sono_da_memoria 27, memoria_indice 26, rodizio_partida 24, bpmn 22 (enxugar), memoria_gatilho_de_acao 15.
5. Os 15 testes que guardam caso do docs/EVALS.md ficam (test_evals_so_cita_teste_que_existe confere).
6. Branch a partir da main atualizada; um commit por arquivo reescrito; push é do owner.

Falta decidir:
1. Nada antes de começar; dúvida de desenho num hook → pergunte ao owner.

Regras desta conversa: o que está decidido não se reabre. Ao passar de 75% da janela, pare num arquivo fechado e entregue este texto atualizado para a próxima conversa.
```

**2. Molde de CI padrão para os projetos (pasta do kit)**

```
/mss-spec:nova-feature Molde de CI padrão para os projetos que usam o kit.

Leia antes: .github/workflows/testes.yml, a linha de 2026-11-17 sobre o CI em docs/decisoes.md, memory/reference_ci_do_kit_sem_login.md e o item "Molde de CI" do to-dolist.md.

Já decidido — não reabrir:
1. Nos projetos, a suíte inteira roda no CI a cada push; na máquina roda só o teste do que mudou (regra 9 do kit).
2. O kit já faz assim: .github/workflows/testes.yml, verde em 24 s. A lista dos testes que falharam sai numa anotação, legível sem login.
3. O molde chega aos projetos pelo /mss-spec:kickoff e pelo /mss-spec:upgrade; o owner tem projetos grandes (ATM Transporte, Atendimento WhatsApp, mss-utils e outros) e quer algo pronto e padrão para replicar.

Falta decidir:
1. Onde cada projeto fica hospedado (GitHub, Azure DevOps ou outro) e se é um molde por plataforma.
2. Como o CI instala as dependências de cada projeto e o que fazer com teste que precisa de banco ou serviço externo.

Regras desta conversa: o que está decidido não se reabre — mostre em lista única só as suas escolhas e pergunte de uma vez, no fim, o que só o owner decide.
```

**3. Custo dos hooks num projeto grande (pasta do kit; o projeto grande é só lido)**

```
/mss-spec:bug Os hooks do kit pesam em todo projeto, a cada ação do Claude; num projeto grande é pior.

Leia antes: hooks/hooks.json, o item "Medir o custo dos hooks" do to-dolist.md e memory/sessions/2026-11-17-suite-lenta.md.

Já decidido — não reabrir:
1. Fatos do hooks/hooks.json: cada comando de terminal dispara 5 processos python (git_publicacao e banco_producao antes; teto_ao_gravar, banco_producao --post e alerta_contexto depois); cada mensagem do owner dispara 5 (kit_primeiro, um_item_por_janela, recall_memoria, passagem_de_conversa, alerta_contexto); cada resposta dispara 5 (confere_citacoes, passagem_de_conversa, diario_junto, decisao_junto, capturar_nudge).
2. hooks/confere_citacoes.py:107 roda git ls-files -co, que lista todos os arquivos do projeto.
3. A máquina está OK (verificada pela TI e pelo suporte da Dell): não culpar a máquina.
4. Medir antes de mexer: o tempo de cada hook em cada evento, no projeto grande que o owner indicar; o projeto grande é só lido, o conserto é no kit.

Falta decidir:
1. Qual projeto grande serve de medida.
2. O conserto, depois da medição.

Regras desta conversa: o que está decidido não se reabre; nada de hipótese sem medição.
```

## 2026-11-10 — movido do MAPA.md

7. ⬜ **Conversa nova por item — memória em tabela (passo 1) e conferência antes de entregar (passo 2)** — **leia primeiro o registro das decisões do owner**: `docs/specs/memoria-em-tabela.md` (seção "Tudo o que o owner decidiu sobre a memória": 25 decisões; tabela, busca, consultar pela ação e ajudante pesquisador já entregues — 0.55.0 a 0.58.0; o comando guardado inteiro segue aberto) e `docs/specs/conferencia-antes-de-entregar.md` (6 decisões; nada construído). Régua de 944 casos e textos prontos em `docs/analise/2026-11-10-memoria-em-tabela-e-ci.md` (seção 9); ordem nos itens 8 a 15 do INDEX. Regra pra quem abrir: se algo do kit parecer proibir, não responda "o plugin não aceita" — mostre a regra e pergunte. Faltam do owner: a decisão GitLab × GitHub do CI do kit e se o aviso automático de 3 anotações troca de motor.

## 2026-11-06 — movido do MAPA.md

3. ⬜ **`/mss-spec:upgrade` no Whats e no Energy, quando abrir cada um** (**Transportes: ✅ feito em 2026-11-09, na pasta `Transportes\V2`** — a raiz `Transportes` não é repositório git, a janela abre na V2; o `docs/AMBIENTES.md` de lá nasceu com 34 "falta preencher", que só o owner preenche) — nasce o `docs/AMBIENTES.md`; com a 0.53.0, escrever a linha **Hosts de produção (cerca)** na seção Produção (a cerca `banco_producao.py` passa a ser exata) e a regra `envio-externo.md` chega. `doctor` só mede; `upgrade` é quem traz.

## 2026-11-06 — movido do MAPA.md

1. ✅ **Owner: ordem de merge das duas branches abertas** — feito em 2026-11-06: 0.52.0 (`62e5239`) antes da 0.53.0 (`51b2160`), conflitos mantendo os dois lados; push do owner (`fd2d7fb`).

## 2026-11-03 — trocar a junção pelo marketplace local (escolha A)

Ordem importa: instalar ANTES de tirar a junção, senão o kit some no meio.
1. **Registrar a lojinha no `~/.claude/settings.json` do owner (com cópia de segurança, OK do owner):** nesta máquina não existe o comando `claude` (só o app Desktop, da Microsoft Store) e o menu do app não documenta adicionar marketplace de pasta local. É o mesmo jeito que o `superpowers` está registrado lá: `extraKnownMarketplaces.mss-local = {"source": {"source": "directory", "path": "C:/Ronaldo/_Mitsui/Python/Spec-Powers"}}` e `enabledPlugins["mss-spec@mss-local"] = true`. O app lê isso ao abrir a sessão seguinte (docs: plugins/loading). O `marketplace.json` já está na forma documentada (`"source": "./"`, commit `dade1db`).
2. **Conversa nova no kit:** `/mss-spec:doctor` → check 1 ✓ e os comandos `/mss-spec:` na lista; conferir em `~/.claude/plugins/installed_plugins.json` a entrada `mss-spec@mss-local` (como a do `superpowers`).
3. **Só então tirar a junção** `~/.claude/skills/mss-spec`: pelo Python (`os.rmdir` remove só o atalho, nunca o clone) — nada de PowerShell, nada de script — com o OK do owner; depois `/plugin` deve mostrar o kit uma vez só.
4. **Atualizar o kit:** memória `project_mss_spec_instalado_por_junction` (vira "instalado por marketplace local; edição não é live; atualizar pelo app depois de mesclar"), `project_plugin_load_cross_marketplace` (a dependência do superpowers pode voltar a ser declarada), check 11 do `doctor` e `LEIA-ME`; registrar como esta máquina atualiza o kit depois de uma mudança (conferir o comando no primeiro uso, não inventar).
5. **Prova:** mudar uma linha no clone, atualizar pelo app, abrir conversa nova e ver a mudança — e só aí fechar a pendência `project_pendencia_intermitencia_pos_update` como "sem junção, sem o que sumir".

