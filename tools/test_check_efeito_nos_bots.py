#!/usr/bin/env python3
"""Testes de tools/check-efeito-nos-bots — o veredito com lag sobre o Googlebot.

POR QUE ESTE TESTE EXISTE: até 2026-09-01 o script só tinha `return 0`, e ficou
verde durante a queda inteira do rastreio (13,9 páginas/dia por 15 dias). O
veredito que entrou tem três saídas — PASSA, REPROVA, INCONCLUSIVO — e o log
real de origem, em 2026-09-01, só consegue produzir duas delas: toda janela PRÉ
coberta contém a rajada de 12/08 (1.206 páginas num dia), então nenhum
`--desde` real dá PASSA hoje. O ramo PASSA se prova aqui, com contadores
construídos, porque o contrato exige o gate REPROVANDO no caso ruim E passando
no caso bom — e um ramo que nunca rodou é um ramo que pode estar quebrado.

Os contadores construídos NÃO são dado de produção: são a entrada mínima que
distingue cada ramo, e o teste diz em cada caso qual regra está exercitando.

Rodar:
    python3 tools/test_check_efeito_nos_bots.py
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import os
import unittest
from datetime import date, timedelta

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-efeito-nos-bots")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_efeito_nos_bots_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


mod = _load_module()

REFERENCIA = date(2026, 8, 18)
HOJE_VENCIDO = REFERENCIA + timedelta(days=mod.LAG_DIAS)      # 14 dias completos
FAIXAS = ["faixa-de-mentira-so-para-nao-ser-vazia"]           # so o len() importa aqui


def _janelas(pre_por_dia, pos_por_dia):
    """Monta (por_dia, cobertura) a partir de um dicionario por janela:
    {classe: n} repetido em cada um dos 14 dias da janela."""
    por_dia = {}
    cobertura = set()
    for desloc in range(1, mod.JANELA_DIAS + 1):
        dia = REFERENCIA - timedelta(days=desloc)
        por_dia[dia] = dict(pre_por_dia)
        cobertura.add(dia)
    for desloc in range(mod.JANELA_DIAS):
        dia = REFERENCIA + timedelta(days=desloc)
        por_dia[dia] = dict(pos_por_dia)
        cobertura.add(dia)
    return por_dia, cobertura


def _roda(hoje, por_dia, cobertura, faixas=FAIXAS, referencia=REFERENCIA):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        codigo = mod.veredito_googlebot(referencia, "--desde", hoje, por_dia, cobertura,
                                        faixas, 0, "12/Aug/2026:00:00:01")
    return codigo, saida.getvalue()


class VereditoComLag(unittest.TestCase):
    def test_passa_quando_razao_cai_e_paginas_dia_sobe(self):
        # PRE: 10 mapas / 5 paginas por dia (razao 2,0); POS: 5 mapas / 20 paginas
        # (razao 0,25). As duas condicoes melhoram: e o unico caso que passa.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 2, "mapa": 3, "pagina": 20})
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("VEREDITO: PASSA", texto)
        self.assertNotIn("INCONCLUSIVO", texto)

    def test_reprova_quando_razao_nao_cai(self):
        # paginas/dia sobe (5 -> 20) mas o mapa sobe junto e a razao fica igual
        # (2,0 -> 2,0): orcamento cresceu, nao foi redirecionado. Exit 1.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 16, "mapa": 24, "pagina": 20})
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 1, texto)
        self.assertIn("VEREDITO: REPROVA", texto)
        self.assertIn("mapa/pagina NAO caiu", texto)
        self.assertNotIn("paginas/dia NAO subiu", texto)

    def test_reprova_quando_paginas_dia_nao_sobe(self):
        # A razao cai (2,0 -> 0,6) porque o sitemap deixou de ser pedido, mas
        # paginas/dia tambem caiu (5 -> 5, igual nao e subir). E o caso que a
        # regra "as duas juntas" existe para apanhar.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 1, "mapa": 2, "pagina": 5})
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 1, texto)
        self.assertIn("paginas/dia NAO subiu", texto)
        self.assertNotIn("mapa/pagina NAO caiu", texto)

    def test_inconclusivo_antes_do_lag_mesmo_com_dado_ruim(self):
        # Mesmo dado que reprovaria acima, mas hoje e o 13o dia: sem veredito,
        # exit 0, e a palavra INCONCLUSIVO impressa — nunca PASSA.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 16, "mapa": 24, "pagina": 20})
        codigo, texto = _roda(HOJE_VENCIDO - timedelta(days=1), por_dia, cobertura)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("INCONCLUSIVO", texto)
        self.assertIn("faltam 1 dia", texto)
        self.assertNotIn("VEREDITO", texto)

    def test_pos_abaixo_do_n_minimo_com_baseline_valida_e_colapso_nao_inconclusivo(self):
        # ★ ESTE TESTE FIXAVA O BURACO (refutacao adversarial de 2026-09-01). Ele
        #   se chamava test_inconclusivo_abaixo_do_n_minimo e exigia exit 0 com
        #   baseline de 210 requisicoes e POS de 84: "amostra pequena nao decide".
        #   Mas POS pequeno com baseline valida NAO e amostra pequena — e o crawler
        #   SUMINDO, que e o unico evento que este gate existe para acusar. Quanto
        #   pior a queda, mais "inconclusivo" ele ficava. N_MINIMO vale para a
        #   baseline; o POS abaixo dele, com baseline acima, REPROVA.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 1, "mapa": 1, "pagina": 4})
        self.assertLess(6 * mod.JANELA_DIAS, mod.N_MINIMO)
        self.assertGreaterEqual(15 * mod.JANELA_DIAS, mod.N_MINIMO)
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 1, texto)
        self.assertIn("REPROVA", texto)
        self.assertIn("sumiu", texto)
        self.assertNotIn("INCONCLUSIVO", texto)

    def test_inconclusivo_quando_a_baseline_e_pequena(self):
        # A regra de amostra pequena continua valendo — para a BASELINE. Sem uma
        # baseline de N_MINIMO requisicoes nao ha contra o que comparar.
        por_dia, cobertura = _janelas({"robots": 1, "mapa": 1, "pagina": 3},
                                      {"robots": 1, "mapa": 1, "pagina": 4})
        self.assertLess(5 * mod.JANELA_DIAS, mod.N_MINIMO)
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("INCONCLUSIVO", texto)
        self.assertIn("baseline PRE", texto)

    def test_inconclusivo_sem_dia_coberto_na_janela_pre(self):
        # O caso real de --desde 2026-08-10 em 2026-09-01: a retencao do log
        # comeca em 11/08 e a janela PRE (27/07..09/08) nao tem dia nenhum.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 2, "mapa": 3, "pagina": 20})
        cobertura = {d for d in cobertura if d >= REFERENCIA}
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("janela PRE com 0 dia(s) completo(s) coberto(s)", texto)
        self.assertNotIn("VEREDITO", texto)

    def test_inconclusivo_sem_faixa_oficial(self):
        # Sem faixa nao ha autenticacao, e veredito sobre UA solto e veredito
        # sobre scanner. Tem de dizer isso, nao devolver PASSA por zero linhas.
        por_dia, cobertura = _janelas({"robots": 4, "mapa": 6, "pagina": 5},
                                      {"robots": 2, "mapa": 3, "pagina": 20})
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura, faixas=[])
        self.assertEqual(codigo, 0, texto)
        self.assertIn("INCONCLUSIVO", texto)
        self.assertIn("googlebot.json", texto)

    def test_inconclusivo_sem_referencia(self):
        codigo, texto = _roda(HOJE_VENCIDO, {}, set(), referencia=None)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("INCONCLUSIVO", texto)
        self.assertIn("--desde", texto)

    def test_paginas_dia_divide_pelos_dias_cobertos_nao_por_14(self):
        # Janela PRE com 6 dias cobertos (o caso real de --desde 2026-08-18):
        # 6 x 5 = 30 paginas em 6 dias sao 5,0/dia, nao 30/14 = 2,1/dia.
        por_dia, cobertura = _janelas({"robots": 10, "mapa": 10, "pagina": 5},
                                      {"robots": 2, "mapa": 3, "pagina": 20})
        cobertura = {d for d in cobertura if d >= REFERENCIA - timedelta(days=6)}
        codigo, texto = _roda(HOJE_VENCIDO, por_dia, cobertura)
        self.assertEqual(codigo, 0, texto)
        linha_pre = next(l for l in texto.splitlines() if l.startswith("pre "))
        self.assertIn("6/14", linha_pre)
        self.assertTrue(linha_pre.rstrip().endswith("5.0"), linha_pre)


class ClasseDoCaminho(unittest.TestCase):
    def test_classes(self):
        casos = {
            "/robots.txt": "robots",
            "/sitemap.xml": "mapa",
            "/sitemaps/pages-0029.xml": "mapa",
            "/familia/guarda-compartilhada/": "pagina",
            "/familia/guarda-compartilhada/index.md": "pagina",
            "/familia/guarda-compartilhada/?utm_source=x": "pagina",
            "/": "pagina",
            "/glossario": "pagina",
            # O 404 que o Googlebot pediu em 31/08 e um asset qualquer: fora
            # da razao, senao 404 de asset conta como pagina a favor do PASSA.
            "/sitema.xml": "outro",
            "/favicon.ico": "outro",
            # Slug editorial contendo a palavra nao vira mapa: a regra e exata.
            "/digital/sitemap-do-site/": "pagina",
        }
        for caminho, esperado in casos.items():
            with self.subTest(caminho=caminho):
                self.assertEqual(mod.classe_do_caminho(caminho), esperado)


class DiasCompletos(unittest.TestCase):
    def test_arquivo_mais_antigo_comecando_no_meio_do_dia_perde_o_primeiro_dia(self):
        # O caso medido: a retencao comeca em 11/Aug/2026:21:54:45. Contar 11/08
        # como dia deflacionaria paginas/dia da janela PRE.
        dias = mod.dias_completos("11/Aug/2026:21:54:45 -0300", "12/Aug/2026:23:59:55 -0300",
                                  True, date(2026, 9, 1))
        self.assertEqual(dias, {date(2026, 8, 12)})

    def test_arquivo_rotacionado_a_meia_noite_conta_inteiro(self):
        dias = mod.dias_completos("12/Aug/2026:00:00:03 -0300", "12/Aug/2026:23:59:55 -0300",
                                  True, date(2026, 9, 1))
        self.assertEqual(dias, {date(2026, 8, 12)})

    def test_hoje_nunca_conta(self):
        dias = mod.dias_completos("31/Aug/2026:00:00:03 -0300", "01/Sep/2026:15:58:00 -0300",
                                  False, date(2026, 9, 1))
        self.assertEqual(dias, {date(2026, 8, 31)})


class LogAusente(unittest.TestCase):
    def test_sem_arquivo_de_log_e_nao_rodou_exit_2(self):
        # Refutacao de 2026-09-01: com diretorio de log inexistente o gate
        # imprimia "retencao comeca em antes de {data}" -- frase inventada -- e
        # saia 0. Gate que nao leu nada nao pode aprovar nem inventar retencao.
        import subprocess, tempfile
        with tempfile.TemporaryDirectory() as vazio:
            env = dict(os.environ, WIKI_EFEITO_NOS_BOTS_LOG=os.path.join(vazio, "access.log"))
            proc = subprocess.run([os.path.join(TOOLS_DIR, "check-efeito-nos-bots"), "--desde", "2026-08-10"],
                                  capture_output=True, text=True, env=env,
                                  cwd=os.path.dirname(TOOLS_DIR))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("NAO RODOU", proc.stdout + proc.stderr)
        self.assertNotIn("antes de", proc.stdout)



if __name__ == "__main__":
    unittest.main()

