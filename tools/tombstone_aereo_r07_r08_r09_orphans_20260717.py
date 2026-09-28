#!/usr/bin/env python3
"""Reconcilia os órfãos ativos dos shards aereo-r07/r08/r09 tombstoneando-os.

Motivação (2026-07-17): igual ao caso já resolvido de aereo-r06. O gate
v2-internal-link-graph-topology reprova em `loadPagesSnapshot`
(internal/v2internallinkgraph/loader.go) qualquer página ativa sem join exato
no portfólio. As duas intents ativas de cada um destes três shards de
recuperação NÃO constam de nenhum portfólio de data/editorial/portfolio_v2 e
são cobertura semanticamente DUPLICADA de intents canônicas que JÁ possuem
página ativa e registro no portfólio (verificado 2026-07-17 — leitura de corpo
e de long_tail_query, mesma lei viva Res. ANAC 400/2016 / Lei 10.048/2000):

    aereo-r07:
      aer-assento-extra-passsageiro-corpo   ~= aer-obeso-assento-extra
                                              (página ativa em aereo-07.jsonl)
      aer-bagagem-danificada-conserto       ~= aer-bagagem-danificada-avaria
                                              (página ativa em aereo-04.jsonl)
    aereo-r08:
      aer-bagagem-extraviada-21-dias        ~= aer-bagagem-prazo-devolucao-7-21-dias
                                              (página ativa em aereo-04.jsonl)
      aer-bagagem-mao-despachada-portao     ~= aer-bagagem-despacho-portao-gate-check-extravio
                                              (página ativa em codex-sucessoes-portfolio-aereo-r02.jsonl)
    aereo-r09:
      aer-cancelamento-cia-reembolso-7-dias ~= aer-cancelamento-reembolso-prazo-7-dias
                                              (página ativa em aereo-02.jsonl)
      aer-conexao-perdida-bilhetes-separados ~= aer-atraso-conexao-bilhetes-separados
                                              (página ativa em aereo-01.jsonl)

Adicioná-las ao portfólio só realocaria a falha para os gates de duplicidade
semântica de corpo (< 0.70). A reconciliação correta é aposentar (tombstone) as
seis páginas órfãs. O corpo autoral original permanece recuperável pelo git, por
isso NÃO se cria arquivo em data/editorial/v2_superseded (seria varrido por
internal/v2supersessionintegrity/integrity.go). O tombstone mínimo (skipped=true
+ skip_reason, sem a tupla de supersessão) é aceito por adjudicate_shard.go e
ignorado por loadPagesSnapshot — mesmo formato validado em aereo-r06.jsonl.

Segurança: lock exclusivo, CAS sobre os bytes exatos de CADA shard (idempotente
— se já tombstoneado, no-op verde por shard), escrita atômica preservando modo
0644. Cada shard é uma unidade transacional independente. NÃO committa: deixa a
mutação em worktree para o pipeline sancionado, conforme "não committar
v2_pages por fora".
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

LOCK = ROOT / "data/editorial/.tombstone-aereo-r07-r08-r09-orphans-20260717.lock"

SKIP_REASON = "orphan_no_portfolio_join_semantic_duplicate_of_active_canonical"

# shard relativo -> (sha256 dos bytes exatos ANTES da reconciliação,
#                    {intent órfã -> intent canônica que a supersede}).
SHARDS = {
    "data/editorial/v2_pages/aereo-r07.jsonl": (
        "336b0b547cb57f410ff2473c64ea391568ddd973566a692e482ad506bd979d07",
        {
            "aer-assento-extra-passsageiro-corpo": "aer-obeso-assento-extra",
            "aer-bagagem-danificada-conserto": "aer-bagagem-danificada-avaria",
        },
    ),
    "data/editorial/v2_pages/aereo-r08.jsonl": (
        "c0357431d8503a0e796460db10455877eccc95fce18cf565da24074725e9ea23",
        {
            "aer-bagagem-extraviada-21-dias": "aer-bagagem-prazo-devolucao-7-21-dias",
            "aer-bagagem-mao-despachada-portao": "aer-bagagem-despacho-portao-gate-check-extravio",
        },
    ),
    "data/editorial/v2_pages/aereo-r09.jsonl": (
        "18bee3c26c9cd6f2ac0bfd2464e8560c1c52048c9a987f069b5b5052b37414f0",
        {
            "aer-cancelamento-cia-reembolso-7-dias": "aer-cancelamento-reembolso-prazo-7-dias",
            "aer-conexao-perdida-bilhetes-separados": "aer-atraso-conexao-bilhetes-separados",
        },
    ),
}

TOMBSTONE_KEYS = {
    "intent_id",
    "skipped",
    "skip_reason",
    "index_policy",
    "render_allowed",
    "sitemap_allowed",
    "publication_allowed",
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
        and set(record.keys()) == TOMBSTONE_KEYS
    )


def reconcile_shard(shard_rel, expected_sha, orphans):
    shard = ROOT / shard_rel
    payload = shard.read_bytes()
    actual_sha = sha256(payload)

    lines = payload.decode("utf-8").splitlines()
    if not lines:
        raise SystemExit(f"{shard_rel}: shard vazio")
    parsed = []
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            raise SystemExit(f"{shard_rel}: linha em branco {line_number}")
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise SystemExit(f"{shard_rel}: linha {line_number} não é objeto")
        parsed.append((line_number, raw, record))

    # Idempotência: se todas as órfãs já estão no estado tombstoneado, no-op.
    seen_orphans_done = {
        record.get("intent_id")
        for _, _, record in parsed
        if record.get("intent_id") in orphans and is_target_tombstone(record)
    }
    if seen_orphans_done == set(orphans):
        print(f"already-tombstoned shard={shard_rel} sha256={actual_sha}")
        return

    if actual_sha != expected_sha:
        raise SystemExit(
            f"CAS mismatch {shard_rel}: expected={expected_sha} actual={actual_sha}"
        )

    output = []
    retired = set()
    for _, raw, record in parsed:
        intent = record.get("intent_id")
        if intent in orphans:
            if record.get("skipped"):
                output.append(raw)
                continue
            if intent in retired:
                raise SystemExit(f"{shard_rel}: órfã ativa duplicada: {intent}")
            retired.add(intent)
            output.append(tombstone_for(intent))
        else:
            output.append(raw)

    if retired != set(orphans):
        raise SystemExit(
            f"{shard_rel}: conjunto de órfãs divergente "
            f"faltando={sorted(set(orphans) - retired)} extra={sorted(retired - set(orphans))}"
        )

    rewritten = ("\n".join(output) + "\n").encode("utf-8")

    if shard.read_bytes() != payload:
        raise SystemExit(f"{shard_rel}: mudou durante a transação — abortado")

    atomic_write(shard, rewritten)
    print(f"tombstoned shard={shard_rel} orphans={len(retired)} sha256={sha256(rewritten)}")


def main():
    canonical_root = ROOT
    try:
        # A lease global precede o lock histórico e fecha um único epoch para
        # todas as leituras CAS e todos os renames/fsyncs dos três shards.
        with canonical_stock_write_lease(canonical_root):
            with exclusive_lock(LOCK):
                for shard_rel, (expected_sha, orphans) in SHARDS.items():
                    reconcile_shard(shard_rel, expected_sha, orphans)
    except StockEpochBusy as error:
        print(
            f"tombstone-aereo-r07-r09: canonical stock busy: {error}",
            file=sys.stderr,
        )
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
