# Nada morre no produtor — terminalidade só por FATO

Ângulo: publicar e corrigir. O problema não é o limiar, é a TERMINALIDADE.

## Tese

O gerador destrói, com `continue` e `return Pagina{}, motivo`, a única coisa que
poderia depois refutar o veredito: a página. O §5 do contrato exige "gate
estatístico refutado por medição é pulado, com a evidência gravada" — e não
existe evidência de uma página que nunca foi escrita. **Persistir a recusada é o
PRÉ-REQUISITO do §5, não um desvio dele.** O veredito não muda, o limiar não
muda; muda a consequência: de destruir para anotar, gravar e represar.

## Verificado por leitura (arquivo:linha)

| ponto | o que é |
|---|---|
| `cmd/generate-acordao-pages/main.go:271-273` | `break` silencioso por `-limite`; 3.503 candidatos nunca avaliados |
| `cmd/generate-acordao-pages/main.go:294-297` | molde: `continue` + contador. A página JÁ está completa aqui (montaPagina retornou) |
| `cmd/generate-acordao-pages/main.go:1554,1560` | `return Pagina{}, motivo` ANTES de existir página |
| `cmd/generate-acordao-pages/main.go:1653..1692` | `return Pagina{}, motivo` com a página montada — descarta objeto pronto |
| `cmd/generate-acordao-pages/main.go:2268-2312` | `relata` imprime `map[string]int` em stdout. Zero disco |
| `cmd/generate-acordao-pages/main.go:78` | `lane = "informativa"` — o canal JÁ é lane informativa |
| `cmd/generate-acordao-pages/main.go:547` | `ordenaPorEvidencia` — ordenação por âncora já existe |
| `cmd/generate-acordao-pages/main.go:732-764` | `intentsPublicados` é por SHARD, com auto-exclusão em :741-743 |
| `cmd/generate-acordao-pages/main.go:260` | `shinglesDoProprioShard` — o próprio shard vira população de molde |
| `internal/v2ingest/v2ingest.go:130-135` | `Skipped`/`SkipReason`: precedente de "registro gravado que não é página" |
| `internal/v2publish/v2publish.go:163-175` | `Severity` já tem `Publish`, `MediumReasons`, `Lane` |
| `internal/v2publish/v2publish.go:289,356-357` | `ToContentPage` fixa `Status:"published"`, `IndexPolicy:"index"` |
| `internal/v2publish/v2publish.go:391-446` | `SelectPublishable`: 4 recusas, nenhuma estatística |
| `internal/tetodelote/tetodelote.go:33-72` | `Admite(jaNoAr)`/`Conta`/`Acrescentadas` — teto do ACRÉSCIMO |
| `internal/editorial/editorial.go:48-56` | `ValidIndexPolicies`, `IsIndexable` |
| `internal/httpserver/markdown.go:72` | **gêmea .md exclui rota não indexável, de propósito** |
| `cmd/publish-v2-direct/main.go:2398` | llms.txt exclui não indexável |
| `internal/publishedmanifest/publishedmanifest.go:370-378` | rota pública não indexável SEM manifesto é coerente |
| `cmd/publish-v2-direct/qualitygate.go:21-31,81-83,101` | 9 críticos, nenhum estatístico; `Passed()`→"nenhum achado" |
| `tools/run-daily-content:735-736` | fila só é escrita se `grep -q 'achado MÉDIO'` no log |
| `tools/generate-propostas-reescrita:112-127,357,377-384` | JÁ lê `severity=='medio'` e `medium_reasons` |
| `tools/generate-v2-publication-severity:147,558,640,688` | `record.get(...)` — campo novo sobrevive |

## Medições próprias desta sessão

**Fila de refinamento** `data/ops/refinement_queue.jsonl`: 5 linhas, última
2026-09-04. Totais 82+205+205+261+4 = **757 ocorrências acumuladas**. Não tem
`intent_id` — é log de TENDÊNCIA, nada se drena dela. O número "1.267 médios
vivos" do enunciado **não reproduz** deste artefato; o que reproduz é 757
acumuladas e 4 no último dia. Os 10.337 médios por intent_id vivem no censo, que
é outro artefato.

**Por que congelou, e a causa é boa**: 742 das 757 (98%) eram
`source_url_not_official_nor_registered`, classe corrigida NA FONTE pelos commits
de 2026-08-29 (`c2fe3257`, `2f5eb413`, `e2c76ef8`), exatamente na janela 08-28 →
09-04 em que ela some da série. O último toque em quality.go (`87f4e4bf`,
2026-09-05) só acrescentou `www.oab.org.br` com efeito medido zero declarado.
Detector corrigido, não cegado — verifiquei em vez de supor.

**Absorção do Googlebot** `data/ops/crawl_coverage_daily.jsonl`, janela
2026-08-16..2026-09-15 (30 dias), máximo por dia:
`cumulative_sitemap_coverage` 7.152 → 7.263 = **+111 URLs, média 3,70/dia**,
enquanto `sitemap_total` foi 9.926 → 11.142 (+1.216, ~40,5/dia). Razão ~11:1.
Rotas nunca pedidas: 2.774 → 3.879 (bate com a linha do `publica.log` de hoje).
`coverage_is_floor: true` — é PISO. Há descontinuidade de série em 2026-09-02
(7.294 → 7.192); segmentos limpos dão 8,88/dia (08-16..09-01) e 5,46/dia
(09-02..09-15). O intervalo honesto é 3,70–8,88 URLs novas/dia, todos piso.

## DOIS EIXOS ORTOGONAIS — e confundi-los é o erro que eu quase cometi

Qualidade e vazão não são o mesmo eixo. Represar por JUIZO é quarentena
disfarçada e deixa a queixa do dono de pé ("podem ir para o ar, e os gates
anulam"). A separação:

**Eixo 1 — QUALIDADE. JUIZO nunca vira estado.** Ele vira `juizos[]` no
registro; o censo o lê e classifica **MÉDIO**; `publish=true`. É literalmente o
que o §5 manda e o que o acervo vivo já faz com 10.337 médios. Só FATO-impeditivo
é terminal, e mesmo assim com linha de ledger.

**Eixo 2 — VAZÃO. `tetodelote.Teto` marca `estado: pronta|pendente`.** Estado de
vazão, não de mérito. O censo deixa `pendente` passar como `publish=false`
exatamente como já faz com `skipped`
(`tools/generate-v2-publication-severity:640,688`); `SelectPublishable`
(`internal/v2publish/v2publish.go:400`) a pula com `pendente:<n>`. Na onda
seguinte o gerador admite as próximas N. Nada fica preso por mérito.

**A reconciliação, sem criar estado**: `ordenaPorEvidencia`
(`cmd/generate-acordao-pages/main.go:547`) passa a somar a contagem de juízos
como peso NEGATIVO. Página limpa ocupa slot primeiro; a marcada publica depois,
como médio. Isso é ordenação dentro do orçamento — não quarentena.

### FATO-impeditivo (terminal, ledger, nenhuma página)
`elegivel:526 barrado_por_<sigilo>` (§2, exceção taxativa, nunca afrouxa),
`:530 campo_obrigatorio_ausente_no_registro`, `:519 tipo_de_decisao_nao_e_acordao`,
`:516 agravo_ou_embargo` (49.807 — ESCOPO editorial: 49.807 páginas de agravo é o
doorway que o §8 proíbe).

`montaPagina:1554 ementa_sem_item_transcritivel` é **FATO com detector
heurístico**: o fato é "não existe item em prosa"; quem o aproxima é
`integralmenteEmCaixaAlta` (`:1145`, 80% de versal, para no primeiro item). 682
de 4.763 (14,3%) reprovam. O ledger grava a RAZÃO DE VERSAL medida para que a
calibração do detector seja possível depois — sem isso o rótulo "FATO" congela
uma heurística.

### JUIZO (nunca terminal, vira médio e publica)
`:294 molde_acima_do_limiar` (532), `:1653`+`:1660` orçamento de camada (21+123),
`:1668/:1672 texto_oficial_nao_cabe_na_banda`, `:1682 comentario_proprio_abaixo_do_piso`,
`:1679 corpo_abaixo_da_banda`, `:1560 sem_duas_fontes` (contagem é FATO,
terminalidade é JUIZO — 2.423 páginas VIVAS têm menos de 2 fontes),
`elegivel:533 ementa_curta` (4.500, das quais 2.477 têm âncora substantiva),
`:540 sem_ancora_legal_substantiva` (1.151).

**E o SEO também, medido**: `:1685` title fora de 20-65 e `:1688` meta fora de
70-160 matam a página no gerador, mas `internal/seo/seo.go:514-533` emite
`title_too_short/too_long` e `meta_description_too_short/too_long` via
`quality.go:207`, e **nenhum dos quatro está em `criticalQualityCodes`**
(`cmd/publish-v2-direct/qualitygate.go:21-31`, que só tem `missing_*` —
AUSÊNCIA, não comprimento). O publicador vivo publica título curto como MÉDIO
hoje. Matar no gerador é, de novo, o produtor mais severo que o gate que decide.
Idem `:1692 fragmento_terminal` (`visible_text_terminal_fragment`, 31 na fila de
reescrita, fora da lista crítica). Os dois: reparo determinístico na geração, ou
publica como médio com o reparo nomeado — nunca recusa.

## O registro de juízo — o que a refutação exige

Sem estes campos, mover o silêncio do stdout para o JSONL não resolve nada:
`motivo`, `regua` (nome + versão), `score`, `limiar`, `par_mais_proximo`
(intent_id), `populacao_comparada` (N), `ordem_na_passada`, `medido_em`.
`ordem_na_passada` é obrigatório porque `aceitas` cresce dentro da passada
(main.go:300): a n-ésima página é comparada contra n-1 assinaturas, e o veredito
de molde é dependente de ordem por construção.

## Anti-lixo: orçamento medido, NÃO noindex

Reuso `internal/tetodelote.Teto` — já governa só o ACRÉSCIMO, já isenta o que
está no ar, já tem teste. N sai da absorção medida acima (3,70–8,88/dia, piso),
não de número redondo. Ordem de publicação por `ordenaPorEvidencia` (:547).

**Rejeito noindex temporário, por medição**: `internal/httpserver/markdown.go:72`
exclui rota não indexável da gêmea Markdown DE PROPÓSITO, e
`cmd/publish-v2-direct/main.go:2398` a exclui do llms.txt. Num portal AI-first
(§12) cujo produto é o canal de máquina, noindex é invisível para o Google E
para MCP/gêmea/llms.txt — cemitério com mais passos. Pior: virar noindex→index
depois muda a meta robots = mudança de markup = linha `--ressemear` da matriz do
§6 sobre a coorte inteira, mais purga ampla.

**Rejeito lane informativa como quarentena**: `main.go:78` já põe o canal inteiro
em `lane="informativa"`; ela governa CTA (`content.go:473`), não indexação. Usá-la
como depósito corromperia um sinal de ética do §8 (BPC/LOAS).

O que sobra é o certo: a página pendente fica NO SHARD e FORA de `public/`.
O recurso escasso é o slot de índice, e ele se aloca por ordem, não por rótulo.

## Por que isto não é afrouxar o gate

O veredito é idêntico, o limiar é idêntico, e a página pendente **não publica** —
o efeito protetor sobre o acervo é o mesmo. Afrouxar seria mover 0,70 para 0,80
ou apagar o detector; não proponho nem um nem outro. Precedentes vivos:
`cmd/publish-v2-direct/main.go:3957 skipped_statistical_gates` grava o salto nas
11.106; o censo rebaixa `reprovada_por_agente_sem_justificativa` (131) em vez de
destruir. E o ledger de FATO é o mesmo princípio aplicado ao que CONTINUA
terminal: não publica nada, só nomeia.

## Executor do refino

Existe: `tools/generate-propostas-reescrita` já lê o censo e `medium_reasons`
(:112-127, :357, :377-384) e já recusa evidência sem número medido
(`exige_numero_medido()`). Mas a última passada emitiu 100/100 de uma classe só
(`precedente_disponivel_nao_citado`), prioridade 0,51 em todas — as regras de
médio não produziram candidato e o limite foi consumido pela regra de precedente.
É lacuna de RANKING, não ferramenta faltando.

Para o juízo de régua (molde), o executor é o PRÓPRIO gerador re-rodado com a
régua calibrada: determinístico, custo zero de LLM, e o juízo desaparece na
re-medição. É a maior parte dos 532.

Produtor da série: trocar o `grep` de `tools/run-daily-content:736` por um diff
do censo (ontem × hoje por intent_id) — dá tendência E nomes.

## Provas — comando e número esperado

1. **Conservação, o teste que mata o silêncio.**
   `./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 500` e
   depois `wc -l` no ledger novo. Exigir
   `montadas + juizos_anotados + terminais_no_ledger == iterados` — hoje
   500 + 760 = 1.260 — e `iterados + nunca_avaliados == candidatos` — hoje
   1.260 + 3.503 = 4.763. Qualquer sobra é recusa sem nome, que é o defeito.
2. **Zero linha anônima.** `python3 -c` contando linhas do ledger sem
   `intent_id` (ou sem `numero_processo` para as recusas de elegibilidade, que
   ainda não têm intent). Esperado **0**. Hoje o número é 760 de 760.
3. **Orçamento.** `./tools/go-modern test -count=1 ./internal/tetodelote/` — a
   bancada já prova que `jaNoAr` não consome cota
   (`internal/tetodelote/tetodelote_test.go`). Acrescentar asserção
   `Acrescentadas() <= N` no gerador.
4. **Censo atravessa o juízo.** Contar em `data/editorial/v2_publication_severity.jsonl`
   as linhas de `stj-acordao-derivado`: `publish=true` tem de ser igual ao número
   de `pronta` no shard, e `medium_reasons` tem de conter o motivo de juízo.
   Esperado: nenhuma linha crítica de similaridade (é o que o acervo já faz —
   0 críticos estatísticos em 11.206).
5. **Falso positivo sobre amostra real**, exigido pelo §5 para detector novo ou
   alterado: amostra por stride determinístico sobre as marcadas, com o veredito
   conferido à mão. Precedente: as 46 e as 29 eram 100% falso positivo.
6. **Absorção não degrada.** O python desta sessão sobre
   `data/ops/crawl_coverage_daily.jsonl`, máximo por dia, após M ondas:
   inclinação ≥ 3,70 URL nova/dia (piso medido em 30 dias). Se cair, o
   orçamento está grande demais e a prova é essa, não opinião.
7. **Mutação no ledger**: trocar o veredito de uma página e exigir que a linha
   do ledger mude. Ledger que não muda com o veredito não está medindo o
   veredito.

## Riscos que eu mesmo crio

1. **`shinglesDoProprioShard` (:260) passa a ler as pendentes.** Com o
   desacoplamento isto se atenua: `pendente` é estado de VAZÃO e a página vai ao
   ar na onda seguinte, então ela pertence mesmo à população. A régua ficar mais
   severa conforme o acervo cresce é comportamento correto de população — o
   errado é a régua (3-gramas com dígito neutralizado), que é o outro ângulo.
   O que continua sendo defeito meu: se `pendente` virar estado longo, a
   população cresce antes da publicação e o veredito se antecipa ao fato.
2. **Pool pendente cresce se drenagem < entrada.** Cérebro a 1,85–2,9 tok/s.
   Precisa de gate por FLUXO e por entrada nova, nunca por nível.
3. **`ordenaPorEvidencia` pesa âncora, não prosa.** Página ruim com muitas
   citações sobe primeiro. O orçamento limita TAXA, não qualidade. Somar juízo
   como peso negativo atenua, não resolve: juízo mede molde, não utilidade.
7. **N está subdimensionado por construção.** Derivei o orçamento só do
   Googlebot, e o §12 diz que a métrica é "retorno e citação por agente". O
   canal de máquina (MCP, gêmea, `/api/v1`) não tem o gargalo do Googlebot.
   `data/ops/ai_citation_signal_daily.jsonl` e `data/ops/bot_return_daily.jsonl`
   são as séries que reveriam N para CIMA. Não as calculei nesta sessão — nomeio
   como a medição que falta, não como número.
4. **`intentsPublicados` é por shard**: o padrão só é seguro com a auto-exclusão
   de :741-743; outro gerador que o copie sem ela nunca revisita as pendentes.
5. ~~Campo novo recusado por decoder estrito~~ — **VERIFICADO E DESCARTADO**:
   `internal/v2publish/v2publish.go:220` usa `json.Unmarshal` puro, e
   `internal/v2ingest/v2ingest.go:755` usa `decodeJSONWithoutDuplicateKeys` →
   `strictjson.DecodeUnique` (`internal/v2ingest/json_strict.go:26-27`), que
   proíbe chave DUPLICADA, não chave desconhecida. Os
   `DisallowUnknownFields` do v2ingest estão em transaction/vault/plan, não no
   registro de página. `juizos` atravessa os dois decoders.
6. Dependência de ordem continua existindo; gravá-la a torna visível, não ausente.
