# Check de versão do plugin contra o remoto — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Adicionar ao `/mss-spec:doctor` um check "versão do kit" que compara a versão instalada com a publicada no remoto (git fetch no clone, semver) e reporta ✓/⚠/ℹ — só reporta, degrada gracioso offline/dev.

**Architecture:** O `doctor` é um comando-**prosa** (`commands/doctor.md`) que o assistente executa. A feature é um novo item na lista de checks, escrito em prosa, mais um **smoke test** (`tests/test_smoke_kit.py`) que trava as referências-chave no `.md` (padrão do repo — comandos não têm unit test).

**Tech Stack:** Markdown (comando-prosa) + pytest (smoke test de wiring). Sem código de aplicação.

---

### Task 1: Smoke test do check de versão (TDD — vermelho primeiro)

**Files:**
- Modify: `tests/test_smoke_kit.py` (novo teste `test_doctor_check_versao_wiring`)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `tests/test_smoke_kit.py`:

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_smoke_kit.py::test_doctor_check_versao_wiring -v`
Expected: FAIL (o `doctor.md` ainda não tem "git fetch"/"marketplace update"/etc.)

### Task 2: Adicionar o check "versão do kit" no doctor.md (verde)

**Files:**
- Modify: `commands/doctor.md` (novo item na lista de Checks + menção na linha de saída)

- [ ] **Step 1: Acrescentar o check à prosa do doctor**

Adicionar um item 8 na lista "Checks:" do `commands/doctor.md`, descrevendo: ler a `version` do `plugin.json` no clone localizado (instalada); no mesmo clone, `git fetch` silencioso + ler a `version` de `origin/<ref>` (`git show origin/<ref>:.claude-plugin/plugin.json`) como publicada — mesmo canal do `marketplace update`, não HTTP raw; comparar **semver** (não commit); reportar ✓ (iguais) / ⚠ com `claude plugin marketplace update <nome>` (instalada < publicada; **não roda**) / ℹ "à frente (dev)" (instalada > publicada); degradar gracioso — fetch falha (offline) ou clone sem remote → "a verificar"/pulado, **nunca ✗**.

- [ ] **Step 2: Rodar o teste novo e ver passar**

Run: `python -m pytest tests/test_smoke_kit.py::test_doctor_check_versao_wiring -v`
Expected: PASS

- [ ] **Step 3: Rodar a suíte inteira (anti-regressão)**

Run: `python -m pytest tests/ -q`
Expected: tudo verde (os testes existentes + o novo)

- [ ] **Step 4: Commit**

```bash
git add commands/doctor.md tests/test_smoke_kit.py
git commit -m "feat(doctor): check de versão do kit contra o remoto"
```

---

## Self-review
- **Cobertura da spec:** os 6 ACs da spec (✓ iguais / ⚠ atrás+comando / ℹ à frente / gracioso offline+dev / só reporta) estão cobertos pela prosa da Task 2 e travados pelo teste da Task 1. ✓
- **Placeholders:** `<ref>`/`<nome>` são placeholders de runtime intencionais (o comando resolve). Sem TBD. ✓
- **Consistência:** o teste da Task 1 checa exatamente os termos que a Task 2 escreve (`git fetch`, `marketplace update`, `plugin.json`, `a verificar`/`pulado`, `semver`). ✓
