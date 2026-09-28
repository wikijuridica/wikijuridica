#!/usr/bin/env python3
"""Bancada de tools/check-jsonld-cobertura.

Cada teste diz, no comentário, qual linha da ferramenta faz a asserção reprovar
quando removida (mutação) — gate que passa com o detector morto é pior que gate
nenhum (regressão medida em 2026-09-05 e, de novo, em 2026-09-09 com o Article).
"""
from __future__ import annotations

import importlib.machinery
import io
import json
import os
import re
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ_DO_REPO = os.path.dirname(AQUI)
FERRAMENTA = os.path.join(AQUI, "check-jsonld-cobertura")


def carrega_modulo():
    return importlib.machinery.SourceFileLoader("check_jsonld_cobertura", FERRAMENTA).load_module()


ARTICLE = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"x"}</script>'
NEWS = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"NewsArticle","headline":"n"}</script>'
BREAD = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList"}</script>'
FAQ = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage"}</script>'

# A base canônica da fixture. O gate a lê de content/site.json (nunca de literal
# no código), e a fixture escreve o mesmo valor nos dois lugares: é assim que o
# controle positivo prova o marcador sem reimplementá-lo.
BASE_URL = "https://wikijuridica.com.br"


def institucional(path: str, fragmento: str, tipo: str = "ProfilePage") -> str:
    """O nó institucional COMO O RENDER O EMITE: @id ABSOLUTO.

    internal/structureddata/institutional.go monta `canonical + kind.fragment`, e
    canonical é a URL https completa. A fixture reproduz essa forma — reproduzir
    a forma relativa que o gate SUPUNHA até 2026-09-16 faria a bancada ficar
    verde com o detector morto, que é exatamente o defeito que ela existe para
    apanhar.
    """
    return ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"%s",'
            '"@id":"%s%s%s","url":"%s%s","name":"n","inLanguage":"pt-BR"}</script>'
            % (tipo, BASE_URL, path, fragmento, BASE_URL, path))


def html(*blocos: str) -> str:
    return "<!doctype html><html lang=\"pt-BR\"><head><title>t</title>%s</head><body><h1>t</h1></body></html>" % "".join(blocos)


class Fixture:
    """Um repositório mínimo: content/pages.json + public/**/index.html."""

    def __init__(self):
        self.temporario = tempfile.TemporaryDirectory(prefix="jsonld-cobertura-")
        self.root = self.temporario.name
        os.makedirs(os.path.join(self.root, "content"))
        os.makedirs(os.path.join(self.root, "public"))
        self.paginas = [
            {"path": "/trabalhista/aviso-previo/", "page_type": "artigo", "faq": [{"q": "a", "a": "b"}]},
            {"path": "/familia/guarda/", "page_type": "artigo"},
            {"path": "/jurisprudencia/stj-1/", "page_type": "precedente", "faq": []},
            {"path": "/diarios/rj-20260909/", "page_type": "noticia-juridica"},
            {"path": "/sobre/", "page_type": "institucional"},
            {"path": "/", "page_type": "home"},
        ]
        with open(os.path.join(self.root, "content", "pages.json"), "w", encoding="utf-8") as handle:
            json.dump({"pages": self.paginas}, handle)
        self.escreve_site_json(BASE_URL)
        self.escreve("/trabalhista/aviso-previo/", html(ARTICLE, BREAD, FAQ))
        self.escreve("/familia/guarda/", html(ARTICLE, BREAD))
        self.escreve("/jurisprudencia/stj-1/", html(ARTICLE, BREAD))
        self.escreve("/diarios/rj-20260909/", html(NEWS, BREAD))
        self.escreve("/sobre/", html(institucional("/sobre/", "#profilepage")))
        self.escreve("/", html())
        # hub de área: existe no disco, não está em pages.json
        self.escreve("/trabalhista/", html(BREAD))

    def escreve_site_json(self, base_url) -> None:
        """content/site.json, de onde o gate tira a URL canônica. `None` apaga o
        arquivo: sem base_url o gate não tem como montar o marcador."""
        caminho = os.path.join(self.root, "content", "site.json")
        if base_url is None:
            if os.path.exists(caminho):
                os.remove(caminho)
            return
        with open(caminho, "w", encoding="utf-8") as handle:
            json.dump({"base_url": base_url}, handle)

    def escreve(self, path: str, corpo: str) -> None:
        pasta = os.path.join(self.root, "public", path.strip("/"))
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as handle:
            handle.write(corpo)

    def serie(self) -> str:
        return os.path.join(self.root, "data", "ops", "jsonld_cobertura_daily.jsonl")

    def grava_linha_anterior(self, presentes: dict) -> None:
        os.makedirs(os.path.dirname(self.serie()), exist_ok=True)
        with open(self.serie(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"schema_version": "jsonld_cobertura_v1", "tipos": {
                tipo: {"esperado": n, "presente": n} for tipo, n in presentes.items()}}) + "\n")

    def limpa(self) -> None:
        self.temporario.cleanup()


def roda(modulo, root: str, *args: str):
    saida = io.StringIO()
    rc = modulo.main(["--root", root, *args], saida=saida)
    texto = saida.getvalue()
    linha = None
    for candidata in texto.splitlines():
        if candidata.startswith("{"):
            linha = json.loads(candidata)
    return rc, texto, linha


class Cobertura(unittest.TestCase):
    def setUp(self):
        self.m = carrega_modulo()
        self.f = Fixture()
        self.addCleanup(self.f.limpa)

    def test_disco_coerente_e_verde_e_deriva_o_esperado_do_pages_json(self):
        # Mutação: trocar `legal = registro["page_type"] in LEGAL_PAGE_TYPES` por
        # `True` faz /sobre/ e / entrarem no esperado e o Article "faltar" neles.
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)
        self.assertEqual(linha["tipos"]["article"]["esperado"], 3, "a notícia NÃO espera Article: espera NewsArticle")
        self.assertEqual(linha["tipos"]["article"]["presente"], 3)
        self.assertEqual(linha["tipos"]["newsarticle"]["esperado"], 1)
        self.assertEqual(linha["tipos"]["newsarticle"]["presente"], 1)
        self.assertEqual(linha["tipos"]["article"]["inesperados"], 0)
        self.assertEqual(linha["tipos"]["breadcrumb"]["esperado"], 4, "o breadcrumb continua esperado na notícia")
        self.assertEqual(linha["tipos"]["faqpage"]["esperado"], 1, "só a página com faq não vazio espera FAQPage")
        self.assertEqual(linha["tipos"]["faqpage"]["presente"], 1)
        self.assertEqual(linha["tipos"]["institucional"]["esperado"], 1, "só /sobre/ está na allowlist de rotas")
        self.assertEqual(linha["tipos"]["institucional"]["presente"], 1,
                         "CONTROLE POSITIVO: o marcador TEM de casar o @id absoluto que o render emite")
        self.assertEqual(linha["fora_do_pages_json"], 1, "o hub /trabalhista/ não está em pages.json")
        self.assertEqual(linha["index_html"], 7)
        self.assertEqual(linha["sem_html"], 0)
        self.assertFalse(os.path.exists(self.f.serie()), "sem --gravar nada é escrito")

    def test_article_ausente_em_pagina_legal_reprova_e_nomeia_o_modo_de_falha(self):
        # Mutação: remover o `else: faltantes.append(path)` deixa presente < esperado
        # sem faltante, e o exit volta a 0.
        self.f.escreve("/familia/guarda/", html(BREAD))
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 1, texto)
        self.assertEqual(linha["tipos"]["article"]["faltantes_total"], 1)
        self.assertIn("/familia/guarda/", linha["tipos"]["article"]["faltantes_amostra"])
        self.assertIn("structured_data.go:502-504", texto, "o vermelho tem de dizer onde olhar")
        self.assertIn("falta em /familia/guarda/", texto)
        self.assertEqual(linha["tipos"]["breadcrumb"]["faltantes_total"], 0)

    def test_faqpage_ausente_onde_ha_faq_reprova_e_ausente_sem_faq_nao(self):
        # Mutação: trocar `"faqpage": registro["tem_faq"]` por `False` deixa de esperar
        # o FAQPage e o exit volta a 0.
        self.f.escreve("/trabalhista/aviso-previo/", html(ARTICLE, BREAD))
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 1, texto)
        self.assertEqual(linha["tipos"]["faqpage"]["faltantes_total"], 1)
        self.assertEqual(linha["tipos"]["faqpage"]["inesperados"], 0)

    def test_noticia_que_virou_article_generico_reprova_nos_dois_sentidos(self):
        # Falso positivo de 2026-09-09: 85 /diarios/* acusados sem Article quando
        # tinham NewsArticle. A correção separa os dois tipos; e o inverso (notícia
        # rebaixada a Article) tem de reprovar como faltante de newsarticle E
        # inesperado de article. Mutação: contar NewsArticle como Article deixa o
        # inverso passar verde.
        self.f.escreve("/diarios/rj-20260909/", html(ARTICLE, BREAD))
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 1, texto)
        self.assertEqual(linha["tipos"]["newsarticle"]["faltantes_total"], 1)
        self.assertIn("/diarios/rj-20260909/", linha["tipos"]["newsarticle"]["faltantes_amostra"])
        self.assertEqual(linha["tipos"]["article"]["inesperados"], 1)
        self.assertIn("tipoDeArtigo", texto)

    def test_pagina_institucional_nao_espera_article_nem_breadcrumb(self):
        # Mutação: incluir "institucional" em LEGAL_PAGE_TYPES faz /sobre/ reprovar.
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)
        self.assertNotIn("/sobre/", linha["tipos"]["article"]["faltantes_amostra"])

    def test_queda_relativa_reprova_salvo_publicacao_declarada(self):
        # Mutação: apagar `quedas_relativas` da decisão de veredito faz o exit ser 0
        # com a série dizendo que havia 300 e o disco 3.
        self.f.grava_linha_anterior({"article": 300, "newsarticle": 10, "breadcrumb": 300, "faqpage": 100})
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 1, texto)
        self.assertTrue(any(q["tipo"] == "article" for q in linha["quedas_relativas"]))
        self.assertIn("QUEDA RELATIVA", texto)
        rc, texto, linha = roda(self.m, self.f.root, "--publicacao-declarada")
        self.assertEqual(rc, 0, texto)
        self.assertEqual(linha["quedas_relativas"], [])

    def test_queda_dentro_do_teto_nao_reprova(self):
        # 3 presentes contra 3 anteriores: queda 0%. Mutação: `>` por `>=` no teto
        # reprova queda zero.
        self.f.grava_linha_anterior({"article": 3, "newsarticle": 1, "breadcrumb": 4, "faqpage": 1})
        rc, texto, _ = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)

    def test_gravar_acrescenta_uma_linha_com_o_esquema(self):
        rc, texto, _ = roda(self.m, self.f.root, "--gravar")
        self.assertEqual(rc, 0, texto)
        with open(self.f.serie(), encoding="utf-8") as handle:
            linhas = [json.loads(l) for l in handle if l.strip()]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["schema_version"], "jsonld_cobertura_v1")
        self.assertEqual(linhas[0]["exit"], 0)
        self.assertFalse(linhas[0]["counts_as_audience"])

    def test_pagina_sem_html_e_relatada_sem_reprovar_por_si(self):
        # Página no pages.json sem index.html: outra classe de defeito (publicação).
        self.f.paginas.append({"path": "/civil/nova/", "page_type": "artigo"})
        with open(os.path.join(self.f.root, "content", "pages.json"), "w", encoding="utf-8") as handle:
            json.dump({"pages": self.f.paginas}, handle)
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)
        self.assertEqual(linha["sem_html"], 1)
        self.assertIn("/civil/nova/", texto)

    def test_marcador_institucional_ancora_na_chave_id_e_nao_casa_por_acidente(self):
        """CONTROLE POSITIVO E TRÊS NEGATIVOS do marcador — o teste que faltava.

        O detector `institucional` entrou em produção em 2026-09-11 SEM nenhum
        controle: montava `'"' + path + fragmento + '"'`, supondo @id relativo,
        e o render emite absoluto. Nunca casou uma única vez. Como o tipo era
        novo, `presente=0` era indistinguível de "ainda não mediu" — e só
        apareceu quando reprovou o deploy do acervo inteiro acusando 8 rotas,
        das quais 7 tinham o nó.

        Mutação: voltar o marcador para a forma relativa (sem `"@id":"` e sem a
        base) deixa o positivo vermelho. Tirar só a aspa de fechamento, ou só a
        chave, deixa um dos negativos vermelho.
        """
        marcador = self.m.marcador_institucional(BASE_URL, "/sobre/")

        # POSITIVO: a forma que internal/structureddata/institutional.go emite.
        emitido = institucional("/sobre/", "#profilepage").encode("utf-8")
        self.assertIn(marcador, emitido,
                      "o marcador não casa o @id ABSOLUTO que o render emite — é o defeito de 2026-09-16")

        # NEGATIVO 1 — a premissa errada do marcador antigo: @id relativo.
        # Se um dia o render passar a emitir relativo, o gate tem de reprovar
        # (o @id deixaria de ser globalmente único), nunca aceitar em silêncio.
        relativo = b'{"@id":"/sobre/#profilepage"}'
        self.assertNotIn(marcador, relativo, "@id relativo não pode contar como o nó absoluto")

        # NEGATIVO 2 — mesma rota e mesmo fragmento em OUTRA origem. Sem a base
        # no marcador, uma cópia do portal em outro domínio contaria como nossa.
        outra_origem = b'{"@id":"https://outro.exemplo/sobre/#profilepage"}'
        self.assertNotIn(marcador, outra_origem, "o marcador tem de pinar a origem canônica")

        # NEGATIVO 3 — o que prova que a âncora é a CHAVE, e não a aspa: a MESMA
        # URL completa, com a mesma aspa de abertura, sob outra chave. Um
        # marcador ancorado só na aspa casaria aqui e contaria como presente um
        # nó que não existe.
        outra_chave = b'{"url":"https://wikijuridica.com.br/sobre/#profilepage"}'
        self.assertNotIn(marcador, outra_chave,
                         "a âncora é a chave @id: a mesma URL sob outra chave não é o identificador do nó")

        # NEGATIVO 4 — prefixo: o valor tem de ser o valor INTEIRO.
        mais_longo = b'{"@id":"https://wikijuridica.com.br/sobre/#profilepage-antigo"}'
        self.assertNotIn(marcador, mais_longo, "a aspa de fechamento pina o valor inteiro")

    def test_institucional_ausente_reprova_e_nomeia_a_rota_e_o_sexto_codigo(self):
        # O defeito REAL de 2026-09-16, reduzido a uma rota: /bot/ sem nenhum
        # JSON-LD. Mutação: devolver `False` fixo em presentes[TIPO_INSTITUCIONAL]
        # faz o gate acusar sempre; devolver `True`, nunca.
        self.f.escreve("/sobre/", html())
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 1, texto)
        self.assertEqual(linha["tipos"]["institucional"]["faltantes_total"], 1)
        self.assertIn("/sobre/", linha["tipos"]["institucional"]["faltantes_amostra"])
        self.assertIn("_schema_validation_failed", texto,
                      "o vermelho tem de citar o SEXTO código: é ele que derrubou /bot/, e ele não é "
                      "recusa explícita de RenderInstitutionalScript")
        # E não contamina os outros tipos: /sobre/ não é conteúdo jurídico.
        self.assertEqual(linha["tipos"]["article"]["faltantes_total"], 0)

    def test_rota_fora_da_allowlist_com_no_institucional_nao_conta_como_inesperado(self):
        # /familia/guarda/ não é rota institucional: o marcador não existe para
        # ela e o valor é False — nunca "não sei". Mutação: montar o marcador
        # para rota fora da allowlist levanta KeyError.
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)
        self.assertEqual(linha["tipos"]["institucional"]["inesperados"], 0)

    def test_sem_site_json_e_exit_2_nunca_verde(self):
        """Sem `base_url` o gate NÃO CONSEGUE medir, e isso é exit 2.

        É a diferença entre "não há nada faltando" e "não sei olhar". Mutação:
        fazer `carrega_base_url` devolver "" em vez de levantar deixa o marcador
        virar `'"@id":"/sobre/#profilepage"'` — o marcador relativo de novo — e o
        gate volta a acusar as oito por vacuidade.
        """
        self.f.escreve_site_json(None)
        rc, texto, _ = roda(self.m, self.f.root)
        self.assertEqual(rc, 2, texto)
        self.assertIn("não conseguiu medir", texto)

    def test_base_url_com_barra_final_produz_o_mesmo_marcador(self):
        # O Go faz strings.TrimRight(site.BaseURL, "/") em LoadRepository; o gate
        # espelha com rstrip("/"). Sem isso o marcador viraria "…com.br//sobre/…".
        self.f.escreve_site_json(BASE_URL + "/")
        rc, texto, linha = roda(self.m, self.f.root)
        self.assertEqual(rc, 0, texto)
        self.assertEqual(linha["tipos"]["institucional"]["presente"], 1)

    def test_sem_public_ou_sem_pages_json_e_exit_2(self):
        with tempfile.TemporaryDirectory() as vazio:
            os.makedirs(os.path.join(vazio, "content"))
            with open(os.path.join(vazio, "content", "pages.json"), "w", encoding="utf-8") as handle:
                json.dump({"pages": []}, handle)
            with open(os.path.join(vazio, "content", "site.json"), "w", encoding="utf-8") as handle:
                json.dump({"base_url": BASE_URL}, handle)
            rc, texto, _ = roda(self.m, vazio)
            self.assertEqual(rc, 2, texto)


class ParidadeComOGo(unittest.TestCase):
    def test_lista_de_tipos_legais_e_a_do_internal_content(self):
        """A cópia em Python tem de ser o `var LegalPageTypes` de
        internal/content/content.go, chave por chave — é o que impede "derivado do
        disco" de virar número fixo pela porta de trás."""
        m = carrega_modulo()
        caminho = os.path.join(RAIZ_DO_REPO, "internal", "content", "content.go")
        with open(caminho, encoding="utf-8") as handle:
            fonte = handle.read()
        inicio = fonte.index("var LegalPageTypes = map[string]bool{")
        fim = fonte.index("}", inicio)
        chaves = set(re.findall(r'"([a-z-]+)":\s*true', fonte[inicio:fim]))
        self.assertTrue(chaves, "não achou o mapa no Go")
        self.assertEqual(set(m.LEGAL_PAGE_TYPES), chaves)


    def test_rotas_institucionais_sao_as_do_internal_structureddata(self):
        """A cópia em Python tem de ser o `var institutionalPages` de
        internal/structureddata/institutional.go, ROTA e FRAGMENTO.

        ESTE TESTE NÃO EXISTIA. O comentário da ferramenta (linha 115-117)
        afirmava desde 2026-09-11 que "o teste de paridade reprova se o Go ganhar
        ou perder uma rota sem esta lista acompanhar" — e só `LegalPageTypes`
        tinha um. Comentário que promete teste inexistente é da mesma família do
        detector sem controle positivo: o leitor confia numa garantia que ninguém
        executa.
        """
        m = carrega_modulo()
        caminho = os.path.join(RAIZ_DO_REPO, "internal", "structureddata", "institutional.go")
        with open(caminho, encoding="utf-8") as handle:
            fonte = handle.read()
        inicio = fonte.index("var institutionalPages = map[string]institutionalKind{")
        fim = fonte.index("\n}", inicio)
        pares = dict(re.findall(r'"(/[a-z0-9-]+/)":\s*\{schemaType:\s*"[A-Za-z]+",\s*fragment:\s*"(#[a-z]+)"\}',
                                fonte[inicio:fim]))
        self.assertTrue(pares, "não achou o allowlist no Go")
        self.assertEqual(dict(m.ROTAS_INSTITUCIONAIS), pares)


if __name__ == "__main__":
    unittest.main()
