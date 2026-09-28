# Refutacao adversarial — desenho "Publicar e corrigir: nenhum juizo e terminal"

VEREDITO: CAI.

## Achado que muda o enquadramento inteiro (medido nesta sessao)

O gate VIVO de near-dup do caminho de publicacao nao e 0,70/5-grama. E:

- `internal/quality/quality.go:84`  `const nearDuplicateThreshold = 0.82`
- `internal/quality/quality.go:743` `fastHashedShingles(page.PlainText(), 5)` (5-gramas, digito NAO neutralizado)
- `internal/quality/quality.go:674` emite `near_duplicate_content`
- `cmd/publish-v2-direct/qualitygate.go:21-31` `criticalQualityCodes` NAO contem `near_duplicate_content`
- `cmd/publish-v2-direct/qualitygate.go:117` `if len(criticos) == 0 { return nil }`  -> near-dup PUBLICA como medio
- `internal/v2bodyneardup/neardup.go:66-69` comenta explicitamente: `QualityThreshold = 0.82` e "o limiar que o gate de producao (internal/quality) aplica"

Logo o gerador (`cmd/generate-acordao-pages/main.go:102-103`, 0,70 + 3-gramas +
`reDigito.ReplaceAllString(limpo,"N")` em `:2187-2196`) e mais severo que o gate
vivo em TRES eixos ao mesmo tempo, e o gate vivo nem bloqueia.

O desenho declara "o veredito e o limiar ficam identicos; muda so a consequencia".
Mantendo a regua identica ele CONGELA a miscalibracao de tres eixos e a transforma
em rotulo permanente de medio em 532 paginas. A emenda minima (3 constantes) fica
fora do escopo que ele mesmo declarou.

## Medicoes proprias

| medicao | numero | fonte |
|---|---|---|
| registros em `data/editorial/v2_pages/*.jsonl` | 11.225 | contagem propria |
| paginas /jurisprudencia/ fora do shard (`aceitas` inicial) | 1.134 | contagem propria |
| registros no shard `stj-acordao-derivado-01.jsonl` (`previas`) | **0** | contagem propria |
| 3-gramas neutralizados por pagina /jurisprudencia/ | mediana 389, media 406, max 1.590 | medicao propria |
| registros `publish=true` no censo | 11.125 | censo |
| dos quais tombstones `skipped:true` (0 secoes, intent compartilhado com pagina viva) | 19 | medicao propria |
| **paginas ATIVAS `publish=true`** | **11.106** (bate com o enunciado) | medicao propria |
| dessas, title fora de 20-65 (vazio incluido) | **0** | medicao propria |
| dessas, meta fora de 70-160 | **0** | medicao propria |
| dessas, com menos de 2 `official_sources` | **2.323** | medicao propria (desenho disse 2.423 — nao reproduz) |

Refutacao TENTADA E FALHADA: `internal/v2ingest/transaction.go:3063` decodifica
`transactionJournal`, nao o registro de pagina — campo novo no shard nao morre ali.
`internal/v2ingest/adjudicate_shard.go:1143-1167` SIM impoe
`DisallowUnknownFields` + igualdade byte a byte com o re-marshal canonico, mas
sobre `v2portfolioindex.PortfolioRecord` (portfolio), nao sobre a pagina.

## Kill shots

1. **Censo: semantica invertida.** `tools/generate-v2-publication-severity:688`
   `if record.get("skipped"): critical.append("intencao_pulada_deliberadamente")`
   e `:799 publish = not critical`. `skipped` NAO e "padrao de passagem
   publish=false" — e CRITICO. Ou `pendente` usa `skipped` (e infla o critico de
   100 para ~3.600, repetindo o erro que o proprio comentario :674-687 documenta
   como tendo "quase mandado redigir 17 paginas que nao devem existir"), ou
   `pendente` e campo novo que o censo nunca le (`record.get`), e entao TODAS as
   4.763 publicam. Nao ha terceira opcao.

2. **O orcamento nao e aplicado em lugar nenhum.** `v2publish.LoadPages:193`
   descarta so `len(page.Sections)==0`; pendente TEM secoes -> carrega.
   `v2publish.Severity:163-175` nao tem campo de estado. `SelectPublishable:391-446`
   le so `row.Publish`. Tres edicoes em duas linguagens, apresentadas como reuso.

3. **O(n²) multiplicado ~11x numa passada que o proprio repo mediu falhando.**
   `main_test.go:583-589`: "com n = 1.569 a passada nao terminou em 10 minutos num
   nucleo... passar de algumas centenas por passada exige indexar o anti-molde
   (bucket por shingle ou MinHash)". Hoje: 1.260 iterados x ~1.384 assinaturas
   ~= 1,7M pares. Desenho (monta sempre, 4.763, pendentes entram em `aceitas`):
   4.763 x (1.134 + 4.763/2) ~= 16,7M pares, mais `distanciaDeMolde`
   (`main.go:2320-2335`, O(n²) sobre aceitas) 4.763²/2 ~= 11,3M. O `break` de
   `:272` que o desenho chama de defeito e o unico motivo de a passada terminar.

4. **Se pendente NAO entra em `aceitas`, cluster de doorway publica.** A e B com
   Jaccard 0,98 (mesma prosa, so o numero do processo difere — e digito e
   neutralizado): hoje B morre; no desenho ambas publicam como medio. O desenho
   nao tem BANDA de score, entao nao separa falso positivo (0,70-0,78, o caso do
   CLAUDE.md §8) de duplicata verdadeira (0,95+). Publica os dois.

5. **Introduz vermelho novo em gate hoje verde.** `internal/checks/checks.go:12613`
   poe `near_duplicate_content` em `duplicateCodes` de `checkNoDuplicateContent`,
   onde e ERRO. Hoje: `publica.log` "11118 paginas, nenhum achado" = zero near-dup
   no acervo. Publicar molde vira o gate `no-duplicate-content` vermelho.

6. **Claim de SEO desmentida pelo acervo.** O desenho diz "o publicador vivo
   publica titulo curto como MEDIO hoje" e por isso remove `:1685`/`:1688`.
   Medido: 0 de 11.125 paginas publicadas tem title nao vazio fora de 20-65, e 0
   tem meta fora de 70-160. Os 19 "curtos" tem comprimento ZERO = `missing_title`,
   que E critico (`qualitygate.go:29`). O caminho nunca foi exercido.

7. **Gate de pareamento nao considerado.** `tools/check-v2-portfolio-pairing`
   espelha `check-v2-finalized-commit`: `(not skipped and count != 1) or
   (skipped and count > 1)`, com autoridade no portfolio do commit PAI. Pendente
   ativa sem linha de portfolio no pai reprova o commit.

8. **Circularidade do dreno.** O desenho diz que o executor do refino e "o PROPRIO
   gerador re-rodado com a regua calibrada". Calibrar a regua e exatamente o que
   ele declara fora de escopo. O juizo nunca desaparece.

9. **Proporcionalidade.** Subsistema novo (ledger, `juizos[]`, `estado`, fiacao de
   tetodelote, edicao do censo em Python, campo novo em `Severity`,
   `SelectPublishable`, troca do produtor da serie) para contornar 3 constantes.

## Emenda minima que salvaria alguma coisa

Alinhar o produtor ao gate vivo: `shingleMold 3 -> 5`, remover
`reDigito.ReplaceAllString` de `shinglesNeutralizados`, `limiarMolde 0.70 -> 0.82`
(ou usar `internal/quality`/`v2bodyneardup` direto, com `legalsignature.Tokenize`),
e neutralizar o bloco de ementa citada e o FAQ antes de hashear (precedente:
`tools/generate-page-content-revision`). Indexar por bucket de shingle/MinHash
antes de qualquer passada acima de algumas centenas. Teste de falso positivo sobre
amostra real, exigido pelo §5.
