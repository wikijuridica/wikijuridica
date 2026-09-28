---
name: commit-por-pathspec-leva-o-d-do-vizinho
description: Commit escopado por pathspec carrega a remoção que outra sessão já estagiou dentro daquele pathspec; e git diff refresca o índice mesmo com GIT_OPTIONAL_LOCKS=0
metadata:
  type: project
---

Escopar commit por pathspec **não** isola do índice compartilhado. Medido em git 2.39.5,
repositório de rascunho:

- `commit -F msg -- <caminhos>` monta o candidato de HEAD **mais** o que estiver estagiado
  **dentro** do pathspec. Um `D` que outra sessão estagiou para um caminho da lista **entra no
  commit**. Fora do pathspec, não entra.
- `status --porcelain` escreve `.git/index`; com `GIT_OPTIONAL_LOCKS=0` não escreve.
- `diff --quiet -- <caminhos>` escreve o índice **com ou sem** a variável — para o diff do
  worktree o refresh não é opcional.
- `diff --cached` e `ls-files --others` não escrevem em nenhum dos casos.

**Why:** em `/opt/wiki` o índice é compartilhado entre sessões concorrentes, e a regra
"`git add` por caminho exato" protege só o que EU estagio — não o que já estava lá. Uma porta
autônoma que confere remoção apenas depois do próprio `add` fica vazia na volta seguinte.

**How to apply:** ferramenta que commita sozinha confere `diff --cached --name-status --
<caminhos>` **antes e depois** de estagiar. Para saber se há o que commitar, uma leitura
`status --porcelain --untracked-files=all` sob `GIT_OPTIONAL_LOCKS=0` — nunca `diff` do
worktree, que escreve o índice de produção até num ensaio a seco. Relacionado:
[[bancada-nao-escreve-em-producao]].
