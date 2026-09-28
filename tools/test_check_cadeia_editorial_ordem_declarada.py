#!/usr/bin/env python3
"""Guardas do check-cadeia-editorial-ordem-declarada.

Prova por MUTACAO, executando o gate de verdade (subprocess) contra o
código real de `internal/` (fonte da verdade dos detectores `older_than`) e
um documento SINTÉTICO (nunca o real, para não depender de ele não mudar):

  1. documento com todos os 5 detectores reais declarados -> pass.
  2. documento SEM um dos detectores (mutação: remoção) -> reprova NOMEANDO
     o arquivo:linha (e a função) do detector órfão.
  3. bloco malformado/ausente -> reprova com mensagem clara, não silêncio.
"""
import pathlib
import re
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-cadeia-editorial-ordem-declarada"
INTERNAL_REAL = RAIZ / "internal"

INICIO = "<!-- cadeia:detectores -->"
FIM = "<!-- /cadeia:detectores -->"


def detectores_reais() -> list[str]:
    """Reusa o MESMO grep que o gate usa, para montar um documento sintético
    que reflete o codigo real -- sem isso o teste não prova nada sobre o
    gate, só sobre uma fixture divorciada da fonte."""
    resultado = subprocess.run(
        ["grep", "-rn", "older_than", str(INTERNAL_REAL), "--include=*.go"],
        capture_output=True, text=True)
    entradas = []
    func_re = re.compile(r"^func\s+(\w+)\s*\(")
    for linha in resultado.stdout.splitlines():
        if not linha.strip():
            continue
        caminho, resto = linha.split(":", 1)
        numero_texto, _ = resto.split(":", 1)
        if caminho.endswith("_test.go"):
            continue
        numero = int(numero_texto)
        with open(caminho, encoding="utf-8") as handle:
            linhas_arquivo = handle.readlines()
        funcao = None
        for indice in range(min(numero, len(linhas_arquivo)) - 1, -1, -1):
            m = func_re.match(linhas_arquivo[indice])
            if m:
                funcao = m.group(1)
                break
        caminho_rel = str(pathlib.Path(caminho).resolve().relative_to(RAIZ))
        chave = f"{caminho_rel}:{funcao}"
        if chave not in entradas:
            entradas.append(chave)
    return entradas


def montar_doc(entradas):
    linhas = ["# doc sintetico de teste", "", INICIO]
    linhas.extend(entradas)
    linhas.append(FIM)
    linhas.append("")
    return "\n".join(linhas)


def roda(conteudo_doc):
    with tempfile.TemporaryDirectory() as d:
        doc = pathlib.Path(d) / "doc.md"
        doc.write_text(conteudo_doc, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(GATE), "--doc", str(doc),
             "--internal-dir", str(INTERNAL_REAL), "--json"],
            capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


falhou = 0


def passo(ok, texto):
    global falhou
    print(f"  {'OK' if ok else 'FALHA'} {texto}")
    if not ok:
        falhou = 1


entradas_reais = detectores_reais()
passo(len(entradas_reais) >= 1, f"achou detector(es) older_than reais no codigo: {len(entradas_reais)}")

# ---------- 1. Documento com TODOS os detectores reais -> pass
rc, saida = roda(montar_doc(entradas_reais))
passo(rc == 0, f"documento completo passa (exit {rc}): {saida.strip()[-300:]}")

# ---------- 2. MUTAÇÃO: remove um detector do documento -> reprova nomeando-o
if entradas_reais:
    removido = entradas_reais[0]
    restantes = entradas_reais[1:]
    rc, saida = roda(montar_doc(restantes))
    passo(rc != 0, f"documento sem 1 detector reprova (exit {rc})")
    caminho_removido, funcao_removida = removido.split(":", 1)
    nome_arquivo = caminho_removido.rsplit("/", 1)[-1]
    passo(nome_arquivo in saida and funcao_removida in saida,
          f"a saida nomeia o arquivo ({nome_arquivo}) e a funcao ({funcao_removida}) orfaos: "
          f"{saida.strip()[-400:]}")

# ---------- 3. Bloco ausente -> reprova com mensagem clara (nunca silencio)
rc, saida = roda("# doc sem bloco nenhum\n")
passo(rc != 0, f"documento sem bloco reprova (exit {rc})")
passo("ausente ou malformado" in saida, "mensagem explica o motivo (bloco ausente/malformado)")

print()
print("guardas da cadeia-editorial-ordem-declarada: sem defeito" if not falhou else "REPROVADO")
sys.exit(falhou)
