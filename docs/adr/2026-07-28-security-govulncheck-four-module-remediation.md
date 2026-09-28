# ADR: Remediação govulncheck — grpc, x/text, x/image, antchfx/xpath (4 CVEs ativas)

Data: 2026-07-28

## Status

Adotado. Autorização explícita do dono em 2026-07-28 para correção de segurança.
Elevação de versão de 4 módulos já aprovados no grafo runtime — nenhum módulo novo entra,
nenhum escopo de import muda, publicação continua bloqueada por padrão.

## Contexto

`./tools/go-modern tool -modfile=tools/sca/go.mod govulncheck ./...` (3 execuções, exit status 3)
acusou QUATRO vulnerabilidades com símbolo alcançável a partir de código do módulo raiz
`portaljuridico` (Symbol Results, não apenas grafo):

| ID | Módulo | Em uso | Corrigida em | Classe | Trace de entrada no repo |
|---|---|---|---|---|---|
| GO-2026-6061 | google.golang.org/grpc | v1.80.0 | v1.82.1 | xDS RBAC / HTTP2 transport | `internal/ptbrspell` → `sync.Once` → `transport.NewHTTP2Client` (via zoekt) |
| GO-2026-5970 | golang.org/x/text | v0.38.0 | v0.39.0 | loop infinito em input inválido | `internal/dedupeexternaloracle`, `internal/collydemandmetadata`, `internal/ptbrtext`, `internal/ptbrunicodequality`, `internal/officialpdfprobe`, `internal/planaltochannel` (norm/width) |
| GO-2026-5061 | golang.org/x/image | v0.42.0 | v0.43.0 | panic em VP8/webp | `internal/officialpdfprobe` → pdfcpu → `webp.init` |
| GO-2026-4526 | github.com/antchfx/xpath | v1.3.5 | v1.3.6 | loop infinito | `internal/collydemandmetadata` → colly → htmlquery → `xpath.NodeIterator.MoveNext` |

Três das quatro são DoS (loop infinito/panic) em código que processa material EXTERNO
(PDF oficial, HTML de coleta de demanda, texto normalizado) — exatamente a superfície da fábrica.

## Decisão

Elevar as quatro versões para a versão EXATA corrigida, fixada em `go.mod`:

- `google.golang.org/grpc v1.80.0 → v1.82.1` — dependência INDIRETA
  (`internal/dedupeexternaloracle` → `github.com/sourcegraph/zoekt` → grpc).
- `golang.org/x/text v0.38.0 → v0.39.0` — dependência DIRETA
  (require principal; `internal/refinedpublicprose` importa `x/text/cases`).
- `golang.org/x/image v0.42.0 → v0.43.0` — dependência INDIRETA
  (`internal/officialpdfprobe` → `github.com/pdfcpu/pdfcpu` → `x/image/webp`).
- `github.com/antchfx/xpath v1.3.5 → v1.3.6` — dependência INDIRETA
  (`internal/collydemandmetadata` → `github.com/gocolly/colly/v2` → `github.com/antchfx/htmlquery` → xpath).

Comando: `./tools/go-modern get golang.org/x/text@v0.39.0 golang.org/x/image@v0.43.0
github.com/antchfx/xpath@v1.3.6 google.golang.org/grpc@v1.82.1` seguido de
`./tools/go-modern mod tidy` e `./tools/go-modern mod verify` (all modules verified).

### Mudanças colaterais do resolvedor/tidy (todas reportadas, nenhuma silenciosa)

`go.mod` — exatamente 7 linhas mudaram, nada entrou nem saiu do require:

- Colaterais arrastadas pelo grafo dos 4 alvos:
  - `golang.org/x/mod v0.36.0 → v0.37.0` (par de release do x/text/x/tools)
  - `golang.org/x/tools v0.45.0 → v0.47.0` (requisito do x/text v0.39.0)
  - `google.golang.org/genproto/googleapis/rpc 20260401024825 → 20260414002931` (requisito do grpc v1.82.1)

`go.sum` — 1404 → 842 linhas: 14 adicionadas (h1+go.mod dos 7 módulos elevados) e 576 removidas.
As remoções são as versões antigas dos 7 e hashes `/go.mod` de nós de grafo que o grpc/genproto
novos (grafo podado) deixaram de referenciar (aws-sdk, docker, gin, iris, chromedp etc. —
metadados de resolução antigos, nunca dependências compiladas). Entradas históricas de
`x/text`/`x/mod` usadas pelo gate de política ficaram idênticas (diff por módulo verificado).

## Licenças (verificadas nos arquivos LICENSE do module cache, não assumidas)

| Módulo@versão | Licença | Verificação |
|---|---|---|
| golang.org/x/text@v0.39.0 | BSD-3-Clause | LICENSE Go Authors, cláusula 3 presente |
| golang.org/x/image@v0.43.0 | BSD-3-Clause | idem |
| golang.org/x/mod@v0.37.0 | BSD-3-Clause | idem |
| golang.org/x/tools@v0.47.0 | BSD-3-Clause | idem |
| github.com/antchfx/xpath@v1.3.6 | MIT | LICENSE MIT padrão |
| google.golang.org/grpc@v1.82.1 | Apache-2.0 | LICENSE Apache 2.0 |
| google.golang.org/genproto/googleapis/rpc@20260414002931 | Apache-2.0 | LICENSE Apache 2.0 |

Todas dentro da allowlist do projeto (MIT/BSD/Apache). Nenhuma mudança de licença entre
as versões antigas e novas.

## Família de pins atualizada junto (a elevação não é só go.mod)

O repo fixa versão aprovada em código de gate — elevar sem atualizar os pins criaria
vermelho falso ou, pior, gate mentindo a versão. Atualizados no mesmo movimento:

- `internal/codex2policyenforcement/policy.go` — record `x-text-ptbr-cases` (AdoptedModuleVersion
  v0.39.0 + racional citando GO-2026-5970), record `golang.org/x/mod` (v0.37.0), mapa indireto do
  colly (`antchfx/xpath` v1.3.6).
- `internal/checkperformance/ledger.go` — evidência esperada de `v2-writing-semantic-*`,
  `public-prose-quality-preflight`/`refined-*`, `ptbr-unicode-quality` (x/text v0.39.0) e
  `pkgsite-*-module-audit` (x/mod v0.37.0).
- `internal/ptbrunicodequality/quality.go` — `NormModuleVersion = "v0.39.0"`.
- `internal/pkgsiteaudit/audit.go` — `GoModParserVersionPinned = "v0.37.0"`.
- Testes que asseguram esses pins: `internal/contract/codex2/codex2_policy_enforcement_test.go`
  (record, fixtures de go.mod/go.sum e evidências), `internal/checkperformance/ledger_test.go`,
  `internal/ossscaleintegration/coverage_test.go`. O controle negativo `x_text_wrong_version`
  continua REPROVANDO (agora `v0.38.0/go.mod` como stale — fora da allowlist histórica).

Artefatos versionados regenerados pelos generators sancionados (nunca editados à mão):

- `data/ops/check_performance_ledger.jsonl` — REGENERADO (`./tools/generate-check-performance-ledger`,
  304 checks; linhas x/text→v0.39.0, x/mod→v0.37.0; zero v0.38.0).
- `data/ops/pkgsite_{tools,scorecard,actionlint}_module_audit.jsonl` — REGENERADOS
  (parser pin `v0.37.0` em todos).
- `data/ops/pkgsite_module_audit.jsonl` (ROOT) — PENDENTE, bloqueio PRÉ-EXISTENTE e externo:
  o snapshot versionado é de 2026-06-30 (nem contém x/exp) e o generator hoje falha porque a
  API pkg.go.dev/v1beta responde 404 para as pseudo-versões INALTERADAS de `golang.org/x/exp`
  e `golang.org/x/perf`. RCA da frente de auditoria: tratar pseudo-versão 404 fail-closed com
  razão própria, ou repin. Independente do bump (as duas versões não mudaram).
- `data/ops/sca_cyclonedx_bom.json` — PENDENTE para o maestro:
  `./tools/run-heavy-throttled ./tools/generate-sca-sbom --root-only`. A execução nesta sessão
  ficou 33 min a 96% CPU sem progresso de IO (cyclonedx-gomod v1.10.0, `-test -licenses` sobre
  o grafo novo) e foi abortada pelo próprio especialista; requer janela dedicada/quieta e
  medição — se reincidir, abrir RCA no toolchain SCA (possível caso patológico do classificador
  de licenças).
- `data/research/codex2_policy_enforcement.jsonl` — reescrito pela própria execução do check
  de política (produtor sancionado) na próxima rodada do maestro.

## Alternativas consideradas

1. **Não elevar / aceitar risco** — rejeitada: 3 DoS alcançáveis por símbolo em superfície que
   processa PDF/HTML/texto externos; o dono autorizou explicitamente a correção.
2. **Elevar só os 4 sem atualizar pins/artefatos** — rejeitada: os gates de política e o ledger
   fazem igualdade exata; deixaria vermelho em cascata ou empurraria para relaxar gate (fraude).
3. **Excluir/ignorar via osv-scanner.toml** — rejeitada: ignore é para transitivo de ferramenta
   sem fix publicado (caso Docker documentado); aqui há fix upstream publicado e barato.
4. **Vendoring/patch local** — rejeitada: contra a disciplina do repo (proxy oficial, versão
   fixada, mínima superfície própria).

## Consequências e riscos residuais

- O grafo do grpc v1.82.1 é PODADO: go.sum encolheu 40% — menos superfície de supply chain.
- `x/text v0.39.0` não altera comportamento observado nos consumidores PT-BR
  (12 pacotes de teste focado verdes, incl. norm/width/cases; ver Evidência).
- PRÉ-EXISTENTE, não introduzido por esta ADR: `data/ops/ptbr_unicode_quality_evidence.jsonl`
  está stale desde 2026-07-18 (sha da fonte `data/editorial/refined_public_prose.jsonl` divergente;
  `ptbr_unicode_quality_live_metrics_stale` já disparava antes do bump) e o generator recusa
  regenerar porque a lane refined tem 590 registros contra mínimo DEC-014 de 7178 (blocker do
  passo 12 da cascata refined-public-prose). Quando a lane alcançar o stock, rodar
  `./tools/generate-ptbr-unicode-quality` fecha também o novo campo de identidade v0.39.0.
  NÃO se corrige editando a evidência à mão nem baixando o mínimo.
- Módulos-ferramenta isolados `tools/sca/go.mod` e `tools/ci/go.mod` ainda referenciam
  x/text v0.38.0 nos próprios grafos (dev-only, fora da superfície runtime e fora do escopo
  autorizado desta ADR); tratáveis em ciclo próprio de manutenção do toolchain SCA.

## Validação executada (evidência)

```bash
./tools/go-modern tool -modfile=tools/sca/go.mod govulncheck ./...   # antes: 4 vulns (exit 3) / depois: ver abaixo
./tools/go-modern mod verify                                        # all modules verified
flock /tmp/opt-wiki-agent-heavy.lock ./tools/go-modern test -count=1 ./internal/<pacote-consumidor>/
```

Testes focados nos consumidores reais dos 4 módulos e nos pacotes de gate editados
(resultado real da bateria em 2026-07-28, 18 pacotes):

- VERDES (15): `internal/dedupeexternaloracle` (zoekt/grpc+x/text), `internal/collydemandmetadata`
  (colly/xpath), `internal/officialpdfprobe` (pdfcpu/x/image), `internal/ptbrspell` (trace grpc),
  `internal/ptbrtext`, `internal/ptbrunicodequality`, `internal/portfoliowave3`*,
  `internal/v2internallinkgraph`, `internal/v2portfoliohintnormalize`, `internal/v2writingsemantic`,
  `internal/planaltochannel`, `internal/codex2policyenforcement`, `internal/pkgsiteaudit`,
  `internal/ossscaleintegration`, `cmd/collect-stj-precedentes-qualificados`.
  (*verde com `umask 0022`; o sandbox de agente usa 0077 e derruba fixtures que validam modo 0644 —
  artefato de ambiente, não do código.)
- VERMELHOS, todos com PRÉ-EXISTÊNCIA PROVADA por isolamento de variável
  (`go test -modfile=<go.mod anterior ao bump>`, mesmo código e mesmos dados):
  1. `internal/refinedpublicprose` — 55 falhas IDÊNTICAS com x/text v0.38.0 e v0.39.0
     (diff vazio entre os conjuntos). Família do passo 12 (detectores/reparadores da lane
     refined); zero relação com o bump.
  2. `internal/contract/codex2` — 6 falhas idênticas com as dependências antigas
     (frontier/DataJud/source-lock: regeneração live × JSONL persistido). O teste
     `TestCodex2PolicyEnforcementKeepsDependencies...`, que cobre exatamente os pins deste ADR,
     está VERDE.
  3. `internal/checkperformance` — apenas `TestRunGoCmdCachedArtifactClaimFingerprints...`:
     reprova em execução crua E sob `run-heavy-throttled`, desde o hardening do wrapper
     (dad121a3/86d48c41, 2026-07-22): a guarda de ancestralidade real recusa antes do
     `artifact_claim` que o teste espera. Reconciliar teste×script na frente do wrapper —
     burlar a guarda por env seria enfraquecer proteção anti-fraude e não foi feito.

## govulncheck — antes/depois (evidência primária)

- ANTES (3 execuções, exit 3): 4 vulnerabilidades com símbolo chamado (GO-2026-6061,
  GO-2026-5970, GO-2026-5061, GO-2026-4526) + 3 findings módulo-não-chamado.
- DEPOIS (exit 0): `No vulnerabilities found. Your code is affected by 0 vulnerabilities.`
  Resta 1 finding módulo-não-chamado: GO-2026-5932 em `golang.org/x/crypto v0.53.0` —
  SEM versão corrigida publicada (osv-scanner: `FIXED VERSION --`); nada a elevar hoje;
  o código não chama o símbolo vulnerável. Nenhuma vulnerabilidade NOVA introduzida pelo bump.

## Nota cross-frente registrada no log de engenharia

Durante a validação, a onda concorrente de memoização deletou acidentalmente
`var declarativeNonAlphanumericPattern` em `internal/v2ingest/current_legal_facts.go`
(quebrando a compilação de 4+ pacotes); a linha foi restaurada byte-idêntica ao HEAD por
edição pontual, preservando as 82 inserções da onda. Registro completo em
`docs/goal/MAESTRO_CODEX_LOG.md` (entrada 2026-07-28 do especialista-crítico).
