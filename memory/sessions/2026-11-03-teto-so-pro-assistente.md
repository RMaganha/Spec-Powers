# 2026-11-03 (tarde) — o teto fala só com o assistente · upgrade sem refazer infra (0.52.0)

## Conversamos
Começou como `/mss-spec:doctor` e upgrade 0.51.1 no próprio kit (migração do `CLAUDE.md`, `AMBIENTES.md`, `/logs/`), mesclados
e publicados pelo owner. Depois o desabafo: *"a cada conversa que tenho aqui ou em outros projetos recebo um: 'alerta o mapa
está no limite de 6k... bla bla'"*, *"já ajustamos isso e não resolve, fica alarmando, meus projetos são grandes"*, *"pq esse
bendito teto, já separamos isso em índices???"*. E sobre o upgrade nos projetos em homologação/produção: *"tenta fazer toda a
parte de infra novamente … e se perde, isso é irritante"*. Diagnóstico pelo `/mss-spec:bug` + registro dos hooks + transcripts:
o aviso são três textos de dois hooks, e o upgrade reescreve os arquivos do Docker porque o projeto nascido do kit e em
produção cai fora dos freios da infra própria e do brownfield.

## Pivôs
- **"Feature ou upgrades?" → feature**: os upgrades fechariam só o aviso de abertura dos 5 projetos que o owner quase não abre;
  o barulho real (kit e Whats) é o aviso de gravação, que o upgrade não toca. O freio do upgrade entrou na mesma feature.
- **O teto não é aviso pro owner, é gatilho da separação.** Mostrei a memória (`docs/decisoes.md:39-40`: o hook fala com o
  assistente; "Avise o owner em 1 linha" era texto dos hooks, não decisão) e o owner escolheu: MAPA/INDEX só pro assistente,
  uma vez por sessão; ele ouve só quando o ato é dele (`CLAUDE.md` sem marca → upgrade; `MEMORY.md` → `dividir` com OK).
- **Simulação antes do código, pedida pelo owner** (*"copiar 1 ou 2 projetos para pastas temporárias"*): cópias do Whats e do
  MSS-SSC no scratchpad, sem `.git`, hooks de 0.51.1 rodando nelas. Reproduziu as 36 repetições (bloco vivo de 6,9 KB: 3
  edições, 3 avisos) e o "avise o owner" abaixo do teto (MSS-SSC). **Premissa que caiu:** o MAPA do Whats de 26/10 tinha 0 B
  de comentário do molde — a medida "só conteúdo" não era a causa lá (caso F-051).
- **A CA fica fora do freio do upgrade**: o Stop hook apontou `project_docker_build_fortigate` (CA velha quebra o build); o
  `certs/corp-ca.pem` nem está na categoria 1 — a lista caiu pros 4 arquivos do Docker.

## Rejeitado
- Subir o teto do MAPA (`feedback_teto_que_sempre_estoura_e_estrutura`; o owner em 23/10: "precisamos resolver em definitivo").
- Encurtar o guia do molde e trocar nos projetos: só chega depois de um upgrade em cada um; fora de escopo por ora.
- Rodar os upgrades nos outros projetos daqui: é do owner, na conversa de cada um (`docs/decisoes.md:52`).

## Fizemos
Branch `feature/teto-avisa-uma-vez-e-upgrade-sem-refazer-infra` (da `main` em `4d28026`): `hooks/teto_ao_gravar.py` (recado só pro
assistente; "ainda acima" uma vez por sessão por arquivo, chave `_avisados`; `CLAUDE.md` uma vez por sessão com owner e
`systemMessage`), `hooks/orcamento_partida.py` (owner e `systemMessage` só pra `CLAUDE.md`/`MEMORY.md`; MAPA/INDEX medidos sem
comentário), `templates/rodizio_partida.py` (`bytes_de_conteudo`), `anatomia.py`, `tests/test_orcamento_contexto.py`,
`commands/upgrade.md` (freio "do que já roda", `AMBIENTE.md` sem seção nova, `AMBIENTES.md` sem questionário), spec
`partida-no-orcamento` (9 e 10), spec nova `upgrade.md`, memória `project_upgrade_categoria1_sobrescreve` corrigida, F-051,
CHANGELOG 0.52.0, versão nos dois manifestos. Prova "depois" nas mesmas cópias: bloco vivo → 1 recado interno, depois
silêncio; MSS-SSC → só `CLAUDE.md`/`MEMORY.md` na abertura. Suíte inteira rodando no fecho.

## Próximo
Owner: merge `--no-ff` da branch na `main` (com aprovação ao assistente) e push; `/mss-spec:upgrade` nos projetos quando abrir
cada um (agora sem reescrever infra). Em aberto: F-051 (gatilho do recall casar com a própria proposta), `LC_ALL=enu`, escolha A
da junção (marketplace local).
