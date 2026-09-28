#!/usr/bin/env python3
"""Prova as três classes de lastro de `tools/check-internal-link-integrity` e a
identidade da sonda.

O DEFEITO QUE ORIGINOU ESTE TESTE (2026-09-05): o gate só aceitava como lastro
arquivo em `public/`, e o modo `--com-fallback` sondava `127.0.0.1:8089`. Para
`/redesocial/` — servida por `cmd/social` na 8091 — o :8089 responde 404, então
o socorro errava exatamente na rota dinâmica que ele existia para salvar. Com a
âncora de `/redesocial/` nas 10.141 páginas do acervo, o gate ficaria vermelho
com 10.141 ocorrências "SEM LASTRO", todas falsas.

Nenhum caso aqui depende de serviço vivo: cada um sobe um `http.server` em
porta efêmera e injeta a origem por `--origem`. O servidor GRAVA os cabeçalhos
recebidos, porque a proibição de forjar UA de bot real só é cobrada se alguém
conferir o que saiu no fio.
"""
import contextlib
import http.server
import io
import os
import socket
import tempfile
import threading
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = SourceFileLoader(
    "check_internal_link_integrity",
    os.path.join(RAIZ, "tools/check-internal-link-integrity"),
).load_module()


class _Manipulador(http.server.BaseHTTPRequestHandler):
    """Serve a tabela `rotas` da classe e registra tudo o que chega."""

    rotas = {}
    recebidas = None

    # Nome em maiúsculas fixado pela stdlib: o BaseHTTPRequestHandler despacha
    # por `do_<METODO>`. Não há nada a renomear.
    def do_HEAD(self):
        type(self).recebidas.append((self.path, dict(self.headers)))
        status = type(self).rotas.get(self.path, 404)
        self.send_response(status)
        if 300 <= status < 400:
            self.send_header("Location", "/destino-final/")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_GET = do_HEAD

    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def origem(rotas):
    """Sobe uma origem HTTP local com a tabela de rotas dada."""
    recebidas = []
    manipulador = type("ManipuladorDeCaso", (_Manipulador,),
                       {"rotas": rotas, "recebidas": recebidas})
    servidor = http.server.HTTPServer(("127.0.0.1", 0), manipulador)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d" % servidor.server_address[1], recebidas
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def acervo(paginas):
    """Cria um `public/` de mentira: {caminho de pasta: lista de hrefs}."""
    with tempfile.TemporaryDirectory(prefix="wj-link-integrity-") as base:
        for pasta, hrefs in paginas.items():
            destino = base if pasta == "/" else os.path.join(base, pasta.strip("/"))
            os.makedirs(destino, exist_ok=True)
            corpo = "".join('<a href="%s">x</a>' % h for h in hrefs)
            with open(os.path.join(destino, "index.html"), "w", encoding="utf-8") as handle:
                handle.write("<html><body>%s</body></html>" % corpo)
        yield base


def roda(argv):
    """Executa o gate e devolve (codigo, saida)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        codigo = GATE.main(argv)
    return codigo, buffer.getvalue()


def porta_fechada():
    """Porta que ninguém escuta: liga, lê o número e desliga."""
    with socket.socket() as tomada:
        tomada.bind(("127.0.0.1", 0))
        return tomada.getsockname()[1]


class DestinoComArquivo(unittest.TestCase):
    def test_passa_sem_sondar_nada(self):
        """Acervo íntegro não pode gastar uma requisição sequer — é o que
        permite o gate ser verde com a origem parada."""
        with acervo({"/": ["/familia/"], "/familia/": ["/"]}) as base, \
                origem({"/": 200}) as (url, recebidas):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 0, saida)
        self.assertIn("OK: todo link interno tem artefato em disco.", saida)
        self.assertIn("sonda                 : nao foi preciso", saida)
        self.assertEqual(recebidas, [])


class DestinoDinamico(unittest.TestCase):
    def test_rota_que_responde_200_e_lastro_provado(self):
        with acervo({"/": ["/redesocial/"]}) as base, \
                origem({"/": 200, "/redesocial/": 200}) as (url, recebidas):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 0, saida)
        self.assertIn("DINAMICOS PROVADOS POR SONDA", saida)
        self.assertIn("/redesocial/", saida)
        self.assertIn("OK com ressalva", saida)
        self.assertNotIn("SEM LASTRO", saida)
        self.assertIn("/redesocial/", [caminho for caminho, _ in recebidas])

    def test_sonda_sai_com_ua_proprio_e_header_de_aquecimento(self):
        with acervo({"/": ["/redesocial/"]}) as base, \
                origem({"/": 200, "/redesocial/": 200}) as (url, recebidas):
            roda(["--public", base, "--origem", url])
        self.assertTrue(recebidas)
        for caminho, cabecalhos in recebidas:
            self.assertEqual(cabecalhos.get("User-Agent"),
                             "wikijuridica-superficie-probe/1.0", caminho)
            self.assertEqual(cabecalhos.get("X-Warming-Request"), "true", caminho)

    def test_modo_estrito_reprova_a_rota_dinamica_sem_sondar(self):
        """A pergunta de 2026-08-07 continua respondível: o que quebra se o
        processo cair."""
        with acervo({"/": ["/redesocial/"]}) as base, \
                origem({"/": 200, "/redesocial/": 200}) as (url, recebidas):
            codigo, saida = roda(["--public", base, "--origem", url, "--estrito"])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("SEM LASTRO", saida)
        self.assertEqual(recebidas, [])


class DestinoQuebrado(unittest.TestCase):
    def test_404_continua_reprovando(self):
        with acervo({"/": ["/pagina-que-nao-existe/"]}) as base, \
                origem({"/": 200}) as (url, _):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("SEM LASTRO", saida)
        self.assertIn("/pagina-que-nao-existe/", saida)
        self.assertIn("[404]", saida)

    def test_redirecionamento_nao_conta_como_lastro(self):
        with acervo({"/": ["/rota-que-redireciona"]}) as base, \
                origem({"/": 200, "/rota-que-redireciona": 301}) as (url, _):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("[301]", saida)

    def test_um_404_reprova_mesmo_com_dinamico_valido_ao_lado(self):
        with acervo({"/": ["/redesocial/", "/sumida/"]}) as base, \
                origem({"/": 200, "/redesocial/": 200}) as (url, _):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("DINAMICOS PROVADOS POR SONDA", saida)
        self.assertIn("/sumida/", saida)


class OrigemQueNaoDaParaMedir(unittest.TestCase):
    def test_origem_inalcancavel_nao_reprova_e_nao_aprova(self):
        with acervo({"/": ["/redesocial/"]}) as base:
            codigo, saida = roda(["--public", base,
                                  "--origem", "http://127.0.0.1:%d" % porta_fechada()])
        self.assertEqual(codigo, 2, saida)
        self.assertIn("INALCANCAVEL", saida)
        self.assertIn("NAO PROVADOS", saida)
        self.assertIn("INDETERMINADO", saida)
        self.assertNotIn("SEM LASTRO", saida)
        self.assertNotIn("OK com ressalva", saida)

    def test_502_e_processo_parado_nao_link_morto(self):
        """502 em /redesocial/ significa cmd/social fora do ar. Reprovar aqui
        seria culpar o acervo pela saúde do serviço."""
        with acervo({"/": ["/redesocial/"]}) as base, \
                origem({"/": 200, "/redesocial/": 502}) as (url, _):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO PROVADOS", saida)
        self.assertIn("[502]", saida)
        self.assertNotIn("SEM LASTRO", saida)

    def test_429_nao_diz_nada_sobre_a_rota_existir(self):
        with acervo({"/": ["/redesocial/"]}) as base, \
                origem({"/": 200, "/redesocial/": 429}) as (url, _):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 2, saida)
        self.assertIn("[429]", saida)


class DestinoNaoASCII(unittest.TestCase):
    def test_href_acentuado_e_sondado_percent_encoded(self):
        """Sem o encoding, o `urllib` estoura UnicodeEncodeError DENTRO do
        `open` — exceção que não é OSError nem URLError e derrubaria o gate
        inteiro em vez de medir aquele destino."""
        with acervo({"/": ["/glossário/citação/"]}) as base, \
                origem({"/": 200, "/gloss%C3%A1rio/cita%C3%A7%C3%A3o/": 200}) as (url, recebidas):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 0, saida)
        self.assertIn("DINAMICOS PROVADOS POR SONDA", saida)
        self.assertIn("/gloss%C3%A1rio/cita%C3%A7%C3%A3o/",
                      [caminho for caminho, _ in recebidas])

    def test_href_ja_codificado_nao_e_codificado_de_novo(self):
        with acervo({"/": ["/gloss%C3%A1rio/"]}) as base, \
                origem({"/": 200, "/gloss%C3%A1rio/": 200}) as (url, recebidas):
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 0, saida)
        self.assertNotIn("/gloss%25C3%25A1rio/", [caminho for caminho, _ in recebidas])


class OrigemQueFalaLixo(unittest.TestCase):
    """`http.client.HTTPException` não herda de `OSError`: sem capturá-la, uma
    linha de status ilegível derrubaria o gate inteiro em vez de marcar aquele
    destino como não provado."""

    @staticmethod
    @contextlib.contextmanager
    def origem_torta():
        ouvinte = socket.socket()
        ouvinte.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ouvinte.bind(("127.0.0.1", 0))
        ouvinte.listen(8)

        def servir():
            while True:
                try:
                    conexao, _ = ouvinte.accept()
                except OSError:
                    return
                with conexao:
                    try:
                        linha = conexao.recv(4096).split(b"\r\n", 1)[0]
                        if linha.split(b" ")[1:2] == [b"/"]:
                            conexao.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
                        else:
                            conexao.sendall(b"isto nao e uma linha de status\r\n\r\n")
                    except OSError:
                        continue

        thread = threading.Thread(target=servir, daemon=True)
        thread.start()
        try:
            yield "http://127.0.0.1:%d" % ouvinte.getsockname()[1]
        finally:
            ouvinte.close()
            thread.join(timeout=5)

    def test_linha_de_status_ilegivel_vira_nao_provado(self):
        with acervo({"/": ["/redesocial/"]}) as base, self.origem_torta() as url:
            codigo, saida = roda(["--public", base, "--origem", url])
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO PROVADOS", saida)
        self.assertIn("[sem resposta]", saida)
        self.assertNotIn("SEM LASTRO", saida)
        # O controle em `/` respondeu HTTP válido: quem falhou foi a sonda do
        # destino. Sem esta linha o teste passaria também pelo caminho de
        # "origem inalcançável", que já é coberto por outro caso.
        self.assertNotIn("INALCANCAVEL", saida)


class ClassificacaoDeStatus(unittest.TestCase):
    def test_tabela_de_veredito(self):
        for status, esperado in [(200, "provado"), (204, "provado"),
                                 (301, "sem_lastro"), (404, "sem_lastro"),
                                 (410, "sem_lastro"), (429, "nao_provado"),
                                 (500, "nao_provado"), (502, "nao_provado"),
                                 (503, "nao_provado"), (None, "nao_provado")]:
            self.assertEqual(GATE.veredito_do_status(status), esperado, status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
