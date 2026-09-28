#!/usr/bin/env python3
"""Precondição de ambiente da medição global e motivo persistido no relatório.

Contexto medido (2026-08-04, terceira ocorrência da família): o binário
cacheado da fábrica foi reconstruído às 09:41:04 e um agente concorrente
editou ``internal/v2stockepoch/lease.go`` às 09:45:45. A medição global rodou
depois disso, gastou a fase per-shard inteira (852 shards / 9.595 páginas) e só
então descobriu que o binário estava stale — reprovando os 852 shards por
``distinctness_index_unavailable``. 655 deles não tinham nenhum outro defeito.

Dois defeitos de engenharia, cobertos aqui:

1. a precondição de ambiente custa milissegundos e era avaliada DEPOIS da fase
   cara. Agora o modo global recusa antes de escanear, com o motivo real;
2. o relatório persistido reduzia os defeitos a ``{chave: quantidade}`` e
   descartava o motivo, tornando indistinguíveis um relatório envenenado por
   ambiente e um relatório de conteúdo ruim.

Nada aqui afrouxa o gate: a recusa continua sendo a mesma, e nenhum veredito
muda. Rodar: ``nice -n 19 python3 tools/test_audit_v2_pages_global_environment_precondition.py``
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import audit_v2_pages as auditor  # noqa: E402

AUDITOR_PATH = os.path.join(ROOT, 'tools', 'audit_v2_pages.py')


class GlobalEnvironmentPreconditionTest(unittest.TestCase):
    """A precondição fala pelo motivo REAL, e só quando há o que medir."""

    def setUp(self):
        self.original_root = auditor.ROOT

    def tearDown(self):
        auditor.ROOT = self.original_root

    def test_empty_finalized_stock_stays_silent(self):
        """Estoque vazio não tem medição a proteger — modo global segue lendo.

        Sem esta guarda, o modo global passaria a abortar em qualquer raiz sem
        binário cacheado (fixtures de contrato incluídas), trocando um
        relatório legítimo de estoque vazio por um erro.
        """
        with tempfile.TemporaryDirectory() as empty_root:
            os.makedirs(os.path.join(empty_root, 'data/editorial/v2_pages'))
            auditor.ROOT = empty_root
            self.assertIsNone(auditor.global_distinctness_environment_error())

    def test_stale_factory_is_reported_by_its_real_reason(self):
        """Fonte Go mais nova que o binário: motivo nomeia o arquivo culpado."""
        with tempfile.TemporaryDirectory() as fake_root:
            pages = os.path.join(fake_root, 'data/editorial/v2_pages')
            os.makedirs(pages)
            shard = os.path.join(pages, 'aereo-01.jsonl')
            with open(shard, 'w', encoding='utf-8') as handle:
                handle.write('{"intent_id": "x"}\n')
            auditor.ROOT = fake_root
            # O estoque agora é não-vazio, então a precondição consulta o
            # teste de confiança de verdade e propaga o motivo dele.
            self.assertTrue(auditor.is_finalized_v2_path(shard))
            observed = auditor.global_distinctness_environment_error()
            self.assertIsNotNone(
                observed,
                'estoque não-vazio sem cache de fábrica tem de recusar')
            self.assertEqual(
                observed, auditor.cached_factory_binary_error(),
                'a precondição não pode inventar motivo próprio: ela repete '
                'exatamente o veredito de cached_factory_binary_error')

    def test_cli_aborts_before_the_expensive_scan_with_exit_code_2(self):
        """A recusa é acionável e distinta de "medi e reprovou" (exit 1).

        O ``ROOT`` do CLI vem do local do script, então o auditor é copiado
        para dentro da raiz falsa — é assim que os testes de contrato em
        ``internal/contract/v2`` exercitam o modo global.
        """
        with tempfile.TemporaryDirectory() as fake_root:
            os.makedirs(os.path.join(fake_root, 'tools'))
            pages = os.path.join(fake_root, 'data/editorial/v2_pages')
            os.makedirs(pages)
            with open(os.path.join(pages, 'aereo-01.jsonl'), 'w',
                      encoding='utf-8') as handle:
                handle.write('{"intent_id": "x"}\n')
            copied = os.path.join(fake_root, 'tools', 'audit_v2_pages.py')
            with open(AUDITOR_PATH, 'rb') as source:
                payload = source.read()
            with open(copied, 'wb') as destination:
                destination.write(payload)
            completed = subprocess.run(
                [sys.executable, copied, '--global'],
                cwd=fake_root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(
                completed.returncode, 2,
                f'esperado exit 2 (nao medi), obtido {completed.returncode}: '
                f'{completed.stderr[:400]}')
            self.assertIn('ambiente de auditoria indisponivel',
                          completed.stderr)
            self.assertIn('tools/ensure-audit-ready', completed.stderr)
            self.assertEqual(
                completed.stdout, '',
                'a recusa nao pode emitir relatorio parcial no stdout')


class PersistedReasonTest(unittest.TestCase):
    """O relatório persistido separa ambiente de conteúdo."""

    def _summary_for(self, files):
        with tempfile.TemporaryDirectory() as directory:
            report = os.path.join(directory, 'report.jsonl')
            original_canonical = auditor.canonical_report_path
            auditor.canonical_report_path = lambda path: path
            try:
                auditor.persist_global_summary(
                    {'total_pages': 0, 'files': files}, report)
            finally:
                auditor.canonical_report_path = original_canonical
            with open(report, encoding='utf-8') as handle:
                lines = [line for line in handle.read().splitlines() if line]
        return json.loads(lines[-1])

    def test_unavailable_reason_survives_into_the_report(self):
        reason = 'cached_factory_stale:internal/v2stockepoch/lease.go'
        summary = self._summary_for({
            'data/editorial/v2_pages/aereo-01.jsonl': {
                'ok': False,
                'defects': {'distinctness_index_unavailable': [reason]},
                'distinctness_index': {
                    'status': 'global_batch_unavailable_fail_closed',
                    'reason': reason},
            },
            'data/editorial/v2_pages/aereo-02.jsonl': {
                'ok': False,
                'defects': {'distinctness_index_unavailable': [reason]},
                'distinctness_index': {
                    'status': 'global_batch_unavailable_fail_closed',
                    'reason': reason},
            },
        })
        self.assertEqual(
            summary['distinctness_index_status'],
            {'global_batch_unavailable_fail_closed': 2})
        self.assertEqual(summary['distinctness_index_reasons'], {reason: 2})
        self.assertEqual(summary['files_ok'], 0)

    def test_ready_index_is_recorded_without_reason(self):
        summary = self._summary_for({
            'data/editorial/v2_pages/aereo-01.jsonl': {
                'ok': True, 'defects': {},
                'distinctness_index': {'status': 'ready'},
            },
        })
        self.assertEqual(summary['distinctness_index_status'], {'ready': 1})
        self.assertEqual(summary['distinctness_index_reasons'], {})
        self.assertEqual(summary['files_ok'], 1)

    def test_empty_audit_still_persists_the_new_fields(self):
        """O contrato read-only chama com ``{'total_pages': 0, 'files': {}}``."""
        summary = self._summary_for({})
        self.assertEqual(summary['distinctness_index_status'], {})
        self.assertEqual(summary['distinctness_index_reasons'], {})
        self.assertEqual(summary['files_total'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
