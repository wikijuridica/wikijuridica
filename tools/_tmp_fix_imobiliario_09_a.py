#!/usr/bin/env python3
"""Reescreve as paginas 1 a 6 do shard imobiliario-09."""

from _tmp_fix_imobiliario_09_lib import apply_updates, section, source


EXPECTED_SHA256 = "b26c70be4d403db3d5bec8a037cbd58466f7e6f2e0a2799cf396789f4a06165f"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CDC = "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"
CTN = "https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm"
LRP = "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm"


UPDATES = {
    "imob-vicio-construtivo-acao": {
        "opening": (
            "Infiltracao, fissura, descolamento de revestimento e falha de impermeabilizacao podem ter "
            "origens e consequencias muito diferentes. Antes de cobrar a construtora, e preciso identificar "
            "quando o defeito apareceu, se compromete solidez ou seguranca, qual era a manutencao prevista e "
            "qual remedio se pretende: conserto, abatimento, resolucao ou indenizacao. Os prazos tambem mudam "
            "conforme a pretensao. A garantia de cinco anos do artigo 618 do Codigo Civil nao deve ser confundida "
            "com a decadencia de cento e oitenta dias do seu paragrafo unico nem com o prazo para uma acao "
            "indenizatoria por danos decorrentes da construcao."
        ),
        "sections": [
            section(
                "A garantia do artigo 618 tem objeto definido",
                "O construtor de edificio ou outra construcao consideravel responde, durante cinco anos, pela "
                "solidez e seguranca do trabalho, em razao dos materiais e do solo. O periodo e contado da entrega "
                "da obra e protege contra defeitos que se manifestem dentro dele. Nem toda mancha, rejunte gasto ou "
                "peca quebrada e automaticamente um problema de solidez; um laudo precisa relacionar o sintoma ao "
                "projeto, ao material ou a execucao.\n\nO paragrafo unico do artigo 618 estabelece decadencia de "
                "cento e oitenta dias para o dono da obra propor a acao contra o empreiteiro depois do aparecimento "
                "do vicio ou defeito. Essa regra nao converte toda demanda ligada a obra em uma unica acao com um "
                "unico prazo. O pedido de cumprimento da garantia e a pretensao de indenizar prejuizos ja causados "
                "possuem fundamentos que devem ser classificados separadamente."
            ),
            section(
                "Indenizacao por defeito nao se confunde com redibicao",
                "O Superior Tribunal de Justica distingue o prazo de garantia do artigo 618 do prazo prescricional "
                "da pretensao indenizatoria. Para defeito surgido dentro da garantia em contrato submetido ao Codigo "
                "Civil atual, o tribunal aplica, em regra, a prescricao de dez anos a reparacao contratual, sem "
                "transformar isso em autorizacao para esperar. Data da entrega, ciencia do dano, reclamacoes e "
                "natureza do pedido continuam decisivas.\n\nEm relacao de consumo, a decadencia do artigo 26 do CDC "
                "disciplina a reclamacao por vicio, enquanto a pretensao compensatoria por danos provocados pelo "
                "defeito nao recebe automaticamente o mesmo tratamento. A notificacao comprovada ao fornecedor "
                "tambem pode repercutir na contagem prevista pelo CDC. A analise deve evitar tanto encerrar cedo um "
                "direito existente quanto anunciar que qualquer pretensao permanece aberta por dez anos."
            ),
            section(
                "O CDC oferece remedios depois da oportunidade de saneamento",
                "Quando incorporadora ou construtora atua como fornecedora, o artigo 18 do CDC permite exigir a "
                "reexecucao ou saneamento do vicio. Nao resolvido o problema no prazo legal ou convencionalmente "
                "ajustado nos limites permitidos, o consumidor pode escolher, conforme o caso, substituicao, "
                "restituicao da quantia ou abatimento proporcional. Em imovel, substituicao integral e resolucao "
                "costumam exigir gravidade compativel; pequenos reparos nao tornam inevitavel desfazer a compra.\n\n"
                "Venda ocasional entre particulares nao e relacao de consumo apenas porque existe um comprador. Se "
                "o vendedor exerce a atividade de forma habitual, a qualificacao pode mudar. Contrato, identidade "
                "dos participantes e cadeia de fornecimento precisam ser verificados antes de escolher o regime."
            ),
            section(
                "Pericia e cronologia separam obra, uso e manutencao",
                "Fotografe a evolucao, preserve manual, memorial descritivo, termo de entrega e chamados de "
                "assistencia. Laudo de engenheiro ou arquiteto habilitado deve apontar causa provavel, extensao, "
                "urgencia, metodo de reparo e risco de agravamento. Em condominio, tambem e preciso localizar se a "
                "origem esta na unidade, em area comum ou em intervencao de terceiro.\n\nA construtora pode demonstrar "
                "mau uso, reforma incompatível ou falta de manutencao, mas uma clausula generica nao apaga defeito "
                "de projeto ou execucao. Medida emergencial para conter agua ou risco deve ser documentada, com "
                "orcamentos e notas, sem destruir desnecessariamente vestigios que permitiriam a pericia."
            ),
            section(
                "O pedido judicial depende do remedio e da prova",
                "Notificacao e tentativa de vistoria ajudam a delimitar a recusa, mas nao substituem tutela urgente "
                "quando ha risco a pessoas ou ao edificio. Obrigacao de fazer, abatimento, resolucao e perdas e danos "
                "podem ser combinados apenas quando juridicamente compativeis. Dano moral nao decorre de toda falha "
                "construtiva, e lucros cessantes ou despesas de moradia exigem nexo e comprovacao.\n\nPericia complexa "
                "pode afastar o rito do juizado especial; valor da causa nao e o unico criterio. Uma revisao tecnica "
                "e juridica da cronologia permite escolher a acao e o prazo defensaveis sem prometer reparo, liminar "
                "ou indenizacao antes do contraditorio."
            ),
        ],
        "faq": [
            {"q": "Os cinco anos do artigo 618 sao o prazo para ajuizar qualquer acao?", "a": "Nao. Sao o periodo legal de garantia de solidez e seguranca; o prazo da pretensao depende do remedio, do regime aplicavel e das datas comprovadas."},
            {"q": "O condominio pode cobrar defeitos nas areas comuns?", "a": "Pode defender interesses comuns representado pelo sindico, sem substituir automaticamente pretensoes individuais sobre danos exclusivos de cada unidade."},
        ],
        "official_sources": [
            source(CC + "#art618", "Codigo Civil, art. 618", "garantia de solidez e seguranca e decadencia especifica do paragrafo unico"),
            source(CDC + "#art18", "Codigo de Defesa do Consumidor, arts. 18 e 26", "remedios do vicio e disciplina da reclamacao no regime de consumo"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&b=infj&i=81&l=20&livre=cc+&p=true&refinar=s.disp.", "STJ, Informativo de Jurisprudencia 856", "distincao entre garantia, decadencia e prescricao da pretensao indenizatoria por vicio construtivo"),
        ],
    },
    "imob-vicio-oculto-imovel-usado": {
        "opening": (
            "Um defeito descoberto depois da compra de imovel usado so e redibitorio quando ja existia na entrega, "
            "nao era reconhecivel pela diligencia normal e torna o bem improprio ao uso ou reduz sensivelmente seu "
            "valor. Idade da construcao, desgaste visivel e reforma posterior nao bastam. Entre particulares, o "
            "Codigo Civil costuma reger o caso; o CDC pode incidir se o alienante atuar como fornecedor habitual. "
            "A investigacao deve comecar depressa, porque o artigo 445 fixa decadencia e possui regra propria para "
            "defeito que, por sua natureza, so pode ser conhecido mais tarde."
        ),
        "sections": [
            section(
                "Os artigos 441 e 442 oferecem duas escolhas",
                "Provado o vicio oculto, o adquirente pode rejeitar a coisa, desfazendo o contrato pela acao "
                "redibitoria, ou conserva-la e pedir abatimento do preco pela acao estimatoria. A resolucao precisa "
                "ser proporcional a gravidade: uma instalacao clandestina que inviabiliza o uso tem efeito diferente "
                "de reparo localizado. O abatimento nao corresponde automaticamente ao primeiro orcamento; pode "
                "considerar custo necessario e efetiva perda de valor.\n\nDefeito aparente, informado ou refletido "
                "expressamente no preco nao e oculto. A vistoria comum, porem, nao exige que todo comprador abra "
                "paredes ou remova forro. Fotografias do anuncio, mensagens e laudo sobre a antiguidade do problema "
                "ajudam a reconstruir o estado do bem na venda."
            ),
            section(
                "O artigo 445 nao concede cento e oitenta dias ao imovel",
                "Para bem imovel, a regra geral e decadencia de um ano contado da entrega efetiva. Se o adquirente "
                "ja estava na posse, o prazo e reduzido pela metade e corre da alienacao. Quando o vicio, por sua "
                "natureza, somente puder ser conhecido mais tarde, o paragrafo primeiro manda contar da ciencia, "
                "observado o limite maximo de um ano para imoveis. Os cento e oitenta dias mencionados nessa parte "
                "da lei se referem a bens moveis, nao a imoveis.\n\nGarantia contratual pode repercutir na contagem "
                "nos termos do artigo 446, mas nao autoriza abandono da notificacao. Registre data, sintoma inicial "
                "e momento em que o diagnostico tecnico tornou conhecida a causa."
            ),
            section(
                "A ciencia do vendedor altera a indenizacao",
                "Pelo artigo 443, se o alienante conhecia o vicio, deve restituir o que recebeu e responder por "
                "perdas e danos. Se nao o conhecia, restitui o valor recebido e as despesas do contrato. Isso nao "
                "significa que a simples existencia de pintura nova prove dolo. E preciso ligar a conduta a tentativa "
                "de ocultar o defeito, por mensagens, obras cosmeticas, laudos anteriores ou reclamacoes de antigos "
                "ocupantes.\n\nClausula de venda no estado em que se encontra tem maior peso para defeitos visiveis e "
                "riscos descritos. Ela nao deve servir de abrigo a omissao consciente sobre problema escondido. O "
                "alcance concreto depende do texto, da informacao oferecida e da possibilidade real de vistoria."
            ),
            section(
                "O laudo deve provar anterioridade e relevancia",
                "O profissional tecnico precisa descrever causa, idade aproximada, sinais de intervencao anterior, "
                "risco, reparo necessario e compatibilidade com uso ou obra posterior. Preserve amostras e permita, "
                "quando seguro, vistoria do vendedor. Orcamentos, notas e fotos datadas quantificam o pedido; uma "
                "estimativa sem diagnostico nao prova que o defeito existia na compra.\n\nNotifique por meio "
                "comprovavel e proponha vistoria sem admitir prorrogacao informal do prazo. Reparos urgentes para "
                "evitar incendio, desabamento ou infiltracao maior devem ser documentados antes e depois."
            ),
            section(
                "Negociacao nao autoriza perder a janela judicial",
                "Vendedor pode oferecer conserto, abatimento ou desfazimento. Qualquer acordo deve definir obra, "
                "prazo, acesso, garantia e alcance da quitacao. Se o prazo decadencial estiver proximo, troca de "
                "mensagens sem solucao nao deve ser tratada como suspensao segura.\n\nUma analise juridica da data de "
                "entrega, posse anterior, descoberta e eventual garantia contratual permite escolher o pedido. "
                "Indenizacao moral nao e consequencia automatica de vicio redibitorio, e o exito depende da prova "
                "tecnica e do contraditorio."
            ),
        ],
        "faq": [
            {"q": "Venda entre duas pessoas fisicas nunca segue o CDC?", "a": "Nao se conclui apenas pela forma civil das partes. Venda ocasional costuma seguir o Codigo Civil; atividade habitual de fornecimento pode alterar a qualificacao."},
            {"q": "Posso consertar antes da pericia?", "a": "Medidas urgentes podem ser necessarias, mas preserve fotos, laudo, notas e, quando possivel, oportunidade de vistoria para nao eliminar a prova da origem."},
        ],
        "official_sources": [
            source(CC + "#art441", "Codigo Civil, arts. 441 e 442", "requisitos do vicio redibitorio e escolhas entre redibicao e abatimento"),
            source(CC + "#art443", "Codigo Civil, art. 443", "efeitos distintos conforme o alienante conhecia ou nao o vicio"),
            source(CC + "#art445", "Codigo Civil, arts. 445 e 446", "decadencia para imoveis, descoberta tardia e garantia contratual"),
        ],
    },
    "imob-evicao-perdi-imovel": {
        "opening": (
            "Eviccao e a perda total ou parcial do bem adquirido em contrato oneroso porque prevalece direito de "
            "terceiro anterior a compra. Ela nao se limita a uma sentenca reivindicatoria transitada em julgado: a "
            "privacao pode decorrer de ato administrativo ou de outra decisao fundada em causa juridica preexistente, "
            "desde que a perda seja efetiva e nao resulte de fato criado pelo proprio comprador. O vendedor responde "
            "em regra mesmo sem conhecer o problema, mas a extensao da garantia, a defesa exercida e o contrato "
            "precisam ser examinados antes de calcular qualquer ressarcimento."
        ),
        "sections": [
            section(
                "A causa anterior distingue eviccao de perda posterior",
                "Os artigos 447 a 457 do Codigo Civil protegem o adquirente oneroso. Titulo dominial de terceiro, "
                "venda feita por quem nao podia alienar ou restricao publica preexistente podem sustentar a garantia. "
                "Desapropriacao por fato posterior, penhora por divida do proprio comprador ou perda decorrente de "
                "seu inadimplemento nao sao eviccao imputavel ao antigo vendedor.\n\nA responsabilidade tambem pode "
                "existir em aquisicao feita em hasta publica. Em toda hipotese, a decisao ou ato que retirou o bem, "
                "a anterioridade do direito e a cadeia de contratos precisam ser preservados."
            ),
            section(
                "O artigo 450 usa o valor do bem na epoca da eviccao",
                "Salvo estipulacao valida em sentido diferente, o evicto pode receber a restituicao integral do "
                "preco ou da parte correspondente, calculada pelo valor da coisa na epoca em que se evenceu. A lei "
                "tambem inclui frutos que ele foi obrigado a restituir, despesas do contrato, prejuizos diretamente "
                "resultantes e custas e honorarios da demanda. Benfeitorias necessarias ou uteis que nao tenham sido "
                "pagas por quem recebeu o bem podem integrar a responsabilidade nos termos dos artigos seguintes.\n\n"
                "Nao basta repetir o preco nominal da escritura nem somar toda despesa realizada no imovel. Deve-se "
                "provar o valor na data relevante, o desembolso e o nexo com a perda. Na eviccao parcial, a resolucao "
                "integral depende de a parte perdida ser consideravel; fora disso, cabe indenizacao proporcional."
            ),
            section(
                "Denunciacao da lide deixou de ser requisito de conservacao",
                "O CPC permite denunciar o alienante imediato no processo em que o terceiro reclama o bem. A medida "
                "pode concentrar defesa e regresso, mas nao e obrigatoria no sistema atual. O STJ reconhece que a "
                "falta de denunciacao nao elimina a garantia, que pode ser cobrada em acao autonoma. Tambem admite "
                "pretensao direta contra alienante que integra a cadeia, conforme os limites do caso.\n\nMesmo sem "
                "obrigatoriedade, informar o vendedor e permitir que contribua para a defesa reduz controverse sobre "
                "omissao processual. O comprador deve contestar adequadamente a pretensao do terceiro; abandono "
                "deliberado ou acordo sem necessidade pode romper o nexo do prejuizo."
            ),
            section(
                "Clausula de exclusao nao apaga sempre o preco",
                "As partes podem reforcar, diminuir ou excluir a responsabilidade, mas o artigo 449 preserva ao "
                "evicto que nao sabia do risco, ou que informado nao o assumiu, o direito de receber o preco. A perda "
                "inclusive desse valor exige ciencia e assuncao expressa do risco. Texto generico de venda no estado "
                "do imovel nao prova por si so que o comprador aceitou perder o dominio para terceiro.\n\nSe houve "
                "dolo ou omissao relevante, outras pretensoes podem coexistir. O contrato, a due diligence e a "
                "informacao dada antes da compra mostram qual risco foi efetivamente distribuido."
            ),
            section(
                "Monte a prova antes de formular o regresso",
                "Reuna titulo de compra, pagamentos, matricula historica, peticoes e decisoes do conflito, prova da "
                "entrega do bem ao terceiro, despesas, frutos e benfeitorias. Identifique todos os alienantes da "
                "cadeia e qualquer clausula de garantia. Um calculo por rubrica evita duplicar preco, valorizacao e "
                "obra ja indenizada.\n\nA estrategia pode ser incidental ou autonoma conforme a fase do processo. "
                "Nenhuma pagina consegue prometer restituicao integral antes de saber se houve perda efetiva, qual "
                "era o direito anterior e se o adquirente assumiu conscientemente o risco."
            ),
        ],
        "faq": [
            {"q": "Sem denunciar o vendedor no primeiro processo eu perco a garantia?", "a": "Nao automaticamente. O STJ admite acao autonoma de eviccao; a qualidade da defesa e a prova do nexo continuam relevantes."},
            {"q": "Perda de parte do terreno permite desfazer toda a compra?", "a": "Somente quando a parte perdida for consideravel; nos demais casos, a resposta legal tende a ser indenizacao proporcional."},
        ],
        "official_sources": [
            source(CC + "#art447", "Codigo Civil, arts. 447 a 457", "garantia da eviccao, clausulas, indenizacao e perda parcial"),
            source(CC + "#art450", "Codigo Civil, art. 450", "componentes e referencia temporal da indenizacao do evicto"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D014122", "STJ, Informativo de Jurisprudencia 519", "carater facultativo da denunciacao da lide e possibilidade de acao autonoma"),
        ],
    },
    "imob-area-menor-escritura": {
        "opening": (
            "Encontrar area menor que a indicada no titulo nao produz uma solucao automatica. O artigo 500 do "
            "Codigo Civil distingue venda por medida, em que a extensao influencia o preco, da venda de coisa certa "
            "e discriminada, em que a metragem aparece apenas como referencia. A diferenca de ate um vigesimo cria "
            "presuncao relativa, nao uma tolerancia que apaga todo direito. Alem de medir corretamente, e preciso "
            "conferir contrato, matricula, registro e o prazo decadencial de um ano previsto no artigo 501."
        ),
        "sections": [
            section(
                "Na venda por medida, o comprador possui tres remedios",
                "Se o preco foi estipulado por extensao ou a area determinada foi decisiva, a falta pode autorizar "
                "complemento da area. Sendo impossivel, o comprador pode pedir resolucao ou abatimento proporcional. "
                "Se a area real for maior e o vendedor provar que ignorava a medida exata, o comprador pode completar "
                "o preco ou devolver o excesso, quando possivel.\n\nPlanta, anuncio, preco por metro quadrado e "
                "negociacao ajudam a provar que a medida compunha o objeto. A simples presenca de numeros na escritura "
                "nao resolve sozinha a classificacao."
            ),
            section(
                "Cinco por cento e presuncao, nao franquia absoluta",
                "O paragrafo primeiro do artigo 500 presume que a referencia a dimensoes foi apenas enunciativa "
                "quando a diferenca nao excede um vigesimo da area total. O comprador pode superar essa presuncao "
                "demonstrando que, mesmo menor, a diferenca nao teria sido aceita. Por outro lado, diferenca superior "
                "a cinco por cento nao garante automaticamente resolucao: ainda se examinam modalidade da venda, "
                "relevancia e possibilidade de complemento.\n\nEm venda ad corpus, o bem e identificado como corpo "
                "certo, por limites e caracteristicas proprias. Rotular o contrato dessa forma nao basta se a prova "
                "mostrar que a metragem determinou preco ou finalidade."
            ),
            section(
                "O artigo 501 fixa decadencia de um ano",
                "O direito de propor as acoes do artigo 500 decai em um ano contado do registro do titulo. Se a "
                "imissao na posse foi atrasada por culpa do vendedor, o prazo corre da posse. Esse marco nao deve ser "
                "substituido pela data em que o comprador resolveu contratar topografo, embora a descoberta tardia "
                "possa ser relevante para outras alegacoes juridicamente distintas.\n\nNotificacao ou negociacao "
                "informal nao devem ser tratadas como suspensao certa da decadencia. Consulte a certidao do registro e "
                "a prova da entrega da posse assim que a divergencia surgir."
            ),
            section(
                "Retificacao registral e pretensao contratual nao sao iguais",
                "Se o terreno fisico coincide com o que as partes sempre ocuparam, mas a matricula contem erro de "
                "descricao, pode caber retificacao nos termos do artigo 213 da Lei de Registros Publicos, com planta, "
                "memorial, responsabilidade tecnica e participacao dos confrontantes conforme o caso. Retificar a "
                "matricula nao cria area que invade vizinho nem substitui aquisicao do dominio faltante.\n\nQuando o "
                "vendedor entregou efetivamente menos terreno, a questao e contratual e pode coexistir com conflito de "
                "limites. Levantamento georreferenciado deve comparar titulo, marcos e ocupacao sem mover cercas por "
                "conta propria."
            ),
            section(
                "Documentos permitem escolher a via correta",
                "Reuna contrato, escritura, certidao integral da matricula, planta aprovada, cadastro municipal, "
                "levantamento assinado e comprovante do registro e da posse. Verifique se a diferenca esta na area "
                "total, util, privativa ou comum; conceitos diferentes nao podem ser comparados como se fossem uma "
                "medida unica.\n\nUma revisao tecnica e juridica deve classificar a venda, contar o prazo e identificar "
                "se ha erro registral, descumprimento contratual ou disputa de divisa. Abatimento e resolucao dependem "
                "dessa prova, sem resultado automatico pelo percentual isolado."
            ),
        ],
        "faq": [
            {"q": "Diferenca menor que cinco por cento nunca gera direito?", "a": "Pode gerar, se o comprador provar que a medida foi determinante e que nao teria aceitado a diferenca; a lei estabelece presuncao relativa."},
            {"q": "O prazo de um ano conta do laudo?", "a": "Em regra, o artigo 501 conta do registro do titulo, ou da posse quando esta foi atrasada por culpa do vendedor."},
        ],
        "official_sources": [
            source(CC + "#art500", "Codigo Civil, art. 500", "venda por medida, venda de coisa certa, presuncao de um vigesimo e remedios"),
            source(CC + "#art501", "Codigo Civil, art. 501", "decadencia de um ano e marco excepcional da imissao na posse"),
            source(LRP + "#art213", "Lei 6.015/1973, art. 213", "procedimentos de retificacao do registro imobiliario"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20210426&formato=PDF&nreg=202002534078&salvar=false&seq=2027113&tipo=0", "STJ, REsp 1.898.171/SP", "aplicacao do prazo decadencial do artigo 501 a pretensao por diferenca de area"),
        ],
    },
    "imob-metragem-planta-menor": {
        "opening": (
            "A area informada na planta, no quadro de areas e na publicidade precisa ser comparada com a mesma "
            "categoria medida depois da entrega. Area privativa nao e area total, comum ou equivalente de construcao. "
            "Confirmada diferenca real, o CDC vincula a oferta, mas o Codigo Civil ainda pode disciplinar a falta de "
            "metragem e o prazo da pretensao. Nao existe uma tolerancia tecnica universal que autorize reduzir toda "
            "unidade em determinado percentual, nem toda divergencia pequena permite desfazer o contrato."
        ),
        "sections": [
            section(
                "Primeiro compare conceitos e documentos equivalentes",
                "Memorial de incorporacao, quadro NBR, contrato, planta comercial e matricula podem exibir numeros "
                "distintos porque medem superficies diferentes. Um profissional habilitado deve indicar paredes, "
                "vazios, vagas, depositos e areas comuns incluidos em cada numero. Comparar area privativa anunciada "
                "com area util aferida por outro metodo produz falso deficit.\n\nO artigo 32 da Lei 4.591 exige "
                "documentacao registral da incorporacao, e a oferta suficientemente precisa integra o contrato pelo "
                "artigo 30 do CDC. Preserve a versao do anuncio e da planta vigente na assinatura, nao apenas material "
                "publicitario alterado depois."
            ),
            section(
                "Oferta descumprida e falta de area possuem remedios proprios",
                "Pelo artigo 35 do CDC, a recusa ao cumprimento da oferta permite exigir cumprimento forcado, aceitar "
                "prestacao equivalente ou resolver o contrato com restituicao e perdas e danos. Abatimento proporcional "
                "pode decorrer do regime do vicio e da venda por medida, mas nao deve ser atribuido a uma opcao literal "
                "inexistente no artigo 35.\n\nO artigo 500 do Codigo Civil permite complemento, resolucao ou abatimento "
                "na venda ad mensuram. A relacao de consumo nao elimina automaticamente esse regime. O STJ aplica a "
                "decadencia de um ano do artigo 501 a pretensoes de diferenca de area, inclusive em controversias com "
                "adquirente consumidor."
            ),
            section(
                "Diferenca pequena nao garante resolucao",
                "A presuncao de um vigesimo do artigo 500 e relativa e pode ser superada se a medida era determinante. "
                "No sentido inverso, o STJ ja afastou a resolucao quando a diferenca era insignificante e nao impedia "
                "o uso normal da unidade. Percentual, destino do comodo, possibilidade de complemento, valor e impacto "
                "funcional precisam ser examinados em conjunto.\n\nClausula contratual de tolerancia nao autoriza "
                "informacao enganosa nem desvio ilimitado. Sua validade depende de transparencia, metodo e ausencia de "
                "desvantagem abusiva, e nao substitui a medicao concreta."
            ),
            section(
                "O prazo exige consulta imediata ao registro",
                "O artigo 501 conta um ano do registro do titulo para as acoes do artigo 500; se a posse atrasou por "
                "culpa do alienante, conta-se da imissao. Reclamar na assistencia tecnica sem definir a pretensao nao "
                "deve ser tratado como prorrogacao segura. Data das chaves e data do registro podem ser diferentes, e "
                "ambas devem constar da cronologia.\n\nOutros pedidos consumeristas podem ter disciplina propria, mas "
                "isso nao permite ignorar o prazo especifico da falta de area. Laudo tardio nao reinicia automaticamente "
                "a decadencia."
            ),
            section(
                "Laudo e negociacao devem tratar do impacto real",
                "Solicite planta aprovada, memorial, quadro de areas, habite-se, matricula e medicao com responsabilidade "
                "tecnica. O laudo deve declarar o metodo, a margem de medicao e a categoria comparada. Orcamento de obra "
                "nao prova sozinho perda de metragem, e avaliacao de mercado deve explicar como o deficit afeta o preco.\n\n"
                "Na negociacao, identifique se o pedido e corrigir documento, complementar area, abater preco ou resolver. "
                "Dano moral e perdas adicionais exigem fatos e prova; a mera diferenca numerica nao garante compensacao."
            ),
        ],
        "faq": [
            {"q": "A construtora pode entregar sempre ate cinco por cento a menos?", "a": "Nao. Um vigesimo e presuncao relativa do Codigo Civil, nao autorizacao tecnica universal nem dispensa do dever de informar."},
            {"q": "Area privativa e area util sao a mesma coisa?", "a": "Nem sempre. O metodo e os elementos incluidos devem ser conferidos antes de afirmar que houve deficit."},
        ],
        "official_sources": [
            source(CDC + "#art30", "Codigo de Defesa do Consumidor, art. 30", "vinculacao da informacao ou publicidade suficientemente precisa"),
            source(CDC + "#art35", "Codigo de Defesa do Consumidor, art. 35", "alternativas legais diante da recusa de cumprimento da oferta"),
            source(CC + "#art500", "Codigo Civil, arts. 500 e 501", "remedios da falta de area, presuncao relativa e prazo decadencial"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20210426&formato=PDF&nreg=202002534078&salvar=false&seq=2027113&tipo=0", "STJ, REsp 1.898.171/SP", "prazo do artigo 501 em controversia de diferenca de area de imovel adquirido por consumidor"),
        ],
    },
    "imob-itbi-base-calculo": {
        "opening": (
            "O municipio nao pode transformar uma tabela unilateral de valor de referencia em piso automatico do "
            "ITBI. No Tema Repetitivo 1.113, o STJ definiu que a base e o valor do imovel transmitido em condicoes "
            "normais de mercado; o valor declarado na transacao goza de presuncao relativa e so pode ser afastado "
            "em procedimento proprio de arbitramento, com contraditorio. A tese tambem impede vincular a base do ITBI "
            "a do IPTU. Isso nao torna intocavel um preco simulado ou sem suporte documental."
        ),
        "sections": [
            section(
                "Valor venal significa valor de mercado da transmissao",
                "O artigo 38 do CTN usa valor venal dos bens ou direitos transmitidos. Segundo o Tema 1.113, trata-se "
                "do valor pelo qual o bem seria negociado em condicoes normais, consideradas as particularidades da "
                "operacao. O valor cadastral do IPTU segue logica de lancamento em massa e nao pode ser importado como "
                "base minima obrigatoria.\n\nNa compra comum entre partes independentes, o preco declarado presume-se "
                "compativel com o mercado. A presuncao nao e absoluta: parentesco, pagamento lateral, condicao anormal "
                "ou discrepancia demonstravel podem justificar fiscalizacao, sem autorizar aumento instantaneo por "
                "algoritmo municipal."
            ),
            section(
                "Arbitramento exige procedimento do artigo 148 do CTN",
                "Se a declaracao ou os documentos forem omissos ou nao merecerem fe, a autoridade pode arbitrar o "
                "valor mediante processo regular. O contribuinte deve conhecer criterios e elementos comparativos e "
                "poder contestar avaliacao, estado de conservacao, ocupacao e outras caracteristicas. Emitir guia ja "
                "calculada pelo maior valor, sem essa etapa, contraria a tese repetitiva.\n\nA administracao pode pedir "
                "documentos e realizar avaliacao individual. O Tema nao obriga aceitar valor simbolico nem impede "
                "lancamento complementar depois de apuracao valida. Declarar o preco real e manter rastreabilidade do "
                "pagamento continuam indispensaveis."
            ),
            section(
                "A impugnacao depende da lei e do processo municipal",
                "Contrato, escritura, comprovantes, avaliacao do financiamento, fotos e negocios comparaveis podem "
                "sustentar o valor. A guia, a memoria de calculo e a norma local mostram se houve valor de referencia "
                "automatico ou arbitramento formal. Cada municipio define canal, prazo e autoridade revisora dentro "
                "dos limites nacionais.\n\nNao existe uma obrigacao geral de esgotar a via administrativa antes de "
                "qualquer acao judicial, mas perder prazo de impugnacao pode dificultar a solucao local. Protocolar "
                "pedido tambem nao suspende por si so exigibilidade, registro ou encargos; esse efeito depende da lei "
                "e das medidas adotadas."
            ),
            section(
                "Mandado de seguranca nao serve para toda avaliacao",
                "Quando a ilegalidade e demonstravel por documentos preconstituidos, pode-se examinar mandado de "
                "seguranca dentro do prazo proprio. Se a controversia exige pericia sobre valor de mercado, acao de "
                "conhecimento ou anulatoria pode ser mais adequada. Pagamento a maior pode permitir repeticao do "
                "indebito, observadas legitimidade, prova e prescricao.\n\nNao se deve prometer recalculo pelo preco "
                "contratual sem testar sua aderencia ao mercado. O pedido correto pode ser afastar a tabela automatica "
                "e exigir procedimento de arbitramento, nao declarar verdadeiro qualquer numero escolhido pelas partes."
            ),
            section(
                "Organize os valores antes de contestar",
                "Monte uma tabela com preco, financiamento, valor cadastral do IPTU, valor de referencia, base da guia "
                "e aliquota. Separe eventuais moveis ou direitos que nao integram a transmissao e confira se o negocio "
                "inclui usufruto, cessao ou outro fato tributavel segundo a lei local.\n\nUma revisao tributaria pode "
                "comparar a cobranca com as tres teses do Tema 1.113, selecionar a prova de mercado e contar os prazos. "
                "A autoridade preserva poder de fiscalizar, mas deve usa-lo pelo processo previsto no CTN."
            ),
        ],
        "faq": [
            {"q": "A prefeitura e obrigada a aceitar qualquer preco da escritura?", "a": "Nao. O preco tem presuncao relativa; pode ser afastado por arbitramento regular com elementos concretos e contraditorio."},
            {"q": "O valor do IPTU pode ser usado como piso do ITBI?", "a": "Nao segundo o Tema 1.113. As bases possuem criterios distintos, e a do ITBI nao fica previamente vinculada a do IPTU."},
        ],
        "official_sources": [
            source(CTN + "#art38", "Codigo Tributario Nacional, art. 38", "valor venal como base legal do ITBI"),
            source(CTN + "#art148", "Codigo Tributario Nacional, art. 148", "arbitramento em processo regular quando declaracoes nao merecem fe"),
            source("https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1113&cod_tema_inicial=1113&novaConsulta=true&tipo_pesquisa=T", "STJ, Tema Repetitivo 1.113", "valor de mercado, presuncao do preco declarado e vedacao do valor de referencia unilateral"),
        ],
    },
}


if __name__ == "__main__":
    apply_updates(EXPECTED_SHA256, UPDATES, "imobiliario-09-a")
