# Plano de re-coleta do corpus de grounding — turnkey — 2026-07-22 (onda 8)

Autor: `claude-cowork-fable` (Cowork Fable 5, onda 8). Torna o `corpus-stub-sanitize` acionável.
Complementa `CORPUS_STUB_CENSUS_20260722.md`. Metadata-only (tamanhos/paths/URLs — nenhum texto de
lei copiado). Read-only; a execução é do terminal.

## Achado central: a maior parte NÃO precisa de re-fetch

Das 3 frentes, **2 se resolvem sem baixar nada** — só re-apontar o resolvedor e re-fatiar offline.
Só CF, CP e ~33 leis precisam de coleta real no planalto.

## BUG NOVO (join) — pré-requisito de qualquer sanitize

O join âncora→manifesto falha por mismatch de underscore: a âncora da prosa grava `art482` e o
manifesto grava `art_482`. Join ingênuo **não casa** e subconta stubs. **Normalizar `art(\d+)` →
`art_\1` (ou vice-versa) nos dois lados antes de medir/sanear** — senão o gate de stub some
dispositivos.

## PARTE A — de-dup "prefer-larger" (full blob JÁ presente, zero fetch) — 10

Cada URN de lei inteira tem 3 linhas no manifesto: 2 stubs idênticos (~25–241 B,
`senado_legis_dados_abertos_json`) + 1 blob full. Fix = resolvedor aponta para a linha maior.

| Lei | URN | stub | blob full (sha12) + bytes |
|---|---|---|---|
| Código Civil | lei;10406 | 25 B | `blobs/4c/4c50ff85082b…` 643.780 |
| CPC | lei;13105 | 26 B | `blobs/b4/b4822b5e249a…` 600.107 |
| Lei 8.213/91 | lei;8213 | 89 B | `blobs/31/31db8aefc93b…` 188.316 |
| CDC (8.078) | lei;8078 | 68 B | `blobs/89/89aa6b6376d8…` 84.792 |
| Lei 15.040/24 (seguros) | lei;15040 | 174 B | `blobs/02/026438e537f3…` 62.185 |
| Lei 8.245 (inquilinato) | lei;8245 | 87 B | `blobs/64/6469c75925db…` 58.162 |
| Lei 9.099/95 | lei;9099 | 83 B | `blobs/22/22a9d20cfc46…` 41.750 |
| Lei 6.194/74 (DPVAT) | lei;6194 | 155 B | `blobs/19/1921b37ef05e…` 14.771 |
| Lei 4.594/64 | lei;4594 | 43 B | `blobs/42/42d913b96eed…` 8.948 |
| Lei 14.544/23 | lei;14544 | 241 B | `blobs/ad/adc2a454dd36…` 4.158 |

## PARTE C — artigos que ancoram as 25 prosas quarentenadas (stub-only) — 21

**Todos** pertencem a CC/CDC/CLT/8.245 — que já têm o blob full inteiro (Parte A). **Re-fatiar o
artigo offline do blob existente**; planalto só como fallback (anexar `#art<NNN>`).

| Lei (blob p/ re-fatiar) → planalto | artigos (bytes) |
|---|---|
| **CC** `4c50ff85082b` → /ccivil_03/leis/2002/l10406compilada.htm | art389(788) art1723(565) art1571(545) art1694(494) art1829(481) art421(454) art927(385) art186(211) art944(207) art187(195) art422(147) art1784(112) |
| **CDC** `89aa6b6376d8` → /ccivil_03/leis/l8078compilado.htm | art3(703) art7(640) art2(270) art1(249) |
| **8.245** `6469c75925db` → /ccivil_03/leis/l8245.htm | art4(756) art46(598) art9(429) |
| **CLT** `9dbef1c5d0cf` → /ccivil_03/decreto-lei/del5452.htm | art3(380) art129(242) |

## PARTE B — genuinamente ausente/stub, SEM full (precisa fetch planalto) — CF/CP + ~33

**Prioridade máxima: CF e CP têm ZERO entradas no manifesto** (nenhum stub sequer) — códigos
maiores, base de dezenas de páginas. Nenhum item da Parte B é citado pelas 25 prosas (rankeado por
prominência do código). URLs ✓ = confirmadas em `data/source-registry/`; "confirm" = padrão não
verificado no repo.

| Lei | planalto |
|---|---|
| CF/1988 | /ccivil_03/constituicao/constituicao.htm ✓ |
| CP (DL 2.848/40) | /ccivil_03/decreto-lei/del2848compilado.htm ✓ |
| LBI 13.146/15 | /ccivil_03/_ato2015-2018/2015/lei/l13146.htm ✓ |
| Maria da Penha 11.340/06 | /ccivil_03/_ato2004-2006/2006/lei/l11340.htm ✓ |
| Falência 11.101/05 | /ccivil_03/_ato2004-2006/2005/lei/l11101.htm ✓ |
| Drogas 11.343/06 | /ccivil_03/_ato2004-2006/2006/lei/l11343.htm ✓ |
| Est. Idoso 10.741/03 | /ccivil_03/leis/2003/l10.741.htm (confirm dot-form) |
| Mand. Segurança 12.016/09 | /ccivil_03/_ato2007-2010/2009/lei/l12016.htm ✓ |
| Superendiv. 14.181/21 | /ccivil_03/_ato2019-2022/2021/lei/l14181.htm ✓ |
| Est. Cidade 10.257/01 | /ccivil_03/leis/leis_2001/l10257.htm ✓ |
| Consignado 10.820/03 | /ccivil_03/leis/2003/l10.820.htm (confirm) |
| Consórcio 11.795/08 | /ccivil_03/_ato2007-2010/2008/lei/l11795.htm ✓ |
| Migração 13.445/17 | /ccivil_03/_ato2015-2018/2017/lei/l13445.htm ✓ |
| LAI 12.527/11 | /ccivil_03/_ato2011-2014/2011/lei/l12527.htm ✓ |
| Alien. Parental 12.318/10 | /ccivil_03/_ato2007-2010/2010/lei/l12318.htm ✓ |
| Lib. Econ. 13.874/19 | /ccivil_03/_ato2019-2022/2019/lei/l13874.htm ✓ |
| Planos saúde 14.454/22 | /ccivil_03/_ato2019-2022/2022/lei/L14454.htm ✓ |
| Distrato 13.786/18 | /ccivil_03/_ato2015-2018/2018/lei/l13786.htm ✓ |
| Cad. Positivo 12.414/11 | /ccivil_03/_ato2011-2014/2011/lei/l12414.htm ✓ |
| Saneamento 11.445/07 | /ccivil_03/_ato2007-2010/2007/lei/l11445.htm ✓ |
| Marco Garantias 14.711/23 | /ccivil_03/_ato2023-2026/2023/lei/l14711.htm ✓ |
| Juros CC 14.905/24 | /ccivil_03/_ato2023-2026/2024/lei/l14905.htm ✓ |
| Crimes eletr. 14.155/21 | /ccivil_03/_ato2019-2022/2021/lei/l14155.htm ✓ |
| LC 116/03 | /ccivil_03/leis/lcp/lcp116.htm ✓ |
| LC 150/15 | /ccivil_03/leis/lcp/lcp150.htm ✓ |

Menores/omitidos (baixa prioridade): 10.522/02, 10.931/04, 14.382/22, 14.478/22, 13.988/20,
Dec 11.034/22 (SAC ✓), LC 211/24, FIES/PROUNI/JEF, e **~67 stubs de súmula/1963 (48–254 B)** —
curtos por natureza, não são códigos, prioridade mínima.

## Ordem de execução recomendada

1. **Normalizar o join `art_NNN`** (pré-requisito — senão a medição do gate mente).
2. **Parte A** (dedup prefer-larger) — recupera os códigos mais usados, custo zero.
3. **Parte C** (re-fatiar 21 artigos dos blobs já em disco) — destrava o lastro das 25 prosas.
4. **Gate T3 blob<1KB reprova** (do CENSUS §5) — barra prosa mal-lastreada enquanto B não fecha.
5. **Parte B**: coletar CF e CP primeiro; demais leis por prominência.
6. Quarentena `0a21044e` das 54 prosas permanece até A+C+gate.
