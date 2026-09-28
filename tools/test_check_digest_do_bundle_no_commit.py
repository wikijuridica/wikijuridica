#!/usr/bin/env python3
"""Prova do gate que impede a QUARTA ocorrência do digest defasado.

O defeito e as três ocorrências estão no cabeçalho de
`tools/check-digest-do-bundle-no-commit`. O que estes testes travam é o
comportamento que separa gate útil de gate barulhento: reprovar exatamente o
commit que muda o bundle sem reancorar, e ficar calado em todo o resto.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-digest-do-bundle-no-commit"
HOOKS_JSON = ".codex/hooks.json"
# Arquivo REAL do bundle, lido da mesma função que o hook usa em runtime. Não é
# literal escolhido à mão: se alguém tirar este arquivo do bundle, o teste passa
# a exercitar outro, e não um caminho que deixou de importar.
import importlib.util  # noqa: E402
import sys  # noqa: E402


def _um_arquivo_do_bundle() -> str:
    caminho = RAIZ / ".codex" / "hooks" / "anti_loop.py"
    spec = importlib.util.spec_from_file_location("anti_loop", str(caminho))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["anti_loop"] = modulo
    spec.loader.exec_module(modulo)
    arquivos = modulo._integrity_bundle_files()  # noqa: SLF001
    return arquivos[0].relative_to(RAIZ).as_posix()


class GateDoDigestNoCommit(unittest.TestCase):
    def roda(self, caminhos: list[str]) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as arquivo:
            arquivo.write("\n".join(caminhos) + "\n")
            lista = arquivo.name
        try:
            ambiente = dict(os.environ, WIKI_BUNDLE_ARQUIVOS_DO_COMMIT=lista)
            return subprocess.run([str(GATE)], cwd=RAIZ, env=ambiente,
                                  capture_output=True, text=True, timeout=120, check=False)
        finally:
            os.unlink(lista)

    def test_commit_que_toca_o_bundle_sem_reancorar_reprova(self) -> None:
        alvo = _um_arquivo_do_bundle()
        saida = self.roda([alvo])
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        # A mensagem tem de NOMEAR o arquivo e o conserto: gate que reprova sem
        # dizer o que fazer transfere ao leitor o custo do diagnóstico, que é a
        # família de defeito que esta sessão passou o dia atacando.
        self.assertIn(alvo, saida.stderr)
        self.assertIn("generate-codex-hooks-digest", saida.stderr)

    def test_commit_que_reancora_junto_passa(self) -> None:
        saida = self.roda([_um_arquivo_do_bundle(), HOOKS_JSON])
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_commit_sem_arquivo_do_bundle_passa(self) -> None:
        saida = self.roda(["README.md", "internal/render/render.go",
                           "data/ops/qualidade_diaria.jsonl"])
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_indice_vazio_passa(self) -> None:
        # Commit que só remove caminho, ou hook rodando fora de commit: ausência
        # de dado não é reprovação.
        saida = self.roda([])
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_caminho_parecido_mas_fora_do_bundle_nao_e_acusado(self) -> None:
        # FALSO POSITIVO que uma regra por prefixo de diretório produziria: o
        # `_test.go` ao lado do arquivo do bundle NÃO está no bundle
        # (`_integrity_bundle_files` o exclui por construção), e acusá-lo faria
        # todo commit de teste pedir reancoragem inútil.
        saida = self.roda(["internal/goalbaseline/baseline_test.go"])
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_o_digest_do_disco_esta_ancorado_agora(self) -> None:
        # O gate acima cobra a DISCIPLINA do commit; este caso mede o ESTADO.
        # Os dois juntos são o que faltava: em 2026-09-10 o estado estava
        # defasado e nenhum executor automático perguntava.
        saida = subprocess.run(
            [str(RAIZ / "tools" / "generate-codex-hooks-digest"), "--dry-run"],
            cwd=RAIZ, capture_output=True, text=True, timeout=120, check=False)
        self.assertEqual(saida.returncode, 0,
                         "o digest de .codex/hooks.json está defasado do bundle: "
                         "rode ./tools/generate-codex-hooks-digest\n" + saida.stdout + saida.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
