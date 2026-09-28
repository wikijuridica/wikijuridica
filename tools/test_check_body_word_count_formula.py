#!/usr/bin/env python3
"""Testes de tools/check-body-word-count-formula — a verificação do PRODUTOR.

O check já conferia o leitor (o censo) e o resultado (o campo no estoque). O
que faltava, e o que deixou o BUG-048 durar meses, era conferir quem ESCREVE o
`word_count`: cinco geradores de canal derivado rodam todo dia por
tools/run-daily-content e quatro deles contavam com `strings.Fields`, que não
quebra número pontuado — "Lei 9.494/97" valia uma palavra em vez de quatro.

Este arquivo prova as duas pontas exigidas pelo contrato:

  1. a fonte ANTERIOR à correção (lida do commit HEAD, não reescrita à mão)
     REPROVA — é o contra-teste que impede a verificação de virar no-op;
  2. a fonte VIVA da worktree aprova, e aprova pelos dois caminhos que existem
     no projeto: a chamada direta a ptbrtext.BodyWords e a chamada por função
     intermediária do próprio gerador (o caso de generate-stj-tema-pages).
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

# Último commit em que cmd/generate-{diario,noticia,stf-informativo,stj-sumula}
# -pages ainda declaravam word_count com strings.Fields (BUG-048, 2026-08-29).
COMMIT_ANTES_DA_CORRECAO = "dfc954b8683de4082dcce86b2059198d4cbafe74"

QUEBRADOS_ANTES_DA_CORRECAO = (
    "generate-diario-pages",
    "generate-noticia-pages",
    "generate-stf-informativo-pages",
    "generate-stj-sumula-pages",
)


def carregar_check():
    caminho = os.path.join(RAIZ, "tools", "check-body-word-count-formula")
    spec = importlib.util.spec_from_loader(
        "check_body_word_count_formula",
        importlib.machinery.SourceFileLoader("check_body_word_count_formula", caminho))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def fonte_no_commit(commit, caminho_relativo):
    resultado = subprocess.run(
        ["git", "show", "%s:%s" % (commit, caminho_relativo)],
        cwd=RAIZ, text=True, capture_output=True, check=False)
    if resultado.returncode != 0:
        raise unittest.SkipTest(
            "git show %s:%s indisponível: %s" % (commit, caminho_relativo,
                                                 resultado.stderr.strip()))
    return resultado.stdout


class FormulaDoProdutorTest(unittest.TestCase):
    def setUp(self):
        self.check = carregar_check()

    def test_fonte_anterior_a_correcao_reprova(self):
        """A fonte que produziu as 950 divergências tem de reprovar aqui.

        Sem este caso a verificação poderia estar cega e ninguém notaria: um
        check que só vê verde nunca prova que sabe enxergar vermelho.

        O commit é FIXO de propósito. Apontar para HEAD faria o teste passar
        hoje e quebrar no primeiro commit da própria correção, que é justamente
        quando ele precisa continuar valendo. `COMMIT_ANTES_DA_CORRECAO` é o
        último estado da árvore em que os quatro geradores ainda contavam com
        strings.Fields — o defeito real, não uma fonte sintética.
        """
        for nome in QUEBRADOS_ANTES_DA_CORRECAO:
            with self.subTest(gerador=nome):
                fonte = fonte_no_commit(COMMIT_ANTES_DA_CORRECAO,
                                        "cmd/%s/main.go" % nome)
                falhas = self.check.falhas_da_formula_do_produtor(nome, fonte)
                self.assertTrue(
                    falhas,
                    "%s usava strings.Fields no commit HEAD e a verificação "
                    "não reprovou — ela está cega" % nome)
                self.assertIn("strings.Fields", falhas[0])

    def test_fonte_viva_aprova_nos_dois_formatos_de_chamada(self):
        """Chamada direta e chamada por função intermediária, ambas válidas."""
        for nome in self.check.PRODUTORES:
            with self.subTest(gerador=nome):
                caminho = os.path.join(RAIZ, "cmd", nome, "main.go")
                with open(caminho, encoding="utf-8") as handle:
                    fonte = handle.read()
                self.assertEqual(
                    [], self.check.falhas_da_formula_do_produtor(nome, fonte),
                    "%s deveria contar por ptbrtext.BodyWords" % nome)

    def test_gerador_que_perde_a_atribuicao_reprova(self):
        """Se o produtor deixar de declarar WordCount por função, avisa em vez
        de aprovar em silêncio — cegueira do detector é falha, não aprovação."""
        falhas = self.check.falhas_da_formula_do_produtor(
            "gerador-hipotetico", "package main\n\nfunc main() {}\n")
        self.assertTrue(falhas)
        self.assertIn("cegou", falhas[0])

    def test_produtor_python_com_split_reprova(self):
        """O contra-teste da varredura Python, sobre a fonte REAL do defeito.

        tools/generate-v2-rescued-pages declarava `len(body.split())` até hoje.
        A varredura roda sobre a worktree; para provar que ela enxerga o
        vermelho, o teste monta um diretório com um gerador vivo escrito com a
        fórmula antiga e confere que reprova — e que o mesmo arquivo, com a
        fórmula do auditor, aprova.
        """
        antigo = ('#!/usr/bin/env python3\n'
                  'body = ""\n'
                  'out["word_count"] = len(body.split())\n')
        correto = ('#!/usr/bin/env python3\n'
                   'from audit_v2_pages import body_word_count\n'
                   'out["word_count"] = body_word_count(out)\n')
        for fonte, deve_reprovar in ((antigo, True), (correto, False)):
            with tempfile.TemporaryDirectory() as diretorio:
                ferramentas = os.path.join(diretorio, "tools")
                os.makedirs(ferramentas)
                alvo = os.path.join(ferramentas, "generate-v2-paginas-vivas")
                with open(alvo, "w", encoding="utf-8") as handle:
                    handle.write(fonte)
                falhas = self.check.falhas_dos_produtores_python(diretorio)
                self.assertEqual(bool(falhas), deve_reprovar,
                                 "fonte=%r falhas=%r" % (fonte, falhas))

    def test_produtor_python_datado_nao_reprova(self):
        """Reparo datado já executado não é produtor vivo — o estoque dele é
        conferido pela igualdade exata, e reprovar aqui seria vermelho
        permanente contra trabalho concluído."""
        with tempfile.TemporaryDirectory() as diretorio:
            ferramentas = os.path.join(diretorio, "tools")
            os.makedirs(ferramentas)
            alvo = os.path.join(ferramentas, "generate-v2-reparo-20260804")
            with open(alvo, "w", encoding="utf-8") as handle:
                handle.write('out["word_count"] = len(body.split())\n')
            self.assertEqual([], self.check.falhas_dos_produtores_python(diretorio))

    def test_intermediaria_com_strings_fields_reprova(self):
        """O salto de um nível não pode virar porta dos fundos."""
        fonte = (
            "package main\n\n"
            "func conta(p Pagina) int {\n\treturn len(corpoEmPalavras(p))\n}\n\n"
            "func corpoEmPalavras(p Pagina) []string {\n"
            "\treturn strings.Fields(p.Opening)\n}\n\n"
            "func x() {\n\tpagina.WordCount = conta(pagina)\n}\n")
        falhas = self.check.falhas_da_formula_do_produtor("gerador-hipotetico", fonte)
        self.assertTrue(falhas)
        self.assertIn("strings.Fields", falhas[0])


if __name__ == "__main__":
    unittest.main()
