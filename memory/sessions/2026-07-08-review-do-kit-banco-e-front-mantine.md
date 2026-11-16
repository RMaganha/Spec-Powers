# 2026-07-08 — review do kit, conexão de banco e front Mantine (diário retroativo)

conversa: 0db1e7d1-98ee-4f57-afdb-26224ce28b23

> Escrito no sono da memória de 2026-11-16 a partir do texto da conversa (só as falas do owner e do assistente; sem
> saída de ferramenta). Período: 2026-07-08 a 2026-07-14. Credencial dita em texto nas falas 040, 041, 044 e 045:
> não copiada aqui (`*****`; o valor vive no `get_connection.py` do projeto MSS-SSC).

## Conversamos
Review do kit (v0.2.0), estrutura de pastas por camada, `get_connection` com `CONEXAO_SQL`/`CONEXAO_SQL_PORTA`,
build do Docker com ODBC atrás do FortiGate e o front Mantine na branch `plugin-v2`.

## Pivôs
- Credencial cifrada no código e não no `.env` (fala 018).
- **O Transportes V2 é só o modelo do `get_connection.py`, nunca fonte de credencial.** O assistente mandou copiar
  o par DEV do Transportes e deixou os pares HML/PROD como "copie do Transportes V2"; o owner corrigiu: "esse projeto
  não é de transportes eu nunca disse isso, é só deve apontar para o sqlserver certo, D0, HML OU PRD!!" (fala 040, 2026-07-10).
  O assistente: "O Transportes V2 foi só a referência do padrão do `get_connection.py`… nunca foi fonte de credencial"
  (fala 041). A credencial certa foi a que o owner deu (fala 045).
- Erro SQL 18456 = a conexão chegou ao servidor e só a autenticação falhou: mexer em porta ou rede não resolve; o
  assistente testou outras portas mesmo com o owner dizendo "porta padrão" (falas 039, 042-045).
- Só versão estável (fala 068); Mantine 9 / React 19 conferidos no npm (falas 074-078); TypeScript 7 aceito (falas 082-083).
- O owner aceitou que, onde a Mantine entra, o Tailwind sai: "Entendi que conflita um deles com o Tailwind, mas deve
  ter tudo que o Tailwind e muito mais" (fala 054); "Pode seguir" (fala 062).
- Sem ponto de retorno: o branch do git não protege arquivo que nunca foi commitado — voltar atrás virou reescrever
  à mão (no MSS-SSC a troca MRT → datatable) (falas 061, 070, 071).
- **Correção e padrão vêm primeiro pro kit:** "sempre as correções vamos trazer aqui e as melhorias de layout… você
  faz ai o controle é nosso" (fala 090, 2026-07-14) — os projetos consomem o padrão do kit.

## Rejeitado
MRT beta, Next/Remix, status inventado no exemplo (fala 104).

## Fizemos
v0.2.0 a v0.7.0, scaffold do front, `StatusBadge`/`StatusLegend`, busca por funil na coluna (fala 109).

## Próximo
Fechar o funil no MSS-SSC; o ATM depois.
