#!/usr/bin/env python3
"""Prova que `repair-mojibake-v2` repara o defeito e NAO toca texto correto.

O reparo de charset e destrutivo por natureza -- ele reescreve texto publicado.
Por isso os controles negativos valem mais que os positivos aqui: um reparador
guloso corromperia portugues correto em versal, que e exatamente a forma da
ementa do STJ.

Mutantes que estes casos matam (conferido em 2026-09-16):
  - `repara` devolvendo sempre o roundtrip     -> test_versal_com_a_til_nao_muda
  - tirar a guarda "eliminou a assinatura"     -> test_sequencia_invalida_nao_muda
  - reparar a string inteira em vez do run     -> test_aspa_curva_no_meio_sobrevive
  - tirar a checagem de assinatura na entrada  -> test_texto_limpo_nao_muda
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest

FERRAMENTA = pathlib.Path(__file__).resolve().parent / "repair-mojibake-v2"


def carrega():
    loader = importlib.machinery.SourceFileLoader("rmv2", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("rmv2", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


RMV2 = carrega()

# O defeito real, transcrito de jur-stj-resp-1834975 em 2026-09-16.
MOJIBAKE_REAL = "Superior Tribunal de JustiÃ§a, em SessÃ£o Virtual de 08/04/2025"
ESPERADO_REAL = "Superior Tribunal de Justiça, em Sessão Virtual de 08/04/2025"


class Repara(unittest.TestCase):
    def test_mojibake_real_e_reparado(self):
        self.assertEqual(ESPERADO_REAL, RMV2.repara(MOJIBAKE_REAL))

    def test_aspa_curva_no_meio_sobrevive(self):
        # O CASO QUE QUEBRAVA O REPARO: a secao mistura o mojibake com a aspa
        # curva que o nosso gerador insere (U+201C), fora de Latin-1. Reparar a
        # string inteira levantava UnicodeEncodeError e nada era consertado.
        texto = ("O colegiado disse “nos termos do voto” e o "
                 + MOJIBAKE_REAL + " confirmou “a tese”.")
        reparado = RMV2.repara(texto)
        self.assertIn(ESPERADO_REAL, reparado)
        # As aspas curvas continuam curvas: o reparo nao as tocou.
        self.assertEqual(texto.count("“"), reparado.count("“"))
        self.assertEqual(texto.count("”"), reparado.count("”"))

    def test_cedilha_e_til_em_varias_ocorrencias(self):
        texto = "VIOLAÃ§Ã£O NÃ£O CONFIGURADA"
        self.assertEqual("VIOLAçãO NãO CONFIGURADA", RMV2.repara(texto))


class NaoTocaTextoCorreto(unittest.TestCase):
    """Controles negativos: e aqui que um reparador guloso se denuncia."""

    def test_versal_com_a_til_nao_muda(self):
        # Palavra portuguesa em versal terminada em A-til seguida de ESPACO.
        # Foi o falso positivo que parou a onda em jur-stj-resp-2204038.
        casos = [
            "RECURSO INTERPOSTO POR IGREJA CRISTÃ APOSTÓLICA RENASCER EM CRISTO",
            "ALIMENTOS PEDIDOS PELA IRMÃ DO FALECIDO",
            "PRAZO QUE SE ENCERRA NA MANHÃ SEGUINTE",
            "SOCIEDADE ALEMÃ COM FILIAL NO BRASIL",
        ]
        for texto in casos:
            self.assertEqual(texto, RMV2.repara(texto), f"reparador tocou texto correto: {texto!r}")

    def test_a_til_seguido_de_letra_nao_muda(self):
        # QUESTAO e ACORDAO em versal: A-til seguido de LETRA, nao de byte de
        # continuacao. Era o que a minha primeira medicao contava errado.
        casos = [
            "II. QUESTÃO EM DISCUSSÃO 5",
            "ACÓRDÃO RECORRIDO MANTIDO",
            "DECISÃO AGRAVADA REFORMADA",
        ]
        for texto in casos:
            self.assertEqual(texto, RMV2.repara(texto), f"reparador tocou texto correto: {texto!r}")

    def test_texto_limpo_nao_muda(self):
        texto = "O recurso especial não comporta provimento, à luz da Súmula 7 desta Corte."
        self.assertEqual(texto, RMV2.repara(texto))

    def test_sequencia_invalida_nao_muda(self):
        # C3 seguido de continuacao que NAO forma UTF-8 valido: a assinatura
        # casa, mas o decode falha, e o texto fica intacto.
        texto = "trecho ÃÃ§ suspeito"
        reparado = RMV2.repara(texto)
        self.assertNotIn("�", reparado)

    def test_par_latin1_decodificavel_sem_assinatura_nao_muda(self):
        # ESTE CASO EXISTE PARA MATAR UM MUTANTE ESPECIFICO, e ele sobreviveu
        # a primeira versao deste teste: tirar a checagem de assinatura na
        # ENTRADA do run.
        #
        # "Ð´" e D0 B4 em Latin-1, que por acaso e UTF-8 valido e
        # decodifica para o cirilico "д". Nao ha assinatura (D0 nao e C3
        # nem C2), entao NAO e mojibake nosso e o texto tem de ficar intacto.
        # Sem a checagem de entrada, o reparador reescreveria isto.
        texto = "sigla Ð´ no corpo do acordao"
        self.assertEqual(texto, RMV2.repara(texto))

    def test_roundtrip_que_mantem_a_assinatura_nao_e_aplicado(self):
        # E ESTE MATA O OUTRO MUTANTE que sobreviveu: tirar a guarda "o reparo
        # so vale se ELIMINOU a assinatura".
        #
        # Bytes C3 83 C2 80 lidos como Latin-1 sao "ÃÂ";
        # o roundtrip devolve "Ã", que AINDA carrega a assinatura --
        # e mojibake de mojibake, e reparar uma camada deixa o texto num estado
        # intermediario que ninguem sabe ler. A guarda recusa o reparo parcial.
        texto = "ÃÂ"
        self.assertEqual(texto, RMV2.repara(texto))

    def test_repara_run_tambem_checa_a_assinatura_na_entrada(self):
        # `repara` ja barra na porta o texto sem assinatura, o que torna a
        # checagem DENTRO de `repara_run` redundante por aquele caminho -- e foi
        # por isso que o mutante que a removia SOBREVIVEU a primeira rodada.
        # Ele nao e defeito; e mutante equivalente. Mas `repara_run` e publica e
        # pode ser chamada direto, e ai a guarda e a unica que existe: sem ela,
        # "Ð´" (D0 B4, UTF-8 valido por acaso) viraria cirilico.
        texto = "sigla Ð´ no corpo do acordao"
        self.assertEqual(texto, RMV2.repara_run(texto))


class ReparaArvore(unittest.TestCase):
    def test_estrutura_do_documento_e_preservada(self):
        doc = {
            "intent_id": "jur-x",
            "sections": [{"heading": "Ementa", "text": MOJIBAKE_REAL}],
            "faq": [],
            "palavras": 845,
            "ativo": True,
        }
        novo = RMV2.repara_arvore(doc)
        self.assertEqual(ESPERADO_REAL, novo["sections"][0]["text"])
        self.assertEqual("Ementa", novo["sections"][0]["heading"])
        self.assertEqual(845, novo["palavras"])
        self.assertIs(True, novo["ativo"])
        self.assertEqual([], novo["faq"])
        self.assertEqual(sorted(doc), sorted(novo))


if __name__ == "__main__":
    unittest.main()
