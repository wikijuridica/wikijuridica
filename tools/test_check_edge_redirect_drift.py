#!/usr/bin/env python3
"""Testes de check-edge-redirect-drift, com o falso positivo real que ele produziu.

Na primeira execução o gate acusou 10.480 arquivos, e os 10.480 eram falso
positivo: `index.html.br` é variante pré-comprimida, entregue por negociação de
`Accept-Encoding` sobre a URL do arquivo original — ninguém pede
`/pagina/index.html.br`. Este arquivo existe para que essa correção não se
perca, e para provar os dois sentidos: que o detector deixa passar o que é
legítimo E que ainda acusa o acoplamento real.
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(RAIZ, "tools", "check-edge-redirect-drift")

_spec = importlib.util.spec_from_loader(
    "check_edge_redirect_drift",
    importlib.machinery.SourceFileLoader("check_edge_redirect_drift", ALVO),
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class TestVarianteComprimida(unittest.TestCase):
    """O falso positivo medido: variante pré-comprimida não é endereçável."""

    def _servidos(self, arquivos: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            for caminho, conteudo in arquivos.items():
                completo = os.path.join(tmp, caminho)
                os.makedirs(os.path.dirname(completo), exist_ok=True)
                with open(completo, "w", encoding="utf-8") as fh:
                    fh.write(conteudo)
            original = gate.PUBLICO
            gate.PUBLICO = tmp
            try:
                return gate.arquivos_servidos_pelo_nome()
            finally:
                gate.PUBLICO = original

    def test_br_com_original_ao_lado_nao_conta(self):
        servidos = self._servidos(
            {"familia/x/index.html": "<html>", "familia/x/index.html.br": "comprimido"}
        )
        self.assertEqual(
            servidos,
            [],
            "variante .br com o original ao lado voltou a ser contada — "
            "era este o falso positivo de 10.480 arquivos",
        )

    def test_br_orfao_conta(self):
        """Sem o original ao lado, o .br não é variante de nada: é arquivo."""
        servidos = self._servidos({"orfao/perdido.br": "comprimido"})
        self.assertEqual(
            servidos,
            ["/orfao/perdido.br"],
            "um .br sem original sumiu da verificação; a exclusão virou cega",
        )

    def test_folha_de_estilo_conta(self):
        servidos = self._servidos({"assets/wj-abc.css": "body{}"})
        self.assertEqual(servidos, ["/assets/wj-abc.css"])


class TestExpressao(unittest.TestCase):
    """O detector acusa o acoplamento real e absolve o que está excluído."""

    EXPRESSAO_SEM_ASSETS = (
        'not ends_with(http.request.uri.path, "/") '
        'and not ends_with(http.request.uri.path, ".html")'
    )
    EXPRESSAO_COM_ASSETS = (
        EXPRESSAO_SEM_ASSETS + ' and not starts_with(http.request.uri.path, "/assets/")'
    )

    def test_css_sem_exclusao_seria_redirecionado(self):
        self.assertTrue(
            gate.seria_redirecionado("/assets/wj-abc.css", self.EXPRESSAO_SEM_ASSETS),
            "o detector não acusa a folha de estilo tomando 301 — era o defeito que "
            "tiraria o estilo das 10.141 páginas",
        )

    def test_css_com_exclusao_de_prefixo_sobrevive(self):
        self.assertFalse(
            gate.seria_redirecionado("/assets/wj-abc.css", self.EXPRESSAO_COM_ASSETS)
        )

    def test_extensao_excluida_sobrevive(self):
        self.assertFalse(
            gate.seria_redirecionado("/robots.html", self.EXPRESSAO_SEM_ASSETS)
        )


class TestRegraVersionada(unittest.TestCase):
    """A regra que está no repositório hoje não quebra nada que já é servido."""

    def test_nenhum_arquivo_servido_seria_redirecionado(self):
        declaradas = gate.carrega_declarado()
        self.assertTrue(declaradas, "o repositório deixou de declarar regra de redirect")
        servidos = gate.arquivos_servidos_pelo_nome()
        if not servidos:
            self.skipTest("public/ ausente nesta árvore; nada servido a verificar")
        for regra in declaradas:
            if not regra.get("enabled", True):
                continue
            quebrados = [
                p for p in servidos if gate.seria_redirecionado(p, regra["expression"])
            ]
            self.assertEqual(
                quebrados[:5],
                [],
                f"a regra versionada redirecionaria {len(quebrados)} arquivo(s) servido(s)",
            )

    def test_assets_das_duas_superficies_estao_excluidos(self):
        """O acervo e a rede social servem folha por caminho próprio; os dois
        prefixos têm de constar, senão aplicar a regra apaga o estilo."""
        expressao = gate.carrega_declarado()[0]["expression"]
        prefixos = gate.prefixos_excluidos(expressao)
        self.assertIn("/assets/", prefixos)
        self.assertIn("/redesocial/assets/", prefixos)


class TestSuperficieSocial(unittest.TestCase):
    """A rede social não passa por public/, e era por isso que o gate saía verde
    sem nunca ter olhado para /redesocial/assets/."""

    def _com_fonte(self, conteudo: str):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "socialheaders.go")
            with open(caminho, "w", encoding="utf-8") as fh:
                fh.write(conteudo)
            return gate.caminhos_servidos_pela_rede_social(caminho)

    def test_deriva_a_folha_do_repositorio_real(self):
        caminhos, erro = gate.caminhos_servidos_pela_rede_social()
        self.assertIsNone(erro, f"a derivação falhou na árvore real: {erro}")
        self.assertEqual(len(caminhos), 1)
        self.assertRegex(
            caminhos[0],
            r"^/redesocial/assets/css/wj-social-[0-9a-f]{16}\.css$",
            "o caminho derivado não tem a forma da folha da rede social",
        )

    def test_fonte_ausente_reprova_em_vez_de_silenciar(self):
        caminhos, erro = gate.caminhos_servidos_pela_rede_social(
            "/opt/wiki/internal/socialheaders/arquivo-que-nao-existe.go"
        )
        self.assertEqual(caminhos, [])
        self.assertIsNotNone(
            erro,
            "sem a fonte o gate voltaria a medir só o public/ em silêncio — "
            "que é exatamente o defeito de origem",
        )

    def test_mencao_em_comentario_nao_e_declaracao(self):
        """A armadilha de sempre: o detector procura o literal e acha a prosa."""
        caminhos, erro = self._com_fonte(
            "package socialheaders\n"
            "// PrefixoDeEstilo = \"https://wikijuridica.com.br/redesocial/assets/css/x.css\"\n"
        )
        self.assertEqual(caminhos, [])
        self.assertIsNotNone(erro)

    def test_raiz_dos_assets_reprova(self):
        """URL terminando no diretório daria escopo de diretório a style-src."""
        caminhos, erro = self._com_fonte(
            'package socialheaders\n'
            'const PrefixoDeEstilo = "https://wikijuridica.com.br/redesocial/assets/"\n'
        )
        self.assertEqual(caminhos, [])
        self.assertIn("RAIZ", (erro or "").upper())

    def test_folha_fora_do_prefixo_reprova(self):
        """A folha do ACERVO não é servida pela location social."""
        caminhos, erro = self._com_fonte(
            'package socialheaders\n'
            'const PrefixoDeEstilo = "https://wikijuridica.com.br/assets/wj-abc.css"\n'
        )
        self.assertEqual(caminhos, [])
        self.assertIsNotNone(erro)


class TestMainMedeAsDuasSuperficies(unittest.TestCase):
    """Prova por mutação: sem a exclusão, o gate ACUSA a folha da rede social.

    A zona nunca é consultada aqui — `le_zona` é substituída pelo que o próprio
    arquivo de regra declara, para que o teste rode sem credencial, sem rede e
    dentro dos 60 s que tools/run-qualidade-diaria concede.
    """

    EXCLUSAO = ' and not starts_with(http.request.uri.path, "/redesocial/assets/")'

    def _roda(self, regras: list[dict]) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "regras.json")
            with open(caminho, "w", encoding="utf-8") as fh:
                json.dump({"rules": regras}, fh, ensure_ascii=False)
            original = gate.le_zona
            gate.le_zona = lambda: (regras, None)
            saida, erro = io.StringIO(), io.StringIO()
            try:
                with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
                    codigo = gate.main(["--regras", caminho])
            finally:
                gate.le_zona = original
            return codigo, saida.getvalue(), erro.getvalue()

    def test_sem_a_exclusao_o_gate_acusa_a_folha_social(self):
        regras = gate.carrega_declarado()
        self.assertIn(
            self.EXCLUSAO,
            regras[0]["expression"],
            "a regra versionada perdeu a exclusão de /redesocial/assets/",
        )
        regras[0]["expression"] = regras[0]["expression"].replace(self.EXCLUSAO, "")
        codigo, _, erro = self._roda(regras)
        self.assertEqual(codigo, 1, "o gate aprovou uma regra que mata a folha da rede social")
        self.assertIn("/redesocial/assets/css/wj-social-", erro)

    def test_com_a_exclusao_o_gate_aprova_e_conta_as_duas_fontes(self):
        codigo, saida, erro = self._roda(gate.carrega_declarado())
        self.assertEqual(codigo, 0, f"o gate reprovou a regra real: {erro}")
        self.assertIn("da rede social", saida)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
