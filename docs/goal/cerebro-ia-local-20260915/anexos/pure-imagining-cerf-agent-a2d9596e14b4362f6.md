# Varredura: a cadeia real de build e deploy do /opt/wiki

Sessao 2026-09-15, PLAN MODE (somente leitura). Tudo abaixo com arquivo:linha.
Numero sem fonte de medicao esta marcado **nao medido**.

---

## 0. O que eu MEDI nesta sessao (nao li: rodei)

| medicao | valor | como |
|---|---|---|
| `served_sha256` de pagina real com `datePublished` trocado | **IDENTICO** (`ab27922b6f77c85b…` antes e depois) | carreguei `tools/generate-page-content-revision` como modulo e apliquei `neutraliza_datas` + `BLOCOS_DE_NAVEGACAO` sobre `public/jurisprudencia/stj-tema-979/index.html`, com e sem a correcao |
| ocorrencias ISO num HTML de acervo | **12 e 14** (nao 7, como o codigo afirma) | `DATA_ISO_NO_HTML.findall` em 2 paginas de `/jurisprudencia/` |
| borda viva de uma pagina do acervo | `cf-cache-status: HIT`, `age: 27291`, `cache-control: public, max-age=86400, s-maxage=604800` | `curl -D -` com UA de sonda interna contra producao |
| borda da gemea `.md` | `MISS`, `max-age=600, s-maxage=604800` | idem |
| `tools/check-v2-portfolio-pairing` | **3,45 s**; 11.106 intents ativos, 11.438 no portfolio, pareamento OK | `/usr/bin/time` |
| `tools/generate-page-content-revision --purge-targets` | **140,17 s** e **115,07 s** (duas passadas, cargas diferentes); saida de hoje = **6 linhas: 3 rotas HTML + 3 gemeas `.md`** | `/usr/bin/time` + `wc -l` |
| `wikijuridica-daily-content.service` agora | `ExecMainStatus=1` **e** `Result=success`, `KillSignal=15`, `TimeoutStopUSec=90s`, `SuccessExitStatus=0 1` | `systemctl show` |
| `deploy-binario-go` completo, do proprio ledger | **403,1 s** e **409,9 s** (11.158 rotas) | `data/ops/deploy_binario_go.jsonl` |
| `deploy-binario-go --rota` (2 rotas) | 48,9 / 54,3 / 61,0 / 95,9 s | idem |
| `signal.Notify` em `cmd/publish-v2-direct`, `internal/publicrelease`, `cmd/build` | **ZERO ocorrencias** | `grep -rn` nos tres |

---

## 1. Inventario: o que cada passo MUTA, a ordem, e o tempo

### `tools/go-modern` — wrapper, nao muta nada alem do GOCACHE
- Versao do toolchain sai do `go.mod` (`tools/go-modern:16`), fallback literal `go1.26.6` em `:18-19`.
- Injeta `-tags devcmds` em `run` e `test` (`:117`, `:169`) — sem isso, dev-main de `cmd/` falha com "build constraints exclude all Go files".
- Escreve: `$GOCACHE` (regenerável). **Ordem: nenhuma.**

### `tools/deploy-binario-go` — 8 passos, ORDEM CANONICA em 3 copias
`ORDEM_CANONICA` em `:127-136`; `PASSOS` em `:511-560`; `confere_ordem()` em `:563-575` **recusa rodar** (exit 2) se divergirem; a terceira copia esta em `internal/deployordem/deployordem.go` (le o proprio script e o confronta).

| passo | arquivo:linha | muta |
|---|---|---|
| 1 build p/ nome temporario | `:260-276` | `bin/wikijuridica-server.next` |
| 2 validacao ISOLADA | `:279-314` | `var/deploy-binario/<carimbo>/isolado/` (cache, access-log, stage proprios) |
| 3 troca atomica (`os.replace`) | `:317-333` | `bin/wikijuridica-server`, `bin/wikijuridica-server.anterior` |
| 4 socket ANTES do servico | `:336-367` | systemd: `start .socket`, `restart .service` |
| 5 readiness Go **e** nginx | `:370-391` | nada |
| 6 invalidar origem | `:394-422` | `var/nginx/cache` (unlink, lotes de 400 — `LOTE_ORIGEM` `:122`) |
| 7 aquecer origem | `:425-470` | `var/nginx/cache` (enche), `data/ops/origin_cache_warm.jsonl` |
| 8 purgar borda | `:473-508` | Cloudflare + `data/ops/edge_cache_purge.jsonl`, `var/deploy-binario/<c>/rotas-borda.txt` |

Tambem escreve `data/ops/.deploy-em-curso.lock` (`:628-637`, removido por `atexit`) e `data/ops/deploy_binario_go.jsonl` (`:689-706`). **Em `--seco` nao grava lock nem ledger** (`:629`, `:692`) e `roda()` nao executa (`:213`).

### `tools/deploy-publico` — 0a → 7, e **NAO TEM MODO SECO**
Aceita so `--sem-republicar`, `--so-cache`, `--ressemear` (`:225-249`). Nao ha `--seco`/`--dry-run`: **toda invocacao muta.**

| passo | linha | muta |
|---|---|---|
| 0a atestado do validador / fontes do ingress / units | `:266-285` | nada (3 gates read-only, fail-fast) |
| 0a-bis estoque editorial commitado | `:307-323` | nada (le `git status`) |
| 0 reingerir estoque | `:404-458` | `data/editorial/stock_manifest.json`, contentstore, `.agents/runtime/deploy-ingest-*.log` |
| 1 republicar | `:461-469` | **apaga `data/ops/.publish-v2-direct.lock` sem conferir vida** (`:463`), depois `public/`, `content/pages.json`, manifesto, sitemaps |
| 1b JSON-LD | `:485-490` | nada (2,7 s medidos declarados em `:484`) |
| 2 build | `:493-506` | `bin/*.next` (servidor **e** social) |
| 2.5 brotli | `:644-650` | `public/**/*.br` (3m20s com 4 jobs, declarado `:643`) |
| 2.6 indice de percursos | `:677-684` | `content/legal_cocitation_index.jsonl` (~16 s ocioso / ~29 s sob carga, `:675`) |
| 2.7 espelho de temas | `:713-724` | `var/social/social.db` (so INSERT/UPDATE; nunca remove, `:701-702`) |
| 3 parar servico **e socket** | `:726-745` | systemd |
| 4 limpar caches + reload nginx condicional | `:747-851` | apaga `var/on-demand-cache`, `var/nginx/cache`; `cp` do binario; `nginx -t` **sem sudo** (`:820`) e `systemctl reload` so se `INGRESS_MUDOU` |
| 4-bis social | `:864-875` | `mv` do binario social, restart, prova `/readyz` |
| 5 subir | `:878-886` | systemd |
| 5b aquecer origem | `:895-900` | `var/nginx/cache`, ledger |
| 6 purga de borda + reaquecimento dirigido | `:901-1343` | Cloudflare, `data/ops/edge_cache_purge.jsonl`, `data/ops/edge_cache_warm.jsonl` |
| IndexNow incremental | `:1365-1377` | api.indexnow.org (**calado sob `--ressemear`**, `:1365`) |
| registro de revisao | `:1398-1412` | `data/ops/page_content_revision.jsonl` + `..._formula.txt` |
| 7 gates + smoke borda×origem | `:1414-1596` | serie de carencia, serie JSON-LD (`--gravar`) |
| fim: impressao da camada | `:1604-1612` | `data/ops/deploy_layer_fingerprint.json` (**so se o smoke passou**) |

**Tempos reais citados no proprio arquivo, com a data da medicao:** deploy #3 de 2026-09-10 levou **46 min** por causa do reaquecimento (`:139`); a passada de reaquecimento de 22.446 URLs a 12 r/s custa **31 min** (`:140`); deploy #4 purgou 22.414 URLs = 1.868 s (`:1271`); deploy #5 aqueceu 22.392 em 1.866 s (`:1293`).

### `tools/publish-v2-direct` — **NAO EXISTE**
Nao ha arquivo com esse nome em `tools/`. O publicador e `cmd/publish-v2-direct` (4.082 linhas em `main.go`), invocado por `tools/deploy-publico:464` e por `tools/run-daily-content:684`.

### `tools/purge-edge-cache`
- `LOTE = 100` (`:94`), teto `--teto-por-url` default **3000** (`:137-138`): acima dele **degrada em silencio para `purge_everything`** (`:191`, `:205-210`).
- `--dry-run` sai em `:218-220` **antes** de qualquer chamada e antes do ledger. Read-only.
- Muta: Cloudflare + `data/ops/edge_cache_purge.jsonl` (`:241-243`).

### `tools/warm-edge-cache`
- `--rps` default 25 (`:591`), `--concorrencia` 12 (`:592`). `--listar-artefatos` sai em `:633-636` **antes** do lock e de qualquer request → read-only.
- `flock` em `/tmp/opt-wiki-warm-edge-cache.lock` (`:57`): timer periodico PULA se ha outro em voo; `--de-arquivo` **espera** ate 20 min (`:658-662`).
- Muta: cache de borda, `data/ops/edge_cache_warm.jsonl`.

### `tools/warm-origin-cache`
- `--listar-rotas` sai em `:297-305` antes do `/readyz` → read-only. E o **catalogo unico** de rotas dinamicas: `deploy-binario-go:175-198` carrega este arquivo como modulo para nao existirem dois catalogos.
- `VARIANTES_ACCEPT_ENCODING = ("gzip, br", "")` (`:99`) — o nginx guarda **um objeto por variante**.
- Muta: `var/nginx/cache`, `data/ops/origin_cache_warm.jsonl`.

### `tools/generate-page-content-revision` — o coracao do problema do P1b
- `--purge-targets` (`:730-742`) e `--dry-run` (`:764-766`) **nao escrevem**. Sem flag, escreve `data/ops/page_content_revision.jsonl` + `page_content_revision_formula.txt` (`:768-775`).
- `confere_formula()` (`:415-432`) **recusa** (`RECUSADO`, exit 1) se a formula mudou sem `--ressemear` — e `deploy-publico:1407-1409` **aborta o deploy** nesse caso.
- Teto de churn `TETO_CHURN_FRACAO = 0.05` (`:135`); isento para `--ressemear` e `--purge-targets` (`:596`).
- **140,17 s medidos** sobre o acervo de hoje.

### `tools/check-csp-style-hashes` (35 linhas) → `tools/run-check csp-style-hashes --timings`
Read-only. Orcamento declarado no `data/ops/check_performance_ledger.jsonl`: `expected_duration_ms = 20000`. **Roda na suite, nao no caminho do deploy** — quem publica confere por fora.

### `tools/check-v2-portfolio-pairing` (173 linhas, Python)
Read-only (`git ls-tree`/`git show` + disco). **3,45 s medidos.**

### `tools/check-http-smoke` (30 linhas) → `tools/run-check http-smoke`
Orcamento declarado `expected_duration_ms = 100000`. Sonda o acervo em processo **e** a rede social em `127.0.0.1:8091`; **cala** quando `data/ops/.deploy-em-curso.lock` existe (ate 30 min) e a linha de aprovacao diz qual dos dois casos ocorreu.

### `tools/run-daily-content` — passos 2.5 a 9 (o que o P6 vai recortar)
`etapa` em: `:490` 2.5 baseline · `:501` 3 preservacao (**PARA**) · `:544` 3.5 untracked (avisa) · `:553` 4 integridade (**PARA**) · `:590` 5 commit do portfolio · `:622` 6 pareamento + commit das paginas (**PARA**) · `:640` 7 censo · `:649` 7.9 data de revisao · `:683` 8 publicacao transacional (**PARA com exit 2**) · `:722` 8-bis fila de refinamento · `:797` 8.5 brotli · `:822` 8.6 onda avancou · `:832` 8.7 gates · `:859` 9 prova HTTP (`reload-wiki-server`, `check-edge-discovery-freshness` + purga de 7 artefatos, IndexNow).

**ACHADO QUE MUDA O P6:** a onda diaria **NAO purga a borda das paginas que publicou**. O unico `purge-edge-cache` dela e `:877-878`, e so com **7 URLs fixas** de descoberta (`/`, `/sitemap.xml`, `/feed.xml`, `/rss.xml`, `/robots.txt`, `/llms.txt`, `/llms-full.txt`), e so quando `check-edge-discovery-freshness` reprova. Pagina **reescrita** pela onda fica velha na borda ate `s-maxage=604800` = **7 dias**. Pagina nova nao sofre (nunca esteve na borda). Isso e corroborado por `tools/check-edge-frescor:9-13`, que mediu em 2026-09-09: **287 de 288 rotas carimbadas em 24 h estavam velhas na borda** (240 no HTML com HIT de 3 a 14 h; 287 na gemea).

---

## 2. Resposta 1 — binario Go novo: a sequencia e por que 7 vem antes de 8

**Sequencia exata (uma linha, o resto e o script):**
```
./tools/deploy-binario-go --seco      # confere o plano, nada muta
./tools/deploy-binario-go             # 8 passos, ~405 s com 11.158 rotas
```
Os 8 degraus e o incidente de cada um: `tools/deploy-binario-go:11-50`.

**Por que purgar antes de invalidar/aquecer repopula o Tiered Cache com conteudo VELHO:** a borda, ao ser purgada, repopula **da origem**. A origem tem duas camadas de guarda de objeto velho — `var/nginx/cache` (zona `proxy_cache wj_dyn`, `s-maxage=604800`) e `var/on-demand-cache` do Go. Purgando primeiro, o primeiro MISS da borda busca no nginx e recebe o objeto da versao ANTERIOR, e o Tiered Cache o promove como se fosse novo: fica `HIT`/`age: 0` com conteudo velho — e o operador ve "HIT, age 0" e conclui que a purga funcionou.

**A medicao de 2026-09-05, fonte primaria encontrada:** `.agents/runtime/mensagens/msg-deploy-binario.txt:18-22` —
> "A ORDEM 6-7-8 E' O PRODUTO. Purgar a borda antes de aquecer a origem faz o Tiered Cache repopular com o conteudo VELHO -- medido hoje: age 0, cf-cache-status HIT, campos=0, cinco tentativas seguidas. Com a ordem certa, campos=3 de primeira."

Copias derivadas: `tools/deploy-binario-go:52-57` e `:428-431`; `internal/deployordem/deployordem.go:14-17`; `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md:930-936`; e o CLAUDE.md §1. **Nao ha JSONL com os cinco `campos=0` crus** — a evidencia primaria e a mensagem de commit. O ledger `data/ops/deploy_binario_go.jsonl` so comeca **depois** da correcao (primeiro registro 2026-09-05T15:26, abortado no passo 2).

**A guarda e executavel, nao documental:** inverter 7 e 8 no arquivo real faz a propria ferramenta recusar rodar com exit 2 (`confere_ordem`, `:563-575`) e `internal/deployordem` reprovar nomeando o incidente (18 testes, 13 mutacoes — `msg-deploy-binario.txt:33-38`).

**Instrumento para provar DEPOIS, sem esperar:** `tools/check-edge-frescor` compara, por rota, o byte da borda × `public/` e o byte da gemea na borda × o do processo Go × o `Repr-Digest` de cada variante no nginx. E ele que nomeia a classe `origem_cache_velha`. Read-only sem `--purgar`/`--gravar`.

---

## 3. Resposta 2 — `--ressemear` e o P1b. **MEDIDO: o P1b nao re-data nada, e por isso a purga tem de ser manual**

### Quando `--ressemear` e obrigatorio e quando e proibido
- **Obrigatorio** quando a *formula* do `served_sha256` muda (trocar `BLOCOS_DE_NAVEGACAO` ou o corpo de `neutraliza_datas`): `assinatura_da_formula()` `:387-412` hasheia os patterns **e** o fonte da funcao, e `confere_formula()` `:415-432` recusa. Tambem e o remedio correto quando mudou markup/CSS/atributo servido **sem** mudar texto (matriz do CLAUDE.md §6; motivo em `deploy-publico:207-223`).
- **Proibido** quando o texto editorial mudou: ai a re-datacao e verdadeira, e suprimi-la esconde do buscador conteudo que mudou de fato. E `--desde-commit` **nao pode** ir na mesma passada (`:431-432`), porque ele compara `html_sha256` do manifesto, que nao passa pela neutralizacao.

### O P1b (datePublished no JSON-LD): markup ou texto? **NENHUM DOS DOIS — e mudanca NEUTRALIZADA**
`datePublished` esta em forma ISO dentro do JSON-LD e e apagado por `DATA_ISO_NO_HTML` (`:245`, `neutraliza_datas` `:266-306`) **antes** do hash. E `content_sha256` so cobre `("title","meta_description","heading","summary","body_sections","faq")` (`CAMPOS_DE_CONTEUDO`, `:185-186`) — nenhum campo de data.

**Prova que rodei**, sobre `public/jurisprudencia/stj-tema-979/index.html` (pagina real, um dos 875 casos de `/jurisprudencia/`), trocando `article:published_time`, `"datePublished"` e o `<time datetime=…>15 de setembro de 2026</time>` de `2026-09-15` para `2026-08-28`:
```
served_sha256 ANTES : ab27922b6f77c85bd37f74a88daf57b00c6dedd86f929f666d0d67cc0f805276
served_sha256 DEPOIS: ab27922b6f77c85bd37f74a88daf57b00c6dedd86f929f666d0d67cc0f805276
IGUAIS? True
```
A forma por extenso tambem cai, porque `neutraliza_datas` deriva o extenso de cada ISO que o proprio documento declara (`:289-302`).

### As tres consequencias operacionais, e a terceira e a perigosa
1. **NAO usar `--ressemear` no P1b.** A formula nao muda; `--ressemear` alem de desnecessario **rebaixa carimbos de instante para dia** quando repetidos ≥ 50 vezes (`:702-717`) e regrava o ledger inteiro. Efeito colateral gratuito.
2. **As 944 paginas NAO serao re-datadas** — nem `revised_on`, nem `<lastmod>`, nem `Last-Modified`, nem IndexNow. **Isso esta certo**: o texto nao mudou; o que se corrige e metadado de estreia. O acervo **nao** sera re-anunciado ao Googlebot.
3. **`--purge-targets` devolvera ZERO para essas 944 rotas** → em `deploy-publico:929-933` sai `ALVOS_N=0`; sem binario novo cai no ramo `:1104` e **so os artefatos de descoberta sao purgados**. As 944 paginas continuam servindo o `datePublished` errado pela borda por ate **7 dias** (`s-maxage=604800`, medido vivo hoje: `HIT`, `age: 27291`).
   **⇒ A purga do P1b e MANUAL e DIRIGIDA, e tem de listar as 944 rotas + as 944 gemeas `.md` + `/api/v1/pages<rota>` + `/api/v1/citar<rota>`** (o padrao que o proprio deploy usa em `:1199-1221`), com `--teto-por-url` acima do tamanho da lista (senao `purge-edge-cache:191` degrada para `purge_everything` e joga fora ~11 mil paginas quentes), e **reaquecimento dirigido logo em seguida** (`warm-edge-cache --de-arquivo <a mesma lista> --rps 12 --concorrencia 4`), porque o timer so passa 04:20 e 16:20 UTC.

### A cegueira e de FAMILIA, nao de uma ferramenta — e `check-edge-frescor` tambem e cego ao P1b
Todo instrumento que deriva "o que mudou" de `data/ops/page_content_revision.jsonl` fica cego a uma correcao que o hash neutraliza:
`--purge-targets` · o passo 6 do `deploy-publico` · o IndexNow incremental (`deploy-publico:1365`) · `check-lastmod-causalidade` · e **`tools/check-edge-frescor`**, cujos seletores de janela sao `--dia` / `--desde-horas` / `--desde-ledger` (`:834-837`), todos sobre "rotas **carimbadas** no periodo". Como o P1b nao carimba ninguem, `check-edge-frescor --purgar` acharia **zero** das 944. **Nao usar esse atalho.**

**A fonte correta da lista de purga do P1b e o diff CRU de `html_sha256` do `published_manifest.jsonl`** (antes × depois da republicacao) — nao neutralizado, portanto enxerga as 944 e tambem os `/api/v1/citar<rota>`, que carregam o `html_sha256` da pagina. `rotas_com_bytes_novos()` em `generate-page-content-revision:440-478` **ja computa exatamente isso**, mas esta cabeada apenas a `--desde-commit`, que forca re-datacao e e proibido na mesma passada (`:431-432`).
**LACUNA: nao existe hoje ferramenta read-only que emita essa lista.** Procedimento manual do P1b, enquanto ela nao existir: `cp data/editorial/published_manifest.jsonl /tmp/manifesto.antes` antes de publicar; depois, diff por rota do campo `html_sha256` (ultima linha por rota vence — o manifesto e append-only, `:457-462`); essa lista e a da purga.

### A origem depende de QUAL publicador leva o P1b
- **Por `tools/deploy-publico`:** o passo 4 (`:763-767`) apaga `var/nginx/cache` e o 5b (`:895-900`) reaquece. Origem ja resolvida; **falta so a purga de borda dirigida** (que o passo 6 nao fara, porque `ALVOS_N=0`).
- **Pela onda (`run-daily-content:684`) ou por `publish-v2-direct` solto:** ninguem toca a zona `wj_dyn`. As gemeas `.md` das 944 ficam velhas no cache de ORIGEM por ate 7 dias, e purgar so a borda **reproduz 2026-09-05**. Ordem obrigatoria: `tools/purge-origin-cache --rota <cada .md>` → aquecer a origem → `tools/purge-edge-cache --de-arquivo <lista> --teto-por-url <N+1>` → `tools/warm-edge-cache --de-arquivo <a mesma lista> --rps 12 --concorrencia 4`.

### E `Last-Modified` NAO serve de prova do P1b — medido
`escritor.gravaDatado` carimba o mtime do arquivo **a partir da data editorial** (`cmd/publish-v2-direct/escritor_publico_test.go:189-223`, `meiaNoiteUTC`). Como o P1b nao avanca `revised_on`, o mtime volta ao mesmo valor e o `Last-Modified` fica identico. Medido agora contra a origem:
```
If-Modified-Since: Thu, 10 Sep 2026 00:00:00 GMT  ->  HTTP/1.1 304 Not Modified
(sem o cabecalho, controle)                       ->  HTTP/1.1 200 OK, Content-Length: 20584
```
Consequencia dupla: (a) a **verificacao** do P1b tem de ler o CORPO servido (`grep datePublished`), nunca um cabecalho; (b) qualquer cliente que revalide por `If-Modified-Since` — inclusive os bots que o projeto ja mediu revalidando — mantem o `datePublished` errado. O `ETag` **muda** (o corpo muda de tamanho), entao `If-None-Match` enxerga; e a borda, depois de purgada, busca sem validador e recebe 200 com os bytes novos — a purga funciona, o que nao funciona e medir por data.

**Resumo de uma linha para o runbook:** *P1b = linha "script inline / malha de links" da matriz do §6: sem `--ressemear`, sem re-datacao, com **purga ampla manual obrigatoria** derivada do diff CRU de `html_sha256`, origem antes da borda, reaquecimento em seguida, e prova por corpo — nunca por `Last-Modified`.*

---

## 4. Resposta 3 — publicacao transacional

### Qual dos dois roda hoje
**`cmd/publish-v2-direct`.** `internal/publicrelease` **nao e um segundo publicador**: e a biblioteca de predicados de aprovacao/rollback que o publicador e os `cmd/prove-*`/`cmd/promote-*` consultam. Os dois pontos de invocacao vivos do publicador: `tools/deploy-publico:464` (`--allow-public-write`) e `tools/run-daily-content:684` (`-published-at HOJE -reviewed-at HOJE -allow-public-write`, `timeout 1800`).

### Tem staging, SHA-256, lock, rollback e smoke?
| elemento | onde | o que realmente e |
|---|---|---|
| **lock** | `main.go:95` (`data/ops/.publish-v2-direct.lock`), `acquireLock` `:3969-3986` | `O_CREATE\|O_EXCL`, grava `pid=` e `started_at=`, liberado por `defer release()` `:862`. **Nao le o pid de volta**: orfao so se remove a mao |
| **snapshot/rollback** | `writeRollbackSnapshot` `:3988-4058`, chamado `:863-868` | copia **3 arquivos**, gzip: `content/pages.json`, `data/editorial/published_manifest.jsonl`, o rehearsal jsonl. **NAO copia `public/` nem `public/sitemaps/`** |
| **SHA-256** | `HTMLSHA256`/`SitemapSHA256` por rota `:3845-3846`; `sha256Sum` `:2949` | o manifesto certifica cada artefato |
| **staging** | `escritorPublico` `:854`; `StagingMaterialized` `:3937` | o ensaio (`escrever=false`) desce pelo mesmo caminho: renderiza, compara, **sem lock, sem snapshot, sem syscall de escrita** (`:846-853`) |
| **smoke** | fora do publicador | `deploy-publico:1525-1589` (borda **e** origem) e `run-daily-content:859` |

### O que acontece se o processo morrer no meio — **confirmado**
- **Nenhum `signal.Notify` em `cmd/publish-v2-direct`, `internal/publicrelease` nem `cmd/build`** (grep: zero). Em Go, SIGTERM sem handler mata o processo **sem rodar defers**.
- A unit e `oneshot` com **`KillSignal=15`** e `TimeoutStopUSec=90s` (medido ao vivo). `run-daily-content:684` ainda poe `timeout 1800` por cima, que tambem manda SIGTERM.
- **Consequencia 1:** `defer release()` nao roda → `data/ops/.publish-v2-direct.lock` fica **orfao**, e a proxima execucao morre com "promocao ja em curso".
- **Consequencia 2:** `public/` e os shards de sitemap ficam num estado intermediario que o snapshot **nao cobre**. Se sobrar `<loc>` de sitemap sem linha de manifesto, `publishedmanifest.Validate` **aborta o boot** (`published_manifest_sitemap_loc_without_manifest`) — e a unit do servidor tem `Restart=always` com `StartLimitIntervalSec=0`: **laco infinito de reinicio**. E exatamente o cenario que `run-daily-content:692-719` descreve e por causa do qual a onda passou a sair com exit 2.
- **Consequencia 3, achado novo:** `tools/deploy-publico:463` faz `rm -f data/ops/.publish-v2-direct.lock` **incondicionalmente, sem conferir se o pid do lock esta vivo**. Isso resolve o orfao e abre a porta para **dois publicadores concorrentes** — que e precisamente o que o lock existe para impedir (`:3969-3970`).
- **Rota de recuo documentada:** o `RESTORE.md` do snapshot (`:4043-4056`) ensina que esvaziar o manifesto devolve o validador ao ramo leniente e o servidor sobe **mesmo com `public/` incoerente**.

---

## 5. Resposta 4 — o gate de pareamento e o que ele obriga no P6

**Por que a autoridade e o commit PAI:** o gate `tools/check-v2-finalized-commit` recusa pagina cujo `intent_id` nao esteja no portfolio **ja commitado**, "para que ninguem fabrique a demanda e o conteudo no mesmo movimento atomico" (`tools/check-v2-portfolio-pairing:6-13`). O verificador **espelha** a condicao do gate, inclusive a tolerancia a tombstones (`skipped: true`), porque verificador mais severo que o gate manda consertar o que nao esta quebrado (`:56-70`).

**O caso caro** e `so_no_candidato` (`:148-150`): a intencao existe no disco mas nao no pai. A saida imprime o proximo comando exato (`:154-159`).

**O deadlock historico:** ate 2026-08-26 a onda rodava o pareamento **antes** de commitar o portfolio; como a etapa 2/9 gera intencoes toda madrugada, `so_no_candidato` nunca era vazio e a onda morria antes de publicar — **6 de 6 execucoes parciais, IndexNow mudo de 20/08 a 26/08** (`run-daily-content:592-605`).

**O que isso obriga no P6 — dois commits separados, nesta ordem, sempre:**
```
git add data/editorial/portfolio_v2   &&  git commit -F <msg> -- data/editorial/portfolio_v2
./tools/check-v2-portfolio-pairing            # 3,45 s, exit 0 obrigatorio
git add data/editorial/v2_pages       &&  git commit -F <msg> -- data/editorial/v2_pages
```
E o que `run-daily-content:613-637` ja faz. **O publicador autonomo do P6 nao pode pular isso**: `cmd/generate-acordao-pages` emite pagina **e** intencao, entao publicar sem os dois commits na ordem certa queima um pre-commit inteiro (build Go de minutos) por tentativa — **4 tentativas queimadas** e o precedente registrado (`check-v2-portfolio-pairing:15-21`).
Corolario: o oneshot do P6 precisa **commitar antes de publicar** e precisa do `git add` por **caminho exato** e do `commit` em comando **separado** (regra de maquina; `add` por diretorio ja varreu trabalho de outra sessao 3×).

---

## 6. Resposta 5 — seguro (read-only) × muta

### SEGUROS em plan mode — nao escrevem disco de produto, nao tocam systemd, nao purgam
| comando | por que e seguro (arquivo:linha) |
|---|---|
| `./tools/deploy-binario-go --seco [--json]` | sem lock (`:629`), sem ledger (`:692`), `roda()` nao executa (`:213`) |
| `./tools/purge-edge-cache --dry-run` | retorna em `:218-220` antes da chamada e do ledger |
| `./tools/generate-page-content-revision --purge-targets` | retorna em `:730-742` antes da escrita — **140,17 s medidos** |
| `./tools/generate-page-content-revision --dry-run` | `:764-766` |
| `./tools/warm-origin-cache --listar-rotas` | `:297-305`, antes do `/readyz` e de qualquer GET |
| `./tools/warm-edge-cache --listar-artefatos` | `:633-636`, antes do flock e de qualquer GET |
| `./tools/check-v2-portfolio-pairing [--index]` | so `git ls-tree`/`git show` + disco — **3,45 s** |
| `./tools/check-csp-style-hashes` | read-only por desenho (cabecalho `:1-30`); compila o cache de gates em `.cache/check-bin` |
| `./tools/check-http-smoke` | **isolamento CONFERIDO**: `checks.go:7100-7105` cria `os.MkdirTemp` proprio e usa `httpserver.NewParaVerificacao(repo, smokeCacheDir)` com `defer os.RemoveAll` — **nao** compartilha `var/on-demand-cache` com producao (o incidente de 2026-08-19). O guarda-costas e `internal/checks/ledger_vivo_test.go:36-60`, que proibe qualquer arquivo de producao do pacote de chamar `httpserver.New` (ligaria um SEGUNDO ledger de acesso sobre o arquivo vivo) |
| `./tools/check-edge-frescor` (sem `--purgar`/`--gravar`) | so le borda, Go, nginx e `public/` |
| `./tools/check-jsonld-cobertura` (sem `--gravar`) | a serie so e escrita com `--gravar` (`deploy-publico:1520-1523`) |
| `./tools/reload-wiki-server --check` | "so mede, nao reinicia (read-only)", cabecalho `:35` |
| `./tools/check-sitemap-shard-grace --listar-removidos`, `check-validator-attestation`, `check-ingress-fontes-completas`, `check-units-instaladas`, `check-robots-parser-real`, `check-untracked-product-inventory` | gates read-only chamados pelo proprio deploy fora do caminho de escrita |
| `nginx -t` **sem sudo** | `deploy-publico:815-821`: a unit ja o faz assim, com o mesmo usuario |

### MUTAM — proibidos em plan mode
`tools/deploy-publico` (**qualquer** invocacao; nao tem modo seco) · `tools/deploy-binario-go` sem `--seco` · `cmd/publish-v2-direct` com `--allow-public-write` · `tools/run-daily-content` (com ou sem `--somente-noticias`; `--seco` esta **morto** desde 2026-09-09, P2) · `tools/purge-edge-cache` sem `--dry-run` · `tools/purge-origin-cache` sem `--seco` · `tools/warm-edge-cache` e `tools/warm-origin-cache` sem flag de listagem (enchem cache + gravam ledger) · `tools/generate-page-content-revision` sem flag (reescreve o ledger e a assinatura) · `tools/generate-brotli-static` · `tools/ingest-v2-stock` · `cmd/generate-legal-cocitation` · `cmd/generate-social-temas --aplicar` · `cmd/seed-sitemap-registry --escrever` · `tools/generate-indexnow-*` · `tools/reload-wiki-server` sem `--check` · qualquer `systemctl start/stop/restart/reload`.

### Duas armadilhas de "read-only" ja catalogadas que continuam valendo
- `tools/check-portal-health` **escreve** `portal_health_state.json` e zera `reparo_ultimo` mesmo sem `--repair`.
- `cmd/check` **sem argumento roda TODOS os gates** — ja abriu 45 processos e levou o load a 52. Sempre `./tools/go-modern run ./cmd/check <nome>`, com o nome lido de `internal/checks/checks.go` (`http-smoke` `:784`, `csp-style-hashes` `:808`).

---

## 7. Defeitos NOVOS achados nesta varredura (nao estavam no diagnostico entregue)

1. **`purge-edge-cache:249` — `NameError` no caminho de sucesso da purga por TAG.**
   `alvos` so e atribuido dentro de `if seletivo:` (`:191-196`). Na linha `:249`, `purga_total or len(alvos) >= 1000` e avaliado **depois** de a purga ter sido aceita pela API. Com `--tag` **sem** `--url` (ou com `--url` acima do teto + `--tag`), `purga_total` e `False` e `alvos` nao existe → traceback e **exit != 0 sobre uma purga que FUNCIONOU**. Quem chama le "AVISO: cache de borda NAO foi purgado" e purga de novo, jogando fora o aquecimento.
   *Verificado por leitura, nao executado* (exigiria credencial e uma purga real). O ledger `edge_cache_purge.jsonl` mostra que o caminho misto (`29 URL(s) … 1 tag(s)`) rodou hoje sem cair — consistente, porque ali `alvos` existe.
   **E isto morde o atalho natural do P1b:** `--tag area-jurisprudencia` (875 das 944 paginas, tag emitida pelo nginx em `ops/nginx/wikijuridica.conf`) cai no `NameError` a menos que pelo menos **um** `--url` abaixo do teto va junto — modo misto e o unico caminho que o ledger prova funcionando hoje.
2. **`deploy-publico:463` remove o lock do publicador sem prova de vida** — abre janela para dois `publish-v2-direct` concorrentes, que e exatamente o que `acquireLock` existe para impedir.
3. **`writeRollbackSnapshot` nao cobre `public/` nem `public/sitemaps/`** — o "rollback transacional" restaura manifesto e `pages.json`, nunca o HTML servido. Em interrupcao, a coerencia so volta republicando.
4. **O comentario de `generate-page-content-revision:239-244` esta desatualizado**: afirma "7 ocorrencias de AAAA-MM-DD e todas as 7 sao metadado de data". Medido hoje: **12 e 14**, e parte delas sao **URNs LexML** (`urn:lex:br:federal:lei:2015-03-16;13105`, `…constituicao:1988-10-05;1988`). Ou seja, a data do dispositivo citado **tambem** e neutralizada: trocar a norma citada por outra que difira **so** na data da URN nao re-data a pagina. E um ponto cego real, alem de um comentario que mente sobre a propria medicao (R1).
5. **A onda diaria nao purga a borda do conteudo que publica** (so 7 artefatos de descoberta, e so sob reprovacao) — ver §1. Corroborado por `check-edge-frescor:9-13` (287/288 velhas em 2026-09-09).
6. **`SuccessExitStatus=0 1` mascarando a onda agora mesmo**: `ExecMainStatus=1` com `Result=success` — confirmado ao vivo, sem `OnFailure` disparado. (P10 ja previu; fica aqui a confirmacao da medicao de hoje.)

---

## 8. O que NAO medi, e por que

- *(resolvido durante a varredura)* `--purge-targets` hoje lista **6 linhas — 3 rotas HTML + 3 gemeas**, em 115,07 s. Ou seja: de 11.106 paginas, o instrumento que decide a purga do deploy enxerga **3** como mudadas. E o numero que dimensiona o §3: qualquer correcao invisivel ao hash some dentro desse 3.
- **Tempo real de `deploy-publico` fim a fim nesta maquina hoje**: os numeros que dou (46 min, 31 min, 1.868 s, 1.866 s) sao os que o proprio script registra com data (2026-09-10), nao medicao minha — rodar seria mutar producao.
- **`check-http-smoke` e `check-csp-style-hashes` em segundos reais**: dei o **orcamento declarado** (100.000 ms e 20.000 ms, `data/ops/check_performance_ledger.jsonl`), nao o tempo de parede; rodar compila o binario de gates.
- **As cinco leituras cruas `campos=0` de 2026-09-05**: nao existem em JSONL. A fonte primaria e a mensagem de commit `.agents/runtime/mensagens/msg-deploy-binario.txt:18-22`.

---

## 9. O que o advisor mudou

Quatro correcoes, todas incorporadas acima, e nenhuma delas cosmetica:

1. **Eu recomendava `tools/check-edge-frescor --purgar` como atalho do P1b — estava ERRADO.** Os seletores dele (`:834-837`) sao "rotas **carimbadas** no periodo", e o P1b nao carimba ninguem: ele acharia zero das 944, pelo MESMO motivo que `--purge-targets`. A correcao generalizou o achado: a cegueira e da **familia inteira** de instrumentos que derivam "o que mudou" do `page_content_revision.jsonl`, e a fonte correta da lista e o **diff cru de `html_sha256` do manifesto** — que `rotas_com_bytes_novos():440-478` ja sabe computar mas so expõe por `--desde-commit`, proibido na mesma passada. Virou **lacuna nomeada**, com o procedimento manual enquanto a ferramenta nao existir.
2. **Distingui a origem por publicador.** `deploy-publico` ja limpa e reaquece `var/nginx/cache` (passos 4 e 5b); a onda e o `publish-v2-direct` solto **nao tocam** a zona `wj_dyn`, entao por esses caminhos a purga de origem das gemeas tem de vir ANTES da borda ou reproduz 2026-09-05.
3. **`check-http-smoke` so entrou na coluna "seguro" DEPOIS de conferir**, em vez de por analogia: `checks.go:7100-7105` isola o cache em `os.MkdirTemp` e o teste `ledger_vivo_test.go:36-60` proibe `httpserver.New` no pacote. Sem essa conferencia ele seria uma armadilha, nao um comando seguro.
4. **Medi a revalidacao**, que eu nao tinha medido: a origem devolve **304** a `If-Modified-Since` da data atual, porque `gravaDatado` carimba o mtime a partir da data editorial. Isso derruba `Last-Modified` como prova do P1b e obriga a verificacao por CORPO.
5. Acrescentei que o atalho `--tag area-jurisprudencia` cai no `NameError` do defeito #1 se nao houver um `--url` junto.
