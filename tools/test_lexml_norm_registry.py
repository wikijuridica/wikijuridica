#!/usr/bin/env python3
"""test_lexml_norm_registry — testes de tools/generate-lexml-norm-registry-20260826.

POR QUE ELE EXISTE. Em 2026-08-29 o raspador mudou em quatro pontos ao mesmo
tempo — leitura do número de REEDIÇÃO no nome oficial, ordenação da tabela,
formato da chave do censo e união com a evidência já gravada — e nenhum deles
tinha teste. O runner diário descobre `tools/test_*.py` por glob; sem este
arquivo as quatro mudanças ficariam cegas para o próximo agente.

O QUE ELE COBRE. Só função pura e leitura de arquivo. **Nenhum teste aqui toca a
rede**: a API pública do LexML/Senado é fonte externa, e teste que depende dela
falharia por indisponibilidade alheia, que é ruído, não sinal.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-lexml-norm-registry-20260826")
EVIDENCIA = os.path.join(RAIZ, "data", "source-audit",
                         "lexml_norm_registry_20260826.jsonl")
TABELA = os.path.join(RAIZ, "internal", "lexml", "norm_registry_generated.go")

falhas: list[str] = []


def confere(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhas.append(mensagem)


def carrega_modulo():
    spec = importlib.util.spec_from_loader(
        "gen_lexml_registry",
        importlib.machinery.SourceFileLoader("gen_lexml_registry", FERRAMENTA),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def testa_numero_do_nome(m) -> None:
    """O sufixo de reedição faz parte do número do ato.

    A forma anterior devolvia "2200" para "Medida Provisória nº 2.200-2", e a
    conferência então RECUSAVA a resposta CORRETA da fonte oficial com "numero
    divergente". Treze medidas provisórias reeditadas ficaram fora da tabela por
    esse motivo — entre elas a 2.200-2, da ICP-Brasil.
    """
    casos = [
        ("Medida Provisória nº 2.200-2 de 24/08/2001", "2200-2"),
        ("Medida Provisória nº 2.225-45 de 04/09/2001", "2225-45"),
        ("Medida Provisória nº 2.200 de 28/06/2001", "2200"),
        ("Lei nº 8.078 de 11/09/1990", "8078"),
        ("Lei Complementar nº 123 de 14/12/2006", "123"),
        ("Emenda Constitucional nº 103 de 12/11/2019", "103"),
    ]
    for nome, esperado in casos:
        obtido = m.numero_do_nome(nome)
        confere(obtido == esperado,
                f"numero_do_nome({nome!r}) = {obtido!r}, esperado {esperado!r}")
    confere(m.numero_do_nome("Constituição Federal de 1988") is None,
            "nome sem 'nº' deveria devolver None, não um número inventado")


def testa_ordem_numero(m) -> None:
    """int('2200-2') estoura — era isso que impedia a tabela de aceitar
    reedição. A reedição ordena logo depois do ato base."""
    confere(m.ordem_numero("2200") < m.ordem_numero("2200-2"),
            "a reedição deve ordenar depois do ato base")
    confere(m.ordem_numero("2200-2") < m.ordem_numero("2225"),
            "a ordenação principal continua sendo pelo número base")
    confere(m.ordem_numero("103") < m.ordem_numero("1103"),
            "ordenação numérica, não lexicográfica")


def testa_chave_do_censo(m) -> None:
    """A chave do censo aceita o sufixo de reedição; sem isso a MP reeditada
    nem chegava a ser consultada."""
    achado = m.CHAVE.match("lei-ref:medida.provisoria:2200-2:2001")
    confere(achado is not None, "CHAVE deveria aceitar número com reedição")
    if achado:
        confere(achado.groups() == ("medida.provisoria", "2200-2", "2001"),
                f"grupos errados: {achado.groups()}")
    simples = m.CHAVE.match("lei-ref:lei:8078:1990")
    confere(simples is not None, "CHAVE deveria continuar aceitando número simples")
    confere(m.CHAVE.match("lei-ref:lei:8078:90") is None,
            "ano de dois dígitos não é chave válida")


def testa_especies_cobrem_a_tabela(m) -> None:
    """Todo tipo que a tabela gerada usa precisa estar em ESPECIES, senão
    escreve_tabela estoura no meio da regeneração."""
    if not os.path.isfile(TABELA):
        return
    rotulos = set(m.ESPECIES.values())
    with open(TABELA, encoding="utf-8") as fh:
        for linha in fh:
            if "{Tipo: " not in linha:
                continue
            rotulo = linha.split("{Tipo: ", 1)[1].split(",", 1)[0].strip()
            confere(rotulo in rotulos,
                    f"tabela usa {rotulo!r}, que não está em ESPECIES")


def testa_evidencia_bate_com_a_tabela() -> None:
    """Toda linha da tabela tem de ter evidência com URL, data da consulta e
    sha256 — é o que separa 'data conferida na fonte' de 'data digitada'."""
    if not (os.path.isfile(EVIDENCIA) and os.path.isfile(TABELA)):
        return
    resolvidas = {}
    for linha in open(EVIDENCIA, encoding="utf-8"):
        linha = linha.strip()
        if not linha:
            continue
        reg = json.loads(linha)
        if not reg.get("tipo"):
            continue
        for campo in ("urn", "fonte", "consultado_em", "sha256_resposta", "data"):
            confere(bool(reg.get(campo)),
                    f"evidência de {reg.get('chave_fallback')} sem {campo}")
        resolvidas[(reg["numero"], reg["ano"])] = reg["data"]

    faltando = []
    for linha in open(TABELA, encoding="utf-8"):
        if "{Tipo: " not in linha:
            continue
        numero = linha.split('Numero: "', 1)[1].split('"', 1)[0]
        ano = int(linha.split("Ano: ", 1)[1].split(",", 1)[0])
        data = linha.split('Data: "', 1)[1].split('"', 1)[0]
        registrada = resolvidas.get((numero, ano))
        if registrada is None:
            faltando.append(f"{numero}/{ano}")
        elif registrada != data:
            falhas.append(f"tabela diz {data} para {numero}/{ano}, "
                          f"evidência diz {registrada}")
    confere(not faltando,
            f"{len(faltando)} entrada(s) da tabela sem evidência: {faltando[:5]}")


def testa_reedicoes_chegaram_na_tabela() -> None:
    """Guarda de regressão do achado: as MPs reeditadas que o acervo cita
    precisam estar datadas, senão a URN não se monta e a norma some do JSON-LD.

    MP 2.200-2 é a da ICP-Brasil (assinatura eletrônica), a mais citada delas.
    """
    if not os.path.isfile(TABELA):
        return
    conteudo = open(TABELA, encoding="utf-8").read()
    for numero, data in (("2200-2", "2001-08-24"), ("2225-45", "2001-09-04")):
        confere(f'Numero: "{numero}"' in conteudo,
                f"MP {numero} ausente da tabela — a reedição volta a colapsar "
                f"no ato base, que é outro ato")
        if f'Numero: "{numero}"' in conteudo:
            linha = [l for l in conteudo.splitlines()
                     if f'Numero: "{numero}"' in l][0]
            confere(f'Data: "{data}"' in linha,
                    f"MP {numero} com data diferente da conferida na fonte "
                    f"({data}): {linha.strip()}")


def testa_uniao_e_o_padrao() -> None:
    """A ARMADILHA QUE FOI DESARMADA, com guarda para não voltar.

    A primeira versão do `--censo` deixava a união OPCIONAL (`--merge`). Rodar
    com censo parcial e sem a flag regenerava a tabela só com o que o censo
    trouxesse, apagando em silêncio as normas já datadas — falha invisível até o
    JSON-LD perder a norma. Texto de --help não é guarda.

    Este teste é sobre o CÓDIGO-FONTE, e não sobre execução, de propósito: o
    caminho de união só se exercita consultando a API pública do LexML, e teste
    que depende de fonte externa falha por indisponibilidade alheia, que é
    ruído. O que precisa ser garantido aqui é a POLARIDADE do default.
    """
    fonte = open(FERRAMENTA, encoding="utf-8").read()
    confere("--substituir" in fonte,
            "a flag de substituição sumiu; sem ela não há como pedir o "
            "comportamento destrutivo explicitamente")
    confere('parser.add_argument("--merge"' not in fonte,
            "--merge voltou: união deve ser o PADRÃO, não uma opção que alguém "
            "esquece de passar")
    confere("if not args.substituir and EVIDENCIA.exists():" in fonte,
            "o ramo de união deixou de ser o padrão — com censo parcial isso "
            "apaga em silêncio as normas já datadas")
    confere("recusas anteriores preservadas" in fonte or "recusas_antigas" in fonte,
            "a preservação das recusas sumiu; recusa com motivo é a evidência "
            "do que a fonte NÃO comprova (R9)")


def main() -> int:
    modulo = carrega_modulo()
    testa_numero_do_nome(modulo)
    testa_ordem_numero(modulo)
    testa_chave_do_censo(modulo)
    testa_especies_cobrem_a_tabela(modulo)
    testa_evidencia_bate_com_a_tabela()
    testa_reedicoes_chegaram_na_tabela()
    testa_uniao_e_o_padrao()

    if falhas:
        for f in falhas:
            print(f"FALHA: {f}", file=sys.stderr)
        return 1
    print("test_lexml_norm_registry: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
