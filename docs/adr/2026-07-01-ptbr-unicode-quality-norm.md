# ADR: Unicode NFC quality gate for PT-BR public prose

Data: 2026-07-01

## Decisao

Adotar `golang.org/x/text/unicode/norm v0.38.0`, ja presente no repo, como adapter auditavel em `internal/ptbrunicodequality` para validar o corpus vivo bloqueado de `data/editorial/refined_public_prose.jsonl`.

O adapter nao reescreve conteudo automaticamente. Ele materializa evidencia em `data/ops/ptbr_unicode_quality_evidence.jsonl` e bloqueia release quando texto publico visivel tiver forma nao NFC, sinais comuns de mojibake, caractere de substituicao ou controles invisiveis.

## Comparacao OSS

- `golang.org/x/text/unicode/norm`: escolhido. A documentacao do Go define o pacote como suporte a normalizacao Unicode, e UAX #15 explica que manter texto em forma normalizada garante representacao binaria unica para strings equivalentes. Isso complementa os gates existentes sem novo runtime pesado.
- `github.com/hunspell/hunspell`: rejeitado como nova integracao nesta frente. Hunspell e relevante para ortografia e morfologia, mas o repo ja usa Hunspell por `internal/ptbrspell` com dicionario PT-BR, alem de LanguageTool e Vale. Integrar outro wrapper Hunspell duplicaria a camada.
- `morfologik/morfologik-stemming`: rejeitado. O projeto e Java, focado em automatos/dicionarios morfossintaticos, com dicionario polones como referencia principal. Para PT-BR neste repo, Simplemma, Snowball, Hunspell e LanguageTool ja cobrem lema/stem/ortografia com menor custo operacional.
- `github.com/clipperhouse/uax29`: rejeitado como nova frente porque ja esta integrado em `internal/ptbrtext` e `ptbr-text-shape-release` para palavras e sentencas. UAX #29 continua essencial para segmentacao, mas nao cobre por si so normalizacao NFC.
- Lexers de codigo ou sintaxe geral: rejeitados. Eles classificam tokens de linguagens/sintaxe e nao resolvem qualidade linguistica PT-BR natural no corpo juridico.

## Escopo permitido

- `internal/ptbrunicodequality` como adapter e validador.
- `cmd/generate-ptbr-unicode-quality` e wrappers `tools/generate-ptbr-unicode-quality` / `tools/check-ptbr-unicode-quality`.
- `data/ops/ptbr_unicode_quality_evidence.jsonl`, sempre bloqueado, `index_policy=noindex`, sem texto bruto persistido.
- Registro nos gates de `internal/checks`, `internal/checkselection`, `internal/checkperformance` e `internal/ossscaleintegration`.

## Gates

- `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `approval=false` e `public_path=""`.
- `MinimumReleaseRecords` default = 10000.
- Check read-only deve falhar se a evidencia estiver ausente, stale ou com blocker.
- Gerador deve usar lock de fabrica e cache Go; check wrapper deve usar `tools/run-check`.

## Fontes externas usadas

- https://pkg.go.dev/golang.org/x/text/unicode/norm
- https://www.unicode.org/reports/tr15/
- https://www.unicode.org/reports/tr29/
- https://github.com/hunspell/hunspell
- https://github.com/morfologik/morfologik-stemming
- https://github.com/clipperhouse/uax29

## Autocritica

Esta integracao nao substitui LanguageTool, Vale, ptbrspell, Simplemma, Snowball nem UAX #29. Ela fecha uma lacuna anterior: texto com acento decomposto ou mojibake podia atravessar scanners que comparam tokens ja normalizados, enquanto a superficie publica continuaria visualmente suspeita. O ganho e uma barreira barata e auditavel antes de release, sem abrir publicacao.
