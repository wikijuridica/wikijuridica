#!/usr/bin/env python3
"""generate-source-hint-catalog-normas-legbr — conector metadata-only.

Dado um source_hint slug do portfolio_v2 (ex.: "cc-lei-10406-2002-art-1147")
que descreve um ato normativo federal explícito (lei, lei complementar,
decreto, decreto-lei, emenda constitucional) com número e ano, resolve a URL
oficial canônica no portal normas.leg.br (Rede LexML/Senado Federal) via a
API pública de dados abertos do Senado (legis.senado.leg.br/dadosabertos,
sem credencial, robots Allow /), VERIFICA ao vivo (HTTP 200 real, corpo
contém o número do ato) e escreve o resultado como novas entradas em
data/editorial/v2_source_hint_catalog.json.

Metadata-only: nunca lê nem copia o corpo articulado do ato. O anchor_claim
é só uma frase de identificação institucional (tipo, número, data de
assinatura), nunca um resumo do conteúdo jurídico do ato.

Nunca edita o catálogo na mão: este é o gerador sancionado. Idempotente:
não sobrescreve entrada existente; roda de novo só adiciona o que faltar.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import time
import http.client
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_v2_source_hint_resolution import (  # noqa: E402
    parse_explicit_identities, read_regular_snapshot, decode_object,
    decode_jsonl, RegistryMatcher, normalize_url,
)

HINT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGAL_KINDS = {"lei", "lei-complementar", "decreto-lei", "decreto", "emenda-constitucional"}
TIPO_SEGMENT = {
    "lei": "LEI", "lei-complementar": "LCP", "decreto": "DEC",
    "decreto-lei": "DEL", "emenda-constitucional": "EMC",
}
KIND_LABEL = {
    "lei": "Lei", "lei-complementar": "Lei Complementar", "decreto": "Decreto",
    "decreto-lei": "Decreto-Lei", "emenda-constitucional": "Emenda Constitucional",
}
# Identidade única de saída (CLAUDE.md §11 e internal/wikijuridicabot). Este
# arquivo fala com DOIS hosts externos: legis.senado.leg.br (resolução do ato
# em `resolve_act`) e normas.leg.br (conferência ao vivo em `verify_url_live`).
#
# MEDIDO em 2026-09-05, um GET por host:
#   legis.senado.leg.br/dadosabertos/legislacao/LEI/10192/2001?formato=json
#       canônico -> HTTP 200, 6.118 bytes | antigo -> HTTP 200, 6.118 bytes
#   normas.leg.br/api/public/metadados/gerais?urn=...lei:2001;10192
#       canônico -> HTTP 200, 3.690 bytes | antigo -> HTTP 200, 3.690 bytes
# Nenhum dos dois discrimina por User-Agent; a identidade canônica não custa
# acesso e torna a coleta verificável por quem a recebe.
USER_AGENT = ("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
              "+https://wikijuridica.com.br/bot/; verificacao-de-fonte)")
MAX_CATALOG_BYTES = 8 << 20
MAX_PORTFOLIO_BYTES = 64 << 20
MAX_REGISTRY_BYTES = 16 << 20


def fetch_json(url: str, timeout: float) -> dict | None:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            raw = resp.read(4 << 20)
    except (urllib.error.URLError, TimeoutError, ConnectionError,
            http.client.HTTPException):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def verify_url_live(url: str, timeout: float) -> bool:
    """Confirma ao vivo que a URL oficial responde 200. Nunca registra URL
    não verificada. Não lê nem armazena o corpo (checagem de status apenas
    com HEAD; fallback GET bounded só para status quando HEAD não é aceito)."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except urllib.error.HTTPError as exc:
            if exc.code == 405 and method == "HEAD":
                continue
            return False
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                http.client.HTTPException):
            return False
    return False


def resolve_act(kind: str, number: str, year: str, timeout: float, delay: float) -> dict | None:
    tipo = TIPO_SEGMENT[kind]
    api_url = (f"https://legis.senado.leg.br/dadosabertos/legislacao/"
               f"{tipo}/{number}/{year}?formato=json")
    payload = fetch_json(api_url, timeout)
    time.sleep(delay)
    if not payload:
        return None
    try:
        docs = payload["DetalheDocumento"]["documentos"]["documento"]
    except (KeyError, TypeError):
        return None
    if not isinstance(docs, list) or len(docs) != 1:
        return None
    ident = docs[0].get("identificacao")
    if not isinstance(ident, dict):
        return None
    url_documento = ident.get("urlDocumento")
    norma_nome = ident.get("normaNome")
    data_assinatura = ident.get("dataassinatura")
    numero_resp = ident.get("numero")
    if (not isinstance(url_documento, str) or not isinstance(norma_nome, str) or
            not isinstance(data_assinatura, str) or not isinstance(numero_resp, str)):
        return None
    normalized = normalize_url(url_documento)
    if not normalized or not normalized.startswith("https://normas.leg.br/"):
        return None
    if re.sub(r"^0+", "", numero_resp) != re.sub(r"^0+", "", number):
        return None
    if not verify_url_live(normalized, timeout):
        return None
    return {"url": normalized, "name": norma_nome, "signature_date": data_assinatura}


def load_catalog(root: Path) -> tuple[dict, bytes]:
    path = root / "data/editorial/v2_source_hint_catalog.json"
    payload = read_regular_snapshot(path, MAX_CATALOG_BYTES)
    return decode_object(payload, str(path)), payload


def load_registry_matcher(root: Path) -> RegistryMatcher:
    path = root / "data/source-registry/source_registry_v2.jsonl"
    payload = read_regular_snapshot(path, MAX_REGISTRY_BYTES)
    records = [row for _, row in decode_jsonl(payload, str(path))]
    return RegistryMatcher(records)


def collect_candidate_hints(root: Path) -> dict[str, tuple[str, str, str]]:
    """Varre portfolio_v2 e devolve {hint_slug: (kind, number, year)} para
    hints em formato de slug canônico (HINT_ID) com identidade explícita de
    ato normativo federal com número e ano — os únicos hints que a chave do
    catálogo (regex de slug) pode resolver."""
    import glob
    candidates: dict[str, tuple[str, str, str]] = {}
    for filename in sorted(glob.glob(str(root / "data/editorial/portfolio_v2/*.jsonl"))):
        payload = read_regular_snapshot(Path(filename), MAX_PORTFOLIO_BYTES)
        for _, row in decode_jsonl(payload, filename):
            hints = row.get("source_hints")
            if not isinstance(hints, list):
                continue
            for hint in hints:
                if not isinstance(hint, str) or not HINT_ID.fullmatch(hint) or hint in candidates:
                    continue
                ids = parse_explicit_identities(hint.replace("-", " "))
                if len(ids) == 1 and ids[0].kind in LEGAL_KINDS and ids[0].year:
                    candidates[hint] = (ids[0].kind, ids[0].number, ids[0].year)
    return candidates


def atomic_write_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(obj, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            os.unlink(tmp)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-acts", type=int, default=0, help="0 = sem limite")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.35,
                         help="segundos entre chamadas ao Senado dados-abertos (respeito a rate limit)")
    parser.add_argument("--apply", action="store_true",
                         help="grava o catálogo; sem esta flag roda em modo dry-run só de relatório")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    catalog, _raw = load_catalog(root)
    sources = catalog.setdefault("source_hints", {})
    matcher = load_registry_matcher(root)

    candidates = collect_candidate_hints(root)
    pending = sorted(hint for hint in candidates if hint not in sources)

    acts_cache: dict[tuple[str, str, str], dict | None] = {}
    resolved = 0
    unresolved = 0
    added_hints = []
    checked_acts = 0
    for hint in pending:
        if args.max_acts and checked_acts >= args.max_acts and (candidates[hint] not in acts_cache):
            continue
        act = candidates[hint]
        if act not in acts_cache:
            checked_acts += 1
            kind, number, year = act
            acts_cache[act] = resolve_act(kind, number, year, args.timeout, args.delay)
        result = acts_cache[act]
        if result is None:
            unresolved += 1
            continue
        if not matcher.match(result["url"]):
            unresolved += 1
            continue
        kind, number, year = act
        anchor_claim = (
            f"{KIND_LABEL[kind]} nº {result['name'].split('nº', 1)[-1].split(' de', 1)[0].strip() or number}, "
            f"de {result['signature_date']}, identificada pela URN LexML e disponível no portal oficial "
            "consolidado da Rede de Informação Legislativa e Jurídica (normas.leg.br / Senado Federal)."
        )
        sources[hint] = {
            "name": result["name"],
            "url": result["url"],
            "anchor_claim": anchor_claim,
            "source_kind": "legal_act",
        }
        resolved += 1
        added_hints.append(hint)

    report = {
        "candidate_slug_hints_total": len(candidates),
        "already_in_catalog": len(candidates) - len(pending),
        "pending_before_run": len(pending),
        "distinct_acts_queried": checked_acts,
        "resolved_hints_added": resolved,
        "unresolved_hints": unresolved,
        "applied": bool(args.apply),
    }
    if args.apply and resolved:
        catalog_path = root / "data/editorial/v2_source_hint_catalog.json"
        atomic_write_json(catalog_path, catalog)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    if added_hints:
        print("added_hints_sample:", json.dumps(sorted(added_hints)[:10], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
