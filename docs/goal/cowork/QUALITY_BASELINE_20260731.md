# QUALITY BASELINE — Auditoria adversarial Fable, 2026-07-31

Fiscal de qualidade Fable 5 (read-only em `data/`). Leitura de TEXTO REAL de 24 páginas + varredura
sistêmica do corpus inteiro (7.964 registros em `data/editorial/v2_pages/`, 7.843 páginas ativas,
121 stubs skip; 289 páginas em `data/editorial/v2_blocked_drafts/`). Check verde não substitui
leitura: tudo abaixo foi lido na íntegra, com verificação jurídica offline (conhecimento até jan/2026)
e dúvidas sinalizadas explicitamente.

**Escala:** APTA = publicável como está · APTA-COM-RESSALVA = publicável só após correção pontual
nomeada · DEFEITO-P0 = falha bloqueante (invenção, molde, vazamento, promessa, truncamento).

## Placar

| Grupo | APTA | APTA-COM-RESSALVA | DEFEITO-P0 | wc médio |
|---|---|---|---|---|
| A — recém-promovidas hoje (8) | 4 | 4 | 0 | ~583 |
| B — estoque antigo (8) | 6 | 2 | 0 | ~642 |
| C — represados blocked_drafts (8) | 5 | 3 | 0 | ~1.084 |
| **Total amostra (24)** | **15** | **9** | **0** | — |

Fora da amostra, na varredura de corpus: **1 DEFEITO-P0 real** (vazamento de vocabulário interno em
`bancario-10.jsonl`, ver S2) e 1 stub não-página sorteado em `consumidor-28.jsonl` (ver achados menores).

## Veredito por página

### Grupo A — recém-promovidas (glossario2-14, autonomos-w3-01, telecom_energia-16, lgpd-25)

1. **glossario2-14 L1 `gloss-lgpd`** (informativa, 390) — **APTA-COM-RESSALVA.** Dois erros objetivos
   em página definicional: (i) chama a ANPD de "**Agência** Nacional de Proteção de Dados" — o nome
   oficial é **Autoridade** Nacional de Proteção de Dados (LGPD art. 55-A); (ii) quebra de
   concordância "Toda coleta, armazenamento, **compartilhado** ou eliminação" (→ compartilhamento).
   Resto correto (EC 115/2022, art. 5º LXXIX CF; arts. 1º/6º/7º LGPD; vigência 2020).
2. **glossario2-14 L12 `gloss-anonimizacao`** (informativa, 320) — **APTA.** Arts. 5º XI, 12 caput/§1º/§2º
   e 13 §4º LGPD conferem; exemplo concreto; FAQ distingue pseudonimização corretamente.
3. **lgpd-25 L1 `lgpd-camera-vizinho-aponta-minha-casa`** (comercial, 1.285) — **APTA.** Forte: exceção
   doméstica (art. 4º LGPD) explicada sem exagerar a LGPD; arts. 5º X CF, 21 e 1.277 CC, 206 §3º V CC
   corretos; seção de limite ("câmera só para o próprio terreno") é anti-captação exemplar; fecho
   comercial sóbrio e coerente com a lane.
4. **autonomos-w3-01 L1 `acon-b2b-monitoria`** (comercial, 720) — **APTA-COM-RESSALVA.** Direito correto
   (art. 700/701 CPC, honorários reduzidos, conversão em título, prescrição 206 §5º I/II). Ressalvas:
   nome de fonte visível sem acento ("**Codigo** de Processo Civil (Lei **no** 13.105/2015)") e a
   formulação frouxa "inversão do ônus de mover a ação".
5. **autonomos-w3-01 L10 `acon-distrato-multa-perdas`** (comercial, 667) — **APTA.** Arts. 416 caput/p.u.,
   412, 413 CC e 373 CPC exatos; didática de piso/teto correta; fecho coerente.
6. **autonomos-w3-01 L18 `acon-resp-clausula-limitacao`** (comercial, 402) — **APTA-COM-RESSALVA.**
   Abre com "Em geral sim, ..." respondendo pergunta que o H1 não formulou (coesão de abertura);
   direito correto (421-A por Lei 13.874/2019; 927 CC; hedge honesto de doutrina/jurisprudência).
7. **telecom_energia-16 L1 `ene-tarifa-social-quem-tem-direito`** (informativa, 392) — **APTA-COM-RESSALVA
   (desatualização).** Descreve o desconto "por faixa... mais generoso nas primeiras faixas e
   reduzindo-se conforme o consumo aumenta" — regime ANTERIOR à Lei 15.235/2025. A página irmã no
   MESMO shard (L3) afirma corretamente que a redação vigente da Lei 12.212 dá **100% até 80 kWh** à
   faixa tradicional. Inconsistência normativa intra-shard; atualizar antes de release.
8. **telecom_energia-16 L3 `ene-conta-de-luz-gratis-baixa-renda`** (informativa, 487) — **APTA.**
   Atual e precisa: Lei 15.235/2025 (conversão da MP 1.300/2025), isenção CDE até 120 kWh para faixa
   ½–1 SM a partir de 2026-01-01, distinção TSEE × isenção de cota CDE bem explicada.

### Grupo B — estoque antigo (áreas variadas)

9. **bancario-03 L11 `banc-conta-e-divida-abertas-com-meus-documentos`** (comercial, 646) —
   **APTA-COM-RESSALVA (lane).** Conteúdo sólido (Súmula 479 STJ aplicada certo, Registrato, 206 §3º V);
   porém lane=comercial **sem nenhum sinal de contratação no corpo** — se o render anexa CTA WhatsApp
   pela lane, viola `paid_intent_blocked_cta_only_paid_signal`. Reclassificar ou escrever fecho.
10. **bancario-11 L8 `banc-penhora-poupanca-40-salarios`** (comercial, 792) — **APTA.** Art. 833 X e IV,
    §2º (alimentos; excedente de 50 SM) exatos; soma de contas, extensão a outras aplicações tratada
    com hedge honesto; fecho coerente.
11. **familia-05 L5 `fam-lar-de-referencia`** (informativa, 426) — **APTA-COM-RESSALVA.** Parêntese meta
    vazando no corpo público: "(**numeração usual**: art. 1583, combinado com o art. 1584...)" — nota
    de editor, não texto de leitor; formatação de artigo inconsistente (1.583/1583). Conteúdo correto
    (art. 1.583 §3º CC).
12. **familia-14 L1 `fam-desfazer-paternidade-socioafetiva`** (comercial, 828) — **APTA.** Arts. 1.610 e
    178 I/II CC exatos; distinção arrependimento × vício exemplar; actio nata marcada como construção
    pretoriana (honestidade rara). Dúvida leve a conferir online: numeração arts. 505/506 do CNN
    (Provimento CNJ 149/2023). Fecho comercial ético ("avaliar se há chance ou simples arrependimento").
13. **consumidor-07 L11 `cons-devolucao-proporcional-cancelamento-no-meio-do-ciclo`** (informativa, 402) —
    **APTA.** Art. 884 CC correto e bem aplicado; equilíbrio (cláusula clara pode valer). Nota: frase
    confusa sobre JEC "somados a outros consumidores" (lógica coletiva em rito individual).
14. **tributario-06 L1 `trib-autuacao-icms-estadual-defesa`** (comercial, 991) — **APTA.** CTN arts. 145,
    149, 151 III; Decreto 70.235/1972; LC 87/1996; MS 120 dias — tudo confere; honesto sobre variação
    estadual; exemplo de glosa de crédito concreto. Sinal de contratação só na FAQ (fraco, mas presente).
15. **aereo-04 L17 `aer-objeto-esquecido-aviao-achados-perdidos`** (informativa, 605) — **APTA.** Distingue
    corretamente achados-e-perdidos de bagagem extraviada (Res. ANAC 400); CC arts. 1.233–1.237 corretos;
    voz mais staccato que o resto do corpus (variação de safra de redator, não defeito). RBAC 108 Emd 08:
    específico e datado; conferência online recomendada.
16. **consumidor-05 L17 `cons-couvert-nao-pedido-cobrado`** (informativa, 444) — **APTA.** CDC art. 6º III
    e art. 39 III + p.u. (amostra grátis) corretos; seção "quando a cobrança é legítima" equilibra.

### Grupo C — represados (v2_blocked_drafts, campo `page`)

17. **aereo-09 L1 `aer-pacote-operadora-alterou-datas`** (comercial, 1.348) — **APTA.** CDC arts. 30, 35,
    51 XIII/IV, 26, 27; Lei 11.771/2008 com redação da **Lei 14.978/2024**; CC 393 — tudo confere.
    Página rica, contra-seção honesta, fecho condicionado. Bloqueio = "BLOQUEIO DE SISTEMA (global da
    onda W4, não da página)".
18. **seguros-06 L1 `seg-vida-cobeneficiario-premorto`** (comercial, 1.211) — **APTA.** Lei 15.040/2024
    (vigente dez/2025) aplicada com sofisticação; tese do acréscimo (CC 1.942–1.944) autoqualificada
    como interpretativa — honestidade exemplar. Dúvida pontual a conferir online: §§ do art. 115 e
    arts. 86/87/126-III da lei nova. Bloqueio = CASMismatch (drift de dependência).
19. **bancario-w3-01 L1 `banc-golpe-valores-a-receber-bc-taxa-liberacao`** (comercial, 942) —
    **APTA-COM-RESSALVA.** Erro verificável: "para valores de até 40 salários mínimos, o JEC **dispensa
    advogado até esse limite**" — a dispensa vai até **20 SM** (Lei 9.099 art. 9º); 40 SM é teto de
    competência. Resto forte (SVR gratuito, Súmula 479, art. 14 CDC, contra-seção de culpa exclusiva).
20. **bancario-w3-01 L12 `banc-rj-revisional-financiamento-imovel-sfh`** (comercial, 727) — **APTA.**
    Sóbrio, correto no nível de generalidade escolhido (Lei 9.514/1997 + CDC); não promete redução de
    juros — diz o oposto. Fontes de lei inteira sem âncora `#art` (especificidade menor que os pares).
21. **lgpd-22 L1 `lgpd-anular-consentimento-por-dark-pattern`** (comercial, 1.466) — **APTA.** Precisão
    notável: art. 8º §§1º–5º, art. 9º §1º, art. 18 VI/VII/§5º, art. 7º (10 hipóteses), CDC art. 46 —
    tudo confere; voz própria; contra-seção tripla. Das melhores páginas do corpus.
22. **familia-25 L1 `fam-violencia-contra-idoso-na-familia`** (informativa, 982) — **APTA-COM-RESSALVA
    (verificação online obrigatória).** Estatuto arts. 4º, 19 caput/§1º, 98, 102, 44/45 e ação pública
    incondicionada conferem. A afirmação de que a **Lei 15.163/2025** elevou a pena do art. 99 para
    reclusão 2–5 anos (3–7 se lesão grave) é específica e plausível, mas **não confirmável offline** —
    checar contra o compilado Planalto antes de release. Lane informativa coerente (Disque 100,
    canais públicos, zero CTA).
23. **consumidor-w3-01 L1 `cons-superend-home-equity-risco-perder-imovel`** (comercial, 839) —
    **APTA-COM-RESSALVA.** Atribui o processo de repactuação ao "art. 54-A do CDC" — o rito é do
    **art. 104-A** (que a própria página cita corretamente na frase seguinte e na FAQ). Corrigir uma
    frase. Resto muito bom (exclusão de garantia real, Decreto 11.150/2022 art. 6º p.u., valor do
    mínimo existencial deixado evergreen de propósito).
24. **saude-16 L1 `saude-sus-procedimento-nao-ofertado-custeio`** (informativa, 1.153) — **APTA.**
    Página exemplar: Decreto 7.508/2011 arts. 8º/9º/20/21/22/24, Lei 8.080 arts. 19-M II/19-N II,
    CF arts. 198/196/23 II — tudo confere; fila × ausência de oferta é distinção que quase nenhum
    conteúdo concorrente faz; lane informativa perfeita (Defensoria/MP, sem CTA comercial).

## Recém-promovidas × estoque antigo × represadas

- **Não há decadência — há melhora.** As safras mais novas (w3 e represadas W4) são mais longas
  (~1.084 vs ~600 palavras), com contra-seções ("onde a tese perde força") sistemáticas, hedges
  honestos sobre jurisprudência e leis novas (Lei 15.040/2024, Lei 14.978/2024, Lei 15.235/2025) que
  o estoque antigo não usava. As duas melhores páginas da amostra (lgpd-22, saude-16) estão REPRESADAS.
- As ressalvas das recém-promovidas são de tipo diferente: **atualização normativa e nomes** (ANPD,
  regime da tarifa social), não estrutura. O estoque antigo tem mais problemas de **coerência de
  lane** e resíduos de edição (parêntese meta).
- Todas as 8 represadas foram bloqueadas por **defeito de infraestrutura** (contrato semântico/CAS/
  StockEpoch), nenhuma por qualidade. O represamento retém produto acima da média.
- Anti-template: esqueleto editorial comum (problema → fundamento → documentos → caminho → limites →
  FAQ) é house style, não molde verbal — headings repetidos no corpus são raros em termos absolutos
  (pior caso: "Documentos que sustentam o pedido" 32× em 7.843 ≈ 0,4%) e os 4 pares de abertura
  repetida têm corpos distintos (Jaccard 3-gram ≤ 0,044).

## Top-5 problemas sistêmicos (com camada de origem)

**S1 — 874 de 3.477 páginas lane=comercial (25%) sem NENHUM sinal de contratação no corpo**
(regex ampla: advogad|contratar|honorári|atendimento particular/digital|whatsapp). Exemplos:
`administrativo-r02.jsonl` (8 páginas), `aereo-01.jsonl` (atraso de voo — casos clássicos de
contratação), `bancario-03.jsonl` L11 (amostrada). Se o render anexa CTA WhatsApp pela lane, cada uma
viola `paid_intent_blocked_cta_only_paid_signal`; se não anexa, a lane está superdimensionada.
*Camada: classificador de lane no catálogo de intents + gate paid-intent (não cruza lane↔corpo hoje).*
Correção executável: check novo `lane=comercial ⇒ sinal no corpo` e, por lote, reescrever fecho ou
reclassificar para informativa.

**S2 — Vazamento de vocabulário interno em texto público (DEFEITO-P0, 1 página):**
`bancario-10.jsonl`, intent `banc-adimplemento-substancial-busca-apreensao`, corpo contém
"**Na lane comercial**, uma análise jurídica particular pode organizar a resposta...". Único hit do
corpus (grep integral). *Camada: redator (taxonomia vazou do prompt) + gate anti-vocabulário (lexicon
não contém "lane").* Correção: editar a frase + adicionar `lane`, `intent`, `shard` ao lexicon do gate.

**S3 — Desatualização/inconsistência normativa entre páginas que citam a MESMA lei.**
Caso provado: `telecom_energia-16` L1 descreve o regime de faixas pré-2025 da Lei 12.212 enquanto L3
(mesmo shard) descreve a redação vigente pós-Lei 15.235/2025 (100% até 80 kWh). Agravante: claims
legislativos de 2025 não verificáveis offline (Lei 15.163/2025 em `familia-25`) sem data/âncora de
compilado na fonte. *Camada: redator (snapshots de lei divergentes entre ondas) + gate de fonte (não
valida concordância normativa entre páginas do mesmo estatuto).* Correção: check de consistência por
estatuto citado + fila de recheck online para toda lei ≥2024 citada com pena/valor/percentual.

**S4 — Erros jurídicos pontuais e verificáveis em páginas de resto excelentes** (4 na amostra de 24):
"Agência" → **Autoridade** Nacional de Proteção de Dados (`glossario2-14`); JEC "dispensa advogado
até 40 SM" → **20 SM** (`bancario-w3-01`); repactuação "criada pelo art. 54-A" → **art. 104-A**
(`consumidor-w3-01`); "compartilhado" → compartilhamento (`glossario2-14`). *Camada: redator; o gate
de citação não cobre nome de órgão nem limites processuais consagrados.* Correção barata: check
lexical de armadilhas recorrentes (nomes de órgãos, 20/40 SM, 54-A/104-A, detenção/reclusão).

**S5 — 289 páginas prontas 100% represadas por defeito de sistema, qualidade acima da média.**
Distribuição de `blocked_reason`: 206× ValueError "candidato semantico... owner nao e globalmente
exato e unico", 14× StockEpochError, 12× source_hints não materializados, 8× CAS de lote, 8× bloqueio
global W4, 3× CASMismatch... Zero bloqueios editoriais. Amostra de 8: 5 APTA / 3 ressalva, wc médio
~1.084. *Camada: pipeline CAS/contrato semântico — engenharia, não conteúdo.* Produto pago parado:
drenar a fila é a alavanca de estoque mais barata que existe (páginas já escritas e já boas).

## Achados menores (não-top-5)

- 121 stubs `{"skipped": true, ...}` dentro do canônico `v2_pages` (pior: `cidadania-04` com 20).
  Os contadores tratam (`reconcile_v2_strict_source_stock.py` conta como tombstones), mas qualquer
  consumidor novo do shard precisa filtrar; o sorteio desta auditoria caiu num deles (`consumidor-28` L1).
- 41 nomes de fonte visíveis sem acento ("Codigo", "Constituicao") — PT-BR público degradado se renderizado.
- 1 página lane=informativa com fecho de contratação: `imobiliario-13` `imob-quorum-alterar-convencao`
  ("pode ser feita por advogado particular... enviada digitalmente") — reclassificar ou cortar a frase.
  (Outros 2 hits da regex eram falso-positivos: menções neutras a advogado+certificado digital.)
- Pares de abertura repetida (molde só na 1ª frase; corpos distintos): bancario-03 (2 intents de fraude),
  glossario-12 × imobiliario-17 (usucapião extrajudicial — vigiar canibalização de SERP, mesma intenção
  respondida em 2 áreas), previdenciario-r02 × procedimentos-06 (isenção IR doença grave), 
  tributario-inf1 × tributario-r09 (COSIP).
- Ética OAB: **zero** promessa de resultado, preço-chamariz ou captação nas 24 páginas; contra-seções
  "quando o pedido não prospera" funcionam como antídoto estrutural. Fecho comercial varia de redação
  (sem molde: "advogado particular" no último bloco de só 17% das comerciais) e é sempre condicionado.

## Metodologia (reproduzível)

Amostra determinística (hash md5 do nome do shard mod nº de linhas) para o estoque antigo; recém-
promovidas conforme escopo da missão; represadas incluindo aereo-09, seguros-06, bancario-w3-01.
Varredura de corpus em python (nice 19): lanes, sinal de contratação no corpo, headings repetidos,
aberturas duplicadas + Jaccard 3-gram, lexicon interno (rascunho/seed/lane/noindex/etc.), thin
(<280 palavras: **zero**), acentuação de fontes, causas de bloqueio. Verificação jurídica offline
contra conhecimento consolidado; toda dúvida está sinalizada no veredito da página, nunca omitida.
