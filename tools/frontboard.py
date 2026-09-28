"""frontboard — leitor canônico de `.agents/runtime/p0_frontboard.jsonl`.

POR QUE UM MÓDULO, E NÃO UMA CÓPIA POR FERRAMENTA: em 2026-08-26, ao preparar a
tasklist do PLANO_SUPERFICIE_BOTS_20260826, os DOIS consumidores do frontboard
foram medidos e os DOIS estavam cegos — cada um por um motivo diferente, e
nenhum dos dois falhava em voz alta.

  1. `tools/p0-next` — o "dispatcher de autonomia", que existe para o engenheiro
     "NUNCA ficar ocioso" — filtra `status` por `available` / `running` /
     `blocked`. O board NÃO usa esse vocabulário desde que passou a gravar
     `queued` / `in_progress` / `near_done` / `done` / `closed` / `open` /
     `superseded`. Medido: **144 linhas no board, ZERO casadas** — ele imprime
     "Nada AVAILABLE" com 29 tarefas livres e manda o agente entrante PARAR.
     O `wiki-brief` já documentava esse defeito em 5 linhas de comentário e
     pedia, por escrito, que alguém o consertasse.

  2. `tools/wiki-brief` — estoura `TypeError: '<' not supported between
     instances of 'str' and 'int'` ao ordenar, porque `priority` mistura
     inteiro e texto no mesmo arquivo. Medido no board de 144 linhas:
     **`int` em 24 tarefas livres e `str` em 11**; entre as `in_progress`,
     15 contra 3. O `2>/dev/null` engole o traceback e o brief imprime um
     `BOARD ?` mudo — as duas linhas mais úteis dele (`BOARD ATIVA` e
     `BOARD LIVRE`) simplesmente somem, e ninguém é avisado.

O código dos dois estava certo. O **dado** é que é heterogêneo, porque o board
foi escrito por muitas sessões ao longo de meses, cada uma com o vocabulário do
seu dia. É a mesma família do `edgetelemetry`: o critério de leitura mora num
lugar só, senão a próxima ferramenta reintroduz a divergência.

────────────────────────────────────────────────────────────────────────────
COMO OS MAPAS FORAM DERIVADOS (não são convenção inventada)

Ambos saem do vocabulário REALMENTE presente no arquivo, medido em 2026-08-26:

    status  : done=61 queued=29 open=23 in_progress=18 near_done=6
              closed=6 superseded=1
    priority: 'alta'=38 1=30 'media'=18 0=12 2=12 'critica'=10 '1'=9 '0'=8
              'baixa'=3 3=2 '2'=2

`aberta` vs `fechada` sai da semântica que os próprios consumidores já
aplicavam: o `wiki-brief` trata `queued`/`available`/`near_done` como trabalho
que se pode PEGAR e `in_progress` como trabalho EM VOO, e ordena
`near_done` DEPOIS das livres — com o motivo escrito no arquivo: "sem esta
chave, um near_done p0 rouba o topo de 19 queued e manda o agente entrante
pegar tarefa em andamento". Essa ordenação é preservada aqui, não reinventada.

O mapa de prioridade textual→numérica segue a escala que o board já usa nos
dois formatos: crítica é o topo (0) e baixa é o fim (3). Nenhuma tarefa muda de
posição relativa por causa da normalização — ela só deixa de estourar o sort.

POR QUE NÃO REESCREVER AS 144 LINHAS HISTÓRICAS: porque o defeito é de LEITURA,
e reescrever dado histórico para agradar um leitor é a inversão errada. As
linhas antigas continuam como foram gravadas; o gerador novo escreve no formato
numérico, e este módulo entende os dois para sempre.

────────────────────────────────────────────────────────────────────────────
REMEDIÇÃO 2026-09-05 — o board cresceu de 144 para 559 linhas e o vocabulário
cresceu junto. `test_frontboard.py` pegou 112 status REAIS fora do mapa acima
(`desconhecidas`). Medido por `status`, board inteiro:

    done=348 todo=87 queued=30 open=27 in_progress=21 superseded=9 parcial=9
    aberto=9 near_done=6 closed=6 fechado=3 derrubado=2 refutado=1 bloqueado=1

Sete rótulos novos, todos com significado auditável na origem — nenhum é lixo:

  - `todo` (87) é o vocabulário oficial da campanha `caca-bugs-20260829`
    (`docs/goal/PLANO_CACA_BUGS_20260829.md` §4: `status: "todo|doing|done|
    refutado"`, contado por lá via `grep -c '"status": *"todo"'`) — mesmo
    sentido de `queued`/`open`: trabalho livre. `aberto` é o mesmo rótulo em
    português.
  - `refutado` é, pelo mesmo documento, "status de sucesso: a suspeita foi
    investigada e derrubada por medição" — terminal, mesmo bucket de `done`.
    `fechado` é `closed` em português.
  - `derrubado` (2 ocorrências, amostradas em `bots-t4.6` e `bots-t11.1`) marca
    tarefa avaliada e descartada por medição — as duas trazem nota "Estado
    TERMINAL para não reabrir como pendência": mesmo bucket de `refutado`.
  - `bloqueado` é `blocked` em português (visto em `caca-BUG-112`, bloqueada por
    dependência real, mesma semântica da entrada `blocked` já mapeada).
  - `parcial` (9) não está no vocabulário de 4 valores do plano — é extensão ad
    hoc da campanha. Amostradas as 9: 8 têm `commit` gravado (investigação já
    encerrada com correção aplicada, resultado só não é 100% limpo) e a exceção
    (`caca-BUG-044`) documenta medição completa e vigiada por gate próprio, com
    o reparo do gerador tratado como tarefa nova — nenhuma das 9 é "trabalho
    esperando ser pego" por este leitor. Mapeada para `fechada`.

Nenhuma linha das 559 foi tocada; o remédio é só neste dicionário, pela mesma
regra do parágrafo anterior.
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterable

CAMINHO_PADRAO = os.path.join(
    os.environ.get("WIKI_ROOT", "/opt/wiki"),
    ".agents/runtime/p0_frontboard.jsonl",
)

# Sinônimos medidos no arquivo. `available` e `running` NÃO aparecem no board
# de hoje, mas são o vocabulário que o `p0-next` esperava — ficam aqui para que
# um board antigo (ou um consumidor antigo) continue sendo entendido.
_STATUS_CANONICO = {
    "queued": "livre",
    "available": "livre",
    "open": "livre",
    "todo": "livre",
    "aberto": "livre",
    "in_progress": "em_voo",
    "running": "em_voo",
    "near_done": "quase",
    "blocked": "bloqueada",
    "bloqueado": "bloqueada",
    "done": "fechada",
    "closed": "fechada",
    "fechado": "fechada",
    "superseded": "fechada",
    "refutado": "fechada",
    "derrubado": "fechada",
    "parcial": "fechada",
}

_PRIORIDADE_TEXTO = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}

# Ordem de exibição, preservando a decisão já tomada no `wiki-brief`: trabalho
# em voo primeiro (para ser integrado), depois o que se pode pegar, e o que já
# fechou por último.
ORDEM_STATUS = ["em_voo", "livre", "quase", "bloqueada", "fechada"]

PRIORIDADE_AUSENTE = 99


def normaliza_status(valor: Any) -> str:
    """Devolve o status canônico. Status desconhecido vira `desconhecida` — nunca
    é silenciosamente tratado como fechada, senão trabalho real some do board."""
    if not isinstance(valor, str):
        return "desconhecida"
    return _STATUS_CANONICO.get(valor.strip().lower(), "desconhecida")


def normaliza_prioridade(valor: Any) -> int:
    """Devolve prioridade inteira (0 = mais urgente). Aceita int, str numérica e
    os rótulos em português que o board usa. Valor irreconhecível vira
    PRIORIDADE_AUSENTE — vai para o fim da fila, mas continua visível."""
    if isinstance(valor, bool):
        return PRIORIDADE_AUSENTE
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str):
        v = valor.strip().lower()
        if v.isdigit():
            return int(v)
        if v in _PRIORIDADE_TEXTO:
            return _PRIORIDADE_TEXTO[v]
    return PRIORIDADE_AUSENTE


def carrega(caminho: str = CAMINHO_PADRAO) -> list[dict]:
    """Lê o frontboard inteiro, acrescentando a cada linha os campos derivados
    `_status`, `_prioridade` e `_ordem` (posição no arquivo, para desempate
    estável). Linha corrompida é PULADA e contada em `_erros_de_parse` na
    primeira linha devolvida — ausência de linha nunca vira ausência de fato."""
    linhas: list[dict] = []
    erros = 0
    try:
        arquivo = open(caminho, encoding="utf-8")
    except FileNotFoundError:
        return []
    with arquivo:
        for i, bruta in enumerate(arquivo):
            bruta = bruta.strip()
            if not bruta:
                continue
            try:
                registro = json.loads(bruta)
            except Exception:
                erros += 1
                continue
            if not isinstance(registro, dict):
                erros += 1
                continue
            registro["_status"] = normaliza_status(registro.get("status"))
            registro["_prioridade"] = normaliza_prioridade(registro.get("priority"))
            registro["_ordem"] = i
            linhas.append(registro)
    if linhas:
        linhas[0]["_erros_de_parse"] = erros
    return linhas


def livres(linhas: Iterable[dict]) -> list[dict]:
    """Tarefas que um agente entrante pode PEGAR, na ordem em que deve pegá-las.
    `quase` (near_done) vem depois de `livre` de propósito — é trabalho em voo."""
    candidatas = [r for r in linhas if r.get("_status") in ("livre", "quase")]
    candidatas.sort(
        key=lambda r: (
            0 if r["_status"] == "livre" else 1,
            r["_prioridade"],
            r["_ordem"],
        )
    )
    return candidatas


def por_status(linhas: Iterable[dict], status: str) -> list[dict]:
    """Tarefas de um status canônico, ordenadas por prioridade e posição."""
    selecionadas = [r for r in linhas if r.get("_status") == status]
    selecionadas.sort(key=lambda r: (r["_prioridade"], r["_ordem"]))
    return selecionadas


def contagem(linhas: Iterable[dict]) -> dict[str, int]:
    """Contagem por status canônico, na ordem de exibição."""
    bruto: dict[str, int] = {}
    for r in linhas:
        s = r.get("_status", "desconhecida")
        bruto[s] = bruto.get(s, 0) + 1
    ordenado = {k: bruto[k] for k in ORDEM_STATUS if k in bruto}
    for k in bruto:
        if k not in ordenado:
            ordenado[k] = bruto[k]
    return ordenado


def dono(registro: dict) -> str:
    """Quem abriu ou está com a tarefa. O `p0-next` procurava `owner`, campo que
    o board NUNCA teve — ele grava `opened_by` (72 linhas) e `closed_by` (6)."""
    for chave in ("owner", "opened_by", "closed_by"):
        valor = registro.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return "?"
