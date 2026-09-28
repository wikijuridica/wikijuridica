#!/usr/bin/env python3
"""Aposenta suc-venda-pai-filho-anuencia, subsumida por imob-venda-ascendente-descendente.

Motivacao (2026-08-04): das 8 duplas de canibalizacao do acervo (duas paginas
ativas declarando a MESMA long_tail_query), sete eram declaracao errada sobre
conteudo legitimamente distinto e foram corrigidas por
`tools/generate-v2-cannibalization-query-differentiation`. Esta e a unica em que
a evidencia aponta redundancia REAL, e por isso e a unica resolvida por
tombstone.

Query disputada: "pai pode vender imovel para um filho sem os outros assinarem".

  imob-venda-ascendente-descendente  /imobiliario/venda-ascendente-descendente/
      pergunta, 611 palavras de corpo, 5 secoes + 2 FAQ
      art. 496 CC; quem precisa consentir (demais descendentes + conjuge);
      forma do consentimento; colacao; anulabilidade e prazo de 2 anos;
      a escritura tem de refletir a operacao real

  suc-venda-pai-filho-anuencia       /sucessoes/venda-pai-filho-anuencia/
      pergunta, 403 palavras de corpo, 4 secoes + 1 FAQ
      art. 496 CC; quem precisa consentir; prazo para anular; como formalizar

Todo topico da pagina de sucessoes ja e coberto pela de imobiliario, que ainda
acrescenta colacao e forma da escritura. A prosa e textualmente disjunta
(Jaccard de shingles de 4 tokens = 0,010; containment = 0,025), motivo pelo qual
`check-v2-body-near-duplicates` e `check-v2-body-semantic-duplicates` sao CEGOS
a este caso por construcao: os corpos sao distintos, a pergunta do leitor e a
mesma. Declarar duas queries diferentes aqui seria mentir para o gate; a unica
saida honesta e aposentar a peca subsumida.

Por que tombstone MINIMO (sem a tupla de supersessao): `adjudicate_shard.go:775-784`
aceita a tupla como all-present ou all-absent; preenche-la exigiria criar arquivo
em `data/editorial/v2_superseded/`, varrido e reprovado por
`internal/v2supersessionintegrity` como archive nao pinado. O corpo autoral
permanece recuperavel pelo historico git deste shard.

Seguranca: lease canonica de epoca + lock exclusivo, CAS sobre os bytes exatos
do shard, escrita atomica com fsync, modo 0644, idempotente. NAO committa.
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

SHARD_REL = "data/editorial/v2_pages/sucessoes-12.jsonl"
SHARD = ROOT / SHARD_REL
LOCK = ROOT / "data/editorial/.tombstone-sucessoes-12-subsumed-20260804.lock"

EXPECTED_SOURCE_SHA = "264829195e7a0a0b4d8c5f16def6256c0858218abb2e4aa7d3fd2645b3e156d9"

RETIRED = {"suc-venda-pai-filho-anuencia": "imob-venda-ascendente-descendente"}

SKIP_REASON = (
    "search_intent_subsumed_by_active_canonical: disputava a query declarada "
    "\"pai pode vender imovel para um filho sem os outros assinarem\" com "
    "imob-venda-ascendente-descendente (/imobiliario/venda-ascendente-descendente/, "
    "pergunta, 611 palavras), cuja cobertura contem integralmente a desta pagina "
    "(art. 496 CC, quem precisa consentir, prazo de anulacao) e ainda acrescenta "
    "colacao e forma da escritura. Corpos textualmente disjuntos (Jaccard shingle-4 "
    "= 0,010), por isso invisivel a check-v2-body-near-duplicates e "
    "check-v2-body-semantic-duplicates. Corpo autoral recuperavel no historico git."
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
        and set(record.keys()) == TOMBSTONE_KEYS
    )


def run_locked():
    payload = SHARD.read_bytes()
    actual_sha = sha256(payload)
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
    if SHARD.read_bytes() != payload:
        raise SystemExit(f"{SHARD_REL}: mudou durante a transacao - abortado")

    atomic_write(SHARD, rewritten)
    print(
        f"tombstoned shard={SHARD_REL} retired={sorted(retired)} "
        f"survivor={sorted(set(RETIRED.values()))} sha256={sha256(rewritten)}"
    )


def main():
    # DESATIVADO EM 2026-08-04, no mesmo dia em que foi escrito. Este tombstone
    # FOI aplicado e teve de ser desfeito por
    # `tools/restore_sucessoes_12_active_page_20260804.py`: a intencao consta do
    # archive de supersessao
    # `data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-15.jsonl:108`,
    # e `internal/v2supersessionintegrity/integrity.go:1087-1093` so aceita, para
    # intencao arquivada, um tombstone que amarre archive + shard canonico +
    # registro preservado E que ocupe a linha pinada (19; a pagina viva esta na
    # 22). O tombstone minimo emitido aqui vira `invalid_tombstone` e faz
    # `ingest-v2-stock` ABORTAR antes de avaliar qualquer pagina. A canibalizacao
    # que motivou o script foi resolvida sem destruir conteudo, diferenciando a
    # `long_tail_query` em
    # `tools/generate-v2-cannibalization-query-differentiation`.
    #
    # O corpo do script fica preservado como registro da tentativa e do porque
    # ela nao serve; executa-lo reintroduziria a falha.
    print(
        "tombstone-sucessoes-12-subsumed: DESATIVADO — este tombstone quebra "
        "check-v2-supersession-integrity (invalid_tombstone) e aborta "
        "ingest-v2-stock. Ver tools/restore_sucessoes_12_active_page_20260804.py "
        "e tools/generate-v2-cannibalization-query-differentiation.",
        file=sys.stderr,
    )
    return 78

    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(f"tombstone-sucessoes-12-subsumed: canonical stock busy: {error}", file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
