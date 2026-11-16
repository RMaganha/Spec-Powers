# 2026-10-14 — proteção do histórico de conversas (diário retroativo)

conversa: c67c2651-6670-46f4-a878-3c2850ab3eb4

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
Proteção contra a limpeza automática das conversas do Claude Code: o owner perdeu conversas do ATA ("Sessão não
encontrada no disco").

## Pivôs
- O Claude Code apaga sozinho as conversas paradas há mais de `cleanupPeriodDays` dias (padrão 30); `0` falha na
  validação; plugin não define essa chave; nesta máquina ela estava em 730 (falas 001-002).
- De comandos manuais para tudo automático, fora do plugin: "Tinha que ser auto suficiente para fazer sozinho" (fala 003).

## Rejeitado
`/mss-spec:salvar-historico` e `/mss-spec:restaurar-historico`.

## Fizemos
Só o diagnóstico (730 dias; a regra do nome da pasta conferida).

## Próximo
As respostas sobre Docker e restauração (fala 004); nada implementado.
