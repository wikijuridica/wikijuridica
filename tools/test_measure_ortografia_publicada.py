#!/usr/bin/env python3
"""Prova que o censo de ortografia NAO acusa endereco, e que continua acusando erro.

POR QUE ESTE TESTE NASCE EM 2026-09-10. Os quatro tokens de maior alcance do
censo exato eram `br` (1.658 paginas), `gov` (1.604), `Gov` (69) e `ans` (16),
mais `jurisprudencia` (10) — nenhum erro de portugues, todos pedacos de
`Consumidor.gov.br`, `(gov.br/ans)` e `/jurisprudencia/stj-tema-1261/` partidos
pelo tokenizador do proprio instrumento. Falso positivo de instrumento e pior
que erro nao achado: ele manda corrigir texto correto.

O CONTROLE NEGATIVO E O QUE DA VALOR AO TESTE. Uma regra de endereco frouxa
engole prosa: `8.078` (numero de lei), `presumida.Assim` (fronteira de frase
perdida, que e defeito de verdade e tem de continuar visivel a quem mede) e
`erro` puro e simples. Os tres estao aqui, e uma regra que os engula reprova.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_loader(
    "measure_ortografia_publicada",
    importlib.machinery.SourceFileLoader(
        "measure_ortografia_publicada",
        str(RAIZ / "tools" / "measure-ortografia-publicada")))
medidor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(medidor)


# O TESTE EXERCITA `censo()`, NAO UMA REIMPLEMENTACAO DELE.
#
# A primeira versao deste arquivo reproduzia o pipeline aplicando os tres
# padroes a mao. Ela passava com a regra de caminho e a de URL DESLIGADAS na
# ferramenta — porque o teste nunca chamava o codigo que as usa. Instrumento que
# mede a si mesmo em vez de medir o alvo e o defeito que este repositorio ja
# nomeou em `detector-conta-em-vez-de-comparar-conjunto`; aqui ele apareceu
# dentro do proprio teste, e foi a bancada de mutacao que o denunciou (M3 e M5
# sobreviviam).
def censo_de(texto: str, allowlist: str = "") -> dict:
    """Roda o censo REAL sobre uma arvore temporaria com uma pagina so."""
    with tempfile.TemporaryDirectory() as raiz:
        base = pathlib.Path(raiz)
        pagina = base / "public" / "amostra"
        pagina.mkdir(parents=True)
        (pagina / "index.html").write_text(
            f"<html><body><p>{texto}</p></body></html>", encoding="utf-8")
        (base / "content").mkdir()
        (base / "content" / "ptbr_spellcheck_allowlist.txt").write_text(
            allowlist, encoding="utf-8")
        return medidor.censo(str(base), 1)


def tokens_de(texto: str) -> set[str]:
    """Os tokens que o censo REAL considerou — candidatos, nao so os reprovados."""
    return set(_ultimos_candidatos(texto))


def _ultimos_candidatos(texto: str) -> list[str]:
    capturados: list[str] = []
    original = medidor.subprocess.run

    def espiao(cmd, *args, **kwargs):
        capturados.extend((kwargs.get("input") or "").split("\n"))
        return original(cmd, *args, **kwargs)

    medidor.subprocess.run = espiao
    try:
        censo_de(texto)
    finally:
        medidor.subprocess.run = original
    return [c for c in capturados if c]


class EnderecoNaoEProsa(unittest.TestCase):
    def test_servico_federal_escrito_na_frase_nao_vira_token(self):
        tokens = tokens_de("Procon e Consumidor.gov.br podem mediar relacao de consumo")
        for pedaco in ("gov", "br", "Consumidor"):
            self.assertNotIn(pedaco, tokens, f"{pedaco!r} sobreviveu ao endereco")
        self.assertIn("mediar", tokens)

    def test_dominio_com_caminho_leva_o_caminho_junto(self):
        tokens = tokens_de("ANS, canais do consumidor (gov.br/ans) verificado hoje")
        for pedaco in ("gov", "br", "ans"):
            self.assertNotIn(pedaco, tokens, f"{pedaco!r} sobreviveu ao endereco")
        self.assertIn("consumidor", tokens)

    def test_caminho_do_proprio_portal_nao_vira_token(self):
        tokens = tokens_de("tese transcrita em /jurisprudencia/stj-tema-1261/ e comentada")
        self.assertNotIn("jurisprudencia", tokens)
        self.assertIn("transcrita", tokens)

    def test_url_absoluta_sai_inteira(self):
        tokens = tokens_de("consulte https://www.planalto.gov.br/ccivil_03/leis/l8078.htm hoje")
        for pedaco in ("www", "planalto", "ccivil", "htm"):
            self.assertNotIn(pedaco, tokens, f"{pedaco!r} sobreviveu a URL")
        self.assertIn("consulte", tokens)

    def test_dominio_depois_de_barra_em_prosa_tambem_sai(self):
        # `Celpe-Bras (Inep/gov.br)` e prosa, nao URL: o dominio vem depois de
        # uma barra escrita pelo redator. Com a barra na guarda de contexto,
        # `br` sobrevivia em 7 paginas do censo exato.
        tokens = tokens_de("o exame Celpe-Bras (Inep/gov.br) verifica o nivel")
        self.assertNotIn("br", tokens)
        self.assertNotIn("gov", tokens)

    def test_extensao_escrita_com_ponto_na_frente_tambem_sai(self):
        tokens = tokens_de('os sites autorizados usam a extensao ".bet.br" no endereco')
        self.assertNotIn("br", tokens)
        self.assertNotIn("bet", tokens)
        self.assertIn("autorizados", tokens)

    def test_dominio_em_caixa_alta_tambem_sai(self):
        self.assertNotIn("Fala", tokens_de("registre manifestacao no Fala.BR hoje"))


class OQueNaoPodeSerEngolido(unittest.TestCase):
    """Os controles negativos: regra frouxa de endereco apaga prosa."""

    def test_numero_de_lei_nao_e_endereco(self):
        self.assertIn("Lei", tokens_de("a Lei 8.078 de 1990 protege"))

    def test_fronteira_de_frase_perdida_continua_visivel(self):
        tokens = tokens_de("nao pode ser presumida.Assim, a data")
        self.assertIn("presumida", tokens)
        self.assertIn("Assim", tokens)

    def test_abertura_de_frase_com_Com_nao_e_engolida_como_dominio(self):
        # `Com` abre frase em portugues juridico o tempo todo. Se `com` estivesse
        # em DOMINIO_DE_TOPO, `anterior.Com efeito` casaria e o instrumento
        # apagaria a palavra ANTES do ponto — a que ele existe para medir.
        tokens = tokens_de("havia entendimento anteriorr.Com efeito, a Turma decidiu")
        self.assertIn("anteriorr", tokens)
        self.assertIn("Com", tokens)

    def test_nome_de_arquivo_na_frase_nao_vira_token(self):
        tokens = tokens_de("recuse em uma linha de robots.txt, veja "
                           "/datasets/datasets.json e o index.md da gemea")
        for pedaco in ("txt", "json", "md", "robots"):
            self.assertNotIn(pedaco, tokens, f"{pedaco!r} sobreviveu ao arquivo")
        self.assertIn("recuse", tokens)

    def test_palavra_terminada_como_extensao_nao_e_arquivo(self):
        # Controle: a regra exige o PONTO. Sem ele, `md` e `txt` continuam
        # tokens, e uma palavra que por acaso termine assim nao e engolida.
        tokens = tokens_de("o formato md e o txt sao lidos por maquina")
        self.assertIn("md", tokens)
        self.assertIn("txt", tokens)

    def test_br_solto_sem_ponto_nao_e_endereco(self):
        # Controle do proprio remendo: uma regra com o ponto opcional casaria a
        # palavra `br` sozinha, e o instrumento passaria a apagar token em vez de
        # endereco. Aqui `br` tem de SOBREVIVER e ser medido.
        tokens = tokens_de("a sigla br aparece sozinha nesta frase")
        self.assertIn("br", tokens)

    def test_palavra_comum_continua_token(self):
        self.assertIn("anonimizacao", tokens_de("a anonimizacao do dado"))

    def test_sigla_de_orgao_sozinha_sai_como_SIGLA_e_nao_como_endereco(self):
        # `ANS` nunca chega ao hunspell — e isento por `e_sigla`, que espelha
        # `isAllowedAcronymToken`. O que este caso trava e que a regra de
        # endereco NAO se atribua o descarte: `enderecos_ignorados` tem de ficar
        # em zero aqui, senao os dois motivos passam a se confundir no artefato.
        estado = censo_de("a ANS regula os planos de saude")
        self.assertEqual(sum(estado["enderecos_ignorados"].values()), 0)
        self.assertNotIn("ANS", tokens_de("a ANS regula os planos de saude"))


class AutodescricaoDoArtefato(unittest.TestCase):
    """O artefato tem de dizer o que NAO esta nele, e com o nome da regra."""

    def test_toda_classe_de_descarte_esta_declarada_com_a_regra_que_a_aplica(self):
        motivos = medidor.DESCARTADO_MOTIVO
        exigido = {
            "sigla": "isAllowedAcronymToken",
            "allowlist": "ptbr_spellcheck_allowlist",
            "endereco": "DOMINIO_DE_TOPO",
            "curto_ou_numero": "digitos",
            "nao_descartado": "sem_origem",
        }
        for chave, marca in exigido.items():
            self.assertIn(chave, motivos)
            self.assertIn(marca, motivos[chave],
                          f"{chave} nao nomeia a regra que o aplica ({marca})")

    def test_censo_publica_a_autodescricao_e_a_contagem_de_enderecos(self):
        estado = censo_de("Procon e Consumidor.gov.br mediam; veja "
                          "/jurisprudencia/stj-tema-1261/ e "
                          "https://www.planalto.gov.br/l8078.htm")
        self.assertEqual(estado["descartado_motivo"], medidor.DESCARTADO_MOTIVO)
        ignorados = estado["enderecos_ignorados"]
        self.assertGreaterEqual(ignorados.get("url", 0), 1)
        self.assertGreaterEqual(ignorados.get("dominio", 0), 1)
        self.assertGreaterEqual(ignorados.get("caminho", 0), 1)


if __name__ == "__main__":
    unittest.main()
