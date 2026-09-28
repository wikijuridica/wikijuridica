#!/usr/bin/env python3
"""Restaura suc-venda-pai-filho-anuencia como pagina ATIVA em sucessoes-12.jsonl.

Contexto (2026-08-04): esta sessao havia aposentado a intencao por canibalizacao
de query com imob-venda-ascendente-descendente. A medicao editorial estava certa
— o arquivo `data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-15.jsonl:108`
registra exatamente a mesma conclusao, com o mesmo canonico
(`imobiliario-09.jsonl` linha 15) — mas o tombstone estava ERRADO como mecanica:

  1. `internal/v2supersessionintegrity/integrity.go:1087-1091` exige, para toda
     intencao presente num archive de supersessao, um tombstone que AMARRE
     archive + shard canonico + registro preservado
     (skip_reason == "duplicate_intent_consolidated", superseded_by ==
     canonical_shard, supersession_archive == caminho do archive,
     superseded_record_sha256 == source_record_sha256 do archive). O tombstone
     minimo emitido nao amarrava nada e virou `invalid_tombstone`.
  2. `integrity.go:1093` ainda exige que o tombstone ocupe a LINHA pinada no
     archive (`source_line=19`); a pagina viva esta na linha 22, porque o shard
     cresceu desde 2026-07-15. Nao ha tombstone valido possivel nessa posicao
     sem reordenar o shard inteiro.
  3. O efeito pratico foi FATAL para a fabrica: `ingest-v2-stock` aborta em
     "validate v2 supersession integrity" antes de qualquer pagina ser avaliada.

Alem disso a leitura do archive mostra que a pagina foi DELIBERADAMENTE revivida
depois da consolidacao de 2026-07-15, por revisao independente
(`integrity.go:490-503`, contadores `active_changed`/`independent_reviews` do
proprio check). Aposenta-la de novo por decisao unilateral desta sessao
contraria uma decisao editorial ja tomada e revisada.

Correcao para frente: a pagina volta a ATIVA, byte a byte como estava antes
desta sessao, e a canibalizacao de query e resolvida como nos outros 7 pares —
diferenciando a `long_tail_query` declarada em
`tools/generate-v2-cannibalization-query-differentiation`, que passa a declarar
para esta pagina a pergunta que ela de fato responde ("como formalizar a venda
de pai para filho sem risco de anulacao", secao 'Como formalizar a venda sem
risco de anulacao futura' + FAQ sobre preco abaixo do mercado).

Fonte da restauracao: os bytes exatos de HEAD (`git show HEAD:<shard>`), cujo
sha256 confere com o estado pre-edicao registrado por esta sessao. Nenhum
comando de retorno de estado do git e usado (nada de checkout/restore/reset):
apenas leitura de HEAD e reescrita atomica da UNICA linha alterada.

Seguranca: lease canonica + lock exclusivo, CAS sobre os bytes atuais e
verificacao do sha256 final contra o alvo, escrita atomica com fsync,
idempotente. NAO committa.
"""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease

SHARD_REL = "data/editorial/v2_pages/sucessoes-12.jsonl"
SHARD = ROOT / SHARD_REL
LOCK = ROOT / "data/editorial/.restore-sucessoes-12-active-20260804.lock"

INTENT = "suc-venda-pai-filho-anuencia"
TARGET_LINE = 22

# sha256 do shard com o tombstone indevido (estado a corrigir).
EXPECTED_CURRENT_SHA = "e5ec91e238f275f7c1d4e77dccdff4b7186a406916afdbd62a30c52679d9332a"
# sha256 do shard com a pagina ativa (estado restaurado; igual a HEAD).
EXPECTED_RESTORED_SHA = "264829195e7a0a0b4d8c5f16def6256c0858218abb2e4aa7d3fd2645b3e156d9"


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        os.fchmod(fd, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_write(path, payload):
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def head_bytes():
    completed = subprocess.run(
        ["git", "show", f"HEAD:{SHARD_REL}"],
        cwd=os.fspath(ROOT), capture_output=True, check=True,
    )
    return completed.stdout


def run_locked():
    current = SHARD.read_bytes()
    current_sha = sha256(current)
    if current_sha == EXPECTED_RESTORED_SHA:
        print(f"already-restored shard={SHARD_REL} sha256={current_sha}")
        return
    if current_sha != EXPECTED_CURRENT_SHA:
        raise SystemExit(
            f"CAS mismatch {SHARD_REL}: expected={EXPECTED_CURRENT_SHA} actual={current_sha}"
        )

    head = head_bytes()
    if sha256(head) != EXPECTED_RESTORED_SHA:
        raise SystemExit(
            f"HEAD de {SHARD_REL} nao e a origem esperada: sha256={sha256(head)}"
        )

    head_lines = head.decode("utf-8").splitlines()
    current_lines = current.decode("utf-8").splitlines()
    if len(head_lines) != len(current_lines):
        raise SystemExit(
            f"{SHARD_REL}: contagem de linhas divergente head={len(head_lines)} atual={len(current_lines)}"
        )

    divergent = [i + 1 for i, (a, b) in enumerate(zip(head_lines, current_lines)) if a != b]
    if divergent != [TARGET_LINE]:
        raise SystemExit(
            f"{SHARD_REL}: esperava divergencia apenas na linha {TARGET_LINE}, achei {divergent}"
        )

    restored_record = json.loads(head_lines[TARGET_LINE - 1])
    replaced_record = json.loads(current_lines[TARGET_LINE - 1])
    if restored_record.get("intent_id") != INTENT or replaced_record.get("intent_id") != INTENT:
        raise SystemExit(f"{SHARD_REL}:{TARGET_LINE}: intent_id inesperado")
    if restored_record.get("skipped") is True:
        raise SystemExit(f"{SHARD_REL}:{TARGET_LINE}: registro de HEAD ja e tombstone")
    if replaced_record.get("skipped") is not True:
        raise SystemExit(f"{SHARD_REL}:{TARGET_LINE}: registro atual nao e o tombstone desta sessao")

    output = list(current_lines)
    output[TARGET_LINE - 1] = head_lines[TARGET_LINE - 1]
    rewritten = ("\n".join(output) + "\n").encode("utf-8")
    if sha256(rewritten) != EXPECTED_RESTORED_SHA:
        raise SystemExit(
            f"resultado nao confere com o alvo: sha256={sha256(rewritten)} alvo={EXPECTED_RESTORED_SHA}"
        )
    if SHARD.read_bytes() != current:
        raise SystemExit(f"{SHARD_REL}: mudou durante a transacao - abortado")

    atomic_write(SHARD, rewritten)
    print(f"restored shard={SHARD_REL} linha={TARGET_LINE} intent={INTENT} sha256={sha256(rewritten)}")


def main():
    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(f"restore-sucessoes-12-active: canonical stock busy: {error}", file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
