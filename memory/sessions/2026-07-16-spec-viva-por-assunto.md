# 2026-07-16 — spec viva por assunto (diário retroativo)

conversa: 57f4d059-668e-434a-9f91-3f181ae200fd

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta).

## Conversamos
Os artigos de SDD (sdd-skill e Heeki) e a taxonomia da Böckeler.

## Pivôs
- O owner trouxe o caso "spec antiga, mudo ou crio nova?" e a decisão virou spec viva por assunto:
  `docs/specs/<assunto>.md` com Estado atual + Histórico; o nível médio gera spec enxuta; correção que muda
  comportamento atualiza a spec (falas 015, 019, 021). Registrado no desenho
  `docs/superpowers/specs/2026-07-16-spec-viva-por-assunto-design.md` e na regra crítica 6 das regras do kit.
- O owner reclamou da explicação por metáfora: "não entendi nada sua explicação com referencia a pão e outra com
  mordeu, péssima explicação" (fala 005).
- O comando git entregue usava `\` para continuar a linha, o que quebra no PowerShell (falas 039-040).

## Rejeitado
Arquivos `spec_v1`/`spec_v2`; adotar o sdd-skill; separar por tamanho de projeto.

## Fizemos
Desenho, `nova-feature`, moldes e roteiro no kit; no MSS-SSC, a spec `extracao-jedai` movida para `docs/specs/` (a
spec dizia Fase 1, o código já tinha Fase 2).

## Próximo
O commit do kit ficou pendente (fala 048).
