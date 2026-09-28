#!/usr/bin/env python3
"""test_v2_link_topics_writer — testes da máquina de escrita de internal_link_topics.

POR QUE ELE EXISTE. Em 2026-08-29 a máquina de escrita foi extraída de
`generate-v2-link-topics-enrich-20260812` para `tools/v2_link_topics_writer.py`,
para que o segundo gerador do mesmo tipo (pontes cross-área) não a copiasse. Uma
extração sem teste é uma aposta: o código que ela move escreve no ESTOQUE
CANÔNICO, e a falha dele é silenciosa — um splice que mexe num byte a mais
corrompe a linha e ninguém vê até a página sair errada no ar.

O QUE ELE COBRE, e por que cada caso está aqui:

  - `splice_topicos` preserva o resto da linha BYTE A BYTE, inclusive quando o
    registro mistura formas de serialização (nível de cima com ", " e objetos
    aninhados compactos) — que é o caso real do acervo;
  - o array com `]` DENTRO de uma string não fecha cedo (`_limites_do_array`);
  - `texto_visivel` alcança opening, heading, text, q e a — se ele encolher,
    o preflight passa a aceitar trecho que não está no texto;
  - o preflight RECUSA cada uma das seis formas de par inválido, uma a uma;
  - `aplicar` é idempotente, e um par já presente não reescreve o arquivo;
  - `aplicar` PRESERVA o estado anterior antes de escrever;
  - `--dry-run` não toca no disco.

Nada aqui escreve no acervo real: todo caso roda sobre shard de mentira em
diretório temporário.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from tools.v2_link_topics_writer import (  # noqa: E402
    Destinos,
    _limites_do_array,
    aplicar,
    escrever_evidencia,
    indexar_acervo,
    preflight,
    splice_topicos,
    texto_visivel,
)

falhas: list[str] = []


def confere(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhas.append(mensagem)


TRECHO = "O prazo decadencial para revisar o benefício é de dez anos, contados do primeiro pagamento."


def registro(intent: str, topicos: list[str]) -> str:
    """Linha no formato REAL do acervo: nível de cima espaçado, aninhado compacto."""
    return (
        '{"intent_id": "' + intent + '", "title": "Titulo de ' + intent + '", '
        '"h1": "H1 de ' + intent + '", "opening": "' + TRECHO + '", '
        '"sections": [{"heading":"Uma secao","text":"Texto da secao [com colchete] dentro."}], '
        '"faq": [{"q":"Uma pergunta?","a":"Uma resposta."}], '
        '"internal_link_topics": ' + json.dumps(topicos, ensure_ascii=False) + ', '
        '"lane": "informativa", "word_count": 900}'
    )


def testa_limites_do_array() -> None:
    linha = '{"internal_link_topics": ["a]b", "c"], "depois": 1}'
    abre, fecha = _limites_do_array(linha, linha.index('"internal_link_topics"') + 22)
    confere(json.loads(linha[abre:fecha]) == ["a]b", "c"],
            "array com ] dentro de string fechou cedo")


def testa_splice_preserva_o_resto() -> None:
    linha = registro("pag-a", ["um"])
    nova = splice_topicos(linha, ["um", "dois"])
    antes, depois = json.loads(linha), json.loads(nova)
    confere(depois["internal_link_topics"] == ["um", "dois"], "splice não gravou os tópicos")
    antes.pop("internal_link_topics")
    depois.pop("internal_link_topics")
    confere(antes == depois, "splice alterou campo que não era o dele")
    # A prova textual: fora do array, os bytes têm de ser os mesmos.
    corte = linha.index('"internal_link_topics"')
    confere(linha[:corte] == nova[:corte], "splice mexeu nos bytes ANTES do array")
    confere(linha.endswith('"word_count": 900}') and nova.endswith('"word_count": 900}'),
            "splice mexeu nos bytes DEPOIS do array")


def testa_splice_preserva_array_compacto() -> None:
    linha = '{"intent_id":"x","internal_link_topics":["a"],"lane":"informativa"}'
    nova = splice_topicos(linha, ["a", "b"])
    confere('"internal_link_topics":["a","b"]' in nova,
            f"forma compacta do array não foi preservada: {nova}")


def testa_splice_desempata_array_ambiguo() -> None:
    """Array de 0 ou 1 item não revela a própria forma — quem revela é o vizinho.

    As duas linhas abaixo são as duas formas REAIS medidas no acervo em
    2026-08-29: `imobiliario-p10.jsonl` traz ": " depois da chave e vírgula
    COMPACTA dentro dos arrays (16 linhas), enquanto o resto do estoque usa a
    forma espaçada nos dois lugares. Um desempate que olhasse só o separador da
    chave acertaria a segunda e erraria a primeira.
    """
    compacto = ('{"intent_id": "x", "sections": [{"heading":"a","text":"b"},'
                '{"heading":"c","text":"d"}], "internal_link_topics": ["so-um"], '
                '"lane": "informativa"}')
    confere('"internal_link_topics": ["so-um","dois"]' in splice_topicos(compacto, ["so-um", "dois"]),
            "array ambíguo em linha de vírgula compacta virou forma espaçada")

    espacado = ('{"intent_id": "y", "official_sources": [{"url": "a"}, {"url": "b"}], '
                '"internal_link_topics": ["um"], "lane": "informativa"}')
    confere('"internal_link_topics": ["um", "dois"]' in splice_topicos(espacado, ["um", "dois"]),
            "array ambíguo em linha espaçada virou forma compacta")

    # Array VAZIO é o caso extremo do mesmo problema, e é o mais comum de todos.
    vazio = ('{"intent_id": "z", "sections": [{"heading":"a","text":"b"},'
             '{"heading":"c","text":"d"}], "internal_link_topics": [], "lane": "informativa"}')
    confere('"internal_link_topics": ["a","b"]' in splice_topicos(vazio, ["a", "b"]),
            "array vazio em linha compacta virou forma espaçada")


def testa_texto_visivel_alcanca_tudo() -> None:
    reg = json.loads(registro("pag-a", []))
    texto = texto_visivel(reg)
    for pedaco in (TRECHO, "Uma secao", "Texto da secao", "Uma pergunta?", "Uma resposta."):
        confere(pedaco in texto, f"texto_visivel não alcança {pedaco!r}")


def monta_acervo(diretorio: Path, linhas: list[str]) -> Destinos:
    pages = diretorio / "data/editorial/v2_pages"
    pages.mkdir(parents=True)
    (pages / "shard-01.jsonl").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return Destinos(
        root=diretorio,
        lock=diretorio / "data/editorial/.teste.lock",
        pages=pages,
        backup=diretorio / ".agents/runtime/backup-teste",
        evidencia=diretorio / "data/editorial/evidencia-teste.jsonl",
        gerador="test_v2_link_topics_writer",
    )


def par(intent: str, topico: str, **troca) -> dict:
    base = {
        "intent_id": intent,
        "topico": topico,
        "veredito": "verdadeiro",
        "porque": "as duas páginas tratam do mesmo prazo decadencial",
        "trecho_justificativa": TRECHO,
    }
    base.update(troca)
    return base


def testa_preflight_recusa_o_invalido() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        destinos = monta_acervo(Path(tmp), [registro("pag-a", ["x"]), registro("pag-b", [])])
        onde, registros = indexar_acervo(destinos)
        confere(set(onde) == {"pag-a", "pag-b"}, f"indexar_acervo achou {sorted(onde)}")

        # O caso bom passa.
        por_shard = preflight([par("pag-a", "pag-b")], onde, registros)
        confere(len(por_shard) == 1, "preflight recusou um par válido")

        invalidos = {
            "página inexistente": par("pag-z", "pag-b"),
            "tópico que não é intent_id": par("pag-a", "nao-existe"),
            "auto-referência": par("pag-a", "pag-a"),
            "veredito fraco": par("pag-a", "pag-b", veredito="fraco"),
            "sem razão declarada": par("pag-a", "pag-b", porque=""),
            "trecho curto": par("pag-a", "pag-b", trecho_justificativa="curto"),
            "trecho fora do texto": par(
                "pag-a", "pag-b",
                trecho_justificativa="Uma frase que nunca foi escrita nesta pagina de teste."),
        }
        for nome, item in invalidos.items():
            try:
                preflight([item], onde, registros)
            except SystemExit:
                continue
            falhas.append(f"preflight ACEITOU par inválido: {nome}")

        # Par repetido no mesmo lote também é recusa.
        try:
            preflight([par("pag-a", "pag-b"), par("pag-a", "pag-b")], onde, registros)
            falhas.append("preflight aceitou par repetido no lote")
        except SystemExit:
            pass


def testa_aplicar_idempotente_e_preserva() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        destinos = monta_acervo(raiz, [registro("pag-a", ["x"]), registro("pag-b", [])])
        shard_rel = os.path.relpath(destinos.pages / "shard-01.jsonl", raiz)
        alvo = destinos.pages / "shard-01.jsonl"
        antes = alvo.read_bytes()

        # dry-run não toca no disco.
        alterados, ja = aplicar(destinos, shard_rel, [par("pag-a", "pag-b")], True)
        confere(alterados == 1 and ja == 0, f"dry-run contou {alterados}/{ja}")
        confere(alvo.read_bytes() == antes, "dry-run ESCREVEU no shard")

        alterados, ja = aplicar(destinos, shard_rel, [par("pag-a", "pag-b")], False)
        confere(alterados == 1 and ja == 0, f"escrita real contou {alterados}/{ja}")
        vivo = json.loads(alvo.read_text(encoding="utf-8").splitlines()[0])
        confere(vivo["internal_link_topics"] == ["x", "pag-b"],
                f"tópicos gravados: {vivo['internal_link_topics']}")
        confere(vivo["word_count"] == 900, "word_count foi alterado — não podia")

        # O estado anterior tem de estar recuperável byte a byte.
        preservado = destinos.backup / shard_rel.replace("/", "_")
        confere(preservado.is_file(), "estado anterior NÃO foi preservado")
        if preservado.is_file():
            linha = preservado.read_text(encoding="utf-8").splitlines()[0]
            numero, conteudo = linha.split("\t", 1)
            confere(numero == "1", f"número de linha preservado errado: {numero}")
            confere(conteudo == antes.decode("utf-8").splitlines()[0],
                    "a linha preservada não bate byte a byte com a original")

        # Rodar de novo não muda nada: idempotente.
        depois = alvo.read_bytes()
        alterados, ja = aplicar(destinos, shard_rel, [par("pag-a", "pag-b")], False)
        confere(alterados == 0 and ja == 1, f"segunda passada contou {alterados}/{ja}")
        confere(alvo.read_bytes() == depois, "segunda passada reescreveu o shard")

        onde, _ = indexar_acervo(destinos)
        escrever_evidencia(destinos, [par("pag-a", "pag-b")], onde)
        confere(destinos.evidencia.is_file(), "evidência não foi escrita")
        if destinos.evidencia.is_file():
            reg = json.loads(destinos.evidencia.read_text(encoding="utf-8").splitlines()[0])
            confere(reg["intent_id"] == "pag-a" and reg["topico_acrescentado"] == "pag-b",
                    f"evidência com conteúdo errado: {reg}")
            confere(reg["shard"] == shard_rel, f"evidência com shard errado: {reg['shard']}")


def main() -> int:
    testa_limites_do_array()
    testa_splice_preserva_o_resto()
    testa_splice_preserva_array_compacto()
    testa_splice_desempata_array_ambiguo()
    testa_texto_visivel_alcanca_tudo()
    testa_preflight_recusa_o_invalido()
    testa_aplicar_idempotente_e_preserva()

    if falhas:
        for f in falhas:
            print(f"FALHA: {f}", file=sys.stderr)
        return 1
    print("test_v2_link_topics_writer: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
