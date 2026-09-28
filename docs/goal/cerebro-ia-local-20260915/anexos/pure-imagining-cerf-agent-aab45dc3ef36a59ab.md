# Auditoria de `tools/run-daily-content` — os sete defeitos re-verificados + os novos

Medido em 2026-09-15 contra o código e o dado vivo. Modo somente leitura.
Todo número abaixo é medição própria; onde não medi, está escrito "NÃO MEDIDO" e o porquê.

## Correções aos números do enunciado

- **"35 execuções consecutivas sem verde"** → medido: a última linha `resultado: "ok"` é de **2026-08-26**; depois dela há **30 linhas** no ledger, todas `parcial`. O real é **≥ 30**, porque execução rejeitada pela trava não grava linha (defeito (a)).
- **"149 páginas em 26 dias"** → não reproduzi essa janela. O que medi: o manifesto foi de **11.039** `unique_intent_id` em `315ac61b` (2026-09-10) para **11.106** no disco hoje = **+67 em 5 dias**.
- **Teto declarado de 410/dia** → confere: 200+80+60+40+30 dos cinco geradores (`:368-374`).
- **"1.267 páginas de severidade média"** → medido **10.337**. Não achei de onde sai 1.267: os 3.201 intents da `v2_rewrite_queue` se repartem em 2.578 `medio`, 523 `limpo`, 100 `critico`.

---

## Ordenado por DANO REAL sendo causado hoje

| # | defeito | veredito | dano hoje |
|---|---|---|---|
| 1 | (f) estreia móvel — `generate-first-published-at` órfão | **CONFIRMADO, pior que o alegado** | 944 páginas servem `datePublished` errado HOJE; 942 com cronologia impossível |
| 2 | **N1** (novo) chaves de array com espaço (shfmt `d4c942f2`) | **CONFIRMADO** | ledger de coleta partiu identidade em 09-11; `check-frescor-canal-diario` cego desde então |
| 3 | **N2** (novo) `diarios-municipais` morto desde 2026-08-29 | **CONFIRMADO** | 1 dos 5 canais não produz; é a causa de 22/44 vermelhos |
| 4 | (b) `SuccessExitStatus=0 1` | **CONFIRMADO** | mascarando exit 1 AGORA (`Result=success`, `ExecMainStatus=1`) |
| 5 | (g) fila de refinamento | **CORRIGIDO-PARA** | fila sem consumidor; 10.337 médias publicadas sem refino |
| 6 | (c) `TimeoutStartSec` | **CORRIGIDO-PARA** | risco latente, mas sem handler de sinal no publicador |
| 7 | (a) `flock` antes do `trap` | **CONFIRMADO no código** | incidência NÃO MEDIDA (journal só retém o boot atual) |
| 8 | (d) `vereditoDe` cego a prefixo | **CORRIGIDO-PARA** | só o texto do alerta; o veredito não muda |
| 9 | (e) lock pesado | **CONFIRMADO (parcial)** | sobreposição de CPU, sem colisão de dado |

---

## (f) CONFIRMADO — e é muito pior que a alegação

- `tools/generate-first-published-at` é **órfão**: grep em `tools/ ops/ .githooks/ internal/ cmd/ docs/` devolve só ele mesmo e dois comentários (`internal/httpserver/api_novidades.go:86`, `cmd/publish-v2-direct/main.go:3558`). Nenhum runner, nenhuma unit.
- `data/editorial/first_published_at.json` congelado em **2026-08-28 17:26** (18 dias). Contém 10.107 chaves; `commits_percorridos: 31`.
- Manifesto tem **11.106** `unique_intent_id`. **999 ausentes** do ledger de estreia. O log da publicação de hoje confirma: `data de estreia : 10107 de 11106 páginas`.
- Mecanismo: `cmd/publish-v2-direct/main.go:3837` — `ApprovedAt: primeiroNaoVazio(page.PublicationDate, opts.publishedAt)`. Sem registro de estreia, cai em `opts.publishedAt` = `-published-at "$HOJE"` (`tools/run-daily-content:685`) = **hoje**.
- **A data se MOVE** (medido por `git show 315ac61b` de 2026-09-10 contra o disco): 900 intents tinham `approved_at=2026-09-10` e hoje têm `2026-09-15`.
- **População, não amostra**: dos 944 ausentes com `approved_at=2026-09-15`, li os **944** HTML servidos em `public/`. **944 de 944** trazem `datePublished = 2026-09-15`. **942 de 944** trazem `dateModified` ANTERIOR ao `datePublished`.
  - Exemplo: `public/jurisprudencia/stf-adi-4376/index.html` → `datePublished 2026-09-15`, `dateModified 2026-09-05`.
  - É exatamente a cronologia que `cmd/publish-v2-direct/main.go:485-492` declara impossível e manda não cometer.
- Canais afetados (944): `/jurisprudencia/` 875, `/leis/` 38, `/sumulas/` 29, `/noticias/` 2. Os 55 com data estável são `/noticias/` 30 e `/diarios/` 25 — canais que populam `publication_date` no próprio shard.
- **Segundo consumidor**: `internal/httpserver/api_novidades.go:293` faz `publicadoEm: estreias[registro.UniqueIntentID]` — lookup em mapa Go, chave ausente devolve `""`. As 999 saem com `publicado_em` VAZIO no canal de máquina (`:623`).
- Severidade honesta: o gerador reconstrói a estreia do histórico do git — o dado **é recuperável**. O dano é o artefato SERVIDO estar errado todo dia, não perda permanente.

## N1 (NOVO) CONFIRMADO — `shfmt` trocou a identidade das chaves

`d4c942f2` (2026-09-11, "108 scripts formatados pelo shfmt") reescreveu as chaves de array associativo:

- `tools/run-daily-content:336` → `[stj - precedentes]`, `[stf - informativo]`, `[normas - federais]`, `[diarios - municipais]`, `[noticias - oficiais]`
- `tools/run-daily-content:368` → `[stj - tema]`, `[stj - sumula]`, `[stf - informativo]`

`bash -n` passa (sintaxe válida); a semântica mudou em silêncio. Três consequências medidas:

1. **`--somente-noticias` roda ZERO coletas.** `:355` compara `[ "$chave" = "noticias-oficiais" ]` contra a chave real `noticias - oficiais` → `unset` em TODAS. Reproduzido em bash: `restantes: 0`. O script imprime "1 coleta, 1 gerador" e roda 0 coletas. (`:378` compara contra `noticias`, chave sem espaço — o gerador sobrevive.) **Dano pequeno, e é justo dizer**: `wikijuridica-noticias-coleta.timer` já coleta notícias 4×/dia (07:15, 11:50, 16:20, 21:50) sob o lock pesado, então o que se perde é a linha de log falsa, não a coleta.
2. **O ledger de coleta partiu a série em 2026-09-11.** `data/ops/daily_content_collect.jsonl`: as 5 chaves antigas param em `2026-09-10`; 5 chaves novas nascem em `2026-09-11`.
3. **`check-frescor-canal-diario` ficou cego.** `tools/check-frescor-canal-diario:65-85` tem `CANAIS` com `"fontes": ["diarios-municipais"]`, `["noticias-oficiais"]`, `["stj-precedentes","stf-informativo"]` — nomes ANTIGOS. `avalia_canal` (`:208-213`) faz `ledger_por_fonte.get(fonte, {})` e `ultimo_dia_da_fonte` devolve o último dia presente = **2026-09-10, congelado**. A saída do gate de hoje prova: cita `(2026-09-10)` para jurisprudência e súmulas, e reprova diários com a mensagem de 09-10 ("0 de 166 inéditas") enquanto o erro REAL de hoje é outro (TLS handshake failure). Os canais sazonais não podem mais reprovar.

Também nos logs: `data/ops/daily_content_logs/` tem os dois nomes (`stj-precedentes.log` de 09-10 e `stj - precedentes.log` de 09-15).

## N2 (NOVO) CONFIRMADO — `diarios-municipais` não ingere nada desde 2026-08-29

Do ledger de coleta (32 execuções somando as duas chaves): `ok=13`, `falha=19`. As outras 4 fontes: 0 falhas.
- 08-29 a 09-12: `0 de 166 coletada(s) inéditas (marca d'água 2026-08-29T04:19:51)`.
- 09-13: recuperou (`569 registros, 403 inéditas`).
- 09-14 e 09-15: `robots.txt de api.queridodiario.ok.org.br inalcançável: tls: handshake failure`.

É a causa dominante do vermelho: `check-frescor-canal-diario` reprovou 22 de 44 execuções e `coleta:diarios*` 22 de 44.

## (b) CONFIRMADO — com prova viva de hoje

`ops/systemd/wikijuridica-daily-content.service:55` → `SuccessExitStatus=0 1`, confirmado por `systemctl show`. E a execução de HOJE: `ExecMainStatus=1`, `Result=success`, `NRestarts=0`, `OnFailure=wikijuridica-alerta@wikijuridica-daily-content.service` **não disparou**.

Units do projeto com a mesma máscara (`0 1` ou `1` — 0 já é sucesso sempre, então as duas formas mascaram igual):
`daily-content:55`, `daily-content-noticias:34`, `edge-live:41`, `crawler-error-budget:60`, `efeito-nos-bots:28`, `tunnel-health:40`, `fontes-alcancaveis:29`, `network-health:60`, `edge-cache-coverage:48`, `edge-warm:80`, `watchdog:30`, `edge-frescor:48`, `alertas-abertos:64`, `qualidade-diaria:42`, `qualidade-longa:42`, `qualidade-race:28`, `untracked-inventory:19`, `brotli-cobertura:23`, `corpus-oraculo-recoleta:44`, `moderacao-transparencia:75` (`=75`).

Units que deliberadamente NÃO mascaram, com o motivo escrito: `ai-citation`, `websub-ping`, `crawl-coverage`, `bot-telemetry`, `edge-traffic`, `edge-bot-status`, `indexnow`, `cache-baseline`, `efeito-deploy`, `sitemap-shard-grace`, `source-evidence-recheck`, `bot-ipranges`.

## (c) CORRIGIDO-PARA — o 14.420 s não é medição, é a soma dos tetos

- `TimeoutStartSec=7200` confirmado (`systemctl show` → `TimeoutStartUSec=2h`).
- **Os 14.420 s são a soma dos 10 `timeout` declarados** (linhas 422, 456, 471, 572, 579, 641, 674, 684, 880, 893), expandindo os laços de 5 coletas e 5 geradores: 4500+600+4500+600+1800+1800+20+600 = **14.420**. Não é tempo medido.
- **Tempo REAL medido** (44 linhas do ledger, 27 com `escopo: completa`): mediana **802 s**, máximo **1.326 s**, mínimo 119 s. Nenhuma execução chegou perto de 7.200 s.
- **O comentário da unit está desatualizado**: afirma "as sete etapas com timeout proprio somam 5.700 s". São dez, e somam 14.420.
- **Pior: não existe soma finita.** **19 pontos de chamada** não têm `timeout` nenhum — `check-verified-repair`, `check-shard-preservation`, `check-untracked-product-inventory`, `check-onda-avanca` ×2, `check-v2-portfolio-pairing`, os **2 `git commit`** (cujo pre-commit compila Go), `generate-brotli-static`, os **7** gates do 8.7, `reload-wiki-server`, `check-edge-discovery-freshness`, `purge-edge-cache`. O teto declarado não pode cobrir o que não tem teto.
- Unit de notícias: `TimeoutStartUSec=40min` (2.400 s) contra soma declarada da mesma passada de ~7.220 s.
- **O risco de SIGTERM na transação é real e a recuperação é manual**: `grep -rn "signal.Notify|SIGTERM|os.Interrupt"` em `cmd/publish-v2-direct/` e `internal/publicrelease/` devolve **zero**. O publicador não trata sinal. O toolchain fixado ignora só `os.Interrupt` e `SIGQUIT` (`.toolchains/go1.26.6/src/cmd/go/internal/base/signal_unix.go`) — **SIGTERM não está na lista**. A unit usa `KillMode=control-group`, `KillSignal=15`: o SIGTERM alcança todo o cgroup. O snapshot existe (`data/ops/publish-rollback-20260915-152712`) mas o rollback é por `RESTORE.md`, à mão.
- A condição de boot abortado é real: `internal/publishedmanifest/publishedmanifest.go:215,300` emitem `published_manifest_sitemap_loc_without_manifest`.

**O conserto NÃO é aumentar o teto — e a medição diz por quê.** Atribuí os tempos da onda de hoje cruzando o journal (`04:24:45` → `04:42:10`, 1.045 s) com os carimbos `medido_em` do ledger de coleta:

| bloco | teto declarado | custo real medido | uso do teto |
|---|---|---|---|
| etapa 1 (as 5 coletas) | 4.500 s | **268 s** (todas terminaram às 07:29:13 UTC) | **6,0%** |
| etapas 1.5 a 9 (o resto) | 9.920 s | **777 s** | 7,8% |
| **onda inteira** | **14.420 s** | **1.045 s** | **7,2%** |

A repartição por bloco é **N=1** (a onda de hoje) — é o que o ledger de coleta permite atribuir. A afirmação "nenhum passo é lento" se apoia no N=27 das execuções completas: máximo **1.326 s**, 18% da janela. O teto de 900 s por coleta é ~17× o custo medido. Logo o defeito não é janela curta nem passo lento: é que **o orçamento declarado é ficção** — 14.420 s de tetos que ninguém encosta, contra uma janela de 7.200 s que ninguém alcança —, e o buraco real são os **16 passos sem teto nenhum**, onde um `git commit` que compile Go ou um `reload-wiki-server` pendurado roda para sempre sem que o teto de etapa perceba. O que precisa mudar é o teto por etapa descer ao que a medição mostra e os 16 passos sem teto ganharem um; `TimeoutStartSec` não se toca.

## (d) CORRIGIDO-PARA — perde o diagnóstico, não o veredito

`vereditoDe` (`:127-140`) resolve `log="$LOGS_COLETA/$1.log"`. Falha registrada como `coleta:diarios - municipais` procura `data/ops/daily_content_logs/coleta:diarios - municipais.log`, que não existe → imprime **"(sem log)"**.

Mas o veredito NÃO é afetado: `registra` (`:112`) empilha em `falhas` sem olhar prefixo, e `resultado` (`:171`) só testa `${#falhas[@]} -eq 0`. Verifiquei os dois consumidores do ledger: `tools/generate-alertas-reconciliados:160` lê `falhas` só por vacuidade; `tools/check-public-sem-lixo` não filtra por nome.

O defeito é mais amplo que `coleta:`: atinge **todos** os prefixos — `geracao:`, `writeback:`, `commit:` — e afeta só o corpo do `notify-owner`. Medido no ledger: `coleta:diarios-municipais` 18×, `coleta:diarios - municipais` 4×, `commit:portfolio` 4× — todas chegaram ao dono como "(sem log)".

## (e) CONFIRMADO parcialmente — e a premissa do lock de commit é falsa

- A onda toma **só** `/tmp/wiki-daily-content.lock` (`:70`, `:77-78`, `flock -n`).
- `/tmp/opt-wiki-agent-heavy.lock` é tomado, **bloqueante e sem timeout**, por: `qualidade-diaria.service:19`, `qualidade-longa.service:19`, `qualidade-race.service:25`, `noticias-coleta.service:22`, `corpus-oraculo-recoleta.service:40`, `official-source-url-inventory-refresh.service:41`. A onda **não** entra nessa fila.
- **`/tmp/opt-wiki-commit.lock` NÃO EXISTE no código.** Verifiquei eu mesmo: grep em `tools/ ops/ .githooks/ docs/ internal/ cmd/` só casa uma string de teste sem relação. A memória do projeto descreve intenção, não implementação. E o `.githooks/pre-commit` não toma flock nenhum.
- Sobreposição de relógio: onda 04:20 (+900 s de random, ~15-20 min de duração) × bancada 04:40 (+600 s, ~38 min). Sobreposição real de ~25 min na execução de hoje.
- **Sem colisão de dado**: a bancada escreve `data/ops/qualidade_diaria.jsonl` e `.agents/runtime/qualidade-diaria/`; a onda escreve `data/editorial/`, `public/`, `data/ops/daily_content_*`. Disjuntos. A disputa é CPU/I/O, não corrupção.
- Mas os **2 `git commit` da onda (`:615`, `:632`) disputam o índice do git** com qualquer sessão, sem lock nenhum.

**Veredito sobre "deveria tomar o heavy":** para os COMMITS, **não** — o contrato (§1) manda serializar sob heavy só commit que toca Go/`go.mod`/`go.sum`; os dois commits da onda são de dado (`portfolio_v2`, `v2_pages`) e o contrato os classifica como "leve — frequente e concorrente". A alegação de que a onda deveria pegar o heavy por causa dos commits está **REFUTADA**. O que de fato é pesado e roda fora do lock são as ~10 compilações `$GO run` das etapas 1 e 2 — que a unit afirma acontecerem num `ExecStartPre` inexistente (N10).

## (g) CORRIGIDO-PARA — dois arquivos foram confundidos

- `data/editorial/v2_rewrite_queue.jsonl`: **3.201 linhas, todas com `queued_at = 2026-09-11`**, mtime 2026-09-11 02:58. **Não** é 2026-09-04. Produtor: `internal/v2ingest/v2ingest.go:631,642` (`RewriteQueueRelPath`, `:34`), acionado por `cmd/ingest-v2-stock` sob demanda — **não está em runner nem em timer**.
- `data/ops/refinement_queue.jsonl`: **5 linhas**, última **2026-09-04**, mtime 2026-09-04 13:24. **Esta** é a que parou em 09-04.
- **Severidade média viva: 10.337**, não 1.267 (`data/editorial/v2_publication_severity.jsonl`, medido hoje). Todas as 10.337 estão PUBLICADAS. Causas: `batch_global_similarity_refutado_por_medicao` 5.600, `fonte_insuficiente` 2.323, `blocker_pipeline:anti_template` 2.089, `corpo_entre_250_e_400_palavras` 1.695.
- **Por que parou**: a onda só escreve a fila quando `grep -q 'achado MÉDIO'` no log da publicação (`:738`). O único produtor dessa string é `cmd/publish-v2-direct/qualitygate.go:101`, e o log de hoje diz `gate de qualidade : 11118 páginas, nenhum achado`.
- **Nenhuma das duas filas tem consumidor.** Nada lê `refinement_queue.jsonl` para refinar. `v2_rewrite_queue.jsonl` só é lido para reconciliação da própria ingestão (`internal/v2ingest/plan.go:294,454`).

## (a) CONFIRMADO no código, incidência NÃO MEDIDA

`:77-80` — `exec 9>"$TRAVA"` / `flock -n 9` / `exit 0`. O `trap gravaEvidencia EXIT` está em **`:280`**, 200 linhas depois. Execução rejeitada pela trava: sem linha no ledger, `exit 0`, systemd diz sucesso.

**Incidência NÃO MEDIDA**, e o motivo: `journalctl --list-boots` mostra **um único boot**, desde 2026-09-14 22:26 — não há retenção para 30 dias. Do lado do ledger não há dia faltando: 08-21 a 09-15, todos presentes, 2 linhas/dia desde 09-10. Não encontrei evidência de rejeição pela trava; também não posso descartá-la.

Cenário concreto em que morde: ambos os timers têm `Persistent=true`; depois de um reboot que coma as duas janelas, os dois disparam juntos no boot e um sai 0 em silêncio.

---

## Outros defeitos novos, no mesmo formato

**N3 — `registra_aviso` é no-op e o comentário mente.** `:47-51`. O comentário diz "anota no ledger"; o corpo só faz `printf >&2`. E o único chamador (`:546`) é `registra_aviso "untracked" 2>/dev/null || true` — stderr para `/dev/null`. O aviso não chega a lugar nenhum. (R1: comentário que mente é bug.)

**N4 — `git add` por DIRETÓRIO.** `:615` `git add data/editorial/portfolio_v2` e `:632` `git add data/editorial/v2_pages`. O contrato do repo manda caminho exato; o histórico registra 3 varreduras de trabalho de outra sessão. A onda roda sem ninguém olhando às 04:20.

**N5 — falha de escrita do ledger de coleta é engolida.** `:56` `python3 - ... 2>/dev/null || true`. Se `registra_coleta` falhar, some sem rastro — e é o ledger de que `check-frescor-canal-diario` depende.

**N6 — `check-untracked-product-inventory` com saída descartada.** `:546` `>/dev/null 2>&1`: a onda sabe que há produto untracked e não preserva O QUÊ.

**N7 — gate não-executável some em silêncio.** `:845` `if [[ -x "./tools/$gate" ]]` sem `else`. Um dos 7 gates que perca o bit de execução deixa de rodar sem uma linha de aviso.

**N8 — o modo `--seco` está MORTO desde 2026-09-09.** `:36-37` lê `--seco` e faz `SECO=1`. Mas o laço de argumentos de `:99-108`, acrescentado por `134f4184` (2026-09-09), itera `"$@"`, não conhece `--seco`, cai no `*)` e faz **`exit 2`**. Reproduzido em bash isolado: `SECO=1` / `argumento desconhecido: --seco` / `EXIT=2`. O `exit 2` é em `:105`, **antes do trap de `:280`** — então nem linha de evidência fica. O ensaio documentado no cabeçalho do próprio script (`:30`) não roda desde então. Consistente com o ledger: **0 de 44 linhas** têm `escopo: "ensaio"`. Toda a máquina de `--seco` (`:179-192` do produtor e a lógica "ensaio não fecha alerta" do reconciliador) protege um modo que não existe mais.

**N9 — `paginas_geradas` conta o shard remontado.** O próprio comentário de `:496` admite: imprimiu 415 com zero páginas novas. O número que vai ao ledger e à mensagem de sucesso não mede acréscimo. (`check-onda-avanca` mede certo, mas o ledger guarda o número errado.)

**N10 — a unit afirma um `ExecStartPre` que não existe.** `ops/systemd/wikijuridica-daily-content.service:7`: "O binário Go é construído no ExecStartPre e não vem de cache". Não há diretiva `ExecStartPre=` na unit. Consequência: as ~10 compilações `$GO run` das etapas 1 e 2 acontecem DENTRO do `ExecStart`, dentro da janela cronometrada e fora de qualquer lock pesado.

**N11 — censo que falha não impede a publicação de usar o veredito de ontem.** Etapa 7 (`:641`): censo falha → `registra "censo"` e a onda SEGUE. A etapa 8/9 chama `v2publish.LoadSeverity` (`cmd/publish-v2-direct/main.go:320`), e `internal/v2publish/v2publish.go:239` **não confere data, `as_of` nem mtime** do arquivo. Censo falhado ⇒ publica com a severidade da véspera, em silêncio.

**N12 — baseline de `check-onda-avanca` sem validação.** Etapa 2.5 falha → `registra "onda-avanca:baseline"` e a onda SEGUE. Em `:120` o `--depois` só confere que `.agents/runtime/onda-avanca/antes.txt` EXISTE. O arquivo é uma lista crua de intent_id, sem rótulo nem carimbo de tempo — então o 8.6 compara contra o baseline de uma execução anterior e o veredito "a onda avançou" fica falso nos dois sentidos.

**N13 — a etapa 8/9 escreve estado sem deixar evidência versionada.** A onda commita `portfolio_v2` (`:615`) e `v2_pages` (`:632`) e **nunca commita `data/editorial/published_manifest.jsonl`**: último commit `315ac61b`, 2026-09-10; no disco está `M` há 5 dias. Isso realimenta (f): `first_published_at.json` declara `fonte: histórico git do published_manifest`, então mesmo religado o gerador só enxerga intent cuja linha de manifesto chegou ao git.

### Pontos onde falha é engolida — auditados e LIMPOS
`:812` brotli e `:893` IndexNow usam `PIPESTATUS[0]` corretamente. O `timeout 20 tail -f /dev/null` de `:880` é espera sem `sleep` (o hook barra `sleep`), com `|| true` correto.
