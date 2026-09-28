#!/usr/bin/env python3
"""Prova que `tools/check-indexnow-backlog` REPROVA quando deve.

Um gate que só se viu verde não prova nada — o defeito de 2026-09-08 sobreviveu
um mês debaixo de uma mensagem tranquilizadora ("nada a submeter") que descrevia
corretamente o delta e escondia 6.803 URLs por anunciar. Aqui cada veredito
vermelho é exercitado com estado montado, e o verde também, para que o gate não
possa passar a reprovar sempre sem ninguém notar.

Offline por construção: nenhuma rede, nenhuma escrita fora do diretório temporário.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = str(RAIZ / "tools" / "check-indexnow-backlog")
BASE = "https://exemplo.test"
ROTAS = ["/familia/a/", "/tributario/b/", "/aereo/c/"]


def _carrega_modulo_fresco():
    loader = SourceFileLoader("check_indexnow_backlog_test_subject", _ALVO)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def _prepara(estado, ledger=()):
    raiz = tempfile.mkdtemp(prefix="check-indexnow-backlog-")
    os.makedirs(os.path.join(raiz, "public/sitemaps"))
    locs = "".join("<url><loc>%s%s</loc></url>" % (BASE, rota) for rota in ROTAS)
    with io.open(os.path.join(raiz, "public/sitemaps/pages-1.xml"), "w", encoding="utf-8") as h:
        h.write("<?xml version='1.0'?><urlset>%s</urlset>" % locs)
    os.makedirs(os.path.join(raiz, "data/ops"))
    with io.open(os.path.join(raiz, "data/ops/indexnow_submission_state.json"),
                 "w", encoding="utf-8") as h:
        json.dump(estado, h)
    caminho_ledger = os.path.join(raiz, "data/ops/indexnow_url_state.jsonl")
    with io.open(caminho_ledger, "w", encoding="utf-8") as h:
        for linha in ledger:
            h.write(json.dumps(linha) + "\n")
    modulo = _carrega_modulo_fresco()
    modulo.ROOT = raiz
    modulo.ESTADO = os.path.join(raiz, "data/ops/indexnow_submission_state.json")
    # REBIND OBRIGATORIO, e ele ja pegou um defeito: sem esta linha
    # `LEDGER_URL` continua apontando para o arquivo REAL do repositorio, e a
    # fixture passa a medir producao. Ao acrescentar o sentido inverso em
    # 2026-09-16, tres testes ficaram vermelhos por isso — o teste lia os 2.422
    # eventos de verdade e reprovava um cenario que deveria ser verde. Constante
    # derivada de ROOT tem de ser rebindada junto com ROOT.
    modulo.LEDGER_URL = caminho_ledger
    return modulo


def _evento(url, submitted_at, http_status=200):
    """Uma linha do ledger por URL, no formato que o submissor grava."""
    return {"schema_version": "indexnow_url_state_v1", "url": url,
            "lote": 1, "url_count": 1, "endpoint": "https://api.indexnow.org/indexnow",
            "http_status": http_status, "submitted_at": submitted_at}


def _roda(modulo, argumentos=()):
    import sys
    sys.argv = ["check-indexnow-backlog"] + list(argumentos)
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
        codigo = modulo.main()
    return codigo, saida.getvalue()


def _urls(com_recibo):
    urls = {}
    for rota in ROTAS:
        registro = {"content_sha256": "0" * 64, "hash_source": "public_html"}
        if rota in com_recibo:
            registro["submitted_at"] = "2026-09-01T00:00:00+00:00"
            registro["http_status"] = 200
        else:
            registro["seeded"] = True
        urls[BASE + rota] = registro
    return urls


class GateDoBacklog(unittest.TestCase):
    def test_reprova_o_defeito_original_backlog_sem_nenhuma_drenagem(self):
        modulo = _prepara({"urls": _urls(set())})
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("NENHUMA drenagem registrada", saida)

    def test_reprova_drenagem_parada_com_backlog_no_ar(self):
        modulo = _prepara({"urls": _urls(set()),
                           "backlog_drain": {"date": "2020-01-01", "sent": 10}})
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("drenagem está parada", saida)

    def test_aprova_drenagem_em_andamento(self):
        import datetime
        hoje = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        modulo = _prepara({"urls": _urls({"/familia/a/"}),
                           "backlog_drain": {"date": hoje, "sent": 1000}})
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("drenagem em andamento", saida)

    def test_aprova_quando_todo_o_acervo_tem_recibo(self):
        modulo = _prepara({"urls": _urls(set(ROTAS))})
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("toda URL no ar tem recibo", saida)

    def test_seeded_nao_vale_como_recibo(self):
        """O erro conceitual que criou o defeito: tratar a semente como envio."""
        modulo = _prepara({"urls": _urls(set()),
                           "backlog_drain": {"date": "2020-01-01", "sent": 1}})
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("sem recibo      : 3", saida)

    def test_rota_aposentada_no_estado_nao_conta_como_divida(self):
        estado = {"urls": _urls(set(ROTAS)),
                  "backlog_drain": {"date": "2020-01-01", "sent": 1}}
        estado["urls"][BASE + "/aposentada/z/"] = {"content_sha256": "0" * 64, "seeded": True}
        modulo = _prepara(estado)
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("toda URL no ar tem recibo", saida)


def _hoje():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


class SentidoInverso(unittest.TestCase):
    """RECIBO → SITEMAP, o lado para o qual o gate era cego até 2026-09-16.

    Enquanto ele imprimia "OK: toda URL no ar tem recibo", 1.968 URLs fora do
    sitemap estavam sendo anunciadas. Nenhum teste podia apanhar isso porque
    nenhum media este sentido.
    """

    def test_gemea_anunciada_REPROVA_mesmo_com_o_sentido_direto_perfeito(self):
        # Este é o cenário REAL de 2026-09-16: sitemap→recibo 100%, e metade do
        # lote era gêmea. O gate antigo devolvia 0 aqui.
        modulo = _prepara(
            {"urls": _urls(set(ROTAS))},
            ledger=[_evento(BASE + ROTAS[0], _hoje()),
                    _evento(BASE + ROTAS[0] + "index.md", _hoje())])
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("não estão no sitemap", saida)
        self.assertIn("GÊMEA MARKDOWN", saida)
        # Dizer QUAL é exigência: um gate que acusa sem nomear não é acionável.
        self.assertIn(BASE + ROTAS[0] + "index.md", saida)

    def test_anuncio_limpo_passa(self):
        # O controle pareado: o gate não pode passar a reprovar sempre.
        modulo = _prepara({"urls": _urls(set(ROTAS))},
                          ledger=[_evento(BASE + rota, _hoje()) for rota in ROTAS])
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("nada fora do sitemap foi anunciado", saida)

    def test_evento_recusado_pelo_operador_nao_e_poluicao_nossa(self):
        modulo = _prepara(
            {"urls": _urls(set(ROTAS))},
            ledger=[_evento(BASE + ROTAS[0] + "index.md", _hoje(), http_status=403)])
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)

    def test_reprova_por_FLUXO_e_nao_por_estoque(self):
        # Evento velho fora da janela conta como histórico e NÃO reprova: um
        # gate vermelho por dívida que nada drena é gate que ninguém lê.
        modulo = _prepara(
            {"urls": _urls(set(ROTAS))},
            ledger=[_evento(BASE + ROTAS[0] + "index.md", "2020-01-01T00:00:00+00:00")])
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("1 no histórico", saida)

    def test_classe_OUTRA_e_separada_da_gemea(self):
        modulo = _prepara(
            {"urls": _urls(set(ROTAS))},
            ledger=[_evento(BASE + "/aposentada/z/", _hoje())])
        codigo, saida = _roda(modulo)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("OUTRA (1)", saida)
        self.assertNotIn("GÊMEA MARKDOWN", saida)

    def test_a_FONTE_do_sentido_inverso_e_o_ledger_por_URL(self):
        """O falso-verde que este gate quase teve.

        `indexnow_submission_state.json` tem ZERO `.md` por CONSTRUÇÃO: quem o
        escreve só grava URL para a qual existe `public/<rota>/index.html`, e
        para `/x/index.md` esse caminho não existe. Um sentido inverso apoiado
        nele ficaria verde para sempre.

        Aqui o estado NÃO contém a gêmea (como em produção) e o ledger contém.
        Se alguém trocar a fonte, este teste fica verde por 0 e o
        `test_gemea_anunciada_REPROVA...` acima cai — é o par que mata o
        mutante.
        """
        estado = {"urls": _urls(set(ROTAS))}
        modulo = _prepara(estado, ledger=[_evento(BASE + ROTAS[0] + "index.md", _hoje())])
        self.assertNotIn(BASE + ROTAS[0] + "index.md", estado["urls"],
                         "a fixture tem de espelhar produção: o estado não vê a gêmea")
        gemeas, outras, no_periodo, _ = modulo.anunciadas_fora_do_sitemap(
            {BASE + rota for rota in ROTAS}, "2000-01-01")
        self.assertEqual(gemeas, [BASE + ROTAS[0] + "index.md"])
        self.assertEqual(outras, [])
        self.assertEqual(no_periodo, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
