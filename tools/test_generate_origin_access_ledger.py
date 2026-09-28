#!/usr/bin/env python3
"""Prova que o ledger de origem lê TODAS as gerações do log do nginx e descarta
só o que é tráfego próprio.

Os dois casos que originaram o teste (2026-09-03):
  1. regex exigindo todos os campos -> 58.711 linhas anteriores a 12/08 viravam
     "não parseada" (dado real declarado ilegível);
  2. os mesmos campos tornados opcionais numa regex ancorada em `$` -> 1.739.514
     linhas ilegíveis (o motor casava os grupos vazios e sobrava texto).
Ambos passariam num teste que só exercitasse a linha de hoje.
"""
import contextlib
import datetime
import glob
import io
import hashlib
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

# NOTA SOBRE O IPv6 DAS FIXTURES: 2001:db8::/32 (RFC 3849) seria o certo
# para documentacao, e NAO serve aqui -- `botagents.ip_nao_publico` a
# desconta, corretamente, e a fixture de visitante humano precisa de um
# endereco que a ferramenta aceite como publico. Usa-se um /64 arbitrario
# da faixa publica, que nao e o de nenhum visitante medido: o dado pessoal
# era o bloco ESPECIFICO da pessoa observada, nao a faixa do provedor.

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = SourceFileLoader("gerador", os.path.join(RAIZ, "tools/generate-origin-access-ledger")).load_module()
V = SourceFileLoader("varredor", os.path.join(RAIZ, "tools/sweep-origin-access-raw")).load_module()

# Endereço IPv6 em qualquer forma escrita — dois ou mais grupos hexadecimais
# separados por `:`. Serve para provar AUSÊNCIA no arquivo versionado; para
# provar presença, o teste compara com o valor exato.
IPV6_QUALQUER = re.compile(r"\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{0,4}){2,7}\b")

# Geração 1 (antes de 12/08/2026): termina em reqlen=.
L1 = ('127.0.0.1 - [11/Aug/2026:21:55:40 -0300] host=wikijuridica.com.br '
      '"GET /previdenciario/maternidade-homem/ HTTP/1.1" 200 20543 '
      '"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" '
      'allow=1 bot_sim=- rt=0.000 cf_ray=a29b8457-GIG reqlen=212')
# Geração 2 (12/08): ganha ref= e warm=.
L2 = ('66.249.66.1 - [20/Aug/2026:10:00:00 -0300] host=wikijuridica.com.br '
      '"GET /familia/divorcio/ HTTP/1.1" 200 21000 "Googlebot/2.1" '
      'allow=1 bot_sim=- rt=0.010 cf_ray=abc-GIG reqlen=100 ref="-" warm=-')
# Geração 4 (03/09): com ae=, ocs=, inm= e ims= (valor com espaços, sem aspas).
L4 = ('74.7.229.207 - [03/Sep/2026:00:01:07 -0300] host=wikijuridica.com.br '
      '"GET /glossario/alimentos-avoengos/index.md HTTP/1.1" 200 2535 '
      '"Chrome/131.0.0.0; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot" '
      'allow=1 bot_sim=- rt=0.001 cf_ray=a351820efa1ac128-GIG reqlen=752 '
      'ref="https://wikijuridica.com.br/glossario/alimentos-avoengos/" warm=- '
      'ae="gzip, br" ocs=HIT inm=- ims=Wed, 02 Sep 2026 20:00:00 GMT')
# Tráfego próprio, que NÃO entra: aquecedor (warm=true) e sonda (bot_sim).
L_WARM = ('127.0.0.1 - [03/Sep/2026:09:04:01 -0300] host=wikijuridica.com.br '
          '"GET /seguros/x/index.md HTTP/1.1" 200 8256 "wikijuridica-origin-warm/1.0" '
          'allow=0 bot_sim=- rt=0.001 cf_ray=- reqlen=263 ref="-" warm=true ae="identity" ocs=MISS inm=- ims=-')
L_SIM = ('127.0.0.1 - [03/Sep/2026:09:04:02 -0300] host=wikijuridica.com.br '
         '"GET / HTTP/1.1" 200 100 "Mozilla/5.0 (compatible; Googlebot/2.1)" '
         'allow=1 bot_sim=true rt=0.001 cf_ray=- reqlen=200 ref="-" warm=- ae="identity" ocs=- inm=- ims=-')


def campos_de(linha):
    casou = G.CABECA.match(linha)
    if not casou:
        return None, None
    return casou, G.pares(casou.group("resto"))


class LeituraDeTodasAsGeracoes(unittest.TestCase):
    def test_todas_as_geracoes_parseiam(self):
        for nome, linha in (("g1", L1), ("g2", L2), ("g4", L4), ("warm", L_WARM), ("sim", L_SIM)):
            casou, _ = campos_de(linha)
            self.assertIsNotNone(casou, "%s não parseou" % nome)

    def test_geracao_antiga_sem_ref_warm(self):
        casou, campos = campos_de(L1)
        self.assertEqual(casou.group("status"), "200")
        self.assertEqual(campos.get("allow"), "1")
        self.assertIsNone(campos.get("warm"))
        self.assertIsNone(campos.get("ocs"))

    def test_ims_com_espacos_vai_ate_o_fim(self):
        _, campos = campos_de(L4)
        self.assertEqual(campos["ims"], "Wed, 02 Sep 2026 20:00:00 GMT")
        self.assertEqual(campos["ocs"], "HIT")
        self.assertEqual(campos["ae"], "gzip, br")
        self.assertEqual(campos["ref"], "https://wikijuridica.com.br/glossario/alimentos-avoengos/")

    def test_instante_converte_fuso(self):
        quando = G.instante("03/Sep/2026:00:01:07 -0300")
        self.assertIsNotNone(quando)
        self.assertEqual(quando.astimezone(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "2026-09-03T03:01:07Z")

    def test_classe_de_rota(self):
        self.assertEqual(G.classe_de_rota("/familia/divorcio/", 200), "page")
        self.assertEqual(G.classe_de_rota("/familia/divorcio/index.md", 200), "markdown")
        self.assertEqual(G.classe_de_rota("/mcp", 200), "mcp")
        self.assertEqual(G.classe_de_rota("/api/v1/lote?area=x", 200), "lote")
        self.assertEqual(G.classe_de_rota("/.well-known/agent-card.json", 200), "descritor")
        self.assertEqual(G.classe_de_rota("/robots.txt", 200), "robots")
        self.assertEqual(G.classe_de_rota("/sitemaps/pages-0001.xml", 200), "sitemap")
        self.assertEqual(G.classe_de_rota("/nao-existe/", 404), "not_found")

    def test_o_token_da_assinatura_de_agenda_nao_entra_no_ledger(self):
        """O ledger é VERSIONADO, e a assinatura iCalendar é aberta por um
        segredo que mora no caminho da URL. Sem a redação, o token de cada
        advogado ficaria commitado no git — e com ele a agenda de processos.

        A redação preserva o prefixo: a linha continua sendo classificada como
        era, e o que some é só o segredo."""
        segredo = "a1" * 32
        caminho = "/redesocial/conta/prazo/agenda/%s/agenda.ics" % segredo
        redigido = G.caminho_sem_segredo(caminho)
        self.assertNotIn(segredo, redigido)
        self.assertEqual(redigido, "/redesocial/conta/prazo/agenda/<assinatura>/agenda.ics")
        # Com parâmetro de rastreamento colado no fim, idem.
        self.assertNotIn(segredo, G.caminho_sem_segredo(caminho + "?utm_source=x"))
        # Caminho sem segredo nenhum passa intacto: a redação não pode reescrever
        # o acervo inteiro por acidente.
        for intacto in ("/familia/divorcio/", "/redesocial/conta/prazo/agenda/",
                        "/redesocial/conta/prazo/"):
            self.assertEqual(G.caminho_sem_segredo(intacto), intacto)
        # E a classificação da rota sobrevive à redação.
        self.assertEqual(G.superficie_de(redigido), G.superficie_de(caminho))

    def test_trafego_proprio_e_descartado_e_bot_real_entra(self):
        botagents = SourceFileLoader("botagents", os.path.join(RAIZ, "tools/botagents.py")).load_module()
        for linha, esperado in ((L_WARM, "aquecimento_marcado"), (L_SIM, "sonda_bot_sim")):
            casou, campos = campos_de(linha)
            motivo = botagents.motivo_de_desconto(bot_sim=campos.get("bot_sim"), warm=campos.get("warm"),
                                                  ip=casou.group("ip"), user_agent=casou.group("ua"))
            self.assertEqual(motivo, esperado)
        casou, campos = campos_de(L4)
        motivo = botagents.motivo_de_desconto(bot_sim=campos.get("bot_sim"), warm=campos.get("warm"),
                                              ip=casou.group("ip"), user_agent=casou.group("ua"))
        self.assertIsNone(motivo, "bot externo real não pode ser descartado")


# ─────────────────────────────────────────────────────────────────────────────
# ESQUEMA v2 (2026-09-05): superfície, pseudônimo do dia e a guarda do art. 15.
#
# O que estes testes protegem, em uma frase: o IP de quem usa a REDE SOCIAL não
# pode entrar no git (que guarda para sempre), e ao mesmo tempo não pode sumir
# do disco antes dos seis meses que o Marco Civil da Internet, art. 15, obriga
# a guardar. As duas coisas juntas — nem uma nem outra sozinha.
#
# NENHUM ENDEREÇO REAL DE VISITANTE ENTRA NESTE ARQUIVO. Os IPv6 abaixo são
# sintéticos e nunca estiveram em log nenhum; o endereço real do visitante de
# 2026-09-05 não é citado aqui de propósito, porque este arquivo também é
# versionado — seria repetir, no teste, o defeito que o v2 corrige. A cobertura
# sobre tráfego real vem de `LedgerVersionadoReal`, que lê o ledger do dia no
# disco em vez de copiar valores para cá.
IPV6_A = "2804:7f4:8a90:4c00:1a2b:3c4d:5e6f:1"      # sintético
IPV6_B = "2804:7f4:8a90:4c00:9f8e:7d6c:5b4a:2"      # mesmo /64 do anterior
IPV6_OUTRO_64 = "2804:7f4:8a90:4c01:1a2b:3c4d:5e6f:1"
IPV4_SINTETICO = "203.0.113.9"  # RFC 5737, faixa de documentação
# Para atravessar `transcreve` o endereço tem de ser PÚBLICO: `ip_nao_publico`
# descarta faixa de documentação e rede privada antes de virar registro. O IP do
# Googlebot serve — é público, é de máquina e já é o do fixture L2.
IP_GOOGLEBOT = "66.249.66.1"


def linha_de_log(ip, caminho, quando="04:28:15", dia="05/Sep/2026", ua=None):
    """Uma linha no formato `wj_main` da geração 4 (03/09/2026 em diante)."""
    return ('%s - [%s:%s -0300] host=wikijuridica.com.br "GET %s HTTP/1.1" 200 2865 "%s" '
            'allow=0 bot_sim=- rt=0.064 cf_ray=a363841d599ffeaa-GIG reqlen=1076 ref="-" '
            'warm=- ae="gzip, br" ocs=EXPIRED inm=- ims=-'
            % (ip, dia, quando, caminho,
               ua or "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"))


class SuperficieDaRota(unittest.TestCase):
    """`superficie` nasce AO LADO de `route_class`, sem tomar o lugar dela."""

    def test_rotas_da_rede_social(self):
        for caminho in ("/redesocial/", "/redesocial", "/redesocial/conta/cadastrar/",
                        "/redesocial/conta/entrar/", "/redesocial/consulta/?termo=pensao",
                        "/redesocial/duvida/como-pedir-guarda/", "/redesocial/index.md",
                        "/api/v1/redesocial/publicacoes"):
            self.assertEqual(G.superficie_de(caminho), "redesocial", caminho)

    def test_acervo_inclui_o_canal_de_maquina(self):
        for caminho in ("/familia/divorcio/", "/familia/divorcio/index.md", "/mcp",
                        "/a2a", "/api/v1/lote?area=familia", "/sitemaps/pages-0001.xml",
                        "/robots.txt", "/.well-known/agent-card.json"):
            self.assertEqual(G.superficie_de(caminho), "acervo", caminho)

    def test_operacao_e_interno(self):
        for caminho in ("/healthz", "/readyz", "/livez", "/nginx_status", "/metrics"):
            self.assertEqual(G.superficie_de(caminho), "interno", caminho)

    def test_route_class_continua_igual_ao_v1(self):
        # O eixo antigo não muda de significado: é o que mantém o consumidor v1
        # lendo o v2 sem alteração.
        self.assertEqual(G.classe_de_rota("/redesocial/", 200), "page")
        self.assertEqual(G.classe_de_rota("/redesocial/index.md", 200), "markdown")


class PseudonimoDoDia(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="chaves-pseudonimo-")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.chave_05 = G.chave_do_dia("2026-09-05", self.pasta)
        self.chave_06 = G.chave_do_dia("2026-09-06", self.pasta)

    def test_mesmo_visitante_no_mesmo_dia_da_o_mesmo_token(self):
        primeiro = G.pseudonimo(IPV6_A, "2026-09-05", self.chave_05)
        segundo = G.pseudonimo(IPV6_A, "2026-09-05", self.chave_05)
        self.assertEqual(primeiro, segundo)
        # E reproduz depois de reler a chave do disco — a série do dia tem de
        # sobreviver ao processo morrer no meio.
        relida = G.chave_do_dia("2026-09-05", self.pasta)
        self.assertEqual(primeiro, G.pseudonimo(IPV6_A, "2026-09-05", relida))

    def test_dia_seguinte_da_token_diferente(self):
        self.assertNotEqual(G.pseudonimo(IPV6_A, "2026-09-05", self.chave_05),
                            G.pseudonimo(IPV6_A, "2026-09-06", self.chave_06))

    def test_ipv6_rotativo_no_mesmo_64_e_o_mesmo_visitante(self):
        """Medido em 2026-09-05: o mesmo visitante trocou o sufixo da interface
        entre 03:52 e 07:28. Pseudonimizar o endereço inteiro transformaria um
        visitante em dois SEM VOLTA — o endereço não fica lá para reagrupar."""
        self.assertEqual(G.pseudonimo(IPV6_A, "2026-09-05", self.chave_05),
                         G.pseudonimo(IPV6_B, "2026-09-05", self.chave_05))
        self.assertNotEqual(G.pseudonimo(IPV6_A, "2026-09-05", self.chave_05),
                            G.pseudonimo(IPV6_OUTRO_64, "2026-09-05", self.chave_05))

    def test_ipv4_nao_e_agrupado_por_faixa(self):
        self.assertNotEqual(G.pseudonimo("198.51.100.5", "2026-09-05", self.chave_05),
                            G.pseudonimo("198.51.100.6", "2026-09-05", self.chave_05))

    def test_token_nao_e_endereco_e_tem_forma_fixa(self):
        token = G.pseudonimo(IPV4_SINTETICO, "2026-09-05", self.chave_05)
        self.assertTrue(token.startswith(G.PREFIXO_PSEUDONIMO))
        self.assertRegex(token, r"^pseudo-[0-9a-f]{32}$")
        with self.assertRaises(ValueError):
            ipaddress.ip_address(token)

    def test_chave_nasce_fora_do_git_com_permissao_600(self):
        caminho = os.path.join(self.pasta, "pseudonimo-2026-09-05.key")
        self.assertTrue(os.path.isfile(caminho))
        self.assertEqual(stat.S_IMODE(os.stat(caminho).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.pasta).st_mode), 0o700)
        with open(caminho, encoding="utf-8") as fh:
            material = fh.read().strip()
        self.assertRegex(material, r"^[0-9a-f]{64}$")
        # E não é reescrita na segunda chamada: o pseudônimo do dia não muda no
        # meio do dia.
        G.chave_do_dia("2026-09-05", self.pasta)
        with open(caminho, encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), material)

    def test_chave_truncada_falha_alto_em_vez_de_trocar_a_serie(self):
        caminho = os.path.join(self.pasta, "pseudonimo-2026-09-07.key")
        with open(caminho, "w", encoding="utf-8") as fh:
            fh.write("abc123\n")
        with self.assertRaises(ValueError):
            G.chave_do_dia("2026-09-07", self.pasta)

    def test_chave_do_dia_nunca_esta_no_repositorio(self):
        """A chave mora em `var/`, que o `.gitignore` cobre na linha 4."""
        checagem = subprocess.run(["git", "-C", RAIZ, "check-ignore", "-q",
                                   os.path.join(RAIZ, "var/ops/access-keys")])
        self.assertEqual(checagem.returncode, 0,
                         "var/ops/access-keys precisa estar ignorado pelo git")
        checagem = subprocess.run(["git", "-C", RAIZ, "check-ignore", "-q",
                                   os.path.join(RAIZ, "var/ops/access-raw")])
        self.assertEqual(checagem.returncode, 0,
                         "var/ops/access-raw precisa estar ignorado pelo git")


class TranscricaoComPseudonimo(unittest.TestCase):
    """O caminho inteiro: linha do log -> registro -> versão que vai para o git."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="ledger-v2-")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.log = os.path.join(self.pasta, "access.log")
        with open(self.log, "w", encoding="utf-8") as fh:
            fh.write(linha_de_log(IPV6_A, "/redesocial/") + "\n")
            fh.write(linha_de_log(IPV6_B, "/redesocial/index.md", quando="04:29:09") + "\n")
            fh.write(linha_de_log(IPV6_B, "/redesocial/conta/cadastrar/", quando="04:31:00") + "\n")
            fh.write(linha_de_log(IP_GOOGLEBOT, "/familia/divorcio/", quando="05:00:00",
                                  ua="Mozilla/5.0 (compatible; Googlebot/2.1; "
                                     "+http://www.google.com/bot.html)") + "\n")
        self.log_anterior = G.LOG
        G.LOG = self.log
        self.addCleanup(setattr, G, "LOG", self.log_anterior)
        self.chaves = os.path.join(self.pasta, "chaves")
        self.por_dia, _ = G.transcreve({"2026-09-05"})
        self.registros = sorted(self.por_dia["2026-09-05"], key=lambda r: r["ts"])
        self.chave = G.chave_do_dia("2026-09-05", self.chaves)
        self.publicos = [G.versao_publica(r, "2026-09-05", self.chave) for r in self.registros]

    def test_o_log_sintetico_produziu_as_quatro_linhas_do_dia(self):
        self.assertEqual(len(self.registros), 4)
        self.assertEqual([r["superficie"] for r in self.registros],
                         ["redesocial", "redesocial", "redesocial", "acervo"])

    def test_linha_social_sai_pseudonimizada(self):
        sociais = [r for r in self.publicos if r["superficie"] == "redesocial"]
        self.assertEqual(len(sociais), 3)
        for registro in sociais:
            self.assertEqual(registro["remote_addr_forma"], "pseudonimo_diario")
            self.assertRegex(registro["remote_addr"], r"^pseudo-[0-9a-f]{32}$")
            with self.assertRaises(ValueError):
                ipaddress.ip_address(registro["remote_addr"])
        # Mesmo /64 => mesmo visitante, dentro do dia.
        self.assertEqual(len({r["remote_addr"] for r in sociais}), 1)

    def test_nenhum_ip_em_claro_na_linha_social_serializada(self):
        for registro in self.publicos:
            if registro["superficie"] != "redesocial":
                continue
            linha = json.dumps(registro, ensure_ascii=False, sort_keys=True)
            self.assertNotIn(IPV6_A, linha)
            self.assertNotIn(IPV6_B, linha)
            self.assertIsNone(IPV6_QUALQUER.search(linha),
                              "IPv6 em claro na linha social: %s" % linha)

    def test_acervo_sai_exatamente_como_no_v1(self):
        acervo = [r for r in self.publicos if r["superficie"] == "acervo"]
        originais = [r for r in self.registros if r["superficie"] == "acervo"]
        self.assertEqual(len(acervo), 1)
        for publico, original in zip(acervo, originais):
            self.assertEqual(publico["remote_addr"], original["remote_addr"])
            self.assertEqual(publico["remote_addr_forma"], "ip")
            # Nenhum campo do v1 mudou de valor: o esquema é aditivo.
            for chave, valor in original.items():
                self.assertEqual(publico[chave], valor, chave)

    def test_o_bruto_guarda_o_ip_que_o_versionado_deixou_de_guardar(self):
        bruto_dir = os.path.join(self.pasta, "bruto")
        sociais = [r for r in self.registros if r["superficie"] == "redesocial"]
        caminho = G.grava_bruto("2026-09-05", sociais, bruto_dir)
        self.assertEqual(stat.S_IMODE(os.stat(caminho).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(bruto_dir).st_mode), 0o700)
        with open(caminho, encoding="utf-8") as fh:
            gravado = [json.loads(linha) for linha in fh]
        self.assertEqual([r["remote_addr"] for r in gravado], [IPV6_A, IPV6_B, IPV6_B])
        # Só o que saiu do versionado: acervo não é copiado duas vezes.
        self.assertTrue(all(r["superficie"] == "redesocial" for r in gravado))

    def test_duas_execucoes_dao_o_mesmo_sha256(self):
        def digesto():
            chave = G.chave_do_dia("2026-09-05", self.chaves)
            corpo = "".join(json.dumps(G.versao_publica(r, "2026-09-05", chave),
                                       ensure_ascii=False, sort_keys=True) + "\n"
                            for r in self.registros)
            return hashlib.sha256(corpo.encode("utf-8")).hexdigest()
        self.assertEqual(digesto(), digesto())

    def test_versao_publica_nao_altera_o_registro_recebido(self):
        antes = dict(self.registros[0])
        G.versao_publica(self.registros[0], "2026-09-05", self.chave)
        self.assertEqual(self.registros[0], antes)


class VeredictoDeIdentidadeSobreviveAoPseudonimo(unittest.TestCase):
    """O bot na rede social continua verificável DEPOIS da pseudonimização.

    O DEFEITO QUE ESTA CLASSE IMPEDE DE VOLTAR: a linha social vai para o git
    com `remote_addr` pseudonimizado por HMAC do dia — o que está certo e não se
    afrouxa. Mas a verificação de identidade de bot na origem é faixa de IP
    oficial, e faixa não casa com pseudônimo. Sem o veredito gravado ANTES do
    HMAC, no dia em que o primeiro Googlebot pedisse `/redesocial/` a requisição
    seria para sempre `unverifiable` — e o marco de rastreio da rede social
    ficaria estruturalmente inalcançável. Gate que nunca pode ficar verde é gate
    que ninguém lê.
    """

    def setUp(self):
        self.faixas = G._botagents.ler_faixas(RAIZ)

    def test_ip_dentro_da_faixa_oficial_e_autentico(self):
        self.assertEqual(
            G.veredito_de_identidade(IP_GOOGLEBOT, "googlebot", self.faixas),
            ("authentic", "ip_range"))

    def test_ip_fora_da_faixa_com_ua_de_bot_e_forjado(self):
        # O caso medido: requisições com `bot_allow=1` declarando ChatGPT-User
        # de endereços que não são da OpenAI. Chave vazia por User-Agent é chave
        # vazia para quem digitar o User-Agent.
        self.assertEqual(
            G.veredito_de_identidade("203.0.113.7", "googlebot", self.faixas),
            ("forged", "ip_range"))

    def test_sem_agente_declarado_nao_e_forjado(self):
        # Gente comum não é bot forjando identidade. Fundir os dois casos faria
        # a métrica acusar visitante humano de fraude.
        for vazio in (None, "", "   "):
            self.assertEqual(
                G.veredito_de_identidade(IP_GOOGLEBOT, vazio, self.faixas),
                ("unverifiable", "none"))

    def test_agente_sem_faixa_publicada_e_inverificavel_nunca_forjado(self):
        # semrushbot, cloudflare-ai-search e mcpbeat não publicam faixa. Acusar
        # forjamento sem ter como verificar é a métrica inventando acusação —
        # o inverso simétrico de inventar aprovação.
        self.assertEqual(
            G.veredito_de_identidade(IP_GOOGLEBOT, "semrushbot", self.faixas),
            ("unverifiable", "none"))

    def test_a_linha_social_carrega_o_veredito_E_o_pseudonimo(self):
        registro = {"superficie": "redesocial", "remote_addr": IP_GOOGLEBOT,
                    "agent_key": "googlebot", "path": "/redesocial/"}
        publico = G.versao_publica(registro, "2026-09-05", b"chave-de-teste-32-bytes---------",
                                   self.faixas)
        self.assertEqual(publico["ip_verificacao"], "authentic")
        self.assertEqual(publico["ip_verificacao_metodo"], "ip_range")
        self.assertEqual(publico["remote_addr_forma"], "pseudonimo_diario")
        # O endereço NÃO sobrevive: o veredito é uma palavra, não um IP.
        self.assertNotIn(IP_GOOGLEBOT, json.dumps(publico))
        self.assertTrue(publico["remote_addr"].startswith(G.PREFIXO_PSEUDONIMO))

    def test_mutacao_o_pseudonimo_sozinho_nao_autentica_ninguem(self):
        # CONTROLE POSITIVO da classe inteira: prova que o veredito é a ÚNICA
        # via. Sem ele, o consumidor a jusante recebe o pseudônimo e `em_faixa`
        # falha — que era exatamente o estado anterior.
        registro = {"superficie": "redesocial", "remote_addr": IP_GOOGLEBOT,
                    "agent_key": "googlebot", "path": "/redesocial/"}
        publico = G.versao_publica(registro, "2026-09-05", b"chave-de-teste-32-bytes---------",
                                   self.faixas)
        self.assertFalse(
            G._botagents.em_faixa(publico["remote_addr"], self.faixas["googlebot"]),
            "se o pseudônimo casasse a faixa, a pseudonimização não estaria protegendo nada")

    def test_linha_do_acervo_nao_ganha_veredito(self):
        # Fora da rede social o `remote_addr` fica em claro, e quem consome
        # verifica direto. Gravar o veredito ali seria campo redundante em
        # milhões de linhas.
        publico = G.versao_publica(
            {"superficie": "acervo", "remote_addr": IP_GOOGLEBOT, "agent_key": "googlebot"},
            "2026-09-05", None, self.faixas)
        self.assertNotIn("ip_verificacao", publico)
        self.assertEqual(publico["remote_addr_forma"], "ip")


class LedgerVersionadoReal(unittest.TestCase):
    """A prova sobre TRÁFEGO REAL: o ledger do disco, a partir da vigência do v2.

    Este é o teste que o dono confere com `grep`: nenhuma linha de
    `superficie=redesocial` gravada de 2026-09-05 em diante pode ter endereço em
    claro no `remote_addr`. O `grep` tem de ser NO CAMPO, não na linha inteira —
    o User-Agent do Chrome carrega `Chrome/152.0.0.0`, que casa com qualquer
    regex de IPv4 e não é endereço nenhum.
    """

    @classmethod
    def setUpClass(cls):
        cls.arquivos = []
        for caminho in sorted(glob.glob(os.path.join(RAIZ, "data/ops/access/nginx-*.jsonl"))):
            dia = os.path.basename(caminho)[len("nginx-"):-len(".jsonl")]
            if dia >= G.DATA_DE_VIGENCIA_V2:
                cls.arquivos.append((dia, caminho))

    def test_ha_arquivo_a_partir_da_vigencia(self):
        self.assertTrue(self.arquivos,
                        "nenhum ledger de %s em diante em data/ops/access/" % G.DATA_DE_VIGENCIA_V2)

    def test_nenhum_endereco_em_claro_na_superficie_social(self):
        social = 0
        for dia, caminho in self.arquivos:
            with open(caminho, encoding="utf-8") as fh:
                for numero, linha in enumerate(fh, 1):
                    registro = json.loads(linha)
                    # A superfície é RECALCULADA do caminho: um arquivo escrito
                    # antes do campo existir não escapa da verificação.
                    if G.superficie_de(registro.get("path")) != "redesocial":
                        continue
                    social += 1
                    endereco = registro.get("remote_addr") or ""
                    self.assertTrue(endereco.startswith(G.PREFIXO_PSEUDONIMO),
                                    "%s:%d remote_addr em claro: %s" % (caminho, numero, endereco))
                    with self.assertRaises(ValueError):
                        ipaddress.ip_address(endereco)
                    self.assertEqual(registro.get("remote_addr_forma"), "pseudonimo_diario")
        self.assertGreater(social, 0,
                           "nenhuma requisição a /redesocial/ no ledger real — o teste não provou nada")

    def test_acervo_do_mesmo_arquivo_continua_com_ip(self):
        """A contraprova: a pseudonimização é cirúrgica, não uma lavagem geral.
        Sem isto, um bug que apagasse todo `remote_addr` passaria verde."""
        com_endereco = 0
        for dia, caminho in self.arquivos:
            with open(caminho, encoding="utf-8") as fh:
                for linha in fh:
                    registro = json.loads(linha)
                    if G.superficie_de(registro.get("path")) == "redesocial":
                        continue
                    endereco = registro.get("remote_addr")
                    if not endereco:
                        continue
                    try:
                        ipaddress.ip_address(endereco)
                    except ValueError:
                        self.fail("%s: acervo com remote_addr que não é endereço: %s"
                                  % (caminho, endereco))
                    com_endereco += 1
        self.assertGreater(com_endereco, 0, "nenhuma linha de acervo com IP — arquivo vazio?")


class LedgerAntigoNaoEhTruncado(unittest.TestCase):
    """Pedir um dia que já saiu do logrotate NÃO apaga o ledger daquele dia.

    O log do nginx guarda ~14 dias; o ledger versionado, para sempre — são 31
    arquivos rastreados em 2026-09-05. Sem esta guarda, um
    `--dia 2026-01-10` devolveria zero linha e a reescrita atômica truncaria um
    arquivo commitado: apagar dado real achando que estava atualizando.
    """

    def test_dia_sem_linha_no_log_preserva_o_arquivo_existente(self):
        pasta = tempfile.mkdtemp(prefix="ledger-antigo-")
        self.addCleanup(shutil.rmtree, pasta, True)
        log = os.path.join(pasta, "access.log")
        with open(log, "w", encoding="utf-8") as fh:
            fh.write(linha_de_log(IP_GOOGLEBOT, "/familia/divorcio/") + "\n")
        destino = os.path.join(pasta, "access")
        os.makedirs(destino)
        antigo = os.path.join(destino, "nginx-2026-01-10.jsonl")
        conteudo = '{"path": "/familia/divorcio/", "remote_addr": "66.249.66.1"}\n'
        with open(antigo, "w", encoding="utf-8") as fh:
            fh.write(conteudo)

        log_anterior, destino_anterior, argv_anterior = G.LOG, G.DESTINO, sys.argv
        G.LOG, G.DESTINO = log, destino
        sys.argv = ["generate-origin-access-ledger", "--dia", "2026-01-10",
                    "--sem-varredura", "--json"]
        try:
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                codigo = G.main()
        finally:
            G.LOG, G.DESTINO, sys.argv = log_anterior, destino_anterior, argv_anterior

        self.assertEqual(codigo, 0)
        with open(antigo, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), conteudo, "ledger antigo foi sobrescrito")
        self.assertIn("2026-01-10", json.loads(saida.getvalue())["dias_preservados_sem_linha_no_log"])


class GuardaDoArtigo15(unittest.TestCase):
    """O varredor: apaga o bruto DEPOIS de seis meses, nunca antes."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="varredura-")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.bruto = os.path.join(self.pasta, "access-raw")
        self.chaves = os.path.join(self.pasta, "access-keys")
        os.makedirs(self.bruto)
        os.makedirs(self.chaves)

    def cria(self, dia):
        with open(os.path.join(self.bruto, "nginx-%s.jsonl" % dia), "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        with open(os.path.join(self.chaves, "pseudonimo-%s.key" % dia), "w", encoding="utf-8") as fh:
            fh.write("0" * 64 + "\n")

    def test_meses_de_calendario_e_nao_180_dias(self):
        self.assertEqual(V.subtrai_meses(datetime.date(2026, 9, 5), 6), datetime.date(2026, 3, 5))
        self.assertEqual(V.subtrai_meses(datetime.date(2026, 1, 15), 6), datetime.date(2025, 7, 15))
        # 31/03 não tem correspondente seis meses antes: recua para o último dia
        # existente, adiando a exclusão. O erro cai para o lado de guardar mais.
        self.assertEqual(V.subtrai_meses(datetime.date(2026, 3, 31), 6), datetime.date(2025, 9, 30))

    def test_dentro_do_prazo_nao_sai_do_disco(self):
        hoje = datetime.date(2026, 9, 5)
        for dia in ("2026-09-05", "2026-06-01", "2026-03-05", "2026-03-06"):
            self.cria(dia)
        resultado = V.varre(hoje=hoje, bruto_dir=self.bruto, chaves_dir=self.chaves)
        self.assertEqual(resultado["brutos_apagados"], [])
        self.assertEqual(resultado["chaves_apagadas"], [])
        self.assertEqual(len(os.listdir(self.bruto)), 4)

    def test_vencido_sai_com_a_chave_do_mesmo_dia(self):
        hoje = datetime.date(2026, 9, 5)
        self.cria("2026-03-04")
        self.cria("2026-09-05")
        resultado = V.varre(hoje=hoje, bruto_dir=self.bruto, chaves_dir=self.chaves)
        self.assertEqual([os.path.basename(c) for c in resultado["brutos_apagados"]],
                         ["nginx-2026-03-04.jsonl"])
        self.assertEqual([os.path.basename(c) for c in resultado["chaves_apagadas"]],
                         ["pseudonimo-2026-03-04.key"])
        self.assertEqual(sorted(os.listdir(self.bruto)), ["nginx-2026-09-05.jsonl"])
        self.assertEqual(sorted(os.listdir(self.chaves)), ["pseudonimo-2026-09-05.key"])

    def test_simular_nao_apaga(self):
        self.cria("2025-01-01")
        resultado = V.varre(hoje=datetime.date(2026, 9, 5), bruto_dir=self.bruto,
                            chaves_dir=self.chaves, simular=True)
        self.assertEqual(len(resultado["brutos_apagados"]), 1)
        self.assertTrue(os.path.isfile(os.path.join(self.bruto, "nginx-2025-01-01.jsonl")))

    def test_arquivo_de_outro_formato_nao_e_tocado(self):
        vizinho = os.path.join(self.bruto, "LEIA-ME.txt")
        with open(vizinho, "w", encoding="utf-8") as fh:
            fh.write("nao sou ledger\n")
        V.varre(hoje=datetime.date(2026, 9, 5), bruto_dir=self.bruto, chaves_dir=self.chaves)
        self.assertTrue(os.path.isfile(vizinho))

    def test_recusa_varrer_dentro_de_data(self):
        """O ledger versionado é história do git: o varredor nunca chega nele."""
        resultado = V.varre(hoje=datetime.date(2026, 9, 5),
                            bruto_dir=os.path.join(RAIZ, "data/ops/access"),
                            chaves_dir=self.chaves)
        self.assertEqual(resultado["brutos_apagados"], [])
        self.assertTrue(any("data/" in erro for erro in resultado["erros"]))

    def test_prazo_menor_que_seis_meses_e_recusado_na_linha_de_comando(self):
        saida = subprocess.run([os.path.join(RAIZ, "tools/sweep-origin-access-raw"),
                                "--meses", "3", "--simular"],
                               capture_output=True, text=True)
        self.assertEqual(saida.returncode, 2)
        self.assertIn("art. 15", saida.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
