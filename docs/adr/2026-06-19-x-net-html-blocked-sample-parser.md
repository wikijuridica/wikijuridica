# ADR: golang.org/x/net/html para amostras HTML bloqueadas

Date: 2026-06-19

## Status

Accepted as internal blocked runtime dependency. This ADR documents the operational integration of `golang.org/x/net/html` through the existing `golang.org/x/net v0.56.0` module. It does not approve scraping, source cloning, public rendering, sitemap entry, `published_manifest`, `content/pages.json`, `public/` writes, or any public URL.

## Context

The P0 demand research layer needs limited text samples from permitted HTML sources to understand language, context and extraction quality before authorial rewrite. Regex-based HTML extraction is brittle: it can keep navigation chrome, script/style text, malformed fragments, or miss the real `main`/`article` body. The current implementation imports `nethtml "golang.org/x/net/html"` only in `internal/demandobservations`, where official HTML pages are parsed into blocked `demand_content_samples` candidates.

Official source review for this dependency:

- Module: `golang.org/x/net`
- Imported package: `golang.org/x/net/html`
- Adopted version: `v0.56.0`
- License: `BSD-3-Clause`
- Official package documentation: `https://pkg.go.dev/golang.org/x/net/html`
- Official module documentation: `https://pkg.go.dev/golang.org/x/net`
- Official repository/tag: `https://go.googlesource.com/net/+/refs/tags/v0.56.0`
- License evidence: `https://pkg.go.dev/golang.org/x/net/html?tab=licenses`

The official Go package documentation describes the package as an HTML5 tokenizer and parser and notes that callers must provide UTF-8 encoded HTML and take care when parsing untrusted input. The repository is an official Go supplementary module, not the Go standard library, so the dependency stays exact-versioned and scope-limited.

## Decision

Use `golang.org/x/net/html` only for internal blocked HTML sample parsing in `internal/demandobservations`.

The allowed behavior is narrow:

- Parse HTML with `nethtml.Parse` after `looksLikeHTMLDocument` detects an HTML document.
- Extract limited visible text from `html.main`, falling back to `html.article` and then `html.body` only when the selected node has research body.
- Extract `html.title` and `html.meta.description` or `og:description`.
- Skip non-content tags: `script`, `style`, `nav`, `header`, `footer`, `noscript` and `template`.
- Preserve the existing response/sample limits: default response cap `262144` bytes, maximum response cap `1048576` bytes, default sample cap `4000` runes, maximum sample cap `8000` runes, and raw textual sample cap `1200` runes.
- Store only blocked, bounded research samples with `full_text_stored=false`, `rewrite_required=true`, `authorial_review_required=true`, `legal_editorial_review_needed=true`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false` and `public_path=""`.

The forbidden behavior is explicit:

- Do not use this dependency to crawl, scrape at scale, mirror, clone, republish, or create public legal content from source text.
- Do not treat official source body as final legal source text for publication.
- Do not persist full HTML body, full text, raw official page clones, screenshots, public routes, sitemap entries or rendered HTML.
- Do not import `golang.org/x/net/html` outside `internal/demandobservations` unless a new ADR, evidence file, tests and policy update approve the exact scope.

## Risks And Mitigations

Supply-chain risk is medium for a new runtime module and low-medium for transitive surface: `golang.org/x/net v0.56.0` is a tagged official Go module, but it is still outside stdlib. Mitigation: exact version, policy gate, import-scope validation and no public runtime output.

Performance risk is low-medium. DOM parsing is CPU-bound and can become expensive on large or hostile HTML. Mitigation: existing response byte caps, sample rune caps, request timeout and blocked sample-only use. Any future 10k/100k-scale parser run must be benchmarked before release.

Legal/editorial risk is medium if parsed source text is mistaken for publishable content. Mitigation: all samples remain blocked research evidence, require authorial rewrite, legal-editorial review and official source review, and keep public flags closed.

Security risk is low-medium for parsing untrusted HTML as data. Mitigation: no script execution, no browser/runtime rendering, no public echo of parsed HTML, visible-text extraction only, non-content tag skipping and existing network/terms gates.

## Consequences

This integration improves extraction correctness for blocked demand samples and reduces brittle regex behavior, but it does not reduce `deficit_to_10000` and does not publish anything. It only strengthens the factory path before authorial rewrite, source review, anti-template checks, CTA/OAB gates, HTML/crawl validation and public release.

## Validation

Focused validation commands for this ADR and evidence:

- `./tools/check-codex2-policy-enforcement --timings`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/demandobservations -run 'TestParseOfficialHTMLContentSampleCandidates|TestParseOfficialHTMLContentSampleCandidatesUsesDOMAndSkipsChrome'`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/contract -run TestCodex2PolicyEnforcement`
- `git diff --exit-code -- public/ content/pages.json data/editorial/published_manifest.jsonl public/sitemap.xml public/sitemaps public/robots.txt`
- `git diff --check -- docs/adr/2026-06-19-x-net-html-blocked-sample-parser.md data/research/x_net_html_blocked_sample_parser_evidence.jsonl`

