#!/usr/bin/env python3
"""Prova por MUTAÇÃO que `detect_encoding_defects` enxerga a terceira classe de
mojibake: os bytes de controle C1 do cp1252 lidos como texto.

POR QUE ESTE TESTE EXISTE, com o número que o originou.

O detector conhecia duas formas de encoding quebrado — UTF-8 lido como latin1
(`[ÃÂ][\\x80-\\xbf]`, o clássico "Ã©") e o caractere de substituição U+FFFD — e
era CEGO à terceira: o texto que veio de cp1252 e ficou com os bytes C1 crus.
Medido em 2026-09-10 sobre o disco:

    data/legal-corpus/*.json : 145 artigos em 20 arquivos
    content/pages.json       : 6 páginas JÁ PUBLICADAS

e o que estava no ar era o texto do Código Penal com o travessão sumido:

    "ou qualquer outro meio fraudulento: Pena \\x96 reclusão, de 1 (um) a 5"

U+0096 é o travessão do cp1252. Num navegador ele não desenha nada: a pena do
artigo aparece como "Pena  reclusão". É defeito de encoding em texto de LEI
publicado, que é exatamente o que a severidade `defeito_de_encoding` existe para
barrar antes da publicação — e ela não barrou porque não sabia olhar.

A correção é decodificar para o caractere real (U+0096 -> travessão), NUNCA
apagar o byte: apagar produz a frase mutilada que já foi ao ar.
"""
import importlib.machinery
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-v2-publication-severity")

# Os C1 do cp1252 que aparecem em texto jurídico brasileiro, por escape — este
# arquivo é lido por gente e por ferramenta, e byte de controle literal no fonte
# é justamente a família de defeito que ele cobra.
TRAVESSAO = ""
ASPA_ESQ = ""
ASPA_DIR = ""
APOSTROFO = ""


class C1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "gen_v2_publication_severity", FERRAMENTA).load_module()

    def test_texto_limpo_nao_acusa_nada(self):
        limpo = "A pena é de reclusão, de 1 (um) a 5 (cinco) anos, e multa."
        self.assertEqual(self.mod.detect_encoding_defects(limpo), [])

    def test_travessao_c1_do_cp1252_e_acusado(self):
        # O caso REAL que foi publicado em 6 páginas.
        texto = "meio fraudulento: Pena " + TRAVESSAO + " reclusão, de 1 (um) a 5 (cinco) anos"
        self.assertIn("mojibake_c1", self.mod.detect_encoding_defects(texto))

    def test_aspas_e_apostrofo_c1_tambem(self):
        for caractere in (ASPA_ESQ, ASPA_DIR, APOSTROFO):
            with self.subTest(caractere="U+%04X" % ord(caractere)):
                texto = "o contrato diz " + caractere + "boa-fé objetiva" + caractere + " no artigo"
                self.assertIn("mojibake_c1", self.mod.detect_encoding_defects(texto))

    def test_as_duas_classes_antigas_continuam_valendo(self):
        # Mutação de guarda: acrescentar a classe nova não pode apagar as velhas.
        self.assertIn("mojibake", self.mod.detect_encoding_defects("prisÃ£o preventiva"))
        self.assertIn("replacement_char", self.mod.detect_encoding_defects("deciso� judicial"))
        self.assertIn("soft_hyphen", self.mod.detect_encoding_defects("indeniza­ção"))

    def test_c1_e_mojibake_classico_no_mesmo_texto_saem_os_dois(self):
        texto = "Pena " + TRAVESSAO + " reclusão da prisÃ£o preventiva"
        defeitos = self.mod.detect_encoding_defects(texto)
        self.assertIn("mojibake_c1", defeitos)
        self.assertIn("mojibake", defeitos)

    def test_caractere_de_controle_legitimo_nao_e_acusado(self):
        # Quebra de linha, tabulação e retorno de carro são C0 legítimos em texto
        # de lei transcrito; acusá-los reprovaria o acervo inteiro.
        texto = "Art. 1º\tDispõe sobre:\r\n I - o primeiro inciso;\n II - o segundo."
        self.assertNotIn("mojibake_c1", self.mod.detect_encoding_defects(texto))

    def test_defeito_de_encoding_entra_como_CRITICO(self):
        # Encoding quebrado é motivo CRÍTICO, e crítico NÃO PUBLICA (§5 do
        # contrato). A classe nova só serve se entrar por esse caminho: o
        # detector devolve a tag e a linha 721 a prefixa com "encoding:" dentro
        # da lista `critical`. Se alguém rebaixar isso para médio, ou passar a
        # ignorar a tag nova, este teste avisa.
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn('critical.append("encoding:" + defect)', fonte)
        self.assertIn("for defect in detect_encoding_defects(text):", fonte)


if __name__ == "__main__":
    unittest.main()
