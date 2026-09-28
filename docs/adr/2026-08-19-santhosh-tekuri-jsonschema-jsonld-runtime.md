# ADR 2026-08-19: santhosh-tekuri/jsonschema/v6 como validador de JSON-LD no render e de contratos JSONL

Status: ADR **retroativo**. A dependência entrou em `go.mod` no commit `246cf945` (2026-06-30, "Integrate JSON Schema JSONL gate") sem ADR próprio; este documento registra o estado medido em 2026-08-19. **É a única das sete dependências auditadas que roda no caminho de produção.**

## Contexto

Duas necessidades diferentes convergem no mesmo validador:

1. **JSON-LD no HTML público.** Toda página publicada emite `<script type="application/ld+json">` com `Article`, `FAQPage`, `HowTo`, `QAPage`, `BreadcrumbList`, `Organization`, `WebSite` e `LegalService`. JSON-LD malformado ou com campo obrigatório ausente é defeito que só aparece no buscador, semanas depois — precisa ser barrado antes de o HTML existir.
2. **Contratos das camadas JSONL bloqueadas.** As cadeias editoriais têm campos obrigatórios e flags públicas que precisam estar fechadas antes do release. Validar isso com condicional em Go espalha a regra pelo código; um schema por camada mantém o contrato declarativo e comparável por hash.

Draft 2020-12 é o alvo, e `santhosh-tekuri/jsonschema/v6` é a implementação Go de referência para essa versão do padrão.

## Versão fixada e licença

- Módulo: `github.com/santhosh-tekuri/jsonschema/v6`, versão **`v6.0.2`**, fixada em `go.mod` linha 36.
- Licença: **Apache-2.0**, lida em `~/go/pkg/mod/github.com/santhosh-tekuri/jsonschema/v6@v6.0.2/LICENSE`.
- Constantes de proveniência batendo com o disco em dois pontos: `internal/structureddata/structured_data.go:26-29` e `internal/jsonschemagate/gate.go:30-33` (ambos `ModuleVersionPinned = "v6.0.2"`, `ModuleLicense = "Apache-2.0"`, `SchemaDraft = "https://json-schema.org/draft/2020-12/schema"`).

Atenção a uma homonímia que engana busca: `go.mod` linha 79 tem `github.com/google/jsonschema-go v0.4.3 // indirect` — módulo diferente, indireto, sem relação com esta adoção.

## Onde é usada de fato

Quatro imports, em dois pacotes:

- `internal/structureddata/structured_data.go:14`
- `internal/structureddata/collection.go:11`
- `internal/structureddata/institutional.go:7`
- `internal/jsonschemagate/gate.go:18`

Uso real, com a cadeia de chamada fechada até o render:

**No caminho de render (produção).** `internal/render/render.go:567` chama `structureddata.RenderScriptWithIdentity(page, identity, baseURL)`, definida em `structured_data.go:308`, que delega a `renderArticleScript` (`structured_data.go:312`); dentro dela, `structured_data.go:328` executa `articleSchema().Validate(decoded)` e **só devolve a tag `<script>` se a validação passar** (`structured_data.go:331`). O mesmo padrão vale para os outros tipos, via `emitJSONLD(value, schema, codePrefix)` (`structured_data.go:1364`, com `schema.Validate(decoded)` em `structured_data.go:1375`), chamado por `RenderWebSiteScript` (1189), `RenderLegalServiceScript` (1225), `RenderHowToScript` (1258), `RenderQAPageScript` (1342) e `RenderInstitutionalScript` (`institutional.go:236`). Os schemas são compilados uma vez em variáveis de pacote (`jsonschema.NewCompiler()` em `structured_data.go:1936`, `2041`, `collection.go:179`, `institutional.go:338`), então a compilação não se repete por página.

Chamadas de render que atravessam esse caminho: `render.go:567, 574, 581, 588, 609, 615, 621, 627, 649` — Article, FAQ, HowTo, QAPage, Breadcrumb, Organization, WebSite, LegalService e institucional.

**No caminho de gate.** `internal/jsonschemagate/gate.go:447-448` compila um schema por camada JSONL (`compileSchema`) e valida os registros vivos.

## Runtime de produção: SIM

Única das sete que os entrypoints públicos alcançam. Por grafo estático de imports a partir de cada `main.go`:

- `cmd/server` (servidor HTTP :8080) — **alcança**, via `internal/structureddata`.
- `cmd/build` (gera `public/`) — **alcança**, via `internal/structureddata`.
- `cmd/publish-v2-direct` (promoção transacional) — **alcança**, via `internal/structureddata`.
- `cmd/check` — alcança pelos dois pacotes (`structureddata` e `jsonschemagate`).

Total de 180 entrypoints alcançam o módulo (limite superior: `//go:build` não avaliado pelo walker; `cmd/server/main.go`, `cmd/build/main.go`, `cmd/check/main.go` e `cmd/publish-v2-direct/main.go` foram conferidos e não têm build tag).

Consequência prática: **toda página renderizada passa por validação de schema**. Se o schema reprovar, o bloco JSON-LD daquele tipo simplesmente não é emitido (o `Report` volta com `structured_data_schema_validation_failed` e o chamador em `render.go` testa `report.Passed()` antes de concatenar) — a página sai sem aquele dado estruturado em vez de sair com dado inválido. É fail-safe para o HTML, mas silencioso: uma regressão de schema degrada SEO sem quebrar o build.

## Benchmark: REALIZADO no gate JSONL; NÃO MEDIDO no render

**Medido**, em `data/ops/jsonschema_jsonl_gate_evidence.jsonl`: `live_record_count: 40000`, `live_byte_count: 548.862.075` (≈ 549 MB), `scan_duration_ms: 21114`, `schema_validation_errors: 0`, `invalid_json_lines: 0`, `required_layer_coverage_ready: true`. Critério gravado: `"jsonschema_v6_draft2020_12_validates_live_40k_jsonl_public_flags_closed_under_30s"` — 40k sob 30 s, cumprido com 21,1 s (≈ 1.894 registros/s). Flags públicas fechadas no registro (`publication_allowed`, `render_allowed`, `sitemap_allowed`, `approval` em `false`; `index_policy: "noindex"`).

**Não medido, e é a lacuna relevante desta dependência:** o custo por página da validação no caminho de render. Nenhum benchmark do repositório isola `articleSchema().Validate()` por página, e o alvo declarado do projeto é 10.000 páginas subindo a centenas de milhares. Os 21,1 s para 40k registros JSONL são indicativo favorável — e não substituem a medição do caminho de render, que valida documentos diferentes, menores e mais numerosos por página (até nove blocos JSON-LD). A compilação de schema está amortizada em variáveis de pacote, o que remove o custo dominante; o custo residual de `Validate` por documento permanece não medido. Também não medido: 100k e 1M no gate JSONL.

## Alternativas consideradas

Diferente das outras seis, esta dependência **tem registro contemporâneo de decisão** — em `internal/codex2policyenforcement/policy.go:1647-1680`, na função `adoptedJSONSchemaJSONLGateDependencyRecord()`, com campos preenchidos de risco e escopo. Vale citar o que está lá, porque é fonte primária da época:

- Justificativa de escolha: "maintained public Go JSON Schema implementation with Draft 2020-12 support; use is restricted to internal blocked JSONL schema validation and JSON-LD structured data evidence".
- Risco operacional: "low: standalone runtime dependency with no service, network or storage side effects in the approved adapter".
- Risco de qualidade: "low_medium: schema changes can create false green/red release gates, mitigated by generated per-layer schemas, tests and freshness validation over live 40k JSONL records and rendered rehearsal HTML".
- Escopo de import fixado: `AllowedImportScopes = []string{"internal/jsonschemagate/", "internal/structureddata/"}` — e a auditoria de 2026-08-19 confirma que os quatro imports respeitam esse limite.
- `DecisionReason`: "santhosh-tekuri/jsonschema is approved only behind internal/jsonschemagate and internal/structureddata for blocked JSONL and rendered JSON-LD schema validation; it cannot open render, sitemap, public_path, approval or publication".

O que **não** está documentado é a comparação com alternativas: `xeipuuv/gojsonschema` (Draft 7, sem 2020-12), `qri-io/jsonschema` (2020-12, menos mantida) ou validação manual em Go. A escolha por Draft 2020-12 restringe fortemente o campo, mas a comparação não foi escrita e não será reconstruída aqui.

**Referência pendente encontrada na auditoria:** o mesmo registro fixa `record.ADRPath = "docs/DECISIONS.md"` (`policy.go:1668`). O arquivo existe (404 KB), mas a busca por `jsonschema` nele retorna **zero ocorrências** — a decisão nunca foi escrita ali. O ponteiro é, portanto, uma referência morta apontando para arquivo vivo: o pior tipo, porque parece resolvida. Este ADR é o destino correto desse campo.

## Risco e saída

Licença Apache-2.0, permissiva; sem coleta, cópia ou publicação de texto jurídico pela biblioteca.

Riscos específicos por ser a única em produção:

- **Falso verde silencioso.** Schema frouxo aprova JSON-LD pobre; schema errado suprime bloco válido sem alarme, porque a supressão é o comportamento normal do render. Mitigação existente: schemas versionados e testes em `internal/render` e `internal/structureddata`.
- **Custo por página não medido**, conforme acima — a corrigir com benchmark dedicado antes da escala para centenas de milhares de URLs.
- **Superfície de ataque**: a biblioteca só compila schemas do próprio repositório e valida documentos gerados localmente; não busca `$ref` remoto no uso atual.

Se a dependência sumisse: **é a saída mais cara das sete.** Quebra a compilação de `cmd/server`, `cmd/build`, `cmd/publish-v2-direct` e de mais 177 entrypoints. Sem substituto, toda página perderia a validação de JSON-LD antes da emissão — o HTML continuaria sendo gerado, mas sem a garantia de que o dado estruturado está bem formado, que é justamente o que sustenta rich results e citação por assistentes de IA. A saída realista não é remover: é substituir por outra implementação Draft 2020-12 atrás das mesmas funções `articleSchema()`/`emitJSONLD()`/`compileSchema()`, que já isolam a API de terceiro em um punhado de pontos.

## Consequências

O registro documental exigido pelo contrato passa a existir para a dependência que mais o exigia. Ficam registradas duas pendências para sessão dedicada: (a) benchmark do custo por página da validação JSON-LD no caminho de render, hoje não medido e relevante para 10k→100k páginas; (b) `internal/codex2policyenforcement/policy.go:1668` aponta `ADRPath` para `docs/DECISIONS.md`, que não documenta esta dependência — o campo deve passar a apontar para `docs/adr/2026-08-19-santhosh-tekuri-jsonschema-jsonld-runtime.md`.
