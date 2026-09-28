"""Produtor determinístico da fila de revisão v2.

O auditor é a única fonte dos defeitos. Este módulo apenas transforma o
relatório completo em itens de trabalho e publica o snapshot com CAS, sem
truncar alvos bloqueantes nem sobrescrever evolução concorrente.
"""

from __future__ import annotations

import atexit
import collections
import concurrent.futures
import base64
import functools
import fcntl
import ctypes
import datetime
import errno
import heapq
import hashlib
import json
import math
import os
import pathlib
import re
import secrets
import sqlite3
import stat
import tempfile
from typing import Any, Callable, Iterable, Mapping, NamedTuple
from urllib.parse import unquote, urlsplit

if __package__:
    from .v2_stock_epoch import (
        canonical_stock_root_for_target,
        canonical_stock_write_lease,
    )
else:
    from v2_stock_epoch import (  # type: ignore[no-redef]
        canonical_stock_root_for_target,
        canonical_stock_write_lease,
    )


NGRAM_DEFECT_CLASSES = frozenset(("ngram_dup", "ngram_dup_global"))
WRITING_RECOVERY_DEFECT_TARGETS = {
    # audit_v2_pages.audit_file: framing/JSON inválido não oferece intent_id
    # confiável. Isso jamais autoriza uma revisão editorial file-wide: o shard
    # integral volta ao produtor de escrita/recovery, ligado à preimagem crua.
    "json_invalido": re.compile(
        r"(?:jsonl_sem_lf_terminal|jsonl_cr_ou_crlf_nao_canonico|"
        r"linha_[1-9][0-9]*)\Z"),
    # A cardinalidade também pertence ao slice integral do inventário. Um
    # revisor não pode criar/remover registros sob o contrato cardinal do review.
    "contagem": re.compile(r"esperado=[0-9]+ real=[0-9]+\Z"),
}
WRITING_RECOVERY_DEFECT_CLASSES = frozenset(
    WRITING_RECOVERY_DEFECT_TARGETS)
# Findings de registro que não carregam identidade endereçável também exigem
# recomposição raw. Tombstone com intent_id canônico continua sendo revisão
# row-level; apenas a projeção literalmente sem identidade amplia para recovery.
WRITING_RECOVERY_UNADDRESSABLE_TARGETS = {
    "tombstone_invalido": frozenset(("(sem-intent)",)),
    "estrutura": frozenset(("(sem-intent)",)),
}
# Compatibilidade de leitura para finalizadores/recibos de filas v2 anteriores.
# O produtor vigente não consulta este alias nem emite novos itens file-wide;
# removê-lo antes de drenar/inutilizar artefatos antigos quebraria a validação
# fail-closed desses recibos sem tornar recovery executável.
FILE_WIDE_REVIEW_DEFECT_TARGETS = WRITING_RECOVERY_DEFECT_TARGETS
V3_SIMILARITY_DEFECT_CLASSES = frozenset((
    "body_jaccard_near_duplicate",
    "editorial_span_duplicate",
    "editorial_repeat_density",
))
V3_EXACT_REVIEW_DEFECT_CLASSES = frozenset((
    "title_dup_global", "meta_dup_global", "h1_dup_global",
))
V3_REVIEW_DEFECT_CLASSES = (
    V3_SIMILARITY_DEFECT_CLASSES | V3_EXACT_REVIEW_DEFECT_CLASSES)
V3_OPERATIONAL_DEFECT_CLASSES = frozenset(("intent_id_dup_global",))
GLOBAL_DISTINCTNESS_MODE = "global-distinctness-v3-read-only"
V3_CANDIDATE_REASON_ORDER = (
    "intent", "title", "meta", "h1", "jaccard", "density",
)
V3_BODY_JACCARD_THRESHOLD = 0.70
V3_IDENTICAL_SPAN_THRESHOLD = 40
V3_REPEAT_DENSITY_THRESHOLD = 0.15
V3_COUNTER_MAX = 100_000_000
EXACT_COMPONENT_WAVE_SCHEMA = "v2_exact_component_wave_v1"
DEFAULT_EXACT_COMPONENT_WAVE_MEMBERS = 24
MAX_EXACT_COMPONENT_WAVE_MEMBERS = 31
WRITING_RAW_RECOVERY_PREIMAGE_DIR = (
    "data/editorial/v2_raw_recovery_preimages")
_WRITING_RAW_RECOVERY_PREIMAGE_REL = re.compile(
    r"data/editorial/v2_raw_recovery_preimages/[0-9a-f]{64}\.raw")
NGRAM_EVIDENCE_WORDS = 12
NGRAM_EVIDENCE_FIELD_RE = re.compile(
    r"^(?:title|meta_description|h1|opening|"
    r"sections\[\d+\]\.(?:heading|text)|faq\[\d+\]\.(?:q|a))$"
)


class CASMismatch(RuntimeError):
    """O arquivo mudou depois da leitura usada para montar o snapshot."""


class DistinctnessOperationalError(ValueError):
    """Falha de infraestrutura/identidade que jamais vira tarefa editorial."""

    def __init__(
        self,
        reason_codes: Iterable[str],
        affected_shards: Iterable[str],
        details: Iterable[str] = (),
    ) -> None:
        def summarize(values: Iterable[str], limit: int) -> dict[str, Any]:
            digest = hashlib.sha256()
            sample: list[str] = []
            total = 0
            for value in values:
                normalized = str(value)
                digest.update(normalized.encode("utf-8"))
                digest.update(b"\n")
                total += 1
                if len(sample) < limit:
                    sample.append(normalized)
            return {
                "total": total,
                "sha256": digest.hexdigest(),
                "sample": sample,
            }

        reasons = tuple(sorted(set(reason_codes)))
        shard_summary = summarize(affected_shards, 32)
        detail_summary = summarize(details, 32)
        self.rca = {
            "schema_version": 1,
            "kind": "distinctness_operational_rca",
            "reason_codes": list(reasons),
            "affected_shards": shard_summary["sample"],
            "affected_shards_total": shard_summary["total"],
            "affected_shards_sha256": shard_summary["sha256"],
            "details": detail_summary["sample"],
            "details_total": detail_summary["total"],
            "details_sha256": detail_summary["sha256"],
            "editorial_tasks": 0,
            "publication_allowed": False,
            "index_policy": "noindex",
        }
        super().__init__(
            "distinctness operacional; zero tarefas editoriais: " +
            json.dumps(self.rca, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"))
        )


class BatchCompletion(NamedTuple):
    """Resultado fail-closed da presença estrutural de um lote de escrita."""

    complete: bool
    reusable_expected: tuple[str, ...]
    authenticated_extras: tuple[str, ...]
    # ★ O VEREDITO SEM O MOTIVO CUSTOU UM DIA DE DIAGNÓSTICO ERRADO (2026-09-05).
    #
    # ``complete`` é a conjunção de cinco cláusulas independentes. Quem chama
    # recebia UM bit e não tinha como dizer o que faltava: o fechamento
    # (``verify_v2_writing_queue_closure.py``) traduzia qualquer uma das cinco
    # por "classificador não confirmou lote completo" e embrulhava em "lote
    # omitido sem shard completo", frase que se lê como "não há páginas". Sobre
    # o inventário vivo desse dia as cinco cláusulas separavam 86 lotes em
    # quatro populações com destinos OPOSTOS — 27 sem shard nenhum (185 páginas
    # a redigir), 19 com o shard faltando 1–5 intenções (39 a redigir), 6 com
    # intenção bloqueada pelo contrato semântico (recorte, não redação) e 34 com
    # o conjunto INTEIRO escrito e só a ordem das linhas divergindo do pin
    # (zero redação: ``tools/generate-v2-shard-slice-reorder``). Uma frase só
    # para quatro destinos é o defeito.
    #
    # ``reasons`` é ADITIVO e não participa do cálculo de ``complete``: um bug
    # aqui nunca pode transformar um lote reprovado em aprovado. A invariante
    # ``complete == (not reasons)`` é cobrada por teste sobre a topologia viva,
    # não por raise em runtime — levantar aqui converteria lote pronto em
    # SystemExit dentro de ``ops/relaunch-writing.sh``.
    #
    # O vocabulário é o MESMO de ``tools/generate-writing-queue-blocker-census``
    # (shard_ausente/linha_faltante/bloqueio_semantico/ordem_divergente/
    # corpo_nao_reusavel) de propósito: duas ferramentas que nomeiam a mesma
    # causa com palavras diferentes reabrem exatamente o defeito que esta
    # família já pagou três vezes.
    reasons: tuple[str, ...] = ()


class ReviewScope(NamedTuple):
    """Escopo editorial autenticado sem fallback implícito para o shard."""

    file_wide: bool
    target_intents: tuple[str, ...]


class WritingSourceResolution(NamedTuple):
    """Projeção autenticada do slice que o worker deve materializar."""

    selected_intents: tuple[str, ...]
    source_overrides: Mapping[str, Mapping[str, Mapping[str, str]]]
    strict_source_intents: tuple[str, ...]


class WritingSemanticContract(NamedTuple):
    """Snapshot dos recortes, owners atuais e preimagens semanticamente antigas."""

    digest: str
    unresolved_intents: frozenset[str]
    requirement_fingerprints: Mapping[str, str]
    portfolio_rel_paths: Mapping[str, str]
    target_rel_paths: Mapping[str, str]
    superseded_target_rel_paths: Mapping[str, str]
    superseded_page_record_sha256: Mapping[str, str | None]
    evidence_kinds: Mapping[str, str]
    evidence_rel_paths: Mapping[str, str]
    evidence_sha256: Mapping[str, str]
    dependency_sha256: Mapping[str, str]
    absent_dependency_paths: frozenset[str]


_PORTFOLIO_REL_PATH = re.compile(
    r"data/editorial/portfolio_v2/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"
)
_TARGET_REL_PATH = re.compile(
    r"data/editorial/v2_pages/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"
)
_SOURCE_HINT_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_FAMILY_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_INTENT_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_OFFICIAL_SOURCE_SUFFIXES = ("gov.br", "jus.br", "leg.br", "mp.br")
_WRITING_SOURCE_EXACT_HOSTS = frozenset({
    "sistemas.cfm.org.br",
    "site.cfp.org.br",
    "www.icao.int",
    "publications.europa.eu",
    "oeil.europarl.europa.eu",
    "europa.eu",
    "www.govinfo.gov",
    "www.subtel.gob.cl",
    # Gazetas/diarios oficiais estrangeiros (decisao do dono 2026-07-15).
    "dre.pt",
    "diariodarepublica.pt",
    "www.boe.es",
    "www.normattiva.it",
    "www.gazzettaufficiale.it",
    "www.gesetze-im-internet.de",
    "isap.sejm.gov.pl",
    "www.esteri.it",
    # Ministero dell'Interno: autoridade italiana que decide o pedido de
    # cidadania. Aceito em internal/v2ingest/validate.go e ausente daqui, o que
    # fazia a fila de revisao recusar a fonte que o ingest considera oficial.
    "www.interno.gov.it",
    "www1.interno.gov.it",
    "eur-lex.europa.eu",
    "portaldascomunidades.mne.gov.pt",
    # Conselho Federal da OAB. Aceito em internal/v2ingest/validate.go desde
    # 2026-09-05; ausente daqui, a fila de revisao recusaria a fonte que o
    # ingest considera oficial -- o mesmo defeito que o Ministero dell'Interno
    # produziu. A medicao esta em internal/oabgate/fonteoficial.go.
    "www.oab.org.br",
})
_CANONICAL_OFFICIAL_HOST_RE = re.compile(
    r"[a-z0-9-]+(?:\.[a-z0-9-]+)+\Z")
_SOURCE_HINT_CATALOG_REL_PATH = "data/editorial/v2_source_hint_catalog.json"
_WRITING_SEMANTIC_CONTRACT_REL_PATH = (
    "data/editorial/v2_writing_semantic_contract.json"
)
_MAX_SOURCE_RESOLUTION_PROJECTION_BYTES = 4 * 1024 * 1024
_MAX_OFFICIAL_SOURCE_URL_BYTES = 4096
_MAX_WRITING_SEMANTIC_CONTRACT_BYTES = 4 * 1024 * 1024
_MAX_WRITING_SEMANTIC_EVIDENCE_BYTES = 64 * 1024 * 1024
_MAX_WRITING_SEMANTIC_SNAPSHOT_BYTES = 64 * 1024 * 1024
MAX_REVIEW_QUEUE_ITEM_BYTES = 8 * 1024 * 1024
MAX_REVIEW_QUEUE_OUTPUT_BYTES = 64 * 1024 * 1024
DEFAULT_REVIEW_QUEUE_OUTPUT_BYTES = 60 * 1024 * 1024
_WRITING_SEMANTIC_EVIDENCE_PATHS = frozenset({
    (
        "data/editorial/v2_superseded/"
        "duplicate-intent-consolidation-2026-07-15.jsonl"
    ),
    (
        "data/editorial/v2_semantic_superseded/"
        "writing-semantic-recuts-20260715.jsonl"
    ),
})
_WRITING_SEMANTIC_REQUIREMENTS_SHA256 = (
    "0294306cf27b95f3d1dec31baf0036827351921fa19a7368a4ba0b3e2a6492c0"
)
_WRITING_SEMANTIC_REVIEW_CONTRACT = (
    "codex_legal_semantic_exact_page+deterministic_material_v1"
)


def _utc_validation_date() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def _canonical_official_source_url(
    value: str,
    *,
    require_specific_path: bool = True,
) -> bool:
    """Aceita somente autoridade HTTPS literal e path documental específico.

    ``urlsplit().hostname`` normaliza caixa, enquanto parsers WHATWG também
    apagam a porta ``:443``. A comparação com ``netloc`` cru impede que uma
    exceção exact-host atravesse por caixa alternativa, escape, userinfo,
    porta explícita, ponto terminal ou subdomínio adicional.
    """
    if not isinstance(value, str):
        return False
    try:
        encoded_value = value.encode("utf-8")
    except UnicodeEncodeError:
        # Surrogate isolado não representa URL UTF-8 e diverge dos parsers JS.
        return False
    if (len(encoded_value) > _MAX_OFFICIAL_SOURCE_URL_BYTES or
            not value.startswith("https://") or
            any(ord(char) < 0x20 or ord(char) == 0x7f or
                ord(char) in (0xfffd, 0x2028, 0x2029)
                for char in value)):
        return False
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname or ""
        port = parsed.port
        if (re.search(r"%(?![0-9A-Fa-f]{2})", parsed.path) or
                re.search(r"%(?![0-9A-Fa-f]{2})", parsed.fragment)):
            return False
        decoded_path = unquote(parsed.path, errors="strict")
        decoded_fragment = unquote(parsed.fragment, errors="strict")
    except (TypeError, ValueError, UnicodeError):
        return False
    path_segments = decoded_path.split("/")
    if path_segments and path_segments[-1] == "":
        path_segments.pop()
    canonical_path = (
        bool(path_segments)
        and path_segments[0] == ""
        and all(segment not in ("", ".", "..")
                for segment in path_segments[1:])
    )
    specific_path = canonical_path and len(path_segments) > 1
    suffix_allowed = any(
        hostname == suffix or hostname.endswith("." + suffix)
        for suffix in _OFFICIAL_SOURCE_SUFFIXES)
    exact_allowed = hostname in _WRITING_SOURCE_EXACT_HOSTS
    fragment_allowed = (
        "#" not in value or
        bool(decoded_fragment) and
        all(not (ord(char) < 0x20 or ord(char) == 0x7f or
                ord(char) in (0xfffd, 0x2028, 0x2029))
            for char in decoded_fragment)
    )
    return (
        parsed.scheme == "https"
        and bool(hostname)
        and _CANONICAL_OFFICIAL_HOST_RE.fullmatch(hostname) is not None
        and parsed.username is None
        and parsed.password is None
        and port is None
        and parsed.netloc == hostname
        and fragment_allowed
        and canonical_path
        and (specific_path or not require_specific_path)
        and (specific_path or not parsed.query)
        and (suffix_allowed or exact_allowed)
    )


def decode_json_no_duplicate_keys(value: str | bytes, label: str) -> Any:
    """Decodifica JSON recusando chaves repetidas em qualquer objeto."""
    if not isinstance(value, (str, bytes)):
        raise TypeError(f"{label}: payload JSON deve ser texto ou bytes")
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{label}: JSON não é UTF-8") from error

    def closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"{label}: chave JSON duplicada: {key}")
            result[key] = item
        return result

    try:
        return json.loads(value, object_pairs_hook=closed_object)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label}: JSON inválido") from error


def _semantic_contract_fingerprint(value: Mapping[str, Any]) -> str:
    """Hash estável de um requisito fechado, independente da indentação."""
    return _sha256(json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8"))


def _semantic_page_material_evidence(
    page: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
    """Recalcula a evidência material mínima da página semanticamente revista.

    A satisfação jurídica do recorte continua sendo uma atestação explícita do
    revisor Codex; este adaptador impede que essa atestação seja anexada a um
    objeto fino, fonte sem proveniência ou bytes diferentes dos efetivamente
    revistos. Não alega substituir o auditor global de release.
    """
    if not isinstance(page, Mapping) or page.get("skipped") is True:
        raise ValueError(f"{label}: página não material")

    def canonical_text(value: Any, field: str) -> str:
        if (not isinstance(value, str) or not value or
                value != value.strip() or
                any((ord(char) < 0x20 and char not in "\n\t") or
                    0xd800 <= ord(char) <= 0xdfff or
                    ord(char) in (0xfffd, 0x2028, 0x2029)
                    for char in value)):
            raise ValueError(f"{label}: {field} não é texto canônico")
        return value

    visible: dict[str, Any] = {}
    for field in ("title", "meta_description", "h1", "opening"):
        visible[field] = canonical_text(page.get(field), field)
    if (not 20 <= len(visible["title"]) <= 65 or
            not 70 <= len(visible["meta_description"]) <= 160 or
            visible["h1"].casefold() == visible["title"].casefold()):
        raise ValueError(f"{label}: title/meta/H1 não passam forma pública")

    sections = page.get("sections")
    if not isinstance(sections, list) or len(sections) < 2:
        raise ValueError(f"{label}: sections não comprovam página material")
    canonical_sections: list[dict[str, str]] = []
    for index, section in enumerate(sections, 1):
        if not isinstance(section, Mapping):
            raise ValueError(f"{label}: seção {index} não é objeto")
        canonical_sections.append({
            "heading": canonical_text(
                section.get("heading"), f"sections[{index}].heading"),
            "text": canonical_text(
                section.get("text"), f"sections[{index}].text"),
        })
    visible["sections"] = canonical_sections

    faq = page.get("faq", [])
    if not isinstance(faq, list):
        raise ValueError(f"{label}: FAQ não é lista")
    canonical_faq: list[dict[str, str]] = []
    for index, item in enumerate(faq, 1):
        if not isinstance(item, Mapping):
            raise ValueError(f"{label}: FAQ {index} não é objeto")
        canonical_faq.append({
            "q": canonical_text(item.get("q"), f"faq[{index}].q"),
            "a": canonical_text(item.get("a"), f"faq[{index}].a"),
        })
    visible["faq"] = canonical_faq

    body_parts = [visible["opening"]]
    for section in canonical_sections:
        body_parts.extend((section["heading"], section["text"]))
    for item in canonical_faq:
        body_parts.extend((item["q"], item["a"]))
    computed_word_count = len(re.findall(
        r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+", " ".join(body_parts)))
    declared_word_count = page.get("word_count")
    if (type(declared_word_count) is not int or
            computed_word_count < 80 or
            abs(declared_word_count - computed_word_count) * 10 >
            computed_word_count):
        raise ValueError(f"{label}: word_count não autentica corpo útil")

    if (page.get("lane") not in ("comercial", "informativa") or
            ("needs_source_research" in page and
             page.get("needs_source_research") is not False)):
        raise ValueError(f"{label}: lane/pesquisa de fonte não fechadas")
    topics = page.get("internal_link_topics")
    if (not isinstance(topics, list) or len(topics) < 2 or
            len(topics) != len(set(topics)) or
            any(not isinstance(topic, str) or not topic or
                topic != topic.strip() for topic in topics)):
        raise ValueError(f"{label}: tópicos internos não canônicos")

    sources = page.get("official_sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise ValueError(f"{label}: fontes oficiais insuficientes")
    canonical_sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    current_date = _utc_validation_date()
    for index, source in enumerate(sources, 1):
        source_label = f"{label}:official_sources[{index}]"
        if (not isinstance(source, Mapping) or
                set(source) != {
                    "name", "url", "anchor_claim", "verified_at",
                    "http_status"}):
            raise ValueError(f"{source_label}: schema de proveniência inválido")
        name = canonical_text(source.get("name"), source_label + ".name")
        anchor = canonical_text(
            source.get("anchor_claim"), source_label + ".anchor_claim")
        url = source.get("url")
        verified_at = source.get("verified_at")
        status = source.get("http_status")
        if (not isinstance(url, str) or
                not _canonical_official_source_url(url) or
                url in seen_urls or
                not isinstance(verified_at, str) or
                re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", verified_at)
                is None or
                type(status) is not int or status not in (200, 203, 206)):
            raise ValueError(f"{source_label}: proveniência não canônica")
        try:
            verified_date = datetime.date.fromisoformat(verified_at)
        except ValueError as error:
            raise ValueError(
                f"{source_label}: data de proveniência inválida") from error
        # Data FUTURA continua reprovando: é conferência que não pode ter
        # acontecido, sinal de fabricação. Idade sozinha NÃO reprova — "faz 31
        # dias que conferi" não torna a Lei 8.245/1991 menos vigente, e o gate
        # vencia sozinho, sem ninguém mudar nada, travando a escrita do acervo
        # inteiro (12.266 de 23.699 fontes já passavam dos 30 dias em
        # 2026-08-12). A idade virou higiene, cobrada por
        # tools/check-official-source-freshness e reconferida de verdade por
        # tools/verify-official-sources, ambos lendo o prazo de
        # internal/v2writingsemantic para não existirem dois números. A
        # revogação, que é a pergunta que de fato protege o leitor, tem regra
        # substantiva própria em internal/v2ingest/revoked_legal_sources.go e
        # na família current_legal_fact_stale_assertion.
        if verified_date > current_date:
            raise ValueError(f"{source_label}: proveniência está no futuro")
        seen_urls.add(url)
        canonical_sources.append({
            "name": name,
            "url": url,
            "anchor_claim": anchor,
            "verified_at": verified_at,
            "http_status": status,
        })

    def digest(value: Any) -> str:
        return _sha256(json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))

    return {
        "contract": "v2_semantic_page_material_v1",
        "visible_text_sha256": digest(visible),
        "official_sources_sha256": digest(canonical_sources),
        "computed_word_count": computed_word_count,
    }


_SNAPSHOT_INDEX_REL_PATH = ".agents/runtime/cache/v2_snapshot_index.sqlite3"
_SNAPSHOT_INDEX_SINGLETON: "_PersistentSnapshotIndex | None" = None


def _stat_identity_stamp(info: os.stat_result) -> tuple[int, int, int, int, int]:
    """Identidade observável do arquivo: troca a qualquer escrita real.

    ``st_ctime_ns`` entra junto de dispositivo, inode, tamanho e ``st_mtime_ns``
    porque o kernel o atualiza em toda mudança de conteúdo ou de metadado e o
    espaço de usuário não consegue reescrevê-lo (``utimensat`` só ajusta atime e
    mtime). O carimbo é, portanto, estritamente mais forte que o memo em RAM
    histórico deste módulo, que comparava apenas tamanho, mtime_ns e inode.
    """
    return (info.st_dev, info.st_ino, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


class _PersistentSnapshotIndex:
    """Índice incremental (stat -> digest + intents) partilhado entre processos.

    O produtor recarrega o contrato semântico uma vez por lote, e cada driver de
    promoção roda o lote em um PROCESSO NOVO: qualquer memo em RAM nasce frio e
    o estoque inteiro era relido e redecodificado do zero (medido em 2026-08-04:
    855 shards / 52,3 MB, 960 ms só na carga, ~28 min para drenar o acervo e
    ~47 h projetadas em 100k páginas). Este índice persiste, por caminho
    absoluto, o carimbo (device, inode, tamanho, mtime_ns, ctime_ns) junto do
    digest SHA-256 e — para shard de estoque — dos ``intent_id`` na ordem exata
    das linhas.

    Por que isto NÃO afrouxa nenhuma garantia:

    * o carimbo é estritamente mais estrito que o memo em RAM já sancionado em
      ``_stat_cached_snapshot_sha256`` (que compara só tamanho, mtime_ns e
      inode) e que o ``_semantic_contract_epoch`` de
      ``generate-v2-shard-slice-reorder``; ``st_ctime_ns`` não é ajustável por
      espaço de usuário e toda escrita do próprio CAS instala inode novo
      (``RENAME_EXCHANGE`` sobre arquivo temporário), então escrita concorrente,
      shard criado, removido ou reaparecido sempre invalidam a entrada;
    * o digest lido daqui só existe para POUPAR trabalho, nunca para decidir
      sozinho: ``writing_promotion_dependency_epoch`` fecha com
      ``_assert_dependency_epoch``, que RELÊ e re-hasheia integralmente cada
      dependência antes de qualquer byte ser escrito. Entrada stale ou forjada
      diverge do hash real e vira ``CASMismatch`` — o pior caso é recusar a
      promoção, jamais aceitar estoque não autenticado;
    * a lista de ``intent_id`` é gravada atrelada ao digest que a produziu e só
      depois de a linha inteira passar pela mesma validação estrutural do
      caminho longo; provar o digest prova o parse.

    Indisponibilidade do índice (sem sqlite, disco cheio, base corrompida) não
    degrada o veredito: o objeto se desativa e todo acesso volta a ler e
    hashear os bytes vivos.
    """

    _CREATE_TABLE = (
        "CREATE TABLE IF NOT EXISTS file_snapshot ("
        "abs_path TEXT PRIMARY KEY, device INTEGER NOT NULL, "
        "inode INTEGER NOT NULL, size INTEGER NOT NULL, "
        "mtime_ns INTEGER NOT NULL, ctime_ns INTEGER NOT NULL, "
        "digest TEXT NOT NULL, intents TEXT)"
    )
    _UPSERT = (
        "INSERT INTO file_snapshot (abs_path, device, inode, size, mtime_ns, "
        "ctime_ns, digest, intents) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(abs_path) DO UPDATE SET device=excluded.device, "
        "inode=excluded.inode, size=excluded.size, "
        "mtime_ns=excluded.mtime_ns, ctime_ns=excluded.ctime_ns, "
        "digest=excluded.digest, intents=CASE "
        "WHEN excluded.intents IS NOT NULL THEN excluded.intents "
        "WHEN file_snapshot.digest = excluded.digest THEN file_snapshot.intents "
        "ELSE NULL END"
    )
    # A cláusula CASE existe porque dois produtores gravam o mesmo caminho: o
    # scan de estoque grava digest E intents, a reverificação de dependências
    # grava só digest. Sem ela, a segunda gravação apagaria o índice de intents
    # e o scan seguinte voltaria a reler o acervo inteiro. Preservar os intents
    # só quando o digest permanece idêntico é exato: eles são função pura dos
    # bytes, e digest igual significa exatamente os mesmos bytes; digest
    # diferente descarta o parse antigo.

    def __init__(
        self, database_path: pathlib.Path, repository_root: pathlib.Path,
    ) -> None:
        self._database_path = database_path
        # Só caminhos DENTRO do repositório são indexados. Fixtures de teste
        # vivem em diretórios temporários que somem no fim do processo; indexá-
        # los faria a base crescer para sempre com linhas que nunca mais serão
        # consultadas (38 delas já haviam se acumulado quando a guarda entrou).
        self._root_prefix = os.path.join(os.fspath(repository_root), "")
        self._connection: sqlite3.Connection | None = None
        self._disabled = os.environ.get("WIKI_V2_SNAPSHOT_INDEX") == "0"
        self._pending: list[tuple[Any, ...]] = []
        self._atexit_registered = False
        self._pruned = False

    def _disable(self) -> None:
        """Desliga o atalho e volta tudo a ler os bytes vivos.

        A conexão é apenas SOLTA, não fechada: ``close`` pode falhar de novo no
        mesmo estado que causou a desativação, e o SQLite já garante o que
        importa — ao finalizar a conexão, qualquer transação não commitada é
        desfeita. Nenhum dado do repositório depende desta base.
        """
        self._disabled = True
        self._pending.clear()
        self._connection = None

    def _open(self) -> sqlite3.Connection | None:
        if self._disabled:
            return None
        if self._connection is not None:
            return self._connection
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                os.fspath(self._database_path), timeout=10.0,
                isolation_level=None)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute(self._CREATE_TABLE)
        except (sqlite3.Error, OSError, ValueError):
            self._disable()
            return None
        self._connection = connection
        if not self._atexit_registered:
            atexit.register(self.flush)
            self._atexit_registered = True
        return connection

    @staticmethod
    def _stamp(info: os.stat_result) -> tuple[int, int, int, int, int]:
        return _stat_identity_stamp(info)

    def lookup(
        self, absolute: str, info: os.stat_result,
    ) -> tuple[str, tuple[str, ...] | None] | None:
        """Digest (e intents) já provados para ESTES bytes, ou ``None``."""
        connection = self._open()
        if connection is None:
            return None
        try:
            row = connection.execute(
                "SELECT device, inode, size, mtime_ns, ctime_ns, digest, "
                "intents FROM file_snapshot WHERE abs_path = ?",
                (absolute,),
            ).fetchone()
        except sqlite3.Error:
            self._disable()
            return None
        if row is None or tuple(row[:5]) != self._stamp(info):
            return None
        digest = row[5]
        if (not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            return None
        intents = row[6]
        if intents is None:
            return digest, None
        if not isinstance(intents, str) or "\n" not in intents:
            return None
        # A coluna guarda "<sha256 do resto>\n<intent>\n<intent>...". O re-hash
        # do EPOCH prova os BYTES do shard contra o digest, mas nunca rederiva
        # esta lista: sem o selo próprio, corrupção da coluna poderia encolher a
        # lista e deixar uma cópia do intent em outro shard passar pela prova de
        # unicidade global. Selo divergente é tratado como ausência de cache —
        # o shard volta a ser lido e decodificado por inteiro.
        seal, _, payload = intents.partition("\n")
        if (re.fullmatch(r"[0-9a-f]{64}", seal) is None or
                _sha256(payload.encode("utf-8")) != seal or not payload):
            return None
        parsed = tuple(payload.split("\n"))
        if any(_INTENT_ID.fullmatch(intent) is None for intent in parsed):
            return None
        return digest, parsed

    def store(
        self,
        absolute: str,
        info: os.stat_result,
        digest: str,
        intents: tuple[str, ...] | None = None,
    ) -> None:
        """Enfileira o carimbo provado; ``flush`` grava tudo numa transação."""
        if self._disabled or not absolute.startswith(self._root_prefix):
            return
        sealed_intents: str | None = None
        if intents is not None:
            payload = "\n".join(intents)
            sealed_intents = f"{_sha256(payload.encode('utf-8'))}\n{payload}"
        self._pending.append(
            (absolute, *self._stamp(info), digest, sealed_intents))
        if len(self._pending) >= 4096:
            self.flush()

    def flush(self) -> None:
        if not self._pending:
            return
        connection = self._open()
        if connection is None:
            return
        rows = self._pending
        self._pending = []
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.executemany(self._UPSERT, rows)
            if not self._pruned:
                # Uma varredura por processo, dentro de uma transação que já
                # estava acontecendo: descarta o que ficou de fora da árvore do
                # repositório antes da guarda de store existir.
                connection.execute(
                    "DELETE FROM file_snapshot WHERE substr(abs_path, 1, ?) <> ?",
                    (len(self._root_prefix), self._root_prefix))
                self._pruned = True
            connection.execute("COMMIT")
        except sqlite3.Error:
            # Soltar a conexão desfaz a transação aberta na finalização; tentar
            # um ROLLBACK explícito aqui só arriscaria um segundo erro sobre a
            # mesma base já degradada.
            self._disable()


def _snapshot_index() -> _PersistentSnapshotIndex:
    """Índice único do processo, ancorado na árvore do repositório."""
    global _SNAPSHOT_INDEX_SINGLETON
    if _SNAPSHOT_INDEX_SINGLETON is None:
        repository_root = pathlib.Path(__file__).resolve().parent.parent
        _SNAPSHOT_INDEX_SINGLETON = _PersistentSnapshotIndex(
            repository_root / _SNAPSHOT_INDEX_REL_PATH, repository_root)
    return _SNAPSHOT_INDEX_SINGLETON


def load_writing_semantic_contract(
    root: pathlib.Path | str,
) -> WritingSemanticContract:
    """Carrega requisitos de recorte e resolve somente página exata atestada.

    O ``intent_id`` e a presença de ``sections`` não provam que uma página
    anterior responde ao recorte atual do portfólio. Este sidecar registra a
    linha exata que mudou e mantém o intent bloqueado para ``complete``/``reuse``
    até uma resolução jurídico-editorial apontar para os bytes crus da nova
    página. Alterar posteriormente requisito, portfólio ou página invalida a
    resolução em vez de herdar uma aprovação por identidade nominal.
    ``superseded_target_rel_path`` localiza apenas a preimagem antiga;
    ``target_rel_path`` é o owner vigente onde a nova redação deve nascer.
    Owners ainda inexistentes integram o epoch como ausência autenticada.
    """
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    contract_path = canonical_root / _WRITING_SEMANTIC_CONTRACT_REL_PATH
    contract_snapshot = read_regular_file_snapshot(
        contract_path, max_bytes=_MAX_WRITING_SEMANTIC_CONTRACT_BYTES)
    if (not contract_snapshot.payload or
            not contract_snapshot.payload.endswith(b"\n")):
        raise ValueError("contrato semântico de escrita é vazio ou não terminado")
    value = decode_json_no_duplicate_keys(
        contract_snapshot.payload, "contrato semântico de escrita")
    schema_version = (value.get("_meta", {}).get("schema_version")
                      if isinstance(value, dict) and
                      isinstance(value.get("_meta"), dict) else None)
    expected_meta = {
        "schema_version": schema_version,
        "purpose": "block_reuse_until_exact_page_semantic_review",
        "requirements_sha256": _WRITING_SEMANTIC_REQUIREMENTS_SHA256,
        "index_policy": "noindex",
        "render_allowed": False,
        "sitemap_allowed": False,
        "publication_allowed": False,
    }
    expected_top_level = (
        {"_meta", "requirements", "resolutions"}
        if schema_version == "v2_writing_semantic_contract_v2" else
        {"_meta", "requirements", "forward_candidates",
         "adopt_existing_targets", "resolutions"}
        if schema_version == "v2_writing_semantic_contract_v3" else set()
    )
    if (not expected_top_level or not isinstance(value, dict) or
            set(value) != expected_top_level or
            value.get("_meta") != expected_meta or
            not isinstance(value.get("requirements"), list) or
            (schema_version == "v2_writing_semantic_contract_v3" and (
                not isinstance(value.get("forward_candidates"), list) or
                not isinstance(value.get("adopt_existing_targets"), list))) or
            not isinstance(value.get("resolutions"), list)):
        raise ValueError("contrato semântico de escrita perdeu schema fechado")

    requirement_fields = {
        "intent_id", "portfolio_rel_path", "portfolio_record_sha256",
        "target_rel_path", "superseded_target_rel_path",
        "superseded_page_record_sha256", "superseded_evidence_kind",
        "superseded_evidence_rel_path", "superseded_evidence_sha256",
        "reason", "required_review",
    }
    requirements: dict[str, Mapping[str, Any]] = {}
    requirement_fingerprints: dict[str, str] = {}
    observed_requirement_order: list[str] = []
    dependency_sha256: dict[str, str] = {}
    dependency_snapshots: dict[str, RegularFileSnapshot] = {}
    absent_dependency_paths: set[str] = set()
    dependency_bytes = len(contract_snapshot.payload)
    # Teto de snapshot proporcional ao estoque (stopgap de escala).
    # O contrato v3 autentica o estoque INTEIRO (cada shard entra no CAS em
    # 888-909), então o orçamento agregado não pode ser um teto fixo de 64 MB:
    # ele abortava com ValueError perto de ~12,7k páginas. Mantém-se o teto
    # original como headroom PURO das dependências não-estoque (contrato,
    # portfólios, evidência — a folga que o desenho já provou suficiente) e
    # soma-se o tamanho real do estoque em disco mais 25% de margem para
    # appends concorrentes. Novo orçamento >= antigo sempre: superset estrito
    # das entradas aceitas — nenhum veredito anti-fraude muda, só sobe o limiar
    # de abort por tamanho. O limite por-arquivo de 64 MB
    # (read_regular_file_snapshot) continua sendo a guarda fail-closed real. O
    # scan em memória que era o gargalo remanescente rumo a milhões foi
    # eliminado em 2026-08-04: o estoque não é mais lido nem retido por inteiro
    # a cada carga (ver o índice incremental abaixo), então o orçamento agregado
    # passou a ser contabilizado pelo tamanho em disco do shard carimbado, com o
    # mesmo teto e as mesmas mensagens de abort do caminho de leitura.
    snapshot_budget = _MAX_WRITING_SEMANTIC_SNAPSHOT_BYTES
    if schema_version == "v2_writing_semantic_contract_v3":
        stock_on_disk = 0
        for stock_path in (
                canonical_root / "data/editorial/v2_pages").glob("*.jsonl"):
            try:
                stock_on_disk += stock_path.stat().st_size
            except OSError as error:
                raise ValueError(
                    "estoque semântico ilegível durante orçamento: "
                    f"{stock_path}") from error
        snapshot_budget += stock_on_disk + (stock_on_disk >> 2)

    # Digest que entrou no CAS por carimbo de stat (índice incremental) sem que
    # os bytes tenham sido lidos nesta carga. Se o caminho longo reler o mesmo
    # arquivo depois — um shard de estoque também é target de requisito, por
    # exemplo — o digest real TEM de bater com o que já foi publicado em
    # dependency_sha256; divergir significa escrita concorrente no meio da
    # carga, e a carga aborta em vez de misturar duas épocas do mesmo arquivo.
    stat_pinned_digest: dict[str, str] = {}

    def budgeted_read_limit(rel_path: str, size: int, max_bytes: int) -> int:
        """Aplica o mesmo orçamento agregado do caminho de leitura."""
        remaining = snapshot_budget - dependency_bytes
        if remaining < 0:
            raise ValueError(
                "snapshot semântico excede orçamento agregado de "
                f"{snapshot_budget} bytes")
        read_limit = min(max_bytes, remaining)
        if size > read_limit:
            if read_limit < max_bytes:
                raise ValueError(
                    "snapshot semântico excede orçamento agregado de "
                    f"{snapshot_budget} bytes")
            raise ValueError(
                f"arquivo excede limite de {read_limit} bytes: {rel_path}")
        return read_limit

    def dependency(rel_path: str, *, max_bytes: int) -> RegularFileSnapshot:
        nonlocal dependency_bytes
        if rel_path in absent_dependency_paths:
            raise CASMismatch(
                f"dependência semântica apareceu durante leitura: {rel_path}")
        snapshot = dependency_snapshots.get(rel_path)
        if snapshot is None:
            remaining = snapshot_budget - dependency_bytes
            if remaining < 0:
                raise ValueError(
                    "snapshot semântico excede orçamento agregado de "
                    f"{snapshot_budget} bytes")
            read_limit = min(max_bytes, remaining)
            try:
                snapshot = read_regular_file_snapshot(
                    canonical_root / rel_path, max_bytes=read_limit)
            except ValueError as error:
                if read_limit < max_bytes:
                    raise ValueError(
                        "snapshot semântico excede orçamento agregado de "
                        f"{snapshot_budget} bytes"
                    ) from error
                raise
            pinned = stat_pinned_digest.get(rel_path)
            if pinned is not None and pinned != snapshot.digest:
                raise CASMismatch(
                    f"dependência semântica evoluiu durante a carga: {rel_path}")
            if rel_path not in dependency_sha256:
                dependency_bytes += len(snapshot.payload)
            dependency_snapshots[rel_path] = snapshot
            dependency_sha256[rel_path] = snapshot.digest
        return snapshot

    def capture_optional_dependency(rel_path: str, *, max_bytes: int) -> None:
        try:
            dependency(rel_path, max_bytes=max_bytes)
        except FileNotFoundError:
            absent_dependency_paths.add(rel_path)

    evidence_lines_by_path: dict[
        str, tuple[tuple[bytes, Mapping[str, Any]], ...]
    ] = {}

    def evidence_lines(
        rel_path: str,
    ) -> tuple[tuple[bytes, Mapping[str, Any]], ...]:
        cached = evidence_lines_by_path.get(rel_path)
        if cached is not None:
            return cached
        snapshot = dependency(
            rel_path, max_bytes=_MAX_WRITING_SEMANTIC_EVIDENCE_BYTES)
        if not snapshot.payload or not snapshot.payload.endswith(b"\n"):
            raise ValueError(
                f"evidência semântica vazia ou sem newline: {rel_path}")
        decoded: list[tuple[bytes, Mapping[str, Any]]] = []
        for line_number, raw_line in enumerate(
                snapshot.payload[:-1].split(b"\n"), 1):
            if not raw_line:
                raise ValueError(
                    f"evidência semântica contém linha vazia: "
                    f"{rel_path}:{line_number}")
            row = decode_json_no_duplicate_keys(
                raw_line, f"{rel_path}:{line_number}")
            if not isinstance(row, dict):
                raise ValueError(
                    f"evidência semântica não é objeto: "
                    f"{rel_path}:{line_number}")
            decoded.append((raw_line, row))
        cached = tuple(decoded)
        evidence_lines_by_path[rel_path] = cached
        return cached

    def authenticate_superseded_evidence(
        intent_id: str,
        requirement: Mapping[str, Any],
    ) -> None:
        rel_path = requirement["superseded_evidence_rel_path"]
        evidence_kind = requirement["superseded_evidence_kind"]
        evidence_sha256 = requirement["superseded_evidence_sha256"]
        baseline_name = pathlib.PurePosixPath(
            requirement["superseded_target_rel_path"]
        ).name
        lines = evidence_lines(rel_path)
        if evidence_kind == "archived_shard_snapshot":
            if rel_path != (
                    "data/editorial/v2_semantic_superseded/"
                    "writing-semantic-recuts-20260715.jsonl"):
                raise ValueError(
                    f"snapshot semântico usa archive inesperado: {intent_id}")
            meta = lines[0][1]
            expected_meta_fields = {
                "schema_version", "purpose", "checked_at",
                "source_rel_path", "source_sha256", "record_count",
                "index_policy", "render_allowed", "sitemap_allowed",
                "publication_allowed",
            }
            if (set(meta) != {"_meta"} or
                    not isinstance(meta.get("_meta"), dict) or
                    set(meta["_meta"]) != expected_meta_fields):
                raise ValueError("bundle semântico imobiliário perdeu schema")
            archive_meta = meta["_meta"]
            source_lines = tuple(raw for raw, _ in lines[1:])
            source_payload = b"\n".join(source_lines) + b"\n"
            if (archive_meta.get("schema_version") !=
                    "v2_semantic_superseded_evidence_v2" or
                    archive_meta.get("purpose") !=
                    "preserve_exact_shard_for_semantic_preimage_and_absence" or
                    archive_meta.get("checked_at") != "2026-07-15" or
                    archive_meta.get("source_rel_path") !=
                    requirement["superseded_target_rel_path"] or
                    not isinstance(archive_meta.get("source_sha256"), str) or
                    re.fullmatch(r"[0-9a-f]{64}",
                                 archive_meta["source_sha256"]) is None or
                    type(archive_meta.get("record_count")) is not int or
                    archive_meta["record_count"] != len(source_lines) or
                    archive_meta.get("index_policy") != "noindex" or
                    any(archive_meta.get(flag) is not False for flag in (
                        "render_allowed", "sitemap_allowed",
                        "publication_allowed",
                    )) or
                    _sha256(source_payload) != archive_meta["source_sha256"] or
                    evidence_sha256 != archive_meta["source_sha256"] or
                    pathlib.PurePosixPath(
                        archive_meta["source_rel_path"]
                    ).name != baseline_name):
                raise ValueError(
                    "bundle semântico imobiliário não recompõe o shard")
            matching_intents = [
                (raw_line, row) for raw_line, row in lines[1:]
                if row.get("intent_id") == intent_id
            ]
            superseded_sha256 = requirement[
                "superseded_page_record_sha256"]
            if superseded_sha256 is None:
                if matching_intents:
                    raise ValueError(
                        f"evidência de ausência semântica inválida: {intent_id}")
                return
            if (len(matching_intents) != 1 or
                    _sha256(matching_intents[0][0]) != superseded_sha256):
                raise ValueError(
                    f"preimagem semântica imobiliária inválida: {intent_id}")
            return

        if (evidence_kind != "duplicate_supersession_record" or
                rel_path != (
                    "data/editorial/v2_superseded/"
                    "duplicate-intent-consolidation-2026-07-15.jsonl")):
            raise ValueError(
                f"tipo/path de evidência semântica inválido: {intent_id}")
        matches = [
            (raw_line, row) for raw_line, row in lines
            if _sha256(raw_line) == evidence_sha256
        ]
        superseded_sha256 = requirement["superseded_page_record_sha256"]
        if (len(matches) != 1 or superseded_sha256 is None):
            raise ValueError(
                f"evidência de supersessão não é única: {intent_id}")
        _, row = matches[0]
        original_line = row.get("original_line")
        if (row.get("record_type") !=
                "v2_duplicate_intent_supersession" or
                row.get("intent_id") != intent_id or
                row.get("source_shard") != baseline_name or
                row.get("source_record_sha256") != superseded_sha256 or
                not isinstance(original_line, str) or
                _sha256(original_line.encode("utf-8")) !=
                superseded_sha256 or
                row.get("index_policy") != "noindex" or
                any(row.get(flag) is not False for flag in (
                    "render_allowed", "sitemap_allowed",
                    "publication_allowed",
                ))):
            raise ValueError(
                f"archive não autentica preimagem semântica: {intent_id}")

    portfolio_raw_by_path: dict[str, dict[str, list[bytes]]] = {}
    used_evidence: set[tuple[str, str]] = set()
    for index, requirement in enumerate(value["requirements"], 1):
        label = f"requisito semântico {index}"
        if (not isinstance(requirement, dict) or
                set(requirement) != requirement_fields):
            raise ValueError(f"{label}: schema aberto ou incompleto")
        intent_id = requirement.get("intent_id")
        portfolio_rel_path = requirement.get("portfolio_rel_path")
        portfolio_record_sha256 = requirement.get("portfolio_record_sha256")
        target_rel_path = requirement.get("target_rel_path")
        superseded_target_rel_path = requirement.get(
            "superseded_target_rel_path")
        superseded_page_sha256 = requirement.get(
            "superseded_page_record_sha256")
        superseded_evidence_kind = requirement.get(
            "superseded_evidence_kind")
        superseded_evidence_rel_path = requirement.get(
            "superseded_evidence_rel_path")
        superseded_evidence_sha256 = requirement.get(
            "superseded_evidence_sha256")
        if (not isinstance(intent_id, str) or
                _INTENT_ID.fullmatch(intent_id) is None or
                intent_id in requirements or
                not isinstance(portfolio_rel_path, str) or
                _PORTFOLIO_REL_PATH.fullmatch(portfolio_rel_path) is None or
                not isinstance(portfolio_record_sha256, str) or
                re.fullmatch(r"[0-9a-f]{64}", portfolio_record_sha256) is None or
                not isinstance(target_rel_path, str) or
                _TARGET_REL_PATH.fullmatch(target_rel_path) is None or
                not isinstance(superseded_target_rel_path, str) or
                _TARGET_REL_PATH.fullmatch(superseded_target_rel_path)
                is None or
                superseded_evidence_kind not in {
                    "duplicate_supersession_record",
                    "archived_shard_snapshot",
                } or
                superseded_evidence_rel_path not in
                _WRITING_SEMANTIC_EVIDENCE_PATHS or
                not isinstance(superseded_evidence_sha256, str) or
                re.fullmatch(r"[0-9a-f]{64}",
                             superseded_evidence_sha256) is None or
                (superseded_page_sha256 is not None and (
                    not isinstance(superseded_page_sha256, str) or
                    re.fullmatch(r"[0-9a-f]{64}", superseded_page_sha256)
                    is None)) or
                requirement.get("reason") !=
                "portfolio_semantics_changed_after_page_review" or
                requirement.get("required_review") !=
                "codex_legal_editorial_semantic_exact_page"):
            raise ValueError(f"{label}: identidade/política não canônica")
        observed_requirement_order.append(intent_id)
        requirements[intent_id] = requirement
        requirement_fingerprints[intent_id] = (
            _semantic_contract_fingerprint(requirement))
        if superseded_evidence_kind == "duplicate_supersession_record":
            evidence_key = (
                superseded_evidence_rel_path, superseded_evidence_sha256
            )
            if evidence_key in used_evidence:
                raise ValueError(
                    f"evidência semântica foi reutilizada: {intent_id}")
            used_evidence.add(evidence_key)
        authenticate_superseded_evidence(intent_id, requirement)
        # O owner atual pode ainda não existir. A ausência também integra o
        # epoch: se o shard aparecer antes do CAS, a reautenticação reprova.
        capture_optional_dependency(
            target_rel_path, max_bytes=64 * 1024 * 1024)
        if superseded_target_rel_path != target_rel_path:
            capture_optional_dependency(
                superseded_target_rel_path, max_bytes=64 * 1024 * 1024)

        raw_by_intent = portfolio_raw_by_path.get(portfolio_rel_path)
        if raw_by_intent is None:
            portfolio = dependency(
                portfolio_rel_path, max_bytes=64 * 1024 * 1024)
            if (not portfolio.payload or
                    not portfolio.payload.endswith(b"\n")):
                raise ValueError(
                    f"portfolio de requisito não termina com newline: "
                    f"{portfolio_rel_path}")
            raw_by_intent = collections.defaultdict(list)
            for line_number, raw_line in enumerate(
                    portfolio.payload[:-1].split(b"\n"), 1):
                record = decode_json_no_duplicate_keys(
                    raw_line, f"{portfolio_rel_path}:{line_number}")
                if not isinstance(record, dict):
                    raise ValueError(
                        f"portfolio de requisito não é objeto: "
                        f"{portfolio_rel_path}:{line_number}")
                row_intent = record.get("intent_id")
                if (not isinstance(row_intent, str) or
                        _INTENT_ID.fullmatch(row_intent) is None):
                    raise ValueError(
                        f"portfolio de requisito sem intent canônico: "
                        f"{portfolio_rel_path}:{line_number}")
                raw_by_intent[row_intent].append(raw_line)
            portfolio_raw_by_path[portfolio_rel_path] = raw_by_intent
        matched = raw_by_intent.get(intent_id, [])
        if len(matched) != 1 or _sha256(matched[0]) != portfolio_record_sha256:
            raise ValueError(
                f"requisito semântico stale no portfolio: {intent_id}")

    if (not requirements or
            observed_requirement_order != sorted(observed_requirement_order)):
        raise ValueError(
            "requisitos semânticos devem ser não vazios, únicos e ordenados")
    requirements_sha256 = _sha256(json.dumps(
        value["requirements"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8"))
    if requirements_sha256 != _WRITING_SEMANTIC_REQUIREMENTS_SHA256:
        raise ValueError(
            "conjunto-base de requisitos semânticos foi removido ou alterado")

    sha256_pattern = re.compile(r"[0-9a-f]{64}")
    material_fields = {
        "contract", "visible_text_sha256", "official_sources_sha256",
        "computed_word_count",
    }

    def validate_material_binding(
        claimed: Any, page: Mapping[str, Any], label: str,
    ) -> None:
        if (not isinstance(claimed, dict) or set(claimed) != material_fields or
                claimed != _semantic_page_material_evidence(page, label)):
            raise ValueError(f"{label}: evidência material não é recomputável")

    def validate_internal_page(page: Mapping[str, Any], label: str) -> None:
        if (page.get("index_policy", "noindex") != "noindex" or
                any(page.get(flag, False) is not False for flag in (
                    "render_allowed", "sitemap_allowed",
                    "publication_allowed"))):
            raise ValueError(f"{label}: candidato não permanece interno")

    # O epoch v3 autentica o estoque inteiro: um claim de bytes alterados não
    # pode ocultar uma segunda cópia do intent em outro shard. Cada arquivo
    # entra no dependency CAS, inclusive os que não contêm requisito.
    #
    # Escala (2026-08-04): o laço lia e redecodificava os 855 shards / 52,3 MB a
    # CADA carga do contrato, e a carga acontece uma vez por lote promovido —
    # 960 ms por lote medidos, ~28 min só de re-scan para drenar o acervo e
    # ~47 h projetadas em 100k páginas. Todo esse trabalho servia a três
    # produtos: (a) o digest de cada shard para o dependency CAS, (b) a prova de
    # unicidade GLOBAL de cada intent do estoque e (c) as linhas cruas dos
    # intents citados por candidatos forward e adoções — 13 no contrato vivo,
    # contra 9.742 linhas decodificadas.
    #
    # (a) e (b) passaram a sair do índice incremental persistido
    # (caminho -> digest + intent_ids em ordem de linha, revalidado por
    # dev/ino/tamanho/mtime_ns/ctime_ns); (c) materializa sob demanda lendo
    # APENAS o shard dono do intent consultado. O conjunto de dependências e os
    # digests entregues são idênticos aos do caminho longo, o epoch continua
    # cobrindo o estoque inteiro, e _assert_dependency_epoch segue relendo e
    # re-hasheando cada arquivo antes de qualquer escrita — ver
    # _PersistentSnapshotIndex para o argumento de integridade completo.
    stock_owner_index: dict[str, list[str]] = collections.defaultdict(list)
    stock_row_cache: dict[str, list[tuple[str, bytes, Mapping[str, Any]]]] = {}

    def stock_shard_lines(
        rel_path: str, payload: bytes,
    ) -> list[tuple[int, bytes, Mapping[str, Any], str]]:
        """Valida e decodifica um shard de estoque com o rigor do caminho longo."""
        if not payload or not payload.endswith(b"\n"):
            raise ValueError(f"estoque semântico inválido: {rel_path}")
        decoded: list[tuple[int, bytes, Mapping[str, Any], str]] = []
        for line_number, raw_line in enumerate(payload[:-1].split(b"\n"), 1):
            if not raw_line:
                raise ValueError(
                    f"estoque semântico contém linha vazia: "
                    f"{rel_path}:{line_number}")
            page = decode_json_no_duplicate_keys(
                raw_line, f"{rel_path}:{line_number}")
            intent_id = page.get("intent_id") if isinstance(page, dict) else None
            if (not isinstance(intent_id, str) or
                    _INTENT_ID.fullmatch(intent_id) is None):
                raise ValueError(
                    f"estoque semântico sem intent canônico: "
                    f"{rel_path}:{line_number}")
            decoded.append((line_number, raw_line, page, intent_id))
        return decoded

    def stock_shard_intents(
        rel_path: str, stock_path: pathlib.Path, index: _PersistentSnapshotIndex,
    ) -> tuple[str, ...]:
        """Intents do shard, na ordem das linhas, relendo só o que mudou."""
        nonlocal dependency_bytes
        # O caminho longo chamava dependency() para TODO shard, e a primeira
        # coisa que dependency() faz é reprovar um path registrado como ausente
        # que reapareceu no disco. O atalho por carimbo não pode pular essa
        # guarda: um owner declarado ausente (target de requisito ainda
        # inexistente) que ressurja durante o scan tem de abortar a carga.
        if rel_path in absent_dependency_paths:
            raise CASMismatch(
                f"dependência semântica apareceu durante leitura: {rel_path}")
        absolute = os.fspath(stock_path)
        before: os.stat_result | None = None
        if rel_path not in dependency_snapshots:
            try:
                before = os.stat(stock_path)
            except OSError:
                before = None
            if before is not None and stat.S_ISREG(before.st_mode):
                cached = index.lookup(absolute, before)
                if cached is not None and cached[1] is not None:
                    budgeted_read_limit(
                        rel_path, before.st_size, 64 * 1024 * 1024)
                    if rel_path not in dependency_sha256:
                        dependency_bytes += before.st_size
                    dependency_sha256[rel_path] = cached[0]
                    stat_pinned_digest[rel_path] = cached[0]
                    return cached[1]
            else:
                before = None
        snapshot = dependency(rel_path, max_bytes=64 * 1024 * 1024)
        intents = tuple(
            line[3] for line in stock_shard_lines(rel_path, snapshot.payload))
        if before is not None:
            try:
                after = os.stat(stock_path)
            except OSError:
                after = None
            # Só se grava carimbo cujo stat cerca a leitura sem variação: o
            # digest gravado tem de descrever exatamente os bytes carimbados.
            if (after is not None and
                    _stat_identity_stamp(after) ==
                    _stat_identity_stamp(before)):
                index.store(absolute, after, snapshot.digest, intents)
        return intents

    def stock_rows_for(
        intent_id: str,
    ) -> list[tuple[str, bytes, Mapping[str, Any]]]:
        """Linhas cruas do intent no estoque, lendo apenas os shards donos."""
        cached_rows = stock_row_cache.get(intent_id)
        if cached_rows is not None:
            return cached_rows
        materialized: list[tuple[str, bytes, Mapping[str, Any]]] = []
        # dict.fromkeys preserva a ordem de shard do glob ordenado e evita
        # reler o mesmo shard quando ele hospeda o intent mais de uma vez.
        for rel_path in dict.fromkeys(stock_owner_index.get(intent_id, ())):
            snapshot = dependency(rel_path, max_bytes=64 * 1024 * 1024)
            materialized.extend(
                (rel_path, raw_line, page)
                for _, raw_line, page, line_intent
                in stock_shard_lines(rel_path, snapshot.payload)
                if line_intent == intent_id
            )
        stock_row_cache[intent_id] = materialized
        return materialized

    if schema_version == "v2_writing_semantic_contract_v3":
        pages_root = canonical_root / "data/editorial/v2_pages"
        snapshot_index = _snapshot_index()
        for stock_path in sorted(pages_root.glob("*.jsonl")):
            rel_path = stock_path.relative_to(canonical_root).as_posix()
            for intent_id in stock_shard_intents(
                    rel_path, stock_path, snapshot_index):
                stock_owner_index[intent_id].append(rel_path)
        snapshot_index.flush()

    forward_fields = {
        "intent_id", "requirement_sha256", "archived_page_record_sha256",
        "current_source_rel_path", "current_source_record_sha256",
        "target_rel_path", "observed_at", "observed_by", "status",
        "material_validation", "index_policy", "render_allowed",
        "sitemap_allowed", "publication_allowed",
    }
    forward_intents: set[str] = set()
    observed_forward_order: list[str] = []
    for index, candidate in enumerate(value.get("forward_candidates", []), 1):
        label = f"candidato semântico forward {index}"
        if not isinstance(candidate, dict) or set(candidate) != forward_fields:
            raise ValueError(f"{label}: schema aberto ou incompleto")
        intent_id = candidate.get("intent_id")
        requirement = requirements.get(intent_id)
        archived_sha256 = candidate.get("archived_page_record_sha256")
        current_sha256 = candidate.get("current_source_record_sha256")
        if (requirement is None or intent_id in forward_intents or
                candidate.get("requirement_sha256") !=
                requirement_fingerprints.get(intent_id) or
                candidate.get("current_source_rel_path") !=
                requirement["superseded_target_rel_path"] or
                candidate.get("target_rel_path") !=
                requirement["target_rel_path"] or
                archived_sha256 !=
                requirement["superseded_page_record_sha256"] or
                not isinstance(current_sha256, str) or
                sha256_pattern.fullmatch(current_sha256) is None or
                (archived_sha256 is not None and
                 current_sha256 == archived_sha256) or
                candidate.get("status") != "internal_review_pending" or
                candidate.get("index_policy") != "noindex" or
                any(candidate.get(flag) is not False for flag in (
                    "render_allowed", "sitemap_allowed",
                    "publication_allowed")) or
                not isinstance(candidate.get("observed_by"), str) or
                _INTENT_ID.fullmatch(candidate["observed_by"]) is None):
            raise ValueError(f"{label}: identidade/política não canônica")
        try:
            observed_date = datetime.date.fromisoformat(candidate["observed_at"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label}: data de observação inválida") from error
        if (candidate["observed_at"] != observed_date.isoformat() or
                observed_date > _utc_validation_date()):
            raise ValueError(f"{label}: data de observação inválida ou futura")
        matches = stock_rows_for(intent_id)
        if (len(matches) != 1 or matches[0][0] !=
                candidate["current_source_rel_path"] or
                _sha256(matches[0][1]) != current_sha256):
            raise ValueError(
                f"{label}: owner atual não é globalmente exato e único")
        validate_internal_page(matches[0][2], label)
        validate_material_binding(
            candidate.get("material_validation"), matches[0][2], label)
        observed_forward_order.append(intent_id)
        forward_intents.add(intent_id)
    if observed_forward_order != sorted(observed_forward_order):
        raise ValueError("candidatos semânticos forward devem ser únicos e ordenados")

    adoption_fields = {
        "intent_id", "transition_kind", "requirement_sha256",
        "archived_page_record_sha256", "source_rel_path",
        "source_record_state", "target_rel_path",
        "target_page_record_sha256", "reviewed_at", "reviewed_by",
        "review_contract", "semantic_review_evidence",
        "material_validation", "verdict", "index_policy", "render_allowed",
        "sitemap_allowed", "publication_allowed",
    }
    semantic_evidence_fields = {
        "requirement_sha256", "page_record_sha256", "review_dimensions",
        "finding",
    }
    adopted: set[str] = set()
    observed_adoption_order: list[str] = []
    for index, adoption in enumerate(value.get("adopt_existing_targets", []), 1):
        label = f"adoção semântica {index}"
        if not isinstance(adoption, dict) or set(adoption) != adoption_fields:
            raise ValueError(f"{label}: schema aberto ou incompleto")
        intent_id = adoption.get("intent_id")
        requirement = requirements.get(intent_id)
        target_sha256 = adoption.get("target_page_record_sha256")
        transition = adoption.get("transition_kind")
        is_adoption = bool(requirement) and (
            transition == "adopt_existing_target" and
            adoption.get("archived_page_record_sha256") is None and
            requirement["superseded_page_record_sha256"] is None and
            adoption.get("source_record_state") == "absent" and
            adoption.get("source_rel_path") != adoption.get("target_rel_path"))
        is_affirmation = bool(requirement) and (
            transition == "affirm_existing_owner" and
            adoption.get("archived_page_record_sha256") ==
            requirement["superseded_page_record_sha256"] and
            adoption.get("archived_page_record_sha256") is not None and
            adoption.get("source_record_state") == "exact_reviewed" and
            adoption.get("source_rel_path") == adoption.get("target_rel_path") and
            target_sha256 == adoption.get("archived_page_record_sha256"))
        if (requirement is None or intent_id in adopted or
                intent_id in forward_intents or
                adoption.get("requirement_sha256") !=
                requirement_fingerprints.get(intent_id) or
                not (is_adoption or is_affirmation) or
                adoption.get("source_rel_path") !=
                requirement["superseded_target_rel_path"] or
                adoption.get("target_rel_path") != requirement["target_rel_path"] or
                not isinstance(target_sha256, str) or
                sha256_pattern.fullmatch(target_sha256) is None or
                not isinstance(adoption.get("reviewed_by"), str) or
                _INTENT_ID.fullmatch(adoption["reviewed_by"]) is None or
                adoption.get("review_contract") !=
                _WRITING_SEMANTIC_REVIEW_CONTRACT or
                adoption.get("verdict") !=
                "portfolio_requirement_satisfied" or
                adoption.get("index_policy") != "noindex" or
                any(adoption.get(flag) is not False for flag in (
                    "render_allowed", "sitemap_allowed",
                    "publication_allowed"))):
            raise ValueError(f"{label}: identidade/revisão não canônica")
        try:
            reviewed_date = datetime.date.fromisoformat(adoption["reviewed_at"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label}: data de revisão inválida") from error
        if (adoption["reviewed_at"] != reviewed_date.isoformat() or
                reviewed_date > _utc_validation_date()):
            raise ValueError(f"{label}: data de revisão inválida ou futura")
        expected_finding = (
            "current_portfolio_requirement_satisfied_by_fresh_exact_owner_affirmation"
            if is_affirmation else
            "current_portfolio_requirement_satisfied_by_exact_existing_target")
        expected_evidence = {
            "requirement_sha256": requirement_fingerprints[intent_id],
            "page_record_sha256": target_sha256,
            "review_dimensions": [
                "legal_scope", "current_rule", "user_question",
                "distinction_from_superseded",
            ],
            "finding": expected_finding,
        }
        if (not isinstance(adoption.get("semantic_review_evidence"), dict) or
                set(adoption["semantic_review_evidence"]) !=
                semantic_evidence_fields or
                adoption["semantic_review_evidence"] != expected_evidence):
            raise ValueError(f"{label}: evidência semântica não canônica")
        matches = stock_rows_for(intent_id)
        if (len(matches) != 1 or matches[0][0] != adoption["target_rel_path"] or
                _sha256(matches[0][1]) != target_sha256):
            raise ValueError(f"{label}: target não é globalmente exato e único")
        validate_internal_page(matches[0][2], label)
        validate_material_binding(
            adoption.get("material_validation"), matches[0][2], label)
        observed_adoption_order.append(intent_id)
        adopted.add(intent_id)
    if observed_adoption_order != sorted(observed_adoption_order):
        raise ValueError("adoções semânticas devem ser únicas e ordenadas")

    resolution_fields = {
        "intent_id", "requirement_sha256", "target_rel_path",
        "page_record_sha256", "reviewed_at", "reviewed_by",
        "review_contract", "semantic_review_evidence",
        "material_validation", "verdict",
    }
    resolved: set[str] = set()
    observed_resolution_order: list[str] = []
    target_rows_by_path: dict[str, dict[str, list[tuple[bytes, Mapping[str, Any]]]]] = {}

    def target_rows(
        target_rel_path: str,
    ) -> dict[str, list[tuple[bytes, Mapping[str, Any]]]]:
        rows = target_rows_by_path.get(target_rel_path)
        if rows is not None:
            return rows
        target = dependency(target_rel_path, max_bytes=64 * 1024 * 1024)
        if not target.payload or not target.payload.endswith(b"\n"):
            raise ValueError(
                "target de requisito semântico é vazio ou sem newline: "
                f"{target_rel_path}")
        rows = collections.defaultdict(list)
        for line_number, raw_line in enumerate(
                target.payload[:-1].split(b"\n"), 1):
            if not raw_line:
                raise ValueError(
                    f"target de requisito contém linha vazia: "
                    f"{target_rel_path}:{line_number}")
            record = decode_json_no_duplicate_keys(
                raw_line, f"{target_rel_path}:{line_number}")
            if not isinstance(record, dict):
                raise ValueError(
                    f"target de requisito não é objeto: "
                    f"{target_rel_path}:{line_number}")
            row_intent = record.get("intent_id")
            if (not isinstance(row_intent, str) or
                    _INTENT_ID.fullmatch(row_intent) is None):
                raise ValueError(
                    f"target de requisito sem intent canônico: "
                    f"{target_rel_path}:{line_number}")
            rows[row_intent].append((raw_line, record))
        target_rows_by_path[target_rel_path] = rows
        return rows

    for index, resolution in enumerate(value["resolutions"], 1):
        label = f"resolução semântica {index}"
        if (not isinstance(resolution, dict) or
                set(resolution) != resolution_fields):
            raise ValueError(f"{label}: schema aberto ou incompleto")
        intent_id = resolution.get("intent_id")
        requirement = requirements.get(intent_id)
        target_rel_path = resolution.get("target_rel_path")
        page_record_sha256 = resolution.get("page_record_sha256")
        if (requirement is None or intent_id in resolved or
                intent_id in adopted or intent_id in forward_intents or
                not isinstance(target_rel_path, str) or
                target_rel_path != requirement["target_rel_path"] or
                not isinstance(page_record_sha256, str) or
                re.fullmatch(r"[0-9a-f]{64}", page_record_sha256) is None or
                resolution.get("requirement_sha256") !=
                requirement_fingerprints[intent_id] or
                not isinstance(resolution.get("reviewed_at"), str) or
                re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                             resolution["reviewed_at"]) is None or
                not isinstance(resolution.get("reviewed_by"), str) or
                _INTENT_ID.fullmatch(resolution["reviewed_by"]) is None or
                resolution.get("review_contract") !=
                _WRITING_SEMANTIC_REVIEW_CONTRACT or
                resolution.get("verdict") !=
                "portfolio_requirement_satisfied"):
            raise ValueError(f"{label}: identidade/revisão não canônica")
        try:
            reviewed_date = datetime.date.fromisoformat(
                resolution["reviewed_at"])
        except ValueError as error:
            raise ValueError(f"{label}: data de revisão inválida") from error
        if reviewed_date > _utc_validation_date():
            raise ValueError(f"{label}: data de revisão está no futuro")
        if (requirement["superseded_page_record_sha256"] is not None and
                page_record_sha256 ==
                requirement["superseded_page_record_sha256"]):
            raise ValueError(
                f"resolução reutiliza página semanticamente superada: {intent_id}")
        observed_resolution_order.append(intent_id)

        matched_rows = target_rows(target_rel_path).get(intent_id, [])
        if len(matched_rows) != 1:
            raise ValueError(
                f"resolução não encontra página exata única: {intent_id}")
        raw_line, page = matched_rows[0]
        if _sha256(raw_line) != page_record_sha256:
            raise ValueError(
                f"resolução não autentica bytes exatos da página: {intent_id}")
        semantic_evidence = {
            "requirement_sha256": requirement_fingerprints[intent_id],
            "page_record_sha256": page_record_sha256,
            "review_dimensions": [
                "legal_scope", "current_rule", "user_question",
                "distinction_from_superseded",
            ],
            "finding": "current_portfolio_requirement_satisfied_by_exact_page",
        }
        if resolution.get("semantic_review_evidence") != semantic_evidence:
            raise ValueError(
                f"resolução sem evidência semântica fechada: {intent_id}")
        material_evidence = _semantic_page_material_evidence(
            page, f"resolução semântica {intent_id}")
        if resolution.get("material_validation") != material_evidence:
            raise ValueError(
                f"resolução sem evidência material recomputável: {intent_id}")
        resolved.add(intent_id)

    if observed_resolution_order != sorted(observed_resolution_order):
        raise ValueError("resoluções semânticas devem ser únicas e ordenadas")

    relocation_rows_by_path: dict[str, dict[str, list[bytes]]] = {}

    def relocation_rows(rel_path: str) -> dict[str, list[bytes]]:
        cached = relocation_rows_by_path.get(rel_path)
        if cached is not None:
            return cached
        rows: dict[str, list[bytes]] = collections.defaultdict(list)
        if rel_path in absent_dependency_paths:
            relocation_rows_by_path[rel_path] = rows
            return rows
        snapshot = dependency(rel_path, max_bytes=64 * 1024 * 1024)
        if not snapshot.payload or not snapshot.payload.endswith(b"\n"):
            raise ValueError(
                f"target antigo de relocação é vazio ou sem newline: {rel_path}")
        for line_number, raw_line in enumerate(
                snapshot.payload[:-1].split(b"\n"), 1):
            if not raw_line:
                raise ValueError(
                    f"target antigo contém linha vazia: "
                    f"{rel_path}:{line_number}")
            record = decode_json_no_duplicate_keys(
                raw_line, f"{rel_path}:{line_number}")
            if not isinstance(record, dict):
                raise ValueError(
                    f"target antigo não é objeto: {rel_path}:{line_number}")
            row_intent = record.get("intent_id")
            if (not isinstance(row_intent, str) or
                    _INTENT_ID.fullmatch(row_intent) is None):
                raise ValueError(
                    f"target antigo sem intent canônico: "
                    f"{rel_path}:{line_number}")
            rows[row_intent].append(raw_line)
        relocation_rows_by_path[rel_path] = rows
        return rows

    for intent_id, requirement in requirements.items():
        old_target = requirement["superseded_target_rel_path"]
        if old_target == requirement["target_rel_path"]:
            continue
        matches = relocation_rows(old_target).get(intent_id, [])
        superseded_sha256 = requirement["superseded_page_record_sha256"]
        if superseded_sha256 is None:
            if matches:
                raise ValueError(
                    "ausência arquivada reapareceu no target antigo: "
                    f"{intent_id}")
            continue
        if intent_id in resolved or intent_id in adopted:
            if matches:
                raise ValueError(
                    "relocação semântica resolvida permaneceu no target antigo: "
                    f"{intent_id}")
            continue
        expected_live_sha256 = (
            next(candidate["current_source_record_sha256"]
                 for candidate in value.get("forward_candidates", [])
                 if candidate["intent_id"] == intent_id)
            if intent_id in forward_intents else superseded_sha256
        )
        if (len(matches) != 1 or
                _sha256(matches[0]) != expected_live_sha256):
            raise ValueError(
                "preimagem de relocação saiu antes da resolução exata: "
                f"{intent_id}")
    return WritingSemanticContract(
        digest=contract_snapshot.digest,
        unresolved_intents=frozenset(set(requirements) - resolved - adopted),
        requirement_fingerprints=requirement_fingerprints,
        portfolio_rel_paths={
            intent_id: requirement["portfolio_rel_path"]
            for intent_id, requirement in requirements.items()
        },
        target_rel_paths={
            intent_id: requirement["target_rel_path"]
            for intent_id, requirement in requirements.items()
        },
        superseded_target_rel_paths={
            intent_id: requirement["superseded_target_rel_path"]
            for intent_id, requirement in requirements.items()
        },
        superseded_page_record_sha256={
            intent_id: requirement["superseded_page_record_sha256"]
            for intent_id, requirement in requirements.items()
        },
        evidence_kinds={
            intent_id: requirement["superseded_evidence_kind"]
            for intent_id, requirement in requirements.items()
        },
        evidence_rel_paths={
            intent_id: requirement["superseded_evidence_rel_path"]
            for intent_id, requirement in requirements.items()
        },
        evidence_sha256={
            intent_id: requirement["superseded_evidence_sha256"]
            for intent_id, requirement in requirements.items()
        },
        dependency_sha256=dependency_sha256,
        absent_dependency_paths=frozenset(absent_dependency_paths),
    )


_DEPENDENCY_DIGEST_STAT_CACHE: dict[str, tuple[tuple, str]] = {}


def _stat_cached_snapshot_sha256(path: pathlib.Path, max_bytes: int) -> str:
    """snapshot_sha256 com atalho por stat (tamanho, mtime_ns, inode).

    Mesmo padrão já sancionado em generate-v2-shard-slice-reorder
    (``_semantic_contract_epoch``) para o contrato inteiro; aqui aplicado por
    arquivo dentro da reverificação de dependências. Drift real — escrita
    concorrente, shard novo/removido, até a própria escrita do processo via
    atomic-replace (troca de inode) — muda o stat e força o re-hash: mesma
    garantia fail-closed de snapshot_sha256, só sem pagar leitura+SHA256 de
    novo quando nada mudou desde a última vez que este processo hasheou o
    arquivo.
    """
    cache_key = str(path)
    try:
        info = path.stat()
    except OSError:
        _DEPENDENCY_DIGEST_STAT_CACHE.pop(cache_key, None)
        return snapshot_sha256(path, max_bytes=max_bytes)
    stamp = (info.st_size, info.st_mtime_ns, info.st_ino)
    cached = _DEPENDENCY_DIGEST_STAT_CACHE.get(cache_key)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    # Cada lote de promoção roda em processo NOVO: o memo acima nasce vazio e a
    # reverificação relia e re-hasheava o estoque inteiro (218 ms medidos por
    # processo frio em 855 shards). O índice persistido responde o mesmo digest
    # sob carimbo estritamente mais estrito, e continua sendo só um atalho —
    # _assert_dependency_epoch relê os bytes antes de qualquer escrita.
    absolute = os.path.abspath(cache_key)
    index = _snapshot_index()
    persisted = index.lookup(absolute, info)
    if persisted is not None:
        _DEPENDENCY_DIGEST_STAT_CACHE[cache_key] = (stamp, persisted[0])
        return persisted[0]
    digest = snapshot_sha256(path, max_bytes=max_bytes)
    try:
        after = path.stat()
    except OSError:
        after = None
    if after is not None and _stat_identity_stamp(after) == _stat_identity_stamp(info):
        # Sem flush por chamada: o lote acumula e desce numa transação só
        # (limite interno ou atexit), senão um processo frio abriria uma
        # transação por dependência.
        index.store(absolute, after, digest)
    _DEPENDENCY_DIGEST_STAT_CACHE[cache_key] = (stamp, digest)
    return digest


def verify_writing_semantic_contract_dependencies(
    root: pathlib.Path | str,
    contract: WritingSemanticContract,
) -> None:
    """Reautentica o sidecar e os bytes que sustentaram suas decisões.

    O laço de lotes de relaunch-writing.sh chama esta função uma vez por
    lote (~700+) sobre o MESMO contrato: sem atalho, cada chamada relia e
    re-hasheava as 731 dependências / 42 MB do estoque inteiro (achado
    2026-07-30, ~0,5-0,8s cada, ~O(lotes × estoque) no total — sozinho
    esgotava o orçamento de tempo do produtor). O atalho por stat abaixo
    preserva a mesma reautenticação fail-closed contra os bytes vivos.
    """
    if not isinstance(contract, WritingSemanticContract):
        raise TypeError("contrato semântico de escrita inválido")
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    if _stat_cached_snapshot_sha256(
            canonical_root / _WRITING_SEMANTIC_CONTRACT_REL_PATH,
            _MAX_WRITING_SEMANTIC_CONTRACT_BYTES) != contract.digest:
        raise CASMismatch("contrato semântico de escrita evoluiu")
    for rel_path, expected_digest in contract.dependency_sha256.items():
        max_bytes = 64 * 1024 * 1024
        if _stat_cached_snapshot_sha256(
                canonical_root / rel_path, max_bytes) != expected_digest:
            raise CASMismatch(
                f"dependência do contrato semântico evoluiu: {rel_path}")
    if (set(contract.absent_dependency_paths) &
            set(contract.dependency_sha256)):
        raise ValueError(
            "dependência semântica não pode ser presente e ausente"
        )
    for rel_path in contract.absent_dependency_paths:
        if (not isinstance(rel_path, str) or
                _TARGET_REL_PATH.fullmatch(rel_path) is None):
            raise ValueError("dependência semântica ausente tem path inválido")
        try:
            read_regular_file_snapshot(
                canonical_root / rel_path, max_bytes=64 * 1024 * 1024)
        except FileNotFoundError:
            continue
        raise CASMismatch(
            f"dependência ausente do contrato semântico apareceu: {rel_path}")


def writing_promotion_dependency_epoch(
    root: pathlib.Path | str,
    contract: WritingSemanticContract,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    source_catalog_rel_path: str,
    source_catalog_sha256: str,
    raw_recovery_preimage_evidence: Mapping[str, Any] | None = None,
) -> Mapping[pathlib.Path, str | None]:
    """Materializa o epoch multi-arquivo que deve cercar o CAS de escrita."""
    if not isinstance(contract, WritingSemanticContract):
        raise TypeError("contrato semântico de escrita inválido")
    if (not isinstance(portfolio_rel_path, str) or
            _PORTFOLIO_REL_PATH.fullmatch(portfolio_rel_path) is None or
            source_catalog_rel_path != _SOURCE_HINT_CATALOG_REL_PATH or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in (portfolio_sha256, source_catalog_sha256))):
        raise ValueError("epoch de promoção de escrita é inválido")
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    epoch: dict[pathlib.Path, str | None] = {}

    def bind(relative: str, digest: str | None) -> None:
        path = canonical_root / relative
        if path in epoch and epoch[path] != digest:
            raise CASMismatch(
                f"epoch de escrita diverge para dependência repetida: {relative}")
        epoch[path] = digest

    bind(_WRITING_SEMANTIC_CONTRACT_REL_PATH, contract.digest)
    for relative, digest in contract.dependency_sha256.items():
        bind(relative, digest)
    for relative in contract.absent_dependency_paths:
        bind(relative, None)
    bind(portfolio_rel_path, portfolio_sha256)
    bind(source_catalog_rel_path, source_catalog_sha256)
    if raw_recovery_preimage_evidence is not None:
        evidence = validate_writing_raw_recovery_preimage_evidence(
            raw_recovery_preimage_evidence)
        bind(evidence["path"], evidence["sha256"])
    _assert_dependency_epoch(epoch)
    return epoch


def semantic_blocked_for_batch(
    expected_intents: Iterable[str],
    contract: WritingSemanticContract,
) -> tuple[str, ...]:
    """Projeta pendências na ordem semântica do lote, nunca em ordem de set."""
    if not isinstance(contract, WritingSemanticContract):
        raise TypeError("contrato semântico de escrita inválido")
    expected_order = tuple(expected_intents)
    if (not expected_order or len(set(expected_order)) != len(expected_order) or
            any(not isinstance(intent_id, str) or
                _INTENT_ID.fullmatch(intent_id) is None
                for intent_id in expected_order)):
        raise ValueError("ordem esperada do lote semântico é inválida")
    return tuple(
        intent_id for intent_id in expected_order
        if intent_id in contract.unresolved_intents
    )


def semantic_relocation_removals_for_target(
    target_rel_path: str,
    raw_records: Iterable[tuple[bytes, Mapping[str, Any]]],
    contract: WritingSemanticContract,
) -> tuple[dict[str, str], ...]:
    """Autentica linhas antigas que devem sair após nascer o owner novo.

    Um recorte movido não é ``preserve_extras``: a linha antiga só pode ser
    filtrada da classificação estrutural quando seus bytes coincidem com a
    preimagem arquivada. A fila pode registrar a remoção ainda pendente, porém
    o staged só a efetiva depois da resolução exata no owner vigente.
    """
    if (not isinstance(target_rel_path, str) or
            _TARGET_REL_PATH.fullmatch(target_rel_path) is None or
            not isinstance(contract, WritingSemanticContract)):
        raise TypeError("projeção de relocação semântica inválida")
    candidates = {
        intent_id: {
            "intent_id": intent_id,
            "record_sha256": superseded_sha256,
            "owner_target_rel_path": contract.target_rel_paths[intent_id],
            "requirement_sha256":
                contract.requirement_fingerprints[intent_id],
        }
        for intent_id, superseded_sha256 in
        contract.superseded_page_record_sha256.items()
        if (superseded_sha256 is not None and
            contract.superseded_target_rel_paths[intent_id] == target_rel_path and
            contract.target_rel_paths[intent_id] != target_rel_path)
    }
    observed: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, pair in enumerate(raw_records, 1):
        if (not isinstance(pair, tuple) or len(pair) != 2 or
                not isinstance(pair[0], bytes) or
                not isinstance(pair[1], Mapping)):
            raise ValueError(
                f"registro cru inválido na relocação semântica: {index}")
        raw_line, record = pair
        intent_id = record.get("intent_id")
        removal = candidates.get(intent_id)
        if removal is None:
            continue
        if intent_id in seen:
            raise ValueError(
                f"baseline semântica duplicada no shard antigo: {intent_id}")
        seen.add(intent_id)
        if _sha256(raw_line) != removal["record_sha256"]:
            raise ValueError(
                f"baseline semântica diverge da preimagem arquivada: {intent_id}")
        observed.append(removal)
    prematurely_missing = sorted(
        intent_id for intent_id in candidates
        if intent_id not in seen and intent_id in contract.unresolved_intents
    )
    if prematurely_missing:
        raise ValueError(
            "baseline semântica foi removida antes da resolução no owner: " +
            ", ".join(prematurely_missing[:8])
        )
    return tuple(observed)


def _validate_source_catalog_meta(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("_meta do catálogo de fontes tem schema inválido")
    version = value.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("_meta do catálogo de fontes tem schema inválido")
    text_fields = ("purpose", "source_policy")
    expected_keys = {"schema_version", "purpose", "source_policy"}
    if version == 2:
        text_fields = ("purpose", "source_policy", "source_kind_policy")
        expected_keys = expected_keys | {"source_kind_policy"}
    if (set(value) != expected_keys or
            any(not isinstance(value.get(field), str) or
                not value[field] or value[field] != value[field].strip()
                for field in text_fields)):
        raise ValueError("_meta do catálogo de fontes tem schema inválido")


_CATALOG_SOURCE_KINDS = frozenset({
    "legal_act", "binding_precedent", "judicial_decision",
    "official_guidance", "official_service",
})


def _canonical_exact_source(value: Any, label: str) -> dict[str, str]:
    if (not isinstance(value, dict) or
            set(value) not in (
                {"name", "url", "anchor_claim"},
                {"name", "url", "anchor_claim", "source_kind"})):
        raise ValueError(f"{label}: fonte oficial tem schema inválido")
    for field in ("name", "url", "anchor_claim"):
        text = value.get(field)
        if (not isinstance(text, str) or not text or text != text.strip() or
                any(0xd800 <= ord(char) <= 0xdfff or
                    ord(char) in (0xfffd, 0x2028, 0x2029)
                    for char in text)):
            raise ValueError(f"{label}: {field} não é texto canônico")
    if "source_kind" in value:
        # Classificação do catálogo (schema v2): validada aqui e removida do
        # retorno — o contrato congelado da fila/escrita segue {name, url,
        # anchor_claim} exatos.
        if value["source_kind"] not in _CATALOG_SOURCE_KINDS:
            raise ValueError(f"{label}: source_kind fora do enum fechado")
    if not _canonical_official_source_url(value["url"]):
        raise ValueError(f"{label}: URL oficial HTTPS inválida")
    return {field: value[field] for field in ("name", "url", "anchor_claim")}


def _canonical_candidate_source(value: Any, label: str) -> dict[str, str]:
    """Autentica uma pista de pesquisa sem promovê-la a fonte específica.

    As ``sources`` da fila entram literalmente no prompt do redator. Elas podem
    apontar para a raiz de um órgão — ao contrário de ``source_overrides`` —,
    mas ainda precisam estar confinadas a autoridade oficial HTTPS canônica e
    não podem carregar controles ou payload textual desproporcional.
    """
    if (not isinstance(value, dict) or set(value) != {"name", "url"}):
        raise ValueError(f"{label}: fonte candidata tem schema inválido")
    name = value.get("name")
    url = value.get("url")
    if (not isinstance(name, str) or not name or name != name.strip() or
            len(name) > 256 or
            any(ord(character) < 0x20 or ord(character) == 0x7f
                or 0xd800 <= ord(character) <= 0xdfff
                or ord(character) in (0xfffd, 0x2028, 0x2029)
                for character in name)):
        raise ValueError(f"{label}: nome da fonte candidata não é canônico")
    if (not isinstance(url, str) or
            not _canonical_official_source_url(
                url, require_specific_path=False)):
        raise ValueError(f"{label}: URL candidata oficial HTTPS inválida")
    return dict(value)


_SOURCE_RESOLUTION_BLOCKING_MARKERS = (
    # Grafias acentuada e sem acento do MESMO defeito. A projeção de fontes
    # deste módulo emite a forma acentuada ("sem resolução exata"); o texto
    # anterior, que ops/relaunch-writing.sh emitia antes de delegar a
    # resolução, vinha sem acento. Verificar as duas é o que impede a
    # classificação de se perder por acento em texto de erro.
    "hint fora do catalogo",
    "sem resolucao exata",
    "sem resolução exata",
    # Mesma FAMÍLIA de defeito: a entrada existe no catálogo mas a URL não é
    # documental (ex.: query URN sobre path raiz). O lote aguarda
    # tools/generate-catalog-url-repair.
    "URL oficial HTTPS invalida",
    "URL oficial HTTPS inválida",
)


def source_resolution_blocking_defect(detail: str) -> bool:
    """O defeito do lote é da família RESOLUÇÃO DE FONTE (emit-clean)?

    Esta é a ÚNICA família que ``ops/relaunch-writing.sh`` pode emitir-clean:
    o lote não entra na fila, cai no manifesto de defeitos com a lista exata
    de hints, e os lotes limpos seguem (perda zero, não-silenciosa). Qualquer
    outra família continua vetando a emissão (fail-closed).

    A função mora AQUI, e não dentro do heredoc do relaunch, porque quem
    verifica o fechamento da fila
    (``tools/verify_v2_writing_queue_closure.py``) precisa do MESMO predicado:
    duas cópias de uma lista de cinco strings foi exatamente como o acento se
    perdeu uma vez, e um verificador com predicado mais frouxo que o produtor
    transformaria a projeção negativa da fila em carimbo.

    Proveniência é requisito de publicação (R9): sem URL oficial, data e hash
    não se escreve linha nenhuma. Por isso o bloqueio NÃO é redação pendente
    nem gate quebrado — é curadoria de catálogo pendente, e o lote fica
    contado, nomeado e visível até ela acontecer.
    """
    if not isinstance(detail, str):
        raise TypeError("detalhe de defeito precisa ser str")
    return any(
        marker in detail for marker in _SOURCE_RESOLUTION_BLOCKING_MARKERS)


def derive_writing_source_resolution(
    root: pathlib.Path | str,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    catalog_rel_path: str,
    catalog_sha256: str,
    families: Iterable[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: list[str] | None,
) -> WritingSourceResolution:
    """Deriva a projeção exata de um seletor sob snapshots autenticados.

    ``take > 0`` continua sendo um slice posicional e exige ``intent_ids``
    ausente (representado por ``None`` nesta API). ``take == 0`` é sempre
    pinado: a lista explícita preserva sua ordem semântica mesmo se o portfólio
    receber novas intenções ou for reordenado. Cada pin precisa existir no
    mesmo snapshot e pertencer a uma das famílias declaradas.
    """
    if (not isinstance(portfolio_rel_path, str) or
            _PORTFOLIO_REL_PATH.fullmatch(portfolio_rel_path) is None or
            catalog_rel_path != _SOURCE_HINT_CATALOG_REL_PATH or
            not isinstance(portfolio_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", portfolio_sha256) is None or
            not isinstance(catalog_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", catalog_sha256) is None or
            type(skip) is not int or skip < 0 or
            type(take) is not int or take < 0 or
            type(expected_n) is not int or expected_n < 1):
        raise ValueError("identidade da projeção de fontes é inválida")
    try:
        family_order = list(families)
    except TypeError as error:
        raise ValueError("seletor da projeção de fontes é inválido") from error
    if (not family_order or
            any(not isinstance(family, str) or
                _FAMILY_ID.fullmatch(family) is None for family in family_order) or
            len(set(family_order)) != len(family_order) or
            (take > 0 and len(family_order) != 1) or
            (take == 0 and skip != 0) or
            (take > 0 and intent_ids is not None) or
            (take == 0 and (
                not isinstance(intent_ids, list) or
                len(intent_ids) != expected_n or
                any(not isinstance(intent_id, str) or
                    _INTENT_ID.fullmatch(intent_id) is None
                    for intent_id in intent_ids) or
                len(set(intent_ids)) != len(intent_ids)))):
        raise ValueError("seletor da projeção de fontes é inválido")

    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    portfolio = read_regular_file_snapshot(
        canonical_root / portfolio_rel_path, max_bytes=64 * 1024 * 1024)
    catalog = read_regular_file_snapshot(
        canonical_root / catalog_rel_path, max_bytes=8 * 1024 * 1024)
    if portfolio.digest != portfolio_sha256 or catalog.digest != catalog_sha256:
        raise CASMismatch("portfolio ou catálogo de fontes mudou depois da fila")
    catalog_value = decode_json_no_duplicate_keys(
        catalog.payload, "catálogo de fontes")
    if (not isinstance(catalog_value, dict) or
            set(catalog_value) != {"_meta", "strict_intents", "source_hints"} or
            not isinstance(catalog_value["_meta"], dict) or
            not isinstance(catalog_value["strict_intents"], list) or
            not isinstance(catalog_value["source_hints"], dict)):
        raise ValueError("catálogo de fontes tem schema inválido")
    _validate_source_catalog_meta(catalog_value["_meta"])
    strict_intents = catalog_value["strict_intents"]
    if (len(strict_intents) != len(set(strict_intents)) or
            any(not isinstance(intent, str) or
                _INTENT_ID.fullmatch(intent) is None for intent in strict_intents)):
        raise ValueError("strict_intents do catálogo não são canônicos")
    strict_set = set(strict_intents)
    source_entries = catalog_value["source_hints"]
    for hint in source_entries:
        if (not isinstance(hint, str) or
                _SOURCE_HINT_ID.fullmatch(hint) is None):
            raise ValueError("catálogo contém source_hint inválido")
    # Materialização LAZY e memoizada: _canonical_exact_source roda SOMENTE
    # para hint referenciado por intent selecionado. Entrada defeituosa que
    # nenhum intent do lote usa não envenena mais a projeção (antes, UMA URL
    # inválida no catálogo derrubava TODA fila/preflight/escrita, mesmo de
    # lotes sem relação com a entrada). Hint referenciado com entrada
    # inválida continua reprovando o SEU lote com a MESMA mensagem
    # ("source_hints.<hint>: URL oficial HTTPS inválida" — família emit-clean
    # do relaunch/empacotador). A validação global de INTEGRIDADE do catálogo
    # inteiro permanece nos gates dedicados
    # (reconcile_v2_strict_source_stock/TestV2StrictSourceStockMatchesExactCatalog).
    exact_sources: dict[str, dict[str, str]] = {}

    def _exact_source(hint: str) -> dict[str, str]:
        materialized = exact_sources.get(hint)
        if materialized is None:
            materialized = _canonical_exact_source(
                source_entries[hint], f"source_hints.{hint}")
            exact_sources[hint] = materialized
        return materialized

    by_family: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    by_intent: dict[str, dict[str, Any]] = {}
    seen_intents: set[str] = set()
    if not portfolio.payload or not portfolio.payload.endswith(b"\n"):
        raise ValueError("portfolio de fontes é vazio ou não terminado")
    for line_number, raw_line in enumerate(portfolio.payload.splitlines(), 1):
        try:
            record = decode_json_no_duplicate_keys(
                raw_line, f"portfolio de fontes:{line_number}")
        except ValueError as error:
            raise ValueError(
                f"portfolio de fontes inválido na linha {line_number}") from error
        if not isinstance(record, dict):
            raise ValueError(f"portfolio não é objeto na linha {line_number}")
        intent_id = record.get("intent_id")
        family = record.get("family")
        hints = record.get("source_hints")
        needs_source_research = record.get("needs_source_research")
        if (not isinstance(intent_id, str) or
                _INTENT_ID.fullmatch(intent_id) is None or
                not isinstance(family, str) or
                _FAMILY_ID.fullmatch(family) is None or
                not isinstance(hints, list) or
                len(hints) > 32 or
                any(not isinstance(hint, str) or not hint or
                    hint != hint.strip() for hint in hints) or
                len(hints) != len(set(hints)) or
                type(needs_source_research) is not bool or
                intent_id in seen_intents):
            raise ValueError(
                f"identidade/source_hints não canônicos na linha {line_number}")
        seen_intents.add(intent_id)
        selected_record = {
            "intent_id": intent_id,
            "family": family,
            "source_hints": hints,
            "needs_source_research": needs_source_research,
        }
        by_family[family].append(selected_record)
        by_intent[intent_id] = selected_record

    if take > 0:
        family_records = by_family.get(family_order[0], [])
        if skip + take > len(family_records):
            raise ValueError("slice da projeção de fontes fora do portfolio")
        selected = family_records[skip:skip + take]
    else:
        if intent_ids is None:
            raise ValueError(
                "seletor pinado perdeu intent_ids depois da validação")
        selected = []
        allowed_families = set(family_order)
        for intent_id in intent_ids:
            record = by_intent.get(intent_id)
            if record is None:
                raise ValueError(
                    f"intent_id pinado não existe no portfolio: {intent_id}")
            if record["family"] not in allowed_families:
                raise ValueError(
                    "intent_id pinado não pertence às families declaradas: "
                    f"{intent_id}: {record['family']}")
            selected.append(record)
        # O pin preserva a ordem literal dos IDs, mas essa ordem precisa
        # continuar semanticamente particionada pelas ``families`` declaradas.
        # Membership em set sozinho aceitava família omitida, inversão e
        # intercalamento A/B/A, divergindo do runtime JS e do consumidor Go.
        observed_family_runs: list[str] = []
        for record in selected:
            family = record["family"]
            if not observed_family_runs or observed_family_runs[-1] != family:
                observed_family_runs.append(family)
        if observed_family_runs != family_order:
            raise ValueError(
                "ordem integral dos intent_ids não coincide com as families "
                "declaradas")
    if len(selected) != expected_n:
        raise ValueError(
            f"projeção selecionou {len(selected)} intenções; esperava {expected_n}")

    expected_overrides: dict[str, dict[str, dict[str, str]]] = {}
    expected_strict: list[str] = []
    for record in selected:
        intent_id = record["intent_id"]
        hints = record["source_hints"]
        resolved = {
            hint: _exact_source(hint) for hint in sorted(hints)
            if hint in source_entries
        }
        unresolved = [hint for hint in hints if hint not in source_entries]
        if unresolved and not record["needs_source_research"]:
            raise ValueError(
                "intent declara pesquisa concluída sem resolução exata: "
                f"{intent_id}")
        if intent_id in strict_set:
            expected_strict.append(intent_id)
            if not hints or unresolved or len(resolved) != len(hints):
                raise ValueError(
                    f"intent strict sem resolução exata: {intent_id}")
        elif unresolved:
            # Pesquisa ainda aberta pode permanecer na fila, mas o verificador
            # só aceita tombstone: sem override, um registro materializado
            # reprova como intent strict sem fonte exata.
            expected_strict.append(intent_id)
            resolved = {}
        if resolved:
            expected_overrides[intent_id] = resolved
    expected_projection: dict[str, Any] = {
        "source_overrides": {
            intent: expected_overrides[intent]
            for intent in sorted(expected_overrides)
        },
        "strict_source_intents": sorted(expected_strict),
    }
    return WritingSourceResolution(
        selected_intents=tuple(record["intent_id"] for record in selected),
        source_overrides=expected_projection["source_overrides"],
        strict_source_intents=tuple(expected_projection["strict_source_intents"]),
    )


def verify_writing_source_resolution(
    root: pathlib.Path | str,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    catalog_rel_path: str,
    catalog_sha256: str,
    families: Iterable[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: list[str] | None,
    projection_base64: str,
) -> WritingSourceResolution:
    """Recomputa e autentica catálogo, seletor pinado e projeção da fila."""
    if (not isinstance(projection_base64, str) or
            len(projection_base64) >
            _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES * 2):
        raise ValueError("identidade da projeção de fontes é inválida")
    resolution = derive_writing_source_resolution(
        root,
        portfolio_rel_path,
        portfolio_sha256,
        catalog_rel_path,
        catalog_sha256,
        families,
        skip,
        take,
        expected_n,
        intent_ids,
    )
    expected_projection = {
        "source_overrides": dict(resolution.source_overrides),
        "strict_source_intents": list(resolution.strict_source_intents),
    }
    try:
        encoded = projection_base64.encode("ascii")
        raw_projection = base64.b64decode(encoded, validate=True)
        if len(raw_projection) > _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES:
            raise ValueError("projeção de fontes excede limite")
        actual_projection = decode_json_no_duplicate_keys(
            raw_projection, "projeção de fontes")
    except (UnicodeEncodeError, UnicodeDecodeError, ValueError) as error:
        raise ValueError("projeção de fontes da fila é inválida") from error
    if (not isinstance(actual_projection, dict) or
            set(actual_projection) != {"source_overrides", "strict_source_intents"} or
            actual_projection != expected_projection):
        raise ValueError(
            "source_overrides/strict_source_intents divergem da projeção exata")
    return resolution


def derive_writing_raw_recovery_projection(
    payload: bytes,
    target_rel_path: str,
    target_sha256: str,
    expected_intents: Iterable[str],
    *,
    semantically_blocked_intents: Iterable[str] = (),
) -> dict[str, Any] | None:
    """Describe a safe full-slice rewrite for an unparseable raw preimage.

    Valid, uniquely addressable rows from the expected slice may be preserved
    byte-for-byte. Invalid/ambiguous rows are never interpreted. A canonical
    extra outside the slice is not disposable evidence and therefore blocks
    automatic recovery until a migration/supersession contract authenticates
    it. ``None`` means the ordinary writing contract can parse the preimage.
    """
    if (not isinstance(payload, bytes) or
            not isinstance(target_rel_path, str) or
            _TARGET_REL_PATH.fullmatch(target_rel_path) is None or
            not isinstance(target_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", target_sha256) is None or
            _sha256(payload) != target_sha256):
        raise ValueError("identidade raw-recovery inválida")
    expected = tuple(expected_intents)
    if (not expected or len(expected) != len(set(expected)) or
            any(not isinstance(intent, str) or
                _INTENT_ID.fullmatch(intent) is None
                for intent in expected)):
        raise ValueError("slice esperado de raw-recovery inválido")
    blocked = tuple(semantically_blocked_intents)
    if (len(blocked) != len(set(blocked)) or
            any(not isinstance(intent, str) or
                _INTENT_ID.fullmatch(intent) is None
                for intent in blocked) or
            not set(blocked).issubset(set(expected))):
        raise ValueError("bloqueios semânticos de raw-recovery inválidos")

    reasons: set[str] = set()
    if not payload.endswith(b"\n"):
        reasons.add("missing_terminal_lf")
    if b"\r" in payload:
        reasons.add("noncanonical_cr")
    raw_lines = payload.split(b"\n")
    if payload.endswith(b"\n"):
        raw_lines = raw_lines[:-1]
    if len(raw_lines) > 1_000_000:
        raise ValueError("preimagem raw-recovery excede limite de linhas")
    parsed: list[tuple[bytes, dict[str, Any], str]] = []
    object_rows = 0
    invalid_rows = 0
    unaddressable_rows = 0
    for line_number, raw_line in enumerate(raw_lines, 1):
        if not raw_line:
            invalid_rows += 1
            reasons.add("invalid_json_row")
            continue
        try:
            row = decode_json_no_duplicate_keys(
                raw_line, f"raw-recovery:{line_number}")
        except ValueError:
            invalid_rows += 1
            reasons.add("invalid_json_row")
            continue
        if not isinstance(row, dict):
            invalid_rows += 1
            reasons.add("non_object_row")
            continue
        object_rows += 1
        intent_id = row.get("intent_id")
        if (not isinstance(intent_id, str) or
                _INTENT_ID.fullmatch(intent_id) is None):
            unaddressable_rows += 1
            reasons.add("unaddressable_row")
            continue
        parsed.append((raw_line, row, intent_id))

    occurrences = collections.Counter(intent for _, _, intent in parsed)
    duplicates = sorted(
        intent for intent, count in occurrences.items() if count != 1)
    if duplicates:
        reasons.add("duplicate_intent_rows")
    extras = sorted(set(occurrences) - set(expected))
    if extras:
        raise DistinctnessOperationalError(
            ("writing_raw_recovery_valid_extra_requires_migration",),
            (target_rel_path,), extras,
        )
    if object_rows != len(expected):
        reasons.add("cardinality_mismatch")
    observed_unique_order = tuple(
        intent for _, _, intent in parsed if occurrences[intent] == 1)
    if (not duplicates and not invalid_rows and not unaddressable_rows and
            observed_unique_order != expected):
        reasons.add("intent_order_mismatch")
    if not reasons:
        return None

    blocked_set = set(blocked)
    preserved: dict[str, str] = {}
    reusable: list[str] = []
    by_intent = {
        intent: (raw_line, row)
        for raw_line, row, intent in parsed
        if occurrences[intent] == 1
    }
    for intent in expected:
        entry = by_intent.get(intent)
        if entry is None or intent in blocked_set:
            continue
        raw_line, row = entry
        if b"\r" in raw_line:
            continue
        # Mesmo predicado de reuse do classificador (``writing_reusable_page``):
        # só página ativa. Até 2026-09-05 esta rota tinha definição própria —
        # tombstone fechada entrava em reuse (congelando um bloqueio que o
        # catálogo pinado do lote já desfazia) e página com fonte fora do
        # allowlist atual ficava de fora (mandando o redator reescrever texto
        # pago que a rota ordinária preserva). Como ``ops/relaunch-writing.sh``
        # copia este ``reuse`` para o lote e o fechamento da fila usa o
        # classificador como oráculo, qualquer diferença entre os dois virava
        # "reuse diverge da preimagem autenticada". A fonte de uma linha
        # preservada não é revalidada aqui nem no staged: a linha é ligada por
        # hash aos bytes vivos e jamais reescrita.
        if not writing_reusable_page(row):
            continue
        reusable.append(intent)
        preserved[intent] = _sha256(raw_line)

    expected_payload = json.dumps(
        expected, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    projection: dict[str, Any] = {
        "schema_version": "v2_writing_raw_recovery_v1",
        "route": "writing_full_shard_recovery",
        "target_rel_path": target_rel_path,
        "target_sha256": target_sha256,
        "expected_n": len(expected),
        "expected_intent_ids": list(expected),
        "expected_intent_ids_sha256": _sha256(expected_payload),
        "reason_codes": sorted(reasons),
        "raw_lines_seen": len(raw_lines),
        "parsed_object_rows": object_rows,
        "invalid_rows": invalid_rows,
        "unaddressable_rows": unaddressable_rows,
        "reuse": reusable,
        "preserved_record_sha256": preserved,
        "review_allowed": False,
        "publication_allowed": False,
        "index_policy": "noindex",
    }
    projection["recovery_item_sha256"] = writing_recovery_item_sha256(
        projection)
    return validate_writing_raw_recovery_projection(
        projection, target_rel_path=target_rel_path,
        target_sha256=target_sha256, expected_intents=expected)


def capture_writing_raw_recovery_projection(
    root: pathlib.Path | str,
    target_rel_path: str,
    target_sha256: str,
    expected_intents: Iterable[str],
    *,
    semantic_contract_loader: (
        Callable[[], WritingSemanticContract] | None) = None,
) -> dict[str, Any] | None:
    """Capture the live raw target once and derive its recovery projection.

    ``semantic_contract_loader`` é opcional e serve a quem processa um LOTE:
    carregar o contrato custa ~1,5 s porque o epoch v3 autentica o estoque
    inteiro (731 dependências, 42 MB lidos e parseados), e refazer isso por
    registro é O(lote × estoque). É um CALLABLE, não o contrato pronto, para
    preservar a preguiça do caminho atual — registro que já morre no CAS da
    preimagem (logo acima) não paga contrato nenhum, como antes.
    Injetar o loader NÃO afrouxa nada: a reautenticação CAS abaixo
    (``verify_writing_semantic_contract_dependencies``) continua obrigatória e
    roda contra os bytes VIVOS, então um contrato memoizado já vencido levanta
    ``CASMismatch`` em vez de ser aceito — fail-closed idêntico ao caminho que
    carrega na hora. Quem memoiza é responsável por invalidar o próprio cache
    quando ele mesmo escreve no estoque.
    """
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    target = read_regular_file_snapshot(
        canonical_root / target_rel_path, max_bytes=64 * 1024 * 1024)
    if target.digest != target_sha256:
        raise CASMismatch("preimagem raw mudou depois da fila")
    if semantic_contract_loader is None:
        semantic_contract = load_writing_semantic_contract(canonical_root)
    else:
        semantic_contract = semantic_contract_loader()
        if not isinstance(semantic_contract, WritingSemanticContract):
            raise TypeError("contrato semântico de escrita inválido")
    expected = tuple(expected_intents)
    blocked = set(expected) & semantic_contract.unresolved_intents
    projection = derive_writing_raw_recovery_projection(
        target.payload, target_rel_path, target_sha256, expected,
        semantically_blocked_intents=blocked)
    verify_writing_semantic_contract_dependencies(
        canonical_root, semantic_contract)
    return projection


def writing_raw_recovery_preimage_evidence(
    target_sha256: str,
) -> dict[str, str]:
    """Return the closed content-addressed identity of a raw preimage."""
    if (not isinstance(target_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", target_sha256) is None):
        raise ValueError("SHA da preimagem raw-recovery inválido")
    return {
        "path": (
            f"{WRITING_RAW_RECOVERY_PREIMAGE_DIR}/{target_sha256}.raw"),
        "sha256": target_sha256,
    }


def validate_writing_raw_recovery_preimage_evidence(
    value: Mapping[str, Any],
    *,
    target_sha256: str | None = None,
) -> dict[str, str]:
    """Validate the exact path/digest pair used by claims and CAS epochs."""
    if (not isinstance(value, Mapping) or
            set(value) != {"path", "sha256"} or
            not isinstance(value.get("path"), str) or
            not isinstance(value.get("sha256"), str) or
            _WRITING_RAW_RECOVERY_PREIMAGE_REL.fullmatch(value["path"])
            is None):
        raise ValueError("evidência da preimagem raw-recovery inválida")
    expected = writing_raw_recovery_preimage_evidence(value["sha256"])
    if dict(value) != expected:
        raise ValueError("path da preimagem raw-recovery diverge do SHA")
    if target_sha256 is not None and value["sha256"] != target_sha256:
        raise ValueError("evidência raw-recovery diverge do target SHA")
    return expected


def persist_writing_raw_recovery_preimage(
    root: pathlib.Path | str,
    payload: bytes,
    target_sha256: str,
) -> dict[str, str]:
    """Create once, or reuse byte-identically, an opaque raw preimage.

    A private temporary inode is fully written and fsynced before a hard-link
    publishes the digest-named file with no-replace semantics.  The temporary
    name is then removed, so every accepted final object has exactly one link.
    A crash can leave only an unreferenced dot-file, never a partial final
    object.  A pre-existing final object is authority only when its bytes hash
    to the requested digest.
    """
    if not isinstance(payload, bytes):
        raise TypeError("preimagem raw-recovery deve ser bytes")
    evidence = writing_raw_recovery_preimage_evidence(target_sha256)
    if _sha256(payload) != target_sha256:
        raise ValueError("bytes raw-recovery divergem do target SHA")
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    editorial = canonical_root / "data" / "editorial"
    editorial_fd, _, _ = _open_parent_directory(editorial / ".anchor")
    archive_fd: int | None = None
    temporary_name: str | None = None
    try:
        try:
            os.mkdir("v2_raw_recovery_preimages", 0o755,
                     dir_fd=editorial_fd)
            os.fsync(editorial_fd)
        except FileExistsError:
            pass
        archive_fd = os.open(
            "v2_raw_recovery_preimages",
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=editorial_fd,
        )
        final_name = f"{target_sha256}.raw"
        existing = _read_snapshot_at(
            archive_fd, final_name, missing_ok=True,
            max_bytes=64 * 1024 * 1024)
        if existing is not None:
            if (existing.nlink != 1 or existing.digest != target_sha256 or
                    existing.payload != payload):
                raise CASMismatch(
                    "preimagem raw-recovery permanente diverge do digest")
            return evidence

        temporary_name = (
            f".{target_sha256}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
        fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC |
            os.O_NOFOLLOW,
            0o600,
            dir_fd=archive_fd,
        )
        try:
            view = memoryview(payload)
            offset = 0
            while offset < len(view):
                written = os.write(fd, view[offset:])
                if written <= 0:
                    raise OSError("escrita raw-recovery não avançou")
                offset += written
            os.fsync(fd)
            os.fchmod(fd, 0o444)
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(
                temporary_name, final_name,
                src_dir_fd=archive_fd, dst_dir_fd=archive_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            pass
        finally:
            os.unlink(temporary_name, dir_fd=archive_fd)
            temporary_name = None
        os.fsync(archive_fd)
        final = _read_snapshot_at(
            archive_fd, final_name, missing_ok=False,
            max_bytes=64 * 1024 * 1024)
        if (final is None or final.nlink != 1 or
                final.digest != target_sha256 or final.payload != payload):
            raise CASMismatch(
                "preimagem raw-recovery permanente não é byte-idêntica")
        return evidence
    finally:
        if archive_fd is not None:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=archive_fd)
                except FileNotFoundError:
                    pass
            os.close(archive_fd)
        os.close(editorial_fd)


def read_writing_raw_recovery_preimage(
    root: pathlib.Path | str,
    evidence: Mapping[str, Any],
    target_sha256: str,
) -> "RegularFileSnapshot":
    """Read one permanent raw object through a closed path/digest binding."""
    bound = validate_writing_raw_recovery_preimage_evidence(
        evidence, target_sha256=target_sha256)
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    snapshot = read_regular_file_snapshot(
        canonical_root / bound["path"], max_bytes=64 * 1024 * 1024)
    if snapshot.digest != target_sha256:
        raise CASMismatch("preimagem raw-recovery permanente evoluiu")
    return snapshot


def verify_writing_raw_recovery_preimage_projection(
    root: pathlib.Path | str,
    evidence: Mapping[str, Any],
    target_rel_path: str,
    target_sha256: str,
    expected_intents: Iterable[str],
    semantic_contract: "WritingSemanticContract | None" = None,
) -> dict[str, Any] | None:
    """Recompute a queue projection from the permanent opaque preimage.

    ``semantic_contract`` é opcional (achado 2026-07-30): quando o chamador já
    fez ``load_writing_semantic_contract`` uma vez (ex.: relaunch-writing.sh no
    topo do próprio script), reusar essa instância evita reler/reparsear o
    contrato e os portfolios dependentes a cada lote do laço — cada recarga
    custava ~1.2-1.4s e o laço percorre centenas de lotes, o que sozinho
    esgotava o orçamento de tempo do produtor. Omitido (None, default),
    o comportamento é IDÊNTICO ao anterior: carrega uma cópia própria.
    """
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    snapshot = read_writing_raw_recovery_preimage(
        canonical_root, evidence, target_sha256)
    if semantic_contract is None:
        semantic_contract = load_writing_semantic_contract(canonical_root)
    expected = tuple(expected_intents)
    blocked = set(expected) & semantic_contract.unresolved_intents
    projection = derive_writing_raw_recovery_projection(
        snapshot.payload, target_rel_path, target_sha256, expected,
        semantically_blocked_intents=blocked)
    verify_writing_semantic_contract_dependencies(
        canonical_root, semantic_contract)
    return projection


def _canonical_consolidated_source(
    by_hint: Mapping[str, Mapping[str, str]],
) -> dict[str, str]:
    """Materializa uma URL repetida sem perder nenhum anchor do catálogo.

    ``official_sources`` não admite duplicar a mesma URL. Para manter a
    resolução auditável, o nome vem do primeiro hint em ordem lexical e todos
    os ``anchor_claim`` entram, sem reescrita, separados por `` | ``. Qualquer
    outra composição seria semanticamente impossível de autenticar por
    máquina e reabriria o falso-verde de fonte oficial porém irrelevante.
    """
    hints = sorted(by_hint)
    if not hints:
        raise ValueError("grupo de source_hints não pode ser vazio")
    first = by_hint[hints[0]]
    url = first["url"]
    if any(by_hint[hint]["url"] != url for hint in hints):
        raise ValueError("grupo consolidado mistura URLs")
    return {
        "name": first["name"],
        "url": url,
        "anchor_claim": " | ".join(
            by_hint[hint]["anchor_claim"] for hint in hints),
    }


def _canonical_staged_official_source(value: Any, label: str) -> dict[str, str]:
    """Valida toda fonte antes da etapa live, inclusive fontes adicionais.

    ``verified_at``/``http_status`` só podem nascer na ferramenta de
    proveniência posterior ao CAS. Aceitá-los no staged permitiria ao redator
    fabricar o cache live e, no pior caso, entregar URL não oficial ao probe.
    """
    if (not isinstance(value, dict) or
            set(value) != {"name", "url", "anchor_claim"}):
        raise ValueError(f"{label}: fonte staged tem schema inválido")
    for field in ("name", "url", "anchor_claim"):
        text = value.get(field)
        if (not isinstance(text, str) or not text or text != text.strip()):
            raise ValueError(f"{label}: {field} não é texto canônico")
    if not _canonical_official_source_url(value["url"]):
        raise ValueError(f"{label}: URL staged não é fonte oficial permitida")
    return dict(value)


def verify_staged_writing_source_resolution(
    root: pathlib.Path | str,
    staged_path: pathlib.Path | str,
    target_rel_path: str,
    target_sha256: str,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    catalog_rel_path: str,
    catalog_sha256: str,
    families: Iterable[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: list[str] | None,
    projection_base64: str,
    preservation_base64: str | None = None,
) -> "RegularFileSnapshot":
    """Autentica a forma integral/fontes escritas e devolve o mesmo snapshot.

    O preflight da fila prova a resolução catálogo→intent, mas não prova que o
    redator a materializou. Esta segunda etapa relê ``final.jsonl`` por descritor
    seguro, exige a ordem exata do slice + extras, autentica byte a byte todo
    registro que a fila mandou preservar e compara cada URL consolidada com a
    identidade material derivada do catálogo. Tombstones fechadas continuam
    permitidas: a indisponibilidade de uma fonte deve manter a intenção na fila,
    nunca pressionar o redator a fabricar uma página. O chamador deve promover
    Tombstone bloqueia a página neste estoque; ela não promete reentrada
    automática na fila, que exige uma correção explícita da fonte/intenção.
    O chamador deve promover ``snapshot.payload`` diretamente; reabrir
    ``staged_path`` depois desta
    função recriaria a janela TOCTOU que este contrato fecha.
    """
    resolution = verify_writing_source_resolution(
        root,
        portfolio_rel_path,
        portfolio_sha256,
        catalog_rel_path,
        catalog_sha256,
        families,
        skip,
        take,
        expected_n,
        intent_ids,
        projection_base64,
    )
    semantic_contract = load_writing_semantic_contract(root)
    selected_set = set(resolution.selected_intents)
    semantically_blocked = selected_set & semantic_contract.unresolved_intents
    misbound_semantic = sorted(
        intent_id for intent_id in selected_set
        if (intent_id in semantic_contract.requirement_fingerprints and
            semantic_contract.target_rel_paths[intent_id] != target_rel_path)
    )
    if misbound_semantic:
        raise ValueError(
            "requisito semântico pertence a outro shard: " +
            ", ".join(misbound_semantic[:8]))
    if preservation_base64 is None:
        preservation: Any = {
            "reuse": [],
            "preserve_extras": [],
            "preserved_record_sha256": {},
            "authenticated_replacement": False,
            "semantic_contract_sha256": semantic_contract.digest,
            "semantic_relocation_removals": [],
        }
    else:
        if (not isinstance(preservation_base64, str) or
                len(preservation_base64) >
                _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES * 2):
            raise ValueError("projeção de preservação da fila é inválida")
        try:
            encoded = preservation_base64.encode("ascii")
            raw_preservation = base64.b64decode(encoded, validate=True)
            if len(raw_preservation) > _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES:
                raise ValueError("projeção de preservação excede limite")
            preservation = decode_json_no_duplicate_keys(
                raw_preservation, "projeção de preservação")
        except (UnicodeEncodeError, UnicodeDecodeError, ValueError) as error:
            raise ValueError(
                "projeção de preservação da fila é inválida") from error
    if (not isinstance(preservation, dict) or
            set(preservation) != {
                "reuse", "preserve_extras", "preserved_record_sha256",
                "authenticated_replacement", "semantic_contract_sha256",
                "semantic_relocation_removals"} or
            type(preservation["authenticated_replacement"]) is not bool or
            not isinstance(preservation["semantic_contract_sha256"], str) or
            re.fullmatch(
                r"[0-9a-f]{64}",
                preservation["semantic_contract_sha256"],
            ) is None or
            preservation["semantic_contract_sha256"] !=
            semantic_contract.digest):
        raise ValueError("projeção de preservação tem schema inválido")
    reuse = preservation["reuse"]
    preserve_extras = preservation["preserve_extras"]
    preserved_hashes = preservation["preserved_record_sha256"]
    relocation_removals = preservation["semantic_relocation_removals"]
    for label, values in (("reuse", reuse),
                          ("preserve_extras", preserve_extras)):
        if (not isinstance(values, list) or
                len(values) != len(set(values)) or
                any(not isinstance(intent, str) or
                    _INTENT_ID.fullmatch(intent) is None for intent in values)):
            raise ValueError(f"{label} da preservação não é canônico")
    if (not set(reuse).issubset(selected_set) or
            set(preserve_extras) & selected_set or
            set(reuse) & set(preserve_extras)):
        raise ValueError("reuse/extras não coincidem com o slice autenticado")
    preserved_ids = set(reuse) | set(preserve_extras)
    if (not isinstance(preserved_hashes, dict) or
            set(preserved_hashes) != preserved_ids or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in preserved_hashes.values())):
        raise ValueError("hashes dos registros preservados divergem da fila")
    relocation_fields = {
        "intent_id", "record_sha256", "owner_target_rel_path",
        "requirement_sha256",
    }
    if (not isinstance(relocation_removals, list) or
            len({item.get("intent_id") for item in relocation_removals
                 if isinstance(item, dict)}) != len(relocation_removals) or
            any(not isinstance(item, dict) or set(item) != relocation_fields or
                not isinstance(item.get("intent_id"), str) or
                _INTENT_ID.fullmatch(item["intent_id"]) is None or
                not isinstance(item.get("owner_target_rel_path"), str) or
                _TARGET_REL_PATH.fullmatch(
                    item["owner_target_rel_path"]) is None or
                any(not isinstance(item.get(field), str) or
                    re.fullmatch(r"[0-9a-f]{64}", item[field]) is None
                    for field in ("record_sha256", "requirement_sha256"))
                for item in relocation_removals)):
        raise ValueError("remoções semânticas da preservação não são canônicas")
    relocation_ids = {
        item["intent_id"] for item in relocation_removals
    }
    if (relocation_ids & selected_set or relocation_ids & preserved_ids):
        raise ValueError(
            "remoção semântica conflita com slice ou registros preservados")

    if (not isinstance(target_rel_path, str) or
            _TARGET_REL_PATH.fullmatch(target_rel_path) is None or
            not isinstance(target_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", target_sha256) is None):
        raise ValueError("identidade da preimagem de escrita é inválida")
    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    try:
        target = read_regular_file_snapshot(
            canonical_root / target_rel_path, max_bytes=64 * 1024 * 1024)
    except FileNotFoundError:
        target = RegularFileSnapshot(b"", _sha256(b""))
    if target.digest != target_sha256:
        raise CASMismatch("preimagem do shard mudou depois da fila")

    preimage_rows: list[dict[str, Any]] = []
    preimage_raw: list[bytes] = []
    if target.payload:
        if not target.payload.endswith(b"\n"):
            raise ValueError("preimagem do shard não termina com newline")
        preimage_raw = target.payload[:-1].split(b"\n")
        for line_number, raw_line in enumerate(preimage_raw, 1):
            if not raw_line:
                raise ValueError(
                    f"preimagem do shard contém linha vazia: {line_number}")
            row = decode_json_no_duplicate_keys(
                raw_line, f"preimagem do shard:{line_number}")
            if not isinstance(row, dict):
                raise ValueError(
                    f"preimagem do shard não é objeto: {line_number}")
            intent_id = row.get("intent_id")
            if (not isinstance(intent_id, str) or
                    _INTENT_ID.fullmatch(intent_id) is None):
                raise ValueError(
                    f"preimagem sem intent_id canônico: {line_number}")
            preimage_rows.append(row)

    if preservation["authenticated_replacement"]:
        if reuse or preserve_extras or preserved_hashes or relocation_removals:
            raise ValueError(
                "migração integral não pode misturar registros preservados")
    else:
        occurrences = collections.Counter(
            row["intent_id"] for row in preimage_rows)
        expected_reuse = [
            row["intent_id"] for row in preimage_rows
            if (row["intent_id"] in selected_set and
                row["intent_id"] not in semantically_blocked and
                occurrences[row["intent_id"]] == 1 and
                writing_reusable_page(row))
        ]
        expected_extras: list[str] = []
        extra_seen: set[str] = set()
        tombstone_extras: set[str] = set()
        dec020_winners = None
        for row in preimage_rows:
            intent_id = row["intent_id"]
            if intent_id in selected_set or intent_id in relocation_ids:
                continue
            if row.get("skipped") is True:
                # Tombstone DEC-020 deslocado do slice pelo re-pin de posse:
                # é evidência obrigatória da cadeia (o gate Go exige o par
                # tombstone na origem + ativo no canônico) e autentica pela
                # MESMA chave de vencedor do classificador. Qualquer outro
                # registro pulado continua não preservável.
                reason = row.get("skip_reason")
                if (intent_id not in extra_seen and
                        isinstance(reason, str) and
                        reason.strip() == "duplicate_intent_consolidated"):
                    if dec020_winners is None:
                        from tools import audit_v2_pages as auditor
                        dec020_winners, _ = (
                            auditor.validated_duplicate_supersession_winners(
                                canonical_root))
                    if (row.get("superseded_by"),
                            intent_id) in dec020_winners:
                        extra_seen.add(intent_id)
                        tombstone_extras.add(intent_id)
                        expected_extras.append(intent_id)
                        continue
                raise ValueError(
                    f"preimagem contém extra não preservável: {intent_id}")
            if intent_id in extra_seen or not row.get("sections"):
                raise ValueError(
                    f"preimagem contém extra não preservável: {intent_id}")
            extra_seen.add(intent_id)
            expected_extras.append(intent_id)
        if expected_extras:
            # A mera presença de ``sections`` não autoriza uma linha fora do
            # slice. Reuse da fila só pode preservar o vencedor único de uma
            # cadeia DEC-020 autenticada pelo mesmo validador do auditor.
            if dec020_winners is None:
                from tools import audit_v2_pages as auditor
                dec020_winners, _ = (
                    auditor.validated_duplicate_supersession_winners(
                        canonical_root))
            winners = dec020_winners
            target_name = pathlib.PurePosixPath(target_rel_path).name
            unauthorized = [
                intent_id for intent_id in expected_extras
                if (intent_id not in tombstone_extras and
                    (target_name, intent_id) not in winners)
            ]
            if unauthorized:
                raise ValueError(
                    "preimagem contém extra sem vencedor DEC-020: "
                    f"{unauthorized[:8]}")
        expected_preserved = set(expected_reuse) | set(expected_extras)
        expected_hashes = {
            row["intent_id"]: _sha256(raw_line)
            for row, raw_line in zip(preimage_rows, preimage_raw)
            if row["intent_id"] in expected_preserved
        }
        if (reuse != expected_reuse or
                preserve_extras != expected_extras or
                preserved_hashes != expected_hashes):
            raise ValueError(
                "preservação da fila diverge da preimagem autenticada")

    expected_relocation_removals = list(
        semantic_relocation_removals_for_target(
            target_rel_path,
            tuple(zip(preimage_raw, preimage_rows)),
            semantic_contract,
        )
    )
    if relocation_removals != expected_relocation_removals:
        raise ValueError(
            "remoções semânticas divergem da preimagem autenticada")
    unresolved_relocations = sorted(
        removal["intent_id"] for removal in expected_relocation_removals
        if removal["intent_id"] in semantic_contract.unresolved_intents
    )
    if unresolved_relocations:
        raise ValueError(
            "baseline semântica não pode sair antes da resolução no owner: " +
            ", ".join(unresolved_relocations[:8])
        )

    staged = read_regular_file_snapshot(
        staged_path, max_bytes=64 * 1024 * 1024)
    if not staged.payload or not staged.payload.endswith(b"\n"):
        raise ValueError("staged de escrita é vazio ou não termina com newline")
    rows: list[dict[str, Any]] = []
    raw_lines = staged.payload[:-1].split(b"\n")
    for line_number, raw_line in enumerate(raw_lines, 1):
        if not raw_line:
            raise ValueError(f"staged de escrita contém linha vazia: {line_number}")
        try:
            row = decode_json_no_duplicate_keys(
                raw_line, f"staged de escrita:{line_number}")
        except ValueError as error:
            raise ValueError(
                f"staged de escrita não é JSON na linha {line_number}") from error
        if not isinstance(row, dict):
            raise ValueError(
                f"staged de escrita não é objeto na linha {line_number}")
        rows.append(row)
    expected_order = resolution.selected_intents + tuple(preserve_extras)
    if len(rows) != len(expected_order):
        raise ValueError(
            f"staged tem {len(rows)} linhas; fila exige {len(expected_order)}")
    observed_intents = tuple(row.get("intent_id") for row in rows)
    if observed_intents != expected_order:
        raise ValueError(
            "ordem integral dos intent_ids diverge do slice/extras autenticados")
    raw_by_intent = dict(zip(observed_intents, raw_lines))
    unchanged_semantic = sorted(
        intent_id for intent_id in semantically_blocked
        if (semantic_contract.superseded_page_record_sha256[intent_id]
            is not None and
            _sha256(raw_by_intent[intent_id]) ==
            semantic_contract.superseded_page_record_sha256[intent_id]))
    if unchanged_semantic:
        raise ValueError(
            "staged repetiu bytes da página semanticamente superada: " +
            ", ".join(unchanged_semantic[:8]))
    for intent_id, expected_digest in preserved_hashes.items():
        if _sha256(raw_by_intent[intent_id]) != expected_digest:
            raise ValueError(
                f"registro preservado mudou byte a byte: {intent_id}")

    strict = set(resolution.strict_source_intents)
    reuse_set = set(reuse)
    for row in rows[:expected_n]:
        intent_id = row["intent_id"]
        if row.get("skipped") is True:
            if (set(row) != {"intent_id", "skipped", "skip_reason"} or
                    not isinstance(row.get("skip_reason"), str) or
                    not row["skip_reason"].strip() or
                    row["skip_reason"] != row["skip_reason"].strip()):
                raise ValueError(f"tombstone de escrita não é fechada: {intent_id}")
            continue
        if intent_id in reuse_set:
            # Registro reusado é preservado BYTE A BYTE (autenticado acima
            # contra preserved_hashes antes deste laço) — o override do
            # catálogo só existe para guiar ESCRITA NOVA. Comparar a fonte
            # já gravada contra a projeção fresca do catálogo compararia
            # conteúdo que jamais será reescrito e pode reprovar wording
            # legítimo do momento original da escrita (ex.: "Lei
            # 10.406/2002" vs "Lei nº 10.406/2002" do catálogo atual) sem
            # que o registro preservado esteja errado. O gate de
            # integridade do reuse é o hash byte a byte, não este.
            #
            # 2026-07-31: o skip precisa vir ANTES da validação de schema do
            # staged. _canonical_staged_official_source exige exatamente
            # {name,url,anchor_claim} para impedir que o REDATOR fabrique
            # verified_at/http_status — mas página já promovida e auditada
            # carrega esse par, gravado por audit-v2-source-provenance. Com a
            # checagem rodando antes do skip, os dois gates se contradiziam
            # (o hash byte a byte exige preservar exatamente esses bytes; o
            # schema estrito rejeitava esses mesmos bytes) e NENHUMA promoção
            # com reuse de página auditada podia concluir — defeito
            # determinístico reproduzido em glossario2-14/lgpd-25/aereo-25.
            # A proteção antifraude do redator segue intacta: conteúdo
            # reusado é autenticado contra preserved_record_sha256, que vem
            # da preimagem em disco, não do texto entregue pelo redator.
            continue
        official_sources = row.get("official_sources")
        if not isinstance(official_sources, list) or not official_sources:
            raise ValueError(
                f"página staged sem official_sources: {intent_id}")
        actual_by_url: dict[str, Mapping[str, Any]] = {}
        for source_index, source in enumerate(official_sources, 1):
            canonical_source = _canonical_staged_official_source(
                source, f"official_sources:{intent_id}:{source_index}")
            url = canonical_source["url"]
            if url in actual_by_url:
                raise ValueError(
                    f"official_sources duplica URL em {intent_id}: {url}")
            actual_by_url[url] = canonical_source

        expected_by_hint = resolution.source_overrides.get(intent_id, {})
        if intent_id in strict and not expected_by_hint:
            raise ValueError(
                f"intent strict sem source_hints materializados: {intent_id}")
        if not expected_by_hint:
            continue

        expected_hints_by_url: dict[
            str, dict[str, Mapping[str, str]]
        ] = collections.defaultdict(dict)
        for hint, source in expected_by_hint.items():
            expected_hints_by_url[source["url"]][hint] = source
        for url, hints in expected_hints_by_url.items():
            expected_source = _canonical_consolidated_source(hints)
            actual_source = actual_by_url.get(url)
            if actual_source is None:
                raise ValueError(
                    f"intent perdeu fonte exata {intent_id}: {url}")
            actual_identity = {
                field: actual_source.get(field)
                for field in ("name", "url", "anchor_claim")
            }
            if actual_identity != expected_source:
                raise ValueError(
                    "fonte material diverge da consolidação exata: "
                    f"{intent_id}: {url}")
    verify_writing_semantic_contract_dependencies(root, semantic_contract)
    return staged


def verify_staged_writing_recovery(
    root: pathlib.Path | str,
    staged_path: pathlib.Path | str,
    target_rel_path: str,
    target_sha256: str,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    catalog_rel_path: str,
    catalog_sha256: str,
    families: Iterable[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: list[str] | None,
    source_projection_base64: str,
    recovery_projection_base64: str,
    raw_recovery_preimage_evidence: Mapping[str, Any],
) -> "RegularFileSnapshot":
    """Authenticate a canonical staged replacement over a raw preimage.

    This path deliberately never parses an invalid line as authority. It
    rebinds the opaque target bytes by SHA, recomputes the deterministic
    recovery projection, preserves every selected reusable row byte-for-byte,
    then applies the same portfolio/source/semantic checks as normal writing.
    The returned snapshot is the only payload the caller may pass to CAS.
    """
    resolution = verify_writing_source_resolution(
        root, portfolio_rel_path, portfolio_sha256,
        catalog_rel_path, catalog_sha256, families, skip, take,
        expected_n, intent_ids, source_projection_base64)
    if (not isinstance(recovery_projection_base64, str) or
            len(recovery_projection_base64) >
            _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES * 2):
        raise ValueError("projeção raw-recovery inválida")
    try:
        encoded = recovery_projection_base64.encode("ascii")
        raw_projection = base64.b64decode(encoded, validate=True)
        if (len(raw_projection) > _MAX_SOURCE_RESOLUTION_PROJECTION_BYTES or
                base64.b64encode(raw_projection) != encoded):
            raise ValueError("projeção raw-recovery excede limite/canonical")
        projection = decode_json_no_duplicate_keys(
            raw_projection, "projeção raw-recovery")
    except (UnicodeEncodeError, UnicodeDecodeError, ValueError) as error:
        raise ValueError("projeção raw-recovery da fila é inválida") from error
    if not isinstance(projection, dict):
        raise ValueError("projeção raw-recovery não é objeto")

    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    target = read_writing_raw_recovery_preimage(
        canonical_root, raw_recovery_preimage_evidence, target_sha256)
    semantic_contract = load_writing_semantic_contract(canonical_root)
    expected = tuple(resolution.selected_intents)
    projection = validate_writing_raw_recovery_projection(
        projection, target_rel_path=target_rel_path,
        target_sha256=target_sha256, expected_intents=expected)
    selected_set = set(expected)
    misbound_semantic = sorted(
        intent for intent in expected
        if (intent in semantic_contract.requirement_fingerprints and
            semantic_contract.target_rel_paths[intent] != target_rel_path))
    if misbound_semantic:
        raise ValueError(
            "requisito semântico pertence a outro shard: " +
            ", ".join(misbound_semantic[:8]))
    blocked = selected_set & semantic_contract.unresolved_intents
    expected_projection = derive_writing_raw_recovery_projection(
        target.payload, target_rel_path, target_sha256, expected,
        semantically_blocked_intents=blocked)
    if expected_projection is None or projection != expected_projection:
        raise ValueError(
            "projeção raw-recovery diverge da preimagem/slice autenticados")
    staged = read_regular_file_snapshot(
        staged_path, max_bytes=64 * 1024 * 1024)
    if not staged.payload or not staged.payload.endswith(b"\n") or b"\r" in staged.payload:
        raise ValueError("staged raw-recovery não é JSONL LF canônico")
    raw_lines = staged.payload[:-1].split(b"\n")
    if len(raw_lines) != len(expected) or any(not line for line in raw_lines):
        raise ValueError(
            f"staged raw-recovery exige exatamente {len(expected)} linhas")
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw_lines, 1):
        row = decode_json_no_duplicate_keys(
            raw_line, f"staged raw-recovery:{line_number}")
        if not isinstance(row, dict):
            raise ValueError(
                f"staged raw-recovery não é objeto: {line_number}")
        rows.append(row)
    observed = tuple(row.get("intent_id") for row in rows)
    if observed != expected:
        raise ValueError(
            "ordem/cardinalidade raw-recovery diverge do slice autenticado")
    raw_by_intent = dict(zip(observed, raw_lines))
    preserved = projection["preserved_record_sha256"]
    if (not isinstance(preserved, dict) or
            set(preserved) != set(projection["reuse"])):
        raise ValueError("preservação raw-recovery não é fechada")
    changed = sorted(
        intent for intent, digest in preserved.items()
        if _sha256(raw_by_intent[intent]) != digest)
    if changed:
        raise ValueError(
            "raw-recovery alterou registro preservado: " +
            ", ".join(changed[:8]))
    unchanged_semantic = sorted(
        intent for intent in blocked
        if (semantic_contract.superseded_page_record_sha256[intent]
            is not None and
            _sha256(raw_by_intent[intent]) ==
            semantic_contract.superseded_page_record_sha256[intent]))
    if unchanged_semantic:
        raise ValueError(
            "raw-recovery repetiu página semanticamente superada: " +
            ", ".join(unchanged_semantic[:8]))

    strict = set(resolution.strict_source_intents)
    preserved_intents = set(preserved)
    for row in rows:
        intent = row["intent_id"]
        if row.get("skipped") is True:
            if (set(row) != {"intent_id", "skipped", "skip_reason"} or
                    not isinstance(row.get("skip_reason"), str) or
                    not row["skip_reason"].strip() or
                    row["skip_reason"] != row["skip_reason"].strip()):
                raise ValueError(
                    f"tombstone raw-recovery não é fechada: {intent}")
            continue
        if intent in preserved_intents:
            # Registro preservado byte a byte pelo raw-recovery: o hash já foi
            # autenticado acima contra ``preserved`` (que vem da preimagem em
            # disco, não do texto do redator) e ``writing_reusable_page`` já
            # exigiu página ativa com ``sections``. Espelha a rota ordinária
            # (``verify_staged_writing_preservation``, decisão de 2026-07-31):
            # schema de fonte, allowlist de URL e override do catálogo existem
            # para guiar ESCRITA NOVA; aplicá-los a uma linha que jamais será
            # reescrita reprovaria página publicada legítima (medido em
            # 2026-09-05: 171 páginas em 38 shards carregam URL repetida,
            # chave extra de proveniência ou host fora do allowlist atual) e
            # mandaria o redator reautorar texto pago. Linha NÃO preservada
            # segue abaixo com todos os gates de escrita nova.
            continue
        sources = row.get("official_sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(
                f"página raw-recovery sem official_sources: {intent}")
        actual_by_url: dict[str, Mapping[str, Any]] = {}
        for source_index, source in enumerate(sources, 1):
            canonical_source = _canonical_staged_official_source(
                source, f"official_sources:{intent}:{source_index}")
            url = canonical_source["url"]
            if url in actual_by_url:
                raise ValueError(
                    f"official_sources duplica URL em {intent}: {url}")
            actual_by_url[url] = canonical_source
        expected_by_hint = resolution.source_overrides.get(intent, {})
        if intent in strict and not expected_by_hint:
            raise ValueError(
                f"intent strict sem source_hints materializados: {intent}")
        expected_hints_by_url: dict[
            str, dict[str, Mapping[str, str]]
        ] = collections.defaultdict(dict)
        for hint, source in expected_by_hint.items():
            expected_hints_by_url[source["url"]][hint] = source
        for url, hints in expected_hints_by_url.items():
            expected_source = _canonical_consolidated_source(hints)
            actual_source = actual_by_url.get(url)
            actual_identity = (
                None if actual_source is None else {
                    field: actual_source.get(field)
                    for field in ("name", "url", "anchor_claim")})
            if actual_identity != expected_source:
                raise ValueError(
                    "fonte material diverge da consolidação exata: "
                    f"{intent}: {url}")
    verify_writing_semantic_contract_dependencies(
        canonical_root, semantic_contract)
    return staged


def review_addressable_invalid_tombstone_batch(
    records: Iterable[Mapping[str, Any]],
    expected_intents: Iterable[str],
    *,
    semantically_blocked_intents: Iterable[str] = (),
) -> bool:
    """Whether review can repair only malformed tombstones by exact row ID."""
    rows = tuple(records)
    expected = tuple(expected_intents)
    blocked = set(semantically_blocked_intents)
    if (not expected or blocked or len(rows) != len(expected) or
            tuple(row.get("intent_id") if isinstance(row, Mapping) else None
                  for row in rows) != expected):
        return False
    found_invalid_tombstone = False
    for row in rows:
        if row.get("skipped") is True:
            closed = (
                set(row) == {"intent_id", "skipped", "skip_reason"} and
                isinstance(row.get("skip_reason"), str) and
                bool(row["skip_reason"].strip()) and
                row["skip_reason"] == row["skip_reason"].strip())
            if not closed:
                found_invalid_tombstone = True
            continue
        if not row.get("sections"):
            return False
    return found_invalid_tombstone


def writing_reusable_page(row: Mapping[str, Any]) -> bool:
    """Decide se uma linha do shard pode entrar em ``reuse`` na fila de escrita.

    ``reuse`` é uma ORDEM ao redator: preservar a linha byte a byte
    (``preserved_record_sha256``) e não autorar nada para aquele intent. Só
    uma PÁGINA ATIVA — registro sem ``skipped`` e com ``sections`` — merece
    essa ordem: texto redigido foi pago pelo dono e nunca é reescrito por um
    redator de volume.

    Tombstone (``skipped: true`` + ``skip_reason``) NUNCA é reuse, qualquer
    que seja o motivo. Ela PREENCHE o slot do lote (``classify_batch_completion``
    a conta em ``filled``: o pulo honesto não reenfileira o lote nem
    pressiona fabricação), mas o bloqueio que ela registra é o da execução em
    que nasceu — o ``skip_reason`` vivo diz "nesta execução" e cita o hash do
    catálogo pinado do lote. Quando o lote reabre por qualquer motivo (linha
    faltante, ordem do slice), a fila recalcula ``source_overrides`` e
    ``strict_source_intents`` com o catálogo ATUAL, e o redator re-decide o
    slot de forma determinística: hint ainda não resolvido → a intenção é
    strict e o verificador staged só aceita outra tombstone fechada (zero
    fabricação); hints resolvidos → página com as fontes exatas do catálogo.
    Essa visita é o ÚNICO caminho orgânico para uma tombstone virar página:
    a fila de review não cria linha, e um lote completo não reabre por
    mudança de catálogo. Preservar a tombstone byte a byte congelaria o
    bloqueio para sempre — medido em 2026-09-05: o catálogo pinado dos lotes
    ``aereo-18`` e ``sucessoes2-09`` já resolvia todos os hints que as
    tombstones diziam não resolver, e a fila mandava preservá-las.

    A tombstone DEC-020 (``duplicate_intent_consolidated`` + ``superseded_by``)
    segue a mesma regra de reuse (nunca) e tem a SUA distinção em ``filled``,
    que exige vencedor autenticado.

    Este predicado é a fonte única de verdade: ``classify_batch_completion``
    (oráculo do fechamento da fila), ``verify_staged_writing_preservation``
    (rota ordinária) e ``derive_writing_raw_recovery_projection`` (rota
    raw-recovery, cujo ``reuse`` ``ops/relaunch-writing.sh`` copia para o
    lote) concordam por construção — dois produtores com definições próprias
    foi a causa-raiz do "reuse diverge da preimagem autenticada" em lotes
    vivos. ``skipped`` é lido por veracidade (qualquer marca de pulo exclui do
    reuse): mais conservador que ``is True`` e idêntico sobre o estoque vivo,
    onde o campo é sempre ``true`` ou ausente.

    O predicado responde QUAIS intents; a ORDEM tem uma segunda regra única, e
    esquecê-la deixou a mesma família meio corrigida por um dia: ``reuse`` sai
    SEMPRE na ordem do slice autenticado (``expected_intents``), nunca na
    ordem observada no shard. As duas rotas convergem aí — a raw-recovery por
    iterar ``for intent in expected``, o classificador por permutar o
    resultado da varredura em ``classify_batch_completion``. Um teste de
    igualdade entre os dois produtores só enxerga isso com DUAS ou mais
    páginas reusáveis fora de ordem: com uma só, qualquer ordenação passa.
    """
    return not row.get("skipped") and bool(row.get("sections"))


def classify_batch_completion(
    records: Iterable[Mapping[str, Any]],
    expected_intents: Iterable[str],
    target_shard: str,
    supersession_winners: Iterable[tuple[str, str]],
    authenticated_replacement_intents: Iterable[str] | None = None,
    *,
    semantically_blocked_intents: Iterable[str],
) -> BatchCompletion:
    """Classify a writing batch without discarding DEC-020 winners.

    Ordinarily a finalized shard must contain exactly the portfolio slice in
    its authenticated semantic order; DEC-020 winners, when present, form a
    suffix in their observed order.
    An active extra is preservable only when authenticated as the unique
    winner of one valid ``duplicate_intent_consolidated`` tombstone. A
    skipped extra is preservable only when it IS such a tombstone whose
    ``(superseded_by, intent_id)`` pair is an authenticated winner — the
    inventory may re-pin ownership to the shard holding the active bytes,
    but the tombstone stays in the source shard as mandatory evidence of
    the DEC-020 chain and must survive recomposition byte by byte. A full
    replacement is a separate exception: every observed intent must coincide,
    in order, with a preimage independently archived by the portfolio migration
    registry. Any other extra raises instead of being handed to a writer that
    could accidentally erase evolved content while rebuilding the slice.
    """
    target_path = pathlib.PurePosixPath(target_shard)
    if (target_path.name != target_shard or
            target_path.suffix != ".jsonl"):
        raise ValueError(f"nome de shard inválido: {target_shard}")
    expected_order = tuple(expected_intents)
    if (not expected_order or
            any(not isinstance(iid, str) or not iid.strip() or iid != iid.strip()
                for iid in expected_order) or
            len(set(expected_order)) != len(expected_order)):
        raise ValueError("intent_ids esperados devem ser únicos e canônicos")
    expected = set(expected_order)
    blocked_order = tuple(semantically_blocked_intents)
    if (len(set(blocked_order)) != len(blocked_order) or
            any(not isinstance(iid, str) or
                _INTENT_ID.fullmatch(iid) is None for iid in blocked_order) or
            not set(blocked_order).issubset(expected)):
        raise ValueError(
            "intent_ids bloqueados semanticamente devem ser únicos e do lote")
    semantically_blocked = set(blocked_order)
    record_list = tuple(records)
    if authenticated_replacement_intents is not None:
        retired_order = tuple(authenticated_replacement_intents)
        if (not retired_order or len(set(retired_order)) != len(retired_order) or
                any(not isinstance(iid, str) or not iid.strip() or
                    iid != iid.strip() for iid in retired_order) or
                set(retired_order) & expected):
            raise ValueError("intent_ids retirados devem ser únicos, canônicos e disjuntos")
        observed: list[str] = []
        for record in record_list:
            if not isinstance(record, Mapping):
                raise ValueError(f"registro não é objeto em {target_shard}")
            iid = record.get("intent_id")
            if not isinstance(iid, str) or not iid.strip() or iid != iid.strip():
                raise ValueError(f"registro sem intent_id canônico em {target_shard}")
            observed.append(iid)
        if tuple(observed) != retired_order:
            raise ValueError(
                f"preimagem não coincide com migração autenticada em {target_shard}")
        # A preimagem integral já foi preservada fora do estoque ativo. Nenhuma
        # linha antiga pode virar reuse ou extra silencioso: o CAS do workflow
        # substitui exatamente este snapshot pelas novas intenções.
        #
        # Este ``False`` não é defeito do shard: é ESTADO de substituição
        # autenticada. Sem um motivo aqui a invariante ``complete == (not
        # reasons)`` quebraria justamente no ramo em que o lote está correto.
        return BatchCompletion(
            False, (), (), ("substituicao_integral_autenticada",))
    winners = set(supersession_winners)
    occurrences: dict[str, int] = collections.Counter()
    filled: set[str] = set()
    reusable: list[str] = []
    extras: list[str] = []
    extra_seen: set[str] = set()
    observed_order: list[str] = []
    total = 0
    for record in record_list:
        total += 1
        if not isinstance(record, Mapping):
            raise ValueError(f"registro não é objeto em {target_shard}")
        iid = record.get("intent_id")
        if not isinstance(iid, str) or not iid.strip() or iid != iid.strip():
            raise ValueError(f"registro sem intent_id canônico em {target_shard}")
        observed_order.append(iid)
        if iid in expected:
            occurrences[iid] += 1
            if occurrences[iid] != 1:
                continue
            # Uma página estruturalmente válida pode responder ao recorte antigo
            # do mesmo ID. Até uma resolução exata ligar requisito e nova linha
            # revisada, ela não preenche o lote e jamais entra em ``reuse``.
            if iid in semantically_blocked:
                continue
            reason = record.get("skip_reason")
            if record.get("skipped") and isinstance(reason, str) and reason.strip():
                if (reason.strip() == "duplicate_intent_consolidated" and
                        (record.get("superseded_by"), iid) not in winners):
                    raise ValueError(
                        f"tombstone DEC-020 sem vencedor autenticado em "
                        f"{target_shard}: {iid}")
                filled.add(iid)
            # Tombstone preencheu o slot no ramo acima e NUNCA entra em
            # ``reuse``; página ativa preenche E é preservada byte a byte.
            # Predicado compartilhado com as outras rotas: ``writing_reusable_page``.
            elif writing_reusable_page(record):
                filled.add(iid)
                reusable.append(iid)
            continue
        if record.get("skipped"):
            # Tombstone DEC-020 fora do slice: quando o inventário re-pina a
            # posse do intent para o shard dos bytes ativos, o tombstone
            # permanece no shard de origem como evidência OBRIGATÓRIA da
            # cadeia (o gate Go exige exatamente o par tombstone na origem +
            # ativo no canônico). Ele autentica como extra preservável pela
            # MESMA chave de vencedor usada no ramo esperado; qualquer outro
            # registro pulado continua reprovando fail-closed.
            reason = record.get("skip_reason")
            if (isinstance(reason, str) and
                    reason.strip() == "duplicate_intent_consolidated" and
                    (record.get("superseded_by"), iid) in winners and
                    iid not in extra_seen):
                extra_seen.add(iid)
                extras.append(iid)
                continue
            raise ValueError(
                f"extra ativo sem supersessão única autenticada em "
                f"{target_shard}: {iid}")
        if (not record.get("sections") or
                (target_shard, iid) not in winners or iid in extra_seen):
            raise ValueError(
                f"extra ativo sem supersessão única autenticada em "
                f"{target_shard}: {iid}")
        extra_seen.add(iid)
        extras.append(iid)
    # A ULTIMA CLAUSULA COMPARA SO' AS PINADAS, e nao o arquivo inteiro
    # (2026-09-10). Ela dizia `tuple(observed_order) == expected_order +
    # tuple(extras)`, isto e', exigia que os extras DEC-020 formassem SUFIXO —
    # e o extra DEC-020 nao pode ser movido: o registro de arquivo prende
    # `source_line` e `canonical_line` aos dois lados
    # (audit_v2_pages.py:24425-24439). O gate pedia a migracao que outro gate
    # proibe. Ver a nota datada em `_batch_completion_reasons`, com o caso
    # medido (`imobiliario-22`: 12 pinadas na ordem exata do pin, dois
    # tombstones ancorados nas linhas 11 e 12).
    #
    # O que se compara agora e' a subsequencia das pinadas, na ordem em que
    # aparecem no arquivo, contra a ordem do pin. As outras quatro clausulas
    # ficam byte por byte como estavam: conjunto, ocorrencia unica,
    # preenchimento e cardinalidade continuam fechando o lote.
    pinadas_observadas = tuple(
        iid for iid in observed_order if iid not in set(extras))
    complete = (
        set(occurrences) == expected and
        all(count == 1 for count in occurrences.values()) and
        filled == expected and
        total == len(expected_order) + len(extras) and
        pinadas_observadas == expected_order
    )
    # A conjunção acima é a de sempre, cláusula por cláusula, byte por byte:
    # nada aqui afrouxa veredito. ``_batch_completion_reasons`` percorre as
    # MESMAS cinco cláusulas e devolve o que cada uma reprovou, com número.
    reasons = _batch_completion_reasons(
        expected_order=expected_order,
        expected=expected,
        occurrences=occurrences,
        filled=filled,
        semantically_blocked=semantically_blocked,
        observed_order=tuple(observed_order),
        extras=tuple(extras),
        total=total,
    )
    # ★ ORDEM CANÔNICA DE ``reuse``: O SLICE AUTENTICADO, NUNCA O SHARD.
    #
    # ``reusable`` nasce da varredura dos registros, logo na ordem OBSERVADA no
    # arquivo. Emitir o campo nessa ordem fazia os dois produtores da fila
    # divergirem em LISTA com o mesmo CONJUNTO, e não havia valor de ``reuse``
    # capaz de satisfazer os dois checks que o fechamento aplica ao MESMO
    # campo: ``verify_v2_writing_queue_closure.py:385`` exige igualdade com o
    # ``reuse`` da raw-recovery (``derive_writing_raw_recovery_projection``,
    # que itera ``for intent in expected``) e ``:833`` exige igualdade com este
    # ``reusable_expected``. Medido em 2026-09-05 no lote ``cidadania-04``: as
    # mesmas 3 páginas ativas, na posição 8/21/22 do slice e nas linhas
    # 20/21/22 do shard — "reuse diverge da preimagem autenticada" sem uma
    # única página de diferença.
    #
    # O desempate não é de gosto, e não é deste comentário: a ordem do slice
    # JÁ ERA a regra de schema em dois lugares independentes — o validador da
    # projeção (``validate_writing_raw_recovery_projection``, que levanta
    # "projeção raw-recovery tem identidade inválida" quando
    # ``reuse != [intent for intent in expected if intent in set(reuse)]``) e o
    # consumidor que EXECUTA a ordem (``scripts/workflows/writing-mass.js:419``,
    # que recusa qualquer ``reuse`` diferente de
    # ``expected_intent_ids.filter(...)``). O classificador era o único
    # produtor fora dessa regra. Faz sentido: quando as duas ordens divergem é
    # a ordem do SHARD que está com defeito — é exatamente o que o lote vai
    # reparar (``intent_order_mismatch``) — e derivar um campo do contrato da
    # corrupção que ele existe para desfazer é o defeito; o slice pinado é
    # autenticado, estável e idêntico para todos os produtores.
    #
    # É PERMUTAÇÃO, não filtro: mesmo conjunto, mesma cardinalidade, mesma
    # regra de ocorrência única. Nenhuma página deixa de ser preservada byte a
    # byte por causa desta linha — ``reuse`` ⊆ ``expected`` por construção
    # (só o ramo ``iid in expected`` alimenta ``reusable``).
    reusable_by_intent = set(reusable)
    return BatchCompletion(
        complete=complete,
        # A primeira ocorrência não vira reuse quando o mesmo intent aparece
        # outra vez: não existe registro único que possa ser preservado byte a
        # byte sem escolher silenciosamente entre versões concorrentes.
        reusable_expected=tuple(
            intent for intent in expected_order
            if intent in reusable_by_intent and occurrences[intent] == 1),
        authenticated_extras=tuple(extras),
        reasons=reasons,
    )


def _amostra(intents: Iterable[str], teto: int = 5) -> str:
    """Lista limitada e determinística: erro legível não é dump de lote."""
    ordenados = list(intents)
    cabeca = ", ".join(ordenados[:teto])
    if len(ordenados) > teto:
        cabeca += f", +{len(ordenados) - teto}"
    return cabeca


def _batch_completion_reasons(
    *,
    expected_order: tuple[str, ...],
    expected: set[str],
    occurrences: Mapping[str, int],
    filled: set[str],
    semantically_blocked: set[str],
    observed_order: tuple[str, ...],
    extras: tuple[str, ...],
    total: int,
) -> tuple[str, ...]:
    """Espelha as cinco cláusulas de ``complete`` e nomeia o que reprovou.

    Função PURA e aditiva — não decide nada, só explica. Prova da invariante
    ``complete == (not reasons)``, cláusula a cláusula:

    * ``set(occurrences) ⊆ expected`` por construção (só o ramo
      ``iid in expected`` incrementa), logo a cláusula 1 só falha com
      ``expected - set(occurrences)`` não vazio ⇒ emite ``linha_faltante``.
    * cláusula 2 falha ⇔ existe contagem ≠ 1 ⇒ emite ``intent_duplicado``.
    * ``filled ⊆ expected`` pela mesma construção; o que falta ou está ausente
      do shard (cláusula 1 já emitiu) ou está presente sem preencher — e aí é
      ``bloqueio_semantico`` (o contrato recusou o recorte antigo) ou
      ``corpo_nao_reusavel`` (``writing_reusable_page`` reprovou os bytes).
    * cláusula 4 é IMPLICADA por 1∧2 e não tem caso próprio: com todo esperado
      presente exatamente uma vez, ``sum(occurrences.values()) ==
      len(expected_order)``, e todo registro fora do slice ou levanta ou entra
      em ``extras`` uma única vez (``extra_seen``), logo ``total`` já é
      ``len(expected_order) + len(extras)``. Ela fica como rede defensiva,
      emitida só quando 1 e 2 passam — estado hoje inalcançável. Repeti-la
      junto de ``linha_faltante`` era ruído: a contagem de linhas do shard
      passou para dentro daquela mesma frase.
    * cláusula 5 só é reportada como ``ordem_divergente`` quando 1, 2 e 4
      passam: aí o multiconjunto observado é PROVADAMENTE igual a
      ``expected_order + extras``. Se 1, 2 ou 4 falharam, a ordem diferente é
      CONSEQUÊNCIA da linha que falta ou sobra, e anunciá-la como defeito
      próprio mandaria o operador reordenar um shard que precisa de redação.

    O ENCAMINHAMENTO dentro de ``ordem_divergente`` é medido, não genérico:
    ``tools/generate-v2-shard-slice-reorder`` exige
    ``writing_recovery_mechanical_only``, que reprova lote com extra DEC-020
    (``writing_raw_recovery_valid_extra_requires_migration``) e lote com
    intenção que não preenche. Medido em 2026-09-05 sobre os 40 lotes com o
    conjunto inteiro escrito: 32 mecânicos, 2 recusados por extra
    (``imobiliario-10``, ``imobiliario-22``) e 6 com bloqueio semântico.
    Mandar os 8 para a permutação mecânica é mandá-los para uma ferramenta que
    recusa — exatamente o erro de encaminhamento que esta função existe para
    acabar.

    POR QUE "exige migracao de portfolio" NAO E' FORCA DE EXPRESSAO, medido em
    2026-09-10 ao custo de uma escrita revertida: uma sessao leu este
    encaminhamento como burocracia e permutou ``imobiliario-22`` a mao — os
    dois extras sao TOMBSTONES DEC-020 (``skipped``,
    ``duplicate_intent_consolidated``, ``superseded_by: imobiliario-05.jsonl``)
    e a permutacao preservou cada linha byte a byte, multiset identico,
    ``classify_batch_completion`` aprovando o payload novo. Ainda assim
    ``validated_duplicate_supersession_winners`` passou de 0 para 2 problemas
    ``archive_record_metadata_invalid``: o registro de arquivo DEC-020 fixa
    ``source_line`` e ``canonical_line`` — o NUMERO DA LINHA de cada lado — e
    tambem ``source_shard_sha256`` (``audit_v2_pages.py:24425-24439``). Mover
    a linha invalida a atestacao, e corrigir os numeros a mao seria reescrever
    evidencia de auditoria sem re-verificar.

    Ou seja: com extra DEC-020 no shard, NENHUMA permutacao e' segura, dos
    dois lados (o tombstone na origem e o ativo no canonico estao ambos
    presos a linha). O conserto e' uma migracao acoplada shard+arquivo que
    re-verifica e re-carimba ``checked_at`` — e nao existe gerador de pe' para
    isso: os registros vieram de consolidacoes datadas
    (``tools/consolidate_v2_duplicate_intents_20260711.py``). O shard foi
    restaurado por CAS a partir da preimagem
    (``.agents/runtime/20260910-fila-escrita/``) e os problemas voltaram a 0.
    """
    razoes: list[str] = []
    faltantes = [iid for iid in expected_order if iid not in occurrences]
    if faltantes:
        razoes.append(
            f"linha_faltante={len(faltantes)} de {len(expected_order)} "
            f"(o shard tem {total} linha(s)): {_amostra(faltantes)}")
    # A cláusula 1 é ``set(occurrences) == expected``, uma igualdade de
    # CONJUNTOS, e a linha acima só cobre um dos lados (o que falta). O outro é
    # ``set(occurrences) - expected``: intenção contada como ocorrência sem
    # pertencer ao slice. Hoje isso é inalcançável — só o ramo ``iid in
    # expected`` incrementa ``occurrences`` (:3452) — e é justamente por isso
    # que a checagem entra: quando uma refatoração afrouxar aquele ramo, a
    # cláusula 1 passará a falhar por um motivo que esta função, olhando só
    # ``expected_order``, atribuiria em silêncio a ``ordem_divergente``,
    # mandando reordenar um shard que ganhou linha indevida.
    #
    # É também o único uso de ``expected`` — o parâmetro existe para que o
    # espelho das cinco cláusulas seja fiel à que está escrita, não a uma
    # aproximação por tupla. ``expected_order`` e ``expected`` divergiriam
    # tambem se o slice pinado repetisse uma intenção.
    intrusas = sorted(set(occurrences) - expected)
    if intrusas:
        razoes.append(
            f"intent_fora_do_slice={len(intrusas)} ({_amostra(intrusas)}) "
            f"— contado como ocorrencia sem pertencer ao slice pinado")
    duplicados = [iid for iid in expected_order if occurrences.get(iid, 0) > 1]
    if duplicados:
        razoes.append(
            f"intent_duplicado={len(duplicados)} ({_amostra(duplicados)})")
    nao_preenchidos = [
        iid for iid in expected_order
        if iid in occurrences and iid not in filled]
    bloqueados = [iid for iid in nao_preenchidos if iid in semantically_blocked]
    sem_corpo = [iid for iid in nao_preenchidos
                 if iid not in semantically_blocked]
    if bloqueados:
        razoes.append(
            f"bloqueio_semantico={len(bloqueados)} ({_amostra(bloqueados)}) "
            f"— recorte novo do contrato semantico, nao redacao")
    if sem_corpo:
        razoes.append(
            f"corpo_nao_reusavel={len(sem_corpo)} ({_amostra(sem_corpo)})")
    esperado_total = len(expected_order) + len(extras)
    if total != esperado_total and not faltantes and not duplicados:
        razoes.append(
            f"cardinalidade: {total} linha(s) no shard para "
            f"{len(expected_order)} do slice + {len(extras)} extra(s) "
            f"autenticado(s)")
    canonico = expected_order + extras
    # A ORDEM QUE E' CONTRATO E' A DAS PINADAS ENTRE SI, e nao a posicao
    # absoluta de cada linha no arquivo (2026-09-10). O paragrafo anterior
    # desta docstring — "DEC-020 winners, when present, form a suffix" — fica
    # SUPERADO nesta data, com o motivo medido, e nao se apaga: ele descrevia o
    # layout que `tools/generate-v2-shard-slice-reorder` PRODUZ, e virou regra
    # de aceitacao sem que ninguem tivesse decidido isso.
    #
    # O extra DEC-020 nao pode ser movido. O registro de arquivo fixa
    # `source_line`, `canonical_line` e `source_shard_sha256`
    # (audit_v2_pages.py:24425-24439): o numero da linha e' evidencia de
    # auditoria dos dois lados, e uma sessao ja pagou por descobrir isso —
    # permutou `imobiliario-22` preservando cada linha byte a byte, com o
    # multiset identico, e `validated_duplicate_supersession_winners` foi de 0
    # a 2 `archive_record_metadata_invalid`.
    #
    # Exigir o sufixo era, portanto, exigir uma migracao que o proprio sistema
    # declara insegura — gate pedindo o que outro gate proibe. Medido em
    # `imobiliario-22`: as 12 intencoes pinadas estao nas linhas 1-10, 13 e 14,
    # EXATAMENTE na ordem do pin; os dois tombstones (`superseded_by:
    # imobiliario-05.jsonl`) ocupam as linhas 11 e 12. O lote esta completo, e
    # a unica coisa "divergente" era a ancora de auditoria no meio dele.
    #
    # O que continua sendo cobrado, e e' o que importa: toda pinada presente
    # uma vez (clausula 1 e 2), cardinalidade fechada (clausula 4) e as
    # pinadas na ordem do pin quando se leem SO' elas. Extra nao autenticado
    # nunca chega aqui — `extras` so' recebe o que passou pela autenticacao
    # DEC-020 mais acima.
    fora_do_pin = set(extras)
    # `list(...)` nas duas pontas: `expected_order` chega como tupla e
    # `observed_order` como lista, e `[] != ()` e' sempre verdadeiro em Python.
    # Sem isto a clausula disparava com zero posicoes divergentes.
    observado_pinado = [iid for iid in observed_order if iid not in fora_do_pin]
    ordem_do_pin = list(expected_order)
    if (not faltantes and not duplicados and total == esperado_total and
            observado_pinado != ordem_do_pin):
        divergentes = sum(
            1 for observado, esperado in zip(observado_pinado, ordem_do_pin)
            if observado != esperado)
        primeira = next(
            (posicao for posicao, (observado, esperado)
             in enumerate(zip(observado_pinado, ordem_do_pin), 1)
             if observado != esperado), 0)
        if extras:
            encaminhamento = (
                f"{len(extras)} extra(s) DEC-020 autenticado(s) ancorado(s) "
                f"por linha: a reordenacao mecanica RECUSA o lote "
                f"(writing_raw_recovery_valid_extra_requires_migration), e a "
                f"permutacao a mao invalida o registro de arquivo")
        elif bloqueados or sem_corpo:
            encaminhamento = (
                "reordenar NAO basta: o lote tambem tem intencao bloqueada "
                "pelo contrato semantico ou sem corpo utilizavel, e o "
                "predicado mecanico recusa enquanto isso durar")
        else:
            encaminhamento = (
                "permutacao pura, zero redacao "
                "(tools/generate-v2-shard-slice-reorder)")
        razoes.append(
            f"ordem_divergente={divergentes} de {len(ordem_do_pin)} "
            f"posicao(oes) do pin (o shard tem {len(canonico)} linha(s) "
            f"contando os extras); a {primeira}ª pinada e' "
            f"{observado_pinado[primeira - 1]!r} onde o pin manda "
            f"{ordem_do_pin[primeira - 1]!r} — {encaminhamento}")
    return tuple(razoes)


# Razões de raw-recovery cuja reconstrução preserva TODAS as linhas do slice
# byte a byte: o defeito é apenas de ENQUADRAMENTO do arquivo (ordem das
# linhas vs slice pinado; LF terminal ausente). A reconstrução é uma
# permutação determinística das mesmas linhas + framing canônico — nunca
# autoria. Qualquer outra razão (linha JSON inválida, linha sem identidade,
# duplicata, cardinalidade divergente, CR não canônico) implica linha a
# reconstruir/decidir e continua exigindo redator. Razão futura desconhecida
# cai OBRIGATORIAMENTE do lado da autoria (fail-closed via subset).
_WRITING_RECOVERY_MECHANICAL_REASONS = frozenset({
    "intent_order_mismatch",
    "missing_terminal_lf",
})


def writing_recovery_mechanical_only(
    writing_recovery: Any, expected_n: int) -> bool:
    """True quando a raw-recovery é 100% mecânica (zero autoria).

    Mecânica ⟺ toda linha esperada do slice já existe, é única, endereçável e
    reprovou apenas por enquadramento do ARQUIVO (``intent_order_mismatch`` /
    ``missing_terminal_lf``): ``invalid_rows==0``, ``unaddressable_rows==0``,
    ``parsed_object_rows==raw_lines_seen==expected_n`` e ``reuse`` cobrindo o
    slice inteiro com ``preserved_record_sha256`` por linha. Nesse estado a
    única mutação legal é permutar as MESMAS linhas para a ordem do slice e
    fechar com LF terminal — transformação determinística CAS
    (``tools/generate-v2-shard-slice-reorder``), jamais um redator LLM (o
    contrato o proíbe de alterar qualquer byte preservado; chamá-lo garante
    ``written=0`` → hard-fail no ``wellFormedBatchProgress`` → circuit
    breaker). Função pura e fail-closed: qualquer campo ausente, contador
    inconsistente ou razão fora do conjunto mecânico devolve False e o lote
    segue o caminho de autoria de sempre. NÃO afrouxa gate nenhum — um lote
    com QUALQUER linha a reconstruir (``invalid_rows>0``,
    ``unaddressable_rows>0``, duplicata, cardinalidade) continua autoria.
    """
    if (not isinstance(expected_n, int) or isinstance(expected_n, bool) or
            expected_n <= 0):
        return False
    if not isinstance(writing_recovery, Mapping):
        return False
    reasons = writing_recovery.get("reason_codes")
    reuse = writing_recovery.get("reuse")
    preserved = writing_recovery.get("preserved_record_sha256")
    expected_ids = writing_recovery.get("expected_intent_ids")
    if (not isinstance(reasons, list) or not reasons or
            any(not isinstance(reason, str) for reason in reasons) or
            not set(reasons) <= _WRITING_RECOVERY_MECHANICAL_REASONS):
        return False
    for counter in ("invalid_rows", "unaddressable_rows"):
        value = writing_recovery.get(counter)
        if type(value) is not int or value != 0:
            return False
    for counter in ("expected_n", "parsed_object_rows", "raw_lines_seen"):
        value = writing_recovery.get(counter)
        if type(value) is not int or value != expected_n:
            return False
    if (not isinstance(expected_ids, list) or
            len(expected_ids) != expected_n or
            len(set(expected_ids)) != expected_n or
            any(not isinstance(intent, str) or
                _INTENT_ID.fullmatch(intent) is None
                for intent in expected_ids)):
        return False
    if (not isinstance(reuse, list) or len(reuse) != expected_n or
            len(set(reuse)) != expected_n or
            set(reuse) != set(expected_ids)):
        return False
    if (not isinstance(preserved, Mapping) or
            set(preserved) != set(reuse) or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in preserved.values())):
        return False
    return True


def writer_noop_batch(
    reusable_expected: Iterable[str],
    expected_n: int,
    *,
    semantic_relocation_removals: Iterable[Any] = (),
    authenticated_replacement: bool = False,
    writing_recovery: Any = None,
) -> bool:
    """True quando o redator não teria NADA a autorar (no-op byte-idêntico).

    Um lote de escrita só é no-op quando o slice inteiro já está materializado
    no shard — ``reusable_expected`` (o ``reuse`` do lote) cobre os
    ``expected_n`` intents esperados — e não resta AUTORIA para um redator:
    nenhuma remoção de relocação semântica (que apaga linhas), nenhuma
    substituição/migração integral autenticada e nenhuma reconstrução
    raw-recovery que reescreva/decida linha (linha corrompida, sem identidade,
    duplicada ou faltante). Uma raw-recovery PURAMENTE MECÂNICA
    (``writing_recovery_mechanical_only``: só ordem do slice/LF terminal, com
    todas as linhas preservadas byte a byte) NÃO constitui autoria — a mera
    presença do objeto ``writing_recovery`` não basta para emitir redator; a
    resolução dessa família é a permutação determinística CAS
    (``tools/generate-v2-shard-slice-reorder``), nunca um agente LLM proibido
    de alterar os bytes que deveria "reescrever". O contrato da fila obriga a
    PRESERVAR cada página reusada byte a byte (``preserved_record_sha256`` no
    CAS), logo um lote reuse==n sem autoria pendente não pode autorar nem
    corrigir nada: o staged sairia idêntico ao alvo
    (``audited_sha256 == target_sha256``) — ou, no caso mecânico, o redator
    honesto reporta ``written=0`` — e jamais satisfaz o
    ``wellFormedBatchProgress`` do consumidor: hard-fail garantido que
    alimenta o circuit breaker. A fila deve RESOLVER esse lote sem agente;
    defeitos de qualidade das páginas existentes seguem pela fila de review,
    nunca por um redator de volume proibido de tocá-las. Função pura (sem
    I/O), aditiva: não afrouxa nenhum gate — apenas evita emitir trabalho
    incapaz de progredir. É PROIBIDO (e este predicado garante) marcar como
    no-op um lote com qualquer linha a reconstruir.
    """
    if (not isinstance(expected_n, int) or isinstance(expected_n, bool) or
            expected_n < 0):
        raise ValueError("expected_n deve ser inteiro não negativo")
    # Qualquer mutação estrutural pendente = trabalho real → NÃO é no-op.
    # Raw-recovery só conta como trabalho de REDATOR quando exige autoria:
    # a família mecânica (ordem/LF, linhas 100% preservadas) resolve-se por
    # transformação determinística, sem agente.
    if authenticated_replacement:
        return False
    if writing_recovery is not None and not writing_recovery_mechanical_only(
            writing_recovery, expected_n):
        return False
    if tuple(semantic_relocation_removals):
        return False
    reuse = tuple(reusable_expected)
    if any(not isinstance(intent, str) or _INTENT_ID.fullmatch(intent) is None
           for intent in reuse):
        raise ValueError("reusable_expected deve conter intents canônicos")
    if len(set(reuse)) != len(reuse):
        raise ValueError("reusable_expected não pode repetir intent")
    if writing_recovery is not None:
        # O reuse do LOTE precisa ser exatamente o reuse da recovery mecânica:
        # divergência = fila inconsistente → caminho de autoria (fail-closed).
        recovery_reuse = writing_recovery.get("reuse")
        if (not isinstance(recovery_reuse, list) or
                set(reuse) != set(recovery_reuse) or
                len(reuse) != len(recovery_reuse)):
            return False
    # No-op ⟺ o reuse já cobre todo o slice esperado e nada mais precisa ser
    # escrito. expected_n>0 evita marcar um lote vazio como resolvido.
    return expected_n > 0 and len(reuse) == expected_n


def _parse_ngram_target(raw_target: str) -> tuple[str, str]:
    """Parse the auditor's symmetric ``intent~peer`` edge notation."""
    if raw_target.count("~") != 1:
        raise ValueError(f"aresta ngram inválida: {raw_target!r}")
    current, peer = raw_target.split("~", 1)
    if (not current or not peer or current != current.strip() or
            peer != peer.strip() or ":" in current or ":" in peer):
        raise ValueError(f"aresta ngram inválida: {raw_target!r}")
    return current, peer


def _deterministic_vertex_cover(
    edges: set[tuple[str, tuple[str, str], tuple[str, str]]],
    *,
    node_key: Any,
    immutable: set[tuple[str, str]],
    forced: set[tuple[str, str]],
    fail_on_immutable_only: bool,
) -> dict[
    tuple[str, tuple[str, str], tuple[str, str]], tuple[str, str]
]:
    """Greedy max-degree cover in O((V+E) log V), with stable tie breaks."""
    residual = set(edges)
    assigned: dict[
        tuple[str, tuple[str, str], tuple[str, str]], tuple[str, str]
    ] = {}
    adjacency: dict[
        tuple[str, str], set[
            tuple[str, tuple[str, str], tuple[str, str]]
        ]
    ] = collections.defaultdict(set)
    for edge in residual:
        adjacency[edge[1]].add(edge)
        adjacency[edge[2]].add(edge)
    nodes = sorted(adjacency, key=node_key)
    rank = {node: index for index, node in enumerate(nodes)}
    heap: list[tuple[int, int, tuple[str, str]]] = []

    def push(node: tuple[str, str]) -> None:
        if node not in immutable and adjacency[node]:
            heapq.heappush(
                heap, (-len(adjacency[node]), -rank[node], node))

    def cover(
        edge: tuple[str, tuple[str, str], tuple[str, str]],
        target: tuple[str, str],
    ) -> None:
        if edge not in residual:
            return
        residual.remove(edge)
        assigned[edge] = target
        for endpoint in edge[1:]:
            adjacency[endpoint].discard(edge)
            push(endpoint)

    for edge in sorted(edges):
        preferred = sorted(
            (node for node in edge[1:]
             if node in forced and node not in immutable),
            key=node_key)
        if preferred:
            cover(edge, preferred[-1])
    for node in nodes:
        push(node)
    while residual:
        target = None
        while heap:
            negative_degree, negative_rank, candidate = heapq.heappop(heap)
            if (candidate in immutable or not adjacency[candidate] or
                    -negative_degree != len(adjacency[candidate]) or
                    -negative_rank != rank[candidate]):
                continue
            target = candidate
            break
        if target is None:
            if fail_on_immutable_only:
                blocked = sorted(
                    f"{first[0]}:{first[1]}~{second[0]}:{second[1]}"
                    for _, first, second in residual)
                sample = blocked[:32]
                raise ValueError(
                    "componente relacional pertence só à fila de escrita: " +
                    f"total={len(blocked)} sample={','.join(sample)}")
            break
        for edge in tuple(adjacency[target]):
            cover(edge, target)
    return assigned


def _record_target_from_finding(raw_target: str) -> str:
    return raw_target.split("~", 1)[0].split(":", 1)[0]


def writing_recovery_findings(
    result: Mapping[str, Any],
    *,
    expected_pages: int | None = None,
) -> dict[str, list[str]]:
    """Return canonical shard-recovery findings, never editorial authority.

    ``audit_global`` authenticates the raw-file/JSON findings but does not know
    each portfolio slice cardinality.  For that one invariant the caller
    supplies the authenticated inventory count and this adapter combines it
    with the auditor's captured ``pages`` counter.  Any contradictory finding
    fails closed instead of being normalized into a task.
    """
    if not isinstance(result, Mapping):
        raise ValueError("resultado de recovery deve ser mapping")
    defects = result.get("defects")
    if not isinstance(defects, Mapping):
        raise ValueError("resultado de recovery sem defeitos")
    pages = result.get("pages")
    if not isinstance(pages, int) or isinstance(pages, bool) or pages < 0:
        raise ValueError("resultado de recovery sem pages canônico")
    if (expected_pages is not None and
            (not isinstance(expected_pages, int) or
             isinstance(expected_pages, bool) or expected_pages < 1)):
        raise ValueError("expected_pages de recovery inválido")

    findings: dict[str, list[str]] = {}
    for defect_class, pattern in WRITING_RECOVERY_DEFECT_TARGETS.items():
        raw_targets = defects.get(defect_class, [])
        if (not isinstance(raw_targets, list) or
                any(not isinstance(target, str) or
                    pattern.fullmatch(target) is None
                    for target in raw_targets) or
                len(raw_targets) != len(set(raw_targets))):
            details = (
                [f"{defect_class}:{target}" for target in raw_targets]
                if isinstance(raw_targets, list) else
                [f"{defect_class}:non_list"]
            )
            raise DistinctnessOperationalError(
                ("writing_recovery_finding_invalid",), (),
                details,
            )
        if raw_targets:
            findings[defect_class] = sorted(raw_targets)

    for defect_class, recovery_targets in (
            WRITING_RECOVERY_UNADDRESSABLE_TARGETS.items()):
        raw_targets = defects.get(defect_class, [])
        if not isinstance(raw_targets, list) or any(
                not isinstance(target, str) for target in raw_targets):
            raise ValueError(
                f"alvos não canônicos em {defect_class}")
        selected = sorted(set(raw_targets) & set(recovery_targets))
        if selected:
            findings[defect_class] = selected

    if expected_pages is not None:
        expected_finding = f"esperado={expected_pages} real={pages}"
        observed_count = findings.get("contagem", [])
        if pages == expected_pages:
            if observed_count:
                raise DistinctnessOperationalError(
                    ("writing_recovery_count_contradiction",), (),
                    observed_count,
                )
        elif observed_count and observed_count != [expected_finding]:
            raise DistinctnessOperationalError(
                ("writing_recovery_count_contradiction",), (),
                [*observed_count, expected_finding],
            )
        elif not observed_count:
            findings["contagem"] = [expected_finding]
    return {key: findings[key] for key in sorted(findings)}


def validate_review_scopes(
    report: Mapping[str, Any],
    intent_locations: Mapping[tuple[str, str], int],
) -> dict[str, ReviewScope]:
    """Authenticate every record-level target without file-wide fallback.

    A finding that does not resolve to the exact shard/intent is not authority
    to edit every line. Raw JSON/framing/cardinality findings belong to the
    authenticated writing/recovery route and therefore project zero editorial
    targets here; ``build_todo`` proves that their shard has that owner.
    """
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    locations: dict[tuple[str, str], int] = {}
    lines_by_file: dict[str, set[int]] = collections.defaultdict(set)
    for node, line_number in intent_locations.items():
        if (not isinstance(node, tuple) or len(node) != 2 or
                not _canonical_review_shard(node[0]) or
                not isinstance(node[1], str) or
                _INTENT_ID.fullmatch(node[1]) is None or
                type(line_number) is not int or line_number < 1 or
                node in locations or
                line_number in lines_by_file[node[0]]):
            raise ValueError(
                f"localização de escopo de revisão inválida: {node!r}")
        locations[node] = line_number
        lines_by_file[node[0]].add(line_number)

    scopes: dict[str, ReviewScope] = {}
    for filename, result in files.items():
        if (not _canonical_review_shard(filename) or
                not isinstance(result, Mapping)):
            raise ValueError(f"resultado de revisão inválido: {filename!r}")
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            raise ValueError(f"defeitos inválidos para {filename}")
        recovery = writing_recovery_findings(result)
        if recovery:
            scopes[filename] = ReviewScope(False, ())
            continue
        targets: set[str] = set()
        for defect_class, raw_targets in defects.items():
            if not isinstance(defect_class, str):
                raise ValueError(
                    f"classe de defeito inválida em {filename}")
            if defect_class == "skipped":
                continue
            if (not isinstance(raw_targets, list) or
                    not all(isinstance(target, str) and target
                            for target in raw_targets) or
                    len(raw_targets) != len(set(raw_targets))):
                raise ValueError(
                    f"alvos inválidos em {filename}:{defect_class}")
            if not raw_targets:
                continue
            for raw_target in raw_targets:
                candidate = _record_target_from_finding(raw_target)
                if (_INTENT_ID.fullmatch(candidate) is None or
                        (filename, candidate) not in locations):
                    raise DistinctnessOperationalError(
                        ("review_scope_record_target_unresolved",),
                        (filename,),
                        (f"{defect_class}:{raw_target}",),
                    )
                targets.add(candidate)
        ordered = tuple(sorted(
            targets, key=lambda intent: (locations[(filename, intent)], intent)))
        scopes[filename] = ReviewScope(False, ordered)
    return scopes


def plan_ngram_repairs(
    report: Mapping[str, Any],
    intent_locations: Mapping[tuple[str, str], int],
    writing_owned: Iterable[str],
    eligible_paths: Iterable[str] | None = None,
    review_scope_locations: Mapping[tuple[str, str], int] | None = None,
) -> dict[tuple[str, str], list[str]]:
    """Collapse symmetric n-gram defects into one deterministic repair side.

    ``audit_global`` intentionally reports both A~B and B~A so both product
    records remain blocked.  A repair queue cannot hand those two directions
    to independent reviewers: each would be told that the other page is the
    original owner.  This planner validates the symmetric graph, computes a
    deterministic vertex cover, and emits every undirected edge exactly once.

    Pages already editable because of another defect are preferred.  Shards
    owned by the writing queue are immutable here, preserving the mutual
    exclusion between writing and review.  Any ambiguous or asymmetric graph
    aborts queue production instead of silently hiding a product defect.
    """
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    validate_review_scopes(
        report,
        intent_locations if review_scope_locations is None
        else review_scope_locations,
    )
    locations: dict[tuple[str, str], int] = {}
    by_intent: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for node, line_number in intent_locations.items():
        if (not isinstance(node, tuple) or len(node) != 2 or
                not all(isinstance(value, str) and value for value in node) or
                not isinstance(line_number, int) or isinstance(line_number, bool) or
                line_number < 1 or node in locations):
            raise ValueError(f"localização de intent inválida: {node!r}")
        locations[node] = line_number
        by_intent[node[1]].append(node)
    if not locations:
        if any(
            isinstance(result, Mapping) and
            isinstance(result.get("defects"), Mapping) and
            any(result["defects"].get(name) for name in NGRAM_DEFECT_CLASSES)
            for result in files.values()
        ):
            raise ValueError("arestas ngram exigem localizações autenticadas")
        return {}

    writing_owned = set(writing_owned)
    eligible = None if eligible_paths is None else set(eligible_paths)
    immutable = {
        node for node in locations
        if pathlib.PurePosixPath(node[0]).stem in writing_owned
    }
    forced: set[tuple[str, str]] = set()
    directed: set[
        tuple[str, tuple[str, str], tuple[str, str]]
    ] = set()

    for filename, result in files.items():
        if not isinstance(filename, str) or not isinstance(result, Mapping):
            raise ValueError("arquivo/resultado inválido no relatório")
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            raise ValueError(f"defeitos inválidos para {filename}")
        recovery = writing_recovery_findings(result)
        for defect_class, raw_targets in defects.items():
            if not isinstance(raw_targets, list) or not all(
                isinstance(target, str) for target in raw_targets
            ):
                raise ValueError(
                    f"alvos inválidos em {filename}:{defect_class}"
                )
            if defect_class not in NGRAM_DEFECT_CLASSES:
                if defect_class == "skipped":
                    continue
                # O shard integral pertence ao recovery. Seus defeitos locais
                # não ampliam escopo nem forçam vértices editoriais; arestas
                # n-gram ainda são validadas abaixo para manter o grafo global.
                if recovery:
                    continue
                # validate_review_scopes already bound every finding to this
                # exact shard. Never reinterpret an unresolved target as
                # permission to rewrite all records.
                for raw_target in raw_targets:
                    candidate = _record_target_from_finding(raw_target)
                    forced.add((filename, candidate))
                continue
            for raw_target in raw_targets:
                current_intent, peer_intent = _parse_ngram_target(raw_target)
                current = (filename, current_intent)
                if current not in locations:
                    raise ValueError(
                        f"endpoint ngram ausente: {filename}:{current_intent}"
                    )
                if defect_class == "ngram_dup":
                    peer = (filename, peer_intent)
                    if peer not in locations:
                        raise ValueError(
                            f"peer ngram local ausente: {filename}:{peer_intent}"
                        )
                else:
                    current_candidates = by_intent.get(current_intent, ())
                    peer_candidates = by_intent.get(peer_intent, ())
                    if len(current_candidates) != 1 or len(peer_candidates) != 1:
                        raise DistinctnessOperationalError(
                            ("review_ngram_global_endpoint_ambiguous",),
                            sorted({
                                filename,
                                *(node[0] for node in current_candidates),
                                *(node[0] for node in peer_candidates),
                            }),
                            (f"{current_intent}~{peer_intent}",),
                        )
                    peer = peer_candidates[0]
                    if peer[0] == filename:
                        raise ValueError(
                            f"aresta ngram global no mesmo shard: {raw_target}"
                        )
                if current == peer:
                    raise ValueError(f"self-loop ngram inválido: {raw_target}")
                directed.add((defect_class, current, peer))

    for defect_class, current, peer in directed:
        if (defect_class, peer, current) not in directed:
            raise ValueError(
                "aresta ngram sem reverso simétrico: "
                f"{current[0]}:{current[1]}~{peer[0]}:{peer[1]}"
            )

    edges = {
        (defect_class,) + tuple(sorted((current, peer)))
        for defect_class, current, peer in directed
        if eligible is None or (
            current[0] in eligible and peer[0] in eligible)
    }
    def node_key(node: tuple[str, str]) -> tuple[str, int, str]:
        return node[0], locations[node], node[1]

    assigned = _deterministic_vertex_cover(
        edges, node_key=node_key, immutable=immutable, forced=forced,
        fail_on_immutable_only=True)

    planned: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for edge in sorted(edges):
        defect_class, first, second = edge
        target = assigned.get(edge)
        if target is None:
            raise ValueError(f"aresta ngram sem target: {edge!r}")
        peer = second if target == first else first
        planned[(target[0], defect_class)].append(
            f"{target[1]}~{peer[1]}"
        )
    return {
        key: sorted(set(values)) for key, values in planned.items()
    }


def validate_ngram_evidence(
    report: Mapping[str, Any],
    intent_locations: Mapping[tuple[str, str], int],
) -> dict[tuple[str, str], dict[str, dict[str, str]]]:
    """Authenticate a one-to-one evidence record for every directed edge.

    The repair planner deliberately assigns only one side of each symmetric
    product defect, but filtering must not hide malformed evidence on the
    other side.  Validate the complete auditor graph first: every directed
    defect has exactly one complete evidence record, no evidence target is
    extra, and the reverse record carries the same normalized phrase with the
    target/peer fields swapped.  The queue can then select its assigned side
    without weakening the auditor's symmetric blocking semantics.
    """
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    by_intent: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for node in intent_locations:
        if (not isinstance(node, tuple) or len(node) != 2 or
                not all(isinstance(value, str) and value for value in node)):
            raise ValueError(f"localização de intent inválida: {node!r}")
        by_intent[node[1]].append(node)

    validated: dict[
        tuple[str, str], dict[str, dict[str, str]]
    ] = {}
    for filename, result in files.items():
        if not isinstance(filename, str) or not isinstance(result, Mapping):
            raise ValueError("arquivo/resultado inválido no relatório")
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            raise ValueError(f"defeitos inválidos para {filename}")
        raw_evidence = result.get("evidence", {})
        if raw_evidence is None:
            raw_evidence = {}
        if not isinstance(raw_evidence, Mapping):
            raise ValueError(f"evidências inválidas para {filename}")
        for defect_class in NGRAM_DEFECT_CLASSES:
            raw_targets = defects.get(defect_class, [])
            if not isinstance(raw_targets, list) or not all(
                isinstance(target, str) for target in raw_targets
            ):
                raise ValueError(
                    f"alvos inválidos em {filename}:{defect_class}"
                )
            target_counts = collections.Counter(raw_targets)
            duplicated_targets = sorted(
                target for target, count in target_counts.items() if count != 1)
            if duplicated_targets:
                raise ValueError(
                    "alvo ngram duplicado no relatório em "
                    f"{filename}:{defect_class}:" +
                    ",".join(duplicated_targets)
                )
            expected_targets = set(raw_targets)
            entries = raw_evidence.get(defect_class, [])
            if not isinstance(entries, list) or not all(
                isinstance(entry, Mapping) for entry in entries
            ):
                raise ValueError(
                    f"evidências inválidas em {filename}:{defect_class}"
                )
            by_target: dict[str, dict[str, str]] = {}
            for entry in entries:
                evidence_target = entry.get("target")
                if not isinstance(evidence_target, str):
                    raise ValueError(
                        "target de evidência ngram inválido em "
                        f"{filename}:{defect_class}"
                    )
                if evidence_target not in expected_targets:
                    raise ValueError(
                        "target extra de evidência ngram em "
                        f"{filename}:{defect_class}:{evidence_target}"
                    )
                if evidence_target in by_target:
                    raise ValueError(
                        "evidência ngram duplicada em "
                        f"{filename}:{defect_class}:{evidence_target}"
                    )
                normalized = {
                    key: entry.get(key) for key in (
                        "target", "phrase", "field", "peer_field")
                }
                if not all(
                    isinstance(value, str) and value and value == value.strip()
                    for value in normalized.values()
                ):
                    raise ValueError(
                        "evidência ngram incompleta em "
                        f"{filename}:{defect_class}:{evidence_target}"
                    )
                if (len(normalized["phrase"].split()) !=
                        NGRAM_EVIDENCE_WORDS or
                        normalized["phrase"] != " ".join(
                            normalized["phrase"].split()) or
                        NGRAM_EVIDENCE_FIELD_RE.fullmatch(
                            normalized["field"]) is None or
                        NGRAM_EVIDENCE_FIELD_RE.fullmatch(
                            normalized["peer_field"]) is None):
                    raise ValueError(
                        "evidência ngram inconsistente em "
                        f"{filename}:{defect_class}:{evidence_target}"
                    )
                by_target[evidence_target] = normalized
            missing = expected_targets - set(by_target)
            if missing:
                raise ValueError(
                    "alvo ngram sem evidência autenticada em "
                    f"{filename}:{defect_class}:" + ",".join(sorted(missing))
                )
            if by_target:
                validated[(filename, defect_class)] = by_target

    for (filename, defect_class), entries in validated.items():
        for raw_target, evidence in entries.items():
            current_intent, peer_intent = _parse_ngram_target(raw_target)
            if defect_class == "ngram_dup":
                peer_file = filename
            else:
                current_candidates = by_intent.get(current_intent, ())
                peer_candidates = by_intent.get(peer_intent, ())
                if len(current_candidates) != 1 or len(peer_candidates) != 1:
                    raise ValueError(
                        "endpoint de evidência ngram global ausente ou ambíguo: "
                        f"{raw_target}"
                    )
                if current_candidates[0][0] != filename:
                    raise ValueError(
                        "target de evidência ngram fora do shard: "
                        f"{filename}:{raw_target}"
                    )
                peer_file = peer_candidates[0][0]
            reverse_target = f"{peer_intent}~{current_intent}"
            reverse = validated.get(
                (peer_file, defect_class), {}).get(reverse_target)
            if reverse is None:
                raise ValueError(
                    "evidência ngram sem reverso simétrico em "
                    f"{filename}:{defect_class}:{raw_target}"
                )
            if (evidence["phrase"] != reverse["phrase"] or
                    evidence["field"] != reverse["peer_field"] or
                    evidence["peer_field"] != reverse["field"]):
                raise ValueError(
                    "evidência ngram diverge do reverso em "
                    f"{filename}:{defect_class}:{raw_target}"
                )
    return validated


def legacy_ngram_global_dependency_paths(
    filename: str,
    assigned_targets: Iterable[str],
    intent_locations: Mapping[tuple[str, str], int],
) -> set[str]:
    """Resolve every selected legacy global peer to one authenticated shard."""
    if not _canonical_review_shard(filename):
        raise ValueError("shard alvo ngram global inválido")
    by_intent: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for node, line_number in intent_locations.items():
        if (not isinstance(node, tuple) or len(node) != 2 or
                not _canonical_review_shard(node[0]) or
                not isinstance(node[1], str) or
                _INTENT_ID.fullmatch(node[1]) is None or
                type(line_number) is not int or line_number < 1):
            raise ValueError("mapa intent→shard ngram global inválido")
        by_intent[node[1]].append(node)
    dependencies: set[str] = set()
    observed: set[str] = set()
    for raw_target in assigned_targets:
        if not isinstance(raw_target, str) or raw_target in observed:
            raise ValueError("alvo ngram global atribuído inválido")
        observed.add(raw_target)
        current_intent, peer_intent = _parse_ngram_target(raw_target)
        current_candidates = by_intent.get(current_intent, ())
        peer_candidates = by_intent.get(peer_intent, ())
        if (len(current_candidates) != 1 or
                current_candidates[0][0] != filename or
                len(peer_candidates) != 1 or
                peer_candidates[0][0] == filename):
            raise DistinctnessOperationalError(
                ("review_ngram_global_dependency_ambiguous",),
                sorted({
                    filename,
                    *(node[0] for node in current_candidates),
                    *(node[0] for node in peer_candidates),
                }),
                (raw_target,),
            )
        dependencies.add(peer_candidates[0][0])
    return dependencies


def _canonical_review_shard(path: object) -> bool:
    if not isinstance(path, str):
        return False
    shard_path = pathlib.PurePosixPath(path)
    return (
        shard_path.parent == pathlib.PurePosixPath(
            "data/editorial/v2_pages") and
        re.fullmatch(
            r"[a-z0-9_]+(?:-[a-z0-9_]+)+\.jsonl",
            shard_path.name,
        ) is not None and
        not any(token in {
            "bak", "backup", "candidate", "draft", "partial",
            "poisoned", "stale", "tmp",
        } for token in re.split(
            r"[-_.]+", shard_path.name.removesuffix(".jsonl")))
    )


def raise_for_distinctness_operational_failures(
    report: Mapping[str, Any],
    considered_paths: Iterable[str] | None = None,
) -> None:
    """Aggregate infrastructure/identity blockers before creating any task."""
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    considered = set(files) if considered_paths is None else set(considered_paths)
    reasons: set[str] = set()
    shards: set[str] = set()
    for filename in sorted(considered):
        result = files.get(filename)
        if not isinstance(result, Mapping):
            continue
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            continue
        for defect_class, raw_targets in defects.items():
            if (not isinstance(defect_class, str) or
                    not raw_targets or
                    not (defect_class.startswith("distinctness_") or
                         defect_class in V3_OPERATIONAL_DEFECT_CLASSES)):
                continue
            reasons.add(defect_class)
            shards.add(filename)
    if reasons:
        def details() -> Iterable[str]:
            for filename in sorted(shards):
                defects = files[filename]["defects"]
                for defect_class in sorted(defects):
                    if defect_class not in reasons:
                        continue
                    raw_targets = defects[defect_class]
                    if not isinstance(raw_targets, list):
                        yield f"{filename}:{defect_class}:invalid_targets"
                        continue
                    for target in sorted(
                            value for value in raw_targets
                            if isinstance(value, str)):
                        yield f"{filename}:{defect_class}:{target}"

        raise DistinctnessOperationalError(
            sorted(reasons), sorted(shards), details())


def validate_global_distinctness_epoch(
    report: Mapping[str, Any],
    authenticated_stock: Mapping[str, str],
    considered_paths: Iterable[str],
    *,
    expected_schema_version: int,
    expected_algorithm_fingerprint: str,
    expected_batch_fingerprint: str,
    expected_visible_surfaces: Iterable[str],
) -> dict[str, Any]:
    """Bind every stable report projection to one authenticated global epoch."""
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    paths = tuple(sorted(set(considered_paths)))
    errors: list[str] = []
    generations: set[str] = set()
    stocks: set[str] = set()
    visible_surfaces = list(expected_visible_surfaces)
    if not paths:
        errors.append("epoch:empty_inventory")
    if set(files) != set(paths):
        errors.append("epoch:report_inventory_set_mismatch")
    if set(authenticated_stock) != set(paths):
        errors.append("epoch:authenticated_stock_set_mismatch")
    expected_pages = 0
    for path in paths:
        result = files.get(path)
        active_pages = result.get("active_pages") if isinstance(
            result, Mapping) else None
        if type(active_pages) is not int or active_pages < 0:
            errors.append(f"{path}:active_pages")
        else:
            expected_pages += active_pages
    for path in paths:
        expected_digest = authenticated_stock.get(path)
        result = files.get(path)
        if (not _canonical_review_shard(path) or
                not isinstance(expected_digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None or
                not isinstance(result, Mapping)):
            errors.append(f"{path}:snapshot_or_result_missing")
            continue
        index = result.get("distinctness_index")
        if not isinstance(index, Mapping):
            errors.append(f"{path}:index_missing")
            continue
        checks = (
            (result.get("file") == path, "result_file"),
            (index.get("status") == "ready", "status"),
            (index.get("mode") == GLOBAL_DISTINCTNESS_MODE, "mode"),
            (type(index.get("schema_version")) is int and
             index.get("schema_version") == expected_schema_version,
             "schema_version"),
            (index.get("algorithm_fingerprint") ==
             expected_algorithm_fingerprint, "algorithm_fingerprint"),
            (index.get("batch_fingerprint") == expected_batch_fingerprint,
             "batch_fingerprint"),
            (index.get("target_digest") == expected_digest,
             "target_digest"),
            (index.get("target_snapshot_bound") is True,
             "target_snapshot_bound"),
            (index.get("inventory_complete") is True,
             "inventory_complete"),
            (index.get("inventory_stable") is True,
             "inventory_stable"),
            (index.get("stock_shards") == len(paths), "stock_shards"),
            (index.get("stock_pages") == expected_pages, "stock_pages"),
            (index.get("visible_surface_scope_complete") is True,
             "visible_surface_scope_complete"),
            (index.get("visible_surfaces") == visible_surfaces,
             "visible_surfaces"),
            (index.get("candidate_routing_complete") is True,
             "candidate_routing_complete"),
            (index.get("local_routing_complete") is True,
             "local_routing_complete"),
            (index.get("publication_allowed") is False,
             "publication_allowed"),
            (index.get("index_policy") == "noindex", "index_policy"),
        )
        errors.extend(
            f"{path}:{field}" for passed, field in checks if not passed)
        generation = index.get("generation_root")
        stock = index.get("stock_root")
        if (not isinstance(generation, str) or
                re.fullmatch(r"[0-9a-f]{64}", generation) is None):
            errors.append(f"{path}:generation_root")
        else:
            generations.add(generation)
        if (not isinstance(stock, str) or
                re.fullmatch(r"[0-9a-f]{64}", stock) is None):
            errors.append(f"{path}:stock_root")
        else:
            stocks.add(stock)
    if paths and len(generations) != 1:
        errors.append("epoch:generation_root_not_unique")
    if paths and len(stocks) != 1:
        errors.append("epoch:stock_root_not_unique")
    if errors:
        raise DistinctnessOperationalError(
            ("distinctness_epoch_authentication_failed",), paths, errors)
    return {
        "mode": GLOBAL_DISTINCTNESS_MODE,
        "schema_version": expected_schema_version,
        "algorithm_fingerprint": expected_algorithm_fingerprint,
        "batch_fingerprint": expected_batch_fingerprint,
        "generation_root": next(iter(generations), None),
        "stock_root": next(iter(stocks), None),
        "authenticated_shards": len(paths),
        "publication_allowed": False,
        "index_policy": "noindex",
    }


def _v3_endpoint(raw: object, label: str) -> tuple[str, str]:
    if not isinstance(raw, Mapping) or set(raw) != {"shard", "intent_id"}:
        raise ValueError(f"endpoint distinctness inválido ({label})")
    shard, intent = raw.get("shard"), raw.get("intent_id")
    if (not _canonical_review_shard(shard) or
            not isinstance(intent, str) or
            _INTENT_ID.fullmatch(intent) is None):
        raise ValueError(f"endpoint distinctness inválido ({label})")
    return shard, intent


def _parse_v3_target(raw_target: object) -> tuple[str, str]:
    if (not isinstance(raw_target, str) or raw_target.count("~") != 1 or
            raw_target != raw_target.strip()):
        raise ValueError(f"aresta distinctness v3 inválida: {raw_target!r}")
    current, peer = raw_target.split("~", 1)
    if (_INTENT_ID.fullmatch(current) is None or
            _INTENT_ID.fullmatch(peer) is None):
        raise ValueError(f"aresta distinctness v3 inválida: {raw_target!r}")
    return current, peer


def _v3_bounded_unit_number(value: object) -> bool:
    return (
        type(value) in (int, float) and
        math.isfinite(value) and
        0 <= value <= 1
    )


def _v3_valid_candidate_reasons(value: object) -> bool:
    if (not isinstance(value, list) or not value or
            any(not isinstance(reason, str) or
                reason not in V3_CANDIDATE_REASON_ORDER
                for reason in value) or
            len(value) != len(set(value))):
        return False
    positions = {
        reason: index
        for index, reason in enumerate(V3_CANDIDATE_REASON_ORDER)
    }
    return value == sorted(value, key=positions.__getitem__)


def _validate_v3_issue_schema(
    entry: Mapping[str, Any],
    filename: str,
) -> None:
    """Mirror the auditor's closed global-batch issue contract.

    The queue is a separate trust boundary: accepting an authenticated pair
    with a wrong code/field/reason combination or an unbounded metric would
    turn malformed audit output into an editorial instruction.  Keep the
    literals aligned with ``audit_v2_pages._global_batch_issue_schema_valid``.
    """
    code = entry.get("code")
    common = {
        "type", "code", "left", "right", "field", "candidate_reasons",
        "publication_allowed", "index_policy", "projection_target",
        "projection_peer",
    }
    if (entry.get("type") != "issue" or
            entry.get("publication_allowed") is not False or
            entry.get("index_policy") != "noindex"):
        raise ValueError(
            f"política/tipo de evidência distinctness inválido em "
            f"{filename}:{code}")

    exact = {
        "title_dup_global": ("title", "title"),
        "meta_dup_global": ("meta_description", "meta"),
        "h1_dup_global": ("h1", "h1"),
    }
    if code in exact:
        field, reason = exact[code]
        if (set(entry) != common or entry.get("field") != field or
                entry.get("candidate_reasons") != [reason]):
            raise ValueError(
                f"schema exato distinctness inválido em {filename}:{code}")
        return

    if code not in V3_SIMILARITY_DEFECT_CLASSES:
        raise ValueError(
            f"classe não editorial em evidência distinctness: "
            f"{filename}:{code}")
    metrics = {
        "body_jaccard", "max_identical_span_tokens",
        "target_repeated_density", "peer_repeated_density",
    }
    if (not common.issubset(entry) or
            not set(entry).issubset(common | metrics) or
            entry.get("field") != "body" or
            not _v3_valid_candidate_reasons(
                entry.get("candidate_reasons"))):
        raise ValueError(
            f"schema de similaridade distinctness inválido em "
            f"{filename}:{code}")
    for metric in (
            "body_jaccard", "target_repeated_density",
            "peer_repeated_density"):
        if metric in entry and not _v3_bounded_unit_number(entry[metric]):
            raise ValueError(
                f"métrica distinctness inválida em {filename}:{code}:"
                f"{metric}")
    if ("max_identical_span_tokens" in entry and
            (type(entry["max_identical_span_tokens"]) is not int or
             not 0 <= entry["max_identical_span_tokens"] <= V3_COUNTER_MAX)):
        raise ValueError(
            f"métrica distinctness inválida em {filename}:{code}:"
            "max_identical_span_tokens")
    if (code == "body_jaccard_near_duplicate" and
            entry.get("body_jaccard", -1) < V3_BODY_JACCARD_THRESHOLD):
        raise ValueError(
            f"métrica abaixo do limiar em {filename}:{code}:body_jaccard")
    if (code == "editorial_span_duplicate" and
            entry.get("max_identical_span_tokens", -1) <
            V3_IDENTICAL_SPAN_THRESHOLD):
        raise ValueError(
            f"métrica abaixo do limiar em {filename}:{code}:span")
    if (code == "editorial_repeat_density" and
            max(entry.get("target_repeated_density", -1),
                entry.get("peer_repeated_density", -1)) <
            V3_REPEAT_DENSITY_THRESHOLD):
        raise ValueError(
            f"métrica abaixo do limiar em {filename}:{code}:density")


def _validated_v3_evidence(
    report: Mapping[str, Any],
) -> dict[
    tuple[str, tuple[str, str], tuple[str, str]], dict[str, Any]
]:
    """Validate the complete symmetric v3 graph using shard-aware endpoints."""
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    directed: dict[
        tuple[str, tuple[str, str], tuple[str, str]], dict[str, Any]
    ] = {}
    fingerprints: dict[
        tuple[str, tuple[str, str], tuple[str, str]], str
    ] = {}
    expected_by_file: dict[tuple[str, str], set[str]] = {}
    observed_by_file: dict[tuple[str, str], set[str]] = collections.defaultdict(set)

    for filename, result in files.items():
        if not _canonical_review_shard(filename) or not isinstance(result, Mapping):
            raise ValueError(f"resultado distinctness inválido: {filename!r}")
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            raise ValueError(f"defeitos inválidos para {filename}")
        for code in V3_REVIEW_DEFECT_CLASSES:
            raw_targets = defects.get(code, [])
            if (not isinstance(raw_targets, list) or
                    not all(isinstance(target, str) for target in raw_targets)):
                raise ValueError(f"alvos inválidos em {filename}:{code}")
            if len(raw_targets) != len(set(raw_targets)):
                raise ValueError(f"alvo distinctness duplicado em {filename}:{code}")
            for raw_target in raw_targets:
                _parse_v3_target(raw_target)
            expected_by_file[(filename, code)] = set(raw_targets)

        evidence = result.get("evidence", {})
        if evidence is None:
            evidence = {}
        if not isinstance(evidence, Mapping):
            raise ValueError(f"evidências inválidas para {filename}")
        entries = evidence.get("distinctness", [])
        if (not isinstance(entries, list) or
                not all(isinstance(entry, Mapping) for entry in entries)):
            raise ValueError(f"evidências distinctness inválidas para {filename}")
        for entry in entries:
            code = entry.get("code")
            if code not in V3_REVIEW_DEFECT_CLASSES:
                if (isinstance(code, str) and
                        (code.startswith("distinctness_") or
                         code in V3_OPERATIONAL_DEFECT_CLASSES)):
                    raise ValueError(
                        "evidência operacional distinctness não pode virar "
                        f"tarefa editorial: {filename}:{code}")
                continue
            _validate_v3_issue_schema(entry, filename)
            target = _v3_endpoint(entry.get("projection_target"), "target")
            peer = _v3_endpoint(entry.get("projection_peer"), "peer")
            left = _v3_endpoint(entry.get("left"), "left")
            right = _v3_endpoint(entry.get("right"), "right")
            if (target[0] != filename or target == peer or
                    {left, right} != {target, peer} or
                    entry.get("publication_allowed") is not False or
                    entry.get("index_policy") != "noindex"):
                raise ValueError(
                    f"projeção distinctness inválida em {filename}:{code}")
            raw_target = f"{target[1]}~{peer[1]}"
            if raw_target not in expected_by_file[(filename, code)]:
                raise ValueError(
                    f"evidência distinctness extra em {filename}:{code}:"
                    f"{raw_target}")
            key = (code, target, peer)
            if key in directed:
                raise ValueError(
                    f"evidência distinctness duplicada em {filename}:{code}:"
                    f"{raw_target}")
            normalized = dict(entry)
            base = {
                key_name: value for key_name, value in normalized.items()
                if key_name not in {"projection_target", "projection_peer"}
            }
            fingerprints[key] = json.dumps(
                base, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"))
            directed[key] = normalized
            observed_by_file[(filename, code)].add(raw_target)

    for key, expected in expected_by_file.items():
        missing = expected - observed_by_file.get(key, set())
        if missing:
            raise ValueError(
                f"alvo distinctness sem evidência autenticada em "
                f"{key[0]}:{key[1]}:" + ",".join(sorted(missing)))
    for key, fingerprint in fingerprints.items():
        code, target, peer = key
        reverse = (code, peer, target)
        if reverse not in directed or fingerprints.get(reverse) != fingerprint:
            raise ValueError(
                "evidência distinctness sem reverso simétrico: "
                f"{code}:{target[0]}:{target[1]}~{peer[0]}:{peer[1]}")
    return directed


def plan_v3_distinctness_repairs(
    report: Mapping[str, Any],
    intent_locations: Mapping[tuple[str, str], int],
    writing_owned: Iterable[str],
    eligible_paths: Iterable[str] | None = None,
) -> tuple[
    dict[tuple[str, str], list[str]],
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], list[dict[str, Any]]],
]:
    """Assign similarity cover and one serialized repair per exact component."""
    directed = _validated_v3_evidence(report)
    files = report["files"]
    considered = set(files) if eligible_paths is None else set(eligible_paths)
    writing_owned = set(writing_owned)
    immutable_paths = {
        path for path in files
        if pathlib.PurePosixPath(path).stem in writing_owned
    }
    locations: dict[tuple[str, str], int] = {}
    for node, line_number in intent_locations.items():
        if (not isinstance(node, tuple) or len(node) != 2 or
                not _canonical_review_shard(node[0]) or
                not isinstance(node[1], str) or
                _INTENT_ID.fullmatch(node[1]) is None or
                type(line_number) is not int or line_number < 1 or
                node in locations):
            raise ValueError(f"localização distinctness inválida: {node!r}")
        locations[node] = line_number

    edges = {
        (code,) + tuple(sorted((target, peer)))
        for code, target, peer in directed
    }
    planned: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    selected: dict[
        tuple[str, str], list[dict[str, Any]]
    ] = collections.defaultdict(list)
    components_out: dict[
        tuple[str, str], list[dict[str, Any]]
    ] = collections.defaultdict(list)
    exact_assigned: set[tuple[str, str]] = set()

    def node_key(node: tuple[str, str]) -> tuple[str, int, str]:
        line = locations.get(node)
        if type(line) is not int:
            raise ValueError(
                f"endpoint distinctness sem localização autenticada: {node!r}")
        return node[0], line, node[1]

    for code in sorted(V3_EXACT_REVIEW_DEFECT_CLASSES):
        adjacency: dict[tuple[str, str], set[tuple[str, str]]] = (
            collections.defaultdict(set))
        for edge_code, first, second in edges:
            if edge_code != code:
                continue
            adjacency[first].add(second)
            adjacency[second].add(first)
        pending = set(adjacency)
        while pending:
            seed = min(pending)
            component: set[tuple[str, str]] = set()
            frontier = [seed]
            while frontier:
                node = frontier.pop()
                if node in component:
                    continue
                component.add(node)
                frontier.extend(adjacency[node] - component)
            pending.difference_update(component)
            if not any(node[0] in considered for node in component):
                continue
            immutable = sorted(
                (node for node in component if node[0] in immutable_paths))
            if len(immutable) > 1:
                raise DistinctnessOperationalError(
                    ("distinctness_exact_component_multiple_immutable",),
                    (node[0] for node in component),
                    (f"{code}:{node[0]}:{node[1]}" for node in immutable))
            # Um peer instável, reivindicado ou fora do snapshot autenticado
            # adia o componente inteiro. Reparar só um subgrafo pode preservar
            # duas cópias exatas que a estrela global conecta indiretamente.
            if any(node[0] not in considered for node in component):
                continue
            for node in component:
                node_key(node)
            owner = immutable[0] if immutable else min(component, key=node_key)
            ordered_members = sorted(component, key=node_key)
            component_identity = code + "\n" + "\n".join(
                f"{node[0]}\0{node[1]}" for node in ordered_members)
            component_id = hashlib.sha256(
                component_identity.encode("utf-8")).hexdigest()
            # O owner é a única linha preservada. Todos os N-1 alvos entram no
            # plano da mesma geração; a camada de cohort abaixo agrupa seus
            # shards numa wave transacional bounded. Escolher um único shard
            # aqui fazia um componente em 20 shards exigir ~19 relaunches e,
            # pior, transformava a primeira CAS válida em drift dos demais.
            component_targets = sorted(
                component - {owner},
                key=node_key)
            for target in component_targets:
                exact_assigned.add(target)
                peers = sorted(adjacency[target], key=node_key)
                for peer in peers:
                    raw_target = f"{target[1]}~{peer[1]}"
                    planned[(target[0], code)].append(raw_target)
                    selected[(target[0], code)].append(
                        directed[(code, target, peer)])
                components_out[(target[0], code)].append({
                    "projection_target": {
                        "shard": target[0], "intent_id": target[1]},
                    "preserved_owner": {
                        "shard": owner[0], "intent_id": owner[1]},
                    "component_id": component_id,
                    "member_count": len(component),
                    "dependency_paths": sorted({
                        node[0] for node in component}),
                })

    similarity_edges = {
        edge for edge in edges
        if edge[0] in V3_SIMILARITY_DEFECT_CLASSES and
        edge[1][0] in considered and edge[2][0] in considered
    }
    for _, first, second in similarity_edges:
        node_key(first)
        node_key(second)
    forced = set(exact_assigned)
    immutable_nodes = {
        node for edge in similarity_edges for node in edge[1:]
        if node[0] in immutable_paths
    }
    assigned = _deterministic_vertex_cover(
        similarity_edges, node_key=node_key, immutable=immutable_nodes,
        forced=forced, fail_on_immutable_only=False)
    for edge in sorted(similarity_edges):
        code, first, second = edge
        target = assigned.get(edge)
        if target is None:
            continue
        peer = second if target == first else first
        planned[(target[0], code)].append(f"{target[1]}~{peer[1]}")
        selected[(target[0], code)].append(directed[(code, target, peer)])

    def unique_sorted(values: Iterable[str]) -> list[str]:
        return sorted(set(values))

    return (
        {key: unique_sorted(values) for key, values in planned.items()},
        {
            key: sorted(values, key=lambda entry: (
                entry["projection_target"]["intent_id"],
                entry["projection_peer"]["shard"],
                entry["projection_peer"]["intent_id"],
            ))
            for key, values in selected.items()
        },
        {
            key: sorted(values, key=lambda item: (
                item["projection_target"]["intent_id"],
                item["preserved_owner"]["shard"],
                item["preserved_owner"]["intent_id"],
            ))
            for key, values in components_out.items()
        },
    )


def writing_recovery_item_sha256(item: Mapping[str, Any]) -> str:
    """Fingerprint one closed raw-shard recovery instruction."""
    if not isinstance(item, Mapping) or not item:
        raise ValueError("item de writing recovery deve ser mapping não vazio")
    canonical = dict(item)
    canonical.pop("recovery_item_sha256", None)
    payload = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_writing_raw_recovery_projection(
    value: Mapping[str, Any],
    *,
    target_rel_path: str | None = None,
    target_sha256: str | None = None,
    expected_intents: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate the closed queue schema without interpreting raw bad lines."""
    fields = {
        "schema_version", "route", "target_rel_path", "target_sha256",
        "expected_n", "expected_intent_ids", "expected_intent_ids_sha256",
        "reason_codes", "raw_lines_seen", "parsed_object_rows",
        "invalid_rows", "unaddressable_rows", "reuse",
        "preserved_record_sha256", "review_allowed",
        "publication_allowed", "index_policy", "recovery_item_sha256",
    }
    allowed_reasons = {
        "missing_terminal_lf", "noncanonical_cr", "invalid_json_row",
        "non_object_row", "unaddressable_row", "duplicate_intent_rows",
        "cardinality_mismatch", "intent_order_mismatch",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError("projeção raw-recovery perdeu schema fechado")
    projection = dict(value)
    expected = projection.get("expected_intent_ids")
    reasons = projection.get("reason_codes")
    reuse = projection.get("reuse")
    preserved = projection.get("preserved_record_sha256")
    if (projection.get("schema_version") !=
            "v2_writing_raw_recovery_v1" or
            projection.get("route") != "writing_full_shard_recovery" or
            not _canonical_review_shard(projection.get("target_rel_path")) or
            not isinstance(projection.get("target_sha256"), str) or
            re.fullmatch(r"[0-9a-f]{64}", projection["target_sha256"]) is None or
            type(projection.get("expected_n")) is not int or
            projection["expected_n"] < 1 or
            not isinstance(expected, list) or
            len(expected) != projection["expected_n"] or
            len(expected) != len(set(expected)) or
            any(not isinstance(intent, str) or
                _INTENT_ID.fullmatch(intent) is None for intent in expected) or
            not isinstance(reasons, list) or not reasons or
            reasons != sorted(set(reasons)) or
            not set(reasons).issubset(allowed_reasons) or
            not isinstance(reuse, list) or len(reuse) != len(set(reuse)) or
            any(intent not in expected for intent in reuse) or
            reuse != [intent for intent in expected if intent in set(reuse)] or
            not isinstance(preserved, dict) or set(preserved) != set(reuse) or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in preserved.values()) or
            projection.get("review_allowed") is not False or
            projection.get("publication_allowed") is not False or
            projection.get("index_policy") != "noindex"):
        raise ValueError("projeção raw-recovery tem identidade inválida")
    for counter in (
            "raw_lines_seen", "parsed_object_rows", "invalid_rows",
            "unaddressable_rows"):
        if (type(projection.get(counter)) is not int or
                not 0 <= projection[counter] <= 1_000_000):
            raise ValueError("contador raw-recovery inválido")
    expected_payload = json.dumps(
        expected, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    if (projection.get("expected_intent_ids_sha256") !=
            _sha256(expected_payload) or
            projection.get("recovery_item_sha256") !=
            writing_recovery_item_sha256(projection)):
        raise ValueError("fingerprint raw-recovery inválido")
    if (target_rel_path is not None and
            projection["target_rel_path"] != target_rel_path):
        raise ValueError("path raw-recovery diverge da fila")
    if (target_sha256 is not None and
            projection["target_sha256"] != target_sha256):
        raise ValueError("target SHA raw-recovery diverge da fila")
    if (expected_intents is not None and
            tuple(expected) != tuple(expected_intents)):
        raise ValueError("slice raw-recovery diverge da fila")
    if (("cardinality_mismatch" in reasons) !=
            (projection["parsed_object_rows"] != projection["expected_n"]) or
            ("invalid_json_row" in reasons and
             projection["invalid_rows"] == 0) or
            ("unaddressable_row" in reasons and
             projection["unaddressable_rows"] == 0)):
        raise ValueError("diagnóstico raw-recovery contradiz contadores")
    return projection


def build_writing_recovery_contract(
    report: Mapping[str, Any],
    writing_owned: Iterable[str],
    authenticated_stock: Mapping[str, str],
    expected_intents_by_path: Mapping[str, Iterable[str]],
) -> list[dict[str, Any]]:
    """Bind non-editorial shard recovery to raw bytes and inventory intent.

    The returned records are metadata for the writing/recovery producer, never
    review tasks and never publication authority.  They make malformed JSONL,
    missing terminal LF and cardinality drift observable without asking the
    review finalizer to parse an impossible preimage or change row count.
    """
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório de recovery sem objeto files")
    owners = set(writing_owned)
    stock = dict(authenticated_stock)
    expected_map = dict(expected_intents_by_path)
    routes: list[dict[str, Any]] = []
    for filename in sorted(files):
        result = files[filename]
        if not _canonical_review_shard(filename):
            raise ValueError(f"path de recovery inválido: {filename!r}")
        expected_raw = expected_map.get(filename)
        if expected_raw is None:
            # Só precisamos de owner de inventário quando existe finding de
            # raw recovery; ``writing_recovery_findings`` ainda valida as
            # formas emitidas pelo auditor antes de decidir isso.
            findings = writing_recovery_findings(result)
            if findings:
                raise DistinctnessOperationalError(
                    ("writing_recovery_inventory_owner_missing",),
                    (filename,),
                )
            continue
        expected = tuple(expected_raw)
        if (not expected or len(expected) != len(set(expected)) or
                any(not isinstance(intent, str) or
                    _INTENT_ID.fullmatch(intent) is None
                    for intent in expected)):
            raise ValueError(
                f"inventário de recovery inválido para {filename}")
        findings = writing_recovery_findings(
            result, expected_pages=len(expected))
        if not findings:
            continue
        slug = pathlib.PurePosixPath(filename).stem
        if slug not in owners:
            raise DistinctnessOperationalError(
                ("writing_recovery_route_owner_missing",), (filename,),
                (f"{code}:{target}"
                 for code, targets in findings.items()
                 for target in targets),
            )
        target_digest = stock.get(filename)
        if (not isinstance(target_digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", target_digest) is None):
            raise DistinctnessOperationalError(
                ("writing_recovery_target_snapshot_missing",), (filename,),
            )
        expected_payload = json.dumps(
            expected, ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
        route = {
            "schema_version": "v2_writing_recovery_v1",
            "route": "writing_full_shard_recovery",
            "slug": slug,
            "target_rel_path": filename,
            "target_sha256": target_digest,
            "expected_n": len(expected),
            "observed_pages": result["pages"],
            "expected_intent_ids": list(expected),
            "expected_intent_ids_sha256": hashlib.sha256(
                expected_payload).hexdigest(),
            "defeitos": {
                code: len(targets) for code, targets in findings.items()
            },
            "alvos": findings,
            "review_allowed": False,
            "publication_allowed": False,
            "index_policy": "noindex",
        }
        route["recovery_item_sha256"] = writing_recovery_item_sha256(route)
        routes.append(route)
    return routes


def build_todo(
    report: Mapping[str, Any],
    writing_owned: Iterable[str],
    slug_meta: Mapping[str, Mapping[str, Any]],
    intent_locations: Mapping[tuple[str, str], int] | None = None,
    eligible_paths: Iterable[str] | None = None,
    review_scope_locations: Mapping[tuple[str, str], int] | None = None,
) -> list[dict[str, Any]]:
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("relatório do auditor sem objeto files")
    writing_owned = set(writing_owned)
    eligible = None if eligible_paths is None else set(eligible_paths)
    if eligible is not None and any(
            not _canonical_review_shard(path) for path in eligible):
        raise ValueError("conjunto de shards elegíveis contém path inválido")
    recovery_without_owner = []
    recovery_details = []
    for filename, result in files.items():
        findings = writing_recovery_findings(result)
        if not findings:
            continue
        slug = pathlib.PurePosixPath(filename).stem
        if slug not in writing_owned:
            recovery_without_owner.append(filename)
            recovery_details.extend(
                f"{code}:{filename}:{target}"
                for code, targets in findings.items()
                for target in targets)
    if recovery_without_owner:
        raise DistinctnessOperationalError(
            ("writing_recovery_route_owner_missing",),
            sorted(recovery_without_owner), sorted(recovery_details))
    raise_for_distinctness_operational_failures(report)
    authenticated_locations = intent_locations or {}
    try:
        planned_ngrams = plan_ngram_repairs(
            report, authenticated_locations, writing_owned, eligible,
            review_scope_locations)
        validated_ngram_evidence = validate_ngram_evidence(
            report, authenticated_locations)
        (planned_v3, validated_v3_evidence,
         validated_v3_components) = plan_v3_distinctness_repairs(
             report, authenticated_locations, writing_owned, eligible)
    except DistinctnessOperationalError:
        raise
    except ValueError as error:
        raise DistinctnessOperationalError(
            ("distinctness_review_graph_invalid",), sorted(files),
            (str(error),)) from error
    todo: list[dict[str, Any]] = []
    for filename in sorted(files):
        if not isinstance(filename, str):
            raise ValueError("path de shard deve ser string")
        shard_path = pathlib.PurePosixPath(filename)
        if not _canonical_review_shard(filename):
            raise ValueError(f"path de shard inválido: {filename}")
        if eligible is not None and filename not in eligible:
            continue
        result = files[filename]
        if not isinstance(result, Mapping):
            raise ValueError(f"resultado inválido para {filename}")
        slug = shard_path.name.removesuffix(".jsonl")
        if slug in writing_owned:
            continue
        defects = result.get("defects")
        if not isinstance(defects, Mapping):
            raise ValueError(f"defeitos inválidos para {filename}")
        blocking: dict[str, list[str]] = {}
        for defect_class in sorted(defects):
            if not isinstance(defect_class, str):
                raise ValueError(f"classe de defeito inválida em {filename}")
            if defect_class == "skipped":
                continue
            targets = defects[defect_class]
            if not isinstance(targets, list) or not all(
                isinstance(target, str) for target in targets
            ):
                raise ValueError(
                    f"alvos inválidos em {filename}:{defect_class}"
                )
            if defect_class in NGRAM_DEFECT_CLASSES:
                targets = planned_ngrams.get((filename, defect_class), [])
            elif defect_class in V3_REVIEW_DEFECT_CLASSES:
                targets = planned_v3.get((filename, defect_class), [])
            if targets:
                blocking[defect_class] = sorted(targets)
        if not blocking:
            continue
        review_evidence: dict[str, list[dict[str, str]]] = {}
        for defect_class in NGRAM_DEFECT_CLASSES:
            assigned_targets = set(blocking.get(defect_class, ()))
            if not assigned_targets:
                continue
            entries = validated_ngram_evidence.get(
                (filename, defect_class), {})
            missing_evidence = assigned_targets - set(entries)
            if missing_evidence:
                raise ValueError(
                    "alvo ngram sem evidência autenticada em "
                    f"{filename}:{defect_class}:" +
                    ",".join(sorted(missing_evidence))
                )
            review_evidence[defect_class] = sorted(
                (entries[target] for target in assigned_targets),
                key=lambda entry: (
                    entry["target"], entry["field"],
                    entry["peer_field"], entry["phrase"]),
            )
        pages = result.get("pages")
        if not isinstance(pages, int) or isinstance(pages, bool) or pages < 0:
            raise ValueError(f"contagem de páginas inválida para {filename}")
        metadata = slug_meta.get(slug, {})
        area = metadata.get("area") if isinstance(metadata, Mapping) else None
        if not isinstance(area, str) or not area.strip():
            area = slug.split("-", 1)[0]
        item = {
                "slug": slug,
                "n": pages,
                "area": area or slug.split("-", 1)[0],
                "defeitos": {
                    defect_class: len(targets)
                    for defect_class, targets in blocking.items()
                },
                # Sem [:20]: todo bloqueio produzido pelo auditor chega ao
                # revisor responsável pelo shard.
                "alvos": blocking,
            }
        if review_evidence:
            item["evidencias"] = review_evidence
        distinctness_evidence = {
            defect_class: validated_v3_evidence[(filename, defect_class)]
            for defect_class in sorted(V3_REVIEW_DEFECT_CLASSES)
            if (filename, defect_class) in validated_v3_evidence and
            defect_class in blocking
        }
        if distinctness_evidence:
            item["evidencias_distinctness"] = distinctness_evidence
        distinctness_components = {
            defect_class: validated_v3_components[(filename, defect_class)]
            for defect_class in sorted(V3_EXACT_REVIEW_DEFECT_CLASSES)
            if (filename, defect_class) in validated_v3_components and
            defect_class in blocking
        }
        if distinctness_components:
            item["componentes_distinctness"] = distinctness_components
        dependency_paths: set[str] = set()
        legacy_global_targets = blocking.get("ngram_dup_global", ())
        if legacy_global_targets:
            dependency_paths.update(legacy_ngram_global_dependency_paths(
                filename,
                legacy_global_targets,
                authenticated_locations,
            ))
        for entries in distinctness_evidence.values():
            for entry in entries:
                dependency_paths.add(entry["projection_target"]["shard"])
                dependency_paths.add(entry["projection_peer"]["shard"])
        for components in distinctness_components.values():
            for component in components:
                dependency_paths.update(component["dependency_paths"])
        dependency_paths.discard(filename)
        if dependency_paths:
            item["distinctness_dependency_paths"] = sorted(dependency_paths)
        todo.append(item)
    return todo


def _review_item_path(item: Mapping[str, Any]) -> str:
    slug = item.get("slug") if isinstance(item, Mapping) else None
    if (not isinstance(slug, str) or
            re.fullmatch(r"[a-z0-9_]+(?:-[a-z0-9_]+)+", slug) is None):
        raise ValueError("item de review sem slug canônico")
    path = f"data/editorial/v2_pages/{slug}.jsonl"
    if not _canonical_review_shard(path):
        raise ValueError("item de review resolveu path inválido")
    return path


def _exact_component_memberships(
    item: Mapping[str, Any],
) -> dict[str, tuple[tuple[str, str], int]]:
    """Return component -> (owner endpoint, global member count)."""
    raw = item.get("componentes_distinctness")
    if raw is None:
        return {}
    if not isinstance(raw, Mapping) or not raw:
        raise ValueError("componentes exact devem ser objeto não vazio")
    path = _review_item_path(item)
    memberships: dict[str, tuple[tuple[str, str], int]] = {}
    for defect_class in sorted(raw):
        if defect_class not in V3_EXACT_REVIEW_DEFECT_CLASSES:
            raise ValueError("classe não-exact em componentes distinctness")
        entries = raw[defect_class]
        if not isinstance(entries, list) or not entries:
            raise ValueError("lista de componentes exact vazia")
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise ValueError("componente exact não é objeto")
            component_id = entry.get("component_id")
            member_count = entry.get("member_count")
            target = _v3_endpoint(entry.get("projection_target"), "wave-target")
            owner = _v3_endpoint(entry.get("preserved_owner"), "wave-owner")
            if (target[0] != path or target == owner or
                    not isinstance(component_id, str) or
                    re.fullmatch(r"[0-9a-f]{64}", component_id) is None or
                    type(member_count) is not int or
                    not 2 <= member_count <= V3_COUNTER_MAX):
                raise ValueError("identidade de componente exact inválida")
            contract = (owner, member_count)
            prior = memberships.get(component_id)
            if prior is not None and prior != contract:
                raise ValueError("component_id possui owners/contagens divergentes")
            memberships[component_id] = contract
    return memberships


def plan_exact_component_wave_cohorts(
    items: Iterable[Mapping[str, Any]],
    max_members: int = DEFAULT_EXACT_COMPONENT_WAVE_MEMBERS,
    *,
    hard_max_members: int = MAX_EXACT_COMPONENT_WAVE_MEMBERS,
) -> list[dict[str, Any]]:
    """Plan deterministic target-shard cohorts for exact components.

    Every connected exact component is indivisible: all N-1 projection targets
    must be visible before the first post-wave audit. ``max_members`` is the
    configured epoch budget and ``hard_max_members`` is the absolute overlay
    ceiling. A component above either bound fails before drafts/CAS instead of
    being split into cohorts that would mechanically invalidate one another.
    """
    if (type(hard_max_members) is not int or
            not 1 <= hard_max_members <= MAX_EXACT_COMPONENT_WAVE_MEMBERS or
            type(max_members) is not int or
            not 1 <= max_members <= hard_max_members):
        raise ValueError("cohort exact deve usar 1..31 membros")
    by_path: dict[str, dict[str, tuple[tuple[str, str], int]]] = {}
    item_by_path: dict[str, Mapping[str, Any]] = {}
    component_targets: dict[str, set[str]] = collections.defaultdict(set)
    component_contracts: dict[str, tuple[tuple[str, str], int]] = {}
    for raw_item in items:
        if not isinstance(raw_item, Mapping):
            raise ValueError("fila exact contém item não-objeto")
        path = _review_item_path(raw_item)
        if path in item_by_path:
            raise ValueError("fila exact contém shard repetido")
        item_by_path[path] = raw_item
        memberships = _exact_component_memberships(raw_item)
        if not memberships:
            continue
        by_path[path] = memberships
        for component_id, contract in memberships.items():
            prior = component_contracts.get(component_id)
            if prior is not None and prior != contract:
                raise ValueError(
                    "component_id diverge entre shards da mesma fila")
            component_contracts[component_id] = contract
            component_targets[component_id].add(path)

    # Union-find no grafo shard<->component. Um shard que corrige dois
    # componentes liga ambos à mesma unidade de mutação e não pode participar
    # de dois finalizadores concorrentes.
    parent = {path: path for path in by_path}

    def find(path: str) -> str:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for paths in component_targets.values():
        ordered = sorted(paths)
        for path in ordered[1:]:
            union(ordered[0], path)
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(by_path):
        groups[find(path)].append(path)

    planned: list[dict[str, Any]] = []
    for group_paths in sorted(groups.values(), key=lambda paths: tuple(paths)):
        all_components = sorted({
            component_id
            for path in group_paths
            for component_id in by_path[path]
        })
        owners = sorted({
            component_contracts[component_id][0]
            for component_id in all_components
        })
        group_seed = {
            "schema_version": EXACT_COMPONENT_WAVE_SCHEMA,
            "member_paths": group_paths,
            "component_ids": all_components,
            "preserved_owners": [
                {"shard": owner[0], "intent_id": owner[1]}
                for owner in owners
            ],
            "component_member_counts": {
                component_id: component_contracts[component_id][1]
                for component_id in all_components
            },
        }
        group_id = hashlib.sha256(json.dumps(
            group_seed, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        if len(group_paths) > hard_max_members:
            raise DistinctnessOperationalError(
                ("exact_component_wave_hard_limit_exceeded",),
                group_paths,
                (f"group_id={group_id}",
                 f"targets={len(group_paths)}",
                 f"hard_max_members={hard_max_members}",
                 *all_components),
            )
        if len(group_paths) > max_members:
            raise DistinctnessOperationalError(
                ("exact_component_wave_epoch_budget_exceeded",),
                group_paths,
                (f"group_id={group_id}",
                 f"targets={len(group_paths)}",
                 f"max_members={max_members}",
                 *all_components),
            )
        planned.append({
            "schema_version": EXACT_COMPONENT_WAVE_SCHEMA,
            "group_id": group_id,
            "cohort_index": 0,
            "cohort_count": 1,
            "member_paths": list(group_paths),
            "component_ids": all_components,
            "preserved_owners": [
                {"shard": owner[0], "intent_id": owner[1]}
                for owner in owners
            ],
            "publication_allowed": False,
            "index_policy": "noindex",
        })
    return planned


def select_review_wave_epoch(
    items: Iterable[Mapping[str, Any]],
    max_files: int = DEFAULT_EXACT_COMPONENT_WAVE_MEMBERS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Select one fresh cohort per exact group plus independent work."""
    if (type(max_files) is not int or
            not 1 <= max_files <= MAX_EXACT_COMPONENT_WAVE_MEMBERS):
        raise ValueError("epoch de review deve usar 1..31 arquivos")
    copied = [dict(item) for item in items]
    path_to_item = {_review_item_path(item): item for item in copied}
    if len(path_to_item) != len(copied):
        raise ValueError("epoch de review contém shard duplicado")
    cohorts = plan_exact_component_wave_cohorts(copied, max_files)
    first_cohorts = [cohort for cohort in cohorts
                     if cohort["cohort_index"] == 0]
    selected_paths: set[str] = set()
    selected_resources: set[str] = set()
    selected_cohorts: list[dict[str, Any]] = []
    for cohort in first_cohorts:
        member_paths = cohort["member_paths"]
        if len(selected_paths) + len(member_paths) > max_files:
            continue
        resources = set(member_paths)
        for path in member_paths:
            resources.update(
                path_to_item[path].get("distinctness_dependency_paths", ()))
        if selected_resources & resources:
            continue
        selected_paths.update(member_paths)
        selected_resources.update(resources)
        selected_cohorts.append(dict(cohort))

    exact_paths = {
        path for path, item in path_to_item.items()
        if _exact_component_memberships(item)
    }
    for path in sorted(path_to_item):
        if len(selected_paths) >= max_files:
            break
        if path in exact_paths or path in selected_paths:
            continue
        item = path_to_item[path]
        resources = {path, *item.get("distinctness_dependency_paths", ())}
        if selected_resources & resources:
            continue
        selected_paths.add(path)
        selected_resources.update(resources)
    selected = [path_to_item[path] for path in sorted(selected_paths)]
    return selected, selected_cohorts, len(copied) - len(selected)


def bind_exact_component_waves(
    items: Iterable[Mapping[str, Any]],
    cohorts: Iterable[Mapping[str, Any]],
    authenticated_stock: Mapping[str, str],
    distinctness_epoch: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Bind selected cohorts to preimages and the authenticated generation."""
    result = [dict(item) for item in items]
    cohort_records = list(cohorts)
    by_path = {_review_item_path(item): item for item in result}
    if len(by_path) != len(result):
        raise ValueError("binding de wave contém shard duplicado")
    if not cohort_records:
        exact_unbound = sorted(
            path for path, item in by_path.items()
            if _exact_component_memberships(item))
        if exact_unbound:
            raise ValueError(
                "target exact selecionado sem cohort transacional: " +
                ",".join(exact_unbound[:8]))
        return result
    generation_root = distinctness_epoch.get("generation_root")
    if (not isinstance(generation_root, str) or
            re.fullmatch(r"[0-9a-f]{64}", generation_root) is None):
        raise ValueError("wave exact sem generation_root autenticado")
    bound_paths: set[str] = set()
    for raw_cohort in cohort_records:
        if not isinstance(raw_cohort, Mapping):
            raise ValueError("cohort exact não é objeto")
        cohort = dict(raw_cohort)
        member_paths = cohort.get("member_paths")
        if (cohort.get("schema_version") != EXACT_COMPONENT_WAVE_SCHEMA or
                not isinstance(member_paths, list) or not member_paths or
                len(member_paths) > MAX_EXACT_COMPONENT_WAVE_MEMBERS or
                member_paths != sorted(set(member_paths)) or
                any(path not in by_path for path in member_paths) or
                bound_paths.intersection(member_paths)):
            raise ValueError("cohort exact perdeu membros canônicos")
        preimages = {}
        for path in member_paths:
            digest = authenticated_stock.get(path)
            if (not isinstance(digest, str) or
                    re.fullmatch(r"[0-9a-f]{64}", digest) is None or
                    by_path[path].get("target_sha256") != digest):
                raise ValueError("cohort exact não liga preimagem do target")
            preimages[path] = digest
        contract_without_id = {
            **cohort,
            "mode": "exact-component-wave",
            "member_pre_sha256": preimages,
            "distinctness_generation_root": generation_root,
        }
        wave_id = hashlib.sha256(json.dumps(
            contract_without_id, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        contract = {**contract_without_id, "wave_id": wave_id}
        for path in member_paths:
            item = by_path[path]
            dependencies = dict(
                item.get("distinctness_dependency_sha256", {}))
            for peer_path, peer_digest in preimages.items():
                if peer_path != path:
                    previous = dependencies.get(peer_path)
                    if previous is not None and previous != peer_digest:
                        raise ValueError(
                            "wave exact contradiz preimagem relacional")
                    dependencies[peer_path] = peer_digest
            item["distinctness_dependency_sha256"] = dict(
                sorted(dependencies.items()))
            item["exact_component_wave"] = contract
        bound_paths.update(member_paths)
    exact_unbound = sorted(
        path for path, item in by_path.items()
        if _exact_component_memberships(item) and path not in bound_paths)
    if exact_unbound:
        raise ValueError(
            "target exact selecionado sem cohort transacional: " +
            ",".join(exact_unbound[:8]))
    return result


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def review_queue_item_sha256(item: Mapping[str, Any]) -> str:
    """Fingerprint canonical queue semantics, excluding its receipt field."""
    if not isinstance(item, Mapping) or not item:
        raise ValueError("item de fila deve ser mapping não vazio")
    canonical = dict(item)
    canonical.pop("queue_item_sha256", None)
    if not canonical:
        raise ValueError("item de fila não pode conter somente o recibo")

    def validate_json(value: object, label: str) -> None:
        if value is None or type(value) in (bool, int, str):
            return
        if type(value) is float:
            if not math.isfinite(value):
                raise ValueError(f"item de fila contém float inválido: {label}")
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                validate_json(child, f"{label}[{index}]")
            return
        if isinstance(value, Mapping):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError(
                        f"item de fila contém chave não textual: {label}")
                validate_json(child, f"{label}.{key}")
            return
        raise ValueError(
            f"item de fila contém tipo não JSON: {label}:"
            f"{type(value).__name__}")

    validate_json(canonical, "item")
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(payload) > MAX_REVIEW_QUEUE_ITEM_BYTES:
        raise ValueError("item de fila excede orçamento canônico de 8 MiB")
    return _sha256(payload)


def select_review_items_by_encoded_budget(
    items: Iterable[Mapping[str, Any]],
    max_json_bytes: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Pack an authenticated queue without exceeding its JSON-array budget.

    The workflow consumer reads the complete generated JavaScript through a
    64 MiB bounded snapshot.  A per-item ceiling alone therefore permits a
    producer to create an unreadable queue.  This deterministic first-fit pass
    accounts for the exact ``json.dumps(..., ensure_ascii=False)`` array bytes
    used by ``ops/relaunch-review.sh`` and defers overflow items without
    weakening their defects or fingerprints.
    """
    if (type(max_json_bytes) is not int or max_json_bytes < 2 or
            max_json_bytes > MAX_REVIEW_QUEUE_OUTPUT_BYTES):
        raise ValueError("orçamento JSON da fila deve estar entre 2 bytes e 64 MiB")
    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    encoded_bytes = 2  # []
    for position, raw_item in enumerate(items):
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"item de fila não é objeto: posição {position}")
        item = dict(raw_item)
        declared = item.get("queue_item_sha256")
        if (not isinstance(declared, str) or
                re.fullmatch(r"[0-9a-f]{64}", declared) is None or
                review_queue_item_sha256(item) != declared):
            raise ValueError(
                f"item de fila sem fingerprint válido: posição {position}")
        payload = json.dumps(
            item, ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        next_bytes = encoded_bytes + len(payload) + (2 if selected else 0)
        if next_bytes <= max_json_bytes:
            selected.append(item)
            encoded_bytes = next_bytes
        else:
            deferred.append(item)
    return selected, deferred, encoded_bytes


class _Snapshot(NamedTuple):
    payload: bytes
    digest: str
    device: int
    inode: int
    mode: int
    nlink: int


class RegularFileSnapshot(NamedTuple):
    """Bytes e SHA-256 da mesma leitura segura de um arquivo regular único."""

    payload: bytes
    digest: str


_LIBC = ctypes.CDLL(None, use_errno=True)
_RENAME_NOREPLACE = 1
_RENAME_EXCHANGE = 2


def _renameat2(
    old_dir_fd: int,
    old_name: str,
    new_dir_fd: int,
    new_name: str,
    flags: int,
) -> None:
    renameat2 = getattr(_LIBC, "renameat2", None)
    if renameat2 is not None:
        result = renameat2(
            old_dir_fd,
            os.fsencode(old_name),
            new_dir_fd,
            os.fsencode(new_name),
            flags,
        )
        if result == 0:
            return
        error_number = ctypes.get_errno()
        if error_number not in (errno.EINVAL, errno.ENOSYS, errno.ENOTSUP):
            raise OSError(error_number, os.strerror(error_number))
        # EINVAL/ENOSYS/ENOTSUP com flags: filesystem sem suporte às flags de
        # renameat2 (medido em 2026-07-30 no mount virtiofs do sandbox Cowork,
        # onde NOREPLACE e EXCHANGE devolvem EINVAL). Cai no fallback portátil
        # abaixo, que preserva a pós-condição byte a byte. Qualquer outro errno
        # (EEXIST, ENOENT, EACCES…) é resultado REAL da operação e propaga.
    _renameat2_fallback(old_dir_fd, old_name, new_dir_fd, new_name, flags)


def _renameat2_fallback(
    old_dir_fd: int,
    old_name: str,
    new_dir_fd: int,
    new_name: str,
    flags: int,
) -> None:
    """Emula NOREPLACE/EXCHANGE onde renameat2 não suporta flags.

    Contrato de uso (igual ao dos call sites reais): o chamador SEMPRE segura o
    flock exclusivo do alvo (atomic_replace_cas) ou opera nome-token com
    entropia criptográfica (recovery). Sob essa serialização cooperativa:

    - NOREPLACE vira checagem de ausência + rename plano. A janela TOCTOU
      residual é de um syscall, coberta pelo lock cooperativo e pela
      autenticação pós-instalação que o CAS já executa (verify-after: qualquer
      corrida vira CASMismatch alto com recovery, nunca perda silenciosa).
    - EXCHANGE vira link(velho→token) + rename(novo→alvo) + rename(token→velho):
      pós-condição idêntica (bytes antigos terminam no nome antigo do temp,
      MESMO inode — escritor não cooperativo com FD aberto continua ligado a um
      pathname), alvo nunca fica ausente em nenhum instante.
    Falha no meio da sequência aborta com o estado nomeado; nenhum byte é
    descartado (delete é proibido neste ambiente e não é usado aqui).
    """
    if flags == _RENAME_NOREPLACE:
        try:
            os.stat(new_name, dir_fd=new_dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST))
        os.rename(
            old_name, new_name,
            src_dir_fd=old_dir_fd, dst_dir_fd=new_dir_fd,
        )
        return
    if flags == _RENAME_EXCHANGE:
        if old_dir_fd != new_dir_fd:
            raise OSError(
                errno.EINVAL,
                "fallback EXCHANGE exige o mesmo diretório nas duas pontas",
            )
        swap_name = None
        for _ in range(8):
            candidate = f".{new_name}.xchg-{secrets.token_hex(16)}"
            try:
                os.link(
                    new_name, candidate,
                    src_dir_fd=new_dir_fd, dst_dir_fd=new_dir_fd,
                    follow_symlinks=False,
                )
            except FileExistsError:
                continue
            swap_name = candidate
            break
        if swap_name is None:
            raise OSError(
                errno.EEXIST, "fallback EXCHANGE não reservou nome de swap")
        try:
            os.rename(
                old_name, new_name,
                src_dir_fd=old_dir_fd, dst_dir_fd=new_dir_fd,
            )
        except OSError as swap_error:
            raise OSError(
                swap_error.errno,
                "fallback EXCHANGE abortou após reservar "
                f"hardlink {swap_name}; alvo intacto — remova o hardlink "
                f"manualmente: {os.strerror(swap_error.errno)}",
            ) from swap_error
        os.rename(
            swap_name, old_name,
            src_dir_fd=new_dir_fd, dst_dir_fd=old_dir_fd,
        )
        return
    raise OSError(
        errno.EINVAL, f"fallback não implementado para flags={flags}")


def _open_parent_directory(path: pathlib.Path | str) -> tuple[int, str, pathlib.Path]:
    raw = os.fspath(path)
    if not isinstance(raw, str):
        raise TypeError("path de saída deve ser texto")
    if not raw or "\x00" in raw:
        raise ValueError("path de saída inválido")
    absolute = pathlib.Path(os.path.abspath(raw))
    if absolute.name in ("", ".", ".."):
        raise ValueError("path de saída deve apontar para arquivo")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    directory_fd = os.open(os.path.sep, flags)
    try:
        for component in absolute.parent.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        return directory_fd, absolute.name, absolute
    except Exception:
        os.close(directory_fd)
        raise


def _read_snapshot_at(
    directory_fd: int,
    name: str,
    *,
    missing_ok: bool,
    max_bytes: int | None = None,
) -> _Snapshot | None:
    if max_bytes is not None and (
            type(max_bytes) is not int or max_bytes < 0):
        raise ValueError("max_bytes deve ser inteiro não negativo")
    try:
        file_fd = os.open(
            name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    try:
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError(f"alvo deve ser arquivo regular: {name}")
        if max_bytes is not None and before.st_size > max_bytes:
            raise ValueError(
                f"arquivo excede limite de {max_bytes} bytes: {name}")
        chunks: list[bytes] = []
        total = 0
        while True:
            read_size = 1024 * 1024
            if max_bytes is not None:
                # Leia no máximo um byte além do orçamento restante. Assim o
                # limite continua válido se o arquivo crescer depois do
                # primeiro fstat, sem reservar o payload excedente inteiro.
                read_size = min(read_size, max_bytes - total + 1)
            chunk = os.read(file_fd, read_size)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                raise ValueError(
                    f"arquivo excede limite de {max_bytes} bytes: {name}")
            chunks.append(chunk)
        after = os.fstat(file_fd)
        identity_before = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns, before.st_nlink,
        )
        identity_after = (
            after.st_dev, after.st_ino, after.st_size,
            after.st_mtime_ns, after.st_ctime_ns, after.st_nlink,
        )
        if identity_before != identity_after:
            raise CASMismatch(f"arquivo mudou durante leitura segura: {name}")
        payload = b"".join(chunks)
        return _Snapshot(
            payload=payload,
            digest=_sha256(payload),
            device=after.st_dev,
            inode=after.st_ino,
            mode=stat.S_IMODE(after.st_mode),
            nlink=after.st_nlink,
        )
    finally:
        os.close(file_fd)


def snapshot_sha256(
    path: pathlib.Path | str,
    *,
    max_bytes: int | None = None,
) -> str:
    """Lê o hash esperado sem seguir symlink e autentica hardlinks."""
    directory_fd, name, _ = _open_parent_directory(path)
    try:
        snapshot = _read_snapshot_at(
            directory_fd, name, missing_ok=True, max_bytes=max_bytes)
        if snapshot is None:
            return _sha256(b"")
        if snapshot.nlink != 1:
            raise RuntimeError(f"alvo deve ter exatamente um hardlink: {path}")
        return snapshot.digest
    finally:
        os.close(directory_fd)


def read_regular_file_snapshot(
    path: pathlib.Path | str,
    *,
    max_bytes: int | None = None,
) -> RegularFileSnapshot:
    """Relê bytes/hash atomicamente, recusando ausência, symlink e hardlink.

    Consumidores de claims de Workflow precisam analisar exatamente os mesmos
    bytes cujo digest autenticam. Duas chamadas independentes ``read_bytes`` +
    ``snapshot_sha256`` reabririam uma janela TOCTOU entre conteúdo e hash.
    """
    directory_fd, name, absolute = _open_parent_directory(path)
    try:
        snapshot = _read_snapshot_at(
            directory_fd, name, missing_ok=False, max_bytes=max_bytes)
        if snapshot is None:  # apenas para estreitar o tipo; missing_ok=False
            raise FileNotFoundError(absolute)
        if snapshot.nlink != 1:
            raise RuntimeError(
                f"alvo deve ter exatamente um hardlink: {absolute}")
        return RegularFileSnapshot(snapshot.payload, snapshot.digest)
    finally:
        os.close(directory_fd)


def _review_jsonl_records(
    payload: bytes,
    label: str,
) -> tuple[tuple[str, ...], dict[str, bytes]]:
    if not payload or not payload.endswith(b"\n"):
        raise ValueError(f"{label} é vazio ou não termina com newline")
    intents: list[str] = []
    raw_by_intent: dict[str, bytes] = {}
    for line_number, raw_line in enumerate(payload[:-1].split(b"\n"), 1):
        if not raw_line:
            raise ValueError(f"{label} contém linha vazia: {line_number}")
        row = decode_json_no_duplicate_keys(
            raw_line, f"{label}:{line_number}")
        if not isinstance(row, dict):
            raise ValueError(f"{label} não contém objeto: {line_number}")
        intent_id = row.get("intent_id")
        if (not isinstance(intent_id, str) or
                _INTENT_ID.fullmatch(intent_id) is None or
                intent_id in raw_by_intent):
            raise ValueError(
                f"{label} tem intent_id ausente/duplicado: {line_number}")
        intents.append(intent_id)
        raw_by_intent[intent_id] = raw_line
    return tuple(intents), raw_by_intent


def verify_staged_review_scope(
    root: pathlib.Path | str,
    workspace_path: pathlib.Path | str,
    staged_path: pathlib.Path | str,
    target_rel_path: str,
    target_sha256: str,
    target_intent_ids: list[str],
    review_target_intent_ids: list[str],
    preserved_record_sha256: Mapping[str, str],
    *,
    file_wide_review: bool,
) -> RegularFileSnapshot:
    """Capture one staged payload after authenticating its complete scope.

    The caller must pass ``returned.payload`` directly to ``atomic_replace_cas``.
    Reopening ``staged_path`` would discard the TOCTOU guarantee established by
    the descriptor-relative capture below.
    """
    if (not isinstance(target_rel_path, str) or
            not _canonical_review_shard(target_rel_path) or
            not isinstance(target_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", target_sha256) is None or
            type(file_wide_review) is not bool):
        raise ValueError("identidade target/escopo de revisão inválida")

    def canonical_intents(value: object, label: str) -> tuple[str, ...]:
        if (not isinstance(value, list) or not value or
                len(value) != len(set(value)) or
                any(not isinstance(intent, str) or
                    _INTENT_ID.fullmatch(intent) is None for intent in value)):
            raise ValueError(f"{label} não é lista canônica não vazia")
        return tuple(value)

    target_ids = canonical_intents(target_intent_ids, "target_intent_ids")
    review_ids = canonical_intents(
        review_target_intent_ids, "review_target_intent_ids")
    target_set = set(target_ids)
    review_set = set(review_ids)
    if (not review_set.issubset(target_set) or
            review_ids != tuple(
                intent for intent in target_ids if intent in review_set)):
        raise ValueError(
            "review_target_intent_ids não é subsequência exata do target")
    if file_wide_review and review_ids != target_ids:
        raise ValueError("revisão file-wide deve cobrir todos os intent_ids")
    expected_preserved_ids = tuple(
        intent for intent in target_ids if intent not in review_set)
    if (not isinstance(preserved_record_sha256, Mapping) or
            set(preserved_record_sha256) != set(expected_preserved_ids) or
            any(not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None
                for digest in preserved_record_sha256.values())):
        raise ValueError(
            "preserved_record_sha256 não é o complemento exato da revisão")

    canonical_root = pathlib.Path(os.path.abspath(os.fspath(root)))
    target = read_regular_file_snapshot(
        canonical_root / target_rel_path, max_bytes=64 * 1024 * 1024)
    if target.digest != target_sha256:
        raise CASMismatch("target mudou depois da fila de revisão")
    observed_target_ids, target_raw = _review_jsonl_records(
        target.payload, "target de revisão")
    if observed_target_ids != target_ids:
        raise ValueError(
            "target_intent_ids diverge da preimagem capturada")
    computed_preserved = {
        intent: _sha256(target_raw[intent])
        for intent in expected_preserved_ids
    }
    if dict(preserved_record_sha256) != computed_preserved:
        raise ValueError(
            "hash preservado diverge dos bytes crus da preimagem")

    raw_workspace = os.fspath(workspace_path)
    raw_staged = os.fspath(staged_path)
    if (not isinstance(raw_workspace, str) or not raw_workspace or
            not isinstance(raw_staged, str) or not raw_staged or
            "\x00" in raw_workspace or "\x00" in raw_staged):
        raise ValueError("workspace/staged inválido")
    absolute_workspace = pathlib.Path(os.path.abspath(raw_workspace))
    absolute_staged = pathlib.Path(os.path.abspath(raw_staged))
    if (absolute_staged.parent != absolute_workspace or
            absolute_staged.name in ("", ".", "..")):
        raise ValueError("staged deve ser filho direto do workspace autenticado")

    parent_fd, workspace_name, _ = _open_parent_directory(absolute_workspace)
    workspace_fd: int | None = None
    try:
        workspace_fd = os.open(
            workspace_name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        workspace_info = os.fstat(workspace_fd)
        if (not stat.S_ISDIR(workspace_info.st_mode) or
                stat.S_IMODE(workspace_info.st_mode) != 0o700 or
                workspace_info.st_uid != os.geteuid()):
            raise RuntimeError(
                "workspace deve ser diretório privado 0700 do processo")
        staged = _read_snapshot_at(
            workspace_fd,
            absolute_staged.name,
            missing_ok=False,
            max_bytes=64 * 1024 * 1024,
        )
        if staged is None:  # estreitamento: missing_ok=False
            raise FileNotFoundError(absolute_staged)
        if staged.nlink != 1:
            raise RuntimeError("staged deve ter exatamente um hardlink")
    finally:
        if workspace_fd is not None:
            os.close(workspace_fd)
        os.close(parent_fd)

    staged_ids, staged_raw = _review_jsonl_records(
        staged.payload, "staged de revisão")
    if staged_ids != target_ids:
        raise ValueError(
            "staged alterou cardinalidade ou ordem dos intent_ids")
    changed_preserved = [
        intent for intent in expected_preserved_ids
        if (_sha256(staged_raw[intent]) !=
            preserved_record_sha256[intent])
    ]
    if changed_preserved:
        raise ValueError(
            "staged alterou registro fora do escopo: " +
            ",".join(changed_preserved[:8]))
    return RegularFileSnapshot(staged.payload, staged.digest)


def _dependency_epoch_without_self(
    target: pathlib.Path | str,
    dependencies: Mapping[pathlib.Path | str, str | None] | None,
) -> Mapping[pathlib.Path | str, str | None] | None:
    """Remove o próprio alvo do epoch: ele muda por definição na troca.

    O contrato semântico de escrita lista como dependência TODO shard citado
    em ``target_rel_path``/``superseded_target_rel_path``, inclusive o shard
    que está sendo promovido. ``atomic_replace_cas`` revalida o epoch depois
    do ``RENAME_EXCHANGE``: relendo o alvo já trocado, o hash pré-troca
    gravado no epoch NUNCA bate e a promoção aborta com ``CASMismatch``
    determinístico (reproduzido em telecom_energia-16 e glossario2-14, com
    o staged preservado em ``.stale-cas-dependency-drift-staged-*``). O
    estado pré-troca do alvo continua autenticado — de forma mais forte —
    pelo ``expected_sha256`` do próprio CAS, então excluir a autorreferência
    não afrouxa nenhuma garantia; apenas remove a contradição entre "o alvo
    deve mudar" e "esta dependência não pode mudar".
    """
    if dependencies is None or not isinstance(dependencies, Mapping):
        return dependencies
    try:
        target_absolute = os.path.abspath(os.fspath(target))
        filtered = {
            dependency_path: digest
            for dependency_path, digest in dependencies.items()
            if os.path.abspath(os.fspath(dependency_path)) != target_absolute
        }
    except TypeError:
        # Entrada malformada continua sendo responsabilidade (e erro
        # canônico) de _assert_dependency_epoch.
        return dependencies
    if len(filtered) == len(dependencies):
        return dependencies
    return filtered


_EPOCH_VERIFICATION_WORKERS = min(4, os.cpu_count() or 1)
_EPOCH_PARALLEL_THRESHOLD = 32
_EPOCH_SLICES_PER_WORKER = 4


def _verify_epoch_slice(
    task: tuple[int, tuple[tuple[int, str, str | None], ...]],
) -> list[tuple[int, Exception]]:
    """Reautentica uma fatia contígua do epoch dentro de UM diretório fixado.

    Devolve as falhas com a posição original em vez de levantá-las, para que o
    chamador relevante exatamente a primeira falha na ordem de iteração do
    mapping — o mesmo veredito do laço sequencial que esta função substitui.
    """
    directory_fd, entries = task
    failures: list[tuple[int, Exception]] = []
    for position, absolute, expected in entries:
        try:
            snapshot = _read_snapshot_at(
                directory_fd, os.path.basename(absolute), missing_ok=True,
                max_bytes=64 * 1024 * 1024)
            if expected is None:
                if snapshot is not None:
                    failures.append((position, CASMismatch(
                        "dependência antes ausente apareceu: "
                        f"{pathlib.Path(absolute)}")))
                continue
            if (snapshot is None or snapshot.nlink != 1 or
                    snapshot.digest != expected):
                failures.append((position, CASMismatch(
                    f"dependência evoluiu: {pathlib.Path(absolute)}")))
        except Exception as error:  # devolvida intacta e relevantada em ordem
            failures.append((position, error))
    return failures


def _assert_dependency_epoch(
    dependencies: Mapping[pathlib.Path | str, str | None] | None,
) -> None:
    """Reautentica presença/ausência exata sem reter payloads em memória.

    Esta é a guarda fail-closed que cerca toda escrita: ela RELÊ e re-hasheia
    cada dependência do epoch imediatamente antes e depois do
    ``RENAME_EXCHANGE``. Nenhum atalho por carimbo de stat entra aqui — é
    justamente esta releitura integral que torna seguro o índice incremental
    usado na carga do contrato, porque um digest derivado de stat que não
    corresponda aos bytes vivos morre aqui como ``CASMismatch``.

    O que mudou em 2026-08-04 foi só a FORMA de percorrer. O epoch do contrato
    v3 cobre o estoque inteiro (866 arquivos / 52 MB no acervo atual) e era
    percorrido entrada a entrada, cada uma recaminhando o path desde ``/`` e
    hasheando com o processo ocioso durante a I/O. Agora o diretório-pai é
    aberto UMA vez por diretório (4 no acervo atual, contra 5.178 aberturas de
    componente) e as entradas são verificadas em fatias contíguas distribuídas
    entre threads — ``os.read`` e ``hashlib`` liberam a GIL. Medido: 176 ms ->
    58 ms por passagem.

    Fixar o descritor do diretório é mais estrito, não menos: o caminhamento
    repetido seguiria um diretório TROCADO no meio da verificação, enquanto o
    descritor fixado permanece preso ao inode original — é o mesmo padrão que
    ``atomic_replace_cas`` já usa ao manter um único ``directory_fd`` para ler,
    criar e renomear. Bytes lidos, digests comparados e a primeira falha
    levantada são idênticos aos do laço sequencial; nenhuma dependência sai do
    epoch e nenhuma verificação é pulada.
    """
    if dependencies is None:
        return
    if not isinstance(dependencies, Mapping) or len(dependencies) > 50_000:
        raise ValueError("epoch de dependências deve ser mapping bounded")
    seen: set[str] = set()
    entries: list[tuple[int, str, str | None]] = []
    # O laço original intercalava validação e verificação: uma entrada inválida
    # na posição k só era alcançada depois de 0..k-1 terem sido verificadas (e
    # de qualquer divergência delas ter sido levantada primeiro). O erro de
    # parada é guardado com esse mesmo contrato — as entradas anteriores
    # continuam sendo verificadas e vencem o erro estrutural se falharem.
    stop_error: Exception | None = None
    for raw_path, expected in dependencies.items():
        try:
            path_text = os.fspath(raw_path)
        except TypeError as error:
            stop_error = ValueError("path do epoch de dependências é inválido")
            stop_error.__cause__ = error
            break
        if (not isinstance(path_text, str) or not path_text or
                "\x00" in path_text or
                (expected is not None and (
                    not isinstance(expected, str) or
                    re.fullmatch(r"[0-9a-f]{64}", expected) is None))):
            stop_error = ValueError(
                "entrada do epoch de dependências é inválida")
            break
        absolute = os.path.abspath(path_text)
        if absolute in seen:
            stop_error = ValueError(
                "epoch de dependências repete path canônico")
            break
        seen.add(absolute)
        entries.append((len(entries), absolute, expected))

    directory_fds: dict[str, int] = {}
    try:
        for position, absolute, _ in entries:
            parent = os.path.dirname(absolute)
            if parent in directory_fds:
                continue
            try:
                directory_fds[parent] = _open_parent_directory(absolute)[0]
            except Exception as error:
                # Abrir o diretório-pai falhava na mesma posição no laço
                # original: trunca aqui e deixa as anteriores decidirem.
                entries = entries[:position]
                stop_error = error
                break

        target_slice = max(1, -(-len(entries) // (
            _EPOCH_VERIFICATION_WORKERS * _EPOCH_SLICES_PER_WORKER)))
        tasks: list[tuple[int, tuple[tuple[int, str, str | None], ...]]] = []
        current: list[tuple[int, str, str | None]] = []
        current_parent = ""
        for item in entries:
            parent = os.path.dirname(item[1])
            if current and (parent != current_parent or
                            len(current) >= target_slice):
                tasks.append((directory_fds[current_parent], tuple(current)))
                current = []
            current_parent = parent
            current.append(item)
        if current:
            tasks.append((directory_fds[current_parent], tuple(current)))

        failures: list[tuple[int, Exception]] = []
        if len(entries) < _EPOCH_PARALLEL_THRESHOLD:
            for task in tasks:
                failures.extend(_verify_epoch_slice(task))
        else:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=_EPOCH_VERIFICATION_WORKERS) as pool:
                for slice_failures in pool.map(_verify_epoch_slice, tasks):
                    failures.extend(slice_failures)
    finally:
        for directory_fd in directory_fds.values():
            os.close(directory_fd)

    if failures:
        raise min(failures, key=lambda failure: failure[0])[1]
    if stop_error is not None:
        raise stop_error


def workflow_workspace_parent() -> pathlib.Path:
    """Diretório-pai canônico dos workspaces privados de composição e revisão.

    Fonte ÚNICA do namespace. ``create_workflow_workspace`` cria aqui quando
    ``base_dir`` é omitido, e todo consumidor que autentica um workspace pelo
    caminho — ``tools/finalize-v2-review`` (``_open_workspace``) e
    ``tools/verify-v2-workflow-results`` (receipt simples e de exact wave) —
    deriva o pai DAQUI em vez de repeti-lo. O motivo é medido (2026-09-05): o
    produtor saiu de ``/tmp`` sozinho em 92c6a7f8 (2026-08-04) e os três
    consumidores continuaram exigindo ``/tmp``; desde então cada workspace real
    do fluxo de revisão (``scripts/workflows/writing-review.js`` chama este
    produtor sem ``base_dir`` e passa o caminho ao finalizador) era recusado com
    "workspace não pertence ao namespace privado desta tarefa". Só devolve o
    caminho: quem cria é ``create_workflow_workspace``, que segue tolerando a
    árvore ausente do repositório.
    """
    return (pathlib.Path(__file__).resolve().parent.parent
            / ".agents" / "runtime" / "wworkspaces")


def create_workflow_workspace(
    slug: str,
    expected_sha256: str,
    base_dir: pathlib.Path | str | None = None,
) -> pathlib.Path:
    """Reserva namespace privado por execução para composição de shard.

    O CAS protege o destino final, mas não protege arquivos intermediários
    previsíveis em ``/tmp``. Dois lançamentos do mesmo lote e snapshot devem
    compor bytes em diretórios distintos antes de disputar o CAS final.

    ``base_dir`` omitido NÃO cai mais em ``/tmp``: o padrão passou a ser
    ``.agents/runtime/wworkspaces`` dentro do repositório (2026-08-04). O
    motivo é medido — o systemd apaga todo o conteúdo de /tmp a cada boot
    (``D /tmp`` em /usr/lib/tmpfiles.d/tmp.conf), e um lote inteiro de páginas
    redigidas some sem rastro se o workspace viver lá. Só
    ``generate-v2-blocked-promotion`` passava caminho do repositório
    explicitamente; qualquer chamador novo que esquecesse o argumento reabria o
    buraco por inteiro. Quem precisar de outro destino continua passando
    ``base_dir`` — o comportamento explícito não mudou.
    """
    if (not isinstance(slug, str) or
            re.fullmatch(r"[a-z0-9_]+(?:-[a-z0-9_]+)+", slug) is None):
        raise ValueError("slug de workflow deve ser canônico")
    if (not isinstance(expected_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise ValueError("expected_sha256 deve ser SHA-256 hexadecimal")
    if base_dir is None:
        padrao = workflow_workspace_parent()
        try:
            padrao.mkdir(parents=True, exist_ok=True)
            parent = os.fspath(padrao)
        except OSError:
            # Ambiente sem a árvore do repositório (sandbox, cópia isolada):
            # degrada para o diretório temporário do sistema em vez de abortar
            # a composição. O resgate de tools/generate-v2-workdir-rescue cobre
            # esse caso residual.
            parent = None
    else:
        parent = os.fspath(base_dir)
    workspace = pathlib.Path(tempfile.mkdtemp(
        prefix=f"wiki-v2-{slug}-{expected_sha256[:12]}-",
        dir=parent,
    ))
    workspace.chmod(0o700)
    return workspace


def authenticate_snapshot_set(
    before: Mapping[str, str],
    after: Mapping[str, str],
    report_paths: Iterable[str],
) -> dict[str, str]:
    """Liga um relatório multi-arquivo ao mesmo estoque antes e depois."""
    before_copy = dict(before)
    after_copy = dict(after)
    expected = set(report_paths)
    if (set(before_copy) != expected or set(after_copy) != expected or
            any(not isinstance(path, str) for path in expected)):
        raise CASMismatch("conjunto de shards mudou durante a produção")
    invalid = sorted(
        path for path, digest in [*before_copy.items(), *after_copy.items()]
        if (not isinstance(digest, str) or
            re.fullmatch(r"[0-9a-f]{64}", digest) is None)
    )
    if invalid:
        raise ValueError(f"snapshot sem SHA-256 canônico: {invalid[:8]}")
    changed = sorted(
        path for path, digest in before_copy.items()
        if after_copy[path] != digest
    )
    if changed:
        raise CASMismatch(
            f"bytes mudaram durante a produção: {changed[:8]}")
    return before_copy


def verify_review_dependency_snapshots(
    dependencies: Mapping[str, str],
) -> int:
    """Revalidate every shard that made a one-sided v3 repair safe."""
    if (not isinstance(dependencies, Mapping) or
            len(dependencies) > 50_000):
        raise ValueError("dependências distinctness devem ser mapping bounded")
    normalized: dict[str, str] = {}
    for path, digest in dependencies.items():
        if (not _canonical_review_shard(path) or path in normalized or
                not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            raise ValueError("dependência distinctness inválida")
        normalized[path] = digest
    items = sorted(normalized.items())
    for offset in range(0, len(items), 256):
        _assert_dependency_epoch(dict(items[offset:offset + 256]))
    return len(items)


def _create_temp_at(
    directory_fd: int,
    target_name: str,
    payload: bytes,
    mode: int,
) -> tuple[str, _Snapshot]:
    for _ in range(128):
        name = f".{target_name}.{secrets.token_hex(16)}.tmp"
        try:
            file_fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
        except FileExistsError:
            continue
        try:
            os.fchmod(file_fd, mode)
            view = memoryview(payload)
            while view:
                written = os.write(file_fd, view)
                if written <= 0:
                    raise OSError("escrita temporária não progrediu")
                view = view[written:]
            os.fsync(file_fd)
            info = os.fstat(file_fd)
            snapshot = _Snapshot(
                payload=payload,
                digest=_sha256(payload),
                device=info.st_dev,
                inode=info.st_ino,
                mode=stat.S_IMODE(info.st_mode),
                nlink=info.st_nlink,
            )
            return name, snapshot
        except Exception:
            try:
                os.unlink(name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            raise
        finally:
            os.close(file_fd)
    raise RuntimeError("não foi possível reservar temporário exclusivo")


def _same_snapshot(left: _Snapshot, right: _Snapshot) -> bool:
    return (
        left.digest == right.digest and
        left.device == right.device and
        left.inode == right.inode and
        left.mode == right.mode and
        left.nlink == right.nlink
    )


def _open_or_create_directory_at(parent_fd: int, name: str) -> int:
    """Abra diretório filho sem symlink; criação é durável no pai."""
    created = False
    try:
        os.mkdir(name, 0o755, dir_fd=parent_fd)
        created = True
    except FileExistsError:
        pass
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    child_fd = os.open(name, flags, dir_fd=parent_fd)
    info = os.fstat(child_fd)
    if not stat.S_ISDIR(info.st_mode):
        os.close(child_fd)
        raise RuntimeError(f"entrada fria não é diretório: {name}")
    if created:
        os.fsync(parent_fd)
    return child_fd


def _cold_terminal_recovery_directory_fd(
    directory_fd: int,
    target_name: str,
    label: str,
) -> int | None:
    """Roteie apenas o sucesso terminal canônico para incoming frio.

    Estados de rollback/conflito continuam no diretório de origem porque ainda
    são recovery operacional. O handoff frio é atômico no mesmo filesystem e o
    consumidor Go o autentica, journaliza e endereça por conteúdo em lote.
    """
    if label != "displaced-committed-retained":
        return None
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,190}\.jsonl", target_name) is None:
        return None
    try:
        directory_path = pathlib.Path(
            os.readlink(f"/proc/self/fd/{directory_fd}"))
    except OSError:
        return None
    stock_root = canonical_stock_root_for_target(directory_path / target_name)
    if stock_root is None:
        return None
    expected = pathlib.Path(stock_root) / "data/editorial/v2_pages"
    try:
        if directory_path.resolve(strict=True) != expected.resolve(strict=True):
            return None
    except OSError:
        return None

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    editorial_fd = os.open("..", flags, dir_fd=directory_fd)
    opened = [editorial_fd]
    try:
        vault_fd = _open_or_create_directory_at(
            editorial_fd, "v2_artifact_vault")
        opened.append(vault_fd)
        incoming_fd = _open_or_create_directory_at(vault_fd, "incoming")
        opened.append(incoming_fd)
        terminal_fd = _open_or_create_directory_at(
            incoming_fd, "review_queue_stale_cas")
        opened.append(terminal_fd)
        return opened.pop()
    finally:
        for opened_fd in reversed(opened):
            os.close(opened_fd)


def _preserve_recovery_entry(
    directory_fd: int,
    source_name: str,
    target_name: str,
    label: str,
) -> str:
    """Move bytes capturados para recibo forense único e auto-inventariado.

    O sucesso terminal do produtor canônico vai direto ao incoming frio; falha,
    rollback ou layout não canônico permanece ao lado do alvo para recovery.
    Nenhuma rota unlinka o inode, então um escritor não cooperativo com FD
    aberto continua ligado a um pathname recuperável.
    """
    cold_fd = _cold_terminal_recovery_directory_fd(
        directory_fd, target_name, label)
    destination_fd = directory_fd if cold_fd is None else cold_fd
    try:
        for _ in range(128):
            recovery_name = (
                f".{target_name}.stale-cas-{label}-"
                f"{secrets.token_hex(16)}"
            )
            try:
                _renameat2(
                    directory_fd, source_name,
                    destination_fd, recovery_name,
                    _RENAME_NOREPLACE,
                )
                os.fsync(directory_fd)
                if destination_fd != directory_fd:
                    os.fsync(destination_fd)
                return recovery_name
            except OSError as error:
                if error.errno == errno.EEXIST:
                    continue
                raise
        raise RuntimeError("não foi possível reservar recibo de recovery")
    finally:
        if cold_fd is not None:
            os.close(cold_fd)


def _canonical_stock_writer(function):
    @functools.wraps(function)
    def guarded(path, *args, **kwargs):
        stock_root = canonical_stock_root_for_target(path)
        if stock_root is None:
            return function(path, *args, **kwargs)
        with canonical_stock_write_lease(stock_root):
            return function(path, *args, **kwargs)
    return guarded


@_canonical_stock_writer
def atomic_replace_cas(
    path: pathlib.Path | str,
    payload: bytes,
    expected_sha256: str,
    *,
    dependency_sha256: Mapping[pathlib.Path | str, str | None] | None = None,
) -> None:
    """Troca ``path`` atomicamente somente se o conteúdo esperado persistir."""
    if not isinstance(payload, bytes):
        raise TypeError("payload deve ser bytes")
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ValueError("expected_sha256 deve ser SHA-256 hexadecimal")
    dependency_sha256 = _dependency_epoch_without_self(path, dependency_sha256)
    directory_fd, target_name, target = _open_parent_directory(path)
    lock_key = hashlib.sha256(
        os.path.abspath(os.fspath(target)).encode("utf-8")
    ).hexdigest()
    lock_path = pathlib.Path(tempfile.gettempdir()) / (
        f"v2-review-queue-{lock_key}.lock"
    )
    try:
        lock_directory_fd, lock_name, _ = _open_parent_directory(lock_path)
    except Exception:
        os.close(directory_fd)
        raise
    try:
        lock_fd = os.open(
            lock_name,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=lock_directory_fd,
        )
        lock_info = os.fstat(lock_fd)
        if not stat.S_ISREG(lock_info.st_mode) or lock_info.st_nlink != 1:
            raise RuntimeError("lock deve ser arquivo regular exclusivo")
        os.fchmod(lock_fd, 0o600)
    except Exception:
        if "lock_fd" in locals():
            os.close(lock_fd)
        os.close(lock_directory_fd)
        os.close(directory_fd)
        raise
    temp_name: str | None = None
    # Antes do EXCHANGE, temp é criação privada e pode ser apagado em erro.
    # Depois do EXCHANGE, ele passa a nomear bytes que podem ter escritor com
    # FD aberto; dali em diante cleanup destrutivo é proibido.
    temp_cleanup_allowed = True
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise CASMismatch(
                f"produtor concorrente possui o lock de {target}; fail-fast"
            ) from error
        original = _read_snapshot_at(
            directory_fd, target_name, missing_ok=True)
        if original is not None and original.nlink != 1:
            raise RuntimeError(
                f"alvo deve ter exatamente um hardlink antes da troca: {target}"
            )
        current_digest = _sha256(b"") if original is None else original.digest
        if current_digest != expected_sha256:
            raise CASMismatch(f"snapshot mudou antes da troca: {target}")
        mode = 0o644 if original is None else original.mode
        temp_name, staged = _create_temp_at(
            directory_fd, target_name, payload, mode)
        try:
            if original is None:
                _assert_dependency_epoch(dependency_sha256)
                try:
                    _renameat2(
                        directory_fd, temp_name,
                        directory_fd, target_name,
                        _RENAME_NOREPLACE,
                    )
                except OSError as error:
                    if error.errno == errno.EEXIST:
                        raise CASMismatch(
                            f"snapshot ausente foi criado concorrentemente: {target}"
                        ) from error
                    raise
                temp_name = None
                os.fsync(directory_fd)
                installed = _read_snapshot_at(
                    directory_fd, target_name, missing_ok=False)
                if installed is None or not _same_snapshot(installed, staged):
                    raise CASMismatch(
                        f"saída instalada mudou durante criação: {target}"
                    )
                try:
                    _assert_dependency_epoch(dependency_sha256)
                except (OSError, RuntimeError, ValueError) as dependency_error:
                    recovery_name = _preserve_recovery_entry(
                        directory_fd, target_name, target_name,
                        "dependency-drift-new-target",
                    )
                    raise CASMismatch(
                        "dependência mudou durante criação; alvo novo abortado e "
                        f"preservado em {target.parent / recovery_name}"
                    ) from dependency_error
                return

            _assert_dependency_epoch(dependency_sha256)
            temp_cleanup_allowed = False
            _renameat2(
                directory_fd, temp_name,
                directory_fd, target_name,
                _RENAME_EXCHANGE,
            )
            os.fsync(directory_fd)
            try:
                displaced = _read_snapshot_at(
                    directory_fd, temp_name, missing_ok=False)
                installed = _read_snapshot_at(
                    directory_fd, target_name, missing_ok=False)
            except Exception as authentication_error:
                preserved_name = temp_name
                temp_name = None
                raise RuntimeError(
                    "CAS não pôde autenticar as duas entradas; "
                    f"target preservado={target}, displaced preservado="
                    f"{target.parent / preserved_name}"
                ) from authentication_error
            displaced_changed = (
                displaced is None or not _same_snapshot(displaced, original))
            installed_changed = (
                installed is None or not _same_snapshot(installed, staged))
            if installed_changed:
                label = (
                    "both-changed" if displaced_changed else
                    "displaced-original"
                )
                try:
                    recovery_name = _preserve_recovery_entry(
                        directory_fd, temp_name, target_name, label,
                    )
                    temp_name = None
                except Exception as preserve_error:
                    preserved_name = temp_name
                    temp_name = None
                    raise RuntimeError(
                        "target evoluído preservado e displaced mantido em "
                        f"{target.parent / preserved_name}: {target}"
                    ) from preserve_error
                raise CASMismatch(
                    "target instalado mudou após exchange; evolução mantida "
                    f"em {target}; displaced preservado em "
                    f"{target.parent / recovery_name}"
                )
            if displaced_changed:
                try:
                    _renameat2(
                        directory_fd, temp_name,
                        directory_fd, target_name,
                        _RENAME_EXCHANGE,
                    )
                    os.fsync(directory_fd)
                except OSError as rollback_error:
                    preserved_name = temp_name
                    temp_name = None
                    raise RuntimeError(
                        "CAS divergiu e rollback falhou; entradas preservadas "
                        f"em {target} e {target.parent / preserved_name}"
                    ) from rollback_error
                # Outro escritor pode evoluir o target entre a autenticação
                # acima e este rollback. Nesse caso a evolução acabou de ser
                # deslocada para ``temp_name``; apagá-lo no ``finally`` perderia
                # bytes concorrentes. Autentique as duas pernas após a troca e
                # mova qualquer divergência para um recovery path exclusivo.
                try:
                    restored = _read_snapshot_at(
                        directory_fd, target_name, missing_ok=False)
                    rollback_displaced = _read_snapshot_at(
                        directory_fd, temp_name, missing_ok=False)
                except Exception as rollback_auth_error:
                    try:
                        recovery_name = _preserve_recovery_entry(
                            directory_fd, temp_name, target_name,
                            "rollback-unauthenticated",
                        )
                        temp_name = None
                    except Exception as preserve_error:
                        preserved_name = temp_name
                        temp_name = None
                        raise RuntimeError(
                            "rollback não autenticado; target e entrada "
                            f"preservados em {target} e "
                            f"{target.parent / preserved_name}"
                        ) from preserve_error
                    raise RuntimeError(
                        "rollback não autenticado; entrada deslocada preservada "
                        f"em {target.parent / recovery_name}"
                    ) from rollback_auth_error
                restored_changed = (
                    restored is None or not _same_snapshot(restored, displaced))
                rollback_displaced_changed = (
                    rollback_displaced is None or
                    not _same_snapshot(rollback_displaced, installed))
                if restored_changed or rollback_displaced_changed:
                    label = (
                        "rollback-both-changed" if restored_changed else
                        "rollback-target-evolution"
                    )
                    try:
                        recovery_name = _preserve_recovery_entry(
                            directory_fd, temp_name, target_name, label,
                        )
                        temp_name = None
                    except Exception as preserve_error:
                        preserved_name = temp_name
                        temp_name = None
                        raise RuntimeError(
                            "rollback encontrou evolução concorrente; entradas "
                            f"preservadas em {target} e "
                            f"{target.parent / preserved_name}"
                        ) from preserve_error
                    raise CASMismatch(
                        "rollback encontrou evolução concorrente; target mantido "
                        f"em {target} e entrada deslocada preservada em "
                        f"{target.parent / recovery_name}"
                    )
                # Mesmo depois da autenticação, um escritor não cooperativo
                # pode manter FD aberto para o inode que agora está em
                # ``temp_name`` e escrever entre esta linha e um unlink. Não
                # existe read-then-unlink capaz de fechar essa janela. Retenha
                # a entrada sob nome exclusivo: qualquer escrita tardia pelo
                # FD continuará ligada a um path recuperável.
                try:
                    _preserve_recovery_entry(
                        directory_fd, temp_name, target_name,
                        "rollback-staged-retained",
                    )
                    temp_name = None
                except Exception as preserve_error:
                    preserved_name = temp_name
                    temp_name = None
                    raise RuntimeError(
                        "rollback restaurou target, mas entrada deslocada "
                        "precisa permanecer retida em "
                        f"{target.parent / preserved_name}"
                    ) from preserve_error
                raise CASMismatch(
                    f"snapshot deslocado mudou; rollback preservou {target}"
                )
            try:
                _assert_dependency_epoch(dependency_sha256)
            except (OSError, RuntimeError, ValueError) as dependency_error:
                try:
                    _renameat2(
                        directory_fd, temp_name,
                        directory_fd, target_name,
                        _RENAME_EXCHANGE,
                    )
                    os.fsync(directory_fd)
                    restored = _read_snapshot_at(
                        directory_fd, target_name, missing_ok=False)
                    aborted = _read_snapshot_at(
                        directory_fd, temp_name, missing_ok=False)
                    if (restored is None or not _same_snapshot(restored, original) or
                            aborted is None or not _same_snapshot(aborted, staged)):
                        raise RuntimeError(
                            "rollback por drift de dependência encontrou evolução")
                    recovery_name = _preserve_recovery_entry(
                        directory_fd, temp_name, target_name,
                        "dependency-drift-staged",
                    )
                    temp_name = None
                except Exception as rollback_error:
                    preserved_name = temp_name
                    temp_name = None
                    raise RuntimeError(
                        "drift de dependência não pôde abortar sem perda; entradas "
                        f"preservadas em {target} e "
                        f"{target.parent / preserved_name}"
                    ) from rollback_error
                raise CASMismatch(
                    "dependência mudou durante CAS; preimagem restaurada e staged "
                    f"preservado em {target.parent / recovery_name}"
                ) from dependency_error
            # Retenção é obrigatória mesmo no sucesso. Um terceiro pode ter
            # aberto o inode original antes do EXCHANGE e escrever nele depois
            # das duas leituras de autenticação. Renomeá-lo, em vez de apagá-lo,
            # mantém essas escritas futuras alcançáveis sem tocar no novo alvo.
            try:
                _preserve_recovery_entry(
                    directory_fd, temp_name, target_name,
                    "displaced-committed-retained",
                )
                temp_name = None
            except Exception as preserve_error:
                preserved_name = temp_name
                temp_name = None
                raise RuntimeError(
                    "CAS instalou o novo target, mas a entrada deslocada "
                    f"precisa permanecer retida em {target.parent / preserved_name}"
                ) from preserve_error
        finally:
            if temp_name is not None and temp_cleanup_allowed:
                try:
                    os.unlink(temp_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            elif temp_name is not None:
                # Melhor esforço para dar nome explícito ao recibo. Se até a
                # renomeação falhar, o nome .tmp exclusivo continua existindo;
                # em nenhuma hipótese ele é apagado após um EXCHANGE tentado.
                try:
                    _preserve_recovery_entry(
                        directory_fd, temp_name, target_name,
                        "post-exchange-exception-retained",
                    )
                except Exception:
                    pass
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        os.close(lock_directory_fd)
        os.close(directory_fd)


def atomic_replace_cas_pair_roll_forward(
    first_path: pathlib.Path | str,
    first_payload: bytes,
    first_expected_sha256: str,
    second_path: pathlib.Path | str,
    second_payload: bytes,
    second_expected_sha256: str,
) -> tuple[str, str]:
    """Advance a derived-output pair without ever restoring old bytes.

    The caller serializes the producer and authenticates its input epoch. If
    the second leg fails, the first postimage is intentionally left installed;
    the next invocation observes that digest, skips the completed leg and
    advances only the missing leg. Any digest outside the declared pre/post
    states is external drift and fails closed.
    """
    if (not isinstance(first_payload, bytes) or
            not isinstance(second_payload, bytes)):
        raise TypeError("payloads do par CAS devem ser bytes")
    first_post = _sha256(first_payload)
    second_post = _sha256(second_payload)
    for label, expected in (
            ("primeira", first_expected_sha256),
            ("segunda", second_expected_sha256)):
        if re.fullmatch(r"[0-9a-f]{64}", expected or "") is None:
            raise ValueError(f"preimage da {label} perna não é SHA-256")

    first_observed = snapshot_sha256(
        first_path, max_bytes=128 * 1024 * 1024)
    if first_observed not in {first_expected_sha256, first_post}:
        raise CASMismatch("primeira perna do par sofreu drift externo")
    if first_observed != first_post:
        atomic_replace_cas(
            first_path, first_payload, first_expected_sha256)
    if snapshot_sha256(
            first_path, max_bytes=128 * 1024 * 1024) != first_post:
        raise CASMismatch("primeira perna do par não fechou postimage")

    second_observed = snapshot_sha256(
        second_path, max_bytes=128 * 1024 * 1024)
    if second_observed not in {second_expected_sha256, second_post}:
        raise CASMismatch("segunda perna do par sofreu drift externo")
    try:
        if second_observed != second_post:
            atomic_replace_cas(
                second_path, second_payload, second_expected_sha256)
    except Exception as error:
        raise CASMismatch(
            "segunda perna falhou; primeira permanece no postimage e o "
            "próximo ciclo deve completar somente para frente") from error
    if snapshot_sha256(
            second_path, max_bytes=128 * 1024 * 1024) != second_post:
        raise CASMismatch("segunda perna do par não fechou postimage")
    return first_post, second_post
