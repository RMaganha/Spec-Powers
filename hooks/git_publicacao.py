"""Hook do mss-spec: PUBLICAR e INTEGRAR é ato do owner — o assistente não aperta esse botão.

Nasceu de um acidente real (2026-09, caso F-022 em `docs/EVALS.md`): numa janela aberta pra
UMA feature, o assistente absorveu um 2º e um 3º assunto, mesclou branches e disparou
`git push` — e o push é o gatilho do deploy automático em homologação. Quando o owner viu,
vários já tinham ido; o ambiente quebrou inteiro e custou centenas de testes pra entender o quê.

A frase "`git push` só quando eu pedir" JÁ estava no `CLAUDE.md` e foi ignorada: prosa não
segura na hora 2 de uma sessão longa. Este hook é a camada que não depende de o assistente se
comportar — a mesma filosofia da cerca da âncora (`projeto_ativo.py`).

Contrato:
- evento `PreToolUse`, matcher `Bash|PowerShell`; lê `tool_input.command`;
- **nega** o que publica (`git push`), integra (`git merge`, `git rebase`, `gh pr merge`) ou
  faz deploy (`docker push`, `az acr build`, `az webapp <escrita>`, `az containerapp update`);
  casa o VERBO no início de um comando simples (após `;`, `&&`, `|`, `(`, quebra de linha ou
  prefixo `VAR=x`), não a palavra solta — `grep 'git push'` e `echo pushing` passam;
- **libera** o resto do git (status, log, diff, fetch, add, commit, checkout/switch/branch,
  `merge --abort`, `rebase --abort`) — abrir a branch da feature continua livre;
- **falha FECHADA**: há comando e a avaliação estourou → nega (cerca com defeito não pode abrir
  sozinha). Evento sem comando (malformado) → libera calado: não existe push num evento vazio.

Escape consciente, só do owner: `MSS_PUBLICACAO_OFF=1`.
"""
import json
import os
import re
import sys

ENV_DESLIGA = "MSS_PUBLICACAO_OFF"
TOOLS_DE_SHELL = ("Bash", "PowerShell")

# Início de um comando simples: começo do texto, separador de shell, abre-parêntese ou `$(`.
_INICIO = r"(?:^|[;&|\n(]|\$\()\s*"
# Prefixo `VAR=valor` (um ou mais) antes do executável.
_ENV = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
# `git` com opções globais antes do verbo: `-C <dir>`, `-c k=v`, `--no-pager`, `--git-dir=…`.
_GIT = r"git(?:\s+-[cC]\s+\S+|\s+--[\w-]+(?:=\S+)?)*\s+"

PADROES = (
    (re.compile(_INICIO + _ENV + _GIT + r"push\b"), "git push — publica e dispara o deploy"),
    (re.compile(_INICIO + _ENV + _GIT + r"merge\b(?!\s+--abort\b)"), "git merge — integra branches"),
    (re.compile(_INICIO + _ENV + _GIT + r"rebase\b(?!\s+--abort\b)"), "git rebase — reescreve/integra"),
    (re.compile(_INICIO + _ENV + r"gh\s+pr\s+merge\b"), "gh pr merge — integra o PR"),
    (re.compile(_INICIO + _ENV + r"docker\s+push\b"), "docker push — publica imagem"),
    (re.compile(_INICIO + _ENV + r"az\s+acr\s+build\b"), "az acr build — constrói e publica imagem"),
    (re.compile(_INICIO + _ENV + r"az\s+webapp\s+(?!(?:log|show|list)\b)\S"),
     "az webapp <escrita> — altera o Web App"),
    (re.compile(_INICIO + _ENV + r"az\s+containerapp\s+(?:update|create|revision)\b"),
     "az containerapp — altera o Container App"),
)

MOTIVO = (
    "[mss-spec] BLOQUEADO — publicar/integrar é ato do OWNER, não do assistente.\n"
    "Comando recusado ({alvo}):\n  {comando}\n\n"
    "Por quê: `git push` dispara o deploy automático (homologação/produção) e merge/rebase "
    "mistura branches. Em 2026-09 o assistente disparou vários pushes numa janela de feature e "
    "quebrou a homologação inteira (caso F-022 do docs/EVALS.md). "
    "Se a mudança está pronta: rode `/mss-spec:release` (gate de pré-publicação), cole o veredito "
    "e PEÇA — o owner publica e integra do terminal dele. "
    "Escape consciente (só o owner decide): {env}=1."
)

MOTIVO_DEFEITO = (
    "[mss-spec] BLOQUEADO — a cerca de publicação está com DEFEITO ({erro!r}) e, por segurança, "
    "nega em vez de abrir. Publicar/integrar segue sendo ato do owner (rode `/mss-spec:release` "
    "e peça). Reporte o erro; escape consciente (só o owner): {env}=1."
)


def _texto(valor):
    """Env/campo vazio ou em branco conta como ausente."""
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def publica_ou_integra(comando):
    """Rótulo do 1º padrão de publicação/integração que o comando contém, ou None."""
    for padrao, rotulo in PADROES:
        if padrao.search(comando):
            return rotulo
    return None


def decidir(evento, ambiente=None):
    """None = libera; str = motivo do bloqueio."""
    ambiente = os.environ if ambiente is None else ambiente
    if _texto(ambiente.get(ENV_DESLIGA)):
        return None
    if not isinstance(evento, dict) or evento.get("tool_name") not in TOOLS_DE_SHELL:
        return None
    entrada = evento.get("tool_input")
    comando = entrada.get("command") if isinstance(entrada, dict) else None
    comando = _texto(comando)
    if comando is None:
        return None                                  # nada a avaliar → nada a negar
    try:
        alvo = publica_ou_integra(comando)
    except Exception as erro:                        # noqa: BLE001 — falha FECHADA
        return MOTIVO_DEFEITO.format(erro=erro, env=ENV_DESLIGA)
    if alvo is None:
        return None
    return MOTIVO.format(alvo=alvo, comando=comando[:200], env=ENV_DESLIGA)


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:                                # noqa: BLE001
        sys.exit(0)                                  # entrada inválida: não há comando → libera
    motivo = decidir(evento)
    if motivo is None:
        sys.exit(0)                                  # libera, calado
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": motivo,
    }}))
    print(motivo, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
