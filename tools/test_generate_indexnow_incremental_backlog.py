#!/usr/bin/env python3
"""Prova, SEM nenhuma requisição de rede, que
`generate-indexnow-incremental-submit` drena o backlog de URLs sem recibo de
aceite — o defeito que deixou 6.803 páginas no ar sem nunca serem anunciadas ao
IndexNow (medido em 2026-09-08).

O DEFEITO QUE ESTE TESTE TRANCA. A semeadura de 2026-08-12 gravou no estado o
hash do conteúdo ATUAL de cada URL, marcando `seeded: true` e sem recibo. O delta
compara hash com hash; com o hash já igual, aquelas URLs nunca apareciam como
"mudadas" e o serviço diário imprimia "nada a submeter" com dois terços do acervo
por anunciar. O dono exportou 21 URLs fora do índice do Bing e as 21, sem
exceção, eram desse conjunto.

Cada teste abaixo falha contra a versão anterior da ferramenta — é a prova por
mutação de que eles medem a correção e não o acaso:

  - `test_pendente_sem_recibo_entra_na_selecao` falharia: o envio era só o delta.
  - `test_cota_diaria_e_compartilhada_entre_execucoes` falharia: não havia cota.
  - `test_ordem_do_backlog_faz_rodizio_entre_areas` falharia: não havia fila.

O teste é offline por construção: só o modo `--dry-run` é exercitado, e ele
retorna antes de qualquer POST ou subprocesso.
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
_ALVO = str(RAIZ / "tools" / "generate-indexnow-incremental-submit")
BASE = "https://exemplo.test"


def _carrega_modulo_fresco():
    """Uma CÓPIA nova por teste: o módulo calcula ROOT/ESTADO/SITE na importação,
    e um monkeypatch vazado entre testes esconderia defeito real."""
    loader = SourceFileLoader("generate_indexnow_incremental_submit_test_subject", _ALVO)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def _monta_arvore(raiz, rotas, estado):
    """Portal mínimo: site.json, um shard de sitemap e o HTML de cada rota."""
    os.makedirs(os.path.join(raiz, "content"), exist_ok=True)
    with io.open(os.path.join(raiz, "content/site.json"), "w", encoding="utf-8") as h:
        json.dump({"base_url": BASE}, h)

    os.makedirs(os.path.join(raiz, "public/sitemaps"), exist_ok=True)
    locs = "".join("<url><loc>%s%s</loc></url>" % (BASE, rota) for rota in rotas)
    with io.open(os.path.join(raiz, "public/sitemaps/pages-1.xml"), "w", encoding="utf-8") as h:
        h.write("<?xml version='1.0'?><urlset>%s</urlset>" % locs)

    for rota in rotas:
        destino = os.path.join(raiz, "public", rota.strip("/"))
        os.makedirs(destino, exist_ok=True)
        with io.open(os.path.join(destino, "index.html"), "w", encoding="utf-8") as h:
            h.write("<html>%s</html>" % rota)

    os.makedirs(os.path.join(raiz, "data/ops"), exist_ok=True)
    with io.open(os.path.join(raiz, "data/ops/indexnow_submission_state.json"),
                 "w", encoding="utf-8") as h:
        json.dump(estado, h)


def _aponta_modulo(modulo, raiz):
    modulo.ROOT = raiz
    modulo.SITE = os.path.join(raiz, "content/site.json")
    modulo.REVISAO = os.path.join(raiz, "data/ops/page_content_revision.jsonl")
    modulo.ESTADO = os.path.join(raiz, "data/ops/indexnow_submission_state.json")
    modulo.EVIDENCIA = os.path.join(raiz, "data/ops/indexnow_direct_submissions.jsonl")


def _sha_do_html(raiz, rota):
    import hashlib
    alvo = os.path.join(raiz, "public", rota.strip("/"), "index.html")
    with open(alvo, "rb") as h:
        return hashlib.sha256(h.read()).hexdigest()


def _estado_com(raiz, rotas, com_recibo):
    """Estado onde toda rota é conhecida com o hash do conteúdo atual — a
    situação exata da semeadura. `com_recibo` recebe `submitted_at`."""
    urls = {}
    for rota in rotas:
        registro = {"content_sha256": _sha_do_html(raiz, rota), "hash_source": "public_html"}
        if rota in com_recibo:
            registro["submitted_at"] = "2026-09-01T00:00:00+00:00"
            registro["http_status"] = 200
        else:
            registro["seeded"] = True
            registro["seeded_at"] = "2026-08-12T09:09:30+00:00"
        urls[BASE + rota] = registro
    return {"schema_version": "indexnow_submission_state_v1", "urls": urls}


def _roda(modulo, argumentos):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
        codigo = modulo.main()
    return codigo, saida.getvalue()


class DrenagemDoBacklog(unittest.TestCase):
    ROTAS = ["/familia/a/", "/familia/b/", "/tributario/c/", "/tributario/d/", "/aereo/e/"]

    def _prepara(self, com_recibo=(), tmp=None):
        raiz = tmp or tempfile.mkdtemp(prefix="indexnow-backlog-")
        # a árvore precisa existir antes do estado, que hasheia o HTML servido
        _monta_arvore(raiz, self.ROTAS, {"schema_version": "x", "urls": {}})
        estado = _estado_com(raiz, self.ROTAS, set(com_recibo))
        _monta_arvore(raiz, self.ROTAS, estado)
        modulo = _carrega_modulo_fresco()
        _aponta_modulo(modulo, raiz)
        return modulo, raiz

    def test_pendente_sem_recibo_entra_na_selecao(self):
        """O caso do defeito: hash igual ao do conteúdo atual e nenhum recibo."""
        modulo, raiz = self._prepara(com_recibo=["/familia/a/"])
        import sys
        sys.argv = ["x", "--dry-run"]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("sem recibo      : 4 URL(s)", saida)
        self.assertIn("a submeter      : 4 URL(s) (0 do delta + 4 do backlog)", saida)
        # a que já tem recibo NÃO volta ao fio
        self.assertNotIn("%s/familia/a/" % BASE, saida)

    def test_url_com_recibo_nunca_volta(self):
        modulo, raiz = self._prepara(com_recibo=self.ROTAS)
        import sys
        sys.argv = ["x", "--dry-run"]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("nada a submeter", saida)
        self.assertNotIn("sem recibo", saida)

    def test_sem_backlog_preserva_o_comportamento_antigo(self):
        modulo, raiz = self._prepara()
        import sys
        sys.argv = ["x", "--dry-run", "--sem-backlog"]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("drenagem desligada por --sem-backlog", saida)
        self.assertIn("nada a submeter", saida)

    def test_cota_limita_o_backlog_e_nao_o_delta(self):
        modulo, raiz = self._prepara()
        import sys
        sys.argv = ["x", "--dry-run", "--cota", "2"]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("a submeter      : 2 URL(s) (0 do delta + 2 do backlog)", saida)

    def test_delta_sai_inteiro_mesmo_com_cota_zero(self):
        """Conteúdo que mudou é o sinal do protocolo: a cota governa só a
        drenagem, nunca o delta."""
        modulo, raiz = self._prepara(com_recibo=self.ROTAS)
        alvo = os.path.join(raiz, "public/familia/a/index.html")
        with io.open(alvo, "w", encoding="utf-8") as h:
            h.write("<html>outro conteudo</html>")
        import sys
        sys.argv = ["x", "--dry-run", "--cota", "0"]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("a submeter      : 1 URL(s) (1 do delta + 0 do backlog)", saida)

    def test_cota_diaria_e_compartilhada_entre_execucoes(self):
        """Dois disparadores no mesmo dia (run-daily-content e o timer) não podem
        dobrar o volume: o contador vive no estado, não na execução."""
        modulo, raiz = self._prepara()
        estado = modulo.ler_estado()
        modulo.registra_drenagem(estado, 3, "2026-09-08T10:00:00+00:00")
        modulo.gravar_estado(estado)
        restante, ja = modulo.cota_restante_hoje(estado, 4, "2026-09-08T23:00:00+00:00")
        self.assertEqual((restante, ja), (1, 3))
        # virada do dia zera o contador
        restante, ja = modulo.cota_restante_hoje(estado, 4, "2026-09-09T00:01:00+00:00")
        self.assertEqual((restante, ja), (4, 0))

    def test_ordem_do_backlog_faz_rodizio_entre_areas(self):
        """Alfabético mandaria 1.000 URLs de uma área só no dia 1. O rodízio faz
        cada lote atravessar o acervo inteiro."""
        modulo, raiz = self._prepara()
        urls = [BASE + rota for rota in self.ROTAS]
        ordem = modulo.intercala_por_area(urls, BASE)
        areas = [modulo.area_da_url(u, BASE) for u in ordem]
        self.assertEqual(areas[:3], ["familia", "tributario", "aereo"])
        self.assertEqual(sorted(ordem), sorted(urls))
        self.assertEqual(ordem, modulo.intercala_por_area(urls, BASE), "não determinístico")

    def test_prioridade_le_o_csv_do_bing_com_bom_e_aspas(self):
        modulo, raiz = self._prepara()
        caminho = os.path.join(raiz, "bing.csv")
        with io.open(caminho, "w", encoding="utf-8-sig") as h:
            h.write('"URL"\n"%s/aereo/e/"\n"https://outro.test/x/"\n\n' % BASE)
        achadas = modulo.urls_de_arquivo(caminho, BASE)
        self.assertEqual(achadas, ["%s/aereo/e/" % BASE])

    def test_prioridade_vai_na_frente_da_fila(self):
        modulo, raiz = self._prepara()
        caminho = os.path.join(raiz, "bing.csv")
        with io.open(caminho, "w", encoding="utf-8-sig") as h:
            h.write('"URL"\n"%s/aereo/e/"\n' % BASE)
        import sys
        sys.argv = ["x", "--dry-run", "--cota", "1", "--prioridade", caminho]
        codigo, saida = _roda(modulo, sys.argv)
        self.assertEqual(codigo, 0, saida)
        self.assertIn("prioridade      : 1 URL(s)", saida)
        self.assertIn("%s/aereo/e/" % BASE, saida)

    def test_url_fora_do_sitemap_nao_entra_no_backlog(self):
        """O submissor REPROVA a execução inteira, antes do POST, se a lista
        trouxer URL que o sitemap não anuncia. Estado morto não pode derrubar o
        dia."""
        modulo, raiz = self._prepara()
        estado = modulo.ler_estado()
        estado["urls"][BASE + "/aposentada/z/"] = {
            "content_sha256": "0" * 64, "hash_source": "public_html", "seeded": True}
        modulo.gravar_estado(estado)
        hashes, _ = modulo.hashes_de_conteudo(
            modulo.sitemap_urls(BASE), BASE)
        pendentes = modulo.pendentes_sem_recibo(estado["urls"], hashes)
        self.assertNotIn(BASE + "/aposentada/z/", pendentes)
        self.assertEqual(len(pendentes), len(self.ROTAS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
