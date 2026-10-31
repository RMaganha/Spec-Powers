<#
.SYNOPSIS
  Guardiao da juncao do mss-spec: confere que ~/.claude/skills/mss-spec e uma juncao para o clone do kit
  e, se sumiu ou aponta pra outro lugar, captura a evidencia e recria. Nunca apaga pasta real.

.DESCRIPTION
  Por que existe (pendencia "intermitencia pos-update", memory/project_pendencia_intermitencia_pos_update.md):
  o app Claude Code se atualiza sozinho (autoUpdatesChannel: latest) e ja aconteceu de a juncao sumir ou
  deixar de ser lida depois de uma atualizacao. Quando ela some, o kit inteiro some: comandos e hooks.
  Por isso este guarda vive FORA do kit: e chamado por um hook SessionStart no settings.json do USUARIO
  (nao do plugin) e por uma tarefa do Agendador do Windows (logon + a cada hora).

  Regras:
  - tudo certo -> uma linha "ok" no log e silencio (exit 0);
  - problema -> captura a evidencia no log ANTES de mexer (o que havia no lugar, a listagem de skills/),
    depois conserta: pasta real com conteudo e RENOMEADA para mss-spec.bak-<data>, nunca apagada;
    juncao errada e removida (so o atalho, o destino nao e tocado); juncao nova e criada;
  - alvo (o clone do kit) ausente -> nao cria nada, so registra;
  - -Sessao: alem do log, imprime {"systemMessage": ...} quando AGIU (o hook SessionStart mostra ao owner);
  - exit 0 sempre; nunca bloqueia nada.

.PARAMETER Alvo
  Pasta do clone do kit. Padrao: a pasta acima de templates/ (onde este script mora).
.PARAMETER Link
  Caminho da juncao. Padrao: $env:USERPROFILE\.claude\skills\mss-spec
.PARAMETER Log
  Arquivo de log. Padrao: $env:USERPROFILE\.claude\mss-spec\guardiao-juncao.log
.PARAMETER Sessao
  Modo hook SessionStart: imprime systemMessage em JSON quando recria ou falha.
#>
[CmdletBinding()]
param(
  [string]$Alvo = "",
  [string]$Link = (Join-Path $env:USERPROFILE ".claude\skills\mss-spec"),
  [string]$Log = (Join-Path $env:USERPROFILE ".claude\mss-spec\guardiao-juncao.log"),
  [switch]$Sessao
)

$ErrorActionPreference = "Stop"

# O padrao do alvo e o clone onde este script mora (pasta acima de templates/). Calculado AQUI, no corpo:
# no PowerShell 5.1 chamado com -File, $PSScriptRoot chega vazio na hora de avaliar o default do param
# (foi assim que a 1a rodada de verdade falhou, com os testes verdes porque passavam -Alvo).
if (-not $Alvo) {
  $aqui = $MyInvocation.MyCommand.Path
  if (-not $aqui) { $aqui = $PSCommandPath }
  $Alvo = Split-Path -Parent (Split-Path -Parent $aqui)
}

function Normalizar([string]$p) {
  if (-not $p) { return "" }
  $p = $p -replace '^\\\\\?\\', ''          # tira o prefixo \\?\ que o Windows poe no Target
  return ($p.TrimEnd('\', '/')).ToLowerInvariant()
}

function Anotar([string]$decisao, [string]$detalhe) {
  try {
    $pasta = Split-Path -Parent $Log
    if (-not (Test-Path -LiteralPath $pasta)) { New-Item -ItemType Directory -Path $pasta -Force | Out-Null }
    $linha = "{0} {1} {2}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"), $decisao, $detalhe
    Add-Content -LiteralPath $Log -Value $linha -Encoding UTF8
  } catch { }
}

function Estado {
  # ausente | pasta-real | aponta-errado:<destino> | sem-hooks | ok
  if (-not (Test-Path -LiteralPath $Link)) { return "ausente" }
  $item = Get-Item -LiteralPath $Link -Force
  if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return "pasta-real" }
  $destino = [string]($item.Target | Select-Object -First 1)
  if ((Normalizar $destino) -ne (Normalizar $Alvo)) { return "aponta-errado:$destino" }
  if (-not (Test-Path -LiteralPath (Join-Path $Link "hooks\hooks.json"))) { return "sem-hooks" }
  return "ok"
}

function Evidencia([string]$estado) {
  $pai = Split-Path -Parent $Link
  $lista = "(pasta skills ausente)"
  if (Test-Path -LiteralPath $pai) {
    $lista = (Get-ChildItem -LiteralPath $pai -Force | ForEach-Object {
      $tipo = if ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) { "juncao->" + [string]($_.Target | Select-Object -First 1) } elseif ($_.PSIsContainer) { "pasta" } else { "arquivo" }
      "$($_.Name)[$tipo]"
    }) -join "; "
  }
  Anotar "evidencia" ("estado=$estado alvo=$Alvo skills: $lista")
}

function Mensagem([string]$texto) {
  if ($Sessao) {
    $obj = @{ systemMessage = "[mss-spec] $texto" }
    Write-Output ($obj | ConvertTo-Json -Compress)
  }
}

try {
  if (-not (Test-Path -LiteralPath (Join-Path $Alvo "hooks\hooks.json"))) {
    Anotar "alvo-ausente" "alvo=$Alvo (nada criado)"
    Mensagem "O clone do kit nao esta em $Alvo; a juncao nao foi refeita. Confira a pasta do repo."
    exit 0
  }

  $estado = Estado
  if ($estado -eq "ok") {
    Anotar "ok" "link=$Link"
    exit 0
  }

  Evidencia $estado

  if ($estado -eq "pasta-real") {
    $bak = "$Link.bak-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Rename-Item -LiteralPath $Link -NewName (Split-Path -Leaf $bak)
    Anotar "renomeou" "pasta real -> $bak (nada apagado)"
  } elseif ($estado -ne "ausente") {
    (Get-Item -LiteralPath $Link -Force).Delete()     # remove so o atalho; o destino nao e tocado
    Anotar "removeu" "juncao antiga ($estado)"
  }

  New-Item -ItemType Junction -Path $Link -Target $Alvo | Out-Null
  $depois = Estado
  if ($depois -eq "ok") {
    Anotar "recriou" "link=$Link -> $Alvo (estava: $estado)"
    Mensagem "A juncao do kit estava '$estado' e foi refeita. Feche e reabra esta conversa para o kit carregar."
  } else {
    Anotar "falhou" "depois de recriar o estado e '$depois'"
    Mensagem "Tentei refazer a juncao do kit e o estado ficou '$depois'. Veja o log em $Log."
  }
} catch {
  Anotar "erro" ($_.Exception.Message -replace "`r?`n", " ")
  Mensagem ("O guardiao da juncao falhou: " + ($_.Exception.Message -replace "`r?`n", " ") + ". Log em $Log.")
}
exit 0
