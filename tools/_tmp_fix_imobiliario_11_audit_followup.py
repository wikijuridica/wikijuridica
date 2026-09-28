#!/usr/bin/env python3
"""Fecha defeitos de audit e a omissão da carência legal em imobiliário-11."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "aa52813a83dd6e16ea72f9766a788c94becea514f39c1c80bb7a175a079e6d28"


def words(value):
    plain = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    values = [page.get("opening", "")]
    for section in page.get("sections", []):
        values.extend((section.get("heading", ""), section.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return sum(len(words(value)) for value in values)


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_id = {page["intent_id"]: page for page in pages}

    parei = by_id["imob-parei-pagar-financiamento"]
    parei["opening"] = (
        "O atraso não transfere o imóvel ao credor no dia seguinte, mas também não existe um número legal de "
        "parcelas que garanta espera. O contrato pode definir a carência depois da qual o credor pede a intimação "
        "pelo registro de imóveis; se não definir, a lei vigente fixa 15 dias. A partir daí, datas, espécie da "
        "operação e forma da comunicação determinam se ainda é possível manter o contrato ou se resta apenas "
        "adquirir o bem por preferência."
    )
    parei["sections"][0]["heading"] = "Carência contratual ou prazo legal antecedem a intimação"
    parei["sections"][0]["text"] = (
        "O art. 26 da Lei 9.514/1997 parte de dívida vencida e não paga, no todo ou em parte. O contrato pode "
        "estabelecer a carência para expedição da intimação; na omissão, o § 2º-A adota 15 dias. Uma única "
        "prestação pode, portanto, sustentar o início do rito depois desse intervalo. Esperar duas, três ou mais "
        "parcelas é política eventual do credor, não direito do mutuário.\n\n"
        "Antes do cartório, uma renegociação pode alterar vencimentos ou incorporar atrasos, mas só produz esse "
        "efeito se for formalizada. Conversas telefônicas e propostas ainda não aceitas não suspendem o procedimento "
        "nem substituem o pagamento previsto no contrato."
    )

    atraso = by_id["imob-atraso-quantas-parcelas-execucao"]
    atraso["sections"][2]["text"] = (
        "A requerimento do credor, o oficial do registro de imóveis intima o devedor e, se houver, o terceiro "
        "fiduciante. O § 1º concede então 15 dias. O montante reúne o boleto inadimplido e os vencimentos ocorridos "
        "até a quitação, com juros convencionais, penalidades, encargos do contrato e da lei, tributos, condomínio "
        "imputável ao imóvel e despesas de cobrança e intimação.\n\n"
        "Portanto, pagar apenas o boleto mais antigo pode não purgar a mora. Peça memória discriminada e recibo do "
        "valor efetivamente recebido no procedimento. Se o montante tiver erro, a contestação precisa apontar o "
        "lançamento e preservar o prazo, em vez de supor que a discussão o suspende."
    )

    sac = by_id["imob-tabela-sac-vs-price"]
    sac["sections"][3]["text"] = (
        "A controvérsia repetitiva 572 trata a presença de capitalização no método Price como questão probatória: "
        "contrato, execução do fluxo e, quando necessária, perícia devem demonstrar o que ocorreu. Não se presume a "
        "irregularidade apenas pelo nome do sistema. Para operações do SFH, a Lei 4.380/1964 recebeu o art. 15-A, "
        "que autoriza a contratação de capitalização em periodicidade mensal.\n\n"
        "Uma perícia séria identifica período, cláusula, taxa e lançamentos. Substituir a Price pelo SAC em uma "
        "calculadora, sem apontar a regra violada, não demonstra valor indevido."
    )

    revisao = by_id["imob-revisao-financiamento-imobiliario"]
    revisao["sections"][1]["text"] = (
        "O julgamento repetitivo dos Temas 27, 28 e 29 afastou a ideia de um teto bancário geral de 12 por cento ao "
        "ano e admitiu revisão dos juros apenas em situação excepcional, numa relação de consumo, quando as "
        "particularidades demonstrarem cabalmente a desvantagem exagerada. Não existe, portanto, percentual universal "
        "que transforme qualquer contrato em abusivo.\n\n"
        "A taxa média de operações equivalentes pode integrar a comparação, mas não deve virar multiplicador mecânico. "
        "Modalidade, data, prazo, risco e garantias precisam ser comparáveis, e a divergência deve ser conectada aos "
        "lançamentos do contrato examinado."
    )
    revisao["sections"][3]["text"] = (
        "Uma taxa efetiva anual maior do que doze vezes a taxa mensal não demonstra cobrança escondida automaticamente. "
        "A composição periódica faz com que a equivalência anual não seja uma multiplicação simples. A conferência "
        "útil verifica se o instrumento informou as taxas nominal e efetiva, a periodicidade e o custo total, e se a "
        "execução financeira corresponde ao que foi pactuado.\n\n"
        "Se a planilha do credor usa percentual diferente, muda a periodicidade ou inclui encargo sem previsão, a "
        "divergência deve ser quantificada mês a mês. A relação matemática correta não convalida falta de informação "
        "nem autoriza alterar unilateralmente a taxa."
    )
    keep_urls = {
        "https://www.planalto.gov.br/ccivil_03/leis/l4380.htm#art15a",
        "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&num_processo_classe=1061530&sg_classe=REsp&tipo_pesquisa=T",
        "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=572&cod_tema_inicial=572&novaConsulta=true&tipo_pesquisa=T",
        "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=972&cod_tema_inicial=972&novaConsulta=true&tipo_pesquisa=T",
        "https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/seguros/seguro-habitacional",
    }
    revisao["official_sources"] = [
        item for item in revisao["official_sources"] if item["url"] in keep_urls
    ]
    if len(revisao["official_sources"]) != 5:
        raise SystemExit("seleção revisional não resultou em cinco fontes")

    additions = {
        "imob-intimacao-edital-nulidade": (
            " Registre também se o endereço eletrônico contratual recebeu aviso antes do edital, quando aplicável; "
            "a redação vigente do art. 26 trata esse envio como dado próprio da tentativa editalícia."
        ),
        "imob-saldo-leilao-devolucao": (
            " Se o repasse foi parcial, confronte a data de cada crédito com o demonstrativo e separe a diferença "
            "principal da atualização reclamada, evitando cobrar duas vezes a mesma rubrica."
        ),
        "imob-desocupacao-pos-consolidacao": (
            " O acordo deve ainda dizer quem informará a entrega ao juízo e como será comprovada a imissão na posse, "
            "marco relevante para cessar a taxa de ocupação."
        ),
    }
    for intent_id, addition in additions.items():
        by_id[intent_id]["sections"][-1]["text"] += addition

    for intent_id in (
        "imob-alienacao-fiduciaria-verbete",
        "imob-execucao-hipoteca-diferenca",
        "imob-fgts-amortizar-financiamento",
        "imob-fgts-comprar-imovel-procedimento",
        "imob-portabilidade-financiamento",
        "imob-tabela-sac-vs-price",
    ):
        by_id[intent_id]["lane"] = "informativa"

    for page in pages:
        page["word_count"] = body_word_count(page)
        if page.get("skipped"):
            continue
        if not 350 <= page["word_count"] <= 1400:
            raise SystemExit(f"{page['intent_id']}: contagem inesperada {page['word_count']}")

    encoded = "".join(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(hashlib.sha256(encoded).hexdigest())
    for intent_id in (
        "imob-parei-pagar-financiamento",
        "imob-atraso-quantas-parcelas-execucao",
        "imob-tabela-sac-vs-price",
        "imob-revisao-financiamento-imobiliario",
        "imob-intimacao-edital-nulidade",
        "imob-saldo-leilao-devolucao",
        "imob-desocupacao-pos-consolidacao",
    ):
        print(intent_id, by_id[intent_id]["word_count"])


if __name__ == "__main__":
    main()
