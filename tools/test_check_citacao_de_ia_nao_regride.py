#!/usr/bin/env python3
"""Testes de `tools/check-citacao-de-ia-nao-regride`, com ledgers SINTETICOS.

POR QUE SINTETICO. Hoje o ledger real nao tem nenhuma linha de citacao — a serie
so comeca depois que o titular autenticar a conta Microsoft uma vez. Um teste
que so soubesse rodar contra o repositorio de hoje exercitaria um caminho de
codigo e daria a impressao de cobrir os outros cinco.

O CASO QUE DA' NOME A ESTE ARQUIVO e' `test_ledger_parado_acusa_parada_e_nao_o_
dia_velho`: e' a prova, por mutacao, de que este gate compara com HOJE e nao com
"o ultimo registro que existir". Troque `< hoje` por uma comparacao com o ultimo
dia da serie e ele fica verde com a coleta parada ha cinco dias — que e'
exatamente o defeito que deixou `check-frescor-canal-diario` nomeando a causa
errada por cinco dias em setembro de 2026.

Descoberto pelo passo 2c de `tools/run-qualidade-diaria` (glob `tools/test_*.py`).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-citacao-de-ia-nao-regride")


def monta_ledger(raiz, linhas):
    destino = os.path.join(raiz, "data", "ops")
    os.makedirs(destino, exist_ok=True)
    caminho = os.path.join(destino, "bing_webmaster_daily.jsonl")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
    return caminho


def export(dia, ok=True):
    return {
        "tipo": "citacao_ia_export",
        "schema": "bing_webmaster_v1",
        "site": "https://wikijuridica.com.br/",
        "coletado_em": dia + "T04:10:00.000Z",
        "ok": ok,
    }


def diaria(dia, total):
    return {
        "tipo": "citacao_ia_diaria",
        "schema": "bing_webmaster_v1",
        "site": "https://wikijuridica.com.br/",
        "coletado_em": dia + "T04:10:00.000Z",
        "data": dia,
        "total_de_citacoes": total,
    }


def dias(inicio_ordinal, quantidade):
    import datetime as dt
    base = dt.date.fromordinal(inicio_ordinal)
    return [(base + dt.timedelta(days=i)).isoformat() for i in range(quantidade)]


def roda(raiz, hoje, extra=()):
    comando = [sys.executable, GATE, "--raiz", raiz, "--hoje", hoje, *extra]
    processo = subprocess.run(comando, capture_output=True, text=True, timeout=120)
    return processo.returncode, processo.stdout + processo.stderr


class CitacaoDeIA(unittest.TestCase):

    def test_serie_nunca_iniciada_reprova_e_nomeia_o_comando_do_titular(self):
        """Sem serie, o gate nao pode ficar verde — e tem de dizer o que destrava."""
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [{"tipo": "busca_diaria", "Date": "/Date(0)/"}])
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 1, saida)
            self.assertIn("serie_nunca_iniciada", saida)
            self.assertIn("collect-bing-ai-citations --login", saida)

    def test_reconhecimento_sem_export_diz_que_houve_tentativa(self):
        """"Nunca comecou" e "tentou e nao conseguiu" mandam olhar lugares diferentes."""
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [{
                "tipo": "citacao_ia_reconhecimento",
                "coletado_em": "2026-09-15T04:10:00Z",
                "motivo": "nenhuma requisicao de exportacao observada",
            }])
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 1, saida)
            self.assertIn("serie_nunca_iniciada_com_reconhecimento", saida)
            self.assertIn("2026-09-15", saida)

    def test_ledger_parado_acusa_parada_e_nao_o_dia_velho(self):
        """A REGUA E' HOJE. Cinco dias parada e' "parou ha 5 dias", nao um veredito
        sobre o quinto dia atras.

        MUTACAO QUE ESTE CASO MATA: trocar a comparacao com `hoje` por uma
        comparacao com o ultimo dia da serie deixa o gate verde aqui — e foi
        exatamente assim que `check-frescor-canal-diario` passou cinco dias
        nomeando a causa errada.
        """
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [export("2026-09-11")])
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 1, saida)
            self.assertIn("coleta_parou", saida)
            self.assertIn("ha 5 dia(s)", saida)

    def test_export_hoje_sem_contagem_passa_com_a_fase_2_declarada(self):
        """FASE 1: a coleta avanca e o teste de queda diz que esta desligado.

        Vermelho todo dia por divida conhecida e' gate que ninguem le — e ai o
        proximo defeito entra junto com o ruido.
        """
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [export("2026-09-16")])
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 0, saida)
            self.assertIn("DESLIGADO", saida)
            self.assertIn("inventar esquema", saida)

    def test_export_recusado_nao_conta_como_coleta(self):
        """`ok: false` e' tentativa que falhou; contar como avanco mascararia a queda."""
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [export("2026-09-15"), export("2026-09-16", ok=False)])
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 1, saida)
            self.assertIn("coleta_parou", saida)

    def test_serie_curta_desliga_o_teste_de_queda_e_diz_por_que(self):
        """Limiar sem serie e' ruido inventado. O gate declara em vez de adivinhar."""
        with tempfile.TemporaryDirectory() as tmp:
            serie = dias(739000, 4)
            linhas = [export(serie[-1])] + [diaria(d, 100) for d in serie]
            monta_ledger(tmp, linhas)
            codigo, saida = roda(tmp, serie[-1])
            self.assertEqual(codigo, 0, saida)
            self.assertIn("DESLIGADO", saida)
            self.assertIn("serie curta demais", saida)

    def test_queda_brutal_reprova(self):
        """O caso que o gate existe para pegar — no ultimo dia FECHADO.

        A queda vai em `serie[-2]` de proposito: `serie[-1]` e' o dia corrente,
        que e' parcial e por desenho nao e' julgado. Escrever a queda no dia
        corrente testaria o caminho errado e ficaria verde, que foi exatamente o
        que aconteceu na primeira versao deste caso.
        """
        with tempfile.TemporaryDirectory() as tmp:
            serie = dias(739000, 16)
            valores = [1000 + (i % 3) * 7 for i in range(14)] + [120, 1000]
            linhas = [export(serie[-1])]
            linhas += [diaria(d, v) for d, v in zip(serie, valores)]
            monta_ledger(tmp, linhas)
            codigo, saida = roda(tmp, serie[-1])
            self.assertEqual(codigo, 1, saida)
            self.assertIn("queda_alem_do_ruido", saida)
            self.assertIn("REVERTE-SE A MUDANCA", saida)
            self.assertIn(serie[-2], saida)

    def test_oscilacao_normal_nao_reprova(self):
        """Controle negativo: gate que acusa ruido vira gate que ninguem le.

        O piso de dispersao relativo (5% da mediana) existe por isto: numa serie
        quase plana o MAD tende a zero e uma variacao de uma unidade viraria
        vermelho — o instrumento mediria a propria estabilidade como se fosse
        sensibilidade.
        """
        with tempfile.TemporaryDirectory() as tmp:
            serie = dias(739000, 16)
            valores = [1000, 1010, 995, 1005, 990, 1020, 1000, 1008, 992, 1015,
                       1001, 999, 1007, 993, 1011, 970]
            linhas = [export(serie[-1])]
            linhas += [diaria(d, v) for d, v in zip(serie, valores)]
            monta_ledger(tmp, linhas)
            codigo, saida = roda(tmp, serie[-1])
            self.assertEqual(codigo, 0, saida)
            self.assertIn("veredito            : VERDE", saida)

    def test_dia_corrente_parcial_nao_e_julgado(self):
        """O dia de hoje e' PARCIAL: julga-lo acusaria queda todo dia, ao meio-dia.

        Aqui a serie e' estavel em ~1000 e o dia CORRENTE tem 3. Se o gate
        julgasse o dia corrente, reprovaria; ele julga o ultimo dia FECHADO.
        """
        with tempfile.TemporaryDirectory() as tmp:
            serie = dias(739000, 16)
            linhas = [export(serie[-1])]
            linhas += [diaria(d, 1000) for d in serie[:-1]]
            linhas += [diaria(serie[-1], 3)]
            monta_ledger(tmp, linhas)
            codigo, saida = roda(tmp, serie[-1])
            self.assertEqual(codigo, 0, saida)
            self.assertIn(serie[-2], saida)

    def test_ultima_linha_do_dia_vence(self):
        """O Bing REVISA numeros de dias recentes, e a revisao e' informacao."""
        with tempfile.TemporaryDirectory() as tmp:
            serie = dias(739000, 16)
            linhas = [export(serie[-1])]
            linhas += [diaria(d, 1000) for d in serie]
            # revisao do ultimo dia FECHADO, para baixo e alem do ruido
            linhas += [diaria(serie[-2], 50)]
            monta_ledger(tmp, linhas)
            codigo, saida = roda(tmp, serie[-1])
            self.assertEqual(codigo, 1, saida)
            self.assertIn("queda_alem_do_ruido", saida)

    def test_ledger_ilegivel_e_exit_2_nunca_veredito(self):
        """"Nao consegui medir" nunca pode virar "esta tudo certo" nem "esta ruim"."""
        with tempfile.TemporaryDirectory() as tmp:
            # Um DIRETORIO no lugar do arquivo faz a leitura levantar OSError.
            os.makedirs(os.path.join(tmp, "data", "ops", "bing_webmaster_daily.jsonl"))
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NAO MEDIU", saida)

    def test_hoje_invalido_e_exit_2(self):
        """Argumento invalido e' defeito de invocacao, nao veredito sobre o portal."""
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [export("2026-09-16")])
            codigo, saida = roda(tmp, "16/09/2026")
            self.assertEqual(codigo, 2, saida)

    def test_json_sai_legivel_por_maquina(self):
        """O painel de alcance le este relatorio; formato quebrado o cega."""
        with tempfile.TemporaryDirectory() as tmp:
            monta_ledger(tmp, [export("2026-09-16")])
            codigo, saida = roda(tmp, "2026-09-16", extra=["--json"])
            self.assertEqual(codigo, 0, saida)
            dados = json.loads(saida)
            self.assertEqual(dados["hoje"], "2026-09-16")
            self.assertEqual(dados["exports_ok"], 1)
            self.assertEqual(dados["queda"]["estado"], "desligado")


if __name__ == "__main__":
    unittest.main(verbosity=2)
