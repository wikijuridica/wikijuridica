#!/usr/bin/env python3
"""test_medir_pareado_energia_fuso — prova que a atribuicao de regime cruza as
duas series pelo INSTANTE, nunca pela string do carimbo.

POR QUE ESTE TESTE EXISTE, com o numero que obriga (medido em 2026-09-09, na
primeira execucao real da ferramenta): `data/ops/ia_local_daily.jsonl` grava o
carimbo em UTC ("...Z") e `data/ops/energia_cpu.jsonl` grava em horario local
("...-03:00"). Comparadas como texto, "14:33:39-03:00" < "16:17:26Z", entao a
leitura de energia das 14:33 LOCAL (17:33Z) passava a valer para amostras do
cerebro a partir das 14:33Z — TRES HORAS antes de o regime existir. Resultado:
243 amostras colhidas sob PL1=17W durante dois deploys foram rotuladas como
PL1=15W, e a ferramenta imprimiu "PL1=17W contra PL1=15W: -13,2%". O numero
media fuso horario, nao watt, e ia decidir a troca do Environment= de
`ops/systemd/wikijuridica-energia.service`.

O segundo teste prova a guarda de densidade: um lote de embedding leva 28-36 s
medidos, entao mais de 3 amostras por minuto num regime e fisicamente
impossivel e denuncia rotulagem errada. A ferramenta tem de ABORTAR nomeando o
defeito, em vez de imprimir um numero que mente.

MUTACAO QUE TEM DE REPROVAR: trocar `instante(ts)` por comparacao direta de
string em `regime_de` faz `test_carimbo_em_fusos_diferentes_nao_troca_regime`
falhar.

Uso:
    python3 -m pytest tools/test_medir_pareado_energia_fuso.py -q
"""

from __future__ import annotations

import datetime
import importlib.machinery
import importlib.util
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def carrega():
    caminho = RAIZ / "tools" / "medir-pareado-energia"
    spec = importlib.util.spec_from_loader(
        "medir_pareado_energia",
        importlib.machinery.SourceFileLoader("medir_pareado_energia", str(caminho)),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo

M = carrega()


def test_carimbo_em_fusos_diferentes_nao_troca_regime():
    """A serie de energia em -03:00, a do cerebro em Z, troca de regime no meio.

    A amostra do cerebro 1 s ANTES da troca (comparada em UTC) fica no regime
    antigo; 1 s DEPOIS, no novo. Com comparacao de string o primeiro caso cai
    no regime novo, porque "17:00:00-03:00" < "19:59:59Z" lexicograficamente.
    """
    energia = [
        {"ts": "2026-09-09T14:00:00-03:00", "pl1_mmio_uw": 17000000, "no_turbo": 0, "load1": 2.0},
        {"ts": "2026-09-09T17:00:00-03:00", "pl1_mmio_uw": 15000000, "no_turbo": 0, "load1": 2.0},
    ]
    pontos = M.regime_por_instante(energia)

    # 17:00 local = 20:00Z. Um segundo antes ainda e o regime de 17 W.
    antes = M.regime_de("2026-09-09T19:59:59Z", pontos)
    depois = M.regime_de("2026-09-09T20:00:01Z", pontos)

    assert antes is not None and depois is not None
    assert antes[0] == 17000000, f"1 s antes da troca devia ser 17 W; veio {antes[0]}"
    assert depois[0] == 15000000, f"1 s depois da troca devia ser 15 W; veio {depois[0]}"


def test_instante_normaliza_os_dois_fusos_para_o_mesmo_ponto():
    """14:33:39-03:00 e 17:33:39Z sao o MESMO instante."""
    local = M.instante("2026-09-09T14:33:39-03:00")
    utc = M.instante("2026-09-09T17:33:39Z")
    assert local == utc
    assert local.tzinfo == datetime.timezone.utc


def test_carimbo_sem_fuso_nao_vira_regime():
    """Carimbo ingenuo nao se compara com carimbo com fuso: descarta, nao adivinha."""
    assert M.instante("2026-09-09T14:33:39") is None
    assert M.instante("") is None
    assert M.instante("ontem de tarde") is None


def test_duracao_por_regime_mede_a_janela_de_cada_regime():
    energia = [
        {"ts": "2026-09-09T14:00:00-03:00", "pl1_mmio_uw": 17000000, "no_turbo": 0, "load1": 1.0},
        {"ts": "2026-09-09T15:00:00-03:00", "pl1_mmio_uw": 15000000, "no_turbo": 0, "load1": 1.0},
        {"ts": "2026-09-09T15:30:00-03:00", "pl1_mmio_uw": 15000000, "no_turbo": 0, "load1": 1.0},
    ]
    pontos = M.regime_por_instante(energia)
    # Com `fim` explicito a janela e' exatamente a da serie: o regime de 17 W vai
    # das 14h as 15h, e o de 15 W das 15h ao fim declarado.
    fim = M.instante("2026-09-09T15:30:00-03:00")
    duracao = M.duracao_por_regime(pontos, fim=fim)
    assert duracao[(17000000, 0)] == 60.0
    assert duracao[(15000000, 0)] == 30.0

    # ★ SEM `fim`, O REGIME VIGENTE VAI ATE AGORA — E ISSO E' O CONSERTO, NAO UM
    #   DEFEITO (2026-09-09, commit 461fcb7b).
    #
    # Somando so intervalos entre pontos consecutivos, o ultimo regime ficava com
    # 0 minuto e a guarda de densidade pulava por `minutos <= 0` — muda no caso
    # exato que a motivou. Este assert mata a mutacao que remove a extensao: o
    # regime vigente tem de medir MAIS que os 30 min entre suas duas amostras.
    aberta = M.duracao_por_regime(pontos)
    assert aberta[(17000000, 0)] == 60.0
    assert aberta[(15000000, 0)] > 30.0


def test_carga_enquadra_a_leitura_pelas_duas_amostras_vizinhas():
    """Com amostragem de 5 min, a amostra ANTERIOR sozinha deixa passar leitura
    colhida no meio de um pico que a seguinte ja registra."""
    energia = [
        {"ts": "2026-09-09T14:00:00-03:00", "pl1_mmio_uw": 17000000, "no_turbo": 0, "load1": 1.0},
        {"ts": "2026-09-09T14:05:00-03:00", "pl1_mmio_uw": 17000000, "no_turbo": 0, "load1": 20.0},
    ]
    pontos = M.regime_por_instante(energia)
    regime = M.regime_de("2026-09-09T17:02:00Z", pontos)  # 14:02 local, entre as duas
    assert regime[2] == 20.0, "a carga tem de ser a MAIOR das duas amostras que enquadram"


def _serie(raiz, energia, ia):
    import json
    import os
    os.makedirs(os.path.join(raiz, "data", "ops"), exist_ok=True)
    for nome, linhas in ((M.SERIE_ENERGIA, energia), (M.SERIE_IA, ia)):
        with open(os.path.join(raiz, nome), "w", encoding="utf-8") as f:
            for linha in linhas:
                f.write(json.dumps(linha) + "\n")


def test_densidade_impossivel_aborta_em_vez_de_dar_numero(tmp_path, capsys):
    """O caso REAL de 2026-09-09: uma amostra de energia num regime aplicado ha
    5 minutos, e 244 amostras do cerebro atribuidas a ele. Um lote leva 28-36 s:
    244 em 5 min e impossivel. A ferramenta tem de ABORTAR nomeando o defeito.

    Este teste tambem prende a extensao do ULTIMO regime ate a leitura mais
    recente: sem ela o regime vigente fica com 0 minuto de duracao, a guarda
    pula por `minutos <= 0` e o numero falso sai assim mesmo.
    """
    energia = [
        {"ts": "2026-09-09T11:00:00-03:00", "pl1_mmio_uw": 17000000, "no_turbo": 0, "load1": 2.0},
        {"ts": "2026-09-09T14:33:00-03:00", "pl1_mmio_uw": 15000000, "no_turbo": 0, "load1": 2.0},
    ]
    ia = [
        {
            "tipo": "embed_pagina",
            "ts": f"2026-09-09T17:3{4 + i // 60}:{i % 60:02d}Z",
            "prompt_tok_s": 60.0,
        }
        for i in range(244)
    ]
    _serie(str(tmp_path), energia, ia)

    codigo = M.main_com_argv(["--raiz", str(tmp_path)])
    saida = capsys.readouterr()
    assert codigo == 2, "densidade impossivel tem de abortar, nunca imprimir veredito"
    assert "ABORTA" in saida.err
    assert "rotulagem errada" in saida.err


def test_serie_honesta_nao_dispara_a_guarda(tmp_path, capsys):
    """Controle negativo: 10 amostras em 5 min (2/min) e fisicamente possivel e
    tem de passar pela guarda — chegando ao veredito 'sem dado' por numero de
    amostras, que e outra coisa."""
    energia = [
        {"ts": "2026-09-09T14:33:00-03:00", "pl1_mmio_uw": 15000000, "no_turbo": 0, "load1": 2.0},
    ]
    ia = [
        {"tipo": "embed_pagina", "ts": f"2026-09-09T17:3{4 + i // 2}:{(i % 2) * 30:02d}Z",
         "prompt_tok_s": 60.0}
        for i in range(10)
    ]
    _serie(str(tmp_path), energia, ia)

    codigo = M.main_com_argv(["--raiz", str(tmp_path)])
    saida = capsys.readouterr()
    assert "ABORTA" not in saida.err, saida.err
    assert "sem dado" in saida.out
    # exit 1 e o valor DESENHADO para a recusa de veredito: sem 30+ amostras em
    # dois regimes a ferramenta nao da numero, e recusar nao e sucesso.
    assert codigo == 1


# ★ SEM ESTA GUARDA O ARQUIVO SAI 0 SEM EXECUTAR UMA ASSERCAO (2026-09-10).
#
# `tools/run-qualidade-diaria:455` invoca cada teste desta pasta como
# `python3 "$teste"` — nunca `pytest arquivo.py`. Um modulo pytest sem
# `__main__` define as funcoes, nao chama nenhuma e devolve exit 0. O ledger
# grava "verde" para um teste que nao rodou, que e a forma mais silenciosa de
# uma bancada mentir: as 17 assercoes deste arquivo estavam nesse estado.
# `-p no:cacheprovider` evita deixar `.pytest_cache` no repositorio.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
