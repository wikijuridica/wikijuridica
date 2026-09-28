#!/usr/bin/env python3
"""Guardas do check-reorder-nao-invalida-pin-de-shard.

Prova por MUTACAO, executando o gate de verdade (subprocess), nunca por
raciocinio:
  (a) manifesto vazio -> pass, "0 lotes".
  (b) shard no manifesto SEM fila em nenhum ledger -> pass.
  (c) shard no manifesto COM fila viva (pin batendo com o disco, com o
      prefixo "sha256:" que a fila de reescrita usa de verdade) -> REPROVA
      nomeando o shard e o numero de linhas.
  (d) shard no manifesto com pin JA divergente do disco -> pass, mas contado
      a parte em "divida_anterior" (nao entra em "conflitos").
  (e) manifesto com linha malformada (schema_version errado) -> reprova, e
      NAO e confundido com "0 lotes" (ha 1 linha, so que invalida).

Mais uma mutacao de regressao (f): pin da migrations SEM o prefixo
"sha256:" tambem tem de casar com o disco quando vivo — prova que a
normalizacao nao depende do formato de um unico ledger.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-reorder-nao-invalida-pin-de-shard"

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


def registro_lote(slug):
    return json.dumps({
        "schema_version": "v2_writing_mechanical_reorder_v1",
        "slug": slug,
        "target_rel_path": f"data/editorial/v2_pages/{slug}.jsonl",
        "target_sha256": "a" * 64,
        "expected_n": 1,
        "expected_intent_ids": ["intent-dummy"],
        "reason_codes": ["intent_order_mismatch"],
        "preserved_record_sha256": {"intent-dummy": "b" * 64},
        "recovery_item_sha256": "c" * 64,
    })


def roda(manifesto_conteudo, *, shard_slug=None, shard_bytes=b"",
         fila_linhas=(), migracoes_linhas=(), criar_shard=True):
    """Monta um checkout minimo em tempfile e roda o gate real via subprocess.

    fila_linhas: lista de dict pronta para virar linha de v2_rewrite_queue.jsonl
    migracoes_linhas: lista de dict pronta para v2_portfolio_intent_migrations.jsonl
    """
    with tempfile.TemporaryDirectory() as d:
        raiz = pathlib.Path(d)
        (raiz / "data" / "ops").mkdir(parents=True)
        (raiz / "data" / "editorial" / "v2_pages").mkdir(parents=True)
        manifesto = raiz / "data" / "ops" / "writing_mechanical_reorder_todo.jsonl"
        fila = raiz / "data" / "editorial" / "v2_rewrite_queue.jsonl"
        migracoes = raiz / "data" / "editorial" / "v2_portfolio_intent_migrations.jsonl"

        if manifesto_conteudo is not None:
            manifesto.write_text(manifesto_conteudo, encoding="utf-8")
        if shard_slug and criar_shard:
            (raiz / "data" / "editorial" / "v2_pages" / f"{shard_slug}.jsonl").write_bytes(shard_bytes)

        fila.write_text(
            "".join(json.dumps(linha) + "\n" for linha in fila_linhas), encoding="utf-8")
        migracoes.write_text(
            "".join(json.dumps(linha) + "\n" for linha in migracoes_linhas), encoding="utf-8")

        r = subprocess.run(
            [sys.executable, str(GATE), "--manifest", str(manifesto),
             "--rewrite-queue", str(fila), "--migrations", str(migracoes),
             "--root", str(raiz), "--json"],
            capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


def extrai_json(saida):
    linha_json = next(l for l in saida.splitlines() if l.startswith("{"))
    return json.loads(linha_json)


# ---------- (a) manifesto vazio -> pass, "0 lotes"
rc, saida = roda("")
passo(rc == 0, f"manifesto vazio passa (exit {rc})")
passo("0 lotes" in saida, "mensagem explicita de 0 lotes a conferir")

# manifesto AUSENTE (None) tambem tem de passar com "0 lotes"
rc, saida = roda(None)
passo(rc == 0, f"manifesto ausente passa (exit {rc})")
passo("0 lotes" in saida, "mensagem explicita de 0 lotes a conferir (ausente)")


# ---------- (b) shard no manifesto SEM fila em nenhum ledger -> pass
shard_bytes = b'{"intent_id": "intent-dummy"}\n'
disco = hashlib.sha256(shard_bytes).hexdigest()
manifesto = registro_lote("familia-sem-fila") + "\n"
rc, saida = roda(manifesto, shard_slug="familia-sem-fila", shard_bytes=shard_bytes)
passo(rc == 0, f"shard sem fila em nenhum ledger passa (exit {rc}): {saida.strip()[-200:]}")
dados = extrai_json(saida)
passo(dados["conflitos"] == [], "nenhum conflito reportado")
passo(dados["divida_anterior"] == [], "nenhuma divida anterior reportada")


# ---------- (c) shard COM fila viva (pin batendo, com prefixo "sha256:") -> REPROVA
manifesto = registro_lote("familia-viva") + "\n"
fila_linhas = [
    {"source_shard": "data/editorial/v2_pages/familia-viva.jsonl", "source_line": 1,
     "source_shard_sha256": "sha256:" + disco, "source_record_sha256": "sha256:" + "d" * 64,
     "intent_id": "intent-dummy"},
    {"source_shard": "data/editorial/v2_pages/familia-viva.jsonl", "source_line": 2,
     "source_shard_sha256": "sha256:" + disco, "source_record_sha256": "sha256:" + "e" * 64,
     "intent_id": "intent-outro"},
]
rc, saida = roda(manifesto, shard_slug="familia-viva", shard_bytes=shard_bytes,
                  fila_linhas=fila_linhas)
passo(rc != 0, f"shard com fila viva reprova (exit {rc})")
passo("familia-viva" in saida, "a saida nomeia o shard")
dados = extrai_json(saida)
passo(len(dados["conflitos"]) == 1 and dados["conflitos"][0]["linhas_afetadas"] == 2,
      f"JSON nomeia exatamente as 2 linhas vivas: {dados['conflitos']}")
passo("SAIR do manifesto mecanico" in saida, "a mensagem manda o lote SAIR do manifesto (nao drenar a fila)")


# ---------- (d) shard com pin JA divergente do disco -> pass, conta a parte
manifesto = registro_lote("familia-divida") + "\n"
migracoes_linhas = [
    {"target_shard": "familia-divida.jsonl", "source_shard_sha256": "f" * 64,
     "migration_id": "migracao-velha-20260101"},
]
rc, saida = roda(manifesto, shard_slug="familia-divida", shard_bytes=shard_bytes,
                  migracoes_linhas=migracoes_linhas)
passo(rc == 0, f"pin ja divergente nao reprova (exit {rc}): {saida.strip()[-200:]}")
dados = extrai_json(saida)
passo(dados["conflitos"] == [], "nao entra em conflitos")
passo(len(dados["divida_anterior"]) == 1 and dados["divida_anterior"][0]["linhas_afetadas"] == 1,
      f"entra em divida_anterior: {dados['divida_anterior']}")


# ---------- (e) manifesto com linha malformada -> reprova, NAO confunde com "0 lotes"
manifesto = json.dumps({
    "schema_version": "versao_desconhecida", "slug": "familia-malformada",
    "target_rel_path": "data/editorial/v2_pages/familia-malformada.jsonl",
    "target_sha256": "d" * 64, "expected_n": 1,
    "expected_intent_ids": ["intent-a"], "reason_codes": ["missing_terminal_lf"],
    "preserved_record_sha256": {"intent-a": "e" * 64},
    "recovery_item_sha256": "f" * 64,
}) + "\n"
rc, saida = roda(manifesto)
passo(rc != 0, f"manifesto so com linha malformada reprova (exit {rc})")
passo("0 lotes" not in saida, "nao e tratado como manifesto vazio (ha 1 linha, so que invalida)")
dados = extrai_json(saida)
passo(len(dados["malformados"]) == 1, f"malformados carrega exatamente 1 motivo: {dados['malformados']}")


# ---------- (f) regressao: pin da migrations SEM prefixo "sha256:" tambem
#    tem de ser reconhecido como VIVO quando bate com o disco — prova que a
#    normalizacao nao depende do formato de um ledger so.
manifesto = registro_lote("familia-migracao-viva") + "\n"
migracoes_linhas = [
    {"target_shard": "familia-migracao-viva.jsonl", "source_shard_sha256": disco,
     "migration_id": "migracao-viva-20260908"},
]
rc, saida = roda(manifesto, shard_slug="familia-migracao-viva", shard_bytes=shard_bytes,
                  migracoes_linhas=migracoes_linhas)
passo(rc != 0, f"pin de migrations sem prefixo, vivo, reprova (exit {rc})")
dados = extrai_json(saida)
passo(len(dados["conflitos"]) == 1 and dados["conflitos"][0]["ledger"].endswith("v2_portfolio_intent_migrations.jsonl"),
      f"conflito nomeia o ledger de migrations: {dados['conflitos']}")


print()
print("guardas do reorder-nao-invalida-pin-de-shard: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
