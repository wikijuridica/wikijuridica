---
name: identificador-anunciado-vem-do-produtor
description: Hash/versão anunciada em canal de máquina tem de ser lida do produtor do artefato; cópia em registro derivado envelhece e mente em 100%
metadata:
  type: project
---

Identificador de versão anunciado a máquina (`version:` da gêmea, `html_sha256`,
`content_sha256`) só é verdadeiro se for LIDO do produtor do artefato no momento
de servir. Cópia guardada em registro derivado precisa ser regenerada em
lockstep com a publicação — e não é.

**Why:** medido em 2026-09-16. O `version:` da gêmea Markdown vinha de
`data/editorial/anchor_claim_publication.jsonl` (gerador datado, congelado em
2026-08-26) enquanto o acervo é republicado todo dia: 10.070 de 10.070 rotas
divergiam do `html_sha256` do `published_manifest`, 100,0%. Pela ponta do
consumidor (curl na borda, 13 rotas por stride): 0/13 batiam com o HTML servido,
e o manifesto batia 13/13 com a borda e 40/40 com `public/`. O `content/pages.json`
não carregava o campo em nenhuma das 11.161 páginas — o registro congelado era a
única fonte.

**How to apply:** antes de anunciar qualquer identificador, faça o censo de
QUANTOS canais anunciam "o hash desta página" e de QUAL artefato cada um sai.
Neste repo eram quatro canais e três definições: gêmea/CSL (manifesto, depois da
correção), `/api/v1/citar` (manifesto), `/changes.json` + `/api/v1/novidades` +
`/api/v1/lote` (`data/ops/page_content_revision.jsonl`, fingerprint SEMÂNTICO
que ignora datas de propósito — não é defeito, mas tem nome colidente). Cheque a
direção do import antes de escolher a camada: `publishedmanifest` importa
`content`, então `content` não pode ler o manifesto — o carimbo mora no boot do
servidor, que é o único processo que emite `.md`. Quando não houver hash com
lastro, OMITA: rota fora do manifesto não anuncia versão. Ver
[[mutante-de-fiacao-precisa-compilar]] para a prova de que o carimbo está
ligado.
