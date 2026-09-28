#!/usr/bin/env python3
"""Cria as 3 intencoes-vizinhas ausentes do portfolio v2 (2026-08-12).

Motivo (apurado no acervo vivo, nao em memoria): tres paginas ja escritas
ficaram sem vizinha afim de verdade porque o tema companheiro nao existe em
`data/editorial/portfolio_v2/`:

  1. `lei-anticorrupcao` (data/editorial/v2_pages/leis-inf1.jsonl) declara
     internal_link_topics ["acordo-de-leniencia", "programa-de-integridade",
     "licitacao-e-fraude"]. O portfolio tem `lei-improbidade-administrativa` e
     `adm-licitacao`, mas NENHUMA intencao sobre a ARTICULACAO dos tres regimes
     sancionatorios sobre o mesmo fato (art. 159 da Lei 14.133 manda apurar
     conjuntamente o que tambem e ato lesivo da Lei 12.846).

  2. `lei-lindb` (mesmo shard) declara ["hierarquia-das-normas",
     "vigencia-da-lei", "direito-adquirido"]. Existe pagina para
     `const-direito-adquirido`; nao existe nenhuma intencao sobre hierarquia
     (lei x decreto x portaria) nem sobre vigencia/vacancia/revogacao.

  3. `trib-aduana-drawback-suspensao` (data/editorial/v2_pages/tributario-r08.jsonl)
     declara ["drawback suspensao", "ato concessorio", "regime aduaneiro"]. O
     portfolio so tem a modalidade SUSPENSAO; a modalidade ISENCAO (reposicao de
     estoque, arts. 383, II, e 393 a 396 do Regulamento Aduaneiro) nao existe.

Busca de duplicidade executada antes de criar (regex sobre os 11 campos de
10.041 registros de portfolio_v2 e sobre v2_pages): nenhum intent_id ja cobre
os tres temas. As intencoes nascem com family e practice_area REUTILIZADAS
(`panorama-leis` / `regimes-aduaneiros`) para que a fila canonica as selecione
sem contrato novo.

Por que arquivos NOVOS e nao append em leis-w3.jsonl/tributario.jsonl: append
mudaria o `portfolio_sha256` desses arquivos e invalidaria qualquer lote da fila
de escrita pinado neles. Arquivo novo (padrao das ondas -w3/-r06 ja existentes)
nao perturba nenhum sha256 vigente.

Este script NAO escreve em data/editorial/v2_pages/ (isso e exclusivo do writer
CAS), NAO commita e NAO publica. Seguranca: lease canonica de estoque + lock
exclusivo, criacao apenas se o arquivo nao existir ou ja for exatamente o
payload esperado (idempotente), escrita atomica com fsync.
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

LOCK = ROOT / "data/editorial/.generate-portfolio-vizinhas-20260812.lock"

PORTFOLIO_FIELDS = (
    "intent_id", "page_type", "practice_area", "family", "long_tail_query",
    "working_title", "reader_problem", "lane", "source_hints",
    "needs_source_research", "distinct_because",
)

NEW_INTENTS = {
    "data/editorial/portfolio_v2/leis-viz1.jsonl": [
        {
            "intent_id": "lei-empresa-sancao-fraude-licitacao",
            "page_type": "guia_problema",
            "practice_area": "leis",
            "family": "panorama-leis",
            "long_tail_query": (
                "empresa responde na lei anticorrupção e na lei de licitações "
                "pelo mesmo contrato"
            ),
            "working_title": (
                "Empresa acusada de fraude em licitação: quais leis a punem e "
                "como as sanções se somam"
            ),
            "reader_problem": (
                "Sócio de empresa que recebeu intimação de processo de "
                "responsabilização por fraude em licitação não sabe se "
                "responde pela Lei 14.133/2021, pela Lei Anticorrupção ou pela "
                "Lei de Improbidade, se os processos correm juntos e se o "
                "programa de integridade e o acordo de leniência ainda "
                "adiantam alguma coisa depois de instaurada a apuração."
            ),
            "lane": "informativa",
            "source_hints": [
                "lei-14133-2021-licitacoes",
                "lei-no-12-846-de-1o-de-agosto-de-2013-planalto",
                "lei-no-8-429-de-2-de-junho-de-1992-planalto",
                "lei-14230-2021",
            ],
            "needs_source_research": False,
            "distinct_because": (
                "trata da articulação entre regimes sancionatórios sobre o "
                "mesmo fato — apuração conjunta determinada pelo art. 159 da "
                "Lei 14.133, responsabilização objetiva da pessoa jurídica na "
                "Lei 12.846, desconsideração da personalidade jurídica, "
                "reabilitação e o alcance restringido da Lei 8.429 depois da "
                "Lei 14.230 —, enquanto as páginas existentes descrevem cada "
                "lei isoladamente e a de licitação cuida do procedimento de "
                "contratação, não da punição da empresa"
            ),
        },
        {
            "intent_id": "lei-hierarquia-e-vigencia-das-normas",
            "page_type": "verbete",
            "practice_area": "leis",
            "family": "panorama-leis",
            "long_tail_query": (
                "portaria pode exigir o que a lei não exige e quando a lei "
                "nova passa a valer"
            ),
            "working_title": (
                "Lei, decreto e portaria: qual norma prevalece e desde quando "
                "ela obriga"
            ),
            "reader_problem": (
                "Pessoa que encontrou portaria ou instrução normativa exigindo "
                "documento que a lei não pede quer saber qual das duas "
                "prevalece, e também a partir de que data uma lei recém "
                "publicada realmente passa a obrigar."
            ),
            "lane": "informativa",
            "source_hints": [
                "decreto-lei-no-4-657-de-4-de-setembro-de-1942-planalto",
            ],
            "needs_source_research": False,
            "distinct_because": (
                "explica os critérios de solução de conflito entre normas — "
                "hierárquico (ato infralegal não inova sobre a lei) e "
                "cronológico (vacância de 45 dias, revogação expressa e "
                "tácita, lei especial que convive com a geral) —, enquanto o "
                "verbete da LINDB apresenta a lei como um todo e a página de "
                "direito adquirido cuida do efeito da lei nova sobre situações "
                "já consolidadas"
            ),
        },
    ],
    "data/editorial/portfolio_v2/tributario-viz1.jsonl": [
        {
            "intent_id": "trib-aduana-drawback-isencao-reposicao-estoque",
            "page_type": "guia_problema",
            "practice_area": "tributario",
            "family": "regimes-aduaneiros",
            "long_tail_query": (
                "drawback isenção repõe insumo de exportação já feita como "
                "pedir o ato concessório"
            ),
            "working_title": (
                "Drawback isenção: repor o estoque de insumo depois que a "
                "exportação já aconteceu"
            ),
            "reader_problem": (
                "Indústria que já exportou usando insumo importado com tributo "
                "pago quer saber se consegue repor esse estoque sem novo custo "
                "tributário, que prova de exportação anterior o ato concessório "
                "exige e por que esse caminho é diferente do drawback "
                "suspensão, que amarra a importação a um compromisso futuro."
            ),
            "lane": "comercial",
            "source_hints": [
                "decreto-6-759-2009-regulamento-aduaneiro",
                "lei-12-350-2010",
            ],
            "needs_source_research": True,
            "distinct_because": (
                "modalidade de isenção do drawback — reposição de estoque "
                "apoiada em exportação JÁ comprovada, arts. 383, II, e 393 a "
                "396 do Regulamento Aduaneiro —, cuja lógica temporal é "
                "inversa à do drawback suspensão, que condiciona a importação "
                "desonerada a exportar depois dentro do prazo do ato "
                "concessório"
            ),
        },
    ],
}


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


def existing_intent_ids():
    seen = {}
    directory = ROOT / "data/editorial/portfolio_v2"
    for path in sorted(directory.glob("*.jsonl")):
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            seen[json.loads(raw)["intent_id"]] = f"{path.name}:{number}"
    return seen


def render(records):
    lines = []
    for record in records:
        if tuple(record) != PORTFOLIO_FIELDS:
            raise SystemExit(f"campo fora do contrato de 11 chaves: {record['intent_id']}")
        lines.append(json.dumps(record, ensure_ascii=False))
    return ("\n".join(lines) + "\n").encode("utf-8")


def run_locked():
    catalog = json.loads(
        (ROOT / "data/editorial/v2_source_hint_catalog.json").read_text(encoding="utf-8")
    )["source_hints"]
    known = existing_intent_ids()
    created = 0
    for rel, records in sorted(NEW_INTENTS.items()):
        path = ROOT / rel
        payload = render(records)
        for record in records:
            for hint in record["source_hints"]:
                if hint not in catalog:
                    raise SystemExit(
                        f"source_hint fora do catalogo curado: {hint} "
                        f"({record['intent_id']}) — proibido inventar fonte"
                    )
            other = known.get(record["intent_id"])
            if other and not other.startswith(path.name + ":"):
                raise SystemExit(
                    f"intent_id ja existe no portfolio: {record['intent_id']} em {other}"
                )
        if path.exists():
            if path.read_bytes() == payload:
                print(f"already-present {rel} intents={len(records)}")
                continue
            raise SystemExit(f"{rel} existe com conteudo divergente — abortado sem sobrescrever")
        atomic_write(path, payload)
        created += len(records)
        print(f"created {rel} intents={len(records)} "
              f"ids={','.join(r['intent_id'] for r in records)}")
    print(f"total-created={created}")


def main():
    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(f"generate-portfolio-vizinhas-20260812: canonical stock busy: {error}",
              file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
