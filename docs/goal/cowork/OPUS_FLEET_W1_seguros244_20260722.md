# OPUS FLEET W1 — seguros 244 correções lote-2 (Lei 15.040/2024)

Autor: Opus 4.8 (Cowork wave W1). Data: 2026-07-22. Frontboard: `seguros-244-correcoes-lote2` (P1).
Modo: READ-ONLY sobre repo/dado; verificação viva em fonte oficial; entrega executável única.

## SCOPE

Aplicar as correções lote-2 pós-cutoff às páginas que citam a **Lei 15.040/2024 (Marco Legal dos
Seguros)** ANTES de escrever mais seguros. O censo-fonte (`cowork_poscutoff_verificacao_lote2`) já
verificou a lei como VERDADEIRA na substância e prescreveu dois ajustes: (a) citação precisa do
art. 10; (b) nuance de transição (não afirmar que a 15.040 rege "hoje" sem ressalva). Este arquivo
converte isso em fila executável por `intent_id`, mais um achado novo (inconsistência de data
10 vs 11/12/2025) apanhado na auditoria direta dos shards.

## WHAT I READ

- Frontboard `.agents/runtime/p0_frontboard.jsonl` — task `seguros-244-correcoes-lote2` (P1) e
  vizinhas (`ondas-gap-2345` adia seguros; `mold-specs-wiring`; `faq-qa-unmarshal-bug` toca
  `seguros-r03/-r08`).
- Censo-fonte: `data/source-audit/cowork_poscutoff_verificacao_lote2_20260722.md` (item 1, 244 pg),
  `cowork_claims_poscutoff_lote2_20260722.md`, `cowork_poscutoff_census_verificacao_20260722.md`
  (Lei 15.040 = 678 pg / 41 shards no censo completo).
- Shards v2: 44 shards citam a lei; **201 páginas** invocam textualmente "15.040 / Marco Legal dos
  Seguros" (top: seguros-05/07/09/04/03/08/06/d01/10/02; cauda em bancário, imobiliário, sucessões,
  lgpd, procedimentos, sumulas, autônomos). Página-exemplo `seg-empresarial-do-defesa-multa`
  (`codex-autonomos-seguros-r16`) lida na íntegra (schema: opening/sections[{heading,text}]/faq).
- Fontes oficiais ao vivo (WebSearch + web_fetch): Planalto l15040, Câmara notícia 1119630,
  camara.leg.br/legin publicação original.

## FINDINGS

1. **Issue A (citação art. 10) é ESTREITA — 1 página, não centenas.** Só `seg-empresarial-do-defesa-multa`
   cita "art. 10, I". O correto é **art. 10, parágrafo único, I** (o inciso pende do parágrafo único,
   não do caput). `lgpd-seguro-cyber-cobre-multa` já escreve "art. 10, parágrafo único" — está certa.
2. **Achado novo — erro material de data (1 dia), com inconsistência interna no estoque.** Publicação
   DOU 10/12/2024; vacatio de 1 ano. Por LC 95/1998, art. 8, §1º (inclui a data de publicação e o
   último dia do prazo, vigor no dia subsequente), a vigência começa em **11/12/2025** — como o censo
   fixou e como `proc-susep-reclamar` e `seg-condicoes-gerais-nao-entregues` escrevem. Mas
   `seg-vida-suicidio-dois-anos` e `sum-stj-402` dizem **"10 de dezembro de 2025"** — errado por 1 dia.
3. **Issue B (nuance de transição) — 13 páginas com moldura de presente** ("hoje rege / passou a reger
   / em vigor desde / regido pela 15.040") sem ressalva de que apólices e sinistros anteriores à
   vigência seguem o Código Civil. Nenhuma AFIRMA algo falso; falta a ressalva prescrita pelo censo.
4. **Substância limpa (NÃO mexer).** Verifiquei ao vivo os artigos mais citados e todos conferem:
   art. 10 par.ún. I (multas/penalidades por ilícito criminal — nulas); art. 126 (I e II = 1 ano;
   III = 3 anos); art. 133 (revoga art. 206 §1º II + arts. 757–802 CC + arts. 9–14 do DL 73/66);
   art. 132 (apólice de vida = título executivo extrajudicial); art. 116 (capital-morte não é
   herança), 118 (carência ≤ metade da vigência), 120 (suicídio 2 anos), 89/94 (dano/sub-rogação).
   Sem lei, número, prazo ou tese inventados nesta amostra.

## CORRECTION QUEUE

### P1 — bloqueiam promote (erro material / citação imprecisa)

| # | intent_id | shard | issue | texto corrigido / ação | fonte |
|---|---|---|---|---|---|
| 1 | seg-empresarial-do-defesa-multa | codex-autonomos-seguros-r16 | citação: "O art. 10, I, da Lei 15.040 declara nula a garantia de multas..." | trocar por "O **art. 10, parágrafo único, I**, da Lei 15.040/2024 declara nula a garantia dos valores de multas e demais penalidades aplicadas por atos pessoais do segurado que caracterizem ilícito criminal." (substância já correta; só a âncora do inciso) | planalto l15040 #art10 |
| 2 | seg-vida-suicidio-dois-anos | seguros-06 | data errada: "em vigor desde 10 de dezembro de 2025" | "em vigor desde **11 de dezembro de 2025**" | LC 95/98 art. 8 §1 + vacatio 15.040 |
| 3 | sum-stj-402 | sumulas-03 | data errada: "passou a reger o contrato de seguro em 10 de dezembro de 2025" | "...em **11 de dezembro de 2025**" | idem |

### P2 — nuance de transição (exigida pelo censo p/ as 244; não bloqueia se substância certa)

**Regra blanket (inserir onde a página afirma que a 15.040 rege "hoje" os contratos):**
> "A Lei 15.040/2024 (Marco Legal dos Seguros) entrou em vigor em 11 de dezembro de 2025 e disciplina
> os contratos de seguro celebrados a partir dessa data. Apólices firmadas e sinistros ocorridos antes
> da vigência continuam regidos pelo Código Civil (arts. 757 a 802); nas renovações, vale conferir a
> data de contratação e as condições da apólice."

Aplicar (trocar "hoje rege / passou a reger / em vigor desde ... " isolado pela moldura acima ou
acrescentar a ressalva na sequência):

| # | intent_id | shard | trecho atual (presente sem ressalva) |
|---|---|---|---|
| 4 | imob-seguro-mip-morte-invalidez | imobiliario-11 | "...é regida pelo art. 44 da Lei 15.040/2024, que revogou os arts. 757..." |
| 5 | proc-susep-reclamar | procedimentos-13 | "A Lei do Contrato de Seguro está em vigor desde 11 de dezembro de 2025..." (data OK; falta ressalva) |
| 6 | seg-verbete-dps | seguros-03 | "...foi revogado pela Lei 15.040/2024, que hoje disciplina a matéria..." |
| 7 | seg-auto-perda-total-criterio | seguros-04 | "A Lei 15.040/2024, em vigor desde dezembro de 2025, estabelece no artigo 89..." |
| 8 | seg-auto-acionar-seguro-do-culpado | seguros-05 | "A Lei 15.040/2024, que passou a reger os contratos de seguro no lugar dos antigos artigos..." |
| 9 | seg-vida-vs-acidentes-pessoais | seguros-07 | "O seguro de vida, hoje regido pela Lei 15.040/2024, garante..." |
| 10 | seg-empresarial-o-que-cobre | seguros-09 | "A Lei 15.040/2024, que hoje rege o contrato de seguro de forma geral, trata..." |
| 11 | seg-celular-roubo-furto | seguros-10 | "15.040/2024, publicada em dezembro de 2024 e em vigor desde dezembro de 2025 — quando passou a disciplinar..." |
| 12 | seg-vida-negativa-esporte-radical | seguros-d01 | "...regidos pela Lei 15.040/2024, a seguradora não pode se eximir..." |
| 13 | seg-auto-endosso-troca-veiculo-mesma-apolice | seguros-inf1 | "A Lei 15.040/2024, que hoje rege os contratos de seguro no Brasil, trata..." |
| 14 | seg-condicoes-gerais-nao-entregues | seguros-r10 | "A Lei 15.040/2024 passou a reger o contrato de seguro em 11 de dezembro de 2025..." (data OK; falta ressalva) |
| 15 | seg-empresarial-do-defesa-multa | codex-autonomos-seguros-r16 | (além do #1: acrescentar ressalva de transição) |
| 16 | seg-vida-suicidio-dois-anos | seguros-06 | (além do #2: acrescentar ressalva de transição) |
| 17 | sum-stj-402 | sumulas-03 | (além do #3: acrescentar ressalva de transição) |

> Nota de cobertura: enumerei as 13 páginas com moldura de PRESENTE (as de maior risco). O censo
> pede a nuance nas ~244; as demais só citam a lei em contexto histórico/pontual (baixo risco). A
> aplicação em lote deve varrer `hoje reg|passou a reger|em vigor desde|regid[ao] pel.* 15.040` e
> injetar a ressalva blanket via gerador, nunca à mão página a página.

## VERIFICATION EVIDENCE

- **Art. 10, parágrafo único, I** — "São nulas as garantias... I - dos valores das multas e demais
  penalidades aplicadas em virtude de atos pessoais praticados pelo segurado que caracterizem ilícito
  criminal." (WebSearch dominio planalto/camara/in/senado, 2026-07-22). Confirma o alvo do fix #1.
- **Art. 126** — I e II = 1 ano; III = 3 anos (beneficiário/terceiro). Confere com as páginas
  `proc-susep-reclamar`, `seg-sinistro-prescricao-um-ano`, `seg-vida-suicidio-dois-anos`.
- **Art. 132 / 133** — 132 = apólice de vida é título executivo extrajudicial; **133 revoga art. 206
  §1º II + arts. 757–802 CC + arts. 9–14 do DL 73/66**. Confirma as páginas `lei-cc-art-763/768/798`.
- **Vigência** — Planalto: "entra em vigor após decorrido 1 (um) ano de sua publicação oficial";
  DOU 10/12/2024 → por LC 95/98 art. 8 §1, vigor em **11/12/2025**. A notícia da Câmara 1119630
  (datada 10/12/2024, terça-feira) trata da SANÇÃO e usou "entra em vigor" de forma jornalística —
  provável origem da confusão do "10" em duas páginas.
- **Substância corroborada** pela síntese oficial da Câmara 1119630: suicídio 2 anos, carência ≤
  metade da vigência, capital-morte fora da herança, salvados reembolso até 20% se não pactuado,
  pagamento em 30 dias (até 120 pela Susep) — batem com o estoque.
- Fontes: planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15040.htm ;
  camara.leg.br/noticias/1119630-entra-em-vigor-o-marco-legal-dos-seguros ;
  camara.leg.br/legin .../lei-15040-9-dezembro-2024-796661-publicacaooriginal .

## COLLISION-SAFETY NOTE

- 100% READ-ONLY: nenhuma edição em `data/`, `v2ingest.go`, `validate.go`, nenhum git, nenhum build
  pesado. Única escrita = este arquivo. Greps/reads focados + 4 WebSearch + 1 web_fetch.
- Esta fila é INSUMO para o terminal/gerador sancionado — a aplicação em `data/editorial/v2_pages/*`
  deve ser feita pelo gerador correspondente (não à mão), preservando trabalho concorrente das outras
  waves; shards `seguros-r03/-r08` também estão na task `faq-qa-unmarshal-bug` (coordenar ordem).
- NÃO relaxar gate para as 3 páginas P1: são fixes de precisão (âncora de inciso + data), a
  substância permanece intacta. Após aplicar #1–#3 e a ressalva blanket, as páginas ficam aptas ao
  cohort de promote junto com o restante da massa 15.040 (substância já verificada VERDADEIRA).
