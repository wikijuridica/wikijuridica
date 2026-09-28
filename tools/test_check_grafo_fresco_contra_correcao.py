#!/usr/bin/env python3
"""Teste de tools/check-grafo-fresco-contra-correcao.

RODAR:  python3 tools/test_check_grafo_fresco_contra_correcao.py

TOTALMENTE OFFLINE e sem tocar o dado vivo: cada caso monta a própria raiz
temporária com `data/ai/extracoes_dispositivos.jsonl` e um `data/ai/grafo.sqlite`
de uma tabela só, e invoca a ferramenta como SUBPROCESSO com `--raiz`, para
exercitar `sys.exit(main())` — a linha que decide 0 ou 1 — e não `main()`
importado.

★ POR QUE A MAIORIA DOS CASOS É DE FALSO POSITIVO

O detector ingênuo aqui é "o arquivo é mais novo que o grafo, logo o grafo está
velho". Ele reprovaria SEMPRE, porque o cérebro apende 24/7: no dado real de
2026-09-11 são 37.212 linhas para 35.013 chaves, e das 2.015 chaves
reprocessadas 1.530 são ACRÉSCIMO — o grafo fica incompleto, não errado, e o
timer o completa. Os casos `chave_inedita_depois_do_grafo` e
`acrescimo_de_urn_depois_do_grafo` fixam isso: os dois saem 0.

O que tem de reprovar é estreito e é o incidente que originou o gate: a revisão
`norma_nomeada_no_artigo_v8` retirou `13105!art253` de `acordao:STJ:1444372`, o
writeback ficou correto no mesmo minuto e o grafo — regenerado ANTES — continuou
servindo a aresta. É o caso `remocao_de_urn_depois_do_grafo`.

★ PROVA POR MUTAÇÃO (cada caso mata um mutante nomeado)

  remocao_de_urn_depois_do_grafo ....... `ultima >= penultima` virar `True`
                                          (tudo vira acréscimo, nada reprova)
  remocao_de_urn_antes_do_grafo ........ tirar a comparação `quando > quando_grafo`
                                          (correção antiga volta a reprovar)
  troca_de_urn_depois_do_grafo ......... `ultima >= penultima` virar
                                          `len(ultima) >= len(penultima)`
                                          (troca de mesmo tamanho passaria)
  grafo_sem_gerado_em .................. `quando_grafo is None` devolver 0
  primeira_ocorrencia_nao_e_correcao ... `len(ocorrencias) < 2` virar `< 1`
                                          (IndexError ou chave nova acusada)
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "check-grafo-fresco-contra-correcao")

falhas = []


def extracao(chave, carimbo, urns):
    """Um registro com a MESMA forma que internal/cerebro/extracao.go escreve."""
    return {
        "schema_version": "extracao_dispositivos_v1",
        "chave": chave,
        "gerado_em": carimbo,
        "modelo": "qwen3.5:4b",
        "texto_sha256": "0" * 64,
        "prompt_sha256": "1" * 64,
        "dispositivos": [{"urn": u, "norma": "", "artigo": "", "texto_citado": ""}
                         for u in urns],
    }


def monta(linhas, grafo_em):
    """Raiz temporária com as extrações e um grafo que declara `gerado_em`.

    `grafo_em=None` grava a tabela `meta` vazia — o grafo existe e não diz
    quando nasceu, que é o caso em que nenhum consumidor pode decidir nada.
    """
    destino = tempfile.mkdtemp(prefix="grafo-fresco-")
    pasta = os.path.join(destino, "data", "ai")
    os.makedirs(pasta)
    with open(os.path.join(pasta, "extracoes_dispositivos.jsonl"), "w",
              encoding="utf-8") as handle:
        for registro in linhas:
            handle.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")
    conexao = sqlite3.connect(os.path.join(pasta, "grafo.sqlite"))
    conexao.execute("create table meta (chave text primary key, valor text)")
    if grafo_em is not None:
        conexao.execute("insert into meta values ('gerado_em', ?)", (grafo_em,))
    conexao.commit()
    conexao.close()
    return destino


def roda(raiz):
    proc = subprocess.run([sys.executable, FERRAMENTA, "--raiz", raiz],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def caso(nome, linhas, grafo_em, esperado, exige=()):
    raiz = monta(linhas, grafo_em)
    try:
        codigo, saida = roda(raiz)
    finally:
        shutil.rmtree(raiz, ignore_errors=True)
    if codigo != esperado:
        falhas.append("%s: exit %d, esperado %d\n%s" % (nome, codigo, esperado, saida))
        return
    for trecho in exige:
        if trecho not in saida:
            falhas.append("%s: a saída não traz %r\n%s" % (nome, trecho, saida))
            return
    print("  ok   %-38s exit %d" % (nome, codigo))


ANTES = "2026-09-11T00:00:00Z"
GRAFO = "2026-09-11T01:00:00Z"
DEPOIS = "2026-09-11T02:00:00Z"

CPC253 = "urn:lex:br:federal:lei:2015-03-16;13105!art253"
CPC1022 = "urn:lex:br:federal:lei:2015-03-16;13105!art1022"
CPC489 = "urn:lex:br:federal:lei:2015-03-16;13105!art489"

# ---------------------------------------------------------------- FALSO POSITIVO
# O cérebro apende 24/7. Nenhum destes é defeito, e todos saem 0.

caso("chave_inedita_depois_do_grafo",
     [extracao("acordao:STJ:1", ANTES, [CPC1022]),
      extracao("acordao:STJ:2", DEPOIS, [CPC489])],
     GRAFO, esperado=0)

caso("acrescimo_de_urn_depois_do_grafo",
     [extracao("acordao:STJ:1", ANTES, [CPC1022]),
      extracao("acordao:STJ:1", DEPOIS, [CPC1022, CPC489])],
     GRAFO, esperado=0,
     exige=("acréscimo: 1",))

caso("reprocessamento_identico_depois_do_grafo",
     [extracao("acordao:STJ:1", ANTES, [CPC1022]),
      extracao("acordao:STJ:1", DEPOIS, [CPC1022])],
     GRAFO, esperado=0)

caso("remocao_de_urn_antes_do_grafo",
     [extracao("acordao:STJ:1444372", "2026-09-10T00:00:00Z", [CPC253, CPC1022]),
      extracao("acordao:STJ:1444372", ANTES, [CPC1022])],
     GRAFO, esperado=0,
     exige=("correção: 1", "posterior a toda correção"))

caso("sem_extracoes_e_sem_grafo_nao_inventa_veredito",
     [], GRAFO, esperado=0)

# ---------------------------------------------------------------- REPROVA
# O incidente real de 2026-09-10, reduzido ao mínimo.

caso("remocao_de_urn_depois_do_grafo",
     [extracao("acordao:STJ:1444372", ANTES, [CPC253, CPC1022]),
      extracao("acordao:STJ:1444372", DEPOIS, [CPC1022])],
     GRAFO, esperado=1,
     exige=("acordao:STJ:1444372", CPC253, "generate-grafo-juridico"))

caso("troca_de_urn_depois_do_grafo",
     [extracao("acordao:STJ:1", ANTES, [CPC253]),
      extracao("acordao:STJ:1", DEPOIS, [CPC489])],
     GRAFO, esperado=1,
     exige=(CPC253,))

caso("grafo_sem_gerado_em",
     [extracao("acordao:STJ:1", ANTES, [CPC1022])],
     None, esperado=1,
     exige=("não declara `gerado_em`",))

print()
if falhas:
    for f in falhas:
        print("FALHOU: %s" % f)
    print("%d caso(s) falharam" % len(falhas))
    sys.exit(1)
print("todos os casos passaram")
