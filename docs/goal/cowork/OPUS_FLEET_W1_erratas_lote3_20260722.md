# OPUS FLEET W1 — Erratas lote-3: fila de correção executável (pré-promote)

Autor: `claude-cowork-opus` (W1). Read-only sobre `data/`; nenhuma edição aplicada. Verificação viva
(WebSearch, domínios oficiais) das 3 leis/teses de 2026 que sustentam correção de conteúdo.

## SCOPE

Frontboard `erratas-lote3-hold` (P0): censo triado ~30 páginas / 7 famílias (penal, bancário, leis,
previdenciário, trabalhista, procedimentos/eleitoral, aéreo-portarias). Objetivo: emitir a fila de
correção executável e separar **errata real que bloqueia promote** de **falso-positivo de triagem**,
ANTES de promover essas páginas. O censo JÁ EXISTE (não foi preciso reconstruir).

## WHAT I READ

- `data/source-audit/cowork_poscutoff_verificacao_lote3_20260722.md` (as 10 erratas originais).
- `data/source-audit/cowork_poscutoff_verificacao_lote4_20260722.md` (errata-da-errata: censo real = 5 pgs).
- `data/source-audit/cowork_poscutoff_verificacao_lote5_20260722.md` e `cowork_claims_poscutoff_lote2_20260722.md`.
- `docs/goal/cowork/ADJUDICATION_AUDIT_20260722.md` (fiscal-do-fiscal: encolhe holds) e `PROMOTE_REDTEAM_20260722B.md`.
- `.agents/runtime/p0_frontboard.jsonl:28` (task) + `.agents/runtime/coordination/bus.jsonl` (1444-1447).
- Shards v2 reais (metadata-only): `criminal-01/04/09/11/12/13`, `bancario-inf1`, `bancario-18`,
  `leis-inf2`, `previdenciario-14`, `trabalhista-14`.

## FINDINGS

O censo original listou 10 erratas ≈ 30 páginas. A varredura página-a-página (lote-4 +
adjudicação + minha leitura dos corpos reais) colapsa quase tudo em **falso-positivo de string**.
**Erratas REAIS que bloqueiam promote = 3** (penal, bancário, leis).

Refinamento próprio (correção cruzada da errata do lote-3, item 5): verifiquei Tema 1.279/STJ ao
vivo. A tese (REsp 2.126.264, 2ª Seção, rel. Antonio Carlos Ferreira; notícia STJ 25/08/2025) fixou
SOMENTE o termo inicial dos **5 dias** (art. 3º §1º DL 911/69) a partir da execução da liminar. O
lote-3 disse que "os 15 dias seguem da juntada" — **isso não se confirma**: o art. 3º §3º do DL
911/69 conta os 15 dias de contestação também "da execução da liminar" (literal). Logo o erro real
não é o prazo em si, e sim **atribuir ao Tema 1.279 um alcance que ele não tem** ("ambos os prazos").

## EXECUTABLE CORRECTION QUEUE

Formato: `intent_id | família | erratum (verbatim curto) | texto corrigido | fonte oficial (URL + data) | bloqueia?`

**BLOQUEIAM PROMOTE (3):**

1. **`crim-quanto-cumprir-para-progredir`** (`criminal-11.jsonl:2`) — **família: penal**
   - Erratum (verbatim): *"A Lei 15.402/2026 retomou um sexto como regra geral"* — corpo trata a lei como plenamente aplicável, **sem ressalva** de suspensão pelo STF nem menção aos vetos (`RESSALVA_STF_PRESENTE=False` no corpo).
   - Texto corrigido (acrescentar após o parágrafo da 15.402): *"Ressalva obrigatória: a Lei nº 15.402/2026 (Lei da Dosimetria) é objeto das ADIs 7.966 e 7.967, ajuizadas em 8 de maio de 2026. Em 9 de maio de 2026, o ministro Alexandre de Moraes suspendeu a aplicação da lei às execuções penais dos condenados pelos atos de 8 de janeiro de 2023 que tramitam no STF, até o julgamento do mérito pelo Plenário. Além disso, dispositivos que fixariam frações específicas para crimes hediondos foram vetados e a controvérsia segue em aberto. O percentual concreto depende da data do fato, da natureza do crime e do desfecho dessas ações — não há aplicação automática."*
   - Fonte: https://noticias.stf.jus.br/postsnoticias/stf-recebe-primeiras-acoes-contra-lei-da-dosimetria/ (suspensão 09/05/2026, verificado 2026-07-22) + https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15402.htm
   - Bloqueia? **SIM** (publica execução penal desatualizada; medida do STF em vigor).

2. **`banc-fver-liminar-deferida-sem-ouvir-devedor`** (`bancario-inf1.jsonl:4`) — **família: bancário**
   - Erratum (verbatim): *"O Superior Tribunal de Justiça, ao julgar o Tema 1.279 dos recursos repetitivos, fixou que **ambos os prazos** começam a correr da execução da liminar…"* — extrapola a tese, que só tratou dos 5 dias.
   - Texto corrigido (substituir o período): *"O Superior Tribunal de Justiça, no Tema 1.279 dos recursos repetitivos (REsp 2.126.264), fixou que o prazo de cinco dias para pagamento integral, previsto no art. 3º, §1º, do Decreto-Lei 911/1969, começa a correr da execução da liminar — e não da citação. O prazo de quinze dias para contestação também se conta da execução da liminar, mas por força do próprio art. 3º, §3º, do Decreto-Lei 911/1969, e não da tese do Tema 1.279, cujo alcance se limitou ao termo inicial dos cinco dias."*
   - Fonte: https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2025/25082025-Prazo-de-cinco-dias-para-pagar-divida-fiduciaria-comeca-na-execucao-da-liminar-de-busca-e-apreensao.aspx (25/08/2025) + https://www.planalto.gov.br/ccivil_03/decreto-lei/1965-1988/del0911.htm (art. 3º §3º)
   - Bloqueia? **SIM** (afirma alcance de tese repetitiva que ela não tem — claim verificável falso sobre a decisão).

3. **`lei-maria-da-penha`** (`leis-inf2.jsonl:8`) — **família: leis**
   - Erratum (verbatim): *"a Lei nº 15.384/2026, que passou a prever a violência vicária … e reforços que dão às medidas protetivas de natureza cível força de título executivo"* — o efeito de título executivo é da **Lei 15.412/2026**, não da 15.384; a 15.412 nunca é citada, e a 15.384 não está em `official_sources`.
   - Texto corrigido: *"A Lei nº 15.384/2026 passou a prever a violência vicária como forma de violência doméstica. Já a Lei nº 15.412/2026 incluiu o §10 no art. 22 da Lei nº 11.340/2006, estabelecendo que as medidas protetivas de natureza cível — inclusive alimentos provisórios ou provisionais — constituem título executivo judicial de pleno direito, dispensando o ajuizamento de ação principal."* + adicionar a `official_sources`: `l15412.htm` e `l15384.htm`.
   - Fonte: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15412.htm (§10 art. 22, verificado 2026-07-22) + https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15384.htm
   - Bloqueia? **SIM** (efeito jurídico real sem proveniência + atribuído à lei errada — viola regra de fonte).

**FALSO-POSITIVO / NÃO BLOQUEIA (disposição das ~27 páginas restantes das 7 famílias):**

| censo item / tema | páginas triadas | veredito | ação |
|---|---|---|---|
| 1. Lei 15.438/2026 "12 meses" (penal) | crim-fui-vitima-estelionato, crim-golpe-pix, crim-golpe-do-amor (criminal-01), crim-decadencia-e-prescricao (criminal-09), crim-acao-penal-condicionada (criminal-04-real), crim-representar-prazo-decadencial (criminal-13) — ~6 | **CORRETAS**: todas restringem os 12 meses a "violência doméstica e familiar contra a mulher" e mantêm 6 meses como regra geral (art. 103 CP) | nenhuma; sair do hold |
| 5. Tema 1.279 (bancário) — demais | banc-fver-leasing-reintegracao-posse-diferenca, banc-fver-recompra-veiculo (bancario-inf1), transito-r01 ×2 | **CORRETAS** (não atribuem ao Tema 1.279; prazos batem com DL 911) | nenhuma |
| 6/MP 1.355 + MP 1.331 (bancário) | banc-fgts-saque-aniversario-...-fintech-riscos (bancario-18:20) | **HISTORICIZADA OK**: "pagamentos concluídos até 1º/06/2026", "não muda demissões futuras" (MP 1.331 caducou 01/06/2026) | nenhuma (adjudicação confirma) |
| 3. TSE 23.751 (eleitoral/proced.) | procedimentos-12:11,14 | **CORRETAS** (uso p/ atos gerais: local de votação/e-Título; propaganda cita 23.610/2019) | nenhuma |
| 10. Tema 1.124 (proced./imobiliário) | imobiliario-09, procedimentos-14 | **CORRETAS** (tratam STF 1.124 como "pendente"; sem tese vigente citada) | nenhuma |
| 4. "Portaria ANAC 1/2026" (aéreo) | aereo-01 ×2 | **CORRETAS**: Portaria Reg. 1/SAS EXISTE (ANAC Passageiro) — errata-da-errata lote-4; power banks = Portaria Reg. 21 já citada | nenhuma |
| 7/8/9. Portarias 76/2025, 13/2026, IN 138/128 (prev.) | 0 páginas casadas | **SEM PÁGINA** que erre a descrição (76 já = biometria) | nenhuma |
| Lei 15.371 paternidade (prev./trab.) | prev-maternidade-homem (previdenciario-14:7), trab-licenca-paternidade (trabalhista-14:12) | **RESSALVA JÁ PRESENTE** ("entra em vigor em 1º/01/2027"; `tem_ressalva_2027=True`) | nenhuma |
| MP 1.355 string-match | 14 hits | **falso-positivo** (maioria = CC art. 1.331 condomínio) | nenhuma |

Nota adjacente (fora do lote-3, não incluída na contagem): `seg-empresarial-do-defesa-multa`
(codex-autonomos-seguros-r16) cita "art. 10, I/II" da Lei 15.040 — deve ser "art. 10, **parágrafo
único**, I/II" (lote-5; bug recorrente ~244 pgs de seguros). Encaminhar à fila de seguros.

## VERIFICATION EVIDENCE

- **Lei 15.402/2026 (Dosimetria)** — CONFIRMADA ao vivo. ADIs 7.966/7.967 protocoladas 08/05/2026
  (ABI e PSOL-Rede); Moraes suspendeu 09/05/2026 a aplicação às execuções dos condenados do 8/1 até
  o Plenário; caput retomou 1/6 como regra geral. (noticias.stf.jus.br; planalto l15402.htm.)
- **Tema 1.279/STJ** — CONFIRMADO. REsp 2.126.264, 2ª Seção, rel. Antonio Carlos Ferreira: os 5 dias
  do art. 3º §1º DL 911/69 correm da execução da liminar. A tese **não** alcança os 15 dias
  (art. 3º §3º), que já correm da execução por texto legal expresso. (stj.jus.br notícia 25/08/2025.)
- **Lei 15.412/2026** — CONFIRMADA. Incluiu §10 no art. 22 da Lei 11.340/2006: medidas protetivas
  cíveis (inclusive alimentos provisórios/provisionais) = título executivo judicial de pleno direito,
  dispensando ação principal. Pacote "Maria da Penha 2026" (15.409/15.411/15.412). 15.384/2026 =
  violência vicária (distinta). (planalto l15412.htm; l15384.htm.)
- **Lei 15.438/2026** — os 12 meses valem só p/ violência doméstica/familiar contra a mulher; regra
  geral segue 6 meses (art. 103 CP). Todas as páginas do estoque já aplicam o recorte (lido nos corpos).

## COLLISION-SAFETY NOTE

Trabalho 100% read-only: nenhuma edição em `data/editorial/`, `data/ops/`, `v2ingest.go`,
`validate.go`; nenhum `git add/commit`. Fonte usada como proveniência, nunca corpo. As 3 correções
são **executáveis pela fila de revisão** (não aplicadas aqui) — cada uma nomeia o campo (sec/`official_sources`),
o texto novo e a URL oficial + data. Esta é a única saída via Write, no path designado. As páginas
das 3 erratas devem permanecer no `erratas-lote3-hold` até a fila de revisão aplicar o fix; as demais
~27 páginas triadas podem sair do hold (falso-positivo confirmado por leitura do corpo real).
