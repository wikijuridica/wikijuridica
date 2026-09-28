# Migração do servidor — como este plano foi apurado

**2026-09-22** · Companheiro de [`MIGRACAO_SERVIDOR_20260922.md`](MIGRACAO_SERVIDOR_20260922.md), que é o estado final. Este arquivo guarda o **caminho** — o que caiu, por quê, e o que ficou no lugar.

Existe por um motivo prático: quem executa lê o estado final, não a arqueologia. Mas quem for **mexer** no plano precisa saber o que já foi tentado e derrubado, senão reintroduz um erro que custou horas para achar.

---

## O método

Medir a máquina → ler o contrato e o código → delegar varredura → **tentar derrubar o resultado** → corrigir. Oito relatórios de agente, três rodadas de advisor, **quatro rodadas de refutação adversarial**.

As refutações derrubaram **oito** pontos do plano e corrigiram **quinze** erros factuais — inclusive um cometido nas duas direções, e uma contradição em que o texto foi corrigido e o script executável ficou na versão velha.

**Depois veio uma quinta rodada, e o método dela é outro.** As quatro primeiras atacaram o plano; a quinta auditou o **executável** e o **conteúdo real da mídia gravada** — a classe de defeito que passa em `bash -n`, em `shellcheck` e em qualquer leitura do texto, porque o caminho está certo e só não existe ainda, ou porque a guarda sai verde exatamente onde falha. Ela está na seção *Quinta rodada*, mais abaixo, e foi a que achou o passo que **não existia em script nenhum**: instalar as units.

---

## As duas viradas de decisão

### Distro: Debian 13 → Ubuntu Server 26.04.1

A primeira versão escolheu Debian 13, justificando com "o repo CUDA da NVIDIA para debian13 serve `cuda-drivers_615.71.09-2`". A refutação derrubou: Blackwell exige módulo **aberto**, e não havia variante `-open` em suíte nenhuma do Debian — o próprio wiki dele diz *"Currently no Debian-packaged version supports Blackwell GPUs… consider other packaging methods"*.

**Depois veio o erro na direção oposta, e foi pior:** a afirmação de que **"não há um único pacote com 'open' naquele índice"**. Também errada — `nvidia-open_615.71.09-2_amd64.deb` responde HTTP 200, e o guia oficial da NVIDIA para Debian manda exatamente `apt -V install nvidia-open`. O listing HTML **trunca antes da letra "n"**, e a truncagem foi lida como ausência.

**A escolha do Ubuntu sobrevive, mas pelo argumento certo:** o que ele entrega e o Debian não é o módulo **pré-compilado e assinado pela Canonical**, versionado junto ao ABI do kernel — zero DKMS, zero MOK. Pelo repo da NVIDIA no Debian o caminho existe, mas passa por DKMS e exige enrolar chave. Para um servidor 24/7 provisionado sem supervisão, a diferença é material.

### Canal: rede → transplante → backup frio + delta, com transplante depois

Começou com "rede e HDD externo". Medir mudou tudo:

| canal | medido |
|---|---|
| Toshiba na USB 2.0 | **38,3 MB/s** |
| HDD SATA interno | **107 MB/s** |
| NVMe Kingston | **2,2 GB/s** |

Com o notebook sendo aposentado, "transferir" deixou de ser o problema certo — transplantar os discos é 57× mais rápido. Mas a terceira refutação derrubou isso **como canal**: transplantar exige desligar o notebook, e o cutover precisa da velha **ligada**.

A síntese: o dado atravessa por backup frio + delta (o churn de 24 h fora de caches é de **355 arquivos, 2.597 MB**), e os discos são transplantados **depois** do cutover, como destino final.

---

## O que cada rodada de refutação derrubou

### Primeira rodada

Dois pontos caíram inteiros:

- **Parar o nginx cedo** serviria 502 na janela toda. O nginx é quem serve o acervo estático (`root /opt/wiki/public`, com o comentário "se o Go morrer ou não subir, o acervo continua no ar"). O custo está medido no repositório: em 2026-08-11 o Googlebot levou 19 respostas 530 e 8 de 502, e **nas seis horas seguintes o rastreio caiu de ~300 req/h para 2**, patamar que durou mais de um dia.
- **`stop` sem `disable`**: 57 timers `Persistent=true` voltariam num reboot.

Mais cinco erros factuais: `releases/current` que nunca existiu, um bind-mount que já tinha `nofail`, `/etc/letsencrypt` classificado como essencial sendo resíduo de TLS, a aritmética do Ventoy, e as units de energia cuja exclusão tornaria o gate impossível de passar.

E **duas das três correções propostas para o grafo estavam erradas**: `json.Decoder` quebraria um teste que exige o número da linha, e o "teto de grau com amostragem" corromperia o `Impacto`, que lê exatamente as arestas que seriam cortadas.

### Segunda rodada — a contradição grosseira

O plano prometia "nginx e túnel no ar" **e** mandava desligar o notebook antes de validar. Máquina desligada não serve nada: entre o `poweroff` e a validação não haveria **nenhum conector do túnel**, e a borda devolveria **530** por dezenas de minutos.

Pelo mesmo motivo, "fazer `disable` na velha depois do cutover" era **inexecutável**. E a Fase 3 subia servidor, túnel e timers na nova **antes do dado** — pondo as duas máquinas no mesmo túnel.

Mais: `--exclude '*.db'` sem escopo **apagaria as senhas do Thunderbird** (`key4.db`) e o NSS do token A3; o par de pacotes NVIDIA escolhido era **ininstalável** (`Conflicts` entre sabores); e o `bin/` transplantado traria o binário em laço, fazendo a validação nunca passar.

### Terceira rodada — texto corrigido, executável não

O plano passou a carregar **duas sequências incompatíveis**: a decisão de canal na versão nova, e a Fase 1, a Fase 4 e o script que o dono ia rodar ainda na antiga. Quem seguisse o `LEIA-ME.txt` executaria a versão derrubada.

Mais três quedas:

- **`tools/deploy-publico` aborta** se `check-units-instaladas` reprovar, e o gate reprova ~59 timers inativos. O caminho sancionado exigiria os timers antes do servidor — mas habilitar os timers **sobe o túnel sozinho**, porque `check-tunnel-health --repair` reinicia o `cloudflared` após 2 ciclos ruins.
- **O "downtime de segundos" era falso**: o `stop` leva 5–30 s por causa do `grace-period`, medido no journal. E a correção inverteu a própria regra — com o conteúdo já validado, a sobreposição é **segura**, e o certo é make-before-break com janela zero.
- **Desabilitar 5 units na velha não basta: são 25**, contando 11 não-timer e 9 de usuário com linger. E a cadeia do cérebro chega a `purge-edge-cache`, o que faria a máquina velha **purgar a borda que a nova serve**.

E o corte em `tribunal` chamado de "seguro" faria o MCP responder **`Total = 0`** para o STJ — a mesma fabricação de ausência rejeitada duas linhas acima.

### Quarta rodada — a que mais salvou dado

1. **`--exclude '/opt/wiki/var/'` apagaria três bancos e a trilha LGPD.** `var/` estava classificado como "3,3 G de cache". Lá dentro: `social.db`, `lgpd.db`, `datajudfila.db`, o **armazém DJEN** (154 M), o **bruto do log de origem** (144 M) e — o pior — **`social.db.sal`**, que `internal/moderacao/pseudonimo.go` **regenera em silêncio** se sumir, quebrando a correlação legal sem emitir erro. Três desses são cópia única.
2. **A lista de exclusão não funcionava.** Testado em dry-run: padrões ancorados em `/opt/wiki/…` são inertes quando a origem é `/opt/wiki/` — os bancos brutos passariam e **sobrescreveriam as cópias boas**. E a mesma lista no `tar` significa o oposto, porque a barra final desarma o casamento.
3. **`--exclude '.toolchains/'` com "exceto go1.26.6"** não tem exceção possível em rsync, e derrubaria o **pipeline sancionado de commit de `v2_pages`**, que exige um tarball com SHA pinado.
4. **O home não tinha regra** (30 G medidos contra os "< 0,5 GB" orçados), **`/root` não estava no plano**, e `~/.local/state/wikijuridica/perfil-*` — as **sessões logadas das redes sociais** — não aparecia em lugar nenhum.

Mais: `VACUUM INTO` duas vezes no mesmo destino **falha**; `bin/*.anterior` **é o alvo de rollback do deploy**; e o firewall tem **três donos**, então salvar só a foto do `nft` não basta.

Duas afirmações **corrigidas para melhor**: os 1.144 `tmp_obj_*` do `.git` são **hardlinks dos objetos reais**, não corrupção; e os "41.598 arquivos com mais de um link" eram do HDD inteiro — em `/opt/wiki` são 3.756.

### Rodada final do advisor — faltava o plano de EXECUÇÃO

Quatro rodadas verificaram *o quê*; nenhuma verificou *em que ordem, por qual script*.

1. **A Fase 0 não tinha quando.** Três itens exigem a velha quente, e o `.credentials.json` rotaciona diariamente.
2. **A ordem interna dos scripts não estava escrita.** Caso concreto: validar o grafo **antes** de rodar a unit que gera o manifesto reprova por `fingerprint mismatch`, e quem opera não sabe se é bug ou ordem.
3. **`congelar-velha.sh` antes de `cutover-tunel.sh` reabriria o 530** — o `mask` alcança o `nginx` da velha, que é a única origem servindo até o cutover terminar.

---

## O que a execução achou, além do plano

Cinco defeitos que só apareceram ao **rodar** o que estava escrito:

| achado | como apareceu |
|---|---|
| **Os "1.111 pacotes Python" eram 1.111 entradas de diretório**, não pacotes — os reais são 477 `.dist-info` e 473 no freeze | contagem independente ao gerar o freeze |
| **A varredura de escalada só via a grafia de shell.** Os tools em Python escalam por lista (`["sudo","-n",…]`), que aquele padrão não casa: 7 arquivos viraram **13 binários em 19 arquivos** | ao escrever a regra de sudoers nomeada |
| **O instrumento contava a si mesmo** (15/21 em vez de 13/19) depois de ser versionado sob `ops/` | ao rodar o script do caminho novo |
| **O `sed` comia a barra de escape do `grub.cfg`**, gerando `ds=nocloud;` — e a verificação usava `grep 'ds=nocloud'`, que **passa sem a barra**. Guarda pela metade | `cat -A` na ISO gerada |
| **Criar o drop-in em `ops/systemd/` mudou produção na hora** — aquele diretório é symlink de `/etc/systemd/system/`, e o `PATH` de ~75 units mudou no instante em que o arquivo nasceu. Pior: apontava para um venv 3.12 com **1 pacote**, enquanto os 477 estão no 3.11 | ao provar o mecanismo de prefixo |

**A auditoria sistemática, depois — e foi ela que achou o mais grave.** Depois de achar um nome de unit errado à mão, varri *toda* unit, *todo* caminho e *todo* `ExecStart` citado nos scripts contra o que a máquina realmente tem:

| achado | o que teria acontecido |
|---|---|
| **As units das réplicas do túnel tinham nome inexistente** (`cloudflared-tunnel-replica@` em vez de `cloudflared-wikijuridica-replica@`) | falha no passo 2 do cutover, com o vigia da velha já desarmado. E no `congelar-velha.sh` seria pior: o laço que confere "nenhum conector ativo aqui" contaria **zero** para units inexistentes, concluiria que o cutover terminou, e mascararia o nginx com a velha ainda servindo |
| **`/storage` é partição separada**, não diretório da raiz | **51 GB** (29 de blobs do Ollama, 22 da VM do Claude) ficariam para trás **em silêncio** — `copiar_de` trata origem ausente como aviso |
| **`blockdev --setro` sem guarda** | rodar o consolidar no notebook, ou passar o disco errado, **congela o sistema** em somente-leitura. Sem desfazer sem reboot forçado |
| **`authorized_keys` não existia** na máquina velha | `ssh -o BatchMode=yes` falha na hora: o delta não roda, e o cutover não consegue desarmar o vigia nem parar os conectores da velha |
| **Destinos que são symlink morto** (`~/.config/Claude/vm_bundles`, `/usr/share/ollama` → `/storage`) | `install -d` sobre link morto **falha** — testado |
| **`ai-process-reaper.timer` não existe** (o timer é `ai-orphan-reaper`) | o congelamento deixaria um timer de usuário vivo |
| **`tar` exit 1 tratado como falha** | num repositório vivo o tar **sempre** devolve 1 ("file changed as we read it"). O backup reprovaria toda vez — e reprovou |
| **Três textos, três caminhos** para o mesmo diretório de backup | o dono apontaria para o lugar errado no passo mais delicado |
| **`goaltree` é editable órfão** | nada quebra, mas quem lê a linha do freeze procura um diretório que não existe |

**A terceira varredura: capturar não é restaurar.** Comparando os 466 termos técnicos do plano contra *todos* os scripts e documentos, apareceu um padrão que nenhuma leitura tinha pego — **metade do trabalho estava feito duas vezes**:

| capturado por | faltava quem restaurasse |
|---|---|
| Fase 0.2 — 65 segredos cifrados em dois discos | nada os punha de volta nos 19 destinos, com dono e modo |
| Fase 0.3 — udev, audit, sysctl, `ollama.service`, firewall | nada os punha de volta nos 13 destinos |

Nasceram daí o `restaurar-segredos.sh` e o `restaurar-etc.sh`. O segundo **recusa** três coisas, e cada recusa é decisão: não sobrescreve o `/etc/fstab` (o da nova tem os UUIDs dela), não aplica o ruleset do nftables (são três donos de firewall, e um `ufw enable` regrava as chains por cima), e não traz o `/etc/sudoers.d` da velha (que tem um `NOPASSWD: ALL`).

A mesma varredura achou o último caminho descoberto: `/var/log/audit`, 38 MB — a trilha de quem mexeu em configuração, que seis regras de auditoria registravam e que não se reconstrói depois que o disco sai.

Três ferramentas nasceram disso e ficam no kit: `conferir-units-citadas.py`, `conferir_execstart` e `verificar-kit.sh`, que roda todas as verificações num comando — **eram 28 quando ele nasceu; 93 depois da quinta rodada, medidas em 2026-09-22 às 13h37 sobre o kit commitado**. A contagem sobe a cada script novo do kit, e é por isso que ela não vale como estado: o que vale é rodar.

E dois no caminho, consertados junto (Regra 20):

- **`warm-origin-cache` falhava por construção** numa rota de 63 MB com timeout de 30 s fixos — e `except Exception: return 0, 0` **engolia o motivo**, deixando o operador com "status 0" sem saber se foi timeout, recusa ou DNS.
- **O campo `metodo` do MCP não declarava a agregação**, então `total: 0` para o STJ seria lido como "nada está ligado a esta entidade".

---

## Quinta rodada — auditar o executável, e a mídia que já estava gravada

As quatro rodadas anteriores tentaram derrubar o **plano**. Esta leu o que os scripts **fazem** e o que a mídia gravada **realmente contém**, e é outra classe de achado: nenhum destes aparece em `bash -n`, em `shellcheck` ou numa leitura do texto — o caminho está sintaticamente certo, só não existe ainda no instante em que é lido; ou o arquivo que devia estar na ISO não está; ou a guarda sai verde justamente onde falha.

Seis commits, cada um com a medição ao lado: `c62f5d0e`, `5986a20e`, `d8ab1d48`, `06313724`, `292159ef`, `7dda0a1c`.

### O que caiu

| achado | a medição que o derrubou | o que teria custado |
|---|---|---|
| **Ninguém instalava as units.** Nenhum script fazia o symlink de `ops/systemd/` para `/etc/systemd/system` | `grep -rn 'ln -s' ops/provisionamento/` devolvia **um** acerto, e era o symlink de home do `consolidar-discos.sh`. O `provisionar.sh` apenas **checava**, e naquela janela o repositório ainda nem chegou | `systemctl start` sobre **142 units inexistentes**, com a mensagem "não consegui iniciar X" — sintoma a dois passos da causa, no passo em que a máquina velha ainda é a única origem |
| **`ln -sfn` sem o `-T` instala e inutiliza em silêncio** | Medido nos dois sentidos com unit descartável, produção intocada: contra destino que já é diretório real, `ln -sfn` **sai 0** e cria `X.service.d/X.service.d`; com `-T`, sai 1 e diz por quê | drop-in aninhado, inerte, **com a saída verde** — carregando `Slice=`/`PATH` errado para a unit inteira, e sem aparecer em gate nenhum |
| **O provisionamento terminava verde sem o venv Python 3.11** | `uv` e `~/.local/share/uv` só chegam dentro do tar do home, no PASSO 4. A causa não era "o venv falha": era que a fase 3 e a fase pós-migração eram o **mesmo código sem distinção de fase** | as **819 tools Python** mortas, sem uma linha de erro, e nada no roteiro mandando re-rodar o script depois do PASSO 4 |
| **O roteiro mandava a máquina nova ler o HDD do notebook** | `LEIA-ME:88`, `:109` e `:143` — **numeração da versão então gravada**, não da atual — apontavam para `/mnt/hdd/…`, que é o HDD SATA interno do notebook e só chega na máquina nova no PASSO 9, **depois** dos passos que o liam | a migração parava ali, no passo em que o dono já tinha a máquina nova instalada e o backup pronto |
| **A instalação reinstalava a si mesma** | O `user-data` não tinha `shutdown:`, e o subiquity nasce em `REBOOT`. Conferido no instalador que vai rodar, não de memória: `subiquity_7403.snap` extraído da própria mídia gravada — `server/controllers/shutdown.py:36-37`, enum `["reboot","poweroff"]` | com boot order USB-first, a máquina reencontra o `/cdrom/nocloud/` e roda o autoinstall **de novo, zero-touch**, por cima do sistema recém-instalado |
| **A ordem 3c/3d era impossível de executar** | `restaurar-segredos.sh` precisa de `~/.ssh/id_ed25519` para decifrar o tarball `age`, e essa chave chega **dentro** do tar do home, no passo 4 (`exclusoes_home()` não exclui `.ssh`, conferido no mesmo dia). `restaurar-etc.sh` lê `ops/firewall/`, que está fora de `ops/provisionamento/` e não viaja na mídia | o primeiro era um impasse — a chave dentro do arquivo que ela abre. O segundo deixava a máquina **exposta sem emitir erro**: o jail de SSH do fail2ban não era aplicado e o script terminava verde |
| **O `ssh` rodava como root e não achava a chave** | `sudo ls /root/.ssh/` → só `known_hosts`; `sudo ssh rafael@localhost` → `Permission denied (publickey)`; o mesmo `ssh` como `rafael` → exit 0. No `rsync` do delta: **exit 12** antes, **exit 0 com 60 itens** depois | descobrir isso **no cutover**, com o vigia da máquina velha já desarmado — o pior momento possível, porque é quando a origem velha ainda é a única servindo |
| **A mídia entregava o kit pela metade** | O laço do `remasterizar-iso.sh` testava `[ -f "$extra" ]`, então **nenhum diretório** entrava na ISO. Provado por mutação numa cópia isolada do kit: reintroduzido o `[ -f ]`, a guarda por conjunto reprovou com exit 1 e **listou os 28 arquivos ausentes**, inclusive o `20-python.conf` | o silencioso de novo: o `provisionar.sh` emitia só um aviso e terminava verde, e a máquina nova nascia sem o venv 3.11 no PATH das ~75 units `wikijuridica-*` |
| **Um backtick executava `cloudflared tunnel login`** | A linha que avisa "NUNCA rode `cloudflared tunnel login`" escrevia o comando entre **backticks dentro de aspas duplas** — e ali o bash não cita, executa. Rodava toda vez que o `cert.pem` existia | é exatamente o comando que **sobrescreve o `cert.pem`**, que não se regenera sem re-rotear o DNS do domínio. Não foi fatal só porque o binário ainda não está no PATH do root nessa fase. Mesmo defeito já visto em `consolidar-discos.sh`, onde um backtick executou `ro` como comando |
| **`/usr/local/bin` não tinha produtor** | `grep -n 'usr/local' consolidar-discos.sh` vinha **vazio**: os 29 GB de blobs do Ollama atravessavam e o binário que os lê, não. São **44 itens** que pacote nenhum instala. Pior: o `provisionar.sh` **afirmava**, no aviso da fase do Ollama (linha 209 da versão de então), que o binário "vem do disco velho em consolidar-discos.sh" — e era ali que estava escrito o "Go estático" | a IA local não subiria — com os blobs no disco, que é o que torna o erro difícil de enxergar. E o `rclone`, que é o `ExecStart` do `escritorio-drive.service`, não chegaria: o `apt` traz o `rclone-browser`, a interface gráfica |
| **Sobrescrever era irreversível, nos dois restauradores** | Medido por incidente, não por leitura: às 14:17 o `.env.local` de produção — 6.351 bytes, 8 chaves, entre elas as três da Cloudflare — virou a fixture de 33 bytes da bancada, e o sintoma só apareceu **uma hora depois**, em três units de borda com exit 2 ("sem credencial Cloudflare"). O `por()` dos dois scripts sobrescrevia sem guardar | o arquivo continua existindo, com o modo e o dono certos, e `.env.local` é gitignored — então `git status` fica mudo. A recuperação exigiu decifrar o tarball de segredos de 10:47. Corrigido: preservam em `<destino>.substituido-AAAAMMDD-HHMMSS` e **param** se a cópia falhar |
| **A guarda nova abria um vazamento de segredo** | `git check-ignore -v` sobre os seis destinos que os restauradores tocam dentro de `/opt/wiki`: **quatro** dos preservados entrariam no git — `.env.social`, a chave IndexNow, a prova dela e `ops/ingress.env`. Só `.env.local.*` já estava coberto | a guarda escrita para **evitar perda** criava exposição: um `git add` por diretório de outra frente varreria quatro segredos para dentro do repositório, que tem espelho. `*.substituido-20*` fecha, e nenhum arquivo rastreado casa o padrão |
| **A bancada nunca via o `restaurar-etc.sh` escrever** | A única cobertura dele era `--seco`, que por definição retorna **antes** da escrita. E o primeiro caso que escrevi para cobrir isso passou **por acidente**: procurava o caminho na saída, e o mesmo caminho aparece dentro da mensagem de FALHA `NAO consegui guardar o <caminho>` | teste verde sobre o erro que devia pegar. Agora ele exige a marca `✓` do sucesso, e o bloco D roda num namespace próprio onde só ele deixa `/etc` gravável — a trava de somente-leitura dos outros blocos fica intacta |
| **`congelar-velha.sh` citado sem `--sim`** em dois scripts | Sem a flag ele sai **0 sem congelar nada** (`congelar-velha.sh:66`) | o operador leria "concluído" com a máquina velha ainda armada para voltar sozinha em qualquer reboot, com 5 conectores e a credencial viva |

**Duas afirmações corrigidas, e as duas mudam o que tem de atravessar.** O `ollama` **não é Go estático** — medido com `file` e `readelf -d`, o 0.33.3 é **PIE dinâmico** (`libstdc++`, `libgcc_s`, `libresolv`, `libdl`, `libpthread`, `libm`, `libc`) e **sem RPATH/RUNPATH**. E o binário sozinho não resolve: quem gera token é `/usr/local/lib/ollama/llama-server`, **2,1 GB de runtimes**, que também não tinham produtor. Sem eles, `ollama serve` sobe, responde `/api/tags` e falha em **toda** geração — parece vivo, e esse é o custo.

O `tmux` é a única exclusão do `/usr/local/bin`, e o motivo não é o que se supunha: não é ABI, é **sombreamento**. A distro instala o dela em `/usr/bin`, e `/usr/local/bin` vem antes no PATH para sempre — se os sonames do Ubuntu 26.04 forem compatíveis, o `ldd` passa e o sombreamento fica invisível, que é o pior desfecho.

### A guarda de classe, e o que ela achou sozinha

Dois dos furos acima eram da mesma família — **dependência que chega depois de quem a usa** —, e nenhum aparece em sintaxe. Daí a **seção 12** do `verificar-kit.sh`: ela extrai todo `$RAIZ/…` de cada script que roda antes do PASSO 4 e reprova o que não estiver sob `ops/provisionamento/`, a menos que conste de uma lista de exceções **com o motivo escrito ao lado**. Ausência tratada com um `aviso` que o operador lê como "está tudo bem" **não conta como exceção: é o defeito**.

Duas exceções a própria guarda encontrou, e cada uma foi classificada lendo o código antes de declarar: o `.venv-tools311`, que é destino e não dependência, e o `goaltree`, editable órfão (`grep -rl 'import goaltree'` vem vazio). Provada por mutação: acrescentado um `$RAIZ/ops/firewall/x` ao `provisionar.sh` numa cópia isolada, a seção reprova nomeando o caminho.

### A bancada do instalador, e os três defeitos dela mesma

O passo que instala as units nasceu nesta rodada e era o único do kit sem bancada. Ela ficou **autossuficiente**: extrai as funções do `migrar-dados.sh` real, na hora, entre marcadores, em vez de depender de uma cópia — testar a cópia seria testar a cópia. Se os marcadores sumirem, ela **para com exit 2** em vez de seguir verde testando nada.

Três defeitos consertados no próprio harness durante a promoção, e o segundo é o que importa guardar:

- as raízes de teste nasciam em `ops/provisionamento/`, deixando `t1..t4` untracked dentro do repositório — e a próxima remasterização os levaria **para dentro da ISO**;
- **a mutação estava cega.** O mutante era gerado a partir de um arquivo que deixou de existir, saía com **zero bytes**, e a guarda era só `diff` — arquivo vazio "difere" do original, então ela dizia "mutante aplicado". Carregar um arquivo vazio deixa as funções **originais** em memória: a asserção seguinte passava sem testar nada. Agora há **piso de volume** (não vazio, ≥ 20 linhas) além do `diff`;
- a bancada cita units de mentira, e o `conferir-units-citadas` passou a reprovar por elas. A isenção é **pelo prefixo `zzfalsa-`**, nunca pelo arquivo: isentar o arquivo inteiro criaria ponto cego — uma bancada que citasse `wikijuridica-server.servico`, nome real escrito errado, passaria despercebida. E a contagem de isentadas é **impressa**, para a exceção não virar filtro que ninguém vê.

Com a mutação funcionando de verdade: controle 0 falhas · `ln -sfnT` comentado **8 falhas** · destino `.d` já diretório real **2 falhas** · restaurado 0 falhas.

### O que esta rodada NÃO provou, e fica registrado

- **Nenhuma biblioteca do Ubuntu 26.04 foi medida.** O instrumento do `/usr/local/bin` é o `ldd` **da máquina nova**, e ele só existe lá. O `pwnat`, compilado com AddressSanitizer contra a `libasan.so.8` do gcc-12 do Debian 12, é o candidato natural a reprovar — e quem decide é o `ldd` de lá.
- **O caminho destrutivo do `preparar-disco-backup.sh` nunca executou** — não há alvo seguro nesta máquina. O que se provou foram as **recusas**, como usuário comum: `/dev/nvme0n1` e `/dev/nvme0n1p6` recusados por serem o disco do sistema, `/dev/sda` recusado porque `/dev/sda1` carrega `/mnt/hdd`, `/dev/sda1` recusado por ser partição, `/etc/hostname` recusado por não ser dispositivo de bloco. Nunca rodado contra `/dev/sdb`.
- **`shutdown: poweroff` foi conferido no schema do instalador, não executado.**
- **A mídia física não foi verificada.** O que se mediu foi a ISO no disco: a mais nova (`…iso.v4`, 12:55 de 2026-09-22) **não tem** `shutdown: poweroff` e **não tem** `preparar-disco-backup.sh` nem `testa-instalar-units.sh`, enquanto os arquivos do kit são das 13h. O que está gravado no Toshiba exige plugá-lo e rodar o `verificar-midia.sh`.

---

## Duas armadilhas de processo, para não repetir

**Hook que bloqueia comando composto descarta a preparação junto.** O commit do conserto do grafo falhou com `could not read log file` porque o heredoc que criava a mensagem estava no **mesmo comando** que o hook barrou por juntar as duas operações de git staging e git commit. O arquivo nunca chegou a existir. Preparar a mensagem numa chamada, commitar na seguinte.

**Editar um script enquanto ele roda corrompe a execução.** Editei o `fazer-backup-frio.sh` três vezes durante um `tar` de 24 GB. O bash lê o script **por offset de byte**: inserir linhas no meio desloca tudo o que vem depois, e ele passa a executar o resto de uma palavra cortada ao meio. O sintoma foi `linha 106: t:: comando não encontrado` — `t:` não existe em lugar nenhum do código. Perdi o backup inteiro. Commite, rode uma **cópia**, edite o original.

**`cmd | tail` engole o exit real.** O mesmo commit foi reportado como sucesso porque o pipeline devolveu 0; o `exit=128` estava impresso na saída e passou despercebido. Redirecionar para arquivo e ler `$?` direto, ou `PIPESTATUS[0]`.

---

## Quinta rodada — três buracos que só apareceram com o kit inteiro montado

As quatro primeiras rodadas refutaram o **plano**. Esta refutou a **execução**: o kit já existia, verde, com bancada, e ainda assim carregava três defeitos que nenhuma leitura de plano acha, porque só existem na costura entre um script e o seguinte.

### 1. O cutover levava os bancos de ONTEM — e nenhum verde acusava

O passo 6 do `migrar-dados.sh` posicionava `$BACKUP/bancos/*`: os bancos do **backup frio**, feitos no PASSO 3 do LEIA-ME, horas ou dias antes do cutover. E o delta do passo 5 **não os supria** — não por esquecimento, mas por desenho: as exclusões derivadas de `BANCOS` barram todo `.db`/`.sqlite` e os `-wal`, `-shm` e `-journal` deles, porque copiar banco a quente entrega banco rasgado.

O plano mandava o certo desde a Fase 5 — *"parar os escritores na velha, `VACUUM INTO` fresco lá, e só então o delta"* — e o script não fazia nenhum dos três. O efeito era perda silenciosa de dado de produção: tudo o que a máquina velha escrevesse em `fila.sqlite`, `social.db`, `datajudfila.db` e `prazos.db` entre o backup e o cutover ficava para trás, **com os arquivos íntegros, `PRAGMA quick_check` dizendo `ok` e o conteúdo de ontem**. `prazos.db` é prazo processual de advogado.

A lição que fica é sobre a **forma** do defeito, não sobre ele: cada peça estava certa isolada. A exclusão dos bancos no rsync está certa. O `VACUUM INTO` da Fase 2 está certo. O passo 6 posicionando o que o backup trouxe está certo. O que estava errado era a **junção** — e junção não tem arquivo, então nenhuma bancada de arquivo a cobria.

### 2. A máquina nova serviria produção por dias sem um único timer

`migrar-dados.sh` habilita as 75 units **sem `--now`**, e isso está certo e é deliberado: com `--now`, `wikijuridica-tunnel-health.timer` roda `check-tunnel-health --repair`, que faz `sudo -n systemctl restart` nos `cloudflared` (`tools/check-tunnel-health:424`) — o túnel da nova subiria sozinho com a velha ainda servindo, e as duas ficariam no mesmo túnel.

Só que **ninguém dava `start` depois**. O `cutover-tunel.sh` subia os cinco conectores e parava ali. Entre o PASSO 6 e o reboot do PASSO 10 — e o LEIA-ME diz ao dono *"Observar. Dias, se quiser."* — a máquina nova serviria com **zero timer**: sem `wikijuridica-watchdog.timer`, que é quem roda `check-portal-health --repair`; sem aquecimento de borda; sem a cadeia de conteúdo; sem coleta.

**Tudo habilitado, nada correndo, e nenhum erro em lugar nenhum.** É a assinatura do defeito desta classe: timer que não roda não falha, ele apenas para de acontecer. O plano dizia *"só então os timers, e `tunnel-health` e `network-health` por último"*, e nenhum passo executava a frase.

### 3. O verificador conferia a sintaxe das bancadas e nunca as executava

`verificar-kit.sh` tinha 137 verdes e **nenhum deles vinha de uma asserção** das bancadas de `instalar-units`, `habilitar-units`, `preparar-disco-backup` e `restauradores`. A seção 1 confere a sintaxe de todo shell do kit e a 2 passa o `shellcheck`; nenhuma das duas executa nada. As duas únicas que rodavam eram a do `comum.sh` e a do autoinstall, por terem linha própria.

Bancada que ninguém roda vale o mesmo que bancada que não existe — com o agravante de que o verde do verificador passava a **afirmar mais do que media**. Custo de fechar: 10,3 s.

---

## A refutação que derrubou o chefe, e é a mais instrutiva desta rodada

Mandei um agente consertar `tools/check-network-health`, que numa placa cabeada classifica "rádio não associado" como curável e executa `nmcli device disconnect` **na interface do próprio uplink**. O briefing que escrevi dizia, com todas as letras, qual era o conserto:

> `rc != 0` → a interface **não é de rádio** → devolver `{}`.
> `rc == 0` e `"Not connected"` → rádio sem associação → continuar devolvendo `{"associado": False}`.

**Estava errado, e o conserto que eu prescrevi não consertaria o bug.** Medido na máquina (kernel 6.1, `iw` 5.19), e reconferido por mim depois:

```
iw dev lo         link -> rc 0    "Not connected."
iw dev virbr0     link -> rc 0    "Not connected."
iw dev wlp2s0     link -> rc 0    "Connected to e4:c0:e2:db:1d:45"
iw dev naoexiste0 link -> rc 237  "command failed: No such device (-19)"
```

Numa interface que **não é de rádio o `iw link` não falha**: devolve rc 0 e exatamente a mesma string de um rádio que perdeu a associação. O `rc != 0` significa "a interface não existe", não "é cabeada" — então a máquina cabeada cai precisamente no ramo que eu mandei **preservar**, e continuaria derrubando a própria rede. O agente provou isso aplicando o meu conserto como mutante e mostrando que o teste de fiação continuava pegando a chamada a `curar`.

Quem separa os dois casos é o kernel, pelo sysfs: `/sys/class/net/<iface>/phy80211` existe só onde o `cfg80211` registrou um netdev de rádio. Conferido: existe em `wlp2s0`, não existe em `lo`.

Três correções menores ao mesmo briefing: `CICLOS_RUINS_PARA_REPARO` **não existe** (é o literal `2`); o dano começa **um degrau antes** do que eu disse, no `nmcli connection up` do degrau 0, que também derruba conexão cabeada; e `rodar()` devolve rc 127 por `OSError`, sem exceção.

**O que isso ensina sobre orquestração:** o briefing detalhado é o que torna o agente útil — ele não herda a conversa — mas detalhe que eu não medi entra como **ordem**, não como hipótese. Um agente obediente teria implementado o meu erro, com teste verde em cima dele, e o vigia continuaria derrubando a rede da máquina nova. O que salvou foi o agente ter ido ao instrumento antes de escrever, e ter trazido o rc medido em vez do rc suposto.

É a mesma regra do contrato, aplicada na direção incomum: **evidência primária ganha de autoridade — inclusive da autoridade de quem mandou.**
