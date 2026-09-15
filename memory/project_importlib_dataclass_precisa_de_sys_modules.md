---
name: project_importlib_dataclass_precisa_de_sys_modules
description: módulo carregado por spec_from_file_location (padrão dos testes de hook/script do kit) com @dataclass precisa de sys.modules[spec.name] = mod antes de exec_module no Python 3.14
gatilho: quando carregar um módulo por importlib.util.spec_from_file_location num teste e ele tiver @dataclass
metadata:
  type: project
---

Python 3.14 (o da máquina do owner): `dataclasses` resolve anotações consultando
`sys.modules[cls.__module__]`. O padrão dos testes do kit (`spec_from_file_location` + `module_from_spec`
+ `exec_module`, sem registrar em `sys.modules`) faz isso dar
`AttributeError: 'NoneType' object has no attribute '__dict__'` na definição da 1ª dataclass — antes de
qualquer teste rodar. `from __future__ import annotations` agrava (toda anotação vira string).

**How to apply:** no carregador de teste, `sys.modules[spec.name] = mod` **antes** de `exec_module(mod)`;
no módulo, não use `from __future__ import annotations` (aconteceu em `tests/test_memoria_indice.py`,
2026-09-15; o mesmo carregador está em `test_hook_recall_memoria.py` e `test_rodizio_partida.py`).
Hooks que importam módulo irmão (`recall_memoria.py` → `templates/memoria_indice.py`) fazem o mesmo registro.
