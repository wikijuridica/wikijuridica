# OPUS_FLEET_W1 — prosas-4-reredacao (idx 52 / 27 / 3 / 21)

Autor: `claude-cowork-opus-fleet` (Opus 4.8, onda Cowork W1). Escopo QUEUED disjunto
`prosas-4-reredacao` (P1, fora do caminho 10k). Entrega READ-ONLY, executável: para cada
uma das 4 prosas de entidade com erro material CONFIRMADO byte-a-byte, a frase errada
VERBATIM + a frase autoral corrigida ancorada no artigo REAL + o texto do artigo (fonte
oficial planalto.gov.br, verificado ao vivo em 2026-07-22) + URL.

NÃO editei `data/editorial/` nem `data/ops/` nem nenhum dado do repo; NÃO toquei
`v2ingest.go`/`validate.go`; NÃO commitei; NÃO rodei build/suíte Go. Só leitura + fetch.

---

## SCOPE

- **Fonte das 4 prosas:** `data/ops/entity_prose_grounded_20260721.jsonl` (54 registros,
  commit `4f5954d0`, quarentena `0a21044e`). O `idx` do censo do fiscal é **0-based** = nº da
  linha (0-based) do JSONL. Mapeamento confirmado lendo os títulos das 54 linhas:
  - `idx 3`  (linha 4)  → `epd-cand-9a49524a9fbfacb1` — "Art. 5º do CDC" — redator `prosa2-1`.
  - `idx 21` (linha 22) → `epd-cand-75c8800331dcfc27` — "Art. 3º da CLT" — redator `prosa2-7`.
  - `idx 27` (linha 28) → `epd-cand-8f68449bc517b9b8` — "Art. 59 da Lei do Inquilinato" — redator `prosa2-9`.
  - `idx 52` (linha 53) → `epd-cand-c5c922297714845f` — "Art. 74 da Lei 8.213/91" — redator `prosa2-17`.
- Todas as 4 estão `index_policy=noindex`, `publication_allowed=false` (quarentena correta).
- Erros já apontados pelo fiscal Fable (`docs/goal/cowork/FISCAL_TERMINAL_20260722.md`, §1);
  esta entrega os RE-VERIFICA ao vivo contra planalto e entrega a reescrita ancorada.
- **Causa-raiz sistêmica (não corrigível aqui):** corpus com stub de 25–89 bytes servindo como
  "Lei 8.213"/"Lei 8.245" (ver `CORPUS_STUB_CENSUS_20260722.md`). Reescrever o texto NÃO basta
  se a promoção não exigir blob-fonte ≥1KB + conferência contra a redação VIGENTE. As reescritas
  abaixo já vêm ancoradas na redação vigente para o gate T3.

## WHAT I READ

- Os 4 registros integrais (title, h1, meta, opening, sections, faq) de
  `data/ops/entity_prose_grounded_20260721.jsonl` (idx 3, 21, 27, 52).
- `p0_frontboard.jsonl:33` (task) + `coordination/bus.jsonl` (ondas do fiscal 1440/1442/1451/1461).
- `FISCAL_TERMINAL_20260722.md` §1 (tabela de erros) e `FISCAL_TERMINAL_20260722B.md`.
- **Fonte oficial (planalto.gov.br), fetch ao vivo 2026-07-22 (accessed 2026-07-22):**
  - CLT art. 3º — `del5452compilado.htm` (texto capturado verbatim).
  - CDC art. 5º — `l8078compilado.htm` (I a VII + §§ vetados, verbatim).
  - Lei 8.245/91 art. 59 — `l8245.htm` (caput + §1º, incisos I–IX, verbatim).
  - Lei 8.213/91 art. 74, I — via lei alteradora `L13846.htm` (redação vigente, verbatim) +
    cross-check `WebSearch` (STJ, jusbrasil, legjur). O `l8213cons.htm` veio truncado no art. 21
    pelo tamanho da página, por isso a prova do art. 74 vem da L13.846/2019 (que deu a redação).

---

## PER-PAGE CORRECTIONS (4)

### 1) idx 52 — `epd-cand-c5c922297714845f` — Art. 74 da Lei 8.213/91 (pensão por morte)

**Erro material:** a prosa apresenta o prazo de **180 dias** para retroação ao óbito como
**regra geral, para todos os dependentes**. A redação vigente (art. 74, I, com redação da Lei
13.846/2019) só dá 180 dias aos **filhos menores de 16 anos**; para os **demais dependentes**
(cônjuge, companheiro etc.) o prazo é de **90 dias**. Erro contamina meta, um heading de seção,
o corpo dessa seção e uma pergunta do FAQ.

**Frase(s) errada(s) VERBATIM (da prosa):**
- Heading: `Pedido em até 180 dias: benefício desde o óbito`
- Corpo: `Quando o pedido é feito em até cento e oitenta dias após o óbito, o benefício retroage à data da morte, alcançando o período desde o falecimento. Trata-se da hipótese mais favorável aos dependentes, que preserva o direito ao intervalo entre o óbito e o requerimento.`
- Meta: `O art. 74 da Lei nº 8.213/1991 define quando a pensão por morte é devida aos dependentes: prazo de 180 dias, pedido tardio e morte presumida.`
- FAQ Q: `Por que os 180 dias fazem diferença na pensão por morte?` — A: `Quando o pedido é feito dentro desse prazo, a pensão retroage à data do óbito. Fora dele, o benefício passa a ser devido apenas a partir da data do requerimento.`

**Frase(s) autoral(is) corrigida(s) (ancorada no art. 74, I):**
- Heading: `Pedido no prazo — 90 dias, ou 180 dias para filho menor de 16 anos: benefício desde o óbito`
- Corpo: `Quando o requerimento é apresentado em até 90 dias após o óbito, o benefício retroage à data da morte para os demais dependentes; esse prazo sobe para 180 dias apenas em favor dos filhos menores de 16 anos. Feito o pedido dentro do prazo aplicável a cada dependente, a pensão alcança todo o período desde o falecimento — é a hipótese mais favorável, que preserva o intervalo entre o óbito e o requerimento.`
- Meta: `O art. 74 da Lei nº 8.213/1991 fixa quando começa a pensão por morte: retroação ao óbito se o pedido é feito em até 90 dias (180 dias para filhos menores de 16 anos), início na data do pedido tardio e início na decisão de morte presumida.`
- FAQ Q: `Qual é o prazo para a pensão por morte retroagir à data do óbito?` — A: `Para os demais dependentes, o pedido precisa ser feito em até 90 dias após o óbito; para os filhos menores de 16 anos, o prazo é de 180 dias. Dentro desse prazo, a pensão retroage à data da morte; fora dele, passa a ser devida apenas a partir da data do requerimento.`

**Texto do artigo que prova (planalto — redação vigente dada pela Lei 13.846/2019):**
> Art. 74. [A pensão por morte será devida ao conjunto dos dependentes do segurado que
> falecer, aposentado ou não, a contar da data:] **I - do óbito, quando requerida em até 180
> (cento e oitenta) dias após o óbito, para os filhos menores de 16 (dezesseis) anos, ou em
> até 90 (noventa) dias após o óbito, para os demais dependentes; II - do requerimento, quando
> requerida após o prazo previsto no inciso I do caput deste artigo; ou III - da decisão
> judicial, na hipótese de morte presumida.**

- URL (redação vigente): https://www.planalto.gov.br/ccivil_03/_Ato2019-2022/2019/Lei/L13846.htm#art24 — accessed 2026-07-22.
- URL (consolidado): https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm#art74 — accessed 2026-07-22.
- Cross-check ao vivo: STJ, 1ª Seção (10/06/2026) fixou que pensão de menor pedida após 180
  dias não retroage — confirma que o prazo de retroação é limite legal, não regra geral de 180d.

---

### 2) idx 27 — `epd-cand-8f68449bc517b9b8` — Art. 59 da Lei 8.245/91 (liminar de despejo)

**Erro material (3 pontos):** o tema (despejo/rito + liminar em 15 dias) está certo, mas:
(a) a prosa escreve `rescisão do contrato` onde a lei diz rescisão do **contrato de trabalho**
(hipótese do art. 47, II — locação atrelada ao emprego); a supressão de "de trabalho" **troca o
sentido**; (b) omite que a caução é **de três meses de aluguel**; (c) omite o prazo de **trinta
dias** para a hipótese de temporada.

**Frase errada VERBATIM (da prosa, seção "Quando cabe a liminar..."):**
`Entre elas estão o descumprimento de acordo de desocupação feito por escrito e assinado pelas partes; a situação prevista no art. 47 quando há prova escrita da rescisão do contrato; e o término do prazo da locação para temporada, quando a ação é proposta logo após o encerramento do período contratado. Em todos os casos, a lei condiciona a medida à prestação de caução.`

**Frase autoral corrigida (ancorada no art. 59, §1º, I–III):**
`Entre essas hipóteses estão: o descumprimento do acordo de desocupação feito por escrito e assinado pelas partes e por duas testemunhas; a retomada do art. 47, inciso II, quando há prova escrita da rescisão do contrato de trabalho que vinculava a locação ao emprego; e o término do prazo da locação para temporada, desde que a ação de despejo seja proposta em até trinta dias após o vencimento do contrato. Em todos os casos, a liminar depende de o locador prestar caução no valor equivalente a três meses de aluguel.`

(Ajustes de coerência: no opening e no FAQ, trocar `prestação de caução` por `caução equivalente
a três meses de aluguel`.)

**Texto do artigo que prova (planalto — Lei 8.245/91, art. 59):**
> Art. 59. Com as modificações constantes deste capítulo, as ações de despejo terão o rito
> ordinário. § 1º Conceder-se-á liminar para desocupação em quinze dias, independentemente da
> audiência da parte contrária e **desde que prestada a caução no valor equivalente a três meses
> de aluguel**, nas ações que tiverem por fundamento exclusivo: I - o descumprimento do mútuo
> acordo (art. 9º, inciso I), celebrado por escrito e assinado pelas partes e por duas
> testemunhas, no qual tenha sido ajustado o prazo mínimo de seis meses para desocupação (...);
> **II - o disposto no inciso II do art. 47, havendo prova escrita da rescisão do contrato de
> trabalho ou sendo ela demonstrada em audiência prévia; III - o término do prazo da locação
> para temporada, tendo sido proposta a ação de despejo em até trinta dias após o vencimento do
> contrato;** (...)

- URL: https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art59 — accessed 2026-07-22.

---

### 3) idx 3 — `epd-cand-9a49524a9fbfacb1` — Art. 5º do CDC (instrumentos da PNRC)

**Erro material:** a prosa fecha o rol de instrumentos no inciso IV (juizados), com "Por fim",
e o FAQ enumera os quatro como se fosse a lista completa. Faltam o **inciso V** (estímulos às
Associações de Defesa do Consumidor) e os **incisos VI e VII** (mecanismos e núcleos de
prevenção/tratamento do superendividamento, incluídos pela **Lei 14.181/2021**). Além disso,
ignora que o **caput** diz "os seguintes instrumentos, **entre outros**" (rol exemplificativo).

**Frase(s) errada(s) VERBATIM (da prosa):**
- Seção: `Por fim, o art. 5º aponta a criação de Juizados Especiais de Pequenas Causas e de Varas Especializadas para a solução de litígios de consumo. A finalidade é oferecer caminhos de julgamento mais ágeis e adequados às particularidades das relações de consumo, aproximando a resposta judicial da realidade dessas disputas.`
- FAQ A: `O texto aponta a assistência jurídica integral e gratuita ao consumidor carente, as Promotorias de Justiça de Defesa do Consumidor no Ministério Público, delegacias de polícia especializadas em infrações penais de consumo e juizados e varas especializados para julgar litígios de consumo.`
- Meta: `O art. 5º do CDC lista os instrumentos do poder público para a Política Nacional das Relações de Consumo, da assistência jurídica gratuita aos juizados.`

**Frase(s) autoral(is) corrigida(s) (ancorada no art. 5º, I–VII):**
- Seção: `O art. 5º aponta ainda a criação de Juizados Especiais de Pequenas Causas e de Varas Especializadas para a solução de litígios de consumo; a concessão de estímulos à criação e ao desenvolvimento das Associações de Defesa do Consumidor; e, por força da Lei nº 14.181/2021, a instituição de mecanismos de prevenção e tratamento judicial e extrajudicial do superendividamento e de núcleos de conciliação e mediação desses conflitos. O próprio caput deixa a lista aberta, ao falar em "os seguintes instrumentos, entre outros".`
- FAQ A: `O texto aponta a assistência jurídica integral e gratuita ao consumidor carente; as Promotorias de Justiça de Defesa do Consumidor no Ministério Público; delegacias de polícia especializadas em infrações penais de consumo; Juizados Especiais e Varas especializadas para julgar litígios de consumo; estímulos às Associações de Defesa do Consumidor; e, desde a Lei 14.181/2021, mecanismos e núcleos de tratamento do superendividamento. O caput é expresso ao dizer que são instrumentos "entre outros", ou seja, a lista é exemplificativa.`
- Meta: `O art. 5º do CDC elenca os instrumentos do poder público para a Política Nacional das Relações de Consumo — da assistência jurídica gratuita às Associações de Defesa do Consumidor e ao combate ao superendividamento (Lei 14.181/2021).`

**Texto do artigo que prova (planalto — Lei 8.078/90, art. 5º):**
> Art. 5° Para a execução da Política Nacional das Relações de Consumo, contará o poder público
> com os seguintes instrumentos, **entre outros**: I - manutenção de assistência jurídica,
> integral e gratuita para o consumidor carente; II - instituição de Promotorias de Justiça de
> Defesa do Consumidor, no âmbito do Ministério Público; III - criação de delegacias de polícia
> especializadas no atendimento de consumidores vítimas de infrações penais de consumo; IV -
> criação de Juizados Especiais de Pequenas Causas e Varas Especializadas para a solução de
> litígios de consumo; **V - concessão de estímulos à criação e desenvolvimento das Associações
> de Defesa do Consumidor;** **VI - instituição de mecanismos de prevenção e tratamento
> extrajudicial e judicial do superendividamento e de proteção do consumidor pessoa natural;
> (Incluído pela Lei nº 14.181, de 2021) VII - instituição de núcleos de conciliação e mediação
> de conflitos oriundos de superendividamento. (Incluído pela Lei nº 14.181, de 2021)** § 1°
> (Vetado). § 2º (Vetado).

- URL: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art5 — accessed 2026-07-22.

---

### 4) idx 21 — `epd-cand-75c8800331dcfc27` — Art. 3º da CLT (conceito de empregado)

**Erro material:** a definição de empregado na prosa **omite o elemento "e mediante salário"**
(onerosidade), presente no caput do art. 3º. A omissão aparece na meta, no opening, na seção que
"enumera os elementos" (lista só pessoa física, não eventualidade e subordinação) e no FAQ. Sem
onerosidade, a definição fica juridicamente incompleta.

**Frase(s) errada(s) VERBATIM (da prosa):**
- Opening: `Segundo o dispositivo, empregado é a pessoa física que presta serviços de natureza não eventual a um empregador, sob dependência deste.`
- Meta: `O art. 3º da CLT define quem é empregado: a pessoa física que presta serviços não eventuais e subordinados ao empregador.`
- Seção "Os elementos...": `E a prestação ocorre sob dependência do empregador, elemento que a doutrina lê como subordinação. É a soma desses elementos que revela a existência de vínculo empregatício.`
- FAQ A: `Ele define quem é empregado: a pessoa física que presta serviços não eventuais e subordinados a um empregador. É a norma que caracteriza a relação de emprego.`

**Frase(s) autoral(is) corrigida(s) (ancorada no caput do art. 3º):**
- Opening: `Segundo o dispositivo, empregado é a pessoa física que presta serviços de natureza não eventual a um empregador, sob a dependência deste e mediante salário. É esse artigo que separa o vínculo de emprego de outras formas de trabalho: sem pessoa física, não eventualidade, subordinação e onerosidade — o pagamento de salário —, não há relação empregatícia.`
- Meta: `O art. 3º da CLT define quem é empregado: a pessoa física que presta serviços não eventuais, subordinados e mediante salário (de forma onerosa) a um empregador.`
- Seção "Os elementos...": `E a prestação ocorre sob a dependência do empregador — subordinação — e mediante salário, isto é, de forma onerosa. É a soma desses elementos, inclusive a contraprestação salarial, que revela a existência de vínculo empregatício.`
- FAQ A: `Ele define quem é empregado: a pessoa física que presta serviços não eventuais, subordinados e mediante salário a um empregador. É a norma que caracteriza a relação de emprego, cujos requisitos incluem a onerosidade.`

**Texto do artigo que prova (planalto — Decreto-Lei 5.452/43 — CLT, art. 3º):**
> Art. 3º - Considera-se empregado toda pessoa física que prestar serviços de natureza não
> eventual a empregador, sob a dependência deste **e mediante salário**. Parágrafo único - Não
> haverá distinções relativas à espécie de emprego e à condição de trabalhador (...).

- URL: https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm#art3 — accessed 2026-07-22.

---

## VERIFICATION EVIDENCE

| idx | artigo | fonte oficial (planalto) | achado verificado ao vivo |
|---|---|---|---|
| 52 | art. 74, I, L8.213 | L13846.htm#art24 (redação vigente) + l8213cons.htm | "180 dias" só p/ filhos < 16; "90 dias" p/ demais dependentes. Confirmado verbatim + STJ 10/06/2026. |
| 27 | art. 59, §1º, L8.245 | l8245.htm | Caução = "três meses de aluguel"; inc. II = rescisão do **contrato de trabalho**; inc. III temporada = "até trinta dias". Verbatim. |
| 3 | art. 5º, CDC (L8.078) | l8078compilado.htm | Caput "entre outros"; incisos I–VII, com V (Associações) e VI/VII (superendividamento, L14.181/2021). Verbatim. |
| 21 | art. 3º, CLT (DL5.452) | del5452compilado.htm | Caput inclui "e mediante salário". Verbatim (linhas 71–72 do fetch). |

- Método: fetch direto planalto.gov.br (páginas em latin-1; acentos normalizados para o
  português canônico nas citações acima — o conteúdo é fiel ao oficial). Onde a página do
  consolidado veio truncada (L8.213, art. 74 além do corte), a prova veio da lei alteradora
  L13.846/2019 (que fixa a redação vigente) + cross-check WebSearch (STJ/jusbrasil/legjur).
- 4/4 páginas localizadas; 4/4 artigos verificados ao vivo; 4/4 erros confirmados; 4/4 reescritas
  entregues ancoradas no texto oficial.

## COLLISION-SAFETY NOTE

- **READ-ONLY cumprido:** nenhuma edição em `data/editorial/`, `data/ops/`, `v2ingest.go`,
  `validate.go`; nenhum `git`; nenhum build/suíte Go. Só Read/Grep/Bash-read-only/web_fetch e
  este único Write.
- **Único artefato escrito:** `docs/goal/cowork/OPUS_FLEET_W1_prosas4_20260722.md` (UNTRACKED).
  Handoff para a onda ativa landar por pathspec quando liberar o lock de commit.
- **Não apliquei** as reescritas na fonte `entity_prose_grounded_20260721.jsonl` (fora do meu
  escopo READ-ONLY e a quarentena deve permanecer até o corpus ser saneado — blob-fonte <1KB é a
  causa-raiz, ver `CORPUS_STUB_CENSUS_20260722.md`/`CORPUS_RECOLLECTION_PLAN_20260722.md`). Quem
  aplicar deve: (1) reescrever os 4 registros com os textos acima; (2) só promover com blob-fonte
  ≥1KB + gate T3 conferindo claim numérico/prazo contra a redação VIGENTE (flag "Redação dada
  pela Lei..."). As 4 continuam `noindex`/`publication_allowed=false` até isso.
- Sem conflito com o fiscal Fable: esta entrega converte o achado dele (FISCAL_TERMINAL §1) em
  patch de conteúdo executável, sem tocar os arquivos que ele stageou.
