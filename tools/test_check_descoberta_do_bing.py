#!/usr/bin/env python3
"""Testes do gate de canais de descoberta do Bing.

O risco desta ferramenta é dizer "está tudo bem" quando não está: ela existe
justamente para autorizar alguém a NÃO perseguir a mediana alta de
`check-time-to-first-crawl`. Um verde frouxo aqui esconderia robots bloqueando,
borda desafiando o crawler ou o índice do Bing encolhendo.

Por isso cada canal tem teste nos dois sentidos — o saudável que passa e a
quebra que reprova — sobre fixtures sintéticas, não sobre o dado vivo (que muda
todo dia e faria o teste medir o Bing em vez de medir o gate).
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import types
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "check-descoberta-do-bing"

# O CARREGAMENTO NÃO PASSA POR BYTECODE, e isso me custou um falso verde hoje.
#
# `tools/test_bytecode_obsoleto_cega_teste_de_ferramenta.py` já diagnosticou o
# defeito em 2026-09-05: as ferramentas de `tools/` não têm extensão `.py`, o
# CPython grava `.pyc` para elas assim mesmo, e `SourceFileLoader` revalida esse
# bytecode por (mtime em segundos, tamanho em bytes). Uma mutação que PERMUTA
# — `min` por `max`, `2 *` por `4 *` — preserva o tamanho; caindo no mesmo
# segundo, o par bate e o loader executa o bytecode ANTIGO.
#
# A defesa que aquele teste trava é `PYTHONDONTWRITEBYTECODE=1` no runner
# (`tools/run-qualidade-diaria:455`), e ela está certa — para a SUÍTE. Ela não
# alcança quem roda o teste à mão, que é exatamente o que se faz durante uma
# prova por mutação. Em 2026-09-10 esta bancada devolveu OK, três mutações de
# mesmo tamanho e, ao restaurar o original, FAILED — com o disco byte a byte
# igual ao que tinha passado. O `.pyc` de `tools/__pycache__/` respondia.
#
# `PYTHONDONTWRITEBYTECODE` também não bastaria sozinha aqui: ela impede
# GRAVAR, e um `.pyc` obsoleto que já exista continua sendo LIDO. Compilar a
# fonte a cada carga fecha as duas pontas e custa 2 ms.
sys.dont_write_bytecode = True


def carrega():
    modulo = types.ModuleType("gate_descoberta")
    modulo.__file__ = str(ALVO)
    codigo = compile(ALVO.read_text(encoding="utf-8"), str(ALVO), "exec")
    exec(codigo, modulo.__dict__)
    return modulo


def escreve(raiz: pathlib.Path, rel: str, registros: list[dict]) -> None:
    alvo = raiz / rel
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros),
        encoding="utf-8")


def relatorio(data: str, in_index: int, **ajustes) -> dict:
    base = {"Date": data, "tipo": "rastreio_diario", "InIndex": in_index,
            "CrawledPages": 497, "BlockedByRobotsTxt": 0, "Code4xx": 0,
            "Code5xx": 0, "AllOtherCodes": 970}
    base.update(ajustes)
    return base


class TestBingWebmaster(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_indice_crescendo_passa(self):
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-09-01", 2653), relatorio("2026-09-02", 2939),
            relatorio("2026-09-03", 3179), relatorio("2026-09-04", 3468)])
        self.assertEqual(self.gate.mede_robots_e_indice(self.raiz)["problemas"], [])

    def test_indice_encolhendo_reprova(self):
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-09-01", 3468), relatorio("2026-09-02", 3100),
            relatorio("2026-09-03", 2900), relatorio("2026-09-04", 2700)])
        problemas = self.gate.mede_robots_e_indice(self.raiz)["problemas"]
        self.assertEqual(len(problemas), 1)
        self.assertIn("ENCOLHEU", problemas[0])

    def test_robots_bloqueando_reprova(self):
        escreve(self.raiz, self.gate.BING_WEBMASTER,
                [relatorio("2026-09-04", 3468, BlockedByRobotsTxt=812)])
        problemas = self.gate.mede_robots_e_indice(self.raiz)["problemas"]
        self.assertTrue(any("robots bloqueia 812" in p for p in problemas), problemas)

    def test_4xx_reprova(self):
        escreve(self.raiz, self.gate.BING_WEBMASTER,
                [relatorio("2026-09-04", 3468, Code4xx=57)])
        problemas = self.gate.mede_robots_e_indice(self.raiz)["problemas"]
        self.assertTrue(any("Code4xx=57" in p for p in problemas), problemas)

    # O caso `test_5xx_do_bing_reprova_e_diz_que_e_estoque` viveu aqui até
    # 2026-09-10 e travava a regra "nível de estoque > 0 reprova". Ele não se
    # apaga em silêncio: o motivo dele era bom (5xx é mais grave que 4xx, e o
    # campo estava sendo lido sem ser avaliado), a régua é que estava errada. O
    # que o derrubou foi medição própria, não conveniência: as 9 gêmeas
    # `/x/index.md` que o vermelho mandava reentregar responderam 200 nas nove,
    # sondadas com a sonda interna; a série do estoque sobe e DESCE sozinha
    # (0..1, 2, 9, 9, 7, 11, 10, 10) sem que nada nosso a toque; e `InIndex`
    # cresce todo dia na mesma janela. Gate que reprova por número que nada
    # drena fica vermelho para sempre, e vermelho permanente ensina a ignorar o
    # gate. Os quatro casos abaixo travam a régua que substituiu aquela: o NÍVEL
    # se relata, a ENTRADA nova é que reprova.

    def test_5xx_estoque_parado_nao_reprova(self):
        """A série real de 2026-09-05..09 — o estoque oscila e termina em queda.

        Este é o caso que o `if` antigo reprovava e que a medição inocentou.
        Mutação que o mata: fazer o nível voltar a reprovar (`if Code5xx:`).
        """
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-09-05", 4022, Code5xx=9),
            relatorio("2026-09-06", 4022, Code5xx=7),
            relatorio("2026-09-07", 4318, Code5xx=11),
            relatorio("2026-09-08", 4667, Code5xx=10),
            relatorio("2026-09-09", 5049, Code5xx=10)])
        estado = self.gate.mede_robots_e_indice(self.raiz)
        self.assertEqual(estado["problemas"], [])
        # O número não some do relatório: ele vira dado nomeado e datado.
        self.assertEqual(estado["code_5xx"], 10)
        self.assertEqual(estado["code_5xx_janela"], [9, 7, 11, 10, 10])
        self.assertEqual(estado["code_5xx_entrada"], -1)
        # amplitude 3 (10 contra piso 7) cabe no dobro da tolerancia: oscilacao
        # do estoque nao e rampa.
        self.assertEqual(estado["code_5xx_amplitude"], 3)

    def test_5xx_entrada_nova_acima_da_tolerancia_reprova(self):
        """O salto real de 2026-09-04, no dia seguinte às ~16 h com o Go fora.

        Com 1.039 respostas 503 na origem em 09-02, o campo foi de 2 para 9.
        É o único uso honesto deste campo: ele enxerga o rastreio do Bing pelos
        olhos do Bing, e portanto pega 5xx servido a bingbot que a borda não
        classificou como verificado.
        """
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-08-31", 2319, Code5xx=1),
            relatorio("2026-09-01", 2653, Code5xx=1),
            relatorio("2026-09-02", 2939, Code5xx=1),
            relatorio("2026-09-03", 3179, Code5xx=2),
            relatorio("2026-09-04", 3468, Code5xx=9)])
        problemas = self.gate.mede_robots_e_indice(self.raiz)["problemas"]
        self.assertTrue(any("entraram 7 URL(s) NOVAS" in p for p in problemas),
                        problemas)
        # A mensagem manda olhar o dado NOSSO, não reentregar URL ao Bing.
        self.assertTrue(any("data/ops/access/" in p for p in problemas), problemas)

    def test_5xx_blip_dentro_da_tolerancia_nao_reprova(self):
        """2026-09-07 subiu +2 sobre o máximo anterior e não é indisponibilidade.

        `mede_borda` já decidiu que blip de túnel não reprova ("o gate acusa
        indisponibilidade, não ruído de túnel"); deixar o estoque reprovar em +2
        faria o MESMO blip reprovar por outra porta. Mutação que o mata: baixar
        a tolerância para 0, ou comparar contra o `min` da janela em vez do
        `max`.
        """
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-09-04", 3468, Code5xx=9),
            relatorio("2026-09-05", 4022, Code5xx=9),
            relatorio("2026-09-06", 4022, Code5xx=7),
            relatorio("2026-09-07", 4318, Code5xx=11)])
        estado = self.gate.mede_robots_e_indice(self.raiz)
        self.assertEqual(estado["problemas"], [])
        self.assertEqual(estado["code_5xx_entrada"], 2)
        # AMPLITUDE 4 = exatamente o dobro da tolerancia, a borda do segundo
        # braco: dois blips de +2 em dias diferentes cabem, um terceiro degrau
        # na mesma direcao nao cabe. Se este numero mudar, o segundo braco
        # passou a reprovar ruido de tunel.
        self.assertEqual(estado["code_5xx_amplitude"], 4)

    def test_5xx_em_rampa_reprova_mesmo_sem_degrau(self):
        """A rampa que o primeiro braço nao ve, e a borda tambem nao.

        10, 12, 14, 16, 18: entrada de +2 TODO dia, nunca acima da tolerancia,
        e o estoque quase dobra na janela. Do lado da borda, 2 erros em ~440
        requisicoes diarias de bingbot dao 0,45% — sob o teto de 2% de
        `mede_borda`. Sem o segundo braco esse dano nao aparece em instrumento
        nenhum, e o unico aviso restante seria `InIndex` encolhendo, que e
        indicador de resultado e chega tarde.

        Mutacao que o mata: apagar o ramo `elif amplitude_5xx > ...`, ou afrouxar
        o multiplicador para 4x a tolerancia.
        """
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            relatorio("2026-09-05", 4022, Code5xx=10),
            relatorio("2026-09-06", 4300, Code5xx=12),
            relatorio("2026-09-07", 4600, Code5xx=14),
            relatorio("2026-09-08", 4900, Code5xx=16),
            relatorio("2026-09-09", 5200, Code5xx=18)])
        estado = self.gate.mede_robots_e_indice(self.raiz)
        problemas = estado["problemas"]
        self.assertTrue(any("RAMPA" in p for p in problemas), problemas)
        # O primeiro braco NAO disparou — e essa e a razao de o segundo existir.
        self.assertFalse(any("URL(s) NOVAS" in p for p in problemas), problemas)
        self.assertEqual(estado["code_5xx_entrada"], 2)
        self.assertEqual(estado["code_5xx_amplitude"], 8)

    def test_5xx_primeiro_dia_da_serie_nao_inventa_entrada(self):
        """Sem dia anterior não há entrada a calcular — e ausência de base de
        comparação nunca vira acusação."""
        escreve(self.raiz, self.gate.BING_WEBMASTER,
                [relatorio("2026-09-09", 5049, Code5xx=10)])
        estado = self.gate.mede_robots_e_indice(self.raiz)
        self.assertEqual(estado["problemas"], [])
        self.assertIsNone(estado["code_5xx_entrada"])
        self.assertEqual(estado["code_5xx"], 10)

    def test_5xx_zerado_nao_inventa_problema(self):
        escreve(self.raiz, self.gate.BING_WEBMASTER,
                [relatorio("2026-09-09", 5049, Code5xx=0)])
        self.assertEqual(self.gate.mede_robots_e_indice(self.raiz)["problemas"], [])

    def test_serie_ausente_nao_finge_saude(self):
        estado = self.gate.mede_robots_e_indice(self.raiz)
        self.assertFalse(estado["disponivel"])
        self.assertTrue(estado["problemas"])

    def test_linhas_de_busca_nao_contaminam_o_rastreio(self):
        """O ledger mistura `busca_diaria` e `rastreio_diario` no mesmo arquivo."""
        escreve(self.raiz, self.gate.BING_WEBMASTER, [
            {"Date": "2026-09-04", "tipo": "busca_diaria", "Impressions": 1318,
             "Clicks": 25},
            relatorio("2026-09-04", 3468)])
        estado = self.gate.mede_robots_e_indice(self.raiz)
        self.assertEqual(estado["in_index"], 3468)
        self.assertEqual(estado["problemas"], [])


class TestBorda(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def borda(self, pares: list[tuple[int, int]], agente: str = "bingbot"):
        escreve(self.raiz, self.gate.EDGE_STATUS, [
            {"agent_key": agente, "edge_response_status": s,
             "requests_estimated": n, "date": "2026-09-04"} for s, n in pares])

    def test_borda_entregando_passa(self):
        self.borda([(200, 6336), (301, 80), (404, 31), (503, 9)])
        estado = self.gate.mede_borda(self.raiz)
        self.assertEqual(estado["problemas"], [])
        self.assertLess(estado["recusa_pct"], 1.0)

    def test_challenge_reprova(self):
        """403 em massa é a borda comendo o orçamento de rastreio do bot."""
        self.borda([(200, 5000), (403, 3000)])
        problemas = self.gate.mede_borda(self.raiz)["problemas"]
        self.assertTrue(any("borda recusou" in p for p in problemas), problemas)
        # A mensagem nomeia o DIA: sem isso, quem lê o vermelho não sabe onde
        # procurar no log, e foi assim que a rajada de 2026-09-02 ficou anônima.
        self.assertTrue(any("2026-09-04" in p for p in problemas), problemas)

    def test_429_conta_como_recusa(self):
        self.borda([(200, 1000), (429, 500)])
        self.assertTrue(self.gate.mede_borda(self.raiz)["problemas"])

    def test_redirecionamento_nao_conta_como_recusa(self):
        """3xx é decisão nossa de rota, não recusa ao crawler."""
        self.borda([(200, 100), (301, 900)])
        self.assertEqual(self.gate.mede_borda(self.raiz)["problemas"], [])

    def dias(self, mapa: dict[str, list[tuple[int, int]]], agente: str = "bingbot"):
        """Fixture multi-dia: {data: [(status, n), ...]}."""
        escreve(self.raiz, self.gate.EDGE_STATUS, [
            {"agent_key": agente, "edge_response_status": s,
             "requests_estimated": n, "date": dia}
            for dia, pares in mapa.items() for s, n in pares])

    def test_rajada_de_um_dia_nao_se_dilui_no_acumulado(self):
        """O defeito que custou o P0 de 2026-09-10, reproduzido em fixture.

        Números do dado real: em 2026-09-02 o bingbot levou 10 erros em 474
        requisições — 2,11% do dia, acima do teto. Somados aos outros seis dias
        limpos da janela, os mesmos 10 erros viram 0,32% (10 de 3.174) e passam. Se este teste
        ficar verde com o teto aplicado ao acumulado, o gate voltou a ser cego.
        """
        limpo = [(200, 450)]
        self.dias({"2026-09-01": limpo,
                   "2026-09-02": [(200, 464), (503, 9), (520, 1)],
                   "2026-09-03": limpo, "2026-09-04": limpo,
                   "2026-09-05": limpo, "2026-09-06": limpo,
                   "2026-09-07": limpo})
        estado = self.gate.mede_borda(self.raiz)
        self.assertEqual(estado["dias_acima_do_teto"], ["2026-09-02"])
        self.assertTrue(any("2026-09-02" in p and "2.11%" in p
                            for p in estado["problemas"]), estado["problemas"])
        # E a prova de que o acumulado NÃO acusaria: a mesma janela dá 0,35%.
        self.assertLess(estado["recusa_pct"], self.gate.TETO_ERRO_BORDA_PCT)

    def test_dia_ruim_que_saiu_da_janela_para_de_reprovar(self):
        """Gate que nunca solta o passado vira vermelho permanente, e vermelho
        permanente ninguém lê. Passada a janela com a borda sadia, ele limpa."""
        limpo = [(200, 450)]
        mapa = {"2026-09-02": [(200, 464), (503, 9), (520, 1)]}
        for dia in range(3, 11):
            mapa[f"2026-09-{dia:02d}"] = limpo
        self.dias(mapa)
        estado = self.gate.mede_borda(self.raiz)
        self.assertEqual(estado["dias_acima_do_teto"], [])
        self.assertEqual(estado["problemas"], [])
        self.assertNotIn("2026-09-02", estado["janela"])
        self.assertEqual(len(estado["janela"]), self.gate.JANELA_BORDA)

    def test_blip_isolado_de_tunel_nao_vira_alarme(self):
        """2026-09-04 (2 de 530) e 2026-09-06 (2 de 502) são queda pontual de
        túnel: 0,43% e 0,49% do dia. Acusá-los seria gate histérico."""
        self.dias({"2026-09-04": [(200, 462), (530, 2)],
                   "2026-09-06": [(200, 405), (502, 2)]})
        estado = self.gate.mede_borda(self.raiz)
        self.assertEqual(estado["problemas"], [])

    def test_registro_sem_data_nao_e_descartado_em_silencio(self):
        """Sem `date` não há janela, e janela é o que faz o teto valer. Um
        schema que pare de emitir o campo tem de gritar, não emudecer."""
        escreve(self.raiz, self.gate.EDGE_STATUS, [
            {"agent_key": "bingbot", "edge_response_status": 200,
             "requests_estimated": 400, "date": "2026-09-09"},
            {"agent_key": "bingbot", "edge_response_status": 503,
             "requests_estimated": 40}])
        problemas = self.gate.mede_borda(self.raiz)["problemas"]
        self.assertTrue(any("sem campo `date`" in p for p in problemas), problemas)

    def test_outro_bot_nao_entra_na_conta(self):
        self.borda([(403, 9999)], agente="semrushbot")
        estado = self.gate.mede_borda(self.raiz)
        self.assertFalse(estado["disponivel"])


class TestIndexNow(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def submissoes(self, registros):
        escreve(self.raiz, self.gate.INDEXNOW, registros)

    def test_submissoes_aceitas_passam(self):
        self.submissoes([{"submitted_at": "2026-09-05T08:33:49Z", "url_count": 250,
                          "http_status": 200, "success": True,
                          "ownership_proof_verified_over_http": True}])
        self.assertEqual(self.gate.mede_indexnow(self.raiz)["problemas"], [])

    def test_submissao_recusada_reprova(self):
        self.submissoes([{"submitted_at": "2026-09-05T08:33:49Z", "url_count": 250,
                          "http_status": 422, "success": False,
                          "ownership_proof_verified_over_http": True}])
        problemas = self.gate.mede_indexnow(self.raiz)["problemas"]
        self.assertTrue(any("falharam" in p for p in problemas), problemas)

    def test_sem_prova_de_posse_reprova(self):
        """Sem a prova por HTTP, o endpoint aceita e o Bing ignora."""
        self.submissoes([{"submitted_at": "2026-09-05T08:33:49Z", "url_count": 250,
                          "http_status": 200, "success": True,
                          "ownership_proof_verified_over_http": False}])
        problemas = self.gate.mede_indexnow(self.raiz)["problemas"]
        self.assertTrue(any("prova de posse" in p for p in problemas), problemas)


class TestJsonlInvalido(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()

    def test_linha_corrompida_reprova_em_vez_de_ignorar(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            alvo = raiz / self.gate.BING_WEBMASTER
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text('{"Date": "2026-09-04"}\nnao-e-json\n', encoding="utf-8")
            with self.assertRaises(ValueError) as capturado:
                self.gate.mede_robots_e_indice(raiz)
            self.assertIn("linha 2", str(capturado.exception))


if __name__ == "__main__":
    unittest.main()
