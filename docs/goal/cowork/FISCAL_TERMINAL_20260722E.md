# FISCAL_TERMINAL_20260722E — deltas da janela 12h (sessão agendada) — SÓ o que B/C/D/PM não cobriram

Autor: `claude-cowork-fable` (sessão agendada 11:48–13:00). Método: diffs integrais + `go test` focado EXECUTADO + grep. Cross-ref: FISCAL_C cobriu 61449a8c comportamental (H1–H4); FISCAL_PM cobriu 410-dormente + FAQ q/a (já corrigido em v2ingest.go via UnmarshalJSON alias — verificado no HEAD) + taxonomia das 524; FISCAL_B cobriu ff5b9030; D cobriu 2fa8bda3/97858ea0. Abaixo, SÓ achados novos.

## 1. BUG NO HEAD: `go test ./internal/entitysitemap/` FALHA (61449a8c esqueceu o teste irmão)

`sitemap.go:18` foi 45000→40000, mas `internal/entitysitemap/entitysitemap_test.go:39-58` ainda espera o corte antigo: **FAIL real executado** (`shard[0] pages=40000 want=45000`). O pre-commit só builda — vermelho latente que vai estourar no próximo `test ./...`/lab-cycle. FIX 1 frase: linhas 53/56 usarem `sitemap.DefaultMaxURLsPerShard` e `50000-sitemap.DefaultMaxURLsPerShard` (+comentário :40-41). A implementação em si está correta (delegação sem constante duplicada, flush-antes-de-append, sem off-by-one) — concordo com o SOLIDO comportamental do FISCAL_C; o defeito é exclusivamente o teste desatualizado.

## 2. d22827dd — verificador `cowork_live_browser` (consome MEUS insumos): allowlist SÓLIDA, 3 fixes

Fail-closed no ponto crítico (agregador → `source_host_not_official` via `inventory.go:625-666`). Fixes executáveis:
1. **Sem piso de frescor**: `audit.go:766-771` só rejeita `verified_at` futuro — um insumo de anos atrás revalidaria fonte morta. Exigir `CheckedAt − VerifiedViaEvidenceAt ≤ OfficialSourceVerificationMaxAgeDays`.
2. **`reachable`/`looks_official` parseados e IGNORADOS** (`cowork_live_browser.go:192`): registro `reachable:false, verdict:"ok"` passaria. Exigir ambos true.
3. `http_status` sintetizado 200 (`:227`) — aceitável por design (request real falhou), documentar no código.

## 3. d22827dd — strictjson (decoder à mão no caminho quente do ingest, ~40 call sites)

Sem divergência alcançável construída, MAS: (a) **zero fuzz** — criar `FuzzDecodeUnique` diferencial vs `json.Unmarshal`; (b) diff-test não cobre `uint64` (ex.: `adjudicate_shard.go:112`), float, nesting ~128, `\uXXXX`/surrogates; (c) **comentário FALSO** `decode.go:36-38` ("never partially decodes") — bail de valor ocorre APÓS mutar campos anteriores; a correção do fallback depende de invariante não-declarado (re-Unmarshal no mesmo destino). Corrigir comentário ou decodificar em temp. (d) Fim do single-use: `transaction_retired_tombstone_name_test.go` NÃO prova anti-replay — proteção real é inode-CAS (`transaction_safe_io.go:1152+`) + unit-ledger do committer; falta teste de replay do canal.

## 4. 1a2ad2e4 — reconcile stale-skip: produto UNTRACKED + conteúdo não commitado

(a) O gerador inteiro está untracked: `internal/v2sourceresearchreconcile/` + `cmd/generate-v2-stale-skip-reconcile/` + `tools/generate-v2-stale-skip-reconcile` — viola "produto não fica untracked". (b) `data/editorial/v2_pages/tributario-07.jsonl` modificado e NÃO commitado — o commit levou o relatório sem a mudança que ele descreve. (c) Frontboard `tributario07-stale-skip` segue `queued`. FIX: um commit por pathspec com os 4 caminhos + frontboard. Dados do relatório conferidos: 1 removida (intent vive ativo em tributario-r01:1, sem duplicata), 45 held 100% `no_active_page_in_another_shard` (curto-circuito por design); tombstone ADI 5881 tratado (staleskip.go:147-149 exclui supersessões da fila).

## 5. a6686a53/fc4d5286 — 2 fixes pequenos

(a) Nada amarra **canal→tipo** (`requiredChannelContracts` não impede futuro tipo=lei via lexml_urn) — amarrar no channelContract; (b) teste só cobre caminho feliz — adicionar caso NEGATIVO (canal bogus/tipo inválido disparam os códigos). Registry: 67/67 lexml_urn=sumula hoje, domínios oficiais intactos, repair-journal 281 entradas 100% quarentena com manifest_sha256 batendo.

## 6. 61449a8c — miudezas restantes

`httpserver.go:516,520`: trocar `time.Parse(http.TimeFormat,…)` por `http.ParseTime(…)` (idioma do repo em 6 call sites). Comentário `httpserver.go:67-68` afirma fonte de verdade que não existe (concorda com o 410-dormente do PM — corrigir o comentário junto com a fiação DEC).

## 7. Funil 14:00Z — confirmações de previsão

`dup_phrase` 484→**205** (−58%) só com o rerun — confirma a previsão central do `DUPPHRASE_DRAIN_SPEC_20260722.md` (fila velha era pré-e9905e06). `source_unverified_research_pending` 104→**5** (reconcile funcionou). 391 stale seguem aguardando o re-stamp (2 execuções barradas em gates distintos — frontboard `restamp-391-live`).

## 8. Súmulas — convergência independente de 2 métodos (portal-STF títulos × LexML fichas)

Minha checagem paralela (títulos oficiais do portal STF) convergiu com a regeneração LexML do loop gemeo: S.152 única com marca oficial `(revogada)`; S.14 SEM marca em ambos os métodos — sustenta o achado metodológico (silêncio ≠ vigência) por rota independente. Dados adicionais meus: súmulas canceladas de fato CARREGAM marca no título em vários casos (S.4, S.394, S.584, S.599) — ou seja, o conjunto de marcas é INCOMPLETO, reforçando o fail-closed; S.104 tem página dedicada sem marca (vigente com evidência mais forte); alegação de revogação da S.159 em fonte secundária é provável confusão com a S.152; rótulos "superada_material" de S.113/118/120/163 do arquivo vetado NÃO se reproduzem em fonte oficial → tratar como não-confirmados (o jsonl oficial do gemeo já faz isso).
