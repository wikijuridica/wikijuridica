#!/usr/bin/env python3
"""Prova do gate `bot-registry-decidido`, com controle POSITIVO e NEGATIVO.

Sem os dois, "zero achados" é indistinguível de "o predicado parou de casar" —
e este gate nasce para virar vermelho num dia que ninguém está olhando, o dia em
que um agente novo aparece pela segunda vez.

CONTROLE NEGATIVO: o registro completo sobre o ledger real. Tem de sair VERDE.
CONTROLE POSITIVO: seis defeitos, um por vez, cada um o modo de falha que o gate
existe para pegar — e cada um tem de sair vermelho com o SEU código, não com
outro qualquer.

Os User-Agents das fixtures são literais do tráfego real (borda e origem,
2026-09-15/16); nenhum foi inventado.
"""
import io
import json
import os
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")
sys.path.insert(0, os.path.join(RAIZ, "tools"))
gate = SourceFileLoader("check_bot_registry_decidido",
                        os.path.join(RAIZ, "tools", "check-bot-registry-decidido")).load_module()

UA_BAIDU = ("Mozilla/5.0 (compatible; Baiduspider/2.0; "
            "+http://www.baidu.com/search/spider.html)")
UA_SHAPBOT = ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); "
              "compatible; ShapBot/0.1.0")
UA_NODE = "node"

# PISO DA FIXTURE. Travar a fixture no piso de produção (50) mediria o tamanho
# da fixture, não o predicado — é a mesma razão pela qual
# `checkProdutorOrfaoComPiso` parametriza o piso.
PISO_FIXTURE = 4


def candidatos(extra=()):
    linhas = [
        {"token": "Baiduspider", "date": "2026-09-15", "requests": 609,
         "user_agent_sample": UA_BAIDU},
        {"token": "Baiduspider", "date": "2026-09-16", "requests": 447,
         "user_agent_sample": UA_BAIDU},
        {"token": "ShapBot", "date": "2026-09-15", "requests": 238,
         "user_agent_sample": UA_SHAPBOT},
        {"token": "ShapBot", "date": "2026-09-16", "requests": 1072,
         "user_agent_sample": UA_SHAPBOT},
        {"token": "node", "date": "2026-09-15", "requests": 659,
         "user_agent_sample": UA_NODE},
        {"token": "node", "date": "2026-09-16", "requests": 701,
         "user_agent_sample": UA_NODE},
        # Aparece UMA vez só: não exige decisão, e é o controle de que o limiar
        # de persistência não virou "todo token que passar por aqui".
        {"token": "TelegramBot", "date": "2026-09-16", "requests": 40,
         "user_agent_sample": "TelegramBot (like TwitterBot)"},
    ]
    return list(linhas) + list(extra)


def registro_completo(mudanca=None, remover=None, extra=()):
    linhas = [
        {"token": "Baiduspider", "decisao": "registrado", "agent_key": "baiduspider",
         "user_agent": UA_BAIDU, "decidido_em": "2026-09-16"},
        {"token": "ShapBot", "decisao": "nao_identificado", "agent_key": None,
         "user_agent": UA_SHAPBOT, "decidido_em": "2026-09-16"},
        {"token": "node", "decisao": "cliente_generico", "agent_key": None,
         "user_agent": UA_NODE, "decidido_em": "2026-09-16"},
    ]
    if remover:
        linhas = [l for l in linhas if l["token"] != remover]
    if mudanca:
        for l in linhas:
            if l["token"] == mudanca[0]:
                l.update(mudanca[1])
    return linhas + list(extra)


class GateDeDecisao(unittest.TestCase):
    def roda(self, cands, reg):
        d = tempfile.mkdtemp(prefix="bot-registry-decidido-")
        led = os.path.join(d, "candidatos.jsonl")
        regc = os.path.join(d, "decididos.jsonl")
        with io.open(led, "w", encoding="utf-8") as f:
            for l in cands:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
        with io.open(regc, "w", encoding="utf-8") as f:
            f.write("# comentario nao registra nada\n")
            for l in reg:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
        return gate.audita(led, regc, piso=PISO_FIXTURE)

    # ---------------- controle NEGATIVO ----------------
    def test_registro_completo_sai_verde(self):
        problemas, resumo = self.roda(candidatos(), registro_completo())
        self.assertEqual(problemas, [], problemas)
        self.assertEqual(resumo["tokens_persistentes"], 3)
        self.assertEqual(resumo["decisoes"], 3)

    def test_token_de_uma_data_so_nao_exige_decisao(self):
        """Persistência é o limiar. Um scanner de passagem não vira registro."""
        problemas, _ = self.roda(candidatos(), registro_completo())
        self.assertNotIn("TelegramBot", [t for _, t, _ in problemas])

    # ---------------- controle POSITIVO ----------------
    def test_token_persistente_sem_decisao_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(remover="ShapBot"))
        self.assertIn(("token_sem_decisao", "ShapBot"),
                      [(c, t) for c, t, _ in problemas])

    def test_decisao_envelhecida_reprova(self):
        """O agente foi registrado e a linha daqui ficou dizendo o contrário.

        `Baiduspider` tem chave desde 2026-09-16; declará-lo `nao_identificado`
        faz o registro afirmar, com autoridade, uma coisa que a régua já nega.
        """
        problemas, _ = self.roda(candidatos(), registro_completo(
            mudanca=("Baiduspider", {"decisao": "nao_identificado", "agent_key": None})))
        self.assertIn(("decisao_envelhecida", "Baiduspider"),
                      [(c, t) for c, t, _ in problemas])

    def test_agent_key_divergente_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(
            mudanca=("Baiduspider", {"agent_key": "googlebot"})))
        self.assertIn(("agent_key_divergente", "Baiduspider"),
                      [(c, t) for c, t, _ in problemas])

    def test_registrado_que_perdeu_a_entrada_na_telemetria_reprova(self):
        """O caminho inverso: alguém tira a entrada de tools/botagents.py."""
        problemas, _ = self.roda(candidatos(), registro_completo(
            mudanca=("Baiduspider", {"user_agent": "UmAgenteQueNinguemRegistrou/1.0"})))
        self.assertIn(("registrado_sem_chave_na_telemetria", "Baiduspider"),
                      [(c, t) for c, t, _ in problemas])

    def test_decisao_sem_candidato_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(extra=[
            {"token": "BotQueNuncaVeio", "decisao": "nao_identificado",
             "agent_key": None, "user_agent": "BotQueNuncaVeio/1.0",
             "decidido_em": "2026-09-16"}]))
        self.assertIn(("decisao_sem_candidato", "BotQueNuncaVeio"),
                      [(c, t) for c, t, _ in problemas])

    def test_decisao_sem_user_agent_literal_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(
            mudanca=("ShapBot", {"user_agent": ""})))
        self.assertIn(("decisao_sem_user_agent_literal", "ShapBot"),
                      [(c, t) for c, t, _ in problemas])

    def test_token_invalido_exige_substituto(self):
        cands = candidatos(extra=[
            {"token": "robot", "date": "2026-08-25", "requests": 1369,
             "user_agent_sample": "Mozilla/5.0 (compatible; X/1; +http://e.test/robot/x)"},
            {"token": "robot", "date": "2026-09-15", "requests": 1182,
             "user_agent_sample": "Mozilla/5.0 (compatible; X/1; +http://e.test/robot/x)"}])
        reg = registro_completo(extra=[
            {"token": "robot", "decisao": "token_invalido", "agent_key": None,
             "user_agent": "", "decidido_em": "2026-09-16"}])
        problemas, _ = self.roda(cands, reg)
        self.assertIn(("token_invalido_sem_substituto", "robot"),
                      [(c, t) for c, t, _ in problemas])

    def test_decisao_duplicada_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(extra=[
            {"token": "node", "decisao": "desta_casa", "agent_key": None,
             "user_agent": UA_NODE, "decidido_em": "2026-09-16"}]))
        self.assertIn(("decisao_duplicada", "node"),
                      [(c, t) for c, t, _ in problemas])

    def test_decisao_desconhecida_reprova(self):
        problemas, _ = self.roda(candidatos(), registro_completo(
            mudanca=("ShapBot", {"decisao": "a_decidir_depois"})))
        self.assertIn(("decisao_desconhecida", "ShapBot"),
                      [(c, t) for c, t, _ in problemas])

    def test_piso_de_deteccao_reprova_varredura_cega(self):
        """Ledger truncado ou caminho errado tem de gritar, não passar verde."""
        problemas, _ = self.roda(candidatos()[:2], registro_completo())
        self.assertEqual([c for c, _, _ in problemas],
                         ["ledger_de_candidatos_abaixo_do_piso"])

    # ---------------- a árvore real ----------------
    def test_arvore_real_esta_decidida(self):
        """O registro nasce COMPLETO. Gate que nasce vermelho se aprende a ignorar."""
        problemas, resumo = gate.audita(gate.LEDGER_PADRAO, gate.REGISTRO_PADRAO)
        self.assertEqual(problemas, [], problemas)
        self.assertGreaterEqual(resumo["candidatos"], gate.PISO_DE_DETECCAO)
        self.assertGreater(resumo["tokens_persistentes"], 0)


if __name__ == "__main__":
    unittest.main()
