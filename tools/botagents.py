"""botagents — identidade EXATA de bot, fonte única para toda a telemetria.

POR QUE UM MÓDULO, E NÃO UMA TABELA POR FERRAMENTA: existem duas medições de bot
no projeto — a da BORDA (Cloudflare, tem volume mas não tem IP verificável) e a
da ORIGEM (log do nginx, tem IP real mas janela curta). Se cada uma tivesse a
própria tabela, elas divergiriam na primeira vez que um operador lançasse um
agente novo, e a série histórica passaria a comparar coisas diferentes sem que
ninguém percebesse.

O PONTO DE TUDO ISSO é a separação entre TREINO e BUSCA. A tabela de famílias
que já existia em `tools/check-edge-traffic` colapsa os dois:

    ("OpenAI",    ["oai-searchbot", "chatgpt-user", "gptbot"])
    ("Anthropic", ["claude-searchbot", "claude-user", "claudebot"])

GPTBot e ClaudeBot rastreiam para treinar modelo; OAI-SearchBot e
Claude-SearchBot são os que decidem se o portal aparece citado numa resposta.
Medido em 2026-08-07: os dois de treino varreram o acervo inteiro no mesmo dia
(43.087 e 16.460 requisições estimadas) enquanto os dois de busca somaram 2. Sob
o rótulo "OpenAI"/"Anthropic" essa diferença some — e é a única que importa para
o objetivo do portal.
"""

# Identidade EXATA de bot. A ordem importa: a primeira marca que casar vence,
# então o mais específico vem antes.
#
# "chrome-lighthouse" tem entrada própria porque roda de IP do Google
# (66.249.*) e, numa análise anterior, fez PageSpeed Insights ser contado como
# Googlebot: 61 hits viraram 13 quando a separação entrou. É o erro que esta
# tabela existe para impedir.
AGENTES = [
    ("googlebot-image", ["googlebot-image"]),
    ("googlebot-news", ["googlebot-news"]),
    ("googlebot-video", ["googlebot-video"]),
    ("google-inspectiontool", ["google-inspectiontool"]),
    ("googleother-image", ["googleother-image"]),
    ("googleother-video", ["googleother-video"]),
    ("googleother", ["googleother"]),
    ("storebot-google", ["storebot-google"]),
    # AdsBot-Google-Mobile CADASTRADO EM 2026-09-03, junto do registro em
    # internal/crawl/crawl.go. Precisa vir ANTES de "adsbot-google": é o mesmo
    # caso de "googlebot-image" antes de "googlebot" — "adsbot-google" é
    # PREFIXO de "adsbot-google-mobile", e a ordem de agente_de() casa a
    # primeira marca que bater, então sem isso o agente mobile nunca seria
    # identificado (colapsaria dentro de "adsbot-google").
    ("adsbot-google-mobile", ["adsbot-google-mobile"]),
    ("adsbot-google", ["adsbot-google"]),
    ("google-extended", ["google-extended"]),
    ("chrome-lighthouse", ["chrome-lighthouse"]),
    # Token real confirmado na doc oficial (developers.google.com/crawling/docs/
    # crawlers-fetchers/google-user-triggered-fetchers, lido em 2026-08-11):
    # "Google Site Verifier ... Mozilla/5.0 (compatible; Google-Site-Verification/1.0)".
    # A chave "google-site-verifier" que existia em data/ops/bot_ip_ranges/
    # google-user-triggered.json (1.056 prefixos) nunca autenticou nada porque
    # NENHUMA marca aqui casava com ela — nem o nome batia com o UA real. Corrigido
    # nos dois lados (aqui e em tools/generate-bot-ip-ranges) em vez de descartar
    # 1.056 prefixos oficiais publicados pelo Google.
    ("google-site-verification", ["google-site-verification"]),
    ("googlebot", ["googlebot"]),

    ("adidxbot", ["adidxbot"]),
    ("bingbot", ["bingbot", "bingpreview"]),

    ("oai-searchbot", ["oai-searchbot"]),
    ("oai-adsbot", ["oai-adsbot"]),
    ("chatgpt-user", ["chatgpt-user"]),
    ("gptbot", ["gptbot"]),

    ("claude-searchbot", ["claude-searchbot"]),
    ("claude-user", ["claude-user"]),
    ("claudebot", ["claudebot"]),

    ("perplexity-user", ["perplexity-user"]),
    ("perplexitybot", ["perplexitybot"]),

    # Mistral publica TRÊS tokens no mesmo documento e eles têm funções
    # diferentes (docs.mistral.ai/robots, cadastrados em internal/crawl/crawl.go
    # :245-247 e :275). Entram com o token INTEIRO, nunca como prefixo
    # `mistralai`: o prefixo nu colapsaria o crawler de dataset com o índice da
    # busca e com o fetch disparado por pergunta — exatamente o colapso que o
    # cabeçalho deste módulo existe para impedir.
    ("mistralai-index", ["mistralai-index"]),
    ("mistralai-user", ["mistralai-user"]),
    ("mistralai-training", ["mistralai-training"]),

    ("applebot-extended", ["applebot-extended"]),
    ("applebot", ["applebot"]),
    # `duckassistbot` NÃO casa `duckduckbot` (são tokens distintos, e por isso o
    # vhost precisou de linha própria para ele em ops/nginx/wikijuridica.conf).
    # Sem esta entrada, `agente_de` devolvia None para o agente que busca a
    # página EM TEMPO REAL para montar a resposta assistida do DuckDuckGo — o
    # sinal de citação mais direto que a origem consegue observar sumia da
    # telemetria inteira sem deixar rastro.
    ("duckassistbot", ["duckassistbot"]),
    ("duckduckbot", ["duckduckbot"]),
    ("yandexbot", ["yandexbot"]),
    # Baiduspider CADASTRADO EM 2026-09-16. Ele era, ate esta data, o terceiro
    # maior agente declarado que a telemetria nao conhecia: 1.147 requisicoes na
    # borda nas 24h encerradas em 2026-09-16T16:00:00Z e 609 na origem em 15/09. A identidade
    # nao e palpite -- 280 IPs distintos na origem, rDNS FORWARD-CONFIRMED em
    # `*.crawl.baidu.com` (ex.: 116.179.32.101 ->
    # baiduspider-116-179-32-101.crawl.baidu.com e de volta), e a URL que o
    # proprio UA embute (http://www.baidu.com/search/spider.html) respondeu 200
    # a sonda de `generate-bot-registry-candidates`.
    #
    # `baiduspider-render` ANTES de `baiduspider`: e o mesmo caso de
    # "googlebot-image" antes de "googlebot" -- o segundo e PREFIXO do primeiro,
    # e `agente_de` casa a primeira marca que bater. Sem esta ordem o
    # renderizador nunca teria chave propria. Os dois tem funcao diferente: o
    # `-render` executa a pagina para ver o que o JS monta, o outro rastreia.
    ("baiduspider-render", ["baiduspider-render"]),
    ("baiduspider", ["baiduspider"]),
    ("ccbot", ["ccbot"]),
    ("amzn-searchbot", ["amzn-searchbot"]),
    ("amzn-user", ["amzn-user"]),
    ("amazonbot", ["amazonbot"]),
    ("bytespider", ["bytespider"]),
    # meta-externalfetcher SAIU da chave de treinamento em 2026-08-12. Estava
    # colapsado dentro de `meta-externalagent`, e os dois têm função OPOSTA para
    # o objetivo do portal: `meta-externalagent` coleta para treinar modelo,
    # enquanto `meta-externalfetcher` é fetch disparado por usuário
    # (internal/crawl/crawl.go:224 o declara BotPurposeUserTriggered e
    # BotClassValuableSearchOrUser, com pista de rate ilimitada). Somados, um
    # fetch de citação aparecia na série como rastreio de dataset — o mesmo erro
    # que o cabeçalho deste módulo descreve para "OpenAI"/"Anthropic".
    ("meta-externalfetcher", ["meta-externalfetcher"]),
    ("meta-externalagent", ["meta-externalagent"]),
    # meta-webindexer e slackbot-linkexpanding ENTRARAM em 2026-08-26, e a falta
    # deles era GOVERNANÇA SEM MEDIÇÃO: os dois estão no registry desde
    # 2026-08-13 como `valuable_search_or_user_bot` com pista ilimitada, têm
    # grupo próprio em robots.txt e linha própria no map do nginx — e a telemetria
    # devolvia None para os dois, então o tráfego deles não aparecia em série
    # nenhuma. Concedia-se tratamento diferenciado a dois agentes cujo uso do
    # tratamento ninguém conseguia ver. Achado por
    # tools/check-bot-identity-fonte-unica, que confere as duas direções.
    ("meta-webindexer", ["meta-webindexer"]),
    ("facebookexternalhit", ["facebookexternalhit"]),
    ("slackbot-linkexpanding", ["slackbot-linkexpanding"]),

    # AI2Bot, PetalBot e a classe seo_tool CADASTRADOS EM 2026-09-03, junto do
    # registro em internal/crawl/crawl.go (mesma sessão, mesma fonte).
    ("ai2bot", ["ai2bot"]),
    ("petalbot", ["petalbot"]),

    ("semrushbot", ["semrushbot"]),
    # AhrefsSiteAudit CADASTRADO EM 2026-09-16, e ele era o MAIOR agente
    # declarado fora do registro: 5.859 requisicoes na borda nas 24h ate
    # encerradas em 2026-09-16T16:00:00Z (46% do balde inteiro) contra 1.182 na origem em 15/09 --
    # a diferenca e o `s-maxage=604800` da Regra 15. Operador confirmado por
    # rDNS forward-confirmed sobre 284 IPs distintos: `*.ahrefs.net` (ex.:
    # 168.100.149.0 -> proxy-us000-san0.ahrefs.net e de volta).
    #
    # TOKEN PROPRIO, NUNCA colapsado em `ahrefsbot`: o AhrefsBot rastreia a web
    # para o indice de backlinks da Ahrefs, enquanto o SiteAudit varre UM site a
    # pedido de quem contratou a auditoria dele. Sao volumes de ordem
    # completamente diferente -- 5.859 contra 60 na mesma janela -- e somar os
    # dois sob "ahrefs" faria uma auditoria contratada por terceiro parecer
    # interesse do indice da Ahrefs pelo portal. E o mesmo erro que o cabecalho
    # deste modulo descreve para "OpenAI"/"Anthropic".
    ("ahrefssiteaudit", ["ahrefssiteaudit"]),
    ("ahrefsbot", ["ahrefsbot"]),
    ("mj12bot", ["mj12bot"]),
    ("dotbot", ["dotbot"]),
    ("blexbot", ["blexbot"]),
    # "dataforseobot" ANTES de "dataforseo": é o token EXATO que
    # internal/crawl/crawl.go registra (doc oficial: "User agent string:
    # Mozilla/5.0 (compatible; DataForSeoBot; +https://dataforseo.com/
    # dataforseo-bot)"), e por isso precisa vencer o casamento por
    # especificidade — "dataforseo" continua abaixo como fallback para
    # qualquer outro produto da mesma empresa que não leve o sufixo "bot".
    ("dataforseobot", ["dataforseobot"]),
    ("dataforseo", ["dataforseo"]),

    ("cloudflare-agentreadiness", ["cloudflare-agentreadiness"]),

    # TRÊS MONITORES DE MCP ACRESCENTADOS EM 2026-09-03. Não são crawler de
    # conteúdo — batem em /mcp e /a2a/v1 para checar disponibilidade, nunca
    # buscam página do acervo — e por isso NÃO entram em
    # internal/crawl/crawl.go (o registro é de política de crawl do acervo, e
    # eles não o rastreiam). Existiam como "não verificado" na telemetria
    # (UA presente no log, `agente_de` devolvendo None) até esta entrada. UA
    # real medido em data/ops/access/nginx-2026-09-0{2,3}.jsonl:
    #   SentinelOracle/0.1 (+https://glimind.com/opt-out; liveness-only, never invokes tools)
    #   mcpbeat/0.1 (+https://mcpbeat.com/bot/; liveness check)
    #   zevruna-monitor/1.0 (+https://zevruna.com)
    ("sentineloracle", ["sentineloracle"]),
    ("mcpbeat", ["mcpbeat"]),
    ("zevruna-monitor", ["zevruna-monitor"]),
    ("google-agent", ["google-agent"]),
    ("google-gemininotebook", ["google-gemininotebook"]),
    ("google-read-aloud", ["google-read-aloud"]),
    ("feedfetcher-google", ["feedfetcher-google"]),
    ("google-cws", ["google-cws"]),
    ("googlemessages", ["googlemessages"]),
    ("google-pinpoint", ["google-pinpoint"]),
    ("googleproducer", ["googleproducer"]),
    ("google-cloudvertexbot", ["google-cloudvertexbot"]),
    ("apis-google", ["apis-google"]),
    ("mediapartners-google", ["mediapartners-google"]),
    ("google-safety", ["google-safety"]),
    ("kagibot", ["kagibot"]),
    ("seekportbot", ["seekportbot"]),
    ("pinterestbot", ["pinterestbot"]),
    ("diffbot-user", ["diffbot-user"]),
    ("diffbot", ["diffbot"]),
    ("imagesiftbot", ["imagesiftbot"]),
    ("webzio-extended", ["webzio-extended"]),
    ("webzio", ["webzio"]),
    ("cloudflare-ai-search", ["cloudflare-ai-search"]),
]

# Função declarada de cada agente — a separação que faltava:
#   search    — alimenta índice de busca ou resposta com citação  (O ALVO)
#   user      — busca a pedido de um usuário, no momento da pergunta
#   training  — coleta para treinar modelo (não é o alvo; também não se barra)
#   ads       — validação de anúncio
#   diagnostic— ferramenta de inspeção do próprio operador
#   seo       — ferramenta de terceiro
#   infra     — sonda de infraestrutura
FUNCAO = {
    "googlebot": "search", "googlebot-image": "search", "googlebot-news": "search",
    "googlebot-video": "search", "bingbot": "search", "applebot": "search",
    "duckduckbot": "search", "yandexbot": "search",
    # Baiduspider CADASTRADO EM 2026-09-16: o rastreador do indice de busca da
    # Baidu, declarado na propria doc que o UA aponta. O `-render` e o mesmo
    # operador executando a pagina para ver o DOM montado -- funcao de
    # diagnostico do rastreador, nao de indexacao, e por isso chave separada.
    "baiduspider": "search",
    "baiduspider-render": "diagnostic",
    "oai-searchbot": "search", "claude-searchbot": "search", "perplexitybot": "search",
    "mistralai-index": "search", "amzn-searchbot": "search",
    # PetalBot CADASTRADO EM 2026-09-03: busca/indexação (doc oficial: alimenta
    # o buscador Petal e "content recommendations" no Huawei Assistant).
    "petalbot": "search",
    "chatgpt-user": "user", "claude-user": "user", "perplexity-user": "user",
    "amzn-user": "user", "duckassistbot": "user", "mistralai-user": "user",
    "meta-externalfetcher": "user",
    "gptbot": "training", "claudebot": "training", "ccbot": "training",
    "bytespider": "training", "amazonbot": "training", "meta-externalagent": "training",
    "mistralai-training": "training",
    "google-extended": "training", "applebot-extended": "training",
    # AI2Bot CADASTRADO EM 2026-09-03: doc oficial diz sem meio-termo "used to
    # train open language models".
    "ai2bot": "training",
    "adsbot-google": "ads", "adidxbot": "ads", "oai-adsbot": "ads",
    # AdsBot-Google-Mobile CADASTRADO EM 2026-09-03: mesma função de
    # "adsbot-google" (validação de anúncio), variante mobile, token distinto.
    "adsbot-google-mobile": "ads",
    "google-inspectiontool": "diagnostic", "chrome-lighthouse": "diagnostic",
    "googleother": "diagnostic", "storebot-google": "diagnostic",
    "google-site-verification": "diagnostic",
    # O registry declara search_discovery para o Meta-WebIndexer (é o índice de
    # busca da Meta) e user_triggered_fetch para o Slackbot-LinkExpanding — que
    # aqui vira "social" pelo mesmo critério do facebookexternalhit: ele desdobra
    # link colado por uma pessoa numa conversa, não responde a uma pergunta.
    "meta-webindexer": "search",
    "facebookexternalhit": "social",
    "slackbot-linkexpanding": "social",
    "semrushbot": "seo", "ahrefsbot": "seo", "mj12bot": "seo", "dotbot": "seo",
    # AhrefsSiteAudit CADASTRADO EM 2026-09-16: ferramenta de terceiro, como o
    # AhrefsBot. Ela NAO alimenta indice de busca nem resposta com citacao, e
    # por isso fica fora do que o ranking de promocao considera valioso -- o
    # criterio esta em cmd/cerebro/comentarios.go, `agentesValiososParaRanking`.
    "ahrefssiteaudit": "seo",
    "blexbot": "seo", "dataforseo": "seo",
    # DataForSeoBot CADASTRADO EM 2026-09-03 no registry, classe seo_tool nova
    # (junto de SemrushBot/MJ12bot/AhrefsBot). "dataforseobot" é o token EXATO
    # (ver AGENTES acima); "dataforseo" continua declarado para o produto sem
    # o sufixo "bot".
    "dataforseobot": "seo",
    "cloudflare-agentreadiness": "infra",
    # Monitores de MCP (liveness/uptime de /mcp e /a2a/v1) — função própria,
    # não são "infra" deste portal (não sondam o servidor Go em si) nem
    # "diagnostic" (não são ferramenta do operador). Ver AGENTES acima.
    "sentineloracle": "mcp_scanner",
    "mcpbeat": "mcp_scanner",
    "zevruna-monitor": "mcp_scanner",
    "google-agent": "user",
    "google-gemininotebook": "user",
    "google-read-aloud": "user",
    "feedfetcher-google": "user",
    "google-cws": "user",
    "googlemessages": "user",
    "google-pinpoint": "user",
    "googleproducer": "user",
    "google-cloudvertexbot": "user",
    "googleother-image": "search",
    "googleother-video": "search",
    "apis-google": "user",
    "mediapartners-google": "ads",
    "google-safety": "user",
    "kagibot": "search",
    "seekportbot": "search",
    "pinterestbot": "search",
    "diffbot": "training",
    "diffbot-user": "user",
    "imagesiftbot": "training",
    "webzio": "training",
    "webzio-extended": "training",
    "cloudflare-ai-search": "search",
}

# Operadores que rastreiam SEMPRE das próprias redes, publicadas e fora do
# Brasil. Um desses User-Agents chegando de IP brasileiro não é visita: é a
# verificação local batendo no domínio público.
OPERADORES_SEMPRE_ESTRANGEIROS = {
    "googlebot", "googlebot-image", "googlebot-news", "googlebot-video",
    "google-inspectiontool", "googleother", "storebot-google", "adsbot-google",
    "google-extended", "chrome-lighthouse", "google-site-verification",
    "bingbot", "adidxbot",
    "oai-searchbot", "oai-adsbot", "chatgpt-user", "gptbot",
    "claude-searchbot", "claude-user", "claudebot",
    "perplexitybot", "perplexity-user",
    "mistralai-index", "mistralai-user", "mistralai-training",
    "applebot", "applebot-extended", "duckduckbot", "duckassistbot",
    "yandexbot", "ccbot",
    "amazonbot", "amzn-searchbot", "amzn-user", "bytespider",
    "meta-externalagent", "meta-externalfetcher", "meta-webindexer",
    "facebookexternalhit", "slackbot-linkexpanding",
}

# Ordem de apresentação: o que decide citação primeiro.
ORDEM_FUNCAO = ("search", "user", "training", "ads", "diagnostic", "seo", "social", "infra", "mcp_scanner")

# Sufixos de rDNS que os operadores documentam, usados quando não há JSON de
# faixa (ou como reforço quando há). Confirmação SEMPRE nos dois sentidos (PTR e
# depois A/AAAA de volta) — só o PTR é forjável por quem controla o DNS reverso
# do próprio IP. Centralizado aqui (fonte única) porque a medição da ORIGEM
# (generate-bot-traffic-origin) e qualquer check de honestidade de telemetria
# precisam concordar sobre quais agentes TÊM método de verificação — um agente
# sem entrada aqui e sem faixa de IP publicada é "não verificável", nunca
# "forjado" (ver a distinção em generate-bot-traffic-origin).
RDNS = {
    "googlebot": (".googlebot.com", ".google.com"),
    "googlebot-image": (".googlebot.com",), "googlebot-news": (".googlebot.com",),
    "googlebot-video": (".googlebot.com",),
    "googleother": (".googlebot.com", ".google.com"),
    "google-inspectiontool": (".google.com",),
    "storebot-google": (".googlebot.com",),
    # Google-Extended não tem crawler próprio: GoogleOther/Googlebot/
    # Google-CloudVertexBot é quem carrega o token — por isso o mesmo sufixo.
    # Medido em C4 (docs/plans/2026-08-11-recuperacao-crawl.md): 40 requests
    # com este UA, 0 confirmados por este método — o resto é o scanner.
    "google-extended": (".googlebot.com", ".google.com"),
    "bingbot": (".search.msn.com",),
    "applebot": (".applebot.apple.com",),
    "amazonbot": (".crawl.amazonbot.amazon",),
    "duckduckbot": (".duckduckgo.com",),
    "yandexbot": (".yandex.ru", ".yandex.net", ".yandex.com"),
    # MEDIDOS EM 2026-09-16 sobre data/ops/access/nginx-2026-09-1{5,6}.jsonl,
    # forward-confirmed nos dois sentidos, e nao copiados de documentacao:
    # 280/280 IPs de Baiduspider em `.crawl.baidu.com` e 284/284 de
    # AhrefsSiteAudit em `.ahrefs.net`.
    "baiduspider": (".crawl.baidu.com",),
    "baiduspider-render": (".crawl.baidu.com",),
    "ahrefssiteaudit": (".ahrefs.net",),
}


def ler_faixas(root):
    """agent_key -> lista de ip_network, lida de data/ops/bot_ip_ranges/.

    É a verificação de identidade disponível na ORIGEM — onde a borda não é a
    fonte (log do nginx), a faixa oficial publicada pelo operador faz o papel
    que `verifiedBotCategory` faz na Cloudflare. Os arquivos são mantidos pelo
    timer `wikijuridica-bot-ipranges`.

    Operador ausente simplesmente não autentica ninguém — NUNCA vira "não
    autêntico". A distinção importa: não saber quem é não é o mesmo que saber
    que é forjado, e confundir as duas coisas foi o que fez a telemetria deste
    projeto acusar de fraude bot honesto e chamar de crawler a própria sonda.

    Vive aqui, e não em cada ferramenta, pelo mesmo motivo das tabelas de
    identidade: duas cópias divergem na primeira vez que um operador troca de
    bloco, e a divergência aparece como bot "sumindo" de uma série só.
    """
    import ipaddress
    import json as _json
    import os as _os

    por_agente = {}
    diretorio = _os.path.join(root, "data", "ops", "bot_ip_ranges")
    if not _os.path.isdir(diretorio):
        return por_agente
    for nome in sorted(_os.listdir(diretorio)):
        if not nome.endswith(".json"):
            continue
        try:
            with open(_os.path.join(diretorio, nome), encoding="utf-8") as handle:
                dados = _json.load(handle)
        except Exception:
            continue
        redes = []
        for bruto in dados.get("prefixes", []):
            try:
                redes.append(ipaddress.ip_network(bruto, strict=False))
            except ValueError:
                continue
        for agente in dados.get("authenticates_agents", []):
            por_agente.setdefault(agente, []).extend(redes)
    return por_agente


def em_faixa(ip, redes):
    """IP dentro de alguma faixa publicada pelo operador."""
    import ipaddress

    try:
        endereco = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(endereco in rede for rede in redes)


def rdns_confirmado(ip, sufixos):
    """PTR e volta (FCrDNS). Devolve (confirmado, nome_encontrado).

    Só o PTR não basta: quem controla o reverso do próprio IP escreve nele o que
    quiser. A confirmação exige que o nome termine num sufixo que o operador
    documenta E que o A/AAAA daquele nome volte para o MESMO IP.

    MORA AQUI PELO MESMO MOTIVO DA TABELA `RDNS`, dez linhas acima: o método de
    verificação é propriedade do OPERADOR, não da ferramenta que mede. Enquanto
    esta função viveu dentro de `generate-bot-traffic-origin`, quem quisesse
    medir bot por outra fonte (o ledger de origem em JSONL, por exemplo) tinha de
    copiá-la — e duas cópias divergem na primeira vez que um operador troca de
    sufixo, com o bot "sumindo" de uma série só.

    Faz consulta de DNS: quem chama decide se pode pagá-la, e cacheia por
    (agente, ip). Falha de rede devolve (False, ""), NUNCA exceção — e quem
    chama tem de tratar isso como "não confirmado nesta execução", jamais como
    "forjado": não conseguir verificar não é o mesmo que verificar e reprovar.
    """
    import socket

    try:
        nome = socket.gethostbyaddr(ip)[0].rstrip(".").lower()
    except Exception:
        return False, ""
    if not any(nome.endswith(sufixo) for sufixo in sufixos):
        return False, nome
    try:
        _, _, enderecos = socket.gethostbyname_ex(nome)
    except Exception:
        return False, nome
    return ip in enderecos, nome


def ip_nao_publico(ip):
    """IP que NÃO pode ser de um visitante vindo da internet.

    Cobre loopback, redes privadas (RFC 1918), link-local e as faixas de
    documentação (RFC 5737: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) —
    `is_private` do módulo `ipaddress` engloba todas elas.

    POR QUE ISSO EXISTE: no access log de 2026-08-12 apareceram 2.000 linhas de
    `WikiJuridicaInfraAudit/1.0`, `Audit/1.0`, `curl-teste/1.0` e
    `wj-urlspace-audit/1.0` vindas de 203.0.113.x e de 127.0.0.1 — ferramenta e
    fixture desta casa. Nenhuma delas casa o prefixo `wikijuridica-` que os
    filtros de User-Agent procuram, então todas passavam por VISITANTE. O IP
    resolve o que a string não resolve: quem vem de faixa não-roteável na
    internet não é audiência, qualquer que seja o User-Agent que escreva.
    """
    import ipaddress

    try:
        endereco = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return endereco.is_private or endereco.is_loopback or endereco.is_link_local


def agente_de(user_agent):
    """Identidade EXATA do bot, ou None se não for bot conhecido.

    Nunca colapsa dois agentes de função diferente na mesma chave. Ferramenta do
    próprio repositório devolve None: contá-la seria inflar a métrica, a
    proibição mais dura do contrato.
    """
    baixo = (user_agent or "").lower()
    if not baixo:
        return None
    if baixo.startswith("wikijuridica-"):
        return None
    for chave, marcas in AGENTES:
        if any(marca in baixo for marca in marcas):
            return chave
    return None


def funcao_de(chave):
    return FUNCAO.get(chave, "unknown")


# ---------------------------------------------------------------------------
# DENOMINADOR LÍQUIDO — o critério único de desconto do tráfego desta casa.
#
# POR QUE EXISTE, com a medição que obriga (2026-08-29, BUG-070): no log de
# origem do dia, `tools/check-access-log-bots` mediu `linhas=13362
# ferramenta_interna=12987` — 97,2% do log é ferramenta desta casa, e 74% dessas
# são 304 de aquecimento. Medido de novo às 13h07 do mesmo dia, com o log já
# maior: `linhas=50231 ferramenta_interna=48077`, 95,7%. Os dois números são
# honestos e diferentes porque a JANELA é outra; o que não é honesto é publicar
# uma taxa sobre o bruto sem dizer qual dos dois se está lendo.
#
# Qualquer taxa calculada sobre o total bruto é ficção. E o problema não era
# falta de classificador — `check-access-log-bots` já classificava certo —, era
# cada consumidor ter o seu, e nenhum publicar o par.
#
# O CRITÉRIO É VERSIONADO NO NOME. Mudou o critério, muda a versão, e a série
# antiga continua legível: é a mesma razão do `schema_version` dos ledgers.
CRITERIO_DENOMINADOR = "denominador_liquido_v1"

# As quatro provas, na ordem em que valem. As duas primeiras são CATEGÓRICAS (o
# nginx grava o que a requisição de fato trouxe); as duas últimas são a
# degradação declarada para linha antiga, quando o log_format ainda não tinha os
# campos — e é por isso que o motivo sai nomeado, nunca como um booleano solto.
MOTIVOS_DE_DESCONTO = (
    "sonda_bot_sim",       # X-Bot-Simulation: sonda que finge ser bot para auditar
    "aquecimento_marcado",  # X-Warming-Request: true, gravado como warm=
    "origem_nao_publica",   # loopback/RFC1918/RFC5737: esta máquina, não a internet
    "ua_desta_casa",        # User-Agent com prefixo wikijuridica-
)


def motivo_de_desconto(bot_sim=None, warm=None, ip=None, user_agent=None):
    """Diz POR QUE esta linha do log não é audiência, ou None se ela for.

    Devolve um dos MOTIVOS_DE_DESCONTO. A ordem é a da confiabilidade da prova:
    marca do nginx primeiro, convenção de User-Agent por último.

    A `check-superficie-bots-live` grava em data/ops/edge_probe_requests.jsonl o
    que a própria sonda mandou à borda, justamente para que `organic_requests`
    não conte auditoria como audiência. Esta função é a MESMA ideia do lado da
    origem, e não substitui aquele ledger: são superfícies diferentes.
    """
    if str(bot_sim or "").strip() not in ("", "-", "0"):
        return "sonda_bot_sim"
    if str(warm or "").strip().lower() not in ("", "-", "0", "false"):
        return "aquecimento_marcado"
    if ip and ip_nao_publico(ip):
        return "origem_nao_publica"
    if (user_agent or "").lower().startswith("wikijuridica-"):
        return "ua_desta_casa"
    return None


def denominador(bruto, descontadas, criterio=CRITERIO_DENOMINADOR):
    """O par que todo consumidor tem de publicar, pronto para imprimir e para JSON.

    `liquido` nunca fica negativo: contagem inconsistente vira zero e o par
    continua legível, porque um denominador negativo produziria taxa acima de
    100% e ninguém saberia de onde veio.
    """
    bruto = max(0, int(bruto))
    descontadas = max(0, min(int(descontadas), bruto))
    liquido = bruto - descontadas
    return {
        "bruto": bruto,
        "criterio_desconto": criterio,
        "descontadas": descontadas,
        "liquido": liquido,
        "proporcao_interna": round(descontadas / bruto, 4) if bruto else 0.0,
    }


def denominador_em_uma_linha(par, rotulo="denominador"):
    """A linha literal que o contrato do BUG-070 exige: bruto, líquido e o
    critério do desconto JUNTOS, para ninguém precisar adivinhar qual dos dois
    está lendo.
    """
    return ("%s: bruto=%d liquido=%d descontadas=%d (%.1f%% interno) criterio=%s"
            % (rotulo, par["bruto"], par["liquido"], par["descontadas"],
               100 * par["proporcao_interna"], par["criterio_desconto"]))
