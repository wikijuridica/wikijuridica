#!/usr/bin/env python3
"""Testes de tools/check-social-bots.

O QUE ELES IMPEDEM DE VOLTAR, e o mais importante é o último bloco. Um gate de
rastreio que aprova por construção é pior do que gate nenhum: ele transforma
silêncio em atestado. Por isso há teste exigindo que o veredito de crescimento
saia com a palavra INCONCLUSIVO enquanto as janelas de 14+14 dias não existirem,
e teste exigindo que o tripwire NÃO atribua à rede social uma queda anterior ao
nascimento dela.

O extrator de divergência entre comentário e mapa nasce com teste de FALSO
POSITIVO sobre o texto real do nginx: uma frase que diz, corretamente, que o
SemrushBot fica em tier finito não pode virar acusação.

Tudo offline: nenhum teste toca a rede, o serviço ou o log de produção. O
horizonte do log rotacionado é medido sobre um diretório temporário — teste que
lesse /var/log/nginx mediria a máquina, não o código.
"""
import datetime
import importlib.machinery
import importlib.util
import ipaddress
import os
import tempfile
import unittest

# NOTA SOBRE O IPv6 DAS FIXTURES: 2001:db8::/32 (RFC 3849) seria o certo
# para documentacao, e NAO serve aqui -- `botagents.ip_nao_publico` a
# desconta, corretamente, e a fixture de visitante humano precisa de um
# endereco que a ferramenta aceite como publico. Usa-se um /64 arbitrario
# da faixa publica, que nao e o de nenhum visitante medido: o dado pessoal
# era o bloco ESPECIFICO da pessoa observada, nao a faixa do provedor.

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(RAIZ, "tools", "check-social-bots")

_spec = importlib.util.spec_from_loader(
    "check_social_bots",
    importlib.machinery.SourceFileLoader("check_social_bots", ALVO),
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


NGINX_MINIMO = """
map $http_user_agent $wj_bot_allow {
    default 0;
    ~*googlebot             1;
    ~*bingbot               1;
    ~*applebot/             1;
}

server {
    limit_req zone=wj_generic burst=600 nodelay;

    # NENHUMA `limit_req` AQUI, e a ausencia e a regra. A heranca de limit_req no
    # nginx e tudo-ou-nada: declarar uma so dentro desta location SUBSTITUIRIA as
    # cinco do server{}, inclusive a que da pista livre ao Googlebot, ao GPTBot e
    # ao ClaudeBot.
    location ^~ /redesocial/ {
        proxy_pass http://127.0.0.1:8091;
        proxy_cache wj_social;
    }

    location ^~ /api/v1/redesocial/ {
        limit_req zone=wj_social_escrita burst=10 nodelay;
    }
}
"""


class TestArquivoAuditado(unittest.TestCase):
    def test_banner_no_cabecalho_recusa_a_auditoria(self):
        texto = "# ═══ NAO-CARREGADO-EM-PRODUCAO ═══\nserver {}\n"
        self.assertTrue(gate.banner_de_nao_carregado(texto))

    def test_banner_citado_em_prosa_no_meio_do_arquivo_nao_recusa(self):
        # O nginx vivo cita o banner do outro arquivo na linha 232. Uma busca
        # ingênua se recusaria a auditar justamente a config carregada.
        texto = "server {\n" + "\n" * 200 + "# ver ops/nginx/wikijuridica.conf, onde o banner " \
                "NAO-CARREGADO-EM-PRODUCAO avisa\n}\n"
        self.assertFalse(gate.banner_de_nao_carregado(texto))


class TestBlocoDaLocation(unittest.TestCase):
    def test_recorta_preambulo_e_corpo(self):
        preambulo, corpo = gate.linhas_do_bloco(NGINX_MINIMO, "/redesocial/")
        self.assertIn("pista livre", preambulo)
        self.assertIn("proxy_pass", corpo)
        self.assertNotIn("wj_social_escrita", corpo)

    def test_location_ausente_devolve_nada(self):
        self.assertEqual(gate.linhas_do_bloco("server {}\n", "/redesocial/"), (None, None))

    def test_zero_limit_req_no_bloco_de_leitura(self):
        _, corpo = gate.linhas_do_bloco(NGINX_MINIMO, "/redesocial/")
        self.assertEqual(gate.conta_limit_req(corpo), 0)

    def test_limit_req_comentada_nao_conta_como_diretiva(self):
        texto = NGINX_MINIMO.replace("        proxy_cache wj_social;",
                                     "        # limit_req zone=wj_generic burst=1 nodelay;")
        _, corpo = gate.linhas_do_bloco(texto, "/redesocial/")
        self.assertEqual(gate.conta_limit_req(corpo), 0)

    def test_limit_req_real_no_bloco_de_leitura_e_vista(self):
        # Uma só substituiria as cinco do server{}: a herança é tudo-ou-nada.
        texto = NGINX_MINIMO.replace("        proxy_cache wj_social;",
                                     "        limit_req zone=wj_generic burst=1 nodelay;")
        _, corpo = gate.linhas_do_bloco(texto, "/redesocial/")
        self.assertEqual(gate.conta_limit_req(corpo), 1)


class TestMapaContraAPolitica(unittest.TestCase):
    def test_extrai_tokens_e_default(self):
        tokens, default_zero = gate.tokens_do_mapa(NGINX_MINIMO)
        self.assertEqual(tokens, ["googlebot", "bingbot", "applebot/"])
        self.assertTrue(default_zero)

    def test_equivalencia_exata_nao_produz_falha(self):
        tokens = ["googlebot", "bingbot", "applebot/"]
        self.assertEqual(gate.confere_mapa(tokens, ["Googlebot", "Bingbot", "Applebot"], ["GPTBot", "ClaudeBot"]), [])

    def test_agente_ilimitado_sem_token_reprova(self):
        falhas = gate.confere_mapa(["googlebot"], ["Googlebot", "Bingbot"], [])
        self.assertTrue(any("Bingbot" in f for f in falhas), falhas)

    def test_token_que_isenta_agente_de_tier_finito_reprova(self):
        # `~*applebot` sem a barra da versão pegaria Applebot-Extended, que é
        # treinamento. A barra existe para isso, e o gate tem de enxergar.
        falhas = gate.confere_mapa(["applebot"], ["Applebot"], ["Applebot-Extended"])
        self.assertTrue(any("Applebot-Extended" in f for f in falhas), falhas)

    def test_a_barra_da_versao_separa_applebot_de_applebot_extended(self):
        self.assertEqual(gate.confere_mapa(["applebot/"], ["Applebot"], ["Applebot-Extended"]), [])

    def test_token_orfao_reprova(self):
        falhas = gate.confere_mapa(["googlebot", "botinventado"], ["Googlebot"], [])
        self.assertTrue(any("botinventado" in f for f in falhas), falhas)


class TestDivergenciaDeComentario(unittest.TestCase):
    def test_acha_o_bot_prometido_e_ausente_do_mapa(self):
        preambulo, corpo = gate.linhas_do_bloco(NGINX_MINIMO, "/redesocial/")
        divergentes = gate.divergencia_de_comentario(preambulo, corpo, ["googlebot", "bingbot"], ["Googlebot", "Bingbot"])
        self.assertIn("gptbot", divergentes)
        self.assertIn("claudebot", divergentes)
        self.assertNotIn("googlebot", divergentes)

    def test_frase_sem_promessa_de_isencao_nao_vira_acusacao(self):
        # Falso positivo que este teste impede: a frase diz o CERTO — que o
        # SemrushBot fica em tier finito — e não pode ser lida como promessa.
        preambulo = "# O SemrushBot fica no tier de ferramenta de SEO, com 300 r/m."
        self.assertEqual(gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"]), [])

    def test_bot_isento_e_presente_no_mapa_nao_e_divergencia(self):
        preambulo = "# A heranca da pista livre ao Googlebot continua valendo aqui."
        self.assertEqual(gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"]), [])

    def test_frase_atravessa_varias_linhas_de_comentario(self):
        preambulo = "# ... inclusive a que da pista livre ao Googlebot, ao GPTBot e\n# ao ClaudeBot"
        divergentes = gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"])
        self.assertEqual(sorted(divergentes), ["claudebot", "gptbot"])

    def test_comentario_que_NEGA_a_isencao_nao_vira_acusacao(self):
        # O FALSO POSITIVO QUE CUSTOU UMA RODADA, e ele é do mesmo feitio do
        # defeito que este gate existe para achar: quem corrige a mentira
        # nomeia o bot ao lado da marca de isenção exatamente como a mentira o
        # nomeava. O detector procurava o literal e achava a prosa que o
        # desmentia — e reprovava o comentário CERTO.
        preambulo = "# O GPTBot e o ClaudeBot NAO TEM PISTA LIVRE: o mapa os deixa no tier finito"
        self.assertEqual(gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"]), [])

    def test_negacao_nao_apaga_a_deteccao_quando_a_promessa_e_real(self):
        # Controle positivo da mutação acima: sem ele, "ensinar a ler negação"
        # poderia ter virado "parar de detectar".
        preambulo = "# a pista livre do GPTBot vale aqui"
        self.assertEqual(gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"]), ["gptbot"])

    def test_virgula_corta_a_janela_do_negador(self):
        # A janela é curta e a vírgula a corta de propósito: uma ressalva
        # intercalada não pode virar álibi para a promessa que vem depois.
        preambulo = "# o GPTBot, que nao deveria, tem pista livre neste bloco"
        self.assertEqual(gate.divergencia_de_comentario(preambulo, "", ["googlebot"], ["Googlebot"]), ["gptbot"])

    def test_o_nginx_REAL_desta_arvore_nao_acusa_ninguem(self):
        # Amostra real, não fixture: é o texto servido em produção. Se alguém
        # reescrever o comentário do bloco social prometendo isenção que o mapa
        # não dá, este teste cai junto com o gate.
        caminho = os.path.join(RAIZ, "ops", "nginx", "standalone", "nginx.conf")
        with open(caminho, encoding="utf-8") as arquivo:
            texto = arquivo.read()
        preambulo, corpo = gate.linhas_do_bloco(texto, "/redesocial/")
        tokens, _ = gate.tokens_do_mapa(texto)
        ilimitados, _ = gate.agentes_da_politica(RAIZ)
        self.assertEqual(gate.divergencia_de_comentario(preambulo, corpo, tokens, ilimitados), [])


class TestFaixasDeIP(unittest.TestCase):
    def test_ipv4_dentro_e_fora(self):
        redes = [ipaddress.ip_network("104.208.184.192/28")]
        self.assertTrue(gate.dentro_das_faixas("104.208.184.200", redes))
        self.assertFalse(gate.dentro_das_faixas("8.8.8.8", redes))

    def test_ipv6_e_reconhecido(self):
        redes = [ipaddress.ip_network("2600:1f14::/32")]
        self.assertTrue(gate.dentro_das_faixas("2600:1f14::1", redes))
        self.assertFalse(gate.dentro_das_faixas("2804:7f4::1", redes))

    def test_ip_ilegivel_devolve_none_e_nao_vira_forjada(self):
        # None é "não decidi", e é diferente de False: um IP ilegível não pode
        # virar acusação de fraude contra um bot legítimo.
        self.assertIsNone(gate.dentro_das_faixas("nao-e-ip", []))
        self.assertIsNone(gate.dentro_das_faixas(None, []))


class TestMetodoDeVerificacao(unittest.TestCase):
    def test_ip_range_sem_faixa_no_disco_reprova(self):
        declarados = {"ultima_data": "2026-09-05", "corte": "2026-08-30",
                      "metodos": {"semrushbot": "ip_range", "googlebot": "ip_range"}}
        falhas = gate.confere_metodos(declarados, ["googlebot"])
        self.assertTrue(any("semrushbot" in f for f in falhas), falhas)

    def test_metodo_por_agente_passa(self):
        declarados = {"ultima_data": "2026-09-05", "corte": "2026-08-30",
                      "metodos": {"googlebot": "ip_range", "yandexbot": "rdns_fcrdns", "semrushbot": "none"}}
        self.assertEqual(gate.confere_metodos(declarados, ["googlebot"]), [])

    def test_metodo_unico_em_bloco_reprova(self):
        # Declarar o mesmo método para quem tem faixa oficial e para quem não
        # tem é a métrica mentindo a nosso favor.
        declarados = {"ultima_data": "2026-09-05", "corte": "2026-08-30",
                      "metodos": {"googlebot": "none", "semrushbot": "none"}}
        falhas = gate.confere_metodos(declarados, ["googlebot"])
        self.assertTrue(any("em bloco" in f for f in falhas), falhas)


class TestHorizonteDoLogBruto(unittest.TestCase):
    """O horizonte é medido sobre um diretório de mentira, e não sobre
    /var/log/nginx: teste que depende do log da máquina mede a máquina, não o
    código, e passa ou falha por motivo que ninguém controla."""

    def test_conta_arquivos_e_data_o_mais_antigo(self):
        with tempfile.TemporaryDirectory() as pasta:
            for nome, quando in (("access.log", 1788000000), ("access.log.1", 1787900000),
                                 ("access.log.2.gz", 1787800000), ("error.log", 1787000000)):
                caminho = os.path.join(pasta, nome)
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("x")
                os.utime(caminho, (quando, quando))
            horizonte, erro = gate.horizonte_do_log_bruto(os.path.join(pasta, "access.log"))
        self.assertIsNone(erro)
        # O error.log fica de fora: só a família access.log* transcreve acesso.
        self.assertEqual(horizonte["arquivos"], 3)
        self.assertEqual(horizonte["dia_mais_antigo"],
                         datetime.date.fromtimestamp(1787800000).isoformat())

    def test_diretorio_inexistente_devolve_erro_legivel_e_nao_excecao(self):
        # O gate roda em máquina onde /var/log/nginx pode não ser listável. O que
        # não pode é exceção subindo e derrubando a medição inteira por causa de
        # uma nota de relatório.
        horizonte, erro = gate.horizonte_do_log_bruto("/caminho/que/nao/existe/access.log")
        self.assertIsNone(horizonte)
        self.assertIn("não consegui listar", erro)

    def test_diretorio_sem_access_log_devolve_erro(self):
        with tempfile.TemporaryDirectory() as pasta:
            horizonte, erro = gate.horizonte_do_log_bruto(os.path.join(pasta, "access.log"))
        self.assertIsNone(horizonte)
        self.assertIn("nenhum arquivo access.log*", erro)


def resumo(horas_por_dia, bot_por_dia, ultima_data):
    """Monta o resumo que `le_log_de_origem` produziria."""
    return {
        "horas_por_dia": {d: set(f"{h:02d}" for h in range(n)) for d, n in horas_por_dia.items()},
        "bot_acervo_por_dia": bot_por_dia,
        "ultima_data": ultima_data,
    }


class TestDiasCompletos(unittest.TestCase):
    def test_dia_parcial_nao_conta(self):
        dados = resumo({"2026-09-04": 24, "2026-09-05": 12}, {}, "2026-09-05")
        self.assertEqual(gate.dias_completos(dados["horas_por_dia"]), ["2026-09-04"])


class TestTripwireDoAcervo(unittest.TestCase):
    def test_sem_dia_completo_pos_nascimento_fica_inconclusivo(self):
        # A queda medida entre 02 e 04 de setembro é ANTERIOR à rede social.
        # Atribuí-la a ela seria falsa atribuição.
        dados = resumo({"2026-09-02": 24, "2026-09-03": 24, "2026-09-04": 24, "2026-09-05": 12},
                       {"2026-09-02": 6119, "2026-09-03": 4354, "2026-09-04": 3801, "2026-09-05": 643},
                       "2026-09-05")
        falha, nota = gate.tripwire_do_acervo(dados)
        self.assertIsNone(falha)
        self.assertIn("INCONCLUSIVO", nota)

    def test_queda_acima_do_teto_depois_do_nascimento_dispara(self):
        dados = resumo({"2026-09-03": 24, "2026-09-04": 24, "2026-09-06": 24},
                       {"2026-09-03": 1000, "2026-09-04": 1000, "2026-09-06": 500},
                       "2026-09-06")
        falha, _ = gate.tripwire_do_acervo(dados)
        self.assertIsNotNone(falha)
        self.assertIn("caiu", falha)

    def test_queda_dentro_do_teto_nao_dispara(self):
        dados = resumo({"2026-09-03": 24, "2026-09-04": 24, "2026-09-06": 24},
                       {"2026-09-03": 1000, "2026-09-04": 1000, "2026-09-06": 900},
                       "2026-09-06")
        falha, nota = gate.tripwire_do_acervo(dados)
        self.assertIsNone(falha)
        self.assertIn("tripwire", nota)

    def test_sem_dia_anterior_fica_inconclusivo(self):
        dados = resumo({"2026-09-06": 24}, {"2026-09-06": 10}, "2026-09-06")
        falha, nota = gate.tripwire_do_acervo(dados)
        self.assertIsNone(falha)
        self.assertIn("INCONCLUSIVO", nota)


class TestVereditoDeCrescimento(unittest.TestCase):
    def test_hoje_so_pode_sair_inconclusivo_com_os_dias_que_faltam(self):
        dados = resumo({"2026-09-02": 24, "2026-09-03": 24, "2026-09-04": 24, "2026-09-05": 12},
                       {"2026-09-02": 6119, "2026-09-03": 4354, "2026-09-04": 3801},
                       "2026-09-05")
        linha = gate.veredito_de_crescimento(dados)
        self.assertIn("INCONCLUSIVO", linha)
        self.assertIn("faltam 11 dia(s)", linha)
        self.assertIn("14 na posterior", linha)

    def test_janela_anterior_nao_promete_contagem_regressiva(self):
        # A armadilha que este teste fecha: a janela ANTERIOR é passado, e
        # anunciar "faltam 11 dias" como se esperar resolvesse seria uma contagem
        # regressiva que nunca termina — o verde por construção ao contrário.
        # Ela se completa transcrevendo o log rotacionado, e a linha tem de dizer
        # isso e nomear o produtor.
        dados = resumo({"2026-09-02": 24, "2026-09-03": 24, "2026-09-04": 24},
                       {"2026-09-02": 6119, "2026-09-03": 4354, "2026-09-04": 3801},
                       "2026-09-05")
        linha = gate.veredito_de_crescimento(dados, {"arquivos": 25, "dia_mais_antigo": "2026-08-12"})
        self.assertIn("não se completa por espera", linha)
        self.assertIn("tools/generate-origin-access-ledger --dia", linha)
        self.assertIn("2026-09-02", linha)
        self.assertIn("25 arquivo(s)", linha)
        self.assertIn("2026-08-12", linha)

    def test_janela_posterior_se_completa_por_espera(self):
        dados = resumo({"2026-09-02": 24}, {"2026-09-02": 6119}, "2026-09-05")
        linha = gate.veredito_de_crescimento(dados)
        self.assertIn("posterior se completa por espera", linha)

    def test_janelas_completas_com_n_baixo_continuam_inconclusivas(self):
        horas = {}
        bot = {}
        for dia in range(18, 32):
            horas[f"2026-08-{dia:02d}"] = 24
            bot[f"2026-08-{dia:02d}"] = 1
        for dia in range(5, 19):
            horas[f"2026-09-{dia:02d}"] = 24
            bot[f"2026-09-{dia:02d}"] = 1
        linha = gate.veredito_de_crescimento(resumo(horas, bot, "2026-09-18"))
        self.assertIn("INCONCLUSIVO", linha)
        self.assertIn("N>=100", linha)

    def test_janelas_completas_com_n_suficiente_produzem_medicao(self):
        horas = {}
        bot = {}
        for dia in range(18, 32):
            horas[f"2026-08-{dia:02d}"] = 24
            bot[f"2026-08-{dia:02d}"] = 100
        for dia in range(5, 19):
            horas[f"2026-09-{dia:02d}"] = 24
            bot[f"2026-09-{dia:02d}"] = 150
        linha = gate.veredito_de_crescimento(resumo(horas, bot, "2026-09-18"))
        self.assertNotIn("INCONCLUSIVO", linha)
        self.assertIn("crescimento medido", linha)
        self.assertIn("+50.0%", linha)


def resumoComAtribuicao(horas_por_dia, bot_por_dia, ultima_data, social_por_dia=None, por_agente_dia=None):
    """O resumo com os campos que a ATRIBUICAO do tripwire usa.

    Existe separado de `resumo` para nao mexer nas fixtures que ja provam outra
    coisa: teste que muda de forma para acomodar caso novo e teste que deixa de
    provar o caso velho.
    """
    base = resumo(horas_por_dia, bot_por_dia, ultima_data)
    base["bot_social_por_dia"] = social_por_dia or {}
    base["acervo_por_agente_dia"] = por_agente_dia or {}
    return base


class TestAtribuicaoDaQuedaDoAcervo(unittest.TestCase):
    """O tripwire media uma queda real e lhe pendurava uma causa nao medida.

    Ate 2026-09-05 a mensagem dizia "caiu X% DEPOIS DO NASCIMENTO DA REDE
    SOCIAL" sem nunca ter contado uma requisicao sequer na rede social. Estes
    testes reproduzem os TRES DIAS REAIS que expuseram o defeito, com os numeros
    medidos no ledger de origem -- nao com numeros inventados que confirmariam o
    que eu ja queria concluir.
    """

    # Os numeros abaixo sao os medidos em data/ops/access/nginx-2026-09-0{3,4,5}.jsonl,
    # descontado aquecimento e simulacao.
    DIAS = {"2026-09-03": 24, "2026-09-04": 24, "2026-09-05": 24}
    ACERVO = {"2026-09-03": 4354, "2026-09-04": 3801, "2026-09-05": 2106}
    POR_AGENTE = {
        "2026-09-04": {"mj12bot": 1146, "semrushbot": 519, "oai-searchbot": 456, "amazonbot": 277},
        "2026-09-05": {"semrushbot": 47, "oai-searchbot": 552, "amazonbot": 255},
    }

    def test_zero_trafego_social_nao_e_atribuido_a_rede_social(self):
        dados = resumoComAtribuicao(self.DIAS, self.ACERVO, "2026-09-05",
                                    social_por_dia={}, por_agente_dia=self.POR_AGENTE)
        falha, _ = gate.tripwire_do_acervo(dados)
        self.assertIsNotNone(falha, "queda de 51% tem de continuar REPROVANDO: R6 do contrato")
        self.assertIn("NÃO é atribuível à rede social", falha)
        self.assertIn("ZERO", falha)

    def test_a_queda_continua_reprovando_mesmo_com_causa_benigna(self):
        """O ponto que separa correcao de afrouxamento.

        A causa ser externa NAO transforma o vermelho em verde. Trocar o
        veredito porque a causa parece benigna e o afrouxamento que o contrato
        chama de fraude de gate; o que muda e a EXPLICACAO, nunca o veredito.
        """
        dados = resumoComAtribuicao(self.DIAS, self.ACERVO, "2026-09-05",
                                    social_por_dia={}, por_agente_dia=self.POR_AGENTE)
        falha, _ = gate.tripwire_do_acervo(dados)
        # 48,4% e nao os 51,6% que o gate reportou sobre o disco: a fixture tem
        # DOIS dias completos anteriores (mediana 4078) e o disco tinha mais.
        # O numero da fixture e o da fixture -- copiar aqui o do disco faria o
        # teste passar por coincidencia e quebrar no dia seguinte.
        self.assertIn("48.4%", falha)
        self.assertIn("o teto do tripwire é 20%", falha)

    def test_nomeia_os_agentes_que_sumiram(self):
        dados = resumoComAtribuicao(self.DIAS, self.ACERVO, "2026-09-05",
                                    social_por_dia={}, por_agente_dia=self.POR_AGENTE)
        falha, _ = gate.tripwire_do_acervo(dados)
        self.assertIn("mj12bot (1146 -> 0)", falha)
        self.assertIn("semrushbot (519 -> 47)", falha)
        # Quem NAO caiu nao entra: nomear estavel junto de sumido faz a lista
        # deixar de apontar para onde investigar.
        self.assertNotIn("oai-searchbot", falha)

    def test_com_trafego_social_a_hipotese_de_realocacao_fica_viva(self):
        """O controle positivo, e ele e o que impede o teste de ser tautologico.

        Se a rede social RECEBEU rastreio, realocacao volta a ser hipotese
        legitima -- e a mensagem tem de dizer isso, nao o contrario. Sem este
        caso, o teste de cima passaria com um gate que escrevesse "não é
        atribuível" incondicionalmente, que seria o mesmo defeito ao contrario.
        """
        dados = resumoComAtribuicao(self.DIAS, self.ACERVO, "2026-09-05",
                                    social_por_dia={"2026-09-05": 812},
                                    por_agente_dia=self.POR_AGENTE)
        falha, _ = gate.tripwire_do_acervo(dados)
        self.assertIn("812", falha)
        self.assertIn("hipótese VIVA", falha)
        self.assertNotIn("NÃO é atribuível", falha)

    def test_queda_difusa_nao_inventa_culpado(self):
        """Quando ninguem cai sozinho, dizer isso vale mais que nomear alguem.

        Queda difusa aponta para causa comum -- borda, robots, certificado --,
        que e diagnostico diferente de "um agente foi embora". O gate que
        nomeasse o maior da lista de qualquer jeito mandaria o operador
        investigar o lugar errado.
        """
        difusa = {
            "2026-09-04": {"a": 1000, "b": 1000, "c": 1000},
            "2026-09-05": {"a": 700, "b": 700, "c": 706},
        }
        dados = resumoComAtribuicao(self.DIAS, {"2026-09-03": 4354, "2026-09-04": 3000, "2026-09-05": 2106},
                                    "2026-09-05", social_por_dia={}, por_agente_dia=difusa)
        falha, _ = gate.tripwire_do_acervo(dados)
        self.assertIn("difusa", falha)
        self.assertIn("causa comum", falha)


if __name__ == "__main__":
    unittest.main()
