#!/usr/bin/env python3
"""Plan deterministic V2 source-hint joins without mutating source catalogs.

The planner is deliberately not a catalog generator and not a publication
gate.  It groups unresolved portfolio hints by an exact legal-source identity,
then reports either:

* an existing catalog alias review candidate backed only by repeated page
  observations for the exact act/provision identity; or
* a blocked research plan carrying the existing official URLs that need
  juridical/editorial review.

Page repetition is explicitly not called independent provenance or consensus.
No record produced here authorizes a rewrite, approval, rendering, sitemap
inclusion or publication. Existing official source text is never read or copied.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import datetime as dt
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata
from urllib.parse import parse_qsl, unquote, urlsplit, urlunsplit


MAX_CATALOG_BYTES = 8 << 20
MAX_REGISTRY_BYTES = 16 << 20
MAX_JSONL_BYTES = 64 << 20
MAX_INPUT_FILES = 200_000
MAX_HINT_RUNES = 512
MAX_SOURCE_RUNES = 8_192
MAX_SAMPLES = 3
MAX_VERIFICATION_AGE_DAYS = 30

INTENT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CANONICAL_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ARTICLE_MARKERS = {"art", "arts", "artigo", "artigos"}
ARTICLE_STOP = {
    "par", "paragrafo", "inciso", "incisos", "alinea", "alineas",
    "lei", "decreto", "resolucao", "codigo", "constituicao", "sumula",
    "tema", "caput", "seguro", "responsabilidade", "procedimento",
}
CONNECTORS = {"a", "e", "ao", "ate", "do", "dos", "ou"}

ISSUER_ALIASES = {
    "anac": "anac", "anatel": "anatel", "aneel": "aneel", "ans": "ans",
    "anpd": "anpd", "cd-anpd": "cd-anpd", "cfm": "cfm", "cgu": "cgu",
    "cjf": "cjf", "cnj": "cnj", "cnsp": "cnsp", "contran": "contran",
    "cvm": "cvm", "inss": "inss", "rfb": "rfb", "susep": "susep",
    "stf": "stf", "stj": "stj", "tst": "tst", "tnu": "tnu",
}
HOST_ISSUERS = {
    "www.anac.gov.br": "anac", "www.gov.br/anac": "anac",
    "www.anatel.gov.br": "anatel", "informacoes.anatel.gov.br": "anatel",
    "www.aneel.gov.br": "aneel", "www2.aneel.gov.br": "aneel",
    "www.ans.gov.br": "ans", "bvsms.saude.gov.br": "ans",
    "www.gov.br/anpd": "anpd", "atos.cnj.jus.br": "cnj",
    "www.cnj.jus.br": "cnj", "portal.cfm.org.br": "cfm",
    "sistemas.cfm.org.br": "cfm", "www.gov.br/inss": "inss",
    "www.gov.br/receitafederal": "rfb", "www.gov.br/susep": "susep",
    "www2.susep.gov.br": "susep", "processo.stj.jus.br": "stj",
    "www.stj.jus.br": "stj", "portal.stf.jus.br": "stf",
    "jurisprudencia.stf.jus.br": "stf", "www.tst.jus.br": "tst",
}
ISSUER_SENSITIVE_KINDS = {
    "resolucao", "instrucao-normativa", "circular", "provimento",
    "sumula", "tema", "re", "resp", "adi", "adc", "adpf", "are",
}
YEAR_REQUIRED_KINDS = {
    "lei", "lei-complementar", "decreto-lei", "decreto", "resolucao",
    "instrucao-normativa", "circular", "provimento", "emenda-constitucional",
}
GENERIC_ALIAS_LABELS = {
    "anac", "anatel", "aneel", "ans", "bcb", "cnj", "gov br", "inss",
    "planalto", "receita federal", "stf", "stj", "susep", "tst",
    "jurisprudencia", "jurisprudencia stj", "stj jurisprudencia",
    "lei", "lei complementar", "lc", "decreto", "decreto lei", "resolucao",
    "res", "rn", "instrucao normativa", "in", "circular", "provimento",
    "sumula", "tema", "re", "resp", "are", "adi", "adc", "adpf",
    "constituicao", "cf", "crfb", "emenda constitucional", "ec", "codigo",
}
NAME_PREFIXES = {
    "planalto", "camara", "senado", "stf", "stj", "tst", "cnj", "anac",
    "anatel", "aneel", "ans", "anpd", "inss", "susep", "bcb", "cgu",
}


@dataclass(frozen=True, order=True)
class ActIdentity:
    kind: str
    issuer: str
    number: str
    year: str = ""

    @property
    def coarse(self) -> tuple[str, str, str]:
        return self.kind, self.issuer, self.number

    @property
    def key(self) -> str:
        issuer = self.issuer or "_"
        year = self.year or "_"
        return f"{self.kind}:{issuer}:{self.number}:{year}"


@dataclass(frozen=True)
class Signature:
    identity: ActIdentity
    articles: tuple[str, ...] = ()
    article_relation: str = ""
    paragraphs: tuple[str, ...] = ()
    incisos: tuple[str, ...] = ()
    alineas: tuple[str, ...] = ()
    caput: bool = False
    temporal_status: str = ""

    @property
    def key(self) -> str:
        articles = ",".join(self.articles) or "_"
        article_relation = self.article_relation or "_"
        paragraphs = ",".join(self.paragraphs) or "_"
        incisos = ",".join(self.incisos) or "_"
        alineas = ",".join(self.alineas) or "_"
        temporal = self.temporal_status or "_"
        return (f"{self.identity.key}:art={articles}:artrel={article_relation}:par={paragraphs}:"
                f"inc={incisos}:ali={alineas}:caput={int(self.caput)}:tempo={temporal}")


@dataclass
class HintAggregate:
    hint: str
    occurrences: int = 0
    researched_occurrences: int = 0
    pending_occurrences: int = 0
    sample_intents: list[str] = field(default_factory=list)

    def add(self, intent_id: str, needs_research: bool) -> None:
        self.occurrences += 1
        if needs_research:
            self.pending_occurrences += 1
        else:
            self.researched_occurrences += 1
        if intent_id not in self.sample_intents and len(self.sample_intents) < MAX_SAMPLES:
            self.sample_intents.append(intent_id)


@dataclass
class EvidenceBucket:
    url: str
    registry_source_id: str
    observations: int = 0
    distinct_intent_hashes: set[str] = field(default_factory=set)
    distinct_files: set[str] = field(default_factory=set)
    samples: list[dict] = field(default_factory=list)

    def add(self, rel_path: str, intent_id: str, minimum: int) -> None:
        self.observations += 1
        digest = hashlib.sha256(intent_id.encode("utf-8")).hexdigest()[:24]
        if len(self.distinct_intent_hashes) < minimum:
            self.distinct_intent_hashes.add(digest)
        if len(self.distinct_files) < minimum:
            self.distinct_files.add(rel_path)
        sample = {"file": rel_path, "intent_id": intent_id}
        if sample not in self.samples and len(self.samples) < MAX_SAMPLES:
            self.samples.append(sample)

    @property
    def distinct_intents_lower_bound(self) -> int:
        return len(self.distinct_intent_hashes)

    @property
    def distinct_files_lower_bound(self) -> int:
        return len(self.distinct_files)


@dataclass(frozen=True)
class CatalogTarget:
    hint: str
    signature: Signature
    name: str
    url: str
    registry_source_id: str


class InputFingerprint:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self.files = 0
        self.bytes = 0

    def add(self, rel_path: str, payload: bytes) -> None:
        self._digest.update(rel_path.encode("utf-8"))
        self._digest.update(b"\0")
        self._digest.update(hashlib.sha256(payload).digest())
        self._digest.update(b"\n")
        self.files += 1
        self.bytes += len(payload)

    def report(self) -> dict:
        return {
            "sha256": self._digest.hexdigest(),
            "files": self.files,
            "bytes": self.bytes,
        }


def fold_text(value: str) -> str:
    value = value.replace("§", " paragrafo ").replace("º", " ").replace("ª", " ")
    decomposed = unicodedata.normalize("NFKD", value)
    folded = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    folded = folded.lower()
    folded = re.sub(r"(?<=\d)\.(?=\d)", "", folded)
    return folded


def tokens(value: str) -> list[str]:
    return re.findall(r"[a-z]+|\d+[a-z]?", fold_text(value))


def normalize_number(value: str) -> str:
    normalized = value.lower().replace(".", "")
    match = re.fullmatch(r"0*(\d+)([a-z]?)", normalized)
    if not match:
        return ""
    return str(int(match.group(1))) + match.group(2)


def extract_articles(value: str) -> tuple[str, ...]:
    sequence = tokens(value)
    result: list[str] = []
    for index, token in enumerate(sequence):
        if token not in ARTICLE_MARKERS:
            continue
        local: list[str] = []
        for candidate in sequence[index + 1:index + 18]:
            if candidate in ARTICLE_STOP:
                break
            if candidate in CONNECTORS or candidate in {"n", "no", "numero"}:
                continue
            article = normalize_number(candidate)
            if article:
                local.append(article)
                continue
            break
        if local:
            result.extend(local)
            break
    return tuple(dict.fromkeys(result))


ROMAN = re.compile(r"^(?=[ivxlcdm]+$)m{0,4}(?:cm|cd|d?c{0,3})"
                   r"(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})$")


def _ordered_unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _marked_values(sequence: list[str], markers: set[str], value_kind: str) -> tuple[str, ...]:
    values: list[str] = []
    all_markers = (ARTICLE_MARKERS | {"par", "paragrafo", "paragrafos", "inciso", "incisos",
                                      "alinea", "alineas", "caput"})
    for index, token in enumerate(sequence):
        if token not in markers:
            continue
        for candidate in sequence[index + 1:index + 12]:
            if candidate in all_markers or candidate in ARTICLE_STOP:
                break
            if ((candidate in CONNECTORS and not (value_kind == "alinea" and candidate == "a")) or
                    candidate in {"n", "no", "numero", "da", "das"}):
                continue
            value = ""
            if value_kind == "paragraph":
                value = "unico" if candidate == "unico" else normalize_number(candidate)
            elif value_kind == "inciso":
                value = candidate if ROMAN.fullmatch(candidate) else normalize_number(candidate)
            elif value_kind == "alinea":
                value = candidate if re.fullmatch(r"[a-z]", candidate) else ""
            if not value:
                break
            values.append(value)
    return _ordered_unique(values)


def extract_article_relation(sequence: list[str], articles: tuple[str, ...]) -> str:
    if not articles:
        return ""
    if len(articles) == 1:
        return "single"
    for index, token in enumerate(sequence):
        if token not in ARTICLE_MARKERS:
            continue
        connectors = []
        numbers_seen = 0
        for candidate in sequence[index + 1:index + 18]:
            if candidate in ARTICLE_STOP:
                break
            if normalize_number(candidate):
                numbers_seen += 1
                if numbers_seen >= 2:
                    break
                continue
            if numbers_seen and candidate in CONNECTORS:
                connectors.append(candidate)
                continue
            if numbers_seen:
                break
        if any(item in {"a", "ate"} for item in connectors):
            return "range"
        if any(item in {"e", "ou"} for item in connectors):
            return "list"
        return "sequence"
    return "sequence"


def extract_locator(value: str) -> tuple[tuple[str, ...], str, tuple[str, ...],
                                          tuple[str, ...], tuple[str, ...], bool, str]:
    sequence = tokens(value)
    articles = extract_articles(value)
    article_relation = extract_article_relation(sequence, articles)
    paragraphs = _marked_values(sequence, {"par", "paragrafo", "paragrafos"}, "paragraph")
    incisos = list(_marked_values(sequence, {"inciso", "incisos"}, "inciso"))
    alineas = _marked_values(sequence, {"alinea", "alineas"}, "alinea")

    # Legal shorthand commonly omits the word "inciso" (for example,
    # "CF, art. 155, II").  Capture only an immediate Roman numeral after
    # the article number(s); prose elsewhere must never become a locator.
    for index, token in enumerate(sequence):
        if token not in ARTICLE_MARKERS:
            continue
        saw_article = False
        for candidate in sequence[index + 1:index + 18]:
            if normalize_number(candidate):
                saw_article = True
                continue
            if saw_article and candidate in CONNECTORS:
                continue
            if saw_article and ROMAN.fullmatch(candidate):
                incisos.append(candidate)
            break
        break

    # The compact form "§ 3º, II" also omits the word "inciso".  Bind the
    # Roman numeral only when it immediately follows the paragraph value.
    for index, token in enumerate(sequence):
        if token not in {"par", "paragrafo", "paragrafos"}:
            continue
        saw_paragraph = False
        for candidate in sequence[index + 1:index + 8]:
            if normalize_number(candidate) or candidate == "unico":
                saw_paragraph = True
                continue
            if saw_paragraph and ROMAN.fullmatch(candidate):
                incisos.append(candidate)
            break
        break

    temporal = set()
    if any(item.startswith("revogad") or item == "revogacao" for item in sequence):
        temporal.add("revoked")
    if (any(item.startswith("historic") for item in sequence) or
            any(sequence[index:index + 2] in (["redacao", "anterior"], ["regime", "anterior"])
                for index in range(max(0, len(sequence) - 1)))):
        temporal.add("historical")
    if any(item in {"vigente", "vigencia", "atual"} for item in sequence):
        temporal.add("current")
    negated_temporal = any(
        item in {"nao", "nunca"} and any(
            candidate.startswith(("revogad", "historic", "vigent")) or candidate == "atual"
            for candidate in sequence[index + 1:index + 4])
        for index, item in enumerate(sequence))
    if negated_temporal or ("current" in temporal and len(temporal) > 1):
        temporal_status = "conflict"
    elif temporal == {"revoked", "historical"}:
        temporal_status = "revoked_historical"
    else:
        temporal_status = next(iter(temporal)) if len(temporal) == 1 else ""
    return (articles, article_relation, paragraphs, _ordered_unique(incisos), alineas,
            "caput" in sequence, temporal_status)


def locator_has_material(locator: tuple) -> bool:
    return any((locator[0], locator[2], locator[3], locator[4], locator[5], locator[6]))


def locator_structure_issue(value: str, locator: tuple) -> bool:
    if re.search(
            r"\d+\s*[ºª]?\s*[-‐‑‒–—]\s*[A-Za-z](?![A-Za-z])"
            r"(?!\s*[-‐‑‒–—]\s*\d)", value):
        return True
    sequence = tokens(value)
    if sum(item in ARTICLE_MARKERS for item in sequence) > 1:
        return True
    if sum(item in {"par", "paragrafo", "paragrafos"} for item in sequence) > 1:
        return True
    if sum(item in {"inciso", "incisos"} for item in sequence) > 1:
        return True
    has_qualifier = bool(locator[2] or locator[3] or locator[4] or locator[5])
    if len(locator[0]) > 1 and has_qualifier:
        return True
    if locator[5] and any((locator[2], locator[3], locator[4])):
        return True
    return locator[-1] == "conflict"


def locator_has_orphan_qualifier(locator: tuple) -> bool:
    return not locator[0] and any((locator[2], locator[3], locator[4], locator[5]))


def locators_conflict(left: tuple, right: tuple) -> bool:
    if left[0] and right[0] and (left[0] != right[0] or left[1] != right[1]):
        return True
    for index in (2, 3, 4):
        if left[index] and right[index] and left[index] != right[index]:
            return True
    left_specific = bool(left[2] or left[3] or left[4] or left[5])
    right_specific = bool(right[2] or right[3] or right[4] or right[5])
    if left_specific and right_specific and left[5] != right[5] and (left[5] or right[5]):
        return True
    if left[6] and right[6] and left[6] != right[6]:
        return True
    return False


def canonical_issuer(parts: list[str], marker_index: int, number_index: int) -> str:
    candidates = (parts[max(0, marker_index - 4):marker_index] +
                  parts[marker_index + 1:number_index] +
                  parts[number_index + 1:number_index + 5])
    joined = "-".join(candidates)
    if "cd-anpd" in joined:
        return "cd-anpd"
    issuers = {ISSUER_ALIASES[candidate] for candidate in candidates
               if candidate in ISSUER_ALIASES}
    return next(iter(issuers)) if len(issuers) == 1 else ""


def parse_explicit_identities(value: str) -> list[ActIdentity]:
    sequence = tokens(value)
    identities: list[ActIdentity] = []

    marker_specs = [
        (("lei", "complementar"), "lei-complementar"),
        (("decreto", "lei"), "decreto-lei"),
        (("instrucao", "normativa"), "instrucao-normativa"),
        (("emenda", "constitucional"), "emenda-constitucional"),
        (("lei",), "lei"), (("decreto",), "decreto"),
        (("resolucao",), "resolucao"), (("res",), "resolucao"),
        (("rn",), "resolucao"), (("in",), "instrucao-normativa"),
        (("circular",), "circular"), (("provimento",), "provimento"),
        (("sumula",), "sumula"), (("tema",), "tema"),
        (("resp",), "resp"), (("re",), "re"), (("are",), "are"),
        (("adi",), "adi"), (("adc",), "adc"), (("adpf",), "adpf"),
        (("lc",), "lei-complementar"), (("ec",), "emenda-constitucional"),
    ]

    for marker, kind in marker_specs:
        width = len(marker)
        for index in range(0, len(sequence) - width + 1):
            if tuple(sequence[index:index + width]) != marker:
                continue
            if marker == ("lei",) and (
                    (index > 0 and sequence[index - 1] == "decreto") or
                    (index + 1 < len(sequence) and sequence[index + 1] == "complementar")):
                continue
            if marker == ("decreto",) and index + 1 < len(sequence) and sequence[index + 1] == "lei":
                continue
            number_index = -1
            for cursor in range(index + width, min(len(sequence), index + width + 6)):
                if sequence[cursor] in ARTICLE_MARKERS:
                    break
                candidate = normalize_number(sequence[cursor])
                if candidate:
                    number_index = cursor
                    break
            if number_index < 0:
                continue
            number = normalize_number(sequence[number_index])
            year = ""
            for cursor in range(number_index + 1, min(len(sequence), number_index + 4)):
                if sequence[cursor] in ARTICLE_MARKERS:
                    break
                candidate = normalize_number(sequence[cursor])
                if candidate.isdigit() and len(candidate) == 4 and 1800 <= int(candidate) <= 2100:
                    year = candidate
                    break
            issuer = ""
            if kind in ISSUER_SENSITIVE_KINDS:
                issuer = canonical_issuer(sequence, index + width - 1, number_index)
            identities.append(ActIdentity(kind, issuer, number, year))

    for index, token in enumerate(sequence):
        if token not in {"cf", "crfb", "constituicao"}:
            continue
        nearby = sequence[index + 1:index + 5]
        if "federal" in nearby:
            nearby = [item for item in nearby if item != "federal"]
        year = next((normalize_number(item) for item in nearby
                     if (normalize_number(item) == "88" or
                         (normalize_number(item).isdigit() and
                          len(normalize_number(item)) == 4 and
                          1800 <= int(normalize_number(item)) <= 2100))), "")
        if year == "88":
            year = "1988"
        if year or token in {"cf", "crfb"}:
            constitution_year = year or "1988"
            identities.append(ActIdentity(
                "constituicao", "", constitution_year, constitution_year))

    unique = []
    for identity in identities:
        if identity not in unique:
            unique.append(identity)
    return unique


def issuer_from_host(host: str, path: str) -> str:
    direct = HOST_ISSUERS.get(host)
    if direct:
        return direct
    combined = host + path
    for prefix, issuer in HOST_ISSUERS.items():
        if "/" in prefix and combined.startswith(prefix):
            return issuer
    return ""


def normalize_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_SOURCE_RUNES:
        return ""
    if (value != value.strip() or any(ord(char) < 32 for char in value) or
            "\\" in value or re.search(r"%(?![0-9a-fA-F]{2})", value)):
        return ""
    try:
        parsed = urlsplit(value)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except (UnicodeError, ValueError):
        return ""
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        return ""
    try:
        port = parsed.port
    except ValueError:
        return ""
    if port is not None:
        return ""
    host = parsed.hostname.lower().rstrip(".")
    if len({key for key, _ in query_pairs}) != len(query_pairs):
        return ""
    try:
        path = unquote(parsed.path or "/", errors="strict")
    except UnicodeError:
        return ""
    if any(part in {".", ".."} for part in path.split("/")):
        return ""
    path = re.sub(r"/{2,}", "/", path)
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit(("https", host, path, parsed.query, ""))


def identity_from_url(value: str) -> ActIdentity | None:
    normalized = normalize_url(value)
    if not normalized:
        return None
    parsed = urlsplit(normalized)
    host = parsed.hostname or ""
    path = unquote(parsed.path).lower()
    query = parsed.query.lower()
    query_values = dict(parse_qsl(query, keep_blank_values=True, strict_parsing=True))
    issuer = issuer_from_host(host, path)

    patterns = []
    if host == "www.planalto.gov.br":
        patterns.extend([
            (r"/leis/lcp/lcp(\d+)", "lei-complementar"),
            (r"/decreto-lei/del(\d+)", "decreto-lei"),
            (r"/decreto/d(\d+)", "decreto"),
            (r"/(?:lei/)?l(\d+)(?:compilad[oa])?\.htm", "lei"),
        ])
    elif host == "www.camara.leg.br":
        patterns.append((r"/lei-(\d+)-[^/]*-(\d{4})-", "lei"))
    for pattern, kind in patterns:
        match = re.search(pattern, path)
        if not match:
            continue
        number = normalize_number(match.group(1))
        year = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
        if not year:
            parent_year = re.search(r"/(18|19|20)\d{2}/", path)
            if parent_year:
                year = parent_year.group(0).strip("/")
        return ActIdentity(kind, "", number, year)

    if host == "www.planalto.gov.br" and "/constituicao/constituicao" in path:
        return ActIdentity("constituicao", "", "1988", "1988")

    if host == "normas.leg.br":
        urn = query_values.get("urn", "")
        urn_kind = {
            "lei": "lei", "lei.complementar": "lei-complementar",
            "decreto": "decreto", "decreto.lei": "decreto-lei",
            "emenda.constitucional": "emenda-constitucional",
        }
        match = re.fullmatch(
            r"urn:lex:br:federal:([a-z.]+):(\d{4})-\d{2}-\d{2};(\d+)", urn)
        if match and match.group(1) in urn_kind:
            return ActIdentity(
                urn_kind[match.group(1)], "", normalize_number(match.group(3)),
                match.group(2))

    resolution = re.search(r"resolucao(?:-n[oa])?-(\d+)[^/]*(\d{4})", path)
    if resolution and issuer:
        return ActIdentity("resolucao", issuer, normalize_number(resolution.group(1)), resolution.group(2))

    if issuer == "stj":
        match = re.search(r"(?:^|&)sumula=(\d+)(?:&|$)", query)
        if match:
            return ActIdentity("sumula", "stj", normalize_number(match.group(1)), "")
        final_theme = query_values.get("cod_tema_final", "")
        initial_theme = query_values.get("cod_tema_inicial", "")
        if final_theme and initial_theme and final_theme != initial_theme:
            return None
        match = re.search(r"(?:^|&)cod_tema_(?:final|inicial)=(\d+)(?:&|$)", query)
        if match:
            return ActIdentity("tema", "stj", normalize_number(match.group(1)), "")
    if issuer == "stf":
        match = re.search(r"(?:^|&)numerotema=(\d+)(?:&|$)", query)
        if match:
            return ActIdentity("tema", "stf", normalize_number(match.group(1)), "")

    explicit = parse_explicit_identities(path + " " + query) if issuer else []
    if len(explicit) == 1:
        identity = explicit[0]
        if identity.kind not in ISSUER_SENSITIVE_KINDS:
            return None
        if not identity.issuer and issuer:
            return ActIdentity(identity.kind, issuer, identity.number, identity.year)
        return identity
    return None


def identities_compatible(left: ActIdentity, right: ActIdentity) -> bool:
    if left.kind != right.kind or left.number != right.number:
        return False
    if left.kind in ISSUER_SENSITIVE_KINDS:
        if left.issuer and right.issuer and left.issuer != right.issuer:
            return False
    elif left.issuer and right.issuer and left.issuer != right.issuer:
        return False
    return not (left.year and right.year and left.year != right.year)


def combine_identity(textual: ActIdentity | None, url: ActIdentity | None) -> ActIdentity | None:
    if textual and url:
        if not identities_compatible(textual, url):
            return None
        return ActIdentity(
            textual.kind,
            textual.issuer or url.issuer,
            textual.number,
            textual.year or url.year,
        )
    return textual or url


def label_from_value(value: str) -> str:
    sequence = tokens(value)
    if not sequence:
        return ""
    marker = next((index for index, item in enumerate(sequence) if item in ARTICLE_MARKERS), len(sequence))
    sequence = sequence[:marker]
    while sequence and sequence[0] in NAME_PREFIXES:
        sequence = sequence[1:]
    cleaned = [item for item in sequence
               if not normalize_number(item) and item not in {
                   "n", "no", "numero", "compilado", "compilada", "consolidado", "consolidada",
               }]
    label = " ".join(cleaned).strip()
    if not label or label in GENERIC_ALIAS_LABELS or len(cleaned) > 8:
        return ""
    return label


def source_identity(name: str, url: str) -> ActIdentity | None:
    textuals = parse_explicit_identities(name)
    if len(textuals) > 1:
        return None
    textual = textuals[0] if len(textuals) == 1 else None
    named_issuers = {ISSUER_ALIASES[item] for item in tokens(name)
                     if item in ISSUER_ALIASES}
    if textual is not None and textual.kind in ISSUER_SENSITIVE_KINDS and len(named_issuers) > 1:
        return None
    url_identity = identity_from_url(url)
    # A label can lie.  When it asserts an act, the canonical URL must encode
    # the same act identity; an unrelated official-domain page is not legal
    # provenance merely because its display name says "ADI" or "Lei".
    if textual is not None and url_identity is None:
        return None
    return combine_identity(textual, url_identity)


def build_aliases(candidates: dict[str, set[ActIdentity]]) -> dict[str, ActIdentity]:
    result = {}
    for label, identities in candidates.items():
        if not label or label in GENERIC_ALIAS_LABELS:
            continue
        coarse = {(item.kind, item.issuer, item.number) for item in identities}
        years = {item.year for item in identities if item.year}
        if len(coarse) != 1 or len(years) > 1:
            continue
        exemplar = sorted(identities)[0]
        result[label] = ActIdentity(
            exemplar.kind, exemplar.issuer, exemplar.number,
            next(iter(years)) if years else "")
    return result


def signature_from_hint_diagnostic(
        value: str, aliases: dict[str, ActIdentity]) -> tuple[Signature | None, str]:
    explicit = parse_explicit_identities(value)
    if len(explicit) > 1:
        return None, "identity_conflict_research_required"
    identity = explicit[0] if len(explicit) == 1 else None
    if identity is None:
        label = label_from_value(value)
        identity = aliases.get(label)
        if identity is not None:
            sequence = tokens(value)
            marker = next((index for index, item in enumerate(sequence)
                           if item in ARTICLE_MARKERS), len(sequence))
            numeric_prefix = {normalize_number(item) for item in sequence[:marker]
                              if normalize_number(item)}
            allowed = {identity.number}
            if identity.year:
                allowed.add(identity.year)
                allowed.add(identity.year[-2:])
            if numeric_prefix - allowed:
                return None, "identity_conflict_research_required"
    if identity is None:
        normalized_label = " ".join(tokens(value))
        if normalized_label in GENERIC_ALIAS_LABELS:
            return None, "generic_authority_research_required"
        return None, "needs_source_research_no_exact_identity"
    if identity.kind in ISSUER_SENSITIVE_KINDS and not identity.issuer:
        return None, "missing_regulatory_authority_or_year"
    if identity.kind in YEAR_REQUIRED_KINDS and not identity.year:
        return None, "missing_regulatory_authority_or_year"
    locator = extract_locator(value)
    if locator[-1] == "conflict":
        return None, "temporal_conflict_research_required"
    if locator_structure_issue(value, locator):
        return None, "compound_locator_research_required"
    return Signature(identity, *locator), ""


def signature_from_hint(value: str, aliases: dict[str, ActIdentity]) -> Signature | None:
    return signature_from_hint_diagnostic(value, aliases)[0]


def read_regular_snapshot(path: Path, maximum: int) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                before.st_size < 0 or before.st_size > maximum):
            raise ValueError(f"{path}: unsafe or oversized regular file")
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after = os.fstat(descriptor)
        identity = lambda value: (
            value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_ctime_ns)
        if len(payload) > maximum or identity(before) != identity(after):
            raise ValueError(f"{path}: file changed during bounded read")
        return payload
    finally:
        os.close(descriptor)


def require_real_directory(path: Path) -> None:
    metadata = os.lstat(path)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{path}: expected real directory, not symlink or special file")


def decode_object(raw: bytes, label: str) -> dict:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label}: duplicate JSON key {key}")
            result[key] = value
        return result

    def no_nonfinite(value):
        raise ValueError(f"{label}: non-finite JSON number {value}")

    try:
        value = json.loads(
            raw, object_pairs_hook=no_duplicates, parse_constant=no_nonfinite)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON: {exc.msg} at column {exc.colno}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label}: JSON value is not an object")
    return value


def decode_jsonl(payload: bytes, label: str):
    if not payload or not payload.endswith(b"\n") or b"\r" in payload:
        raise ValueError(f"{label}: JSONL is not canonical")
    for line_number, raw in enumerate(payload.splitlines(), 1):
        if not raw:
            raise ValueError(f"{label}:{line_number}: blank line")
        yield line_number, decode_object(raw, f"{label}:{line_number}")


class RegistryMatcher:
    def __init__(self, records: list[dict]):
        self._entries: list[tuple[str, str, str]] = []
        for record in records:
            source_id = record.get("source_id")
            domains = record.get("official_domains")
            bases = record.get("canonical_base_urls")
            if (not isinstance(source_id, str) or not source_id or
                    not isinstance(domains, list) or not isinstance(bases, list)):
                raise ValueError("source registry record lacks exact URL identity")
            domain_set = {item.lower().rstrip(".") for item in domains if isinstance(item, str)}
            for base in bases:
                normalized = normalize_url(base) if isinstance(base, str) else ""
                if not normalized:
                    continue
                parsed = urlsplit(normalized)
                if parsed.hostname not in domain_set:
                    raise ValueError(f"source registry host mismatch: {source_id}")
                self._entries.append((source_id, normalized, parsed.path or "/"))

    def match(self, value: str) -> str:
        normalized = normalize_url(value)
        if not normalized:
            return ""
        parsed = urlsplit(normalized)
        candidates = []
        for source_id, base, base_path in self._entries:
            base_parsed = urlsplit(base)
            if parsed.hostname != base_parsed.hostname:
                continue
            if parsed.path == base_path or parsed.path.startswith(base_path.rstrip("/") + "/"):
                if base_parsed.query and parsed.query != base_parsed.query:
                    continue
                candidates.append((len(base_path), source_id))
        if not candidates:
            return ""
        longest = max(length for length, _ in candidates)
        source_ids = {source_id for length, source_id in candidates if length == longest}
        return next(iter(source_ids)) if len(source_ids) == 1 else ""


def load_inputs(root: Path, shard_count: int, shard_index: int, minimum: int,
                as_of: dt.date):
    for relative in (
            "data", "data/editorial", "data/editorial/portfolio_v2",
            "data/editorial/v2_pages", "data/source-registry"):
        require_real_directory(root / relative)
    fingerprints = {
        "catalog": InputFingerprint(), "registry": InputFingerprint(),
        "portfolio": InputFingerprint(), "pages": InputFingerprint(),
    }
    catalog_path = root / "data/editorial/v2_source_hint_catalog.json"
    catalog_payload = read_regular_snapshot(catalog_path, MAX_CATALOG_BYTES)
    fingerprints["catalog"].add("data/editorial/v2_source_hint_catalog.json", catalog_payload)
    catalog = decode_object(catalog_payload, str(catalog_path))
    catalog_sources = catalog.get("source_hints")
    if not isinstance(catalog_sources, dict):
        raise ValueError("source hint catalog lacks source_hints object")

    registry_path = root / "data/source-registry/source_registry_v2.jsonl"
    registry_payload = read_regular_snapshot(registry_path, MAX_REGISTRY_BYTES)
    fingerprints["registry"].add("data/source-registry/source_registry_v2.jsonl", registry_payload)
    registry_records = [row for _, row in decode_jsonl(registry_payload, str(registry_path))]
    matcher = RegistryMatcher(registry_records)

    alias_candidates: dict[str, set[ActIdentity]] = defaultdict(set)
    preliminary_catalog = []
    valid_catalog_hints = set()
    for hint, source in sorted(catalog_sources.items()):
        if (not isinstance(hint, str) or not isinstance(source, dict) or
                not isinstance(source.get("name"), str) or
                not isinstance(source.get("url"), str) or
                not isinstance(source.get("anchor_claim"), str) or
                not source["anchor_claim"].strip()):
            raise ValueError("source hint catalog contains invalid source")
        identity = source_identity(source["name"], source["url"])
        if identity is None:
            continue
        normalized = normalize_url(source["url"])
        registry_source_id = matcher.match(normalized)
        if (not normalized or not registry_source_id or
                (identity.kind in ISSUER_SENSITIVE_KINDS and not identity.issuer) or
                (identity.kind in YEAR_REQUIRED_KINDS and not identity.year)):
            continue
        hint_identities = parse_explicit_identities(hint)
        if len(hint_identities) > 1:
            continue
        if hint_identities:
            hinted_signature = signature_from_hint(hint, {})
            if hinted_signature is None or hinted_signature.identity != identity:
                continue
        claim_identities = parse_explicit_identities(source["anchor_claim"])
        if (len(claim_identities) > 1 or
                (claim_identities and not identities_compatible(identity, claim_identities[0]))):
            continue
        hint_locator = extract_locator(hint)
        name_locator = extract_locator(source["name"])
        claim_locator = extract_locator(source["anchor_claim"])
        if (locator_structure_issue(hint, hint_locator) or
                locator_structure_issue(source["name"], name_locator) or
                locator_structure_issue(source["anchor_claim"], claim_locator) or
                locator_has_orphan_qualifier(claim_locator) or
                locators_conflict(hint_locator, name_locator) or
                locators_conflict(hint_locator, claim_locator) or
                locators_conflict(name_locator, claim_locator)):
            continue
        target_locator = hint_locator if locator_has_material(hint_locator) else name_locator
        if (locator_has_material(target_locator) and
                target_locator not in (name_locator, claim_locator)):
            continue
        preliminary_catalog.append((hint, source, identity, target_locator))
        valid_catalog_hints.add(hint)
        for label in (label_from_value(hint), label_from_value(source["name"])):
            if label:
                alias_candidates[label].add(identity)
    # Aliases are learned only from already-existing catalog entries.  Page
    # observations are evidence candidates, not an authority for inventing a
    # vocabulary or silently teaching the matcher a new alias.
    catalog_aliases = build_aliases(alias_candidates)

    hints: dict[str, HintAggregate] = {}
    seen_intent_hashes: set[bytes] = set()
    portfolio_files = sorted(glob.glob(str(root / "data/editorial/portfolio_v2/*.jsonl")))
    if len(portfolio_files) > MAX_INPUT_FILES:
        raise ValueError("too many portfolio files")
    portfolio_records = researched_records = pending_records = 0
    for filename in portfolio_files:
        path = Path(filename)
        payload = read_regular_snapshot(path, MAX_JSONL_BYTES)
        rel_path = os.path.relpath(path, root).replace(os.sep, "/")
        fingerprints["portfolio"].add(rel_path, payload)
        for line_number, row in decode_jsonl(payload, filename):
            intent = row.get("intent_id")
            source_hints = row.get("source_hints")
            needs_research = row.get("needs_source_research")
            invalid_hints = (not isinstance(source_hints, list) or not source_hints or
                             any(not isinstance(item, str) or not item or item != item.strip() or
                                 len(item) > MAX_HINT_RUNES for item in source_hints))
            intent_hash = (hashlib.sha256(intent.encode("utf-8")).digest()
                           if isinstance(intent, str) else b"")
            if (not isinstance(intent, str) or not INTENT_ID.fullmatch(intent) or
                    intent_hash in seen_intent_hashes or invalid_hints or
                    len(source_hints) != len(set(source_hints)) or
                    type(needs_research) is not bool):
                raise ValueError(f"{filename}:{line_number}: invalid portfolio source identity")
            seen_intent_hashes.add(intent_hash)
            portfolio_records += 1
            pending_records += int(needs_research)
            researched_records += int(not needs_research)
            for hint in source_hints:
                if hint in valid_catalog_hints:
                    continue
                digest = int.from_bytes(hashlib.sha256(hint.encode("utf-8")).digest()[:8], "big")
                if digest % shard_count != shard_index:
                    continue
                aggregate = hints.setdefault(hint, HintAggregate(hint))
                aggregate.add(intent, needs_research)

    required_signatures = set()
    for hint in hints:
        signature = signature_from_hint(hint, catalog_aliases)
        if signature is not None:
            required_signatures.add(signature)

    evidence: dict[Signature, dict[str, EvidenceBucket]] = defaultdict(dict)
    source_stats = Counter()
    page_files = sorted(glob.glob(str(root / "data/editorial/v2_pages/*.jsonl")))
    if len(page_files) > MAX_INPUT_FILES:
        raise ValueError("too many v2 page files")
    for filename in page_files:
        path = Path(filename)
        payload = read_regular_snapshot(path, MAX_JSONL_BYTES)
        rel_path = os.path.relpath(path, root).replace(os.sep, "/")
        fingerprints["pages"].add(rel_path, payload)
        for line_number, row in decode_jsonl(payload, filename):
            intent = row.get("intent_id")
            sources = row.get("official_sources")
            if (not isinstance(intent, str) or not INTENT_ID.fullmatch(intent) or
                    not isinstance(sources, list)):
                source_stats["invalid_page_source_shape"] += 1
                continue
            seen_page_urls = set()
            for source in sources:
                source_stats["observations"] += 1
                if not isinstance(source, dict):
                    source_stats["invalid_source"] += 1
                    continue
                name, url = source.get("name"), source.get("url")
                claim = source.get("anchor_claim")
                verified_at, http_status = source.get("verified_at"), source.get("http_status")
                if (not isinstance(name, str) or not isinstance(url, str) or
                        not isinstance(claim, str) or not claim.strip() or
                        len(claim) > MAX_SOURCE_RUNES or
                        not isinstance(verified_at, str) or not CANONICAL_DATE.fullmatch(verified_at) or
                        type(http_status) is not int or not (200 <= http_status < 300)):
                    source_stats["unverified_or_invalid"] += 1
                    continue
                try:
                    verified_date = dt.date.fromisoformat(verified_at)
                    if verified_date > as_of:
                        source_stats["future_verification"] += 1
                        continue
                    if (as_of - verified_date).days > MAX_VERIFICATION_AGE_DAYS:
                        source_stats["stale_verification"] += 1
                        continue
                except ValueError:
                    source_stats["unverified_or_invalid"] += 1
                    continue
                normalized = normalize_url(url)
                registry_source_id = matcher.match(normalized)
                if not normalized or not registry_source_id:
                    source_stats["outside_exact_registry_prefix"] += 1
                    continue
                identity = source_identity(name, normalized)
                if identity is None:
                    source_stats["identity_unresolved_or_conflicting"] += 1
                    continue
                if ((identity.kind in ISSUER_SENSITIVE_KINDS and not identity.issuer) or
                        (identity.kind in YEAR_REQUIRED_KINDS and not identity.year)):
                    source_stats["incomplete_act_identity"] += 1
                    continue
                claim_identities = parse_explicit_identities(claim)
                if (len(claim_identities) > 1 or
                        (claim_identities and
                         not identities_compatible(identity, claim_identities[0]))):
                    source_stats["anchor_identity_conflict"] += 1
                    continue
                name_locator = extract_locator(name)
                claim_locator = extract_locator(claim)
                if (locator_structure_issue(name, name_locator) or
                        locator_structure_issue(claim, claim_locator) or
                        locator_has_orphan_qualifier(claim_locator) or
                        locators_conflict(name_locator, claim_locator)):
                    source_stats["anchor_locator_conflict"] += 1
                    continue
                locator_text = name + " " + claim
                locator = extract_locator(locator_text)
                if locator[-1] == "conflict":
                    source_stats["temporal_locator_conflict"] += 1
                    continue
                source_signature = Signature(identity, *locator)
                if source_signature not in required_signatures:
                    source_stats["signature_not_required_by_shard"] += 1
                    continue
                dedupe_key = (intent, normalized, source_signature)
                if dedupe_key in seen_page_urls:
                    source_stats["duplicate_within_page"] += 1
                    continue
                seen_page_urls.add(dedupe_key)
                bucket = evidence[source_signature].get(normalized)
                if bucket is None:
                    bucket = EvidenceBucket(normalized, registry_source_id)
                    evidence[source_signature][normalized] = bucket
                bucket.add(rel_path, intent, minimum)
                source_stats["eligible"] += 1

    aliases = catalog_aliases
    catalog_targets: dict[Signature, list[CatalogTarget]] = defaultdict(list)
    for hint, source, identity, locator in preliminary_catalog:
        signature = Signature(identity, *locator)
        normalized = normalize_url(source["url"])
        registry_source_id = matcher.match(normalized)
        if not normalized or not registry_source_id:
            continue
        catalog_targets[signature].append(CatalogTarget(
            hint, signature, source["name"], normalized, registry_source_id))

    counts = {
        "portfolio_records": portfolio_records,
        "researched_records": researched_records,
        "research_pending_records": pending_records,
        "catalog_hints": len(catalog_sources),
        "valid_exact_catalog_hints": len(valid_catalog_hints),
        "unresolved_hints_in_shard": len(hints),
        "unresolved_occurrences_in_shard": sum(item.occurrences for item in hints.values()),
    }
    return hints, aliases, catalog_targets, evidence, matcher, fingerprints, counts, source_stats


def matching_evidence(signature: Signature, evidence, minimum: int) -> list[dict]:
    result = []
    for url, bucket in evidence.get(signature, {}).items():
        result.append({
            "url": url,
            "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "registry_source_id": bucket.registry_source_id,
            "observations": bucket.observations,
            "distinct_intents_lower_bound": bucket.distinct_intents_lower_bound,
            "distinct_files_lower_bound": bucket.distinct_files_lower_bound,
            "page_observation_threshold_met": (
                bucket.distinct_intents_lower_bound >= minimum and
                bucket.distinct_files_lower_bound >= minimum),
            "independent_live_evidence_runs": 0,
            "independent_provenance_verified": False,
            "samples": sorted(bucket.samples, key=lambda item: (item["file"], item["intent_id"])),
        })
    return sorted(result, key=lambda item: (
        not item["page_observation_threshold_met"],
        -item["distinct_intents_lower_bound"], item["url"]))


def compatible_catalog_targets(signature: Signature, targets) -> list[CatalogTarget]:
    return sorted(targets.get(signature, []), key=lambda item: item.hint)


def make_plan_record(aggregate: HintAggregate, signature: Signature | None,
                     targets, evidence, minimum: int,
                     unresolved_status: str = "needs_source_research_no_exact_identity",
                     evidence_cache: dict[Signature, list[dict]] | None = None) -> dict:
    record = {
        "source_hint": aggregate.hint,
        "source_hint_sha256": hashlib.sha256(aggregate.hint.encode("utf-8")).hexdigest(),
        "occurrences": aggregate.occurrences,
        "researched_occurrences": aggregate.researched_occurrences,
        "pending_occurrences": aggregate.pending_occurrences,
        "sample_intents": sorted(aggregate.sample_intents),
        "source_signature": signature.key if signature else "",
        "resolution_status": unresolved_status,
        "resolution_applied": False,
        "needs_source_research_required_until_applied": True,
        "candidate_official_sources": [],
        "candidate_catalog_hint": "",
        "next_action": "set needs_source_research=true and research an exact official act/source",
        "approval": False,
        "publication_allowed": False,
        "render_allowed": False,
        "sitemap_allowed": False,
        "index_policy": "noindex",
        "public_path": "",
    }
    if signature is None:
        return record

    if evidence_cache is None:
        candidates = matching_evidence(signature, evidence, minimum)
    elif signature in evidence_cache:
        candidates = evidence_cache[signature]
    else:
        candidates = matching_evidence(signature, evidence, minimum)
        evidence_cache[signature] = candidates
    catalog = compatible_catalog_targets(signature, targets)
    record["candidate_official_sources"] = candidates[:8]
    if len(catalog) > 1:
        record["resolution_status"] = "blocked_ambiguous_existing_catalog_alias"
        record["candidate_catalog_hints"] = [item.hint for item in catalog]
        record["next_action"] = "keep needs_source_research=true; catalog identities collide"
        return record
    if len(catalog) == 1:
        target = catalog[0]
        target_evidence = next((item for item in candidates if item["url"] == target.url), None)
        record["candidate_catalog_hint"] = target.hint
        record["candidate_catalog_url"] = target.url
        record["candidate_catalog_registry_source_id"] = target.registry_source_id
        if target_evidence and target_evidence["page_observation_threshold_met"]:
            record["resolution_status"] = "existing_catalog_alias_review_candidate_exact_observation_only"
            record["next_action"] = (
                "obtain independent live provenance and juridical review before any authenticated CAS rewrite")
        else:
            record["resolution_status"] = "existing_catalog_alias_needs_independent_provenance"
            record["next_action"] = (
                "keep needs_source_research=true until the exact catalog URL has independent live provenance")
        return record

    repeated = [item for item in candidates if item["page_observation_threshold_met"]]
    if len(repeated) == 1:
        record["resolution_status"] = "official_source_cluster_research_plan_observation_only"
        record["next_action"] = (
            "keep needs_source_research=true; obtain independent provenance and review the exact source")
    elif len(repeated) > 1:
        record["resolution_status"] = "multiple_official_source_clusters_require_juridical_choice"
        record["next_action"] = (
            "keep needs_source_research=true; choose claim-specific official source without automatic aliasing")
    else:
        record["resolution_status"] = "needs_source_research_insufficient_observation"
        record["next_action"] = "keep needs_source_research=true and collect exact independent provenance"
    return record


def build_plan(root: Path, *, shard_count: int = 1, shard_index: int = 0,
               minimum_page_observations: int = 2, max_records: int = 0,
               as_of: dt.date | None = None) -> dict:
    if as_of is None:
        as_of = dt.date.today()
    if not isinstance(as_of, dt.date):
        raise ValueError("as_of must be a date")
    if shard_count < 1 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError("invalid deterministic shard")
    if minimum_page_observations < 2 or minimum_page_observations > 5:
        raise ValueError("minimum_page_observations must be between 2 and 5")
    if max_records < 0:
        raise ValueError("max_records must be nonnegative")

    (hints, aliases, targets, evidence, _matcher, fingerprints,
     counts, source_stats) = load_inputs(
         root, shard_count, shard_index, minimum_page_observations, as_of)
    records = []
    status_counts = Counter()
    evidence_cache: dict[Signature, list[dict]] = {}
    for hint, aggregate in sorted(hints.items()):
        signature, unresolved_status = signature_from_hint_diagnostic(hint, aliases)
        record = make_plan_record(
            aggregate, signature, targets, evidence, minimum_page_observations,
            unresolved_status or "needs_source_research_no_exact_identity",
            evidence_cache)
        status_counts[record["resolution_status"]] += 1
        records.append(record)
    total = len(records)
    if max_records:
        records = records[:max_records]
    return {
        "schema_version": 1,
        "record_status": "v2_source_hint_resolution_plan_blocked_no_publication",
        "planner_policy": "exact_act_provision_observation_plan_no_independence_claim_v2",
        "snapshot_consistency": "bounded_per_file_snapshot_not_publication_transaction",
        "shard_count": shard_count,
        "shard_index": shard_index,
        "minimum_page_observations": minimum_page_observations,
        "evidence_as_of": as_of.isoformat(),
        "maximum_verification_age_days": MAX_VERIFICATION_AGE_DAYS,
        "counts": counts,
        "source_observation_counts": dict(sorted(source_stats.items())),
        "resolution_status_counts": dict(sorted(status_counts.items())),
        "learned_unambiguous_aliases": len(aliases),
        "records_total": total,
        "records_returned": len(records),
        "input_fingerprints": {name: value.report() for name, value in fingerprints.items()},
        "scale_path": {
            "complexity": (
                "O(input + hints*log(hints) + matched_urls*log(matched_urls)); exact Signature index, no HxE scan"),
            "bounded_samples_per_source": MAX_SAMPLES,
            "10k_100k": "single read-only scan with exact signature filtering and deterministic output",
            "1m_current_limit": (
                "hint sharding bounds candidate memory but each shard still rescans immutable inputs"),
            "1m_required_integration": (
                "content-addressed compact source-evidence index plus merge that pins fingerprints and as_of"),
        },
        "approval": False,
        "publication_allowed": False,
        "render_allowed": False,
        "sitemap_allowed": False,
        "index_policy": "noindex",
        "public_path": "",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--minimum-page-observations", type=int, default=2)
    parser.add_argument("--max-records", type=int, default=0)
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    args = parser.parse_args()
    try:
        as_of = dt.date.fromisoformat(args.as_of)
        report = build_plan(
            Path(args.root).resolve(), shard_count=args.shard_count,
            shard_index=args.shard_index,
            minimum_page_observations=args.minimum_page_observations,
            max_records=args.max_records, as_of=as_of)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"plan-v2-source-hint-resolution: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
