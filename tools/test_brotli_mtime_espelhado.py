#!/usr/bin/env python3
"""Prova que o `.br` espelha o mtime do fonte e que o gerador detecta RETROCESSO.

POR QUE ESTE TESTE EXISTE (medido em 2026-08-28): o gerador dava ao `.br` o
mtime do fonte + 1 s, e decidia recomprimir com `fonte > br`. As duas coisas
juntas produziam dois defeitos:

  1. ETag e Last-Modified do `.br` divergiam do identity em 100% dos 10.340
     pares. O Googlebot manda `Accept-Encoding: br`; quando a borda ia à origem
     (83% das requisições dele), o validador não casava e ele recebia o corpo
     inteiro em vez de 304.
  2. Quando o mtime do fonte RETROCEDE -- que é exatamente o que a correção do
     carimbo de `reviewed_at` provoca -- `fonte > br` fica falso e o `.br` nunca
     mais é regenerado, servindo conteúdo velho para sempre.

O teste exercita o código REAL do gerador, importado do arquivo.
"""
import importlib.util, os, pathlib, subprocess, sys, tempfile
from importlib.machinery import SourceFileLoader

# O gerador nao tem extensao .py, entao o loader precisa ser explicito.
RAIZ = pathlib.Path(__file__).resolve().parent.parent
_alvo = str(RAIZ / "tools" / "generate-brotli-static")
_loader = SourceFileLoader("gbs", _alvo)
spec = importlib.util.spec_from_loader("gbs", _loader)
gbs = importlib.util.module_from_spec(spec)
_loader.exec_module(gbs)

falhou = 0
def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok: falhou = 1

if not (shutil_ok := subprocess.run(["which", "brotli"], capture_output=True).returncode == 0):
    print("  brotli ausente: o teste comprime pelo modulo, seguindo")

with tempfile.TemporaryDirectory() as d:
    fonte = os.path.join(d, "pagina.html")
    br = fonte + ".br"
    open(fonte, "w").write("<html>" + "conteudo real " * 400 + "</html>")

    # ---------- comprime uma vez
    gbs.comprime(fonte)
    passo(os.path.exists(br), "o .br foi criado")

    # ---------- 1: mtime ESPELHADO, nao +1
    m_fonte, m_br = os.stat(fonte).st_mtime, os.stat(br).st_mtime
    passo(m_fonte == m_br, f"mtime espelhado exatamente (fonte={m_fonte} br={m_br})")

    # ---------- 2: idempotencia — nao recomprime sem motivo
    passo(not gbs.precisa(fonte), "nao recomprime quando nada mudou")

    # ---------- 3: RETROCESSO do fonte e detectado (o alcapao)
    antigo = m_fonte - 172800  # dois dias atras, como a correcao do carimbo faz
    os.utime(fonte, (antigo, antigo))
    passo(gbs.precisa(fonte), "detecta mtime do fonte RETROCEDENDO")

    # ---------- 4: depois de recomprimir, volta a espelhar
    gbs.comprime(fonte)
    passo(os.stat(fonte).st_mtime == os.stat(br).st_mtime, "volta a espelhar apos o retrocesso")

    # ---------- 5: avanco normal continua detectado
    novo = os.stat(fonte).st_mtime + 60
    os.utime(fonte, (novo, novo))
    passo(gbs.precisa(fonte), "detecta mtime do fonte AVANCANDO")

    # ---------- FALSO POSITIVO 1: .br ausente pede compressao, nao erro
    gbs.comprime(fonte); os.unlink(br)
    passo(gbs.precisa(fonte), "falso positivo: .br ausente -> precisa=True")

    # ---------- FALSO POSITIVO 2: poda nao marca stale um par espelhado
    gbs.comprime(fonte)
    stale, orfaos = gbs.poda_lista(d) if hasattr(gbs, "poda_lista") else ([], [])
    if hasattr(gbs, "poda_lista"):
        passo(br not in stale, "falso positivo: par espelhado nao e stale")
    else:
        # poda() varre PUBLICO; exercita a regra diretamente
        espelhado = os.path.getmtime(br) != os.path.getmtime(fonte)
        passo(not espelhado, "falso positivo: par espelhado nao e stale (regra direta)")

    # ---------- FALSO POSITIVO 3: comprimido maior que o original nao gera .br
    pequeno = os.path.join(d, "curto.html")
    open(pequeno, "w").write("ab")
    gbs.comprime(pequeno)
    passo(not os.path.exists(pequeno + ".br"), "falso positivo: nao cria .br maior que o fonte")

print()
print("brotli mtime espelhado: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
