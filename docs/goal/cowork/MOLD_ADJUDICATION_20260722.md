# MOLD_ADJUDICATION_20260722 — Adjudicação adversarial de molde (Cowork Fable 5)

Autor: `claude-cowork-fable`. Método: leitura lado a lado de 12 páginas (4 por shard) dos shards piores
+ cruzamento fila×measurement. Fontes: `data/ops/v2_mold_rewrite_queue_20260721.jsonl` (301 entradas),
`data/ops/v2_structural_mold_measurement_20260721.json`, `data/ops/v2_mold_rewrite_specs_20260721.jsonl`.

## Veredito: MOLDE REAL (não é falso-positivo) — mas a causa é outra

Nos 3 shards-alvo (`empresarial-p1` 75%, `procedimentos-15` 71%, `procedimentos-09` 71%), **headings são
únicos por página** (zero clone literal). O molde real tem 3 camadas que o classificador de sequência não nomeia:

1. **Mismatch arquétipo×prosa**: TODAS as páginas lidas têm `arquetipo_alvo` (checklist-documental,
   linha-do-tempo, tabela-criterios, passo-a-passo) que a prosa NÃO materializa — tudo é 4-5 parágrafos
   corridos. O rótulo promete estrutura que o corpo não entrega; a sequência vira `[outro,outro,outro,...]`
   dominante.
2. **Fórmula de fechamento (empresarial-*, lane comercial)**: as 4 amostras fecham com o MESMO esqueleto:
   `[remoto/digital] + [canal] + "sem prometer resultado" + "depende de X e da prova de Y"`. Vocabulário
   varia, esqueleto não. Exemplos exatos no transcript da adjudicação.
3. **Fórmula de abertura (procedimentos-*)**: 2º parágrafo em "mito→correção" ("Não existe uma regra geral
   segundo a qual…", "já não descreve o regime atual") em 3 de 4; slot anti-fraude iniciando por
   "Desconfie de" em quase todas (conteúdo BOM — manter; variar a entrada).

## Spec executável (complemento ao spec mecânico existente)

`v2_mold_rewrite_specs_20260721.jsonl` já cobre 301/301 com retitulação/reordenação — **mas
`writing-mass.js` não lê esses campos** (grep confirma zero referência). Diretiva para o lote de reescrita:

- Aplicar sempre `headings_novos` + `mapeamento` do spec existente (não reabrir).
- Micro-edição de corpo por arquétipo: passo-a-passo → 1ª frase de seção no imperativo; checklist →
  ≥1 lista itemizada real (3-6 itens); linha-do-tempo → marcador temporal explícito abrindo cada seção;
  tabela-criterios → lista "Critério — o que verifica" inline. objecao/resposta/glossario → retitulação basta.
- Banir molde de 2ª ordem: empresarial → variar ≥2 de 4 eixos do fechamento (abertura do parágrafo, canal,
  verbo de garantia, cláusula de dependência) entre páginas do mesmo lote; procedimentos → alternar a
  entrada do 2º parágrafo (pergunta retórica / dado / contraste / cronologia) e proibir "Desconfie de"
  como 1ª expressão em >1 página por lote de 4.
- Gate de saída do lote: re-rodar o classificador do measurement; `dominant_seq_pct < 50%`; similaridade
  das fórmulas de fechamento/abertura ≤0.60 entre páginas do lote.

## Bug de cobertura da fila (para o terminal corrigir)

`cidadania-04` (90,91%, n=22), `bancario-r02` (100%, n=3), `seguros-r02` (80%), `leis-20` (77,8%) têm
`dominant_seq_pct` MAIOR que empresarial-p1 no measurement e **não estão na fila de reescrita** —
gap na geração de `v2_mold_rewrite_queue`. Regenerar a fila com corte por percentil, não lista fixa.
