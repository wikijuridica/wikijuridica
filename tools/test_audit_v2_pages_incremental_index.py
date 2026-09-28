#!/usr/bin/env python3
"""Índice incremental persistente da fase per-shard de ``_audit_global``.

Antes deste índice, ``--global`` reauditava (relia + rehasheava + reparseava a
prosa de) TODOS os shards a cada invocação. Repetido por evento/onda, isso é o
rescan full-corpus O(eventos × N) que estoura memória/tempo no corpus grande.

Estes testes travam as duas propriedades que tornam o índice correto e útil:

1. Equivalência (a auditoria NÃO é relaxada): o veredito reduzido servido do
   cache (execução quente) é byte-idêntico, após JSON canônico, ao veredito
   recomputado a frio. O cache é invisível ao resultado.

2. O(delta): a 2ª execução sobre um corpus inalterado não reaudita shard algum
   (short-circuit de delta vazio); alterar 1 shard reaudita exatamente 1.

Roda em modo serial in-process (``AUDIT_V2_SERIAL=1``) para que o contador de
``audit_file`` observe cada reauditoria real, sem depender do pool de processos.
"""

import json
import os
import shutil
import tempfile
import unittest

from tools import audit_v2_pages as audit


def _canonical(value):
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


class IncrementalShardIndexTests(unittest.TestCase):
    def setUp(self):
        self._saved_root = audit.ROOT
        self._saved_serial = os.environ.get('AUDIT_V2_SERIAL')
        self._saved_audit_file = audit.audit_file
        self._saved_fingerprint = audit._SHARD_SIDECAR_SOURCE_FINGERPRINT
        os.environ['AUDIT_V2_SERIAL'] = '1'
        self.tmp = tempfile.mkdtemp(prefix='audit-incremental-')
        audit.ROOT = self.tmp
        self.pages_dir = os.path.join(
            self.tmp, 'data', 'editorial', 'v2_pages')
        os.makedirs(self.pages_dir, exist_ok=True)

        self.audit_calls = []
        real_audit_file = self._saved_audit_file

        def counting_audit_file(path, portfolio, *args, **kwargs):
            self.audit_calls.append(os.path.basename(path))
            return real_audit_file(path, portfolio, *args, **kwargs)

        audit.audit_file = counting_audit_file

    def tearDown(self):
        audit.ROOT = self._saved_root
        audit.audit_file = self._saved_audit_file
        audit._SHARD_SIDECAR_SOURCE_FINGERPRINT = self._saved_fingerprint
        if self._saved_serial is None:
            os.environ.pop('AUDIT_V2_SERIAL', None)
        else:
            os.environ['AUDIT_V2_SERIAL'] = self._saved_serial
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_shard(self, name, intent, body):
        page = {
            'intent_id': intent,
            'title': f'Titulo juridico unico de {intent} para o corpus',
            'meta_description': (
                f'Descricao unica e informativa da pagina {intent} usada '
                'apenas para exercitar o indice incremental do auditor.'),
            'h1': f'Cabecalho visivel exclusivo de {intent}',
            'opening': body,
            'sections': [{'heading': f'Bloco de {intent}', 'text': body}],
            'faq': [],
        }
        path = os.path.join(self.pages_dir, name)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(json.dumps(page, ensure_ascii=False) + '\n')
        return path

    def _files(self):
        return sorted(
            os.path.join(self.pages_dir, name)
            for name in os.listdir(self.pages_dir)
            if name.endswith('.jsonl'))

    def test_warm_run_is_verdict_identical_and_o_delta(self):
        self._write_shard('civil-a.jsonl', 'civ-a', 'conteudo autoral um')
        self._write_shard('civil-b.jsonl', 'civ-b', 'conteudo autoral dois')
        self._write_shard('civil-c.jsonl', 'civ-c', 'conteudo autoral tres')
        files = self._files()
        portfolio = {}

        # Execução fria: audita os 3 shards e persiste o índice.
        self.audit_calls.clear()
        cold = audit._run_per_shard_audits(files, portfolio)
        self.assertEqual(sorted(self.audit_calls), [
            'civil-a.jsonl', 'civil-b.jsonl', 'civil-c.jsonl'])
        self.assertTrue(os.path.exists(audit._shard_sidecar_path()))

        # Execução quente sem mudança: delta vazio -> nenhuma reauditoria.
        self.audit_calls.clear()
        warm = audit._run_per_shard_audits(files, portfolio)
        self.assertEqual(self.audit_calls, [],
                         'delta vazio releu/reauditou o corpus')

        # Equivalência: o cache é invisível ao veredito (JSON canônico igual).
        self.assertEqual(set(cold), set(warm))
        for path in files:
            self.assertEqual(_canonical(cold[path]), _canonical(warm[path]),
                             f'veredito quente divergiu do frio em {path}')

        # Alterar 1 shard reaudita exatamente 1 (delta de tamanho 1).
        self._write_shard(
            'civil-b.jsonl', 'civ-b',
            'conteudo autoral dois totalmente reescrito com outro tamanho')
        self.audit_calls.clear()
        delta = audit._run_per_shard_audits(files, portfolio)
        self.assertEqual(self.audit_calls, ['civil-b.jsonl'],
                         'delta de 1 shard nao ficou O(delta)')
        # Os 2 shards inalterados continuam vindo do cache, idênticos ao frio.
        for path in files:
            if os.path.basename(path) == 'civil-b.jsonl':
                continue
            self.assertEqual(_canonical(cold[path]), _canonical(delta[path]))

    def test_header_mismatch_forces_full_reaudit(self):
        self._write_shard('civil-a.jsonl', 'civ-a', 'conteudo autoral um')
        self._write_shard('civil-b.jsonl', 'civ-b', 'conteudo autoral dois')
        files = self._files()

        self.audit_calls.clear()
        audit._run_per_shard_audits(files, {})
        self.assertEqual(len(self.audit_calls), 2)

        # Portfólio diferente -> fingerprint de cabeçalho diferente -> o índice
        # antigo é descartado e tudo é reauditado (nunca serve veredito de
        # outra época/entrada).
        self.audit_calls.clear()
        audit._run_per_shard_audits(files, {'civ-a': {'lane': 'informativa'}})
        self.assertEqual(len(self.audit_calls), 2,
                         'cabecalho divergente reaproveitou cache indevido')

    def test_corrupt_index_is_fail_safe(self):
        self._write_shard('civil-a.jsonl', 'civ-a', 'conteudo autoral um')
        files = self._files()
        audit._run_per_shard_audits(files, {})

        # Índice corrompido -> miss total -> re-auditoria, nunca crash.
        with open(audit._shard_sidecar_path(), 'w', encoding='utf-8') as handle:
            handle.write('{ truncado nao-json')
        self.audit_calls.clear()
        result = audit._run_per_shard_audits(files, {})
        self.assertEqual(self.audit_calls, ['civil-a.jsonl'])
        self.assertEqual(set(result), set(files))


if __name__ == '__main__':
    unittest.main()
