"""Memória em tabela, parte 2 (0.56.0): a tabela se atualiza sozinha e a busca vai nela primeiro.

Por que existe: a parte 1 entregou um modo manual (`/mss-spec:memory tabela`) e o owner recusou comando pra
lembrar — "vai fazer se perder quando eu perguntar" (caso F-057). Decisões 13 a 22 de
docs/specs/memoria-em-tabela.md: grava-se no arquivo e a tabela acompanha; busca-se na tabela e, se precisar,
nos arquivos; a busca usa os pedidos anteriores da conversa e devolve 30 linhas curtas em dois blocos.

Camadas (2026-11-18, `docs/decisoes.md`): o projeto e o arquivo da conversa são um dicionário (`Disco`, sem git) e
a tabela é um SQLite `:memory:` que sobrevive entre as conexões (`BancoNaMemoria`); o modo `buscar` da linha de
comando roda pela função dele. O git de verdade (o que perguntar a ele quando um arquivo muda, o dono que fica, o
ignorado que muda) fica num teste só, num repositório montado uma vez; o processo python, num teste só.
"""
import argparse
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "templates" / "memoria_tabela.py"
BASE = REPO.parent / "memoria-busca-que-nao-existe"          # absoluto, nunca criado
APP = BASE / "app"

NOTA = ("---\nname: project-boleto\ndescription: O boleto vem do CRM e nao do portal\n"
        "gatilho: quando emitir segunda via\nmetadata:\n  type: project\n---\n\n"
        "A segunda via usa a tabela TB_BOLETO.\n\n<private>segredo-xyz</private>\n")
EVALS = ("# Falhas\n\n| id | data | gatilho | classe | guardrail | status |\n|---|---|---|---|---|---|\n"
         "| F-001 | 2026-09-29 | quando emitir boleto sem conferir | premissa não-dita | conferir o CRM antes | aberto |\n")
HTML = ("<html><head><style>p{color:red}</style></head><body><h2>Deploy</h2>"
        "<p>Publicar no ambiente <b>orquidea</b>.</p><script>var x=1</script></body></html>")
ARQUIVOS = {
    "CLAUDE.md": "# {titulo} — objetivo em uma frase\n",
    "memory/MEMORY.md": "- **Geral** → [subíndice](indice/geral.md) — 1 memórias\n",
    "memory/indice/geral.md": ("# Geral\n\n- **quando mexer no boleto do corretor** → [Boleto vem do CRM]"
                               "(../project_boleto.md) — gancho do indice\n"),
    "memory/project_boleto.md": NOTA,
    "memory/DIARIO.md": ("# Diário\n\n## 2026-10-01\n\n- [boleto-no-crm] Sessao sobre o boleto no CRM → "
                         "sessions/2026-10-01-boleto-no-crm.md\n"),
    "memory/sessions/2026-10-01-boleto-no-crm.md": ("# 2026-10-01 — boleto\n\n## Conversamos\n"
                                                    "- falamos do boleto zebra\n\n## Pivôs\n- trocamos de rota\n"),
    "docs/decisoes.md": "# Decisões\n\n- 2026-09-30 — **usar a fila X em vez de Y** — porque Z.\n",
    "docs/EVALS.md": EVALS,
    "docs/specs/boleto.md": "# Boleto\n\n## Estado atual\nA rota /boleto devolve o PDF.\n\n## Histórico\n- 2026-09-01 — criado.\n",
    "docs/superpowers/plans/2026-09-01-boleto.md": "# Plano\n\n## Tarefas\n1. fazer a rota girafa\n",
    "docs/superpowers/MAPA.md": "# Mapa\n\n## Onde estamos\nna branch do boleto hipopotamo\n",
    "docs/ARQUITETURA.md": ("# Arquitetura\n\n## Visão\ntexto da visao do sistema.\n\n## Banco\n"
                            "tabela TB_BOLETO fica no schema dbo.\n"),
    "docs/guia.html": HTML,
    "to-dolist.md": "# To-do\n\n- comprar o dominio tartaruga\n",
    ".env": "SENHA=abc123\n",
    "docs/variaveis.txt": "TOKEN=zzz999\n",
}


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("memoria_tabela", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ o projeto, a conversa e a tabela em memória

class Disco:
    """O projeto e a pasta do app em memória, com os métodos do `DiscoReal`: sem git (`git` devolve None), a
    "data" de cada arquivo é um contador que sobe a cada gravação, e conta o que foi lido."""

    def __init__(self):
        self.dados, self.versao, self.lidos, self.gits = {}, {}, 0, 0

    def gravar(self, p, texto):
        self.dados[Path(p)] = texto.encode("utf-8") if isinstance(texto, str) else texto
        self.versao[Path(p)] = self.versao.get(Path(p), 0) + 1

    def apagar(self, p):
        del self.dados[Path(p)]

    def eh_arquivo(self, p):
        return Path(p) in self.dados

    def ler_bytes(self, p):
        self.lidos += 1
        try:
            return self.dados[Path(p)]
        except KeyError:
            raise FileNotFoundError(str(p)) from None

    def ler_texto(self, p):
        return self.ler_bytes(Path(p)).decode("utf-8", "replace")

    def arquivos(self, raiz, pasta):
        base = Path(raiz) / pasta
        return [p.relative_to(raiz).as_posix() for p in self.dados if base in p.parents]

    def pastas_em(self, base):
        base = Path(base)
        filhos = {base / p.relative_to(base).parts[0] for p in self.dados if base in p.parents}
        if not filhos:
            raise FileNotFoundError(str(base))
        return sorted(filhos)

    def marca(self, p):
        return (len(self.dados[Path(p)]), self.versao[Path(p)]) if Path(p) in self.dados else None

    def git(self, raiz, *args):
        self.gits += 1
        return None

    def conversas(self, pasta):
        return []

    def lidas_ate(self, raiz):
        return ""


class _SemFechar:
    """A conexão do banco em memória: `close` não fecha (senão a tabela some)."""

    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass

    def __getattr__(self, nome):
        return getattr(self._conn, nome)


class BancoNaMemoria:
    """A tabela num SQLite `:memory:` — os métodos do `BancoReal`. `presa=True` simula a tabela aberta em outro
    programa."""

    def __init__(self, presa=False):
        self.conn, self.criado, self.presa = sqlite3.connect(":memory:"), False, presa

    def __str__(self):
        return "(tabela em memória)"

    def existe(self):
        return self.criado

    def preparar(self):
        pass

    def conectar(self, timeout):
        if self.presa:
            raise sqlite3.OperationalError("database is locked")
        self.criado = True
        return _SemFechar(self.conn)

    def sql(self, consulta, args=()):
        return self.conn.execute(consulta, args).fetchall()


def _projeto(disco, pasta="alfa", titulo="Projeto Alfa"):
    raiz = BASE / pasta
    for rel, texto in ARQUIVOS.items():
        disco.gravar(raiz / rel, texto.replace("{titulo}", titulo))
    return raiz


@pytest.fixture()
def disco():
    return Disco()


@pytest.fixture()
def banco():
    return BancoNaMemoria()


def _atualizar(mod, disco, banco, raiz):
    return mod.atualizar(raiz, banco, usar_git=False, disco=disco)


def _montado(mod, disco, banco, pasta="alfa", titulo="Projeto Alfa"):
    raiz = _projeto(disco, pasta, titulo)
    mod.montar(raiz, banco, usar_git=False, disco=disco)
    return raiz


# ------------------------------------------------------------------ conferência rápida e atualizar

def test_atualizar_monta_quando_a_tabela_nao_existe(mod, disco, banco):
    r = _atualizar(mod, disco, banco, _projeto(disco))
    assert r is not None and r.novos == 10 and banco.existe()


def test_atualizar_em_dia_nao_le_arquivo_nem_chama_o_git(mod, disco, banco):
    raiz = _projeto(disco)
    _atualizar(mod, disco, banco, raiz)
    disco.lidos = disco.gits = 0
    assert mod.atualizar(raiz, banco, disco=disco) is None
    assert (disco.lidos, disco.gits) == (0, 0), "tabela em dia: não era pra ler arquivo nem chamar o git"


def test_atualizar_pega_arquivo_mudado_novo_e_apagado(mod, disco, banco):
    raiz = _projeto(disco)
    _atualizar(mod, disco, banco, raiz)
    disco.gravar(raiz / "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    disco.gravar(raiz / "memory/feedback_novo.md", "---\nname: feedback-novo\ndescription: nota nova\n---\n\ncorpo novo tucano\n")
    disco.apagar(raiz / "docs/guia.html")
    r = _atualizar(mod, disco, banco, raiz)
    assert (r.novos, r.refeitos, r.removidos) == (1, 1, 1)
    assert banco.sql("SELECT arq FROM memoria WHERE memoria MATCH 'tucano'") == [("memory/feedback_novo.md",)]
    assert _atualizar(mod, disco, banco, raiz) is None, "atualizada: a conferência seguinte não refaz nada"


def test_linha_de_controle_e_uma_por_projeto_e_nao_conta_como_memoria(mod, disco, banco):
    raiz = _projeto(disco)
    r = mod.montar(raiz, banco, usar_git=False, disco=disco)
    disco.gravar(raiz / "to-dolist.md", "# To-do\n\n- outro item\n")
    mod.montar(raiz, banco, usar_git=False, disco=disco)
    assert "controle" not in r.por_tipo
    assert banco.sql("SELECT count(*) FROM memoria WHERE tipo = 'controle'")[0][0] == 1
    assert mod.status(raiz, banco, usar_git=False, disco=disco).linhas == 12


def test_tabela_da_parte_1_sem_linha_de_controle_e_conferida_uma_vez(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    banco.conn.execute("DELETE FROM memoria WHERE tipo = 'controle'")
    r = _atualizar(mod, disco, banco, raiz)
    assert r is not None and (r.novos, r.refeitos, r.removidos, r.iguais) == (0, 0, 0, 10)
    assert _atualizar(mod, disco, banco, raiz) is None


def test_trocar_o_nome_do_projeto_e_visto_pela_conferencia(mod, disco, banco):
    raiz = _projeto(disco)
    _atualizar(mod, disco, banco, raiz)
    disco.gravar(raiz / "CLAUDE.md", "# Projeto Gama — outro objetivo\n")
    assert _atualizar(mod, disco, banco, raiz) is not None
    assert {p for (p,) in banco.sql("SELECT DISTINCT projeto FROM memoria")} == {"Projeto Gama"}


# ------------------------------------------------------------------ buscar e formatar

def _muitos_guias(disco, raiz, quantos=40):
    for i in range(quantos):
        disco.gravar(raiz / f"docs/guias/guia-{i:02d}.md",
                     f"# Guia {i}\n\n## Parte\ntexto sobre a capivara numero {i}\n\n## Outra\nmais capivara neste guia\n")


def test_buscar_acha_a_anotacao_e_o_documento_do_pedido(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    achados = mod.buscar(raiz, "como emitir a segunda via do boleto pelo CRM", tabela=banco)
    arqs = [a["arq"] for a in achados]
    assert "memory/project_boleto.md" in arqs and "docs/specs/boleto.md" in arqs
    assert set(achados[0]) == {"arq", "tipo", "ponteiro", "titulo", "trecho"}


def test_buscar_devolve_30_linhas_de_30_arquivos_diferentes(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    _muitos_guias(disco, raiz)
    mod.montar(raiz, banco, usar_git=False, disco=disco)
    achados = mod.buscar(raiz, "onde fica a capivara", tabela=banco)
    assert len(achados) == 30 and len({a["arq"] for a in achados}) == 30
    assert len(mod.buscar(raiz, "onde fica a capivara", tabela=banco, limite=5)) == 5


def test_buscar_so_ve_o_projeto_da_janela(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    outro = _projeto(disco, "beta", "Projeto Beta")
    disco.gravar(outro / "docs/segredo-do-beta.md", "# Beta\n\n## Parte\no ornitorrinco mora so no beta\n")
    mod.montar(outro, banco, usar_git=False, disco=disco)
    assert mod.buscar(raiz, "cade o ornitorrinco", tabela=banco) == []
    assert [a["arq"] for a in mod.buscar(outro, "cade o ornitorrinco", tabela=banco)] == ["docs/segredo-do-beta.md"]


def test_palavra_longa_casa_pelo_comeco_e_acento_nao_atrapalha(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    disco.gravar(raiz / "docs/servidor.md", "# Servidor\n\n## Parte\na configuração fica no painel\n")
    mod.montar(raiz, banco, usar_git=False, disco=disco)
    assert "docs/servidor.md" in [a["arq"] for a in mod.buscar(raiz, "quais configuracoes existem", tabela=banco)]


def test_contexto_da_conversa_entra_na_busca(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    assert mod.buscar(raiz, "e isso funciona mesmo?", tabela=banco) == []
    com = mod.buscar(raiz, "e isso funciona mesmo?", contexto=["como emitir a segunda via do boleto"], tabela=banco)
    assert "memory/project_boleto.md" in [a["arq"] for a in com]


def test_pedido_sem_palavra_util_ou_com_simbolos_nao_da_erro(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    assert mod.buscar(raiz, "?? e a de", tabela=banco) == []
    achados = mod.buscar(raiz, 'boleto "AND" OR NEAR( * ^ : -- \' ) [x]', tabela=banco)
    assert "memory/project_boleto.md" in [a["arq"] for a in achados]


def test_buscar_pode_deixar_tipos_de_fora_e_nunca_devolve_a_linha_de_controle(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    todos = mod.buscar(raiz, "emitir boleto sem conferir", tabela=banco)
    assert "falha" in {a["tipo"] for a in todos} and "controle" not in {a["tipo"] for a in todos}
    assert "falha" not in {a["tipo"] for a in mod.buscar(raiz, "emitir boleto sem conferir", tabela=banco,
                                                         sem_tipos=("falha",))}


def test_buscar_sem_tabela_da_erro_tratavel_e_nao_cria_a_tabela(mod, disco, banco):
    with pytest.raises(sqlite3.Error):
        mod.buscar(_projeto(disco), "boleto", tabela=banco)
    assert not banco.existe(), "sem tabela a busca tem de avisar, nunca devolver vazio calada nem criar"
    with pytest.raises(sqlite3.Error):
        mod.buscar(_projeto(disco), "boleto", tabela=BASE / "nao-existe.sqlite3")
    assert not BASE.exists()


def test_formatar_separa_anotacoes_de_documentos_em_linhas_curtas(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    disco.gravar(raiz / "docs/longo.md", "# Longo\n\n## " + ("titulo comprido " * 12) + "\nboleto " + ("palavra\n" * 80) + "\n")
    mod.montar(raiz, banco, usar_git=False, disco=disco)
    texto = mod.formatar(mod.buscar(raiz, "segunda via do boleto no CRM zebra", tabela=banco))
    blocos = texto.split("Documentos (")
    assert texto.startswith("Anotações (1)") and len(blocos) == 2
    assert "- anotacao | memory/project_boleto.md | project boleto | " in blocos[0]
    assert "memory/sessions/2026-10-01-boleto-no-crm.md" in blocos[1], "diário fica com os documentos"
    assert "docs/specs/boleto.md:3" in blocos[1], "documento aponta arquivo e linha"
    for linha in [l for l in texto.splitlines() if l.startswith("- ")]:
        _tipo, _ponteiro, titulo, trecho = linha[2:].split(" | ", 3)
        assert len(titulo) <= 80 and len(trecho) <= 170, linha


def test_formatar_diz_quando_um_bloco_veio_vazio(mod, disco, banco):
    raiz = _montado(mod, disco, banco)
    texto = mod.formatar(mod.buscar(raiz, "dominio tartaruga", tabela=banco))
    assert "Anotações (0)" in texto and "(nenhuma)" in texto and "to-dolist.md" in texto


# ------------------------------------------------------------------ contexto: os pedidos da própria conversa

def _owner(texto, **extra):
    return dict({"type": "user", "message": {"role": "user", "content": texto}}, **extra)


def _jsonl(registros):
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in registros) + "\n"


def _conversa(disco, registros, nome="sessao-abc.jsonl"):
    arq = APP / "projects" / "C--proj" / nome
    disco.gravar(arq, _jsonl(registros))
    return arq


def test_pedidos_da_conversa_devolve_os_4_ultimos_na_ordem_e_cortados_em_600(mod):
    pedidos = mod.pedidos_do_texto(_jsonl([
        _owner("primeiro pedido do owner sobre o cadastro de corretor"),
        _owner("segundo pedido do owner sobre a rota do boleto"),
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "resposta do assistente, que nunca entra"}]}},
        _owner("terceiro pedido do owner sobre o deploy da homologacao"),
        _owner("quarto pedido " + ("muito longo " * 80)),
        _owner("quinto pedido do owner sobre a segunda via"),
    ]))
    assert len(pedidos) == 4 and pedidos[0].startswith("segundo pedido") and pedidos[-1].startswith("quinto pedido")
    assert len(pedidos[2]) == 600


def test_pedidos_da_conversa_fica_so_com_o_que_o_owner_escreveu(mod):
    assert mod.pedidos_do_texto(_jsonl([
        _owner("Ok"),
        _owner("Base directory for this skill: C:/x/skills/brainstorming # Brainstorming", isMeta=True),
        _owner("Stop hook feedback: [mss-spec] Antes de entregar — fonte ou não sei"),
        _owner("pedido de dentro de um ajudante, que nao e do owner", isSidechain=True),
        _owner([{"type": "tool_result", "content": "saida de ferramenta comprida que nao e pedido"}]),
        _owner("<command-message>mss-spec:tarefa</command-message> <command-name>/mss-spec:tarefa</command-name> "
               "<command-args>ajustar o texto do email de cobranca</command-args>"),
        _owner('<pasted_content id="77"> conteudo colado pelo owner sobre o boleto vencido </pasted_content id="77">'),
        _owner([{"type": "text", "text": "pedido em bloco de texto <system-reminder>lembrete do app</system-reminder> sobre o relatorio mensal"}]),
    ])) == [
        "ajustar o texto do email de cobranca",
        "conteudo colado pelo owner sobre o boleto vencido",
        "pedido em bloco de texto sobre o relatorio mensal",
    ]


def test_o_pedido_atual_entra_mesmo_curto_e_o_curto_do_meio_fica_fora(mod):
    """`/mss-spec:duvida e o deploy?` é pedido de 11 letras: se o corte de tamanho o tirasse, a busca sairia com
    os pedidos velhos e sem o que o owner acabou de perguntar."""
    assert mod.pedidos_do_texto(_jsonl([
        _owner("preciso emitir a segunda via do boleto do corretor"),
        _owner("pode seguir"),
        _owner("<command-message>mss-spec:duvida</command-message> <command-args>e o deploy?</command-args>"),
        _owner("Base directory for this skill: C:/x/skills/qualquer # Corpo de skill", isMeta=True),
    ])) == ["preciso emitir a segunda via do boleto do corretor", "e o deploy?"]


def test_pedidos_da_conversa_sem_arquivo_ou_com_linha_torta_nao_da_erro(mod, disco):
    assert mod.pedidos_da_conversa(APP / "nao-existe.jsonl", disco=disco) == []
    assert mod.pedidos_da_conversa(None, disco=disco) == []
    torta = APP / "torta.jsonl"
    disco.gravar(torta, '{"type": "user"\nnao e json\n' + json.dumps(_owner("pedido inteiro depois da linha torta do arquivo")) + "\n")
    assert mod.pedidos_da_conversa(torta, disco=disco) == ["pedido inteiro depois da linha torta do arquivo"]


def test_arquivo_da_conversa_vem_do_numero_da_sessao(mod, disco):
    arq = _conversa(disco, [_owner("um pedido qualquer do owner nesta conversa")])
    amb = {"CLAUDE_CODE_SESSION_ID": "sessao-abc", "CLAUDE_CONFIG_DIR": str(APP)}
    assert mod.arquivo_da_conversa(amb, disco) == arq
    assert mod.arquivo_da_conversa({"CLAUDE_CONFIG_DIR": str(APP)}, disco) is None
    assert mod.arquivo_da_conversa(dict(amb, CLAUDE_CODE_SESSION_ID="outra-sessao"), disco) is None
    assert mod.arquivo_da_conversa(dict(amb, CLAUDE_CODE_SESSION_ID="../*"), disco) is None, \
        "número de sessão não é padrão de busca"
    assert mod.arquivo_da_conversa(dict(amb, CLAUDE_CONFIG_DIR=str(BASE / "sem-app")), disco) is None


# ------------------------------------------------------------------ o modo buscar da linha de comando

def _buscar(mod, disco, banco, raiz, *texto, conversa=None, capsys):
    a = argparse.Namespace(texto=list(texto), conversa="", sem_git=True, limite=mod.LIMITE_BUSCA)
    amb = {"CLAUDE_CONFIG_DIR": str(APP)}
    if conversa:
        amb["CLAUDE_CODE_SESSION_ID"] = conversa
    codigo = mod._modo_buscar(raiz, banco, a, disco=disco, ambiente=amb)
    return codigo, capsys.readouterr().out


def test_modo_buscar_monta_a_tabela_e_devolve_os_dois_blocos(mod, disco, banco, capsys):
    codigo, saida = _buscar(mod, disco, banco, _projeto(disco), "segunda via do boleto", capsys=capsys)
    assert codigo == 0 and banco.existe(), saida
    assert "Anotações (1)" in saida and "memory/project_boleto.md" in saida and "Documentos (" in saida


def test_modo_buscar_sem_texto_usa_o_ultimo_pedido_e_os_3_anteriores(mod, disco, banco, capsys):
    raiz = _projeto(disco)
    _conversa(disco, [
        _owner("pedido antigo demais falando do ornitorrinco, que fica de fora"),
        _owner("preciso emitir a segunda via do boleto do corretor"),
        _owner("e depois ver o plano da rota girafa que ficou pronto"),
        _owner("tambem quero conferir o dominio tartaruga no to-do"),
        _owner("e isso tudo funciona mesmo no ambiente de hoje?"),
    ])
    disco.gravar(raiz / "docs/bicho.md", "# Bicho\n\n## Parte\no ornitorrinco so aparece neste documento\n")
    codigo, saida = _buscar(mod, disco, banco, raiz, conversa="sessao-abc", capsys=capsys)
    assert codigo == 0, saida
    for esperado in ("memory/project_boleto.md", "docs/superpowers/plans/2026-09-01-boleto.md", "to-dolist.md"):
        assert esperado in saida, saida
    assert "docs/bicho.md" not in saida, "o 5º pedido pra trás não entra no contexto"


def test_modo_buscar_com_texto_busca_so_o_texto(mod, disco, banco, capsys):
    raiz = _projeto(disco)
    _conversa(disco, [_owner("preciso emitir a segunda via do boleto do corretor")])
    codigo, saida = _buscar(mod, disco, banco, raiz, "tartaruga", conversa="sessao-abc", capsys=capsys)
    assert codigo == 0 and "to-dolist.md" in saida and "project_boleto" not in saida, saida


def test_modo_buscar_ve_o_arquivo_que_mudou_por_fora(mod, disco, banco, capsys):
    raiz = _projeto(disco)
    _buscar(mod, disco, banco, raiz, "boleto", capsys=capsys)
    disco.gravar(raiz / "docs/novo-por-fora.md", "# Novo\n\n## Parte\nchegou pelo git pull falando do flamingo\n")
    codigo, saida = _buscar(mod, disco, banco, raiz, "flamingo", capsys=capsys)
    assert codigo == 0 and "docs/novo-por-fora.md" in saida, saida


def test_modo_buscar_sem_achado_sai_com_1_e_manda_pros_arquivos(mod, disco, banco, capsys):
    codigo, saida = _buscar(mod, disco, banco, _projeto(disco), "xilofone inexistente", capsys=capsys)
    assert codigo == 1 and "memory/MEMORY.md" in saida and "nada" in saida.lower(), saida


def test_modo_buscar_sem_texto_e_sem_conversa_sai_com_1(mod, disco, banco, capsys):
    codigo, saida = _buscar(mod, disco, banco, _projeto(disco), capsys=capsys)
    assert codigo == 1 and "memory/MEMORY.md" in saida, saida


def test_modo_buscar_com_a_tabela_indisponivel_sai_com_2_e_manda_pros_arquivos(mod, disco, capsys):
    codigo, saida = _buscar(mod, disco, BancoNaMemoria(presa=True), _projeto(disco), "boleto", capsys=capsys)
    assert codigo == 2 and "memory/MEMORY.md" in saida and "indisponível" in saida, saida


# ------------------------------------------------------------------ ligação ao kit (prosa dos comandos)

CHAMADA = 'memoria_tabela.py" buscar'


def _comando(nome):
    return (REPO / "commands" / f"{nome}.md").read_text(encoding="utf-8")


def test_as_tres_portas_buscam_na_tabela_e_tem_os_arquivos_como_reserva():
    for nome in ("tarefa", "bug", "duvida"):
        texto = _comando(nome)
        assert CHAMADA in texto, f"{nome}.md: o passo de memória não manda rodar a busca da tabela"
        passo = " ".join(texto.split(CHAMADA, 1)[1][:1400].split())        # a prosa quebra linha onde quiser
        assert "não resuma o pedido" in passo, f"{nome}.md: falta dizer que o pedido não se resume (medido: piora)"
        assert "abra só as que servem" in passo, f"{nome}.md: falta dizer que o assistente escolhe quais abrir"
        assert "memory/MEMORY.md" in passo and "memory/indice/" in passo, f"{nome}.md: falta a reserva nos arquivos"
        assert "entre aspas" in passo, f"{nome}.md: falta o que fazer quando a busca não acha a conversa"


def test_memory_buscar_usa_a_tabela_e_cai_no_indice_se_precisar():
    modo = _comando("memory").split("## Modo: buscar", 1)[1].split("\n## ", 1)[0]
    assert CHAMADA in modo, "memory.md: o modo buscar não usa a tabela"
    assert modo.index(CHAMADA) < modo.index('memoria_indice.py" buscar'), "memory.md: a tabela vem primeiro"
    assert "Anotações" in modo and "Documentos" in modo


def test_ninguem_manda_o_owner_montar_a_tabela():
    """Sem comando pra lembrar (decisão 13): fora do uso interno e do procedimento de troca de máquina, nenhum
    comando do kit manda rodar o `montar`."""
    for arq in sorted((REPO / "commands").glob("*.md")):
        texto = arq.read_text(encoding="utf-8")
        if arq.name == "memory.md":
            texto = texto.split("## Uso interno: tabela", 1)[0]
        assert 'memoria_tabela.py" montar' not in texto, f"{arq.name} manda montar a tabela à mão"


# ------------------------------------------------------------------ o git de verdade e o processo (repositório montado uma vez)

def _grava(raiz, rel, texto):
    p = raiz / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")


def _git(raiz, *args, autor="Fulana Teste", data="2026-08-15T10:00:00"):
    env = dict(os.environ, GIT_AUTHOR_NAME=autor, GIT_AUTHOR_EMAIL="fulana@exemplo.test", GIT_AUTHOR_DATE=data,
               GIT_COMMITTER_NAME=autor, GIT_COMMITTER_EMAIL="fulana@exemplo.test", GIT_COMMITTER_DATE=data)
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")


def _sql(tabela, consulta, args=()):
    c = sqlite3.connect(str(tabela))
    try:
        return c.execute(consulta, args).fetchall()
    finally:
        c.close()


@pytest.fixture(scope="module")
def pasta(tmp_path_factory):
    base = tmp_path_factory.mktemp("memoria_tabela_busca")
    for nome in ("repo", "cli"):
        for rel, texto in ARQUIVOS.items():
            _grava(base / nome, rel, texto.replace("{titulo}", "Projeto Alfa"))
    raiz = base / "repo"
    _grava(raiz, ".gitignore", ".env\ndocs/escondido.md\n")
    _grava(raiz, "docs/escondido.md", "# Escondido\n\n## Parte\nconteudo ignorado pelo git papagaio\n")
    _git(raiz, "init", "-q", "--template=")
    _git(raiz, "add", ".gitignore", "CLAUDE.md", "memory", "docs", "to-dolist.md")
    _git(raiz, "commit", "-q", "-m", "inicio")
    (base / "casa").mkdir()
    return base


def test_git_de_verdade_so_pelo_que_mudou(mod, pasta, monkeypatch):
    raiz, tabela = pasta / "repo", pasta / "t.sqlite3"
    # montar do zero traz dono e data de tudo; a decisão mantém a data que já traz
    mod.atualizar(raiz, tabela)
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'memory/project_boleto.md'") == [
        ("Fulana Teste", "2026-08-15")]
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'docs/decisoes.md'") == [
        ("Fulana Teste", "2026-09-30")], "decisão mantém a data que já traz"
    # o arquivo ignorado pelo git que muda não vira remontagem sem fim
    _grava(raiz, "docs/escondido.md", "# Escondido\n\n## Parte\nmudou e continua ignorado arara\n")
    r = mod.atualizar(raiz, tabela)
    assert r is not None and (r.novos, r.refeitos, r.removidos) == (0, 0, 0)
    assert not _sql(tabela, "SELECT 1 FROM memoria WHERE memoria MATCH 'arara'")
    assert mod.atualizar(raiz, tabela) is None
    # o git só é perguntado pelo arquivo que mudou, e o dono fica; pendência é só do relatório do montar
    chamadas, original = [], mod._git

    def espia(raiz_git, *args):
        chamadas.append(args)
        return original(raiz_git, *args)
    monkeypatch.setattr(mod, "_git", espia)
    _grava(raiz, "docs/specs/boleto.md", "# Boleto\n\n## Estado atual\nAgora devolve o PDF em anexo jacare.\n")
    mod.atualizar(raiz, tabela)
    logs = [a for a in chamadas if "log" in a]
    assert len(logs) == 1 and "docs/specs/boleto.md" in logs[0] and "memory" not in logs[0], logs
    assert not [a for a in chamadas if "status" in a or "rev-list" in a]
    assert _sql(tabela, "SELECT DISTINCT dono, data FROM memoria WHERE arq = 'docs/specs/boleto.md'") == [
        ("Fulana Teste", "2026-08-15")]
    # só com arquivo apagado, nada de git log
    chamadas.clear()
    (raiz / "docs" / "guia.html").unlink()
    assert mod.atualizar(raiz, tabela).removidos == 1 and not [a for a in chamadas if "log" in a]


def test_processo_buscar_com_os_padroes_monta_a_tabela_e_devolve_os_dois_blocos(pasta):
    casa = pasta / "casa"
    env = dict(os.environ, USERPROFILE=str(casa), HOME=str(casa), PYTHONIOENCODING="utf-8",
               CLAUDE_CONFIG_DIR=str(pasta / "app"))
    for chave in ("MSS_MEMORIA_TABELA", "CLAUDE_CODE_SESSION_ID"):
        env.pop(chave, None)
    r = subprocess.run([sys.executable, str(SCRIPT), "buscar", "segunda via do boleto", "--sem-git"],
                       cwd=str(pasta / "cli"), env=env, capture_output=True, timeout=120)
    saida = r.stdout.decode("utf-8", "ignore")
    assert r.returncode == 0 and (casa / "mss-spec" / "memoria.sqlite3").is_file(), saida
    assert "Anotações (1)" in saida and "memory/project_boleto.md" in saida and "Documentos (" in saida
