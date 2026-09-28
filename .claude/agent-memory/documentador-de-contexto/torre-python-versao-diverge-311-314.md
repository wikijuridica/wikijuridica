---
name: torre-python-versao-diverge-311-314
description: torre (Ubuntu 26.04) tem python3 3.14 como default; notebook (Debian 12) tem 3.11.2 — pip install --user de ~/.local/bin não sobrevive à migração
metadata:
  type: project
---

Medido em 2026-09-24 (auditoria de migração, fatia C): o notebook roda `python3` 3.11.2
(Debian 12, `python3 -c 'import sys;print(sys.version)'`). A torre nova (Ubuntu 26.04) tem
`python3` **3.14.3-0ubuntu2** como default do sistema (medido via ssh pelo chefe,
`inventario-torre.txt`, seção `dpkg`; `command-v` mostra `python3.11 AUSENTE` na torre).

**Por quê importa:** os ~208 executáveis de `~/.local/bin` do notebook incluem dezenas de shims
`pip install --user` com shebang `#!/usr/bin/python3` (ex.: `chardetect`, `alphashape`, `cbor2`,
`ckeygen`, `cftp`). O pacote instalado mora em `~/.local/lib/python3.11/site-packages`, fora do
`sys.path` de um interpretador 3.14 — o `ldd` não detecta esse tipo de quebra (roda contra o
binário `/usr/bin/python3`, presente nos dois lados; o que falta é o pacote Python, não a lib
ELF). Isso é diferente do `.venv-tools311` (uv standalone, isolado, já resolvido para
`supervise-process-tree` — ver achado do chefe de 12:40 em
`migracao-auditoria-achados-compartilhados.md`) — aqui é o Python DO SISTEMA que mudou de versão
major entre as duas máquinas.

**Como aplicar:** antes de assumir que "o home veio no tar, então a ferramenta funciona", separe
binário nativo (ELF, resolve por `ldd`) de shim interpretado (script + pacote instalado à parte,
resolve por versão do interpretador + `site-packages`). Ferramenta relevante encontrada só depois
da migração completa exige reinstalação explícita (`pip install --user` ou `uv tool install`) na
máquina nova, não cópia de arquivo.

Ver também: `hook-so-permite-leitura-listada.md` (como medir dpkg/version sem `apt-mark`/`ssh`
direto) e o mapa completo em
`.agents/runtime/contexto/2026-09-24-migracao-auditoria-C-binarios.md`.
