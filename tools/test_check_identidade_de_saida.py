#!/usr/bin/env python3
"""Testes de `tools/check-identidade-de-saida`, com casos SINTÉTICOS em tmpdir.

Por que sintético: um gate provado só contra o repositório de hoje é um gate que
sabe dizer "verde" e nada mais. Aqui cada regra tem um arquivo mínimo que a
exercita, e o teste roda o gate como PROCESSO — é o exit code que o runner de
qualidade lê, e exit code errado é o defeito que faz gate vermelho passar por
verde.

Nenhum caso toca a rede. O gate é leitura de arquivo, e teste que precisa de
rede não roda na madrugada quando o link cai.

Descoberto pelo passo 2c de `tools/run-qualidade-diaria` (glob `tools/test_*.py`).
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-identidade-de-saida")

CANONICO = ("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
            "+https://wikijuridica.com.br/bot/; coleta-oficial)")


def escreve(diretorio, nome, conteudo):
    caminho = os.path.join(diretorio, nome)
    with open(caminho, "w", encoding="utf-8") as handle:
        handle.write(conteudo)
    return caminho


def roda(*caminhos, raiz=None):
    """Executa o gate e devolve (exit_code, saida_completa)."""
    comando = [sys.executable, GATE]
    if raiz:
        comando += ["--raiz", raiz]
    comando += list(caminhos)
    processo = subprocess.run(comando, capture_output=True, text=True, timeout=120)
    return processo.returncode, processo.stdout + processo.stderr


class IdentidadeDeSaida(unittest.TestCase):

    def test_canonico_com_destino_externo_passa(self):
        """A forma canônica é o que o contrato manda: não pode reprovar."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-coisa", (
                "import urllib.request\n"
                'API = "https://normas.leg.br/api/public/metadados/gerais"\n'
                'USER_AGENT = "%s"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n' % CANONICO))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("VERDE", saida)

    def test_comentario_go_nao_vira_ponto_de_saida(self):
        """Regressao de 2026-09-05, quando o gate foi apontado para internal/.

        Ele acusou TRES pontos em internal/wikijuridicabot/bot.go:28-30 que eram
        a TABELA DE MEDICAO do WAF do Planalto, escrita em comentario `//` --
        justamente o arquivo que DEFINE a identidade canonica. O mascaramento so
        conhecia `#` e docstring de Python.

        Acusacao errada desmoraliza o gate: este repositorio ja teve detector que
        apontou 46 paginas e as 46 eram falso positivo.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "cliente.go", (
                "package cliente\n"
                "\n"
                "// Medido em 2026-09-05 contra www.planalto.gov.br:\n"
                "//\n"
                "//\tcurl -A 'curl/8.5.0'                    -> Recv failure\n"
                "//\tcurl -A 'wikijuridica-verificacao/1.0'   -> Recv failure\n"
                "//\n"
                "/* Bloco antigo, mantido como historico:\n"
                '   req.Header.Set("User-Agent", "wikijuridica-antigo/1.0")\n'
                "   destino: https://www.planalto.gov.br */\n"
                "\n"
                "func Busca() {\n"
                '\treq, _ := http.NewRequest("GET", '
                '"https://www.planalto.gov.br/ccivil_03/leis/l8906.htm", nil)\n'
                "\twikijuridicabot.Aplica(req, wikijuridicabot.PropositoColetaOficial)\n"
                "}\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("VERDE", saida)

    def test_ua_real_em_go_ao_lado_de_comentario_ainda_reprova(self):
        """O outro lado: mascarar comentario nao pode cegar o gate para o codigo.

        Sem este par, a correcao do falso positivo poderia ter sido "ignore
        arquivo .go" -- que trocaria ruido por cegueira.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "envio.go", (
                "package envio\n"
                "\n"
                "// Este comentario fala de User-Agent e nao e ponto de saida.\n"
                "\n"
                "func Envia() {\n"
                '\treq, _ := http.NewRequest("POST", "https://api.resend.com/emails", nil)\n'
                '\treq.Header.Set("User-Agent", "wikijuridica-socialmail/1.0")\n'
                "}\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("wikijuridica-socialmail/1.0", saida)

    def test_canonico_partido_em_duas_linhas_passa(self):
        """Concatenação implícita é como as ferramentas reais escrevem o UA."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-partido", (
                "import urllib.request\n"
                'API = "https://legis.senado.leg.br/dadosabertos"\n'
                'USER_AGENT = ("Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "\n'
                '              "+https://wikijuridica.com.br/bot/; verificacao-de-fonte)")\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_ua_proprio_com_destino_externo_reprova(self):
        """O caso que o gate existe para pegar, com arquivo:linha e o UA na saída."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-coleta", (
                "import urllib.request\n"
                'API = "https://www.planalto.gov.br/ccivil_03"\n'
                'USER_AGENT = "wikijuridica-coletor/1.0 (+wikijuridica.com.br)"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("generate-coleta:3", saida)
            self.assertIn("wikijuridica-coletor/1.0", saida)
            self.assertIn("www.planalto.gov.br", saida)

    def test_sonda_interna_em_127_passa(self):
        """Sonda do próprio portal tem UA próprio de propósito — não se mexe."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-sonda", (
                "import urllib.request\n"
                'BASE = "http://127.0.0.1:8089"\n'
                'UA = "wikijuridica-sonda-de-teste/1.0 (+interno; nao-indexar)"\n'
                'def sondar(rota):\n'
                '    pedido = urllib.request.Request(BASE + rota, headers={\n'
                '        "User-Agent": UA, "X-Warming-Request": "true"})\n'
                '    return urllib.request.urlopen(pedido)\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_sonda_contratual_superficie_probe_passa(self):
        """O contrato nomeia esta sonda e manda não mexer nela."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-superficie", (
                "import urllib.request\n"
                'UA = "wikijuridica-superficie-probe/1.0"\n'
                'def sondar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": UA}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_destino_nao_determinavel_reprova(self):
        """URL vinda de config não isenta: sem prova de destino interno, reprova."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-de-config", (
                "import json\n"
                "import urllib.request\n"
                'USER_AGENT = "wikijuridica-faixas/1.0 (+https://wikijuridica.com.br)"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'
                'def main():\n'
                '    for fonte in json.load(open("politica.json")):\n'
                '        baixar(fonte["url"])\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("destino nao determinavel", saida)

    def test_url_dentro_do_ua_de_terceiro_nao_e_destino(self):
        """`+https://openai.com/gptbot` é documentação de agente, não destino."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-simulacao", (
                "import urllib.request\n"
                'BASE = "http://127.0.0.1:8089"\n'
                'AGENTES = ["Mozilla/5.0 (compatible; GPTBot/1.2; '
                '+https://openai.com/gptbot)"]\n'
                'UA = "wikijuridica-sonda-de-teste/1.0 (+interno; nao-indexar)"\n'
                'def sondar(rota):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        BASE + rota, headers={"User-Agent": UA}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_url_em_comentario_e_docstring_nao_e_destino(self):
        """Bloco de comentário com medição não transforma sonda em saída externa."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-documentado", (
                '"""Mediu-se https://www.planalto.gov.br/ccivil_03 em 2026-09-05."""\n'
                "import urllib.request\n"
                "# Comparado com https://normas.leg.br/api/public/metadados\n"
                'BASE = "http://127.0.0.1:8089"\n'
                'UA = "wikijuridica-doc-probe/1.0 (+interno; nao-indexar)"\n'
                'def sondar(rota):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        BASE + rota, headers={"User-Agent": UA}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_arquivo_de_teste_e_ignorado(self):
        """Fixture de teste não é ponto de saída — varrer tudo seria ruído."""
        with tempfile.TemporaryDirectory() as tmp:
            escreve(tmp, "test_alguma_coisa.py", (
                "import urllib.request\n"
                'API = "https://www.planalto.gov.br/ccivil_03"\n'
                'USER_AGENT = "wikijuridica-fixture/1.0"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            escreve(tmp, "coisa_test.py", (
                "import urllib.request\n"
                'API = "https://www.planalto.gov.br/ccivil_03"\n'
                'USER_AGENT = "wikijuridica-fixture/1.0"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(tmp, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_arquivo_sem_io_de_rede_e_ignorado(self):
        """Analisador de log fala de user_agent o tempo todo e nunca envia nada."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "analisa-log.py", (
                "def familia(registro):\n"
                '    user_agent = registro.get("user_agent") or ""\n'
                '    if "https://www.planalto.gov.br" in user_agent:\n'
                '        return "estranho"\n'
                '    return "outro"\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_arquivo_ilegivel_devolve_dois(self):
        """Link quebrado não pode virar verde: 'não rodou' é exit 2."""
        with tempfile.TemporaryDirectory() as tmp:
            os.symlink(os.path.join(tmp, "inexistente"), os.path.join(tmp, "generate-orfao"))
            codigo, saida = roda(tmp, raiz=tmp)
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NAO RODOU", saida)

    def test_caminho_inexistente_devolve_dois(self):
        """Raiz errada é erro de operação, não veredito de qualidade."""
        with tempfile.TemporaryDirectory() as tmp:
            codigo, saida = roda(os.path.join(tmp, "nao-existe"), raiz=tmp)
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NAO RODOU", saida)

    def test_shell_com_curl_dash_a_reprova(self):
        """Ferramenta em shell tem a mesma régua: `-A` é definição de UA."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "coleta.sh", (
                "#!/usr/bin/env bash\n"
                "UA='wikijuridica-shell/1.0'\n"
                "curl -sS -A \"$UA\" https://www.planalto.gov.br/ccivil_03\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("wikijuridica-shell/1.0", saida)

    def test_ua_montado_por_constantes_canonico_passa(self):
        """A forma correta é montar por constantes, como o pacote Go faz."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-por-constantes", (
                "import urllib.request\n"
                'API = "https://www.planalto.gov.br/ccivil_03"\n'
                'PREFIXO = "Mozilla/5.0 (compatible; "\n'
                'NOME_AGENTE = "WikijuridicaBot"\n'
                'VERSAO = "1.0"\n'
                'DOC = "https://wikijuridica.com.br/bot/"\n'
                'PROPOSITO = "coleta-oficial"\n'
                'USER_AGENT = (\n'
                '    PREFIXO + NOME_AGENTE + "/" + VERSAO + "; +" + DOC\n'
                '    + "; " + PROPOSITO + ")"\n'
                ')\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_ua_montado_por_constantes_com_prefixo_de_navegador_reprova(self):
        """Mutação no prefixo é disfarce de navegador e tem de ser vista."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-disfarcado", (
                "import urllib.request\n"
                'API = "https://www.planalto.gov.br/ccivil_03"\n'
                'PREFIXO = "Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0.0.0 "\n'
                'NOME_AGENTE = "WikijuridicaBot"\n'
                'VERSAO = "1.0"\n'
                'USER_AGENT = PREFIXO + NOME_AGENTE + "/" + VERSAO\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("Chrome/126.0.0.0", saida)

    def test_url_de_documentacao_do_agente_nao_prova_destino_interno(self):
        """`wikijuridica.com.br/bot/` documenta o agente; não é destino."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-com-doc", (
                "import urllib.request\n"
                'DOC = "https://wikijuridica.com.br/bot/"\n'
                'USER_AGENT = "wikijuridica-improvisado/1.0"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("destino nao determinavel", saida)

    # ------------------------------------------------------------------
    # AUSÊNCIA DE IDENTIDADE (item 8 do gate) — o defeito de 2026-09-10.
    # ------------------------------------------------------------------

    MUDO = ("import urllib.request\n"
            'API = "https://ssl.bing.com/webmaster/api.svc/json"\n'
            'def baixar(url):\n'
            '    return urllib.request.urlopen(urllib.request.Request(url))\n')

    def test_saida_sem_user_agent_nenhum_reprova(self):
        """O buraco que o gate tinha: `if not agentes: return [], False`.

        Arquivo que sai para host de terceiro e NÃO define User-Agent nenhum
        escapava da régua que existe justamente para cobrar identidade — o gate
        acusava quem se apresentava errado e absolvia quem não se apresentava.
        Custo medido: `collect-bing-webmaster` e `generate-bing-submit-batch`
        saíram como `Python-urllib/3.x` em ~305 requisicoes/dia para ssl.bing.com
        desde 2026-08-29, com o gate VERDE o tempo inteiro.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "collect-mudo", self.MUDO)
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("collect-mudo:4", saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)
            self.assertIn("ssl.bing.com", saida)

    def test_mutacao_por_ausencia_o_mesmo_arquivo_com_ua_canonico_passa(self):
        """O par do anterior: acrescentar a identidade tem de deixar verde.

        Sem este par, a regra da ausência poderia ser "reprove todo mundo", que
        é gate cego pelo outro lado.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "collect-identificado", (
                "import urllib.request\n"
                'API = "https://ssl.bing.com/webmaster/api.svc/json"\n'
                'USER_AGENT = "%s"\n'
                'def baixar(url):\n'
                '    return urllib.request.urlopen(urllib.request.Request(\n'
                '        url, headers={"User-Agent": USER_AGENT}))\n' % CANONICO))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_sonda_loopback_muda_tambem_reprova(self):
        """Loopback não isenta: sonda sem identidade entra na métrica do portal.

        O contrato (secao 11) manda a sonda do proprio portal sair com
        `wikijuridica-superficie-probe/1.0` E `X-Warming-Request: true` — sem
        isso o portal mede o proprio eco. Um arquivo mudo apontado para
        127.0.0.1 é exatamente esse defeito.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-sonda-muda", (
                "import urllib.request\n"
                'BASE = "http://127.0.0.1:8088"\n'
                'def sondar(rota):\n'
                '    return urllib.request.urlopen(BASE + rota)\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("sonda 127.0.0.1", saida)

    def test_go_que_chama_o_pacote_canonico_nao_e_mudo(self):
        """`wikijuridicabot.Aplica` é a fonte única: quem a chama está identificado.

        Sem esta regra, todo `cmd/*.go` que faz a coisa CERTA viraria falso
        positivo da regra da ausência — nove arquivos, medido em 2026-09-10.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "fetch.go", (
                "package coleta\n"
                "func Busca(url string) {\n"
                '\treq, _ := http.NewRequest("GET", url, nil)\n'
                "\twikijuridicabot.Aplica(req, wikijuridicabot.PropositoColetaOficial)\n"
                "\thttp.DefaultClient.Do(req)\n"
                "}\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_go_mudo_reprova(self):
        """O par: Go que abre requisição e não chama o pacote sai como
        `Go-http-client/1.1`, que é tão anônimo quanto `Python-urllib`."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "fetch-mudo.go", (
                "package coleta\n"
                "func Busca() {\n"
                '\treq, _ := http.NewRequest("GET", '
                '"https://www.planalto.gov.br/ccivil_03", nil)\n'
                "\thttp.DefaultClient.Do(req)\n"
                "}\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)

    # ------------------------------------------------------------------
    # O FALSO POSITIVO SIMÉTRICO: "não sai para a rede" não se acusa.
    # ------------------------------------------------------------------

    def test_vocabulario_com_a_palavra_curl_nao_e_saida(self):
        """`"waf", "curl", "tls"` é vocabulário de motivos, não invocação.

        Caso real: `tools/generate-v2-tombstone-revival` classifica por que uma
        página morreu, e `tools/report-access-traffic` casa `"curl/"`, `"wget"`
        contra o User-Agent de QUEM NOS VISITA. Nenhum dos dois abre socket.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "classifica-motivo", (
                "MOTIVOS = [\n"
                '    "waf", "curl", "tls", "conexao", "wget", "python-urllib",\n'
                "]\n"
                "def familia(texto):\n"
                "    return next((m for m in MOTIVOS if m in texto), 'outro')\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("com chamada de rede : 0", saida)

    def test_prosa_de_descritor_com_a_palavra_curl_nao_e_saida(self):
        """`cmd/publish-v2-direct` escreve "exemplos de `curl`" num descritor.

        É string de conteúdo, não comentário — o mascaramento não a apaga, e
        mesmo assim não é ponto de saída.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "descritor.go", (
                "package descritor\n"
                "const Texto = \"das respostas, exemplos de `curl` e quais \" +\n"
                '\t"operacoes exigem credencial (curl exit 56, HTTP 000)"\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("com chamada de rede : 0", saida)

    def test_curl_em_lista_de_argumentos_e_saida_de_verdade(self):
        """O outro lado: `["curl", "-s", url]` é invocação e tem de ser vista."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "measure-mudo", (
                "import subprocess\n"
                'DESTINO = "https://speed.cloudflare.com"\n'
                "def medir():\n"
                '    return subprocess.run(["curl", "-sS", "--max-time", "20",\n'
                '                           DESTINO + "/__down?bytes=25000000"])\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("speed.cloudflare.com", saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)

    def test_dash_A_em_lista_de_argumentos_conta_como_identidade(self):
        """`"-A", "wikijuridica-superficie-probe/1.0"` em lista de subprocess.

        Caso real de `tools/publicar`: a opção e o valor são DOIS elementos, o
        `-A` fica cercado de aspas e o padrão de shell não o alcançava. O gate o
        lia como MUDO — e a regra da ausência o acusaria por defeito inexistente.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "publicar-confere", (
                "import subprocess\n"
                "def confere(rota):\n"
                '    return subprocess.run(["curl", "-s", "--max-time", "12",\n'
                '                           "-A", "wikijuridica-superficie-probe/1.0",\n'
                '                           "-H", "X-Warming-Request: true",\n'
                '                           "http://127.0.0.1:8088" + rota])\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_ua_de_bot_de_terceiro_no_proprio_portal_fica_fora_da_regra_da_ausencia(self):
        """`check-crawl-recovery-e2e` monta `{"User-Agent": ua}` num laço.

        O valor vem de um dicionário e o extrator não o resolve — mas o arquivo
        NÃO é mudo, e a fronteira declarada do gate manda deixar UA de bot de
        terceiro apontado para o próprio portal para a outra régua
        (`protect-bot-ratelimit`). A regra da ausência não pode invadir isso.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-e2e", (
                "import urllib.request\n"
                'BASE = "https://wikijuridica.com.br"\n'
                'AGENTES = {"googlebot": "Mozilla/5.0 (compatible; Goog"\n'
                '                        "lebot/2.1; +http://www.google.com/bot.html)"}\n'
                'def sondar(nome, rota):\n'
                '    ua = AGENTES[nome]\n'
                '    pedido = urllib.request.Request(BASE + rota,\n'
                '                                    headers={"User-Agent": ua})\n'
                '    return urllib.request.urlopen(pedido)\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    # ------------------------------------------------------------------
    # O EXTRATOR NÃO PODE GRUDAR O CABEÇALHO VIZINHO DENTRO DO UA.
    # ------------------------------------------------------------------

    def test_accept_ao_lado_do_ua_nao_entra_no_ua(self):
        """Regressão de `tools/generate-wikidata-lexml:37`, gate vermelho hoje.

        `headers={"User-Agent": UA, "Accept": "application/sparql-results+json"}`:
        o fatiador engolia o dicionário inteiro e, como `sparql-results+json` tem
        um `+`, a expressão "parecia" concatenação. O gate reprovava um UA que
        ninguém escreveu — `…; wikidata-lexml)Acceptapplication/sparql-results+json`.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-wikidata", (
                "import urllib.request\n"
                'SPARQL = "https://query.wikidata.org/sparql"\n'
                'UA = "%s"\n'
                'def consulta(url):\n'
                '    req = urllib.request.Request(url, headers={"User-Agent": UA, '
                '"Accept": "application/sparql-results+json"})\n'
                '    return urllib.request.urlopen(req)\n' % CANONICO))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertNotIn("Accept", saida)

    def test_mutacao_do_ua_ao_lado_do_accept_continua_sendo_vista(self):
        """O par do anterior: parar de grudar o `Accept` não pode virar cegueira.

        Troca-se só o VALOR da constante por um disfarce de navegador; o resto do
        arquivo é idêntico. Se o extrator tivesse desistido de resolver o nome
        `UA`, este caso ficaria verde e a correção teria trocado falso positivo
        por falso negativo.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "generate-wikidata-disfarcado", (
                "import urllib.request\n"
                'SPARQL = "https://query.wikidata.org/sparql"\n'
                'UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0.0.0 Safari/537.36"\n'
                'def consulta(url):\n'
                '    req = urllib.request.Request(url, headers={"User-Agent": UA, '
                '"Accept": "application/sparql-results+json"})\n'
                '    return urllib.request.urlopen(req)\n'))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("Chrome/126.0.0.0", saida)
            self.assertIn("query.wikidata.org", saida)

    def test_namespace_xml_nao_conta_como_host_de_destino(self):
        """`{http://www.sitemaps.org/schemas/sitemap/0.9}` é identificador de
        vocabulário. Contá-lo como destino fazia o gate dizer "sai para
        www.sitemaps.org" sobre quatro ferramentas que só sondam 127.0.0.1."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "check-sitemap-local", (
                "import http.client\n"
                'ESPACO = "{http://www.sitemaps.org/schemas/sitemap/0.9}"\n'
                'UA = "wikijuridica-superficie-probe/1.0"\n'
                "def busca(porta, rota):\n"
                '    conexao = http.client.HTTPConnection("127.0.0.1", porta)\n'
                '    conexao.request("GET", rota, headers={"User-Agent": UA,\n'
                '                                          "X-Warming-Request": "true"})\n'
                "    return conexao.getresponse()\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertNotIn("sitemaps.org", saida)

    # ------------------------------------------------------------------
    # DELEGAÇÃO É DELEGAÇÃO; MENÇÃO NÃO É.
    # ------------------------------------------------------------------

    def test_quem_carrega_o_modulo_com_a_identidade_nao_e_mudo(self):
        """As quatro ferramentas sociais carregam `tools/social_borda_probe.py`
        e as dezessete da borda importam `tools/cloudflare_auth.py`: a identidade
        mora no módulo compartilhado e elas só a repassam. Copiar o literal para
        cada uma seria a segunda cópia da verdade."""
        with tempfile.TemporaryDirectory() as tmp:
            tools = os.path.join(tmp, "tools")
            os.makedirs(tools)
            escreve(tools, "sonda_compartilhada.py", (
                'UA = "wikijuridica-superficie-probe/1.0"\n'
                'CABECALHOS_BASE = {"User-Agent": UA, "X-Warming-Request": "true"}\n'))
            alvo = escreve(tools, "check-que-delega", (
                "import http.client\n"
                "import importlib.util\n"
                "def carrega():\n"
                '    spec = importlib.util.spec_from_file_location(\n'
                '        "sonda", "sonda_compartilhada.py")\n'
                "    modulo = importlib.util.module_from_spec(spec)\n"
                "    spec.loader.exec_module(modulo)\n"
                "    return modulo\n"
                "def sondar(base, porta, rota):\n"
                '    conexao = http.client.HTTPConnection("127.0.0.1", porta)\n'
                '    conexao.request("GET", rota, headers=base.CABECALHOS_BASE)\n'
                "    return conexao.getresponse()\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)

    def test_apenas_citar_o_nome_de_outra_ferramenta_nao_absolve(self):
        """O par do anterior, e o furo que ele fecharia se não existisse: uma
        frase de ajuda que NOMEIA uma ferramenta identificada não carrega nada.
        Aceitá-la absolveria arquivo mudo por causa de um `print`."""
        with tempfile.TemporaryDirectory() as tmp:
            tools = os.path.join(tmp, "tools")
            os.makedirs(tools)
            escreve(tools, "sonda_compartilhada.py", (
                'UA = "wikijuridica-superficie-probe/1.0"\n'
                'CABECALHOS_BASE = {"User-Agent": UA}\n'))
            alvo = escreve(tools, "check-que-so-cita", (
                "import urllib.request\n"
                'API = "https://api.cloudflare.com/client/v4/zones"\n'
                "def baixar():\n"
                '    print("antes rode sonda_compartilhada.py")\n'
                "    return urllib.request.urlopen(API)\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)
            self.assertIn("api.cloudflare.com", saida)

    def test_grep_dash_A_nao_conta_como_user_agent(self):
        """`-A` de contexto do grep não é `-A` de User-Agent do curl.

        Sem a exigência de que o valor comece em aspas ou `$`, qualquer
        ferramenta de shell com um `grep -A 2` passava a ser tratada como
        identificada — e o `curl` dela continuava saindo como `curl/8.x`.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "coleta-com-grep.sh", (
                "#!/usr/bin/env bash\n"
                "grep -A 2 'padrao' /tmp/entrada.txt\n"
                "curl -sS https://api.cloudflare.com/client/v4/zones\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)

    # ------------------------------------------------------------------
    # NAVEGADOR DIRIGIDO (2026-09-16). Ate aqui o gate so' conhecia idiomas de
    # cliente HTTP, e por isso os cinco arquivos do publicador social saiam para
    # Facebook, LinkedIn e Instagram sem entrar sequer na conta de "arquivos com
    # chamada de rede". A prova por mutacao destes quatro casos e' direta:
    # desfaca a adicao a CHAMADA_DE_REDE e o primeiro fica verde.

    def test_navegacao_por_playwright_sem_identidade_reprova(self):
        """`page.goto` para host de terceiro e' ponto de saida como qualquer outro."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "publicar-coisa.mjs", (
                "import { chromium } from 'playwright-core';\n"
                "const ctx = await chromium.launchPersistentContext('/tmp/p', {});\n"
                "const page = ctx.pages()[0];\n"
                "await page.goto('https://www.facebook.com/wikijuridica');\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("SEM SE IDENTIFICAR", saida)
            self.assertIn("www.facebook.com", saida)

    def test_navegacao_para_file_url_nao_e_saida(self):
        """`goto('file://...')` abre copia local: nao manda navegador para fora.

        E' o caso real de publicador-social/provar-fragmento-de-ancora.mjs, que
        usa `file://` JUSTAMENTE para nao sair — acusa-lo seria inverter o
        veredito sobre quem fez a coisa certa.
        """
        with tempfile.TemporaryDirectory() as tmp:
            alvo = escreve(tmp, "provar-coisa.mjs", (
                "import { chromium } from 'playwright-core'\n"
                "const navegador = await chromium.launch({ headless: true })\n"
                "const pagina = await navegador.newPage()\n"
                "await pagina.goto('file:///tmp/copia.html#art206')\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("com chamada de rede : 0", saida)

    def test_navegador_declarado_no_go_passa_e_sai_nomeado(self):
        """A excecao e' NOMINAL e VISIVEL: passa, e aparece impressa a cada execucao."""
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "tools", "publicador-social")
            os.makedirs(destino)
            alvo = escreve(destino, "publicar.mjs", (
                "import { chromium } from 'playwright-core';\n"
                "const ctx = await chromium.launchPersistentContext('/tmp/p', {});\n"
                "const page = ctx.pages()[0];\n"
                "await page.goto('https://www.linkedin.com/feed/');\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("publicar.mjs [isento pela excecao", saida)
            self.assertIn("sess\u00e3o do titular", saida)
            # O arquivo que NAO entrou nesta varredura nao pode sair com rotulo
            # de alarme: "nao vi" e "nao varri" sao estados diferentes.
            self.assertIn("olhar-pagina.mjs [fora desta varredura]", saida)

    def test_arquivo_declarado_que_se_identifica_sai_como_aprovado(self):
        """QUATRO ESTADOS. Aprovado pela identidade propria NAO e' "nao vi".

        E' o caso real de `tools/coletor-bing-ia/coletar.mjs`: ele define o UA
        canonico, entao o gate o CONTA como ponto de saida e o aprova pelo
        valor; a excecao continua declarada porque cobre a fase de LOGIN, que
        nenhuma varredura de texto alcanca. Colapsar este estado com "nao
        reconhecido" faria o rotulo do instrumento esconder o do dado.
        """
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "tools", "coletor-bing-ia")
            os.makedirs(destino)
            alvo = escreve(destino, "coletar.mjs", (
                "import { chromium } from 'playwright-core';\n"
                "const CAB = { 'User-Agent': '%s' };\n"
                "const ctx = await chromium.launchPersistentContext('/tmp/p', {});\n"
                "const page = ctx.pages()[0];\n"
                "await page.goto('https://www.bing.com/webmasters/home');\n"
                "await ctx.request.post('https://www.bing.com/webmasters/api/x',"
                " { headers: CAB });\n" % CANONICO))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 0, saida)
            self.assertIn("coletar.mjs [analisado como saida, identidade propria aprovada]",
                          saida)

    def test_navegador_declarado_que_escreve_ua_improvisado_ainda_reprova(self):
        """A excecao cobre a AUSENCIA de UA, nunca um UA improvisado escrito ali.

        Sem esta separacao a lista viraria cheque em branco sobre o arquivo, e
        cheque em branco e' como um `Chrome/126.0.0.0` escrito a mao entra sem
        ninguem ver — que e' o defeito que a isencao por TEXTO ja causou neste
        repositorio em 2026-09-05.
        """
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "tools", "publicador-social")
            os.makedirs(destino)
            alvo = escreve(destino, "publicar.mjs", (
                "import { chromium } from 'playwright-core';\n"
                "const ctx = await chromium.launchPersistentContext('/tmp/p', {});\n"
                "const page = ctx.pages()[0];\n"
                "await page.setExtraHTTPHeaders({ 'User-Agent': 'Chrome/126.0.0.0' });\n"
                "await page.goto('https://www.linkedin.com/feed/');\n"))
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 1, saida)
            self.assertIn("Chrome/126.0.0.0", saida)

    def test_lista_do_go_ilegivel_e_exit_2_nunca_verde(self):
        """Perder a fonte unica e' INFRA QUEBRADA, nunca "nao ha excecao nenhuma"."""
        with tempfile.TemporaryDirectory() as tmp:
            pacote = os.path.join(tmp, "internal", "wikijuridicabot")
            os.makedirs(pacote)
            escreve(pacote, "bot.go", (
                "package wikijuridicabot\n\n"
                "var SegundaIdentidadeConhecida = map[string]string{\n"
                '\t"tools/x": "motivo",\n'
                "}\n"))
            alvo = escreve(tmp, "check-nada", "print('sem rede')\n")
            codigo, saida = roda(alvo, raiz=tmp)
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NavegadorRealDoTitular", saida)

    def test_gate_nao_reprova_a_si_mesmo(self):
        """O gate carrega literais de UA como padrão; reprovar-se seria absurdo."""
        codigo, saida = roda(GATE)
        self.assertEqual(codigo, 0, saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
