---
name: webfetch-trunca-e-parafraseia
description: WebFetch resume/parafraseia e pode truncar páginas longas (Rufus FAQ) ou não seguir redirect (documentation.ubuntu.com); para citação literal use curl + grep
metadata:
  type: feedback
---

Ao colher documentação oficial para citação literal (o mandato exige "trecho literal curto"),
`WebFetch` não é confiável como fonte do texto exato: ele passa a página por um modelo pequeno que
resume e pode truncar ("Content truncated due to length...", visto na FAQ do Rufus,
`github.com/pbatard/rufus/wiki/FAQ`, que tem 4.137 linhas). Uma citação de "enum
`WLANSupportInstallState`" veio do "conhecimento do modelo" (WebSearch), não do arquivo — o nome
real, achado só ao ler o código-fonte com `curl`, é `PackageInstallState`
(`subiquity/common/types/__init__.py`).

**Como aplicar**: para qualquer citação que vá para o arquivo de contexto como "trecho literal",
baixe a página com `curl -s URL -o /tmp/arquivo.html` (ou `.py`, `.rst`) e `grep -n -A N 'padrão'`
sobre o arquivo bruto. `WebFetch`/`WebSearch` servem para *achar* a URL certa e ter uma primeira
leitura de orientação — nunca como fonte da citação final.

**Duas armadilhas de URL vistas nesta colheita**:
- `documentation.ubuntu.com/server/...` faz 301 para `ubuntu.com/server/docs/...`, e o `WebFetch`
  não segue esse redirect sozinho (devolve "REDIRECT DETECTED", pede nova chamada manual) — em
  compensação `curl -sIL` segue sem problema.
- `raw.githubusercontent.com/wiki/<user>/<repo>/<Page>.md` **não existe** para wikis do GitHub (dá
  404) — o wiki é servido só pela página HTML normal (`github.com/<user>/<repo>/wiki/<Page>`), que
  precisa de `curl` + `grep -A N` para extrair o texto sob as tags HTML (`sed 's/<[^>]*>//g'`
  também ajuda a limpar).

Ver também: `.claude/agent-memory/documentador-de-contexto/api-github-code-search-exige-auth.md`
(a buscar, se ainda não existir) — a busca de código do GitHub (`api.github.com/search/code`) exige
autenticação (401 sem token), então achar arquivo-fonte por nome exige listar o diretório primeiro
(`api.github.com/repos/<org>/<repo>/contents/<path>`), nunca adivinhar o nome do arquivo.
