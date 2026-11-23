"""Conversa nova não se perde — hook `passagem_de_conversa.py` (0.59.0, item CRÍTICO do `to-dolist.md`).

Nasceu de 2026-11-11 (casos F-058 e F-053, `docs/EVALS.md`): duas conversas abertas com o texto pronto se
perderam (*"dizendo que o plugin não aceita isso ou aquilo"*) e a terceira, com 6 itens decididos no pedido,
respondeu "Os tópicos, na ordem em que quero fechar com você" e "Tópico 1 — …". O próprio texto pronto pedia
"um tópico por vez" e não dizia para não reabrir. Os textos abaixo são os REAIS dessa conversa (`56ec3cd9`),
encurtados.

Propriedades (spec `docs/specs/conversa-nova-nao-se-perde.md`, critérios 1 a 5):
- quem recebe: pedido com `Já decidido` / `O que eu já decidi` + itens → guarda os itens da conversa e entrega a
  regra (só ao assistente); daí em diante a resposta volta uma vez se anunciar "Tópico N", se uma pergunta repetir
  item decidido, ou se espalhar perguntas pelo meio;
- quem entrega: texto pronto para outra conversa sem `Já decidido`, `Falta decidir` e `Regras desta conversa`
  (ou com "um tópico por vez") → volta com o molde;
- "o kit não aceita / negou / bloqueou" sem `arquivo:linha` ou sem pergunta → volta; "Nada no kit proíbe" passa;
- contrato do `Stop`: JSON `{"decision": "block"}` e saída 0; `stop_hook_active` → deixa sair; falha ABERTA;
  escape só do owner: `MSS_PASSAGEM_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o que o hook guardaria no disco (o estado de cada
conversa, os textos prontos do projeto, as specs) fica num objeto do teste e entra como dado. O disco de verdade
fica num teste só (a casca `avaliar` lê e grava), numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "passagem_de_conversa.py"
AGORA = 1_800_000_000.0

PEDIDO_REAL = """/mss-spec:nova-feature Memória em tabela — parte 2: a busca usa a tabela e a tabela se atualiza sozinha.
Leia antes de qualquer desenho, nesta ordem: docs/specs/memoria-em-tabela.md.
O que eu já decidi (resumo; o registro completo está na spec):
1. Gravar continua sendo no arquivo, e a tabela se atualiza sozinha logo depois. Sem comando pra eu lembrar.
2. Buscar é na tabela primeiro e, se precisar, nos arquivos.
3. A tabela se atualiza sozinha quando a conversa abre no projeto, e é montada na hora se não existir.
4. O modo "tabela" do /mss-spec:memory some da minha vista: fica interno e no procedimento de troca de máquina.
5. A busca usa o contexto da conversa, devolve 30 linhas curtas com anotações e documentos separados, e o
   assistente escolhe quais abrir.
6. As portas tarefa, bug e duvida e o /mss-spec:memory buscar passam a usar a tabela.
Como provar: teste para cada item acima, e a régua.
Como trabalhar comigo: português simples, resultado na primeira linha, um tópico por vez, pergunta só no texto.
"""

RESPOSTA_F058 = """**Nada no kit proíbe o que você decidiu.** Li os quatro materiais na ordem pedida e conferi as regras.

A regra que chega mais perto é `docs/decisoes.md:61`.

## Os tópicos, na ordem em que quero fechar com você

1. **Quando a tabela se atualiza** — ao abrir a conversa, depois de gravar e antes de buscar.
2. **Como a busca pega o contexto da conversa** — os seus pedidos anteriores.
5. **As portas `tarefa`, `bug`, `duvida` e o `/mss-spec:memory buscar`** — passam a usar a tabela.
6. **O modo `tabela` some da sua vista.**

## Tópico 1 — quando a tabela se atualiza

**Hoje:** só quando alguém roda `/mss-spec:memory tabela`.

**A proposta:** três momentos, todos sem você fazer nada.

O tópico 1 fecha assim, ou falta algum momento?
"""

RESPOSTA_QUE_DEU_CERTO = """**Segue a lista única do que é escolha minha; os seus itens de 1 a 6 não voltam à mesa.** Nenhum arquivo foi alterado ainda.

## Minhas escolhas de desenho

1. Dois hooks Python do kit, calados: um ao abrir a conversa, outro depois de gravar. Motivo: `docs/decisoes.md:61`.
2. "Depois de gravar" vale para arquivo em `memory/`, `docs/`, `to-dolist.md`.
12. O `/mss-spec:memory buscar <termo>` mostra as 30 linhas e não abre arquivo, como hoje.
13. O modo `tabela` sai da descrição e da ajuda do `/mss-spec:memory`.

## O que só você decide

Nada agora. A única decisão sua vem depois, com os números do item 14.

Sobre a captura: está anotado que "decidir por tópicos, um de cada vez" vale só para o que ainda não foi decidido.

Com o seu OK nesta lista, abro a branch e sigo para o plano e o código.
"""


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("passagem_de_conversa", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Guardado:
    """O que o hook guarda no disco, em memória: o estado de cada conversa, os textos prontos e as specs do projeto.
    `avaliar` chama a regra com isso como dado e aplica o que ela devolve — o papel da casca, sem disco."""

    def __init__(self, mod):
        self.mod, self.estados, self.passagens, self.specs, self.anotacoes = mod, {}, None, [], []

    def avaliar(self, evento, ambiente=None):
        sessao = evento.get("session_id") if isinstance(evento, dict) else None
        tipo, texto, mudancas = self.mod.regra(evento, ambiente or {}, self.estados.get(sessao, {}),
                                                 lambda: self.passagens, lambda: list(self.specs), AGORA)
        if "estado" in mudancas:
            self.estados[sessao] = mudancas["estado"]
        if "passagens" in mudancas:
            self.passagens = mudancas["passagens"]
        self.anotacoes += mudancas["anotacoes"]
        return tipo, texto


@pytest.fixture()
def hook(mod):
    return Guardado(mod)


def _pedido(texto, sessao):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(REPO), "prompt": texto}


def _fim(texto, sessao, **extra):
    return {"hook_event_name": "Stop", "session_id": sessao, "cwd": str(REPO), "last_assistant_message": texto,
            **extra}


# --- quem recebe: os itens chegam como decididos --------------------------------------------------------

def test_le_os_itens_decididos_do_pedido_real(mod):
    itens = mod.decididos(PEDIDO_REAL)
    assert len(itens) == 6, itens
    assert itens[0].startswith("Gravar continua sendo no arquivo")
    assert itens[4].endswith("assistente escolhe quais abrir."), "a linha de continuação do item 5 se perdeu"
    assert not any("Como provar" in i for i in itens), "o que vem depois da lista entrou como item"


@pytest.mark.parametrize("titulo", [
    "Já decidido — não reabrir:",
    "## Já decidido (não reabrir)",
    "**Já decidido — não reabrir:**",
    "O que eu já decidi:",
    "Decisões já tomadas:",
])
def test_formas_do_titulo(mod, titulo):
    texto = f"/mss-spec:nova-feature x\n{titulo}\n1. A tabela é cópia para busca.\n2. O arquivo é o original.\n\nFalta decidir:\n1. onde mora"
    assert mod.decididos(texto) == ["A tabela é cópia para busca.", "O arquivo é o original."]


def test_pedido_colado_tambem(mod):
    colado = '<pasted_content id="77">\n' + PEDIDO_REAL + "</pasted_content>"
    assert len(mod.decididos(colado)) == 6


def test_pedido_sem_lista_decidida_nao_tem_itens(mod):
    assert mod.decididos("já decidi que vou almoçar; agora me explique o hook") == []
    assert mod.decididos("Já decidido — não reabrir: nada\nFalta decidir:\n1. tudo") == []
    assert mod.decididos(None) == []


def test_pedido_com_decididos_entrega_a_regra_so_ao_assistente(hook):
    tipo, texto = hook.avaliar(_pedido(PEDIDO_REAL, "s-a"))
    assert tipo == "contexto"
    assert "6" in texto and "DECIDID" in texto
    assert "lista única" in texto and "de uma vez" in texto and "arquivo e linha" in texto
    assert hook.avaliar(_pedido("bom dia, me explique o hook", "s-b")) == (None, None)


# --- critério 1: a resposta real do F-058 volta ---------------------------------------------------------

def test_resposta_real_do_f058_volta(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    tipo, motivo = hook.avaliar(_fim(RESPOSTA_F058, "s"))
    assert tipo == "devolve", "a resposta que reabriu tópico a tópico saiu (F-058)"
    assert "tópico" in motivo.lower() and "lista única" in motivo
    assert "6" in motivo, "o motivo não diz quantos itens chegaram decididos"


def test_sem_decididos_o_topico_a_topico_passa(hook):
    """O formato tópico a tópico vale para o que ainda NÃO foi decidido — conversa sem passagem não é barrada."""
    assert hook.avaliar(_fim(RESPOSTA_F058, "s")) == (None, None)


# --- critério 2: a resposta que deu certo sai -----------------------------------------------------------

def test_resposta_real_que_deu_certo_sai(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    assert hook.avaliar(_fim(RESPOSTA_QUE_DEU_CERTO, "s")) == (None, None)


def test_perguntas_de_uma_vez_no_fim_saem(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    resposta = ("**Lista única das minhas escolhas.**\n\n1. Hook calado. Motivo: `docs/decisoes.md:61`.\n"
                "2. Estado no temp.\n\n## O que só você decide\n\n"
                "1. O aviso das 3 anotações troca de motor agora ou depois da medição?\n"
                "2. A versão sai como 0.56.0?\n")
    assert hook.avaliar(_fim(resposta, "s")) == (None, None)


# --- critério 3: pergunta que repete item decidido ------------------------------------------------------

def test_pergunta_que_repete_item_decidido_volta(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    resposta = ("**Minhas escolhas abaixo.**\n\n1. Hook calado.\n\n## O que só você decide\n\n"
                "A busca vai na tabela primeiro e só depois nos arquivos, confirma?\n")
    tipo, motivo = hook.avaliar(_fim(resposta, "s"))
    assert tipo == "devolve"
    assert "Buscar é na tabela primeiro" in motivo, "o motivo não aponta o item decidido"


def test_perguntas_espalhadas_pelo_meio_voltam(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    meio = "\n".join(f"{n}. escolha {n}, com o motivo dela." for n in range(1, 16))
    resposta = f"**Escolhas.**\n\nO hook roda em qual momento?\n\n{meio}\n\nE a versão, qual vai ser?\n"
    tipo, motivo = hook.avaliar(_fim(resposta, "s"))
    assert tipo == "devolve" and "de uma vez" in motivo


def test_devolve_uma_vez_por_tipo_na_conversa(hook):
    """Volta à toa custa segundos; em laço custa a conversa: cada conferência de quem recebe age uma vez."""
    hook.avaliar(_pedido(PEDIDO_REAL, "s"))
    assert hook.avaliar(_fim(RESPOSTA_F058, "s"))[0] == "devolve"
    assert hook.avaliar(_fim(RESPOSTA_F058, "s")) == (None, None)


# --- critério 4: "o kit não aceita" ---------------------------------------------------------------------

@pytest.mark.parametrize("frase", [
    "Não dá para gravar a tabela no repositório: o plugin não aceita isso.",
    "O kit não permite abrir a conversa daqui.",
    "O hook `sem_worktree.py` negou a criação do worktree, então parei.",
    "A trava de publicação bloqueou o push.",
    "O comando foi negado pelo hook do kit.",
    "Não posso seguir por esse caminho porque a regra do kit proíbe banco como fonte.",
])
def test_recusa_sem_regra_e_sem_pergunta_volta(hook, frase):
    tipo, motivo = hook.avaliar(_fim(f"**Parei aqui.**\n\n{frase}\n", "s"))
    assert tipo == "devolve", f"recusa atribuída ao kit saiu sem regra: {frase}"
    assert "arquivo e linha" in motivo and "pergunt" in motivo.lower()


def test_recusa_com_regra_e_pergunta_sai(hook):
    resposta = ("**Uma regra do kit parece proibir isto.**\n\nO hook negou o push: `hooks/git_publicacao.py:17` diz "
                "que push para `main` é ato do owner.\n\nVocê mantém essa regra ou quer que eu prepare o passo a passo?\n")
    assert hook.avaliar(_fim(resposta, "s")) == (None, None)


def test_recusa_so_com_regra_ainda_volta(hook):
    resposta = "O hook negou o push (`hooks/git_publicacao.py:17`). Parei aqui.\n"
    tipo, motivo = hook.avaliar(_fim(resposta, "s"))
    assert tipo == "devolve" and "pergunt" in motivo.lower()


@pytest.mark.parametrize("frase", [
    "**Nada no kit proíbe o que você decidiu.** Li os quatro materiais.",            # real, conversa 56ec3cd9
    "Abri a memória que o hook apontou e ela não veta nem muda nada do que propus.",   # real, conversa be490360
    'Você pediu que a conversa nova nunca responda "o plugin não aceita".',            # citação da fala do owner
    "O comando é negado uma vez, com as regras pra eu abrir; repetir passa.",          # descrição de desenho
    "A cerca nega push para `main` e pede aprovação para o resto.",                    # descrição
    "O hook de fecho nunca bloqueou nada nas conversas medidas.",                      # real, conversa 71d6a992
    "O hook não negou o comando; ele passou na segunda vez.",
    "```\nO hook negou o push.\n```",                                                  # dentro de bloco
    "> O kit não permite isso.",                                                       # citação
])
def test_o_que_nao_e_recusa_passa(hook, frase):
    assert hook.avaliar(_fim(frase + "\n", "s")) == (None, None), f"disparou à toa: {frase}"


# --- critério 5: quem entrega o texto pronto ------------------------------------------------------------

TEXTO_PRONTO_RUIM = """**O próximo passo é numa conversa nova.** Abra pelo + e cole o texto pronto abaixo.

```text
/mss-spec:nova-feature Memória em tabela — parte 2
Leia antes de qualquer desenho: docs/specs/memoria-em-tabela.md.
O que falta: a busca usar a tabela.
Como provar: teste para cada item.
Como trabalhar comigo: português simples, um tópico por vez.
```
"""

TEXTO_PRONTO_BOM = """**O próximo passo é numa conversa nova.** Abra pelo + e cole o texto pronto abaixo.

```text
/mss-spec:nova-feature Memória em tabela — parte 2
Leia antes de qualquer desenho: docs/specs/memoria-em-tabela.md.
Já decidido — não reabrir:
1. Gravar continua sendo no arquivo (docs/specs/memoria-em-tabela.md:79).
2. Buscar é na tabela primeiro.
Falta decidir:
1. Se o aviso das 3 anotações troca de motor.
Regras desta conversa: o que está decidido não se reabre — mostre em lista única só as SUAS escolhas e pergunte
de uma vez, no fim, o que só eu decido; siga depois do meu OK. Se alguma regra do kit parecer proibir, mostre a
regra com arquivo e linha e me pergunte.
```
"""


def test_texto_pronto_sem_as_tres_partes_volta_com_o_molde(hook):
    tipo, motivo = hook.avaliar(_fim(TEXTO_PRONTO_RUIM, "s"))
    assert tipo == "devolve"
    for parte in ("Já decidido — não reabrir:", "Falta decidir:", "Regras desta conversa:"):
        assert parte in motivo, f"o molde não traz `{parte}`"


def test_texto_pronto_com_as_tres_partes_sai(hook):
    assert hook.avaliar(_fim(TEXTO_PRONTO_BOM, "s")) == (None, None)


def test_texto_pronto_com_um_topico_por_vez_volta(hook):
    """O texto real de 2026-11-11 pedia "um tópico por vez" — e a conversa que recebeu obedeceu."""
    ruim = TEXTO_PRONTO_BOM.replace("siga depois do meu OK.", "siga depois do meu OK. Um tópico por vez.")
    tipo, motivo = hook.avaliar(_fim(ruim, "s"))
    assert tipo == "devolve" and "tópico por vez" in motivo


def test_o_molde_do_proprio_hook_e_um_texto_valido(hook, mod):
    resposta = "Abra uma conversa nova e cole:\n\n```text\n" + mod.MOLDE + "\n```\n"
    assert hook.avaliar(_fim(resposta, "s")) == (None, None), "o molde que o hook ensina não passa nele"
    assert mod.decididos(mod.MOLDE), "a conversa que recebe não lê os itens do molde"


@pytest.mark.parametrize("resposta", [
    # comando para rodar em outra janela não é passagem de trabalho
    "Abra uma janela nova na pasta do outro projeto e cole lá:\n\n```\nRode no terminal e me mostre a saída:\ngit status -sb\n```\n",
    # fala de conversa nova sem bloco de texto
    "Isso fica para uma conversa nova; quando quiser eu monto o texto pronto.",
    # bloco de código, não de texto
    "Na conversa nova, cole este comando:\n\n```bash\ngit status -sb\ngit log --oneline -3\ngit branch\ngit diff\ngit stash list\n```\n",
])
def test_o_que_nao_e_texto_pronto_de_passagem_passa(hook, resposta):
    assert hook.avaliar(_fim(resposta, "s")) == (None, None)


# --- 0.67.0: o texto pronto começa pelo comando do kit (caso F-077) --------------------------------------
# A conversa "Análise de consultas de apólice e boleto" (Whats, 2026-11-23 13:30) entregou este bloco de 4 linhas —
# abaixo do mínimo de 5, então nada o conferiu. A conversa aberta com ele não entrou por porta nenhuma do kit.

TEXTO_CURTO_REAL = """Cole isto na janela nova, aberta na raiz do repositório:

```text
Continuação da feature financeiro-emissao-crm (consulta de apólice e boleto) — não é feature nova.
Leia docs/superpowers/plans/2026-11-23-prompt-tela-apolice-boleto.md e siga.
Quero uma entrada exclusiva de Apólice e Boleto no Painel_V2 para fazer o simulado e validar o decisor novo,
parando de usar a planilha, e a chave liga/desliga dele nesse painel. Comece pelo desenho, sem código.
```
"""


def test_texto_curto_real_sem_comando_do_kit_volta(hook):
    tipo, motivo = hook.avaliar(_fim(TEXTO_CURTO_REAL, "s"))
    assert tipo == "devolve", "o texto de continuação sem comando do kit saiu"
    assert "/mss-spec:" in motivo and "1ª linha" in motivo


def test_texto_curto_que_comeca_pelo_comando_sai(hook):
    bom = ("Cole isto na janela nova:\n\n```text\n/mss-spec:tarefa continuação da consulta de apólice e boleto\n"
           "Leia docs/superpowers/plans/2026-11-23-prompt-tela-apolice-boleto.md e siga.\n```\n")
    assert hook.avaliar(_fim(bom, "s")) == (None, None)


def test_texto_curto_real_com_comando_ainda_cobra_as_tres_partes(hook):
    """Com o comando, o bloco real chega a 5 linhas: aí vale o molde inteiro (caso F-058), como antes."""
    com = TEXTO_CURTO_REAL.replace("```text\n", "```text\n/mss-spec:tarefa continuação da consulta de apólice e boleto\n")
    tipo, motivo = hook.avaliar(_fim(com, "s"))
    assert tipo == "devolve" and "Já decidido" in motivo and "1ª linha" not in motivo


def test_texto_grande_sem_comando_do_kit_volta(hook):
    sem = TEXTO_PRONTO_BOM.replace("/mss-spec:nova-feature Memória em tabela — parte 2\n", "Memória em tabela — parte 2\n")
    tipo, motivo = hook.avaliar(_fim(sem, "s"))
    assert tipo == "devolve" and "/mss-spec:" in motivo


# --- garantias ------------------------------------------------------------------------------------------

def test_stop_hook_active_deixa_sair(hook):
    assert hook.avaliar(_fim("O kit não permite isso.", "s", stop_hook_active=True)) == (None, None)


def test_escape_do_owner(hook):
    desligado = {"MSS_PASSAGEM_OFF": "1"}
    assert hook.avaliar(_fim("O kit não permite isso.", "s"), desligado) == (None, None)
    assert hook.avaliar(_pedido(PEDIDO_REAL, "s"), desligado) == (None, None)


@pytest.mark.parametrize("ruim", [None, "texto", 42, [], {}, {"hook_event_name": "Stop"},
                                  {"hook_event_name": "UserPromptSubmit", "prompt": None}])
def test_entrada_malformada_libera(hook, ruim):
    assert hook.avaliar(ruim) == (None, None)


def test_conversas_sao_independentes(hook):
    hook.avaliar(_pedido(PEDIDO_REAL, "a"))
    assert hook.avaliar(_fim(RESPOSTA_F058, "b")) == (None, None), "a conversa B herdou os itens da A"
    assert hook.avaliar(_fim(RESPOSTA_F058, "a"))[0] == "devolve"


def test_registro_guarda_que_devolveu_sem_o_texto(hook):
    hook.avaliar(_fim("O kit não permite abrir a conversa daqui.", "s"))
    assert [d for d, _ in hook.anotacoes] == ["devolveu"]
    assert not any("abrir a conversa daqui" in detalhe for _, detalhe in hook.anotacoes), \
        "o texto da resposta foi pro registro"


def test_saida_pelo_contrato_de_cada_evento(mod):
    """`Stop`: JSON `{"decision": "block"}` (exit 2 + stderr se perde nesta máquina, decisão de 2026-10-30).
    Pedido: `additionalContext`, nunca `systemMessage` — o owner não tem nada a fazer. Nada a dizer: calado."""
    devolve = json.loads(mod.saida("devolve", "motivo com arquivo e linha"))
    assert devolve == {"decision": "block", "reason": "motivo com arquivo e linha"}
    contexto = json.loads(mod.saida("contexto", "itens DECIDIDOS"))
    assert "systemMessage" not in contexto
    assert contexto["hookSpecificOutput"] == {"hookEventName": "UserPromptSubmit",
                                              "additionalContext": "itens DECIDIDOS"}
    assert mod.saida(None, None) is None


# --- o disco de verdade: a casca lê e grava (pasta montada uma vez) -------------------------------------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("passagem")
    temp, proj = base / "temp", base / "projeto"
    temp.mkdir()
    (proj / "docs" / "specs").mkdir(parents=True)
    (proj / "docs" / "specs" / "memoria-em-tabela.md").write_text(
        "# Memória em tabela\n\n## O que o owner decidiu\n\n1. Gravar é no arquivo.\n", encoding="utf-8")
    return temp, proj


def test_casca_le_e_grava_o_estado_os_textos_prontos_e_a_spec(mod, pasta):
    temp, proj = pasta
    amb = {"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp), "CLAUDE_PROJECT_DIR": str(proj)}
    # textos prontos: a conversa A entrega, a B acha (lidos do disco), junto com a spec do projeto
    assert mod.avaliar(_fim(TEXTO_PRONTO_BOM, "disco-a"), amb) == (None, None)
    assert list(proj.rglob("mss_passagens_*.json")) == [], "o texto guardado sujou a pasta do projeto"
    tipo, achado = mod.avaliar(_pedido("vamos continuar a memória em tabela", "disco-b"), amb)
    assert tipo == "contexto" and "Buscar é na tabela primeiro." in achado
    assert "docs/specs/memoria-em-tabela.md:3" in achado, "a spec do disco não foi lida"
    # estado da conversa: os itens gravados num evento e lidos no seguinte
    assert mod.avaliar(_pedido(PEDIDO_REAL, "disco-c"), amb)[0] == "contexto"
    assert mod.avaliar(_fim(RESPOSTA_F058, "disco-c"), amb)[0] == "devolve"
    assert mod.avaliar(_fim(RESPOSTA_F058, "disco-c"), amb) == (None, None), "o que já devolveu não foi gravado"
    # defeito no disco: spec ilegível e texto guardado quebrado não seguram o pedido; a spec boa ainda é achada
    (proj / "docs" / "specs" / "ilegivel.md").write_bytes(b"\xff\xfe\x00## O que o owner decidiu\n1. x\n")
    next(temp.glob("mss_passagens_*.json")).write_text("{quebrado", encoding="utf-8")
    tipo, achado = mod.avaliar(_pedido("vamos continuar a memória em tabela", "disco-d"), amb)
    assert tipo == "contexto" and "Gravar é no arquivo." in achado


def test_processo_devolve_pelo_contrato_do_stop(pasta):
    """O processo python de verdade: lê a entrada, imprime o JSON e sai com 0."""
    temp, _ = pasta
    env = {**__import__("os").environ, "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(_fim("O kit não permite isso.", "s-proc")),
                          capture_output=True, text=True, encoding="utf-8", env=env)
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert saida["decision"] == "block" and "arquivo e linha" in saida["reason"]
