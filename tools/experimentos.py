"""experimentos — núcleo do A/B **cluster-randomizado por página** do portal.

★ POR QUE POR PÁGINA, E NUNCA POR VISITANTE

O acervo (11.039 páginas em 2026-09-09) sai ESTÁTICO do disco, servido pelo
nginx com `root public/`, atrás de uma CDN com `s-maxage=604800`. Um teste por
visitante exigiria variar a resposta na mesma URL — o que significa `Vary`,
cookie ou decisão por User-Agent:

  - `Vary`/cookie multiplicam a chave de cache e matam os 7 dias de borda que
    hoje sustentam o portal (a borda já é 93,2% do tráfego);
  - decidir por User-Agent é CLOAKING: servir a bot e a humano coisas
    diferentes na mesma URL é spam para o Google, e o CLAUDE.md §12 proíbe em
    letra ("Mesmo conteúdo para bot e humano, sempre").

Por isso a unidade de aleatorização é a PÁGINA (cluster), não a sessão. Cada
página fica num braço só, o HTML servido continua único por URL, a borda
continua cacheando, e a comparação é entre grupos de páginas.

★ A COORTE É DETERMINÍSTICA, E É POR ISSO QUE ELA É AUDITÁVEL

A atribuição sai de `sha256(sal + domínio + path normalizado)` — nunca de
`random` sem semente e nunca de `hash()` do Python, que é aleatorizado por
processo (PYTHONHASHSEED) e daria coorte diferente a cada execução. É a regra
R3 do `docs/CONTRATO_DADO_REAL.md`: afirmação numérica vem de medição
reprodutível. Qualquer pessoa recalcula a coorte inteira com o `sal` gravado no
ledger e tem de chegar ao mesmo conjunto, byte a byte.

★ O QUE ESTE MÓDULO **NÃO** FAZ: ESCREVER PROSA

A DEC-017 (`docs/goal/V1_V2_CONTENT_LINEAGE.md:42`) é lei neste repositório:
**a máquina nunca inventa prosa pública.** Um framework de A/B é exatamente o
lugar onde essa lei costuma ser burlada sem querer — "gerar 10 títulos e ver
qual ganha" é geração automática de prosa pública com outro nome.

Aqui o texto da variante ou (a) já foi escrito pelo autor e está no estoque v2,
sendo apenas MOVIDO de campo (o `h1` autoral vira `<title>`), ou (b) é
permutação de conteúdo já aprovado (a ordem do FAQ), ou (c) NÃO EXISTE — e
então o experimento nasce no estado `aguardando_prosa`, listando quantas
páginas esperam texto humano. Nenhum caminho deste módulo compõe frase nova.

★ ONDE ISTO ENCOSTA NO RESTO DO PROJETO

  - universo: `data/editorial/published_manifest.jsonl` (path + intent, o que
    está de fato no ar);
  - texto candidato: `data/editorial/v2_pages/*.jsonl` (title, h1, opening,
    meta_description, faq) — casamento medido em 2026-09-10: 11.039/11.039
    intents do manifesto têm registro v2, e `public_path` está VAZIO em todos
    eles, então o path vem do manifesto e nunca do estoque;
  - contratos de indexação (CLAUDE.md §6): `<title>` de 20 a 65 caracteres,
    meta description de 70 a 160, ambos ÚNICOS no acervo;
  - ética (Provimento OAB 205/2021): promessa de resultado é crítico, e o
    detector canônico é o de `tools/generate-v2-publication-severity` — que
    este módulo IMPORTA em vez de reescrever, porque duas tabelas de promessa
    divergiriam na primeira palavra nova.
"""
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from importlib.machinery import SourceFileLoader
from urllib.parse import unquote, urlsplit

SCHEMA_VERSION = "experimentos_v1"
LEDGER_REL = "data/ai/experimentos.jsonl"
MANIFESTO_REL = "data/editorial/published_manifest.jsonl"
SHARDS_REL = "data/editorial/v2_pages"
SEVERIDADE_REL = "tools/generate-v2-publication-severity"

DOMINIO = "wikijuridica.com.br"

# Teto do dono (plano de 2026-09-09): no máximo 5% do acervo em experimento
# SIMULTÂNEO — somando todos os experimentos ativos, não por experimento.
TETO_FRACAO_ACERVO = 0.05
JANELA_DIAS_PADRAO = 14

# Contrato de indexação do CLAUDE.md §6. Não são parâmetros: são o que o
# `internal/htmlcontract` e o `internal/seo` cobram da página publicada.
TITULO_MIN, TITULO_MAX = 20, 65
META_MIN, META_MAX = 70, 160

FATORES = ("titulo", "meta_description", "resumo_tres_linhas", "ordem_faq")

# Estados do experimento. Só os ATIVOS ocupam o teto de 5%.
ESTADOS_ATIVOS = (
    "aguardando_prosa",            # falta texto humano (DEC-017: a máquina não escreve)
    "aguardando_revisao_autoral",  # texto autoral movido de campo, à espera do OK do autor
    "aguardando_aplicacao",        # pronto para o gerador datado com CAS
    "aplicado",                    # variante no ar, janela correndo
)
ESTADOS_TERMINAIS = ("encerrado_adotado", "encerrado_descartado", "cancelado")

RECEITA_HASH = (
    "u = int(sha256(sal + '\\n' + dominio + '\\n' + path_normalizado)[:8], 'big') / 2**64; "
    "seleção usa dominio='selecao', braço usa dominio='braco'"
)


class FonteAusente(Exception):
    """Arquivo de entrada que a ferramenta precisa e não existe.

    Nunca se resolve com valor padrão: quem chama imprime o que falta e sai com
    código próprio (regra do repositório — ferramenta não finge dado)."""


def raiz_do_repo(arquivo=None):
    """Raiz do /opt/wiki a partir deste arquivo (tools/experimentos.py)."""
    base = os.path.abspath(arquivo or __file__)
    return os.path.dirname(os.path.dirname(base))


def normaliza_path(bruto):
    """URL ou path vira o path canônico do acervo.

    Une as três grafias que as séries de desfecho usam para a MESMA página:
      - manifesto:  `/familia/x/`
      - Bing:       `https://wikijuridica.com.br/familia/x/`
      - Clarity:    `https://wikijuridica.com.br/familia/x/?utm_source=chatgpt.com`

    Sem isto o join silenciosamente devolve zero e o experimento pareceria "sem
    tráfego" quando o tráfego existe — o modo de falha que o CLAUDE.md descreve
    como "chave que engana a medição".
    """
    if bruto is None:
        return ""
    texto = str(bruto).strip()
    if not texto:
        return ""
    partes = urlsplit(texto)
    caminho = partes.path if partes.scheme or partes.netloc else texto.split("?")[0].split("#")[0]
    caminho = unquote(caminho)
    if not caminho.startswith("/"):
        caminho = "/" + caminho
    ultimo = caminho.rsplit("/", 1)[-1]
    if "." not in ultimo and not caminho.endswith("/"):
        caminho += "/"
    return caminho


def u_de(sal, dominio_do_sorteio, path):
    """Uniforme em [0,1) determinístico para (sal, domínio do sorteio, página).

    `hashlib`, nunca `hash()`: o built-in é aleatorizado por processo desde o
    Python 3.3 e devolveria uma coorte diferente a cada execução — o oposto de
    reprodutível.
    """
    material = "\n".join((sal, dominio_do_sorteio, normaliza_path(path))).encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def atribui_braco(sal, path, bracos):
    """Braço da página. Fatias iguais, fronteira determinística pelo hash."""
    if len(bracos) < 2:
        raise ValueError("um experimento precisa de pelo menos dois braços")
    u = u_de(sal, "braco", path)
    indice = int(u * len(bracos))
    if indice >= len(bracos):        # u < 1 sempre, mas ponto flutuante merece guarda
        indice = len(bracos) - 1
    return bracos[indice], u


def permutacao_faq(sal, path, n):
    """Ordem alternativa do FAQ: permutação determinística, sempre ≠ identidade.

    Fisher-Yates alimentado por sha256 — não por `random`, para não depender da
    implementação do Mersenne Twister nem de estado global de processo. Com
    n = 2 (a maioria das páginas do acervo que têm FAQ) a permutação é a
    inversão; com n ≥ 3 é embaralhamento, e se por acaso sair a identidade,
    inverte-se, senão o braço "variante" seria idêntico ao controle e o teste
    mediria nada.
    """
    if n < 2:
        raise ValueError("ordem de FAQ só faz sentido com duas perguntas ou mais")
    ordem = list(range(n))
    base = "\n".join((sal, "ordem_faq", normaliza_path(path))).encode("utf-8")
    for i in range(n - 1, 0, -1):
        digest = hashlib.sha256(base + b"\n" + str(i).encode("ascii")).digest()
        j = int.from_bytes(digest[:8], "big") % (i + 1)
        ordem[i], ordem[j] = ordem[j], ordem[i]
    if ordem == list(range(n)):
        ordem.reverse()
    return ordem


def carrega_detectores(raiz):
    """Detectores canônicos de `generate-v2-publication-severity`.

    Importar em vez de recopiar: promessa de resultado (Provimento OAB
    205/2021) e defeito de encoding já têm detector com controle positivo neste
    repositório. Uma segunda tabela divergiria da primeira e a página reprovada
    pelo gate de publicação passaria pelo gate do experimento.
    """
    caminho = os.path.join(raiz, SEVERIDADE_REL)
    if not os.path.isfile(caminho):
        raise FonteAusente(
            f"{SEVERIDADE_REL} não existe — é dele que saem os detectores de promessa "
            "de resultado e de encoding; sem ele o experimento não valida texto")
    loader = SourceFileLoader("severidade_v2_para_experimentos", caminho)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    for nome in ("detect_promise", "detect_encoding_defects"):
        if not hasattr(modulo, nome):
            raise FonteAusente(f"{SEVERIDADE_REL} não expõe {nome}()")
    return modulo


# ── contrato de texto ────────────────────────────────────────────────────────

_ESPACO = re.compile(r"\s+")

# Vocabulário interno que jamais pode vazar para o público (CLAUDE.md §8).
#
# A DIVISÃO EM DOIS PADRÕES NÃO É ESTILO: "TODO" com re.IGNORECASE casa a
# palavra portuguesa **todo**, e a primeira versão deste módulo reprovou por
# "vocabulário interno" 19 H1 legítimos do acervo — "Nem todo conteúdo precisa
# de processo judicial para sair do ar" entre eles. É o falso positivo que o
# CLAUDE.md §5 manda medir antes de confiar num detector novo.
#
# Medido em 2026-09-10 sobre os 11.201 registros de data/editorial/v2_pages/
# (h1, title e o recorte de meta description do opening): os dois padrões
# abaixo dão ZERO ocorrência — nenhum falso positivo — e continuam reprovando
# o texto que de fato vazaria (provado por controle positivo em
# tools/test_generate_experimento.py).
VAZAMENTO_SENSIVEL = re.compile(r"\b(TODO|FIXME|XXX|TBD|CTA)\b")
VAZAMENTO_INSENSIVEL = re.compile(
    r"\b(placeholder|lorem\s+ipsum|rascunho|seed|template|molde|call\s+to\s+action)\b",
    re.IGNORECASE)


def vazamento_interno(texto):
    """Marca de vocabulário interno no texto, ou None."""
    for padrao in (VAZAMENTO_SENSIVEL, VAZAMENTO_INSENSIVEL):
        achado = padrao.search(texto or "")
        if achado:
            return achado.group(0)
    return None


def limpa(texto):
    return _ESPACO.sub(" ", (texto or "").strip())


def valida_titulo(texto, detectores, titulos_ocupados=()):
    """Motivos pelos quais este texto NÃO pode virar `<title>`. Lista vazia = pode."""
    motivos = []
    t = limpa(texto)
    if not t:
        return ["vazio"]
    if len(t) < TITULO_MIN:
        motivos.append(f"titulo_curto:{len(t)}")
    if len(t) > TITULO_MAX:
        motivos.append(f"titulo_longo:{len(t)}")
    if t in titulos_ocupados:
        motivos.append("titulo_duplicado_no_acervo")
    motivos.extend("promessa_oab:" + tag for tag in detectores.detect_promise(t))
    motivos.extend("encoding:" + d for d in detectores.detect_encoding_defects(t))
    marca = vazamento_interno(t)
    if marca:
        motivos.append("vocabulario_interno:" + marca)
    return motivos


def valida_meta(texto, detectores, metas_ocupadas=()):
    """Motivos pelos quais este texto NÃO pode virar meta description."""
    motivos = []
    t = limpa(texto)
    if not t:
        return ["vazio"]
    if len(t) < META_MIN:
        motivos.append(f"meta_curta:{len(t)}")
    if len(t) > META_MAX:
        motivos.append(f"meta_longa:{len(t)}")
    if t in metas_ocupadas:
        motivos.append("meta_duplicada_no_acervo")
    motivos.extend("promessa_oab:" + tag for tag in detectores.detect_promise(t))
    motivos.extend("encoding:" + d for d in detectores.detect_encoding_defects(t))
    marca = vazamento_interno(t)
    if marca:
        motivos.append("vocabulario_interno:" + marca)
    return motivos


_FIM_DE_FRASE = re.compile(r"(?<=[.!?])\s+")


def recorte_por_frase(texto, minimo, maximo):
    """Prefixo de `texto` formado por frases INTEIRAS que caiba em [min, max].

    Corte só em fronteira de frase: o CLAUDE.md §8 trata fragmento truncado e
    conectivo pendurado como falha P0, e cortar em N caracteres produz
    exatamente isso. Se nenhuma combinação de frases inteiras couber na faixa,
    devolve None — a página fica INELEGÍVEL, e não se inventa texto para ela.
    """
    base = limpa(texto)
    if not base:
        return None
    acumulado = ""
    for frase in _FIM_DE_FRASE.split(base):
        candidato = (acumulado + " " + frase).strip() if acumulado else frase.strip()
        if len(candidato) > maximo:
            break
        acumulado = candidato
        if len(acumulado) >= minimo:
            return acumulado
    return None


# ── ledger ───────────────────────────────────────────────────────────────────

def caminho_do_ledger(raiz):
    return os.path.join(raiz, LEDGER_REL)


def le_ledger(raiz):
    """Registros do ledger. Arquivo ausente é lista vazia — ausência é ausência.

    Linha ilegível NÃO é ignorada em silêncio: vira exceção, porque um
    experimento que sumiu do ledger por causa de uma linha corrompida liberaria
    o teto de 5% para outro experimento em cima das mesmas páginas.
    """
    caminho = caminho_do_ledger(raiz)
    if not os.path.isfile(caminho):
        return []
    registros = []
    with open(caminho, encoding="utf-8") as handle:
        for numero, linha in enumerate(handle, 1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError as erro:
                raise ValueError(f"{LEDGER_REL}:{numero} não é JSON válido: {erro}") from erro
    return registros


def acrescenta_ao_ledger(raiz, registro):
    """Acrescenta UMA linha ao ledger, sob lock exclusivo. Nunca reescreve.

    O ledger é append-only por decisão: cada experimento e cada medição é um
    fato datado, e reescrever a linha antiga apagaria a evidência de qual era a
    regra de veredito no dia em que o experimento nasceu.
    """
    caminho = caminho_do_ledger(raiz)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    trava = caminho + ".lock"
    linha = json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n"
    with open(trava, "a", encoding="utf-8") as guarda:
        fcntl.flock(guarda.fileno(), fcntl.LOCK_EX)
        try:
            with open(caminho, "a", encoding="utf-8") as handle:
                handle.write(linha)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            fcntl.flock(guarda.fileno(), fcntl.LOCK_UN)
    return caminho


def dobra_experimentos(registros):
    """experimento_id -> registro com o estado VIVO, dobrado sobre o ledger.

    O ledger é append-only: a linha de criação nunca é reescrita, e cada
    transição (aplicação, adoção, descarte, cancelamento) entra como uma linha
    `tipo=estado` posterior. Quem quiser saber o estado de hoje tem de DOBRAR
    as linhas na ordem — ler só a linha de criação devolveria para sempre
    "nunca aplicado", e foi assim que a primeira versão deste módulo deixou o
    veredito inalcançável e o teto de 5% ocupado por experimentos já
    encerrados.

    Campos que a transição pode atualizar: `estado`, `aplicado_em` e o motivo.
    """
    vivos = {}
    for registro in registros:
        if registro.get("tipo") != "experimento":
            continue
        eid = registro.get("experimento_id")
        if eid:
            vivos[eid] = dict(registro)
    for registro in registros:
        if registro.get("tipo") != "estado":
            continue
        eid = registro.get("experimento_id")
        alvo = vivos.get(eid)
        if alvo is None:
            continue
        if registro.get("estado"):
            alvo["estado"] = registro["estado"]
        if registro.get("aplicado_em"):
            alvo["aplicado_em"] = registro["aplicado_em"]
        alvo["estado_mudou_em"] = registro.get("gerado_em")
        if registro.get("motivo"):
            alvo["motivo_da_transicao"] = registro["motivo"]
    return vivos


def experimentos_ativos(registros):
    """Só os que ainda ocupam o teto de 5%, já com o estado dobrado."""
    return {eid: reg for eid, reg in dobra_experimentos(registros).items()
            if reg.get("estado") in ESTADOS_ATIVOS}


def paginas_ocupadas(registros):
    """path → experimento_id, para toda página em experimento ativo.

    Duas variantes ao mesmo tempo na mesma página tornam o desfecho
    ininterpretável (interferência); a página é recusada, com o motivo.
    """
    ocupadas = {}
    for eid, registro in experimentos_ativos(registros).items():
        for item in registro.get("coorte", []):
            caminho = normaliza_path(item.get("path"))
            if caminho:
                ocupadas[caminho] = eid
    return ocupadas


def agora_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ── desfechos: as séries REAIS do disco, com as ressalvas que elas próprias ──
#    declaram. Nenhuma métrica de conversão é inventada aqui: o portal não
#    mede conversão por página, e um desfecho que não existe no disco não entra
#    no catálogo.

BOT_ROTAS_REL = "data/ops/origin_bot_routes_daily.jsonl"
BING_REL = "data/ops/bing_webmaster_daily.jsonl"
CLARITY_REL = "data/ops/clarity_insights_daily.jsonl"

# Só bot cuja função DECIDE citação. `training` (gptbot, amazonbot, claudebot)
# fica de fora de propósito: medido em 2026-09-10 sobre origin_bot_routes_daily,
# treino é 58.246 das 126.480 requisições da série e não indica que a página foi
# lida para responder a alguém. A tabela de funções é a de tools/botagents.py —
# fonte única, importada, nunca recopiada.
FUNCOES_DE_IA = ("search", "user")

DESFECHOS = {
    "bot_ia_leituras": {
        "descricao": "requisições de bot de busca/assistente por rota e por dia",
        "unidade": "requisições",
        "modelo": "poisson",
        "fonte": BOT_ROTAS_REL,
        "chave": "top_routes[].route × date, agent_key com FUNCAO em " + str(list(FUNCOES_DE_IA)),
        "ressalvas": [
            "é medição de ORIGEM, não de borda: a Cloudflare serve o acervo com "
            "s-maxage=604800, então todo HIT nunca chega ao nginx. O número é "
            "PISO (o mesmo `is_lower_bound` que data/ops/ai_citation_signal_daily.jsonl declara).",
            "top_routes tem teto de 200 rotas por janela (`top_routes_cap`): "
            "janela com mais rotas distintas do que isso é truncada, e a "
            "medição conta quantas linhas vieram truncadas.",
            "identidade do agente é por faixa de IP oficial + UA (data/ops/bot_ip_ranges), "
            "não por rDNS nesta série.",
        ],
    },
    "bing_impressoes": {
        "descricao": "impressões do Bing por página e por dia",
        "unidade": "impressões",
        "modelo": "poisson",
        "fonte": BING_REL,
        "chave": "tipo=pagina_diaria (Query traz a URL); por consulta só como reserva",
        "ressalvas": [
            "linha `pagina_diaria` é o TOTAL do dia e a soma das linhas por consulta "
            "é menor (medido 2026-09-10: 277 contra 152 na mesma página-dia, porque a "
            "quebra por consulta é truncada). Somar as duas famílias duplicaria a contagem.",
            "a coleta é esparsa: em 2026-09-10 a série tinha três datas com página "
            "(2026-08-21, 2026-08-28, 2026-09-04), não uma por dia.",
        ],
    },
    "bing_cliques": {
        "descricao": "cliques do Bing por página e por dia",
        "unidade": "cliques",
        "modelo": "poisson",
        "fonte": BING_REL,
        "chave": "tipo=pagina_diaria (Query traz a URL); por consulta só como reserva",
        "ressalvas": ["mesma esparsidade das impressões; clique é evento raro e "
                      "costuma ficar abaixo de qualquer piso de decisão."],
    },
    "clarity_sessoes": {
        "descricao": "sessões do Clarity por URL",
        "unidade": "sessões",
        "modelo": "poisson",
        "fonte": CLARITY_REL,
        "chave": "linhas com dimensoes=['URL'], sessionsCount por Url",
        "ressalvas": [
            "janelas NÃO são somáveis entre si: cada linha tem `janela_dias` própria "
            "(medido 2026-09-10: duas coletas, uma de 1 dia e outra de 3).",
            "`sessionsCount` vem nulo em parte das métricas da mesma URL (17 de 30 "
            "URLs na coleta de 2026-08-29); vale o maior valor não nulo.",
            "é ranking de topo, não o acervo: URL ausente da coleta é ausência de "
            "amostra, não zero sessão.",
        ],
    },
}

DESFECHO_PRIMARIO_PADRAO = "bot_ia_leituras"


def _carrega_botagents(raiz):
    caminho = os.path.join(raiz, "tools", "botagents.py")
    if not os.path.isfile(caminho):
        raise FonteAusente("tools/botagents.py não existe — é a fonte única da "
                           "identidade e da função de cada bot")
    loader = SourceFileLoader("botagents_para_experimentos", caminho)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def _linhas(caminho):
    with open(caminho, encoding="utf-8") as handle:
        for numero, linha in enumerate(handle, 1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                yield numero, json.loads(linha)
            except json.JSONDecodeError:
                continue


def le_bot_ia_por_rota(raiz, inicio, fim):
    """{(date, path): requisições} de bot de busca/assistente, mais ressalvas.

    `summable: true` na própria linha da série autoriza somar janelas do mesmo
    dia — é o oposto de `edge_bot_agents_daily`, que é cumulativo e onde somar
    seria contar o mesmo tráfego várias vezes.
    """
    caminho = os.path.join(raiz, BOT_ROTAS_REL)
    if not os.path.isfile(caminho):
        raise FonteAusente(f"{BOT_ROTAS_REL} não existe — é a série de leitura de bot por rota")
    bots = _carrega_botagents(raiz)
    contagem = {}
    truncadas = 0
    nao_somaveis = 0
    agentes = set()
    for _, registro in _linhas(caminho):
        data = str(registro.get("date") or "")
        if not (inicio <= data <= fim):
            continue
        chave = registro.get("agent_key")
        if bots.FUNCAO.get(chave) not in FUNCOES_DE_IA:
            continue
        if registro.get("summable") is not True:
            nao_somaveis += 1
            continue
        rotas = registro.get("top_routes") or []
        if registro.get("distinct_routes_in_window", 0) > len(rotas):
            truncadas += 1
        agentes.add(chave)
        for rota in rotas:
            caminho_norm = normaliza_path(rota.get("route"))
            if not caminho_norm:
                continue
            contagem[(data, caminho_norm)] = contagem.get((data, caminho_norm), 0) + int(rota.get("requests") or 0)
    ressalvas = list(DESFECHOS["bot_ia_leituras"]["ressalvas"])
    ressalvas.append(f"janelas truncadas pelo top_routes_cap no período: {truncadas}")
    if nao_somaveis:
        ressalvas.append(f"linhas sem summable=true descartadas: {nao_somaveis}")
    return contagem, {"agentes": sorted(agentes), "janelas_truncadas": truncadas,
                      "linhas_nao_somaveis": nao_somaveis, "ressalvas": ressalvas}


def le_bing_por_pagina(raiz, inicio, fim):
    """{(date, path): {'impressoes', 'cliques', 'origem'}} do Bing Webmaster.

    `pagina_diaria` é o total do dia da página e vence; a quebra por consulta
    (`pagina_consulta`/`consulta_pagina`) só entra onde não existe total, e aí
    a página-dia fica marcada como PARCIAL — nunca as duas famílias somadas.
    """
    caminho = os.path.join(raiz, BING_REL)
    if not os.path.isfile(caminho):
        raise FonteAusente(f"{BING_REL} não existe — é a série de impressões e cliques do Bing")
    total = {}
    por_consulta = {}
    coletas = {}
    for _, registro in _linhas(caminho):
        data = str(registro.get("Date") or "")
        if not (inicio <= data <= fim):
            continue
        tipo = registro.get("tipo")
        colet = registro.get("coletado_em") or ""
        if tipo == "pagina_diaria":
            alvo = normaliza_path(registro.get("Query"))
            if not alvo:
                continue
            # Recoleta do mesmo dia: vale a coleta mais recente, nunca a soma.
            chave = (data, alvo)
            if coletas.get(chave, "") <= colet:
                coletas[chave] = colet
                total[chave] = {"impressoes": int(registro.get("Impressions") or 0),
                                "cliques": int(registro.get("Clicks") or 0),
                                "origem": "pagina_diaria", "parcial": False}
        elif tipo in ("pagina_consulta", "consulta_pagina"):
            alvo = normaliza_path(registro.get("Pagina"))
            if not alvo:
                continue
            chave = (data, alvo, registro.get("Consulta") or registro.get("Query") or "")
            anterior = por_consulta.get(chave)
            if anterior is None or anterior[2] <= colet:
                por_consulta[chave] = (int(registro.get("Impressions") or 0),
                                       int(registro.get("Clicks") or 0), colet)
    reserva = {}
    for (data, alvo, _consulta), (imp, cli, _c) in por_consulta.items():
        acumulado = reserva.setdefault((data, alvo), {"impressoes": 0, "cliques": 0,
                                                      "origem": "por_consulta", "parcial": True})
        acumulado["impressoes"] += imp
        acumulado["cliques"] += cli
    for chave, valor in reserva.items():
        total.setdefault(chave, valor)
    datas = sorted({d for d, _ in total})
    ressalvas = list(DESFECHOS["bing_impressoes"]["ressalvas"])
    ressalvas.append(f"datas com página no período: {datas or 'nenhuma'}")
    return total, {"datas": datas, "paginas_dia": len(total),
                   "parciais": sum(1 for v in total.values() if v["parcial"]),
                   "ressalvas": ressalvas}


def le_clarity_por_url(raiz, inicio, fim):
    """Coletas do Clarity com dimensão URL, cada uma com sua janela.

    Devolve uma LISTA de coletas, não uma soma: janelas de 1 e de 3 dias se
    sobrepõem e somá-las contaria a mesma sessão duas vezes.
    """
    caminho = os.path.join(raiz, CLARITY_REL)
    if not os.path.isfile(caminho):
        raise FonteAusente(f"{CLARITY_REL} não existe — é a série de sessões do Clarity")
    coletas = []
    for _, registro in _linhas(caminho):
        if (registro.get("dimensoes") or []) != ["URL"]:
            continue
        colet = str(registro.get("coletado_em") or "")
        if colet[:10] and not (inicio <= colet[:10] <= fim):
            continue
        sessoes = {}
        for metrica in registro.get("metricas") or []:
            for item in metrica.get("information") or []:
                alvo = normaliza_path(item.get("Url"))
                bruto = item.get("sessionsCount")
                if not alvo or bruto is None:
                    continue
                sessoes[alvo] = max(sessoes.get(alvo, 0), int(bruto))
        coletas.append({"coletado_em": colet, "janela_dias": registro.get("janela_dias"),
                        "urls": len(sessoes), "sessoes": sessoes})
    return coletas, {"coletas": len(coletas),
                     "janelas": sorted({c["janela_dias"] for c in coletas}),
                     "ressalvas": list(DESFECHOS["clarity_sessoes"]["ressalvas"])}
