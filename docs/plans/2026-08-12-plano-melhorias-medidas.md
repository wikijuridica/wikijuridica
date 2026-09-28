PLANO CONSOLIDADO — 5 frentes, 2026-08-12. READ-ONLY: nada foi escrito no repo.

## 1. ORDEM (dependência explícita)

**P1 — #36 Chtimes no publicador. PRÉ-CONDIÇÃO DE TUDO.** Trava a republicação: hoje a
republicação recarimba ~3.998 artefatos com mtime de deploy; se #36 entrar depois, o Chtimes
toca os 9.844 e paga-se um SEGUNDO reset total de validador (perda de 304 no acervo inteiro +
2ª purga). Junto, um reset só — e ele já está pago nesta janela (binário dirty → CAMADA_MUDOU=1
→ purga total dispara de qualquer forma).
- ONDE: `cmd/publish-v2-direct/main.go:1206` `escritorPublico.grava` (retorna cedo em conteúdo
  idêntico SEM tocar mtime — #18 já pousada, `escritor_publico_test.go` presente). Método novo
  `gravaDatado(target, novo, dataISO)`; chamadas em **:570 (páginas)** e **:773 (hubs)**.
- DADO: 9.844/9.844 index.html com mtime de hoje contra `dateModified` 2026-08-06; ETag do nginx
  = hex(mtime)-hex(size) (decodificado nas duas frentes), logo (b) via `add_header` não conserta
  a revalidação — só o mtime conserta.
- HUB (furo que o crítico abriu, e que fecha de graça): a data-alvo do hub já existe —
  `render.AreaHubView.UpdatedAt` (`internal/render/area_hub.go:63`), populada em
  `internal/ondemand/areahub.go:323`, já validada como ISO em `area_hub.go:237`. Sem essa linha,
  os 29 hubs — por onde 85% dos artigos são alcançados — mantêm a contradição sitemap×header.
- REGRA: bytes mudaram → mtime de escrita (nunca esconde mudança real). Bytes idênticos →
  Chtimes para a data editorial às **00:00:00 UTC** (mesma base de `httpserver.go:687`
  `parseContentDate`), e só se diferir do alvo. Data vazia/inválida/**futura** → não mexe.
  Ensaio (`escrever=false`) nunca chama Chtimes. Home/institucional/feed/sitemap ficam com mtime
  de escrita: decisão, são poucos e reescrevem a cada mudança de acervo.
- TESTE (`cmd/publish-v2-direct/escritor_publico_test.go`, método novo p/ os testes de #18 seguirem
  verdes): (i) idêntico+mtime errado → vira data editorial 00:00Z e NÃO reescreve; (ii) 2ª chamada
  = 0 syscalls; (iii) bytes diferentes → mtime de escrita; (iv) data vazia/inválida → intocado;
  (v) data futura → intocado; (vi) ensaio → intocado.
- VERIFICAR EM PROD: `curl -sI -H "Host: wikijuridica.com.br" http://127.0.0.1:8088/servidor/formas-de-provimento-cargo/`
  → `Last-Modified` == `dateModified` do próprio HTML; `If-Modified-Since` com essa data → 304.
  `find public -name index.html -newermt "$(date +%F) 00:00" | wc -l` cai de 9.844 para o nº de
  páginas realmente mudadas.
- RISCO: mtime uniformizado para trás pode confundir rsync/backup por timestamp. SINAL DE ERRO:
  contador de Chtimes ≠ 0 na 2ª passada (não convergiu) ou `find -newermt` continuar em 9.8k.
  Convergência legítima leva 1–2 deploys (a data está DENTRO do HTML, `seo.go:116`): um contador
  de ~2.401 reescritas no deploy N+1 é esperado, não falha.

**P2 — commit dos 475 shards + republicação (#33, #19).** Depende de P1.
- `git status --porcelain data/editorial/v2_pages/ | wc -l` = **475** não-commitados (medido).
- PINS: passo CONDICIONAL, não incondicional — `python3 tools/check-v2-semantic-pins-fresh`;
  só rodar `tools/refresh-v2-semantic-pins` se reprovar (o crítico provou que HOJE passa; refresh
  incondicional é escrita sem dado).
- ENSAIO OBRIGATÓRIO antes: `nice -n 19 ./tools/go-modern run ./cmd/publish-v2-direct` (sem
  `--allow-public-write`, não escreve byte). Depois `tools/deploy-publico`.
- DADO: `ALVOS_N` esperado **0** (as correções de âncora são `official_sources`, campo fora do
  hash de `tools/generate-page-content-revision:90`); entrega real = 3.998 artefatos, slots
  ociosos de malha 467→12 (backfillCandidatePool 24→120, #32), sitemap 45→56 shards.
- VERIFICAR: `grep -rl 'compilado.htm#art' public | wc -l` cai de **1.198** (número do crítico,
  não os 2.323 do plano) para ~0. RISCO: ingest de 510 s (fórmula `deploy-publico:110-122`) pode
  estourar. SINAL DE ERRO: `ALVOS_N` ≥200 ou ≈9,6k = hash de conteúdo se moveu em massa =
  regressão de render → PARAR e não purgar.

**P3 — frente proveniência (#37), re-sequenciada pelo dado.** Não depende de P1/P2; pode correr
em paralelo. **A premissa do briefing está errada** (ver §3): as 1.684 não são "sem proveniência",
são **rejeitadas pelo ingest e publicadas assim mesmo** — 100% têm `official_sources` no estoque.
- **Lote 0 (1 linha, faz sozinho o resto render):** o UA de `tools/verify-official-sources:66-71`
  leva reset do Planalto (`http=000`), medido por duas frentes independentes; o UA já usado com
  sucesso hoje (`Mozilla/5.0 (compatible; wikijuridica-source-audit/1.0; +https://wikijuridica.com.br)`,
  `tools/measure-planalto-anchor-coverage-20260812:53`) responde 200. Planalto = **15.085 das
  21.039** ocorrências (72%, medido). Rodar a re-verificação com o UA atual marcaria a maioria do
  acervo como fonte morta — falso negativo em massa. TESTE: `curl -sI -A "<ua>" https://www.planalto.gov.br/ccivil_03/leis/l9784.htm`
  → 200 nos dois UAs antes de qualquer re-verificação.
- **RECONTAR ENTRE LOTES, nunca somar:** 594 das 1.684 têm 2+ classes (medido). Os 283
  `official_source_http_status_invalid` (status=0) são plausivelmente o MESMO reset de UA →
  Lote 0 pode zerar 283 + 116 `verified_at_invalid` + as 35 URLs sem `verified_at` sozinho.
- Lote 1: **636** páginas cuja ÚNICA classe é `official_sources_insufficient` (medido; o total da
  classe é 1.051) → `tools/generate-v2-second-official-source-from-corpus-20260806` (existe, 336
  linhas). Lote 2: **760** `duplicate_phrase_with_page` (292 exclusivas) → gerador datado com CAS.
  Lote 3: resto nomeado (`current_legal_fact_*` 116, `word_count_out_of_range` 25,
  `source_unverified_research_pending` 9, `root/homepage_not_specific` 12, `lane_mismatch` 1,
  `above_maximum` 1).
- REEMISSÃO DO REGISTRO: reprocessar o estoque corrigido por `cmd/ingest-v2-stock`
  (`tools/deploy-publico:131`) — `internal/v2ingest/plan.go:297` filtra payload por RunID, então
  o registro sai completo. Não precisa modo novo.
- VERIFICAR: `intent_id` de `data/ops/v2_ingest_report.jsonl` com status accepted ∩ `content/pages.json`
  sobe de 7.965 e o conjunto rejeitado-publicado cai de 1.684. RISCO: a 2ª fonte automática pode
  ser genérica (homepage) e disparar `official_source_root_url_not_specific`. SINAL: essa classe
  subir de 12 depois do Lote 1.

**P4 — três páginas novas (#34).** Só pelo pipeline sancionado: `ops/relaunch-writing.sh` +
`tools/generate_v2_writing_inventory_pack.py` (ambos existem, `ls` conferido). O lote montado à
mão do plano original NÃO executa (§3). Conteúdo, fontes oficiais conferidas hoje (14.133 art.
159/160/163, 8.429 art. 3º §2º, 12.846 arts. 16/22/30 com a armadilha da MP 703 "Vigência
encerrada", LINDB art. 2º, DL 37/1966 art. 78 III, Lei 12.350/2010 art. 31) e as 3 rotas sem
colisão continuam válidos como INPUT do pack — não se perde nada. VERIFICAR: `curl -s -o /dev/null
-w '%{http_code}' https://wikijuridica.com.br/leis/responsabilizacao-empresa-licitacao/` → 200 e
linha no `published_manifest`. RISCO: canibalizar as irmãs. SINAL: `lei-lindb` ou
`const-direito-adquirido` perderem posição; fronteira dura = não repetir vacatio nem direito
adquirido.

**P5 — #35 re-escopada: NÃO é dreno de atraso, é construção de linha de base.** O atraso não
existe (§3). O que existe, e é o achado mais forte do dia: **`source_page_sha256` é o hash do
NOSSO registro, não do documento oficial — 21.039/21.039 idênticos a `source_record_sha256`**
(medido), porque `internal/v2ingest/v2ingest.go:284` grava `pageFingerprint = sha256(raw da nossa
página)` e `internal/v2ingest/plan.go:1221` EXIGE que os dois sejam iguais. Não existe linha de
base para "a fonte mudou?".
- FAZER: (a) campo novo `official_document_sha256` alimentado por baseline própria — e a semente
  atual NÃO serve (`v2_planalto_anchor_conference_20260812.jsonl` grava `ancoras_no_documento`
  como INT, não conjunto; regerar com `sha256_ancoras` + lista de normas); (b) campo novo
  `SourcesVerifiedAt` FORA da cadeia de `internal/content/content.go:204`
  (`ContentRevisedAt→ReviewedAt→PublicationDate`) — escrever reconferência em `ReviewedAt` moveria
  `lastmod`/`dateModified`/`Last-Modified` sem o conteúdo mudar, exatamente a fraude de frescor que
  o próprio comentário em `content.go:202` proíbe ("quando um HUMANO revisou"). TESTE irmão de
  `internal/content/last_modified_test.go:61` provando que `LastModified()` NÃO observa o campo novo.
- GATILHO: sha256 cru do HTML NÃO serve (§3). Serve: PDF (hash cru estável nas 3 buscas) e
  impressão normativa (âncoras+normas+ano) — com **fail-closed** obrigatório: extração vazia = SEM
  digital (4 documentos distintos deram a mesma `d8e09da58ba1`), nunca valor comparável.
- RISCO: `publish:false` como alavanca de congelamento cria página ÓRFÃ — o HTML de artigo nunca é
  removido (`os.Remove` em `main.go:830` só varre paginação) e manifesto/sitemap saem só de
  `selected` (`main.go:1139`), o que `publishedmanifest.Validate` proíbe (`httpserver.go:243`).
  Congelar ≠ despublicar.

## 2. RESULTADO NEGATIVO — o que os críticos derrubaram (entrega também)
- "1.684 páginas SEM proveniência": falso. São rejeitadas-publicadas, **100% com `official_sources`**
  no estoque; accepted(7.965)+rejected(1.787)=9.752 = registro exato, gap 0.
- "família /aereo/ inteira": falso — **6 de 207** (2,9%). Cluster real é a onda `-w3`, espalhada.
- "12.287 ocorrências fora do prazo das TTLs": só existe com TTL=30 achatado em tudo. Medido:
  ocorrências >60d = **0**, >90d = **0**, idade máxima **35 dias**; `ttlDays()`
  (`internal/sourceregistryv2/registry.go:1015`) dá 90 a `legislation_federal` = 72% do acervo.
- "5 páginas com fragmento terminal (classe CRÍTICA)": 4 são falso positivo de homógrafo — "para"
  é o verbo *parar* ("onde essa proteção para", "onde a responsabilidade do buscador para") e
  "esta" é pronome ("não para esta", "que se confundem com esta"); a 5ª (`/transito/ipva-divida-ativa-protestado-impede-transferencia/`,
  "Por que a transferência para") é gramatical mas feia. **Consequência: ZERO crítica entre as
  1.684 → nada a despublicar**; o detector precisa de teste de falso positivo (política 2026-08-06,
  item 2) antes de voltar a barrar.
- "sha256 cru do documento oficial como gatilho": derrubado com 3 buscas — 6/11 instáveis por
  token anti-bot (F5 `f5_cspm` no Planalto, `csrf-token` no INPI, Rocket Loader na Anatel: 324.383
  bytes por norma zero), 5 delas com byte count idêntico.
- "upper tier é GIG": derrubado — 253 requisições de IAD na origem pós-warm, rota canônica limpa.
- "10 pinos semânticos velhos, refresh obrigatório": `check-v2-semantic-pins-fresh` passa.
- Pipeline da frente 5 como escrito: `writing-mass.js:110-146` exige 16 chaves
  (`closedBatchSchema`, chamado em :442) e `_validate_new_batch` (`inventory_pack.py:384-395`)
  exige `skip=0/take=0/intent_ids` explícitos + `file == portfolio_v2/{area}.jsonl`; o alocador
  gera o slug sozinho. Lote à mão reprova antes de rodar.
- Números stale corrigidos: `compilado.htm#art` em public = **1.198** (não 2.323); no estoque
  **200 ocorrências / 132 registros** (não 171); datas no sitemap = **9.814 / 21 / 6** (não
  9.628/5/1); breakdown de reasons todo recontado (1.051 / 760 / 283 / 116 / 116).

## 3. FILA DE MEDIÇÃO — sem dado, NÃO entra em execução
- **#31 tiered cache.** Dado contraditório (IAD na origem com tiered ligado). EXPERIMENTO: janela
  de 2 h pós-`warm-edge-cache`, contar em `/var/log/nginx/wikijuridica/access.log` requisições por
  colo (`CF-Ray` sufixo) sobre rota canônica já aquecida; tiered funcionando ⇒ só o upper tier
  aparece. Sem isso, nenhuma mudança de config de cache.
- **Join URL→família→TTL.** As 1.762 URLs-base >30d vencem ou não? Depende de qual constante
  governa: `ttlDays()` (`registry.go:1015`, 30/90/60) ou os `FreshnessTTLDays: 30` hardcoded em
  `registry.go:521`, `:553`, `:580`. EXPERIMENTO: resolver cada URL de
  `data/source-audit/v2_source_provenance.jsonl` à sua `family_id` no registry e recontar por TTL
  efetivo — comando único, sem escrita. Só depois se define cadência (o "146/dia" do plano drena
  atraso fictício e o "52,8/dia" fica ~2× subestimado; os dois não podem valer juntos).
- **Gramática de norma alteradora por família.** O regex `(Redação dada pela Lei nº X)` deu 0 em 6
  de 11 famílias por construção (ANAC/Anatel escrevem "Alterado pela Resolução nº X").
  EXPERIMENTO: amostra de 3 documentos por família antes de escrever qualquer extrator.
- **Máscara de numeral volátil.** Removendo `<script|style|noscript>` COM corpo + `<meta>`, o texto
  visível vai a 10/11 estável; o residual é o contador "Acessos: 195345→195350" da Anatel.
  EXPERIMENTO: 3 buscas do mesmo doc com a máscara aplicada antes de adotar o fallback.
