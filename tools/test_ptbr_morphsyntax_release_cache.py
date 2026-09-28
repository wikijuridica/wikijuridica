#!/usr/bin/env python3
"""Prova o cache de release do oraculo de morfossintaxe: chave, falha aberta e lote.

POR QUE ESTE TESTE NASCE EM 2026-09-10. O passe de release percorria os 7.959
registros de `refined_public_prose.jsonl` a cada execucao. O commit 944a40fa
mediu 116 s em 2026-07-09 e escreveu que "escala a 10k"; aquela medicao era sobre
N=590 (5.295.507 bytes) e o corpus de hoje tem 86.519.453 — 13,5x. Medido em
execucao direta, sem envelope: mais de 1.020 s de parede a 92% de CPU, contra
orcamento de 180 s e teto duro de 540 s. A evidencia ficou em
`checked_at=2026-07-15` porque nao havia como regenera-la.

O QUE O TESTE TRAVA nao e a performance — e a CORRECAO do cache, que e o unico
jeito de o ganho nao virar falso verde:

  1. a chave muda quando o CONTEUDO muda;
  2. a chave muda quando a IDENTIDADE DO MOTOR muda (spaCy, modelo, stanza,
     torch) — cache que ignorasse isso devolveria o veredito do motor velho
     depois de um upgrade;
  3. cache ilegivel FALHA ABERTO: vira cache vazio e tudo e reanalisado;
  4. o lote limita o que se analisa por execucao, nunca o que se mede.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_loader(
    "ptbr_morphsyntax_oracle",
    importlib.machinery.SourceFileLoader(
        "ptbr_morphsyntax_oracle",
        str(RAIZ / "scripts" / "ptbr_morphsyntax_oracle.py")))
oraculo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oraculo)

RUNTIME = {
    "spacy_version": "3.8.14",
    "spacy_model_version": "3.8.0",
    "stanza_version": "1.13.0",
    "torch_version": "2.12.1+cpu",
}
REGISTRO = {"sample_id": "corpus-1", "text": "A tese firmada pelo tribunal."}
SEGMENTOS = [{"text": "A tese firmada pelo tribunal."}]


def chave(registro=None, segmentos=None, runtime=None, max_chars=100000):
    return oraculo.chave_de_release(registro or REGISTRO, segmentos or SEGMENTOS,
                                    runtime or RUNTIME, max_chars)


class ChaveDeConteudo(unittest.TestCase):
    def test_mesma_entrada_mesma_chave(self):
        self.assertEqual(chave(), chave())

    def test_texto_diferente_chave_diferente(self):
        outro = dict(REGISTRO, text="A tese firmada pelo tribunal e outra coisa.")
        self.assertNotEqual(chave(), chave(registro=outro))

    def test_segmento_diferente_chave_diferente(self):
        self.assertNotEqual(chave(), chave(segmentos=[{"text": "Outro segmento."}]))

    def test_teto_de_caracteres_diferente_chave_diferente(self):
        self.assertNotEqual(chave(), chave(max_chars=50000))

    def test_versao_de_cada_motor_entra_na_chave(self):
        for campo in ("spacy_version", "spacy_model_version", "stanza_version", "torch_version"):
            with self.subTest(campo=campo):
                outro = dict(RUNTIME, **{campo: RUNTIME[campo] + ".9"})
                self.assertNotEqual(chave(), chave(runtime=outro),
                                    f"{campo} nao entra na chave: upgrade devolveria veredito velho")

    def test_segmentos_nao_se_confundem_por_concatenacao(self):
        # "ab" + "c" e "a" + "bc" nao podem dar a mesma chave.
        um = chave(segmentos=[{"text": "ab"}, {"text": "c"}])
        outro = chave(segmentos=[{"text": "a"}, {"text": "bc"}])
        self.assertNotEqual(um, outro)


class CacheFalhaAberto(unittest.TestCase):
    def escreve(self, conteudo: str) -> pathlib.Path:
        base = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        caminho = base / "cache.jsonl"
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho

    def test_cache_ausente_e_vazio(self):
        base = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.assertEqual(oraculo.carrega_cache_de_release(base / "nao-existe.jsonl"), {})

    def test_json_quebrado_descarta_o_cache_INTEIRO_e_nao_so_a_linha(self):
        # A primeira linha e VALIDA e COMPLETA de proposito: se ela nao fosse, a
        # guarda de campo obrigatorio devolveria vazio antes de o parser chegar a
        # linha quebrada, e o teste passaria sem exercitar a falha aberta. Foi
        # exatamente isso que deixou o mutante "cache ilegivel vira parcial" vivo
        # na primeira bancada.
        boa = {campo: False for campo in oraculo.CAMPOS_DE_CACHE}
        boa["sample_id"] = "corpus-1"
        boa["blocking_codes"] = []
        caminho = self.escreve(json.dumps({"chave": "a", "analise": boa}) + "\n{quebrado\n")
        self.assertEqual(oraculo.carrega_cache_de_release(caminho), {},
                         "linha quebrada tem de derrubar o cache inteiro, nao so a si mesma")

    def test_analise_sem_campo_obrigatorio_descarta_o_cache_inteiro(self):
        parcial = {campo: False for campo in oraculo.CAMPOS_DE_CACHE if campo != "sample_id"}
        caminho = self.escreve(json.dumps({"chave": "a", "analise": parcial}) + "\n")
        self.assertEqual(oraculo.carrega_cache_de_release(caminho), {},
                         "analise incompleta tem de derrubar o cache, nunca aprovar")

    def test_cache_completo_e_lido(self):
        analise = {campo: False for campo in oraculo.CAMPOS_DE_CACHE}
        analise["sample_id"] = "corpus-1"
        analise["blocking_codes"] = []
        caminho = self.escreve(json.dumps({"chave": "a", "analise": analise}) + "\n")
        lido = oraculo.carrega_cache_de_release(caminho)
        self.assertEqual(list(lido), ["a"])
        self.assertEqual(lido["a"]["sample_id"], "corpus-1")

    def test_grava_e_le_de_volta_o_mesmo_conjunto(self):
        base = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        caminho = base / "sub" / "cache.jsonl"
        analise = {campo: False for campo in oraculo.CAMPOS_DE_CACHE}
        analise["sample_id"] = "corpus-1"
        analise["blocking_codes"] = ["terminal_preposition"]
        oraculo.grava_cache_de_release(caminho, {"a": analise, "b": dict(analise, sample_id="corpus-2")})
        self.assertEqual(oraculo.carrega_cache_de_release(caminho).keys(), {"a", "b"})


class ProveniencaDoRelease(unittest.TestCase):
    """O artefato tem de dizer QUANTO desta execucao veio do cache.

    `input_fingerprint_sha256` e o hash do arquivo INTEIRO e `validate_record` o
    compara com o arquivo vivo — o registro afirma "fui produzido analisando este
    arquivo". Com cache, os vereditos podem vir de execucoes anteriores; cada um
    continua correto (a chave e o conteudo do registro mais a identidade dos
    motores), mas sem estes dois numeros
    `release_covered_records=7959` nao distingue passada completa de passada que
    nao analisou nada.
    """

    def base(self, **extra):
        registro = {
            "input_records": 10,
            "release_covered_records": 10,
            "release_computed_now": 4,
            "release_from_cache": 6,
            "release_cache_schema": oraculo.RELEASE_CACHE_SCHEMA,
            "release_blocked_record_count": 0,
            "public_release_blocked": False,
        }
        registro.update(extra)
        return registro

    def valida(self, registro):
        # Chama a funcao REAL que `validate_record` usa. A primeira versao deste
        # teste chamava `validate_record` inteiro e as tres asserções falhavam:
        # o validador reprovava antes, por campo anterior ausente, e a guarda de
        # proveniencia nunca era alcancada. Guarda que o teste nao alcanca e
        # guarda que o teste nao prova.
        try:
            oraculo.valida_proveniencia_de_release(
                registro, registro.get("release_covered_records", 0))
        except oraculo.OracleError as erro:
            return str(erro)
        return ""

    def test_soma_que_nao_fecha_reprova(self):
        mensagem = self.valida(self.base(release_from_cache=5))
        self.assertIn("release provenance inconsistent", mensagem)

    def test_campo_ausente_reprova(self):
        registro = self.base()
        del registro["release_computed_now"]
        self.assertIn("release provenance missing", self.valida(registro))

    def test_esquema_de_cache_velho_reprova(self):
        mensagem = self.valida(self.base(release_cache_schema=oraculo.RELEASE_CACHE_SCHEMA - 1))
        self.assertIn("release cache schema stale", mensagem)

    def test_contagem_negativa_reprova_mesmo_com_a_soma_fechando(self):
        # -1 + 11 = 10 fecha a soma e e impossivel: nenhuma execucao analisa um
        # numero negativo de registros. Sem esta guarda, um erro de sinal passaria
        # pela conferencia da soma sem ser visto.
        mensagem = self.valida(self.base(release_computed_now=-1, release_from_cache=11))
        self.assertIn("release provenance invalid", mensagem)

    def test_soma_que_fecha_passa_desta_guarda(self):
        mensagem = self.valida(self.base())
        self.assertNotIn("release provenance", mensagem)
        self.assertNotIn("release cache schema", mensagem)


class LoteParcial(unittest.TestCase):
    def test_release_parcial_carrega_os_tres_numeros(self):
        erro = oraculo.ReleaseParcial(analisados=3000, restantes=4959, total=7959)
        self.assertEqual((erro.analisados, erro.restantes, erro.total), (3000, 4959, 7959))
        self.assertIn("4959", str(erro))


if __name__ == "__main__":
    unittest.main()
