"""Bancada de tools/generate-mapa-de-evidencia-stale.

Carrega o modulo REAL por compile() do texto e chama as funcoes dele — nunca
uma copia. A primeira bancada que eu escrevi hoje para a varredura irma
reimplementava a decisao, e 3 de 4 mutantes sobreviveram por isso.
"""
import json
import types
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools/generate-mapa-de-evidencia-stale"


def carrega():
    modulo = types.ModuleType("mapa_de_evidencia_stale")
    modulo.__file__ = str(FERRAMENTA)
    exec(compile(FERRAMENTA.read_text(encoding="utf-8"), str(FERRAMENTA), "exec"),
         modulo.__dict__)
    return modulo


MODULO = carrega()


def linha(gate, exit_code, tail):
    return {"gate": gate, "exit": exit_code, "tail": tail}


class CodigoDeErro(unittest.TestCase):
    def test_exige_tres_segmentos(self):
        """Dois segmentos casariam palavra comum: `no_such`, `not_found`,
        `open_failed` apareceriam em qualquer mensagem de erro do sistema."""
        self.assertEqual(MODULO.codigo_da_cauda("html_brotli_evidence_stale: x"),
                         "html_brotli_evidence_stale")
        self.assertEqual(MODULO.codigo_da_cauda("open /tmp/x: no such file"), "")
        # O caso que EXERCITA o `{2,}`: o de cima nao tem underscore nenhum e
        # passaria com qualquer quantificador. Na prova por mutacao, trocar
        # `{2,}` por `{1,}` SOBREVIVEU ate esta linha existir — asserção que
        # nao alcança a regra mede outra coisa.
        self.assertEqual(MODULO.codigo_da_cauda("erro: open_failed ao ler o arquivo"), "")
        self.assertEqual(MODULO.codigo_da_cauda("erro: cache_open_failed ao ler"),
                         "cache_open_failed")

    def test_o_primeiro_codigo_e_o_que_anuncia_a_causa(self):
        cauda = "check-x: primeiro_codigo_aqui: detalhe\n  segundo_codigo_qualquer: ruido"
        self.assertEqual(MODULO.codigo_da_cauda(cauda), "primeiro_codigo_aqui")

    def test_familia_e_o_sufixo(self):
        """`*_source_fingerprint_stale`, `*_input_stale` e `*_live_metrics_stale`
        sao o mesmo problema com nomes diferentes."""
        for codigo in ("html_brotli_evidence_stale", "vale_lint_input_stale",
                       "ptbr_wordfreq_live_metrics_stale"):
            self.assertEqual(MODULO.familia_do_codigo(codigo), "stale")


class PareamentoComOGerador(unittest.TestCase):
    def test_convencao_majoritaria_check_para_generate(self):
        self.assertEqual(MODULO.candidatos_de_gerador("check-html-minify")[0],
                         "tools/generate-html-minify")

    def test_o_sufixo_evidence_tambem_e_convencao(self):
        """Medido em 2026-09-10: check-html-minify e servido por
        tools/generate-html-minify-EVIDENCE, que existe. Parear so pela forma
        exata classificaria o gate como "sem produtor" e mandaria alguem
        escrever um gerador que ja esta la."""
        self.assertIn("tools/generate-html-minify-evidence",
                      MODULO.candidatos_de_gerador("check-html-minify"))
        self.assertIn("tools/generate-html-brotli",
                      MODULO.candidatos_de_gerador("check-html-brotli-evidence"))

    def test_gate_de_qualidade_pareia_com_gerador_de_evidencia(self):
        """Medido em 2026-09-11: o gate nomeia a QUALIDADE que afere e o
        produtor nomeia a EVIDENCIA que grava.

            check-ptbr-confusables-quality -> generate-ptbr-confusables-evidence

        Sem esta forma o gate saia na lista "sem produtor pareado", e quem
        lesse o mapa escreveria um gerador que ja existe no disco — o mesmo
        dano que a forma `-evidence` ja tinha corrigido, numa familia que a
        funcao ainda nao conhecia."""
        candidatos = MODULO.candidatos_de_gerador("check-ptbr-confusables-quality")
        self.assertIn("tools/generate-ptbr-confusables-evidence", candidatos)
        self.assertIn("tools/generate-ptbr-confusables", candidatos)
        # E o gate cujo nome nao termina em -quality nao ganha forma nova: a
        # regra e por sufixo, nao por adivinhacao.
        self.assertNotIn("tools/generate-html-minify-",
                         MODULO.candidatos_de_gerador("check-html-minify"))

    def test_escolhe_o_candidato_que_existe_no_disco(self):
        self.assertEqual(MODULO.gerador_irmao("check-html-minify"),
                         "tools/generate-html-minify-evidence")

    def test_sem_nenhum_candidato_no_disco_devolve_o_canonico(self):
        """A mensagem tem de dizer QUAL nome faltou — devolver vazio esconderia
        o que o leitor precisa procurar."""
        self.assertEqual(MODULO.gerador_irmao("check-nao-existe-mesmo-este"),
                         "tools/generate-nao-existe-mesmo-este")

    def test_nome_sem_prefixo_check_nao_e_mutilado(self):
        self.assertEqual(MODULO.candidatos_de_gerador("outro-nome")[0],
                         "tools/generate-outro-nome")


class Monta(unittest.TestCase):
    def test_so_exit_1_conta_como_reprovacao(self):
        """exit 124 (timeout), 75 (run-go-cmd-cached abortou) e 2 (inconclusivo)
        NAO sao reprovacao de conteudo — contá-los infla o numero que este mapa
        existe para apurar."""
        mapa = MODULO.monta([
            linha("check-a", 1, "a_b_stale: x"),
            linha("check-b", 124, "b_c_stale: x"),
            linha("check-c", 75, "c_d_stale: x"),
            linha("check-d", 2, "d_e_stale: x"),
            linha("check-e", 0, "ok"),
        ])
        self.assertEqual(mapa["reprovacoes_exit_1"], 1)
        self.assertEqual(mapa["por_familia"], {"stale": 1})

    def test_separa_quem_tem_produtor_de_quem_nao_tem(self):
        """O `check-varredura-bateria-gates` nao existe como generate-, e
        `check-html-brotli-evidence` existe — os dois entram, em listas
        diferentes."""
        mapa = MODULO.monta([
            linha("check-html-brotli-evidence", 1, "html_brotli_evidence_stale: x"),
            linha("check-nao-existe-mesmo-este", 1, "nao_existe_mesmo_stale: x"),
        ])
        com = [i["gate"] for i in mapa["com_gerador_irmao"]]
        sem = [i["gate"] for i in mapa["sem_gerador_irmao"]]
        self.assertIn("check-html-brotli-evidence", com)
        self.assertIn("check-nao-existe-mesmo-este", sem)

    def test_a_contagem_por_familia_nao_encolhe_com_o_recorte(self):
        """`por_familia` conta a POPULACAO de reprovacoes; o recorte so escolhe
        qual familia detalhar. Se encolhesse junto, a fracao mentiria para cima —
        o mesmo defeito que o medidor de dispositivos corrigiu hoje."""
        entrada = [
            linha("check-a", 1, "a_b_stale: x"),
            linha("check-b", 1, "b_c_mismatch: x"),
            linha("check-c", 1, "c_d_failed: x"),
        ]
        for alvo in ("stale", "mismatch", "failed"):
            mapa = MODULO.monta(entrada, alvo)
            self.assertEqual(mapa["por_familia"], {"stale": 1, "mismatch": 1, "failed": 1},
                             "recorte %s encolheu a populacao" % alvo)

    def test_reprovacao_sem_codigo_conta_mas_nao_entra_em_familia(self):
        """33 dos 149 nao emitem codigo estruturado. Eles sao reprovacao real e
        precisam aparecer no total; atribuir familia a eles seria inventar."""
        mapa = MODULO.monta([linha("check-x", 1, "REPROVADO: 3 paginas sem fonte")])
        self.assertEqual(mapa["reprovacoes_exit_1"], 1)
        self.assertEqual(mapa["por_familia"], {})
        self.assertEqual(mapa["com_gerador_irmao"], [])
        self.assertEqual(mapa["sem_gerador_irmao"], [])



class PareamentoPorCodigoDeErro(unittest.TestCase):
    """Dois gates que reprovam pelo MESMO código leem a MESMA evidência.

    O par `check-X` / `check-X-release` é o caso típico e aparece três vezes na
    varredura de 2026-09-10: `source-family-policy` reprova com
    `source_registry_v2_stale`, o mesmo código de `check-source-registry-v2`,
    que TEM produtor. Parear só por nome classificava os dois primeiros como
    "sem produtor" — 9 na primeira versão, 5 depois do sufixo `-evidence`, 2
    depois desta regra.
    """

    def test_gate_sem_nome_pareado_herda_o_produtor_do_MESMO_codigo(self):
        mapa = MODULO.monta([
            linha("check-html-minify", 1, "html_minify_evidence_stale: x"),
            linha("check-html-minify-release", 1, "html_minify_evidence_stale: x"),
        ])
        self.assertEqual(len(mapa["sem_gerador_irmao"]), 0)
        por = {i["gate"]: i for i in mapa["com_gerador_irmao"]}
        self.assertEqual(por["check-html-minify"]["pareado_por"], "nome")
        self.assertEqual(por["check-html-minify-release"]["pareado_por"], "codigo")
        self.assertEqual(por["check-html-minify-release"]["gerador"],
                         por["check-html-minify"]["gerador"])

    def test_codigo_sem_nenhum_produtor_continua_sem(self):
        """A herança não pode inventar: se NENHUM gate daquele código tem
        produtor, os dois continuam na lista que precisa de nome."""
        mapa = MODULO.monta([
            linha("check-nao-existe-a", 1, "codigo_orfao_qualquer_stale: x"),
            linha("check-nao-existe-b", 1, "codigo_orfao_qualquer_stale: x"),
        ])
        self.assertEqual(len(mapa["com_gerador_irmao"]), 0)
        self.assertEqual(len(mapa["sem_gerador_irmao"]), 2)

    def test_o_pareamento_por_nome_tem_precedencia(self):
        """Nome nomeia o produtor DAQUELE gate; código só resolve o que sobra.
        Inverter faria um gate com produtor próprio herdar o do vizinho."""
        mapa = MODULO.monta([
            linha("check-html-minify", 1, "compartilhado_por_dois_stale: x"),
            linha("check-html-brotli-evidence", 1, "compartilhado_por_dois_stale: x"),
        ])
        por = {i["gate"]: i for i in mapa["com_gerador_irmao"]}
        self.assertEqual(por["check-html-minify"]["gerador"],
                         "tools/generate-html-minify-evidence")
        self.assertEqual(por["check-html-brotli-evidence"]["gerador"],
                         "tools/generate-html-brotli-evidence")
        for item in mapa["com_gerador_irmao"]:
            self.assertEqual(item["pareado_por"], "nome")

if __name__ == "__main__":
    unittest.main()
