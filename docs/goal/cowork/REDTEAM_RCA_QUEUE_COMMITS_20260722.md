# REDTEAM_RCA_QUEUE_COMMITS_20260722 — Red-team de 4 commits do terminal (Cowork Fable 5)

Método: 2 agentes adversariais com leitura de diff completo + código ao redor + testes rodados ao vivo.

## 1. `8cdb06da` (RCA D4.8) — SÓLIDO COM RESSALVAS, com FURO LÓGICO no design

- Diagnóstico factual bom (timeline com hashes reais). MAS: o dano maior do loop (9 commits/11,7h
  reparando a MESMA família, um furo por vez) NÃO é "rerun idêntico" — e a fórmula proposta
  `unit_key = sha256(kind+queue+input_oids+EPOCH_DO_CÓDIGO)` **zera o orçamento a cada edição**
  (todo retry pós-edit vira "unidade nova"). O mecanismo não bloquearia as tentativas 3ª-9ª.
- O entregável real do commit é 100% prosa (a própria seção 5 admite: "comitter/geradores ainda
  não recusam rerun por chave"). Nenhum unit-ledger existe no repo.
- **REUSO IGNORADO**: `internal/factoryworkqueue/types.go:42-47` JÁ TEM `WorkUnitKey`
  (content-addressed, sem timestamp/HEAD), `LineageKey` (orçamento anti-micro-ajuste POR FAMÍLIA)
  e `CircuitState/CircuitReason` — circuit-breaker pronto que a RCA propõe reinventar.
- **Correção executável**: `family_key = sha256(kind + target_path_set)` SEM epoch, contador
  próprio; 3ª tentativa na mesma família → hook bloqueia commit e abre task de censo. Implementar
  sobre `factoryworkqueue`, não criar segundo ledger.

## 2. `5a40b63d` (fila destravada) — SÓLIDO COM RESSALVAS; FURO ABERTO CONFIRMADO

- Dedupe cross-lote existe e roda (`relaunch-writing.sh:422-430`), exclusão escrita/revisão é
  estrutural — mas a lógica é COPY-PASTE nos dois scripts (extrair para produtor comum).
- **FURO ativo**: `banc-alienacao-fiduciaria` (intent genérico antigo com shard escrito) ficou FORA
  do pin do lote `bancario-14` (21 sub-intents) SEM tombstone DEC-020 → guard fail-closed trava a
  fila. "Pipeline destravado" no título é otimista; frontboard já enfileira 4º patch no mesmo dia
  (padrão "um furo por vez" que a própria RCA D4.8 diagnostica).
- **Correção executável**: gravar tombstone DEC-020 ligando `banc-alienacao-fiduciaria` aos 21
  sucessores (ou reincluí-lo no pin) + anexar log VERDE de `ops/relaunch-writing.sh` ao commit
  que fechar `writing-queue-unblock` — não declarar destrave sem a corrida real.
- Cobertura de gap: os lotes novos NÃO atacam o GAP2345 (2 fora do top-5; 1 é intent único) —
  fix de schema, não de volume. As 6 ondas do WRITING_WAVES seguem sendo a rota do gap.

## 3. `6e69183b` (closure semantic-recut generation-aware) — SÓLIDO

- Não aceita âncora stale: 2 anchors sempre-reautenticados por digest vs env; 2 imutáveis exigem
  OID pai==filho fora do delta (`GuardError` em divergência). Teste novo cobre exatamente o
  cenário stale; suíte 26/26 verde rodada ao vivo. Bypass por env var é pré-existente/documentado
  (guard cooperativo, não barreira anti-insider). **Destrava o pouso dos 317 com segurança.**

## 4. `d3dcf141` (projeção DEC-020 byte-exact) — RESSALVAS

- Paridade real: `TRUSTED_SUPERSESSION_ARCHIVE_SHA256` bate com `integrity.go:42` ✓; comparação
  é worktree×archive com SHA do archive inteiro ✓. Falso-positivo: NÃO (conteúdo mudado → None).
- Lacunas: (a) só espelha a perna `ExactActiveSources` — pernas `ChangedActiveSources`+forward
  ficam fora do espelho Python (falso-NEGATIVO conservador; Go continua correto); (b) ~180 linhas
  novas SEM teste unitário dedicado (só a corrida ao vivo). **Pedir regressão automatizada.**

## 5. Estado B4→B6 / publicação (fiscal)

`published_manifest.jsonl` = **0 bytes**. Nenhum commit pós-87e805cb toca publicrelease/promote.
Os avanços atuais são B5 (recuperação pré-ingestão, "desbloqueia 13 lotes"). A fase de release
ainda não começou — o primeiro cohort segue sendo o marco que falta.

## 6. Adjudicação dos "20 intent_ids duplicados" — JÁ RESOLVIDOS (19/20)

19 pares já consolidados por `duplicate_intent_consolidated` (lotes 2026-07-11 imobiliário e
2026-07-21 aéreo) com archive em `v2_superseded/` — adjudicação independente CONFIRMA as
canônicas escolhidas (nenhuma inversão necessária; 1 par apertado: `aer-cancelamento-...`, wc
decide por 17%). O 20º (`trib-execfiscal-averbacao-pre-executoria`) NÃO é duplicata: skip antigo
por incerteza da ADI 5881 + página nova r01 que a resolve — apenas padronizar metadado
(`superseded_by` em tributario-07) quando conveniente. Fila de limpeza: FECHADA.
