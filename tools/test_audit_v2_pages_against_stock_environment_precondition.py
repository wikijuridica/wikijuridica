#!/usr/bin/env python3
"""Precondição de ambiente do modo --against-stock (causa-raiz 2026-08-12).

Contexto medido ao vivo (onda de 6 lotes redigida em 2026-08-12): o lote
``tributario-viz1-01`` reprovou na autoauditoria (regra 8 de
``scripts/workflows/writing-mass.js``) com
``distinctness_index_unavailable: ["cached_factory_stale:module_metadata"]``
sem NENHUM outro defeito -- ou seja, defeito de AMBIENTE (binario/indice
cacheado da fabrica ficou stale porque outro agente concorrente tocou Go),
nao de conteudo da pagina. Antes deste teste, o modo ``--against-stock``
descobria isso tarde, DENTRO de ``query_incremental_distinctness`` (depois de
``audit_file`` ja ter rodado a auditoria de conteudo inteira do shard), e
devolvia o MESMO exit 1 e a MESMA forma ``{ok: false, defects: {...}}`` que
uma pagina com defeito de conteudo real -- o chamador (redator,
``measure-v2-approval-rate``, ``finalize-v2-review``) nao tinha como
distinguir sem abrir o JSON e comparar a chave do defeito a mao. O modo
``--global`` ja resolvia isso (``global_distinctness_environment_error`` +
exit 2); este teste prova que ``--against-stock`` agora espelha o MESMO
contrato: mesma funcao de deteccao (``cached_factory_binary_error``), mesmo
exit code 2, stdout vazio (nunca relatorio parcial), mensagem apontando para
``tools/ensure-audit-ready``.

Isto NAO afrouxa o gate: nenhum veredito de conteudo muda -- shard com
defeito real continua saindo com exit 1 e o JSON de sempre quando o ambiente
esta ok. A verificacao tardia dentro de ``query_incremental_distinctness``
continua de pe (corrida residual: edicao Go pousando NO MEIO desta auditoria)
e nao e alterada por este teste.

Rodar: nice -n 19 python3 tools/test_audit_v2_pages_against_stock_environment_precondition.py
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import audit_v2_pages as auditor  # noqa: E402

AUDITOR_PATH = os.path.join(ROOT, 'tools', 'audit_v2_pages.py')


class AgainstStockEnvironmentPreconditionTest(unittest.TestCase):
    """--against-stock deixa de misturar falha de ambiente com defeito real."""

    def _run_main_with_argv(self, argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(sys, 'argv', ['audit_v2_pages.py', *argv]), \
                contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                auditor.main()
        return ctx.exception.code, stdout.getvalue(), stderr.getvalue()

    def test_stale_factory_aborts_before_content_audit_with_exit_code_2(self):
        """Ambiente indisponivel: exit 2, stdout vazio, motivo real no stderr.

        ``audit_against_stock`` nunca deveria ser chamado -- a falha de
        ambiente e detectada e reportada ANTES da auditoria de conteudo cara.
        """
        with mock.patch.object(
                auditor, 'cached_factory_binary_error',
                return_value='cached_factory_stale:module_metadata'), \
                mock.patch.object(
                    auditor, 'audit_against_stock') as fake_audit:
            code, out, err = self._run_main_with_argv(
                ['/opt/wiki/data/editorial/v2_pages/tributario-viz1-01.jsonl',
                 '--expect-n', '9', '--against-stock'])
        fake_audit.assert_not_called()
        self.assertEqual(
            code, 2,
            f'esperado exit 2 (ambiente, nao conteudo), obtido {code}: {err[:400]}')
        self.assertEqual(
            out, '',
            'a recusa de ambiente nao pode emitir relatorio parcial no stdout')
        self.assertIn('ambiente de auditoria indisponivel', err)
        self.assertIn('cached_factory_stale:module_metadata', err)
        self.assertIn('tools/ensure-audit-ready', err)

    def test_fresh_environment_reaches_the_real_content_audit_unchanged(self):
        """Ambiente ok: comportamento identico ao de antes desta correcao."""
        canned = {
            'file': 'data/editorial/v2_pages/tributario-viz1-01.jsonl',
            'pages': 9, 'active_pages': 9, 'defects': {}, 'ok': True,
            'distinctness_index': {'status': 'ready'},
        }
        with mock.patch.object(
                auditor, 'cached_factory_binary_error', return_value=None), \
                mock.patch.object(
                    auditor, 'audit_against_stock',
                    return_value=canned) as fake_audit:
            code, out, err = self._run_main_with_argv(
                ['/opt/wiki/data/editorial/v2_pages/tributario-viz1-01.jsonl',
                 '--expect-n', '9', '--against-stock'])
        fake_audit.assert_called_once_with(
            '/opt/wiki/data/editorial/v2_pages/tributario-viz1-01.jsonl', 9)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), canned)

    def test_fresh_environment_still_exits_1_on_real_content_defect(self):
        """Ambiente ok mas pagina ruim: exit 1 continua identico a hoje."""
        canned = {
            'file': 'data/editorial/v2_pages/tributario-viz1-01.jsonl',
            'pages': 9, 'active_pages': 9,
            'defects': {'thin_content': ['tributario-viz1-01:3']},
            'ok': False,
        }
        with mock.patch.object(
                auditor, 'cached_factory_binary_error', return_value=None), \
                mock.patch.object(
                    auditor, 'audit_against_stock', return_value=canned):
            code, out, err = self._run_main_with_argv(
                ['/opt/wiki/data/editorial/v2_pages/tributario-viz1-01.jsonl',
                 '--expect-n', '9', '--against-stock'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)['defects'], canned['defects'])

    def test_cli_subprocess_without_cached_factory_aborts_with_exit_2(self):
        """Ponta a ponta: processo real, sem cache de fabrica, root isolado."""
        with tempfile.TemporaryDirectory() as fake_root:
            os.makedirs(os.path.join(fake_root, 'tools'))
            pages = os.path.join(fake_root, 'data/editorial/v2_pages')
            os.makedirs(pages)
            shard = os.path.join(pages, 'aereo-01.jsonl')
            with open(shard, 'w', encoding='utf-8') as handle:
                handle.write('{"intent_id": "x"}\n')
            copied = os.path.join(fake_root, 'tools', 'audit_v2_pages.py')
            with open(AUDITOR_PATH, 'rb') as source:
                payload = source.read()
            with open(copied, 'wb') as destination:
                destination.write(payload)
            completed = subprocess.run(
                [sys.executable, copied, shard, '--expect-n', '1',
                 '--against-stock'],
                cwd=fake_root, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(
                completed.returncode, 2,
                f'esperado exit 2 (nao medi), obtido {completed.returncode}: '
                f'{completed.stderr[:400]}')
            self.assertEqual(completed.stdout, '')
            self.assertIn('tools/ensure-audit-ready', completed.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
