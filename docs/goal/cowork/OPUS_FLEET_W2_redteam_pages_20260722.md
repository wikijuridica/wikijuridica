# OPUS_FLEET_W2 — Red-team adversarial de páginas v2 pré-promote (cohort-1)

Autor: `claude-cowork-opus-w2` (Opus 4.8, red-team jurídico adversarial). Data: 2026-07-22.
Método: leitura humana-adversarial integral de amostra estratificada + verificação AO VIVO
(WebSearch/oficial) de cada citação falsificável + varredura sistemática das 5 famílias cohort
(1.904 páginas). READ-ONLY. Complementa `PROMOTE_REDTEAM_20260722`/`B` e
`cowork_tema987_verificacao_20260722.md` (não duplica os intents já cobertos lá).

## SCOPE
- Alvo: páginas v2 perto de promote das 5 famílias elegíveis a cohort — **consumidor, bancário,
  trabalhista, sucessões, previdenciário** — priorizando as que citam lei/artigo/prazo/valor
  específico, súmula, tema de repetitivo/repercussão geral.
- Caça a 7 classes de blocker: (1) lei/artigo/prazo/valor errado ou desatualizado; (2) nº de
  tema/súmula/RE/REsp errado; (3) PT-BR truncado/conectivo/molde; (4) paid_intent só no CTA;
  (5) lane errada (BPC/LOAS/gratuidade com CTA comercial); (6) fonte homepage/genérica; (7) FAQ
  juridicamente incorreta.
- Verificado AO VIVO (não apenas check): 12+ citações-âncora em domínios oficiais/imprensa jurídica.

## AMOSTRA (16 páginas lidas na íntegra + varredura de 1.904)
prev: `prev-revisao-vida-toda-situacao`, `prev-especial-ruido`, `prev-beneficio-penhorado-divida`,
`prev-ir-isencao-doenca-grave-quais-doencas`, `prev-rural-boia-fria`.
trab: `trab-terceirizacao-atividade-fim`, `trab-pdv-quitacao`, `trab-reflexos-horas-extras`.
banc: `banc-atraso-financiamento-imovel-o-que-acontece`, `banc-cheque-prescrito-ainda-pode-ser-cobrado`,
`banc-med-devolucao-parcial-saldo-insuficiente`, `banc-whatsapp-clonado-pedindo-dinheiro`.
suc: `suc-companheiro-concorre-filhos-hibrida`. cons: `cons-crianca-comprou-no-aplicativo-sem-autorizacao`,
`cons-prestador-desistiu-sinal-em-dobro`, `cons-corpo-estranho-na-comida`.
+ cluster Tema 987 (27 páginas escaneadas) e varredura de lane/truncamento/leak/fonte nas 5 famílias.

## DEFEITOS (tabela)
| # | intent_id | tipo | severidade | bloqueia promote? |
|---|-----------|------|-----------|-------------------|
| D1 | `prev-ir-isencao-doenca-grave-quais-doencas` (previdenciario-r02) | lista taxativa de lei INCOMPLETA (omite doença) | média | SIM — a página É a lista |
| D2 | cluster: 233 páginas lane `comercial` (prev 131, banc 50, cons 25, trab 17, suc 10) | paid_intent sem sinal de contratação no corpo | média | SIM (gate `missing_paid_signal`/`cta_only`) — mas heterogêneo |
| D3 | `suc-consignado-morte` (sucessoes-13), `suc-espolio-declaracao-ir-anual` (sucessoes2-02) | registro skip-stub sem conteúdo/fonte | baixa | N/A — já excluídos (needs_source_research) |
| S1 | `cons-crianca-comprou-no-aplicativo` | fonte genérica (consumidor.gov.br landing) 1 de 4 | soft | NÃO (3 deep-links CC) |
| S2 | `trab-pdv-quitacao` | fonte TRT6 (tema) em vez de deep-link STF | soft | NÃO (fonte oficial válida) |

Nenhum defeito das classes (1) lei/tema/súmula/RE/REsp ERRADO, (3) truncamento/molde real,
(5) lane BPC/LOAS comercial, (7) FAQ incorreta foi encontrado na amostra. Varredura: **0** lane-errors
assistência+comercial; **0** truncamentos reais (12 falsos-positivos = itens de bullet-list); **0**
leaks de jargão editorial (rascunho/seed/CTA/noindex/TODO); **0** páginas sem fonte além dos 2 stubs.

## FIX DETAILS
**D1 — `prev-ir-isencao-doenca-grave-quais-doencas`, seção S0 "A lista é definida em lei".**
- Trecho VERBATIM: *"A norma menciona moléstia profissional, tuberculose ativa, alienação mental,
  esclerose múltipla, neoplasia maligna, cegueira, hanseníase, paralisia irreversível e
  incapacitante, cardiopatia grave, Parkinson, espondiloartrose anquilosante, nefropatia grave,
  hepatopatia grave, estágio avançado de Paget, contaminação por radiação e síndrome da
  imunodeficiência adquirida."*
- Defeito: o rol do **art. 6º, XIV, da Lei 7.713/1988 é TAXATIVO** (jurisprudência STJ) e inclui
  **fibrose cística (mucoviscidose)** (incluída pela Lei 8.541/1992). A página enumera 16 moléstias
  e OMITE a fibrose cística, apresentando a lista como "definida em lei" — um leitor portador dessa
  doença é induzido a concluir, erradamente, que não se enquadra. Em rol taxativo a completude importa.
- Correção exata: acrescentar "**, fibrose cística (mucoviscidose)**" ao final da enumeração (antes de
  "e síndrome da imunodeficiência adquirida").
- Fonte oficial: Planalto, Lei 7.713/1988 art. 6º XIV — https://www.planalto.gov.br/ccivil_03/leis/l7713.htm
  (verificado ao vivo 2026-07-22; inclusão da fibrose cística pela Lei 8.541/1992, art. 47).

**D2 — cluster paid_intent-thin (233 páginas comerciais).** O gate `paidintent`
(`internal/paidintent/paidintent.go`, lista de sinais-core: "advogado particular", "contratar
advogado/advogada", "honorários"+oferta) exige sinal de contratação NO CORPO para lane comercial;
sem ele → `paid_intent_blocked_missing_paid_signal`/`cta_only_paid_signal`. Exemplos reais lidos
(fecham em autotutela/juizado, sem pitch de contratação):
- `cons-produto-vencido-no-mercado`: *"...possibilidade de indenização além da simples reposição do
  item — cenário em que vale reunir também atendimento médico e demais provas do dano..."* (sem sinal).
- `cons-carro-danificado-no-estacionamento`: fecha em exemplo de auto-resolução ("obteve do shopping o
  ressarcimento"), sem contratação.
- Correção exata (por página): OU (a) acrescentar 1 frase de intenção de contratação particular no
  corpo (padrão da casa: "um advogado particular pode analisar remotamente ... por WhatsApp/envio
  digital"), OU (b) re-lane para `informativa` quando o tema não sustenta contratação (ex.: episódios
  de baixo valor resolvidos por SAC/vigilância sanitária). NOTA: parte do cluster tem sinal SOFT
  (WhatsApp/remoto sem a palavra "advogado", ex. `cons-produto-trocado-veio-com-defeito-novamente`) e
  pode passar — a decisão final é por página, pelo próprio gate; não é erro jurídico, é ajuste de
  lane/sinal e yield. Este é o principal gargalo de promoção do cohort comercial, não um defeito que
  "vaza" (o gate segura).

**D3 — 2 skip-stubs sucessões.** `suc-consignado-morte` (skip_reason: jurisprudência STJ pendente) e
`suc-espolio-declaracao-ir-anual` (skip_reason: falta fonte RF específica). Corretos como excluídos;
apenas garantir que o gerador do shard não os conte no denominador cohort. Sem ação de conteúdo.

## FALSOS-POSITIVOS EVITADOS (conteúdo sofisticado CONFIRMADO correto — NÃO sinalizar)
Verificados ao vivo e mantidos:
- `prev-revisao-vida-toda-situacao`: reflete CORRETAMENTE a virada de 2024 (ADIs 2110/2111, art. 3º
  cogente) e a modulação — valores recebidos até **05/04/2024** irrepetíveis ✓ (confirmado ao vivo).
- `trab-terceirizacao-atividade-fim`: Tema 725/ADPF 324/RE 958.252 (atividade-fim lícita) + pejotização
  no **Tema 1389 do STF** (ARE 1.532.603, suspensão nacional abr/2025) ✓ — atualíssimo, correto.
- `suc-companheiro-concorre-filhos-hibrida`: **REsp 1.617.650-RS, Informativo 651**, art. 1.832 CC —
  reserva de 1/4 AFASTADA na filiação híbrida ✓ (bate exatamente com o julgado, 3ª Turma, 11/06/2019).
- `banc-atraso-financiamento-imovel`: art. 26-A Lei 9.514/1997 (Lei 14.711/2023) — averbação da
  consolidação **30 dias** após a intimação ✓; leilões 60/15 dias, art. 27 §4º 5 dias ✓.
- `prev-beneficio-penhorado-divida`: **Tema 1230 STJ EM JULGAMENTO** (art. 833 §2º CPC, dívida não
  alimentar < 50 SM), EREsp 1.874.222 Corte Especial ✓ — enquadramento cauteloso correto.
- `prev-especial-ruido`: limites 80/90/85 dB por período ✓, **Tema 1083 STJ** (NEN/pico + perícia) ✓,
  Tema 694 ✓, Tema 555 STF (EPI não descaracteriza ruído) ✓.
- `banc-cheque-prescrito`: art. 33 (30/60 dias), art. 59 (6 meses), art. 61 (2 anos) Lei 7.357/85 ✓,
  **Súmula 503** (monitória 5 anos) e **531 STJ** ✓.
- Cluster **Tema 987** (27 páginas): "efeitos desde 5 de agosto de 2025" está CORRETO — as páginas o
  rotulam como "publicação da ata do julgamento de mérito" (mérito julgado 26/06/2025); nenhuma comete
  o erro de chamá-lo de "data do julgamento" ✓ (confere com `cowork_tema987_verificacao_20260722.md`).
- `trab-reflexos-horas-extras`: revisão da OJ 394 TST (efeitos 20/03/2023), Súmulas 45/63/172/347 ✓.
- `trab-pdv-quitacao`: RE 590415/Tema 152 + art. 477-B CLT ✓. `cons-crianca-comprou`: art. 3/4/166/
  171/178/180 CC ✓. `cons-prestador-sinal-dobro`: arras art. 418-420 CC + art. 35 CDC ✓.
- (Lembrete do estoque: caso art. 59 §§2-5 L8213 era lei vigente — mesma disciplina aqui: não sinalizar
  conteúdo correto e atual.)

## COLLISION-SAFETY
READ-ONLY integral. Nenhuma edição em `data/editorial/`, `data/ops/`, `validate.go`, `v2ingest.go`.
Nenhum git, build Go ou suíte global. Apenas Grep/Read/python3 read-only + WebSearch + 1 leitura de
`internal/paidintent/paidintent.go`. Escrita única: este arquivo. As correções D1/D2 são para a fila
de revisão editorial executá-las pelo gerador correspondente (nunca edição manual do JSONL).

## Resumo final
- **Amostradas:** 16 páginas lidas na íntegra (5 famílias cohort) + varredura sistemática de 1.904
  páginas + verificação ao vivo de 12+ citações-âncora + cluster Tema 987 (27 páginas).
- **Defeitos REAIS:** 1 de conteúdo (D1: lista taxativa da Lei 7.713/88 omite fibrose cística) +
  1 cluster de lane/paid-signal (D2: 233 páginas comerciais sem sinal de contratação no corpo) +
  2 skip-stubs (D3, sem ação).
- **Bloqueiam promote:** D1 (1 página, fix de 1 linha) e D2 (gate paid_intent segura o cohort comercial
  até re-lane/sinal — o maior gargalo de yield, não um vazamento). Zero erro de lei/tema/súmula/RE/REsp,
  zero truncamento/molde, zero lane BPC comercial, zero FAQ incorreta na amostra: o estoque jurídico é
  excepcionalmente preciso e atual (2024–2026 corretamente refletidos).
- Path: `/opt/wiki/docs/goal/cowork/OPUS_FLEET_W2_redteam_pages_20260722.md`
