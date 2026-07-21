# Captura de memória (decisões + diário de sessão) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidar no `/mss-spec:memory` um ritual de captura que destila a sessão em decisões (incl. "não fazer") + diário de sessão datado/indexado, roteando pras 3 camadas de memória, com gatilho determinístico no fecho + hook opt-in só como rede.

**Architecture:** Comando-prosa (markdown que o assistente executa), testado por **wiring no smoke** (`tests/test_smoke_kit.py`) — a regra da casa: comando-prosa não se testa como código. Exceção: o hook tem um pedaço de código real (a decisão de *throttle*), que ganha unit test de verdade. Zero stack nova — tudo markdown versionado + 1 script Python pequeno.

**Tech Stack:** Markdown (commands/templates), pytest (smoke + 1 unit), Python (hook opt-in).

**Spec:** [2026-07-21-captura-de-memoria-design.md](../specs/2026-07-21-captura-de-memoria-design.md)

---

## Estrutura de arquivos

| Arquivo | Responsabilidade | Ação |
|---|---|---|
| `commands/memory.md` | comando de memória com 2 modos (`resgatar` intacto + `capturar` novo) | Modificar |
| `templates/DIARIO.md` | skeleton do índice do diário (`## <data>` → `- [<assunto>] … → sessions/…`) | Criar |
| `templates/CLAUDE.md` | regra `<private>` + índice-primeiro + ponteiro pro diário | Modificar |
| `commands/kickoff.md` | scaffolding: `memory/DIARIO.md` + pasta `memory/sessions/` | Modificar |
| `commands/nova-feature.md` | fecho **delega** a `/mss-spec:memory capturar` + `/mss-spec:mapa` (incl. antes do merge → principal) | Modificar |
| `hooks/capturar_nudge.py` | hook opt-in: função `deve_cutucar` (throttle) + emissão do nudge | Criar |
| `hooks/README.md` | como habilitar o hook (opt-in, off por padrão, não-bloqueante, só cutuca) | Criar |
| `memory/DIARIO.md` | dogfood: o índice do diário do próprio kit | Criar |
| `tests/test_smoke_kit.py` | asserções de wiring (family `test_captura_*`) + unit do throttle | Modificar |
| `docs/LEIA-ME.md` · `docs/decisoes.md` · `docs/superpowers/PLANO-TESTE.md` | docs/índices | Modificar |

> **Nota sobre versionamento:** o diário (`memory/DIARIO.md` + `memory/sessions/*.md`) **é pra ser versionado** — nada de gitignore (diferente da saída derivada do mapa-neural). `memory/` já é versionada.

---

### Task 1: `/mss-spec:memory` ganha o modo `capturar` (mantendo `resgatar`)

**Files:**
- Modify: `commands/memory.md`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste de wiring (vermelho)**

Adicione ao fim de `tests/test_smoke_kit.py`:

```python
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
```

- [ ] **Step 2: Rodar o teste (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_memory_dois_modos -v`
Expected: FAIL (memory.md ainda só tem o modo resgatar).

- [ ] **Step 3: Editar `commands/memory.md`**

- Trocar o `argument-hint` do frontmatter para: `argument-hint: "resgatar | capturar (sem argumento: pergunto qual)"`.
- Ajustar a `description` do frontmatter para citar os 2 modos (ex.: "Memória do projeto: `resgatar` a nativa pro repo · `capturar` a sessão em decisões + diário").
- **Preservar** todo o corpo atual como a seção `## Modo: resgatar` (o texto de hoje, intacto).
- **Acrescentar** a seção `## Modo: capturar`, com este conteúdo (o executor escreve prosa; estes são os pontos obrigatórios que o teste trava):
  - Abre dizendo que **destila a sessão a partir do contexto atual da conversa** (o diff da branch + o que foi decidido/conversado) — **não relê arquivos** (captura barata).
  - **Roteia** cada achado pro lar durável certo, sem inventar destino:
    - decisão transversal ("X em vez de Y porque Z") → **`docs/decisoes.md`** (1 linha);
    - decisão de escopo ("decidiu-se NÃO fazer W") → seção **"Fora de escopo"** do `docs/superpowers/INDEX.md`;
    - narrativa do assunto ("tentou-se, virou isso") → **Histórico** da spec viva em `docs/superpowers/specs/`;
    - aprendizado durável atemporal → arquivo em **`memory/`** + 1 linha no **`memory/MEMORY.md`** (não duplicar fato já coberto — atualiza o arquivo existente);
    - resumo compacto da sessão → **`memory/sessions/<data>-<assunto>.md`** + 1 linha no índice **`memory/DIARIO.md`**.
  - **Foco do resumo de sessão:** priorizar os **pivôs / decisões repensadas** (`cogitou X → repensou por Y → ajustou pra Z`) — a *evolução*, não só o estado final.
  - **`<private>`:** qualquer trecho marcado `<private>…</private>` (na conversa ou no rascunho) **nunca** entra em nada versionado.
  - **OK do owner:** monta e **mostra todos os rascunhos** (o que vai pra onde) e **não grava nada antes de gravar** sem o "ok" do owner.
  - **Não duplicar:** antes de escrever, checa se o índice (`MEMORY.md`/`DIARIO.md`) já cobre o fato/entrada; se sim, atualiza em vez de duplicar.
  - **MAPA:** ao final, **chama `/mss-spec:mapa`** pra reconciliar *Onde estamos*/*Próximo passo* — **não reimplementa** o MAPA aqui.
- No topo do arquivo, acrescente 1 linha dizendo que **sem argumento o comando pergunta qual modo** (resgatar ou capturar).

- [ ] **Step 4: Rodar o teste (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_memory_dois_modos -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/memory.md tests/test_smoke_kit.py
git commit -m "feat(memory): modo capturar (decisões + diário) além do resgatar"
```

---

### Task 2: `templates/DIARIO.md` + dogfood `memory/DIARIO.md`

**Files:**
- Create: `templates/DIARIO.md`
- Create: `memory/DIARIO.md` (dogfood — o índice do próprio kit)
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste (vermelho)**

Adicione:

```python
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
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_diario_template -v`
Expected: FAIL (templates/DIARIO.md não existe).

- [ ] **Step 3: Criar `templates/DIARIO.md`**

Conteúdo (estilo dos outros templates — comentário-guia no topo):

```markdown
<!-- Índice do DIÁRIO DE SESSÃO — mantido pelo /mss-spec:memory capturar.
     Camada de contexto "o que conversamos/decidimos", isolada por captura e barata de reler:
     este índice é leve; o detalhe vive em memory/sessions/<data>-<assunto>.md (abra SÓ o que precisar).
     NÃO leia a pasta inteira — ache a linha por data+assunto e abra o arquivo apontado. -->

# Diário de sessão

<!-- As entradas mais recentes em cima. Uma linha por captura. -->

## <data>
- [<assunto>] <gist de 1 linha — o pivô/decisão central da sessão> → sessions/<data>-<assunto>.md
```

E acrescente, como comentário no fim, a **estrutura do arquivo de sessão** que o `capturar` gera em `memory/sessions/<data>-<assunto>.md`:

```markdown
<!-- Estrutura de memory/sessions/<data>-<assunto>.md (curto — o rastro do raciocínio é o essencial):
# <data-hora> — <assunto>
## Conversamos      — o tema, em 1-3 linhas
## Pivôs            — cada mudança de rumo: cogitou X → repensou por Y → ajustou pra Z  (o CORAÇÃO)
## Rejeitado        — o que se decidiu NÃO fazer, com o motivo
## Fizemos          — o que efetivamente mudou
## Próximo          — próxima ação concreta
-->
```

- [ ] **Step 4: Criar o dogfood `memory/DIARIO.md`**

```markdown
<!-- Índice do diário de sessão do próprio kit mss-spec (dogfood). Ver templates/DIARIO.md. -->

# Diário de sessão — mss-spec

<!-- entradas mais recentes em cima; 1 linha por captura; detalhe em memory/sessions/ -->
```

(A 1ª entrada real — a captura desta própria sessão — será gravada no **fecho** desta feature, via `/mss-spec:memory capturar`.)

- [ ] **Step 5: Rodar (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_diario_template -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add templates/DIARIO.md memory/DIARIO.md tests/test_smoke_kit.py
git commit -m "feat(diario): template do índice de diário + dogfood memory/DIARIO.md"
```

---

### Task 3: `kickoff` faz o scaffolding do diário

**Files:**
- Modify: `commands/kickoff.md`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste (vermelho)**

```python
def test_captura_kickoff_scaffold():
    """kickoff monta o diário no projeto: copia o template e cria a pasta de sessões."""
    kickoff = (REPO / "commands" / "kickoff.md").read_text(encoding="utf-8")
    assert "templates/DIARIO.md" in kickoff, "kickoff não copia templates/DIARIO.md"
    assert "memory/DIARIO.md" in kickoff, "kickoff não cria memory/DIARIO.md"
    assert "memory/sessions/" in kickoff, "kickoff não cria a pasta memory/sessions/"
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_kickoff_scaffold -v`
Expected: FAIL.

- [ ] **Step 3: Editar `commands/kickoff.md`**

Na lista de scaffolding de memória (onde já copia `templates/MEMORY.md` → `memory/MEMORY.md`), acrescente:
- copiar `${CLAUDE_PLUGIN_ROOT}/templates/DIARIO.md` → `memory/DIARIO.md`;
- criar a pasta `memory/sessions/` (diário de sessão, versionada; o `/mss-spec:memory capturar` grava aqui).

- [ ] **Step 4: Rodar (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_kickoff_scaffold -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/kickoff.md tests/test_smoke_kit.py
git commit -m "feat(kickoff): scaffolding do diário (DIARIO.md + memory/sessions/)"
```

---

### Task 4: convenção `<private>` + índice-primeiro nos templates

**Files:**
- Modify: `templates/CLAUDE.md`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste (vermelho)**

```python
def test_captura_private_e_indice():
    """CLAUDE.md do projeto carrega: convenção <private>, ponteiro pro diário, e o índice-primeiro."""
    claude = (REPO / "templates" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<private>" in claude, "CLAUDE.md não documenta a convenção <private> (nunca vira memória)"
    assert "DIARIO.md" in claude, "CLAUDE.md não aponta o diário de sessão (memory/DIARIO.md)"
    assert "pasta inteira" in claude.lower(), \
        "CLAUDE.md não reforça o índice-primeiro (consultar índice; nunca ler a pasta inteira)"
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_private_e_indice -v`
Expected: FAIL.

- [ ] **Step 3: Editar `templates/CLAUDE.md`**

Na seção de memória do template, acrescente (prosa curta com estes pontos obrigatórios):
- **`<private>`:** trecho marcado `<private>…</private>` na conversa **nunca** é gravado em memória/diário/decisões versionados — é o jeito de marcar segredo/ruído que não deve durar.
- **Diário de sessão:** existe `memory/DIARIO.md` (índice datado) apontando `memory/sessions/<data>-<assunto>.md`; é a camada "o que conversamos", lida **sob demanda**.
- **Índice-primeiro (custo):** na partida/consulta, leia o **índice** (`MEMORY.md`/`DIARIO.md`) e abra **só** o arquivo relevante; **nunca leia a pasta inteira** de uma vez (é a amnésia cara que o índice existe pra matar).

- [ ] **Step 4: Rodar (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_private_e_indice -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/CLAUDE.md tests/test_smoke_kit.py
git commit -m "docs(memoria): convenção <private> + índice-primeiro + ponteiro pro diário"
```

---

### Task 5: fecho do `nova-feature` delega a captura (incl. antes do merge → principal)

**Files:**
- Modify: `commands/nova-feature.md`
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste (vermelho)**

```python
def test_captura_delegacao_fecho():
    """O fecho do nova-feature DELEGA a captura ao /mss-spec:memory capturar (não re-descreve inline),
    e a captura entra no caminho do merge → principal (consolidar decisões do assunto)."""
    nova = (REPO / "commands" / "nova-feature.md").read_text(encoding="utf-8")
    assert "/mss-spec:memory capturar" in nova, \
        "nova-feature (fecho) não delega a captura ao /mss-spec:memory capturar"
    # a captura acontece antes de integrar (merge/finishing), consolidando as decisões do assunto
    assert "finishing" in nova.lower(), "nova-feature não posiciona a captura junto ao finishing/integração"
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_delegacao_fecho -v`
Expected: FAIL.

- [ ] **Step 3: Editar `commands/nova-feature.md`**

No passo de fecho (passo 6, onde hoje diz "se surgiu aprendizado durável, grave em `memory/`… atualize o `MAPA.md`…"), **substituir a escrita inline por delegação**:
- "Rode **`/mss-spec:memory capturar`** — ele destila a sessão em decisões (incl. as **negativas**, o insumo anti-re-litígio), grava o **diário de sessão** e roteia memória/decisões/Histórico, e chama o **`/mss-spec:mapa`**." 
- Manter a menção de que isso acontece **antes de integrar** (o `finishing-a-development-branch`/merge → principal já citado ali) — é o momento de consolidar as decisões do assunto.
- Não remover as regras de segurança/release já existentes do fecho; só trocar o "grave memória/MAPA à mão" pela delegação.

- [ ] **Step 4: Rodar (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_delegacao_fecho -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/nova-feature.md tests/test_smoke_kit.py
git commit -m "feat(nova-feature): fecho delega a captura ao /mss-spec:memory capturar + mapa"
```

---

### Task 6: hook opt-in (experimental, desligado por padrão) — a rede

**Files:**
- Create: `hooks/capturar_nudge.py`
- Create: `hooks/README.md`
- Test: `tests/test_smoke_kit.py`

> **Experimental e por último de propósito:** o owner já pegou hook falhando em silêncio. A garantia é o passo determinístico da Task 5; o hook é só conveniência. **Não** é registrado no `plugin.json` (senão viria ligado); é opt-in via `settings.json` do usuário, documentado no README.

- [ ] **Step 1: Escrever os testes (vermelho)**

```python
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
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_hook_throttle tests/test_smoke_kit.py::test_captura_hook_optin_doc -v`
Expected: FAIL (hooks/ não existe).

- [ ] **Step 3: Criar `hooks/capturar_nudge.py`**

```python
"""Hook OPT-IN (experimental) do mss-spec: cutuca pra rodar /mss-spec:memory capturar.

NÃO grava nada e NÃO bloqueia — só emite um lembrete quando faz tempo desde a última captura.
A fonte da verdade é o comando (rodado no fecho); este hook é só a rede. Ver hooks/README.md.
Uso: registrado (opt-in) nos eventos Stop e/ou PreCompact no settings.json do usuário.
"""
import os
import sys
import time

NUDGE = ("[mss-spec] Faz um tempo desde a última captura de memória. "
         "Se fechou um raciocínio/decisão, rode /mss-spec:memory capturar "
         "pra não perder o diário desta sessão.")
INTERVALO_PADRAO_S = 1800  # ~30 min de conversa; ajustável por env MSS_CAPTURA_INTERVALO_S
STATE = os.path.join(os.environ.get("TEMP", "/tmp"), "mss_captura_ultimo.txt")


def deve_cutucar(ultimo_ts, agora, intervalo_s):
    """Decisão pura de throttle: cutuca se nunca cutucou ou se passou o intervalo."""
    if ultimo_ts is None:
        return True
    return (agora - ultimo_ts) >= intervalo_s


def _ler_ultimo():
    try:
        with open(STATE, encoding="utf-8") as f:
            return float(f.read().strip())
    except (OSError, ValueError):
        return None


def _gravar_agora(agora):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            f.write(str(agora))
    except OSError:
        pass


def main():
    agora = time.time()
    intervalo = int(os.environ.get("MSS_CAPTURA_INTERVALO_S", INTERVALO_PADRAO_S))
    if deve_cutucar(_ler_ultimo(), agora, intervalo):
        print(NUDGE)          # stdout do hook entra no contexto do assistente
        _gravar_agora(agora)
    sys.exit(0)               # SEMPRE 0 — não-bloqueante


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Criar `hooks/README.md`**

Conteúdo (pontos obrigatórios que o teste trava):
- Título + 1 parágrafo: hook **opt-in**, **desligado por padrão**, **não-bloqueante**, que **só cutuca** (nunca grava) pra rodar `/mss-spec:memory capturar`. A fonte da verdade é o comando no fecho; **se o hook não disparar, nada se perde**.
- Como habilitar: trecho de `settings.json` registrando `python "${CLAUDE_PLUGIN_ROOT}/hooks/capturar_nudge.py"` nos eventos **`Stop`** e/ou **`PreCompact`** (explicar que **não existe hook nativo "a cada X min"**; o throttle por timestamp aproxima isso a cada ~30 min, ajustável por `MSS_CAPTURA_INTERVALO_S`).
- Aviso honesto: hooks podem falhar em silêncio (experiência do owner) — por isso é rede, não garantia.

- [ ] **Step 5: Rodar (verde)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_hook_throttle tests/test_smoke_kit.py::test_captura_hook_optin_doc -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add hooks/capturar_nudge.py hooks/README.md tests/test_smoke_kit.py
git commit -m "feat(hook): nudge opt-in (Stop/PreCompact) pra captura — experimental, off por padrão"
```

---

### Task 7: docs finais + baseline

**Files:**
- Modify: `docs/LEIA-ME.md` (linha do `/mss-spec:memory` com os 2 modos)
- Modify: `docs/decisoes.md` (1 linha — decisão transversal desta feature)
- Modify: `docs/superpowers/PLANO-TESTE.md` (linhas dos testes novos)
- Test: `tests/test_smoke_kit.py`

- [ ] **Step 1: Escrever o teste (vermelho)**

```python
def test_captura_docs_leiame():
    """LEIA-ME documenta o modo capturar do /mss-spec:memory (o dev descobre a capacidade)."""
    leiame = (REPO / "docs" / "LEIA-ME.md").read_text(encoding="utf-8")
    assert "capturar" in leiame.lower(), "LEIA-ME não documenta o modo capturar do /mss-spec:memory"
```

- [ ] **Step 2: Rodar (vermelho)**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_docs_leiame -v`
Expected: FAIL.

- [ ] **Step 3: Editar as docs**

- `docs/LEIA-ME.md`: na linha/tabela do `/mss-spec:memory`, refletir os 2 modos (`resgatar` a nativa · `capturar` a sessão → decisões + diário).
- `docs/decisoes.md`: acrescentar 1 linha — "**memória em 3 camadas + captura consolidada no `/mss-spec:memory capturar`** (fatos · decisões incl. negativas · diário de sessão datado/indexado), gatilho determinístico no fecho + hook só como rede — em vez de comando novo/serviço/vetorial (claude-mem) — porque casa com os pilares (curada, não-serviço, texto consultável) e não incha o plugin".
- `docs/superpowers/PLANO-TESTE.md`: acrescentar as linhas dos testes `test_captura_*` no inventário (não é o baseline — o baseline é regravado pelo `/mss-spec:plano-teste` no fecho).

- [ ] **Step 4: Rodar (verde) + suíte inteira**

Run: `python -m pytest tests/test_smoke_kit.py::test_captura_docs_leiame -v`
Expected: PASS.
Run: `python -m pytest tests/ -q`
Expected: toda a suíte verde (os testes antigos + os `test_captura_*`).

- [ ] **Step 5: Commit**

```bash
git add docs/LEIA-ME.md docs/decisoes.md docs/superpowers/PLANO-TESTE.md tests/test_smoke_kit.py
git commit -m "docs(captura): LEIA-ME (2 modos) + decisão transversal + inventário de testes"
```

---

## Fecho (fora das tasks — passo 6 do nova-feature)

Depois das 7 tasks verdes: `requesting-code-review` → `/mss-spec:plano-teste` (regrava o baseline) → confirmar que o "Estado atual" da spec bate com o entregue → mudar a linha do INDEX para **fechada** → atualizar o `MAPA.md` (**Próximo passo**) → **rodar a 1ª captura real desta sessão** (`/mss-spec:memory capturar` — o dogfood do diário) → `/mss-spec:release` → `finishing-a-development-branch`.
> Segurança (`docs/SEGURANCA.md`): esta feature **não cria rota/endpoint de integração** — só comandos-prosa + 1 hook local que não recebe entrada externa. Sem gate de authz aplicável.

## Self-review (cobertura da spec)
- **CA1** (roteia + OK) → Task 1. **CA2** (grava sem duplicar, índices) → Task 1. **CA3** (`<private>`) → Task 1 (aplica) + Task 4 (documenta). **CA4** (resgatar intacto) → Task 1. **CA5** (delegação fecho/finishing) → Task 5. **CA6** (diário índice→arquivo) → Task 2 + Task 3. **CA7** (decisão negativa recuperável na partida) → roteamento pra `decisoes.md`/INDEX (Task 1); a leitura na partida já é regra existente do `CLAUDE.md` (anotar-decisoes) — sem teste novo (comportamental). **CA8** (hook opt-in) → Task 6. **CA9** (smoke) → família `test_captura_*` (Tasks 1-7).
- Placeholders: nenhum — `<data>`/`<assunto>` são formatos de template, não pendências.
- Consistência de nomes: `deve_cutucar(ultimo_ts, agora, intervalo_s)` idêntico no teste (Task 6 step 1) e no script (step 3); `test_captura_*` e caminhos batem em todas as tasks.
