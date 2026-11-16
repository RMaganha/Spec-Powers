# 2026-09-22 — inventário do banco vivo, 0.28.0 (diário retroativo)

conversa: d38f613e-7098-41ab-9118-4537815241be

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
Como analisar um projeto C# legado com banco SQL Server; esta janela é só do plugin (fala 003).

## Pivôs
- Comando próprio que a `analise` dispara sozinha (fala 005); a credencial vem do par Fernet reaproveitado + `--base`,
  sem arquivo de configuração.
- Por subagentes ficou lento ("muito demorado com agents", fala 028): implementação direta com um revisor no fim.

## Rejeitado
Fase em prosa; subcomando do `banco`; `banco.md` como configuração; HTML na v1.

## Fizemos
0.28.0, 452 testes, `COMO-FUNCIONA.html` com 25 cartões e teste de contagem. Decisão em `docs/decisoes.md:35`.

## Próximo
Merge e push do owner; teste contra o banco real no projeto C#.
