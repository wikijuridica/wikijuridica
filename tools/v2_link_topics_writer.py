#!/usr/bin/env python3
"""v2_link_topics_writer — a máquina de escrita de `internal_link_topics`.

POR QUE ESTE MÓDULO EXISTE. Em 2026-08-12 nasceu
`generate-v2-link-topics-enrich-20260812` com um contrato de escrita caro de
acertar: lease de época do estoque canônico, lock exclusivo próprio, CAS pelo
sha256 da LINHA viva, substituição CIRÚRGICA do array (as demais chaves
preservadas byte a byte, porque o acervo mistura formas de serialização dentro
da mesma linha), escrita atômica com fsync do arquivo e do diretório,
idempotência e preservação do estado anterior antes de qualquer escrita.

Em 2026-08-29 a frente da malha precisou de um SEGUNDO gerador do mesmo tipo
(pontes cross-área). Copiar essas trezentas linhas seria criar o segundo lugar
para divergir num código cuja falha silenciosa é corromper o estoque canônico —
exatamente o que este repositório proíbe. A máquina foi extraída para cá, com um
teste próprio (`tools/test_v2_link_topics_writer.py`, alcançado pela descoberta
automática do `tools/run-qualidade-diaria`), e os dois geradores passaram a
importá-la. O comportamento não mudou: a extração é textual.

O QUE ESTE MÓDULO NÃO FAZ, de propósito: ele não decide NADA. Qual par entra,
por que ele é verdadeiro e qual trecho o sustenta é decisão jurídico-editorial de
quem monta o `.data.json`. Aqui só se verifica e se escreve.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path

CHAVE_TOPICOS = '"internal_link_topics"'


@dataclass(frozen=True)
class Destinos:
    """Os caminhos que distinguem um gerador do outro.

    root      raiz do repositório
    lock      lock exclusivo DESTE gerador (não o do estoque canônico)
    pages     diretório dos shards do estoque v2
    backup    onde o estado anterior de cada linha tocada é preservado
    evidencia o JSONL auditável do que foi escrito e por quê
    gerador   nome do arquivo do gerador, gravado na evidência
    """

    root: Path
    lock: Path
    pages: Path
    backup: Path
    evidencia: Path
    gerador: str


@contextmanager
def exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        os.fchmod(fd, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _limites_do_array(linha: str, inicio: int) -> tuple[int, int]:
    """Devolve (abre, fecha_exclusivo) do array JSON que começa em/depois de inicio.

    Varre respeitando string e escape — um `]` dentro de um tópico não pode
    fechar o array. Só trata array, que é o que este campo sempre é.
    """
    abre = linha.index("[", inicio)
    dentro_de_string = False
    escapado = False
    for posicao in range(abre, len(linha)):
        char = linha[posicao]
        if dentro_de_string:
            if escapado:
                escapado = False
            elif char == "\\":
                escapado = True
            elif char == '"':
                dentro_de_string = False
            continue
        if char == '"':
            dentro_de_string = True
        elif char == "]":
            return abre, posicao + 1
    raise ValueError("array de internal_link_topics não fecha")


def _forma_de_outro_array(linha: str, pular_em: int) -> tuple[str, str] | None:
    """Descobre a forma de serialização olhando outro array da MESMA linha.

    Devolve a tupla `separators` do primeiro array que round-trip identifica sem
    ambiguidade, ignorando o que começa em `pular_em` (o que está sendo
    substituído). None quando nenhum decide.
    """
    posicao = 0
    while True:
        posicao = linha.find("[", posicao)
        if posicao < 0:
            return None
        if posicao != pular_em:
            try:
                abre, fecha = _limites_do_array(linha, posicao)
                valor = json.loads(linha[abre:fecha])
            except (ValueError, json.JSONDecodeError):
                posicao += 1
                continue
            texto = linha[abre:fecha]
            casam = [c for c in ((", ", ": "), (",", ":"))
                     if json.dumps(valor, ensure_ascii=False, separators=c) == texto]
            if len(casam) == 1:
                return casam[0]
        posicao += 1


def splice_topicos(linha_viva: str, topicos: list[str]) -> str:
    """Reescreve SÓ o array internal_link_topics, preservando o resto byte a byte.

    O acervo mistura formas de serialização DENTRO da mesma linha (o nível de
    cima com ", " e os objetos de official_sources compactos), então reemitir o
    registro inteiro mudaria bytes de campos que este gerador não toca. A
    substituição cirúrgica mantém a diferença restrita ao campo que mudou, e a
    forma local do array é descoberta pelo round-trip do array ORIGINAL.
    """
    posicao = linha_viva.index(CHAVE_TOPICOS)
    depois_da_chave = posicao + len(CHAVE_TOPICOS)
    abre, fecha = _limites_do_array(linha_viva, depois_da_chave)
    original_txt = linha_viva[abre:fecha]
    original = json.loads(original_txt)

    candidatos = [c for c in ((", ", ": "), (",", ":"))
                  if json.dumps(original, ensure_ascii=False, separators=c) == original_txt]
    if len(candidatos) == 1:
        separadores = candidatos[0]
    elif candidatos:
        # ROUND-TRIP AMBÍGUO, e isto NÃO é caso de borda raro: `[]` e `["um"]`
        # serializam igual nas duas formas, porque não há vírgula nenhuma para
        # separar. Até 2026-08-29 o desempate era a ORDEM da lista de candidatos,
        # então toda página cujo array tinha zero ou um tópico recebia a forma
        # ESPAÇADA — mesmo estando numa linha compacta. O valor saía certo e a
        # forma saía errada, que é exatamente o que este splice existe para não
        # fazer. O defeito veio junto da máquina, de 2026-08-12.
        #
        # O desempate certo é olhar OUTRO array da mesma linha que não seja
        # ambíguo, e herdar a forma dele. O separador da chave (": " contra ":")
        # parece um atalho e ERRA: medido em 2026-08-29, 16 linhas de
        # imobiliario-p10.jsonl trazem ": " depois da chave e vírgula COMPACTA
        # dentro do array, porque o acervo mistura as duas formas na mesma
        # linha. Ele fica como último recurso, para a linha em que nenhum outro
        # array decide.
        separadores = _forma_de_outro_array(linha_viva, abre)
        if separadores is None:
            entre = linha_viva[depois_da_chave:abre]
            separadores = (", ", ": ") if entre.startswith(": ") else (",", ":")
    else:
        print("  aviso: forma do array não reconhecida; usando a padrão",
              file=sys.stderr)
        separadores = (", ", ": ")
    novo = json.dumps(topicos, ensure_ascii=False, separators=separadores)
    return linha_viva[:abre] + novo + linha_viva[fecha:]


def texto_visivel(record: dict) -> str:
    """Todo texto redigido da página, para conferir o trecho que justifica."""
    partes = [record.get("opening") or ""]
    for section in record.get("sections") or []:
        partes.append(section.get("heading") or "")
        partes.append(section.get("text") or "")
    for item in record.get("faq") or []:
        partes.append(item.get("q") or "")
        partes.append(item.get("a") or "")
    return "\n".join(partes)


def indexar_acervo(destinos: Destinos) -> tuple[dict[str, str], dict[str, dict]]:
    """intent_id -> shard e intent_id -> registro, lidos do acervo VIVO.

    O shard vem do disco, nunca do arquivo de dados: se um agente errar o
    caminho, a escrita iria para o lugar errado ou não seria encontrada.
    """
    onde: dict[str, str] = {}
    registros: dict[str, dict] = {}
    for shard in sorted(destinos.pages.glob("*.jsonl")):
        for linha in shard.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            registro = json.loads(linha)
            intent = registro.get("intent_id")
            if intent and intent not in onde:
                onde[intent] = os.path.relpath(shard, destinos.root)
                registros[intent] = registro
    return onde, registros


def preflight(topicos: list[dict], onde: dict[str, str],
              registros: dict[str, dict]) -> dict[str, list[dict]]:
    """Recusa o lote inteiro se QUALQUER par não se sustentar.

    Falha fechada de propósito: escrever metade de um lote no estoque canônico
    deixa o acervo num estado que ninguém sabe descrever depois.
    """
    problemas: list[str] = []
    por_shard: dict[str, list[dict]] = {}
    vistos: set[tuple[str, str]] = set()
    for item in topicos:
        pagina = item.get("intent_id") or ""
        topico = item.get("topico") or ""
        rotulo = f"{pagina} += {topico}"
        if not pagina or not topico:
            problemas.append(f"{rotulo}: registro sem página ou sem tópico")
            continue
        if pagina not in onde:
            problemas.append(f"{rotulo}: página não existe no acervo vivo")
            continue
        # O tópico só vale +100 se for o intent_id EXATO de uma página do acervo.
        if topico not in onde:
            problemas.append(f"{rotulo}: o tópico não é intent_id de página do acervo")
            continue
        if topico == pagina:
            problemas.append(f"{rotulo}: auto-referência")
        if item.get("veredito") != "verdadeiro":
            problemas.append(f"{rotulo}: veredito não é 'verdadeiro'")
        if not item.get("porque"):
            problemas.append(f"{rotulo}: sem razão declarada")
        trecho = item.get("trecho_justificativa") or ""
        if len(trecho) < 40:
            problemas.append(f"{rotulo}: trecho de justificativa ausente ou curto demais")
        elif trecho not in texto_visivel(registros[pagina]):
            problemas.append(
                f"{rotulo}: o trecho que justifica NÃO está no texto vivo da página")
        chave = (pagina, topico)
        if chave in vistos:
            problemas.append(f"{rotulo}: par repetido no arquivo de dados")
        vistos.add(chave)
        por_shard.setdefault(onde[pagina], []).append(item)
    if problemas:
        for problema in problemas:
            print(f"PREFLIGHT FALHOU: {problema}", file=sys.stderr)
        raise SystemExit(1)
    print(f"preflight ok: {len(topicos)} tópico(s) em "
          f"{len({t['intent_id'] for t in topicos})} página(s), "
          f"{len(por_shard)} shard(s); todo tópico resolve para página real e "
          f"todo trecho confere com o texto vivo")
    return por_shard


def preservar(destinos: Destinos, shard_rel: str,
              linhas_originais: dict[int, str]) -> Path:
    """Guarda a linha ANTERIOR de todo registro que será tocado.

    Página escrita nunca é descartada: antes de qualquer escrita, o estado atual
    vai para .agents/runtime/ datado, com o número da linha, para que a versão
    anterior seja recuperável byte a byte.
    """
    destino = destinos.backup / shard_rel.replace("/", "_")
    payload = "".join(f"{numero}\t{linha}\n"
                      for numero, linha in sorted(linhas_originais.items()))
    atomic_write(destino, payload.encode("utf-8"))
    return destino


def aplicar(destinos: Destinos, shard_rel: str, itens: list[dict],
            dry_run: bool) -> tuple[int, int]:
    path = destinos.root / shard_rel
    bruto = path.read_bytes().decode("utf-8")
    linhas = bruto.split("\n")
    fim_com_newline = bool(linhas) and linhas[-1] == ""
    if fim_com_newline:
        linhas = linhas[:-1]

    por_intent: dict[str, list[dict]] = {}
    for item in itens:
        por_intent.setdefault(item["intent_id"], []).append(item)

    saida: list[str] = []
    originais: dict[int, str] = {}
    alterados = 0
    ja_feitos = 0
    for numero, raw in enumerate(linhas, 1):
        if not raw.strip():
            raise SystemExit(f"{shard_rel}: linha em branco {numero}")
        intent = json.loads(raw).get("intent_id")
        if intent not in por_intent:
            saida.append(raw)
            continue

        registro = json.loads(raw)
        digest_antes = hashlib.sha256(raw.strip().encode("utf-8")).hexdigest()
        topicos = list(registro.get("internal_link_topics") or [])
        acrescentados = 0
        for item in por_intent[intent]:
            topico = item["topico"]
            if topico in topicos:
                ja_feitos += 1
                continue
            topicos.append(topico)
            acrescentados += 1
            print(f"  {intent}: += {topico}")

        if not acrescentados:
            saida.append(raw)
            continue

        nova = splice_topicos(raw, topicos)
        # Conferência de valor: o registro reemitido tem de diferir do vivo em
        # NADA além da lista de tópicos. Splice textual é cirúrgico, e é
        # justamente por isso que precisa de prova.
        conferido = json.loads(nova)
        esperado = dict(registro)
        esperado["internal_link_topics"] = topicos
        if conferido != esperado:
            raise SystemExit(
                f"{shard_rel}:{numero} ({intent}): a substituição cirúrgica "
                f"alterou algo além de internal_link_topics — abortado.")
        atual = hashlib.sha256(
            path.read_bytes().decode("utf-8").split("\n")[numero - 1]
            .strip().encode("utf-8")).hexdigest()
        if atual != digest_antes:
            raise SystemExit(
                f"CAS DE LINHA FALHOU em {shard_rel}:{numero} ({intent}): "
                f"outra frente tocou este registro durante a execução.")
        originais[numero] = raw
        saida.append(nova)
        alterados += 1

    if alterados and not dry_run:
        destino = preservar(destinos, shard_rel, originais)
        print(f"    estado anterior preservado em "
              f"{os.path.relpath(destino, destinos.root)}")
        payload = "\n".join(saida) + ("\n" if fim_com_newline else "")
        atomic_write(path, payload.encode("utf-8"))
    return alterados, ja_feitos


def escrever_evidencia(destinos: Destinos, topicos: list[dict],
                       onde: dict[str, str]) -> None:
    """Evidência auditável: um registro por tópico, determinística e ordenada."""
    linhas: list[str] = []
    for item in sorted(topicos, key=lambda t: (t["intent_id"], t["topico"])):
        linhas.append(json.dumps({
            "gerador": destinos.gerador,
            "gerado_em": date.today().isoformat(),
            "intent_id": item["intent_id"],
            "shard": onde.get(item["intent_id"], ""),
            "topico_acrescentado": item["topico"],
            "topico_destino_shard": onde.get(item["topico"], ""),
            "motivo_da_cauda": item.get("motivo_da_cauda", ""),
            "porque": item.get("porque", ""),
            "trecho_justificativa": item.get("trecho_justificativa", ""),
            "campo_do_trecho": item.get("campo_do_trecho", ""),
            "veredito": item.get("veredito", ""),
            "verificado_por": item.get("verificado_por", ""),
            "texto_anterior_preservado_em":
                os.path.relpath(destinos.backup, destinos.root) + "/",
        }, ensure_ascii=False))
    atomic_write(destinos.evidencia, ("\n".join(linhas) + "\n").encode("utf-8"))
    print(f"evidência: {len(linhas)} registro(s) em "
          f"{os.path.relpath(destinos.evidencia, destinos.root)}")
