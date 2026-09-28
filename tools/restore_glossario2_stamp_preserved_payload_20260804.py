#!/usr/bin/env python3
"""Devolve 2 registros preservados por supersessao ao payload autenticado.

Contexto (2026-08-04): a rodada de carimbo de fontes oficiais (commit 11744d09,
`internal/v2officialsourcestamp.Apply`) escreveu verified_at/http_status em
2.606 fontes. Duas das paginas carimbadas sao registros ATIVOS preservados no
archive de supersessao `duplicate-intent-consolidation-2026-07-15.jsonl`
(linhas 14 e 58):

    gloss-dolo-eventual-culpa-consciente  data/editorial/v2_pages/glossario2-02.jsonl:22
    gloss-certidao-onus-reais             data/editorial/v2_pages/glossario2-19.jsonl:3

Mecanismo do gate (`internal/v2supersessionintegrity/integrity.go`):
  1. O archive preserva os BYTES exatos do registro (`original_line`, com
     `source_record_sha256 == sha256(original_line)` verificado em
     integrity.go:782-784).
  2. Para registro preservado que continua ATIVO no shard, o audit exige
     igualdade byte a byte `current.Raw == record.OriginalLine`
     (integrity.go:503) OU proveniencia de sucessor duravel — contrato
     writing-semantic (integrity.go:462), committed forward ancorado em git
     (integrity.go:477; exige os bytes novos JA em HEAD pinado) ou revisao
     independente selada (integrity.go:490; autoridade com digest compilado,
     81 linhas fixas). Sem nada disso: `active_source_changed_without_provenance`
     (integrity.go:506-509) e `ingest-v2-stock` aborta antes de avaliar
     qualquer pagina (cmd/ingest-v2-stock/main.go:325-328).
  3. O carimbo NAO tem nenhum desses canais: os bytes carimbados nao estao em
     HEAD (os shards foram deliberadamente isolados do commit 11744d09), nao
     ha recut semantico e a autoridade de revisao e imutavel.

Por que restaurar (e nao criar proveniencia): as duas paginas sao duplicatas
consolidadas — o conteudo canonico vive em criminal-07.jsonl:2
(crim-dolo-eventual-e-culpa-consciente, verified_at 2026-07-11) e
imobiliario-10.jsonl:17 (imob-certidao-onus-reais, verified_at 2026-07-08),
ambos com carimbo proprio. Carimbar a duplicata destinada a aposentadoria nao
tem valor de produto e quebra o invariante do audit; nenhum dado se perde ao
desfazer. O ledger do carimbo (data/ops/v2_official_source_stamp_ledger.jsonl,
linhas 181-184) registra exatamente essas mutacoes com sha256_before igual a
HEAD, entao a reversao e a inversa auditavel da mesma esteira.

Fonte da restauracao: `original_line` do proprio archive (payload autenticado
por sha256 pinado no archive, cujo digest e ancorado em
defaultTrustedArchiveSHA256), conferido tambem contra os bytes de HEAD
(`git show HEAD:<shard>`). Nenhum comando de retorno de estado do git e usado.

Seguranca: lease canonica do estoque + lock exclusivo, CAS por sha256 do shard,
verificacao de que a UNICA divergencia e o par verified_at/http_status,
verificacao do sha256 final, escrita atomica temp+rename+fsync, entrada de
preimagem no ledger do carimbo ANTES da escrita, idempotente. NAO committa.
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

ARCHIVE_REL = "data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-15.jsonl"
LEDGER_REL = "data/ops/v2_official_source_stamp_ledger.jsonl"
LOCK = ROOT / "data/editorial/.restore-glossario2-stamp-preserved-20260804.lock"

TARGETS = [
    {
        "shard_rel": "data/editorial/v2_pages/glossario2-02.jsonl",
        "intent": "gloss-dolo-eventual-culpa-consciente",
        "line": 22,
        # sha256 do shard com o carimbo indevido (estado a corrigir).
        "expected_current_sha": "19f1b8bc24e508a6b6506307d0866216f7e34db387399711e45b4b2e68aa8e51",
        # sha256 do shard restaurado (igual a HEAD e ao pin pre-carimbo do ledger).
        "expected_restored_sha": "5ec8f4b5df1321c942dc9f6eca6f632eb45e6c49d93edccc52417a377bdfa1f0",
        # source_record_sha256 do archive (sha256 do original_line preservado).
        "preserved_record_sha": "6e8208085d4caa6a93ab8630fd50f345b2380ca7b8bfb0d7d2209558118eba9b",
    },
    {
        "shard_rel": "data/editorial/v2_pages/glossario2-19.jsonl",
        "intent": "gloss-certidao-onus-reais",
        "line": 3,
        "expected_current_sha": "1446d5980ad7c58a1b37dda090d3daf50c1212cc5bbb4e9d655f3a0ca55ebd16",
        "expected_restored_sha": "24f875bf9b211de0525de40d480c73c9224ac1c33d3f9cd7a2519db70ad3f219",
        "preserved_record_sha": "a45c40a21bcae16bc292d24e1c593adc4e8806424e3c1d5b83b63c252c4366f7",
    },
]

STAMP_ONLY_KEYS = {"verified_at", "http_status"}


def sha256_hex(payload):
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


def append_ledger(record):
    path = ROOT / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


def utc_now():
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def preserved_line_from_archive(intent, shard_basename, preserved_record_sha):
    archive = ROOT / ARCHIVE_REL
    for raw in archive.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        if (
            record.get("record_type") == "v2_duplicate_intent_supersession"
            and record.get("intent_id") == intent
            and record.get("source_shard") == shard_basename
        ):
            original_line = record["original_line"]
            actual_sha = sha256_hex(original_line.encode("utf-8"))
            if actual_sha != preserved_record_sha:
                raise SystemExit(
                    f"{ARCHIVE_REL}: original_line de {intent} nao confere: "
                    f"esperado={preserved_record_sha} atual={actual_sha}"
                )
            if record.get("source_record_sha256") != preserved_record_sha:
                raise SystemExit(
                    f"{ARCHIVE_REL}: source_record_sha256 de {intent} difere do pin deste tool"
                )
            return original_line
    raise SystemExit(f"{ARCHIVE_REL}: intent {intent} shard {shard_basename} nao encontrado")


def head_bytes(shard_rel):
    completed = subprocess.run(
        ["git", "show", f"HEAD:{shard_rel}"],
        cwd=os.fspath(ROOT),
        capture_output=True,
        check=True,
    )
    return completed.stdout


def stamp_only_delta(current_record, preserved_record):
    """True sse current == preserved apos remover verified_at/http_status das fontes."""
    if set(current_record) != set(preserved_record):
        return False
    for key in current_record:
        if key == "official_sources":
            continue
        if current_record[key] != preserved_record[key]:
            return False
    current_sources = current_record.get("official_sources")
    preserved_sources = preserved_record.get("official_sources")
    if not isinstance(current_sources, list) or not isinstance(preserved_sources, list):
        return False
    if len(current_sources) != len(preserved_sources):
        return False
    for current_source, preserved_source in zip(current_sources, preserved_sources):
        stripped = {k: v for k, v in current_source.items() if k not in STAMP_ONLY_KEYS}
        preserved_stripped = {
            k: v for k, v in preserved_source.items() if k not in STAMP_ONLY_KEYS
        }
        if stripped != preserved_stripped:
            return False
    return True


def restore_target(target):
    shard = ROOT / target["shard_rel"]
    shard_basename = shard.name
    current = shard.read_bytes()
    current_sha = sha256_hex(current)
    if current_sha == target["expected_restored_sha"]:
        print(f"already-restored shard={target['shard_rel']} sha256={current_sha}")
        return

    if current_sha != target["expected_current_sha"]:
        raise SystemExit(
            f"CAS mismatch {target['shard_rel']}: esperado={target['expected_current_sha']} "
            f"atual={current_sha}"
        )

    preserved_line = preserved_line_from_archive(
        target["intent"], shard_basename, target["preserved_record_sha"]
    )

    head = head_bytes(target["shard_rel"])
    if sha256_hex(head) != target["expected_restored_sha"]:
        raise SystemExit(
            f"HEAD de {target['shard_rel']} nao e a origem esperada: sha256={sha256_hex(head)}"
        )
    head_lines = head.decode("utf-8").splitlines()
    current_lines = current.decode("utf-8").splitlines()
    if len(head_lines) != len(current_lines):
        raise SystemExit(
            f"{target['shard_rel']}: contagem de linhas divergente "
            f"head={len(head_lines)} atual={len(current_lines)}"
        )
    divergent = [i + 1 for i, (a, b) in enumerate(zip(head_lines, current_lines)) if a != b]
    if divergent != [target["line"]]:
        raise SystemExit(
            f"{target['shard_rel']}: esperava divergencia apenas na linha {target['line']}, "
            f"achei {divergent}"
        )
    if head_lines[target["line"] - 1] != preserved_line:
        raise SystemExit(
            f"{target['shard_rel']}:{target['line']}: linha de HEAD difere do payload "
            f"preservado no archive — abortado"
        )

    current_record = json.loads(current_lines[target["line"] - 1])
    preserved_record = json.loads(preserved_line)
    if current_record.get("intent_id") != target["intent"]:
        raise SystemExit(f"{target['shard_rel']}:{target['line']}: intent_id inesperado")
    if not stamp_only_delta(current_record, preserved_record):
        raise SystemExit(
            f"{target['shard_rel']}:{target['line']}: divergencia alem de "
            f"verified_at/http_status — restauracao cega proibida, abortado"
        )

    output = list(current_lines)
    output[target["line"] - 1] = preserved_line
    rewritten = ("\n".join(output) + "\n").encode("utf-8")
    if sha256_hex(rewritten) != target["expected_restored_sha"]:
        raise SystemExit(
            f"resultado nao confere com o alvo: sha256={sha256_hex(rewritten)} "
            f"alvo={target['expected_restored_sha']}"
        )

    sources_restored = sum(
        1
        for source in current_record.get("official_sources", [])
        if any(key in source for key in STAMP_ONLY_KEYS)
    )
    append_ledger(
        {
            "ts": utc_now(),
            "shard": shard_basename,
            "phase": "preimage",
            "sha256_before": current_sha,
            "lines_touched": [target["line"]],
            "sources_patched": sources_restored,
            "operation": "restore_supersession_preserved_payload",
        }
    )

    if shard.read_bytes() != current:
        raise SystemExit(f"{target['shard_rel']}: mudou durante a transacao — abortado")
    atomic_write(shard, rewritten)

    append_ledger(
        {
            "ts": utc_now(),
            "shard": shard_basename,
            "phase": "committed",
            "sha256_before": current_sha,
            "sha256_after": sha256_hex(rewritten),
            "lines_touched": [target["line"]],
            "sources_patched": sources_restored,
            "operation": "restore_supersession_preserved_payload",
        }
    )
    print(
        f"restored shard={target['shard_rel']} linha={target['line']} "
        f"intent={target['intent']} sha256={sha256_hex(rewritten)}"
    )


def main():
    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                for target in TARGETS:
                    restore_target(target)
    except StockEpochBusy as error:
        print(
            f"restore-glossario2-stamp-preserved: canonical stock busy: {error}",
            file=sys.stderr,
        )
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
