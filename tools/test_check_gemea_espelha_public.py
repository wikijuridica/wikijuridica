#!/usr/bin/env python3
"""Bancada de tools/check-gemea-espelha-public — a travessia entre os dois canais.

O DEFEITO COBERTO (P1b/B21, 2026-09-16): o HTML de public/ ja' trazia a data
corrigida e a GEMEA MARKDOWN continuava servindo a data falsa, porque o processo
Go carregava um `pages.json` anterior ao deploy. Dois canais, duas verdades, e
nenhum instrumento perguntava aos dois.

FIXTURE PROPRIA: uma arvore de tmpdir com manifesto, public/ e um servidor HTTP
de mentira que responde a gemea. Nada e' lido do disco vivo — a licao da sessao
e' que fixture emprestada deixa de exercitar o caso no dia em que o disco muda.

CONTROLE PAREADO em todos os casos: a mesma arvore, com os dois canais de
acordo, sai 0.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-gemea-espelha-public")

ROTAS = [f"/area{i}/pagina-{i}/" for i in range(8)]

HTML = """<!doctype html><html><head><title>{titulo_seo}</title>
<link rel="canonical" href="https://wikijuridica.com.br{rota}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article",
"datePublished":"{publicada}","dateModified":"{modificada}"}}</script>
</head><body><h1>{h1}</h1><p>corpo</p></body></html>"""

GEMEA = """---
title: "{h1}"
url: "https://wikijuridica.com.br{rota}"
date_published: "{publicada}"
date_modified: "{modificada}"
---

# {h1}
"""


class Portal:
    """Serve a gemea de cada rota a partir de um dicionario — o 'processo Go'."""

    def __init__(self, paginas):
        self.paginas = paginas
        rotas = self.paginas

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                caminho = self.path
                if not caminho.endswith("index.md"):
                    self.send_error(404)
                    return
                rota = caminho[: -len("index.md")]
                pagina = rotas.get(rota)
                if pagina is None:
                    self.send_error(404)
                    return
                corpo = GEMEA.format(**pagina).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def log_message(self, *a):  # silencio
                pass

        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.porta = self.servidor.server_address[1]
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base(self):
        return f"http://127.0.0.1:{self.porta}"

    def fim(self):
        self.servidor.shutdown()
        self.servidor.server_close()


class TestGemeaEspelhaPublic(unittest.TestCase):
    def monta(self, titulo_seo_igual_h1=True):
        raiz = tempfile.mkdtemp(prefix="gemea-espelha-")
        self.addCleanup(shutil.rmtree, raiz, True)
        paginas = {}
        os.makedirs(os.path.join(raiz, "data/editorial"), exist_ok=True)
        with open(os.path.join(raiz, "data/editorial/published_manifest.jsonl"), "w", encoding="utf-8") as mf:
            for i, rota in enumerate(ROTAS):
                dados = {"rota": rota, "h1": f"Titulo do documento {i}",
                         "titulo_seo": f"Titulo do documento {i}" if titulo_seo_igual_h1
                         else f"Busca: como resolver {i} | Wiki",
                         "publicada": "2026-09-01", "modificada": "2026-09-10"}
                paginas[rota] = dados
                destino = os.path.join(raiz, "public", rota.strip("/"))
                os.makedirs(destino, exist_ok=True)
                with open(os.path.join(destino, "index.html"), "w", encoding="utf-8") as hf:
                    hf.write(HTML.format(**dados))
                mf.write(json.dumps({"path": rota, "unique_intent_id": f"i-{i}"}) + "\n")
        return raiz, paginas

    def roda(self, raiz, base, amostra=4):
        proc = subprocess.run(
            [sys.executable, GATE, "--raiz", raiz, "--base", base, "--amostra", str(amostra)],
            capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    # ------------------------------------------------------------- o par central
    def test_gemea_com_data_velha_reprova_e_o_controle_sai_zero(self):
        """O caso real: public/ corrigido, processo servindo pages.json anterior."""
        raiz, paginas = self.monta()
        portal = Portal(paginas)
        self.addCleanup(portal.fim)

        rc, saida = self.roda(raiz, portal.base)
        self.assertEqual(rc, 0, f"CONTROLE: canais iguais tinham de sair 0; saida:\n{saida}")

        paginas[ROTAS[0]]["modificada"] = "2026-09-05"  # o processo ficou para tras
        rc2, saida2 = self.roda(raiz, portal.base)
        self.assertEqual(rc2, 1, f"gemea com data velha tinha de reprovar; saida:\n{saida2}")
        self.assertIn("date_modified", saida2)
        self.assertIn(ROTAS[0], saida2)

    def test_data_pura_contra_timestamp_do_mesmo_dia_reprova(self):
        """Mesmo DIA, bytes diferentes: quem cita recebe documentos distintos.

        No acervo as duas formas convivem (85 rotas com timestamp em
        content_revised_at, medido em 2026-09-16), e comparar por dia deixaria
        passar exatamente a divergencia de forma entre os canais.
        """
        raiz, paginas = self.monta()
        portal = Portal(paginas)
        self.addCleanup(portal.fim)
        paginas[ROTAS[0]]["modificada"] = "2026-09-10T17:22:26Z"
        rc, saida = self.roda(raiz, portal.base)
        self.assertEqual(rc, 1, f"forma diferente no mesmo dia tinha de reprovar; saida:\n{saida}")
        self.assertIn("2026-09-10T17:22:26Z", saida)

    def test_titulo_de_busca_diferente_do_h1_NAO_e_divergencia(self):
        """O falso positivo que a primeira versao do gate produziu: 36 em 40.

        `<title>` e' titulo de BUSCA e `<h1>` e' titulo do DOCUMENTO; eles
        divergem por desenho, e a gemea carrega o do documento. Um detector que
        confunde os dois acusa 90% do acervo e nao mede o portal.
        """
        raiz, paginas = self.monta(titulo_seo_igual_h1=False)
        portal = Portal(paginas)
        self.addCleanup(portal.fim)
        rc, saida = self.roda(raiz, portal.base)
        self.assertEqual(rc, 0, f"<title> != <h1> e' desenho, nao defeito; saida:\n{saida}")

    def test_h1_divergente_reprova(self):
        """CONTROLE do caso acima: o que o gate TEM de pegar e' o H1 discordando."""
        raiz, paginas = self.monta(titulo_seo_igual_h1=False)
        portal = Portal(paginas)
        self.addCleanup(portal.fim)
        paginas[ROTAS[0]]["h1"] = "Outro documento inteiramente"
        rc, saida = self.roda(raiz, portal.base)
        self.assertEqual(rc, 1, f"H1 divergente tinha de reprovar; saida:\n{saida}")
        self.assertIn("title/h1", saida)

    # --------------------------------------------------- sem sinal nao e' aprovacao
    def test_servidor_fora_do_ar_sai_dois_e_nao_zero(self):
        raiz, paginas = self.monta()
        portal = Portal(paginas)
        base = portal.base
        portal.fim()  # derruba antes de medir
        rc, saida = self.roda(raiz, base)
        self.assertEqual(rc, 2, f"sem gemea o veredito e' sobre o INSTRUMENTO; saida:\n{saida}")
        self.assertIn("INSTRUMENTO", saida)
        # O DIAGNOSTICO TAMBEM E' O PRODUTO. So' o exit code nao basta: o piso de
        # volume (`comparadas < amostra//2`) tambem devolve 2 quando o servidor
        # cai, e por isso o mutante que apagava ESTE ramo sobreviveu na primeira
        # rodada de mutacao. Quem le o alerta as 04:40 precisa da causa —
        # "nenhuma gemea respondeu em <base>" aponta o processo; "so' 0 de 8
        # rotas comparadas" manda procurar em public/.
        self.assertIn("nenhuma gemea respondeu", saida)
        self.assertIn(base, saida)

    def test_manifesto_menor_que_a_amostra_sai_dois(self):
        raiz, paginas = self.monta()
        portal = Portal(paginas)
        self.addCleanup(portal.fim)
        rc, saida = self.roda(raiz, portal.base, amostra=99)
        self.assertEqual(rc, 2, f"amostra maior que o manifesto e' piso quebrado; saida:\n{saida}")
        self.assertIn("INSTRUMENTO", saida)

    def test_html_ausente_em_public_nao_vira_verde_silencioso(self):
        """Piso de volume: metade da amostra tem de ser comparada de fato."""
        raiz, paginas = self.monta()
        portal = Portal(paginas)
        self.addCleanup(portal.fim)
        for rota in ROTAS[:6]:
            os.remove(os.path.join(raiz, "public", rota.strip("/"), "index.html"))
        rc, saida = self.roda(raiz, portal.base)
        self.assertEqual(rc, 2, f"public/ esvaziado nao pode sair verde; saida:\n{saida}")
        self.assertIn("INSTRUMENTO", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
