---
paths:
  - "tools/requirements-*.txt"
  - "tools/requirements_interpretadores.json"
  - "tools/*-env"
---

# Cada `requirements-*.txt` tem interpretador PROPRIO — medir no python3 do sistema e' medir o ambiente ao lado

Memorias de origem: `gate-mede-o-interpretador-ao-lado.md`,
`pip-user-quebra-todo-venv-do-repo.md`.

Doze arquivos, doze venvs declarados em `.cache/<nome>-venv` (mais o legado em
`${TMPDIR}/opt-wiki-<nome>-venv`, que BUG-098 manteve). Conferir os 46 pins
contra um interpretador so produziu, em 2026-09-10, **cinco divergencias das
quais quatro eram falsas** — `trafilatura`, `torch`, `pip` e `setuptools`
estavam certos nos venvs deles.

## Tres regimes, em `tools/requirements_interpretadores.json`, cada um com prova em arquivo:linha

- **`sempre`** — o consumidor le `WIKI_*_PYTHON` e cai direto no `python3`, sem
  NUNCA consultar o venv
  (`internal/ptbrlexicaldiversity/lexical_diversity.go:654-657` e cinco irmaos).
  O sistema fica vivo **mesmo com o venv no disco**, porque `cmd/check <nome>`
  chamado direto nao passa pelo wrapper que exporta a variavel — foi por ai que
  o `nltk` do sistema derivou para 3.10.3 e reprovou `ptbr-lexical-diversity`.
- **`quando_sem_venv`** — o consumidor consulta o venv ANTES
  (`internal/ossinstallmatrix/matrix.go:1952-1968`). Provisionar o venv tira o
  sistema da conta.
- **`nunca`** — recusa explicita: `internal/ptbrmorphsyntaxoracle/oracle.go:79`
  escreve "nunca cai silenciosamente para o python3 do sistema".

## A armadilha que inverte a medicao: `os.path.realpath`

`.cache/<venv>/bin/python` e' SYMLINK para `/usr/bin/python3.11`. Comparar
interpretadores por `realpath` **iguala venv e sistema**, e o atalho "e' o mesmo
interpretador, resolvo em processo" dispara — o instrumento passa a medir o
sistema achando que mede o venv. Quem define o venv e' o `pyvenv.cfg` ao lado do
caminho **invocado**, nunca o binario para onde o link aponta. Compare por
`os.path.abspath`.

Venv declarado que nao existe no disco **nao e' divergencia**: e' ambiente nao
provisionado, e o conserto e' a materializacao
(`./tools/python-quality-sca-env true`, `./tools/oss-install-matrix-env true`).

## Por que venv some: `pip.conf` desta maquina tem `user = true`

`~/.config/pip/pip.conf` declara `break-system-packages = true` e `user = true`.
Fora de venv e' a escolha do dono; **dentro** de um venv o pip recusa:
`ERROR: Can not perform a '--user' install. User site-packages are not visible in
this virtualenv.` Medido em 2026-09-10: **nenhum** dos quinze wrappers de
`tools/` que criam venv declarava `PIP_USER`, e tres venvs estavam ausentes em
silencio — `.cache/oss-python-venv`, `.cache/python-quality-sca-venv` e
`.cache/zizmor-workflow-security-venv`. O do SCA e' o ambiente de `ruff`, `mypy`,
`pip-audit` e `pip-licenses`: **`sca-staticcheck` nao tinha onde rodar.**

O defeito e' invisivel ate alguem tentar: venv criado ANTES da mudanca do
pip.conf continua vivo; o wrapper so falha ao criar um venv NOVO — e falha
**depois** de ja ter criado o diretorio, deixando `bin/python` valido e
site-packages vazio, o estado mais enganoso possivel. O conserto e' `PIP_USER=0`
no ponto de uso, que nao contorna a configuracao do dono: afirma a intencao.

Tres armadilhas medidas ao consertar a familia de wrappers:

1. `VAR=x funcao_de_shell` propaga ao filho **em bash** (medido com
   `f() { timeout 5 env; }` e `PIP_USER=0 f`), mas a assinatura difere de
   `VAR=x comando_externo` — vale medir, nao deduzir.
2. **Editar um script enquanto o bash o executa corrompe a execucao**: o bash le
   por offset de byte, e um `oss-install-matrix-env` em curso quebrou com
   `rements-oss-install-matrix-*.ok: comando nao encontrado` (exit 127) so porque
   o arquivo foi editado no meio. `bash -n` passa: o arquivo esta integro.
3. **Provar o diagnostico nao e' provar o conserto**: teste que so faz `grep` da
   string no wrapper confere o rotulo, nao o comportamento. A prova e' rodar o
   wrapper com `env | grep -c '^PIP_USER'` = 0.

## Antes de afirmar que um pin esta violado

Resolva QUEM executa aquele arquivo — `grep -rln <basename do requirements>
tools/ internal/ cmd/` — e leia o consumidor ate achar a resolucao do
interpretador. Mapa que declara ambiente e' afirmacao sobre o disco: acompanhe-o
de teste que confira cada entrada contra o consumidor citado. E **prove por
mutacao COM VENV VIVO**: com venv ausente os tres regimes sao indistinguiveis, e
tres mutantes sobreviveram na primeira bancada por causa disso.
