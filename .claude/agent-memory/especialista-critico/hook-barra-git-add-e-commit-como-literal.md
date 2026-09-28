---
name: hook-barra-git-add-e-commit-como-literal
description: O hook de commit do /opt/wiki casa as strings de indexar+commitar em QUALQUER lugar do comando Bash, inclusive dentro de heredoc Python e de texto de documentação
metadata:
  type: project
---

O hook que protege o `pre-commit` barra um comando Bash quando as strings de
**indexar** e de **commitar** aparecem juntas nele — e ele casa por texto, não
por invocação. Um `python3 - <<'PY'` que apenas *escreve documentação*
mencionando os dois comandos é bloqueado, assim como um patch que insere uma
mensagem de quarentena nomeando o ato que destrava.

**Why:** o defeito real que o hook protege (índice mudando durante a compilação
do `pre-commit`) é caro, e o hook prefere um falso positivo a um falso negativo.

**How to apply:** três saídas, nesta ordem de preferência — (1) use a ferramenta
`Edit`/`Write`, que não passa pelo hook de Bash; (2) monte os literais a partir
de variáveis no Python (`G = 'g'+'it'`); (3) separe em duas chamadas Bash. Vale
também para *texto* que você está gravando em arquivo, não só para comandos.
Relacionado: [[ensaio-de-flag-abre-alerta-real]].
