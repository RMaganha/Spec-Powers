# -*- coding: utf-8 -*-
"""Gera o painel "anatomia de runtime" do kit mss-spec (/mss-spec:anatomia).

O que o mapa-neural não mostra: QUANDO cada peça do kit entra na janela do assistente
(partida / por evento / sob demanda / fecho), QUEM lê × escreve cada artefato, onde mora
o risco e o que está na fila.

Regra dura (mesma do mapa-neural): número que aparece no HTML é MEDIDO — manifestos,
frontmatter dos comandos, hooks.json, rules, bytes do orçamento, tabela do EVALS — nunca
escrito à mão. O que não dá pra medir (matriz lê×escreve, classes de risco) é metadado
CURADO versionado aqui dentro, e cada entrada declara os arquivos do kit que cita
(`alvos`): o teste de wiring confere que todos existem — painel não mente em silêncio.

Uso:  python anatomia.py [--proj DIR] [--kit DIR] [--out DIR]
Saída: <out|proj/docs>/anatomia.html — self-contained (zero CDN; proxy MSIG), fora do git.
"""
import argparse
import html as _html
import json
import re
from pathlib import Path

# tetos do orçamento de contexto (os mesmos travados em tests/test_orcamento_contexto.py)
TETOS = {
    "CLAUDE.md": 8000,
    "docs/superpowers/MAPA.md": 6000,
    "docs/superpowers/INDEX.md": 7000,
    "memory/MEMORY.md": 25 * 1024,
}


def _ler(p: Path) -> str:
    # utf-8-sig: manifesto gravado com BOM (PowerShell 5.1) não derruba o painel
    return p.read_text(encoding="utf-8-sig")


def _frontmatter(texto: str) -> str:
    return texto.split("---")[1] if texto.startswith("---") else ""


# ---------------------------------------------------------------------------- medido, não escrito

def versao_kit(kit: Path) -> str:
    return json.loads(_ler(Path(kit) / ".claude-plugin" / "plugin.json"))["version"]


def comandos(kit: Path) -> list:
    """Todo commands/*.md: nome, bytes, description e a marca invocável × disable-model-invocation."""
    saida = []
    for md in sorted((Path(kit) / "commands").glob("*.md")):
        fm = _frontmatter(_ler(md))
        desc = re.search(r"^description:\s*(.+)$", fm, re.M)
        saida.append({
            "nome": md.stem,
            "bytes": md.stat().st_size,
            "description": desc.group(1).strip().strip('"') if desc else "",
            "disable": bool(re.search(r"^disable-model-invocation:\s*true", fm, re.M)),
        })
    return saida


def hooks_do_kit(kit: Path) -> list:
    """hooks/*.py com a marca registrado (aparece no hooks.json) × presente-e-não-registrado."""
    kit = Path(kit)
    reg_txt = ""
    hj = kit / "hooks" / "hooks.json"
    eventos_por_arquivo = {}
    if hj.exists():
        reg_txt = _ler(hj)
        cfg = json.loads(reg_txt)
        for evento, grupos in cfg.get("hooks", {}).items():
            for g in grupos:
                for h in g.get("hooks", []):
                    m = re.search(r"([\w-]+\.py)", h.get("command", ""))
                    if m:
                        eventos_por_arquivo.setdefault(m.group(1), []).append(
                            f"{evento} ({g.get('matcher', '*')})")
    saida = []
    for py in sorted((kit / "hooks").glob("*.py")):
        saida.append({
            "arquivo": py.name,
            "registrado": py.name in reg_txt,
            "eventos": eventos_por_arquivo.get(py.name, []),
        })
    return saida


def rules_do_kit(kit: Path) -> list:
    """templates/rules/*.md com os globs do `paths:` (o Claude Code carrega sozinho ao tocar)."""
    saida = []
    for md in sorted((Path(kit) / "templates" / "rules").glob("*.md")):
        fm = _frontmatter(_ler(md))
        saida.append({"nome": md.stem, "paths": re.findall(r'-\s*"([^"]+)"', fm)})
    return saida


def orcamento(proj: Path) -> list:
    """Bytes reais × teto dos arquivos da partida que EXISTEM no projeto."""
    saida = []
    for rel, teto in TETOS.items():
        p = Path(proj) / rel
        if p.exists():
            saida.append({"arquivo": rel, "bytes": p.stat().st_size, "teto": teto})
    return saida


_CASO = re.compile(r"^\| (F-\d{3}) \|", re.M)


def evals(proj: Path) -> dict:
    """Total de casos e ids abertos, direto da tabela do docs/EVALS.md."""
    p = Path(proj) / "docs" / "EVALS.md"
    if not p.exists():
        return {"total": 0, "abertos": []}
    abertos, total = [], 0
    for linha in _ler(p).splitlines():
        m = _CASO.match(linha)
        if not m:
            continue
        total += 1
        status = linha.rstrip("| ").rsplit("|", 1)[-1].strip().strip("*`")
        if status == "aberto":
            abertos.append(m.group(1))
    return {"total": total, "abertos": abertos}


def testes(proj: Path) -> int:
    pasta = Path(proj) / "tests"
    if not pasta.is_dir():
        return 0
    return sum(len(re.findall(r"^def test_", _ler(py), re.M)) for py in pasta.glob("test_*.py"))


def proximo_passo(proj: Path) -> str:
    """1º parágrafo da seção 'Próximo passo' do MAPA (até comentário/nova seção)."""
    p = Path(proj) / "docs" / "superpowers" / "MAPA.md"
    if not p.exists():
        return ""
    m = re.search(r"^## Próximo passo\s*\n(.*?)(?=\n<!--|\n## |\Z)", _ler(p), re.S | re.M)
    return m.group(1).strip() if m else ""


def a_fazer(proj: Path) -> list:
    """Itens vivos da seção 'A fazer' do INDEX."""
    p = Path(proj) / "docs" / "superpowers" / "INDEX.md"
    if not p.exists():
        return []
    m = re.search(r"^## A fazer.*?\n(.*?)(?=\n## |\Z)", _ler(p), re.S | re.M)
    if not m:
        return []
    return [l.strip() for l in m.group(1).splitlines()
            if re.match(r"^\s*(\d+\.|-)\s+\S", l)]


# ------------------------------------------------------------------- metadado CURADO (com alvos)
# Cada entrada declara em `alvos` os arquivos do kit que cita; alvos_curados() alimenta o teste
# de wiring: alvo que deixar de existir = teste vermelho, nunca painel mentindo em silêncio.

LANE_PARTIDA = [
    ("Molde do CLAUDE.md do projeto", "Entra inteiro em toda sessão (teto 8 KB travado por teste): "
     "só guardrail + ponteiro; procedimento mora nos comandos.", ["templates/CLAUDE.md"]),
    ("Ritual de partida", "O assistente lê MAPA (onde estamos) → INDEX (aberto + fora de escopo) → "
     "índice de memória POR GATILHO — destilado antes da fonte.",
     ["templates/MAPA.md", "templates/INDEX.md", "templates/MEMORY.md"]),
    ("Ponteiro na pasta nativa", "O índice que o Claude Code auto-carrega aponta pro memory/MEMORY.md "
     "do repo (F-012: duas cópias = a errada carrega).", ["templates/MEMORY.md"]),
    ("doctor na 1ª tarefa", "Pré-voo: plugin resolve? versão atrás do remoto? orçamento de contexto "
     "dentro do teto (check 9)?", ["commands/doctor.md"]),
]

LANE_FECHO = [
    ("1 · plano-teste", "Suíte inteira; baseline anti-regressão só atualiza a 100%.",
     ["commands/plano-teste.md"]),
    ("2 · seguranca", "Só se a entrega mexeu em rota/endpoint (authz, entrada validada, Bearer).",
     ["commands/seguranca.md"]),
    ("3 · memory capturar", "Destila a sessão: decisões (incl. negativas), pivôs → diário, falha → "
     "EVALS, escopo → fora-de-escopo. Pede OK antes de gravar; chama o mapa no final.",
     ["commands/memory.md", "commands/mapa.md"]),
    ("4 · release → finishing", "Gate ✓/✗: testes · versão nos 2 manifestos · CHANGELOG · specs "
     "coerentes · convenções · corpus · working tree. Verde → merge/PR; push só a pedido.",
     ["commands/release.md"]),
]

# colunas da matriz (atores) e linhas (artefato, {coluna: L/E/LE + nota}, alvos citados)
ATORES = ["partida", "nova-feature / divergir", "analise", "kickoff / upgrade",
          "memory capturar", "mapa / mapa-neural", "doctor / release"]

MATRIZ = [
    ("CLAUDE.md (molde do projeto)",
     {"partida": "L", "nova-feature / divergir": "L", "analise": "L",
      "kickoff / upgrade": "LE mescla", "doctor / release": "L"},
     ["templates/CLAUDE.md", "commands/upgrade.md"]),
    ("docs/superpowers/MAPA.md",
     {"partida": "L", "nova-feature / divergir": "E branch/fecho", "analise": "E",
      "kickoff / upgrade": "E cria", "memory capturar": "L delega",
      "mapa / mapa-neural": "LE reconcilia", "doctor / release": "L"},
     ["commands/mapa.md", "commands/nova-feature.md"]),
    ("docs/superpowers/INDEX.md",
     {"partida": "L", "nova-feature / divergir": "LE status", "analise": "E semeia",
      "kickoff / upgrade": "E backlog", "memory capturar": "E fora-de-escopo",
      "mapa / mapa-neural": "L", "doctor / release": "L"},
     ["commands/nova-feature.md", "commands/analise.md"]),
    ("docs/specs/ (spec viva por assunto)",
     {"nova-feature / divergir": "LE dono", "analise": "E c/ evidência",
      "memory capturar": "E histórico", "doctor / release": "L coerência"},
     ["commands/nova-feature.md", "commands/release.md"]),
    ("docs/decisoes.md",
     {"nova-feature / divergir": "E", "kickoff / upgrade": "E cria",
      "memory capturar": "E", "doctor / release": "L"},
     ["commands/memory.md", "commands/kickoff.md"]),
    ("docs/EVALS.md (corpus de falhas)",
     {"partida": "L", "nova-feature / divergir": "L premissas", "kickoff / upgrade": "E cria vazio",
      "memory capturar": "E caso novo", "doctor / release": "L check"},
     ["commands/doctor.md", "commands/release.md", "templates/EVALS.md"]),
    ("memory/ + MEMORY.md (gatilhos)",
     {"partida": "L índice", "nova-feature / divergir": "L por gatilho", "analise": "E",
      "kickoff / upgrade": "E cria", "memory capturar": "LE dono",
      "mapa / mapa-neural": "L dimensão", "doctor / release": "L teto"},
     ["commands/memory.md", "templates/MEMORY.md"]),
    ("memory/DIARIO.md + sessions/",
     {"kickoff / upgrade": "E cria", "memory capturar": "LE dono"},
     ["commands/memory.md", "templates/DIARIO.md"]),
    ("CHANGELOG.md + manifestos (versão ×2)",
     {"nova-feature / divergir": "E no release", "doctor / release": "L gate/versão"},
     ["commands/release.md"]),
    ("ARQUITETURA.md (descritivo, brownfield)",
     {"nova-feature / divergir": "L", "analise": "LE dono", "kickoff / upgrade": "L freio cat.1",
      "mapa / mapa-neural": "L"},
     ["commands/analise.md", "templates/ARQUITETURA.md"]),
    ("FRONTEND.md / SEGURANCA.md / ESTRUTURA.md",
     {"nova-feature / divergir": "L decide nível", "analise": "L não impõe",
      "kickoff / upgrade": "LE cat.1", "doctor / release": "L seguranca"},
     ["templates/FRONTEND.md", "templates/SEGURANCA.md", "templates/ESTRUTURA.md"]),
]

RISCOS = [
    ("Intermitência pós-update do app", "ABERTA",
     "O mss-spec já parou de carregar depois de update do Claude Code (instalação por junction). "
     "Pendência registrada — falta capturar o estado quebrado pra diagnosticar.",
     "nenhuma automática — o doctor (check 1) diagnostica depois que você percebe.",
     ["memory/project_pendencia_intermitencia_pos_update.md", "commands/doctor.md"]),
    ("Prosa não é código: o modelo pode ignorar a regra", "estrutural",
     "Os comandos crescem a cada feature (bytes medidos no topo do painel). A lição do CLAUDE.md "
     "(0.20.0) vale aqui: arquivo de instrução inchado = regra ignorada. Os testes de wiring "
     "travam a PRESENÇA do texto, não a obediência.",
     "teto por teste já provado no CLAUDE.md; a poda dos comandos está na fila.",
     ["commands/nova-feature.md"]),
    ("Windows: encoding e fim de linha", "reincidente",
     "Classe que já mordeu 3×: BOM do PowerShell 5.1 em JSON · text=True no subprocess quebrando "
     "o git · CRLF em filtro. Cada caso virou memória/guardrail; a classe segue viva.",
     "memórias com gatilho + a suíte pega na hora (foi ela que acusou o BOM).",
     ["memory/project_subprocess_texto_windows_quebra_git.md",
      "memory/feedback_testar_js_gerado_node_check.md"]),
    ("Hooks podem falhar em silêncio", "desenho consciente",
     "A cerca é fail-open (bug não trava trabalho — mas também não cerca) e o nudge é opt-in. "
     "Hook que não dispara = volta ao estado só-prosa, sem aviso.",
     "política em docs/decisoes.md; fallback de registro via settings.json no README dos hooks.",
     ["hooks/README.md", "hooks/projeto_ativo.py"]),
    ("Doc destilado pode mentir", "residual",
     "MAPA/spec/INDEX são a memória de partida; bugfix que altera comportamento sem atualizar a "
     "spec induz o assistente a reintroduzir o bug depois.",
     "regra no nova-feature (bugfix atualiza spec) + check de coerência do release.",
     ["commands/nova-feature.md", "commands/release.md"]),
    ("Dependência do superpowers fora do manifesto", "frágil",
     "A dep cross-marketplace quebrava o load via skills-dir/symlink — ficou via settings.json. "
     "Se sumir dali, brainstorming/planos param sem erro apontando a causa.",
     "decisão registrada; reentra pelo marketplace git (preparado, não ativado).",
     ["docs/decisoes.md"]),
    ("Validação viva é humana", "assumido",
     "Harness de eval foi descartado de propósito (lento, não-determinístico): ninguém automatizou "
     "\"o índice entra sozinho? as rules acendem?\".",
     "o próprio owner, com o corpus EVALS pra registrar o que falhar.",
     ["templates/EVALS.md"]),
]


def alvos_curados():
    """(origem, alvo) de TODO metadado curado — insumo do teste de wiring."""
    for titulo, _, alvos in LANE_PARTIDA + LANE_FECHO:
        for a in alvos:
            yield (f"lane:{titulo}", a)
    for artefato, _, alvos in MATRIZ:
        for a in alvos:
            yield (f"matriz:{artefato}", a)
    for titulo, _, _, _, alvos in RISCOS:
        for a in alvos:
            yield (f"risco:{titulo}", a)


# ----------------------------------------------------------------------------------------- render

_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b2430;--mut:#5b6674;--line:#e3e7ec;
--partida:#2563eb;--partida-bg:#eff4ff;--evento:#b45309;--evento-bg:#fff7ea;
--demanda:#15803d;--demanda-bg:#effaf1;--fecho:#7c3aed;--fecho-bg:#f6f0ff;
--risco:#b91c1c;--melhoria:#0f766e;--melhoria-bg:#ecfbf9}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,sans-serif;padding-bottom:60px}
header{background:var(--card);border-bottom:1px solid var(--line);padding:26px 4vw 20px}
h1{margin:0 0 4px;font-size:23px} h1 small{color:var(--mut);font-weight:400;font-size:14px}
.sub{color:var(--mut);max-width:1000px;margin:4px 0 14px}
.stats{display:flex;flex-wrap:wrap;gap:10px}
.stat{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 12px;font-size:13px}
.stat b{font-size:15px}
main{max-width:1240px;margin:0 auto;padding:0 4vw}
h2{font-size:19px;margin:38px 0 6px} .h2sub{color:var(--mut);margin:0 0 16px;max-width:1000px}
.lanes{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}
.lane{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;border-top:4px solid var(--lc)}
.lane h3{margin:0;padding:12px 14px 2px;font-size:15px;color:var(--lc)}
.lane .quando{padding:0 14px 10px;color:var(--mut);font-size:12.5px;border-bottom:1px solid var(--line)}
.item{padding:10px 14px;border-bottom:1px solid var(--line)} .item:last-child{border-bottom:none}
.item b{font-size:13.5px} .item p{margin:2px 0 0;font-size:12.5px;color:var(--mut)}
.item:hover{background:var(--lb)}
.tag{display:inline-block;font-size:10.5px;padding:1px 7px;border-radius:99px;background:var(--lb);
color:var(--lc);border:1px solid currentColor;margin-left:6px;vertical-align:1px}
code{background:#eef1f5;border-radius:4px;padding:0 4px;font-size:12px}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;min-width:900px;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:center;white-space:nowrap}
th{background:#fbfcfd;font-weight:600}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--card);
border-right:1px solid var(--line);max-width:280px;white-space:normal}
td.m{font-weight:700} td.m .l{color:var(--partida)} td.m .e{color:var(--risco)}
td .nota{font-weight:400;color:var(--mut);font-size:11px}
.legend{color:var(--mut);font-size:12.5px;margin:8px 2px}
.legend b.l{color:var(--partida)} .legend b.e{color:var(--risco)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
.rcard{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--risco);
border-radius:10px;padding:13px 16px}
.rcard h4{margin:0 0 4px;font-size:14.5px}
.rcard .grau{float:right;font-size:11px;color:var(--risco);border:1px solid var(--risco);border-radius:99px;padding:1px 8px}
.rcard p{margin:4px 0;font-size:13px;color:var(--mut)}
.rede{background:var(--melhoria-bg);border-radius:6px;padding:6px 9px;font-size:12.5px;margin-top:8px}
.rede::before{content:"rede de segurança hoje: ";font-weight:600;color:var(--melhoria)}
ol.fila{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0;padding:16px 16px 16px 40px}
ol.fila li{margin:9px 0;font-size:14px}
.fonte{color:var(--mut);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:10px}
"""

_JS = """
var mx=document.getElementById('mx');
if(mx){
  mx.addEventListener('mouseover',function(e){
    var td=e.target.closest('td,th'); if(!td) return;
    var todos=mx.querySelectorAll('td,th'),i;
    for(i=0;i<todos.length;i++) todos[i].style.background='';
    if(td.closest('tbody')){
      var cs=td.parentNode.cells, idx=td.cellIndex, r;
      for(i=0;i<cs.length;i++) cs[i].style.background='#eaf1fa';
      for(i=0;i<mx.rows.length;i++){ r=mx.rows[i]; if(r.cells[idx]) r.cells[idx].style.background='#eaf1fa'; }
    }
  });
  mx.addEventListener('mouseleave',function(){
    var todos=mx.querySelectorAll('td,th');
    for(var i=0;i<todos.length;i++) todos[i].style.background='';
  });
}
"""


def _esc(t):
    return _html.escape(str(t), quote=False)


def _marca(m):
    if not m:
        return "<td></td>"
    letras, _, nota = m.partition(" ")
    dentro = "".join(f'<span class="{"l" if ch == "L" else "e"}">{ch}</span>' for ch in letras)
    if nota:
        dentro += f' <span class="nota">{_esc(nota)}</span>'
    return f'<td class="m">{dentro}</td>'


def _item(titulo, texto, tag=""):
    t = f'<span class="tag">{_esc(tag)}</span>' if tag else ""
    return f'<div class="item"><b>{_esc(titulo)}</b>{t}<p>{_esc(texto)}</p></div>'


def _lane(titulo, quando, itens, cor):
    corpo = "".join(itens)
    return (f'<div class="lane" style="--lc:var(--{cor});--lb:var(--{cor}-bg)">'
            f'<h3>{_esc(titulo)}</h3><div class="quando">{_esc(quando)}</div>{corpo}</div>')


def gerar(proj, kit=None, out=None) -> Path:
    proj = Path(proj)
    kit = Path(kit) if kit else Path(__file__).resolve().parent.parent
    out = Path(out) if out else proj / "docs"
    out.mkdir(parents=True, exist_ok=True)

    v = versao_kit(kit)
    cmds = comandos(kit)
    hks = hooks_do_kit(kit)
    rls = rules_do_kit(kit)
    orc = orcamento(proj)
    ev = evals(proj)
    n_testes = testes(proj)
    fila = a_fazer(proj)
    passo = proximo_passo(proj)

    total_cmd = sum(c["bytes"] for c in cmds)
    hk_reg = sum(1 for h in hks if h["registrado"])
    hk_opt = len(hks) - hk_reg

    stats = [
        f"<span class='stat'><b>{len(cmds)}</b> comandos ({total_cmd:,} B)</span>".replace(",", "."),
        f"<span class='stat'><b>{len(hks)}</b> hooks ({hk_reg} registrado · {hk_opt} opt-in)</span>",
        f"<span class='stat'><b>{len(rls)}</b> rules path-scoped</span>",
    ]
    if n_testes:
        stats.append(f"<span class='stat'><b>{n_testes}</b> testes na suíte</span>")
    if ev["total"]:
        ab = f" · <b style='color:var(--risco)'>{len(ev['abertos'])} abertos</b>" if ev["abertos"] else " · 0 abertos"
        stats.append(f"<span class='stat'>corpus <b>{ev['total']}</b> casos{ab}</span>")
    if orc:
        soma = sum(o["bytes"] for o in orc)
        stats.append(f"<span class='stat'>partida <b>{soma:,} B</b> medidos</span>".replace(",", "."))

    # lanes ------------------------------------------------------------------
    partida = [_item(t, x) for t, x, _ in LANE_PARTIDA]

    evento = []
    for h in hks:
        if h["registrado"]:
            evento.append(_item(h["arquivo"], " · ".join(h["eventos"]) or "registrado no hooks.json",
                                "hook LIGADO"))
        else:
            evento.append(_item(h["arquivo"], "presente e NÃO registrado — só entra por opt-in "
                                              "(settings.json).", "opt-in"))
    for r in rls:
        evento.append(_item(f"rule {r['nome']}", "acende ao tocar: " + ", ".join(r["paths"]),
                            ".claude/rules/"))

    invocaveis = [c for c in cmds if not c["disable"]]
    executaveis = [c for c in cmds if c["disable"]]
    demanda = [_item(f"/mss-spec:{c['nome']}", c["description"], f"{c['bytes']:,} B".replace(",", "."))
               for c in invocaveis]
    demanda.append(_item(f"+ {len(executaveis)} comandos disable-model-invocation",
                         "o assistente EXECUTA lendo commands/<x>.md (nunca invoca via Skill): " +
                         ", ".join(c["nome"] for c in executaveis) + ".", "executar, não invocar"))

    fecho = [_item(t, x) for t, x, _ in LANE_FECHO]

    lanes = (
        _lane("Partida — automático", "toda sessão, antes de qualquer trabalho", partida, "partida")
        + _lane("Por evento — automático", "no meio do trabalho, quando a condição acontece",
                evento, "evento")
        + _lane("Sob demanda — invocado", "quando o owner chama (ou o assistente propõe)",
                demanda, "demanda")
        + _lane("Fecho — ao concluir o assunto", "sequência fixa antes de integrar", fecho, "fecho")
    )

    # matriz -----------------------------------------------------------------
    cab = "<th>artefato ▸ ator</th>" + "".join(f"<th>{_esc(a)}</th>" for a in ATORES)
    linhas = ""
    for artefato, mapa, _ in MATRIZ:
        cels = "".join(_marca(mapa.get(a, "")) for a in ATORES)
        linhas += f"<tr><td><code>{_esc(artefato)}</code></td>{cels}</tr>"

    # riscos (curados + dinâmicos) --------------------------------------------
    rcards = ""
    for titulo, grau, texto, rede, _ in RISCOS:
        if "comandos crescem" in texto:
            texto = texto.replace("bytes medidos no topo do painel",
                                  f"{total_cmd:,} B em {len(cmds)} arquivos hoje".replace(",", "."))
        rcards += (f'<div class="rcard"><h4>{_esc(titulo)} <span class="grau">{_esc(grau)}</span></h4>'
                   f'<p>{_esc(texto)}</p><div class="rede">{_esc(rede)}</div></div>')
    for caso in ev["abertos"]:
        rcards += (f'<div class="rcard"><h4>Caso {_esc(caso)} do corpus está ABERTO '
                   f'<span class="grau">medido</span></h4><p>Falha registrada em docs/EVALS.md que '
                   f'ainda não virou guardrail — dívida de prosa viva.</p>'
                   f'<div class="rede">fechar o caso (guardrail + teste); o release sinaliza.</div></div>')
    for o in orc:
        if o["bytes"] > o["teto"]:
            rcards += (f'<div class="rcard"><h4>Orçamento estourado: {_esc(o["arquivo"])} '
                       f'<span class="grau">medido</span></h4><p>{o["bytes"]:,} bytes contra o teto de '
                       f'{o["teto"]:,} — arquivo de partida acima do teto vira regra ignorada.</p>'
                       f'<div class="rede">poda por mover-nunca-apagar (doctor check 9 aponta).</div></div>'
                       ).replace(",", ".")

    # fila --------------------------------------------------------------------
    itens_fila = ""
    if passo:
        itens_fila += f"<li><b>Próximo passo (MAPA):</b> {_esc(passo)}</li>"
    for item in fila:
        itens_fila += f"<li>{_esc(re.sub(chr(96), '', item))}</li>"
    if not itens_fila:
        itens_fila = "<li>nada declarado — MAPA/INDEX sem pendência aberta.</li>"

    orc_txt = " · ".join(f"{o['arquivo']} {o['bytes']:,}/{o['teto']:,} B".replace(",", ".")
                         for o in orc) or "sem arquivos de partida no projeto"

    html_final = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>anatomia de runtime — mss-spec v{v}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>Anatomia de runtime — mss-spec <small>v{v} · projeto: {_esc(proj.name)}</small></h1>
  <p class="sub">Quando cada peça do kit entra na janela do assistente, quem lê × quem escreve cada
  artefato, riscos e fila. Números <b>medidos</b> do repo na geração; matriz e classes de risco são
  metadado curado do kit, travado por teste (só cita arquivo que existe).</p>
  <div class="stats">{''.join(stats)}</div>
</header>
<main>
<h2>1 · Quando cada peça entra na janela</h2>
<p class="h2sub">Quatro regimes de disparo — só a coluna azul custa contexto em toda sessão
(orçamento medido: {orc_txt}).</p>
<div class="lanes">{lanes}</div>

<h2>2 · Quem lê × quem escreve cada artefato</h2>
<p class="h2sub">Passe o mouse pra cruzar linha e coluna.
<span class="legend"><b class="l">L</b> = lê · <b class="e">E</b> = escreve · vazio = não toca.</span></p>
<div class="wrap"><table id="mx"><thead><tr>{cab}</tr></thead><tbody>{linhas}</tbody></table></div>

<h2>3 · Suscetível a falha — o que pode quebrar e o que já segura</h2>
<p class="h2sub">Classes curadas do kit + o que a geração mediu agora (casos abertos, orçamento).</p>
<div class="cards">{rcards}</div>

<h2>4 · Fila — o que o próprio repo declara</h2>
<ol class="fila">{itens_fila}</ol>

<p class="fonte">Gerado por templates/anatomia.py (kit v{v}) a partir de: manifestos ·
frontmatter de commands/ · hooks/hooks.json · templates/rules/ · orçamento em bytes ·
docs/EVALS.md · MAPA/INDEX. Saída derivada e regenerável — fora do git de propósito.</p>
</main>
<script>{_JS}</script>
</body>
</html>
"""
    destino = out / "anatomia.html"
    destino.write_text(html_final, encoding="utf-8", newline="\n")
    return destino


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gera o painel 'anatomia de runtime' do kit mss-spec.")
    ap.add_argument("--proj", help="diretório do projeto (default: diretório atual)")
    ap.add_argument("--kit", help="raiz do plugin (default: a pasta acima deste script)")
    ap.add_argument("--out", help="pasta de saída (default: <proj>/docs)")
    args = ap.parse_args(argv)
    destino = gerar(proj=args.proj or Path.cwd(), kit=args.kit, out=args.out)
    print(f"anatomia gerada: {destino}")


if __name__ == "__main__":
    main()
