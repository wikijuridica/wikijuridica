# Propostas da Fase 9 para arquivos de outras frentes — 2026-08-26

Tudo aqui foi **medido** por mim (frente de dependências e cadeia de suprimento) em arquivos que **não são meus para editar**. Cada item traz o comando que reproduz a medição. Nenhuma linha destes arquivos foi tocada.

---

## 1. `internal/structureddata` — NÃO remover o `HowTo` (T9.14)

**A medição do plano confere, e é a única parte que confere.** 293 páginas publicam `HowTo`, somando **1.149.327 bytes** de marcação. Reproduzível:

```
grep -rl '"@type": *"HowTo"' public/ | wc -l          # 293
./tools/generate-public-jsonld-validation --dry-run    # tipos por nó, incluindo HowTo
```

**A conclusão do plano — "marcação sem retorno possível" — é falsa, e a fonte que a derruba é do próprio Google.** A documentação de HowTo (https://developers.google.com/search/docs/appearance/structured-data/how-to, rich result removido em **2023-09-14**) diz, sobre deixar a marcação no ar:

> *"you may leave the markup on your site since other search engines and systems can still utilize it for understanding web page content."*

Para um portal cuja Fase 9 inteira existe para ser **lido e citado por agente de IA**, "other systems" não é nota de rodapé: é o público-alvo. Remover marcação legível por máquina para otimizar um rich result que não existe mais troca um ganho de zero por uma perda real.

**E há o teste de consistência, que é o argumento decisivo.** Aplicado com coerência, o critério do plano ("Google removeu o rich result → remover a marcação") atinge muito mais que o `HowTo`:

| Tipo | Páginas | Bytes | Situação oficial |
|---|---:|---:|---|
| `HowTo` | 293 | 1.149.327 | rich result removido em 2023-09-14 |
| **`FAQPage`** | **8.207** | **6.286.643** | restrito a governo/saúde em 2023-09-14 e **deixou de aparecer na Busca em 2026-05-07** (doc removida em junho/2026) |

O `FAQPage` é **28× mais páginas e 5,5× mais bytes**, foi depreciado **mais recentemente**, e o plano não o mencionou. Ou o critério vale para os dois — e aí a proposta seria apagar 6,3 MB de marcação semântica —, ou o critério está errado. Está errado.

**Proposta:** manter os dois. E **não** substituir `HowTo` por `FAQPage`: os dois perderam elegibilidade de rich result, e a troca seria trabalho para chegar ao mesmo lugar.

**Achado lateral, este sim acionável:** cinco páginas não têm nenhum bloco JSON-LD. Três são esperadas (`50x.html`, `/buscar/` que é `noindex`, e a home de erro); **duas merecem decisão da sua frente**: `/contato/advogado/` e `/fontes/` (mais `/fontes/planalto/`). São rotas públicas indexáveis sem nenhum dado estruturado.

---

## 2. `internal/httpserver` — o span de OpenTelemetry no caminho quente (T9.15)

**Medido:**

- `internal/httpserver/httpserver.go:1139` abre um span por requisição:
  `otel.Tracer("portaljuridico/internal/httpserver").Start(..., trace.WithSpanKind(trace.SpanKindServer))`
- `internal/httpserver/httpserver.go:2248` (`annotateHTTPSpan`) anexa atributos a cada resposta, incluindo `attribute.String("otel.module_path", ...)` e `otel.module_version`.
- **O único `otel.SetTracerProvider` do repositório inteiro está em `internal/checks/checks.go:6595`** — dentro do harness de gate, não em produção:
  ```
  grep -rn 'SetTracerProvider' internal/ cmd/ --include='*.go' | grep -v _test
  ```

Ou seja: em produção o provider global é o *no-op*, não há exportador e **nenhum span sai da máquina**. O `Start` no-op é barato, mas `annotateHTTPSpan` monta os atributos de qualquer jeito, a cada requisição, e ninguém os lê.

**Proposta (duas rotas, a escolha é sua):** (a) configurar um `TracerProvider` real com exportador local, transformando o custo em observabilidade de verdade; ou (b) fechar o caminho quando não há provider, evitando montar atributos que ninguém lê. **Não** proponho remover a instrumentação — ela está correta e é a base de (a).

Junto: `go.opentelemetry.io/otel` (+ `/sdk`, `/trace`) é uma das **seis famílias de dependência direta sem ADR e sem registro nenhum** (ver §5).

---

## 3. `nginx` (frente de produção/borda) — capturar `Signature-Agent` (T9.13)

**Por que só isto, e não o verificador.** `cloudflare/web-bot-auth` é **Rust**, não importável em Go; e um verificador RFC 9421 alcançaria **3,95% do tráfego**. A decisão é de *colocação* (borda × origem), não de biblioteca — e não se decide colocação sem saber quem já assina.

**Hoje o portal não consegue saber.** O `log_format wj_main` não captura o cabeçalho `Signature-Agent`, então não há como medir quantos agentes já assinam requisições. Instrumentar o log é **pré-requisito** de qualquer decisão, e custa uma variável.

**Mudança proposta** — acrescentar ao `log_format wj_main`, sem remover nem reordenar nada do que já existe:

```nginx
# Web Bot Auth (RFC 9421): quem assina requisicao declara a chave em
# Signature-Agent. Sem capturar, nao ha como medir adocao e a decisao de
# verificar (na borda ou na origem) fica sem base.
'"sigagent":"$http_signature_agent",'
'"sighdr":"$http_signature",'
'"siginput":"$http_signature_input",'
```

Cabeçalho ausente vira string vazia — nenhuma linha do log quebra, nenhum consumidor atual perde campo. Depois de uma semana de coleta dá para responder, com número, se vale construir o verificador.

**Cuidado com o consumidor:** quem faz o parse do `wj_main` precisa tolerar campos novos antes do deploy, senão o log passa a ser rejeitado. Vale conferir antes de aplicar.

---

## 4. `go.mod` — os bumps sem CVE que eu **não** executei, e por quê (T9.7)

Os dois candidatos são legítimos e ambos ficam **dentro do mesmo major** (conferido com `go list -m -versions`):

- `github.com/RoaringBitmap/roaring/v2` **v2.14.5 → v2.25.0** (dentro do binário público)
- `github.com/mmcdole/gofeed` **v1.3.0 → v1.4.2**

**O que impede fazer agora não é o bump, é a cauda de evidência.** A versão `v2.14.5` está escrita, como dado, em pelo menos seis artefatos versionados:

```
data/ops/scale_index_benchmark_evidence.jsonl      (bitmap_version_pinned)
data/ops/roaring_postings_dedupe_evidence.jsonl    (module_version_pinned)
data/ops/check_performance_ledger.jsonl            (3 linhas)
data/ops/pkgsite_module_audit.jsonl                (audita o pin do go.mod)
data/ops/sca_cyclonedx_bom.json                    (2 ocorrencias)
```

Cada um tem **gerador próprio** e alguns são caros (o `roaring_postings_dedupe` leva ~11 s de build sobre 10.000 documentos; o `pkgsite_module_audit` chama a API do pkg.go.dev). Bumpar sem regenerar deixaria seis artefatos **declarando uma versão que o `go.mod` não tem** — que é exatamente a classe de defeito que o gate `sca-govulncheck-evidence` (commit `4a21896c`) passou a proibir hoje. Fazer isso pela metade seria pior do que não fazer.

Some-se que a regeneração do SBOM da raiz estava **em voo** durante esta sessão: bumpar no meio invalidaria o artefato sendo gerado.

**Proposta:** uma passada única e orçada, nesta ordem — bump → `go mod tidy` → testes dos pacotes importadores (`internal/roaringpostings`, `internal/scaleindex`, `internal/densepairset`, `internal/semanticclusterindex`, `internal/demandobservations`) → regenerar os seis artefatos pelos geradores deles → um commit pesado.

**`ristretto` fica de fora e é proposta, não tarefa.** Há duas linhas major no mesmo build (`v0.2.0` direta + `v2.2.0` indireta), e a `v0.2.0` é de `internal/refinedpublicprose`, protegido pela DEC-017. Consolidar as linhas exige editar pacote protegido: não toquei, e recomendo que quem tocar leia a DEC-017 antes.

---

## 5. Resíduo de ADR — são **seis** famílias, não uma e não dezoito (T9.9)

A varredura anterior alegou "18 diretas sem ADR". Ela cruzou só `docs/adr/` e `DECISIONS.md`, ignorando `internal/codex2policyenforcement/policy.go` e o ledger `data/research/codex2_policy_enforcement.jsonl`. Refeita a conta contra **as quatro fontes**, e conferida por mim módulo a módulo:

```
for m in <modulo>; do grep -rl "$m" docs/adr/ docs/goal/DECISIONS.md \
  internal/codex2policyenforcement/policy.go \
  data/research/codex2_policy_enforcement.jsonl; done
```

**Têm registro** (a hipótese "sem ADR" era falsa para eles): `modelcontextprotocol/go-sdk`, `andybalholm/brotli`, `prometheus/client_golang`, além dos 16 já cobertos por ADR próprio (`bluge`, `meilisearch-go`, `simhash`, `miekg/dns`, `simdjson-go`, `opensearch-go`, `pdfcpu`, `zoekt`, `tdewolff/parse`, `tidwall/sjson`, `typesense-go` e outros).

**Sem registro em fonte nenhuma — o resíduo real:**

1. `go.opentelemetry.io/otel` (+ `/sdk`, `/trace`) — ver §2
2. `github.com/felixge/fgprof`
3. `github.com/google/pprof`
4. `github.com/allegro/bigcache/v3`
5. `github.com/sony/gobreaker/v2`
6. `github.com/cenkalti/backoff/v5`

Quatro das seis (otel, fgprof, pprof e, por vizinhança, gobreaker) são a pilha de observabilidade/resiliência que **não está ligada a nada**. Isso sugere que o ADR certo não é um por módulo, e sim **um ADR de decisão sobre a pilha de observabilidade** — depois de decidir §2. Escrever seis ADRs retroativos agora seria documentar em vez de decidir.

*Nenhum `BenchmarkEvidencePath` registrado em `policy.go` aponta para arquivo inexistente — os 57 conferidos existem no disco.*

---

## 6. Higiene de build (T9.15, nível de recomendação)

- **Não existe `vendor/`.** O build offline depende de um module cache de **18 GB** (`du -sh $(./tools/go-modern env GOMODCACHE)`) que vive fora do git e está sujeito a GC. Um `go mod vendor` do módulo raiz tornaria o build reprodutível sem rede — ao custo de peso no repositório. Decisão do dono.
- **`GOTOOLCHAIN=auto` no caminho interativo × `local` no pre-commit** (`.githooks/pre-commit:169` e `:177`) — e essa assimetria **me mordeu hoje**, o que é a melhor evidência de que ela é real: um módulo de ferramenta declarando `go 1.26.6` compilou pelo wrapper e foi **rejeitado** pelo pre-commit com `go.mod requires go >= 1.26.6 (running go 1.26.5; GOTOOLCHAIN=local)`.
- **Consequência mais séria da linha acima, e vale conferir:** o `go.mod` declara `toolchain go1.26.6`, o wrapper `tools/go-modern` roda **go1.26.6**, mas o pre-commit — que é o gate de segurança — compilou com **go1.26.5**, segundo a própria mensagem de erro dele. O go1.26.5 é a versão que GO-2026-6179 e GO-2026-6180 listam como afetada (`fixed 1.26.6`), e foi por isso que o toolchain subiu hoje de manhã. O binário publicado sai pelo wrapper, então **produção não está exposta**; o que está desalinhado é o toolchain com que o gate valida. Recomendo localizar qual `go` o hook resolve sob `PATH=/usr/bin:/bin` (o `/usr/bin/go` do sistema é 1.19.8 e o `/usr/local/go/bin/go` é 1.26.6, então nenhum dos dois explica o 1.26.5) e alinhá-lo ao `toolchain` do `go.mod`.
