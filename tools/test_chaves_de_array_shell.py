#!/usr/bin/env python3
"""Bancada de tools/check-chaves-de-array-shell.

A guarda nasce de um defeito REAL: o commit d4c942f2 espacou 8 chaves de array
associativo em tools/run-daily-content e cegou o gate diario por cinco dias.
`bash -n` aprovava. As fixtures abaixo sao as linhas verbatim daquele commit.

PROVA POR MUTACAO: se o predicado da guarda for desligado (parar de exigir o
espaco, parar de delimitar o bloco do array, ou aceitar array indexado), pelo
menos um destes testes fica vermelho. Teste que nao morre com mutante e
decorativo.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "check-chaves-de-array-shell"


def carrega_modulo():
    """Importa a ferramenta, que nao tem extensao .py."""
    spec = importlib.util.spec_from_loader(
        "check_chaves_de_array_shell",
        importlib.machinery.SourceFileLoader("check_chaves_de_array_shell", str(FERRAMENTA)),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


MOD = carrega_modulo()


# As 8 linhas verbatim do defeito de d4c942f2, com o contexto de comentario que
# separava os dois blocos -- o comentario importa: a guarda tem de continuar
# dentro do array ao atravessa-lo.
CORROMPIDO = """#!/usr/bin/env bash
declare -A COLETORES=(
\t[stj - precedentes]="./cmd/collect-stj-precedentes"
\t[stf - informativo]="./cmd/collect-stf-informativo"
\t# -com-texto 60: o texto integral da norma.
\t[normas - federais]="./cmd/collect-normas-federais -limite 60 -com-texto 60"
\t[diarios - municipais]="./cmd/collect-diarios-municipais -limite 300"
\t[noticias - oficiais]="./cmd/collect-noticias-oficiais -limite 200"
)

declare -A GERADORES=(
\t[stj - tema]="./cmd/generate-stj-tema-pages -limite 200"
\t[stj - sumula]="./cmd/generate-stj-sumula-pages -limite 80"
\t[stf - informativo]="./cmd/generate-stf-informativo-pages -limite 60"
\t[noticias]="./cmd/generate-noticia-pages -limite 40"
\t[diarios]="./cmd/generate-diario-pages -limite 30"
)
"""

CORRIGIDO = CORROMPIDO.replace(" - ", "-")


def escreve(conteudo: str) -> Path:
    arquivo = Path(tempfile.mkdtemp(prefix="chaves-array-")) / "script.sh"
    arquivo.write_text(conteudo, encoding="utf-8")
    return arquivo


class TesteDeteccao(unittest.TestCase):
    def test_pega_as_oito_chaves_do_defeito_real(self):
        achados = MOD.achados_no_arquivo(escreve(CORROMPIDO))
        self.assertEqual(
            len(achados), 8, f"esperava as 8 chaves de d4c942f2, achei {len(achados)}: {achados}"
        )
        chaves = [chave for _, _, chave in achados]
        self.assertIn("noticias - oficiais", chaves)
        self.assertIn("stj - tema", chaves)

    def test_nomeia_o_array_e_a_linha(self):
        achados = MOD.achados_no_arquivo(escreve(CORROMPIDO))
        linha, array, chave = achados[0]
        self.assertEqual(linha, 3, "a primeira chave corrompida esta na linha 3 da fixture")
        self.assertEqual(array, "COLETORES")
        self.assertEqual(chave, "stj - precedentes")

    def test_arquivo_corrigido_nao_acusa(self):
        self.assertEqual(MOD.achados_no_arquivo(escreve(CORRIGIDO)), [])

    def test_atravessa_comentario_dentro_do_array(self):
        """Comentario no meio do bloco nao pode encerrar o array.

        Mutante que fecha o array no primeiro comentario acha 2 em vez de 8:
        perderia justamente normas-federais, diarios-municipais e
        noticias-oficiais -- as tres que mais doeram.
        """
        achados = MOD.achados_no_arquivo(escreve(CORROMPIDO))
        depois_do_comentario = [ch for _, _, ch in achados if ch.startswith(("normas", "diarios", "noticias"))]
        self.assertEqual(len(depois_do_comentario), 3, achados)


class TesteControleNegativo(unittest.TestCase):
    """Sem controle negativo, uma guarda que acusa tudo passaria nos testes acima."""

    def test_array_indexado_com_aritmetica_nao_e_acusado(self):
        """Em array INDEXADO, espaco no subscript e aritmetica legitima.

        E a outra metade do defeito: o shfmt espacou as chaves porque leu
        `[stj-precedentes]` como subtracao -- o que num `declare -a` seria
        correto. A fixture tem de trazer uma entrada `[chave]=` de verdade,
        senao nao testa nada: a primeira versao deste teste usava um array sem
        nenhuma entrada indexada e SOBREVIVEU ao mutante que aceita `-a`.
        """
        fonte = (
            "#!/bin/bash\n"
            "n=2\n"
            "declare -a LISTA=(\n"
            '\t[0]="zero"\n'
            '\t[n + 1]="indice calculado, legitimo em array indexado"\n'
            ")\n"
        )
        self.assertEqual(MOD.achados_no_arquivo(escreve(fonte)), [])

    def test_comparacao_com_espaco_fora_de_array_nao_e_acusada(self):
        fonte = '#!/bin/bash\nif [[ "$x" == "a b" ]]; then echo oi; fi\n[ "$y" = "c d" ] && echo tchau\n'
        self.assertEqual(MOD.achados_no_arquivo(escreve(fonte)), [])

    def test_fora_de_bloco_de_array_nao_e_acusado(self):
        """`[a b]=` solto no arquivo nao e entrada de array associativo."""
        fonte = '#!/bin/bash\necho ok\n[chave com espaco]=valor\n'
        self.assertEqual(MOD.achados_no_arquivo(escreve(fonte)), [])

    def test_chave_com_espaco_deliberada_ainda_e_acusada(self):
        """Se alguem quiser mesmo uma chave com espaco, a guarda acusa.

        E correto: neste repo toda chave de array associativo e comparada por
        string exata em algum ponto, e o custo de um falso positivo aqui e uma
        linha de excecao -- contra cinco dias de gate cego no outro lado.
        """
        fonte = '#!/bin/bash\ndeclare -A M=(\n\t[nome composto]="x"\n)\n'
        self.assertEqual(len(MOD.achados_no_arquivo(escreve(fonte))), 1)


class TesteBlindagemContraOShfmt(unittest.TestCase):
    """A guarda detecta o defeito; as ASPAS impedem que ele nasca.

    Medido em 2026-09-16, DEPOIS de a frente P2 restaurar as 8 chaves: o shfmt
    v3.13.1 continuava querendo reescreve-las com espaco -- ou seja, a correcao
    sobreviveria ate a proxima vez que alguem rodasse
    tools/generate-shell-script-quality-evidence, que ESCREVE. Corrigir sem
    blindar era deixar uma bomba com o pino solto.

    Chave entre aspas o shfmt nao toca (nao e expressao aritmetica), e o bash
    casa exatamente igual. Duas camadas: as aspas impedem, a guarda detecta se
    alguem as remover.
    """

    SHFMT = RAIZ / ".cache" / "tools" / "shfmt-v3.13.1"

    def test_chave_com_aspas_sobrevive_ao_shfmt(self):
        if not self.SHFMT.is_file():
            self.skipTest("shfmt nao construido; tools/check-shell-script-quality o constroi")
        fonte = (
            "#!/usr/bin/env bash\n"
            "declare -A A=(\n"
            '\t["com-aspas"]="y"\n'
            "\t[sem-aspas]=\"x\"\n"
            ")\n"
        )
        arquivo = escreve(fonte)
        saida = subprocess.run([str(self.SHFMT), str(arquivo)], capture_output=True, text=True)
        self.assertEqual(saida.returncode, 0, saida.stderr)
        self.assertIn('["com-aspas"]', saida.stdout, "o shfmt nao pode tocar em chave com aspas")
        self.assertIn("[sem - aspas]", saida.stdout, "controle positivo: sem aspas ELE espaca")

    def test_run_daily_content_usa_aspas_em_todas_as_chaves(self):
        """Trava o arquivo que originou o incidente."""
        fonte = (RAIZ / "tools" / "run-daily-content").read_text(encoding="utf-8")
        dentro, sem_aspas = False, []
        for numero, linha in enumerate(fonte.splitlines(), start=1):
            if linha.startswith("declare -A "):
                dentro = True
                continue
            if dentro and linha.strip() == ")":
                dentro = False
                continue
            if dentro and linha.lstrip().startswith("[") and "]=" in linha:
                chave = linha.lstrip()[1 : linha.lstrip().index("]=")]
                if not (chave.startswith(('"', "'")) and chave.endswith(('"', "'"))):
                    sem_aspas.append((numero, chave))
        self.assertEqual(
            sem_aspas, [], f"chave sem aspas em run-daily-content: {sem_aspas} — o shfmt a espacara"
        )

    def test_o_shfmt_nao_quer_mudar_as_chaves_do_arquivo_real(self):
        if not self.SHFMT.is_file():
            self.skipTest("shfmt nao construido")
        alvo = RAIZ / "tools" / "run-daily-content"
        d = subprocess.run([str(self.SHFMT), "-d", str(alvo)], capture_output=True, text=True)
        mudancas_em_chave = [
            l for l in d.stdout.splitlines() if l[:1] in "+-" and "]=" in l and l[1:2] not in "+-"
        ]
        self.assertEqual(mudancas_em_chave, [], "o shfmt voltou a querer reescrever as chaves")


class TesteIntegracao(unittest.TestCase):
    def test_repo_limpo_sai_zero(self):
        proc = subprocess.run([str(FERRAMENTA)], capture_output=True, text=True, cwd=str(RAIZ))
        self.assertEqual(proc.returncode, 0, f"stdout={proc.stdout}\nstderr={proc.stderr}")

    def test_run_daily_content_nao_regride(self):
        """O arquivo que originou a guarda fica travado por nome."""
        alvo = RAIZ / "tools" / "run-daily-content"
        self.assertTrue(alvo.is_file(), "tools/run-daily-content sumiu")
        self.assertEqual(MOD.achados_no_arquivo(alvo), [])

    def test_ferramenta_e_read_only(self):
        """check-* que escreve e falha de ferramenta (precedente BUG-236)."""
        fonte = FERRAMENTA.read_text(encoding="utf-8")
        for proibido in ("write_text(", "os.remove", "shutil.rmtree", ".mkdir(", "os.rename"):
            self.assertNotIn(proibido, fonte, f"a guarda nao pode escrever: achei {proibido}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
