# DUPPHRASE_205_CHARACTERIZATION_20260722 — os 205 `duplicate_phrase_with_page` são falso-positivo de citação legal (GATE-TUNE, não rewriter)

Autor: `claude-cowork-fable` (Fable 5). Continuação de `DUPPHRASE_DRAIN_SPEC_20260722.md`: o rerun que aquele spec pediu ACONTECEU (bucket caiu 484→205). Este arquivo caracteriza os 205 remanescentes do run `v2-ingest-20260722T140000Z`. **Evidência lida no disco (páginas + partner + validador Go), não memória.**

## Veredito

**Os 205 são majoritariamente FALSO-POSITIVO sobre texto estatutário repetido legitimamente. Recomendação: TUNAR O GATE (2 isenções cirúrgicas), NÃO gastar rewriter** — reescrever destruiria citação legal correta para satisfazer um bug do gate. **0 molde real** na amostra.

## Regra atual do gate (com file:line)

- Emite em `internal/v2ingest/validate.go:409` → `duplicate_phrase_with_page:line=<partner>:intent=<partner_intent>` (o partner é sempre uma página ACEITA; a mais antiga em ordem estável vence).
- `classifyDuplicatePhrases` (validate.go:995): **janela n-gram = 12 palavras** (`duplicatePhraseNgramSize=12`, :24). Duas páginas colidem se compartilham UMA janela idêntica de 12 tokens (title/meta/H1/opening/seções/FAQ, foldadas por `ptbrtext.FoldTokenForCompare`).
- Isenção `isLegalCitationExempt` (validate.go:1040) só libera se **os TRÊS** valerem: (a) `legalAnchorNearWindow` — `art./Lei/Súmula/Decreto`+número ou token de código (`cdc/clt/cpc/cf/ctn/inciso/paragrafo/caput`) dentro de **20 tokens** (:46); (b) trecho idêntico contíguo ≤ **40 palavras** (:41); (c) as duas páginas compartilham a MESMA URL de fonte oficial normalizada. Falhou um → REJEITA.

## Amostra (15 pares, shards distintos)

| # | shard rej | frase colidente (curta) | por que não isenta | classe |
|---|---|---|---|---|
| 1 | imobiliario-p10 | "art 725 CC…remuneracao devida ao corretor…arrependimento das partes" (span 41) | span>40 (por 1) | LEGIT (CC 725 verbatim) |
| 2 | leis-04 | "informacoes insuficientes ou inadequadas sobre a utilizacao e os riscos do produto" | sem âncora+sem src | LEGIT (CDC 12 §1) |
| 3 | imobiliario-03 | "flagrante delito desastre para prestar socorro ou durante o dia por determinacao judicial" | sem âncora | LEGIT (CF 5º XI) |
| 4 | sucessoes-01 | "convivencia publica continua e duradoura…objetivo de constituir familia" | sem fonte comum | LEGIT (CC 1.723) |
| 5 | codex-autonomos-seguros | "ouvidoria consumidor gov br e susep podem tratar da conduta mas nao substituem" | sem âncora | AMBÍGUO (canais SUSEP) |
| 6 | telecom_energia-04 | "defeituoso o servico que nao oferece a seguranca que o consumidor dele" | sem âncora | LEGIT (CDC 14 §1) |
| 7 | trabalhista-01 | "ser proposta em ate dois anos apos o fim do contrato" | sem âncora | LEGIT (prescrição CF 7º XXIX) |
| 8 | lgpd-02 | "de acordo com o requerimento da pessoa interessada" | sem âncora | AMBÍGUO (retificação) |
| 9 | glossario-01 | "reconhecimento de seu direito sucessorio e a restituicao da heranca" | sem âncora | LEGIT (CC 1.824 petição herança) |
| 10 | previdenciario-08 | "ao conselho de recursos da previdencia social no prazo de trinta dias" | sem âncora | LEGIT (CRPS) |
| 11 | consumidor-10 | "antigo proprietario deve encaminhar ao orgao de transito no prazo de sessenta dias" | sem âncora | LEGIT (CTB 134, 60d vigente) |
| 12 | transito-03 | "despesas com o tratamento da vitima seu funeral e o luto da familia" | sem fonte comum | LEGIT (CC 948 I) |
| 13 | familia-09 | "a defensoria publica do seu estado que atua gratuitamente em acoes de" | sem âncora | AMBÍGUO/molde-lean (referral reusado) |
| 14 | imobiliario-25 | "tem como fato gerador a propriedade o dominio util ou a posse" | sem fonte comum | LEGIT (CTN 32) |
| 15 | codex-sucessoes | "o codigo de defesa do consumidor preve responsabilidade por defeito do servico" | sem fonte comum | LEGIT (CDC serviço) |

**Split:** LEGIT ~12/15 (80%); AMBÍGUO ~3/15 (20%); **REAL-MOLDE 0/15.**

## Análise do conjunto inteiro (205)

- **199/205 frases colidentes são ÚNICAS; ZERO frase repete ≥3×.** Molde reusa a MESMA sentença em muitas páginas — aqui é ~1 colisão : 1 frase. Isso, sozinho, exclui molde.
- **152/205 (74%) colisões são CROSS-família** (imobiliário↔criminal em "casa inviolável"; transito↔consumidor em CTB 134; telecom↔consumidor em CDC 14). Colisão entre áreas em janela de 12 palavras = boilerplate estatutário compartilhado, não molde de gerador.
- Espalhado por **139 shards / 25 áreas**, máx 6/shard. Sem hotspot.
- Run idêntico curto: mediana **13 palavras**, média 14,4; **204/205 ≤40 palavras** (só 1 passa — e é CC 725 verbatim).
- **Por que a isenção falha:** 142/205 (69%) falham SÓ o critério (a) `sem âncora` — **e todas compartilham a MESMA URL de fonte com o partner** e são ≤40 palavras. 45/205 (22%) falham SÓ (c) `sem fonte comum` tendo âncora legal válida. 17 falham ambos. Só 1 falha o span.

## Recomendação — GATE-TUNE (não rewriter)

1. **Primária (corrige 142/205): dispensar o requisito de "número de artigo adjacente" quando o critério de fonte-compartilhada já vale.** Quando (b) span≤40 E (c) as duas páginas citam a MESMA URL de fonte oficial normalizada, não exigir também `art NNN` dentro de 20 tokens. Fragmentos estatutários citam a substância sem o número do artigo colado. O comentário em `validate.go:1032` já nota a tensão ("se a mera presença de uma fonte bastasse, (a) colapsaria em (c)") — mas o dado mostra que uma URL de fonte oficial **específica e auditada** compartilhada JÁ é âncora suficiente. Manter (a) como guarda só no caminho sem-fonte-comum.
2. **Secundária (corrige ~45/205): afrouxar (c) para nível-de-lei, não URL-exata.** Casos CC 948 / CTN fato gerador / CDC serviço falham porque as duas páginas linkam a mesma lei por anchors/paths diferentes. Normalizar `sourceKeysIntersect` para comparar host+lei (ignorando fragmento `#artNNN` e segmentos de path por-artigo), OU liberar quando a âncora textual (nome da lei + número do artigo) casa mesmo com URLs distintas.
3. **Terciária (1 registro): subir `maxLegalCitationSpanWords` 40→~48** para citações verbatim ancoradas em fonte. Baixa prioridade.

## Por que TUNAR não é relaxar anti-fraude (nota do fiscal)

O gate dup-phrase (janela exata de 12 palavras) é defesa DIFERENTE do gate de **similaridade semântica de corpo <0.70** (anti-molde estrutural). Afrouxar a isenção de CITAÇÃO no dup-phrase — restrita a `span≤40 + mesma URL de fonte oficial auditada` — **não** enfraquece a defesa anti-molde, que continua pegando molde estrutural pelo outro gate. A isenção é estreita e ancorada em proveniência real (mesma lei oficial), não em texto de marketing. Impacto: potencial desbloqueio de **~187/205** páginas de citação legítima rumo aos 10k, sem gastar rewriter (que aqui seria destrutivo).

**Amostra ANTES de aplicar:** ler os ~3 ambíguos (referral Defensoria familia-09; canais SUSEP; retificação lgpd-02) — são boilerplate informativo curto (12-13 palavras), não molde; não justificam rewriter, mas se o dono quiser rigor, variar essas 3 sentenças institucionais é opcional.
