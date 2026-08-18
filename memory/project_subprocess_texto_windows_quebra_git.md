---
name: project_subprocess_texto_windows_quebra_git
description: subprocess com text=True no Windows converte \n em \r\n na entrada — o git recebe o caminho com CR e devolve tudo aspeado; use bytes + `-z`
gatilho: quando chamar processo externo (git, cli) por subprocess no Windows
metadata:
  type: project
---

Ao alimentar um processo externo por **stdin** no Windows, `subprocess.run(..., text=True)` aplica
tradução de fim de linha na **entrada**: o `\n` que você escreveu chega como `\r\n`. Ferramenta que
trata a linha como **dado** (não como texto solto) engasga — o `git check-ignore --stdin` recebeu
`backup/\r`, considerou o CR parte do nome e devolveu o caminho **aspeado** (`"backup/\r"`), então o
parse não casou com nada e o filtro do `.gitignore` **morreu em silêncio**: nenhuma exceção, nenhum
retorno de erro, só um `set()` vazio e o mapa continuando a mostrar a pasta que o projeto ignora.

**Regra:** protocolo com o git (e com CLI em geral) por stdin vai em **bytes**, com o separador que a
ferramenta oferece:

```python
r = subprocess.run(["git", "-C", str(proj), "check-ignore", "-z", "--stdin"],
                   input=b"\0".join(p.encode("utf-8") for p in caminhos),
                   capture_output=True, timeout=15)          # sem text=True
saida = r.stdout.decode("utf-8", "ignore").split("\0")
```

**Why:** o modo `-z`/NUL existe exatamente para caminho com caractere estranho, e bytes tiram a
tradução de newline do caminho. **How to apply:** qualquer integração nova com CLI por stdin — bytes
+ separador explícito; e **teste o caminho feliz de verdade** (foi um teste rodando `git init` num
tmp que expôs isto; um mock teria passado verde).

Relacionado: [[project_dogfood_gerador_diff_antes_depois]] (a mesma rodada: o que só aparece rodando
no real) e [[feedback_testar_js_gerado_node_check]] (verde por substring/mock ≠ funciona).
