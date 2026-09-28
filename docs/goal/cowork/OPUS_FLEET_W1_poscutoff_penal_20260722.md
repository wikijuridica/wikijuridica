# OPUS FLEET W1 — Verificação pós-cutoff / leis penais 2026 (pre-promote HOLD/CLEAR)

Frontboard task: `poscutoff-alto-risco-penal` (P0, BLOQUEIO pre-promote)
Auditor: Opus 4.8 (Cowork W1) — 2026-07-22 — READ-ONLY, um único arquivo escrito.
Cutoff do modelo: jan/2026 → leis de 2026 são genuinamente pós-cutoff e foram verificadas AO VIVO em fonte oficial.

## SCOPE
- Alvo: toda página v2 (`data/editorial/v2_pages/*.jsonl`) que cita lei federal de 2026 no escopo PENAL/criminal, incluindo o cluster Maria da Penha (crimes de VD/F contra a mulher).
- Leis nomeadas na task: **15.402, 15.358, 15.438**. A varredura ampliou o alvo e achou **6** leis penais de 2026 citadas: **15.358, 15.380, 15.383, 15.384, 15.402, 15.438**.
- Objetivo: para cada (página × lei), decidir CLEAR / HOLD / FIX antes do promote, com URL oficial + data e correção executável quando aplicável.
- Fora do escopo penal (listadas no fim, sem verificação minha → default HOLD do respectivo vertical): 15.327, 15.348, 15.352, 15.363, 15.371, 15.378, 15.415, 15.428 e 15.321/2025.

## WHAT I READ
Repo (read-only, grep/python):
- Varredura `data/editorial/v2_pages/*.jsonl` p/ `15\.\d{3}` (todos os nºs de lei 15.xxx) e extração intent_id + frase verbatim por ocorrência.
- Shards penais: `criminal-01.jsonl`, `criminal-04.jsonl`, `criminal-09.jsonl`, `criminal-11.jsonl`, `criminal-13.jsonl`, `criminal-16.jsonl`, `familia-16.jsonl`, `leis-inf2.jsonl`.
Fontes oficiais AO VIVO (Planalto/Câmara/Senado), buscadas só em domínios .gov/.leg/.jus:
- Planalto l15358, l15380, l15383, l15384, l15402, l15438 (textos promulgados) + l7210 (LEP consolidada) + www2.camara.leg.br (15.358) + www12.senado.leg.br (nota Antifacção). URLs completas na seção VERIFICATION EVIDENCE.

## FINDINGS
- **Nenhuma lei penal inventada.** As 6 leis de 2026 citadas EXISTEM e o conteúdo atribuído bate com o texto oficial promulgado. Isso é o resultado forte deste gate: as páginas não alucinaram lei/artigo/data.
- **20 páginas penais** citam essas leis (22 pares página×lei). **19 CLEAR, 1 HOLD, 0 FIX.**
- **Único HOLD:** `crim-quanto-cumprir-para-progredir` (criminal-11) — cita 15.358 (marcos 70/75/80/85% do art. 112 LEP) E 15.402 (que "voltou a alterar" o art. 112 em 08/05/2026, com incisos IV–X **VETADOS**). Duas leis reescrevem o MESMO art. 112 em 6 semanas; não foi possível confirmar positivamente, na LEP consolidada do Planalto (fetch de hoje veio sem o corpo dos incisos), que os marcos 70–85% seguem vigentes após a 15.402. É risco de vigência/currency, não de lei falsa → HOLD até reconciliação.
- Confirmações-chave verbatim: 15.402 acrescentou **§ 9º ao art. 126 LEP** ("regime domiciliar não impede remição") — bate; 15.358 reescreveu **art. 310 CPP** (custódia por videoconferência em tempo real, presencial só por força maior/decisão justificada) e **art. 313, V, CPP** (preventiva p/ integrante de org. criminosa ultraviolenta/paramilitar/milícia) — batem; 15.438 alterou **CP art. 103 p.ú., CPP art. 38 §2º e LMP art. 16-A** (prazo decadencial de 12 meses em VD/F) — bate; 15.380 alterou **LMP art. 16 p.ú.** (audiência de retratação só a pedido expresso, antes do recebimento da denúncia) — bate; 15.383 (**LMP art. 12-D/22 VIII/24-A §4º**, monitoração autônoma + aumento 1/3 a 1/2) e 15.384 (**LMP art. 7º VI + CP art. 121-B vicaricídio + L8072 I-C**, violência vicária) — batem.

## EXECUTABLE QUEUE (promote-hold/clear)
Formato: intent_id | shard | Lei | claim (verbatim curto) | VERDICT | fonte oficial + data | correção

| intent_id | shard | Lei | claim (curto) | VERDICT | fonte oficial + data |
|---|---|---|---|---|---|
| crim-fui-vitima-estelionato | criminal-01 | 15.438/2026 | "prazo de doze meses para queixa ou representação" em VD/F | CLEAR | Planalto l15438, 18/06/2026 (DOU 19.6) |
| crim-golpe-pix-como-denunciar | criminal-01 | 15.438/2026 | "estendeu para doze meses a janela de queixa ou representação" em VD/F | CLEAR | Planalto l15438, 18/06/2026 |
| crim-golpe-do-amor-como-agir | criminal-01 | 15.438/2026 | "o prazo passa a doze meses quando configurar violência doméstica" | CLEAR | Planalto l15438, 18/06/2026 |
| crim-acao-penal-condicionada-ou-incondicionada | criminal-09 | 15.438/2026 | "ampliou esse prazo... doze meses para representar ou apresentar queixa" | CLEAR | Planalto l15438, 18/06/2026 |
| crim-representar-prazo-decadencial | criminal-13 | 15.438/2026 | "acrescentou regra específica ao CP, ao CPP e à Lei Maria da Penha" | CLEAR | Planalto l15438 (CP 103 p.ú., CPP 38 §2º, LMP 16-A) |
| fam-crime-perseguicao-stalking | familia-16 | 15.438/2026 | "doze meses, contados do dia em que soube quem é o autor" | CLEAR | Planalto l15438, 18/06/2026 |
| crim-familiar-preso-em-flagrante | criminal-04 | 15.358/2026 | "regra legal é a videoconferência em tempo real; presencial só em força maior, decisão justificada" | CLEAR | Planalto l15358 art.310 CPP, 24/03/2026 |
| crim-defesa-audiencia-de-custodia | criminal-04 | 15.358/2026 | "art. 310 do CPP... em até 24 horas e, como regra, por videoconferência em tempo real" | CLEAR | Planalto l15358 art.310 CPP, 24/03/2026 |
| crim-preventiva-quando-pode-ser-decretada | criminal-04 | 15.358/2026 | "inciso V também alcança crime de integrante de org. criminosa ultraviolenta, grupo paramilitar ou milícia" | CLEAR | Planalto l15358 art.313 V CPP, 24/03/2026 |
| crim-quanto-cumprir-para-progredir | criminal-11 | 15.358/2026 | "elevou marcos hediondos: 70% primário; 75% inc.VI; 80% reincidente; 85% reincidente c/ morte" | **HOLD** | Planalto l15358 art.112 V-VIII LEP, 24/03/2026 |
| crim-quanto-cumprir-para-progredir | criminal-11 | 15.402/2026 | "Em 8 de maio de 2026, a Lei 15.402 voltou a alterar profundamente o art. 112" | **HOLD** | Planalto l15402, 08/05/2026 (IV-X VETADOS) |
| crim-livramento-condicional | criminal-11 | 15.358/2026 | "Atualizou os marcos dos hediondos e as vedações expressas ao livramento" | CLEAR | Planalto l15358 art.112 VI-b/VIII LEP, 24/03/2026 |
| crim-livramento-ou-progressao | criminal-11 | 15.402/2026 | "requisito temporal... hoje alterado pela Lei 15.402/2026" | CLEAR | Planalto l15402 art.112 LEP, 08/05/2026 |
| crim-remicao-de-pena | criminal-11 | 15.402/2026 | "acrescentou o § 9º ao art. 126... regime domiciliar não impede remição desde maio/2026" | CLEAR | Planalto l15402 art.126 §9º LEP, 08/05/2026 |
| crim-retratar-representacao | criminal-13 | 15.380/2026 | "audiência confirma a retratação e só é marcada por manifestação expressa, antes daquele marco" | CLEAR | Planalto l15380 art.16 p.ú. LMP, 06/04/2026 |
| crim-lesao-domestica-precisa-representacao | criminal-16 | 15.380/2026 | "audiência só pode ser marcada após pedido expresso da ofendida, escrito ou oral" | CLEAR | Planalto l15380 art.16 p.ú. LMP, 06/04/2026 |
| crim-quais-situacoes-maria-da-penha | criminal-16 | 15.384/2026 | "violência vicária... exige a finalidade de atingir a mulher" | CLEAR | Planalto l15384 art.7º VI LMP, 09/04/2026 |
| fam-violencia-vicaria | familia-16 | 15.384/2026 | "acrescentou o inciso VI ao art. 7º [LMP]" | CLEAR | Planalto l15384, 09/04/2026 |
| lei-maria-da-penha | leis-inf2 | 15.384/2026 | "passou a prever a violência vicária como forma de violência doméstica" | CLEAR | Planalto l15384, 09/04/2026 |
| crim-como-pedir-medida-protetiva | criminal-16 | 15.383/2026 | "monitoração eletrônica como medida autônoma, zonas de exclusão, alertas à vítima" | CLEAR | Planalto l15383 art.12-D/22 VIII LMP, 09/04/2026 |
| crim-descumprir-medida-protetiva | criminal-16 | 15.383/2026 | "aumento de um terço à metade ao violar zona de exclusão / remover o dispositivo" | CLEAR | Planalto l15383 art.24-A §4º LMP, 09/04/2026 |
| lei-maria-da-penha | leis-inf2 | 15.383/2026 | "acrescentou um oitavo inciso ao art. 22" (Lei de 09/04/2026) | CLEAR | Planalto l15383 art.22 VIII LMP, 09/04/2026 |

### Ação executável do único HOLD
- Página: `crim-quanto-cumprir-para-progredir` (criminal-11.jsonl). Ambas as leis são REAIS; NÃO reescrever como erro de lei.
- Correção antes do promote: (1) abrir o art. 112 da LEP CONSOLIDADA no Planalto (https://www.planalto.gov.br/ccivil_03/leis/l7210.htm#art112) e confirmar se os incisos V–VIII (70/75/80/85%) da Lei 15.358 permanecem vigentes após a Lei 15.402/2026 (cujo texto lista incisos IV–X como VETADO e dá nova redação ao caput + I–III: 25%/30%/20% por violência/grave ameaça). (2) No corpo, atribuir explicitamente cada marco à sua lei e datar ("marcos de hediondo: Lei 15.358/2026; nova redação de caput/incisos I–III e regime domiciliar/remição: Lei 15.402/2026, promulgada sobre veto"). (3) Só liberar CLEAR após a confirmação do texto consolidado em vigor na data de publicação. Manter registro de proveniência (URL + data + hash) no `official_sources`.

## VERIFICATION EVIDENCE (fontes oficiais + datas)
- Lei 15.358, de 24/03/2026 (Lei Antifacção; DOU 25.3.2026) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15358.htm | corrobora: https://www2.camara.leg.br/legin/fed/lei/2026/lei-15358-24-marco-2026-798846-norma-pl.html | https://www12.senado.leg.br/noticias/materias/2026/03/25/lei-antifaccao-de-combate-ao-crime-organizado-entra-em-vigor . Verificado: art. 310 CPP (custódia por videoconferência, presencial só força maior), art. 313 V CPP (preventiva p/ facção), art. 112 LEP V-VIII = 70/75/80/85% c/ vedação de livramento em VI-b e VIII.
- Lei 15.380, de 06/04/2026 (DOU 7.4.2026) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15380.htm . Verificado: LMP art. 16, parágrafo único (audiência de retratação só mediante manifestação expressa, escrita/oral, antes do recebimento da denúncia).
- Lei 15.383, de 09/04/2026 (DOU 10.4.2026) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15383.htm . Verificado: LMP art. 12-D (monitoração autônoma), art. 22 VIII + §§6º-9º (app de alerta, áreas de exclusão), art. 24-A §4º (aumento 1/3 a 1/2).
- Lei 15.384, de 09/04/2026 (DOU 10.4.2026, ret. 15.4.2026) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15384.htm . Verificado: LMP art. 7º VI (violência vicária), CP art. 121-B (vicaricídio, 20-40 anos), L8072 art. 1º I-C (hediondo).
- Lei 15.402, de 08/05/2026 (DOU 8.5.2026 - Ed. extra; promulgada pelo Presidente do Senado sobre veto total ao PL 2.162/2023) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15402.htm . Verificado: LEP art. 112 (nova redação caput + I-III; IV-X VETADOS), art. 126 §9º (remição em regime domiciliar), CP arts. 359-M-A/359-M-B.
- Lei 15.438, de 18/06/2026 (DOU 19.6.2026) — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15438.htm . Verificado: CP art. 103 p.ú., LMP art. 16-A, CPP art. 38 §2º (decadência de 12 meses em VD/F contra a mulher).
- LEP consolidada (checagem de vigência) — https://www.planalto.gov.br/ccivil_03/leis/l7210.htm . Observação: confirma alterações da Lei 15.358 (ex.: art. 35, monitoramento) e o §3º do art. 112; o corpo dos incisos do art. 112 não veio legível no fetch → base do HOLD acima.

## Fora do escopo penal (não verificadas por mim — HOLD do vertical dono até verificação)
Existência NÃO confirmada nesta task; encaminhar à onda do vertical antes de promover:
- 15.352/2026 (ANPD→agência): `glossario2-14` (gloss-encarregado-dpo, gloss-anpd), `leis-inf2` (lei-geral-protecao-dados) → LGPD/digital.
- 15.415/2026 (salário-maternidade 30 dias) e 15.371/2026 (salário-paternidade, vigência 2027): `previdenciario-14`, `trabalhista-14` → previdenciário/trabalhista.
- 15.363/2026 (contagem recíproca/multa): `previdenciario-18`. 15.327/2026 (mensalidades associativas INSS): `previdenciario-r02`, `procedimentos-r01` → previdenciário.
- 15.428/2026 (renovação CNH/exame): `procedimentos-09`, `transito-02` → trânsito. 15.348/2026 (vale-gás): `procedimentos-15` → consumidor.
- 15.378/2026 (Estatuto dos Direitos do Paciente): `saude-r10` → saúde. 15.321/**2025** (Selic): `sumulas-07` → tributário (é 2025, não 2026).
- Falsos positivos numéricos (NÃO são leis, sem impacto): `15.575` em `imobiliario-p4` (contexto art. 26 CDC) e `15.632` em `imobiliario-06` (é "REsp 1.815.632", nº de recurso do STJ).

## COLLISION-SAFETY NOTE
- READ-ONLY confirmado. NÃO editei nada em `data/editorial/`, `data/ops/`, `v2ingest.go`, `validate.go`. Nenhum `git add/commit/reset/checkout/restore`. Nenhum `go build ./...`, suíte de checks ou lab-cycle. Só grep/Read e python3 focado (extração e listagem), além de WebSearch/web_fetch em domínios oficiais.
- Escrevi EXATAMENTE UM arquivo: `/opt/wiki/docs/goal/cowork/OPUS_FLEET_W1_poscutoff_penal_20260722.md`. Nenhum outro arquivo criado/alterado.
