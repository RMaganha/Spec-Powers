"""Um item por janela — um chat não abre uma 2ª feature enquanto a dele estiver aberta.

Nasceu do mesmo acidente do F-022: a janela de uma feature absorveu um 2º e um 3º assunto,
misturou branches e quebrou homologação. A regra "um assunto por janela" existia como ALERTA
("é alerta, não trava") e ficou muda. Virou trava (0.26.0) — mas contando por PROJETO: com 6
features abertas em 6 chats, o chat novo não abria nada e o owner passou a tirar o comando do
prompt (2026-09-24). Desde a 0.34.0 conta por CHAT (`session_id`): o hook lembra qual feature cada
chat abriu (`~/.claude/mss-spec/um-item-janelas.json`) e só bloqueia o MESMO chat pedindo outra.

Propriedades:
- chat sem feature → passa (e grava a dele); outras abertas no INDEX → passa com AVISO (worktree);
- chat com feature Y ainda aberta pedindo X → bloqueia; Y de novo → passa (retomar não é misturar);
  Y `fechada`/`pausada` (no INDEX ou no INDEX-historico) → passa e o chat fica com X;
- só age no comando de abrir feature — qualquer outro prompt passa calado;
- projeto sem INDEX (sem o kit) → passa;
- falha ABERTA: bug/entrada malformada libera (apagar prompt do owner por bug seria pior);
- escape consciente só do owner: `MSS_UM_ITEM_OFF=1`.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "um_item_por_janela.py"

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


def _mod():
    spec = importlib.util.spec_from_file_location("um_item_por_janela", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _projeto(tmp_path, index):
    raiz = tmp_path / "proj"
    (raiz / "docs" / "superpowers").mkdir(parents=True)
    if index is not None:
        (raiz / "docs" / "superpowers" / "INDEX.md").write_text(index, encoding="utf-8")
    return raiz


def _evento(prompt, raiz, sessao=None):
    ev = {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}
    if sessao is not None:
        ev["session_id"] = sessao
    return ev


def _amb(tmp_path):
    """Estado dos chats numa pasta temporária — a suíte nunca toca o `~/.claude/mss-spec/` do owner."""
    return {"MSS_UM_ITEM_ESTADO": str(tmp_path / "um-item-janelas.json")}


# --- AC1: abertas ---------------------------------------------------------------------

def test_lista_abertas_ignora_fechada_e_pausada():
    mod = _mod()
    abertas = mod.abertas(INDEX_COM_ABERTA)
    assert len(abertas) == 1
    assert "formatação da resposta no WhatsApp" in abertas[0]


def test_em_andamento_conta_como_aberta():
    mod = _mod()
    abertas = mod.abertas(INDEX_EM_ANDAMENTO)
    assert len(abertas) == 1 and "upgrade" in abertas[0]


def test_indice_vazio_nao_tem_aberta():
    assert _mod().abertas(INDEX_VAZIO) == []


# --- AC2: decisão por chat -------------------------------------------------------------

def test_sem_aberta_passa(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    assert _mod().decidir(_evento("/mss-spec:nova-feature login por SSO", raiz), ambiente={}) is None


def test_chat_novo_passa_mesmo_com_outra_aberta(tmp_path):
    """O caso de 2026-09-24: 6 abertas em outros chats e o chat NOVO não abria nada."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    ev = _evento("/mss-spec:nova-feature login por SSO", raiz, sessao="chat-novo")
    assert _mod().decidir(ev, ambiente=_amb(tmp_path)) is None, "chat novo bloqueado — a regra é por chat"


def test_chat_novo_com_outra_aberta_avisa_e_lembra_worktree(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    decisao, texto = _mod().avaliar(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"),
                                    ambiente=_amb(tmp_path))
    assert decisao == "avisa"
    assert "formatação da resposta no WhatsApp" in texto, "aviso não lista a outra aberta"
    assert "relatório mensal" not in texto, "listou feature fechada como aberta"
    assert "worktree" in texto.lower(), "aviso não lembra do worktree (duas features na mesma pasta)"
    assert "pausada" in texto.lower(), "aviso não ensina a limpar linha parada (pausada: <motivo>)"


def test_mesmo_chat_pedindo_outra_bloqueia(tmp_path):
    """O F-022 de verdade: a janela de uma feature absorvendo um 2º assunto."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    motivo = mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb)
    assert motivo is not None, "o mesmo chat abriu uma 2ª feature — a trava não travou"
    assert "login por SSO" in motivo, "motivo não diz de qual feature este chat já é"
    assert "chat novo" in motivo.lower(), "motivo não manda abrir um chat novo"
    assert "pausada" in motivo.lower() and "janela" in motivo.lower()


def test_outro_chat_nao_herda_a_trava(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c2"), amb) is None


def test_mesma_feature_retoma(tmp_path):
    """Retomar a feature do chat não é misturar — passa, inclusive com grafia diferente."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature formatação da resposta no WhatsApp", raiz,
                               sessao="c1"), amb) is None
    for texto in ("/mss-spec:nova-feature formatação da resposta no WhatsApp",
                  "/mss-spec:nova-feature formatacao-resposta-whatsapp",
                  "/mss-spec:nova-feature Formatação da Resposta no whatsapp — continuar"):
        assert mod.decidir(_evento(texto, raiz, sessao="c1"), amb) is None, f"barrou retomar: {texto!r}"


def test_retomar_nao_avisa_da_propria_feature(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    decisao, _ = _mod().avaliar(_evento("/mss-spec:nova-feature formatacao-resposta-whatsapp", raiz,
                                        sessao="c1"), ambiente=_amb(tmp_path))
    assert decisao == "libera", "avisou que a própria feature está aberta"


def test_feature_do_chat_fora_do_index_segue_valendo(tmp_path):
    """A linha do INDEX só nasce no passo 3 do nova-feature — antes disso a feature do chat vale."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None


def test_feature_do_chat_encerrada_libera_a_proxima(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    for encerrada in ("relatório mensal", "importador-apolices"):       # fechada · pausada
        sessao = f"c-{encerrada}"
        assert mod.decidir(_evento(f"/mss-spec:nova-feature {encerrada}", raiz, sessao=sessao), amb) is None
        assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao=sessao), amb) is None, \
            f"{encerrada} já saiu de aberta e o chat não pôde abrir a próxima"
        assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao=sessao), amb) is not None, \
            "o chat não passou a ser da feature nova"


def test_fechada_movida_pro_historico_libera_a_proxima(tmp_path):
    """O rodízio move a linha `fechada` pro INDEX-historico.md — ela não some da conta."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    (raiz / "docs" / "superpowers" / "INDEX-historico.md").write_text(
        "# Histórico\n- [login por SSO](../specs/login-sso.md) — entrar com a conta MSIG — fechada\n",
        encoding="utf-8")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login-sso", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is None


def test_nome_da_feature_e_so_a_primeira_linha(tmp_path):
    """O prompt real (2026-09-24) tinha o comando + parágrafos de contexto. O texto todo como nome
    faria qualquer palavra do contexto casar como 'a mesma feature' — e o motivo citaria o parágrafo."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    prompt = ("/mss-spec:nova-feature Roteiro Azure Banco Produção\n"
              "Em continuação ao roteiro, o banco miti_ai_chatbot vai pro Azure; "
              "formatação da resposta no WhatsApp fica pra depois.")
    decisao, texto = mod.avaliar(_evento(prompt, raiz, sessao="c1"), ambiente=amb)
    assert decisao == "avisa", "o parágrafo de contexto fez a feature casar com outra aberta"
    assert "`Roteiro Azure Banco Produção`" in texto
    motivo = mod.decidir(_evento("/mss-spec:nova-feature miti_ai_chatbot", raiz, sessao="c1"), amb)
    assert motivo is not None, "palavra do parágrafo casou como se fosse o nome gravado"
    assert "vai pro Azure" not in motivo, "o motivo citou o parágrafo como nome da feature do chat"


# --- revisão 0.34.0: o nome digitado não é o título que o passo 3 grava --------------------

def _index(raiz, texto):
    (raiz / "docs" / "superpowers" / "INDEX.md").write_text(texto, encoding="utf-8")


def _historico(raiz, texto):
    (raiz / "docs" / "superpowers" / "INDEX-historico.md").write_text(texto, encoding="utf-8")


def test_titulo_do_passo_3_contido_no_nome_digitado_liga_ao_chat(tmp_path):
    """O passo 3 escolhe o assunto "pelo tema": o owner digita 'exportar relatório em PDF' e o INDEX
    ganha 'Exportar PDF'. Retomar pelo slug passa; fechada a linha, o chat abre a próxima."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar relatório em PDF", raiz, sessao="c1"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar o PDF — aberta\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar-pdf", raiz, sessao="c1"), amb) is None, \
        "barrou retomar pelo slug da linha que o passo 3 gravou"
    assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1"), amb) is not None
    _index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar o PDF — fechada\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1"), amb) is None, \
        "o chat fechou a própria feature e continuou travado"


def test_nome_com_erro_de_digitacao_trava_enquanto_houver_aberta(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature cadstro de clientes", raiz, sessao="c1"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n- [cadastro de clientes](../specs/cadastro-clientes.md) — tela — aberta\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None
    _index(raiz, "# Índice\n## Em andamento\n- [cadastro de clientes](../specs/cadastro-clientes.md) — tela — pausada: layout\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is None


def test_linha_nova_do_backlog_nao_prende_o_chat(tmp_path):
    """to-dolist no meio da feature grava `aberta` no Backlog — isso não é a feature do chat."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar relatório em PDF", raiz, sessao="c1"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n- [Exportar PDF](../specs/exportar-pdf.md) — gerar — fechada\n"
                 "## Backlog\n- tratar erro do n8n — mensagem genérica — aberta\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="c1"), amb) is None


def test_v1_fechada_nao_encerra_a_v2_aberta(tmp_path):
    raiz = _projeto(tmp_path, "# Índice\n## Em andamento\n- busca vetorial v2 — reindexar — aberta\n")
    _historico(raiz, "# Histórico\n- busca vetorial — primeira versão — fechada\n")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature busca vetorial v2", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None, \
        "a v1 fechada no histórico encerrou a v2 aberta — F-022 passou"


def test_v1_fechada_que_casa_melhor_nao_encerra_a_linha_aberta_do_chat(tmp_path):
    """3ª revisão: evoluir feature já fechada. O chat abre 'busca vetorial' (= nome exato da v1
    fechada) e o passo 3 grava 'busca vetorial hibrida' aberta — a v1 casar melhor não encerra nada."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    _historico(raiz, "# Histórico\n- [busca vetorial](../specs/busca-vetorial.md) — v1 — fechada\n")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature busca vetorial", raiz, sessao="c1"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n"
                 "- [busca vetorial hibrida](../specs/busca-vetorial-hibrida.md) — BM25 + vetor — aberta\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None, \
        "a v1 fechada encerrou a linha aberta do próprio chat — F-022 passou"


def test_nome_curto_fechado_nao_encerra_por_pedaco_de_palavra(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    _historico(raiz, "# Histórico\n- [UI](../specs/ui.md) — tema escuro — fechada\n")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature guia do usuário", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None, \
        "'ui' dentro de 'guia' encerrou a feature do chat"


def test_linha_de_terceiro_nao_vira_ponte_entre_assuntos(tmp_path):
    raiz = _projeto(tmp_path, "# Índice\n## Em andamento\n- [API](../specs/api.md) — contrato — aberta\n")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature rapido cadastro", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature api de pagamentos", raiz, sessao="c1"), amb) is not None, \
        "'rápido cadastro' e 'api de pagamentos' viraram a mesma feature pela linha API"


def test_comando_sem_nome_na_mesma_linha_nao_grava_o_paragrafo(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    prompt = "/mss-spec:nova-feature\n\nPreciso levar o banco pro Azure e ajustar o roteiro"
    assert mod.decidir(_evento(prompt, raiz, sessao="c1"), amb) is None
    assert not Path(amb["MSS_UM_ITEM_ESTADO"]).exists(), "a 1ª frase do contexto virou nome de feature"


INDEX_DOIS_CHATS = ("# Índice\n## Em andamento\n"
                    "- [Login SSO](../specs/login-sso.md) — entrar com a conta MSIG — {login}\n"
                    "- [Exportar CSV](../specs/exportar-csv.md) — planilha do mês — aberta\n")


def test_linha_de_outro_chat_nao_vira_do_chat(tmp_path):
    """2ª revisão: o chat A abriu 'entrar com a conta da empresa' e o passo 3 gravou 'Login SSO'
    (nenhuma palavra em comum); o chat B abriu 'Exportar CSV' na mesma pasta. Linha nova no INDEX não
    diz de qual chat é — o A não pode assumir a do B."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature entrar com a conta da empresa", raiz, sessao="A"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="B"), amb) is None
    _index(raiz, INDEX_DOIS_CHATS.format(login="aberta"))
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="A"), amb) is not None, \
        "o chat A 'retomou' a feature do chat B — F-022 pela linha do vizinho"


def test_nome_sem_linha_com_outra_aberta_bloqueia_e_manda_chat_novo(tmp_path):
    """Custo aceito e declarado: o nome digitado não casa com linha nenhuma e há feature aberta (de
    outro chat) → o hook não sabe se a do chat fechou; bloqueia dizendo isso e dando as saídas."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature entrar com a conta da empresa", raiz, sessao="A"), amb) is None
    _index(raiz, INDEX_DOIS_CHATS.format(login="fechada"))
    motivo = mod.decidir(_evento("/mss-spec:nova-feature relatorio mensal", raiz, sessao="A"), amb)
    assert motivo is not None
    assert "não achei" in motivo.lower() and "chat novo" in motivo.lower(), \
        "bloqueio sem dizer que a linha não foi achada — o owner vê 'ainda aberta' sobre o que acabou de fechar"
    assert "ainda aberta" not in motivo
    assert "/mss-spec:nova-feature entrar com a conta da empresa" in motivo, "sem o comando exato pra continuar"


def test_nome_sem_linha_e_nada_aberto_libera(tmp_path):
    """Sem nenhuma feature aberta no INDEX, a do chat não pode estar aberta — seja qual for o título."""
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n- [Painel de SLA](../specs/painel-sla.md) — prazos — fechada\n"
                 "- Movido para [ASSUNTOS-EXISTENTES.md](ASSUNTOS-EXISTENTES.md) em 2026-09-25 — ponteiro\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature outra coisa", raiz, sessao="A"), amb) is None, \
        "linha sem status (ponteiro do rodízio) ou título que subiu do backlog prendeu o chat"


def test_retomar_pelo_nome_digitado_sempre_passa(tmp_path):
    raiz = _projeto(tmp_path, "# Índice\n## Backlog\n- [Painel de SLA](../specs/painel-sla.md) — prazos — aberta\n")
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A"), amb) is None
    _index(raiz, "# Índice\n## Em andamento\n- [Painel de SLA](../specs/painel-sla.md) — prazos — aberta\n")
    assert mod.decidir(_evento("/mss-spec:nova-feature dashboard de atrasos", raiz, sessao="A"), amb) is None


def test_voltar_ao_projeto_anterior_mantem_a_trava_dele(tmp_path):
    a = _projeto(tmp_path / "a", INDEX_VAZIO)
    b = _projeto(tmp_path / "b", INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature primeira", a, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature segunda", b, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature terceira", a, sessao="c1"), amb) is not None, \
        "passar pelo projeto B apagou a trava do chat no A"


def test_retomar_renova_a_validade(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    caminho = Path(amb["MSS_UM_ITEM_ESTADO"])
    estado = json.loads(caminho.read_text(encoding="utf-8"))
    for reg in estado.values():
        reg["quando"] = "2026-01-01T00:00:00"
    caminho.write_text(json.dumps(estado), encoding="utf-8")
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    assert all(r["quando"] > "2026-01-02" for r in json.loads(caminho.read_text(encoding="utf-8")).values()), \
        "retomar não renovou a data — feature longa perde a trava aos 30 dias"


def test_sem_argumento_passa(tmp_path):
    """`/mss-spec:nova-feature` sem nome não tem o que comparar — passa, sem gravar."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is None


def test_so_age_no_comando_de_abrir_feature(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    for texto in ("como está o INDEX?", "/mss-spec:mapa", "/mss-spec:to-dolist adicionar x",
                  "vamos falar da nova-feature depois", "/mss-spec:diagnostico 400 na Blip"):
        assert mod.decidir(_evento(texto, raiz, sessao="c1"), amb) is None, f"agiu fora do comando: {texto!r}"


def test_aceita_forma_curta_do_comando(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None


def test_projeto_sem_index_passa(tmp_path):
    raiz = _projeto(tmp_path, None)
    assert _mod().decidir(_evento("/mss-spec:nova-feature x", raiz, sessao="c1"), _amb(tmp_path)) is None


def test_mesmo_chat_em_outro_projeto_nao_herda(tmp_path):
    a = _projeto(tmp_path / "a", INDEX_VAZIO)
    b = _projeto(tmp_path / "b", INDEX_VAZIO)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", a, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", b, sessao="c1"), amb) is None


def test_escape_do_owner(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod, amb = _mod(), _amb(tmp_path)
    assert mod.decidir(_evento("/mss-spec:nova-feature primeira", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature segunda", raiz, sessao="c1"),
                       ambiente={**amb, "MSS_UM_ITEM_OFF": "1"}) is None


def test_entrada_malformada_libera():
    mod = _mod()
    assert mod.decidir({}, ambiente={}) is None
    assert mod.decidir({"prompt": "/mss-spec:nova-feature x"}, ambiente={}) is None  # sem cwd
    assert mod.decidir({"prompt": None, "cwd": "."}, ambiente={}) is None


def test_estado_corrompido_libera_e_se_refaz(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    amb = _amb(tmp_path)
    Path(amb["MSS_UM_ITEM_ESTADO"]).write_text("{não é json", encoding="utf-8")
    mod = _mod()
    assert mod.decidir(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), amb) is None
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), amb) is not None


def test_sem_session_id_passa_sem_gravar(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    amb = _amb(tmp_path)
    assert _mod().decidir(_evento("/mss-spec:nova-feature login por SSO", raiz), amb) is None
    assert not Path(amb["MSS_UM_ITEM_ESTADO"]).exists()


def test_estado_descarta_chat_com_mais_de_30_dias(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    amb = _amb(tmp_path)
    mod = _mod()
    Path(amb["MSS_UM_ITEM_ESTADO"]).write_text(json.dumps({
        "velho": {"projeto": "x", "feature": "y", "quando": "2020-01-01T00:00:00"},
    }), encoding="utf-8")
    assert mod.decidir(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c2"), amb) is None
    estado = json.loads(Path(amb["MSS_UM_ITEM_ESTADO"]).read_text(encoding="utf-8"))
    assert "velho" not in estado and any(k.startswith("c2|") for k in estado)


# --- AC3: protocolo de processo --------------------------------------------------------

def _rodar(evento, raw=None, estado=None):
    amb = {k: v for k, v in os.environ.items() if k not in ("MSS_UM_ITEM_OFF", "MSS_UM_ITEM_ESTADO")}
    if estado is not None:
        amb["MSS_UM_ITEM_ESTADO"] = str(estado)
    return subprocess.run([sys.executable, str(HOOK)],
                          input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=30)


def test_processo_bloqueia_pelos_dois_protocolos(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    estado = tmp_path / "estado.json"
    primeiro = _rodar(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"), estado=estado)
    assert primeiro.returncode == 0, primeiro.stderr
    proc = _rodar(_evento("/mss-spec:nova-feature exportar CSV", raiz, sessao="c1"), estado=estado)
    assert proc.returncode == 2, f"esperava exit 2; saiu {proc.returncode}: {proc.stderr}"
    saida = json.loads(proc.stdout)
    assert saida["decision"] == "block"
    assert "login por SSO" in saida["reason"]
    assert proc.stderr.strip(), "stderr vazio — é o que o owner vê no terminal"


def test_processo_avisa_pro_assistente_e_pro_terminal(tmp_path):
    """No app Desktop o `systemMessage` não aparece — o `additionalContext` faz o assistente abrir a
    resposta com o aviso (mesmo protocolo do `alerta_contexto.py`)."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    proc = _rodar(_evento("/mss-spec:nova-feature login por SSO", raiz, sessao="c1"),
                  estado=tmp_path / "estado.json")
    assert proc.returncode == 0, proc.stderr
    saida = json.loads(proc.stdout)
    assert saida["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "worktree" in saida["hookSpecificOutput"]["additionalContext"].lower()
    assert "formatação da resposta no WhatsApp" in saida["systemMessage"]
    assert "decision" not in saida, "aviso não pode bloquear"


def test_processo_libera_silencioso(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    proc = _rodar(_evento("/mss-spec:nova-feature x", raiz, sessao="c1"), estado=tmp_path / "estado.json")
    assert proc.returncode == 0 and proc.stdout.strip() == "" and proc.stderr.strip() == ""


def test_processo_entrada_malformada_libera():
    proc = _rodar(None, raw="não é json")
    assert proc.returncode == 0


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


def test_item_de_backlog_nao_conta_como_aberta():
    """No Whats, 34 itens de backlog `aberta` travavam o nova-feature pra sempre — e o assistente
    passou a fazer tudo à mão, fora do ritual."""
    abertas = _mod().abertas(INDEX_COM_BACKLOG)
    assert len(abertas) == 1 and "painel qa" in abertas[0], abertas


def test_subsecao_do_backlog_herda_o_backlog():
    """`### Crítico` embaixo de `## Backlog` continua sendo backlog."""
    assert _mod().abertas(INDEX_SO_BACKLOG) == []


def test_secao_depois_do_backlog_volta_a_contar():
    texto = INDEX_SO_BACKLOG + "\n## Em andamento\n- deploy prod — publicar a main — aberta\n"
    abertas = _mod().abertas(texto)
    assert len(abertas) == 1 and "deploy prod" in abertas[0]


def test_so_backlog_nao_avisa(tmp_path):
    raiz = _projeto(tmp_path, INDEX_SO_BACKLOG)
    decisao, _ = _mod().avaliar(_evento("/mss-spec:nova-feature deploy-azure-prd", raiz, sessao="c1"),
                                ambiente=_amb(tmp_path))
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
        "passo 0 ainda conta por projeto — a regra é por chat, com aviso de worktree"
    assert "feature nova só quando não há feature aberta" not in low, "passo 0 com a regra antiga"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "É alerta, não trava" not in claude, "CLAUDE.md ainda trata 2º assunto como alerta"
    assert "um assunto por janela" in claude.lower()
    assert "não age" in claude.lower() or "não aja" in claude.lower(), \
        "CLAUDE.md não proíbe agir sobre o 2º assunto na janela atual"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8").lower()
    assert "um_item_por_janela.py" in readme and "mss_um_item_off" in readme
    assert "session_id" in readme and "um-item-janelas.json" in readme, "README sem a regra por chat"
