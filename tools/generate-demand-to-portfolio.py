#!/usr/bin/env python3
"""Conversor demanda->portfolio_v2 (secao 12 do PLANO_ARQUITETURA_FABRICA_10M).

Pega CANDIDATOS CONFIRMADOS e os materializa como intents no formato canonico
de 11 campos do portfolio_v2, DEDUPADOS contra o portfolio existente (DEC-007),
IDEMPOTENTE por conjunto (saida ordenada e deterministica -> re-run reescreve
bytes identicos).

Duas fontes de candidato confirmado:
  (A) ENTIDADE ancorada em URN LexML oficial
      -> data/source-registry/entity_page_candidates-*.jsonl
      (cada URN unica = pagina distinta; chave canonica = URN).
  (B) DEMANDA com 2 familias de superficie independentes
      -> data/research/demand_confirmation_state.jsonl
      filtro: independent_surface_family_count >= 2.
      (hoje rende 0 -- caminho honesto/vazio, NAO se fabrica confirmacao.)

REGRA metadata-only / DEC-017 / proibido inventar: a maquina NAO conhece o teor
(enunciado/holding) da sumula/artigo. Portanto todo intent convertido nasce com
needs_source_research=true e com distinct_because/reader_problem ancorados em
IDENTIDADE (numero, tribunal/codigo, titulo oficial, URN) -- nunca numa descricao
inventada do que a norma decide. O texto oficial e pesquisado na fonte antes da
redacao (fora deste conversor).

Saida NAO commitada. Prova = rodar o gate real
check-portfolio-v2-intent-distinctness sobre existente+novo.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_DIR = os.path.join(ROOT, "data", "editorial", "portfolio_v2")
ENTITY_GLOB = os.path.join(ROOT, "data", "source-registry", "entity_page_candidates-*.jsonl")
DEMAND_STATE = os.path.join(ROOT, "data", "research", "demand_confirmation_state.jsonl")

INTENT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Sinal textual ANCORADO de sumula na long_tail de um intent existente.
# Vale como assinatura de dedup somente quando a referencia esta na CABECA da
# consulta (ate SUMULA_TEXTUAL_HEAD_TOKENS tokens antes), isto e, quando o
# intent existente e SOBRE aquela sumula -- "sumula 479 do stj", "o que diz a
# sumula 385 do stj sobre negativacao". Citacao de passagem no meio da prosa de
# outro intent NAO gera assinatura: derrubava candidato legitimo como
# dedup_signature sem que existisse pagina dedicada aquela sumula.
# O conectivo opcional ("do/da/de") e obrigatorio para nao repetir o
# falso-NEGATIVO da versao anterior, que exigia adjacencia ("sumula 479 stj") e
# por isso deixava passar a forma canonica gerada por este proprio conversor
# ("sumula 479 do stj") -- 32 intents vivos do portfolio escapavam do dedup.
SUMULA_TEXTUAL_HEAD_TOKENS = 5
SUMULA_TEXTUAL = re.compile(r"\bsumula (vinculante )?(\d+) (?:d[eao] )?(stf|stj|tst)\b")
SUMULA_TEXTUAL_INVERTED = re.compile(r"\b(stf|stj|tst) sumula (vinculante )?(\d+)\b")

COURT_BY_URN = [
    ("supremo.tribunal.federal", "STF", "sumula-vinculante" if False else None),
    ("superior.tribunal.justica", "STJ", None),
    ("tribunal.superior.trabalho", "TST", None),
]


def strip_accents(text):
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def kebab(text):
    ascii_text = strip_accents(text).lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    return ascii_text.strip("-")


def norm_long_tail(text):
    """Espelha legalsignature.NormalizeText o suficiente p/ dedup coarse:
    minusculas, sem acento, colapsa nao-alfanumerico em espaco."""
    ascii_text = strip_accents(text).lower()
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return " ".join(ascii_text.split())


# ---------------------------------------------------------------------------
# Leitura do portfolio existente -> conjuntos de dedup
# ---------------------------------------------------------------------------

def load_existing():
    existing_ids = set()
    existing_longtail = set()
    existing_sig = set()  # assinatura semantica coarse (ex.: ("sumula","stf","104"))
    for path in sorted(glob.glob(os.path.join(PORTFOLIO_DIR, "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                iid = d.get("intent_id", "")
                existing_ids.add(iid)
                existing_longtail.add(norm_long_tail(d.get("long_tail_query", "")))
                for sig in signatures_from_existing(d):
                    existing_sig.add(sig)
    return existing_ids, existing_longtail, existing_sig


def signatures_from_existing(d):
    """Extrai assinatura(s) coarse de um intent existente p/ dedup semantica."""
    sigs = []
    iid = d.get("intent_id", "")
    m = re.match(r"^sum-(stj|stf|tst|sv)-(\d+)$", iid)
    if m:
        sigs.append(("sumula", m.group(1), m.group(2)))
    m = re.match(r"^lei-([a-z0-9]+)-art-(\d+[a-z]?)$", iid)
    if m:
        sigs.append(("artigo", m.group(1), m.group(2)))
    # Sinal textual ANCORADO (ver SUMULA_TEXTUAL acima): so conta quando o
    # intent existente e' SOBRE a sumula, nunca quando ela aparece de passagem
    # no meio da prosa de outro intent.
    q = norm_long_tail(d.get("long_tail_query", ""))
    for pattern, inverted in ((SUMULA_TEXTUAL, False),
                              (SUMULA_TEXTUAL_INVERTED, True)):
        for match in pattern.finditer(q):
            if len(q[:match.start()].split()) > SUMULA_TEXTUAL_HEAD_TOKENS:
                continue
            if inverted:
                court, vinculante, num = match.group(1), match.group(2), match.group(3)
            else:
                vinculante, num, court = match.group(1), match.group(2), match.group(3)
            # "sv" espelha o court_slug de parse_entity para sumula vinculante:
            # SV 11 do STF e a Sumula 11 do STF sao paginas distintas.
            sigs.append(("sumula", "sv" if vinculante else court, num))
    return sigs


# ---------------------------------------------------------------------------
# Fonte A: ENTIDADE ancorada em URN
# ---------------------------------------------------------------------------

def parse_entity(d):
    """Retorna dict de campos derivados da entidade, ou None se nao conversivel."""
    urn = d.get("urn", "")
    tipo = d.get("tipo", "")
    titulo = (d.get("titulo_curto", "") or "").strip()
    fonte = d.get("fonte_oficial_url", "")
    source_id = d.get("source_id", "")

    if tipo in ("sumula", "sumula_vinculante"):
        court = None
        for frag, name, _ in COURT_BY_URN:
            if frag in urn:
                court = name
                break
        m = re.search(r";(\d+)\s*$", urn)
        if not court or not m:
            return None
        num = m.group(1)
        vinc = tipo == "sumula_vinculante"
        court_slug = ("sv" if vinc else court.lower())
        sig = ("sumula", court_slug, num)
        intent_id = "sum-%s-%s" % (court_slug, num)
        court_label = ("Súmula Vinculante %s do STF" % num if vinc
                       else "Súmula %s do %s" % (num, court))
        long_tail = ("súmula vinculante %s do stf o que diz e quando se aplica" % num
                     if vinc else
                     "súmula %s do %s o que diz e quando se aplica" % (num, court.lower()))
        working_title = titulo or court_label
        reader_problem = (
            "Pessoa se deparou com a %s em uma decisão ou petição e precisa "
            "entender o alcance e a aplicação do enunciado %s antes de recorrer "
            "ou fundamentar o pedido." % (court_label, num))
        distinct_because = (
            "Enunciado próprio da %s (chave %s): norma sumular distinta por número "
            "e teor consolidado, cujo texto oficial será pesquisado na fonte %s "
            "antes da redação." % (court_label, urn, court))
        hints = [kebab("sumula-%s-%s" % (num, court_slug)), court.lower()]
        practice_area = "sumulas"
        family = ("stf-sumula-vinculante" if vinc else "%s-sumula" % court.lower())
        page_type = "verbete"

    elif tipo in ("tema_repercussao_geral", "tema_repetitivo"):
        court = "STF" if tipo == "tema_repercussao_geral" else "STJ"
        m = re.search(r";(\d+)\s*$", urn) or re.search(r"(\d+)\s*$", titulo)
        if not m:
            return None
        num = m.group(1)
        kind = "repercussão geral" if court == "STF" else "repetitivo"
        sig = ("tema", court.lower(), num)
        intent_id = "tema-%s-%s" % (court.lower(), num)
        label = "Tema %s de %s do %s" % (num, kind, court)
        long_tail = "tema %s de %s do %s o que decidiu" % (num, kind, court.lower())
        working_title = titulo or label
        reader_problem = (
            "Parte ou advogado encontrou o %s citado como precedente vinculante e "
            "precisa saber a tese firmada no tema %s antes de sustentar o recurso."
            % (label, num))
        distinct_because = (
            "Precedente qualificado de %s no %s (chave %s): tese vinculante própria, "
            "distinta por número e objeto, com texto oficial a pesquisar na fonte "
            "antes da redação." % (kind, court, urn))
        hints = [kebab("tema-%s-%s" % (num, court.lower())), court.lower()]
        practice_area = "sumulas"
        family = "%s-tema" % court.lower()
        page_type = "verbete"

    elif tipo in ("artigo",):
        m = re.search(r"!art(\d+[a-z]?)", urn)
        if not m or not source_id:
            return None
        art = m.group(1)
        sig = ("artigo", kebab(source_id), art)
        intent_id = "lei-%s-art-%s" % (kebab(source_id), art)
        label = titulo or ("Artigo %s" % art)
        long_tail = "artigo %s %s o que estabelece" % (art, kebab(source_id).replace("-", " "))
        working_title = label
        reader_problem = (
            "Pessoa precisa entender o que o %s determina e como esse dispositivo "
            "se aplica ao seu caso concreto antes de agir." % label)
        distinct_because = (
            "Dispositivo legal próprio — %s (chave %s): regra específica distinta "
            "dos demais artigos, com texto oficial a pesquisar na fonte oficial "
            "antes da redação." % (label, urn))
        hints = [kebab(source_id), "planalto"]
        practice_area = "leis"
        family = kebab(source_id)
        page_type = "verbete"
    else:
        return None

    if not fonte.startswith("https://"):
        return None
    if INTENT_ID.fullmatch(intent_id) is None:
        return None
    # dedup interno de hints
    seen = set()
    hints = [h for h in hints if h and not (h in seen or seen.add(h))]

    return {
        "sig": sig,
        "urn": urn,
        "intent": {
            "intent_id": intent_id,
            "page_type": page_type,
            "practice_area": practice_area,
            "family": family,
            "long_tail_query": long_tail,
            "working_title": working_title,
            "reader_problem": reader_problem,
            "lane": "informativa",
            "source_hints": hints,
            "needs_source_research": True,
            "distinct_because": distinct_because,
        },
    }


def load_entity_candidates():
    out = []
    for path in sorted(glob.glob(ENTITY_GLOB)):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# Fonte B: DEMANDA 2 familias independentes (honesto: hoje = 0)
# ---------------------------------------------------------------------------

def load_confirmed_demand():
    confirmed = []
    if not os.path.exists(DEMAND_STATE):
        return confirmed
    with open(DEMAND_STATE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if int(d.get("independent_surface_family_count", 0)) >= 2:
                confirmed.append(d)
    return confirmed


# ---------------------------------------------------------------------------
# Conversao + dedup + idempotencia
# ---------------------------------------------------------------------------

def convert(only_tipo=None, court_filter=None, limit=0):
    existing_ids, existing_longtail, existing_sig = load_existing()
    # Fonte B e' medida, mas NAO alimenta `emitted` nesta versao: a emissao
    # abaixo itera so' load_entity_candidates() (Fonte A). A chave leva o
    # sufixo _not_emitted para o numero no stderr nao ser lido como
    # contribuicao -- hoje o filtro independent_surface_family_count>=2 rende 0
    # em 11.255 registros de demand_confirmation_state.jsonl (medido 2026-07-29,
    # max observado = 0). Quando a camada de demanda amadurecer e esse contador
    # ficar > 0, integrar a emissao aqui; enquanto for 0, o valor e' a evidencia
    # honesta de que nao se fabrica confirmacao.
    stats = {
        "entity_input": 0,
        "demand_confirmed_source_b_not_emitted": len(load_confirmed_demand()),
        "unparseable": 0, "dedup_intent_id": 0, "dedup_signature": 0,
        "dedup_longtail": 0, "dedup_within_batch": 0, "emitted": 0,
    }
    emitted = []
    seen_ids = set()
    seen_sig = set()
    seen_lt = set()

    for cand in load_entity_candidates():
        tipo = cand.get("tipo", "")
        if only_tipo and tipo != only_tipo:
            continue
        stats["entity_input"] += 1
        rec = parse_entity(cand)
        if rec is None:
            stats["unparseable"] += 1
            continue
        intent = rec["intent"]
        if court_filter and court_filter.lower() not in intent["intent_id"]:
            continue
        sig = rec["sig"]
        lt = norm_long_tail(intent["long_tail_query"])
        if intent["intent_id"] in existing_ids:
            stats["dedup_intent_id"] += 1
            continue
        if sig in existing_sig:
            stats["dedup_signature"] += 1
            continue
        if lt in existing_longtail:
            stats["dedup_longtail"] += 1
            continue
        if intent["intent_id"] in seen_ids or sig in seen_sig or lt in seen_lt:
            stats["dedup_within_batch"] += 1
            continue
        seen_ids.add(intent["intent_id"])
        seen_sig.add(sig)
        seen_lt.add(lt)
        emitted.append(intent)

    # ordenacao deterministica -> idempotencia por conjunto
    emitted.sort(key=lambda x: x["intent_id"])
    if limit and len(emitted) > limit:
        emitted = emitted[:limit]
    stats["emitted"] = len(emitted)
    return emitted, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="arquivo de saida .jsonl")
    ap.add_argument("--tipo", default=None, help="filtra por tipo de entidade (ex.: sumula)")
    ap.add_argument("--court", default=None, help="filtra por tribunal no intent_id (ex.: stf)")
    ap.add_argument("--limit", type=int, default=0, help="teto de intents emitidos (0=sem teto)")
    ap.add_argument("--stats-only", action="store_true")
    args = ap.parse_args()

    emitted, stats = convert(args.tipo, args.court, args.limit)
    print(json.dumps(stats, ensure_ascii=False), file=sys.stderr)
    if args.stats_only:
        return 0

    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for intent in emitted:
            fh.write(json.dumps(intent, ensure_ascii=False) + "\n")
    os.replace(tmp, args.out)
    print("wrote %d intents -> %s" % (len(emitted), args.out), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
