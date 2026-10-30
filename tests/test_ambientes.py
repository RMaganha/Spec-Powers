"""`docs/AMBIENTES.md` — um lugar só, por projeto, pra cada ambiente: o que é, como o assistente lê, quem
acessa o quê, e as variáveis com os valores (caso F-048).

Na conversa do Whats de 2026-10-30 o assistente chamou o servidor `-dev-br` de "homologação sem conferir",
passou 20 minutos sem saber se `N8N_WHATSAPP_PUSH_URL` de produção era o host certo e mandou o owner abrir o
Kudu de produção, que ele não acessa. Os nomes estavam em 4 arquivos diferentes. O owner: "deve ter um
arquivo independente que guarde as informações dos ambientes, variáveis e valores".

Propriedades:
- modelo no kit com as três seções (Local · Homologação · Produção), a tabela `Variável | Valor | Onde vive |
  Lido por / quando`, segredo `*****` e `falta preencher`;
- o kickoff copia, o upgrade cria quando falta (sem inventar valor) e não toca nos valores quando existe;
- o motor de memória trata cada seção como fonte: "qual o servidor de produção" aponta a seção Produção;
- bug, duvida e diagnostico leem a seção do ambiente citado (coberto em `test_smoke_kit.py`).
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODELO = REPO / "templates" / "AMBIENTES.md"


def _motor():
    spec = importlib.util.spec_from_file_location("memoria_indice", REPO / "templates" / "memoria_indice.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _recall():
    spec = importlib.util.spec_from_file_location("recall_memoria", REPO / "hooks" / "recall_memoria.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


AMBIENTES_WHATS = """# Ambientes — IA Bot Agent - Whats

## Local

- **O que é:** docker compose na máquina do owner; Postgres em `host.docker.internal:5432`
- **Quem acessa:** owner: sim · assistente: sim

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `PG_CONN_STR` | `*****` | `.env` | owner, 2026-10-30 |

## Homologação

- **O que é:** Web App `mss-miti-ai-agent-bot-webwhats-dev-br`; Postgres `mss-miti-ai-postgree-sv-dev-br`; branch `dev`
- **Como o assistente lê:** banco pelo túnel, chave `BANCO_HML` do `sql/.env`, só leitura
- **Quem acessa:** owner: Portal sim, Kudu sim · assistente: só leitura pelo túnel

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `MITI_DEV_AUTH` | `1` | App Setting do Web App `mss-miti-ai-agent-bot-webwhats-dev-br` | owner, 2026-10-30 |

## Produção

- **O que é:** Web App `mss-miti-ai-agent-bot-webwhats-prod` (grupo `RG-MSSAI-PRD`, restrito à infra); Postgres `mss-miti-ai-postgree-sv-prod-br`; branch `main`
- **Como o assistente lê:** banco pelo túnel, chave `BANCO_PRD` do `sql/.env`, só leitura; nunca Kudu/Portal
- **Quem acessa:** owner: Portal não, Kudu não · infra: tudo · assistente: só leitura pelo túnel

| Variável | Valor | Onde vive | Lido por / quando |
|---|---|---|---|
| `N8N_WHATSAPP_PUSH_URL` | `https://mitiai-n8n.msig.com.br/webhook/mitiai-push-especialista` | App Setting do Web App `mss-miti-ai-agent-bot-webwhats-prod` | owner, 2026-10-30 |
| `MITI_DEV_AUTH` | `0` | App Setting do Web App `mss-miti-ai-agent-bot-webwhats-prod` | owner, 2026-10-30 |
"""


def _projeto(tmp_path, com_ambientes=True):
    raiz = tmp_path / "whats"
    (raiz / "memory").mkdir(parents=True)
    (raiz / "memory" / "MEMORY.md").write_text("# topo\n", encoding="utf-8")
    (raiz / "memory" / "postgres-da-azure-so-pelo-proxy-socks.md").write_text(
        "---\nname: postgres-da-azure-so-pelo-proxy-socks\n"
        "description: o Postgres da Azure não é alcançável direto — o DBeaver chega por proxy SOCKS\n"
        "gatilho: quando o TCP 5432 pro Postgres da Azure der timeout\n---\n", encoding="utf-8")
    if com_ambientes:
        (raiz / "docs").mkdir()
        (raiz / "docs" / "AMBIENTES.md").write_text(AMBIENTES_WHATS, encoding="utf-8")
    return raiz


# --- AC1: o modelo --------------------------------------------------------------------------

def test_modelo_tem_as_tres_secoes_e_a_tabela():
    assert MODELO.exists(), "falta templates/AMBIENTES.md"
    t = MODELO.read_text(encoding="utf-8")
    for secao in ("## Local", "## Homologação", "## Produção"):
        assert secao in t, f"modelo sem a seção {secao}"
    assert "| Variável | Valor | Onde vive | Lido por / quando |" in t, "modelo sem a tabela de variáveis"
    assert "*****" in t and "falta preencher" in t, "modelo não ensina segredo (*****) e valor não conferido"
    assert "Quem acessa" in t and "Como o assistente lê" in t, "modelo sem 'quem acessa' / 'como o assistente lê'"
    assert "docs/AMBIENTE.md" in t, "modelo não aponta o AMBIENTE.md (infra) como o outro arquivo"


def test_kickoff_copia_e_upgrade_cria_sem_inventar():
    kick = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "`templates/AMBIENTES.md` → `docs/AMBIENTES.md`" in kick, "kickoff não copia o AMBIENTES.md"
    up = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    assert "docs/AMBIENTES.md" in up and "falta preencher" in up, "upgrade não cria o AMBIENTES.md sem inventar valor"
    assert "não toque nos valores" in up, "upgrade não protege os valores que o owner preencheu"


# --- AC2: o motor de memória casa a seção do ambiente ----------------------------------------

def test_pergunta_sobre_producao_aponta_a_secao_producao(tmp_path):
    mod = _motor()
    ponteiros = mod.casar(_projeto(tmp_path), "qual é o servidor do Postgres de produção e quem acessa?", limite=3)
    assert ponteiros, "nada casou"
    assert "docs/AMBIENTES.md" in ponteiros[0].ponteiro and "Produção" in ponteiros[0].ponteiro, \
        [p.ponteiro for p in ponteiros]
    assert "2 variável(is)" in ponteiros[0].ponteiro


def test_variavel_citada_aponta_o_ambiente_dela(tmp_path):
    mod = _motor()
    ponteiros = mod.casar(_projeto(tmp_path), "o valor de N8N_WHATSAPP_PUSH_URL em produção está certo?", limite=3)
    assert ponteiros and "Produção" in ponteiros[0].ponteiro, [p.ponteiro for p in ponteiros]


def test_homologacao_aponta_a_secao_dela_pela_linha(tmp_path):
    mod = _motor()
    ponteiros = mod.casar(_projeto(tmp_path), "em homologação o MITI_DEV_AUTH fica ligado no Web App?", limite=3)
    assert ponteiros and "Homologação" in ponteiros[0].ponteiro, [p.ponteiro for p in ponteiros]
    linha = int(ponteiros[0].ponteiro.split("docs/AMBIENTES.md:")[1].split(" ")[0])
    assert AMBIENTES_WHATS.split("\n")[linha - 1] == "## Homologação"


def test_pergunta_fora_do_assunto_nao_traz_ambiente(tmp_path):
    mod = _motor()
    ponteiros = mod.casar(_projeto(tmp_path), "como formatar a data brasileira no template Jinja?", limite=3)
    assert not any("AMBIENTES.md" in p.ponteiro for p in ponteiros)


def test_sem_o_arquivo_nada_muda(tmp_path):
    mod = _motor()
    assert mod.fontes_ambientes(_projeto(tmp_path, com_ambientes=False)) == []


def test_recall_injeta_a_secao(tmp_path):
    raiz = _projeto(tmp_path)
    saida = _recall().responder({"hook_event_name": "UserPromptSubmit", "cwd": str(raiz),
                                 "prompt": "qual o servidor do banco Postgres de produção e quem acessa o Portal?"}, {})
    assert saida is not None
    ctx = saida["hookSpecificOutput"]["additionalContext"]
    assert "docs/AMBIENTES.md" in ctx and "Produção" in ctx


# --- AC3: os comandos leem a seção do ambiente citado (também coberto no smoke) ---------------

def test_bug_duvida_e_diagnostico_leem_o_ambiente_citado():
    for nome in ("bug", "duvida", "diagnostico"):
        t = (REPO / "commands" / f"{nome}.md").read_text(encoding="utf-8")
        assert "docs/AMBIENTES.md" in t and "memory/DIARIO.md" in t, f"{nome}.md não lê AMBIENTES e DIARIO"


def test_doctor_confere_o_arquivo_e_o_locale_dos_hooks():
    d = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    assert "docs/AMBIENTES.md" in d and "falta preencher" in d, "doctor não confere o docs/AMBIENTES.md"
    assert "LC_ALL" in d and "appears to be missing" in d, "doctor não avisa o LC_ALL que fazia o Stop não chegar"
