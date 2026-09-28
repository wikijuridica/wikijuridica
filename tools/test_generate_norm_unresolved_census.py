"""Bancada de tools/generate-norm-unresolved-census.

A ferramenta e curta e o que ela protege e caro: um censo mal montado faz o
gerador do registro consultar a fonte oficial para a norma errada, ou — pior —
gravar um censo vazio que "passa" e deixa o registro parado no passado.

Carrega o modulo por compile() do TEXTO do arquivo, nunca por import de nome:
tools/ nao e pacote, e SourceFileLoader ja serviu bytecode velho neste
repositorio quando duas permutas do mesmo tamanho caem no mesmo segundo.
"""
import json
import tempfile
import types
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools/generate-norm-unresolved-census"


def carrega():
    modulo = types.ModuleType("generate_norm_unresolved_census")
    modulo.__file__ = str(FERRAMENTA)
    codigo = compile(FERRAMENTA.read_text(encoding="utf-8"), str(FERRAMENTA), "exec")
    exec(codigo, modulo.__dict__)
    return modulo


MODULO = carrega()


def relatorio(normas, **extra):
    base = {
        "paginas_renderizadas": 11051,
        "artigos": 11039,
        "artigos_citam_lei_sem_no_legislation": 22,
        "normas_nao_normalizadas": normas,
    }
    base.update(extra)
    return base


def norma(chave, paginas=1, ocorrencias=1, exemplo="Lei 1"):
    return {"chave_fallback": chave, "exemplo_texto": exemplo,
            "ocorrencias": ocorrencias, "paginas": paginas}


class MontaCenso(unittest.TestCase):
    def test_renomeia_a_chave_que_o_gerador_do_registro_le(self):
        censo = MODULO.monta_censo(relatorio([norma("lei-ref:lei:5194:1966")]),
                                   "2026-09-10")
        self.assertIn("normas", censo)
        self.assertNotIn("normas_nao_normalizadas", censo)
        self.assertEqual(censo["normas"][0]["chave_fallback"], "lei-ref:lei:5194:1966")

    def test_preserva_os_quatro_campos_e_descarta_o_resto(self):
        entrada = norma("lei-ref:lei:8078:1990", paginas=248, ocorrencias=250,
                        exemplo="Lei nº 8.078/1990")
        entrada["campo_que_o_medidor_pode_ganhar_depois"] = "ignorado"
        censo = MODULO.monta_censo(relatorio([entrada]), "2026-09-10")
        self.assertEqual(censo["normas"][0],
                         {"chave_fallback": "lei-ref:lei:8078:1990",
                          "exemplo_texto": "Lei nº 8.078/1990",
                          "ocorrencias": 250, "paginas": 248})

    def test_a_ordem_do_medidor_e_preservada(self):
        # O censo alimenta uma coleta com pausa de 1,1 s por norma. Se a ordem
        # se perder, quem interromper no meio deixa de fora justamente as de
        # maior alcance.
        # As chaves estao em ordem alfabetica INVERSA a de paginas de
        # proposito: com chaves crescentes, um mutante que ordenasse por
        # chave_fallback sobreviveria — e sobreviveu, na primeira versao
        # deste teste. Mutante vivo e a assercao dizendo que era fraca.
        entrada = [norma("lei-ref:lei:9111:1990", paginas=248),
                   norma("lei-ref:lei:5222:1990", paginas=7),
                   norma("lei-ref:lei:1333:1990", paginas=1)]
        censo = MODULO.monta_censo(relatorio(entrada), "2026-09-10")
        self.assertEqual([n["paginas"] for n in censo["normas"]], [248, 7, 1])
        self.assertEqual([n["chave_fallback"] for n in censo["normas"]],
                         ["lei-ref:lei:9111:1990", "lei-ref:lei:5222:1990",
                          "lei-ref:lei:1333:1990"])

    def test_totais_sao_derivados_do_conteudo_nao_copiados(self):
        # O medidor tambem publica os proprios totais. Copiá-los deixaria o
        # censo afirmar um numero que nao corresponde as linhas que ele traz —
        # exatamente o defeito de "detector que conta em vez de comparar".
        entrada = [norma("lei-ref:lei:1:1990", ocorrencias=3),
                   norma("lei-ref:lei:2:1990", ocorrencias=4)]
        censo = MODULO.monta_censo(
            relatorio(entrada, normas_distintas_nao_normalizadas=999,
                      ocorrencias_totais=999), "2026-09-10")
        self.assertEqual(censo["normas_distintas_nao_normalizadas"], 2)
        self.assertEqual(censo["ocorrencias_totais"], 7)

    def test_relatorio_de_outra_ferramenta_e_recusado(self):
        with self.assertRaises(SystemExit) as erro:
            MODULO.monta_censo({"paginas_renderizadas": 10}, "2026-09-10")
        self.assertIn("normas_nao_normalizadas", str(erro.exception))

    def test_norma_sem_campo_obrigatorio_e_recusada_com_o_nome_do_campo(self):
        incompleta = {"chave_fallback": "lei-ref:lei:1:1990", "ocorrencias": 1}
        with self.assertRaises(SystemExit) as erro:
            MODULO.monta_censo(relatorio([incompleta]), "2026-09-10")
        self.assertIn("exemplo_texto", str(erro.exception))
        self.assertIn("paginas", str(erro.exception))

    def test_censo_vazio_e_gravavel_mas_declara_zero(self):
        # Zero norma nao normalizada e o objetivo do projeto, nao um erro. O
        # que nao pode e o censo dizer zero quando o relatorio nao foi lido —
        # e isso quem impede e test_relatorio_de_outra_ferramenta_e_recusado.
        censo = MODULO.monta_censo(relatorio([]), "2026-09-10")
        self.assertEqual(censo["normas"], [])
        self.assertEqual(censo["ocorrencias_totais"], 0)

    def test_medicao_declara_a_populacao_contada(self):
        censo = MODULO.monta_censo(relatorio([]), "2026-09-10")
        self.assertIn("render offline", censo["medicao"])
        self.assertEqual(censo["ferramenta"], "cmd/measure-graph-authority")
        self.assertEqual(censo["gerado_em"], "2026-09-10")


class GravaAtomico(unittest.TestCase):
    def test_grava_e_substitui_sem_deixar_temporario(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "censo.json"
            MODULO.grava_atomico(destino, b'{"a":1}')
            self.assertEqual(json.loads(destino.read_text()), {"a": 1})
            MODULO.grava_atomico(destino, b'{"a":2}')
            self.assertEqual(json.loads(destino.read_text()), {"a": 2})
            self.assertEqual(sorted(p.name for p in Path(pasta).iterdir()),
                             ["censo.json"])


if __name__ == "__main__":
    unittest.main()
