#!/usr/bin/env python3
"""Empacota intents órfãos do portfólio em lotes pinados de até 22 páginas.

Causa-raiz (frente EMPACOTAMENTO 2026-07-29): o inventário canônico
(scripts/workflows/writing-mass-full.js) só ganhava lotes novos pelo
materializador wave3 (internal/portfoliowave3/workflow.go:336-351), que fatia
POR FAMÍLIA — família com 1 intent restante vira lote de 1 página — e a onda
-w3 (2.4k intents já no portfólio) nem sequer ganhou lote: 2.041 intents
faltantes estavam órfãos de inventário. Este gerador cobre a família inteira
do problema: TODO intent de portfólio sem dono no inventário e sem página em
data/editorial/v2_pages/ entra num lote pinado (take==0, intent_ids
explícitos), agrupando famílias da MESMA área em ordem não-intercalada até o
teto de 22 — exatamente a forma que ops/relaunch-writing.sh (expected_intents)
e tools/verify_v2_writing_queue_closure.py (_validate_base_batch) já validam.

Separação por resolvibilidade de fonte (espelha
producer.derive_writing_source_resolution, generate_v2_review_queue.py:1724):
um único intent com needs_source_research=false e hint fora do catálogo
derruba o lote INTEIRO no preflight de fontes. Por isso intents que passam o
preflight hoje (classe A) nunca dividem lote com intents que aguardam o
catálogo (classe B); lotes B nascem separados, caem no manifesto emit-clean do
relaunch e entram na fila automaticamente quando o catálogo os cobrir. Cada
lote classe A emitido é PROVADO aqui contra o preflight real
(producer.verify_writing_source_resolution) antes de o inventário ser escrito;
cada lote classe B é provado que falha EXATAMENTE na classe emit-clean — outra
classe de falha aborta a produção inteira (fail-closed).

O CAS da fila não muda: cada lote novo aponta para um shard NOVO
(data/editorial/v2_pages/<area>-NN.jsonl inexistente). A escrita serializa no
MESMO lock do produtor da fila (/tmp/opt-wiki-relaunch-writing-pair.lock,
flock não-bloqueante, exit 75) e re-verifica os snapshots de inventário,
portfólios e catálogo antes do replace atômico. Zero rede, zero LLM.
"""

from __future__ import annotations

import argparse
import base64
import collections
import contextlib
import fcntl
import json
import os
import pathlib
import re
import sys
import tempfile

_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import generate_v2_review_queue as producer

INVENTORY_REL_PATH = "scripts/workflows/writing-mass-full.js"
AREA_SOURCES_REL_PATH = "data/editorial/v2_area_sources.json"
SOURCE_HINT_CATALOG_REL_PATH = "data/editorial/v2_source_hint_catalog.json"
PAGES_DIR_REL_PATH = "data/editorial/v2_pages"
PORTFOLIO_DIR_REL_PATH = "data/editorial/portfolio_v2"
PRODUCER_LOCK_PATH = "/tmp/opt-wiki-relaunch-writing-pair.lock"
MAX_BATCH_PAGES = 22
_MAX_INVENTORY_BYTES = 16 * 1024 * 1024
_MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024
_MAX_AREA_SOURCES_BYTES = 8 * 1024 * 1024
_MAX_CATALOG_BYTES = 8 * 1024 * 1024

_MARKER = b"const batches = "
_SLUG = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)+")
_AREA = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)*")
_FAMILY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_INTENT = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PORTFOLIO_REL = re.compile(
    r"data/editorial/portfolio_v2/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl")
_EMIT_CLEAN_MARKERS = (
    "pesquisa concluída sem resolução exata",
    "pesquisa concluida sem resolucao exata",
    "intent strict sem resolução exata",
    "intent strict sem resolucao exata",
    # Mesma família de defeito de FONTE: entrada presente no catálogo com URL
    # não documental (ex.: query URN sobre path raiz). O lote nasce classe B e
    # entra na fila quando tools/generate-catalog-url-repair cobrir a entrada.
    "URL oficial HTTPS inválida",
    "URL oficial HTTPS invalida",
)
_FINALIZED_SHARD_MARKERS = (
    ".partial.", ".candidate.", ".tmp.", ".stale.", ".poisoned.")


class PackError(RuntimeError):
    """Falha fail-closed da produção do empacotamento."""


def _load_inventory(root: pathlib.Path):
    snapshot = producer.read_regular_file_snapshot(
        root / INVENTORY_REL_PATH, max_bytes=_MAX_INVENTORY_BYTES)
    payload = snapshot.payload
    marker_index = payload.find(_MARKER)
    if marker_index < 0 or (
            marker_index > 0 and payload[marker_index - 1:marker_index] != b"\n"):
        raise PackError(f"{INVENTORY_REL_PATH}: âncora const batches ausente")
    if payload.find(_MARKER, marker_index + len(_MARKER)) >= 0:
        raise PackError(f"{INVENTORY_REL_PATH}: mais de um inventário")
    array_start = marker_index + len(_MARKER)
    try:
        text = payload[array_start:].decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackError(f"{INVENTORY_REL_PATH}: inventário não é UTF-8") from error
    try:
        batches, consumed = json.JSONDecoder().raw_decode(text)
    except ValueError as error:
        raise PackError(f"{INVENTORY_REL_PATH}: JSON inválido: {error}") from error
    raw = text[:consumed].encode("utf-8")
    array_end = array_start + len(raw)
    if payload[array_end:array_end + 1] != b"\n":
        raise PackError(
            f"{INVENTORY_REL_PATH}: array deve terminar a própria linha")
    if not isinstance(batches, list) or not batches or any(
            not isinstance(batch, dict) for batch in batches):
        raise PackError(f"{INVENTORY_REL_PATH}: inventário deve ser array de objetos")
    # Reparse estrito da região exata: chaves duplicadas seriam last-wins no
    # raw_decode acima e mudariam a projeção de donos silenciosamente.
    producer.decode_json_no_duplicate_keys(
        raw, f"{INVENTORY_REL_PATH}: inventário")
    return snapshot, batches, array_start, array_end


def _load_portfolios(root: pathlib.Path):
    portfolio_dir = root / PORTFOLIO_DIR_REL_PATH
    if pathlib.Path(os.path.realpath(portfolio_dir)) != portfolio_dir:
        raise PackError("diretório de portfólios não pode conter symlink")
    files = {}
    owners = {}
    for path in sorted(portfolio_dir.glob("*.jsonl"), key=lambda p: p.name):
        rel_path = path.relative_to(root).as_posix()
        if _PORTFOLIO_REL.fullmatch(rel_path) is None:
            raise PackError(f"portfólio com path não canônico: {rel_path!r}")
        snapshot = producer.read_regular_file_snapshot(
            path, max_bytes=_MAX_PORTFOLIO_BYTES)
        records = []
        fam_order = collections.defaultdict(list)
        seen = set()
        if not snapshot.payload.endswith(b"\n"):
            raise PackError(f"{rel_path}: portfólio não termina com newline")
        for line_number, raw_line in enumerate(
                snapshot.payload.splitlines(), start=1):
            record = producer.decode_json_no_duplicate_keys(
                raw_line, f"{rel_path}:{line_number}")
            if not isinstance(record, dict):
                raise PackError(f"{rel_path}:{line_number}: registro não é objeto")
            intent_id = record.get("intent_id")
            family = record.get("family")
            hints = record.get("source_hints")
            needs_research = record.get("needs_source_research")
            if (not isinstance(intent_id, str) or
                    _INTENT.fullmatch(intent_id) is None or
                    not isinstance(family, str) or
                    _FAMILY.fullmatch(family) is None or
                    not isinstance(hints, list) or len(hints) > 32 or
                    any(not isinstance(hint, str) or not hint or
                        hint != hint.strip() for hint in hints) or
                    len(set(hints)) != len(hints) or
                    type(needs_research) is not bool or
                    intent_id in seen):
                # A mesma identidade que relaunch-writing.sh exige (:300-338):
                # emitir lote sobre registro fora do contrato só adia o erro.
                raise PackError(
                    f"{rel_path}:{line_number}: registro fora do contrato da fila")
            prior = owners.get(intent_id)
            if prior is not None:
                raise PackError(
                    f"intent_id duplicado entre portfólios: {intent_id}: "
                    f"{prior}, {rel_path}")
            owners[intent_id] = rel_path
            seen.add(intent_id)
            fam_order[family].append(intent_id)
            records.append({
                "intent_id": intent_id,
                "family": family,
                "source_hints": list(hints),
                "needs_source_research": needs_research,
            })
        files[rel_path] = {
            "snapshot": snapshot,
            "records": records,
            "fam_order": dict(fam_order),
        }
    if not files:
        raise PackError("estoque de portfólios está vazio")
    return files


def _owned_intents(batches, portfolios):
    owned = {}
    for index, batch in enumerate(batches, start=1):
        label = f"inventário lote {index} ({batch.get('slug')!r})"
        rel_path = batch.get("file")
        portfolio = portfolios.get(rel_path)
        if portfolio is None:
            raise PackError(f"{label}: portfólio ausente: {rel_path!r}")
        take = batch.get("take")
        skip = batch.get("skip")
        count = batch.get("n")
        families = batch.get("families")
        if (not isinstance(families, list) or not families or
                type(take) is not int or take < 0 or
                type(skip) is not int or skip < 0 or
                type(count) is not int or count < 1):
            raise PackError(f"{label}: seletor fora do contrato")
        if take > 0:
            if len(families) != 1 or take != count or "intent_ids" in batch:
                raise PackError(f"{label}: slice fora do contrato")
            family_intents = portfolio["fam_order"].get(families[0], [])
            selected = family_intents[skip:skip + take]
        else:
            selected = batch.get("intent_ids")
            if (skip != 0 or not isinstance(selected, list) or
                    len(selected) != count or
                    len(set(selected)) != len(selected)):
                raise PackError(f"{label}: pin fora do contrato")
        if len(selected) != count:
            raise PackError(
                f"{label}: seleção={len(selected)} diverge de n={count}")
        for intent_id in selected:
            prior = owned.get(intent_id)
            if prior is not None:
                raise PackError(
                    f"intent com mais de um dono no inventário: {intent_id}: "
                    f"{prior}, {batch.get('slug')!r}")
            owned[intent_id] = batch.get("slug")
    return owned


def _written_intents(root: pathlib.Path):
    pages_dir = root / PAGES_DIR_REL_PATH
    written = set()
    existing_shards = set()
    if not pages_dir.is_dir():
        raise PackError(f"{PAGES_DIR_REL_PATH}: diretório de shards ausente")
    for path in sorted(pages_dir.glob("*.jsonl"), key=lambda p: p.name):
        name = path.name.lower()
        existing_shards.add(path.stem)
        if name.startswith(".") or any(
                marker in name for marker in _FINALIZED_SHARD_MARKERS):
            continue
        with open(path, "rb") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    raise PackError(
                        f"{path.name}:{line_number}: linha vazia no estoque")
                try:
                    record = json.loads(stripped)
                except ValueError as error:
                    raise PackError(
                        f"{path.name}:{line_number}: JSON inválido no "
                        f"estoque: {error}") from error
                intent_id = record.get("intent_id") if isinstance(
                    record, dict) else None
                if isinstance(intent_id, str):
                    written.add(intent_id)
    return written, existing_shards


def _load_catalog(root: pathlib.Path):
    snapshot = producer.read_regular_file_snapshot(
        root / SOURCE_HINT_CATALOG_REL_PATH, max_bytes=_MAX_CATALOG_BYTES)
    catalog = producer.decode_json_no_duplicate_keys(
        snapshot.payload, "catálogo source_hint")
    if (not isinstance(catalog, dict) or
            set(catalog) != {"_meta", "strict_intents", "source_hints"} or
            not isinstance(catalog["strict_intents"], list) or
            not isinstance(catalog["source_hints"], dict)):
        raise PackError("catálogo source_hint perdeu o schema fechado")
    # "Resolvido" = presente E com URL documental que o produtor aceita
    # (producer._canonical_official_source_url, o MESMO critério de
    # generate_v2_review_queue.py:1523). Entrada presente com URL inválida
    # classifica o intent como B (aguarda generate-catalog-url-repair) em vez
    # de virar classe A e abortar a produção inteira na prova do preflight.
    resolved_hints = {
        hint for hint, entry in catalog["source_hints"].items()
        if isinstance(entry, dict) and
        producer._canonical_official_source_url(entry.get("url"))}
    present_hints = set(catalog["source_hints"])
    return snapshot, present_hints, resolved_hints, set(catalog["strict_intents"])


def _classify_record(record, present_hints, resolved_hints, strict_intents):
    """Espelha derive_writing_source_resolution (fila reprova a classe B).

    Classe A passa o preflight hoje; classe B é exatamente a família
    emit-clean do relaunch: pesquisa declarada concluída (ou intent strict)
    com hint ainda fora do catálogo — ou hint PRESENTE no catálogo com URL
    inválida, que o preflight real reprova com "URL oficial HTTPS inválida"
    (mesma família emit-clean; aguarda generate-catalog-url-repair).
    """
    unresolved = [hint for hint in record["source_hints"]
                  if hint not in resolved_hints]
    if any(hint in present_hints for hint in unresolved):
        return "B"
    if not unresolved:
        if record["intent_id"] in strict_intents and not record["source_hints"]:
            return "B"
        return "A"
    if record["intent_id"] in strict_intents:
        return "B"
    if record["needs_source_research"] is False:
        return "B"
    return "A"


def _next_slug_allocator(batches, existing_shards):
    used_slugs = {batch.get("slug") for batch in batches}
    next_index = collections.defaultdict(int)
    for slug in used_slugs:
        if not isinstance(slug, str):
            raise PackError("inventário contém slug não textual")
    for batch in batches:
        area = batch.get("area")
        slug = batch.get("slug")
        prefix = f"{area}-"
        if isinstance(area, str) and slug.startswith(prefix):
            suffix = slug[len(prefix):]
            if suffix.isdigit():
                next_index[area] = max(next_index[area], int(suffix) + 1)

    def allocate(area: str) -> str:
        index = max(next_index[area], 1)
        while True:
            slug = f"{area}-{index:02d}"
            index += 1
            if slug in used_slugs or slug in existing_shards:
                continue
            next_index[area] = index
            used_slugs.add(slug)
            return slug

    return allocate


def _pack_area(area, rel_path, selected_records, allocate):
    """Agrupa por família em ordem de portfólio e corta em lotes de até 22.

    A ordem dos intent_ids é (família na ordem de primeira aparição no
    arquivo, intents na ordem do arquivo dentro da família): cada família
    forma UMA corrida contígua por lote — o invariante não-intercalado que
    relaunch-writing.sh:363-374 e o fechamento exigem. Família maior que o
    espaço restante continua no lote seguinte (cada lote declara apenas as
    famílias que realmente contém).
    """
    grouped = collections.OrderedDict()
    for record in selected_records:
        grouped.setdefault(record["family"], []).append(record["intent_id"])
    ordered_ids = []
    family_of = {}
    for family, intent_ids in grouped.items():
        for intent_id in intent_ids:
            ordered_ids.append(intent_id)
            family_of[intent_id] = family
    batches = []
    for start in range(0, len(ordered_ids), MAX_BATCH_PAGES):
        chunk = ordered_ids[start:start + MAX_BATCH_PAGES]
        families = []
        for intent_id in chunk:
            family = family_of[intent_id]
            if not families or families[-1] != family:
                if family in families:
                    raise PackError(
                        f"empacotador intercalou família {family} em {area}")
                families.append(family)
        batches.append({
            "families": families,
            "skip": 0,
            "take": 0,
            "n": len(chunk),
            "area": area,
            "file": rel_path,
            "slug": allocate(area),
            "intent_ids": chunk,
        })
    return batches


def _validate_new_batch(batch, portfolios):
    slug = batch["slug"]
    area = batch["area"]
    rel_path = batch["file"]
    if (_SLUG.fullmatch(slug) is None or _AREA.fullmatch(area) is None or
            _PORTFOLIO_REL.fullmatch(rel_path) is None or
            rel_path != f"{PORTFOLIO_DIR_REL_PATH}/{area}.jsonl" or
            not slug.startswith(f"{area}-") or
            batch["skip"] != 0 or batch["take"] != 0 or
            not 1 <= batch["n"] <= MAX_BATCH_PAGES or
            len(batch["intent_ids"]) != batch["n"] or
            len(set(batch["intent_ids"])) != batch["n"] or
            not batch["families"] or
            len(set(batch["families"])) != len(batch["families"]) or
            any(_FAMILY.fullmatch(family) is None
                for family in batch["families"]) or
            any(_INTENT.fullmatch(intent_id) is None
                for intent_id in batch["intent_ids"]) or
            list(batch) != ["families", "skip", "take", "n", "area", "file",
                            "slug", "intent_ids"]):
        raise PackError(f"lote novo não canônico: {slug!r}")
    portfolio = portfolios[rel_path]
    family_by_intent = {
        record["intent_id"]: record["family"]
        for record in portfolio["records"]
    }
    observed = []
    for intent_id in batch["intent_ids"]:
        family = family_by_intent.get(intent_id)
        if family is None:
            raise PackError(f"lote {slug}: pin fora do portfólio: {intent_id}")
        if family not in batch["families"]:
            raise PackError(
                f"lote {slug}: pin de família não declarada: {intent_id}")
        if not observed or observed[-1] != family:
            if family in observed:
                raise PackError(f"lote {slug}: famílias intercaladas: {family}")
            observed.append(family)
    if observed != batch["families"]:
        raise PackError(
            f"lote {slug}: ordem de famílias diverge do pin: "
            f"observadas={observed!r} declaradas={batch['families']!r}")


def _prove_source_preflight(root, batch, portfolios, catalog_snapshot,
                            expected_class):
    """Prova cada lote contra o preflight REAL do redator antes de escrever.

    Classe A tem de passar derive+verify (a mesma identidade base64 do
    template). Classe B tem de falhar EXATAMENTE na família emit-clean do
    relaunch; qualquer outra falha aborta a produção — controle negativo
    embutido, não um relaxamento.
    """
    portfolio = portfolios[batch["file"]]
    try:
        resolution = producer.derive_writing_source_resolution(
            root, batch["file"], portfolio["snapshot"].digest,
            SOURCE_HINT_CATALOG_REL_PATH, catalog_snapshot.digest,
            batch["families"], 0, 0, batch["n"], list(batch["intent_ids"]))
    except (ValueError, producer.CASMismatch) as error:
        message = str(error)
        if expected_class == "B" and any(
                marker in message for marker in _EMIT_CLEAN_MARKERS):
            return "emit-clean"
        raise PackError(
            f"lote {batch['slug']}: preflight de fontes reprovaria fora da "
            f"classe emit-clean: {message}") from error
    if expected_class == "B":
        raise PackError(
            f"lote {batch['slug']}: classificado B mas o preflight passou — "
            "classificador local divergiu do produtor")
    if resolution.selected_intents != tuple(batch["intent_ids"]):
        raise PackError(
            f"lote {batch['slug']}: seleção do preflight diverge do pin")
    projection_base64 = base64.b64encode(json.dumps(
        {
            "source_overrides": dict(resolution.source_overrides),
            "strict_source_intents": list(resolution.strict_source_intents),
        },
        ensure_ascii=False,
    ).encode("utf-8")).decode("ascii")
    producer.verify_writing_source_resolution(
        root, batch["file"], portfolio["snapshot"].digest,
        SOURCE_HINT_CATALOG_REL_PATH, catalog_snapshot.digest,
        batch["families"], 0, 0, batch["n"], list(batch["intent_ids"]),
        projection_base64)
    return "preflight-ok"


def build_plan(root: pathlib.Path):
    inventory_snapshot, batches, _, array_end = _load_inventory(root)
    portfolios = _load_portfolios(root)
    owned = _owned_intents(batches, portfolios)
    written, existing_shards = _written_intents(root)
    catalog_snapshot, present_hints, resolved_hints, strict_intents = (
        _load_catalog(root))
    allocate = _next_slug_allocator(batches, existing_shards)
    new_batches = []
    per_area = {}
    orphan_written = 0
    for rel_path in sorted(portfolios):
        portfolio = portfolios[rel_path]
        area = pathlib.PurePosixPath(rel_path).stem
        selected = {"A": [], "B": []}
        for record in portfolio["records"]:
            intent_id = record["intent_id"]
            if intent_id in owned:
                continue
            if intent_id in written:
                orphan_written += 1
                continue
            selected[_classify_record(
                record, present_hints, resolved_hints,
                strict_intents)].append(record)
        if not selected["A"] and not selected["B"]:
            continue
        area_batches = []
        for source_class in ("A", "B"):
            if not selected[source_class]:
                continue
            for batch in _pack_area(
                    area, rel_path, selected[source_class], allocate):
                batch_class = source_class
                area_batches.append((batch_class, batch))
        per_area[area] = {
            "A": sum(len(b["intent_ids"]) for cls, b in area_batches
                     if cls == "A"),
            "B": sum(len(b["intent_ids"]) for cls, b in area_batches
                     if cls == "B"),
            "lotes": len(area_batches),
        }
        new_batches.extend(area_batches)
    return {
        "inventory_snapshot": inventory_snapshot,
        "batches": batches,
        "array_end": array_end,
        "portfolios": portfolios,
        "catalog_snapshot": catalog_snapshot,
        "owned": owned,
        "written": written,
        "orphan_written": orphan_written,
        "new_batches": new_batches,
        "per_area": per_area,
    }


def validate_plan(root: pathlib.Path, plan) -> dict:
    portfolios = plan["portfolios"]
    owned = dict(plan["owned"])
    proofs = collections.Counter()
    for batch_class, batch in plan["new_batches"]:
        _validate_new_batch(batch, portfolios)
        for intent_id in batch["intent_ids"]:
            prior = owned.get(intent_id)
            if prior is not None:
                raise PackError(
                    f"lote {batch['slug']}: intent já tem dono: "
                    f"{intent_id} ({prior!r})")
            owned[intent_id] = batch["slug"]
        proofs[_prove_source_preflight(
            root, batch, portfolios, plan["catalog_snapshot"], batch_class)] += 1
    return dict(proofs)


def _splice_inventory(plan) -> bytes:
    payload = plan["inventory_snapshot"].payload
    array_end = plan["array_end"]
    encoded = []
    for _, batch in plan["new_batches"]:
        encoded.append(json.dumps(batch, ensure_ascii=False).encode("utf-8"))
    addition = b"," + b", ".join(encoded)
    new_payload = payload[:array_end - 1] + addition + payload[array_end - 1:]
    marker_index = new_payload.find(_MARKER)
    text = new_payload[marker_index + len(_MARKER):].decode("utf-8")
    reparsed, _ = json.JSONDecoder().raw_decode(text)
    expected_total = len(plan["batches"]) + len(plan["new_batches"])
    if len(reparsed) != expected_total:
        raise PackError(
            f"splice divergente: {len(reparsed)} lotes != {expected_total}")
    if reparsed[:len(plan["batches"])] != plan["batches"]:
        raise PackError("splice alterou lotes existentes — abortado")
    if reparsed[len(plan["batches"]):] != [
            batch for _, batch in plan["new_batches"]]:
        raise PackError("splice não materializou os lotes novos exatos")
    return new_payload


def _atomic_write(root: pathlib.Path, rel_path: str, payload: bytes,
                  expected_digest: str):
    target = root / rel_path
    live_digest = producer.read_regular_file_snapshot(
        target, max_bytes=_MAX_INVENTORY_BYTES).digest
    if live_digest != expected_digest:
        raise PackError(
            f"{rel_path} evoluiu durante a produção; regenerar o plano")
    fd, temp_path = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_path)
        raise


def _area_sources_aliases(root: pathlib.Path, portfolios) -> tuple:
    snapshot = producer.read_regular_file_snapshot(
        root / AREA_SOURCES_REL_PATH, max_bytes=_MAX_AREA_SOURCES_BYTES)
    area_sources = producer.decode_json_no_duplicate_keys(
        snapshot.payload, "mapa v2_area_sources")
    if (not isinstance(area_sources, dict) or
            not isinstance(area_sources.get("_meta"), dict)):
        raise PackError("mapa v2_area_sources perdeu o schema raiz")
    for area, sources in area_sources.items():
        if area == "_meta":
            continue
        if (not _AREA.fullmatch(area) or not isinstance(sources, list) or
                any(not isinstance(source, dict) or
                    set(source) != {"name", "url"} or
                    any(not isinstance(source[field], str) or not source[field]
                        or source[field] != source[field].strip()
                        for field in ("name", "url"))
                    for source in sources)):
            raise PackError(f"mapa v2_area_sources não canônico: {area}")
    aliases = {}
    for rel_path in sorted(portfolios):
        area = pathlib.PurePosixPath(rel_path).stem
        if area in area_sources:
            continue
        base = re.sub(r"-(?:w3|r\d+)$", "", area)
        if base != area and base in area_sources and area_sources[base]:
            aliases[area] = [dict(source) for source in area_sources[base]]
    if not aliases:
        return snapshot, None, {}
    updated = dict(area_sources)
    updated.update(aliases)
    payload = (json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True)
               + "\n").encode("utf-8")
    return snapshot, payload, aliases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--apply", action="store_true",
        help="escreve o inventário (default: só planeja e valida)")
    parser.add_argument(
        "--with-area-sources", action="store_true",
        help="também estende v2_area_sources.json com aliases -w3/-rNN")
    args = parser.parse_args()
    root = pathlib.Path(os.path.abspath(args.root))
    if not (root / INVENTORY_REL_PATH).is_file():
        raise SystemExit(f"--root inválido: {root}")

    lock_handle = open(PRODUCER_LOCK_PATH, "a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("generate-v2-writing-inventory-pack: produtor da fila ativo; "
              "tente depois", file=sys.stderr)
        return 75

    plan = build_plan(root)
    proofs = validate_plan(root, plan)
    class_a = [b for cls, b in plan["new_batches"] if cls == "A"]
    class_b = [b for cls, b in plan["new_batches"] if cls == "B"]
    pages_a = sum(b["n"] for b in class_a)
    pages_b = sum(b["n"] for b in class_b)
    print(json.dumps({
        "novos_lotes": len(plan["new_batches"]),
        "lotes_classe_a": len(class_a),
        "paginas_classe_a": pages_a,
        "lotes_classe_b_aguardam_catalogo": len(class_b),
        "paginas_classe_b": pages_b,
        "provas_preflight": proofs,
        "orfaos_ja_escritos_fora_do_inventario": plan["orphan_written"],
        "media_paginas_por_lote": round(
            (pages_a + pages_b) / max(len(plan["new_batches"]), 1), 2),
        "por_area": plan["per_area"],
    }, ensure_ascii=False, sort_keys=True, indent=2))
    if not plan["new_batches"]:
        print("nada a empacotar: todo intent de portfólio tem dono ou página")
        return 0
    if not args.apply:
        print("dry-run: use --apply para escrever o inventário")
        return 0

    new_payload = _splice_inventory(plan)
    _atomic_write(root, INVENTORY_REL_PATH, new_payload,
                  plan["inventory_snapshot"].digest)
    reloaded = producer.read_regular_file_snapshot(
        root / INVENTORY_REL_PATH, max_bytes=_MAX_INVENTORY_BYTES)
    if reloaded.payload != new_payload:
        raise PackError("inventário divergiu depois do replace atômico")
    print(f"inventário atualizado: {INVENTORY_REL_PATH} "
          f"({plan['inventory_snapshot'].digest[:12]} -> {reloaded.digest[:12]})")

    if args.with_area_sources:
        sources_snapshot, sources_payload, aliases = _area_sources_aliases(
            root, plan["portfolios"])
        if sources_payload is None:
            print("v2_area_sources.json já cobre todas as áreas do portfólio")
        else:
            _atomic_write(root, AREA_SOURCES_REL_PATH, sources_payload,
                          sources_snapshot.digest)
            print(f"aliases de fontes por área: {sorted(aliases)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PackError as error:
        print(f"generate-v2-writing-inventory-pack: {error}", file=sys.stderr)
        sys.exit(1)
