"""Variáveis de ambiente (App Settings) da homologação levadas pra produção — gerado pelo /mss-spec:azure-ambiente.

Roda DENTRO do pipeline (azure-pipelines-infra.yml), já logado no Azure pela conexão do pipeline.
Nunca imprime valor: só nomes e o que acontece com cada um.

O arquivo `infra/app-settings.json` (versionado, sem valor nenhum) diz o que fazer com cada variável:
  "copiar"            → copia o valor da homologação (vazia na leitura → pendência, nunca grava vazio; a
                        DOCKER_REGISTRY_SERVER_PASSWORD, que o Azure não entrega, vem do próprio registro)
  "senha"             → grava ***** só se a variável ainda não existe em produção (nunca apaga a verdadeira)
  {"prd": "<valor>"}  → grava o valor de produção escrito ali (nunca senha — senha é "senha"); é também
                        o jeito de criar variável que só existe em produção (ex.: WEBSITE_DNS_ALT_SERVER)

  conferir  → compara homologação × arquivo e mostra o plano. Variável da homologação fora do arquivo
              TRAVA (exit 1) com o nome dela; sem arquivo, imprime a proposta pronta pra colar.
  aplicar   → confere e grava em produção por MESCLA (o que não está no plano fica como está) e lista
              as senhas que ainda estão ***** em produção — o que falta o prestador preencher.
  plataforma → numa homologação NOVA, cria só as variáveis de plataforma da casa (registro de imagens,
              porta, tempo de subida, saúde, fuso, DNS) que ainda não existem — nunca sobrescreve. As do
              sistema o owner cria no portal.

Fora do Bicep de propósito: no Bicep, `appSettings` substitui a coleção inteira — uma 2ª execução
apagaria a senha que o prestador colocou à mão.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

MASCARA = "*****"
_SENHA = re.compile(r"(?i)PASS|PWD|SENHA|SECRET|KEY|TOKEN|CIPHER|CONNECTION|CREDENTIAL")


@dataclass
class Plano:
    gravar: dict = field(default_factory=dict)
    acoes: list = field(default_factory=list)       # (nome, o que acontece) — nunca o valor
    faltando: list = field(default_factory=list)    # na homologação, fora do arquivo → trava
    sobrando: list = field(default_factory=list)    # no arquivo, fora da homologação, sem valor de prd → só avisa
    invalidas: list = field(default_factory=list)   # marca que não é copiar/senha/{"prd": ...} → trava
    pendentes: list = field(default_factory=list)   # senha que fica ***** em produção


# Iguais nos dois ambientes (docs/AMBIENTE.md §5): o registro de imagens é compartilhado — com *****
# produção não sobe até o prestador preencher (decisão do owner, 2026-10-15).
_SEMPRE_COPIAR = {"DOCKER_REGISTRY_SERVER_PASSWORD"}
# Liga/desliga (true/false) não é senha mesmo com TOKEN/KEY no nome — ex.: NFCOMISSAO_AUTH_TOKEN_ATIVO.
_LIGA_DESLIGA = re.compile(r"(?i)_ATIV[OA]$")
# O Azure não entrega o valor desta na leitura das variáveis: vem do próprio registro de imagens.
SENHA_REGISTRO = "DOCKER_REGISTRY_SERVER_PASSWORD"


def sugerir(nomes):
    """Proposta inicial do arquivo: senha pelo nome, o resto copia. O owner revisa antes do commit."""
    return {n: ("senha" if _SENHA.search(n) and n not in _SEMPRE_COPIAR and not _LIGA_DESLIGA.search(n)
                else "copiar") for n in nomes}


def _valor_prd(marca):
    return isinstance(marca, dict) and set(marca) == {"prd"} and isinstance(marca["prd"], str)


def planejar(hml, prd, config):
    p = Plano()
    p.faltando = sorted(n for n in hml if n not in config)
    # só em produção (ex.: WEBSITE_DNS_ALT_SERVER — o DNS de cada VNet é diferente): vale com valor de
    # produção; "copiar"/"senha" sem a variável na homologação não tem de onde vir → só avisa
    for nome in sorted(n for n in config if n not in hml):
        if _valor_prd(config[nome]):
            p.gravar[nome] = config[nome]["prd"]
            p.acoes.append((nome, "só em produção: valor do app-settings.json"))
        else:
            p.sobrando.append(nome)
    for nome in sorted(n for n in config if n in hml):
        marca = config[nome]
        if marca == "copiar":
            if hml[nome] in (None, ""):     # vazia na leitura: gravar vazio derrubaria produção calado
                p.acoes.append((nome, "veio vazia da homologação: preencher"))
                p.pendentes.append(nome)
            else:
                p.gravar[nome] = hml[nome]
                p.acoes.append((nome, "copia o valor da homologação"))
        elif marca == "senha":
            if nome not in prd:
                p.gravar[nome] = MASCARA
                p.acoes.append((nome, "senha nova: grava *****"))
                p.pendentes.append(nome)
            elif prd[nome] == MASCARA:
                p.acoes.append((nome, "senha ainda ***** em produção: preencher"))
                p.pendentes.append(nome)
            else:
                p.acoes.append((nome, "senha já preenchida em produção: não mexe"))
        elif _valor_prd(marca):
            p.gravar[nome] = marca["prd"]
            p.acoes.append((nome, "valor de produção do app-settings.json"))
        else:
            p.invalidas.append(nome)
    return p


def _az_real(args):
    proc = subprocess.run(["az", *args], capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout


def _listar(az, rg, app):
    """{nome: valor} das App Settings, ou None se o Web App não existe/não responde."""
    code, saida = az(["webapp", "config", "appsettings", "list", "-g", rg, "-n", app, "-o", "json"])
    if code != 0:
        return None
    return {i["name"]: i["value"] for i in json.loads(saida or "[]")}


def _senha_do_registro(az, hml):
    """Senha do registro de imagens lida do próprio registro — o nome sai da DOCKER_REGISTRY_SERVER_URL
    (https://<nome>.azurecr.io). None se não der (sem URL, sem acesso): aí ela vira pendência."""
    url = (hml.get("DOCKER_REGISTRY_SERVER_URL") or "").strip()
    m = re.match(r"(?i)^(?:https?://)?([a-z0-9]+)\.azurecr\.io/?$", url)
    if not m:
        return None
    code, valor = az(["acr", "credential", "show", "-n", m.group(1), "--query", "passwords[0].value", "-o", "tsv"])
    return valor.strip() if code == 0 and valor.strip() else None


def _gravar(az, rg, app, valores):
    """Grava por MESCLA (o que não está em `valores` fica como está). Valores passam por arquivo
    temporário apagado em seguida — nunca pela linha de comando nem pelo log."""
    fd, caminho = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump([{"name": k, "value": v, "slotSetting": False} for k, v in valores.items()], f)
        code, _ = az(["webapp", "config", "appsettings", "set", "-g", rg, "-n", app,
                      "--settings", "@" + caminho, "-o", "none"])
    finally:
        os.remove(caminho)
    return code


# Variáveis de PLATAFORMA (não são do sistema) de toda homologação nova — roteiro do MSS-UTILS
# (docs/deploy-azure-dev.md §8) e docs/AMBIENTE.md §5. As do sistema o owner cria no portal.
REGISTRO = "mssaicontainerregistry"
PLATAFORMA = {
    "DOCKER_REGISTRY_SERVER_URL": f"https://{REGISTRO}.azurecr.io",
    "DOCKER_REGISTRY_SERVER_USERNAME": REGISTRO,
    "WEBSITES_CONTAINER_START_TIME_LIMIT": "600",
    "WEBSITE_HEALTHCHECK_MAXPINGFAILURES": "10",
    "TZ": "America/Sao_Paulo",
    "WEBSITE_DNS_SERVER": "10.170.210.2",
}


def plataforma(a, az, saida):
    atual = _listar(az, a.app_rg, a.app)
    if atual is None:
        saida(f"ERRO: o Web App {a.app} em {a.app_rg} não existe ou não responde — a receita tem de criá-lo antes.")
        return 1
    desejado = dict(PLATAFORMA, WEBSITES_PORT=a.porta)
    senha = _senha_do_registro(az, {"DOCKER_REGISTRY_SERVER_URL": PLATAFORMA["DOCKER_REGISTRY_SERVER_URL"]})
    pendentes = []
    if senha:
        desejado[SENHA_REGISTRO] = senha
    elif atual.get(SENHA_REGISTRO) in (None, ""):
        pendentes.append(SENHA_REGISTRO)
    gravar = {k: v for k, v in desejado.items() if atual.get(k) in (None, "")}
    for nome in sorted(desejado):
        saida(f"  {nome}: {'cria' if nome in gravar else 'já existe: não mexe'}")
    if gravar:
        code = _gravar(az, a.app_rg, a.app, gravar)
        if code != 0:
            saida(f"ERRO: a gravação das variáveis em {a.app} falhou (az saiu {code}).")
            return 1
        saida(f"Gravadas {len(gravar)} variáveis de plataforma em {a.app}. As do sistema: crie no portal.")
    if pendentes:
        saida(f"Faltam preencher (com ***** ou vazias): {', '.join(pendentes)}")
    return 0


def executar(argv, az=_az_real, saida=print):
    ap = argparse.ArgumentParser(prog="app_settings.py")
    sub = ap.add_subparsers(dest="acao", required=True)
    for acao in ("conferir", "aplicar"):
        p = sub.add_parser(acao)
        p.add_argument("--config", required=True)
        p.add_argument("--hml-rg", required=True)
        p.add_argument("--hml-app", required=True)
        p.add_argument("--prd-rg", required=True)
        p.add_argument("--prd-app", required=True)
    p = sub.add_parser("plataforma")
    p.add_argument("--app-rg", required=True)
    p.add_argument("--app", required=True)
    p.add_argument("--porta", required=True)
    a = ap.parse_args(argv)
    if a.acao == "plataforma":
        return plataforma(a, az, saida)

    hml = _listar(az, a.hml_rg, a.hml_app)
    if hml is None:
        saida(f"ERRO: não deu pra ler as variáveis da homologação ({a.hml_app} em {a.hml_rg}).")
        return 1
    if not os.path.exists(a.config):
        saida(f"ERRO: falta o {a.config}. Proposta com as {len(hml)} variáveis da homologação:")
        saida(json.dumps(sugerir(sorted(hml)), indent=2, ensure_ascii=False))
        saida("Revise antes de gravar: senha/chave → \"senha\"; valor que muda em produção (URL, "
              "servidor, ambiente) → troque \"copiar\" pelo objeto com a chave \"prd\" e o valor de produção.")
        return 1
    with open(a.config, encoding="utf-8") as f:
        config = json.load(f)
    if config.get(SENHA_REGISTRO) == "copiar" and hml.get(SENHA_REGISTRO) in (None, ""):
        senha = _senha_do_registro(az, hml)
        if senha:
            hml[SENHA_REGISTRO] = senha

    prd = _listar(az, a.prd_rg, a.prd_app)
    if prd is None and a.acao == "aplicar":
        saida(f"ERRO: o Web App de produção {a.prd_app} em {a.prd_rg} não existe ou não responde — "
              "a receita tem de criá-lo antes.")
        return 1
    plano = planejar(hml, prd or {}, config)

    saida(f"Variáveis: {len(hml)} na homologação → {a.prd_app} ({a.prd_rg})")
    for nome, oque in plano.acoes:
        saida(f"  {nome}: {oque}")
    for nome in plano.sobrando:
        saida(f"  AVISO {nome}: está no arquivo, não existe na homologação e não tem valor de "
              "produção — não é gravada")
    if plano.faltando or plano.invalidas:
        if plano.faltando:
            saida("ERRO: variáveis da homologação que NÃO estão no "
                  f"{a.config} (acrescente com a marca certa): {', '.join(plano.faltando)}")
        if plano.invalidas:
            saida(f"ERRO: marca inválida (use \"copiar\", \"senha\" ou {{\"prd\": \"<valor>\"}}): "
                  f"{', '.join(plano.invalidas)}")
        return 1

    if a.acao == "aplicar" and plano.gravar:
        code = _gravar(az, a.prd_rg, a.prd_app, plano.gravar)
        if code != 0:
            saida(f"ERRO: a gravação das variáveis em {a.prd_app} falhou (az saiu {code}).")
            return 1
        saida(f"Gravadas {len(plano.gravar)} variáveis em {a.prd_app} (as demais ficaram como estavam).")
    if plano.pendentes:
        saida(f"Faltam preencher em produção (com ***** ou vazias): {', '.join(plano.pendentes)}")
    return 0


if __name__ == "__main__":
    sys.exit(executar(sys.argv[1:]))
