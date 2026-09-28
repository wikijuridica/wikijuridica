#!/usr/bin/env python3
"""Desfaz a diferenciacao de long_tail_query de suc-venda-pai-filho-anuencia.

Contexto (2026-08-04): a correcao de canibalizacao desta sessao diferenciou a
`long_tail_query` de 8 pares. Sete permanecem. Este oitavo teve de ser desfeito.

`data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-15.jsonl`
pina a intencao DUAS vezes — linha 108 preserva o registro da PAGINA
(`data/editorial/v2_pages/sucessoes-12.jsonl`) e linha 107 preserva a linha do
PORTFOLIO (`data/editorial/portfolio_v2/sucessoes.jsonl`). Para qualquer
registro ativo que divirja do payload preservado sem provenancia de sucessor
duravel, `internal/v2supersessionintegrity/integrity.go` emite
`active_source_changed_without_provenance`, e `ingest-v2-stock` ABORTA em
"validate v2 supersession integrity" antes de avaliar qualquer pagina. Alterar
a query do portfolio reproduziu exatamente essa falha (FAIL archive=...:107).

Portanto a intencao e imutavel pelos meios desta frente: a rota sancionada para
mexer nela e emitir provenancia por
`tools/generate-v2-supersession-forward-evidence`, o que e mudanca de escopo.
Correcao para frente: o campo volta ao valor preservado e a canibalizacao do par
fica registrada como residuo declarado.

Seguranca: lease canonica + lock exclusivo, CAS por campo, reescrita apenas da
linha alvo, escrita atomica com fsync, idempotente. NAO committa.
"""

from contextlib import contextmanager
import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease

PORTFOLIO_REL = "data/editorial/portfolio_v2/sucessoes.jsonl"
PORTFOLIO = ROOT / PORTFOLIO_REL
LOCK = ROOT / "data/editorial/.restore-sucessoes-portfolio-query-20260804.lock"

INTENT = "suc-venda-pai-filho-anuencia"
FIELD = "long_tail_query"
APPLIED = "como formalizar a venda de pai para filho sem risco de anulação"
PRESERVED = "pai pode vender imóvel para um filho sem os outros assinarem"


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


def run_locked():
    payload = PORTFOLIO.read_bytes()
    lines = payload.decode("utf-8").split("\n")
    trailing_newline = lines and lines[-1] == ""
    if trailing_newline:
        lines = lines[:-1]

    output = []
    restored = 0
    already = 0
    seen = False
    for number, raw in enumerate(lines, 1):
        if not raw.strip():
            raise SystemExit(f"{PORTFOLIO_REL}: linha em branco {number}")
        record = json.loads(raw)
        if record.get("intent_id") != INTENT:
            output.append(raw)
            continue
        seen = True
        current = record.get(FIELD)
        if current == PRESERVED:
            already += 1
            output.append(raw)
            continue
        if current != APPLIED:
            raise SystemExit(
                f"CAS de campo falhou {PORTFOLIO_REL}:{number} {FIELD} "
                f"esperado={APPLIED!r} atual={current!r}"
            )
        record[FIELD] = PRESERVED
        output.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        restored += 1

    if not seen:
        raise SystemExit(f"{PORTFOLIO_REL}: intent {INTENT} nao encontrado")
    if restored == 0:
        print(f"already-restored portfolio={PORTFOLIO_REL} intent={INTENT}")
        return

    rewritten = "\n".join(output)
    if trailing_newline:
        rewritten += "\n"
    if PORTFOLIO.read_bytes() != payload:
        raise SystemExit(f"{PORTFOLIO_REL}: mudou durante a transacao - abortado")
    atomic_write(PORTFOLIO, rewritten.encode("utf-8"))
    print(f"restored portfolio={PORTFOLIO_REL} intent={INTENT} {FIELD}={PRESERVED!r}")


def main():
    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(f"restore-sucessoes-portfolio-query: canonical stock busy: {error}", file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
