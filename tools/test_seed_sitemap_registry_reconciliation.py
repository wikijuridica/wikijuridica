#!/usr/bin/env python3
"""Prova, em árvore sintética, a reconciliação e a adoção de
tools/seed-sitemap-registry — sem depender do Go (a suíte foca na lógica
Python nova; a cobertura do plano vivo já é coberta por
cmd/seed-sitemap-registry e por ./tools/go-modern test ./internal/sitemap/).

O CASO REAL (2026-09-03): pages-0035.xml retirado em disco, ordinal 35 sem
NENHUMA chave em `assigned` — `reconcilia()` tem de classificá-lo como órfão,
e `cmd_adotar_orfaos` tem de dar a ele uma chave sintética estável que o
registry (e, depois, o ExpireRetired do Go) consiga rotear normalmente.

Cobre:
  1. órfão puro (sem chave nenhuma) -> reconcilia como órfão; adoção grava
     assigned+retired com a MESMA marca de disco, byte a byte.
  2. conhecido por tombstone -> não aparece como órfão nem inconsistente.
  3. conhecido por chave já retirada -> idem.
  4. inconsistente (chave existe, não está em retired) -> categoria própria,
     NUNCA adotada automaticamente.
  5. --seco não escreve nada.
  6. ordinal órfão >= next_id -> guarda recusa (não inventa alocação).
  7. adoção é idempotente: rodar duas vezes não duplica nem desloca nada.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = str(RAIZ / "tools" / "seed-sitemap-registry")
_LOADER = SourceFileLoader("seed_sitemap_registry_test_subject", _ALVO)
_SPEC = importlib.util.spec_from_loader("seed_sitemap_registry_test_subject", _LOADER)
seedreg = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(seedreg)


def _escreve_shard(diretorio: str, nome: str, retirado_em: str | None) -> None:
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>']
    if retirado_em:
        linhas.append(f"<!-- {seedreg.MARCA} retirado-em={retirado_em} motivo=teste-sintetico -->")
    linhas.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    linhas.append("  <url><loc>https://e.com/x/</loc></url>")
    linhas.append("</urlset>")
    with open(os.path.join(diretorio, nome), "w", encoding="utf-8") as handle:
        handle.write("\n".join(linhas) + "\n")


class ReconciliacaoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="seed-sitemap-registry-")
        self._shards_original = seedreg.SHARDS
        self._registry_original = seedreg.REGISTRY
        seedreg.SHARDS = os.path.join(self._tmp, "public", "sitemaps")
        seedreg.REGISTRY = os.path.join(self._tmp, "data", "ops", "sitemap_shard_registry.json")
        os.makedirs(seedreg.SHARDS, exist_ok=True)
        os.makedirs(os.path.dirname(seedreg.REGISTRY), exist_ok=True)

    def tearDown(self) -> None:
        seedreg.SHARDS = self._shards_original
        seedreg.REGISTRY = self._registry_original
        shutil.rmtree(self._tmp, ignore_errors=True)

    def escreve_registry(self, assigned, retired, tombstones=None, next_id=100):
        registro = {
            "next_id": next_id, "assigned": assigned, "tombstones": tombstones,
            "retired": retired, "schema_version": "sitemap_shard_registry_v1",
        }
        with open(seedreg.REGISTRY, "w", encoding="utf-8") as handle:
            json.dump(registro, handle, ensure_ascii=False)
        return registro

    def registry_atual(self):
        with open(seedreg.REGISTRY, encoding="utf-8") as handle:
            return json.load(handle)


class TestReconcilia(ReconciliacaoTestCase):
    def test_orfao_puro(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        registro = self.escreve_registry(assigned={"2026-08-28|familia#0": 47}, retired={})
        conhecidos, orfaos, inconsistentes = seedreg.reconcilia(registro)
        self.assertEqual(len(conhecidos), 0)
        self.assertEqual(len(inconsistentes), 0)
        self.assertEqual(len(orfaos), 1)
        self.assertEqual(orfaos[0]["ordinal"], 35)
        self.assertEqual(orfaos[0]["retirado_em"], "2026-08-28T21:35:49Z")

    def test_conhecido_por_tombstone(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        registro = self.escreve_registry(assigned={}, retired={}, tombstones=[35])
        conhecidos, orfaos, inconsistentes = seedreg.reconcilia(registro)
        self.assertEqual(len(orfaos), 0)
        self.assertEqual(len(inconsistentes), 0)
        self.assertEqual(len(conhecidos), 1)
        self.assertEqual(conhecidos[0]["via"], "tombstone")

    def test_conhecido_por_chave_retirada(self):
        _escreve_shard(seedreg.SHARDS, "pages-0040.xml", "2026-08-20T09:00:00Z")
        chave = "2026-08-20|trabalhista#0"
        registro = self.escreve_registry(
            assigned={chave: 40}, retired={chave: "2026-08-20T09:00:00Z"})
        conhecidos, orfaos, inconsistentes = seedreg.reconcilia(registro)
        self.assertEqual(len(orfaos), 0)
        self.assertEqual(len(inconsistentes), 0)
        self.assertEqual(len(conhecidos), 1)
        self.assertEqual(conhecidos[0]["via"], "chave")
        self.assertEqual(conhecidos[0]["chave"], chave)

    def test_inconsistente_chave_sem_retired(self):
        _escreve_shard(seedreg.SHARDS, "pages-0041.xml", "2026-08-20T09:00:00Z")
        chave = "2026-08-20|consumidor#0"
        registro = self.escreve_registry(assigned={chave: 41}, retired={})
        conhecidos, orfaos, inconsistentes = seedreg.reconcilia(registro)
        self.assertEqual(len(orfaos), 0)
        self.assertEqual(len(conhecidos), 0)
        self.assertEqual(len(inconsistentes), 1)
        self.assertEqual(inconsistentes[0]["chaves_nao_retiradas"], [chave])

    def test_shard_ativo_sem_marca_fica_fora(self):
        _escreve_shard(seedreg.SHARDS, "pages-0100.xml", retirado_em=None)
        registro = self.escreve_registry(assigned={}, retired={})
        conhecidos, orfaos, inconsistentes = seedreg.reconcilia(registro)
        self.assertEqual((len(conhecidos), len(orfaos), len(inconsistentes)), (0, 0, 0))


class TestAdotarOrfaos(ReconciliacaoTestCase):
    def test_adota_e_grava_marca_identica_ao_disco(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        self.escreve_registry(assigned={"2026-08-28|familia#0": 47},
                               retired={"2026-08-28|familia#0": "2026-08-29T00:19:12Z"})

        codigo = seedreg.cmd_adotar_orfaos(seco=False)
        self.assertEqual(codigo, 0)

        depois = self.registry_atual()
        chave = seedreg.chave_sintetica("pages-0035.xml")
        self.assertEqual(depois["assigned"].get(chave), 35)
        self.assertEqual(depois["retired"].get(chave), "2026-08-28T21:35:49Z",
                          "o carimbo adotado tem de ser BYTE A BYTE o que estava no disco")
        # A chave que já existia não pode ter sido tocada.
        self.assertEqual(depois["assigned"].get("2026-08-28|familia#0"), 47)
        self.assertEqual(depois["retired"].get("2026-08-28|familia#0"), "2026-08-29T00:19:12Z")

    def test_seco_nao_escreve(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        antes = self.escreve_registry(assigned={}, retired={})
        codigo = seedreg.cmd_adotar_orfaos(seco=True)
        self.assertEqual(codigo, 0)
        depois = self.registry_atual()
        self.assertEqual(depois["assigned"], antes["assigned"])
        self.assertEqual(depois["retired"], antes["retired"])

    def test_nao_adota_inconsistente(self):
        _escreve_shard(seedreg.SHARDS, "pages-0041.xml", "2026-08-20T09:00:00Z")
        chave = "2026-08-20|consumidor#0"
        self.escreve_registry(assigned={chave: 41}, retired={})  # inconsistente, não órfão
        codigo = seedreg.cmd_adotar_orfaos(seco=False)
        self.assertEqual(codigo, 0)  # "nada a adotar", não é erro
        depois = self.registry_atual()
        self.assertNotIn(chave, depois["retired"], "inconsistente não pode ser adotado por engano")

    def test_ordinal_acima_de_next_id_nao_adota(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        self.escreve_registry(assigned={}, retired={}, next_id=10)  # 35 >= 10
        codigo = seedreg.cmd_adotar_orfaos(seco=False)
        self.assertEqual(codigo, 1)  # todos os candidatos foram recusados
        depois = self.registry_atual()
        self.assertEqual(depois["assigned"], {})

    def test_idempotente(self):
        _escreve_shard(seedreg.SHARDS, "pages-0035.xml", "2026-08-28T21:35:49Z")
        self.escreve_registry(assigned={}, retired={})
        seedreg.cmd_adotar_orfaos(seco=False)
        primeira = self.registry_atual()
        # Na segunda passada o ordinal já está "conhecido" (via chave, agora
        # que foi adotado) — reconcilia() não deve mais classificá-lo como
        # órfão, então cmd_adotar_orfaos não tem nada a fazer.
        codigo = seedreg.cmd_adotar_orfaos(seco=False)
        self.assertEqual(codigo, 0)
        segunda = self.registry_atual()
        self.assertEqual(primeira["assigned"], segunda["assigned"])
        self.assertEqual(primeira["retired"], segunda["retired"])
        self.assertEqual(len(segunda["assigned"]), 1)


def main() -> int:
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
