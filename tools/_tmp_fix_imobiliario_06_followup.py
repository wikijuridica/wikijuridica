#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-06.jsonl")
EXPECTED_SHA256 = "669cd948fcae39c4b68e8dc8881622bc5b786d0e5f0d6b021b4d6c5fdd9c0cf9"


def section(page, heading):
    for item in page["sections"]:
        if item["heading"] == heading:
            return item
    raise KeyError(f"{page['intent_id']}: {heading}")


raw = PATH.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")
pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
by_id = {page["intent_id"]: page for page in pages}

page = by_id["imob-fundo-comercio-indenizacao"]
section(page, "Como o valor é apurado")["text"] += (
    " A perícia deve evitar dupla contagem: faturamento não é, sozinho, o valor do fundo, e equipamentos removíveis não se transformam automaticamente em aviamento. O método precisa explicar período histórico, normalização de receitas, custos de reinstalação e tempo provável de recomposição da clientela. A parte contrária pode impugnar premissas, documentos e nexo, razão pela qual memória de cálculo e registros contábeis coerentes são tão importantes quanto o número final apresentado.")

page = by_id["imob-luvas-locacao-comercial"]
section(page, "Diferença entre luvas e outras cobranças do ponto")["text"] += (
    " A identificação também depende do beneficiário. Pagamento ao empreendedor pela primeira contratação, preço ao antigo empresário pelo estabelecimento e aluguel extraordinário previsto para uso do espaço têm causas distintas. Documento sem descrição da causa, valor quitado fora do contrato ou cobrança verbal na véspera da renovação aumentam o risco de requalificação. Recibo, proposta e correspondência devem registrar de modo consistente o que está sendo remunerado.")

page = by_id["imob-decimo-terceiro-aluguel-shopping"]
section(page, "Como conferir se a cobrança do seu contrato é regular")["text"] += (
    " Também é necessário verificar se o contrato chama de aluguel dúplice o dobro do mínimo, uma parcela adicional ou outra fórmula, pois essas expressões podem gerar resultados diferentes. Boletos e demonstrativos devem permitir reconstruir a base e o índice de reajuste. Se o empreendedor alterou a metodologia ao longo da relação, a comparação anual ajuda a localizar quando surgiu a divergência e qual documento teria autorizado a mudança.")

page = by_id["imob-clausula-raio-shopping"]
base = section(page, "A base de validade dentro da liberdade contratual")
base["text"] = base["text"].replace("REsp 1.254.428", "REsp 1.535.727")
section(page, "Como avaliar um plano de expansão sem violar o contrato")["text"] += (
    " A medição deve seguir o ponto de origem definido no instrumento e um método geográfico verificável; distância em linha reta e percurso viário não são equivalentes. Franquias, canais digitais e lojas temporárias também podem receber tratamento diferente. Antes de concluir que a nova unidade está proibida, a empresa precisa identificar sujeito obrigado, marca alcançada, atividade similar, território, prazo e sanção, além da possibilidade de autorização escrita para o endereço específico.")
for item in page["official_sources"]:
    if "CNOT%3D%27015948%27" in item.get("url", ""):
        item["name"] = "STJ, Informativo 585, REsp 1.535.727"

page = by_id["imob-built-to-suit-rescisao-multa"]
item = section(page, "Quando a multa pode ser revista")
item["text"] = item["text"].replace(
    "quando a obrigação principal foi cumprida em parte",
    "quando houve cumprimento parcial da obrigação principal")

page = by_id["imob-trespasse-e-locacao"]
section(page, "O risco de vender ou comprar sem essa anuência")["text"] += (
    " O risco não se limita à posse. Se o comprador começa a pagar aluguel sem formalizar sua posição, podem surgir disputas sobre quem responde pelos encargos, quem exerce direitos processuais e se as garantias do contrato anterior continuam. O contrato de trespasse deve atribuir consequências para a recusa do locador, prever restituição de valores e impedir que a transferência econômica seja tratada como concluída enquanto a permanência no imóvel ainda estiver juridicamente incerta.")

page = by_id["imob-denuncia-vazia-comercial"]
item = section(page, "O procedimento e o prazo de desocupação")
item["text"] = item["text"].replace(
    "A liminar do art. 59, § 1º, VIII, tem requisitos adicionais:",
    "A liminar do art. 59, § 1º, inciso VIII, tem requisitos adicionais:")
item["text"] = item["text"].replace(
    "propositura em até trinta dias",
    "ação ajuizada em até 30 dias")

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

print(hashlib.sha256(payload).hexdigest())
