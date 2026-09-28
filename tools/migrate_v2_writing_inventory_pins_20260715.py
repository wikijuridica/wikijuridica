#!/usr/bin/env python3
"""Fixa seletores dinâmicos e reconcilia a fila de escrita v2 uma única vez.

O inventário histórico permitia ``take == 0`` sem identidade explícita. Uma
adição posterior ao portfólio mudava silenciosamente o significado do mesmo
slug e podia deslocar a fila em cascata. Este produtor transforma cada lote
dinâmico em um pin ordenado, preserva cinco lotes que excederiam o limite de
22 nas suas intenções anteriores e cobre somente as caudas ainda sem dono com
novos slices posicionais.

A operação não executa redatores, não altera ``v2_pages`` e não publica. Ela
reconstrói as duas filas bloqueadas a partir do estoque autenticado, instala o
trio sob CAS com rollback para frente e grava um recibo interno ``noindex``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
import argparse
import errno
import fcntl
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
from typing import Any, Callable, Iterable, Mapping, Sequence


_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import generate_v2_review_queue as queue
from tools import v2_portfolio_intent_migrations as portfolio_migrations


ROOT = _IMPORT_ROOT
FULL_REL = "scripts/workflows/writing-mass-full.js"
TODO_REL = "scripts/workflows/writing-mass-todo.js"
TODO_WITHOUT_TELECOM_REL = (
    "scripts/workflows/writing-mass-todo-sem-telecom.js"
)
TEMPLATE_REL = "scripts/workflows/writing-mass.js"
AREA_SOURCES_REL = "data/editorial/v2_area_sources.json"
SOURCE_CATALOG_REL = "data/editorial/v2_source_hint_catalog.json"
SEMANTIC_CONTRACT_REL = (
    "data/editorial/v2_writing_semantic_contract.json"
)
PREIMAGE_ROOT_REL = (
    "data/editorial/v2_migration_preimages/"
    "writing-inventory-pins-20260715"
)
PREIMAGE_ARCHIVE_BY_OUTPUT: Mapping[str, str] = {
    FULL_REL: f"{PREIMAGE_ROOT_REL}/{FULL_REL}",
    TODO_REL: f"{PREIMAGE_ROOT_REL}/{TODO_REL}",
    TODO_WITHOUT_TELECOM_REL: (
        f"{PREIMAGE_ROOT_REL}/{TODO_WITHOUT_TELECOM_REL}"
    ),
}
PREIMAGE_MANIFEST_REL = f"{PREIMAGE_ROOT_REL}/manifest.json"
RECEIPT_REL = (
    "data/editorial/v2_writing_inventory_pin_migration_20260715.json"
)
LOCK_PATH = pathlib.Path(
    "/tmp/opt-wiki-v2-writing-inventory-pin-migration.lock"
)

WORKFLOW_MARKER = b"const batches = "
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
MAX_WORKFLOW_BYTES = 128 * 1024 * 1024
MAX_PREIMAGE_MANIFEST_BYTES = 1024 * 1024
MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024
MAX_STOCK_BYTES = 64 * 1024 * 1024
EXPECTED_BATCHES_BEFORE = 667
EXPECTED_BATCHES_AFTER = 737
EXPECTED_PORTFOLIO_INTENTS = 7600
EXPECTED_TAKE_ZERO_BATCHES = 107
EXPECTED_NEW_BATCHES = 79
EXPECTED_NEW_INTENTS = 183
EXPECTED_AGGREGATE_BATCHES = 8
EXPECTED_RETIRED_BATCHES = 17
EXPECTED_ADJUSTED_BATCHES = 7
EXPECTED_COMPLETE_BATCHES = 373
EXPECTED_TODO_BATCHES = 364
EXPECTED_TODO_WITHOUT_TELECOM_BATCHES = 340
EXPECTED_SEMANTIC_REQUIREMENTS = 21
EXPECTED_UNRESOLVED_SEMANTIC_REQUIREMENTS = 21

# Preimagens finais são preenchidas somente depois dos três handoffs de código
# e runtime. Qualquer diferença exige uma nova migração datada, não um rerun
# adaptativo desta operação one-shot.
EXPECTED_INPUT_SHA256: Mapping[str, str] = {
    FULL_REL: "9ff9cce01b76e7b07dfe05869a8bd33ee6fbc59404d36b3728efb76eff558631",
    TODO_REL: "52cb3e61ce659da2455b8993c02470ddac59a39334e6d7e94f4232caa1ab6a7a",
    TODO_WITHOUT_TELECOM_REL: "7affd44ec221c5e036ec7da6d9c69d2502d7d2f7c46852b4531603bedfc335b3",
    TEMPLATE_REL: "861883226da603282a178fa6547a61e6f7c9f43f259cc31f09788935d6a4c447",
    AREA_SOURCES_REL: "404670dea102fcd910f84c14da43a4c73db334427ebaad204a4d5f14ae407aef",
    SOURCE_CATALOG_REL: "86f36512f9059f7a2c65f74f9de19da00c4b02220395131baaca286d24661d1e",
}
EXPECTED_PORTFOLIO_SET_SHA256 = (
    "4399a9e6bd704c54f811d0b639639a984bda50052d014027c2158cc2c705f309"
)
EXPECTED_AGGREGATE_SET_SHA256 = (
    "a0b0d5a4955426cbbe5f754ba9e0219c13258dc068721e2774fcf1b25917d079"
)

_SLUG = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)+\Z")
_AREA = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)*\Z")
_FAMILY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_INTENT = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_PORTFOLIO = re.compile(
    r"data/editorial/portfolio_v2/"
    r"[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl\Z"
)
_BASE_FIELDS = ("families", "skip", "take", "n", "area", "file", "slug")
_QUEUE_OWNED_FIELDS = {
    *_BASE_FIELDS,
    "intent_ids",
    "writer",
    "model",
    "sources",
    "source_overrides",
    "strict_source_intents",
    "source_hint_catalog_sha256",
    "portfolio_sha256",
    "reuse",
    "preserve_extras",
    "semantic_relocation_removals",
    "portfolio_intent_migration",
    "preserved_record_sha256",
    "target_sha256",
    "semantic_contract_sha256",
}
_FULL_FORBIDDEN_FIELDS = _QUEUE_OWNED_FIELDS - {
    *_BASE_FIELDS,
    "intent_ids",
}
_PUBLIC_FORBIDDEN_FIELDS = {
    "public_path",
    "publication_touches",
    "index_policy",
    "render_allowed",
    "sitemap_allowed",
    "publication_allowed",
    "approval",
    "publicly_indexable",
}
_OUTPUT_PATHS = frozenset({FULL_REL, TODO_REL, TODO_WITHOUT_TELECOM_REL})
_PREIMAGE_ARCHIVE_PATHS = frozenset(PREIMAGE_ARCHIVE_BY_OUTPUT.values())
_RECEIPT_KEYS = {
    "schema_version",
    "migration_id",
    "checked_at",
    "input_sha256",
    "absent_input_paths",
    "stock_sha256",
    "stock_set_sha256",
    "output_sha256",
    "preimage_manifest_sha256",
    "preimage_archive_sha256",
    "preimage_set_sha256",
    "counts",
    "overflow_pin_sha256",
    "publication_touches",
    "index_policy",
    "render_allowed",
    "sitemap_allowed",
    "publication_allowed",
    "approval",
    "publicly_indexable",
}
_HIGH_ACCURACY_AREAS = {"criminal", "sumulas", "tributario"}
_DPVAT_SOURCE_HINTS = (
    "lc-211-2024-art-4",
    "lc-207-2024-spvat-revogada",
    "lindb-art-2-par-3",
    "lei-14544-2023-fdpvat-2023",
    "res-cnsp-457-2022-fdpvat-2023",
    "caixa-dpvat-faq-2021-2023",
    "caixa-dpvat-servico-2021-2023",
    "susep-spvat-revogado-31-12-2024",
    "susep-dpvat-historico",
)

# Estes arquivos não são lixo nem novos intents: são oito shards editoriais
# completos que consolidam 99 IDs antes espalhados por 26 owners. A migração
# aposenta somente os slices totalmente substituídos, encurta sete slices e
# pinna os dois lotes multi-family afetados. Os bytes dos shards permanecem no
# mesmo path e entram como owners canônicos, sem cópia nem descarte.
AGGREGATE_SHARDS = (
    "consumidor-d01",
    "glossario2-d01",
    "glossario2-d02",
    "glossario2-d03",
    "glossario2-d04",
    "glossario2-d05",
    "seguros-d01",
    "tributario-d02",
)
RETIRED_BATCHES = frozenset({
    "consumidor-23",
    "consumidor-24",
    *(f"glossario2-{number:02d}" for number in range(22, 34)),
    "seguros-17",
    "tributario-27",
    "tributario-28",
})
SLICE_ADJUSTMENTS: Mapping[str, tuple[int, int]] = {
    "consumidor-21": (35, 4),
    "seguros-13": (13, 2),
    "seguros-14": (2, 1),
    "seguros-15": (3, 1),
    "seguros-16": (2, 2),
    "tributario-26": (0, 3),
    "tributario-29": (1, 2),
}
TAKE_ZERO_EXCLUSIONS: Mapping[str, frozenset[str]] = {
    "seguros-04": frozenset({"seg-auto-negativa-fuga-local"}),
    "seguros-06": frozenset({"seg-vida-beneficiario-causou-morte"}),
}

# Estes pins foram derivados da preimagem imediatamente anterior à expansão
# 2c423559 e revisados contra a ordem atual de cada família. As novas caudas
# permanecem no portfólio e recebem slices próprios; nenhum conteúdo é apagado.
OVERFLOW_PINS: Mapping[str, Sequence[str]] = {
    "aereo-09": (
        "aer-agencia-cancelou-pacote-reembolso",
        "aer-responsabilidade-solidaria-agencia-cia",
        "aer-ota-voo-cancelado-quem-devolve",
        "aer-operadora-falencia-viagem-paga",
        "aer-desistir-pacote-arrependimento-multa",
        "aer-pacote-hotel-diferente-anunciado",
        "aer-cruzeiro-cancelado-direitos",
        "aer-agencia-nao-emitiu-bilhete-pago",
        "aer-agencia-nao-repassou-bilhete-cancelado",
        "aer-hotel-overbooking-sem-quarto",
        "aer-hotel-cancelou-reserva-paga",
        "aer-cancelar-reserva-hotel-multa-arrependimento",
        "aer-plataforma-acomodacao-diferente-anuncio",
        "aer-anfitriao-cancelou-vespera-plataforma",
        "aer-hotel-taxa-servico-turismo-cobranca",
        "aer-furto-quarto-hotel-responsabilidade",
        "aer-menor-hotel-hospedagem-eca",
        "aer-hotel-no-show-cobranca-diaria",
        "aer-hotel-cobranca-danos-quarto",
    ),
    "seguros-05": (
        "seg-auto-acionar-seguro-do-culpado",
        "seg-auto-culpado-sem-seguro",
        "seg-auto-rcf-v-o-que-cobre",
        "seg-auto-vitima-processar-seguradora",
        "seg-auto-subrogacao-cobrando-culpado",
        "seg-auto-app-passageiro-lesao",
        "seg-auto-seguradora-culpado-nega-vitima",
        "seg-auto-franquia-o-que-e",
        "seg-auto-franquia-perda-total-roubo",
        "seg-auto-franquia-culpa-de-terceiro",
        "seg-auto-bonus-o-que-e",
        "seg-auto-perda-de-bonus",
        "seg-auto-transferir-bonus",
        "seg-auto-roubo-como-funciona",
        "seg-auto-carro-roubado-apareceu",
        "seg-auto-alagamento-enchente",
        "seg-auto-incendio",
        "seg-auto-vidros-farois",
        "seg-auto-furto-pertences-dentro",
        "seg-auto-carro-reserva",
        "seg-auto-assistencia-24h",
    ),
    "seguros-07": (
        "seg-vida-invalidez-doenca-ou-acidente",
        "seg-vida-invalidez-proporcional",
        "seg-vida-doencas-graves",
        "seg-vida-diaria-incapacidade-dit",
        "seg-vida-morte-acidental-adicional",
        "seg-vida-vs-acidentes-pessoais",
        "seg-vida-morte-presumida",
        "seg-vida-limite-idade-contratacao",
        "seg-vida-imposto-de-renda",
        "seg-vida-invalidez-inss-reconhece-seguradora-nega",
        "seg-vida-doenca-grave-negada-enquadramento",
        "seg-residencial-o-que-cobre",
        "seg-residencial-roubo-vs-furto",
        "seg-residencial-danos-eletricos",
        "seg-residencial-vendaval-granizo",
        "seg-residencial-vazamento-agua",
        "seg-residencial-rc-danos-vizinho",
        "seg-residencial-alugado-quem-contrata",
        "seg-residencial-imovel-desabitado",
        "seg-residencial-furto-sem-arrombamento",
        "seg-residencial-joias-valores-excluidos",
        "seg-residencial-incendio-negado-instalacao",
    ),
    "seguros-08": (
        "seg-prestamista-o-que-e",
        "seg-prestamista-quitacao-obito",
        "seg-prestamista-invalidez",
        "seg-prestamista-desemprego",
        "seg-prestamista-venda-casada",
        "seg-prestamista-cancelar-restituir",
        "seg-prestamista-descobrir-heranca",
        "seg-prestamista-banco-cobra-apos-obito",
        "seg-prestamista-desemprego-negado-autonomo",
        "seg-viagem-obrigatorio-europa",
        "seg-viagem-o-que-cobre",
        "seg-viagem-negativa-preexistente",
        "seg-viagem-bagagem-e-companhia",
        "seg-viagem-cancelamento",
        "seg-viagem-nacional",
        "seg-viagem-exclusoes-gestante-esporte",
        "seg-viagem-repatriacao-corpo",
        "seg-viagem-negativa-reembolso-exterior",
        "seg-garantia-estendida-vs-legal",
        "seg-garantia-estendida-cancelar",
        "seg-garantia-estendida-negou-conserto",
        "seg-garantia-estendida-loja-fechou",
    ),
    "seguros-09": (
        "seg-agravamento-de-risco",
        "seg-comunicar-agravamento",
        "seg-mora-premio-atraso",
        "seg-cancelamento-falta-pagamento",
        "seg-boa-fe-contrato",
        "seg-diminuicao-risco-desconto",
        "seg-empresarial-o-que-cobre",
        "seg-rc-geral-empresa",
        "seg-rc-profissional",
        "seg-do-diretores",
        "seg-garantia-o-que-e",
        "seg-garantia-judicial",
        "seg-condominio-obrigatorio",
        "seg-condominio-cobre-apartamento",
        "seg-lucros-cessantes-empresa",
        "seg-empresarial-negativa-lucros-cessantes",
        "seg-rc-profissional-negativa-dolo",
        "seg-condominio-sinistro-negado-area-comum",
        "seg-fianca-locaticia-como-funciona",
        "seg-fianca-seguradora-cobra-inquilino",
        "seg-fianca-nao-cobre-danos-imovel",
    ),
}


@dataclass(frozen=True)
class WorkflowDocument:
    prefix: bytes
    batches: list[dict[str, Any]]
    suffix: bytes

    def encode(self, batches: Sequence[Mapping[str, Any]]) -> bytes:
        encoded = json.dumps(
            list(batches), ensure_ascii=False, separators=(", ", ": ")
        ).encode("utf-8")
        return self.prefix + encoded + self.suffix


@dataclass(frozen=True)
class PortfolioSnapshot:
    rel_path: str
    payload: bytes
    digest: str
    records: tuple[Mapping[str, Any], ...]
    by_family: Mapping[str, tuple[str, ...]]
    family_by_intent: Mapping[str, str]


@dataclass(frozen=True)
class PreimageBundle:
    manifest: queue.RegularFileSnapshot
    archives: Mapping[str, queue.RegularFileSnapshot]


@dataclass(frozen=True)
class MigrationPlan:
    inputs: Mapping[str, queue.RegularFileSnapshot]
    dependency_sha256: Mapping[str, str]
    stock_sha256: Mapping[str, str]
    portfolio_paths: tuple[str, ...]
    semantic_contract: queue.WritingSemanticContract
    outputs: Mapping[str, bytes]
    preimage_bundle: PreimageBundle
    receipt_payload: bytes
    counts: Mapping[str, int]


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _preimage_set_digest(
    entries: Mapping[str, Mapping[str, Any]],
) -> str:
    """Liga o conjunto fechado de preimages às identidades e aos metadados."""
    return _digest(json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8"))


def _read_immutable_preimage(
    root: pathlib.Path,
    rel_path: str,
    *,
    missing_ok: bool,
) -> queue.RegularFileSnapshot | None:
    """Lê evidência append-only exigindo arquivo regular 0644 e link único."""
    try:
        directory_fd, name, absolute = queue._open_parent_directory(
            root / rel_path
        )
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    try:
        max_bytes = (
            MAX_PREIMAGE_MANIFEST_BYTES
            if rel_path == PREIMAGE_MANIFEST_REL else MAX_WORKFLOW_BYTES
        )
        snapshot = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=missing_ok,
            max_bytes=max_bytes,
        )
        if snapshot is None:
            return None
        if snapshot.mode != 0o644 or snapshot.nlink != 1:
            raise RuntimeError(
                "preimage imutável exige mode=0644 e nlink=1: "
                f"{absolute}"
            )
        return queue.RegularFileSnapshot(snapshot.payload, snapshot.digest)
    finally:
        os.close(directory_fd)


def _read_canonical_0644_artifact(
    root: pathlib.Path,
    rel_path: str,
    *,
    max_bytes: int,
) -> queue.RegularFileSnapshot:
    """Lê um artefato transacional exigindo modo e identidade canônicos.

    ``read_regular_file_snapshot`` já fecha bytes/hash e recusa hardlinks,
    mas deliberadamente aceita qualquer modo. Workflows e o receipt desta
    migração têm modo contratado 0644; aceitar somente o hash permitiria
    que um ``chmod`` concorrente ou posterior passasse como evidência íntegra.
    """
    directory_fd, name, absolute = queue._open_parent_directory(
        root / rel_path
    )
    try:
        snapshot = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=False,
            max_bytes=max_bytes,
        )
        if snapshot is None:  # estreita o tipo; missing_ok=False
            raise FileNotFoundError(absolute)
        if snapshot.mode != 0o644 or snapshot.nlink != 1:
            raise RuntimeError(
                "artefato transacional exige mode=0644 e nlink=1: "
                f"{absolute}"
            )
        return queue.RegularFileSnapshot(snapshot.payload, snapshot.digest)
    finally:
        os.close(directory_fd)


def _ensure_relative_directory(root: pathlib.Path, rel_path: str) -> None:
    """Cria diretórios por descritor, sem seguir ancestrais simbólicos."""
    pure = pathlib.PurePosixPath(rel_path)
    if (not rel_path or pure.is_absolute() or pure.as_posix() != rel_path or
            ".." in pure.parts):
        raise ValueError(f"diretório relativo inseguro: {rel_path!r}")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    directory_fd = os.open(os.path.abspath(os.fspath(root)), flags)
    try:
        for component in pure.parts:
            created = False
            try:
                os.mkdir(component, mode=0o755, dir_fd=directory_fd)
                created = True
            except FileExistsError:
                pass
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            if created:
                os.fsync(directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
    finally:
        os.close(directory_fd)


def _atomic_create_immutable(
    root: pathlib.Path,
    rel_path: str,
    payload: bytes,
) -> bool:
    """Cria por NOREPLACE ou reutiliza somente os mesmos bytes 0644/únicos."""
    max_bytes = (
        MAX_PREIMAGE_MANIFEST_BYTES
        if rel_path == PREIMAGE_MANIFEST_REL else MAX_WORKFLOW_BYTES
    )
    if not isinstance(payload, bytes) or len(payload) > max_bytes:
        raise ValueError(f"preimage ausente ou grande demais: {rel_path}")
    existing = _read_immutable_preimage(root, rel_path, missing_ok=True)
    if existing is not None:
        if existing.payload != payload or existing.digest != _digest(payload):
            raise queue.CASMismatch(
                f"preimage imutável existente diverge: {rel_path}"
            )
        return False

    directory_fd, name, absolute = queue._open_parent_directory(
        root / rel_path
    )
    temp_name: str | None = None
    try:
        # Reobserve sob o mesmo descritor que receberá o RENAME_NOREPLACE.
        raced = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=True,
            max_bytes=max_bytes,
        )
        if raced is not None:
            if (raced.mode == 0o644 and raced.nlink == 1 and
                    raced.payload == payload and
                    raced.digest == _digest(payload)):
                return False
            raise queue.CASMismatch(
                f"preimage apareceu com identidade divergente: {rel_path}"
            )
        temp_name, staged = queue._create_temp_at(
            directory_fd, name, payload, 0o644
        )
        try:
            queue._renameat2(
                directory_fd,
                temp_name,
                directory_fd,
                name,
                queue._RENAME_NOREPLACE,
            )
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
            raced = queue._read_snapshot_at(
                directory_fd,
                name,
                missing_ok=False,
                max_bytes=max_bytes,
            )
            if (raced is None or raced.mode != 0o644 or raced.nlink != 1 or
                    raced.payload != payload or
                    raced.digest != _digest(payload)):
                raise queue.CASMismatch(
                    f"criação concorrente divergiu: {rel_path}"
                ) from error
            return False
        temp_name = None
        os.fsync(directory_fd)
        installed = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=False,
            max_bytes=max_bytes,
        )
        if (installed is None or installed.mode != 0o644 or
                installed.nlink != 1 or
                not queue._same_snapshot(installed, staged)):
            raise queue.CASMismatch(
                f"preimage criado mudou durante autenticação: {absolute}"
            )
        return True
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)


def _preimage_entries(
    archives: Mapping[str, queue.RegularFileSnapshot],
) -> dict[str, dict[str, Any]]:
    if set(archives) != _PREIMAGE_ARCHIVE_PATHS:
        raise ValueError("conjunto de archives de preimage é incompleto")
    entries: dict[str, dict[str, Any]] = {}
    for active_path in sorted(PREIMAGE_ARCHIVE_BY_OUTPUT):
        archive_path = PREIMAGE_ARCHIVE_BY_OUTPUT[active_path]
        snapshot = archives[archive_path]
        expected = EXPECTED_INPUT_SHA256[active_path]
        if snapshot.digest != expected:
            raise queue.CASMismatch(
                f"archive não autentica preimage pinado: {archive_path}"
            )
        entries[active_path] = {
            "archive_path": archive_path,
            "sha256": snapshot.digest,
            "bytes": len(snapshot.payload),
            "mode": "0644",
            "nlink": 1,
        }
    return entries


def _preimage_manifest_payload(
    archives: Mapping[str, queue.RegularFileSnapshot],
) -> bytes:
    entries = _preimage_entries(archives)
    value = {
        "schema_version": "v2_writing_inventory_preimages_v1",
        "migration_id": "writing-inventory-pins-20260715",
        "checked_at": "2026-07-15",
        "preimages": entries,
        "preimage_set_sha256": _preimage_set_digest(entries),
        "publication_touches": [],
        "index_policy": "noindex",
        "render_allowed": False,
        "sitemap_allowed": False,
        "publication_allowed": False,
        "approval": False,
        "publicly_indexable": False,
    }
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _verify_preimage_manifest(root: pathlib.Path) -> PreimageBundle:
    manifest = _read_immutable_preimage(
        root, PREIMAGE_MANIFEST_REL, missing_ok=False
    )
    if manifest is None:  # estreita o tipo; missing_ok=False
        raise FileNotFoundError(root / PREIMAGE_MANIFEST_REL)
    if not manifest.payload or not manifest.payload.endswith(b"\n"):
        raise ValueError("manifest de preimages não termina com newline")
    value = queue.decode_json_no_duplicate_keys(
        manifest.payload, PREIMAGE_MANIFEST_REL
    )
    expected_keys = {
        "schema_version", "migration_id", "checked_at", "preimages",
        "preimage_set_sha256",
        "publication_touches", "index_policy", "render_allowed",
        "sitemap_allowed", "publication_allowed", "approval",
        "publicly_indexable",
    }
    if (not isinstance(value, dict) or set(value) != expected_keys or
            value.get("schema_version") !=
            "v2_writing_inventory_preimages_v1" or
            value.get("migration_id") !=
            "writing-inventory-pins-20260715" or
            value.get("checked_at") != "2026-07-15" or
            value.get("publication_touches") != [] or
            value.get("index_policy") != "noindex" or
            any(value.get(flag) is not False for flag in (
                "render_allowed", "sitemap_allowed",
                "publication_allowed", "approval", "publicly_indexable",
            )) or not isinstance(value.get("preimages"), dict) or
            not isinstance(value.get("preimage_set_sha256"), str) or
            re.fullmatch(
                r"[0-9a-f]{64}", value["preimage_set_sha256"]
            ) is None or
            set(value["preimages"]) != _OUTPUT_PATHS):
        raise ValueError("manifest de preimages tem schema/path-set inválido")

    archives: dict[str, queue.RegularFileSnapshot] = {}
    for active_path in sorted(_OUTPUT_PATHS):
        entry = value["preimages"][active_path]
        archive_path = PREIMAGE_ARCHIVE_BY_OUTPUT[active_path]
        if (not isinstance(entry, dict) or
                set(entry) != {
                    "archive_path", "sha256", "bytes", "mode", "nlink"
                } or entry.get("archive_path") != archive_path or
                entry.get("sha256") != EXPECTED_INPUT_SHA256[active_path] or
                type(entry.get("bytes")) is not int or
                entry["bytes"] < 0 or entry.get("mode") != "0644" or
                entry.get("nlink") != 1):
            raise ValueError(
                f"manifest não autentica preimage exato: {active_path}"
            )
        archive = _read_immutable_preimage(
            root, archive_path, missing_ok=False
        )
        if (archive is None or archive.digest != entry["sha256"] or
                len(archive.payload) != entry["bytes"]):
            raise queue.CASMismatch(
                f"archive diverge do manifest: {archive_path}"
            )
        archives[archive_path] = archive
    if value["preimage_set_sha256"] != _preimage_set_digest(
            value["preimages"]):
        raise ValueError(
            "manifest não liga preimage_set aos seus membros exatos"
        )
    canonical = _preimage_manifest_payload(archives)
    if canonical != manifest.payload or _digest(canonical) != manifest.digest:
        raise ValueError("manifest de preimages não é canônico")
    # Fecha o sandwich do bundle: manifest e raws precisam continuar com os
    # mesmos bytes, mode e nlink depois que a relação inteira foi recomposta.
    final_manifest = _read_immutable_preimage(
        root, PREIMAGE_MANIFEST_REL, missing_ok=False
    )
    if (final_manifest is None or final_manifest.payload != manifest.payload or
            final_manifest.digest != manifest.digest):
        raise queue.CASMismatch(
            "manifest de preimages mudou durante autenticação"
        )
    final_archives: dict[str, queue.RegularFileSnapshot] = {}
    for archive_path in sorted(archives):
        final_archive = _read_immutable_preimage(
            root, archive_path, missing_ok=False
        )
        if (final_archive is None or
                final_archive.payload != archives[archive_path].payload or
                final_archive.digest != archives[archive_path].digest):
            raise queue.CASMismatch(
                f"archive mudou durante autenticação: {archive_path}"
            )
        final_archives[archive_path] = final_archive
    return PreimageBundle(
        manifest=final_manifest,
        archives=final_archives,
    )


def _snapshot_active_preimages(
    root: pathlib.Path,
) -> dict[str, queue.RegularFileSnapshot]:
    snapshots: dict[str, queue.RegularFileSnapshot] = {}
    for rel_path in sorted(_OUTPUT_PATHS):
        snapshot = _read_canonical_0644_artifact(
            root, rel_path, max_bytes=MAX_WORKFLOW_BYTES
        )
        if snapshot.digest != EXPECTED_INPUT_SHA256[rel_path]:
            raise queue.CASMismatch(
                f"preimage ativa divergiu do pin: {rel_path}"
            )
        snapshots[rel_path] = snapshot
    return snapshots


def prepare_preimages(root: pathlib.Path = ROOT) -> PreimageBundle:
    """Persiste o bundle inerte append-only; nunca altera workflows ativos."""
    manifest = _read_immutable_preimage(
        root, PREIMAGE_MANIFEST_REL, missing_ok=True
    )
    if manifest is not None:
        return _verify_preimage_manifest(root)

    active = _snapshot_active_preimages(root)
    _ensure_relative_directory(
        root, pathlib.PurePosixPath(PREIMAGE_MANIFEST_REL).parent.as_posix()
    )
    _ensure_relative_directory(
        root,
        pathlib.PurePosixPath(
            PREIMAGE_ARCHIVE_BY_OUTPUT[FULL_REL]
        ).parent.as_posix(),
    )
    for active_path in sorted(_OUTPUT_PATHS):
        _atomic_create_immutable(
            root,
            PREIMAGE_ARCHIVE_BY_OUTPUT[active_path],
            active[active_path].payload,
        )
    archives = {
        archive_path: _read_immutable_preimage(
            root, archive_path, missing_ok=False
        )
        for archive_path in sorted(_PREIMAGE_ARCHIVE_PATHS)
    }
    if any(snapshot is None for snapshot in archives.values()):
        raise RuntimeError("archive de preimage desapareceu durante preparo")
    typed_archives = {
        path: snapshot for path, snapshot in archives.items()
        if snapshot is not None
    }
    current_active = {
        path: queue.snapshot_sha256(
            root / path, max_bytes=MAX_WORKFLOW_BYTES
        )
        for path in sorted(active)
    }
    queue.authenticate_snapshot_set(
        {path: snapshot.digest for path, snapshot in active.items()},
        current_active,
        active,
    )
    _atomic_create_immutable(
        root,
        PREIMAGE_MANIFEST_REL,
        _preimage_manifest_payload(typed_archives),
    )
    bundle = _verify_preimage_manifest(root)
    final_active = {
        path: queue.snapshot_sha256(
            root / path, max_bytes=MAX_WORKFLOW_BYTES
        )
        for path in sorted(active)
    }
    queue.authenticate_snapshot_set(current_active, final_active, active)
    final_bundle = _verify_preimage_manifest(root)
    if (final_bundle.manifest.digest != bundle.manifest.digest or
            {
                path: snapshot.digest
                for path, snapshot in final_bundle.archives.items()
            } != {
                path: snapshot.digest
                for path, snapshot in bundle.archives.items()
            }):
        raise queue.CASMismatch(
            "bundle de preimages mudou durante fechamento do preparo"
        )
    return final_bundle


def parse_workflow_document(payload: bytes, label: str) -> WorkflowDocument:
    if not isinstance(payload, bytes) or len(payload) > MAX_WORKFLOW_BYTES:
        raise ValueError(f"{label}: payload ausente ou grande demais")
    marker = payload.find(WORKFLOW_MARKER)
    if (marker < 0 or payload.find(WORKFLOW_MARKER, marker + 1) >= 0 or
            (marker > 0 and payload[marker - 1] != 0x0A)):
        raise ValueError(f"{label}: âncora const batches ambígua")
    start = marker + len(WORKFLOW_MARKER)
    try:
        tail = payload[start:].decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label}: workflow não é UTF-8") from error
    if not tail.startswith("["):
        raise ValueError(f"{label}: array não começa na âncora")
    try:
        _, end = json.JSONDecoder().raw_decode(tail)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label}: array JSON inválido") from error
    raw = tail[:end]
    value = queue.decode_json_no_duplicate_keys(raw, label)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: batches deve ser array não vazio")
    if any(not isinstance(batch, dict) for batch in value):
        raise ValueError(f"{label}: lote não é objeto")
    raw_bytes = raw.encode("utf-8")
    return WorkflowDocument(
        prefix=payload[:start],
        batches=value,
        suffix=payload[start + len(raw_bytes):],
    )


def _validate_batch(batch: Mapping[str, Any], label: str) -> None:
    if any(field not in batch for field in _BASE_FIELDS):
        raise ValueError(f"{label}: campos-base ausentes")
    forbidden = sorted(
        (set(batch) & _FULL_FORBIDDEN_FIELDS) |
        (set(batch) & _PUBLIC_FORBIDDEN_FIELDS)
    )
    if forbidden:
        raise ValueError(
            f"{label}: campos operacionais/públicos proibidos: {forbidden}"
        )
    families = batch["families"]
    if (not isinstance(batch["slug"], str) or
            _SLUG.fullmatch(batch["slug"]) is None or
            not isinstance(batch["area"], str) or
            _AREA.fullmatch(batch["area"]) is None or
            not isinstance(batch["file"], str) or
            _PORTFOLIO.fullmatch(batch["file"]) is None or
            batch["file"] !=
            f"data/editorial/portfolio_v2/{batch['area']}.jsonl" or
            not batch["slug"].startswith(batch["area"] + "-") or
            not isinstance(families, list) or not families or
            len(families) != len(set(families)) or
            any(not isinstance(family, str) or
                _FAMILY.fullmatch(family) is None for family in families) or
            type(batch["skip"]) is not int or batch["skip"] < 0 or
            type(batch["take"]) is not int or batch["take"] < 0 or
            type(batch["n"]) is not int or not 1 <= batch["n"] <= 22 or
            (batch["take"] > 0 and (
                len(families) != 1 or batch["take"] != batch["n"] or
                "intent_ids" in batch)) or
            (batch["take"] == 0 and batch["skip"] != 0)):
        raise ValueError(f"{label}: seletor não canônico")


def load_portfolio(
    rel_path: str,
    snapshot: queue.RegularFileSnapshot,
) -> PortfolioSnapshot:
    if (not snapshot.payload or not snapshot.payload.endswith(b"\n") or
            len(snapshot.payload) > MAX_PORTFOLIO_BYTES):
        raise ValueError(f"{rel_path}: portfólio vazio ou não terminado")
    records: list[Mapping[str, Any]] = []
    by_family: dict[str, list[str]] = defaultdict(list)
    family_by_intent: dict[str, str] = {}
    for line_number, raw in enumerate(snapshot.payload.splitlines(), 1):
        record = queue.decode_json_no_duplicate_keys(
            raw, f"{rel_path}:{line_number}"
        )
        if not isinstance(record, dict):
            raise ValueError(f"{rel_path}:{line_number}: registro não é objeto")
        intent_id = record.get("intent_id")
        family = record.get("family")
        if (not isinstance(intent_id, str) or
                _INTENT.fullmatch(intent_id) is None or
                not isinstance(family, str) or
                _FAMILY.fullmatch(family) is None or
                intent_id in family_by_intent):
            raise ValueError(
                f"{rel_path}:{line_number}: identidade duplicada/não canônica"
            )
        records.append(record)
        family_by_intent[intent_id] = family
        by_family[family].append(intent_id)
    return PortfolioSnapshot(
        rel_path=rel_path,
        payload=snapshot.payload,
        digest=snapshot.digest,
        records=tuple(records),
        by_family={key: tuple(value) for key, value in by_family.items()},
        family_by_intent=family_by_intent,
    )


def _select_ids(
    batch: Mapping[str, Any],
    portfolio: PortfolioSnapshot,
) -> tuple[str, ...]:
    _validate_batch(batch, f"lote {batch.get('slug', '?')}")
    if batch["take"] > 0:
        family_ids = portfolio.by_family.get(batch["families"][0], ())
        end = batch["skip"] + batch["take"]
        if end > len(family_ids):
            raise ValueError(f"{batch['slug']}: slice excede a família")
        selected = tuple(family_ids[batch["skip"]:end])
    else:
        pins = batch.get("intent_ids")
        if (not isinstance(pins, list) or len(pins) != batch["n"] or
                len(pins) != len(set(pins)) or
                any(not isinstance(value, str) or
                    _INTENT.fullmatch(value) is None for value in pins)):
            raise ValueError(f"{batch['slug']}: pin inválido")
        allowed = set(batch["families"])
        selected = tuple(pins)
        for intent_id in selected:
            family = portfolio.family_by_intent.get(intent_id)
            if family not in allowed:
                raise ValueError(
                    f"{batch['slug']}: pin ausente ou de outra família: "
                    f"{intent_id}"
                )
        semantic = tuple(
            intent_id
            for family in batch["families"]
            for intent_id in portfolio.by_family.get(family, ())
            if intent_id in set(selected)
        )
        if semantic != selected:
            raise ValueError(
                f"{batch['slug']}: ordem do pin diverge das famílias"
            )
        if any(not any(
                portfolio.family_by_intent[intent_id] == family
                for intent_id in selected
        ) for family in batch["families"]):
            raise ValueError(f"{batch['slug']}: família declarada ficou ociosa")
    if len(selected) != batch["n"]:
        raise ValueError(
            f"{batch['slug']}: selecionou {len(selected)}; n={batch['n']}"
        )
    return selected


def _next_slug_numbers(batches: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = defaultdict(lambda: 1)
    for batch in batches:
        prefix = batch["area"] + "-"
        suffix = batch["slug"][len(prefix):]
        if re.fullmatch(r"d[0-9]+", suffix):
            continue
        if not suffix.isdigit():
            raise ValueError(f"slug sem sufixo numérico: {batch['slug']}")
        number = int(suffix)
        if number < 1 or number >= 999_999:
            raise ValueError(f"sufixo de slug fora do limite: {batch['slug']}")
        result[batch["area"]] = max(result[batch["area"]], number + 1)
    return result


def pin_and_expand_inventory(
    batches: Sequence[Mapping[str, Any]],
    portfolios: Mapping[str, PortfolioSnapshot],
    *,
    overflow_pins: Mapping[str, Sequence[str]] = OVERFLOW_PINS,
    aggregate_intents: Mapping[str, Sequence[str]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Retorna inventário fechado sem alterar objetos de entrada."""
    if len(batches) != len({batch.get("slug") for batch in batches}):
        raise ValueError("inventário repete slug")
    aggregates = dict(aggregate_intents or {})
    if set(aggregates) != set(AGGREGATE_SHARDS):
        raise ValueError(
            "conjunto de shards agregados divergiu: "
            f"{sorted(aggregates)}"
        )
    incoming_slugs = {batch.get("slug") for batch in batches}
    missing_retired = sorted(RETIRED_BATCHES - incoming_slugs)
    missing_adjusted = sorted(set(SLICE_ADJUSTMENTS) - incoming_slugs)
    missing_exclusions = sorted(set(TAKE_ZERO_EXCLUSIONS) - incoming_slugs)
    if missing_retired or missing_adjusted or missing_exclusions:
        raise ValueError(
            "plano agregado não coincide com a preimagem: "
            f"retired={missing_retired} adjusted={missing_adjusted} "
            f"exclusions={missing_exclusions}"
        )
    result: list[dict[str, Any]] = []
    owners: dict[str, str] = {}
    take_zero = 0
    used_overflows: set[str] = set()
    for index, original in enumerate(batches, 1):
        batch = dict(original)
        _validate_batch(batch, f"lote {index}")
        if batch["slug"] in RETIRED_BATCHES:
            metadata_keys = sorted(
                set(batch) - set(_BASE_FIELDS) - {"intent_ids"}
            )
            if metadata_keys:
                raise ValueError(
                    f"{batch['slug']}: lote aposentado possui metadata sem "
                    f"destino explícito: {metadata_keys}"
                )
            continue
        adjustment = SLICE_ADJUSTMENTS.get(batch["slug"])
        if adjustment is not None:
            if batch["take"] <= 0 or len(batch["families"]) != 1:
                raise ValueError(
                    f"{batch['slug']}: ajuste esperado não é slice simples"
                )
            batch["skip"], batch["take"] = adjustment
            batch["n"] = batch["take"]
        portfolio = portfolios.get(batch["file"])
        if portfolio is None:
            raise ValueError(f"{batch['slug']}: portfólio ausente")
        if batch["take"] == 0:
            take_zero += 1
            excluded = TAKE_ZERO_EXCLUSIONS.get(
                batch["slug"], frozenset()
            )
            dynamic = tuple(
                intent_id
                for family in batch["families"]
                for intent_id in portfolio.by_family.get(family, ())
                if intent_id not in excluded
            )
            if excluded and (
                    not excluded.issubset(portfolio.family_by_intent) or
                    any(portfolio.family_by_intent[intent_id] not in
                        set(batch["families"]) for intent_id in excluded)):
                raise ValueError(
                    f"{batch['slug']}: exclusão agregada não pertence ao lote"
                )
            if len(dynamic) <= 22:
                pins = dynamic
            else:
                reviewed = overflow_pins.get(batch["slug"])
                if reviewed is None:
                    raise ValueError(
                        f"{batch['slug']}: seleção dinâmica excedeu 22 sem pin"
                    )
                pins = tuple(reviewed)
                used_overflows.add(batch["slug"])
            if not pins:
                raise ValueError(f"{batch['slug']}: lote pinado ficou vazio")
            batch["n"] = len(pins)
            batch["intent_ids"] = list(pins)
        else:
            if "intent_ids" in batch:
                raise ValueError(
                    f"{batch['slug']}: slice posicional carregou intent_ids"
                )
        selected = _select_ids(batch, portfolio)
        for intent_id in selected:
            prior = owners.get(intent_id)
            if prior is not None:
                raise ValueError(
                    f"{intent_id}: donos duplicados {prior} e {batch['slug']}"
                )
            owners[intent_id] = batch["slug"]
        result.append(batch)
    unused = sorted(set(overflow_pins) - used_overflows)
    if unused:
        raise ValueError(f"pins de overflow não consumidos: {unused}")

    # Os oito shards consolidados tornam-se owners explícitos antes da criação
    # das caudas Wave3. Sua ordem física já foi revisada como ordem semântica.
    for slug in AGGREGATE_SHARDS:
        area = slug.split("-d", 1)[0]
        rel_path = f"data/editorial/portfolio_v2/{area}.jsonl"
        portfolio = portfolios.get(rel_path)
        if portfolio is None:
            raise ValueError(f"{slug}: portfólio agregado ausente")
        intent_ids = list(aggregates[slug])
        if (not intent_ids or len(intent_ids) > 22 or
                len(intent_ids) != len(set(intent_ids))):
            raise ValueError(f"{slug}: IDs agregados inválidos")
        families: list[str] = []
        for intent_id in intent_ids:
            family = portfolio.family_by_intent.get(intent_id)
            if family is None:
                raise ValueError(
                    f"{slug}: intent agregado ausente do portfólio: {intent_id}"
                )
            if family not in families:
                families.append(family)
        aggregate_batch = {
            "families": families,
            "skip": 0,
            "take": 0,
            "n": len(intent_ids),
            "area": area,
            "file": rel_path,
            "slug": slug,
            "intent_ids": intent_ids,
        }
        if _select_ids(aggregate_batch, portfolio) != tuple(intent_ids):
            raise ValueError(f"{slug}: shard não está em ordem semântica")
        for intent_id in intent_ids:
            prior = owners.get(intent_id)
            if prior is not None:
                raise ValueError(
                    f"{slug}: intent agregado ainda pertence a {prior}: "
                    f"{intent_id}"
                )
            owners[intent_id] = slug
        result.append(aggregate_batch)
        take_zero += 1

    all_intents: dict[str, str] = {}
    for rel_path, portfolio in portfolios.items():
        for intent_id in portfolio.family_by_intent:
            prior = all_intents.get(intent_id)
            if prior is not None:
                raise ValueError(
                    f"intent_id repetido nos portfólios {prior} e {rel_path}: "
                    f"{intent_id}"
                )
            all_intents[intent_id] = rel_path
    orphan_ids = set(all_intents) - set(owners)
    # Slug aposentado continua reservado: reusá-lo apontaria um target físico
    # histórico para outro seletor. O teto parte da preimagem integral, não do
    # inventário já filtrado.
    next_number = _next_slug_numbers(batches)
    occupied_slugs = {
        batch["slug"] for batch in batches
    } | {batch["slug"] for batch in result}
    new_batches = 0
    new_intents = 0
    for rel_path in sorted(portfolios):
        portfolio = portfolios[rel_path]
        area = pathlib.PurePosixPath(rel_path).stem
        families_in_order: list[str] = []
        seen_families: set[str] = set()
        for record in portfolio.records:
            family = record["family"]
            if family not in seen_families:
                seen_families.add(family)
                families_in_order.append(family)
        for family in families_in_order:
            family_ids = portfolio.by_family[family]
            positions = [
                offset for offset, intent_id in enumerate(family_ids)
                if intent_id in orphan_ids
            ]
            if not positions:
                continue
            expected_positions = list(range(positions[0], len(family_ids)))
            if positions != expected_positions:
                raise ValueError(
                    f"{rel_path}:{family}: órfãos não formam cauda contígua"
                )
            orphan_family_ids = [family_ids[offset] for offset in positions]
            for offset in range(0, len(orphan_family_ids), 22):
                chunk = orphan_family_ids[offset:offset + 22]
                number = next_number[area]
                if number >= 999_999:
                    raise ValueError(f"{area}: espaço de slugs esgotado")
                slug = f"{area}-{number:02d}"
                next_number[area] += 1
                if slug in occupied_slugs:
                    raise ValueError(f"alocador repetiu slug {slug}")
                batch = {
                    "families": [family],
                    "skip": positions[0] + offset,
                    "take": len(chunk),
                    "n": len(chunk),
                    "area": area,
                    "file": rel_path,
                    "slug": slug,
                }
                if _select_ids(batch, portfolio) != tuple(chunk):
                    raise ValueError(f"{slug}: slice novo não cobre sua cauda")
                for intent_id in chunk:
                    if intent_id in owners:
                        raise ValueError(f"{slug}: órfão já recebeu dono")
                    owners[intent_id] = slug
                occupied_slugs.add(slug)
                result.append(batch)
                new_batches += 1
                new_intents += len(chunk)

    missing = sorted(set(all_intents) - set(owners))
    extras = sorted(set(owners) - set(all_intents))
    if missing or extras or len(owners) != len(all_intents):
        raise ValueError(
            "inventário não fecha o portfólio: "
            f"missing={missing[:8]} extras={extras[:8]}"
        )
    counts = {
        "batches_before": len(batches),
        "batches_after": len(result),
        "portfolio_intents": len(all_intents),
        "take_zero_batches": take_zero,
        "aggregate_batches": len(AGGREGATE_SHARDS),
        "retired_batches": len(RETIRED_BATCHES),
        "adjusted_batches": len(SLICE_ADJUSTMENTS),
        "new_batches": new_batches,
        "new_intents": new_intents,
    }
    return result, counts


def _decode_area_sources(payload: bytes) -> Mapping[str, list[dict[str, str]]]:
    value = queue.decode_json_no_duplicate_keys(payload, AREA_SOURCES_REL)
    if not isinstance(value, dict) or not isinstance(value.get("_meta"), dict):
        raise ValueError("mapa de fontes por área perdeu schema raiz")
    result: dict[str, list[dict[str, str]]] = {}
    for area, sources in value.items():
        if area == "_meta":
            continue
        if (not isinstance(area, str) or _AREA.fullmatch(area) is None or
                not isinstance(sources, list)):
            raise ValueError(f"fontes candidatas inválidas para {area}")
        result[area] = [
            queue._canonical_candidate_source(
                source, f"{AREA_SOURCES_REL}:{area}"
            )
            for source in sources
        ]
    return result


def _decode_source_catalog(payload: bytes) -> Mapping[str, Any]:
    value = queue.decode_json_no_duplicate_keys(payload, SOURCE_CATALOG_REL)
    if (not isinstance(value, dict) or
            set(value) != {"_meta", "strict_intents", "source_hints"} or
            not isinstance(value["source_hints"], dict)):
        raise ValueError("catálogo de source hints perdeu schema")
    queue._validate_source_catalog_meta(value["_meta"])
    return value


def _candidate_sources(
    batch: Mapping[str, Any],
    area_sources: Mapping[str, list[dict[str, str]]],
    source_catalog: Mapping[str, Any],
) -> list[dict[str, str]]:
    if batch["families"] != ["dpvat-spvat"]:
        return [dict(source) for source in area_sources.get(batch["area"], ())[:8]]
    hints = source_catalog["source_hints"]
    result: list[dict[str, str]] = []
    for hint in _DPVAT_SOURCE_HINTS:
        source = hints.get(hint)
        canonical = queue._canonical_exact_source(
            source, f"source_hints.{hint}"
        )
        result.append({"name": canonical["name"], "url": canonical["url"]})
    return result


def _decode_target(
    rel_path: str,
    snapshot: queue.RegularFileSnapshot,
) -> tuple[list[Mapping[str, Any]], Mapping[str, list[str]]]:
    if not snapshot.payload:
        return [], {}
    if not snapshot.payload.endswith(b"\n"):
        raise ValueError(f"{rel_path}: shard não termina com newline")
    records: list[Mapping[str, Any]] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    for line_number, raw in enumerate(snapshot.payload[:-1].split(b"\n"), 1):
        if not raw:
            raise ValueError(f"{rel_path}:{line_number}: linha vazia")
        record = queue.decode_json_no_duplicate_keys(
            raw, f"{rel_path}:{line_number}"
        )
        if not isinstance(record, dict):
            raise ValueError(f"{rel_path}:{line_number}: registro não é objeto")
        records.append(record)
        intent_id = record.get("intent_id")
        if isinstance(intent_id, str):
            hashes[intent_id].append(_digest(raw))
    return records, hashes


def build_queue_items(
    root: pathlib.Path,
    batches: Sequence[Mapping[str, Any]],
    portfolios: Mapping[str, PortfolioSnapshot],
    source_catalog: queue.RegularFileSnapshot,
    area_sources_snapshot: queue.RegularFileSnapshot,
    target_snapshots: Mapping[str, queue.RegularFileSnapshot],
    supersession_winners: Iterable[tuple[str, str]],
    migration_catalog: portfolio_migrations.MigrationCatalog,
    semantic_contract: queue.WritingSemanticContract,
    existing_todo: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    area_sources = _decode_area_sources(area_sources_snapshot.payload)
    source_catalog_value = _decode_source_catalog(source_catalog.payload)
    if any(not isinstance(item, Mapping) for item in existing_todo):
        raise ValueError("fila anterior contém lote que não é objeto")
    existing_by_slug: dict[str, Mapping[str, Any]] = {}
    for item in existing_todo:
        slug = item.get("slug")
        if (not isinstance(slug, str) or
                _SLUG.fullmatch(slug) is None):
            raise ValueError(f"fila anterior contém slug inválido: {slug!r}")
        if slug in existing_by_slug:
            raise ValueError("fila anterior repete slug")
        existing_by_slug[slug] = item
    batch_slugs = {batch["slug"] for batch in batches}
    unknown_previous = sorted(
        slug for slug in existing_by_slug
        if slug not in batch_slugs and slug not in RETIRED_BATCHES
    )
    if unknown_previous:
        raise ValueError(
            f"fila anterior contém slugs sem destino: {unknown_previous[:8]}"
        )
    for slug, previous in existing_by_slug.items():
        forbidden = sorted(set(previous) & _PUBLIC_FORBIDDEN_FIELDS)
        if forbidden:
            raise ValueError(
                f"{slug}: fila interna carregou campos públicos: {forbidden}"
            )
        if slug in RETIRED_BATCHES:
            metadata_keys = sorted(
                set(previous) - _QUEUE_OWNED_FIELDS
            )
            if metadata_keys:
                raise ValueError(
                    f"{slug}: metadata de fila aposentada exige migração "
                    f"explícita: {metadata_keys}"
                )
    todo: list[dict[str, Any]] = []
    for batch in batches:
        portfolio = portfolios[batch["file"]]
        pins = batch.get("intent_ids") if batch["take"] == 0 else None
        resolution = queue.derive_writing_source_resolution(
            root,
            batch["file"],
            portfolio.digest,
            SOURCE_CATALOG_REL,
            source_catalog.digest,
            batch["families"],
            batch["skip"],
            batch["take"],
            batch["n"],
            pins,
        )
        expected_order = tuple(resolution.selected_intents)
        if expected_order != _select_ids(batch, portfolio):
            raise ValueError(f"{batch['slug']}: helper de fontes mudou o seletor")
        target_rel = f"data/editorial/v2_pages/{batch['slug']}.jsonl"
        target = target_snapshots.get(
            target_rel, queue.RegularFileSnapshot(b"", EMPTY_SHA256)
        )
        records, raw_hashes = _decode_target(target_rel, target)
        raw_lines = (
            target.payload[:-1].split(b"\n") if target.payload else []
        )
        relocation_removals = (
            queue.semantic_relocation_removals_for_target(
                target_rel,
                tuple(zip(raw_lines, records)),
                semantic_contract,
            )
        )
        relocation_ids = {
            removal["intent_id"] for removal in relocation_removals
        }
        if relocation_ids & set(expected_order):
            raise ValueError(
                f"{target_rel}: remoção semântica ainda pertence ao slice pinado"
            )
        classification_records = [
            record for record in records
            if record.get("intent_id") not in relocation_ids
        ]
        semantic_blocked = queue.semantic_blocked_for_batch(
            expected_order, semantic_contract
        )
        migration_authorization = None
        try:
            completion = queue.classify_batch_completion(
                classification_records,
                expected_order,
                pathlib.PurePosixPath(target_rel).name,
                supersession_winners,
                semantically_blocked_intents=semantic_blocked,
            )
        except ValueError as ordinary_error:
            try:
                migration_authorization = (
                    portfolio_migrations.queue_authorization(
                        migration_catalog,
                        pathlib.PurePosixPath(target_rel).name,
                        target.payload,
                        target.digest,
                        batch["file"],
                        portfolio.payload,
                        portfolio.digest,
                        expected_order,
                        batch["families"],
                        batch["skip"],
                        batch["take"],
                        batch["n"],
                        pins,
                    )
                )
            except (OSError, RuntimeError, ValueError) as migration_error:
                raise ValueError(
                    f"{target_rel}: {ordinary_error}; migração recusada: "
                    f"{migration_error}"
                ) from migration_error
            if migration_authorization is None:
                raise ValueError(f"{target_rel}: {ordinary_error}") from ordinary_error
            if relocation_removals:
                raise ValueError(
                    f"{target_rel}: relocação semântica não pode coexistir com "
                    "migração integral"
                )
            completion = queue.classify_batch_completion(
                classification_records,
                expected_order,
                pathlib.PurePosixPath(target_rel).name,
                supersession_winners,
                migration_authorization["source_intent_ids"],
                semantically_blocked_intents=semantic_blocked,
            )
        if completion.complete and not relocation_removals:
            continue

        item = dict(batch)
        previous = existing_by_slug.get(batch["slug"])
        if previous is not None:
            for key, value in previous.items():
                if key not in _QUEUE_OWNED_FIELDS:
                    item[key] = value
        item["writer"] = "redator-juridico"
        if batch["area"] in _HIGH_ACCURACY_AREAS:
            item["model"] = "opus"
        item["sources"] = _candidate_sources(
            batch, area_sources, source_catalog_value
        )
        item["source_overrides"] = dict(resolution.source_overrides)
        item["strict_source_intents"] = list(
            resolution.strict_source_intents
        )
        item["source_hint_catalog_sha256"] = source_catalog.digest
        item["portfolio_sha256"] = portfolio.digest
        item["semantic_contract_sha256"] = semantic_contract.digest
        if completion.reusable_expected:
            item["reuse"] = list(completion.reusable_expected)
        if completion.authenticated_extras:
            item["preserve_extras"] = list(
                completion.authenticated_extras
            )
        if relocation_removals:
            item["semantic_relocation_removals"] = list(
                relocation_removals
            )
        if migration_authorization is not None:
            item["portfolio_intent_migration"] = migration_authorization
        preserved: dict[str, str] = {}
        for intent_id in (
            *completion.reusable_expected,
            *completion.authenticated_extras,
        ):
            values = raw_hashes.get(intent_id, ())
            if len(values) != 1:
                raise ValueError(
                    f"{target_rel}: registro preservado ambíguo {intent_id}"
                )
            preserved[intent_id] = values[0]
        item["preserved_record_sha256"] = preserved
        item["target_sha256"] = target.digest
        forbidden = sorted(set(item) & _PUBLIC_FORBIDDEN_FIELDS)
        if forbidden:
            raise ValueError(
                f"{batch['slug']}: saída da fila abriu campos públicos: "
                f"{forbidden}"
            )
        todo.append(item)
    return todo


def _embed_queue(template: bytes, items: Sequence[Mapping[str, Any]], name: str) -> bytes:
    try:
        text = template.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("template writing-mass não é UTF-8") from error
    inject = (
        "const parsedArgs = typeof args === 'string' ? JSON.parse(args) : args\n"
        "if (!Array.isArray(parsedArgs)) throw new Error('args deve ser o array de lotes')\n"
        "const batches = parsedArgs"
    )
    if text.count(inject) != 1 or text.count("name: 'writing-mass'") != 1:
        raise ValueError("âncora do template writing-mass mudou")
    embed = "const batches = " + json.dumps(
        list(items), ensure_ascii=False, separators=(", ", ": ")
    )
    result = text.replace(inject, embed).replace(
        "name: 'writing-mass'", f"name: '{name}'"
    )
    return result.encode("utf-8")


def _validate_existing_without_telecom_projection(
    todo: Sequence[Mapping[str, Any]],
    without_telecom: Sequence[Mapping[str, Any]],
) -> None:
    expected = [
        dict(item) for item in todo
        if item.get("area") != "telecom_energia"
    ]
    actual = [dict(item) for item in without_telecom]
    if actual != expected:
        raise ValueError(
            "fila sem telecom diverge da projeção exata da fila canônica; "
            "recusar evita perder metadata/reuse/extras"
        )


def _portfolio_set_digest(portfolios: Mapping[str, PortfolioSnapshot]) -> str:
    payload = json.dumps(
        {path: portfolios[path].digest for path in sorted(portfolios)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return _digest(payload)


def _snapshot_set_digest(values: Mapping[str, str]) -> str:
    return _digest(json.dumps(
        dict(sorted(values.items())), sort_keys=True, separators=(",", ":")
    ).encode("ascii"))


def _merge_dependency_sha256(
    *groups: Mapping[str, str],
) -> dict[str, str]:
    """Une epochs sem permitir que expansão de ``dict`` oculte colisões."""
    merged: dict[str, str] = {}
    for group in groups:
        for rel_path, digest in group.items():
            if (not isinstance(rel_path, str) or not rel_path or
                    not isinstance(digest, str) or
                    re.fullmatch(r"[0-9a-f]{64}", digest) is None):
                raise ValueError(
                    f"dependência SHA-256 inválida: {rel_path!r}"
                )
            previous = merged.get(rel_path)
            if previous is not None and previous != digest:
                raise queue.CASMismatch(
                    "epochs atribuem hashes diferentes ao mesmo path: "
                    f"{rel_path}"
                )
            merged[rel_path] = digest
    return merged


def _portfolio_paths(root: pathlib.Path) -> tuple[str, ...]:
    """Descobre o conjunto canônico sem seguir ancestrais simbólicos.

    Derivar os paths apenas dos lotes existentes deixaria um JSONL novo e
    ainda sem owner invisível para a migração. A listagem por descritor fecha
    essa lacuna e o sandwich do chamador detecta criação/remoção concorrente.
    Tombstones transacionais não são portfólios e permanecem fora do conjunto.
    """
    directory = root / "data/editorial/portfolio_v2"
    directory_fd, _, _ = queue._open_parent_directory(
        directory / ".portfolio-membership"
    )
    try:
        names = os.listdir(directory_fd)
    finally:
        os.close(directory_fd)
    paths: list[str] = []
    for name in names:
        if not name.endswith(".jsonl"):
            continue
        rel_path = f"data/editorial/portfolio_v2/{name}"
        if _PORTFOLIO.fullmatch(rel_path) is None:
            raise ValueError(
                f"diretório de portfólios contém JSONL não canônico: {name}"
            )
        paths.append(rel_path)
    if len(paths) != len(set(paths)):
        raise ValueError("diretório de portfólios repete identidade")
    return tuple(sorted(paths))


def _read_required_inputs(
    root: pathlib.Path,
    preimages: PreimageBundle,
) -> dict[str, queue.RegularFileSnapshot]:
    result: dict[str, queue.RegularFileSnapshot] = {}
    for rel_path in EXPECTED_INPUT_SHA256:
        if rel_path in _OUTPUT_PATHS:
            archive_path = PREIMAGE_ARCHIVE_BY_OUTPUT[rel_path]
            snapshot = preimages.archives[archive_path]
            active = _read_canonical_0644_artifact(
                root, rel_path, max_bytes=MAX_WORKFLOW_BYTES
            )
            if (active.digest != snapshot.digest or
                    active.payload != snapshot.payload):
                raise queue.CASMismatch(
                    "workflow ativo não coincide byte a byte com seu "
                    f"archive inerte: {rel_path}"
                )
        else:
            snapshot = queue.read_regular_file_snapshot(
                root / rel_path, max_bytes=MAX_WORKFLOW_BYTES
            )
        expected = EXPECTED_INPUT_SHA256[rel_path]
        if snapshot.digest != expected:
            raise queue.CASMismatch(
                f"preimagem one-shot mudou: {rel_path}: "
                f"expected={expected} actual={snapshot.digest}"
            )
        result[rel_path] = snapshot
    return result


def _snapshot_portfolios(
    root: pathlib.Path,
    batches: Sequence[Mapping[str, Any]],
) -> dict[str, PortfolioSnapshot]:
    selected_paths = tuple(sorted({batch["file"] for batch in batches}))
    before_paths = _portfolio_paths(root)
    if before_paths != selected_paths:
        missing = sorted(set(before_paths) - set(selected_paths))
        stale = sorted(set(selected_paths) - set(before_paths))
        raise queue.CASMismatch(
            "inventário full não cobre o conjunto vivo de portfólios: "
            f"sem_owner={missing[:8]} ausentes={stale[:8]}"
        )
    result: dict[str, PortfolioSnapshot] = {}
    for rel_path in selected_paths:
        snapshot = queue.read_regular_file_snapshot(
            root / rel_path, max_bytes=MAX_PORTFOLIO_BYTES
        )
        result[rel_path] = load_portfolio(rel_path, snapshot)
    if _portfolio_paths(root) != before_paths:
        raise queue.CASMismatch(
            "conjunto de portfólios mudou durante o snapshot"
        )
    fingerprint = _portfolio_set_digest(result)
    if fingerprint != EXPECTED_PORTFOLIO_SET_SHA256:
        raise queue.CASMismatch(
            "conjunto de portfólios divergiu da revisão one-shot: "
            f"expected={EXPECTED_PORTFOLIO_SET_SHA256} actual={fingerprint}"
        )
    return result


def _snapshot_aggregate_intents(
    root: pathlib.Path,
    portfolios: Mapping[str, PortfolioSnapshot],
) -> tuple[
    dict[str, tuple[str, ...]],
    dict[str, queue.RegularFileSnapshot],
]:
    expected_counts = {
        "consumidor-d01": 13,
        "glossario2-d01": 13,
        "glossario2-d02": 13,
        "glossario2-d03": 13,
        "glossario2-d04": 13,
        "glossario2-d05": 8,
        "seguros-d01": 13,
        "tributario-d02": 13,
    }
    snapshots: dict[str, queue.RegularFileSnapshot] = {}
    result: dict[str, tuple[str, ...]] = {}
    for slug in AGGREGATE_SHARDS:
        rel_path = f"data/editorial/v2_pages/{slug}.jsonl"
        snapshot = queue.read_regular_file_snapshot(
            root / rel_path, max_bytes=MAX_STOCK_BYTES
        )
        records, _ = _decode_target(rel_path, snapshot)
        intent_ids = tuple(record.get("intent_id") for record in records)
        area = slug.split("-d", 1)[0]
        portfolio = portfolios[
            f"data/editorial/portfolio_v2/{area}.jsonl"
        ]
        if (len(intent_ids) != expected_counts[slug] or
                len(intent_ids) != len(set(intent_ids)) or
                any(not isinstance(intent_id, str) or
                    _INTENT.fullmatch(intent_id) is None or
                    intent_id not in portfolio.family_by_intent
                    for intent_id in intent_ids)):
            raise ValueError(f"{rel_path}: aggregate não é canônico")
        result[slug] = intent_ids
        snapshots[rel_path] = snapshot
    fingerprint = _snapshot_set_digest({
        path: snapshot.digest for path, snapshot in snapshots.items()
    })
    if fingerprint != EXPECTED_AGGREGATE_SET_SHA256:
        raise queue.CASMismatch(
            "shards agregados divergiram da revisão one-shot: "
            f"expected={EXPECTED_AGGREGATE_SET_SHA256} actual={fingerprint}"
        )
    return result, snapshots


def _stock_paths(root: pathlib.Path) -> list[pathlib.Path]:
    from tools import audit_v2_pages as auditor

    return sorted(
        path for path in (root / "data/editorial/v2_pages").glob("*.jsonl")
        if auditor.is_finalized_v2_path(path.as_posix())
    )


def _trusted_supersession_dependency_sha256() -> dict[str, str]:
    from tools import audit_v2_pages as auditor

    return dict(auditor.TRUSTED_SUPERSESSION_ARCHIVE_SHA256)


def _snapshot_stock(
    root: pathlib.Path,
) -> tuple[
    dict[str, queue.RegularFileSnapshot],
    set[tuple[str, str]],
    dict[str, queue.RegularFileSnapshot],
]:
    # Import tardio: o auditor é leitor do estoque, nunca produtor desta
    # migração. Capturar antes/depois liga os vencedores DEC-020 ao mesmo epoch.
    from tools import audit_v2_pages as auditor

    before_paths = _stock_paths(root)
    before = {
        path.relative_to(root).as_posix(): queue.read_regular_file_snapshot(
            path, max_bytes=MAX_STOCK_BYTES
        )
        for path in before_paths
    }
    trusted_supersession_sha256 = (
        _trusted_supersession_dependency_sha256()
    )
    supersession_evidence = {
        rel_path: queue.read_regular_file_snapshot(
            root / rel_path,
            max_bytes=portfolio_migrations.MAX_ARCHIVE_BYTES,
        )
        for rel_path in sorted(trusted_supersession_sha256)
    }
    for rel_path, snapshot in supersession_evidence.items():
        expected = trusted_supersession_sha256[rel_path]
        if snapshot.digest != expected:
            raise queue.CASMismatch(
                f"archive DEC-020 divergiu do pin: {rel_path}"
            )
    winners, issues = auditor.validated_duplicate_supersession_winners(
        root=root
    )
    if issues:
        raise ValueError(
            "projeção DEC-020 inválida: " + ", ".join(issues[:8])
        )
    after_paths = _stock_paths(root)
    after = {
        path.relative_to(root).as_posix(): queue.snapshot_sha256(
            path, max_bytes=MAX_STOCK_BYTES
        )
        for path in after_paths
    }
    queue.authenticate_snapshot_set(
        {path: snapshot.digest for path, snapshot in before.items()},
        after,
        before,
    )
    for rel_path, snapshot in supersession_evidence.items():
        if queue.snapshot_sha256(
                root / rel_path,
                max_bytes=portfolio_migrations.MAX_ARCHIVE_BYTES,
        ) != snapshot.digest:
            raise queue.CASMismatch(
                f"archive DEC-020 mudou durante snapshot: {rel_path}"
            )
    return before, set(winners), supersession_evidence


def _validate_semantic_contract_epoch(
    root: pathlib.Path,
    batches: Sequence[Mapping[str, Any]],
    portfolios: Mapping[str, PortfolioSnapshot],
    stock: Mapping[str, queue.RegularFileSnapshot],
    semantic_contract: queue.WritingSemanticContract,
) -> None:
    """Liga cada requisito ao owner e aos snapshots já capturados do plano."""
    if (not isinstance(semantic_contract, queue.WritingSemanticContract) or
            re.fullmatch(r"[0-9a-f]{64}", semantic_contract.digest) is None):
        raise TypeError("contrato semântico inválido no plano one-shot")
    requirement_ids = set(semantic_contract.requirement_fingerprints)
    keyed_maps = {
        "portfolio_rel_paths": semantic_contract.portfolio_rel_paths,
        "target_rel_paths": semantic_contract.target_rel_paths,
        "superseded_target_rel_paths":
            semantic_contract.superseded_target_rel_paths,
        "superseded_page_record_sha256":
            semantic_contract.superseded_page_record_sha256,
        "evidence_kinds": semantic_contract.evidence_kinds,
        "evidence_rel_paths": semantic_contract.evidence_rel_paths,
        "evidence_sha256": semantic_contract.evidence_sha256,
    }
    divergent_keysets = sorted(
        name for name, values in keyed_maps.items()
        if set(values) != requirement_ids
    )
    if (divergent_keysets or
            set(semantic_contract.superseded_target_rel_paths) !=
            requirement_ids or
            not set(semantic_contract.unresolved_intents).issubset(
                requirement_ids
            )):
        raise ValueError(
            "contrato semântico diverge entre requisitos, targets, evidências "
            f"e estado: {divergent_keysets}"
        )

    owners: dict[str, str] = {}
    owner_portfolios: dict[str, str] = {}
    for batch in batches:
        portfolio = portfolios.get(batch["file"])
        if portfolio is None:
            raise ValueError(
                f"{batch['slug']}: portfólio ausente no epoch semântico"
            )
        target_rel = f"data/editorial/v2_pages/{batch['slug']}.jsonl"
        for intent_id in _select_ids(batch, portfolio):
            previous = owners.get(intent_id)
            if previous is not None:
                raise ValueError(
                    f"intent com owners semânticos duplicados: {intent_id}: "
                    f"{previous} e {target_rel}"
                )
            owners[intent_id] = target_rel
            owner_portfolios[intent_id] = portfolio.rel_path

    missing = sorted(requirement_ids - set(owners))
    misbound = sorted(
        intent_id for intent_id in requirement_ids
        if intent_id in owners and
        semantic_contract.target_rel_paths[intent_id] != owners[intent_id]
    )
    portfolio_misbound = sorted(
        intent_id for intent_id in requirement_ids
        if intent_id in owner_portfolios and
        semantic_contract.portfolio_rel_paths[intent_id] !=
        owner_portfolios[intent_id]
    )
    if missing or misbound or portfolio_misbound:
        raise ValueError(
            "requisitos semânticos sem owner exato no inventário: "
            f"ausentes={missing[:8]} target_divergente={misbound[:8]} "
            f"portfolio_divergente={portfolio_misbound[:8]}"
        )

    referenced_portfolios = set(semantic_contract.portfolio_rel_paths.values())
    evidence_paths = set(semantic_contract.evidence_rel_paths.values())
    current_owner_paths = set(semantic_contract.target_rel_paths.values())
    present_owner_paths = current_owner_paths & set(stock)
    expected_absent = current_owner_paths - set(stock)
    expected_dependencies = (
        referenced_portfolios | evidence_paths | present_owner_paths
    )
    actual_dependencies = set(semantic_contract.dependency_sha256)
    unexpected = sorted(actual_dependencies - expected_dependencies)
    missing_dependencies = sorted(expected_dependencies - actual_dependencies)
    captured: dict[str, str] = {}
    for rel_path in referenced_portfolios:
        portfolio = portfolios.get(rel_path)
        if portfolio is None:
            raise ValueError(
                f"portfólio semântico não foi capturado: {rel_path}")
        captured[rel_path] = portfolio.digest
    for rel_path in present_owner_paths:
        captured[rel_path] = stock[rel_path].digest
    for rel_path in evidence_paths:
        if rel_path not in captured:
            captured[rel_path] = queue.snapshot_sha256(
                root / rel_path, max_bytes=64 * 1024 * 1024
            )
    stale = sorted(
        rel_path for rel_path, digest in
        semantic_contract.dependency_sha256.items()
        if captured.get(rel_path) != digest
    )
    actual_absent = set(semantic_contract.absent_dependency_paths)
    missing_absence = sorted(expected_absent - actual_absent)
    extra_absence = sorted(actual_absent - expected_absent)
    if (unexpected or missing_dependencies or stale or missing_absence or
            extra_absence):
        raise queue.CASMismatch(
            "dependências semânticas não pertencem ao epoch capturado: "
            f"inesperadas={unexpected[:8]} faltantes={missing_dependencies[:8]} "
            f"divergentes={stale[:8]} ausencia_faltante="
            f"{missing_absence[:8]} ausencia_extra={extra_absence[:8]}"
        )
    queue.verify_writing_semantic_contract_dependencies(
        root, semantic_contract
    )


def _validate_counts(counts: Mapping[str, int]) -> None:
    expected = {
        "batches_before": EXPECTED_BATCHES_BEFORE,
        "batches_after": EXPECTED_BATCHES_AFTER,
        "portfolio_intents": EXPECTED_PORTFOLIO_INTENTS,
        "take_zero_batches": EXPECTED_TAKE_ZERO_BATCHES,
        "aggregate_batches": EXPECTED_AGGREGATE_BATCHES,
        "retired_batches": EXPECTED_RETIRED_BATCHES,
        "adjusted_batches": EXPECTED_ADJUSTED_BATCHES,
        "new_batches": EXPECTED_NEW_BATCHES,
        "new_intents": EXPECTED_NEW_INTENTS,
        "complete_batches": EXPECTED_COMPLETE_BATCHES,
        "todo_batches": EXPECTED_TODO_BATCHES,
        "todo_without_telecom_batches": EXPECTED_TODO_WITHOUT_TELECOM_BATCHES,
        "semantic_requirements": EXPECTED_SEMANTIC_REQUIREMENTS,
        "unresolved_semantic_requirements": (
            EXPECTED_UNRESOLVED_SEMANTIC_REQUIREMENTS
        ),
    }
    if dict(counts) != expected:
        raise ValueError(f"contadores da migração divergiram: {counts!r}")


def build_plan(root: pathlib.Path = ROOT) -> MigrationPlan:
    preimage_bundle = _verify_preimage_manifest(root)
    inputs = _read_required_inputs(root, preimage_bundle)
    full_document = parse_workflow_document(inputs[FULL_REL].payload, FULL_REL)
    todo_document = parse_workflow_document(inputs[TODO_REL].payload, TODO_REL)
    todo_without_document = parse_workflow_document(
        inputs[TODO_WITHOUT_TELECOM_REL].payload,
        TODO_WITHOUT_TELECOM_REL,
    )
    _validate_existing_without_telecom_projection(
        todo_document.batches,
        todo_without_document.batches,
    )
    portfolios = _snapshot_portfolios(root, full_document.batches)
    aggregate_intents, aggregate_snapshots = _snapshot_aggregate_intents(
        root, portfolios
    )
    pinned, counts = pin_and_expand_inventory(
        full_document.batches,
        portfolios,
        aggregate_intents=aggregate_intents,
    )
    stock, winners, supersession_evidence = _snapshot_stock(root)
    semantic_contract = queue.load_writing_semantic_contract(root)
    _validate_semantic_contract_epoch(
        root, pinned, portfolios, stock, semantic_contract
    )
    source_catalog = inputs[SOURCE_CATALOG_REL]
    area_sources = inputs[AREA_SOURCES_REL]
    migration_catalog = portfolio_migrations.load_catalog(root)
    todo = build_queue_items(
        root,
        pinned,
        portfolios,
        source_catalog,
        area_sources,
        stock,
        winners,
        migration_catalog,
        semantic_contract,
        todo_document.batches,
    )
    todo_without_telecom = [
        item for item in todo if item["area"] != "telecom_energia"
    ]
    counts = {
        **counts,
        "complete_batches": len(pinned) - len(todo),
        "todo_batches": len(todo),
        "todo_without_telecom_batches": len(todo_without_telecom),
        "semantic_requirements": len(
            semantic_contract.requirement_fingerprints
        ),
        "unresolved_semantic_requirements": len(
            semantic_contract.unresolved_intents
        ),
    }
    _validate_counts(counts)
    outputs = {
        FULL_REL: full_document.encode(pinned),
        TODO_REL: _embed_queue(
            inputs[TEMPLATE_REL].payload, todo, "writing-mass-todo"
        ),
        TODO_WITHOUT_TELECOM_REL: _embed_queue(
            inputs[TEMPLATE_REL].payload,
            todo_without_telecom,
            "writing-mass-todo-sem-telecom",
        ),
    }
    dependency_sha256 = _merge_dependency_sha256(
        {path: snapshot.digest for path, snapshot in inputs.items()},
        {PREIMAGE_MANIFEST_REL: preimage_bundle.manifest.digest},
        {
            path: snapshot.digest
            for path, snapshot in preimage_bundle.archives.items()
        },
        {
            path: portfolio.digest
            for path, portfolio in portfolios.items()
        },
        {
            "portfolio_set": _portfolio_set_digest(portfolios),
            "aggregate_set": _snapshot_set_digest({
                path: snapshot.digest
                for path, snapshot in aggregate_snapshots.items()
            }),
        },
        {
            path: snapshot.digest
            for path, snapshot in aggregate_snapshots.items()
        },
        dict(migration_catalog.dependency_sha256),
        {
            path: snapshot.digest
            for path, snapshot in supersession_evidence.items()
        },
        {SEMANTIC_CONTRACT_REL: semantic_contract.digest},
        semantic_contract.dependency_sha256,
    )
    stock_sha256 = {path: snapshot.digest for path, snapshot in stock.items()}
    receipt = {
        "schema_version": "v2_writing_inventory_pin_migration_v3",
        "migration_id": "writing-inventory-pins-20260715",
        "checked_at": "2026-07-15",
        "input_sha256": dict(sorted(dependency_sha256.items())),
        "absent_input_paths": sorted(
            semantic_contract.absent_dependency_paths
        ),
        "stock_sha256": dict(sorted(stock_sha256.items())),
        "stock_set_sha256": _snapshot_set_digest(stock_sha256),
        "output_sha256": {
            path: _digest(payload) for path, payload in sorted(outputs.items())
        },
        "preimage_manifest_sha256": preimage_bundle.manifest.digest,
        "preimage_archive_sha256": {
            path: snapshot.digest
            for path, snapshot in sorted(preimage_bundle.archives.items())
        },
        "preimage_set_sha256": _preimage_set_digest(
            _preimage_entries(preimage_bundle.archives)
        ),
        "counts": counts,
        "overflow_pin_sha256": _digest(json.dumps(
            {slug: list(OVERFLOW_PINS[slug]) for slug in sorted(OVERFLOW_PINS)},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")),
        "publication_touches": [],
        "index_policy": "noindex",
        "render_allowed": False,
        "sitemap_allowed": False,
        "publication_allowed": False,
        "approval": False,
        "publicly_indexable": False,
    }
    receipt_payload = (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    return MigrationPlan(
        inputs=inputs,
        dependency_sha256=dependency_sha256,
        stock_sha256=stock_sha256,
        portfolio_paths=tuple(sorted(portfolios)),
        semantic_contract=semantic_contract,
        outputs=outputs,
        preimage_bundle=preimage_bundle,
        receipt_payload=receipt_payload,
        counts=counts,
    )


def _revalidate_plan(
    root: pathlib.Path,
    plan: MigrationPlan,
    *,
    outputs_installed: bool = False,
) -> None:
    if _portfolio_paths(root) != plan.portfolio_paths:
        raise queue.CASMismatch(
            "conjunto de portfólios mudou antes do CAS"
        )
    for rel_path, expected in plan.dependency_sha256.items():
        if rel_path in {"portfolio_set", "aggregate_set"}:
            continue
        if outputs_installed and rel_path in plan.outputs:
            expected = _digest(plan.outputs[rel_path])
        actual = queue.snapshot_sha256(
            root / rel_path,
            max_bytes=_dependency_max_bytes(rel_path),
        )
        if actual != expected:
            raise queue.CASMismatch(
                f"dependência mudou antes do CAS: {rel_path}"
            )
    before_paths = {
        path.relative_to(root).as_posix() for path in _stock_paths(root)
    }
    if before_paths != set(plan.stock_sha256):
        raise queue.CASMismatch("conjunto de shards mudou antes do CAS")
    current_stock = {
        path: queue.snapshot_sha256(root / path, max_bytes=MAX_STOCK_BYTES)
        for path in sorted(before_paths)
    }
    after_paths = {
        path.relative_to(root).as_posix() for path in _stock_paths(root)
    }
    queue.authenticate_snapshot_set(
        plan.stock_sha256, current_stock, after_paths
    )
    if _portfolio_paths(root) != plan.portfolio_paths:
        raise queue.CASMismatch(
            "conjunto de portfólios mudou durante a revalidação CAS"
        )


def _dependency_max_bytes(rel_path: str) -> int:
    if rel_path == SEMANTIC_CONTRACT_REL:
        return queue._MAX_WRITING_SEMANTIC_CONTRACT_BYTES
    if rel_path == portfolio_migrations.REGISTRY_REL_PATH:
        return portfolio_migrations.MAX_REGISTRY_BYTES
    if rel_path.startswith("data/editorial/v2_superseded/"):
        return portfolio_migrations.MAX_ARCHIVE_BYTES
    if rel_path.startswith("data/editorial/v2_semantic_superseded/"):
        return queue._MAX_WRITING_SEMANTIC_EVIDENCE_BYTES
    if _PORTFOLIO.fullmatch(rel_path) is not None:
        return MAX_PORTFOLIO_BYTES
    if (pathlib.PurePosixPath(rel_path).parent.as_posix() ==
            "data/editorial/v2_pages"):
        return MAX_STOCK_BYTES
    return MAX_WORKFLOW_BYTES


@contextmanager
def exclusive_lock(path: pathlib.Path = LOCK_PATH):
    fd = os.open(
        path,
        os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    locked = False
    try:
        info = os.fstat(fd)
        named = os.lstat(path)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                info.st_uid != os.geteuid() or
                not stat.S_ISREG(named.st_mode) or named.st_nlink != 1 or
                (info.st_dev, info.st_ino) != (named.st_dev, named.st_ino)):
            raise RuntimeError("lock da migração não é arquivo regular único")
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise queue.CASMismatch("migração já possui executor ativo") from error
        locked = True
        yield
    finally:
        if locked:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_replace_many(
    root: pathlib.Path,
    replacements: Sequence[tuple[str, bytes, bytes]],
    *,
    replace: Callable[[pathlib.Path, bytes, str], None] | None = None,
    before_last: Callable[[], None] | None = None,
    commit_marker_rel: str | None = None,
) -> None:
    """Instala saídas em sequência e restaura somente efeitos autenticados.

    O produtor CAS subjacente é deliberadamente fail-stop: uma falha de
    ``fsync`` ou da autenticação posterior pode ser devolvida depois de o
    rename já ter acontecido. Por isso, erro de ``replace`` não prova ausência
    de efeito. Saída intermediária que já contém exatamente ``after`` entra no
    conjunto de rollback. Se o marcador final apareceu, porém, os outputs não
    voltam à preimagem: remover ou esvaziar esse path perderia o inode que pode
    continuar recebendo escrita por FD aberto e criaria um recibo incoerente.
    """
    for rel_path, before, after in replacements:
        if not isinstance(rel_path, str):
            raise TypeError("path de saída precisa ser texto")
        pure = pathlib.PurePosixPath(rel_path)
        if (not rel_path or pure.is_absolute() or
                pure.as_posix() != rel_path or ".." in pure.parts):
            raise ValueError(f"path de saída inseguro: {rel_path!r}")
        if not isinstance(before, bytes) or not isinstance(after, bytes):
            raise TypeError(f"preimagem e saída precisam ser bytes: {rel_path}")

    rel_paths = [rel_path for rel_path, _, _ in replacements]
    if len(rel_paths) != len(set(rel_paths)):
        raise ValueError("transação repete path de saída")

    marker_path: pathlib.Path | None = None
    marker_after: bytes | None = None
    if commit_marker_rel is not None:
        if (not rel_paths or rel_paths[-1] != commit_marker_rel or
                rel_paths.count(commit_marker_rel) != 1):
            raise ValueError("commit marker precisa ser a última saída única")
        marker_path = root / commit_marker_rel
        marker_before = replacements[-1][1]
        marker_after = replacements[-1][2]
        if marker_before != b"":
            raise ValueError("commit marker precisa ter preimagem ausente")

    replace_fn = replace or (
        lambda path, payload, expected: queue.atomic_replace_cas(
            path, payload, expected
        )
    )

    def has_exact_payload(path: pathlib.Path, payload: bytes) -> bool:
        try:
            snapshot = queue.read_regular_file_snapshot(
                path,
                max_bytes=max(MAX_WORKFLOW_BYTES, len(payload) + 1),
            )
        except (OSError, RuntimeError, ValueError):
            return False
        return snapshot.payload == payload and snapshot.digest == _digest(payload)

    def observe_marker() -> tuple[bool, str]:
        """Distingue ausência segura de qualquer estado final observável.

        ``lexists`` sozinho não autentica tipo, hardlinks nem ancestrais. A
        leitura segura recusa esses casos; depois que outputs foram tocados,
        qualquer estado que não possa ser provado ausente é tratado como um
        marcador aparecido e força fail-stop sem rollback destrutivo.
        """
        if marker_path is None or marker_after is None:
            return False, "ausente"
        try:
            snapshot = queue.read_regular_file_snapshot(
                marker_path,
                max_bytes=max(MAX_WORKFLOW_BYTES, len(marker_after) + 1),
            )
        except FileNotFoundError:
            # ``read_regular_file_snapshot`` também pode devolver ENOENT para
            # pai ausente. Isso não é uma precondição válida: o CAS final não
            # conseguiria criar o marcador depois de alterar os outputs.
            try:
                parent = os.lstat(marker_path.parent)
            except OSError as error:
                return True, (
                    "diretório pai não autenticado "
                    f"({type(error).__name__})"
                )
            if not stat.S_ISDIR(parent.st_mode):
                return True, "diretório pai não é diretório regular"
            try:
                os.lstat(marker_path)
            except FileNotFoundError:
                return False, "ausente"
            except OSError as error:
                return True, (
                    "entrada final não autenticada "
                    f"({type(error).__name__})"
                )
            return True, "entrada final apareceu durante autenticação"
        except (OSError, RuntimeError, ValueError) as error:
            return True, (
                "entrada final insegura/não autenticada "
                f"({type(error).__name__})"
            )
        if (snapshot.payload == marker_after and
                snapshot.digest == _digest(marker_after)):
            return True, "payload exato"
        return True, "payload regular divergente"

    if marker_path is not None:
        marker_present, marker_state = observe_marker()
        if marker_present:
            raise ValueError(
                "commit marker precisa estar ausente antes da transação "
                f"({marker_state})"
            )

    installed: list[tuple[str, bytes, bytes]] = []
    marker_state_after_error: str | None = None
    try:
        for index, (rel_path, before, after) in enumerate(replacements):
            if before_last is not None and index == len(replacements) - 1:
                before_last()
            target = root / rel_path
            try:
                replace_fn(target, after, _digest(before))
            except Exception:
                if rel_path == commit_marker_rel:
                    marker_present, marker_state = observe_marker()
                    if marker_present:
                        marker_state_after_error = marker_state
                elif has_exact_payload(target, after):
                    # O produtor aplicou o efeito antes de reportar falha.
                    # Autenticá-lo permite restaurar somente bytes ainda nossos.
                    installed.append((rel_path, before, after))
                raise
            installed.append((rel_path, before, after))
    except Exception as install_error:
        # A falha pode vir de ``before_last`` (antes de chamar ``replace`` no
        # marcador) ou de qualquer output intermediário. Reobserve sempre: um
        # marcador ausente no preflight que apareceu desde então torna rollback
        # proibido, ainda que não tenha sido o call site que lançou.
        if marker_state_after_error is None and marker_path is not None:
            marker_present, marker_state = observe_marker()
            if marker_present:
                marker_state_after_error = marker_state
        if marker_state_after_error is not None:
            raise RuntimeError(
                "transação reportou erro depois que o commit marker apareceu "
                f"({marker_state_after_error}); outputs e marcador foram "
                "preservados sem rollback "
                "e a retomada deve autenticar o recibo"
            ) from install_error

        rolled_back: list[tuple[str, bytes, bytes]] = []
        rollback_errors: list[str] = []
        for rel_path, before, after in reversed(installed):
            if marker_path is not None:
                marker_present, marker_state = observe_marker()
                if marker_present:
                    marker_state_after_error = marker_state
                    break
            try:
                replace_fn(root / rel_path, before, _digest(after))
            except Exception as rollback_error:  # preserve bytes concorrentes
                if not has_exact_payload(root / rel_path, before):
                    rollback_errors.append(f"{rel_path}: {rollback_error}")
                else:
                    rolled_back.append((rel_path, before, after))
            else:
                if has_exact_payload(root / rel_path, before):
                    rolled_back.append((rel_path, before, after))
                else:
                    rollback_errors.append(
                        f"{rel_path}: rollback retornou sem preimagem autenticada"
                    )
            if marker_path is not None:
                marker_present, marker_state = observe_marker()
                if marker_present:
                    marker_state_after_error = marker_state
                    break

        if marker_state_after_error is not None:
            # O marcador apareceu durante o rollback. Reaplique somente efeitos
            # que este loop autenticou como restaurados; CAS recusa qualquer
            # evolução concorrente. Outputs ainda em ``after`` não são tocados.
            reapply_errors: list[str] = []
            for rel_path, before, after in reversed(rolled_back):
                try:
                    replace_fn(root / rel_path, after, _digest(before))
                except Exception as reapply_error:
                    if not has_exact_payload(root / rel_path, after):
                        reapply_errors.append(
                            f"{rel_path}: {reapply_error}"
                        )
                else:
                    if not has_exact_payload(root / rel_path, after):
                        reapply_errors.append(
                            f"{rel_path}: reaplicação sem efeito autenticado"
                        )
            detail = (
                "; evolução concorrente preservada durante reaplicação: " +
                "; ".join(reapply_errors)
                if reapply_errors else
                "; efeitos já rollbackados foram reaplicados por CAS"
            )
            raise RuntimeError(
                "commit marker apareceu durante rollback "
                f"({marker_state_after_error}); rollback foi interrompido" +
                detail
            ) from install_error
        if rollback_errors:
            raise RuntimeError(
                "transação falhou e rollback encontrou evolução concorrente; "
                "nenhum byte concorrente foi descartado: " +
                "; ".join(rollback_errors)
            ) from install_error
        raise RuntimeError(
            "transação falhou; saídas anteriores voltaram às preimagens CAS"
        ) from install_error


def _verify_completed_receipt(root: pathlib.Path) -> Mapping[str, Any] | None:
    receipt_path = root / RECEIPT_REL
    if not os.path.lexists(receipt_path):
        return None
    snapshot = _read_canonical_0644_artifact(
        root, RECEIPT_REL, max_bytes=1024 * 1024
    )
    if not snapshot.payload or not snapshot.payload.endswith(b"\n"):
        raise ValueError("recibo existente não termina com newline")
    value = queue.decode_json_no_duplicate_keys(snapshot.payload, RECEIPT_REL)
    if (not isinstance(value, dict) or
            set(value) != _RECEIPT_KEYS or
            value.get("schema_version") !=
            "v2_writing_inventory_pin_migration_v3" or
            value.get("migration_id") != "writing-inventory-pins-20260715" or
            value.get("checked_at") != "2026-07-15" or
            value.get("publication_touches") != [] or
            value.get("index_policy") != "noindex" or
            any(value.get(flag) is not False for flag in (
                "render_allowed", "sitemap_allowed",
                "publication_allowed", "approval", "publicly_indexable",
            )) or
            not isinstance(value.get("input_sha256"), dict) or
            not isinstance(value.get("absent_input_paths"), list) or
            not isinstance(value.get("stock_sha256"), dict) or
            not isinstance(value.get("output_sha256"), dict) or
            not isinstance(value.get("preimage_manifest_sha256"), str) or
            re.fullmatch(
                r"[0-9a-f]{64}", value["preimage_manifest_sha256"]
            ) is None or
            not isinstance(value.get("preimage_archive_sha256"), dict) or
            not isinstance(value.get("preimage_set_sha256"), str) or
            re.fullmatch(
                r"[0-9a-f]{64}", value["preimage_set_sha256"]
            ) is None or
            not isinstance(value.get("counts"), dict)):
        raise ValueError("recibo existente da migração é inválido")
    canonical_receipt = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    if canonical_receipt != snapshot.payload:
        raise ValueError("recibo existente da migração não é canônico")

    semantic_contract = queue.load_writing_semantic_contract(root)
    queue.verify_writing_semantic_contract_dependencies(
        root, semantic_contract
    )
    semantic_dependency_sha256 = _merge_dependency_sha256(
        {SEMANTIC_CONTRACT_REL: semantic_contract.digest},
        semantic_contract.dependency_sha256,
    )
    absent_input_paths = value["absent_input_paths"]
    if (absent_input_paths != sorted(set(absent_input_paths)) or
            any(not isinstance(rel_path, str) or
                queue._TARGET_REL_PATH.fullmatch(rel_path) is None
                for rel_path in absent_input_paths) or
            set(absent_input_paths) !=
            set(semantic_contract.absent_dependency_paths)):
        raise ValueError(
            "recibo não autentica ausências semânticas canônicas"
        )

    input_sha256 = value["input_sha256"]
    required_inputs = {
        **dict(EXPECTED_INPUT_SHA256),
        "portfolio_set": EXPECTED_PORTFOLIO_SET_SHA256,
        "aggregate_set": EXPECTED_AGGREGATE_SET_SHA256,
        **semantic_dependency_sha256,
    }
    if (any(input_sha256.get(path) != expected
            for path, expected in required_inputs.items()) or
            any(not isinstance(path, str) or not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for path, digest in input_sha256.items())):
        raise ValueError("recibo não autentica todas as preimagens one-shot")

    portfolio_sha256 = {
        rel_path: digest for rel_path, digest in input_sha256.items()
        if _PORTFOLIO.fullmatch(rel_path) is not None
    }
    if (not portfolio_sha256 or
            _snapshot_set_digest(portfolio_sha256) !=
            input_sha256["portfolio_set"]):
        raise ValueError(
            "recibo não liga portfolio_set aos seus membros exatos"
        )
    aggregate_paths = {
        f"data/editorial/v2_pages/{slug}.jsonl"
        for slug in AGGREGATE_SHARDS
    }
    aggregate_sha256 = {
        rel_path: digest for rel_path, digest in input_sha256.items()
        if rel_path in aggregate_paths
    }
    if (set(aggregate_sha256) != aggregate_paths or
            _snapshot_set_digest(aggregate_sha256) !=
            input_sha256["aggregate_set"]):
        raise ValueError(
            "recibo não liga aggregate_set aos seus membros exatos"
        )
    for rel_path in input_sha256:
        if rel_path in {"portfolio_set", "aggregate_set"}:
            continue
        pure = pathlib.PurePosixPath(rel_path)
        if (pure.is_absolute() or pure.as_posix() != rel_path or
                ".." in pure.parts or rel_path == RECEIPT_REL or
                not (
                    rel_path in EXPECTED_INPUT_SHA256 or
                    rel_path == SEMANTIC_CONTRACT_REL or
                    rel_path == PREIMAGE_MANIFEST_REL or
                    rel_path in _PREIMAGE_ARCHIVE_PATHS or
                    rel_path == portfolio_migrations.REGISTRY_REL_PATH or
                    rel_path.startswith("data/editorial/portfolio_v2/") or
                    rel_path.startswith("data/editorial/v2_pages/") or
                    rel_path.startswith("data/editorial/v2_superseded/") or
                    rel_path.startswith(
                        "data/editorial/v2_semantic_superseded/")
                )):
            raise ValueError(f"recibo contém dependência insegura: {rel_path}")

    preimage_bundle = _verify_preimage_manifest(root)
    current_preimage_sha256 = {
        path: snapshot.digest
        for path, snapshot in preimage_bundle.archives.items()
    }
    receipt_preimage_sha256 = value["preimage_archive_sha256"]
    current_preimage_set_sha256 = _preimage_set_digest(
        _preimage_entries(preimage_bundle.archives)
    )
    if (set(receipt_preimage_sha256) != _PREIMAGE_ARCHIVE_PATHS or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in receipt_preimage_sha256.values()) or
            receipt_preimage_sha256 != current_preimage_sha256 or
            value["preimage_set_sha256"] !=
            current_preimage_set_sha256 or
            value["preimage_manifest_sha256"] !=
            preimage_bundle.manifest.digest):
        raise queue.CASMismatch(
            "recibo diverge do bundle imutável de preimages"
        )
    for active_path, archive_path in PREIMAGE_ARCHIVE_BY_OUTPUT.items():
        if (input_sha256.get(active_path) !=
                receipt_preimage_sha256[archive_path] or
                input_sha256.get(archive_path) !=
                receipt_preimage_sha256[archive_path]):
            raise ValueError(
                "recibo não liga archive ao preimage do output: "
                f"{active_path}"
            )
    if input_sha256.get(PREIMAGE_MANIFEST_REL) != value[
            "preimage_manifest_sha256"]:
        raise ValueError("recibo não liga manifest às dependências")

    migration_catalog = portfolio_migrations.load_catalog(root)
    catalog_dependency_sha256 = dict(
        migration_catalog.dependency_sha256
    )
    if portfolio_migrations.REGISTRY_REL_PATH not in catalog_dependency_sha256:
        raise queue.CASMismatch(
            "registro de migrações desapareceu depois da operação one-shot"
        )
    trusted_supersession_sha256 = (
        _trusted_supersession_dependency_sha256()
    )
    expected_input_paths = {
        *EXPECTED_INPUT_SHA256,
        *portfolio_sha256,
        *aggregate_paths,
        PREIMAGE_MANIFEST_REL,
        *_PREIMAGE_ARCHIVE_PATHS,
        *catalog_dependency_sha256,
        *trusted_supersession_sha256,
        *semantic_dependency_sha256,
        "portfolio_set",
        "aggregate_set",
    }
    if set(input_sha256) != expected_input_paths:
        raise ValueError(
            "recibo contém conjunto de dependências aberto/incompleto"
        )
    if (set(absent_input_paths) & set(input_sha256) or
            set(absent_input_paths) & set(value["stock_sha256"])):
        raise ValueError(
            "recibo mistura dependência semântica ausente com input/estoque"
        )
    live_legal_dependencies = _merge_dependency_sha256(
        catalog_dependency_sha256,
        trusted_supersession_sha256,
        semantic_dependency_sha256,
        {PREIMAGE_MANIFEST_REL: preimage_bundle.manifest.digest},
        current_preimage_sha256,
    )
    if any(
        input_sha256[rel_path] != digest
        for rel_path, digest in live_legal_dependencies.items()
    ):
        raise queue.CASMismatch(
            "recibo diverge das dependências jurídicas vivas da migração"
        )

    # O receipt é uma prova durável do epoch que produziu as filas, não apenas
    # um objeto internamente autoconsistente. Reautentique todo input que deve
    # continuar vivo depois da migração. Os três workflows de saída são a única
    # exceção: seus hashes correntes são os pós-estados autenticados abaixo.
    current_portfolio_paths = _portfolio_paths(root)
    if current_portfolio_paths != tuple(sorted(portfolio_sha256)):
        raise queue.CASMismatch(
            "migração já executada, mas conjunto de portfólios evoluiu"
        )
    expected_current_dependencies = {
        rel_path: digest
        for rel_path, digest in input_sha256.items()
        if rel_path not in {"portfolio_set", "aggregate_set"}
        and rel_path not in _OUTPUT_PATHS
    }
    current_dependencies = {
        rel_path: queue.snapshot_sha256(
            root / rel_path,
            max_bytes=_dependency_max_bytes(rel_path),
        )
        for rel_path in sorted(expected_current_dependencies)
    }
    queue.authenticate_snapshot_set(
        expected_current_dependencies,
        current_dependencies,
        expected_current_dependencies,
    )
    if _portfolio_paths(root) != current_portfolio_paths:
        raise queue.CASMismatch(
            "conjunto de portfólios mudou durante verificação do receipt"
        )

    stock_sha256 = value["stock_sha256"]
    if (not stock_sha256 or
            any(not isinstance(rel_path, str) or
                pathlib.PurePosixPath(rel_path).parent.as_posix() !=
                "data/editorial/v2_pages" or
                pathlib.PurePosixPath(rel_path).name == "" or
                not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for rel_path, digest in stock_sha256.items()) or
            value.get("stock_set_sha256") !=
            _snapshot_set_digest(stock_sha256)):
        raise ValueError("recibo contém snapshot de estoque inválido")
    if any(stock_sha256.get(path) != digest
           for path, digest in aggregate_sha256.items()):
        raise ValueError(
            "recibo diverge entre aggregates e snapshot de estoque"
        )
    semantic_page_sha256 = {
        rel_path: digest
        for rel_path, digest in semantic_contract.dependency_sha256.items()
        if pathlib.PurePosixPath(rel_path).parent.as_posix() ==
        "data/editorial/v2_pages"
    }
    if any(
        stock_sha256.get(rel_path) != digest
        for rel_path, digest in semantic_page_sha256.items()
    ):
        raise ValueError(
            "recibo diverge entre dependências semânticas e estoque"
        )
    if set(semantic_contract.absent_dependency_paths) & set(stock_sha256):
        raise queue.CASMismatch(
            "recibo declara owner semântico ausente presente no estoque"
        )
    current_stock_paths = tuple(
        path.relative_to(root).as_posix() for path in _stock_paths(root)
    )
    if current_stock_paths != tuple(sorted(stock_sha256)):
        raise queue.CASMismatch(
            "migração já executada, mas conjunto de shards evoluiu"
        )
    current_stock = {
        rel_path: queue.snapshot_sha256(
            root / rel_path, max_bytes=MAX_STOCK_BYTES
        )
        for rel_path in current_stock_paths
    }
    queue.authenticate_snapshot_set(
        stock_sha256, current_stock, current_stock_paths
    )

    output_sha256 = value["output_sha256"]
    if (set(output_sha256) != _OUTPUT_PATHS or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in output_sha256.values())):
        raise ValueError("recibo contém conjunto de saídas aberto/incompleto")
    counts = value["counts"]
    if any(type(count) is not int for count in counts.values()):
        raise ValueError("recibo contém contador não inteiro")
    _validate_counts(counts)
    expected_pin_digest = _digest(json.dumps(
        {slug: list(OVERFLOW_PINS[slug]) for slug in sorted(OVERFLOW_PINS)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8"))
    if value.get("overflow_pin_sha256") != expected_pin_digest:
        raise ValueError("recibo não autentica os pins revisados")

    current_outputs = {
        rel_path: _read_canonical_0644_artifact(
            root, rel_path, max_bytes=MAX_WORKFLOW_BYTES
        ).digest
        for rel_path in sorted(output_sha256)
    }
    queue.authenticate_snapshot_set(
        output_sha256, current_outputs, output_sha256
    )

    # Sandwich final: uma troca concorrente após a primeira leitura não pode
    # transformar receipt stale em sucesso. O lock one-shot exclui outro
    # migrador; estas releituras fecham escritores externos nos inputs.
    final_dependencies = {
        rel_path: queue.snapshot_sha256(
            root / rel_path,
            max_bytes=_dependency_max_bytes(rel_path),
        )
        for rel_path in sorted(current_dependencies)
    }
    queue.authenticate_snapshot_set(
        current_dependencies,
        final_dependencies,
        current_dependencies,
    )
    final_stock_paths = tuple(
        path.relative_to(root).as_posix() for path in _stock_paths(root)
    )
    final_stock = {
        rel_path: queue.snapshot_sha256(
            root / rel_path, max_bytes=MAX_STOCK_BYTES
        )
        for rel_path in final_stock_paths
    }
    queue.authenticate_snapshot_set(
        current_stock, final_stock, final_stock_paths
    )
    final_outputs = {
        rel_path: _read_canonical_0644_artifact(
            root, rel_path, max_bytes=MAX_WORKFLOW_BYTES
        ).digest
        for rel_path in sorted(current_outputs)
    }
    queue.authenticate_snapshot_set(
        current_outputs, final_outputs, current_outputs
    )
    final_preimage_bundle = _verify_preimage_manifest(root)
    if (final_preimage_bundle.manifest.digest !=
            preimage_bundle.manifest.digest or
            {
                path: snapshot.digest
                for path, snapshot in final_preimage_bundle.archives.items()
            } != current_preimage_sha256):
        raise queue.CASMismatch(
            "bundle de preimages mudou durante verificação do receipt"
        )
    if (_portfolio_paths(root) != current_portfolio_paths or
            _read_canonical_0644_artifact(
                root, RECEIPT_REL, max_bytes=1024 * 1024
            ).digest != snapshot.digest):
        raise queue.CASMismatch(
            "receipt ou conjunto de portfólios mudou durante verificação"
        )
    queue.verify_writing_semantic_contract_dependencies(
        root, semantic_contract
    )
    return value


def run(root: pathlib.Path = ROOT) -> Mapping[str, int]:
    with exclusive_lock():
        completed = _verify_completed_receipt(root)
        if completed is not None:
            counts = completed.get("counts")
            if not isinstance(counts, dict):
                raise ValueError("recibo concluído perdeu contadores")
            return counts
        plan = build_plan(root)
        _revalidate_plan(root, plan)
        queue.verify_writing_semantic_contract_dependencies(
            root, plan.semantic_contract
        )
        replacements = [
            (
                rel_path,
                plan.inputs[rel_path].payload,
                plan.outputs[rel_path],
            )
            for rel_path in (
                FULL_REL, TODO_REL, TODO_WITHOUT_TELECOM_REL
            )
        ]
        replacements.append((RECEIPT_REL, b"", plan.receipt_payload))
        if replacements[-1][0] != RECEIPT_REL:
            raise RuntimeError("recibo precisa ser o commit marker final")

        def validate_before_receipt() -> None:
            for rel_path, payload in plan.outputs.items():
                if _read_canonical_0644_artifact(
                        root,
                        rel_path,
                        max_bytes=MAX_WORKFLOW_BYTES,
                ).digest != _digest(payload):
                    raise queue.CASMismatch(
                        f"saída instalada divergiu: {rel_path}"
                    )
            _revalidate_plan(root, plan, outputs_installed=True)
            queue.verify_writing_semantic_contract_dependencies(
                root, plan.semantic_contract
            )

        atomic_replace_many(
            root,
            replacements,
            before_last=validate_before_receipt,
            commit_marker_rel=RECEIPT_REL,
        )
        _verify_completed_receipt(root)
        return plan.counts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--prepare-preimages",
        action="store_true",
        help=(
            "cria/reutiliza somente o bundle inerte append-only; não altera "
            "os workflows ativos"
        ),
    )
    action.add_argument(
        "--apply",
        action="store_true",
        help="executa a transação somente após integrar o bundle inerte",
    )
    args = parser.parse_args(argv)
    if args.prepare_preimages:
        with exclusive_lock():
            bundle = prepare_preimages()
        print(json.dumps({
            "migration_id": "writing-inventory-pins-20260715",
            "manifest": PREIMAGE_MANIFEST_REL,
            "manifest_sha256": bundle.manifest.digest,
            "preimage_archive_sha256": {
                path: snapshot.digest
                for path, snapshot in sorted(bundle.archives.items())
            },
            "active_workflows_unchanged": True,
            "publication": False,
        }, sort_keys=True, ensure_ascii=False))
        return 0
    counts = run()
    print(json.dumps(dict(counts), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
