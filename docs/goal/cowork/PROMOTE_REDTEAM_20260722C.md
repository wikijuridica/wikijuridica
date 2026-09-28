# PROMOTE RED-TEAM — seed C (2026-07-22, run v2-ingest-20260722T140000Z)

Autor: `claude-cowork-fable`. Amostra determinística sha256(intent_id), 14 páginas, 3 buckets SEM overlap com seeds A/B: shards tocados hoje fora do reconcile (B1), reconciliadas (B2), famílias inéditas nos seeds (B3: aereo, cidadania, constitucional, educacao). Registros lidos INTEGRAIS.

## VEREDITO GLOBAL: APTO-COM-FILA

Zero invenção de lei/decisão/citação nas 14 (2 claims pós-2024 mais carregados re-verificados AO VIVO: Lei 15.270/2025 e Tema 1.240/STF — ambos corretos). Titles 14/14 em 20–65; metas 14/14 em 70–160; aberturas 14/14 distintas, cenário concreto. Utilidade forte e uniforme.

## Amostra (defeitos apenas; 7/14 OK sem ressalva)

| página (shard) | defeito |
|---|---|
| trib-iptu-revisao-valor-venal (codex-educacao-tributario-r19) | “Este guia é informativo.” — meta-discurso + contradiz sinal pago na mesma frase |
| banc-cartao-seguro-servico-embutido-fatura (bancario-r03) | paid-signal genérico (fecho “advogado… sem prometer”), sem “particular” |
| trib-cnd-financiamento-imobiliario-pj (tributario-r03) | idem |
| seg-empresarial-negativa-lucros-cessantes (codex-autonomos-seguros-r20) | idem + fonte 4 Susep tangencial (página genérica “etapas-da-vida”) |
| imob-direito-de-laje-vender-financiar (imobiliario-r03) | paid-signal genérico |
| pi-dominio-ex-prestador-registrou (pi-r02) | paid-signal genérico |
| banc-pix-por-aproximacao-roubo-contestar (bancario-r03) | paid-signal genérico |
| cid-estr-refugio-solicitar (cidadania-06) | H1 quase-paráfrase do title; fonte 2 com http_status=206 (gate trata como sucesso?) |

## MOLDE SINTÁTICO QUANTIFICADO (grep no estoque aceito inteiro, 7.178 páginas)

1. **`advogad[oa]…sem (prometer|garantir)`: 105 páginas aceitas** (98 comercial). Destas, **67 comerciais sem NENHUM outro marcador de contratação particular** (particular/contratar/honorário/escritório) — dependem só do fecho genérico como sinal pago. Risco direto de `paid_intent_blocked_cta_only_paid_signal` em massa e de molde perceptível ao leitor/Google.
2. **`(conteúdo|guia) é informativ…`: 75 páginas aceitas** (66 comercial), concentradas em `codex-*-portfolio-*`. **Corrige o censo do frontboard `molde-disclaimer-28`: universo real = 75 aceitas**, não 28 (censo anterior usou string exata; regex ampla pega variantes).
3. `não é automátic…`: 337 páginas — ressalva provavelmente legítima (anti-promessa), risco baixo, registrado por completude.

Molde é SINTÁTICO (esqueleto de 15–20 palavras; corpo ao redor varia) — tende a passar no gate de similaridade <0.70. **Recomendação de gate:** regex dedicado anti-frase-esqueleto no check editorial, além do embedding de corpo.

## FILA EXECUTÁVEL (via canal sancionado)

1. Extinguir “Este guia é informativo.”/variantes nas 75 (fundir com item molde-disclaimer do frontboard, atualizando 28→75).
2. Reescrever fecho das 67 comerciais sem marcador: 1 frase sóbria com sinal explícito de contratação particular (atendimento remoto/documentos por WhatsApp), sem promessa de resultado.
3. seg-empresarial-negativa-lucros-cessantes: fonte Susep específica de lucros cessantes.
4. cid-estr-refugio-solicitar: reescrever H1; conferir tratamento de http_status=206 no gate de fontes (se 206 passa como 200, endurecer).
5. Polimento: URLs com `#art` quando anchor_claim cita artigo específico (5 páginas da amostra).
