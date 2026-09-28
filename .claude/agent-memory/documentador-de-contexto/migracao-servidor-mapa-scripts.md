---
name: migracao-servidor-mapa-scripts
description: Onde ler cada passo do kit de migração (ops/provisionamento/), quem toca o quê e a armadilha do ambiente Bash concedido ao agente de contexto
metadata:
  type: project
---

Colheita de 2026-09-24 sobre `/opt/wiki/ops/provisionamento/` (migração do notebook, 192.168.1.5,
para a torre nova). Mapa completo em
`.agents/runtime/contexto/2026-09-24-migracao-plano-passos-3b-a-11.md`.

**Armadilha de ambiente**: o Bash concedido ao agente de contexto pode rodar na máquina VELHA
(notebook, produção) mesmo com `cwd` dentro do repositório compartilhado — confira sempre com
`hostname`/`uname -a` antes de medir `du`/`df`, e não assuma que está na torre só porque a
encomenda fala dela. Neste caso: `hostname` = `debian`, kernel Debian 6.1.187, `df -h /storage
/mnt/hdd` batendo com os números de produção citados na doc — ou seja, o Bash era o do notebook.
`ip` está fora da lista de leitura permitida ao colhedor de contexto (hook bloqueou).

**Estrutura do LEIA-ME.txt**: `grep -n '┌─ PASSO' LEIA-ME.txt` acha todos os blocos (inclusive os
dois blocos "REGISTRO" aposentados da rota do autoinstall, no fim do arquivo — não confundir com
os passos ativos).

**Os três scripts com validação FRACA de caminho** (aceitam qualquer diretório, não só o
Toshiba): `fazer-backup-frio.sh --destino <dir>` (linha 26), `migrar-dados.sh --backup <dir>`
(linha 43, usado só como prefixo de string). Isso é achado de leitura de código, não afirmação da
doc — a doc só descreve a rota física do Toshiba.

**`migrar-tudo.sh` não tem `--seco` de verdade para o passo pesado**: ele repassa `--seco` a
`restaurar-segredos.sh`, `restaurar-etc.sh` e `provisionar.sh`, mas `migrar-dados.sh` não aceita a
flag — no modo seco essa chamada simplesmente não roda (só imprime o comando).

**Cadeia da chave SSH**: `CHAVE_DONO=/home/$DONO/.ssh/id_ed25519` (comum.sh:158) não existe na
torre antes do PASSO 4. `migrar-dados.sh` resolve isso sozinho: restaura `/home` no passo 1/9
ANTES de tentar qualquer SSH para a velha (primeiro uso em `:406`). Não é ovo-e-galinha.

**Passos que afetam produção (notebook) de verdade**: PASSO 4 (congela escritores pela rede, mas
NÃO nginx/cloudflared), PASSO 6 (cutover, make-before-break, ~10s reversível), PASSO 8 (`congelar-
velha.sh --sim`, mascara TUDO inclusive nginx — sem `--sim` sai 0 sem fazer nada, armadilha
clássica se alguém citar o comando sem a flag).
