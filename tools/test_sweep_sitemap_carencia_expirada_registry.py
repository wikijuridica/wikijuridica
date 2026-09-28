#!/usr/bin/env python3
"""Prova, em árvore sintética, que sweep-sitemap-carencia-expirada tomba o
ordinal no registry no INSTANTE em que remove o arquivo — a lacuna medida em
2026-09-03: pages-0035.xml estava retirado desde 2026-08-28T21:35:49Z e o
ordinal 35 não existia em NENHUMA chave de `data/ops/sitemap_shard_registry.json`
(nem `assigned`, nem `tombstones`). `SeedFromPlan` só semeia a partir do plano
AO VIVO (plan.Shards); um shard já em carência no instante da semeadura nunca
ganha chave — sem chave, `Retire`/`ExpireRetired` (que só o publish chama)
NUNCA alcançam esse ordinal.

Este teste exercita o CÓDIGO REAL do sweep (importado do arquivo, sem
reimplementar nada), sobre uma árvore temporária, com o relógio injetado via
`sweep.agora_utc` — nunca dependendo de um shard real vencer (o real vence em
2026-09-05, dois dias depois de este teste ter sido escrito).

Cobre os quatro casos que importam:
  1. ordinal ÓRFÃO (sem chave em assigned) vencido -> tombado DIRETO.
  2. ordinal com CHAVE em assigned+retired, vencido -> tombado pela chave
     (assigned e retired perdem a chave; tombstones ganha o número).
  3. ordinal AINDA em carência -> nada é removido, nada é tombado.
  4. --seco -> relata o que tombaria, não escreve nem remove nada.
  5. chave em assigned que NÃO está em retired -> não tomba (inconsistência
     relatada, nunca silenciada).
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
from datetime import datetime, timezone
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = str(RAIZ / "tools" / "sweep-sitemap-carencia-expirada")
_LOADER = SourceFileLoader("sweep_carencia_registry_test_subject", _ALVO)
_SPEC = importlib.util.spec_from_loader("sweep_carencia_registry_test_subject", _LOADER)
sweep = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(sweep)


def _escreve_shard(caminho: str, locs: list[str], retirado_em: str | None = None) -> None:
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>']
    if retirado_em:
        linhas.append(f"<!-- {sweep.MARCA} retirado-em={retirado_em} motivo=teste-sintetico -->")
    linhas.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc in locs:
        linhas.append(f"  <url><loc>{loc}</loc></url>")
    linhas.append("</urlset>")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as handle:
        handle.write("\n".join(linhas) + "\n")


def _escreve_indice(nomes_indexados: list[str]) -> None:
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for nome in nomes_indexados:
        linhas.append(f"  <sitemap><loc>https://e.com/sitemaps/{nome}</loc></sitemap>")
    linhas.append("</sitemapindex>")
    with open("public/sitemap.xml", "w", encoding="utf-8") as handle:
        handle.write("\n".join(linhas) + "\n")


def _escreve_registry(assigned: dict, retired: dict, tombstones=None, next_id: int = 100) -> None:
    registro = {
        "next_id": next_id,
        "assigned": assigned,
        "tombstones": tombstones,
        "retired": retired,
        "schema_version": "sitemap_shard_registry_v1",
    }
    os.makedirs(os.path.dirname(sweep.REGISTRY), exist_ok=True)
    with open(sweep.REGISTRY, "w", encoding="utf-8") as handle:
        json.dump(registro, handle, ensure_ascii=False)


class ArvoreSinteticaTestCase(unittest.TestCase):
    """Base: cwd numa árvore temporária, porque sweep usa caminhos relativos
    (SHARDS/INDICE/REGISTRY) — é o mesmo regime em que ele roda de verdade
    (ExecStartPre, cwd = raiz do repositório)."""

    def setUp(self) -> None:
        self._cwd_original = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="sweep-carencia-registry-")
        os.chdir(self._tmp)
        os.makedirs("public/sitemaps", exist_ok=True)
        os.makedirs("data/ops", exist_ok=True)
        self._agora_original = sweep.agora_utc
        self._argv_original = sys.argv

    def tearDown(self) -> None:
        sweep.agora_utc = self._agora_original
        sys.argv = self._argv_original
        os.chdir(self._cwd_original)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def fixa_agora(self, ano, mes, dia, hora=12):
        sweep.agora_utc = lambda: datetime(ano, mes, dia, hora, 0, 0, tzinfo=timezone.utc)

    def registry_atual(self):
        with open(sweep.REGISTRY, encoding="utf-8") as handle:
            return json.load(handle)


class TestOrdinalOrfaoTombadoDireto(ArvoreSinteticaTestCase):
    """O CASO REAL de 2026-09-03: ordinal sem NENHUMA chave em `assigned`."""

    def test_removido_e_tombado(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/a/"])
        _escreve_shard("public/sitemaps/pages-0035.xml", ["https://e.com/a/"],
                        retirado_em="2026-08-25T12:00:00Z")
        _escreve_registry(assigned={"2026-08-28|familia#0": 47}, retired={})

        self.fixa_agora(2026, 9, 6)  # 12 dias depois de retirado > 8 dias de carência
        sys.argv = ["sweep-sitemap-carencia-expirada"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        self.assertFalse(os.path.exists("public/sitemaps/pages-0035.xml"),
                          "shard vencido deveria ter sido removido")
        depois = self.registry_atual()
        self.assertEqual(depois["tombstones"], [35], depois)
        self.assertNotIn(35, depois["assigned"].values())
        # A chave que já existia (viva) não pode ter sido tocada.
        self.assertEqual(depois["assigned"].get("2026-08-28|familia#0"), 47)

    def test_idempotente_rodar_duas_vezes(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/a/"])
        _escreve_shard("public/sitemaps/pages-0035.xml", ["https://e.com/a/"],
                        retirado_em="2026-08-25T12:00:00Z")
        _escreve_registry(assigned={}, retired={})
        self.fixa_agora(2026, 9, 6)
        sys.argv = ["sweep-sitemap-carencia-expirada"]

        self.assertEqual(sweep.main(), 0)
        primeira = self.registry_atual()
        # Segunda execução: o shard já não existe em disco (nada a varrer para
        # ele), e o tombstone já gravado não pode duplicar nem sumir.
        self.assertEqual(sweep.main(), 0)
        segunda = self.registry_atual()
        self.assertEqual(primeira["tombstones"], segunda["tombstones"])
        self.assertEqual(segunda["tombstones"], [35])


class TestOrdinalComChaveTombadoPelaChave(ArvoreSinteticaTestCase):
    """Caminho normal: a chave já existia em `assigned` e `retired` (o
    registry sempre soube da coorte) — mesma lógica de ExpireRetired, só que
    disparada pela remoção física em vez de por um publish."""

    def test_remove_a_chave_de_assigned_e_retired(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/b/"])
        _escreve_shard("public/sitemaps/pages-0040.xml", ["https://e.com/b/"],
                        retirado_em="2026-08-20T09:00:00Z")
        chave = "2026-08-20|trabalhista#0"
        _escreve_registry(
            assigned={chave: 40, "2026-08-28|familia#0": 47},
            retired={chave: "2026-08-20T09:00:00Z"},
        )
        self.fixa_agora(2026, 9, 6)
        sys.argv = ["sweep-sitemap-carencia-expirada"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        self.assertFalse(os.path.exists("public/sitemaps/pages-0040.xml"))
        depois = self.registry_atual()
        self.assertEqual(depois["tombstones"], [40], depois)
        self.assertNotIn(chave, depois["assigned"])
        self.assertNotIn(chave, depois["retired"])
        self.assertEqual(depois["assigned"].get("2026-08-28|familia#0"), 47)


class TestAindaEmCarenciaNaoTocaNada(ArvoreSinteticaTestCase):
    def test_nao_remove_nem_tomba(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/c/"])
        _escreve_shard("public/sitemaps/pages-0035.xml", ["https://e.com/c/"],
                        retirado_em="2026-09-01T12:00:00Z")  # 2 dias atrás
        _escreve_registry(assigned={}, retired={})
        self.fixa_agora(2026, 9, 3, hora=12)  # só 2 dias de carência corrida
        sys.argv = ["sweep-sitemap-carencia-expirada"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        self.assertTrue(os.path.exists("public/sitemaps/pages-0035.xml"),
                         "shard AINDA em carência não pode ser removido")
        depois = self.registry_atual()
        self.assertIsNone(depois["tombstones"])


class TestSecoNaoEscreveNadaNoRegistry(ArvoreSinteticaTestCase):
    def test_seco_so_relata(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/d/"])
        _escreve_shard("public/sitemaps/pages-0035.xml", ["https://e.com/d/"],
                        retirado_em="2026-08-25T12:00:00Z")
        _escreve_registry(assigned={}, retired={})
        self.fixa_agora(2026, 9, 6)
        sys.argv = ["sweep-sitemap-carencia-expirada", "--seco"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        self.assertTrue(os.path.exists("public/sitemaps/pages-0035.xml"),
                         "--seco não pode remover nada do disco")
        depois = self.registry_atual()
        self.assertIsNone(depois["tombstones"], "--seco não pode escrever no registry")

    def test_seco_preserva_tombstones_ja_existentes_intactos(self):
        # A lacuna que os dois testes acima NÃO fecham: os dois partem de
        # tombstones vazio, então uma reescrita acidental que "voltasse vazio"
        # passaria despercebida. Aqui o registry JÁ tem conteúdo em
        # tombstones -- --seco tem de devolver-lo EXATAMENTE como estava,
        # nunca reescrito, nunca com o ordinal novo somado.
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/d/"])
        _escreve_shard("public/sitemaps/pages-0035.xml", ["https://e.com/d/"],
                        retirado_em="2026-08-25T12:00:00Z")
        _escreve_registry(assigned={"2026-08-01|leis#0": 10}, retired={},
                           tombstones=[3, 10])
        self.fixa_agora(2026, 9, 6)
        sys.argv = ["sweep-sitemap-carencia-expirada", "--seco"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        depois = self.registry_atual()
        self.assertEqual(depois["tombstones"], [3, 10],
                          "--seco alterou tombstones que já existiam no registry")
        self.assertEqual(depois["assigned"], {"2026-08-01|leis#0": 10})


class TestChaveSemMarcaRetiredNaoTomba(ArvoreSinteticaTestCase):
    """FALSO POSITIVO OBRIGATÓRIO: o disco diz que o shard está retirado, mas
    o registry NUNCA marcou a chave dona como `retired`. As duas fontes
    discordam — tombar aqui seria mascarar a discordância, não resolvê-la."""

    def test_avisa_e_nao_tomba(self):
        _escreve_indice(["pages-0100.xml"])
        _escreve_shard("public/sitemaps/pages-0100.xml", ["https://e.com/e/"])
        _escreve_shard("public/sitemaps/pages-0041.xml", ["https://e.com/e/"],
                        retirado_em="2026-08-20T09:00:00Z")
        chave = "2026-08-20|consumidor#0"
        # A chave existe em assigned com o ordinal certo, mas NUNCA foi
        # marcada retired — inconsistência deliberada para este teste.
        _escreve_registry(assigned={chave: 41}, retired={})
        self.fixa_agora(2026, 9, 6)
        sys.argv = ["sweep-sitemap-carencia-expirada"]
        codigo = sweep.main()

        self.assertEqual(codigo, 0)
        # O ARQUIVO ainda é removido (a carência do arquivo, por si, venceu e
        # todas as URLs estão cobertas pelo plano vivo) — só o TOMBAMENTO no
        # registry é que se recusa, porque é ele que seria inventado.
        self.assertFalse(os.path.exists("public/sitemaps/pages-0041.xml"))
        depois = self.registry_atual()
        self.assertIsNone(depois["tombstones"], depois)
        self.assertEqual(depois["assigned"].get(chave), 41,
                          "a chave inconsistente não pode ter sido tocada")


class TestFuncaoTombaDiretamente(unittest.TestCase):
    """Exercita tomba_ordinal_expirado isoladamente, sem depender de main()
    nem de arquivo em disco — cobre o guard de next_id e o de já-tombado."""

    def setUp(self):
        self._cwd_original = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="sweep-carencia-fn-")
        os.chdir(self._tmp)
        os.makedirs("data/ops", exist_ok=True)

    def tearDown(self):
        os.chdir(self._cwd_original)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_ordinal_ja_tombado_e_nao_op(self):
        _escreve_registry(assigned={}, retired={}, tombstones=[35])
        relato = sweep.tomba_ordinal_expirado(35, seco=False)
        self.assertIn("ja tombado", relato)
        depois = json.load(open(sweep.REGISTRY, encoding="utf-8"))
        self.assertEqual(depois["tombstones"], [35])

    def test_ordinal_acima_de_next_id_recusa(self):
        _escreve_registry(assigned={}, retired={}, next_id=10)
        relato = sweep.tomba_ordinal_expirado(35, seco=False)
        self.assertIn("AVISO", relato)
        self.assertIn("next_id", relato)
        depois = json.load(open(sweep.REGISTRY, encoding="utf-8"))
        self.assertIsNone(depois["tombstones"])

    def test_sem_registry_devolve_none(self):
        # Nenhum arquivo em data/ops/: sweep continua funcionando sem
        # registry, exatamente como antes de ele existir.
        self.assertIsNone(sweep.tomba_ordinal_expirado(35, seco=False))


def main() -> int:
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
