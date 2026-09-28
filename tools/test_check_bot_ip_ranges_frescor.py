#!/usr/bin/env python3
"""Teste de tools/check-bot-ip-ranges-frescor.

RODAR:  python3 tools/test_check_bot_ip_ranges_frescor.py

TOTALMENTE OFFLINE. Nenhum caso toca a rede nem as faixas versionadas: cada
teste monta o seu proprio diretorio temporario e invoca a ferramenta como
SUBPROCESSO com `--dir`, para exercitar `sys.exit(main())` — a linha que decide
0, 1 ou 2 — em vez de `main()` importado.

★ POR QUE A MAIORIA DOS CASOS E DE FALSO POSITIVO

Regra da casa: detector novo nasce com teste de falso positivo sobre caso
inocente parecido. Ja houve aqui detector que acusou 46 paginas sendo que as 46
eram falso positivo, e este gate tem um caso inocente OBVIO e MEDIDO no dado
real de 2026-08-28:

    bingbot.json ........... creationTime = 2024-01-03  (mais de 1,5 ano)
    perplexitybot.json ..... creationTime = 2025-02-07
    openai-gptbot.json ..... creationTime = 2025-10-30
    openai-searchbot.json .. creationTime = 2026-01-02

Os quatro estao RIGOROSAMENTE EM DIA — quem esta velho e a lista do operador,
nao a nossa coleta. Um detector de frescor que lesse `creationTime` reprovaria
4 dos 12 arquivos de imediato. O caso `upstream_antigo_coleta_nova` fixa isso.

Cada caso afirma o exit code CERTO **e nega o errado**: nao basta "nao deu 0",
tem de nao ser 1 quando a resposta correta e 2 — as duas pedem acoes diferentes
de quem le o exit (faixa velha se recoleta; faixa ilegivel se investiga).
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "check-bot-ip-ranges-frescor")

falhas = []


def carimbo(dias_atras):
    """`fetched_at` relativo ao relogio real, na forma que o gerador grava."""
    instante = (datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=dias_atras))
    return instante.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def faixa(operador, dias_atras, **extra):
    """Um registro com a MESMA forma que generate-bot-ip-ranges escreve."""
    registro = {
        "schema_version": "bot_ip_ranges_v1",
        "operator": operador,
        "source_url": "https://example.invalid/%s.json" % operador,
        "prefix_schema": "prefixes_ipv4prefix_ipv6prefix",
        "official_doc": "",
        "authenticates_agents": [operador],
        "creation_time_upstream": "2026-08-27T14:46:16.000000",
        "prefix_count": 2,
        "prefixes": ["66.249.64.0/27", "2001:4860:4801:10::/64"],
        "malformed_prefixes": [],
    }
    if dias_atras is not None:
        registro["fetched_at"] = carimbo(dias_atras)
    registro.update(extra)
    return registro


def monta(arquivos):
    """Diretorio temporario com os arquivos pedidos. `None` grava texto cru."""
    destino = tempfile.mkdtemp(prefix="frescor-")
    for nome, conteudo in arquivos.items():
        caminho = os.path.join(destino, nome)
        with open(caminho, "w", encoding="utf-8") as handle:
            if isinstance(conteudo, str):
                handle.write(conteudo)
            else:
                json.dump(conteudo, handle, ensure_ascii=False, indent=1, sort_keys=True)
    return destino


def roda(diretorio, *args):
    proc = subprocess.run([sys.executable, FERRAMENTA, "--dir", diretorio] + list(args),
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def caso(nome, arquivos, esperado, args=(), nega=()):
    diretorio = monta(arquivos)
    try:
        codigo, saida = roda(diretorio, *args)
    finally:
        shutil.rmtree(diretorio, ignore_errors=True)
    if codigo != esperado:
        falhas.append("%s: exit %d, esperado %d\n%s" % (nome, codigo, esperado, saida))
        return
    for proibido in nega:
        if codigo == proibido:
            falhas.append("%s: exit %d era exatamente o veredito errado" % (nome, proibido))
    print("  ok   %-34s exit %d" % (nome, codigo))


# ---------------------------------------------------------------- FALSO POSITIVO
# Casos inocentes que um detector ingenuo acusaria. Todos tem de sair 0.

caso("upstream_antigo_coleta_nova",
     # O caso real: bingbot publica com creationTime de 2024-01-03 e esta em dia.
     {"bingbot.json": faixa("bingbot", 0.2,
                            creation_time_upstream="2024-01-03T10:00:00.121331")},
     esperado=0, nega=(1,))

caso("logo_abaixo_do_limiar",
     {"googlebot.json": faixa("googlebot", 2.9)},
     esperado=0, nega=(1,))

caso("fetched_at_com_offset_em_vez_de_Z",
     # ISO 8601 valido escrito por outra ferramenta. Reprovar seria acusar
     # formato, nao idade.
     {"anthropic.json": faixa("anthropic", 0.5,
                              fetched_at=(datetime.datetime.now(datetime.timezone.utc)
                                          - datetime.timedelta(hours=12))
                              .replace(microsecond=0).isoformat())},
     esperado=0, nega=(1,))

caso("arquivo_que_nao_e_faixa_ao_lado",
     # Um indice/nota no diretorio nao tem fetched_at e nunca prometeu ter.
     {"googlebot.json": faixa("googlebot", 0.1),
      "_notas.json": {"observacao": "arquivo auxiliar sem prefixos"}},
     esperado=0, nega=(1,))

caso("arquivo_nao_json_ignorado",
     {"googlebot.json": faixa("googlebot", 0.1), "README.md": "texto solto\n"},
     esperado=0, nega=(1, 2))

caso("carimbo_alguns_segundos_no_futuro",
     # Passo de NTP, nao adulteracao: dentro de SKEW_TOLERADO_S.
     {"googlebot.json": faixa("googlebot", -60.0 / 86400.0)},
     esperado=0, nega=(1,))

caso("doze_faixas_frescas",
     {("op%02d.json" % i): faixa("op%02d" % i, 0.3 + i * 0.05) for i in range(12)},
     esperado=0, nega=(1, 2))

# ------------------------------------------------------------- VERDADEIRO POSITIVO
# O que o gate existe para pegar. Exit 1 = veredito medido.

caso("faixa_vencida",
     {"googlebot.json": faixa("googlebot", 5.0)},
     esperado=1, nega=(0, 2))

caso("uma_vencida_no_meio_de_frescas",
     {"googlebot.json": faixa("googlebot", 0.2),
      "bingbot.json": faixa("bingbot", 9.0),
      "anthropic.json": faixa("anthropic", 0.4)},
     esperado=1, nega=(0,))

caso("sem_fetched_at",
     # Estado do disco ANTES desta frente: JSON valido, idade indeterminada.
     {"googlebot.json": faixa("googlebot", None)},
     esperado=1, nega=(0, 2))

caso("fetched_at_sem_fuso",
     {"googlebot.json": faixa("googlebot", 0.1, fetched_at="2026-08-28T10:00:00")},
     esperado=1, nega=(0,))

caso("fetched_at_no_futuro_alem_do_skew",
     {"googlebot.json": faixa("googlebot", -2.0)},
     esperado=1, nega=(0,))

caso("fetched_at_lixo",
     {"googlebot.json": faixa("googlebot", 0.1, fetched_at="ontem")},
     esperado=1, nega=(0,))

caso("limiar_apertado_pela_flag",
     {"googlebot.json": faixa("googlebot", 2.0)},
     esperado=1, args=("--max-dias", "1"), nega=(0,))

# ------------------------------------------------------------------ NAO CONSEGUI MEDIR
# Exit 2. Nunca pode virar 1: "nao abri o arquivo" nao e "a faixa esta velha".

caso("json_invalido",
     {"googlebot.json": "{\"prefixes\": [ truncado"},
     esperado=2, nega=(0, 1))

caso("json_valido_que_nao_e_objeto",
     {"googlebot.json": "[1, 2, 3]"},
     esperado=2, nega=(0, 1))

caso("invalido_no_meio_de_frescas",
     # Um operador que eu nao sei conferir ja impede afirmar que o diretorio
     # esta fresco — e continua sendo falha de medicao, nao veredito.
     {"googlebot.json": faixa("googlebot", 0.2), "bingbot.json": "{ nao fecha"},
     esperado=2, nega=(0, 1))

caso("diretorio_vazio",
     {},
     esperado=2, nega=(0, 1))

caso("so_arquivos_que_nao_sao_faixa",
     {"_notas.json": {"observacao": "sem prefixos"}},
     esperado=2, nega=(0, 1))

# `--dir` inexistente nao passa por monta(); testado direto.
_codigo, _saida = roda(os.path.join(tempfile.gettempdir(), "frescor-nao-existe-xyz"))
if _codigo != 2:
    falhas.append("diretorio_ausente: exit %d, esperado 2\n%s" % (_codigo, _saida))
else:
    print("  ok   %-34s exit %d" % ("diretorio_ausente", _codigo))

print()
if falhas:
    for f in falhas:
        print("FALHOU: %s" % f)
    print("%d caso(s) falharam" % len(falhas))
    sys.exit(1)
print("todos os casos passaram")
