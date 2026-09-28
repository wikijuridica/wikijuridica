# Três lacunas fechadas — systemd 252 / cérebro / coleta STJ

Modo somente leitura. Nada foi editado, gravado no repo, commitado, nem unit
iniciada/parada. Marcação obrigatória por afirmação: **MEDIDO** (observei a saída),
**DERIVADO** (concluí de fonte primária + aritmética), **NÃO VERIFICÁVEL**.

Versão do alvo: **systemd 252 (252.39-1~deb12u2)**, Debian 12.15 — MEDIDO
(`systemctl --version`, `/etc/debian_version`).

---

## LACUNA A — `BindReadOnlyPaths` + `PrivateTmp=true` no systemd 252

### Veredito: a ROTA 1 FUNCIONA. Não é preciso desligar o `PrivateTmp`.

O bind mount **não é aplicado depois do /tmp privado no mesmo caminho** — é isso que
a aposta original supunha e é por isso que ela parecia arriscada. O que acontece é
melhor: **o /tmp privado nunca chega a cobrir o `/tmp` real durante a montagem**.

#### O que NÃO serve de prova (e por que a lacuna existia)

- **MEDIDO**: nenhuma unit instalada neste host combina `PrivateTmp=` com
  `BindPaths=`/`BindReadOnlyPaths=`. Varri `/etc/systemd/system`,
  `/usr/lib/systemd/system`, `/lib/systemd/system`, `/run/systemd/system`
  (`grep -rlE '^(BindPaths|BindReadOnlyPaths)='` → zero) e, para pegar drop-in e
  unit transiente, `systemctl show '*.service'` com as quatro propriedades → zero
  não-vazio. **Não há prova in vivo neste host.**
- **MEDIDO**: o `man systemd.exec` desta máquina **não declara** a ordem de aplicação
  entre `PrivateTmp=` e `BindPaths=`. A única frase de ordem no documento é sobre
  outra coisa (símbolos de `RuntimeDirectory=` criados "after any BindPaths= or
  TemporaryFileSystem= options have been set up").
- **MEDIDO, e descartado como instrumento**: tentei datar a ordem pelos mount IDs
  do namespace vivo (`/proc/926445/mountinfo`). Não serve: o host tem 37 mounts e o
  namespace 39, ocupando a faixa contígua 647–687 — os IDs vêm da cópia da árvore no
  `unshare` e da reutilização pelo IDA depois do `pivot_root`, não da ordem em que o
  systemd agiu. Registro aqui para ninguém repetir a tentativa.

#### O que fecha: a fonte primária do binário que está rodando

Li `src/core/namespace.c` da **versão exata do pacote** (sources.debian.org,
`systemd/252.39-1~deb12u2`, HTTP 200, 117.552 bytes). A cadeia é esta — **DERIVADO**
(leitura de fonte primária, não execução):

1. **linha 2134-2151** — sem `RootDirectory=`, o systemd não monta nada na raiz real.
   Conferido que este `if/else` está no corpo de `setup_namespace` (2008), **sem
   guarda de contagem de mounts** — o bloco anterior (2085-2132) é o tratamento de
   `RootImage=`, que aqui não se aplica:
   ```c
   root = "/run/systemd/unit-root";
   (void) mkdir_label(root, 0700);
   require_prefix = true;
   ```
   com o comentário que responde a pergunta inteira:
   > "Always create the mount namespace in a temporary directory, instead of operating
   > directly in the root. **The temporary directory prevents any mounts from being
   > potentially obscured [b]y other mounts we already applied.**"
2. **linha 2408** — `prefix_where_needed(mounts, n_mounts, root)` prefixa apenas o
   **destino** (`mount_entry_path`). **linha 377-394** — `append_bind_mounts` grava
   `.path_const = b->destination` e `.source_const = b->source` com `has_prefix`
   default `false`: a **origem nunca é prefixada**.
3. **linha 2417** `unshare(CLONE_NEWNS)` → **2440** `/` como `MS_SLAVE|MS_REC` →
   **2483** bind de `/` sobre `/run/systemd/unit-root` → **2493** `apply_mounts()` →
   **2498** `mount_move_root(root)`.
4. **linha 1441-1465** (`apply_one_mount`, caso `BIND_MOUNT`):
   ```c
   /* ... Note that bind mount source paths are always relative to the host root,
      hence we pass NULL as root directory to chase_symlinks() here. */
   r = chase_symlinks(mount_entry_source(m), NULL, CHASE_TRAIL_SLASH, &chased, NULL);
   ```

**Consequência**: durante o `apply_mounts`, o `PrivateTmp` é montado em
`/run/systemd/unit-root/tmp` — o `/tmp` **real** continua intacto — e a origem
`/tmp/opt-wiki-agent-heavy.lock` é resolvida contra esse `/tmp` real. O inode do host
entra. Só no fim (`mount_move_root`) a árvore temporária vira `/`.

Dois detalhes que também ficam provados pela mesma leitura:

- **ordem**: `mount_path_compare` (664-683) ordena "prefixes first" e
  `drop_unused_mounts` (1738) faz `typesafe_qsort` — logo `<root>/tmp` é aplicado
  antes de `<root>/tmp/opt-wiki-agent-heavy.lock`, que é o necessário para o destino
  ter pai.
- **destino criado sozinho**: 1517-1534 — em `-ENOENT` com `make`, o systemd chama
  `mkdir_parents` + `make_mount_point_inode_from_path` e refaz o mount. O arquivo
  destino dentro do /tmp privado (vazio) é criado pelo próprio systemd.

#### Duas condições obrigatórias que a rota 1 traz junto (e que derrubariam o cérebro)

1. **O prefixo `-` não é opcional.** **MEDIDO**: `/usr/lib/tmpfiles.d/tmp.conf` traz
   `D /tmp 1777 root root -` — `/tmp` é **esvaziado no boot**. Se a unit subir antes
   de qualquer ferramenta criar o lock, a origem não existe e, sem `-`,
   `apply_one_mount` devolve erro (1536, `"Failed to mount %s to %s"`), o exec falha
   com 226/NAMESPACE e — pela Lacuna C — vira **laço de reinício eterno e mudo**.
   Forma correta: `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock`.
2. **Só o `-` reintroduz a mentira em silêncio**: origem ausente ⇒ bind ignorado ⇒
   /tmp privado vazio ⇒ a guarda volta a dizer "livre" sempre, sem erro nenhum. O
   fecho é garantir a existência do arquivo antes da unit: um snippet
   `tmpfiles.d` (`f /tmp/opt-wiki-agent-heavy.lock 0666 rafael rafael -`) — e a
   ordenação já é garantida, porque **MEDIDO** no `man systemd.exec`, `PrivateTmp=`
   "adds ... an implicitly `After=` ordering on `systemd-tmpfiles-setup.service`".

#### `O_CREATE` é a única razão da mentira? NÃO.

`internal/cerebro/carga_linux.go:19` — `os.OpenFile(caminho, os.O_CREATE|os.O_RDWR, 0o666)`.

- Tirar o `O_CREATE` **sozinho não resolve**: dentro do /tmp privado o arquivo não
  existe, o open devolve `ENOENT`, "ENOENT = livre" e a guarda continua respondendo
  **sempre "não tomado"** — mesmo veredito errado, só sem o arquivo fantasma. O
  namespace precisa ser religado de qualquer forma. **DERIVADO** (leitura do arquivo
  inteiro + inodes medidos: host `39454263` × daemon `39739472`).
- Com `BindReadOnlyPaths` o mount é read-only e `O_RDWR` falharia com `EROFS`. Logo a
  mudança de código é **obrigatória**, e a correta é `O_RDONLY` sem `O_CREATE`,
  tratando `ENOENT` como livre: **MEDIDO** em `man 2 flock` desta máquina — "A shared
  or exclusive lock can be placed on a file regardless of the mode in which the file
  was opened" —, então `LOCK_EX|LOCK_NB` sobre fd `O_RDONLY` continua sendo a mesma
  prova que `flock -n` faz.

#### Ressalva residual (não bloqueia, mas tem de ficar escrita)

O bind **fixa o inode no start da unit**. Se alguém apagar e recriar o lock do host
(`rm` + `flock`), o daemon segue medindo o inode morto **sem erro nenhum** — a mesma
classe de mentira, com outra causa. Mitigação barata: logar `st_dev:st_ino` do lock
no boot do cérebro, e nunca apagar o lock (as ferramentas usam `flock`, que não
apaga).

#### Se ainda assim quiser a prova empírica (teste mínimo, fora do modo leitura)

```bash
stat -c %i /tmp/opt-wiki-agent-heavy.lock                      # inode do host
systemd-run --user --unit=prova-bind-tmp --wait --collect \
  -p PrivateUsers=yes -p PrivateTmp=true \
  -p BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock \
  /usr/bin/stat -c %i /tmp/opt-wiki-agent-heavy.lock           # inode dentro
```
Inode igual = bind sobreviveu. `PrivateUsers=yes` é necessário no gerenciador de
usuário: **MEDIDO** no `man systemd.exec`, `PrivateTmp=` "is only available for system
services, or for services running in per-user instances of the service manager when
`PrivateUsers=` is enabled". É exatamente o método que este repositório já usou em
2026-09-05 (docstring de `tools/check-units-alarme`: "Medido no gerenciador de usuario
deste mesmo systemd 252, com units volateis descartadas depois").

---

## LACUNA B — desde quando a coleta do STJ falha

### Veredito: 7 falhas datadas, de 7 disparos esperados, 2026-09-09 a 2026-09-15. Último sucesso observado por instrumento: 2026-09-10T07:32:07Z.

| afirmação | número | fonte | marca |
|---|---|---|---|
| falhas datadas | **7** (09-09, 09-10, 09-11, 09-12, 09-13, 09-14, 09-15, uma por dia) | `data/ops/owner_alerts.jsonl`, chave `unit-falhou-wikijuridica-stj-acordaos-coleta`, campo `alertado_em` | MEDIDO |
| disparos esperados | **7** (timer habilitado em 2026-09-08 14:05:16; `OnCalendar=*-*-* 09:40` + `RandomizedDelaySec=20min`, `Persistent=true`) | ctime do symlink `timers.target.wants/…timer`; arquivo `.timer` | MEDIDO |
| último disparo | 2026-09-15 09:58:12 -03 | `LastTriggerUSec`; stamp `/var/lib/systemd/timers/stamp-…` (mtime idêntico) | MEDIDO |
| última gravação de dado | **2026-09-10 09:52:51 -03** (mtime **e** ctime iguais em `cursor.json` e `manifest.jsonl`; o campo `atualizado_em` do cursor diz `2026-09-10T12:52:51Z`, o mesmo instante) | `stat` + leitura do cursor | MEDIDO |
| último sucesso observado | **2026-09-10T07:32:07Z** (04:32 -03) | linha de reconciliação em `owner_alerts.jsonl`: `"fechado por reconciliacao com a serie viva: Result=success ActiveState=inactive"` | MEDIDO |
| estado agora | `Result=exit-code`, `ExecMainStatus=1`, `ActiveState=failed`, run de 09-15 09:58:12→09:59:17 | `systemctl show` | MEDIDO |

### A premissa "cada commit é uma coleta bem-sucedida" é FALSA — e corrigi-la muda a resposta

O último commit que tocou `data/corpus/jurisprudencia/stj-espelhos/` é **`ea559b13`,
2026-09-10 10:18:19 -03**. Ele carrega os artefatos de **09-10 09:52:51**, que são a
saída **parcial de um run que FALHOU**: o alerta daquele dia está em
`2026-09-10T12:53:02Z` = **09:53:02 -03**, onze segundos depois da última gravação.
O coletor grava por desenho — o comentário da própria unit diz "grava o cursor **A
CADA LOTE**". **Logo data de commit ≠ data de sucesso**, e datar sucesso por commit
teria devolvido 09-10 10:18 como "último sucesso", que é falso. (MEDIDO: `git log` do
path, `stat`, e os dois timestamps do ledger.)

### Causa raiz, medida (e por que é a mesma todo dia)

Só o run de 09-15 é visível no journal — **MEDIDO**: `journalctl --list-boots`
devolve **um único boot** (desde 2026-09-14 22:26), com `Storage=persistent` e 86,8 MB
em uso; é rotação, não ausência de persistência. Nesse run:

```
collect-stj-acordaos: dataset espelhos-de-acordaos-segunda-secao competencia 20240229:
stjacordaos: decodificando o arquivo mensal de espelhos: invalid character '}' after array element
systemd[1]: Main process exited, code=exited, status=1/FAILURE
```

**MEDIDO** para 09-15. **DERIVADO** para 09-09…09-14: é falha determinística de parse
de **um** arquivo mensal; o cursor está congelado em `2026-09-10T12:52:51Z` com 4
datasets e **sem** entrada para essa competência, então nada avança além dela e o
disparo seguinte reencontra o mesmo arquivo. A cadência de um alerta por dia, com a
mesma chave, casa com isso.

### O achado que vale mais que a data

**Não existe ledger de execução desta coleta.** O único rastro persistente e datável é
`owner_alerts.jsonl`, e ele **só registra falha** (com cooldown de 1800 s). Sucesso não
deixa linha datada em lugar nenhum — foi por isso que o "último sucesso" teve de sair
de uma **mensagem de reconciliação**, e não de uma medição direta. Isso é defeito de
instrumento, não detalhe: fecha-se com um JSONL por execução (início, fim, exit,
datasets tocados, registros novos), que é o que torna a pergunta desta lacuna
respondível em um `grep`.

---

## LACUNA C — o alerta do cérebro pode disparar?

### Veredito: CONFIRMADO. O `OnFailure=` da unit do cérebro não tem caminho para disparar — e o repositório já mediu essa classe, sem saber que o cérebro caía nela.

**MEDIDO** (`systemctl show wikijuridica-cerebro`): `Restart=always`, `RestartUSec=15s`,
`StartLimitIntervalUSec=10s`, `StartLimitBurst=5`, `WatchdogUSec=0`, `NRestarts=1`,
`ActiveState=active` desde 2026-09-14 04:40:57.

1. **Os 10 s / 5 não são declarados: são o default do manager.** **MEDIDO** — o
   arquivo da unit (`ops/systemd/wikijuridica-cerebro.service`, que é o mesmo do
   `/etc/systemd/system` por **symlink**, conferido `IDENTICOS`) não tem nenhuma
   diretiva `StartLimit*`; `systemctl show` do manager devolve
   `DefaultStartLimitIntervalUSec=10s` e `DefaultStartLimitBurst=5`.
2. **O limitador é inalcançável, e a pergunta sobre o reset do contador nem precisa de
   resposta.** **MEDIDO** no `man systemd.unit` desta máquina: "Units which are started
   more than *burst* times **within an interval time span** are not permitted to start
   any more." Com `RestartSec=15s`, **nenhuma janela de 10 s contém duas partidas** —
   qualquer que seja a semântica de reset, 5 partidas em 10 s é impossível. DERIVADO
   (doc + aritmética). O `RestartSec` é a espera **entre a saída do processo e a
   próxima partida**, então a distância mínima entre partidas contadas é 15 s + tempo
   de execução.
3. **`OnFailure` só existe a partir de `failed`.** **MEDIDO** no `man systemd.unit`:
   "OnFailure= — ... units that are activated when this unit enters the **'failed'**
   state." Não há caminho documentado de disparo sem `failed`.
4. **Os caminhos alternativos de `failed` estão fechados para esta unit** — e aqui o
   repositório já tem a medição, feita neste mesmo systemd 252 em units voláteis do
   gerenciador de usuário, na docstring de `tools/check-units-alarme` (linhas 84-106):
   - **(A)** `Restart=always` com limitador desarmado + `ExecStart` falhando em laço →
     `activating/auto-restart`, `NRestarts` subindo, **OnFailure NÃO dispara**
     (confirmado em produção: a rede social acumulou **87 restarts** sem sair de
     `activating`);
   - **(C)** falha de dependência por `Requires=` → **dispara**. **Fechado aqui**: o
     cérebro declara `Wants=ollama.service`, não `Requires=` (MEDIDO no arquivo);
   - **(D)** `.socket` sem bind → **dispara**. **Fechado aqui**: o cérebro não tem
     socket.
   Sobra só a classe (A). **Conclusão do usuário confirmada.**
5. **O que é novo para o repositório**: o `check-units-alarme` descreve a classe (A)
   como "`Restart=always` + `StartLimitIntervalSec=0`". O cérebro chega **ao mesmo
   lugar sem declarar nada** — `RestartSec=15` > intervalo default de 10 s produz um
   limitador igualmente inalcançável. Quem ler a unit à procura de `StartLimitIntervalSec=0`
   não vê o problema.
6. **E ninguém mais está olhando.** **MEDIDO**: `tools/check-units-alarme` isenta
   estruturalmente quem tem `Restart=` (classe DAEMON), então não cobra nada do
   cérebro; e o detector que salva a classe (A) — a derivada de `NRestarts` em
   `tools/check-portal-health` — cobre **só** `wikijuridica-server.service`,
   `wikijuridica-server.socket` e `SERVICO_SOCIAL = "wikijuridica-social"` (grep do
   arquivo). **O cérebro não tem detector nenhum.**

### O achado dependente se sustenta

**MEDIDO**: `cmd/cerebro/main.go:157-160` devolve erro se o Ollama não responder
(`cliente.Versao(ctx)`), antes de carregar acervo e fila; `main` sai com
`os.Exit(1)` (linha 81). Somando: exit 1 no boot + `Restart=always` + limitador
inalcançável + `WatchdogUSec=0` + `OnFailure` que não pode disparar + nenhum detector
de `NRestarts` para esta unit ⇒ **"Ollama fora do ar no boot do cérebro = laço de
reinício eterno e mudo" está correto**. Precisão útil: o laço é de ~4 partidas por
minuto (uma a cada 15 s), e o único canal que registra é o journal — que, **MEDIDO**
nesta máquina, guarda apenas o boot corrente. E `WatchdogUSec=0` acrescenta a metade
que ninguém citou: worker **travado** (não morto) também é invisível.

---

## Plano de correção (para a sessão que puder escrever)

Ordem importa: o item 1 sem o item 2 troca uma mentira silenciosa por um laço de boot.

1. **Código** — `internal/cerebro/carga_linux.go`: abrir `O_RDONLY` sem `O_CREATE`;
   `ENOENT` ⇒ livre; manter `LOCK_EX|LOCK_NB` + `LOCK_UN`. Teste de regressão: com o
   arquivo ausente a guarda devolve livre sem criar nada (hoje ela cria); com o
   arquivo travado por outro processo devolve tomado. Prova por mutação: reintroduzir
   `O_CREATE` tem de deixar o teste vermelho.
2. **tmpfiles** — snippet versionado em `ops/` criando
   `f /tmp/opt-wiki-agent-heavy.lock 0666 rafael rafael -`, para o arquivo existir
   depois do esvaziamento de `/tmp` no boot. A ordenação vem de graça pelo
   `After=systemd-tmpfiles-setup.service` implícito do `PrivateTmp=`.
3. **Unit do cérebro** — `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock`,
   **mantendo** `PrivateTmp=true`, com o comentário do porquê (fonte primária,
   `namespace.c` 2142-2151 e 1448-1452) ao lado. Verificação pós-swap, sem adivinhar:
   `stat -c %i` do host × `/proc/<MainPID>/root/tmp/opt-wiki-agent-heavy.lock` — hoje
   `39454263` × `39739472`; tem de virar o mesmo número.
4. **Detector do cérebro** — estender a derivada de `NRestarts` de
   `tools/check-portal-health` à `wikijuridica-cerebro.service` (o código já existe
   para duas units) e registrar na unit que o `OnFailure` ali é decorativo para a
   classe (A). Sem isso, a Lacuna C continua aberta na prática mesmo com A e B
   resolvidas.
5. **Coleta STJ** — (a) tratar o arquivo mensal ilegível como recurso descartado com
   linha de descarte contada, em vez de exit 1 que congela o cursor (a fonte publica
   JSON inválido; abortar a coleta inteira por um mês defeituoso é fragilidade nossa);
   (b) criar o ledger JSONL por execução, que é o que faltou para responder esta
   lacuna sem inferência.
