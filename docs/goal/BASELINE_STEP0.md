# BASELINE STEP 0 — métricas pré-registradas (P0)

Medido em 2026-07-17T17:28Z (sessão de implementação da arquitetura de escala).
Fonte: medição direta no repositório vivo. Serve de **âncora anti-regressão**:
qualquer mudança que cruze um threshold abaixo é regressão P0 a investigar.

## Estoque e demanda (medido)

| Métrica | Valor | Threshold (regressão se) | Notas |
|---|---:|---|---|
| `v2_pages` shards | 766 | cair sem migração registrada | `data/editorial/v2_pages/*.jsonl` |
| `v2_pages` páginas totais | 7934 | cair sem supersessão registrada | cresceu de ~6584 (2026-07-09) |
| `portfolio_v2` intents | 10019 | cair sem quarentena registrada | demanda distinta > 10k (piso P0) |
| `published_manifest` | 0 | — (meta P0 = 10000) | zero é proteção temporária; sobe pós-release chain |

## Engenharia (medido)

| Métrica | Valor | Threshold (regressão se) | Notas |
|---|---:|---|---|
| Build de PRODUÇÃO (server+build+check) | 4.06s | > 60s | dev-mains tagueados `//go:build devcmds` (era ~10min) |
| Pacotes `internal/` | 339 | — | +8 novos nesta sessão |
| Pacotes `cmd/` | 265 | — | maioria dev-main tagueada |
| Checks registrados (grep) | ~1055 tokens | — | auditoria proporcional por perfil (`checkselection`) |

## Motor de fiscalização/escala construído nesta sessão (testado)

`quality`·`legalsignature`·`qualitysampling`·`infogain`·`fiscalizationtiers` (T0–T2)
· `grounding`(+`cache` O(fontes)≠O(páginas))·`groundingcontrols`·`adversarialconsensus` (T3–T4)
· `entitycandidate` (escala/anti-doorway)·`answerfirst` (GEO)·`sitesearch` (P1 `/buscar/`)
· `redteamcoverage` (catch-rate adversarial)·`pagefactory` (orquestrador capstone).

## Caminho crítico restante até `published_manifest > 0`

O gargalo NÃO é geração (7934 páginas existem) nem arquitetura (construída). É a
**integração**: aterrar o fecho semântico v2 em HEAD (commit sancionado
`semantic-recut`) → `ingest-v2-stock` WRITE-FULL → `bootstrap-chain` → verdict → cohort
→ `promote-authorial-mass-public-release`. Ver `wiki-session-commit-gate-state` (memória).
