#!/usr/bin/env python3
"""Teste de tools/generate-escolha-de-serializacao.

RODAR:  python3 tools/test_generate_escolha_de_serializacao.py

OFFLINE e sem tocar o dado vivo: cada caso monta os próprios ledgers num
diretório temporário, importa o módulo por caminho (é executável sem extensão) e
chama as funções públicas — nunca reimplementa a agregação, porque teste que
refaz o pipeline à mão fica verde com a regra desligada no código real.

★ OS QUATRO DEFEITOS QUE ESTES CASOS TRAVAM, todos medidos no dado vivo:

1. DUPLA CONTAGEM. `nginx-*.jsonl` e `access-*.jsonl` registram a MESMA
   requisição dinâmica — `/mcp` dá 5.016 pelo nginx e 5.084 pelo Go na janela de
   2026-09-08..11. Somar os dois inflaria `/mcp`, `/api` e a gêmea em ~100%. O
   caso `so_le_o_ledger_do_nginx` prova que o ledger do Go não entra.

2. LINHA ILEGÍVEL ENGOLIDA. 173 linhas de `access-*.jsonl` não são JSON válido,
   em rajadas (65 num dia). Um `except ValueError: continue` sem contador faz a
   rajada seguinte passar invisível. `linha_ilegivel_e_contada`.

3. TRÁFEGO NOSSO NA CONTA. 198.817 das 410.510 linhas de 2026-09-10 são do
   harness de checks (`bot_simulation`), e o aquecimento tem marca própria. Os
   dois saem da conta E aparecem em `descartados`.

4. ADOÇÃO INFLADA POR PROTOCOLO. `robots.txt` e sitemap todo crawler pede, saiba
   ele ou não que existe porta de máquina. Contá-los como "formato de máquina"
   mediria o que o bot faria de qualquer jeito.

★ PROVA POR MUTAÇÃO (cada caso mata um mutante nomeado):

  so_le_o_ledger_do_nginx ........ glob `nginx-*` virar `*-*` (soma os dois)
  linha_ilegivel_e_contada ....... o `except ValueError` voltar a só `continue`
  descarta_aquecimento_e_sonda ... tirar qualquer um dos dois `if` de descarte
  robots_e_sitemap_fora .......... `robots`/`sitemap-feed` entrarem em
                                   CANAIS_DE_MAQUINA
  canal_por_rota ................. `.md` ser testado antes de `/api/v1`
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-escolha-de-serializacao")

_spec = importlib.util.spec_from_loader(
    "escolha_de_serializacao",
    importlib.machinery.SourceFileLoader("escolha_de_serializacao", FERRAMENTA))
modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(modulo)

falhas = []


def req(path, agente="perplexitybot", ts="2026-09-10T12:00:00Z", **extra):
    linha = {"ts": ts, "method": "GET", "path": path, "status": 200,
             "agent_key": agente, "warming": False, "bot_simulation": False,
             "route_class": "page", "origem": "nginx"}
    linha.update(extra)
    return json.dumps(linha, ensure_ascii=False)


def monta(nginx=(), access=(), dia="2026-09-10"):
    destino = tempfile.mkdtemp(prefix="escolha-")
    for prefixo, linhas in (("nginx", nginx), ("access", access)):
        if linhas is None:
            continue
        with open(os.path.join(destino, "%s-%s.jsonl" % (prefixo, dia)), "w",
                  encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
    return destino


def agrega(diretorio):
    """Passa pela SELECAO DE FONTE de producao, nunca por um glob do teste.

    Reimplementar o glob aqui foi o furo original: o mutante que trocava
    `nginx-*` por `*-*` sobrevivia porque o teste nunca chamava a linha mutada.
    """
    linhas, _ = modulo.agrega(modulo.ledgers_de(diretorio), None)
    return linhas


def checa(nome, condicao, detalhe=""):
    if condicao:
        print("  ok   %s" % nome)
    else:
        falhas.append("%s%s" % (nome, (": " + detalhe) if detalhe else ""))


# ------------------------------------------------------------------ 1. FONTE
# O ledger do Go traz a MESMA requisição /mcp. A ferramenta só pode ver a do nginx.
diretorio = monta(nginx=[req("/mcp", agente="claude-user")],
                  access=[req("/mcp", agente="claude-user", origem="go")])
try:
    linhas = agrega(diretorio)
    checa("so_le_o_ledger_do_nginx",
          len(linhas) == 1 and linhas[0]["por_canal"].get("mcp") == 1,
          "esperado mcp=1 (so o nginx), veio %s" % (linhas[0]["por_canal"] if linhas else None))
    # E o teste tem de PROVAR que o arquivo do Go existe, senão passaria por vacuidade.
    checa("o ledger do Go existe no caso",
          os.path.exists(os.path.join(diretorio, "access-2026-09-10.jsonl")))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# ------------------------------------------------------- 2. LINHA ILEGÍVEL
diretorio = monta(nginx=[req("/familia/x/"),
                         '{"ts":"2026-09-10T12:00:01Z","path":"/a/"{"ts":"2026-09-10T12:00:00Z"',
                         req("/familia/y/")])
try:
    linhas = agrega(diretorio)
    checa("linha_ilegivel_e_contada",
          linhas and linhas[0]["linhas_ilegiveis"] == 1,
          "esperado 1, veio %s" % (linhas[0]["linhas_ilegiveis"] if linhas else None))
    checa("linha_ilegivel_nao_vira_requisicao",
          linhas and linhas[0]["requisicoes"] == 2,
          "esperado 2, veio %s" % (linhas[0]["requisicoes"] if linhas else None))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# ------------------------------------------------- 3. AQUECIMENTO E SONDA
diretorio = monta(nginx=[req("/familia/x/"),
                         req("/familia/x/", warming=True),
                         req("/familia/x/", bot_simulation=True,
                             bot_class="self_simulation_probe")])
try:
    linhas = agrega(diretorio)
    checa("descarta_aquecimento_e_sonda",
          linhas and linhas[0]["requisicoes"] == 1,
          "esperado 1, veio %s" % (linhas[0]["requisicoes"] if linhas else None))
    checa("descartados_ficam_visiveis",
          linhas and linhas[0]["descartados"] == {"aquecimento": 1, "sonda_interna": 1},
          "veio %s" % (linhas[0]["descartados"] if linhas else None))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# ------------------------------------------ 4. PROTOCOLO NÃO É ADOÇÃO
diretorio = monta(nginx=[req("/robots.txt"), req("/sitemap.xml"),
                         req("/familia/x/index.md"), req("/familia/x/")])
try:
    linhas = agrega(diretorio)
    checa("robots_e_sitemap_fora_da_conta_de_maquina",
          linhas and linhas[0]["de_maquina"] == 1,
          "esperado 1 (so a gemea), veio %s com %s"
          % (linhas[0]["de_maquina"] if linhas else None,
             linhas[0]["por_canal"] if linhas else None))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# ---------------------------- 4-bis. OS NOMES DO PAR CONTAM COMO MÁQUINA
# O caso 4 prova o que fica FORA de `de_maquina`; este prova o que fica DENTRO, e
# ele nasceu de um mutante que sobreviveu: trocar `feed`/`descritor` de volta por
# `changes`/`well-known` em CANAIS_DE_MAQUINA não era acusado por nenhum caso.
# O efeito de um nome órfão ali é silencioso e caro — `de_maquina` passaria a
# EXCLUIR o feed incremental e o descritor de agente, e a série mentiria sobre
# adoção justamente nas duas portas que a medem.
diretorio = monta(nginx=[req("/changes.json"), req("/.well-known/agent.json"),
                         req("/familia/x/")])
try:
    linhas = agrega(diretorio)
    checa("feed_e_descritor_contam_como_maquina",
          linhas and linhas[0]["de_maquina"] == 2,
          "esperado 2, veio %s com %s"
          % (linhas[0]["de_maquina"] if linhas else None,
             linhas[0]["por_canal"] if linhas else None))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# ------------------------------------------------------- 5. CLASSIFICAÇÃO
esperado = {
    "/mcp": "mcp", "/mcp/": "mcp", "/a2a/v1/card": "a2a",
    "/api/v1/citacoes": "api:citacoes", "/api/v1/citar": "api:citar",
    "/api/v1/lote": "api:lote", "/api/v1/pages": "api:outro",
    # Nomes do par (6a1d0654): `feed` e `descritor` dizem o que a porta E.
    # Este caso e o que acusou a mudanca dele no minuto em que ela pousou.
    "/changes.json": "feed", "/.well-known/agent.json": "descritor",
    "/familia/x/index.md": "gemea", "/robots.txt": "robots",
    "/sitemap.xml": "sitemap-feed", "/feed.xml": "sitemap-feed",
    "/familia/x/": "html", "/familia/x/?utm_source=a": "html",
}
erros = [(rota, modulo.canal_de(rota), alvo)
         for rota, alvo in esperado.items() if modulo.canal_de(rota) != alvo]
checa("canal_por_rota", not erros, "divergiram: %s" % erros)

# ------------------------------------------------- 6. FRAÇÃO POR AGENTE
diretorio = monta(nginx=[req("/familia/x/index.md", agente="gptbot")] * 3
                        + [req("/familia/x/", agente="gptbot")]
                        + [req("/familia/y/", agente="chatgpt-user")] * 2)
try:
    linhas = agrega(diretorio)
    por_agente = {a["agente"]: a for a in linhas[0]["agentes"]}
    checa("fracao_de_maquina_por_agente",
          por_agente["gptbot"]["fracao_de_maquina"] == 0.75
          and por_agente["chatgpt-user"]["fracao_de_maquina"] == 0.0,
          "gptbot %s, chatgpt-user %s" % (por_agente["gptbot"]["fracao_de_maquina"],
                                          por_agente["chatgpt-user"]["fracao_de_maquina"]))
finally:
    shutil.rmtree(diretorio, ignore_errors=True)

# --------------------------------------- 7. A REGUA DAS PORTAS E A DO PAR
# Se cada serie tiver a propria definicao de "/mcp", a divergencia de REGUA
# aparece como fato do mundo. Este caso prova que `canal_de` DELEGA, em vez de
# reimplementar: o mutante que troca a importacao por uma copia local passaria
# despercebido sem ele.
_espec = importlib.util.spec_from_loader(
    "funil_de_maquina_no_teste",
    importlib.machinery.SourceFileLoader(
        "funil_de_maquina_no_teste",
        os.path.join(RAIZ, "tools", "generate-funil-de-maquina")))
_funil = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(_funil)

checa("regua_das_portas_e_a_mesma_funcao",
      modulo.porta_de is _funil.porta_de
      or modulo.porta_de.__code__.co_code == _funil.porta_de.__code__.co_code,
      "canal_de nao esta delegando para o porta_de de generate-funil-de-maquina")

divergentes = [(rota, modulo.canal_de(rota), _funil.porta_de(rota))
               for rota in ("/mcp", "/mcp/", "/a2a/v1/card", "/familia/x/index.md")
               if modulo.canal_de(rota) != _funil.porta_de(rota)]
checa("portas_nao_divergem_entre_as_duas_series", not divergentes,
      "divergiram: %s" % divergentes)

print()
if falhas:
    for f in falhas:
        print("FALHOU: %s" % f)
    print("%d caso(s) falharam" % len(falhas))
    sys.exit(1)
print("todos os casos passaram")
