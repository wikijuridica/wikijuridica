# RUNBOOK OPERACIONAL — Bloco P2 · P1 · P3
## desfazer o shfmt · destravar a coleta do STJ · matar os órfãos

Medido em 2026-09-15, 21:30–22:20 -03. Repositório em PLAN MODE: **nada mutado**.
HEAD `62d71de0`. Índice VAZIO, `go.mod`/`go.sum` limpos (medido).
Revisado com o advisor: §F no fim lista o que ele mudou e o que eu refutei com medição.

---

## 0. O QUE EU MEDI (e que muda o plano)

| # | achado | prova | consequência |
|---|---|---|---|
| A1 | **shfmt v3.13.1 RE-CORROMPE a chave assim que alguém a conserta.** Lê `[stj-precedentes]` como aritmética e escreve `[stj - precedentes]`. | `shfmt -d /tmp/shfmt-probe/a.sh` → exit 1 com o diff exato | "pôr o hífen de volta" NÃO é a correção. A estável é **aspar o subscrito**. |
| A2 | **Subscrito ASPEADO é shfmt-estável.** `["stj-precedentes"]` → `shfmt -d` exit **0**, sem diff; bash lê certo. | `/tmp/shfmt-probe/b.sh` exit 0 + execução | é esta a forma a escrever. |
| A3 | shfmt corrompe também a LEITURA literal: `${COLETORES[stj-precedentes]}` → `[stj - precedentes]`. | mesmo diff de A1 | em `run-daily-content` as leituras são `${COLETORES[$fonte]}` e escaparam; o gate novo cobre os dois lados. |
| A4 | **A corrupção entra no ledger em 2026-09-11T07:24:30.** Linhas de 09-10 e anteriores têm o nome canônico. | `data/ops/daily_content_collect.jsonl`, 60 últimas linhas | ledger é append-only: a leitura trata as duas grafias como **sinônimo**, nunca renomeia o passado. |
| A5 | **`check-frescor-canal-diario` dá VERDE sobre medição de 2026-09-10** em `jurisprudencia` e `sumulas`; hoje é 2026-09-16 UTC. `noticias` passa na borda do fuso (`gap 1d ≤ tolerância 1d`). | execução real, exit 1 | 2 de 4 canais em falso verde + alarme falso latente toda noite. |
| A6 | **O arquivo que derruba a coleta: 599 bytes, `sha256 ea2537c3…9b46`, `last-modified Thu, 07 Mar 2024 17:13:14 GMT`, e é SENTINELA** (`"Obs": "Sem lançamentos para o mês de fevereiro/2024"`, `ementa: ""`). Defeito: `[ { … } } ]`, uma `}` a mais. | GET real com a identidade do projeto + `cat -A` + `json.loads` | **quarentenar não perde nada**: mesmo válido o registro cairia em `semEmenta`. E está quebrado na FONTE desde 2024-03-07 — não se conserta sozinho. |
| A7 | **4 de 10 datasets no cursor; 6 nunca coletados.** terceira-turma 52, quarta-turma 52, segunda-secao 21, primeira-turma 3; **zero** em corte-especial, primeira-secao, terceira-secao, segunda-turma, quinta-turma, sexta-turma. | `cursor.json` | o `ExecStart` põe `segunda-secao` em 3º: o abort mata os 7 seguintes. |
| A8 | **392 competências a recoletar** (52 por dataset, contado na página real), **456 MB (mediana) a 565 MB (média)**, **3.920 s + 100 s de páginas ≈ 67 min** de Crawl-Delay. | contagem de `download/\d{8}.json` na página + `manifest.jsonl` (138 lotes, mediana 1.163.328 B) | teto externo legítimo. Atalho: §B-16 roda ANTES e não depende dela. |
| A9 | **A promoção por parser é 81,4% EXATOS**: 28.559 acórdãos contra 6.523 do `qwen3.5:4b`, em 35.082 distintos. | `data/ai/dispositivos_promovidos.jsonl`, contagem por `modelo` | o parser entrega o ganho **hoje**, sobre os 60.221 registros já no disco. |
| A10 | **O TLS do Querido Diário é DELES: SNI aposentado, não rota nem nosso OpenSSL.** No MESMO IP `[2606:4700:10::6814:2e4c]:443`: SNI `queridodiario.ok.org.br` → TLSv1.3 OK, `subject=CN = ok.org.br`, `Verify return code: 0`. SNI `api.queridodiario.ok.org.br` → `alert number 40`, **nenhum certificado**. Falha igual em TLS 1.2 e 1.3, IPv4 e IPv6. | `openssl s_client` com os dois SNI no mesmo socket | hostname retirado. Irreversível do nosso lado. |
| A11 | **O host vivo `api.queridodiario.org.br` OSCILA: 1 de 7 respostas 200; 6 de 6 retentativas seguidas 503 `no available server`.** O corpo de 200 CUMPRE o contrato: `territory_id "2909307"` (7 dígitos), `date 2026-09-14`, `scraped_at 2026-09-14T22:20:35`, `total_gazettes 311`. | 7 GETs medidos ~21:5x -03 | a fonte **está ingerindo** (scraped_at de ontem): a mensagem "marca d'água 2026-08-29" do ledger é resíduo velho. |
| A12 | **`sourceresolve.Resolver` não tem NENHUMA retentativa** (`resolve.go:210-214`: `status != 200` → `continue`), e `resolveAPIBase` cai de volta no host MORTO quando a resolução falha (`if err != nil { return apiBase, trilha }`). | leitura do código | **é esta a causa raiz de diarios.** O TLS é o sintoma a dois passos: um 503 do host vivo joga o coletor contra o SNI aposentado. |
| A13 | **`robots.txt` do host vivo é 404** (`{"detail":"Not Found"}`, 22 bytes). O comentário de `cmd/collect-diarios-municipais/main.go:52` afirma "robots 200 com `User-agent: * / Allow: /`". | GET real | 404 é permissão total (RFC 9309 §2.3.1.4) e `robotstxt.FromStatusAndBytes` já trata assim — mas comentário que mente é bug (R1). |
| A14 | **TRÊS produtores de página órfãos, não dois**: `generate-acordao-pages`, `generate-lei-artigo-pages` e **`generate-entity-pages`** (este o plano não nomeava). Os 5 restantes têm invocação real via `GERADORES` de `run-daily-content:369-373`. As citações dos órfãos em runners são **texto de comentário** (`run-daily-content:446-447`, `check-writeback-do-cerebro-nao-atrasa:8`, `generate-motor-tier-a:58`). | `ls cmd \| grep -cE '^generate-.*-pages$'` = **8**, + grep de invocação com filtro de comentário | o gate do P3 casa **INVOCAÇÃO**, nunca menção — senão os órfãos passam. |
| A15 | **Nenhum pacote deste bloco está no grafo do validador**: `internal/stjacordaos`, `internal/shellscriptquality`, `internal/checks`, `internal/cerebro`, `internal/sourcecollect`, `internal/sourceresolve` — FORA. Controle positivo: `internal/quality`, `internal/seo`, `internal/editorial`, `internal/lexml`, `internal/v2ingest` DENTRO; 98 pacotes `portaljuridico/*` no grafo. | `go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` | **nenhum commit deste bloco exige reatestação.** |
| A16 | A bancada do pacote STJ custa **1,61 s de parede** (`test 0,539 s`). | `/usr/bin/time` sobre `go-modern test -count=1 ./internal/stjacordaos/` | rodá-la em todo passo é grátis. |
| A17 | **`core.autocrlf = input`**: o fixture de 599 bytes com 23 CRLF virará blob de **576 bytes** no commit (`git cat-file -s` = 576, git avisa "CRLF will be replaced by LF"). E `.gitattributes` **proíbe** acrescentar `-text`/`eol=` nele. | `git hash-object -w --path …` + `git cat-file -s` | o fixture se guarda em **LF** (576 B, `sha256 3c4dd3c5…b8c9`) e o teste **reconstrói** o CRLF. Round-trip LF→CRLF == original: **True** (medido); as duas formas falham no parser de modo idêntico. |
| A18 | **`Fila` não tem função que apague ou cancele tarefa.** Só `Enfileirar` (INSERT OR IGNORE), `Reivindicar`, `Concluir`, `Falhar`, `Recuperar`, `Reabrir`, `AtualizaPrioridade`. | `grep 'func (f \*Fila)' internal/cerebro/fila.go` | **`pendente` NÃO cai** com o parser. A prova do §B-16 é outra (ver o passo). |
| A19 | **`-limite` do coletor de diários é TAMANHO DE PÁGINA (default 1000), não teto da rodada** — "a rodada pagina até esgotar a janela", com `tetoPaginas = 12`. Com 311 gazetas na janela, `-limite 5` exigiria 63 páginas e a rodada **falha sem gravar**. E ele **tem `-seco`** (`flag.BoolVar(&seco,"seco",…, "relata sem gravar")`). | `main.go:377-379`, `coletarJanelaInteira:661-706` | usar a invocação do `COLETORES` (`-limite 300 -com-texto 25`) e ensaiar com `-seco`. |
| A20 | **`--desde`/`--ate` do coletor do STJ aceitam hífen e são normalizados**: `main.go:74-75` chama `competencia(...)` e `:166` faz `strings.ReplaceAll(limpa, "-", "")`. | leitura do código | a forma `--desde 2024-02-01` do §B-13 está correta. (Ponto do advisor **refutado por medição**.) |
| A21 | **304 não escreve manifesto**: `coleta.go:169-172` faz `rel.NaoModificados++; continue` antes de qualquer gravação. | leitura do código | "timer desligado" e "nada novo na fonte" ficam indistinguíveis por `coletado_em`. O gate do §B-11 precisa de um **resumo por execução**. |

Saída literal do A5 (exit 1):
```
[REPROVA] diarios         (cadencia ) — coleta falhou hoje (ledger ok=false) … (marca d'água 2026-08-29…)
[OK     ] noticias        (cadencia ) — máx. publicado 2026-09-15, último arquivo 2026-09-15, hoje 2026-09-16 (gap 1d ≤ tolerância 1d)
[OK     ] jurisprudencia  (sazonal  ) — fonte(s) saudável(is) … stj-precedentes (2026-09-10) … stf-informativo (2026-09-10)
[OK     ] sumulas         (sazonal  ) — fonte(s) saudável(is) … stj-precedentes (2026-09-10)
```

---

## 0-bis. JANELAS PROIBIDAS E LOCKS (medido)

| janela local | quem ocupa | por que importa |
|---|---|---|
| **09:40–10:17** | `wikijuridica-stj-acordaos-coleta.timer` (`OnCalendar=09:40`, `RandomizedDelaySec=20min`, até 100 recursos × 10 s ≈ 17 min) | toma `scope:collect:stj-acordaos:gocache:/home/rafael/.cache/go-build`. À mão aí, espera `WIKI_HEAVY_LOCK_WAIT_SECONDS=600` e **sai 75**. |
| **04:47–05:50** | `wikijuridica-qualidade-diaria.service` segura `/tmp/opt-wiki-agent-heavy.lock` no `ExecStart` (~70 min) | commit que toca Go serializa nesse lock e fica preso. |
| **04:31 / 12:20** | `wikijuridica-daily-content.timer` e `-noticias.timer` | tomam `/tmp/wiki-daily-content.lock` e LEEM `tools/run-daily-content` do disco no disparo. Não editar durante a execução. |

`/tmp/opt-wiki-commit.lock` que a memória descreve **NÃO existe no repositório** (`grep -rln` em `tools/ docs/ .githooks/ ops/` → vazio, medido). Vale o do contrato: `flock /tmp/opt-wiki-agent-heavy.lock` para commit que toca Go.

Pré-voo (<2 s, read-only):
```bash
cd /opt/wiki && date '+%F %T %z' && cat /proc/loadavg && \
  git status --porcelain go.mod go.sum && git diff --cached --name-only && \
  systemctl list-timers 'wikijuridica-stj-acordaos-coleta.timer' 'wikijuridica-qualidade-diaria.timer' --no-pager
```
Esperado: nenhuma linha em `go.mod`/`go.sum` nem no índice; hora fora das duas janelas.

---

# §A — P2 · DESFAZER O shfmt

### 1. Criar o instrumento ANTES da correção: regra `chave_associativa_nao_aspeada`

**INSTRUMENTO A CRIAR.** Regra nova dentro do gate já registrado `shell-script-quality`
(`internal/checks/checks.go:390` em `Names`, `:1820` no dispatcher → `shellscriptquality.Validate(root)`).
**Predicado ESTREITO** (o amplo dispararia em `${a[i+1]}` e `${a[$idx]}` nos 108 scripts de produto):
só subscritos dentro de um bloco `declare -A NOME=( … )` e leituras `${NOME[…]}` de nomes declarados `-A`
**no mesmo arquivo**. Acusa (a) subscrito já corrompido (contém ` - `) e (b) subscrito não aspeado com
caractere fora de `[A-Za-z0-9_]`. Grava: **nada**. Reporta `Issue{Code:"shell_script_chave_associativa_nao_aspeada"}`
+ campo `chaves_associativas_nao_aspeadas` no `EvidenceRecord`. Exit pelo `Report.Messages()`.

- **ANTES**
  ```bash
  grep -c 'shell_script_chave_associativa' internal/shellscriptquality/quality.go   # 0 (MEDIDO)
  grep -nE '^\s*\[[A-Za-z0-9_]+ - ' tools/run-daily-content | wc -l                  # 8 (MEDIDO)
  ```
- **AÇÃO** Escrever a regra + teste com quatro fixtures: `[a - b]=` → 1 issue · `[a-b]=` → 1 issue ·
  `["a-b"]=` → 0 · `${v[i+1]}` num array indexado → **0** (o falso positivo que o predicado estreito evita).
  A prova por mutação é grátis: **o disco de hoje é o controle negativo**.
- **DEPOIS**
  ```bash
  ./tools/go-modern test -count=1 ./internal/shellscriptquality/     # ok
  ./tools/check-shell-script-quality 2>&1 | tail -20                 # REPROVA citando tools/run-daily-content, 8 ocorrências
  ```
- **SE NÃO VIER** Verde aqui = o enumerador não alcança `tools/run-daily-content`. Imprima o conjunto `scripts`
  de `quality.go` (ele vem de `git ls-files`, não de glob) antes de culpar a regra. Se acusar em outro script,
  é achado NOVO: corrija-o no mesmo commit; nunca afrouxe a regra.
- **ROLLBACK** Para frente: a regra é aditiva. Falso positivo ⇒ estreitar o predicado, nunca desligar.

### 2. Corrigir as 8 chaves de `tools/run-daily-content` com subscrito ASPEADO

- **ANTES**
  ```bash
  grep -nE '^\s*\[[A-Za-z0-9_]+ - ' tools/run-daily-content   # :337 :338 :345 :346 :347 + 3 de GERADORES
  bash -n tools/run-daily-content && echo "bash -n aprova o ERRADO (esperado)"
  ```
- **AÇÃO** Edição pontual, 10 linhas lidas uma a uma:
  `[stj - precedentes]`→`["stj-precedentes"]` · `[stf - informativo]`→`["stf-informativo"]` ·
  `[normas - federais]`→`["normas-federais"]` · `[diarios - municipais]`→`["diarios-municipais"]` ·
  `[noticias - oficiais]`→`["noticias-oficiais"]` · `[stj - tema]`→`["stj-tema"]` ·
  `[stj - sumula]`→`["stj-sumula"]` · `[stf - informativo]` (GERADORES)→`["stf-informativo"]` ·
  e `[noticias]`→`["noticias"]`, `[diarios]`→`["diarios"]` por uniformidade.
- **DEPOIS**
  ```bash
  bash -n tools/run-daily-content && echo OK
  /opt/wiki/.cache/tools/shfmt-v3.13.1 -d tools/run-daily-content; echo "shfmt exit=$?"   # 0, sem diff (A2)
  grep -cE '^\s*\["[a-z-]+"\]=' tools/run-daily-content                                    # 10
  ```
- **SE NÃO VIER** `shfmt -d` saindo 1 em OUTRA linha é dívida de formatação preexistente: rode `shfmt -d`
  **antes** da edição para separar o que já estava torto do que você escreveu.
- **ROLLBACK** Para frente; a forma anterior está em `git show HEAD:tools/run-daily-content`.

### 3. Ressuscitar `--seco` (morto desde 2026-09-09)

- **ANTES** `sed -n '37,38p;99,108p' tools/run-daily-content` — :37-38 liga `SECO=1`; :101 só conhece
  `--somente-noticias`; :105 faz `exit 2`. Os usos vivos estão em :193 e :483-485 (MEDIDO).
- **AÇÃO** Acrescentar `--seco) SECO=1 ;;` ao `case` de :100-107 e corrigir a linha de uso :104 para
  `uso: run-daily-content [--seco] [--somente-noticias]`. Mover a atribuição de :37-38 para dentro do `case`
  (uma fonte de verdade só).
- **DEPOIS**
  ```bash
  tools/run-daily-content --argumento-que-nao-existe ; echo "exit=$?"   # 2 (o caminho de recusa segue vivo)
  bash tools/test_run_daily_content_chaves.sh ; echo "exit=$?"          # 0 (passo 4 cobre --seco no parser de flags)
  ```
- **AVISO OPERACIONAL, não passo**: `--seco` roda coleta **e geração**, então deixa `data/editorial/v2_pages/`
  e `portfolio_v2/` **sujos** até a onda seguinte commitá-los. Enquanto estiverem sujos,
  `tools/deploy-publico` **para no passo 0a-bis/7 para TODAS as frentes**. Não deixe `--seco` de véspera de deploy,
  e **nunca** use `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` para contornar.
- **SE NÃO VIER** exit 2 com `--seco` ⇒ o `case` não foi alcançado; confira se nenhum `[[ "${1:-}" == … ]]`
  anterior curto-circuitou o `for argumento in "$@"` de :99.
- **ROLLBACK** Para frente.

### 4. Criar `tools/test_run_daily_content_chaves.sh`

**INSTRUMENTO A CRIAR.** Descoberto sozinho pelo glob `tools/test_*.sh` do passo **2c-bis** de
`tools/run-qualidade-diaria` (teto 600 s/arquivo). Mede, contra os BYTES REAIS do arquivo (via
`WIKI_ALVO`, default `tools/run-daily-content`):
(i) `COLETORES` com exatamente 5 chaves, todas `^[a-z]+(-[a-z]+)*$`; (ii) `GERADORES` idem, 5;
(iii) o filtro `--somente-noticias` deixa **1** coletor (`noticias-oficiais`) e **1** gerador (`noticias`);
(iv) `--seco` é aceito pelo parser de flags (não cai no `*)`); (v) `shfmt -d` exit 0.
Grava nada. Exit 0 passou · 1 falhou · 2 não conseguiu extrair os blocos (defeito do teste, não veredito).

- **ANTES** `ls tools/test_run_daily_content_chaves.sh` → não existe (MEDIDO).
- **AÇÃO** Extrair os blocos por `sed -n '/^declare -A COLETORES=(/,/^)/p'` e avaliá-los num subshell.
  **Nunca** `source` do arquivo inteiro: ele toma flock e roda a onda.
- **DEPOIS**
  ```bash
  bash tools/test_run_daily_content_chaves.sh ; echo "exit=$?"     # 0
  cp tools/run-daily-content /tmp/mut.sh && sed -i 's/\["stj-precedentes"\]/[stj - precedentes]/' /tmp/mut.sh
  WIKI_ALVO=/tmp/mut.sh bash tools/test_run_daily_content_chaves.sh ; echo "mutante exit=$? (esperado 1)"
  ```
- **SE NÃO VIER** Mutante vivo (exit 0) ⇒ o teste reimplementa a leitura em vez de ler o arquivo.
  Imprima as chaves extraídas ANTES de escrever a asserção.
- **ROLLBACK** Para frente.

### 5. Corrigir `tools/check-frescor-canal-diario`: sinônimos + fuso

- **ANTES** `tools/check-frescor-canal-diario ; echo "exit=$?"` → 1, com `jurisprudencia`/`sumulas` em `[OK]` citando **2026-09-10** (MEDIDO).
- **AÇÃO** Duas correções:
  1. **Sinônimos** em `status_por_fonte_por_dia`: normalizar `registro.get("fonte")` com
     `re.sub(r'\s*-\s*', '-', fonte)`. **Nunca reescrever o ledger**: as linhas de 09-11 a 09-15 com
     `stj - precedentes` são verdade histórica (A4).
  2. **Fuso**: comparar contra a data **local** (`America/Sao_Paulo`), não `datetime.now(timezone.utc).date()`.
     O ledger grava UTC, mas a *cadência* medida é a da onda, que é local — com `TOLERANCIA_DIAS_CADENCIA = 1`
     a folga inteira queima a partir das 21:00 local (medido: passou exatamente na borda hoje).
- **DEPOIS**
  ```bash
  tools/check-frescor-canal-diario ; echo "exit=$?"
  # esperado: jurisprudencia e sumulas passam a citar a data de HOJE (não 2026-09-10);
  # diarios segue REPROVA (defeito real, §C); noticias [OK] sem depender da borda do fuso.
  ```
- **SE NÃO VIER** `jurisprudencia` ainda em 2026-09-10 depois do sinônimo ⇒ não é o nome: a onda rodou com o
  arquivo corrompido e gravou ZERO coletas naquele canal. O passo 2 é a causa; volte a ele.
- **ROLLBACK** Para frente.

### 6. Commit LEVE de P2-shell (sem Go no índice)

- **ANTES** `git diff --cached --name-only` vazio; `git status --porcelain tools/` com os 3 arquivos.
- **AÇÃO** `add` por caminho exato, `commit` em invocação **separada**:
  ```bash
  git add tools/run-daily-content
  git add tools/check-frescor-canal-diario
  git add tools/test_run_daily_content_chaves.sh
  git commit -F /tmp/msg-p2-shell.txt
  ```
- **DEPOIS** `git log -1 --stat` com 3 arquivos; `git status --porcelain go.mod go.sum` vazio.
- **SE NÃO VIER** Reprovação em `check-go-index-compile-closure` com índice sem Go = índice sujo de OUTRA sessão;
  `git diff --cached --name-only` diz quem. **Nunca** `--no-verify`; escopeie com pathspec
  (`git commit -F msg -- tools/…`, que não toca a worktree) ou espere.
- **ROLLBACK** Para frente.

### 7. Commit PESADO de P2-Go (a regra do gate)

- **ANTES** Hora fora de 04:47–05:50; `cat /proc/loadavg`.
- **AÇÃO**
  ```bash
  flock /tmp/opt-wiki-agent-heavy.lock -c 'cd /opt/wiki && \
    git add internal/shellscriptquality/quality.go internal/shellscriptquality/quality_test.go && \
    git commit -F /tmp/msg-p2-gate.txt'
  ```
- **DEPOIS** `./tools/check-shell-script-quality` sai **0**.
- **SE NÃO VIER** Ver o SE NÃO VIER do passo 1.
- **ROLLBACK** Para frente. Sem reatestação: `internal/shellscriptquality` está FORA do grafo (A15).

---

# §B — P1 · DESTRAVAR A COLETA DO STJ

### 8. Congelar a evidência em `testdata/` — em LF, com o CRLF reconstruído no teste

- **ANTES** `ls internal/stjacordaos/testdata/` → 2 arquivos (MEDIDO).
- **AÇÃO** Uma requisição com a identidade do projeto (espaçar ≥10 s de qualquer outra à fonte),
  e gravar **em LF**, porque `core.autocrlf = input` normalizaria de todo jeito e `.gitattributes`
  proíbe `-text` (A17):
  ```bash
  UA='Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; coleta-oficial)'
  curl -sS -A "$UA" --max-time 60 \
    'https://dadosabertos.web.stj.jus.br/dataset/7107650a-f26c-4900-bffd-4492af6361cf/resource/5176e318-5de1-4d28-8931-3ee31fd9d7d7/download/20240229.json' \
    | tr -d '\r' > internal/stjacordaos/testdata/espelhos-segunda-secao-20240229-ilegivel.json
  ```
- **DEPOIS**
  ```bash
  wc -c internal/stjacordaos/testdata/espelhos-segunda-secao-20240229-ilegivel.json   # 576 (MEDIDO)
  sha256sum internal/stjacordaos/testdata/espelhos-segunda-secao-20240229-ilegivel.json
  # 3c4dd3c5e9a7980f041d9d01816c76b480527316774b49a74f775364a074b8c9 (MEDIDO)
  ```
  O teste reconstrói `\n`→`\r\n` e assere `sha256 == ea2537c36c1e11d5206f7cee7b82178fc455cb8832cd7110a1acc807b7da9b46`,
  que é o corpo servido pelo STJ. Round-trip verificado: **True** (MEDIDO); as duas formas falham no parser de
  modo idêntico (`Expecting ',' delimiter: line 24`).
- **SE NÃO VIER** sha diferente ⇒ a fonte consertou o arquivo. O defeito de abort continua existindo (o próximo
  quebrado o aciona): mantenha a fixture com os bytes medidos aqui e declare no cabeçalho do teste que ela
  **reproduz o corpo medido em 2026-09-15**, com os dois shas.
- **ROLLBACK** Não apagar — é evidência. Fonte consertada ⇒ acrescente o corpo novo ao lado.

### 9. Escrever o teste que REPROVA contra o código de hoje (controle negativo grátis)

- **ANTES** `./tools/go-modern test -count=1 ./internal/stjacordaos/` → ok, 0,539 s (MEDIDO).
- **AÇÃO** Em `coleta_test.go`, `TestUmaCompetenciaIlegivelNaoDerrubaODatasetInteiro`, sobre o harness
  `servidorEspelhandoOSTJ` já existente (acrescentando um caso no `mux` que devolve o fixture para UMA
  competência do meio). Asserções: (i) `err == nil`; (ii) os meses BONS depois do ilegível foram lidos;
  (iii) `cursor.JaColetado(slug, "<ilegível>") == false` — o cursor não pode mentir;
  (iv) `quarentena.jsonl` tem a linha com `dataset, competencia, url, sha256, bytes, erro, quarentenado_em`.
- **DEPOIS**
  ```bash
  ./tools/go-modern test -count=1 -run TestUmaCompetenciaIlegivel ./internal/stjacordaos/
  # esperado FALHA — coleta.go:176-178 ainda retorna erro. É o controle negativo.
  ```
- **SE NÃO VIER** Teste PASSANDO contra o código de hoje ⇒ não exercita o caminho. Imprima `err` e `rel` antes de asserir.
- **ROLLBACK** n/a.

### 10. Corrigir `internal/stjacordaos/coleta.go:175-178` — quarentenar e SEGUIR

- **ANTES** `sed -n '173,180p' internal/stjacordaos/coleta.go` mostra `return rel, fmt.Errorf(…)` (MEDIDO).
- **AÇÃO** Cinco peças, mesmo commit:
  1. `:175-178`: em vez de `return`, gravar a quarentena, `rel.Ilegiveis++` e `continue`.
     **Não** chamar `cursor.Registra` — o cursor significa "coletado", e marcá-lo faria o cursor mentir
     e apagaria a chance de a fonte consertar.
  2. `Relatorio`: campos `Ilegiveis int` e `Quarentenados int`.
  3. `internal/stjacordaos/quarentena.go`: `LinhaQuarentena{Dataset,Competencia,URL,ETag,LastModified,SHA256,Bytes,Erro,QuarentenadoEm}`,
     append em `filepath.Join(cfg.Raiz,"quarentena.jsonl")`, + `CarregaQuarentena(raiz)`.
  4. **Revalidação condicional**: antes do `Busca`, competência em quarentena e `!cfg.Refazer` ⇒ mandar o
     `If-None-Match`/`If-Modified-Since` gravados. 304 ⇒ `rel.Quarentenados++` e `continue` (custo diário:
     1 requisição, 0 bytes). 200 com sha diferente ⇒ tentar parsear de novo.
  5. Em ENSAIO (`!cfg.Aplicar`) **não escrever** `quarentena.jsonl`; só contar.
- **DEPOIS**
  ```bash
  ./tools/go-modern build ./internal/... ./cmd/...
  ./tools/go-modern test -count=1 ./internal/stjacordaos/    # ok, TODOS os testes, inclusive o novo
  ```
- **SE NÃO VIER** Se `TestColetaRespeitaOTetoDeRecursosPorExecucao` quebrar, é porque você incrementou
  `RecursosLidos` para o ilegível. Decisão explícita: **ilegível NÃO é recurso lido** (não produziu espelho);
  use `rel.Ilegiveis`.
- **ROLLBACK** Para frente. Fora do grafo (A15).

### 11. Criar o gate `coleta-stj-cobertura` — o que teria pego "6 de 10" no dia 1

**INSTRUMENTO A CRIAR.** Nome livre (medido: 361 gates registrados). Registro em `var Names` **e** `case` no
dispatcher — `dispatcher_orfao_test.go` varre por AST nos **dois** sentidos e reprova quem faltar num lado.
Lê `data/corpus/jurisprudencia/stj-espelhos/{cursor.json,manifest.jsonl,quarentena.jsonl,execucoes.jsonl}`
e `stjacordaos.DatasetsEspelhos`. Grava **nada**. Exit pelo `Report.Messages()`.

**Peça obrigatória que o A21 revelou:** `coletado_em` do manifesto **não avança em execução toda-304**
(`coleta.go:169-172` faz `continue` antes de gravar). Sem mais nada, "timer desligado" e "nada novo na fonte"
ficam indistinguíveis. Então `Coleta` passa a escrever **uma linha de resumo por execução** em
`execucoes.jsonl` (`iniciada_em, terminada_em, datasets, requisicoes, recursos_lidos, nao_modificados,
gravados, ilegiveis, quarentenados`) — inclusive quando tudo deu 304 — e é dela que o gate lê vivacidade.

**Veredito por FLUXO, não por nível** (precedente `gate-vermelho-por-estoque-que-nada-drena`):
- linha informativa, nunca reprova sozinha: `cobertura: N/10 datasets com competência; faltam M`
  (hoje seria `4/10; faltam 392` — MEDIDO/DERIVADO);
- **REPROVA** se (a) a última linha de `execucoes.jsonl` é mais velha que **2×** o período do timer (2 dias)
  — a coleta parou de rodar; ou (b) houve execução mas `recursos_lidos + nao_modificados == 0` com `faltam > 0`
  — rodou e não drenou; ou (c) dataset da lista canônica com **0** competências e **nenhuma** linha de quarentena
  que o explique; ou (d) competência em quarentena não revalidada na execução mais recente.
- **Controle positivo obrigatório antes do zero**: o gate imprime os 10 slugs que leu e as chaves do cursor.
  Filtro por chave errada devolveria "nada faltando" em silêncio (precedente `varredura-com-campo-inexistente`).

- **ANTES** `grep -c '"coleta-stj-cobertura"' internal/checks/checks.go` → 0.
- **AÇÃO** Escrever `internal/checks/coleta_stj_cobertura.go` + registro + teste (com fixture de cursor a 4/10).
- **DEPOIS**
  ```bash
  ./tools/go-modern run ./cmd/check coleta-stj-cobertura ; echo "exit=$?"
  # HOJE, antes da recoleta: REPROVA por (c) — 6 datasets em zero. É o veredito CERTO.
  ./tools/go-modern test -count=1 ./internal/checks/
  ```
- **SE NÃO VIER** Exit 0 hoje ⇒ está lendo cursor ou lista errados. Imprima `len(DatasetsEspelhos)` (10) e
  as chaves de `cursor.datasets` (4) antes de decidir.
- **ROLLBACK** Para frente.

### 12. Commit PESADO de P1-Go

- **AÇÃO**
  ```bash
  flock /tmp/opt-wiki-agent-heavy.lock -c 'cd /opt/wiki && \
    git add internal/stjacordaos/coleta.go internal/stjacordaos/quarentena.go \
            internal/stjacordaos/coleta_test.go internal/stjacordaos/quarentena_test.go \
            internal/stjacordaos/testdata/espelhos-segunda-secao-20240229-ilegivel.json \
            internal/checks/coleta_stj_cobertura.go internal/checks/checks.go \
            internal/checks/coleta_stj_cobertura_test.go && \
    git commit -F /tmp/msg-p1-go.txt'
  ```
- **DEPOIS** `git log -1 --stat`; `./tools/check-validator-attestation` segue verde (nada a reatestar, A15);
  `git status --porcelain internal/stjacordaos/testdata/` **vazio** (se aparecer modificado, o CRLF voltou — A17).
- **SE NÃO VIER** Reprovação em `check-redesocial-completude` é gatilho de `^internal/` (pre-commit:300):
  leia o veredito, não o nome. Exit 75 do guardião = lock de build alheio; vira AVISO, não barra.
- **ROLLBACK** Para frente.

### 13. **A cadeia de extração VEM ANTES da recoleta** — 81,4% do ganho, sem esperar 67 min

**Por que esta é a ordem, e não a inversa:** (i) o parser não depende de nada novo — roda sobre os
**60.221 registros já no disco** e responde por 81,4% da promoção (A9); (ii) rodar em paralelo com a coleta é
**corrida de decodificador**: o coletor faz `O_APPEND` em `registros-*.jsonl` com registros de ~11 KB
(acima do que uma escrita atômica garante) enquanto o parser e o `enfileirar-extracoes` fazem `json.Decode`
nos mesmos arquivos e **abortam** em linha parcial (`%s: %w`). Então: extração → coleta → extração do delta.

- **ANTES**
  ```bash
  wc -l data/ai/dispositivos_promovidos.jsonl data/ai/extracoes_dispositivos.jsonl   # 35.082 e 44.160 (MEDIDO)
  cat data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl | wc -l              # 60.221 (MEDIDO)
  /home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3 \
    "file:$PWD/data/ai/fila.sqlite?mode=ro" ".timeout 5000" \
    "SELECT tipo,estado,COUNT(*) FROM tarefa GROUP BY 1,2 ORDER BY 3 DESC;"
  # MEDIDO: extrair_dispositivos|pendente|34.166 · concluida|8.322 · erro|39 · executando|3
  ```
  Use **este** `sqlite3` (é o único da máquina, fora do PATH das units) e **nunca** `cerebro status`,
  que abre a fila sem `mode=ro` e roda DDL no banco do worker vivo.
- **AÇÃO** Nesta ordem, ensaio antes de cada aplicação:
  ```bash
  ./tools/go-modern run ./cmd/generate-extracao-por-parser                 # ENSAIO (padrão)
  ./tools/go-modern run ./cmd/generate-extracao-por-parser -aplicar
  ./tools/go-modern run ./cmd/generate-writeback-extracoes -dry-run
  ./tools/go-modern run ./cmd/generate-writeback-extracoes
  ./tools/go-modern run ./cmd/cerebro enfileirar-extracoes
  ```
  A ordem sai do cabeçalho de `generate-extracao-por-parser/main.go:1-27`: o parser grava `modelo:"parser"`,
  o writeback promove para o corpus, e só então `enfileirar-extracoes --so-sem-referencias` (padrão `true`)
  vê o campo preenchido e **não reenfileira** o já resolvido. Inverter faz o cérebro reprocessar a 43,6 s/tarefa.
- **DEPOIS** — **atenção: `pendente` NÃO cai** com isto. `Fila` não tem função que apague ou cancele tarefa
  (A18: só `Enfileirar` INSERT OR IGNORE, `Concluir`, `Falhar`, `Recuperar`, `Reabrir`, `AtualizaPrioridade`).
  As provas certas são três:
  ```bash
  wc -l data/ai/dispositivos_promovidos.jsonl     # A MEDIR: > 35.082
  python3 -c "
  import json,collections;c=collections.Counter()
  for l in open('data/ai/dispositivos_promovidos.jsonl'):
      try: c[json.loads(l).get('modelo')]+=1
      except: pass
  t=sum(c.values());print({k:(v,f'{100*v/t:.1f}%') for k,v in c.items()})"
  # HOJE parser 28.559 (81,4%) · qwen3.5:4b 6.523 (18,6%) — MEDIDO. Esperado: share do parser SOBE.
  ```
  e, na saída do `enfileirar-extracoes`, a linha `writeback: N promoção(ões) no artefato, M aplicada(s) ao
  corpus carregado` (`cmd/cerebro/main.go:710-714`) com **M > 0**;
  e o `pendente` **não subir além de** `34.166 − concluídas no intervalo + registros novos sem referência`.
- **SE NÃO VIER** `M == 0` ⇒ promoção que não casa com acórdão nenhum é **dado órfão**: confira
  `stjacordaos.CarregaSobreposicao` e a chave (`id_fonte`/`texto_sha256`) antes de culpar o parser.
  Se `pendente` subir sem registro novo, `--so-sem-referencias` está lendo campo que o writeback não preencheu.
- **ROLLBACK** Os três artefatos são append-only com "última linha por chave vence": desfazer é promover de novo.
  Para frente.

### 14. Primeira prova CONTRA A FONTE VIVA: ensaio no dataset que morre

- **ANTES**
  ```bash
  python3 -c "import json;d=json.load(open('data/corpus/jurisprudencia/stj-espelhos/cursor.json'))['datasets'];print({k.split('acordaos-')[1]:len(v) for k,v in d.items()})"
  # {terceira-turma:52, quarta-turma:52, segunda-secao:21, primeira-turma:3} (MEDIDO)
  ```
- **AÇÃO** ENSAIO (o padrão do comando é ensaio: lê a fonte, não grava). A forma com hífen está correta —
  `main.go:74-75` + `:166` normalizam com `strings.ReplaceAll(limpa,"-","")` (A20):
  ```bash
  tools/collect-stj-acordaos --dataset espelhos-de-acordaos-segunda-secao \
    --desde 2024-02-01 --ate 2024-04-30 --max-recursos 5 --timings
  ```
- **DEPOIS** A saída cita `20240229` como ilegível/quarentenada e **segue** para `20240331` e `20240430`;
  `echo $?` = **0**. E:
  ```bash
  git status --porcelain data/corpus/   # VAZIO — ensaio que grava é ensaio que mente
  ```
- **SE NÃO VIER** Exit 1 com `invalid character '}' after array element` ⇒ o binário de
  `.cache/go-cmd-bin/` está velho. Exit **75** com `source/toolchain/binary identity changed` é proteção
  correta de `run-go-cmd-cached`: termine o passo 12 antes.
- **ROLLBACK** n/a (ensaio).

### 15. Aplicar no dataset que morre — destrava segunda-secao

- **AÇÃO** (janela fora de 09:40–10:17)
  ```bash
  tools/collect-stj-acordaos --aplicar --dataset espelhos-de-acordaos-segunda-secao \
    --max-recursos 60 --timings
  ```
  60 > 31 restantes ⇒ cobre o dataset inteiro: 31×10 s + 1 página ≈ **320 s**, dentro de
  `WIKI_GO_CMD_TIMEOUT_SECONDS=1500`.
- **DEPOIS**
  ```bash
  python3 -c "import json;print(len(json.load(open('data/corpus/jurisprudencia/stj-espelhos/cursor.json'))['datasets']['espelhos-de-acordaos-segunda-secao']))"
  # esperado 51 = 52 recursos − 1 em quarentena (DERIVADO; A MEDIR NA EXECUÇÃO)
  wc -l data/corpus/jurisprudencia/stj-espelhos/quarentena.jsonl    # 1
  tail -1 data/corpus/jurisprudencia/stj-espelhos/quarentena.jsonl | python3 -m json.tool | grep -E 'competencia|sha256|bytes'
  # competencia 20240229 · sha256 ea2537c3… · bytes 599
  ```
- **SE NÃO VIER** 51 não veio e o cursor parou em outra competência ⇒ há um **segundo** arquivo quebrado.
  Não é falha do plano: `quarentena.jsonl` agora traz sha e erro de cada um. Siga.
- **ROLLBACK** Cursor e manifesto são append/merge; desfazer é recoletar. Para frente.

### 16. Recuperar os 7 datasets restantes — 1 execução por dataset, sequencial

**A espera é externa e medida: Crawl-Delay 10 s declarado no `robots.txt` do STJ** (confirmado no journal:
`robots: /dataset/ permitido, Crawl-Delay 10s`). 392 competências × 10 s = **3.920 s = 65,3 min**, + 10 páginas
de dataset = **~67 min**. Não há atalho para o relógio da fonte, e acelerar seria desrespeitar o `robots.txt`.
**O atalho é de ORDEM, e já foi tomado:** o §B-13 entregou 81,4% do ganho antes, sem esperar nada.

- **AÇÃO** Sequencial — cada execução ~530 s, muito abaixo dos tetos:
  ```bash
  for d in espelhos-de-acordaos-primeira-turma espelhos-de-acordaos-segunda-turma \
           espelhos-de-acordaos-quinta-turma  espelhos-de-acordaos-sexta-turma \
           espelhos-de-acordaos-primeira-secao espelhos-de-acordaos-terceira-secao \
           espelhos-de-acordaos-corte-especial; do
    echo "=== $d $(date -Is) ==="
    tools/collect-stj-acordaos --aplicar --dataset "$d" --max-recursos 60 --timings
    echo "exit=$?"
  done
  ```
  **Por que não `--max-recursos 400` de uma vez:** 3.920 s estoura `WIKI_GO_CMD_TIMEOUT_SECONDS=1500` e
  `WIKI_HEAVY_TIMEOUT_SECONDS=1800`. Elevar o timeout seria mascaramento — e é desnecessário: o cursor torna
  a execução retomável por construção.
- **DEPOIS**
  ```bash
  python3 -c "
  import json;d=json.load(open('data/corpus/jurisprudencia/stj-espelhos/cursor.json'))['datasets']
  print(len(d),'datasets'); [print(f'  {k}: {len(d[k])}') for k in sorted(d)]"
  # esperado 10 datasets, cada um com 51 ou 52 (A MEDIR NA EXECUÇÃO)
  cat data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl | wc -l   # HOJE 60.221; depois: A MEDIR
  ./tools/go-modern run ./cmd/check coleta-stj-cobertura ; echo "exit=$?"  # 0
  ```
- **SE NÃO VIER** Exit 75 ⇒ colisão com o timer ou com outra sessão no mesmo escopo;
  `run-heavy-throttled` imprime `lock_scope=` e o dono. Reoriente para o §D e volte — **nunca** mate o dono do lock.
- **ROLLBACK** Para frente.

### 17. Extração do DELTA + commit dos dados

- **AÇÃO** Repetir o §B-13 **agora que a coleta parou** (sem corrida de decodificador), e commitar:
  ```bash
  ./tools/go-modern run ./cmd/generate-extracao-por-parser -aplicar
  ./tools/go-modern run ./cmd/generate-writeback-extracoes
  ./tools/go-modern run ./cmd/cerebro enfileirar-extracoes
  git add data/corpus/jurisprudencia/stj-espelhos/cursor.json
  git add data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl
  git add data/corpus/jurisprudencia/stj-espelhos/quarentena.jsonl
  git add data/corpus/jurisprudencia/stj-espelhos/execucoes.jsonl
  git add data/ai/dispositivos_promovidos.jsonl
  git commit -F /tmp/msg-p1-dados.txt
  ```
  (`registros-*.jsonl` são ignorados por `.gitignore:697` — verificado.)
- **DEPOIS** `git status --porcelain data/corpus/ data/ai/dispositivos_promovidos.jsonl` → vazio.
- **SE NÃO VIER** `quarentena.jsonl` e `execucoes.jsonl` são arquivos NOVOS e **têm** de entrar no commit da
  própria frente (produto não fica untracked). Se o `.gitignore` os pegar, acrescente a exceção no mesmo commit.
- **ROLLBACK** Para frente.

### 18. Não tocar o `ExecStart` da unit

A ordem atual (privado primeiro) veio de medição em 2026-09-08 (TF-IDF mediana 0,020 contra a Primeira Turma).
**Com a quarentena ela deixa de importar para a sobrevivência** — nenhum dataset bloqueia o seguinte.
Editar `ops/systemd/*.service` marca `NeedDaemonReload=yes`, `check-units-instaladas` reprova e
**`deploy-publico` para no passo 0a/7 para TODAS as frentes**. Só toque com motivo e com `daemon-reload` junto.

---

# §C — DIÁRIOS MUNICIPAIS: a resposta medida

**"É TLS nosso, deles, ou rota?" — é DELES, e são DOIS defeitos empilhados, com a causa raiz do nosso lado no meio.**

1. `api.queridodiario.ok.org.br`: **SNI aposentado**. No mesmo IP Cloudflare, SNI `queridodiario.ok.org.br`
   fecha TLSv1.3 com `subject=CN = ok.org.br`, `Verify return code: 0`; SNI `api.…` recebe `alert number 40`
   **antes de qualquer certificado**. Não é a nossa OpenSSL (a mesma pilha fecha o outro SNI no mesmo socket),
   não é rota (mesmo IP e porta), não é versão de TLS (falha igual em 1.2 e 1.3, IPv4 e IPv6). **MEDIDO.**
2. `api.queridodiario.org.br` (o vivo): **oscilando** — 1 de 7 respostas 200, 6 de 6 retentativas 503
   `no available server`. O corpo de 200 **cumpre o contrato**. **MEDIDO.**
3. **Nosso lado, a causa raiz:** `sourceresolve.Resolver` não retenta (`resolve.go:210-214`) e `resolveAPIBase`
   devolve o host MORTO quando a resolução falha. Um único 503 do host vivo joga o coletor contra o SNI
   aposentado — e o erro que chega ao ledger é o do TLS, **sintoma a dois passos da causa**.

### 19. Dar retentativa ao resolvedor (a correção de causa)

- **ANTES**
  ```bash
  sed -n '208,216p' internal/sourceresolve/resolve.go          # status != 200 → continue, sem retry
  tail -2 data/ops/daily_content_collect.jsonl | grep -c 'tls: handshake fail'    # 2 (MEDIDO)
  ```
- **AÇÃO** Quatro peças:
  1. Em `internal/sourceresolve`: retentar **status transitório** (429, 500, 502, 503, 504) por candidato,
     com backoff exponencial e jitter — **reusar** o predicado que `cmd/collect-diarios-municipais` já tem
     (`tetoTentativas=4`, `baseBackoff=2s`, `jitterFracao=0.5`), nunca escrever um segundo.
  2. Registrar **cada tentativa** na `Evidencia` (hoje só a última sobrevive), para a trilha não mentir.
  3. Em `resolveAPIBase`: falha de resolução **não** cai em `apiBase`. Cai na **última base confirmada**,
     persistida em `data/ops/diarios_api_base.json` quando uma resolução dá certo. Sem base confirmada,
     falhar honesto — a postura que o cabeçalho do arquivo já declara.
  4. Corrigir o comentário de `main.go:52` que afirma `robots 200`: **medi 404** (A13).
- **DEPOIS**
  ```bash
  ./tools/go-modern test -count=1 ./internal/sourceresolve/ ./internal/sourcecollect/
  # ENSAIO, com a invocação REAL do COLETORES (A19: -limite é TAMANHO DE PÁGINA, não teto da rodada;
  # -limite 5 exigiria 63 páginas contra tetoPaginas=12 e a rodada falharia sem gravar):
  ./tools/go-modern run ./cmd/collect-diarios-municipais -seco -limite 300 -com-texto 0
  ```
  Esperado: exit **0**, com a saída do próprio comando nomeando a base resolvida
  (`api.queridodiario.org.br`) e a contagem de edições da janela. E então, aplicando:
  ```bash
  ./tools/go-modern run ./cmd/collect-diarios-municipais -limite 300 -com-texto 25
  ls -la data/research/daily/diarios-municipais/ | tail -3     # arquivo do dia, A MEDIR
  ```
  **Não** procure a prova em `data/ops/daily_content_collect.jsonl`: aquela linha é escrita por
  `registra_coleta` dentro de `tools/run-daily-content`, e um `go run` direto não passa por lá.
- **SE NÃO VIER** Se continuar `tls: handshake fail`, o fallback ainda aponta para `apiBase`: imprima a trilha
  de `sourceresolve.Evidencia`, que já carrega URL, status, content-type e sha do corpo por candidato.
  Se o ensaio sair ≠ 0 com "janela não esgotou", **não** suba `tetoPaginas`: é a guarda que impede a marca
  d'água de passar por cima de edição não coletada. O caminho é a retentativa (peça 1).
- **ROLLBACK** Para frente. `internal/sourceresolve` está FORA do grafo (A15).

### 20. Promover o endereço no registry, com a evidência anexada

`content/source_registry.json` ainda declara o host **morto** em `research_url` (linha 1036) e em `alt` (1038)
— MEDIDO. `tools/check-fontes-alcancaveis` varre exatamente esses campos: hoje ele mede um endereço aposentado.

- **AÇÃO** Promover o endereço com evidência, que é o que o cabeçalho do gate (linha 34) exige
  ("Promover endereco novo e ato deliberado com evidencia"). A evidência são as duas medições desta sessão:
  SNI sem certificado; e o 200 de `api.queridodiario.org.br` com `total_gazettes 311`, `territory_id 2909307`,
  `date 2026-09-14`, `scraped_at 2026-09-14T22:20:35`.
- **DEPOIS** `tools/check-fontes-alcancaveis 2>&1 | grep -i queridodiario` → alcançável (A MEDIR).
- **SE NÃO VIER** A oscilação de A11 fará o gate piscar. O veredito para esta fonte tem de exigir **k de n**
  tentativas, nunca 1 de 1 — senão vira alarme falso e alguém desliga o gate (precedente `check-efeito-nos-bots`).
- **ROLLBACK** Para frente; o valor anterior está em `git show HEAD:content/source_registry.json`.

### 21. Commit de §C

```bash
flock /tmp/opt-wiki-agent-heavy.lock -c 'cd /opt/wiki && \
  git add internal/sourceresolve/resolve.go internal/sourceresolve/resolve_test.go \
          cmd/collect-diarios-municipais/main.go content/source_registry.json && \
  git commit -F /tmp/msg-diarios.txt'
```
Registry no MESMO commit do código: endereço novo e lógica que o alcança são uma coisa só, e separá-los deixa
uma janela em que o registry aponta para host que o binário não resolve.

---

# §D — P3 · MATAR OS ÓRFÃOS

**Medido (A14): 8 produtores de página em `cmd/generate-*-pages`, dos quais 5 têm invocação real
(`run-daily-content:369-373`) e TRÊS são órfãos — `generate-acordao-pages`, `generate-lei-artigo-pages` e
`generate-entity-pages`, este último não nomeado pelo plano.** Mais `tools/generate-propostas-reescrita`
(só citado pelo próprio teste) e `tools/generate-first-published-at` (citado por ninguém). **10 linhas de registro,
5 ativas, 5 a triar.**

### 22. Criar `ops/produtores-de-pagina.jsonl`

**INSTRUMENTO A CRIAR.** Uma linha por produtor: `produtor`, `artefato` (o que escreve), `runner`
(unit/timer/script que o **INVOCA**; vazio = órfão declarado), `gate_a_jusante`, `estado`
(`ativo` | `orfao_declarado` | `aposentado`), `motivo`, `medido_em`.
`orfao_declarado` é legítimo **com motivo escrito e data**; o proibido é órfão **silencioso**.

### 23. Criar o gate `produtor-orfao` em `internal/checks`

**INSTRUMENTO A CRIAR.** Nome livre (medido). Registro em `Names` **e** `case` no dispatcher
(`dispatcher_orfao_test.go` varre por AST nos dois sentidos). Lê `ops/produtores-de-pagina.jsonl`,
`ops/systemd/*`, `tools/*`, `.githooks/*`. Grava nada.

**Escopo FECHADO, não amplo** (o amplo repetiria o padrão `gate-vermelho-por-estoque-que-nada-drena`):
o conjunto é `cmd/generate-*-pages` — **8 hoje, contados** — mais os dois produtores de `tools/` que o P3 nomeia.

**A asserção que separa catalogar de fechar:** o gate casa **INVOCAÇÃO**, nunca menção —
`$GO run ./cmd/<nome>`, `ExecStart=…<nome>`, `"$ROOT/tools/<nome>"`, `./cmd/<nome>` em posição de comando —
e **não** o nome dentro de comentário ou de string de prosa. É exatamente esse falso positivo que existe hoje
em `run-daily-content:446-447` e faria os três órfãos passarem (A14).

Vereditos: REPROVA produtor do conjunto ausente do registro · REPROVA linha cujo `runner` declarado **não
invoca** o produtor (registro que mente) · REPROVA produtor `ativo` sem `gate_a_jusante` ·
PASSA `orfao_declarado` com `motivo` não vazio e `medido_em` presente.

- **ANTES** `grep -c '"produtor-orfao"' internal/checks/checks.go` → 0;
  `ls cmd | grep -cE '^generate-.*-pages$'` → **8** (MEDIDO).
- **AÇÃO** Escrever o gate, o registro com as 10 linhas e o teste — com fixture de "menção em comentário"
  que **não** pode contar como invocação.
- **DEPOIS**
  ```bash
  ./tools/go-modern run ./cmd/check produtor-orfao ; echo "exit=$?"   # 0 com as 10 linhas preenchidas
  ./tools/go-modern test -count=1 ./internal/checks/
  ```
- **SE NÃO VIER** Exit 0 **antes** de escrever o registro ⇒ o casamento aceita comentário. Rode o gate contra
  uma cópia em `/tmp` que contenha **apenas** as duas linhas de comentário de `run-daily-content:446-447`
  e exija REPROVA.
- **ROLLBACK** Para frente.

### 24. Commit de P3

```bash
flock /tmp/opt-wiki-agent-heavy.lock -c 'cd /opt/wiki && \
  git add ops/produtores-de-pagina.jsonl internal/checks/produtor_orfao.go \
          internal/checks/checks.go internal/checks/produtor_orfao_test.go && \
  git commit -F /tmp/msg-p3.txt'
```

---

# §E — O QUE SE MEDE NA PRODUÇÃO AO VIVO

**Este bloco não publica página nenhuma.** Sem `--ressemear`, sem purga de borda, sem coorte nova. Ele muda
o INSUMO (corpus, fila, ledgers) e as GUARDAS. Dizer isso é mais honesto que inventar prova de SEO onde não houve
publicação.

### 25. Produção de pé (30 s, zero espera)

```bash
UA='Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)'
curl -sS -A "$UA" -H 'X-Warming-Request: true' -D - -o /dev/null --max-time 20 \
  -w '\nhttp=%{http_code} t=%{time_total}\n' https://wikijuridica.com.br/healthz | grep -iE 'cf-cache-status|http='
```
Esperado `http=200` + `cf-cache-status: DYNAMIC` (MEDIDO nesta sessão: 200, 0,202 s, DYNAMIC). `/healthz` está
EXCLUÍDA da Cache Rule e atravessa borda→túnel→nginx→Go toda vez.
**SE NÃO VIER `DYNAMIC`**: a Cache Rule derivou e toda sonda de saúde pela borda passou a mentir — achado maior
que este bloco; trate primeiro.

### 26. Que a onda use o arquivo corrigido — **sem publicar nada**

A prova instantânea de que `--somente-noticias` deixa 1 coletor e 1 gerador é o **teste do §A-4**, que roda em
menos de 1 s contra os bytes reais. Use-o.
`tools/run-daily-content --somente-noticias` **não** é verificação: ele roda as etapas 3 a 9 na íntegra —
commit do portfólio (5/9), commit das páginas (6/9), **publicação transacional (8/9)**, reload do servidor e
IndexNow. É publicação em produção e só se dispara quando houver conteúdo a publicar, com o runbook de publicação,
não como prova de P2. Duas armadilhas medidas se ele for disparado: sai **0 sem fazer nada** se o timer das 12:20
estiver com o flock `/tmp/wiki-daily-content.lock`; e falha em 0a-bis se um `--seco` anterior deixou
`v2_pages`/`portfolio_v2` sujos (§A-3).

Se a pergunta é só "a onda gravou o nome canônico?", ela se responde na primeira execução agendada, lendo o ledger
— sem esperar nada nem publicar nada:
```bash
tail -6 data/ops/daily_content_collect.jsonl | python3 -c "
import sys,json
for l in sys.stdin:
    d=json.loads(l); print(d['medido_em'][:19], repr(d['fonte']), d['exit_code'])"
```
Esperado: `'noticias-oficiais'`, `'stj-precedentes'` etc. **sem espaços**.

### 27. Comportamento dos bots de IA — o que É observável agora

O log do nginx tem **lag ZERO** e retenção real medida de **30 dias**. É ele que responde "quem entrou e o que
levou" sem janela de horas:
```bash
LC_ALL=C grep -a "$(LC_ALL=C date -d '60 min ago' '+%d/%b/%Y:%H')" /var/log/nginx/wikijuridica/access.log \
 | grep -c -iE 'GPTBot|PerplexityBot|ClaudeBot|OAI-SearchBot|ChatGPT-User|Googlebot|bingbot|Applebot'
```
**Duas armadilhas medidas:** `LC_ALL=C` é obrigatório — `date +%b` em pt_BR devolve `set` e o nginx escreve `Sep`,
e a comparação falha **em silêncio** devolvendo zero. E conte **linha** (`grep -c`), nunca ocorrência (`grep -oE`):
o UA do PetalBot casa duas vezes por requisição.

Referência desta sessão (20:00–21:14 -03 de 2026-09-15, 950 linhas de origem): Applebot 37, bingbot 4,
Perplexity 3, OAI-SearchBot 3, ChatGPT-User 3, Googlebot 2.

**O que NÃO se conclui daqui:** ausência na origem não é ausência. Com `s-maxage=604800` a maior parte do rastreio
nunca toca a origem — medido: GPTBot leu 686 rotas na borda e **0** na origem no mesmo lote. Para presença na borda,
`data/ops/crawl_coverage_state.json` → `crawlers_verified.<bot>.paths_first_seen`; e o atalho para não esperar o
timer de 01:11 é rodar `tools/measure-crawl-coverage` sob demanda, que é consulta GraphQL.

### 28. Estado do cérebro depois da cadeia (4 comandos, 2,1 s somados)

```bash
systemctl show wikijuridica-cerebro.service -p ActiveState -p SubState -p NRestarts -p MainPID
curl -sS --max-time 5 http://127.0.0.1:11434/api/ps | python3 -m json.tool | grep -E '"model"|"size"|"size_vram"'
/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3 "file:$PWD/data/ai/fila.sqlite?mode=ro" \
  ".timeout 5000" "SELECT estado,COUNT(*) FROM tarefa WHERE tipo='extrair_dispositivos' GROUP BY 1;"
cat /proc/loadavg
```
Esperado hoje: `active/running`, `NRestarts=1`, residente `qwen3.5:4b` 3,01 GiB `size_vram=0`.
`pendente` medido antes: **34.166** — e, por A18, ele **não cai** com o parser; o que muda é a taxa de
reenfileiramento. **Declare a carga junto de qualquer tok/s**: `CargaMax=12` estava mordendo nesta sessão
(loadavg 12,77 medido), e todo tok/s medido sob carga é **teto inferior**.

---

# §F — O QUE O ADVISOR MUDOU

Nove pontos. **Um refutado por medição primária; oito adotados**, um deles com correção melhor que a proposta.

1. **ADOTADO (§B-13).** Ele disse que "`pendente` tem de CAIR" era falso. Medi: `grep 'func (f \*Fila)'
   internal/cerebro/fila.go` não tem nenhuma função que apague ou cancele tarefa, e `enfileirar-extracoes`
   só chama `Enfileirar` (INSERT OR IGNORE) e `AtualizaPrioridade`. Troquei a asserção pelas três certas:
   `dispositivos_promovidos.jsonl` cresce, `M > 0` na linha de writeback, e `pendente` não sobe além do delta.
2. **ADOTADO, e virou reordenação do bloco.** Corrida de decodificador: o coletor faz `O_APPEND` de registros
   de ~11 KB enquanto o parser faz `json.Decode` nos mesmos arquivos. A extração passou para **antes** da coleta
   (§B-13), e o delta depois (§B-17) — mesma sessão, zero espera acrescentada.
3. **REFUTADO POR MEDIÇÃO.** Ele suspeitou que `--desde 2024-02-01` comparasse string com hífen contra
   `AAAAMMDD` e lesse zero recursos com exit 0. Li: `cmd/collect-stj-acordaos/main.go:74-75` chama
   `competencia(desde)` e `:166` faz `strings.ReplaceAll(limpa, "-", "")`. A forma com hífen está correta.
   Registrado como A20 com a linha.
4. **ADOTADO e corrigido para além do pedido.** Ele mandou escopar o gate a `cmd/generate-*-pages` e estimou ~7.
   Medi **8**, e achei um órfão que nem o plano nem ele nomeavam: **`generate-entity-pages`**. São 3 órfãos de
   página, não 2, e 10 linhas de registro.
5. **ADOTADO.** `-limite` do coletor de diários é **tamanho de página** (default 1000), não teto da rodada;
   com 311 gazetas, `-limite 5` exigiria 63 páginas contra `tetoPaginas=12` e a rodada falharia sem gravar.
   Troquei pela invocação real do `COLETORES` e achei o `-seco` que aquele comando já tem. E tirei a verificação
   por `daily_content_collect.jsonl`, que é escrito por `registra_coleta` dentro de `run-daily-content` e não por
   um `go run` direto.
6. **ADOTADO.** `--somente-noticias` é publicação transacional completa (etapas 3 a 9), não prova. §E-26 foi
   reescrito: a prova de P2 é o teste do §A-4. Acrescentei o aviso, que o advisor levantou, de que `--seco`
   deixa `v2_pages`/`portfolio_v2` sujos e **bloqueia `deploy-publico` para todas as frentes** até a onda commitá-los.
7. **ADOTADO.** `coleta.go:169-172` faz `continue` no 304 **antes** de gravar o manifesto, então `coletado_em`
   não distingue "timer desligado" de "nada novo na fonte". O gate ganhou uma fonte nova: `execucoes.jsonl`,
   uma linha de resumo por execução, inclusive quando tudo deu 304.
8. **ADOTADO com correção melhor.** Ele apontou o risco de eol. Medi: `core.autocrlf = input`, e o blob que o git
   guardaria tem **576 bytes**, não 599 (`git cat-file -s`), com aviso explícito do git. `.gitattributes` proíbe
   `-text`. Em vez de asserir os bytes commitados (a sugestão dele), gravo o fixture **em LF** e o teste
   **reconstrói** o CRLF — round-trip verificado `True`, as duas formas falham no parser de modo idêntico, e a
   proveniência byte-exata da fonte fica provada pelos dois shas (`3c4dd3c5…` em disco, `ea2537c3…` reconstruído).
9. **ADOTADO.** O predicado do gate de chave associativa foi estreitado para blocos `declare -A` e leituras de
   nomes declarados `-A` no mesmo arquivo, com fixture de controle `${v[i+1]}` que **não** pode acusar.

Nada foi trocado em silêncio. O único ponto em que contrariei o advisor (o #3) está registrado com arquivo e linha.

---

## 29. O QUE ESTE BLOCO NÃO MEDIU, E POR QUÊ

| não medido | por quê |
|---|---|
| parede real de cada recoleta de dataset | `--aplicar` muta o corpus; PLAN MODE. O ~530 s/dataset é **DERIVADO** de 52 × 10 s + 1 página. |
| quantos registros os 7 datasets novos trazem | só sai com a coleta feita. A banda 456–565 MB é derivada da mediana/média dos 138 lotes do manifesto. |
| se o parser mantém 81,4% sobre o corpus ampliado | o share atual é MEDIDO (28.559/35.082); o futuro depende dos órgãos criminais, nunca coletados. **A MEDIR** no §B-17. |
| taxa de êxito do host vivo do Querido Diário ao longo do dia | 7 requisições em ~3 min, 1 êxito: amostra, não população — e por isso §C-20 exige veredito por *k de n*. |
| se há um SEGUNDO arquivo quebrado nos 392 | só a coleta diz; `quarentena.jsonl` passa a responder com sha e erro por linha. |
| parede do pre-commit em cada commit | depende da carga; o contrato mediu 14,9 s com índice limpo contra 77,6 s com `internal/v2ingest` no índice. Mantenha o índice limpo entre commits. |
