#!/usr/bin/env python3
"""Revisao juridico-editorial integral e atomica do shard imobiliario-02."""

import hashlib
import importlib.util
import json
import os
import re
import tempfile
import unicodedata


_COMMON_ACCENT_PATH = os.path.join(os.path.dirname(__file__), "_tmp_fix_imobiliario_03_ptbr.py")
_COMMON_ACCENT_SPEC = importlib.util.spec_from_file_location(
    "_imobiliario_common_accents", _COMMON_ACCENT_PATH
)
if _COMMON_ACCENT_SPEC is None or _COMMON_ACCENT_SPEC.loader is None:
    raise RuntimeError("nao foi possivel carregar o restaurador PT-BR comum")
_COMMON_ACCENT_MODULE = importlib.util.module_from_spec(_COMMON_ACCENT_SPEC)
_COMMON_ACCENT_SPEC.loader.exec_module(_COMMON_ACCENT_MODULE)
restore_common_accents = _COMMON_ACCENT_MODULE.restore_accents


TARGET = "data/editorial/v2_pages/imobiliario-02.jsonl"
EXPECTED_SHA256 = "631ee7bb6f0cf1c767f5ffe2757879345e7af9a184453b6f64bc728e666377b8"

LEI = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
LAW_10192 = "https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10192.htm"
LAW_14905 = "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l14905.htm"
LAW_15040 = "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15040.htm"

SUSEP_FIANCA = (
    "https://www.gov.br/susep/pt-br/copy_of_planos-e-produtos/seguros/"
    "seguro-fianca-locaticia"
)
SUSEP_CAPITALIZACAO = (
    "https://www.gov.br/susep/pt-br/copy_of_planos-e-produtos/capitalizacao/"
    "perguntas-frequentes-1/capitalizacao"
)
SUSEP_CAPITALIZACAO_MANUAL = (
    "https://www.gov.br/susep/pt-br/arquivos/arquivos-planos-e-produtos/"
    "manual-tecnico-de-capitalizacao.pdf/%40%40download/file"
)
STJ_SUMULA_332 = "https://scon.stj.jus.br/SCON/sumstj/toc.jsp?sumula=332.num."
STJ_TESES_101 = (
    "https://stj.jus.br/internet_docs/jurisprudencia/jurisprudenciaemteses/"
    "Jurisprud%C3%AAncia%20em%20teses%20101%20-%20Da%20Fian%C3%A7a%20-%20I.pdf"
)
STJ_INFO_420 = (
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/"
    "?livre=%40CNOT%3D010820"
)
STJ_RESP_1745916 = (
    "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?"
    "dt_publicacao=22%2F02%2F2019&num_registro=201801289623"
)
STJ_RESP_439945 = (
    "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?"
    "dt_publicacao=07%2F10%2F2002&num_registro=200200718424"
)
STJ_INFO_660 = (
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/"
    "?acao=pesquisar&livre=%40CNOT%3D%27017357%27"
)
STJ_RESP_2233511 = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/"
    "24032026-Fianca-em-contrato-de-aluguel-nao-exclui-direito-do-locador-ao-penhor-legal.aspx"
)

LOCAL_PAIRS = """
aceitacao|aceitação
acessoria|acessória
acessorio|acessório
acrescimo|acréscimo
acumulacao|acumulação
ajuiza|ajuíza
alcancado|alcançado
alcancar|alcançar
alcancou|alcançou
alocacao|alocação
amigavel|amigável
antecipacao|antecipação
anuencia|anuência
anulacao|anulação
anulavel|anulável
anuncios|anúncios
aperfeicoa|aperfeiçoa
aplicaveis|aplicáveis
apolice|apólice
apreensao|apreensão
apresentacao|apresentação
aprovacao|aprovação
aproximacao|aproximação
apuracao|apuração
apuracoes|apurações
atencao|atenção
atribuido|atribuído
atualizacao|atualização
auditavel|auditável
avaliacao|avaliação
basica|básica
bonificacao|bonificação
bonus|bônus
botao|botão
cabivel|cabível
calculos|cálculos
capitalizacao|capitalização
caracterizacao|caracterização
carater|caráter
carencia|carência
cenario|cenário
certidoes|certidões
citacao|citação
coexistencia|coexistência
comparacoes|comparações
comparaveis|comparáveis
competencia|competência
composicao|composição
compreensivel|compreensível
comprobatorio|comprobatório
conciliacao|conciliação
concluida|concluída
conclusoes|conclusões
condenacao|condenação
conjuge|cônjuge
conjuges|cônjuges
consequencias|consequências
conservacao|conservação
construido|construído
contemporaneo|contemporâneo
contravencao|contravenção
controversia|controvérsia
correcao|correção
creditos|créditos
criterio|critério
declaracao|declaração
decretacao|decretação
demolicao|demolição
demonstracao|demonstração
denominacao|denominação
dependencia|dependência
depositos|depósitos
desapareca|desapareça
desapropriacao|desapropriação
desconfortavel|desconfortável
desequilibrio|desequilíbrio
desproporcao|desproporção
deterioracao|deterioração
diferencas|diferenças
discordancia|discordância
disponivel|disponível
dissolucao|dissolução
divergencia|divergência
economica|econômica
endereco|endereço
escritorio|escritório
estavel|estável
exoneracao|exoneração
expressao|expressão
extincao|extinção
falencia|falência
familia|família
ficticia|fictícia
fiscalizacao|fiscalização
fisicos|físicos
fixacao|fixação
fracao|fração
fracoes|frações
gravacao|gravação
habilitacao|habilitação
heranca|herança
hereditario|hereditário
homologacao|homologação
idonea|idônea
idoneas|idôneas
idoneo|idôneo
imobiliarias|imobiliárias
impoe|impõe
importacao|importação
imprevisiveis|imprevisíveis
imprevisivel|imprevisível
incendio|incêndio
incluidos|incluídos
indenizacoes|indenizações
indicacao|indicação
indice|índice
indices|índices
indispensaveis|indispensáveis
ineficacia|ineficácia
inequivoca|inequívoca
inflacao|inflação
informacao|informação
insercao|inserção
insolvencia|insolvência
instituicao|instituição
insuficiencia|insuficiência
inteligivel|inteligível
intencao|intenção
investigacao|investigação
juridico|jurídico
justificaveis|justificáveis
legitimos|legítimos
liberacao|liberação
liberatorio|liberatório
licenca|licença
localizacao|localização
lotacao|lotação
majoracao|majoração
matematica|matemática
maximo|máximo
meacao|meação
mecanica|mecânica
mes|mês
minimo|mínimo
monetaria|monetária
monetario|monetário
movimentacao|movimentação
multiplos|múltiplos
municipio|município
negativacao|negativação
negociacao|negociação
notificacoes|notificações
numeros|números
obito|óbito
ocasiao|ocasião
opcoes|opções
operacao|operação
orgao|órgão
periodos|períodos
peticao|petição
precos|preços
predio|prédio
prescricao|prescrição
proporcao|proporção
proprios|próprios
prorrogacao|prorrogação
provisao|provisão
provisorio|provisório
provisorios|provisórios
proximo|próximo
proximos|próximos
publicacao|publicação
punicao|punição
quantificacao|quantificação
questoes|questões
quitacao|quitação
recomeca|recomeça
reconciliacao|reconciliação
recuperacao|recuperação
reducao|redução
relacoes|relações
remocao|remoção
renegociacao|renegociação
renegociacoes|renegociações
renovatoria|renovatória
responsavel|responsável
restituido|restituído
reu|réu
reuna|reúna
revogacao|revogação
rogacao|rogação
rotulos|rótulos
sancao|sanção
sancoes|sanções
sentenca|sentença
simulacao|simulação
simultaneas|simultâneas
sinonimo|sinônimo
sobreposicao|sobreposição
temporaria|temporária
temporario|temporário
titulos|títulos
transicao|transição
trienio|triênio
uniao|união
unica|única
utilizacao|utilização
validacao|validação
valorizacao|valorização
variacao|variação
venia|vênia
verificacao|verificação
verificaveis|verificáveis
vigencia|vigência
"""
LOCAL_ACCENTS = dict(line.split("|", 1) for line in LOCAL_PAIRS.splitlines() if line)
LOCAL_TOKEN = re.compile(
    r"(?<![\w])(" + "|".join(
        sorted(map(re.escape, LOCAL_ACCENTS), key=len, reverse=True)
    ) + r")(?![\w])",
    re.IGNORECASE,
)


def restore_ptbr(value):
    value = restore_common_accents(value or "")

    def replace(match):
        original = match.group(0)
        corrected = LOCAL_ACCENTS[original.lower()]
        if original.isupper():
            return corrected.upper()
        if original[:1].isupper():
            return corrected[:1].upper() + corrected[1:]
        return corrected

    return LOCAL_TOKEN.sub(replace, value)


def section(heading, text):
    return {"heading": heading, "text": text}


def faq(question, answer):
    return {"q": question, "a": answer}


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


UPDATES = {
    "imob-substituicao-garantia-exigida": {
        "opening": (
            "Receber uma notificacao para trocar o fiador nao significa que a imobiliaria possa "
            "alterar a garantia por simples preferencia. A Lei do Inquilinato enumera fatos que "
            "autorizam a exigencia, fixa trinta dias para a apresentacao de garantia nova e reserva "
            "ao Judiciario qualquer ordem de desocupacao. Motivo, prova e data da notificacao "
            "precisam ser conferidos antes de responder."
        ),
        "sections": [
            section(
                "O rol do artigo 40 precisa ser aplicado ao fato comprovado",
                "O artigo 40 da Lei 8.245/1991 admite a substituicao em hipoteses como morte, "
                "ausencia, interdicao, recuperacao judicial, falencia ou insolvencia do fiador; "
                "exoneracao; desaparecimento do bem dado em garantia; desapropriacao ou alienacao "
                "do imovel locado; encerramento do fundo cujas quotas foram cedidas; e situacoes "
                "ligadas a prorrogacao e sub-rogacao previstas na propria lei. O pedido deve "
                "identificar qual inciso ocorreu e apresentar elemento que o sustente.\n\n"
                "A perda de renda do fiador, uma avaliacao cadastral mais rigorosa ou a troca de "
                "administradora nao equivalem automaticamente a insolvencia declarada. Tambem nao "
                "basta dizer que um imovel usado na analise inicial foi vendido: o inciso III fala "
                "em alienacao ou gravacao de todos os imoveis do fiador, ou em mudanca para outro "
                "municipio sem comunicacao ao locador."
            ),
            section(
                "O prazo legal para a nova garantia e de trinta dias",
                "Configurada uma das causas legais, o paragrafo unico do artigo 40 permite que o "
                "locador notifique o locatario para apresentar nova garantia no prazo de trinta "
                "dias. Esse prazo nao e uma pratica local nem um intervalo livremente inventado na "
                "carta. O recebimento deve ser documentado, pois marca a contagem e influencia a "
                "avaliacao de eventual inadimplemento.\n\n"
                "Pedir mais tempo pode ser util, mas a prorrogacao depende de concordancia que "
                "tambem deve ficar escrita. Enquanto negocia, o locatario pode reunir propostas de "
                "fianca, caucao, seguro-fianca ou cessao fiduciaria de quotas. A modalidade e a "
                "idoneidade precisam ser aceitas no contrato; o locatario nao impoe unilateralmente "
                "qualquer garantia, e o locador nao pode acumular duas modalidades contratuais."
            ),
            section(
                "A liminar do artigo 59 nao e despejo automatico",
                "Depois de vencido o prazo do artigo 40 sem garantia idonea, pode haver acao de "
                "despejo fundada na falta de substituicao. O artigo 59, paragrafo 1, inciso VII, "
                "admite liminar para desocupacao em quinze dias, mas exige processo, decisao "
                "judicial e caucao equivalente a tres meses de aluguel prestada pelo autor. A "
                "notificacao privada, sozinha, nao autoriza retirada forcada, troca de fechadura ou "
                "corte de servicos.\n\n"
                "A defesa pode discutir se o fato do artigo 40 realmente aconteceu, se a comunicacao "
                "foi recebida e se a garantia oferecida era idonea. Isso nao torna prudente ignorar "
                "a carta: a resposta deve enfrentar o inciso alegado e anexar documentos, sem "
                "confundir contestacao do motivo com permissao para deixar o contrato sem resposta."
            ),
            section(
                "Venda de um bem e mudanca do fiador exigem leitura precisa",
                "Certidoes atuais das matriculas ajudam quando se invoca o inciso III. Se o fiador "
                "possui outros imoveis, a venda isolada daquele usado como referencia cadastral nao "
                "prova a alienacao de todos os imoveis. Se a alegacao for mudanca, confira municipio, "
                "data e comunicacao anterior; mudar de endereco dentro do mesmo municipio nao e o "
                "fato descrito pelo dispositivo.\n\n"
                "Quando o proprio fiador pretende sair, e indispensavel distinguir fiança em prazo "
                "determinado, prorrogacao indeterminada e as hipoteses especiais da lei. A extensao "
                "residual de responsabilidade e o momento da substituicao variam conforme o motivo, "
                "por isso uma frase generica de exoneracao nao resolve toda situacao."
            ),
            section(
                "Contrato, notificacao e certidoes orientam a resposta",
                "Separe o contrato e eventuais aditivos, o instrumento de garantia, a notificacao "
                "com comprovante de recebimento, a resposta enviada e os documentos relacionados ao "
                "inciso citado. Certidoes imobiliarias, comprovante de domicilio ou ato de "
                "exoneracao so fazem sentido quando correspondem ao fundamento realmente usado.\n\n"
                "Uma analise juridica pode comparar esses registros, apontar a falta de enquadramento "
                "ou organizar uma proposta dentro dos trinta dias. O resultado depende da prova e "
                "da aceitacao da garantia; nao e possivel assegurar previamente que a notificacao "
                "sera anulada ou que determinada modalidade sera aceita."
            ),
        ],
        "faq": [
            faq(
                "O locador pode exigir outra garantia apenas porque prefere seguro-fianca?",
                "Nao por mera preferencia. E necessario enquadrar o fato em uma das hipoteses do artigo 40 e observar a notificacao de trinta dias."
            ),
            faq(
                "A carta da imobiliaria ja obriga a desocupacao em quinze dias?",
                "Nao. A liminar do artigo 59, paragrafo 1, VII, depende de acao, decisao judicial, vencimento do prazo do artigo 40 e caucao do autor equivalente a tres alugueis."
            ),
        ],
        "official_sources": [
            source(LEI + "#art40", "Lei 8.245/1991, art. 40", "causas de substituicao e prazo de trinta dias"),
            source(LEI + "#art59", "Lei 8.245/1991, art. 59, paragrafo 1, VII", "requisitos processuais da liminar por falta de nova garantia"),
            source(LEI + "#art37", "Lei 8.245/1991, art. 37", "modalidades contratuais e vedacao de cumular garantias"),
        ],
    },
    "imob-fiador-caucao-seguro-diferenca": {
        "opening": (
            "Fianca, caucao e seguro-fianca protegem o contrato por mecanismos diferentes. A "
            "comparacao util nao procura uma modalidade universalmente melhor: identifica quem "
            "imobiliza dinheiro, quem assume risco patrimonial, quais custos se repetem e como a "
            "garantia termina. A escolha depende de acordo e so uma modalidade contratual pode "
            "ser exigida na mesma locacao."
        ),
        "sections": [
            section(
                "Fianca compromete o patrimonio de uma terceira pessoa",
                "Na fianca, o garantidor assume por escrito obrigacoes delimitadas pelo contrato e "
                "pela lei. Beneficio de ordem, solidariedade, duracao, aditivos e prorrogacao devem "
                "ser lidos no instrumento. A garantia pode alcancar patrimonio relevante do fiador, "
                "inclusive com as excecoes legais aplicaveis ao bem de familia, e nao deve ser "
                "tratada como simples favor sem consequencias. O estado civil tambem importa porque "
                "determinados casamentos exigem autorizacao do outro conjuge."
            ),
            section(
                "Caucao pode recair sobre dinheiro, moveis ou imoveis",
                "O artigo 38 disciplina formas distintas de caucao. Em dinheiro, o limite e de tres "
                "meses de aluguel e o valor deve ser depositado em caderneta de poupanca, com as "
                "vantagens revertidas ao locatario no levantamento. Bens moveis exigem registro em "
                "cartorio de titulos e documentos; bens imoveis, averbacao na respectiva matricula. "
                "A caucao nao autoriza desconto sem demonstracao do debito no encerramento."
            ),
            section(
                "Seguro-fianca transfere o risco coberto, nao a divida do locatario",
                "A apolice tem o locador como segurado e o locatario como garantido. A cobertura "
                "basica envolve falta de pagamento de alugueis; encargos, contas ou danos dependem "
                "das coberturas efetivamente contratadas. O premio e custo do produto, nao saldo "
                "automaticamente devolvido. Se a seguradora indenizar o locador, o locatario nao "
                "fica liberado da obrigacao inadimplida e pode enfrentar cobranca nos limites "
                "juridicamente demonstrados."
            ),
            section(
                "A quarta modalidade legal e a cessao fiduciaria de quotas",
                "O inciso IV do artigo 37 menciona cessao fiduciaria de quotas de fundo de "
                "investimento. Ela nao se confunde com titulo de capitalizacao. Produtos de "
                "capitalizacao usados como instrumento de garantia possuem regulacao propria da "
                "SUSEP e precisam ser enquadrados e descritos corretamente, sem transformar o "
                "inciso IV em permissao generica para qualquer produto financeiro."
            ),
            section(
                "Custo, liquidez e encerramento devem constar da comparacao",
                "Compare desembolso inicial, pagamento recorrente, rendimento ou carregamento, "
                "documentos para liberacao, prazo de vigencia e alcance sobre encargos. Confira "
                "tambem quem pode substituir a garantia e em que situacoes. A Lei do Inquilinato "
                "veda mais de uma modalidade contratual no mesmo contrato; apresentar duas opcoes "
                "para negociacao e diferente de manter ambas simultaneamente."
            ),
        ],
        "faq": [
            faq("Qual garantia custa menos?", "Nao ha resposta unica. A caucao imobiliza capital, o seguro cobra premio e a fianca desloca risco patrimonial a terceiro; compare o custo total e a duracao."),
            faq("O locatario escolhe sozinho a modalidade?", "Nao. A garantia integra a negociacao do contrato. O locador pode avaliar sua idoneidade, mas nao pode exigir duas modalidades contratuais simultaneas."),
        ],
        "official_sources": [
            source(LEI + "#art37", "Lei 8.245/1991, art. 37", "quatro modalidades de garantia e vedacao de cumulo contratual"),
            source(LEI + "#art38", "Lei 8.245/1991, art. 38", "formas, registros e limite da caucao em dinheiro"),
            source(SUSEP_FIANCA, "SUSEP, Seguro Fianca Locaticia", "partes, coberturas, vigencia e permanencia da obrigacao do locatario"),
        ],
    },
    "imob-caucao-nao-devolvida": {
        "opening": (
            "A entrega das chaves nao transforma automaticamente toda caucao em valor livre para "
            "o locador nem garante devolucao integral sem acerto. E preciso apurar alugueis, "
            "encargos, danos comprovados e os rendimentos da poupanca. Sem demonstrativo e prova "
            "do desconto, a retencao pode ser contestada; com pendencias documentadas, o saldo deve "
            "ser calculado em vez de simplesmente ignorado."
        ),
        "sections": [
            section(
                "O saldo em poupanca pertence ao locatario no levantamento",
                "O artigo 38, paragrafo 2, determina que a caucao em dinheiro seja depositada em "
                "caderneta de poupanca e que todas as vantagens dela decorrentes revertam ao "
                "locatario quando a soma for levantada. Por isso, o ponto de partida nao e apenas o "
                "valor nominal pago anos antes. Extrato, data do deposito e evolucao do saldo "
                "permitem calcular o montante sujeito ao acerto final.\n\n"
                "Se o locador nao fez o deposito legal, a ausencia da conta nao deve beneficiar quem "
                "descumpriu a regra. A quantificacao do equivalente e de eventuais encargos depende "
                "das datas e da constituicao em mora, evitando aplicar juros ou indices em "
                "duplicidade sem base."
            ),
            section(
                "Descontos exigem vinculo com uma obrigacao da locacao",
                "Aluguel vencido, encargo atribuido ao locatario no contrato e dano que exceda o "
                "desgaste normal podem entrar no acerto se forem demonstrados. A vistoria de entrada "
                "e a de saida devem ser comparadas, com fotos, notas, orcamentos e oportunidade de "
                "contestacao. Cobrar pintura integral apenas porque o imovel foi usado nao substitui "
                "a prova de deterioracao imputavel ao ocupante.\n\n"
                "Tambem e preciso evitar dupla recuperacao. Um valor ja quitado, coberto por seguro "
                "ou cobrado de outra forma nao pode reaparecer sem reconciliacao. O demonstrativo "
                "deve separar principal, periodo, documento e saldo de cada item."
            ),
            section(
                "A notificacao deve pedir saldo, extrato e memoria de calculo",
                "Registre a data da entrega das chaves, identifique o valor originalmente pago e "
                "solicite o extrato da poupanca, a lista de descontos e os respectivos comprovantes. "
                "A Lei do Inquilinato nao fixa um numero geral de dias para toda devolucao de caucao; "
                "o contrato, o tempo necessario ao acerto e uma eventual mora precisam ser "
                "avaliados concretamente.\n\n"
                "Fixar prazo objetivo na notificacao ajuda a documentar a cobranca, mas nao cria uma "
                "vitoria automatica. Se houver parcela incontroversa, pedir seu pagamento imediato "
                "evita que uma divergencia pequena seja usada para reter todo o saldo."
            ),
            section(
                "Juizado ou procedimento comum dependem do caso",
                "Uma cobranca de valor determinado pode caber no juizado especial quando respeita "
                "competencia, valor e complexidade probatoria. Danos tecnicos controvertidos, prova "
                "pericial ou pedidos mais amplos podem exigir outro procedimento. Nao se deve "
                "prometer dispensa de advogado sem conferir o valor, a fase e as regras locais.\n\n"
                "Contrato, recibo da caucao, extratos, laudos, comprovante de chaves e mensagens "
                "formam a base da avaliacao. A pretensao pode envolver devolucao do saldo, "
                "atualizacao e consequencias da mora, sempre com calculo que evite sobreposicao."
            ),
            section(
                "Uma revisao documental separa retencao legitima de excesso",
                "Antes de aceitar um termo de quitacao, confira se ele informa o saldo e cada "
                "abatimento. Assinar declaracao ampla sem receber os documentos pode dificultar a "
                "discussao posterior. Por outro lado, negar toda pendencia apesar de laudos "
                "consistentes tambem enfraquece a cobranca.\n\n"
                "Orientacao juridica serve para qualificar a prova, calcular o pedido e escolher o "
                "procedimento. Nenhum texto geral permite garantir devolucao integral, prazo de "
                "pagamento ou indenizacao sem conhecer o estado do imovel e as obrigacoes abertas."
            ),
            section(
                "Quitacao ampla merece conferencia antes da assinatura",
                "Um termo de encerramento pode declarar que nada mais e devido mesmo quando o saldo "
                "da caucao ainda nao foi apresentado. Antes de assinar, registre ressalva, confira "
                "se a devolucao aparece com valor e data e peça copia de todos os anexos. Se ja houve "
                "assinatura, o alcance da declaracao depende da redacao, da informacao disponivel, "
                "de eventual vicio e dos pagamentos posteriores; a prova se torna mais exigente, "
                "mas o documento nao deve ser interpretado fora de seu contexto."
            ),
        ],
        "faq": [
            faq("Existe prazo legal fixo para devolver toda caucao?", "A Lei 8.245/1991 nao estabelece um prazo unico. A devolucao deve acompanhar o encerramento e o acerto comprovado, observados contrato, notificacao e eventual mora."),
            faq("O locador pode descontar pintura?", "Somente a existencia da pintura nao basta. E preciso demonstrar deterioracao alem do uso normal e o custo correspondente, comparando as vistorias e demais provas."),
        ],
        "official_sources": [
            source(LEI + "#art38", "Lei 8.245/1991, art. 38, paragrafo 2", "deposito em poupanca e reversao das vantagens ao locatario"),
            source(CC + "#art389", "Codigo Civil, art. 389", "consequencias do inadimplemento e indice supletivo de atualizacao"),
        ],
    },
    "imob-caucao-limite-tres-alugueis": {
        "opening": (
            "O teto de tres meses vale para caucao em dinheiro, nao para todo bem oferecido como "
            "garantia. Identificar a modalidade e essencial: um deposito de seis alugueis nao vira "
            "regular por receber outro nome, mas uma caucao imobiliaria segue regras de registro e "
            "valor diferentes. O contrato e os comprovantes mostram se houve excesso ou outra forma "
            "de garantia."
        ),
        "sections": [
            section(
                "O paragrafo 2 do artigo 38 limita a caucao em dinheiro",
                "A caucao paga em dinheiro nao pode exceder o equivalente a tres meses de aluguel e "
                "deve permanecer em caderneta de poupanca. O limite recai sobre o valor da garantia, "
                "nao sobre adiantamentos ou encargos validos de natureza diferente. Separar cada "
                "rubrica evita que deposito excessivo seja mascarado como taxa administrativa."
            ),
            section(
                "Bens moveis e imoveis seguem outra disciplina",
                "O mesmo artigo admite caucao em bens moveis, registrada no cartorio de titulos e "
                "documentos, e em bens imoveis, averbada na matricula. Nessas formas, a lei nao usa o "
                "teto de tres alugueis. Isso nao autoriza avaliacao ficticia, falta de registro ou "
                "cumulo com outra modalidade contratual; apenas mostra que o limite monetario nao "
                "pode ser transportado sem criterio."
            ),
            section(
                "O excesso pode ser exigencia vedada e deve ser documentado",
                "O artigo 43, inciso I, trata como contravencao exigir, por motivo de locacao, quantia "
                "alem do aluguel e encargos permitidos. A aplicacao penal depende dos fatos e da "
                "autoridade competente, enquanto a esfera civil pode discutir a clausula e a "
                "devolucao do que excedeu o limite. Nao cabe prometer condenacao ou restituicao em "
                "dobro apenas pela leitura isolada do valor."
            ),
            section(
                "Comprovante e finalidade revelam a cobranca real",
                "Reuna proposta, contrato, recibo, transferencia e mensagens. Confira se o valor foi "
                "entregue ao locador, depositado em poupanca e descrito como garantia. Se ja houve "
                "pagamento acima do teto, uma notificacao pode pedir reducao e demonstrativo; se o "
                "contrato ainda nao foi assinado, a divergencia deve ficar registrada antes de "
                "qualquer desembolso."
            ),
        ],
        "faq": [
            faq("O teto vale para caucao em imovel?", "Nao. Os tres meses limitam especificamente a caucao em dinheiro; a caucao imobiliaria exige averbacao e analise propria."),
            faq("Pagar seis alugueis torna todo contrato nulo?", "Nao automaticamente. A locacao e a garantia precisam ser separadas; o excesso pode ser discutido e restituido conforme prova, sem presumir a invalidade integral do contrato."),
            faq("Posso descontar o excesso dos proximos alugueis?", "Nao e prudente fazer compensacao unilateral sem acordo ou base processual adequada. Notifique, apure o credito e preserve o pagamento do aluguel para nao criar mora enquanto discute a devolucao."),
        ],
        "official_sources": [
            source(LEI + "#art38", "Lei 8.245/1991, art. 38", "teto da caucao em dinheiro e registros das demais formas"),
            source(LEI + "#art43", "Lei 8.245/1991, art. 43, I", "contravencao por exigencia de quantia alem do permitido"),
        ],
    },
    "imob-caucao-poupanca-correcao": {
        "opening": (
            "A caucao em dinheiro nao deveria ficar misturada ao caixa do locador. A Lei do "
            "Inquilinato determina deposito em caderneta de poupanca e atribui ao locatario as "
            "vantagens obtidas quando o saldo for levantado. Extrato, data e valor inicial permitem "
            "conferir o acerto sem inventar indice alternativo ou rendimento garantido."
        ),
        "sections": [
            section(
                "A poupanca e destino legal do deposito em dinheiro",
                "O artigo 38, paragrafo 2, combina tres regras: limite de tres alugueis, deposito em "
                "caderneta de poupanca e reversao das vantagens ao locatario por ocasiao do "
                "levantamento. A conta serve para preservar e tornar verificavel o saldo da garantia. "
                "Manter o dinheiro em conta corrente propria ou aplica-lo em produto escolhido pelo "
                "locador nao substitui a forma prevista na lei."
            ),
            section(
                "Rendimento incide sobre o saldo, nao sobre uma promessa abstrata",
                "A conferencia deve usar extratos da caderneta e o periodo efetivo. Se o deposito "
                "legal nao existiu, o equivalente controvertido precisa ser calculado a partir da "
                "obrigacao descumprida e das datas. A taxa legal de juros, quando cabivel, nao deve "
                "ser somada mecanicamente a atualizacao e ao rendimento sem verificar mora e evitar "
                "duplicidade."
            ),
            section(
                "Durante o contrato o saldo continua vinculado a garantia",
                "O locatario nao pode exigir livre movimentacao enquanto persistem as obrigacoes "
                "garantidas, e o locador nao pode consumir o valor como receita. Uso parcial para "
                "cobrir debito deve ser documentado e pode exigir recomposicao conforme o contrato. "
                "No encerramento, o acerto identifica pendencias comprovadas e libera o restante com "
                "as vantagens acumuladas."
            ),
            section(
                "Extrato e recibo evitam calculos por aproximacao",
                "Guarde comprovante inicial, identificacao da conta, extratos e termo de encerramento. "
                "Se a administradora nao apresenta os registros, solicite-os por escrito e indique o "
                "periodo que precisa ser esclarecido. A ausencia de documento pode justificar "
                "cobranca, mas nao autoriza afirmar previamente qual sera o valor reconhecido em "
                "acordo ou decisao."
            ),
        ],
        "faq": [
            faq("A caucao rende igual a qualquer investimento?", "Nao. A lei escolhe a caderneta de poupanca; o saldo e as vantagens devem ser apurados pelos extratos dessa modalidade."),
            faq("O locador pode usar a caucao durante a locacao?", "O valor permanece vinculado a garantia. Qualquer utilizacao para debito deve ter fundamento, demonstracao e acerto, nao servir a despesas pessoais do locador."),
            faq("Quem pode pedir o extrato da poupanca?", "O locatario tem interesse direto em conferir o saldo que revertera em seu beneficio. O contrato e o recibo ajudam a pedir identificacao da conta e demonstrativos ao locador ou administradora."),
        ],
        "official_sources": [
            source(LEI + "#art38", "Lei 8.245/1991, art. 38, paragrafo 2", "custodia em poupanca e vantagens do locatario"),
            source(CC + "#art389", "Codigo Civil, art. 389", "efeitos do inadimplemento e atualizacao supletiva"),
        ],
    },
    "imob-duas-garantias-vedacao": {
        "opening": (
            "Fiador e caucao inseridos como garantias contratuais da mesma locacao violam a regra "
            "do artigo 37. Isso nao significa que o locatario possa apagar sozinho a garantia mais "
            "onerosa, nem que toda protecao criada diretamente pela lei desapareca. A regularizacao "
            "precisa distinguir garantias convencionadas, ordem dos atos e eventual penhor legal."
        ),
        "sections": [
            section(
                "O artigo 37 proibe duas modalidades contratuais",
                "O paragrafo unico do artigo 37 veda, sob pena de nulidade, mais de uma modalidade de "
                "garantia no mesmo contrato. A regra alcanca a combinacao convencional de caucao, "
                "fianca, seguro-fianca locaticia e cessao fiduciaria de quotas. Separar finalidades "
                "no texto, chamando uma garantia de protecao para danos e outra de garantia do "
                "aluguel, nao afasta necessariamente o cumulo.\n\n"
                "O artigo 43, inciso II, tambem preve contravencao para quem exige mais de uma "
                "modalidade. Responsabilidade penal depende de apuracao propria; na esfera civil, o "
                "objetivo imediato e impedir cobranca duplicada e definir, com base no negocio, qual "
                "efeito a nulidade produz."
            ),
            section(
                "Nao existe escolha unilateral automatica da garantia sobrevivente",
                "A lei declara vedado o cumulo, mas nao entrega ao locatario um botao para liberar o "
                "fiador ou levantar a caucao sem concordancia. Cronologia, redacao, intencao, "
                "execucao do contrato e eventual decisao influenciam a solucao. Devolver por conta "
                "propria uma garantia antes de formalizar a substituicao tambem pode criar nova "
                "disputa sobre insuficiencia.\n\n"
                "A notificacao deve identificar ambas as modalidades, pedir regularizacao e propor "
                "uma unica garantia. Se houver deposito, informe valor e conta; se houver fiador, "
                "inclua o instrumento assinado. A resposta escrita do locador reduz incerteza sobre "
                "o que permaneceu pactuado."
            ),
            section(
                "Penhor legal nao e segunda garantia escolhida no contrato",
                "O Codigo Civil, artigo 1.467, II, reconhece ao dono do predio penhor legal sobre bens "
                "moveis que guarnecem o imovel pelos alugueis ou rendas. No REsp 2.233.511, julgado "
                "em 2026, o STJ distinguiu esse mecanismo das garantias contratuais: a fianca "
                "ajustada nao exclui, por si, o penhor que decorre diretamente da lei.\n\n"
                "A decisao nao autoriza apreensao ilimitada. Os artigos 1.469 a 1.471 limitam bens ao "
                "valor da divida, exigem comprovante na tomada urgente e homologacao judicial em "
                "seguida. A protecao legal e a exigencia abusiva de duas garantias no contrato sao "
                "problemas diferentes."
            ),
            section(
                "Garantia acessoria ou simples obrigacao precisa ser classificada",
                "Nem todo dever contratual e modalidade de garantia. Vistoria, seguro contra "
                "incendio atribuido por clausula ou obrigacao de conservar o imovel nao viram caucao "
                "apenas porque protegem economicamente o locador. Em sentido inverso, reter um valor "
                "com funcao real de assegurar o contrato pode ser garantia ainda que receba nome "
                "criativo. Importam estrutura e funcao, nao apenas o rotulo."
            ),
            section(
                "Documentos mostram se houve cumulo e cobranca efetiva",
                "Contrato, aditivos, recibos, apolice, termo de fianca e comunicacoes permitem mapear "
                "quando cada garantia nasceu. Uma orientacao juridica pode formular pedido de "
                "declaracao, liberacao ou devolucao conforme esse historico, sem prometer qual "
                "modalidade sera mantida antes de analisar o conjunto.\n\n"
                "Se ja existe cobranca judicial ou penhor legal, a estrategia precisa preservar "
                "prazos e separar a nulidade contratual da garantia criada pela lei. Tratar ambos "
                "como a mesma coisa pode produzir uma defesa incompleta."
            ),
            section(
                "Nulidade civil e contravencao seguem apuracoes distintas",
                "A vedacao contratual pode impedir execucao duplicada ou fundamentar regularizacao, "
                "enquanto a contravencao do artigo 43 exige apuracao pelos canais competentes. Uma "
                "notificacao privada nao condena locador ou administradora. Em sentido inverso, a "
                "existencia de investigacao penal nao libera automaticamente caucao ou fiador. Cada "
                "pretensao precisa de pedido, legitimidade e prova apropriados, sem usar ameaca "
                "criminal como substituto de solucao contratual."
            ),
        ],
        "faq": [
            faq("Posso exigir a devolucao imediata da caucao e manter o fiador?", "A cumulação e vedada, mas a garantia que permanece nao e escolhida automaticamente pelo locatario. Formalize a regularizacao com base no contrato e nos atos praticados."),
            faq("Fianca impede penhor legal dos bens no imovel?", "Nao por si so. No REsp 2.233.511, o STJ distinguiu a vedacao de garantias contratuais do penhor que nasce diretamente do artigo 1.467 do Codigo Civil."),
            faq("Duas assinaturas no mesmo instrumento provam qual garantia e valida?", "Nao necessariamente. Assinaturas provam o pacto, mas a solucao do cumulo considera cronologia, funcao das clausulas, execucao e eventual regularizacao; nao ha escolha unilateral automatica. Recibos e atos posteriores tambem podem esclarecer o que foi efetivamente exigido."),
        ],
        "official_sources": [
            source(LEI + "#art37", "Lei 8.245/1991, art. 37", "vedacao de mais de uma modalidade contratual"),
            source(LEI + "#art43", "Lei 8.245/1991, art. 43, II", "contravencao pela exigencia de mais de uma garantia"),
            source(CC + "#art1467", "Codigo Civil, arts. 1.467 a 1.471", "penhor legal do locador e seus limites"),
            source(STJ_RESP_2233511, "STJ, REsp 2.233.511/AL", "fianca contratual nao exclui o penhor legal"),
        ],
    },
    "imob-seguro-fianca-regresso": {
        "opening": (
            "O seguro-fianca protege o locador dentro das coberturas e limites da apolice, mas nao "
            "apaga a obrigacao inadimplida do locatario. Depois da indenizacao, a seguradora pode "
            "buscar o credito sub-rogado. Em 2026, a base geral vigente esta na Lei 15.040/2024, e "
            "nao mais no revogado artigo 786 do Codigo Civil."
        ),
        "sections": [
            section(
                "A apolice define o prejuizo garantido ao locador",
                "A SUSEP explica que o segurado e o locador e o garantido e o locatario. Falta de "
                "pagamento de alugueis e cobertura basica; encargos, tributos, contas e danos fisicos "
                "dependem do que foi contratado. A indenizacao deve respeitar cobertura, limite, "
                "vigencia e data de encerramento. O seguro e acessorio ao contrato de locacao e nao "
                "pode ampliar silenciosamente a obrigacao principal.\n\n"
                "A entrega amigavel das chaves, o abandono ou a decretacao do despejo influenciam a "
                "caracterizacao e o calculo do sinistro segundo a orientacao especifica da SUSEP. "
                "Por isso, termo de entrega e comunicacao de encerramento sao essenciais para "
                "conferir periodos incluidos."
            ),
            section(
                "A Lei 15.040 substituiu a antiga regra do Codigo Civil",
                "A Lei 15.040/2024 entrou em vigor em 11 de dezembro de 2025 e revogou os artigos "
                "757 a 802 do Codigo Civil. Seu artigo 94 estabelece que a seguradora se sub-roga nos "
                "direitos do segurado pelas indenizacoes pagas nos seguros de dano. A cobranca fica "
                "limitada ao direito transferido pelo pagamento; nao nasce um credito independente "
                "de qualquer valor ou encargo desejado.\n\n"
                "A propria SUSEP ressalta que a indenizacao ao locador nao isenta o locatario das "
                "obrigacoes da locacao. Isso explica a cobranca posterior, mas nao dispensa prova "
                "do desembolso, do periodo, da cobertura e da composicao do saldo."
            ),
            section(
                "Demonstrativo deve reconciliar pagamento, cobertura e divida",
                "Solicite apolice e condicoes, aviso e regulacao do sinistro, comprovante do valor "
                "pago ao locador, memoria de calculo e historico da locacao. Compare aluguel, "
                "encargos, multas e datas com boletos e comprovantes. Parcela ja paga, abatida ou "
                "fora da cobertura nao pode ser presumida correta apenas porque aparece em planilha "
                "da cobradora.\n\n"
                "A sub-rogacao tambem nao pode prejudicar o direito remanescente do segurado contra "
                "terceiros, conforme o paragrafo 3 do artigo 94. Se o locador recebeu apenas parte do "
                "prejuizo, a conciliacao dos creditos deve evitar pagamento duplicado."
            ),
            section(
                "Encerramento antecipado precisa chegar a seguradora",
                "Segundo a SUSEP, locador ou locatario podem comunicar o termino antecipado com "
                "documento comprobatorio. A apolice e cancelada a partir dessa data e pode haver "
                "restituicao proporcional do premio ao responsavel pelo pagamento, exceto em caso de "
                "sinistro. Essa regra nao elimina dividas anteriores, mas impede tratar vigencia "
                "ficticia como fato incontroverso.\n\n"
                "Se a imobiliaria retardou a comunicacao, guarde entrega das chaves, distrato e "
                "protocolos. A responsabilidade pelo periodo adicional depende desses fatos; nao "
                "basta supor que todo valor depois da mudanca seja automaticamente indevido."
            ),
            section(
                "Contestacao responsavel aponta itens, nao nega o seguro inteiro",
                "Uma resposta util identifica divergencia de periodo, pagamento ou encargo e anexa a "
                "prova correspondente. Se o saldo estiver correto, negociacao pode discutir forma "
                "de pagamento sem reconhecimento de rubricas estranhas. Se houver negativacao, "
                "avalie comunicacoes e origem do dado com as regras aplicaveis ao cadastro.\n\n"
                "Analise juridica da apolice e da memoria permite medir a pretensao, mas nao garante "
                "reducao, retirada de cadastro ou acordo. O desfecho depende da cobertura, da "
                "indenizacao efetiva e dos documentos da locacao."
            ),
            section(
                "Cobrador deve demonstrar a cadeia do credito",
                "Quando a cobranca e feita por escritorio ou empresa diferente da seguradora, peça "
                "identificacao do credor, mandato ou cessao pertinente e canal para conferencia. A "
                "sub-rogacao do artigo 94 nasce com a indenizacao paga pela seguradora; uma empresa "
                "terceira precisa explicar em que qualidade atua. Isso nao autoriza ignorar citacao "
                "ou revela fraude por si, mas reduz o risco de pagar sem obter baixa e quitacao do "
                "titular correto."
            ),
        ],
        "faq": [
            faq("Pagar o premio quita alugueis futuros?", "Nao. O premio compra a cobertura do locador; a SUSEP informa que o locatario permanece responsavel pela obrigacao inadimplida."),
            faq("A seguradora pode cobrar mais do que indenizou?", "A sub-rogacao do artigo 94 da Lei 15.040 se vincula as indenizacoes pagas. Encargos adicionais exigem fundamento, demonstracao e compatibilidade com a obrigacao original."),
            faq("O artigo 786 do Codigo Civil ainda e a regra vigente?", "Nao. A Lei 15.040 entrou em vigor em dezembro de 2025, revogou os artigos 757 a 802 e passou a disciplinar a sub-rogacao no artigo 94."),
        ],
        "official_sources": [
            source(LAW_15040 + "#art94", "Lei 15.040/2024, arts. 94 e 133 a 134", "sub-rogacao vigente e revogacao do antigo regime do Codigo Civil"),
            source(SUSEP_FIANCA, "SUSEP, Seguro Fianca Locaticia", "coberturas, partes, termino e responsabilidade do locatario"),
        ],
    },
    "imob-titulo-capitalizacao-resgate": {
        "opening": (
            "O titulo usado na locacao deve ser da modalidade instrumento de garantia e ter "
            "condicoes gerais proprias. Ele nao e a cessao fiduciaria de quotas de fundo descrita no "
            "artigo 37, inciso IV, da Lei do Inquilinato. Para saber quem pode resgatar e quando, e "
            "necessario ler o contrato principal, o titulo, a cessao e a regulacao da SUSEP."
        ),
        "sections": [
            section(
                "O inciso IV do artigo 37 trata de quotas de fundo",
                "A quarta modalidade listada na Lei 8.245/1991 e a cessao fiduciaria de quotas de "
                "fundo de investimento. Titulo de capitalizacao nao e quota de fundo e nao deve ser "
                "apresentado como se estivesse nominalmente nesse inciso. Quando usado na locacao, "
                "o produto precisa ser enquadrado no contrato como instrumento de garantia ou outra "
                "forma de caucao admitida, sem se somar a fianca, seguro-fianca ou segunda garantia "
                "convencional.\n\n"
                "Essa distincao evita duas conclusoes erradas: que qualquer titulo serve e que o "
                "artigo 37, IV, regula diretamente resgate, carencia e cessao. Esses pontos pertencem "
                "as condicoes do produto e as normas da capitalizacao."
            ),
            section(
                "A modalidade da SUSEP assegura obrigacao de contrato principal",
                "A Resolucao CNSP 384/2020, reproduzida no manual tecnico da SUSEP, define instrumento "
                "de garantia como titulo cuja provisao matematica assegura obrigacao assumida pelo "
                "titular perante terceiro. O contrato principal deve prever expressamente essa "
                "modalidade ou outra enquadrada como caucao. A cessao do direito de resgate so se "
                "aperfeicoa, no limite da obrigacao, quando ocorre o inadimplemento previsto.\n\n"
                "Durante a vigencia do contrato principal, o titular so pode resgatar com anuencia "
                "do terceiro garantido. Isso explica por que a sociedade de capitalizacao pede prova "
                "de liberacao; a exigencia precisa corresponder ao documento assinado, e nao a uma "
                "recusa sem motivo apos o encerramento."
            ),
            section(
                "Fim antecipado da locacao abre alternativas de resgate",
                "Pelas regras apresentadas pela SUSEP, se o contrato principal terminar antes, o "
                "titular pode usar o titulo para outro contrato, solicitar resgate antecipado sem "
                "penalidade ou aguardar o fim da vigencia para o resgate final. O procedimento exige "
                "comprovar a extincao e observar as condicoes gerais. Debito locaticio pendente pode "
                "ser discutido e nao deve ser confundido com simples demora administrativa.\n\n"
                "Termo de entrega das chaves, distrato, quitacao dos encargos e comunicacao a "
                "sociedade emissora permitem identificar quem ainda precisa praticar ato. Se houver "
                "controversia sobre danos, o saldo efetivamente vinculado e o limite da obrigacao "
                "devem ser demonstrados."
            ),
            section(
                "Valor de resgate nao e sinonimo de tudo o que foi pago",
                "A SUSEP informa que parte dos pagamentos forma a provisao matematica e outras "
                "parcelas podem custear carregamento e sorteios. As condicoes gerais devem mostrar "
                "percentuais, atualizacao, vigencia e resgate. Portanto, comparar apenas o pagamento "
                "unico com o saldo liberado pode produzir conclusao errada; e necessario conferir a "
                "tabela do produto e a modalidade registrada.\n\n"
                "A aprovacao pela SUSEP significa adequacao normativa, nao recomendacao de compra ou "
                "garantia de rentabilidade. Antes da contratacao, consulte o numero do processo e a "
                "situacao do produto nos canais oficiais."
            ),
            section(
                "Uma notificacao deve apontar o documento que falta",
                "Se o resgate permanece bloqueado depois do fim da locacao, solicite por escrito a "
                "causa, a clausula e o ato necessario. Envie os comprovantes ao locador, a "
                "administradora e a sociedade de capitalizacao conforme as responsabilidades de "
                "cada um. Protocolo e resposta ajudam a distinguir pendencia documental de retencao "
                "injustificada.\n\n"
                "Uma cobranca juridica pode pedir liberacao ou discutir perdas demonstradas, mas nao "
                "se pode assegurar prazo, saldo ou indenizacao sem examinar titulo, cessao, contrato "
                "principal e eventuais dividas abertas."
            ),
            section(
                "Consulta do produto confirma modalidade e condicoes registradas",
                "O numero do processo SUSEP permite conferir se o titulo esta registrado e liberado. "
                "A denominacao comercial, a sociedade emissora e as condicoes entregues devem "
                "coincidir com a consulta. Divergencia de documento, titular ou modalidade precisa "
                "ser esclarecida antes do resgate. A fiscalizacao do produto nao valida o contrato "
                "de locacao individual nem decide se houve inadimplemento; essas questoes continuam "
                "dependentes da prova da relacao principal."
            ),
        ],
        "faq": [
            faq("O artigo 37, IV, cria a garantia por titulo de capitalizacao?", "Nao. O inciso IV menciona cessao fiduciaria de quotas de fundo. O titulo de capitalizacao tem regulacao propria da SUSEP e nao se confunde com essa modalidade."),
            faq("O resgate sempre devolve todo o valor pago?", "Nao necessariamente. O saldo depende da provisao matematica e das condicoes gerais; confira tabela, atualizacao e regras especificas do produto registrado."),
        ],
        "official_sources": [
            source(LEI + "#art37", "Lei 8.245/1991, art. 37, IV", "cessao fiduciaria de quotas, distinta de titulo de capitalizacao"),
            source(SUSEP_CAPITALIZACAO_MANUAL, "SUSEP, Manual Tecnico de Capitalizacao", "instrumento de garantia, cessao e resgate apos fim do contrato principal"),
            source(SUSEP_CAPITALIZACAO, "SUSEP, perguntas frequentes sobre capitalizacao", "modalidades, provisao, carencia e consulta do produto"),
        ],
    },
    "imob-aluguel-antecipado-quando-pode": {
        "opening": (
            "A Lei do Inquilinato proibe antecipar aluguel como regra, mas abre duas excecoes "
            "diferentes: locacao sem garantia e locacao por temporada. O primeiro mes pago na "
            "assinatura nao e pratica automaticamente valida quando ja existe fiador, caucao ou "
            "seguro. Contrato, modalidade e data de vencimento precisam ser lidos juntos."
        ),
        "sections": [
            section(
                "O artigo 20 estabelece a proibicao e remete as excecoes",
                "Fora do artigo 42 e da locacao por temporada, o locador nao pode exigir pagamento "
                "antecipado. A regra nao distingue primeiro mes de meses seguintes e nao transforma "
                "costume de mercado em permissao. Se o contrato tem garantia e e residencial comum, "
                "a cobranca antecipada deve ser questionada com base na estrutura real do negocio."
            ),
            section(
                "Sem garantia, o artigo 42 permite cobrar o mes vincendo",
                "Quando a locacao nao esta garantida por nenhuma modalidade do artigo 37, o artigo "
                "42 autoriza exigir aluguel e encargos ate o sexto dia util do mes vincendo. Nessa "
                "hipotese, a antecipacao compensa a ausencia de garantia. Nao e correto exigir "
                "fiador ou caucao e usar simultaneamente a excecao destinada ao contrato sem "
                "garantia."
            ),
            section(
                "Temporada admite antecipacao e tambem garantia",
                "O artigo 49 permite receber de uma so vez e antecipadamente alugueis e encargos da "
                "temporada, alem de exigir uma modalidade de garantia. A temporada tem finalidade e "
                "prazo definidos no artigo 48, de ate noventa dias; apenas rotular uma locacao longa "
                "como temporaria nao cria a excecao. Nesse regime, pagamento antecipado e garantia "
                "podem coexistir por autorizacao expressa."
            ),
            section(
                "A cobranca irregular pode ter consequencias civis e penais",
                "O artigo 43, inciso III, tipifica a cobranca antecipada fora das hipoteses do artigo "
                "42 e da temporada. A apuracao penal nao e automatica nem substitui a regularizacao "
                "civil. Guarde proposta, contrato, comprovantes e mensagens para demonstrar se havia "
                "garantia, qual periodo foi cobrado e quando o pagamento foi exigido."
            ),
        ],
        "faq": [
            faq("Pode cobrar o primeiro aluguel na entrega das chaves?", "Nao e automaticamente valido. Com garantia contratual, o primeiro mes nao cria excecao propria; sem garantia, aplica-se o artigo 42 e seu vencimento ate o sexto dia util do mes vincendo."),
            faq("Temporada pode ter garantia e aluguel antecipado?", "Sim. O artigo 49 autoriza ambos, desde que a locacao realmente se enquadre na finalidade e no prazo da temporada."),
            faq("Contrato sem garantia pode cobrar depois do sexto dia util?", "As partes podem fixar vencimento compativel, mas a permissao de antecipar do artigo 42 vai ate o sexto dia util do mes vincendo; a clausula precisa ser conferida sem ampliar a excecao."),
        ],
        "official_sources": [
            source(LEI + "#art20", "Lei 8.245/1991, art. 20", "proibicao geral de aluguel antecipado"),
            source(LEI + "#art42", "Lei 8.245/1991, art. 42", "antecipacao no contrato sem garantia ate o sexto dia util"),
            source(LEI + "#art49", "Lei 8.245/1991, arts. 48 e 49", "antecipacao e garantia na locacao por temporada"),
            source(LEI + "#art43", "Lei 8.245/1991, art. 43, III", "contravencao fora das excecoes legais"),
        ],
    },
    "imob-fianca-sem-outorga-conjugal": {
        "title": "Fianca sem assinatura do conjuge: quando a garantia e ineficaz",
        "meta_description": "Entenda a outorga conjugal na fianca, a Sumula 332 do STJ, a separacao convencional ou obrigatoria e a excecao reconhecida para uniao estavel.",
        "h1": "Fianca sem outorga conjugal e os limites da Sumula 332 do STJ",
        "opening": (
            "A falta de assinatura do outro conjuge pode tornar a fianca inteiramente ineficaz, mas "
            "a resposta depende do estado civil e do regime de bens. Separacao convencional nao se "
            "confunde com separacao legal obrigatoria, e o STJ nao estende a mesma regra a uniao "
            "estavel. Certidao, pacto e data da garantia sao indispensaveis."
        ),
        "sections": [
            section(
                "O artigo 1.647 exige outorga para fianca e aval",
                "O Codigo Civil impede que pessoa casada preste fianca ou aval sem autorizacao do "
                "outro conjuge, salvo no regime de separacao absoluta. A verificacao nao termina na "
                "expressao usada informalmente pelo fiador: certidao de casamento, pacto registrado "
                "e eventual decisao sobre regime mostram qual disciplina incidia quando o "
                "instrumento foi assinado."
            ),
            section(
                "A Sumula 332 fala em ineficacia total da garantia",
                "A Sumula 332 do STJ estabelece que a fianca prestada sem autorizacao de um dos "
                "conjuges implica ineficacia total da garantia. Nao se limita automaticamente a "
                "meacao do conjuge ausente. A Jurisprudencia em Teses 101 registra ainda ressalva "
                "para fiador que declarou falsamente ser solteiro, situacao que exige prova e nao "
                "pode ser presumida em qualquer contrato."
            ),
            section(
                "Separacao convencional e obrigatoria nao recebem o mesmo tratamento",
                "A expressao separacao absoluta nao significa que toda separacao imposta pela lei "
                "dispense outorga. No REsp 1.163.074, resumido no Informativo 420, o STJ entendeu que "
                "a excecao se refere a separacao convencional; na separacao legal obrigatoria, a "
                "venia continuou exigida. Logo, dizer que a dispensa decorre de qualquer regra legal "
                "ou que depende apenas da idade do fiador e impreciso."
            ),
            section(
                "Uniao estavel tem excecao jurisprudencial especifica",
                "A Jurisprudencia em Teses 101, com base no REsp 1.299.866, afirma que a fianca "
                "prestada por convivente em uniao estavel sem outorga do companheiro nao e nula nem "
                "anulavel. Portanto, a Sumula 332 nao se aplica automaticamente a uniao estavel, "
                "ainda que formalizada por escritura. Isso nao resolve outros temas patrimoniais do "
                "casal, apenas delimita essa garantia perante terceiros."
            ),
            section(
                "Documentos definem a defesa ou a substituicao",
                "Reuna contrato, termo de fianca, certidao atualizada, pacto antenupcial e eventual "
                "declaracao de estado civil. Locador pode precisar de nova garantia se a fianca for "
                "ineficaz; fiador e conjuge devem avaliar legitimidade, prazo e conduta declarada. "
                "Nao se deve prometer anulacao apenas porque falta uma assinatura visivel na copia, "
                "sem verificar todos os instrumentos."
            ),
        ],
        "faq": [
            faq("A regra da Sumula 332 vale para uniao estavel?", "Nao automaticamente. A Jurisprudencia em Teses 101 do STJ afirma que a fianca do convivente sem outorga do companheiro nao e nula nem anulavel."),
            faq("Separacao obrigatoria dispensa a assinatura?", "Segundo o STJ no REsp 1.163.074, nao. A excecao da separacao absoluta foi associada a separacao convencional, enquanto a legal obrigatoria exige outorga."),
        ],
        "official_sources": [
            source(CC + "#art1647", "Codigo Civil, arts. 1.647 a 1.650", "outorga, suprimento, anulabilidade e legitimidade"),
            source(STJ_SUMULA_332, "STJ, Sumula 332", "ineficacia total da fianca sem autorizacao conjugal"),
            source(STJ_TESES_101, "STJ, Jurisprudencia em Teses 101", "Sumula 332 e excecao para uniao estavel"),
            source(STJ_INFO_420, "STJ, Informativo 420, REsp 1.163.074/PB", "outorga na separacao legal obrigatoria"),
        ],
    },
    "imob-reajuste-anual-indice": {
        "opening": (
            "O indice do aluguel nasce da clausula ou de acordo posterior, mas a periodicidade nao "
            "e livre. A Lei 10.192/2001 invalida reajuste com intervalo inferior a um ano. O aumento "
            "tambem nao pode ser ligado a moeda estrangeira, cambio ou salario minimo. Sem clausula "
            "aplicavel, uma parte nao escolhe sozinha o indice."
        ),
        "sections": [
            section(
                "Valor e indice sao convencionados dentro de limites",
                "O artigo 17 da Lei 8.245/1991 permite convencionar o aluguel, vedando moeda "
                "estrangeira, variacao cambial e salario minimo. O artigo 18 admite que as partes, de "
                "comum acordo, fixem novo valor ou insiram e modifiquem clausula de reajuste. IGP-M, "
                "IPCA ou outro indice de precos nao se aplica por preferencia unilateral da "
                "imobiliaria quando o contrato aponta criterio diferente."
            ),
            section(
                "A Lei 10.192 exige intervalo minimo de doze meses",
                "O artigo 2 da Lei 10.192/2001 admite indices gerais, setoriais ou ligados a custos "
                "nos contratos com duracao igual ou superior a um ano e declara nula a periodicidade "
                "inferior a um ano. Devem transcorrer ao menos 12 meses entre reajustes. Expedientes "
                "que reproduzem financeiramente atualizacao mais frequente tambem sao vedados."
            ),
            section(
                "O contrato omisso nao autoriza calculo improvisado",
                "Sem indice definido, locador e locatario podem pactuar aditivo. Nao havendo acordo, "
                "a acao revisional do artigo 19 so ajusta o aluguel ao mercado depois de tres anos "
                "do contrato ou do ultimo acordo; ela nao serve como reajuste anual automatico. "
                "Continuar pagando valor incontroverso e registrar a divergencia reduz risco de mora, "
                "mas a forma de pagamento deve ser avaliada no caso concreto."
            ),
            section(
                "Memoria de calculo precisa mostrar datas e variacao",
                "Confira data-base, indice contratual, periodo acumulado e valor anterior. Consulte a "
                "serie na instituicao oficial que a divulga e verifique se houve substituicao prevista "
                "na clausula. Arredondamento, periodo errado e aplicacao retroativa sao problemas "
                "diferentes de discordancia com o indice escolhido."
            ),
        ],
        "faq": [
            faq("Pode haver dois reajustes no mesmo ano?", "Em regra, nao. A Lei 10.192 considera nula a periodicidade inferior a um ano e tambem expedientes equivalentes a reajuste mais frequente."),
            faq("Sem indice no contrato, o locador escolhe o IPCA?", "Nao unilateralmente. A insercao ou mudanca da clausula depende de acordo; a revisao judicial ao mercado tem requisitos proprios."),
            faq("Indice negativo reduz o aluguel?", "A resposta depende da redacao da clausula, inclusive de piso ou tratamento da variacao negativa. Confira o texto e a serie oficial; nao se deve presumir reducao ou congelamento fora do pacto."),
        ],
        "official_sources": [
            source(LEI + "#art17", "Lei 8.245/1991, arts. 17 e 18", "limites do aluguel e alteracao consensual do reajuste"),
            source(LAW_10192 + "#art2", "Lei 10.192/2001, art. 2", "periodicidade minima anual e indices admitidos"),
        ],
    },
    "imob-igpm-alto-renegociar": {
        "opening": (
            "Uma alta expressiva do IGP-M nao torna a clausula ilegal por si so nem autoriza trocar "
            "o indice unilateralmente. Primeiro se confere se o percentual, a data-base e o periodo "
            "foram aplicados como contratados. Depois se avaliam acordo, revisao ao valor de mercado "
            "ou, em situacao realmente excepcional, os requisitos de intervencao judicial."
        ),
        "sections": [
            section(
                "Indice alto e erro de calculo sao problemas diferentes",
                "A memoria do reajuste deve indicar valor anterior, serie usada, meses acumulados e "
                "resultado. Um percentual desconfortavel pode reproduzir corretamente o indice; ja "
                "usar mes errado, indice diferente ou intervalo inferior a um ano e defeito "
                "verificavel. Separar as duas situacoes evita discutir abusividade quando a primeira "
                "providencia seria apenas corrigir a conta.\n\n"
                "Guarde contrato, aditivos, boletos e a publicacao oficial da serie. Se a clausula "
                "preve indice substituto em determinada circunstancia, confira se o evento ocorreu. "
                "Preferencia atual por IPCA nao altera sozinha o que foi pactuado."
            ),
            section(
                "O artigo 18 permite negociar valor e clausula",
                "Locador e locatario podem, de comum acordo, fixar novo aluguel, substituir o indice "
                "ou criar uma transicao. O aditivo deve indicar valor de partida, data de eficacia, "
                "novo indexador e proxima data-base. Desconto temporario sem esclarecer se muda o "
                "valor nominal pode gerar nova disputa no aniversario seguinte.\n\n"
                "Uma proposta consistente compara o aluguel atualizado com imoveis equivalentes e "
                "mostra o impacto financeiro. O locador nao e obrigado a aceitar a troca, e o "
                "locatario nao e obrigado a aderir a aumento diferente da clausula valida."
            ),
            section(
                "A revisional trienal procura preco de mercado",
                "Sem acordo, o artigo 19 autoriza locador ou locatario a pedir revisao judicial depois "
                "de tres anos de vigencia do contrato ou do ultimo acordo realizado. O objeto e "
                "ajustar o aluguel ao preco de mercado, nao declarar que o IGP-M e sempre indevido. "
                "Um acordo de valor reinicia o trienio mesmo que uma parte depois considere que o "
                "resultado nao alcancou o mercado.\n\n"
                "A prova costuma comparar localizacao, area, estado, vagas, uso e data das ofertas ou "
                "contratos. Anuncios isolados e nao concluídos podem ter peso limitado, por isso a "
                "qualidade da amostra importa mais que a quantidade."
            ),
            section(
                "O artigo 317 exige desproporcao por motivo imprevisivel",
                "A regra geral do Codigo Civil permite corrigir prestacao que se torne manifestamente "
                "desproporcional por motivos imprevisiveis. Isso nao transforma toda variacao de "
                "indice em fato imprevisivel e nao garante substituicao por IPCA. E preciso demonstrar "
                "evento superveniente, desproporcao concreta e relacao com a prestacao.\n\n"
                "A jurisprudencia examina natureza do contrato, alocacao de riscos e prova do "
                "desequilibrio. Portanto, citar apenas o percentual anual e insuficiente para "
                "assegurar liminar ou reducao; o fundamento precisa ser construido com fatos do caso."
            ),
            section(
                "Pagamento e negociacao precisam evitar mora artificial",
                "Enquanto nao existe aditivo ou decisao, deixar de pagar o reajuste contratual pode "
                "gerar cobranca e despejo. A parcela incontroversa, a forma de consignar e eventual "
                "pedido urgente devem ser avaliados antes de reter valores. Pagar informalmente o "
                "numero que parece justo nao substitui acordo nem deposito juridicamente adequado.\n\n"
                "Orientacao juridica pode revisar calculo, elaborar proposta e escolher a via, mas "
                "nao deve prometer novo indice, percentual ou resultado. A solucao depende da "
                "clausula, do trienio, do mercado e da prova de excepcionalidade."
            ),
            section(
                "Aditivo precisa dizer se substitui ou apenas adia o reajuste",
                "Durante periodos de alta, e comum pactuar desconto temporario ou teto excepcional. "
                "O documento deve esclarecer se o indice acumulado foi renunciado, diferido, "
                "parcelado ou incorporado ao novo valor. Tambem deve definir se o trienio revisional "
                "recomeca por haver acordo de valor. Sem essas respostas, a solucao imediata pode "
                "criar disputa maior na data-base seguinte, com cobranca retroativa que nenhuma das "
                "partes registrou de forma compreensivel."
            ),
        ],
        "faq": [
            faq("O IGP-M pode ser trocado por IPCA sem concordancia?", "Nao apenas porque subiu. A mudanca contratual depende de acordo; revisao judicial exige fundamento e prova proprios."),
            faq("Preciso esperar tres anos para qualquer negociacao?", "Nao. O artigo 18 permite acordo a qualquer tempo. O trienio e requisito da acao revisional especifica do artigo 19."),
            faq("Um acordo temporario reinicia o trienio?", "Depende de ele fixar novo valor ou apenas conceder tolerancia sem alterar o aluguel. A redacao e a execucao do aditivo precisam ser analisadas, pois acordos de valor podem reiniciar a contagem."),
        ],
        "official_sources": [
            source(LEI + "#art18", "Lei 8.245/1991, art. 18", "alteracao consensual do aluguel e da clausula de reajuste"),
            source(LEI + "#art19", "Lei 8.245/1991, art. 19", "revisao trienal ao preco de mercado"),
            source(CC + "#art317", "Codigo Civil, art. 317", "correcao excepcional de prestacao manifestamente desproporcional"),
        ],
    },
    "imob-acao-revisional-aluguel": {
        "opening": (
            "A acao revisional nao serve apenas a locador nem corrige automaticamente o indice. "
            "Depois de tres anos do contrato ou do ultimo acordo de valor, qualquer das partes pode "
            "pedir que o aluguel seja ajustado ao preco de mercado. O pedido exige valor pretendido, "
            "comparacoes idoneas e atencao aos limites do aluguel provisorio."
        ),
        "sections": [
            section(
                "O trienio conta da ultima fixacao consensual",
                "O artigo 19 da Lei 8.245/1991 exige tres anos de vigencia do contrato ou do acordo "
                "anteriormente realizado. Nao se conta apenas da assinatura original se houve acordo "
                "posterior que fixou novo valor. No REsp 1.566.231, o STJ reafirmou que um acordo de "
                "majoracao impede nova revisional durante o trienio, ainda que o valor acertado nao "
                "tenha alcancado o mercado.\n\n"
                "Reajuste anual pela clausula nao e necessariamente um novo acordo de valor: em geral, "
                "e aplicacao automatica da formula ja pactuada. A natureza de aditivo, desconto ou "
                "renegociacao deve ser conferida nos documentos antes de calcular o prazo."
            ),
            section(
                "A referencia e o mercado de imoveis comparaveis",
                "A revisional pode elevar ou reduzir o aluguel. Area, localizacao, conservacao, vagas, "
                "destinacao, periodo e condicoes do negocio interferem na comparacao. Anuncio sem "
                "locacao concluida mostra oferta, nao necessariamente preco efetivo; laudo e dados "
                "consistentes ajudam a explicar ajustes entre os imoveis.\n\n"
                "O processo nao existe para premiar uma parte pelo indice acumulado, mas para medir o "
                "valor locativo contemporaneo. Benfeitorias e caracteristicas incorporadas podem "
                "exigir exame tecnico, principalmente quando as partes divergem sobre autoria e "
                "impacto."
            ),
            section(
                "O artigo 68 fixa limites diferentes para o aluguel provisorio",
                "Na acao proposta pelo locador, o aluguel provisorio nao pode exceder 80 por cento do "
                "valor pedido. Na proposta pelo locatario, nao pode ser inferior a 80 por cento do "
                "aluguel vigente. Esses limites nao significam que o juiz aplicara automaticamente o "
                "percentual maximo ou minimo; elementos apresentados e clausulas de reajuste tambem "
                "sao considerados.\n\n"
                "A decisao provisoria produz efeitos a partir da citacao conforme o rito legal. O reu "
                "pode pedir revisao desse valor com elementos adequados, e a sentenca definira o "
                "aluguel final."
            ),
            section(
                "Diferencas sao acertadas depois da definicao final",
                "O artigo 69 estabelece que o aluguel fixado retroage a citacao. As diferencas "
                "apuradas durante o processo, descontado o que foi pago provisoriamente, tornam-se "
                "exigiveis nos termos legais depois do transito em julgado. Por isso, ambas as partes "
                "devem guardar pagamentos e reservar o risco de complemento ou restituicao.\n\n"
                "Aluguel provisorio nao encerra a controversia nem garante o valor da sentenca. Uma "
                "simulacao financeira deve incluir cenario de diferenca, correcao e duracao do "
                "processo sem apresentar economia certa."
            ),
            section(
                "A peticao e a contestacao precisam de numeros verificaveis",
                "Contrato, aditivos, historico de reajustes, planta, fotos, laudos e comparaveis formam "
                "a base. A inicial indica o aluguel cuja fixacao se pretende; a defesa pode apresentar "
                "contraproposta e contestar amostras. Pericia pode ser necessaria quando os valores "
                "permanecem distantes.\n\n"
                "Uma avaliacao juridica e tecnica define se o trienio se completou e se a prova "
                "justifica o custo do processo. Nao e responsavel prometer aluguel provisorio, "
                "percentual de reducao ou sentenca antes dessa analise."
            ),
            section(
                "Renovatoria, reajuste e revisional nao devem ser confundidos",
                "A acao renovatoria de locacao empresarial discute continuidade e possui requisitos "
                "proprios; o reajuste aplica indice contratual; a revisional do artigo 19 mede preco "
                "de mercado. Mesmo quando dois temas aparecem no mesmo periodo, pedido e prova de "
                "cada um permanecem distintos. Classificar corretamente a pretensao evita usar o "
                "trienio como se fosse prazo de qualquer acao e impede apresentar simples planilha "
                "de inflacao como laudo de valor locativo."
            ),
        ],
        "faq": [
            faq("Reajuste anual reinicia sempre o prazo de tres anos?", "A aplicacao automatica do indice nao se confunde necessariamente com acordo de novo valor. Aditivos e renegociacoes precisam ser classificados pelos documentos."),
            faq("O aluguel provisorio e sempre 80 por cento do pedido?", "Nao. O artigo 68 fixa tetos ou pisos distintos conforme quem ajuiza; o juiz considera os elementos do caso dentro desses limites."),
            faq("A diferenca da sentenca e cobrada desde quando?", "O artigo 69 faz o aluguel fixado retroagir a citacao e disciplina o acerto das diferencas depois do transito em julgado, descontando os valores provisorios efetivamente pagos. Recibos mensais e memoria de atualizacao sao essenciais para evitar cobranca repetida ao final do processo."),
        ],
        "official_sources": [
            source(LEI + "#art19", "Lei 8.245/1991, art. 19", "trienio e ajuste ao preco de mercado"),
            source(LEI + "#art68", "Lei 8.245/1991, arts. 68 e 69", "rito, limites provisorios e efeitos desde a citacao"),
            source(
                "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20160307&formato=PDF&nreg=201500901224&salvar=false&seq=1491451&tipo=0",
                "STJ, REsp 1.566.231/PE",
                "novo acordo de aluguel reinicia o prazo trienal"
            ),
        ],
    },
    "imob-aumento-fora-contrato": {
        "opening": (
            "Fora da formula e da data contratadas, o locador pode propor novo aluguel, mas nao o "
            "impor por mensagem ou boleto. Recusar a proposta tambem nao autoriza simplesmente reter "
            "ou pagar informalmente qualquer valor se o credor deixa de receber. Acordo, prova da "
            "recusa e consignacao judicial podem ser necessarios para evitar mora."
        ),
        "sections": [
            section(
                "O artigo 18 exige acordo para mudar o valor",
                "Locador e locatario podem fixar novo aluguel e alterar a clausula de reajuste a "
                "qualquer tempo, desde que concordem. A proposta de aumento nao produz aditivo por "
                "si. Silencio, conversa incompleta ou boleto unilateral devem ser comparados com o "
                "contrato e com os pagamentos posteriores antes de afirmar que houve aceitacao.\n\n"
                "Se houver consenso, o documento deve definir valor, inicio, indice e data-base. Isso "
                "evita que um aumento negociado seja somado ao reajuste anual poucos dias depois sem "
                "que as partes tenham tratado do efeito cumulativo."
            ),
            section(
                "Valorizacao do mercado nao substitui a via revisional",
                "Sem acordo, a adequacao ao mercado segue o artigo 19 depois de tres anos do contrato "
                "ou do ultimo acordo. O locador nao pode converter a propria pesquisa de anuncios em "
                "ordem imediata de pagamento. O locatario, por sua vez, nao deve tratar a ausencia de "
                "aditivo como licenca para ignorar reajuste anual valido ja previsto.\n\n"
                "Reajuste contratual e renegociacao sao atos diferentes. A primeira aplica a formula "
                "vigente; a segunda cria novo valor por consenso; a revisional pede ao juiz valor de "
                "mercado quando o requisito temporal esta preenchido."
            ),
            section(
                "Recusa do valor correto pode levar a consignacao judicial",
                "Se o locador recusa receber o valor correto, nao basta reter o dinheiro nem pagar "
                "informalmente por meio que nao gere quitacao. O artigo 67 disciplina a consignacao "
                "judicial de alugueis e acessorios, com indicacao dos valores e depositos no processo. "
                "A medida exige procedimento e prazos proprios; uma transferencia rejeitada nao tem "
                "automaticamente o mesmo efeito liberatorio.\n\n"
                "Antes de ajuizar, registre a oferta, a recusa e a composicao do valor. Se parte e "
                "incontroversa e outra depende de calculo, a estrategia deve evitar deposito "
                "insuficiente e explicar a diferenca."
            ),
            section(
                "A recusa ao aumento nao permite medidas de pressao",
                "Continuar cumprindo o contrato valido nao autoriza troca de fechadura, corte de agua "
                "ou constrangimento. Eventual despejo depende de fundamento legal e processo. Se o "
                "locador alega inadimplemento pelo novo valor, contrato, boletos anteriores, proposta "
                "e resposta mostram se existiu acordo ou apenas tentativa unilateral.\n\n"
                "Tambem nao e prudente prometer que todo pagamento antigo impedira a mora. Quando o "
                "credor se recusa a receber ou ha incerteza real, a via de consignacao e o valor "
                "correto precisam ser avaliados rapidamente."
            ),
            section(
                "Uma resposta escrita deve separar proposta e obrigacao",
                "Indique a clausula vigente, a data do proximo reajuste, o valor que reconhece e se "
                "aceita ou recusa a renegociacao. Guarde comprovantes de oferta de pagamento. Uma "
                "analise juridica pode revisar a clausula, preparar aditivo ou consignacao e responder "
                "a notificacao.\n\n"
                "Nao se pode assegurar a manutencao definitiva do aluguel, pois reajuste futuro, "
                "acao revisional ou termino legitimo da locacao podem alterar a relacao. O ponto "
                "imediato e impedir que proposta unilateral seja confundida com acordo."
            ),
            section(
                "Consignar nao significa fixar definitivamente o aluguel",
                "O deposito busca liberar pagamentos nos limites reconhecidos enquanto a divergencia "
                "e julgada; nao transforma o valor escolhido em aluguel final por vontade do "
                "depositante. O locador pode contestar insuficiencia, e a lei disciplina complemento "
                "e efeitos processuais. Por isso, calculo e causa da recusa devem acompanhar a "
                "medida. Usar consignacao como simples conta paralela, sem enfrentar reajuste valido "
                "ou acordo comprovado, pode deixar diferencas em aberto."
            ),
        ],
        "faq": [
            faq("Posso apenas continuar transferindo o aluguel antigo?", "Se o valor e o meio sao aceitos, preserve recibos. Havendo recusa, nao basta pagar informalmente: o artigo 67 e a consignacao judicial podem ser necessarios para liberar a obrigacao."),
            faq("O locador pode propor aumento antes do aniversario?", "Pode propor, mas a alteracao depende de acordo. Sem consenso, continuam a clausula valida e, quando cabivel, a revisional trienal."),
            faq("Consignar torna meu valor definitivo?", "Nao. O deposito procura liberar a prestacao discutida; o locador pode alegar insuficiencia e o processo definira o valor correto. A memoria de calculo, a oferta recusada e o contrato devem acompanhar a medida desde o primeiro deposito."),
        ],
        "official_sources": [
            source(LEI + "#art18", "Lei 8.245/1991, arts. 18 e 19", "acordo para novo valor e revisao trienal"),
            source(LEI + "#art67", "Lei 8.245/1991, art. 67", "consignacao judicial de aluguel e acessorios"),
        ],
    },
    "imob-multa-juros-aluguel-atrasado": {
        "opening": (
            "Multa, juros e atualizacao exercem funcoes distintas, mas nao podem ser somados sem "
            "ler o contrato e a lei vigente. A Lei 14.905/2024 mudou o artigo 406 do Codigo Civil: "
            "quando nao ha taxa convencionada, a taxa legal parte da Selic menos a atualizacao "
            "monetaria, evitando duplicidade."
        ),
        "sections": [
            section(
                "A multa nasce da clausula e tem limites civis",
                "A Lei do Inquilinato nao fixa percentual unico de multa para aluguel. O contrato "
                "deve ser conferido, e os artigos 412 e 413 do Codigo Civil impedem que a clausula "
                "penal exceda a obrigacao principal e permitem reducao equitativa quando houve "
                "cumprimento parcial ou excesso manifesto. O teto de dois por cento do credito ao "
                "consumidor nao pode ser transportado automaticamente a toda locacao civil."
            ),
            section(
                "A taxa legal mudou com a Lei 14.905 de 2024",
                "O artigo 406 atual determina taxa legal quando os juros nao foram convencionados, "
                "foram previstos sem percentual ou decorrem da lei. Ela corresponde a Selic menos o "
                "indice de atualizacao monetaria do artigo 389, conforme metodologia regulamentada. "
                "Se o resultado for negativo, considera-se zero. A antiga referencia generica aos "
                "tributos federais nao descreve mais a redacao vigente."
            ),
            section(
                "Atualizacao supletiva e juros nao devem repetir a inflacao",
                "Sem indice convencionado ou lei especifica, o artigo 389 usa o IPCA como atualizacao "
                "supletiva. Como a taxa legal do artigo 406 ja deduz essa atualizacao da Selic, nao se "
                "soma novamente a Selic integral ao IPCA. O calculo deve manter atualizacao monetaria "
                "e juros em componentes coerentes, sem duplicidade. Dividas que atravessam a entrada "
                "em vigor da Lei 14.905/2024 exigem analise temporal."
            ),
            section(
                "Planilha deve reproduzir contrato, datas e pagamentos",
                "Separe principal de cada mes, vencimento, multa, taxa de juros, indice e abatimentos. "
                "Verifique se encargos incidiram sobre parcela ja paga ou se houve capitalizacao nao "
                "prevista. Divergencia deve ser contestada item a item, sem assumir que todo acrescimo "
                "e abusivo ou que a taxa contratual sempre prevalece."
            ),
        ],
        "faq": [
            faq("A multa de aluguel e sempre limitada a dois por cento?", "Nao. Esse limite nao se aplica automaticamente a toda locacao civil; valem contrato, artigos 412 e 413 e controle concreto de excesso."),
            faq("Posso somar IPCA e Selic integral quando nao ha clausula?", "Nao pela sistematica vigente. A Lei 14.905 define taxa legal como Selic menos atualizacao monetaria, justamente para evitar duplicidade com o artigo 389."),
            faq("Qual taxa vale para atraso iniciado antes de 2024?", "Divida que atravessa a mudanca legislativa exige analise temporal das parcelas e da entrada em vigor. Nao aplique a formula nova retroativamente sem conferir o periodo juridico."),
        ],
        "official_sources": [
            source(CC + "#art406", "Codigo Civil, arts. 389 e 406", "IPCA supletivo e taxa legal vigente"),
            source(LAW_14905, "Lei 14.905/2024", "nova formula de atualizacao e juros legais"),
            source(CC + "#art412", "Codigo Civil, arts. 412 e 413", "limite e reducao da clausula penal"),
        ],
    },
    "imob-desconto-pontualidade": {
        "opening": (
            "Perder desconto e pagar multa no mesmo boleto nao configura sempre dupla punicao. O "
            "precedente especifico do STJ exige olhar a estrutura contratual: qual e o aluguel cheio, "
            "qual data gera a bonificacao e quando nasce a mora. Rotulos nao substituem essa "
            "comparacao, e um abatimento artificial pode receber tratamento diferente."
        ),
        "sections": [
            section(
                "Bonificacao e multa possuem fatos geradores distintos",
                "No REsp 1.745.916/PR, o STJ concluiu que o desconto de pontualidade recompensa o "
                "pagamento tempestivo, enquanto a multa sanciona o atraso. Por isso, a perda do abono "
                "e a multa nao sao sempre dupla punicao. O julgamento admitiu a multa sobre o valor "
                "integral do aluguel previsto no contrato, apesar da perda do desconto.\n\n"
                "Isso nao cria validacao abstrata de qualquer planilha. E preciso identificar se o "
                "valor cheio era realmente a obrigacao contratada e se a data do bonus e a data de "
                "vencimento foram descritas de modo inteligivel."
            ),
            section(
                "Estrutura contratual separa incentivo de multa escondida",
                "Um contrato pode prever aluguel cheio e abatimento para pagamento ate a data "
                "combinada. Se, porem, o chamado valor cheio so aparece depois do atraso e nao "
                "funciona como preco real da locacao, a qualificacao pode ser discutida. Historico de "
                "boletos, recibos e ofertas ajuda a mostrar como a clausula foi executada.\n\n"
                "O REsp 832.293/PR tambem enfatizou a compatibilidade entre as datas de bonus e multa. "
                "Nao basta somar percentuais: a analise pergunta quando cada efeito nasce e sobre qual "
                "base."
            ),
            section(
                "Excesso manifesto continua sujeito ao Codigo Civil",
                "Os artigos 412 e 413 limitam e permitem reduzir clausula penal excessiva. Esses "
                "dispositivos nao convertem automaticamente o desconto em penalidade, mas ajudam a "
                "examinar multa e demais sancoes quando o resultado global e manifestamente "
                "desproporcional. Um dia de atraso, sozinho, nao garante reducao judicial; valor, "
                "redacao e execucao importam."
            ),
            section(
                "Calculo deve partir do aluguel integral identificado",
                "Monte uma linha com valor cheio, desconto, vencimento normal, data paga, multa, juros "
                "e correcao. Compare-a com a clausula e com meses anteriores. Se a imobiliaria usou "
                "base diferente ou antecipou a mora, a contestacao deve apontar exatamente o erro, "
                "em vez de afirmar genericamente que toda acumulacao e proibida."
            ),
            section(
                "Prova documental permite uma avaliacao sem promessas",
                "Contrato completo, boletos com as duas datas, recibos e comunicacoes mostram o "
                "funcionamento real. Uma orientacao juridica pode qualificar a clausula e recalcular "
                "o debito. O precedente do STJ impede prometer exclusao da multa apenas porque houve "
                "perda de desconto; tambem nao impede discutir estrutura artificial ou excesso "
                "comprovado."
            ),
            section(
                "Datas diferentes tornam o incentivo mais transparente",
                "Quando o desconto vale para pagamento antes do vencimento normal e o valor cheio "
                "vence em data posterior claramente indicada, a funcao premial fica mais visivel. Se "
                "ambos aparecem na mesma data, ainda e necessario examinar o precedente aplicavel, a "
                "forma como o preco foi anunciado e o historico do contrato. Nenhum desses sinais "
                "resolve sozinho a validade, mas eles impedem que o calculo seja decidido apenas pelo "
                "nome dado a clausula."
            ),
            section(
                "Percentual do bonus nao tem teto locaticio automatico",
                "A lei nao fixa percentual universal para desconto de pontualidade. Quanto maior a "
                "diferenca entre valor cheio e pago habitualmente, mais importante demonstrar que o "
                "primeiro era preco real e informado. O controle de excesso considera a operacao "
                "inteira, e nao a importacao mecanica do limite de multa de relacoes de consumo. A "
                "conclusao deve vir da clausula, do comportamento e dos precedentes, sem prometer "
                "reducao por um numero isolado."
            ),
        ],
        "faq": [
            faq("Desconto perdido e multa sempre configuram bis in idem?", "Nao. O STJ admite a coexistencia quando a estrutura contratual distingue bonificacao por pontualidade e sancao por mora."),
            faq("A multa incide sobre o valor com desconto?", "No REsp 1.745.916, incidiu sobre o aluguel integral pactuado. A resposta concreta depende de qual valor o contrato define como obrigacao principal."),
            faq("Um atraso de um dia garante reducao da cobranca?", "Nao. Duracao do atraso e relevante, mas nao decide sozinha. Redacao, valor cheio real, datas, multa e eventual excesso precisam ser avaliados em conjunto a luz dos precedentes. Compare boletos anteriores, recibos e a proposta original para confirmar se a bonificacao era oferecida de modo consistente, em vez de surgir apenas depois da mora como acrescimo inesperado sem base no historico contratual anterior."),
        ],
        "official_sources": [
            source(STJ_RESP_1745916, "STJ, REsp 1.745.916/PR", "desconto de pontualidade e multa possuem hipoteses distintas"),
            source(
                "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20151028&formato=PDF&nreg=200600689797&salvar=false&seq=1423390&tipo=0",
                "STJ, REsp 832.293/PR",
                "compatibilidade das datas do bonus e da multa"
            ),
            source(CC + "#art412", "Codigo Civil, arts. 412 e 413", "limite e reducao equitativa da penalidade"),
        ],
    },
    "imob-devolucao-antecipada-multa": {
        "opening": (
            "No prazo determinado, o locatario pode devolver o imovel pagando a multa pactuada de "
            "forma proporcional. No prazo indeterminado, a regra muda: o artigo 6 exige aviso escrito "
            "de trinta dias ou permite cobrar um mes de aluguel e encargos pela falta do aviso. "
            "Misturar os dois regimes produz cobranca errada."
        ),
        "sections": [
            section(
                "O artigo 4 rege a saida durante o prazo determinado",
                "A multa contratual deve ser reduzida proporcionalmente ao periodo de cumprimento. "
                "Uma forma usual calcula a fracao do prazo que restava sobre o prazo total e a aplica "
                "a multa cheia, mas a clausula e as datas precisam ser conferidas. Exemplo: multa de "
                "tres alugueis em contrato de trinta meses, com vinte meses restantes, resulta em "
                "dois alugueis, antes de outros acertos legitimos.\n\n"
                "Se nao houve multa pactuada, o artigo 4 nao autoriza inventar qualquer percentual. "
                "Eventual prejuizo e outras obrigacoes seguem fundamentos proprios e precisam de "
                "demonstracao."
            ),
            section(
                "Nao existe aviso previo generico criado pelo artigo 4",
                "Para devolucao no prazo determinado, o artigo 4 trata da multa proporcional e nao "
                "exige aviso previo generico adicional. O contrato pode disciplinar comunicacao e "
                "procedimento de chaves, mas cobrar automaticamente um mes como se a locacao ja fosse "
                "indeterminada confunde regimes. Clausula e eventual excesso podem ser revistos "
                "judicialmente.\n\n"
                "A comunicacao escrita continua sendo pratica probatoria importante: fixa a data "
                "pretendida, permite vistoria e reduz disputa sobre entrega. Sua utilidade nao deve "
                "ser apresentada como penalidade legal inexistente."
            ),
            section(
                "O artigo 6 reserva trinta dias ao prazo indeterminado",
                "Depois que a locacao se torna indeterminada, o locatario pode denuncia-la mediante "
                "aviso escrito ao locador com antecedencia minima de 30 dias. Sem o aviso, o locador "
                "pode exigir quantia correspondente a um mes de aluguel e encargos vigentes. Nessa "
                "fase nao se aplica multa por romper prazo que ja terminou, salvo outra obrigacao "
                "autonoma validamente demonstrada."
            ),
            section(
                "Entrega de chaves encerra uso sem apagar acertos",
                "Multa, danos e contas podem ser apurados depois; condicionar o recebimento das chaves "
                "a concordancia com vistoria prolonga indevidamente a locacao. Em decisao divulgada "
                "em 2026 no REsp 2.220.656, o STJ afastou alugueis dos fiadores quando o locador "
                "recusou as chaves por esse motivo. Se houver recusa, documente-a e avalie meio "
                "formal ou judicial de entrega.\n\n"
                "Isso nao perdoa avarias. Danos comprovados podem ser cobrados separadamente, sem "
                "transformar a posse das chaves em instrumento para impor quitacao unilateral."
            ),
            section(
                "Datas e clausula produzem um calculo auditavel",
                "Reuna inicio, termino previsto, data efetiva de entrega, valor do aluguel e texto da "
                "multa. Separe caução, contas e vistoria. Uma avaliacao juridica pode conferir a "
                "proporcao, a fase determinada ou indeterminada e eventual excecao por transferencia "
                "de trabalho. Nao se deve prometer isencao sem analisar esses elementos."
            ),
            section(
                "Fracoes de mes e data efetiva pedem criterio explicito",
                "Se a entrega ocorre no meio do mes, o calculo da multa deve usar a unidade e o "
                "criterio previstos ou justificaveis, sem arredondar automaticamente todo periodo "
                "contra uma parte. Aluguel pelo tempo de ocupacao, multa pelo prazo restante e "
                "encargos de consumo sao rubricas separadas. Uma memoria transparente informa datas, "
                "formula e arredondamento, permitindo conferir se a proporcionalidade foi preservada."
            ),
            section(
                "Transferencia pelo empregador e excecao autonoma",
                "O paragrafo unico do artigo 4 dispensa a multa quando a devolucao decorre de "
                "transferencia pelo empregador para outra localidade e o locador recebe aviso escrito "
                "com trinta dias. Nessa situacao, nao se calcula apenas uma multa menor: examina-se "
                "isencao. Mudanca voluntaria, novo emprego ou comunicacao tardia nao devem ser "
                "equiparados sem prova aos requisitos legais."
            ),
        ],
        "faq": [
            faq("Prazo determinado exige sempre aviso de trinta dias?", "Nao pelo artigo 4. Ele exige multa proporcional; o aviso legal de trinta dias do artigo 6 pertence a locacao por prazo indeterminado."),
            faq("O locador pode recusar chaves ate eu aceitar a vistoria?", "Avarias podem ser cobradas separadamente. A recusa deve ser documentada e pode exigir entrega formal ou judicial para evitar alugueis posteriores."),
            faq("Como calcular quando faltam dias, e nao meses inteiros?", "Use datas e a unidade coerente com contrato e periodo total, explicando qualquer fracao e arredondamento. Nao converta automaticamente parte de mes em mes cheio contra uma das partes. Separe esse calculo do aluguel e dos encargos efetivamente devidos ate a entrega documentada das chaves ao locador responsavel."),
        ],
        "official_sources": [
            source(LEI + "#art4", "Lei 8.245/1991, art. 4", "multa proporcional no prazo determinado e excecao de transferencia"),
            source(LEI + "#art6", "Lei 8.245/1991, art. 6", "aviso de trinta dias no prazo indeterminado"),
            source(
                "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/16012026-Fiador-fica-liberado-dos-alugueis-se-o-locador-se-recusa-a-receber-as-chaves.aspx",
                "STJ, REsp 2.220.656/RS",
                "recusa de chaves por discordancia de vistoria nao prolonga responsabilidade do fiador"
            ),
        ],
    },
    "imob-transferencia-trabalho-sem-multa": {
        "opening": (
            "A transferencia feita pelo empregador, publico ou privado, para prestar servicos em "
            "localidade diferente daquela do inicio do contrato pode afastar a multa de saida. O "
            "beneficio exige nexo entre transferencia e devolucao, alem de aviso escrito ao locador "
            "com pelo menos trinta dias. Mudanca pessoal de emprego nao e automaticamente igual."
        ),
        "sections": [
            section(
                "O paragrafo unico do artigo 4 tem requisitos cumulativos",
                "A dispensa alcanca o locatario transferido pelo seu empregador para prestar servicos "
                "em outra localidade. A lei menciona expressamente empregador privado ou publico. A "
                "saida deve decorrer dessa transferencia e ser comunicada por escrito ao locador com "
                "antecedencia minima de 30 dias. Sem um desses elementos, a multa proporcional do "
                "prazo determinado pode continuar em discussao.\n\n"
                "A norma nao exige cargo especifico nem tempo minimo no emprego. O ponto e demonstrar "
                "uma decisao atribuivel ao empregador e a mudanca do local de prestacao em relacao ao "
                "inicio da locacao."
            ),
            section(
                "Carta do empregador deve explicar local e data",
                "Um documento util identifica empresa ou orgao, trabalhador, lotacao anterior, nova "
                "localidade, data de inicio e carater da transferencia. E-mail sem autoria ou simples "
                "declaracao do locatario pode ser insuficiente. Se a empresa usa regime remoto ou "
                "multiplos postos, explique por que a mudanca exige a devolucao do imovel.\n\n"
                "Localidade diversa nao deve ser reduzida mecanicamente a fronteira municipal nem "
                "ampliada a qualquer troca de unidade proxima. Distancia, local inicial descrito no "
                "contrato e efetiva alteracao da prestacao precisam ser provados no caso concreto."
            ),
            section(
                "Pedido voluntario e transferencia empresarial nao se confundem",
                "Se o trabalhador escolheu mudar e depois obteve anuencia da empresa, pode haver "
                "controversia sobre quem determinou a transferencia. Aumento salarial ou interesse "
                "pessoal nao decide sozinho; comunicados, politicas e aditivos mostram a origem da "
                "medida. O texto legal nao cobre automaticamente troca de emprego para outra empresa "
                "ou decisao pessoal de trabalhar em cidade diferente."
            ),
            section(
                "A isencao afasta a multa, nao todas as contas da locacao",
                "Aluguel ate a entrega, consumo, condominio atribuido ao locatario e danos comprovados "
                "continuam sujeitos ao acerto. A transferencia tambem nao elimina a necessidade de "
                "devolver chaves e documentar vistoria. Caucao e demais garantias sao liberadas depois "
                "da reconciliacao, sem penalidade adicional apenas pelo uso da excecao.\n\n"
                "O aviso de trinta dias deve indicar a base legal, anexar prova e propor data de "
                "vistoria. Guarde o recebimento; mensagem enviada sem prova pode gerar disputa sobre "
                "o requisito temporal."
            ),
            section(
                "Resposta do locador deve ser enfrentada com documentos",
                "Se houver recusa, identifique qual requisito e contestado: empregador, localidade, "
                "causalidade ou prazo. Uma orientacao juridica pode revisar a carta, responder e "
                "calcular o valor controvertido. Nao e possivel garantir isencao apenas com uma oferta "
                "de emprego ou com a intencao de mudar.\n\n"
                "Pagar valor incontroverso e preservar a prova evita que a discussao da multa se "
                "misture com inadimplementos independentes. A estrategia judicial depende da "
                "qualidade dos documentos e da cronologia."
            ),
            section(
                "Empregado publico e privado recebem a mesma referencia legal",
                "A redacao inclui transferencia por empregador privado ou publico. Servidor removido "
                "por ato da administracao deve apresentar o ato e a nova lotacao; empregado de "
                "empresa pode usar carta ou aditivo idoneo. Em ambos, a denominacao funcional nao "
                "substitui o nexo com a mudanca. Autonomo, socio ou prestador sem relacao de emprego "
                "pode ter outros fundamentos contratuais, mas nao entra automaticamente na excecao "
                "destinada ao locatario transferido pelo empregador."
            ),
            section(
                "Aviso legal e entrega devem caber no cronograma",
                "A antecedencia minima se relaciona a devolucao comunicada. Se a ordem de "
                "transferencia chega em prazo menor, registre a data e negocie uma entrega compativel; "
                "o texto legal nao cria dispensa expressa do aviso pela urgencia empresarial. A "
                "negociacao pode afastar conflito, mas deve indicar se houve renuncia a multa ou "
                "apenas tolerancia de alguns dias."
            ),
        ],
        "faq": [
            faq("Trocar de empresa afasta a multa?", "Nao automaticamente. A excecao se refere a transferencia do locatario pelo empregador, publico ou privado, para outra localidade."),
            faq("O aviso de trinta dias pode ser verbal?", "A lei exige notificacao escrita. Preserve conteudo, anexos e prova de recebimento pelo locador."),
            faq("Servidor removido pode usar a excecao?", "Pode se o ato do empregador publico transferir a prestacao para localidade diversa e houver aviso escrito no prazo. O ato de remocao, a nova lotacao e a cronologia precisam ser demonstrados."),
        ],
        "official_sources": [
            source(LEI + "#art4", "Lei 8.245/1991, art. 4, paragrafo unico", "transferencia pelo empregador e notificacao de trinta dias"),
        ],
    },
    "imob-contrato-curto-prorrogacao": {
        "opening": (
            "Na locacao residencial verbal ou escrita por menos de 30 meses, o fim do prazo nao abre "
            "denuncia vazia imediata. O artigo 47 prorroga o contrato automaticamente por prazo "
            "indeterminado e restringe a retomada. A espera de trinta dias pertence ao artigo 46, "
            "para contrato residencial de 30 meses ou mais, nao ao contrato curto."
        ),
        "sections": [
            section(
                "O artigo 47 prorroga sem carencia de trinta dias",
                "A regra alcanca locacao residencial ajustada verbalmente ou por escrito por prazo "
                "inferior a 30 meses. Findo o prazo, ela se torna indeterminada automaticamente. Nao "
                "e necessario que o locatario permaneça mais trinta dias para produzir esse efeito. "
                "Pagamento e recibos continuam importantes para provar valor e demais condicoes."
            ),
            section(
                "Retomada fica limitada as hipoteses legais",
                "O imovel pode ser retomado nos casos do artigo 9; por extincao de contrato de "
                "trabalho ligado a ocupacao; para uso proprio, do conjuge ou companheiro, ou uso "
                "residencial de ascendente ou descendente nas condicoes legais; para demolicao ou "
                "obra com os requisitos do inciso IV; ou quando a vigencia ininterrupta ultrapassa "
                "cinco anos. A simples vontade do locador antes desses cinco anos nao basta."
            ),
            section(
                "O artigo 46 cuida do residencial de 30 meses ou mais",
                "No contrato escrito por prazo igual ou superior a 30 meses, o termino resolve a "
                "locacao independentemente de aviso. Se o locatario permanece mais de trinta dias "
                "sem oposicao, surge prorrogacao indeterminada e o locador pode denuncia-la com trinta "
                "dias para desocupacao. Transportar essa regra ao artigo 47 elimina indevidamente a "
                "protecao do contrato curto."
            ),
            section(
                "O artigo 57 e proprio da locacao nao residencial",
                "Na locacao nao residencial por prazo indeterminado, o artigo 57 permite denuncia por "
                "escrito com trinta dias para desocupacao. Ele nao deve ser usado para criar denuncia "
                "vazia de residencia curta. Antes de responder a notificacao, identifique finalidade, "
                "forma escrita ou verbal, prazo original e tempo total ininterrupto."
            ),
        ],
        "faq": [
            faq("Preciso ficar trinta dias apos o vencimento para o artigo 47 valer?", "Nao. A prorrogacao do contrato residencial inferior a 30 meses e automatica no fim do prazo; a espera de trinta dias esta no artigo 46."),
            faq("Depois de cinco anos o locador pode denunciar?", "O inciso V do artigo 47 admite retomada quando a vigencia ininterrupta ultrapassa cinco anos, observados notificacao e procedimento aplicaveis."),
            faq("O artigo 57 vale para meu apartamento residencial?", "Nao. O artigo 57 trata da locacao nao residencial indeterminada. A residencia curta continua submetida ao artigo 47 e as hipoteses nele previstas."),
        ],
        "official_sources": [
            source(LEI + "#art46", "Lei 8.245/1991, art. 46", "residencial escrito por 30 meses ou mais"),
            source(LEI + "#art47", "Lei 8.245/1991, art. 47", "prorrogacao e retomada da locacao residencial curta"),
            source(LEI + "#art57", "Lei 8.245/1991, art. 57", "denuncia da locacao nao residencial indeterminada"),
        ],
    },
    "imob-morte-locatario-quem-fica": {
        "opening": (
            "A morte do titular nao encerra automaticamente toda locacao residencial. O artigo 11 "
            "transfere direitos e obrigacoes a pessoas que ja residiam no imovel, seguindo ordem "
            "legal. Essa sub-rogacao nao significa manutencao da fianca original: o STJ distingue a "
            "continuidade da locacao da garantia pessoal."
        ),
        "sections": [
            section(
                "O artigo 11 define quem se sub-roga na residencia",
                "Primeiro aparecem o conjuge sobrevivente ou companheiro. Sucessivamente, podem "
                "sub-rogar-se os herdeiros necessarios e as pessoas que viviam na dependencia "
                "economica do falecido, desde que residissem no imovel. Ser herdeiro sem morar ali "
                "nao basta. A prova pode incluir documentos de domicilio, contas, cadastro e a "
                "realidade da convivencia."
            ),
            section(
                "Sub-rogacao transmite a posicao contratual",
                "Quem se enquadra assume direitos e obrigacoes da locacao a partir do obito. Nao e "
                "preciso aguardar o inventario para que a regra locaticia exista, mas comunicar o "
                "locador por escrito, apresentar certidao e identificar o novo responsavel reduz "
                "incerteza de boletos e notificacoes. O artigo 11 nao cria a janela de 30 dias e o "
                "residual de 120 dias do artigo 12, que trata de separacao e divorcio."
            ),
            section(
                "O REsp 439.945 extingue a fianca para obrigacoes posteriores",
                "No REsp 439.945/RS, o STJ decidiu que a morte do locatario afiançado extingue a "
                "fianca para obrigacoes posteriores, apesar da sub-rogacao prevista no artigo 11. O "
                "fiador nao responde por obrigacoes posteriores ao obito apenas porque o contrato "
                "dizia durar ate a entrega das chaves. Debitos anteriores permanecem sujeitos ao "
                "alcance original da garantia."
            ),
            section(
                "Nova garantia e permanencia exigem formalizacao",
                "Com a garantia pessoal extinta para o periodo novo, locador e sub-rogado devem "
                "examinar como a locacao prosseguira. Eventual nova garantia depende de instrumento "
                "valido e nao pode ser imposta retroativamente. Contrato, certidao de obito, prova de "
                "residencia e termo de fianca permitem separar o que continua do que terminou."
            ),
        ],
        "faq": [
            faq("Qualquer filho pode assumir o aluguel?", "Nao. O artigo 11 exige a ordem legal e residencia no imovel; parentes que moravam em outro local nao se sub-rogam apenas pela heranca."),
            faq("O fiador continua apos a morte?", "O STJ, no REsp 439.945, afastou a fianca para obrigacoes posteriores ao obito, mesmo havendo sub-rogacao da locacao."),
            faq("Precisa concluir inventario para continuar morando?", "A sub-rogacao locaticia decorre do artigo 11 e nao aguarda a partilha, mas quem permanece deve provar enquadramento e comunicar o locador para organizar pagamentos, documentos e eventual nova garantia."),
        ],
        "official_sources": [
            source(LEI + "#art11", "Lei 8.245/1991, art. 11", "ordem e residencia exigidas para sub-rogacao por morte"),
            source(STJ_RESP_439945, "STJ, REsp 439.945/RS", "extincao da fianca quanto a obrigacoes posteriores ao obito"),
        ],
    },
    "imob-dividas-locatario-falecido": {
        "opening": (
            "Alugueis vencidos antes do obito, obrigacoes surgidas depois e divida garantida por "
            "fianca nao formam um bloco unico. O espolio responde pelo passivo anterior com a heranca; "
            "quem se sub-roga assume o periodo novo; e o STJ limita a fianca original as obrigacoes "
            "anteriores a morte. Cronologia e documentos definem contra quem cobrar."
        ),
        "sections": [
            section(
                "O espolio concentra as dividas existentes ate a morte",
                "Alugueis e encargos ja vencidos integram o passivo hereditario. Durante o inventario, "
                "o espolio, representado pelo inventariante, pode responder conforme as regras "
                "processuais. A forma de apresentar ou cobrar o credito depende da existencia de "
                "inventario, liquidez e documentos; habilitacao nao deve ser anunciada como unico "
                "caminho possivel em qualquer situacao."
            ),
            section(
                "Herdeiro nao paga alem das forcas da heranca",
                "O artigo 1.792 do Codigo Civil limita os encargos ao patrimonio herdado. Feita a "
                "partilha, o artigo 1.997 distribui responsabilidade entre herdeiros na proporcao da "
                "parte recebida. Isso nao autoriza escolher um familiar e cobrar todo o debito de seu "
                "patrimonio pessoal sem examinar espolio, partilha, garantia e eventual obrigacao "
                "propria."
            ),
            section(
                "O artigo 11 separa o periodo posterior pela sub-rogacao",
                "Conjuge, companheiro e, sucessivamente, herdeiros necessarios ou dependentes que "
                "residiam no imovel podem assumir a locacao. A partir dai, alugueis do uso continuado "
                "nao sao simplesmente dividas do falecido: pertencem a relacao sub-rogada. Data do "
                "obito, permanencia, entrega de chaves e pagamentos devem ser reconciliados."
            ),
            section(
                "Fiador responde ate a morte, nao pelo periodo novo",
                "O REsp 439.945/RS reconhece que o fiador responde pelas dividas anteriores cobertas "
                "pelo contrato, mas a fianca se extingue para obrigacoes posteriores ao obito do "
                "locatario, apesar da sub-rogacao. Nao depende de uma exoneracao feita pelo fiador "
                "depois da morte para cortar o periodo novo. O valor anterior ainda exige conferir "
                "alcance, pagamentos e prescricao."
            ),
        ],
        "faq": [
            faq("Posso cobrar toda a divida de um unico herdeiro?", "Nao sem examinar o caso. A heranca limita a responsabilidade, e depois da partilha cada herdeiro responde na proporcao recebida, salvo obrigacao propria diversa."),
            faq("Fiador paga alugueis apos o obito?", "Segundo o REsp 439.945, nao as obrigacoes posteriores: a fianca original se extingue para o novo periodo, embora cubra debitos anteriores dentro de seus limites."),
            faq("Aluguel de quem ficou no imovel entra sempre no espolio?", "Nao. Depois da sub-rogacao, o periodo novo pertence a relacao assumida por quem permaneceu. Datas de obito, ocupacao, pagamentos e entrega das chaves separam os debitos."),
        ],
        "official_sources": [
            source(CC + "#art1792", "Codigo Civil, arts. 1.792 e 1.997", "limite da heranca e responsabilidade apos a partilha"),
            source(LEI + "#art11", "Lei 8.245/1991, art. 11", "sub-rogacao da locacao residencial por morte"),
            source(STJ_RESP_439945, "STJ, REsp 439.945/RS", "fianca anterior e extincao quanto a obrigacoes posteriores"),
        ],
    },
    "imob-divorcio-inquilinos-locacao": {
        "opening": (
            "Na separacao de fato, separacao judicial, divorcio ou dissolucao de uniao estavel, a "
            "locacao residencial prossegue automaticamente com quem permanece no imovel. O artigo 12 "
            "exige comunicacao escrita ao locador e ao fiador. Essa noticia abre prazo de 30 dias para "
            "exoneracao e, se exercida, responsabilidade residual de 120 dias."
        ),
        "sections": [
            section(
                "O artigo 12 transfere a locacao a quem permanece",
                "A sub-rogacao decorre da lei e nao depende de novo contrato mais oneroso. Ela alcanca "
                "separacao de fato, separacao judicial, divorcio e dissolucao de uniao estavel. Quem "
                "fica assume a posicao locaticia; quem saiu deve preservar prova da data e da "
                "comunicacao, pois boletos em nome antigo podem esconder que a administradora ainda "
                "nao atualizou o cadastro."
            ),
            section(
                "Locador e fiador precisam receber comunicacao escrita",
                "O paragrafo 1 exige noticia por escrito ao locador e, se a garantia for fianca, ao "
                "fiador. Certidao, escritura, decisao ou declaracao de separacao de fato podem "
                "acompanhar a mensagem conforme o caso. Conteudo, recebimento e data importam mais "
                "que o canal usado, porque acionam direitos da garantia."
            ),
            section(
                "Fiador tem 30 dias e permanece por mais 120 apos notificar",
                "Recebida a comunicacao, o fiador pode exonerar-se no prazo de 30 dias. Se o fizer, "
                "continua responsavel pelos efeitos da fianca durante 120 dias depois de notificar o "
                "locador. O Informativo 660 do STJ, no REsp 1.510.503, admite que ciencia inequivoca "
                "obtida de outra forma inicie a janela, pois a finalidade da comunicacao prevalece "
                "sobre formalismo vazio."
            ),
            section(
                "Exoneracao pode gerar pedido de nova garantia em trinta dias",
                "O artigo 40, inciso VIII, inclui a exoneracao decorrente do artigo 12 entre as causas "
                "de substituicao. O locador pode notificar o sub-rogado para apresentar nova garantia "
                "no prazo de 30 dias. Esse prazo de substituicao e diferente da janela dada ao fiador "
                "e do residual de 120 dias, embora os tres marcos possam aparecer na mesma cronologia."
            ),
            section(
                "Divida anterior nao e automaticamente dos dois ex-parceiros",
                "Responsabilidade por alugueis anteriores depende de quem assinou como locatario, "
                "solidariedade, regime patrimonial, beneficio a familia e momento da obrigacao. O "
                "divorcio nao apaga divida valida, mas tambem nao permite afirmar que ambos sempre "
                "respondem. Contrato, comprovantes, comunicacao e acordo ou decisao da separacao "
                "precisam ser lidos conjuntamente."
            ),
        ],
        "faq": [
            faq("Preciso esperar o divorcio terminar?", "Nao. O artigo 12 inclui separacao de fato, mas a comunicacao escrita e a prova de quem permaneceu sao essenciais."),
            faq("A fianca termina no dia da separacao?", "Nao nessa hipotese. O fiador tem 30 dias para exonerar-se apos a comunicacao e permanece por 120 dias depois de notificar o locador."),
        ],
        "official_sources": [
            source(LEI + "#art12", "Lei 8.245/1991, art. 12", "sub-rogacao, comunicacao, janela de 30 dias e residual de 120 dias"),
            source(LEI + "#art40", "Lei 8.245/1991, art. 40, VIII e paragrafo unico", "substituicao da garantia em trinta dias"),
            source(STJ_INFO_660, "STJ, Informativo 660, REsp 1.510.503/ES", "ciencia inequivoca e inicio do prazo de exoneracao"),
        ],
    },
}


def normalized_words(value):
    plain = "".join(
        char
        for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    total = len(normalized_words(page.get("opening", "")))
    for item in page.get("sections", []):
        total += len(normalized_words(item.get("heading", "")))
        total += len(normalized_words(item.get("text", "")))
    for item in page.get("faq", []):
        total += len(normalized_words(item.get("q", "")))
        total += len(normalized_words(item.get("a", "")))
    return total


def main():
    original = open(TARGET, "rb").read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS inicial falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    if len(pages) != 22 or len({page["intent_id"] for page in pages}) != 22:
        raise SystemExit("shard deveria conter 22 intents unicos")
    if set(UPDATES) != {page["intent_id"] for page in pages}:
        missing = sorted({page["intent_id"] for page in pages} - set(UPDATES))
        extra = sorted(set(UPDATES) - {page["intent_id"] for page in pages})
        raise SystemExit(f"cobertura integral ausente: missing={missing}, extra={extra}")

    page_types = {}
    with open("data/editorial/portfolio_v2/imobiliario.jsonl", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            page_types[record["intent_id"]] = record["page_type"]

    for page in pages:
        prior_sources = {item["url"]: item for item in page.get("official_sources", [])}
        update = UPDATES[page["intent_id"]]
        page.update(update)
        for field in ("title", "meta_description", "h1", "opening"):
            page[field] = restore_ptbr(page.get(field, ""))
        for item in page.get("sections", []):
            item["heading"] = restore_ptbr(item.get("heading", ""))
            item["text"] = restore_ptbr(item.get("text", ""))
        for item in page.get("faq", []):
            item["q"] = restore_ptbr(item.get("q", ""))
            item["a"] = restore_ptbr(item.get("a", ""))
        for item in page.get("official_sources", []):
            item["name"] = restore_ptbr(item.get("name", ""))
            item["anchor_claim"] = restore_ptbr(item.get("anchor_claim", ""))
        preserved = []
        for item in page["official_sources"]:
            merged = dict(item)
            previous = prior_sources.get(item["url"])
            if previous:
                if "verified_at" in previous:
                    merged["verified_at"] = previous["verified_at"]
                if "http_status" in previous:
                    merged["http_status"] = previous["http_status"]
            preserved.append(merged)
        page["official_sources"] = preserved
        page["word_count"] = body_word_count(page)
        expected = (700, 1400) if page_types[page["intent_id"]] == "guia_problema" else (400, 800)
        if not expected[0] <= page["word_count"] <= expected[1]:
            raise SystemExit(
                f"{page['intent_id']}: word_count={page['word_count']} fora de {expected}"
            )

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-02-review.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS falhou antes da promocao atomica")
        os.replace(temporary, TARGET)
        directory_fd = os.open(os.path.dirname(TARGET), os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(f"22 paginas revisadas; sha256={hashlib.sha256(rendered).hexdigest()}")
    for page in pages:
        print(f"{page['intent_id']}\t{page['word_count']}")


if __name__ == "__main__":
    main()
