#!/usr/bin/env python3
"""Prova que a simulação de crawler em `check-crawl-recovery-e2e` é OPT-IN, e que
a sonda padrão sai com a identidade do portal.

POR QUE ESTE TESTE EXISTE.

Duas réguas do dono se cruzam nesta ferramenta. O `CLAUDE.md` da máquina proíbe
"requisição com User-Agent de bot real (GPTBot, ClaudeBot, Googlebot…)" e obriga
"sonda interna com UA próprio + header `X-Warming-Request: true`". O contrato do
repositório, §11, permite simular Googlebot com `httptest` contra o nosso
próprio handler — o que não sai para a rede. Esta ferramenta faz a terceira
coisa: sai para o domínio público com o UA de cada crawler, porque a pergunta
dela ("o que a BORDA faz com cada crawler") é decidida por User-Agent no WAF, nas
bot rules e no cache, e trocar o UA muda o que se mede.

A conciliação, decidida em 2026-09-10 e cobrada aqui: a simulação deixa de ser
padrão e passa a exigir `--simular-bots`, dita por quem responde pela execução.
Sem a flag, a ferramenta sonda com a identidade do portal. Em qualquer dos dois
modos toda requisição leva `X-Bot-Simulation: true`, que é o que mantém o ensaio
fora da contagem de audiência (`tools/generate-bot-traffic-origin` os exclui em
`simulations_excluded`).

MUTAÇÃO QUE ESTE TESTE PEGA: alguém devolver a simulação ao caminho padrão, ou
remover o `X-Bot-Simulation` de um dos modos.
"""
import importlib.machinery
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "check-crawl-recovery-e2e")


class SimulacaoOptIn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "check_crawl_recovery_e2e", FERRAMENTA).load_module()
        cls.fonte = open(FERRAMENTA, encoding="utf-8").read()

    def test_a_identidade_padrao_e_a_sonda_do_portal(self):
        self.assertEqual(self.mod.UA_DA_SONDA, "wikijuridica-superficie-probe/1.0")

    def test_a_flag_existe_e_governa_a_selecao(self):
        self.assertIn('parser.add_argument("--simular-bots"', self.fonte)
        self.assertIn('agentes = dict(UAS) if args.simular_bots else {"sonda": UA_DA_SONDA}',
                      self.fonte)

    def test_nenhum_caminho_usa_o_dicionario_de_bots_fora_da_flag(self):
        # Se voltar a existir `UAS[...]` ou `UAS.items()` no corpo, o UA de bot
        # real volta ao caminho padrão sem ninguém pedir.
        self.assertNotIn("UAS[", self.fonte)
        self.assertNotIn("UAS.items()", self.fonte)

    def test_os_dois_modos_marcam_a_requisicao_como_simulacao(self):
        self.assertIn('"X-Bot-Simulation": "true"', self.fonte)

    def test_a_sonda_propria_fica_fora_da_contagem_de_audiencia(self):
        self.assertIn('if ua == UA_DA_SONDA:', self.fonte)
        self.assertIn('cabecalhos["X-Warming-Request"] = "true"', self.fonte)

    def test_os_ua_de_crawler_continuam_disponiveis_para_a_flag(self):
        # A capacidade não foi removida — foi condicionada. Perder os UAs seria
        # perder a única medição de comportamento da borda por crawler.
        for chave in ("googlebot", "bingbot", "gptbot", "perplexitybot"):
            with self.subTest(chave=chave):
                self.assertIn(chave, self.mod.UAS)


if __name__ == "__main__":
    unittest.main()
