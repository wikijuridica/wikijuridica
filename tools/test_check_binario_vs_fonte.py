#!/usr/bin/env python3
"""Testes do pathspec de check-binario-vs-fonte.

O gate compara o `vcs.revision` gravado no binário com os commits de código
posteriores. Até 2026-09-05 ele contava QUALQUER commit sob `internal/` ou
`cmd/` — inclusive os que só tocam `*_test.go`, que `go build` não compila.
Medido naquele dia: 4 commits acusados sobre `vcs.revision=6a293de6`, dos quais
2 eram só arquivo de teste.

O risco de errar aqui tem os dois sentidos, e por isso cada um tem teste:
excluir de menos devolve o vermelho por commit inócuo, que ensina a ignorar o
gate; excluir de mais deixa produção rodando binário defasado sem ninguém
avisar — que é o defeito de 2026-08-20 que fez este gate nascer.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "check-binario-vs-fonte"


def carrega():
    loader = importlib.machinery.SourceFileLoader("gate_binario", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def git(repo: pathlib.Path, *args: str) -> str:
    saida = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                           text=True, check=True)
    return saida.stdout


def commita(repo: pathlib.Path, caminho: str, conteudo: str, mensagem: str) -> str:
    alvo = repo / caminho
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(conteudo, encoding="utf-8")
    git(repo, "add", caminho)
    git(repo, "commit", "-q", "-m", mensagem)
    return git(repo, "rev-parse", "HEAD").strip()


class TestPathspecEmRepoSintetico(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "teste@local")
        git(self.repo, "config", "user.name", "teste")
        self.base = commita(self.repo, "internal/x/base.go",
                            "package x\n", "base")

    def tearDown(self):
        self._tmp.cleanup()

    def posteriores(self) -> list[str]:
        saida = git(self.repo, "log", "--oneline", f"{self.base}..HEAD", "--",
                    *self.gate.CAMINHOS_DE_CODIGO, *self.gate.EXCLUSOES_DE_CODIGO)
        return [linha for linha in saida.strip().split("\n") if linha.strip()]

    def test_commit_so_de_teste_nao_conta(self):
        commita(self.repo, "internal/x/x_test.go", "package x\n", "so teste")
        self.assertEqual(self.posteriores(), [])

    def test_commit_de_teste_em_qualquer_profundidade_nao_conta(self):
        """O pathspec sem :(glob) deixa `*` casar `/` — é disso que dependemos."""
        commita(self.repo, "internal/a/b/c/fundo_test.go", "package c\n", "fundo")
        self.assertEqual(self.posteriores(), [])

    def test_commit_de_producao_conta(self):
        commita(self.repo, "internal/x/producao.go", "package x\n", "producao")
        self.assertEqual(len(self.posteriores()), 1)

    def test_commit_misto_conta(self):
        """Teste JUNTO com produção não pode blindar o commit inteiro."""
        (self.repo / "internal/x/misto.go").write_text("package x\n", encoding="utf-8")
        (self.repo / "internal/x/misto_test.go").write_text("package x\n", encoding="utf-8")
        git(self.repo, "add", "internal/x/misto.go", "internal/x/misto_test.go")
        git(self.repo, "commit", "-q", "-m", "misto")
        self.assertEqual(len(self.posteriores()), 1)

    def test_go_mod_conta(self):
        commita(self.repo, "go.mod", "module t\n\ngo 1.26\n", "go.mod")
        self.assertEqual(len(self.posteriores()), 1)

    def test_arquivo_fora_dos_caminhos_de_codigo_nao_conta(self):
        commita(self.repo, "docs/nota.md", "nota\n", "doc")
        self.assertEqual(self.posteriores(), [])

    def test_dado_embutivel_dentro_de_internal_continua_contando(self):
        """NÃO AFROUXOU: `//go:embed` alcança não-.go sob internal/, e o gate vê."""
        commita(self.repo, "internal/x/tabela.json", "{}\n", "dado embutido")
        self.assertEqual(len(self.posteriores()), 1)

    def test_testdata_continua_contando(self):
        """Decisão deliberada: `testdata/` fica FORA da exclusão.

        Hoje nenhum `//go:embed` do repo aponta para `testdata/` (verificado em
        2026-09-05), mas essa é uma condição que uma linha futura muda em
        silêncio — enquanto "o compilador não compila _test.go" é do toolchain.
        Se um dia a exclusão for ampliada, este teste cobra a decisão explícita.
        """
        commita(self.repo, "internal/x/testdata/fixture.json", "{}\n", "fixture")
        self.assertEqual(len(self.posteriores()), 1)


class TestContraOsCommitsReais(unittest.TestCase):
    """Os hashes abaixo são imutáveis: commits que já existem neste repositório."""

    def setUp(self):
        self.gate = carrega()

    def conta(self, intervalo: str, com_exclusao: bool) -> int:
        args = ["git", "log", "--oneline", intervalo, "--",
                *self.gate.CAMINHOS_DE_CODIGO]
        if com_exclusao:
            args += self.gate.EXCLUSOES_DE_CODIGO
        saida = subprocess.run(args, cwd=RAIZ, capture_output=True, text=True)
        if saida.returncode != 0:
            self.skipTest(f"commit ausente nesta arvore: {saida.stderr.strip()[:80]}")
        return len([l for l in saida.stdout.strip().split("\n") if l.strip()])

    def test_commit_so_de_teste_sai_da_conta(self):
        """e0fae8e9 tocou apenas internal/contract/checkmeta/*_test.go."""
        self.assertEqual(self.conta("e0fae8e9~1..e0fae8e9", com_exclusao=False), 1)
        self.assertEqual(self.conta("e0fae8e9~1..e0fae8e9", com_exclusao=True), 0)

    def test_commit_de_producao_permanece(self):
        """2a14a29f mexeu no servidor da rede social — tem de continuar contando."""
        self.assertEqual(self.conta("2a14a29f~1..2a14a29f", com_exclusao=True), 1)


if __name__ == "__main__":
    unittest.main()
