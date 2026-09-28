#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-06.jsonl")
EXPECTED_SHA256 = "3e0d190e33f2414f2f3b1268366e959f157120eaeda81b1707b8d855be205b24"


def source(page, url, name, anchor_claim):
    current = next((item for item in page["official_sources"] if item.get("url") == url), {})
    result = {"url": url, "name": name, "anchor_claim": anchor_claim}
    for field in ("verified_at", "http_status"):
        if field in current:
            result[field] = current[field]
    return result


def section(page, heading, text):
    for item in page["sections"]:
        if item["heading"] == heading:
            item["text"] = text
            return
    raise KeyError(f"{page['intent_id']}: section not found: {heading}")


def rename_section(page, old_heading, heading, text):
    for item in page["sections"]:
        if item["heading"] == old_heading:
            item["heading"] = heading
            item["text"] = text
            return
    raise KeyError(f"{page['intent_id']}: section not found: {old_heading}")


def faq(page, question, answer):
    for item in page["faq"]:
        if item["q"] == question:
            item["a"] = answer
            return
    raise KeyError(f"{page['intent_id']}: FAQ not found: {question}")


raw = PATH.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f"CAS mismatch for {PATH}: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
by_id = {page["intent_id"]: page for page in pages}
if len(pages) != 22 or len(by_id) != 22:
    raise SystemExit(f"unexpected shard cardinality: pages={len(pages)} unique={len(by_id)}")

law_51 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art51"
law_52 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art52"
law_54 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art54"
law_54a = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art54a"
law_56 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art56"
law_57 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art57"
law_59 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art59"
law_68 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art68"
law_71 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art71"
law_72 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art72"
law_75 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art75"
cc = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"


page = by_id["imob-acao-renovatoria-requisitos"]
section(page, "O contrato por escrito e o prazo mínimo de cinco anos",
        "O art. 51 separa duas exigências que não devem ser confundidas. Pelo inciso I, o contrato que se pretende renovar precisa ser escrito e ter prazo determinado. Pelo inciso II, o prazo desse contrato ou a soma dos prazos ininterruptos de contratos escritos deve alcançar cinco anos. Assim, um instrumento escrito de dois anos pode integrar a contagem, mas não basta sozinho; contratos sucessivos podem ser somados quando preservam a continuidade documental da locação.")
section(page, "Como reunir a prova documental antes de ajuizar",
        "O art. 71 exige mais do que uma cópia do contrato. A inicial deve provar os três requisitos do art. 51, o cumprimento exato do contrato em curso e a quitação dos tributos e taxas atribuídos ao locatário. Também precisa indicar com clareza as condições oferecidas para a renovação e, se houver fiança, identificar o fiador, demonstrar sua idoneidade atual e juntar sua aceitação, com autorização conjugal quando exigível. Cessionário ou sucessor ainda prova o título oponível ao proprietário. Organizar esses itens antes do prazo reduz o risco de uma falha processual difícil de corrigir depois.")
section(page, "O caminho antes de entrar com a ação",
        "A negociação escrita pode resolver prazo e aluguel sem processo, mas não interrompe a decadência. Se não houver acordo, a ação deve ser proposta dentro da janela do art. 51, § 5º. O art. 58 indica o foro da situação do imóvel, salvo foro de eleição válido no contrato; por isso, contrato e cláusula de competência precisam ser lidos antes do protocolo. A tentativa amigável não deve consumir os últimos dias da janela legal.")
section(page, "Quando a renovatória não prospera",
        "Além da falta de algum requisito, o locador pode alegar as matérias do art. 72: proposta abaixo do valor locativo real, proposta de terceiro em condições melhores ou uma das hipóteses do art. 52. Estas últimas abrangem transformação radical ou valorizadora do imóvel e uso próprio ou transferência de fundo de comércio nos limites legais. Cada defesa tem prova e consequência próprias; não existe uma autorização genérica para retomar apenas porque o proprietário prefere outro ocupante.")
page["official_sources"] = [
    source(page, law_51, "Lei 8.245/1991, art. 51", "separa contrato escrito e determinado, prazo agregado de cinco anos, mesmo ramo por três anos e janela decadencial"),
    source(page, law_71, "Lei 8.245/1991, art. 71", "lista os documentos e condições que devem instruir a ação renovatória"),
    source(page, law_72, "Lei 8.245/1991, art. 72", "delimita as matérias de fato da contestação e a prova da proposta de terceiro"),
    source(page, law_52, "Lei 8.245/1991, art. 52", "disciplina obras, uso próprio, shopping center e indenização pela não renovação"),
]


page = by_id["imob-renovatoria-prazo-decadencial"]
section(page, "O que acontece se o prazo passar sem ação ajuizada",
        "Perdida a janela, deixa de existir a pretensão à renovação compulsória daquele contrato. Isso não antecipa o término que ainda não chegou. No fim do prazo, o art. 56 faz cessar a locação não residencial; se o locatário ficar por mais de trinta dias sem oposição, ela se prorroga por prazo indeterminado. Só então o art. 57 permite denúncia escrita com trinta dias para desocupação. Uma renovação voluntária ainda pode ser negociada, mas já não pode ser imposta com base na janela perdida.")
page["official_sources"] = [
    source(page, law_51, "Lei 8.245/1991, art. 51, § 5º", "fixa o intervalo de um ano a seis meses antes do término para propor a renovatória"),
    source(page, law_56, "Lei 8.245/1991, art. 56", "disciplina o fim e a prorrogação da locação não residencial por prazo determinado"),
    source(page, law_57, "Lei 8.245/1991, art. 57", "exige denúncia escrita e concede trinta dias na locação não residencial indeterminada"),
]


page = by_id["imob-renovatoria-excecao-retomada"]
section(page, "A proposta de terceiro em condições melhores",
        "A proposta de terceiro está no art. 72, III. O locador deve juntar documento subscrito pelo proponente e por duas testemunhas, indicar claramente as condições e informar ramo diferente do explorado pelo locatário. Na réplica, o locatário pode aceitar essas condições para obter a renovação. Se a proposta prevalecer e a locação não for prorrogada, a sentença fixa a indenização do art. 75, devida solidariamente pelo locador e pelo proponente.")
section(page, "Reforma determinada pelo poder público e uso próprio",
        "O art. 52 dispensa a renovação quando uma determinação pública exigir transformação radical ou quando o proprietário comprovar modificação valorizadora nos termos legais. Também contempla uso próprio ou transferência de fundo de comércio existente há mais de um ano, controlado majoritariamente pelo locador, cônjuge, ascendente ou descendente. Em regra, esse novo uso não pode repetir o ramo do antigo locatário. A exceção de uso próprio não pode ser invocada pelo empreendedor para negar renovação de espaço em shopping center.")
section(page, "O que muda se a retomada for insincera",
        "Se, em três meses da entrega, o locador não der ao imóvel o destino afirmado ou não iniciar as obras declaradas, o art. 52, § 3º, prevê indenização pelos prejuízos e lucros cessantes ligados à mudança, perda do lugar e desvalorização do fundo de comércio. A lei oferece um marco objetivo; não basta falar em demora razoável sem confrontar a data da entrega e a providência efetivamente adotada.")
page["official_sources"] = [
    source(page, law_72, "Lei 8.245/1991, art. 72", "exige proposta escrita, duas testemunhas, ramo diverso e permite aceitação em réplica"),
    source(page, law_52, "Lei 8.245/1991, art. 52", "define obras, uso próprio, restrição no shopping e prazo de três meses para a destinação"),
    source(page, law_75, "Lei 8.245/1991, art. 75", "manda fixar na sentença a indenização solidária na proposta de terceiro"),
]


page = by_id["imob-renovatoria-retomada-insincera"]
section(page, "O que caracteriza a insinceridade da retomada",
        "O art. 52, § 3º, adota um marco objetivo para a locação comercial: se, no prazo de três meses da entrega do imóvel, o locador não der o destino alegado ou não iniciar as obras determinadas pelo poder público ou declaradas na defesa, nasce a hipótese legal de indenização. O ponto de partida é a entrega efetiva, que deve ser documentada. A análise não pode substituir os três meses por uma noção vaga de prazo razoável.")
section(page, "As hipóteses mais comuns de desvio",
        "A divergência pode aparecer quando o proprietário invoca uso próprio e entrega o espaço a terceiro, ou quando anuncia transformação relevante e nenhuma obra começa no trimestre legal. Também importa verificar a restrição do art. 52, § 1º, ao uso no mesmo ramo do antigo locatário, ressalvada a locação que envolvia o próprio fundo de comércio, instalações e pertences. Fotografias, anúncios e documentos empresariais ajudam a reconstruir a destinação real.")
section(page, "O que pode ser pedido em indenização",
        "A lei menciona ressarcimento dos prejuízos e dos lucros cessantes suportados com a mudança, a perda do lugar e a desvalorização do fundo de comércio. Não se presume o valor: despesas de transferência, queda de receita e impacto sobre o ponto precisam de prova e nexo com a não renovação. Benfeitorias ou outros danos só entram se houver fundamento próprio e demonstração concreta, evitando transformar a indenização em uma lista automática.")
section(page, "Quando o pedido de indenização esbarra em limites",
        "A falta de destinação ou de início das obras no trimestre legal é relevante, mas a defesa pode discutir força maior, data real da entrega, execução efetiva do projeto e nexo dos prejuízos. Se o destino foi cumprido no prazo e uma mudança posterior ocorreu por fato superveniente, é necessário examinar a cronologia e a prova, sem presumir fraude apenas pelo resultado posterior. A prescrição e o termo inicial da pretensão também devem ser avaliados no caso concreto.")
faq(page, "Preciso provar má-fé do locador desde o início do processo de retomada?",
    "A hipótese do art. 52, § 3º, parte do descumprimento objetivo da destinação ou do início das obras em três meses; ainda assim, o pedido exige prova da entrega, da conduta posterior e dos prejuízos reclamados.")
page["official_sources"] = [
    source(page, law_52, "Lei 8.245/1991, art. 52, § 3º", "fixa três meses da entrega e delimita prejuízos, lucros cessantes, mudança, perda do lugar e fundo de comércio"),
    source(page, law_72, "Lei 8.245/1991, art. 72, §§ 2º e 3º", "define as provas da proposta de terceiro e das obras alegadas na contestação"),
]


page = by_id["imob-fundo-comercio-indenizacao"]
section(page, "As hipóteses que geram direito à indenização",
        "Na renovatória, o art. 52, § 3º, prevê ressarcimento se a não renovação decorrer de proposta de terceiro em melhores condições ou se o locador não der o destino alegado nem iniciar as obras em três meses da entrega. Na proposta de terceiro, o art. 75 torna locador e proponente solidários. Fora desse desenho, a indenização depende de outra causa jurídica; a simples perda de um ponto sem direito à renovação não cria, sozinha, um pagamento automático.")
section(page, "Quando a indenização não é devida",
        "A inexistência dos pressupostos do art. 52, a destinação comprovadamente cumprida no prazo ou a falta de prova do dano podem afastar o pedido. O valor do negócio não substitui nexo causal. Em desapropriação, a jurisprudência trata o prejuízo do locatário em relação própria e exige demonstração do fundo atingido, sem confundir a indenização do ocupante com o preço do imóvel devido ao proprietário.")
section(page, "A farmácia desapropriada e o valor do fundo perdido",
        "O Informativo 131 do STJ, no REsp 406.502, reconheceu que o locatário comercial pode pedir indenização, inclusive pelo fundo de comércio, quando o imóvel locado é desapropriado, independentemente da relação entre proprietário e inquilino. Isso não dispensa prova econômica: a farmácia deve demonstrar o negócio existente, a perda causada pelo ato expropriatório e o valor dos elementos atingidos, normalmente por perícia contábil.")
page["official_sources"] = [
    source(page, cc + "#art1142", "Código Civil, art. 1.142", "define o estabelecimento como complexo de bens organizado para o exercício da empresa"),
    source(page, law_52, "Lei 8.245/1991, art. 52, § 3º", "delimita a indenização na proposta melhor e na destinação ou obra não cumprida em três meses"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D002932", "STJ, Informativo 131, REsp 406.502", "reconhece indenização própria do locatário comercial na desapropriação, inclusive pelo fundo comprovado"),
]


page = by_id["imob-luvas-locacao-comercial"]
section(page, "Luvas na contratação inicial: cobrança lícita",
        "No REsp 406.934, resumido no Informativo 128, o STJ distinguiu a contratação original da renovação: no início da locação, a corte entendeu não haver vedação legal à estipulação de luvas dentro da liberdade contratual. O precedente não autoriza cobrança oculta nem resolve qualquer vício de consentimento; ele responde à diferença temporal entre o primeiro contrato e a exigência feita para conservar uma locação já protegida.")
section(page, "Luvas na renovação: cobrança vedada",
        "O art. 45 torna nula a cláusula que afaste o direito à renovação do art. 51 ou imponha obrigação pecuniária para exercê-lo. Por isso, o pagamento que era admissível na contratação original não pode reaparecer como preço para o locatário manter o ponto mediante renovação legal. Aluguel de mercado e condições regulares do novo período continuam discutíveis; o que a lei veda é comprar de volta o próprio direito renovatório.")
section(page, "O que fazer diante de cobrança irregular",
        "A primeira providência é guardar a proposta, identificar quem exige o valor e separar a contratação original de uma renovação ou trespasse. Se a exigência condiciona a renovação, pode ser impugnada com base no art. 45 dentro da negociação ou da própria ação renovatória. Valores pagos a um antigo empresário pela venda do estabelecimento seguem outro regime e não devem ser rotulados automaticamente como luvas do locador.")
page["official_sources"] = [
    source(page, "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art45", "Lei 8.245/1991, art. 45", "anula obrigação pecuniária destinada a afastar ou condicionar o direito à renovação"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D002855", "STJ, Informativo 128, REsp 406.934", "distingue a ausência de vedação às luvas na contratação original da ilicitude na renovação"),
]


page = by_id["imob-renovatoria-soma-contratos"]
section(page, "Os requisitos para a soma valer",
        "O texto legal exige contratos escritos e prazos ininterruptos. A continuidade da ocupação ajuda a provar o histórico, mas não substitui os instrumentos; já a troca do proprietário não apaga automaticamente a locação que se transmitiu regularmente. Mudança de pessoa jurídica do locatário exige demonstrar cessão ou sucessão apta a preservar o direito, em vez de presumir que a mera semelhança do negócio mantém toda a sequência.")
section(page, "Quando a soma não é aceita",
        "Lacuna contratual, período verbal usado para completar os cinco anos ou mudança do ocupante sem título de cessão ou sucessão podem quebrar a prova do inciso II. A relevância de um intervalo e a identidade da relação são questões documentais, não uma regra matemática criada fora da lei. O REsp 1.323.410 confirma a accessio temporis, mas também limita a renovação compulsória ao prazo máximo de cinco anos.")
page["official_sources"] = [
    source(page, law_51, "Lei 8.245/1991, art. 51", "admite somar prazos ininterruptos de contratos escritos para alcançar cinco anos"),
    source(page, "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20131120&formato=HTML&nreg=201102195783&salvar=false&seq=1279536&tipo=0", "STJ, REsp 1.323.410", "reconhece a accessio temporis e delimita o prazo da renovação compulsória"),
]


page = by_id["imob-renovatoria-sublocatario"]
section(page, "A regra da sublocação total",
        "O art. 51, § 1º, é específico: na sublocação total do imóvel, somente o sublocatário pode exercer o direito à renovação, desde que cumpra os requisitos legais. Não se trata de ação conjunta facultativa com o locatário original. O pedido precisa demonstrar contratos escritos, prazo agregado de cinco anos e atividade no mesmo ramo por três anos, além da regularidade da sublocação perante o proprietário.")
section(page, "O que muda na sublocação parcial",
        "A sublocação parcial não pode ser descartada com a frase de que nunca admite renovatória. O parágrafo único do art. 71 disciplina expressamente a ação proposta pelo sublocatário do imóvel ou de parte dele e manda citar sublocador e locador como litisconsortes, salvo quando o prazo da locação originária ou renovada permitir ao sublocador renovar a sublocação. Se a ação direta for procedente na primeira hipótese, o proprietário fica obrigado à renovação. Área, contrato principal e prazo disponível precisam ser confrontados.")
faq(page, "Preciso incluir o locatário original na ação renovatória?",
    "O art. 71 manda citar o sublocador e o locador como litisconsortes na ação do sublocatário, ressalvando a hipótese em que o sublocador já dispõe de prazo suficiente para renovar a sublocação.")
page["official_sources"] = [
    source(page, law_51, "Lei 8.245/1991, art. 51, § 1º", "atribui somente ao sublocatário o exercício da renovatória na sublocação total"),
    source(page, law_71, "Lei 8.245/1991, art. 71, parágrafo único", "disciplina ação do sublocatário do imóvel ou de parte dele e o litisconsórcio com sublocador e locador"),
]


page = by_id["imob-mudanca-ramo-renovatoria"]
section(page, "O que conta como mudança relevante de ramo",
        "A lei não oferece uma tabela de CNAEs para definir o mesmo ramo. O exame considera a atividade efetivamente explorada e a continuidade da clientela protegida. Ampliar produtos compatíveis pode preservar o ramo; substituir uma papelaria por restaurante indica ruptura mais clara. Alterações híbridas exigem prova sobre atividade principal, comunicação ao público e licenças, sem presumir que qualquer ajuste cadastral zere o prazo ou que toda expansão o preserve.")
faq(page, "A mudança de razão social, sem alterar o ramo, afeta a contagem?",
    "Uma simples alteração do nome da mesma pessoa jurídica não muda o ramo. Se houver outra pessoa jurídica, cessão ou sucessão, porém, o autor da renovatória precisa provar o título que preserva o direito, conforme os arts. 51 e 71.")
page["official_sources"] = [
    source(page, law_51, "Lei 8.245/1991, art. 51, III e §§ 1º a 3º", "exige três anos no mesmo ramo e disciplina cessionários e sucessores"),
    source(page, law_71, "Lei 8.245/1991, art. 71", "exige prova dos requisitos e do título de cessão ou sucessão oponível ao proprietário"),
]


page = by_id["imob-renovatoria-novo-aluguel-pericia"]
section(page, "O aluguel provisório pedido pelo locador",
        "O art. 72, § 4º, permite ao locador ou sublocador pedir na contestação aluguel provisório a partir do primeiro mês do período renovando. O pedido precisa vir acompanhado de elementos hábeis para aferir o justo valor e está sujeito ao limite legal de oitenta por cento do valor pedido. A decisão provisória não antecipa automaticamente o resultado final.")
section(page, "A perícia de avaliação do imóvel",
        "A perícia pode esclarecer metragem, localização, estado e valores comparáveis, excluída a valorização trazida pelo locatário ao ponto ou lugar. Ela não dá ao juiz liberdade para escolher qualquer cifra. No REsp 1.815.632, divulgado na Edição Extraordinária 6, o STJ decidiu que a ação tem natureza dúplice e o valor fica delimitado pelo pedido do locatário e pela contraproposta do locador; não cabe decidir por equidade fora dessas balizas apenas porque o laudo apontou outro número.")
page["official_sources"] = [
    source(page, law_72, "Lei 8.245/1991, art. 72", "regula contraproposta, aluguel provisório e limite de oitenta por cento"),
    source(page, law_75.replace("#art75", "#art73"), "Lei 8.245/1991, art. 73", "manda executar nos autos e pagar de uma vez as diferenças vencidas"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D019194", "STJ, Edição Extraordinária 6, REsp 1.815.632", "impede fixação por equidade fora do pedido e da contraproposta na renovatória"),
]


page = by_id["imob-revisional-aluguel-comercial"]
section(page, "Como o processo apura o valor",
        "O art. 68 prevê aluguel provisório, se pedido, devido desde a citação. Na ação do locador, ele não pode exceder oitenta por cento do valor pretendido; na ação do locatário, não pode ficar abaixo de oitenta por cento do aluguel vigente. Se não houver conciliação, a contestação apresenta contraproposta e o juiz determina perícia quando necessária. O aluguel definitivo retroage à citação, e as diferenças seguem o art. 69.")
rename_section(page, "Quem pode pedir e quando", "O que entra na avaliação do imóvel",
               "A Corte Especial decidiu no EREsp 1.411.420 que benfeitorias e acessões feitas pelo locatário com autorização do locador podem integrar o cálculo do aluguel na revisional. Portanto, não é correto limitar a perícia ao imóvel como existia no primeiro dia do contrato. A autorização, a incorporação ao bem e o efeito patrimonial precisam ser provados; investimentos ligados apenas à atividade empresarial não se confundem automaticamente com valorização do imóvel.")
section(page, "Quando a revisional não é o caminho certo",
        "O art. 68, § 1º, impede a revisional enquanto pende prazo de desocupação legal, amigável ou judicial. A proximidade do término também pode tornar a renovatória mais adequada para discutir o novo período. Revisional e renovatória têm objetos distintos e podem gerar questões de conexão conforme os períodos discutidos; não se deve afirmar, sem examinar datas e pedidos, que jamais podem coexistir.")
faq(page, "A revisional e a renovatória podem ser discutidas ao mesmo tempo?",
    "Não há resposta abstrata única. Elas tratam, em regra, de períodos e pedidos diferentes; datas, conexão, eventual prazo de desocupação e risco de decisões incompatíveis precisam ser examinados no caso concreto.")
page["official_sources"] = [
    source(page, "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art19", "Lei 8.245/1991, art. 19", "autoriza revisão após três anos do contrato ou do último acordo de valor"),
    source(page, law_68, "Lei 8.245/1991, arts. 68 e 69", "disciplina aluguel provisório, perícia, impedimentos e retroação do valor"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D017766", "STJ, Informativo 678, EREsp 1.411.420", "inclui no cálculo benfeitorias e acessões autorizadas feitas pelo locatário"),
]


page = by_id["imob-despejo-comercial-diferencas"]
section(page, "As liminares específicas do despejo comercial",
        "O art. 59, § 1º, VIII, admite liminar de desocupação em quinze dias, com caução equivalente a três meses de aluguel, quando a ação se funda exclusivamente no término da locação não residencial. Há uma janela importante: a ação deve ser proposta em até trinta dias do termo do contrato ou do cumprimento da notificação que comunicou a retomada. Fora desse intervalo, pode haver despejo pelo rito aplicável, mas não se presume essa liminar específica.")
section(page, "Quando o despejo comercial encontra resistência do lojista",
        "Uma renovatória tempestiva pode sustentar a permanência, mas sua existência, requisitos e partes precisam ser demonstrados; não basta alegar intenção de renovar. Também podem existir discussão sobre prorrogação, validade da denúncia, fundamento exclusivo, caução e observância da janela do art. 59, VIII. Em falta de pagamento, entram as regras próprias dos arts. 59, IX, e 62, que não devem ser misturadas ao simples término comercial.")
page["official_sources"] = [
    source(page, law_56, "Lei 8.245/1991, art. 56", "rege término e prorrogação da locação não residencial determinada"),
    source(page, law_57, "Lei 8.245/1991, art. 57", "rege denúncia escrita e desocupação em trinta dias na locação indeterminada"),
    source(page, law_59, "Lei 8.245/1991, art. 59, § 1º, VIII", "exige caução, fundamento exclusivo e ação em até trinta dias para a liminar comercial"),
]


page = by_id["imob-ponto-comercial-verbete"]
page["official_sources"] = [
    source(page, cc + "#art1142", "Código Civil, art. 1.142", "define o estabelecimento como complexo organizado de bens da empresa"),
    source(page, law_51, "Lei 8.245/1991, art. 51", "protege a continuidade do ponto mediante renovatória quando os requisitos são cumpridos"),
]


page = by_id["imob-res-sperata-verbete"]
page["opening"] = "Res sperata é a prestação ligada à fase de implantação de um shopping center, normalmente ajustada antes da conclusão do empreendimento. Ela remunera a atividade de organização, planejamento e reserva de localização prometida ao futuro lojista; não é sinônimo de aluguel mensal depois da abertura nem de luvas cobradas para renovar uma locação existente. Como o nome não resolve o contrato, finalidade, período de cobrança e entregas prometidas precisam estar documentados."
section(page, "Por que existe essa cobrança pré-operacional",
        "A prestação costuma ser paga durante a construção para viabilizar planejamento, tenant mix, divulgação e a reserva de determinado espaço. O marco temporal nasce do contrato: não se deve dizer genericamente que ela substitui o aluguel até o shopping atingir fluxo razoável. Obra, inauguração, entrega da unidade e obrigações do empreendedor formam a cronologia relevante para conferir se a cobrança corresponde ao que foi prometido.")
section(page, "A base contratual da cobrança em shopping centers",
        "O art. 54 da Lei 8.245/1991 reconhece a liberdade contratual entre lojista e empreendedor, sem eliminar a boa-fé nem as vedações da própria lei. A res sperata precisa aparecer com causa, valor, duração e contrapartidas identificáveis. Dar outro nome a luvas de renovação ou a cobrança sem prestação correspondente não impede o controle do conteúdo real do negócio.")
section(page, "Como se diferencia de outras cobranças do shopping",
        "A res sperata se liga à organização e à reserva durante a implantação; o aluguel mínimo ou percentual remunera o uso da loja em operação; e luvas, no sentido examinado pelo STJ, dizem respeito ao ingresso no contrato original ou à cobrança vedada para renovação. No REsp 1.259.210, o litígio sobre lojas âncoras mostrou que o direito à restituição depende do inadimplemento das vantagens concretamente prometidas, e não apenas do rótulo empregado.")
section(page, "Pontos de atenção na negociação do contrato",
        "O lojista deve localizar o cronograma de obra, a data de entrega, as lojas âncoras ou demais condições anunciadas, as hipóteses de atraso e a regra de restituição. Também convém separar a res sperata de aluguel, fundo de promoção e despesas administrativas. Se o empreendimento entregue divergir do projeto contratado, documentos de comercialização e anexos técnicos ajudam a avaliar cumprimento, resolução e eventual restituição.")
page["official_sources"] = [
    source(page, law_54, "Lei 8.245/1991, art. 54", "estabelece liberdade contratual qualificada nas relações entre lojistas e shopping centers"),
    source(page, "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20120807&formato=PDF&nreg=201100619640&salvar=false&seq=1112338&tipo=0", "STJ, REsp 1.259.210", "examina restituição da res sperata diante do descumprimento de vantagens prometidas ao lojista"),
]


page = by_id["imob-locacao-shopping-regras"]
section(page, "As despesas que o empreendedor não pode cobrar",
        "O art. 54, § 1º, impede cobrar as despesas das alíneas a, b e d do art. 22: obras estruturais ou acréscimos de interesse integral, pintura de fachadas e esquadrias externas e indenizações trabalhistas ou previdenciárias por dispensas anteriores à locação. Também veda obras ou troca de equipamentos que modifiquem o projeto ou memorial do habite-se e obras de paisagismo nas áreas comuns. O contrato não pode transformar essas exclusões em despesa ordinária apenas mudando o nome da rubrica.")
section(page, "O papel do contrato na prática",
        "Aluguel mínimo e percentual, fundo de promoção, horários, auditoria e manutenção dependem do instrumento e dos anexos do empreendimento. Já o § 2º exige que despesas cobradas estejam previstas em orçamento, salvo urgência ou força maior demonstrada, e permite ao lojista ou à entidade de classe exigir comprovação a cada sessenta dias. Contrato, orçamento e prestação de contas devem ser conferidos juntos.")
faq(page, "O lojista pode se recusar a participar do fundo de promoção do shopping?",
    "A resposta depende da cláusula, da finalidade e da cobrança efetiva. A previsão contratual é relevante, mas não dispensa transparência, aderência ao pactuado e controle pelas vedações legais; não existe exigibilidade automática só porque a rubrica aparece no contrato.")
page["official_sources"] = [
    source(page, law_54, "Lei 8.245/1991, art. 54", "delimita liberdade contratual, despesas vedadas, orçamento e comprovação a cada sessenta dias"),
    source(page, "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art22", "Lei 8.245/1991, art. 22", "identifica as despesas extraordinárias referidas pelo art. 54, § 1º"),
]


page = by_id["imob-decimo-terceiro-aluguel-shopping"]
section(page, "A base legal que sustenta a cláusula",
        "No REsp 1.409.849, o STJ restabeleceu a cobrança do aluguel dobrado em dezembro porque ela estava livremente pactuada em contrato empresarial de shopping e não havia alteração superveniente demonstrada que justificasse afastá-la. O fundamento foi o art. 54, lido com a autonomia privada e a boa-fé. O precedente não cria um décimo terceiro aluguel legal para todo shopping: sem cláusula, não há como presumir a parcela; com vício ou mudança relevante, a controvérsia precisa ser examinada.")
section(page, "Quando a cobrança pode ser questionada",
        "A conferência começa pela redação original, pelos aditivos e pela base de cálculo. Cobrança em mês diferente, duplicação de rubrica não contratada ou aplicação sobre parcela que o texto não alcança pode ser impugnada. A revisão judicial de contrato empresarial é excepcional, mas não impossível; exige indicar o defeito concreto, em vez de sustentar que toda cobrança de dezembro é abusiva por natureza.")
page["official_sources"] = [
    source(page, law_54, "Lei 8.245/1991, art. 54", "reconhece a força das condições livremente pactuadas no contrato de shopping"),
    source(page, "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?dt=20160505&formato=PDF&nreg=201303420570&salvar=false&seq=56930107&tipo=51", "STJ, REsp 1.409.849", "reconhece no caso a validade do aluguel dobrado de dezembro livremente pactuado"),
]


page = by_id["imob-aluguel-percentual-faturamento"]
section(page, "A estrutura do aluguel mínimo mais percentual",
        "O contrato costuma comparar um mínimo mensal com um percentual do faturamento e cobrar a parcela que resultar superior, sem somar automaticamente as duas. O REsp 1.409.849 descreve esse arranjo como prática do contrato de shopping, mas a fórmula concreta continua sendo a assinada pelas partes. Percentual, piso, exclusões, estornos e vendas vinculadas à unidade precisam ser lidos no instrumento, não presumidos por costume do setor.")
section(page, "O dever de abertura de contas e fiscalização",
        "Auditoria de faturamento pode ser prevista para viabilizar a parcela variável, porém finalidade e acesso devem ser proporcionais ao cálculo contratado. O lojista deve saber quais documentos serão apresentados, quem terá acesso, por quanto tempo e como divergências serão contestadas. O art. 54 favorece o pacto empresarial, não um acesso ilimitado a qualquer dado sem relação com o aluguel.")
page["official_sources"] = [
    source(page, law_54, "Lei 8.245/1991, art. 54", "fundamenta as condições contratuais específicas da locação em shopping"),
    source(page, "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?dt=20160505&formato=PDF&nreg=201303420570&salvar=false&seq=56930107&tipo=51", "STJ, REsp 1.409.849", "descreve aluguel mínimo e percentual na estrutura econômica do contrato de shopping"),
]


page = by_id["imob-clausula-raio-shopping"]
section(page, "A base de validade dentro da liberdade contratual",
        "No REsp 1.254.428, resumido no Informativo 585, o STJ decidiu que a cláusula de raio em tese não é abusiva no estatuto de shopping center, pois pode proteger a organização e os interesses comuns do empreendimento. A expressão em tese é decisiva: o precedente não valida qualquer distância, duração, grupo econômico ou sanção sem leitura do contrato e do mercado afetado.")
section(page, "Quando a cláusula pode configurar ilícito concorrencial",
        "O exame do caso concreto considera alcance territorial, duração, atividades e marcas atingidas, poder de mercado e efeito real sobre a concorrência. Uma restrição proporcional pode cumprir função contratual; outra, ampla ou acumulada em vários empreendimentos, pode excedê-la. A Lei 12.529/2011 oferece parâmetros concorrenciais, mas a conclusão depende de fatos econômicos e não de um raio máximo inexistente na lei.")
faq(page, "A cláusula de raio vale também depois que o contrato termina?",
    "Só a redação não encerra a análise. Uma vigência residual expressa ainda precisa ser examinada quanto a duração, alcance, finalidade legítima e efeitos concorrenciais no caso concreto.")
page["official_sources"] = [
    source(page, "https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D%27015948%27", "STJ, Informativo 585, REsp 1.254.428", "afirma que a cláusula de raio em tese não é abusiva e explica sua função no shopping"),
    source(page, "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12529.htm", "Lei 12.529/2011", "fornece os parâmetros legais para avaliar efeitos anticoncorrenciais no caso concreto"),
]


page = by_id["imob-built-to-suit-verbete"]
section(page, "As duas cláusulas que tornam o built to suit atípico",
        "O § 1º do art. 54-A diz que a renúncia à revisão pode ser convencionada. Ela é facultativa e precisa constar do contrato; o modelo built to suit não elimina automaticamente a revisional. O § 2º permite multa de saída antecipada, mas fixa teto: a soma dos aluguéis restantes, isto é, dos aluguéis a receber até o termo final. Valor, fórmula e eventos de rescisão continuam dependentes da cláusula pactuada.")
section(page, "O contraponto para o locatário",
        "A empresa assume compromisso de longo prazo porque o imóvel foi adquirido, construído ou reformado para sua especificação. Se houver cláusula de renúncia, a revisão ordinária do aluguel fica afastada durante a vigência; se ela não existir, não deve ser inventada. A saída antecipada pode gerar multa elevada até o teto legal, o que exige comparar investimentos ainda não amortizados, prazo restante e hipóteses de inadimplemento antes da assinatura.")
page["official_sources"] = [
    source(page, law_54a, "Lei 8.245/1991, art. 54-A", "define o built to suit, torna facultativa a renúncia à revisão e limita a multa aos aluguéis a receber"),
    source(page, "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12744.htm", "Lei 12.744/2012", "incluiu o art. 54-A no regime das locações urbanas"),
]


page = by_id["imob-built-to-suit-rescisao-multa"]
rename_section(page, "Quando a multa integral pode ser afastada", "Quando a multa pode ser revista",
               "O teto do art. 54-A não significa que toda multa abaixo dele seja intocável. O art. 413 do Código Civil prevê redução equitativa quando a obrigação principal foi cumprida em parte ou a penalidade é manifestamente excessiva, consideradas natureza e finalidade do negócio. No Informativo 627, REsp 1.447.247, o STJ tratou essa regra como cogente. Aplicá-la ao built to suit não é automático: depende do caso concreto, da função econômica da multa, do período cumprido e dos investimentos não amortizados.")
faq(page, "A multa pode ser reduzida judicialmente mesmo estando dentro do teto legal?",
    "Pode haver discussão pelo art. 413 se houve cumprimento parcial ou excesso manifesto, mas a redução não é automática. O juiz examina finalidade do built to suit, investimento, utilidade do período cumprido e equilíbrio concreto.")
page["official_sources"] = [
    source(page, law_54a, "Lei 8.245/1991, art. 54-A, § 2º", "limita a multa convencionada aos aluguéis a receber até o termo final"),
    source(page, cc + "#art413", "Código Civil, art. 413", "prevê redução equitativa por cumprimento parcial ou penalidade manifestamente excessiva"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D%27016696%27", "STJ, Informativo 627, REsp 1.447.247", "reconhece o controle do art. 413 como norma de ordem pública, sem redução matemática automática"),
]


page = by_id["imob-trespasse-e-locacao"]
section(page, "O que caracteriza o trespasse",
        "Trespasse é a transferência do estabelecimento organizado. O art. 1.144 do Código Civil exige averbação no Registro Público de Empresas Mercantis e publicação para eficácia perante terceiros; isso não substitui a anuência locatícia. O art. 1.146 ainda faz o adquirente responder pelos débitos anteriores regularmente contabilizados e mantém o alienante solidariamente responsável por um ano nos marcos legais.")
section(page, "Por que a locação não segue automaticamente o negócio",
        "O art. 13 exige consentimento prévio e escrito para cessão da locação. No REsp 1.202.077, Informativo 465, o STJ confirmou que essa regra se aplica ao trespasse de locação comercial porque o locador escolheu a contraparte considerando capacidade e idoneidade. Publicar e averbar a venda do estabelecimento não impõe ao proprietário do imóvel um novo locatário.")
section(page, "Como reduzir o risco na negociação",
        "A anuência pode ser condição suspensiva do trespasse. O REsp 1.443.135 também exige leitura cuidadosa do § 2º do art. 13: após notificação escrita específica, a falta de oposição em trinta dias pode produzir consentimento no contexto examinado pelo STJ; simples demora ou ciência informal não bastam. Notificação, prova de recebimento, contrato principal e resposta devem integrar o dossiê da operação.")
faq(page, "O locador pode cobrar algo para autorizar a transferência do contrato?",
    "Não presuma que qualquer condição monetária seja automaticamente válida. É preciso examinar contrato, natureza da exigência e limites legais; a anuência não deve ser comprada sem identificar por escrito fundamento e contrapartida.")
faq(page, "O comprador do estabelecimento assume as dívidas do negócio automaticamente?",
    "O art. 1.146 atribui ao adquirente os débitos anteriores regularmente contabilizados e mantém o alienante solidariamente responsável por um ano nos marcos do dispositivo. Dívidas fiscais, trabalhistas e locatícias podem seguir regimes próprios.")
page["official_sources"] = [
    source(page, "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art13", "Lei 8.245/1991, art. 13", "exige consentimento escrito e disciplina notificação específica e oposição em trinta dias"),
    source(page, cc + "#art1144", "Código Civil, art. 1.144", "disciplina averbação e publicação do contrato de alienação do estabelecimento"),
    source(page, cc + "#art1146", "Código Civil, art. 1.146", "regula débitos contabilizados do adquirente e responsabilidade residual do alienante"),
    source(page, "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D012287", "STJ, Informativo 465, REsp 1.202.077", "confirma que a anuência do art. 13 é essencial no trespasse de locação comercial"),
    source(page, "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20180430&formato=PDF&nreg=201400616510&salvar=false&seq=1703168&tipo=0", "STJ, REsp 1.443.135", "qualifica o efeito do silêncio após notificação escrita específica da cessão"),
]


page = by_id["imob-denuncia-vazia-comercial"]
section(page, "O procedimento e o prazo de desocupação",
        "Pelo art. 57, o locador denuncia por escrito a locação não residencial já indeterminada e concede trinta dias para desocupação. Se o imóvel não for entregue, cabe despejo. A liminar do art. 59, § 1º, VIII, tem requisitos adicionais: ação fundada exclusivamente no término, caução de três aluguéis e propositura em até trinta dias do termo ou do cumprimento da notificação. Atendidos esses pontos, a ordem liminar prevê desocupação em quinze dias.")
section(page, "A diferença para quem tem direito à renovatória",
        "O direito à renovatória exige contrato escrito e determinado, prazo isolado ou somado de cinco anos, três anos no mesmo ramo e ação no intervalo legal. Não basta ter ocupado o ponto por cinco anos nem falar em renovação depois de perder a janela. Se a ação foi tempestiva e preenche os requisitos, ela oferece a via própria para discutir a continuidade; se não, a prorrogação indeterminada fica sujeita ao art. 57.")
page["official_sources"] = [
    source(page, law_56, "Lei 8.245/1991, art. 56", "faz cessar o prazo determinado e prorroga após mais de trinta dias sem oposição"),
    source(page, law_57, "Lei 8.245/1991, art. 57", "exige denúncia escrita e dá trinta dias para desocupação"),
    source(page, law_59, "Lei 8.245/1991, art. 59, § 1º, VIII", "condiciona a liminar de quinze dias à caução e à ação proposta em até trinta dias"),
]


for page in pages:
    page["word_count"] = body_word_count(page)

payload = "".join(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages).encode("utf-8")
fd, temporary = tempfile.mkstemp(prefix=PATH.name + ".", dir=PATH.parent)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if hashlib.sha256(PATH.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("CAS mismatch immediately before replace")
    os.replace(temporary, PATH)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)

print(f"updated {PATH}: pages={len(pages)} sha256={hashlib.sha256(payload).hexdigest()}")
