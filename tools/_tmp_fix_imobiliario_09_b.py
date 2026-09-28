#!/usr/bin/env python3
"""Reescreve as páginas 7 a 12 do shard imobiliário-09."""

from _tmp_fix_imobiliario_09_lib import apply_updates, section, source


EXPECTED_SHA256 = "8e2321f512c9b7a898624c2189f569b0841168d04c793d49f59ee89a271b1c94"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CTN = "https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm"
LRP = "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm"
CF = "https://www.planalto.gov.br/ccivil_03/constituicao/constituicaocompilado.htm"


UPDATES = {
    "imob-itbi-quem-paga-quando": {
        "opening": (
            "Quem recolhe o ITBI e quando a guia deve ser paga não se resolve apenas pela cláusula da compra. "
            "O artigo 42 do Código Tributário Nacional permite que a lei municipal escolha como contribuinte qualquer "
            "das partes da operação tributada. Em muitas cidades, o adquirente é indicado, mas a regra local precisa "
            "ser lida. O contrato pode distribuir o custo entre comprador e vendedor, sem alterar perante o fisco a "
            "responsabilidade definida em lei. O momento de emissão ou pagamento da guia também não deve ser confundido "
            "com a ocorrência material da transmissão imobiliária."
        ),
        "sections": [
            section(
                "A lei municipal identifica contribuinte, alíquota e procedimento",
                "A Constituição atribui aos municípios o imposto sobre transmissão onerosa entre vivos de imóveis e "
                "de direitos reais imobiliários, ressalvadas as garantias, além da cessão de direitos à aquisição. O "
                "CTN delimita normas gerais, mas cadastro, declaração, alíquota dentro dos limites aplicáveis, vencimento "
                "e pedido de revisão dependem da legislação de cada local. Não existe uma única guia nacional.\n\nO "
                "artigo 42 autoriza a lei a apontar qualquer parte como contribuinte. É comum atribuir a obrigação ao "
                "adquirente, sem que essa prática substitua a consulta ao texto municipal vigente na data do fato. Em "
                "permuta, cessão, usufruto ou arrematação, o participante indicado e a base podem ter disciplina própria."
            ),
            section(
                "O contrato não muda o sujeito passivo perante a prefeitura",
                "Comprador e vendedor podem ajustar quem suportará economicamente o imposto. Pelo artigo 123 do CTN, "
                "convenções particulares não são opostas à Fazenda para modificar a definição legal do sujeito passivo. "
                "Se a lei municipal responsabiliza o adquirente e o contrato diz que o vendedor pagará, eventual recusa "
                "do vendedor gera questão contratual entre as partes; não impede a cobrança municipal do contribuinte.\n\n"
                "A minuta deve dizer quem providencia a declaração, quem antecipa o dinheiro, como se comprova o pagamento "
                "e o que ocorre se a base for revista. Essa distribuição evita atraso no registro, mas não cria imunidade, "
                "isenção ou contribuinte diferente do previsto em lei."
            ),
            section(
                "Na compra e venda, propriedade passa com o registro",
                "O artigo 1.245 do Código Civil estabelece que a propriedade entre vivos se transfere pelo registro do "
                "título no Registro de Imóveis; enquanto não registrado, o alienante continua havido como dono. Essa "
                "regra sustenta a distinção entre assinatura do contrato, lavratura da escritura e transmissão do domínio. "
                "O município pode organizar declaração e recolhimento antes da apresentação do título, mas o procedimento "
                "de arrecadação não deve, por si só, antecipar o núcleo constitucional da transmissão da propriedade.\n\n"
                "O raciocínio precisa ser adaptado quando a operação transmite outro direito real ou cede direito à "
                "aquisição, hipóteses expressamente mencionadas na Constituição e no CTN. Por isso, uma página sobre compra "
                "registrada não resolve automaticamente cessões contratuais ou direitos reais específicos."
            ),
            section(
                "Negócio desfeito pode permitir restituição, não automática",
                "Se a transmissão não chega a ocorrer ou o título é cancelado, pode existir pedido de restituição do ITBI "
                "pago, conforme a causa, a prova e a lei local. Recusa registral temporária não significa necessariamente "
                "que o negócio acabou; antes de pedir devolução, é preciso saber se o título será corrigido e reapresentado. "
                "Prazo, legitimidade e documentação seguem o processo tributário aplicável.\n\nContrato, guia, comprovante, "
                "nota devolutiva, distrato e matrícula mostram o que efetivamente ocorreu. Se houve transmissão seguida de "
                "novo negócio, a análise não pode tratar duas operações como simples pagamento sem causa."
            ),
            section(
                "Uma cronologia evita pagar ou contestar no marco errado",
                "Registre datas da promessa, escritura, declaração municipal, pagamento, protocolo e registro. Leia a lei "
                "do município do imóvel, porque o domicílio das partes não define a competência territorial do imposto. "
                "Confirme ainda se há benefício legal e quais documentos o condicionam antes de emitir a guia.\n\nUma "
                "revisão tributária pode confrontar a cobrança com o CTN e a norma municipal, sem afirmar que todo pagamento "
                "anterior ao registro é inválido ou que qualquer negócio não registrado gera restituição imediata."
            ),
        ],
        "faq": [
            {"q": "Se o contrato manda o vendedor pagar, a prefeitura só pode cobrar dele?", "a": "Não. O acordo distribui o custo entre as partes, mas não altera o contribuinte definido pela lei municipal."},
            {"q": "Assinar a escritura já transfere a propriedade?", "a": "Não. Na compra e venda imobiliária, a propriedade entre vivos se transfere com o registro do título."},
        ],
        "official_sources": [
            source(CTN + "#art42", "Código Tributário Nacional, art. 42", "eleição legal do contribuinte entre as partes da operação tributada"),
            source(CTN + "#art123", "Código Tributário Nacional, art. 123", "inoponibilidade de convenções particulares à Fazenda para mudar o sujeito passivo"),
            source(CC + "#art1245", "Código Civil, art. 1.245", "transferência da propriedade imobiliária entre vivos pelo registro do título"),
        ],
    },
    "imob-itbi-cessao-direitos": {
        "opening": (
            "A incidência de ITBI na cessão de direitos à aquisição de imóvel é tema constitucional em julgamento no "
            "STF. O Tema 1.124 da repercussão geral discute se o imposto pode incidir antes da transferência da propriedade "
            "pelo registro. Até a última movimentação oficial consultada, o mérito permanecia pendente, de modo que não é "
            "correto apresentar como tese definitiva nem a cobrança irrestrita nem a não incidência universal. A Constituição "
            "e o CTN mencionam cessão de direitos, enquanto a natureza do direito cedido e a lei municipal delimitam o caso."
        ),
        "sections": [
            section(
                "Constituição e CTN incluem cessões no campo do imposto",
                "O artigo 156, inciso II, da Constituição alcança a transmissão onerosa entre vivos de imóveis, de direitos "
                "reais sobre imóveis, exceto garantia, e a cessão de direitos à sua aquisição. O artigo 35, inciso III, do "
                "CTN também menciona cessões de direitos relativos às transmissões listadas. Esses textos impedem reduzir o "
                "ITBI apenas à escritura definitiva de propriedade.\n\nIsso não significa que toda troca de posição em um "
                "contrato produza o mesmo fato. Promessa, cessão de posição contratual, cessão de direito real à aquisição e "
                "venda definitiva possuem estruturas distintas. O instrumento e o direito efetivamente transferido devem ser "
                "identificados antes de aplicar o código tributário municipal."
            ),
            section(
                "O Tema 1.124 do STF ainda exige acompanhamento",
                "No ARE 1.294.969, o STF reconheceu repercussão geral para decidir se a cessão de direitos à aquisição de "
                "imóvel, sem ingresso do título no registro, configura fato gerador do ITBI. A consulta oficial do Tema 1.124 "
                "deve ser verificada na data da operação e da medida judicial, porque uma futura decisão de mérito poderá "
                "definir tese e modulação.\n\nEnquanto o julgamento não é concluído, decisões locais podem divergir e o risco "
                "processual precisa ser explicado. Citar precedente sobre simples compra e venda registrada como se encerrasse "
                "a controvérsia específica da cessão omite justamente o objeto submetido ao Supremo."
            ),
            section(
                "Propriedade e direito cedido não são sinônimos",
                "Pelo artigo 1.245 do Código Civil, o domínio imobiliário entre vivos se transfere com o registro. Um cedente "
                "pode transferir ao cessionário direitos e obrigações de contrato sem ainda ser proprietário, desde que o "
                "contrato, a lei e eventual anuência necessária permitam. A operação pode exigir escritura ou registro conforme "
                "a espécie do direito, sem que o nome dado pelas partes determine sozinho sua natureza.\n\nTambém é preciso "
                "separar ITBI de taxa de anuência, saldo do preço, comissão, laudêmio ou tributo sobre ganho. Cobrar valor "
                "contratual não transforma automaticamente a rubrica em imposto municipal, e afastar uma taxa não resolve "
                "por si a incidência tributária."
            ),
            section(
                "A lei municipal e o procedimento precisam entrar no dossiê",
                "Reúna promessa original, aditivos, instrumento de cessão, anuência do vendedor ou incorporador, pagamentos, "
                "guia, decisão administrativa e matrícula. Identifique o artigo municipal que descreve o fato, o contribuinte, "
                "a base e o momento de recolhimento. Uma guia emitida sem motivação pode exigir impugnação, mas isso não prova "
                "sozinho que a obrigação é inexistente.\n\nSe o preço declarado for questionado, a controvérsia sobre base de "
                "cálculo ainda deve respeitar o regime de arbitramento. Já a discussão sobre ocorrência do fato gerador depende "
                "da natureza da cessão e do estado atual do Tema 1.124."
            ),
            section(
                "Decisão prática depende de prazo e finalidade",
                "Antes de pagar, depositar ou ajuizar, verifique se a cessão precisa ser concluída imediatamente, se o cartório "
                "ou incorporador exige documentos e qual prazo existe para impugnar a cobrança. Mandado de segurança requer "
                "prova documental e possui prazo próprio; ações de repetição ou anulação seguem pressupostos diferentes.\n\nA "
                "orientação responsável registra a pendência do STF, apresenta as duas bases normativas e evita prometer que "
                "uma tese futura terá determinado alcance temporal."
            ),
        ],
        "faq": [
            {"q": "O STF já decidiu definitivamente que cessão sem registro não paga ITBI?", "a": "Não. O Tema 1.124 foi reconhecido, mas o mérito permanecia pendente na consulta oficial usada nesta revisão."},
            {"q": "Cessão de contrato e venda do imóvel são a mesma operação?", "a": "Não. É preciso identificar o direito transferido, a posição das partes e os atos registrais previstos para a operação concreta."},
        ],
        "official_sources": [
            source(CF + "#art156", "Constituição Federal, art. 156, II", "competência municipal sobre transmissões e cessões onerosas imobiliárias"),
            source(CTN + "#art35", "Código Tributário Nacional, art. 35", "hipóteses gerais do ITBI, inclusive cessões de direitos relativos à aquisição"),
            source("https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp?classeProcesso=ARE&incidente=6031137&numeroProcesso=1294969&numeroTema=1124", "STF, Tema 1.124 da repercussão geral", "andamento oficial da controvérsia sobre cessão de direitos sem registro"),
            source(CC + "#art1245", "Código Civil, art. 1.245", "registro como modo de transferência da propriedade imobiliária entre vivos"),
        ],
    },
    "imob-escritura-quando-obrigatoria": {
        "opening": (
            "Escritura pública e registro são etapas diferentes. O artigo 108 do Código Civil exige forma pública, "
            "salvo disposição legal em contrário, para negócios que constituam, transfiram, modifiquem ou renunciem a "
            "direitos reais sobre imóveis de valor superior a trinta vezes o maior salário mínimo vigente no país. Abaixo "
            "desse limite, a forma pública pode ser dispensada, mas o título ainda precisa cumprir os demais requisitos e "
            "ser registrável. Leis especiais também atribuem força de escritura a certos instrumentos particulares."
        ),
        "sections": [
            section(
                "O artigo 108 olha o valor e a data do negócio",
                "A comparação utiliza o maior salário mínimo vigente quando o negócio é celebrado e o valor do imóvel ou "
                "direito negociado, não apenas uma parcela declarada artificialmente. Acima do limite, a escritura é elemento "
                "de validade quando nenhuma lei especial autoriza outra forma. Abaixo dele, instrumento particular pode ser "
                "título hábil, desde que identifique partes, imóvel, preço, manifestação de vontade e demais exigências.\n\n"
                "Dispensa de escritura não é dispensa de ITBI, qualificação registral ou registro. O contrato produz os efeitos "
                "que lhe cabem, mas a propriedade entre vivos só passa com a inscrição do título no Registro de Imóveis."
            ),
            section(
                "A Lei 9.514 não cobre todo financiamento bancário",
                "O artigo 38 da Lei 9.514 admite instrumento particular com efeitos de escritura para atos e contratos "
                "referidos na própria lei ou dela resultantes, inclusive alienação fiduciária imobiliária. A exceção precisa "
                "estar ligada ao regime legal aplicável. O simples fato de um banco participar ou de o preço ser financiado "
                "não transforma qualquer minuta privada em escritura pública.\n\nOutras leis especiais podem conferir força "
                "semelhante a contratos de sistemas específicos. O instrumento deve indicar o fundamento e conter as cláusulas "
                "necessárias, assinaturas e certificações exigidas para que o registrador possa qualificá-lo."
            ),
            section(
                "Forma inadequada pode gerar nulidade, não domínio informal",
                "O artigo 166, inciso IV, considera nulo o negócio que não observa a forma prescrita em lei. Se a escritura era "
                "essencial e não há exceção, o instrumento particular comum não transfere o direito real. Dependendo de seus "
                "elementos, pode ser discutida conversão do negócio pelo artigo 170 ou obrigação de outorgar escritura, mas "
                "nenhuma dessas consequências é automática.\n\nPagamento integral e posse não corrigem sozinhos a forma nem "
                "substituem o registro. Podem sustentar pretensões contratuais, adjudicação ou usucapião quando os respectivos "
                "requisitos existirem, sem tornar proprietário quem apenas guarda um recibo."
            ),
            section(
                "A escritura não encerra a qualificação registral",
                "Tabelião verifica identidade, capacidade, vontade e elementos do ato notarial. O registro examina continuidade, "
                "especialidade, disponibilidade e legalidade do título perante a matrícula. Assim, escritura lavrada pode receber "
                "nota devolutiva se faltar descrição, autorização, imposto ou encadeamento dominial.\n\nAntes de assinar, obtenha "
                "matrícula recente, confirme titularidade, estado civil, poderes de representação e restrições. Depois, protocole o "
                "título e responda às exigências dentro da vigência da prenotação, em vez de tratar a escritura guardada como domínio."
            ),
            section(
                "O documento correto depende da operação concreta",
                "Compra, doação, permuta, instituição de usufruto, garantia e partilha têm regras próprias. Valor, natureza do "
                "direito, participantes e lei especial definem a forma. Assinatura eletrônica pode ser admitida quando atende ao "
                "regime do ato e ao padrão aceito, mas não elimina exigência de escritura pública onde a lei a mantém.\n\nUma revisão "
                "prévia da minuta e da matrícula evita pagar por instrumento incapaz de registro, sem prometer que todo contrato "
                "particular abaixo do limite será aceito apesar de defeitos documentais."
            ),
        ],
        "faq": [
            {"q": "Escritura pública já coloca o imóvel em meu nome?", "a": "Não. Ela pode ser o título necessário, mas a transferência da propriedade ocorre com o registro."},
            {"q": "Todo financiamento bancário dispensa escritura?", "a": "Não. A força de escritura precisa decorrer da Lei 9.514 ou de outra norma especial aplicável ao instrumento."},
        ],
        "official_sources": [
            source(CC + "#art108", "Código Civil, art. 108", "regra geral de escritura pública acima de trinta salários mínimos"),
            source(CC + "#art166", "Código Civil, arts. 166, IV, e 170", "nulidade por falta de forma e possível conversão quando preenchidos seus requisitos"),
            source(CC + "#art1245", "Código Civil, art. 1.245", "registro do título como modo de transferência da propriedade"),
            source("https://www.planalto.gov.br/ccivil_03/leis/l9514.htm#art38", "Lei 9.514/1997, art. 38", "efeitos de escritura dos instrumentos particulares abrangidos pela lei especial"),
        ],
    },
    "imob-registro-imovel-passo-a-passo": {
        "opening": (
            "Comprar e pagar não bastam para transferir a propriedade imobiliária. O artigo 1.245 do Código Civil exige "
            "registro do título no cartório competente. O procedimento começa pela escolha do título correto, passa pelo "
            "protocolo e pela qualificação do registrador e termina com a inscrição e a certidão atualizada. Documentos, "
            "tributos e emolumentos variam conforme negócio, imóvel e estado; uma lista genérica não substitui a nota do "
            "cartório nem autoriza exigir certidões pessoais sem fundamento para todo caso."
        ),
        "sections": [
            section(
                "Confirme matrícula, competência e título",
                "A matrícula identifica imóvel, titular, ônus e atos anteriores. Peça certidão atual próxima da assinatura e "
                "confira descrição, número cadastral, vagas, frações, estado civil e poderes de representação. O título deve ser "
                "apresentado ao Registro de Imóveis da circunscrição do bem, ainda que as partes morem ou assinem em outro local.\n\n"
                "Escritura, contrato particular com força legal, formal de partilha, carta de arrematação e decisão judicial são "
                "exemplos de títulos distintos. Cada um possui documentos de apoio e requisitos próprios; chamar qualquer papel "
                "de contrato de compra e venda não o torna registrável."
            ),
            section(
                "Protocolo gera prenotação e prioridade",
                "Ao receber título apto a protocolo, o cartório lança número e data. A prenotação estabelece prioridade em relação "
                "a títulos incompatíveis apresentados depois. Seus efeitos não são eternos: o artigo 205 prevê cessação quando o "
                "interessado deixa transcorrer o prazo legal sem atender às exigências. Guarde recibo e acompanhe o andamento.\n\n"
                "A prioridade não cura nulidade nem falta de disponibilidade. Ela organiza a ordem de exame e registro. Se o título "
                "for reapresentado após o cancelamento da prenotação, poderá receber nova posição diante de atos intermediários."
            ),
            section(
                "Qualificação pode resultar em registro ou nota devolutiva",
                "O oficial verifica legalidade, continuidade, especialidade e disponibilidade. Havendo exigência, o artigo 198 da "
                "Lei de Registros Públicos determina indicação escrita, clara, objetiva e feita de uma só vez, ressalvadas novas "
                "questões surgidas com o cumprimento. Corrigir documento não é o mesmo que negociar informalmente a recusa.\n\nSe "
                "o apresentante não concorda ou não pode cumprir, pode requerer suscitação de dúvida ao juízo competente. A decisão "
                "administrativa da dúvida não impede uso do processo contencioso adequado, e cada via possui finalidade própria."
            ),
            section(
                "Imposto e emolumentos dependem do ato",
                "Compra onerosa costuma envolver ITBI e emolumentos estaduais; doação ou herança pode envolver ITCMD. Imunidade, "
                "isenção, gratuidade ou redução exigem norma e prova específicas. O registrador pode solicitar comprovante fiscal "
                "quando legalmente necessário, mas não decide livremente criar tributo.\n\nPeça orçamento discriminado e confira "
                "tabela oficial do estado. Uma guia paga com base, código ou contribuinte errados pode gerar exigência e precisa ser "
                "corrigida no órgão fiscal, não apenas no balcão registral."
            ),
            section(
                "Só a certidão final confirma a inscrição",
                "Depois do registro, solicite certidão atualizada e confira adquirente, título, valor declarado, ônus e averbações. "
                "Atualize cadastros municipal e condominial quando necessário, sabendo que esses cadastros não substituem a matrícula. "
                "Guarde título, guia, recibos e nota de registro. Compare também o número de ordem e a data da inscrição com o recibo "
                "de protocolo, especialmente quando outro título foi apresentado no intervalo. Erro de grafia, qualificação pessoal "
                "ou descrição deve ser levado ao cartório com o documento correto, sem rasura feita pelo interessado.\n\nSe a certidão "
                "não mostra o ato, não presuma que o protocolo ou a "
                "entrega de documentos concluiu a transferência. Uma análise registral pode responder à nota devolutiva e preservar "
                "a prioridade, sem prometer aceitação antes da qualificação oficial."
            ),
        ],
        "faq": [
            {"q": "Entregar a escritura ao cartório já me torna proprietário?", "a": "Não. O protocolo inicia o procedimento; a propriedade passa quando o registro é efetivamente lançado."},
            {"q": "Posso contestar uma exigência do registrador?", "a": "Sim. A Lei de Registros Públicos prevê suscitação de dúvida, além das medidas contenciosas cabíveis."},
        ],
        "official_sources": [
            source(CC + "#art1245", "Código Civil, art. 1.245", "aquisição da propriedade imobiliária pelo registro do título"),
            source(LRP + "#art182", "Lei 6.015/1973, arts. 182 e 205", "protocolo, prioridade e duração dos efeitos da prenotação"),
            source(LRP + "#art198", "Lei 6.015/1973, arts. 198 a 204", "nota de exigências e procedimento de suscitação de dúvida"),
        ],
    },
    "imob-comprei-nao-registrei": {
        "opening": (
            "Quem compra, paga e recebe as chaves sem registrar o título ainda não adquiriu a propriedade imobiliária "
            "pelo modo normal do artigo 1.245 do Código Civil. O contrato pode gerar direitos contra o vendedor, posse e "
            "meios de defesa, mas o alienante continua figurando como dono perante o registro. Isso expõe o bem a nova "
            "alienação, inventário, divórcio e constrições, embora o comprador sem registro não fique automaticamente sem "
            "proteção: boa-fé, posse, data e natureza do contrato importam."
        ),
        "sections": [
            section(
                "Contrato e posse não equivalem ao domínio registrado",
                "A promessa quitada pode obrigar o vendedor a outorgar título e, em certas condições, sustentar adjudicação "
                "compulsória. A posse permite tutela possessória contra turbação. Nenhum desses efeitos altera a matrícula por "
                "mera passagem do tempo. Até o registro, o alienante continua havido como dono, salvo aquisição por outro modo "
                "legal reconhecida e formalizada.\n\nIPTU, condomínio e contas em nome do comprador ajudam a provar ocupação e "
                "pagamentos, mas não substituem o título. Da mesma forma, reconhecer firma ou registrar o contrato em Títulos e "
                "Documentos não produz o registro imobiliário necessário à propriedade."
            ),
            section(
                "Venda posterior e penhora não têm resultado automático",
                "Um segundo adquirente que registra pode obter posição real mais forte, mas sua boa-fé, a validade dos títulos, a "
                "posse aparente e eventual fraude precisam ser examinadas. Não existe regra responsável segundo a qual o segundo "
                "sempre vence independentemente de ciência do primeiro negócio.\n\nSe credor do vendedor penhora o imóvel, o "
                "comprador pode avaliar embargos de terceiro. A Súmula 84 do STJ admite essa defesa fundada em posse oriunda de "
                "compromisso de compra e venda mesmo sem registro. Admissibilidade não significa procedência: autenticidade, data, "
                "boa-fé, pagamento e situação do crédito serão discutidos."
            ),
            section(
                "Adjudicação compulsória pode ser judicial ou extrajudicial",
                "Quando existe promessa sem arrependimento, preço cumprido e recusa ou impossibilidade de outorga pelo vendedor, "
                "pode caber adjudicação compulsória. O artigo 216-B da Lei de Registros Públicos criou via extrajudicial perante o "
                "cartório, com advogado, ata notarial e documentos previstos em lei. Pendência litigiosa, defeito do título ou "
                "resistência relevante pode exigir a via judicial.\n\nA falta de registro prévio do compromisso não impede por si "
                "só a adjudicação, mas a cadeia dominial, especialidade do imóvel e quitação precisam estar demonstradas. O "
                "procedimento não serve para corrigir compra feita por quem não era titular sem enfrentar o defeito de origem."
            ),
            section(
                "Primeiro descubra por que o registro não ocorreu",
                "Obtenha certidão integral da matrícula e leia o contrato. Falta de escritura, ITBI, inventário, outorga conjugal, "
                "descrição divergente, indisponibilidade ou parcelamento irregular exigem soluções diferentes. Protocole o título "
                "existente quando houver base para isso e peça nota devolutiva escrita, em vez de trabalhar com recusa verbal.\n\n"
                "Se o vendedor faleceu, os sucessores e o espólio podem integrar a regularização. Se desapareceu ou recusa assinar, "
                "notificações e prova da quitação ajudam a demonstrar o inadimplemento sem autorizar assinatura simulada."
            ),
            section(
                "A urgência cresce com sinais de conflito",
                "Nova venda anunciada, processo contra o vendedor, morte, separação ou tentativa de retomada pedem consulta rápida à "
                "matrícula e ao processo. Medidas cautelares dependem de probabilidade e perigo; a existência de contrato antigo não "
                "garante bloqueio imediato.\n\nOrganize contrato, comprovantes, posse, tributos, mensagens e certidões. A estratégia "
                "pode ser simples registro, obtenção de escritura, adjudicação ou defesa contra constrição. O objetivo é levar o "
                "direito demonstrado à matrícula, sem afirmar que recibos já fizeram o mesmo trabalho."
            ),
        ],
        "faq": [
            {"q": "Contrato sem registro não vale nada?", "a": "Ele pode gerar obrigação, posse e defesas, mas não transfere por si só a propriedade imobiliária perante o registro."},
            {"q": "Adjudicação compulsória exige sempre processo judicial?", "a": "Não. O artigo 216-B prevê procedimento extrajudicial, desde que seus requisitos possam ser demonstrados."},
        ],
        "official_sources": [
            source(CC + "#art1245", "Código Civil, art. 1.245", "registro como modo normal de transferência da propriedade entre vivos"),
            source(LRP + "#art216-B", "Lei 6.015/1973, art. 216-B", "procedimento extrajudicial de adjudicação compulsória"),
            source("https://www.stj.jus.br/docs_internet/revista/eletronica/stj-revista-sumulas-2009_6_capSumula84.pdf", "STJ, Súmula 84", "embargos de terceiro fundados em posse de compromisso sem registro"),
        ],
    },
    "imob-due-diligence-compra": {
        "opening": (
            "Diligência imobiliária começa pela matrícula, mas não termina nela. O artigo 54 da Lei 13.097 fortalece a "
            "concentração registral e protege o terceiro de boa-fé contra situações não lançadas, com exceções legais. "
            "Ao mesmo tempo, a própria lei diz que certidões forenses não são requisito geral de validade, eficácia ou "
            "caracterização da boa-fé. Pedir documentos adicionais pode ser prudente conforme risco, valor e perfil do vendedor; "
            "não se deve transformar uma lista indiscriminada em obrigação federal nem prometer risco zero."
        ),
        "sections": [
            section(
                "Matrícula recente é o eixo da análise",
                "A certidão deve ser obtida perto da assinatura e novamente conferida antes do registro quando houver intervalo "
                "relevante. Não existe validade federal universal de trinta dias para toda matrícula; serventia, negócio ou norma "
                "local podem exigir atualidade específica. Leia titularidade, descrição, ônus, indisponibilidades, ações reais, "
                "averbações premonitórias e cadeia dos atos.\n\nCompare imóvel físico, cadastro municipal, planta, área, vagas e "
                "ocupação. Matrícula sem gravame não prova regularidade urbanística, ambiental, condominial ou fiscal, e uma "
                "certidão antiga não revela ato apresentado depois de sua emissão."
            ),
            section(
                "Concentração registral possui alcance e exceções",
                "O artigo 54 torna eficaz o negócio do terceiro de boa-fé diante de atos precedentes que deveriam estar registrados "
                "ou averbados e não estavam. O parágrafo primeiro ressalva, entre outros pontos, hipóteses da Lei de Recuperação e "
                "Falências e aquisições ou extinções que independam de registro. Boa-fé continua incompatível com ciência concreta "
                "de fraude.\n\nO parágrafo segundo afasta a exigência de certidões forenses para validade, eficácia ou caracterização "
                "da boa-fé. Isso não proíbe investigação adicional quando sinais objetivos justificam cautela, nem converte a "
                "matrícula em garantia contra todo risco tributário ou pessoal."
            ),
            section(
                "Execução fiscal merece verificação própria",
                "O artigo 185 do CTN e o Tema Repetitivo 290 do STJ formam exceção importante ao raciocínio comum da Súmula 375. "
                "Para alienação posterior a 9 de junho de 2005, a inscrição do crédito tributário em dívida ativa pode configurar "
                "fraude se o devedor não reserva bens suficientes, independentemente de registro da penhora e da boa-fé alegada "
                "pelo adquirente.\n\nPor isso, certidões fiscais e investigação proporcional do vendedor podem ser úteis mesmo com "
                "matrícula limpa. O resultado precisa ser interpretado: homônimo, dívida garantida, bem reservado ou alienação "
                "anterior mudam a análise. Certidão não deve ser apenas colecionada sem leitura."
            ),
            section(
                "Documentos variam conforme imóvel e vendedor",
                "Confira IPTU ou tributo rural, condomínio, ocupação, licenças e representação. Para pessoa jurídica, examine contrato "
                "social, poderes, aprovações e situação de insolvência. Imóvel rural pode exigir cadastro, certificação e questões "
                "ambientais; unidade nova pede incorporação, memorial e habite-se. Certidão criminal genérica raramente informa risco "
                "dominial e amplia tratamento de dados sem finalidade.\n\nConsultas cíveis, fiscais, trabalhistas e de protesto devem "
                "ser selecionadas pelo vínculo possível com insolvência ou constrição, respeitando minimização de dados. Resultado "
                "positivo exige acesso ao processo ou documento que explique valor, fase e alcance."
            ),
            section(
                "Contrato distribui riscos sem apagar direitos de terceiros",
                "Declarações do vendedor, dever de informar fatos novos, condição para pagamento e solução de pendências ajudam a "
                "organizar a operação. Retenção de preço ou conta vinculada depende de acordo, instituição e redação executável; não "
                "é prática obrigatória em toda compra. Quitação de condomínio e tributos deve ser demonstrada no marco combinado.\n\n"
                "Monte relatório com fonte, data, nome consultado, achado e decisão. A conclusão deve indicar riscos eliminados, "
                "mitigados e residuais. Uma diligência séria não afirma que certidão limpa impede qualquer disputa e não exige do "
                "comprador um inventário ilimitado de dados pessoais."
            ),
        ],
        "faq": [
            {"q": "A lei exige todas as certidões judiciais para provar boa-fé?", "a": "Não. O artigo 54, parágrafo segundo, afasta essa exigência geral, embora consultas proporcionais possam ser prudentes diante do risco concreto."},
            {"q": "Matrícula limpa afasta fraude em execução fiscal?", "a": "Não necessariamente. O artigo 185 do CTN e o Tema 290 estabelecem regime especial ligado à inscrição em dívida ativa."},
        ],
        "official_sources": [
            source("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13097.htm#art54", "Lei 13.097/2015, art. 54", "concentração registral, exceções e dispensa geral de certidões forenses"),
            source(CTN + "#art185", "Código Tributário Nacional, art. 185", "presunção de fraude na alienação posterior à inscrição em dívida ativa"),
            source("https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=290&cod_tema_inicial=290&novaConsulta=true&tipo_pesquisa=T", "STJ, Tema Repetitivo 290", "regime especial da fraude à execução fiscal após a Lei Complementar 118/2005"),
            source(LRP + "#art167", "Lei 6.015/1973, art. 167", "atos registráveis e averbáveis na matrícula imobiliária"),
        ],
    },
}


if __name__ == "__main__":
    apply_updates(EXPECTED_SHA256, UPDATES, "imobiliario-09-b")
