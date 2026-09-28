#!/usr/bin/env python3
"""Constroi data/research/source_hint_curation/trabalhista_w4_curated.jsonl.

Entrada: .agents/runtime/staging/curadoria_trabalhista_w4/{part1,part2}.jsonl
Saida: schema exato {hint, name, url, anchor_claim, source_kind} exigido por
tools/generate-curated-source-hints (unico caminho sancionado ao catalogo).

part1: slug_key -> hint; ja traz source_kind e anchor_claim autoral limpo.
       As 14 chaves ja cobertas pelo catalogo sao dropadas aqui.
part2: key -> hint; source_kind atribuido por regra de host/path; anchor_claim
       REESCRITO por chave (o original era despejo de grep truncado).
Script efemero (tools/_tmp_* e ruido classificado no .gitignore).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools import generate_v2_review_queue as producer  # noqa: E402

STAGING = os.path.join(ROOT, ".agents/runtime/staging/curadoria_trabalhista_w4")
OUT = os.path.join(
    ROOT, "data/research/source_hint_curation/trabalhista_w4_curated.jsonl")
CATALOG = os.path.join(ROOT, "data/editorial/v2_source_hint_catalog.json")

# Chave com candidato divergente pre-existente em outro arquivo do mesmo
# diretorio (cowork-w3-agent-02.jsonl, URL caixa.gov.br que responde 302):
# incluir aqui reprovaria AMBOS por divergencia. Fica de fora e vai no relato.
DROP = {"app-fgts"}

# --- anchor_claims autorais para as chaves da part2 (uma frase especifica
# sobre o que a fonte estabelece; base: texto oficial capturado no
# evidence_grep + ementa da norma). ---
LIVRO = ("publicado no Livro de Súmulas, Orientações Jurisprudenciais e "
         "Precedentes Normativos do Tribunal")

CLAIMS = {
    # ---------------- Planalto: Codigo Penal ----------------
    "codigo-penal-art-149": "texto oficial vigente do art. 149 do Código Penal, que tipifica a redução de alguém a condição análoga à de escravo mediante trabalhos forçados, jornada exaustiva, condições degradantes de trabalho ou restrição da locomoção em razão de dívida contraída com o empregador",
    "codigo-penal-art-168-a": "texto oficial vigente do art. 168-A do Código Penal, que tipifica a apropriação indébita previdenciária consistente em deixar de repassar à previdência social as contribuições recolhidas dos contribuintes no prazo e na forma legal ou convencional",
    "codigo-penal-art-216-a": "texto oficial vigente do art. 216-A do Código Penal, que tipifica o assédio sexual praticado por quem se prevalece da condição de superior hierárquico ou da ascendência inerente ao exercício de emprego, cargo ou função",
    "codigo-penal-art-302": "texto oficial vigente do art. 302 do Código Penal, que tipifica a conduta do médico que, no exercício da profissão, fornece atestado falso, com pena de multa cumulativa quando o crime é cometido com fim de lucro",
    # ---------------- Planalto: decretos ----------------
    "decreto-10060-2019": "texto oficial vigente do Decreto nº 10.060/2019, que regulamenta a Lei nº 6.019/1974 na parte relativa ao trabalho temporário e às obrigações das empresas de trabalho temporário",
    "decreto-10854-2021": "texto oficial vigente do Decreto nº 10.854/2021, que regulamenta disposições da legislação trabalhista e institui o Programa Permanente de Consolidação, Simplificação e Desburocratização de Normas Trabalhistas Infralegais",
    "decreto-5113-2004": "texto oficial vigente do Decreto nº 5.113/2004, que regulamenta o art. 20, inciso XVI, da Lei nº 8.036/1990 e disciplina a movimentação da conta vinculada do FGTS por necessidade pessoal urgente e grave decorrente de desastre natural",
    "decreto-73626-1974": "texto oficial vigente do Decreto nº 73.626/1974, que aprova o regulamento da Lei nº 5.889/1973 e detalha a aplicação das normas reguladoras do trabalho rural",
    # ---------------- gov.br: servicos ----------------
    "gov-br-trabalho": "página oficial de serviços do Ministério do Trabalho e Emprego no portal gov.br, que reúne os canais de Carteira de Trabalho Digital, FGTS, seguro-desemprego, registro profissional e qualificação profissional",
    # ---------------- LC 150/2015 (domestico) ----------------
    "lc-150-2015-art-1": "texto oficial vigente do art. 1º da Lei Complementar nº 150/2015, que define o empregado doméstico como quem presta serviços de forma contínua, subordinada, onerosa e pessoal, com finalidade não lucrativa, no âmbito residencial da pessoa ou da família",
    "lc-150-2015-art-11": "texto oficial vigente do art. 11 da Lei Complementar nº 150/2015, que trata do empregado doméstico que acompanha o empregador em viagem e manda considerar apenas as horas efetivamente trabalhadas no período, admitida compensação",
    "lc-150-2015-art-2": "texto oficial vigente do art. 2º da Lei Complementar nº 150/2015, que limita a jornada do empregado doméstico a oito horas diárias e quarenta e quatro semanais e fixa em no mínimo cinquenta por cento o adicional da hora extraordinária",
    "lc-150-2015-art-31": "texto oficial vigente do art. 31 da Lei Complementar nº 150/2015, que institui o Simples Doméstico, regime unificado de pagamento dos tributos, das contribuições e dos demais encargos do empregador doméstico",
    "lc-150-2015-arts-2-e-12": "texto oficial vigente dos arts. 2º e 12 da Lei Complementar nº 150/2015, que fixam a jornada do empregado doméstico e tornam obrigatório o registro do horário de trabalho por meio manual, mecânico ou eletrônico idôneo",
    "lc-150-2015-arts-21-e-22": "texto oficial vigente dos arts. 21 e 22 da Lei Complementar nº 150/2015, que determinam a inclusão do empregado doméstico no FGTS e criam o depósito mensal destinado à indenização compensatória da perda do emprego sem justa causa",
    "lc-150-2015-arts-26-a-28": "texto oficial vigente dos arts. 26 a 28 da Lei Complementar nº 150/2015, que asseguram ao empregado doméstico dispensado sem justa causa o seguro-desemprego no valor de um salário mínimo e fixam as condições e o número de parcelas",
    # ---------------- Planalto: leis ----------------
    "lei-10097-2000": "texto oficial vigente da Lei nº 10.097/2000, que alterou dispositivos da CLT para disciplinar o contrato de aprendizagem e a obrigação de os estabelecimentos contratarem aprendizes",
    "lei-10101-2000-art-6": "texto oficial vigente do art. 6º da Lei nº 10.101/2000, que autoriza o trabalho aos domingos no comércio varejista em geral e exige que o repouso semanal remunerado coincida periodicamente com o domingo, observada a legislação municipal",
    "lei-10243-2001": "texto oficial vigente da Lei nº 10.243/2001, que acrescentou parágrafos ao art. 58 da CLT sobre o tempo à disposição do empregador e deu nova redação ao § 2º do art. 458 quanto às utilidades não consideradas salário",
    "lei-11101-2005-art-83": "texto oficial vigente do art. 83 da Lei nº 11.101/2005, que classifica os créditos na falência e coloca em primeiro lugar os derivados da legislação do trabalho, limitados a cento e cinquenta salários mínimos por credor, e os decorrentes de acidente de trabalho",
    "lei-11442-2007": "texto oficial vigente da Lei nº 11.442/2007, que disciplina o transporte rodoviário de cargas por conta de terceiros e mediante remuneração, inclusive a atuação do transportador autônomo de cargas",
    "lei-12690-2012": "texto oficial vigente da Lei nº 12.690/2012, que dispõe sobre a organização e o funcionamento das cooperativas de trabalho e institui o Programa Nacional de Fomento às Cooperativas de Trabalho",
    "lei-12740-2012": "texto oficial vigente da Lei nº 12.740/2012, que alterou o art. 193 da CLT para redefinir os critérios de caracterização das atividades perigosas e o direito ao adicional de periculosidade",
    "lei-12815-2013": "texto oficial vigente da Lei nº 12.815/2013, que dispõe sobre a exploração de portos e instalações portuárias e sobre as atividades dos operadores portuários, inclusive o trabalho portuário avulso e o órgão gestor de mão de obra",
    "lei-12873-2013": "texto oficial vigente da Lei nº 12.873/2013, que alterou a CLT para disciplinar a licença-maternidade em caso de adoção e a transferência do benefício ao empregado sobrevivente no caso de falecimento da genitora",
    "lei-12997-2014": "texto oficial vigente da Lei nº 12.997/2014, que acrescentou o § 4º ao art. 193 da CLT para considerar perigosas as atividades de trabalhador em motocicleta",
    "lei-13257-2016": "texto oficial vigente da Lei nº 13.257/2016 (Marco Legal da Primeira Infância), que alterou a CLT para permitir a ausência do empregado em consultas e exames do filho e ampliou a licença-paternidade no Programa Empresa Cidadã",
    "lei-13352-2016": "texto oficial vigente da Lei nº 13.352/2016, que alterou a Lei nº 12.592/2012 para instituir o contrato de parceria entre salão-parceiro e profissional-parceiro nas atividades de cabeleireiro, barbeiro, esteticista, manicure, pedicure, depilador e maquiador",
    "lei-14457-2022": "texto oficial vigente da Lei nº 14.457/2022, que institui o Programa Emprega + Mulheres e altera a CLT com medidas de apoio à parentalidade, flexibilização de jornada e prevenção do assédio no ambiente de trabalho",
    "lei-14611-2023": "texto oficial vigente da Lei nº 14.611/2023, que dispõe sobre a igualdade salarial e de critérios remuneratórios entre mulheres e homens e altera a CLT para prever multa específica e relatórios periódicos de transparência salarial",
    "lei-3207-1957": "texto oficial vigente da Lei nº 3.207/1957, que regulamenta as atividades dos empregados vendedores, viajantes ou pracistas, inclusive comissões, zona de trabalho e prestação de contas",
    "lei-3207-1957-art-7": "texto oficial vigente do art. 7º da Lei nº 3.207/1957, que assegura ao empregador o direito de estornar a comissão já paga quando verificada a insolvência do comprador",
    "lei-4375-1964": "texto oficial vigente da Lei nº 4.375/1964 (Lei do Serviço Militar), que fixa a natureza, a obrigatoriedade e a duração do serviço militar e as situações do convocado e do incorporado",
    "lei-4749-1965": "texto oficial vigente da Lei nº 4.749/1965, que disciplina o pagamento da gratificação natalina instituída pela Lei nº 4.090/1962, com quitação até 20 de dezembro e compensação do adiantamento já pago",
    "lei-4749-1965-art-1": "texto oficial vigente do art. 1º da Lei nº 4.749/1965, que obriga o empregador a pagar a gratificação natalina até o dia 20 de dezembro de cada ano, compensada a importância paga a título de adiantamento",
    "lei-5553-1968": "texto oficial vigente da Lei nº 5.553/1968, que disciplina a apresentação e o uso de documentos de identificação pessoal e veda a retenção do documento por quem o recebe",
    "lei-5889-1973-art-14": "texto oficial vigente do art. 14 da Lei nº 5.889/1973, que assegura ao safrista, ao término normal do contrato, indenização de tempo de serviço equivalente a um doze avos do salário mensal por mês de serviço ou fração superior a quatorze dias",
    "lei-5889-1973-art-9": "texto oficial vigente do art. 9º da Lei nº 5.889/1973, que enumera de forma taxativa os descontos admitidos ao empregado rural, calculados sobre o salário mínimo, ressalvadas autorização legal e decisão judicial",
    "lei-6019-1974-art-5-a": "texto oficial vigente do art. 5º-A da Lei nº 6.019/1974, que define contratante como a pessoa física ou jurídica que celebra contrato com empresa de prestação de serviços determinados e específicos",
    "lei-6019-1974-art-5-a-par-3": "texto oficial vigente do art. 5º-A, § 3º, da Lei nº 6.019/1974, que atribui à contratante o dever de garantir as condições de segurança, higiene e salubridade dos trabalhadores terceirizados quando o serviço é prestado em suas dependências ou em local convencionado",
    "lei-605-1949": "texto oficial vigente da Lei nº 605/1949, que assegura o repouso semanal remunerado de vinte e quatro horas consecutivas, preferentemente aos domingos, e o pagamento do salário nos feriados civis e religiosos",
    "lei-605-1949-art-1": "texto oficial vigente do art. 1º da Lei nº 605/1949, que garante a todo empregado repouso semanal remunerado de vinte e quatro horas consecutivas, preferentemente aos domingos e, nos limites das exigências técnicas das empresas, nos feriados",
    "lei-605-1949-art-9": "texto oficial vigente do art. 9º da Lei nº 605/1949, que manda pagar em dobro a remuneração do trabalho prestado em feriado civil ou religioso, salvo quando o empregador determina outro dia de folga",
    "lei-7064-1982": "texto oficial vigente da Lei nº 7.064/1982, que disciplina a situação dos trabalhadores contratados no Brasil ou transferidos para prestar serviços no exterior, inclusive a legislação aplicável e as garantias mínimas do contrato",
    "lei-7418-1985": "texto oficial vigente da Lei nº 7.418/1985, que institui o vale-transporte como antecipação custeada pelo empregador para o deslocamento do empregado entre a residência e o local de trabalho",
    "lei-7783-1989": "texto oficial vigente da Lei nº 7.783/1989, que regula o exercício do direito de greve, define as atividades essenciais e disciplina o atendimento das necessidades inadiáveis da comunidade",
    "lei-7998-1990-art-2-c": "texto oficial vigente do art. 2º-C da Lei nº 7.998/1990, que assegura ao trabalhador identificado como submetido a trabalho forçado ou a condição análoga à de escravo, em ação de fiscalização do trabalho, o pagamento de parcelas do seguro-desemprego",
    "lei-7998-1990-art-4": "texto oficial vigente do art. 4º da Lei nº 7.998/1990, que fixa em até quatro meses, de forma contínua ou alternada, a duração do seguro-desemprego a cada período aquisitivo de dezesseis meses",
    "lei-7998-1990-art-9": "texto oficial vigente do art. 9º da Lei nº 7.998/1990, que assegura o abono salarial anual aos empregados que preenchem os requisitos de cadastro, tempo de vínculo e remuneração média nele previstos",
    "lei-8036-1990-art-18-par-1": "texto oficial vigente do art. 18, § 1º, da Lei nº 8.036/1990, que obriga o empregador, na dispensa sem justa causa, a depositar importância igual a quarenta por cento do montante dos depósitos do FGTS feitos na conta vinculada, atualizados e acrescidos de juros",
    "lei-8036-1990-art-3": "texto oficial vigente do art. 3º da Lei nº 8.036/1990, que atribui ao Conselho Curador do FGTS, de composição tripartite, a fixação das normas e diretrizes do Fundo",
    "lei-8212-1991-art-30": "texto oficial vigente do art. 30 da Lei nº 8.212/1991, que fixa as regras de arrecadação e recolhimento das contribuições devidas à Seguridade Social, inclusive o desconto da contribuição do empregado pela empresa",
    "lei-8212-1991-art-33-par-5": "texto oficial vigente do art. 33, § 5º, da Lei nº 8.212/1991, segundo o qual o desconto da contribuição se presume sempre feito oportuna e regularmente pela empresa obrigada, que não pode alegar omissão para se eximir do recolhimento",
    "lei-8213-1991-art-21-a": "texto oficial vigente do art. 21-A da Lei nº 8.213/1991, que manda a perícia médica do INSS caracterizar a natureza acidentária da incapacidade quando constatado nexo técnico epidemiológico entre o trabalho e o agravo",
    "lei-8213-1991-art-21-i": "texto oficial vigente do art. 21, I, da Lei nº 8.213/1991, que equipara a acidente do trabalho o acidente ligado ao trabalho que, embora não seja a causa única, contribui diretamente para a morte do segurado ou para a redução ou perda da capacidade laborativa",
    "lei-8213-1991-art-21-iv": "texto oficial vigente do art. 21, IV, da Lei nº 8.213/1991, que equipara a acidente do trabalho o sofrido fora do local e do horário de trabalho na execução de ordem da empresa, em viagem a serviço ou no percurso entre a residência e o local de trabalho",
    "lei-8213-1991-art-40": "texto oficial vigente do art. 40 da Lei nº 8.213/1991, que assegura abono anual ao segurado e ao dependente que, durante o ano, receberam auxílio-doença, auxílio-acidente, aposentadoria, pensão por morte ou auxílio-reclusão",
    "lei-8213-1991-art-58-par-4": "texto oficial vigente do art. 58, § 4º, da Lei nº 8.213/1991, que exige a comprovação da efetiva exposição a agentes nocivos por formulário emitido pela empresa com base em laudo técnico de condições ambientais do trabalho",
    "lei-8213-1991-art-65": "texto oficial vigente do art. 65 da Lei nº 8.213/1991, que assegura o salário-família ao segurado empregado, exceto o doméstico, e ao trabalhador avulso, na proporção do número de filhos ou equiparados",
    "lei-8213-1991-art-89": "texto oficial vigente do art. 89 da Lei nº 8.213/1991, que define a finalidade da habilitação e da reabilitação profissional e social devidas ao beneficiário incapacitado e à pessoa com deficiência",
    "lei-8213-1991-art-93": "texto oficial vigente do art. 93 da Lei nº 8.213/1991, que obriga a empresa com cem ou mais empregados a preencher de dois a cinco por cento dos cargos com beneficiários reabilitados ou pessoas com deficiência habilitadas, na proporção nele fixada",
    "lei-8213-1991-art-93-par-1": "texto oficial vigente do art. 93, § 1º, da Lei nº 8.213/1991, que condiciona a dispensa de empregado com deficiência ou reabilitado, em contrato por prazo indeterminado ou determinado de mais de noventa dias, à contratação de substituto em condição semelhante",
    "lei-9029-1995-art-1": "texto oficial vigente do art. 1º da Lei nº 9.029/1995, que proíbe prática discriminatória e limitativa para acesso à relação de emprego ou sua manutenção por motivo de sexo, origem, raça, cor, estado civil, situação familiar, deficiência, reabilitação profissional ou idade",
    "lei-9029-1995-art-2": "texto oficial vigente do art. 2º da Lei nº 9.029/1995, que tipifica como crime a exigência de teste, exame, perícia, laudo ou atestado relativo a esterilização ou a estado de gravidez e a indução a práticas de controle de natalidade",
    "lei-9504-1997-art-98": "texto oficial vigente do art. 98 da Lei nº 9.504/1997, que assegura aos eleitores nomeados para mesas receptoras ou juntas eleitorais e aos requisitados dispensa do serviço, sem prejuízo do salário, pelo dobro dos dias de convocação",
    "lei-9608-1998": "texto oficial vigente da Lei nº 9.608/1998, que define o serviço voluntário como atividade não remunerada que não gera vínculo empregatício nem obrigação de natureza trabalhista, previdenciária ou afim",
    "lei-9615-1998": "texto oficial vigente da Lei nº 9.615/1998 (Lei Pelé), cujo art. 28 caracteriza a atividade do atleta profissional pela remuneração pactuada em contrato especial de trabalho firmado com entidade de prática desportiva",
    # ---------------- Normas Regulamentadoras (MTE) ----------------
    "nr-15-anexo-1": "anexo nº 1 da NR-15 publicado pelo Ministério do Trabalho e Emprego, que fixa os limites de tolerância para ruído contínuo ou intermitente e a máxima exposição diária permitida para cada nível de ruído em decibéis",
    "nr-15-anexo-14": "anexo nº 14 da NR-15 publicado pelo Ministério do Trabalho e Emprego, que relaciona as atividades envolvendo agentes biológicos cuja insalubridade é caracterizada por avaliação qualitativa em grau máximo ou médio",
    "nr-15-anexo-3": "anexo nº 3 da NR-15 publicado pelo Ministério do Trabalho e Emprego, que fixa os limites de tolerância para exposição ao calor e o método oficial de avaliação da sobrecarga térmica",
    "nr-15-anexo-9": "anexo nº 9 da NR-15 publicado pelo Ministério do Trabalho e Emprego, que caracteriza como insalubres as atividades executadas no interior de câmaras frigoríficas ou em locais de condições similares sem a proteção adequada contra o frio",
    "nr-16": "página oficial do Ministério do Trabalho e Emprego sobre a NR-16, que relaciona as atividades e operações perigosas que dão direito ao adicional de periculosidade e remete aos anexos por agente de risco",
    "nr-17": "página oficial do Ministério do Trabalho e Emprego sobre a NR-17, que estabelece os parâmetros de ergonomia para adaptação das condições de trabalho às características psicofisiológicas dos trabalhadores",
    "nr-17-anexo-ii": "anexo II da NR-17 publicado pelo Ministério do Trabalho e Emprego, que fixa os parâmetros mínimos do trabalho em teleatendimento e telemarketing, inclusive jornada, pausas, mobiliário e organização do trabalho",
    "nr-24": "página oficial do Ministério do Trabalho e Emprego sobre a NR-24, que fixa as condições de higiene e conforto nos locais de trabalho, como instalações sanitárias, vestiários, refeitórios e fornecimento de água potável",
    "nr-31": "página oficial do Ministério do Trabalho e Emprego sobre a NR-31, que estabelece os preceitos de segurança e saúde no trabalho na agricultura, pecuária, silvicultura, exploração florestal e aquicultura",
    "nr-5": "página oficial do Ministério do Trabalho e Emprego sobre a NR-5, que disciplina a Comissão Interna de Prevenção de Acidentes e de Assédio (CIPA), seu dimensionamento, processo eleitoral e atribuições",
    "nr-7": "página oficial do Ministério do Trabalho e Emprego sobre a NR-7, que estabelece o Programa de Controle Médico de Saúde Ocupacional (PCMSO) e os exames médicos ocupacionais obrigatórios",
    # ---------------- TST: OJs da SBDI-1 ----------------
    "oj-113-sdi-1-tst": f"verbete oficial da Orientação Jurisprudencial nº 113 da SBDI-1 do TST, {LIVRO}, segundo o qual o adicional de transferência é devido ainda que o empregado exerça cargo de confiança ou haja previsão contratual de transferência, desde que esta seja provisória",
    "oj-125-sdi-1-tst": f"verbete oficial da Orientação Jurisprudencial nº 125 da SBDI-1 do TST, {LIVRO}, segundo o qual o simples desvio funcional não gera direito a novo enquadramento, mas apenas às diferenças salariais respectivas",
    "oj-355-sdi-1-tst": f"registro oficial de que a Orientação Jurisprudencial nº 355 da SBDI-1 do TST, sobre horas extras pela inobservância do intervalo interjornadas do art. 66 da CLT, foi cancelada por perda de eficácia a partir de 11 de novembro de 2017 em razão da Lei nº 13.467/2017, conforme o Livro de Súmulas, Orientações Jurisprudenciais e Precedentes Normativos do Tribunal",
    "oj-358-sdi-1-tst": f"verbete oficial da Orientação Jurisprudencial nº 358 da SBDI-1 do TST, {LIVRO}, que admite o pagamento do piso salarial ou do salário mínimo proporcional na contratação para jornada reduzida, mas considera inválida, na Administração Pública direta, autárquica e fundacional, remuneração de empregado público inferior ao salário mínimo",
    "oj-394-sdi-1-tst": f"verbete oficial da Orientação Jurisprudencial nº 394 da SBDI-1 do TST, {LIVRO}, segundo o qual a majoração do repouso semanal remunerado decorrente da integração das horas extras habituais deve repercutir no cálculo das férias, do décimo terceiro salário, do aviso prévio e dos depósitos do FGTS, sem bis in idem, a partir do marco temporal fixado no próprio verbete",
    "oj-82-sdi-1-tst": f"verbete oficial da Orientação Jurisprudencial nº 82 da SBDI-1 do TST, {LIVRO}, segundo o qual a data de saída anotada na CTPS deve corresponder à do término do prazo do aviso prévio, ainda que indenizado",
    # ---------------- TST: Sumulas ----------------
    "sumula-102-tst": f"verbete oficial da Súmula nº 102 do TST, {LIVRO}, que trata do bancário em cargo de confiança e estabelece que a gratificação não inferior a um terço do salário já remunera as duas horas excedentes de seis, além de fixar os critérios de enquadramento e de prova do exercício da função",
    "sumula-125-tst": f"verbete oficial da Súmula nº 125 do TST, {LIVRO}, segundo a qual o art. 479 da CLT se aplica ao trabalhador optante pelo FGTS admitido mediante contrato por prazo determinado",
    "sumula-14-tst": f"verbete oficial da Súmula nº 14 do TST, {LIVRO}, segundo a qual, reconhecida a culpa recíproca na rescisão do contrato de trabalho, o empregado tem direito a cinquenta por cento do valor do aviso prévio, do décimo terceiro salário e das férias proporcionais",
    "sumula-146-tst": f"verbete oficial da Súmula nº 146 do TST, {LIVRO}, segundo a qual o trabalho prestado em domingos e feriados, não compensado, deve ser pago em dobro, sem prejuízo da remuneração relativa ao repouso semanal",
    "sumula-159-tst": f"verbete oficial da Súmula nº 159 do TST, {LIVRO}, segundo a qual o substituto faz jus ao salário contratual do substituído enquanto perdurar a substituição não meramente eventual, mas não tem direito a salário igual ao do antecessor quando o cargo fica vago em definitivo",
    "sumula-171-tst": f"verbete oficial da Súmula nº 171 do TST, {LIVRO}, segundo a qual, salvo dispensa por justa causa, a extinção do contrato de trabalho sujeita o empregador ao pagamento da remuneração das férias proporcionais ainda que incompleto o período aquisitivo",
    "sumula-244-i-tst": f"verbete oficial do item I da Súmula nº 244 do TST, {LIVRO}, segundo o qual o desconhecimento do estado gravídico pelo empregador não afasta o direito ao pagamento da indenização decorrente da estabilidade da gestante",
    "sumula-244-iii-tst": f"verbete oficial do item III da Súmula nº 244 do TST, {LIVRO}, segundo o qual a empregada gestante tem direito à estabilidade provisória mesmo na hipótese de admissão mediante contrato por tempo determinado",
    "sumula-244-tst": f"verbete oficial da Súmula nº 244 do TST, {LIVRO}, que trata da estabilidade da gestante e estabelece que o desconhecimento da gravidez não afasta a indenização, que a reintegração só é autorizada durante o período de estabilidade e que a garantia alcança o contrato por tempo determinado",
    "sumula-247-tst": f"verbete oficial da Súmula nº 247 do TST, {LIVRO}, segundo a qual a parcela paga aos bancários sob a denominação quebra de caixa tem natureza salarial e integra o salário do prestador de serviços para todos os efeitos legais",
    "sumula-248-tst": f"verbete oficial da Súmula nº 248 do TST, {LIVRO}, segundo a qual a reclassificação ou a descaracterização da insalubridade por ato da autoridade competente repercute na satisfação do respectivo adicional, sem ofensa a direito adquirido ou à irredutibilidade salarial",
    "sumula-261-tst": f"verbete oficial da Súmula nº 261 do TST, {LIVRO}, segundo a qual o empregado que se demite antes de completar doze meses de serviço tem direito a férias proporcionais",
    "sumula-264-tst": f"verbete oficial da Súmula nº 264 do TST, {LIVRO}, segundo a qual a remuneração do serviço suplementar é composta do valor da hora normal, integrado por parcelas de natureza salarial e acrescido do adicional previsto em lei, contrato, acordo, convenção coletiva ou sentença normativa",
    "sumula-27-tst": f"verbete oficial da Súmula nº 27 do TST, {LIVRO}, segundo a qual é devida a remuneração do repouso semanal e dos dias feriados ao empregado comissionista, ainda que pracista",
    "sumula-276-tst": f"verbete oficial da Súmula nº 276 do TST, {LIVRO}, segundo a qual o pedido de dispensa do cumprimento do aviso prévio não exime o empregador de pagar o respectivo valor, salvo comprovação de que o empregado obteve novo emprego",
    "sumula-289-tst": f"verbete oficial da Súmula nº 289 do TST, {LIVRO}, segundo a qual o simples fornecimento do aparelho de proteção não exime o empregador do pagamento do adicional de insalubridade, cabendo-lhe adotar as medidas que conduzam à diminuição ou eliminação da nocividade, entre elas o uso efetivo do equipamento",
    "sumula-291-tst": f"verbete oficial da Súmula nº 291 do TST, {LIVRO}, segundo a qual a supressão total ou parcial, pelo empregador, de serviço suplementar prestado com habitualidade por pelo menos um ano assegura ao empregado indenização correspondente",
    "sumula-32-tst": f"verbete oficial da Súmula nº 32 do TST, {LIVRO}, segundo a qual se presume o abandono de emprego se o trabalhador não retorna ao serviço no prazo de trinta dias após a cessação do benefício previdenciário nem justifica o motivo",
    "sumula-330-tst": f"verbete oficial da Súmula nº 330 do TST, {LIVRO}, segundo a qual a quitação passada pelo empregado com assistência da entidade sindical, observados os requisitos dos parágrafos do art. 477 da CLT, tem eficácia liberatória quanto às parcelas expressamente consignadas no recibo",
    "sumula-331-iv-tst": f"verbete oficial do item IV da Súmula nº 331 do TST, {LIVRO}, segundo o qual o inadimplemento das obrigações trabalhistas pelo empregador implica responsabilidade subsidiária do tomador dos serviços, desde que este tenha participado da relação processual e conste do título executivo judicial",
    "sumula-331-tst": f"verbete oficial da Súmula nº 331 do TST, {LIVRO}, que trata do contrato de prestação de serviços e fixa a ilicitude da contratação de trabalhadores por empresa interposta, as hipóteses em que não se forma vínculo com o tomador e a responsabilidade subsidiária deste",
    "sumula-338-tst": f"verbete oficial da Súmula nº 338 do TST, {LIVRO}, segundo a qual a não apresentação injustificada dos controles de frequência gera presunção relativa de veracidade da jornada alegada, que pode ser elidida por prova em contrário",
    "sumula-339-tst": f"verbete oficial da Súmula nº 339 do TST, {LIVRO}, segundo a qual o suplente da CIPA goza da garantia de emprego prevista no art. 10, II, 'a', do ADCT e essa estabilidade não constitui vantagem pessoal, mas garantia para a atividade dos membros da comissão",
    "sumula-340-tst": f"verbete oficial da Súmula nº 340 do TST, {LIVRO}, segundo a qual o empregado sujeito a controle de horário e remunerado à base de comissões tem direito ao adicional de no mínimo cinquenta por cento pelo trabalho em horas extras, calculado sobre o valor-hora das comissões recebidas",
    "sumula-342-tst": f"verbete oficial da Súmula nº 342 do TST, {LIVRO}, segundo a qual são válidos os descontos salariais autorizados prévia e por escrito pelo empregado para planos de assistência odontológica, médico-hospitalar, seguro, previdência privada ou entidade cooperativa, salvo vício de consentimento",
    "sumula-354-tst": f"verbete oficial da Súmula nº 354 do TST, {LIVRO}, segundo a qual as gorjetas cobradas na nota de serviço ou oferecidas espontaneamente pelos clientes integram a remuneração do empregado, mas não servem de base de cálculo para aviso prévio, adicional noturno, horas extras e repouso semanal remunerado",
    "sumula-357-tst": f"verbete oficial da Súmula nº 357 do TST, {LIVRO}, segundo a qual não torna suspeita a testemunha o simples fato de estar litigando ou de ter litigado contra o mesmo empregador",
    "sumula-362-tst": f"verbete oficial da Súmula nº 362 do TST, {LIVRO}, que fixa a prescrição do FGTS em trinta anos contados do termo inicial ou em cinco anos a partir de 13 de novembro de 2014, prevalecendo o prazo que se consumar primeiro, conforme o julgamento do ARE 709212 pelo STF",
    "sumula-367-tst": f"verbete oficial da Súmula nº 367 do TST, {LIVRO}, que trata do salário utilidade e registra, entre outros pontos, que o cigarro não se considera salário utilidade em face de sua nocividade à saúde",
    "sumula-369-tst": f"verbete oficial da Súmula nº 369 do TST, {LIVRO}, que trata da estabilidade do dirigente sindical, registra a recepção do art. 522 da CLT pela Constituição de 1988 e limita a garantia a sete dirigentes e igual número de suplentes",
    "sumula-371-tst": f"verbete oficial da Súmula nº 371 do TST, {LIVRO}, segundo a qual a projeção do aviso prévio indenizado se restringe às vantagens econômicas do período, mas, concedido auxílio-doença no curso do aviso, os efeitos da dispensa só se concretizam depois de expirado o benefício previdenciário",
    "sumula-372-tst": f"verbete oficial da Súmula nº 372 do TST, {LIVRO}, segundo a qual, percebida a gratificação de função por dez ou mais anos, a reversão ao cargo efetivo sem justo motivo não autoriza a retirada da parcela, em razão do princípio da estabilidade financeira",
    "sumula-376-tst": f"verbete oficial da Súmula nº 376 do TST, {LIVRO}, segundo a qual o valor das horas extras habitualmente prestadas integra o cálculo dos haveres trabalhistas independentemente da limitação prevista no caput do art. 59 da CLT",
    "sumula-378-ii-tst": f"verbete oficial do item II da Súmula nº 378 do TST, {LIVRO}, segundo o qual são pressupostos da estabilidade acidentária o afastamento superior a quinze dias e a consequente percepção do auxílio-doença acidentário, salvo constatação, após a despedida, de doença profissional relacionada à execução do contrato",
    "sumula-378-iii-tst": f"verbete oficial do item III da Súmula nº 378 do TST, {LIVRO}, segundo o qual o empregado submetido a contrato de trabalho por tempo determinado goza da garantia provisória de emprego decorrente de acidente do trabalho",
    "sumula-378-tst": f"verbete oficial da Súmula nº 378 do TST, {LIVRO}, que trata da estabilidade provisória decorrente de acidente do trabalho prevista no art. 118 da Lei nº 8.213/1991, fixando seus pressupostos e sua aplicação ao contrato por tempo determinado",
    "sumula-389-tst": f"verbete oficial da Súmula nº 389 do TST, {LIVRO}, segundo a qual compete à Justiça do Trabalho julgar o pedido de indenização pelo não fornecimento das guias do seguro-desemprego, cuja omissão pelo empregador dá origem ao direito à indenização",
    "sumula-396-tst": f"verbete oficial da Súmula nº 396 do TST, {LIVRO}, segundo a qual, exaurido o período de estabilidade, são devidos apenas os salários entre a data da despedida e o final desse período, não havendo julgamento extra petita na decisão que defere salários quando o pedido é de reintegração",
    "sumula-423-tst": "registro oficial de que a Súmula nº 423 do TST, sobre a fixação de jornada em turno ininterrupto de revezamento mediante negociação coletiva, foi cancelada por perda de eficácia em razão da decisão do STF no ARE 1.121.633, conforme o Livro de Súmulas, Orientações Jurisprudenciais e Precedentes Normativos do Tribunal",
    "sumula-425-tst": f"verbete oficial da Súmula nº 425 do TST, {LIVRO}, segundo a qual o jus postulandi previsto no art. 791 da CLT se limita às Varas do Trabalho e aos Tribunais Regionais do Trabalho, não alcançando ação rescisória, ação cautelar, mandado de segurança e recursos de competência do próprio TST",
    "sumula-428-tst": f"verbete oficial da Súmula nº 428 do TST, {LIVRO}, segundo a qual o uso de instrumento telemático ou informatizado fornecido pela empresa não caracteriza por si só o sobreaviso, que se configura quando o empregado, submetido a controle patronal, permanece em regime de plantão aguardando chamado ao serviço",
    "sumula-43-tst": f"verbete oficial da Súmula nº 43 do TST, {LIVRO}, segundo a qual se presume abusiva a transferência de que trata o § 1º do art. 469 da CLT quando não comprovada a necessidade do serviço",
    "sumula-440-tst": f"verbete oficial da Súmula nº 440 do TST, {LIVRO}, segundo a qual é assegurada a manutenção do plano de saúde ou de assistência médica oferecido pela empresa ao empregado mesmo com o contrato de trabalho suspenso por auxílio-doença acidentário ou aposentadoria por invalidez",
    "sumula-443-tst": f"verbete oficial da Súmula nº 443 do TST, {LIVRO}, segundo a qual se presume discriminatória a despedida de empregado portador do vírus HIV ou de outra doença grave que suscite estigma ou preconceito, cabendo a reintegração no emprego uma vez invalidado o ato",
    "sumula-448-ii-tst": f"verbete oficial do item II da Súmula nº 448 do TST, {LIVRO}, segundo o qual a higienização de instalações sanitárias de uso público ou coletivo de grande circulação e a respectiva coleta de lixo não se equiparam à limpeza de residências e escritórios e ensejam adicional de insalubridade em grau máximo",
    "sumula-448-tst": f"verbete oficial da Súmula nº 448 do TST, {LIVRO}, que condiciona a caracterização da insalubridade à classificação da atividade na relação oficial do Ministério do Trabalho e reconhece grau máximo na higienização de instalações sanitárias de uso público de grande circulação",
    "sumula-45-tst": f"verbete oficial da Súmula nº 45 do TST, {LIVRO}, segundo a qual a remuneração do serviço suplementar habitualmente prestado integra o cálculo da gratificação natalina prevista na Lei nº 4.090/1962",
    "sumula-451-tst": f"verbete oficial da Súmula nº 451 do TST, {LIVRO}, segundo a qual é devido o pagamento proporcional da participação nos lucros e resultados ao empregado dispensado sem justa causa antes da data da distribuição, inclusive na rescisão contratual antecipada",
    "sumula-51-tst": f"verbete oficial da Súmula nº 51 do TST, {LIVRO}, segundo a qual as cláusulas regulamentares que revoguem ou alterem vantagens só atingem os trabalhadores admitidos após a alteração e, havendo dois regulamentos da empresa, a opção por um deles implica renúncia às regras do outro",
    "sumula-6-tst": f"verbete oficial da Súmula nº 6 do TST, {LIVRO}, que fixa os critérios da equiparação salarial do art. 461 da CLT, inclusive a validade do quadro de carreira, o conceito de trabalho de igual valor e a desnecessidade de reclamante e paradigma estarem a serviço do estabelecimento ao tempo da reclamação",
    "sumula-60-tst": f"verbete oficial da Súmula nº 60 do TST, {LIVRO}, segundo a qual o adicional noturno pago com habitualidade integra o salário para todos os efeitos e é devido também quanto às horas prorrogadas quando cumprida integralmente a jornada no período noturno",
    "sumula-80-tst": f"verbete oficial da Súmula nº 80 do TST, {LIVRO}, segundo a qual a eliminação da insalubridade mediante fornecimento de aparelhos protetores aprovados pelo órgão competente do Poder Executivo exclui a percepção do respectivo adicional",
    "sumula-85-tst": f"verbete oficial da Súmula nº 85 do TST, {LIVRO}, segundo a qual a compensação de jornada deve ser ajustada por acordo individual escrito, acordo coletivo ou convenção coletiva, sendo válido o acordo individual salvo norma coletiva em sentido contrário",
}

# Correcao de 'name' cuja ementa oficial (evidence_grep) desmente o rotulo do
# pesquisador: o Decreto 10.060/2019 regulamenta a Lei 6.019/1974 (trabalho
# temporario), nao o Programa de Alimentacao do Trabalhador.
NAME_FIX = {
    "decreto-10060-2019": ("Decreto nº 10.060, de 14 de outubro de 2019 "
                           "(regulamenta a Lei nº 6.019/1974 — trabalho temporário)"),
}


def kind_for(url: str) -> str:
    if "planalto.gov.br/ccivil_03" in url:
        return "legal_act"
    if "tst.jus.br/documents" in url:
        return "binding_precedent"
    if url.endswith("/trabalho-e-emprego/pt-br/servicos"):
        return "official_service"
    if "gov.br/trabalho-e-emprego" in url:
        return "official_guidance"
    if "fgts.gov.br" in url:
        return "official_service"
    raise SystemExit(f"source_kind indefinido para {url}")


def load(name):
    path = os.path.join(STAGING, name)
    return [json.loads(line) for line in open(path, encoding="utf-8")
            if line.strip()]


def main() -> int:
    catalog = json.load(open(CATALOG, encoding="utf-8"))
    hints = catalog["source_hints"]

    def covered(hint):
        entry = hints.get(hint)
        return (isinstance(entry, dict) and
                bool(producer._canonical_official_source_url(entry.get("url"))))

    rows, order, skipped_covered = {}, [], []
    for record in load("part1.jsonl"):
        hint = record["slug_key"]
        if covered(hint):
            skipped_covered.append(hint)
            continue
        rows[hint] = {
            "hint": hint,
            "name": record["name"].strip(),
            "url": record["url"].strip(),
            "anchor_claim": record["anchor_claim"].strip(),
            "source_kind": record["source_kind"],
        }
        order.append(hint)

    reused_from_part1, dropped = [], []
    for record in load("part2.jsonl"):
        hint = record["key"]
        if hint in DROP:
            dropped.append(hint)
            continue
        if covered(hint):
            skipped_covered.append(hint)
            continue
        if hint in rows:                      # ja veio da part1 (mais rica)
            reused_from_part1.append(hint)
            continue
        claim = CLAIMS.get(hint)
        if not claim:
            raise SystemExit(f"anchor_claim autoral ausente para {hint}")
        rows[hint] = {
            "hint": hint,
            "name": NAME_FIX.get(hint, record["name"]).strip(),
            "url": record["url"].strip(),
            "anchor_claim": claim.strip(),
            "source_kind": kind_for(record["url"]),
        }
        order.append(hint)

    # Validacao local com os MESMOS predicados do gate (menos o probe HTTP).
    problems = []
    for hint in order:
        row = rows[hint]
        if set(row) != {"hint", "name", "url", "anchor_claim", "source_kind"}:
            problems.append((hint, "schema"))
        if producer._SOURCE_HINT_ID.fullmatch(hint) is None:
            problems.append((hint, "hint fora do slug canonico"))
        if row["source_kind"] not in producer._CATALOG_SOURCE_KINDS:
            problems.append((hint, "source_kind fora do enum"))
        for field in ("name", "url", "anchor_claim"):
            value = row[field]
            if (not isinstance(value, str) or not value or
                    value != value.strip()):
                problems.append((hint, f"{field} nao canonico"))
            if any(0xd800 <= ord(c) <= 0xdfff or
                   ord(c) in (0xfffd, 0x2028, 0x2029) for c in value):
                problems.append((hint, f"{field} com caractere proibido"))
        if not producer._canonical_official_source_url(row["url"]):
            problems.append((hint, "URL reprovada pelo gate canonico"))
        if len(row["anchor_claim"]) < 60:
            problems.append((hint, "anchor_claim curto demais"))
    if problems:
        for hint, why in problems:
            print("PROBLEMA", hint, why)
        return 1

    with open(OUT, "w", encoding="utf-8") as handle:
        for hint in sorted(order):
            handle.write(json.dumps(rows[hint], ensure_ascii=False,
                                    sort_keys=True) + "\n")
    print(f"escritas={len(order)} "
          f"skip_ja_no_catalogo={len(set(skipped_covered))} "
          f"dedup_part2_com_part1={len(reused_from_part1)} "
          f"dropadas_por_divergencia={dropped}")
    print("saida:", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
