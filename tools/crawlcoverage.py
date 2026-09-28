#!/usr/bin/env python3
"""crawlcoverage — o leitor CANÔNICO de data/ops/crawl_coverage_daily.jsonl.

★ POR QUE ESTE MÓDULO EXISTE (medido em 2026-08-26)

O arquivo é append-only e CUMULATIVO, e não tinha leitor canônico. Consequência
medida no disco, agora:

    linhas                     1.225
    chaves (crawler, date)       220
    chaves com MAIS DE UMA linha 210   (95,5%)

E o caso que dá o tamanho do estrago: `googlebot` em `2026-08-12` tem **21
linhas**, e `paths_requested_that_day` assume {0, 7, 8, 13, 40, 103} entre elas.
`amazonbot` no mesmo dia varia de 105 a 4.667 — divergência de 4.562 numa única
chave. Quem somasse o arquivo (o jeito ingênuo) contaria o mesmo dia até 21
vezes; quem pegasse "a primeira linha" leria 0 onde houve 40.

É a MESMA armadilha que o ledger de borda já resolveu com
`tools/edgetelemetry.serie_saneada`, numa segunda fonte — e é por isso que a
interface aqui é a mesma: `serie_saneada(root)` devolvendo
`(por_chave, descartadas)`.

★ AS TRÊS REGRAS, E POR QUE CADA UMA

1. **Dedup por (crawler, date).** A convenção é DECLARADA pelo próprio produtor,
   em `tools/measure-crawl-coverage` (ele imprime "append-only: dedupe por
   (date, crawler) mantendo a ULTIMA linha"). Ela só nunca tinha sido
   implementada num leitor compartilhado.

2. **Schema v2 vence v1 na mesma chave.** As 193 linhas v1 contam por STRING de
   User-Agent; as 1.032 linhas v2 contam por identidade AUTENTICADA pela
   Cloudflare (`verifiedBotCategory`), que é o que separa o crawler real da
   sonda do próprio repositório. Medição do produtor: no access log local, 2.053
   de 2.061 linhas "Googlebot" eram `bot_sim=true` — inflação de 258x. Numa
   chave que tem as duas formas, a v1 é a leitura desmentida; ficar com "a
   última linha" já resolveria por ordem cronológica, mas depender da ordem de
   escrita para acertar a semântica é sorte, não desenho.

3. **Linha fisicamente impossível é DESCARTADA com o motivo à vista**, nunca
   somada: cobertura acumulada maior que o sitemap, paths pedidos num dia
   maiores que o sitemap, contagem negativa. Mesmo critério de
   `edgetelemetry.avaliar_linha`.

★ O QUE ESTE MÓDULO NÃO FAZ

Não soma dias. `cumulative_sitemap_coverage` já é acumulado pelo produtor (ele
guarda estado em `crawl_coverage_state.json` porque o dataset da Cloudflare tem
retenção de 8 dias); somar dois dias dessa série contaria a mesma URL duas
vezes. `paths_requested_that_day` e `new_sitemap_urls_that_day`, ao contrário,
são do DIA e podem ser somados. A distinção está em `CAMPOS_DO_DIA` e
`CAMPOS_ACUMULADOS` abaixo, para quem consome não precisar adivinhar.

Uso como módulo:

    import sys; sys.path.insert(0, "tools")
    import crawlcoverage
    por_chave, descartadas = crawlcoverage.serie_saneada(".")

Uso na linha de comando (auditoria):

    tools/crawlcoverage.py            # resumo do saneamento
    tools/crawlcoverage.py --json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

CAMINHO_RELATIVO = os.path.join("data", "ops", "crawl_coverage_daily.jsonl")

# Campos que descrevem O DIA: somáveis entre datas.
CAMPOS_DO_DIA = ("paths_requested_that_day", "new_sitemap_urls_that_day",
                 "requests_verified", "requests_discarded_unverified")

# Campos ACUMULADOS pelo produtor: NUNCA somar entre datas — a leitura correta
# é o valor da data mais recente.
CAMPOS_ACUMULADOS = ("cumulative_sitemap_coverage", "cumulative_coverage_pct",
                     "legacy_ua_cumulative_coverage")

# Precedência de schema. Número maior vence na mesma chave.
#
# v3 (2026-09-02): tools/measure-crawl-coverage ganhou a segunda lane de
# verificação por faixa de IP oficial (para o operador que a Cloudflare não
# autentica por verifiedBotCategory mas publica a própria faixa — medido no
# PerplexityBot). Schema AUSENTE deste mapa cai no default de `.get(..., 0)`
# abaixo, que perde para QUALQUER schema catalogado — é assim que uma v3 não
# listada aqui seria descartada em favor de uma v2 mais antiga na mesma chave,
# silenciosamente. Catalogar a versão nova é parte da correção, não um detalhe.
PRECEDENCIA_SCHEMA = {
    "crawl_coverage_daily_v1": 1,
    "crawl_coverage_daily_v2": 2,
    "crawl_coverage_daily_v3": 3,
}


def sha_linha(bruto: str) -> str:
    """Identidade estável da linha, para o descarte ser auditável.

    blake2b e não `hash()` do Python, que é randomizado por processo e por isso
    produziria um identificador diferente a cada execução — o contrato do dado
    real proíbe (R3).
    """
    return hashlib.blake2b(bruto.encode("utf-8"), digest_size=16).hexdigest()


def avaliar_linha(registro: dict) -> list[str]:
    """Devolve os motivos que tornam a linha impossível. Lista vazia = aceita."""
    motivos = []
    if not registro.get("crawler") or not registro.get("date"):
        motivos.append("sem crawler ou sem date")
        return motivos
    total = registro.get("sitemap_total")
    for campo in CAMPOS_DO_DIA + CAMPOS_ACUMULADOS:
        valor = registro.get(campo)
        if valor is None:
            continue
        if not isinstance(valor, (int, float)) or valor < 0:
            motivos.append(f"{campo} negativo ou não numérico: {valor!r}")
    if isinstance(total, int) and total > 0:
        for campo in ("paths_requested_that_day", "new_sitemap_urls_that_day",
                      "cumulative_sitemap_coverage"):
            valor = registro.get(campo)
            if isinstance(valor, int) and valor > total:
                motivos.append(f"{campo}={valor} maior que sitemap_total={total}")
    pct = registro.get("cumulative_coverage_pct")
    if isinstance(pct, (int, float)) and pct > 100.0:
        motivos.append(f"cumulative_coverage_pct={pct} acima de 100")
    return motivos


def serie_saneada(root: str, caminho: str | None = None):
    """A série de cobertura como um consumidor honesto deve lê-la.

    Devolve (por_chave, descartadas), com chave = (date, crawler) — a MESMA
    ordem de tupla que edgetelemetry.serie_saneada usa, para os dois leitores
    serem intercambiáveis na cabeça de quem escreve o consumidor.
    """
    if caminho is None:
        caminho = os.path.join(root, CAMINHO_RELATIVO)
    por_chave: dict[tuple, dict] = {}
    precedencia_da_chave: dict[tuple, int] = {}
    descartadas: list[dict] = []
    if not os.path.isfile(caminho):
        return por_chave, descartadas
    with open(caminho, encoding="utf-8") as handle:
        for numero, bruto in enumerate(handle, start=1):
            bruto = bruto.strip()
            if not bruto:
                continue
            try:
                registro = json.loads(bruto)
            except json.JSONDecodeError:
                descartadas.append({"line": numero, "line_sha256": sha_linha(bruto),
                                    "reasons": ["JSON inválido"]})
                continue
            motivos = avaliar_linha(registro)
            if motivos:
                descartadas.append({
                    "line": numero,
                    "line_sha256": sha_linha(bruto),
                    "date": registro.get("date"),
                    "crawler": registro.get("crawler"),
                    "reasons": motivos,
                })
                continue
            chave = (registro.get("date"), registro.get("crawler"))
            peso = PRECEDENCIA_SCHEMA.get(registro.get("schema_version"), 0)
            anterior = precedencia_da_chave.get(chave)
            if anterior is not None and peso < anterior:
                # v1 chegando depois de uma v2 já lida: a v1 conta por string de
                # User-Agent e é a leitura desmentida. Não é descarte por linha
                # inválida, é precedência — por isso não entra em `descartadas`,
                # que existe para sinalizar DADO ERRADO.
                continue
            por_chave[chave] = registro
            precedencia_da_chave[chave] = peso
    return por_chave, descartadas


def por_crawler(root: str, caminho: str | None = None):
    """Reagrupa a série saneada em crawler -> lista de registros por data,
    ordenada da mais antiga para a mais recente."""
    saneada, _ = serie_saneada(root, caminho)
    agrupado: dict[str, list[dict]] = {}
    for (data, crawler), registro in saneada.items():
        agrupado.setdefault(crawler, []).append(registro)
    for crawler in agrupado:
        agrupado[crawler].sort(key=lambda r: r.get("date") or "")
    return agrupado


def _resumo(root: str) -> dict:
    saneada, descartadas = serie_saneada(root)
    caminho = os.path.join(root, CAMINHO_RELATIVO)
    linhas = 0
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as handle:
            linhas = sum(1 for linha in handle if linha.strip())
    agrupado = {}
    for (data, crawler) in saneada:
        agrupado.setdefault(crawler, []).append(data)
    return {
        "arquivo": CAMINHO_RELATIVO,
        "linhas_no_arquivo": linhas,
        "chaves_saneadas": len(saneada),
        "linhas_descartadas": len(descartadas),
        "linhas_colapsadas_por_dedup": linhas - len(saneada) - len(descartadas),
        "crawlers": {c: len(d) for c, d in sorted(agrupado.items())},
        "descartadas": descartadas[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raiz", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    resumo = _resumo(args.raiz)
    if args.json:
        print(json.dumps(resumo, ensure_ascii=False, indent=1))
        return 0
    print(f"{resumo['arquivo']}: {resumo['linhas_no_arquivo']} linhas no disco")
    print(f"  chaves (date, crawler) saneadas : {resumo['chaves_saneadas']}")
    print(f"  linhas colapsadas por dedup     : {resumo['linhas_colapsadas_por_dedup']}")
    print(f"  linhas descartadas (impossíveis): {resumo['linhas_descartadas']}")
    print("  dias por crawler:")
    for crawler, dias in resumo["crawlers"].items():
        print(f"    {crawler:<28} {dias}")
    for descartada in resumo["descartadas"]:
        print(f"  ! linha {descartada['line']} ({descartada.get('crawler')}/{descartada.get('date')}): "
              + "; ".join(descartada["reasons"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
