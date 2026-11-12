# Ao testar

- **quando escrever teste pra comando ou skill do kit** → [Comando-prosa não se testa como código](../feedback_comandos_prosa_nao_unit_test.md) — wiring no smoke, nunca unit test teatral
- **quando for validar uma tela ou UI** → [Validação de UI só determinística](../feedback_validacao_ui_deterministica.md) — nunca dirigir o browser ao vivo; smoke visual = humano
- **quando provar um hook do kit como processo, mandando o evento pela entrada do programa** → [Hook pelo PowerShell chega com marca](../project_hook_pelo_powershell_chega_com_marca.md) — pelo pipe do PowerShell 5.1 o hook sai calado; chame pelo Bash, lendo o evento de um arquivo
- **quando carregar módulo por `spec_from_file_location` num teste e ele tiver `@dataclass`** → [importlib + dataclass precisa de sys.modules](../project_importlib_dataclass_precisa_de_sys_modules.md) — Python 3.14: registre `sys.modules[spec.name] = mod` antes do `exec_module`, senão `'NoneType' has no attribute '__dict__'`
