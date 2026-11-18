"""Conversa nova acha sozinha o que o owner já decidiu — hook `passagem_de_conversa.py` (0.61.0).

O owner (2026-11-12): *"Conversa nova tem de achar sozinha o que eu já decidi - sem eu colar texto nem digitar
comando."* Decidido por ele: abre a conversa com uma frase comum, o kit acha o assunto e traz o que já foi
decidido; não é comando novo e não pode travar.

Propriedades (spec `docs/specs/conversa-nova-nao-se-perde.md`, critérios 6 a 8):
- quem entrega: o bloco de texto pronto que está no molde fica guardado sozinho (temp do SO, um arquivo por
  projeto) — inclusive na resposta refeita depois de devolvida (`stop_hook_active`);
- quem abre: no 1º pedido da conversa, sem `Já decidido` colado, a frase é casada com o assunto do texto guardado
  e com o nome/título da spec que tem `## O que o owner decidiu`; casou → os itens chegam como contexto;
- casa pelo termo curto do tema (`docs/decisoes.md:54`): o nome inteiro do assunto na frase, ou 3 palavras do
  título e pelo menos metade — nunca pelo texto dos itens;
- só informa: o que foi achado sozinho não entra na devolução de resposta;
- nada casa, 2º pedido, pedido com `Já decidido`, outro projeto, texto vencido, qualquer defeito → igual a hoje.

Camadas (2026-11-17): tudo em memória — os textos prontos guardados de cada projeto, as specs (como texto, lidas
pela `specs_de`) e o estado de cada conversa ficam num objeto do teste e entram na `regra` como dado. O disco de
verdade e o processo deste hook ficam no `test_hook_passagem_de_conversa.py` (um teste de cada por hook).
"""
import importlib.util
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "passagem_de_conversa.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
PROJ = BASE / "projeto"
AGORA = 1_800_000_000.0

ENTREGA = """**O próximo passo é numa conversa nova.** Abra pelo + e cole o texto pronto abaixo.

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

SPEC = """# Memória em tabela — tudo o que é memória do projeto numa tabela local

## Estado atual
Entregue.

## O que o owner decidiu
1. A tabela é cópia para busca; o arquivo continua sendo a fonte.
2. Sem comando pra lembrar: a tabela se atualiza
   sozinha quando a conversa abre.

## Histórico
- 2026-11-10 — criado.
"""


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("passagem_de_conversa", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Projetos:
    """O que o hook guarda e lê no disco, em memória: por projeto, os textos prontos guardados e as specs (texto);
    por conversa, o estado. `avaliar` chama a regra com isso como dado e aplica o que ela devolve — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.passagens, self.specs, self.estados, self.anotacoes = mod, {}, {}, {}, []

    def spec(self, nome="memoria-em-tabela", texto=SPEC, raiz=PROJ):
        self.specs.setdefault(str(raiz), {})[f"{nome}.md"] = texto

    def avaliar(self, evento, ambiente=None, agora=AGORA):
        ambiente = ambiente or {}
        raiz = ambiente.get("CLAUDE_PROJECT_DIR") or evento.get("cwd")
        sessao = evento.get("session_id")
        tipo, texto, mudancas = self.mod.regra(
            evento, ambiente, self.estados.get(sessao, {}), lambda: self.passagens.get(raiz),
            lambda: self.mod.specs_de(self.specs.get(raiz, {})), agora)
        if "estado" in mudancas:
            self.estados[sessao] = mudancas["estado"]
        if "passagens" in mudancas:
            self.passagens[raiz] = mudancas["passagens"]
        self.anotacoes += mudancas["anotacoes"]
        return tipo, texto


@pytest.fixture()
def pj(mod):
    return Projetos(mod)


def _pedido(texto, sessao, raiz=PROJ):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(raiz), "prompt": texto}


def _fim(texto, sessao, raiz=PROJ, **extra):
    return {"hook_event_name": "Stop", "session_id": sessao, "cwd": str(raiz), "last_assistant_message": texto,
            **extra}


# --- o texto pronto fica guardado e a conversa nova o acha -----------------------------------------------

def test_conversa_nova_acha_o_texto_que_outra_entregou(pj):
    assert pj.avaliar(_fim(ENTREGA, "a")) == (None, None)
    tipo, texto = pj.avaliar(_pedido("vamos continuar a memória em tabela", "b"))
    assert tipo == "contexto"
    assert "Gravar continua sendo no arquivo" in texto and "Buscar é na tabela primeiro" in texto
    assert "DECIDIDO" in texto and "lista única" in texto
    assert "Se o aviso das 3 anotações" not in texto, "o que falta decidir não chega como decidido"


def test_resposta_refeita_depois_de_devolvida_tambem_fica_guardada(pj):
    """A resposta que sai certa na 2ª tentativa chega com `stop_hook_active` — é justamente a que vale."""
    assert pj.avaliar(_fim(ENTREGA, "a", stop_hook_active=True)) == (None, None)
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "b"))[0] == "contexto"


def test_texto_fora_do_molde_nao_fica_guardado(pj):
    ruim = ENTREGA.replace("Já decidido — não reabrir:", "O que falta:")
    assert pj.avaliar(_fim(ruim, "a"))[0] == "devolve"
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "b")) == (None, None)


def test_o_molde_do_proprio_hook_nao_vira_assunto_guardado(pj, mod):
    pj.avaliar(_fim("Na conversa nova, cole o texto pronto:\n\n```text\n" + mod.MOLDE + "\n```\n", "a"))
    assert pj.passagens == {}


def test_trecho_privado_nao_fica_guardado(pj):
    pj.avaliar(_fim(ENTREGA.replace("2. Buscar é na tabela primeiro.", "2. <private>senha do banco</private>"), "a"))
    assert pj.passagens == {}


def test_outro_projeto_nao_acha(pj):
    pj.avaliar(_fim(ENTREGA, "a"))
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "b", BASE / "outro")) == (None, None)


def test_texto_guardado_vence_em_sete_dias(pj):
    pj.avaliar(_fim(ENTREGA, "a"))
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "b"), agora=AGORA + 8 * 86400) == (None, None)
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "c"), agora=AGORA + 6 * 86400)[0] == "contexto"


def test_registro_guarda_que_guardou_e_que_achou_sem_o_texto(pj):
    pj.avaliar(_fim(ENTREGA, "a"))
    pj.avaliar(_pedido("vamos continuar a memória em tabela parte 2", "b"))
    assert [d for d, _ in pj.anotacoes] == ["guardou", "achou"]
    assert not any("Gravar continua" in det or "vamos continuar" in det for _, det in pj.anotacoes)


# --- a spec que guarda o que o owner decidiu ---------------------------------------------------------------

def test_conversa_nova_acha_a_secao_da_spec(pj):
    pj.spec()
    tipo, texto = pj.avaliar(_pedido("bom dia, vamos continuar a memória em tabela", "a"))
    assert tipo == "contexto"
    assert "A tabela é cópia para busca" in texto
    assert "a tabela se atualiza sozinha quando a conversa abre" in texto, "item de duas linhas chegou cortado"
    assert "docs/specs/memoria-em-tabela.md:6" in texto
    assert "criado" not in texto, "a lista passou do fim da seção"


def test_spec_sem_a_secao_nao_e_assunto(pj):
    pj.spec(texto=SPEC.replace("## O que o owner decidiu", "## Notas"))
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "a")) == (None, None)


def test_texto_guardado_vem_antes_da_spec_e_aponta_a_spec(pj):
    pj.spec()
    pj.avaliar(_fim(ENTREGA, "a"))
    _, texto = pj.avaliar(_pedido("vamos continuar a memória em tabela parte 2", "b"))
    assert "Gravar continua sendo no arquivo" in texto
    assert "A tabela é cópia para busca" not in texto
    assert "docs/specs/memoria-em-tabela.md:6" in texto


def test_dois_assuntos_empatados_chegam_so_os_nomes(pj):
    pj.spec("tabela-de-precos", SPEC.replace("Memória em tabela", "Tabela de preços"))
    pj.spec("tabela-de-prazos", SPEC.replace("Memória em tabela", "Tabela de prazos"))
    tipo, texto = pj.avaliar(_pedido("vamos mexer na tabela de preços e na tabela de prazos", "a"))
    assert tipo == "contexto"
    assert "tabela-de-precos.md" in texto and "tabela-de-prazos.md" in texto
    assert "A tabela é cópia para busca" not in texto, "no empate não se entrega item de nenhum"
    assert "qual" in texto.lower()


def test_entrega_respeita_o_teto(pj, mod):
    itens = "\n".join(f"{n}. Decisão {n}: " + "palavra " * 30 for n in range(1, 31))
    pj.spec(texto=SPEC.split("## O que o owner decidiu")[0] + "## O que o owner decidiu\n" + itens + "\n")
    _, texto = pj.avaliar(_pedido("vamos continuar a memória em tabela", "a"))
    assert "1. Decisão 1:" in texto and "30. Decisão 30:" not in texto
    assert len(texto.encode("utf-8")) <= mod.ACHADO_TETO + 1200
    assert "não couberam" in texto and "docs/specs/memoria-em-tabela.md:6" in texto


def test_item_comprido_chega_inteiro(mod):
    """Cortar a frase no meio pode inverter o sentido ("nunca responde … sem a regra"): ou vai inteiro, ou não vai."""
    comprido = "Nunca responde que o plugin recusa " + "alguma coisa " * 40 + "sem a regra à vista."
    pj = Projetos(mod)
    pj.spec(texto=SPEC.replace("A tabela é cópia para busca; o arquivo continua sendo a fonte.", comprido))
    _, texto = pj.avaliar(_pedido("vamos continuar a memória em tabela", "a"))
    assert comprido in texto

    pj = Projetos(mod)
    pj.avaliar(_fim(ENTREGA.replace("Buscar é na tabela primeiro.", comprido), "a"))
    _, texto = pj.avaliar(_pedido("vamos continuar a memória em tabela parte 2", "b"))
    assert comprido in texto


# --- quando fica calado: igual a hoje ---------------------------------------------------------------------

@pytest.mark.parametrize("frase", [
    "bom dia",
    "abri conversa nova pra ver o bug do login",
    "a tabela de preços está errada",
    "como funciona o deploy?",
])
def test_frase_que_nao_casa_fica_calada(pj, frase):
    pj.spec()
    pj.spec("conversa-nova-nao-se-perde",
            SPEC.replace("Memória em tabela — tudo o que é memória do projeto numa tabela local",
                         "Conversa nova não se perde — o que está decidido chega como decidido"))
    assert pj.avaliar(_pedido(frase, "a")) == (None, None)


def test_so_procura_no_primeiro_pedido_da_conversa(pj):
    pj.spec()
    assert pj.avaliar(_pedido("bom dia", "a")) == (None, None)
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "a")) == (None, None)


def test_pedido_com_ja_decidido_colado_segue_como_hoje(pj):
    pj.spec()
    pedido = "Vamos continuar a memória em tabela.\nJá decidido — não reabrir:\n1. O item colado vale.\n"
    tipo, texto = pj.avaliar(_pedido(pedido, "a"))
    assert tipo == "contexto" and "1 item(ns)" in texto and "A tabela é cópia" not in texto
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "a")) == (None, None)


def test_sem_conversa_identificada_nao_procura(pj):
    pj.spec()
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", None)) == (None, None)


def test_escape_do_owner(pj):
    pj.spec()
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "a"), {"MSS_PASSAGEM_OFF": "1"}) == (None, None)


def test_defeito_ao_ler_fica_calado(mod):
    """Leitura que quebra (spec ou texto guardado) não segura o pedido nem a resposta."""
    def quebrado():
        raise OSError("disco")

    evento = _pedido("vamos continuar a memória em tabela", "a")
    assert mod.regra(evento, {}, {}, quebrado, quebrado, AGORA)[:2] == (None, None)
    assert mod.regra(_fim(ENTREGA, "b"), {}, {}, quebrado, quebrado, AGORA)[:2] == (None, None)


# --- só informa: o que foi achado sozinho não devolve resposta --------------------------------------------

def test_achado_sozinho_nao_entra_na_devolucao(pj):
    pj.spec()
    assert pj.avaliar(_pedido("vamos continuar a memória em tabela", "a"))[0] == "contexto"
    resposta = "## Tópico 1 — a tabela\n\nA tabela é cópia para busca, ou o arquivo deixa de ser a fonte?\n"
    assert pj.avaliar(_fim(resposta, "a")) == (None, None)


# --- a régua: termo curto do tema ---------------------------------------------------------------------------

def _specs_do_repo():
    out = []
    for arquivo in sorted((REPO / "docs" / "specs").glob("*.md")):
        titulo = arquivo.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ").strip()
        out.append({"origem": "spec", "curto": arquivo.stem.replace("-", " "), "longo": titulo,
                    "fonte": arquivo.name})
    return out


def test_cada_nome_de_spec_do_repo_acha_a_sua_e_so_ela(mod):
    specs = _specs_do_repo()
    assert len(specs) >= 21
    for spec in specs:
        vencedor, empatados = mod.escolher("vamos continuar " + spec["curto"], specs)
        assert vencedor is not None and vencedor["fonte"] == spec["fonte"], (spec["fonte"], empatados)


def test_a_frase_real_do_owner_acha_a_spec_deste_assunto(mod):
    vencedor, _ = mod.escolher("vamos continuar a conversa nova que acha sozinha o que eu já decidi",
                               _specs_do_repo())
    assert vencedor is not None and vencedor["fonte"] == "conversa-nova-nao-se-perde.md"


def test_nome_de_uma_palavra_curta_nao_casa_sozinho(mod):
    """`bug` solto numa frase não é assunto; `upgrade` é."""
    candidatos = [{"origem": "passagem", "curto": "Bug", "longo": "Bug", "fonte": "a"},
                  {"origem": "spec", "curto": "upgrade", "longo": "Upgrade — trazer o projeto", "fonte": "b"}]
    assert mod.escolher("tem um bug no login", candidatos) == (None, [])
    assert mod.escolher("vamos continuar o upgrade", candidatos)[0]["fonte"] == "b"
