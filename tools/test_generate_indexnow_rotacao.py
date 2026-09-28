#!/usr/bin/env python3
"""Prova a ROTAÇÃO do acervo no IndexNow — aleatória E completa.

ORDEM DO DONO (2026-09-16): "tem que enviar URLs aleatórias; quando enviar todo
o acervo, não deve parar, porque os bots e agentes descobrem através do Bing."

O que estes testes vigiam, e cada um tem precedente medido neste projeto:

  1. COBERTURA. Amostra aleatória com reposição não garante que toda URL saia.
     Uma fatia do acervo pode ficar órfã por meses sem que ninguém veja, porque
     cada execução isolada parece aleatória. O ciclo aqui é uma permutação com
     cursor: ao fim, toda URL saiu exatamente uma vez.

  2. SEM SEMENTE FIXA. Semente constante faz o "sorteio" devolver sempre o mesmo
     subconjunto. Esta sessão achou o defeito duas vezes: `random.Random(20260806)`
     na amostra de vivacidade do submissor, e — noutra frente — um ranking de rede
     social decidido por ordem alfabética, em que 78,7% do top-300 entrava pela
     letra da área.

  3. O CONTROLE PAREADO, que é o que impede a rotação de virar regressão: página
     NOVA é sempre anunciada, e a rotação nunca toma o lugar dela. Um filtro de
     volume que engole o novo em silêncio é exatamente o defeito que o dono
     mandou evitar ao pedir a instrumentação.
"""
import importlib.machinery
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-indexnow-incremental-submit")
AGORA = "2026-09-16T18:00:00+00:00"


class Rotacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "gen_indexnow_incremental", FERRAMENTA).load_module()

    def setUp(self):
        self.acervo = {"https://w.test/p%02d/" % n for n in range(10)}

    def test_um_ciclo_cobre_o_acervo_INTEIRO_sem_repetir(self):
        estado, vistas, voltas = {}, [], 0
        while voltas < 10:
            fatia, rot = self.mod.fila_de_rotacao(estado, self.acervo, 3, AGORA)
            if not fatia:
                break
            vistas.extend(fatia)
            estado["rotation"] = rot
            voltas += 1
            if rot["cursor"] >= rot["cycle_size"]:
                break
        self.assertEqual(sorted(vistas), sorted(self.acervo),
                         "o ciclo tem de cobrir o acervo inteiro, uma vez cada")
        self.assertEqual(len(vistas), len(set(vistas)), "nenhuma URL sai duas vezes no ciclo")

    def test_a_ordem_NAO_e_alfabetica(self):
        # O defeito medido na outra frente: ordenação estável disfarçada de sorteio.
        alfabetica = 0
        for _ in range(8):
            _, rot = self.mod.fila_de_rotacao({}, self.acervo, 10, AGORA)
            if rot["order"] == sorted(self.acervo):
                alfabetica += 1
        self.assertLess(alfabetica, 8, "oito ciclos não podem sair todos em ordem alfabética")

    def test_ciclos_diferentes_usam_sementes_diferentes(self):
        sementes = {self.mod.fila_de_rotacao({}, self.acervo, 1, AGORA)[1]["seed"]
                    for _ in range(5)}
        self.assertGreater(len(sementes), 1, "semente fixa faz a rotação ser sempre igual")

    def test_o_cursor_avanca_e_nao_repete_a_fatia(self):
        estado = {}
        primeira, rot = self.mod.fila_de_rotacao(estado, self.acervo, 4, AGORA)
        estado["rotation"] = rot
        segunda, rot2 = self.mod.fila_de_rotacao(estado, self.acervo, 4, AGORA)
        self.assertEqual(rot2["cursor"], 8)
        self.assertFalse(set(primeira) & set(segunda), "a segunda fatia não repete a primeira")
        self.assertEqual(rot2["seed"], rot["seed"], "o ciclo não reembaralha no meio")

    def test_rota_que_saiu_do_sitemap_nao_e_reanunciada(self):
        estado = {}
        _, rot = self.mod.fila_de_rotacao(estado, self.acervo, 2, AGORA)
        estado["rotation"] = rot
        encolhido = {u for u in self.acervo if not u.endswith("p09/")}
        for _ in range(9):
            fatia, rot = self.mod.fila_de_rotacao(estado, encolhido, 2, AGORA)
            estado["rotation"] = rot
            self.assertNotIn("https://w.test/p09/", fatia,
                             "rota fora do sitemap não se anuncia — o submissor reprova por isso")
            if not fatia:
                break

    def test_acervo_que_cresce_entra_no_ciclo_seguinte(self):
        # As 7.538 páginas de acórdão entram assim quando o ciclo virar. No
        # ciclo corrente elas saem antes, como `delta`, que tem prioridade.
        estado = {}
        fatia, rot = self.mod.fila_de_rotacao(estado, self.acervo, 10, AGORA)
        estado["rotation"] = rot
        self.assertEqual(rot["cursor"], rot["cycle_size"])
        maior = self.acervo | {"https://w.test/nova/"}
        _, rot2 = self.mod.fila_de_rotacao(estado, maior, 3, AGORA)
        self.assertEqual(rot2["cycle_size"], len(maior))
        self.assertIn("https://w.test/nova/", rot2["order"])

    def test_rotacao_zero_nao_devolve_nada(self):
        fatia, _ = self.mod.fila_de_rotacao({}, self.acervo, 0, AGORA)
        self.assertEqual(fatia, [])


class ProveniencIaEControle(unittest.TestCase):
    """O rótulo `kind` e o controle pareado, lidos no fonte que os liga."""

    def test_o_delta_tem_prioridade_e_a_rotacao_nunca_o_desloca(self):
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        # A rotação só olha o que NÃO está no envio, e entra depois.
        self.assertIn("candidatas = [u for u in hashes if u not in ja_no_envio]", fonte)
        self.assertIn("envio = delta + drenar + rotacao_urls", fonte)

    def test_o_kind_acompanha_a_url_ate_o_submissor(self):
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn('kind_de[url] = "delta"', fonte)
        self.assertIn('kind_de.setdefault(url, "rotacao")', fonte)
        self.assertIn('"%s\\t%s\\n" % (url, kind_de.get(url, "delta"))', fonte)

    def test_a_rotacao_conta_como_drenagem_para_o_gate(self):
        # Sem isto, `check-indexnow-backlog` reprova por "canal parado" num dia
        # em que o canal trabalhou.
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn("if rotacao_urls:\n        registra_drenagem(estado, 0, agora)", fonte)

    def test_o_cursor_so_avanca_depois_do_recibo(self):
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn('if rotacao_estado is not None:\n        estado["rotation"] = rotacao_estado',
                      fonte)


class CasamentoLoteRecibo(unittest.TestCase):
    """A precondição que liga o incremental ao submissor — e que era acidental.

    O incremental casa cada recibo com `envio[inicio:inicio+MAX_URLS]` por
    url_count/first_url/last_url. Desde 2026-09-16 o submissor PARTICIONA e
    descarta a gêmea `.md`. Se uma URL descartada lá entrasse no `envio` aqui,
    os lotes reposicionariam, nenhum recibo casaria e o estado pararia de
    avançar EM SILÊNCIO — submissão acontece, memória dela não.
    """

    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "gen_indexnow_incremental_casamento", FERRAMENTA).load_module()

    def test_a_precondicao_e_afirmada_e_nao_apenas_verdadeira_por_acaso(self):
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn("fora_do_sitemap = [u for u in envio if u not in hashes]", fonte)
        self.assertIn("o casamento", fonte)

    def test_a_precondicao_REPROVA_e_nao_filtra_em_silencio(self):
        """Um mutante sobreviveu à primeira versão deste teste: trocar a
        reprovação por um filtro silencioso (`envio = [u for u in envio if u in
        hashes]`) mantinha tudo verde.

        Filtrar esconde o defeito da FONTE que colocou a URL ali — e a fonte é
        o que precisa de conserto. O envio seguiria, o operador não saberia, e
        a próxima execução repetiria. Reprovar é a única saída que nomeia a
        causa.
        """
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        inicio = fonte.index("fora_do_sitemap = [u for u in envio if u not in hashes]")
        bloco = fonte[inicio:inicio + 1200]
        self.assertIn("REPROVADO", bloco, "a precondição tem de reprovar")
        self.assertIn("return 1", bloco, "e abortar antes do POST")
        self.assertNotIn("envio = [u for u in envio", bloco,
                         "filtrar em silêncio esconderia a fonte do defeito")

    def test_as_tres_fontes_do_envio_derivam_do_sitemap(self):
        # delta, backlog e rotação saem todos de `hashes`, que vem de
        # sitemap_urls(). É o que torna a precondição verdadeira hoje.
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn("urls = sitemap_urls(base)", fonte)
        self.assertIn("hashes, sem_hash = hashes_de_conteudo(urls, base)", fonte)
        self.assertIn("backlog = pendentes_sem_recibo(conhecidas, hashes)", fonte)
        self.assertIn("candidatas = [u for u in hashes if u not in ja_no_envio]", fonte)
        # a prioridade é filtrada pelo backlog, não entra crua
        self.assertIn("if u in pendente", fonte)

    def test_a_rotacao_nunca_devolve_url_fora_do_conjunto_recebido(self):
        acervo = {"https://w.test/a/", "https://w.test/b/", "https://w.test/c/"}
        estado = {}
        for _ in range(4):
            fatia, rot = self.mod.fila_de_rotacao(estado, acervo, 2, AGORA)
            estado["rotation"] = rot
            for url in fatia:
                self.assertIn(url, acervo,
                              "rotação só pode devolver o que recebeu — o submissor reprova o resto")



if __name__ == "__main__":
    unittest.main(verbosity=2)
