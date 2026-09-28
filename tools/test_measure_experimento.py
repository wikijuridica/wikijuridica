#!/usr/bin/env python3
"""Testes de tools/measure-experimento — séries sintéticas numa raiz temporária.

A regra que esta bancada existe para travar: **nunca declarar vencedor sem
intervalo**, e amostra pequena sair como `sem_decisao` dizendo o N que falta.

O que ela prova, e como cada asserção reprova quando a linha some:
  - diferença que é RUÍDO com amostra pequena => `sem_decisao` + `faltam`;
  - diferença que é ruído com amostra GRANDE => `continuar`, nunca `adotar`;
  - P(variante melhor) ≥ 0,95 com o IC95 da razão ainda cruzando 1 =>
    `continuar` (é o caso real medido: 93 contra 71 eventos);
  - a forma fechada da razão de duas Gamas bate com Monte Carlo semeado;
  - variante não aplicada => A/A declarado, saída 4, nunca efeito;
  - desfecho que não é o primário declarado não vira veredito;
  - bot de TREINO não conta como leitura de IA — provado por MUTAÇÃO da tabela;
  - Bing não soma o total do dia com a quebra por consulta — provado por
    MUTAÇÃO do leitor;
  - dia sem série não vira página×dia de exposição;
  - ensaio não escreve; só `--gravar` grava.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

import numpy as np

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ_REPO, "tools", "measure-experimento")
NUCLEO = os.path.join(RAIZ_REPO, "tools", "experimentos.py")

CONTROLE = "controle"
VARIANTE = "titulo_do_h1"


def carrega(fonte_nucleo=None):
    guardado = sys.modules.get("experimentos")
    if fonte_nucleo is not None:
        nucleo = types.ModuleType("experimentos")
        nucleo.__file__ = NUCLEO
        exec(compile(fonte_nucleo, NUCLEO, "exec"), nucleo.__dict__)
        sys.modules["experimentos"] = nucleo
    try:
        ferramenta = types.ModuleType("measure_experimento_sob_teste")
        ferramenta.__file__ = FERRAMENTA
        with open(FERRAMENTA, encoding="utf-8") as handle:
            exec(compile(handle.read(), FERRAMENTA, "exec"), ferramenta.__dict__)
        return ferramenta
    finally:
        if fonte_nucleo is not None:
            if guardado is None:
                sys.modules.pop("experimentos", None)
            else:
                sys.modules["experimentos"] = guardado


def roda(ferramenta, *argumentos):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
        codigo = ferramenta.principal(list(argumentos))
    return codigo, saida.getvalue()


def caminhos(prefixo, quantos):
    return [f"/familia/{prefixo}-{i:03d}/" for i in range(quantos)]


class Bancada:
    """Raiz temporária com um experimento e as três séries de desfecho."""

    def __init__(self, paginas_por_braco=20, aplicado_em="2026-09-01",
                 piso_eventos=30, piso_page_days=100):
        self.raiz = tempfile.mkdtemp(prefix="medicao-teste-")
        os.makedirs(os.path.join(self.raiz, "data", "ops"))
        os.makedirs(os.path.join(self.raiz, "data", "ai"))
        os.symlink(os.path.join(RAIZ_REPO, "tools"), os.path.join(self.raiz, "tools"))
        self.controle = caminhos("controle", paginas_por_braco)
        self.variante = caminhos("variante", paginas_por_braco)
        coorte = ([{"path": p, "braco": CONTROLE, "intent_id": f"c{i}"} for i, p in enumerate(self.controle)]
                  + [{"path": p, "braco": VARIANTE, "intent_id": f"v{i}"} for i, p in enumerate(self.variante)])
        self.experimento = {
            "schema_version": "experimentos_v1", "tipo": "experimento",
            "experimento_id": "exp-teste", "date": "2026-09-01",
            "gerado_em": "2026-09-01T00:00:00+00:00", "estado": "aplicado",
            "fator": "titulo", "campo_alterado": "title",
            "aplicado_em": aplicado_em, "janela_dias": 14,
            "desfecho_primario": "bot_ia_leituras",
            "bracos": [{"nome": CONTROLE, "paginas": paginas_por_braco},
                       {"nome": VARIANTE, "paginas": paginas_por_braco}],
            "regra_de_veredito": {
                "p_variante_melhor_para_adotar": 0.95,
                "p_variante_melhor_para_descartar": 0.05,
                "piso_eventos_por_braco": piso_eventos,
                "piso_page_days_por_braco": piso_page_days,
            },
            "coorte": coorte,
        }
        with open(os.path.join(self.raiz, "data", "ai", "experimentos.jsonl"),
                  "w", encoding="utf-8") as handle:
            handle.write(json.dumps(self.experimento, ensure_ascii=False) + "\n")
        self.escreve_bing([])
        self.escreve_clarity([])

    def escreve_bot(self, por_dia):
        """por_dia: {data: {rota: requisições}} do agente oai-searchbot (função `search`)."""
        linhas = []
        for data, rotas in sorted(por_dia.items()):
            linhas.append({"agent_key": "oai-searchbot", "date": data, "function": "search",
                           "summable": True, "schema_version": "origin_bot_routes_daily_v1",
                           "distinct_routes_in_window": len(rotas), "top_routes_cap": 200,
                           "requests": sum(rotas.values()),
                           "top_routes": [{"route": r, "requests": n} for r, n in sorted(rotas.items())]})
        self._grava("origin_bot_routes_daily.jsonl", linhas)

    def acrescenta_bot_de_treino(self, data, rotas):
        caminho = os.path.join(self.raiz, "data", "ops", "origin_bot_routes_daily.jsonl")
        with open(caminho, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "agent_key": "gptbot", "date": data, "function": "training", "summable": True,
                "schema_version": "origin_bot_routes_daily_v1",
                "distinct_routes_in_window": len(rotas), "top_routes_cap": 200,
                "requests": sum(rotas.values()),
                "top_routes": [{"route": r, "requests": n} for r, n in sorted(rotas.items())]}) + "\n")

    def escreve_bing(self, linhas):
        self._grava("bing_webmaster_daily.jsonl", linhas)

    def escreve_clarity(self, linhas):
        self._grava("clarity_insights_daily.jsonl", linhas)

    def _grava(self, nome, linhas):
        with open(os.path.join(self.raiz, "data", "ops", nome), "w", encoding="utf-8") as handle:
            for linha in linhas:
                handle.write(json.dumps(linha, ensure_ascii=False) + "\n")

    def ledger(self):
        caminho = os.path.join(self.raiz, "data", "ai", "experimentos.jsonl")
        with open(caminho, encoding="utf-8") as handle:
            return [json.loads(linha) for linha in handle if linha.strip()]

    def limpa(self):
        shutil.rmtree(self.raiz, ignore_errors=True)


def serie_uniforme(bancada, dias, por_pagina_controle, por_pagina_variante):
    por_dia = {}
    for indice in range(dias):
        data = f"2026-09-{indice + 1:02d}"
        rotas = {}
        for caminho in bancada.controle:
            rotas[caminho] = por_pagina_controle
        for caminho in bancada.variante:
            rotas[caminho] = por_pagina_variante
        por_dia[data] = rotas
    return por_dia


class TesteVeredito(unittest.TestCase):
    def setUp(self):
        self.ferramenta = carrega()

    def mede(self, bancada, *extra):
        codigo, saida = roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo",
                             "--desde", "2026-09-01", "--ate", "2026-09-14", "--gravar", *extra)
        return codigo, saida, bancada.ledger()[-1]

    def test_ruido_com_amostra_pequena_sai_sem_decisao(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 1, 1, 1))
        codigo, _saida, linha = self.mede(bancada)
        self.assertEqual(codigo, 0)
        # reprova se: o piso sair de veredito() — com 20 eventos por braço e
        # taxas idênticas, qualquer veredito que não seja "sem decisão" é ruído
        # promovido a decisão
        self.assertEqual(linha["veredito"], "sem_decisao")
        self.assertEqual(linha["faltam"]["eventos"], {CONTROLE: 10, VARIANTE: 10})
        self.assertEqual(linha["faltam"]["page_days"], {CONTROLE: 80, VARIANTE: 80})
        # e o intervalo continua sendo publicado, mesmo sem decisão
        self.assertIn("razao_ic95", linha["comparacao"])

    def test_ruido_com_amostra_grande_nunca_vira_vencedor(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 3, 3))
        _codigo, _saida, linha = self.mede(bancada)
        self.assertEqual(linha["eventos_por_braco"][CONTROLE], 600)
        self.assertEqual(linha["eventos_por_braco"][VARIANTE], 600)
        # reprova se: a regra passar a decidir só por P — com taxas iguais e
        # 600 eventos por braço o veredito correto é continuar observando
        self.assertEqual(linha["veredito"], "continuar")
        baixo, alto = linha["comparacao"]["razao_ic95"]
        self.assertLess(baixo, 1.0)
        self.assertGreater(alto, 1.0)

    def test_efeito_grande_vira_adotar_com_intervalo_que_exclui_um(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 4))
        _codigo, saida, linha = self.mede(bancada)
        self.assertEqual(linha["veredito"], "adotar")
        baixo, _alto = linha["comparacao"]["razao_ic95"]
        # reprova se: `exclui_um` sair da regra — adotar com IC cruzando 1 é
        # exatamente "declarar vencedor sem intervalo"
        self.assertGreater(baixo, 1.0)
        self.assertIn("IC95", saida)

    def test_efeito_negativo_vira_descartar(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 4, 2))
        _codigo, _saida, linha = self.mede(bancada)
        self.assertEqual(linha["veredito"], "descartar")
        self.assertLess(linha["comparacao"]["razao_ic95"][1], 1.0)

    def test_p_alto_com_intervalo_cruzando_um_nao_adota(self):
        """O caso real: 93 contra 71 eventos dá P = 0,953 e IC95 [0,956; 1,774]."""
        ferramenta = self.ferramenta
        post_v = ferramenta.posterior(93, 3850.0)
        post_c = ferramenta.posterior(71, 3822.0)
        comp = ferramenta.compara(post_v, post_c)
        self.assertGreater(comp["p_variante_melhor"], 0.95)
        self.assertLess(comp["razao_ic95"][0], 1.0)
        registro = {"regra_de_veredito": {"piso_eventos_por_braco": 30,
                                          "piso_page_days_por_braco": 100,
                                          "p_variante_melhor_para_adotar": 0.95,
                                          "p_variante_melhor_para_descartar": 0.05}}
        medida = {"eventos": {CONTROLE: 71, VARIANTE: 93},
                  "exposicao": {CONTROLE: 3822, VARIANTE: 3850}}
        decisao, motivo, _faltam = ferramenta.veredito(registro, medida, comp, True)
        # reprova se: o "e IC95 exclui 1" virar "ou" — é a diferença entre
        # trocar o título de 5% do acervo por evidência e por sorte
        self.assertEqual(decisao, "continuar")
        self.assertIn("IC95", motivo)

    def test_forma_fechada_bate_com_monte_carlo(self):
        ferramenta = self.ferramenta
        gerador = np.random.default_rng(20260910)
        for eventos_v, exposicao_v, eventos_c, exposicao_c in ((93, 3850.0, 71, 3822.0),
                                                               (12, 300.0, 30, 310.0),
                                                               (600, 2000.0, 640, 2000.0)):
            post_v = ferramenta.posterior(eventos_v, exposicao_v)
            post_c = ferramenta.posterior(eventos_c, exposicao_c)
            comp = ferramenta.compara(post_v, post_c)
            amostra_v = gerador.gamma(post_v["alpha"], 1.0 / exposicao_v, 400000)
            amostra_c = gerador.gamma(post_c["alpha"], 1.0 / exposicao_c, 400000)
            # reprova se: a identidade (λv/λc)=(bc/bv)(av/ac)·F(2av,2ac) for trocada
            # por uma aproximação normal — que erra justamente na cauda que decide
            self.assertAlmostEqual(comp["p_variante_melhor"], float((amostra_v > amostra_c).mean()),
                                   places=2)
            baixo, alto = np.quantile(amostra_v / amostra_c, [0.025, 0.975])
            self.assertAlmostEqual(comp["razao_ic95"][0], float(baixo), delta=0.02 * float(baixo))
            self.assertAlmostEqual(comp["razao_ic95"][1], float(alto), delta=0.02 * float(alto))

    def test_variante_nao_aplicada_e_a_a_com_saida_propria(self):
        bancada = Bancada(aplicado_em=None)
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 4))
        codigo, saida, linha = self.mede(bancada)
        # reprova se: `if not aplicado` sair de veredito() — os dias anteriores
        # à aplicação virariam "efeito" de uma intervenção que não houve
        self.assertEqual(codigo, 4)
        self.assertEqual(linha["veredito"], "sem_decisao")
        self.assertIn("variante_nao_aplicada", linha["motivo"])
        self.assertIn("A/A", saida)

    def test_linha_de_estado_habilita_o_veredito(self):
        """A transição no ledger é o que tira a medição do modo A/A."""
        bancada = Bancada(aplicado_em=None)
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 4))
        codigo, _saida, linha = self.mede(bancada)
        self.assertEqual(codigo, 4)
        self.assertEqual(linha["veredito"], "sem_decisao")
        with open(os.path.join(bancada.raiz, "data", "ai", "experimentos.jsonl"), "a",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"schema_version": "experimentos_v1", "tipo": "estado",
                                     "experimento_id": "exp-teste", "estado": "aplicado",
                                     "aplicado_em": "2026-09-01",
                                     "gerado_em": "2026-09-01T12:00:00+00:00"}) + "\n")
        codigo, _saida, linha = self.mede(bancada)
        # reprova se: measure voltar a ler a linha de CRIAÇÃO em vez do estado
        # dobrado — `adotar` seria inalcançável fora dos testes
        self.assertEqual(codigo, 0)
        self.assertEqual(linha["aplicado_em"], "2026-09-01")
        self.assertEqual(linha["veredito"], "adotar")

    def test_desfecho_nao_primario_nao_decide(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 4))
        _codigo, _saida, linha = self.mede(bancada, "--desfecho", "clarity_sessoes")
        # reprova se: o guarda do desfecho primário sair — seria escolher a
        # régua depois de ver os números
        self.assertEqual(linha["veredito"], "sem_decisao")
        self.assertIn("não é o primário declarado", linha["motivo"])

    def test_ensaio_nao_escreve(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 4))
        antes = len(bancada.ledger())
        codigo, saida = roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo",
                             "--desde", "2026-09-01", "--ate", "2026-09-14")
        self.assertEqual(codigo, 0)
        self.assertIn("ENSAIO", saida)
        # reprova se: a gravação deixar de depender de `if args.gravar`
        self.assertEqual(len(bancada.ledger()), antes)


class TesteLeituraDasSeries(unittest.TestCase):
    def setUp(self):
        self.ferramenta = carrega()

    def test_bot_de_treino_nao_conta_como_leitura_de_ia(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 2))
        bancada.acrescenta_bot_de_treino("2026-09-01", {p: 50 for p in bancada.variante})
        codigo, _saida = roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo",
                              "--desde", "2026-09-01", "--ate", "2026-09-14", "--gravar")
        self.assertEqual(codigo, 0)
        linha = bancada.ledger()[-1]
        # reprova se: FUNCOES_DE_IA passar a aceitar `training` — o GPTBot
        # varre o acervo inteiro e afogaria qualquer efeito real
        self.assertEqual(linha["eventos_por_braco"][VARIANTE], 400)

        with open(NUCLEO, encoding="utf-8") as handle:
            fonte = handle.read()
        alvo = 'FUNCOES_DE_IA = ("search", "user")'
        self.assertIn(alvo, fonte)
        mutante = carrega(fonte.replace(alvo, 'FUNCOES_DE_IA = ("search", "user", "training")'))
        roda(mutante, "--raiz", bancada.raiz, "--ultimo", "--desde", "2026-09-01",
             "--ate", "2026-09-14", "--gravar")
        # o mutante prova que a tabela de funções é quem filtra
        self.assertEqual(bancada.ledger()[-1]["eventos_por_braco"][VARIANTE], 400 + 20 * 50)

    def test_bing_nao_soma_total_do_dia_com_quebra_por_consulta(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 2))
        alvo = bancada.variante[0]
        url = "https://wikijuridica.com.br" + alvo
        bancada.escreve_bing([
            {"tipo": "pagina_diaria", "Date": "2026-09-04", "Query": url, "Impressions": 40,
             "Clicks": 2, "coletado_em": "2026-09-05T00:00:00+00:00", "schema": "bing_webmaster_v1"},
            {"tipo": "pagina_consulta", "Date": "2026-09-04", "Pagina": url, "Consulta": "pensão",
             "Impressions": 15, "Clicks": 1, "coletado_em": "2026-09-05T00:00:00+00:00",
             "schema": "bing_webmaster_v1"},
            {"tipo": "pagina_consulta", "Date": "2026-09-04", "Pagina": url, "Consulta": "guarda",
             "Impressions": 10, "Clicks": 0, "coletado_em": "2026-09-05T00:00:00+00:00",
             "schema": "bing_webmaster_v1"},
        ])
        roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo", "--desde", "2026-09-01",
             "--ate", "2026-09-14", "--gravar")
        linha = bancada.ledger()[-1]
        impressoes = linha["desfechos_secundarios"]["bing_impressoes"]["eventos"][VARIANTE]
        # reprova se: o leitor somar as duas famílias — daria 65 no lugar de 40,
        # e a página com mais consultas listadas pareceria ter mais tráfego
        self.assertEqual(impressoes, 40)

        with open(NUCLEO, encoding="utf-8") as handle:
            fonte = handle.read()
        alvo_fonte = "        total.setdefault(chave, valor)"
        self.assertIn(alvo_fonte, fonte)
        mutante = carrega(fonte.replace(
            alvo_fonte,
            "        alvo_mut = total.setdefault(chave, dict(valor))\n"
            "        if alvo_mut is not valor:\n"
            "            alvo_mut['impressoes'] += valor['impressoes']"))
        roda(mutante, "--raiz", bancada.raiz, "--ultimo", "--desde", "2026-09-01",
             "--ate", "2026-09-14", "--gravar")
        self.assertEqual(
            bancada.ledger()[-1]["desfechos_secundarios"]["bing_impressoes"]["eventos"][VARIANTE], 65)

    def test_clarity_ignora_sessao_nula_e_pesa_pela_janela(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 10, 2, 2))
        url = "https://wikijuridica.com.br" + bancada.variante[0] + "?utm_source=chatgpt.com"
        bancada.escreve_clarity([{
            "schema": "clarity_insights_v1", "coletado_em": "2026-09-05T00:00:00+00:00",
            "janela_dias": 3, "dimensoes": ["URL"],
            "metricas": [
                {"metricName": "DeadClickCount",
                 "information": [{"Url": url, "sessionsCount": None}]},
                {"metricName": "Traffic",
                 "information": [{"Url": url, "sessionsCount": 7}]},
            ]}])
        roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo", "--desde", "2026-09-01",
             "--ate", "2026-09-14", "--gravar")
        dados = bancada.ledger()[-1]["desfechos_secundarios"]["clarity_sessoes"]
        # reprova se: `if bruto is None: continue` sair — a sessão sumiria por
        # aparecer nula numa das nove métricas da mesma URL
        self.assertEqual(dados["eventos"][VARIANTE], 7)
        # reprova se: a exposição do Clarity voltar a contar COLETAS em vez de dias
        self.assertEqual(dados["cobertura"]["dias_com_serie"], 3)
        self.assertFalse(dados["cobertura"]["observacoes_independentes"])

    def test_dia_sem_serie_nao_vira_exposicao(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 4, 2, 2))
        roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo", "--desde", "2026-09-01",
             "--ate", "2026-09-14", "--gravar")
        linha = bancada.ledger()[-1]
        # a janela de calendário tem 14 dias, mas a série só tem 4
        self.assertEqual(linha["janela"]["dias_no_calendario"], 14)
        self.assertEqual(linha["cobertura"]["dias_com_serie"], 4)
        # reprova se: a exposição passar a usar os dias do calendário — dia em
        # que a coleta não rodou viraria zero observado, e a taxa cairia sozinha
        self.assertEqual(linha["exposicao_page_days"][CONTROLE], 80)

    def test_experimento_inexistente_e_ledger_ausente(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 4, 2, 2))
        codigo, saida = roda(self.ferramenta, "--raiz", bancada.raiz, "--experimento", "exp-que-nao-existe")
        self.assertEqual(codigo, 3)
        self.assertIn("não está no ledger", saida)
        vazia = tempfile.mkdtemp(prefix="medicao-vazia-")
        self.addCleanup(shutil.rmtree, vazia, True)
        codigo, saida = roda(self.ferramenta, "--raiz", vazia, "--ultimo")
        self.assertEqual(codigo, 3)
        self.assertIn("nenhum experimento", saida)

    def test_fonte_de_desfecho_ausente_sai_com_codigo_proprio(self):
        bancada = Bancada()
        self.addCleanup(bancada.limpa)
        bancada.escreve_bot(serie_uniforme(bancada, 4, 2, 2))
        os.remove(os.path.join(bancada.raiz, "data", "ops", "origin_bot_routes_daily.jsonl"))
        codigo, saida = roda(self.ferramenta, "--raiz", bancada.raiz, "--ultimo")
        # reprova se: a série ausente virar zero — "não medi" e "medi zero" são
        # coisas diferentes, e a segunda decidiria o experimento
        self.assertEqual(codigo, 2)
        self.assertIn("fonte ausente", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
