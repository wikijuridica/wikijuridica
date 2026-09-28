#!/usr/bin/env python3
"""Teste de MUTACAO de tools/check-nginx-standalone-parity — prova que o
"segundo criterio" (linhas_perdidas_na_regeracao, que reusa
linhas_decisivas() de tools/generate-nginx-standalone) de fato reprova quando
o gerador fica atras do que esta implantado, nomeando a linha perdida.

Contexto do defeito original (2026-09-08): commits 86e41b41/ba7f0238
(2026-09-02) corrigiram ops/nginx/standalone/nginx.conf DIRETO, em incidente
de producao, e o gerador nunca foi atualizado — cinco diretivas de contexto
main/http (`user`, `variables_hash_max_size`, `if_modified_since`, dois
`proxy_cache_path`) sumiram do que ele produz. A comparacao vivo-vs-dedicado
JA EXISTENTE neste check nao pega essa classe (vhost vivo e um FRAGMENTO sem
`http {}`, entao essas diretivas nunca aparecem do lado "vivo"). Este teste
prova que o segundo criterio pega.

Metodo: copia gerador + check + os dois arquivos nginx para um diretorio
temporario com o MESMO layout relativo (tools/, ops/nginx/,
ops/nginx/standalone/) — RAIZ de ambos os scripts e derivada do proprio
__file__, entao a copia funciona sem tocar o repositorio real. Roda o check
copiado por subprocess (nunca importa o script real, e nunca escreve em
ops/nginx/standalone/nginx.conf do repositorio).

Casos:
  1. gerador intacto  -> "if_modified_since before;" NAO aparece na lista de
     linhas novas perdidas (o teste nao afirma exit 0 geral: a baseline de
     divida pre-existente do redesocial pode reprovar por outro motivo, mas
     NUNCA por esta linha).
  2. gerador mutado (linha se apaga do template) -> reprova, e a mensagem cita
     literalmente "if_modified_since before;".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_RAIZ = os.path.dirname(TOOLS_DIR)
GERADOR_REAL = os.path.join(TOOLS_DIR, "generate-nginx-standalone")
CHECK_REAL = os.path.join(TOOLS_DIR, "check-nginx-standalone-parity")
VHOST_REAL = os.path.join(REPO_RAIZ, "ops", "nginx", "wikijuridica.conf")
DEDICADO_REAL = os.path.join(REPO_RAIZ, "ops", "nginx", "standalone", "nginx.conf")

LINHA_ALVO = "if_modified_since before;"


def _monta_copia(tmp: str) -> tuple[str, str]:
    """Copia os quatro arquivos para dentro de `tmp`, preservando o layout
    relativo (tools/... e ops/nginx/...) de que os dois scripts dependem via
    `pathlib.Path(__file__).resolve().parent.parent`. Devolve os caminhos do
    check e do gerador DENTRO da copia."""
    tools_dir = os.path.join(tmp, "tools")
    nginx_dir = os.path.join(tmp, "ops", "nginx")
    standalone_dir = os.path.join(nginx_dir, "standalone")
    os.makedirs(tools_dir, exist_ok=True)
    os.makedirs(standalone_dir, exist_ok=True)

    gerador_copia = os.path.join(tools_dir, "generate-nginx-standalone")
    check_copia = os.path.join(tools_dir, "check-nginx-standalone-parity")
    shutil.copyfile(GERADOR_REAL, gerador_copia)
    shutil.copyfile(CHECK_REAL, check_copia)
    shutil.copyfile(VHOST_REAL, os.path.join(nginx_dir, "wikijuridica.conf"))
    shutil.copyfile(DEDICADO_REAL, os.path.join(standalone_dir, "nginx.conf"))
    os.chmod(gerador_copia, 0o755)
    os.chmod(check_copia, 0o755)
    return check_copia, gerador_copia


def _apaga_linha_do_gerador(caminho_gerador: str, linha_alvo: str) -> None:
    with open(caminho_gerador, encoding="utf-8") as f:
        texto = f.read()
    linhas = texto.split("\n")
    antes = len(linhas)
    linhas = [l for l in linhas if l.strip() != linha_alvo]
    depois = len(linhas)
    assert depois == antes - 1, (
        f"esperava remover exatamente 1 ocorrencia de {linha_alvo!r}, "
        f"removeu {antes - depois}"
    )
    with open(caminho_gerador, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def _roda_check(caminho_check: str) -> tuple[int, str]:
    resultado = subprocess.run(
        [sys.executable, caminho_check],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return resultado.returncode, resultado.stdout + resultado.stderr


class GeradorIntactoNaoAcusaALinhaTest(unittest.TestCase):
    def test_linha_alvo_presente_no_gerador_intacto(self):
        with tempfile.TemporaryDirectory(prefix="wj-parity-mut-ok-") as tmp:
            check_copia, gerador_copia = _monta_copia(tmp)
            with open(gerador_copia, encoding="utf-8") as f:
                self.assertIn(LINHA_ALVO, f.read())
            exit_code, saida = _roda_check(check_copia)
            self.assertNotIn(
                f"- {LINHA_ALVO}", saida,
                "gerador intacto nao deveria acusar perda desta linha",
            )
            # NAO BASTA "a linha nao apareceu" — isso tambem seria verdade se
            # o segundo criterio nunca tivesse rodado (p.ex. o check morresse
            # num modo de falha anterior). A prova de que RODOU e concluiu e o
            # resumo "0 linha(s) nova(s)", so impresso depois de
            # linhas_perdidas_na_regeracao() terminar sem novas_perdas.
            self.assertIn(
                "regeracao: 0 linha(s) nova(s)", saida,
                f"o segundo criterio (linhas_perdidas_na_regeracao) nao "
                f"chegou a concluir; saida:\n{saida}",
            )
            self.assertEqual(0, exit_code, f"saida:\n{saida}")


class GeradorMutadoAcusaALinhaTest(unittest.TestCase):
    def test_linha_removida_do_gerador_reprova_nomeando_a_linha(self):
        with tempfile.TemporaryDirectory(prefix="wj-parity-mut-bad-") as tmp:
            check_copia, gerador_copia = _monta_copia(tmp)
            _apaga_linha_do_gerador(gerador_copia, LINHA_ALVO)
            with open(gerador_copia, encoding="utf-8") as f:
                self.assertNotIn(LINHA_ALVO, f.read())

            exit_code, saida = _roda_check(check_copia)

            self.assertNotEqual(0, exit_code, f"deveria reprovar; saida:\n{saida}")
            self.assertIn(
                "gerador atras do implantado", saida,
                f"deveria nomear a classe do defeito; saida:\n{saida}",
            )
            self.assertIn(
                LINHA_ALVO, saida,
                f"deveria citar a linha especifica que sumiria; saida:\n{saida}",
            )


if __name__ == "__main__":
    unittest.main()
