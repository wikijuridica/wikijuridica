#!/usr/bin/env python3
"""Corrige a pagina sobre revisao de financiamento imobiliario."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "4f7c67dce58a483335e719b50bf8b4e9e56d8837cab10068fa0e895ed2a8537f"
INTENT = "imob-revisao-financiamento-imobiliario"


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
    previous_sources = {
        source.get("url"): source
        for source in page.get("official_sources", [])
        if source.get("url")
    }

    page.update({
        "title": "Revisão de financiamento imobiliário: teses e provas",
        "meta_description": (
            "Veja quando juros, Tabela Price, seguro e encargos podem justificar a revisão do financiamento "
            "imobiliário e por que não existe redução automática."
        ),
        "h1": "O que realmente pode ser revisto no financiamento imobiliário",
        "opening": (
            "Uma parcela alta não prova, sozinha, que o financiamento imobiliário contém cobrança ilegal. A "
            "análise precisa identificar o regime do contrato, a data, as taxas pactuadas, o sistema de "
            "amortização e o lançamento concreto que se pretende contestar. Só então é possível separar uma "
            "divergência demonstrável de promessas genéricas de reduzir a dívida por determinado percentual."
        ),
        "sections": [
            {
                "heading": "A primeira triagem identifica contrato, regime e cobrança",
                "text": (
                    "Financiamentos vinculados ao Sistema Financeiro da Habitação e operações do Sistema de "
                    "Financiamento Imobiliário não devem ser analisados como se fossem o mesmo contrato. A data "
                    "da assinatura também importa, porque alterações legislativas mudaram o tratamento da "
                    "capitalização. Contrato, proposta, aditivos e planilha de evolução do saldo mostram quais "
                    "regras foram pactuadas.\n\n"
                    "A revisão deve apontar uma cláusula ou lançamento: taxa aplicada diferente da contratada, "
                    "índice substituído, tarifa sem base no instrumento, seguro imposto sem liberdade de escolha "
                    "ou cálculo incompatível com o regime jurídico aplicável. A dificuldade financeira pode "
                    "justificar negociação, mas não substitui a prova de uma irregularidade revisional."
                ),
            },
            {
                "heading": "Juros acima de 12 por cento ao ano não bastam",
                "text": (
                    "A Súmula 382 do STJ afirma que juros remuneratórios superiores a 12 por cento ao ano não "
                    "indicam abusividade por si sós. No Tema 27, o tribunal admitiu a revisão apenas em situação "
                    "excepcional, numa relação de consumo, quando a desvantagem exagerada estiver cabalmente "
                    "demonstrada pelas particularidades do caso. Não existe, portanto, um percentual universal "
                    "que transforme qualquer contrato em abusivo.\n\n"
                    "A taxa média de operações equivalentes pode integrar a comparação, mas também não deve virar "
                    "um multiplicador mecânico. O Tema 1.378 do STJ, ainda afetado no portal oficial, discute "
                    "justamente se médias de mercado ou outros critérios previamente definidos bastam, sozinhos, "
                    "para aferir abusividade. A situação desse precedente precisa ser conferida quando o caso for "
                    "analisado."
                ),
            },
            {
                "heading": "Tabela Price ou SAC não resolvem a questão sem prova",
                "text": (
                    "Escolher a Tabela Price ou o SAC descreve uma forma de amortização; isso não prova, em "
                    "abstrato, que houve anatocismo nem que o contrato é válido em qualquer circunstância. No Tema "
                    "572, o STJ decidiu que verificar capitalização na Tabela Price é matéria de fato, dependente "
                    "da interpretação do contrato e, quando necessária, de prova técnica. O precedente destaca os "
                    "financiamentos do SFH anteriores à Lei 11.977/2009.\n\n"
                    "O art. 15-A da Lei 4.380/1964 passou a permitir pactuação de capitalização mensal nas operações "
                    "das entidades integrantes do SFH. Por isso, o perito não deve apenas trocar a tabela por outra: "
                    "precisa considerar a data, a cláusula de juros, a evolução do saldo e a legislação aplicável, "
                    "explicando qual diferença numérica decorre da irregularidade alegada."
                ),
            },
            {
                "heading": "Taxas mensal e anual devem ser lidas como foram contratadas",
                "text": (
                    "Uma taxa efetiva anual maior do que doze vezes a taxa mensal não demonstra cobrança escondida "
                    "automaticamente. Segundo a Súmula 541 do STJ, a previsão contratual de taxa anual superior ao "
                    "duodécuplo da mensal é suficiente, nos contratos bancários alcançados pelo entendimento, para "
                    "permitir a taxa efetiva anual contratada. A conferência útil compara o que consta no "
                    "instrumento com o que foi efetivamente lançado, sem confundir composição matemática com "
                    "encargo não informado."
                ),
            },
            {
                "heading": "Seguro pode ser obrigatório sem prender o consumidor à seguradora",
                "text": (
                    "O seguro habitacional cobre riscos próprios do financiamento, mas o Tema 972 do STJ impede "
                    "compelir o consumidor a contratar seguro com o banco ou com a seguradora indicada por ele. A "
                    "SUSEP também informa que o consumidor pode escolher seguradora autorizada e apta. O ponto "
                    "revisável é a restrição comprovada da escolha ou uma cobrança incompatível com o contrato, e "
                    "não a simples variação do prêmio ou a existência do seguro.\n\n"
                    "Um exemplo documentável seria a proposta limitar o seguro a uma empresa do grupo econômico e "
                    "o banco recusar, sem fundamento técnico, alternativa equivalente apresentada pelo mutuário. "
                    "Proposta, negativa escrita, certificado e composição do custo permitem confrontar o caso com "
                    "o precedente, sem prometer restituição antes dessa verificação."
                ),
            },
            {
                "heading": "A ação revisional não suspende parcelas automaticamente",
                "text": (
                    "A simples propositura da ação não impede a mora, conforme o Tema 29 e a Súmula 380 do STJ. O "
                    "Tema 28 distingue a hipótese em que se reconhece abusividade nos encargos do período de "
                    "normalidade, capaz de descaracterizar a mora. Já o Tema 972 esclarece que a abusividade de "
                    "encargos acessórios não produz esse efeito. Parar de pagar apenas porque a ação foi ajuizada "
                    "pode agravar a dívida e expor a garantia.\n\n"
                    "Pedido de tutela, depósito ou caução depende dos requisitos processuais e da prova disponível; "
                    "não há bloqueio automático da cobrança. Qualquer estratégia deve registrar a parcela "
                    "incontroversa, o risco de inadimplência e o estágio de eventual procedimento de consolidação "
                    "da propriedade."
                ),
            },
            {
                "heading": "Documentos e cálculo definem se há uma tese viável",
                "text": (
                    "Reúna contrato completo, proposta, aditivos, demonstrativo de evolução do saldo, boletos, "
                    "comprovantes, planilha do custo efetivo total, certificado do seguro e protocolos enviados ao "
                    "banco. Compare taxa, índice, amortização e encargos mês a mês. Uma memória de cálculo deve "
                    "explicar a premissa jurídica e quantificar a diferença, não apenas apresentar uma parcela "
                    "menor como resultado desejado.\n\n"
                    "Um advogado pode fazer a triagem documental e definir se é necessário contador ou perito. A "
                    "orientação responsável também considera negociação e portabilidade quando não há ilegalidade "
                    "demonstrável. Nenhum anúncio consegue prever redução, liminar ou economia antes de examinar o "
                    "instrumento e a prova do lançamento contestado."
                ),
            },
        ],
        "faq": [
            {
                "q": "A Tabela Price torna o financiamento ilegal?",
                "a": (
                    "Não de forma automática. O STJ trata a existência de capitalização no método como questão "
                    "fática, que pode exigir interpretação contratual e perícia, além da análise da data e do "
                    "regime jurídico do financiamento."
                ),
            },
            {
                "q": "Entrar com ação permite parar de pagar as parcelas?",
                "a": (
                    "Não. O ajuizamento isolado da ação revisional não impede a caracterização da mora; qualquer "
                    "medida sobre pagamento depende de decisão específica e dos requisitos do caso concreto."
                ),
            },
        ],
        "official_sources": [
            previous_sources["https://www.planalto.gov.br/ccivil_03/leis/l9514.htm"],
            previous_sources["https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art51"],
            {
                "url": "https://www.planalto.gov.br/ccivil_03/leis/l4380.htm#art15a",
                "name": "Lei 4.380/1964, art. 15-A",
                "anchor_claim": "permite pactuar capitalização mensal nas operações das entidades integrantes do SFH",
            },
            {
                "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&num_processo_classe=1061530&sg_classe=REsp&tipo_pesquisa=T",
                "name": "STJ, Temas 27, 28 e 29",
                "anchor_claim": "revisão excepcional dos juros e efeitos distintos sobre a mora",
            },
            {
                "url": "https://processo.stj.jus.br/SCON/sumstj/toc.jsp?sumula=382.num.",
                "name": "STJ, Súmula 382",
                "anchor_claim": "juros superiores a 12 por cento ao ano não indicam abusividade por si sós",
            },
            {
                "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=572&cod_tema_inicial=572&novaConsulta=true&tipo_pesquisa=T",
                "name": "STJ, Tema 572",
                "anchor_claim": "capitalização na Tabela Price é questão fática que pode exigir prova técnica",
            },
            {
                "url": "https://processo.stj.jus.br/SCON/sumstj/toc.jsp?sumula=541.num.",
                "name": "STJ, Súmula 541",
                "anchor_claim": "relação entre taxas contratadas mensal e efetiva anual",
            },
            {
                "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=972&cod_tema_inicial=972&novaConsulta=true&tipo_pesquisa=T",
                "name": "STJ, Tema 972",
                "anchor_claim": "liberdade de escolha da seguradora e efeito dos encargos acessórios sobre a mora",
            },
            {
                "url": "https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/seguros/seguro-habitacional",
                "name": "SUSEP, Seguro Habitacional",
                "anchor_claim": "seguro obrigatório e possibilidade de escolher seguradora autorizada e apta",
            },
            {
                "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&num_processo_classe=2227280&sg_classe=REsp&tipo_pesquisa=T",
                "name": "STJ, Tema 1.378",
                "anchor_claim": "controvérsia afetada sobre suficiência de taxas médias para aferir abusividade",
            },
        ],
        "internal_link_topics": [
            "SAC ou Price no financiamento",
            "seguro MIP e quitação por morte ou invalidez",
            "portabilidade do financiamento imobiliário",
        ],
        "lane": "comercial",
    })
    page["word_count"] = body_word_count(page)
    if not 700 <= page["word_count"] <= 1400:
        raise SystemExit(f"faixa inesperada: {page['word_count']}")

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-revisional.", dir=os.path.dirname(TARGET))
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

    print(f"revisional corrigida; words={page['word_count']}; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
