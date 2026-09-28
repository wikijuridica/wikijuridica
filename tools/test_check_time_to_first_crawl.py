#!/usr/bin/env python3
"""Guardas do check-time-to-first-crawl (BUG-076: a serie que reage em dias
nao tinha leitor).

Cada caso aqui e uma forma de o gate ficar verde sem ter medido nada — a
doenca dos vigias que passaram verdes com o Googlebot a 13,9 paginas/dia e
3.057 paginas nunca pedidas. O gate nasce provando que REPROVA no caso ruim,
que PASSA no caso bom, e que dado ausente nunca vira aprovacao.
"""
import datetime, json, pathlib, subprocess, sys, tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-time-to-first-crawl"
HOJE = "2026-09-01"

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


def linha(data, bot, mediana, nunca, publicadas=10107, **extra):
    registro = {
        "schema_version": "time_to_first_crawl_daily_v1", "date": data, "bot": bot,
        "rotas_publicadas": publicadas, "com_primeira_visita": publicadas - nunca,
        "nunca_pedidas": nunca, "mediana_dias": mediana, "p90_dias": mediana,
        "maximo_dias": 26, "anterior_ao_registro": 0,
    }
    registro.update(extra)
    return json.dumps(registro)


def serie(nuncas, mediana=4, bots=("googlebot", "bingbot"), inicio="2026-08-28",
          publicadas=None, replicar=1):
    """Ledger sintetico: uma linha por (data, bot). `nuncas[i]` e o
    nunca_pedidas do dia i; `publicadas[i]`, quando dado, o acervo do dia i.
    `replicar` repete cada data N vezes, como o ledger de cobertura fazia."""
    base = datetime.date.fromisoformat(inicio)
    linhas = []
    for _ in range(replicar):
        for i, nunca in enumerate(nuncas):
            data = (base + datetime.timedelta(days=i)).isoformat()
            pub = publicadas[i] if publicadas else 10107
            for bot in bots:
                linhas.append(linha(data, bot, mediana, nunca, pub))
    return "\n".join(linhas) + "\n"


def roda(conteudo, *args):
    with tempfile.TemporaryDirectory() as d:
        ledger = pathlib.Path(d) / "time_to_first_crawl_daily.jsonl"
        ledger.write_text(conteudo, encoding="utf-8")
        r = subprocess.run([sys.executable, str(GATE), "--serie", str(ledger),
                            "--hoje", HOJE, *args], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


# ---------- 1. CASO BOM: mediana 4 (a medida) e nunca_pedidas caindo, como a serie real
rc, saida = roda(serie([2955, 2945, 2943, 2939, 2937]))
passo(rc == 0 and "check-time-to-first-crawl: pass" in saida,
      f"mediana 4 com nunca_pedidas caindo passa (exit {rc})")

# ---------- 2. CASO RUIM: mediana 12 e nunca_pedidas CRESCENDO — os dois criterios nomeados
rc, saida = roda(serie([2900, 2930, 2960, 2990, 3020], mediana=12))
passo(rc == 1 and "googlebot_mediana_acima_do_teto" in saida
      and "googlebot_nunca_pedidas_nao_caiu" in saida
      and "bingbot_mediana_acima_do_teto" in saida
      and "bingbot_nunca_pedidas_nao_caiu" in saida,
      f"mediana 12 e nunca_pedidas crescendo reprova pelos dois criterios (exit {rc})")

# ---------- 3. Cada criterio sozinho reprova
rc, saida = roda(serie([2937, 2937, 2937, 2937, 2937], mediana=4))
passo(rc == 1 and "nunca_pedidas_nao_caiu" in saida and "mediana_acima_do_teto" not in saida,
      f"nunca_pedidas parado reprova mesmo com mediana 4 (exit {rc})")
rc, saida = roda(serie([2955, 2945, 2943, 2939, 2937], mediana=8))
passo(rc == 1 and "mediana_acima_do_teto" in saida and "nunca_pedidas_nao_caiu" not in saida,
      f"mediana 8 reprova mesmo com nunca_pedidas caindo (exit {rc})")

# ---------- 4. FRONTEIRA do teto: "passar de 7" e ESTRITO — 7 passa, 7,5 reprova
rc7, _ = roda(serie([2955, 2945, 2943, 2939, 2937], mediana=7))
rc75, _ = roda(serie([2955, 2945, 2943, 2939, 2937], mediana=7.5))
passo(rc7 == 0 and rc75 == 1, f"teto 7: mediana 7 passa ({rc7}), 7,5 reprova ({rc75})")

# ---------- 5. A JANELA E TETO: queda de 10 dias atras nao esconde estagnacao de 7 dias
#    15 datas: cai nos 5 primeiros dias, fica parada nos 10 ultimos. Com janela
#    7 a comparacao so alcanca o trecho parado -> reprova. So alargando a janela
#    para 15 (parametro DECLARADO, nao dado a mais) e que a queda antiga entra.
antiga = serie([3000, 2990, 2980, 2970, 2960] + [2960] * 10, inicio="2026-08-18")
rc7, saida7 = roda(antiga, "--janela-dias", "7")
rc15, _ = roda(antiga, "--janela-dias", "15")
passo(rc7 == 1 and "nunca_pedidas_nao_caiu" in saida7 and rc15 == 0,
      f"queda fora da janela nao aprova (janela 7: {rc7}; janela 15: {rc15})")

# ---------- 6. Linha repetida pelo produtor nao muda o veredito
rc_uma, _ = roda(serie([2937, 2937, 2937, 2937, 2937], replicar=1))
rc_oito, _ = roda(serie([2937, 2937, 2937, 2937, 2937], replicar=8))
passo(rc_uma == 1 and rc_oito == 1,
      f"replay do produtor nao muda o veredito ({rc_uma} x {rc_oito})")

# ---------- 7. Crawler principal AUSENTE da serie = INCONCLUSIVO, nunca pass
rc, saida = roda(serie([2955, 2945, 2943, 2939, 2937], bots=("bingbot",)))
passo(rc == 1 and "INCONCLUSIVO" in saida and "googlebot" in saida
      and "ausente da serie" in saida and ": pass" not in saida,
      f"googlebot ausente da serie e INCONCLUSIVO e nao passa (exit {rc})")

# ---------- 8. Coorte abaixo do minimo = INCONCLUSIVO, nunca pass
#    40 rotas com primeira visita (10107 - 10067): a mediana de 40 rotas e sorteio.
rc, saida = roda(serie([10070, 10069, 10068, 10068, 10067]))
passo(rc == 1 and "coorte de 40 rota(s)" in saida and ": pass" not in saida,
      f"coorte de 40 rotas e INCONCLUSIVO e nao passa (exit {rc})")

# ---------- 9. Campo ausente = INCONCLUSIVO, nunca pass (mediana_dias sumiu da ultima linha)
boa = serie([2955, 2945, 2943, 2939, 2937]).splitlines()
sem_mediana = []
for l in boa:
    r = json.loads(l)
    if r["date"] == "2026-09-01":
        del r["mediana_dias"]
    sem_mediana.append(json.dumps(r))
rc, saida = roda("\n".join(sem_mediana) + "\n")
passo(rc == 1 and "INCONCLUSIVO" in saida and ": pass" not in saida,
      f"mediana_dias ausente e INCONCLUSIVO e nao passa (exit {rc})")

# ---------- 10. Serie PARADA (ultima linha de 5 dias atras) = INCONCLUSIVO, nunca pass
rc, saida = roda(serie([2955, 2945, 2943, 2939, 2937], inicio="2026-08-23"))
passo(rc == 1 and "serie parada" in saida and ": pass" not in saida,
      f"serie parada ha 5 dias e INCONCLUSIVO e nao passa (exit {rc})")

# ---------- 11. ONDA DIARIA: acervo +100 faz nunca_pedidas SUBIR embora o crawler avance
#    Bruto: 2937 -> 3032 (+95). Liquido: o crawler pediu 5 do backlog. Passa, e a
#    tabela mostra os dois numeros. O inverso — acervo -50 com nenhuma visita nova —
#    faz o bruto CAIR sem o crawler mexer um dedo, e reprova.
rc, saida = roda(serie([2937, 2960, 2984, 3008, 3032],
                       publicadas=[10107, 10132, 10157, 10182, 10207]))
passo(rc == 0 and "acervo +100" in saida and "liquido -5" in saida,
      f"acervo +100 com 5 rotas a mais pedidas passa e mostra bruto e liquido (exit {rc})")
rc, saida = roda(serie([2937, 2937, 2937, 2887, 2887],
                       publicadas=[10107, 10107, 10107, 10057, 10057]))
passo(rc == 1 and "nunca_pedidas_nao_caiu" in saida,
      f"acervo -50 sem visita nova nao conta como queda (exit {rc})")

# ---------- 12. Serie ausente reprova
r = subprocess.run([sys.executable, str(GATE), "--serie", "/nonexistent/ttfc.jsonl"],
                   capture_output=True, text=True)
passo(r.returncode == 1 and "serie ausente" in r.stderr, f"serie ausente reprova (exit {r.returncode})")

print()
print("guardas do time-to-first-crawl: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
