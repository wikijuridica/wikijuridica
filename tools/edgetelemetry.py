"""edgetelemetry — plausibilidade FÍSICA da telemetria de bot da borda.

POR QUE UM MÓDULO, E NÃO UMA CÓPIA POR FERRAMENTA: em 2026-08-12 o
`data/ops/edge_bot_agents_daily.jsonl` foi auditado e apareceram 10 linhas com
número fisicamente impossível — a pior delas `requests_estimated`
1.000.000.000.000 (um trilhão) para o YandexBot num dia, sobre um acervo de
9.835 URLs. O `check-bot-telemetry-honesty` rodava e devolvia OK: ele conferia
`schema_version` e o campo `authenticity`, nunca a MAGNITUDE. Um gate chamado
"honestidade de telemetria" que não vê um trilhão é falso verde.

O critério mora aqui, num lugar só, porque quem lê a série vai crescer (hoje o
check de honestidade; amanhã qualquer relatório de cobertura de crawler). Se
cada leitor tivesse o próprio limiar, um deles voltaria a somar o trilhão.

────────────────────────────────────────────────────────────────────────────
COMO OS TETOS FORAM MEDIDOS (não são constante mágica)

Corpus: as 4.495 linhas do ledger em 2026-08-12, separadas à mão entre medição
real e as 10 forjadas.

  • Maior `requests_estimated` REAL: 43.087 (claudebot, 2026-08-07). Não é
    suspeita — está documentada como medição em tools/botagents.py, que cita
    "43.087 e 16.460 requisições estimadas" para os bots de treino naquele dia.
    Sobre 9.835 URLs isso dá 4,38 requisições por URL por dia.
  • Maior `requests_sampled` REAL: 9.669 (claudebot) — ~1,0 vez o acervo.
  • Maior fator de extrapolação REAL: 4,46 (43.087 / 9.665).
  • Menor `requests_estimated` FORJADO: 1.000.000.
  • Fatores FORJADOS: exatamente 1.000, 10.000 e 1.000.000 — redondos, o que
    medição amostrada nunca é.

Entre o teto real (43.087) e o piso forjado (1.000.000) há duas ordens de
grandeza de folga. Os tetos abaixo ficam no meio dessa folga: largos o
bastante para não reprovar crescimento honesto do crawler, apertados o
bastante para que qualquer das 10 linhas forjadas caia.

ATENÇÃO AO FALSO POSITIVO — este módulo nasceu com o teste exigido pela regra
do repositório ("detector novo nasce com teste de falso positivo sobre amostra
real"). O critério ingênuo que motivou a auditoria (estimado > 50.000 OU fator
> 3) acusa 88 linhas, das quais 78 são MEDIÇÃO REAL: as 56 do claudebot em
43.087 (fator 4,45, sampleInterval legítimo da Cloudflare) e as 22 do
cloudflare-agentreadiness em 160 (fator 3,27). Reprovar essas seria acusar de
fraude o dado honesto, e um gate que grita no dado bom é um gate que o
operador aprende a ignorar.
"""
import hashlib
import json
import os
import re

# Teto do fator de extrapolação (`requests_estimated / requests_sampled`).
#
# O produtor (tools/generate-bot-agents-daily) calcula estimado como
# soma(count × sampleInterval), onde sampleInterval vem do próprio
# httpRequestsAdaptiveGroups da Cloudflare. Esse intervalo é a taxa de
# amostragem do dataset: 1 = nada amostrado, e sobe em passos de ordem de
# grandeza (1, 10, 100) conforme o volume da zona. Como o produtor pede
# `avg { sampleInterval }`, o valor gravado é uma MÉDIA e por isso sai
# fracionário (3,27 e 4,46 aparecem no corpus real).
#
# 100 é o passo de amostragem mais alto que essa zona poderia plausivelmente
# receber, e ainda deixa 22× de folga sobre o maior fator real (4,46). O menor
# fator forjado é 1.000 — dez vezes acima do teto.
#
# Este é o teste ESPINHA-DORSAL: não depende do tamanho do acervo e sozinho
# apanha as 10 linhas forjadas. Se a contagem de URLs falhar, ele continua de pé.
MAX_FATOR_EXTRAPOLACAO = 100.0

# Teto de requisições por URL por dia, por bot.
#
# O pico real medido é 4,38 (claudebot varrendo o acervo inteiro ~4 vezes num
# dia). 20 dá 4,5× de folga sobre isso — cabe um crawler muito mais agressivo
# que qualquer um já observado. Sobre as 9.835 URLs de hoje o teto fica em
# 196.700; a menor linha forjada (1.000.000) está 5× acima dele.
#
# O teto é derivado do acervo em tempo de execução, nunca fixo: quando o portal
# for a 100k páginas o limite acompanha sozinho, em vez de virar falso positivo.
MAX_REQUISICOES_POR_URL_DIA = 20

# Sem acervo legível não dá para afirmar teto de volume — mas o fator continua
# valendo. Ver `avaliar_linha`: os testes de volume são pulados e o chamador é
# avisado, em vez de o módulo inventar um número ou reprovar tudo.
ACERVO_DESCONHECIDO = 0

_LOC = re.compile(r"<loc>")


def acervo_urls(root):
    """Quantas URLs públicas o portal tem HOJE.

    Fonte primária: os shards de sitemap, que são o que o crawler realmente
    enxerga — é o denominador honesto para "requisições por URL". Fonte
    secundária: o published_manifest, usado quando o build público ainda não
    rodou. Devolve ACERVO_DESCONHECIDO se nenhuma das duas existir.
    """
    sitemaps = os.path.join(root, "public", "sitemaps")
    total = 0
    if os.path.isdir(sitemaps):
        for nome in sorted(os.listdir(sitemaps)):
            if not nome.endswith(".xml"):
                continue
            try:
                with open(os.path.join(sitemaps, nome), encoding="utf-8") as handle:
                    total += len(_LOC.findall(handle.read()))
            except OSError:
                continue
    if total:
        return total

    manifesto = os.path.join(root, "data", "editorial", "published_manifest.jsonl")
    if os.path.isfile(manifesto):
        try:
            with open(manifesto, encoding="utf-8") as handle:
                return sum(1 for linha in handle if linha.strip())
        except OSError:
            return ACERVO_DESCONHECIDO
    return ACERVO_DESCONHECIDO


def teto_requisicoes_dia(acervo):
    """Teto físico de requisições de UM bot em UM dia, dado o acervo."""
    if acervo <= ACERVO_DESCONHECIDO:
        return None
    return acervo * MAX_REQUISICOES_POR_URL_DIA


def sha_linha(bruto):
    """Identidade estável de uma linha do ledger.

    A quarentena é indexada por este hash, e NÃO por número de linha: o ledger
    é append-only e um timer escreve nele a cada 30 minutos (entre o commit
    a4c48ea8 e a auditoria ele foi de 4.321 para 4.495 linhas). Número de linha
    apontaria para outro registro em poucas horas.
    """
    return hashlib.sha256(bruto.strip().encode("utf-8")).hexdigest()


def avaliar_linha(registro, acervo):
    """Devolve a lista de motivos pelos quais a linha é fisicamente impossível.

    Lista vazia = plausível. Cada motivo já vem com o número medido e o teto,
    para que a reprovação possa ser conferida sem abrir o código.
    """
    motivos = []
    estimado = registro.get("requests_estimated")
    amostrado = registro.get("requests_sampled")

    # Contador ausente ou não-numérico é reprovação AQUI, e não "problema de
    # outro check": nenhuma verificação de esquema no projeto inspeciona o TIPO
    # destes dois campos, nem no v1 nem no v2. Se este módulo devolvesse "sem
    # motivo" para valor não-numérico, bastaria gravar a string
    # "1000000000000" no lugar do inteiro para escapar de toda a verificação de
    # magnitude — o mesmo trilhão, agora invisível. Booleano entra na regra
    # porque em Python `True` é instância de int e passaria como o número 1.
    if isinstance(estimado, bool) or isinstance(amostrado, bool) \
            or not isinstance(estimado, (int, float)) \
            or not isinstance(amostrado, (int, float)):
        motivos.append(
            "contador ausente ou nao-numerico: requests_estimated=%r "
            "requests_sampled=%r — sem numero nao ha como afirmar plausibilidade, "
            "e string no lugar do inteiro burlaria os tetos"
            % (estimado, amostrado))
        return motivos

    if estimado < 0 or amostrado < 0:
        motivos.append("valor negativo: estimado=%s amostrado=%s" % (estimado, amostrado))
        return motivos

    # A extrapolação nunca pode ser MENOR que a amostra que a originou:
    # estimado = amostrado × sampleInterval, e sampleInterval >= 1.
    if amostrado > 0 and estimado < amostrado:
        motivos.append(
            "estimativa abaixo da amostra: estimado=%d < amostrado=%d "
            "(estimado = amostrado x sampleInterval, e sampleInterval nunca e < 1)"
            % (estimado, amostrado))

    if amostrado > 0:
        fator = estimado / amostrado
        if fator > MAX_FATOR_EXTRAPOLACAO:
            motivos.append(
                "fator de extrapolacao %.1fx acima do teto %.0fx "
                "(estimado=%d / amostrado=%d; maior fator real medido no corpus: 4,46x)"
                % (fator, MAX_FATOR_EXTRAPOLACAO, estimado, amostrado))

    teto = teto_requisicoes_dia(acervo)
    if teto is not None:
        if estimado > teto:
            motivos.append(
                "estimado=%d acima do teto fisico %d (%d URLs publicas x %d "
                "requisicoes/URL/dia; maior valor real medido: 43.087)"
                % (estimado, teto, acervo, MAX_REQUISICOES_POR_URL_DIA))
        if amostrado > teto:
            motivos.append(
                "amostrado=%d acima do teto fisico %d — a amostra e um "
                "subconjunto do trafego real, entao nao pode passar do total "
                "plausivel do dia (maior valor real medido: 9.669)"
                % (amostrado, teto))

    # v4 (2026-09-02): a contagem passou a ter DUAS pernas de verificacao —
    # Cloudflare (verifiedBotCategory) e faixa de IP oficial do operador,
    # medida numa segunda consulta por familia de User-Agent (ver
    # tools/generate-bot-agents-daily). A magnitude sozinha nao pega um
    # produtor que inflasse requests_sampled sem que nenhuma das duas pernas o
    # explique: a soma tem que fechar, e a autenticidade que alega faixa de IP
    # tem que ter contagem de faixa de IP para sustenta-la. Achado que motivou
    # a segunda perna: PerplexityBot, verifiedBotCategory vazia em 100% das
    # requisicoes e 100% dos clientIP dentro dos 8 prefixos oficiais
    # publicados em data/ops/bot_ip_ranges/perplexitybot.json, medido em
    # 2026-09-02. So roda para linha v4 — v1/v2/v3 nao tem as duas pernas e
    # continuam validadas so pelas regras acima.
    if registro.get("schema_version") == "edge_bot_agents_daily_v4":
        cf_verificado = registro.get("requests_sampled_cloudflare_verified")
        faixa_ip = registro.get("requests_sampled_ip_range")
        if isinstance(cf_verificado, bool) or isinstance(faixa_ip, bool) \
                or not isinstance(cf_verificado, (int, float)) \
                or not isinstance(faixa_ip, (int, float)):
            motivos.append(
                "v4 sem as duas pernas de verificacao como numero: "
                "requests_sampled_cloudflare_verified=%r requests_sampled_ip_range=%r"
                % (cf_verificado, faixa_ip))
        else:
            if amostrado != cf_verificado + faixa_ip:
                motivos.append(
                    "v4 nao fecha a soma: requests_sampled=%s != "
                    "requests_sampled_cloudflare_verified(%s) + requests_sampled_ip_range(%s)"
                    % (amostrado, cf_verificado, faixa_ip))
            autenticidade = registro.get("authenticity")
            if autenticidade in ("ip_range_at_edge", "cloudflare_and_ip_range") and not faixa_ip:
                motivos.append(
                    "v4 authenticity=%r exige requests_sampled_ip_range > 0, recebeu %r"
                    % (autenticidade, faixa_ip))

    return motivos


def caminho_quarentena(root):
    return os.path.join(root, "data", "ops", "edge_bot_agents_daily_quarantine.jsonl")


def carregar_quarentena(root):
    """Hashes das linhas já reconhecidas como impossíveis e neutralizadas.

    A quarentena existe porque o ledger é append-only e a regra do repositório
    proíbe apagar linha ou reescrever histórico. A linha ruim CONTINUA no
    arquivo, visível e auditável; o que a quarentena faz é registrar, com
    motivo e evidência, que ela não entra em nenhuma conta.

    Ser membro por HASH, e não um "pular tudo que é grande", é o que mantém o
    gate útil: uma linha impossível NOVA, que ninguém revisou, continua
    reprovando mesmo depois da quarentena existir.
    """
    caminho = caminho_quarentena(root)
    quarentenados = {}
    if not os.path.isfile(caminho):
        return quarentenados
    with open(caminho, encoding="utf-8") as handle:
        for bruto in handle:
            bruto = bruto.strip()
            if not bruto:
                continue
            try:
                registro = json.loads(bruto)
            except json.JSONDecodeError:
                continue
            chave = registro.get("line_sha256")
            if chave:
                quarentenados[chave] = registro
    return quarentenados


def serie_saneada(root, caminho=None):
    """A série da borda como um consumidor honesto deve lê-la.

    Faz as DUAS coisas que todo leitor precisa e que ninguém deveria
    reimplementar:

      1. Descarta a linha fisicamente impossível (com o motivo disponível em
         `descartadas`), em vez de somá-la.
      2. Deduplica por (date, agent_key) mantendo a ÚLTIMA linha, que é a
         convenção declarada pelo produtor para o arquivo append-only.

    Devolve (registros_por_chave, descartadas).
    """
    if caminho is None:
        caminho = os.path.join(root, "data", "ops", "edge_bot_agents_daily.jsonl")
    acervo = acervo_urls(root)
    quarentena = carregar_quarentena(root)
    por_chave = {}
    descartadas = []
    if not os.path.isfile(caminho):
        return por_chave, descartadas
    with open(caminho, encoding="utf-8") as handle:
        for numero, bruto in enumerate(handle, start=1):
            bruto = bruto.strip()
            if not bruto:
                continue
            try:
                registro = json.loads(bruto)
            except json.JSONDecodeError:
                continue
            motivos = avaliar_linha(registro, acervo)
            if motivos or sha_linha(bruto) in quarentena:
                descartadas.append({
                    "line": numero,
                    "line_sha256": sha_linha(bruto),
                    "date": registro.get("date"),
                    "agent_key": registro.get("agent_key"),
                    "reasons": motivos,
                })
                continue
            por_chave[(registro.get("date"), registro.get("agent_key"))] = registro
    return por_chave, descartadas
