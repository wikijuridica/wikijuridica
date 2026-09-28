"""Bancada da classificação de aplicabilidade de tools/generate-varredura-bateria-gates.

POR QUE ELA EXISTE. A varredura mede o exit code real de cada `tools/check-*`
chamando-o SEM argumento — correto para a esmagadora maioria, que roda sozinha.
Os que pedem parâmetro não estão reprovando: estão dizendo que a chamada é que
faltou. Contá-los como vermelho infla o número que a varredura existe para
apurar.

A regra do prefixo `uso:`/`usage:` já existia e pegava 5 dos 7 casos da
primeira varredura completa (2026-09-10). `check-onda-avanca` escapava porque
escreve "informe --antes ou --depois" — sem o prefixo — e entrava na conta de
177 vermelhos. O número real era 149.

Carrega a regra por compile() do TEXTO do arquivo, não por import de nome:
tools/ não é pacote, e SourceFileLoader já serviu bytecode velho nesta casa.
"""
import re
import types
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools/generate-varredura-bateria-gates"


def carrega():
    """Recorta a DECISAO REAL do arquivo — a funcao, nao uma copia dela.

    A primeira versao desta bancada reimplementava a regra aqui dentro, e a
    prova por mutacao denunciou: 3 de 4 mutantes SOBREVIVERAM, porque mudar o
    arquivo real nao mudava a copia local. E a memoria
    `teste-que-reimplementa-nao-testa` deste repositorio, exercida contra quem a
    escreveu.
    """
    fonte = FERRAMENTA.read_text(encoding="utf-8")
    inicio = fonte.index("def aplicavel_sem_argumento(")
    fim = fonte.index("def main()", inicio)
    modulo = types.ModuleType("varredura_bateria_gates")
    exec(compile("import re\n" + fonte[inicio:fim], str(FERRAMENTA), "exec"), modulo.__dict__)
    return modulo


MODULO = carrega()


def classifica(texto, codigo):
    return MODULO.aplicavel_sem_argumento(texto, codigo)


class FaltaDeArgumentoNaoEVermelho(unittest.TestCase):
    def test_mensagem_de_uso_continua_reconhecida(self):
        """A regra antiga não pode ter regredido: ela pegava 5 dos 7."""
        for texto in (
            "uso: check-baseline-testes-vermelhos <log-do-go-test>",
            "usage: check-v2-finalized-commit [-h] [--root ROOT] --old OLD",
            "erro: --agent é obrigatório\nUso: tools/check-coord-inbox --agent ID",
        ):
            self.assertFalse(classifica(texto, 2), texto)

    def test_exigencia_de_flag_sem_o_prefixo_uso(self):
        """O caso REAL que escapava: check-onda-avanca, exit 2, 2026-09-10."""
        self.assertFalse(classifica("check-onda-avanca: informe --antes ou --depois", 2))
        self.assertFalse(classifica("--root is required", 2))
        self.assertFalse(classifica("a flag --agent é obrigatória", 2))

    def test_reprovacao_real_com_exit_2_continua_contando(self):
        """`check-v2-portfolio-source-hints` sai com exit 2 e NÃO pede parâmetro:
        fala de catálogo irresolúvel. A regra é estreita de propósito."""
        self.assertTrue(classifica(
            "check-v2-portfolio-source-hints: source hint catalog entry is not resolvable", 2))

    def test_reprovacao_de_conteudo_nunca_e_confundida(self):
        for texto in (
            "REPROVADO: 3 pagina(s) sem fonte oficial",
            "politica governa 69 token(s) | telemetria identifica 77",
            "informe a data no formato AAAA-MM-DD",  # "informe" sem flag longa
        ):
            self.assertTrue(classifica(texto, 1), texto)
            self.assertTrue(classifica(texto, 2), texto)

    def test_a_exigencia_de_flag_so_vale_com_exit_2(self):
        """Exit 1 é reprovação de conteúdo por convenção da casa. Um gate que
        reprovasse dizendo 'informe --x' com exit 1 continua vermelho — a
        conjunção é o que mantém a regra estreita."""
        texto = "informe --antes ou --depois"
        self.assertFalse(classifica(texto, 2))
        self.assertTrue(classifica(texto, 1))

    def test_so_as_duas_primeiras_linhas_contam(self):
        """Mensagem de uso no RODAPÉ de um relatório de reprovação não pode
        converter o veredito — senão qualquer gate que imprima a própria ajuda
        no fim vira 'não aplicável'."""
        texto = "REPROVADO: 12 itens\n  detalhe...\nuso: check-x --flag"
        self.assertTrue(classifica(texto, 2))


class TestLinhasDeErro(unittest.TestCase):
    """O `tail` guarda o FIM da saida, e o fim e onde mora o motivo mais raso.

    Medido em 2026-09-11: check-ptbr-confusables-quality saiu na varredura como
    `ptbr_confusables_live_metrics_stale` enquanto embaixo estava
    `ptbr_confusables_blockers: dangerous=1` — um homoglifo cirilico numa pagina
    publicada. Gravar so o tail fez a varredura registrar o motivo raso e
    propagar o ponto cego para a triagem seguinte.
    """

    def test_guarda_todas_as_linhas_com_codigo_de_erro(self):
        texto = (
            "run-check: executing cached check binary\n"
            "TIMING check=x status=start\n"
            "x: ptbr_confusables_blockers: records=1 mixed=1 dangerous=1\n"
            "x: ptbr_confusables_live_metrics_stale: data/editorial/arquivo.jsonl\n"
        )
        erros = MODULO.linhas_de_erro(texto)
        self.assertTrue(any("ptbr_confusables_blockers" in l for l in erros),
                        "o motivo do DADO ficou de fora: %r" % erros)
        self.assertTrue(any("ptbr_confusables_live_metrics_stale" in l for l in erros))

    def test_linha_sem_codigo_de_erro_nao_entra(self):
        texto = "tudo certo por aqui\nnenhum diagnostico nesta linha\n"
        self.assertEqual(MODULO.linhas_de_erro(texto), [])

    def test_teto_de_linhas_e_de_tamanho(self):
        texto = "\n".join("x: codigo_de_erro_numero_%d: %s" % (i, "a" * 500)
                          for i in range(100))
        erros = MODULO.linhas_de_erro(texto)
        self.assertEqual(len(erros), 40, "sem teto, um gate verboso incha o registro")
        self.assertTrue(all(len(l) <= 300 for l in erros))

    def test_texto_vazio_nao_quebra(self):
        self.assertEqual(MODULO.linhas_de_erro(""), [])
        self.assertEqual(MODULO.linhas_de_erro(None), [])


if __name__ == "__main__":
    unittest.main()
