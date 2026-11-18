"""Outra conversa em texto (0.58.0) — `templates/conversa_texto.py`, apoio do ajudante pesquisador.

A conversa gravada pelo app é um `.jsonl` com resultado de ferramenta, raciocínio e fala de ajudante no meio;
o ajudante (que só lê) não consegue tirar dali o que foi dito. O script lista as conversas do projeto e grava
uma delas em texto, só com as falas do owner e do assistente (critério 4 de `docs/specs/ajudante-pesquisador.md`).

Camadas (2026-11-18, `docs/decisoes.md`): o script lê e grava por um objeto de disco; aqui ele é um dicionário
(`Disco`) com as conversas, a data de cada uma e os textos gravados, e a linha de comando roda pelo `main` com esse
disco. O disco de verdade (a conversa lida linha a linha, a gravação com provisório e troca, a data do arquivo)
fica num teste só, numa pasta montada uma vez; o processo python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "conversa_texto.py"
BASE = REPO.parent / "conversas-que-nao-existem"          # absoluto, nunca criado
PROJ, SAIDA = BASE / "proj", BASE / "saida"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("conversa_texto", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


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


def _jsonl(registros, cru=()):
    return "\n".join([json.dumps(r, ensure_ascii=False) for r in registros] + list(cru)) + "\n"


def _marca_do_dia(dia):
    """A data de gravação ao meio-dia (hora local) do `dia`."""
    return time.mktime(time.strptime(dia + " 12:00", "%Y-%m-%d %H:%M"))


class Disco:
    """As conversas e os textos gravados em memória, com os métodos do `DiscoReal`."""

    def __init__(self):
        self.dados, self.datas, self.gravados = {}, {}, []

    def conversa(self, pasta, nome, registros, cru=(), data=1_700_000_000.0):
        arq = Path(pasta) / f"{nome}.jsonl"
        self.dados[arq], self.datas[arq] = _jsonl(registros, cru), data
        return arq

    def linhas(self, arquivo):
        p = Path(arquivo)                              # Path(None) levanta TypeError, como o open
        if p not in self.dados:
            raise FileNotFoundError(str(p))
        return iter(self.dados[p].splitlines(keepends=True))

    def jsonl(self, pasta):
        return [p for p in self.dados if p.parent == Path(pasta) and p.suffix == ".jsonl"]

    def marca(self, p):
        if Path(p) not in self.dados:
            raise FileNotFoundError(str(p))
        return self.datas.get(Path(p), 1_700_000_000.0), len(self.dados[Path(p)].encode("utf-8"))

    def eh_arquivo(self, p):
        return Path(p) in self.dados

    def eh_pasta(self, p):
        return any(Path(p) in q.parents for q in self.dados)

    def pastas_em(self, base):
        filhos = {Path(base) / q.relative_to(base).parts[0] for q in self.dados if Path(base) in q.parents}
        if not filhos:
            raise FileNotFoundError(str(base))
        return sorted(filhos)

    def ler_texto(self, p):
        return self.dados[Path(p)]

    def gravar(self, destino, conteudo):
        self.dados[Path(destino)] = conteudo
        self.gravados.append(Path(destino))


PEDIDO = "Preciso entender por que o upgrade do Transportes parou na segunda rodada"
CONVERSA = [
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
]
ID = "aaaa1111-2222-3333-4444-555566667777"


@pytest.fixture
def disco():
    return Disco()


def _falas(mod, registros, cru=()):
    d = Disco()
    return mod.falas(d.conversa(PROJ, "c", registros, cru), d)


# --- as falas -----------------------------------------------------------------------------------------

def test_falas_so_do_owner_e_do_assistente(mod):
    falas = _falas(mod, CONVERSA)
    assert [f.quem for f in falas] == ["OWNER", "ASSISTENTE", "OWNER", "ASSISTENTE"]
    assert falas[0].texto == PEDIDO and falas[0].quando == "2026-11-10 13:00"
    tudo = "\n".join(f.texto for f in falas)
    for fora in ("RACIOCINIO-INTERNO", "CONTEUDO-DO-ARQUIVO-LIDO", "FALA-DE-AJUDANTE", "AVISO-DO-SISTEMA",
                 "SEGREDO-DO-ASSISTENTE", "SEGREDO-DO-OWNER"):
        assert fora not in tudo, f"{fora} não é fala da conversa e entrou no texto"


def test_o_turno_do_assistente_vira_uma_fala_com_o_que_ele_gravou(mod):
    falas = _falas(mod, CONVERSA)
    turno = falas[1]
    assert "Vou abrir o comando de upgrade." in turno.texto and "Corrigi." in turno.texto
    assert turno.gravou == ["commands/upgrade.md", "docs/specs/upgrade.md"], "o que foi gravado no turno, sem repetir, na ordem"
    assert falas[3].gravou == []


def test_comando_do_kit_aparece_com_o_nome_e_o_pedido(mod):
    com_pedido = ("<command-message>mss-spec:duvida</command-message>\n<command-name>/mss-spec:duvida</command-name>\n"
                  "<command-args>como o hook de publicação decide o que negar?</command-args>")
    sem_pedido = "<command-message>mss-spec:mapa</command-message>\n<command-name>/mss-spec:mapa</command-name>"
    falas = _falas(mod, [_owner(com_pedido), _assistente(_texto("Decide pela branch.")), _owner(sem_pedido)])
    assert falas[0].texto == "/mss-spec:duvida como o hook de publicação decide o que negar?"
    assert falas[2].texto == "/mss-spec:mapa", "comando sem argumento ainda é fala do owner"


def test_texto_colado_pelo_owner_fica_e_retorno_de_hook_sai(mod):
    colado = "veja isto <pasted_content id=\"x1\">erro na linha 42 do arquivo de carga</pasted_content> e me diga"
    falas = _falas(mod, [
        _owner(colado),
        _owner("Stop hook feedback:\n[mss-spec] Antes de entregar — fonte ou não sei"),
        _owner([{"type": "text", "text": "<system-reminder>lembrete do sistema</system-reminder>"}]),
    ])
    assert len(falas) == 1 and "erro na linha 42 do arquivo de carga" in falas[0].texto


def test_linha_torta_e_arquivo_que_nao_abre_nao_derrubam(mod, disco):
    assert [f.texto for f in _falas(mod, [_owner(PEDIDO)], cru=["{isto não é json", "", "[1, 2, 3]", "\"solto\""])] == [PEDIDO]
    assert mod.falas(PROJ / "nao-existe.jsonl", disco) == []
    assert mod.falas(None, disco) == []


# --- achados da revisão (2026-11-11), cada um visto nas conversas reais do kit -----------------------

def _fila(texto, modo="prompt", origem="human", quando="2026-11-10T13:02:00.000Z"):
    """A fala digitada enquanto o assistente trabalhava: o app grava como anexo de fila, não como `user`."""
    return {"type": "attachment", "timestamp": quando,
            "attachment": {"type": "queued_command", "prompt": texto, "commandMode": modo,
                           "origin": {"kind": origem}, "timestamp": quando}}


CORRECAO = "Eu quero uma análise, não é para sair desenvolvendo nem planejando nada"


def test_fala_digitada_enquanto_o_assistente_trabalhava_entra(mod):
    falas = _falas(mod, [_owner(PEDIDO), _assistente(_texto("Começando o plano.")), _fila(CORRECAO),
                         _assistente(_texto("Entendido, só análise."))])
    assert [(f.quem, f.texto) for f in falas] == [
        ("OWNER", PEDIDO), ("ASSISTENTE", "Começando o plano."), ("OWNER", CORRECAO), ("ASSISTENTE", "Entendido, só análise.")]
    assert falas[2].quando == "2026-11-10 13:02"


def test_fala_que_veio_pela_fila_e_pelo_registro_entra_uma_vez(mod):
    for nome, ordem in (("f2", [_fila(CORRECAO), _owner(CORRECAO)]), ("f3", [_owner(CORRECAO), _fila(CORRECAO)])):
        falas = _falas(mod, [_owner(PEDIDO), *ordem, _assistente(_texto("Certo."))])
        assert [f.texto for f in falas if f.quem == "OWNER"] == [PEDIDO, CORRECAO], nome
    repetiu = _falas(mod, [_owner(CORRECAO), _assistente(_texto("Certo.")), _owner(CORRECAO)])
    assert len([f for f in repetiu if f.quem == "OWNER"]) == 2, "o owner repetir a frase é fala de verdade"


def test_aviso_do_app_nao_vira_fala(mod):
    notificacao = "<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n</task-notification>\nRead the output file to see it."
    resumo = ("This session is being continued from a previous conversation that ran out of context. "
              "O owner rodou <command-name>/mss-spec:bug</command-name> antes.")
    falas = _falas(mod, [
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
    assert [(f.quem, f.texto) for f in falas] == [("OWNER", PEDIDO)], "só a fala do owner é fala"


def test_private_nao_escapa_com_tag_dentro_nem_sem_fechar(mod):
    falas = _falas(mod, [
        _owner("a config é <private>senha=ABC <b>x</b> TOKEN-SECRETO-123</private> e está combinado assim"),
        _assistente(_texto("Anotado. <private>SEG-A <i>com</i> tag</private> Sigo. <private>SEG-B sem fechar")),
        _owner("a outra senha é <private>SEGREDO-SEM-FECHAR e segue o texto até o fim"),
        _fila("pela fila: <private>SEGREDO-DA-FILA</private> fim da fala digitada no meio do trabalho"),
    ])
    tudo = "\n".join(f.texto for f in falas)
    for segredo in ("TOKEN-SECRETO-123", "senha=ABC", "SEG-A", "SEG-B", "SEGREDO-SEM-FECHAR", "SEGREDO-DA-FILA", "private"):
        assert segredo not in tudo, f"{segredo} escapou do trecho privado"
    assert "a config é" in falas[0].texto and "combinado assim" in falas[0].texto
    assert "Anotado." in falas[1].texto and "Sigo." in falas[1].texto


def test_o_que_o_owner_escreveu_entre_sinais_de_menor_e_maior_fica(mod):
    textos = [f.texto for f in _falas(mod, [
        _owner('memória do plugin: <StatusBadge tone="ok">Processado</StatusBadge> vira pílula verde'),
        _owner("rode git switch -c <nome> e depois cole aqui o </body> do html"),
        _owner("o hook disse [mss-spec] Janela em 76% e agora o que faço?"),
        _owner("linha um do pedido\nlinha dois do pedido"),
    ])]
    assert textos == [
        'memória do plugin: <StatusBadge tone="ok">Processado</StatusBadge> vira pílula verde',
        "rode git switch -c <nome> e depois cole aqui o </body> do html",
        "o hook disse [mss-spec] Janela em 76% e agora o que faço?",
        "linha um do pedido\nlinha dois do pedido",
    ]


def test_nome_de_comando_citado_no_meio_da_fala_nao_vira_comando(mod):
    falas = _falas(mod, [_owner("ontem eu rodei <command-name>/mss-spec:bug</command-name> e travou tudo")])
    assert not falas[0].texto.startswith("/mss-spec:bug"), "só o registro que É um comando sai com o nome na frente"


# --- o texto gravado ---------------------------------------------------------------------------------

def test_gravar_texto_numera_as_falas_e_nao_tem_linha_gigante(mod, disco):
    destino = mod.gravar_texto(disco.conversa(PROJ, ID, CONVERSA), SAIDA, disco=disco)
    assert destino == SAIDA / f"{ID}.txt" and disco.gravados == [destino]
    linhas = disco.ler_texto(destino).splitlines()
    assert linhas[0].startswith(f"# Conversa {ID}") and "4 falas" in linhas[0]
    assert "[001] OWNER (2026-11-10 13:00)" in linhas and "[002] ASSISTENTE (2026-11-10 13:01)" in linhas
    assert "(gravou: commands/upgrade.md, docs/specs/upgrade.md)" in linhas
    assert max(len(l) for l in linhas) <= mod.LARGURA == 160, "linha longa demais: o ajudante lê por linha e cita `arquivo:linha`"


def test_fala_comprida_e_quebrada_em_linhas(mod, disco):
    comprido = " ".join(f"palavra{i}" for i in range(400))
    destino = mod.gravar_texto(disco.conversa(PROJ, "c4", [_owner(comprido)]), SAIDA, disco=disco)
    linhas = disco.ler_texto(destino).splitlines()
    assert max(len(l) for l in linhas) <= 160
    assert " ".join(l for l in linhas if l.startswith("palavra")) == comprido, "a quebra não pode perder nem trocar texto"


def test_conversa_sem_fala_nao_grava(mod, disco):
    assert mod.gravar_texto(disco.conversa(PROJ, "vazia", [_resultado("só ferramenta")]), SAIDA, disco=disco) is None
    assert disco.gravados == []


def test_pasta_de_saida_padrao_fica_fora_do_repo_e_do_claude(mod):
    assert mod.pasta_de_saida({}) == Path.home() / "mss-spec" / "conversas"
    assert mod.pasta_de_saida({"MSS_CONVERSAS_DIR": str(SAIDA)}) == SAIDA
    assert os.environ.get("MSS_CONVERSAS_DIR"), "a suíte tem de desviar a pasta real do owner (tests/conftest.py)"


# --- listar e achar ----------------------------------------------------------------------------------

@pytest.fixture
def pasta(disco):
    for i, (nome, pedido) in enumerate((("aaaa1111-velha", PEDIDO),
                                         ("aaaa9999-outra", "Revisar o texto do LEIA-ME antes de publicar a versão"),
                                         ("bbbb2222-nova", "Quero trocar a junção pelo marketplace local nesta máquina"))):
        disco.conversa(PROJ, nome, [_owner(pedido)], data=1_700_000_000 + i * 1000)
    disco.conversa(PROJ, "agent-xyz", [_owner("fala de ajudante gravada em arquivo próprio, não é conversa do owner")],
                   data=1_800_000_000)
    return PROJ


def test_listar_da_mais_nova_pra_mais_velha_com_o_primeiro_pedido(mod, disco, pasta):
    resumos = mod.listar(pasta, ambiente={}, disco=disco)
    assert [r.ident for r in resumos] == ["bbbb2222-nova", "aaaa9999-outra", "aaaa1111-velha"], "arquivo de ajudante não é conversa"
    assert resumos[0].pedido.startswith("Quero trocar a junção") and resumos[0].tamanho > 0
    assert len(mod.listar(pasta, quantas=2, ambiente={}, disco=disco)) == 2


def test_achar_por_comeco_do_id_por_caminho_e_por_palavra(mod, disco, pasta):
    assert [p.stem for p in mod.achar(pasta, "bbbb", disco)] == ["bbbb2222-nova"]
    assert {p.stem for p in mod.achar(pasta, "aaaa", disco)} == {"aaaa1111-velha", "aaaa9999-outra"}
    assert mod.achar(pasta, str(pasta / "aaaa1111-velha.jsonl"), disco) == [pasta / "aaaa1111-velha.jsonl"]
    assert [p.stem for p in mod.achar(pasta, "upgrade transportes", disco)] == ["aaaa1111-velha"], \
        "todas as palavras, sem ligar pra maiúscula"
    assert mod.achar(pasta, "nada-que-exista", disco) == []


def test_palavra_que_tambem_e_comeco_de_id_traz_as_duas(mod, disco):
    disco.conversa(PROJ, "cafe1234-id", [_owner("Revisar o texto do LEIA-ME antes de publicar a versão")])
    disco.conversa(PROJ, "bbbb0000-pedido", [_owner("Quero entender por que o cafe da manhã não entrou no relatório")])
    assert {x.stem for x in mod.achar(PROJ, "cafe", disco)} == {"cafe1234-id", "bbbb0000-pedido"}


def test_listar_marca_a_conversa_em_curso(mod, disco, pasta):
    resumos = mod.listar(pasta, ambiente={"CLAUDE_CODE_SESSION_ID": "bbbb2222-nova"}, disco=disco)
    assert [r.ident for r in resumos if r.esta] == ["bbbb2222-nova"]


def test_pasta_das_conversas_pelo_caminho_do_projeto(mod, disco):
    config, raiz = BASE / "config", BASE / "Meu Projeto_1"
    esperado = config / "projects" / mod.apelido_da_pasta(raiz)
    amb = {"CLAUDE_CONFIG_DIR": str(config)}
    assert mod.pasta_das_conversas(amb, raiz, disco) is None, "sem a pasta, não inventa"
    disco.conversa(esperado, "x", [_owner(PEDIDO)])
    assert mod.pasta_das_conversas(amb, raiz, disco) == esperado
    em_curso = disco.conversa(config / "projects" / "outro", "sessao-abc", [_owner(PEDIDO)])
    assert mod.pasta_das_conversas(dict(amb, CLAUDE_CODE_SESSION_ID="sessao-abc"), raiz, disco) == em_curso.parent
    assert mod.apelido_da_pasta(Path(r"C:\Ronaldo\_Mitsui\Python\Spec-Powers")) == "C--Ronaldo--Mitsui-Python-Spec-Powers"


# --- lote (o sono da memória, parte 2) ---------------------------------------------------------------

@pytest.fixture
def pasta_lote(disco):
    disco.conversa(PROJ, "aaaa-antes", [_owner(PEDIDO, quando="2026-11-10T13:00:00.000Z"),
                                        _assistente(_texto("Feito."), quando="2026-11-10T14:00:00.000Z")],
                   data=_marca_do_dia("2026-11-10"))
    disco.conversa(PROJ, "bbbb-no-dia", [_owner("Conversa gravada no próprio dia do último sono, já lida")],
                   data=_marca_do_dia("2026-11-13"))
    disco.conversa(PROJ, "cccc-depois", [_owner("Quero trocar a junção pelo marketplace local nesta máquina",
                                                quando="2026-11-14T09:00:00.000Z"),
                                         _assistente(_texto("Vou abrir o comando."), quando="2026-11-15T10:00:00.000Z")],
                   data=_marca_do_dia("2026-11-15"))
    disco.conversa(PROJ, "dddd-vazia", [_resultado("só ferramenta")], data=_marca_do_dia("2026-11-14"))
    disco.conversa(PROJ, "eeee-em-curso", [_owner("A conversa do próprio sono não se lê a si mesma")],
                   data=_marca_do_dia("2026-11-16"))
    disco.conversa(PROJ, "agent-xyz", [_owner("fala de ajudante gravada em arquivo próprio, não é conversa do owner")],
                   data=_marca_do_dia("2026-11-16"))
    return PROJ


EM_CURSO = {"CLAUDE_CODE_SESSION_ID": "eeee-em-curso"}


def test_lote_sem_data_grava_todas_menos_a_em_curso_e_as_de_ajudante(mod, disco, pasta_lote):
    itens = mod.lote(pasta_lote, "", SAIDA, ambiente=EM_CURSO, disco=disco)
    assert [i.ident for i in itens] == ["cccc-depois", "dddd-vazia", "bbbb-no-dia", "aaaa-antes"], "mais nova primeiro"
    assert sorted(p.name for p in disco.gravados) == ["aaaa-antes.txt", "bbbb-no-dia.txt", "cccc-depois.txt"]
    vazia = itens[1]
    assert vazia.texto is None and vazia.falas == 0, "conversa sem fala entra na lista, sem texto"


def test_lote_com_data_so_as_mudadas_depois_do_dia(mod, disco, pasta_lote):
    itens = mod.lote(pasta_lote, "2026-11-13", SAIDA, ambiente=EM_CURSO, disco=disco)
    assert [i.ident for i in itens] == ["cccc-depois", "dddd-vazia"], "o dia do último sono já foi lido"
    cccc = itens[0]
    assert cccc.periodo == "2026-11-14 09:00 a 2026-11-15 10:00" and cccc.falas == 2
    assert cccc.letras == len(disco.ler_texto(cccc.texto)) and cccc.pedido.startswith("Quero trocar")


# --- linha de comando, pelo main com o disco em memória ----------------------------------------------

@pytest.fixture
def cli(mod, disco, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(BASE / "config-vazia"))
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "")

    def rodar(*args, sessao=""):
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", sessao)
        codigo = mod.main(list(args), disco)
        return codigo, capsys.readouterr().out
    return rodar


def test_cli_lote_imprime_uma_linha_por_conversa_e_o_total(cli, pasta_lote):
    codigo, saida = cli("lote", "--desde", "2026-11-13", "--pasta", str(pasta_lote), "--saida", str(SAIDA),
                        sessao="eeee-em-curso")
    assert codigo == 0, saida
    assert "cccc-depois" in saida and "dddd-vazia" in saida and "aaaa-antes" not in saida
    assert "sem fala" in saida and "2 conversas" in saida and str(SAIDA) in saida
    codigo, saida = cli("lote", "--desde", "2026-12-01", "--pasta", str(pasta_lote), "--saida", str(SAIDA))
    assert codigo == 1 and "nenhuma conversa" in saida


def test_cli_lote_data_torta_sai_com_2(cli, pasta_lote):
    codigo, saida = cli("lote", "--desde", "13/11/2026", "--pasta", str(pasta_lote), "--saida", str(SAIDA))
    assert codigo == 2 and "AAAA-MM-DD" in saida


def test_cli_listar_e_texto(cli, disco, pasta):
    codigo, saida = cli("listar", "--pasta", str(pasta))
    assert codigo == 0 and saida.index("bbbb2222-nova") < saida.index("aaaa1111-velha")
    codigo, saida = cli("texto", "bbbb", "--pasta", str(pasta), "--saida", str(SAIDA))
    assert codigo == 0, saida
    assert str(SAIDA / "bbbb2222-nova.txt") in saida and "mss-spec:pesquisador" in saida
    assert disco.gravados == [SAIDA / "bbbb2222-nova.txt"]


def test_cli_mais_de_uma_ou_nenhuma_sai_com_1_e_nao_grava(cli, disco, pasta):
    codigo, saida = cli("texto", "aaaa", "--pasta", str(pasta), "--saida", str(SAIDA))
    assert codigo == 1 and "aaaa1111-velha" in saida and "aaaa9999-outra" in saida, "tem de mostrar as que casaram"
    codigo, saida = cli("texto", "zzzz", "--pasta", str(pasta), "--saida", str(SAIDA))
    assert codigo == 1 and "listar" in saida
    assert disco.gravados == []


def test_cli_sem_achar_a_pasta_das_conversas_sai_com_2(cli):
    codigo, saida = cli("listar")
    assert codigo == 2 and "--pasta" in saida


def test_cli_caminho_do_arquivo_basta_mesmo_sem_a_pasta_das_conversas(cli, disco):
    arq = disco.conversa(BASE / "pasta com espaço", "dddd4444", [_owner(PEDIDO)])
    codigo, saida = cli("texto", str(arq), "--saida", str(SAIDA))
    assert codigo == 0, saida
    assert disco.gravados == [SAIDA / "dddd4444.txt"]


def test_cli_conversa_sem_fala_sai_com_1_e_diz_por_que(cli, disco, pasta):
    disco.conversa(pasta, "eeee5555-vazia", [_resultado("só ferramenta")])
    codigo, saida = cli("texto", "eeee5555", "--pasta", str(pasta), "--saida", str(SAIDA))
    assert codigo == 1 and "não tem fala" in saida
    assert disco.gravados == []


# --- o disco de verdade e o processo (pasta montada uma vez) ----------------------------------------

@pytest.fixture(scope="module")
def real(tmp_path_factory):
    base = tmp_path_factory.mktemp("conversa_texto")
    pasta = base / "proj"
    pasta.mkdir()
    for nome, registros, dia in ((ID, CONVERSA, "2026-11-10"),
                                 ("bbbb2222-nova", [_owner("Quero trocar a junção pelo marketplace local nesta máquina",
                                                           quando="2026-11-14T09:00:00.000Z")], "2026-11-15"),
                                 ("agent-xyz", [_owner("fala de ajudante gravada em arquivo próprio, não é conversa")],
                                  "2026-11-16")):
        arq = pasta / f"{nome}.jsonl"
        arq.write_text(_jsonl(registros), encoding="utf-8")
        os.utime(arq, (_marca_do_dia(dia), _marca_do_dia(dia)))
    return base


def test_disco_de_verdade_le_linha_a_linha_e_grava_com_troca(mod, real):
    pasta, saida = real / "proj", real / "saida"
    assert [f.quem for f in mod.falas(pasta / f"{ID}.jsonl")] == ["OWNER", "ASSISTENTE", "OWNER", "ASSISTENTE"]
    assert mod.falas(pasta / "nao-existe.jsonl") == []
    assert [r.ident for r in mod.listar(pasta, ambiente={})] == ["bbbb2222-nova", ID], "data de verdade e sem ajudante"
    assert mod.achar(pasta, str(pasta / f"{ID}.jsonl")) == [pasta / f"{ID}.jsonl"]
    itens = mod.lote(pasta, "2026-11-12", saida, ambiente={})
    assert [i.ident for i in itens] == ["bbbb2222-nova"]
    assert itens[0].letras == len((saida / "bbbb2222-nova.txt").read_text(encoding="utf-8"))
    destino = mod.gravar_texto(pasta / f"{ID}.jsonl", saida)
    assert destino.read_text(encoding="utf-8").startswith(f"# Conversa {ID}")
    assert sorted(p.name for p in saida.iterdir()) == [f"{ID}.txt", "bbbb2222-nova.txt"], "sobrou o provisório"
    config = real / "config"
    (config / "projects" / mod.apelido_da_pasta(pasta)).mkdir(parents=True)
    assert mod.pasta_das_conversas({"CLAUDE_CONFIG_DIR": str(config)}, pasta) == \
        config / "projects" / mod.apelido_da_pasta(pasta)


def test_processo_grava_o_texto_e_diz_o_caminho(real):
    pasta, saida = real / "proj", real / "saida-cli"
    r = subprocess.run([sys.executable, str(SCRIPT), "texto", "bbbb", "--pasta", str(pasta), "--saida", str(saida)],
                       capture_output=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=60)
    texto = r.stdout.decode("utf-8", "replace")
    assert r.returncode == 0, texto + r.stderr.decode("utf-8", "replace")
    assert str(saida / "bbbb2222-nova.txt") in texto and "mss-spec:pesquisador" in texto
    assert (saida / "bbbb2222-nova.txt").is_file()
