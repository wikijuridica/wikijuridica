# -*- coding: utf-8 -*-
import json, os, re, tempfile, unicodedata

def words_of(s):
    def deaccent(t):
        return ''.join(c for c in unicodedata.normalize('NFKD', t)
                       if not unicodedata.combining(c))
    return re.findall(r'[^\W_]+', deaccent((s or '').lower()), re.UNICODE)

def wc(page):
    total = len(words_of(page.get('opening', '')))
    for s in page.get('sections', []):
        total += len(words_of(s.get('heading', '')))
        total += len(words_of(s.get('text', '')))
    for f in page.get('faq', []):
        total += len(words_of(f.get('q', '')))
        total += len(words_of(f.get('a', '')))
    return total

CLT = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm"
L14442 = "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14442.htm"
LGPD = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"
L8213 = "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm"
LBI = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
SUM428 = "https://www.tst.jus.br/-/nova-redacao-da-sumula-428-reconhece-sobreaviso-em-escala-com-celular"
TST_TELEWORK_WRITTEN = "https://www.tst.jus.br/-/sem-aditivo-contratual-escrito-sobre-teletrabalho-corretora-tera-de-pagar-horas-extras-a-gerente"
TST_IRR125 = "https://www.tst.jus.br/documents/d/guest/irr125-2-pdf"
TST_ASSEDIO = "https://www.tst.jus.br/documents/10157/26144164/Campanha%2Bass%C3%A9dio%2Bmoral%2Be%2Bsexual%2B-%2Ba5%2B-%2B12092022.pdf/f10d0579-f70f-2a1e-42ae-c9dcfcc1fd47?t=1665432735176"

pages = []

# 1
pages.append({
"intent_id":"trab-teletrabalho-sem-contrato-escrito",
"title":"Teletrabalho sem aditivo escrito: o que muda no contrato",
"meta_description":"Foi para o home office sem assinar nada? Veja por que a Lei 14.442 exige teletrabalho por escrito e o que a falta do aditivo pode custar à empresa.",
"h1":"Fui para o home office sem aditivo: preciso formalizar?",
"opening":"Muita gente migrou para o trabalho remoto no meio de uma reunião, por mensagem ou por um simples \"a partir de segunda você fica em casa\", sem que nada disso fosse para o papel. O regime mudou na prática, mas o contrato continuou dizendo que o serviço é presencial. Essa distância entre o que se combina e o que se assina não é detalhe burocrático: é justamente onde nascem os problemas de custo, jornada e retorno forçado.\n\nA Lei 14.442/2022, que reescreveu as regras de teletrabalho na CLT, tratou a formalização como condição do regime, não como formalidade dispensável. Entender o que o texto escrito protege ajuda a decidir se vale cobrar o aditivo antes que uma dessas questões apareça.",
"sections":[
{"heading":"O que a redação atual do art. 75-C exige","text":"O art. 75-C da CLT determina que a prestação de serviços em teletrabalho conste expressamente do contrato individual. A redação vigente não repete a antiga exigência de listar no contrato todas as atividades: esse trecho foi retirado pela Lei 14.442/2022. O ponto obrigatório hoje é registrar o próprio regime remoto.\n\nPara passar do presencial ao teletrabalho, o § 1º exige mútuo acordo e aditivo. Trabalhar de casa sem esse registro não apaga o serviço realmente prestado nem transforma automaticamente todas as discussões em favor de uma das partes; cria, isso sim, uma desconformidade documental que precisa ser confrontada com a rotina efetiva."},
{"heading":"O que precisa ficar claro no documento","text":"O art. 75-D manda prever por escrito a responsabilidade por equipamentos, infraestrutura e eventual reembolso de despesas. Jornada também precisa ser tratada com precisão: o art. 75-B admite trabalho remoto por jornada ou por produção ou tarefa, e a exceção às regras de duração alcança esta última modalidade, nos termos do art. 62, III.\n\nO aditivo deve retratar o que ocorre de verdade. Chamar de produção um trabalho com horário controlado não resolve, por si só, uma controvérsia sobre horas extras. No sentido inverso, a simples existência de mensagens ou reuniões não prova automaticamente toda a jornada alegada. Documentos e rotina precisam ser examinados em conjunto."},
{"heading":"O que fazer quando a empresa não formaliza","text":"Peça o aditivo por e-mail ou pelo canal interno de recursos humanos, descrevendo o regime praticado, os dias remotos e como foram tratados equipamentos e despesas. Guarde também mensagens de convocação, registros de acesso, escalas e comprovantes relacionados ao trabalho em casa.\n\nEm 2025, o TST divulgou caso em que a ausência do aditivo foi relevante para afastar o enquadramento excepcional invocado por uma corretora e reconhecer horas extras de gerente. É um precedente ligado às provas daquele processo, não uma regra de que todo home office informal gera automaticamente horas extras."},
{"heading":"Quando buscar análise individual","text":"Nem toda falta de aditivo produz a mesma consequência. O problema concreto pode estar na jornada, nos custos, na mudança imposta para o remoto ou no retorno sem a transição legal. Antes de formular um pedido, organize contrato, comunicações, registros de horário e despesas.\n\nUma orientação jurídica individual pode confrontar esses documentos com a rotina efetiva e indicar se a medida adequada é pedir formalização, corrigir uma cláusula ou discutir diferenças específicas. O objetivo é avaliar a prova, sem presumir que a irregularidade documental decide sozinha todo o caso."}
],
"faq":[
{"q":"O teletrabalho sem aditivo é ilegal?","a":"A falta do registro escrito contraria o art. 75-C, mas não anula o contrato de emprego nem define sozinha jornada, despesas ou outros efeitos. A rotina efetiva e as demais provas continuam relevantes."},
{"q":"Posso me recusar a ir para o home office sem aditivo?","a":"A mudança de regime, pela CLT, depende de mútuo acordo registrado em aditivo. Você pode condicionar a aceitação à formalização por escrito das condições, inclusive de quem paga as despesas do trabalho remoto."},
{"q":"A empresa pode me mandar voltar ao presencial se nada foi assinado?","a":"O art. 75-C, § 2º, permite ao empregador determinar o retorno, mas exige transição mínima de quinze dias e registro em aditivo. A falta do documento anterior não elimina essas condições para a volta."}
],
"official_sources":[
{"url":CLT+"#art75c","name":"CLT, art. 75-C, caput e §§ 1º e 2º","anchor_claim":"registro contratual do teletrabalho, acordo para ingresso no regime e retorno presencial determinado pelo empregador com transição"},
{"url":CLT+"#art75d","name":"CLT, art. 75-D","anchor_claim":"responsabilidade por equipamentos, infraestrutura e reembolso definida em contrato escrito"},
{"url":CLT+"#art75b","name":"CLT, art. 75-B","anchor_claim":"teletrabalho pode ser por jornada ou por produção, com efeitos distintos sobre o controle de horas"},
{"url":CLT+"#art62","name":"CLT, art. 62, III","anchor_claim":"exceção de duração do trabalho para teletrabalho por produção ou tarefa"},
{"url":TST_TELEWORK_WRITTEN,"name":"TST — teletrabalho sem aditivo e horas extras","anchor_claim":"caso concreto em que a falta de previsão escrita impediu o enquadramento excepcional de jornada pretendido pela empresa"}
],
"internal_link_topics":["desconto de despesas de home office","retorno forcado ao presencial","hora extra no teletrabalho"],
"lane":"comercial","word_count":0})

# 2
pages.append({
"intent_id":"trab-teletrabalho-retorno-presencial-sem-transicao",
"title":"Voltar ao presencial de um dia para o outro: pode?",
"meta_description":"A empresa mandou você deixar o home office e voltar ao escritório já? A CLT prevê prazo mínimo de transição para o retorno presencial. Entenda seus limites.",
"h1":"Retorno ao presencial sem aviso: o que a CLT garante",
"opening":"Depois de meses ou anos em casa, receber um comunicado dizendo para voltar ao escritório amanhã desorganiza a vida inteira: transporte, escola dos filhos, orçamento, rotina. A pergunta imediata é se a empresa pode mesmo determinar essa volta de um dia para o outro.\n\nA CLT autoriza o empregador a encerrar o regime de teletrabalho, inclusive quando ele está escrito no contrato, mas impõe transição e aditivo. Outras questões — local contratual, norma coletiva ou necessidade de adaptação — podem existir, porém não apagam nem substituem essa regra específica.",
"sections":[
{"heading":"A empresa pode encerrar o teletrabalho","text":"Sim. O art. 75-C, § 2º, permite a alteração do teletrabalho para o presencial por determinação do empregador. A norma não limita esse poder aos casos em que o regime remoto era apenas uma política informal; por isso, a presença do teletrabalho no contrato não cria, sozinha, um direito permanente de ficar remoto.\n\nA entrada no teletrabalho depende de mútuo acordo, conforme o § 1º. A saída tem regra diferente: pode ser determinada pela empresa, desde que sejam cumpridas as condições legais e eventuais cláusulas mais favoráveis aplicáveis ao caso."},
{"heading":"O prazo mínimo de transição de quinze dias","text":"A mesma norma exige que o retorno respeite prazo mínimo de transição de quinze dias, com o correspondente registro em aditivo contratual. Esse período serve para você reorganizar deslocamento, cuidados familiares e rotina antes de voltar à mesa do escritório.\n\nNa prática, um comunicado de \"volte amanhã\" não cumpre a lei: falta o intervalo mínimo e falta o aditivo que documenta a mudança. Imagine quem organizou a vida em torno do trabalho remoto — matrícula do filho em creche perto de casa, ausência de carro próprio — e recebe na sexta a ordem de comparecer na segunda: os quinze dias existem exatamente para absorver esse tipo de reorganização. Registrar por escrito a data do aviso e o dia exigido de retorno é o primeiro passo para demonstrar que o prazo foi desrespeitado."},
{"heading":"O que pode mudar a análise além dos quinze dias","text":"O retorno ao presencial não autoriza qualquer outra mudança. Se a ordem exige trabalhar em localidade diversa da prevista no contrato e implica mudança de domicílio, entram as regras de transferência do art. 469. Norma coletiva ou cláusula individual também pode prever aviso maior ou condição mais favorável.\n\nHá ainda a hipótese tratada no § 3º do art. 75-C: quando o próprio empregado escolheu trabalhar remotamente fora da localidade contratual, o empregador não responde pelas despesas do retorno, salvo ajuste diferente. Portanto, morar longe hoje não prova, por si só, que a ordem é ilegal; é preciso saber qual era a localidade contratada e quem decidiu a mudança."},
{"heading":"O que registrar antes de reagir","text":"Guarde o comunicado com a data do aviso e a data marcada para comparecimento, o contrato, o aditivo, a norma coletiva e os documentos sobre a localidade de trabalho. Se houver condição de saúde, deficiência ou outra necessidade de adaptação, registre-a separadamente com os documentos pertinentes.\n\nUma orientação jurídica individual pode distinguir o simples descumprimento do prazo de quinze dias de uma transferência, violação de norma coletiva ou situação discriminatória. Essa distinção importa antes de recusar a ordem, porque uma recusa sem base pode gerar consequência disciplinar."}
],
"faq":[
{"q":"Quinze dias é sempre suficiente de aviso?","a":"É o piso do art. 75-C, § 2º. Norma coletiva ou contrato pode prever prazo maior, e questões separadas como transferência de localidade ou adaptação razoável exigem análise própria."},
{"q":"Posso negociar o retorno ao invés de simplesmente aceitar?","a":"Sim. A empresa pode determinar o retorno, mas nada impede propor um modelo híbrido ou uma data que concilie sua rotina. Registrar a negociação por escrito preserva seus argumentos caso o impasse evolua."},
{"q":"E se eu me recusar a voltar ao presencial?","a":"A recusa pura e simples pode ser tratada como descumprimento de ordem quando o retorno observa a lei. Antes de recusar, verifique prazo, aditivo, localidade contratual, norma coletiva e eventual necessidade de adaptação."}
],
"official_sources":[
{"url":CLT+"#art75c","name":"CLT, art. 75-C (Decreto-Lei 5.452/1943)","anchor_claim":"retorno ao presencial por determinação do empregador com prazo mínimo de transição de quinze dias e aditivo"},
{"url":CLT+"#art469","name":"CLT, art. 469","anchor_claim":"limites para transferência que implique mudança de domicílio para localidade diversa da contratada"}
],
"internal_link_topics":["teletrabalho sem aditivo escrito","rescisao indireta por fim do home office","mudanca de dias no trabalho hibrido"],
"lane":"comercial","word_count":0})

# 3
pages.append({
"intent_id":"trab-teletrabalho-desconto-custos-salario",
"title":"Custos do home office descontados do salário: limites",
"meta_description":"A empresa lançou internet ou energia do trabalho remoto no contracheque? Entenda as regras dos arts. 462 e 75-D da CLT antes de avaliar o desconto.",
"h1":"A empresa pode descontar despesas do home office?",
"opening":"Trabalhar de casa pode aumentar o gasto com internet, energia e telefonia. Uma coisa é definir previamente quem suportará cada despesa; outra é lançar um abatimento no contracheque depois que o salário já foi ajustado. A diferença importa porque a CLT protege a remuneração contra descontos e exige tratamento escrito para equipamentos, infraestrutura e reembolso no teletrabalho.\n\nNão existe uma resposta automática para todo custo doméstico. É preciso ler a cláusula aplicável, identificar o que foi fornecido ou reembolsado e separar uma despesa atribuída ao empregado de um desconto salarial efetivamente praticado.",
"sections":[
{"heading":"Quais descontos o art. 462 admite","text":"O caput do art. 462 da CLT veda descontos salariais, salvo quando resultarem de adiantamentos, de dispositivos de lei ou de contrato coletivo. O § 1º trata de situação diferente: dano causado pelo empregado, cujo desconto pode ocorrer se essa possibilidade tiver sido acordada ou se houver dolo.\n\nUma conta comum de internet ou energia não vira dano apenas porque surgiu durante o trabalho remoto. Para avaliar um lançamento no contracheque, confira a rubrica, a origem do valor e a base invocada pela empresa. Uma autorização genérica não deve ser lida como permissão ilimitada para reduzir salário."},
{"heading":"O que o art. 75-D exige sobre despesas","text":"O art. 75-D determina que contrato escrito trate da responsabilidade pela aquisição, manutenção ou fornecimento de equipamentos e infraestrutura, além do reembolso de despesas arcadas pelo empregado. A regra manda distribuir responsabilidades com clareza, mas não diz que toda despesa doméstica será paga pela empresa.\n\nTambém não transforma uma cláusula de custeio em autorização automática para desconto em folha. É preciso separar a obrigação de pagar diretamente uma conta, o fornecimento de um equipamento, o reembolso de gasto comprovado e o abatimento de salário. Cada operação tem fundamento e prova próprios."},
{"heading":"Equipamentos e reembolsos não são salário","text":"O parágrafo único do art. 75-D afirma que as utilidades mencionadas no caput não integram a remuneração. Assim, equipamento fornecido, infraestrutura custeada ou reembolso relacionado ao teletrabalho não se torna salário apenas por beneficiar o empregado durante a execução do serviço.\n\nEssa regra evita confundir o que viabiliza o trabalho com pagamento pelo trabalho. Ela, porém, não resolve sozinha se determinado valor foi corretamente calculado nem autoriza compensá-lo unilateralmente com outras parcelas salariais."},
{"heading":"Como conferir um lançamento no contracheque","text":"Reúna contracheques, contrato, aditivo de teletrabalho, política de despesas, comprovantes e a comunicação que criou o lançamento. Peça por escrito a memória de cálculo e o fundamento do desconto. Compare o documento com o que efetivamente ocorreu: quem contratou o serviço, quem recebeu o equipamento e se houve reembolso anterior.\n\nObserve também se o valor foi abatido do salário, compensado com reembolso, cobrado fora da folha ou apenas informado no demonstrativo. Rubricas parecidas podem representar operações juridicamente diferentes, e a sequência dos pagamentos ajuda a evitar contagem em duplicidade.\n\nSe a resposta não explicar a rubrica ou se o desconto não corresponder ao que foi pactuado, uma análise jurídica individual pode avaliar restituição e outros efeitos. A conclusão deve partir dos documentos e da forma real de custeio, sem presumir que todo gasto doméstico pertence à empresa ou que toda cláusula permite desconto salarial."}
],
"faq":[
{"q":"A empresa é obrigada a pagar minha internet no home office?","a":"A CLT manda definir por escrito a responsabilidade por infraestrutura e reembolso, mas não atribui automaticamente toda conta doméstica à empresa. Contrato, política aplicável e uso profissional precisam ser verificados."},
{"q":"Posso pedir de volta valores já descontados?","a":"Pode haver restituição quando o abatimento não se enquadra nas hipóteses do art. 462. Antes de concluir, é necessário identificar a rubrica, o fundamento apresentado e os documentos de cada período."},
{"q":"Uma cláusula de despesas autoriza desconto no salário?","a":"Não automaticamente. A cláusula pode distribuir custos do teletrabalho, mas o desconto em folha ainda precisa respeitar o art. 462 e corresponder exatamente à obrigação pactuada e comprovada."}
],
"official_sources":[
{"url":CLT+"#art462","name":"CLT, art. 462, caput e § 1º","anchor_claim":"limites para descontos salariais e hipótese específica de dano causado pelo empregado"},
{"url":CLT+"#art75d","name":"CLT, art. 75-D e parágrafo único","anchor_claim":"responsabilidade escrita por equipamentos, infraestrutura e reembolso, sem integração das utilidades à remuneração"}
],
"internal_link_topics":["teletrabalho sem aditivo escrito","equipamentos e ergonomia no home office","natureza indenizatoria do reembolso"],
"lane":"comercial","word_count":0})

# 4
pages.append({
"intent_id":"trab-teletrabalho-sobreaviso-disponibilidade-app",
"title":"Ficar disponível no WhatsApp fora do horário é pago?",
"meta_description":"Seu chefe cobra resposta no aplicativo a qualquer hora? Veja quando a disponibilidade permanente vira sobreaviso e gera pagamento, segundo a Súmula 428 do TST.",
"h1":"Cobrança por app fora do expediente gera direito a receber?",
"opening":"O celular apita à noite, no fim de semana ou na folga: uma mensagem do chefe, um chamado no grupo, um cliente que pede resposta imediata. Nem todo contato digital fora do horário produz o mesmo efeito jurídico, especialmente no teletrabalho.\n\nA Súmula 428 do TST distingue o simples uso de aparelho do regime de plantão. Desde 2022, o art. 75-B, § 5º, da CLT acrescenta regra específica para o trabalho remoto sobre uso de tecnologias fora da jornada. As duas referências precisam ser lidas juntas, com eventual acordo individual ou coletivo, antes de classificar espera, acionamento e trabalho efetivo.",
"sections":[
{"heading":"O aparelho, sozinho, não configura sobreaviso","text":"O item I da Súmula 428 afirma que instrumentos telemáticos ou informatizados fornecidos pela empresa, por si sós, não caracterizam sobreaviso. Aplicativo instalado, notebook corporativo ou possibilidade genérica de contato não bastam. O art. 6º da CLT reconhece meios digitais de comando e controle, mas essa equiparação também não converte automaticamente qualquer conexão em tempo remunerado.\n\nPara quem está em teletrabalho, o art. 75-B, § 5º, é ainda mais específico: o tempo de uso de equipamentos, infraestrutura, softwares, ferramentas digitais ou aplicações de internet fora da jornada normal não constitui tempo à disposição, prontidão ou sobreaviso, salvo previsão em acordo individual, acordo coletivo ou convenção coletiva."},
{"heading":"Plantão da Súmula 428 e a regra especial do teletrabalho","text":"O item II da Súmula 428 considera em sobreaviso o empregado que, a distância e submetido a controle por meios digitais, permanece em regime de plantão ou equivalente aguardando chamado durante o descanso. Não é necessário permanecer em casa; importam escala, prontidão exigida e controle patronal.\n\nNo teletrabalho, porém, esse critério precisa ser confrontado com o § 5º do art. 75-B e com os instrumentos aplicáveis. Por isso, não é seguro prometer sobreaviso apenas porque havia prazo curto para responder. Escala formal, acordo individual ou coletivo, consequências pelo não atendimento e liberdade real durante o descanso compõem a análise."},
{"heading":"Quanto vale o período reconhecido como sobreaviso","text":"Quando o sobreaviso é juridicamente reconhecido, a Súmula 428 usa por analogia o art. 244, § 2º, da CLT, que calcula as horas à razão de um terço do salário normal. A fração remunera a espera em plantão, não uma jornada contínua de trabalho efetivo.\n\nQuando há acionamento e execução de tarefa, o período efetivamente trabalhado precisa ser apurado separadamente. A existência de hora extra dependerá do total da jornada e das regras aplicáveis; nem toda interação de poucos segundos produz, isoladamente, uma hora inteira a pagar. Espera e execução não devem ser contadas duas vezes."},
{"heading":"Como documentar a disponibilidade exigida","text":"Salve escalas de plantão, mensagens que exigem resposta imediata, registros de acionamento e políticas internas sobre prontidão fora do expediente. O contexto é decisivo: horário, prazo de resposta, frequência, consequência pelo silêncio e liberdade real para usar o descanso. Compare dias úteis, fins de semana e semanas diferentes.\n\nOrganize também evidências do trabalho efetivamente realizado após cada chamado. Uma análise individual pode então separar contato esporádico, plantão em sobreaviso e tempo de execução, sem presumir que portar o aparelho basta ou que toda mensagem noturna tem o mesmo efeito jurídico."}
],
"faq":[
{"q":"Responder uma mensagem à noite já gera hora extra?","a":"O tempo efetivamente trabalhado deve ser apurado, mas a existência e a quantidade de hora extra dependem da jornada total e das regras do caso. Uma mensagem isolada também não configura, sozinha, sobreaviso."},
{"q":"Preciso ficar em casa para haver sobreaviso?","a":"A Súmula 428 não exige permanência em casa, mas exige plantão ou equivalente sob controle digital. No teletrabalho, também é necessário considerar o art. 75-B, § 5º, e eventual acordo individual ou coletivo."},
{"q":"O sobreaviso é pago pela hora inteira?","a":"Quando reconhecido, é calculado à razão de um terço do salário normal por hora, segundo a aplicação analógica do art. 244, § 2º. Trabalho efetivo após acionamento é apurado separadamente."}
],
"official_sources":[
{"url":SUM428,"name":"TST, Súmula 428 (sobreaviso)","anchor_claim":"uso de instrumentos telemáticos por si só não gera sobreaviso, que se configura no regime de plantão aguardando chamado"},
{"url":CLT+"#art75b","name":"CLT, art. 75-B, § 5º","anchor_claim":"uso de tecnologias fora da jornada no teletrabalho não constitui tempo à disposição, prontidão ou sobreaviso, salvo acordo individual ou coletivo"},
{"url":CLT+"#art244","name":"CLT, art. 244, § 2º","anchor_claim":"horas de sobreaviso contadas à razão de um terço do salário normal"},
{"url":CLT+"#art6","name":"CLT, art. 6º","anchor_claim":"meios telemáticos de comando e controle equiparados aos meios pessoais de subordinação"}
],
"internal_link_topics":["hora extra no teletrabalho por jornada","direito a desconexao","assedio moral em grupos de mensagem"],
"lane":"comercial","word_count":0})

# 5
pages.append({
"intent_id":"trab-teletrabalho-producao-negativa-hora-extra",
"title":"Teletrabalho por produção não tem hora extra? Depende",
"meta_description":"A empresa diz que teletrabalho por produção não gera hora extra, mas você cumpre horário e metas? Entenda a diferença entre produção e jornada na CLT.",
"h1":"Home office por produção sem hora extra: quando é indevido",
"opening":"A frase \"teletrabalho não tem hora extra\" omite a distinção criada pela CLT. A exclusão das regras de duração alcança empregados em teletrabalho que prestam serviços por produção ou tarefa; o trabalho remoto organizado por jornada segue outra disciplina.\n\nO nome colocado no contrato é relevante, mas não encerra a análise. A forma de medir a obrigação, a autonomia temporal, os registros existentes e a rotina praticada precisam ser lidos em conjunto. Reuniões, metas e sistemas podem revelar coordenação ou controle, mas nenhum sinal isolado resolve automaticamente o enquadramento.",
"sections":[
{"heading":"Qual modalidade fica fora das regras de duração","text":"O art. 62, III, da CLT alcança empregados em teletrabalho que prestam serviço por produção ou tarefa. O art. 75-B, § 3º, repete que, nessa modalidade, não se aplica o capítulo da duração do trabalho. O texto legal descreve a forma de organizar a prestação; não exige, como definição universal, que o salário seja calculado por peça entregue.\n\nJá o teletrabalho organizado por jornada não recebe essa exclusão apenas por ocorrer fora da empresa. Para saber qual hipótese existe, é preciso identificar se a obrigação central é entregar produção ou tarefa com autonomia temporal, ou cumprir períodos de trabalho sujeitos a acompanhamento."},
{"heading":"Como os fatos ajudam a distinguir as modalidades","text":"Horário fixo, obrigação de permanecer conectado, registros de entrada e saída e cobranças vinculadas a períodos determinados podem apontar organização por jornada. O art. 6º confirma que meios telemáticos de comando, controle e supervisão se equiparam aos meios pessoais.\n\nReuniões e metas, porém, também podem existir em trabalhos por produção ou tarefa. O ponto não é contar sinais mecanicamente, e sim entender se eles apenas coordenam entregas ou se delimitam e fiscalizam o tempo de trabalho. Contrato, sistemas, mensagens e depoimentos devem formar uma narrativa coerente."},
{"heading":"Que documentos preservam a discussão","text":"Guarde contrato e aditivos, regras de produção, registros de acesso, convites de reuniões, escalas, mensagens sobre disponibilidade e relatórios que indiquem início e fim. Preserve também documentos que mostrem como a entrega era medida e se havia liberdade real para distribuir o tempo. Compare dias comuns, períodos de pico e eventuais pausas, porque uma amostra excepcional não representa necessariamente toda a relação.\n\nA distribuição do ônus da prova e o valor de cada registro dependem das alegações, dos documentos que a empresa deve manter e das circunstâncias processuais. Por isso, a ausência de um print específico não significa vitória automática de uma versão, assim como um login isolado não prova toda a jornada alegada."},
{"heading":"Como formular a pergunta correta","text":"Em vez de perguntar apenas se o contrato usa a palavra \"produção\", descreva uma semana típica: qual era a tarefa, quando você precisava estar disponível, como o desempenho era medido e quem conhecia seus horários. Calcule separadamente o tempo normal, eventuais excedentes e intervalos, indicando também variações entre dias, períodos e semanas de trabalho.\n\nUma orientação jurídica individual pode confrontar essa rotina com os arts. 62, III, 75-B e 6º da CLT. A análise deve evitar dois atalhos: negar horas extras a todo trabalhador remoto ou presumir que qualquer coordenação digital converte produção em jornada."}
],
"faq":[
{"q":"O contrato diz teletrabalho por produção. Isso encerra a discussão?","a":"Não necessariamente. O documento é uma prova, mas deve corresponder à forma real de organizar o serviço. Controle de períodos de trabalho e autonomia para distribuir o tempo precisam ser examinados."},
{"q":"Reunião diária marcada prova controle de jornada?","a":"É um elemento de contexto, não uma conclusão automática. Importam também duração, horários exigidos, registros, disponibilidade e se a reunião apenas coordenava uma entrega por produção ou tarefa."},
{"q":"Teletrabalho por produção gera hora extra?","a":"Os arts. 62, III, e 75-B, § 3º, afastam as regras de duração para a prestação por produção ou tarefa. A controvérsia costuma estar em saber se a rotina concreta pertence realmente a essa modalidade."}
],
"official_sources":[
{"url":CLT+"#art62","name":"CLT, art. 62, III (Decreto-Lei 5.452/1943)","anchor_claim":"exclusão do controle de jornada apenas para o teletrabalho por produção ou tarefa"},
{"url":CLT+"#art75b","name":"CLT, art. 75-B","anchor_claim":"teletrabalho por jornada ou por produção, com afastamento das regras de duração só na produção"},
{"url":CLT+"#art6","name":"CLT, art. 6º","anchor_claim":"meios telemáticos de controle equiparados à supervisão pessoal do trabalho"}
],
"internal_link_topics":["disponibilidade por aplicativo e sobreaviso","teletrabalho sem aditivo escrito","direito a desconexao"],
"lane":"comercial","word_count":0})

# 6
pages.append({
"intent_id":"trab-teletrabalho-prioridade-filho-pequeno",
"title":"Prioridade no home office para pai de filho pequeno",
"meta_description":"Tem filho de até quatro anos e a empresa negou seu teletrabalho prioritário? Veja como o art. 75-F prioriza responsáveis por crianças pequenas em vagas remotas.",
"h1":"Empresa negou home office com filho de até 4 anos",
"opening":"Conciliar a rotina de uma criança pequena com um trabalho presencial rígido é uma equação que muitas famílias não conseguem fechar. Por isso a Lei 14.442/2022 trouxe uma regra pouco conhecida: dentro do teletrabalho, certos empregados têm preferência. Quem tem filho de até quatro anos está nesse grupo.\n\nEssa prioridade não é um direito absoluto de trabalhar de casa em qualquer situação, e é importante ler o texto com precisão para não confundir preferência com garantia incondicional. Ainda assim, é uma ferramenta concreta que muita gente desconhece e deixa de usar quando o pedido é negado.",
"sections":[
{"heading":"O que o art. 75-F assegura a quem tem criança pequena","text":"O art. 75-F da CLT manda priorizar empregados com filhos ou criança sob guarda judicial de até quatro anos quando são preenchidas vagas cujas funções admitem trabalho remoto. A regra não distingue pai e mãe e também alcança quem detém a guarda judicial.\n\nPrioridade não significa criação obrigatória de função remota nem concessão automática do regime. Significa que o critério legal deve ser considerado quando há atividade compatível e vaga a ser preenchida. A lei não acrescenta a expressão \"em igualdade de condições\" nem define, sozinha, todo o procedimento interno de escolha."},
{"heading":"O limite da regra: preferência não é garantia absoluta","text":"Ser honesto sobre o alcance da norma evita frustração. Se a função é incompatível com o trabalho remoto por sua própria natureza, a prioridade não transforma o presencial em remoto. E se não há vaga de teletrabalho disponível, não há posto sobre o qual exercer a preferência.\n\nA prioridade morde de verdade em dois momentos: quando a empresa abre ou redistribui posições passíveis de teletrabalho e quando trata de forma desigual empregados na mesma situação. Negar a preferência a quem tem filho pequeno para conceder o mesmo posto a colega sem esse critério, sem justificativa técnica, é onde a regra ganha força. O histórico de vagas e os critérios divulgados ajudam a verificar se houve alocação real, e não apenas pedido abstrato de criação de regime."},
{"heading":"Como pedir e o que registrar quando há negativa","text":"Formalize o pedido por escrito, indicando a idade do filho ou a guarda judicial, a função exercida e por que a atividade pode ser realizada remotamente. Certidão de nascimento ou termo de guarda permite verificar a faixa etária. Peça que a empresa responda pelo mesmo canal e informe se havia vagas compatíveis.\n\nO art. 75-F não prescreve um rito completo nem uma obrigação geral de motivação formal. Ainda assim, pedido e resposta escritos ajudam a reconstruir quais vagas existiam, quais critérios foram usados e se a prioridade foi efetivamente considerada."},
{"heading":"Como avaliar uma recusa","text":"Compare a atividade exercida com vagas remotas existentes, normas coletivas, políticas internas e critérios aplicados a outros empregados. Uma função que exige presença física pode afastar a alocação remota; uma recusa sem relação com as tarefas, diante de vaga compatível, exige explicação mais cuidadosa.\n\nUma análise jurídica individual pode verificar se houve simples inexistência de vaga ou desrespeito à prioridade legal. O resultado depende dos fatos documentados, e não de uma promessa de home office automático baseada apenas na idade da criança."}
],
"faq":[
{"q":"A prioridade obriga a empresa a me colocar em home office?","a":"Não automaticamente. Ela orienta a alocação em vagas cujas atividades possam ser remotas; não cria uma função incompatível nem dispensa a verificação de vagas e critérios concretos."},
{"q":"Vale para pai, ou só para a mãe?","a":"Vale para ambos. O art. 75-F fala em empregados com filhos ou criança sob guarda judicial até quatro anos, sem distinção de gênero, alcançando pai, mãe e quem detém a guarda judicial."},
{"q":"Meu filho fez cinco anos. A prioridade continua?","a":"A regra específica alcança filho ou criança sob guarda judicial até quatro anos de idade. Depois dessa faixa, o art. 75-F não sustenta essa prioridade, embora outro fundamento possa existir no caso concreto."}
],
"official_sources":[
{"url":CLT+"#art75f","name":"CLT, art. 75-F (Decreto-Lei 5.452/1943)","anchor_claim":"prioridade no teletrabalho para empregados com filhos ou criança sob guarda judicial até quatro anos"},
{"url":L14442,"name":"Lei 14.442/2022","anchor_claim":"criação da regra de prioridade no teletrabalho para responsáveis por criança pequena"}
],
"internal_link_topics":["prioridade de teletrabalho por deficiencia","teletrabalho sem aditivo escrito","mudanca de dias no trabalho hibrido"],
"lane":"comercial","word_count":0})

# 7
pages.append({
"intent_id":"trab-teletrabalho-prioridade-deficiencia",
"title":"Home office prioritário para pessoa com deficiência",
"meta_description":"É pessoa com deficiência e a empresa recusa seu teletrabalho prioritário? Entenda a prioridade legal da pessoa com deficiência em vagas remotas compatíveis.",
"h1":"Sou PcD e a empresa nega meu teletrabalho prioritário",
"opening":"Para muitas pessoas com deficiência, o trabalho remoto não é conforto: é a diferença entre um emprego viável e uma barreira diária de acessibilidade, transporte e cansaço. Reconhecendo isso, a legislação colocou o empregado com deficiência entre os que têm preferência no teletrabalho. Quando a empresa ignora essa prioridade, vale saber exatamente em que ela se apoia.\n\nO ponto de partida é o art. 75-F da CLT, mas ele conversa com todo um sistema de proteção à inclusão. Ler a preferência dentro desse contexto ajuda a entender por que a recusa desmotivada é mais frágil do que costuma parecer.",
"sections":[
{"heading":"A prioridade específica do art. 75-F","text":"O art. 75-F da CLT inclui empregados com deficiência entre aqueles a quem o empregador deve dar prioridade na alocação em vagas para atividades que possam ser realizadas por teletrabalho ou trabalho remoto. A regra incide sobre a alocação em atividade compatível; não cria automaticamente um posto remoto nem elimina requisitos técnicos da função.\n\nQuando existem vagas remotas compatíveis, a deficiência não pode ser ignorada como critério legal de prioridade. Para verificar se a regra foi aplicada, é útil identificar a vaga, suas tarefas, o processo de escolha e as adaptações consideradas."},
{"heading":"Como a Lei Brasileira de Inclusão se relaciona com o pedido","text":"A Lei Brasileira de Inclusão assegura ambiente de trabalho acessível e inclusivo e prevê acessibilidade, fornecimento de recursos de tecnologia assistiva e adaptação razoável. O trabalho remoto pode ser uma das medidas capazes de remover barreiras, mas não é a única nem é automaticamente a adaptação adequada em todo caso.\n\nUma pessoa pode precisar de home office por barreira de transporte; outra pode necessitar de equipamento acessível na sede, horário ajustado ou solução híbrida. A escolha deve considerar a barreira concreta, as funções essenciais e a efetividade das alternativas, sem tratar deficiência como sinônimo obrigatório de trabalho em casa."},
{"heading":"O que documentar quando o teletrabalho é negado","text":"Formalize o pedido, com comprovação pertinente da deficiência e descrição objetiva da barreira enfrentada. Relacione as tarefas que podem ser realizadas remotamente e, quando possível, proponha adaptações. Evite expor dados de saúde além do necessário para avaliar a medida.\n\nSe houver negativa, peça uma resposta escrita e preserve informação sobre vagas remotas ou soluções adotadas em funções semelhantes. O art. 75-F não cria uma obrigação universal de a empresa justificar formalmente toda recusa; o registro, porém, permite examinar se a prioridade e a adaptação razoável foram de fato consideradas."},
{"heading":"Como avaliar prioridade e adaptação","text":"Reúna descrição da função, política de teletrabalho, vagas disponíveis, pedido, resposta e documentos sobre a barreira. A análise precisa distinguir três perguntas: a atividade admite trabalho remoto, havia vaga para alocação e o caso também exige adaptação razoável nos termos da LBI. Registre quais alternativas foram oferecidas e se elas realmente removem a barreira descrita.\n\nUma orientação jurídica individual pode comparar as alternativas e identificar eventual tratamento discriminatório ou descumprimento da prioridade. O resultado deve ser construído a partir dessas evidências, sem prometer home office automático nem desconsiderar uma solução presencial efetivamente acessível."}
],
"faq":[
{"q":"A empresa é obrigada a me dar home office por eu ser PcD?","a":"O art. 75-F garante prioridade na alocação em vagas de teletrabalho, não a criação de um posto onde a função não comporta. A força do pedido cresce quando há vaga apta e o regime remoto elimina barreiras de acessibilidade."},
{"q":"Preciso apresentar laudo médico?","a":"A comprovação da deficiência ampara o pedido e ajuda a demonstrar o enquadramento na preferência legal e a necessidade de adaptação. Documentar a barreira concreta enfrentada no presencial reforça o requerimento."},
{"q":"A recusa precisa ser justificada por escrito?","a":"O art. 75-F não estabelece essa formalidade para toda recusa. Pedir resposta escrita é útil para verificar vagas, compatibilidade da atividade, prioridade e eventual adaptação razoável à luz da LBI."}
],
"official_sources":[
{"url":CLT+"#art75f","name":"CLT, art. 75-F (Decreto-Lei 5.452/1943)","anchor_claim":"prioridade no teletrabalho para empregados com deficiência"},
{"url":LBI+"#art34","name":"Lei 13.146/2015, arts. 34 e 37","anchor_claim":"ambiente de trabalho acessível e inclusivo, acessibilidade, tecnologia assistiva e adaptação razoável"},
{"url":L14442,"name":"Lei 14.442/2022","anchor_claim":"disciplina do teletrabalho que fixou a preferência para pessoa com deficiência"}
],
"internal_link_topics":["prioridade de teletrabalho por filho pequeno","teletrabalho sem aditivo escrito","retorno forcado ao presencial"],
"lane":"comercial","word_count":0})

# 8
pages.append({
"intent_id":"trab-teletrabalho-punicao-monitoramento-tela",
"title":"Punido por software que vigia a tela no home office",
"meta_description":"Foi advertido ou demitido com base em programa que monitora sua tela em casa? Veja os limites da prova por vigilância e o que a LGPD exige do monitoramento.",
"h1":"Advertência baseada em monitoramento de tela: vale?",
"opening":"Programas que tiram prints da tela em intervalos, registram cada tecla, medem tempo de \"ociosidade\" e cronometram pausas se tornaram comuns no trabalho remoto. Quando essa vigilância vira base para uma advertência, uma justa causa ou uma demissão, surge uma dúvida legítima: até onde a empresa pode ir e o que esse tipo de prova realmente vale.\n\nMonitorar o trabalho não é, em si, proibido — o empregador tem poder de fiscalização. Mas esse poder encontra limites na proteção de dados e na dignidade do trabalhador. É nesse limite que se decide se a punição se sustenta ou se resvala em abuso.",
"sections":[
{"heading":"Fiscalização digital não é autorização ilimitada","text":"O art. 6º da CLT equipara meios telemáticos e informatizados de comando, controle e supervisão aos meios pessoais e diretos. Isso permite acompanhar a prestação remota, mas não decide qual tecnologia, frequência ou dado é necessário em cada atividade.\n\nCaptura contínua de tela pode alcançar conversas particulares, credenciais e outros conteúdos estranhos ao serviço. A legalidade e o valor probatório dependem do desenho concreto: equipamento usado, informação coletada, finalidade, alcance, segurança e alternativas menos invasivas. O relatório não é automaticamente válido nem inválido apenas porque foi produzido por software."},
{"heading":"Base legal e princípios da LGPD","text":"Imagens de tela, registros de atividade e identificadores associados ao empregado são dados pessoais. O tratamento precisa se apoiar em uma hipótese legal aplicável do art. 7º da LGPD e respeitar os princípios do art. 6º, como finalidade, adequação, necessidade, transparência, segurança e não discriminação. Consentimento não deve ser presumido como solução universal para relações de trabalho.\n\nA empresa precisa definir por que coleta, quais dados são indispensáveis, por quanto tempo os conserva e quem terá acesso. Informação transparente integra essa análise, mas aviso prévio, sozinho, não torna proporcional uma vigilância excessiva nem substitui a base legal."},
{"heading":"O que o relatório precisa demonstrar para sustentar punição","text":"Indicadores de inatividade podem confundir leitura, reunião, ligação ou tarefa offline com abandono. Antes de associar a métrica a uma falta, é necessário verificar integridade, contexto, período e a conduta efetivamente atribuída. Para justa causa, a empresa ainda precisa relacionar os fatos a uma hipótese do art. 482 da CLT e demonstrar gravidade suficiente.\n\nNão há uma regra geral na CLT que exija contraditório formal antes de toda penalidade aplicada pelo empregador. A ausência desse rito não derruba automaticamente a medida; inconsistência do dado, invasão desnecessária, falta de transparência, desproporção e fragilidade na individualização podem ser questionadas com fundamentos próprios."},
{"heading":"Como reconstruir o contexto da punição","text":"Preserve a advertência ou comunicação de dispensa, relatório usado, política de monitoramento, aviso de privacidade e informação técnica disponível sobre o programa. Registre tarefas offline, reuniões, falhas do sistema e quem podia acessar o dado. Peça esclarecimento sobre o evento, o período e a regra supostamente descumprida. Se houver contestação de integridade, versões, logs e critérios de geração do relatório podem ser mais úteis do que uma captura isolada.\n\nUma análise individual pode examinar, separadamente, tratamento de dados, qualidade da prova e proporcionalidade disciplinar. Essa separação evita concluir que qualquer problema de LGPD anula a punição ou que uma métrica automatizada comprova sozinha uma falta grave."}
],
"faq":[
{"q":"A empresa pode monitorar minha tela em casa?","a":"Pode fiscalizar o trabalho, mas o tratamento deve ter base legal e respeitar finalidade, necessidade, transparência, segurança e os demais princípios da LGPD. A extensão concreta precisa ser proporcional."},
{"q":"Posso sofrer justa causa com base nesses relatórios?","a":"Um relatório pode integrar a prova, mas deve ser íntegro e contextualizado. A justa causa ainda exige conduta individualizada, enquadramento no art. 482 e gravidade compatível; a métrica automática não resolve isso sozinha."},
{"q":"Preciso ser informado do monitoramento?","a":"Transparência é princípio da LGPD, mas a análise não termina no aviso. Também são necessários hipótese legal aplicável, finalidade definida, coleta necessária, segurança e uso compatível com o que foi informado."}
],
"official_sources":[
{"url":LGPD+"#art6","name":"LGPD, art. 6º","anchor_claim":"princípios aplicáveis ao tratamento, incluindo finalidade, adequação, necessidade, transparência e segurança"},
{"url":LGPD+"#art7","name":"LGPD, art. 7º","anchor_claim":"hipóteses legais para tratamento de dados pessoais"},
{"url":CLT+"#art6","name":"CLT, art. 6º","anchor_claim":"equiparação dos meios telemáticos e informatizados de comando, controle e supervisão"},
{"url":CLT+"#art482","name":"CLT, art. 482","anchor_claim":"hipóteses legais de justa causa que exigem correspondência com a conduta comprovada"}
],
"internal_link_topics":["assedio moral em grupos de mensagem","disponibilidade por aplicativo e sobreaviso","rescisao indireta no teletrabalho"],
"lane":"comercial","word_count":0})

# 9
pages.append({
"intent_id":"trab-teletrabalho-lerdort-ergonomia",
"title":"Tendinite no home office: a empresa responde?",
"meta_description":"Desenvolveu LER ou DORT trabalhando em casa sem cadeira e mesa adequadas? Veja o dever de instrução ergonômica do art. 75-E da CLT e a doença ocupacional.",
"h1":"Adoeci por ergonomia ruim no home office: e agora?",
"opening":"A mesa da cozinha, a cadeira da sala e o notebook no colo podem anteceder dor no punho, ombro ou pescoço e diagnósticos como tendinite, LER ou DORT. O fato de os sintomas surgirem durante o trabalho em casa não prova, sozinho, a origem ocupacional; também não exclui a responsabilidade apenas porque o posto estava na residência.\n\nA análise combina os deveres específicos do teletrabalho com a investigação médica das causas e concausas. É essa ligação entre condições do serviço e adoecimento — e não o endereço — que orienta o enquadramento jurídico.",
"sections":[
{"heading":"Instruções e termo de responsabilidade no teletrabalho","text":"O art. 75-E da CLT determina que o empregador instrua o empregado, de maneira expressa e ostensiva, sobre precauções para evitar doenças e acidentes. O empregado deve assinar termo comprometendo-se a seguir as orientações fornecidas. O documento registra a instrução, mas não substitui a verificação de seu conteúdo e da realidade do trabalho.\n\nO art. 75-D trata, em contrato escrito, da responsabilidade por equipamentos e infraestrutura. Ele não afirma que toda empresa deve fornecer mesa e cadeira em qualquer arranjo, nem elimina os demais deveres de saúde e segurança. Orientação, condições reais, custeio pactuado e conduta de ambas as partes precisam ser analisados em conjunto."},
{"heading":"Quando a doença pode ser considerada ocupacional","text":"O art. 20 da Lei 8.213/1991 inclui a doença do trabalho adquirida ou desencadeada por condições especiais em que o serviço é realizado e diretamente relacionada a ele. Também há exclusões e necessidade de avaliação individual. LER e DORT podem se enquadrar quando as condições de trabalho atuam como causa ou concausa comprovada.\n\nO diagnóstico, por si só, não identifica a origem. Histórico clínico, atividades executadas, repetitividade, pausas, jornada, fatores pessoais e condições ergonômicas compõem a investigação. A perícia pode ser decisiva quando existe controvérsia."},
{"heading":"Como preservar fatos relevantes para o nexo","text":"Guarde laudos, exames, atestados e histórico de tratamento, além de documentos que descrevam tarefas e evolução dos sintomas. Fotos do posto, mensagens sobre dor, ritmo de trabalho, pausas, orientações recebidas e pedidos de adaptação ajudam a reconstruir as condições do período.\n\nA comunicação de acidente de trabalho pode ser pertinente, mas sua emissão ou ausência não encerra, sozinha, a discussão. Registre datas e evite afirmar nexo médico sem avaliação profissional. O conjunto deve permitir distinguir coincidência temporal de relação causal ou concausal."},
{"heading":"Estabilidade e responsabilidade não são automáticas","text":"O art. 118 da Lei 8.213/1991 prevê manutenção do contrato por doze meses após a cessação do auxílio-doença acidentário. Há, porém, uma exceção jurisprudencial atual importante: no Tema 125, o TST fixou tese vinculante de que afastamento superior a quinze dias e percepção do benefício acidentário não são necessários quando, depois do fim do contrato, se reconhece nexo causal ou concausal entre doença ocupacional e atividades exercidas.\n\nIsso não dispensa a prova do nexo nem garante estabilidade a todo diagnóstico surgido no home office. Uma análise individual deve separar enquadramento previdenciário, garantia provisória de emprego e eventual reparação civil, porque cada consequência tem requisitos próprios."}
],
"faq":[
{"q":"Doença que surgiu em casa pode ser considerada do trabalho?","a":"Pode, se houver relação causal ou concausal entre a doença e as condições do serviço. O local doméstico não impede o enquadramento, mas coincidência de datas e diagnóstico isolado não bastam."},
{"q":"A empresa tinha que fornecer cadeira e mesa?","a":"O art. 75-D manda definir por escrito a responsabilidade por equipamentos e infraestrutura; não impõe uma solução única para todo contrato. O art. 75-E exige instruções expressas e ostensivas de prevenção."},
{"q":"Sem afastamento maior que quinze dias, perco a estabilidade?","a":"Não necessariamente. O Tema 125 do TST admite a garantia quando o nexo causal ou concausal é reconhecido após o fim do contrato, mesmo sem esse afastamento ou benefício acidentário. O nexo continua precisando ser provado."}
],
"official_sources":[
{"url":CLT+"#art75e","name":"CLT, art. 75-E","anchor_claim":"instrução expressa e ostensiva sobre prevenção e termo de responsabilidade do empregado"},
{"url":CLT+"#art75d","name":"CLT, art. 75-D","anchor_claim":"responsabilidade por equipamentos, infraestrutura e reembolso definida em contrato escrito"},
{"url":L8213+"#art20","name":"Lei 8.213/1991, art. 20","anchor_claim":"conceito de doença profissional e doença do trabalho equiparadas a acidente"},
{"url":L8213+"#art118","name":"Lei 8.213/1991, art. 118","anchor_claim":"garantia de manutenção do contrato após cessação do auxílio-doença acidentário"},
{"url":TST_IRR125,"name":"TST, Tema Repetitivo 125","anchor_claim":"tese vinculante sobre estabilidade por doença ocupacional reconhecida após o fim do contrato sem exigência de afastamento superior a quinze dias ou benefício acidentário"}
],
"internal_link_topics":["desconto de despesas de home office","teletrabalho sem aditivo escrito","doenca ocupacional e estabilidade"],
"lane":"comercial","word_count":0})

# 10
pages.append({
"intent_id":"trab-teletrabalho-hibrido-mudanca-dias",
"title":"Híbrido: a empresa pode mudar os dias presenciais?",
"meta_description":"No trabalho híbrido, a empresa altera os dias no escritório? Veja o que contrato, norma coletiva e arts. 75-B, 75-C e 468 da CLT realmente regulam.",
"h1":"Empresa muda meus dias presenciais toda semana: pode?",
"opening":"No trabalho híbrido, mudar segunda-feira por terça pode afetar transporte, cuidados familiares e organização da equipe. A CLT reconhece que o comparecimento habitual ao estabelecimento não descaracteriza o teletrabalho, mas não fixa uma antecedência universal para cada troca de dia presencial.\n\nOs limites podem vir do contrato, do aditivo, de norma coletiva e da forma como a escala foi definida. Também importa saber se houve simples ajuste dentro de um modelo variável ou alteração prejudicial de uma condição contratual. Misturar essas hipóteses leva a aplicar ao calendário semanal uma regra criada para mudança de regime.",
"sections":[
{"heading":"Como a CLT reconhece o trabalho híbrido","text":"O art. 75-B define teletrabalho ou trabalho remoto como prestação fora das dependências do empregador, de maneira preponderante ou não, com tecnologias de informação e comunicação e sem configurar trabalho externo. O § 1º esclarece que comparecer, ainda que habitualmente, para atividades específicas não descaracteriza o regime.\n\nPor isso, alternar casa e escritório pode permanecer dentro do teletrabalho. A lei não escolhe quais dias serão presenciais. Essa distribuição pode estar em aditivo, regulamento, norma coletiva ou escala variável comunicada pela empresa."},
{"heading":"Quando o art. 468 pode ser relevante","text":"O art. 468 veda alteração contratual sem mútuo consentimento quando dela resulta prejuízo direto ou indireto. Para aplicá-lo à escala híbrida, primeiro é preciso demonstrar qual condição integrava o contrato e qual mudança efetivamente ocorreu. Uma rotina longa é elemento de prova, mas não torna automaticamente cada dia da semana uma cláusula imutável. Frequência, comunicações e reserva expressa de flexibilidade ajudam a interpretar o arranjo.\n\nSe o aditivo fixa dias remotos ou uma norma coletiva exige antecedência, o descumprimento tem base objetiva. Quando o modelo sempre foi variável, o poder de organização é mais amplo, embora ainda encontre limites legais, contratuais, coletivos e antidiscriminatórios."},
{"heading":"A regra dos quinze dias não vale para toda troca de escala","text":"O art. 75-C, § 2º, permite ao empregador determinar a alteração do regime de teletrabalho para o presencial, com transição mínima de quinze dias e aditivo. Essa regra trata da mudança de regime para o presencial; não estabelece aviso de quinze dias para cada remanejamento de segunda por terça em um modelo que continua híbrido.\n\nSe a mudança semanal, na prática, elimina o teletrabalho e converte a atividade em presencial, o § 2º pode incidir. Se apenas redistribui dias dentro do regime, é necessário procurar outra fonte de previsibilidade no contrato, na norma coletiva, no regulamento ou no ajuste aplicável."},
{"heading":"Como documentar o problema sem ampliar a regra","text":"Guarde contrato, aditivo, política híbrida, norma coletiva e sucessivas escalas. Registre datas de comunicação e prejuízos concretos, como gastos adicionais ou impossibilidade de cumprir obrigação familiar previamente informada. Peça uma regra de antecedência e a confirmação dos dias por escrito. Compare também quantos dias remotos existiam antes e depois de cada mudança concreta.\n\nUma análise individual pode distinguir ajuste gerencial, descumprimento de cláusula e mudança efetiva para o presencial. Essa classificação vem antes de invocar o art. 468 ou os quinze dias do art. 75-C, evitando prometer estabilidade semanal que a lei não criou de forma geral."}
],
"faq":[
{"q":"A empresa pode definir uma escala híbrida variável?","a":"Pode haver escala variável se contrato, norma coletiva e política aplicável permitirem. A CLT não fixa dias universais, mas a organização ainda deve respeitar condições contratuais e outros limites legais."},
{"q":"Toda mudança de dia exige quinze dias de aviso?","a":"Não. O prazo do art. 75-C, § 2º, vale para alteração do regime de teletrabalho para o presencial, não automaticamente para cada troca de dia dentro de um regime que permanece híbrido."},
{"q":"Quando o prejuízo familiar importa?","a":"Documente o impacto e verifique cláusulas de previsibilidade, prioridade do art. 75-F e eventual necessidade de adaptação. O prejuízo é relevante para a análise, mas não cria sozinho uma escala fixa universal."}
],
"official_sources":[
{"url":CLT+"#art75b","name":"CLT, art. 75-B, caput e § 1º","anchor_claim":"definição de teletrabalho preponderante ou não e comparecimento habitual que não descaracteriza o regime"},
{"url":CLT+"#art75c","name":"CLT, art. 75-C, § 2º","anchor_claim":"mudança do teletrabalho para o presencial com transição mínima de quinze dias e aditivo"},
{"url":CLT+"#art468","name":"CLT, art. 468","anchor_claim":"limite para alteração contratual que resulte prejuízo direto ou indireto ao empregado"}
],
"internal_link_topics":["retorno forcado ao presencial","teletrabalho sem aditivo escrito","prioridade de teletrabalho por filho pequeno"],
"lane":"comercial","word_count":0})

# 11
pages.append({
"intent_id":"trab-rescisao-indireta-revogacao-teletrabalho",
"title":"Contrato remoto e retorno em outra cidade: quais limites?",
"meta_description":"A empresa encerrou o teletrabalho escrito e exige presença em outra cidade? Entenda a volta autorizada pela CLT e quando uma falta separada pode ser grave.",
"h1":"Fim do home office contratado: como avaliar o retorno",
"opening":"O teletrabalho pode constar expressamente do contrato e ainda assim ser encerrado por determinação do empregador. Essa é a regra atual do art. 75-C, § 2º, que exige transição mínima de quinze dias e registro em aditivo. Portanto, o documento escrito não cria, sozinho, permanência remota indefinida.\n\nA análise muda quando a ordem desrespeita essa transição, exige transferência para localidade diversa, viola cláusula mais favorável ou vem acompanhada de outra falta grave. Só depois de separar esses fatos faz sentido perguntar se existe base para rescisão indireta.",
"sections":[
{"heading":"O que a empresa pode determinar","text":"O caput do art. 75-C exige que o teletrabalho conste expressamente do contrato individual. O § 2º, contudo, autoriza a alteração para o regime presencial por determinação do empregador, desde que haja transição mínima de quinze dias e o correspondente aditivo. A regra alcança também o teletrabalho que estava escrito.\n\nA entrada no remoto segue lógica diferente: o § 1º exige mútuo acordo. Confundir os dois sentidos da mudança leva à afirmação incorreta de que o empregador precisa de novo consentimento para qualquer retorno. Contrato ou norma coletiva pode prever proteção adicional, mas ela precisa ser identificada."},
{"heading":"Outra cidade traz perguntas separadas","text":"Se o retorno exige prestação em localidade diversa da contratada e mudança de domicílio, o art. 469 da CLT pode impor limites à transferência. Também é necessário verificar a localidade registrada, a existência de estabelecimentos, a natureza da ordem e cláusulas mais favoráveis. Distância e custo são fatos relevantes, mas não substituem esse enquadramento.\n\nO art. 75-C, § 3º, prevê ainda que o empregador não responde pelas despesas do retorno ao presencial quando o empregado optou por realizar teletrabalho fora da localidade do contrato, salvo disposição em contrário. Por isso, morar longe por escolha posterior e ser contratado originalmente em outra cidade são situações que não devem ser tratadas como idênticas."},
{"heading":"Quando uma falta pode sustentar rescisão indireta","text":"O art. 483 exige enquadramento em uma das faltas atribuídas ao empregador e gravidade compatível com a ruptura. A alínea \"a\" inclui exigência de serviços alheios ao contrato, além de outras hipóteses ali descritas; a alínea \"d\" trata do descumprimento das obrigações contratuais. O retorno autorizado pelo art. 75-C não se torna falta grave apenas porque o remoto constava do contrato.\n\nPodem alterar a análise o descumprimento dos quinze dias e do aditivo, uma transferência vedada, a violação reiterada de cláusula mais favorável ou outra conduta grave comprovada. Mesmo nesses casos, rescisão indireta não é consequência automática: fatos, contemporaneidade, prova e intensidade precisam ser avaliados."},
{"heading":"Como agir sem transformar dúvida em abandono","text":"Reúna contrato, aditivos, localidade contratual, comunicação do retorno, datas, norma coletiva e comprovantes das condições impostas. Peça correção do prazo ou esclarecimento sobre o local antes de concluir que a ordem inteira é inválida. Registre também propostas intermediárias e a resposta recebida.\n\nO § 3º do art. 483 permite, nas hipóteses das alíneas \"d\" e \"g\", pleitear a rescisão permanecendo ou não no serviço até a decisão final. Essa regra especial não é orientação genérica para parar de trabalhar. A estratégia depende do enquadramento correto e do risco disciplinar, razão pela qual deve ser definida a partir dos documentos do caso."}
],
"faq":[
{"q":"Teletrabalho escrito impede retorno determinado pela empresa?","a":"Não. O art. 75-C, § 2º, permite determinar a volta ao presencial, com transição mínima de quinze dias e aditivo. Cláusula ou norma mais favorável pode acrescentar condições."},
{"q":"Presencial em outra cidade é sempre transferência ilegal?","a":"Não. É preciso verificar localidade contratual, necessidade de mudança de domicílio, circunstâncias do art. 469 e se o empregado escolheu trabalhar remotamente fora da localidade original."},
{"q":"Posso parar de trabalhar e pedir rescisão indireta?","a":"O art. 483 traz regra específica para certas alíneas, mas a escolha é arriscada se o enquadramento estiver errado. O retorno, por si só, é autorizado; eventual falta separada e sua gravidade precisam ser provadas."}
],
"official_sources":[
{"url":CLT+"#art75c","name":"CLT, art. 75-C, caput e §§ 1º a 3º","anchor_claim":"registro do teletrabalho, regras distintas de ingresso e retorno ao presencial e despesas na volta de outra localidade"},
{"url":CLT+"#art469","name":"CLT, art. 469","anchor_claim":"limites e exceções para transferência a localidade diversa que implique mudança de domicílio"},
{"url":CLT+"#art483","name":"CLT, art. 483, alíneas a e d e § 3º","anchor_claim":"hipóteses de rescisão indireta e regra sobre permanência no serviço em alíneas específicas"}
],
"internal_link_topics":["retorno forcado ao presencial","mudanca de dias no trabalho hibrido","teletrabalho sem aditivo escrito"],
"lane":"comercial","word_count":0})

# 12
pages.append({
"intent_id":"trab-assedio-moral-remoto-grupos-mensagem",
"title":"Assédio moral em grupo de WhatsApp: como provar",
"meta_description":"Sofre cobrança humilhante em grupos de WhatsApp ou Teams da empresa? Veja como reunir provas digitais do assédio moral remoto e o que a CLT permite fazer.",
"h1":"Humilhação em grupo de mensagens da empresa: o que fazer",
"opening":"Cobranças humilhantes em grupos de mensagem, exposição pública de erros e ataques reiterados também podem ocorrer no trabalho remoto. O ambiente digital deixa registros úteis, mas uma captura de tela não explica sozinha autoria, integridade, contexto nem repetição.\n\nÉ preciso separar cobrança legítima, conduta inadequada isolada e padrão de assédio moral. Essa distinção não minimiza um episódio único: ele pode gerar outras consequências mesmo quando não reúne todos os elementos normalmente associados ao assédio continuado.",
"sections":[
{"heading":"Repetição, duração e efeito sobre a dignidade","text":"Material institucional do TST descreve assédio moral como exposição a situações humilhantes e constrangedoras de forma repetitiva e prolongada durante a jornada e no exercício das funções. A análise considera a degradação das condições de trabalho e a violação da dignidade, não uma exigência universal de provar intenção psicológica específica do autor. Frequência, posição hierárquica, alcance do grupo e efeito sobre o ambiente ajudam a caracterizar o padrão.\n\nNo ambiente digital, ele pode aparecer em sucessivas exposições, apelidos, ameaças, isolamento ou cobranças degradantes. Uma mensagem isolada geralmente não demonstra repetição e prolongamento; ainda assim, pode constituir ofensa, discriminação, ameaça ou outro ilícito conforme seu conteúdo e contexto."},
{"heading":"Como preservar mensagens sem prometer prova conclusiva","text":"Mantenha a conversa completa, com participantes, datas, horários e mensagens anteriores e posteriores. Exporte o histórico quando a ferramenta permitir, conserve o arquivo original e registre como ele foi obtido. Capturas recortadas podem ocultar contexto; montagens comprometem a confiabilidade. Testemunhas e comunicações por outros canais podem confirmar a dinâmica.\n\nO art. 384 do CPC permite documentar fatos por ata notarial, inclusive dados representados por imagem ou som em arquivos eletrônicos. A ata registra o que o tabelião constatou naquele momento; não decide, por si só, autoria, veracidade de todas as falas ou caracterização jurídica do assédio."},
{"heading":"Dano, responsabilidade e vínculo com a empresa","text":"Os arts. 223-B e 223-C da CLT protegem bens da esfera moral, como honra, imagem, intimidade, autoestima e saúde. Para responsabilização, é necessário demonstrar conduta, dano e os demais elementos aplicáveis. Os arts. 932, III, e 933 do Código Civil também disciplinam a responsabilidade do empregador ou comitente por atos de empregados, serviçais e prepostos no exercício do trabalho ou em razão dele.\n\nIsso não significa que toda mensagem de colega seja automaticamente imputada à empresa em qualquer contexto. Importam autoria, relação com o trabalho, exercício das funções, ciência e resposta organizacional. Em quadro grave, o art. 483 da CLT pode ser discutido, mas rescisão indireta depende de falta enquadrável e suficientemente séria."},
{"heading":"Como organizar uma avaliação responsável","text":"Monte uma linha do tempo com episódios, participantes, canais, testemunhas e efeitos concretos. Preserve também reclamações internas e respostas, sem retirar arquivos sigilosos aos quais você não tenha acesso legítimo. Se houver risco à saúde, busque atendimento e guarde a documentação clínica pertinente, com as datas correspondentes de cada etapa.\n\nUma orientação jurídica individual pode avaliar o conjunto e indicar medidas de preservação, comunicação interna, reparação ou discussão contratual. O conteúdo não deve estimular confronto imediato, contratação ou ação judicial automática: a medida adequada depende da segurança da pessoa, da qualidade da prova e da gravidade do caso."}
],
"faq":[
{"q":"Print de conversa serve como prova?","a":"Pode integrar a prova quando preserva remetente, data, horário e contexto. Arquivo exportado, testemunhas e outros registros ajudam a avaliar integridade e autoria; ata notarial documenta o que foi constatado, sem decidir o mérito."},
{"q":"Uma cobrança dura já é assédio moral?","a":"Não necessariamente. Assédio costuma envolver conduta humilhante repetida e prolongada. Um episódio isolado pode não preencher esse padrão, mas ainda pode ter consequência jurídica conforme gravidade e conteúdo."},
{"q":"Assédio em mensagens permite rescisão indireta?","a":"Pode haver discussão sob o art. 483 quando a conduta comprovada é grave e se enquadra nas hipóteses legais. A presença de mensagens não torna a ruptura automática; contexto, repetição, autoria e gravidade importam."}
],
"official_sources":[
{"url":CLT+"#art223b","name":"CLT, arts. 223-B e 223-C","anchor_claim":"dano extrapatrimonial e bens juridicamente tutelados da pessoa física"},
{"url":CLT+"#art483","name":"CLT, art. 483","anchor_claim":"hipóteses de rescisão indireta, incluindo rigor excessivo e atos lesivos à honra e boa fama"},
{"url":CPC+"#art384","name":"CPC, art. 384","anchor_claim":"documentação de fatos por ata notarial, inclusive dados em arquivos eletrônicos"},
{"url":CC+"#art932","name":"Código Civil, arts. 932, III, e 933","anchor_claim":"responsabilidade por atos de empregados, serviçais e prepostos no exercício do trabalho ou em razão dele"},
{"url":TST_ASSEDIO,"name":"TST — material educativo sobre assédio moral e sexual","anchor_claim":"conceito institucional de exposição humilhante e constrangedora repetitiva e prolongada no trabalho"}
],
"internal_link_topics":["disponibilidade por aplicativo e sobreaviso","punicao por monitoramento de tela","rescisao indireta no teletrabalho"],
"lane":"comercial","word_count":0})

# --- write ---
for p in pages:
    p["word_count"] = wc(p)

out = "/opt/wiki/data/editorial/v2_pages/trabalhista-p1.jsonl"
tmpf = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=os.path.dirname(out), delete=False, suffix=".tmp")
try:
    for p in pages:
        tmpf.write(json.dumps(p, ensure_ascii=False) + "\n")
    tmpf.flush(); os.fsync(tmpf.fileno()); tmpf.close()
    os.replace(tmpf.name, out)
finally:
    if os.path.exists(tmpf.name):
        os.remove(tmpf.name)

# local sanity
for p in pages:
    t=len(p["title"]); m=len(p["meta_description"])
    flags=[]
    if not (20<=t<=65): flags.append(f"TITLE_LEN={t}")
    if not (70<=m<=160): flags.append(f"META_LEN={m}")
    if p["h1"].strip().lower()==p["title"].strip().lower(): flags.append("H1_EQ_TITLE")
    band=(700,1400); wcv=p["word_count"]
    if not (band[0]*0.9<=wcv<=band[1]*1.1): flags.append(f"WC_BAND={wcv}")
    ns=len(p["official_sources"]); 
    if not (2<=ns<=5): flags.append(f"NSRC={ns}")
    nsec=len(p["sections"])+ (1 if p["faq"] else 0)
    if nsec<4: flags.append(f"SEC={nsec}")
    print(p["intent_id"], "title",t,"meta",m,"wc",wcv,"sec",len(p["sections"]),"faq",len(p["faq"]),"src",ns, ("OK" if not flags else "!! "+",".join(flags)))
print("titles unique:", len({p["title"] for p in pages})==len(pages))
print("meta unique:", len({p["meta_description"] for p in pages})==len(pages))
print("h1 unique:", len({p["h1"] for p in pages})==len(pages))
print("wrote", len(pages), "->", out)
