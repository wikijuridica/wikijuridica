#!/usr/bin/env python3
"""cloudflare_auth.py — fonte única da credencial Cloudflare para as ferramentas de borda.

MEDIÇÃO (2026-09-02/03, engenheiro-chefe). `.env.local` guarda DUAS credenciais
para a mesma conta:

  CLOUDFLARE_ZONE_TOKEN — Bearer de ESCOPO DE ZONA (criado em 2026-08-19 pela
      própria API). Lê: Zone Read, Analytics Read, Cache Purge, Zone Settings
      Read, Cache Settings Read, DNS Read; na conta: Account Analytics Read.
      NÃO lê `bot_management` nem a fase `http_request_firewall_custom`, e NÃO
      escreve ruleset (PUT/PATCH devolvem 403 / código 10000 "Authentication
      error" / "request is not authorized" — medido). É o menor privilégio:
      usar primeiro sempre que ele alcançar o endpoint.

  CLOUDFLARE_EMAIL + CLOUDFLARE_API_TOKEN — apesar do nome da segunda
      variável, isto é a GLOBAL API KEY da conta. Autentica SÓ pelo par de
      cabeçalhos `X-Auth-Email` / `X-Auth-Key`; testada como
      "Authorization: Bearer" ela devolve "Invalid API Token" (código 1000) —
      e foi por isso que o repositório a registrou por meses como "inválida"
      (o sintoma estava certo, a causa errada). Lê e ESCREVE tudo: é a única
      credencial que alcança `bot_management`, a fase
      `http_request_firewall_custom` e o PUT de Cache Rule.

REGRA DE OURO, e ela é o motivo deste módulo existir: NUNCA usar a Global API
Key como "Authorization: Bearer". Confundir os dois modos foi exatamente o que
produziu o diagnóstico errado descrito acima.

Até 2026-09-03 a função que decide qual credencial usar estava COPIADA (byte a
byte, com pequenas divergências de ordem) em 10 ferramentas e importada por
`SourceFileLoader` em mais 4. Em 5 das cópias a ordem verificava
`CLOUDFLARE_API_TOKEN` ANTES de olhar o token de zona — então elas abortavam
com "credencial ausente" mesmo com o token de zona, sozinho, perfeitamente
capaz de responder. Este módulo fecha as duas dívidas: uma fonte só, e a
ordem correta (menor privilégio primeiro) em todo lugar que a consome.

USO — quatro escopos, cada um resolve para a credencial que de fato alcança o
endpoint (ver `cabecalhos()` para o mapeamento exato):

    from tools import cloudflare_auth   # ou, de dentro de tools/:
                                         # sys.path.insert(0, os.path.dirname(
                                         #     os.path.abspath(__file__)))
                                         # import cloudflare_auth

    cab, rotulo = cloudflare_auth.cabecalhos("leitura")
    dados, erro = cloudflare_auth.pega(url, "leitura")
    zid, erro = cloudflare_auth.zona_id("wikijuridica.com.br")
    ok, detalhe = cloudflare_auth.verificar("leitura")

O plano Free do GraphQL Analytics recusa consulta com janela maior que 1 dia
por chamada (medido pelos consumidores deste módulo) — daí
`JANELA_MAXIMA_DIAS_FREE`, para quem precisar fatiar uma consulta.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")
ENV_PADRAO = os.path.join(RAIZ, ".env.local")
API = "https://api.cloudflare.com/client/v4"

# O plano Free do Cloudflare Analytics (GraphQL) recusa consulta com janela
# maior que 1 dia por chamada — medido por mais de um consumidor deste módulo
# (check-crawler-error-budget, check-reconciliacao-crawl). Quem precisa de uma
# janela maior fatia em passos de no máximo este tanto.
JANELA_MAXIMA_DIAS_FREE = 1

_ESCOPOS = ("leitura", "purga", "escrita", "firewall")

# A IDENTIDADE DE SAÍDA, e por que ela mora AQUI.
#
# Medido em 2026-09-10: as 17 ferramentas de borda que consomem este módulo
# falavam com `api.cloudflare.com` sem definir User-Agent nenhum (12 delas
# acusadas nominalmente pelo gate; as outras 5 chegam lá por `pega`/`graphql`) — e `urllib` manda o
# dele, `Python-urllib/3.11`. Não é disfarce, é pior: é requisição que ninguém
# consegue atribuir a nós, nem no log do operador nem no nosso. O contrato
# (CLAUDE.md secao 11, ordem do dono de 2026-09-05) fixa uma forma só, montada
# em Go por `internal/wikijuridicabot`; este módulo é o equivalente do lado
# Python para a família da borda.
#
# A correção é AQUI e não em 17 arquivos porque a credencial já é resolvida
# aqui: toda requisição de borda passa por `cabecalhos()`, e uma identidade que
# se acrescenta em 17 lugares volta a divergir no primeiro esquecimento —
# foi exatamente assim que a escolha de credencial ficou copiada em dez cópias
# com cinco ordens erradas até 2026-09-03.
#
# O PROPÓSITO É SEMÂNTICO, e sai do ESCOPO em vez de um parâmetro novo: o escopo
# já diz o que a chamada faz. Quem lê métrica não é quem purga cache nem quem
# reescreve ruleset, e é isso que o operador do outro lado precisa distinguir
# quando olha o log. Chamador com propósito mais específico passa `proposito=`.
IDENTIDADE_FORMATO = ("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
                      "+https://wikijuridica.com.br/bot/; %s)")

PROPOSITO_POR_ESCOPO = {
    "leitura": "medicao-de-borda",
    "purga": "purga-de-borda",
    "escrita": "regras-de-borda",
    "firewall": "regras-de-borda",
}


def user_agent(escopo: str, proposito: str | None = None) -> str:
    """A identidade canônica de saída para o escopo dado.

    `proposito` sobrescreve o padrão derivado do escopo. Ele é texto livre em
    minúsculas, como no lado Go (`UserAgentComProposito`), e entra dentro do
    parêntese `compatible` — que é onde o operador do site olha.
    """
    if escopo not in _ESCOPOS:
        raise ValueError(f"escopo invalido: {escopo!r} (esperado um de {_ESCOPOS})")
    return IDENTIDADE_FORMATO % (proposito or PROPOSITO_POR_ESCOPO[escopo])

# rotulo é CONTRATO OBSERVÁVEL: impresso por várias ferramentas e gravado,
# byte a byte, em ops/cloudflare/cache-rule-rollback.json pelo campo
# `_captura.credencial` (tools/generate-cache-rule-rollback). Não renomear.
ROTULO_ZONA = "zone-token"
ROTULO_GLOBAL = "global-api-key"
ROTULO_AUSENTE = "sem-credencial"

_cache_verificar: dict[str, tuple[float, tuple[bool, str]]] = {}
_TTL_VERIFICAR_SEGUNDOS = 3600  # 1h

_cache_zona: dict[tuple[str, str], tuple[str | None, str | None]] = {}


def ambiente(caminho: str | None = None) -> dict:
    """As variáveis `CLOUDFLARE_*`, com o ambiente do processo tendo
    precedência sobre o arquivo — a mesma regra que o cabeçalho do próprio
    `.env.local` documenta ("Variável já presente no ambiente do processo tem
    precedência sobre o valor declarado aqui").

    `caminho` deixa o chamador apontar para outro arquivo — cada ferramenta
    migrada passa a SUA PRÓPRIA constante `ENV` (algumas honram `WIKI_ROOT`,
    outras não; passar o caminho explícito preserva qual arquivo cada uma lê),
    e `check-reconciliacao-crawl` usa isto para isolar teste com `--env-file`
    apontando a um caminho inexistente. Padrão: `RAIZ/.env.local`.

    Nunca lança: arquivo ausente ou ilegível vira dict vazio (mais o que
    estiver em `os.environ`) — ausência de credencial é responsabilidade de
    quem CHAMA decidir (ver `cabecalhos`), não deste leitor.
    """
    dados: dict = {}
    alvo = caminho if caminho is not None else ENV_PADRAO
    try:
        with open(alvo, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                k, v = linha.split("=", 1)
                dados[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    dados.update({k: v for k, v in os.environ.items() if k.startswith("CLOUDFLARE_")})
    return dados


def cabecalhos(escopo: str, env: dict | None = None, proposito: str | None = None):
    """(cabeçalhos_ou_None, rótulo). `rótulo` é sempre um de `ROTULO_ZONA`,
    `ROTULO_GLOBAL`, `ROTULO_AUSENTE` — três strings que são CONTRATO
    OBSERVÁVEL (ver o comentário acima das constantes).

    escopo:
      "leitura" | "purga" — Bearer do token de zona (`CLOUDFLARE_ZONE_TOKEN`),
          o menor privilégio: cobre GET de zona/ruleset/settings e o POST de
          `purge_cache` (Cache Purge está no escopo do token, medido). Sem
          token de zona no ambiente, cai para a Global API Key.
      "escrita" | "firewall" — SEMPRE a Global API Key
          (`CLOUDFLARE_EMAIL` + `CLOUDFLARE_API_TOKEN`, cabeçalhos
          `X-Auth-Email`/`X-Auth-Key`): o token de zona não tem PUT de
          ruleset nem leitura de `bot_management`/WAF (medido). Ir direto para
          a Global Key evita uma chamada à API fadada a falhar por escopo.

    NUNCA devolve `CLOUDFLARE_API_TOKEN` como "Authorization: Bearer" — essa é
    a Global API Key, e nesse cabeçalho ela devolve "Invalid API Token"
    (medido). Um ambiente com `CLOUDFLARE_API_TOKEN` mas sem `CLOUDFLARE_EMAIL`
    e sem `CLOUDFLARE_ZONE_TOKEN` devolve `(None, ROTULO_AUSENTE)` em vez de
    tentar essa combinação — antes de 2026-09-03 cinco das dez cópias faziam
    exatamente essa tentativa fadada.
    """
    identidade = user_agent(escopo, proposito)  # valida o escopo, e é a saída
    if env is None:
        env = ambiente()
    zona_token = env.get("CLOUDFLARE_ZONE_TOKEN")
    email = env.get("CLOUDFLARE_EMAIL")
    global_key = env.get("CLOUDFLARE_API_TOKEN")
    tem_global = bool(email and global_key)

    if escopo in ("escrita", "firewall"):
        if tem_global:
            return ({"X-Auth-Email": email, "X-Auth-Key": global_key,
                      "Content-Type": "application/json",
                      "User-Agent": identidade}, ROTULO_GLOBAL)
        return (None, ROTULO_AUSENTE)

    # "leitura" | "purga": menor privilégio primeiro.
    if zona_token:
        return ({"Authorization": f"Bearer {zona_token}",
                  "Content-Type": "application/json",
                  "User-Agent": identidade}, ROTULO_ZONA)
    if tem_global:
        return ({"X-Auth-Email": email, "X-Auth-Key": global_key,
                  "Content-Type": "application/json",
                  "User-Agent": identidade}, ROTULO_GLOBAL)
    return (None, ROTULO_AUSENTE)


def _requisitar(url: str, cabecalhos_dict: dict, timeout: float = 30):
    """GET cru. Devolve (dados_ou_None, erro_ou_None) — nunca lança. Em erro
    HTTP tenta decodificar o corpo mesmo assim (a API do Cloudflare devolve
    JSON com `errors` mesmo em 4xx), e só cai para o código puro se o corpo
    não for JSON."""
    req = urllib.request.Request(url, headers=cabecalhos_dict)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as erro:
        try:
            return json.loads(erro.read().decode("utf-8")), None
        except Exception:
            return None, f"HTTP {erro.code}"
    except Exception as erro:
        return None, str(erro)[:160]


def pega(url: str, escopo: str, env: dict | None = None, timeout: float = 30,
         proposito: str | None = None):
    """(dados_ou_None, erro_ou_None). GET em `url` com a credencial do
    `escopo` dado. Resolve a credencial a cada chamada — quem faz muitas
    chamadas com o mesmo escopo na mesma execução deve resolver `cabecalhos()`
    uma vez e reusar, como as ferramentas migradas já fazem."""
    cab, _ = cabecalhos(escopo, env=env, proposito=proposito)
    if cab is None:
        return None, ROTULO_AUSENTE
    return _requisitar(url, cab, timeout=timeout)


def graphql(consulta: str, variaveis: dict, escopo: str = "leitura",
            env: dict | None = None, timeout: float = 90,
            proposito: str | None = None):
    """(dados_ou_None, erro). POST em `/graphql` com a credencial do `escopo`
    dado. `dados` é o valor de `data` da resposta (não lança em erro HTTP nem
    em `errors` no corpo — os dois viram `(None, motivo)`)."""
    cab, _ = cabecalhos(escopo, env=env, proposito=proposito)
    if cab is None:
        return None, ROTULO_AUSENTE
    corpo = json.dumps({"query": consulta, "variables": variaveis}).encode("utf-8")
    req = urllib.request.Request(API + "/graphql", data=corpo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        return None, f"HTTP {erro.code}"
    except Exception as erro:
        return None, str(erro)[:160]
    if dados.get("errors"):
        return None, "; ".join(e.get("message", "?") for e in dados["errors"][:2])
    return dados.get("data"), ""


def zona_id(dominio: str, escopo: str = "leitura", env: dict | None = None):
    """(id_ou_None, erro_ou_None). GET `/zones?name=dominio`. O padrão
    `escopo="leitura"` resolve com o token de zona sozinho — "Zone Read" está
    no escopo dele (medido) — sem precisar da Global Key.

    Cache em memória por (domínio, escopo) durante a vida do processo: o id de
    uma zona não muda, e cada ferramenta chamando isto uma vez por execução
    não pesa, mas evita repetir a chamada dentro de uma mesma execução com
    múltiplas consultas."""
    chave = (dominio, escopo)
    if chave in _cache_zona:
        return _cache_zona[chave]
    dados, erro = pega(f"{API}/zones?name={dominio}", escopo, env=env)
    if erro:
        return (None, erro)
    if (dados or {}).get("success") is False:
        msgs = "; ".join(e.get("message", "") for e in (dados or {}).get("errors", []))
        return (None, msgs or "API respondeu sem sucesso")
    resultado_lista = (dados or {}).get("result") or []
    if not resultado_lista:
        return (None, f"zona {dominio} nao encontrada")
    resultado = (resultado_lista[0]["id"], None)
    _cache_zona[chave] = resultado
    return resultado


def verificar(escopo: str, env: dict | None = None):
    """(ok, detalhe). Confere a credencial do escopo dado contra a própria
    API: Bearer via `GET /user/tokens/verify` (só existe para token de API,
    não para Global Key), Global Key via `GET /user` (o inverso: `/tokens/verify`
    não aceita `X-Auth-Key`). Cache em memória de 1h por escopo — nenhuma
    ferramenta deste repositório precisa saber duas vezes por hora que o mesmo
    segredo continua válido."""
    agora = time.time()
    entrada = _cache_verificar.get(escopo)
    if entrada and (agora - entrada[0]) < _TTL_VERIFICAR_SEGUNDOS:
        return entrada[1]
    cab, rotulo = cabecalhos(escopo, env=env)
    if cab is None:
        resultado = (False, ROTULO_AUSENTE)
        _cache_verificar[escopo] = (agora, resultado)
        return resultado
    url = API + ("/user/tokens/verify" if rotulo == ROTULO_ZONA else "/user")
    dados, erro = _requisitar(url, cab, timeout=20)
    if erro:
        resultado = (False, erro)
    else:
        ok = bool((dados or {}).get("success"))
        if ok:
            resultado = (True, rotulo)
        else:
            msgs = "; ".join(e.get("message", "") for e in (dados or {}).get("errors", []))
            resultado = (False, msgs or "API respondeu sem sucesso")
    _cache_verificar[escopo] = (agora, resultado)
    return resultado
