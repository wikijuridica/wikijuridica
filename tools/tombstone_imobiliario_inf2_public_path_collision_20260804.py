#!/usr/bin/env python3
"""Resolve a colisao de URL publica /imobiliario/direito-de-superficie/.

Motivacao (2026-08-04): o path publico de uma pagina da massa v2 e derivado, e
nao declarado. `internal/v2ingest/validate.go:583-594` monta
`publicpath.PublicPagePath(practice_area, seed, "", "")` com
`seed = seedTermIDFromIntentID(intent_id)`, e
`internal/v2ingest/validate.go:788-794` define esse seed como "o intent_id sem o
primeiro segmento antes do primeiro hifen". Logo, dois intents distintos com o
mesmo sufixo e a mesma practice_area colidem OBRIGATORIAMENTE na mesma URL:

    imob-direito-de-superficie -> /imobiliario/direito-de-superficie/
    amb-direito-de-superficie  -> /imobiliario/direito-de-superficie/

Estado medido antes desta reconciliacao (data/ops/v2_ingest_report.jsonl,
run_id=v2-ingest-20260804T150000Z-v2-stock-merged-jsonl): AMBAS as paginas estao
`status=rejected` com uma unica razao cada, `public_path_duplicate_in_batch`.
O par contribui ZERO pagina aprovada hoje. Alem disso
`tools/check-v2-internal-link-graph` ABORTA em
`internal/v2internallinkgraph/graph.go:353` ("path duplicado
/imobiliario/direito-de-superficie/") antes de `countOrphans()`, o que cega o
gate de orfandade para o acervo inteiro.

Escolha do sobrevivente (medida, nao presumida):

  imob-direito-de-superficie  guia_problema  629 palavras reais  4 secoes  2 FAQ
      fontes: Codigo Civil arts. 1.369-1.377 + Estatuto da Cidade arts. 21-24
  amb-direito-de-superficie   verbete        350 palavras reais  3 secoes  1 FAQ
      fontes: Lei 10.257/2001 arts. 21 e 23 + Codigo Civil art. 1.369

O guia sobrevive: e mais profundo e suas fontes oficiais SUBSUMEM as do verbete
(ele ja cita o Estatuto da Cidade que e a base do verbete). O verbete e
aposentado. Os corpos nao sao duplicata textual (Jaccard de shingles de 4
tokens = 0,004), mas ocupam a mesma URL derivada e a mesma practice_area: manter
os dois exigiria renomear um intent_id, operacao que passa pelo subsistema
`internal/v2portfoliomigration` + registro em
`data/editorial/v2_portfolio_intent_migrations.jsonl` + arquivo de preservacao
pinado, e que, por contrato do proprio modulo, "nao escreve v2_pages". O ganho
marginal seria +1 pagina aprovada; o custo seria uma migracao bijetiva atravessando
shards de portfolio sob edicao concorrente. Aposentar o verbete leva o par de 0
para 1 pagina aprovada com uma unica escrita.

Por que tombstone MINIMO (sem a tupla de supersessao): `adjudicate_shard.go:775-784`
aceita a tupla (superseded_by, superseded_record_sha256, supersession_archive)
como all-present ou all-absent; preenche-la exigiria criar arquivo em
`data/editorial/v2_superseded/`, que `internal/v2supersessionintegrity`
(discoverArchives) varre e reprova como archive nao pinado. O corpo autoral
original permanece integralmente recuperavel pelo historico git deste shard.

Seguranca: lease canonica de epoca do estoque + lock exclusivo, CAS sobre os
bytes exatos do shard (idempotente: se ja tombstoneado, no-op verde), escrita
atomica com fsync preservando modo 0644. NAO committa.
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

SHARD_REL = "data/editorial/v2_pages/imobiliario-inf2.jsonl"
SHARD = ROOT / SHARD_REL
LOCK = ROOT / "data/editorial/.tombstone-imobiliario-inf2-collision-20260804.lock"

# sha256 dos bytes exatos do shard ANTES da reconciliacao. Confere com o
# source_shard_sha256 pinado em data/editorial/v2_rewrite_queue.jsonl:1161.
EXPECTED_SOURCE_SHA = "676ba6df09c636c7d42ea265e52e5ae9ad4668f85ab72e9fae5a400f912734b6"

# intent aposentada -> intent canonica que ocupa a URL (documentacao/provenancia).
RETIRED = {"amb-direito-de-superficie": "imob-direito-de-superficie"}

SKIP_REASON = (
    "public_path_collision_with_active_canonical: o slug publico e derivado por "
    "seedTermIDFromIntentID (internal/v2ingest/validate.go:788), que remove apenas o "
    "primeiro segmento do intent_id, entao amb-direito-de-superficie e "
    "imob-direito-de-superficie derivam a MESMA URL /imobiliario/direito-de-superficie/ "
    "e ambos eram reprovados por public_path_duplicate_in_batch. A URL fica com "
    "imob-direito-de-superficie (guia_problema, 629 palavras, Codigo Civil arts. "
    "1.369-1.377 + Estatuto da Cidade arts. 21-24), cujas fontes oficiais subsumem as "
    "deste verbete (Lei 10.257/2001 arts. 21 e 23 + CC art. 1.369). Corpo autoral "
    "original recuperavel no historico git deste shard."
)

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
        and set(record.keys()) == TOMBSTONE_KEYS
    )


def parse_shard(payload):
    lines = payload.decode("utf-8").splitlines()
    if not lines:
        raise SystemExit(f"{SHARD_REL}: shard vazio")
    parsed = []
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            raise SystemExit(f"{SHARD_REL}: linha em branco {line_number}")
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise SystemExit(f"{SHARD_REL}: linha {line_number} nao e objeto")
        parsed.append((line_number, raw, record))
    return parsed


def run_locked():
    payload = SHARD.read_bytes()
    actual_sha = sha256(payload)
    parsed = parse_shard(payload)

    # Idempotencia: se ja esta no estado tombstoneado esperado, no-op verde.
    already = {
        record.get("intent_id")
        for _, _, record in parsed
        if record.get("intent_id") in RETIRED and is_target_tombstone(record)
    }
    if already == set(RETIRED):
        print(f"already-tombstoned shard={SHARD_REL} sha256={actual_sha}")
        return

    if actual_sha != EXPECTED_SOURCE_SHA:
        raise SystemExit(
            f"CAS mismatch {SHARD_REL}: expected={EXPECTED_SOURCE_SHA} actual={actual_sha}"
        )

    output = []
    retired = set()
    for _, raw, record in parsed:
        intent = record.get("intent_id")
        if intent in RETIRED:
            if record.get("skipped"):
                output.append(raw)
                continue
            if intent in retired:
                raise SystemExit(f"intent ativa duplicada no shard: {intent}")
            retired.add(intent)
            output.append(tombstone_for(intent))
        else:
            output.append(raw)

    if retired != set(RETIRED):
        raise SystemExit(
            "conjunto de intents divergente "
            f"faltando={sorted(set(RETIRED) - retired)} extra={sorted(retired - set(RETIRED))}"
        )

    rewritten = ("\n".join(output) + "\n").encode("utf-8")

    # Re-checa que o shard nao mudou entre leitura e escrita (CAS final).
    if SHARD.read_bytes() != payload:
        raise SystemExit(f"{SHARD_REL}: mudou durante a transacao - abortado")

    atomic_write(SHARD, rewritten)
    print(
        f"tombstoned shard={SHARD_REL} retired={sorted(retired)} "
        f"survivor={sorted(set(RETIRED.values()))} sha256={sha256(rewritten)}"
    )


def main():
    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(
            f"tombstone-imobiliario-inf2-collision: canonical stock busy: {error}",
            file=sys.stderr,
        )
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
