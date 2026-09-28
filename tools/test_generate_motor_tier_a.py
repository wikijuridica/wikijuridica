#!/usr/bin/env python3
"""test_generate_motor_tier_a — prova as quatro exclusoes do seletor de artigos,
cada uma com o caso concreto que a obriga.

POR QUE ESTE TESTE EXISTE. O plano do motor registrou que o gerador de pagina
de artigo emitiria `911-art-3` para um artigo cuja rota `lei-dl-911-art-3` JA
ESTA no ar — conteudo duplicado autoinfligido que
`check-v2-cross-shard-collision` nao pega, porque sao shards e slugs
diferentes. Medido em 2026-09-09 sobre o acervo real: a exclusao
`rota_ja_publicada` dispara 154 vezes, nao uma.

O mesmo plano listou os apelidos `cp`, `cpp`, `ctn` e `lgpd` como se fossem
derivados do disco. Nenhum dos quatro existe em rota nenhuma — foram
inventados, e apelido inventado e a causa raiz do caso `dl-911`. Por isso a
regra e RECUSAR a URN cujo apelido nao esteja na tabela derivada, nunca chutar.

Uso:
    python3 -m pytest tools/test_generate_motor_tier_a.py -q
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sqlite3

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def carrega():
    caminho = RAIZ / "tools" / "generate-motor-tier-a"
    spec = importlib.util.spec_from_loader(
        "generate_motor_tier_a",
        importlib.machinery.SourceFileLoader("generate_motor_tier_a", str(caminho)),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M = carrega()

URN_CC = "urn:lex:br:federal:lei:2002-01-10;10406!art186"
URN_CLT = "urn:lex:br:federal:decreto.lei:1943-05-01;5452!art3"
URN_REVOGADA = "urn:lex:br:federal:lei:1973-01-11;5869!art535"
URN_SEM_APELIDO = "urn:lex:br:federal:lei:2018-08-14;13709!art5"


def monta_raiz(tmp_path, urns, publicadas=("lei-cc-art-1639",), status_5869="revogado",
               so_processual=False, snapshots_de_artigo=()):
    """Monta uma raiz sintetica: grafo, corpus, shard publicado e snapshots."""
    raiz = str(tmp_path)
    os.makedirs(os.path.join(raiz, "data", "ai"), exist_ok=True)
    os.makedirs(os.path.join(raiz, "data", "legal-corpus"), exist_ok=True)
    os.makedirs(os.path.join(raiz, "data", "editorial", "v2_pages"), exist_ok=True)
    os.makedirs(os.path.join(raiz, "data", "source-snapshots"), exist_ok=True)

    con = sqlite3.connect(os.path.join(raiz, "data", "ai", "grafo.sqlite"))
    con.execute("create table nos (id integer primary key, tipo text, chave text)")
    con.execute("create table arestas (origem integer, destino integer, tipo text)")

    proximo = [1]

    def no(tipo, chave):
        con.execute("insert into nos (id, tipo, chave) values (?,?,?)",
                    (proximo[0], tipo, chave))
        proximo[0] += 1
        return proximo[0] - 1

    # A CHAVE DO GRAFO TEM PREFIXO: `sumula:STJ:37`, nunca `STJ:37`. A primeira
    # versao desta fixture usava a forma nua e por isso o teste passava ANTES e
    # DEPOIS da correcao do filtro — exercitava so o caminho "nao processual" e
    # nao prendia nada. Gate verde nao e prova.
    sumula = no("sumula", "sumula:STJ:37")
    sumula_processual = no("sumula", "sumula:STJ:7")
    for urn in urns:
        disp = no("dispositivo", urn)
        # tres acordaos citantes, cada um citando tambem uma sumula NAO
        # processual — o piso de evidencia do Tier A.
        for _ in range(3):
            ac = no("acordao", f"acordao:STJ:{proximo[0]}")
            con.execute("insert into arestas values (?,?,'cita')", (ac, disp))
            con.execute("insert into arestas values (?,?,'cita')",
                        (ac, sumula_processual if so_processual else sumula))
    con.commit()
    con.close()

    with open(os.path.join(raiz, "data", "legal-corpus", "cc.json"), "w", encoding="utf-8") as f:
        json.dump({"nome": "Código Civil (Lei 10.406/2002)",
                   "citation_url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm",
                   "articles": {"186": "Aquele que, por ação ou omissão voluntária, causar dano."}}, f)
    with open(os.path.join(raiz, "data", "legal-corpus", "clt.json"), "w", encoding="utf-8") as f:
        json.dump({"nome": "CLT (Decreto-Lei 5.452/1943)",
                   "citation_url": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm",
                   "articles": {"3": "Considera-se empregado toda pessoa física que prestar serviços."}}, f)
    with open(os.path.join(raiz, "data", "legal-corpus", "cpc73.json"), "w", encoding="utf-8") as f:
        json.dump({"nome": "Código de Processo Civil (Lei 5.869/1973)",
                   "citation_url": "https://www.planalto.gov.br/ccivil_03/leis/l5869.htm",
                   "articles": {"535": "Cabem embargos de declaração."}}, f)

    registros = [
        {"intent_id": "lei-cc-art-1639",
         "official_sources": [{"url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art1639",
                               "name": "Código Civil (Lei nº 10.406/2002), art. 1.639"}]},
        {"intent_id": "lei-clt-art-8",
         "official_sources": [{"url": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm#art8",
                               "name": "Decreto-Lei 5.452/1943 (CLT), art. 8º"}]},
        {"intent_id": "lei-cpc73-art-1",
         "official_sources": [{"url": "https://www.planalto.gov.br/ccivil_03/leis/l5869.htm#art1",
                               "name": "Lei 5.869/1973, art. 1º"}]},
    ]
    for extra in publicadas:
        if extra not in [r["intent_id"] for r in registros]:
            registros.append({"intent_id": extra, "official_sources": []})
    with open(os.path.join(raiz, "data", "editorial", "v2_pages", "leis-01.jsonl"),
              "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(os.path.join(raiz, "data", "source-snapshots", "manifest.jsonl"),
              "w", encoding="utf-8") as f:
        f.write(json.dumps({"urn_lex": URN_CC, "vigencia_status": "vigente"}) + "\n")
        f.write(json.dumps({"urn_lex": URN_CLT, "vigencia_status": "vigente"}) + "\n")
        f.write(json.dumps({"urn_lex": URN_REVOGADA, "vigencia_status": status_5869}) + "\n")
        # Observacao POR ARTIGO, no formato real do manifest de producao
        # (`dispositivo: "art_186"`, medido em 2026-09-10 em 13.300 de 13.437
        # linhas). Sem ela o candidato so tem evidencia da norma.
        for registro in snapshots_de_artigo:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return raiz


def roda(raiz, capsys):
    saida = os.path.join(raiz, "saida.jsonl")
    codigo = M.main_com_argv(["--raiz", raiz, "--saida", saida])
    texto = capsys.readouterr().out
    linhas = []
    if os.path.isfile(saida):
        with open(saida, encoding="utf-8") as f:
            linhas = [json.loads(l) for l in f if l.strip()]
    return codigo, texto, linhas


def test_artigo_com_evidencia_e_texto_entra(tmp_path, capsys):
    raiz = monta_raiz(tmp_path, [URN_CC])
    codigo, _, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert [r["intent_id"] for r in linhas] == ["lei-cc-art-186"]
    assert linhas[0]["apelido"] == "cc", "o apelido vem do intent_id publicado, nao do nome do arquivo"
    assert linhas[0]["acordaos_citantes"] == 3


def test_rota_ja_publicada_nunca_vira_candidata(tmp_path, capsys):
    """O caso `dl-911`: o mesmo artigo com outro slug e duplicata que o gate de
    colisao entre shards nao pega."""
    raiz = monta_raiz(tmp_path, [URN_CC], publicadas=("lei-cc-art-186",))
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert linhas == []
    assert "rota_ja_publicada" in texto


def test_apelido_nao_derivavel_do_disco_e_recusado(tmp_path, capsys):
    """LGPD (13709) nao tem rota publicada nenhuma: nao ha apelido a derivar, e
    inventar `lgpd` e exatamente o erro que produziu o caso `dl-911`."""
    raiz = monta_raiz(tmp_path, [URN_SEM_APELIDO])
    # O texto EXISTE: assim a unica razao possivel da exclusao e o apelido.
    with open(os.path.join(raiz, "data", "legal-corpus", "lgpd.json"), "w", encoding="utf-8") as f:
        json.dump({"nome": "Lei Geral de Proteção de Dados (Lei 13.709/2018)",
                   "citation_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
                   "articles": {"5": "Para os fins desta Lei, considera-se: I - dado pessoal."}}, f)
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert linhas == []
    assert "apelido_nao_derivavel_do_disco" in texto


def test_norma_revogada_fica_de_fora(tmp_path, capsys):
    """CPC/1973: a vigencia se le de source-snapshots, nao de lista fixa."""
    raiz = monta_raiz(tmp_path, [URN_REVOGADA])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert linhas == []
    assert "norma_revogada" in texto


def test_mesma_norma_vigente_passa_a_entrar(tmp_path, capsys):
    """Controle negativo da exclusao por vigencia: com a fonte dizendo
    'vigente', o MESMO artigo entra — a exclusao mede vigencia, nao o numero
    da norma."""
    raiz = monta_raiz(tmp_path, [URN_REVOGADA], status_5869="vigente")
    codigo, _, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert [r["intent_id"] for r in linhas] == ["lei-cpc73-art-535"]


def test_sem_texto_do_artigo_nao_vira_pagina(tmp_path, capsys):
    """Sem texto oficial nao ha camada citada, nao ha ancora e nao ha pagina."""
    raiz = monta_raiz(tmp_path, [URN_CC])
    with open(os.path.join(raiz, "data", "legal-corpus", "cc.json"), "w", encoding="utf-8") as f:
        json.dump({"nome": "Código Civil (Lei 10.406/2002)",
                   "citation_url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm",
                   "articles": {"1639": "Outro artigo, nao o 186."}}, f)
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert linhas == []
    assert "sem_texto_do_artigo" in texto


def test_sumula_processual_com_prefixo_do_grafo_nao_sustenta_pagina(tmp_path, capsys):
    """O caso que quebrou em producao, agora preso por teste.

    Os nos do grafo sao `sumula:STJ:7`; o filtro comparava contra `STJ:7` e
    NUNCA casava. O efeito visivel foi uma pagina afirmando que "enunciados de
    admissibilidade recursal ficam de fora desta lista de proposito" logo acima
    de uma lista que comecava pela Sumula 7 do STJ — o enunciado de
    admissibilidade mais citado que existe.

    MUTACAO QUE TEM DE REPROVAR: fazer `sumula_normalizada` devolver a chave
    intacta faz este teste voltar a aprovar o artigo, que e o bug.
    """
    raiz = monta_raiz(tmp_path, [URN_CC], so_processual=True)
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    assert linhas == [], "artigo sustentado SO por sumula de admissibilidade nao vira pagina"
    assert "sem_sumula_nao_processual_nem_cocitacao" in texto


def test_urn_de_paragrafo_funde_no_artigo_em_vez_de_duplicar_rota(tmp_path, capsys):
    """`!art186` e `!art186_par2` sao o MESMO artigo e o mesmo intent_id.

    Emitidas separadas, produziriam `lei-cc-art-186` duas vezes no shard — rota
    duplicada, que e o dano que este seletor existe para impedir e que
    check-v2-portfolio-pairing reprovou com `lei-cpc-art-485 aparece 3x`.
    """
    raiz = monta_raiz(tmp_path, [URN_CC, URN_CC + "_par2"])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0
    intents = [r["intent_id"] for r in linhas]
    assert intents == ["lei-cc-art-186"], f"esperava uma linha por artigo; veio {intents}"
    assert "urn_de_paragrafo_fundida_no_artigo" in texto
    # A evidencia se funde, e o numero de acordaos NAO soma: o acordao que cita
    # o caput e o paragrafo e UM acordao.
    assert linhas[0]["acordaos_citantes"] == 3
    assert len(linhas[0]["urns_do_artigo"]) == 2


# ★ SEM ESTA GUARDA O ARQUIVO SAI 0 SEM EXECUTAR UMA ASSERCAO (2026-09-10).
#
# `tools/run-qualidade-diaria:455` invoca cada teste desta pasta como
# `python3 "$teste"` — nunca `pytest arquivo.py`. Um modulo pytest sem
# `__main__` define as funcoes, nao chama nenhuma e devolve exit 0. O ledger
# grava "verde" para um teste que nao rodou, que e a forma mais silenciosa de
# uma bancada mentir: as 17 assercoes deste arquivo estavam nesse estado.
# `-p no:cacheprovider` evita deixar `.pytest_cache` no repositorio.

# ---------------------------------------------------------------------------
# VIGENCIA E DO ARTIGO, NAO DA NORMA (2026-09-10)
# ---------------------------------------------------------------------------
#
# A versao anterior lia o `vigencia_status` PREDOMINANTE por numero de norma e o
# aplicava ao artigo. Uma norma vigente com um artigo revogado sairia como
# "vigente" na pagina daquele artigo — a classe de defeito que a auditoria
# adversarial ja pegou uma vez neste motor. Os tres casos abaixo fixam a
# assimetria: evidencia de NORMA reprova, nunca aprova.


def test_artigo_revogado_na_fonte_nao_vira_pagina(tmp_path, capsys):
    """★ A NORMA VIGENTE NAO SALVA O ARTIGO REVOGADO.

    O manifest diz que a Lei 10.406 esta vigente E que o art. 186 dela esta
    revogado. Antes, o candidato saia com vigencia_status "vigente"."""
    raiz = monta_raiz(
        tmp_path, [URN_CC],
        snapshots_de_artigo=[
            {"urn_lex": "urn:lex:br:federal:lei:2002-01-10;10406",
             "dispositivo": "art_186", "vigencia_status": "revogado",
             "revogado_por": "urn:lex:br:federal:lei:2020-01-01;13999",
             "version_seq": 2, "as_of_date": "2026-09-01"},
        ])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0, texto
    assert linhas == [], linhas
    assert "artigo_revogado_na_fonte" in texto, texto


def test_artigo_observado_vigente_carrega_o_status_da_propria_observacao(tmp_path, capsys):
    raiz = monta_raiz(
        tmp_path, [URN_CC],
        snapshots_de_artigo=[
            {"urn_lex": "urn:lex:br:federal:lei:2002-01-10;10406",
             "dispositivo": "art_186", "vigencia_status": "vigente",
             "version_seq": 3, "as_of_date": "2026-09-02"},
        ])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0, texto
    assert len(linhas) == 1, texto
    assert linhas[0]["vigencia_status"] == "vigente", linhas[0]


def test_sem_observacao_do_artigo_o_status_diz_que_a_evidencia_e_da_norma(tmp_path, capsys):
    """★ NAO AFIRMAR VIGENCIA QUE A FONTE NAO OBSERVOU.

    Sem linha de `dispositivo` para o artigo, o candidato sai marcado
    `vigencia_da_norma_apenas` — e cmd/generate-lei-artigo-pages:1134 recusa
    qualquer coisa diferente de "vigente", entao a pagina nao nasce afirmando
    vigor sobre evidencia que nao a sustenta. Medido em 2026-09-10: eram QUATRO
    artigos do Codigo Civil (757, 760, 765, 786) saindo como "vigente" assim."""
    raiz = monta_raiz(tmp_path, [URN_CC])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0, texto
    assert len(linhas) == 1, texto
    assert linhas[0]["vigencia_status"] == "vigencia_da_norma_apenas", linhas[0]


def test_observacao_mais_recente_vence_a_predominante(tmp_path, capsys):
    """Contar ocorrencias faria a HISTORIA da norma vencer o estado de hoje: duas
    linhas antigas de "revogado" contra uma recente de "vigente" tem de resultar
    em vigente, e o inverso tambem."""
    raiz = monta_raiz(
        tmp_path, [URN_CC],
        snapshots_de_artigo=[
            {"urn_lex": "urn:lex:br:federal:lei:2002-01-10;10406",
             "dispositivo": "art_186", "vigencia_status": "vigente",
             "version_seq": 1, "as_of_date": "2020-01-01"},
            {"urn_lex": "urn:lex:br:federal:lei:2002-01-10;10406",
             "dispositivo": "art_186", "vigencia_status": "vigente",
             "version_seq": 2, "as_of_date": "2021-01-01"},
            {"urn_lex": "urn:lex:br:federal:lei:2002-01-10;10406",
             "dispositivo": "art_186", "vigencia_status": "revogado",
             "version_seq": 3, "as_of_date": "2026-09-01"},
        ])
    codigo, texto, linhas = roda(raiz, capsys)
    assert codigo == 0, texto
    assert linhas == [], texto
    assert "artigo_revogado_na_fonte" in texto, texto


def test_artigo_base_reduz_paragrafo_e_letra(tmp_path):
    assert M.artigo_base("art_186") == "186"
    assert M.artigo_base("art. 223-B") == "223b"
    assert M.artigo_base("art223b") == "223b"
    assert M.artigo_base("art_152_par2") == "152"
    assert M.artigo_base("artigo sem numero") is None
    assert M.artigo_base("") is None

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
