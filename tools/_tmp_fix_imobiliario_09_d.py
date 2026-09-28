#!/usr/bin/env python3
"""Reescreve as páginas 18 a 22 do shard imobiliário-09."""

from _tmp_fix_imobiliario_09_lib import apply_updates, section, source


EXPECTED_SHA256 = "d71fbf5ce21eed0cd0d51e340dc268b1777dbcd849c1f25ac9bf974ee976db4b"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
CTN = "https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm"
LRP = "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm"


UPDATES = {
    "imob-compra-imovel-leilao-ocupado": {
        "opening": (
            "Imóvel ocupado não segue um único procedimento depois do leilão. Na arrematação judicial, o artigo 901 "
            "do CPC prevê carta de arrematação acompanhada do mandado de imissão na posse, após depósito ou garantias e "
            "pagamento das despesas indicadas. No leilão decorrente de alienação fiduciária, o artigo 30 da Lei 9.514 "
            "assegura reintegração de posse, inclusive ao adquirente, com liminar para desocupação em sessenta dias quando "
            "comprovada a consolidação. Ocupante, edital, tipo de leilão e vícios pendentes precisam ser identificados."
        ),
        "sections": [
            section(
                "Arrematação judicial produz carta e mandado próprios",
                "O auto registra condições da alienação. Cumpridos depósito ou garantia, comissão e demais despesas, a carta "
                "do imóvel deve trazer descrição, referência à matrícula, cópia do auto, prova do ITBI e indicação de ônus. "
                "O respectivo mandado de imissão pode ser expedido no processo executivo, sem exigir em toda situação nova ação "
                "de conhecimento.\n\nRegistro da carta continua essencial para publicidade e domínio, mas o texto do artigo 901 "
                "não deve ser reescrito como se o mandado dependesse sempre de certidão já lançada em nome do arrematante. O "
                "juízo da execução, o edital e a fase da arrematação determinam o requerimento adequado."
            ),
            section(
                "Alienação fiduciária usa reintegração do artigo 30",
                "Quando o imóvel foi consolidado pelo procedimento da Lei 9.514 e vendido nos leilões previstos nessa lei, o "
                "fiduciário, cessionário, sucessor ou adquirente pode pedir reintegração. A liminar estabelece desocupação em "
                "sessenta dias desde que a consolidação da propriedade esteja comprovada na forma legal. Não se trata de prazo "
                "automático contado da compra nem de retirada privada do ocupante.\n\nA Lei 9.514 também disciplina controvérsias "
                "sobre cobrança e leilão depois da consolidação, com ressalvas no texto vigente. Notificação do devedor, matrícula "
                "e observância do procedimento devem ser lidas antes de presumir que toda impugnação se converte em perdas e danos."
            ),
            section(
                "Ocupação por terceiro exige conhecer o título alegado",
                "Antigo proprietário, locatário, companheiro, possuidor ou pessoa sem título apresentam defesas diferentes. Contrato "
                "de locação pode ou não ser oponível conforme data, cláusula de vigência, registro, ciência e regime do leilão. "
                "Benfeitorias podem gerar discussão de indenização ou retenção, sem impedir automaticamente a entrega.\n\nVisite quando "
                "o edital permitir, consulte processos e identifique pessoas no local sem constrangimento ou exposição. Edital que "
                "atribui ao arrematante a desocupação distribui custo e risco, mas não autoriza corte de serviços, troca clandestina "
                "de fechadura ou remoção de bens sem ordem."
            ),
            section(
                "Arrematação pode ser impugnada nos limites do CPC",
                "O artigo 903 considera a arrematação perfeita e irretratável depois de assinado o auto, preservadas hipóteses de "
                "invalidação, ineficácia ou resolução e os prazos processuais correspondentes. Depois da carta, eventual ação autônoma "
                "de invalidação deve incluir o arrematante. A existência de impugnação não suspende por si toda posse, mas decisão "
                "específica pode alterar o andamento.\n\nAntes do lance, leia edital, matrícula, avaliação, débitos, recursos e "
                "responsabilidade por condomínio e tributos. Preço baixo precisa ser comparado com ocupação, obras e litígios, não "
                "apenas com a avaliação nominal."
            ),
            section(
                "Cumprimento deve preservar pessoas e bens",
                "Concedida a medida, oficial de justiça cumpre o mandado e o juízo decide prazo, apoio e providências. Bens deixados "
                "no local devem ser inventariados e tratados conforme a ordem, sem apropriação pelo arrematante. Acordo de saída pode "
                "definir data, vistoria e entrega de chaves, desde que voluntário e documentado.\n\nReúna edital, auto, carta, matrícula, "
                "pagamentos, identificação do ocupante e decisões. Uma análise jurídica escolhe imissão, reintegração ou providência "
                "incidental correta, sem prometer desocupação imediata ou ignorar defesa legítima."
            ),
        ],
        "faq": [
            {"q": "No leilão fiduciário o pedido é sempre imissão na posse?", "a": "Não. O artigo 30 da Lei 9.514 denomina a medida reintegração na posse e exige prova da consolidação."},
            {"q": "Posso retirar os bens do ocupante assim que arremato?", "a": "Não por iniciativa própria. Desocupação e destino dos bens devem seguir acordo válido ou ordem judicial."},
        ],
        "official_sources": [
            source(CPC + "#art901", "Código de Processo Civil, arts. 901 e 903", "carta, mandado de imissão e disciplina da arrematação judicial"),
            source("https://www.planalto.gov.br/ccivil_03/leis/l9514.htm#art30", "Lei 9.514/1997, art. 30", "reintegração de posse e desocupação em sessenta dias após consolidação"),
        ],
    },
    "imob-permuta-imoveis": {
        "opening": (
            "Permuta troca um bem por outro e segue, em grande parte, as regras da compra e venda, mas o artigo 533 do "
            "Código Civil traz ajustes próprios. A divisão legal refere-se às despesas do instrumento da troca, não a todos "
            "os emolumentos de cada registro. Na permuta entre ascendente e descendente, a exigência especial de consentimento "
            "surge quando os valores são desiguais. ITBI pode incidir sobre cada aquisição segundo a lei municipal, enquanto o "
            "ganho de capital da pessoa física distingue permuta sem dinheiro da operação com torna."
        ),
        "sections": [
            section(
                "Cada parte é alienante e adquirente",
                "Os dois imóveis precisam de matrícula, avaliação, exame de ônus e título registrável. Defeito, evicção, ocupação e "
                "dívida de um lado não desaparecem porque não houve preço integral em dinheiro. O contrato deve identificar valores "
                "atribuídos, estado, posse, tributos, condomínio, documentos e momento de cada transferência.\n\nSe uma entrega depende "
                "da outra, condições e solução para recusa precisam ser expressas. Uma permuta mal descrita como duas vendas pode "
                "alterar custos e prova; duas vendas independentes não viram permuta apenas porque os pagamentos se compensam informalmente."
            ),
            section(
                "Artigo 533 divide somente despesas do instrumento",
                "Salvo disposição em contrário, cada contratante paga metade das despesas com o instrumento da troca. Isso não significa "
                "que todos os registros, certidões, impostos e regularizações serão sempre divididos ao meio. As partes podem distribuir "
                "custos no contrato, respeitando responsabilidades tributárias e perante terceiros definidas em lei.\n\nO inciso II "
                "considera anulável a troca de valores desiguais entre ascendente e descendente sem consentimento dos outros descendentes "
                "e do cônjuge do alienante. Igualdade deve ser sustentada por avaliação séria, não por números artificiais escolhidos "
                "apenas para evitar anuência."
            ),
            section(
                "Torna precisa aparecer no preço e no pagamento",
                "Quando um imóvel vale mais, a diferença em dinheiro é chamada torna. O contrato deve indicar valor, vencimento, garantia, "
                "correção e efeito do inadimplemento. Financiamento da torna ou assunção de dívida exige anuência do credor quando necessária; "
                "não se presume liberação do devedor antigo.\n\nPara pessoa física residente, a Receita Federal informa que a permuta de "
                "unidades imobiliárias sem recebimento de diferença em dinheiro não fica sujeita ao ganho de capital. Com torna, a apuração "
                "recai sobre a parcela nos termos fiscais. Pessoa jurídica e operação empresarial seguem regime próprio e não devem usar "
                "essa regra pessoal sem análise contábil."
            ),
            section(
                "ITBI e forma são examinados para cada transmissão",
                "A permuta produz duas aquisições, e a lei do município de cada imóvel define contribuinte, base e alíquota do ITBI. O "
                "artigo 35 do CTN oferece a moldura nacional, sem criar isenção por ausência de dinheiro. Valores declarados precisam "
                "refletir condições de mercado e podem ser arbitrados apenas pelo procedimento tributário regular.\n\nA escritura pública "
                "é exigida pelo artigo 108 quando o valor ultrapassa o limite e não há exceção legal. Depois do título, cada transmissão "
                "deve ser registrada na matrícula competente; receber as chaves não transfere domínio."
            ),
            section(
                "Fechamento simultâneo reduz risco de prestação isolada",
                "Confirme certidões próximas da assinatura, guias, quitações e disponibilidade dos dois bens. Organize a apresentação dos "
                "títulos para que nenhuma parte transfira seu imóvel sem mecanismo contratual para receber o outro. Se cartórios ficam em "
                "circunscrições distintas, planeje documentos e condições de liberação.\n\nUma revisão jurídica e tributária deve simular "
                "custos dos dois lados e da torna. Não prometa ausência de imposto com base apenas no nome permuta nem atribua metade de "
                "toda despesa ao artigo 533."
            ),
        ],
        "faq": [
            {"q": "Permuta sem torna nunca paga imposto?", "a": "Não. A regra de ganho de capital da pessoa física não afasta eventual ITBI sobre cada aquisição nem outros regimes tributários."},
            {"q": "Cada parte paga metade de todos os custos?", "a": "O artigo 533 divide, salvo ajuste contrário, as despesas do instrumento; impostos e registros precisam de análise própria."},
        ],
        "official_sources": [
            source(CC + "#art533", "Código Civil, art. 533", "despesas do instrumento e permuta desigual entre ascendente e descendente"),
            source("https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/ganhos-de-capital/operacoes-nao-sujeitas", "Receita Federal, operações não sujeitas a ganho de capital", "tratamento da pessoa física na permuta imobiliária sem diferença em dinheiro"),
            source(CTN + "#art35", "Código Tributário Nacional, art. 35", "moldura do ITBI aplicável às transmissões imobiliárias onerosas"),
            source(CC + "#art108", "Código Civil, art. 108", "forma pública quando o negócio ultrapassa o limite legal"),
        ],
    },
    "imob-retrovenda-verbete": {
        "opening": (
            "Retrovenda é cláusula especial da compra e venda de imóvel pela qual o vendedor reserva o direito de recobrar "
            "o bem no prazo máximo de três anos. Para exercer o resgate, precisa restituir o preço e reembolsar as despesas "
            "previstas no artigo 505 do Código Civil. Não é simples arrependimento nem promessa de recompra prorrogável. O "
            "direito pode ser exercido contra terceiro adquirente, razão pela qual a cláusula precisa constar do título e "
            "receber publicidade no registro. Estruturas usadas como empréstimo disfarçado exigem cautela contra simulação."
        ),
        "sections": [
            section(
                "Prazo de três anos é decadencial e máximo",
                "A reserva só cabe para coisa imóvel e deve integrar a compra e venda. O vendedor pode exercer dentro do período "
                "convencionado, limitado a três anos. Cláusula de cinco anos não amplia o teto, e aditivo posterior não deve ser "
                "tratado como reinício automático. Decadência extingue o próprio direito se ele não for exercido no prazo.\n\nO "
                "termo inicial e as condições do título precisam ser claros. Notificação pode demonstrar exercício, mas a recusa do "
                "comprador exige providência capaz de depositar integralmente o que é devido antes do fim da janela. Aguarde apenas o "
                "tempo necessário para apurar a conta: tratativas sem depósito ou ação adequada podem consumir a decadência. Preserve "
                "comprovante de recebimento da comunicação e qualquer resposta sobre valores ou acesso ao imóvel."
            ),
            section(
                "Resgate inclui preço, despesas e benfeitorias delimitadas",
                "O artigo 505 manda restituir o preço recebido e reembolsar despesas do comprador. Inclui gastos efetuados durante "
                "o período de resgate com autorização escrita do vendedor e despesas para benfeitorias necessárias. Melhorias úteis "
                "ou luxuosas feitas sem a autorização descrita não entram automaticamente na conta.\n\nTributos, emolumentos, conservação "
                "e frutos devem ser classificados conforme título e lei, sem somar toda despesa pessoal do comprador. Apuração detalhada "
                "reduz o risco de um depósito insuficiente impedir a recuperação do domínio."
            ),
            section(
                "Recusa do comprador leva a depósito judicial",
                "Se o comprador não aceita receber as quantias, o artigo 506 determina que o vendedor as deposite judicialmente. O "
                "parágrafo único é expresso: verificada insuficiência, o vendedor não será restituído no domínio enquanto o comprador "
                "não estiver integralmente pago. Não basta depositar apenas o preço nominal e discutir depois todas as despesas.\n\nA "
                "petição deve apresentar título, registro, cálculo, oferta de pagamento e prova da recusa. Medida urgente depende dos "
                "requisitos processuais e não autoriza retirada privada do ocupante."
            ),
            section(
                "Direito é transmissível e alcança terceiro adquirente",
                "O artigo 507 permite cessão e transmissão do direito a herdeiros e legatários. Havendo vários titulares, o exercício "
                "segue as regras do dispositivo, sem fracionar o imóvel unilateralmente. Pelo artigo 508, o direito pode ser exercido "
                "contra terceiro adquirente.\n\nEssa eficácia torna indispensável que o título registrado revele a retrovenda. Quem "
                "compra durante o prazo deve ler a matrícula e calcular a possibilidade de resgate. Ocultar a cláusula ou manter apenas "
                "pacto paralelo cria disputa de publicidade e boa-fé que a formalização correta procura evitar."
            ),
            section(
                "Retrovenda não deve mascarar garantia de empréstimo",
                "Se o suposto comprador apenas entrega dinheiro como mútuo, o vendedor continua usando o imóvel e o valor de resgate "
                "funciona como dívida com encargos, pode haver discussão sobre simulação, usura, pacto comissório ou verdadeira natureza "
                "da operação. O nome dado ao contrato não prevalece contra os fatos.\n\nAvaliação, fluxo financeiro, posse, finalidade e "
                "negociação precisam ser documentados. Uma revisão civil e registral pode estruturar venda real com retrovenda ou indicar "
                "instrumento de garantia apropriado, sem prometer recuperação automática do imóvel ao final."
            ),
        ],
        "faq": [
            {"q": "As partes podem combinar retrovenda por mais de três anos?", "a": "Não. O artigo 505 fixa prazo máximo decadencial de três anos."},
            {"q": "Depositar apenas o preço original já recupera o imóvel?", "a": "Não necessariamente. Despesas reembolsáveis integram o resgate, e depósito insuficiente impede a restituição do domínio até pagamento integral."},
        ],
        "official_sources": [
            source(CC + "#art505", "Código Civil, arts. 505 a 508", "prazo, reembolso, depósito, transmissão e exercício contra terceiro"),
            source(LRP + "#art167", "Lei 6.015/1973, art. 167", "registro da compra e venda condicional e publicidade imobiliária"),
        ],
    },
    "imob-preferencia-condomino-venda-fracao": {
        "opening": (
            "O artigo 504 do Código Civil protege o condômino quando outro coproprietário vende sua parte de coisa comum "
            "indivisível a pessoa estranha sem oferecer as mesmas condições. O direito não abrange automaticamente a venda "
            "de unidade autônoma em condomínio edilício nem qualquer imóvel divisível. Para haver a parte para si, o condômino "
            "precisa agir em cento e oitenta dias e depositar o preço. Se não houve comunicação prévia, o STJ conta o prazo do "
            "registro da escritura, que torna o negócio publicamente cognoscível."
        ),
        "sections": [
            section(
                "Preferência exige coisa indivisível e venda a estranho",
                "A regra incide na alienação onerosa de quinhão ideal da coisa que não pode ser comodamente dividida. Venda a outro "
                "condômino não aciona a preferência contra estranho. A negociação deve ser comparada com o título real: doação, permuta "
                "ou transferência de unidade autônoma podem ter disciplina diferente, e simulação do rótulo pode ser discutida.\n\nA "
                "indivisibilidade pode decorrer da natureza, da lei ou da inviabilidade econômica da divisão. Matrícula, planta e uso "
                "mostram se existe copropriedade pro indiviso ou unidades juridicamente independentes."
            ),
            section(
                "Oferta deve revelar todas as condições",
                "Antes de vender ao terceiro, o condômino deve informar preço, forma e prazo de pagamento, garantias, comissão e demais "
                "vantagens relevantes. Notificação judicial ou extrajudicial com comprovante facilita provar ciência inequívoca, embora "
                "o STJ admita outros meios idôneos. Convite vago para comprar, sem condições equivalentes, não inicia com segurança a escolha.\n\n"
                "O preferente precisa aceitar em igualdade, não selecionar apenas parcelas favoráveis. Se o terceiro obteve prazo, desconto "
                "ou encargo lateral, esses elementos devem entrar na comparação e no valor a depositar."
            ),
            section(
                "Prazo corre da ciência ou, sem aviso, do registro",
                "O artigo 504 fixa decadência de cento e oitenta dias. No REsp 1.628.478, o STJ decidiu que, ausente notificação prévia, "
                "o registro da escritura de compra e venda inicia o prazo, porque dá publicidade às informações do título. Se houve ciência "
                "inequívoca antes, a data comprovada pode antecipar a contagem.\n\nNão se deve aguardar indefinidamente alegando descoberta "
                "subjetiva depois do registro. Certidão histórica e cópia da escritura revelam data, preço e condições. Negociação informal "
                "não suspende automaticamente a decadência."
            ),
            section(
                "Depósito integral integra o exercício da preferência",
                "O condômino busca haver para si a parte vendida mediante ação de preferência e depósito do preço nas condições do artigo. "
                "Não é simples adjudicação compulsória baseada em promessa anterior. Depósito incompleto ou fora do prazo pode levar à "
                "decadência; necessidade de financiamento não autoriza presumir extensão judicial da janela legal.\n\nComprador e vendedor "
                "devem participar do contraditório. A sentença, se procedente, produz os efeitos necessários sobre o quinhão e o preço, "
                "sem transformar o terceiro em autor automático de perdas e danos contra todos os envolvidos."
            ),
            section(
                "Vários condôminos seguem a prioridade do parágrafo único",
                "Concorrendo mais de um, prefere quem tiver benfeitorias de maior valor; faltando benfeitorias, quem possuir quinhão maior. "
                "Em igualdade, os comproprietários interessados podem haver a parte depositando previamente o preço. Prova das benfeitorias, "
                "titularidade e frações deve acompanhar a medida. Avaliação das melhorias deve separar obra incorporada à coisa de simples "
                "despesa de uso, e a certidão deve confirmar o tamanho atual de cada quinhão antes de aplicar a prioridade.\n\nAntes da venda, notificar todos e registrar respostas reduz litígio. "
                "Depois dela, organize matrícula, escritura, comunicações e recursos para o depósito. A análise jurídica deve contar o "
                "prazo de forma conservadora, sem prometer preferência quando o objeto é divisível ou unidade autônoma."
            ),
        ],
        "faq": [
            {"q": "Os 180 dias contam sempre de quando descobri a venda?", "a": "Não. Sem notificação prévia, o STJ fixou o registro da escritura como início, por presumir ciência pública do negócio."},
            {"q": "Basta ajuizar sem depositar o preço?", "a": "Não. O artigo 504 vincula o exercício ao depósito do preço, e a integralidade e o prazo precisam ser observados."},
        ],
        "official_sources": [
            source(CC + "#art504", "Código Civil, art. 504", "preferência, prazo, depósito e prioridade entre condôminos"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D017947", "STJ, Informativo de Jurisprudência 683", "registro como termo inicial quando não houve notificação prévia"),
            source(CC + "#art1245", "Código Civil, art. 1.245", "registro do título e publicidade da transferência imobiliária"),
        ],
    },
    "imob-vendedor-nao-entrega-imovel": {
        "opening": (
            "Comprador que cumpriu o contrato e não recebe a posse pode exigir cumprimento ou resolução, com perdas e danos "
            "quando provadas, nos termos do artigo 475 do Código Civil. O caminho processual depende do direito já adquirido. "
            "Proprietário registrado pode buscar imissão fundada no domínio; comprador apenas contratual pede tutela específica "
            "das obrigações de entregar, outorgar título ou desocupar, conforme o instrumento. O artigo 538 do CPC disciplina o "
            "cumprimento de decisão de entrega de coisa, não cria sozinho uma ação autônoma baseada em promessa quitada."
        ),
        "sections": [
            section(
                "Mora pode decorrer do prazo ou de interpelação",
                "Se o contrato fixa data certa para entrega, o artigo 397 do Código Civil coloca o devedor em mora pelo vencimento, "
                "salvo condição ou justificativa juridicamente relevante. Sem termo claro, interpelação judicial ou extrajudicial pode "
                "ser necessária para constituir mora. Notificar é útil para definir recusa e prazo, mas não deve ser anunciada como "
                "requisito universal quando a obrigação já venceu de pleno direito.\n\nConfira se pagamento, financiamento, registro, "
                "baixa de gravame ou outra condição estava pendente. O comprador não pode exigir entrega ignorando obrigação simultânea "
                "que deixou de cumprir."
            ),
            section(
                "Cumprimento específico segue os artigos 497 e 498",
                "Na ação de conhecimento, o juiz pode conceder tutela específica da obrigação de fazer ou entregar coisa, adotando medidas "
                "capazes de produzir o resultado devido. O pedido deve refletir o contrato: entrega de chaves, desocupação, outorga de "
                "escritura e registro não são sinônimos. Se a propriedade já está registrada no nome do comprador, a causa possessória "
                "também muda.\n\nDepois de reconhecida a obrigação de entregar, o artigo 538 rege o cumprimento da sentença e permite prazo "
                "para entrega, mandado de busca e apreensão de móvel ou imissão na posse de imóvel. Ele não dispensa a fase que reconhece "
                "o direito quando o vendedor ainda o contesta."
            ),
            section(
                "Tutela provisória exige probabilidade e perigo",
                "O artigo 300 permite medida de urgência quando há probabilidade do direito e perigo de dano ou risco ao resultado útil. "
                "Contrato, quitação, vencimento, matrícula e prova da recusa sustentam a análise. Ocupação por família, terceiro com título, "
                "irreversibilidade e necessidade de contraditório também pesam. Não há prazo garantido de dias ou semanas para receber o bem.\n\n"
                "Entrada forçada, corte de água ou troca de fechadura sem ordem podem gerar responsabilidade. Mesmo com preço pago, o "
                "comprador deve usar a via judicial ou acordo formal para obter a posse."
            ),
            section(
                "Danos materiais precisam de nexo e mitigação",
                "Aluguel necessário em outra moradia, armazenagem, mudança perdida e renda locatícia frustrada podem ser examinados com "
                "recibos, datas e prova de que decorrem diretamente do atraso. Lucros cessantes não são um aluguel presumido em toda compra, "
                "especialmente quando o imóvel não estava apto ou destinado à locação. O prejudicado também deve evitar agravar o dano.\n\n"
                "Dano moral exige repercussão além do inadimplemento comum e não nasce automaticamente da falta de chaves. Multa contratual "
                "pode coexistir ou limitar outras parcelas conforme redação, natureza e vedação ao enriquecimento duplicado."
            ),
            section(
                "Cumprimento ou resolução exigem escolha coerente",
                "Se a entrega ainda interessa e é possível, o comprador pode insistir no cumprimento. Se o atraso destruiu a finalidade ou "
                "o bem foi validamente destinado a terceiro, a resolução com restituição e indenização comprovada pode ser mais adequada. "
                "Não se acumulam soluções incompatíveis como ficar definitivamente com o imóvel e receber todo o preço de volta.\n\nReúna "
                "contrato, pagamentos, matrícula, notificações, despesas e prova da ocupação. Uma revisão jurídica pode formular tutela e "
                "quantificar danos defensáveis, sem prometer liminar, prazo de desocupação ou indenização moral."
            ),
        ],
        "faq": [
            {"q": "O artigo 538 permite imissão imediata só com o contrato quitado?", "a": "Não. Ele disciplina o cumprimento de decisão que reconheceu a entrega; o direito contratual pode precisar ser definido antes."},
            {"q": "Notificação é sempre necessária para constituir mora?", "a": "Não. Obrigação positiva, líquida e com termo certo pode gerar mora no vencimento; sem termo, a interpelação pode ser necessária."},
        ],
        "official_sources": [
            source(CC + "#art475", "Código Civil, arts. 475 e 397", "escolha diante do inadimplemento e constituição da mora"),
            source(CPC + "#art497", "Código de Processo Civil, arts. 497 e 498", "tutela específica das obrigações de fazer e entregar coisa"),
            source(CPC + "#art538", "Código de Processo Civil, art. 538", "cumprimento de decisão que reconhece obrigação de entregar coisa"),
            source(CPC + "#art300", "Código de Processo Civil, art. 300", "requisitos da tutela provisória de urgência"),
        ],
    },
}


if __name__ == "__main__":
    apply_updates(EXPECTED_SHA256, UPDATES, "imobiliario-09-d")
