#!/usr/bin/env python3
"""Testes de tools/medir-ancoras-de-dispositivo.

TODO teste roda OFFLINE, sobre HTML e registry escritos aqui — nada lê `public/`
nem a rede.

O caso que importa é a PROVA POR MUTAÇÃO do padrão de link, porque foi ali que o
instrumento anterior errou por um fator de dois. As páginas do portal trazem
links para o Planalto de DOIS produtores com atributos diferentes:

    <a href="...l8112cons.htm#art8" rel="external">art. 8º</a>
    <a href="...l8112cons.htm#art8" target="_blank" rel="external noopener">…</a>

Um padrão que exija a forma literal `" rel="external">` casa o primeiro e perde o
segundo — e como o segundo é o bloco de Proveniência, que existe em quase toda
página, o instrumento devolve metade do acervo com cara de total. Medido em
2026-09-11 sobre `public/`: 8.034 contra 16.530.

Rodar:
    python3 tools/test_medir_ancoras_de_dispositivo.py
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import inspect
import json
import os
import pathlib
import tempfile
import unittest

FERRAMENTA = pathlib.Path(__file__).resolve().parent / "medir-ancoras-de-dispositivo"


def carrega():
    loader = importlib.machinery.SourceFileLoader("medir_ancoras", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


M = carrega()

DOC = "https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm"
OUTRO = "https://www.planalto.gov.br/ccivil_03/leis/l9999.htm"

REGISTRY = {
    DOC: {
        "artigo": {"art8", "art41", "art37"},
        "letrado": {"art1015a"},
        "paragrafo": {"art37§6", "art41§2"},
    },
}


def inline(href, texto):
    return '<a href="%s" rel="external">%s</a>' % (href, texto)


def proveniencia(href, texto):
    """A forma do bloco de Proveniência — a que o instrumento antigo perdia."""
    return '<a href="%s" target="_blank" rel="external noopener">%s</a>' % (href, texto)


class Classes(unittest.TestCase):
    def test_fragmento_de_paragrafo_conta_nas_duas_grafias(self):
        html = (inline(DOC + "#art37§6", "art. 37, § 6º")
                + proveniencia(DOC + "#art41%C2%A72", "art. 41, § 2º"))
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_resolvido"], 2, dict(contagens))
        self.assertEqual(contagens["raso"], 0, dict(contagens))

    def test_raso_com_paragrafo_no_texto_e_emitivel_quando_o_registry_tem(self):
        html = inline(DOC + "#art37", "art. 37, § 6º da Constituição")
        contagens, tocada = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["raso"], 1, dict(contagens))
        self.assertEqual(contagens["paragrafo_emitivel"], 1, dict(contagens))
        self.assertIn("paragrafo", tocada)

    def test_raso_com_paragrafo_que_o_registry_nao_tem_continua_recuando(self):
        html = inline(DOC + "#art8", "art. 8º, § 3º")
        contagens, tocada = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_sem_ancora"], 1, dict(contagens))
        self.assertEqual(contagens["paragrafo_emitivel"], 0, dict(contagens))
        self.assertEqual(tocada, set())

    def test_sem_fragmento_com_artigo_letrado_no_texto(self):
        html = proveniencia(DOC, "Lei 8.112/1990, art. 1.015-A")
        contagens, tocada = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["sem_fragmento"], 1, dict(contagens))
        self.assertEqual(contagens["letrado_emitivel"], 1, dict(contagens))
        self.assertIn("letrado", tocada)

    def test_letrado_fora_do_registry_do_documento_continua_no_topo(self):
        html = inline(DOC, "art. 99-Z")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["letrado_sem_ancora"], 1, dict(contagens))

    def test_documento_fora_do_registry_e_contado_a_parte(self):
        html = inline(OUTRO + "#art1", "art. 1º, § 2º") + inline(OUTRO, "art. 5º-A")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["fora_do_registry"], 2, dict(contagens))
        self.assertEqual(contagens["paragrafo_emitivel"], 0, dict(contagens))
        self.assertEqual(contagens["letrado_emitivel"], 0, dict(contagens))

    def test_pagina_conta_uma_vez_por_classe_mesmo_com_varios_links(self):
        html = (inline(DOC + "#art37", "art. 37, § 6º")
                + inline(DOC + "#art41", "art. 41, § 2º"))
        contagens, tocada = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_emitivel"], 2, dict(contagens))
        self.assertEqual(tocada, {"paragrafo"})


class VarreduraEArgumentos(unittest.TestCase):
    def monta(self, base, rota, html):
        pasta = os.path.join(base, rota.strip("/"))
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as arquivo:
            arquivo.write(html)

    def test_varre_arvore_e_conta_paginas_distintas(self):
        with tempfile.TemporaryDirectory() as base:
            self.monta(base, "/a/", inline(DOC + "#art37", "art. 37, § 6º"))
            self.monta(base, "/b/", inline(DOC + "#art41", "art. 41, § 2º"))
            self.monta(base, "/c/", "<p>sem link</p>")
            arquivos, total, paginas = M.varre(base, REGISTRY)
        self.assertEqual(arquivos, 3)
        self.assertEqual(total["paragrafo_emitivel"], 2)
        self.assertEqual(paginas["paragrafo"], 2)

    def test_registry_vazio_recusa_medir(self):
        with tempfile.TemporaryDirectory() as base:
            vazio = os.path.join(base, "registry.jsonl")
            open(vazio, "w").close()
            self.assertEqual(M.main(["--raiz", base, "--registry", vazio]), 2)

    def test_arvore_sem_index_recusa_medir(self):
        with tempfile.TemporaryDirectory() as base:
            registry = os.path.join(base, "registry.jsonl")
            with open(registry, "w", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps({"url": DOC, "ancoras_de_artigo": ["art8"]}) + "\n")
            self.assertEqual(M.main(["--raiz", base, "--registry", registry]), 2)


class FormasDoFragmento(unittest.TestCase):
    """As formas que o acervo tem de verdade, e que uma forma imaginada perdia.

    Medido em 2026-09-11: 7 dos 91 links já resolvidos não casavam
    `^art[0-9a-z]+(§|%C2%A7)\\d+$` e caíam em `raso` — classe ERRADA, que não
    reduz total nenhum e por isso não aparece em conferência por soma.
    """

    def test_adct_tem_prefixo_proprio_e_conta(self):
        html = inline(DOC + "#adctart10§1", "ADCT art. 10, §1º")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_resolvido"], 1, dict(contagens))

    def test_adct_sem_paragrafo_e_raso_e_nao_some(self):
        html = inline(DOC + "#adctart82", "ADCT art. 82")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["raso"], 1, dict(contagens))
        self.assertEqual(contagens["fragmento_de_outra_forma"], 0, dict(contagens))

    def test_sufixo_ponto_zero_do_planalto_conta_como_resolvido(self):
        html = inline(DOC + "#art16§5.0", "Lei 8.213/1991, art. 16, § 5º")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_resolvido"], 1, dict(contagens))

    def test_inciso_colado_ao_paragrafo_conta_como_resolvido(self):
        html = inline(DOC + "#art225§1iv", "art. 225, § 1º, IV")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_resolvido"], 1, dict(contagens))

    def test_fragmento_que_nao_e_dispositivo_nao_infla_raso(self):
        html = inline(DOC + "#topo", "a lei")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["fragmento_de_outra_forma"], 1, dict(contagens))
        self.assertEqual(contagens["raso"], 0, dict(contagens))


class Mutacao(unittest.TestCase):
    def mutante(self, de, para):
        fonte = inspect.getsource(M)
        self.assertIn(de, fonte, "a mutação precisa deste literal para significar alguma coisa")
        # `__file__` e `__name__` entram porque o módulo os usa para derivar ROOT
        # e para decidir se roda o main; sem eles o mutante morre de NameError e
        # o teste passaria a provar o erro errado.
        escopo = {"__file__": str(FERRAMENTA), "__name__": "mutante"}
        exec(compile(fonte.replace(de, para), "<mutante>", "exec"), escopo)
        return escopo

    def test_padrao_que_exige_rel_external_literal_perde_a_proveniencia(self):
        """É o defeito medido: 8.034 de 16.530 links, e o instrumento não avisava."""
        html = (inline(DOC + "#art37", "art. 37, § 6º")
                + proveniencia(DOC + "#art41", "art. 41, § 2º"))
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_emitivel"], 2, dict(contagens))

        escopo = self.mutante(
            r'(?:#([^"]*))?"[^>]*>([^<]*)</a>',
            r'(?:#([^"]*))?" rel="external">([^<]*)</a>')
        contagens_mutante, _ = escopo["classifica"](html, REGISTRY)
        self.assertEqual(contagens_mutante["paragrafo_emitivel"], 1, dict(contagens_mutante))

    def test_so_percent_encoded_esconde_os_links_ja_resolvidos(self):
        """91 links do acervo saem com `§` literal; olhar só `%C2%A7` diria zero."""
        html = inline(DOC + "#art37§6", "art. 37, § 6º")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["paragrafo_resolvido"], 1, dict(contagens))

        escopo = self.mutante(
            r'MARCA_DE_PARAGRAFO = re.compile(r"(?:%C2%A7|§)")',
            r'MARCA_DE_PARAGRAFO = re.compile(r"%C2%A7")')
        contagens_mutante, _ = escopo["classifica"](html, REGISTRY)
        self.assertEqual(contagens_mutante["paragrafo_resolvido"], 0, dict(contagens_mutante))
        # E o link vai para a classe ERRADA em vez de sumir, que é o pior caso:
        # nenhum total encolhe, então uma conferência por soma não acusa nada.
        # Com o `§` no fragmento ele nem sequer tem forma de artigo, e cai em
        # `fragmento_de_outra_forma`.
        self.assertEqual(contagens_mutante["fragmento_de_outra_forma"], 1, dict(contagens_mutante))
        self.assertEqual(contagens_mutante["raso"], 0, dict(contagens_mutante))

    def test_ponto_de_milhar_no_texto_letrado_precisa_cair(self):
        html = inline(DOC, "art. 1.015-A")
        contagens, _ = M.classifica(html, REGISTRY)
        self.assertEqual(contagens["letrado_emitivel"], 1, dict(contagens))

        escopo = self.mutante(
            'return "art" + achado.group(1).replace(".", "") + achado.group(2).lower()',
            'return "art" + achado.group(1) + achado.group(2).lower()')
        contagens_mutante, _ = escopo["classifica"](html, REGISTRY)
        self.assertEqual(contagens_mutante["letrado_emitivel"], 0, dict(contagens_mutante))
        self.assertEqual(contagens_mutante["letrado_sem_ancora"], 1, dict(contagens_mutante))


if __name__ == "__main__":
    unittest.main(verbosity=2)
