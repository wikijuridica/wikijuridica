# FISCAL_TERMINAL_20260722 — revisão adversarial dos commits recentes do terminal

Autor: `claude-cowork-fable` (Cowork Fable 5, ciclo agendado 08:11–08:35). Método: 6 agentes
paralelos com leitura REAL (diffs, 10 prosas inteiras, 10 súmulas vs fonte viva, 10 páginas de
3 shards, varredura pós-cutoff do estoque). Escopo: `5a40b63d`, `8cdb06da`, `4f5954d0`, `8289e875`.

## 1. `4f5954d0` — 54 prosas de entidade GROUNDED: **REPROVADO para público** (grave)

Texto bom (PT-BR natural, teor normativo real — promessa do 55cdc904 cumprida no eixo "teor"),
mas **~40% da amostra de 10 tem erro material**. A T3 verify-grounding é INDISPENSÁVEL antes de
qualquer promoção destas prosas. Arquivo: `data/ops/entity_prose_grounded_20260721.jsonl`.

| idx | página | erro |
|---|---|---|
| 52 | art. 74 L8.213 | **GRAVE**: "pedido em até 180 dias → retroage ao óbito" como regra geral. Lei vigente (L13.846/2019, no próprio corpus): 180 dias SÓ filhos <16; **90 dias** para os demais dependentes. Erro em title, meta, seção e FAQ. |
| 27 | art. 59 L8.245 | "prova escrita da rescisão do contrato" — a lei diz rescisão do **contrato de trabalho** (locação de ex-empregado). Sentido trocado. Omite caução=3 aluguéis e 30 dias da temporada. |
| 3 | art. 5º CDC | Rol apresentado como completo sem incisos V (associações) e VI (superendividamento, L14.181/2021); caput diz "entre outros". |
| 21 | art. 3º CLT | Definição de empregado **sem "mediante salário"** (onerosidade) em título, meta, corpo e FAQ. |

Causa-raiz adicional descoberta: **furo no corpus** — manifest aponta stubs de 89/87 bytes (só
ementa do Senado) como "Lei 8.213" e "Lei 8.245"; o texto real da 8.245 existe em blob de 55KB
desligado da URN; da 8.213 só excerto de 3KB do art. 74. ~19/54 prosas (previdenciário +
inquilinato) foram "grounded" com lastro incompleto. Molde leve: "Na prática" abre 52% das prosas;
opening≈seção-1 no redator prosa2-17. Schema inconsistente: 10 seções `paragraphs[]` vs 192 `body`;
FAQ em 3 formatos (`q/a`, `question/answer`, `pergunta/resposta`) — renderer que espere `body`
dropa conteúdo silencioso.

**Correções executáveis:** (1) T3 dura pré-promoção: claim numérico/prazo confere contra redação
VIGENTE (flag "redação dada pela Lei..."); reescrever idx 52, 27, 3, 21 com os textos acima.
(2) Sanear corpus: ingerir texto integral da L8.213; religar URN→blob 55KB da L8.245; T3 reprova
automática de entidade com blob-fonte <1KB. (3) Normalizar schema (sections→`body`, faq→`q/a`) +
reprompt: banir "Na prática" na opening (cap 1/redator), proibir opening≈seção-1.

## 2. `8289e875` — 67 súmulas STF via LexML: **APROVADO** (canal confiável)

Verificação viva por amostragem: **10/10 exact** contra fonte oficial (4 por fetch direto LexML
server-rendered; 0 divergências). Detalhe em `data/source-audit/cowork_sumulas_stf_recheck_20260722.jsonl`.
Ressalvas: (a) **Súmula 14 está CANCELADA** (RE 74.486 → Súmula 683) — manifest sinaliza
honestamente `vigencia_status:"nao_verificado"`, mas VIGÊNCIA precisa de camada própria antes de
uso editorial (súmula cancelada citada como vigente seria erro grave); (b) URN gravada como
`sumula:1963;N` — LexML canônico é `sumula:1963-12-13;N` (data completa); resolver aceita a curta,
mas normalizar para a datada é mais robusto para recheck futuro.

## 3. `5a40b63d` — pipeline de fila destravado: **APROVADO-COM-RESSALVAS**

Sólido: `take` 6076→6076, 0 intent_ids duplicados, fontes NÃO inventadas (catálogo pré-existente,
82 hints; a mensagem superdimensiona — só os validadores passaram a aceitar v2). Ressalvas:
(a) enum de source_kind hardcoded em 2 lugares (`tools/generate_v2_review_queue.py:1490` e
`ops/relaunch-writing.sh:192`) — derivar de `_meta.source_kind_policy` do catálogo (fonte única);
(b) `scripts/workflows/writing-mass-full.js` é espelho inerte (throw no topo) — pode divergir
silencioso; criar check ou remover; (c) fila dup_phrase: o fix destrava a regen mas NÃO regenera —
a fila CAS ainda precisa do rerun (consistente com DUPPHRASE_DRAIN_SPEC_20260722: rerun antes de
gastar redator).

## 4. `8cdb06da` — RCA D4.8: **APROVADO** (forense genuína; evidência 100% verificada)

51 tombstones conferem; hashes batem; contramedidas não contradizem contratos. Ressalvas para a
implementação do guard: (a) **`epoch_do_código` subespecificado** (§4.1 l.111) — se for git HEAD,
mata o dedup a cada commit; fixar como hash de conteúdo do binário/closure da tool; (b) função de
identidade de "falha NOVA" (§4.3 l.137) não definida; (c) nit: "9 commits" no §2 — o comando citado
retorna 6 (os 3 extras tocam outros paths).

## 5. Ligações com entregas paralelas deste ciclo

- Estoque criminal: **claim FALSO** achado ao vivo — `criminal-11.jsonl:2` cita "inciso IV = 30%
  reincidente violento" (Lei 15.402/2026); oficial: 30% é **inciso II**; inciso IV foi **VETADO**.
  + causalidade imprecisa da Lei 15.358/2026 (patamares 70/75% já existiam desde 2019).
  Detalhe e fila de 15 claims: `data/source-audit/cowork_claims_poscutoff_20260722.md`.
- Molde: cidadania-04 é **falso-positivo de medição** (20 skips contados como páginas);
  seguros-r02 tem molde real (módulo Lei 15.040 clonado 4/5). Specs:
  `docs/goal/cowork/MOLD_ADJUDICATION_ADDENDUM_20260722.md`.
- Demanda: gap de escrita nova é **2.345 intents** (não 3.2k — o resto é fila de revisão);
  top 10 famílias cobrem 61,7%: `docs/goal/cowork/DEMANDA_BRIEF_20260722.md`.
