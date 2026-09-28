#!/usr/bin/env python3
"""Correção jurídica/editorial determinística do shard finalizado 21."""

import hashlib
import json
import os
import tempfile

from tools.audit_v2_pages import body_word_count


PATH = "data/editorial/v2_pages/previdenciario-21.jsonl"
EXPECTED_SHA256 = "b13a917ff181e57b924f9ef6e524d57dc4d8c38c0802fce60bafa0d5dc885b9d"
VERIFIED_AT = "2026-07-10"


def source(url, name, claim):
    return {
        "url": url,
        "name": name,
        "anchor_claim": claim,
        "verified_at": VERIFIED_AT,
        "http_status": 200,
    }


with open(PATH, "rb") as handle:
    raw = handle.read()
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
    raise SystemExit("previdenciario-21 mudou após a revisão; releia antes de aplicar")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
if len(pages) != 4:
    raise SystemExit(f"estoque inesperado: {len(pages)} páginas")
by_id = {page["intent_id"]: page for page in pages}

page = by_id["prev-verbete-carta-de-concessao"]
page["sections"][0]["text"] = (
    "RMI é a renda mensal inicial: o valor apurado para o começo do benefício, antes dos "
    "reajustes posteriores. DIB é a data de início do benefício, usada para definir desde quando "
    "a prestação é devida. Ela não deve ser confundida com o início do prazo decadencial de uma "
    "revisão, que, em regra, parte do primeiro dia do mês seguinte ao recebimento da primeira "
    "prestação, conforme o art. 103 da Lei 8.213/1991.\n\n"
    "O período básico de cálculo reúne os salários de contribuição considerados na média. Para "
    "benefícios alcançados pela EC 103/2019, o art. 26 usa as contribuições desde julho de 1994, "
    "com regras próprias conforme a espécie e a data em que o direito foi adquirido. O coeficiente "
    "é o percentual aplicado à média para chegar à RMI; ele não é igual para aposentadoria, pensão "
    "e benefício por incapacidade."
)
page["sections"][1]["text"] = (
    "A carta mostra a forma de cálculo, mas a conferência completa pode exigir também a memória de "
    "cálculo e o processo administrativo. Compare as competências e remunerações usadas com o CNIS "
    "e com os documentos contemporâneos. Ausência, indicador ou valor divergente não significa "
    "automaticamente que o mês entrou como zero: o efeito depende da categoria, da competência e "
    "das regras de salário mínimo aplicáveis.\n\n"
    "Confira depois a espécie do benefício, a DIB, o coeficiente e o banco indicado. Se a conta não "
    "fechar, baixe a carta no serviço oficial e obtenha a cópia do processo antes de pedir revisão. "
    "Isso permite apontar a competência ou a fórmula exata, em vez de formular uma discordância "
    "genérica."
)
page["faq"][0]["a"] = (
    "Sim. Erro de dado ou de cálculo pode fundamentar revisão, mas a pretensão de rever o ato de "
    "concessão normalmente está sujeita ao prazo decadencial de dez anos do art. 103 da Lei 8.213/1991."
)
page["official_sources"] = [
    source(
        "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm#art29",
        "Lei 8.213/1991, art. 29",
        "fundamenta o salário de benefício usado na apuração da renda inicial",
    ),
    source(
        "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm#art103",
        "Lei 8.213/1991, art. 103",
        "define o termo inicial e o prazo geral de decadência da revisão do ato de concessão",
    ),
    source(
        "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art26",
        "EC 103/2019, art. 26",
        "define a média contributiva e os coeficientes aplicáveis aos benefícios alcançados pela reforma",
    ),
    source(
        "https://www.gov.br/pt-br/servicos/emitir-carta-de-concessao-de-beneficio",
        "Serviço Emitir Carta de Concessão de Benefício",
        "confirma os campos do documento e o download imediato pelo Meu INSS",
    ),
]

page = by_id["prev-acompanhar-processo-meu-inss"]
page["sections"][0]["text"] = (
    "No Meu INSS, entre com a conta gov.br, abra Consultar Pedidos, escolha o protocolo e use "
    "Detalhar. Essa tela reúne o andamento, as comunicações e os documentos do processo; quando a "
    "cópia já estiver disponível, também permite baixar o processo.\n\n"
    "Não dependa apenas de aviso no celular. A ciência e o prazo aplicável decorrem da comunicação "
    "registrada no processo. A carta de exigência informa o documento pedido e o prazo para resposta, "
    "normalmente de trinta dias, que deve ser conferido no próprio comunicado."
)
page["sections"][1]["text"] = (
    "Em análise indica que ainda não há decisão final. Em exigência significa que o INSS pediu "
    "informação ou documento; o art. 176 do Decreto 3.048/1999 impede que a documentação incompleta, "
    "sozinha, cause recusa imediata e prevê carta de exigência quando necessária.\n\n"
    "Se o prazo terminar sem o documento indispensável, o INSS pode arquivar o pedido sem análise de "
    "mérito; o § 3º do art. 176 afasta recurso ao CRPS contra esse arquivamento específico. Se houver "
    "elementos suficientes, o órgão deve decidir o direito. Quando houver indeferimento de mérito, o "
    "recurso ordinário ao CRPS tem prazo de trinta dias contado da ciência da decisão."
)
page["sections"][3]["text"] = (
    "Depois do deferimento, baixe a carta de concessão e consulte o extrato de pagamento. Confira "
    "espécie, DIB, RMI, banco e data prevista para o crédito. O deferimento na tela não substitui essa "
    "conferência, e eventual pagamento ausente deve ser tratado pelo serviço próprio ou pela Central 135."
)
page["official_sources"] = [
    source(
        "https://www.planalto.gov.br/ccivil_03/decreto/d3048compilado.htm#art176",
        "Decreto 3.048/1999, art. 176",
        "disciplina documentação incompleta, exigência, decisão e arquivamento administrativo",
    ),
    source(
        "https://www.gov.br/pt-br/servicos/solicitar-copia-de-processo-no-inss",
        "Serviço Solicitar Cópia de Processo no INSS",
        "confirma o caminho Consultar Pedidos, Detalhar e Baixar Processo no Meu INSS",
    ),
    source(
        "https://www.gov.br/inss/pt-br/direitos-e-deveres/recurso/duvidas-frequentes",
        "INSS: dúvidas frequentes sobre recurso ao CRPS",
        "informa o prazo de trinta dias para o recurso ordinário após a ciência da decisão",
    ),
]

page = by_id["prev-primeiro-pagamento-quando-cai"]
page["opening"] = (
    "A carta de concessão chegou, o status virou deferido, mas a data do crédito ainda precisa ser "
    "conferida. A Lei 8.213/1991 fixa um limite de até 45 dias após a apresentação da documentação "
    "necessária, enquanto a orientação operacional do INSS informa que o primeiro pagamento costuma "
    "ficar disponível em torno de quinze dias depois da concessão. O extrato de pagamento mostra o "
    "banco e o dia efetivo do caso concreto."
)
page["sections"][0]["heading"] = "O prazo legal e o calendário que realmente se aplica"
page["sections"][0]["text"] = (
    "O art. 41-A, § 5º, da Lei 8.213/1991 determina que o primeiro pagamento seja efetuado em até 45 "
    "dias após a apresentação da documentação necessária. Esse limite não transforma todo processo "
    "em pagamento no quadragésimo quinto dia: depois da concessão, o extrato individual informa a "
    "data prevista.\n\n"
    "Nos pagamentos mensais seguintes, a data depende do final do número do benefício e da renda. "
    "Quem recebe até um salário mínimo entra nos últimos cinco dias úteis do mês e nos cinco primeiros "
    "do mês seguinte; benefícios acima do piso são pagos nos cinco primeiros dias úteis do mês seguinte. "
    "Por isso não existe uma única data válida para todos."
)
page["sections"][1]["text"] = (
    "O crédito pode não aparecer na conta esperada porque o primeiro pagamento foi direcionado ao banco "
    "indicado na carta, porque a data do calendário ainda não chegou ou porque houve bloqueio cadastral. "
    "Consulte primeiro o Extrato de Pagamento: ele identifica banco, local e data.\n\n"
    "Se o extrato mostrar pagamento emitido e o valor não tiver sido recebido, use o serviço específico "
    "de pagamento não recebido ou a Central 135. Uma nova exigência antes da decisão pode ampliar a "
    "instrução do processo, mas não se deve afirmar genericamente que qualquer aviso posterior reinicia "
    "o prazo legal."
)
page["sections"][2]["text"] = (
    "Passados o dia indicado no extrato e o prazo legal sem crédito, guarde a carta, o extrato de "
    "pagamento e o protocolo da reclamação. A cobrança administrativa deve identificar o benefício e "
    "a competência não paga. Persistindo mora injustificada, esses documentos permitem avaliar medida "
    "judicial sem confundir atraso de análise com pagamento já emitido."
)
page["faq"][0]["a"] = (
    "Pode incluir parcelas desde a DIB quando essa data antecede a concessão, mas o termo inicial varia "
    "conforme a espécie, o requerimento e os fatos reconhecidos; confira a memória e o extrato do caso."
)
page["official_sources"] = [
    source(
        "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm#art41a",
        "Lei 8.213/1991, art. 41-A, § 5º",
        "fixa o limite de 45 dias para o primeiro pagamento após a documentação necessária",
    ),
    source(
        "https://www.gov.br/inss/pt-br/saiba-mais/seus-direitos-e-deveres/pagamento-de-beneficios",
        "INSS: Pagamento de Benefícios",
        "orienta sobre primeiro recebimento, carta, banco e consulta pelo extrato de pagamento",
    ),
    source(
        "https://www.gov.br/inss/pt-br/assuntos/noticias/calendario-de-pagamentos-do-inss-de-2026-esta-disponivel",
        "INSS: calendário de pagamentos de 2026",
        "publica as datas vigentes de 2026 por renda e final do benefício",
    ),
]

page = by_id["prev-transferir-beneficio-de-banco"]
page["meta_description"] = (
    "Saiba quando pedir a mudança diretamente ao banco e quando usar o Meu INSS para alterar o cartão "
    "de benefício ou a agência responsável."
)
page["opening"] = (
    "O beneficiário pode deixar o banco inicialmente indicado pelo INSS, mas há duas rotas diferentes. "
    "Para passar a receber em conta-corrente ou poupança própria, a solicitação é feita diretamente ao "
    "banco no qual a conta existe. O serviço Alterar Local ou Forma de Pagamento do Meu INSS serve para "
    "cartão de benefício e mudança da agência responsável; nele não é possível escolher o banco."
)
page["sections"][0]["heading"] = "Conta bancária e cartão de benefício não são a mesma mudança"
page["sections"][0]["text"] = (
    "O art. 166 do Decreto 3.048/1999 disciplina os meios de pagamento. Na operação atual, o primeiro "
    "crédito é encaminhado à instituição indicada na carta. Depois, quem possui conta-corrente ou "
    "poupança em instituição contratada pelo INSS pode pedir ao próprio banco que passe a receber ali.\n\n"
    "Já o serviço do Meu INSS permite voltar ou passar para cartão de benefício e alterar a agência do "
    "INSS responsável. A página oficial é expressa: nesse serviço não se escolhe banco."
)
page["sections"][1]["heading"] = "Como transferir para uma conta sem perder o primeiro crédito"
page["sections"][1]["text"] = (
    "Consulte a carta e o Extrato de Pagamento antes da mudança. Receba a primeira parcela no local "
    "indicado e, para levar os créditos seguintes a uma conta própria, solicite a alteração diretamente "
    "ao banco dessa conta. Confirme que a instituição mantém contrato com o INSS e aguarde a atualização "
    "no extrato antes de encerrar a forma anterior.\n\n"
    "Se a intenção for mudar a agência pagadora do cartão de benefício, use Alterar Local ou Forma de "
    "Pagamento no Meu INSS ou a Central 135. Não informe conta de terceiro como se fosse do titular."
)
page["sections"][2]["text"] = (
    "A transferência do pagamento não cancela empréstimo consignado nem muda a titularidade do benefício. "
    "Antes de qualquer alteração, confira descontos no extrato e guarde o protocolo. Se um crédito já "
    "emitido não aparecer, consulte o banco/local indicado naquele extrato e use o serviço de pagamento "
    "não recebido, em vez de repetir pedidos de troca.\n\n"
    "Não confunda essa mudança com portabilidade de empréstimo ou com abertura obrigatória de conta. O "
    "cartão de benefício permite receber sem conta-corrente, e a instituição pagadora deve oferecer o meio "
    "de saque previsto para essa modalidade. Se optar por conta própria, ela deve pertencer ao titular; "
    "senha e dados de acesso ao Meu INSS não devem ser entregues ao banco ou a intermediários."
)
page["faq"] = [
    {
        "q": "É obrigatório abrir conta-corrente no banco indicado pelo INSS?",
        "a": (
            "Não. O primeiro pagamento pode ser recebido no local indicado por cartão de benefício. A "
            "conta-corrente ou poupança é uma escolha posterior do titular, solicitada diretamente à "
            "instituição em que ele já mantém a conta."
        ),
    }
]
page["official_sources"] = [
    source(
        "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm#art166",
        "Decreto 3.048/1999, art. 166",
        "disciplina os meios bancários de pagamento dos benefícios do RGPS",
    ),
    source(
        "https://www.gov.br/pt-br/servicos/alterar-local-ou-forma-de-pagamento",
        "Serviço Alterar Local ou Forma de Pagamento",
        "distingue cartão de benefício da transferência para conta solicitada diretamente ao banco",
    ),
    source(
        "https://www.gov.br/inss/pt-br/saiba-mais/seus-direitos-e-deveres/pagamento-de-beneficios",
        "INSS: Pagamento de Benefícios",
        "orienta sobre primeiro crédito, banco indicado e transferência posterior para conta própria",
    ),
]

for page in pages:
    page["word_count"] = body_word_count(page)

directory = os.path.dirname(PATH)
fd, temporary = tempfile.mkstemp(prefix=".previdenciario-21.", suffix=".tmp", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, PATH)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
