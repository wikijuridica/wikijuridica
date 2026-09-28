#!/usr/bin/env python3
"""Guardas do check-crawl-coverage-stall.

DOIS DEFEITOS MEDIDOS EM 2026-08-28, ambos no mesmo ponto:

1. Fatiava as ultimas N LINHAS, nao N DATAS. O produtor reprocessa a janela de
   8 dias a cada execucao, entao a "janela de 7 dias" era o replay de um run --
   e ALARGAR a janela AFROUXAVA o gate: `--dias 2` reprovava, `--dias 10`
   passava. Gate que fica mais verde quanto mais dado recebe nao e gate.
2. Incluia o dia CORRENTE, que e uma janela de ~4h10 (o timer roda 04:10 UTC e
   o produtor grampeia `fim=agora`), fazendo a serie parecer estagnada num dia
   em que ela ainda nao foi medida ate o fim.

Estes testes provam que o gate DETECTA estagnacao de verdade e que NAO afrouxa.
"""
import datetime, importlib.util, json, pathlib, subprocess, sys, tempfile
RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-crawl-coverage-stall"

falhou = 0
def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok: falhou = 1

def serie(dias_cobertura, crawler="googlebot", replicar=1):
    """Monta um ledger sintetico. `replicar` simula o produtor reprocessando
    a janela: a MESMA data aparece N vezes, que era o que quebrava o fatiamento."""
    linhas = []
    base = datetime.date(2026, 8, 1)
    for _ in range(replicar):
        for i, cob in enumerate(dias_cobertura):
            linhas.append(json.dumps({
                "date": (base + datetime.timedelta(days=i)).isoformat(),
                "crawler": crawler,
                "schema_version": "crawl_coverage_daily_v2",
                "cumulative_sitemap_coverage": cob,
                "sitemap_total": 10000,
                # A cobertura da fixture decide: dia que nao avanca tem 0 URL
                # nova. Antes o primeiro dia sempre saia com 5, e com isso uma
                # janela que o incluisse deixava de ser "todos_zero" -- a fixture
                # e que era inconsistente, nao o gate.
                "paths_requested_that_day": 0 if (i == 0 or cob == dias_cobertura[i-1]) else 5,
                "new_sitemap_urls_that_day": 0 if (i == 0 or cob == dias_cobertura[i-1]) else 5,
                "requests_verified": 10,
            }))
    return "\n".join(linhas) + "\n"

def roda(conteudo, *args):
    with tempfile.TemporaryDirectory() as d:
        ledger = pathlib.Path(d) / "crawl_coverage_daily.jsonl"
        ledger.write_text(conteudo, encoding="utf-8")
        r = subprocess.run([sys.executable, str(GATE), "--serie", str(ledger), *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

# ---------- 1. DETECTA estagnacao real (a razao de o gate existir)
rc, saida = roda(serie([100, 100, 100, 100, 100]), "--dias", "4")
passo(rc != 0, f"detecta cobertura congelada (exit {rc})")

# ---------- 2. NAO acusa serie que avanca
#    O gate ganhou em 2026-09-01 um segundo criterio, independente de
#    estagnacao: "lento" (ritmo medido < ritmo exigido para fechar o total no
#    horizonte declarado, --horizonte-dias, default 90). Esta serie sintetica
#    avanca 20 paginas/dia sobre um sitemap_total de 10000 -- rapida o
#    suficiente para nunca ser ESTAGNADA, mas lenta demais para fechar 9820
#    URLs em 90 dias (exigiria 109/dia), entao o horizonte default reprova por
#    um motivo que este subteste nao existe para cobrir -- o criterio de ritmo
#    tem cobertura PROPRIA no caso 6, mais abaixo, com a MESMA serie sob
#    horizonte default. --horizonte-dias bem folgado isola o que ESTE
#    subteste prova: uma serie que avanca nao pode ser confundida com uma
#    serie congelada.
rc, _ = roda(serie([100, 120, 140, 160, 180]), "--dias", "4", "--horizonte-dias", "10000000")
passo(rc == 0, f"serie que avanca passa (exit {rc})")

# ---------- 3. O DEFEITO: alargar a janela nao pode AFROUXAR.
#    Comparamos so janelas que CABEM na serie (5 datas). Janela maior que a
#    serie e outra coisa -- ver caso 3b.
rcs = {d: roda(serie([100, 100, 100, 100, 100]), "--dias", str(d))[0] for d in (2, 3, 4, 5)}
passo(all(v != 0 for v in rcs.values()),
      f"reprova em toda janela que cabe na serie: {rcs}")

# ---------- 3b. Janela MAIOR que a serie: nao julga, e isso e honesto --
#    mas nao pode ser silencioso. O relatorio tem de dizer serie_curta.
rc, saida = roda(serie([100, 100, 100]), "--dias", "10", "--json")
passo("serie_curta" in saida,
      "janela maior que a serie e reportada como curta, nao como aprovada")

# ---------- 4. O DEFEITO: linha repetida pelo reprocessamento nao muda o veredito
rc_uma, _ = roda(serie([100, 100, 100, 100, 100], replicar=1), "--dias", "4")
rc_oito, _ = roda(serie([100, 100, 100, 100, 100], replicar=8), "--dias", "4")
passo((rc_uma != 0) == (rc_oito != 0),
      f"reprocessamento do produtor nao muda o veredito ({rc_uma} x {rc_oito})")

# ---------- 5. FALSO POSITIVO: o dia corrente (parcial) nao pode condenar
hoje = datetime.date.today().isoformat()
parcial = serie([100, 120, 140]) + json.dumps({
    "date": hoje, "crawler": "googlebot", "schema_version": "crawl_coverage_daily_v2",
    "cumulative_sitemap_coverage": 140, "sitemap_total": 10000,
    "paths_requested_that_day": 0, "new_sitemap_urls_that_day": 0,
    "requests_verified": 0, "no_groups_returned": True}) + "\n"
# Mesmo isolamento do caso 2: esta serie tambem avanca devagar demais para o
# horizonte default (90 dias) sem ser ESTAGNADA -- e o que este subteste prova
# e so a exclusao do dia corrente parcial, nao o criterio de ritmo.
rc, _ = roda(parcial, "--dias", "3", "--horizonte-dias", "10000000")
passo(rc == 0, f"dia corrente parcial nao condena serie que avancava (exit {rc})")

# ---------- 6. O criterio "lento" (ritmo) tem cobertura PROPRIA -- sem isto,
#    o isolamento dos casos 2 e 5 (--horizonte-dias folgado) apagaria da suite
#    o unico criterio que faz o gate ficar vermelho hoje em producao (medido
#    2026-09-01: Googlebot a 13,9 paginas/dia contra 34 exigidas). MESMA serie
#    do caso 2, agora sob o horizonte DEFAULT (sem folga): tem de reprovar
#    como "lento", nunca como "estagnado" (a serie avanca de verdade).
rc, saida = roda(serie([100, 120, 140, 160, 180]), "--dias", "4", "--json")
passo(
    rc != 0 and '"status": "lento"' in saida and "ritmo_insuficiente" in saida
    and '"status": "estagnado"' not in saida,
    f"serie que avanca devagar demais reprova por RITMO sob horizonte default (exit {rc})",
)

print()
print("guardas do stall: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
