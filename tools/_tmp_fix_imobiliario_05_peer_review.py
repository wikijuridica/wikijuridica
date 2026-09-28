#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-05.jsonl")
EXPECTED_SHA256 = "4a3221827df48cef2e99c1f4dd9cede4fdf5d3edeef4620c14917b6798d48447"


def one(items, predicate, label):
    matches = [item for item in items if predicate(item)]
    if len(matches) != 1:
        raise SystemExit(f"expected one {label}, got {len(matches)}")
    return matches[0]


raw = PATH.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
by_intent = {page["intent_id"]: page for page in pages}

page = by_intent["imob-exclusividade-corretor-vendi-sozinho"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "STJ aplica a exclusividade conforme contrato e desempenho",
    "broker STJ section",
)
section["heading"] = "Precedente exige leitura do contrato e da prova"
section["text"] = (
    "No AgInt no AREsp 2.072.274, as instâncias concluíram que a venda resultou "
    "de diligência do proprietário e que o corretor não aproximou as partes. A "
    "Quarta Turma manteve o resultado porque rever contrato e fatos encontrava "
    "os limites das Súmulas 5 e 7. O julgamento não reescreve o artigo 726 nem "
    "cria regra abstrata contra toda exclusividade: mostra que vigência, atividade, "
    "inércia e resultado precisam ser provados no caso concreto."
)
source = one(
    page["official_sources"],
    lambda item: "202103285072" in item["url"],
    "old broker precedent",
)
source.update({
    "url": "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?dt_publicacao=18%2F08%2F2022&num_registro=202200429212",
    "name": "STJ, AgInt no AREsp 2.072.274/DF",
    "anchor_claim": "caso em que a venda decorreu da diligência do proprietário e a revisão da prova e do contrato esbarrou nas Súmulas 5 e 7",
})

page = by_intent["imob-divida-condominio-omitida-venda"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "Posse e ciência do condomínio podem influenciar o polo passivo",
    "condominium debt current-law section",
)
section["heading"] = "Tema 886 está sob revisão no Tema 1.349"
section["text"] = (
    "O Tema 886 relacionou posse e ciência inequívoca do condomínio à definição "
    "do polo passivo na promessa não registrada. Em 2025, porém, a Segunda Seção, "
    "no REsp 1.910.280, reconheceu legitimidade concorrente do proprietário registral "
    "e do comprador independentemente da ciência inequívoca. O Tema 1.349 foi "
    "afetado para revisar o Tema 886 e seguia sem julgamento na atualização oficial "
    "de 10 de fevereiro de 2026, com suspensão dos recursos abrangidos. Portanto, "
    "não se deve apresentar a exclusão do vendedor como solução definitiva; a "
    "responsabilidade perante o condomínio e o regresso contratual são planos distintos."
)
source = one(
    page["official_sources"],
    lambda item: "015512" in item["url"],
    "Tema 886 source",
)
source.update({
    "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1349&cod_tema_inicial=1349&novaConsulta=true&tipo_pesquisa=T",
    "name": "STJ, Temas 886 e 1.349",
    "anchor_claim": "registra a tese do Tema 886 e a revisão afetada no Tema 1.349, ainda sem julgamento na atualização oficial de 10/02/2026",
})
page["official_sources"].insert(2, {
    "url": "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2025/05052025-Segunda-Secao-confirma-que-vendedor-pode-responder-por-obrigacoes-do-imovel-posteriores-a-posse-do-comprador.aspx",
    "name": "STJ, REsp 1.910.280",
    "anchor_claim": "reconhece legitimidade concorrente de vendedor e comprador, independentemente da ciência do condomínio, no caso examinado pela Segunda Seção",
})

page = by_intent["imob-dupla-venda-mesmo-imovel"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "Promessa sem registro em regra não vence terceiro de boa-fé",
    "double-sale precedent section",
)
section["heading"] = "REsp 2.141.417 é limite de publicidade, não caso de dupla venda"
section["text"] = (
    "O REsp 2.141.417 tratou de promessa não registrada de imóvel comercial em "
    "confronto com terceiro de boa-fé que recebeu garantia hipotecária registrada "
    "e promoveu a penhora. A Súmula 308 não foi aplicada por não se tratar da "
    "hipótese residencial protegida por ela. O terceiro não era segundo comprador, "
    "e o precedente não tratou de segunda compra registrada; ele apenas ilustra por "
    "que a falta de publicidade da promessa pode impedir sua oposição a direito real "
    "de terceiro. Fraude consciente e aquisição posterior exigem análise própria."
)
source = one(
    page["official_sources"],
    lambda item: "202301383107" in item["url"],
    "REsp 2.141.417 source",
)
source["anchor_claim"] = (
    "inoponibilidade de promessa não registrada de imóvel comercial a terceiro de "
    "boa-fé titular de garantia hipotecária; não era caso de segunda compra"
)

page = by_intent["imob-arrematacao-dividas-anteriores"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "Tema 1.134 impede que o edital transfira IPTU anterior",
    "Tema 1.134 section",
)
section["text"] = (
    "No Tema Repetitivo 1.134, divulgado no Informativo 829, o STJ fixou que é "
    "inválida previsão de edital atribuindo ao arrematante débitos tributários "
    "anteriores à alienação, porque o artigo 130, parágrafo único, impõe a "
    "sub-rogação no preço. Houve modulação: a tese alcança editais divulgados depois "
    "da publicação da ata de julgamento, ressalvados pedidos administrativos e ações "
    "judiciais pendentes, aos quais se aplica de imediato. O entendimento trata de "
    "tributos e não migra automaticamente para cota condominial ou contrato privado."
)
source = one(
    page["official_sources"],
    lambda item: "021067" in item["url"],
    "Tema 1.134 source",
)
source["anchor_claim"] = (
    "invalidade da transferência editalícia de tributo anterior e modulação para "
    "editais posteriores à ata, ressalvados pedidos e ações pendentes"
)
faq = one(page["faq"], lambda item: "IPTU antigo" in item["q"], "Tema 1.134 FAQ")
faq["a"] = (
    "O Tema 1.134 afasta essa transferência dentro de sua modulação: editais "
    "divulgados depois da ata, além de pedidos administrativos e ações judiciais "
    "que já estavam pendentes."
)

page = by_intent["imob-imovel-alugado-penhorado-leilao"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "Os 90 dias do artigo 8 não se aplicam automaticamente",
    "auction tenancy article 8 section",
)
section["heading"] = "Artigo 8 também exige leitura específica na arrematação"
section["text"] = (
    "O artigo 8 da Lei 8.245/1991 permite ao adquirente denunciar a locação em seu "
    "campo próprio e concede noventa dias para desocupação, ressalvado contrato por "
    "prazo determinado com cláusula de vigência e averbação anterior. No Informativo "
    "288, sobre o EREsp 511.637, discutiu-se que adquirente não se limita ao "
    "proprietário registrado e que a averbação posterior à arrematação não preservava "
    "automaticamente a locação; os embargos de divergência não foram conhecidos. "
    "Esse precedente impede tanto prometer sempre noventa dias quanto declarar que "
    "o artigo 8 nunca alcança arrematação. Contrato, edital, matrícula e cronologia "
    "continuam decisivos."
)
page["official_sources"].append({
    "url": "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisarumaedicao&from=feed&livre=0288.cod.",
    "name": "STJ, Informativo 288, EREsp 511.637",
    "anchor_claim": "discute o adquirente do art. 8º após arrematação, a averbação tardia e registra que os embargos não foram conhecidos",
})

page = by_intent["imob-sublocacao-valor-maior"]
section = one(
    page["sections"],
    lambda item: item["heading"] == "Sublocação exige consentimento prévio e escrito",
    "sublocation article 13 section",
)
section["text"] = (
    "O artigo 13 exige consentimento prévio e escrito do locador para cessão, "
    "sublocação ou empréstimo do imóvel. Pelo parágrafo 2º, recebido o pedido escrito, "
    "o locador tem 30 dias para manifestar formalmente sua oposição. Não é silêncio "
    "genérico nem tolerância informal: o efeito legal depende de solicitação escrita "
    "específica, recebimento comprovado e ausência de oposição no prazo. A autorização "
    "deve identificar imóvel, extensão, duração e pessoas."
)
source = one(
    page["official_sources"],
    lambda item: "l8245.htm#art13" in item["url"],
    "article 13 source",
)
source["anchor_claim"] = (
    "consentimento prévio e escrito e prazo de 30 dias para oposição após pedido "
    "escrito específico"
)

for intent in (
        "imob-exclusividade-corretor-vendi-sozinho",
        "imob-divida-condominio-omitida-venda",
        "imob-dupla-venda-mesmo-imovel",
        "imob-arrematacao-dividas-anteriores",
        "imob-imovel-alugado-penhorado-leilao",
        "imob-sublocacao-valor-maior"):
    by_intent[intent]["word_count"] = body_word_count(by_intent[intent])

payload = "".join(
    json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
    for item in pages
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
