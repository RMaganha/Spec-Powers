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
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "passagem_de_conversa.py"

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


def _mod():
    spec = importlib.util.spec_from_file_location("passagem_de_conversa", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def amb(tmp_path):
    temp = tmp_path / "temp"
    temp.mkdir()
    return {"TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "projeto"
    (raiz / "docs" / "specs").mkdir(parents=True)
    return raiz


def _nova():
    return "s-" + uuid.uuid4().hex[:8]


def _pedido(texto, sessao, raiz):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sessao, "cwd": str(raiz), "prompt": texto}


def _fim(texto, sessao, raiz, **extra):
    return {"hook_event_name": "Stop", "session_id": sessao, "cwd": str(raiz), "last_assistant_message": texto,
            **extra}


def _spec(proj, nome="memoria-em-tabela", texto=SPEC):
    (proj / "docs" / "specs" / f"{nome}.md").write_text(texto, encoding="utf-8")


# --- o texto pronto fica guardado e a conversa nova o acha -----------------------------------------------

def test_conversa_nova_acha_o_texto_que_outra_entregou(amb, proj):
    mod = _mod()
    assert mod.avaliar(_fim(ENTREGA, _nova(), proj), amb) == (None, None)
    tipo, texto = mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb)
    assert tipo == "contexto"
    assert "Gravar continua sendo no arquivo" in texto and "Buscar é na tabela primeiro" in texto
    assert "DECIDIDO" in texto and "lista única" in texto
    assert "Se o aviso das 3 anotações" not in texto, "o que falta decidir não chega como decidido"


def test_o_texto_guardado_nao_suja_a_pasta_do_projeto(amb, proj):
    _mod().avaliar(_fim(ENTREGA, _nova(), proj), amb)
    assert [p.name for p in proj.rglob("*") if p.is_file()] == []
    assert any(n.startswith("mss_passagens_") for n in os.listdir(amb["TEMP"]))


def test_resposta_refeita_depois_de_devolvida_tambem_fica_guardada(amb, proj):
    """A resposta que sai certa na 2ª tentativa chega com `stop_hook_active` — é justamente a que vale."""
    mod = _mod()
    assert mod.avaliar(_fim(ENTREGA, _nova(), proj, stop_hook_active=True), amb) == (None, None)
    tipo, _ = mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb)
    assert tipo == "contexto"


def test_texto_fora_do_molde_nao_fica_guardado(amb, proj):
    mod = _mod()
    ruim = ENTREGA.replace("Já decidido — não reabrir:", "O que falta:")
    assert mod.avaliar(_fim(ruim, _nova(), proj), amb)[0] == "devolve"
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb) == (None, None)


def test_o_molde_do_proprio_hook_nao_vira_assunto_guardado(amb, proj):
    mod = _mod()
    mod.avaliar(_fim("Na conversa nova, cole o texto pronto:\n\n```text\n" + mod.MOLDE + "\n```\n", _nova(), proj), amb)
    assert not any(n.startswith("mss_passagens_") for n in os.listdir(amb["TEMP"]))


def test_trecho_privado_nao_fica_guardado(amb, proj):
    mod = _mod()
    privado = ENTREGA.replace("2. Buscar é na tabela primeiro.", "2. <private>senha do banco</private>")
    mod.avaliar(_fim(privado, _nova(), proj), amb)
    assert not any(n.startswith("mss_passagens_") for n in os.listdir(amb["TEMP"]))


def test_outro_projeto_nao_acha(amb, proj, tmp_path):
    mod = _mod()
    mod.avaliar(_fim(ENTREGA, _nova(), proj), amb)
    outro = tmp_path / "outro"
    outro.mkdir()
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), outro), amb) == (None, None)


def test_texto_guardado_vence_em_sete_dias(amb, proj):
    mod = _mod()
    mod.avaliar(_fim(ENTREGA, _nova(), proj), amb)
    arquivo = next(Path(amb["TEMP"]).glob("mss_passagens_*.json"))
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    dados["passagens"][0]["quando"] = time.time() - 8 * 86400
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb) == (None, None)


# --- a spec que guarda o que o owner decidiu ---------------------------------------------------------------

def test_conversa_nova_acha_a_secao_da_spec(amb, proj):
    _spec(proj)
    tipo, texto = _mod().avaliar(_pedido("bom dia, vamos continuar a memória em tabela", _nova(), proj), amb)
    assert tipo == "contexto"
    assert "A tabela é cópia para busca" in texto
    assert "a tabela se atualiza sozinha quando a conversa abre" in texto, "item de duas linhas chegou cortado"
    assert "docs/specs/memoria-em-tabela.md:6" in texto
    assert "criado" not in texto, "a lista passou do fim da seção"


def test_spec_sem_a_secao_nao_e_assunto(amb, proj):
    _spec(proj, texto=SPEC.replace("## O que o owner decidiu", "## Notas"))
    assert _mod().avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb) == (None, None)


def test_texto_guardado_vem_antes_da_spec_e_aponta_a_spec(amb, proj):
    mod = _mod()
    _spec(proj)
    mod.avaliar(_fim(ENTREGA, _nova(), proj), amb)
    _, texto = mod.avaliar(_pedido("vamos continuar a memória em tabela parte 2", _nova(), proj), amb)
    assert "Gravar continua sendo no arquivo" in texto
    assert "A tabela é cópia para busca" not in texto
    assert "docs/specs/memoria-em-tabela.md:6" in texto


def test_dois_assuntos_empatados_chegam_so_os_nomes(amb, proj):
    _spec(proj, "tabela-de-precos", SPEC.replace("Memória em tabela", "Tabela de preços"))
    _spec(proj, "tabela-de-prazos", SPEC.replace("Memória em tabela", "Tabela de prazos"))
    tipo, texto = _mod().avaliar(
        _pedido("vamos mexer na tabela de preços e na tabela de prazos", _nova(), proj), amb)
    assert tipo == "contexto"
    assert "tabela-de-precos.md" in texto and "tabela-de-prazos.md" in texto
    assert "A tabela é cópia para busca" not in texto, "no empate não se entrega item de nenhum"
    assert "qual" in texto.lower()


def test_entrega_respeita_o_teto(amb, proj):
    itens = "\n".join(f"{n}. Decisão {n}: " + "palavra " * 30 for n in range(1, 31))
    _spec(proj, texto=SPEC.split("## O que o owner decidiu")[0] + "## O que o owner decidiu\n" + itens + "\n")
    mod = _mod()
    _, texto = mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb)
    assert "1. Decisão 1:" in texto and "30. Decisão 30:" not in texto
    assert len(texto.encode("utf-8")) <= mod.ACHADO_TETO + 1200
    assert "não couberam" in texto and "docs/specs/memoria-em-tabela.md:6" in texto


def test_item_comprido_chega_inteiro(amb, proj):
    """Cortar a frase no meio pode inverter o sentido ("nunca responde … sem a regra"): ou vai inteiro, ou não vai."""
    comprido = "Nunca responde que o plugin recusa " + "alguma coisa " * 40 + "sem a regra à vista."
    _spec(proj, texto=SPEC.replace("A tabela é cópia para busca; o arquivo continua sendo a fonte.", comprido))
    _, texto = _mod().avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb)
    assert comprido in texto

    mod = _mod()
    mod.avaliar(_fim(ENTREGA.replace("Buscar é na tabela primeiro.", comprido), _nova(), proj), amb)
    _, texto = mod.avaliar(_pedido("vamos continuar a memória em tabela parte 2", _nova(), proj), amb)
    assert comprido in texto


# --- quando fica calado: igual a hoje ---------------------------------------------------------------------

@pytest.mark.parametrize("frase", [
    "bom dia",
    "abri conversa nova pra ver o bug do login",
    "a tabela de preços está errada",
    "como funciona o deploy?",
])
def test_frase_que_nao_casa_fica_calada(amb, proj, frase):
    _spec(proj)
    _spec(proj, "conversa-nova-nao-se-perde",
          SPEC.replace("Memória em tabela — tudo o que é memória do projeto numa tabela local",
                       "Conversa nova não se perde — o que está decidido chega como decidido"))
    assert _mod().avaliar(_pedido(frase, _nova(), proj), amb) == (None, None)


def test_so_procura_no_primeiro_pedido_da_conversa(amb, proj):
    mod, sessao = _mod(), _nova()
    _spec(proj)
    assert mod.avaliar(_pedido("bom dia", sessao, proj), amb) == (None, None)
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", sessao, proj), amb) == (None, None)


def test_pedido_com_ja_decidido_colado_segue_como_hoje(amb, proj):
    mod, sessao = _mod(), _nova()
    _spec(proj)
    pedido = "Vamos continuar a memória em tabela.\nJá decidido — não reabrir:\n1. O item colado vale.\n"
    tipo, texto = mod.avaliar(_pedido(pedido, sessao, proj), amb)
    assert tipo == "contexto" and "1 item(ns)" in texto and "A tabela é cópia" not in texto
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", sessao, proj), amb) == (None, None)


def test_sem_conversa_identificada_nao_procura(amb, proj):
    _spec(proj)
    evento = _pedido("vamos continuar a memória em tabela", None, proj)
    assert _mod().avaliar(evento, amb) == (None, None)


def test_escape_do_owner(amb, proj):
    _spec(proj)
    evento = _pedido("vamos continuar a memória em tabela", _nova(), proj)
    assert _mod().avaliar(evento, {**amb, "MSS_PASSAGEM_OFF": "1"}) == (None, None)


def test_defeito_no_disco_fica_calado(amb, proj):
    (proj / "docs" / "specs" / "memoria-em-tabela.md").write_bytes(b"\xff\xfe\x00## O que o owner decidiu\n1. x\n")
    Path(amb["TEMP"], "lixo").write_text("x", encoding="utf-8")
    mod = _mod()
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", _nova(), proj), amb) == (None, None)
    sessao = _nova()
    Path(amb["TEMP"], f"mss_passagens_{mod._chave(str(proj))}.json").write_text("{quebrado", encoding="utf-8")
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", sessao, proj), amb) == (None, None)
    assert mod.avaliar(_fim(ENTREGA, _nova(), proj), amb) == (None, None)


# --- só informa: o que foi achado sozinho não devolve resposta --------------------------------------------

def test_achado_sozinho_nao_entra_na_devolucao(amb, proj):
    mod, sessao = _mod(), _nova()
    _spec(proj)
    assert mod.avaliar(_pedido("vamos continuar a memória em tabela", sessao, proj), amb)[0] == "contexto"
    resposta = "## Tópico 1 — a tabela\n\nA tabela é cópia para busca, ou o arquivo deixa de ser a fonte?\n"
    assert mod.avaliar(_fim(resposta, sessao, proj), amb) == (None, None)


# --- a régua: termo curto do tema ---------------------------------------------------------------------------

def _specs_do_repo():
    out = []
    for arquivo in sorted((REPO / "docs" / "specs").glob("*.md")):
        titulo = arquivo.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ").strip()
        out.append({"origem": "spec", "curto": arquivo.stem.replace("-", " "), "longo": titulo,
                    "fonte": arquivo.name})
    return out


def test_cada_nome_de_spec_do_repo_acha_a_sua_e_so_ela():
    mod, specs = _mod(), _specs_do_repo()
    assert len(specs) >= 21
    for spec in specs:
        vencedor, empatados = mod.escolher("vamos continuar " + spec["curto"], specs)
        assert vencedor is not None and vencedor["fonte"] == spec["fonte"], (spec["fonte"], empatados)


def test_a_frase_real_do_owner_acha_a_spec_deste_assunto():
    mod = _mod()
    vencedor, _ = mod.escolher("vamos continuar a conversa nova que acha sozinha o que eu já decidi",
                               _specs_do_repo())
    assert vencedor is not None and vencedor["fonte"] == "conversa-nova-nao-se-perde.md"


def test_nome_de_uma_palavra_curta_nao_casa_sozinho():
    """`bug` solto numa frase não é assunto; `upgrade` é."""
    mod = _mod()
    candidatos = [{"origem": "passagem", "curto": "Bug", "longo": "Bug", "fonte": "a"},
                  {"origem": "spec", "curto": "upgrade", "longo": "Upgrade — trazer o projeto", "fonte": "b"}]
    assert mod.escolher("tem um bug no login", candidatos) == (None, [])
    assert mod.escolher("vamos continuar o upgrade", candidatos)[0]["fonte"] == "b"


# --- o processo de verdade ----------------------------------------------------------------------------------

def _rodar(evento, tmp_path, proj):
    env = {**os.environ, "TEMP": str(tmp_path), "TMP": str(tmp_path), "CLAUDE_PROJECT_DIR": str(proj),
           "MSS_REGISTRO_ARQUIVO": str(tmp_path / "registro.jsonl")}
    env.pop("MSS_PASSAGEM_OFF", None)
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(evento), capture_output=True, text=True,
                          encoding="utf-8", env=env)


def test_processo_entrega_o_achado_como_contexto_e_nunca_segura_o_pedido(tmp_path, proj):
    _spec(proj)
    proc = _rodar(_pedido("vamos continuar a memória em tabela", "s-acha", proj), tmp_path, proj)
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert "decision" not in saida and "systemMessage" not in saida
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "A tabela" in saida["hookSpecificOutput"]["additionalContext"]


def test_registro_guarda_que_achou_e_que_guardou_sem_o_texto(tmp_path, proj):
    _spec(proj)
    _rodar(_fim(ENTREGA, "s-entrega", proj), tmp_path, proj)
    _rodar(_pedido("vamos continuar a memória em tabela parte 2", "s-abre", proj), tmp_path, proj)
    registro = (tmp_path / "registro.jsonl").read_text(encoding="utf-8")
    assert "guardou" in registro and "achou" in registro
    assert "Gravar continua" not in registro and "vamos continuar" not in registro
