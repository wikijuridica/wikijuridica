#!/usr/bin/env python3
"""Reconcilia os órfãos ativos do shard aereo-r06 tombstoneando-os no lugar.

Motivação (2026-07-17): o gate v2-internal-link-graph-topology reprova em
`loadPagesSnapshot` (internal/v2internallinkgraph/loader.go) qualquer página
ativa sem join exato no portfólio. As duas intents ativas de
data/editorial/v2_pages/aereo-r06.jsonl NÃO constam do portfólio
data/editorial/portfolio_v2/aereo.jsonl e são cobertura semanticamente
duplicada de intents canônicas que JÁ possuem página ativa e registro no
portfólio:

    aer-acompanhante-pcd-desconto   ~= aer-acompanhante-desconto-80-por-cento
                                        (página ativa em aereo-07.jsonl)
    aer-animal-apoio-emocional-cabine ~= aer-animal-suporte-emocional-negado
                                        (página ativa em aereo-r02.jsonl)

Adicioná-las ao portfólio só realocaria a falha para os gates de duplicidade
semântica de corpo. A reconciliação correta é aposentar (tombstone) as duas
páginas órfãs. O corpo autoral original permanece recuperável pelo histórico
git (commit 57a22852 — "content: add reviewed accessible air travel guidance
r06"), por isso NÃO se cria arquivo em data/editorial/v2_superseded: um novo
arquivo lá seria varrido por internal/v2supersessionintegrity/integrity.go
(discoverArchives) e reprovado como archive não confiável/record_type não
suportado, exigindo pin em constante Go. O tombstone mínimo (skipped=true +
skip_reason, sem a tupla de supersessão, que a validação aceita como
all-absent) é aceito por adjudicate_shard.go e ignorado por loadPagesSnapshot.

Segurança: lock exclusivo, CAS sobre os bytes exatos do shard (idempotente — se
já tombstoneado, no-op verde), escrita atômica preservando modo 0644. NÃO
committa: aplicar deixa a mutação em worktree para o pipeline sancionado / após
o release em curso, conforme a regra "não committar v2_pages por fora".
"""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease

SHARD_REL = "data/editorial/v2_pages/aereo-r06.jsonl"
SHARD = ROOT / SHARD_REL
LOCK = ROOT / "data/editorial/.tombstone-aereo-r06-orphans-20260717.lock"

# sha256 dos bytes exatos do shard ANTES da reconciliação (estado ativo).
EXPECTED_SOURCE_SHA = "760b988e0eb4fa73374a38415f2d0fe82c9ae3ee8129fde5e8437f56acd25c42"

SKIP_REASON = "orphan_no_portfolio_join_semantic_duplicate_of_active_canonical"

# intent órfã -> intent canônica que a supersede (documentação/provenância).
ORPHANS = {
    "aer-acompanhante-pcd-desconto": "aer-acompanhante-desconto-80-por-cento",
    "aer-animal-apoio-emocional-cabine": "aer-animal-suporte-emocional-negado",
}


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
    path.parent.mkdir(parents=True, exist_ok=True)
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


def tombstone_for(intent_id):
    return json.dumps(
        {
            "intent_id": intent_id,
            "skipped": True,
            "skip_reason": SKIP_REASON,
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def is_target_tombstone(record):
    return (
        record.get("skipped") is True
        and record.get("skip_reason") == SKIP_REASON
        and record.get("index_policy") == "noindex"
        and record.get("render_allowed") is False
        and record.get("sitemap_allowed") is False
        and record.get("publication_allowed") is False
        and set(record.keys())
        == {
            "intent_id",
            "skipped",
            "skip_reason",
            "index_policy",
            "render_allowed",
            "sitemap_allowed",
            "publication_allowed",
        }
    )


def run_locked():
    payload = SHARD.read_bytes()
    actual_sha = sha256(payload)

    # Idempotência: se já está no estado tombstoneado esperado, no-op verde.
    lines = payload.decode("utf-8").splitlines()
    if not lines:
        raise SystemExit(f"{SHARD_REL}: shard vazio")
    parsed = []
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            raise SystemExit(f"{SHARD_REL}: linha em branco {line_number}")
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise SystemExit(f"{SHARD_REL}: linha {line_number} não é objeto")
        parsed.append((line_number, raw, record))

    already = all(
        is_target_tombstone(record)
        for _, _, record in parsed
        if record.get("intent_id") in ORPHANS
    ) and any(record.get("intent_id") in ORPHANS for _, _, record in parsed)
    seen_orphans_now = {
        record.get("intent_id")
        for _, _, record in parsed
        if record.get("intent_id") in ORPHANS and is_target_tombstone(record)
    }
    if seen_orphans_now == set(ORPHANS):
        print(f"already-tombstoned shard={SHARD_REL} sha256={actual_sha}")
        return

    if actual_sha != EXPECTED_SOURCE_SHA:
        raise SystemExit(
            f"CAS mismatch {SHARD_REL}: expected={EXPECTED_SOURCE_SHA} actual={actual_sha}"
        )

    output = []
    retired = set()
    for line_number, raw, record in parsed:
        intent = record.get("intent_id")
        if intent in ORPHANS:
            if record.get("skipped"):
                output.append(raw)
                continue
            if intent in retired:
                raise SystemExit(f"órfã ativa duplicada no shard: {intent}")
            retired.add(intent)
            output.append(tombstone_for(intent))
        else:
            output.append(raw)

    if retired != set(ORPHANS):
        raise SystemExit(
            "conjunto de órfãs divergente "
            f"faltando={sorted(set(ORPHANS) - retired)} extra={sorted(retired - set(ORPHANS))}"
        )

    rewritten = ("\n".join(output) + "\n").encode("utf-8")

    # Re-checa que o shard não mudou entre leitura e escrita (CAS final).
    if SHARD.read_bytes() != payload:
        raise SystemExit(f"{SHARD_REL}: mudou durante a transação — abortado")

    atomic_write(SHARD, rewritten)
    print(f"tombstoned shard={SHARD_REL} orphans={len(retired)} sha256={sha256(rewritten)}")


def main():
    canonical_root = ROOT
    try:
        # Lock global primeiro: se outro epoch estiver ativo, nem o lock legado
        # em data/editorial é criado. CAS, temp, fsync e rename ficam na mesma
        # época canônica.
        with canonical_stock_write_lease(canonical_root):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(
            f"tombstone-aereo-r06: canonical stock busy: {error}",
            file=sys.stderr,
        )
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
