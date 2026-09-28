#!/usr/bin/env python3
"""Reconstroi partial.jsonl do zero a partir dos p<NN>.json atuais (pos-edicao),
garantindo que nenhuma entrada fique desatualizada. So roda quando TODOS os
p<NN>.json do slice ja existem e passaram pelo recount --write.
"""
import json
import sys
from pathlib import Path

WORKDIR = Path(sys.argv[1])

order = [
    ("p01.json", "suc-substituicao-vulgar-testamento"),
    ("p02.json", "suc-legado-imovel-com-divida"),
    ("p03.json", "suc-legado-alimentos-pensao"),
    ("p04.json", "suc-testamento-testemunhas-requisitos"),
    ("p05.json", "suc-testamento-guarda-custodia-vias"),
    ("p06.json", "suc-testamento-fundacao-caridade"),
    ("p07.json", "suc-testamento-parte-disponivel-companheiro"),
    ("p08.json", "suc-testamento-ordem-preferencia-legados"),
    ("p09.json", "suc-testamento-encargo-modal"),
    ("p10.json", "suc-testamento-bens-digitais-senha-cripto"),
    ("p11.json", "suc-testamento-testamenteiro-dativo"),
    ("p12.json", "suc-testamento-curatelado-interdito"),
    ("p13.json", "suc-testamento-assinatura-a-rogo"),
    ("p14.json", "suc-testamento-cerrado-extraviado"),
    ("p15.json", "suc-testamento-indicar-curador-filho-deficiente"),
]

lines = []
for fname, intent in order:
    path = WORKDIR / fname
    if not path.exists():
        print(f"ERRO: {fname} nao existe ainda -- abortando rebuild")
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("intent_id") != intent:
        print(f"ERRO: {fname} intent_id {data.get('intent_id')!r} != {intent!r}")
        sys.exit(1)
    wc = data.get("word_count")
    if not isinstance(wc, int) or isinstance(wc, bool) or wc <= 0:
        print(f"ERRO: {fname} word_count invalido: {wc!r}")
        sys.exit(1)
    lines.append(json.dumps(data, ensure_ascii=False))

partial_path = WORKDIR / "partial.jsonl"
partial_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"OK: partial.jsonl reconstruido com {len(lines)} linhas")
for fname, intent in order:
    print(" -", intent)
