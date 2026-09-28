# FISCAL FABLE — Red-team dos 10 drops OPUS_FLEET_W1 (2026-07-22)

Fiscal: Fable 5 adversarial. Método: releitura integral dos 10 drops + re-verificação AO VIVO das
alegações jurídicas de maior risco (planalto.gov.br, gov.br/susep, stj.jus.br, noticias.stf.jus.br,
camara.leg.br — fetch/busca 2026-07-22) + spot-check de file:line e dados no repo (read-only).
Resultado: **5 GREEN · 4 YELLOW · 1 RED**. Uma refutação viva material (prosas33 FIX-1).
Nenhum drop editou `data/editorial/`, `data/ops/`, `v2ingest.go` ou `validate.go` (os patches de
fila-noop e catálogo encontrados no worktree foram aplicados pelo main, conforme handoff dos drops).

---

## PER-DROP VERDICTS

### 1) `OPUS_FLEET_W1_poscutoff_penal_20260722.md` — **GREEN**
Re-verifiquei ao vivo TODAS as 6 leis penais de 2026 no Planalto (independente do agente):
- **15.358** (l15358.htm): art. 310 CPP "no prazo máximo de até 24 horas… por meio de videoconferência
  em tempo real" ✓; alterações ao art. 313 CPP com "organização criminosa ultraviolenta, grupo
  paramilitar ou milícia privada" ✓; art. 112 LEP V=70% primário hediondo, VI=75%, VII=80%
  reincidente hediondo, VIII=85% reincidente hediondo com morte ✓ (verbatim).
- **15.402** (l15402.htm): caput art. 112 = "ao menos 1/6 (um sexto)"; I=25% primário
  violência/grave ameaça, II=30% reincidente, III=20% reincidente em crime diverso; **IV a X (VETADO)**
  ✓; art. 126 §9º ✓. O HOLD único (`crim-quanto-cumprir-para-progredir`) está VINDICADO: duas
  redações do mesmo art. 112 em 6 semanas com incisos hediondos vetados = risco real de vigência.
- **15.380**: audiência de retratação "somente será designada pelo juiz mediante manifestação
  expressa" + "tem por objetivo confirmar a retratação, não a representação" ✓.
- **15.383**: art. 12-D (risco atual/iminente → monitoração), art. 22/24-A alterados ✓.
- **15.384**: ementa = violência vicária + tipo penal do **vicaricídio (art. 121-B CP)** + rol de
  hediondos ✓; **zero ocorrências de "título executivo"** (relevante p/ drop 2).
- **15.438**: "prazo de 12 (doze) meses, contado do dia em que veio a saber quem é o autor" ✓,
  tocando CP 103 / CPP 38 / LMP 16-A ✓.
Nota: o HOLD deve ser resolvido em conjunto com o erratum #1 do drop 2 (ressalva STF) — a página
precisa das DUAS coisas (reconciliação de vigência + ressalva de suspensão). Nit sem efeito: a
tabela deste drop acerta o shard de `crim-acao-penal-condicionada` (criminal-09; confirmado no disco).

### 2) `OPUS_FLEET_W1_erratas_lote3_20260722.md` — **GREEN**
As 3 erratas bloqueantes confirmadas ao vivo por mim:
1. **15.402/STF**: ADIs 7.966/7.967 (ABI e PSOL-Rede, 08/05/2026) + decisões de Moraes assinadas
   09/05/2026 suspendendo a aplicação às execuções dos condenados do 8/1 até o Plenário —
   confirmado em noticias.stf.jus.br ("Relator suspende aplicação da Lei da Dosimetria a execuções
   penais no STF"). O trecho-alvo "retomou um sexto como regra geral" existe verbatim em
   criminal-11.jsonl:2 ✓ e é juridicamente correto (caput = 1/6) — falta só a ressalva, como o drop diz.
2. **Tema 1.279**: "ambos os prazos" existe verbatim em bancario-inf1.jsonl:4 ✓. DL 911/69 ao vivo:
   §1º "Cinco dias após executada a liminar…"; §3º "resposta no prazo de quinze dias da execução da
   liminar" ✓ — o texto corrigido (5 dias = tese; 15 dias = texto legal, não a tese) é exato.
3. **Título executivo**: Planalto **l15412.htm** = "Art. 22 … § 10 As medidas protetivas de natureza
   cível, inclusive as de prestação de alimentos provisionais ou provisórios, constituem título
   executivo judicial de pleno direito, dispensando a propositura de ação principal" ✓ VERBATIM,
   inclusive o detalhe "§ 10 no art. 22". **l15384.htm não contém "título executivo"** →
   a misattribuição em leis-inf2.jsonl:8 (frase confirmada no shard) é real e o fix é o correto.
File:line 3/3 exatos (bancario-inf1:4, leis-inf2:8, criminal-11:2 — conferidos no disco).
Nit: o parêntese "(criminal-04-real)" para crim-acao-penal está errado (é criminal-09), mas essa
linha é um falso-positivo que não gera ação — sem efeito.

### 3) `OPUS_FLEET_W1_mold_disclaimer_20260722.md` — **YELLOW** (landa com caveats)
Censo confirmado no disco: 28 ocorrências / 23 shards da string exata ✓. F3 verificado:
`dig-remocao-expedita-video-intimo` está `lane=comercial`, `cta=null` no digital-07.jsonl → a
reclassificação para informativa é correta e OAB-conservadora. F4: Resolução CNJ 571/2024 é REAL
(26/08/2024, altera a Res. 35/2007 — divórcio/inventário extrajudicial; múltiplas fontes), e a
recusa de inventar o ID de atos.cnj é o fail-closed certo. Lexicon: `internal/paidintent/paidintent.go`
contém "advogado particular" → F1/F2 casam o léxico. Caveats obrigatórios:
- **(a) Família > 28**: meu grep da família `(conteúdo|guia) é informativ` = **95 ocorrências** no
  estoque (mais até que os "75 pgs" citados). Drenar por regex/percentil como o próprio drop pede;
  extinguir só as 28 não fecha o molde.
- **(b) Molde residual nas NEW**: as aberturas variam, mas quase todas fecham no esqueleto
  "…depende de X, Y e Z" (enumeração tripla). Rodar dup-phrase/similarity sobre as 28 NEW antes de
  aplicar; para as 7 informativas preferir a REMOÇÃO (rota que o drop já recomenda).
- **(c) `**bold**` nos textos F1/F2**: os trechos de inserção contêm marcadores markdown `**` —
  corpo v2 é texto puro; aplicar SEM os asteriscos (senão vira lixo visível PT-BR).

### 4) `OPUS_FLEET_W1_prosas4_20260722.md` — **GREEN**
idx 52 re-verificado ao vivo por mim no l8213cons.htm: art. 74, I = "…em até cento e oitenta dias
após o óbito, para os filhos menores de dezesseis anos, ou em até **noventa dias após o óbito, para
os demais dependentes**" ✓ (ambas as redações MP 871 e L13.846 no consolidado). A prosa idx 52 no
`entity_prose_grounded` (linha 53) realmente apresenta 180d como regra geral e tem **zero**
ocorrências de "noventa" ✓ → erro material real, reescrita correta. idx 3 (CDC art. 5º I–VII, "entre
outros", VI/VII pela L14.181/2021), idx 21 (CLT art. 3º "e mediante salário") e idx 27 (L8245 art.
59 §1º: caução de 3 meses, inc. II "contrato de trabalho", inc. III 30 dias) batem com o texto
consolidado estável (pré-cutoff, sem alteração 2026) — sem risco de currency. Reescritas autorais,
sóbrias, ancoradas; quarentena mantida; handoff correto (gate blob≥1KB antes de promover). GREEN.

### 5) `OPUS_FLEET_W1_prosas33_grounding_20260722.md` — **RED** (não landar como está)
**REFUTAÇÃO VIVA do FIX-1 (o único achado "material" do drop).** O drop afirma: "O art. 59 [L8213]
**não menciona prisão, reclusão nem prazo de 60 dias**" e manda **excluir integralmente** as seções
e FAQs de prisão/60 dias da prosa idx 18, roteando-a como alucinação estrutural. O Planalto AO VIVO
(l8213cons.htm, 2026-07-22) diz o contrário — art. 59 tem exatamente esse regime:
> "§ 2º Não será devido o auxílio-doença para o segurado **recluso em regime fechado**. (Incluído
> pela Lei nº 13.846, de 2019) § 3º O segurado em gozo de auxílio-doença na data do **recolhimento à
> prisão terá o benefício suspenso**. § 4º A suspensão prevista no § 3º deste artigo será de **até 60
> (sessenta) dias**, contados da data do recolhimento à prisão, **cessado o benefício após o referido
> prazo**. § 5º …restabelecido a partir da data da soltura."
Ou seja: a prosa idx 18 está SUBSTANCIALMENTE CORRETA nos pontos que o drop chama de invenção;
executar a "correção" apagaria conteúdo jurídico verdadeiro e introduziria erro. Causa provável: o
fetch do agente veio truncado (o próprio drop 4 registra que l8213cons trunca) e ele julgou com
página parcial — exatamente o risco de blob-stub que a frota já mapeou.
**Salvável do drop:** (i) FIX-2 é correto (CLT art. 71 §1º: os 15 min só quando a jornada ultrapassa
4h — texto vigente confirma); (ii) dentro do FIX-1, a ÚNICA parte válida é aditiva: a prosa omite o
núcleo "incapacidade por mais de 15 dias consecutivos" e o §1º — acrescentar, sem apagar nada;
(iii) a tabela de 10 CLEAR e a lista de 38 residuais seguem úteis. **NÃO rotear idx 18 para
`prosas-4-reredacao` como erro material.** Reprocessar o FIX-1 com o texto integral do art. 59.

### 6) `OPUS_FLEET_W1_seguros244_20260722.md` — **YELLOW** (landa com sweep completo)
- Fix #1 confirmado verbatim ao vivo (l15040.htm): "Art. 10 … **Parágrafo único.** São nulas as
  garantias…: I - de interesses patrimoniais relativos aos valores das multas e outras penalidades
  aplicadas em virtude de atos cometidos pessoalmente pelo segurado que caracterizem ilícito
  criminal" ✓ → "art. 10, parágrafo único, I" é a âncora certa.
- Fixes #2/#3 (10→11/12/2025): **SUSEP oficial confirma 11/12/2025** — notícia gov.br/susep
  publicada 11/12/2025 08:30: "**Entrou em vigor hoje (11)** a Lei nº 15.040/2024" ✓. A notícia da
  Câmara 1119630 é mesmo de 10/12/2024 19:34 (teoria da origem do erro confirmada). Arts. 132/133 e
  134 (vacatio 1 ano) conferidos ao vivo ✓.
- **Caveat 1 (incompletude do sweep):** `seguros-06` tem **≥3** ocorrências de "10 de dezembro de
  2025" (contextos arts. 120, 116 e exclusões) e `sumulas-03` tem **≥3** — a fila cita 1 trecho por
  página. Substituir TODAS as ocorrências nas duas páginas e re-grepar o estoque inteiro por
  `10 de dezembro de 2025` associado à 15.040 antes de fechar.
- **Caveat 2 (proveniência da data):** ancorar o "11/12/2025" na notícia oficial da SUSEP (URL acima)
  em `official_sources`, não na derivação LC 95/98 — a aritmética estrita do art. 8º §1º (paralelo
  CC/2002: publicado 11/01/2002 → vigor 11/01/2003) a partir de DOU 10/12/2024 daria 10/12/2025;
  quem fixa o 11 é a manifestação oficial do regulador, e é ela que deve constar como fonte.
- **Caveat 3 (anti-template no P2):** injetar a MESMA moldura de transição verbatim em 13–17+
  páginas cria bloco repetido literal — variar a redação por página (ou decidir conscientemente a
  isenção como boilerplate de vigência), NUNCA afrouxar o gate de duplicidade para ela passar.

### 7) `OPUS_FLEET_W1_restamp391_20260722.md` — **YELLOW** (landa com 1 sub-recomendação vetada)
- GATE A: `pesquisa_livre=1390` confirmado no tributario-r02.jsonl (com 3 irmãos `cod_tema_inicial`
  passando) ✓. **Tema 1.390 é REAL**: notícia oficial do STJ (23/02/2026, "Repetitivo afasta teto de
  20 salários mínimos para base de cálculo das contribuições parafiscais"; Primeira Seção, unânime,
  rel. p/ acórdão Min. Maria Thereza) — tese: a base de INCRA, salário-educação, DPC, FAER, SENAR,
  SEST, SENAT, SESCOOP, SEBRAE, APEX-Brasil e ABDI **não** se limita a 20 SM ✓. A troca da URL por
  deep-link `cod_tema_inicial=1390` é a mesma família dos irmãos que passam → correta, via fila.
- GATE B: file:line reais (main.go:32-49 ainda pré-patch; audit.go:482-491 `record.CheckedAt ==
  checkedAt` confirmado). Como evidência stale NUNCA é reutilizável (guard de mesmo-dia), o patch
  abort→drop-and-refetch **não estende confiança a bytes velhos e não afrouxa gate** — e preserva
  fail-closed para falha não-stale de hoje. Aprovado; Go = commit pesado serializado, junto do bundle
  `verifier-live-browser-kind` como o drop já pede.
- **VETO parcial no P2 (evidence-laundering):** a "resolução preferida" mapearia registros wave2 com
  `method: websearch_confirmed` para `cowork-fable-live-*` + `verdict:"ok"` + nota de browser. Isso
  **fabrica proveniência**: declara verificação live-browser que NÃO aconteceu, passando pelo canal
  de override mais confiável do loader. NÃO normalizar os ~6 refs wave2 sem antes re-verificá-los em
  browser DE VERDADE (aí sim carimbar com método verdadeiro). Alternativa aceitável: deixá-los
  bloqueados até a verificação real. O restante do drop (P1: passar o flag `--cowork-live-browser-insumo`
  no driver) está correto.

### 8) `OPUS_FLEET_W1_fila_noop_20260722.md` — **GREEN** (já aplicado pelo main; verificado no disco)
Patch JÁ LANDADO no worktree exatamente como o spec: `writer_noop_batch` em
`tools/generate_v2_review_queue.py:2965` e wiring em `ops/relaunch-writing.sh:862-867` (guards de
raw-recovery/migração/relocação presentes; `if ok:` intacto logo abaixo). Mecânica do breaker
conferida no consumidor vivo (`CHUNK = 6` :727; `hardFails >= Math.max(2, ceil(0.75*janela))` :765;
progresso exige `audited_sha256 !== target_sha256`) — a análise de causa-raiz é correta: no-op
nunca progride por definição e envenena o breaker. CAS/anti-fraude intocados ✓. Caveats leves:
- Adicionar o teste de regressão para o buraco teórico "reuse==n + linha EXTRA não-autenticada no
  disco" (provar que esse lote não vira `noop` — hoje o filtro não olha extras órfãos; se tal estado
  puder chegar à emissão, o lixo ficaria estagnado no shard).
- `writing-mass-todo-part1.js` já foi regenerado (composição difere do snapshot 48/17/2 do drop) —
  re-emitir a fila antes da próxima onda, como o próprio drop manda.

### 9) `OPUS_FLEET_W1_catalogo_hints_onda2_20260722.md` — **GREEN** (conteúdo OK; atenção ao estado vivo)
- URLs de maior risco re-verificadas por mim (HTTP 200 com corpo substancial): `l8213compilado.htm`,
  `l6404compilada.htm`, `l7565compilado.htm`, `2003/l10.820.htm`, `l9870.htm`, `l5172compilado.htm` ✓.
- Flag do Tema 987/STF no anchor_claim do Marco Civil art. 19 é prudente e verdadeiro; DEFER de
  ITCMD estadual / RN 465-ANS é o fail-closed certo (não forçar linha sem prefixo oficial).
- **Bug `parse_qsl` é REAL**: `tools/check_v2_portfolio_source_hints.py:38` usa
  `strict_parsing=True` sem guard de query vazia — bug latente confirmado; abrir task de engenharia.
- **Caveat de estado vivo:** o catálogo no disco JÁ TEM **185** entradas e **52/52 chaves propostas
  JÁ EXISTEM** (crescimento 121→185 não commitado; último commit do arquivo ainda é "82->121").
  Ou seja: a onda-2 já foi aplicada ao worktree. NÃO re-inserir às cegas — aplicar como merge
  idempotente e reconciliar 1 divergência encontrada: no disco `lei-8213-1991` aponta
  `L8213compilado.htm` (L maiúsculo) vs `l8213compilado.htm` do drop — escolher casing canônico
  único após conferir se o RegistryMatcher é case-sensitive no path. Commitar o catálogo (produto
  não fica untracked).

### 10) `OPUS_FLEET_W1_rejection_triage_20260722.md` — **YELLOW** (triage OK; gate-tune sob condições)
Verificado no disco: `v2_ingest_report.jsonl` = 7702 registros / **524 rejected** ✓ (o "857" do
frontboard é mesmo stale); soma dos buckets = 524 ✓; magnitudes corroboradas (linhas com
`duplicate_phrase_with_page` = 205; `official_source_verified_at_invalid` = 225 — coerente com
dedup por causa dominante). `validate.go` refs reais (razões dup-phrase ~:409; `isLegalCitationExempt`
:1040 com critérios âncora + span ≤40 palavras). O achado estrutural **7.703 candidatos < 10k** é
sólido e importante (fila sozinha não alcança o piso; frente de geração líquida em paralelo).
**Condições vinculantes para o bucket #2 (gate-tune, +194):**
1. **Nenhuma edição em `validate.go` enquanto o fix de FAQ estiver em voo** (colisão proibida). O
   +194 espera; não entra "de carona" no mesmo arquivo em mid-flight.
2. **Amostra ANTES do tune**: auditar ≥30 dos 194 rejects com janelas verbatim e publicar a taxa
   real de falso-positivo. Só é isentável a janela que comprovadamente é citação legal (âncora
   explícita + ≤40 palavras + mesma norma/fonte). O caso cross-area já observado
   (`cons-assinatura…`←`aer-milhas…`) mostra que há vazamento no lote.
3. **Proibido relaxar** `maxLegalCitationSpanWords` (teto de 40) e a exigência de fonte/norma — o
   alargamento admissível é só de RECALL de detecção de âncora / matching de família da mesma norma,
   com testes que provem que molde real continua reprovando. Red-team Fable no diff final (este
   fiscal se voluntaria).
4. Endosso explícito do **DROP dos 39 órfãos duplicados** — publicá-los seria regressão doorway.

---

## CONSOLIDADO

**SAFE-TO-LAND (como estão, com os caveats anotados):**
- erratas_lote3 (3 erratas → fila de revisão; todas re-verificadas ao vivo).
- poscutoff_penal (19 CLEAR saem do hold; HOLD único mantido e fundido com a ressalva STF do drop 2).
- prosas4 (4 reescritas para a fila; quarentena/noindex mantidos até blob≥1KB).
- fila_noop (já aplicado; adicionar teste de extras órfãos + re-emitir fila).
- catalogo_hints_onda2 (já aplicado no worktree; merge idempotente + reconciliar casing L8213 +
  commitar + task para o bug parse_qsl).
- restamp391 GATE A (troca de URL Tema 1.390 via fila) e GATE B (patch main.go, commit Go serializado).
- seguros244 fix #1 (art. 10, parágrafo único, I) e #2/#3 com **sweep de TODAS as ocorrências**
  ("10 de dezembro de 2025" ×3 em seguros-06 e ×3 em sumulas-03) + SUSEP como fonte da data.
- mold_disclaimer: remoção nas 7 informativas; reescritas comerciais após checagem anti-molde;
  F3 (lane→informativa) e F4 (ancorar Res. CNJ 571/2024 sem inventar ID); F1/F2 sem os `**`.

**HOLD / REWORK:**
- **prosas33 FIX-1 (idx 18) — REFUTADO: não executar.** Não apagar as seções de prisão/60 dias (são
  o art. 59 §§2º-4º vigente, verbatim no Planalto); não rotear idx 18 como erro material. Rework:
  correção ADITIVA (incluir o marco de 15 dias + §1º) e re-auditar o drop com o texto integral.
- restamp391 P2 (normalização wave2 → insumo): **vetado até re-verificação real em browser** dos ~6
  refs `websearch_confirmed` — proibido rotulá-los `cowork-fable-live-*`/`verdict:ok` sem a
  verificação ter acontecido (fabricação de proveniência).
- rejection_triage bucket #2 (+194): aguarda FAQ-fix landar + amostra de 30 + tune restrito a recall
  de âncora com testes; span-cap e same-source intocáveis.
- Página `crim-quanto-cumprir-para-progredir`: permanece HOLD até (a) reconciliação da LEP
  consolidada pós-15.402 e (b) inserção da ressalva STF (ADIs 7.966/7.967, suspensão de 09/05/2026).

**RE-VERIFICAÇÕES VIVAS QUE CONTRADIZEM UM AGENTE:**
1. **prosas33 FIX-1**: art. 59 da L8213 CONTÉM §§2º-5º (recluso em regime fechado; suspensão;
   até 60 dias; restabelecimento na soltura — Lei 13.846/2019). A afirmação "não menciona prisão,
   reclusão nem prazo de 60 dias" é falsa; a correção proposta destruiria conteúdo correto.
2. **seguros244 (parcial)**: o fix está certo na direção, mas subdimensionado — 3 ocorrências da
   data errada por página (não 1); e a fundamentação pela LC 95/98 é frágil (a aritmética estrita
   daria 10/12 a partir de DOU 10/12/2024) — o 11/12/2025 se sustenta na manifestação OFICIAL da
   SUSEP ("Entrou em vigor hoje (11)", 11/12/2025), que deve ser a proveniência.
3. **catalogo_hints (estado)**: "0 colisão com as 121" está stale — o catálogo vivo tem 185 entradas
   e as 52 chaves já existem; além de 1 divergência de casing (`L8213compilado.htm`).
4. Verificações que CONFIRMARAM os agentes contra minha dúvida inicial: Lei 15.412/2026 §10 no art.
   22 (título executivo) — atribuição do drop 2 exata; Tema 1.390/STJ existe com a tese descrita;
   Res. CNJ 571/2024 existe; todas as URLs "estranhas" do catálogo (l8213compilado/l6404compilada/
   l7565compilado/l10.820) respondem 200.

**Fontes-chave (acessadas 2026-07-22):** planalto l8213cons.htm · l15358.htm · l15380.htm ·
l15383.htm · l15384.htm · l15402.htm · l15412.htm · l15438.htm · l15040.htm · del0911.htm ·
gov.br/susep notícia 11/12/2025 "Lei do Contrato de Seguro entra em vigor…" · stj.jus.br notícia
23/02/2026 (Tema 1.390) · noticias.stf.jus.br "Relator suspende aplicação da Lei da Dosimetria…" ·
camara.leg.br/noticias/1119630 (10/12/2024 19:34) · buscas Res. CNJ 571/2024 (IBDFAM/LegisWeb).
