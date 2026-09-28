#!/usr/bin/env python3
"""Testes de tools/check-redesocial-culpa-do-commit.

O script decide se uma entrega sem prova barra o commit ou apenas o avisa. Errar
para o lado frouxo deixa passar entrega marcada como pronta sem prova; errar
para o lado severo trava frentes inteiras por dívida alheia — foi o que
aconteceu em 2026-09-05, quando 8 provas ausentes da rede social barraram quatro
commits sem relação nenhuma e prenderam 25 arquivos no índice compartilhado.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "tools" / "check-redesocial-culpa-do-commit"


class CulpaDoCommitTest(unittest.TestCase):
    def roda(self, saida: str, staged: str):
        with tempfile.TemporaryDirectory() as tmp:
            a = pathlib.Path(tmp) / "saida.txt"
            b = pathlib.Path(tmp) / "staged.txt"
            a.write_text(saida, encoding="utf-8")
            b.write_text(staged, encoding="utf-8")
            return subprocess.run(
                [str(SCRIPT), str(a), str(b)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_divida_em_arquivo_que_o_commit_nao_toca_nao_barra(self):
        """O caso que travou quatro frentes: a prova falta em content/pages.json,
        e o commit mexe em internal/corpus. Não é regressão dele."""
        r = self.roda(
            'redesocial-completude: redesocial_prova_texto_ausente: F0-paginas-legais: '
            'content/pages.json nao contem "art. 42, I" fora de comentario\n',
            "internal/corpus/corpus.go\ninternal/corpus/veto_test.go\n",
        )
        self.assertEqual(r.returncode, 0, f"devia apenas avisar:\n{r.stdout}{r.stderr}")
        self.assertIn("ALHEIA:", r.stdout)
        self.assertNotIn("MINHA:", r.stdout)
        # a dívida continua impressa: avisar não é esconder
        self.assertIn("art. 42, I", r.stdout)

    def test_divida_em_arquivo_que_o_commit_toca_barra(self):
        """O caso que o gate existe para pegar: quem mexe no arquivo responde
        pela prova que deveria estar nele."""
        r = self.roda(
            'redesocial-completude: redesocial_prova_texto_ausente: F0-paginas-legais: '
            'content/pages.json nao contem "art. 42, I" fora de comentario\n',
            "content/pages.json\ninternal/corpus/corpus.go\n",
        )
        self.assertEqual(r.returncode, 1, f"devia barrar:\n{r.stdout}{r.stderr}")
        self.assertIn("MINHA:", r.stdout)

    def test_linha_sem_caminho_reconhecivel_barra_fail_closed(self):
        """Se o script não sabe de quem é a dívida, o commit para. Na dúvida, a
        direção segura é barrar — o inverso deixaria passar o formato de mensagem
        que ninguém previu."""
        r = self.roda(
            "redesocial-completude: redesocial_entrega_sem_pacote: FP-alguma-coisa sem pacote declarado\n",
            "internal/corpus/corpus.go\n",
        )
        self.assertEqual(r.returncode, 1, f"fail-closed devia barrar:\n{r.stdout}{r.stderr}")
        self.assertIn("MINHA:", r.stdout)

    def test_linha_que_nao_e_veredito_nao_classifica_nada(self):
        """Ruído de progresso não pode virar reprovação — nem absolvição."""
        r = self.roda(
            "redesocial-completude: lendo content/redesocial_entregas.json\n"
            "varrendo 163 entregas\n",
            "internal/corpus/corpus.go\n",
        )
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_mistura_barra_e_separa_as_duas(self):
        """Uma linha de cada: barra por causa da própria, e ainda assim reporta a
        alheia, para o autor saber que ela existe."""
        r = self.roda(
            'redesocial-completude: redesocial_prova_texto_ausente: F0-paginas-legais: '
            'content/pages.json nao contem "art. 42, I" fora de comentario\n'
            'redesocial-completude: redesocial_prova_texto_ausente: FP-antes-de-perguntar: '
            'cmd/social/rotas.go nao contem "antes-de-perguntar" fora de comentario\n',
            "cmd/social/rotas.go\n",
        )
        self.assertEqual(r.returncode, 1)
        self.assertIn("ALHEIA:", r.stdout)
        self.assertIn("MINHA:", r.stdout)
        self.assertIn("content/pages.json", r.stdout)
        self.assertIn("cmd/social/rotas.go", r.stdout)

    def test_caminho_parcial_nao_conta_como_staged(self):
        """`pages.json` staged não absolve uma dívida em `content/pages.json`:
        a comparação é por linha inteira, não por substring."""
        r = self.roda(
            'redesocial-completude: redesocial_prova_texto_ausente: F0-paginas-legais: '
            'content/pages.json nao contem "art. 42, I" fora de comentario\n',
            "pages.json\n",
        )
        self.assertEqual(r.returncode, 0, "substring nao pode casar")
        self.assertIn("ALHEIA:", r.stdout)

    def test_uso_incorreto_sai_2(self):
        """Exit 2 é distinto de 0 e 1: 'não consegui decidir' não pode ser lido
        como 'está tudo bem'."""
        r = subprocess.run([str(SCRIPT)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 2)
        r = self.roda("qualquer\n", "coisa\n")
        self.assertIn(r.returncode, (0, 1))
        faltando = subprocess.run(
            [str(SCRIPT), "/inexistente/a.txt", "/inexistente/b.txt"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(faltando.returncode, 2)


if __name__ == "__main__":
    unittest.main()
