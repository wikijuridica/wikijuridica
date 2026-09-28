#!/usr/bin/env python3
"""Guardas do check-reorder-nao-toca-publicada.

Prova por MUTACAO, executando o gate de verdade (subprocess), nunca por
raciocinio:
  1. manifesto so com intents NAO publicados -> pass.
  2. um intent PUBLICADO no meio de um lote -> reprova NOMEANDO esse intent.
  3. manifesto ausente/vazio -> pass com mensagem explicita "0 lotes".
  4. target_rel_path que aponta para shard inexistente -> reprova nomeando o
     shard ausente (o MESMO defeito visto pelo outro lado, conforme o
     enunciado da tarefa).
"""
import json
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-reorder-nao-toca-publicada"

falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


def registro_lote(slug, expected_intent_ids):
    return json.dumps({
        "schema_version": "v2_writing_mechanical_reorder_v1",
        "slug": slug,
        "target_rel_path": f"data/editorial/v2_pages/{slug}.jsonl",
        "target_sha256": "a" * 64,
        "expected_n": len(expected_intent_ids),
        "expected_intent_ids": expected_intent_ids,
        "reason_codes": ["intent_order_mismatch"],
        "preserved_record_sha256": {i: "b" * 64 for i in expected_intent_ids},
        "recovery_item_sha256": "c" * 64,
    })


def roda(manifesto_conteudo, publicados_conteudo, *, criar_shards=True, args_extra=()):
    with tempfile.TemporaryDirectory() as d:
        raiz = pathlib.Path(d)
        (raiz / "data" / "ops").mkdir(parents=True)
        (raiz / "data" / "editorial" / "v2_pages").mkdir(parents=True)
        manifesto = raiz / "data" / "ops" / "writing_mechanical_reorder_todo.jsonl"
        publicados = raiz / "data" / "editorial" / "published_manifest.jsonl"
        if manifesto_conteudo is not None:
            manifesto.write_text(manifesto_conteudo, encoding="utf-8")
        if publicados_conteudo is not None:
            publicados.write_text(publicados_conteudo, encoding="utf-8")
        if criar_shards and manifesto_conteudo:
            for linha in manifesto_conteudo.strip().split("\n"):
                if not linha:
                    continue
                registro = json.loads(linha)
                shard = raiz / registro["target_rel_path"]
                shard.write_text("", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(GATE), "--manifest", str(manifesto),
             "--publicados", str(publicados), "--root", str(raiz), "--json", *args_extra],
            capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


def publicados_jsonl(unique_intent_ids):
    return "\n".join(
        json.dumps({"unique_intent_id": i, "page_status": "published"})
        for i in unique_intent_ids
    ) + "\n"


# ---------- 1. So intents NAO publicados -> pass
manifesto = registro_lote("familia-04", ["intent-a", "intent-b"]) + "\n"
publicados = publicados_jsonl(["intent-x", "intent-y"])
rc, saida = roda(manifesto, publicados)
passo(rc == 0, f"lote so com intents nao publicados passa (exit {rc}): {saida.strip()[-200:]}")

# ---------- 2. Um intent PUBLICADO no meio -> reprova NOMEANDO o intent
manifesto = registro_lote("familia-05", ["intent-a", "intent-PUBLICADO", "intent-b"]) + "\n"
publicados = publicados_jsonl(["intent-PUBLICADO", "intent-x"])
rc, saida = roda(manifesto, publicados)
passo(rc != 0, f"lote com intent publicado reprova (exit {rc})")
passo("intent-PUBLICADO" in saida, "a saida nomeia o intent publicado")
linha_json = next(l for l in saida.splitlines() if l.startswith("{"))
dados = json.loads(linha_json)
passo(dados["violacoes"] and dados["violacoes"][0]["intents_publicados"] == ["intent-PUBLICADO"],
      f"JSON nomeia exatamente o intent violado: {dados['violacoes']}")

# ---------- 3a. Manifesto AUSENTE -> pass com "0 lotes"
rc, saida = roda(None, publicados_jsonl(["intent-x"]))
passo(rc == 0, f"manifesto ausente passa (exit {rc})")
passo("0 lotes" in saida, "mensagem explicita de 0 lotes a conferir")

# ---------- 3b. Manifesto VAZIO (0 bytes) -> pass com "0 lotes"
rc, saida = roda("", publicados_jsonl(["intent-x"]))
passo(rc == 0, f"manifesto vazio passa (exit {rc})")
passo("0 lotes" in saida, "mensagem explicita de 0 lotes a conferir (vazio)")

# ---------- 4. target_rel_path aponta para shard AUSENTE no disco -> reprova
#    nomeando o shard, mesmo com todos os intents nao publicados.
manifesto = registro_lote("familia-fantasma", ["intent-a"]) + "\n"
rc, saida = roda(manifesto, publicados_jsonl(["intent-x"]), criar_shards=False)
passo(rc != 0, f"shard inexistente reprova mesmo sem intent publicado (exit {rc})")
passo("familia-fantasma" in saida, "a saida nomeia o shard ausente")

# ---------- 5. Universo publicado AUSENTE (published_manifest sumiu/vazio)
#    com lote(s) existentes -> reprova. "Nao sei se toca publicada" NAO pode
#    virar aprovacao por falta de dado (mesmo defeito ja documentado em
#    check-crawl-coverage-stall: campo ausente nao e aprovacao).
manifesto = registro_lote("familia-06", ["intent-a", "intent-b"]) + "\n"
rc, saida = roda(manifesto, publicados_conteudo=None)
passo(rc != 0, f"universo publicado ausente com lotes existentes reprova (exit {rc})")
passo("universo publicado" in saida, "a saida explica o motivo: universo publicado vazio/ausente")

# ---------- 6. Manifesto so com linha(s) MALFORMADA(S) (schema_version
#    errado) -> reprova (lotes=[] mas malformados=[...], nao pode virar
#    "0 lotes a conferir" -- e um registro que a ferramenta nao consegue
#    provar seguro, nao um manifesto vazio).
manifesto = json.dumps({
    "schema_version": "versao_desconhecida", "slug": "familia-07",
    "target_rel_path": "data/editorial/v2_pages/familia-07.jsonl",
    "target_sha256": "d" * 64, "expected_n": 1,
    "expected_intent_ids": ["intent-a"], "reason_codes": ["missing_terminal_lf"],
    "preserved_record_sha256": {"intent-a": "e" * 64},
    "recovery_item_sha256": "f" * 64,
}) + "\n"
rc, saida = roda(manifesto, publicados_jsonl(["intent-x"]))
passo(rc != 0, f"manifesto so com linha malformada reprova (exit {rc})")
passo("0 lotes" not in saida, "nao e tratado como manifesto vazio (ha 1 linha, so que invalida)")

print()
print("guardas do reorder-nao-toca-publicada: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
