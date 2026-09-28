#!/usr/bin/env python3
"""Restaura diacríticos e fecha as faixas dos guias de imobiliário-03."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-03.jsonl"
EXPECTED_SHA256 = "64871fb23c392928af766aed6dcaad7c3c8c07460167c9a7704cbf27e68e064f"

PAIRS = """
agua|água
alem|além
codigo|código
comunicacao|comunicação
consignacao|consignação
constituicao|constituição
desbotamento|desbotamento
elaboracao|elaboração
exclusoes|exclusões
inadimplencia|inadimplência
indenizacao|indenização
interdicao|interdição
ja|já
judiciario|judiciário
nao|não
negocios|negócios
notificacao|notificação
regularizacao|regularização
reiteracao|reiteração
repeticao|repetição
resilicao|resilição
resolucao|resolução
saida|saída
sublocacao|sublocação
tambem|também
acao|ação
acessao|acessão
acessorios|acessórios
adaptacoes|adaptações
adequacao|adequação
administracao|administração
afericao|aferição
alcanca|alcança
alegacao|alegação
alienacao|alienação
alteracao|alteração
ameaca|ameaça
antecedencia|antecedência
antemao|antemão
aplicacao|aplicação
aplicavel|aplicável
apropriacao|apropriação
aquisicao|aquisição
area|área
areas|áreas
assuncao|assunção
atribuicao|atribuição
atribuivel|atribuível
ausencia|ausência
aptidao|aptidão
automatica|automática
automatico|automático
autonoma|autônoma
autonomas|autônomas
autonomo|autônomo
autorizacao|autorização
autorizacoes|autorizações
averbacao|averbação
caracteristicas|características
cardapio|cardápio
cartorio|cartório
caucao|caução
certidao|certidão
cessao|cessão
ciencia|ciência
cisao|cisão
classificacao|classificação
cobranca|cobrança
combinacao|combinação
comeca|começa
comecar|começar
comissao|comissão
comparacao|comparação
compativeis|compatíveis
compativel|compatível
compensacao|compensação
comunicacoes|comunicações
concessao|concessão
conclusao|conclusão
concordancia|concordância
condicao|condição
condicoes|condições
condominio|condomínio
confirmacao|confirmação
confissao|confissão
construcao|construção
contestacao|contestação
conteudo|conteúdo
contratacao|contratação
convencao|convenção
conveniencia|conveniência
convivencia|convivência
cooperacao|cooperação
criancas|crianças
dacao|dação
debitos|débitos
decisao|decisão
defensavel|defensável
definicao|definição
depreciacao|depreciação
descricao|descrição
desocupacao|desocupação
destinacao|destinação
deterioracoes|deteriorações
determinacao|determinação
devolucao|devolução
diferenca|diferença
dificil|difícil
dinamica|dinâmica
discussao|discussão
discutiveis|discutíveis
disposicao|disposição
distribuicao|distribuição
distincao|distinção
doacao|doação
documentacao|documentação
dominio|domínio
duracao|duração
eletrica|elétrica
emergencia|emergência
emprestimo|empréstimo
espaco|espaço
estao|estão
estetico|estético
evolucao|evolução
excecao|exceção
exclusao|exclusão
excecoes|exceções
excluidas|excluídas
execucao|execução
exercicio|exercício
exigencia|exigência
exigiveis|exigíveis
exigivel|exigível
existencia|existência
explicacao|explicação
exposicao|exposição
extensao|extensão
fe|fé
fianca|fiança
fiduciaria|fiduciária
fisica|física
formalizacao|formalização
funcao|função
funcoes|funções
fusao|fusão
generica|genérica
generico|genérico
gestao|gestão
habitacoes|habitações
havera|haverá
hipotese|hipótese
hipoteses|hipóteses
historico|histórico
horario|horário
identificacao|identificação
identificavel|identificável
imobiliaria|imobiliária
imovel|imóvel
impermeabilizacao|impermeabilização
importancia|importância
impossivel|impossível
imputavel|imputável
incidencia|incidência
incorporacao|incorporação
indenizaveis|indenizáveis
indenizavel|indenizável
indispensavel|indispensável
inequivoco|inequívoco
inevitavel|inevitável
infiltracao|infiltração
infracao|infração
instalacao|instalação
instalacoes|instalações
integralizacao|integralização
intermediacao|intermediação
interrupcoes|interrupções
intervencao|intervenção
invasao|invasão
inviolavel|inviolável
invisivel|invisível
isencao|isenção
juridica|jurídica
jurisprudencia|jurisprudência
justificavel|justificável
leilao|leilão
locacao|locação
locatario|locatário
locaticia|locatícia
locaticio|locatício
mandatario|mandatário
manutencao|manutenção
manutencoes|manutenções
minima|mínima
modificacao|modificação
mudanca|mudança
mudancas|mudanças
necessaria|necessária
necessarias|necessárias
necessario|necessário
necessarios|necessários
obrigacao|obrigação
obrigacoes|obrigações
obrigatoria|obrigatória
obstrucao|obstrução
ocorrencia|ocorrência
ocupacao|ocupação
omissao|omissão
onus|ônus
opoe|opõe
oposicao|oposição
orcamento|orçamento
orcamentos|orçamentos
ordinarias|ordinárias
orientacao|orientação
padrao|padrão
paragrafos|parágrafos
perfuracao|perfuração
periodo|período
permanencia|permanência
permissao|permissão
perturbacao|perturbação
posicao|posição
possiveis|possíveis
possivel|possível
poupanca|poupança
preco|preço
prejuizo|prejuízo
prejuizos|prejuízos
preservacao|preservação
pressao|pressão
prestacao|prestação
presuncao|presunção
pretensao|pretensão
preve|prevê
previo|prévio
privacao|privação
probatoria|probatória
probatorio|probatório
proibe|proíbe
proibicao|proibição
propria|própria
proprias|próprias
proprietario|proprietário
proprio|próprio
protecao|proteção
proxima|próxima
qualificacao|qualificação
realizacao|realização
reclamacao|reclamação
reclamacoes|reclamações
recomendacao|recomendação
recomposicao|recomposição
redacao|redação
reforcam|reforçam
regulacao|regulação
relacao|relação
remedio|remédio
remedios|remédios
removivel|removível
remuneracao|remuneração
renovacao|renovação
reparacao|reparação
reparacoes|reparações
repercussao|repercussão
rescisao|rescisão
resistencia|resistência
responsaveis|responsáveis
restituicao|restituição
restituida|restituída
restricao|restrição
retencao|retenção
retransmissao|retransmissão
reversao|reversão
reversivel|reversível
revisao|revisão
sao|são
saude|saúde
secundario|secundário
seguranca|segurança
separacao|separação
servico|serviço
servicos|serviços
sistematica|sistemática
situacao|situação
situacoes|situações
so|só
solucao|solução
sublocacoes|sublocações
sublocatario|sublocatário
subsidiarios|subsidiários
substituicao|substituição
substituido|substituído
tecnica|técnica
tecnico|técnico
tecnicos|técnicos
tolerancia|tolerância
transferencia|transferência
tres|três
tubulacao|tubulação
unico|único
urgencia|urgência
usuario|usuário
util|útil
vedacao|vedação
ventilacao|ventilação
verificavel|verificável
vicios|vícios
videos|vídeos
violacao|violação
visivel|visível
voluptuarias|voluptuárias
"""

ACCENTS = dict(line.split("|", 1) for line in PAIRS.splitlines() if line)
TOKEN = re.compile(
    r"(?<![\w])(" + "|".join(sorted(map(re.escape, ACCENTS), key=len, reverse=True)) + r")(?![\w])",
    re.IGNORECASE,
)


def restore_accents(value):
    def replace(match):
        original = match.group(0)
        corrected = ACCENTS[original.lower()]
        if original.isupper():
            return corrected.upper()
        if original[:1].isupper():
            return corrected[:1].upper() + corrected[1:]
        return corrected

    return TOKEN.sub(replace, value or "")


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


def replace_section(page, heading, text):
    matches = [section for section in page["sections"] if section.get("heading") == heading]
    if len(matches) != 1:
        raise RuntimeError(f"{page['intent_id']}: seção {heading!r} encontrada {len(matches)} vez(es)")
    matches[0]["text"] = text


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page["intent_id"]: page for page in pages}

    visible_fields = ("title", "meta_description", "h1", "opening")
    for page in pages:
        for field in visible_fields:
            page[field] = restore_accents(page.get(field, ""))
        for section in page.get("sections", []):
            section["heading"] = restore_accents(section.get("heading", ""))
            section["text"] = restore_accents(section.get("text", ""))
        for item in page.get("faq", []):
            item["q"] = restore_accents(item.get("q", ""))
            item["a"] = restore_accents(item.get("a", ""))
        for item in page.get("official_sources", []):
            item["name"] = restore_accents(item.get("name", ""))
            item["anchor_claim"] = restore_accents(item.get("anchor_claim", ""))

    replace_section(
        by_intent["imob-visitas-imovel-a-venda"],
        "O que fazer diante de visitas fora de hora",
        "O primeiro passo é propor por escrito janelas de visita viáveis e pedir que cada horário seja confirmado. O morador pode solicitar a identificação do corretor e acompanhar o exame; não precisa entregar livre acesso, deixar estranhos sozinhos ou expor documentos e objetos pessoais. Ao mesmo tempo, deve oferecer alternativas reais para não transformar proteção da rotina em recusa permanente.\n\nSe houver ingresso sem consentimento, ameaça ou sequência incompatível com o que foi combinado, preserve mensagens e imagens antes de notificar locador e imobiliária. Eventual obrigação de não fazer ou reparação depende da gravidade e da prova. A resposta jurídica deve separar o direito de mostrar o bem do dever de respeitar posse, privacidade e segurança de quem reside nele.",
    )
    replace_section(
        by_intent["imob-obras-imovel-abatimento"],
        "Como calcular e negociar o abatimento devido",
        "A base temporal do artigo 26 é objetiva. Se um reparo urgente a cargo do locador durar dezoito dias, o período excedente ao décimo é de oito dias; o cálculo deve partir dessa fração do aluguel e dos documentos que fixam início e fim. Interrupção real da obra, acesso parcial e valores já ajustados precisam constar da memória de cálculo, sem transformar o abatimento legal em isenção integral.\n\nOutros prejuízos, como hospedagem ou dano a bens, não entram automaticamente nessa conta e exigem fundamento e prova próprios. A proposta ao locador deve discriminar período, valor incontroverso e quantia discutida. Na falta de acordo, não é prudente simplesmente reter todo o aluguel: consignação ou pedido judicial adequado evita que a reivindicação de desconto produza mora artificial.",
    )
    replace_section(
        by_intent["imob-taxa-contrato-cadastro"],
        "Como reagir a uma exigência de pagamento antes da assinatura",
        "Peça a tabela, o fundamento contratual, o destinatário do valor e a descrição do serviço antes de pagar. Se a verba remunera administração, intermediação, elaboração do instrumento ou aferição de idoneidade do candidato ou fiador, o artigo 22, VII, a atribui ao locador, mesmo quando a consulta é feita por empresa terceirizada. Recusar a tarifa não elimina a necessidade de fornecer documentos legítimos para análise cadastral.\n\nGuarde anúncio, proposta, boleto e resposta da imobiliária. O artigo 43, I, trata como contravenção a exigência, por motivo de locação ou sublocação, de quantia além do aluguel e encargos permitidos; o enquadramento depende dos fatos e não deve ser proclamado sem examinar a cobrança. Para recuperar valor já pago, é preciso demonstrar quem recebeu, por qual rubrica e por que a obrigação era do locador.",
    )
    taxa = by_intent["imob-taxa-contrato-cadastro"]
    art43 = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art43"
    if not any(item.get("url") == art43 for item in taxa["official_sources"]):
        taxa["official_sources"].append({
            "url": art43,
            "name": "Lei 8.245/1991, art. 43, I",
            "anchor_claim": "contravenção por exigir quantia além do aluguel e encargos permitidos",
        })

    for page in pages:
        page["word_count"] = body_word_count(page)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-03-ptbr.", dir=directory)
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

    print(f"PT-BR restaurado em {len(pages)} páginas; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
