#!/usr/bin/env python3
"""Prova que `check-rota-nova-com-contexto` REPROVA -- não só aprova.

Uma sonda que devolve "40/40 íntegras" sem teste de falso positivo é asserção
sem controle: ela passaria verde se `confere()` devolvesse lista vazia sempre.
Cada caso abaixo corresponde a um defeito que a sonda tem de nomear, e os
CONTROLES no fim provam que ela não reprova página boa.

Mutantes que estes casos matam (conferido em 2026-09-16):
  - `return []` no início de `confere`        -> 6 casos vermelhos
  - remover o teste de cronologia              -> test_cronologia_impossivel
  - trocar `maior < minimo` por `maior <= 0`   -> test_citacao_curta
  - tirar o `so_digitos` da comparação do H1   -> test_h1_com_pontos (controle)
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest

FERRAMENTA = pathlib.Path(__file__).resolve().parent / "check-rota-nova-com-contexto"

# A sonda de produção usa estes dois pisos; o teste os repete de propósito, para
# que mudar o piso no produtor sem revisar o teste apareça como divergência.
MIN_CITACAO = 25
MIN_AUTORAL = 120


def carrega():
    loader = importlib.machinery.SourceFileLoader("crnc", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("crnc", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


CRNC = carrega()

CITACAO_BOA = (
    "“O recurso especial não comporta provimento porque a alegada violação "
    "do artigo invocado não se verifica no acórdão recorrido, que decidiu a "
    "controvérsia com fundamento em matéria de prova, cuja revisão é vedada "
    "pela Súmula 7 desta Corte, conforme reiterada jurisprudência.”"
)
CITACAO_CURTA = (
    "“O recurso especial não comporta provimento porque a alegada violação "
    "do artigo invocado não se verifica no acórdão recorrido.”"
)
AUTORAL = " ".join(["comentário"] * 200)


def pagina(*, h1="REsp 1.514.567", citacao=CITACAO_BOA, autoral=AUTORAL,
           pub='"datePublished": "2026-09-16"', mod='"dateModified": "2026-09-16"'):
    partes = [f"<h1>{h1}</h1>" if h1 is not None else "", f"<p>{citacao}</p>",
              f"<p>{autoral}</p>", "<script>{", pub, ",", mod, "}</script>"]
    return "".join(p for p in partes if p)


def defeitos(html, rota="/jurisprudencia/stj-resp-1514567/", status=200):
    return CRNC.confere(rota, status, html, MIN_CITACAO, MIN_AUTORAL)


class SondaReprova(unittest.TestCase):
    """O que importa: cada defeito real sai NOMEADO."""

    def test_h1_nao_nomeia_o_julgado(self):
        # H1 genérico: o leitor e o agente não sabem qual julgado é este.
        d = defeitos(pagina(h1="Jurisprudência do STJ"))
        self.assertIn("h1_nao_nomeia_o_julgado", d)

    def test_sem_h1(self):
        d = defeitos(pagina(h1=None))
        self.assertIn("sem_h1", d)

    def test_citacao_curta(self):
        # 20 palavras: abaixo do piso de 25 da camada citada da DEC-032.
        self.assertLess(CRNC.palavras(CITACAO_CURTA), MIN_CITACAO)
        d = defeitos(pagina(citacao=CITACAO_CURTA))
        self.assertTrue(any(x.startswith("citacao_oficial_com_") for x in d), d)

    def test_camada_autoral_ausente(self):
        # Página que só transcreve a fonte é espelho, não conteúdo (DEC-032).
        d = defeitos(pagina(autoral="Veja o acórdão."))
        self.assertIn("camada_autoral_ausente", d)

    def test_cronologia_impossivel(self):
        # É o defeito do P1b: publicado DEPOIS de modificado.
        d = defeitos(pagina(pub='"datePublished": "2026-09-16"',
                            mod='"dateModified": "2026-09-05"'))
        self.assertTrue(any(x.startswith("cronologia_impossivel_") for x in d), d)

    def test_sem_data_publicada(self):
        d = defeitos(pagina(pub=""))
        self.assertIn("sem_datePublished", d)

    def test_rota_404_nao_mede_a_pagina_de_erro(self):
        # Sem 200 as outras conferências mediriam o HTML do erro. A sonda
        # devolve SÓ o status -- um defeito, não cinco derivados dele.
        d = defeitos("<h1>404</h1>", status=404)
        self.assertEqual(["http_404"], d)


class SondaNaoReprovaPaginaBoa(unittest.TestCase):
    """Controle de falso positivo: sem isto, endurecer a sonda passaria verde."""

    def test_pagina_integra_nao_tem_defeito(self):
        self.assertEqual([], defeitos(pagina()))

    def test_h1_com_pontos_casa_o_slug_sem_pontos(self):
        # O H1 escreve 1.514.567 e o slug 1514567: comparar texto cru reprovaria
        # 100% das páginas. A sonda compara só dígitos.
        self.assertEqual([], defeitos(pagina(h1="REsp 1.514.567 -- Terceira Turma")))

    def test_datas_iguais_nao_sao_cronologia_impossivel(self):
        # Estreia no mesmo dia da última modificação é o caso normal.
        self.assertEqual([], defeitos(pagina(mod='"dateModified": "2026-09-16"')))

    def test_rota_sem_numero_no_slug_nao_cobra_h1_numerado(self):
        # Verbete e página de tema não têm número; cobrar um reprovaria o acervo.
        self.assertEqual([], defeitos(pagina(h1="Dano moral em atraso de voo"),
                                      rota="/temas/dano-moral-atraso-de-voo/"))


class FormatoDoNumero(unittest.TestCase):
    def test_numero_legivel(self):
        self.assertEqual("1.514.567", CRNC.numero_legivel("1514567"))
        self.assertEqual("567", CRNC.numero_legivel("567"))
        self.assertEqual("2.199.487", CRNC.numero_legivel("2199487"))


if __name__ == "__main__":
    unittest.main()
