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
    assert "velho" not in estado and "c2" in estado


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
