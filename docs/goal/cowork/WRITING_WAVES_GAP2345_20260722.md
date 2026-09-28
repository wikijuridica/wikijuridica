# WRITING_WAVES_GAP2345 — Gap de escrita medido + 6 ondas priorizadas (Cowork Fable 5, 2026-07-22)

Método: interseção de conjuntos de intent_id (portfólio `data/editorial/portfolio_v2/*.jsonl`, 61 arquivos
× estoque `data/editorial/v2_pages/*.jsonl`, 671 shards) — NÃO a subtração ingênua do BUG-009.

## Números exatos (2026-07-22)

- Portfólio: **10.041** intents únicos (sem duplicidade interna)
- Estoque: **7.702** intents únicos (7.722 linhas; **20 intent_id duplicados** em 2 shards cada — limpar)
- Interseção: **7.696** | Órfãos no estoque sem portfólio: **6**
- **GAP: 2.345** (23,4%) — lane comercial **1.975 (84,2%)** / informativa 370

## Gap por área (top) × taxa de aceitação histórica (report 17-18/07)

consumidor 243 (91,8%), glossario 182 (88,1%, informativa), empresarial 172 (96,7%),
trabalhista 159 (91,9%), bancario 142 (96,2%, 100% comercial), previdenciario 132 (95,9%),
criminal 110 (100%), familia 108 (96,2%), saude 105 (94,0%), digital 102 (87,4%),
seguros 102 (65,5% — risco de retrabalho), tributario 95, sucessoes 88, servidor 82.

## 6 ondas propostas (~40 páginas/onda, score = gap × aceitação)

1. **Consumidor** — maior gap absoluto (243), 97% comercial, pipeline mais maduro
2. **Empresarial** — melhor aceitação entre gaps>100 (96,7%)
3. **Bancário** — 100% comercial (todo o lote monetizável), 96,2%
4. **Consumidor** (2ª rodada — pool restante 203)
5. **Trabalhista** — 159 gap, 91,9%
6. **Previdenciário** — 95,9%, 93,9% comercial

Projeção: 240 páginas fecham 10,2% do gap concentradas no top-5 qualidade×volume. Ondas 7+ continuam a
rotação no top-5 antes de descer a criminal/familia/saude (>94%). **Seguros adiado** apesar de 102 gap:
aceitação 65,5% + as 244 páginas existentes da Lei 15.040 precisam primeiro das correções do lote 2
pós-cutoff (art. 10 §ú I + nuance de transição) — escrever mais seguros agora multiplicaria o defeito.

## Limpezas apontadas (fila do terminal)

- 20 intent_id duplicados entre shards (2 cópias cada) — adjudicar canônica + tombstone DEC-020
- 6 páginas órfãs de portfólio — remapear ou aposentar
- Glossário (182, informativa) é pool de piso-10k barato: intercalar mini-lotes informativos quando
  a fila comercial estiver em revisão, sem CTA.
