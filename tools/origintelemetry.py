"""Leitor canônico do ledger de tráfego de bot da ORIGEM.

POR QUE ESTE MÓDULO EXISTE (2026-08-20).

`data/ops/origin_bot_traffic_daily.jsonl` grava INCREMENTOS: uma linha por janela
de cursor (~30 min; medido, 35 linhas num único dia só de googlebot), cada uma com
`"summable": true`. O produtor documenta a regra em
`tools/generate-bot-traffic-origin:70-85` — *"as linhas do ledger são INCREMENTOS.
Quem consome SOMA por (date, agent_key), não pega a última."*

Nenhum leitor implementava essa regra. O único consumidor
(`tools/check-bot-telemetry-honesty`) valida linha a linha e nunca agrega. O
resultado: quem precisava do total reimplementava a leitura na hora, e em
2026-08-20 alguém aplicou a convenção do ledger da BORDA — que é cumulativo e se
lê deduplicando — obtendo **Googlebot = 7 requisições em 7 dias** onde havia
**269**. Fator de 38×, e a conclusão errada quase virou premissa de um plano.

SEGUNDA ARMADILHA, achada ao escrever este módulo: o mesmo arquivo carrega DOIS
schemas com nomes de campo diferentes para o mesmo fato.

    origin_bot_traffic_daily_v2  ->  requests_verified / requests_unverified
    origin_bot_traffic_daily_v3  ->  requests_authentic / requests_forged
                                     / requests_unverifiable

Somar só `requests_authentic` ignora silenciosamente todas as linhas v2 (579 no
corpus de hoje); somar só `requests_verified` ignora as v3 (567). Quem escolhe um
nome de campo e segue em frente subconta sem receber erro nenhum.

DIVISÃO DE TRABALHO ENTRE OS DOIS LEDGERS — escolha pela pergunta:

  contagem, volume, cobertura  ->  BORDA  (tools/edgetelemetry.py)
  autenticidade, forjado,      ->  ORIGEM (este módulo)
  PerplexityBot, referer

A origem só enxerga o que o cache da Cloudflare não absorveu (`s-maxage=604800`):
ela é PISO de volume, nunca contador. Em 19/08 o Googlebot deu 77 na borda e 1 na
origem lida errado — e nenhum dos dois números está errado, eles medem coisas
diferentes.
"""

import json
import os
from collections import Counter, defaultdict

LEDGER_REL = "data/ops/origin_bot_traffic_daily.jsonl"

# Nome do campo por schema. A ordem importa: v3 é o mais recente e mais preciso
# (separa "forjado" de "não verificável"), então é consultado primeiro.
CAMPOS_AUTENTICO = ("requests_authentic", "requests_verified")
CAMPOS_FORJADO = ("requests_forged",)
CAMPOS_NAO_VERIFICAVEL = ("requests_unverifiable", "requests_unverified")


def _primeiro_campo(registro, nomes):
    """Devolve (valor, nome_do_campo_usado) do primeiro nome presente.

    Ausência total devolve (0, None) — e não exceção: uma linha de schema
    desconhecido não pode derrubar a leitura das outras, mas é contabilizada
    como schema não reconhecido para quem quiser reprovar por isso.
    """
    for nome in nomes:
        if nome in registro:
            valor = registro.get(nome)
            if isinstance(valor, (int, float)):
                return int(valor), nome
    return 0, None


def serie_somada(raiz=".", inicio=None, fim=None):
    """Soma o ledger da origem por (date, agent_key), como o produtor manda.

    `inicio` e `fim` são datas ISO inclusivas (AAAA-MM-DD) ou None.

    Devolve (por_agente, diagnostico), onde por_agente mapeia
    agent_key -> {"autenticas", "forjadas", "nao_verificaveis", "linhas", "dias"}
    e diagnostico traz o que foi ignorado e por quê — porque leitura silenciosa é
    exatamente o que produziu o erro de 38×.
    """
    caminho = os.path.join(raiz, LEDGER_REL)
    por_agente = defaultdict(lambda: {
        "autenticas": 0, "forjadas": 0, "nao_verificaveis": 0, "linhas": 0, "dias": set(),
    })
    diagnostico = {
        "linhas_lidas": 0,
        "linhas_ilegiveis": 0,
        "linhas_nao_somaveis": 0,
        "linhas_fora_da_janela": 0,
        "linhas_sem_campo_conhecido": 0,
        "schemas": Counter(),
        "campos_usados": Counter(),
    }

    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError:
                diagnostico["linhas_ilegiveis"] += 1
                continue
            diagnostico["linhas_lidas"] += 1
            diagnostico["schemas"][registro.get("schema_version", "(sem)")] += 1

            data = registro.get("date") or ""
            if (inicio and data < inicio) or (fim and data > fim):
                diagnostico["linhas_fora_da_janela"] += 1
                continue

            # `summable` é a declaração do produtor de que a linha é incremento.
            # Linha sem ela (ou com false) NÃO entra na soma: seria dobrar.
            if not registro.get("summable"):
                diagnostico["linhas_nao_somaveis"] += 1
                continue

            autenticas, campo = _primeiro_campo(registro, CAMPOS_AUTENTICO)
            if campo is None:
                diagnostico["linhas_sem_campo_conhecido"] += 1
                continue
            diagnostico["campos_usados"][campo] += 1
            forjadas, _ = _primeiro_campo(registro, CAMPOS_FORJADO)
            nao_verificaveis, _ = _primeiro_campo(registro, CAMPOS_NAO_VERIFICAVEL)

            agente = registro.get("agent_key") or "(sem agent_key)"
            acumulado = por_agente[agente]
            acumulado["autenticas"] += autenticas
            acumulado["forjadas"] += forjadas
            acumulado["nao_verificaveis"] += nao_verificaveis
            acumulado["linhas"] += 1
            if data:
                acumulado["dias"].add(data)

    for acumulado in por_agente.values():
        acumulado["dias"] = len(acumulado["dias"])
    return dict(por_agente), diagnostico


def leitura_errada_dedup(raiz=".", inicio=None, fim=None):
    """Reproduz DE PROPÓSITO a leitura errada: última linha por (date, agent).

    Existe só para o gate poder demonstrar a diferença com número, em vez de
    afirmar que a regra importa. Não use isto para medir nada.
    """
    caminho = os.path.join(raiz, LEDGER_REL)
    ultima = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError:
                continue
            data = registro.get("date") or ""
            if (inicio and data < inicio) or (fim and data > fim):
                continue
            ultima[(data, registro.get("agent_key"))] = registro
    por_agente = Counter()
    for registro in ultima.values():
        valor, campo = _primeiro_campo(registro, CAMPOS_AUTENTICO)
        if campo is not None:
            por_agente[registro.get("agent_key")] += valor
    return dict(por_agente)
