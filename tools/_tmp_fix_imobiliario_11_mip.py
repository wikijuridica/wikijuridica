#!/usr/bin/env python3
"""Corrige cobertura MIP, cotitularidade e fontes oficiais específicas."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "74fde217c8a9e0a66893c8f971693b65b3b822a61aa1d9e3a96773dfaa680a32"
INTENT = "imob-seguro-mip-morte-invalidez"


def words(value):
    plain = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    total = len(words(page.get("opening", "")))
    for section in page.get("sections", []):
        total += len(words(section.get("heading", "")))
        total += len(words(section.get("text", "")))
    for item in page.get("faq", []):
        total += len(words(item.get("q", ""))) + len(words(item.get("a", "")))
    return total


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    matches = [page for page in pages if page.get("intent_id") == INTENT]
    if len(matches) != 1:
        raise SystemExit(f"intent encontrado {len(matches)} vez(es)")
    page = matches[0]

    page.update({
        "title": "Seguro MIP: cobertura por morte ou invalidez no financiamento",
        "meta_description": "Entenda quanto o seguro MIP paga no financiamento imobiliário, como funciona quando há mais de um segurado e como contestar uma negativa.",
        "h1": "Como o seguro MIP reduz o saldo após morte ou invalidez",
        "opening": (
            "O seguro habitacional ligado ao financiamento protege riscos de morte e invalidez permanente, "
            "na cobertura conhecida como MIP. A ocorrência do sinistro não apaga a dívida por uma regra única "
            "para todos os contratos: a seguradora paga ao financiador o saldo vincendo coberto, observado o "
            "percentual de responsabilidade de cada segurado na composição de renda e as condições da apólice. "
            "Por isso, a família precisa acionar o seguro e conferir o certificado antes de concluir que haverá "
            "quitação total."
        ),
        "sections": [
            {
                "heading": "O que a cobertura MIP paga ao financiador",
                "text": (
                    "A orientação oficial da SUSEP define MIP como morte e invalidez permanente. No sinistro "
                    "coberto, a indenização corresponde ao saldo devedor a vencer na data do evento, paga de uma "
                    "só vez ao estipulante ou financiador. O limite mensal acompanha o saldo depois das prestações "
                    "vencidas e amortizações já pagas; não é um capital livre entregue aos herdeiros.\n\n"
                    "A morte exige certidão e a invalidez permanente deve ser comprovada por declaração médica, "
                    "além dos documentos previstos nas condições do plano. O conceito coberto, a vigência, "
                    "eventual carência permitida e as exclusões precisam ser lidos no certificado individual ou "
                    "na apólice, sem substituir essa análise por uma promessa genérica de quitação."
                ),
            },
            {
                "heading": "Dois mutuários podem gerar quitação apenas parcial",
                "text": (
                    "Quando mais de uma pessoa compõe a renda para fins do seguro, a SUSEP informa que o pagamento "
                    "é proporcional ao percentual de responsabilidade do segurado que morreu ou se tornou inválido, "
                    "conforme a participação vigente na data do sinistro. Se uma pessoa respondia por 60 por cento, "
                    "a cobertura tende a liquidar essa parcela, permanecendo a dívida correspondente aos demais.\n\n"
                    "O MIP continua para os outros componentes sobre o saldo remanescente. O contrato e o certificado "
                    "devem mostrar os percentuais; usar apenas a divisão informal das parcelas da família pode levar "
                    "a uma expectativa errada sobre o valor que a seguradora deve pagar."
                ),
            },
            {
                "heading": "O consumidor pode escolher seguradora apta",
                "text": (
                    "O seguro habitacional é obrigatório, mas a própria SUSEP esclarece que o consumidor não precisa "
                    "contratá-lo necessariamente com o financiador: pode escolher outra seguradora autorizada e apta "
                    "a operar o produto. O custo efetivo do seguro habitacional, o CESH, deve ser apresentado para "
                    "permitir comparação das coberturas de MIP e danos físicos ao imóvel.\n\n"
                    "Depois da contratação, o número do processo SUSEP permite consultar as condições do produto. "
                    "Registro na autarquia significa submissão regulatória, não recomendação comercial nem garantia "
                    "de que todo evento futuro estará coberto."
                ),
            },
            {
                "heading": "Doença preexistente e a Súmula 609 do STJ",
                "text": (
                    "A Súmula 609 do STJ considera ilícita a recusa por doença preexistente quando a seguradora não "
                    "exigiu exames médicos prévios nem demonstrou má-fé do segurado. A regra impede presumir omissão "
                    "deliberada apenas porque a doença foi diagnosticada depois. Prontuários, perguntas feitas na "
                    "proposta e respostas efetivamente dadas mostram se havia conhecimento e informação relevante.\n\n"
                    "O artigo 768 do Código Civil trata da perda da garantia quando o segurado agrava intencionalmente "
                    "o risco, mas não transforma qualquer inexatidão em má-fé provada. Também é preciso distinguir "
                    "doença preexistente de evento já ocorrido antes do início da cobertura: o STJ já reconheceu que "
                    "um acidente de trabalho anterior à contratação não é risco futuro coberto pela mesma lógica."
                ),
            },
            {
                "heading": "Como contestar uma negativa sem parar o financiamento",
                "text": (
                    "Peça à seguradora a decisão completa, a cláusula aplicada, a cópia da proposta e a memória do "
                    "percentual segurado. Registre reclamação na ouvidoria e, se não houver solução, no "
                    "Consumidor.gov.br, canal que a SUSEP informa acompanhar. A reclamação administrativa não "
                    "suspende automaticamente parcelas nem impede a consolidação da garantia imobiliária.\n\n"
                    "Se houver risco concreto sobre o imóvel, a medida judicial pode discutir cobertura e tutela de "
                    "urgência, mas depende de probabilidade do direito e perigo de dano. Deixar de pagar por conta "
                    "própria pode criar mora adicional; banco, seguradora e mutuário devem receber comunicações "
                    "documentadas enquanto a controvérsia é tratada."
                ),
            },
            {
                "heading": "Documentos para acionar e revisar a cobertura",
                "text": (
                    "Reúna contrato de financiamento, certificado individual ou apólice, proposta, declaração "
                    "pessoal de saúde, demonstrativo do saldo e percentuais de composição de renda. Em caso de morte, "
                    "junte certidão e documentos pedidos pelo plano; em invalidez, laudos que indiquem caráter "
                    "permanente, causa e data do evento. A seguradora deve receber cópias legíveis com protocolo.\n\n"
                    "Para discutir preexistência, preserve prontuários anteriores e posteriores sem divulgar dados "
                    "além do necessário. Um advogado particular pode revisar negativa, cobertura e risco do contrato "
                    "em atendimento remoto, sem prometer quitação integral ou deferimento urgente."
                ),
            },
        ],
        "faq": [{
            "q": "Se um dos dois mutuários morrer, o MIP quita todo o saldo?",
            "a": (
                "Não necessariamente. Havendo mais de um segurado na composição de renda, a indenização é "
                "proporcional ao percentual de responsabilidade da pessoa atingida pelo sinistro; o restante do "
                "financiamento pode continuar com os demais."
            ),
        }],
        "official_sources": [
            {
                "url": "https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/seguros/seguro-habitacional",
                "name": "SUSEP, Seguro Habitacional",
                "anchor_claim": "obrigatoriedade, escolha da seguradora, limites do MIP e proporcionalidade entre segurados",
            },
            {
                "url": "https://arquivocidadao.stj.jus.br/index.php/sumula-609-2?sf_culture=pt_BR",
                "name": "STJ, Súmula 609",
                "anchor_claim": "recusa por doença preexistente exige exame prévio ou demonstração de má-fé",
            },
            {
                "url": "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20231215&formato=PDF&nreg=202301260530&salvar=false&seq=2387407&tipo=0",
                "name": "STJ, REsp 2.093.160/PR",
                "anchor_claim": "distinção entre doença preexistente e acidente ocorrido antes da contratação",
            },
            {
                "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art768",
                "name": "Código Civil, art. 768",
                "anchor_claim": "perda da garantia por agravamento intencional do risco",
            },
        ],
    })
    page["word_count"] = body_word_count(page)
    if not 700 <= page["word_count"] <= 1400:
        raise SystemExit(f"faixa inesperada: {page['word_count']}")

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-mip.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS falhou antes da promoção")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(f"MIP corrigido; words={page['word_count']}; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
