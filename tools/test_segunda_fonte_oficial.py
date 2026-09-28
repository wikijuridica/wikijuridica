#!/usr/bin/env python3
"""tools/test_segunda_fonte_oficial.py — bancada de
tools/generate-v2-second-official-source-from-corpus-20260806.

A ferramenta existia desde 2026-08-06, escreve no estoque canonico v2 com
lease de epoca + lock exclusivo + CAS pela linha viva, e NAO TINHA NENHUM
TESTE. Esta bancada cobre as duas correcoes de 2026-09-16, e so elas:

1. `--dry-run` NAO toma o lease de escrita. Ate 2026-09-16 ele tomava, e com
   outra frente segurando a epoca do estoque a ferramenta abortava com exit 75
   sem imprimir uma linha do plano -- medido nesse dia, com 348 paginas de
   pauta que ninguem conseguiu ler. Planejar e leitura.

2. A guarda do MESMO ATO. O Planalto serve o mesmo diploma em mais de uma URL
   (`l10406.htm` e `l10406compilada.htm`), e a checagem antiga comparava URL
   literal. Medido sobre o plano real: 235 das 271 paginas que a ferramenta
   escreveria (86,7%) ganhariam uma segunda fonte DO MESMO DIPLOMA. O
   validador do ingest contaria as duas e o motivo
   `official_sources_insufficient` sumiria -- sem que a pagina tivesse ganhado
   a referencia independente que o motivo existe para exigir.

Rodar:
    python3 tools/test_segunda_fonte_oficial.py
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import os
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-v2-second-official-source-from-corpus-20260806"

_loader = importlib.machinery.SourceFileLoader("segunda_fonte_oficial", str(FERRAMENTA))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)


CC_BASE = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm"
CC_COMPILADA = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CDC = "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"
CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
FGTS_CONSOL = "https://www.planalto.gov.br/ccivil_03/leis/l8036consol.htm"
FGTS_BASE = "https://www.planalto.gov.br/ccivil_03/leis/l8036.htm"
CF_COM_WWW = "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"
CF_SEM_WWW = "https://planalto.gov.br/ccivil_03/constituicao/constituicao.htm"
# Calada no lexml e DENTRO do Planalto: a tabela de knowncodes.go elege
# `l8245compilado.htm`? Nao -- e `caminhoPlanaltoCanonico` recusa confirmar a
# variante que nao esta na lista. Medida em 2026-09-16 sobre o acervo vivo.
INQUILINATO_CALADA = "https://www.planalto.gov.br/ccivil_03/leis/l8245compilado.htm"
# Calada no lexml e FORA do Planalto: nao ha variante de URL a colidir.
CNJ = "https://atos.cnj.jus.br/atos/detalhar/3334"
SUSEP = ("https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/"
         "seguros-previdencia-e-capitalizacao/seguros/seguro-residencial")

TODAS = (CC_BASE, CC_COMPILADA, CDC, CPC, FGTS_CONSOL, FGTS_BASE, CF_COM_WWW,
         CF_SEM_WWW, INQUILINATO_CALADA, CNJ, SUSEP)


class AtoDoPlanaltoTest(unittest.TestCase):
    """`ato_do_planalto` consulta `internal/lexml` por `cmd/resolve-planalto-urn`
    desde 2026-09-16, e nao mais um regex sobre o radical do caminho.

    As URLs sao REAIS: saem de `data/editorial/v2_pages` e de
    `data/legal-corpus`. O lote de `setUpClass` nao e conveniencia de teste --
    e o mesmo caminho de codigo que a passada usa para nao pagar um `go run`
    por fonte."""

    @classmethod
    def setUpClass(cls):
        mod.resolver_urns(TODAS)

    def test_variantes_do_mesmo_ato_colapsam(self):
        """O caso que motiva a guarda: o Planalto serve o Codigo Civil em dois
        enderecos, e a pagina que registrasse os dois teria 'duas fontes' que
        sao a mesma."""
        self.assertEqual(mod.ato_do_planalto(CC_BASE), mod.ato_do_planalto(CC_COMPILADA))
        self.assertEqual(mod.ato_do_planalto(CC_BASE),
                         "urn:lex:br:federal:lei:2002-01-10;10406")

    def test_sufixo_consol_colapsa_com_a_forma_sem_sufixo(self):
        """A Lei 8.036 nao esta na tabela de codigos canonicos, entao o lexml
        parseia a URL sem exigir caminho conferido e as duas grafias caem na
        mesma URN. E o caso em que a regua nova faz o que a antiga fazia."""
        self.assertEqual(mod.ato_do_planalto(FGTS_CONSOL), mod.ato_do_planalto(FGTS_BASE))
        self.assertIsNotNone(mod.ato_do_planalto(FGTS_BASE))

    def test_atos_diferentes_nao_colapsam(self):
        """Controle negativo: a guarda tem de separar diplomas distintos, senao
        ela para de propor fonte legitima. CDC, CPC/2015 e CC/2002 sao tres."""
        atos = [mod.ato_do_planalto(u) for u in (CDC, CPC, CC_BASE)]
        self.assertNotIn(None, atos, atos)
        self.assertEqual(len(set(atos)), 3, atos)

    def test_constituicao_com_e_sem_www_e_o_mesmo_ato(self):
        """O ganho que a regua antiga nao dava: o caminho da Constituicao nao
        tem radical numerico, entao o regex devolvia a URL inteira e
        `planalto.gov.br` era um ato diferente de `www.planalto.gov.br`."""
        self.assertEqual(mod.ato_do_planalto(CF_COM_WWW), mod.ato_do_planalto(CF_SEM_WWW))
        self.assertEqual(mod.ato_do_planalto(CF_COM_WWW),
                         "urn:lex:br:federal:constituicao:1988-10-05;1988")

    def test_silencio_do_lexml_e_None_e_nao_a_propria_url(self):
        """None e a resposta "esta regua nao afirma nada". Devolver a URL no
        lugar faria duas URLs caladas parecerem dois atos distintos -- que e
        exatamente o fail-open que a guarda existe para impedir."""
        self.assertIsNone(mod.ato_do_planalto(CNJ))
        self.assertIsNone(mod.ato_do_planalto(INQUILINATO_CALADA))

    def test_host_separa_os_dois_silencios(self):
        self.assertEqual(mod.host_da_url(INQUILINATO_CALADA), "planalto.gov.br")
        self.assertEqual(mod.host_da_url(CF_SEM_WWW), "planalto.gov.br")
        self.assertEqual(mod.host_da_url(CNJ), "atos.cnj.jus.br")


class MesmoAtoJaRegistradoTest(unittest.TestCase):
    """A decisao propriamente dita. Medida em 2026-09-16 sobre o plano real de
    348 paginas: 208 puladas por MESMO ato, 29 por identidade nao resolvida, 34
    escritas -- contra 36 da regua antiga, e nenhuma pagina que a regua antiga
    barrava passou a ser escrita."""

    @classmethod
    def setUpClass(cls):
        mod.resolver_urns(TODAS)

    def test_mesmo_ato_por_outra_variante_de_url_pula(self):
        motivo = mod.mesmo_ato_ja_registrado(CC_BASE, [CC_COMPILADA])
        self.assertIn("MESMO ato", motivo)

    def test_ato_distinto_segue(self):
        """Controle positivo: sem ele, uma funcao que pulasse sempre passaria."""
        self.assertEqual(mod.mesmo_ato_ja_registrado(CPC, [CC_COMPILADA]), "")

    def test_fonte_registrada_fora_do_planalto_nao_bloqueia(self):
        """Medido: 4 das 6 paginas que uma guarda 'silencio = nao sei' pularia
        tinham a fonte registrada em atos.cnj.jus.br, processo.stj.jus.br ou
        gov.br/susep. Nenhuma URL do Planalto e outra grafia daquelas."""
        self.assertEqual(mod.mesmo_ato_ja_registrado(CPC, [CNJ]), "")
        self.assertEqual(mod.mesmo_ato_ja_registrado(CPC, [SUSEP, CNJ]), "")

    def test_fonte_registrada_calada_no_mesmo_host_pula(self):
        """O unico "nao sei" de verdade: o lexml nao resolve
        `l8245compilado.htm`, que esta no MESMO host da proposta. Sem URN nao se
        prova que sao atos distintos, e fonte so se acrescenta com prova."""
        motivo = mod.mesmo_ato_ja_registrado(CPC, [INQUILINATO_CALADA])
        self.assertIn("nao resolve", motivo)
        self.assertNotIn("MESMO ato", motivo)

    def test_proposta_calada_com_fonte_do_mesmo_host_pula(self):
        """Simetria: o lado calado pode ser o da proposta. Medido: as 27
        propostas caladas do plano (CPP, Codigo Penal e CTN, cujo
        `citation_url` do corpus nao e a URL que knowncodes.go elegeu) tinham
        TODAS uma fonte do Planalto ja registrada."""
        motivo = mod.mesmo_ato_ja_registrado(INQUILINATO_CALADA, [CC_BASE])
        self.assertIn("nao resolve", motivo)

    def test_proposta_calada_com_fonte_de_outro_host_segue(self):
        """E a simetria do outro lado: sem disputa de espaco de endereco nao ha
        duplicata cosmetica possivel, e pular ali so custaria refino."""
        self.assertEqual(mod.mesmo_ato_ja_registrado(INQUILINATO_CALADA, [CNJ]), "")


class ProtocoloDaPonteTest(unittest.TestCase):
    """A correspondencia posicional e o contrato entre o Python e o Go. Quebrada
    em silencio, ela atribui a URN de um ato a outra URL -- que e pior que nao
    medir. Por isso ela ABORTA."""

    def setUp(self):
        self._bridge = mod.BRIDGE
        self._cache = dict(mod._URN_DE_URL)

    def tearDown(self):
        mod.BRIDGE = self._bridge
        mod._URN_DE_URL.clear()
        mod._URN_DE_URL.update(self._cache)

    def test_linhas_a_menos_abortam(self):
        mod._URN_DE_URL.clear()
        mod.BRIDGE = ("printf", "%s\n", "urn:lex:br:federal:lei:2002-01-10;10406\tplanalto.gov.br")
        with self.assertRaises(SystemExit) as capturado:
            mod.resolver_urns([CC_BASE, CDC])
        self.assertIn("correspondencia posicional", str(capturado.exception))

    def test_exit_nao_zero_aborta(self):
        mod._URN_DE_URL.clear()
        mod.BRIDGE = ("false",)
        with self.assertRaises(SystemExit) as capturado:
            mod.resolver_urns([CC_BASE])
        self.assertIn("resolve-planalto-urn falhou", str(capturado.exception))


class PonteConfiguravelTest(unittest.TestCase):
    """Sob systemd a esteira nao pode depender do compilador Go em runtime: a
    unit compila no ExecStartPre e aponta WJ_RESOLVE_PLANALTO_URN_BIN. Sem a
    variavel, o caminho interativo continua sendo `go-modern run`, que nunca
    serve binario velho."""

    def _bridge_com_env(self, valor):
        ambiente = dict(os.environ)
        if valor is None:
            ambiente.pop("WJ_RESOLVE_PLANALTO_URN_BIN", None)
        else:
            ambiente["WJ_RESOLVE_PLANALTO_URN_BIN"] = valor
        # Recarrega o modulo com o ambiente trocado: BRIDGE e decidido na
        # importacao, que e quando a unit ja exportou a variavel.
        anterior = dict(os.environ)
        os.environ.clear()
        os.environ.update(ambiente)
        try:
            carregador = importlib.machinery.SourceFileLoader("sf_bridge", str(FERRAMENTA))
            modulo = importlib.util.module_from_spec(
                importlib.util.spec_from_loader(carregador.name, carregador))
            carregador.exec_module(modulo)
            return modulo.BRIDGE
        finally:
            os.environ.clear()
            os.environ.update(anterior)

    def test_sem_a_variavel_usa_go_modern_run(self):
        self.assertEqual(self._bridge_com_env(None),
                         ("./tools/go-modern", "run", "./cmd/resolve-planalto-urn"))

    def test_com_a_variavel_usa_o_binario_e_so_ele(self):
        bridge = self._bridge_com_env("/opt/wiki/bin/resolve-planalto-urn")
        self.assertEqual(bridge, ("/opt/wiki/bin/resolve-planalto-urn",))

    def test_variavel_vazia_ou_em_branco_nao_conta(self):
        """String vazia no Environment= da unit nao pode virar um argv com um
        executavel vazio: isso daria FileNotFoundError em vez de cair no
        caminho interativo."""
        for valor in ("", "   "):
            self.assertEqual(self._bridge_com_env(valor),
                             ("./tools/go-modern", "run", "./cmd/resolve-planalto-urn"),
                             f"valor {valor!r}")


class LeaseSoParaQuemEscreveTest(unittest.TestCase):
    """O lease de epoca e o lock exclusivo so podem ser tomados quando ha
    escrita. Sem plano em shard nenhum, `main()` percorre o bloco de escrita
    vazio -- o que ele toma (ou nao) no caminho e exatamente o que se mede."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tomados = []
        self._original = {
            "carregar_corpus": mod.carregar_corpus,
            "intents_protegidos": mod.intents_protegidos,
            "planejar": mod.planejar,
            "canonical_stock_write_lease": mod.canonical_stock_write_lease,
            "exclusive_lock": mod.exclusive_lock,
            "SHARDS": mod.SHARDS,
            "argv": sys.argv,
        }
        mod.carregar_corpus = lambda: {}
        mod.intents_protegidos = lambda: set()
        # Plano com um intent que nao existe em shard nenhum: o bloco de
        # escrita e percorrido e nada e gravado.
        mod.planejar = lambda corpus, protegidos, limite: {"intent-inexistente": ("cc", "1")}
        mod.SHARDS = pathlib.Path(self.tmp.name)

        @contextlib.contextmanager
        def lease_sentinela(root):
            self.tomados.append("lease")
            yield

        @contextlib.contextmanager
        def lock_sentinela(caminho):
            self.tomados.append("lock")
            yield

        mod.canonical_stock_write_lease = lease_sentinela
        mod.exclusive_lock = lock_sentinela

    def tearDown(self):
        for nome, valor in self._original.items():
            if nome == "argv":
                sys.argv = valor
            else:
                setattr(mod, nome, valor)
        self.tmp.cleanup()

    def _roda(self, *args):
        sys.argv = ["generate-v2-second-official-source-from-corpus-20260806", *args]
        saida, erro = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
            codigo = mod.main()
        return codigo, saida.getvalue(), erro.getvalue()

    def test_dry_run_nao_toma_lease_nem_lock(self):
        codigo, saida, _ = self._roda("--dry-run")
        self.assertEqual(codigo, 0)
        self.assertEqual(self.tomados, [],
                         "--dry-run tomou trava de escrita: com a epoca ocupada ele aborta "
                         "com exit 75 e o plano fica ilegivel")
        self.assertIn("nenhum lease de escrita tomado", saida)

    def test_passada_de_escrita_toma_lease_e_lock(self):
        """Controle positivo: sem ele, "nao tomou" ficaria indistinguivel de
        "as sentinelas nao estao no caminho"."""
        codigo, _, _ = self._roda()
        self.assertEqual(codigo, 0)
        self.assertEqual(self.tomados, ["lease", "lock"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
