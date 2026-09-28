"""Horizonte de vencimento de TTL da evidência de vida das fontes oficiais.

POR QUE ISTO EXISTE (2026-09-05)
================================
Duas perguntas parecidas têm respostas OPOSTAS neste dado, e confundi-las é o
defeito que este módulo existe para impedir:

  1. "Quantos registros têm `checked_at` velho?"  — hoje: ZERO.
  2. "Quantos registros carregam MEDIÇÃO de verdade, e quando ela vence?" —
     hoje: 399, e a primeira leva vence em 2026-10-04.

A diferença é que `checked_at` NÃO é sempre uma medição. Quando não há tentativa
de metadado válida para a URL, `(*builder).record`
(internal/officialsourceurlliveevidence/evidence.go:1322, campo `CheckedAt` na
linha 1370) grava `checked_at = run_date` — um CARIMBO do dia em que o lote
rodou, com `http_status_code = 0` e status `..._missing_blocked`. Medido em
2026-09-05 sobre os arquivos reais: 6.022 dos 6.421 registros do arquivo
derivado estão nesse estado.

Consequência prática, e é ela que torna este módulo necessário: um detector de
vencimento que apenas subtraia `checked_at` de hoje sobre o arquivo DERIVADO
responde "nada vencido" TODO DIA, para sempre, assim que existir um job diário
regenerando o derivado — porque no dia em que a medição vence, a regeneração já
reescreveu `checked_at` para o run_date de hoje. Era esse o detector do antigo
revalidador de TTL, e é por isso que ele foi aposentado.

A REGRA, DERIVADA DO CÓDIGO E NÃO DE HEURÍSTICA
===============================================
`checked_at` só é medição quando o status do registro é um dos dois que o
produtor usa depois de falar com a rede (`internal/sourceliveevidence`:38-41):

    official_source_live_metadata_attempted_blocked   -> mediu (2xx/3xx/4xx/5xx)
    official_source_live_metadata_failed_blocked      -> mediu (falha de rede)

Nos outros três (`..._attempt_pending_blocked`, `..._skipped_registry_missing_blocked`,
`..._missing_blocked`) `checked_at` é carimbo de lote, e o registro já está
bloqueado por OUTRO motivo, não por TTL.

O PRAZO É O MESMO QUE O GO APLICA
=================================
`checkedAtFreshAt` (internal/officialsourceurlliveevidence/evidence.go:518)
considera fresco enquanto `run_date - checked_at <= ttl dias`. Logo o último dia
fresco é `checked_at + ttl` e o primeiro dia vencido é `checked_at + ttl + 1`.
Este módulo usa exatamente essa aritmética — se ela mudar lá, o teste
tools/test_official_source_url_live_evidence_ttl_horizon.py fica vermelho aqui.

FONTE DE VERDADE
================
`official_source_url_live_metadata_attempts.jsonl` é a fonte; o
`official_source_url_live_evidence.jsonl` é DERIVADO dela
(`GenerateAt` lê o inventário + as tentativas e reescreve o derivado inteiro).
Por isso `divergencias()` compara os dois: campo de medição que aparece no
derivado sem estar na fonte é produtor gravando no arquivo errado — que foi
exatamente o defeito corrigido em 2026-09-05.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Iterable

CAMINHO_ATTEMPTS = "data/source-registry/official_source_url_live_metadata_attempts.jsonl"
CAMINHO_DERIVADO = "data/source-registry/official_source_url_live_evidence.jsonl"

# internal/sourceliveevidence/evidence.go:38-41 e
# internal/officialsourceurlliveevidence/evidence.go:37-41.
STATUS_MEDIDOS = frozenset({
    "official_source_live_metadata_attempted_blocked",
    "official_source_live_metadata_failed_blocked",
})
STATUS_CARIMBO = frozenset({
    "official_source_live_metadata_attempt_pending_blocked",
    "official_source_live_metadata_skipped_registry_missing_blocked",
    "official_source_live_metadata_missing_blocked",
})

# internal/officialsourceurlliveevidence/evidence.go:64-68.
TTL_PADRAO = 60
TTL_MAXIMO = 365

# Os campos que o agregado COPIA da tentativa quando ela está fresca
# (applyMetadataAttempt, internal/officialsourceurlliveevidence/evidence.go:1550).
# São os mesmos que o revalidador Python aposentado reescrevia direto no
# derivado — por isso é neles que a divergência aparece.
CAMPOS_DE_MEDICAO = ("checked_at", "http_status_code", "content_type", "http_method")


def le_jsonl(caminho: str) -> Iterable[dict]:
    """Percorre um JSONL registro a registro, sem carregar o arquivo inteiro."""
    with open(caminho, encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue
            try:
                yield json.loads(linha)
            except json.JSONDecodeError as erro:
                raise ValueError(f"{caminho}:{numero}: JSON inválido ({erro})") from erro


def eh_medicao(registro: dict) -> bool:
    """True quando `checked_at` do registro é medição, não carimbo de lote."""
    return str(registro.get("live_evidence_status") or "") in STATUS_MEDIDOS


def ttl_do_registro(registro: dict) -> int:
    """TTL efetivo, com o mesmo saneamento do Go (fora da faixa => padrão)."""
    bruto = registro.get("freshness_ttl_days")
    try:
        dias = int(bruto)
    except (TypeError, ValueError):
        return TTL_PADRAO
    if dias <= 0 or dias > TTL_MAXIMO:
        return TTL_PADRAO
    return dias


def data_iso(valor) -> datetime.date | None:
    if not valor:
        return None
    try:
        return datetime.date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def primeiro_dia_vencido(registro: dict) -> datetime.date | None:
    """`checked_at + ttl + 1`: o primeiro dia em que o gate reprova o registro.

    None para registro cujo `checked_at` é carimbo — ele não tem relógio de TTL
    correndo, está bloqueado por não ter medição nenhuma.
    """
    if not eh_medicao(registro):
        return None
    checado = data_iso(registro.get("checked_at"))
    if checado is None:
        return None
    return checado + datetime.timedelta(days=ttl_do_registro(registro) + 1)


def horizonte(registros: Iterable[dict], hoje: datetime.date, janela_dias: int = 30) -> dict:
    """Censo do horizonte de TTL de uma camada.

    Devolve contagens por estado e a agenda de vencimento agrupada por data, em
    ordem — a primeira linha da agenda é a resposta a "quando vence o primeiro".
    """
    total = medidos = carimbos = desconhecidos = 0
    vencidos = 0
    agenda: dict[datetime.date, int] = {}
    por_status: dict[str, int] = {}
    for registro in registros:
        total += 1
        status = str(registro.get("live_evidence_status") or "")
        por_status[status] = por_status.get(status, 0) + 1
        if status in STATUS_CARIMBO:
            carimbos += 1
            continue
        if status not in STATUS_MEDIDOS:
            desconhecidos += 1
            continue
        medidos += 1
        dia = primeiro_dia_vencido(registro)
        if dia is None:
            desconhecidos += 1
            continue
        agenda[dia] = agenda.get(dia, 0) + 1
        if dia <= hoje:
            vencidos += 1
    ordenada = sorted(agenda.items())
    limite = hoje + datetime.timedelta(days=janela_dias)
    return {
        "total": total,
        "medidos": medidos,
        "carimbos": carimbos,
        "desconhecidos": desconhecidos,
        "vencidos_hoje": vencidos,
        "primeiro_vencimento": ordenada[0][0].isoformat() if ordenada else None,
        "registros_no_primeiro_vencimento": ordenada[0][1] if ordenada else 0,
        "dias_ate_o_primeiro": (ordenada[0][0] - hoje).days if ordenada else None,
        "vencem_ate": limite.isoformat(),
        "vencem_na_janela": sum(n for dia, n in ordenada if dia <= limite),
        "janela_dias": janela_dias,
        "agenda": [{"primeiro_dia_vencido": dia.isoformat(), "registros": n} for dia, n in ordenada],
        "por_status": dict(sorted(por_status.items())),
    }


# internal/sourceliveevidence/evidence.go:38-41: só o registro com match seguro
# no registro de fontes vira candidato a sonda. O "pulado" nunca será sondado
# enquanto o join de registro não o alcançar — contá-lo como trabalho pendente
# faria o job de recheck relatar fila eterna.
STATUS_PENDENTE = "official_source_live_metadata_attempt_pending_blocked"
STATUS_PULADO = "official_source_live_metadata_skipped_registry_missing_blocked"


def censo_de_sondagem(registros: Iterable[dict], hoje: datetime.date) -> dict:
    """Quantas URLs uma passada `--live` teria de sondar, e por quê.

    A conta segue `reusablePositiveMetadataAttempt`
    (internal/sourceliveevidence/evidence.go:648): só a medição POSITIVA e
    dentro do TTL é reaproveitada sem rede. Vencida, negativa (4xx/5xx) ou
    falha de rede voltam para a fila de sonda; pendente nunca foi medida; e o
    pulado por falta de match seguro não é candidato nenhum.
    """
    pendentes = vencidos = negativos = pulados = frescos = outros = 0
    for registro in registros:
        status = str(registro.get("live_evidence_status") or "")
        if status == STATUS_PULADO:
            pulados += 1
            continue
        if status == STATUS_PENDENTE:
            pendentes += 1
            continue
        if not eh_medicao(registro):
            outros += 1
            continue
        try:
            codigo = int(registro.get("http_status_code") or 0)
        except (TypeError, ValueError):
            codigo = 0
        if codigo <= 0 or codigo >= 400:
            negativos += 1
            continue
        dia = primeiro_dia_vencido(registro)
        if dia is not None and dia <= hoje:
            vencidos += 1
            continue
        frescos += 1
    return {
        "sondaveis": pendentes + vencidos + negativos,
        "pendentes": pendentes,
        "vencidos": vencidos,
        "negativos": negativos,
        "frescos_reaproveitados": frescos,
        "pulados_sem_match": pulados,
        "sem_classificacao": outros,
    }


def indexa_por_hash(registros: Iterable[dict]) -> dict[str, dict]:
    """Indexa uma camada por `source_url_hash`, guardando só o que se compara."""
    indice: dict[str, dict] = {}
    for registro in registros:
        chave = str(registro.get("source_url_hash") or "").strip()
        if not chave:
            continue
        indice[chave] = {
            "live_evidence_status": registro.get("live_evidence_status"),
            "run_date": registro.get("run_date"),
            "freshness_ttl_days": registro.get("freshness_ttl_days"),
            "official_source_url": registro.get("official_source_url"),
            **{campo: registro.get(campo) for campo in CAMPOS_DE_MEDICAO},
        }
    return indice


def divergencias(fonte: dict[str, dict], derivado: dict[str, dict], limite_exemplos: int = 10) -> dict:
    """Acha medição que existe no DERIVADO e não existe na FONTE.

    É a assinatura de um produtor gravando no arquivo errado. O teste é
    assimétrico de propósito: o derivado pode legitimamente NÃO copiar uma
    medição da fonte (quando ela venceu, `GenerateAt` deixa o carimbo e adiciona
    `source_live_metadata_stale_invalid_or_future_for_run_date`); o que ele
    nunca pode é INVENTAR medição que a fonte não tem, nem carregar `checked_at`
    diferente do que a fonte mediu.
    """
    exemplos = []
    contagem = 0
    orfaos = 0
    for chave, registro_derivado in derivado.items():
        registro_fonte = fonte.get(chave)
        if registro_fonte is None:
            orfaos += 1
            continue
        derivado_mediu = str(registro_derivado.get("live_evidence_status") or "") in STATUS_MEDIDOS
        fonte_mediu = str(registro_fonte.get("live_evidence_status") or "") in STATUS_MEDIDOS
        motivo = ""
        if derivado_mediu and not fonte_mediu:
            motivo = "derivado declara medicao que a fonte nao tem"
        elif derivado_mediu and fonte_mediu:
            diferentes = [
                campo for campo in CAMPOS_DE_MEDICAO
                if registro_derivado.get(campo) != registro_fonte.get(campo)
            ]
            if diferentes:
                motivo = "campos de medicao divergentes: " + ", ".join(diferentes)
        if not motivo:
            continue
        contagem += 1
        if len(exemplos) < limite_exemplos:
            exemplos.append({
                "source_url_hash": chave,
                "official_source_url": registro_derivado.get("official_source_url"),
                "motivo": motivo,
                "fonte": {campo: registro_fonte.get(campo) for campo in CAMPOS_DE_MEDICAO},
                "derivado": {campo: registro_derivado.get(campo) for campo in CAMPOS_DE_MEDICAO},
            })
    return {
        "divergentes": contagem,
        "derivados_sem_fonte": orfaos,
        "exemplos": exemplos,
        "comparados": len(derivado),
    }


def hoje_utc() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def caminho_no_repo(raiz: str, relativo: str) -> str:
    return os.path.join(raiz, relativo)
