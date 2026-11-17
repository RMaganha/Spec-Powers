"""Smoke-test do próprio kit mss-spec — o "plano de teste base" deste repo.

Pega as regressões que já aconteceram (referência morta, ff4d384) e as que o review
apontou: todo caminho citado nos commands/skills tem que existir de verdade.

Nota: a resolução de ${CLAUDE_PLUGIN_ROOT} em runtime (plugin carregado via junction)
não dá pra testar aqui — este smoke valida que, RESOLVIDA a raiz, todos os alvos
existem. O teste manual da junction é rodar /mss-spec:kickoff num projeto de teste.
"""
import json
import re
from pathlib import Path
from _texto_kit import texto_do_kit

REPO = Path(__file__).resolve().parent.parent

PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`\"')\]]+)")
TEMPLATE_REF = re.compile(r"`(templates/[^`<>*]+)`")


def _command_files():
    files = sorted((REPO / "commands").glob("*.md"))
    assert files, "nenhum comando encontrado em commands/"
    return files


def test_plugin_root_refs_existem():
    """Todo ${CLAUDE_PLUGIN_ROOT}/<caminho> citado em commands/ e skills/ existe no repo."""
    faltando = []
    for md in [*_command_files(), *(REPO / "skills").rglob("*.md")]:
        for rel in PLUGIN_ROOT_REF.findall(md.read_text(encoding="utf-8")):
            if not (REPO / rel).exists():
                faltando.append(f"{md.relative_to(REPO)} -> {rel}")
    assert not faltando, "referências mortas:\n" + "\n".join(faltando)


def test_templates_citados_existem():
    """Todo `templates/...` citado nos commands existe (os itens da lista do kickoff/ambiente)."""
    faltando = []
    for md in _command_files():
        for rel in TEMPLATE_REF.findall(md.read_text(encoding="utf-8")):
            if not (REPO / rel).exists():
                faltando.append(f"{md.relative_to(REPO)} -> {rel}")
    assert not faltando, "templates citados que não existem:\n" + "\n".join(faltando)


def test_manifestos_validos_e_coerentes():
    plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "mss-spec"
    assert plugin["version"] == market["version"], "versões do plugin e do marketplace divergem"
    assert any(p["name"] == plugin["name"] for p in market["plugins"])


def test_commands_tem_frontmatter():
    for md in _command_files():
        texto = md.read_text(encoding="utf-8")
        assert texto.startswith("---"), f"{md.name}: sem frontmatter"
        assert "description:" in texto.split("---")[1], f"{md.name}: frontmatter sem description"


def test_compose_templates_sao_yaml_validos():
    yaml = __import__("pytest").importorskip("yaml")
    for nome in ("docker-compose.yml", "docker-compose.office.yml"):
        texto = (REPO / "templates" / "docker" / nome).read_text(encoding="utf-8")
        # <servico> é placeholder — troca por um nome válido só pra parsear
        doc = yaml.safe_load(texto.replace("<servico>", "app"))
        assert "app" in doc["services"], nome


def test_perguntar_nao_vasculhar():
    """A face de LEITURA da fronteira: pra chegar a outro projeto (ou a qualquer fato que o
    owner tem na cabeça — caminho, nome de container/variável, qual arquivo é o compose),
    PERGUNTAR. Varrer o disco é lento, queima tokens e termina em chute — reclamado 2x.
    Mora no molde do CLAUDE.md (viaja pra todo projeto) e onde o kit manda abrir outro repo."""
    for rel in ("templates/CLAUDE.md", "skills/precedentes-msig/SKILL.md",
                "commands/precedentes.md"):
        low = (texto_do_kit() if rel == "templates/CLAUDE.md"
               else (REPO / rel).read_text(encoding="utf-8")).lower()
        assert "não vasculhe" in low or "não vasculhar" in low, \
            f"{rel} não carrega a regra 'pergunte, não vasculhe'"
        assert "pergunte" in low, f"{rel} não manda perguntar o caminho ao owner"
        assert "find" in low, f"{rel} não nomeia a varredura de disco que está proibida"


def test_comando_referenciado_existe_guardrail():
    """Guardrail GERAL (Camada 2 da regressão do frontend): o CLAUDE.md ensina que um
    /mss-spec:<x> referenciado — mesmo sem aparecer na lista de invocáveis, porque é
    disable-model-invocation — EXISTE como commands/<x>.md e deve ser LIDO, nunca declarado
    inexistente nem chutado de memória. É o que impede a mesma confusão com qualquer comando
    (não só o frontend). Sempre-ativo (CLAUDE.md) e chega a projeto existente via upgrade (mescla).
    """
    claude = texto_do_kit()
    low = claude.lower()
    assert "disable-model-invocation" in claude, \
        "CLAUDE.md não explica por que o comando não aparece na lista (disable-model-invocation)"
    assert "commands/" in claude, "CLAUDE.md não diz que o comando existe como commands/<x>.md"
    assert "leia o arquivo" in low, "CLAUDE.md não manda LER o arquivo do comando referenciado"
    assert "não existe" in low, "CLAUDE.md não proíbe concluir que o comando 'não existe'"
    # upgrade mescla CLAUDE.md → a regra nova chega a projeto que já nasceu (ex.: Energy)
    upgrade = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    assert "CLAUDE.md" in upgrade and "MESCLA" in upgrade, \
        "upgrade não mescla CLAUDE.md (a regra nova não chegaria a projeto existente)"


def test_upgrade_respeita_preexistente():
    """O freio: a categoria 1 do upgrade hoje sobrescreve docker-compose.yml/Dockerfile SOZINHO.
    Num brownfield isso mata a infra do projeto — risco destampado no design da análise. Com a
    lista 'não nasceu do kit' do docs/ARQUITETURA.md, esses arquivos passam a PERGUNTAR."""
    up = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    low = up.lower()
    assert "ARQUITETURA.md" in up, "upgrade.md não consulta a lista do docs/ARQUITETURA.md"
    assert "não nasceu do kit" in low, "upgrade.md não reconhece o arquivo que não nasceu do kit"
    assert "brownfield" in low, "upgrade.md não trata o caso brownfield na categoria 1"


# ---- infra MSIG × infra própria (0.18.0) -----------------------------------
# O kit nasceu dentro da MSIG e ASSUMIA a infra corporativa em todo projeto: copiava a CA do
# FortiGate, o compose do escritório, punha proxy no `.env` e oferecia o `get_connection.py`
# das bases MSIG — e o `doctor` cobrava proxy/CA/rede que, num projeto de fora, não existem.
# Agora é PERGUNTA na constituição, e a resposta manda.

def test_infra_pergunta_no_kickoff():
    """CA1 — o kickoff pergunta na entrevista e grava a resposta no CLAUDE.md do projeto."""
    kick = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    low = kick.lower()
    assert "infra msig" in low or "arquitetura msig" in low, \
        "kickoff não pergunta se o projeto segue a infra MSIG"
    assert "própria" in low, "kickoff não oferece a alternativa 'infra própria'"
    assert "**infra:**" in low, "kickoff não grava a resposta na linha `Infra:` do CLAUDE.md"


def test_premissa_com_fonte():
    """CA1/CA2 — antes do OK do owner, o nova-feature declara o que está assumindo SEM ter sido dito,
    cada premissa com fonte (ou marcada `sem fonte`), as sem-fonte primeiro. Premissa derrubada vira
    caso no corpus de falhas, no fecho. Nasceu do F-011 (li 'sem harness' como 'raso basta')."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    low = nova.lower()
    assert "premissa" in low, "nova-feature não manda declarar premissas"
    assert "sem fonte" in low, "nova-feature não prevê a premissa SEM FONTE (a que quebra)"
    assert "antes do ok" in low or "antes de pedir o ok" in low, \
        "nova-feature não posiciona as premissas ANTES do OK do owner"
    # as sem-fonte vêm primeiro (é a ordem que faz o owner ver o risco de cara)
    assert "primeiro" in low, "nova-feature não manda listar as `sem fonte` primeiro"
    # passar no destilado antes de listar: se está lá, não é premissa, é fato com fonte
    for alvo in ("MAPA.md", "MEMORY.md", "docs/EVALS.md"):
        assert alvo in nova, f"nova-feature não manda consultar o destilado ({alvo}) antes de listar"
    # premissa derrubada vira caso no corpus, no fecho
    assert "derrubada" in low, "nova-feature não trata a premissa DERRUBADA pelo owner"
    assert "/mss-spec:memory capturar" in nova, \
        "nova-feature não manda a premissa derrubada virar caso via /mss-spec:memory capturar"
    # não inventar premissa pra preencher o bloco
    assert "não invente" in low or "não inventar" in low, \
        "nova-feature não proíbe inventar premissa quando não há nenhuma não-dita"


def _rules_do_molde():
    d = REPO / "templates" / "rules"
    assert d.is_dir(), "falta templates/rules/ (regras path-scoped do Claude Code)"
    arqs = sorted(d.glob("*.md"))
    assert arqs, "templates/rules/ está vazia"
    return arqs


def test_rules_path_scoped_bem_formadas():
    """CA7 — regra path-scoped só carrega se tiver `paths:` no frontmatter; e tem que ser CURTA
    (ela entra no contexto toda vez que um arquivo casa) e apontar a memória de origem."""
    for md in _rules_do_molde():
        txt = md.read_text(encoding="utf-8")
        assert txt.startswith("---"), f"{md.name}: sem frontmatter"
        fm = txt.split("---")[1]
        assert re.search(r"(?m)^paths:", fm), f"{md.name}: sem `paths:` — não carrega sozinha"
        assert re.search(r'(?m)^\s+-\s+"', fm), f"{md.name}: `paths:` sem nenhum glob"
        n = len(txt.splitlines())
        assert n <= 40, f"{md.name}: {n} linhas (teto 40 — regra path-scoped é curta por design)"
        assert "memory/" in txt, f"{md.name}: não aponta a memória de origem (memory/<arquivo>.md)"


def test_ponteiro_memoria_nativa():
    """CA9 — o índice que o Claude Code auto-carrega é o da pasta NATIVA; o durável é o do repo.
    Depois do resgate, a nativa vira um ponteiro de 1 linha pro índice do repo, e o doctor confere.
    Sem isso, memória durável fica fora da sessão sem ninguém perceber (caso F-012)."""
    mem = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    assert "ponteiro" in mem.lower(), "memory.md (resgatar) não deixa o ponteiro na pasta nativa"
    assert "~/.claude/projects/" in mem, "memory.md não nomeia a pasta nativa"
    assert "auto-carreg" in mem.lower() or "carrega sozinho" in mem.lower(), \
        "memory.md não explica POR QUE o ponteiro existe (só a nativa auto-carrega)"
    doctor = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    assert "ponteiro" in doctor.lower(), "doctor não checa o ponteiro da memória nativa"
    assert "memory/MEMORY.md" in doctor, "doctor não confere pra onde o ponteiro aponta"


def test_pedido_com_mais_de_um_assunto():
    """CA17 — pedido que nomeia 2+ assuntos ("evals E context engineering") exige cobertura
    declarada de CADA um. Nasceu do F-013: entreguei a metade de recall e chamei de completo,
    e o owner teve que apontar duas vezes o que faltava."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    low = nova.lower()
    assert "mais de um assunto" in low, \
        "nova-feature não trata o pedido que nomeia mais de um assunto"
    assert "cada" in low and "sem peça" in low, \
        "nova-feature não exige dizer qual peça serve cada assunto (e qual ficou sem)"


def _indice_memoria_completo() -> str:
    """Topo + subíndices: desde o índice em dois níveis, a linha de cada memória mora em memory/indice/."""
    partes = [(REPO / "memory" / "MEMORY.md").read_text(encoding="utf-8")]
    partes += [p.read_text(encoding="utf-8") for p in sorted((REPO / "memory" / "indice").glob("*.md"))]
    return "\n".join(partes)


def test_divergir_wiring():
    """Anti-ancoragem no design (ideia do repo `adhd`; stack npm rejeitado — ver decisoes.md),
    montada em 3 camadas: (1) piso SEMPRE-ATIVO no brainstorm do nova-feature — as 2-3 abordagens
    vêm de frames deliberadamente distintos e cada uma tem a armadilha sedutora marcada;
    (2) comando opt-in /mss-spec:divergir (subagentes paralelos ISOLADOS, 1 frame cada; a janela
    é o crítico) com gate de AUTO-PROPOSTA no nova-feature — decisão aberta E cara de reverter →
    o assistente propõe sozinho, anunciando o custo (o owner não precisa lembrar que existe);
    (3) memória com gatilho cobre as janelas que não passam pelo nova-feature."""
    # (2) o comando existe e descreve o mecanismo
    cmd = REPO / "commands" / "divergir.md"
    assert cmd.exists(), "falta commands/divergir.md"
    div = cmd.read_text(encoding="utf-8")
    low = div.lower()
    assert "subagente" in low, "divergir.md não dispara subagentes (a divergência é paralela)"
    assert "isolad" in low, "divergir.md não exige isolamento entre os ramos (é o que mata a ancoragem)"
    assert "frame" in low, "divergir.md não usa frames (ângulos deliberadamente distintos)"
    assert "armadilha" in low, "divergir.md não manda o crítico marcar a armadilha sedutora"
    assert "custo" in low, "divergir.md não declara o custo (5-10× uma resposta direta)"
    assert "precedente" in low, "divergir.md não subordina a divergência ao precedente MSIG (reuso vence)"
    # (1) + (2) as pontes no nova-feature: piso sempre-ativo e auto-proposta com critério
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    nlow = nova.lower()
    assert "frames" in nlow, "nova-feature não exige frames distintos nas abordagens do brainstorm"
    assert "armadilha sedutora" in nlow, "nova-feature não manda marcar a armadilha sedutora por abordagem"
    assert "/mss-spec:divergir" in nova, "nova-feature não aponta o /mss-spec:divergir"
    assert "cara de reverter" in nlow, "nova-feature não carrega o critério de auto-proposta (aberta + cara de reverter)"
    # (3) a memória com gatilho existe e está no índice (formato validado pelo test_memoria_gatilho)
    assert (REPO / "memory" / "feedback_divergir_antes_de_convergir.md").exists(), \
        "falta memory/feedback_divergir_antes_de_convergir.md (a rede fora do nova-feature)"
    idx = _indice_memoria_completo()
    assert "feedback_divergir_antes_de_convergir.md" in idx, "a memória do divergir está fora do índice"


def test_desenho_em_termos_do_owner():
    """F-010 — apresentei um desenho usando um termo que EU inventei ("chave MSIG") e a conversa
    travou até eu trocar por uma tabela do-que-acontece-onde. Termo que o owner não usou soa como
    coisa que já existe, e o manda caçar o que não está lá — custa uma rodada inteira."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    low = nova.lower()
    assert "batiz" in low, "nova-feature não proíbe batizar conceito que o owner não nomeou"
    assert "tabela" in low and "exemplo concreto" in low, \
        "nova-feature não manda apresentar o desenho por tabela/exemplo concreto antes de nomear"
    assert "f-010" in low, "o guardrail não aponta o caso de origem no corpus"


def test_diagnostico_wiring():
    """F-015 — 6 rodadas perdidas num 503 (deploy MSS-SSC, 2026-08-26): loop de hipóteses de
    plataforma enquanto a causa (caminho relativo no main.py) aparecia num diff contra o projeto
    de referência que o owner apontou desde o início; + 2 rodadas re-litigando uma App Setting
    correta quando a resposta era "reiniciar". A skill systematic-debugging existia e nunca foi
    invocada. Guardrail em camadas: regra crítica sempre-ativa no molde (dispara na hora 2, quando
    EVALS/memória já saíram do foco) + comando como alavanca do owner (o detector de loop mais
    confiável daquela sessão foi ele) + memória com gatilho + caso no corpus."""
    cmd = REPO / "commands" / "diagnostico.md"
    assert cmd.exists(), "falta commands/diagnostico.md"
    diag = cmd.read_text(encoding="utf-8")
    low = diag.lower()
    # o trilho: disciplina de skill, precedente-primeiro (boot incluso), condição real, fatos do owner
    assert "systematic-debugging" in diag, "diagnostico.md não invoca a superpowers:systematic-debugging"
    assert "precedente" in low and "diff completo" in low,         "diagnostico.md não manda o diff completo contra o precedente que funciona"
    assert "boot" in low, "diagnostico.md não inclui o código de boot/entrypoint no diff (só infra não basta)"
    assert "não se re-litiga" in low, "diagnostico.md não protege o fato afirmado pelo owner"
    assert "condição real" in low and "cwd" in low,         "diagnostico.md não exige reproduzir a condição REAL do ambiente (CWD/envs) — 'passou local' não prova"
    assert "um teste que discrimina" in low,         "diagnostico.md não impõe a economia de rodadas (1 pedido de evidência = 1 teste que discrimina)"
    # F-023 — "mandei o payload certo, voltou 200, API saudável" é UMA variante: exige a matriz do chamador
    assert "matriz de variantes" in low and "content-type" in low, \
        "diagnostico.md não exige a matriz de variantes que o chamador externo pode produzir (F-023)"
    assert "deploy inteiro" in low, "diagnostico.md não manda o diff cobrir o deploy inteiro, não só um arquivo (F-023)"
    # âncora no ponto de contágio: o diff abre outro projeto → read-only, reporte
    assert "somente-leitura" in low and "âncora" in low and "não conserte" in low,         "diagnostico.md manda abrir o precedente sem a fronteira da âncora (read-only; reporte)"
    assert "docs/EVALS.md" in diag, "diagnostico.md não fecha registrando o caso no corpus"
    # F-048: o diário (7 dias) e os ambientes entram ANTES da tabela de fatos
    assert "memory/DIARIO.md" in diag and "7 dias" in low, "diagnostico.md não lê o diário dos últimos 7 dias"
    assert "docs/AMBIENTES.md" in diag, "diagnostico.md não lê a seção do ambiente citado em docs/AMBIENTES.md"
    # regra sempre-ativa no molde (é o único mecanismo vivo na hora 2 de uma sessão longa)
    claude = texto_do_kit()
    clow = claude.lower()
    assert "systematic-debugging" in claude, "CLAUDE.md não manda invocar a systematic-debugging no bug"
    assert "diff completo" in clow, "CLAUDE.md não carrega o diff-antes-de-pedir-evidência"
    assert "não se re-litiga" in clow, "CLAUDE.md não carrega 'fato do owner não se re-litiga'"
    assert "/mss-spec:diagnostico" in claude, "CLAUDE.md não aponta o trilho /mss-spec:diagnostico"
    # o owner descobre a alavanca dele
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "/mss-spec:diagnostico" in leiame, "LEIA-ME não lista o /mss-spec:diagnostico"
    # memória com gatilho + caso no corpus (as camadas de registro)
    assert (REPO / "memory" / "feedback_diagnostico_disciplinado.md").exists(),         "falta memory/feedback_diagnostico_disciplinado.md"
    mem_idx = _indice_memoria_completo()
    assert "feedback_diagnostico_disciplinado.md" in mem_idx, "MEMORY.md não indexa a memória do diagnóstico"
    evals = (REPO / "docs" / "EVALS.md").read_text(encoding="utf-8")
    assert "F-015" in evals, "docs/EVALS.md não registra o caso F-015"


def test_suposicao_do_owner_nao_e_requisito():
    """F-019 — o owner escreveu "acho que até algo html funcionaria" e eu registrei como premissa
    "com fonte: você disse", fechando a decisão do MEIO da entrega na hesitação dele; cheguei a
    pôr o `.bpmn` do Bizagi em "fora de escopo" citando a frase. F-018, do mesmo dia: escrevi
    layout SVG à mão (tira de 4.000 px, 222 rótulos truncados) quando o kit já vendoriza
    biblioteca (`vis-network.min.js`) e o `bpmn-js` estava a um `npm view` de distância."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    low = nova.lower()
    assert "hesitação" in low or "hesitacao" in low, \
        "nova-feature não distingue suposição do owner de requisito"
    assert "acho que" in low, "a regra não cita a forma como a suposição chega ('acho que X')"
    assert "templates/vendor/" in nova, \
        "nova-feature não manda olhar o que o projeto já vendoriza antes de desenhar layout"
    for caso in ("F-018", "F-019"):
        assert caso in nova, f"a regra não aponta o caso {caso} do corpus"

    # e o kit tem de fato a lib vendorizada que o caso exige
    vendor = REPO / "templates" / "vendor"
    for ativo in ("bpmn-navigated-viewer.min.js", "bpmn-auto-layout.min.js", "bpmn-js.css"):
        assert (vendor / ativo).exists(), f"falta templates/vendor/{ativo}"


def test_azure_prd_wiring():
    """/mss-spec:azure-ambiente: receita Bicep da homologacao levada pra producao pelo pipeline com aprovacao.
    Spec: docs/specs/azure-ambiente.md."""
    cmd = (REPO / "commands" / "azure-ambiente.md").read_text(encoding="utf-8")
    for trecho in ("infra/main.bicep", "infra/hml.bicepparam", "infra/prd.bicepparam",
                   "infra/app-settings.json", "infra/app_settings.py", "what-if", "RG-MSSAI-DEV",
                   "RG-MSSAI-PRD", "Approvals and checks", "Run pipeline",
                   "templates/azure-ambiente/azure-pipelines-infra.yml", "templates/azure-ambiente/prd.bicepparam",
                   "templates/azure-ambiente/app_settings.py"):
        assert trecho in cmd, f"commands/azure-ambiente.md sem {trecho!r}"
    # o assistente nunca aplica a receita: quem cria e o pipeline com aprovacao do owner
    assert "az deployment group create" in cmd and "owner" in cmd.lower()
    # F-036: nada roda na maquina do owner contra o Azure — nem az login, nem what-if local
    assert "az login" not in cmd, "o comando voltou a exigir o Azure CLI na maquina do owner"
    assert "```bash\naz " not in cmd, "comando az pra rodar fora do pipeline"
    # F-036: App Settings fora do Bicep (appSettings substitui a colecao inteira e apagaria a senha real)
    assert "appSettings" in cmd and "substitui" in cmd
    # F-036: pipeline de codigo de producao nao e suposto — e conferido
    assert "pendência" in cmd.lower() and "trigger" in cmd
    ambiente = (REPO / "templates" / "AMBIENTE.md").read_text(encoding="utf-8")
    assert "/mss-spec:azure-ambiente" in ambiente, "AMBIENTE.md secao Azure nao aponta o comando"
    # dados de producao mapeados uma vez no kit (medidos no Whats) — o comando usa, nao pergunta
    # F-037: WEBSITE_DNS_SERVER existe em producao (portal), embora os documentos do Whats nao a citassem
    assert "`WEBSITE_DNS_SERVER=10.170.210.2` (o mesmo)" in ambiente
    for trecho in ("mss-ai-asp-prod-br", "VNET-MSSD-PRD", "SNET-WEB-AI-PRD", "WEBSITE_DNS_ALT_SERVER=168.63.129.16",
                   "resourceGroups/RG-MSSD-PRD/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-PRD"):
        assert trecho in ambiente, f"AMBIENTE.md secao 5 sem {trecho!r}"
    assert "não\npergunte" in cmd or "não pergunte" in cmd, "comando voltaria a perguntar o que o kit ja mapeia"
    assert "WEBSITE_DNS_ALT_SERVER" in cmd


def _estagios_azure_prd(doc):
    """Achata os estagios, inclusive os inseridos por `${{ if ... }}` (chave do mapping)."""
    saida = []
    for item in doc["stages"]:
        if "stage" in item:
            saida.append((None, item))
        else:
            (cond, lista), = item.items()
            saida.extend((cond, e) for e in lista)
    return saida


def test_azure_prd_pipeline_e_yaml_com_aprovacao():
    yaml = __import__("pytest").importorskip("yaml")
    texto = (REPO / "templates" / "azure-ambiente" / "azure-pipelines-infra.yml").read_text(encoding="utf-8")
    doc = yaml.safe_load(texto)
    assert "trigger: none" in texto, "pipeline de infra roda a mao, nao por push"
    (param,) = doc["parameters"]
    assert param["name"] == "ambiente" and param["values"] == ["hml", "prd"] and param["default"] == "hml"
    estagios = _estagios_azure_prd(doc)
    assert [e["stage"] for _, e in estagios] == ["Simular", "CriarHml", "Criar"]
    (cond_sim, simular), (cond_hml, criar_hml), (cond_criar, criar) = estagios
    # CriarHml so EXISTE no hml, sem aprovacao (homologacao nova); nunca altera uma que ja existe
    assert cond_hml and "parameters.ambiente" in cond_hml and "'hml'" in cond_hml
    assert "environment" not in criar_hml["jobs"][0]
    h = json.dumps(criar_hml, ensure_ascii=False)
    for trecho in ("az deployment group create", "infra/hml.bicepparam", "app_settings.py plataforma", "nada a criar"):
        assert trecho in h, f"CriarHml sem {trecho!r}"
    assert h.index("nada a criar") < h.index("deployment group create"), "a guarda vem antes de criar"
    assert h.index("deployment group create") < h.index("app_settings.py plataforma")
    # Simular roda nos dois; Criar so EXISTE no prd (removido na compilacao — estagio pulado por
    # `condition:` ainda pediria a aprovacao)
    assert cond_sim is None
    assert cond_criar and "parameters.ambiente" in cond_criar and "'prd'" in cond_criar
    s = json.dumps(simular, ensure_ascii=False)
    for trecho in ("az bicep build", "what-if", "IMAGEM", "linuxFxVersion", "app_settings.py conferir",
                   "${{ parameters.ambiente }}"):
        assert trecho in s, f"Simular sem {trecho!r}"
    assert "deployment group create" not in s and "aplicar" not in s
    assert criar["dependsOn"] == "Simular"
    job = criar["jobs"][0]
    assert job.get("environment") == "producao", "o botao de aprovacao mora no environment 'producao'"
    c = json.dumps(criar, ensure_ascii=False)
    for trecho in ("az deployment group create", "IMAGEM", "app_settings.py aplicar", "RG-MSSAI-PRD"):
        assert trecho in c or trecho in texto, f"Criar sem {trecho!r}"
    assert c.index("deployment group create") < c.index("app_settings.py aplicar"), \
        "as variaveis so podem ser gravadas depois de o Web App existir"


def test_azure_prd_conduz_em_6_etapas_com_um_pedido_por_vez():
    """F-038: no MSS-UTILS o owner se perdeu — o comando pedia aos pedacos, sem mapa nem 'onde estamos',
    aprovava arquivo por arquivo e descrevia teste interno. A conducao agora e regra do comando."""
    cmd = (REPO / "commands" / "azure-ambiente.md").read_text(encoding="utf-8")
    etapas = re.findall(r"^## Etapa (\d) de 6 — ", cmd, flags=re.M)
    assert etapas == ["1", "2", "3", "4", "5", "6"], f"etapas no comando: {etapas}"
    for trecho in ("Etapa X de 6", "O que preciso de você agora", "nada, sigo sozinho",
                   "uma aprovação por etapa", "proteção: N verdes", "export uma vez só",
                   "mensagem curta, sem linguagem técnica", "até 3 linhas", "sem a fonte",
                   "Hoje, publicar na `main` ainda\nnão atualiza produção. Criar isso é tarefa à parte."):
        assert trecho.lower() in cmd.lower(), f"comando sem a regra de conducao {trecho!r}"
    for tecnico in ("imageName", "webAppName"):
        assert tecnico not in cmd, f"termo tecnico {tecnico!r} voltaria pra fala com o owner"
    # a tabela do caminho inteiro vai na 1a mensagem, com as 6 etapas e quem faz cada uma
    tabela = cmd[cmd.index("| Etapa | O que é | Quem faz |"):]
    assert all(f"| {n} |" in tabela[:2000] for n in range(1, 7))
    # o .dockerignore: o Dockerfile costuma copiar a pasta inteira — a receita nao entra na imagem
    assert ".dockerignore" in cmd and "/infra/" in cmd and "/azure-pipelines*.yml" in cmd


def test_azure_prd_licoes_da_1a_producao_real():
    """MSS-UTILS em producao (2026-10-20): o que faltou ao comando, item a item da lista do owner."""
    cmd = (REPO / "commands" / "azure-ambiente.md").read_text(encoding="utf-8")
    low = cmd.lower()
    for trecho in (
        "<PROJETO>-INFRA", "Rename/move",                       # pipeline novo, separado, com nome
        "não precisa de nenhum comando git",                    # a branch ja foi enviada
        "**Permit**",                                           # permissao de uma vez so
        "vai dar erro de propósito",                            # 1a simulacao para nas variaveis
        "Receita + variáveis: o que mudaria", "View raw log",   # o item exato do log
        "Next: Resources",                                      # a tela do Run pipeline
        "Preciso da sua aprovação",                             # texto pronto pro aprovador
        "minúsculo",                                            # nome exato do ambiente producao
        "You do not have permissions to manage checks",         # sem permissao de aprovadores
        "Identidade do pipeline",                               # a identidade REAL recebe as permissoes
        "templates/azure-ambiente/permissoes-infra.md",              # chamado pronto pra infra
        "Vou enviar a branch", "não publica nada",              # avisa antes do envio
        "Chaves de acesso", "Regenerar", "Mostrar valores",     # de onde vem cada senha
        "/health", "Fluxo de log",                              # conferir depois de criar
        "sem `location`",                                       # BCP187 nas partes internas
    ):
        assert trecho.lower() in low, f"comando sem {trecho!r}"
    assert "nunca `networkConfig`" in cmd, "networkConfig exige permissao de alterar a subnet"
    assert "?" not in cmd.split("## Etapa 4 de 6")[1].split("## Etapa 5 de 6")[0].replace("?**", ""), \
        "etapa 4 voltaria a usar ? para valor que falta"
    infra = (REPO / "templates" / "azure-ambiente" / "permissoes-infra.md").read_text(encoding="utf-8")
    for trecho in ("--assignee-object-id", "MSIG-VNet-Join-Subnet", "MSIG-VNet-ServiceEndpoint-Subnet",
                   "joinViaServiceEndpoint", '--role "Reader"', "Identidade do pipeline", "uma vez só",
                   # homologacao nova: as mesmas permissoes na rede de homologacao
                   "resourceGroups/RG-MSSD-DEVQA/providers/Microsoft.Network/virtualNetworks/VNET-MSSD-DEVQA/subnets/SNET-WEB-AI-DEVQA",
                   "## 4. Permissões na rede de homologação"):
        assert trecho in infra, f"permissoes-infra.md sem {trecho!r}"
    assert "subnets/write" not in infra.replace("NÃO dar `subnets/write`", ""), "nunca pedir permissao de alterar a subnet"
    ambiente = (REPO / "templates" / "AMBIENTE.md").read_text(encoding="utf-8")
    assert "permissões da conexão do pipeline em produção" in ambiente.lower()
