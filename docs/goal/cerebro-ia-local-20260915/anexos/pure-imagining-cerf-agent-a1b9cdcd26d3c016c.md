# REFUTAÇÃO ADVERSARIAL — RUNBOOK P2 · P1 · P3

Medido 2026-09-15 22:07–22:35 -03, PLAN MODE (nada mutado). HEAD `62d71de0`, índice VAZIO,
`go.mod`/`go.sum` limpos — confirmado por leitura própria.

VEREDITO: **OPERAVEL_COM_EMENDA**, mas o §A não termina como está escrito (ataque 1) e
o §B-10 tem uma instrução que quebra o único controle de custo da coleta (ataque 4).

---

## ATAQUE 1 — §A-1 e §A-7: o gate `shell-script-quality` JÁ ESTÁ VERMELHO, e o `exit 0` do passo 7 é inalcançável

MEDIDO agora (`timeout 110 ./tools/check-shell-script-quality`, exit **1**, `duration_ms=86122`):

```
shell_script_quality_live_metrics_stale: script_set
shell_script_quality_issue_count_invalid: shellcheck=0 shfmt=5
shell_script_quality_shfmt_issues: unformatted=5 scripts=ops/host-state/etc/du,
   ops/host-state/etc/find, ops/host-state/etc/hdd-safety-net.sh,
   ops/host-state/etc/lsof, ops/host-state/etc/purga-lenta
shell_script_quality_live_metrics_stale: tool_or_issue_count
```

Nenhuma das 4 mensagens tem a ver com chave de array. E os 5 arquivos estão **TRACKED e ` M`
(não commitados)** na worktree compartilhada, último commit `d4c942f2 2026-09-11
style(shell): 108 scripts de produto formatados pelo shfmt` — o MESMO commit que o runbook
culpa pela corrupção. É trabalho não-commitado de outra frente.

Mecanismo, lido: `internal/shellscriptquality/quality.go:222-250` — `Validate` compara
`record.ScriptSetSHA256` (do arquivo commitado `data/ops/shell_script_quality_evidence.jsonl`,
`evidence_id shell-script-quality-evidence-2026-09-11`, `script_count 702`,
`shfmt_unformatted_count 0`) contra o sha vivo de `workspaceShellScripts`. **Qualquer** edição de
script (passos 2, 3 e 4) mantém `live_metrics_stale: script_set`.

Três falhas concretas:
- passo 1 usa o EXIT do gate como controle negativo → indiscriminável (precedente da memória:
  "vermelho conhecido é atribuição");
- passo 7 espera **exit 0** → exigiria (a) consertar 5 arquivos de outra frente e (b) regenerar a
  evidência, nada disso no runbook;
- regenerar a evidência AGORA congelaria no registro os bytes não-commitados de terceiro e
  `shfmt_unformatted_count 5` (precedentes "gomod sujo invalida atestação" e "gate de igualdade
  exata sobre diretório vivo").

EMENDA MÍNIMA: controle negativo = `./tools/go-modern test -count=1 ./internal/shellscriptquality/`
com fixture em `t.TempDir()`. O gate ao vivo lê-se por CÓDIGO DE MENSAGEM, nunca por exit:
`./tools/check-shell-script-quality 2>&1 | grep -c 'chaves_associativas_nao_aspeadas'` → 1 antes do
passo 2, 0 depois. Não tocar `ops/host-state/etc/*` e não regenerar a evidência nesta frente;
declarar os 4 códigos acima como baseline de vermelho conhecido, com data.

## ATAQUE 2 — §A-1: campo novo no `EvidenceRecord` derruba a validação do registro commitado (TRAÇADO, e é pior do que eu havia escrito)

`quality.go:315-316` — `if record.RecordFingerprintSHA256 == "" || record.RecordFingerprintSHA256 != FingerprintEvidenceRecord(record) { … "shell_script_quality_fingerprint_invalid" }`,
e `quality.go:322` — `record.RecordFingerprintSHA256 = ""` antes de hashear, ou seja o
fingerprint cobre **o struct inteiro**. Logo acrescentar `chaves_associativas_nao_aspeadas` ao
`EvidenceRecord` muda `FingerprintEvidenceRecord(record)` e o
`record_fingerprint_sha256: sha256:365e994a…` gravado em
`data/ops/shell_script_quality_evidence.jsonl` deixa de casar: o gate passa a emitir
**`shell_script_quality_fingerprint_invalid`** além dos 4 vermelhos de hoje.
`internal/ossscaleintegration/coverage.go:245`, `:1453` e `:1473` leem
`shellscriptquality.EvidenceRelPath` — segundo gate (`oss-scale-integration-coverage`) sobre o
mesmo arquivo.
EMENDA: a regra emite `Issue` e **não** toca `EvidenceRecord`. Campo novo só junto da
regeneração + commit do JSONL, que esta frente não pode fazer sem congelar bytes de terceiro
(ataque 1).

## ATAQUE 3 — §A-4: o teste novo entra no corpus do gate ANTES de ser commitado

`quality.go:333`: `gitenv.Command(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")`.
`--others` = **untracked**. O `tools/test_run_daily_content_chaves.sh` recém-criado já conta em
`script_count` e já passa por shellcheck e shfmt.
EMENDA: o passo 4 termina com `"${WIKI_SHFMT_BIN:-.cache/tools/shfmt-v3.13.1}" -d tools/test_run_daily_content_chaves.sh`
exit 0 e `shellcheck` limpo, no mesmo passo em que o arquivo nasce.

## ATAQUE 4 — §B-10: "Ilegível NÃO é recurso lido" quebra o único controle de custo da coleta

`internal/stjacordaos/coleta.go:150` — `if cfg.MaxRecursos > 0 && rel.RecursosLidos >= cfg.MaxRecursos`
é O teto da execução. `coleta.go:173` — `rel.RecursosLidos++` acontece **antes** de
`ParseEspelhos` (`:176`). O `SE NÃO VIER` do passo 10 manda não contar o ilegível: aí o arquivo
ilegível deixa de consumir cota **mas continua custando 1 requisição + 10 s de Crawl-Delay**.
`tools/collect-stj-acordaos` declara por escrito "O que mantém o custo previsível é
`--max-recursos`" e fixa `WIKI_GO_CMD_TIMEOUT_SECONDS=1500` / `WIKI_HEAVY_TIMEOUT_SECONDS=1800`.
Com N ilegíveis a execução estoura o orçamento e o cursor para de avançar. Bônus: o teste que ele
manda "consertar" (`coleta_test.go:286 TestColetaRespeitaOTetoDeRecursosPorExecucao`, assere
`RecursosLidos == 3`) usa fixture legível e não quebraria por essa causa — o diagnóstico está errado.
EMENDA: manter `RecursosLidos++` (o recurso FOI buscado e pago) e somar `Ilegiveis++` em paralelo.
O teto é de recursos buscados, não de recursos parseados.

## ATAQUE 5 — §B-10 incompleto: o abort de REDE continua matando os 7 datasets seguintes

`coleta.go:167-168`: `resp, err := cli.Busca(...)` → `if err != nil { return rel, fmt.Errorf("dataset %s competencia %s: %w", …) }`.
Um 500, um reset ou um timeout do STJ no meio da lista aborta o dataset **e os seguintes** —
exatamente o modo de falha que o §B existe para fechar. O passo 10 só cobre o erro de
`ParseEspelhos` (`:176-179`).
EMENDA: mesmo tratamento para erro transitório de rede (registrar, `continue`, contador próprio),
com corte por N falhas consecutivas no MESMO dataset para não varrer 52 meses contra um host fora do ar.

## ATAQUE 6 — §B-13: o cérebro é escritor CONCORRENTE do arquivo que o passo 13 lê e escreve

TRAÇADO até o fim: `cmd/generate-extracao-por-parser/main.go:78` —
`caminho := filepath.Join(raiz, filepath.FromSlash(cerebro.ArquivoExtracoes))`; `:162` —
`acrescenta(caminho, novas)`; `:228-229` — `os.OpenFile(caminho, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)`.
E `internal/cerebro/extracao.go:30` — `ArquivoExtracoes = "data/ai/extracoes_dispositivos.jsonl"`.
É literalmente o mesmo arquivo do worker vivo. Estado medido: `wikijuridica-cerebro.service` `ActiveState=active`
`SubState=running` `NRestarts=1` `WatchdogUSec=0`, `Restart=always`; Ollama com `qwen3.5:4b`
residente (`size_vram=0`). E o arquivo cresceu de **44.160** (número do runbook) para **44.189**
durante esta sessão — o worker está apendando agora.
O runbook analisa a corrida de decodificador só contra o COLETOR e nunca pausa o cérebro. É o
mesmo mecanismo que ele próprio descreve (append > 4 KiB entrelaçado + `json.Decode` abortando em
linha parcial), aplicado ao escritor que ele esqueceu. Não há `cerebro pausar` (subcomandos reais:
`servir, enfileirar-embeddings, enfileirar-medicao, status, ativar, reabrir, compactar,
enfileirar-extracoes, enfileirar-comentarios`); a pausa é por carga (`saude.go:50 CargaMax`) ou
`systemctl stop`.
EMENDA: ordem passa a ser **parar o worker → parser → writeback → enfileirar → religar**, com o
`ActiveState` lido antes e depois; ou o parser grava shard próprio
(`dispositivos_promovidos_parser.jsonl`) e o writeback lê "última linha por chave" entre shards.

## ATAQUE 7 — §B-13: número esperado errado (44.160 contra 44.189 medido)

`wc -l data/ai/extracoes_dispositivos.jsonl` → **44.189** agora.
`dispositivos_promovidos.jsonl` → 35.082 ✓ e `registros-*.jsonl` → 60.221 ✓ (esses dois conferem).
EMENDA: o ANTES do passo 13 grava o número lido e o DEPOIS exige "maior que o ANTES", nunca uma
constante — o arquivo tem escritor vivo.

## ATAQUE 8 — §C-19: o ANTES não executa

`tail -2 data/ops/daily_content_collect.jsonl | grep -c 'tls: handshake fail'` → **0**, `grep` exit **1**.
As duas últimas linhas do ledger são `'noticias - oficiais'` e `'stf - informativo'` (medido); a
linha de diários de hoje está mais atrás.
EMENDA: filtrar por fonte —
`python3 -c "import json;[print(d['medido_em'],d['saida'][:120]) for d in map(json.loads,open('data/ops/daily_content_collect.jsonl')) if 'diarios' in d['fonte']]" | tail -3`.

## ATAQUE 9 — §C-19: o predicado de retentativa omite exatamente a falha que eu medi

O runbook retenta 429/500/502/503/504. MEDI agora:
`curl -A "$UA" 'https://api.queridodiario.org.br/gazettes?size=1&published_since=2026-09-14'`
→ `curl: (28) Operation timed out after 25001 milliseconds`, HTTP **000**.
`internal/sourceresolve/resolve.go:205-209` trata erro de transporte por `prova.ErroDeRede` +
`continue`, FORA do ramo de status (`:210-214`). Com timeout/TLS/reset o predicado por status não
dispara, `Resolver` devolve `ErrNenhumCandidato` e `resolveAPIBase`
(`cmd/collect-diarios-municipais/main.go:239-242`) volta a `apiBase`, o host morto.
Orçamento: `&http.Client{Timeout: 30 * time.Second}` × 4 tentativas × N candidatos + backoff
2/4/8 s cabe mal no `timeout 900` de `run-daily-content:422`.
EMENDA: retentar também erro de transporte; orçamento TOTAL de resolução (ex. 120 s) em vez de
4 tentativas por candidato; e o fallback nunca ser `apiBase` (a base confirmada, como o runbook já
propõe, ou falha honesta).

## ATAQUE 10 — §C: a causa nomeada não é a que o ledger mostra na maioria dos dias

Ledger medido, fonte diários:
- **2026-09-13 exit 0** — `gravado: …/2026-09-13.jsonl (569 registros, 403 inédita(s))`. A fonte
  **não** está morta desde 08-29.
- 09-06 a 09-12: erro é `166 edicoes na janela desde 2026-08-29 e NENHUMA inedita no acervo (marca
  d'agua 2026-08-29T04:19:51)` — guarda de marca d'água, não TLS.
- 09-14 e 09-15: `sourcecollect: robots.txt de api.queridodiario.ok.org.br inalcançável: Get
  "https://api.queridodiario.ok.org.br/robots.txt": remote error: tls: handshake fail`.

E o `check-frescor-canal-diario.log` de hoje 12:29 reprova `diarios` citando a mensagem da MARCA
D'ÁGUA, não a de TLS. A marca d'água atual é `2026-09-13T03:56:39`.
EMENDA: o DEPOIS do §C-19 não pode ter exit 0 do ensaio como prova única — com o resolvedor certo
a fonte pode responder "janela sem inédita" e sair 1 legitimamente. A prova certa é a base
resolvida impressa (`api.queridodiario.org.br`) e a trilha com status/content-type/sha por
candidato; exit 0 é consequência da fonte, não do conserto.
(Verifiquei o resto do §C e CONFIRMO: `api.queridodiario.org.br/robots.txt` → **404**, então o
comentário de `main.go:52` que afirma "robots 200" mente, como o runbook diz. E o `.ok.org.br` não
está morto em bloco: `data.queridodiario.ok.org.br` → 403, `queridodiario.ok.org.br` → 302, só o
`api.` tem SNI aposentado — logo promover apenas `research_url`:1036 e `alt`:1038 está certo, e
deixar `base_url`:1035 e `robots_url`:1045 como estão NÃO é lacuna.)

## ATAQUE 11 — §D-23: o controle negativo cobre 1 de 5 sítios de menção, e 2 deles não são comentário `#`

Medido (`grep -rn` em `tools/ ops/ .githooks/`):
- `tools/run-daily-content:446` e `:447` — comentário `#` (o único que o runbook nomeia);
- `tools/check-writeback-do-cerebro-nao-atrasa:8` — dentro de **docstring Python `"""`**, cita
  `generate-lei-artigo-pages:461` **e** `generate-acordao-pages:413`;
- `tools/generate-motor-tier-a:58` — comentário `#`, cita `cmd/generate-lei-artigo-pages`;
- `tools/test_generate_motor_tier_a.py:308` — string Python, cita `cmd/generate-lei-artigo-pages:1134`.

Um predicado que "descarta comentário `#`" trata a docstring como CÓDIGO e faz o órfão passar — o
falso negativo, não o falso positivo. O controle negativo proposto ("cópia em /tmp que só tenha as
duas linhas de `run-daily-content:446-447`") não o pega.
EMENDA: o controle negativo leva os 5 sítios medidos; o predicado casa POSIÇÃO DE COMANDO
(`$GO run ./cmd/<n>`, `ExecStart=…<n>`, `"$ROOT/tools/<n>"`, `./cmd/<n>` como primeira palavra),
sem depender de remover comentário.

## ATAQUE 12 — PRÉ-VOO omite os dois timers que leem o arquivo que o §A edita

Medido em `systemctl list-timers`: `wikijuridica-daily-content.timer` → **2026-09-16 04:31:33**
(`ExecStart=/opt/wiki/tools/run-daily-content`, service:51) e
`wikijuridica-daily-content-noticias.timer` → **2026-09-16 12:20:55**
(`ExecStart=… --somente-noticias`, service:35). As units leem o script do disco no disparo. O
pré-voo do runbook só checa `stj-acordaos-coleta` e `qualidade-diaria`.
EMENDA: incluir os dois no pré-voo e editar segurando `flock -n 9 /tmp/wiki-daily-content.lock`
(não-bloqueante: se estiver tomado, a onda está rodando — não editar). O laço de trava do próprio
script está em `run-daily-content:76-82`.

## ATAQUE 13 — §E afirma "não publica página nenhuma", e o passo 2 REARMA a coleta da onda de 12:20

Hoje: `[noticias - oficiais]` (corrompida) nunca casa o filtro `[ "$chave" = "noticias-oficiais" ]`
(`run-daily-content:353-357`) → **zero coletas** na passada `--somente-noticias`. Mas a chave do
gerador é `[noticias]`, **sem hífen**, logo o filtro de `:376-380` a preserva — e
`data/ops/daily_content_logs/gen-noticias.log` tem mtime **15/set 12:20**, ou seja a onda de 12:20
GERA e PUBLICA hoje. Depois do passo 2 ela volta a coletar antes de publicar: insumo novo,
publicação transacional (8/9), reload e IndexNow na próxima às 12:20:55.
EMENDA: tirar a frase "este bloco não publica página nenhuma" (é falsa sobre a consequência) e
acrescentar a verificação da PRIMEIRA onda pós-conserto — `tail -6 data/ops/daily_content_collect.jsonl`
exigindo `'noticias-oficiais'` sem espaços, e `tail -1 data/ops/daily_content_runs.jsonl` com
`escopo: "completa"`. Sem esperar: a etapa 1 isolada se exercita com
`./tools/go-modern run ./cmd/collect-noticias-oficiais -limite 200` em ensaio.

## ATAQUE 14 — §A-3 ressuscita um `--seco` que bloqueia o deploy de TODAS as frentes, e nenhum passo prova que ele funciona

Estado de hoje é o SEGURO: `--seco` cai no `*)` e faz `exit 2` em `run-daily-content:105`, ANTES de
`trap gravaEvidencia EXIT` (`:280`). Depois do conserto ele roda coleta + os 5 geradores e sai 0 em
`:483-487` — deixando `v2_pages`/`portfolio_v2` sujos, e `deploy-publico:307` (passo 0a-bis)
para para todo mundo (`WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO` em `deploy-publico:303-318`). O runbook
reconhece isso no AVISO e manda consertar de todo modo, e o único DEPOIS é que
`--argumento-que-nao-existe` continua saindo 2 — não prova nada sobre `--seco`.
EMENDA: ou `--seco` passa a escrever em prefixo de ensaio / exigir `WIKI_ONDA_ENSAIO=1`, ou o passo
3 sai do bloco. Consertar um caminho que nenhum passo exercita e que bloqueia o deploy alheio é
arma carregada.

## ATAQUE 15 — §A-5 muda o gate e não roda o selftest que a bancada roda

`tools/check-frescor-canal-diario-selftest` existe (311+ linhas, exercita o gate como subprocesso) e
é descoberto pelo passo **2c-ter** de `tools/run-qualidade-diaria` (`:614-619`), que roda 04:47–05:50.
O passo 5 não o menciona. Precedente do contrato: gate verde com 14 de 17 testes quebrados.
EMENDA: `python3 tools/check-frescor-canal-diario-selftest` no DEPOIS do passo 5, com exit 0.

## ATAQUE 16 — §A-5 conserta metade do fuso e o erro inverso JÁ ESTÁ NO DISCO, hoje

Há **três** sistemas de data no gate, não dois:
- `dia_de()` (`:105-108`) toma `medido_em[:10]` = dia **UTC** ("o produtor sempre grava em UTC");
- o nome do arquivo de coleta também é **UTC**: medido agora,
  `data/research/daily/noticias-oficiais/2026-09-16.jsonl`, 655.518 B, **escrito às 21:51 local de
  15/set** pelo `wikijuridica-noticias-coleta.timer`;
- `máx. publicado` sai do manifesto e está em **2026-09-15**.

Rodei o gate às 22:26 local (= 2026-09-16 UTC) e ele imprime:
`[OK] noticias — máx. publicado 2026-09-15, último arquivo de coleta 2026-09-16, hoje 2026-09-16
(gap 1d ≤ tolerância 1d)`, exit 1 (só `diarios` reprova). **Isto confirma A5 do runbook** — o meu
log das 12:29 dizia gap 0d porque `hoje` ainda era 09-15 UTC.
Mas é exatamente por isso que a emenda de um lado só quebra: trocando **apenas** `hoje`
(`:337 hoje = args.hoje or datetime.now(timezone.utc)…`) para local, `hoje` vira 2026-09-15 contra
um arquivo de coleta que já se chama 2026-09-16 → **gap negativo**, com o arquivo já no disco
nesta hora. O gate **já aceita `--hoje`**, que é o atalho para provar isso AGORA sem esperar
virada de dia — o runbook não o usa.
EMENDA: converter as TRÊS pontas para `America/Sao_Paulo` (o `dia_de` do ledger, a data do nome do
arquivo de coleta e o `hoje`), e provar antes de commitar com
`tools/check-frescor-canal-diario --hoje 2026-09-15` e `--hoje 2026-09-16`, exigindo gap ≥ 0 nos dois.

## ATAQUE 17 — §A-5 "SE NÃO VIER" manda voltar ao passo 2 por um diagnóstico falso

MEDIDO: a onda de hoje coletou. `2026-09-15T07:29:11 'noticias - oficiais' exit 0
gravado: data/research/daily/noticias-oficiais/2026-09-15.jsonl`;
`2026-09-15T07:28:59 'stj - precedentes' exit 0 temas.csv inalterado (304)`;
`'stf - informativo' exit 0 304`. A data 2026-09-10 no gate é **só o nome**: `CANAIS`
(`:65-86`) tem `stj-precedentes`, `stf-informativo`, `diarios-municipais`, `noticias-oficiais`
canônicos e o ledger passou a gravar a forma com espaços em `2026-09-11T07:24:30`.
A instrução "a onda rodou com o arquivo corrompido e gravou ZERO; volte ao passo 2" manda o
operador para um laço.
EMENDA: o diagnóstico certo é
`grep -c '"fonte": "stj - precedentes"' data/ops/daily_content_collect.jsonl` → 5 e a última linha
de hoje: se existe linha de hoje, o defeito é a normalização do gate, nunca a coleta.

## ATAQUE 18 — passos 13, 15 e 16 não executam pela ferramenta de shell do agente

O `Bash` tem timeout máximo de **120 s**. Passo 15 ≈ 320 s (declarado pelo próprio runbook);
passo 16 = 7 × ~530 s ≈ 3.710 s num único `for`. A chamada é morta no meio, com o `--aplicar` já
tendo escrito parte do cursor — e o operador não vê exit code.
EMENDA: um dataset por chamada, via `ai-pane run NOME 'cmd'` (devolve saída + exit code real, é o
instrumento que o contrato da máquina nomeia) ou em background; nunca um `for` de 7 no foreground.

## ATAQUE 19 — A8 apresenta como MEDIDO um número derivado

520 − (52+52+21+3) = 392 fecha a aritmética, mas supõe 52 competências em corte-especial,
primeira/terceira-secao e segunda/quinta/sexta-turma — os 6 datasets que **nunca** foram coletados
(cursor medido: só 4 chaves). Os 3.920 s e os "67 min" herdam a suposição.
EMENDA: marcar 392 e 67 min como DERIVADOS de 52/dataset, e o gate do passo 11 imprimir
`len(recursos)` POR dataset (controle positivo) antes de qualquer contagem de "faltam".

## ATAQUE 20 — citação errada de arquivo:linha em §B-12

`check-redesocial-completude` está em `.githooks/pre-commit:575` (o `if` do gatilho começa em
`:574`), não em `:300`. O gatilho medido é
`^(internal/|cmd/|ops/nginx/|content/(social_policy|redesocial_entregas)\.json$|docs/goal/PLANO_REDE_SOCIAL\.md$)`
— então os commits de §B-12, §C-21 e §D-24 o disparam de fato, mas quem for conferir a linha 300
encontra `check-produto-nao-some-do-worktree`.
EMENDA: corrigir a linha.

## ATAQUE 21 — §A-2: o DEPOIS `shfmt -d` exit 0 não discrimina

MEDIDO: `.cache/tools/shfmt-v3.13.1 -d tools/run-daily-content` **já sai 0 hoje** — o arquivo está
shfmt-normalizado COM as chaves corrompidas. O mesmo comando dá 0 antes e depois do passo 2.
A prova real é o par que eu medi por stdin: forma `[stj-precedentes]` → exit 1 com o diff que
re-insere os espaços; forma `["stj-precedentes"]` → exit 0, sem diff.
EMENDA: o DEPOIS do passo 2 é o par por stdin (ou sobre cópia em /tmp), mais
`grep -cE '^\s*\["[a-z-]+"\]=' tools/run-daily-content` → 10 e `grep -cE '^\s*\[[A-Za-z0-9_]+ - '` → 0.
(Confirmo os 8 hits de hoje e as 4 linhas de `COLETORES` + 4 de `GERADORES`.)

## ATAQUE 22 — os cinco commits sob `flock` não levam pathspec, e o lock é justamente a janela do índice alheio

Passos §A-7, §B-12, §C-21 e §D-24 são
`flock /tmp/opt-wiki-agent-heavy.lock -c 'cd /opt/wiki && git add <paths> && git commit -F <msg>'`.
Esperar no `flock` (a bancada segura o lock ~70 min) é exatamente a janela em que outra sessão
encena arquivos: o `git commit` **sem pathspec** commita o índice inteiro, levando junto o trabalho
dela. É o precedente `commit-sob-flock-pega-indice-do-futuro` da memória, e o remédio está escrito
no contrato da máquina (`~/.claude/CLAUDE.md:102`: "Para escopar um commit use pathspec
(`git commit -F msg -- <paths>`), que não toca a worktree"). O runbook só cita pathspec como
recurso de exceção no "SE NÃO VIER" do passo 6. Concreto hoje: há 5 arquivos ` M` em
`ops/host-state/etc/` de outra frente, mais ~60 arquivos ` M` em `data/` (git status inicial).
EMENDA: `git commit -F /tmp/msg.txt -- <os mesmos caminhos do add>` nos quatro commits pesados e
no leve; e conferir `git diff --cached --name-only` DEPOIS de obter o lock, não antes.

## ATAQUE 23 — ROLLBACK: os passos de DADO não têm o rollback que o runbook declara

Passos 15/16/17 com `--aplicar` escrevem `cursor.json`, `manifest.jsonl`, `quarentena.jsonl`
(rastreados, recuperáveis por `git show HEAD:`) **e** `registros-*.jsonl`, que são **gitignored**
(`git check-ignore -v` → `.gitignore:697:data/corpus/**/registros-*.jsonl`, verificado). Para esses
não existe "para frente" por git: só `--refazer`, que o runbook nunca nomeia como rollback (a flag
existe, `cmd/collect-stj-acordaos/main.go:65`).
EMENDA: antes do passo 15, preservar `cursor.json` e `manifest.jsonl` em `.agents/runtime/` com
data (o contrato manda preservar antes de mutar) e declarar
`tools/collect-stj-acordaos --aplicar --refazer --dataset <d>` como o rollback para frente dos
registros.

---

## O QUE EU TENTEI DERRUBAR E NÃO CONSEGUI (refutação falhada = verificação)

- **A1/A2 (shfmt re-corrompe o conserto óbvio).** CONFIRMADO por medição própria em stdin: sem
  aspas → exit 1 com `[stj-precedentes]` → `[stj - precedentes]`; com aspas → exit 0.
- **A4 (a corrupção entra em 2026-09-11T07:24:30).** CONFIRMADO: 5 linhas de cada forma corrompida,
  primeira em `2026-09-11T07:24:30.560428+00:00` (`normas - federais`); as canônicas começam em
  `2026-08-26`. Tratar as duas grafias como sinônimo sem reescrever o passado está certo.
- **A7 (segunda-secao é o 3º do ExecStart e o abort mata os 7 seguintes).** Tentei derrubar pela
  ordem de `DatasetsEspelhos` e FALHEI: o `ExecStart` (unit:60) tem ordem PRÓPRIA — terceira-turma,
  quarta-turma, **segunda-secao**, primeira-turma, segunda-turma, primeira-secao, corte-especial,
  quinta-turma, sexta-turma, terceira-secao — e o cursor medido (terceira-turma 52, quarta-turma 52,
  segunda-secao **21**, primeira-turma 3, resto ausente) casa exatamente com abort no 3º.
- **A14 (três órfãos de página, `entity` incluído).** CONFIRMADO: `ls cmd | grep -cE '^generate-.*-pages$'`
  → 8; invocação real só em `run-daily-content:369-373` (stj-tema, stj-sumula, stf-informativo,
  noticia, diario). `generate-{acordao,lei-artigo,entity}-pages` sem nenhuma invocação.
- **A19 (`-limite` é tamanho de página).** CONFIRMADO: `main.go:377 flag.IntVar(&limite,"limite",1000,"edições por página da API; a rodada pagina até esgotar a janela")`; `-seco` em `:378`; `-com-texto` em `:379`.
- **A20 (`--desde`/`--ate` aceitam hífen).** CONFIRMADO pelo help: "competencia minima, AAAA-MM-DD".
- **A21 (304 não escreve manifesto).** CONFIRMADO: `coleta.go:170-173` `if resp.NaoModificado { rel.NaoModificados++; continue }` antes de qualquer gravação.
- **A13 (robots do host vivo é 404).** CONFIRMADO por medição própria: 404 em 0,58 s. O comentário
  de `main.go:52` afirmando 200 mente.
- **A10 (SNI aposentado é deles).** Não re-medi o `openssl`, mas o ledger de 09-14 e 09-15 traz o
  `remote error: tls: handshake fail` no `api.queridodiario.ok.org.br` e o `.ok.org.br` responde
  (403/302) nos outros subdomínios — consistente.
- **A15 (nenhum pacote do bloco está no grafo do validador).** Não re-rodei `list -deps` (custa
  build); `tools/check-validator-attestation` existe e é o instrumento certo no passo 12.
- **§E-27 (LC_ALL=C).** CONFIRMADO: `date -d '60 min ago' '+%d/%b/%Y:%H'` → `15/set/2026:21`
  contra `15/Sep/2026:21` com `LC_ALL=C`. O grep com `LC_ALL=C` devolve **31** linhas de bot na
  última hora, exit 0. `/var/log/nginx/wikijuridica/access.log` é legível (`www-data:adm 0660`,
  63 MB) — o usuário está no grupo `adm`.
- **§E-25 (healthz).** CONFIRMADO: `HTTP/2 200`, `cf-cache-status: DYNAMIC`, 0,305 s.
- **§E-28 (cérebro).** CONFIRMADO: `active/running`, `NRestarts=1`, `WatchdogUSec=0`,
  `Restart=always`; `/api/ps` com `qwen3.5:4b` 3.227.894.413 B, `size_vram=0`, `context_length=8192`.
  loadavg 8,79 agora — abaixo do `CargaMax=12`, logo o worker NÃO está pausado por carga.
- **361 gates** em `var Names` ✓; `internal/checks/dispatcher_orfao_test.go` existe ✓;
  `tools/check-validator-attestation`, `tools/check-fontes-alcancaveis`,
  `tools/generate-propostas-reescrita`, `tools/generate-first-published-at` existem ✓.
- **Passo 7 não colide com outro script**: só 4 scripts do repo usam `declare -A`
  (`check-public-sem-lixo`, `check-ingress-fontes-completas`, `run-daily-content`,
  `check-untracked-product-inventory`) e só `run-daily-content` tem subscrito literal. O predicado
  estreito não vai disparar fora dele.
- **`.gitignore:697`** ignora `data/corpus/**/registros-*.jsonl` ✓ (verificado por `git check-ignore -v`).
- **sqlite3** em `/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3` existe e é o
  `sqlite3` do PATH ✓.
- **2c-bis** (`tools/test_*.sh`) existe em `run-qualidade-diaria:559-582` ✓ — o teste novo entra na
  bancada por descoberta, como o runbook diz.
- **`--somente-noticias` sai 0 sem fazer nada com o flock tomado** ✓ (`run-daily-content:76-82`).

- **A5 (frescor).** Eu havia registrado uma divergência e ela era MINHA, não do runbook: comparei
  contra o log das 12:29. Rodei o gate às 22:26 local e ele confirma A5 na íntegra —
  `jurisprudencia` e `sumulas` em `[OK]` citando **2026-09-10**, `noticias` `[OK]` com
  **gap 1d ≤ tolerância 1d**, `diarios` `[REPROVA]`, exit 1.
- **Nomes de símbolo do passo 9.** Nenhum é inventado: `servidorEspelhandoOSTJ`
  (`coleta_test.go:20`), `Cursor.JaColetado` (`cursor.go:70`), `Cursor.Registra` (`cursor.go:90`),
  `Cursor.Condicional` (`:61`), `Cursor.Salva` (`:103`). O spec do teste do passo 9 compila.

## O QUE NÃO MEDI, E POR QUÊ

- Não rodei `./tools/go-modern build ./internal/... ./cmd/...` nem `list -deps` (custa build de
  ~5 min e o pedido é refutação de runbook, não validação de compilação). A15 fica não verificado.
- Não medi a parede de cada recoleta (exigiria `--aplicar`, que muta).
- Não re-medi o `openssl s_client` do §C-10 (o ledger de 09-14/09-15 e as sondas de hoje já
  separam `api.` morto de `data.`/apex vivos).
- Não verifiquei o conteúdo de `.cache/go-cmd-bin/` citado no "SE NÃO VIER" do passo 14.

## O QUE O ADVISOR MUDOU

1. **Ataque 2 — mandou traçar o fingerprint em vez de supor.** Tracei: `quality.go:315-316` +
   `:322`. Resultado: **não rebaixou, subiu** — o fingerprint cobre o struct inteiro, então o campo
   novo emite `shell_script_quality_fingerprint_invalid`, um quinto vermelho.
2. **Ataque 6 — apontou que meu grep por `extracoes_dispositivos` NÃO havia acertado o parser.**
   Correto. Tracei `main.go:78 → :162 → :228`: `cerebro.ArquivoExtracoes`. O ataque passou de
   plausível a confirmado por leitura.
3. **Passo 9 — mandou conferir os nomes de símbolo.** Confirmados os cinco; retirei a suspeita.
4. **Frescor — apontou que minha "divergência" era artefato de ler o log das 12:29.** Rodei o gate
   e ele me contradisse: A5 está certo. Removi a divergência falsa. Rodar também expôs o terceiro
   sistema de data (arquivo de coleta `2026-09-16.jsonl` escrito às 21:51 local), que transformou o
   ataque 16 de "erro inverso em princípio" em "erro inverso já no disco, hoje".
5. **Acrescentou um ataque que eu não tinha: pathspec nos cinco commits sob `flock`** (agora
   ataque 22), com base no precedente `commit-sob-flock-pega-indice-do-futuro` e em
   `~/.claude/CLAUDE.md:102`. Verifiquei a linha do contrato e os arquivos ` M` de outra frente.
6. Mandou não reabrir o resto. Não reabri.
