#!/usr/bin/env python3
"""Reescreve as páginas 13 a 17 do shard imobiliário-09."""

from _tmp_fix_imobiliario_09_lib import apply_updates, section, source


EXPECTED_SHA256 = "38fdb9971f58fd9d9e1e557b706d2f82bd319eb75fbbaf56d00f8ca89624684c"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
CTN = "https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm"


UPDATES = {
    "imob-fraude-execucao-comprador": {
        "opening": (
            "Comprar imóvel de pessoa demandada não torna a venda automaticamente fraudulenta, mas uma alienação pode "
            "ser ineficaz perante o credor quando se enquadra no artigo 792 do CPC. Para imóveis, registro de penhora, "
            "averbação da execução e prova de má-fé são elementos centrais no regime comum. A Súmula 375 protege a boa-fé "
            "sem dispensar diligência concreta. Execução fiscal segue regra especial: o Tema 290 do STJ liga a fraude à "
            "inscrição em dívida ativa, mesmo sem penhora registrada, nas alienações posteriores à mudança de 2005."
        ),
        "sections": [
            section(
                "O artigo 792 descreve situações diferentes",
                "Há fraude quando a alienação ocorre durante ação fundada em direito real ou pretensão reipersecutória cuja "
                "pendência foi averbada; quando consta averbação da execução ou de constrição; quando tramitava contra o "
                "devedor ação capaz de reduzi-lo à insolvência e se demonstram os requisitos; ou em outra hipótese prevista "
                "em lei. A consequência é ineficácia do negócio em relação ao exequente, não nulidade universal da compra.\n\n"
                "Datas importam: distribuição, citação, averbação, contrato, pagamento e registro precisam entrar na mesma "
                "linha do tempo. Processo de pequeno valor, com patrimônio suficiente reservado, não produz o mesmo quadro de "
                "uma venda que esvazia o único bem do executado."
            ),
            section(
                "Súmula 375 presume boa-fé quando a constrição não foi registrada",
                "No regime civil comum, o STJ afirma que o reconhecimento da fraude depende do registro da penhora do bem "
                "alienado ou da prova de má-fé do terceiro. Sem registro, cabe ao credor demonstrar que o adquirente conhecia "
                "a demanda capaz de levar o vendedor à insolvência. Averbação premonitória ou da própria ação muda a publicidade "
                "e reduz o espaço para alegar desconhecimento.\n\nA súmula não autoriza ignorar sinais evidentes. Parentesco, "
                "preço incompatível, posse mantida pelo vendedor, pagamentos sem rastreabilidade e conhecimento documentado do "
                "processo podem compor a prova. Certidão limpa ajuda, mas não neutraliza ciência real da fraude."
            ),
            section(
                "Execução fiscal é a exceção de maior impacto",
                "O Tema Repetitivo 290 decidiu que, para ato translativo praticado a partir de 9 de junho de 2005, basta a "
                "inscrição do crédito tributário em dívida ativa para configurar fraude nos termos do artigo 185 do CTN, se "
                "o devedor não reserva bens ou rendas suficientes ao pagamento. A boa-fé do comprador e a ausência de penhora "
                "na matrícula não afastam por si esse regime.\n\nPara atos anteriores à alteração legal, o marco adotado pelo "
                "Tema é a citação. Certidão fiscal, data da inscrição e patrimônio remanescente precisam ser verificados; não "
                "basta aplicar mecanicamente a data de uma execução encontrada depois da compra."
            ),
            section(
                "O terceiro deve ser ouvido antes da declaração",
                "O parágrafo quarto do artigo 792 manda intimar o terceiro adquirente antes de declarar a fraude, permitindo "
                "que apresente embargos de terceiro no prazo legal. Nessa defesa, contrato, registro, comprovantes de preço, "
                "posse, certidões e comunicações podem demonstrar cronologia e boa-fé. A decisão examina a eficácia perante o "
                "credor, e não entrega automaticamente indenização contra o vendedor.\n\nSe a compra perde eficácia, podem "
                "existir pretensões contratuais ou de evicção contra quem alienou, conforme ciência do risco e conteúdo do "
                "negócio. Esses pedidos não substituem a defesa urgente da constrição."
            ),
            section(
                "Diligência proporcional deve ser documentada",
                "Obtenha matrícula recente, pesquise averbações, confira vendedor e cônjuge, identifique processos relevantes e "
                "certidões fiscais quando o risco justificar. A Lei 13.097 fortalece a concentração na matrícula, com exceções "
                "legais, mas não protege má-fé comprovada nem afasta o CTN. Registre fontes, datas e interpretação de cada achado.\n\n"
                "Uma revisão jurídica deve separar execução comum, fiscal e eventual fraude contra credores. Não prometa que "
                "matrícula limpa torna qualquer compra imune ou que processo em nome do vendedor invalida automaticamente o título."
            ),
        ],
        "faq": [
            {"q": "Sem penhora registrada nunca existe fraude à execução?", "a": "Não. No regime comum pode haver prova de má-fé; na execução fiscal, o Tema 290 prevê regra especial ligada à inscrição em dívida ativa."},
            {"q": "Fraude à execução torna a venda nula para todos?", "a": "Não. O efeito típico do artigo 792 é a ineficácia da alienação perante o credor exequente."},
        ],
        "official_sources": [
            source(CPC + "#art792", "Código de Processo Civil, art. 792", "hipóteses, efeito e contraditório do terceiro na fraude à execução"),
            source("https://www.stj.jus.br/docs_internet/revista/eletronica/stj-revista-sumulas-2013_33_capSumula375.pdf", "STJ, Súmula 375", "registro da penhora ou prova de má-fé no regime comum"),
            source("https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=290&cod_tema_inicial=290&novaConsulta=true&tipo_pesquisa=T", "STJ, Tema Repetitivo 290", "marco da inscrição em dívida ativa na fraude à execução fiscal posterior a 2005"),
            source("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13097.htm#art54", "Lei 13.097/2015, art. 54", "concentração de atos na matrícula e proteção do terceiro de boa-fé com exceções"),
        ],
    },
    "imob-fraude-credores-vs-execucao": {
        "opening": (
            "Fraude contra credores e fraude à execução protegem o crédito por caminhos diferentes. A primeira é defeito "
            "do negócio previsto no Código Civil e, em regra, exige ação pauliana proposta por credor legitimado. A segunda "
            "surge nas hipóteses do artigo 792 do CPC durante atividade processual e torna a alienação ineficaz perante o "
            "exequente. Não basta dizer que uma ocorre antes e outra depois do processo: anterioridade do crédito, insolvência, "
            "publicidade registral, má-fé e natureza da execução definem o enquadramento."
        ),
        "sections": [
            section(
                "Fraude contra credores parte de crédito anterior",
                "Os artigos 158 a 165 do Código Civil protegem credores que já eram titulares de crédito ao tempo do ato. "
                "Transmissão gratuita ou remissão de dívida pode ser anulável quando o devedor já era insolvente ou se torna "
                "insolvente pelo ato. Em contrato oneroso, o artigo 159 exige que a insolvência fosse notória ou houvesse motivo "
                "para o outro contratante conhecê-la.\n\nPreço de mercado e certidões podem apoiar boa-fé, mas não resolvem toda "
                "a prova. Vínculo próximo, esvaziamento patrimonial, pagamento fictício e permanência do bem com o devedor ajudam "
                "a demonstrar intenção e conhecimento. Credor posterior, em regra, não usa a pauliana para atacar ato anterior ao "
                "seu próprio crédito."
            ),
            section(
                "A ação pauliana tem partes, prazo e efeito próprios",
                "O credor quirografário prejudicado, e também quem recebeu garantia insuficiente, pode buscar a anulação do negócio "
                "fraudulento. A demanda deve alcançar as pessoas indicadas pela disciplina civil, permitindo contraditório ao "
                "adquirente. O artigo 178, inciso II, estabelece prazo decadencial de quatro anos contado da realização do negócio "
                "jurídico para anular por fraude contra credores.\n\nA procedência recompõe a garantia patrimonial em benefício do "
                "conjunto legitimado, segundo os artigos civis; não entrega automaticamente o imóvel ao autor como pagamento. "
                "Antes de propor, é preciso demonstrar crédito, anterioridade, prejuízo patrimonial e requisitos do ato gratuito ou oneroso."
            ),
            section(
                "Fraude à execução opera dentro de relação processual",
                "O artigo 792 lista averbação de ação real, averbação da execução ou constrição, demanda capaz de levar à insolvência "
                "e outras hipóteses legais. O efeito é a ineficácia perante o exequente, permitindo que a execução alcance o bem "
                "apesar da alienação. No regime comum de imóveis, a Súmula 375 liga o reconhecimento ao registro da penhora ou à "
                "prova de má-fé.\n\nO terceiro deve ser intimado antes da declaração e pode apresentar embargos. Isso diferencia a "
                "técnica processual da ação pauliana autônoma, embora um mesmo negócio possa gerar discussões alternativas se os "
                "fatos preencherem regimes distintos."
            ),
            section(
                "Crédito tributário segue o artigo 185 do CTN",
                "Em alienações posteriores a 9 de junho de 2005, o Tema 290 do STJ considera a inscrição em dívida ativa como "
                "marco suficiente da fraude à execução fiscal quando não há reserva patrimonial. A regra não depende da Súmula 375 "
                "nem da prova de má-fé do comprador. Por isso, classificar toda venda apenas como fraude civil ou execução comum "
                "pode produzir conclusão errada.\n\nÉ necessário identificar natureza do credor, data do ato, data da inscrição, "
                "citação quando pertinente e bens remanescentes. Dívida fiscal do próprio imóvel também pode ter efeitos propter rem "
                "distintos da fraude na alienação."
            ),
            section(
                "Um quadro comparativo orienta a defesa",
                "Para cada crédito, registre origem, nascimento, vencimento, processo, citação, averbação e valor. Para a venda, "
                "registre proposta, preço, pagamento, posse, escritura e registro. Em seguida classifique: ação pauliana, incidente "
                "de fraude à execução, execução fiscal ou ausência dos requisitos.\n\nO comprador pode precisar defender o bem e, "
                "se perder eficácia ou validade do negócio, cobrar o vendedor. O credor precisa escolher a via e respeitar o prazo. "
                "A análise não deve prometer proteção só porque não havia processo visível nem anulação só porque o vendedor tinha dívidas."
            ),
        ],
        "faq": [
            {"q": "Fraude contra credores depende de penhora registrada?", "a": "Não. Ela segue os requisitos dos artigos 158 a 165 do Código Civil e é discutida por ação pauliana."},
            {"q": "O prazo da ação pauliana é de dois anos?", "a": "Não. O artigo 178, II, prevê decadência de quatro anos para anulação por fraude contra credores."},
        ],
        "official_sources": [
            source(CC + "#art158", "Código Civil, arts. 158 a 165", "requisitos e efeitos civis da fraude contra credores"),
            source(CC + "#art178", "Código Civil, art. 178, II", "prazo decadencial de quatro anos da ação anulatória"),
            source(CPC + "#art792", "Código de Processo Civil, art. 792", "hipóteses e ineficácia da fraude à execução"),
            source(CTN + "#art185", "Código Tributário Nacional, art. 185", "regime especial da alienação após inscrição em dívida ativa"),
        ],
    },
    "imob-venda-ascendente-descendente": {
        "opening": (
            "A venda de ascendente a descendente é anulável se não houver consentimento expresso dos outros descendentes "
            "e do cônjuge do vendedor. A regra do artigo 496 busca impedir favorecimento oculto, mas não transforma uma venda "
            "real em adiantamento de herança. Colação é própria da doação feita a descendente, nos termos do artigo 544. Para "
            "uma compra e venda genuína, preço, pagamento e consentimentos precisam ser documentados; negócio simulado pode ser "
            "tratado conforme sua verdadeira natureza."
        ),
        "sections": [
            section(
                "Todos os demais descendentes e o cônjuge entram na regra",
                "Se o pai vende a um filho, os outros filhos devem consentir. Havendo descendente de grau mais próximo, a análise "
                "da família e de eventual representação precisa ser feita sem presumir que apenas herdeiros nomeados em testamento "
                "participam. O cônjuge do alienante também consente, ainda que não existam outros descendentes.\n\nO parágrafo único "
                "dispensa o consentimento do cônjuge somente quando o regime de bens é o da separação obrigatória. Não se deve ampliar "
                "o texto para toda separação convencional ou usar a expressão vaga separação absoluta. Estado civil e regime devem "
                "ser comprovados por certidão e pacto quando houver."
            ),
            section(
                "Consentimento deve acompanhar a forma do negócio",
                "O artigo 220 do Código Civil determina que a anuência necessária à validade de um ato deve ser dada na mesma forma "
                "exigida para ele. Se a compra requer escritura pública, o consentimento precisa integrar ou observar essa forma; "
                "conversa familiar, mensagem ambígua ou testemunho de ciência não oferecem a mesma segurança. A manifestação deve "
                "identificar imóvel, comprador, preço e negócio.\n\nRecusa de um descendente não autoriza substituição judicial genérica "
                "do consentimento previsto no artigo 496. As partes podem escolher outra organização patrimonial lícita, mas não "
                "devem simular preço ou assinatura."
            ),
            section(
                "Venda verdadeira não vai automaticamente à colação",
                "Na venda, o descendente paga contraprestação e adquire o bem. Na doação, o artigo 544 presume adiantamento do que lhe "
                "cabe por herança, salvo disciplina sucessória aplicável. Se o preço da suposta venda nunca é pago, retorna ao comprador "
                "sem causa ou fica muito abaixo do valor com outros sinais, herdeiros podem alegar simulação ou doação disfarçada.\n\n"
                "Avaliação independente, transferência bancária rastreável, capacidade financeira e quitação coerente ajudam a provar "
                "realidade. Ainda assim, preço baixo isolado não decide o processo sem contexto e perícia."
            ),
            section(
                "A falta de consentimento gera anulabilidade e prazo de dois anos",
                "O negócio produz efeitos enquanto não for anulado. Como o artigo 496 não fixa prazo próprio, aplica-se o artigo 179: "
                "dois anos contados da conclusão do ato para pleitear anulação. Não se conta automaticamente da morte do ascendente ou "
                "da descoberta pelo irmão. Depois de sentença, o cancelamento do registro segue ordem dirigida ao cartório.\n\nOutros "
                "defeitos, como simulação, incapacidade ou violação da legítima, têm fundamentos e prazos que não devem ser confundidos "
                "com a simples falta de anuência. A decadência do artigo 179 não valida fraude diferente apenas por receber o rótulo de venda."
            ),
            section(
                "A escritura deve refletir a operação real",
                "Reúna certidões da família, regime de bens, matrícula, avaliação, comprovantes de preço e consentimentos. Informe ao "
                "tabelião a relação de parentesco e evite declarações padronizadas incompatíveis com os fatos. Se algum descendente é "
                "incapaz, a operação exige cautela adicional e eventual controle judicial conforme seus interesses.\n\nUma revisão "
                "sucessória e imobiliária pode separar venda, doação, partilha em vida e planejamento patrimonial, sem anunciar que "
                "assinaturas eletrônicas informais ou concordância posterior sempre curam o ato."
            ),
        ],
        "faq": [
            {"q": "Venda real de pai para filho é adiantamento de herança?", "a": "Não automaticamente. A colação é regra da doação; venda efetiva exige preço e pagamento reais, além dos consentimentos do artigo 496."},
            {"q": "Separação convencional dispensa consentimento do cônjuge?", "a": "O parágrafo único do artigo 496 menciona especificamente o regime de separação obrigatória."},
        ],
        "official_sources": [
            source(CC + "#art496", "Código Civil, art. 496", "anulabilidade, consentimentos exigidos e exceção da separação obrigatória"),
            source(CC + "#art179", "Código Civil, art. 179", "prazo de dois anos para anulação quando a lei não fixa outro"),
            source(CC + "#art220", "Código Civil, art. 220", "forma do consentimento necessário ao ato"),
            source(CC + "#art544", "Código Civil, art. 544", "doação a descendente como adiantamento da herança"),
        ],
    },
    "imob-venda-sem-outorga-conjugal": {
        "opening": (
            "Salvo no regime da separação absoluta, um cônjuge não pode alienar ou gravar imóvel sem autorização do outro, "
            "conforme o artigo 1.647 do Código Civil. A exigência não se limita a bem comum ou à meação: alcança imóvel particular "
            "do cônjuge alienante, porque protege a organização patrimonial da família. A falta torna o ato anulável, não nulo de "
            "pleno direito, e existe disciplina própria de prazo, confirmação e legitimidade. União estável exige análise diferente "
            "para proteger terceiro de boa-fé quando a convivência não tinha publicidade."
        ),
        "sections": [
            section(
                "Outorga alcança alienação e ônus real",
                "Venda, doação, hipoteca e outros gravames imobiliários entram no inciso I do artigo 1.647. O regime de separação "
                "absoluta é a exceção expressa. Não basta afirmar que o imóvel foi adquirido antes do casamento ou recebido por "
                "herança: essas circunstâncias podem afastar comunicação patrimonial, mas não eliminam por si a autorização exigida "
                "para dispor do imóvel.\n\nCertidão de casamento atualizada e pacto antenupcial mostram o regime. Procuração ou "
                "consentimento precisam identificar poderes e forma adequados; assinatura do cônjuge apenas como testemunha pode não "
                "demonstrar outorga consciente."
            ),
            section(
                "O juiz pode suprir recusa injusta ou impossibilidade",
                "O artigo 1.648 permite suprimento judicial quando o cônjuge não pode conceder autorização ou a recusa é injusta. "
                "A medida não deve ser substituída por declaração unilateral do vendedor ou do comprador. O processo examina razão "
                "da venda, impacto familiar e eventual risco ao patrimônio, com participação de quem deveria consentir.\n\nSe havia "
                "capacidade e concordância, é melhor formalizar antes do ato. O suprimento não é atalho para ocultar preço, conflito "
                "conjugal ou negócio já impugnado."
            ),
            section(
                "Anulação tem prazo contado do fim da sociedade conjugal",
                "Pelo artigo 1.649, o ato feito sem autorização, quando necessária e não suprida, é anulável. A ação pode ser proposta "
                "até dois anos depois de terminada a sociedade conjugal. O parágrafo único permite aprovação posterior, desde que em "
                "instrumento público ou particular autenticado. O artigo 1.650 reserva a decretação ao cônjuge prejudicado ou seus herdeiros.\n\n"
                "Boa-fé do comprador é relevante para fatos e consequências, mas não deve ser anunciada como cura automática da forma "
                "no casamento. A matrícula, a escritura e a certidão revelam se o estado civil foi informado corretamente."
            ),
            section(
                "União estável e publicidade exigem distinção",
                "O STJ decidiu no REsp 1.424.275 que a alienação de imóvel comum sem anuência do companheiro pode ser válida perante "
                "terceiro de boa-fé quando não havia publicidade da união no registro nem prova de que o adquirente a conhecia. A proteção "
                "externa não apaga eventual acerto patrimonial entre companheiros. Se a união estava registrada ou o comprador sabia, "
                "o resultado pode mudar.\n\nNão se deve importar mecanicamente o prazo e a forma da outorga conjugal para toda união "
                "estável. Data de aquisição, esforço comum, publicidade e ciência concreta compõem a análise."
            ),
            section(
                "O comprador deve conferir estado civil antes de pagar",
                "Peça certidão atual, pacto ou escritura de união, leia a matrícula e confirme quem ocupa o imóvel. Divergência entre "
                "declaração, documentos e vida aparente deve ser esclarecida. Inclua outorga no próprio título ou obtenha instrumento "
                "formal compatível; não aceite assinatura improvisada depois do pagamento integral.\n\nSe a venda já ocorreu, preserve "
                "contrato, pagamentos, posse e comunicações para avaliar confirmação, suprimento, anulação ou responsabilidade do vendedor. "
                "A orientação não deve prometer manutenção do registro ou cancelamento antes de examinar regime, publicidade e prazo."
            ),
        ],
        "faq": [
            {"q": "Imóvel particular comprado antes do casamento dispensa outorga?", "a": "Não necessariamente. A regra do artigo 1.647 alcança alienação de imóveis, ainda que a comunicação patrimonial seja outra questão."},
            {"q": "Companheiro não registrado pode anular venda contra terceiro de boa-fé?", "a": "O STJ condiciona a oponibilidade externa à publicidade da união ou à prova de ciência do adquirente, conforme o caso."},
        ],
        "official_sources": [
            source(CC + "#art1647", "Código Civil, arts. 1.647 e 1.648", "outorga conjugal e possibilidade de suprimento judicial"),
            source(CC + "#art1649", "Código Civil, arts. 1.649 e 1.650", "anulabilidade, prazo, confirmação e legitimidade"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20141216&formato=PDF&nreg=201200753777&salvar=false&seq=1372664&tipo=0", "STJ, REsp 1.424.275/MT", "proteção do terceiro de boa-fé diante de união estável sem publicidade"),
        ],
    },
    "imob-compra-imovel-espolio": {
        "opening": (
            "Imóvel de pessoa falecida integra o espólio até a partilha e não pode ser vendido como se já pertencesse "
            "isoladamente a um herdeiro. No inventário judicial, o artigo 619 do CPC exige autorização do juiz, ouvidos os "
            "interessados. No inventário extrajudicial, a regulamentação nacional do CNJ passou a admitir alienação pelo "
            "inventariante, mediante escritura pública e condições específicas. Cessão de direitos hereditários é outro negócio: "
            "pode transferir quinhão, mas a disposição isolada de bem do acervo possui limites expressos no artigo 1.793."
        ),
        "sections": [
            section(
                "No inventário judicial, a venda depende do juízo",
                "O inventariante administra o acervo, sem liberdade para vender imóvel por decisão individual. O artigo 619, inciso I, "
                "prevê alienação depois de ouvidos os interessados e com autorização judicial. O pedido costuma explicar finalidade, "
                "avaliação, proposta, forma de pagamento e destino do preço. Herdeiro que assina sozinho não substitui a decisão.\n\n"
                "Alvará, decisão e termo do inventariante precisam corresponder ao imóvel e ao negócio levados ao cartório. Condições "
                "judiciais sobre valor mínimo, depósito ou quitação tributária devem ser reproduzidas e comprovadas antes do registro."
            ),
            section(
                "O CNJ admite venda em inventário extrajudicial com requisitos",
                "O artigo 11-A da Resolução CNJ 35, incorporado pela Resolução 571/2024, permite ao inventariante alienar bem do espólio "
                "por escritura pública sem autorização judicial. A norma condiciona a operação, entre outros pontos, à finalidade de "
                "pagar despesas do inventário, discriminação dessas despesas, ausência de indisponibilidade, vinculação do preço e "
                "garantias previstas quando os pagamentos ainda não foram feitos.\n\nNão é autorização genérica para qualquer venda "
                "extrajudicial. Tabelião deve verificar requisitos da redação vigente, e o dinheiro possui destinação controlada. O comprador "
                "precisa ler a escritura de nomeação do inventariante e a escritura de alienação completa."
            ),
            section(
                "Cessão de herança não equivale à venda do apartamento",
                "O coerdeiro pode ceder seu direito hereditário por escritura pública. Antes da partilha, a herança é uma universalidade, "
                "e o artigo 1.793, parágrafo segundo, considera ineficaz a cessão feita por coerdeiro sobre bem singular do acervo. O "
                "parágrafo terceiro também limita disposição de bem do acervo pendente de indivisão sem autorização judicial, ressalvada "
                "a disciplina extrajudicial hoje aplicável ao inventariante.\n\nOs demais coerdeiros têm preferência na cessão onerosa a "
                "estranho nos termos dos artigos 1.794 e 1.795. O cessionário do quinhão assume a posição patrimonial nos limites do negócio, "
                "sem garantia de receber exatamente o imóvel desejado na partilha."
            ),
            section(
                "Due diligence alcança espólio, imóvel e sucessão",
                "Peça certidão de óbito, nomeação do inventariante, peças ou escritura do inventário, matrícula, avaliação, declaração "
                "tributária e manifestação dos interessados. Confira testamento, incapazes, cônjuge ou companheiro, dívidas, penhoras e "
                "indisponibilidades. Verifique quem receberá o preço e em qual conta, conforme decisão ou escritura.\n\nITCMD do inventário "
                "e ITBI da compra possuem fatos distintos. Débitos do imóvel, condomínio e tributos continuam exigindo conferência; a "
                "autorização sucessória não certifica ausência de ônus."
            ),
            section(
                "Registro só ocorre com título sucessório coerente",
                "Se o imóvel já foi partilhado e registrado em nome do herdeiro, a venda segue pelo novo titular. Se permanece no espólio, "
                "o título deve demonstrar poderes do inventariante e autorização ou enquadramento extrajudicial. Nota devolutiva deve ser "
                "respondida com documentos, não com declaração informal dos herdeiros.\n\nUma análise jurídica pode comparar compra direta, "
                "cessão de quinhão e espera da partilha. Cada alternativa possui preço, risco e imposto próprios; nenhuma permite prometer "
                "aquisição segura de bem singular apenas porque todos os familiares disseram concordar."
            ),
        ],
        "faq": [
            {"q": "Inventariante extrajudicial pode vender qualquer imóvel livremente?", "a": "Não. O artigo 11-A da Resolução CNJ 35 impõe finalidade, escritura e condições específicas à alienação."},
            {"q": "Comprar o quinhão de um herdeiro garante aquele imóvel?", "a": "Não. A cessão recai sobre direitos hereditários; bem singular depende da partilha ou do título de alienação válido do espólio."},
        ],
        "official_sources": [
            source(CPC + "#art619", "Código de Processo Civil, art. 619, I", "alienação judicial de bem do espólio com oitiva e autorização"),
            source(CC + "#art1793", "Código Civil, arts. 1.793 a 1.795", "cessão de quinhão, ineficácia sobre bem singular e preferência de coerdeiros"),
            source("https://atos.cnj.jus.br/atos/detalhar/179", "CNJ, Resolução 35/2007 compilada, art. 11-A", "condições vigentes para alienação de bem do espólio em inventário extrajudicial"),
            source("https://atos.cnj.jus.br/atos/detalhar/5705", "CNJ, Resolução 571/2024", "ato que introduziu e atualizou o regime extrajudicial de alienação pelo inventariante"),
        ],
    },
}


if __name__ == "__main__":
    apply_updates(EXPECTED_SHA256, UPDATES, "imobiliario-09-c")

