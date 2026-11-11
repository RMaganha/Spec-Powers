"""Memória em tabela, parte 2 (0.56.0): a tabela se atualiza sozinha e a busca vai nela primeiro.

Por que existe: a parte 1 entregou um modo manual (`/mss-spec:memory tabela`) e o owner recusou comando pra
lembrar — "vai fazer se perder quando eu perguntar" (caso F-057). Decisões 13 a 22 de
docs/specs/memoria-em-tabela.md: grava-se no arquivo e a tabela acompanha; busca-se na tabela e, se precisar,
nos arquivos; a busca usa os pedidos anteriores da conversa e devolve 30 linhas curtas em dois blocos.
"""
import json
import os
import sqlite3
import subprocess
import sys

from test_memoria_tabela import SCRIPT, _grava, _mod, _projeto, _repo, _sql


# ------------------------------------------------------------------ conferência rápida e atualizar

def _proibido(*_a, **_k):
    raise AssertionError("tabela em dia: não era pra ler arquivo nem chamar o git")


def _espiar_git(mod, monkeypatch):
    chamadas, original = [], mod._git

    def espia(raiz, *args):
        chamadas.append(args)
        return original(raiz, *args)

    monkeypatch.setattr(mod, "_git", espia)
    return chamadas


def test_atualizar_monta_quando_a_tabela_nao_existe(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "nova" / "t.sqlite3", _mod()
    r = mod.atualizar(raiz, tabela, usar_git=False)
    assert r is not None and r.novos == 10 and tabela.is_file()


def test_atualizar_em_dia_nao_le_arquivo_nem_chama_o_git(tmp_path, monkeypatch):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela, usar_git=False)
    monkeypatch.setattr(mod, "_ler_projeto", _proibido)
    monkeypatch.setattr(mod, "_git", _proibido)
    assert mod.atualizar(raiz, tabela) is None


def test_atualizar_pega_arquivo_mudado_novo_e_apagado(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela, usar_git=False)
    _grava(raiz, "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    _grava(raiz, "memory/feedback_novo.md", "---\nname: feedback-novo\ndescription: nota nova\n---\n\ncorpo novo tucano\n")
    (raiz / "docs" / "guia.html").unlink()
    r = mod.atualizar(raiz, tabela, usar_git=False)
    assert (r.novos, r.refeitos, r.removidos) == (1, 1, 1)
    assert _sql(tabela, "SELECT arq FROM memoria WHERE memoria MATCH 'tucano'") == [("memory/feedback_novo.md",)]
    assert mod.atualizar(raiz, tabela, usar_git=False) is None, "atualizada: a conferência seguinte não refaz nada"


def test_linha_de_controle_e_uma_por_projeto_e_nao_conta_como_memoria(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    r = mod.montar(raiz, tabela, usar_git=False)
    _grava(raiz, "to-dolist.md", "# To-do\n\n- outro item\n")
    mod.montar(raiz, tabela, usar_git=False)
    assert "controle" not in r.por_tipo
    assert _sql(tabela, "SELECT count(*) FROM memoria WHERE tipo = 'controle'")[0][0] == 1
    assert mod.status(raiz, tabela, usar_git=False).linhas == 12


def test_tabela_da_parte_1_sem_linha_de_controle_e_conferida_uma_vez(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    c = sqlite3.connect(str(tabela))
    c.execute("DELETE FROM memoria WHERE tipo = 'controle'")
    c.commit()
    c.close()
    r = mod.atualizar(raiz, tabela, usar_git=False)
    assert r is not None and (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 0, 10)
    assert mod.atualizar(raiz, tabela, usar_git=False) is None


def test_arquivo_ignorado_pelo_git_que_muda_nao_vira_remontagem_sem_fim(tmp_path):
    raiz, tabela, mod = _repo(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela)
    _grava(raiz, "docs/escondido.md", "# Escondido\n\n## Parte\nmudou e continua ignorado arara\n")
    r = mod.atualizar(raiz, tabela)
    assert r is not None and (r.novos, r.refeitos, r.removidos) == (0, 0, 0)
    assert not _sql(tabela, "SELECT 1 FROM memoria WHERE memoria MATCH 'arara'")
    assert mod.atualizar(raiz, tabela) is None


def test_atualizar_so_pergunta_ao_git_pelo_arquivo_que_mudou_e_mantem_o_dono(tmp_path, monkeypatch):
    raiz, tabela, mod = _repo(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela)
    _grava(raiz, "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    chamadas = _espiar_git(mod, monkeypatch)
    mod.atualizar(raiz, tabela)
    logs = [a for a in chamadas if "log" in a]
    assert len(logs) == 1 and "docs/specs/boleto.md" in logs[0] and "memory" not in logs[0], logs
    assert not [a for a in chamadas if "status" in a or "rev-list" in a], "pendências são só do relatório do montar"
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'docs/specs/boleto.md'") == [
        ("Fulana Teste", "2026-08-15")]


def test_atualizar_so_com_arquivo_apagado_nao_chama_o_git_log(tmp_path, monkeypatch):
    raiz, tabela, mod = _repo(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela)
    (raiz / "docs" / "guia.html").unlink()
    chamadas = _espiar_git(mod, monkeypatch)
    r = mod.atualizar(raiz, tabela)
    assert r.removidos == 1 and not [a for a in chamadas if "log" in a]


def test_montar_do_zero_segue_trazendo_dono_e_data_de_tudo(tmp_path):
    raiz, tabela = _repo(tmp_path), tmp_path / "t.sqlite3"
    _mod().montar(raiz, tabela)
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'memory/project_boleto.md'") == [
        ("Fulana Teste", "2026-08-15")]
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'docs/decisoes.md'") == [
        ("Fulana Teste", "2026-09-30")], "decisão mantém a data que já traz"


def test_trocar_o_nome_do_projeto_e_visto_pela_conferencia(tmp_path):
    raiz, tabela, mod = _projeto(tmp_path), tmp_path / "t.sqlite3", _mod()
    mod.atualizar(raiz, tabela, usar_git=False)
    _grava(raiz, "CLAUDE.md", "# Projeto Gama — outro objetivo\n")
    assert mod.atualizar(raiz, tabela, usar_git=False) is not None
    assert {p for (p,) in _sql(tabela, "SELECT DISTINCT projeto FROM memoria")} == {"Projeto Gama"}


# ------------------------------------------------------------------ buscar e formatar

def _montado(tmp_path, pasta="alfa", titulo="Projeto Alfa", tabela=None):
    raiz, tabela, mod = _projeto(tmp_path, pasta, titulo), tabela or tmp_path / "t.sqlite3", _mod()
    mod.montar(raiz, tabela, usar_git=False)
    return raiz, tabela, mod


def _muitos_guias(raiz, quantos=40):
    for i in range(quantos):
        _grava(raiz, f"docs/guias/guia-{i:02d}.md",
               f"# Guia {i}\n\n## Parte\ntexto sobre a capivara numero {i}\n\n## Outra\nmais capivara neste guia\n")


def test_buscar_acha_a_anotacao_e_o_documento_do_pedido(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    achados = mod.buscar(raiz, "como emitir a segunda via do boleto pelo CRM", tabela=tabela)
    arqs = [a["arq"] for a in achados]
    assert "memory/project_boleto.md" in arqs and "docs/specs/boleto.md" in arqs
    assert set(achados[0]) == {"arq", "tipo", "ponteiro", "titulo", "trecho"}


def test_buscar_devolve_30_linhas_de_30_arquivos_diferentes(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    _muitos_guias(raiz)
    mod.montar(raiz, tabela, usar_git=False)
    achados = mod.buscar(raiz, "onde fica a capivara", tabela=tabela)
    assert len(achados) == 30 and len({a["arq"] for a in achados}) == 30
    assert len(mod.buscar(raiz, "onde fica a capivara", tabela=tabela, limite=5)) == 5


def test_buscar_so_ve_o_projeto_da_janela(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    outro = _projeto(tmp_path, "beta", "Projeto Beta")
    _grava(outro, "docs/segredo-do-beta.md", "# Beta\n\n## Parte\no ornitorrinco mora so no beta\n")
    mod.montar(outro, tabela, usar_git=False)
    assert mod.buscar(raiz, "cade o ornitorrinco", tabela=tabela) == []
    assert [a["arq"] for a in mod.buscar(outro, "cade o ornitorrinco", tabela=tabela)] == ["docs/segredo-do-beta.md"]


def test_palavra_longa_casa_pelo_comeco_e_acento_nao_atrapalha(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    _grava(raiz, "docs/servidor.md", "# Servidor\n\n## Parte\na configuração fica no painel\n")
    mod.montar(raiz, tabela, usar_git=False)
    assert "docs/servidor.md" in [a["arq"] for a in mod.buscar(raiz, "quais configuracoes existem", tabela=tabela)]


def test_contexto_da_conversa_entra_na_busca(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    assert mod.buscar(raiz, "e isso funciona mesmo?", tabela=tabela) == []
    com = mod.buscar(raiz, "e isso funciona mesmo?", contexto=["como emitir a segunda via do boleto"], tabela=tabela)
    assert "memory/project_boleto.md" in [a["arq"] for a in com]


def test_pedido_sem_palavra_util_ou_com_simbolos_nao_da_erro(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    assert mod.buscar(raiz, "?? e a de", tabela=tabela) == []
    achados = mod.buscar(raiz, 'boleto "AND" OR NEAR( * ^ : -- \' ) [x]', tabela=tabela)
    assert "memory/project_boleto.md" in [a["arq"] for a in achados]


def test_buscar_pode_deixar_tipos_de_fora_e_nunca_devolve_a_linha_de_controle(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    todos = mod.buscar(raiz, "emitir boleto sem conferir", tabela=tabela)
    assert "falha" in {a["tipo"] for a in todos} and "controle" not in {a["tipo"] for a in todos}
    assert "falha" not in {a["tipo"] for a in mod.buscar(raiz, "emitir boleto sem conferir", tabela=tabela, sem_tipos=("falha",))}


def test_buscar_sem_tabela_da_erro_tratavel_e_nao_cria_arquivo(tmp_path):
    raiz, mod, tabela = _projeto(tmp_path), _mod(), tmp_path / "nao-existe.sqlite3"
    try:
        mod.buscar(raiz, "boleto", tabela=tabela)
    except sqlite3.Error:
        pass
    else:
        raise AssertionError("sem tabela a busca tem de avisar, nunca devolver vazio calada")
    assert not tabela.exists()


def test_formatar_separa_anotacoes_de_documentos_em_linhas_curtas(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    _grava(raiz, "docs/longo.md", "# Longo\n\n## " + ("titulo comprido " * 12) + "\nboleto " + ("palavra\n" * 80) + "\n")
    mod.montar(raiz, tabela, usar_git=False)
    texto = mod.formatar(mod.buscar(raiz, "segunda via do boleto no CRM zebra", tabela=tabela))
    blocos = texto.split("Documentos (")
    assert texto.startswith("Anotações (1)") and len(blocos) == 2
    assert "- anotacao | memory/project_boleto.md | project boleto | " in blocos[0]
    assert "memory/sessions/2026-10-01-boleto-no-crm.md" in blocos[1], "diário fica com os documentos"
    assert "docs/specs/boleto.md:3" in blocos[1], "documento aponta arquivo e linha"
    for linha in [l for l in texto.splitlines() if l.startswith("- ")]:
        _tipo, _ponteiro, titulo, trecho = linha[2:].split(" | ", 3)
        assert len(titulo) <= 80 and len(trecho) <= 170, linha


def test_formatar_diz_quando_um_bloco_veio_vazio(tmp_path):
    raiz, tabela, mod = _montado(tmp_path)
    texto = mod.formatar(mod.buscar(raiz, "dominio tartaruga", tabela=tabela))
    assert "Anotações (0)" in texto and "(nenhuma)" in texto and "to-dolist.md" in texto


# ------------------------------------------------------------------ contexto: os pedidos da própria conversa

def _conversa(tmp_path, registros, nome="sessao-abc.jsonl"):
    arq = tmp_path / "app" / "projects" / "C--proj" / nome
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in registros) + "\n", encoding="utf-8")
    return arq


def _owner(texto, **extra):
    return dict({"type": "user", "message": {"role": "user", "content": texto}}, **extra)


def test_pedidos_da_conversa_devolve_os_4_ultimos_na_ordem_e_cortados_em_600(tmp_path):
    arq = _conversa(tmp_path, [
        _owner("primeiro pedido do owner sobre o cadastro de corretor"),
        _owner("segundo pedido do owner sobre a rota do boleto"),
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "resposta do assistente, que nunca entra"}]}},
        _owner("terceiro pedido do owner sobre o deploy da homologacao"),
        _owner("quarto pedido " + ("muito longo " * 80)),
        _owner("quinto pedido do owner sobre a segunda via"),
    ])
    pedidos = _mod().pedidos_da_conversa(arq)
    assert len(pedidos) == 4 and pedidos[0].startswith("segundo pedido") and pedidos[-1].startswith("quinto pedido")
    assert len(pedidos[2]) == 600


def test_pedidos_da_conversa_fica_so_com_o_que_o_owner_escreveu(tmp_path):
    arq = _conversa(tmp_path, [
        _owner("Ok"),
        _owner("Base directory for this skill: C:/x/skills/brainstorming # Brainstorming", isMeta=True),
        _owner("Stop hook feedback: [mss-spec] Antes de entregar — fonte ou não sei"),
        _owner("pedido de dentro de um ajudante, que nao e do owner", isSidechain=True),
        _owner([{"type": "tool_result", "content": "saida de ferramenta comprida que nao e pedido"}]),
        _owner("<command-message>mss-spec:tarefa</command-message> <command-name>/mss-spec:tarefa</command-name> "
               "<command-args>ajustar o texto do email de cobranca</command-args>"),
        _owner('<pasted_content id="77"> conteudo colado pelo owner sobre o boleto vencido </pasted_content id="77">'),
        _owner([{"type": "text", "text": "pedido em bloco de texto <system-reminder>lembrete do app</system-reminder> sobre o relatorio mensal"}]),
    ])
    assert _mod().pedidos_da_conversa(arq) == [
        "ajustar o texto do email de cobranca",
        "conteudo colado pelo owner sobre o boleto vencido",
        "pedido em bloco de texto sobre o relatorio mensal",
    ]


def test_pedidos_da_conversa_sem_arquivo_ou_com_linha_torta_nao_da_erro(tmp_path):
    mod = _mod()
    assert mod.pedidos_da_conversa(tmp_path / "nao-existe.jsonl") == []
    assert mod.pedidos_da_conversa(None) == []
    arq = tmp_path / "torta.jsonl"
    arq.write_text('{"type": "user"\nnao e json\n' + json.dumps(_owner("pedido inteiro depois da linha torta do arquivo")) + "\n",
                   encoding="utf-8")
    assert mod.pedidos_da_conversa(arq) == ["pedido inteiro depois da linha torta do arquivo"]


def test_arquivo_da_conversa_vem_do_numero_da_sessao(tmp_path):
    mod = _mod()
    arq = _conversa(tmp_path, [_owner("um pedido qualquer do owner nesta conversa")])
    amb = {"CLAUDE_CODE_SESSION_ID": "sessao-abc", "CLAUDE_CONFIG_DIR": str(tmp_path / "app")}
    assert mod.arquivo_da_conversa(amb) == arq
    assert mod.arquivo_da_conversa({"CLAUDE_CONFIG_DIR": str(tmp_path / "app")}) is None
    assert mod.arquivo_da_conversa(dict(amb, CLAUDE_CODE_SESSION_ID="outra-sessao")) is None
    assert mod.arquivo_da_conversa(dict(amb, CLAUDE_CODE_SESSION_ID="../*")) is None, "número de sessão não é padrão de busca"


# ------------------------------------------------------------------ linha de comando: buscar

def _buscar_cli(args, raiz, tmp_path, conversa=None):
    casa = tmp_path / "casa"
    casa.mkdir(exist_ok=True)
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8",
               CLAUDE_CONFIG_DIR=str(tmp_path / "app"))
    for chave in ("MSS_MEMORIA_TABELA", "CLAUDE_CODE_SESSION_ID"):
        env.pop(chave, None)
    if conversa:
        env["CLAUDE_CODE_SESSION_ID"] = conversa
    r = subprocess.run([sys.executable, str(SCRIPT), "buscar", *args, "--sem-git"], cwd=str(raiz), env=env,
                       capture_output=True, timeout=120)
    return r.returncode, r.stdout.decode("utf-8", "ignore"), casa / "mss-spec" / "memoria.sqlite3"


def test_cli_buscar_com_os_padroes_monta_a_tabela_e_devolve_os_dois_blocos(tmp_path):
    codigo, saida, tabela = _buscar_cli(["segunda via do boleto"], _projeto(tmp_path), tmp_path)
    assert codigo == 0 and tabela.is_file(), saida
    assert "Anotações (1)" in saida and "memory/project_boleto.md" in saida and "Documentos (" in saida


def test_cli_buscar_sem_texto_usa_o_ultimo_pedido_e_os_3_anteriores(tmp_path):
    raiz = _projeto(tmp_path)
    _conversa(tmp_path, [
        _owner("pedido antigo demais falando do ornitorrinco, que fica de fora"),
        _owner("preciso emitir a segunda via do boleto do corretor"),
        _owner("e depois ver o plano da rota girafa que ficou pronto"),
        _owner("tambem quero conferir o dominio tartaruga no to-do"),
        _owner("e isso tudo funciona mesmo no ambiente de hoje?"),
    ])
    _grava(raiz, "docs/bicho.md", "# Bicho\n\n## Parte\no ornitorrinco so aparece neste documento\n")
    codigo, saida, _ = _buscar_cli([], raiz, tmp_path, conversa="sessao-abc")
    assert codigo == 0, saida
    for esperado in ("memory/project_boleto.md", "docs/superpowers/plans/2026-09-01-boleto.md", "to-dolist.md"):
        assert esperado in saida, saida
    assert "docs/bicho.md" not in saida, "o 5º pedido pra trás não entra no contexto"


def test_cli_buscar_com_texto_busca_so_o_texto(tmp_path):
    raiz = _projeto(tmp_path)
    _conversa(tmp_path, [_owner("preciso emitir a segunda via do boleto do corretor")])
    codigo, saida, _ = _buscar_cli(["tartaruga"], raiz, tmp_path, conversa="sessao-abc")
    assert codigo == 0 and "to-dolist.md" in saida and "project_boleto" not in saida, saida


def test_cli_buscar_ve_o_arquivo_que_mudou_por_fora(tmp_path):
    raiz = _projeto(tmp_path)
    _buscar_cli(["boleto"], raiz, tmp_path)
    _grava(raiz, "docs/novo-por-fora.md", "# Novo\n\n## Parte\nchegou pelo git pull falando do flamingo\n")
    codigo, saida, _ = _buscar_cli(["flamingo"], raiz, tmp_path)
    assert codigo == 0 and "docs/novo-por-fora.md" in saida, saida


def test_cli_buscar_sem_achado_sai_com_1_e_manda_pros_arquivos(tmp_path):
    codigo, saida, _ = _buscar_cli(["xilofone inexistente"], _projeto(tmp_path), tmp_path)
    assert codigo == 1 and "memory/MEMORY.md" in saida and "nada" in saida.lower(), saida


def test_cli_buscar_sem_texto_e_sem_conversa_sai_com_1(tmp_path):
    codigo, saida, _ = _buscar_cli([], _projeto(tmp_path), tmp_path)
    assert codigo == 1 and "memory/MEMORY.md" in saida, saida


def test_cli_buscar_com_a_tabela_indisponivel_sai_com_2_e_manda_pros_arquivos(tmp_path, capsys):
    raiz, tabela, mod = _montado(tmp_path)
    _grava(raiz, "to-dolist.md", "# To-do\n\n- item novo\n")
    outro = sqlite3.connect(str(tabela))
    outro.execute("BEGIN EXCLUSIVE")
    try:
        codigo = mod.main(["buscar", "boleto", "--proj", str(raiz), "--tabela", str(tabela), "--sem-git"])
    finally:
        outro.rollback()
        outro.close()
    saida = capsys.readouterr().out
    assert codigo == 2 and "memory/MEMORY.md" in saida and "indisponível" in saida, saida
