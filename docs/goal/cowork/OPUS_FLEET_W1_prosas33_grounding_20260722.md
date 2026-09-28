# OPUS FLEET W1 — Auditoria semântica de grounding das prosas de entidade ANCHORED_PENDING
Data: 2026-07-22 · Verificador: Opus 4.8 (Cowork wave, 1 agente) · Modo: READ-ONLY · Canal P1 (fora do caminho 10k)

## SCOPE
Alvo: prosas de entidade **ancoradas mas pendentes de veredito SEMÂNTICO** (`ANCHORED_PENDING_SEMANTIC`) — o T3 determinístico ancora byte-a-byte o rótulo/artigo citado, mas **não** julga se a AFIRMAÇÃO da prosa corresponde ao que a fonte oficial de fato diz.
- Estoque ancorado: `data/ops/entity_prose_grounded_20260721.jsonl` = **54 registros** (idx 0–53).
- Destes, **4 já confirmados com erro material** (fila `prosas-4-reredacao`): idx 3 (art.5 CDC), idx 21 (art.3 CLT), idx 27 (art.59 Lei Inquilinato), idx 52 (art.74 L8213). **Fora do meu escopo.**
- Restam **50 ANCHORED_PENDING_SEMANTIC** — este é o universo auditável. **Amostrei 12** (os de maior risco: prazos, valores, percentuais, benefícios previdenciários sensíveis a reforma).
- Separado: `entity_prose_quarantine_20260721.jsonl` (42 registros / "prosas-33-grounding-gate") são QUARENTENADOS fail-closed (DEC-021) — **não ancorados**, precisam passar por `cmd/verify-grounding` antes de qualquer semântica. Fora deste escopo.

## WHAT I READ
- `.agents/runtime/p0_frontboard.jsonl` linhas 17 (`prosas-33-grounding-gate`) e 33 (`prosas-4-reredacao`) — definição de escopo e os 4 erros já confirmados.
- `data/ops/entity_prose_grounded_20260721.jsonl` — 54 títulos + corpo/faq das 12 amostradas (opening, sections, faq).
- Fontes oficiais LIVE (fetch Planalto hoje, 2026-07-22, encoding ISO-8859-1 verificado):
  - L8213: `https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm`
  - CLT (Del 5.452/43): `https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm`
  - Lei do Inquilinato (8.245/91): `https://www.planalto.gov.br/ccivil_03/leis/l8245.htm`

## SAMPLE AUDIT TABLE (12 páginas)
| idx | Página (artigo) | Afirmação verificada | Fonte oficial | Veredito |
|----|------------------|----------------------|---------------|----------|
| 1  | Art. 48 L8213 — aposentadoria por idade | Rural: idade reduzida em 5 anos → 60 (h) / 55 (m) | L8213 art. 48 caput | **CLEAR** |
| 15 | Art. 57 L8213 — aposentadoria especial | Agentes químicos/físicos/biológicos; renda "observado art. 33" | L8213 art. 57 §1/§4 + art. 58 | **CLEAR** |
| 18 | Art. 59 L8213 — auxílio-doença | "Teto de até 60 dias" + "suspensão por recolhimento à prisão" | L8213 art. 59 | **FIX (material)** |
| 24 | Art. 59 CLT — horas extras | Adicional mínimo de 50%; banco de horas; saldo na rescisão | CLT art. 59 §1 | **CLEAR** |
| 25→41 | Art. 25 L8213 — carência | 12 contrib. (doença/invalidez); 180 (idade/tempo/especial) | L8213 art. 25 I e II | **CLEAR** |
| 26 | Art. 46 Lei Inquilinato — 30 meses | Aplica-se a locação escrita e prazo ≥ 30 meses | L8245 art. 46 | **CLEAR** |
| 32 | Art. 58 CLT — jornada | Duração normal não excederá 8h, salvo limite expresso | CLT art. 58 | **CLEAR** |
| 36 | Art. 129 CLT — férias | Direito anual a férias sem prejuízo da remuneração | CLT art. 129 | **CLEAR** |
| 43 | Art. 71 CLT — intervalo | ≤ 6h → intervalo obrigatório de 15 min | CLT art. 71 §1 | **FIX (precisão)** |
| 45 | Art. 42 L8213 — invalidez | Incapacidade + carência quando exigida + exame pericial | L8213 art. 42 + §1 | **CLEAR** |
| 46 | Art. 86 L8213 — auxílio-acidente | 50% do salário-de-benefício; não acumula com aposentadoria | L8213 art. 86 §1 | **CLEAR** |
| 51 | Art. 487 CLT — aviso prévio | 8 dias (semana/menor) / 30 dias (quinzena, mês ou >12 meses) | CLT art. 487 I-II | **CLEAR** |

**Resultado: 12 amostradas → 10 CLEAR · 2 FIX** (1 material, 1 de precisão).

## FIX DETAILS

### FIX-1 (MATERIAL) — idx 18 · `epd-cand-c5c22929770e7196` · Art. 59 L8213 (auxílio-doença)
Alucinação estrutural: a prosa inventa um regime de "prisão/suspensão/teto de 60 dias" que **NÃO existe** no art. 59, e OMITE o núcleo real do artigo (incapacidade por mais de 15 dias consecutivos).

Trechos ERRADOS (verbatim, a remover):
- Opening: *"...aponta situações em que ele não se aplica e **trata da suspensão quando o segurado é recolhido à prisão**."*
- Seção: *"...o benefício **não é devido ao segurado que se encontra recluso em regime fechado**."*
- Seção [O limite de tempo da suspensão]: *"O artigo fixa um teto: **ela pode durar até sessenta dias**, contados a partir do marco previsto no próprio dispositivo."*
- FAQ: *"Por quanto tempo o benefício fica suspenso? ... **pode alcançar até sessenta dias**..."* e *"Quem está preso pode receber auxílio-doença?"*

Fonte oficial (Planalto L8213, verificado 2026-07-22):
> "Art. 59. O auxílio-doença será devido ao segurado que, havendo cumprido, quando for o caso, o período de carência exigido nesta Lei, ficar incapacitado para o seu trabalho ou para a sua atividade habitual **por mais de 15 (quinze) dias consecutivos**. § 1º Não será devido o auxílio-doença ao segurado que se filiar ao Regime Geral de Previdência Social já portador da doença ou da lesão invocada como causa para o benefício, exceto quando a incapacidade sobrevier por motivo de progressão ou agravamento da doença ou da lesão."

O art. 59 **não menciona prisão, reclusão nem prazo de 60 dias**. (Recolhimento à prisão aparece em L8213 no art. 16 §5 — prova de dependente — e no auxílio-reclusão, art. 80; nunca no art. 59.)

Correção executável (re-redigir o corpo para):
1. Concessão: devido ao segurado que, cumprida a carência (quando exigível), fica incapacitado para o trabalho/atividade habitual **por mais de 15 dias consecutivos** — incluir esse marco de 15 dias, hoje ausente.
2. Exclusão (§1): não devido a quem se filiou ao RGPS **já portador da doença/lesão**, salvo progressão/agravamento.
3. **Excluir integralmente** as seções [Situações...recluso], [Prisão do segurado e suspensão] e [O limite de tempo da suspensão] e as 2 FAQs de prisão/60 dias.
Recomendação: rotear idx 18 para a fila `prosas-4-reredacao` (mesma gravidade dos 4 já confirmados) — passa a 5/50 com erro material.

### FIX-2 (PRECISÃO) — idx 43 · `epd-cand-a0236dba75031e` · Art. 71 CLT (intervalo)
Trecho ERRADO (verbatim):
> *"Se o trabalho não excede seis horas, o dispositivo ainda assim prevê uma pausa: nesse caso, torna-se obrigatório um intervalo de quinze minutos."*

Omite a condição legal do gatilho (**> 4 horas**), sugerindo que qualquer jornada ≤ 6h (ex.: 3h) exige 15 min.

Fonte oficial (Planalto CLT art. 71 §1, verificado 2026-07-22):
> "§ 1º Não excedendo de 6 (seis) horas o trabalho, será, entretanto, obrigatório um intervalo de 15 (quinze) minutos **quando a duração ultrapassar 4 (quatro) horas**."

Correção executável (texto substituto):
> "Se o trabalho não excede seis horas **mas ultrapassa quatro horas**, torna-se obrigatório um intervalo de quinze minutos. Jornadas contínuas de até quatro horas não têm intervalo intrajornada obrigatório por esse dispositivo."

## RESIDUAL (não auditado)
- **50 ANCHORED_PENDING_SEMANTIC** no total; **12 auditadas** → **38 permanecem SEM veredito semântico.**
- idx auditados (10 CLEAR + 2 FIX): 1, 15, 18, 24, 25, 26, 32, 36, 43, 45, 46, 51.
- idx **residuais un-audited (38):** 0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 20, 22, 23, 28, 29, 30, 31, 33, 34, 35, 37, 38, 39, 40, 42, 44, 47, 48, 49, 50, 53.
- Perfil dos residuais: majoritariamente CDC, Código Civil (sucessões/contratos/família), Lei do Inquilinato e definições institucionais — muitos hedged/estruturais (baixo risco numérico), mas **nenhum pode ser promovido sem auditoria semântica individual**. Priorizar nas próximas ondas os que citam valores/prazos: idx 2 (art.51 renovação 5/3 anos), idx 10/16/17/35/47/48 (Inquilinato), idx 29 (art.1.694 CC alimentos), idx 40 (art.18 L8213 rol de prestações).
- Fora deste canal: 4 re-redação (idx 3/21/27/52) + 42 quarentenados (fail-closed) — trilhas próprias.

## COLLISION-SAFETY NOTE
- **READ-ONLY cumprido.** Nenhuma edição em `data/editorial/`, `data/ops/`, `internal/grounding/v2ingest.go` ou `validate.go`; nenhum git; nenhum build Go/suite pesada. Só Grep/Read + `curl`/`iconv` em `/tmp` (fora do repo) e small python3 read-only sobre o JSONL.
- **Saída única:** este arquivo (`docs/goal/cowork/OPUS_FLEET_W1_prosas33_grounding_20260722.md`). Nada mais escrito.
- Não toquei os JSONL de grounding/quarentena nem os 4 registros da fila `prosas-4-reredacao` (donos: tarefa `prosas-4-reredacao`). idx 18 é **recomendação** de roteamento, não alteração aplicada.
- Vereditos ancorados em texto oficial LIVE do Planalto (2026-07-22); idx 15 foi conferido a fundo para evitar falso-positivo (a taxonomia "químicos/físicos/biológicos" está em art. 57 §4 + art. 58 — legítima, por isso CLEAR).
