#!/usr/bin/env python3
"""Guarda: as duas ocorrencias da projecao de fontes no prompt sao idênticas.

CONTEXTO (2026-08-12): um redator do lote "glossario-12" relatou, em
auditoria byte-a-byte, que a string base64 embutida no COMANDO DE PROMOCAO
(regra 6, segunda ocorrencia) estava corrompida -- faltando o campo ``url``
da fonte ``prov-cnj-65-2017-usucapiao-extrajudicial`` -- e que ele usou em
seu lugar a string do PREFLIGHT (primeira ocorrencia).

INVESTIGACAO (evidencia, nao opiniao): ``scripts/workflows/writing-mass.js``
computa a projecao ``sourceResolutionProjection`` UMA UNICA VEZ (a const na
funcao ``writePrompt``) e a interpola LITERALMENTE DUAS VEZES no mesmo prompt
-- na etapa de preflight (regra 6, inicio) e dentro do comando de promocao
(regra 6, ``dependencyRecheck``/``stagedSourceResolutionPreflight``). Sendo a
MESMA variavel JS reinterpolada, as duas ocorrencias SAO estruturalmente
incapazes de divergir uma da outra dentro de um unico prompt gerado.

Materializando o prompt real do lote "glossario-12" com a ferramenta
sancionada (``tools/generate-writing-prompt-dump``, que avalia o MESMO
codigo que o harness usaria) -- tanto na geracao atual
(``scripts/workflows/writing-mass-todo.js``, commit 170cecc4) quanto na
geracao imediatamente anterior (commit 7482a8ab, antes da regeneracao de
hoje) -- as duas projecoes de ``source_overrides``/``strict_source_intents``
sao BYTE-IDENTICAS, e a fonte ``prov-cnj-65-2017-usucapiao-extrajudicial``
tem ``url`` presente e não vazio em ambas. O "gap" relatado nao reproduz.

Este teste e um GUARDA de regressao, nao a reproducao de um bug: ele passa
HOJE porque o defeito relatado nao existe na fila viva, e reprovaria se uma
mudanca futura em writing-mass.js voltar a computar a projecao duas vezes
por caminhos distintos (a causa estrutural que, se existisse, permitiria a
divergencia relatada) ou se o catalogo perder a URL de alguma fonte mapeada.

Rodar: nice -n 19 python3 tools/test_writing_prompt_source_projection.py
"""

import base64
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_PATH = os.path.join(ROOT, 'scripts/workflows/writing-mass-todo.js')
DUMPER = os.path.join(ROOT, 'tools/generate-writing-prompt-dump')
LONG_BASE64 = re.compile(r"'([A-Za-z0-9+/=]{80,})'")


def load_queue_batches(path):
    """Mesma tecnica de tools/split-writing-queue: JSON puro, sem truncar."""
    with open(path, encoding='utf-8') as handle:
        text = handle.read()
    for line in text.splitlines():
        if line.startswith('const batches = ['):
            payload = line[len('const batches = '):]
            return json.loads(payload)
    raise AssertionError(f"'const batches = [' nao encontrado em {path}")


def source_resolution_blobs(prompt_text):
    """Todos os blobs base64 do prompt cujo payload e {source_overrides,
    strict_source_intents} -- distingue por FORMATO, nao por posicao (um
    lote com raw-recovery intercala blobs de outro formato entre as duas
    ocorrencias da projecao de fontes)."""
    blobs = []
    for candidate in LONG_BASE64.findall(prompt_text):
        try:
            decoded = base64.b64decode(candidate, validate=True)
            obj = json.loads(decoded)
        except Exception:
            continue
        if isinstance(obj, dict) and set(obj.keys()) == {
                'source_overrides', 'strict_source_intents'}:
            blobs.append((candidate, obj))
    return blobs


@unittest.skipUnless(
    os.path.exists(QUEUE_PATH) and os.path.getsize(QUEUE_PATH) > 0,
    f'fila viva ausente/vazia em {QUEUE_PATH} — nada a guardar agora '
    '(nao e um passe silencioso: o teste so roda quando ha fila para medir)')
class WritingPromptSourceProjectionTest(unittest.TestCase):
    """As duas ocorrencias da projecao de fontes no prompt sao idênticas."""

    @classmethod
    def setUpClass(cls):
        cls.batches = load_queue_batches(QUEUE_PATH)
        cls.tmpdir = tempfile.mkdtemp(prefix='writing-prompt-dump-')
        completed = subprocess.run(
            ['node', DUMPER, QUEUE_PATH, cls.tmpdir],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        cls.dump_stdout = completed.stdout
        cls.dump_stderr = completed.stderr
        cls.dump_returncode = completed.returncode

    def test_dumper_materialized_the_whole_queue(self):
        self.assertEqual(
            self.dump_returncode, 0,
            f'generate-writing-prompt-dump falhou: {self.dump_stderr[:800]}')
        manifest_path = os.path.join(self.tmpdir, 'manifest.json')
        with open(manifest_path, encoding='utf-8') as handle:
            manifest = json.load(handle)
        self.assertTrue(
            manifest['complete'],
            f'dump incompleto, lotes faltando: {manifest.get("missing")}')
        self.assertEqual(manifest['total'], len(self.batches))

    def test_every_source_override_hint_has_a_non_empty_url(self):
        """A causa POSSIVEL do relato (fonte sem url) nao existe na fila."""
        gaps = []
        for batch in self.batches:
            for intent_id, hints in (batch.get('source_overrides') or {}).items():
                for hint_id, hint in hints.items():
                    if not (hint.get('url') or '').strip():
                        gaps.append(f'{batch["slug"]}:{intent_id}:{hint_id}')
        self.assertEqual(
            gaps, [],
            f'source_overrides com url ausente/vazia: {gaps}')

    def test_both_prompt_occurrences_are_byte_identical(self):
        """A causa ESTRUTURAL do relato (duas construcoes divergentes) nao
        existe: as duas ocorrencias no prompt real vem da MESMA const JS."""
        failures = []
        for batch in self.batches:
            slug = batch['slug']
            prompt_path = os.path.join(self.tmpdir, f'{slug}.prompt.txt')
            with open(prompt_path, encoding='utf-8') as handle:
                prompt_text = handle.read()
            blobs = source_resolution_blobs(prompt_text)
            if len(blobs) != 2:
                failures.append(
                    f'{slug}: esperava 2 ocorrencias da projecao de fontes, '
                    f'achei {len(blobs)}')
                continue
            (first_raw, first_obj), (second_raw, second_obj) = blobs
            if first_raw != second_raw:
                failures.append(
                    f'{slug}: PREFLIGHT (1a ocorrencia) diverge da PROMOCAO '
                    f'(2a ocorrencia) byte a byte')
            if first_obj != second_obj:
                failures.append(
                    f'{slug}: payloads decodificados divergem apos parse')
        self.assertEqual(failures, [], '; '.join(failures))


if __name__ == '__main__':
    unittest.main(verbosity=2)
