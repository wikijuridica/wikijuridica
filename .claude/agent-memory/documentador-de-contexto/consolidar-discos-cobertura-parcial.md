---
name: consolidar-discos-cobertura-parcial
description: consolidar-discos.sh (PASSO 10 da migração) só copia/recria uma parte do que existe nos discos velhos — mapa completo do que fica para trás
metadata:
  type: project
---

Colheita de 2026-09-24 (fatia F da auditoria de migração), mapa completo em
`.agents/runtime/contexto/2026-09-24-migracao-auditoria-F-dados-discos-20260924.md`.

`ops/provisionamento/consolidar-discos.sh` (lido inteiro, 23.565 B) copia por `rsync` só: blobs
Ollama, VM do Claude Desktop, CPython do `uv`, logs históricos (nginx/journal/audit),
`/usr/local/bin` (critério por `ldd`) e `/usr/local/lib/ollama`. Recria só **3 de 6** symlinks de
`/mnt/hdd/arquivo/*`: `codex-sessions`, `android-vm-lab`, `opt-backups`. **Ficam sem atalho**
`gnome-boxes` (27G) e `codex-logs` (9G) — o dado não se perde (HDD monta `ro,noload` inteiro no
fstab), só falta o `ln -sfn` para achar por `~`.

**Stack de token A3 fora de `/opt/wiki`/`/opt/escritorio`** (`jsignpdf`, `OpenWebStart`,
`pjeoffice-pro`, `certisign-websigner`, `softplan-websigner`, `serpro`, ~1G somados) não está em
`fazer-backup-frio.sh` nem em `consolidar-discos.sh` — os symlinks de `/usr/local/bin` que
apontam para dentro deles ficam mortos a menos que outro passo (não documentado nos 4 arquivos do
kit) os instale. `/opt/google` é a exceção: já existe na torre antes mesmo do PASSO 10 (medido no
inventário do chefe via ssh), confirmando que chega por pacote/instalador — reforça que os outros
6 também deveriam.

`/storage` do notebook tem 234G/276G usados; só 51G (Ollama+VM) atravessam por desenho. O resto —
`cache` 58G, e três diretórios datados do PRÓPRIO dia da migração (`ensaio-migracao` 45G,
`ensaio-instalacao-simples` 38G, `iso-migracao` 36G) — são artefatos do ensaio da migração, não
dado de produção a levar; não confundir com achado de perda.

**Espaço na torre não é gargalo**: inventário do chefe (`torre-inventario-20260924/inventario-torre.txt`,
seção `### df`) mediu `3,6T` no NVMe único, `145G` usado, `3,3T` livre — folga enorme sobre o
payload real (~51G) do PASSO 10.

Ver também [[hook-colhedor-barra-ssh]] (por que não deu para medir a torre direto nesta rodada) e
[[migracao-servidor-mapa-scripts]] (mapa geral dos passos 3b-11).
