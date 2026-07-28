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


def test_seguranca_wiring():
    """A capacidade de segurança está montada e referenciada."""
    assert (REPO / "templates" / "SEGURANCA.md").exists(), "falta templates/SEGURANCA.md"
    assert (REPO / "commands" / "seguranca.md").exists(), "falta commands/seguranca.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "templates/SEGURANCA.md" in kickoff, "kickoff não copia SEGURANCA.md"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/SEGURANCA.md" in claude, "CLAUDE.md não referencia docs/SEGURANCA.md"


def test_todolist_gitignorada():
    """to-dolist.md (captura local do /mss-spec:to-dolist) ignorada e ANCORADA na raiz.

    O padrão tem que ser `/to-dolist.md` (com barra): sem ela, casaria por nome e ignoraria
    também `commands/to-dolist.md` — o próprio arquivo do comando não subiria pro git.
    """
    gi = (REPO / "templates" / "gitignore").read_text(encoding="utf-8")
    assert "/to-dolist.md" in gi, "templates/gitignore precisa ignorar /to-dolist.md ancorado na raiz"


def test_doctor_wiring():
    """Pré-vôo do doctor montado: comando existe e o CLAUDE.md manda rodar no início da 1ª tarefa."""
    assert (REPO / "commands" / "doctor.md").exists(), "falta commands/doctor.md"
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Pré-vôo de ambiente" in claude, "CLAUDE.md não cita o pré-vôo de ambiente (doctor)"


def test_robustez_plugin_root_wiring():
    """Resolução robusta do plugin montada: doctor e kickoff citam o fallback pros locais padrão do Code."""
    doctor = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "plugins/cache" in doctor, "doctor.md não cita o fallback de resolução do plugin (~/.claude/plugins/cache)"
    assert "plugins/cache" in kickoff, "kickoff.md não cita o guard de resolução do plugin (~/.claude/plugins/cache)"


def test_regra_senhas_wiring():
    """A regra de senhas está montada: banco oferece a variável de ambiente e SEGURANCA a documenta."""
    banco = (REPO / "commands" / "banco.md").read_text(encoding="utf-8")
    seg = (REPO / "templates" / "SEGURANCA.md").read_text(encoding="utf-8")
    assert "variável de ambiente" in banco, "banco.md não oferece a opção de variável de ambiente"
    assert "App Settings" in seg, "SEGURANCA.md não cita segredo via App Settings (variável de ambiente)"


def test_anotar_decisoes_wiring():
    """Log de decisões montado: template existe, kickoff copia, CLAUDE.md mapeia, nova-feature acrescenta."""
    assert (REPO / "templates" / "DECISOES.md").exists(), "falta templates/DECISOES.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "DECISOES.md" in kickoff, "kickoff não copia templates/DECISOES.md"
    assert "docs/decisoes.md" in claude, "CLAUDE.md não mapeia docs/decisoes.md"
    assert "docs/decisoes.md" in nova, "nova-feature não acrescenta em docs/decisoes.md"


def test_log_wiring():
    """Padrão de log montado: template funcional existe, comando existe, kickoff monta a
    infra, logs/ é ignorado (ancorado) e o CLAUDE.md carrega a regra (stdout prod / arquivo dev)."""
    assert (REPO / "templates" / "logging.py").exists(), "falta templates/logging.py"
    assert (REPO / "commands" / "log.md").exists(), "falta commands/log.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    gi = (REPO / "templates" / "gitignore").read_text(encoding="utf-8")
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "templates/logging.py" in kickoff, "kickoff não monta templates/logging.py"
    assert "/logs/" in gi, "templates/gitignore precisa ignorar /logs/ ancorado na raiz"
    assert "LOG_ATIVO" in claude, "CLAUDE.md não carrega a regra de log (LOG_ATIVO / stdout prod)"


def test_protocolo_log_por_arquivo_wiring():
    """A regra transversal (c): comandos que GERAM arquivo listam os alvos e perguntam quais
    recebem logger. Canônica no log.md; apontada por banco/nova-feature; registrada em decisoes."""
    log = (REPO / "commands" / "log.md").read_text(encoding="utf-8")
    banco = (REPO / "commands" / "banco.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "getLogger(__name__)" in log, "log.md não descreve a instrumentação (getLogger(__name__))"
    assert "/mss-spec:log" in banco, "banco.md não aponta o protocolo de instrumentação de log"
    assert "/mss-spec:log" in nova, "nova-feature.md não aponta o protocolo de instrumentação de log"


def test_release_wiring():
    """Gate de pré-publicação montado: comando existe, orquestra os checks que já existem
    (testes/segurança/CHANGELOG) e o nova-feature aponta o release no fecho, ANTES do finishing."""
    assert (REPO / "commands" / "release.md").exists(), "falta commands/release.md"
    rel = (REPO / "commands" / "release.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "pytest" in rel or "plano-teste" in rel, "release.md não roda o plano-teste (pytest)"
    assert "/mss-spec:seguranca" in rel, "release.md não lembra o check de segurança"
    assert "CHANGELOG" in rel, "release.md não confere o CHANGELOG"
    assert "/mss-spec:compliance" in rel, "release.md não roda o check de convenções (compliance)"
    assert "finishing-a-development-branch" in rel, "release.md não se posiciona como gate ANTES do finishing"
    assert "/mss-spec:release" in nova, "nova-feature.md não aponta o /mss-spec:release no fecho"


def test_regras_branch_e_escopo_wiring():
    """Duas regras montadas como convenção (doc/comandos, sem hook):
    (1) branch nasce SEMPRE da principal, nunca de outra branch;
    (2) um assunto por janela — ao surgir 2º assunto, ALERTA (não trava) e empurra pro to-dolist."""
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    todo = (REPO / "commands" / "to-dolist.md").read_text(encoding="utf-8")
    # (1) branch da principal
    assert "a partir da principal" in claude, "CLAUDE.md não manda abrir a branch a partir da principal"
    assert "nunca a partir de outra branch" in claude, "CLAUDE.md não proíbe ramificar de outra branch"
    assert "a partir da principal" in nova, "nova-feature.md não manda partir da principal ao abrir a branch"
    # (2) um assunto por janela (aparece como título e inline → checagem case-insensitive)
    assert "um assunto por janela" in claude.lower(), "CLAUDE.md não carrega a regra 'um assunto por janela'"
    assert "um assunto por janela" in nova.lower(), "nova-feature.md não aponta o protocolo 'um assunto por janela'"
    assert "um assunto por janela" in todo.lower(), "to-dolist.md não liga ao protocolo 'um assunto por janela'"


def test_redes_de_seguranca_documentadas():
    """As três redes de segurança que JÁ existem no kit estão explícitas na doc de
    distribuição — fecha os falsos-negativos da análise (docs/analise/Claude.txt) e o
    item 11 do backlog ('o git é o rollback'). Só doc: nada de comando de rollback novo."""
    html = (REPO / "docs" / "COMO-FUNCIONA.html").read_text(encoding="utf-8")
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    upgrade = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    # seção dedicada no HTML (onde o analista procurou e não achou)
    assert 'id="redes"' in html, "COMO-FUNCIONA.html não tem a seção 'Redes de segurança'"
    # (1) auto-teste do próprio kit
    assert "pytest tests/" in html, "HTML não cita o auto-teste do kit (pytest tests/)"
    # (2) o git é o rollback (item 11) — HTML + upgrade + kickoff
    assert "o git é o rollback" in html.lower(), "HTML não documenta 'o git é o rollback'"
    assert "git restore" in upgrade, "upgrade.md não cita o git como rollback (git restore)"
    assert "git restore" in kickoff, "kickoff.md não cita o git como rollback (git restore)"
    # (3) CHANGELOG como rede contra drift entre cópias
    assert "drift" in html.lower(), "HTML não enquadra o CHANGELOG como rede (drift entre cópias)"
    # LEIA-ME reforça a rede que faltava (rollback via git)
    assert "rollback" in leiame.lower(), "LEIA-ME não menciona o git como rollback"


def test_upgrade_dry_run_wiring():
    """Modo --dry-run montado no upgrade (item 10): preview opt-in que mostra o diff
    unificado da categoria 1 (referência — o passo hoje silencioso) SEM escrever arquivo,
    e diz como aplicar de verdade (rodar sem a flag). A flag é aditiva."""
    up = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    fm = up.split("---")[1]  # frontmatter
    # AC3: a flag é aditiva — ofertada no argument-hint, mas opt-in
    assert "--dry-run" in fm, "upgrade.md: argument-hint do frontmatter não oferece --dry-run"
    assert "--dry-run" in up, "upgrade.md não documenta o modo --dry-run"
    # AC1: no dry-run nenhum arquivo é escrito (working tree intacto)
    assert "não escreve" in up.lower(), "upgrade.md não garante que o --dry-run não escreve arquivo"
    # AC1: mostra o diff unificado da categoria 1 (o passo hoje silencioso, alvo da prevenção)
    assert "diff unificado" in up.lower(), "upgrade.md não cita o diff unificado da categoria 1 no --dry-run"
    # AC2: o relatório diz como aplicar de verdade (rodar sem a flag)
    assert "sem a flag" in up.lower(), "upgrade.md não diz como aplicar de verdade (rodar upgrade sem a flag)"


def test_compliance_wiring():
    """Auditoria de convenções montada: comando existe, checa a estrutura/docs/memória do jeito
    da casa (só reporta), e delimita o papel — auditoria profunda é seguranca, sync é upgrade."""
    assert (REPO / "commands" / "compliance.md").exists(), "falta commands/compliance.md"
    comp = (REPO / "commands" / "compliance.md").read_text(encoding="utf-8")
    # cobre os checks-chave do checklist (estrutura, decisões, memória, spec-driven)
    assert "ESTRUTURA.md" in comp, "compliance.md não checa a estrutura em camadas"
    assert "docs/decisoes.md" in comp, "compliance.md não checa docs/decisoes.md"
    assert "MEMORY.md" in comp, "compliance.md não checa memory/MEMORY.md versionada"
    assert "INDEX.md" in comp, "compliance.md não checa o spec-driven (INDEX)"
    # papéis separados: defere a auditoria profunda ao seguranca e o conserto ao upgrade
    assert "/mss-spec:seguranca" in comp, "compliance.md não defere a auditoria AppSec ao seguranca"
    assert "/mss-spec:upgrade" in comp, "compliance.md não aponta o upgrade como quem sincroniza template"


def test_mapa_contexto_wiring():
    """Mapa de contexto (F1 — fundação) montado: cada projeto ganha um docs/superpowers/MAPA.md
    curto (Onde estamos · Próximo passo · Conexões inter-projeto), lido na partida e mantido pelo
    fluxo. Fonte de verdade FEDERADA (cada repo declara; nunca inventar). O mapa neural HTML que
    agrega os repos é F2 (fora daqui). Trava os 4 pontos de integração + o template."""
    mapa_tpl = REPO / "templates" / "MAPA.md"
    mapa_cmd = REPO / "commands" / "mapa.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")

    # CA5: template com as 3 seções + a de Conexões manda declarar do código real / não inventar
    assert mapa_tpl.exists(), "falta templates/MAPA.md"
    tpl = mapa_tpl.read_text(encoding="utf-8")
    assert "Onde estamos" in tpl, "MAPA.md: falta a seção 'Onde estamos'"
    assert "Próximo passo" in tpl, "MAPA.md: falta a seção 'Próximo passo'"
    assert "Conexões" in tpl, "MAPA.md: falta a seção 'Conexões' (dimensão inter-projeto)"
    assert "código real" in tpl.lower(), "MAPA.md: Conexões não manda declarar a partir do código real"
    assert "invent" in tpl.lower(), "MAPA.md: Conexões não avisa pra nunca inventar conexão"

    # CA4: comando /mss-spec:mapa existe e descreve ler + reconciliar (git/INDEX + código) + gravar
    assert mapa_cmd.exists(), "falta commands/mapa.md"
    cmd = mapa_cmd.read_text(encoding="utf-8")
    assert "reconcil" in cmd.lower(), "mapa.md não descreve reconciliar o mapa com as fontes vivas"
    assert "git" in cmd.lower(), "mapa.md não relê o git pra regenerar 'Onde estamos'"
    assert "INDEX" in cmd, "mapa.md não considera o INDEX (tarefa em andamento)"
    assert "Conexões" in cmd, "mapa.md não reconcilia a seção de Conexões (código de integração)"

    # CA1: kickoff copia o template pro caminho do projeto
    assert "templates/MAPA.md" in kickoff, "kickoff não copia templates/MAPA.md"
    assert "docs/superpowers/MAPA.md" in kickoff, "kickoff não cria docs/superpowers/MAPA.md"

    # CA2: CLAUDE.md manda LER o MAPA.md na partida
    assert "MAPA.md" in claude, "CLAUDE.md não referencia o MAPA.md"
    assert "na partida" in claude.lower(), "CLAUDE.md não manda ler o mapa na partida"

    # CA3: nova-feature mantém o mapa (abrir a branch + fecho)
    assert "MAPA.md" in nova, "nova-feature não atualiza o MAPA.md"

    # projeto EXISTENTE (não só o kickoff em greenfield) ganha o MAPA.md via upgrade
    upgrade = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    assert "MAPA.md" in upgrade, "upgrade não garante o docs/superpowers/MAPA.md num projeto que nasceu antes da F1"


def test_mapa_neural_wiring():
    """Mapa mental do projeto (F2 — mesma branch/assunto) montado: o gerador (script Python
    testável) e o comando existem, o comando acha o script via plugin-root e descreve as 4
    dimensões, a saída derivada é gitignorada e o LEIA-ME lista o comando. O comportamento
    (extratores + render) vive no test_mapa_neural."""
    script = REPO / "templates" / "mapa_neural.py"
    cmd = REPO / "commands" / "mapa-neural.md"
    assert script.exists(), "falta templates/mapa_neural.py (o gerador do mapa mental)"
    assert cmd.exists(), "falta commands/mapa-neural.md"
    txt = cmd.read_text(encoding="utf-8")
    assert "templates/mapa_neural.py" in txt, "mapa-neural.md não aponta o gerador templates/mapa_neural.py"
    assert "mapa mental" in txt.lower(), "mapa-neural.md não descreve o mapa mental do projeto"
    for dim in ("Arquitetura", "APIs", "Memórias", "Conexões"):
        assert dim in txt, "mapa-neural.md não cita a dimensão " + dim

    gi = (REPO / "templates" / "gitignore").read_text(encoding="utf-8")
    linhas_gi = [l.strip() for l in gi.splitlines()]
    # a saída é ANCORADA em /docs/ — o padrão solto `mapa-neural.md` casaria por nome e
    # ignoraria o PRÓPRIO commands/mapa-neural.md (mesma armadilha do /to-dolist.md).
    assert "/docs/mapa-neural.html" in linhas_gi, "templates/gitignore não ancora a saída mapa-neural.html em /docs/"
    assert "/docs/mapa-neural.md" in linhas_gi, "templates/gitignore não ancora a saída mapa-neural.md em /docs/"
    assert "mapa-neural.md" not in linhas_gi, "padrão 'mapa-neural.md' SOLTO ignoraria commands/mapa-neural.md — ancore em /docs/"

    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "/mss-spec:mapa-neural" in leiame, "LEIA-ME não lista o comando /mss-spec:mapa-neural"


def test_distribuicao_por_git_wiring():
    """Mecanismo de distribuição por git montado (item 9): o mesmo marketplace.json
    serve add por pasta local E por URL git (source relative-path resolvido no clone),
    a allowlist cross-marketplace deixa a dependência do superpowers a 1 linha, e o
    LEIA-ME documenta as duas vias com a URL do git como placeholder (não host inventado).
    """
    market = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")

    # AC1: plugin mss-spec com source relative-path (mesma raiz do marketplace) -> serve local + git
    plugin_entry = next(p for p in market["plugins"] if p["name"] == "mss-spec")
    src = plugin_entry["source"]
    src_kind = src if isinstance(src, str) else src.get("source")
    assert src_kind == "relative-path", "marketplace.json: plugin mss-spec não usa source relative-path"

    # AC2: allowlist cross-marketplace inclui o marketplace oficial (dep superpowers a 1 linha)
    allow = market.get("allowCrossMarketplaceDependenciesOn", [])
    assert "claude-plugins-official" in allow, (
        "marketplace.json não declara allowCrossMarketplaceDependenciesOn: claude-plugins-official"
    )

    # AC3: LEIA-ME documenta a via git (add por URL + install + update) E a via local por pasta
    assert "marketplace add" in leiame, "LEIA-ME não mostra o comando de adicionar marketplace"
    assert "marketplace update" in leiame, "LEIA-ME não mostra como atualizar (marketplace update / git pull)"
    assert "install mss-spec@mss-local" in leiame, "LEIA-ME não mostra o install a partir da lojinha mss-local"
    assert "pasta local" in leiame.lower(), "LEIA-ME não preserva a via de instalação por pasta local (dev/teste)"

    # AC4: LEIA-ME aponta pra URL real do GitHub (publicado 2026-07-21), não mais o placeholder
    assert "github.com/RMaganha/Spec-Powers" in leiame, "LEIA-ME deve apontar pra URL real do GitHub"
    assert "<URL-do-git-interno>" not in leiame, "LEIA-ME não deve mais conter o placeholder <URL-do-git-interno>"


def test_captura_memory_dois_modos():
    """/mss-spec:memory vira o comando de memória com 2 modos: resgatar (intacto) + capturar (novo).
    capturar destila a SESSÃO do contexto e roteia pras 3 camadas, aplica <private>, pede OK, não duplica."""
    mem = (REPO / "commands" / "memory.md").read_text(encoding="utf-8")
    fm = mem.split("---")[1]  # frontmatter
    # os 2 modos ofertados no argument-hint
    assert "resgatar" in fm, "memory.md: argument-hint não oferece o modo resgatar"
    assert "capturar" in fm, "memory.md: argument-hint não oferece o modo capturar"
    # regressão: o modo resgatar (memória nativa → repo) segue descrito
    assert "nativa" in mem.lower(), "memory.md: modo resgatar (memória nativa → repo) sumiu"
    # capturar roteia pras 3 camadas
    assert "docs/decisoes.md" in mem, "capturar não roteia decisão transversal pro decisoes.md"
    assert "Fora de escopo" in mem, "capturar não roteia decisão 'não fazer' pro INDEX (Fora de escopo)"
    assert "memory/sessions/" in mem, "capturar não grava o resumo em memory/sessions/"
    assert "DIARIO.md" in mem, "capturar não indexa no memory/DIARIO.md"
    assert "MEMORY.md" in mem, "capturar não indexa fato durável no MEMORY.md"
    # convenções e salvaguardas
    assert "<private>" in mem, "capturar não aplica a convenção <private>"
    assert "/mss-spec:mapa" in mem, "capturar não delega o MAPA ao /mss-spec:mapa (não reimplementa)"
    assert "antes de gravar" in mem.lower(), "capturar não pede OK do owner antes de gravar (CA1)"
    assert "não duplic" in mem.lower(), "capturar não garante não-duplicação (CA2)"
    # foco em pivôs (a evolução das decisões, não só o estado final)
    assert "pivô" in mem.lower() or "repensad" in mem.lower(), "capturar não prioriza os pivôs no resumo de sessão"


def test_captura_diario_template():
    """Template do índice do diário: formato por dia, aponta os arquivos de sessão, foca nos pivôs."""
    dia = REPO / "templates" / "DIARIO.md"
    assert dia.exists(), "falta templates/DIARIO.md"
    txt = dia.read_text(encoding="utf-8")
    assert "## <data>" in txt, "DIARIO.md não mostra o formato de índice por dia (## <data>)"
    assert "sessions/" in txt, "DIARIO.md não aponta os arquivos em memory/sessions/"
    assert "pivô" in txt.lower() or "repensad" in txt.lower(), \
        "DIARIO.md não orienta capturar os pivôs (a evolução das decisões)"
    # dogfood: o próprio kit tem seu índice de diário
    assert (REPO / "memory" / "DIARIO.md").exists(), "falta o dogfood memory/DIARIO.md"


def test_captura_kickoff_scaffold():
    """kickoff monta o diário no projeto: copia o template e cria a pasta de sessões."""
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "templates/DIARIO.md" in kickoff, "kickoff não copia templates/DIARIO.md"
    assert "memory/DIARIO.md" in kickoff, "kickoff não cria memory/DIARIO.md"
    assert "memory/sessions/" in kickoff, "kickoff não cria a pasta memory/sessions/"


def test_captura_private_e_indice():
    """CLAUDE.md do projeto carrega: convenção <private>, ponteiro pro diário, e o índice-primeiro."""
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<private>" in claude, "CLAUDE.md não documenta a convenção <private> (nunca vira memória)"
    assert "DIARIO.md" in claude, "CLAUDE.md não aponta o diário de sessão (memory/DIARIO.md)"
    assert "pasta inteira" in claude.lower(), \
        "CLAUDE.md não reforça o índice-primeiro (consultar índice; nunca ler a pasta inteira)"


def test_captura_delegacao_fecho():
    """O fecho do nova-feature DELEGA a captura ao /mss-spec:memory capturar (não re-descreve inline),
    e a captura entra no caminho do merge → principal (consolidar decisões do assunto)."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "/mss-spec:memory capturar" in nova, \
        "nova-feature (fecho) não delega a captura ao /mss-spec:memory capturar"
    # a captura acontece antes de integrar (merge/finishing), consolidando as decisões do assunto
    assert "finishing" in nova.lower(), "nova-feature não posiciona a captura junto ao finishing/integração"


def test_captura_hook_throttle():
    """A decisão de cutucar respeita o intervalo (throttle) — aproxima 'a cada X' por evento."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "capturar_nudge", REPO / "hooks" / "capturar_nudge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # dentro do intervalo → não cutuca; passou do intervalo → cutuca; sem histórico → cutuca (1ª vez)
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=1060.0, intervalo_s=1800) is False
    assert mod.deve_cutucar(ultimo_ts=1000.0, agora=4600.0, intervalo_s=1800) is True
    assert mod.deve_cutucar(ultimo_ts=None, agora=1000.0, intervalo_s=1800) is True


def test_captura_hook_optin_doc():
    """Hook é OPT-IN, off por padrão, não-bloqueante, e só CUTUCA (não grava sozinho)."""
    assert (REPO / "hooks" / "capturar_nudge.py").exists(), "falta hooks/capturar_nudge.py"
    doc = (REPO / "hooks" / "README.md").read_text(encoding="utf-8")
    low = doc.lower()
    assert "opt-in" in low or "desligado por padrão" in low, "hook não é documentado como opt-in/off por padrão"
    assert "Stop" in doc and "PreCompact" in doc, "hook não documenta os eventos Stop/PreCompact"
    assert "/mss-spec:memory capturar" in doc, "hook não cutuca pra rodar /mss-spec:memory capturar"
    assert "não grava" in low or "nunca grava" in low, "hook não deixa claro que só cutuca (não grava)"
    assert "não bloqueia" in low or "não-bloqueante" in low, "hook não deixa claro que é não-bloqueante"


def test_captura_docs_leiame():
    """LEIA-ME documenta o modo capturar do /mss-spec:memory (o dev descobre a capacidade)."""
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "capturar" in leiame.lower(), "LEIA-ME não documenta o modo capturar do /mss-spec:memory"


def test_doctor_check_versao_wiring():
    """Check 'versão do kit' montado no doctor: compara instalada vs publicada no remoto
    (git fetch no clone, semver), reporta o comando de update, degrada gracioso e só reporta."""
    doctor = (REPO / "commands" / "doctor.md").read_text(encoding="utf-8")
    low = doctor.lower()
    # lê a versão dos dois lados a partir do plugin.json (instalada) e do remoto (publicada)
    assert "plugin.json" in doctor, "doctor.md não lê a versão do plugin.json"
    # canal: git fetch no clone (mesmo do marketplace update), não HTTP raw
    assert "git fetch" in low, "doctor.md não usa git fetch pra pegar a versão publicada"
    # reporta o comando de update (mas não roda)
    assert "marketplace update" in low, "doctor.md não indica o comando marketplace update no ⚠"
    # degrada gracioso: offline / sem remote não vira ✗ (a verificar / pulado)
    assert "a verificar" in low or "pulado" in low, \
        "doctor.md não degrada gracioso o check de versão (a verificar/pulado) quando o remoto não resolve"
    # semver, não commit
    assert "semver" in low or "número de versão" in low, \
        "doctor.md não deixa claro que compara por versão (semver), não commit"


def test_frontend_wiring():
    """Design system frontend costurado de ponta a ponta — incluindo a PONTE no nova-feature.

    Regressão real (2026-07): rodando /mss-spec:nova-feature "seguindo o padrão do
    /mss-spec:frontend", o assistente declarou que /mss-spec:frontend "não existe" e chutou o
    nível errado (Jinja em vez de React+Mantine pra tela densa). Causa: nova-feature.md fazia
    ponte pra log/segurança/teste/mapa/memória, mas NÃO pro frontend — então, ao construir uma
    tela, nada mandava consultar o docs/FRONTEND.md nem decidir Nível 1 × Nível 2. As demais
    costuras (template/kickoff/upgrade/CLAUDE.md) já existiam; faltava só a ponte.
    """
    assert (REPO / "templates" / "FRONTEND.md").exists(), "falta templates/FRONTEND.md"
    assert (REPO / "commands" / "frontend.md").exists(), "falta commands/frontend.md"
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    upgrade = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    # costuras que já existiam (regressão-guarda)
    assert "templates/FRONTEND.md" in kickoff, "kickoff não copia templates/FRONTEND.md"
    assert "docs/FRONTEND.md" in upgrade, "upgrade não sincroniza docs/FRONTEND.md"
    assert "docs/FRONTEND.md" in claude, "CLAUDE.md não referencia docs/FRONTEND.md"
    # A LACUNA: nova-feature tem que fazer a ponte pro design system ao construir uma tela.
    assert "FRONTEND.md" in nova, "nova-feature não manda consultar o docs/FRONTEND.md numa feature de UI"
    assert "/mss-spec:frontend" in nova, \
        "nova-feature não aponta o /mss-spec:frontend (instala o Nível 2) pra tela densa"
    assert "Nível" in nova, "nova-feature não cita a decisão Nível 1 × Nível 2 (stack por tela)"


def test_comando_referenciado_existe_guardrail():
    """Guardrail GERAL (Camada 2 da regressão do frontend): o CLAUDE.md ensina que um
    /mss-spec:<x> referenciado — mesmo sem aparecer na lista de invocáveis, porque é
    disable-model-invocation — EXISTE como commands/<x>.md e deve ser LIDO, nunca declarado
    inexistente nem chutado de memória. É o que impede a mesma confusão com qualquer comando
    (não só o frontend). Sempre-ativo (CLAUDE.md) e chega a projeto existente via upgrade (mescla).
    """
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
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


def test_nova_feature_pontes_design_e_dados():
    """nova-feature faz ponte pras capacidades que uma feature aciona (mesma natureza da
    lacuna do frontend, achadas na varredura de completude): no DESIGN, checar reuso entre
    projetos MSIG (precedentes); ao mexer em DADOS/DDL, rotear pela disciplina do banco (SQL
    parametrizado, DDL versionada, rodada FORA do app)."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "precedentes" in nova, \
        "nova-feature não manda checar precedentes MSIG no design (reuso entre projetos)"
    assert "/mss-spec:banco" in nova, \
        "nova-feature não roteia DDL/dados pela disciplina do /mss-spec:banco"


def test_guardrail_executar_nao_invocar():
    """Face gêmea do guardrail (regressão vista no Energy): quando o kit manda "rode /mss-spec:X"
    e X é disable-model-invocation, o assistente TENTAVA invocar via Skill e batia "Falha ao
    executar a habilidade" (erro vermelho que faz parecer quebrado), antes de cair no manual. A
    regra tem que dizer: EXECUTE os passos de commands/<x>.md você mesmo, NÃO invoque a skill.
    Central no CLAUDE.md (chega ao Energy via upgrade) + nota no fecho do nova-feature
    (junction-live: alívio imediato no exato fluxo — captura de memória — que errou)."""
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    low = claude.lower()
    assert "falha ao executar a habilidade" in low, \
        "CLAUDE.md não nomeia o erro real (Falha ao executar a habilidade) que denuncia a invocação indevida"
    assert "execute os passos" in low, \
        "CLAUDE.md não manda EXECUTAR os passos do comando (em vez de invocar a skill)"
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "disable-model-invocation" in nova, \
        "nova-feature (fecho) não avisa que os 'rode /mss-spec:X' são disable-model-invocation (executar, não invocar)"


def test_analise_wiring():
    """/mss-spec:analise — porta de entrada do BROWNFIELD (projeto que já existe).

    O kit nasceu greenfield: o kickoff tinha 1 linha de "faça um scan" sem destino, então o
    assistente entrava num projeto pronto sem conhecer nada dele. O analise lê o repo em 2 fases
    (inventário/manifests/docs → leitura focada em entrypoint/rota/DDL/config → resto por
    amostragem, DIZENDO o que ficou de fora) e destila nos artefatos que o kit já lê na partida.
    """
    cmd = REPO / "commands" / "analise.md"
    tpl = REPO / "templates" / "ARQUITETURA.md"
    assert cmd.exists(), "falta commands/analise.md"
    assert tpl.exists(), "falta templates/ARQUITETURA.md (esqueleto do dossiê)"
    an = cmd.read_text(encoding="utf-8")
    low = an.lower()

    # leitura em 2 fases + honestidade sobre o que NÃO foi lido (sem corte silencioso)
    assert "inventário" in low, "analise.md não descreve a fase 1 (inventário barato)"
    assert "amostr" in low, "analise.md não descreve a amostragem do resto do código"
    assert "ficou de fora" in low, "analise.md não relata honestamente o que ficou de fora da leitura"

    # as extensões que o owner citou — o comando tem que saber navegar nelas
    for ext in (".py", ".html", ".tsx", ".json", ".sql"):
        assert ext in an, f"analise.md não cita a leitura de {ext}"

    # docs pré-existentes são INSUMO (dado), nunca instrução a obedecer
    assert "AGENTS.md" in an, "analise.md não lê os docs pré-existentes (AGENTS.md/CLAUDE.md/README)"
    assert "dado, não instrução" in low, \
        "analise.md não trata doc/código lido como DADO (não instrução) — fronteira de prompt-injection"

    # destila nos artefatos que o kit já lê na partida (não cria 4º lugar de verdade órfão)
    assert "docs/ARQUITETURA.md" in an, "analise.md não grava o dossiê docs/ARQUITETURA.md"
    assert "docs/superpowers/MAPA.md" in an, "analise.md não preenche o MAPA (onde estamos/conexões)"

    # fronteira prescritivo × descritivo: ESTRUTURA.md é do KIT e o upgrade o sobrescreve sozinho
    # (categoria 1) — levantamento gravado lá seria APAGADO no próximo upgrade. O real vai no dossiê.
    assert "**não escreva aqui.**" in an, \
        "analise.md não proíbe escrever no docs/ESTRUTURA.md (o upgrade o sobrescreve e apagaria o levantamento)"

    # RAG/pgvector: o projeto-alvo real do owner — a leitura focada tem alvo dedicado
    assert "pgvector" in low, "analise.md não entende o pipeline RAG/pgvector (alvo real do owner)"
    assert "embedding" in low, "analise.md não inspeciona embeddings (tabela/dimensão/modelo)"
    assert "/mss-spec:precedentes" in an, "analise.md não aponta o catálogo de precedentes ao achar RAG"

    # costuras: quem manda rodar
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "/mss-spec:analise" in kickoff, "kickoff (brownfield) não aponta o /mss-spec:analise"
    assert "/mss-spec:analise" in leiame, "LEIA-ME não lista o comando /mss-spec:analise"
    assert "docs/ARQUITETURA.md" in claude, "CLAUDE.md não mapeia o docs/ARQUITETURA.md (dossiê do brownfield)"


def test_analise_nao_destrutiva():
    """A regra DURA da feature: a análise entende, não conserta.

    Nasce da restrição real do owner: o projeto-alvo já tem compose/infra e **UI/UX própria em
    .html que não pode ser alterada** — aplicar o molde do kit "pararia tudo e teríamos que
    ajustar". Então o analise escreve SÓ artefatos de doc/memória do kit; onde o projeto já tem
    o que o kit também traria, ele REGISTRA a divergência e para (a decisão é do owner).
    """
    an = (REPO / "commands" / "analise.md").read_text(encoding="utf-8")
    low = an.lower()
    assert "não-destrutiva" in low, "analise.md não declara a regra não-destrutiva"
    # não toca em infra/código do projeto
    assert "docker-compose" in low, "analise.md não protege a infra pré-existente (docker-compose)"
    assert "molde do kit" in low and "não aplic" in low, \
        "analise.md não deixa claro que o molde do kit NÃO é aplicado sobre o que já existe"
    # a UI própria é intocável (a preocupação explícita do owner)
    assert "ui própria" in low, "analise.md não registra a UI própria como intocável"
    assert "FRONTEND.md" in an, \
        "analise.md não diz que o design system do kit NÃO é imposto sobre UI própria"
    # a lista que freia o upgrade depois
    assert "não nasceu do kit" in low, \
        "analise.md não produz a lista 'não nasceu do kit' (o freio do upgrade)"
    # e o dossiê tem a seção correspondente
    tpl = (REPO / "templates" / "ARQUITETURA.md").read_text(encoding="utf-8")
    assert "não nasceu do kit" in tpl.lower(), \
        "templates/ARQUITETURA.md não tem a seção do pré-existente (não nasceu do kit)"
    assert "Lacunas" in tpl, "templates/ARQUITETURA.md não tem a seção Lacunas (o que não inferi/não li)"


def test_analise_registro_de_assuntos():
    """Assunto que JÁ existe no código entra como 1 linha `existente` no INDEX; spec viva só
    pros assuntos com evidência LIDA (fase 2), com marca de proveniência e OK do owner — nunca
    spec escrita por amostragem/inferência solta (seria a pior falha: 'spec viva não pode mentir').
    """
    an = (REPO / "commands" / "analise.md").read_text(encoding="utf-8")
    low = an.lower()
    assert "INDEX.md" in an, "analise.md não semeia o docs/superpowers/INDEX.md"
    assert "existente" in low, "analise.md não usa o status 'existente' pro assunto já implementado"
    assert "docs/specs/" in an, "analise.md não gera a spec viva por assunto"
    assert "proveniência" in low, "analise.md não marca a proveniência da spec derivada do código"
    assert "evidência" in low, "analise.md não limita a spec aos assuntos com evidência lida"


def test_upgrade_respeita_preexistente():
    """O freio: a categoria 1 do upgrade hoje sobrescreve docker-compose.yml/Dockerfile SOZINHO.
    Num brownfield isso mata a infra do projeto — risco destampado no design da análise. Com a
    lista 'não nasceu do kit' do docs/ARQUITETURA.md, esses arquivos passam a PERGUNTAR."""
    up = (REPO / "commands" / "upgrade.md").read_text(encoding="utf-8")
    low = up.lower()
    assert "ARQUITETURA.md" in up, "upgrade.md não consulta a lista do docs/ARQUITETURA.md"
    assert "não nasceu do kit" in low, "upgrade.md não reconhece o arquivo que não nasceu do kit"
    assert "brownfield" in low, "upgrade.md não trata o caso brownfield na categoria 1"


def test_guardrail_skills_dir_instalado():
    """Quarta (e última) face da família: o assistente disse "o plugin mss-spec não está
    instalado nesta máquina" — porque checou só o registro de marketplace/installed_plugins.json
    e não viu que o mss-spec é um SKILLS-DIR plugin (em ~/.claude/skills/<nome>/, mecanismo
    oficial; `claude plugin list` o mostra em 'Skills-directory plugins', √ loaded). A regra
    impede o "não instalado" indevido apontando a checagem certa."""
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    low = claude.lower()
    assert "skills-dir" in low, \
        "CLAUDE.md não explica que o mss-spec pode estar instalado como skills-dir plugin"
    assert "plugin list" in low, \
        "CLAUDE.md não aponta o `claude plugin list` como a checagem certa (não o installed_plugins.json)"
