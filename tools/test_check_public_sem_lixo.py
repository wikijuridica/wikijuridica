#!/usr/bin/env python3
"""test_check_public_sem_lixo — o que o gate de lixo em public/ tem de acusar.

POR QUE ESTE TESTE EXISTE (2026-09-04). O `tools/check-public-sem-lixo` nasceu
com uma allowlist congelada numa medição de 2026-08-27 e nunca mais foi tocado.
Em 2026-09-03 o CSS saiu do HTML de todas as páginas para uma folha externa
(`public/assets/wj-<hash>.css`, contrato "HTML leve" do CLAUDE.md), e no dia
seguinte a onda diária passou a terminar PARCIAL todo dia porque o gate acusava
o artefato que o próprio contrato manda existir.

E havia um segundo defeito, mais grave que o primeiro porque era SILENCIOSO: o
script calculava `base="${file%.br}"` — a intenção declarada de julgar a gêmea
comprimida pela extensão de baixo — e depois extraía a extensão de `$file`, não
de `$base`. A variável era escrita e jamais lida. O efeito prático é que `.br`
estar na allowlist transformava o sufixo num CORINGA: qualquer arquivo passava
pelo gate bastando terminar em `.br`. O nginx serve `$uri.br` com
`brotli_static on` sem comparar frescor nem tipo — um `.br` órfão ou de tipo
proibido é conteúdo servido ao público que nenhum gate enxergava.

Os casos abaixo são exatamente esses dois defeitos, mais as bordas que a
correção não pode quebrar.
"""

import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")
GATE = os.path.join(RAIZ, "tools", "check-public-sem-lixo")

# A folha real do acervo, no formato fechado que render.StylesheetPathPattern
# emite (`^/assets/wj-[0-9a-f]{16}\.css$`). Não é um exemplo inventado: é o
# nome do arquivo que está no ar hoje.
FOLHA_REAL = "wj-5b082578c84d2407.css"

falhas = []


def roda_gate(arvore: dict) -> tuple:
    """Monta uma `public/` de mentira e roda o gate REAL contra ela.

    O gate usa `find public` relativo, então basta executá-lo com o cwd na raiz
    temporária — nenhuma cópia do script, nenhuma reimplementação da lógica em
    Python (gate testado por gêmeo em outra linguagem é gate não testado).
    """
    tmp = tempfile.mkdtemp(prefix="wj-sem-lixo-")
    try:
        for caminho, conteudo in arvore.items():
            destino = os.path.join(tmp, caminho)
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as fh:
                fh.write(conteudo)
        proc = subprocess.run(
            [GATE], cwd=tmp, capture_output=True, text=True, timeout=120
        )
        return proc.returncode, proc.stdout + proc.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verifica(nome: str, arvore: dict, espera_exit: int, trecho: str = "") -> None:
    codigo, saida = roda_gate(arvore)
    if codigo != espera_exit:
        falhas.append(
            f"{nome}: esperava exit {espera_exit}, veio {codigo}\n"
            f"    saída: {saida.strip()[:400]}"
        )
        return
    if trecho and trecho not in saida:
        falhas.append(
            f"{nome}: exit correto ({codigo}) mas a mensagem não nomeia a causa\n"
            f"    esperava conter: {trecho!r}\n"
            f"    saída: {saida.strip()[:400]}"
        )


ACERVO_MINIMO = {
    "public/index.html": "<html></html>",
    "public/index.html.br": "brotli",
    "public/sitemap.xml": "<urlset/>",
    "public/robots.txt": "User-agent: *",
    "public/favicon.ico": "ico",
    "public/logo.png": "png",
    "public/icone.svg": "<svg/>",
}


def com(extra: dict) -> dict:
    arvore = dict(ACERVO_MINIMO)
    arvore.update(extra)
    return arvore


# ------------------------------------------------------------------ DEFEITO 1
# A folha externa é o contrato de indexação desde 2026-09-03, não sobra a varrer.
verifica(
    "folha externa no caminho fechado PASSA",
    com({
        f"public/assets/{FOLHA_REAL}": "body{}",
        f"public/assets/{FOLHA_REAL}.br": "brotli",
    }),
    espera_exit=0,
)

# ------------------------------------------------------------------ DEFEITO 2
# `.br` era coringa: qualquer extensão passava bastando o sufixo comprimido.
verifica(
    "gêmea .br de tipo proibido REPROVA NOMEANDO A GÊMEA (era o coringa silencioso)",
    com({"public/instalador.exe": "MZ", "public/instalador.exe.br": "brotli"}),
    espera_exit=1,
    # O `.exe` solto já reprovava; a gêmea `.br` NÃO — era ela que passava por
    # ter o sufixo na allowlist. Cobrar o nome da gêmea na mensagem é o que
    # separa o defeito corrigido do defeito que continua escondido atrás dele.
    trecho="instalador.exe.br",
)

verifica(
    "gêmea .br SEM original REPROVA (nginx serviria conteúdo sem fonte)",
    com({"public/pagina-morta.html.br": "brotli"}),
    espera_exit=1,
    trecho="pagina-morta.html.br",
)

# ------------------------------------------------------- CSS FORA DO CONTRATO
# A CSP recusou `'self'` em style-src exatamente porque ele autorizaria QUALQUER
# .css que aparecesse em public/ (CLAUDE.md, "HTML leve"). O gate é a contraparte
# disciplinada disso: só a folha do padrão fechado passa.
verifica(
    "CSS solto fora de /assets/ REPROVA",
    com({"public/familia/estilo.css": "body{}"}),
    espera_exit=1,
    trecho="estilo.css",
)

verifica(
    "CSS em /assets/ com nome fora do padrão fechado REPROVA",
    com({"public/assets/tema-escuro.css": "body{}"}),
    espera_exit=1,
    trecho="tema-escuro.css",
)

# ------------------------------------------------------------------- BORDAS
verifica(
    "arquivo qualquer em /assets/ REPROVA (o nginx devolve 404 para tudo ali)",
    com({f"public/assets/{FOLHA_REAL}": "body{}", "public/assets/logo.png": "png"}),
    espera_exit=1,
    trecho="logo.png",
)

verifica(
    "arquivo sem extensão REPROVA",
    com({"public/LEIAME": "texto"}),
    espera_exit=1,
    trecho="LEIAME",
)

verifica(
    "extensão proibida em diretório com ponto no nome REPROVA",
    com({"public/v1.2/pacote.zip": "PK"}),
    espera_exit=1,
    trecho="pacote.zip",
)

verifica(
    "arquivo sem extensão em diretório com ponto no nome REPROVA PELA CAUSA CERTA",
    com({"public/v1.2/LEIAME": "texto"}),
    espera_exit=1,
    # `${file##*.}` sobre o caminho INTEIRO devolvia `2/LEIAME` como se fosse a
    # extensão: o gate reprovava por acidente, com uma mensagem que mandaria o
    # operador procurar uma extensão `.2/LEIAME` que não existe. A extensão se
    # extrai do basename, nunca do caminho.
    trecho="sem extensão",
)

verifica(
    "acervo legítimo completo PASSA",
    com({
        f"public/assets/{FOLHA_REAL}": "body{}",
        f"public/assets/{FOLHA_REAL}.br": "brotli",
        "public/familia/divorcio/index.html": "<html></html>",
        "public/familia/divorcio/index.html.br": "brotli",
        "public/llms-full.txt": "texto",
        "public/llms-full.txt.br": "brotli",
        "public/sitemap.xml.br": "brotli",
    }),
    espera_exit=0,
)

if falhas:
    print("test_check_public_sem_lixo: FALHOU")
    for f in falhas:
        print("  - " + f)
    sys.exit(1)

print("test_check_public_sem_lixo: pass — 11 casos (2 defeitos reais + 9 bordas)")
