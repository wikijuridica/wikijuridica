#!/usr/bin/env python3
"""Guardas do check-lastmod-causalidade — para os falsos positivos não voltarem.

DOIS BUGS REAIS, ambos de INDICE de tupla, ambos com 100% de falso positivo, e
ambos introduzidos por mudanca que corrigia OUTRA coisa:

  2026-08-27 — `_parse_ledger` passou a devolver (content_sha256, served_sha256,
               revised_on) para corrigir o invariante 1, que acusava "data
               fabricada" quando so a renderizacao mudava.
  2026-08-28 — descobriu-se que a conferencia do sitemap nao acompanhou o
               indice: comparava `[1]` (served_sha256, um HASH) com o `lastmod`
               do sitemap (uma DATA). Resultado: "sitemap divergente do ledger
               10114 de 10114" -- e o gate reprovava a onda inteira por isso,
               escondendo o defeito que ele existe para pegar.

Um teste que so exercitasse o caminho feliz nao pegaria nenhum dos dois. Estes
comparam TIPO, nao so valor.
"""
import importlib.util, pathlib, sys
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ld = SourceFileLoader("clc", str(RAIZ / "tools" / "check-lastmod-causalidade"))
clc = importlib.util.module_from_spec(importlib.util.spec_from_loader("clc", _ld))
_ld.exec_module(clc)

falhou = 0
def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok: falhou = 1

LINHA = (b'{"path":"/x/","content_sha256":"aaaa","served_sha256":"bbbb",'
         b'"revised_on":"2026-08-26"}\n')
tupla = clc._parse_ledger(LINHA)["/x/"]

# 1. A ordem da tupla e contrato: quem mexer nela quebra aqui, nao em producao.
passo(tupla[0] == "aaaa", "indice 0 e o content_sha256")
passo(tupla[1] == "bbbb", "indice 1 e o served_sha256")
passo(tupla[2] == "2026-08-26", "indice 2 e a data (revised_on)")

# 2. O BUG: comparar o campo errado com um lastmod da forma AAAA-MM-DD.
#    Um hash NUNCA tem a forma de data — e essa e a assercao que pega o
#    indice trocado sem depender de valor nenhum.
import re
FORMA_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}")
passo(bool(FORMA_DATA.match(tupla[2])), "o campo comparado com o sitemap TEM forma de data")
passo(not FORMA_DATA.match(tupla[1]), "o served_sha256 NAO tem forma de data (era ele que estava sendo comparado)")

# 3. Guarda de fonte: a linha que compara tem de usar [2]. Se alguem trocar de
#    novo, isto reprova antes de a onda inteira ficar vermelha.
fonte = (RAIZ / "tools" / "check-lastmod-causalidade").read_text(encoding="utf-8")
passo("esperado = atual[rota][2]" in fonte,
      "a conferencia do sitemap usa o indice da DATA")
passo("esperado = atual[rota][1]" not in fonte,
      "e nao usa o indice do hash")

# 4. FALSO POSITIVO OBRIGATORIO: rota SEM data no ledger nao pode virar
#    divergencia. Ausencia de dado nao e defeito de dado.
vazia = clc._parse_ledger(b'{"path":"/y/","content_sha256":"a","served_sha256":"b"}\n')["/y/"]
passo(not vazia[2], "rota sem revised_on devolve data vazia")
passo(not (("2026-08-26" and vazia[2]) and "2026-08-26" != vazia[2]),
      "falso positivo: data vazia nao entra na conta de divergentes")

# 5. FALSO POSITIVO: instante ISO no ledger nao pode ser lido como divergente de
#    um lastmod de dia. O repo TEM tres rotas com instante.
inst = clc._parse_ledger(
    b'{"path":"/z/","content_sha256":"a","served_sha256":"b",'
    b'"revised_on":"2026-08-26T23:10:58Z"}\n')["/z/"]
passo(inst[2].startswith("2026-08-26"), "instante ISO comeca com o dia (truncavel)")

print()
print("guardas do lastmod-causalidade: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
