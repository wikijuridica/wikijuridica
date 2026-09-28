# Migração do servidor — wikijuridica.com.br

**2026-09-24, 16:10** · Estado: **MIGRAÇÃO CONCLUÍDA, com pendências nomeadas.** Todos os PASSOS do `LEIA-ME.txt` executados na torre: 10 (`consolidar-discos.sh` só com o NVMe velho; 9 modelos do Ollama, IA gera; `/usr/local/bin`; regra udev que refaz o somente-leitura dos discos velhos a cada boot), 10b (VM `escritorio-win11` definida, disco/NVRAM/TPM, desligada), 11 (`IDE VERIFICADO`, terminal), e o que o roteiro não previa: Toshiba em `/mnt/hdd` como destino de backup com os timers habilitados; Drive do escritório montado (AppArmor local do `fusermount3`); `verificar-kit.sh` **verde na torre** (219 ✓) sem afrouxar checagem (namespace das bancadas sob a trava do AppArmor do Ubuntu); `conferir-passo5.sh` 0 falhas. Refutação final (Fable): *concluída com pendências, nada bloqueia* — produção 200 na borda, 5 conectores, 0 units falhadas, bancos `quick_check ok`, `git fsck` limpo. GPU "liga e desliga" medida: ventoinha em zero-RPM, sem defeito. Duas ordens do dono fecham o desenho: **o NVMe velho fica conectado** (só leitura, bloco e fstab) e **o HDD fica de fora** por ora.

**Pendências, por ordem:** (1) primeiro backup na torre em execução às 16:05 (o timer roda às 23:24; o do escritório às 03:20); (2) a entrada `debian` da NVRAM está inativa e é inócua — apagá-la não fecha o vetor, que é a ESP do NVMe velho (`\EFI\BOOT\bootx64.efi`): fecha-se retirando o disco ou limpando `/EFI` dele quando a janela de rollback acabar; (3) ~~o primeiro boot com o fstab pós-transplante~~ **medido às 16:03: boot em 42 s, 0 units falhadas, borda 200, 5 conectores; o NVMe velho trocou de nome (`nvme1n1`→`nvme0n1`) e, por UUID, subiu `RO=1` nas duas partições (regra udev) e montado `ro,noload`; Toshiba em `/mnt/hdd`; Drive montado; primeiro backup do wiki gravado no Toshiba (4.041 commits, 498 s) e o do escritório também;** (4) alertas da cadeia editorial (`onda-diaria`, `publicador-cerebro-noticias-sem-pagina`) são anteriores à migração; (5) exposição na LAN por decisão do dono: `ufw` inativo, sshd com senha, dovecot e glances em `0.0.0.0`; (6) sudo temporário expira 2026-09-25 13:55; a rota do namespace das bancadas depende dele e passa a sair 75 com o motivo; (7) HDD do notebook, quando entrar: `/mnt/hdd-antigo` e os atalhos de `~/.codex`, `gnome-boxes`, `android-vm-lab`; (8) memória: 14,5 GB até o segundo pente; `vm.swappiness=100` do perfil `tuned` de outra sessão fica para rever com 32 GB.

**2026-09-24, 12:31** · Estado: **CUTOVER FEITO — a torre é a produção e o repositório de verdade.** PASSO 4 (`migrar-tudo.sh`) terminou verde depois de dois consertos do kit (`f2c70b6c`); PASSO 5 (`conferir-passo5.sh`, novo, `954636f0`) verde em tudo o que o cutover exige; refutação Fable antes do PASSO 6 achou 14 arquivos de `public/datasets` só no notebook (copiados antes) e o `disk-headroom.timer` que alertaria de hora em hora sem `/mnt/hdd` (adiado). `cutover-tunel.sh` às 12:31: cinco conectores da torre com `readyConnections=4`, só então os cinco do notebook parados. **Medido na borda** (`httpRequestsAdaptiveGroups`, amostra adaptativa, 12:00–13:00 -03): os 503 de 12:02 a 12:30 são as rotas dinâmicas do notebook congelado pelo PASSO 4 (busca/API/MCP fora do ar por ~30 min, previsto no LEIA-ME); depois de 12:31, **nenhum 503**; os únicos 5xx são 504 de um cliente só (UA `nginx-ssl early hints`, `/`, origem 0, `miss`), que em 24 h deu 15 de 15 em 504 **antes e depois** da troca e não chega ao nginx da origem — defeito anterior à migração, aberto (ver *Lacunas abertas em 2026-09-24*). Depois do cutover, na torre: guarda de pre-commit aceita symlink de root do uutils (`f0667c2c`, refutada e mantida), `pam_umask ... nousergroups`, Ollama ligado pelo PASSO 10, units de energia só na Intel (`0aaa747d`), `supervise-process-tree` no Python do sistema porque o do venv não tem pidfd (`855e3969`). O notebook está parado (conectores e escritores) e é a volta — runbook no `LEIA-ME.txt`, PASSO 6. Faltam os PASSOS 7 a 11.

**2026-09-24** · Estado: **rota do autoinstall APOSENTADA; o PASSO 2 passa a ser a ISO OFICIAL com o instalador interativo padrão**, guiado por [`ops/instalacao-simples/GUIA.md`](../../ops/instalacao-simples/GUIA.md). A mídia v12 **instalou** na torre nova (log colhido da partição `writable` do próprio Toshiba: `curtin: Installation finished`, estado `DONE`), mas a tela morria no boot, e o dono via a máquina "travada": o monitor está na RTX 5060 Ti (`vgaarb: setting as boot VGA device`), o `nouveau` tira o console (`Console: switching to colour dummy device 80x25`) e falha no GSP (`gsp: init failed, -22`). A correção é `nouveau.modeset=0` digitado no GRUB **depois do `---`**, e o curtin o copia para o sistema instalado (`install_grub.py`, `get_carryover_params`). A torre **não tem Wi-Fi embutido** (nenhum dispositivo PCI de classe `0x0280`; o "Dell Wireless Device" é teclado e mouse sem fio), então o Wi-Fi vem de um adaptador USB plugado antes da instalação. No Toshiba, desde 2026-09-24: a ISO oficial `ubuntu-26.04.1-live-server-amd64.iso` (sha256 `cc8a95cd…d927`, assinatura da Canonical conferida) e a partição `writable` com o guia, o kit e os dois `.deb` de Wi-Fi do pool da ISO. Ensaios em VM: instalação interativa sem rede VERDE (`ops/instalacao-simples/ENSAIO-INTERATIVO.md`), Wi-Fi WPA2 depois da instalação VERDE com rádio simulado (`ops/instalacao-simples/wifi/ENSAIO-WIFI.md`). Achado no caminho: o "bit flip do USB 2.0" das gravações desde 2026-09-22 era o automount deste notebook marcando o byte 37 do setor de boot da ESP (`comum.sh`, `bloquear_automontagem`). Logs e foto da máquina nova: `/storage/iso-migracao/logs-maquina-nova-20260924/` (com `SHA256SUMS`). *(Os parágrafos de estado abaixo, de 2026-09-22 e 2026-09-23, ficam como registro.)*

**2026-09-23, 17:47** · Estado: **mídia v12 GRAVADA E VERIFICADA no Toshiba** (`TOSHIBA MQ04UBD200 23EQP2RHT`, `IDENTICOS` na tentativa 2, como todas as gravações de hoje pelo USB 2.0), gerada às 17:39 do commit **`28ce471f`**: `/storage/iso-migracao/ubuntu-26.04.1-wikijuridica-autoinstall.iso.v12`, 2.928.238.592 B, sha256 `f2351a027d3a3dd971b95fcde571017ac1dfec082a01062631313a0023c179cf`. **O instrumento é `git diff --stat 28ce471f..HEAD -- ops/provisionamento/`** (vazio = a mídia carrega o kit do HEAD). A v12 = v10 + dois consertos que só o **primeiro boot real** mostrou (o `visudo` do 26.04 é o do `sudo-rs` e recusava o sudoers — a torre passa a usar o sudo clássico por `update-alternatives`; e o resumo do `provisionar.sh` se perdia porque o systemd matava o `tee` da oneshot — agora o script espera o `tee`) + a rede DECLARADA no `user-data` (sem isso o netplan herdava o estado do cabo na hora da instalação: instalar sem cabo deixava o primeiro boot sem IP). O ensaio da própria v12 (gate com a unit do primeiro boot até o marcador, e a variante sem cabo com primeiro boot) está registrado em `docs/goal/ESTADO_MIDIA_E_KIT_20260923.md`, item 7. Histórico do mesmo dia, abaixo. *(Superado às 17:47: a linha seguinte, da v10, fica como registro.)*

**2026-09-23, fim da tarde** · Estado: **mídia v10 GRAVADA E VERIFICADA no Toshiba** (`TOSHIBA MQ04UBD200 23EQP2RHT`, 16:52→16:58, `IDENTICOS` na tentativa 2 — a 1ª teve o bit flip conhecido do caminho USB 2.0), gerada às 16:51 do commit **`2ad34f97`** com o diretório do kit quieto (guarda de higiene nova do `remasterizar-iso.sh`): `/storage/iso-migracao/ubuntu-26.04.1-wikijuridica-autoinstall.iso.v10`, 2.928.214.016 B, sha256 `3cc4c729799ec08531b9c8eef3e4e0003fbe32fca164330626c57a50eb75f304`. **O instrumento passa a ser `git diff --stat 2ad34f97..HEAD -- ops/provisionamento/`** (vazio = a mídia carrega o kit do HEAD). **A v9 (e a v7 gravada em 2026-09-22, e a v8) nunca teriam instalado:** o ensaio em VM (`ops/ensaio-migracao/`, novo) achou `keyboard: variant: abnt2` (não existe; o instalador parava aos 90 s com `Unknown keyboard variant "abnt2" for layout "br"`) e o `cp` sobre `/etc/default/locale`, que no 26.04 já é symlink (parava aos 7 min e o kit nunca chegava ao alvo). Com os dois consertos, a ISO instala e desliga sozinha em ~8 min (fiel 7m51s, observado 8m10s; 38/39 verificações verdes na fase 2). O que mais entrou no kit nesse commit (PASSO 3 automático no primeiro boot, `migrar-tudo.sh`, PASSO 10b da VM do escritório, 447 pacotes, pendências de terceiro, rede pelo NetworkManager) está em `docs/goal/ESTADO_MIDIA_E_KIT_20260923.md`; o ensaio da própria v10, com a unit do primeiro boot até o marcador e a variante sem rede, é o item 7 desse ESTADO — a mídia só se declara pronta com ele verde.

**2026-09-23** · Estado: kit re-editado pelo goal do IDE (commits C2 `1af65779`, C7 `6671c31f`, C2b `fe588fa1`); **mídia v9 gerada, falta gravar.** **O comando que decide se a mídia carrega o kit do HEAD agora é este:** `git diff --stat fe588fa1..HEAD -- ops/provisionamento/`. Vindo **vazio** (e veio, às 09:50), a v9 — `/storage/iso-migracao/ubuntu-26.04.1-wikijuridica-autoinstall.iso.v9`, sha256 `36864c519691f31aa741edebf81074515190ab1e4e26b5ed06d06eb5aa0c722d` — carrega o kit do HEAD; vindo com arquivos, a sequência é `remasterizar-iso.sh` → `gravar-midia.sh` → `verificar-midia.sh`. O Toshiba estava ausente às 09:40:52: `gravar-midia.sh` e `verificar-midia.sh` quando ele for plugado. O parágrafo seguinte, de 2026-09-22, descreve a mídia v7 — gravada e verificada naquele dia e superada em 2026-09-23 — e fica como registro.

**2026-09-22** · Estado: Fase 0 executada, kit de provisionamento auditado e corrigido, **mídia gravada e verificada**.
**A mídia está pronta — e o comando que decide se continua pronta é este:** `git diff --stat 73ff537d..HEAD -- ops/provisionamento/`. Vindo **vazio**, a mídia carrega o kit do `HEAD` e não precisa ser regravada; vindo com arquivos, ela é mais velha que eles e a sequência é `remasterizar-iso.sh` → `gravar-midia.sh` → `verificar-midia.sh`. Hoje vem vazio, e esta frase não envelhece sozinha porque não afirma o resultado: nomeia o instrumento. No Toshiba (`/dev/sdb`, TOSHIBA MQ04UBD200, serial 23EQP2RHT) está a `ubuntu-26.04.1-wikijuridica-autoinstall.iso.v7`, gerada do commit `73ff537d` e gravada por `gravar-midia.sh`, que conferiu byte a byte e aprovou **na tentativa 1: 11/11 blocos IDÊNTICOS**. O conteúdo foi conferido depois disso, por `sha256`, arquivo a arquivo contra o worktree — **na ISO, que é byte-idêntica ao disco pelos 11/11 blocos acima** — e o `user-data` dentro dela tem `shutdown: poweroff` na linha 146, que é o que impede a máquina de se reinstalar por cima.
Histórico de apuração, das quatro rodadas de refutação e da auditoria do executável contra a mídia real: [`MIGRACAO_SERVIDOR_20260922_APURACAO.md`](MIGRACAO_SERVIDOR_20260922_APURACAO.md).
**2026-09-23 — nota ao lado do instrumento, que fica como está:** o goal do IDE edita `ops/provisionamento/` (repositórios da Microsoft e do WezTerm saem do `provisionar.sh` e do `verificar-kit.sh`, pacotes da iGPU entram em `pacotes.txt`, PASSO 11 entra no `LEIA-ME.txt`, Chrome, Node e Claude Desktop passam a ser instalados, e o `restaurar-etc.sh` passa a recriar os links de `/etc` — ver *Lacunas abertas em 2026-09-23*). Desde o commit C2 (`1af65779`, 09:34:45), `git diff --stat 73ff537d..HEAD -- ops/provisionamento/` vem **com arquivos** e a v7 fica atrás do HEAD — é o instrumento acima funcionando, não uma exceção a ele. A **v8** foi gerada às 09:37 do commit C7 (`6671c31f`), sha256 `33511375a99948a17d57094173221705d36be16cfddebfae70385f8d9579faf9` (recalculado às 09:45), e ficou **superada no mesmo dia** pelo commit C2b, que tira `tlp` e `tlp-rdw` do `pacotes.txt`. A mídia final é a **v9**, gerada às 09:47 do commit C2b (`fe588fa1`, 09:46:45): 2.927.976.448 B, sha256 `36864c519691f31aa741edebf81074515190ab1e4e26b5ed06d06eb5aa0c722d` (recalculado às 09:50), com as 13 verificações internas do remasterizador verdes e, antes dela, `KIT VERIFICADO` com 161 verificações e o `conferir-pacotes-no-ubuntu.sh` com 428 de 428 — 262 main, 165 universe, 1 multiverse —, medidos pelo agente `kit-midia`. O Toshiba estava ausente às 09:40:52 (`lsblk` sem TOSHIBA): **falta gravar**. O instrumento passou a nomear o commit da v9, na primeira linha desta página.

> **Custo zero, por contrato.** Nada aqui compra nada nem abre conta em lugar nenhum. O canal é o hardware que já existe; todo o software é OSS. O único binário proprietário é o driver NVIDIA, que é firmware da placa: gratuito, sem cadastro, dos repositórios oficiais do Ubuntu.

---

## Por que esta migração existe

O portal roda num **Lenovo IdeaPad S145** (i7-8565U, 19 GiB, sem Ethernet, Debian 12). Quatro fatos medidos definem a urgência:

| fato | medida |
|---|---|
| **O SSD está morrendo** | Kingston SNV3S: `Percentage Used 49%`, 136 TB escritos em 3.832 h = **894 GB/dia**, TBW nominal 320 TB |
| **O remote não protege nada** | GitHub em `5e89b185`, de 2026-06-10 — o local está **3.825 commits à frente**. O que protege é `/mnt/hdd/backups/wiki/repo.git`, no mesmo chassi |
| **A GPU nova resolve o gargalo da IA** | RTX 5060 Ti aferida em **32,9 tok/s** num 14B Q4 contra **1,85 tok/s** hoje — 17,8× |
| **O NVMe cozinha no chassi** | 83–84 °C, com **1.684 minutos acumulados acima do limite crítico** |

---

## As cinco decisões

| decisão | o quê | por quê |
|---|---|---|
| **1. Distro** | Ubuntu Server 26.04.1 LTS | é a única com módulo aberto para a Blackwell **pré-assinado pela Canonical** — zero DKMS, zero MOK. O Debian não tem em suíte nenhuma, e o próprio wiki dele diz que não suporta RTX 50xx |
| **2. Escopo** | tudo migra, o notebook aposenta | ordem do dono; resolve de uma vez o SSD com 49% de TBW |
| **3. Canal** | dado por backup frio + delta; discos **transplantados depois** | o cutover precisa da velha **ligada**, senão a borda devolve 530. Os discos vão para a nova como destino final, não como veículo |
| **4. Instalação** | ISO remasterizada com `user-data`, gravada por `dd` | menos peças móveis que o Ventoy, é o caminho que a documentação do Ubuntu suporta, e o mesmo disco serve de mídia e depois de backup |
| **5. Descarte** | não copiar ≈ 415 GB de lixo | **nada é deletado**: vira `--exclude` do `rsync`, e os discos velhos ficam intactos |

### Por que ext4 único, sem LVM e sem btrfs

Medido nesta máquina: `systemd-sysctl.service` tem `DefaultDependencies=no`, então **não há ordenação nenhuma** entre ele e as montagens do fstab — a janela é de **1,49 s** (4,689 s contra 6,179 s). Com `/opt/wiki` num volume separado, o symlink `/etc/sysctl.d/zzz-wikijuridica.conf → /opt/wiki/ops/…` não resolve, **em silêncio**. Isso também elimina btrfs por subvolumes.

### Por que o nginx é o da distro

O portal roda num nginx **dedicado** (`nginx.service` do sistema fica `masked`), com `load_module` de três `.so` e `ExecStartPre=nginx -t`. Faltando um, o portal não sobe. Os três existem no Ubuntu:

| `.so` exigido | pacote | versão |
|---|---|---|
| `ngx_http_headers_more_filter_module.so` | `libnginx-mod-http-headers-more-filter` | `1:0.39-2build3` |
| `ngx_http_brotli_filter_module.so` | `libnginx-mod-http-brotli-filter` | `1.0.0~rc-7build3` |
| `ngx_http_brotli_static_module.so` | `libnginx-mod-http-brotli-static` | `1.0.0~rc-7build3` |

**Regra que sai daqui:** não adicionar o repo do nginx.org nem o PPA `ondrej/nginx`. Os módulos exigem `Provides: nginx-abi-*`, que o repo upstream não declara — é dessa mistura que vem o relato de "brotli não instala no 26.04".

### Duas armadilhas do driver NVIDIA

1. **`nvidia-driver-580-open` arrasta `nvidia-dkms-580-open`**, que tenta compilar no `postinst`; sem headers isso falha dentro do `/target` e o servidor nasce quebrado.
2. **Os sabores *desktop* e *server* são mutuamente exclusivos** — `nvidia-kernel-common-580` e `-580-server` declaram `Conflicts`. O par correto, ambos `server`: `linux-modules-nvidia-580-server-open-generic` + `nvidia-headless-no-dkms-580-server-open`.

Fica no ramo **580** (`restricted`, com suporte da Canonical), não no 610 (`multiverse`).

---

## O que já está feito

### Fase 0.1 — o laço de restart, consertado

O servidor estava em `Restart=always` desde `2026-09-21T21:10:27-03`, com **591 reinícios**, cada um lendo 611 MB do artefato de vizinhança.

```
grafo: data/ai/grafo_vizinhanca.jsonl: bufio.Scanner: token too long
```

**Causa, medida:** 196.615 linhas, 611.160.838 bytes. Exatamente uma passa do teto — a 18.776, com **30.348.998 bytes**: o nó `{"chave":"STJ","tipo":"tribunal"}`, que recebe uma aresta `julgado_por` de **entrada** por acórdão do corpus (168.605 delas). São só dois nós `tribunal` no grafo inteiro.

O teto já havia sido elevado de 64 KB para 16 MiB. O dado passou o remendo em seis dias.

**Correção 1 — produtor.** `_exclui_do_vizinho` corta o par (tribunal + `julgado_por` + entrada). Por PAR, nunca um teto de grau genérico: `Impacto` lê exatamente as arestas `cita` e `entrada`, e amostrar ali devolveria uma parte apresentada como o todo (`sumula:STJ:7` tem 28.563 dessas arestas).

**O total não se perde.** `escrever_vizinhanca` conta o que saiu e grava `atributos.julgado_por_entrada`, e o campo `metodo` do MCP nomeia a agregação — sem isso a ferramenta responderia `total: 0` para o STJ, que é fabricação de ausência.

**Correção 2 — parser.** `bufio.Scanner` → `bufio.Reader.ReadBytes('\n')`. O número da linha é contrato (`grafo_test.go` exige "linha 6"), então o laço conta à mão e replica duas arestas que o Scanner dava de graça: a linha em branco, que conta mas não vira nó, e a última linha sem `\n`, que chega junto com `io.EOF`.

**Resultado medido:**

| | antes | depois |
|---|---|---|
| linha do STJ | 30.348.998 bytes | **141 bytes** |
| maior linha do artefato | 28,94 MiB | **6,33 MiB** |
| artefato inteiro | 611.160.838 | 581.066.246 bytes |
| carga do artefato real | — | 5,83 s, heap 0,98 GiB |
| `NRestarts` | 591 e subindo | **congelado** |

**Testes, todos provados por mutação.** 3 casos em `internal/grafo/grafo_test.go` e 5 em `tools/test_grafo_juridico.py`; 7 mutantes lançados, 7 mortos, cada um pelo teste certo. A suíte do produtor segue verde: 41 testes.

**Validado ao vivo:** `/healthz` e `/readyz` = 200 (o `readyz` estava 503), `/api/v1/health` respondendo, busca devolvendo 14 resultados reais, MCP `grafo` e `impacto` funcionando.

### Fase 0.2 — os segredos

Tarball cifrado com **`age` contra a chave SSH do dono** — destranca com `age -d -i ~/.ssh/id_ed25519`, sem senha nova para guardar. 46 arquivos, em **dois discos físicos** (`/mnt/hdd` e `/storage`). Verificado decifrando: `.env.local` e a credencial do túnel conferem byte a byte.

**E a outra metade**, que faltava: `restaurar-segredos.sh` põe cada um de volta no caminho certo, com o modo certo, e confere. Sem ele o dono teria um tarball e uma lista, e 19 destinos para acertar à mão — entre eles quatro chaves privadas de WireGuard. Duas decisões ficam no código: `/etc/sudoers.d` **não** é restaurado em bloco (o da velha tem um `NOPASSWD: ALL`), e modo frouxo em chave privada é **corrigido**, não só reportado.

Cobre o que não existia em backup nenhum: os três `.env`, `ops/ingress.env`, as chaves do IndexNow, **as quatro credenciais de túnel e o `cert.pem`** (que `tunnel login` sobrescreve e não é regenerável sem re-rotear DNS), `~/.ssh`, `~/.gnupg`, rclone, gh, e o `/root/.gnupg/backup-passphrase`.

### Fase 0.3 — o que só existia fora do repositório

| artefato | onde ficou |
|---|---|
| Modelfile do `wj-extracao-sonda` (não existe em registry nenhum) | `ops/ollama/Modelfile.wj-extracao-sonda` |
| os 10 scripts `ai-*` que faltavam | `tools/env/` |
| firewall vivo dos três donos (93 chains) | `ops/firewall/*-20260922*` |
| 473 pacotes Python do user site | `ops/provisionamento/python-user-site.txt` |
| fstab, locale, udev, ICP-Brasil, audit, sysctl | `ops/provisionamento/etc-vivo-20260922/` |

### Fase 0.4 — a linha de base que morre com o notebook

`VACUUM INTO` de `data/ai/fila.sqlite` feito (369 MB, `quick_check: ok`) — `cp` a quente de banco com WAL entrega banco corrompido.

**O Gate 0 virou código.** `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` o descrevia desde sempre — *"duas passadas do mesmo modelo, temperatura 0, mesmo conjunto"* — mas não havia ferramenta: era instrução para um humano seguir à mão. Agora é `cmd/medir-piso-determinismo`, em Go, importando `cerebro.SistemaDaExtracao` e `cerebro.EsquemaDaExtracao` **diretamente** para não criar uma segunda fonte de verdade do prompt.

Ele mede **o quanto o modelo diverge de si mesmo**. Esse número é o piso abaixo do qual nenhuma diferença significa nada — sem ele o Gate 1 (CPU × GPU) e o Gate 2 (bake-off) são teatro, porque qualquer variação seria lida como "o novo é melhor" quando pode ser só o ruído próprio.

> **Dois números de tok/s convivem aqui, e confundi-los engana nos dois sentidos.** O **1,85 tok/s** da tabela de contexto é de um **14B Q4** no relatório de hardware de 09/09, e é o par correto dos 32,9 tok/s da GPU — 14B contra 14B, mesmo modelo, 17,8×. Já o que **roda hoje** no cérebro é `qwen3.5:4b`, medido em **4,66 / 5,07 / 4,95 tok/s**. Comparar os 32,9 contra 4,9 misturaria modelos de tamanhos diferentes e inventaria um ganho que a medição não sustenta. O Gate 1 compara **o mesmo modelo** nos dois hardwares, e é por isso que ele existe.

**Resultado medido, 2026-09-22:**

| | |
|---|---|
| jaccard médio | **1,0000** |
| jaccard mínimo | **1,0000** |
| passadas idênticas | **100%** (8 de 8) |
| **piso de determinismo** | **0,0000** |
| `eval_tok_s` mediano | 3,44 (sob contenção) |
| dispositivos/acórdão | 1,50 |

O modelo **não diverge de si mesmo** nesta máquina. Logo, no Gate 1, qualquer diferença entre CPU e GPU é sinal — e chamá-la de "a GPU entende melhor" passa a exigir outra explicação, não um palpite.

> **Alcance, porque um piso de zero convida a exagero:** são 8 acórdãos, com mediana de 1,5 dispositivo cada. Amostra pequena e extração curta favorecem o acordo. O número vale como *"não foi observada divergência nesta amostra"*, não como *"divergência é impossível"*. Se o Gate 1 achar diferença pequena, repita o Gate 0 com mais acórdãos (`--acordaos N`) antes de concluir qualquer coisa.

### O kit de provisionamento

> Índice do kit, com a ordem de execução e a máquina de cada passo: [`ops/provisionamento/README.md`](../../ops/provisionamento/README.md). O roteiro do dono é o [`LEIA-ME.txt`](../../ops/provisionamento/LEIA-ME.txt): **passos 1 a 10, com 3b, 4b e 4c no meio** — treze blocos, porque a ordem certa não cabe numa numeração corrida. *(2026-09-23: hoje são 16 blocos, PASSOS 1 a 11 — `grep -o '┌─ PASSO [0-9a-z]*' ops/provisionamento/LEIA-ME.txt`, às 08:46, lista 1, 2, 3, 3b, 4, 4b, 4c, 4d, 5, 6, 7, 8, 9, 9b, 10 e 11.)*

| artefato | o que faz |
|---|---|
| `user-data` | autoinstall cloud-init: alvo por `match: {ssd, largest}` — **nunca `/dev/sdX`** —, UID 1000, ABNT2, os 8 pares de `LC_*`, senha temporária com troca forçada, e **`shutdown: poweroff`** (`user-data:146`) — sem essa chave o instalador **reinicia**, reencontra o `/cdrom/nocloud/` e reinstala por cima de si mesmo, sozinho e sem perguntar |
| `remasterizar-iso.sh` | embute o `user-data` **e** edita o `grub.cfg` — as duas coisas, senão o instalador ainda pergunta `Continue with autoinstall?`. Leva **diretório junto**, e a guarda final é por **conjunto**: compara a lista inteira de arquivos do kit com a lista dentro da ISO e nomeia o que faltar (`remasterizar-iso.sh:155-179`) |
| `provisionar.sh` | **duas formas, e a segunda não é opcional.** Sem `--so-repo`, no PASSO 3: pacotes, repos, driver, nginx, `/etc`, usuário do Ollama, sudoers nomeado — e ausência de repositório ou home é **aviso**, porque eles só chegam no PASSO 4. Com **`--so-repo`, depois do PASSO 4**: só as fases que dependem do repositório e do home — toolchain Go, venv Python 3.11, verificação das units —, e ali a mesma ausência é **falha** (`provisionar.sh:6,12-32,72-76`). As duas formas são idempotentes, com log em `/var/log/wikijuridica-provisionamento.log`, e **reportam em vez de abortar** |
| `pacotes.txt` | **417 pacotes, todos conferidos contra o índice real do Ubuntu 26.04** — dos 457 originais, 40 não existiam e foram tratados um a um. *(2026-09-23, HEAD `fe588fa1`: 428 — `grep -vcE '^#\|^$' ops/provisionamento/pacotes.txt` às 09:49 —, com as seções DESKTOP NA iGPU (`pacotes.txt:448-474`) e COWORK DO CLAUDE DESKTOP (`:476`), e com `tlp` e `tlp-rdw` em NAO PORTAR (`:494-495`); no índice do `resolute`, 262 main, 165 universe e 1 multiverse, pelo `conferir-pacotes-no-ubuntu.sh` rodado pelo agente `kit-midia`. Às 08:46 o total também era 428, com outra composição: 263, 164 e 1.)* |
| `sudoers-wikijuridica-ops` | 13 binários **nomeados**, no lugar do `NOPASSWD: ALL` |
| `preparar-disco-backup.sh` | reformata o Toshiba em **ext4** depois que ele deixa de ser mídia, e o monta em `/mnt/backup-frio`. Quatro guardas, **todas antes da exigência de root**, para que a recusa se prove sem privilégio: recusa o disco do sistema, recusa partição, recusa disco que carregue ponto de montagem essencial (é o que protege o `/mnt/hdd`), e só aceita barramento USB. Para seguir, o operador **digita o serial do disco de volta** (`preparar-disco-backup.sh:53-101,125-135`). ext4 e nunca exfat: exfat não guarda dono, modo nem link, e os `0600` dos segredos voltariam errados sem dar erro |
| `migrar-dados.sh` · `cutover-tunel.sh` · `congelar-velha.sh` · `consolidar-discos.sh` | os quatro passos da migração, na ordem obrigatória. O `migrar-dados.sh` ganhou o passo que faltava no kit inteiro: **instalar as units** — `ln -sfnT` das 142 units e dos 16 diretórios de drop-in de `ops/systemd/` para `/etc/systemd/system`, `daemon-reload`, `systemd-analyze verify` e o gate lido por regra (`migrar-dados.sh:102-273,267-269`). O `-T` não é detalhe: sem ele, contra destino que já é diretório real, o `ln` sai 0 e aninha `X.service.d/X.service.d`, inerte, **com a saída verde** |
| `LEIA-ME.txt` | o roteiro manual, em português, sem jargão, dizendo em qual máquina cada passo roda |
| `conferir-pacotes-no-ubuntu.sh` | baixa o índice real do Ubuntu (~21 MB, com cache) e diz quais nomes não existem — foi ele que achou os 40 |
| `gravar-midia.sh` | grava, **verifica byte a byte e regrava** se reprovar. Medido nas duas gravações desta sessão: a primeira precisou de **2 tentativas** (o defeito era **um byte**, que nem `dd` nem `file -s` veem), a segunda passou na **tentativa 1**, com 11/11 blocos idênticos |
| `verificar-kit.sh` | **todas as verificações do kit num comando**, em doze seções: sintaxe e shellcheck de todo shell, `py_compile` de todo Python, as invariantes das listas e as do autoinstall, a existência das units citadas, `visudo`, se todo script declara **onde roda**, se o README menciona todo script, se todo artefato que o LEIA-ME manda rodar existe, os repositórios de terceiro (só com `--com-rede`) e — seção 12 — **dependência que chega depois de quem a usa**. O número cresce junto com o kit — cada script novo entra em quatro seções de uma vez —, então o que vale é o comando, não a contagem: medido em **2026-09-22 às 13h37, sobre o kit commitado e sem rede, 93 verificações, 93 verdes, exit 0**. *(2026-09-23, depois da edição do goal do IDE, medido pelo agente `kit-midia`: 149 verificações sem rede, mais 4 com `--com-rede` — eram 8; antes da v9, sobre o HEAD `fe588fa1`, `KIT VERIFICADO` com 161.)* |
| `testa-comum.sh` · `testa-user-data.py` · `conferir-units-citadas.py` | as três baterias que o verificador **executa** |
| `testa-instalar-units.sh` | a bancada do passo que instala as units, contra units de mentira num `/etc` de mentira — ela extrai as funções do `migrar-dados.sh` real, entre marcadores, em vez de testar uma cópia. **Roda à parte**: o `verificar-kit.sh` confere a sintaxe dela, não a executa (`verificar-kit.sh:21-28,41-47`) |
| `restaurar-segredos.sh` | decifra com a **chave SSH do dono** (sem senha para lembrar) e posiciona os 19 destinos com o modo certo. Tem `--seco` |
| `restaurar-etc.sh` | põe de volta o que não tem par no repositório — udev (inclusive a regra do token A3), auditoria, sysctl, limites do systemd, `ollama.service`. **Recusa três coisas, e cada recusa é decisão:** não sobrescreve o `/etc/fstab` (o da nova tem os UUIDs dela), não aplica o ruleset do nftables (são três donos de firewall, e um `ufw enable` regrava as chains por cima) e não traz o `/etc/sudoers.d` da velha (que tem um `NOPASSWD: ALL`). Também tem `--seco`. **E não sobrescreve nada sem guardar:** se o destino já existe, o anterior vai para `<destino>.substituido-AAAAMMDD-HHMMSS` com modo e dono preservados, e o script **para** se não conseguir copiar — a mesma guarda do `restaurar-segredos.sh`, posta aqui pelo incidente das 14:17 |
| `fazer-backup-frio.sh` | tar+zstd **selado** (os dois HDDs são SMR: árvore com arquivo pequeno colapsa para 200 kB/s), os seis bancos por `VACUUM INTO`, espelho git com `fsck`, e **verificação** — `zstd -t`, `quick_check` e `sha256sum -c` |
| `verificar-midia.sh` | compara a ISO com o disco gravado por blocos e bissecciona até o byte — a primeira gravação saiu com **1 byte** errado que nem `dd` nem `file -s` viram |
| `cmd/medir-piso-determinismo` | **o Gate 0**, que o doc de IA descrevia mas não tinha ferramenta. Duas passadas do mesmo modelo, temperatura 0, mesmo conjunto |

> **Os 40 nomes que não existiam no Ubuntu**, e por que isso importa: `pacotes.txt` nasceu de `apt-mark showmanual` no **Debian 12**. Conferido contra os 75.319 pacotes reais do `resolute`, 40 não existiam. Nove mudaram de nome (`python3.11-venv` → `python3-venv`, `dnsutils` → `bind9-dnsutils`, `p7zip-full` → `7zip`…), 21 eram **SONAME de biblioteca** — que saem da lista, porque o apt traz a versão certa como dependência e fixar o número é justamente o que quebra entre distros — e 10 não fazem falta. Depois da correção: **417 de 417 existem**. *(2026-09-23: com os pacotes da iGPU e do Cowork, 428 de 428 no HEAD `fe588fa1` — 262 main, 165 universe, 1 multiverse —, pelo mesmo `conferir-pacotes-no-ubuntu.sh`, rodado pelo `kit-midia`.)*

**A ISO se verifica em 13 pontos** ao sair do `remasterizar-iso.sh`, entre eles o `ds=nocloud\;s=/cdrom/nocloud/` com a **barra de escape** conferida caractere a caractere (`grep -qF`, não `grep 'ds=nocloud'`, que passa sem a barra), a ISO continuar bootável em UEFI e BIOS, o `user-data` dentro dela ser YAML válido, e o kit inteiro estar presente.

> ✅ **A mídia está gravada, verificada e é a desta data.** `/storage/iso-migracao/ubuntu-26.04.1-wikijuridica-autoinstall.iso.v7`, gerada do commit `73ff537d`, `sha256 ac4737056750ccca555409d9ef05381e6b874c4968c53a5b32d38ee2e8aa7630`. O `gravar-midia.sh` escreveu no `/dev/sdb` (TOSHIBA MQ04UBD200, serial **23EQP2RHT**) e conferiu byte a byte: **11/11 blocos IDÊNTICOS, na tentativa 1** — a gravação anterior desta mesma sessão precisou de duas, e o defeito era **um byte**, que nem `dd` nem `file -s` veem. Depois disso o conteúdo foi conferido de novo, por `sha256` arquivo a arquivo contra o worktree — **na ISO montada em loop, não no disco**, e o que autoriza a conclusão sobre o disco é a identidade byte a byte dos 11/11 blocos. O `verificar-midia.sh` derruba o page cache antes de comparar (`sync; echo 3 > /proc/sys/vm/drop_caches`, linha 43), então o que ele leu veio do disco, e a ISO passa nas **13 verificações internas** do remasterizador, entre elas o `ds=nocloud\;s=/cdrom/nocloud/` com a barra de escape conferida caractere a caractere.
>
> **Para inspecionar a mídia, monte `/dev/sdb` — nunca `/dev/sdb1`.** Medido nesta máquina: a partição do esquema isohybrid declara **5.706.480 setores** e os arquivos do kit ficam a partir do **5.707.112**, além do fim dela. Montando `sdb1`, o `ls` e o `stat` funcionam e a leitura falha com `Erro de entrada/saída` (`dmesg`: *attempt to access beyond end of device*) — e `grep -c` imprime **`0`** nesse caso, idêntico a "não encontrei". É um jeito fácil de dar uma mídia boa por ruim. O `udisks` faz automount de `sdb1` em `/media/` sozinho; desmonte antes, com `sudo umount /dev/sdb1` (o `udisksctl unmount` pendura à espera de polkit sem terminal).

---

## O que falta, na ordem

### 1 · Montar a máquina, só com o SSD novo — PASSO 1

BIOS: **`SATA Mode = AHCI`** (nunca RAID) e Secure Boot desligado.

> ⚠ Em modo RAID, "inicializar" um disco no RAIDXpert2 grava metadados e **apaga o conteúdo** — literal da AMD. Não abrir o RAIDXpert2 nem para olhar.

Onde plugar (a placa compartilha linhas, manual p.3-5): SSD novo em **M2_1**, NVMe velho em **M2_2** (evitando M2_3, que desabilita o PCIE2), HDD numa SATA do ASMedia, GPU no x16.

### 2 · Instalar e provisionar — PASSOS 2 e 3

> **2026-09-24 — superado o texto desta seção até o fim do PASSO 3.** A instalação passa a ser a
> interativa, pela ISO oficial, seguindo [`ops/instalacao-simples/GUIA.md`](../../ops/instalacao-simples/GUIA.md):
> `nouveau.modeset=0` no GRUB, instalar sem rede, Wi-Fi pelo adaptador USB, kit copiado da
> partição `writable` do Toshiba para `/opt/wiki/ops/provisionamento/` e `provisionar.sh` rodado
> à mão. Não há mais desligamento automático nem reinstalação por cima: o instalador interativo
> pede para tirar a mídia e aperta-se Enter. O texto abaixo fica como registro da rota do
> autoinstall.

Boot pelo Toshiba; a instalação corre sozinha, uns 10–15 minutos.

> ⚠ **Ao terminar, a máquina desliga sozinha.** É de propósito. Com ela desligada, e **antes de religar, tire o Toshiba**. Religada com ele plugado, ela reencontra a instalação e reinstala por cima do sistema que acabou de nascer — sozinha, sem perguntar nada. Se em vez de desligar ela reiniciar, a mídia é de uma gravação anterior às correções desta data.

Depois, já sem o Toshiba: `sudo /opt/wiki/ops/provisionamento/provisionar.sh`.

Nesta fase `/opt/wiki` tem **só o que a mídia copiou** — o repositório e o `/home` chegam no PASSO 4. Por isso o script avisa sobre o que ainda não existe e pode terminar verde: ali isso é esperado, e a segunda forma dele (`--so-repo`, abaixo) é que fecha a conta.

**O notebook serve o site este tempo todo.**

### 3 · O backup atravessa no Toshiba — PASSOS 3b, 4, 4b e 4c

O mesmo disco faz **dois papéis, em sequência**: mídia de instalação até o sistema subir, veículo do backup depois. Não é economia de disco — é o que fecha um buraco do roteiro antigo, que mandava a máquina nova ler `/mnt/hdd`. Aquilo é o HDD SATA interno do notebook, e só chega na máquina nova no transplante, no PASSO 9 — depois dos passos que o liam.

**No notebook (PASSO 3b).** `preparar-disco-backup.sh /dev/sdX` reformata o Toshiba em ext4 e o monta em `/mnt/backup-frio`; ele mostra modelo, serial e tamanho e **pede o serial de volta** antes de tocar em disco nenhum. Só chegue aqui com o PASSO 3 terminado: este comando apaga a mídia de instalação.

Passo 0 do backup: **parar `prazos.timer`, `calendario-forense.timer` e `escritorio-backup.timer`** — `prazos.db` tem rollback journal, e copiar `.db` e `-journal` de instantes diferentes é o cenário de corrupção que o SQLite documenta. O `-journal` **não** é apanhado pelas exclusões `*-wal`/`*-shm`. Depois, `fazer-backup-frio.sh --destino /mnt/backup-frio/frio-<data>`.

**O pacote de segredos viaja à parte.** Ele não está dentro do backup: é outro arquivo, em outro diretório (`/mnt/hdd/backups/wiki/segredos/segredos-20260922.tar.age`, com o `.sha256` ao lado), e sem ele o PASSO 4b não tem o que abrir. E **antes de desplugar, sempre `umount` e `sync`** — puxar o cabo deixa parte do backup só na memória, o arquivo chega quebrado do outro lado e nada avisa.

**Na máquina nova (PASSO 4).** Monte por **rótulo** (`mount -L backup-frio`), nunca por `/dev/sdX`: a letra muda de uma máquina para a outra e de uma partida para a outra. Então `migrar-dados.sh`, que restaura, **instala as units**, regenera o grafo antes de validar, **congela os escritores da velha**, **colhe os seis bancos por `VACUUM INTO` fresco lá**, puxa o delta com o `.path` parado, posiciona cada banco conferindo a contagem por tabela contra a origem, compila, sobe e valida. Ele **para e pergunta** antes do cutover.

> **O congelamento da velha entrou no script em 2026-09-22, e é o que separa migrar de perder dado.** A versão anterior posicionava os bancos do **backup frio** — feitos no PASSO 3, horas ou dias antes — e o delta não os supria **por desenho**: as exclusões barram todo `.db`/`.sqlite` e os `-wal`, `-shm` e `-journal` deles, porque copiar banco a quente entrega banco rasgado. Tudo o que a velha escrevesse em `fila.sqlite`, `social.db`, `datajudfila.db` e `prazos.db` entre o backup e o cutover não atravessava, e não atravessava **em silêncio**: os arquivos chegavam íntegros, `PRAGMA quick_check` dizia `ok`, e o conteúdo era o de ontem.
>
> O que o script faz agora, nesta ordem: para pela rede os escritores do notebook em três tempos — timers, os quatro `.path`, e o **resto num único `stop`**, porque cada serviço tem `Requires=` do seu socket e parar o serviço deixando o socket de pé faz a primeira requisição da borda **reativar** o serviço, que então escreve `social.db` depois do `VACUUM`. Os quatro de usuário (`prazos`, `calendario-forense`, `escritorio-backup`, `escritorio-drive`) entram porque nenhum `systemctl` de sistema os alcança, e `prazos.db` é um dos seis. **`wikijuridica-nginx.service` e os cinco `cloudflared` não são tocados**: até o cutover terminar eles são a única origem no ar.
>
> A conferência não confia no exit do `stop` — ela pergunta a cada unit, uma a uma, por um laço remoto que imprime o **nome** junto do estado, porque parear saída com lista por posição nomeia a unit errada a partir da primeira falta. E `sudo -n` se confere **antes** de parar qualquer coisa: descobrir no meio que o sudo pede senha deixaria a velha pela metade, parte parada e parte escrevendo.
>
> Depois de posicionar, a contagem por tabela é comparada com a que veio da velha. `quick_check` prova que o arquivo é um SQLite íntegro; **não** prova que chegou inteiro — um arquivo truncado no rsync abre e responde `ok` com metade das linhas. Com os escritores parados, divergência ali é transporte rasgado, e reprova. Cair no backup frio continua legítimo (`--sem-delta`, ssh quebrado, velha já desligada), mas nunca em silêncio: cada banco que vier dele sai com aviso nomeando a fonte e a data.
>
> Bancada: `testa-congelar-e-colher.sh`, 24 asserções em 7 seções, duas por mutação.

> **Nada alcança a máquina velha antes do PASSO 4, e isso é por construção.** O `ssh` e o `rsync` do delta usam a chave do dono, nomeada (`comum.sh:97-102`, `migrar-dados.sh:414`) — e ela chega dentro do tar do home, no próprio PASSO 4. Rodando como `root`, o `ssh` procuraria em `/root/.ssh`, onde só existe `known_hosts`.

**PASSO 4b — `restaurar-segredos.sh`.** O tarball é destrancado pela chave SSH do dono, que chega no passo anterior: rodá-lo antes é um impasse — a chave mora dentro do arquivo que ela abre. Com `sudo`, sempre: o arquivo é `root:root` modo 0600, e como usuário comum a leitura volta vazia, **sem mensagem de erro nenhuma**.

**PASSO 4c — `restaurar-etc.sh`.** Ele lê `ops/firewall/`, que está **fora** de `ops/provisionamento/` e portanto não viaja na mídia de instalação. Rodado antes do PASSO 4, deixava a máquina exposta **sem emitir erro**: o jail de SSH do fail2ban não era aplicado e o script terminava verde.

**E então `sudo provisionar.sh --so-repo`.** É o passo que fecha o venv Python 3.11 e instala nele os **473 pacotes** do freeze. O `uv` e o `~/.local/share/uv`, onde mora o CPython que o `pyvenv.cfg` referencia, só chegam dentro do tar do home — então no PASSO 3 aquela fase cai no ramo negativo, emite aviso e o script termina **verde**, com as **819 tools Python** sem interpretador. Com `--so-repo` a mesma ausência vira falha, e há pós-condição: venv inexistente depois da tentativa reprova, em vez de o `&& ok` engolir o erro (`provisionar.sh:310-321`).

> ⚠ **Este comando ainda não está no `LEIA-ME.txt`.** Conferido em 2026-09-22: `grep -n so-repo LEIA-ME.txt migrar-dados.sh` não devolve acerto nenhum, e nem o roteiro nem a mensagem final do `migrar-dados.sh` mandam rodá-lo. Até que entrem, **vale esta página**.
>
> *(2026-09-23: **superado** — o comando já está no roteiro e na saída do script. `grep -n so-repo ops/provisionamento/LEIA-ME.txt ops/provisionamento/migrar-dados.sh` → `LEIA-ME.txt:381` (às 09:42; era a linha 364 antes das edições de 2026-09-23 no `LEIA-ME`), dentro do PASSO 4d ("Completar o Python e o Go (NÃO é opcional)"); `migrar-dados.sh:329`, a falha que manda rodar o PASSO 4d; e `migrar-dados.sh:968`, a mensagem final. A frase acima fica como registro do que se conferiu em 2026-09-22.)*

**Só então o PASSO 5, conferir com os próprios olhos**, sem pressa: o site continua saindo do notebook e nada mudou para quem acessa. A régua está em *Verificação de ponta a ponta*, mais abaixo.

### 4 · Cutover — make-before-break, janela zero — PASSO 6

`cutover-tunel.sh`: para o vigia na velha → sobe os cinco na nova → espera `readyConnections=4` em cada → **só então** para os cinco da velha.

> A sobreposição é **segura e desejada** aqui: o conteúdo já está congelado, sincronizado e validado, e a borda tenta outras réplicas se uma falhar. Parar primeiro deixaria 5–30 s sem conector nenhum, porque `grace-period: 30s` faz o processo drenar — medido no journal: `Stopping` 03:24:56 → `Stopped` 03:25:22.

### 5 · Observar, e só então congelar — PASSOS 7 e 8

`congelar-velha.sh --sim`, **depois** do cutover. Ele recusa rodar antes.

> O `--sim` é obrigatório e não é firula: **sem a flag o script explica o que faria, não toca em nada e sai 0** (`congelar-velha.sh:66`). Quem lesse "concluído" deixaria a máquina velha armada para voltar sozinha em qualquer reboot.

> `stop` não basta: 57 dos 61 timers têm `Persistent=true`, e `kernel.panic = 10` reinicia a máquina sozinha. Qualquer reboot subiria 5 conectores com a credencial viva. E a cadeia do cérebro chega à borda mesmo sem túnel — `purge-edge-cache` faria a máquina velha **purgar a borda que a nova está servindo**.

### 6 · Transplantar e consolidar — PASSOS 9 e 10

Desmontagem: palheta **plástica**, **bateria desconectada antes de tocar nos discos**, e **abrir a trava do cabo FFC antes de puxar o HDD**.

> ⚠ Antes de ligar com os discos velhos dentro: **fixar a ordem de boot no UEFI**. A ESP do NVMe velho tem `shim` + `fbx64.efi`, e o `fbx64` recria a entrada "debian" sozinha no primeiro boot.

`consolidar-discos.sh` trava em nível de bloco (`blockdev --setro`), monta `ro,noload` **fora do fstab**, traz o que faltava e escreve o fstab com `passno 0`.

> `mount -o ro` **não** basta: o kernel replaya o journal e escreve se o FS estiver sujo. E `noload` não impede a remoção de inodes órfãos — por isso a trava de bloco vem primeiro.

**São três partições, não duas** — o SSD do notebook tem o sistema **e** o `/storage`, e é no `/storage` que moram os 29 GB de modelos do Ollama e os 22 GB da VM do Claude Desktop. Esquecer o `--storage` deixa esses 51 GB para trás sem dar erro nenhum.

**E é aqui que o `/usr/local/bin` atravessa**, porque pacote nenhum o instala: são 44 itens, entre eles o binário do `ollama` e o `rclone`, que é o `ExecStart` do `escritorio-drive.service` (o `apt` traz o `rclone-browser`, a interface gráfica, não o binário). Cada item é decidido por medição, não por gosto: symlink atravessa se o alvo existir na máquina nova, script atravessa sempre, e ELF atravessa se o `LC_ALL=C ldd` **da máquina nova** não imprimir `not found`. Uma exceção nominal: o `tmux`, que sai por **sombreamento** e não por ABI — a distro instala o dela em `/usr/bin`, e `/usr/local/bin` vem antes no PATH para sempre (`consolidar-discos.sh:190-256`).

> **O binário do Ollama sozinho não resolve, e ele não é Go estático.** Medido em 2026-09-22 com `file` e `readelf -d`: o `ollama` 0.33.3 é **PIE dinâmico** — precisa de `libstdc++.so.6`, `libgcc_s.so.1`, `libresolv`, `libdl`, `libpthread`, `libm` e `libc` — e **sem RPATH/RUNPATH**. Quem gera token é `/usr/local/lib/ollama/llama-server`, **2,1 GB de runtimes** (`cuda_v12` 1,2 GB, `cuda_v13` 811 MB, vulkan 52 MB), que também não tinham produtor. Sem eles, `ollama serve` sobe, responde `/api/tags` e **falha em toda geração** — o modo de falhar mais caro de diagnosticar, porque parece vivo (`consolidar-discos.sh:212-218,300-316`).

---

## Rollback — três regimes

| quando | como | tempo |
|---|---|---|
| antes do cutover | não fazer nada: o site está no notebook | — |
| depois do cutover, antes de congelar | religar os cinco conectores na velha | **~10 s** |
| depois de congelar | `unmask` pela mesma lista + devolver as credenciais de `/root/` | minutos |
| depois do transplante | remontar os discos no notebook | ~15 min por sentido |

**Os discos velhos nunca são formatados, em passo nenhum.** Enquanto existirem, o dado está em três lugares: eles, a máquina nova e o backup frio.

---

## Verificação de ponta a ponta

| o que | como |
|---|---|
| nada se perdeu | `sha256sum` do manifesto conferido no destino; `git fsck --full` mais `for-each-ref` e `count-objects -v` idênticos entre origem `ro` e destino |
| acervo coerente | zero linhas `"tolerado(s) no boot"` no journal **e** `cmd/check published-manifest` exit 0 — o boot sozinho tolera até 10 defeitos por código e 25 no total |
| bancos íntegros | `PRAGMA quick_check` e `count(*)` nos **sete**, conferidos contra a origem |
| o sal da LGPD sobreviveu | `var/social/social.db.sal` presente — `pseudonimo.go` o **regenera em silêncio** se sumir, quebrando a correlação sem emitir erro |
| units corretas | `check-units-instaladas` exit 0 · `check-units-alarme` — e por **symlink**, nunca cópia: o gate aceita symlink para o caminho do repositório, rebaixa cópia idêntica a aviso ("funciona hoje, deriva amanhã") e reprova cópia divergente. A máquina velha tem 145 symlinks e 7 cópias; a nova nasce sem essa classe |
| a dívida do adiamento não se confunde com defeito | no `migrar-dados.sh` o veredito é lido **por regra**, não pelo exit: só `instalada`, `dependencia`, `notify_binario` e `socket_binario` reprovam — os quatro casos em que o systemd não honra a unit. As regras `adiamento_*` saem como **aviso, com o detalhe transcrito e nunca engolido**, e é justamente por isso que um adiamento vencido não derruba a migração: **um vence em 2026-09-23** (`wikijuridica-cerebro-saude.timer`), e sem essa partição a migração passaria a reprovar a partir de 24/09 por dívida de `ops/systemd/timers-adiados.jsonl` — que não se cura ali e nada tem a ver com instalação (`migrar-dados.sh:230-273`) |
| a IA local gera token, não só responde | `LC_ALL=C ldd /usr/local/lib/ollama/llama-server` sem nenhum `not found` **e uma geração de verdade** — `/api/tags` respondendo não prova nada, é exatamente o sintoma de quem subiu sem os runtimes |
| o Drive do escritório monta | `/usr/local/bin/rclone` presente e executável — é o `ExecStart` do `escritorio-drive.service` |
| socket correto | `ss -ltnp 'sport = :8089'` → uma linha LISTEN |
| portal na origem | `:8088` e `:8089` = 200; **busca real**, não só health |
| portal na borda | skill `verificar-producao-viva` — sondar `127.0.0.1` passa verde com o túnel caído |
| os segredos chegaram | `sha256sum` de `.env.local` e `.env.social` contra a velha — o `-` do `EnvironmentFile=-` significa **opcional**: sem o arquivo o serviço sobe e responde 200 |
| o túnel vai subir | `cloudflared tunnel ingress validate` e TCP 7844 IPv4 — `protocol: http2` **não tem fallback** |
| as 819 tools Python rodam | `wikijuridica-previsao.service` sobe verde; `import spacy, stanza, numpy, lxml` dentro do venv 3.11 |
| nada escrito nos discos velhos | `blockdev --getro` = 1 nos dois; `mount` mostrando `ro`; `Lifetime Writes` do SMART inalterado |
| os symlinks resolvem | `find ~ /opt -maxdepth 3 -xtype l` vazio |

---

## Depois do cutover

Um risco por vez — **a GPU não entra junto com a migração.**

1. **Driver NVIDIA**, ambos do sabor `server`. Em `ops/ollama/…/wikijuridica-tuning.conf`: `OLLAMA_LLM_LIBRARY=cuda_v12`, nunca `v13` — o parse do `.nv_fatbin` mostra que `cuda_v12` traz SASS nativo de `sm_120` (143 cubins) e `v13` é PTX puro, com JIT a cada load.
2. **Manter o Ollama em 0.33.3.** A versão e o `sha256` de cada blob são **proveniência** registrada; trocar junto com o hardware destrói a única âncora que torna a comparação CPU×GPU interpretável.
3. **Rever a guarda de 9 GiB** em `internal/cerebro/saude.go:201` — é código, não sai com symlink.
4. **Drenar a fila** (8.892 tarefas ≈ 49 h em CPU, ~3 h na GPU). *Superado em 2026-09-23:* o enfileiramento de 18–19/09 levou a fila a **105.524** `extrair_dispositivos` pendentes (`sqlite3 -readonly data/ai/fila.sqlite "select count(*) from tarefa where tipo='extrair_dispositivos' and estado='pendente'"`), e a essa altura a máquina velha drenava ~2.100/dia — 50 dias de CPU a 4,9 tok/s de eval. Por isso o cérebro está em **pausa declarada** (`data/ops/cerebro_pausa_manual.json`, até 2026-10-07) desde 2026-09-23 06:30 -03: ver `docs/ops/CARGA_TRANSITORIA_ANTES_DO_TRANSPLANTE_20260923.md`. **Esse arquivo mora em `data/ops/` e atravessa no `rsync`: a máquina nova nasce com o cérebro pausado, de propósito.** Retirar a pausa é o passo que abre a drenagem — `tools/cerebro-pausar retirar` — e vem DEPOIS dos itens 1 a 3 desta lista, porque é neles que a GPU e a guarda de residentes são acertadas. Pausa vencida sem retirada deixa `check-cerebro-batimento` vermelho e acorda o dono: é lembrete, não defeito.
5. **`git gc` na máquina nova.** Medido em 2026-09-22: **58.536 objetos soltos ocupando 5,40 GiB**, contra 19.078 empacotados em 3,04 GiB — os soltos são 3× mais objetos em quase o dobro do espaço. Mais 1.144 entradas de `garbage` (58,6 MiB), que são os `tmp_obj_*` já identificados como **hardlinks dos objetos reais**, não corrupção. É também por isso que o `git fsck --full` do backup leva mais de 30 minutos: ele confere o checksum de cada um dos 77 mil objetos.
6. **Monitorar `Percentage Used` do NVMe novo desde o dia 1** — os 894 GB/dia vêm da carga, não do disco velho.
7. **Queda de energia: a resposta é software.** `synchronous=FULL` nos bancos críticos, `commit=` curto no ext4. Se um dia houver nobreak, o caminho OSS é NUT — mas **nada aqui exige comprar coisa alguma**.
8. **Editor e terminal de engenharia — PASSO 11 do `LEIA-ME.txt`, depois do PASSO 10.** *(Acrescentado em 2026-09-23, goal do IDE.)* `sudo /opt/wiki/ops/ide/instalar-ide.sh` instala o VSCodium (repositório `download.vscodium.com/debs`, chave versionada em `ops/ide/` e pinada pelo fingerprint `1302DE60231889FE1EBACADC54678CF75A278D9C`, `codium` em `apt-mark hold`, extensão Claude Code na mesma versão do CLI) e `/opt/wiki/ops/terminal/instalar-terminal.sh` liga o kitty do archive às configs versionadas em `ops/terminal/`. A última linha de `/opt/wiki/ops/ide/instalar-ide.sh --verificar` — **sem `sudo`, como `rafael`** — tem de ser `IDE VERIFICADO`. **A RTX 5060 Ti fica exclusiva para CUDA:** o driver é o `-server-open` headless, sem GL nem driver X para ela (ver *Duas armadilhas do driver NVIDIA*, acima); o desktop Xfce desenha na **iGPU do Ryzen**, com o **monitor na HDMI ou no USB-C (DisplayPort Alt) da placa-mãe** e a iGPU ligada como vídeo primário na BIOS (PASSO 1). Os gates da pilha gráfica rodam **sem tocar `:0`**: `ops/ide/verificar-pilha-grafica.sh` só lê `boot_vga`, `vulkaninfo --summary`, `/var/log/Xorg.0.log` e `nvidia-smi --query-gpu=display_active`, e toda bancada com janela roda em `:99`, pela unit `wikijuridica-xvfb99.service`. Por que não depois do 4c: entre os PASSOS 4 e 6 "a busca e a API do NOTEBOOK ficam fora do ar" (`LEIA-ME.txt:284`), e a regra desta lista é um risco por vez. O bloco do PASSO 11 está em `LEIA-ME.txt:622-644` (conferido às 09:42). Doc: [`IDE_VSCODIUM_20260923.md`](IDE_VSCODIUM_20260923.md) §3 e §5.

---

## Lacunas abertas em 2026-09-23

Achadas pelo goal do IDE (`docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8 frente 9), cada uma com o comando que a mede. Nenhuma é do editor: estão aqui porque mudam o que a máquina nova **é**.

**M14 — cinco links de `/etc` para `ops/` que nenhum script do kit recria.** Medido às 08:18:35 -03: `find /etc -lname '/opt/wiki/ops/*'`, tirados os links de unit e de `*.wants/` (que o `migrar-dados.sh` já instala e habilita, `:102-273` e `:759-870`), devolve cinco caminhos materiais:

| link em `/etc` | aponta para | o que a máquina nova perde sem ele |
|---|---|---|
| `sysctl.d/zzz-wikijuridica.conf` | `ops/sysctl.d/zzz-wikijuridica.conf` | BBR (`:304`), keepalive de 120 s em vez dos 7.200 s do kernel (`:332-334`), `kernel.panic = 10` (`:369`) e `panic_on_oops` (`:375`) |
| `modules-load.d/bbr.conf` | `ops/modules-load.d/zzz-wikijuridica-bbr.conf` | o `tcp_bbr` carregado no boot, antes do `sysctl` que o escolhe |
| `tmpfiles.d/wikijuridica-lock.conf` | `ops/tmpfiles.d/wikijuridica-lock.conf` | o arquivo do flock pesado, `/tmp/opt-wiki-agent-heavy.lock` (dono `rafael`), recriado a cada boot — o `/tmp` é esvaziado no boot |
| `default/earlyoom` | `ops/earlyoom/default` | o `llama-server` como primeiro alvo — o earlyoom subiria com a config da distro |
| `systemd/system/ollama.service.d/wikijuridica-tuning.conf` | `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` | `MemoryMax=12G` e `OLLAMA_MAX_LOADED_MODELS=2` |

Tudo isso falharia **sem erro nenhum**. O mesmo `find` acha `/etc/tlp.d/10-wikijuridica-cpu.conf` (TLP, que *O que NÃO portar* manda deixar) e `/etc/nginx/sites-enabled/wikijuridica` (não material: o nginx é o standalone). Rota: passo novo do kit que recria cada link com `ln -sfnT` a partir do inventário inteiro do `find` — não de uma lista fixa — e aplica (`sysctl --system`, `systemd-tmpfiles --create`, `modprobe`, `systemctl daemon-reload`), com bancada em `unshare` e mutante "link ausente". **FECHADA em 2026-09-23, commit C7 (`6671c31f`)**, conferida no disco às 09:42: o `restaurar-etc.sh` ganhou o passo 1c/5 (`restaurar-etc.sh:476-477`), que chama `ligar_symlinks_etc` (`:239`; bloco entre os marcadores de `:175` e `:406`) sobre o inventário `ops/provisionamento/symlinks-etc.txt` — os cinco links em `:34-38` e as duas exceções `# nao-recriar` em `:40-41`, o `tlp.d` e o `sites-enabled` —, com `ln -sfnT` e, ao aplicar, `modprobe` de cada módulo **antes** do `sysctl --system` (`:219-225`, `:372`). O inventário nasce do `find` (230 links, menos os 223 com alvo em `ops/systemd/`, menos as duas exceções), e a bancada o reconcilia com o host vivo. Bancada `ops/provisionamento/testa-symlinks-etc.sh`, rodada por esta frente às 09:42:44: rc 0 em 0,88 s, "BANCADA VERDE — 3 mutantes mortos, 8 casos no veredito esperado, /etc real intocado" (mutantes: linha ausente do inventário, `ln` sem `-T`, sem preservação). Viaja na ISO v9.

**`.venv` × `.venv-tools311` — fato medido, não defeito do kit.** Medido às 08:15 -03: `.venv/pyvenv.cfg` → `version_info = 3.12.13` e `include-system-site-packages = false`; `ls -d .venv/lib/python*/site-packages/*.dist-info` → só `numpy-2.5.3.dist-info`. O comentário de `provisionar.sh:305-308` registra que as bibliotecas das tools (spacy, stanza, lxml) vivem no user site do 3.11; medido: `/usr/bin/python3` é `Python 3.11.2` e `~/.local/lib/python3.11/site-packages` tem **477** `*.dist-info` — grandeza diferente dos 473 pacotes do freeze citados acima (uma conta distribuições instaladas, a outra linhas do arquivo). O `provisionar.sh:305-313` cria **de propósito** `/opt/wiki/.venv-tools311` (3.11, dedicado), e o comentário de `:305-308` diz por quê. O que estava errado era a premissa do plano do IDE — "`.venv` com os pacotes das tools". Consequência já aplicada lá: o `pyrightconfig.json` do editor não aponta para `.venv`; fica sem `venv`, com `pythonVersion 3.11` e `extraPaths` para o user site 3.11 e para `.venv-tools311/lib/python3.11/site-packages` (decisão do orquestrador, 2026-09-23; conferido no disco às 09:55, commit C3 `10bd4d40`). O interpretador da máquina nova continua decidido aqui, no `--so-repo`.

**`tlp` na lista de pacotes.** `grep -n '^tlp' ops/provisionamento/pacotes.txt` → `370:tlp` e `371:tlp-rdw` (às 08:46), enquanto *O que NÃO portar*, logo abaixo, diz "TLP é de laptop": a torre nasceria com o gerenciador de energia de notebook instalado e ativo. *(Até o C2b: aberta, com a correção coerente com esta página — tirar as duas linhas.)* **FECHADA em 2026-09-23 no commit C2b, `fe588fa1` (09:46:45):** `tlp` e `tlp-rdw` saem da lista da distro e vão para NAO PORTAR com comentário datado (`pacotes.txt:494-495`) — 430 → 428 pacotes; o `tmux` sobe de `pacotes.txt:372` para `:370`, e o `consolidar-discos.sh:220,235`, que cita essa linha, acompanhou.

**Grupos do notebook que ficam fora da máquina nova** — medidos pelo agente `kit-midia` em 2026-09-23; o `provisionar.sh` põe o dono em `kvm` (`:107-109`), `libvirt` (`:240-245`) e `docker` (`:246-250`), e estes cinco não entram:

- `ollama` — `/storage/ollama` é 755 e legível, o cliente fala HTTP, e o grupo nasce do `useradd --system ollama` do passo 7; nenhum uso depende dele.
- `audio` — `/dev/snd/*` é `root:audio`, mas a sessão gráfica recebe ACL do logind; o grupo só vale fora da sessão.
- `video` — `/dev/video0-1`, `/dev/media0` e `/dev/fb0`, com a mesma lógica; a máquina nova talvez nem tenha câmera.
- `netdev` — `/dev/rfkill` e `wpa_supplicant`, que são Wi-Fi; a máquina nova é cabeada (RTL8125BG).
- `tss` — `/dev/tpmrm0` é `root:tss` e nasce do `tpm-udev`; zero uso de `tpm2` em `tools/` e `ops/`. A VM `escritorio-win11` usa `swtpm` pelo libvirt, e `swtpm-tools` não está em `pacotes.txt`: conferir se o TPM virtual reclamar na máquina nova.

**Chrome e Node — FECHADA em 2026-09-23.** Achado do agente `kit-midia`, conferido no disco: `provisionar.sh:153-156` configura os repositórios `google-chrome` e `nodesource`, mas o passo de pacotes instala só as linhas não comentadas de `pacotes.txt` (`provisionar.sh:175`, `grep -vE '^#|^$'`), e ali `google-chrome-stable` e `nodejs` são comentário (`pacotes.txt:472-473` quando o achado foi medido; no HEAD `fe588fa1`, `:520-521`, com a nota datada de `:522-529`). Nenhum passo os instalava: a máquina nova nasceria sem Chrome — o `playwright-core` 1.49.1 de `tools/publicador-social/` e `tools/coletor-bing-ia/` lança `channel: 'chrome'` e não traz navegador — e sem Node (o MCP `context-mode` é `npm i -g`), com o `provisionar.sh` terminando verde. Correção no commit C2 (`1af65779`), lida no disco às 09:42: logo depois do `apt-get update` de `provisionar.sh:206`, comentário datado em `:207` e um `apt-get install` por pacote — `google-chrome-stable` em `:208`, `nodejs/nodistro` em `:209` (o do NodeSource, que traz o `npm`) e `claude-desktop` em `:210` —, cada um virando `aviso` se o repositório de terceiro cair. *(Às 08:46 eram `:164-167`, antes de o pin e o bloco do Claude Desktop entrarem acima.)* **Pin do `nodejs`:** função `gravar_pin_nodejs` (`provisionar.sh:165`), chamada com `/etc/apt/preferences.d/nodejs` (`:173`) — não `nodesource`, como este parágrafo dizia às 08:46 — e corpo `Package: nodejs` / `Pin: origin deb.nodesource.com` / `Pin-Priority: 600` (`:166-168`), o mesmo arquivo e as mesmas três linhas que o `setup_22.x` oficial do NodeSource grava (linhas 98-100 dele, citadas em `:161-164`); 600 vence o 500 do archive, cujo `nodejs` não traz o `npm`, e só reescreve se diferir. A seção 15 do `verificar-kit.sh` (`:411`) extrai e executa a função real (`:418-422`). Viaja na ISO v9.

**Claude Desktop — a VM viajava, o aplicativo não.** Os 22 GB da VM do Claude Desktop atravessam no `/storage` (PASSO 10), mas nenhum passo instalava o `claude-desktop` na máquina nova: em `pacotes.txt` ele é comentário da seção de repositórios de terceiro, como o Chrome e o Node eram. **FECHADA em 2026-09-23, commit C2 (`1af65779`)**, conferida no disco às 09:46: o `provisionar.sh` **restaura** o que o notebook já tem, o `claude-desktop` 2.2553.13 do repositório `downloads.claude.ai/claude-desktop/apt/stable` (`:174-198`). A chave vem de `https://downloads.claude.ai/claude-desktop/key.asc` (`:188`) para o `.asc` que o postinst do pacote reescreve a cada versão — por isso não passa pelo `instalar_repo`, que gravaria um `.gpg` noutro caminho —, e o fingerprint `31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE` (`:180`) é conferido, com uma chave só, **antes** de gravar o keyring e o `.list` (`:186-192`); fora do pino, `aviso`, e o app não entra (`:195`). O install é `provisionar.sh:210`. O Cowork precisa dos grupos `kvm` (`:107-109`), `libvirt` (`:240-245`) e `docker` (`:246-250`), e `ovmf` e `virtiofsd` entram explícitos no `pacotes.txt` (`:482-483`, seção COWORK DO CLAUDE DESKTOP, `:476`). Viaja na ISO v9.

## Lacunas abertas em 2026-09-24

Medidas durante o PASSO 4, com a torre já provisionada. Nenhuma trava a migração. Estão aqui para que a próxima reinstalação não as redescubra.

**A zona DNS do vizinho e as ACLs do BIND não atravessam — e não fazem falta.** O notebook guarda em `/etc/bind/named.conf.local` a zona `divorcioem1dia.com` (arquivo `/etc/bind/zones/db.divorcioem1dia.com`, de 29/04) e, em `named.conf.options`, a `acl "trusted"`, o `rate-limit` e o `deny-answer-addresses ... except-from { "divorcioem1dia.com"; }`. Nenhum script do kit leva isso para a torre: a fase 15 do `provisionar.sh` só grava o `listen-on { !192.168.122.0/24; any; };`. Medido às 12:00 -03: `systemctl is-active named bind9` → `inactive` / `inactive`; `ss -lnup 'sport = :53'` mostra só o dnsmasq do libvirt (`192.168.122.1`) e o do LXC (`10.0.3.1`); o NS da zona é `dns3.hostgator.com.br.`, e há um `.bak.20260429-pre-cf-flip` ao lado. O BIND do notebook não responde por nada hoje: é configuração parada de outro projeto, que esta página não porta (ver *Separação*, no `CLAUDE.md`).

**Três mudanças feitas na torre fora do kit, às 11:15-11:16 -03, por outra sessão do Claude, já encerrada.** Lidas no `journalctl -b -1` (linhas `sudo ... COMMAND=`) e conferidas no estado vivo às 12:00:

- `systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target` → os três primeiros medidos `masked`. Coerente com um servidor 24/7. As "4 camadas de bloqueio de suspensão" de *O que NÃO portar* são do notebook, com tampa e bateria; esta máscara é outra coisa. Falta ela nascer do kit, e não da mão.
- Drop-in `/etc/systemd/system/nvidia-persistenced.service.d/override.conf` com `--persistence-mode --verbose`: mantém a RTX inicializada entre jobs CUDA. Mesma situação: fora do kit.
- `glances-web.service`, com o Glances em `/opt/glances`, passou de `--bind 127.0.0.1` para `--bind 0.0.0.0 --port 61208`, sem senha, com o `ufw` inativo. O painel fica aberto a qualquer aparelho da rede de casa. A descrição da unit ("rede local") mostra que isso foi intencional. Fica como está, registrado aqui, até o dono dizer o contrário.

A investigação de "a tela não volta depois de ociosidade" (agente `especialista-critico`, 2026-09-24) mexe no mesmo assunto, energia e vídeo. O conserto dela entra no kit junto com as duas primeiras mudanças, depois do PASSO 6.

**O boot da torre de 09:46:40 terminou sem desligamento.** A última linha do journal (`journalctl -b -1`) é das 11:50:08, três segundos depois de o Toshiba ser plugado (`sd 8:0:0:0: [sda] Attached SCSI disk`), e o boot seguinte começa às 11:51:12. Não há sequência de shutdown. Duas hipóteses seguem abertas: reset físico com a tela apagada, ou travamento. A investigação da tela as separa.

**CPU da torre, medida:** `LC_ALL=C lscpu` → `AMD Ryzen 7 9800X3D 8-Core Processor`.

**Auditoria notebook × torre antes do transplante (2026-09-24, 13:00–13:50).** Por ordem do dono ("revisar e ver se nada ficou para trás"), seis colhedores (fatias A a F: `/opt/wiki`, units e agendamentos, binários e pacotes, `/etc` e rede, home, dados e discos) mediram o notebook. O lado da torre foi coberto pelo inventário `.agents/runtime/contexto/torre-inventario-20260924/inventario-torre.txt`, e os achados circularam em `.agents/runtime/contexto/migracao-auditoria-achados-compartilhados.md`. Os mapas estão na mesma pasta e também foram para a torre.

Corrigido e medido na torre no mesmo dia:
- **Pilha do PJe e do token A3.** O `pjeoffice-pro.service` apontava para `/opt/pjeoffice-pro`, que estava ausente. A pilha foi copiada, com os atalhos e `.desktop`, e o PJeOffice escuta em 8800/8801. Um passo novo no PASSO 10 traz essa pilha numa reinstalação (`42016268`).
- **Estado do home fora do tar.** Onze diretórios que eram estado, não cache (`.cargo`, `.rustup`, `.nvm`, `.npm-global` com o MCP `context-mode`, `.copilot`, `.wine`, `.android`, `.gradle`, `.m2`, contêineres e waydroid), foram copiados sem sobrescrever. O `.profile` não dá mais erro.
- **Token do Drive.** O `rclone.conf` mais novo (token de 11:35) foi levado.
- **Pacote e atalhos.** `inotify-tools` foi instalado. Os 159 atalhos do `pip --user` do 3.11 foram reapontados para o venv (`60262574`); das 15 falhas restantes, 14 já falhavam no notebook.
- **Alerta ao desktop.** O perfil AppArmor do `notify-send` negava unit com sandbox; foi consertado (`9f240dac`).
- **Tela e servidor que não dorme.** A máscara de sono, que acima estava registrada como "falta ela nascer do kit", passou a ser a fase 17 (`66c23f9d`).
- **Guardas do Ubuntu 26.04.** As do pre-commit, do closure Go, do `supervise-process-tree` e do colhedor foram corrigidas: `f0667c2c`, `02894369`, `855e3969`, `c4052966`.

Fica para o PASSO 10, porque vem dos discos: `/storage` (Ollama com 29 GB e VM do Claude Desktop), `/usr/local/bin`, a VM do escritório e a ISO (PASSO 10b), `/opt/oss-clones` (96 GB) e os atalhos de `gnome-boxes`/`codex-logs`, que já estão no kit.

Não se porta, por decisão:
- o BIND e o nginx do projeto vizinho;
- `/opt/divorcio*`;
- o `minio` do docker, que monta `/opt/divorcio`;
- o sistema do waydroid, parado desde 31/05 e descartado pelo `pacotes.txt:583`;
- o `sudoers.d/temp-claude`.

As 8 portas sem dono no notebook foram todas identificadas (cockpit, containerd, glances, `kilo`, VSCodium, túnel da migração e PJeOffice), e nenhuma é de produção.

**Primeiro boot autônomo da torre, com retaguarda (2026-09-24, 14:00).** A refutação Fable antes do transplante mostrou que o único boot da torre tinha sido antes de o portal ser habilitado. O boot autônomo nunca tinha sido exercitado. O teste foi feito com o ensaio da volta do PASSO 6. Primeiro, os 5 conectores do notebook subiram (`ready=4` nos cinco). Depois veio `systemctl reboot` na torre, sem nenhuma ajuda durante o boot.

Medido:
- **Tempos:** SSH de volta em 25 s; 5 conectores da torre com `ready=4` em 29 s; `systemd-analyze` em 39,5 s.
- **Estado:** 0 units falhadas; portal ativo; Ollama pulado limpo (`ConditionResult=no`); perfil AppArmor do `notify-send` com `attach_disconnected` carregado; alvos de sono mascarados.
- **Tela:** o lightdm executou `lightdm-ativar-saida-conectada --lightdm` ao abrir o greeter (`lightdm: :0=ativo`, exit 0).
- **Sessão do dono:** relogada com `umask 0022`, e PJeOffice ativo. O IP ficou em `192.168.1.10` (DHCP; MAC `9c:6b:00:a5:70:c7`).
- **Borda:** a home sem cache ficou 200 o tempo todo, servida pelo notebook. A API passou por 503 (dinâmica do notebook congelada), um erro de conexão às 14:01:33 e 200 às 14:01:36, já pela torre.

Depois, os conectores do notebook foram parados de novo. O boot mede ~40 s até a borda voltar; é a parte da torre na janela do transplante.

**PASSO 9 feito, com um incidente e uma decisão (2026-09-24, 14:15–15:05).** O dono transplantou só o NVMe do notebook e deixou o HDD de 2,5" fora. A firmware da ASRock criou a entrada `debian` a partir da ESP do NVMe velho e a pôs na frente de `Ubuntu` (`BootOrder: 0001,0000`): a torre subiu o Debian 12 congelado, e a borda deu **530** de ~14:50 a 15:03. Exatamente o aviso do PASSO 9 do `LEIA-ME.txt`, e a ordem no UEFI não bastou. Correção pelo próprio Debian: `efibootmgr -o 0000,0001` e `-n 0000`, cópia da sessão e da memória para o Kingston, reboot. Medido depois: `BootCurrent: 0000`, SSH em ~25 s, 5 conectores `ready=4`, 0 units falhadas, borda 200. **Se a firmware voltar a preferir `debian`, apaga-se só a entrada NVRAM (`efibootmgr -B -b 0001`); o disco fica intacto.**

**Decisão sobre o HDD (2026-09-24, 15:05).** O HDD guardava `/mnt/hdd/backups/` (destino dos timers de backup), `/mnt/hdd/arquivo/` (VMs do GNOME Boxes 27 GB, sessões e logs do Codex, `android-vm-lab`, `opt-backups`, `pool-divorcio`) e o bind `/opt/divorcio` (projeto vizinho arquivado). Nada disso serve o portal; o que o portal precisa é de um **destino de backup em disco físico diferente**, e o Toshiba de 1,8 TB (ext4, `backup-frio`, já com o `frio-20260924`) cumpre isso hoje. Fica: o Toshiba monta em `/mnt/hdd` por UUID (`nofail`), os timers de backup, `backup-restore` e `disk-headroom` são habilitados, e o HDD do notebook entra quando o dono quiser — montado em `/mnt/hdd-antigo`, com os atalhos de `arquivo/` apontados para lá. Sem urgência: é arquivo, não produção.

**504 do cliente `nginx-ssl early hints` — anterior à migração, aberto.** Medido na borda às 12:55 -03 (`httpRequestsAdaptiveGroups`, filtro `userAgent`, 24 h): 15 de 15 requisições desse UA em `/` saem 504, `originResponseStatus` 0, `cacheStatus` miss, e nenhuma chega ao nginx da origem (0 no `data/ops/access/nginx-2026-09-24.jsonl` da torre). O padrão existia no notebook (12:07, antes do cutover) e continua na torre. A causa está entre a borda e o túnel, e o instrumento que falta é o log do cloudflared em nível debug para uma dessas requisições. Um cliente, 15 por dia: não mexe no rastreio. O registro é para que o número não seja lido como regressão do cutover.

**Três ajustes do Ubuntu 26.04 que o notebook não pedia, medidos depois do cutover.** Todos já estão consertados e commitados na torre.
- Coreutils do uutils em symlink: a guarda do pre-commit recusava todo symlink e nenhum commit passava (`f0667c2c`).
- `pam_umask umask=022` virava 002 por causa do `USERGROUPS_ENAB` (`0aaa747d`, fase 14).
- O Python standalone do `uv` no venv 3.11 não tem `pidfd`, e o guardião dos jobs pesados saía 125 (`855e3969`).
- Resumo das causas em memória: `torre-ubuntu2604-armadilhas`.

**Enlace cabeado em 100 Mbit/s, e dois gerenciadores na mesma placa (2026-09-24, 18:02–21:15).** A torre usa uma RTL8125B (`r8169`) ligada à porta 2.5G do Sagemcom da TIM, com plano de 1 Gbit/s. A partir das 18:02 o enlace oscilou. Das 19:51 às 20:50 ele ficou em 100 Mbit/s, e o kernel registrou `Downshift occurred from negotiated speed 2.5Gbps to actual speed 100Mbps, check cabling!`.
- **O servidor foi descartado como causa.** Oito intervenções caíram de volta em 100: renegociar, EEE desligado, anúncio só até 1G, master e slave forçados, recarga do `r8169`, reset PCIe da placa e o driver `r8125` do fabricante (removido depois). O firmware e o módulo conferem com o md5 do pacote.
- **O reboot das 20:49 também subiu em 100M, às 20:50:22.** O enlace só voltou a 2.5G às 20:50:57, num `Lost carrier` sem nenhuma ação do servidor antes.
- **Estado medido depois:** 1018 Mbit/s reais, em download paralelo de mirror Ubuntu.
- **A PHY zera o anúncio de 1000BASE-T ao recuar.** O reg 9 lia `0x0000` durante o recuo e `0x0200` com o enlace são. Por isso `ethtool -r`, que só reinicia a negociação, não é um teste válido nesse estado.
- **O vigia não via nada disso, e agora vê** (`572bb44a`). Ele lê velocidade e quedas do cobre, alerta abaixo de `--velocidade-minima-mbit 1000` e não cura.
- **Episódio seguinte, às 21:11:05–21:12:00, o primeiro pego pelo vigia novo.** Foram 8 quedas num ritmo regular: o enlace sobe em 2.5G, cai uns 3 s depois e volta uns 4 s mais tarde. O vigia registrou "enlace cabeado caiu 6x na janela (11 transições)" e "sem portadora".
- **Nada do servidor precedeu as quedas.** Não houve `sudo`, reparo do vigia, carga de GPU ou IA, nem erro PCIe/AER.
- **O mesmo ritmo aparece às 14:19, 18:02 e 20:13.** Entre os episódios o enlace é limpo: 0 CRC e 3 `rx_errors` em 12,97 milhões de pacotes.
- **Padrão: perturbações episódicas no meio físico ou no roteador,** não canal marginal constante e não software. *Revisto em 2026-09-25: a parte "não software" não se sustenta; ver a revisão abaixo.*
- **Achado lateral, que não é a causa.** O dracut do 26.04 grava `/run/systemd/network/zzzz-dracut-default.network` a cada boot, e o `systemd-networkd` adota a `enp10s0` junto com o NetworkManager. O resultado são dois DHCP, duas rotas default (metric 100 e 1024) e briga de sysctl no journal.
- **Correção aplicada, mas NÃO PROVADA até o próximo boot.** Ela é o link `/etc/systemd/network/zzzz-dracut-default.network -> /dev/null`, e a fase 13 do kit passa a gravá-lo. Não houve reload ao vivo: com `SendRelease=true`, o networkd mandaria DHCPRELEASE de um lease que o NM usa.
- **Critério de prova no próximo boot:**
  - `networkctl list` mostra `enp10s0` como `unmanaged`;
  - `ip route show default` mostra uma rota só, com metric 100;
  - `ip -br addr` não mostra `metric 1024`;
  - `journalctl -b | grep "Foreign process 'NetworkManager'"` fica vazio.

**Revisão de 2026-09-25: duas causas de software seguem em aberto, e há um teste com critério registrado antes.**
- **Houve mais quedas curtas, de 3 a 8 s, e todas voltaram sozinhas em 2.5G.** Em 2026-09-24 foram às 22:33:26, 22:34:01, 22:34:54, 22:36:55, 22:37:20, 22:42:42 e 23:11:04. Em 2026-09-25 houve outra às 00:10:43, e `carrier_changes` chegou a 38. Nenhuma entrada do journal nos 20 s anteriores se repete de uma queda para outra.
- **"O servidor foi descartado" foi uma conclusão forte demais.** Das 19:51 às 20:50 o roteador também anunciava só 100baseT, então o recuo estava preso no lado dele. Nesse estado nenhuma ação do servidor subiria o enlace para 2.5G. As oito falhas mostram isso, mas não inocentam o servidor como gatilho das quedas.
- **Candidato 1: EEE ativo em 2.5G nas duas pontas.** O `ethtool --show-eee enp10s0` lê `enabled - active`, e o roteador anuncia EEE em 100, 1000 e 2500.
  - O `r8169` do kernel 7.0.0-34 desliga EEE em 2.5G só no RTL8125A (`RTL_GIGA_MAC_VER_61`, função `r8169_mdio_register`). Esta placa é RTL8125B (`VER_63`, XID 641), e o r8125 9.016.01 do fabricante também liga EEE em 2.5G nela.
  - O ritmo das rajadas combina com essa hipótese, mas não a prova. O enlace sobe e cai uns 3,6 s depois, e o 802.3 proíbe LPI só no primeiro segundo após o enlace subir.
- **Candidato 2: LTR programado no chip com ASPM desligado.** Com o SO no controle do ASPM (`aspm_manageable`), o `rtl_hw_aspm_clkreq_enable()` do 7.0.0-34 chama `rtl_enable_ltr()`.
  - Essa chamada liga LTR, `ALDPS_LTR_EN` (economia da PHY sem enlace atrelada ao LTR) e o gatilho de L1.2, mesmo com o enlace PCIe em `ASPM Disabled`.
  - A leitura do BAR2 confirmou isso nesta placa: Config2 `0xbc` (`ClkReqEn=1`) e Config5 `0x03` (`ASPM_en=1`).
  - O r8125 do fabricante só faz a mesma programação quando `aspm` está ligado e o offset 0x99 herdado da BIOS tem bits de L1 ligados.
- **Pista de outra plataforma, não causa.** O bug Red Hat 2529752 relata RTL8125B rev 05 com firmware `rtl8125b-2`, 291 quedas em 8 h e recuo para 100M. Lá o 7.1.12 era estável e o 7.1.13 não.
  - O patch "r8169: don't enable chip LTR" (set/2026) condiciona o LTR a `pci_dev->ltr_path`.
  - Aqui todos os saltos PCIe (00:02.1, 03:00.0, 04:0b.0 e 0a:00.0) têm `LTR+`, e o `_OSC` entrega o LTR ao SO. Esse patch, portanto, não mudaria nada nesta máquina.
- **Trocar de kernel não é teste.** O 7.0.0-30 e o 7.0.0-34 têm o mesmo `r8169` (srcversion `997888E1ECA4EA2C2C90B45`).
- **Poucas horas quietas não provam nada.** A mesma configuração ficou 5,5 h limpa nos boots de 08:36 a 14:00 de 2026-09-24.
- **Teste 1: EEE desligado, uma variável por vez.** A persistência é `networkmanager.passthrough` com `ethtool.eee-enabled: "false"` no `/etc/netplan/50-rede-cabo.yaml`.
  - O bloco `cabo` ganhou `renderer: NetworkManager`. Sem isso o netplan recusa o passthrough, porque o arquivo 50 é lido antes do 90, que define o renderer global.
  - Um `netplan generate` em raiz temporária mudou só o `netplan-cabo.nmconnection`, que ganhou `[ethtool] eee-enabled=false`.
  - O `nmcli device reapply` recusa mudança em `ethtool`, então a aplicação foi por `nmcli connection up netplan-cabo` às **2026-09-25 02:04:33**. É o mesmo caminho do boot.
  - **A queda das 02:04:33–02:04:37 foi provocada.** Ela levou `carrier_changes` de 38 a 40 e não conta no critério.
  - Estado medido depois: 2.5G full e `EEE status: disabled`. Houve 908 Mbit/s médios em 8 s com 8 fluxos do mirror Ubuntu, com a rampa do TCP incluída, então não houve perda de velocidade.
- **Critério registrado antes do teste:**
  - sucesso: zero quedas não provocadas por pelo menos 24 h depois da aplicação, ou seja, até 2026-09-26 02:04:37. A medida é o domínio `enlace` do vigia e o `carrier_changes`, que precisa seguir em 40 se não houver reboot;
  - falha: uma única queda não provocada refuta o EEE.
  - Se falhar, o passo 2 é `pcie_aspm=off` no próximo reboot. Com ele o `pci_disable_link_state()` falha, o `aspm_manageable` fica 0 e o `rtl_enable_ltr()` não roda.
  - Os dois passos nunca rodam juntos.
- **O kit ainda não recebeu a mudança, de propósito.** O modelo `ops/instalacao-simples/50-rede-cabo.yaml.modelo` roda antes de existir NetworkManager. Um `renderer: NetworkManager` ali quebraria a instalação. Se o critério passar, quem grava o EEE desligado é a fase de rede do `provisionar.sh`, depois da passagem para o NM.

---

## O que NÃO portar

`wikijuridica-energia*` (RAPL do Intel; num Ryzen a `ConditionPathExists` falha como condição, sem `OnFailure` — instalar o symlink mesmo assim, senão o gate fica impossível de passar) · `ops/tlp.d/` (TLP é de laptop) · perfil Wi-Fi e tudo que cite `wlp2s0` · as 4 camadas de bloqueio de suspensão · `ops/nginx/wikijuridica.conf` (modelo antigo) · `README.md:28` (manda usar o nginx do sistema — desatualizado).

**Re-derivar, não copiar:** `MemoryHigh=15G` (veio de 19,4 GiB), `GOMEMLIMIT=3GiB`, e os limiares do earlyoom.

> **`wikijuridica-network-health.timer` derrubava a rede da máquina nova — consertado em 2026-09-22.** O `ExecStart` traz `--repair --banda-esperada 5GHz`, e numa placa **cabeada** o check classificava "rádio não associado" como curável; o degrau 0 já executa `nmcli connection up`, e o degrau 1, `nmcli device disconnect` na interface do uplink.
>
> **O diagnóstico que este documento trazia estava errado, e a correção importa porque o conserto óbvio não funcionaria.** Estava escrito que "numa placa cabeada o `iw dev link` **falha**". Ele não falha: medido em 2026-09-22 (kernel 6.1, iw 5.19), `iw dev lo link` devolve **rc 0** e a string `"Not connected."` — a **mesma** de um rádio de verdade que perdeu a associação. O `rc != 0` significa "a interface não existe", não "é cabeada". Quem separa os dois casos é o kernel, pelo sysfs: `/sys/class/net/<iface>/phy80211` existe só onde o `cfg80211` registrou um netdev de rádio, e nasce no **registro**, não na associação — então rádio desassociado continua passando.
>
> O conserto está em `tools/check-network-health`, com 15 testes e **cinco** mutantes, entre eles o conserto errado pelo rc, aplicado como mutante para provar que não consertava. Rádio presente cujo `iw` não responde agora sai **2 (NÃO MEDIDO)** no domínio `instrumento`, que não autoriza cura — antes o vigia cegava e saía verde. O timer **saiu** do adiamento da janela e sobe no passo 5/5 do cutover, por último de todas.
