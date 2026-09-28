#!/usr/bin/env python3
"""Bancada da INVARIANTE de frescor de `tools/reload-wiki-server`.

POR QUE ELA EXISTE, com o caso que a originou
---------------------------------------------
`reload-wiki-server` ja comparava CONTEUDO desde 2026-08-20 — mas comparava o
TITULO, porque o incidente daquela data foi de 419 titulos trocados.

Em 2026-09-16 a republicacao corrigiu a DATA DE ESTREIA de 10.996 paginas e nao
mexeu em titulo nenhum. A amostra bateu, a ferramenta imprimiu "sem divergencia:
o processo ja serve o manifesto do disco" e NAO reiniciou. Medido: o processo
subira as 06:51 e `content/pages.json` no disco era de 10:54.

O estrago foi o mesmo de 2026-08-20, uma camada mais fundo. O nginx ja servia o
HTML corrigido de `public/`, e a GEMEA MARKDOWN continuou servindo
`date_published: "2026-09-16"` com `date_modified: "2026-09-05"` — a cronologia
impossivel que `cmd/publish-v2-direct` declara proibida, viva no canal que o
CLAUDE.md §12 define como o produto.

**Comparar um campo e sempre perder o campo seguinte.** A invariante nao compara
campo: confere que o processo vivo subiu DEPOIS do artefato que ele carrega no
boot. Esta bancada existe para que ela nunca volte a ser uma amostra.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
mod = SourceFileLoader("reload_wiki_server", str(RAIZ / "tools/reload-wiki-server")).load_module()

AGORA = time.time()
PROCESSO_SUBIU = AGORA - 3600  # uma hora atras


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.artefato = Path(self.tmp.name) / "pages.json"
        self.ledger_original = mod.LEDGER
        mod.LEDGER = Path(self.tmp.name) / "server_reload.jsonl"
        self.addCleanup(lambda: setattr(mod, "LEDGER", self.ledger_original))
        self.inicio_original = mod.ativo_desde
        mod.ativo_desde = lambda: PROCESSO_SUBIU
        self.addCleanup(lambda: setattr(mod, "ativo_desde", self.inicio_original))
        # RAIZ do modulo entra na mensagem por relative_to; aponta para o tmp.
        self.raiz_original = mod.RAIZ
        mod.RAIZ = Path(self.tmp.name)
        self.addCleanup(lambda: setattr(mod, "RAIZ", self.raiz_original))

    def escreve(self, conteudo: str, mtime: float):
        self.artefato.write_text(conteudo, encoding="utf-8")
        os.utime(self.artefato, (mtime, mtime))


class TesteControlePositivo(Base):
    """O caso que a invariante existe para pegar. Sem ele, ela e decorativa."""

    def test_artefato_mais_novo_que_o_processo_dispara(self):
        self.escreve('{"paginas": 1}', PROCESSO_SUBIU + 600)
        desatualizado, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertTrue(desatualizado, "o detector nao viu artefato mais novo que o processo")
        self.assertIn("EM MEMORIA", motivo, "a mensagem nao explica o que fica desatualizado")
        self.assertIn("pages.json", motivo)

    def test_a_mensagem_traz_as_duas_datas_e_o_sha(self):
        """Mensagem sem numero obriga quem le a remedir. Ela carrega a prova."""
        self.escreve('{"paginas": 2}', PROCESSO_SUBIU + 600)
        _, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertIn(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(PROCESSO_SUBIU)), motivo)
        self.assertIn("sha256", motivo)


class TesteControleNegativo(Base):
    """O que a invariante NAO pode acusar — senao vira restart a cada passada."""

    def test_artefato_anterior_ao_processo_nao_dispara(self):
        self.escreve('{"paginas": 1}', PROCESSO_SUBIU - 600)
        desatualizado, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertFalse(desatualizado, motivo)

    def test_mesmo_conteudo_ja_reconciliado_neste_processo_nao_dispara(self):
        """Reescrita com bytes identicos move o mtime e NAO e motivo de restart.

        Restart sem motivo derruba o indice de busca a frio — e era isso que a
        versao anterior desta ferramenta tentava evitar quando errou para o
        outro lado.
        """
        self.escreve('{"paginas": 3}', PROCESSO_SUBIU + 600)
        sha = mod.impressao(self.artefato)
        mod.LEDGER.write_text(json.dumps({
            "acao": "reload", "resultado": "ok",
            "pages_json_sha256": sha,
            "processo_ativo_desde": PROCESSO_SUBIU,
        }) + "\n", encoding="utf-8")
        desatualizado, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertFalse(desatualizado, motivo)

    def test_conteudo_DIFERENTE_dispara_mesmo_com_ledger(self):
        """A reconciliacao vale para o sha registrado, nao para o arquivo."""
        self.escreve('{"paginas": 3}', PROCESSO_SUBIU + 600)
        mod.LEDGER.write_text(json.dumps({
            "acao": "reload", "resultado": "ok",
            "pages_json_sha256": "0" * 64,
            "processo_ativo_desde": PROCESSO_SUBIU,
        }) + "\n", encoding="utf-8")
        desatualizado, _ = mod.processo_carregou_o_disco(self.artefato)
        self.assertTrue(desatualizado, "ledger com outro sha aprovou artefato novo")

    def test_reconciliacao_de_OUTRO_processo_nao_vale(self):
        """Ledger de um processo anterior nao fala pelo processo de agora."""
        self.escreve('{"paginas": 3}', PROCESSO_SUBIU + 600)
        sha = mod.impressao(self.artefato)
        mod.LEDGER.write_text(json.dumps({
            "acao": "reload", "resultado": "ok",
            "pages_json_sha256": sha,
            "processo_ativo_desde": PROCESSO_SUBIU - 99999,
        }) + "\n", encoding="utf-8")
        desatualizado, _ = mod.processo_carregou_o_disco(self.artefato)
        self.assertTrue(desatualizado, "reconciliacao de outro processo foi aceita")


class TesteNaoMedido(Base):
    """"Nao sei" nunca pode virar "esta tudo bem"."""

    def test_artefato_ausente_e_NAO_MEDIDO(self):
        desatualizado, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertIsNone(desatualizado)
        self.assertIn("nao medido", motivo)

    def test_systemctl_mudo_e_NAO_MEDIDO(self):
        self.escreve('{"paginas": 1}', PROCESSO_SUBIU + 600)
        mod.ativo_desde = lambda: None
        desatualizado, motivo = mod.processo_carregou_o_disco(self.artefato)
        self.assertIsNone(desatualizado, "systemctl mudo virou veredito")
        self.assertIn("nao medido", motivo)


class TesteMutacao(Base):
    """Os mutantes que esta bancada existe para matar."""

    def test_mutante_que_compara_so_o_titulo(self):
        """Mutante: `return False, ""` no lugar da comparacao de tempo.

        E o defeito de 2026-09-16 em forma de codigo: a amostra de titulos bate,
        a invariante cala, e a gemea serve dado velho. O controle positivo acima
        e o que o mata; esta asserção trava o par que o denuncia.
        """
        self.escreve('{"data": "2026-09-16"}', PROCESSO_SUBIU + 600)
        novo, _ = mod.processo_carregou_o_disco(self.artefato)
        self.escreve('{"data": "2026-09-16"}', PROCESSO_SUBIU - 600)
        velho, _ = mod.processo_carregou_o_disco(self.artefato)
        self.assertNotEqual(novo, velho,
                            "o detector devolve o mesmo veredito para artefato novo e velho — "
                            "ele parou de olhar o tempo")


if __name__ == "__main__":
    unittest.main(verbosity=2)
