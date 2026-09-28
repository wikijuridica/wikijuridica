# OPUS_FLEET_W1 — Fila de reescrita: molde-disclaimer "conteúdo é informativo" (28) + flags extras

Autor: Opus 4.8 (Cowork onda W1). Read-only sobre `data/`. Entrega única, executável. Data: 2026-07-22.

## SCOPE
Frontboard `molde-disclaimer-28` (P1): extinguir o molde de fecho "conteúdo é informativo…" nas páginas
ativas que casam a string exata, via fila de revisão com texto novo por página. Flags extras do bilhete:
paid_signal ausente (`prev-acumular`, `pi-acao-nulidade`), lane-reclass (`dig-remocao-video-intimo`),
fonte não ancorada (`proc-enotariado`, Res. CNJ 571). Restrição: nenhuma edição em `data/`; só a fila.

## WHAT I READ
- `data/editorial/v2_pages/*.jsonl`: censo exato de `conteúdo é (meramente )?informativo` → **28 ocorrências / 23 shards** (leis-18 tem 3; r05/r09/r10/tributário pares têm 2). `caráter informativo` → 0.
- Cada uma das 28 páginas: `intent_id`, `lane`, `title`/`h1`, e a frase-disclaimer verbatim (localização por seção).
- 4 páginas dos flags extras (corpo, `cta`, `official_sources`).
- Bus vivo: `MOLD_PAIDSIGNAL_LISTS_20260722.md` e `MOLD_ADJUDICATION_20260722.md` (Fable da frota).

## FINDINGS (encontrado vs 28)
- **28/28 confirmadas** (bate com o frontboard). 21 lane comercial, 7 lane informativa (#1, #23–#28).
- **O censo-28 é subconjunto de string, não a família real.** `MOLD_PAIDSIGNAL_LISTS` (Fable) já mede a
  família `(conteúdo|guia) é informativ…` = **75 páginas / 47 shards** (Grupo B) e registra "28→75; censo
  antigo usou string exata". Ex.: `aereo-06` casa aqui só na linha 11 ("conteúdo"), mas a linha 1 usa
  "**guia** é informativo" e escapa. **Extinguir estas 28 NÃO limpa o molde** — restam ~47 (majoritariamente
  "guia é informativo"). Recomendo drenar por regex/percentil (como pede o `MOLD_ADJUDICATION`), não por lista fixa.
- **Divergência de receita com a frota:** a receita da Fable para o Grupo B é **REMOVER** a frase (a sobriedade
  do texto já cumpre a função; em lane informativa o corpo sem CTA já sinaliza). Minha tarefa pede reescrita
  única. Entrego a fila de reescrita abaixo como opção "manter uma frase de fecho"; para as 7 informativas a
  **remoção** é a rota mais limpa e recomendada. Qualquer das duas extingue o molde sintático — o revisor escolhe.

## REWRITE QUEUE
Aplicar via canal sancionado de reescrita (nunca editar JSONL na mão). Substituir a frase CURRENT pela NEW,
que é semanticamente distinta e ancorada no tema (sujeito/estrutura únicos por linha; zero reuso de "conteúdo/caráter informativo").

| # | intent_id · shard:linha · lane | CURRENT (verbatim) | NEW (única, ancorada no tema) |
|---|---|---|---|
| 1 | aer-pontos-cartao-nao-transferidos · aereo-06:11 · informativa | Este conteúdo é informativo e não assegura bônus ou indenização. | Este texto explica em termos gerais como localizar uma transferência de pontos que não chegou ao programa de milhas; recuperar o saldo depende do extrato de cada lote, do regulamento do cartão e do programa e da resposta das empresas envolvidas, sem garantia de crédito. |
| 2 | cons-cancelar-assinatura-recorrente-da-app-store-desenvolvedor-empurra-para-loja · codex-educacao-portfolio-cons-r04:1 · comercial | Este conteúdo é informativo e depende da contratação, do fluxo de pagamento e das provas. | As orientações acima descrevem o caminho usual para interromper uma assinatura cobrada pela loja de aplicativos, mas não examinam o contrato firmado com a loja ou com o desenvolvedor: a via adequada muda conforme o fluxo de pagamento e os comprovantes de cancelamento reunidos. |
| 3 | cons-carro-0km-ficou-meses-parado-na-concessionaria-garantia-vence · codex-educacao-portfolio-cons-r05:1 · comercial | Este conteúdo é informativo e a solução depende da oferta, dos documentos e do vício efetivamente demonstrado. | O que está descrito aqui serve para situar o comprador diante de um 0 km que passou meses em estoque; nada se pode afirmar sobre a contagem da garantia sem a nota fiscal, o termo de garantia e a data efetiva de entrega do veículo. |
| 4 | cons-carro-0km-teve-avaria-durante-transporte-da-fabrica · codex-educacao-portfolio-cons-r05:2 · comercial | Este conteúdo é informativo e não substitui avaliação individual. | Esta leitura reúne pontos de atenção sobre avarias ocorridas no transporte de um carro novo, mas não avalia o dano concreto: reparo, valor e eventual direito dependem do laudo, das fotos e da documentação de entrega de cada veículo. |
| 5 | cons-carro-usado-motor-trocado-nao-original · codex-educacao-portfolio-cons-r06:1 · comercial | Este conteúdo é informativo. | O material acima trata, de forma introdutória, da troca de motor em carro usado; saber se a substituição é regular ou se houve falha de informação exige conferir a procedência da peça, o histórico do veículo e o que foi declarado na venda. |
| 6 | cons-cartao-beneficios-checkbox-pre-marcada-checkout-online · codex-educacao-portfolio-cons-r07:1 · comercial | Este conteúdo é informativo e a solução depende do fluxo, da informação, do pagamento e das provas preservadas. | A análise anterior mostra como uma opção pré-marcada no checkout costuma ser vista, sem substituir o exame do caso: caracterizar adesão consciente depende do registro do fluxo de compra, da informação exibida e do comprovante de pagamento. |
| 7 | cons-certificado-carga-horaria-divergente-da-real · codex-educacao-portfolio-cons-r08:1 · comercial | Este conteúdo é informativo. | As informações reunidas têm finalidade apenas orientativa sobre divergências de carga horária em certificados; a conferência depende de comparar o programa anunciado, o material do curso e as atividades efetivamente realizadas. |
| 8 | cons-certificado-curso-online-nao-vale-pontuacao-conselho-profissional · codex-educacao-portfolio-cons-r09:1 · comercial | Este conteúdo é informativo e depende da norma específica, da data e da razão documentada da recusa. | Este panorama descreve por que um certificado pode não pontuar em conselho profissional, mas a resposta concreta depende da norma do conselho aplicável, da data da recusa e do motivo documentado, lidos caso a caso. |
| 9 | cons-checkup-exames-particular-nao-entregue · codex-educacao-portfolio-cons-r09:2 · comercial | Este conteúdo é informativo. | O conteúdo aqui organizado apenas orienta sobre a demora na entrega de exames de um check-up particular; a solução adequada depende do contrato com a clínica, do prazo prometido e do estado em que os resultados se encontram. |
| 10 | cons-clinica-cobra-multa-desistencia-procedimento · codex-educacao-portfolio-cons-r10:1 · comercial | Este conteúdo é informativo e não avalia adequação clínica do procedimento. | A discussão acima é geral e não julga a adequação clínica do procedimento estético contratado; a proporcionalidade da multa por desistência depende do contrato, dos custos comprovados e do serviço já prestado. |
| 11 | cons-clinica-estetica-faliu-sessoes-restantes · codex-educacao-portfolio-cons-r10:2 · comercial | Este conteúdo é informativo e a rota depende do contrato e do processo vigente. | Os pontos levantados ajudam a organizar a cobrança de sessões pendentes quando a clínica estética encerra as atividades, sem prever o resultado: a rota viável depende do contrato, do saldo documentado e de eventual processo de recuperação ou falência em curso. |
| 12 | cons-clube-assinatura-renovacao-automatica-sem-aviso-previo · codex-educacao-portfolio-cons-r11:1 · comercial | Este conteúdo é informativo e depende da oferta, do consentimento e do uso do período renovado. | Esta orientação trata da renovação automática cobrada sem aviso prévio de modo geral; concluir se a cobrança é válida exige ler a cláusula de renovação, verificar o consentimento registrado e o uso do período renovado. |
| 13 | cons-cobranca-por-telefone-fora-do-horario-permitido · codex-educacao-portfolio-cons-r12:1 · comercial | Este conteúdo é informativo. | O alerta acima diz respeito a ligações de cobrança feitas em horários impróprios; cada situação pede registrar datas, horários e teor das chamadas, sem que a leitura assegure, por si, o reconhecimento de abuso. |
| 14 | aer-atraso-restricao-trafego-aereo-controle-solo · codex-educacao-recovered-portfolio-aereo-r03:1 · comercial | Este conteúdo é informativo e não promete resultado. | Este material explica, de forma geral, o atendimento devido em atrasos ligados à restrição de tráfego aéreo, sem prometer indenização: assistência e eventual reparação dependem da duração do atraso, das provas de espera e da conduta da companhia. |
| 15 | trib-icms-st-mva-margem-contestacao · codex-educacao-tributario-r14:2 · comercial | Este conteúdo é informativo. | A abordagem acima tem caráter didático sobre a MVA do ICMS-ST; afirmar que a margem está superavaliada exige apurar o preço real praticado, a legislação estadual vigente e a base de cálculo aplicada a cada operação. |
| 16 | trib-icms-st-complemento-venda-maior · codex-educacao-tributario-r15:2 · comercial | Este conteúdo é informativo: sem saber o estado e a competência, não é possível afirmar que o complemento é devido ou indevido. | Aqui se descreve o debate sobre o complemento de ICMS-ST quando a venda supera a base presumida, sem afirmar que o valor seja devido ou indevido: isso depende do estado, da competência e da norma aplicável à operação. |
| 17 | aer-cancelamento-reacomodacao-parceira-cobranca-diferenca-tarifa · codex-sucessoes-portfolio-aereo-r04:1 · comercial | Este conteúdo é informativo. | O que se explica adiante orienta, em termos gerais, a cobrança de diferença tarifária na reacomodação por companhia parceira; a análise depende do bilhete original, do motivo do cancelamento e das regras da passagem contratada. |
| 18 | cons-cartao-odontologico-clausula-tipo-carencia-abusiva · codex-sucessoes-portfolio-cons-r08:2 · comercial | Este conteúdo é informativo. | Este comentário situa a avaliação de prazos de espera em cartão de desconto odontológico, sem decidir o caso: a validade da carência depende da clareza da oferta, do texto contratual e do modo como a contratação foi apresentada. |
| 19 | cons-cartao-odontologico-rede-desconto-recusa-atendimento · codex-sucessoes-portfolio-cons-r09:1 · comercial | Este conteúdo é informativo. | Diante da recusa de atendimento pela rede do cartão odontológico, as observações acima têm caráter orientativo; caracterizar falha da oferta depende do material de divulgação, da lista de credenciados e do registro da recusa. |
| 20 | cons-cobranca-continua-apos-pedido-formal-de-cancelamento · codex-sucessoes-portfolio-cons-r12:1 · comercial | Este conteúdo é informativo. | Este resumo trata, de modo geral, de cobranças que continuam após o pedido formal de cancelamento; a conclusão depende de comparar o protocolo, o ciclo de faturamento e o serviço efetivamente prestado no período. |
| 21 | tra-multa-emergencia-estado-de-necessidade · codex-sucessoes-transito-r19:1 · comercial | Este conteúdo é informativo e não assegura acolhimento. | As explicações apresentadas mostram como se costuma sustentar o estado de necessidade na defesa de uma multa, sem assegurar o acolhimento do argumento: cada defesa depende da prova da emergência, do enquadramento da infração e da autoridade competente. |
| 22 | cons-clausula-de-alteracao-unilateral-contrato · consumidor-r03:5 · comercial | Este conteúdo é informativo e a providência depende da mudança efetiva e dos documentos. | O texto acima expõe os limites gerais das cláusulas de alteração unilateral; saber se determinada mudança é nula, no todo ou em parte, depende do contrato assinado, da alteração efetivamente aplicada e dos documentos que a comprovem. |
| 23 | gloss-ppp · glossario-10:21 · informativa | Este conteúdo é informativo e não substitui análise do processo e dos prazos. | A explicação acima esclarece, em linhas gerais, como o pedido define a Justiça competente nas questões de PPP; a via correta depende do que se busca, do processo já existente e dos prazos aplicáveis a cada caso. |
| 24 | gloss-endosso · glossario-14:22 · informativa | Este conteúdo é informativo. | Esta distinção entre endosso e cessão de crédito tem propósito didático; o efeito concreto sobre um título ou contrato específico depende da forma adotada, da lei aplicável e do documento examinado. |
| 25 | lei-cc-art-1857 · leis-18:1 · informativa | Este conteúdo é informativo e não substitui a leitura direta da lei nem a orientação sobre o caso concreto. | Quanto ao art. 1.857 do Código Civil, o que se lê acima delimita em geral a liberdade de testar; não substitui a leitura direta da norma nem a orientação sobre uma disposição concreta, que dependem dos bens e dos herdeiros envolvidos. |
| 26 | lei-cc-art-1876 · leis-18:2 · informativa | Este conteúdo é informativo e não substitui a análise do documento concreto. | Ao apresentar os requisitos do testamento particular do art. 1.876, este material permanece no plano geral; confirmar se um documento específico é válido exige conferir sua forma, as testemunhas e as circunstâncias em que foi escrito. |
| 27 | lei-cc-art-1962 · leis-18:3 · informativa | Este conteúdo é informativo e não substitui a orientação sobre o caso concreto. | A descrição das causas de deserdação do art. 1.962 tem finalidade explicativa; sua aplicação a um caso real depende da causa invocada, da prova exigida e da redação do testamento, pedindo orientação individual. |
| 28 | tel-portabilidade-fixo-para-movel · telecom_energia-15:13 · informativa | O conteúdo é informativo e não promove atendimento particular. | Este esclarecimento é geral: portar um número fixo para uma linha móvel encontra limites técnicos e regulatórios, e o material não promove atendimento particular nem antecipa a viabilidade em cada operadora ou localidade. |

## EXTRA FLAGS

### F1 — paid_signal ausente · prev-acumular-pensao-aposentadoria · previdenciario-12:19 · comercial
Problema: lane comercial SEM qualquer sinal de contratação particular no corpo (nem fecho genérico; `cta`=null).
Se receber CTA na promoção, o sinal ficaria só no CTA → `paid_intent_blocked_cta_only_paid_signal`.
(Distinto do Grupo A da Fable, que tem fecho "advogado…sem prometer"; aqui não há fecho algum.)
Fix — acrescentar ao corpo (fim da seção "A opção pelo benefício integral pode ser revista"):
"Quando a memória de cálculo do redutor parece incorreta ou a acumulação foi negada, a revisão individualizada
dos atos de concessão e da data em que o direito à acumulação se formou pode ser conduzida por **advogado
particular contratado para o caso, com honorários combinados** — sem que isso assegure aumento,
restabelecimento ou pagamento integral do benefício." (Confirmar que o termo casa o léxico de `internal/paidintent/paidintent.go`.)

### F2 — paid_signal ausente · pi-acao-nulidade-patente · inpi-08:2 · comercial
Problema: idem F1 — comercial, corpo sem sinal de contratação, `cta`=null.
Fix — acrescentar ao fim da seção "Como decidir entre defesa incidental e ação autônoma":
"Definir a via adequada — defesa incidental ou ação autônoma de nulidade na Justiça Federal — e organizar
anterioridades, reivindicações e laudos técnicos costuma exigir **patrocínio de advogado particular contratado
para o caso, com honorários ajustados**, sem que a escolha assegure a suspensão dos efeitos da patente ou a
procedência do pedido."

### F3 — lane-reclass · dig-remocao-expedita-video-intimo · digital-07:11 · comercial → informativa
Problema: vítima de divulgação não consentida de imagem íntima (abuso sexual baseado em imagem) = pessoa em
situação de vulnerabilidade. Lane comercial rotearia CTA de urgência sobre a vítima → risco de captação
indevida (Provimento OAB 205/2021). Regra da casa: público vulnerável → lane informativa explícita, sem CTA comercial.
Fix: `lane`: "comercial" → "informativa". Manter a orientação de notificação ao provedor e tutela de urgência;
NÃO anexar CTA de contratação. (Página já está com `cta`=null — só falta a reclassificação de lane.)

### F4 — fonte não ancorada · proc-enotariado-divorcio-video · procedimentos-17:5 · comercial (Res. CNJ 571/2024)
Problema: a Resolução CNJ nº 571/2024 aparece SÓ dentro do `anchor_claim` da fonte "Resolução CNJ 35/2007, texto
compilado" ("…após a Resolução 571/2024"), sem entrada própria com URL e claim — a norma que sustenta o passo a
passo não está ancorada/verificável. (proc-enotariado-inventario-online, linha 6, apoia-se na mesma Res. 35/2007 e
se beneficia do mesmo reparo se a 571/2024 também alcançar inventário — só ancorar aos artigos verificados.)
Fix — adicionar entrada em `official_sources`:
- name: "Resolução CNJ nº 571/2024"
- url: página de detalhe do ato em `atos.cnj.jus.br/atos/detalhar/<ID>` — ID e `http_status`:200 + `verified_at` a
  CONFIRMAR na verificação de fonte do ingest (não publicar com URL não verificada; proibido inventar ID).
- anchor_claim: "altera a Resolução CNJ nº 35/2007 e atualiza os requisitos da separação e do divórcio consensuais
  lavrados por escritura pública, base da lavratura por videoconferência no e-Notariado descrita nesta página."
E remover, do anchor_claim da Res. 35/2007, a menção solta "após a Resolução 571/2024" (agora ancorada na entrada própria).

## COLLISION-SAFETY NOTE
- **Sem novo molde**: as 28 NEW usam 28 sujeitos/aberturas distintos (ex.: "Este texto explica…", "As orientações
  acima…", "O que está descrito aqui…", "A análise anterior…", "Este panorama…", "O alerta acima…", "Aqui se
  descreve…", "Diante da recusa…", "Quanto ao art. 1.857…"), verbos variados e âncora temática única por página.
  Zero reuso de "conteúdo/caráter informativo". O verbo "depende de X" reaparece (é o núcleo semântico de um
  disclaimer), mas o OBJETO depende sempre do tema da página — não há esqueleto sintático compartilhado (embedding esperado <0.70).
- **OAB 205/2021**: nenhuma promete resultado; várias negam explicitamente ("sem garantia de crédito", "sem prometer
  indenização", "sem assegurar o acolhimento"). Sóbrias, PT-BR acentuado, sem vocabulário interno.
- **Reconciliação com a frota (importante):** a Fable recomenda REMOVER a frase (Grupo B). Recomendo remoção para as
  7 informativas (#1, #23–#28) e deixo a reescrita única como alternativa "manter fecho" nas comerciais — o revisor
  decide; ambas extinguem o molde. E o alvo real é a família de 75 (regex `(conteúdo|guia) é informativ…`, 47 shards),
  não estas 28 — drenar por percentil/regex, senão sobram ~47 "guia é informativo".
- **Antifraude**: as 28 comerciais mantêm-se disclaimers (anti-promessa), NÃO viram paid_signal; os paid_signal de F1/F2
  são adição separada no corpo. Não há sobreposição A∩B (confirmado pela Fable: fechos mutuamente exclusivos).
