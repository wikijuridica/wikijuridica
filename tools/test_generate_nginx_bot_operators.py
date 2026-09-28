#!/usr/bin/env python3
"""Testes do mapa de operador e do tier agregado.

O QUE ELES IMPEDEM DE VOLTAR: a chave de toda zona de rate limit era
`$binary_remote_addr`, então o número do registry não era o teto do OPERADOR —
era o teto de cada endereço dele, multiplicado pela frota. E a isenção era
decidida pelo User-Agent, que é string que o cliente escolhe.

O teste mais importante é o último de cada classe: o que prova que a zona do não
verificado EXISTE e é APLICADA. Sem ela, quem digita o nome do bot vindo de fora
da faixa oficial não é contado em zona nenhuma do tier e cai só na guarda
genérica — teto MAIOR que o de quem não forja.
"""
import ipaddress
import json
import os
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OP = SourceFileLoader("operadores", os.path.join(RAIZ, "tools/generate-nginx-bot-operators")).load_module()
TIERS = SourceFileLoader("tiers", os.path.join(RAIZ, "tools/generate-nginx-rate-tiers")).load_module()


class MapaDeOperador(unittest.TestCase):
    def setUp(self):
        self.por_operador, self.desconhecidos, self.descartados = OP.prefixos_por_operador()

    def test_a_frota_da_mesma_empresa_cai_num_balde_so(self):
        # googlebot.json e google-special-crawlers.json são frotas da MESMA
        # empresa e partilham a saída de rede. Contá-las em baldes separados
        # permitiria o dobro a quem tem dois nomes de crawler.
        self.assertIn("google", self.por_operador)
        self.assertGreater(len(self.por_operador["google"]), 300)
        for produto in ("googlebot", "google-special-crawlers", "google-user-triggered"):
            self.assertEqual(OP.OPERADOR_POR_ARQUIVO[produto], "google")

    def test_prefixo_repetido_entre_arquivos_nao_duplica(self):
        # duckassistbot.json e duckduckbot.json publicam as MESMAS faixas. O
        # nginx aceita a duplicata com aviso no -t, e teste que passa com aviso
        # ensina a ignorar aviso.
        for operador, prefixos in self.por_operador.items():
            self.assertEqual(len(prefixos), len(set(prefixos)),
                             f"{operador} tem prefixo repetido no mapa gerado")

    def test_nenhum_arquivo_de_faixa_fica_sem_operador_em_silencio(self):
        # Arquivo novo em bot_ip_ranges/ sem entrada no mapeamento vira aviso
        # dentro do .conf, nunca faixa faltando sem ninguém saber.
        if self.desconhecidos:
            self.assertIn("ATENÇÃO", OP.bloco())

    def test_o_default_e_vazio_e_isso_e_ausencia_de_prova(self):
        # Vazio significa "não é de frota conhecida", nunca "não é bot".
        gerado = OP.bloco()
        self.assertIn('default "";', gerado)
        self.assertIn("geo $wj_operador_do_ip {", gerado)

    def test_endereco_de_documentacao_nao_pertence_a_operador_nenhum(self):
        # Controle negativo com faixa reservada por RFC 5737: se ela casasse,
        # o mapa estaria largo demais e daria teto de operador a qualquer um.
        fora = ipaddress.ip_address("203.0.113.7")
        for prefixos in self.por_operador.values():
            for prefixo in prefixos:
                self.assertNotIn(fora, ipaddress.ip_network(prefixo))

    def test_o_conf_no_disco_confere_com_as_faixas(self):
        # Amostra real, não fixture: se o timer de faixas atualizar e ninguém
        # regenerar, este teste cai junto com o --conferir.
        caminho = os.path.join(RAIZ, "ops", "nginx", "bot-operators.conf")
        with open(caminho, encoding="utf-8") as arquivo:
            self.assertEqual(arquivo.read(), OP.bloco())


class TierAgregado(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(RAIZ, "content", "crawl_policy.json"), encoding="utf-8") as arquivo:
            self.politica = json.load(arquivo)
        self.bloco = TIERS.bloco()
        self.aplicacao = TIERS.bloco_aplicacao()

    def test_o_tier_agregado_chaveia_pelo_operador_e_nao_pelo_endereco(self):
        self.assertIn(
            'map "$wj_bot_allow:$wj_tier_training_aggregated_marca:$wj_operador_do_ip"',
            self.bloco)
        self.assertIn('"~^0:1:(?<wjop>.+)$"  $wjop;', self.bloco)

    def test_o_nao_verificado_tem_zona_PROPRIA_e_ela_e_APLICADA(self):
        # O teste que sustenta a entrega. Zona definida e não referenciada é
        # rate limit inerte: quem forja o nome cairia só na guarda genérica,
        # com teto maior que o de quem não forja.
        self.assertIn("zone=wj_tier_training_aggregated_nv:", self.bloco)
        self.assertIn("limit_req zone=wj_tier_training_aggregated_nv ", self.aplicacao)
        self.assertIn("limit_req zone=wj_tier_training_aggregated ", self.aplicacao)

    def test_o_teto_do_nao_verificado_e_menor_que_o_do_verificado(self):
        tier = next(t for t in self.politica["rate_tiers"]
                    if t["name"] == "training_tier_aggregated")
        self.assertLess(tier["unverified_requests_per_minute"], tier["requests_per_minute"])

    def test_tier_comum_continua_com_uma_zona_so(self):
        # CONTROLE POSITIVO: sem ele, "ensinar o gerador a emitir duas zonas"
        # poderia ter virado "emitir duas para todo mundo".
        self.assertIn('map "$wj_bot_allow:$wj_tier_training_std_marca" $wj_tier_training_std_key',
                      self.bloco)
        self.assertNotIn("wj_tier_training_std_nv", self.bloco)

    def test_o_teto_agregado_cobre_o_maior_pico_ja_medido(self):
        # 2.010 req/min foi o maior pico por operador em 7 dias de log de
        # origem. O teto não pode nascer abaixo do que já se observou.
        tier = next(t for t in self.politica["rate_tiers"]
                    if t["name"] == "training_tier_aggregated")
        self.assertGreater(tier["requests_per_minute"], 2010)


if __name__ == "__main__":
    unittest.main()
