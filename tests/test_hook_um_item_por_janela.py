"""Um item por janela — `/mss-spec:nova-feature` só abre quando NÃO há feature aberta.

Nasceu do mesmo acidente do F-022: a janela de uma feature absorveu um 2º e um 3º assunto,
misturou branches e quebrou homologação. A regra "um assunto por janela" existia como ALERTA
("é alerta, não trava") e ficou muda. Agora é trava: hook UserPromptSubmit lê o
`docs/superpowers/INDEX.md` do projeto e BLOQUEIA o prompt que abre feature nova enquanto
houver linha `aberta`/`em andamento` de OUTRO assunto.

Propriedades:
- nenhuma aberta → passa; outra aberta → bloqueia listando-as; a MESMA aberta → passa (retomar
  não é misturar); `pausada`/`fechada` não contam como abertas;
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


def _evento(prompt, raiz):
    return {"hook_event_name": "UserPromptSubmit", "cwd": str(raiz), "prompt": prompt}


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


# --- AC2: decisão ---------------------------------------------------------------------

def test_sem_aberta_passa(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    assert _mod().decidir(_evento("/mss-spec:nova-feature login por SSO", raiz), ambiente={}) is None


def test_outra_aberta_bloqueia_e_lista(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    motivo = _mod().decidir(_evento("/mss-spec:nova-feature login por SSO", raiz), ambiente={})
    assert motivo is not None, "abriu feature nova com outra aberta — a trava não travou"
    assert "formatação da resposta no WhatsApp" in motivo, "motivo não lista a feature aberta"
    assert "relatório mensal" not in motivo, "listou feature fechada como aberta"
    assert "pausada" in motivo.lower(), "motivo não ensina a saída honesta (marcar pausada à mão)"
    assert "janela" in motivo.lower()


def test_mesma_feature_retoma(tmp_path):
    """Retomar a feature aberta não é misturar — passa, inclusive com grafia diferente."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod = _mod()
    for texto in ("/mss-spec:nova-feature formatação da resposta no WhatsApp",
                  "/mss-spec:nova-feature formatacao-resposta-whatsapp",
                  "/mss-spec:nova-feature Formatação da Resposta no whatsapp — continuar"):
        assert mod.decidir(_evento(texto, raiz), ambiente={}) is None, f"barrou retomar: {texto!r}"


def test_sem_argumento_com_aberta_bloqueia(tmp_path):
    """`/mss-spec:nova-feature` sem nome, com uma aberta: ambíguo → bloqueia e pede o nome."""
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    motivo = _mod().decidir(_evento("/mss-spec:nova-feature", raiz), ambiente={})
    assert motivo is not None


def test_so_age_no_comando_de_abrir_feature(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    mod = _mod()
    for texto in ("como está o INDEX?", "/mss-spec:mapa", "/mss-spec:to-dolist adicionar x",
                  "vamos falar da nova-feature depois", "/mss-spec:diagnostico 400 na Blip"):
        assert mod.decidir(_evento(texto, raiz), ambiente={}) is None, f"agiu fora do comando: {texto!r}"


def test_aceita_forma_curta_do_comando(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    assert _mod().decidir(_evento("/nova-feature login por SSO", raiz), ambiente={}) is not None


def test_projeto_sem_index_passa(tmp_path):
    raiz = _projeto(tmp_path, None)
    assert _mod().decidir(_evento("/mss-spec:nova-feature x", raiz), ambiente={}) is None


def test_escape_do_owner(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    assert _mod().decidir(_evento("/mss-spec:nova-feature x", raiz),
                          ambiente={"MSS_UM_ITEM_OFF": "1"}) is None


def test_entrada_malformada_libera():
    mod = _mod()
    assert mod.decidir({}, ambiente={}) is None
    assert mod.decidir({"prompt": "/mss-spec:nova-feature x"}, ambiente={}) is None  # sem cwd
    assert mod.decidir({"prompt": None, "cwd": "."}, ambiente={}) is None


# --- AC3: protocolo de processo --------------------------------------------------------

def _rodar(evento, raw=None):
    amb = {k: v for k, v in os.environ.items() if k != "MSS_UM_ITEM_OFF"}
    return subprocess.run([sys.executable, str(HOOK)],
                          input=raw if raw is not None else json.dumps(evento),
                          capture_output=True, text=True, env=amb, timeout=30)


def test_processo_bloqueia_pelos_dois_protocolos(tmp_path):
    raiz = _projeto(tmp_path, INDEX_COM_ABERTA)
    proc = _rodar(_evento("/mss-spec:nova-feature login por SSO", raiz))
    assert proc.returncode == 2, f"esperava exit 2; saiu {proc.returncode}: {proc.stderr}"
    saida = json.loads(proc.stdout)
    assert saida["decision"] == "block"
    assert "formatação da resposta no WhatsApp" in saida["reason"]
    assert proc.stderr.strip(), "stderr vazio — é o que o owner vê no terminal"


def test_processo_libera_silencioso(tmp_path):
    raiz = _projeto(tmp_path, INDEX_VAZIO)
    proc = _rodar(_evento("/mss-spec:nova-feature x", raiz))
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


def test_so_backlog_libera_a_feature_nova(tmp_path):
    raiz = _projeto(tmp_path, INDEX_SO_BACKLOG)
    assert _mod().decidir(_evento("/mss-spec:nova-feature deploy-azure-prd", raiz), {}) is None


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
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "É alerta, não trava" not in claude, "CLAUDE.md ainda trata 2º assunto como alerta"
    assert "um assunto por janela" in claude.lower()
    assert "não age" in claude.lower() or "não aja" in claude.lower(), \
        "CLAUDE.md não proíbe agir sobre o 2º assunto na janela atual"
    readme = (REPO / "hooks" / "README.md").read_text(encoding="utf-8").lower()
    assert "um_item_por_janela.py" in readme and "mss_um_item_off" in readme
