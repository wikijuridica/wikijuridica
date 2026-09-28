#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-06.jsonl")
EXPECTED_SHA256 = "0af3f891247a0d421ff04a6b8aa243db1db3eb70614be8e9558669f6ab8cb233"
INTERMEDIATE_SHA256 = "a16c261deb84de04f89a318e34820bd1dd175a356d0d7a7734175d16f28321a3"
REPHRASED_SHA256 = "5a9e632c0252592bf5bf5427bb5661d01a680eb12e00cdbaa9665f90edb6fe12"
GATE_FIXED_SHA256 = "a6cbc363f10d7426761b1f34997d02adfb651f33742e7b454e82ea44f5d0d4e9"
TARGET_ID = "imob-denuncia-vazia-comercial"
PROTECTED_SECTION_TEXT = (
    "A lista do art. 53 reúne hospitais e asilos; unidades sanitárias oficiais; "
    "estabelecimentos de saúde; estabelecimentos de ensino, desde que autorizados "
    "e fiscalizados pelo Poder Público; e entidades religiosas devidamente "
    "registradas. Para essas destinações, as hipóteses do art. 9º formam a primeira "
    "via de rescisão: mútuo acordo, infração legal ou contratual, inadimplência de aluguel "
    "e encargos ou reparações urgentes determinadas pelo Poder Público nas condições "
    "legais. A segunda via está no art. 53, II: o pedido qualificado para demolir, "
    "realizar edificação licenciada ou executar reforma cujo projeto aumente a área "
    "útil em, no mínimo, cinquenta por cento. O inciso II ainda exige a posição "
    "jurídica, possessória e registral ali descrita para proprietário, promissário "
    "comprador ou promissário cessionário. A proteção também não se presume pelo nome "
    "da instituição: no REsp 1.310.960, o STJ admitiu denúncia vazia quando a entidade "
    "de saúde usava o local apenas para tarefas administrativas, sem prestar ali a "
    "atividade-fim de saúde."
)
PROCEDURE_SECTION_TEXT = (
    "Quando o art. 57 é aplicável, o locador denuncia por escrito a locação não "
    "residencial já indeterminada e concede trinta dias para desocupação. Se o imóvel "
    "não for entregue, cabe despejo. A liminar do art. 59, § 1º, inciso VIII, tem "
    "requisitos adicionais: ação fundada exclusivamente no término, caução de três "
    "aluguéis e ação ajuizada em até trinta dias do termo ou do cumprimento da "
    "notificação. Atendidos esses pontos, a ordem liminar prevê desocupação em quinze "
    "dias. Esse mecanismo processual não corrige uma denúncia vazia materialmente "
    "incabível nem afasta a proteção do art. 53."
)


def replace_exact(value, old, new, label):
    if value.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence")
    return value.replace(old, new)


raw = PATH.read_bytes()
actual_sha256 = hashlib.sha256(raw).hexdigest()
if actual_sha256 not in {
    EXPECTED_SHA256, INTERMEDIATE_SHA256, REPHRASED_SHA256,
    GATE_FIXED_SHA256
}:
    raise SystemExit(
        f"CAS mismatch: expected {EXPECTED_SHA256}, {INTERMEDIATE_SHA256} or "
        f"{REPHRASED_SHA256} or {GATE_FIXED_SHA256}, "
        f"got {actual_sha256}"
    )

lines = raw.splitlines(keepends=True)
target_indexes = []
for index, line in enumerate(lines):
    if not line.strip():
        continue
    page = json.loads(line)
    if page.get("intent_id") == TARGET_ID:
        target_indexes.append(index)
if len(target_indexes) != 1:
    raise SystemExit(f"expected one {TARGET_ID} record, got {len(target_indexes)}")

target_index = target_indexes[0]
original_lines = list(lines)
page = json.loads(lines[target_index])

if actual_sha256 in {
    INTERMEDIATE_SHA256, REPHRASED_SHA256, GATE_FIXED_SHA256
}:
    protected = next(
        item
        for item in page["sections"]
        if item["heading"] == "Quando o art. 53 afasta a retomada imotivada"
    )
    if (actual_sha256 == INTERMEDIATE_SHA256 and
            "O art. 53 alcança imóveis usados por hospitais" not in protected["text"]):
        raise SystemExit("intermediate protected section does not match")
    if (actual_sha256 == REPHRASED_SHA256 and
            "as causas do art. 9º" not in protected["text"]):
        raise SystemExit("rephrased protected section does not match")
    if (actual_sha256 == GATE_FIXED_SHA256 and
            "as causas do art. 9º" not in protected["text"]):
        raise SystemExit("gate-fixed protected section does not match")
    protected["text"] = PROTECTED_SECTION_TEXT
    procedure = next(
        item
        for item in page["sections"]
        if item["heading"] == "O procedimento e o prazo de desocupação"
    )
    if (actual_sha256 == INTERMEDIATE_SHA256 and
            "art. 59, § 1º, VIII" not in procedure["text"]):
        raise SystemExit("intermediate procedure section does not match")
    if (actual_sha256 in {REPHRASED_SHA256, GATE_FIXED_SHA256} and
            "ajuizamento em até trinta dias" not in procedure["text"]):
        if "ação ajuizada em até trinta dias" not in procedure["text"]:
            raise SystemExit("rephrased procedure section does not match")
    procedure["text"] = PROCEDURE_SECTION_TEXT
    page["word_count"] = body_word_count(page)
    lines[target_index] = (
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    for index, (old_line, new_line) in enumerate(zip(original_lines, lines)):
        if index != target_index and old_line != new_line:
            raise SystemExit(f"non-target line changed at index {index}")
    payload = b"".join(lines)
    fd, temporary = tempfile.mkstemp(prefix=PATH.name + ".", dir=PATH.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(PATH.read_bytes()).hexdigest() != actual_sha256:
            raise SystemExit("CAS mismatch immediately before follow-up replace")
        os.replace(temporary, PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(hashlib.sha256(payload).hexdigest())
    raise SystemExit(0)

page["opening"] = (
    "Na locação não residencial comum, a denúncia vazia permite ao locador pedir o imóvel sem indicar uma causa concreta quando o contrato está por prazo indeterminado. Essa possibilidade não nasce automaticamente só porque o ocupante perdeu ou não preencheu a renovatória. Antes de aplicar o art. 57, é indispensável verificar a destinação efetiva do imóvel, pois o art. 53 retira determinadas atividades sociais do campo da retomada imotivada."
)

page["sections"][0]["text"] = (
    "Fora das destinações protegidas pelo art. 53, a denúncia vazia pode ser usada na locação comercial por prazo indeterminado. Isso ocorre quando o contrato comum já foi firmado sem termo final ou quando um contrato determinado termina e o locatário permanece por mais de trinta dias sem oposição do locador, situação em que o art. 56 presume a prorrogação por prazo indeterminado. A qualificação como comercial ou não residencial, sozinha, não resolve o enquadramento: o uso efetivo do imóvel precisa ser conferido antes de concluir que o art. 57 autoriza retomada sem motivo."
)
page["sections"].insert(
    1,
    {
        "heading": "Quando o art. 53 afasta a retomada imotivada",
        "text": PROTECTED_SECTION_TEXT,
    },
)

procedure = next(
    item
    for item in page["sections"]
    if item["heading"] == "O procedimento e o prazo de desocupação"
)
procedure["text"] = PROCEDURE_SECTION_TEXT

renewal = next(
    item
    for item in page["sections"]
    if item["heading"] == "A diferença para quem tem direito à renovatória"
)
renewal["text"] = (
    "O direito à renovatória exige contrato escrito e determinado, prazo isolado ou somado de cinco anos, três anos no mesmo ramo e ação no intervalo legal. Não basta ter ocupado o ponto por cinco anos nem falar em renovação depois de perder a janela. Se a ação foi tempestiva e preenche os requisitos, ela oferece a via própria para discutir a continuidade. A ausência desse direito, porém, não basta para autorizar denúncia vazia de imóvel abrangido pelo art. 53. Somente na locação comum, fora dessa proteção especial, a prorrogação indeterminada fica sujeita ao art. 57."
)

reaction = next(
    item
    for item in page["sections"]
    if item["heading"] == "O que fazer ao receber uma notificação de denúncia vazia"
)
reaction["text"] = (
    "Ao receber a notificação, o primeiro passo é verificar se o contrato realmente está por prazo indeterminado, se existe renovatória tempestiva e qual atividade é efetivamente exercida no imóvel. Hospital, unidade sanitária oficial, asilo, estabelecimento de saúde ou ensino precisa documentar autorização, fiscalização e uso no local; entidade religiosa deve conferir seu registro. Se o art. 53 incidir, também se examinam o fundamento do art. 9º ou do inciso II, os documentos registrais e a realidade da obra alegada. Só depois vêm forma do aviso, datas, caução e demais requisitos processuais. Advogado particular pode fazer essa conferência documental por canal digital antes de definir entrega negociada ou defesa cabível."
)

page["faq"][0]["a"] = (
    "Quando o art. 57 é aplicável, a própria denúncia escrita concede trinta dias para desocupação, sem aviso prévio adicional. Esse prazo não torna válida uma retomada imotivada contra imóvel protegido pelo art. 53, que depende de um dos fundamentos restritos previstos nos arts. 9º e 53, II."
)
page["faq"][1]["a"] = (
    "Sim. Além de vícios de notificação, prazo, caução ou liminar, a defesa pode demonstrar que o contrato não está indeterminado, que existe renovatória tempestiva ou que a destinação efetiva se enquadra no art. 53 e não há fundamento dos arts. 9º ou 53, II. A proteção especial exige prova de suas condições; por outro lado, o Informativo 547 do STJ afasta sua aplicação quando uma instituição de saúde usa o local apenas para tarefas administrativas."
)

for source in page["official_sources"]:
    if source["url"] == "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art57":
        source["anchor_claim"] = (
            "rege a denúncia escrita e os trinta dias na locação não residencial indeterminada quando não incide proteção legal especial"
        )
        break
else:
    raise SystemExit("missing art. 57 source")

page["official_sources"].extend(
    [
        {
            "url": "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art53",
            "name": "Lei 8.245/1991, art. 53",
            "anchor_claim": "restringe a rescisão das destinações sociais protegidas às hipóteses do art. 9º e do inciso II do art. 53",
        },
        {
            "url": "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D014963",
            "name": "STJ, Informativo 547, REsp 1.310.960",
            "anchor_claim": "distingue a atividade-fim de saúde protegida do espaço usado somente para tarefas administrativas",
        },
    ]
)
if len(page["official_sources"]) != 5:
    raise SystemExit(
        f"{TARGET_ID}: expected five official sources, got {len(page['official_sources'])}"
    )
if any(
    "verified_at" in source or "http_status" in source
    for source in page["official_sources"][-2:]
):
    raise SystemExit("new sources must not invent live verification metadata")

page["word_count"] = body_word_count(page)
lines[target_index] = (
    json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
).encode("utf-8")

for index, (old_line, new_line) in enumerate(zip(original_lines, lines)):
    if index != target_index and old_line != new_line:
        raise SystemExit(f"non-target line changed at index {index}")

payload = b"".join(lines)
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
