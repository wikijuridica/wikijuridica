#!/usr/bin/env python3
"""Prova que a série de humano da rede social conta pessoa e só pessoa.

O produtor é `tools/generate-social-humano-real`, e ele existe porque a CSP de
`/redesocial/` é `script-src 'none'` nas duas variantes: sem GA4 e sem Clarity,
a única superfície onde a rede social pode ser medida é o log de origem.

Os riscos que este teste cobre, um a um:

  1. CONTAR BOT COMO PESSOA — o pecado que o contrato chama de inflar métrica.
     A fixture traz uma linha de cada exclusão (aquecimento, simulação de bot,
     bot catalogado, `bot_allow=1`, IP não roteável, cliente que não finge ser
     navegador, `AionBot` escondido dentro de um User-Agent `Mozilla/…`, HEAD,
     folha de estilo, User-Agent vazio) e o piso tem de ignorar todas.

  2. INVERSÃO DO ADAPTADOR DE BOOLEANO — `botagents.motivo_de_desconto` recebe
     o valor COMO O LOG O ESCREVE, e no ledger JSONL `warming`/`bot_simulation`
     já são booleanos. `str(False)` == "False" cai fora do conjunto
     ("", "-", "0") e DESCARTARIA TODAS as linhas: a série ficaria zerada para
     sempre, sem erro nenhum. Este é o teste que separa "sem visita" de
     "agregador quebrado".

  3. JANELA DE SESSÃO NOS DOIS SENTIDOS — 20 min continua a mesma sessão, 40
     min abre outra.

  4. IPv6 ROTATIVO — o sufixo de interface muda dentro da visita (medido no
     ledger real de 2026-09-05); agrupar por IP exato transformaria um
     visitante em dois e o número deixaria de ser piso.

  5. IDEMPOTÊNCIA — duas execuções sobre a mesma fonte têm de produzir o mesmo
     sha256, e o dia que ninguém pediu para recalcular tem de voltar ao arquivo
     byte a byte.

  6. FALSO POSITIVO SOBRE AMOSTRA REAL — detector novo nasce com esse teste
     (CLAUDE.md §5). O ledger de origem do dia, quando existe, é varrido e
     nenhum dos clientes automatizados que de fato aparecem nele pode ser
     classificado como humano.
"""
import datetime
import hashlib

# NOTA SOBRE O IPv6 DAS FIXTURES: 2001:db8::/32 (RFC 3849) seria o certo
# para documentacao, e NAO serve aqui -- `botagents.ip_nao_publico` a
# desconta, corretamente, e a fixture de visitante humano precisa de um
# endereco que a ferramenta aceite como publico. Usa-se um /64 arbitrario
# da faixa publica, que nao e o de nenhum visitante medido: o dado pessoal
# era o bloco ESPECIFICO da pessoa observada, nao a faixa do provedor.
import json
import os
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = SourceFileLoader("gerador_social_humano",
                     os.path.join(RAIZ, "tools/generate-social-humano-real")).load_module()

UA_ANDROID = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/152.0.0.0 Mobile Safari/537.36")
UA_WINDOWS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")
UA_AIONBOT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36 (compatible; AionBot/1.0)")
UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

DIA = "2026-09-05"


def linha(ts, path, ip, ua, **extra):
    """Uma linha de `origin_access_nginx_v1` com os padrões do produtor real."""
    registro = {
        "schema_version": "origin_access_nginx_v1",
        "origem": "nginx",
        "ts": "%sT%sZ" % (DIA, ts),
        "method": "GET",
        "path": path,
        "status": 200,
        "bytes": 2865,
        "duration_ms": 2,
        "route_class": "page",
        "user_agent": ua,
        "agent_key": None,
        "bot_allow": "0",
        "host": "wikijuridica.com.br",
        "remote_addr": ip,
        "cf_ray": "a36248261cebc757-GIG",
        "referer": None,
        "accept_encoding": "gzip, br",
        "origin_cache_status": "HIT",
        "conditional_inm": None,
        "conditional_ims": None,
        "warming": False,
        "bot_simulation": False,
    }
    registro.update(extra)
    return registro


# ── As quatro requisições HUMANAS ────────────────────────────────────────────
# Visitante A: mesmo /64, sufixo de interface trocado no meio da visita.
HUMANAS = [
    linha("10:00:00", "/redesocial/", "2804:7f4:fedc:ba98:1:1:1:1", UA_ANDROID),
    linha("10:20:00", "/redesocial/index.md", "2804:7f4:fedc:ba98:2:2:2:2", UA_ANDROID,
          referer="https://wikijuridica.com.br/redesocial/"),
    # Visitante B: duas visitas separadas por 40 min -> duas sessões.
    linha("12:00:00", "/redesocial/perguntas/", "189.100.10.5", UA_WINDOWS,
          referer="https://www.google.com/search?q=aviso+previo"),
    linha("12:40:00", "/redesocial/duvida/civil-usucapiao-2026-09-05-3/", "189.100.10.5", UA_WINDOWS),
]

# ── Uma linha por motivo de exclusão ─────────────────────────────────────────
EXCLUIDAS = [
    ("aquecimento_marcado",
     linha("09:00:00", "/redesocial/", "127.0.0.1", "wikijuridica-origin-warm/1.0", warming=True)),
    ("sonda_bot_sim",
     linha("09:01:00", "/redesocial/", "191.5.5.5", UA_GOOGLEBOT, bot_simulation=True)),
    ("bot_catalogado",
     linha("09:02:00", "/redesocial/", "66.249.66.1", UA_GOOGLEBOT,
           agent_key="googlebot", bot_allow="1")),
    ("bot_valioso_marcado_no_nginx",
     linha("09:03:00", "/redesocial/", "40.77.167.1", UA_WINDOWS, bot_allow="1")),
    ("origem_nao_publica",
     linha("09:04:00", "/redesocial/", "10.0.0.5", UA_WINDOWS)),
    ("ua_nao_navegador",
     linha("09:05:00", "/redesocial/perguntas/", "45.9.9.9", "undici")),
    ("ua_declara_automacao",
     linha("09:06:00", "/redesocial/", "51.8.8.8", UA_AIONBOT)),
    ("metodo_nao_humano",
     linha("09:07:00", "/redesocial/", "191.6.6.6", UA_WINDOWS, method="HEAD")),
    ("rota_nao_editorial",
     linha("09:08:00", "/redesocial/assets/css/wj-social-2499dfd2f80ff32d.css", "189.100.10.5",
           UA_WINDOWS)),
    ("ua_ausente",
     linha("09:09:00", "/redesocial/", "191.7.7.7", "")),
]

# Fora do escopo: acervo. Não entra nem no bruto.
FORA_DO_ESCOPO = [
    linha("09:10:00", "/familia/divorcio/", "189.100.10.5", UA_WINDOWS),
    linha("09:11:00", "/mcp", "136.124.35.61", "undici", method="POST"),
]

FONTE_FALSA = {"arquivo": "fixture", "sha256": "0" * 64, "linhas": 16}


def agrega_a_fixture():
    registros = list(HUMANAS) + [r for _, r in EXCLUIDAS] + FORA_DO_ESCOPO
    return G.agrega(DIA, registros, FONTE_FALSA)


class ContagemDoPiso(unittest.TestCase):
    def setUp(self):
        self.linha = agrega_a_fixture()

    def test_so_as_humanas_contam(self):
        self.assertEqual(self.linha["requisicoes_humanas_piso"], len(HUMANAS))
        self.assertEqual(self.linha["denominador"]["liquido"], len(HUMANAS))

    def test_bruto_ignora_o_que_esta_fora_do_escopo(self):
        self.assertEqual(self.linha["denominador"]["bruto"], len(HUMANAS) + len(EXCLUIDAS))
        self.assertEqual(self.linha["denominador"]["descontadas"], len(EXCLUIDAS))

    def test_cada_exclusao_aparece_com_o_proprio_motivo(self):
        esperado = {}
        for motivo, _ in EXCLUIDAS:
            esperado[motivo] = esperado.get(motivo, 0) + 1
        self.assertEqual(self.linha["descontadas_por_motivo"], esperado)

    def test_adaptador_de_booleano_nao_descarta_tudo(self):
        # Se `warming`/`bot_simulation` booleanos forem repassados crus a
        # botagents.motivo_de_desconto, TODA linha vira "sonda_bot_sim" e a
        # série fica zerada em silêncio.
        self.assertIsNone(G.motivo_de_exclusao(HUMANAS[0]))
        self.assertEqual(G.motivo_de_exclusao(dict(HUMANAS[0], warming=True)),
                         "aquecimento_marcado")
        self.assertEqual(G.motivo_de_exclusao(dict(HUMANAS[0], bot_simulation=True)),
                         "sonda_bot_sim")

    def test_bot_catalogado_fica_registrado_por_agente(self):
        self.assertEqual(self.linha["bots_por_agente"], {"googlebot": 1})


class Sessao(unittest.TestCase):
    def setUp(self):
        self.linha = agrega_a_fixture()

    def test_tres_sessoes_e_dois_visitantes(self):
        # A: 10:00 + 10:20 (20 min) = 1 sessão. B: 12:00 e 12:40 (40 min) = 2.
        self.assertEqual(self.linha["sessoes_piso"], 3)
        self.assertEqual(self.linha["visitantes_distintos_piso"], 2)

    def test_ipv6_rotativo_no_mesmo_64_e_um_visitante_so(self):
        a = G.chave_de_visitante("2804:7f4:fedc:ba98:1:1:1:1", UA_ANDROID)
        b = G.chave_de_visitante("2804:7f4:fedc:ba98:2:2:2:2", UA_ANDROID)
        outro = G.chave_de_visitante("2804:7f4:c05c:2e01:1:1:1:1", UA_ANDROID)
        self.assertEqual(a, b)
        self.assertNotEqual(a, outro)

    def test_ipv4_nao_e_agrupado_por_faixa(self):
        self.assertNotEqual(G.chave_de_visitante("189.100.10.5", UA_WINDOWS),
                            G.chave_de_visitante("189.100.10.6", UA_WINDOWS))

    def test_janela_nos_dois_sentidos(self):
        base = datetime.datetime(2026, 9, 5, 10, 0, tzinfo=datetime.timezone.utc)
        def evento(minutos):
            return {"quando": base + datetime.timedelta(minutes=minutos)}
        self.assertEqual(len(G.sessoes_de([evento(0), evento(30)])), 1)   # 1800 s exatos
        self.assertEqual(len(G.sessoes_de([evento(0), evento(31)])), 2)   # 1860 s
        # Cadeia de saltos de 25 min é UMA sessão: a janela é entre consecutivas.
        self.assertEqual(len(G.sessoes_de([evento(0), evento(25), evento(50)])), 1)

    def test_nenhum_identificador_de_visitante_e_publicado(self):
        texto = json.dumps(self.linha, ensure_ascii=False)
        for proibido in ("189.100.10.5", "2804:7f4:c05c", "10.0.0.5", "66.249.66.1"):
            self.assertNotIn(proibido, texto, "IP vazou para o registro: %s" % proibido)


class OrigemERota(unittest.TestCase):
    def setUp(self):
        self.linha = agrega_a_fixture()

    def test_origem_e_atributo_da_sessao(self):
        # A segunda requisição de A tem referer interno, mas a SESSÃO dela
        # entrou direto: atribuir por requisição criaria uma sessão "interno"
        # que não existe.
        self.assertEqual(self.linha["por_origem_sessao"], {"busca": 1, "direto": 2})
        self.assertEqual(self.linha["por_origem_requisicao"],
                         {"busca": 1, "direto": 2, "interno": 1})

    def test_referer_entra_so_como_host(self):
        self.assertEqual(self.linha["hosts_de_referencia"],
                         {"www.google.com": 1, "wikijuridica.com.br": 1})
        self.assertNotIn("aviso+previo", json.dumps(self.linha, ensure_ascii=False))

    def test_classes_de_origem(self):
        self.assertEqual(G.origem_de(None), ("direto", None))
        self.assertEqual(G.origem_de("https://wikijuridica.com.br/redesocial/")[0], "interno")
        self.assertEqual(G.origem_de("https://www.google.com/search?q=x")[0], "busca")
        self.assertEqual(G.origem_de("https://gemini.google.com/app")[0], "ia")
        self.assertEqual(G.origem_de("https://chatgpt.com/")[0], "ia")
        self.assertEqual(G.origem_de("https://www.linkedin.com/feed/")[0], "social")
        self.assertEqual(G.origem_de("https://exemplo.com.br/artigo")[0], "referencia_externa")

    def test_rota_normalizada_limita_cardinalidade(self):
        self.assertEqual(G.rota_normalizada("/redesocial/"), "/redesocial/")
        self.assertEqual(G.rota_normalizada("/redesocial/index.md"), "/redesocial/index.md")
        self.assertEqual(
            G.rota_normalizada("/redesocial/duvida/civil-usucapiao-2026-09-05-3/"),
            "/redesocial/duvida/{slug}/")
        self.assertEqual(
            G.rota_normalizada("/redesocial/duvida/civil-usucapiao-2026-09-05-3/pagina/2/"),
            "/redesocial/duvida/{slug}/pagina/{n}/")
        self.assertEqual(
            G.rota_normalizada("/redesocial/duvida/x/index.md"),
            "/redesocial/duvida/{slug}/index.md")
        self.assertEqual(
            G.rota_normalizada("/redesocial/tema/trabalhista/aviso-previo/feed.xml"),
            "/redesocial/tema/{area}/{slug}/feed.xml")
        self.assertEqual(G.rota_normalizada("/redesocial/conta/entrar/"),
                         "/redesocial/conta/{tela}/")
        self.assertEqual(G.rota_normalizada("/api/v1/redesocial/publicar"),
                         "/api/v1/redesocial/publicar")

    def test_por_rota_conta_o_template_e_top_paginas_o_caminho(self):
        self.assertEqual(self.linha["por_rota"], {
            "/redesocial/": 1,
            "/redesocial/duvida/{slug}/": 1,
            "/redesocial/index.md": 1,
            "/redesocial/perguntas/": 1,
        })
        caminhos = [item["chave"] for item in self.linha["top_paginas"]]
        self.assertIn("/redesocial/duvida/civil-usucapiao-2026-09-05-3/", caminhos)


class ContratoDoRegistro(unittest.TestCase):
    def setUp(self):
        self.linha = agrega_a_fixture()

    def test_declara_piso_e_ausencia_de_teto(self):
        self.assertIs(self.linha["piso"], True)
        self.assertIsNone(self.linha["teto"])
        self.assertIn("s-maxage", self.linha["teto_motivo"])
        self.assertEqual(self.linha["fuso"], "UTC")
        self.assertEqual(self.linha["criterio"], G.CRITERIO)

    def test_definicoes_viajam_na_linha(self):
        self.assertEqual(self.linha["sessao_definicao"], "inatividade_1800s_ou_virada_do_dia_utc")
        self.assertIn("ipv6_64", self.linha["visitante_definicao"])
        self.assertIs(self.linha["identificador_publicado"], False)

    def test_cabecalho_publica_o_metodo_por_extenso(self):
        cabecalho = G.cabecalho()
        self.assertEqual(cabecalho["registro"], "cabecalho")
        for chave in ("por_que_origem", "dia", "visitante", "sessao", "humano",
                      "origem_da_sessao", "privacidade", "residuo", "idempotencia", "nao_usa"):
            self.assertTrue(cabecalho["metodo"][chave].strip(), "método sem %s" % chave)
        # O resíduo é o viés PARA CIMA, e omiti-lo seria apresentar piso como
        # certeza.
        self.assertIn("infla", cabecalho["metodo"]["residuo"])
        self.assertIn("uniques_filter", cabecalho["metodo"]["nao_usa"])

    def test_sem_carimbo_de_relogio(self):
        texto = json.dumps(self.linha, sort_keys=True)
        for proibido in ("gerado_em", "executado_em", "timestamp_execucao"):
            self.assertNotIn(proibido, texto)


class Idempotencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="social-humano-")
        self.destino_original = G.DESTINO
        G.DESTINO = os.path.join(self.tmp, "social_humano_daily.jsonl")

    def tearDown(self):
        G.DESTINO = self.destino_original
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sha(self):
        with open(G.DESTINO, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def test_duas_execucoes_mesmo_sha256(self):
        alvo = agrega_a_fixture()
        G.escreve({DIA: alvo})
        primeiro = self.sha()
        G.escreve({DIA: alvo})
        self.assertEqual(self.sha(), primeiro, "a segunda execução mudou o arquivo")
        with open(G.DESTINO, encoding="utf-8") as handle:
            linhas = [json.loads(l) for l in handle if l.strip()]
        self.assertEqual(len(linhas), 2, "cabeçalho + um dia; a segunda passada duplicou linha")
        self.assertEqual(linhas[0]["registro"], "cabecalho")
        self.assertEqual(linhas[1]["dia"], DIA)

    def test_dia_nao_recalculado_volta_byte_a_byte(self):
        antigo = {"schema_version": G.SCHEMA, "registro": "dia", "dia": "2026-09-04",
                  "sessoes_piso": 7, "campo_de_versao_futura": "não mexer"}
        os.makedirs(os.path.dirname(G.DESTINO), exist_ok=True)
        texto_antigo = json.dumps(antigo, ensure_ascii=False, sort_keys=False)
        with open(G.DESTINO, "w", encoding="utf-8") as handle:
            handle.write(G.serializa(G.cabecalho()) + "\n")
            handle.write(texto_antigo + "\n")
        G.escreve({DIA: agrega_a_fixture()})
        with open(G.DESTINO, encoding="utf-8") as handle:
            linhas = [l.rstrip("\n") for l in handle if l.strip()]
        self.assertIn(texto_antigo, linhas, "a linha de 04/09 foi reescrita ou perdida")

    def test_linha_ilegivel_do_destino_nao_e_apagada(self):
        os.makedirs(os.path.dirname(G.DESTINO), exist_ok=True)
        with open(G.DESTINO, "w", encoding="utf-8") as handle:
            handle.write("{isto nao e json\n")
        G.escreve({DIA: agrega_a_fixture()})
        with open(G.DESTINO, encoding="utf-8") as handle:
            conteudo = handle.read()
        self.assertIn("{isto nao e json", conteudo)


class FalsoPositivoSobreAmostraReal(unittest.TestCase):
    """O detector contra o ledger REAL do dia — nunca só contra a fixture."""

    def registros_reais(self):
        caminho = os.path.join(RAIZ, "data/ops/access/nginx-%s.jsonl"
                               % datetime.datetime.now(datetime.timezone.utc).date().isoformat())
        if not os.path.exists(caminho):
            self.skipTest("sem ledger de origem para hoje")
        with open(caminho, encoding="utf-8") as handle:
            return [json.loads(l) for l in handle if l.strip()]

    def test_automacao_real_nunca_e_classificada_como_humana(self):
        # Estes User-Agents estão MEDIDOS no ledger de origem de 2026-09-05.
        automacoes = ["node", "undici", "python-httpx/0.28.1", "Go-http-client/2.0",
                      "Bun/1.1.45", "claude-code/2.1.260 (claude-desktop, agent-sdk/0.3.260)",
                      "meta-externalads/1.1 (+https://developers.facebook.com/docs/sharing/"
                      "webmasters/crawler)", UA_AIONBOT,
                      "rokmcp-collector/0.2 (+https://rokmcp.com/bot)",
                      "MCPWatch/0.1.0 (+mcpwatch@iyre.com) longitudinal MCP security research"]
        for ua in automacoes:
            registro = linha("11:00:00", "/redesocial/", "189.100.10.5", ua)
            self.assertIsNotNone(G.motivo_de_exclusao(registro),
                                 "classificado como humano: %s" % ua)

    def test_navegador_real_do_ledger_de_hoje_conta(self):
        registros = self.registros_reais()
        no_escopo = [r for r in registros if G.no_escopo(r.get("path"))]
        if not no_escopo:
            self.skipTest("nenhuma requisição a /redesocial/ no ledger de hoje")
        humanos = [r for r in no_escopo if G.motivo_de_exclusao(r) is None]
        for registro in humanos:
            ua = registro["user_agent"]
            self.assertTrue(ua.startswith("Mozilla/"), "humano sem UA de navegador: %s" % ua)
            self.assertIsNone(registro["agent_key"])
            self.assertFalse(registro["warming"])
            self.assertFalse(registro["bot_simulation"])

    def test_o_criterio_e_o_mesmo_que_um_jq_reproduz(self):
        """O piso tem de bater com o filtro simples da conferência independente.

        Se um dia divergirem, ou o detector ficou esperto demais para ser
        auditado, ou a conferência deixou de valer — e as duas coisas precisam
        aparecer aqui, não num relatório.
        """
        registros = self.registros_reais()
        no_escopo = [r for r in registros if G.no_escopo(r.get("path"))]
        if not no_escopo:
            self.skipTest("nenhuma requisição a /redesocial/ no ledger de hoje")
        meu = sum(1 for r in no_escopo if G.motivo_de_exclusao(r) is None)
        jq = sum(1 for r in no_escopo
                 if (r.get("user_agent") or "").startswith("Mozilla/")
                 and not G.MARCAS_DE_AUTOMACAO.search(r.get("user_agent") or "")
                 and not r.get("agent_key") and not r.get("warming")
                 and not r.get("bot_simulation")
                 and str(r.get("bot_allow") or "") != "1"
                 and (r.get("method") or "").upper() in ("GET", "POST")
                 and not any((r.get("path") or "").startswith(p)
                             for p in G.PREFIXOS_NAO_EDITORIAIS))
        self.assertEqual(meu, jq)


class NascimentoDaSuperficie(unittest.TestCase):
    """Dia anterior ao ingress não vira zero: zero ali seria linha reta falsa."""

    def test_a_trava_e_o_dia_do_ingress(self):
        # O ingress entrou no ar em 2026-09-05 00:11:11 -0300 (commit 27c394ca),
        # que em UTC é o mesmo dia.
        self.assertEqual(G.DIA_DE_NASCIMENTO_DA_SUPERFICIE, DIA)

    def test_dias_anteriores_ficam_fora_da_serie(self):
        anteriores = ["2026-09-02", "2026-09-03", "2026-09-04"]
        for dia in anteriores:
            self.assertLess(dia, G.DIA_DE_NASCIMENTO_DA_SUPERFICIE)
        # E o dia do ingress em diante entra.
        self.assertGreaterEqual(DIA, G.DIA_DE_NASCIMENTO_DA_SUPERFICIE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
