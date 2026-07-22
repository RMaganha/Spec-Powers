---
name: project_mss_spec_instalado_por_junction
description: na máquina do owner o mss-spec é carregado por JUNCTION em ~/.claude/skills/mss-spec → este clone de dev; edições são live em TODO projeto; NÃO precisa marketplace update / pull / push — só recarregar a sessão
metadata:
  type: project
---

Na máquina de desenvolvimento do owner, o **mss-spec NÃO é um plugin de marketplace**. Ele é carregado
como **skill de nível de usuário via junction** (symlink do Windows):

```
~/.claude/skills/mss-spec  →  C:\Ronaldo\_Mitsui\Python\Spec-Powers   (este clone de dev)
```

Confirmado (2026-07-22): **não** aparece em `~/.claude/plugins/installed_plugins.json` nem em
`known_marketplaces.json`; o `~/.claude/settings.json` só habilita o `superpowers`. O item
`~/.claude/skills/mss-spec` é um **Junction** apontando pro clone.

**Consequências (importantes pra não mandar o owner numa corrida à toa):**
- **Todo projeto** da máquina (MSS-SSC, etc.) usa o código **deste clone no instante em que é salvo aqui** —
  **sem** `claude plugin marketplace update`, **sem** `git pull`, **sem** `git push` pro uso local.
- `claude plugin marketplace update mss-spec` **falha / não faz nada** (não há marketplace mss-spec
  registrado) — **não** sugerir esse comando pra este setup.
- Pra uma sessão **já aberta** pegar comandos/templates alterados: **recarregar/reiniciar o Claude Code**
  no projeto (comandos e skills são lidos na partida).
- O `git push` pro GitHub serve só pra **backup / outras máquinas / o check de versão do doctor** — não
  pro uso do owner na própria máquina.

Relacionado: [[project_plugin_load_cross_marketplace]] (por que o load é via skills-dir/symlink, não
dependência declarada), [[project_marketplace_relative_path_serve_git_e_local]].
