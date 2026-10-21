"""Variáveis de ambiente (App Settings) da homologação levadas pra produção — /mss-spec:azure-ambiente.

O owner exigiu: TODAS as variáveis da homologação vão; senha/chave vai como `*****`; nenhuma pode ficar
pra trás calada. E a receita não pode apagar a senha verdadeira que o prestador colocou em produção numa
2ª execução do pipeline. O `templates/azure-ambiente/app_settings.py` resolve isso fora do Bicep (no Bicep,
`appSettings` substitui a coleção inteira), lendo os valores na hora e gravando por mescla.
Spec: docs/specs/azure-ambiente.md.
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "azure-ambiente" / "app_settings.py"


def _mod():
    spec = importlib.util.spec_from_file_location("app_settings", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HML = {"TZ": "America/Sao_Paulo", "DB_PASSWORD": "segredo-hml", "API_URL": "https://hml.x",
       "DOCKER_REGISTRY_SERVER_PASSWORD": "acr-pwd"}
CONFIG = {"TZ": "copiar", "DB_PASSWORD": "senha", "API_URL": {"prd": "https://prd.x"},
          "DOCKER_REGISTRY_SERVER_PASSWORD": "senha"}


# --- o plano: o que cada variável vira em produção ------------------------------------------

def test_primeira_vez_leva_todas_e_mascara_as_senhas():
    p = _mod().planejar(HML, {}, CONFIG)
    assert p.faltando == [] and p.invalidas == []
    assert p.gravar == {"TZ": "America/Sao_Paulo", "DB_PASSWORD": "*****", "API_URL": "https://prd.x",
                        "DOCKER_REGISTRY_SERVER_PASSWORD": "*****"}
    assert p.pendentes == ["DB_PASSWORD", "DOCKER_REGISTRY_SERVER_PASSWORD"]


def test_segunda_vez_nunca_sobrescreve_a_senha_verdadeira():
    prd = {"TZ": "America/Sao_Paulo", "DB_PASSWORD": "senha-real-do-prestador",
           "API_URL": "https://prd.x", "DOCKER_REGISTRY_SERVER_PASSWORD": "*****"}
    p = _mod().planejar(HML, prd, CONFIG)
    assert "DB_PASSWORD" not in p.gravar, "apagaria a senha que o prestador colocou"
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" not in p.gravar
    assert p.pendentes == ["DOCKER_REGISTRY_SERVER_PASSWORD"], "a que segue ***** continua pendente"


def test_variavel_da_homologacao_fora_do_arquivo_trava():
    hml = dict(HML, NOVA_VAR="x")
    p = _mod().planejar(hml, {}, CONFIG)
    assert p.faltando == ["NOVA_VAR"]


def test_marca_invalida_trava():
    p = _mod().planejar(HML, {}, dict(CONFIG, TZ="copia"))
    assert p.invalidas == ["TZ"]


def test_variavel_so_no_arquivo_e_avisada_e_nao_gravada():
    p = _mod().planejar(HML, {}, dict(CONFIG, VELHA="copiar"))
    assert p.sobrando == ["VELHA"] and "VELHA" not in p.gravar


def test_variavel_que_so_existe_em_producao_e_gravada():
    """Caso do Whats: `WEBSITE_DNS_ALT_SERVER=168.63.129.16` é obrigatória em produção e a homologação
    funciona sem ela — o DNS de cada VNet é diferente."""
    cfg = dict(CONFIG, WEBSITE_DNS_ALT_SERVER={"prd": "168.63.129.16"})
    p = _mod().planejar(HML, {}, cfg)
    assert p.gravar["WEBSITE_DNS_ALT_SERVER"] == "168.63.129.16"
    assert p.sobrando == [] and p.invalidas == []
    assert ("WEBSITE_DNS_ALT_SERVER", "só em produção: valor do app-settings.json") in p.acoes


def test_so_em_producao_tem_de_ter_valor_de_producao():
    for marca in ("copiar", "senha"):
        p = _mod().planejar(HML, {}, dict(CONFIG, SO_PRD=marca))
        assert p.sobrando == ["SO_PRD"] and "SO_PRD" not in p.gravar, marca


def test_variavel_so_em_producao_nao_e_apagada():
    p = _mod().planejar(HML, {"SO_PRD": "x"}, CONFIG)
    assert "SO_PRD" not in p.gravar   # gravação é por mescla: o que não está no plano fica como está


def test_sugestao_copia_o_que_e_igual_nos_dois_ambientes():
    """Registro de imagens compartilhado (mssaicontainerregistry): a senha é a mesma em homologação e
    produção — `*****` deixaria produção sem subir até o prestador preencher (decisão do owner,
    2026-10-15). WEBSITE_DNS_SERVER=10.170.210.2 também é igual nos dois (conferido no portal)."""
    s = _mod().sugerir(["DOCKER_REGISTRY_SERVER_PASSWORD", "DOCKER_REGISTRY_SERVER_USERNAME",
                        "DOCKER_REGISTRY_SERVER_URL", "WEBSITE_DNS_SERVER"])
    assert set(s.values()) == {"copiar"}, s


def test_sugestao_marca_senha_pelo_nome():
    s = _mod().sugerir(["TZ", "DB_PASSWORD", "API_KEY", "AUTH_TOKEN", "SQL_CONNECTION_STRING",
                        "CIPHERTEXT_SSC", "CLIENT_SECRET", "SENHA_BANCO", "LOG_ATIVO", "SQL_PWD"])
    assert s == {"TZ": "copiar", "DB_PASSWORD": "senha", "API_KEY": "senha", "AUTH_TOKEN": "senha",
                 "SQL_CONNECTION_STRING": "senha", "CIPHERTEXT_SSC": "senha", "CLIENT_SECRET": "senha",
                 "SENHA_BANCO": "senha", "LOG_ATIVO": "copiar", "SQL_PWD": "senha"}


# --- a linha de comando que o pipeline roda (az falso) ---------------------------------------

def test_sugestao_liga_desliga_com_token_no_nome_e_copiar():
    """MSS-UTILS: NFCOMISSAO_AUTH_TOKEN_ATIVO (true/false) saiu marcada senha só por ter TOKEN no nome."""
    s = _mod().sugerir(["NFCOMISSAO_AUTH_TOKEN_ATIVO", "NFCOMISSAO_UI_ATIVA", "API_KEY_ATIVA", "NFCOMISSAO_TOKEN_API"])
    assert s == {"NFCOMISSAO_AUTH_TOKEN_ATIVO": "copiar", "NFCOMISSAO_UI_ATIVA": "copiar",
                 "API_KEY_ATIVA": "copiar", "NFCOMISSAO_TOKEN_API": "senha"}


def test_copiar_valor_vazio_nunca_grava_vazio():
    """MSS-UTILS 2026-10-20: a DOCKER_REGISTRY_SERVER_PASSWORD chegou vazia em produção (o Azure não
    entrega o valor dela na leitura) e o Web App não subiu. Valor vazio vira pendência, não gravação."""
    hml = dict(HML, VAZIA="", NULA=None)
    p = _mod().planejar(hml, {}, dict(CONFIG, VAZIA="copiar", NULA="copiar"))
    assert "VAZIA" not in p.gravar and "NULA" not in p.gravar
    assert {"VAZIA", "NULA"} <= set(p.pendentes)
    assert ("VAZIA", "veio vazia da homologação: preencher") in p.acoes


class _Az:
    def __init__(self, hml, prd, acr="senha-do-registro"):
        self.apps = {("RG-MSSAI-DEV", "app-hml"): hml, ("RG-MSSAI-PRD", "app-prd"): prd}
        self.gravado = None
        self.acr = acr
        self.acr_pedido = None

    def __call__(self, args):
        if args[:3] == ["acr", "credential", "show"]:
            self.acr_pedido = args[args.index("-n") + 1]
            return (0, self.acr) if self.acr else (1, "")
        rg = args[args.index("-g") + 1]
        app = args[args.index("-n") + 1]
        if args[:4] == ["webapp", "config", "appsettings", "list"]:
            dados = self.apps.get((rg, app))
            if dados is None:
                return 3, ""
            return 0, json.dumps([{"name": k, "value": v, "slotSetting": False} for k, v in dados.items()])
        if args[:4] == ["webapp", "config", "appsettings", "set"]:
            arquivo = args[args.index("--settings") + 1].lstrip("@")
            self.gravado = {i["name"]: i["value"] for i in json.loads(Path(arquivo).read_text(encoding="utf-8"))}
            self.apps[(rg, app)].update(self.gravado)
            return 0, "[]"
        raise AssertionError(f"az inesperado: {args}")


def _argv(acao, config):
    return [acao, "--config", str(config), "--hml-rg", "RG-MSSAI-DEV", "--hml-app", "app-hml",
            "--prd-rg", "RG-MSSAI-PRD", "--prd-app", "app-prd"]


def _rodar(acao, config, az):
    linhas = []
    code = _mod().executar(_argv(acao, config), az=az, saida=linhas.append)
    return code, "\n".join(linhas)


def test_conferir_sem_arquivo_propoe_a_lista_e_falha(tmp_path):
    az = _Az(HML, None)
    code, log = _rodar("conferir", tmp_path / "app-settings.json", az)
    assert code == 1
    proposta = json.loads(log[log.index("{"):log.rindex("}") + 1])
    assert proposta == {"API_URL": "copiar", "DB_PASSWORD": "senha",
                        "DOCKER_REGISTRY_SERVER_PASSWORD": "copiar", "TZ": "copiar"}


def test_conferir_nunca_mostra_valor_no_log(tmp_path):
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(CONFIG), encoding="utf-8")
    prd = {"DB_PASSWORD": "senha-real-do-prestador"}
    code, log = _rodar("conferir", cfg, _Az(HML, prd))
    assert code == 0
    for valor in ("segredo-hml", "acr-pwd", "senha-real-do-prestador", "America/Sao_Paulo",
                  "https://hml.x", "https://prd.x"):
        assert valor not in log, f"valor {valor!r} vazou no log"
    for nome in CONFIG:
        assert nome in log, f"{nome} não aparece no plano"


def test_conferir_falha_dizendo_o_nome_que_faltou(tmp_path):
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(CONFIG), encoding="utf-8")
    code, log = _rodar("conferir", cfg, _Az(dict(HML, NOVA_VAR="x"), None))
    assert code == 1 and "NOVA_VAR" in log


def test_aplicar_grava_por_mescla_e_lista_pendentes(tmp_path):
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(CONFIG), encoding="utf-8")
    az = _Az(HML, {"SO_PRD": "fica"})
    code, log = _rodar("aplicar", cfg, az)
    assert code == 0
    assert az.gravado["DB_PASSWORD"] == "*****" and az.gravado["TZ"] == "America/Sao_Paulo"
    assert az.apps[("RG-MSSAI-PRD", "app-prd")]["SO_PRD"] == "fica"
    assert "DB_PASSWORD" in log and "DOCKER_REGISTRY_SERVER_PASSWORD" in log and "preencher" in log.lower()
    assert "segredo-hml" not in log and "acr-pwd" not in log
    assert not list(tmp_path.glob("*.tmp*")), "arquivo temporário com valores ficou no disco"


def test_aplicar_sem_web_app_de_producao_falha(tmp_path):
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(CONFIG), encoding="utf-8")
    code, log = _rodar("aplicar", cfg, _Az(HML, None))
    assert code == 1 and "app-prd" in log


def test_senha_do_registro_vem_do_proprio_registro(tmp_path):
    """A senha do registro de imagens nao vem na leitura das variaveis da homologacao; o pipeline le
    direto do registro (o nome sai da DOCKER_REGISTRY_SERVER_URL) e grava em producao, sem mostrar no log."""
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(dict(CONFIG, DOCKER_REGISTRY_SERVER_PASSWORD="copiar",
                                   DOCKER_REGISTRY_SERVER_URL="copiar")), encoding="utf-8")
    hml = dict(HML, DOCKER_REGISTRY_SERVER_PASSWORD=None,
               DOCKER_REGISTRY_SERVER_URL="https://mssaicontainerregistry.azurecr.io")
    az = _Az(hml, {})
    code, log = _rodar("aplicar", cfg, az)
    assert code == 0, log
    assert az.acr_pedido == "mssaicontainerregistry"
    assert az.gravado["DOCKER_REGISTRY_SERVER_PASSWORD"] == "senha-do-registro"
    assert "senha-do-registro" not in log
    pendentes = log.split("Faltam preencher")[-1] if "Faltam preencher" in log else ""
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" not in pendentes


def test_registro_sem_acesso_vira_pendencia(tmp_path):
    cfg = tmp_path / "app-settings.json"
    cfg.write_text(json.dumps(dict(CONFIG, DOCKER_REGISTRY_SERVER_PASSWORD="copiar",
                                   DOCKER_REGISTRY_SERVER_URL="copiar")), encoding="utf-8")
    hml = dict(HML, DOCKER_REGISTRY_SERVER_PASSWORD=None,
               DOCKER_REGISTRY_SERVER_URL="https://mssaicontainerregistry.azurecr.io")
    az = _Az(hml, {}, acr=None)
    code, log = _rodar("aplicar", cfg, az)
    assert code == 0, log
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" not in az.gravado
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" in log.split("Faltam preencher")[-1]


# --- plataforma: as variaveis que nao sao do sistema, numa homologacao nova -------------------

def _plataforma(az, porta="8000"):
    linhas = []
    code = _mod().executar(["plataforma", "--app-rg", "RG-MSSAI-DEV", "--app", "app-hml", "--porta", porta],
                           az=az, saida=linhas.append)
    return code, "\n".join(linhas)


def test_plataforma_cria_as_variaveis_da_casa_numa_homologacao_nova():
    """Valores do roteiro do MSS-UTILS (docs/deploy-azure-dev.md:385-398) + AMBIENTE.md secao 5."""
    az = _Az({}, {})
    code, log = _plataforma(az)
    assert code == 0, log
    assert az.gravado == {
        "DOCKER_REGISTRY_SERVER_URL": "https://mssaicontainerregistry.azurecr.io",
        "DOCKER_REGISTRY_SERVER_USERNAME": "mssaicontainerregistry",
        "DOCKER_REGISTRY_SERVER_PASSWORD": "senha-do-registro",
        "WEBSITES_PORT": "8000",
        "WEBSITES_CONTAINER_START_TIME_LIMIT": "600",
        "WEBSITE_HEALTHCHECK_MAXPINGFAILURES": "10",
        "TZ": "America/Sao_Paulo",
        "WEBSITE_DNS_SERVER": "10.170.210.2",
    }
    assert az.acr_pedido == "mssaicontainerregistry"
    assert "senha-do-registro" not in log


def test_plataforma_nunca_sobrescreve_o_que_ja_existe():
    az = _Az({"WEBSITES_PORT": "9000", "TZ": "UTC"}, {})
    code, _ = _plataforma(az)
    assert code == 0
    assert "WEBSITES_PORT" not in az.gravado and "TZ" not in az.gravado
    assert az.apps[("RG-MSSAI-DEV", "app-hml")]["WEBSITES_PORT"] == "9000"


def test_plataforma_sem_acesso_ao_registro_lista_a_pendencia():
    az = _Az({}, {}, acr=None)
    code, log = _plataforma(az)
    assert code == 0
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" not in az.gravado
    assert "DOCKER_REGISTRY_SERVER_PASSWORD" in log.split("Faltam preencher")[-1]


def test_plataforma_sem_web_app_falha():
    az = _Az(None, {})
    code, log = _plataforma(az)
    assert code == 1 and "app-hml" in log
