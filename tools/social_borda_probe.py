"""social_borda_probe — o que os quatro tools/check-social-* compartilham.

DIVISÃO DE TRABALHO ENTRE O GO E ESTES QUATRO SCRIPTS. A asserção sobre a
CONFIGURAÇÃO vive em `internal/socialborda` e roda por
`./tools/go-modern run ./cmd/check <gate>`: ela é determinística, não depende de
serviço no ar e prova a propriedade todo dia. O que estes scripts acrescentam é
a outra metade, que a configuração não pode provar sozinha — o que a borda
DE FATO devolve. Os dois juntos cobrem os dois modos de falha: config errada
(o Go pega) e config certa que não chega ao cliente (a sonda pega).

OS TRÊS DESFECHOS, e a distinção entre eles é contrato deste repositório:

    0   medido e correto
    1   medido e ERRADO — ou o gate estrutural reprovou
    2   NÃO CONSEGUIU MEDIR (serviço fora do ar, log ilegível, gate estrutural
        que não rodou). Indisponibilidade nunca é reprovação.

SONDAGEM SEM FRAUDE. Toda requisição daqui sai com User-Agent próprio e
`X-Warming-Request: true`, contra 127.0.0.1. Nenhuma delas forja User-Agent de
bot real — nem para testar o limite por bot, que é justamente onde a tentação
apareceria: aquela prova é feita sobre a diretiva, no gate Go.
"""
import http.client
import os
import socket
import subprocess
import sys

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")

# O User-Agent é nosso e o cabeçalho marca a requisição como interna: o relatório
# de tráfego exclui essas linhas, então a sonda não infla métrica nenhuma.
UA = "wikijuridica-superficie-probe/1.0"
CABECALHOS_BASE = {"User-Agent": UA, "X-Warming-Request": "true"}

# O nginx do wiki e o processo da rede social.
PORTA_NGINX = 8088
PORTA_SOCIAL = 8091
HOST_PUBLICO = "wikijuridica.com.br"

ACCESS_LOG = "/var/log/nginx/wikijuridica/access.log"

OK, ERRADO, INCONCLUSIVO = 0, 1, 2


def escuta(porta, host="127.0.0.1", timeout=1.0):
    """Diz se há alguém escutando na porta. É o que separa exit 2 de exit 1."""
    try:
        with socket.create_connection((host, porta), timeout=timeout):
            return True
    except OSError:
        return False


def gate_estrutural(nome):
    """Roda o gate Go correspondente e devolve (codigo, saida).

    O código devolvido já é o do CONTRATO desta camada: 0 aprovado, 1 reprovado,
    2 não rodou. run-check sai 75 quando não consegue preparar o binário e 124
    quando estoura o tempo — nenhum dos dois é veredito sobre a configuração, e
    tratá-los como reprovação transformaria problema de máquina em alarme falso.
    """
    try:
        resultado = subprocess.run(
            [os.path.join(RAIZ, "tools", "run-check"), nome],
            capture_output=True, text=True, timeout=600,
        )
    except subprocess.TimeoutExpired:
        return INCONCLUSIVO, f"o gate estrutural {nome} estourou 600 s"
    except OSError as erro:
        return INCONCLUSIVO, f"nao consegui executar tools/run-check: {erro}"
    saida = (resultado.stdout or "") + (resultado.stderr or "")
    if resultado.returncode == 0:
        return OK, saida
    if resultado.returncode == 1:
        return ERRADO, saida
    return INCONCLUSIVO, f"tools/run-check {nome} saiu {resultado.returncode}:\n{saida}"


def requisita(porta, caminho, metodo="GET", cabecalhos=None, timeout=10):
    """Faz uma requisição a 127.0.0.1 e devolve (status, cabeçalhos, erro).

    O `Host` vai como o domínio público porque o nginx casa server_name e monta
    a chave de cache com `$host`: sondar com Host=127.0.0.1 mediria uma chave de
    cache que visitante nenhum usa.
    """
    todos = dict(CABECALHOS_BASE)
    todos["Host"] = HOST_PUBLICO
    if cabecalhos:
        todos.update(cabecalhos)
    conexao = None
    try:
        conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=timeout)
        conexao.request(metodo, caminho, headers=todos)
        resposta = conexao.getresponse()
        resposta.read()
        return resposta.status, dict(resposta.getheaders()), None
    except (OSError, http.client.HTTPException) as erro:
        return None, {}, f"{type(erro).__name__}: {erro}"
    finally:
        if conexao is not None:
            conexao.close()


def cabecalhos_repetidos(cabecalhos_brutos, nome):
    """Devolve todos os valores de um cabeçalho, e não só o último.

    `dict(getheaders())` colapsa repetição, e repetição é exatamente um dos
    defeitos procurados: duas CSPs na mesma resposta são aplicadas como
    interseção pelo navegador.
    """
    alvo = nome.lower()
    return [valor for chave, valor in cabecalhos_brutos if chave.lower() == alvo]


def requisita_bruto(porta, caminho, metodo="GET", cabecalhos=None, timeout=10):
    """Como requisita, mas devolve a lista de pares para inspecionar repetição."""
    todos = dict(CABECALHOS_BASE)
    todos["Host"] = HOST_PUBLICO
    if cabecalhos:
        todos.update(cabecalhos)
    conexao = None
    try:
        conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=timeout)
        conexao.request(metodo, caminho, headers=todos)
        resposta = conexao.getresponse()
        resposta.read()
        return resposta.status, resposta.getheaders(), None
    except (OSError, http.client.HTTPException) as erro:
        return None, [], f"{type(erro).__name__}: {erro}"
    finally:
        if conexao is not None:
            conexao.close()


def relata(nome, codigo, linhas):
    """Imprime o veredito no formato que a suíte diária consome."""
    rotulo = {OK: "OK", ERRADO: "FAIL", INCONCLUSIVO: "INCONCLUSIVO"}[codigo]
    destino = sys.stdout if codigo == OK else sys.stderr
    print(f"\n{nome}: {rotulo}", file=destino)
    for linha in linhas:
        print(f"  - {linha}", file=destino)
    return codigo
