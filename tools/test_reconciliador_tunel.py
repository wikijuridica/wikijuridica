#!/usr/bin/env python3
"""Guardas do verificador da família `tunel-*` do reconciliador de alertas.

★ O DEFEITO (medido em 2026-09-05)

`check-tunnel-health` resolve a chave que abriu num `elif anterior.get("degradado")`:
só há resolução se a execução ANTERIOR tiver visto degradação. Perdido o estado
do vigia entre o ciclo ruim e o bom, a transição nunca é observada e a chave fica
aberta com o túnel medido saudável no mesmo instante. Medido:

    tunel-uplink   severidade CRÍTICA, aberta desde 2026-09-04T13:33, sem
                   nenhum envio novo desde então, enquanto tunnel_health.jsonl
                   gravava a cada ~35 s `frota_vivas 5, frota_total 5,
                   ha_connections 4, degradado false, problemas []`.

Nenhuma das quatro chaves `tunel-*` constava do mapa de verificadores, então o
reconciliador as classificava como "sem critério" e não as tocava — o mesmo
buraco que `unit-falhou-*` teve em 2026-09-03.

★ O QUE ESTES TESTES TRAVAM

Que o verificador feche por EVIDÊNCIA (série viva, fresca, N amostras boas) e
que ele NÃO feche por ausência de evidência — série morta, série curta, série
degradada. Fechar alerta crítico por fóssil é a fraude que o próprio
reconciliador nasceu para não cometer.
"""
import datetime
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK  ' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


spec = importlib.util.spec_from_loader(
    "reconciliador_alertas",
    importlib.machinery.SourceFileLoader(
        "reconciliador_alertas", str(RAIZ / "tools" / "generate-alertas-reconciliados")),
)
reconciliador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconciliador)


def ciclo(degradado, problemas, minutos_atras):
    instante = (datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(minutes=minutos_atras))
    return {
        "schema_version": "tunnel_health_v1",
        "checked_at": instante.isoformat(),
        "degradado": degradado,
        "problemas": problemas,
        "frota_vivas": 0 if degradado else 5,
        "frota_total": 5,
        "ha_connections": 0 if degradado else 4,
        "ready_connections": 0 if degradado else 4,
    }


def avalia(ciclos, idade_do_arquivo_h=0.0):
    """Roda o verificador contra uma árvore temporária com a série dada."""
    with tempfile.TemporaryDirectory() as diretorio:
        caminho = pathlib.Path(diretorio) / "data" / "ops" / "tunnel_health.jsonl"
        caminho.parent.mkdir(parents=True)
        caminho.write_text("".join(json.dumps(c) + "\n" for c in ciclos), encoding="utf-8")
        if idade_do_arquivo_h:
            quando = datetime.datetime.now().timestamp() - idade_do_arquivo_h * 3600
            os.utime(caminho, (quando, quando))
        original = reconciliador.RAIZ
        reconciliador.RAIZ = diretorio
        try:
            return reconciliador.v_tunel()
        finally:
            reconciliador.RAIZ = original


print("1. FECHA quando a série viva prova a cura")
saudaveis = [ciclo(False, [], m) for m in (3, 2, 1)]
curada, evidencia = avalia(saudaveis)
passo(curada is True, f"3 ciclos saudáveis e frescos fecham a chave: {evidencia[:90]}…")

print("\n2. NÃO fecha o que não está curado")
curada, evidencia = avalia([ciclo(False, [], 3), ciclo(False, [], 2),
                            ciclo(True, ["uplink_fora:sem rota default"], 1)])
passo(curada is False,
      f"o ciclo mais recente degradado mantém a chave aberta ({evidencia[:70]}…)")
curada, _ = avalia([ciclo(True, ["frota_degradada:0_vivas_de_5"], m) for m in (3, 2, 1)])
passo(curada is False, "três ciclos degradados mantêm a chave aberta")

print("\n3. NÃO fecha por ausência de evidência — `None`, nunca `True`")
curada, evidencia = avalia(saudaveis, idade_do_arquivo_h=6)
passo(curada is None,
      f"série PARADA há 6h não conclui (sonda morta não é cura): {evidencia[:80]}…")
curada, evidencia = avalia([ciclo(False, [], 1)])
passo(curada is None, f"série com 1 amostra não conclui: {evidencia}")
curada, evidencia = avalia([])
passo(curada is None, f"série vazia não conclui: {evidencia}")

print("\n4. Meia evidência não fecha: `degradado` e `problemas` têm de concordar")
meia = [ciclo(False, [], 3), ciclo(False, [], 2), ciclo(False, [], 1)]
meia[-1]["problemas"] = ["erros_de_proxy:+12"]
curada, _ = avalia(meia)
passo(curada is False,
      "`degradado: false` com `problemas` não vazio NÃO fecha — as duas leituras "
      "do mesmo fato precisam bater")

print("\n5. As quatro classes do vigia têm verificador, e classe nova também")
for chave in ("tunel-uplink", "tunel-conexoes", "tunel-frota", "tunel-sinais"):
    passo(reconciliador.verificador_de(chave) is reconciliador.v_tunel,
          f"{chave} resolve para v_tunel")
passo(reconciliador.verificador_de("tunel-classe-que-ainda-nao-existe")
      is reconciliador.v_tunel,
      "classe `tunel-*` nova já nasce reconciliável (derivação por prefixo)")
passo(reconciliador.verificador_de("chave-desconhecida") is None,
      "chave fora das famílias conhecidas continua INTOCADA (silêncio por "
      "desconhecimento, nunca fechamento por chute)")

print()
print("FALHOU" if falhou else "todos os passos verdes")
sys.exit(falhou)
