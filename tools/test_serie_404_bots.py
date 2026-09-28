#!/usr/bin/env python3
"""Guardas de generate-serie-404-bots e check-serie-404-bots (BUG-127: o 404
era a unica superficie servida sem medicao).

Cada caso aqui e uma forma de o gate ficar verde sem ter medido nada, ou de o
gerador somar o que nao devia. O par nasce provando que o gate REPROVA no caso
ruim (exit 1), PASSA no caso bom (exit 0), diz NAO RODOU sem serie (exit 2) e
INCONCLUSIVO com bot ausente ou serie parada (exit 1) — e que o gerador
descarta warming/simulacao pela mesma porta que todo leitor do ledger
(accessledger), deduplica combinacao repetida e e idempotente byte a byte.
"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-serie-404-bots"
GERADOR = RAIZ / "tools" / "generate-serie-404-bots"
HOJE = "2026-09-01"
VALIOSOS = ("googlebot", "bingbot", "applebot", "oai-searchbot")

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


# ---------------------------------------------------------------------------
# O GATE, sobre serie sintetica
# ---------------------------------------------------------------------------

def borda(data, bot, total, n404, **extra):
    registro = {
        "schema_version": "serie_404_bots_v1", "record_type": "borda", "date": data,
        "agent_key": bot, "function": "search", "verified": True,
        "requests_total": total, "requests_200": total - n404, "requests_404": n404,
        "requests_other": 0, "status_counts": {"200": total - n404, "404": n404},
        "share_404": round(n404 / total, 4) if total else None, "combination_rows": 1,
        "path_in_source": False, "br_excluded": False, "source": "edge_bot_status_daily",
    }
    registro.update(extra)
    # Valor None em `extra` REMOVE o campo: "ausente" tem de ser ausente de
    # verdade, senao o caso testa um zero e nao a ausencia.
    for chave in [k for k, v in registro.items() if v is None and k in extra]:
        del registro[chave]
    return json.dumps(registro)


def dia(data, total=1000, n404=0):
    return json.dumps({"schema_version": "serie_404_bots_v1", "record_type": "dia", "date": data,
                       "source": "edge_bot_status_daily", "empty_window": False,
                       "agents_verified": 4, "requests_total": total, "requests_200": total - n404,
                       "requests_404": n404, "share_404": n404 / total, "combination_rows": 4})


def serie(por_bot, inicio="2026-08-25", ndias=7, bots=VALIOSOS, dias_extra=()):
    """por_bot[bot] = lista de (total, n404) por dia, ou um (total, n404) fixo.
    Bot em `bots` fora de por_bot recebe (400, 0) — um dia limpo por dia."""
    base = datetime.date.fromisoformat(inicio)
    linhas = []
    for i in range(ndias):
        data = (base + datetime.timedelta(days=i)).isoformat()
        linhas.append(dia(data))
        for bot in bots:
            valor = por_bot.get(bot, (400, 0))
            if isinstance(valor, list):
                if i >= len(valor) or valor[i] is None:
                    continue
                valor = valor[i]
            if isinstance(valor, dict):
                linhas.append(borda(data, bot, 0, 0, **valor))
            else:
                linhas.append(borda(data, bot, *valor))
    linhas.extend(dias_extra)
    return "\n".join(linhas) + "\n"


def roda_gate(conteudo, *args):
    with tempfile.TemporaryDirectory() as d:
        caminho = pathlib.Path(d) / "serie_404_bots.jsonl"
        if conteudo is not None:
            caminho.write_text(conteudo, encoding="utf-8")
        r = subprocess.run([sys.executable, str(GATE), "--serie", str(caminho),
                            "--hoje", HOJE, *args], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


print("gate — caso bom e caso ruim:")
rc, saida = roda_gate(serie({"googlebot": (76, 1), "oai-searchbot": (359, 2)}))
passo(rc == 0 and "check-serie-404-bots: pass" in saida,
      f"caso bom (googlebot 1 de 76, oai 2 de 359, resto 0): PASSA, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": [(400, 0)] * 6 + [(100, 10)]}))
passo(rc == 1 and "FAIL" in saida and "googlebot_404_acima_do_teto@2026-08-31:10 de 100" in saida,
      f"caso ruim (googlebot 10 de 100 = 10% no ultimo dia): REPROVA, exit {rc}")

rc, saida = roda_gate(serie({"bingbot": [(324, 31)] + [(400, 0)] * 6}))
passo(rc == 1 and "bingbot_404_acima_do_teto@2026-08-25:31 de 324" in saida,
      f"o dia real de 2026-08-21 (bingbot 31 de 324 = 9,6%) dentro da janela: REPROVA, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": (100, 5)}))
passo(rc == 0, f"exatamente 5% (5 de 100) NAO passa do teto: PASSA, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": (100, 6)}))
passo(rc == 1, f"6 de 100 = 6% passa do teto: REPROVA, exit {rc}")

print("gate — piso e regra da janela:")
rc, saida = roda_gate(serie({"googlebot": [(400, 0)] * 6 + [(30, 3)]}))
passo(rc == 0 and "aviso: googlebot@2026-08-31: 3 de 30 = 10.0% (abaixo do piso de 50)" in saida,
      f"um dia de 3 de 30 (abaixo do piso) NAO reprova sozinho, mas sai como aviso: exit {rc}")

rc, saida = roda_gate(serie({"googlebot": (30, 3)}))
passo(rc == 1 and "googlebot_404_acima_do_teto_na_janela:21 de 210" in saida,
      f"3 de 30 TODO dia (21 de 210 = 10% na janela, nenhum dia no piso): REPROVA, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": (400, 0), "facebookexternalhit": (2578, 1210)},
                            bots=VALIOSOS + ("facebookexternalhit",)))
passo(rc == 0 and "FALHA         facebookexternalhit" in saida,
      f"facebookexternalhit a 46,9% aparece como FALHA na tabela e NAO decide o exit: exit {rc}")

print("gate — dado ausente nunca e aprovacao:")
rc, saida = roda_gate(serie({"googlebot": (0, 0)}))
passo(rc == 1 and "INCONCLUSIVO" in saida and "presente na serie com 0 requisicoes" in saida
      and "pass" not in saida.split("\n")[-2],
      f"googlebot presente com 0 de 0 em toda a janela: INCONCLUSIVO, nunca pass, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": (76, 1)}) + "{isto nao e json}\n" + '{"date": "x"}\n')
passo(rc == 0 and "ATENCAO: 2 linha(s) ilegivel(is)" in saida,
      f"linha ilegivel e contada e impressa, nao engolida: exit {rc}")

rc, saida = roda_gate(None)
passo(rc == 2 and "NAO RODOU" in saida, f"serie ausente: NAO RODOU, exit {rc}")

rc, saida = roda_gate("")
passo(rc == 2 and "NAO RODOU" in saida, f"serie vazia: NAO RODOU, exit {rc}")

rc, saida = roda_gate("\n".join(borda("2026-08-3%d" % i, "googlebot", 400, 0) for i in range(1, 2)) + "\n")
passo(rc == 2 and "sem linha \"dia\"" in saida,
      f"serie so com linha borda, sem linha dia (produtor torto): NAO RODOU, exit {rc}")

rc, saida = roda_gate(serie({}, bots=("googlebot", "bingbot", "applebot")))
passo(rc == 1 and "INCONCLUSIVO" in saida and "oai-searchbot: ausente da serie" in saida,
      f"oai-searchbot ausente da janela (resto limpo): INCONCLUSIVO, exit {rc}")

rc, saida = roda_gate(serie({}, inicio="2026-08-20", ndias=7))
passo(rc == 1 and "serie parada" in saida,
      f"ultima linha de 2026-08-26 com hoje={HOJE} (6 dias): INCONCLUSIVO serie parada, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": {"requests_total": "400", "requests_404": 0}}))
passo(rc == 1 and "ausente ou nao numerico" in saida,
      f"requests_total como string (\"400\") NAO vira zero nem aprovacao: INCONCLUSIVO, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": {"requests_total": 400, "requests_404": None}}))
passo(rc == 1 and "ausente ou nao numerico" in saida,
      f"requests_404 ausente NAO e zero: INCONCLUSIVO, exit {rc}")

rc, saida = roda_gate(serie({"googlebot": [(400, 0)] * 6 + [(100, 10)]})
                      + borda("2026-08-31", "googlebot", 100, 0) + "\n")
passo(rc == 0, f"replay da chave (dia, bot): a ULTIMA linha vence (100 de 0 depois de 10 de 100): exit {rc}")

rc, saida = roda_gate(serie({"googlebot": [(400, 0)] * 6 + [(100, 10)]}), "--teto-fracao", "0.5")
passo(rc == 0, f"o teto e parametrizavel para o TESTE (0.5 aprova 10%) — e o default fica em 5%: exit {rc}")

# ---------------------------------------------------------------------------
# O GERADOR, sobre fonte de borda e ledger de origem sinteticos
# ---------------------------------------------------------------------------

def combo(data, agente, status, pedidos, cache="hit", colo="GRU", funcao="search", verificado=True):
    registro = {"agent_key": agente, "cache_status": cache, "colo_code": colo, "date": data,
                "edge_response_status": status, "function": funcao, "query_truncated": False,
                "record_type": "combination", "requests_estimated": pedidos,
                "requests_sampled": pedidos, "sampled_dataset": True,
                "schema_version": "edge_bot_status_daily_v1",
                "window_complete": True, "window_start": data + "T00:00:00Z",
                "window_end": data + "T23:59:59Z"}
    if verificado:
        registro["verified_bot_categories"] = {"Search Engine Crawler": pedidos}
    return json.dumps(registro)


def vazio(data):
    return json.dumps({"date": data, "record_type": "empty_window",
                       "schema_version": "edge_bot_status_daily_v1", "window_complete": True})


def acesso(ts, path, status, ua, warming=False, sim=False):
    return json.dumps({"ts": ts, "method": "GET", "path": path, "status": status, "bytes": 1,
                       "duration_ms": 0, "route_class": "not_found" if status == 404 else "page",
                       "bot_class": "valuable_search_or_user_bot", "bot_rule": "x",
                       "user_agent": ua, "warming": warming, "bot_simulation": sim})


UA_GOOGLE = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
UA_SCANNER = "python-requests/2.31"


def roda_gerador(pasta, fonte, ledger_por_dia, *args):
    pasta = pathlib.Path(pasta)
    fonte_path = pasta / "edge.jsonl"
    if fonte is not None:
        fonte_path.write_text(fonte, encoding="utf-8")
    raiz = pasta / "raiz"
    if ledger_por_dia is not None:
        acessos = raiz / "data" / "ops" / "access"
        acessos.mkdir(parents=True, exist_ok=True)
        for data, linhas in ledger_por_dia.items():
            (acessos / f"access-{data}.jsonl").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    else:
        raiz.mkdir(parents=True, exist_ok=True)
    saida = pasta / "serie.jsonl"
    r = subprocess.run([sys.executable, str(GERADOR), "--fonte-borda", str(fonte_path),
                        "--raiz-origem", str(raiz), "--saida", str(saida), "--hoje", HOJE, *args],
                       capture_output=True, text=True)
    linhas = []
    if saida.exists():
        linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines() if l.strip()]
    return r.returncode, r.stdout + r.stderr, linhas, saida


print("gerador — agregacao da borda:")
fonte = "\n".join([
    combo("2026-08-30", "googlebot", 200, 40, cache="hit"),
    combo("2026-08-30", "googlebot", 200, 20, cache="miss"),
    combo("2026-08-30", "googlebot", 404, 5),
    combo("2026-08-30", "googlebot", 301, 3),
    combo("2026-08-30", "googlebot", 404, 5),          # combinacao REPETIDA: a ultima vence, nao soma
    combo("2026-08-30", "bingbot", 200, 100, verificado=False),  # sem verified_bot_categories: fora
    combo("2026-08-31", "bingbot", 200, 10),
    combo("2026-09-01", "bingbot", 404, 999),          # dia corrente: nunca entra
    vazio("2026-08-29"),
]) + "\n"
ledger = {
    "2026-08-30": [
        acesso("2026-08-30T10:00:00Z", "/a/", 200, UA_GOOGLE),
        acesso("2026-08-30T10:00:01Z", "/nao-existe/", 404, UA_GOOGLE),
        acesso("2026-08-30T10:00:02Z", "/nao-existe/", 404, UA_GOOGLE),
        acesso("2026-08-30T10:00:03Z", "/outra/", 404, UA_GOOGLE),
        acesso("2026-08-30T10:00:04Z", "/x/index.html.br", 404, UA_GOOGLE),
        acesso("2026-08-30T10:00:05Z", "/warm/", 404, UA_GOOGLE, warming=True),      # fora
        acesso("2026-08-30T10:00:06Z", "/sim/", 404, UA_GOOGLE, sim=True),           # fora
        acesso("2026-08-30T10:00:07Z", "/wp-json/wp/v2/posts/", 404, UA_SCANNER),
    ],
    "2026-09-01": [acesso("2026-09-01T00:00:01Z", "/hoje/", 404, UA_GOOGLE)],      # dia corrente
}
with tempfile.TemporaryDirectory() as d:
    rc, texto, linhas, caminho = roda_gerador(d, fonte, ledger, "--dias-origem", "3")
    passo(rc == 0, f"gerador com as duas fontes: exit {rc}")
    por = {(l["record_type"], l["date"], l.get("agent_key")): l for l in linhas}
    g = por.get(("borda", "2026-08-30", "googlebot"))
    passo(g is not None and g["requests_total"] == 68 and g["requests_200"] == 60
          and g["requests_404"] == 5 and g["requests_other"] == 3 and g["share_404"] == round(5 / 68, 4),
          "googlebot 2026-08-30: 60 de 200 (hit+miss somados), 5 de 404 (duplicata NAO somada), 3 outros = 68")
    passo(g is not None and g["br_excluded"] is False and g["path_in_source"] is False,
          "linha borda declara br_excluded=false e path_in_source=false")
    passo("duplicadas=1" in texto and "nao_verificadas=1" in texto,
          "relato conta duplicadas=1 e nao_verificadas=1 em vez de somar em silencio")
    passo(("borda", "2026-08-30", "bingbot") not in por, "bingbot sem verified_bot_categories fica fora da borda")
    passo(("borda", "2026-09-01", "bingbot") not in por and ("dia", "2026-09-01", None) not in por,
          "dia corrente (2026-09-01) nao entra em linha nenhuma")
    d29 = por.get(("dia", "2026-08-29", None))
    passo(d29 is not None and d29["empty_window"] is True and d29["agents_verified"] == 0,
          "empty_window vira linha dia com empty_window=true (dia medido, nao dia ausente)")
    d30 = por.get(("dia", "2026-08-30", None))
    passo(d30 is not None and d30["requests_total"] == 68 and d30["requests_404"] == 5 and d30["agents_verified"] == 1,
          "linha dia 2026-08-30 soma os agentes verificados: 68 total, 5 de 404")

    print("gerador — origem pelo accessledger:")
    o = por.get(("origem_go", "2026-08-30", "googlebot"))
    passo(o is not None and o["requests_total"] == 5 and o["requests_404"] == 4 and o["requests_200"] == 1,
          "googlebot na origem: 5 linhas (warming e simulacao EXCLUIDOS pelo accessledger), 4 de 404")
    passo(o is not None and o["verified"] is False and o["coverage"] == "rota_dinamica_e_fallback",
          "linha origem_go declara verified=false e o alcance (so rota dinamica e fallback)")
    passo(o is not None and o["top_404_paths"][0] == {"path": "/nao-existe/", "requests": 2}
          and o["distinct_404_paths"] == 3,
          "top_404_paths ordenado por volume: /nao-existe/ x2 primeiro, 3 caminhos distintos")
    passo(o is not None and o["requests_404_br"] == 1, "404 em rota .br e CONTADO (requests_404_br=1), nao suposto")
    s = por.get(("origem_go", "2026-08-30", "outros-user-agents"))
    passo(s is not None and s["requests_404"] == 1 and s["top_404_paths"][0]["path"] == "/wp-json/wp/v2/posts/",
          "UA sem identidade de bot cai em outros-user-agents com o caminho do scanner")
    passo(("origem_go", "2026-09-01", "googlebot") not in por, "origem do dia corrente nao entra")

    print("gerador — idempotencia e fusao:")
    sha1 = hashlib.sha256(caminho.read_bytes()).hexdigest()
    rc2, texto2, _, _ = roda_gerador(d, fonte, None, "--dias-origem", "3")
    sha2 = hashlib.sha256(caminho.read_bytes()).hexdigest()
    passo(rc2 == 0 and sha1 == sha2, f"segunda execucao identica: sha256 {sha1[:12]} == {sha2[:12]}")
    passo("substituida(s)" in texto2 and "0 nova(s)" not in texto2,
          "a segunda execucao SUBSTITUIU as chaves remedidas (nao duplicou linhas)")
    # Encolher a janela da origem PRESERVA a linha antiga fora dela.
    rc3, _, linhas3, _ = roda_gerador(d, fonte, None, "--dias-origem", "1")
    por3 = {(l["record_type"], l["date"], l.get("agent_key")) for l in linhas3}
    passo(rc3 == 0 and ("origem_go", "2026-08-30", "googlebot") in por3,
          "--dias-origem 1 (so 2026-08-31) preserva a linha origem_go de 2026-08-30 medida antes")

print("gerador — fonte ausente nunca e serie:")
with tempfile.TemporaryDirectory() as d:
    rc, texto, linhas, caminho = roda_gerador(d, None, ledger)
    passo(rc == 2 and "NAO RODOU" in texto and not os.path.exists(caminho),
          f"fonte de borda ausente: NAO RODOU, exit {rc}, nada gravado")
with tempfile.TemporaryDirectory() as d:
    rc, texto, linhas, caminho = roda_gerador(d, "", ledger)
    passo(rc == 2 and "NAO RODOU" in texto, f"fonte de borda vazia: NAO RODOU, exit {rc}")
with tempfile.TemporaryDirectory() as d:
    rc, texto, linhas, caminho = roda_gerador(d, fonte, None)
    tipos = {l["record_type"] for l in linhas}
    passo(rc == 2 and "origem NAO medida" in texto and "borda" in tipos and "origem_go" not in tipos,
          f"ledger de origem ausente: borda gravada, origem nao, exit {rc}")

print("gate sobre a serie do gerador sintetico (ponta a ponta):")
with tempfile.TemporaryDirectory() as d:
    fonte_ruim = "\n".join(
        [combo(f"2026-08-{dd}", bot, 200, 400) for dd in range(25, 32) for bot in VALIOSOS]
        + [combo("2026-08-31", "googlebot", 404, 60)]) + "\n"
    rc, texto, linhas, caminho = roda_gerador(d, fonte_ruim, {}, "--dias-origem", "1")
    r = subprocess.run([sys.executable, str(GATE), "--serie", str(caminho), "--hoje", HOJE],
                       capture_output=True, text=True)
    passo(r.returncode == 1 and "googlebot_404_acima_do_teto@2026-08-31:60 de 460" in r.stdout + r.stderr,
          f"gerador -> gate: googlebot 60 de 460 = 13% REPROVA, exit {r.returncode}")

print("gerador -> gate: dia cortado pela API nao e somado como completo em silencio:")
with tempfile.TemporaryDirectory() as d:
    linhas_fonte = [combo(f"2026-08-{dd}", bot, 200, 400) for dd in range(25, 32) for bot in VALIOSOS]
    cortada = json.loads(linhas_fonte[-1]); cortada["query_truncated"] = True
    linhas_fonte[-1] = json.dumps(cortada)
    rc, texto, linhas, caminho = roda_gerador(d, "\n".join(linhas_fonte) + "\n", {}, "--dias-origem", "1")
    truncados = sorted({l["date"] for l in linhas if l.get("query_truncated") is True})
    nao_truncados = sorted({l["date"] for l in linhas if l.get("query_truncated") is False})
    r = subprocess.run([sys.executable, str(GATE), "--serie", str(caminho), "--hoje", HOJE],
                       capture_output=True, text=True)
    passo(truncados == ["2026-08-31"] and "2026-08-30" in nao_truncados
          and "ATENCAO: a API cortou a consulta em 2026-08-31" in r.stdout + r.stderr,
          f"query_truncated de 2026-08-31 chega a borda/dia e o gate o nomeia: exit {r.returncode}")

if falhou:
    print("test_serie_404_bots: FALHOU")
    sys.exit(1)
print("test_serie_404_bots: OK")
