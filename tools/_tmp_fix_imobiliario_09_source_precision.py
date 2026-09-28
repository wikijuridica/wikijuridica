#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path


PATH = Path("data/editorial/v2_pages/imobiliario-09.jsonl")
EXPECTED_SHA256 = "2698a920c250b7f042630891710ba27af039ba3445d56ac05aea4a948fb29006"


def source(url, name, anchor_claim):
    return {"url": url, "name": name, "anchor_claim": anchor_claim}


def split_source(page, original_url, original_name, original_claim, additions):
    matches = [item for item in page["official_sources"] if item["url"] == original_url]
    if len(matches) != 1:
        raise RuntimeError(f"{page['intent_id']}: expected one source {original_url}, got {len(matches)}")
    item = matches[0]
    item["name"] = original_name
    item["anchor_claim"] = original_claim
    page["official_sources"].extend(additions)
    if len(page["official_sources"]) > 5:
        raise RuntimeError(f"{page['intent_id']}: source cap exceeded")


payload = PATH.read_bytes()
actual = hashlib.sha256(payload).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in payload.decode().splitlines()]
by_intent = {page["intent_id"]: page for page in pages}

split_source(
    by_intent["imob-vicio-construtivo-acao"],
    "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art18",
    "Código de Defesa do Consumidor, art. 18",
    "alternativas do consumidor diante do vício de qualidade",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art26",
        "Código de Defesa do Consumidor, art. 26",
        "decadência, reclamação comprovada e vício oculto no regime de consumo",
    )],
)
split_source(
    by_intent["imob-vicio-oculto-imovel-usado"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art441",
    "Código Civil, art. 441",
    "requisitos do vício redibitório em contrato comutativo",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art442",
        "Código Civil, art. 442",
        "escolha entre redibição e abatimento do preço",
    )],
)
split_source(
    by_intent["imob-vicio-oculto-imovel-usado"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art445",
    "Código Civil, art. 445",
    "decadência para imóvel e descoberta posterior do vício",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art446",
        "Código Civil, art. 446",
        "efeito da garantia contratual sobre o curso do prazo",
    )],
)
split_source(
    by_intent["imob-metragem-planta-menor"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art500",
    "Código Civil, art. 500",
    "remédios da falta de área e presunção relativa de um vigésimo",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art501",
        "Código Civil, art. 501",
        "prazo decadencial e marco excepcional ligado à imissão na posse",
    )],
)
split_source(
    by_intent["imob-escritura-quando-obrigatoria"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art166",
    "Código Civil, art. 166, IV",
    "nulidade do negócio quando não observada a forma prescrita em lei",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art170",
        "Código Civil, art. 170",
        "conversão do negócio nulo quando preenchidos os requisitos de outro negócio",
    )],
)
split_source(
    by_intent["imob-registro-imovel-passo-a-passo"],
    "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art182",
    "Lei 6.015/1973, art. 182",
    "protocolo dos títulos e prioridade segundo a ordem de apresentação",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art205",
        "Lei 6.015/1973, art. 205",
        "cessação dos efeitos da prenotação nos marcos legais",
    )],
)
split_source(
    by_intent["imob-venda-sem-outorga-conjugal"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1647",
    "Código Civil, art. 1.647",
    "atos imobiliários sujeitos à outorga conjugal e exceção do regime de separação absoluta",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1648",
        "Código Civil, art. 1.648",
        "suprimento judicial por impossibilidade ou recusa injusta",
    )],
)
split_source(
    by_intent["imob-venda-sem-outorga-conjugal"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1649",
    "Código Civil, art. 1.649",
    "anulabilidade, prazo e confirmação posterior do ato",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1650",
        "Código Civil, art. 1.650",
        "legitimidade do cônjuge prejudicado e de seus herdeiros",
    )],
)
split_source(
    by_intent["imob-compra-imovel-leilao-ocupado"],
    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art901",
    "Código de Processo Civil, art. 901",
    "carta de arrematação e mandado de imissão na posse na alienação judicial",
    [source(
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art903",
        "Código de Processo Civil, art. 903",
        "estabilidade e hipóteses legais de invalidação da arrematação",
    )],
)
split_source(
    by_intent["imob-retrovenda-verbete"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art505",
    "Código Civil, art. 505",
    "prazo máximo, restituição do preço e despesas reembolsáveis no resgate",
    [
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art506",
            "Código Civil, art. 506",
            "depósito judicial diante da recusa e efeito do pagamento insuficiente",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art507",
            "Código Civil, art. 507",
            "cessão, transmissão e exercício do direito contra terceiro adquirente",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art508",
            "Código Civil, art. 508",
            "concorrência entre titulares do direito de retrato",
        ),
    ],
)
split_source(
    by_intent["imob-vendedor-nao-entrega-imovel"],
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art475",
    "Código Civil, art. 475",
    "cumprimento ou resolução do contrato diante do inadimplemento",
    [source(
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art397",
        "Código Civil, art. 397",
        "mora pelo vencimento de obrigação positiva, líquida e com termo",
    )],
)

encoded = "".join(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages).encode()
PATH.write_bytes(encoded)
print(hashlib.sha256(encoded).hexdigest())
