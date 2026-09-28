# REFUTAÇÃO ADVERSARIAL — RUNBOOK P9 / P10 / P12
Tudo abaixo foi medido no /opt/wiki de 2026-09-15, em PLAN MODE (somente leitura).

## VEREDITO: OPERAVEL_COM_EMENDA — com 7 ataques que quebram ou perdem dado, e 1 que inunda o dono

---

## A. QUEBRA / PERDE DADO

### A1. B2 estranha tarefas em `executando` PARA SEMPRE (o mais grave)
`Reivindicar` incrementa `tentativas` **no claim**: fila.go:409
`UPDATE tarefa SET estado='executando', worker=?, iniciada_em=?, tentativas=tentativas+1`.
B2 manda "`ErrPausado` **sem** `Falhar` e **sem** incrementar `tentativas`". Duas falhas:
1. o incremento já aconteceu antes do executor rodar — "não incrementar" é impossível nesse ponto;
2. sem `Falhar`, as ≤3 linhas do lote ficam `estado='executando'`. O **único** caminho
   `executando → pendente` é `Fila.Recuperar` (fila.go:466-472), chamado só no boot
   (cmd/cerebro/main.go:174) — e B1+B3 existem justamente para o daemon **não** reiniciar.
   `Reivindicar` só lê `estado='pendente'` (fila.go:379-381, :390-392).
   `A12 reabrir` não alcança: `Reabrir` toca só `estado='erro'` (fila.go:482-484).
**Emenda:** instrumento novo `Fila.Devolver(ctx, ids []int64)` —
`UPDATE tarefa SET estado='pendente', worker='', tentativas=MAX(tentativas-1,0), disponivel_em=? WHERE id IN (…) AND estado='executando'` — no ramo de transporte, com teste.
E o DEPOIS de C-a passa a exigir `executando = 0` e `pendente` de volta ao valor de antes,
não "contagem por estado inalterada" (que hoje esconde exatamente essa fuga).

### A2. C-a não prova o portão de E3; C-b prova
§2 fixa "B2+B3+prova C-a verde antes de qualquer passo de E3". Mas o modo de falha de E3 é
**ollama de pé, `generate` falhando** (runner CUDA ruim), e nesse caso `Saude.Verifica` passa:
ela só chama `Cliente.Versao` e `Residentes` (saude.go:120-141). `kill -9` no ollama é a falha
que a guarda **já trata hoje** — pausa em ≤60 s sem B2 e sem B3. C-a fica verde dos dois lados.
**Emenda:** o portão de E3 é **C-b** (modelo ausente / `generate` falhando com `/api/version` 200).

### A3. C-b: o número esperado é inalcançável e a prova passa dos dois lados
`Falhar` só marca `erro` quando `tentativas >= maxTentativas` (fila.go:455; flag `--tentativas 3`),
e o backoff é linear `backoff × tentativas` com `--backoff 5m` (fila.go:459):
1ª falha → `disponivel_em` +5 min; 2ª → +10 min; a 3ª (a que vira `erro`) só é alcançável em
**≥15 min**. Logo, em 10 min `estado='erro'` cresce **0** — com B3, sem B3, com B4 e sem B4.
"≤9 se só o B3 pegar / 0 se o B4 pegar" são indistinguíveis.
**Emenda:** janela >15 min, ou unit volátil com `--backoff 5s --tentativas 1`; e o observável
passa a ser `tentativas` e `estado`, não o crescimento de `erro`.

### A4. C-e não prova B8 — a unit volátil não herda o StartLimit
B8 edita `ops/systemd/wikijuridica-cerebro.service`. O molde
`systemd-run --unit=cerebro-prova -p Restart=always -p RestartSec=15` cria unit **transiente**
com o StartLimit do MANAGER (medido: `StartLimitIntervalUSec=10s`, `StartLimitBurst=5`):
com RestartSec=15 nenhuma janela de 10 s tem duas partidas ⇒ burst inalcançável ⇒
`activating/auto-restart` eterno, zero alerta — **o baseline de hoje**.
**Emenda:** o molde ganha `-p StartLimitIntervalSec=300 -p StartLimitBurst=5`, e o primeiro
DEPOIS de C-e é `systemctl show cerebro-prova -p StartLimitIntervalUSec` = `5min`
(propriedade de [Unit] em unit transiente: conferir, não supor).

### A5. C-d: `failed` por watchdog **nunca** acontece com o StartLimit do B8
Um timeout de watchdog custa `WatchdogSec` (1500 s) + escalonamento SIGABRT→SIGKILL limitado por
`TimeoutStopSec=240` (unit, medido) = **até 1.740 s (29 min) por ocorrência** — e um processo em
`SIGSTOP` não atende SIGABRT, então a escalada é a regra, não a exceção. `failed` exige 5 partidas
dentro de `StartLimitIntervalSec=300`; cinco watchdogs levam ~2 h 6 min. Resultado: worker
congelado vira **restart em laço sem alerta** — o precedente dos 87 restarts da rede social,
reencenado na unit nova.
**Emenda:** (i) o DEPOIS de C-d é "restart, `NRestarts` +1, em ≤29 min", nunca `failed`;
(ii) o canal de alerta do congelamento é A5 (batimento, ≤1.236 s) + A8 (`cerebro_nrestarts_delta`),
escrito como tal; (iii) se se quiser `failed` pela via do systemd, `StartLimitBurst=2` ou
`StartLimitIntervalSec` ≥ 5×(WatchdogSec+RestartSec+TimeoutStopSec).

### A6. C-f é falso-positivo por construção
C-f está na lista das provas que rodam em unit **volátil**, e o molde não tem `PrivateTmp=true`.
Sem PrivateTmp o worker volátil vê o /tmp do host e o lock é o **mesmo inode** — hoje, com
B5/B6/B7 **não** aplicados. A prova fica verde contra o defeito intacto.
Medido hoje: host `inode=39454263 rafael 644`; daemon (`nsenter -t 926445 -m`) `inode=39739472`;
`mnt:[4026531841]` × `mnt:[4026532461]`.
**Emenda:** C-f roda contra a unit de **produção** depois de B7 (DEPOIS = o par `stat`/`nsenter`
com inode igual), ou o molde ganha `-p PrivateTmp=true -p 'BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock'`.

### A7. Depois de B5+B7 a guarda do flock volta a ficar MUDA sem nada acusar
Com `ENOENT ⇒ (false,nil)` (B5) e o prefixo `-` de `BindReadOnlyPaths` (B7), basta o arquivo não
existir no host no instante do start para o bind ser **pulado em silêncio** e o daemon voltar ao
estado de hoje. C-f é pontual; nenhum passo detecta a recaída.
**Emenda:** o batimento (A4) grava `lock_pesado_inode` (um `stat`, custo zero) e o gate A5 reprova
quando ele é 0 ou diverge do inode do host — é a única forma de a guarda deixar de ser "guarda pela metade".

---

## B. ORDEM

### B1. A ordem deixa `binario-vs-fonte` vermelho — e ele **já está vermelho hoje**
`tools/deploy-cerebro` exige `vcs.revision == HEAD` e termina chamando
`./tools/check-binario-vs-fonte` sob `set -euo pipefail`. O runbook deploya dentro do bloco B e
commita no FIM ("ORDEM DE COMMIT"): depois do commit final o HEAD anda, `bin/cerebro` declara o
pai e o gate fica vermelho.
Medido em `data/ops/qualidade_diaria.jsonl` (2026-09-15): `binario-vs-fonte` já é um dos 12 vermelhos.
**Emenda:** o **último** comando do bloco B é `./tools/deploy-cerebro`, **depois** do commit; e cada
deploy intermediário vem depois de um commit — senão o gate final do script reprova e o operador
lê isso como "deploy falhou".

### B2. Duas edições da unit são inevitáveis; o runbook manda uma só
B10 diz "corrigir na mesma edição de B7/B8/B9", mas B7 depende de B5 (Go ⇒ build+deploy) e
B9(ii) depende de B9(i) (Go ⇒ outro deploy).
**Emenda (ordem única e segura):** B1,B2,B3,B4,B5,B9(i) → commit → `deploy-cerebro` → B6 (tmpfiles)
→ **UMA** edição da unit com B7+B8+B9(ii)+B10 → `daemon-reload` → `restart`.
Antecipar B9(i) é grátis: sem `NOTIFY_SOCKET`, `notifica` devolve `(false,nil)`
(internal/sdactivation/sdactivation.go:205-207), então `NotificaPronto()` com `Type=simple` é no-op.

### B3. A ordem A(1-13) → B(14-23) põe o gate A5 no ar antes de o produtor existir
A4 é código Go: só escreve depois de build+deploy, que só acontece no bloco B. Registrado em
`var Names` (internal/checks/checks.go:298+), o gate `cerebro-batimento` entra na varredura da
bancada e, com falha **fechada** por desenho, reprova "morto" — somando um 13º vermelho aos 12
medidos hoje.
**Emenda:** gate e batimento no MESMO commit, registrados só depois do `deploy-cerebro` que põe o
produtor no ar; ou o gate nasce com a carência que `check-csp-style-hashes` tem ("falta deploy,
não é defeito").

---

## C. O DISCRIMINADOR DO BLOCO D ESTÁ ERRADO — e é ele que evita inundar o dono

### C1. `grep notify-owner` mede a coisa ao lado; 3 das 4 "silenciosas" têm escalada escrita
- `tools/run-qualidade-diaria:299-300`: *"Este exit 1 NAO alerta o dono: a unit declara
  SuccessExitStatus=1, entao o OnFailure so dispara em exit 2 (o runner nao conseguiu rodar).
  Verificado em 2026-09-05"*.
- `ops/systemd/wikijuridica-corpus-oraculo-recoleta.service:41-43`: *"Exit 1 = o gate do corpus
  ficou vermelho, que e o PRODUTO desta unit … Exit 2 = algum canal oficial falhou na coleta e
  ISSO chega ao dono. Crash/timeout tambem."*
- `ops/systemd/wikijuridica-fontes-alcancaveis.service:26`: *"SuccessExitStatus=1: o gate REPROVA
  quando ha fonte morta, e isso e o veredito"*.
Logo o "exit 1 nomeando exatamente 4 units" **não é baseline de A6: é o erro do instrumento**.
**Emenda do discriminador:** *a máscara é legítima quando existe um exit NÃO mascarado que alcança
`OnFailure` e o código o emite* — verificável por grep (`exit 2` no ExecStart + ausência do 2 na
máscara). Sob essa régua as 4 saem da lista, e D2/D3 ficam sem alvo até haver um caso real.

### C2. D3 dispara alerta DIÁRIO — medido, não hipotético
`data/ops/qualidade_diaria.jsonl`, 2026-09-15: `vermelhos = "py:test_check_internal_link_block.py
py:test_check_jsonld_cobertura.py py:test_deploy_lock_heartbeat.py
py:test_generate_nginx_bot_operators.py py:test_start_ai_terminal.py sh:test_deploy_publico_purga_api
sh:test_vigilia sca-osv gates-rotativos source-snapshot-corpus descoberta-do-bing binario-vs-fonte"`
— **12 gates vermelhos**; a passada anterior do mesmo dia trouxe `suite-completa producao-saudavel`.
Trocar `SuccessExitStatus=1` por `=0 4` em `qualidade-diaria` e `qualidade-longa` põe **as duas** em
`failed` na próxima passada (04:47 -03) e dispara `wikijuridica-alerta@` todo dia até os 12 ficarem
verdes. É a enxurrada que o bloco D existe para evitar.

### C3. D2 ignora o TERCEIRO significado do exit 1
`run-qualidade-diaria` tem dois caminhos distintos de exit 1: `vermelhos` (:288) e `nao_medidos`
(:312 — relógio/exit 124 e infra ausente/exit 75), e o comentário de :309-310 diz textualmente
*"Transformar `infra` em alerta diario seria a mordaca que test_notify_owner_mordaca.sh existe
para travar"*. A partição 4=nível / 1=regressão não tem casa para `nao_medidos`.
**Emenda:** três códigos, não dois — 4 = nível conhecido, 75 (o que o repo já usa para
EX_TEMPFAIL) = não medido, 1 = regressão nova; e `run-qualidade-diaria` **sai do piloto**: ele é a
bancada e já tem a partição correta. Sobra `check-fontes-alcancaveis`, que é o caso legítimo.

---

## D. NÚMEROS, COMANDOS E ÂNCORAS

- **A2 falha na 1ª execução como está escrito.** `Abrir` (fila.go:290-305) executa `EsquemaSQL`,
  `sqlitepool.Aplica` (PRAGMAs) e `registraVersaoSeVazio` — três escritas — antes de qualquer
  leitura. `file:…?mode=ro` devolve `attempt to write a readonly database` no primeiro
  `ExecContext`. O conserto está no "SE NÃO VIER"; tem de estar na AÇÃO (caminho de leitura que
  **não** chama `Abrir`, ou `Abrir` com `SomenteLeitura` pulando esquema/migração/carimbo).
- **C-g: a mensagem esperada não é a do código.** O formato real (saude.go:142-143) termina em
  `" (incidente de 2026-09-08 12:04:53, CLAUDE.md §12): %s"`, e o Go imprime **ponto** decimal
  ("3.01"), não "3,01". Ancorar em `acima do teto de 0.00 GiB`.
- **C-c: `NRestarts 1 → 2` é literal frágil.** C-a e C-b param e sobem a unit de produção antes de
  C-c, e o start manual zera o contador. Capturar `NRestarts` imediatamente antes e exigir delta +1.
- **A cópia da fila não tem método.** `data/ai/fila.sqlite` é WAL; `cp` só do arquivo principal
  perde as frames do `-wal`. Cópia ruim ⇒ `Abrir` falha ⇒ volátil em laço de restart ⇒ e, por A4,
  **sem alerta nenhum**. Usar `VACUUM INTO` (ou os três arquivos com o worker parado) +
  `PRAGMA integrity_check` antes de subir.
- **`sqlite3` contradiz a própria REGRA 1.** As DEPOIS de C-b e C-e usam o CLI, que nesta máquina
  só existe em `/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3` (medido, `which`).
  As consultas das provas devem ir por `cerebro status --somente-leitura` (A2).
- **Âncoras que não batem** (o runbook as usa como endereço): `Fila.Contagens` está em **fila.go:516**
  (não :513); `Reivindicar` começa em **:367** (não :379); o laço por tarefa está em
  **extracao.go:343-344**.
- **A4 contra o precedente da máquina:** `data/ops/portal_health_state.json` **é rastreado**
  (`git ls-files`), e é reescrito a cada 2 min pelo vigia. Pôr o batimento no `.gitignore` é
  decisão contra o precedente — não quebra nada (`check-untracked-e-alertar` só alerta além de 24 h),
  mas tem de ser dita como escolha.

---

## E. EFEITO COLATERAL EM PRODUÇÃO QUE O RUNBOOK NÃO DECLARA

### E1. C-a / E3 / E4 degradam uma superfície §12, e C-a é declarada "segura"
`internal/httpserver/mcp_semantico.go:74` cria cliente Ollama e **:84** decide **no boot** se
`buscar_semantico` entra em `tools/list`: *"o Ollama … nao respondeu; buscar_semantico fica FORA de
tools/list neste processo"*. Então (i) durante o outage as chamadas de `buscar_semantico` falham —
isso é produto, não teste; e (ii) se algo reiniciar o `wikijuridica-server` dentro da janela, a
ferramenta **desaparece do canal de máquina até o próximo restart, sem alerta**. E o runbook cria
duas fontes de restart: `wikijuridica-server-reload.path:22` observa
`/opt/wiki/data/ai/embeddings/ativo.json`, e o ramo novo do `check-portal-health --repair` reinicia o Go.
**Emenda:** conferir `tools/list` por loopback antes e depois de C-a/E3/E4; e o ensaio de A10
**nunca** com `data/ai` apontando para o de produção — o executor grava `ativo.json` via `AposLote`
(cmd/cerebro/main.go:274-282) e dispararia o `.path`.

### E2. O ramo de reparo do B8 contamina a memória anti-laço do vigia
Em `tools/check-portal-health` o reparo é uma cadeia `if/elif` **exclusiva** (:454, :456, :476) sobre
UM par de campos — `reparo_ultimo` e `reparo_falhas_seguidas` (:452-453, persistidos em :607-610) —
e `LIMITE_REPAROS_IGUAIS = 3` (:101) compara o reparo de agora com o anterior. Um ramo novo de
`reset-failed`/`start` do cérebro escreveria nesses mesmos campos e apagaria a memória do reparo do
**portal** (que chega a `chown var/nginx` + `reload` e a reiniciar o Go). É a mesma classe do defeito
que A7 conserta.
**Emenda:** chaves próprias (`reparo_cerebro_ultimo`, `reparo_cerebro_em`,
`reparo_cerebro_falhas_seguidas`), ramo **fora** da cadeia exclusiva, teto de 1×/hora medido na chave nova.

### E3. Alerta de prova que ninguém consegue fechar
C-e conta com `OnFailure=wikijuridica-alerta@%N.service` na volátil. O template
(ops/systemd/wikijuridica-alerta@.service) chama `tools/notify-owner --chave "unit-falhou-%i"` e
grava em `data/ops/owner_alerts.jsonl` com `--evidencia "systemctl status cerebro-prova"` — e o
`--collect` já descartou a unit. Fica um alerta aberto sobre unit inexistente, que
`wikijuridica-alertas-abertos` (→ `generate-alertas-reconciliados`) passa a carregar.
**Emenda:** alvo/chave próprios com prefixo `prova-`, e a prova termina resolvendo a chave.

### E4. Um `stat` a menos e o batimento não sabe o que o runbook quer que ele saiba
A4 fixa **dois** call sites e proíbe um terceiro, mas o 1º é no topo de `Passo` — **antes** da
saúde (worker.go:61-70) — então `estado`/`pausa_motivo` ali são sempre o veredito do ciclo
**anterior** (cache de 60 s), e o 2º nunca é alcançado quando há pausa (`Passo` retorna em :69).
Na prática, o motivo da pausa chega ao `.json` só no ciclo seguinte (+30 s de `--ocioso`).
**Emenda:** ou um 3º ponto logo depois de o veredito ser calculado, ou o DEPOIS das provas aceita
a defasagem de um ciclo, declarada. E não ancorar prova em `journalctl`: `Roda` loga `"pausa: %v"`
**só na transição** (worker.go:162-166) — se o worker já estava pausado por outro motivo (carga,
lock), a linha esperada **nunca sai**, e C-a/C-b/C-f concluem falha onde houve sucesso.

---

## G. TRÊS ACHADOS DA CHAMADA AO ADVISOR, TODOS CONFERIDOS AQUI

### G1. A7 e A8 editam o vigia VIVO, e a unit dele mascara exit 1
O bloco A diz "nada muta produção". Falso para A7/A8: `ops/systemd/wikijuridica-watchdog.service:27`
tem `ExecStart=/opt/wiki/tools/check-portal-health --repair`, o timer é `OnUnitActiveSec=2min`
(wikijuridica-watchdog.timer:16) e a unit declara `SuccessExitStatus=0 1` (:30). Editar o arquivo
**é** o deploy. Um traceback de Python sai 1 ⇒ mascarado ⇒ o vigia do portal morre a cada 2 min com
`Result=success` e ninguém sabe. É o assunto do P10 escondendo o instrumento do P9.
**Emenda:** editar cópia, `python3 -m py_compile` + os harness (`test_portal_health_*.sh`), e trocar
por `mv` atômico; e A6 tem de classificar esta unit no censo (hoje ela tem `avisar_dono` no código,
então sob o discriminador emendado de C1 ela é legítima — mas tem de aparecer).

### G2. A10 (ensaio) é subespecificado, e a falha é laço de restart SEM alerta
`resolve()` confere **só** `content/pages.json` (cmd/cerebro/main.go:111-113), mas `servir` lê do
`--root`: `CarregaAcervo` (:161), `carregaPublicacaoConfig` (:194 → `content/cerebro_publicacao.json`,
publicacao.go:238), `content.LoadEditorialIdentity` (:198 → `content/site.json`, content.go:774),
`carregaPoliticaHabitualidade` (:202), `ArquivoLedgerPublicacoes` (:206) e
`cerebro.NovoExtrator(c.root, …)` (:251, que precisa do corpus do STJ). Ensaio incompleto **passa**
o `resolve()` e falha depois ⇒ `return err` ⇒ `os.Exit(1)` ⇒ volátil em laço ⇒ e, por A4/A5 acima,
**sem alerta nenhum**, com o operador esperando a linha de pausa que nunca vem.
**Emenda:** montar o ensaio por symlink somente-leitura de `content/` e `data/corpus/` com
`data/ai/` e `data/ops/` próprios; e o DEPOIS do A10 é `bin/cerebro status --root <ensaio>
--somente-leitura` saindo 0 **antes** de qualquer unit volátil subir.

### G3. O limiar de "pausa crônica" do A5 morde a pausa legítima que B5–B7 criam
A5 reprova `pausado` há mais de 4 prazos (~82 min). Depois de B5+B6+B7 a guarda do flock passa a
funcionar de verdade, e a bancada diária segura o mesmo lock por **60 min 42 s** (04:48:12→05:48:54,
número do próprio runbook), seguidos da drenagem de carga (`--carga-max 12` contra loadavg 15,84 do
próprio runbook). 82 min é 1,35× de 61 min: a primeira manhã depois de B7 tende a um vermelho
correto-mas-falso.
**Emenda:** isentar da regra crônica as pausas cujo `pausa_motivo` casa lock-pesado/carga, ou derivar
o limiar da janela medida da bancada com margem (≥2× 61 min).

## F. O QUE TENTEI DERRUBAR E NÃO CAIU (refutação falhada = verificação)

- **Flock mudo:** reproduzido. Host `39454263 rafael 644`; daemon `39739472`; `mnt:[4026531841]` ×
  `mnt:[4026532461]`. Diagnóstico P9 correto, e `carga_linux.go:18` é mesmo `os.O_CREATE|os.O_RDWR`.
  (`flock(LOCK_EX)` sobre fd `O_RDONLY` é legal — a emenda B5 não introduz bug aí.)
- **Censo do P10:** 22 diretivas `SuccessExitStatus` não comentadas em `ops/systemd/*.service` e
  exatamente **9** units com `ExecMainStatus=1` + `Result=success` (alertas-abertos,
  corpus-oraculo-recoleta, daily-content, daily-content-noticias, efeito-nos-bots,
  fontes-alcancaveis, qualidade-diaria, qualidade-longa, untracked-inventory); `edge-frescor` com
  `status=2 / Result=exit-code`. Confere.
- **A1:** `/api/ps` entrega `size_vram: 0` e `context_length: 8192` (e `digest`), e `Residente`
  (cliente.go:275-280) decodifica só `name/model/size/expires_at`. Confere.
- **Unit viva:** `Type=simple`, `WatchdogUSec=0`, `StartLimitIntervalUSec=10s`, `StartLimitBurst=5`,
  `RestartUSec=15s`, `TimeoutStartUSec=1min30s`, `PrivateTmp=yes`, `NRestarts=1`,
  `ExecMainStatus=0`, `NeedDaemonReload=no`; nenhuma das duas linhas de StartLimit está no arquivo.
  Confere, inclusive o "invisível ao grep".
- **Sem reatestação:** `go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` = 452
  pacotes, **nenhum** de `internal/cerebro|ollama|checks|sdactivation`. Confere.
- **`/tmp/opt-wiki-commit.lock` não existe** em `tools/ docs/ .githooks/ internal/ ops/`. Confere.
- **Exit 3 tomado** em `check-api-catalog-usage:483-506` ("catálogo remoto indisponível"). Confere.
- **Drop-in do Ollama:** `LLM_LIBRARY=cpu`, `FLASH_ATTENTION=1`, `CONTEXT_LENGTH=8192`,
  `MAX_LOADED_MODELS=2`, `MemoryMax=12G`, instalado por **symlink**; `check-units-instaladas:72`
  tem `DIR_UNITS = ops/systemd` e nada mais — a lacuna de E8 é real. Confere.
- **SIGTERM não vira exit 1** (tentei provar que todo restart marcaria falha e não marca):
  `cmd/cerebro/main.go:284-288` faz `if err != nil && ctx.Err() != nil { return nil }`.
- **Todos os comandos e símbolos citados existem:** `check-load-headroom --max`,
  `generate-coord-message`, `check-units-alarme` (com as regras R-A…R-E, e R-E exigindo comentário
  adjacente em [Service]), `check-units-instaladas`, `test_units_alarme.sh`,
  `test_portal_health_reparo_unit_ausente.sh`, `deploy-cerebro`, `notify-owner`;
  `cerebro servir` tem `--root --fila --worker --max-lote --ocioso --saude-a-cada --saude-prazo
  --lock-pesado --carga-max`; `URNDaCitacaoPublica` em extracao.go:672;
  `medir-prompt-sumula-pareado` já usa `Temperatura` 0, `Think`, `NumPredict: 512`,
  `PenalidadeDePresenca: 0` (main.go:165-170) — só não são flags, então a instrução "rodar com
  esses parâmetros" se cumpre por leitura do código, não por linha de comando.
- **SEM dano de SEO e SEM risco de CSP:** nenhum passo de P9/P10/P12 toca `public/`,
  `style-src`, hash do script inline, sitemap, `lastmod`, `--ressemear` ou purga de borda.
  `wikijuridica-server.service:54` tem `Requires=wikijuridica-server.socket` e **não** ollama, então
  reiniciar o Ollama (E3/E4) não reinicia o servidor nem o coloca em laço.
- **Nenhuma decisão devolvida ao dono; nenhuma espera de horas sem atalho.** As esperas declaradas
  (vazão do modelo, TTL, ciclo de timer) vêm com número e atalho.
- **Rollback:** todos são "para frente" (edição + `daemon-reload` + `restart`), sem
  `git reset/checkout/stash/revert`. O de B6 está certo: remover o symlink não apaga o arquivo já
  criado em /tmp, e isso é inócuo (`tmp.conf` tem `D /tmp … -`, sem idade, logo
  `systemd-tmpfiles-clean` não o remove).
