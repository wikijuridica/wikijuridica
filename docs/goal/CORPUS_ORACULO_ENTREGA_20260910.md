# Corpus-oráculo — o que mudou em 2026-09-10 e o que o build final vai encontrar

Frente de `internal/sourcesnapshotaudit` + `cmd/collect-oracle`, entregue nesta
data. Este documento existe para que quem faz o build final **não cace como
regressão o que é dívida nomeada com teto escrito**.

Commits: `3151d21a` (detector), `b8f797ee` (regressão da coorte), `88f2927e`
(recoleta dirigida + tetos + notas).

---

## 1. O que estava errado, e não era o que o número dizia

`source_snapshot_placeholder_head` acusava **58** séries. Lidas uma a uma no
blob autenticado, **47 não eram defeito**: são artigo *alterador* inteiro —
`Art. 36. O inciso V do art. 30 da Lei nº 8.212 … passa a vigorar com a
seguinte redação: "Art. 30. ....."` — em que a omissão pontilhada está **dentro
da transcrição** da norma alterada. Texto jurídico utilizável, publicado assim
pela fonte oficial.

O comentário do detector sempre disse *"fragmentos dominados por essa
notação"*; a regra escrita testava **contenção** (`dottedOmissionRE.MatchString`),
que é outra coisa. Passou a exigir que a omissão **abra** o corpo.

## 2. A família que apareceu ao levantar os 11 verdadeiros

O mesmo BUG-118 (fatiamento no `"Art. N.` que abre a transcrição), agora visto
no caminho de coleta. Cada ocorrência produz **dois** defeitos, e o segundo não
tinha detector nenhum:

| Código novo | O que é | Contagem hoje |
|---|---|---|
| `source_snapshot_amending_head_truncated_at_quote` | cabeça alteradora cortada na aspa que abria a transcrição (`… seguinte redação: "`). Sobra texto real, sem pontos, acima de 30 bytes — era `StateVigente` e **ninguém a via** | **19** (era 30) |
| `source_snapshot_quoted_fragment_promoted_device` | trecho transcrito promovido a dispositivo do diploma **errado** | **16** |

Dez dos 16 sobrescrevem artigo que o diploma **realmente tem**: CPC 14, 33, 48,
50, 83, 274 e 275 guardavam texto da Lei 9.099, da Lei 9.307, do Código
Eleitoral e do Código Civil; Lei 8.245 3, 8 e 24 guardavam texto da Lei 8.009,
da Lei 4.380 e da Lei 4.591. É a classe *"citação legal mal atribuída"* que o
`CLAUDE.md` nomeia como P1 permanente.

**Coorte datada:** os 84 registros das 16 séries vieram todos de `fetched_at`
**2026-07-18**, canal `normas_leg_br_api_publica_texto`.

**A causa já estava fechada no código**, e isso está provado por mutação em
`internal/planaltochannel/coorte_20260718_test.go`: quem fecha é o
`quoted.contains` de `SegmentArtigos` (`citationQuoteRanges`), nascido em
`0204bb14` de **2026-07-21** — três dias *depois* daquela coleta. Neutralizar a
seleção canônica de `ValidatedArticleSegments` deixa o teste verde; neutralizar
o `quoted.contains` o deixa vermelho nos dois diplomas.

## 3. O que a recoleta dirigida corrigiu no acervo real

Comando: `collect-oracle --normas-fulltext --somente-documento` sobre as 11 URNs
da família. Ensaiado antes em cópia isolada; só depois aplicado.

| Grandeza | Antes | Depois |
|---|---|---|
| total de issues do gate | 266 | **252** |
| `amending_head_truncated_at_quote` | 30 | **19** |
| `placeholder_head` | 58 → 8 (detector) | **5** |
| séries em quarentena | 118 → 102 | **91** |
| `grounding_visible_series_count` | 6.557 → 6.573 | **6.584** |
| `closed_version_still_vigente` | 53 | 53 (imóvel) |
| `successor_retroactive_start` | 53 | 53 (imóvel) |

**A escrita é append-only e isso foi provado antes do `git add`**, não depois:
`manifest.jsonl` 13.551 → 14.746 linhas e `repair-journal.jsonl` 1.480 → 1.571,
com o prefixo **byte a byte idêntico** ao de `HEAD` nos dois arquivos
(`diff <(git show HEAD:…) <(head -n N …)`). Cinco packs novos, nenhum arquivo
reescrito.

## 4. Os vermelhos que o build final vai ver, e por que ficam

Todos com teto declarado em `internal/sourcesnapshotaudit/known_issue_ceiling_test.go`
e motivo escrito ao lado. **Nenhum é regressão introduzida agora.**

- **19 `amending_head_truncated_at_quote`.** Catorze são séries que o coletor
  pula em `statusConflitoEstadoLegado` (`cmd/collect-oracle/run.go:878`): o
  texto mudou, mas a série carrega estado jurídico legado mais forte do que
  este canal prova, e nada é gravado até decisão explícita. Cinco são da Lei
  8.078 e da Lei 13.709, que **não saem por este canal**
  (`urn_coberta_por_camara_legin_html_reconciliar`); a passada dirigida por
  `--camara-legin` levou **HTTP 429** nas duas, três tentativas cada. Limite
  externo, não escolha.
- **16 `quoted_fragment_promoted_device`.** O manifest é append-only e o corpus
  **não tem retratação de dispositivo**: cinco desses dispositivos não deveriam
  existir (Lei 8.245 `art_167` e `art_169`, CPC `art_2027` e `art_216-A`, Lei
  6.194 `art_20`) e nenhuma versão nova conserta a existência deles. Este teto
  não chega a zero pelo caminho de hoje.
- **53 + 53** (`closed_version_still_vigente`, `successor_retroactive_start`):
  dívida legada já analisada na nota longa do próprio arquivo de tetos.

## 5. O caminho que fica aberto, com o desenho já medido

**As doze séries de `same_observation_multi_hash` são esta mesma família**, e o
**texto certo já está gravado no corpus**. A "oscilação de hash no mesmo dia"
(A→B→A→B em 2026-07-18) era o segmentador quebrado: uma passada recortava o
artigo do próprio diploma, a outra entregava a transcrição. Nas doze a paridade
é limpa — **`version_seq` ímpar = artigo do próprio diploma; par = transcrição
alheia** — e a cabeça caiu na par.

```
(Lei 8.245, art_8)    v1/v3  708 B  "Se o imóvel for alienado durante a locação…"
                      v2/v4  215 B  "O sistema financeiro da habitação…"   (Lei 4.380)
(Lei 13.105, art_48)  v1/v3  617 B  "O foro de domicílio do autor da herança…"
                      v2/v4  224 B  "Caberão embargos de declaração…"      (Lei 9.099)
(Lei 13.105, art_275) v1/v3  583 B  intimação por oficial de justiça
                      v2/v4 1.183 B embargos                               (Código Eleitoral)
```

O modelo **já tem** a saída: `sourcesnapshotaudit.ResolutionCollapse` +
`ResolveReviewedHead` selecionam uma versão observada como cabeça, excluem as
falsas e exigem evidência com verificador independente. O que falta:

1. **produtor** que emita o `RepairRecord` de colapso para essas séries;
2. **`ReviewEvidenceVerifier`** — e aqui a evidência honesta é mecânica, não
   opinativa: re-segmentar hoje o blob de nível-norma da mesma URN e conferir
   que o texto daquele dispositivo bate com `SelectedHeadSHA256`;
3. **consumo**: `corpus.OpenGuarded(root, sha, excluded []SeriesKey)` hoje só
   **exclui** série; resolver cabeça exige campo novo e lógica nova em
   `Get`/`LatestForUpdate`/`ResolveAsOf`. **É mudança de semântica do store.**

**Não foi feito agora de propósito**, e o motivo é de risco, não de escopo:
mexer na resolução de cabeça do `internal/corpus` a poucas horas do build final
faria o build rodar contra um store cuja semântica mudou sem medição do que mais
lê esses caminhos.

**Uma correção de contagem para quem pegar:** são **onze** resolvíveis por
colapso, não doze. `Lei 6.194 art_20` tem as **duas** paridades transcritas
(v1 = art. 20, alínea b do Decreto-Lei 73/1966; v2 = a alínea 1 do mesmo
artigo), então não há cabeça correta a selecionar. E `Lei 14.544 art_3` tem v1/v3
do próprio diploma, porém na forma **truncada na aspa** — selecioná-la troca
fragmento alheio por cabeça truncada, o que é melhor mas não é limpo.

## 6. Efeito em página publicada, medido

A quarentena tirou do grounding dez números de artigo **reais**. Sete arestas
`página→dispositivo` do grafo tocam esses artigos:

- `13105 art_48` — `/sucessoes/competencia-foro-inventario/`,
  `/sucessoes/herdeiro-nao-assina-inventario/`,
  `/sucessoes/inventario-extrajudicial-qual-cartorio/`
- `8245 art_8` — `/imobiliario/clausula-vigencia-averbada/`,
  `/imobiliario/comprador-denuncia-locacao/`,
  `/imobiliario/imovel-alugado-penhorado-leilao/`, `/leis/8245-art-8/`

Medido em `/leis/8245-art-8/` com `cmd/verify-grounding`: `claims=8`,
`UNVERIFIABLE=6`, `PENDING=2`, `páginas-reprovadas=1`. **Dois** dos seis são o
dispositivo `art_8` (`ausente do corpus local`); os outros **quatro** são
vigência de nível-norma (`;8245!` e `;10406!`), que **já reprovavam antes desta
frente** e pertencem à família `metadata_only_vigencia_unverified` (20). Ou
seja: a página não passou a reprovar agora — ganhou dois claims a mais no
mesmo veredito.

E o texto que o grounding servia para `8245 art_8` **era o da Lei 4.380**.
Ficar sem oráculo é pior que nada só na aparência; servir o artigo errado é o
defeito que a OAB enxerga.

---

Autoria e responsabilidade: Rafael Toledo, OAB/RJ 227191.
