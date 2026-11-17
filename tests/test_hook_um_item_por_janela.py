"""Um item por janela — um chat não abre uma 2ª feature enquanto a dele estiver aberta.

Nasceu do mesmo acidente do F-022: a janela de uma feature absorveu um 2º e um 3º assunto,
misturou branches e quebrou homologação. A regra "um assunto por janela" existia como ALERTA
("é alerta, não trava") e ficou muda. Virou trava (0.26.0) — mas contando por PROJETO: com 6
features abertas em 6 chats, o chat novo não abria nada e o owner passou a tirar o comando do
prompt (2026-09-24). Desde a 0.34.0 conta por CHAT (`session_id`): o hook lembra qual feature cada
chat abriu (`~/.claude/mss-spec/um-item-janelas.json`) e só bloqueia o MESMO chat pedindo outra.

Propriedades:
- chat sem feature → passa (e grava a dele); outras abertas no INDEX → passa com AVISO (parar e perguntar);
- chat com feature Y ainda aberta pedindo X → bloqueia; Y de novo → passa (retomar não é misturar);
  Y `fechada`/`pausada` (no INDEX ou no INDEX-historico) → passa e o chat fica com X;
- só age no comando de abrir feature — qualquer outro prompt passa calado;
- projeto sem INDEX (sem o kit) → passa;
- falha ABERTA: bug/entrada malformada libera (apagar prompt do owner por bug seria pior);
- escape consciente só do owner: `MSS_UM_ITEM_OFF=1`.

Camadas (2026-11-17): a REGRA (`regra`) é testada em memória — o INDEX, o INDEX-historico de cada projeto e o
estado dos chats ficam num objeto do teste e entram como dado; os caminhos dos projetos não existem. O disco de
verdade fica num teste só (a casca lê o INDEX e lê e grava o estado), numa pasta montada uma vez; o processo
python, num teste só.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from _texto_kit import texto_do_kit

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "um_item_por_janela.py"
BASE = Path(tempfile.gettempdir()) / "mss-cenario-sem-disco"
AGORA = datetime(2026, 11, 17, 12, 0, 0)

INDEX_VAZIO = """# Índice de tarefas

## A fazer (ordem)

## Fora de escopo (não fazer)
nada
"""

INDEX_COM_ABERTA = """# Índice de tarefas

## A fazer (ordem)
- [formatação da resposta no WhatsApp](../specs/formatacao-resposta-whatsapp.md) — juntar linhas quebradas e tirar travessão — aberta
- [relatório mensal](../specs/relatorio-mensal.md) — PDF por e-mail — fechada
- [importador de apólices](../specs/importador-apolices.md) — ler CSV da seguradora — pausada: aguardando layout novo

## Fora de escopo (não fazer)
nada
"""

INDEX_EM_ANDAMENTO = """# Índice de tarefas

## A fazer (ordem)
5. upgrade — sincroniza projeto existente com a evolução dos templates — **em andamento** (sem commit)
"""


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("um_item_por_janela", HOOK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Maquina:
    """O que o hook lê e grava no disco, em memória: o INDEX e o INDEX-historico de cada projeto e o estado dos
    chats. `avaliar` chama a regra com isso como dado e guarda o estado que ela devolve — o papel da casca."""

    def __init__(self, mod):
        self.mod, self.arquivos, self.estado, self.gravou = mod, {}, {}, False

    def projeto(self, nome, index=None, historico=None):
        raiz = BASE / nome
        if index is not None:
            self.index(raiz, index)
        if historico is not None:
            self.historico(raiz, historico)
        return raiz

    def index(self, raiz, texto):
        self.arquivos[(str(raiz), self.mod.INDEX_REL)] = texto

    def historico(self, raiz, texto):
        self.arquivos[(str(raiz), self.mod.HISTORICO_REL)] = texto

    def avaliar(self, evento, ambiente=None):
        cwd = evento.get("cwd") if isinstance(evento, dict) else None
        decisao, texto, mudancas = self.mod.regra(evento, ambiente or {},
                                                  lambda rel: self.arquivos.get((cwd, rel), ""),
                                                  lambda: self.estado, AGORA)
        if "estado" in mudancas:
            self.estado, self.gravou = mudancas["estado"], True
        return decisao, texto

    def decidir(self, evento, ambiente=None):
        decisao, texto = self.avaliar(evento, ambiente)
        return texto if decisao == "bloqueia" else None


@pytest.fixture()
def maq(mod):
    return Maquina(mod)


def _evento(prompt, raiz, sessao=None):
    ev = {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}
    if sessao is not None:
        ev["session_id"] = sessao
    return ev


# --- AC1: abertas ---------------------------------------------------------------------

def test_lista_abertas_ignora_fechada_e_pausada(mod):
    abertas = mod.abertas(INDEX_COM_ABERTA)
    assert len(abertas) == 1
    assert "formatação da resposta no WhatsApp" in abertas[0]


def test_em_andamento_conta_como_aberta(mod):
    abertas = mod.abertas(INDEX_EM_ANDAMENTO)
    assert len(abertas) == 1 and "upgrade" in abertas[0]


def test_indice_vazio_nao_tem_aberta(mod):
    assert mod.abertas(INDEX_VAZIO) == []


# --- AC2: decisão por chat -------------------------------------------------------------

def test_sem_aberta_passa(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz)) is None


def test_chat_novo_passa_mesmo_com_outra_aberta(maq):
    """O caso de 2026-09-24: 6 abertas em outros chats e o chat NOVO não abria nada."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    ev = _evento("/mss-spec:nova-feature login por SSO", raiz, sessao="chat-novo")
    assert maq.decidir(ev) is None, "chat novo bloqueado — a regra é por chat"


def test_chat_novo_com_outra_aberta_avisa_e_manda_perguntar(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    decisao, texto = maq.avaliar(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"))
    assert decisao == "avisa"
    assert "formatação da resposta no WhatsApp" in texto, "aviso não lista a outra aberta"
    assert "relatório mensal" not in texto, "listou feature fechada como aberta"
    assert "pergunte ao owner" in texto.lower(), "aviso não manda parar e perguntar (pasta em outra feature)"
    assert "pausada" in texto.lower(), "aviso não ensina a limpar linha parada (pausada: <motivo>)"


def test_mesmo_chat_pedindo_outra_bloqueia(maq):
    """O F-022 de verdade: a janela de uma feature absorvendo um 2º assunto."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    motivo = maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"))
    assert motivo is not None, "o mesmo chat abriu uma 2ª feature — a trava não travou"
    assert "login por SSO" in motivo, "motivo não diz de qual feature este chat já é"
    assert "chat novo" in motivo.lower(), "motivo não manda abrir um chat novo"
    assert "pausada" in motivo.lower() and "janela" in motivo.lower()


def test_outro_chat_nao_herda_a_trava(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c2")) is None


def test_mesma_feature_retoma(maq):
    """Retomar a feature do chat não é misturar — passa, inclusive com grafia diferente."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature formatação da resposta no WhatsApp", raiz,
                               sessao="c1")) is None
    for texto in ("/mss-spec:nova-feature formatação da resposta no WhatsApp",
                  "/mss-spec:nova-feature formatacao-resposta-whatsapp",
                  "/mss-spec:nova-feature Formatação da Resposta no whatsapp — continuar"):
        assert maq.decidir(_evento(texto, raiz, sessao="c1")) is None, f"barrou retomar: {texto!r}"


def test_retomar_nao_avisa_da_propria_feature(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    decisao, _ = maq.avaliar(_evento("/mss-spec:nova-feature formatacao-resposta-whatsapp", raiz, sessao="c1"))
    assert decisao == "libera", "avisou que a própria feature está aberta"


def test_feature_do_chat_fora_do_index_segue_valendo(maq):
    """A linha do INDEX só nasce no passo 3 do nova-feature — antes disso a feature do chat vale."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is not None


def test_feature_do_chat_encerrada_libera_a_proxima(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    for encerrada in ("relatório mensal", "importador-apolices"):       # fechada · pausada
        sessao = f"c-{encerrada}"
        assert maq.decidir(_evento(f"/mss-spec:nova-feature {encerrada}", raiz, sessao=sessao)) is None
        assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao=sessao)) is None, \
            f"{encerrada} já saiu de aberta e o chat não pôde abrir a próxima"
        assert maq.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao=sessao)) is not None, \
            "o chat não passou a ser da feature nova"


def test_fechada_movida_pro_historico_libera_a_proxima(maq):
    """O rodízio move a linha `fechada` pro INDEX-historico.md — ela não some da conta."""
    raiz = maq.projeto("proj", INDEX_VAZIO,
                       historico="# Histórico\n- [login por SSO](../specs/login-sso.md) — entrar com a conta MSIG — fechada\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature login-sso", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is None


def test_nome_da_feature_e_so_a_primeira_linha(maq):
    """O prompt real (2026-09-24) tinha o comando + parágrafos de contexto. O texto todo como nome
    faria qualquer palavra do contexto casar como 'a mesma feature' — e o motivo citaria o parágrafo."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    prompt = ("/mss-spec:nova-feature Roteiro Azure Banco Produção\n"
              "Em continuação ao roteiro, o banco miti_ai_chatbot vai pro Azure; "
              "formatação da resposta no WhatsApp fica pra depois.")
    decisao, texto = maq.avaliar(_evento(prompt, raiz, sessao="c1"))
    assert decisao == "avisa", "o parágrafo de contexto fez a feature casar com outra aberta"
    assert "`Roteiro Azure Banco Produção`" in texto
    motivo = maq.decidir(_evento("/mss-spec:nova-feature miti_ai_chatbot", raiz, sessao="c1"))
    assert motivo is not None, "palavra do parágrafo casou como se fosse o nome gravado"
    assert "vai pro Azure" not in motivo, "o motivo citou o parágrafo como nome da feature do chat"


# --- revisão 0.34.0: o nome digitado não é o título que o passo 3 grava --------------------

def test_titulo_do_passo_3_contido_no_nome_digitado_liga_ao_chat(maq):
    """O passo 3 escolhe o assunto "pelo tema": o owner digita 'exportar relatório em PDF' e o INDEX
    ganha 'Exportar PDF'. Retomar pelo slug passa; fechada a linha, o chat abre a próxima."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar relatório em PDF", raiz, sessao="c1")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar o PDF — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar-pdf", raiz, sessao="c1")) is None, \
        "barrou retomar pelo slug da linha que o passo 3 gravou"
    assert maq.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1")) is not None
    maq.index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar o PDF — fechada\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1")) is None, \
        "o chat fechou a própria feature e continuou travado"


def test_nome_com_erro_de_digitacao_trava_enquanto_houver_aberta(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature cadstro de clientes", raiz, sessao="c1")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n- [cadastro de clientes](../specs/cadastro-clientes.md) — tela — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is not None
    maq.index(raiz, "# Índice\n## Em andamento\n- [cadastro de clientes](../specs/cadastro-clientes.md) — tela — pausada: layout\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is None


def test_linha_nova_do_backlog_nao_prende_o_chat(maq):
    """to-dolist no meio da feature grava `aberta` no Backlog — isso não é a feature do chat."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar relatório em PDF", raiz, sessao="c1")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar — fechada\n"
                    "## Backlog\n- tratar erro do n8n — mensagem genérica — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1")) is None


def test_v1_fechada_nao_encerra_a_v2_aberta(maq):
    raiz = maq.projeto("proj", "# Índice\n## Em andamento\n- busca vetorial v2 — reindexar — aberta\n",
                       historico="# Histórico\n- busca vetorial — primeira versão — fechada\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature busca vetorial v2", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is not None, \
        "a v1 fechada no histórico encerrou a v2 aberta — F-022 passou"


def test_v1_fechada_que_casa_melhor_nao_encerra_a_linha_aberta_do_chat(maq):
    """3ª revisão: evoluir feature já fechada. O chat abre 'busca vetorial' (= nome exato da v1
    fechada) e o passo 3 grava 'busca vetorial hibrida' aberta — a v1 casar melhor não encerra nada."""
    raiz = maq.projeto("proj", INDEX_VAZIO,
                       historico="# Histórico\n- [busca vetorial](../specs/busca-vetorial.md) — v1 — fechada\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature busca vetorial", raiz, sessao="c1")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n"
                    "- [busca vetorial hibrida](../specs/busca-vetorial-hibrida.md) — BM25 + vetor — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is not None, \
        "a v1 fechada encerrou a linha aberta do próprio chat — F-022 passou"


def test_nome_curto_fechado_nao_encerra_por_pedaco_de_palavra(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO, historico="# Histórico\n- [UI](../specs/ui.md) — tema escuro — fechada\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature guia do usuário", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is not None, \
        "'ui' dentro de 'guia' encerrou a feature do chat"


def test_linha_de_terceiro_nao_vira_ponte_entre_assuntos(maq):
    raiz = maq.projeto("proj", "# Índice\n## Em andamento\n- [API](../specs/api.md) — contrato — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature rapido cadastro", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature api de pagamentos", raiz, sessao="c1")) is not None, \
        "'rápido cadastro' e 'api de pagamentos' viraram a mesma feature pela linha API"


def test_comando_sem_nome_na_mesma_linha_nao_grava_o_paragrafo(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO)
    prompt = "/mss-spec:nova-feature\n\nPreciso levar o banco pro Azure e ajustar o roteiro"
    assert maq.decidir(_evento(prompt, raiz, sessao="c1")) is None
    assert not maq.gravou, "a 1ª frase do contexto virou nome de feature"


INDEX_DOIS_CHATS = ("# Índice\n## Em andamento\n"
                    "- [Login SSO](../specs/login-sso.md) — entrar com a conta MSIG — {login}\n"
                    "- [Exportar CSV](../specs/exportar-csv.md) — planilha do mês — aberta\n")


def test_linha_de_outro_chat_nao_vira_do_chat(maq):
    """2ª revisão: o chat A abriu 'entrar com a conta da empresa' e o passo 3 gravou 'Login SSO'
    (nenhuma palavra em comum); o chat B abriu 'Exportar CSV' na mesma pasta. Linha nova no INDEX não
    diz de qual chat é — o A não pode assumir a do B."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature entrar com a conta da empresa", raiz, sessao="A")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="B")) is None
    maq.index(raiz, INDEX_DOIS_CHATS.format(login="aberta"))
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="A")) is not None, \
        "o chat A 'retomou' a feature do chat B — F-022 pela linha do vizinho"


def test_nome_sem_linha_com_outra_aberta_bloqueia_e_manda_chat_novo(maq):
    """Custo aceito e declarado: o nome digitado não casa com linha nenhuma e há feature aberta (de
    outro chat) → o hook não sabe se a do chat fechou; bloqueia dizendo isso e dando as saídas."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature entrar com a conta da empresa", raiz, sessao="A")) is None
    maq.index(raiz, INDEX_DOIS_CHATS.format(login="fechada"))
    motivo = maq.decidir(_evento("/mss-spec:nova-feature relatorio mensal", raiz, sessao="A"))
    assert motivo is not None
    assert "não achei" in motivo.lower() and "chat novo" in motivo.lower(), \
        "bloqueio sem dizer que a linha não foi achada — o owner vê 'ainda aberta' sobre o que acabou de fechar"
    assert "ainda aberta" not in motivo
    assert "/mss-spec:nova-feature entrar com a conta da empresa" in motivo, "sem o comando exato pra continuar"


def test_nome_sem_linha_e_nada_aberto_libera(maq):
    """Sem nenhuma feature aberta no INDEX, a do chat não pode estar aberta — seja qual for o título."""
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n- [Painel de SLA](../specs/painel-sla.md) — prazos — fechada\n"
                    "- Movido para [ASSUNTOS-EXISTENTES.md](ASSUNTOS-EXISTENTES.md) em 2026-09-25 — ponteiro\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="A")) is None, \
        "linha sem status (ponteiro do rodízio) ou título que subiu do backlog prendeu o chat"


def test_retomar_pelo_nome_digitado_sempre_passa(maq):
    raiz = maq.projeto("proj", "# Índice\n## Backlog\n- [Painel de SLA](../specs/painel-sla.md) — prazos — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A")) is None
    maq.index(raiz, "# Índice\n## Em andamento\n- [Painel de SLA](../specs/painel-sla.md) — prazos — aberta\n")
    assert maq.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A")) is None


def test_voltar_ao_projeto_anterior_mantem_a_trava_dele(maq):
    a = maq.projeto("a", INDEX_VAZIO)
    b = maq.projeto("b", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature primeira", a, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature segunda", b, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature terceira", a, sessao="c1")) is not None, \
        "passar pelo projeto B apagou a trava do chat no A"


def test_retomar_renova_a_validade(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    for reg in maq.estado.values():
        reg["quando"] = "2026-11-01T00:00:00"
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    assert all(r["quando"] == AGORA.isoformat(timespec="seconds") for r in maq.estado.values()), \
        "retomar não renovou a data — feature longa perde a trava aos 30 dias"


def test_sem_argumento_passa(maq):
    """`/mss-spec:nova-feature` sem nome não tem o que comparar — passa, sem gravar."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1")) is None


def test_so_age_no_comando_de_abrir_feature(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1")) is None
    for texto in ("como está o INDEX?", "/mss-spec:mapa", "/mss-spec:to-dolist adicionar x",
                  "vamos falar da nova-feature depois", "/mss-spec:diagnostico 400 na Blip"):
        assert maq.decidir(_evento(texto, raiz, sessao="c1")) is None, f"agiu fora do comando: {texto!r}"


def test_aceita_forma_curta_do_comando(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/nova-feature login por SSO", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/nova-feature exportar CSV", raiz, sessao="c1")) is not None


def test_projeto_sem_index_passa(maq):
    raiz = maq.projeto("proj")
    assert maq.decidir(_evento("/mss-spec:nova-feature x", raiz, sessao="c1")) is None


def test_mesmo_chat_em_outro_projeto_nao_herda(maq):
    a = maq.projeto("a", INDEX_VAZIO)
    b = maq.projeto("b", INDEX_VAZIO)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", a, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", b, sessao="c1")) is None


def test_escape_do_owner(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature primeira", raiz, sessao="c1")) is None
    assert maq.decidir(_evento("/mss-spec:nova-feature segunda", raiz, sessao="c1"), {"MSS_UM_ITEM_OFF": "1"}) is None


def test_entrada_malformada_libera(maq):
    assert maq.decidir({}) is None
    assert maq.decidir({"prompt": "/mss-spec:nova-feature x"}) is None  # sem cwd
    assert maq.decidir({"prompt": None, "cwd": "."}) is None


def test_sem_session_id_passa_sem_gravar(maq):
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    assert maq.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz)) is None
    assert not maq.gravou


def test_estado_descarta_chat_com_mais_de_30_dias(maq):
    raiz = maq.projeto("proj", INDEX_VAZIO)
    maq.estado = {"velho": {"projeto": "x", "feature": "y", "quando": "2020-01-01T00:00:00"}}
    assert maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c2")) is None
    assert "velho" not in maq.estado and any(k.startswith("c2|") for k in maq.estado)


def test_saida_pelos_protocolos(mod):
    """Bloqueio: JSON `decision: block` + stderr (o que o owner vê no terminal) + exit 2. Aviso: no app Desktop
    o `systemMessage` não aparece — o `additionalContext` faz o assistente abrir a resposta com ele (mesmo
    protocolo do `alerta_contexto.py`). Libera: calado."""
    saida, erro, codigo = mod.saida("bloqueia", "motivo: login por SSO")
    assert codigo == 2 and erro == "motivo: login por SSO"
    assert json.loads(saida) == {"decision": "block", "reason": "motivo: login por SSO"}
    saida, erro, codigo = mod.saida("avisa", "aviso: pergunte ao owner")
    assert codigo == 0 and erro is None
    aviso = json.loads(saida)
    assert aviso["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "pergunte ao owner" in aviso["hookSpecificOutput"]["additionalContext"].lower()
    assert aviso["systemMessage"] == "aviso: pergunte ao owner"
    assert "decision" not in aviso, "aviso não pode bloquear"
    assert mod.saida("libera", None) == (None, None, 0)


# --- o disco de verdade: a casca lê o INDEX e lê e grava o estado (pasta montada uma vez) -----------

@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("um_item")
    raiz = base / "proj"
    (raiz / "docs" / "superpowers").mkdir(parents=True)
    (raiz / "docs" / "superpowers" / "INDEX.md").write_text(INDEX_COM_ABERTA, encoding="utf-8")
    (raiz / "docs" / "superpowers" / "INDEX-historico.md").write_text(
        "# Histórico\n- [login por SSO](../specs/login-sso.md) — entrar com a conta MSIG — fechada\n", encoding="utf-8")
    return raiz, base / "estado.json"


def test_casca_le_o_index_e_le_e_grava_o_estado(mod, pasta):
    raiz, estado = pasta
    amb = {"MSS_UM_ITEM_ESTADO": str(estado)}
    estado.write_text("{não é json", encoding="utf-8")                      # ilegível → libera e se refaz
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is None
    assert any(k.startswith("c1|") for k in json.loads(estado.read_text(encoding="utf-8")))
    assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1"), amb) is not None, \
        "o estado gravado no disco não foi lido de volta"
    # o INDEX-historico do disco: a fechada de lá encerra a feature do chat
    assert mod.decidir(_evento("/mss-spec:nova-feature login-sso", raiz, sessao="c2"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c2"), amb) is None
    assert [p.name for p in estado.parent.iterdir() if p.name.endswith(".tmp")] == [], "sobrou .tmp da gravação"


def test_processo_bloqueia_pelos_dois_protocolos(pasta):
    raiz, _ = pasta
    estado = raiz.parent / "estado-processo.json"
    chave = f"proc|{os.path.normcase(os.path.abspath(raiz))}"
    estado.write_text(json.dumps({chave: {"projeto": "x", "feature": "cadastro de clientes",
                                          "quando": datetime.now().isoformat(timespec="seconds")}}), encoding="utf-8")
    amb = {k: v for k, v in os.environ.items() if k != "MSS_UM_ITEM_OFF"}
    amb["MSS_UM_ITEM_ESTADO"] = str(estado)
    proc = subprocess.run([sys.executable, str(HOOK)],
                          input=json.dumps(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="proc")),
                          capture_output=True, text=True, env=amb, timeout=30)
    assert proc.returncode == 2, f"esperava exit 2; saiu {proc.returncode}: {proc.stderr}"
    saida = json.loads(proc.stdout)
    assert saida["decision"] == "block" and "cadastro de clientes" in saida["reason"]
    assert proc.stderr.strip(), "stderr vazio — é o que o owner vê no terminal"


# --- AC5: backlog não é feature aberta (caso F-030) -----------------------------------------

INDEX_COM_BACKLOG = """# Índice de tarefas

## Em andamento
- [painel qa](../specs/painel-qa.md) — fila de consolidação — em andamento

## Backlog
- nps-whatsapp — dois endpoints de NPS — aberta

### Crítico
- identidade-por-sessao — identidade global de processo — aberta

### Encontrado no código
- tratamento-erro-cotacao — erro do n8n vira mensagem genérica — aberta

## Fora de escopo — decidido NÃO fazer
- Redis para o handoff — aberta
"""

INDEX_SO_BACKLOG = """# Índice de tarefas

## Backlog
- nps-whatsapp — dois endpoints de NPS — aberta
### Crítico
- identidade-por-sessao — identidade global de processo — aberta
"""


def test_item_de_backlog_nao_conta_como_aberta(mod):
    """No Whats, 34 itens de backlog `aberta` travavam o nova-feature pra sempre — e o assistente
    passou a fazer tudo à mão, fora do ritual."""
    abertas = mod.abertas(INDEX_COM_BACKLOG)
    assert len(abertas) == 1 and "painel qa" in abertas[0], abertas


def test_subsecao_do_backlog_herda_o_backlog(mod):
    """`### Crítico` embaixo de `## Backlog` continua sendo backlog."""
    assert mod.abertas(INDEX_SO_BACKLOG) == []


def test_secao_depois_do_backlog_volta_a_contar(mod):
    texto = INDEX_SO_BACKLOG + "\n## Em andamento\n- deploy prod — publicar a main — aberta\n"
    abertas = mod.abertas(texto)
    assert len(abertas) == 1 and "deploy prod" in abertas[0]


def test_so_backlog_nao_avisa(maq):
    raiz = maq.projeto("proj", INDEX_SO_BACKLOG)
    decisao, _ = maq.avaliar(_evento("/mss-spec:nova-feature deploy-azure-prd", raiz, sessao="c1"))
    assert decisao == "libera", "backlog entrou no aviso de feature aberta"


def test_kickoff_semeia_o_backlog_na_secao_backlog():
    """O kickoff grava as necessidades como `aberta`; fora da seção Backlog elas travariam a 1ª feature."""
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "## Backlog" in kickoff, "kickoff.md não manda semear o backlog sob `## Backlog`"
    molde = (REPO / "templates" / "INDEX.md").read_text(encoding="utf-8")
    assert "## Em andamento" in molde and "## Backlog" in molde, "molde do INDEX sem as duas seções"


# --- AC4: registrado, documentado e com a 2ª camada em prosa -----------------------------

def test_hook_registrado_no_user_prompt_submit():
    cfg = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    grupos = cfg.get("UserPromptSubmit") or []
    assert any("um_item_por_janela.py" in h["command"] for g in grupos for h in g["hooks"]), \
        "um_item_por_janela.py não está registrado no UserPromptSubmit"


def test_segunda_camada_em_prosa():
    """Se o hook não disparar, o próprio comando faz o check (passo 0) e a regra do CLAUDE.md
    deixa de ser 'alerta, não trava'."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    low = nova.lower()
    assert "passo 0" in low or "**0." in nova, "nova-feature.md não tem o passo 0 (gate de feature aberta)"
    assert "aberta" in low and "index.md" in low
    assert "pausada" in low, "nova-feature.md não ensina a saída honesta (pausada: <motivo>)"
    assert "esta conversa" in low and "worktree" in low, \
        "passo 0 ainda conta por projeto — a regra é por chat (e nunca worktree)"
    assert "feature nova só quando não há feature aberta" not in low, "passo 0 com a regra antiga"
    claude = texto_do_kit()
    assert "É alerta, não trava" not in claude, "CLAUDE.md ainda trata 2º assunto como alerta"
    assert "um assunto por janela" in claude.lower()
    assert "não age" in claude.lower() or "não aja" in claude.lower(), \
        "CLAUDE.md não proíbe agir sobre o 2º assunto na janela atual"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8").lower()
    assert "um_item_por_janela.py" in readme and "mss_um_item_off" in readme
    assert "session_id" in readme and "um-item-janelas.json" in readme, "README sem a regra por chat"

# --- 0.59.0: comando do kit dentro de texto colado (caso F-053) ------------------------------------

def test_nova_feature_colado_e_enxergado(maq):
    """O pedido colado chega como `<pasted_content id="…">` + o comando: o hook tem de ver o `nova-feature`."""
    raiz = maq.projeto("proj", INDEX_COM_ABERTA)
    colado = '<pasted_content id="6303">\n/mss-spec:nova-feature login por SSO\n\ncontexto do pedido\n</pasted_content>'
    assert maq.decidir(_evento(colado, raiz, sessao="c9")) is None
    motivo = maq.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c9"))
    assert motivo is not None and "login por SSO" in motivo, \
        "o nova-feature colado não ficou registrado como a feature deste chat (F-053)"
    assert "pasted_content" not in motivo, "a marca do texto colado entrou no nome da feature"
