"""Memória em tabela, parte 2 (0.56.0): a tabela se atualiza sozinha e a busca vai nela primeiro.

Por que existe: a parte 1 entregou um modo manual (`/mss-spec:memory tabela`) e o owner recusou comando pra
lembrar — "vai fazer se perder quando eu perguntar" (caso F-057). Decisões 13 a 22 de
docs/specs/memoria-em-tabela.md: grava-se no arquivo e a tabela acompanha; busca-se na tabela e, se precisar,
nos arquivos; a busca usa os pedidos anteriores da conversa e devolve 30 linhas curtas em dois blocos.
"""
import sqlite3

from test_memoria_tabela import _grava, _mod, _projeto, _repo, _sql


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
