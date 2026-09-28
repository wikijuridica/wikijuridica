#!/usr/bin/env python3
"""Testes de `tools/check-sonda-interna-declarada`, com access logs SINTETICOS.

CONTROLE POSITIVO ANTES DO ZERO. Este gate nasceu de uma medicao cujo resultado
esperado era zero: 9.236 de 9.236 requisicoes com o User-Agent do WikijuridicaBot
contra a nossa origem carregam `X-Warming-Request`, e os 22 `tools/call` que o
plano acusou tambem carregam — a acusacao de que "a sonda entra na metrica" e'
refutada NAQUELE conjunto. Um gate cujo unico resultado observado e' zero pode
estar certo ou pode estar quebrado, e os dois se parecem. Por isso o primeiro
caso deste arquivo e' um POSITIVO sintetico: a prova de que ele acusa.

(E a varredura seguinte, com o gate ja funcionando, achou o caso real que o plano
nao tinha nomeado: `tools/reload-wiki-server` mandava ~24 requisicoes por dia sem
o cabecalho, todo dia. Foi corrigido no ponto de saida.)

Descoberto pelo passo 2c de `tools/run-qualidade-diaria` (glob `tools/test_*.py`).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-sonda-interna-declarada")

CANONICO = ("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
            "+https://wikijuridica.com.br/bot/; sonda-interna)")


def escreve_acesso(raiz, dia, linhas):
    destino = os.path.join(raiz, "data", "ops", "access")
    os.makedirs(destino, exist_ok=True)
    caminho = os.path.join(destino, "access-%s.jsonl" % dia)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
    return caminho


def req(ua, *, warming=False, simulacao=False, ts="2026-09-15T10:00:00Z", path="/x/"):
    registro = {"ts": ts, "path": path, "user_agent": ua}
    if warming:
        registro["warming"] = True
    if simulacao:
        registro["bot_simulation"] = True
    return registro


def roda(raiz, extra=()):
    comando = [sys.executable, GATE, "--raiz", raiz, *extra]
    processo = subprocess.run(comando, capture_output=True, text=True, timeout=120)
    return processo.returncode, processo.stdout + processo.stderr


class SondaInternaDeclarada(unittest.TestCase):

    def test_positivo_sintetico_o_gate_acusa(self):
        """CONTROLE POSITIVO. Sem este caso, "VERDE" e "quebrado" sao a mesma saida."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-15", [
                req(CANONICO, warming=True),
                req(CANONICO, warming=False, path="/mcp"),
            ])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("VERMELHO", saida)
            self.assertIn("/mcp", saida)

    def test_sonda_declarada_passa(self):
        """O caminho certo nao pode reprovar: seria gate que pune quem acertou."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-15", [
                req(CANONICO, warming=True),
                req("wikijuridica-superficie-probe/1.0", warming=True),
                req("wikijuridica-reload-check/1.0", warming=True),
            ])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("VERDE", saida)

    def test_simulacao_declarada_tambem_passa(self):
        """`bot_simulation` e' outra forma de se declarar sintetico."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-15", [
                req("wikijuridica-superficie-probe/1.0", simulacao=True)])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)

    def test_visitante_de_verdade_nao_e_assunto_deste_gate(self):
        """Fronteira declarada: aqui so' se julga identidade NOSSA."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-15", [
                req("Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"),
                req("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"),
            ])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("req. com identidade nossa: 0", saida)

    def test_nivel_historico_nao_reprova_mas_sai_datado(self):
        """O ledger e' APPEND-ONLY: reprovar pelo nivel seria divida que nada drena.

        MUTACAO QUE ESTE CASO MATA: trocar `na_metrica_fluxo` por `na_metrica` no
        veredito faz o gate ficar vermelho por dias DEPOIS de a causa estar
        corrigida — e gate que fica vermelho por divida conhecida deixa de ser
        lido, e ai o vermelho que importa entra junto.
        """
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-10",
                           [req(CANONICO, ts="2026-09-10T10:00:00Z")] * 5)
            escreve_acesso(tmp, "2026-09-11", [req(CANONICO, warming=True,
                                                   ts="2026-09-11T10:00:00Z")])
            escreve_acesso(tmp, "2026-09-12", [req(CANONICO, warming=True,
                                                   ts="2026-09-12T10:00:00Z")])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("nivel historico 5", saida)
            self.assertIn("2026-09-10", saida)

    def test_janela_sai_impressa(self):
        """"VERDE sobre 7 dias" e "VERDE sobre tudo" sao afirmacoes diferentes."""
        with tempfile.TemporaryDirectory() as tmp:
            for dia in range(10, 20):
                escreve_acesso(tmp, "2026-09-%d" % dia,
                               [req(CANONICO, warming=True,
                                    ts="2026-09-%dT10:00:00Z" % dia)])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("janela              : 7 de 10 arquivo(s)", saida)

    def test_proposito_composto_a_mao_e_observado_sem_reprovar(self):
        """Higiene se mostra; vermelho se reserva para a sonda que entrou na conta."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve_acesso(tmp, "2026-09-15", [
                req("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
                    "+https://wikijuridica.com.br/bot/; inventario-superficies)",
                    warming=True)])
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("inventario-superficies", saida)
            self.assertIn("VERDE", saida)

    def test_sem_log_e_exit_2_nunca_verde(self):
        """"Nao conferi" jamais pode ser lido como "esta tudo certo"."""
        with tempfile.TemporaryDirectory() as tmp:
            codigo, saida = roda(tmp)
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NAO MEDIU", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
