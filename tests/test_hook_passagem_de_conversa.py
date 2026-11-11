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
"""
import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "passagem_de_conversa.py"

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


def _mod():
    spec = importlib.util.spec_from_file_location("passagem_de_conversa", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    return {"TEMP": str(tmp_path), "TMP": str(tmp_path), "TMPDIR": str(tmp_path)}


def _nova():
    return "s-" + uuid.uuid4().hex[:8]


def _pedido(texto, sessao):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(REPO), "prompt": texto}


def _fim(texto, sessao, **extra):
    return {"hook_event_name": "Stop", "session_id": sessao, "cwd": str(REPO), "last_assistant_message": texto,
            **extra}


# --- quem recebe: os itens chegam como decididos --------------------------------------------------------

def test_le_os_itens_decididos_do_pedido_real():
    itens = _mod().decididos(PEDIDO_REAL)
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
def test_formas_do_titulo(titulo):
    texto = f"/mss-spec:nova-feature x\n{titulo}\n1. A tabela é cópia para busca.\n2. O arquivo é o original.\n\nFalta decidir:\n1. onde mora"
    assert _mod().decididos(texto) == ["A tabela é cópia para busca.", "O arquivo é o original."]


def test_pedido_colado_tambem():
    colado = '<pasted_content id="77">\n' + PEDIDO_REAL + "</pasted_content>"
    assert len(_mod().decididos(colado)) == 6


def test_pedido_sem_lista_decidida_nao_tem_itens():
    mod = _mod()
    assert mod.decididos("já decidi que vou almoçar; agora me explique o hook") == []
    assert mod.decididos("Já decidido — não reabrir: nada\nFalta decidir:\n1. tudo") == []
    assert mod.decididos(None) == []


def test_pedido_com_decididos_entrega_a_regra_so_ao_assistente(amb):
    mod, s = _mod(), _nova()
    tipo, texto = mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    assert tipo == "contexto"
    assert "6" in texto and "DECIDID" in texto
    assert "lista única" in texto and "de uma vez" in texto and "arquivo e linha" in texto
    assert mod.avaliar(_pedido("bom dia, me explique o hook", _nova()), amb) == (None, None)


# --- critério 1: a resposta real do F-058 volta ---------------------------------------------------------

def test_resposta_real_do_f058_volta(amb):
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    tipo, motivo = mod.avaliar(_fim(RESPOSTA_F058, s), amb)
    assert tipo == "devolve", "a resposta que reabriu tópico a tópico saiu (F-058)"
    assert "tópico" in motivo.lower() and "lista única" in motivo
    assert "6" in motivo, "o motivo não diz quantos itens chegaram decididos"


def test_sem_decididos_o_topico_a_topico_passa(amb):
    """O formato tópico a tópico vale para o que ainda NÃO foi decidido — conversa sem passagem não é barrada."""
    assert _mod().avaliar(_fim(RESPOSTA_F058, _nova()), amb) == (None, None)


# --- critério 2: a resposta que deu certo sai -----------------------------------------------------------

def test_resposta_real_que_deu_certo_sai(amb):
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    assert mod.avaliar(_fim(RESPOSTA_QUE_DEU_CERTO, s), amb) == (None, None)


def test_perguntas_de_uma_vez_no_fim_saem(amb):
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    resposta = ("**Lista única das minhas escolhas.**\n\n1. Hook calado. Motivo: `docs/decisoes.md:61`.\n"
                "2. Estado no temp.\n\n## O que só você decide\n\n"
                "1. O aviso das 3 anotações troca de motor agora ou depois da medição?\n"
                "2. A versão sai como 0.56.0?\n")
    assert mod.avaliar(_fim(resposta, s), amb) == (None, None)


# --- critério 3: pergunta que repete item decidido ------------------------------------------------------

def test_pergunta_que_repete_item_decidido_volta(amb):
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    resposta = ("**Minhas escolhas abaixo.**\n\n1. Hook calado.\n\n## O que só você decide\n\n"
                "A busca vai na tabela primeiro e só depois nos arquivos, confirma?\n")
    tipo, motivo = mod.avaliar(_fim(resposta, s), amb)
    assert tipo == "devolve"
    assert "Buscar é na tabela primeiro" in motivo, "o motivo não aponta o item decidido"


def test_perguntas_espalhadas_pelo_meio_voltam(amb):
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    meio = "\n".join(f"{n}. escolha {n}, com o motivo dela." for n in range(1, 16))
    resposta = f"**Escolhas.**\n\nO hook roda em qual momento?\n\n{meio}\n\nE a versão, qual vai ser?\n"
    tipo, motivo = mod.avaliar(_fim(resposta, s), amb)
    assert tipo == "devolve" and "de uma vez" in motivo


def test_devolve_uma_vez_por_tipo_na_conversa(amb):
    """Volta à toa custa segundos; em laço custa a conversa: cada conferência de quem recebe age uma vez."""
    mod, s = _mod(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, s), amb)
    assert mod.avaliar(_fim(RESPOSTA_F058, s), amb)[0] == "devolve"
    assert mod.avaliar(_fim(RESPOSTA_F058, s), amb) == (None, None)


# --- critério 4: "o kit não aceita" ---------------------------------------------------------------------

@pytest.mark.parametrize("frase", [
    "Não dá para gravar a tabela no repositório: o plugin não aceita isso.",
    "O kit não permite abrir a conversa daqui.",
    "O hook `sem_worktree.py` negou a criação do worktree, então parei.",
    "A trava de publicação bloqueou o push.",
    "O comando foi negado pelo hook do kit.",
    "Não posso seguir por esse caminho porque a regra do kit proíbe banco como fonte.",
])
def test_recusa_sem_regra_e_sem_pergunta_volta(amb, frase):
    tipo, motivo = _mod().avaliar(_fim(f"**Parei aqui.**\n\n{frase}\n", _nova()), amb)
    assert tipo == "devolve", f"recusa atribuída ao kit saiu sem regra: {frase}"
    assert "arquivo e linha" in motivo and "pergunt" in motivo.lower()


def test_recusa_com_regra_e_pergunta_sai(amb):
    resposta = ("**Uma regra do kit parece proibir isto.**\n\nO hook negou o push: `hooks/git_publicacao.py:17` diz "
                "que push para `main` é ato do owner.\n\nVocê mantém essa regra ou quer que eu prepare o passo a passo?\n")
    assert _mod().avaliar(_fim(resposta, _nova()), amb) == (None, None)


def test_recusa_so_com_regra_ainda_volta(amb):
    resposta = "O hook negou o push (`hooks/git_publicacao.py:17`). Parei aqui.\n"
    tipo, motivo = _mod().avaliar(_fim(resposta, _nova()), amb)
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
def test_o_que_nao_e_recusa_passa(amb, frase):
    assert _mod().avaliar(_fim(frase + "\n", _nova()), amb) == (None, None), f"disparou à toa: {frase}"


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


def test_texto_pronto_sem_as_tres_partes_volta_com_o_molde(amb):
    tipo, motivo = _mod().avaliar(_fim(TEXTO_PRONTO_RUIM, _nova()), amb)
    assert tipo == "devolve"
    for parte in ("Já decidido — não reabrir:", "Falta decidir:", "Regras desta conversa:"):
        assert parte in motivo, f"o molde não traz `{parte}`"


def test_texto_pronto_com_as_tres_partes_sai(amb):
    assert _mod().avaliar(_fim(TEXTO_PRONTO_BOM, _nova()), amb) == (None, None)


def test_texto_pronto_com_um_topico_por_vez_volta(amb):
    """O texto real de 2026-11-11 pedia "um tópico por vez" — e a conversa que recebeu obedeceu."""
    ruim = TEXTO_PRONTO_BOM.replace("siga depois do meu OK.", "siga depois do meu OK. Um tópico por vez.")
    tipo, motivo = _mod().avaliar(_fim(ruim, _nova()), amb)
    assert tipo == "devolve" and "tópico por vez" in motivo


def test_o_molde_do_proprio_hook_e_um_texto_valido(amb):
    mod = _mod()
    resposta = "Abra uma conversa nova e cole:\n\n```text\n" + mod.MOLDE + "\n```\n"
    assert mod.avaliar(_fim(resposta, _nova()), amb) == (None, None), "o molde que o hook ensina não passa nele"
    assert mod.decididos(mod.MOLDE), "a conversa que recebe não lê os itens do molde"


@pytest.mark.parametrize("resposta", [
    # comando para rodar em outra janela não é passagem de trabalho
    "Abra uma janela nova na pasta do outro projeto e cole lá:\n\n```\nRode no terminal e me mostre a saída:\ngit status -sb\n```\n",
    # fala de conversa nova sem bloco de texto
    "Isso fica para uma conversa nova; quando quiser eu monto o texto pronto.",
    # bloco de código, não de texto
    "Na conversa nova, cole este comando:\n\n```bash\ngit status -sb\ngit log --oneline -3\ngit branch\ngit diff\ngit stash list\n```\n",
])
def test_o_que_nao_e_texto_pronto_de_passagem_passa(amb, resposta):
    assert _mod().avaliar(_fim(resposta, _nova()), amb) == (None, None)


# --- garantias ------------------------------------------------------------------------------------------

def test_stop_hook_active_deixa_sair(amb):
    assert _mod().avaliar(_fim("O kit não permite isso.", _nova(), stop_hook_active=True), amb) == (None, None)


def test_escape_do_owner(amb):
    mod = _mod()
    desligado = {**amb, "MSS_PASSAGEM_OFF": "1"}
    assert mod.avaliar(_fim("O kit não permite isso.", _nova()), desligado) == (None, None)
    assert mod.avaliar(_pedido(PEDIDO_REAL, _nova()), desligado) == (None, None)


@pytest.mark.parametrize("ruim", [None, "texto", 42, [], {}, {"hook_event_name": "Stop"},
                                  {"hook_event_name": "UserPromptSubmit", "prompt": None}])
def test_entrada_malformada_libera(amb, ruim):
    assert _mod().avaliar(ruim, amb) == (None, None)


def test_conversas_sao_independentes(amb):
    mod, a, b = _mod(), _nova(), _nova()
    mod.avaliar(_pedido(PEDIDO_REAL, a), amb)
    assert mod.avaliar(_fim(RESPOSTA_F058, b), amb) == (None, None), "a conversa B herdou os itens da A"
    assert mod.avaliar(_fim(RESPOSTA_F058, a), amb)[0] == "devolve"


def _rodar(evento, tmp_path):
    env = {**__import__("os").environ, "TEMP": str(tmp_path), "TMP": str(tmp_path),
           "MSS_REGISTRO_ARQUIVO": str(tmp_path / "registro.jsonl")}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento), capture_output=True, text=True,
                          encoding="utf-8", env=env)


def test_processo_devolve_pelo_contrato_do_stop(tmp_path):
    """JSON `{"decision": "block"}` no stdout e saída 0 — exit 2 + stderr se perde nesta máquina (decisão de
    2026-10-30)."""
    proc = _rodar(_fim("O kit não permite abrir a conversa daqui.", "s-proc"), tmp_path)
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert saida["decision"] == "block" and "arquivo e linha" in saida["reason"]


def test_processo_entrega_a_regra_como_contexto(tmp_path):
    proc = _rodar(_pedido(PEDIDO_REAL, "s-proc2"), tmp_path)
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert "systemMessage" not in saida, "recado ao owner: ele não tem nada a fazer"
    assert "DECIDID" in saida["hookSpecificOutput"]["additionalContext"]
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_processo_calado_quando_nada_a_dizer(tmp_path):
    proc = _rodar(_fim("Feito: 12 testes verdes.", "s-proc3"), tmp_path)
    assert proc.returncode == 0 and proc.stdout.strip() == ""
    proc = _rodar(_pedido("bom dia", "s-proc3"), tmp_path)
    assert proc.returncode == 0 and proc.stdout.strip() == ""


def test_registro_guarda_que_devolveu_sem_o_texto(tmp_path):
    _rodar(_fim("O kit não permite abrir a conversa daqui.", "s-reg"), tmp_path)
    registro = (tmp_path / "registro.jsonl").read_text(encoding="utf-8")
    assert "passagem_de_conversa" in registro and "devolveu" in registro
    assert "abrir a conversa daqui" not in registro, "o texto da resposta foi pro registro"
