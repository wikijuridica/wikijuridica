#!/usr/bin/env python3
"""Testes de tools/check-edge-frescor — a prova diária de que a borda não serve rota mudada velha.

TODO teste roda OFFLINE: `busca` e `sha_disco` são injetados, nenhum toca a borda
nem o disco de produção. A sonda real já foi medida à mão em 2026-09-09 (287 de
288 rotas velhas na borda; gêmea em variante velha no cache de origem) — o que se
prova aqui é que a CLASSIFICAÇÃO lê a verdade certa e que o exit diz o que
aconteceu.

O caso que importa é a PROVA POR MUTAÇÃO. O oráculo do HTML é o DISCO, atestado
pelo manifesto. Se a comparação usasse o hash do manifesto em vez do disco, o
caso "disco diverge do manifesto" mudaria de classe nos dois sentidos possíveis:

  - borda == disco ≠ manifesto  →  o mutante diz "velha" e PURGA um defeito de
    publicação (traz para a borda um arquivo que ninguém atestou);
  - borda == manifesto ≠ disco  →  o mutante diz "fresca" e ESCONDE o defeito.

O mutante não é escrito à mão: nasce do fonte real de `classifica_html`, com
`sha_disco` trocado por `sha_manifesto` no corpo. O teste primeiro exige que o
fonte contenha o que a mutação vai trocar — um refactor que renomeie o parâmetro
reprova aqui em vez de deixar a mutação vazia passar em silêncio.

A segunda armadilha, medida no mesmo dia: a gêmea tem `Vary: Accept-Encoding` e
o nginx guarda um objeto por variante. A verdade é o Go (`:8089`); o nginx
(`:8088`) é o que a borda recebe num MISS e pode estar velho com a borda fresca.
Os testes cobrem a classe `origem_cache_velha`, a ordem origem → borda → releitura
e a leitura da variante `gzip, br` só pelo `Repr-Digest` (o corpo vem em brotli e
NÃO pode ser hasheado).

Rodar:
    python3 tools/test_check_edge_frescor.py
    python3 -m unittest discover -s tools -p 'test_check_edge_frescor.py'
"""
from __future__ import annotations

import base64
import contextlib
import datetime as dt
import hashlib
import importlib.machinery
import importlib.util
import inspect
import io
import json
import os
import pathlib
import sys
import tempfile
import textwrap
import unittest

AQUI = pathlib.Path(__file__).resolve().parent
# A prova por mutação precisa apontar a bancada para uma cópia mutada da
# ferramenta; sem isso o mutante teria de sobrescrever o arquivo vivo.
FERRAMENTA = pathlib.Path(os.environ.get("CHECK_EDGE_FRESCOR_BIN", str(AQUI / "check-edge-frescor")))
AQUECEDOR_DE_ORIGEM = AQUI / "warm-origin-cache"

sys.dont_write_bytecode = True  # mutante e original sempre lidos da fonte


def carrega():
    loader = importlib.machinery.SourceFileLoader("check_edge_frescor", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


M = carrega()
BASE = "https://wikijuridica.com.br"
AGORA = dt.datetime(2026, 9, 9, 14, 23, 20, tzinfo=dt.timezone.utc)


def sha(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def repr_digest(corpo):
    return "sha-256=:" + base64.b64encode(hashlib.sha256(corpo).digest()).decode() + ":"


def le_linhas(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


class Mundo:
    """Borda, Go, nginx e disco de mentira, endereçados por URL/caminho.

    `borda[url]` guarda o corpo que a borda serve; `go[url]` o que o processo Go
    serve; `nginx[(url, ae)]` o corpo que o cache de origem guarda POR VARIANTE
    de Accept-Encoding; `disco[path]` o conteúdo de public/<path>/index.html.
    A variante "gzip, br" sai com `content-encoding: br` e corpo opaco — o
    Repr-Digest é o do corpo real, como o nginx faz.
    """

    def __init__(self):
        self.borda = {}
        self.go = {}
        self.nginx = {}
        self.disco = {}
        # Como em produção: o manifesto tem milhares de rotas fora da janela do
        # dia. Sem esta semente, um teste com uma única rota institucional (fora
        # do manifesto) veria "manifesto vazio" — que é exit 2 de propósito.
        self.manifesto = {"/acervo/atestada-fora-da-janela/": sha("atestada")}
        self.revisoes = []
        self.pedidos = []
        self.purgas = []
        self.invalidacoes = []
        self.sequencia = []
        self.purga_exit = 0
        self.invalidacao_exit = 0
        self.purga_surte_efeito = True
        # Quantos objetos a zona do nginx guarda por rota. O padrão é 2 porque é
        # o que a zona viva tinha em 11.186 das 13.738 chaves em 2026-09-16
        # (principal + variante de `Vary: Accept-Encoding`).
        self.objetos_por_rota = 2
        # A janela de propagação medida (ESPERA_POS_PURGA_S) não se paga aqui: o
        # teste registra as esperas pedidas e segue. Quem mede o relógio é a
        # sonda na borda viva, não a bancada.
        self.esperas = []
        self.falhas = {}
        self.origem_ok = (True, "")
        # Ledgers endereçados por caminho (o snapshot de --desde-ledger) e os
        # arquivos de texto que o gate lê (as assinaturas da fórmula).
        self.ledgers = {}
        self.textos = {}

    def busca(self, url, cabecalhos, timeout=None):
        self.pedidos.append((url, dict(cabecalhos)))
        if url in self.falhas:
            raise M.FalhaDeSonda(self.falhas[url])
        if url.endswith("/readyz"):
            return 200, {}, b"ok"
        if url.startswith(M.GO):
            corpo = self.go.get(url)
            if corpo is None:
                return 404, {}, b"nao encontrado"
            return 200, {"repr-digest": repr_digest(corpo)}, corpo
        if url.startswith(M.ORIGEM):
            ae = cabecalhos.get("Accept-Encoding")
            corpo = self.nginx.get((url, ae))
            if corpo is None:
                return 404, {}, b"nao encontrado"
            cab = {"repr-digest": repr_digest(corpo)}
            if ae == "gzip, br":
                cab["content-encoding"] = "br"
                return 200, cab, b"\x1b\x00opaco-brotli"
            return 200, cab, corpo
        corpo = self.borda.get(url)
        if corpo is None:
            return 404, {"cf-cache-status": "MISS"}, b"nao encontrado"
        cab = {"cf-cache-status": "HIT", "age": "39932"}
        if url.endswith("index.md"):
            cab["repr-digest"] = repr_digest(corpo)
        return 200, cab, corpo

    def sha_disco(self, path):
        conteudo = self.disco.get(path)
        return None if conteudo is None else hashlib.sha256(conteudo).hexdigest()

    def purga(self, urls):
        self.purgas.append(list(urls))
        self.sequencia.append("borda")
        if self.purga_exit == 0 and self.purga_surte_efeito:
            # A purga real esvazia a borda; a releitura enche com a origem/disco.
            for url in urls:
                path = url[len(BASE):]
                if path.endswith("index.md"):
                    self.borda[url] = self.nginx[(M.ORIGEM + path, "gzip, br")]
                else:
                    self.borda[url] = self.disco[path]
        return self.purga_exit, "simulado"

    def purga_origem(self, rotas):
        """Dublê de tools/purge-origin-cache --de-arquivo - --json.

        Devolve o relatório por OBJETO, como a ferramenta real desde 2026-09-16:
        a zona guarda um objeto por variante de `Vary: Accept-Encoding`, e o
        número que interessa é quantos sobraram, não quantas rotas foram pedidas.
        """
        self.invalidacoes.append(list(rotas))
        self.sequencia.append("origem")
        por_rota, removidos, restantes = [], 0, 0
        for rota in rotas:
            objetos = self.objetos_por_rota
            if self.invalidacao_exit == 0 and self.purga_surte_efeito:
                for ae in M.VARIANTES_ACCEPT_ENCODING:
                    self.nginx[(M.ORIGEM + rota, ae)] = self.go[M.GO + rota]
                r, f = objetos, 0
            else:
                r, f = 0, objetos
            removidos += r
            restantes += f
            por_rota.append({"rota": rota, "objetos": objetos, "removidos": r, "restantes": f})
        relatorio = {"objetos_antes": sum(r["objetos"] for r in por_rota), "removidos": removidos,
                     "restantes": restantes, "rotas": por_rota}
        return self.invalidacao_exit, "simulado", relatorio

    def espera(self, segundos):
        self.esperas.append(segundos)

    def rota(self, path, disco, borda_html=None, go_md=None, borda_md=None, nginx_md=None,
             manifesto="igual_ao_disco", carimbo="2026-09-09T00:36:02Z", served=None):
        """Cadastra uma rota; por padrão tudo fresco e atestado, em todas as variantes."""
        disco_b = disco.encode()
        self.disco[path] = disco_b
        self.borda[BASE + path] = (borda_html if borda_html is not None else disco).encode()
        go_b = (go_md if go_md is not None else "# md de " + path).encode()
        self.go[M.GO + path + "index.md"] = go_b
        nginx_b = nginx_md.encode() if nginx_md is not None else go_b
        for ae in M.VARIANTES_ACCEPT_ENCODING:
            self.nginx[(M.ORIGEM + path + "index.md", ae)] = nginx_b
        self.borda[BASE + path + "index.md"] = borda_md.encode() if borda_md is not None else go_b
        if manifesto == "igual_ao_disco":
            self.manifesto[path] = hashlib.sha256(disco_b).hexdigest()
        elif manifesto is not None:
            self.manifesto[path] = manifesto
        entrada = {"path": path, "revised_on": carimbo, "content_sha256": sha(disco)}
        if served is not None:
            entrada["served_sha256"] = served
        self.revisoes.append(entrada)

    def deps(self, saida):
        return {
            "base": BASE, "dominio": "wikijuridica.com.br",
            "busca": self.busca, "sha_disco": self.sha_disco,
            "limitador": None, "agora": lambda: AGORA,
            "ler_revisoes": lambda: list(self.revisoes),
            "ler_manifesto": lambda: dict(self.manifesto),
            "origem_pronta": lambda busca, dominio: self.origem_ok,
            "purga": self.purga, "purga_origem": self.purga_origem, "saida": saida,
            "espera": self.espera,
            "ler_ledger_de": lambda caminho: list(self.ledgers.get(caminho, [])),
            "ler_texto": lambda caminho: self.textos.get(caminho, ""),
        }


def roda(mundo, *argv):
    """Executa main com o mundo injetado; devolve (exit, stdout, linha do ledger)."""
    with tempfile.TemporaryDirectory() as d:
        saida = os.path.join(d, "edge_frescor_daily.jsonl")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = M.main(list(argv) + ["--gravar"], deps=mundo.deps(saida))
        linhas = le_linhas(saida) if os.path.exists(saida) else []
        return rc, buf.getvalue(), (linhas[-1] if linhas else None)


class Fresca(unittest.TestCase):
    def test_tudo_fresco_sai_zero(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["rotas_mudadas"], 1)
        self.assertEqual(linha["conferidas"], 1)
        self.assertEqual(linha["frescas"], 1)
        self.assertEqual(linha["velhas"], [])
        self.assertEqual(linha["disco_diverge"], [])
        self.assertEqual(linha["origem_cache_velha"], [])
        self.assertEqual(linha["erros_de_sonda"], 0)
        self.assertIs(linha["counts_as_audience"], False)
        self.assertEqual(linha["schema_version"], "edge_frescor_v1")
        self.assertEqual(m.purgas, [])
        self.assertEqual(m.invalidacoes, [])

    def test_sonda_leva_ua_proprio_marca_de_warming_e_identity(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>")
        roda(m, "--dia", "2026-09-09")
        borda = [c for u, c in m.pedidos if u.startswith(BASE)]
        self.assertEqual(len(borda), 2, "HTML e gêmea, uma leitura cada")
        for cab in borda:
            self.assertEqual(cab["User-Agent"], "wikijuridica-superficie-probe/1.0")
            self.assertEqual(cab["X-Warming-Request"], "true")
            self.assertEqual(cab["Accept-Encoding"], "identity")
        locais = [(u, c) for u, c in m.pedidos if u.startswith(M.GO) or u.startswith(M.ORIGEM)]
        self.assertTrue(all(c.get("Host") == "wikijuridica.com.br" for _, c in locais))
        variantes = sorted(c["Accept-Encoding"] for u, c in locais if u.startswith(M.ORIGEM))
        self.assertEqual(variantes, sorted(M.VARIANTES_ACCEPT_ENCODING),
                         "o cache de origem é lido exatamente nas variantes que a borda pede")

    def test_variantes_sao_as_mesmas_do_aquecedor_de_origem(self):
        """A tupla é medida em tools/warm-origin-cache; mudar lá sem mudar aqui reprova."""
        fonte = AQUECEDOR_DE_ORIGEM.read_text(encoding="utf-8")
        self.assertIn('VARIANTES_ACCEPT_ENCODING = ("gzip, br", "")', fonte)
        self.assertEqual(M.VARIANTES_ACCEPT_ENCODING, ("gzip, br", ""))


class Velha(unittest.TestCase):
    def test_html_velho_lista_e_sai_um_sem_purgar(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>novo</html>", borda_html="<html>velho</html>")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas"], ["/familia/divorcio/"])
        self.assertEqual(linha["velhas_total"], 1)
        self.assertEqual(linha["velhas_por_canal"], {"html": 1, "md": 0})
        self.assertEqual(linha["frescas"], 0)
        self.assertIn(BASE + "/familia/divorcio/", saida)
        self.assertEqual(m.purgas, [], "sem --purgar nada pode ser purgado")
        self.assertEqual(linha["purgadas"], 0)
        self.assertIs(linha["purga_pedida"], False)

    def test_gemea_velha_na_borda_purga_so_a_url_da_gemea(self):
        m = Mundo()
        m.rota("/radar-ia/", "<html>ok</html>", go_md="date_modified: 2026-09-09T00:36:02Z",
               borda_md="date_modified: 2026-09-08", manifesto=None)
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas_por_canal"], {"html": 0, "md": 1})
        self.assertEqual(m.purgas, [[BASE + "/radar-ia/index.md"]])
        self.assertEqual(m.invalidacoes, [], "origem fresca não se invalida")
        self.assertEqual(linha["purgadas"], 1)
        self.assertEqual(linha["purga_exit"], 0)
        self.assertEqual(linha["pos_purga_velhas"], 0)
        self.assertEqual(linha["sem_manifesto"], ["/radar-ia/"])
        self.assertEqual(linha["velhas_detalhe"][0]["canal"], "md")
        self.assertEqual(linha["velhas_detalhe"][0]["cf_cache_status"], "HIT")
        self.assertEqual(linha["velhas_detalhe"][0]["age"], 39932)

    def test_gemea_e_comparada_com_o_go_e_nao_com_o_nginx(self):
        """Borda == nginx (velho) != Go: é velha. Ler o nginx como verdade diria fresca."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="velho")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas_por_canal"], {"html": 0, "md": 1})
        self.assertEqual(linha["origem_cache_velha"], ["/a/"])

    def test_rota_sem_manifesto_compara_com_o_disco(self):
        m = Mundo()
        m.rota("/sobre/", "<html>novo</html>", borda_html="<html>velho</html>", manifesto=None)
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas"], ["/sobre/"])
        self.assertEqual(m.purgas, [[BASE + "/sobre/"]])

    def test_purga_que_falha_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>novo</html>", borda_html="<html>velho</html>")
        m.purga_exit = 2
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["purga_exit"], 2)
        self.assertEqual(linha["purgadas"], 0)
        self.assertIsNone(linha["pos_purga_velhas"], "sem purga bem-sucedida não há releitura")

    def test_purga_que_nao_surte_efeito_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>novo</html>", borda_html="<html>velho</html>")
        m.purga_surte_efeito = False
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["purga_exit"], 0)
        self.assertEqual(linha["pos_purga_velhas"], 1)

    def test_purga_real_recebe_teto_igual_ao_tamanho_da_lista(self):
        chamadas = []

        class Proc:
            returncode = 0
            stdout = "OK"
            stderr = ""

        def executor(comando, **kw):
            chamadas.append((comando, kw))
            return Proc()

        urls = [BASE + "/a/", BASE + "/b/index.md"]
        rc, _ = M.purga_por_url(urls, executor=executor)
        self.assertEqual(rc, 0)
        comando, kw = chamadas[0]
        self.assertEqual(comando[0], M.PURGE)
        self.assertIn("--de-arquivo", comando)
        self.assertEqual(comando[comando.index("--teto-por-url") + 1], "2")
        self.assertEqual(kw["input"], "\n".join(urls) + "\n")

    def test_invalidacao_real_passa_uma_rota_por_flag(self):
        chamadas = []

        class Proc:
            returncode = 0
            stdout = json.dumps({"objetos_antes": 4, "removidos": 2, "restantes": 0,
                                 "rotas": [{"rota": "/a/index.md", "objetos": 2, "removidos": 1,
                                            "restantes": 0},
                                           {"rota": "/b/index.md", "objetos": 2, "removidos": 1,
                                            "restantes": 0}]})
            stderr = ""

        entradas = []

        def executor(comando, **kw):
            chamadas.append(comando)
            entradas.append(kw.get("input"))
            return Proc()

        rc, _, relatorio = M.invalida_origem(["/a/index.md", "/b/index.md"], executor=executor)
        self.assertEqual(rc, 0)
        self.assertEqual(chamadas[0], [M.PURGE_ORIGEM, "--de-arquivo", "-", "--json"])
        self.assertEqual(entradas[0], "/a/index.md\n/b/index.md\n")
        self.assertEqual(relatorio["removidos"], 2)


class OrigemVelha(unittest.TestCase):
    def test_borda_fresca_com_cache_de_origem_velho_e_classe_propria(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="novo")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas"], [])
        self.assertEqual(linha["frescas"], 0)
        self.assertEqual(linha["origem_cache_velha"], ["/a/"])
        self.assertEqual(linha["origem_cache_velha_classe"], 1)
        self.assertEqual(sorted(linha["origem_cache_detalhe"][0]["variantes_velhas"]), ["", "gzip, br"])
        self.assertIn("/a/index.md", saida)

    def test_purgar_invalida_a_origem_sem_tocar_na_borda_fresca(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="novo")
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(m.invalidacoes, [["/a/index.md"]])
        self.assertEqual(m.purgas, [], "borda fresca não se purga")
        self.assertEqual(linha["invalidadas_origem"], 1)
        self.assertEqual(linha["invalidacao_origem_exit"], 0)
        self.assertEqual(linha["pos_purga_velhas"], 0)

    def test_origem_e_invalidada_antes_da_borda(self):
        """A ordem do deploy-binario-go: purgar a borda primeiro repopula com o velho."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="velho")
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(m.sequencia, ["origem", "borda"])
        self.assertEqual(linha["pos_purga_velhas"], 0)

    def test_invalidacao_que_falha_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="novo")
        m.invalidacao_exit = 2
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["invalidacao_origem_exit"], 2)

    def test_variante_gzip_br_e_lida_so_pelo_repr_digest(self):
        """O corpo da variante vem em brotli e é opaco; hasheá-lo diria 'velha' para tudo."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["origem_cache_velha"], [])

    def test_variante_sem_repr_digest_e_erro(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        busca_original = m.busca

        def busca_sem_digest(url, cabecalhos, timeout=None):
            status, cab, corpo = busca_original(url, cabecalhos, timeout)
            if url.startswith(M.ORIGEM) and cabecalhos.get("Accept-Encoding") == "gzip, br":
                cab = {k: v for k, v in cab.items() if k != "repr-digest"}
            return status, cab, corpo

        m.busca = busca_sem_digest
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["erros_detalhe"][0]["canal"], "origem:gzip, br")
        self.assertIn("Repr-Digest", linha["erros_detalhe"][0]["erro"])


class InvalidacaoMedida(unittest.TestCase):
    """O NÚMERO QUE DIZ QUE INVALIDOU TEM DE MEDIR AUSÊNCIA (2026-09-16).

    Até esta data `invalidadas_origem` era `len(rotas)` quando o exit fosse 0, e
    `tools/purge-origin-cache` saía 0 mesmo removendo 1 de 3 objetos — ou nenhum.
    A série de `edge_frescor_daily.jsonl` mostrou o preço: `pos_purga_velhas`
    repetindo `origem_cache_velha_total` cinco dias seguidos (794≈796, 297=297,
    48=48, 8=8, 6=6) com `invalidadas_origem` igual ao número de rotas pedidas.
    """

    def test_objeto_que_resiste_zera_a_contagem_e_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="velho")
        m.purga_surte_efeito = False  # a ferramenta não remove: os objetos ficam
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["objetos_origem_antes"], 2)
        self.assertEqual(linha["objetos_origem_removidos"], 0)
        self.assertEqual(linha["objetos_origem_restantes"], 2)
        self.assertEqual(linha["invalidadas_origem"], 0,
                         "rota com objeto restante NÃO conta como invalidada")

    def test_conta_rota_so_quando_removeu_e_nada_sobrou(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="velho")
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["invalidadas_origem"], 1)
        self.assertEqual(linha["objetos_origem_removidos"], 2,
                         "a zona guarda um objeto por variante de Vary, não um por rota")
        self.assertEqual(linha["objetos_origem_restantes"], 0)

    def test_origem_ainda_velha_nao_purga_a_borda_e_sai_dois(self):
        """O CONTROLE DA ORDEM: purgar a borda com a origem velha repopula o velho.

        Medido em 2026-09-16 em `/noticias/index.md`: purga só da borda devolveu
        `MISS` em 1,11 s com o corpo ANTIGO; com a origem invalidada antes, `MISS`
        em 1,03 s com o corpo do Go.
        """
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="velho", borda_md="velho")
        # A ferramenta remove os objetos e diz que removeu, mas o nginx continua
        # servindo a resposta anterior — variante que a fórmula não alcançou.
        purga_original = m.purga_origem

        def purga_sem_efeito_no_nginx(rotas):
            codigo, texto, relatorio = purga_original(rotas)
            for rota in rotas:
                for ae in M.VARIANTES_ACCEPT_ENCODING:
                    m.nginx[(M.ORIGEM + rota, ae)] = b"velho"
            return codigo, texto, relatorio

        m.purga_origem = purga_sem_efeito_no_nginx
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(m.purgas, [], "a borda NÃO pode ser purgada com a origem velha")
        self.assertEqual(linha["origem_velha_apos_invalidacao"], ["/a/index.md"])
        self.assertEqual(linha["origem_velha_apos_invalidacao_total"], 1)
        self.assertIn("continua servindo o objeto anterior", saida)


class JanelaDePropagacao(unittest.TestCase):
    """A releitura pós-purga se repete dentro da janela MEDIDA (2026-09-16).

    Oito purgas por URL na borda viva convergiram entre 0,10 s e 0,72 s do
    retorno da API. Uma amostra só não distinguia "ainda não propagou" de "purga
    que não purgou", e as duas saíam pelo mesmo exit 2 — alerta ao dono.
    """

    def test_converge_na_segunda_tentativa_sem_falso_vermelho(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="novo", borda_md="velho")
        purga_original = m.purga
        estado = {"chamadas": 0}

        def purga_com_atraso(urls):
            estado["chamadas"] += 1
            codigo, texto = purga_original(urls)
            # A borda só reflete a purga na SEGUNDA leitura: é o atraso que a
            # medição encontrou (sub-segundo), reproduzido aqui sem relógio.
            for url in urls:
                m.borda[url] = b"velho"
            return codigo, texto

        m.purga = purga_com_atraso
        leituras = {"n": 0}
        busca_original = m.busca

        def busca_com_propagacao(url, cabecalhos, timeout=None):
            if url == BASE + "/a/index.md":
                leituras["n"] += 1
                if leituras["n"] > 2:  # a 1a é a medição; a 2a é a releitura imediata
                    m.borda[url] = m.go[M.GO + "/a/index.md"]
            return busca_original(url, cabecalhos, timeout)

        m.busca = busca_com_propagacao
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["pos_purga_velhas"], 0)
        self.assertEqual(linha["pos_purga_tentativas"], 2)
        self.assertEqual(m.esperas, [M.ESPERA_POS_PURGA_S[1]],
                         "esperou exatamente a segunda janela medida")
        self.assertEqual(linha["pos_purga_espera_s"], M.ESPERA_POS_PURGA_S[1],
                         "`espera` conta SÓ o que se esperou pela propagação")
        self.assertIsNotNone(linha["pos_purga_releitura_s"],
                             "o relógio de parede da releitura vai em campo próprio")

    def test_velha_de_verdade_continua_saindo_dois_depois_da_janela(self):
        """O CONTROLE da retentativa: esgotada a janela, velha continua velha."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md="novo", nginx_md="novo", borda_md="velho")
        m.purga_surte_efeito = False
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["pos_purga_velhas"], 1)
        self.assertEqual(linha["pos_purga_tentativas"], len(M.ESPERA_POS_PURGA_S))
        self.assertEqual(m.esperas, list(M.ESPERA_POS_PURGA_S[1:]))


class BlocoDeRelacionados(unittest.TestCase):
    """O oráculo que se move — diagnóstico, NUNCA isenção (2026-09-16).

    Medido: o `sha_go` de 6/6 rotas mudou em 9 h sem republicação, e em
    `/diarios/rs-20260914/index.md` o diff ficou inteiro no bloco "Conteúdos
    relacionados". O gate irmão do HTML já neutraliza a seção equivalente; aqui a
    rota continua VELHA e continua sendo purgada, e o campo só CONTA o fenômeno.
    """

    CORPO = ("# titulo\n\ntexto\n\n## Conteúdos relacionados\n\n"
             "- [a](https://x/a/index.md)\n- [b](https://x/b/index.md)\n\n"
             "Versão canônica: <https://x/>\n")
    OUTRO_RELACIONADO = CORPO.replace("- [b](https://x/b/index.md)", "- [c](https://x/c/index.md)")
    OUTRO_CORPO = CORPO.replace("texto", "texto novo")
    OUTRO_FIM = CORPO.replace("Versão canônica: <https://x/>", "Versão canônica: <https://x/y/>")

    def test_divergencia_so_no_bloco_e_contada_mas_continua_velha(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md=self.CORPO, nginx_md=self.CORPO,
               borda_md=self.OUTRO_RELACIONADO)
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas"], ["/a/"], "continua VELHA — o campo não isenta ninguém")
        self.assertEqual(linha["velhas_so_relacionados"], 1)

    def test_divergencia_fora_do_bloco_nao_e_contada(self):
        """O CONTROLE: corpo alterado fora do bloco não pode entrar na conta."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md=self.CORPO, nginx_md=self.CORPO,
               borda_md=self.OUTRO_CORPO)
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas"], ["/a/"])
        self.assertEqual(linha["velhas_so_relacionados"], 0)

    def test_divergencia_depois_do_bloco_nao_e_contada(self):
        """O segundo CONTROLE: o que vem DEPOIS do bloco continua sob o hash —
        cortar o documento no marcador cegaria o fim da gêmea, onde moram o JSON
        de citação e a versão canônica."""
        m = Mundo()
        m.rota("/a/", "<html>a</html>", go_md=self.CORPO, nginx_md=self.CORPO,
               borda_md=self.OUTRO_FIM)
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["velhas_so_relacionados"], 0)

    def test_corpo_sem_o_marcador_nao_muda_de_sha(self):
        corpo = b"# titulo\n\ntexto\n"
        self.assertEqual(M.sha_sem_relacionados(corpo), hashlib.sha256(corpo).hexdigest())


class DiscoDiverge(unittest.TestCase):
    def test_disco_diverge_nao_purga_e_sai_um(self):
        m = Mundo()
        m.rota("/a/", "<html>disco</html>", borda_html="<html>disco</html>", manifesto=sha("<html>publicado</html>"))
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["disco_diverge"], ["/a/"])
        self.assertEqual(linha["disco_diverge_total"], 1)
        self.assertEqual(linha["velhas"], [])
        self.assertEqual(m.purgas, [], "defeito de publicação nunca vira purga")
        self.assertEqual(linha["disco_diverge_detalhe"][0]["motivo"], "disco_diverge_do_manifesto")
        self.assertIs(linha["disco_diverge_detalhe"][0]["borda_igual_manifesto"], False)

    def test_disco_ausente_e_defeito_de_publicacao(self):
        m = Mundo()
        m.rota("/a/", "<html>x</html>")
        del m.disco["/a/"]
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(linha["disco_diverge"], ["/a/"])
        self.assertEqual(linha["disco_diverge_detalhe"][0]["motivo"], "disco_ausente")
        self.assertEqual(m.purgas, [])

    def test_mutante_que_compara_com_o_manifesto_muda_a_classe(self):
        """A prova: com `sha_disco` trocado por `sha_manifesto`, o caso "disco diverge" muda de classe."""
        fonte = textwrap.dedent(inspect.getsource(M.classifica_html))
        cabecalho, corpo = fonte.split("\n", 1)
        self.assertIn("sha_disco", cabecalho)
        self.assertGreaterEqual(corpo.count("sha_disco"), 3,
                                "o corpo precisa ler o disco; sem isso a mutação seria vazia")
        mutante_fonte = cabecalho + "\n" + corpo.replace("sha_disco", "sha_manifesto")
        espaco = {"DISCO_AUSENTE": M.DISCO_AUSENTE, "DISCO_DIVERGE": M.DISCO_DIVERGE,
                  "VELHA": M.VELHA, "FRESCA": M.FRESCA}
        exec(compile(mutante_fonte, "<mutante classifica_html>", "exec"), espaco)
        mutante = espaco["classifica_html"]

        disco, manifesto = sha("disco"), sha("publicado")
        casos = {
            "borda == disco != manifesto": (disco, disco, manifesto),
            "borda == manifesto != disco": (manifesto, disco, manifesto),
        }
        vereditos = {}
        for nome, (borda, d, man) in casos.items():
            original = M.classifica_html(borda, d, man)
            mutado = mutante(borda, d, man)
            vereditos[nome] = (original, mutado)
            self.assertEqual(original, M.DISCO_DIVERGE, nome)
            self.assertNotEqual(mutado, M.DISCO_DIVERGE,
                                "%s: o mutante deveria mudar a classe e não mudou" % nome)
        # Os dois sentidos do erro, nomeados: purgar defeito e esconder defeito.
        self.assertEqual(vereditos["borda == disco != manifesto"][1], M.VELHA)
        self.assertEqual(vereditos["borda == manifesto != disco"][1], M.FRESCA)
        print("\n  mutante (manifesto no lugar do disco) VERMELHO:")
        for nome, (orig, mut) in vereditos.items():
            print("    %-30s original=%-28s mutante=%s" % (nome, orig, mut))

    def test_classificador_puro_nas_quatro_classes(self):
        d, man, outro = sha("d"), sha("m"), sha("o")
        self.assertEqual(M.classifica_html(d, d, d), M.FRESCA)
        self.assertEqual(M.classifica_html(outro, d, d), M.VELHA)
        self.assertEqual(M.classifica_html(d, d, man), M.DISCO_DIVERGE)
        self.assertEqual(M.classifica_html(d, None, man), M.DISCO_AUSENTE)
        self.assertEqual(M.classifica_html(outro, d, None), M.VELHA, "sem manifesto, o disco decide")
        self.assertEqual(M.classifica_html(d, d, None), M.FRESCA)


class Teto(unittest.TestCase):
    def test_acima_do_teto_sai_dois_e_nao_sonda_nem_grava(self):
        m = Mundo()
        for i in range(3):
            m.rota("/r%d/" % i, "<html>%d</html>" % i)
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--max", "2")
        self.assertEqual(rc, 2, saida)
        self.assertIn("3 rotas excedem o teto de 2", saida)
        self.assertIsNone(linha, "acima do teto nada é gravado")
        self.assertEqual([u for u, _ in m.pedidos], [], "acima do teto nada é sondado")

    def test_no_teto_confere_todas(self):
        m = Mundo()
        for i in range(3):
            m.rota("/r%d/" % i, "<html>%d</html>" % i)
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--max", "3")
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["conferidas"], 3)


class ErroDeSonda(unittest.TestCase):
    def test_sonda_que_nao_completa_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        m.falhas[BASE + "/a/"] = "timeout"
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["erros_de_sonda"], 1)
        self.assertEqual(linha["conferidas"], 0)
        self.assertEqual(linha["erros_detalhe"][0]["canal"], "html")

    def test_go_fora_e_erro_da_gemea(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        m.falhas[M.GO + "/a/index.md"] = "connection refused"
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["erros_detalhe"][0]["canal"], "md")
        self.assertIn("go:", linha["erros_detalhe"][0]["erro"])

    def test_repr_digest_que_nao_bate_e_erro_nao_velha(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        busca_original = m.busca

        def busca_com_digest_errado(url, cabecalhos, timeout=None):
            status, cab, corpo = busca_original(url, cabecalhos, timeout)
            if url == BASE + "/a/index.md":
                cab = dict(cab, **{"repr-digest": repr_digest(b"outro corpo")})
            return status, cab, corpo

        m.busca = busca_com_digest_errado
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["velhas"], [])
        self.assertEqual(m.purgas, [])
        self.assertIn("Repr-Digest", linha["erros_detalhe"][0]["erro"])

    def test_corpo_comprimido_e_erro(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        busca_original = m.busca

        def busca_comprimida(url, cabecalhos, timeout=None):
            status, cab, corpo = busca_original(url, cabecalhos, timeout)
            if url == BASE + "/a/":
                cab = dict(cab, **{"content-encoding": "br"})
            return status, cab, corpo

        m.busca = busca_comprimida
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertIn("comprimido", linha["erros_detalhe"][0]["erro"])

    def test_origem_fora_sai_dois_antes_de_sondar(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        m.origem_ok = (False, "nginx /readyz respondeu 503")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertIn("503", saida)
        self.assertIsNone(linha)

    def test_pre_voo_real_exige_nginx_e_go(self):
        def busca(url, cabecalhos, timeout=None):
            return (200 if url.startswith(M.ORIGEM) else 503), {}, b""

        pronta, motivo = M.origem_pronta(busca, "wikijuridica.com.br")
        self.assertFalse(pronta)
        self.assertIn("go", motivo)

    def test_ledger_vazio_sai_dois(self):
        m = Mundo()
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)

    def test_canal_velho_vence_o_erro_do_outro_e_ainda_assim_sai_dois(self):
        m = Mundo()
        m.rota("/a/", "<html>novo</html>", borda_html="<html>velho</html>")
        m.falhas[BASE + "/a/index.md"] = "timeout"
        rc, saida, linha = roda(m, "--dia", "2026-09-09", "--purgar")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["velhas"], ["/a/"])
        self.assertEqual(m.purgas[0], [BASE + "/a/"], "o canal medido velho é purgado mesmo com o outro em erro")
        self.assertEqual(linha["erros_de_sonda"], 1)


class Janela(unittest.TestCase):
    def test_desde_horas_inclui_dia_puro_que_toca_a_janela(self):
        entradas = [
            {"path": "/ontem-dia/", "revised_on": "2026-09-08"},
            {"path": "/anteontem-dia/", "revised_on": "2026-09-07"},
            {"path": "/hoje-instante/", "revised_on": "2026-09-09T00:36:02Z"},
            {"path": "/ontem-instante-fora/", "revised_on": "2026-09-08T10:00:00Z"},
            {"path": "/ontem-instante-dentro/", "revised_on": "2026-09-08T15:00:00Z"},
            {"path": "/quebrado/", "revised_on": "08/09/2026"},
        ]
        desde = AGORA - dt.timedelta(hours=24)
        rotas, invalidos = M.rotas_mudadas(entradas, desde=desde)
        self.assertEqual(rotas, ["/hoje-instante/", "/ontem-dia/", "/ontem-instante-dentro/"])
        self.assertEqual(invalidos, 1)

    def test_dia_casa_pelo_prefixo(self):
        entradas = [
            {"path": "/a/", "revised_on": "2026-09-09"},
            {"path": "/b/", "revised_on": "2026-09-09T23:59:59Z"},
            {"path": "/c/", "revised_on": "2026-09-08"},
        ]
        rotas, _ = M.rotas_mudadas(entradas, dia="2026-09-09")
        self.assertEqual(rotas, ["/a/", "/b/"])

    def test_sem_rota_no_dia_sai_zero_com_linha_vazia(self):
        """Dia DENTRO do alcance do ledger e sem rota: verde, linha vazia, zero sondas.

        Até 2026-09-11 este teste pedia `--dia 2026-09-09` contra um ledger que
        carimbava 2026-09-01 — o dia estava ALÉM do alcance, e o verde que ele
        exigia era o falso verde que `alcance_do_ledger` passou a recusar (ver
        a classe JanelaVazia). O caso que ele guarda continua guardado, agora
        com a janela que o ledger cobre de fato.
        """
        m = Mundo()
        m.rota("/a/", "<html>a</html>", carimbo="2026-09-01")
        rc, saida, linha = roda(m, "--dia", "2026-08-30")
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["rotas_mudadas"], 0)
        self.assertEqual(m.pedidos, [])

    def test_soma_das_classes_fecha_com_as_rotas(self):
        m = Mundo()
        m.rota("/fresca/", "<html>a</html>")
        m.rota("/velha/", "<html>b</html>", borda_html="<html>velho</html>")
        m.rota("/diverge/", "<html>c</html>", manifesto=sha("outro"))
        m.rota("/origem/", "<html>d</html>", go_md="novo", nginx_md="velho", borda_md="novo")
        m.rota("/erro/", "<html>e</html>")
        m.falhas[BASE + "/erro/"] = "timeout"
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertEqual(linha["frescas"] + linha["velhas_total"] + linha["disco_diverge_total"]
                         + linha["origem_cache_velha_classe"] + linha["erros_de_sonda"],
                         linha["rotas_mudadas"])
        self.assertEqual(linha["conferidas"], 4)


class Ledger(unittest.TestCase):
    def test_linha_identica_nao_se_regrava(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "l.jsonl")
            linha = {"schema_version": "edge_frescor_v1", "date": "2026-09-09", "frescas": 1,
                     "duracao_s": 1.5}
            self.assertTrue(M.grava(linha, caminho))
            self.assertFalse(M.grava(dict(linha, duracao_s=9.9), caminho),
                             "duracao_s é volátil e não distingue linhas")
            self.assertTrue(M.grava(dict(linha, frescas=2), caminho))
            gravadas = le_linhas(caminho)
            self.assertEqual(len(gravadas), 2)
            self.assertTrue(all("gerado_em" in g for g in gravadas))

    def test_sem_gravar_nada_e_escrito(self):
        m = Mundo()
        m.rota("/a/", "<html>a</html>")
        with tempfile.TemporaryDirectory() as d:
            saida = os.path.join(d, "l.jsonl")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = M.main(["--dia", "2026-09-09"], deps=m.deps(saida))
            self.assertEqual(rc, 0)
            self.assertFalse(os.path.exists(saida), "check-* sem --gravar é read-only")

    def test_listas_no_teto_de_cinquenta_com_total_ao_lado(self):
        m = Mundo()
        for i in range(60):
            m.rota("/v%02d/" % i, "<html>%d</html>" % i, borda_html="<html>velho</html>")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 1, saida)
        self.assertEqual(len(linha["velhas"]), 50)
        self.assertEqual(linha["velhas_total"], 60)
        self.assertEqual(saida.count(BASE + "/v"), 60, "a saída lista TODAS, o ledger corta em 50")


class ReprDigest(unittest.TestCase):
    def test_decodifica_forma_da_rfc_9530(self):
        corpo = b"abc"
        self.assertEqual(M.decodifica_repr_digest(repr_digest(corpo)), hashlib.sha256(corpo).hexdigest())
        self.assertIsNone(M.decodifica_repr_digest(None))
        self.assertIsNone(M.decodifica_repr_digest("sha-512=:AAAA:"))
        self.assertIsNone(M.decodifica_repr_digest("lixo"))

    def test_caminho_no_disco_da_home_e_das_rotas(self):
        self.assertEqual(M.caminho_no_disco("/"), os.path.join(M.PUBLIC, "index.html"))
        self.assertEqual(M.caminho_no_disco("/familia/x/"), os.path.join(M.PUBLIC, "familia", "x", "index.html"))



class JanelaVazia(unittest.TestCase):
    """Zero rota conferida não é frescor provado.

    Medido em 2026-09-11, logo depois de um `deploy-publico` que mudou 902
    páginas: o gate sem argumento pediu o dia de HOJE em UTC, o ledger carimbava
    o dia ANTERIOR, e a saída foi `rotas mudadas 0 · conferidas 0 · OK`. Verde
    com zero conferidas. Com `--dia` do dia carimbado, o MESMO gate conferiu
    1.520 rotas e achou 1.520 frescas.
    """

    def test_dia_alem_do_ledger_e_inconclusivo(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>", carimbo="2026-09-08T10:00:00Z")
        rc, saida, linha = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertIn("alcança até 2026-09-08", saida)
        self.assertIn("2026-09-09", saida)
        self.assertIsNone(linha, "janela inconclusiva não grava linha no ledger")

    def test_dia_coberto_sem_rota_continua_verde(self):
        """O verde legítimo não pode virar vermelho: dia dentro do alcance e sem rota."""
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>", carimbo="2026-09-08T10:00:00Z")
        rc, saida, linha = roda(m, "--dia", "2026-09-07")
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["rotas_mudadas"], 0)
        self.assertEqual(linha["conferidas"], 0)

    def test_desde_horas_alem_do_ledger_e_inconclusivo(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>", carimbo="2026-09-08T10:00:00Z")
        rc, saida, _ = roda(m, "--desde-horas", "2")
        self.assertEqual(rc, 2, saida)
        self.assertIn("alcança até 2026-09-08", saida)

    def test_ledger_sem_carimbo_legivel_e_inconclusivo(self):
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>", carimbo="ontem de manhã")
        rc, saida, _ = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc, 2, saida)
        self.assertIn("nenhum carimbo de revisão legível", saida)

    def test_mutante_que_diz_que_o_ledger_alcanca_tudo_devolve_falso_verde(self):
        """Sem `alcance_do_ledger`, o dia além do ledger volta a sair VERDE com 0 conferidas."""
        m = Mundo()
        m.rota("/familia/divorcio/", "<html>a</html>", carimbo="2026-09-08T10:00:00Z")
        original = M.alcance_do_ledger
        try:
            M.alcance_do_ledger = lambda entradas: (
                dt.datetime(2099, 1, 1, tzinfo=dt.timezone.utc), "2099-01-01")
            rc_mutante, saida_mutante, linha_mutante = roda(m, "--dia", "2026-09-09")
        finally:
            M.alcance_do_ledger = original
        rc_real, _, _ = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc_real, 2, "o original tem de recusar")
        self.assertEqual(rc_mutante, 0, saida_mutante)
        self.assertEqual(linha_mutante["conferidas"], 0,
                         "o falso verde é exatamente este: passa sem conferir nada")
        print("\n  mutante (ledger alcança tudo) VERDE com 0 conferidas; original exit=2")

    def test_mutante_que_pega_o_carimbo_mais_VELHO_reprova_dia_coberto(self):
        """A função tem de acompanhar o carimbo MAIS NOVO; com o mais velho, verde legítimo vira vermelho."""
        fonte = textwrap.dedent(inspect.getsource(M.alcance_do_ledger))
        self.assertIn("intervalo[1] > fim", fonte,
                      "o fonte precisa comparar pelo mais novo; sem isso a mutação seria vazia")
        mutante_fonte = fonte.replace("intervalo[1] > fim", "intervalo[1] < fim")
        espaco = {"intervalo_do_carimbo": M.intervalo_do_carimbo}
        exec(compile(mutante_fonte, "<mutante alcance_do_ledger>", "exec"), espaco)
        mutante = espaco["alcance_do_ledger"]
        entradas = [{"path": "/a/", "revised_on": "2026-09-05T10:00:00Z"},
                    {"path": "/b/", "revised_on": "2026-09-08T10:00:00Z"}]
        self.assertEqual(M.alcance_do_ledger(entradas)[1], "2026-09-08")
        self.assertEqual(mutante(entradas)[1], "2026-09-05",
                         "o mutante deveria ficar com o carimbo velho")

        m = Mundo()
        m.rota("/a/", "<html>a</html>", carimbo="2026-09-05T10:00:00Z")
        m.rota("/b/", "<html>b</html>", carimbo="2026-09-08T10:00:00Z")
        original = M.alcance_do_ledger
        try:
            M.alcance_do_ledger = mutante
            rc_mutante, saida_mutante, _ = roda(m, "--dia", "2026-09-07")
        finally:
            M.alcance_do_ledger = original
        rc_real, saida_real, _ = roda(m, "--dia", "2026-09-07")
        self.assertEqual(rc_real, 0, saida_real)
        self.assertEqual(rc_mutante, 2, saida_mutante)


class JanelaPorBytes(unittest.TestCase):
    """`--desde-ledger`: a janela que enxerga `--ressemear`.

    O caso que motivou o modo, medido em 2026-09-11: o `--ressemear` regrava o
    `served_sha256` SEM avançar `revised_on`, então a rota que mudou de bytes
    fica com carimbo velho e NENHUMA janela por data a alcança. Pior, o ledger
    costuma já alcançar o dia corrente por causa da publicação da madrugada
    (451 rotas naquele dia), então `--dia hoje` sai VERDE sobre o conjunto
    errado — o que parece prova e não é.

    Por isso `test_served_muda_com_carimbo_parado_e_o_caso_do_ressemear` é o
    teste-âncora desta classe: a rota tem carimbo de dias atrás, `content_sha256`
    idêntico, e só o `served_sha256` diferente.
    """

    SNAP = "/tmp/nao-existe/snapshot-de-teste.jsonl"
    FORMULA = "29055289b861d603f90fccfe78ea6db1f1e010cb8e8c2a5c8520b64445f5eac0"

    def mundo(self, formula_do_snapshot=FORMULA, formula_de_hoje=FORMULA):
        m = Mundo()
        if formula_de_hoje is not None:
            m.textos[M.FORMULA_ATUAL] = formula_de_hoje + "\n"
        if formula_do_snapshot is not None:
            m.textos[M.sufixo_de_formula(self.SNAP)] = formula_do_snapshot + "\n"
        return m

    def test_served_muda_com_carimbo_parado_e_o_caso_do_ressemear(self):
        m = self.mundo()
        m.rota("/a/", "<html>a</html>", carimbo="2026-09-01", served=sha("a-depois"))
        m.rota("/b/", "<html>b</html>", carimbo="2026-09-01", served=sha("b-igual"))
        m.ledgers[self.SNAP] = [
            {"path": "/a/", "revised_on": "2026-09-01", "content_sha256": sha("<html>a</html>"),
             "served_sha256": sha("a-antes")},
            {"path": "/b/", "revised_on": "2026-09-01", "content_sha256": sha("<html>b</html>"),
             "served_sha256": sha("b-igual")},
        ]
        rc, saida, linha = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["conferidas"], 1, saida)
        self.assertEqual(linha["criterio"]["bytes_mudados"], 1, saida)
        self.assertEqual(linha["criterio"]["rotas_novas"], 0, saida)
        self.assertEqual(linha["criterio"]["comparaveis"], 2, saida)
        # E a mesma rota é INVISÍVEL para a janela por data, que é o ponto:
        rc_dia, saida_dia, linha_dia = roda(m, "--dia", "2026-09-09")
        self.assertEqual(rc_dia, 2, saida_dia)
        self.assertIsNone(linha_dia)

    def test_rota_nova_entra_e_rota_removida_nao(self):
        m = self.mundo()
        m.rota("/nova/", "<html>nova</html>", served=sha("nova"))
        m.ledgers[self.SNAP] = [
            {"path": "/sumida/", "revised_on": "2026-09-01", "served_sha256": sha("sumida")},
        ]
        rc, saida, linha = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["criterio"]["rotas_novas"], 1, saida)
        self.assertEqual(linha["conferidas"], 1, saida)
        self.assertEqual(linha["rotas_mudadas"], 1, saida)
        self.assertNotIn("/sumida/", json.dumps(linha), saida)

    def test_nenhum_byte_mudou_sai_zero_e_declara_o_que_comparou(self):
        m = self.mundo()
        m.rota("/a/", "<html>a</html>", served=sha("a"))
        m.rota("/b/", "<html>b</html>", served=sha("b"))
        m.ledgers[self.SNAP] = [
            {"path": "/a/", "revised_on": "2026-09-01", "served_sha256": sha("a")},
            {"path": "/b/", "revised_on": "2026-09-01", "served_sha256": sha("b")},
        ]
        rc, saida, linha = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["conferidas"], 0, saida)
        # Zero conferidas aqui é veredito legítimo — mas só porque o critério
        # declara sobre QUANTAS rotas a comparação foi possível.
        self.assertEqual(linha["criterio"]["comparaveis"], 2, saida)
        self.assertEqual(linha["criterio"]["sem_served_sha256"], 0, saida)
        self.assertEqual(m.pedidos, [], "não deve sondar a borda sem rota a conferir")

    def test_formula_diferente_recusa_medir(self):
        m = self.mundo(formula_do_snapshot="0" * 64)
        m.rota("/a/", "<html>a</html>", served=sha("a-depois"))
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        rc, saida, linha = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 2, saida)
        self.assertIn("formula do served_sha256 mudou", saida)
        self.assertIsNone(linha)
        self.assertEqual(m.pedidos, [], "não sonda nada quando não pode comparar")

    def test_snapshot_sem_assinatura_da_formula_recusa_medir(self):
        m = self.mundo(formula_do_snapshot=None)
        m.rota("/a/", "<html>a</html>", served=sha("a-depois"))
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        rc, saida, _ = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 2, saida)
        self.assertIn("nao declara a formula", saida)

    def test_snapshot_vazio_recusa_medir(self):
        m = self.mundo()
        m.rota("/a/", "<html>a</html>", served=sha("a"))
        m.ledgers[self.SNAP] = []
        rc, saida, _ = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 2, saida)
        self.assertIn("snapshot vazio", saida)

    def test_ledger_sem_served_sha256_e_piso_de_comparabilidade(self):
        """Nenhuma entrada comparável ⇒ zero mudadas ⇒ verde falso, se não houver piso."""
        m = self.mundo()
        m.rota("/a/", "<html>a</html>")   # sem served_sha256
        m.rota("/b/", "<html>b</html>")   # idem
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        rc, saida, _ = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 2, saida)
        self.assertIn("nenhuma entrada do ledger de revisão tem served_sha256", saida)

    def test_entrada_sem_served_e_contada_nao_engolida(self):
        m = self.mundo()
        m.rota("/a/", "<html>a</html>", served=sha("a-depois"))
        m.rota("/sem/", "<html>sem</html>")   # sem served: não sei ler
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        rc, saida, linha = roda(m, "--desde-ledger", self.SNAP)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(linha["criterio"]["sem_served_sha256"], 1, saida)
        self.assertEqual(linha["criterio"]["comparaveis"], 1, saida)

    # ------------------------------------------------------------ mutação

    def test_mutante_que_compara_content_em_vez_de_served_morre(self):
        """Trocar o campo comparado faz o caso do --ressemear desaparecer.

        No mundo do teste-âncora o `content_sha256` é IGUAL nos dois lados (o
        texto não mudou) e só o `served_sha256` difere. Um detector que olhasse
        o content devolveria zero rotas e sairia verde sem conferir nada — que é
        exatamente a cegueira que este modo existe para fechar.
        """
        fonte = inspect.getsource(M.served_por_caminho)
        self.assertIn('entrada.get("served_sha256")', fonte,
                      "a mutação abaixo precisa deste literal para significar alguma coisa")
        mutado = fonte.replace('entrada.get("served_sha256")', 'entrada.get("content_sha256")')
        escopo = {"__builtins__": __builtins__}
        exec(compile(mutado, "<mutante>", "exec"), escopo)

        m = self.mundo()
        m.rota("/a/", "<html>a</html>", carimbo="2026-09-01", served=sha("a-depois"))
        m.ledgers[self.SNAP] = [
            {"path": "/a/", "revised_on": "2026-09-01",
             "content_sha256": sha("<html>a</html>"), "served_sha256": sha("a-antes")},
        ]
        original = M.served_por_caminho
        try:
            M.served_por_caminho = escopo["served_por_caminho"]
            rc_mutante, saida_mutante, linha_mutante = roda(m, "--desde-ledger", self.SNAP)
        finally:
            M.served_por_caminho = original
        rc_real, saida_real, linha_real = roda(m, "--desde-ledger", self.SNAP)

        self.assertEqual(rc_real, 0, saida_real)
        self.assertEqual(linha_real["conferidas"], 1, saida_real)
        # O mutante não vê diferença nenhuma e confere ZERO rotas.
        self.assertEqual(linha_mutante["conferidas"], 0, saida_mutante)

    def test_mutante_que_trata_ausencia_como_igual_morre(self):
        """Contar `served_sha256` ausente como "não mudou" é aceitar o que não se mediu."""
        fonte = inspect.getsource(M.served_por_caminho)
        self.assertIn("sem_campo += 1", fonte,
                      "a mutação abaixo precisa desta contagem para significar alguma coisa")
        mutado = fonte.replace("sem_campo += 1", "pass")
        escopo = {"__builtins__": __builtins__}
        exec(compile(mutado, "<mutante>", "exec"), escopo)

        m = self.mundo()
        m.rota("/a/", "<html>a</html>", served=sha("a-depois"))
        m.rota("/sem/", "<html>sem</html>")
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        original = M.served_por_caminho
        try:
            M.served_por_caminho = escopo["served_por_caminho"]
            _, saida_mutante, linha_mutante = roda(m, "--desde-ledger", self.SNAP)
        finally:
            M.served_por_caminho = original
        _, saida_real, linha_real = roda(m, "--desde-ledger", self.SNAP)

        self.assertEqual(linha_real["criterio"]["sem_served_sha256"], 1, saida_real)
        self.assertEqual(linha_mutante["criterio"]["sem_served_sha256"], 0, saida_mutante)

    def test_mutante_que_dispensa_a_assinatura_da_formula_morre(self):
        """Sem a conferência da fórmula, o gate compararia réguas diferentes."""
        fonte = inspect.getsource(M.formula_comparavel)
        self.assertIn("if declarada.strip() != atual.strip():", fonte,
                      "a mutação abaixo precisa desta comparação para significar alguma coisa")
        mutado = fonte.replace("if declarada.strip() != atual.strip():",
                               "if False:")
        escopo = {"__builtins__": __builtins__, "os": os, "ROOT": M.ROOT,
                  "FORMULA_ATUAL": M.FORMULA_ATUAL, "sufixo_de_formula": M.sufixo_de_formula}
        exec(compile(mutado, "<mutante>", "exec"), escopo)

        m = self.mundo(formula_do_snapshot="0" * 64)
        m.rota("/a/", "<html>a</html>", served=sha("a-depois"))
        m.ledgers[self.SNAP] = [{"path": "/a/", "served_sha256": sha("a-antes")}]
        original = M.formula_comparavel
        try:
            M.formula_comparavel = escopo["formula_comparavel"]
            rc_mutante, saida_mutante, _ = roda(m, "--desde-ledger", self.SNAP)
        finally:
            M.formula_comparavel = original
        rc_real, saida_real, _ = roda(m, "--desde-ledger", self.SNAP)

        self.assertEqual(rc_real, 2, saida_real)
        self.assertEqual(rc_mutante, 0, saida_mutante)


if __name__ == "__main__":
    unittest.main(verbosity=2)
