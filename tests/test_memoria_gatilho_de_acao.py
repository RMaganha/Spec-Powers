"""Gatilho de ação em toda anotação que é regra sobre o que o assistente FAZ (decisão 24 do owner, 2026-11-11).

O owner manteve a decisão de 2026-09-25 (não buscar por palavras a cada comando) e fechou "consultar a memória
pela ação" como AMPLIAR o que já existe: a anotação de regra (`type: feedback`) declara `gatilho_comando:` ou
`gatilho_resposta:` — ou diz por que não tem (`sem_gatilho_de_acao: <motivo>`). Na captura isso é cobrado: o
`memoria_indice.py verificar` acusa, pelo nome, a anotação NOVA (ainda sem commit) que não cumpre; as antigas não
viram problema — entram numa lista (`fila`) que o owner aprova de uma vez.
"""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
COBRANCA = "regra de ação sem gatilho de ação"


def _mod():
    spec = importlib.util.spec_from_file_location("memoria_indice", REPO / "templates" / "memoria_indice.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _acao():
    spec = importlib.util.spec_from_file_location("_memoria_de_acao", REPO / "hooks" / "_memoria_de_acao.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _anotacao(raiz, nome, tipo="feedback", extra=""):
    (raiz / "memory" / f"{nome}.md").write_text(
        f"---\nname: {nome}\ndescription: descrição longa o bastante de {nome}\n"
        f"gatilho: quando acontecer a situação observável de {nome}\n{extra}metadata:\n  type: {tipo}\n---\n\ncorpo\n",
        encoding="utf-8")


@pytest.fixture()
def proj(tmp_path):
    raiz = tmp_path / "proj"
    (raiz / "memory" / "indice").mkdir(parents=True)
    (raiz / "memory" / "MEMORY.md").write_text(
        "# Memória\n\n- **Geral** → [subíndice](indice/geral.md) — 0 memórias · quando: qualquer coisa\n", encoding="utf-8")
    (raiz / "memory" / "indice" / "geral.md").write_text("# Geral\n", encoding="utf-8")
    return raiz


def _cobrancas(mod, raiz, novas):
    return [p for p in mod.verificar(raiz / "memory", sem_commit=set(novas)) if p.startswith(COBRANCA)]


# --- a cobrança na captura (o `verificar`) ----------------------------------------------------------------

def test_anotacao_nova_de_regra_sem_gatilho_de_acao_e_acusada_pelo_nome(proj):
    _anotacao(proj, "feedback_nova_regra")
    achados = _cobrancas(_mod(), proj, {"feedback_nova_regra.md"})
    assert len(achados) == 1 and "feedback_nova_regra.md" in achados[0]
    for campo in ("gatilho_comando:", "gatilho_resposta:", "sem_gatilho_de_acao:"):
        assert campo in achados[0], f"a cobrança não diz que `{campo}` resolve"


@pytest.mark.parametrize("extra", [
    "gatilho_comando: \\bseed\\.py\\b\n",
    "gatilho_resposta: (?i)rode o seed\n",
    "sem_gatilho_de_acao: vale pra toda resposta — o gatilho não separaria nada\n",
])
def test_anotacao_nova_com_gatilho_de_acao_ou_com_o_motivo_passa(proj, extra):
    _anotacao(proj, "feedback_nova_regra", extra=extra)
    assert _cobrancas(_mod(), proj, {"feedback_nova_regra.md"}) == []


@pytest.mark.parametrize("tipo", ["project", "reference", "procedimento", "user"])
def test_so_a_anotacao_de_regra_e_cobrada(proj, tipo):
    """Fato, referência e passo a passo disparam pelo pedido do owner: o `gatilho:` comum já serve."""
    _anotacao(proj, "project_um_fato", tipo=tipo)
    assert _cobrancas(_mod(), proj, {"project_um_fato.md"}) == []


def test_anotacao_obsoleta_nao_e_cobrada(proj):
    _anotacao(proj, "feedback_velha", extra="obsoleta: 2026-11-01 — superada\n")
    assert _cobrancas(_mod(), proj, {"feedback_velha.md"}) == []


def test_antiga_nao_vira_problema_e_entra_na_lista_do_owner(proj):
    """Decisão do owner: pras antigas, a lista das que deveriam ter e não têm — ele aprova de uma vez. Projeto
    com 100 anotações antigas não pode ganhar 100 problemas no `verificar` (o assistente sairia corrigindo sozinho)."""
    mod = _mod()
    _anotacao(proj, "feedback_antiga")
    _anotacao(proj, "feedback_antiga_com_motivo", extra="sem_gatilho_de_acao: já tem hook próprio\n")
    _anotacao(proj, "project_fato_antigo", tipo="project")
    assert _cobrancas(mod, proj, set()) == []
    assert mod.fila(proj / "memory")["sem_gatilho_de_acao"] == ["feedback_antiga.md"]


def test_regex_quebrado_no_gatilho_de_acao_e_acusado(proj):
    """O hook ignora regex inválido calado (falha aberta): sem a acusação, a anotação nunca dispara e ninguém vê."""
    _anotacao(proj, "feedback_regex", extra="gatilho_comando: ([\n")
    probs = [p for p in _mod().verificar(proj / "memory", sem_commit=set()) if p.startswith("regex quebrado")]
    assert len(probs) == 1 and "feedback_regex.md" in probs[0] and "gatilho_comando" in probs[0]


def test_sem_git_ninguem_e_nova(proj):
    """Fora de repositório não dá pra saber o que é novo: nada é cobrado pelo nome, tudo vai pra lista."""
    mod = _mod()
    _anotacao(proj, "feedback_solta")
    assert [p for p in mod.verificar(proj / "memory") if p.startswith(COBRANCA)] == []
    assert mod.fila(proj / "memory")["sem_gatilho_de_acao"] == ["feedback_solta.md"]


@pytest.mark.skipif(not shutil.which("git"), reason="precisa do git pra distinguir a anotação nova da antiga")
def test_no_repositorio_a_nova_e_a_que_ainda_nao_tem_commit(proj):
    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.t", *args], cwd=proj, check=True,
                       capture_output=True)
    _anotacao(proj, "feedback_antiga")
    git("init", "-q")
    git("add", "memory")
    git("commit", "-q", "-m", "base")
    _anotacao(proj, "feedback_nova")
    achados = [p for p in _mod().verificar(proj / "memory") if p.startswith(COBRANCA)]
    assert len(achados) == 1 and "feedback_nova.md" in achados[0]


def test_cli_verificar_avisa_das_antigas_sem_virar_problema(proj, capsys):
    _anotacao(proj, "feedback_antiga")
    (proj / "memory" / "indice" / "geral.md").write_text(
        "# Geral\n\n- **quando acontecer a situação** → [Antiga](../feedback_antiga.md) — resumo\n", encoding="utf-8")
    mod = _mod()
    mod.verificar(proj / "memory", aplicar=True)                       # acerta o N do topo
    assert mod.main(["verificar", "--proj", str(proj)]) == 0
    saida = capsys.readouterr().out
    assert "1 anotação" in saida and "sem gatilho de ação" in saida and "fila" in saida
    assert "owner" in saida, "o aviso não diz que a lista das antigas é pro owner aprovar"


def test_cli_fila_lista_as_antigas_sem_gatilho_de_acao(proj, capsys):
    _anotacao(proj, "feedback_antiga")
    assert _mod().main(["fila", "--proj", str(proj)]) == 0
    saida = capsys.readouterr().out
    assert "sem gatilho de ação (1)" in saida and "feedback_antiga.md" in saida


# --- o próprio kit (dogfood): as 75 anotações cumprem, e os 21 gatilhos aprovados casam o caso real -----------

def test_toda_regra_do_kit_tem_gatilho_de_acao_ou_o_motivo():
    mod = _mod()
    assert mod.fila(REPO / "memory")["sem_gatilho_de_acao"] == []
    assert [p for p in mod.verificar(REPO / "memory") if p.startswith((COBRANCA, "regex quebrado"))] == []


# (anotação, lado, o que TEM de casar, o que NÃO pode casar) — lista aprovada pelo owner em 2026-11-11
APROVADOS = [
    ("feedback_feature_a_partir_da_master", "comando",
     ["git switch -c feature/consultar-pela-acao", "git status -sb && git switch -c feature/x",
      "git checkout main && git checkout -b fix/y"],
     ["git status -sb", "git switch main", "grep -rn 'git switch -c' docs/", "git checkout -- arquivo.py"]),
    ("feedback_trabalho_pendente_do_owner_nunca_commitar", "comando",
     ["git stash", "git stash push -m guardado", "cd repo && git stash pop"],
     ["git stash list", "git status", "echo git stash"]),
    ("feedback_perguntar_em_vez_de_vasculhar", "comando",
     ["find /c/Users/rmaganha /c/Ronaldo -maxdepth 8 -type f -name 'x'", "find ~ -name '*.env'",
      "Get-ChildItem C:\\Users\\rmaganha -Recurse -Filter *.sqlite3"],
     ["find ~/.claude/skills/mss-spec -iname '*nova-feature*'", "find . -name '*.py'", "find docs -type f",
      "Get-ChildItem memory -Filter *.md"]),
    ("feedback_so_dependencia_estavel", "comando",
     ["pip install bpmn-python", "python -m pip install requests==2.0", "npm install mantine", "uv add httpx"],
     ["pip install -r requirements.txt", "npm install", "pip list", "echo pip install x"]),
    ("feedback_avaliar_tool_externa_ideia_vs_stack", "comando",
     ["git clone https://github.com/x/y", "claude mcp add ferramenta", "npx -y @x/servidor"],
     ["git status", "git log --oneline", "grep clone arquivo"]),
    ("project_docker_build_fortigate", "comando",
     ["docker build -t app .", "docker compose build", "docker compose up -d --build", "docker-compose build api"],
     ["docker ps", "docker compose up -d", "docker logs app"]),
    ("project_troca_por_script_em_arquivo_crlf", "comando",
     ["python - <<'PY'\nfrom pathlib import Path\np = Path('a.md')\np.write_text(p.read_text().replace('x', 'y'))\nPY",
      "python -c \"import re,io; t=open('a').read(); open('a','w').write(re.sub('x','y',t))\""],
     ["python -m pytest tests/ -q", "python templates/memoria_tabela.py buscar \"x\"",
      "python -c \"print('a'.replace('a', 'b'))\""]),
    ("feedback_validacao_ui_deterministica", "comando",
     ["npx playwright test", "python -m playwright install", "python -c \"from selenium import webdriver\""],
     ["python -m pytest tests/ -q", "grep -rn playwright docs/"]),
    ("project_versao_em_dois_manifestos", "comando",
     ["git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md",
      "git add CHANGELOG.md .claude-plugin/marketplace.json"],
     ["git add CHANGELOG.md", "cat .claude-plugin/plugin.json", "git diff -- .claude-plugin/plugin.json"]),
    ("project_rode_a_peca_com_os_padroes_antes_de_dizer_pronto", "resposta",
     ["Pronto: suíte 1341 verdes.", "Tudo 100% verde, pode integrar.", "A suíte inteira verde depois da mudança."],
     ["Vou rodar a suíte agora.", "O teste ficou vermelho; corrigindo."]),
    ("feedback_comando_pro_owner_passo_a_passo", "resposta",
     ["Faça assim:\n```bash\ngit switch main\ngit merge --no-ff feature/x\n```", "Agora rode `git push origin main`."],
     ["**1. Publicar**\n```bash\ngit push origin main\n```\n**2. Conferir**\n```bash\ngit status -sb\n```",
      "Rodei o `git status -sb` e a pasta está limpa."]),
    ("feedback_texto_pronto_pra_colar", "resposta",
     ["Abra uma conversa nova pelo + e cole o texto abaixo.", "Cole isto na conversa nova:"],
     ["Colei a saída do teste abaixo.", "A conversa nova lê o MAPA na partida."]),
    ("feedback_nao_encerrar_com_pergunta", "resposta",
     ["Gravei os três arquivos.\n\nQuer que eu rode a suíte agora?", "Feito. Posso seguir com o merge?"],
     ["Quer que eu rode a suíte? Rodei: 1341 verdes.", "Você mantém essa decisão ou revê?"]),
    ("feedback_medir_antes_de_afirmar_ganho", "resposta",
     ["Resumir o pedido em poucas palavras acha melhor.", "Com isso há um ganho de 30% no tempo de partida."],
     ["Medi: 43,8% entre os 10.", "O teste passou."]),
    ("feedback_simular_a_seco_com_dados_reais", "resposta",
     ["Proponho mover as linhas fechadas pro histórico e aplicar no Whats só movendo.",
      "Minha proposta: o rodízio roda sozinho nos outros projetos."],
     ["Proponho renomear a função.", "Li os arquivos do Whats, só leitura."]),
    ("feedback_regra_unica_em_vez_de_config", "resposta",
     ["Proponho uma flag `MSS_X=1` pra ligar o comportamento.", "Sugiro deixar o limite configurável por projeto."],
     ["Proponho uma regra única, sem exceção.", "A flag `--aplicar` já existe."]),
    ("feedback_teto_que_sempre_estoura_e_estrutura", "resposta",
     ["O jeito mais simples é subir o teto do MAPA pra 8 KB.", "Dá pra aumentar o teto da partida."],
     ["O MAPA está acima do teto.", "O teto é 6 KB."]),
    ("feedback_decidir_por_topicos_um_de_cada_vez", "resposta",
     ["1. Qual a data fim?\n2. Qual o prêmio base?\n3. Entra fim de semana?\n4. Quem aprova?"],
     ["Você mantém ou revê?", "1. Aprova as 21?\n2. As 13 ficam como estão?"]),
    ("feedback_um_comando_com_o_porque", "resposta",
     ["Rode o `/mss-spec:doctor` nesse projeto.", "Digite /mss-spec:upgrade na conversa nova."],
     ["O `/mss-spec:doctor` mede e o `/mss-spec:upgrade` conserta.", "Li o commands/doctor.md."]),
    ("feedback_pesquisar_fonte_primaria_antes_de_desenhar", "resposta",
     ["A documentação diz que o hook recebe o texto da resposta.", "O Claude Code não carrega `CLAUDE.md` da pasta do plugin."],
     ["Abri a documentação e colei o trecho abaixo.", "O hook devolveu a resposta."]),
    ("feedback_diagnostico_disciplinado", "resposta",
     ["Cole aqui a saída dos dois comandos e eu interpreto.", "Me mande o print das últimas linhas do log."],
     ["Colei a saída abaixo.", "O log mostra o erro na linha 12."]),
]


def _regex_do_kit(nome, lado):
    for n, _, _, rx in _acao().memorias(str(REPO), lado):
        if n == nome:
            return rx
    return None


@pytest.mark.parametrize("nome,lado,casa,nao_casa", APROVADOS, ids=[a[0] for a in APROVADOS])
def test_gatilho_aprovado_casa_o_caso_real_e_nao_casa_o_vizinho(nome, lado, casa, nao_casa):
    rx = _regex_do_kit(nome, lado)
    assert rx is not None, f"{nome} não declara gatilho de {lado} (ou o regex não compila)"
    for texto in casa:
        assert rx.search(texto), f"{nome}: devia casar {texto!r}"
    for texto in nao_casa:
        assert not rx.search(texto), f"{nome}: não devia casar {texto!r}"


def test_sao_os_21_aprovados_mais_os_5_que_ja_existiam():
    acao = _acao()
    com = {n for lado in ("comando", "resposta") for n, _, _, _ in acao.memorias(str(REPO), lado)}
    assert {a[0] for a in APROVADOS} <= com
    assert len(com) == 26, sorted(com)


# --- a captura manda cobrar (wiring do comando-prosa) -----------------------------------------------------

def test_a_captura_cobra_o_gatilho_de_acao_da_anotacao_de_regra():
    texto = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    captura = texto.split("## Modo: capturar", 1)[1].split("\n## Modo:", 1)[0]
    assert "sem_gatilho_de_acao:" in captura and "gatilho_comando:" in captura and "gatilho_resposta:" in captura
    assert re.search(r"regra de ação sem gatilho de ação", captura), "a captura não cita a acusação do `verificar`"
    assert "Se o gatilho é uma **ação sua**" not in captura, "o gatilho de ação continua opcional no texto da captura"


def test_o_molde_da_memoria_explica_os_tres_campos():
    molde = (REPO / "templates" / "MEMORY.md").read_text(encoding="utf-8")
    for campo in ("gatilho_comando:", "gatilho_resposta:", "sem_gatilho_de_acao:"):
        assert campo in molde, f"templates/MEMORY.md não explica `{campo}`"
