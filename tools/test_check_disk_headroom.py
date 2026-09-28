#!/usr/bin/env python3
"""Guardas do check-disk-headroom (item B8, 2026-09-01).

O DEFEITO MEDIDO: o piso exigido oscilava com a HORA, nao com o disco. Entre
2026-08-31T21:09Z e 2026-09-01T19:08Z, com `/` sempre entre 77 e 87 GiB livres,
o piso foi 137,32 -> 103,49 -> 73,21 -> 57,60 GiB. A tendencia era uma reta de
minimos quadrados ancorada no nascimento da serie, que coincidiu com um surto de
51,5 GiB em 29 h; cada amostra nova com o disco parado diluia o degrau. O gate
reprovou 41 vezes em 3 dias e estava verde as 12:09. Gate que aprova conforme a
hora nao e gate.

O que estes testes provam:

  1. DETERMINISMO: amostras identicas acrescentadas no mesmo dia (disco parado)
     deixam o piso BYTE-IDENTICO — e a reta antiga, recalculada aqui, muda.
  2. NAO AFROUXOU: tendencia real dentro da janela de reacao reprova (exit 1);
     e um surto de 24 h que a mediana sozinha esqueceria continua cobrado.
  3. AUSENCIA NAO E APROVACAO: serie vazia = NAO RODOU (exit 2); menos de dois
     dias completos = INCONCLUSIVO impresso, nunca "ok"; backup desconhecido =
     INCONCLUSIVO, e a checagem de tendencia/surto do HDD nao e pulada.
  4. FRESTA NA VIRADA: maquina desligada na meia-noite (> 3 h sem amostra)
     invalida a fronteira, e os dois dias vizinhos deixam de contar.

Rodar:
    python3 tools/test_check_disk_headroom.py
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
# WIKI_DISK_HEADROOM_GATE existe para provar que o teste REPROVA a versao
# anterior (`git show HEAD~1:tools/check-disk-headroom > /tmp/x; WIKI_DISK_HEADROOM_GATE=/tmp/x
# python3 tools/test_check_disk_headroom.py` deve sair 1). Producao nao a define.
GATE = pathlib.Path(os.environ.get("WIKI_DISK_HEADROOM_GATE", str(RAIZ / "tools" / "check-disk-headroom")))
GIB = 1073741824
UTC = datetime.timezone.utc
# O timer real dispara em *:07. A serie nasce as 00:07 de 08/01, entao a
# meia-noite de 08/01 NAO tem amostra anterior e nao e fronteira: a primeira
# fronteira valida e 08/02, e serie de N horas tem floor(N/24) - 1 dias completos.
INICIO = datetime.datetime(2026, 8, 1, 0, 7, tzinfo=UTC)

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


def linha(t, livre_gib, hdd_livre_gib=500.0):
    total = 700 * GIB
    alvos = []
    for ponto_, livre in (("/", livre_gib), ("/mnt/hdd", hdd_livre_gib)):
        livre_b = int(livre * GIB)
        usado = total - livre_b
        alvos.append({
            "ponto": ponto_, "montado": True, "fonte": "/dev/x", "fstype": "ext4",
            "total_b": total, "usado_b": usado, "livre_b": livre_b,
            "pct_usado": round(100.0 * usado / (usado + livre_b), 4), "reservado_b": 0,
        })
    return json.dumps({
        "schema_version": "disk_headroom_v1",
        "checked_at": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "alvos": alvos,
    })


def serie(perfil, horas, pular=(), hdd=None):
    """`perfil(h)` devolve o livre de `/` em GiB na hora h (0 = primeira
    amostra); uma amostra por hora, como o timer. `pular` remove horas
    (simula a maquina desligada). `hdd(h)` idem para /mnt/hdd."""
    return "\n".join(
        linha(INICIO + datetime.timedelta(hours=h), perfil(h),
              hdd_livre_gib=hdd(h) if hdd else 500.0)
        for h in range(horas + 1) if h not in pular
    ) + "\n"


def roda(conteudo, *args, ledger_backup=None, texto=False):
    """Roda o gate contra uma serie sintetica. Devolve (exit, relatorio, saida);
    `relatorio` e o JSON (None em modo texto)."""
    with tempfile.TemporaryDirectory() as d:
        caminho = pathlib.Path(d) / "disk_headroom.jsonl"
        caminho.write_text(conteudo, encoding="utf-8")
        cmd = [str(GATE), "--sem-alerta", "--serie", str(caminho)]
        if not texto:
            cmd.append("--json")
        if ledger_backup is not None:
            lb = pathlib.Path(d) / "backup_wiki.jsonl"
            lb.write_text(ledger_backup, encoding="utf-8")
            cmd += ["--ledger-backup", str(lb)]
        cmd += list(args)
        r = subprocess.run(cmd, capture_output=True, text=True)
        rel = None
        if not texto:
            try:
                rel = json.loads(r.stdout)
            except ValueError:
                rel = None
        return r.returncode, rel, r.stdout + r.stderr


def ponto(rel, nome="/"):
    return next(e for e in rel["pontos"] if e["ponto"] == nome)


def reta_antiga(conteudo):
    """A tendencia da versao anterior: 8 dias x minimos quadrados sobre livre_b
    de TODAS as amostras. Reproduzida aqui so para provar que ELA muda com
    amostra identica — e o piso novo, nao."""
    pts = []
    for ln in conteudo.splitlines():
        d = json.loads(ln)
        t = datetime.datetime.fromisoformat(d["checked_at"].replace("Z", "+00:00"))
        pts.append((t, [a for a in d["alvos"] if a["ponto"] == "/"][0]["livre_b"]))
    t0 = pts[0][0]
    xs = [(t - t0).total_seconds() / 86400 for t, _ in pts]
    ys = [float(y) for _, y in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return -(num / den) * 8 / GIB


print("1. determinismo: disco parado => piso identico")


def perfil_surto_depois_plano(h):
    # Parecido com o real: surto de 40 GiB nas primeiras 24 h, depois plano.
    return 100.0 - 40.0 * min(h, 24) / 24.0


pisos, retas = [], []
for extra in (0, 5, 10, 20):
    # h=72 e 08/04 00:07; h=73..92 sao 08/04 01:07..20:07 — mesmo dia UTC, disco parado
    conteudo = serie(perfil_surto_depois_plano, 72 + extra)
    rc, rel, _ = roda(conteudo)
    pisos.append(ponto(rel)["piso_livre_b"])
    retas.append(reta_antiga(conteudo))
passo(len(set(pisos)) == 1,
      f"piso byte-identico com +0/+5/+10/+20 amostras identicas: {sorted(set(round(p / GIB, 4) for p in pisos))} GiB")
passo(max(retas) - min(retas) > 1.0,
      f"a reta antiga, no mesmo cenario, teria movido a tendencia em {max(retas) - min(retas):.2f} GiB (de {retas[0]:.2f} a {retas[-1]:.2f})")
rc, rel, _ = roda(serie(perfil_surto_depois_plano, 72))
p = ponto(rel)
passo(p["dias_completos"] == 2, f"fronteiras 08/02, 08/03, 08/04 => 2 dias completos: {p['dias_completos']}")
passo(p["piso_congelado_ate"] == "2026-08-05T00:00Z", f"informa ate quando o piso esta fixo: {p['piso_congelado_ate']}")
passo(abs(p["surto_24h_gib"] - 40.0) < 0.5, f"surto de 24 h medido = {p['surto_24h_gib']} GiB (esperado ~40)")

print("2a. caso ruim: tendencia dentro da janela de reacao")


def perfil_goteira(h):
    return 20.0 + 3.0 * (96 - h) / 24.0  # 3 GiB/dia constantes, termina com 20 GiB livres


rc, rel, _ = roda(serie(perfil_goteira, 96))
p = ponto(rel)
passo(rc == 1 and rel["veredito"] == "reprova",
      f"3 GiB/dia com 20 GiB livres => REPROVA (exit {rc}, veredito {rel['veredito']}, piso {p['piso_livre_gib']} GiB)")
passo(abs(p["consumo_gib_dia"] - 3.0) < 0.05, f"tendencia medida = {p['consumo_gib_dia']} GiB/dia (esperado 3,0)")
passo(p["dias_para_encher"] is not None and p["dias_para_encher"] <= 8,
      f"enche em {p['dias_para_encher']} dias, dentro da janela de 8")
passo(any("dentro da janela de reacao" in x for x in rel["problemas"]), "mensagem diz que enche dentro da janela de reacao")

print("2b. caso bom: disco plano e folgado")
rc, rel, _ = roda(serie(lambda h: 500.0, 96))
passo(rc == 0 and rel["veredito"] == "ok", f"500 GiB planos => ok (exit {rc}, veredito {rel['veredito']})")
rc, _, saida = roda(serie(lambda h: 500.0, 96), texto=True)
passo(rc == 0 and "check-disk-headroom: ok" in saida, "saida em texto termina com 'check-disk-headroom: ok'")

print("2c. surto nao e esquecido pela mediana")


def perfil_surto_semanal(h):
    # 6 dias planos a 100 GiB, queda de 60 GiB em 24 h, depois plano a 40 GiB.
    if h <= 144:
        return 100.0
    if h <= 168:
        return 100.0 - 60.0 * (h - 144) / 24.0
    return 40.0


rc, rel, _ = roda(serie(perfil_surto_semanal, 216))
p = ponto(rel)
passo(p["consumo_gib_dia"] is not None and p["consumo_gib_dia"] <= 0.01,
      f"mediana dos {p['dias_completos']} dias completos = {p['consumo_gib_dia']} GiB/dia (o surto e outlier)")
passo(abs(p["surto_24h_gib"] - 60.0) < 0.5, f"surto de 24 h = {p['surto_24h_gib']} GiB")
passo(rc == 1 and rel["veredito"] == "reprova",
      f"40 GiB livres com surto de 60 na janela => REPROVA (exit {rc}, piso {p['piso_livre_gib']} GiB); a mediana sozinha passaria")
rc2, rel2, _ = roda(serie(perfil_surto_semanal, 216 + 24 * 6))
passo(rc2 == 0 and ponto(rel2)["surto_24h_gib"] < 0.5,
      f"6 viradas depois o surto saiu da janela de 7 dias: surto={ponto(rel2)['surto_24h_gib']} GiB, exit {rc2}")

print("3a. NAO RODOU: serie vazia")
rc, rel, _ = roda("")
passo(rc == 2 and rel is not None and rel["veredito"] == "nao_rodou", f"serie vazia => exit {rc}, veredito {rel and rel['veredito']}")
rc, _, saida = roda("", texto=True)
passo(rc == 2 and "NAO RODOU" in saida, f"em texto imprime NAO RODOU (exit {rc})")

print("3b. INCONCLUSIVO: um dia completo so")
rc, rel, _ = roda(serie(lambda h: 500.0, 54))  # 08/01 00:07 -> 08/03 06:07: fronteiras 08/02 e 08/03
p = ponto(rel)
passo(rc == 0 and rel["veredito"] == "inconclusivo", f"1 dia completo => INCONCLUSIVO (exit {rc}, veredito {rel['veredito']})")
passo(p["dias_completos"] == 1 and p["consumo_gib_dia"] is None, f"dias_completos={p['dias_completos']}, tendencia={p['consumo_gib_dia']}")
rc, _, saida = roda(serie(lambda h: 500.0, 54), texto=True)
passo("INCONCLUSIVO" in saida and "check-disk-headroom: ok" not in saida, "texto imprime INCONCLUSIVO e nao imprime 'ok'")

print("3c. INCONCLUSIVO nao e aprovacao: surto em curso reprova antes da mediana existir")
rc, rel, _ = roda(serie(lambda h: 100.0 - 70.0 * min(h, 20) / 20.0, 54))  # 100 -> 30 GiB em 20 h
p = ponto(rel)
passo(rc == 1 and rel["veredito"] == "reprova",
      f"queda de 70 GiB em 20 h com 30 livres e 1 dia completo => REPROVA (exit {rc}, piso {p['piso_livre_gib']} GiB)")
passo(any("pior 24 h ja medida" in x for x in rel["inconclusivos"]), "o INCONCLUSIVO da tendencia diz que o surto ja esta sendo cobrado")

print("3d. backup desconhecido: HDD sai INCONCLUSIVO e nao pula a checagem")
rc, rel, _ = roda(serie(lambda h: 500.0, 96), ledger_backup="")
passo(rel["veredito"] == "inconclusivo" and any(x.startswith("/mnt/hdd: piso estrutural desconhecido") for x in rel["inconclusivos"]),
      f"ledger de backup vazio => INCONCLUSIVO no HDD (veredito {rel['veredito']})")
rc, rel, _ = roda(serie(lambda h: 500.0, 96, hdd=lambda h: 100.0 + 30.0 * (96 - h) / 24.0), ledger_backup="")
passo(rc == 1 and any(x.startswith("/mnt/hdd: livre") for x in rel["problemas"]),
      f"HDD a 30 GiB/dia com 100 livres e backup desconhecido => REPROVA (exit {rc}); antes a checagem era pulada")

print("4. fresta na virada")
plano = lambda h: 500.0  # noqa: E731
# fronteiras 08/02..08/05 = 3 dias; buraco de 6 h em volta da virada de 08/03 (h=48)
rc, rel, _ = roda(serie(plano, 96, pular=set(range(45, 51))))
passo(ponto(rel)["dias_completos"] == 1,
      f"buraco de 6 h na virada de 08/03: dias completos = {ponto(rel)['dias_completos']} (08/02->08/03 e 08/03->08/04 caem; sobra 08/04->08/05)")
rc, rel, _ = roda(serie(plano, 96, pular={48}))
passo(ponto(rel)["dias_completos"] == 3,
      f"um disparo perdido (fresta de 2 h) ainda fecha a fronteira: dias completos = {ponto(rel)['dias_completos']}")

print("\ncheck-disk-headroom:", "FALHA" if falhou else "todos os passos OK")
sys.exit(falhou)
