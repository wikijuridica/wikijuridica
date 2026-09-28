#!/usr/bin/env python3
"""test_check_internal_link_block — testes do gate do bloco de links.

POR QUE ELE EXISTE. Gate que só passa não protege nada: o que precisa ser
provado é que ele REPROVA quando deve. E como este gate tem duas réguas com
polaridades diferentes (absoluta e no-worse), confundi-las é o defeito mais
provável — um absoluto sobre os 13 grupos byte-idênticos que já estão no disco
nasceria vermelho e travaria a fábrica por defeito preexistente.

A MEDIÇÃO NÃO SE ESCREVE À MÃO AQUI, e isto é correção de causa, não estilo.
Até 2026-09-16 `medicao_limpa()` era uma CÓPIA MANUAL do dicionário que
`check-internal-link-block.mede()` devolve. Em 2026-09-11 o produtor ganhou a
chave `exemplo_sem_ponte` (para que a mensagem "PIOROU: 23 -> 160" nomeasse
alguma página) e a cópia não acompanhou: desde aquele dia esta bancada morria
com `KeyError: 'exemplo_sem_ponte'` — falha que não fala do defeito, fala da
cópia. Agora a medição vem de `mede()` DE VERDADE, sobre um corpus sintético
injetado no lugar da varredura do disco, e a baseline no-worse é derivada dessa
mesma medição: chave nova no produtor entra sozinha, e empatar passa por
construção. O seam já existia — `mede(modulo)` recebe o medidor.

O corpus é pequeno e conhecido, e `testa_corpus_exercita_as_quatro_reguas` é o
controle positivo que impede o inverso do KeyError: um corpus que zerasse as
quatro métricas no-worse deixaria "piorar em 1" passar trivialmente, e a bancada
ficaria verde sem medir nada.

A varredura real de `public/` é coberta por test_measure_link_graph.py, que é de
quem ela é.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-internal-link-block")
BASELINE_VERSIONADA = os.path.join(RAIZ, "data", "ops", "link_graph_baseline.jsonl")

falhas: list[str] = []


def confere(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhas.append(mensagem)


def carrega():
    spec = importlib.util.spec_from_loader(
        "check_internal_link_block",
        importlib.machinery.SourceFileLoader("check_internal_link_block", GATE),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ───────────────────────────── o corpus ──────────────────────────────────────
#
# Seis rotas em duas áreas, desenhadas para que a medição saia LIMPA nas réguas
# absolutas (zero autolink, zero destino inexistente, zero âncora vazia, zero
# destino repetido, zero órfã, tudo abaixo dos tetos de bytes) e NÃO-ZERO nas
# quatro no-worse, que é o que dá sentido a "piorar em 1 reprova":
#
#   agravo e apelacao emitem o MESMO bloco  -> 1 grupo byte-idêntico, 2 páginas
#   agravo e apelacao apontam para os mesmos destinos -> 1 par de doorway
#   agravo e apelacao só linkam dentro da própria área -> 2 sem ponte cross-área
#   recurso promete "Prazos de processo" e o manifesto diz outra coisa -> 1 âncora divergente
#
# Grau de entrada: agravo <- embargos, prazos | apelacao <- recurso, prazos |
# embargos e recurso <- agravo, apelacao | prazos <- embargos, recurso. Nenhuma
# página com bloco fica órfã. `custas` não tem bloco: é o caminho da página fora
# da malha, que existe no acervo e não pode entrar na conta.
TITULOS = {
    "/jurisprudencia/agravo-de-instrumento/": "Agravo de instrumento",
    "/jurisprudencia/apelacao-civel/": "Apelação cível",
    "/jurisprudencia/embargos-de-declaracao/": "Embargos de declaração",
    "/jurisprudencia/recurso-especial/": "Recurso especial",
    "/guias/prazos-processuais/": "Prazos processuais",
    "/guias/custas-judiciais/": "Custas judiciais",
}

AGRAVO = "/jurisprudencia/agravo-de-instrumento/"
APELACAO = "/jurisprudencia/apelacao-civel/"
EMBARGOS = "/jurisprudencia/embargos-de-declaracao/"
RECURSO = "/jurisprudencia/recurso-especial/"
PRAZOS = "/guias/prazos-processuais/"
CUSTAS = "/guias/custas-judiciais/"

# Tamanho da página sem vaga de `testa_projecao_cresce_com_as_vagas`. Tem de ser
# o MAIOR de todo aquele corpus depois da projeção: as outras chegam a
# 42000 + 6×custo e 30000 + 8×custo, com custo ≈ 87 B.
BYTES_DA_PAGINA_CHEIA = 44000


def pagina_sintetica(rota: str, pares: list[tuple[str, str]],
                     pagina_bytes: int = 42000) -> dict:
    """Uma página como `measure-link-graph.varre_acervo` a devolve.

    Os OITO campos, não só os cinco que o gate lê hoje: se amanhã `mede()`
    passar a olhar `externos` ou `titulo_servido`, o corpus já os tem — que é
    metade da razão de o KeyError ter existido.

    O hash do bloco é calculado do markup, não escrito à mão: a identidade entre
    dois blocos EMERGE de eles terem o mesmo conteúdo, em vez de ser afirmada
    pela fixture."""
    itens = "".join(f'<li><a href="{d}">{a}</a></li>' for d, a in pares)
    bloco = f"<h2>Conteúdos relacionados</h2><ul>{itens}</ul>" if pares else ""
    return {
        "destinos": [d for d, _ in pares],
        "ancoras": [a for _, a in pares],
        "bloco_malha_sha256": hashlib.sha256(bloco.encode("utf-8")).hexdigest() if bloco else "",
        "chrome_ancoras": 0,
        "bloco_bytes": len(bloco.encode("utf-8")),
        "pagina_bytes": pagina_bytes,
        "titulo_servido": TITULOS.get(rota, ""),
        "externos": set(),
    }


def corpus() -> dict:
    t = TITULOS
    return {
        AGRAVO: pagina_sintetica(AGRAVO, [(EMBARGOS, t[EMBARGOS]), (RECURSO, t[RECURSO])]),
        APELACAO: pagina_sintetica(APELACAO, [(EMBARGOS, t[EMBARGOS]), (RECURSO, t[RECURSO])]),
        EMBARGOS: pagina_sintetica(EMBARGOS, [(PRAZOS, t[PRAZOS]), (AGRAVO, t[AGRAVO])]),
        # a única âncora que diverge do manifesto
        RECURSO: pagina_sintetica(RECURSO, [(PRAZOS, "Prazos de processo"), (APELACAO, t[APELACAO])]),
        PRAZOS: pagina_sintetica(PRAZOS, [(AGRAVO, t[AGRAVO]), (APELACAO, t[APELACAO])]),
        CUSTAS: pagina_sintetica(CUSTAS, [], pagina_bytes=30000),
    }


class MedidorSintetico:
    """O medidor real, com a varredura do disco e o manifesto trocados.

    Delega TUDO o que é lógica pura (`area_de`, `pares_doorway`, as constantes)
    ao módulo de verdade: o que se injeta aqui é o dado, não a regra. Trocar a
    regra faria o teste concordar consigo mesmo."""

    def __init__(self, real, paginas: dict, titulos: dict):
        self._real = real
        self._paginas = paginas
        self._titulos = titulos

    def __getattr__(self, nome):
        return getattr(self._real, nome)

    def varre_acervo(self):
        paginas = {r: dict(d) for r, d in self._paginas.items()}
        sem_bloco = [r for r, d in paginas.items() if not d["destinos"]]
        return paginas, sem_bloco

    def carrega_titulos_do_manifesto(self):
        return dict(self._titulos)


def medicao_limpa(m, paginas: dict | None = None) -> dict:
    """A medição do produtor sobre o corpus — não uma cópia dela."""
    return m.mede(MedidorSintetico(m.carrega_medidor(),
                                   corpus() if paginas is None else paginas,
                                   TITULOS))


def baseline_atual(medicao: dict) -> dict:
    """A régua no-worse com os números da própria medição: empatar passa.

    Os quatro caminhos de chave são o schema que `measure-link-graph.main()`
    grava em data/ops/link_graph_baseline.jsonl. Ele é montado inline lá, sem
    função pura a reusar — mesma família do defeito que este arquivo conserta,
    produtor sem seam. Enquanto não houver, `testa_schema_da_baseline_versionada`
    confere os quatro caminhos contra a baseline versionada, que é o artefato que
    o produtor de fato escreveu."""
    return {
        "blocos_byte_identicos": {"grupos": medicao["grupos_byte_identicos"]},
        "ancoras": {"divergentes_do_manifesto": medicao["ancoras_divergentes"]},
        "doorway": {"pares_mesma_area_acima_do_limiar": medicao["doorway_pares"]},
        "cross_area": {"paginas_sem_nenhuma_ponte": medicao["paginas_sem_ponte_cross_area"]},
    }


# As quatro métricas no-worse, na forma (chave da medição, caminho na baseline).
NO_WORSE = [
    ("grupos_byte_identicos", ("blocos_byte_identicos", "grupos"), "byte-idêntico"),
    ("ancoras_divergentes", ("ancoras", "divergentes_do_manifesto"), "ncoras divergentes"),
    ("doorway_pares", ("doorway", "pares_mesma_area_acima_do_limiar"), "doorway"),
    ("paginas_sem_ponte_cross_area", ("cross_area", "paginas_sem_nenhuma_ponte"), "sem ponte cross"),
]


# ───────────────────────────── os casos ──────────────────────────────────────
def testa_corpus_exercita_as_quatro_reguas(m) -> None:
    """CONTROLE POSITIVO, e sem ele o resto não vale nada.

    Um corpus que zerasse as métricas no-worse deixaria "piorar de 0 para 1"
    passar por acidente, e as réguas absolutas nunca seriam exercitadas no estado
    limpo. Aqui se afirma que o corpus está medindo o que o desenho diz — e que
    os exemplos existem, porque exemplo vazio foi exatamente o defeito que fez
    nascer `exemplo_sem_ponte`."""
    a = medicao_limpa(m)

    confere(a["paginas_com_bloco"] == 5,
            f"5 das 6 rotas têm bloco; veio {a['paginas_com_bloco']}")
    confere(a["arestas"] == 10, f"10 arestas no corpus; veio {a['arestas']}")

    for campo, _, _ in NO_WORSE:
        confere(a[campo] > 0,
                f"o corpus tem de exercitar {campo} com valor > 0, veio {a[campo]} — "
                f"régua no-worse sobre zero não prova nada")

    confere(a["grupos_byte_identicos"] == 1 and a["paginas_em_grupo_identico"] == 2,
            f"agravo e apelacao emitem o mesmo bloco: 1 grupo/2 páginas, veio "
            f"{a['grupos_byte_identicos']}/{a['paginas_em_grupo_identico']}")
    confere(a["doorway_pares"] == 1 and a["doorway_paginas"] == 2,
            f"1 par de doorway esperado, veio {a['doorway_pares']}/{a['doorway_paginas']}")
    confere(a["ancoras_divergentes"] == 1,
            f"1 âncora divergente esperada, veio {a['ancoras_divergentes']}")
    confere(a["paginas_sem_ponte_cross_area"] == 2,
            f"2 páginas sem ponte esperadas, veio {a['paginas_sem_ponte_cross_area']}")

    confere(a["exemplo_grupo_identico"] == sorted([AGRAVO, APELACAO]),
            f"exemplo do grupo idêntico veio {a['exemplo_grupo_identico']}")
    confere(a["exemplo_sem_ponte"] == sorted([AGRAVO, APELACAO]),
            f"exemplo sem ponte veio {a['exemplo_sem_ponte']}")
    confere(len(a["exemplos_ancora"]) == 1 and "Prazos de processo" in a["exemplos_ancora"][0],
            f"o exemplo de âncora tem de nomear a divergência, veio {a['exemplos_ancora']}")
    confere(len(a["exemplo_doorway"]) == 1, f"exemplo de doorway veio {a['exemplo_doorway']}")

    confere(all(v == 0 for v in a["absolutos"].values()),
            f"o corpus limpo não pode ter defeito absoluto, veio {a['absolutos']}")
    confere(a["orfas"] == 0, f"o corpus não tem órfã, veio {a['orfas']}")
    confere(a["paginas_acima_do_teto"] == 0, "o corpus não tem página acima do teto")
    confere(0 < a["bloco_bytes_max"] <= m.TETO_BLOCO_BYTES,
            f"bloco máximo fora da faixa útil: {a['bloco_bytes_max']}")
    confere(a["projecao_bloco_bytes_no_teto"] <= m.TETO_BLOCO_BYTES
            and a["projecao_pagina_bytes_no_teto"] <= m.TETO_PAGINA_BYTES,
            f"a projeção do corpus limpo tinha de caber nos tetos: "
            f"{a['projecao_bloco_bytes_no_teto']}B / {a['projecao_pagina_bytes_no_teto']}B")


def testa_empate_passa(m) -> None:
    a = medicao_limpa(m)
    problemas = m.avalia(a, baseline_atual(a))
    confere(problemas == [],
            f"medição igual à baseline deveria passar, veio {problemas}")


def testa_melhora_passa(m) -> None:
    base = baseline_atual(medicao_limpa(m))
    atual = medicao_limpa(m)
    for campo, _, _ in NO_WORSE:
        atual[campo] = 0
    confere(m.avalia(atual, base) == [], "melhorar em tudo não pode reprovar")


def testa_regressao_no_worse_reprova(m) -> None:
    """Cada métrica no-worse reprova sozinha, e a mensagem nomeia qual.

    O pior valor é `medido + 1`, nunca um literal: literal é o que envelhece
    junto com o corpus."""
    base = baseline_atual(medicao_limpa(m))
    for campo, _, trecho in NO_WORSE:
        atual = medicao_limpa(m)
        atual[campo] = atual[campo] + 1
        problemas = m.avalia(atual, base)
        confere(len(problemas) == 1,
                f"piorar {campo} deveria produzir exatamente 1 problema, "
                f"veio {problemas}")
        confere(any(trecho in p for p in problemas),
                f"a mensagem de {campo} deveria nomear a métrica: {problemas}")
        confere(any("PIOROU" in p for p in problemas),
                f"a mensagem de {campo} deveria dizer que PIOROU: {problemas}")


def testa_a_mensagem_de_regressao_nomeia_uma_pagina(m) -> None:
    """A regressão que `exemplo_sem_ponte` fechou em 2026-09-11, agora com teste.

    O campo nasceu porque a comparação passava `[]` como amostra para a linha do
    cross-área e SÓ para ela: o gate reprovava com "PIOROU: 23 -> 160" sem
    nomear uma página sequer, e quem lê decide pelo rótulo. Nenhum teste afirmava
    que o exemplo chega à mensagem — por isso o campo pôde sumir da fixture sem
    ninguém notar. As quatro comparações são cobertas, não só a que quebrou."""
    base = baseline_atual(medicao_limpa(m))
    esperados = {
        "grupos_byte_identicos": AGRAVO,
        "ancoras_divergentes": "Prazos de processo",
        "doorway_pares": AGRAVO,
        "paginas_sem_ponte_cross_area": AGRAVO,
    }
    for campo, _, trecho in NO_WORSE:
        atual = medicao_limpa(m)
        atual[campo] = atual[campo] + 1
        problemas = m.avalia(atual, base)
        alvo = esperados[campo]
        confere(any(alvo in p for p in problemas),
                f"a mensagem de {campo} ({trecho}) tem de trazer o exemplo que "
                f"nomeia a página: esperava {alvo!r} em {problemas}")


def testa_absolutos_reprovam_no_primeiro_caso(m) -> None:
    """Estes são zero no acervo hoje. Um só já é defeito novo — não há régua
    no-worse para eles, de propósito."""
    base = baseline_atual(medicao_limpa(m))
    for chave in ("autolink", "destino_inexistente", "ancora_vazia",
                  "destino_repetido_no_bloco"):
        atual = medicao_limpa(m)
        atual["absolutos"][chave] = 1
        atual["exemplos_absolutos"][chave] = [f"{AGRAVO} -> {APELACAO}"]
        problemas = m.avalia(atual, base)
        confere(any(chave in p for p in problemas),
                f"uma única ocorrência de {chave} deveria reprovar: {problemas}")


def testa_defeito_mecanico_no_corpus_e_medido(m) -> None:
    """A régua absoluta medida do PRODUTOR, não injetada no dicionário.

    Injetar `absolutos["autolink"] = 1` prova a régua do `avalia`; este caso
    prova o passo anterior, que é `mede()` reconhecer o defeito no HTML. Uma
    página que linka para si mesma, repete um destino e usa âncora vazia sai com
    três defeitos e um destino inexistente."""
    paginas = corpus()
    paginas[AGRAVO] = pagina_sintetica(
        AGRAVO, [(AGRAVO, TITULOS[AGRAVO]), (EMBARGOS, ""), (EMBARGOS, TITULOS[EMBARGOS]),
                 ("/jurisprudencia/rota-que-nao-existe/", "Rota que não existe")])
    a = medicao_limpa(m, paginas)
    confere(a["absolutos"]["autolink"] == 1, f"autolink veio {a['absolutos']['autolink']}")
    confere(a["absolutos"]["ancora_vazia"] == 1, f"âncora vazia veio {a['absolutos']['ancora_vazia']}")
    confere(a["absolutos"]["destino_repetido_no_bloco"] == 1,
            f"destino repetido veio {a['absolutos']['destino_repetido_no_bloco']}")
    confere(a["absolutos"]["destino_inexistente"] == 1,
            f"destino inexistente veio {a['absolutos']['destino_inexistente']}")
    problemas = m.avalia(a, baseline_atual(medicao_limpa(m)))
    confere(any("autolink" in p for p in problemas),
            f"o autolink medido tinha de reprovar: {problemas}")


def testa_orfa_e_teto_de_pagina_reprovam(m) -> None:
    base = baseline_atual(medicao_limpa(m))

    atual = medicao_limpa(m)
    atual["orfas"] = 1
    confere(any("órfãs" in p for p in m.avalia(atual, base)),
            "página órfã de malha deveria reprovar — o piso do publicador existe "
            "justamente para impedir isso")

    atual = medicao_limpa(m)
    atual["paginas_acima_do_teto"] = 1
    atual["pagina_bytes_max"] = m.TETO_PAGINA_BYTES + 1000
    confere(any("contrato de indexação" in p for p in m.avalia(atual, base)),
            "página acima de 50 KB deveria reprovar pelo contrato de indexação")

    atual = medicao_limpa(m)
    atual["bloco_bytes_max"] = m.TETO_BLOCO_BYTES + 1
    confere(any("acima do teto" in p for p in m.avalia(atual, base)),
            "bloco acima do teto de bytes deveria reprovar")


def testa_orfa_medida_no_corpus(m) -> None:
    """A órfã vista pelo produtor: uma página com bloco que ninguém linka."""
    paginas = corpus()
    orfa = "/guias/honorarios-advocaticios/"
    paginas[orfa] = pagina_sintetica(orfa, [(AGRAVO, TITULOS[AGRAVO])])
    a = medicao_limpa(m, paginas)
    confere(a["orfas"] == 1, f"a página sem grau de entrada tinha de contar como órfã, veio {a['orfas']}")


def testa_projecao_no_teto_editorial_reprova(m) -> None:
    """A defesa que existe ANTES da publicação, e a única que chega a tempo.

    O gate mede `public/`, que é o acervo já publicado, e o teto novo só chega ao
    disco na PRÓXIMA publicação — medido em 2026-08-29, 10.091 das 10.116 páginas
    servidas ainda tinham 6 links com o teto do código já em 8. Sem esta régua o
    gate aprovaria hoje e reprovaria depois de o acervo estar no ar.
    """
    base = baseline_atual(medicao_limpa(m))

    atual = medicao_limpa(m)
    atual["projecao_bloco_bytes_no_teto"] = m.TETO_BLOCO_BYTES + 1
    problemas = m.avalia(atual, base)
    confere(any("pior bloco chegaria" in p for p in problemas),
            f"projeção de bloco acima do teto deveria reprovar, veio {problemas}")

    atual = medicao_limpa(m)
    atual["projecao_pagina_bytes_no_teto"] = m.TETO_PAGINA_BYTES + 1
    problemas = m.avalia(atual, base)
    confere(any("pior página chegaria" in p for p in problemas),
            f"projeção de página acima do teto deveria reprovar, veio {problemas}")

    # E o caso que importa não regredir: a projeção do corpus limpo passa.
    confere(not any("chegaria" in p for p in m.avalia(medicao_limpa(m), base)),
            "a projeção do corpus limpo tinha de passar")


def testa_projecao_cresce_com_as_vagas(m) -> None:
    """A projeção é POR PÁGINA, sobre as vagas de cada uma — não uma média.

    Uma página já no teto editorial não tem vaga e não projeta nada a mais; uma
    com uma vaga só projeta um link. Sem esta asserção, trocar `faltam` por uma
    constante passaria despercebido."""
    teto = m.teto_editorial_de_links()
    cheia = "/guias/tutela-de-urgencia/"
    paginas = corpus()
    # A página cheia REPETE o mesmo destino até o teto — o corpus só tem seis
    # rotas. Isso lhe dá `destino_repetido_no_bloco` alto, e é irrelevante aqui
    # porque este caso mede a PROJEÇÃO, não `avalia()`: não confunda com o corpus
    # limpo, que é o de `testa_corpus_exercita_as_quatro_reguas`.
    paginas[cheia] = pagina_sintetica(
        cheia, [(AGRAVO, TITULOS[AGRAVO])] + [(EMBARGOS, TITULOS[EMBARGOS])] * (teto - 1),
        pagina_bytes=BYTES_DA_PAGINA_CHEIA)
    a = medicao_limpa(m, paginas)
    custo = a["custo_do_pior_link_bytes"]
    confere(custo > m.MARKUP_POR_ITEM_BYTES,
            f"o custo do pior link tem de somar rota e âncora ao markup, veio {custo}")
    # IGUALDADE EXATA, e é isso que torna a asserção capaz de matar o mutante.
    # A cheia tem ZERO vaga, então projeta o próprio tamanho; as demais projetam
    # 42000 + 6×custo e 30000 + 8×custo, todas abaixo dela por construção. Com
    # `>=` no lugar de `==`, trocar `faltam = teto - len(destinos)` pela
    # constante 6 daria 44000 + 6×custo e passaria — mutante vivo, e a docstring
    # estaria mentindo sobre o que este caso cobre.
    confere(a["projecao_pagina_bytes_no_teto"] == BYTES_DA_PAGINA_CHEIA,
            f"a página no teto editorial não tem vaga: a projeção tinha de ser "
            f"{BYTES_DA_PAGINA_CHEIA}, veio {a['projecao_pagina_bytes_no_teto']}")
    confere(a["teto_editorial_de_links"] == teto,
            "o teto projetado tem de ser o teto lido do Go")


def testa_teto_editorial_vem_do_go(m) -> None:
    """O número é do render, não deste gate: duplicá-lo seria divergir em silêncio."""
    teto = m.teto_editorial_de_links()
    confere(teto >= 1, f"teto editorial lido do Go veio {teto}")
    fonte = open(m.TETO_LINKS_GO, encoding="utf-8").read()
    confere(f"MaxRelatedLinksPerPage = {teto}" in fonte,
            f"o teto {teto} não confere com internal/content/relatedmerge.go")


def testa_baseline_ausente_reprova(m) -> None:
    """Sem régua não há no-worse — e passar em silêncio seria pior que reprovar."""
    problemas = m.avalia(medicao_limpa(m), None)
    confere(any("baseline ausente" in p for p in problemas),
            f"baseline ausente deveria reprovar, veio {problemas}")


def testa_schema_da_baseline_versionada(m) -> None:
    """Os quatro caminhos que `avalia` lê existem na baseline que o produtor grava.

    `baseline_atual()` ainda espelha esse schema à mão porque
    measure-link-graph o monta inline em `main()`, sem função pura a reusar. A
    baseline versionada é o artefato que o produtor de fato escreveu: conferir os
    CAMINHOS contra ela (nunca os valores, que são do acervo e mudam) fecha a
    deriva que sobraria — renomear a chave lá reprova aqui, em vez de derrubar o
    gate em produção."""
    if not os.path.isfile(BASELINE_VERSIONADA):
        confere(False, f"{BASELINE_VERSIONADA} não existe — a régua no-worse do "
                       f"gate ficaria sem schema para conferir")
        return
    with open(BASELINE_VERSIONADA, encoding="utf-8") as fh:
        gravada = json.loads(next(l for l in fh if l.strip()))
    for _, caminho, _ in NO_WORSE:
        no = gravada
        for chave in caminho:
            if not isinstance(no, dict) or chave not in no:
                confere(False, f"a baseline versionada não tem o caminho "
                               f"{'.'.join(caminho)} que check-internal-link-block lê")
                break
            no = no[chave]
        else:
            confere(isinstance(no, int),
                    f"{'.'.join(caminho)} devia ser inteiro na baseline, veio {no!r}")


def main() -> int:
    modulo = carrega()
    testa_corpus_exercita_as_quatro_reguas(modulo)
    testa_empate_passa(modulo)
    testa_melhora_passa(modulo)
    testa_regressao_no_worse_reprova(modulo)
    testa_a_mensagem_de_regressao_nomeia_uma_pagina(modulo)
    testa_absolutos_reprovam_no_primeiro_caso(modulo)
    testa_defeito_mecanico_no_corpus_e_medido(modulo)
    testa_orfa_e_teto_de_pagina_reprovam(modulo)
    testa_orfa_medida_no_corpus(modulo)
    testa_projecao_no_teto_editorial_reprova(modulo)
    testa_projecao_cresce_com_as_vagas(modulo)
    testa_teto_editorial_vem_do_go(modulo)
    testa_baseline_ausente_reprova(modulo)
    testa_schema_da_baseline_versionada(modulo)

    if falhas:
        for f in falhas:
            print(f"FALHA: {f}", file=sys.stderr)
        return 1
    print("test_check_internal_link_block: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
