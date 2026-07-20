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

    # AC4: URL do git interno é placeholder marcado, não host inventado
    assert "<URL-do-git-interno>" in leiame, "LEIA-ME deve usar <URL-do-git-interno> como placeholder, não um host real"
