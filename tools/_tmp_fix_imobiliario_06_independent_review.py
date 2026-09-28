#!/usr/bin/env python3
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-06.jsonl")
EXPECTED_SHA256 = "94b2dd28a0cea921aa880c5b006f013e41ea11fb1014ad7a0afab14eb1d68f18"
TARGET_IDS = {
    "imob-renovatoria-prazo-decadencial",
    "imob-fundo-comercio-indenizacao",
    "imob-despejo-comercial-diferencas",
    "imob-luvas-locacao-comercial",
    "imob-renovatoria-novo-aluguel-pericia",
    "imob-renovatoria-sublocatario",
}


def replace_exact(value, old, new, label):
    if value.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence")
    return value.replace(old, new)


def section(page, heading):
    matches = [item for item in page["sections"] if item["heading"] == heading]
    if len(matches) != 1:
        raise SystemExit(f"{page['intent_id']}: missing or duplicate section {heading!r}")
    return matches[0]


def faq(page, question):
    matches = [item for item in page["faq"] if item["q"] == question]
    if len(matches) != 1:
        raise SystemExit(f"{page['intent_id']}: missing or duplicate FAQ {question!r}")
    return matches[0]


def add_source(page, source):
    url = source["url"]
    if any(item.get("url") == url for item in page["official_sources"]):
        raise SystemExit(f"{page['intent_id']}: source already present: {url}")
    page["official_sources"].append(source)
    if len(page["official_sources"]) > 5:
        raise SystemExit(f"{page['intent_id']}: more than five official sources")


raw = PATH.read_bytes()
actual_sha256 = hashlib.sha256(raw).hexdigest()
if actual_sha256 != EXPECTED_SHA256:
    raise SystemExit(
        f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual_sha256}"
    )

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
before = {page["intent_id"]: copy.deepcopy(page) for page in pages}
by_id = {page["intent_id"]: page for page in pages}
if not TARGET_IDS <= by_id.keys():
    raise SystemExit(f"missing target ids: {sorted(TARGET_IDS - by_id.keys())}")

page = by_id["imob-renovatoria-prazo-decadencial"]
page["opening"] = replace_exact(
    page["opening"],
    "A regra é que negociação, férias forenses ou dificuldade documental não suspendem nem interrompem o prazo; existem, porém, exceções legais estreitas no Código Civil, razão pela qual não é correto afirmar que a decadência jamais pode sofrer impedimento.",
    "A regra é que negociação, férias forenses ou dificuldade documental não suspendem nem interrompem o prazo. Isso não elimina a prorrogação do dies ad quem: se o vencimento cair em feriado ou recesso sem expediente, o REsp 55.991-DF admite o protocolo no primeiro dia útil seguinte. Existem também exceções legais estreitas no Código Civil, razão pela qual não é correto afirmar que a decadência jamais pode sofrer impedimento.",
    page["intent_id"],
)
calculation = section(page, "Como calcular a data limite na prática")
calculation["text"] += (
    " Se o último dia da janela cair em feriado ou recesso forense sem expediente, a prorrogação alcança apenas esse vencimento e permite o ajuizamento no primeiro dia útil seguinte. Ela não suspende a contagem durante todo o recesso, não reabre uma janela já perdida e não transforma negociação privada em causa de suspensão."
)
add_source(
    page,
    {
        "url": "https://www.stj.jus.br/docs_internet/revista/eletronica/stj-revista-eletronica-2003_165_capQuartaTurma.pdf",
        "name": "STJ, RSTJ 165, REsp 55.991-DF",
        "anchor_claim": "prorroga o vencimento da renovatória ao primeiro dia útil quando o termo final cai em feriado, sem suspender o prazo pela superveniência das férias forenses",
    },
)

page = by_id["imob-fundo-comercio-indenizacao"]
stock = faq(page, "A indenização pelo fundo de comércio inclui o estoque de mercadorias?")
stock["a"] = (
    "Não automaticamente. O estoque pode integrar o complexo de bens organizado que forma o estabelecimento, nos termos do art. 1.142 do Código Civil, mas não se confunde com o aviamento, que expressa a aptidão econômica da organização. Sua inclusão em uma reparação exige causa jurídica, dano efetivo e nexo próprios, com método que impeça contar o mesmo prejuízo novamente como estoque, aviamento, desvalorização do estabelecimento ou lucros cessantes."
)

page = by_id["imob-despejo-comercial-diferencas"]
ending = section(page, "O fim automático do contrato por prazo determinado")
ending["text"] = replace_exact(
    ending["text"],
    "No contrato não residencial por prazo determinado, o art. 56 estabelece que a locação cessa de pleno direito ao fim do prazo estipulado, independentemente de notificação ou aviso prévio.",
    "Na locação não residencial comum por prazo determinado, fora das destinações protegidas pelo art. 53, o art. 56 estabelece que a locação cessa de pleno direito ao fim do prazo estipulado, independentemente de notificação ou aviso prévio.",
    page["intent_id"],
)
protected = section(page, "Quando o despejo comercial encontra resistência do lojista")
protected["heading"] = "As destinações protegidas e os fundamentos restritos"
protected["text"] = (
    "Uma renovatória tempestiva pode sustentar a permanência, mas sua existência, requisitos e partes precisam ser demonstrados; não basta alegar intenção de renovar. Também pode haver discussão sobre prorrogação, validade da denúncia, fundamento exclusivo, caução e janela do art. 59, § 1º, VIII. Em falta de pagamento, entram as regras próprias dos arts. 59, § 1º, IX, e 62, que não devem ser misturadas ao simples término. O art. 53 protege imóveis usados por hospitais, unidades sanitárias oficiais, asilos, estabelecimentos de saúde e de ensino autorizados e fiscalizados pelo Poder Público e entidades religiosas devidamente registradas. Nesses casos, a rescisão fica restrita às hipóteses do art. 9º — acordo, infração legal ou contratual, falta de pagamento ou reparações urgentes determinadas pelo Poder Público nas condições legais — e ao pedido qualificado do inciso II do art. 53 para demolição, edificação licenciada ou reforma que aumente ao menos cinquenta por cento da área útil. O inciso II ainda exige a posição jurídica e registral descrita na lei para proprietário, promissário comprador ou promissário cessionário. Por isso, destino efetivo, autorização ou registro, fundamento invocado e documentos do imóvel precisam ser conferidos antes de tratar a locação como uma loja comum."
)
short_contract = faq(page, "O locador precisa justificar por que não quer renovar um contrato curto?")
short_contract["a"] = (
    "Na locação comercial comum, fora do art. 53, a duração insuficiente pode afastar a renovatória e o contrato determinado pode terminar pelo art. 56; se houver prorrogação indeterminada, aplica-se a denúncia escrita do art. 57. Essa resposta não vale automaticamente para hospital, unidade sanitária oficial, asilo, estabelecimento de saúde ou ensino autorizado e fiscalizado nem para entidade religiosa devidamente registrada, cujas hipóteses de rescisão são restritas pelo art. 53."
)

page = by_id["imob-luvas-locacao-comercial"]
terms = faq(page, "Luvas e fundo de comércio são a mesma coisa?")
terms["a"] = (
    "Não. Luvas são uma prestação ligada ao ingresso no contrato original ou, quando exigidas para renovar, uma cobrança vedada pelo art. 45. Também não existe equivalência terminológica universal entre fundo de comércio, estabelecimento e aviamento: no Informativo 485, sobre o REsp 907.014, o STJ associou fundo de comércio ao estabelecimento empresarial; na Edição Extraordinária 28, sobre o REsp 1.348.075, empregou a expressão fundo de comércio como aviamento. O contexto jurídico e econômico de cada cobrança deve ser identificado, sem presumir que esses conceitos designam o pagamento de entrada."
)
add_source(
    page,
    {
        "url": "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D012919",
        "name": "STJ, Informativo 485, REsp 907.014",
        "anchor_claim": "associa fundo de comércio ao estabelecimento empresarial no contexto de apuração de haveres",
    },
)
add_source(
    page,
    {
        "url": "https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisarumaedicao&livre=%270028E%27.cod.",
        "name": "STJ, Edição Extraordinária 28, REsp 1.348.075",
        "anchor_claim": "emprega fundo de comércio como aviamento no contexto específico de indenização por desapropriação",
    },
)

page = by_id["imob-renovatoria-novo-aluguel-pericia"]
proposal = section(page, "Como preparar a proposta de valor")
proposal["text"] = (
    "Reunir anúncios de imóveis semelhantes na região, contratos de locação de pontos comparáveis e dados técnicos de metragem, localização e estado ajuda a sustentar o valor locativo proposto já na petição inicial. O histórico de faturamento pode informar a capacidade econômica do negócio e a estratégia de negociação, mas não é comparável direto de aluguel nem substitui a avaliação do imóvel. Também não pode servir para reintroduzir no preço a valorização trazida pelo próprio locatário ao ponto ou lugar, que o art. 72, § 2º, manda excluir. Um advogado particular pode organizar comparáveis, contrato e laudo preliminar a distância antes do ajuizamento, para que o valor pedido seja coerente com a prova e com os limites da ação."
)
for source in page["official_sources"]:
    if source["url"] == "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art72":
        source["anchor_claim"] = (
            "regula contraproposta e aluguel provisório e exclui da perícia a valorização trazida pelo locatário ao ponto ou lugar"
        )
        break
else:
    raise SystemExit(f"{page['intent_id']}: missing art. 72 source")

page = by_id["imob-renovatoria-sublocatario"]
care = section(page, "Cuidados na contratação da sublocação")
care["text"] += (
    " O art. 13 exige consentimento prévio e escrito do locador para a cessão, a sublocação e o empréstimo do imóvel. A simples demora em se opor não permite presumir consentimento. O § 2º traz uma condição específica: quando o locatário notifica por escrito o locador sobre a ocorrência de uma dessas hipóteses, o locador dispõe de trinta dias para manifestar formalmente sua oposição. Não basta converter tolerância informal em autorização; contrato, teor da notificação, prova de entrega e cronologia precisam ser examinados em conjunto."
)
authorization = faq(page, "A sublocação sem autorização do locador é válida?")
authorization["a"] = (
    "O art. 13 exige consentimento prévio e escrito do locador, e o § 1º impede presumir esse consentimento apenas porque ele demorou a se opor. Se o locatário o notificar por escrito sobre a ocorrência da sublocação, o § 2º fixa trinta dias para oposição formal. A aplicação desse procedimento depende da notificação comprovada e das demais condições legais, por isso silêncio contratual ou tolerância informal não bastam, isoladamente, para afirmar regularidade."
)
add_source(
    page,
    {
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art13",
        "name": "Lei 8.245/1991, art. 13 e §§ 1º e 2º",
        "anchor_claim": "exige consentimento prévio e escrito e disciplina a notificação escrita com trinta dias para oposição formal do locador",
    },
)

for page in pages:
    page["word_count"] = body_word_count(page)
    if len(page.get("official_sources", [])) > 5:
        raise SystemExit(f"{page['intent_id']}: more than five official sources")

changed_ids = {
    page["intent_id"] for page in pages if page != before[page["intent_id"]]
}
if changed_ids != TARGET_IDS:
    raise SystemExit(
        f"unexpected changed ids: expected {sorted(TARGET_IDS)}, got {sorted(changed_ids)}"
    )

payload = "".join(
    json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
    for page in pages
).encode("utf-8")

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

print(hashlib.sha256(payload).hexdigest())
