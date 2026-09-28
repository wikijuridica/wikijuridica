#!/usr/bin/env python3
"""Prova por MUTAÇÃO o gerador que põe a diretiva de robots.txt do `/bot/` em
duas linhas — e, sobretudo, que ele não reserializa o resto do arquivo.

O defeito que estes testes existem para impedir foi cometido nesta mesma sessão:
a primeira gravação trocou os 2 campos que declarava e **1.834 linhas que não
declarava**, todas `\\u0026` virando `&` dentro de `source_url` de acórdão do STF.
`content/pages.json` é escrito por Go, cujo `encoding/json` escapa `&`, `<` e `>`
por padrão; `json.dump` do Python não escapa nenhum dos três. O JSON continua
equivalente — e o diff deixa de dizer a verdade, que é o que custa.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GERADOR = RAIZ / "tools/generate-pagina-bot-robots-em-lista-20260910"


def carrega(caminho):
    """Importa o gerador como módulo, apontando PAGES para a raiz temporária."""
    spec = importlib.util.spec_from_loader("gerador_bot",
                                           importlib.machinery.SourceFileLoader(
                                               "gerador_bot", str(caminho)))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


PAGINA_BOT = {
    "path": "/bot/",
    "content_revised_at": "2026-09-06",
    "body_sections": [
        {"heading": "Como bloquear o agente",
         "body": ("Acrescente ao robots.txt do seu site:\n\n"
                  "User-agent: WikijuridicaBot\n"
                  "Disallow: /\n\n"
                  "O agente respeita robots.txt.")},
    ],
}
PAGINA_VIZINHA = {
    "path": "/jurisprudencia/stf-sumula-1602/",
    "content_revised_at": "2026-08-01",
    "source_provenance": [
        {"source_url": "https://portal.stf.jus.br/x.asp?base=30&sumula=1602"},
    ],
}


class GeradorDoBot(unittest.TestCase):
    def monta(self, paginas=None):
        """Cria uma raiz temporária com o gerador e um pages.json escrito com os
        escapes do produtor Go."""
        diretorio = tempfile.mkdtemp()
        raiz = Path(diretorio)
        (raiz / "tools").mkdir()
        (raiz / "content").mkdir()
        copia = raiz / "tools" / GERADOR.name
        shutil.copy2(GERADOR, copia)
        conteudo = json.dumps(paginas if paginas is not None
                              else [PAGINA_BOT, PAGINA_VIZINHA],
                              ensure_ascii=False, indent=2)
        for literal, escapado in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e")):
            conteudo = conteudo.replace(literal, escapado)
        (raiz / "content" / "pages.json").write_text(conteudo + "\n", encoding="utf-8")
        return raiz, copia

    def roda(self, copia, *extra):
        concluido = subprocess.run([sys.executable, str(copia), *extra],
                                   capture_output=True, text=True, timeout=120)
        return concluido.returncode, concluido.stdout + concluido.stderr

    # --- o conserto em si -------------------------------------------------
    def test_troca_a_diretiva_por_duas_linhas_de_lista(self):
        raiz, copia = self.monta()
        codigo, saida = self.roda(copia)
        self.assertEqual(codigo, 0, saida)
        paginas = json.loads((raiz / "content/pages.json").read_text(encoding="utf-8"))
        corpo = paginas[0]["body_sections"][0]["body"]
        self.assertIn("- User-agent: WikijuridicaBot\n- Disallow: /", corpo)
        self.assertNotIn("WikijuridicaBot\nDisallow", corpo)

    def test_a_pagina_vizinha_nao_e_tocada(self):
        raiz, copia = self.monta()
        self.roda(copia)
        paginas = json.loads((raiz / "content/pages.json").read_text(encoding="utf-8"))
        self.assertEqual(paginas[1], PAGINA_VIZINHA)

    def test_os_escapes_do_produtor_go_sobrevivem_a_gravacao(self):
        """O `&` de `?base=30&sumula=1602` tem de continuar `\\u0026` no disco.
        Sem isto, uma correção de dois campos aparece no diff como 1.838 linhas
        e a próxima gravação do Go desfaz tudo de volta."""
        raiz, copia = self.monta()
        self.roda(copia)
        bruto = (raiz / "content/pages.json").read_text(encoding="utf-8")
        self.assertIn("\\u0026sumula=1602", bruto)
        self.assertNotIn("&sumula=1602", bruto)

    def test_so_as_linhas_declaradas_mudam(self):
        """A prova de fogo: diff textual do antes contra o depois.

        UMA linha, e o número caiu de duas em 2026-09-10 por correção, não por
        regressão: o gerador deixou de carimbar `content_revised_at`. O campo é
        derivado de `data/ops/page_content_revision.jsonl`, e escrevê-lo à mão
        afirma um fato — "o conteúdo servido mudou nesta data" — que só o hash do
        HTML servido estabelece. No deploy #4 o carimbo à mão fez a data
        RETROCEDER de 2026-09-10 para 2026-09-06 no diff, porque o publicador
        reescreveu o campo com o `revised_on` do ledger, que só avança depois da
        purga."""
        raiz, copia = self.monta()
        antes = (raiz / "content/pages.json").read_text(encoding="utf-8").splitlines()
        self.roda(copia)
        depois = (raiz / "content/pages.json").read_text(encoding="utf-8").splitlines()
        mudadas = [(a, b) for a, b in zip(antes, depois) if a != b]
        self.assertEqual(len(antes), len(depois), "o numero de linhas nao pode mudar")
        self.assertEqual(len(mudadas), 1,
                         "esperava 1 linha (so o body), veio %d: %s"
                         % (len(mudadas), mudadas[:4]))
        self.assertIn("Disallow", mudadas[0][1])

    def test_nao_carimba_content_revised_at(self):
        """O campo derivado tem de sair intacto — este é o mutante que a correção
        de 2026-09-10 mata."""
        raiz, copia = self.monta()
        self.roda(copia)
        paginas = json.loads((raiz / "content/pages.json").read_text(encoding="utf-8"))
        self.assertEqual(paginas[0]["content_revised_at"], "2026-09-06")

    # --- idempotência e reparo -------------------------------------------
    def test_segunda_execucao_troca_zero_campos(self):
        raiz, copia = self.monta()
        self.roda(copia)
        depois_da_primeira = (raiz / "content/pages.json").read_text(encoding="utf-8")
        codigo, saida = self.roda(copia)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("ja corrigida", saida)
        self.assertEqual((raiz / "content/pages.json").read_text(encoding="utf-8"),
                         depois_da_primeira)

    def test_repara_serializacao_deixada_por_gravacao_anterior(self):
        """Arquivo já corrigido, mas com `&` cru de uma gravação Python anterior:
        rodar de novo devolve o escape, sem tocar em mais nada."""
        raiz, copia = self.monta()
        self.roda(copia)
        caminho = raiz / "content/pages.json"
        caminho.write_text(caminho.read_text(encoding="utf-8").replace("\\u0026", "&"),
                           encoding="utf-8")
        codigo, saida = self.roda(copia)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("serializacao reparada", saida)
        self.assertIn("\\u0026sumula=1602",
                      caminho.read_text(encoding="utf-8"))

    # --- a guarda ---------------------------------------------------------
    def test_guarda_aborta_quando_a_frase_nao_esta_no_disco(self):
        """Nunca sobrescrever o que não se reconhece: se alguém já editou a
        seção, o gerador para em vez de impor a redação dele."""
        pagina = json.loads(json.dumps(PAGINA_BOT))
        pagina["body_sections"][0]["body"] = "Acrescente ao robots.txt: fale conosco."
        raiz, copia = self.monta([pagina, PAGINA_VIZINHA])
        antes = (raiz / "content/pages.json").read_text(encoding="utf-8")
        codigo, saida = self.roda(copia)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("guarda", saida)
        self.assertEqual((raiz / "content/pages.json").read_text(encoding="utf-8"), antes)

    def test_seco_nao_escreve(self):
        raiz, copia = self.monta()
        antes = (raiz / "content/pages.json").read_text(encoding="utf-8")
        codigo, saida = self.roda(copia, "--seco")
        self.assertEqual(codigo, 0, saida)
        self.assertEqual((raiz / "content/pages.json").read_text(encoding="utf-8"), antes)

    def test_secao_ausente_devolve_2_e_nao_1(self):
        pagina = {"path": "/bot/", "body_sections": [{"heading": "Outra", "body": "x"}]}
        raiz, copia = self.monta([pagina])
        codigo, saida = self.roda(copia)
        self.assertEqual(codigo, 2, saida)


if __name__ == "__main__":
    unittest.main()
