#!/usr/bin/env python3
"""generate-v2-writing-briefs — estágio de BRIEF determinístico da fábrica v2.

Para cada intent do portfólio ainda SEM página em data/editorial/v2_pages/,
emite um brief com base legal resolvida, dispositivo, URL oficial JÁ
verificada, status de vigência e o trecho legal pertinente lido do corpus
local (data/source-snapshots/). ZERO rede, ZERO LLM: tudo vem de dado já
coletado e verificado em disco. O objetivo é tirar a pesquisa de fonte do
caminho crítico da redação (o redator deixa de fazer curl por página).

CONTRATO INEGOCIÁVEL (gravado em cada registro emitido):
  * O trecho legal do brief é INSUMO DE PROVENIÊNCIA E CONFERÊNCIA para o
    redator. NUNCA é corpo da página. Copiar, espelhar ou parafrasear
    mecanicamente texto oficial na página viola o contrato editorial
    ("fonte oficial é referência/proveniência, nunca corpo").
  * Vigência não confirmada (vigencia_status != "vigente"), revogação ou
    verificação velha são declaradas no brief — o redator não afirma
    vigência categórica com base em dado não confirmado.
  * Hint sem resolução determinística permanece precisando de pesquisa
    (needs_source_research residual); é PROIBIDO inventar fonte/URL.

Saída (dentro do repo, camada editorial bloqueada, regenerável):
  data/editorial/v2_writing_briefs/<area>.jsonl   (1 brief por intent)
  data/editorial/v2_writing_briefs/coverage_report.json (censo da onda)

Uso:
  tools/generate-v2-writing-briefs [--dry-run] [--areas a,b] \
      [--as-of YYYY-MM-DD] [--stale-after-days 45] [--excerpt-cap 8000]
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import unicodedata

BRIEF_VERSION = 1
DEFAULT_OUT_REL = "data/editorial/v2_writing_briefs"
SNAPSHOTS_REL = "data/source-snapshots"
MANIFEST_REL = f"{SNAPSHOTS_REL}/manifest.jsonl"
CATALOG_REL = "data/editorial/v2_source_hint_catalog.json"
PORTFOLIO_GLOB_RE = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl$")

CONTRATO = {
    "trecho_legal": (
        "O campo trecho_legal_conferencia é insumo de PROVENIÊNCIA e "
        "CONFERÊNCIA do redator. É PROIBIDO copiar, espelhar ou parafrasear "
        "mecanicamente esse texto no corpo da página: fonte oficial é "
        "referência, nunca corpo (contrato editorial do repo)."),
    "redacao": (
        "Texto 100% autoral em PT-BR acentuado, partindo do fato específico "
        "do intent. É PROIBIDO inventar lei, artigo, súmula, prazo, valor ou "
        "decisão que não esteja na fonte citada."),
    "vigencia": (
        "Se vigencia_confirmada=false, stale_verification=true ou houver "
        "alerta_vigencia, o redator NÃO afirma vigência categórica do "
        "dispositivo sem conferir a fonte oficial citada."),
}

USO_DO_TRECHO = (
    "conferencia_e_proveniencia_apenas__nunca_corpo_da_pagina")

# ---------------------------------------------------------------------------
# Normalização de hints


def _strip_accents(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn")


def _norm_text(hint: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(hint).lower().strip())


# alias → (tipo_urn, numero). Cobre apelidos consagrados usados nos hints do
# portfólio; normas fora do corpus ficam aqui de propósito para que o censo
# de lacunas identifique a norma exata que falta coletar.
ALIASES: dict[str, tuple[str, str]] = {
    "cc": ("lei", "10406"),
    "codigo-civil": ("lei", "10406"),
    "codigo civil": ("lei", "10406"),
    "cdc": ("lei", "8078"),
    "codigo-de-defesa-do-consumidor": ("lei", "8078"),
    "codigo de defesa do consumidor": ("lei", "8078"),
    "cpc": ("lei", "13105"),
    "codigo-de-processo-civil": ("lei", "13105"),
    "codigo de processo civil": ("lei", "13105"),
    "clt": ("decreto.lei", "5452"),
    "lgpd": ("lei", "13709"),
    "marco-civil-da-internet": ("lei", "12965"),
    "marco-civil": ("lei", "12965"),
    "marco civil": ("lei", "12965"),
    "mci": ("lei", "12965"),
    "estatuto-do-idoso": ("lei", "10741"),
    "estatuto do idoso": ("lei", "10741"),
    "estatuto-da-pessoa-idosa": ("lei", "10741"),
    "estatuto da pessoa idosa": ("lei", "10741"),
    "lei-maria-da-penha": ("lei", "11340"),
    "lei maria da penha": ("lei", "11340"),
    "estatuto-da-cidade": ("lei", "10257"),
    "estatuto da cidade": ("lei", "10257"),
    "lbi": ("lei", "13146"),
    "estatuto-da-pessoa-com-deficiencia": ("lei", "13146"),
    "loas": ("lei", "8742"),
    "lei-de-locacoes": ("lei", "8245"),
    "lei-do-inquilinato": ("lei", "8245"),
    "lei do inquilinato": ("lei", "8245"),
    # normalizáveis porém FORA do corpus hoje (alimentam o censo de lacuna):
    "cf": ("constituicao", "1988"),
    "cf88": ("constituicao", "1988"),
    "constituicao": ("constituicao", "1988"),
    "constituicao-federal": ("constituicao", "1988"),
    "cp": ("decreto.lei", "2848"),
    "codigo-penal": ("decreto.lei", "2848"),
    "codigo penal": ("decreto.lei", "2848"),
    "cpp": ("decreto.lei", "3689"),
    "codigo-de-processo-penal": ("decreto.lei", "3689"),
    "ctn": ("lei", "5172"),
    "ctb": ("lei", "9503"),
    "codigo-de-transito": ("lei", "9503"),
    "codigo-de-transito-brasileiro": ("lei", "9503"),
    "lep": ("lei", "7210"),
    "lpi": ("lei", "9279"),
    "lrp": ("lei", "6015"),
    "eca": ("lei", "8069"),
}

# Números que podem cair em fallback de tipo sem ano (apelido consagrado e
# sem colisão real no corpus). Fora desta lista, fallback de tipo exige que
# o ano do hint confirme a norma do corpus — proteção contra colisão
# (ex.: lei 11.034/2004 existe e NÃO é o decreto 11.034/2022).
SAFE_TYPE_FALLBACK_NUMBERS = {"5452"}

NUM_YEAR = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d{3,5})\s*/\s*(\d{4})")
SLUG_NUM_YEAR = re.compile(r"(?<![0-9])(\d{3,5})-(\d{4})(?![0-9])")
ART_RE = re.compile(
    r"art(?:igo)?s?[-_. ]*(\d+)(?:[ºo°])?(?:[-. ]?([a-z])(?![a-z0-9]))?",
    re.IGNORECASE)
SUMULA_RE = re.compile(
    r"sumula[-_ ]*(?:vinculante[-_ ]*)?(?:(stf|stj|tst)[-_ ]*)?(\d+)"
    r"|(?:(stf|stj|tst)[-_ ]*sumula[-_ ]*(\d+))"
    r"|sumula\s+(\d+)\s+(?:do\s+)?(stf|stj|tst)", re.IGNORECASE)
VINCULANTE_RE = re.compile(r"vinculante", re.IGNORECASE)
KIND_WORDS = [
    ("lei complementar", "lei.complementar"),
    ("lc", "lei.complementar"),
    ("decreto-lei", "decreto.lei"),
    ("decreto lei", "decreto.lei"),
    ("dl", "decreto.lei"),
    ("decreto", "decreto"),
    ("lei", "lei"),
    ("emenda constitucional", "emenda.constitucional"),
    ("ec", "emenda.constitucional"),
    ("medida provisoria", "medida.provisoria"),
    ("mp", "medida.provisoria"),
]

# Atos de agência/regulador/conselho e jurisprudência: um par NNN/AAAA nesses
# contextos NUNCA vira "lei NNN/AAAA" por default (ren-aneel-1000-2021 não é
# a Lei 1.000/2021). O mesmo padrão alimenta o censo de conectores.
AGENCY_TOKEN_RE = re.compile(
    r"(?:^|[ -])(anac|ans|susep|bcb|bacen|cvm|anatel|aneel|anvisa|antt|"
    r"ancine|cfm|cff|crm|cnj|cnmp|inss|inpi|receita|coaf|previc|cmn|cnsp|"
    r"rdc|rbac|rn|ren|in|res|resolucao|circular|portaria|prov|provimento|"
    r"deliberacao|instrucao|comunicado|carta-circular|"
    r"sumula-administrativa)(?:$|[ .-])")
JURIS_TOKEN_RE = re.compile(
    r"(?:^|[ -])(resp|aresp|eresp|tema|adi|adc|adpf|re|rext|juris|acordao|"
    r"repetitivo)(?:$|[ -])")

NICKNAMES = {
    ("lei", "8078"): "CDC",
    ("lei", "10406"): "Código Civil",
    ("lei", "13105"): "CPC",
    ("decreto.lei", "5452"): "CLT",
    ("lei", "13709"): "LGPD",
    ("lei", "12965"): "Marco Civil da Internet",
    ("lei", "10741"): "Estatuto da Pessoa Idosa",
    ("lei", "11340"): "Lei Maria da Penha",
    ("lei", "13146"): "LBI",
    ("lei", "8742"): "LOAS",
    ("lei", "8245"): "Lei do Inquilinato",
    ("lei", "9099"): "Lei dos Juizados Especiais",
    ("lei", "11101"): "Lei de Falências",
}


def parse_hint(hint: str) -> dict | None:
    """Extrai identidade normativa determinística de um hint (slug ou texto
    livre). Retorna None quando nem norma nem súmula são reconhecíveis."""
    text = _norm_text(hint)
    out = {
        "kind": None, "numero": None, "ano": None,
        "artigo": None, "sufixo": None,
        "sumula_court": None, "sumula_num": None, "vinculante": False,
    }

    m = SUMULA_RE.search(text)
    if m:
        court = (m.group(1) or m.group(3) or m.group(6) or "").lower()
        if not court:
            # formato dominante no portfólio é sufixado (sumula-479-stj):
            # procurar o tribunal em qualquer posição do hint.
            trailing = re.search(r"(?:^|[-_ ])(stf|stj|tst)(?:$|[-_ ])", text)
            if trailing:
                court = trailing.group(1)
        out["sumula_court"] = court
        out["sumula_num"] = m.group(2) or m.group(4) or m.group(5)
        out["vinculante"] = bool(VINCULANTE_RE.search(text))
        return out

    art_match = ART_RE.search(text)
    if art_match:
        out["artigo"] = art_match.group(1)
        out["sufixo"] = art_match.group(2)

    for alias, (kind, numero) in sorted(
            ALIASES.items(), key=lambda kv: -len(kv[0])):
        if text == alias or text.startswith((alias + "-", alias + " ")):
            out["kind"], out["numero"] = kind, numero
            break

    m = NUM_YEAR.search(text) or SLUG_NUM_YEAR.search(text)
    if m:
        numero, ano = m.group(1).replace(".", ""), m.group(2)
        if out["numero"] is None:
            kind = None
            for word, k in KIND_WORDS:
                if re.search(r"(?:^|[ -])" + re.escape(word) + r"(?:$|[ .-])",
                             text):
                    kind = k
                    break
            if kind is None and (AGENCY_TOKEN_RE.search(text) or
                                 JURIS_TOKEN_RE.search(text)):
                # ato de agência/jurisprudência numerado: não é lei federal;
                # segue sem identidade de norma (rota de lacuna/conector).
                return None
            out["numero"], out["kind"] = numero, kind or "lei"
            out["ano"] = ano
        elif numero == out["numero"]:
            # alias e número/ano concordam (ex.: cdc-lei-8078-1990):
            # o ano confirma a norma do alias.
            out["ano"] = ano
    elif out["numero"] is None:
        m2 = re.search(r"(?:^|-)(lei|lc|decreto|dl)-(\d{3,5})(?:-|$)", text)
        if m2:
            prefix = m2.group(1)
            out["numero"] = m2.group(2)
            out["kind"] = {
                "lei": "lei", "lc": "lei.complementar",
                "decreto": "decreto", "dl": "decreto.lei"}[prefix]

    if out["numero"] is None and out["sumula_num"] is None:
        return None
    return out


# ---------------------------------------------------------------------------
# Índice do corpus local


URN_NORM_RE = re.compile(
    r"^urn:lex:br:federal:([a-z.]+):(\d{4})-\d{2}-\d{2};(\d+)$")
URN_SUMULA_STF_RE = re.compile(
    r"^urn:lex:br:supremo\.tribunal\.federal:sumula:\d{4};(\d+)$")


def load_corpus_index(root: pathlib.Path):
    """Indexa o manifesto: (tipo, numero) → norma; (urn, dispositivo) →
    registro mais recente (maior version_seq)."""
    by_norm: dict[tuple[str, str], dict] = {}
    by_series: dict[tuple[str, str], dict] = {}
    manifest = root / MANIFEST_REL
    with manifest.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            urn = rec["urn_lex"]
            m = URN_NORM_RE.match(urn)
            if m:
                key = (m.group(1), m.group(3))
                by_norm.setdefault(key, {"urn": urn, "ano": m.group(2)})
            else:
                m2 = URN_SUMULA_STF_RE.match(urn)
                if m2:
                    by_norm.setdefault(("sumula-stf", m2.group(1)),
                                       {"urn": urn, "ano": ""})
            series_key = (urn, rec.get("dispositivo", ""))
            prev = by_series.get(series_key)
            if prev is None or rec.get("version_seq", 0) >= prev.get(
                    "version_seq", 0):
                by_series[series_key] = rec
    return by_norm, by_series


def read_blob(root: pathlib.Path, rec: dict) -> str | None:
    """Lê e VERIFICA (sha256) o blob de um registro. Suporta blob solto e
    pack (packs/aa/<sha>.pack#offset:length). Retorna None em corrupção —
    nunca entrega texto que não confere com o hash do manifesto."""
    ref = rec.get("blob_ref", "")
    snap = root / SNAPSHOTS_REL
    pack = re.match(
        r"^packs/([0-9a-f]{2})/([0-9a-f]{64})\.pack#(\d+):(\d+)$", ref)
    try:
        if pack:
            if pack.group(1) != pack.group(2)[:2]:
                return None
            path = snap / "packs" / pack.group(1) / (pack.group(2) + ".pack")
            offset, length = int(pack.group(3)), int(pack.group(4))
            with path.open("rb") as handle:
                handle.seek(offset)
                payload = handle.read(length)
                if len(payload) != length:
                    return None
        elif ref.startswith("blobs/"):
            payload = (snap / ref).read_bytes()
        else:
            return None
    except OSError:
        return None
    if hashlib.sha256(payload).hexdigest() != rec.get("content_sha256"):
        return None
    try:
        return payload.decode(rec.get("encoding") or "utf-8")
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------------------
# Resolução hint → corpus/catálogo


def resolve_norm(parsed: dict, by_norm: dict, by_series: dict):
    """→ (status, urn, dispositivo). status ∈ corpus_article | corpus_norm |
    corpus_norm_article_missing | off_corpus."""
    if parsed["sumula_num"] is not None:
        # só casa no corpus com tribunal EXPLÍCITO stf e sem vinculante:
        # número puro jamais é atribuído a um tribunal por palpite.
        if parsed["sumula_court"] == "stf" and not parsed["vinculante"]:
            hit = by_norm.get(("sumula-stf", parsed["sumula_num"]))
            if hit:
                return "corpus_article", hit["urn"], ""
        return "off_corpus", None, None

    kind, numero, ano = parsed["kind"], parsed["numero"], parsed["ano"]
    hit = by_norm.get((kind or "lei", numero))
    if hit is None:
        for fallback_kind in ("decreto.lei", "lei.complementar", "decreto"):
            candidate = by_norm.get((fallback_kind, numero))
            if candidate is None:
                continue
            # fallback de tipo só com confirmação: ou o ano do hint bate com
            # o ano da norma no corpus, ou o número está na lista segura.
            if (ano and candidate["ano"] == ano) or \
                    numero in SAFE_TYPE_FALLBACK_NUMBERS:
                hit = candidate
                break
    if hit is None:
        return "off_corpus", None, None
    if ano and hit["ano"] != ano:
        # hint nomeia outra norma homônima em número: não casar errado.
        return "off_corpus", None, None
    urn = hit["urn"]
    if parsed["artigo"]:
        candidates = []
        if parsed["sufixo"]:
            candidates.append(
                f"art_{parsed['artigo']}-{parsed['sufixo'].upper()}")
        candidates.append(f"art_{parsed['artigo']}")
        for cand in candidates:
            if (urn, cand) in by_series:
                return "corpus_article", urn, cand
        return "corpus_norm_article_missing", urn, ""
    return "corpus_norm", urn, ""


TIPO_DISPLAY = {
    "lei": "Lei nº",
    "decreto.lei": "Decreto-Lei nº",
    "lei.complementar": "Lei Complementar nº",
    "decreto": "Decreto nº",
}


def display_name(urn: str, dispositivo: str) -> str:
    m = URN_NORM_RE.match(urn)
    if m:
        tipo, ano, numero = m.group(1), m.group(2)[:4], m.group(3)
        numero_fmt = f"{int(numero):,}".replace(",", ".")
        base = f"{TIPO_DISPLAY.get(tipo, tipo)} {numero_fmt}/{ano}"
        nick = NICKNAMES.get((tipo, numero))
        if nick:
            base += f" ({nick})"
        if dispositivo.startswith("art_"):
            art = dispositivo[len("art_"):]
            main = re.match(r"^(\d+)(.*)$", art)
            if main:
                number_part, suffix = main.group(1), main.group(2)
                ordinal = "º" if int(number_part) < 10 else ""
                suffix = suffix.replace("_", " ")
                base += f", art. {number_part}{ordinal}{suffix}"
        return base
    m2 = URN_SUMULA_STF_RE.match(urn)
    if m2:
        return f"Súmula nº {m2.group(1)} do STF"
    return urn


def classify_connector(hint: str, parsed: dict | None) -> str:
    text = _norm_text(hint)
    if parsed and parsed["sumula_num"] is not None:
        court = parsed["sumula_court"]
        if parsed["vinculante"]:
            return "sumula_vinculante_stf"
        if court == "stj":
            return "sumula_stj"
        if court == "tst":
            return "sumula_tst"
        if court == "stf":
            return "sumula_stf_fora_do_corpus"
        return "sumula_tribunal_indefinido"
    if parsed and parsed["numero"] is not None:
        if parsed["kind"] == "constituicao":
            return "constituicao_federal"
        if parsed["kind"] == "emenda.constitucional":
            return "emenda_constitucional"
        if parsed["kind"] == "medida.provisoria":
            return "medida_provisoria"
        return "legislacao_federal_fora_do_corpus"
    if JURIS_TOKEN_RE.search(text) or "jurisprudencia" in text:
        return "jurisprudencia_tribunal"
    if AGENCY_TOKEN_RE.search(text):
        return "norma_de_agencia_ou_regulador"
    if "gov-br" in text or "gov.br" in text or text.startswith("gov "):
        return "orientacao_oficial_gov_br"
    return "nao_classificado"


# ---------------------------------------------------------------------------
# Pipeline principal


def load_done_intents(root: pathlib.Path) -> set[str]:
    done: set[str] = set()
    pages_dir = root / "data/editorial/v2_pages"
    for path in sorted(pages_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                intent_id = rec.get("intent_id") or rec.get("id")
                if isinstance(intent_id, str) and intent_id:
                    done.add(intent_id)
    return done


def load_missing_intents(root: pathlib.Path, done: set[str],
                         areas_filter: set[str] | None):
    missing = []
    seen: set[str] = set()
    portfolio_dir = root / "data/editorial/portfolio_v2"
    for path in sorted(portfolio_dir.glob("*.jsonl")):
        if not PORTFOLIO_GLOB_RE.fullmatch(path.name):
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                intent_id = rec["intent_id"]
                if intent_id in done or intent_id in seen:
                    continue
                area = rec.get("practice_area", "")
                if areas_filter and area not in areas_filter:
                    continue
                seen.add(intent_id)
                rec["_portfolio_file"] = path.name
                missing.append(rec)
    return missing


def build_citation_map(catalog_hints: dict):
    """(tipo, numero) → citação curada do catálogo (preferindo planalto).
    Reutiliza dado curado existente — nunca fabrica URL."""
    citation: dict[tuple[str, str], dict] = {}
    for hint, entry in sorted(catalog_hints.items()):
        parsed = parse_hint(hint)
        if not parsed or parsed["numero"] is None or parsed["artigo"]:
            continue
        key = (parsed["kind"] or "lei", parsed["numero"])
        url = entry.get("url", "")
        current = citation.get(key)
        is_planalto = "planalto.gov.br" in url
        if current is None or (is_planalto and
                               "planalto.gov.br" not in current["url"]):
            citation[key] = {"url": url, "name": entry.get("name", "")}
    return citation


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=DEFAULT_OUT_REL)
    parser.add_argument("--areas", default="",
                        help="filtro: lista de practice_area separada por vírgula")
    parser.add_argument("--as-of", default=None,
                        help="data de referência YYYY-MM-DD (default: hoje UTC)")
    parser.add_argument("--stale-after-days", type=int, default=45)
    parser.add_argument("--excerpt-cap", type=int, default=8000)
    parser.add_argument("--dry-run", action="store_true",
                        help="só o censo; não escreve briefs")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    as_of = (datetime.date.fromisoformat(args.as_of) if args.as_of
             else datetime.datetime.now(datetime.timezone.utc).date())
    areas_filter = ({a.strip() for a in args.areas.split(",") if a.strip()}
                    or None)

    catalog_doc = json.loads((root / CATALOG_REL).read_text(encoding="utf-8"))
    catalog_hints = catalog_doc.get("source_hints", {})
    if not isinstance(catalog_hints, dict):
        raise SystemExit("catálogo de hints não canônico")
    citation_map = build_citation_map(catalog_hints)

    by_norm, by_series = load_corpus_index(root)
    done = load_done_intents(root)
    missing = load_missing_intents(root, done, areas_filter)

    briefs_by_area: dict[str, list[dict]] = collections.defaultdict(list)
    intent_class = collections.Counter()
    area_class: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    hint_class = collections.Counter()
    connector_gap = collections.Counter()
    off_corpus_norms = collections.Counter()
    excerpt_integrity_failures = []
    hint_cache: dict[str, dict] = {}

    for rec in missing:
        area = rec.get("practice_area", "desconhecida")
        sources = []
        unresolved = []
        statuses = []
        for hint in rec.get("source_hints", []):
            if hint in hint_cache:
                entry = hint_cache[hint]
            else:
                entry = build_source_entry(
                    hint, root, by_norm, by_series, catalog_hints,
                    citation_map, as_of, args.stale_after_days,
                    args.excerpt_cap, excerpt_integrity_failures)
                hint_cache[hint] = entry
            statuses.append(entry["resolution"])
            hint_class[entry["resolution"]] += 1
            if entry["resolution"] == "unresolved":
                unresolved.append(entry["unresolved"])
                connector_gap[entry["unresolved"]["connector_needed"]] += 1
                norma = entry["unresolved"].get("norma")
                if norma:
                    off_corpus_norms[norma] += 1
            else:
                sources.append(entry["source"])

        corpus_like = {"corpus_article", "corpus_norm",
                       "corpus_norm_article_missing"}
        if not statuses:
            coverage = "sem_hints"
        elif all(s in corpus_like for s in statuses):
            coverage = "full_corpus"
        elif any(s in corpus_like for s in statuses):
            coverage = "partial_corpus"
        elif any(s == "catalog" for s in statuses):
            coverage = "catalog_only"
        else:
            coverage = "none"
        intent_class[coverage] += 1
        area_class[area][coverage] += 1

        brief = {
            "brief_version": BRIEF_VERSION,
            "generator": "tools/generate-v2-writing-briefs",
            "as_of": as_of.isoformat(),
            "intent_id": rec["intent_id"],
            "practice_area": area,
            "family": rec.get("family", ""),
            "page_type": rec.get("page_type", ""),
            "lane": rec.get("lane", ""),
            "portfolio_file": rec["_portfolio_file"],
            "working_title": rec.get("working_title", ""),
            "long_tail_query": rec.get("long_tail_query", ""),
            "reader_problem": rec.get("reader_problem", ""),
            "distinct_because": rec.get("distinct_because", ""),
            "coverage": coverage,
            "sources": sources,
            "unresolved_hints": unresolved,
            "needs_source_research": bool(unresolved),
            "contrato": CONTRATO,
        }
        briefs_by_area[area].append(brief)

    # ------------------------------------------------------------------ IO
    out_dir = root / args.out
    written = []
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        for area in sorted(briefs_by_area):
            rows = sorted(briefs_by_area[area],
                          key=lambda b: b["intent_id"])
            payload = "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in rows).encode("utf-8")
            path = out_dir / f"{area}.jsonl"
            if path.exists() and path.read_bytes() == payload:
                continue
            tmp = out_dir / f".{area}.jsonl.tmp-{os.getpid()}"
            tmp.write_bytes(payload)
            os.replace(tmp, path)
            written.append(path.name)

    report = {
        "generator": "tools/generate-v2-writing-briefs",
        "brief_version": BRIEF_VERSION,
        "as_of": as_of.isoformat(),
        "params": {
            "stale_after_days": args.stale_after_days,
            "excerpt_cap": args.excerpt_cap,
            "areas_filter": sorted(areas_filter) if areas_filter else [],
        },
        "inputs": {
            "portfolio_intents_missing": len(missing),
            "v2_pages_intents": len(done),
            "manifest_sha256": sha256_file(root / MANIFEST_REL),
            "catalog_sha256": sha256_file(root / CATALOG_REL),
        },
        "intent_coverage": dict(sorted(intent_class.items())),
        "hint_resolution_refs": dict(sorted(hint_class.items())),
        "by_area": {
            area: dict(sorted(counter.items()))
            for area, counter in sorted(area_class.items())},
        "connector_gap_refs": dict(connector_gap.most_common()),
        "off_corpus_norm_refs": dict(off_corpus_norms.most_common(40)),
        "excerpt_integrity_failures": excerpt_integrity_failures,
    }
    if not args.dry_run:
        report_path = out_dir / "coverage_report.json"
        payload = (json.dumps(report, ensure_ascii=False, sort_keys=True,
                              indent=1) + "\n").encode("utf-8")
        if not (report_path.exists() and
                report_path.read_bytes() == payload):
            tmp = out_dir / f".coverage_report.json.tmp-{os.getpid()}"
            tmp.write_bytes(payload)
            os.replace(tmp, report_path)
            written.append(report_path.name)

    total = sum(intent_class.values())
    print(f"generate-v2-writing-briefs: intents_faltantes={total} "
          f"cobertura={json.dumps(dict(sorted(intent_class.items())), ensure_ascii=False)}")
    print(f"hints (refs): "
          f"{json.dumps(dict(sorted(hint_class.items())), ensure_ascii=False)}")
    if excerpt_integrity_failures:
        print(f"ALERTA: {len(excerpt_integrity_failures)} blob(s) com falha "
              f"de integridade sha256 — trecho omitido, ver coverage_report",
              file=sys.stderr)
    if args.dry_run:
        print("dry-run: nada escrito")
    else:
        print(f"escritos: {written if written else 'nenhum (byte-estável)'} "
              f"em {args.out}")
    return 0


def build_source_entry(hint, root, by_norm, by_series, catalog_hints,
                       citation_map, as_of, stale_after_days, excerpt_cap,
                       integrity_failures):
    """Resolve um hint em fonte verificada (corpus/catálogo) ou lacuna."""
    parsed = parse_hint(hint)
    status, urn, dispositivo = ("off_corpus", None, None)
    if parsed is not None:
        status, urn, dispositivo = resolve_norm(parsed, by_norm, by_series)

    if status != "off_corpus":
        rec = by_series.get((urn, dispositivo))
        if rec is None:
            rec = next((by_series[k] for k in sorted(by_series)
                        if k[0] == urn), None)
        if rec is None:
            status = "off_corpus"
        else:
            return corpus_source_entry(
                hint, status, urn, dispositivo, rec, parsed, root,
                citation_map, as_of, stale_after_days, excerpt_cap,
                integrity_failures)

    if hint in catalog_hints:
        entry = catalog_hints[hint]
        return {
            "resolution": "catalog",
            "source": {
                "hint": hint,
                "resolution": "catalog",
                "name": entry.get("name", ""),
                "citation_url": entry.get("url", ""),
                "citation_from": "catalogo_curado",
                "source_kind": entry.get("source_kind", ""),
                "anchor_claim": entry.get("anchor_claim", ""),
                "vigencia_confirmada": False,
                "alerta_vigencia": (
                    "fonte do catálogo curado sem verificação automática de "
                    "vigência/conteúdo no corpus; a proveniência live da onda "
                    "confirma a URL, e o redator confere o teor na própria "
                    "fonte"),
                "uso_do_trecho": USO_DO_TRECHO,
            },
        }

    connector = classify_connector(hint, parsed)
    norma = None
    if parsed and parsed["numero"] is not None:
        # chave agregável por norma (sem ano) para o censo de lacunas.
        norma = f"{parsed['kind'] or 'lei'}:{parsed['numero']}"
    elif parsed and parsed["sumula_num"] is not None:
        norma = (f"sumula-{parsed['sumula_court'] or 'indefinido'}:"
                 f"{parsed['sumula_num']}")
    return {
        "resolution": "unresolved",
        "unresolved": {
            "hint": hint,
            "norma": norma,
            "ano": parsed["ano"] if parsed else None,
            "artigo": parsed["artigo"] if parsed else None,
            "connector_needed": connector,
            "regra": ("pesquisa de fonte oficial obrigatória antes da "
                      "redação; PROIBIDO inventar fonte ou URL"),
        },
    }


def corpus_source_entry(hint, status, urn, dispositivo, rec, parsed, root,
                        citation_map, as_of, stale_after_days, excerpt_cap,
                        integrity_failures):
    vigencia_status = rec.get("vigencia_status", "")
    vigencia_confirmada = vigencia_status == "vigente"
    last_verified = rec.get("last_verified_at") or rec.get("as_of_date") or ""
    age_days = None
    stale = False
    if last_verified:
        try:
            verified_date = datetime.date.fromisoformat(last_verified)
            age_days = (as_of - verified_date).days
            stale = age_days > stale_after_days
        except ValueError:
            stale = True

    alerta = None
    if vigencia_status == "revogado" or rec.get("revogado_por"):
        alerta = (f"NORMA/DISPOSITIVO REVOGADO"
                  f"{' por ' + rec['revogado_por'] if rec.get('revogado_por') else ''}: "
                  "não usar como base de direito vigente; tratar apenas como "
                  "histórico com a norma sucessora")
    elif vigencia_status == "vetado":
        # corpus.VigenciaStatusVetado (ADR de 2026-09-05): o veto presidencial
        # derrubou o texto antes da promulgação. Sem este ramo o dispositivo
        # caía no genérico "vigência não verificada" — alerta mais fraco do que
        # a verdade, e que deixaria o redator livre para tratá-lo como norma
        # possivelmente em vigor.
        alerta = ("DISPOSITIVO VETADO: o veto presidencial derrubou o texto "
                  "antes da promulgação e ele NUNCA entrou em vigor; não é "
                  "direito vigente nem histórico revogado. Só pode ser "
                  "mencionado como o fato do veto, com a fonte oficial")
    elif not vigencia_confirmada:
        alerta = ("vigência não verificada automaticamente no corpus; o "
                  "redator não afirma vigência categórica sem conferir a "
                  "fonte oficial citada")
    elif stale:
        alerta = (f"última verificação há {age_days} dias (> "
                  f"{stale_after_days}); conferir a fonte oficial antes de "
                  "afirmar teor/vigência atual")

    trecho = None
    truncado = False
    if status == "corpus_article":
        # dispositivo de artigo OU enunciado de súmula (série de dispositivo
        # vazio): blob pequeno e pertinente — entra como conferência.
        text = read_blob(root, rec)
        if text is None:
            integrity_failures.append({
                "hint": hint, "urn_lex": urn, "dispositivo": dispositivo,
                "blob_ref": rec.get("blob_ref", "")})
        else:
            trecho = text.strip()
            if len(trecho) > excerpt_cap:
                trecho = trecho[:excerpt_cap]
                truncado = True

    key_match = URN_NORM_RE.match(urn)
    citation = None
    if key_match:
        citation = citation_map.get((key_match.group(1), key_match.group(3)))

    source = {
        "hint": hint,
        "resolution": status,
        "name": display_name(urn, dispositivo or ""),
        "urn_lex": urn,
        "dispositivo": dispositivo or "",
        "citation_url": citation["url"] if citation else rec.get(
            "source_url", ""),
        "citation_from": ("catalogo_curado" if citation
                          else "corpus_fetch_url"),
        "fetch_url": rec.get("source_url", ""),
        "urn_resolver_url": f"https://normas.leg.br/?urn={urn}",
        "http_status": rec.get("http_status"),
        "robots_ok": rec.get("robots_ok"),
        "source_channel": rec.get("source_channel", ""),
        "vigencia_status": vigencia_status,
        "vigencia_confirmada": vigencia_confirmada,
        "vigencia_inicio": rec.get("vigencia_inicio", ""),
        "vigencia_fim": rec.get("vigencia_fim", ""),
        "revogado_por": rec.get("revogado_por", ""),
        "last_verified_at": last_verified,
        "verification_age_days": age_days,
        "stale_verification": stale,
        "content_sha256": rec.get("content_sha256", ""),
        "blob_ref": rec.get("blob_ref", ""),
        "uso_do_trecho": USO_DO_TRECHO,
    }
    if alerta:
        source["alerta_vigencia"] = alerta
    if trecho is not None:
        source["trecho_legal_conferencia"] = trecho
        source["trecho_truncado"] = truncado
    if status == "corpus_norm_article_missing" and parsed and \
            parsed.get("artigo"):
        source["artigo_pedido_sem_snapshot"] = parsed["artigo"] + (
            f"-{parsed['sufixo'].upper()}" if parsed.get("sufixo") else "")
        source["alerta_dispositivo"] = (
            "o artigo pedido pelo hint não tem snapshot próprio no corpus; "
            "o redator confere o dispositivo na fonte oficial citada antes "
            "de afirmar teor")
    return {"resolution": status, "source": source}


if __name__ == "__main__":
    sys.exit(main())
