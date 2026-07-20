<!-- MAPA DE CONTEXTO do projeto (anti-amnésia de partida). Copiado pelo /mss-spec:kickoff para
     docs/superpowers/MAPA.md. É a PRIMEIRA coisa que o assistente lê ao abrir uma janela nova.
     Regra de ouro: CURTO (1 tela) e NÃO MENTE. Mantido pelo fluxo (kickoff cria; nova-feature
     atualiza ao abrir a branch e no fecho) e reconciliável com /mss-spec:mapa.
     Só as 3 seções abaixo — detalhe de tarefa vai na spec viva; aprendizado vai na memory/. -->

# Mapa de contexto — <projeto>

## Onde estamos
<branch atual + tipo (feature/fix/refactor) + assunto, em 1 linha. Ex.: "feature/relatorio-x, a
partir da master — implementando o export CSV". Derivável de `git` + da tarefa 'em andamento' no INDEX;
o `/mss-spec:mapa` regenera isto sozinho.>

## Próximo passo
<a próxima ação concreta pra retomar o trabalho, em 1-3 linhas. É o coração anti-amnésia: o que estava
prestes a fazer quando a janela anterior fechou. Ex.: "falta o teste do caminho de erro e rodar a suíte
antes de fechar a feature". Escrito pelos comandos do fluxo e confirmado por você.>

## Conexões
<!-- As integrações de RUNTIME deste projeto com OUTROS projetos MSIG (o que trabalha junto — não é o
     catálogo de precedentes/padrões, que é a skill precedentes-msig). FORMATO FIXO (o /mss-spec:mapa-neural
     parseia estas linhas pra montar o grafo inter-projeto), uma por conexão:
       - → <outro-projeto>: o que ESTE envia/consome (<ponto: endpoint / fila / tabela compartilhada>)
       - ← <outro-projeto>: o que ESTE expõe/recebe   (<ponto>)
     A seta é a DIREÇÃO do dado; o nome ANTES dos dois-pontos é o OUTRO projeto (o nó); o ponto entre
     parênteses é opcional. DECLARE a partir do CÓDIGO REAL (routers de integração, clients HTTP, filas,
     banco compartilhado) + o que o owner confirmar. NUNCA inventar uma conexão: se não sabe o ponto, deixe
     genérico ou marque <a confirmar>. Uma conexão errada é pior que uma lacuna. "nenhuma" é resposta válida
     (o parser ignora linhas "nenhuma"/"<a confirmar>"). -->
- nenhuma conhecida ainda

<!-- Atualizado em <data> · regenerável com /mss-spec:mapa -->
