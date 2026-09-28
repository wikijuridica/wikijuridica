#!/usr/bin/env python3
"""Testes do passo 6 de tools/deploy-binario-go — a invalidação do cache de origem.

POR QUE (2026-09-16). Este passo existe desde a lição de 2026-09-05: purgar a
borda com a origem velha repopula o Tiered Cache com o conteúdo anterior. Só que
ele delegava a `tools/purge-origin-cache`, que até hoje derivava o nome do objeto
de um palpite e alcançava 1 de 2 ou 3 — ou seja, o passo rodava, saía 0 e não
invalidava as variantes de `Vary: Accept-Encoding` que a borda de fato pede.

Com a ferramenta varrendo a zona, o custo saiu do palpite e foi para a varredura,
que é por CHAMADA. Medido sobre as 11.268 rotas dinâmicas (25.022 objetos na
zona, modo seco): 400 rotas por argv = 7,20 s (29 chamadas, ~209 s); 4.000 por
argv = 9,97 s (3 chamadas, ~30 s); a lista inteira por `--de-arquivo` = 5,66 s,
uma chamada. Estes testes travam a forma: UMA chamada, lista em arquivo, e
qualquer exit != 0 aborta ANTES da purga de borda.

Uso: python3 tools/test_deploy_binario_go_invalidacao_origem.py
"""

import importlib.machinery
import importlib.util
import os
import pathlib
import sys

sys.dont_write_bytecode = True

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = pathlib.Path(os.environ.get("DEPLOY_BINARIO_GO_BIN",
                                         str(RAIZ / "tools" / "deploy-binario-go")))

FALHAS = []


def verifica(condicao, descricao):
    print("  %s %s" % ("ok  " if condicao else "FALHA", descricao))
    if not condicao:
        FALHAS.append(descricao)


def carrega():
    loader = importlib.machinery.SourceFileLoader("deploy_binario_go", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class ContextoFalso:
    def __init__(self, rotas, seco=True):
        self.rotas = list(rotas)
        self.seco = seco
        self.registros = []

    def anota(self, passo, estado, detalhe):
        self.registros.append((passo, estado, detalhe))


def com_roda_falso(mod, codigo, comandos, listas):
    def roda(comando, ctx, ambiente=None, timeout=1800):
        comandos.append(list(comando))
        # A lista tem de existir NO MOMENTO da chamada: o passo apaga depois.
        caminho = comando[comando.index("--de-arquivo") + 1] if "--de-arquivo" in comando else None
        listas.append(pathlib.Path(caminho).read_text(encoding="utf-8") if caminho
                      and os.path.exists(caminho) else None)
        return codigo, "(dublê)"
    return roda


def test_uma_chamada_com_a_lista_em_arquivo(mod):
    rotas = ["/r%d/index.md" % i for i in range(5000)]
    ctx = ContextoFalso(rotas)
    comandos, listas = [], []
    roda_original = mod.roda
    try:
        mod.roda = com_roda_falso(mod, 0, comandos, listas)
        mod.passo_6_invalidar_origem(ctx, "6-invalidar-origem")
    finally:
        mod.roda = roda_original
    verifica(len(comandos) == 1,
             "5.000 rotas viram UMA chamada, não um lote por fatia (foram %d)" % len(comandos))
    verifica("--de-arquivo" in comandos[0],
             "a lista vai por arquivo, não por 5.000 `--rota` no argv")
    verifica(not any(a == "--rota" for a in comandos[0]),
             "nenhum `--rota` sobrou no comando")
    verifica(listas[0] is not None and listas[0].count("\n") == 5000,
             "o arquivo continha as 5.000 rotas no momento da chamada")
    verifica("--seco" in comandos[0], "em ensaio o `--seco` vai junto, por defesa em profundidade")
    verifica(ctx.registros and ctx.registros[0][1] == "seco",
             "o passo se anota como ensaio")


def test_lista_temporaria_nao_fica_no_disco(mod):
    ctx = ContextoFalso(["/a/index.md"])
    caminhos = []
    roda_original = mod.roda

    def roda(comando, ctx_, ambiente=None, timeout=1800):
        caminhos.append(comando[comando.index("--de-arquivo") + 1])
        return 0, ""
    try:
        mod.roda = roda
        mod.passo_6_invalidar_origem(ctx, "6-invalidar-origem")
    finally:
        mod.roda = roda_original
    verifica(caminhos and not os.path.exists(caminhos[0]),
             "a lista temporária é apagada depois da chamada")


def test_exit_nao_zero_aborta_antes_da_purga_de_borda(mod):
    """O CONTROLE: exit 2 da ferramenta (objeto que resistiu na zona) tem de
    parar a cadeia. Seguir para a purga de borda com a origem velha é o defeito
    de 2026-09-05 que este passo existe para impedir."""
    ctx = ContextoFalso(["/a/index.md"], seco=False)
    comandos, listas = [], []
    roda_original = mod.roda
    caminho_visto = {}

    def roda(comando, ctx_, ambiente=None, timeout=1800):
        comandos.append(list(comando))
        caminho_visto["p"] = comando[comando.index("--de-arquivo") + 1]
        return 2, "FALHA: 2 objeto(s) continuam na zona"
    try:
        mod.roda = roda
        mod.passo_6_invalidar_origem(ctx, "6-invalidar-origem")
    except mod.Falha as erro:
        verifica("A borda NÃO foi purgada" in str(erro),
                 "a falha diz, em uma linha, que a borda não foi purgada")
        verifica("restantes" in str(erro) or "resistiu" in str(erro),
                 "a falha nomeia o que exit 2 significa na ferramenta nova")
    else:
        verifica(False, "exit 2 da invalidação TEM de levantar Falha")
    finally:
        mod.roda = roda_original
    verifica("--seco" not in comandos[0], "fora do ensaio o comando é real")
    verifica(not os.path.exists(caminho_visto.get("p", "")),
             "a lista temporária some mesmo quando o passo falha")


def main():
    mod = carrega()
    print("uma chamada, lista em arquivo:")
    test_uma_chamada_com_a_lista_em_arquivo(mod)
    print("lista temporária:")
    test_lista_temporaria_nao_fica_no_disco(mod)
    print("exit != 0 aborta:")
    test_exit_nao_zero_aborta_antes_da_purga_de_borda(mod)
    print("\n%d falha(s)" % len(FALHAS))
    for f in FALHAS:
        print("  - %s" % f)
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(main())
