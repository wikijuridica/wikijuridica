#!/usr/bin/env python3
"""Testes do reparo de âncora do CPP de 2026-09-05.

Este gerador escreve em `data/editorial/v2_pages/`, o estoque canônico. Errar
aqui não devolve um teste vermelho: devolve uma citação jurídica apontando para
o artigo errado numa página pública. Por isso os testes atacam as duas formas de
errar que este caso específico oferece.

A PRIMEIRA é o endereçamento. Em `crim-assistente-de-acusacao` as três URLs a
corrigir são BYTE-IDÊNTICAS entre si e cada uma anuncia um artigo diferente no
`name` (268, 271, 269, nessa ordem, que não é a numérica). Um mapa por URL
casaria as três com a mesma correção.

A SEGUNDA é a escrita. Reserializar o registro reescreveria a linha inteira
(medido: 6.534 → 6.449 bytes) e enterraria a mudança real num diff de arquivo
inteiro.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "generate-v2-planalto-anchor-repair-20260905"

COMP = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm"
NUA = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689.htm"


def carrega():
    loader = importlib.machinery.SourceFileLoader("reparo_ancora", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TestAplica(unittest.TestCase):
    def setUp(self):
        self.tool = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.pages = pathlib.Path(self._tmp.name)
        self.tool.PAGES = self.pages

    def tearDown(self):
        self._tmp.cleanup()

    def escreve_shard(self, nome: str, registros: list[dict]) -> pathlib.Path:
        caminho = self.pages / f"{nome}.jsonl"
        caminho.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros),
            encoding="utf-8")
        return caminho

    def tres_identicas(self) -> dict:
        return {"intent_id": "crim-assistente-de-acusacao", "official_sources": [
            {"url": COMP, "name": "CPP, art. 268"},
            {"url": COMP, "name": "CPP, art. 271"},
            {"url": COMP + "#art598", "name": "CPP, art. 598"},
            {"url": COMP, "name": "CPP, art. 269"},
        ]}

    def plano_das_tres(self) -> list[dict]:
        return [
            {"shard": "s", "intent_id": "crim-assistente-de-acusacao", "indice": 0,
             "name": "CPP, art. 268", "url_antiga": COMP, "url_nova": NUA + "#art268"},
            {"shard": "s", "intent_id": "crim-assistente-de-acusacao", "indice": 1,
             "name": "CPP, art. 271", "url_antiga": COMP, "url_nova": NUA + "#art271"},
            {"shard": "s", "intent_id": "crim-assistente-de-acusacao", "indice": 3,
             "name": "CPP, art. 269", "url_antiga": COMP, "url_nova": NUA + "#art269"},
        ]

    def test_tres_urls_identicas_recebem_o_artigo_certo_cada_uma(self):
        caminho = self.escreve_shard("s", [self.tres_identicas()])
        tocados, _ = self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertEqual(tocados, 3)
        fontes = json.loads(caminho.read_text(encoding="utf-8"))["official_sources"]
        self.assertEqual(fontes[0]["url"], NUA + "#art268")
        self.assertEqual(fontes[1]["url"], NUA + "#art271")
        self.assertEqual(fontes[3]["url"], NUA + "#art269")

    def test_a_entrada_que_ja_tinha_fragmento_valido_nao_e_tocada(self):
        """`#art598` existe no compilado (medido); mexer nela seria regressão."""
        caminho = self.escreve_shard("s", [self.tres_identicas()])
        self.tool.aplica(self.plano_das_tres(), aplicar=True)
        fontes = json.loads(caminho.read_text(encoding="utf-8"))["official_sources"]
        self.assertEqual(fontes[2]["url"], COMP + "#art598")

    def test_escrita_preserva_a_linha_fora_das_urls(self):
        registro = self.tres_identicas()
        registro["opening"] = "Um texto editorial com acentuação, vírgulas e ç."
        registro["word_count"] = 412
        caminho = self.escreve_shard("s", [registro])
        antes = caminho.read_text(encoding="utf-8")
        self.tool.aplica(self.plano_das_tres(), aplicar=True)
        depois = caminho.read_text(encoding="utf-8")
        # tudo o que não é a URL trocada continua idêntico
        self.assertEqual(
            depois.replace(NUA + "#art268", COMP)
                  .replace(NUA + "#art271", COMP)
                  .replace(NUA + "#art269", COMP),
            antes)

    def test_dry_run_nao_escreve(self):
        caminho = self.escreve_shard("s", [self.tres_identicas()])
        antes = caminho.read_text(encoding="utf-8")
        tocados, evidencia = self.tool.aplica(self.plano_das_tres(), aplicar=False)
        self.assertEqual(tocados, 3)
        self.assertEqual(len(evidencia), 3)
        self.assertEqual(caminho.read_text(encoding="utf-8"), antes)

    def test_cas_de_name_reprova(self):
        """O `name` é o que distingue as três; se mudou, o plano está velho."""
        registro = self.tres_identicas()
        registro["official_sources"][1]["name"] = "CPP, art. 999"
        self.escreve_shard("s", [registro])
        with self.assertRaises(ValueError) as capturado:
            self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertIn("CAS FALHOU", str(capturado.exception))

    def test_cas_de_url_reprova(self):
        registro = self.tres_identicas()
        registro["official_sources"][0]["url"] = "https://example.org/outra"
        self.escreve_shard("s", [registro])
        with self.assertRaises(ValueError) as capturado:
            self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertIn("CAS FALHOU", str(capturado.exception))

    def test_rodar_duas_vezes_e_idempotente(self):
        caminho = self.escreve_shard("s", [self.tres_identicas()])
        self.tool.aplica(self.plano_das_tres(), aplicar=True)
        primeiro = caminho.read_text(encoding="utf-8")
        tocados, _ = self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertEqual(tocados, 0)
        self.assertEqual(caminho.read_text(encoding="utf-8"), primeiro)

    def test_intent_ausente_reprova(self):
        self.escreve_shard("s", [{"intent_id": "outro", "official_sources": []}])
        with self.assertRaises(ValueError) as capturado:
            self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertIn("não existe em s", str(capturado.exception))

    def test_indice_fora_do_array_reprova(self):
        registro = self.tres_identicas()
        registro["official_sources"] = registro["official_sources"][:2]
        self.escreve_shard("s", [registro])
        with self.assertRaises(ValueError) as capturado:
            self.tool.aplica(self.plano_das_tres(), aplicar=True)
        self.assertIn("índice", str(capturado.exception))


class TestPlanoReal(unittest.TestCase):
    def setUp(self):
        self.tool = carrega()

    def test_o_plano_tem_as_oito_correcoes_medidas(self):
        correcoes = self.tool.carrega_plano()
        self.assertEqual(len(correcoes), 8)
        for item in correcoes:
            self.assertTrue(item["url_nova"].startswith(NUA + "#art"), item)
            self.assertEqual(item["url_antiga"], COMP)

    def test_o_plano_registra_os_tres_que_NAO_sao_defeito(self):
        """`#art24`, `#art598` e `#art18` existem no compilado — ficam."""
        plano = json.loads(
            self.tool.DADOS.read_text(encoding="utf-8"))
        self.assertEqual(sorted(plano["nao_sao_defeito"]["fragmentos"]),
                         ["art18", "art24", "art598"])

    def test_o_estoque_real_ja_esta_reparado(self):
        """Depois de aplicado, rodar de novo não acha nada — trava a regressão."""
        tocados, _ = self.tool.aplica(self.tool.carrega_plano(), aplicar=False)
        self.assertEqual(tocados, 0, "o reparo de 2026-09-05 foi desfeito")


if __name__ == "__main__":
    unittest.main()
