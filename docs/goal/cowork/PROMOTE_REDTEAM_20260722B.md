# PROMOTE_REDTEAM_20260722B — 2ª rodada adversarial pré-promote (Cowork Fable 5)

Amostra: 14 páginas ACEITAS no dry-run, 14 áreas distintas (10 comerciais + 4 informativas),
seed determinístico 20260722B (log de sorteio em `data/ops/cowork_redteam_sample_20260722B.txt`).
Leitura INTEGRAL dos 14 corpos pelo orquestrador Fable.

## Verdict: 11/14 APTAS COMO ESTÃO; 3 correções de corpo + 3 pontuais. NENHUM bloqueio estrutural.

Qualidade geral ALTA e ATUAL: Lei 15.040 art. 124 (proteção 10 anos) correta e sofisticada;
EC 103 art. 24 com faixas explicadas certo (incidência por trecho, não percentual único); RGST
777/2025 com faseamento 09/2027; Súmula 308 já incorporando as decisões da Quarta Turma de
2025/jun-2026; REsp 1.843.507 incidental correto; zero invenção detectada; zero molde entre as 14;
ética OAB impecável nos fechos ("sem prometer", "não torna automático").

## Fila de correção (para writing-review)

1. **`prev-acumular-pensao-aposentadoria`** (previdenciario-12): comercial SEM sinal de contratação
   no corpo → reprovaria `paid_intent_blocked_cta_only_paid_signal`. Fix: inserir 1 frase sóbria de
   revisão particular da memória de cálculo (a seção "Como auditar a memória de cálculo" é o slot
   natural). Conteúdo jurídico: correto.
2. **`pi-acao-nulidade-patente`** (inpi-08): idem — comercial sem sinal no corpo. Slot natural:
   seção final de decisão entre vias. Conteúdo: correto.
3. **`dig-remocao-expedita-video-intimo`** (digital-07): comercial sem sinal no corpo — MAS tema é
   vítima de conteúdo íntimo: sinal comercial agressivo seria risco ético. RECOMENDAÇÃO: ou
   reclassificar lane→informativa, ou sinal mínimo ("advogado particular pode conduzir notificação
   e tutela de urgência com sigilo"). ADICIONALMENTE: a anchor_claim da fonte STF repete o rótulo
   impreciso "vale desde 05/08/2025" — corrigir para "publicação da ata do julgamento de mérito"
   (mesma errata da verificação Tema 987; mérito julgado 26/06/2025).
4. **`proc-enotariado-inventario-online`** (procedimentos-17): opening cita "Resolução CNJ 571/2024"
   SEM entrada correspondente em official_sources (âncoras são Res. 35 e CNN arts. 284-319).
   Fix: adicionar fonte da Res. 571/2024 (atos.cnj.jus.br) ou reancorar a frase nos arts. 12-A/12-B.
5. **`tel-portabilidade-fixo-para-movel`** (telecom_energia-15): última frase "O conteúdo é
   informativo e não promove atendimento particular" é META-DISCURSO editorial vazando para texto
   público (vocabulário interno de lane). Remover/reescrever. Varredura recomendada: grep
   "conteúdo é informativo" no estoque — se repetir em N páginas, é molde-disclaimer a extinguir
   via fila (vi variação também em cons-cobranca na amostra A).
6. Menor: `prev-acumular` fonte 3 é informe ministerial de dez/2019 (síntese) — aceitável, mas
   trocar por página atual gov.br/previdencia de acumulação quando conveniente.

## Nota de gate

`paid_signal` mecânico: 10/10 comerciais têm title/meta ok; 7/10 têm sinal no corpo. As 4
informativas estão limpas de CTA/sinal (correto). Nenhuma das 14 contém promessa de resultado,
preço ou captação. Recomendo cohort-1 prosseguir com as 3 páginas acima indo para revisão em vez
de compor o primeiro lote.
