"""Testes do índice incremental e da reautenticação paralela do epoch.

A carga do contrato semântico deixou de reler e redecodificar o estoque inteiro
a cada lote (índice persistido por carimbo de stat) e o epoch deixou de ser
reautenticado entrada a entrada (descritor de diretório fixado + fatias em
threads). Estes testes provam que nenhuma das duas mudanças afrouxou o veredito:

* o caminho incremental produz exatamente o mesmo contrato e o mesmo epoch que o
  caminho longo;
* o índice quente NÃO consegue esconder um intent duplicado em outro shard, que
  é a razão de o epoch v3 cobrir o estoque inteiro;
* a reautenticação do epoch continua pegando byte alterado, arquivo removido,
  ausência que reapareceu e hardlink extra, com a mesma exceção e a mesma
  mensagem do laço sequencial;
* os erros estruturais do epoch continuam idênticos, inclusive na ordem em que
  vencem uma divergência posterior.

Uso: python3 tools/test_v2_review_queue_incremental_epoch.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools import generate_v2_review_queue as producer  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
STOCK_REL = "data/editorial/v2_pages"
CONTRACT_REL = producer._WRITING_SEMANTIC_CONTRACT_REL_PATH
SANDBOX_TREES = (
    "data/editorial/v2_pages",
    "data/editorial/portfolio_v2",
    "data/editorial/v2_semantic_superseded",
    "data/editorial/v2_superseded",
)
SANDBOX_FILES = (
    CONTRACT_REL,
    "data/editorial/v2_source_hint_catalog.json",
)

_failures: list[str] = []
_checks = 0


def check(condition: bool, label: str) -> None:
    global _checks
    _checks += 1
    if not condition:
        _failures.append(label)
        print(f"  REPROVOU: {label}")
    else:
        print(f"  ok: {label}")


def raises(callable_object) -> BaseException | None:
    try:
        callable_object()
    except BaseException as error:  # noqa: BLE001 — o veredito é a exceção
        return error
    return None


def build_sandbox(destination: pathlib.Path) -> pathlib.Path:
    for tree in SANDBOX_TREES:
        source = REPO / tree
        if source.is_dir():
            shutil.copytree(
                source, destination / tree,
                ignore=shutil.ignore_patterns(".*"))
    for relative in SANDBOX_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)
    return destination


def stock_shards(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted((root / STOCK_REL).glob("*.jsonl"))


def test_incremental_matches_long_path(root: pathlib.Path) -> None:
    print("\n[1] índice frio e índice quente devolvem o mesmo contrato")
    cold = producer.load_writing_semantic_contract(root)
    warm = producer.load_writing_semantic_contract(root)
    check(dict(cold.dependency_sha256) == dict(warm.dependency_sha256),
          "dependency_sha256 idêntico entre carga fria e quente")
    check(cold.digest == warm.digest, "digest do contrato idêntico")
    check(set(cold.unresolved_intents) == set(warm.unresolved_intents),
          "intents não resolvidos idênticos")
    shards = stock_shards(root)
    check(len(cold.dependency_sha256) >= len(shards),
          f"todos os {len(shards)} shards de estoque entram no CAS "
          f"({len(cold.dependency_sha256)} dependências)")
    for shard in shards:
        relative = shard.relative_to(root).as_posix()
        check_once = relative in cold.dependency_sha256
        if not check_once:
            check(False, f"shard fora do CAS: {relative}")
            return
    check(True, "nenhum shard de estoque ficou fora do dependency CAS")


def test_warm_index_cannot_hide_duplicate(root: pathlib.Path) -> None:
    print("\n[2] índice quente NÃO esconde intent duplicado em outro shard")
    contract = producer.load_writing_semantic_contract(root)
    contract_value = json.loads((root / CONTRACT_REL).read_text("utf-8"))
    candidates = contract_value.get("forward_candidates", [])
    if not candidates:
        check(False, "contrato sem candidato forward para exercitar")
        return
    intent_id = candidates[0]["intent_id"]
    owner_rel = candidates[0]["current_source_rel_path"]
    owner = root / owner_rel
    duplicated_line = next(
        line for line in owner.read_bytes().split(b"\n")
        if line and json.loads(line).get("intent_id") == intent_id)

    victims = [
        shard for shard in stock_shards(root)
        if shard.relative_to(root).as_posix() != owner_rel
    ]
    victim = victims[0]
    original = victim.read_bytes()
    try:
        victim.write_bytes(original + duplicated_line + b"\n")
        error = raises(lambda: producer.load_writing_semantic_contract(root))
        check(isinstance(error, ValueError),
              f"cópia do intent em outro shard aborta a carga ({type(error).__name__})")
        check(error is not None and
              "globalmente exato e único" in str(error),
              f"veredito é o de unicidade global: {str(error)[:90]}")
    finally:
        victim.write_bytes(original)
    restored = producer.load_writing_semantic_contract(root)
    check(dict(restored.dependency_sha256) == dict(contract.dependency_sha256),
          "contrato volta ao estado original após restaurar o shard")


def test_epoch_catches_mutation(root: pathlib.Path) -> None:
    print("\n[3] reautenticação do epoch pega mutação, remoção e reaparecimento")
    contract = producer.load_writing_semantic_contract(root)
    epoch = {
        root / relative: digest
        for relative, digest in contract.dependency_sha256.items()
    }
    check(raises(lambda: producer._assert_dependency_epoch(epoch)) is None,
          "epoch íntegro passa sem erro")

    victim = stock_shards(root)[len(stock_shards(root)) // 2]
    original = victim.read_bytes()
    try:
        victim.write_bytes(original.replace(b"a", b"A", 1))
        error = raises(lambda: producer._assert_dependency_epoch(epoch))
        check(isinstance(error, producer.CASMismatch),
              f"byte alterado vira CASMismatch ({type(error).__name__})")
        check(error is not None and str(victim) in str(error),
              "mensagem nomeia o arquivo divergente")
    finally:
        victim.write_bytes(original)

    moved = victim.with_suffix(".jsonl.movido")
    try:
        os.rename(victim, moved)
        error = raises(lambda: producer._assert_dependency_epoch(epoch))
        check(isinstance(error, producer.CASMismatch),
              f"dependência removida vira CASMismatch ({type(error).__name__})")
    finally:
        os.rename(moved, victim)

    absent = root / STOCK_REL / "inexistente-para-teste.jsonl"
    absent_epoch = dict(epoch)
    absent_epoch[absent] = None
    check(raises(lambda: producer._assert_dependency_epoch(absent_epoch)) is None,
          "ausência autenticada passa enquanto o arquivo não existe")
    try:
        absent.write_bytes(b'{"intent_id":"teste-aparecido"}\n')
        error = raises(lambda: producer._assert_dependency_epoch(absent_epoch))
        check(isinstance(error, producer.CASMismatch),
              f"ausência que reapareceu vira CASMismatch ({type(error).__name__})")
        check(error is not None and
              "antes ausente apareceu" in str(error),
              f"mensagem é a de ausência violada: {str(error)[:70]}")
    finally:
        absent.unlink(missing_ok=True)

    linked = victim.parent / "hardlink-para-teste.jsonl"
    try:
        os.link(victim, linked)
        error = raises(lambda: producer._assert_dependency_epoch(epoch))
        check(isinstance(error, producer.CASMismatch),
              f"hardlink extra no alvo vira CASMismatch ({type(error).__name__})")
    finally:
        linked.unlink(missing_ok=True)

    check(raises(lambda: producer._assert_dependency_epoch(epoch)) is None,
          "epoch volta a passar depois de tudo restaurado")


def test_epoch_structural_errors(root: pathlib.Path) -> None:
    print("\n[4] erros estruturais do epoch preservados")
    shard = stock_shards(root)[0]
    digest = producer.snapshot_sha256(shard, max_bytes=64 * 1024 * 1024)

    error = raises(lambda: producer._assert_dependency_epoch(
        {shard: "nao-e-hexadecimal"}))
    check(isinstance(error, ValueError) and
          "entrada do epoch de dependências é inválida" in str(error),
          "digest não hexadecimal vira ValueError canônico")

    error = raises(lambda: producer._assert_dependency_epoch({"": digest}))
    check(isinstance(error, ValueError) and
          "entrada do epoch de dependências é inválida" in str(error),
          "path vazio vira ValueError canônico")

    error = raises(lambda: producer._assert_dependency_epoch({1: digest}))
    check(isinstance(error, ValueError) and
          "path do epoch de dependências é inválido" in str(error),
          "path não-fspath vira ValueError canônico")

    error = raises(lambda: producer._assert_dependency_epoch(
        {str(shard): digest, os.path.join(str(shard.parent), ".", shard.name): digest}))
    check(isinstance(error, ValueError) and
          "repete path canônico" in str(error),
          "path canônico repetido vira ValueError canônico")

    error = raises(lambda: producer._assert_dependency_epoch(["não é mapping"]))
    check(isinstance(error, ValueError) and
          "mapping bounded" in str(error), "mapping inválido vira ValueError")

    error = raises(lambda: producer._assert_dependency_epoch(
        {f"/tmp/inexistente-{index}": digest for index in range(50_001)}))
    check(isinstance(error, ValueError) and
          "mapping bounded" in str(error), "epoch acima de 50k vira ValueError")

    check(raises(lambda: producer._assert_dependency_epoch({})) is None,
          "epoch vazio é aceito")
    check(raises(lambda: producer._assert_dependency_epoch(None)) is None,
          "epoch None é aceito")

    # Divergência ANTES do erro estrutural tem de vencer: é o que o laço
    # sequencial fazia ao verificar 0..k-1 antes de alcançar a entrada inválida.
    original = shard.read_bytes()
    try:
        shard.write_bytes(original + b'{"intent_id":"x-divergente"}\n')
        error = raises(lambda: producer._assert_dependency_epoch(
            {str(shard): digest, "": digest}))
        check(isinstance(error, producer.CASMismatch),
              f"divergência anterior vence o erro estrutural posterior "
              f"({type(error).__name__})")
    finally:
        shard.write_bytes(original)

    error = raises(lambda: producer._assert_dependency_epoch(
        {"": digest, str(shard): "0" * 64}))
    check(isinstance(error, ValueError) and
          "entrada do epoch de dependências é inválida" in str(error),
          "erro estrutural anterior vence divergência posterior")


def test_small_epoch_sequential_path(root: pathlib.Path) -> None:
    print("\n[5] epoch pequeno (caminho sequencial) tem o mesmo veredito")
    shards = stock_shards(root)[:5]
    epoch = {
        shard: producer.snapshot_sha256(shard, max_bytes=64 * 1024 * 1024)
        for shard in shards
    }
    check(len(epoch) < producer._EPOCH_PARALLEL_THRESHOLD,
          "epoch abaixo do limiar de paralelismo")
    check(raises(lambda: producer._assert_dependency_epoch(epoch)) is None,
          "epoch pequeno íntegro passa")
    victim = shards[-1]
    original = victim.read_bytes()
    try:
        victim.write_bytes(original + b"\n")
        error = raises(lambda: producer._assert_dependency_epoch(epoch))
        check(isinstance(error, producer.CASMismatch),
              f"epoch pequeno pega mutação ({type(error).__name__})")
    finally:
        victim.write_bytes(original)


def test_sealed_intents_column(root: pathlib.Path) -> None:
    print("\n[6] coluna de intents corrompida é tratada como ausência de cache")
    producer.load_writing_semantic_contract(root)
    index = producer._snapshot_index()
    index.flush()
    connection = index._open()
    if connection is None:
        # WIKI_V2_SNAPSHOT_INDEX=0 desliga o atalho de propósito: sem base, não
        # há selo a corromper e o caminho longo já é o único em uso.
        print("  pulado: índice desligado (WIKI_V2_SNAPSHOT_INDEX=0)")
        return
    shard = stock_shards(root)[0]
    absolute = os.fspath(shard)
    row = connection.execute(
        "SELECT intents FROM file_snapshot WHERE abs_path = ?",
        (absolute,)).fetchone()
    if row is None or row[0] is None:
        check(False, f"shard sem linha de intents no índice: {absolute}")
        return
    seal, _, payload = row[0].partition("\n")
    check(producer._sha256(payload.encode("utf-8")) == seal,
          "coluna de intents guarda selo próprio coerente")

    truncated = payload.split("\n")
    if len(truncated) < 2:
        check(False, "shard com um único intent não exercita o truncamento")
        return
    connection.execute(
        "UPDATE file_snapshot SET intents = ? WHERE abs_path = ?",
        (f"{seal}\n" + "\n".join(truncated[:-1]), absolute))
    lookup = index.lookup(absolute, shard.stat())
    check(lookup is None or lookup[1] is None,
          "lista de intents encolhida é rejeitada pelo selo")
    contract = producer.load_writing_semantic_contract(root)
    check(absolute.replace(f"{root}/", "") in contract.dependency_sha256,
          "shard com selo quebrado volta a ser lido e continua no CAS")
    connection.execute(
        "UPDATE file_snapshot SET intents = ? WHERE abs_path = ?",
        (row[0], absolute))


def main() -> int:
    with tempfile.TemporaryDirectory(
            prefix="v2-epoch-", dir=REPO / ".agents/runtime") as workspace:
        root = build_sandbox(pathlib.Path(workspace))
        print(f"sandbox: {root}")
        print(f"shards de estoque: {len(stock_shards(root))}")
        test_incremental_matches_long_path(root)
        test_warm_index_cannot_hide_duplicate(root)
        test_epoch_catches_mutation(root)
        test_epoch_structural_errors(root)
        test_small_epoch_sequential_path(root)
        test_sealed_intents_column(root)
        # Remove do índice persistido as linhas do sandbox: ele morre agora.
        index = producer._snapshot_index()
        index.flush()
        connection = index._open()
        if connection is not None:
            connection.execute(
                "DELETE FROM file_snapshot WHERE abs_path LIKE ?",
                (f"{workspace}%",))

    print(f"\n{_checks - len(_failures)}/{_checks} verificações passaram")
    if _failures:
        print("REPROVADO:")
        for failure in _failures:
            print(f"  - {failure}")
        return 1
    print("APROVADO: índice incremental e epoch paralelo mantêm o fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
