---
name: bancada-nao-escreve-em-producao
description: Caso de teste que cria e apaga arquivo em diretório de produção vira varredura de outra sessão e deleção proibida — monte cenário próprio com --raiz
metadata:
  type: feedback
---

Caso de bancada nunca cria arquivo dentro de diretório de produção, nem para provar recusa.
Monte o cenário no `$TMPDIR` e aponte a ferramenta para ele (`--raiz`, `cd`, dublê do registro).

**Why:** escrevi um caso que criava symlink em `data/editorial/v2_pages/` e o removia com
`rm -f`. Três danos possíveis num intervalo de milissegundos: outra sessão fazendo `git add` por
diretório varre o link para dentro de um commit; bancada interrompida deixa o link para trás; e
apagar arquivo do repositório é a espécie de ato que o contrato do cérebro acabara de proibir.

**How to apply:** vale para symlink, arquivo `.bak`, ordinal inventado e qualquer fixture de
caminho. Se o cenário próprio não conseguir reproduzir o caso, o que falta é uma flag de raiz na
ferramenta — construa a flag (e exija `--seco` junto, para que ela nunca escreva histórico
alheio), não o arquivo em produção. Relacionado:
[[commit-por-pathspec-leva-o-d-do-vizinho]], [[ajudante-ausente-deixa-bancada-verde]].
