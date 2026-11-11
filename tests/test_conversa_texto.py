"""Outra conversa em texto (0.58.0) — `templates/conversa_texto.py`, apoio do ajudante pesquisador.

A conversa gravada pelo app é um `.jsonl` com resultado de ferramenta, raciocínio e fala de ajudante no meio;
o ajudante (que só lê) não consegue tirar dali o que foi dito. O script lista as conversas do projeto e grava
uma delas em texto, só com as falas do owner e do assistente (critério 4 de `docs/specs/ajudante-pesquisador.md`).
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "conversa_texto.py"


def _mod():
    nome = "conversa_texto"
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _owner(texto, quando="2026-11-10T13:00:00.000Z", **extra):
    return {"type": "user", "timestamp": quando, "message": {"role": "user", "content": texto}, **extra}


def _assistente(*blocos, quando="2026-11-10T13:01:00.000Z", **extra):
    return {"type": "assistant", "timestamp": quando, "message": {"role": "assistant", "content": list(blocos)}, **extra}


def _texto(t):
    return {"type": "text", "text": t}


def _ferramenta(nome, **entrada):
    return {"type": "tool_use", "id": "t1", "name": nome, "input": entrada}


def _resultado(t):
    return {"type": "user", "timestamp": "2026-11-10T13:01:30.000Z",
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": t}]}}


def _conversa(pasta, nome, registros, cru=()):
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"{nome}.jsonl"
    linhas = [json.dumps(r, ensure_ascii=False) for r in registros] + list(cru)
    arq.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return arq


PEDIDO = "Preciso entender por que o upgrade do Transportes parou na segunda rodada"


@pytest.fixture
def conversa(tmp_path):
    return _conversa(tmp_path / "proj", "aaaa1111-2222-3333-4444-555566667777", [
        _owner(PEDIDO),
        _assistente({"type": "thinking", "thinking": "RACIOCINIO-INTERNO"}, _texto("Vou abrir o comando de upgrade.")),
        _assistente(_ferramenta("Read", file_path="commands/upgrade.md")),
        _resultado("CONTEUDO-DO-ARQUIVO-LIDO " * 50),
        _assistente(_texto("FALA-DE-AJUDANTE"), isSidechain=True),
        _owner("AVISO-DO-SISTEMA que o owner não escreveu, com mais de vinte e cinco letras", isMeta=True),
        _assistente(_ferramenta("Edit", file_path="commands/upgrade.md")),
        _assistente(_ferramenta("Write", file_path="docs/specs/upgrade.md")),
        _assistente(_texto("Parou porque a marca não estava no arquivo. <private>SEGREDO-DO-ASSISTENTE</private> Corrigi."),
                    quando="2026-11-10T13:05:00.000Z"),
        _owner("ok, e a senha é <private>SEGREDO-DO-OWNER</private> como combinado na reunião de ontem",
               quando="2026-11-10T13:06:00.000Z"),
        _assistente(_texto("Anotado, sem repetir a senha."), quando="2026-11-10T13:07:00.000Z"),
    ])


# --- as falas -----------------------------------------------------------------------------------------

def test_falas_so_do_owner_e_do_assistente(conversa):
    falas = _mod().falas(conversa)
    assert [f.quem for f in falas] == ["OWNER", "ASSISTENTE", "OWNER", "ASSISTENTE"]
    assert falas[0].texto == PEDIDO and falas[0].quando == "2026-11-10 13:00"
    tudo = "\n".join(f.texto for f in falas)
    for fora in ("RACIOCINIO-INTERNO", "CONTEUDO-DO-ARQUIVO-LIDO", "FALA-DE-AJUDANTE", "AVISO-DO-SISTEMA",
                 "SEGREDO-DO-ASSISTENTE", "SEGREDO-DO-OWNER"):
        assert fora not in tudo, f"{fora} não é fala da conversa e entrou no texto"


def test_o_turno_do_assistente_vira_uma_fala_com_o_que_ele_gravou(conversa):
    falas = _mod().falas(conversa)
    turno = falas[1]
    assert "Vou abrir o comando de upgrade." in turno.texto and "Corrigi." in turno.texto
    assert turno.gravou == ["commands/upgrade.md", "docs/specs/upgrade.md"], "o que foi gravado no turno, sem repetir, na ordem"
    assert falas[3].gravou == []


def test_comando_do_kit_aparece_com_o_nome_e_o_pedido(tmp_path):
    com_pedido = ("<command-message>mss-spec:duvida</command-message>\n<command-name>/mss-spec:duvida</command-name>\n"
                  "<command-args>como o hook de publicação decide o que negar?</command-args>")
    sem_pedido = "<command-message>mss-spec:mapa</command-message>\n<command-name>/mss-spec:mapa</command-name>"
    arq = _conversa(tmp_path, "c1", [_owner(com_pedido), _assistente(_texto("Decide pela branch.")), _owner(sem_pedido)])
    falas = _mod().falas(arq)
    assert falas[0].texto == "/mss-spec:duvida como o hook de publicação decide o que negar?"
    assert falas[2].texto == "/mss-spec:mapa", "comando sem argumento ainda é fala do owner"


def test_texto_colado_pelo_owner_fica_e_retorno_de_hook_sai(tmp_path):
    colado = "veja isto <pasted_content id=\"x1\">erro na linha 42 do arquivo de carga</pasted_content> e me diga"
    arq = _conversa(tmp_path, "c2", [
        _owner(colado),
        _owner("Stop hook feedback:\n[mss-spec] Antes de entregar — fonte ou não sei"),
        _owner([{"type": "text", "text": "<system-reminder>lembrete do sistema</system-reminder>"}]),
    ])
    falas = _mod().falas(arq)
    assert len(falas) == 1 and "erro na linha 42 do arquivo de carga" in falas[0].texto


def test_linha_torta_e_arquivo_que_nao_abre_nao_derrubam(tmp_path):
    arq = _conversa(tmp_path, "c3", [_owner(PEDIDO)], cru=["{isto não é json", "", "[1, 2, 3]", "\"solto\""])
    assert [f.texto for f in _mod().falas(arq)] == [PEDIDO]
    assert _mod().falas(tmp_path / "nao-existe.jsonl") == []


# --- achados da revisão (2026-11-11), cada um visto nas conversas reais do kit -----------------------

def _fila(texto, modo="prompt", origem="human", quando="2026-11-10T13:02:00.000Z"):
    """A fala digitada enquanto o assistente trabalhava: o app grava como anexo de fila, não como `user`."""
    return {"type": "attachment", "timestamp": quando,
            "attachment": {"type": "queued_command", "prompt": texto, "commandMode": modo,
                           "origin": {"kind": origem}, "timestamp": quando}}


CORRECAO = "Eu quero uma análise, não é para sair desenvolvendo nem planejando nada"


def test_fala_digitada_enquanto_o_assistente_trabalhava_entra(tmp_path):
    arq = _conversa(tmp_path, "f1", [
        _owner(PEDIDO), _assistente(_texto("Começando o plano.")), _fila(CORRECAO), _assistente(_texto("Entendido, só análise.")),
    ])
    falas = _mod().falas(arq)
    assert [(f.quem, f.texto) for f in falas] == [
        ("OWNER", PEDIDO), ("ASSISTENTE", "Começando o plano."), ("OWNER", CORRECAO), ("ASSISTENTE", "Entendido, só análise.")]
    assert falas[2].quando == "2026-11-10 13:02"


def test_fala_que_veio_pela_fila_e_pelo_registro_entra_uma_vez(tmp_path):
    for nome, ordem in (("f2", [_fila(CORRECAO), _owner(CORRECAO)]), ("f3", [_owner(CORRECAO), _fila(CORRECAO)])):
        arq = _conversa(tmp_path, nome, [_owner(PEDIDO), *ordem, _assistente(_texto("Certo."))])
        assert [f.texto for f in _mod().falas(arq) if f.quem == "OWNER"] == [PEDIDO, CORRECAO], nome
    repetiu = _conversa(tmp_path, "f4", [_owner(CORRECAO), _assistente(_texto("Certo.")), _owner(CORRECAO)])
    assert len([f for f in _mod().falas(repetiu) if f.quem == "OWNER"]) == 2, "o owner repetir a frase é fala de verdade"


def test_aviso_do_app_nao_vira_fala(tmp_path):
    notificacao = "<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n</task-notification>\nRead the output file to see it."
    resumo = ("This session is being continued from a previous conversation that ran out of context. "
              "O owner rodou <command-name>/mss-spec:bug</command-name> antes.")
    arq = _conversa(tmp_path, "a1", [
        _owner(PEDIDO),
        _owner(notificacao, origin={"kind": "task-notification"}, promptSource="system"),
        _fila(notificacao, modo="task-notification", origem="task-notification"),
        _owner(resumo, isCompactSummary=True, isVisibleInTranscriptOnly=True),
        _owner("Resumo sem prefixo conhecido, citando <command-name>/mss-spec:bug</command-name>", isCompactSummary=True),
        _owner([{"type": "text", "text": "[Request interrupted by user]"}]),
        _owner([{"type": "text", "text": "[Request interrupted by user for tool use]"}]),
        _owner("The app was quit while you were working. Please continue where you left off."),
        _owner("mensagem de outro ajudante com mais de vinte e cinco letras", origin={"kind": "peer"}),
        {**_assistente(_texto("API Error: Unable to connect to API (ConnectionRefused)")), "isApiErrorMessage": True},
        {"type": "assistant", "timestamp": "2026-11-10T13:03:00.000Z",
         "message": {"role": "assistant", "model": "<synthetic>", "content": [_texto("No response requested.")]}},
    ])
    falas = _mod().falas(arq)
    assert [(f.quem, f.texto) for f in falas] == [("OWNER", PEDIDO)], "só a fala do owner é fala"


def test_private_nao_escapa_com_tag_dentro_nem_sem_fechar(tmp_path):
    arq = _conversa(tmp_path, "p1", [
        _owner("a config é <private>senha=ABC <b>x</b> TOKEN-SECRETO-123</private> e está combinado assim"),
        _assistente(_texto("Anotado. <private>SEG-A <i>com</i> tag</private> Sigo. <private>SEG-B sem fechar")),
        _owner("a outra senha é <private>SEGREDO-SEM-FECHAR e segue o texto até o fim"),
        _fila("pela fila: <private>SEGREDO-DA-FILA</private> fim da fala digitada no meio do trabalho"),
    ])
    falas = _mod().falas(arq)
    tudo = "\n".join(f.texto for f in falas)
    for segredo in ("TOKEN-SECRETO-123", "senha=ABC", "SEG-A", "SEG-B", "SEGREDO-SEM-FECHAR", "SEGREDO-DA-FILA", "private"):
        assert segredo not in tudo, f"{segredo} escapou do trecho privado"
    assert "a config é" in falas[0].texto and "combinado assim" in falas[0].texto
    assert "Anotado." in falas[1].texto and "Sigo." in falas[1].texto


def test_o_que_o_owner_escreveu_entre_sinais_de_menor_e_maior_fica(tmp_path):
    arq = _conversa(tmp_path, "t1", [
        _owner('memória do plugin: <StatusBadge tone="ok">Processado</StatusBadge> vira pílula verde'),
        _owner("rode git switch -c <nome> e depois cole aqui o </body> do html"),
        _owner("o hook disse [mss-spec] Janela em 76% e agora o que faço?"),
        _owner("linha um do pedido\nlinha dois do pedido"),
    ])
    textos = [f.texto for f in _mod().falas(arq)]
    assert textos == [
        'memória do plugin: <StatusBadge tone="ok">Processado</StatusBadge> vira pílula verde',
        "rode git switch -c <nome> e depois cole aqui o </body> do html",
        "o hook disse [mss-spec] Janela em 76% e agora o que faço?",
        "linha um do pedido\nlinha dois do pedido",
    ]


def test_nome_de_comando_citado_no_meio_da_fala_nao_vira_comando(tmp_path):
    arq = _conversa(tmp_path, "t2", [_owner("ontem eu rodei <command-name>/mss-spec:bug</command-name> e travou tudo")])
    assert not _mod().falas(arq)[0].texto.startswith("/mss-spec:bug"), "só o registro que É um comando sai com o nome na frente"


# --- o texto gravado ---------------------------------------------------------------------------------

def test_gravar_texto_numera_as_falas_e_nao_tem_linha_gigante(conversa, tmp_path):
    saida = tmp_path / "saida"
    destino = _mod().gravar_texto(conversa, saida)
    assert destino == saida / "aaaa1111-2222-3333-4444-555566667777.txt"
    linhas = destino.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("# Conversa aaaa1111-2222-3333-4444-555566667777") and "4 falas" in linhas[0]
    assert "[001] OWNER (2026-11-10 13:00)" in linhas and "[002] ASSISTENTE (2026-11-10 13:01)" in linhas
    assert "(gravou: commands/upgrade.md, docs/specs/upgrade.md)" in linhas
    assert max(len(l) for l in linhas) <= _mod().LARGURA == 160, "linha longa demais: o ajudante lê por linha e cita `arquivo:linha`"


def test_fala_comprida_e_quebrada_em_linhas(tmp_path):
    comprido = " ".join(f"palavra{i}" for i in range(400))
    arq = _conversa(tmp_path, "c4", [_owner(comprido)])
    destino = _mod().gravar_texto(arq, tmp_path / "saida")
    linhas = destino.read_text(encoding="utf-8").splitlines()
    assert max(len(l) for l in linhas) <= 160
    assert " ".join(l for l in linhas if l.startswith("palavra")) == comprido, "a quebra não pode perder nem trocar texto"


def test_conversa_sem_fala_nao_grava(tmp_path):
    arq = _conversa(tmp_path, "vazia", [_resultado("só ferramenta")])
    saida = tmp_path / "saida"
    assert _mod().gravar_texto(arq, saida) is None
    assert not saida.exists() or not list(saida.iterdir())


def test_pasta_de_saida_padrao_fica_fora_do_repo_e_do_claude(monkeypatch, tmp_path):
    m = _mod()
    assert m.pasta_de_saida({}) == Path.home() / "mss-spec" / "conversas"
    assert m.pasta_de_saida({"MSS_CONVERSAS_DIR": str(tmp_path)}) == tmp_path
    assert os.environ.get("MSS_CONVERSAS_DIR"), "a suíte tem de desviar a pasta real do owner (tests/conftest.py)"


# --- listar e achar ----------------------------------------------------------------------------------

@pytest.fixture
def pasta(tmp_path):
    p = tmp_path / "proj"
    velha = _conversa(p, "aaaa1111-velha", [_owner(PEDIDO)])
    nova = _conversa(p, "bbbb2222-nova", [_owner("Quero trocar a junção pelo marketplace local nesta máquina")])
    outra = _conversa(p, "aaaa9999-outra", [_owner("Revisar o texto do LEIA-ME antes de publicar a versão")])
    _conversa(p, "agent-xyz", [_owner("fala de ajudante gravada em arquivo próprio, não é conversa do owner")])
    for i, arq in enumerate((velha, outra, nova)):
        os.utime(arq, (1_700_000_000 + i * 1000, 1_700_000_000 + i * 1000))
    return p


def test_listar_da_mais_nova_pra_mais_velha_com_o_primeiro_pedido(pasta):
    resumos = _mod().listar(pasta)
    assert [r.ident for r in resumos] == ["bbbb2222-nova", "aaaa9999-outra", "aaaa1111-velha"], "arquivo de ajudante não é conversa"
    assert resumos[0].pedido.startswith("Quero trocar a junção") and resumos[0].tamanho > 0
    assert len(_mod().listar(pasta, quantas=2)) == 2


def test_achar_por_comeco_do_id_por_caminho_e_por_palavra(pasta):
    m = _mod()
    assert [p.stem for p in m.achar(pasta, "bbbb")] == ["bbbb2222-nova"]
    assert {p.stem for p in m.achar(pasta, "aaaa")} == {"aaaa1111-velha", "aaaa9999-outra"}
    assert m.achar(pasta, str(pasta / "aaaa1111-velha.jsonl")) == [pasta / "aaaa1111-velha.jsonl"]
    assert [p.stem for p in m.achar(pasta, "upgrade transportes")] == ["aaaa1111-velha"], "todas as palavras, sem ligar pra maiúscula"
    assert m.achar(pasta, "nada-que-exista") == []


def test_palavra_que_tambem_e_comeco_de_id_traz_as_duas(tmp_path):
    p = tmp_path / "proj"
    _conversa(p, "cafe1234-id", [_owner("Revisar o texto do LEIA-ME antes de publicar a versão")])
    _conversa(p, "bbbb0000-pedido", [_owner("Quero entender por que o cafe da manhã não entrou no relatório")])
    assert {x.stem for x in _mod().achar(p, "cafe")} == {"cafe1234-id", "bbbb0000-pedido"}


def test_listar_marca_a_conversa_em_curso(pasta):
    resumos = _mod().listar(pasta, ambiente={"CLAUDE_CODE_SESSION_ID": "bbbb2222-nova"})
    assert [r.ident for r in resumos if r.esta] == ["bbbb2222-nova"]


def test_pasta_das_conversas_pelo_caminho_do_projeto(tmp_path):
    m = _mod()
    config = tmp_path / "config"
    raiz = tmp_path / "Meu Projeto_1"
    raiz.mkdir()
    esperado = config / "projects" / m.apelido_da_pasta(raiz)
    assert m.pasta_das_conversas({"CLAUDE_CONFIG_DIR": str(config)}, raiz) is None, "sem a pasta, não inventa"
    esperado.mkdir(parents=True)
    assert m.pasta_das_conversas({"CLAUDE_CONFIG_DIR": str(config)}, raiz) == esperado
    assert m.apelido_da_pasta(Path(r"C:\Ronaldo\_Mitsui\Python\Spec-Powers")) == "C--Ronaldo--Mitsui-Python-Spec-Powers"


# --- linha de comando --------------------------------------------------------------------------------

def _rodar(*args, env=None):
    ambiente = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})}
    r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, env=ambiente, timeout=60)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def test_cli_listar_e_texto(pasta, tmp_path):
    codigo, saida, _ = _rodar("listar", "--pasta", str(pasta))
    assert codigo == 0 and saida.index("bbbb2222-nova") < saida.index("aaaa1111-velha")
    destino = tmp_path / "saida"
    codigo, saida, _ = _rodar("texto", "bbbb", "--pasta", str(pasta), "--saida", str(destino))
    assert codigo == 0, saida
    assert str(destino / "bbbb2222-nova.txt") in saida and "mss-spec:pesquisador" in saida
    assert (destino / "bbbb2222-nova.txt").is_file()


def test_cli_mais_de_uma_ou_nenhuma_sai_com_1_e_nao_grava(pasta, tmp_path):
    destino = tmp_path / "saida"
    codigo, saida, _ = _rodar("texto", "aaaa", "--pasta", str(pasta), "--saida", str(destino))
    assert codigo == 1 and "aaaa1111-velha" in saida and "aaaa9999-outra" in saida, "tem de mostrar as que casaram"
    codigo, saida, _ = _rodar("texto", "zzzz", "--pasta", str(pasta), "--saida", str(destino))
    assert codigo == 1 and "listar" in saida
    assert not destino.exists()


def test_cli_sem_achar_a_pasta_das_conversas_sai_com_2(tmp_path):
    env = {"CLAUDE_CONFIG_DIR": str(tmp_path / "config-vazia"), "CLAUDE_CODE_SESSION_ID": ""}
    codigo, saida, _ = _rodar("listar", env=env)
    assert codigo == 2 and "--pasta" in saida


def test_cli_caminho_do_arquivo_basta_mesmo_sem_a_pasta_das_conversas(tmp_path):
    arq = _conversa(tmp_path / "pasta com espaço", "dddd4444", [_owner(PEDIDO)])
    env = {"CLAUDE_CONFIG_DIR": str(tmp_path / "config-vazia"), "CLAUDE_CODE_SESSION_ID": ""}
    destino = tmp_path / "saida"
    codigo, saida, _ = _rodar("texto", str(arq), "--saida", str(destino), env=env)
    assert codigo == 0, saida
    assert (destino / "dddd4444.txt").is_file()


def test_cli_conversa_sem_fala_sai_com_1_e_diz_por_que(pasta, tmp_path):
    _conversa(pasta, "eeee5555-vazia", [_resultado("só ferramenta")])
    destino = tmp_path / "saida"
    codigo, saida, _ = _rodar("texto", "eeee5555", "--pasta", str(pasta), "--saida", str(destino))
    assert codigo == 1 and "não tem fala" in saida
    assert not destino.exists()
