#!/usr/bin/env python3
"""Testes de tools/measure-tunnel-gaps — a derivação pela série de saúde.

POR QUE ESTE ARQUIVO EXISTE. Em 2026-09-10 a unit
`wikijuridica-tunnel-gaps.service` estava `failed` todo dia com exit 3
("SEM DADOS"), porque a frota está estável e frota estável não gera evento
`Registered`/`Unregistered` no journal. O exit 3 foi escrito de propósito em
2026-09-03 para matar um falso-verde que já enganou uma decisão de engenharia
em 2026-08-13 — e ele continua certo enquanto a ÚNICA fonte for a reconstrução
por evento.

A saída não é afrouxar o exit 3: é usar a segunda fonte que a ferramenta já lê
para refutar janela falsa (`data/ops/tunnel_health.jsonl`). Quando essa fonte
POSITIVA cobre a janela inteira, ela responde sozinha. O exit 3 passa a
significar o que sempre quis dizer: faltam as DUAS.

Estes testes exercem exatamente a fronteira entre "derivou" e "não há base",
porque é ali que um falso-verde voltaria a nascer.

Rodar:
    python3 tools/test_measure_tunnel_gaps.py
"""
from __future__ import annotations

import datetime
import importlib.util
import pathlib
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "measure-tunnel-gaps"


def carrega():
    spec = importlib.util.spec_from_loader(
        "measure_tunnel_gaps",
        importlib.machinery.SourceFileLoader("measure_tunnel_gaps", str(FERRAMENTA)),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


import importlib.machinery  # noqa: E402  (usado por carrega)

MOD = carrega()

FIM = datetime.datetime(2026, 9, 10, 12, 0, 0, tzinfo=datetime.timezone.utc)
INICIO = FIM - datetime.timedelta(hours=48)


def serie(passo_s, ha=4, inicio=None, fim=None):
    """Amostras de saúde a cada `passo_s` segundos, com `ha_connections`=ha.

    `ha` pode ser um callable(instante) para variar ao longo da janela.
    """
    inicio = inicio or INICIO
    fim = fim or FIM
    saida = []
    quando = inicio
    while quando <= fim:
        valor = ha(quando) if callable(ha) else ha
        saida.append((quando, valor, 5))
        quando += datetime.timedelta(seconds=passo_s)
    return saida


class TesteDerivacaoPelaSaude(unittest.TestCase):
    def test_serie_completa_e_saudavel_cobre_a_janela(self):
        coberta, sem_conexao, amostras, maior, motivo = MOD.disponibilidade_pela_saude(
            serie(34), INICIO, FIM)
        self.assertTrue(coberta, motivo)
        self.assertEqual(sem_conexao, 0.0)
        self.assertGreater(amostras, 5000)
        self.assertLessEqual(maior, MOD.TOLERANCIA_LACUNA_S)
        self.assertEqual(motivo, "")

    def test_lacuna_acima_da_tolerancia_nao_cobre(self):
        """O buraco é o caso perigoso: cobertura parcial não prova nada, e sem
        esta recusa o sondador parado viraria 100% de disponibilidade."""
        amostras = serie(34)
        buraco_inicio = len(amostras) // 2
        buraco_fim = buraco_inicio + int(MOD.TOLERANCIA_LACUNA_S // 34) + 5
        furada = amostras[:buraco_inicio] + amostras[buraco_fim:]
        coberta, _sem, _n, maior, motivo = MOD.disponibilidade_pela_saude(
            furada, INICIO, FIM)
        self.assertFalse(coberta)
        self.assertGreater(maior, MOD.TOLERANCIA_LACUNA_S)
        self.assertIn("lacuna", motivo)

    def test_serie_vazia_nao_cobre(self):
        coberta, _sem, amostras, maior, motivo = MOD.disponibilidade_pela_saude(
            [], INICIO, FIM)
        self.assertFalse(coberta)
        self.assertEqual(amostras, 0)
        self.assertIsNone(maior)
        self.assertIn("nenhuma amostra", motivo)

    def test_borda_descoberta_nao_cobre(self):
        """Amostras que param cedo cobrem o meio e deixam o fim no escuro —
        exatamente o que aconteceria com o sondador morto há uma hora."""
        parcial = serie(34, fim=FIM - datetime.timedelta(hours=2))
        coberta, _sem, _n, maior, motivo = MOD.disponibilidade_pela_saude(
            parcial, INICIO, FIM)
        self.assertFalse(coberta)
        self.assertGreater(maior, MOD.TOLERANCIA_LACUNA_S)
        self.assertIn("lacuna", motivo)

    def test_queda_real_vira_segundos_sem_conexao(self):
        """Cobertura não é sinônimo de saúde: com ha_connections=0 numa faixa,
        a derivação tem de DEVOLVER o buraco, não arredondar para 100%."""
        queda_ini = FIM - datetime.timedelta(hours=3)
        queda_fim = FIM - datetime.timedelta(hours=2)

        def ha(quando):
            return 0 if queda_ini <= quando < queda_fim else 4

        coberta, sem_conexao, _n, _maior, motivo = MOD.disponibilidade_pela_saude(
            serie(34, ha=ha), INICIO, FIM)
        self.assertTrue(coberta, motivo)
        # Uma hora de amostras com ha=0, integrada como função-degrau.
        self.assertAlmostEqual(sem_conexao, 3600, delta=70)

    def test_tolerancia_e_a_medida_do_acervo(self):
        """A tolerância não é número redondo escolhido a gosto: a série real de
        48 h tem lacuna máxima de 40,2 s. Se alguém a apertar abaixo disso, a
        cobertura real do host passa a reprovar."""
        self.assertGreater(MOD.TOLERANCIA_LACUNA_S, 40.2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
