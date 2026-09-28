#!/usr/bin/env python3
"""test_check_caracteres_de_controle — prova por MUTAÇÃO o gate do byte invisível.

POR QUE ESTE TESTE EXISTE (2026-09-10). O defeito de origem está em
`internal/legalfacts/norma.go`: uma regex dentro de crase (raw string, onde o Go
não interpreta escape) com um byte 0x08 LITERAL entre `(?i)` e `arts`. A regex
passou a exigir um backspace antes de "arts." e casou ZERO vezes desde
2026-09-06 — 557 das 1.144 ocorrências plurais do acervo deixaram de virar fato
de artigo.

Ele sobreviveu a TODO instrumento do repositório: compila, passa no gofmt,
passa no go vet, é invisível no diff — e o teste que o cobriria foi escrito com
o MESMO byte no dado de entrada, então ficou verde provando nada. É por isso
que aqui a prova é por MUTAÇÃO e não por asserção de saída: o par
"com o byte reprova / sem o byte passa" é a única forma de mostrar que o gate
enxerga o byte, e não o arquivo.

Cada caso monta um repositório git de mentira em `tmp_path` e roda o gate REAL
como subprocesso. Nada é escrito dentro de /opt/wiki, e nenhuma linha do gate é
reimplementada aqui — gate testado por gêmeo em outra linguagem é gate não
testado.

O `-p no:cacheprovider` não é enfeite: sem ele o pytest cria `.pytest_cache/`
na raiz do repositório a cada execução. Um teste de ferramenta READ-ONLY que
deixa rastro no repo que audita contradiz o próprio contrato.

Uso:
    python3 tools/test_check_caracteres_de_controle.py
    python3 -m pytest tools/test_check_caracteres_de_controle.py -q -p no:cacheprovider
"""

from __future__ import annotations

import os
import pathlib
import subprocess

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-caracteres-de-controle"

# O literal do defeito real, reconstruído byte a byte. `\x08` aqui é escape do
# Python: o que vai para o disco é o byte 0x08 sozinho, exatamente como estava
# na crase do norma.go.
REGEX_ENVENENADA = (
    b"package legalfacts\n"
    b"\n"
    b"var reArtigosPlurais = regexp.MustCompile(`(?i)\x08arts?\\.\\s*(\\d+)`)\n"
)
REGEX_SA = REGEX_ENVENENADA.replace(b"\x08", b"")


def monta_repo(tmp_path, arquivos: dict, nao_versionados: dict = None):
    """Repositório git com os arquivos indexados; devolve a raiz.

    `nao_versionados` fica no disco e FORA do índice — é assim que se prova que
    a varredura sai de `git ls-files` e não da árvore.
    """
    raiz = pathlib.Path(tmp_path) / "repo"
    raiz.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(raiz)], check=True)
    for nome, conteudo in arquivos.items():
        destino = raiz / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        subprocess.run(["git", "-C", str(raiz), "add", "-f", nome], check=True)
    for nome, conteudo in (nao_versionados or {}).items():
        destino = raiz / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
    return raiz


def roda(raiz, *extra):
    proc = subprocess.run(
        [str(GATE), "--raiz", str(raiz), *extra],
        capture_output=True,
        timeout=120,
    )
    return proc.returncode, proc.stdout, proc.stderr


def texto(saida: bytes) -> str:
    return saida.decode("utf-8", "replace")


# ---------------------------------------------------------------- a mutação --


def test_o_byte_0x08_na_crase_reprova(tmp_path):
    """O caso de origem: com o byte, exit 1, e a mensagem localiza a linha."""
    raiz = monta_repo(tmp_path, {"internal/legalfacts/norma.go": REGEX_ENVENENADA})
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 1, saida
    assert "internal/legalfacts/norma.go:3" in saida, saida
    assert "0x08" in saida and "backspace" in saida, saida


def test_o_mesmo_arquivo_sem_o_byte_passa(tmp_path):
    """A OUTRA metade da mutação: só o byte muda, e o veredito inverte.

    Sem este par, um gate que reprovasse todo arquivo .go passaria no teste
    acima sem enxergar byte nenhum.
    """
    raiz = monta_repo(tmp_path, {"internal/legalfacts/norma.go": REGEX_SA})
    codigo, out, _ = roda(raiz)
    assert codigo == 0, texto(out)
    assert "zero byte de controle" in texto(out)


def test_a_saida_nunca_imprime_o_byte_cru(tmp_path):
    """0x08 impresso cru APAGARIA o caractere anterior da própria mensagem.

    O gate morreria da doença que diagnostica: o marcador sumiria da tela de
    quem lê. O contexto tem de sair escapado, com o byte marcado.
    """
    raiz = monta_repo(tmp_path, {"internal/legalfacts/norma.go": REGEX_ENVENENADA})
    _, out, _ = roda(raiz)
    assert b"\x08" not in out, "o gate imprimiu o byte cru na saída"
    assert "«0x08»" in texto(out), texto(out)
    assert "(?i)«0x08»arts" in texto(out), texto(out)

    # E o caso que aperta de verdade: o byte VIZINHO, que cai dentro da mesma
    # janela de contexto e não é o marcado. Com um só byte por linha a saída
    # sai limpa mesmo sem escape nenhum — foi assim que a primeira versão deste
    # teste deixou passar a mutação que desligava o escape.
    linha = b"seq \x1b[32mok\x1b[0m fim\n"
    outra = monta_repo(tmp_path / "vizinho", {".agents/runtime/deploy.log": linha})
    codigo, out2, _ = roda(outra)
    assert codigo == 1, texto(out2)
    assert b"\x1b" not in out2, "o gate imprimiu a sequência ANSI crua na saída"
    assert "seq «0x1b»[32mok\\x1b[0m fim" in texto(out2), texto(out2)


# ------------------------------------------------------- o que NÃO reprova --


def test_tab_e_quebra_de_linha_nao_disparam(tmp_path):
    """0x09 e 0x0a são separadores legítimos: um Go indentado com tab passa."""
    fonte = b"package render\n\nfunc Monta() string {\n\treturn \"ok\"\n}\n"
    raiz = monta_repo(
        tmp_path,
        {
            "internal/render/render.go": fonte,
            "content/site.json": b'{\n\t"url": "https://wikijuridica.com.br"\n}\n',
            "ops/nginx/wikijuridica.conf": b"server {\n\tlisten 8088;\n}\n",
        },
    )
    codigo, out, _ = roda(raiz)
    assert codigo == 0, texto(out)
    assert "3 arquivos versionados varridos" in texto(out), texto(out)


def test_arquivo_inteiro_em_crlf_passa(tmp_path):
    """CR emparelhado no arquivo INTEIRO é convenção de plataforma.

    Caso real: `data/ops/bing_webmaster_fora_do_indice_20260908.csv`, export do
    Bing Webmaster com 22 CR, 22 LF e 22 CRLF — nada a consertar ali.
    """
    raiz = monta_repo(tmp_path, {"data/ops/export.csv": b"url,estado\r\n/a,ok\r\n"})
    codigo, out, _ = roda(raiz)
    assert codigo == 0, texto(out)


def test_cr_solto_reprova(tmp_path):
    """Finais de linha MISTOS reprovam, e é a contraparte da regra de cima.

    Um CR sozinho devolve o cursor ao início da linha no terminal: tem o mesmo
    poder de esconder texto que o 0x08 teve na regex.
    """
    raiz = monta_repo(tmp_path, {"ops/systemd/wiki.service": b"[Unit]\r\nExec=/bin/x\n"})
    codigo, out, _ = roda(raiz)
    assert codigo == 1, texto(out)
    assert "0x0d" in texto(out), texto(out)


def test_binario_na_lista_de_extensoes_e_pulado_e_a_lista_aparece(tmp_path):
    """PNG com 0x08 não reprova — e a saída DECLARA o buraco da varredura.

    Varredura parcial que se apresenta como completa é o defeito que este gate
    existe para combater: a lista e a contagem do que foi pulado saem sempre.
    """
    png = b"\x89PNG\r\n\x1a\n" + b"\x08\x00\x01" * 20
    raiz = monta_repo(tmp_path, {"internal/siteicon/favicon.png": png})
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 0, saida
    assert "EXTENSÃO BINÁRIA DECLARADA" in saida, saida
    assert "1 .png" in saida, saida
    assert "0 arquivos versionados varridos" in saida, saida


def test_arquivo_nao_versionado_e_ignorado(tmp_path):
    """A varredura sai de `git ls-files`, nunca da árvore.

    A raiz do /opt/wiki tem centenas de clones não-versionados somando dezenas
    de GB: varrer a árvore é a armadilha que este teste tranca.
    """
    raiz = monta_repo(
        tmp_path,
        {"internal/render/render.go": b"package render\n"},
        nao_versionados={"clone-alheio/regex.go": REGEX_ENVENENADA},
    )
    codigo, out, _ = roda(raiz)
    assert codigo == 0, texto(out)
    assert "clone-alheio" not in texto(out), texto(out)


def test_symlink_versionado_nao_arrasta_a_varredura_para_fora(tmp_path):
    """Modo 120000 é pulado e CONTADO: seguir levaria a varredura para fora."""
    fora = tmp_path / "fora.go"
    fora.write_bytes(REGEX_ENVENENADA)
    raiz = monta_repo(tmp_path, {"internal/render/render.go": b"package render\n"})
    os.symlink(str(fora), str(raiz / "atalho.go"))
    subprocess.run(["git", "-C", str(raiz), "add", "atalho.go"], check=True)
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 0, saida
    assert "por modo do índice" in saida, saida
    assert "120000" in saida, saida


# ------------------------------------------------------------- as arestas --


def test_todo_byte_c0_proibido_e_visto(tmp_path):
    """A família inteira, não o caso: 0x00-0x08, 0x0b, 0x0c e 0x0e-0x1f."""
    proibidos = list(range(0x00, 0x09)) + [0x0B, 0x0C] + list(range(0x0E, 0x20))
    for byte in proibidos:
        arquivo = b"linha um\nvalor: x" + bytes([byte]) + b"y\n"
        raiz = monta_repo(tmp_path / ("b%02x" % byte), {"tools/config.json": arquivo})
        codigo, out, _ = roda(raiz)
        saida = texto(out)
        assert codigo == 1, "byte 0x%02x passou: %s" % (byte, saida)
        assert "0x%02x" % byte in saida, saida
        assert "tools/config.json:2" in saida, saida


def test_limite_por_arquivo_resume_o_resto(tmp_path):
    """Log corrompido não pode inundar a saída — e o resto tem de ser contado."""
    linhas = b"".join(b"passo %d \x1b[32mok\x1b[0m\n" % i for i in range(40))
    raiz = monta_repo(tmp_path, {".agents/runtime/deploy.log": linhas})
    codigo, out, _ = roda(raiz, "--limite-por-arquivo", "3")
    saida = texto(out)
    assert codigo == 1, saida
    assert saida.count("FAIL .agents/runtime/deploy.log") == 3, saida
    assert "e mais 77 ocorrência(s)" in saida, saida
    assert "80 byte(s) de controle" in saida, saida


def test_contexto_mostra_quarenta_caracteres_em_volta(tmp_path):
    """Caminho, linha, hexa e ~40 caracteres de contexto — o contrato da saída."""
    corpo = b"a" * 30 + b"\x0c" + b"b" * 30 + b"\n"
    raiz = monta_repo(tmp_path, {"docs/nota.md": b"cabecalho\n" + corpo})
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 1, saida
    assert "docs/nota.md:2" in saida, saida
    assert ("a" * 20) + "«0x0c»" + ("b" * 20) in saida, saida
    assert "quebra de página" in saida, saida


def test_byte_na_fronteira_do_pedaco_de_leitura(tmp_path):
    """1 MiB é o pedaço de leitura: o byte exatamente na emenda tem de aparecer.

    Sem a cauda do pedaço anterior, o contexto viria truncado e a contagem de
    linha poderia se perder na emenda — defeito que só aparece em arquivo
    grande, que é onde ninguém olha.
    """
    enchimento = (b"x" * 99 + b"\n") * 10486  # ~1,05 MiB, 10.486 linhas
    corpo = enchimento + b"antes\x08depois\n"
    assert len(enchimento) > (1 << 20)
    raiz = monta_repo(tmp_path, {"data/editorial/grande.jsonl": corpo})
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 1, saida
    assert "data/editorial/grande.jsonl:10487" in saida, saida
    assert "antes«0x08»depois" in saida, saida


def test_cr_na_fronteira_do_pedaco(tmp_path):
    """A mesma emenda de 1 MiB, agora no caminho do CR.

    Este caso nasceu de uma MUTAÇÃO que sobreviveu: trocar `cauda + pedaco` por
    `pedaco` no ramo do CR não quebrou teste nenhum, porque todo arquivo com CR
    aqui era pequeno demais para ter emenda. Ramo sem teste é ramo que não
    existe — e são dois ramos, não um.
    """
    enchimento = (b"x" * 99 + b"\n") * 10486  # ~1,05 MiB, 10.486 linhas
    corpo = enchimento + b"antes\rdepois\n"
    raiz = monta_repo(tmp_path, {".agents/runtime/captura.htm": corpo})
    codigo, out, _ = roda(raiz)
    saida = texto(out)
    assert codigo == 1, saida
    assert ".agents/runtime/captura.htm:10487" in saida, saida
    assert "antes«0x0d»depois" in saida, saida



# ---------------------------------------------------------------------------
# DECLARAÇÃO POR CONTEÚDO — os três casos que separam "declarar" de "mascarar"
# ---------------------------------------------------------------------------
#
# A exceção do gate não é por caminho: é uma linha com sha256 e contagem de
# bytes. Os três testes abaixo provam as três consequências disso, e o que cada
# um mata é uma forma diferente de a exceção virar buraco.


def declara(raiz, registros):
    """Escreve data/ops/caracteres_de_controle_declarados.jsonl no repo de teste."""
    import json

    destino = raiz / "data" / "ops" / "caracteres_de_controle_declarados.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in registros),
        encoding="utf-8",
    )


def sha256(conteudo: bytes) -> str:
    import hashlib

    return hashlib.sha256(conteudo).hexdigest()


def test_arquivo_declarado_com_hash_e_contagem_certos_passa(tmp_path):
    """★ A CAPTURA QUE NÃO PODE SER LIMPA SAI DO VERMELHO — E SÓ ELA.

    O segundo arquivo do repositório tem o MESMO byte e NÃO está declarado: o
    gate tem de continuar reprovando por ele. Sem esse par, uma declaração que
    isentasse o repositório inteiro passaria neste teste."""
    sujo = b"saida do deploy\x1b[32m ok\n"
    raiz = monta_repo(
        tmp_path,
        {".agents/runtime/deploy.log": sujo, "internal/codigo.go": sujo},
    )
    declara(
        raiz,
        [{"caminho": ".agents/runtime/deploy.log", "sha256": sha256(sujo), "duros": 1,
          "crs": 0, "motivo": "captura literal do terminal de um deploy real",
          "declarado_em": "2026-09-10"}],
    )
    codigo, out, err = roda(raiz)
    saida = texto(out) + texto(err)
    assert codigo == 1, saida
    assert "internal/codigo.go:1" in saida, saida
    assert "DECLARADO" in saida, saida

    # Agora os dois declarados: o gate passa, e diz quantos declarou.
    declara(
        raiz,
        [{"caminho": ".agents/runtime/deploy.log", "sha256": sha256(sujo), "duros": 1,
          "crs": 0, "motivo": "captura literal do terminal de um deploy real",
          "declarado_em": "2026-09-10"},
         {"caminho": "internal/codigo.go", "sha256": sha256(sujo), "duros": 1,
          "crs": 0, "motivo": "segundo caso do par, so para este teste",
          "declarado_em": "2026-09-10"}],
    )
    codigo, out, err = roda(raiz)
    saida = texto(out) + texto(err)
    assert codigo == 0, saida
    assert "fora dos 2 declarados" in saida, saida


def test_declaracao_com_hash_velho_reprova(tmp_path):
    """★ MUDOU O CONTEÚDO, A DECLARAÇÃO MORRE.

    É o que impede a exceção de virar cobertor: um byte novo entra no arquivo
    declarado e o gate reprova em vez de continuar aceitando o caminho."""
    corpo = b"saida do deploy\x1b[32m ok\n"
    raiz = monta_repo(tmp_path, {".agents/runtime/deploy.log": corpo})
    declara(
        raiz,
        [{"caminho": ".agents/runtime/deploy.log", "sha256": "0" * 64, "duros": 1,
          "crs": 0, "motivo": "captura literal do terminal", "declarado_em": "2026-09-10"}],
    )
    codigo, out, err = roda(raiz)
    saida = texto(out) + texto(err)
    assert codigo == 1, saida
    assert "DECLARAÇÃO VENCIDA" in saida, saida


def test_declaracao_de_arquivo_ja_limpo_reprova(tmp_path):
    """★ EXCEÇÃO MORTA É MENTIRA QUE NINGUÉM COBRA.

    Declaração que não descreve mais nada no disco reprova, para a lista não
    acumular permissão de que ninguém se lembra."""
    raiz = monta_repo(tmp_path, {"internal/limpo.go": b"package limpo\n"})
    declara(
        raiz,
        [{"caminho": "internal/limpo.go", "sha256": "a" * 64, "duros": 1, "crs": 0,
          "motivo": "sobra de uma limpeza anterior", "declarado_em": "2026-09-10"}],
    )
    codigo, out, err = roda(raiz)
    saida = texto(out) + texto(err)
    assert codigo == 1, saida
    assert "DECLARAÇÃO ÓRFÃ" in saida, saida


def test_declaracao_corrompida_erra_em_vez_de_virar_lista_vazia(tmp_path):
    """JSONL ilegível vira exit 2, nunca 'zero exceção declarada' em silêncio."""
    raiz = monta_repo(tmp_path, {"internal/limpo.go": b"package limpo\n"})
    destino = raiz / "data" / "ops" / "caracteres_de_controle_declarados.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text('{"caminho": "x", "sha256"\n', encoding="utf-8")
    codigo, out, err = roda(raiz)
    saida = texto(out) + texto(err)
    assert codigo == 2, saida
    assert "nao e' JSON" in saida, saida


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
