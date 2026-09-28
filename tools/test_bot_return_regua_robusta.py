#!/usr/bin/env python3
"""Guardas da régua de queda de volume do `generate-bot-return-series`.

★ O DEFEITO QUE ESTES TESTES TRAVAM (medido em 2026-09-05 sobre a série real)

A ÚNICA régua de volume era `queda_desde_o_pico_pct`, definida como
`1 - mediana(3 últimas DATAS) / MÁXIMO da janela` — duas coisas erradas de uma
vez: o numerador incluía sempre o PARCIAL de hoje (o mesmo defeito que este
arquivo já corrigira na tendência em 26/08 e que ficou de fora deste campo), e o
denominador era o máximo, que responde "já foi maior um dia", nunca "está caindo
agora". Sob ela, 9 dos 15 bots valiosos passavam de 90%:

    googlebot             -99,2%   veio HOJE, 43 e 36 requisições nos dois
                                   últimos dias completos, contra mediana
                                   própria de 54/dia.
    gptbot               -100,0%   mediana própria de 1 requisição/dia; fez
                                   7, 6 e 9 — SETE VEZES o ritmo dele.
    cloudflare-ai-search  -91,0%   o "pico" (1.647 em 04/09) está DENTRO da
                                   janela comparada: caiu de si mesmo.
    amazonbot             -97,8%   379/dia contra referência de 338.

ATENÇÃO — A QUEDA DESDE O PICO NÃO É FALSA, E NÃO FOI APAGADA. Que o googlebot
tenha feito 4.297 requisições em 10/08 e faça 43/dia agora é fato, e o campo
continua no estado, agora sem o parcial de hoje no numerador. O que ele deixou
de ser é a régua do ALARME: uma lista que inclui bot em crescimento (gptbot a 7×
o próprio ritmo, amazonbot a 379/dia contra 338) não separa nada, e esse ramo
emite severidade alta ao desktop do dono. O alarme passa a sair de
`queda_vs_referencia_pct`; as duas convivem, e os testes cobram as duas.

E o caso real existe: o claudebot SUBIA (207 → 1.374 → 2.574 entre 25 e 27/08) e
cortou a zero em 29/08. Ele tem de continuar sinalizado depois da correção — e
continua, por um TERCEIRO instrumento (AUSÊNCIA), porque o de VOLUME o vê
crescendo 13,6%.

★ POR QUE A FIXTURE É A SÉRIE REAL, E NÃO NÚMERO INVENTADO

Os valores abaixo são `requests_estimated` / `requests_estimated_unverified_ua`
de `data/ops/edge_bot_agents_daily.jsonl` DEPOIS de `edgetelemetry.serie_saneada`
(dedup por (date, agent_key) mantendo a última linha, descarte do fisicamente
impossível), extraídos em 2026-09-05. São medição, congelada para que um teste
de régua não fique intermitente por causa do timer de 30 min que faz append no
ledger — e para que `hoje` seja fixo, já que a régua exclui o dia corrente e sem
congelá-lo o teste mudaria de veredito à meia-noite UTC.

★ POR QUE A INJEÇÃO DE OUTLIER PASSA POR CIMA DO SANITIZADOR

`edgetelemetry` já barra o absurdo grosso (fator de extrapolação > 100×, volume
acima de 20 req/URL/dia) — foi ele que descartou as 4 linhas forjadas de 5 e 100
milhões de requisições do googlebot em 10 e 11/08. Essa é a PRIMEIRA linha de
defesa. Estes testes injetam o outlier direto na série já saneada de propósito:
a régua é a SEGUNDA linha, e ela tem de ser robusta a um dia grande e LEGÍTIMO —
o claudebot fez 43.065 requisições num dia real, e nada nesse número é forjado.
"""
import importlib.machinery
import importlib.util
import pathlib
import statistics
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

HOJE = "2026-09-05"

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK  ' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


def carrega(nome_arquivo, nome_modulo):
    """Importa uma ferramenta sem extensão .py (todas as de tools/ são assim)."""
    spec = importlib.util.spec_from_loader(
        nome_modulo,
        importlib.machinery.SourceFileLoader(nome_modulo, str(RAIZ / "tools" / nome_arquivo)),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


gerador = carrega("generate-bot-return-series", "gerador_bot_return")
checador = carrega("check-bot-abandonment", "checador_bot_abandono")


# [requests_estimated, requests_estimated_unverified_ua] por data.
SERIE_REAL = {
    "googlebot": {"2026-08-04": [0, 0], "2026-08-06": [25, 0], "2026-08-07": [102, 0], "2026-08-08": [2190, 1], "2026-08-09": [1047, 0], "2026-08-10": [4297, 0], "2026-08-11": [1038, 0], "2026-08-12": [49, 0], "2026-08-13": [99, 0], "2026-08-14": [78, 0], "2026-08-15": [78, 0], "2026-08-16": [58, 0], "2026-08-17": [60, 0], "2026-08-18": [223, 0], "2026-08-19": [77, 0], "2026-08-20": [70, 0], "2026-08-21": [36, 0], "2026-08-22": [21, 0], "2026-08-23": [32, 0], "2026-08-24": [32, 0], "2026-08-25": [33, 3], "2026-08-26": [26, 0], "2026-08-27": [19, 0], "2026-08-28": [88, 0], "2026-08-29": [21, 0], "2026-08-30": [76, 0], "2026-08-31": [44, 0], "2026-09-01": [40, 0], "2026-09-02": [50, 0], "2026-09-03": [43, 0], "2026-09-04": [36, 0], "2026-09-05": [7, 0]},
    "gptbot": {"2026-08-04": [9, 0], "2026-08-05": [1, 0], "2026-08-06": [2212, 0], "2026-08-07": [16456, 4], "2026-08-08": [1, 0], "2026-08-09": [1, 0], "2026-08-10": [1, 0], "2026-08-11": [0, 133], "2026-08-12": [1, 0], "2026-08-13": [342, 173], "2026-08-14": [1, 0], "2026-08-15": [1, 0], "2026-08-16": [1, 0], "2026-08-17": [1, 0], "2026-08-18": [1, 30], "2026-08-19": [1, 0], "2026-08-20": [1, 0], "2026-08-21": [1082, 0], "2026-08-22": [1, 60], "2026-08-23": [1, 0], "2026-08-24": [1, 0], "2026-08-25": [1, 0], "2026-08-26": [1, 27], "2026-08-27": [1, 0], "2026-08-28": [1, 0], "2026-08-29": [137, 0], "2026-08-30": [1, 0], "2026-08-31": [336, 0], "2026-09-01": [9, 0], "2026-09-02": [24, 0], "2026-09-03": [7, 0], "2026-09-04": [6, 0], "2026-09-05": [9, 0]},
    "claudebot": {"2026-08-04": [0, 0], "2026-08-07": [43065, 2], "2026-08-08": [20, 0], "2026-08-09": [18, 0], "2026-08-11": [0, 73], "2026-08-12": [0, 0], "2026-08-13": [259, 430], "2026-08-14": [22, 0], "2026-08-15": [20, 0], "2026-08-16": [22, 0], "2026-08-17": [24, 0], "2026-08-18": [24, 30], "2026-08-19": [22, 0], "2026-08-20": [1105, 0], "2026-08-21": [16, 0], "2026-08-22": [21, 47], "2026-08-23": [24, 0], "2026-08-24": [22, 0], "2026-08-25": [23, 0], "2026-08-26": [25, 22], "2026-08-27": [34, 0], "2026-08-28": [3, 0], "2026-08-29": [0, 0], "2026-08-30": [0, 0]},
    "amazonbot": {"2026-08-04": [0, 0], "2026-08-07": [0, 0], "2026-08-09": [1, 0], "2026-08-10": [35, 0], "2026-08-11": [2002, 216], "2026-08-12": [4685, 0], "2026-08-13": [2553, 429], "2026-08-14": [426, 1], "2026-08-15": [174, 0], "2026-08-16": [20, 0], "2026-08-17": [2, 0], "2026-08-18": [0, 72], "2026-08-22": [3, 100], "2026-08-23": [7, 0], "2026-08-24": [383, 0], "2026-08-25": [338, 0], "2026-08-26": [111, 20], "2026-08-27": [17138, 0], "2026-08-28": [2702, 0], "2026-08-29": [485, 0], "2026-08-30": [3, 0], "2026-09-03": [434, 0], "2026-09-04": [379, 0], "2026-09-05": [48, 0]},
    "applebot": {"2026-08-05": [2, 0], "2026-08-06": [0, 0], "2026-08-07": [0, 0], "2026-08-11": [0, 0], "2026-08-12": [0, 0], "2026-08-13": [0, 0], "2026-08-14": [0, 0], "2026-08-25": [38, 0], "2026-08-26": [0, 18], "2026-08-28": [2713, 0], "2026-08-29": [6332, 0], "2026-08-30": [704, 0], "2026-08-31": [209, 0], "2026-09-01": [320, 0], "2026-09-02": [86, 0], "2026-09-03": [26, 0], "2026-09-04": [20, 0], "2026-09-05": [4, 0]},
    "yandexbot": {"2026-08-06": [525, 0], "2026-08-07": [758, 0], "2026-08-09": [2, 0], "2026-08-10": [252, 0], "2026-08-11": [57, 0], "2026-08-12": [198, 0], "2026-08-13": [320, 0], "2026-08-14": [92, 0], "2026-08-15": [3239, 0], "2026-08-16": [4482, 0], "2026-08-17": [35, 0], "2026-08-18": [27, 0], "2026-08-19": [336, 0], "2026-08-20": [174, 0], "2026-08-21": [417, 0], "2026-08-22": [466, 0], "2026-08-23": [9, 0], "2026-08-24": [8, 0], "2026-08-26": [91, 0], "2026-08-27": [2, 0], "2026-08-28": [29, 0], "2026-08-29": [13, 0], "2026-08-30": [61, 0], "2026-08-31": [2, 0], "2026-09-01": [22, 0], "2026-09-02": [8, 0], "2026-09-03": [9, 0], "2026-09-04": [30, 0]},
    "meta-externalagent": {"2026-08-04": [0, 0], "2026-08-07": [0, 0], "2026-08-13": [10080, 1], "2026-08-14": [2100, 1], "2026-08-15": [673, 0], "2026-08-16": [22, 0], "2026-08-18": [2, 0], "2026-08-20": [10606, 0], "2026-08-21": [6, 0], "2026-08-22": [6281, 0], "2026-08-23": [128, 0], "2026-08-26": [0, 18]},
    "bingbot": {"2026-08-04": [0, 0], "2026-08-06": [1, 0], "2026-08-07": [0, 0], "2026-08-08": [23, 0], "2026-08-09": [36, 24], "2026-08-10": [18, 102], "2026-08-11": [24, 0], "2026-08-12": [87, 0], "2026-08-13": [90, 0], "2026-08-14": [38, 880], "2026-08-15": [95, 0], "2026-08-16": [9, 0], "2026-08-17": [34, 0], "2026-08-18": [17, 0], "2026-08-19": [22, 0], "2026-08-20": [523, 0], "2026-08-21": [324, 0], "2026-08-22": [267, 0], "2026-08-23": [218, 0], "2026-08-24": [331, 0], "2026-08-25": [672, 0], "2026-08-26": [415, 1], "2026-08-27": [418, 0], "2026-08-28": [441, 0], "2026-08-29": [419, 0], "2026-08-30": [562, 0], "2026-08-31": [507, 0], "2026-09-01": [447, 0], "2026-09-02": [474, 0], "2026-09-03": [534, 0], "2026-09-04": [464, 0], "2026-09-05": [106, 0]},
}


def borda_de(serie):
    """Converte a fixture no formato que `edgetelemetry.serie_saneada` devolve."""
    return {(data, agente): {
                "requests_estimated": valores[0],
                "requests_estimated_unverified_ua": valores[1],
                "authenticity": "cloudflare_verified_bot_category",
            }
            for agente, dias in serie.items()
            for data, valores in dias.items()}


def estado_de(serie):
    _, estado = gerador.montar(hoje=HOJE, borda=borda_de(serie), borda_descartadas=[],
                               cobertura={}, cobertura_descartadas=[], citacao={})
    return estado


def regua_velha(serie_do_agente):
    """A régua ANTERIOR, reimplementada aqui de propósito.

    Ela NÃO é lida de `git show HEAD:` porque, assim que este trabalho for
    commitado, HEAD passa a ser a versão nova e o teste de mutação compararia
    novo-com-novo — vacuidade permanente, exatamente o formato de trava que
    parece verde e não trava nada. Reimplementada, ela continua sendo a régua
    velha para sempre, e o teste continua discriminando.

        queda = 1 - mediana(requisições das 3 ÚLTIMAS DATAS observadas) / MÁXIMO
    """
    datas = sorted(serie_do_agente)
    valores = [serie_do_agente[d][0] for d in datas]
    pico = max(valores) if valores else 0
    if pico <= 0:
        return None
    return round(100.0 * (1 - (statistics.median(valores[-3:]) / pico)), 1)


def com_outlier(agente, data, valor):
    """Cópia da série real com UM dia isolado substituído por `valor`."""
    copia = {nome: dict(dias) for nome, dias in SERIE_REAL.items()}
    copia[agente][data] = [valor, 0]
    return copia


# ══════════════════════════════════════════════════════════════════════════════
print("1. A régua nova, sobre a série REAL")
estado = estado_de(SERIE_REAL)
agentes = estado["agentes"]

passo(estado["schema_version"] == "bot_return_state_v2",
      f"schema do estado é v2 (recebido: {estado['schema_version']})")
# ★ AS DUAS LEITURAS CONVIVEM, e o teste cobra as duas.
# A queda desde o pico NAO foi apagada: ela e verdadeira e continua no estado.
# O que ela deixou de ser e a regua do ALARME.
passo(all("queda_desde_o_pico_pct" in dados and "queda_vs_referencia_pct" in dados
          for nome, dados in agentes.items() if dados.get("dias_com_visita")),
      "todo agente com visita publica AS DUAS quedas (pico e referência)")

g = agentes["googlebot"]
passo(g["dias_desde_ultima_visita"] == 0,
      f"googlebot visitou HOJE (dias_desde_ultima_visita={g['dias_desde_ultima_visita']})")
passo(g["queda_vs_referencia_pct"] < 90.0,
      f"googlebot NÃO é queda de volume: {g['queda_vs_referencia_pct']}% "
      f"(recente {g['volume_mediano_recente']} vs referência {g['referencia_de_volume']}/dia)")

passo(g["queda_desde_o_pico_pct"] >= 90.0,
      f"e a queda DESDE O PICO do googlebot continua publicada e alta "
      f"({g['queda_desde_o_pico_pct']}%, pico {g['requisicoes_pico']} em "
      f"{g['requisicoes_pico_em']}): ela é verdadeira, só não decide alarme")

p = agentes["gptbot"]
passo(p["queda_vs_referencia_pct"] < 0,
      f"gptbot está CRESCENDO, não caindo: {p['queda_vs_referencia_pct']}% "
      f"(recente {p['volume_mediano_recente']} vs referência {p['referencia_de_volume']}/dia)")

a = agentes["amazonbot"]
passo(a["queda_vs_referencia_pct"] < 90.0 and a["queda_desde_o_pico_pct"] >= 90.0,
      f"amazonbot: -{a['queda_desde_o_pico_pct']}% desde o pico (contexto) mas "
      f"{a['queda_vs_referencia_pct']}% vs referência — está ACIMA da própria "
      f"linha de base e não entra no alarme")

# O PARCIAL DE HOJE SAIU DOS DOIS NUMERADORES. `requisicoes_por_dia_ultimos_3`
# continua sendo as 3 últimas DATAS (fato bruto, inclui hoje); a janela que as
# réguas usam é a de dias com visita COMPLETOS.
passo(g["requisicoes_nos_dias_recentes_completos"][-1] != 7
      and g["requisicoes_por_dia_ultimos_3"][-1] == 7,
      f"o coto de hoje (7 requisições) está no campo bruto "
      f"{g['requisicoes_por_dia_ultimos_3']} e FORA da janela das réguas "
      f"{g['requisicoes_nos_dias_recentes_completos']}")

# ── O sinal verdadeiro tem de sobreviver, e sobrevive pelo OUTRO instrumento.
c = agentes["claudebot"]
passo(c["veredito"] == "abandonou",
      f"claudebot continua sinalizado: veredito={c['veredito']}, "
      f"{c['dias_desde_ultima_visita']} dias sem vir (limite do ritmo dele: "
      f"{c['limite_de_abandono_dias']})")
passo(c["queda_vs_referencia_pct"] < 0,
      f"e a régua de VOLUME o vê crescendo ({c['queda_vs_referencia_pct']}%): "
      f"corte abrupto no meio de uma subida é invisível para volume — quem o "
      f"apanha é a régua de AUSÊNCIA. Dois instrumentos, não um.")

m = agentes["meta-externalagent"]
passo(m["veredito"] == "abandonou" and m["queda_vs_referencia_pct"] >= 90.0,
      f"meta-externalagent continua sinalizado nos dois: {m['veredito']}, "
      f"queda {m['queda_vs_referencia_pct']}%")
for nome in ("applebot", "yandexbot"):
    d = agentes[nome]
    passo(d["veredito"] == "esfriando" and d["queda_vs_referencia_pct"] >= 90.0,
          f"{nome} continua sinalizado: {d['veredito']}, "
          f"queda {d['queda_vs_referencia_pct']}% vs referência "
          f"{d['referencia_de_volume']}/dia")

b = agentes["bingbot"]
passo(b["veredito"] == "ativo" and b["queda_vs_referencia_pct"] < 0,
      f"bingbot, que cresce todo dia, sai como {b['veredito']} "
      f"({b['queda_vs_referencia_pct']}%)")

# ── Invariante: quem veio hoje não é abandonado.
vieram_hoje_e_abandonados = [nome for nome, d in agentes.items()
                             if d.get("dias_desde_ultima_visita") == 0
                             and d.get("veredito") in ("abandonou", "veio_uma_vez_e_sumiu")]
passo(not vieram_hoje_e_abandonados,
      f"nenhum bot com dias_desde_ultima_visita==0 é chamado de abandonado "
      f"(violações: {vieram_hoje_e_abandonados or 'nenhuma'})")


# ══════════════════════════════════════════════════════════════════════════════
print("\n2. MUTAÇÃO — a régua velha, sobre a MESMA série, reprova")
velha_google = regua_velha(SERIE_REAL["googlebot"])
velha_gpt = regua_velha(SERIE_REAL["gptbot"])
velha_amazon = regua_velha(SERIE_REAL["amazonbot"])
passo(velha_google >= 90.0,
      f"régua velha põe googlebot em -{velha_google}% (novo: "
      f"-{g['queda_vs_referencia_pct']}%) — o passo 1 FALHARIA com ela")
passo(velha_gpt >= 90.0,
      f"régua velha põe gptbot em -{velha_gpt}% (novo: "
      f"{p['queda_vs_referencia_pct']}%, crescimento) — o passo 1 FALHARIA com ela")
passo(velha_amazon >= 90.0,
      f"régua velha põe amazonbot em -{velha_amazon}% (novo: "
      f"{a['queda_vs_referencia_pct']}%) — o passo 1 FALHARIA com ela")
passo(regua_velha(SERIE_REAL["claudebot"]) >= 90.0
      and agentes["claudebot"]["veredito"] == "abandonou",
      "e o claudebot era o ÚNICO caso em que a régua velha acertava por acidente: "
      "ela o acusava junto com todos os outros, sem separar nada")


# ══════════════════════════════════════════════════════════════════════════════
print("\n3. OUTLIER — um dia isolado 1000× acima da mediana não move a referência")
mediana_google = statistics.median([v[0] for d, v in SERIE_REAL["googlebot"].items()
                                    if v[0] > 0 and d != HOJE])
gigante = int(mediana_google * 1000)
serie_com_pico = com_outlier("googlebot", "2026-08-19", gigante)
depois = estado_de(serie_com_pico)["agentes"]["googlebot"]
passo(depois["referencia_de_volume"] == g["referencia_de_volume"],
      f"referência intacta com um dia de {gigante} requisições injetado "
      f"(mediana do bot: {mediana_google}/dia): "
      f"{g['referencia_de_volume']} → {depois['referencia_de_volume']}")
passo(depois["queda_vs_referencia_pct"] == g["queda_vs_referencia_pct"],
      f"queda intacta: {g['queda_vs_referencia_pct']}% → "
      f"{depois['queda_vs_referencia_pct']}%")
passo(depois["requisicoes_pico"] == gigante,
      f"o pico bruto REGISTRA o dia ({depois['requisicoes_pico']}) — ele continua "
      f"sendo fato observado, só não é mais régua")
velha_com_pico = regua_velha(serie_com_pico["googlebot"])
passo(velha_com_pico > velha_google,
      f"MUTAÇÃO do mesmo caso: a régua velha vai de -{velha_google}% para "
      f"-{velha_com_pico}% só por causa do dia injetado; a nova não se move")

# O mesmo, com um valor GRANDE E LEGÍTIMO: 43.065 é o dia real do claudebot em
# 07/08, que passou por todo o sanitizador. Robustez não pode depender de o
# número ser implausível.
serie_legit = com_outlier("googlebot", "2026-08-19", 43065)
depois_legit = estado_de(serie_legit)["agentes"]["googlebot"]
passo(depois_legit["referencia_de_volume"] == g["referencia_de_volume"]
      and depois_legit["queda_vs_referencia_pct"] == g["queda_vs_referencia_pct"],
      f"referência e queda também intactas com um dia LEGÍTIMO de 43.065 "
      f"(o dia real do claudebot em 07/08)")


# ══════════════════════════════════════════════════════════════════════════════
print("\n4. O ramo de notificação da queda deixou de ser código morto")


class SubprocessFalso:
    """Captura as chamadas a notify-owner em vez de alertar o dono de verdade."""

    def __init__(self):
        self.chamadas = []

    def run(self, comando, **kwargs):
        self.chamadas.append(list(comando))

        class Resultado:
            returncode = 0
        return Resultado()


relatorio = checador.avaliar(estado)
passo("quedas_de_volume" in relatorio,
      f"`avaliar` devolve `quedas_de_volume` com {len(relatorio['quedas_de_volume'])} bot(s): "
      + ", ".join(q["agent_key"] for q in relatorio["quedas_de_volume"]))
passo({q["agent_key"] for q in relatorio["quedas_de_volume"]}
      == {"applebot", "yandexbot", "meta-externalagent"},
      "e são exatamente os três que caíram de verdade — googlebot, gptbot, "
      "amazonbot, claudebot, perplexitybot e cloudflare-ai-search saíram da lista")

# O defeito: `notificar` lia `relatorio.get("quedas")`, chave que nunca existiu.
# Com `perdas` vazia e quedas presentes, o fluxo caía no `--resolvido`.
sem_perdas = dict(relatorio, perdas=[])
original = checador.subprocess
falso = SubprocessFalso()
checador.subprocess = falso
try:
    checador.notificar(sem_perdas)
finally:
    checador.subprocess = original

chaves = [c[c.index("--chave") + 1] for c in falso.chamadas if "--chave" in c]
resolvidos = [c for c in falso.chamadas if "--resolvido" in c]
passo(chaves == ["bot-queda-de-volume"],
      f"sem perdas e COM quedas, sai um alerta de queda: chaves={chaves}")
passo(not resolvidos,
      f"e NENHUM `--resolvido` (o defeito era declarar resolvido durante a queda): "
      f"{len(resolvidos)} chamada(s) de resolução")
passo(any("alta" in c for c in falso.chamadas),
      "com severidade alta")

# Contraprova: sem perdas E sem quedas, aí sim resolve as duas chaves.
falso2 = SubprocessFalso()
checador.subprocess = falso2
try:
    checador.notificar({"perdas": [], "quedas_de_volume": [], "bots_valiosos_ativos": 15})
finally:
    checador.subprocess = original
chaves2 = sorted(c[c.index("--chave") + 1] for c in falso2.chamadas)
passo(chaves2 == ["bot-abandono", "bot-queda-de-volume"]
      and all("--resolvido" in c for c in falso2.chamadas),
      f"sem perdas E sem quedas, as duas chaves se resolvem: {chaves2}")


print()
print("FALHOU" if falhou else "todos os passos verdes")
sys.exit(falhou)
