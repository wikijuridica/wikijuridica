# OPUS FLEET W2 — Grounding semântico do RESIDUAL das prosas de entidade ANCHORED_PENDING
Data: 2026-07-22 · Verificador: Opus 4.8 (Cowork wave, 1 agente) · Modo: READ-ONLY · Canal P1 (fora do caminho 10k)
Continua `OPUS_FLEET_W1_prosas33_grounding_20260722.md`. Tarefa: `prosas-33-grounding-gate` (residual).

## SCOPE
- Estoque ancorado: `data/ops/entity_prose_grounded_20260721.jsonl` = 54 registros (idx 0–53).
- Fora de escopo: 4 já confirmados com erro (`prosas-4-reredacao`: idx 3, 21, 27, 52) + 12+1 auditados pela Onda 1 (idx 1, 15, 18, 24, 25→41, 26, 32, 36, 43, 45, 46, 51).
- **Universo residual: 37 idx** sem veredito semântico. Auditei **18 de maior risco** (os que citam artigo/prazo/valor/número específico). 19 ficam para a W3.
- **Lição da Onda 1 (Fable reprovou o FIX-1/art. 59):** só marco FIX se PROVAR o erro contra o texto oficial VIGENTE; na dúvida, CLEAR-com-ressalva; nunca tratar lei vigente como alucinação, nunca sugerir apagar conteúdo correto.

## WHAT I READ
- `entity_prose_grounded_20260721.jsonl` — opening+sections+faq das 18 auditadas + títulos dos 37 residuais.
- Drop da Onda 1 (idx já vistos) e `p0_frontboard.jsonl` (definição da task).
- **Fontes oficiais LIVE (Planalto, 2026-07-22, ISO-8859-1 verificada):**
  - L8245 (Inquilinato): `https://www.planalto.gov.br/ccivil_03/leis/l8245.htm` — arts. 4, 47, 51, 62
  - CLT compilado (DL 5.452/43): `https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm` — arts. 7, 62, 443, 457, 477, 482
  - Código Civil compilada (L10.406/02): `https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm` — arts. 944, 1.694, 1.784, 1.829
  - L8213/91: `https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm` — art. 18

## TABELA (18 auditadas)
| idx | cand-id | Página (artigo) | Afirmação central verificada vs texto oficial | Veredito |
|----|---------|-----------------|-----------------------------------------------|----------|
| 0  | cand-8e1df073da04c7d0 | Art. 482 CLT — justa causa | improbidade/incontinência/negociação habitual/condenação criminal/desídia (a–e) | **CLEAR** |
| 2  | cand-8f683c9bc517ac20 | Art. 51 Inquilinato — renovação | escrito+prazo det.; 5 anos (soma); mesmo ramo **3 anos**; cessionários §1 | **CLEAR** |
| 5  | cand-baf6674a50788041 | Art. 944 CC — extensão do dano | indeniz.=extensão do dano; redução equit. por desproporção culpa×dano (§ún.) | **CLEAR** |
| 7  | cand-8e2ef573da134382 | Art. 457 CLT — remuneração | salário+gorjetas; §1 "gratificações legais"; §2 ajuda custo/aux-alim/prêmios (Lei 13.467) | **CLEAR** |
| 10 | cand-8f6bc59bc51acac2 | Art. 22 Inquilinato — deveres do locador | entregar em uso; uso pacífico; forma/destino; vícios anteriores; descrição (I–V) | **CLEAR** |
| 13 | cand-8e280573da0d4004 | Art. 477 CLT — rescisão | anotação CTPS+comunicar+pagar (Lei 13.467); §2 instrumento/quitação; §5 teto compensação (hedged) | **CLEAR** |
| 16 | cand-8f6bc69bc51acc75 | Art. 23 Inquilinato — deveres do locatário | pagar no prazo; uso convencionado; restituir salvo uso normal; comunicar defeitos (I–IV) | **CLEAR** |
| 17 | cand-475bd6d7c04e4c85 | Art. 9º Inquilinato — desfazimento | mútuo acordo; infração; falta de pagamento; reparos urgentes do Poder Público (I–IV) | **CLEAR** |
| 19 | cand-6533302d4db7fd6 | Art. 1.784 CC — saisine | herança transmite-se desde logo a herdeiros legítimos e testamentários | **CLEAR** |
| 22 | cand-8e2b8973da105627 | Art. 443 CLT — prazo determinado | tácito/expresso, verbal/escrito, det./indet.; §2 a-c hipóteses | **CLEAR (ressalva)** |
| 29 | cand-f65e802da1cca18 | Art. 1.694 CC — alimentos | parentes/cônjuges/companheiros; binômio necessidade×possibilidade §1; culpa→subsistência §2 | **CLEAR** |
| 33 | cand-75c87c0331dcf55b | Art. 7º CLT — exclusões | domésticos/rurais/func. públicos/autarquias paraestatais (a–d) — literal vigente | **CLEAR** |
| 35 | cand-8f64d29bc514c22b | Art. 47 Inquilinato — retomada residencial | <30 meses→indeterminado; retomada por **5 anos** de vigência (inc. V) | **CLEAR** |
| 40 | cand-c5cfb2297719e4bd | Art. 18 L8213 — prestações ao segurado | aposent. invalidez/idade/**tempo de contribuição**/especial — literal vigente | **CLEAR** |
| 42 | cand-9ca06dba71eeae | Art. 62 CLT — fora do controle de jornada | I ext. incompatível; II gestão/gerentes; III **teletrabalho por produção/tarefa** (Lei 14.442/22) | **CLEAR** |
| 47 | cand-475bd9d7c04e519e | Art. 4º Inquilinato — saída antecipada | locador não retoma no prazo; devolução c/ multa; dispensa por transferência | **FIX (precisão)** |
| 48 | cand-8f5dcd9bc50e9afe | Art. 62 Inquilinato — evitar despejo | cumulação despejo+cobrança; purga da mora em **15 dias**; Lei 12.112 | **CLEAR (ressalva)** |
| 50 | cand-9639230295815bee | Art. 1.829 CC — sucessão legítima | descendentes(+cônjuge, salvo regimes)/ascendentes(+cônjuge)/cônjuge/colaterais (I–IV) | **CLEAR** |

**Resultado: 18 auditadas → 17 CLEAR (2 com ressalva material) · 1 FIX (precisão). Zero alucinação.**
Confirmações anti-falso-positivo (armadilha da Onda 1): idx 40 "aposentadoria por tempo de contribuição" e idx 33 "domésticos/rurais" **constam LITERALMENTE do texto vigente** (art. 18, I, c L8213 c/ LC 123/2006; art. 7º a-b CLT). A EC 103/2019 e leis próprias mudam a prática, mas a prosa é fiel ao dispositivo ancorado → CLEAR, não FIX.

## FIX DETAILS

### FIX-1 (PRECISÃO) — idx 47 · `cand-475bd9d7c04e519e` · Art. 4º Lei 8.245/91
Dois qualificadores materiais do texto vigente foram OMITIDOS, o que subestima direito e superestima obrigação do locatário (erro por omissão de condição legal, análogo ao FIX-2/art. 71 da Onda 1). Não é alucinação e nada deve ser apagado — a correção **acrescenta** o que falta.

Trecho incompleto (verbatim, seção "A devolução antecipada pelo locatário"):
> "...o locatário pode devolver o imóvel antes do término do prazo, sujeitando-se, em regra, ao pagamento **da multa pactuada**."

Trecho incompleto (verbatim, seção "A dispensa da multa por transferência de trabalho" + FAQ):
> "...o locatário fica liberado da penalidade quando a devolução do imóvel decorre de **transferência determinada pelo seu empregador**." (sem a condição de aviso)

Texto oficial (Planalto L8245, verificado 2026-07-22):
> "Art. 4º ... o locatário, todavia, poderá devolvê-lo, pagando a multa pactuada, **proporcionalmente ao período de cumprimento do contrato**, ou, na sua falta, a que for judicialmente estipulada. (Redação dada pela Lei nº 12.112/2009)
> Parágrafo único. O locatário ficará dispensado da multa se a devolução do imóvel decorrer de transferência, pelo seu empregador, privado ou público, ... **e se notificar, por escrito, o locador com prazo de, no mínimo, trinta dias de antecedência**."

Correção autoral executável (enriquecer, sem remover):
1. Multa: "...sujeitando-se ao pagamento da multa pactuada **reduzida proporcionalmente ao período já cumprido do contrato** (ou, na falta de multa, à que o juiz fixar)."
2. Dispensa: acrescentar que a isenção **exige notificação por escrito ao locador com antecedência mínima de 30 dias** e transferência para localidade diversa da do início do contrato — não é automática.

## RESSALVAS MATERIAIS (CLEAR, mas recomenda-se enriquecer — sem apagar)
- **idx 22 (Art. 443 CLT):** o caput vigente admite três modalidades — "por prazo determinado ou indeterminado, **ou para prestação de trabalho intermitente**" (Lei 13.467/2017). A prosa cita só duas. Afirmação feita é verdadeira; falta a modalidade intermitente. Recomendo acrescentá-la.
- **idx 48 (Art. 62 Inquilinato):** a prosa explica bem a purga da mora (15 dias), mas omite o limite vigente do parágrafo único: "Não se admitirá a emenda da mora se o locatário já houver utilizado essa faculdade **nos 24 (vinte e quatro) meses** imediatamente anteriores à propositura da ação" (Lei 12.112/2009). Recomendo acrescentar a trava temporal.

## OBSERVAÇÃO DE QUALIDADE (thin content — não é grounding, mas barra publicação)
- **idx 35** (Art. 47) e **idx 33** (Art. 7º) têm **section bodies VAZIOS** (só heading + opening + FAQ preenchidos). Reprovariam gate de thin/HTML-leve. Sinalizo para o dono da geração; não é FIX de conteúdo (as partes preenchidas estão corretas).

## RESIDUAL (do residual — 19 idx sem veredito semântico, para a W3)
idx **4, 6, 8, 9, 11, 12, 14, 20, 23, 28, 30, 31, 34, 37, 38, 39, 44, 49, 53**.
Perfil: institucionais/definicionais (idx 6 CLT, 8/14/23/34/39/44 CDC, 9 Inquilinato, 37 L8213, 49 CC) e estruturais de baixo risco numérico (idx 12/20/38 boa-fé/função social/abuso; 30/31/53 inadimplemento/reparação/ato ilícito; 4 união estável; 28 fim da sociedade conjugal). **Prioridade W3:** idx 11 (Art. 483 CLT — rescisão indireta, rol a-g enumerável) e idx 28 (Art. 1.571 CC — hipóteses de dissolução). Nenhum pode ser promovido sem auditoria individual.
Fora deste canal: 4 re-redação (3/21/27/52) + 42 quarentenados fail-closed (`entity_prose_quarantine_20260721.jsonl`).

## COLLISION-SAFETY NOTE
- **READ-ONLY cumprido.** Nenhuma edição em `data/editorial/`, `data/ops/`, `v2ingest.go` ou `validate.go`; nenhum git; nenhum build Go/suíte. Só Grep/Read + `curl`/`iconv`/`sed` em `/tmp` (fora do repo) e python3 read-only sobre o JSONL. web_fetch para páginas grandes (arquivos no host, lidos por Grep).
- **Saída única:** este arquivo. Nada mais escrito. idx 47 é **recomendação** de roteamento a `prosas-4-reredacao` (agora candidato a 5º/6º item), não alteração aplicada.
- Vereditos ancorados em texto oficial LIVE do Planalto (2026-07-22). Armadilhas idx 40/33 conferidas byte-a-byte para não repetir o falso-positivo Fable da Onda 1.
