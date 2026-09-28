#!/usr/bin/env python3
"""Verifica se a fila de escrita fecha o inventário contra shards vivos.

Uma fila ``todo`` é uma projeção negativa: todo lote que ela omite afirma que
o shard correspondente já está estruturalmente completo. Este check torna a
afirmação executável. Em checkout limpo, qualquer shard omitido que não tenha
sido integrado ao mesmo commit deixa de existir (ou volta a bytes antigos) e
o check reprova, impedindo uma fila que só funciona na worktree do produtor.

ATÉ 2026-09-10 o parágrafo acima era a regra INTEIRA, e por isso ele fica
SUPERADO nesta data — sem ser apagado, porque continua descrevendo o que a
fila afirma quando omite um lote COMPLETO. O motivo é datado e medido: em
2026-07-22 (``2956359d``) o produtor ganhou um TERCEIRO estado, o
``emit-clean``. Lote cujo ``source_hint`` não tem resolução exata no catálogo
não pode ser enfileirado — sem URL oficial, data e hash não se escreve linha
nenhuma (R9) — então ele sai da fila, é registrado com a lista exata de hints
no manifesto de defeitos, e os lotes limpos seguem. A invariante deste
verificador foi escrita em 2026-07-14 (``b475677f``), OITO DIAS ANTES desse
estado existir, e nunca soube dele.

A consequência foi medida em 2026-09-10: 802 lotes no inventário, 359
bloqueados por fonte, e 86 lotes omitidos-e-incompletos reprovando este
verificador — 85 deles bloqueados por fonte. O verde era inalcançável por
redação: nenhuma página escrita move um lote que o produtor recusa enfileirar.

A regra passa a ser, então: **um lote omitido da fila afirma que o shard está
completo OU que ele está bloqueado por resolução de fonte** — e o bloqueio é
RE-DERIVADO ao vivo aqui (``_source_resolution_blocker``), pelo mesmo
predicado do produtor (``producer.source_resolution_blocking_defect``), nunca
lido de manifesto e nunca de lista de exceção. Qualquer outra razão para um
lote omitido estar incompleto continua reprovando, e os bloqueados saem
contados e nomeados em ``source_blocked_batches``/``source_blocked_evidence``,
para que a dívida de curadoria fique visível em vez de virar carimbo.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import math
import os
import pathlib
import re
import sys
from typing import Any, Iterable, Mapping

_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import audit_v2_pages as auditor
from tools import generate_v2_review_queue as producer
from tools import v2_portfolio_intent_migrations as migrations


_BASE_REQUIRED_FIELDS = frozenset(
    ("families", "skip", "take", "n", "area", "file", "slug")
)
_BASE_COMPARISON_FIELDS = _BASE_REQUIRED_FIELDS | {"intent_ids"}
_REQUIRED_TODO_FIELDS = _BASE_REQUIRED_FIELDS | {
    "writer",
    "sources",
    "source_overrides",
    "strict_source_intents",
    "source_hint_catalog_sha256",
    "portfolio_sha256",
    "semantic_contract_sha256",
    "preserved_record_sha256",
    "target_sha256",
}
_OPTIONAL_TODO_FIELDS = {
    "model",
    "intent_ids",
    "reuse",
    "preserve_extras",
    "semantic_relocation_removals",
    "portfolio_intent_migration",
    "writing_recovery",
}
_MAX_FULL_WORKFLOW_BYTES = 16 * 1024 * 1024
_MAX_TODO_WORKFLOW_BYTES = 128 * 1024 * 1024
_MAX_SOURCE_CATALOG_BYTES = 8 * 1024 * 1024
_MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024
_MAX_TARGET_BYTES = 64 * 1024 * 1024
_MAX_OFFICIAL_SOURCE_URL_BYTES = producer._MAX_OFFICIAL_SOURCE_URL_BYTES
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SLUG = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)+")
_AREA = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)*")
_FAMILY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PORTFOLIO = re.compile(
    r"data/editorial/portfolio_v2/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"
)


def _decode_json_strict(
    value: str | bytes,
    label: str,
    *,
    max_depth: int = 64,
) -> Any:
    """Decodifica JSON real, sem aliases last-wins nem números não finitos.

    O decoder compartilhado antigo recusava somente a repetição byte a byte.
    Isso ainda deixava ``intent_id`` + ``INTENT_ID`` com duas interpretações:
    Python preservava ambas, enquanto consumidores Go de structs escolhiam um
    campo por ``EqualFold``. A fila é uma fronteira de autenticação; portanto,
    uma mesma classe Unicode/casefold só pode nomear uma chave por objeto.
    """
    if not isinstance(value, (str, bytes)):
        raise TypeError(f"{label}: payload JSON deve ser texto ou bytes")
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{label}: JSON não é UTF-8") from error
    if type(max_depth) is not int or max_depth < 0:
        raise ValueError(f"{label}: limite de profundidade inválido")

    def closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        aliases: dict[str, str] = {}
        for key, item in pairs:
            folded = key.casefold()
            prior = aliases.get(folded)
            if prior is not None:
                raise ValueError(
                    f"{label}: chave JSON ambígua {key!r} aliases {prior!r}")
            aliases[folded] = key
            result[key] = item
        return result

    def reject_constant(token: str) -> Any:
        raise ValueError(f"{label}: constante JSON inválida: {token}")

    try:
        decoded = json.loads(
            value,
            object_pairs_hook=closed_object,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"{label}: JSON inválido") from error

    stack: list[tuple[Any, int]] = [(decoded, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > max_depth:
            raise ValueError(
                f"{label}: profundidade JSON excede {max_depth}")
        if isinstance(item, dict):
            stack.extend((key, depth + 1) for key in item)
            stack.extend((nested, depth + 1) for nested in item.values())
        elif isinstance(item, list):
            stack.extend((nested, depth + 1) for nested in item)
        elif isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValueError(
                    f"{label}: string JSON contém surrogate inválido") from error
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError(f"{label}: número JSON não finito")
    return decoded


def _decode_jsonl_strict(payload: bytes, label: str) -> list[dict[str, Any]]:
    if not payload or not payload.endswith(b"\n"):
        raise ValueError(f"{label} deve terminar com newline")
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload[:-1].split(b"\n"), 1):
        if not raw:
            raise ValueError(f"{label}:{line_number}: linha vazia")
        record = _decode_json_strict(raw, f"{label}:{line_number}")
        if not isinstance(record, dict):
            raise ValueError(f"{label}:{line_number}: registro não é objeto")
        records.append(record)
    return records


def _canonical_root(root: pathlib.Path | str) -> pathlib.Path:
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ValueError("root inválido")
    absolute = pathlib.Path(os.path.abspath(raw))
    resolved = pathlib.Path(os.path.realpath(absolute))
    if resolved != absolute:
        raise ValueError("root não pode conter symlink")
    if not absolute.is_dir():
        raise ValueError("root deve ser diretório existente")
    return absolute


def _static_batches(
    path: pathlib.Path,
    *,
    max_bytes: int,
    require_nonempty: bool,
) -> tuple[list[dict[str, Any]], str]:
    snapshot = producer.read_regular_file_snapshot(path, max_bytes=max_bytes)
    prefix = b"const batches = "
    matching = [line for line in snapshot.payload.splitlines()
                if line.startswith(prefix)]
    if len(matching) != 1:
        raise ValueError(f"{path}: inventário estático ausente ou ambíguo")
    try:
        batches = _decode_json_strict(
            matching[0][len(prefix):], str(path))
    except ValueError as error:
        raise ValueError(f"{path}: inventário JSON inválido") from error
    if not isinstance(batches, list) or (require_nonempty and not batches):
        qualifier = " não vazia" if require_nonempty else ""
        raise ValueError(f"{path}: inventário deve ser lista{qualifier}")
    if any(not isinstance(batch, dict) for batch in batches):
        raise ValueError(f"{path}: lote não é objeto")
    return batches, snapshot.digest


# ★ DOIS TETOS DIFERENTES, E CONFUNDI-LOS REPROVAVA TRABALHO ENTREGUE
# (medido em 2026-08-30).
#
# 22 e o tamanho maximo da FATIA (skip/take sobre uma familia). Lote PINADO nao
# fatia nada: ele carrega a lista exata de intent_ids, e o n dele e o tamanho do
# pino. O teto do pino e o hard max de epoch — o mesmo 31 de
# ops/relaunch-review.sh:669 e de scripts/workflows/writing-review.js:983.
# Aplicar 22 aos dois reprovava `bancario-07` e `aereo-09`, que tem 23 pinos
# cada e shards vivos de exatamente 23 linhas: o inventario estava certo.
_MAX_PINNED_BATCH_N = 31


# ★ O PREFIXO DE AREA NO SLUG ERA CONVENCAO, NAO INTEGRIDADE (removido em
# 2026-08-30).
#
# A regra exigia `slug.startswith(area + "-")` e reprovava 29 lotes do
# inventario integral — TODOS os 29 com shard escrito no disco e com a contagem
# de linhas batendo. Sao campanhas cruzadas: `codex-sucessoes-transito-r14`
# escreve em `transito`, `administrativo-r01` em `servidor`, `sucessoes-r01` em
# `sucessoes2`, `energia-r02` e `telecom-r03` em `telecom_energia`, `pi-r02` em
# `inpi`. O nome do lote guarda a ORIGEM da campanha; o destino ja e declarado
# por `file`.
#
# Nada de integridade se perde ao remove-la, e isso foi verificado clausula a
# clausula: a associacao lote->portfolio continua travada por
# `rel_path == portfolio_v2/{area}.jsonl`; a unicidade do shard, pelo
# `slug in full_by_slug`; e o pertencimento de cada intent pinado, por
# `_expected_intents` (:458-468), que levanta "intent_id pinado fora do
# portfolio" e "family do intent_id pinado diverge". O que a regra fazia de
# fato era reprovar a nomenclatura de campanha depois de a pagina ja estar
# escrita — reprovacao sem defeito.
def _validate_base_batch(batch: Mapping[str, Any], label: str) -> str:
    slug = batch.get("slug")
    area = batch.get("area")
    rel_path = batch.get("file")
    families = batch.get("families")
    skip = batch.get("skip")
    take = batch.get("take")
    count = batch.get("n")
    intent_ids = batch.get("intent_ids")
    has_intent_ids = "intent_ids" in batch
    if (not isinstance(slug, str) or _SLUG.fullmatch(slug) is None or
            not isinstance(area, str) or _AREA.fullmatch(area) is None or
            not isinstance(rel_path, str) or
            _PORTFOLIO.fullmatch(rel_path) is None or
            not isinstance(families, list) or not families or
            any(not isinstance(family, str) or
                _FAMILY.fullmatch(family) is None for family in families) or
            len(set(families)) != len(families) or
            type(skip) is not int or skip < 0 or
            type(take) is not int or take < 0 or
            type(count) is not int or count < 1 or
            count > (22 if take > 0 else _MAX_PINNED_BATCH_N) or
            (take > 0 and (len(families) != 1 or take != count)) or
            (take == 0 and skip != 0) or
            (take > 0 and has_intent_ids) or
            (take == 0 and (
                not has_intent_ids or
                not isinstance(intent_ids, list) or
                len(intent_ids) != count or
                any(not isinstance(intent_id, str) or
                    _ID.fullmatch(intent_id) is None
                    for intent_id in intent_ids) or
                len(set(intent_ids)) != len(intent_ids))) or
            rel_path != f"data/editorial/portfolio_v2/{area}.jsonl"):
        raise ValueError(f"{label}: lote-base não canônico")
    return slug


def _canonical_id_list(value: Any, label: str) -> list[str]:
    if (not isinstance(value, list) or
            any(not isinstance(item, str) or _ID.fullmatch(item) is None
                for item in value) or
            len(set(value)) != len(value)):
        raise ValueError(f"{label}: lista de IDs não canônica")
    return list(value)


def _canonical_semantic_relocation_removals(
    value: Any, label: str,
) -> list[dict[str, str]]:
    required = {
        "intent_id", "record_sha256", "owner_target_rel_path",
        "requirement_sha256",
    }
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: remoções semânticas não canônicas")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(value, 1):
        if (not isinstance(item, dict) or set(item) != required or
                not isinstance(item.get("intent_id"), str) or
                _ID.fullmatch(item["intent_id"]) is None or
                item["intent_id"] in seen or
                not isinstance(item.get("owner_target_rel_path"), str) or
                producer._TARGET_REL_PATH.fullmatch(
                    item["owner_target_rel_path"]) is None or
                any(not isinstance(item.get(field), str) or
                    _SHA256.fullmatch(item[field]) is None
                    for field in ("record_sha256", "requirement_sha256"))):
            raise ValueError(
                f"{label}: remoção semântica inválida na posição {index}")
        seen.add(item["intent_id"])
        result.append(dict(item))
    return result


def _validate_todo_batch(batch: Mapping[str, Any], label: str) -> str:
    fields = set(batch)
    if (not _REQUIRED_TODO_FIELDS.issubset(fields) or
            not fields.issubset(_REQUIRED_TODO_FIELDS | _OPTIONAL_TODO_FIELDS)):
        raise ValueError(f"{label}: schema aberto ou incompleto")
    slug = _validate_base_batch(batch, label)
    if batch.get("writer") != "redator-juridico":
        raise ValueError(f"{label}: writer inválido")
    if "model" in batch and batch["model"] != "opus":
        raise ValueError(f"{label}: model inválido")
    for field in ("target_sha256", "portfolio_sha256",
                  "semantic_contract_sha256",
                  "source_hint_catalog_sha256"):
        if (not isinstance(batch.get(field), str) or
                _SHA256.fullmatch(batch[field]) is None):
            raise ValueError(f"{label}: {field} inválido")
    sources = batch.get("sources")
    if not isinstance(sources, list) or len(sources) > 16:
        raise ValueError(f"{label}: sources inválidas")
    for source_index, source in enumerate(sources, 1):
        if (not isinstance(source, Mapping) or
                not isinstance(source.get("url"), str)):
            raise ValueError(f"{label}: sources inválidas")
        try:
            producer._canonical_candidate_source(
                source, f"{label}:sources:{source_index}")
        except ValueError as error:
            raise ValueError(f"{label}: sources inválidas: {error}") from error
    overrides = batch.get("source_overrides")
    if not isinstance(overrides, dict):
        raise ValueError(f"{label}: source_overrides inválido")
    for intent_id, hints in overrides.items():
        if (not isinstance(intent_id, str) or _ID.fullmatch(intent_id) is None or
                not isinstance(hints, dict) or not hints):
            raise ValueError(f"{label}: source_overrides não canônico")
        for hint, source in hints.items():
            if (not isinstance(hint, str) or _ID.fullmatch(hint) is None or
                    not isinstance(source, dict)):
                raise ValueError(f"{label}: resolução exata de fonte inválida")
            try:
                producer._canonical_exact_source(
                    source,
                    f"{label}:source_overrides:{intent_id}:{hint}",
                )
            except ValueError as error:
                raise ValueError(
                    f"{label}: resolução exata de fonte inválida: {error}"
                ) from error
    _canonical_id_list(batch.get("strict_source_intents"),
                       label + ":strict_source_intents")
    preserved = batch.get("preserved_record_sha256")
    if (not isinstance(preserved, dict) or
            any(not isinstance(intent_id, str) or
                _ID.fullmatch(intent_id) is None or
                not isinstance(digest, str) or _SHA256.fullmatch(digest) is None
                for intent_id, digest in preserved.items())):
        raise ValueError(f"{label}: hashes preservados inválidos")
    for field in ("reuse", "preserve_extras"):
        if field in batch:
            _canonical_id_list(batch[field], label + ":" + field)
    if "semantic_relocation_removals" in batch:
        _canonical_semantic_relocation_removals(
            batch["semantic_relocation_removals"],
            label + ":semantic_relocation_removals",
        )
    if "writing_recovery" in batch:
        take = batch.get("take")
        expected_recovery_intents = (
            batch.get("intent_ids") if take == 0 else None)
        try:
            canonical_recovery = (
                producer.validate_writing_raw_recovery_projection(
                    batch["writing_recovery"],
                    target_rel_path=f"data/editorial/v2_pages/{slug}.jsonl",
                    target_sha256=batch.get("target_sha256"),
                    expected_intents=expected_recovery_intents,
                ))
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"{label}: writing_recovery inválido: {error}") from error
        if (canonical_recovery.get("expected_n") != batch.get("n") or
                canonical_recovery.get("reuse") != batch.get("reuse", []) or
                canonical_recovery.get("preserved_record_sha256") !=
                batch.get("preserved_record_sha256", {}) or
                "preserve_extras" in batch or
                "semantic_relocation_removals" in batch or
                "portfolio_intent_migration" in batch):
            raise ValueError(
                f"{label}: writing_recovery coexistiu com rota divergente")
    return slug


def _snapshot_finalized_stock(root: pathlib.Path) -> dict[str, str]:
    pages_dir = root / "data/editorial/v2_pages"
    snapshots: dict[str, str] = {}
    for path in sorted(pages_dir.glob("*.jsonl")):
        if not auditor.is_finalized_v2_path(path.as_posix()):
            continue
        rel_path = path.relative_to(root).as_posix()
        snapshots[rel_path] = producer.read_regular_file_snapshot(
            path, max_bytes=_MAX_TARGET_BYTES).digest
    return snapshots


def _snapshot_digest(
    path: pathlib.Path,
    *,
    max_bytes: int,
    missing_ok: bool = False,
) -> str:
    try:
        return producer.read_regular_file_snapshot(
            path, max_bytes=max_bytes).digest
    except FileNotFoundError:
        if missing_ok:
            return hashlib.sha256(b"").hexdigest()
        raise


def _portfolio_records(
    root: pathlib.Path,
    rel_path: str,
    cache: dict[str, tuple[bytes, str, Mapping[str, list[str]]]],
) -> tuple[bytes, str, Mapping[str, list[str]]]:
    if rel_path in cache:
        return cache[rel_path]
    if _PORTFOLIO.fullmatch(rel_path) is None:
        raise ValueError(f"portfolio inseguro na fila: {rel_path!r}")
    snapshot = producer.read_regular_file_snapshot(
        root / rel_path, max_bytes=_MAX_PORTFOLIO_BYTES)
    by_family: dict[str, list[str]] = {}
    seen: set[str] = set()
    for line_number, record in enumerate(
            _decode_jsonl_strict(snapshot.payload, rel_path), 1):
        family = record.get("family")
        intent_id = record.get("intent_id")
        if (not isinstance(family, str) or
                _FAMILY.fullmatch(family) is None or
                not isinstance(intent_id, str) or
                _ID.fullmatch(intent_id) is None or intent_id in seen):
            raise ValueError(
                f"portfolio não canônico em {rel_path}:{line_number}")
        seen.add(intent_id)
        by_family.setdefault(family, []).append(intent_id)
    result = (snapshot.payload, snapshot.digest, by_family)
    cache[rel_path] = result
    return result


def _portfolio_rel_paths(root: pathlib.Path) -> list[str]:
    portfolio_dir = root / "data/editorial/portfolio_v2"
    if pathlib.Path(os.path.realpath(portfolio_dir)) != portfolio_dir:
        raise ValueError("diretório de portfólios não pode conter symlink")
    try:
        entries = sorted(portfolio_dir.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise ValueError("diretório de portfólios indisponível") from error
    rel_paths: list[str] = []
    for path in entries:
        if path.suffix != ".jsonl":
            continue
        rel_path = path.relative_to(root).as_posix()
        if _PORTFOLIO.fullmatch(rel_path) is None:
            raise ValueError(f"portfolio com path não canônico: {rel_path!r}")
        rel_paths.append(rel_path)
    if not rel_paths:
        raise ValueError("estoque de portfólios está vazio")
    return rel_paths


def _expected_intents(
    batch: Mapping[str, Any],
    by_family: Mapping[str, list[str]],
) -> list[str]:
    families = batch.get("families")
    skip = batch.get("skip")
    take = batch.get("take")
    count = batch.get("n")
    intent_ids = batch.get("intent_ids")
    has_intent_ids = "intent_ids" in batch
    if (not isinstance(families, list) or not families or
            any(not isinstance(family, str) or not family
                for family in families) or len(set(families)) != len(families) or
            type(skip) is not int or skip < 0 or
            type(take) is not int or take < 0 or
            type(count) is not int or count < 1 or
            count > (22 if take > 0 else _MAX_PINNED_BATCH_N) or
            (take > 0 and has_intent_ids) or
            (take == 0 and (
                not has_intent_ids or
                not isinstance(intent_ids, list) or
                len(intent_ids) != count or
                any(not isinstance(intent_id, str) or
                    _ID.fullmatch(intent_id) is None
                    for intent_id in intent_ids) or
                len(set(intent_ids)) != len(intent_ids)))):
        raise ValueError(f"seletor inválido no lote {batch.get('slug')!r}")
    if take > 0:
        if len(families) != 1:
            raise ValueError(f"slice multi-família inválido em {batch.get('slug')}")
        selected = list(by_family.get(families[0], [])[skip:skip + take])
    else:
        if skip != 0:
            raise ValueError(f"skip sem take em {batch.get('slug')}")
        assert isinstance(intent_ids, list)
        family_by_intent = {
            intent_id: family
            for family, family_intents in by_family.items()
            for intent_id in family_intents
        }
        selected = []
        allowed_families = set(families)
        for intent_id in intent_ids:
            owner_family = family_by_intent.get(intent_id)
            if owner_family is None:
                raise ValueError(
                    f"intent_id pinado fora do portfolio em "
                    f"{batch.get('slug')}: {intent_id}")
            if owner_family not in allowed_families:
                raise ValueError(
                    f"family do intent_id pinado diverge em "
                    f"{batch.get('slug')}: {intent_id}: {owner_family}")
            selected.append(intent_id)
        observed_family_runs: list[str] = []
        for intent_id in selected:
            owner_family = family_by_intent[intent_id]
            if (not observed_family_runs or
                    observed_family_runs[-1] != owner_family):
                observed_family_runs.append(owner_family)
        if observed_family_runs != families:
            raise ValueError(
                "ordem/cobertura de families do pin diverge em "
                f"{batch.get('slug')}: observadas={observed_family_runs!r} "
                f"declaradas={families!r}")
    if len(selected) != count or len(set(selected)) != len(selected):
        raise ValueError(
            f"slice do portfólio diverge em {batch.get('slug')}: "
            f"selecionados={len(selected)} n={count}")
    return selected


_CENSUS_KEYS = (
    "shard_ausente",
    "linha_faltante",
    "intent_duplicado",
    "bloqueio_semantico",
    "corpo_nao_reusavel",
    "cardinalidade",
    "ordem_divergente",
    "substituicao_integral_autenticada",
)


def _error_census_key(error: str) -> str:
    """Classe do erro para o censo do cabeçalho.

    Lê as palavras-chave que o classificador emite em ``BatchCompletion.reasons``
    — vocabulário compartilhado com ``tools/generate-writing-queue-blocker-census``.
    Um lote pode ter mais de um motivo; o censo conta pelo PRIMEIRO da ordem
    canônica das cláusulas, que é o que decide o destino do lote (falta redação
    antes de faltar ordem). Erro que não casa nenhuma palavra-chave entra como
    ``outros`` em vez de sumir — ausência de classe nunca vira ausência de erro.
    """
    for key in _CENSUS_KEYS:
        if key in error:
            return key
    return "outros"


def _source_resolution_blocker(
    root: pathlib.Path,
    batch: Mapping[str, Any],
    catalog_digest: str,
    portfolio_cache: dict[str, tuple[bytes, str, Mapping[str, list[str]]]],
) -> str | None:
    """Este lote está bloqueado por RESOLUÇÃO DE FONTE, medido ao vivo?

    Devolve a mensagem do produtor quando o lote não pode sequer ser
    enfileirado por falta de resolução exata de ``source_hint`` — o único
    defeito que ``ops/relaunch-writing.sh`` emite-clean —, e ``None`` em
    qualquer outro caso, inclusive quando a projeção passa.

    RE-DERIVA, não lê manifesto. ``data/ops/relaunch_writing_defects_*.jsonl``
    é datado pelo mtime do inventário e reescrito a cada execução do produtor:
    depender dele faria o fechamento da fila depender de um arquivo que
    qualquer sessão regenera. Aqui a pergunta é feita à MESMA função que o
    produtor chama, sobre os bytes vivos do portfólio e do catálogo, sob os
    mesmos digests já autenticados neste run.
    """
    try:
        _, portfolio_digest, _ = _portfolio_records(
            root, batch["file"], portfolio_cache)
    except (KeyError, OSError, RuntimeError, ValueError):
        return None
    try:
        producer.derive_writing_source_resolution(
            root,
            batch["file"],
            portfolio_digest,
            "data/editorial/v2_source_hint_catalog.json",
            catalog_digest,
            batch["families"],
            batch["skip"],
            batch["take"],
            batch["n"],
            batch.get("intent_ids"),
        )
    except (OSError, RuntimeError, ValueError) as error:
        detalhe = str(error)
        if producer.source_resolution_blocking_defect(detalhe):
            return detalhe
        return None
    return None


@contextlib.contextmanager
def _working_directory(path: pathlib.Path):
    previous = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def verify(
    root: pathlib.Path | str,
    excluded_areas: Iterable[str] = (),
) -> dict[str, int]:
    canonical_root = _canonical_root(root)
    excluded_values = list(excluded_areas)
    if any(not isinstance(area, str) or _AREA.fullmatch(area) is None
           for area in excluded_values):
        raise ValueError("área excluída não canônica")
    if excluded_values:
        raise ValueError(
            "fila canônica não admite exclusão run-scoped de área")

    full_path = canonical_root / "scripts/workflows/writing-mass-full.js"
    todo_path = canonical_root / "scripts/workflows/writing-mass-todo.js"
    full, full_digest = _static_batches(
        full_path, max_bytes=_MAX_FULL_WORKFLOW_BYTES, require_nonempty=True)
    todo, todo_digest = _static_batches(
        todo_path, max_bytes=_MAX_TODO_WORKFLOW_BYTES, require_nonempty=False)
    full_by_slug: dict[str, dict[str, Any]] = {}
    for index, batch in enumerate(full, 1):
        expected_fields = (
            _BASE_REQUIRED_FIELDS | {"intent_ids"}
            if batch.get("take") == 0 else _BASE_REQUIRED_FIELDS
        )
        if set(batch) != expected_fields:
            raise ValueError(f"inventário lote {index}: schema aberto ou incompleto")
        slug = _validate_base_batch(batch, f"inventário lote {index}")
        if slug in full_by_slug:
            raise ValueError(f"slug integral inválido ou duplicado: {slug!r}")
        full_by_slug[slug] = batch

    catalog_path = canonical_root / "data/editorial/v2_source_hint_catalog.json"
    catalog_digest = producer.read_regular_file_snapshot(
        catalog_path, max_bytes=_MAX_SOURCE_CATALOG_BYTES).digest
    portfolio_cache: dict[str, tuple[bytes, str, Mapping[str, list[str]]]] = {}
    portfolio_rel_paths = _portfolio_rel_paths(canonical_root)
    portfolio_owner: dict[str, str] = {}
    for rel_path in portfolio_rel_paths:
        _, _, by_family = _portfolio_records(
            canonical_root, rel_path, portfolio_cache)
        for intent_ids in by_family.values():
            for intent_id in intent_ids:
                prior = portfolio_owner.get(intent_id)
                if prior is not None:
                    raise ValueError(
                        "intent_id global duplicado nos portfólios: "
                        f"{intent_id}: {prior}, {rel_path}")
                portfolio_owner[intent_id] = rel_path
    expected_by_slug: dict[str, list[str]] = {}
    intent_owner: dict[str, str] = {}
    for slug, batch in full_by_slug.items():
        _, _, by_family = _portfolio_records(
            canonical_root, batch["file"], portfolio_cache)
        expected = _expected_intents(batch, by_family)
        expected_by_slug[slug] = expected
        for intent_id in expected:
            prior = intent_owner.get(intent_id)
            if prior is not None:
                raise ValueError(
                    "intent_id pertence a mais de um slice do inventário: "
                    f"{intent_id}: {prior}, {slug}")
            intent_owner[intent_id] = slug
    # ★ "TEM DONO NO INVENTARIO **OU** JA TEM PAGINA ESCRITA" (2026-08-30).
    #
    # A regra anterior era cobertura EXATA e reprovava 912 intents. Eles nao sao
    # buraco de producao: rodando o empacotador canonico
    # (tools/generate_v2_writing_inventory_pack.py) o veredito foi
    # `orfaos_ja_escritos_fora_do_inventario: 912`, `novos_lotes: 0`, "nada a
    # empacotar: todo intent de portfolio tem dono ou pagina". Sao as ondas
    # `-w3`, `*-derivada-01`, `diarios-municipais-01` e `noticias-oficiais-01`,
    # escritas por outra rota depois de este inventario ser congelado. Exigi-los
    # aqui mandaria redigir 912 paginas que ja existem — e a regra usada e a do
    # proprio empacotador, nao uma invencao deste verificador.
    #
    # Pagina escrita = intent_id PRESENTE no shard. Arquivo existir nao basta:
    # um shard parcial esconderia intent nunca redigido.
    written_intents: set[str] = set()
    for shard_path in sorted(
            (canonical_root / "data/editorial/v2_pages").glob("*.jsonl")):
        for line in shard_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            intent_id = record.get("intent_id")
            if isinstance(intent_id, str) and intent_id:
                written_intents.add(intent_id)
    orphan_intents = sorted(
        set(portfolio_owner) - set(intent_owner) - written_intents)
    unknown_intents = sorted(set(intent_owner) - set(portfolio_owner))
    if orphan_intents or unknown_intents:
        details: list[str] = []
        if orphan_intents:
            details.append(
                "intent_id de portfolio sem lote nem pagina escrita: " +
                ", ".join(orphan_intents[:12]))
        if unknown_intents:
            details.append(
                "intent_id selecionado fora dos portfólios: " +
                ", ".join(unknown_intents[:12]))
        raise ValueError(
            "inventário deixa intent de portfólio sem dono nem página: " +
            "; ".join(details))
    todo_slugs: set[str] = set()
    target_digests: dict[str, str] = {}
    errors: list[str] = []

    with _working_directory(canonical_root):
        migration_catalog = migrations.load_catalog(canonical_root)
        stock_before = _snapshot_finalized_stock(canonical_root)
        semantic_contract = producer.load_writing_semantic_contract(
            canonical_root)
        semantic_unknown = sorted(
            set(semantic_contract.requirement_fingerprints) -
            set(intent_owner)
        )
        if semantic_unknown:
            errors.append(
                "contrato semântico contém intent sem lote canônico: " +
                ", ".join(semantic_unknown[:12]))
        semantic_misbound = sorted(
            intent_id
            for intent_id, target_rel_path in (
                semantic_contract.target_rel_paths.items())
            if (intent_id in intent_owner and
                target_rel_path !=
                f"data/editorial/v2_pages/{intent_owner[intent_id]}.jsonl")
        )
        if semantic_misbound:
            errors.append(
                "contrato semântico ligado ao shard errado: " +
                ", ".join(semantic_misbound[:12]))
        winners, supersession_issues = (
            auditor.validated_duplicate_supersession_winners(canonical_root))
        if supersession_issues:
            errors.append(
                "projeção DEC-020 contém problemas: " +
                ", ".join(supersession_issues[:8]))
        for index, batch in enumerate(todo, 1):
            try:
                slug = _validate_todo_batch(batch, f"fila lote {index}")
            except ValueError as error:
                errors.append(str(error))
                continue
            if slug in todo_slugs:
                errors.append(f"fila repete ou perde slug canônico: {slug!r}")
                continue
            todo_slugs.add(slug)
            original = full_by_slug.get(slug)
            if original is None:
                errors.append(f"fila contém lote fora do inventário: {slug}")
                continue
            if any((field in batch) != (field in original) or
                   batch.get(field) != original.get(field)
                   for field in _BASE_COMPARISON_FIELDS):
                errors.append(f"campos-base do lote divergiram: {slug}")
                continue
            try:
                portfolio_payload, portfolio_digest, _ = _portfolio_records(
                    canonical_root, batch["file"], portfolio_cache)
                expected = expected_by_slug[slug]
                projection = {
                    "source_overrides": batch["source_overrides"],
                    "strict_source_intents": batch["strict_source_intents"],
                }
                encoded_projection = base64.b64encode(json.dumps(
                    projection, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")).decode("ascii")
                resolution = producer.verify_writing_source_resolution(
                    canonical_root,
                    batch["file"], batch["portfolio_sha256"],
                    "data/editorial/v2_source_hint_catalog.json",
                    batch["source_hint_catalog_sha256"],
                    batch["families"], batch["skip"], batch["take"],
                    batch["n"], batch.get("intent_ids"), encoded_projection)
                if list(resolution.selected_intents) != expected:
                    raise ValueError("projeção de fontes mudou a ordem do slice")
                target_rel = f"data/editorial/v2_pages/{slug}.jsonl"
                target_path = canonical_root / target_rel
                try:
                    target_snapshot = producer.read_regular_file_snapshot(
                        target_path, max_bytes=_MAX_TARGET_BYTES)
                except FileNotFoundError:
                    target_snapshot = None
                    target_payload = b""
                    target_digest = hashlib.sha256(b"").hexdigest()
                    records: list[dict[str, Any]] = []
                    raw_lines: list[bytes] = []
                else:
                    target_payload = target_snapshot.payload
                    target_digest = target_snapshot.digest
                    records = _decode_jsonl_strict(
                        target_payload, target_rel)
                    raw_lines = target_payload[:-1].split(b"\n")
                target_digests[target_rel] = target_digest
                if (not isinstance(batch.get("target_sha256"), str) or
                        _SHA256.fullmatch(batch["target_sha256"]) is None or
                        batch["target_sha256"] != target_digest):
                    errors.append(f"target_sha256 stale: {slug}")
                if batch.get("portfolio_sha256") != portfolio_digest:
                    errors.append(f"portfolio_sha256 stale: {slug}")
                if batch.get("source_hint_catalog_sha256") != catalog_digest:
                    errors.append(f"source_hint_catalog_sha256 stale: {slug}")
                if (batch.get("semantic_contract_sha256") !=
                        semantic_contract.digest):
                    errors.append(f"semantic_contract_sha256 stale: {slug}")
                expected_authorization = None
                semantic_blocked = producer.semantic_blocked_for_batch(
                    expected, semantic_contract)
                relocation_removals = (
                    producer.semantic_relocation_removals_for_target(
                        target_rel,
                        tuple(zip(raw_lines, records)),
                        semantic_contract,
                    )
                )
                relocation_ids = {
                    item["intent_id"] for item in relocation_removals
                }
                if relocation_ids & set(expected):
                    raise ValueError(
                        "remoção semântica ainda pertence ao slice pinado")
                classification_records = [
                    record for record in records
                    if record.get("intent_id") not in relocation_ids
                ]
                try:
                    completion = producer.classify_batch_completion(
                        classification_records, expected, f"{slug}.jsonl", winners,
                        semantically_blocked_intents=semantic_blocked)
                except ValueError as ordinary_error:
                    if target_snapshot is None:
                        raise
                    expected_authorization = migrations.queue_authorization(
                        migration_catalog, f"{slug}.jsonl",
                        target_payload, target_digest, batch["file"],
                        portfolio_payload, portfolio_digest, expected,
                        batch["families"], batch["skip"], batch["take"],
                        batch["n"], batch.get("intent_ids"))
                    if expected_authorization is None:
                        raise ordinary_error
                    if relocation_removals:
                        raise ValueError(
                            "relocação semântica coexistiu com migração integral")
                    completion = producer.classify_batch_completion(
                        classification_records, expected, f"{slug}.jsonl", winners,
                        authenticated_replacement_intents=(
                            expected_authorization["source_intent_ids"]),
                        semantically_blocked_intents=semantic_blocked)
                if completion.complete and not relocation_removals:
                    raise ValueError("fila contém lote já completo")
                expected_relocations = list(relocation_removals)
                if (("semantic_relocation_removals" in batch) !=
                        bool(expected_relocations) or
                        batch.get("semantic_relocation_removals", []) !=
                        expected_relocations):
                    raise ValueError(
                        "semantic_relocation_removals diverge da preimagem")
                raw_by_intent: dict[str, list[str]] = {}
                for record, raw_line in zip(records, raw_lines):
                    intent_id = record.get("intent_id")
                    if isinstance(intent_id, str):
                        raw_by_intent.setdefault(intent_id, []).append(
                            hashlib.sha256(raw_line).hexdigest())
                expected_hashes: dict[str, str] = {}
                for intent_id in (*completion.reusable_expected,
                                  *completion.authenticated_extras):
                    hashes = raw_by_intent.get(intent_id, [])
                    if len(hashes) != 1:
                        raise ValueError(
                            f"registro preservado ambíguo: {intent_id}")
                    expected_hashes[intent_id] = hashes[0]
                expected_reuse = list(completion.reusable_expected)
                if (("reuse" in batch) != bool(expected_reuse) or
                        batch.get("reuse", []) != expected_reuse):
                    raise ValueError("reuse diverge da preimagem autenticada")
                expected_extras = list(completion.authenticated_extras)
                if (("preserve_extras" in batch) != bool(expected_extras) or
                        batch.get("preserve_extras", []) != expected_extras):
                    raise ValueError(
                        "preserve_extras diverge da projeção DEC-020")
                if batch["preserved_record_sha256"] != expected_hashes:
                    raise ValueError(
                        "preserved_record_sha256 diverge dos bytes vivos")
                authorization = batch.get("portfolio_intent_migration")
                if (("portfolio_intent_migration" in batch) !=
                        (expected_authorization is not None) or
                        authorization != expected_authorization):
                    raise ValueError(
                        "autorização de migração ausente, espúria ou stale")
                if expected_authorization is not None:
                    migrations.verify_queue_authorization(
                        canonical_root, authorization, target_rel, batch["file"],
                        expected, batch["families"], batch["skip"],
                        batch["take"], batch["n"],
                        batch.get("intent_ids"))
                    if authorization.get("registry_sha256") != (
                            migration_catalog.registry_sha256):
                        errors.append(f"registry_sha256 stale: {slug}")
            except (KeyError, OSError, RuntimeError, ValueError) as error:
                errors.append(f"lote queued inválido {slug}: {error}")

        completed = 0
        source_blocked: list[str] = []
        for slug, batch in full_by_slug.items():
            if slug in todo_slugs:
                continue
            try:
                expected = expected_by_slug[slug]
                target_rel = f"data/editorial/v2_pages/{slug}.jsonl"
                target_path = canonical_root / target_rel
                if not auditor.is_finalized_v2_path(target_path.as_posix()):
                    raise ValueError("path não pertence ao estoque finalizado")
                if not target_path.exists():
                    # Sem este ramo o erro que chega ao operador é o
                    # ``FileNotFoundError: 'bancario-19.jsonl'`` do snapshot,
                    # indistinguível de defeito de caminho. Shard ausente é a
                    # única classe em que TODA a redação falta, e o número que
                    # importa é quantas intenções do slice não existem em
                    # NENHUM shard do estoque.
                    ineditos = [
                        intent_id for intent_id in expected
                        if intent_id not in written_intents
                    ]
                    raise ValueError(
                        f"shard_ausente: nenhum byte em {target_rel}; "
                        f"{len(ineditos)} de {len(expected)} intenções do "
                        f"slice não existem em shard nenhum "
                        f"(aguardam redação)")
                snapshot = producer.read_regular_file_snapshot(
                    target_path, max_bytes=_MAX_TARGET_BYTES)
                target_digests[target_rel] = snapshot.digest
                records = _decode_jsonl_strict(snapshot.payload, target_rel)
                raw_lines = snapshot.payload[:-1].split(b"\n")
                relocation_removals = (
                    producer.semantic_relocation_removals_for_target(
                        target_rel,
                        tuple(zip(raw_lines, records)),
                        semantic_contract,
                    )
                )
                if relocation_removals:
                    raise ValueError(
                        "baseline relocada ainda presente fora da fila")
                semantic_blocked = producer.semantic_blocked_for_batch(
                    expected, semantic_contract)
                completion = producer.classify_batch_completion(
                    records, expected, f"{slug}.jsonl", winners,
                    semantically_blocked_intents=semantic_blocked)
                if not completion.complete:
                    # O motivo vem do classificador, que é quem sabe qual das
                    # cinco cláusulas reprovou. Reafirmar aqui só a frase
                    # genérica foi o que fez um dia inteiro de diagnóstico
                    # concluir "aguardam redação" para 34 lotes já escritos.
                    raise ValueError(
                        "classificador não confirmou lote completo: " +
                        ("; ".join(completion.reasons) or
                         "motivo não instrumentado"))
                completed += 1
            except (OSError, RuntimeError, ValueError) as error:
                # ★ TERCEIRO ESTADO (2026-09-10). Ver o parágrafo datado no
                # docstring do módulo: o produtor emite-clean lote bloqueado
                # por fonte, então "omitido" não implica "completo" desde
                # 2026-07-22. Só o bloqueio de FONTE, re-derivado ao vivo,
                # justifica a omissão de um lote incompleto — e ele é
                # contado e nomeado, nunca silenciado.
                bloqueio = _source_resolution_blocker(
                    canonical_root, batch, catalog_digest, portfolio_cache)
                if bloqueio is None:
                    errors.append(
                        f"lote omitido da fila e incompleto {slug}: {error}")
                else:
                    source_blocked.append(f"{slug}: {bloqueio}")

        # A fila é uma decisão multi-arquivo. Reautentique no fim tudo que
        # sustentou a decisão, inclusive o estoque global DEC-020. Um verde
        # calculado sobre mistura de preimages concorrentes não é evidência.
        try:
            if _snapshot_digest(
                    full_path, max_bytes=_MAX_FULL_WORKFLOW_BYTES) != full_digest:
                raise producer.CASMismatch("inventário integral evoluiu")
            if _snapshot_digest(
                    todo_path, max_bytes=_MAX_TODO_WORKFLOW_BYTES) != todo_digest:
                raise producer.CASMismatch("fila todo evoluiu")
            if _snapshot_digest(
                    catalog_path,
                    max_bytes=_MAX_SOURCE_CATALOG_BYTES) != catalog_digest:
                raise producer.CASMismatch("catálogo de fontes evoluiu")
            for rel_path, (_, digest, _) in portfolio_cache.items():
                if _snapshot_digest(
                        canonical_root / rel_path,
                        max_bytes=_MAX_PORTFOLIO_BYTES) != digest:
                    raise producer.CASMismatch(
                        f"portfólio evoluiu: {rel_path}")
            if _portfolio_rel_paths(canonical_root) != portfolio_rel_paths:
                raise producer.CASMismatch(
                    "conjunto de arquivos de portfólio evoluiu")
            for rel_path, digest in target_digests.items():
                if _snapshot_digest(
                        canonical_root / rel_path,
                        max_bytes=_MAX_TARGET_BYTES,
                        missing_ok=True) != digest:
                    raise producer.CASMismatch(f"shard evoluiu: {rel_path}")
            migrations._verify_catalog_dependencies(
                canonical_root, migration_catalog)
            winners_after, issues_after = (
                auditor.validated_duplicate_supersession_winners(
                    canonical_root))
            if winners_after != winners or issues_after != supersession_issues:
                raise producer.CASMismatch("projeção DEC-020 evoluiu")
            if _snapshot_finalized_stock(canonical_root) != stock_before:
                raise producer.CASMismatch("estoque finalizado evoluiu")
            producer.verify_writing_semantic_contract_dependencies(
                canonical_root, semantic_contract)
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(f"dependência evoluiu durante fechamento: {error}")

    if errors:
        # ★ AMOSTRA NUNCA SE APRESENTA COMO POPULAÇÃO (CONTRATO_DADO_REAL R3).
        #
        # O preview de 20 linhas sobre 86 erros levou uma sessão inteira a ler
        # os 20 primeiros, medir os shards deles e concluir sobre os 86. O
        # preview continua em 20 — erro de 86 linhas ninguém lê —, mas agora vem
        # precedido do CENSO da população inteira, agrupado pela primeira
        # palavra-chave de cada motivo. Quem ler o topo não consegue mais
        # confundir a amostra com o todo.
        census: dict[str, int] = {}
        for error in errors:
            census[_error_census_key(error)] = (
                census.get(_error_census_key(error), 0) + 1)
        breakdown = ", ".join(
            f"{chave}={contagem}"
            for chave, contagem in sorted(
                census.items(), key=lambda item: (-item[1], item[0])))
        preview = "\n".join(f"- {error}" for error in errors[:20])
        suffix = "" if len(errors) <= 20 else f"\n- ... +{len(errors) - 20} erros"
        raise ValueError(
            f"writing queue não fecha o inventário vivo: {len(errors)} erro(s) "
            f"[{breakdown}]; as {min(len(errors), 20)} primeiras linhas abaixo "
            f"são AMOSTRA, não a população:\n" + preview + suffix)
    return {
        "full_batches": len(full),
        "queued_batches": len(todo),
        "completed_batches": completed,
        "source_blocked_batches": len(source_blocked),
        "source_blocked_evidence": sorted(source_blocked),
        "excluded_batches": 0,
        "inventory_intents": len(intent_owner),
        "portfolio_intents": len(portfolio_owner),
        # A TERCEIRA PARCELA DA CONTABILIDADE (2026-09-10). As duas linhas
        # acima nunca foram iguais desde 2026-08-30, quando a regra passou a
        # ser "tem dono no inventario OU ja tem pagina escrita" — e o
        # consumidor Go continuava cobrando igualdade entre elas, reprovando
        # por uma invariante que este verificador ja tinha abandonado com
        # motivo escrito (ver a nota do empacotador canonico, acima).
        #
        # Emitir o numero fecha a conta em vez de afrouxa-la:
        # inventory + written_outside == portfolio, por construcao, porque o
        # conjunto abaixo e' exatamente `portfolio - inventario` e a validacao
        # que antecede este dicionario ja levantou se algum deles estivesse sem
        # pagina escrita (orphan_intents).
        "written_outside_inventory_intents": len(
            set(portfolio_owner) - set(intent_owner)),
        "supersession_issues": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--exclude-area", action="append", default=[])
    args = parser.parse_args()
    result = verify(args.root, args.exclude_area)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
