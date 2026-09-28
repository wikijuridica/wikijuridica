#!/usr/bin/env python3
"""test_check_percursos_fundamento_legal — testes do gate dos percursos.

POR QUE ELE EXISTE. O gate nasceu para vigiar uma seção que só sai em quatro
canais de máquina, onde nenhum humano olha por hábito. Um gate assim, sem teste,
seria a segunda camada de silêncio: ele passaria verde por não estar conferindo
nada e ninguém notaria — que foi exatamente o que aconteceu com os treze testes
que reportavam verde sem exercitar nada (commit 14152a0f).

Cada teste aqui constrói o artefato DEFEITUOSO correspondente e exige a
reprovação. `tools/run-qualidade-diaria` descobre este arquivo pelo glob
`tools/test_*.py`.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "check-percursos-fundamento-legal")

falhas: list[str] = []


def confere(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhas.append(mensagem)


def carrega():
    loader = importlib.machinery.SourceFileLoader("cpfl", FERRAMENTA)
    spec = importlib.util.spec_from_loader("cpfl", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def registro(origem: str, urn: str, rotulo: str, destinos: list[tuple[str, str]]) -> dict:
    return {
        "artefato_versao": "legal-cocitation-v1",
        "intent_id": origem.strip("/").replace("/", "-"),
        "public_path": origem,
        "entrada_sha256": "abc",
        "percursos": [{
            "urn": urn, "rotulo": rotulo,
            "paginas": [{"intent_id": p.strip("/").replace("/", "-"), "path": p,
                         "area": p.split("/")[1], "titulo": t} for p, t in destinos],
        }],
    }


def roda(m, registros: list[dict], rotas_publicadas: list[str]) -> dict:
    """Executa a medição do gate sobre um artefato de mentira."""
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "artefato.jsonl")
        man = os.path.join(tmp, "manifesto.jsonl")
        with open(art, "w", encoding="utf-8") as fh:
            for r in registros:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(man, "w", encoding="utf-8") as fh:
            for rota in rotas_publicadas:
                fh.write(json.dumps({"path": rota, "unique_intent_id": rota}) + "\n")
        art_antigo, man_antigo = m.ARTEFATO, m.MANIFESTO
        m.ARTEFATO, m.MANIFESTO = art, man
        try:
            return m.mede()
        finally:
            m.ARTEFATO, m.MANIFESTO = art_antigo, man_antigo


URN_CC = "urn:lex:br:federal:lei:2002-01-10;10406!art418"
BOM = [registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418",
                [("/consumidor/b/", "B"), ("/trabalhista/c/", "C")])]
ROTAS = ["/imobiliario/a/", "/consumidor/b/", "/trabalhista/c/"]


def testa_caso_bom_passa(m) -> None:
    medida = roda(m, BOM, ROTAS)
    confere(not medida["problemas"], f"o caso bom reprovou: {medida['problemas']}")
    confere(medida["links"] == 2 and medida["cross_area"] == 2,
            f"contagem errada no caso bom: {medida}")


def testa_destino_fora_do_manifesto_reprova(m) -> None:
    """O ANTI-404 EM REPOUSO. O servidor filtra em runtime, mas filtro em runtime
    ESCONDE o problema: se metade dos destinos morreu, o canal empobrece calado."""
    medida = roda(m, BOM, ["/imobiliario/a/", "/consumidor/b/"])
    confere(any("published_manifest" in p for p in medida["problemas"]),
            f"destino fora do manifesto passou: {medida['problemas']}")


def testa_auto_referencia_e_repeticao_reprovam(m) -> None:
    auto = [registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418",
                     [("/imobiliario/a/", "Eu mesmo")])]
    confere(any("si mesma" in p for p in roda(m, auto, ROTAS)["problemas"]),
            "auto-referência passou")
    repetido = [registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418",
                         [("/consumidor/b/", "B"), ("/consumidor/b/", "B de novo")])]
    confere(any("repete o destino" in p for p in roda(m, repetido, ROTAS)["problemas"]),
            "destino repetido na mesma seção passou")


def testa_ancora_vazia_reprova(m) -> None:
    sem = [registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418",
                    [("/consumidor/b/", "")])]
    confere(any("sem âncora" in p for p in roda(m, sem, ROTAS)["problemas"]),
            "destino sem âncora passou — viraria '[](url)' no documento")


def testa_teto_de_atrator_reprova(m) -> None:
    """Sem teto, medido antes de ele existir, uma página era vizinha de 395."""
    rotas = ["/consumidor/atrator/"] + [f"/area{i}/p/" for i in range(m.TETO_DE_ATRATOR + 1)]
    registros = [registro(f"/area{i}/p/", URN_CC, "Código Civil, art. 418",
                          [("/consumidor/atrator/", "Atrator")])
                 for i in range(m.TETO_DE_ATRATOR + 1)]
    medida = roda(m, registros, rotas)
    confere(any("teto de atrator" in p for p in medida["problemas"]),
            f"atrator acima do teto passou: {medida['problemas']}")
    confere(medida["maior_atrator"] == m.TETO_DE_ATRATOR + 1,
            f"maior_atrator veio {medida['maior_atrator']}")


def testa_atribuicao_legal_errada_reprova(m) -> None:
    """A régua mais cara: citação legal mal atribuída é a única classe de defeito
    deste portal com risco real sob a ética da OAB, e nenhuma medição automática
    a pega depois de publicada."""
    errado = [registro("/imobiliario/a/", URN_CC, "CLT, art. 418",
                       [("/consumidor/b/", "B")])]
    confere(any("atribuição legal errada" in p for p in roda(m, errado, ROTAS)["problemas"]),
            "rótulo que nomeia a lei ERRADA passou")
    # E a grafia sem acento continua valendo: não é erro de atribuição.
    sem_acento = [registro("/imobiliario/a/", URN_CC, "Codigo Civil, art. 418",
                           [("/consumidor/b/", "B")])]
    confere(not any("atribuição legal" in p for p in roda(m, sem_acento, ROTAS)["problemas"]),
            "grafia sem acento foi tratada como atribuição errada")


def testa_piso_cross_area_reprova(m) -> None:
    """Se a fração cair ao patamar da malha base, a seção virou mais uma lista."""
    tudo_local = [registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418",
                           [("/imobiliario/b/", "B"), ("/imobiliario/c/", "C")])]
    rotas = ["/imobiliario/a/", "/imobiliario/b/", "/imobiliario/c/"]
    confere(any("atravessam área" in p for p in roda(m, tudo_local, rotas)["problemas"]),
            "artefato 100% same-area passou no piso cross-área")


def testa_duas_geracoes_no_mesmo_artefato_reprovam(m) -> None:
    a = registro("/imobiliario/a/", URN_CC, "Código Civil, art. 418", [("/consumidor/b/", "B")])
    b = registro("/trabalhista/c/", URN_CC, "Código Civil, art. 418", [("/consumidor/b/", "B")])
    b["entrada_sha256"] = "outro"
    confere(any("fingerprints" in p for p in roda(m, [a, b], ROTAS)["problemas"]),
            "artefato montado de duas gerações passou")



def testa_frescor_acusa_artefato_mais_velho_que_a_fonte(m):
    """CONTROLE POSITIVO da regua de frescor.

    Ela nasceu em 2026-09-16 porque este gate saia 0 com o indice CINCO DIAS
    atras da fonte: artefato de 09-11 03:08 contra content/pages.json de 09-16
    10:54. As outras reguas medem densidade — paginas, links, cross-area, maior
    atrator — e densidade alta de um retrato velho continua alta.

    O que ficava servido errado nao aparecia em canal nenhum que alguem abra: a
    secao so sai na gemea .md, no MCP, no A2A e no /api/v1/lote.
    """
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        fonte = os.path.join(tmp, "pages.json")
        open(art, "w").write("{}\n")
        open(fonte, "w").write("[]\n")
        agora = time.time()
        os.utime(art, (agora - 5 * 86400, agora - 5 * 86400))
        os.utime(fonte, (agora, agora))
        velho, motivo = m.frescor(art, fonte)
        confere(velho is True, "artefato 5 dias mais velho que a fonte passou como fresco")
        confere("VELHO" in motivo, f"a mensagem nao diz que esta velho: {motivo!r}")
        confere("5.0 dia" in motivo, f"a mensagem nao traz o atraso medido: {motivo!r}")
        confere("generate-legal-cocitation" in motivo, "a mensagem nao diz como regenerar")


def testa_frescor_aceita_artefato_mais_novo(m):
    """CONTROLE NEGATIVO. Regua que acusa sempre nao serve para nada."""
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        fonte = os.path.join(tmp, "pages.json")
        open(fonte, "w").write("[]\n")
        open(art, "w").write("{}\n")
        agora = time.time()
        os.utime(fonte, (agora - 60, agora - 60))
        os.utime(art, (agora, agora))
        velho, motivo = m.frescor(art, fonte)
        confere(velho is False, f"artefato mais novo que a fonte foi acusado: {motivo!r}")


def testa_frescor_empate_conta_como_em_dia(m):
    """Fronteira escrita antes do numero: `>=`, nao `>`.

    O gerador roda dentro da mesma passada do deploy; mtime igual e o caso
    normal de regeneracao rapida, nao defeito.
    """
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        fonte = os.path.join(tmp, "pages.json")
        open(fonte, "w").write("[]\n")
        open(art, "w").write("{}\n")
        agora = time.time()
        os.utime(fonte, (agora, agora))
        os.utime(art, (agora, agora))
        velho, _ = m.frescor(art, fonte)
        confere(velho is False, "mtime igual foi tratado como atraso")


def testa_frescor_sem_arquivo_e_nao_medido(m):
    """"Nao sei" nunca pode virar "esta tudo bem"."""
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        fonte = os.path.join(tmp, "pages.json")
        open(art, "w").write("{}\n")
        velho, motivo = m.frescor(art, fonte)
        confere(velho is None, "fonte ausente virou veredito")
        confere("nao medido" in motivo, f"a mensagem nao declara que nao mediu: {motivo!r}")



def testa_main_reprova_quando_o_artefato_esta_velho(m):
    """MATA O MUTANTE QUE SOBREVIVEU: a regua existe e nao esta ligada ao veredito.

    Os testes acima exercitam `frescor()` isolada. Trocar `if velho:` por
    `if False:` no `main` os deixaria TODOS verdes com o gate saindo 0 sobre um
    indice vencido — que e exatamente o estado de 2026-09-16, e o motivo pelo qual
    esta regua foi escrita. Cobrir a funcao sem cobrir a fiacao e cobrir metade.
    """
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        man = os.path.join(tmp, "manifesto.jsonl")
        fonte = os.path.join(tmp, "pages.json")
        # Artefato VALIDO pelas outras reguas: um percurso, destino publicado,
        # sem auto-referencia, sem repeticao, atribuicao legal certa. Assim o
        # unico motivo possivel de reprovacao e o frescor.
        # A MESMA fixture que `testa_caso_bom_passa` usa, e o formato de
        # manifesto que `roda()` escreve. Se o cenario tiver QUALQUER outro
        # problema, o gate reprova por ele e o teste passa sem exercitar o
        # frescor — que foi exatamente o que aconteceu na primeira versao deste
        # caso, e o mutante `if False:` sobreviveu.
        with open(art, "w", encoding="utf-8") as fh:
            for r in BOM:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(man, "w", encoding="utf-8") as fh:
            for rota in ROTAS:
                fh.write(json.dumps({"path": rota, "unique_intent_id": rota}) + "\n")
        open(fonte, "w").write("[]\n")
        agora = time.time()
        os.utime(art, (agora - 5 * 86400, agora - 5 * 86400))
        os.utime(fonte, (agora, agora))

        # CONTROLE: com o artefato FRESCO este mesmo cenario tem de sair 0.
        # Sem isto nao se sabe se o 1 veio do frescor ou de outra regua.
        os.utime(art, (agora, agora))
        art_original, man_original, fonte_original = m.ARTEFATO, m.MANIFESTO, m.FONTE
        argv_original_controle = sys.argv
        try:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art, man, fonte
            sys.argv = ["check-percursos-fundamento-legal"]
            codigo_fresco = m.main()
        finally:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art_original, man_original, fonte_original
            sys.argv = argv_original_controle
        confere(codigo_fresco == 0,
                f"o cenario de controle saiu {codigo_fresco} com o artefato FRESCO — "
                "ele tem outro defeito, e o caso abaixo passaria sem exercitar o frescor")
        os.utime(art, (agora - 5 * 86400, agora - 5 * 86400))

        argv_original = sys.argv
        try:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art, man, fonte
            sys.argv = ["check-percursos-fundamento-legal"]
            codigo = m.main()
        finally:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art_original, man_original, fonte_original
            sys.argv = argv_original
        confere(codigo == 1,
                f"o gate saiu {codigo} com o indice 5 dias mais velho que a fonte — "
                "a regua de frescor nao esta ligada ao veredito")
        # E TEM DE SER PELO FRESCOR. Sem esta segunda assercao o teste passaria
        # por qualquer outro problema do artefato de mentira — verde pelo motivo
        # errado, que e o defeito que esta bancada inteira existe para nao ter.
        velho, motivo = m.frescor(art, fonte)
        confere(velho is True and "VELHO" in motivo,
                f"frescor() nao acusou o artefato do cenario: {velho!r} {motivo!r}")
        confere(art in motivo,
                f"a mensagem mede o arquivo REAL em vez do cenario: {motivo!r}")



def testa_main_sai_2_quando_nao_da_para_medir_o_frescor(m):
    """MATA O SEXTO MUTANTE: trocar `return 2` por `return 0` no ramo do
    INCONCLUSIVO.

    Sem este caso, um gate que nao consegue ler a fonte sairia VERDE — e verde
    de quem nao mediu e a forma mais cara de mentira num painel, porque e
    indistinguivel de verde de quem mediu e aprovou.
    """
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "indice.jsonl")
        man = os.path.join(tmp, "manifesto.jsonl")
        fonte = os.path.join(tmp, "pages.json")  # NAO existe de proposito
        with open(art, "w", encoding="utf-8") as fh:
            for r in BOM:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(man, "w", encoding="utf-8") as fh:
            for rota in ROTAS:
                fh.write(json.dumps({"path": rota, "unique_intent_id": rota}) + "\n")

        art_original, man_original, fonte_original = m.ARTEFATO, m.MANIFESTO, m.FONTE
        argv_original = sys.argv
        try:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art, man, fonte
            sys.argv = ["check-percursos-fundamento-legal"]
            codigo = m.main()
        finally:
            m.ARTEFATO, m.MANIFESTO, m.FONTE = art_original, man_original, fonte_original
            sys.argv = argv_original
        confere(codigo == 2,
                f"o gate saiu {codigo} sem conseguir medir o frescor — "
                "'nao medi' tem de ser 2, nunca 0")


def main() -> int:
    m = carrega()
    testa_caso_bom_passa(m)
    testa_destino_fora_do_manifesto_reprova(m)
    testa_auto_referencia_e_repeticao_reprovam(m)
    testa_ancora_vazia_reprova(m)
    testa_teto_de_atrator_reprova(m)
    testa_atribuicao_legal_errada_reprova(m)
    testa_piso_cross_area_reprova(m)
    testa_duas_geracoes_no_mesmo_artefato_reprovam(m)
    testa_frescor_acusa_artefato_mais_velho_que_a_fonte(m)
    testa_frescor_aceita_artefato_mais_novo(m)
    testa_frescor_empate_conta_como_em_dia(m)
    testa_frescor_sem_arquivo_e_nao_medido(m)
    testa_main_reprova_quando_o_artefato_esta_velho(m)
    testa_main_sai_2_quando_nao_da_para_medir_o_frescor(m)

    if falhas:
        for f in falhas:
            print(f"FALHA: {f}", file=sys.stderr)
        return 1
    print("test_check_percursos_fundamento_legal: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
