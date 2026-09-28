---
name: ordem-derivados-editoriais
description: Use antes de regenerar qualquer artefato derivado de data/editorial — a ordem é obrigatória e o erro diz "fingerprint mismatch".
---

# Ordem de regeneração dos derivados de `data/editorial/`

A cadeia tem **13 passos** e cada artefato precisa ser **mais novo que sua
fonte**. Fora de ordem o erro diz `fingerprint mismatch`, nunca "ordem errada" —
e a fábrica ficou **31 dias parada** por isso.

## A ordem

```
1  generate-authorial-mass-drafts
2  generate-authorial-mass-content-expansion
3  generate-authorial-mass-legal-signatures
4  generate-authorial-mass-contextual-compatibility
5  generate-authorial-mass-paid-intent-refinements
6  generate-authorial-mass-similarity-report
7  generate-authorial-mass-signature-candidate-pairs
8  generate-authorial-mass-similarity-semantic-reviews
9  generate-authorial-mass-refinement-quality-report
10 generate-authorial-mass-global-similarity-audit
11 generate-authorial-mass-editorial-quality-vectors
12 generate-authorial-mass-signature-refinement-queue
13 generate-authorial-mass-publication-readiness
```

Regenerar o passo N obriga a regenerar **todos** de N+1 a 13.

## Antes de regravar

Preserve o artefato anterior em `.agents/runtime/<data>/`. Texto redigido foi
pago pelo dono e nunca se descarta.

## A ordem não é suposta — ela é derivável e cobrada

Os detectores vivos saem de `grep -rn "older_than" internal/ --include=*.go`.
Hoje são **cinco**, e três deles (D3, D4) não são case de `cmd/check`: rodam
DENTRO de `authorialmassqualityvectors.Generate`, ou seja, disparam ao regenerar
quality-vectors.

- Documento completo (grafo, ambiguidades declaradas, os seis artefatos sem
  detector próprio): `docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md`
- Gate que prova que o documento não ficou pra trás do código:
  `./tools/check-cadeia-editorial-ordem-declarada`

**Esta cadeia não é a de `data/editorial/v2_pages/*.jsonl`** — essa tem pipeline
próprio (skill `commit-v2`).

## Quando aparecer `fingerprint mismatch`

Não é "artefato corrompido": é ordem. Ache o artefato citado na mensagem,
identifique sua fonte no grafo do documento, e regenere da fonte para frente.
Aumentar timeout ou relaxar o gate não resolve — é o mesmo defeito, adiado.
