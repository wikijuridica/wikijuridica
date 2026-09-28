# ADR (proposta): aceite autenticado de correção de segmentação no corpus-oráculo

Date: 2026-09-10
Status: **PROPOSTA — não implementada.** Nenhum código deste documento está no
repositório. Ela muda a invariante de autenticação da série jurídica e por isso
é decisão de arquitetura do corpus-oráculo, não do coletor.

## O problema, medido

O gate `source-snapshot-corpus` acusa **10** ocorrências de
`source_snapshot_veto_marker_contaminated` (medido em 2026-09-10, manifest de
13.551 linhas). O corpo gravado do dispositivo carrega, colado ao marcador
oficial, o cabeçalho da divisão seguinte ou o fecho da publicação — o caso
canônico é o art. 108 do CDC:

```
Art. 108. (VETADO). TÍTULO VI DISPOSIÇÕES FINAIS
```

O `TÍTULO VI ...` não é do artigo 108. Ele entrou porque o nosso segmentador
fechava o dispositivo apenas no próximo `Art. N`. **A causa já foi corrigida
hoje**, noutra frente: `internal/planaltochannel.FimDoDispositivo` passou a
truncar o corpo no primeiro cabeçalho de divisão autenticado e no fecho da
publicação. O que falta não é parser: é o **aceite** da correção no store.

## Por que a correção não entra hoje

`cmd/collect-oracle/run.go`, função `planVersioned`, já **detecta** o caso
(`ehCorrecaoDeSegmentacao`) e o nomeia
(`statusCorrecaoDeSegmentacao = "skipped_correcao_de_segmentacao_aguarda_aceite_no_store"`),
mas não grava. As duas portas do modelo estão fechadas, e cada uma por um bom
motivo:

- **mesma `version_seq`** — `corpus.validateCorrection` recusa de saída:
  `"version_seq %d reutilizado com conteudo diferente"`. A `version_seq` é
  autenticada pelo `content_sha256`, e é essa invariante que impede reescrita
  silenciosa de texto de lei.
- **nova `version_seq`** — `corpus.validateAppendAgainst` exige predecessora
  fechada: `"version_seq %d sucede predecessora ainda aberta"`. Fechar a
  anterior gravaria uma `vigencia_fim` afirmando que a redação mudou naquela
  data. Nenhuma fonte diz isso — a lei não mudou, o nosso parser mudou.

Ou seja: a única saída honesta exige **admitir `content_sha` novo sob a mesma
`version_seq`**, e isso é exatamente a invariante que protege o acervo.

## A proposta

Um ramo estreito em `validateCorrection`, no molde exato de
`validateVetoCorrection` — a exceção que já existe para a única transição de
estado sem data:

```go
// em internal/corpus/corpus.go, dentro de validateCorrection, ANTES da
// recusa por "conteudo diferente":
if previousText, candidateText, ok := s.textosDaCorrecao(previous, candidate); ok &&
    ehTruncamentoDeSegmentacao(previousText, candidateText) {
    return validateSegmentationCorrection(previous, candidate, previousText, candidateText)
}

func validateSegmentationCorrection(previous, candidate OracleRecord, anterior, novo string) error
```

### O que ela passa a permitir

Uma correção de **mesma `version_seq`** com `content_sha256` **novo**, e só
quando as quatro cláusulas abaixo — as mesmas de
`cmd/collect-oracle.ehCorrecaoDeSegmentacao`, promovidas de heurística de
coletor a **regra do store** — se verificam sobre os textos:

1. **prefixo estrito**: `strings.HasPrefix(anterior, novo)` e
   `len(novo) < len(anterior)`. Redação nova de lei nunca é prefixo da
   anterior; truncamento é.
2. **o corte é O NOSSO, byte a byte**:
   `planaltochannel.FimDoDispositivo(anterior) == novo`. Não basta "algum
   truncamento" — sem esta cláusula, texto cortado por fetch parcial ou HTML
   mutilado entraria como correção autenticada.
3. **marcador de VETO idêntico** nos dois textos.
4. **marcador de REVOGAÇÃO idêntico** nos dois textos.

E, herdadas da regra geral de `validateCorrection`, sem exceção:

5. todo campo jurídico e de proveniência imutável permanece igual
   (`urn_lex`, `dispositivo`, `source_channel`, `source_url`, `version_seq`,
   `version_axis`, `supersedes_ref`, `vigencia_inicio`, `vigencia_fim`,
   `vigencia_status`, `revogado_por`);
6. a observação só pode **avançar** (`last_verified_at`, `as_of_date`,
   `fetched_at` nunca retrocedem);
7. o blob novo é escrito por CAS como qualquer outro — o anterior **não é
   apagado**, e o manifest continua append-only, de modo que o texto
   contaminado permanece auditável.

### O que ela continua barrando

- Qualquer reescrita que **não** seja prefixo do texto anterior — inclusive as
  duas que hoje geram vontade de alargar a regra: correção de ordinal
  (`"Art. 1 o Toda pessoa"` → `"Toda pessoa"`) e conserto de mojibake cp1252.
  Nenhuma das duas produz prefixo, e alargar a cláusula 1 para alcançá-las
  aceitaria qualquer reescrita.
- Truncamento por qualquer outro corte que não `FimDoDispositivo` (cláusula 2).
- Correção que mude o estado jurídico junto com o texto (cláusulas 3, 4 e 5):
  se o marcador mudou, o que mudou não foi só a segmentação, e a decisão volta
  a ser jurídica.
- Correção que retroceda a observação (cláusula 6).
- Reabertura ou movimentação de fechamento — a série tem de estar **aberta**,
  como em `validateVetoCorrection`.

### O custo arquitetural, dito com todas as letras

Hoje `validateAppendAgainst` e `validateCorrection` decidem olhando **apenas
registros**. A cláusula 2 exige que a validação alcance o **texto**, o que
significa dar ao validador acesso ao blob anterior (leitura por CAS dentro do
`Put`/`PutBatch`). Isso:

- acopla `internal/corpus` a `internal/planaltochannel` (hoje independentes) —
  a alternativa é injetar a função de corte como dependência do `Store`, o que
  mantém o corpus agnóstico e é a forma preferida;
- torna a validação de escrita **dependente de I/O**, com o custo por linha de
  uma leitura de blob;
- e, o ponto que importa: passa a existir **um** caminho pelo qual o
  `content_sha256` de uma `version_seq` já gravada muda. Enquanto ele for
  estreito e autenticado, o acervo continua provando o que serve; se alguém o
  alargar depois, o que se perde é a garantia central do corpus.

### Casos de teste exigidos antes de qualquer implementação

Em `internal/corpus`, sobre textos verbatim do acervo:

1. `"Art. 108. (VETADO). TÍTULO VI DISPOSIÇÕES FINAIS"` → `"Art. 108. (VETADO)."`
   — **aceita**, `version_seq` preservada, blob novo por CAS, blob antigo intacto.
2. mesmo par, com `vigencia_status` mudando junto — **recusa** (cláusula 5).
3. mesmo par, com `source_url` diferente — **recusa** (cláusula 5).
4. texto novo que **não** é prefixo do anterior — **recusa** (cláusula 1).
5. texto novo que é prefixo mas **não** é `FimDoDispositivo(anterior)`
   (truncamento arbitrário, simulando fetch parcial) — **recusa** (cláusula 2).
6. par em que o marcador de revogação some do texto novo — **recusa** (cláusula 4).
7. par em que o marcador de veto vira marcador de revogação — **recusa** (cláusula 3).
8. correção sobre série já **fechada** — **recusa**.
9. correção que retrocede `last_verified_at` — **recusa** (cláusula 6).
10. round-trip: reabrir o manifest depois da correção reconstrói a série sem
    erro, e o auditor independente (`internal/sourcesnapshotaudit`) deixa de
    acusar `source_snapshot_veto_marker_contaminated` para as 10 séries, sem
    abrir categoria nova.

E, no lado do produtor, `cmd/collect-oracle`: o ramo
`statusCorrecaoDeSegmentacao` passa a **gravar** e o contador
`CorrecaoDeSegmentacao` a refletir escrita, não recusa — com o teste de
`putVersionedParts` correspondente.

## Alternativas descartadas

- **Fechar a predecessora com a data da observação e abrir `version_seq` nova.**
  Grava `vigencia_fim` afirmando alteração legislativa numa data que fonte
  nenhuma dá. É a falsidade que a política de revogação datada de 2026-09-04
  existe para impedir.
- **Reescrever a linha no manifest.** O manifest é append-only e é isso que o
  torna auditável. Descartado sem discussão.
- **Deixar como está.** É o estado atual e é defensável enquanto as 10 séries
  estiverem em quarentena (não chegam a consumidor nenhum). Deixa de ser
  defensável quando a mesma classe aparecer fora de quarentena, ou quando a
  correção do segmentador for aplicada em massa ao `data/legal-corpus/`
  (1.520 artigos medidos em 2026-09-10 na frente paralela).
