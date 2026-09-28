# Spec conector P2 nº1 — STJ precedentes qualificados (2026-07-21)

## Demanda real medida (7.722 registros / 671 shards)
- sumula: 2.380 citações (top: Súmula 479 STJ)
- tema (repetitivos/repercussão geral): 1.676 (top: Tema 1=274, Tema 987=130, Tema 350=46)
- resolucao: 629 (Resolução 400 ANAC domina: 223+98+21)
- provimento: 57 (Provimento 149 CNJ=26); in_rfb: 44

## Canais verificados (robots/termos, 2026-07-21)
| Tipo | Canal | Veredito |
|---|---|---|
| Súmula/Tema STJ | dadosabertos.web.stj.jus.br (CKAN), dataset "Precedentes qualificados", CSV/JSON, CC-BY; robots: Disallow /api/ e /revision/, Crawl-Delay 10, /dataset/ LIBERADO | **COLETÁVEL** (via página /dataset/<slug> + download; NUNCA /api/) |
| Tema repercussão geral STF | portal.stf.jus.br + painel transparencia (Qlik/JS), sem endpoint REST documentado | **BLOQUEADO** (sem export oficial; engenharia reversa = risco de contrato) |
| Resolução ANAC | dados.gov.br (WAF 401 em fetch anônimo); alternativa gov.br/anac página oficial | **INCERTO** (reverificar com UA honesto) |

## Conector: cmd/collect-stj-precedentes-qualificados
- Canal: https://dadosabertos.web.stj.jus.br/dataset/ — resolve slug do dataset,
  baixa o CSV declarado (nunca /api/).
- Flags: --dataset-slug, --out data/source-registry/stj-precedentes/, --dry-run
  (default true), rate hard-coded >=10s entre requests (Crawl-Delay do robots).
- Destino: data/source-registry/stj_precedentes_qualificados.jsonl —
  METADATA-ONLY: numero do tema, recurso repetitivo, situacao, data de fixacao,
  URL fonte, sha256 do CSV bruto. Nunca texto de acórdão em corpo público.
- Gates fail-closed: robots mudou/bloqueou /dataset/ ⇒ aborta; licença CC-BY
  ausente na página do dataset ⇒ aborta; idempotência por hash (recoleta só se
  o hash do CSV mudar).
- Não encontrado: API REST documentada de súmulas STJ; export estruturado do
  painel STF; dataset ANAC confirmado (WAF).
