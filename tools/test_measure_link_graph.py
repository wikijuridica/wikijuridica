#!/usr/bin/env python3
"""test_measure_link_graph — testes de tools/measure-link-graph.

POR QUE ELE EXISTE. O instrumento que produz a baseline do grafo de links não
podia nascer cego: `tools/run-qualidade-diaria` descobre testes Go por
`./internal/... ./cmd/...` e testes Python por glob em `tools/test_*.py`. Um
medidor que ninguém executa envelhece em silêncio, e uma baseline errada é pior
que baseline nenhuma — o gate mesh-no-worse vai comparar contra ela.

O QUE ELE COBRE. As funções puras (percentil, resumo, área, doorway) sobre casos
construídos, e a execução real sobre o acervo, conferindo o formato e as
invariantes que a tabela de aceite do plano usa. Nada aqui escreve em disco.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "measure-link-graph")


def carrega_modulo():
    """Importa o script sem extensão .py, que é como tools/ nomeia comando."""
    spec = importlib.util.spec_from_loader(
        "measure_link_graph",
        importlib.machinery.SourceFileLoader("measure_link_graph", FERRAMENTA),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


falhas: list[str] = []


def confere(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhas.append(mensagem)


def testa_percentil(m) -> None:
    confere(m.percentil([], 0.5) == 0.0, "percentil de lista vazia deveria ser 0.0")
    confere(m.percentil([7], 0.95) == 7.0, "percentil de um elemento é o próprio")
    confere(m.percentil([1, 2, 3, 4], 0.0) == 1.0, "p0 é o mínimo")
    confere(m.percentil([1, 2, 3, 4], 1.0) == 4.0, "p100 é o máximo")
    # Interpolação linear: entre 2 e 3, na metade do vão de 3 passos.
    confere(abs(m.percentil([1, 2, 3, 4], 0.5) - 2.5) < 1e-9,
            "mediana de [1,2,3,4] deveria ser 2,5 por interpolação")


def testa_resumo(m) -> None:
    confere(m.resumo([]) == {"n": 0}, "resumo de lista vazia deveria trazer só n")
    r = m.resumo([1, 1, 2, 3, 5])
    confere(r["n"] == 5 and r["minimo"] == 1 and r["maximo"] == 5,
            f"resumo com extremos errados: {r}")
    confere(abs(r["media"] - 2.4) < 1e-9, f"média errada: {r['media']}")


def testa_area(m) -> None:
    confere(m.area_de("/familia/guarda/") == "familia", "área é o primeiro segmento")
    confere(m.area_de("/") == "", "raiz não tem área")
    confere(m.area_de("/glossario/") == "glossario", "hub de área")


def testa_doorway(m) -> None:
    """Duas páginas da mesma área com vizinhança quase igual são molde; áreas
    diferentes nunca formam par, porque DetectDoorwayMolds só olha same-area."""
    mesma_area = {
        "/x/a/": ["/x/1/", "/x/2/", "/x/3/", "/x/4/"],
        "/x/b/": ["/x/1/", "/x/2/", "/x/3/", "/x/5/"],  # Jaccard 3/5 = 0,60
        "/x/c/": ["/x/7/", "/x/8/", "/x/9/"],
    }
    pares, paginas, _ = m.pares_doorway(mesma_area)
    confere(pares == 1, f"esperava 1 par acima de 0,50, veio {pares}")
    confere(paginas == 2, f"esperava 2 páginas envolvidas, veio {paginas}")

    areas_distintas = {
        "/x/a/": ["/z/1/", "/z/2/", "/z/3/"],
        "/y/b/": ["/z/1/", "/z/2/", "/z/3/"],  # idênticas, mas áreas diferentes
    }
    pares, _, _ = m.pares_doorway(areas_distintas)
    confere(pares == 0, "par de áreas diferentes não é molde de doorway")

    abaixo = {
        "/x/a/": ["/x/1/", "/x/2/", "/x/3/", "/x/4/"],
        "/x/b/": ["/x/1/", "/x/5/", "/x/6/", "/x/7/"],  # Jaccard 1/7
    }
    pares, _, _ = m.pares_doorway(abaixo)
    confere(pares == 0, "vizinhança pouco compartilhada não é molde")


def testa_execucao_real() -> None:
    """Roda o comando de verdade sobre o acervo e confere o contrato de saída.

    Se public/ não existir (ambiente sem acervo), o comando devolve 2 e o teste
    reconhece isso como ambiente, não como falha.
    """
    proc = subprocess.run([sys.executable, FERRAMENTA], cwd=RAIZ,
                          capture_output=True, timeout=150)
    if proc.returncode == 2:
        print("  (acervo ausente neste ambiente — execução real pulada)")
        return
    confere(proc.returncode == 0,
            f"measure-link-graph devolveu {proc.returncode}: "
            f"{proc.stderr.decode('utf-8', 'replace')[:200]}")
    try:
        d = json.loads(proc.stdout.decode("utf-8"))
    except json.JSONDecodeError as erro:
        falhas.append(f"saída não é JSON: {erro}")
        return

    for chave in ("universo", "arestas", "cross_area", "reciprocidade", "entrada",
                  "doorway", "blocos_byte_identicos", "ancoras", "bytes"):
        confere(chave in d, f"seção {chave!r} ausente da medição")

    # Invariantes que a tabela de aceite do plano usa. São propriedades, não
    # números fixos: o acervo cresce, e um teste que exigisse 60.664 arestas
    # nasceria vermelho no dia seguinte.
    arestas = d["arestas"]["total"]
    confere(arestas > 0, "acervo com bloco de malha mas zero arestas")
    confere(d["arestas"]["slots_ociosos"] >= 0, "slots ociosos negativos")
    confere(0.0 <= d["cross_area"]["fracao"] <= 1.0, "fração cross-área fora de [0,1]")
    confere(0.0 <= d["reciprocidade"]["fracao"] <= 1.0, "fração recíproca fora de [0,1]")
    confere(d["reciprocidade"]["arestas_reciprocas"] <= arestas,
            "mais arestas recíprocas do que arestas")
    confere(d["entrada"]["malha"]["n"] == d["universo"]["com_bloco_de_malha"],
            "grau de entrada medido sobre universo diferente do bloco")
    confere(d["entrada"]["total"]["minimo"] >= d["entrada"]["malha"]["minimo"],
            "entrada TOTAL não pode ser menor que a de malha")
    confere(d["defeitos_mecanicos"].get("destino_inexistente", 0) == 0,
            "há link do bloco apontando para rota que não existe em disco")
    confere(d["defeitos_mecanicos"].get("autolink", 0) == 0,
            "há página linkando para si mesma no bloco")
    confere(d["bytes"]["paginas_acima_de_50kb"] == 0,
            "página publicada acima do teto de 50 KB do contrato de indexação")


def main() -> int:
    modulo = carrega_modulo()
    testa_percentil(modulo)
    testa_resumo(modulo)
    testa_area(modulo)
    testa_doorway(modulo)
    testa_execucao_real()

    if falhas:
        for f in falhas:
            print(f"FALHA: {f}", file=sys.stderr)
        return 1
    print("test_measure_link_graph: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
