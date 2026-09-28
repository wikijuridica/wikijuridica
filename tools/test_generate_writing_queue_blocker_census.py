#!/usr/bin/env python3
"""Testes do censo de bloqueadores da fila de escrita.

O censo existe porque uma frase única — "lote omitido sem shard completo" —
cobria 86 lotes com quatro causas distintas, e a leitura errada dela sustentou
por vários turnos a afirmação de que "86 lotes aguardam redação". Medido em
2026-09-05: 46 exigem redação, 40 têm o texto inteiro no disco.

O risco desta ferramenta é o inverso do gate que ela explica. Um gate frouxo
deixa passar defeito; um censo frouxo diz que não falta redação onde falta, e
alguém deixa de escrever página que o portal precisa. Por isso cada classe tem
teste próprio E um teste de não-confusão: a classe mais benigna
(``ordem_divergente``, que dispensa redação) nunca pode absorver um caso em que
falta linha.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "generate-writing-queue-blocker-census"


def carrega():
    loader = importlib.machinery.SourceFileLoader("censo_bloqueadores", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def registros(*intents: str) -> list[dict[str, str]]:
    return [{"intent_id": intent} for intent in intents]


class TestClassificacao(unittest.TestCase):
    def setUp(self):
        self.censo = carrega()

    def test_ordem_divergente_nao_exige_redacao(self):
        """O caso de familia-03: 22 esperadas, 22 no disco, ordem trocada."""
        linha = self.censo._classifica(
            "familia-03", ["a", "b", "c"], registros("c", "a", "b"), ())
        self.assertEqual(linha["classe"], "ordem_divergente")
        self.assertFalse(linha["exige_redacao"])
        self.assertEqual(linha["esperadas"], 3)
        self.assertEqual(linha["no_shard"], 3)
        self.assertEqual(linha["posicoes_divergentes"], 3)
        self.assertEqual(linha["primeira_divergencia"],
                         {"posicao": 0, "no_shard": "c", "no_slice": "a"})

    def test_linha_faltante_exige_redacao_e_nomeia_o_que_falta(self):
        """O caso de consumidor-17: falta UMA intenção, não o lote."""
        linha = self.censo._classifica(
            "consumidor-17", ["a", "b", "c"], registros("a", "b"), ())
        self.assertEqual(linha["classe"], "linha_faltante")
        self.assertTrue(linha["exige_redacao"])
        self.assertEqual(linha["intents_faltantes"], ["c"])

    def test_bloqueio_semantico_nao_e_redacao(self):
        """O caso de imobiliario-02: texto inteiro, fonte sem resolução exata."""
        linha = self.censo._classifica(
            "imobiliario-02", ["a", "b"], registros("a", "b"), ("b",))
        self.assertEqual(linha["classe"], "bloqueio_semantico")
        self.assertFalse(linha["exige_redacao"])
        self.assertEqual(linha["intents_bloqueadas"], ["b"])

    def test_corpo_nao_reusavel_quando_conjunto_e_ordem_batem(self):
        """Sobrou só a quarta hipótese: as linhas estão lá e na ordem certa."""
        linha = self.censo._classifica(
            "x-01", ["a", "b"], registros("a", "b"), ())
        self.assertEqual(linha["classe"], "corpo_nao_reusavel")
        self.assertFalse(linha["exige_redacao"])

    def test_falta_vence_bloqueio_e_ordem(self):
        """NÃO-CONFUSÃO: linha faltante não pode ser diluída em classe benigna.

        Aqui falta ``c``, ``b`` está bloqueada e a ordem também diverge. Se a
        precedência invertesse, o censo diria "não exige redação" para um lote
        a que falta página — o erro caro que esta ferramenta existe para não
        cometer.
        """
        linha = self.censo._classifica(
            "x-02", ["a", "b", "c"], registros("b", "a"), ("b",))
        self.assertEqual(linha["classe"], "linha_faltante")
        self.assertTrue(linha["exige_redacao"])

    def test_excedente_autenticado_nao_vira_ordem_divergente(self):
        """Extra por supersessão vai ao FIM; isso não é ordem trocada.

        O classificador aceita ``expected_order + extras``. Um shard nessa
        forma que ainda assim é recusado não pode ser rotulado de ordem
        divergente, senão o censo aponta para o reparo errado.
        """
        linha = self.censo._classifica(
            "x-03", ["a", "b"], registros("a", "b", "extra"), ())
        self.assertEqual(linha["classe"], "corpo_nao_reusavel")
        self.assertEqual(linha["intents_excedentes"], ["extra"])

    def test_excedente_no_meio_e_ordem_divergente(self):
        """O mesmo extra FORA do fim quebra a ordem canônica, e o censo vê."""
        linha = self.censo._classifica(
            "x-04", ["a", "b"], registros("a", "extra", "b"), ())
        self.assertEqual(linha["classe"], "ordem_divergente")
        self.assertEqual(linha["intents_excedentes"], ["extra"])


class TestConfrontoComOClassificador(unittest.TestCase):
    """O censo grava DUAS medições e marca quando elas discordam.

    `classe` é inferida por comparação de conjuntos; `motivo_do_classificador`
    é lido de `BatchCompletion.reasons`, que sabe qual das cinco cláusulas
    reprovou. A coincidência entre as duas foi o que autenticou este censo na
    refutação adversarial de 2026-09-05 — uma implementação sozinha não teria
    com o que ser conferida. Quando discordarem, o censo não escolhe: registra.
    """

    def setUp(self):
        self.censo = carrega()

    def _linha(self, classe: str, motivos: tuple[str, ...]) -> dict:
        """Reproduz o confronto que `censo()` faz, sem tocar o acervo vivo."""
        linha = {"classe": classe}
        if motivos:
            linha["motivo_do_classificador"] = list(motivos)
            if not any(m.startswith(linha["classe"]) for m in motivos):
                linha["divergencia"] = (
                    f"inferi {linha['classe']}, o classificador diz "
                    f"{motivos[0].split('=')[0].split(':')[0]}")
        return linha

    def test_medicoes_que_concordam_nao_marcam_divergencia(self):
        linha = self._linha("ordem_divergente",
                            ("ordem_divergente=22 de 22 posicao(oes)",))
        self.assertNotIn("divergencia", linha)
        self.assertEqual(len(linha["motivo_do_classificador"]), 1)

    def test_medicoes_que_discordam_gravam_as_duas(self):
        linha = self._linha("ordem_divergente",
                            ("linha_faltante=1 de 14 (o shard tem 13 linha(s)): x",))
        self.assertIn("divergencia", linha)
        self.assertIn("inferi ordem_divergente", linha["divergencia"])
        self.assertIn("linha_faltante", linha["divergencia"])
        # a inferência NÃO é sobrescrita: as duas ficam no registro
        self.assertEqual(linha["classe"], "ordem_divergente")
        self.assertTrue(linha["motivo_do_classificador"])

    def test_shard_ausente_nao_passa_pelo_classificador_e_nao_diverge(self):
        """Sem chamada ao classificador não há `reasons` — e isso não é conflito."""
        linha = self._linha("shard_ausente", ())
        self.assertNotIn("divergencia", linha)
        self.assertNotIn("motivo_do_classificador", linha)


class TestResumo(unittest.TestCase):
    def setUp(self):
        self.censo = carrega()

    def test_resumo_conta_todas_as_classes_declaradas(self):
        contagem = self.censo._resumo([
            {"classe": "shard_ausente"},
            {"classe": "shard_ausente"},
            {"classe": "ordem_divergente"},
        ])
        self.assertEqual(contagem["shard_ausente"], 2)
        self.assertEqual(contagem["ordem_divergente"], 1)
        self.assertEqual(contagem["linha_faltante"], 0)
        self.assertEqual(set(contagem), set(self.censo.CLASSES))

    def test_toda_classe_emitida_esta_declarada_em_CLASSES(self):
        """Classe nova sem entrada em CLASSES faria _resumo levantar KeyError.

        O teste trava as duas pontas: as classes que ``_classifica`` sabe emitir
        e as que o resumo sabe contar são o mesmo conjunto.
        """
        emitidas = set()
        for esperado, obs, bloq in (
                (["a"], ["a"], ()),
                (["a", "b"], ["b", "a"], ()),
                (["a", "b"], ["a"], ()),
                (["a", "b"], ["a", "b"], ("a",)),
        ):
            emitidas.add(
                self.censo._classifica("s", esperado, registros(*obs), bloq)["classe"])
        self.assertTrue(emitidas <= set(self.censo.CLASSES), emitidas)


class TestLeituraDoShard(unittest.TestCase):
    def setUp(self):
        self.censo = carrega()

    def test_jsonl_invalido_reprova_com_o_numero_da_linha(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            shard = pathlib.Path(tmp) / "x-05.jsonl"
            shard.write_text('{"intent_id": "a"}\nnao-e-json\n', encoding="utf-8")
            with self.assertRaises(ValueError) as capturado:
                self.censo._registros_do_shard(shard)
            self.assertIn("linha 2", str(capturado.exception))

    def test_linha_que_nao_e_objeto_reprova(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            shard = pathlib.Path(tmp) / "x-06.jsonl"
            shard.write_text('["a"]\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                self.censo._registros_do_shard(shard)


if __name__ == "__main__":
    unittest.main()
