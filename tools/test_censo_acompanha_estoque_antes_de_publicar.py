#!/usr/bin/env python3
"""O censo de severidade tem de estar em dia ANTES de o acervo ser republicado.

★ O DEFEITO QUE ESTE TESTE FECHA (medido em 2026-09-16).

`internal/v2publish.SelectPublishable` (v2publish.go:398-402) pula toda página
que não tenha linha no censo, com o motivo `sem_linha_no_censo`. O censo é
derivado dos shards de `data/editorial/v2_pages/`; logo, censo mais velho que
um shard significa que a publicação vai descartar, em silêncio, exatamente o
conteúdo NOVO.

Aconteceu neste repositório, e está no log do próprio deploy
(`.agents/runtime/p1b/deploy4_20260916.log`):

    shard stj-acordao-derivado-01.jsonl  gravado  12:32:25
    censo v2_publication_severity.jsonl  gravado  12:22:53
    publicação                           rodou    ~13:01
    sem_linha_no_censo                             30

As 30 primeiras páginas de acórdão produzidas pela cadeia do cérebro estavam
commitadas, pareadas e corretas — e não foram ao ar. O deploy não parou.

A regra já existia em `tools/check-censo-acompanha-estoque` e o regenerador que
a consulta em `tools/generate-censo-acompanha-estoque`; até 2026-09-16 os dois
tinham ZERO chamadores no repositório. Este teste cobre as duas metades:

  1. a REGRA decide certo (shard mais novo que o censo reprova; censo à frente
     de todos os shards aprova);
  2. a FIAÇÃO existe: `tools/deploy-publico` põe o censo em dia, fail-closed,
     ANTES de chamar `cmd/publish-v2-direct`.

★ PROVA POR MUTAÇÃO, e por que ela está dentro do teste.

Cada asserção é aplicada também a uma CÓPIA mutada do arquivo real, no
diretório temporário — o arquivo do repositório nunca é tocado. Se a asserção
não morre com o mutante, ela não tem dentes e o teste falha dizendo isso.
"""
from __future__ import annotations

import os
import pathlib

import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CHECK = RAIZ / "tools" / "check-censo-acompanha-estoque"
DEPLOY = RAIZ / "tools" / "deploy-publico"

CENSO_REL = "data/editorial/v2_publication_severity.jsonl"
SHARD_REL = "data/editorial/v2_pages/familia-de-teste-01.jsonl"

REGENERADOR = "tools/generate-censo-acompanha-estoque"
PUBLICADOR = "cmd/publish-v2-direct"


def monta_raiz(tmp: pathlib.Path, censo_mais_novo: bool) -> None:
    """Cria a árvore mínima que o check lê, com a ordem de mtime pedida."""
    (tmp / "data" / "editorial" / "v2_pages").mkdir(parents=True)
    censo = tmp / CENSO_REL
    shard = tmp / SHARD_REL
    censo.write_text('{"intent_id":"x","publish":true}\n', encoding="utf-8")
    shard.write_text('{"intent_id":"x"}\n', encoding="utf-8")
    # mtime explícito: o teste não pode depender da resolução do relógio nem da
    # ordem em que o filesystem gravou os dois arquivos.
    if censo_mais_novo:
        os.utime(shard, (1_700_000_000, 1_700_000_000))
        os.utime(censo, (1_700_000_600, 1_700_000_600))
    else:
        os.utime(censo, (1_700_000_000, 1_700_000_000))
        os.utime(shard, (1_700_000_600, 1_700_000_600))


def roda_check(raiz: pathlib.Path, check: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(check)],
        cwd=str(raiz),
        capture_output=True,
        text=True,
        check=False,
    )


def problemas_de_fiacao(texto: str) -> list[str]:
    """Devolve o que falta para o censo ser posto em dia antes de publicar.

    Esta é a asserção sob teste — e é ela que os mutantes precisam matar.
    """
    linhas = texto.splitlines()
    idx_censo = [i for i, linha in enumerate(linhas)
                 if REGENERADOR in linha and not linha.lstrip().startswith("#")]
    idx_publica = [i for i, linha in enumerate(linhas)
                   if PUBLICADOR in linha and not linha.lstrip().startswith("#")]

    problemas: list[str] = []
    if not idx_censo:
        problemas.append(
            f"{DEPLOY.name} nao chama {REGENERADOR}: publicaria com censo velho "
            "e descartaria as paginas novas com sem_linha_no_censo")
        return problemas
    if not idx_publica:
        problemas.append(f"{DEPLOY.name} nao chama {PUBLICADOR}")
        return problemas
    if min(idx_censo) > min(idx_publica):
        problemas.append(
            f"{REGENERADOR} aparece DEPOIS de {PUBLICADOR}: por o censo em dia "
            "depois de publicar nao recupera a pagina que ja foi descartada")
    # Fail-closed: o passo não pode seguir em frente quando o censo não fecha.
    bloco = "\n".join(linhas[min(idx_censo) - 1:min(idx_censo) + 4])
    if "fail " not in bloco:
        problemas.append(
            f"a chamada a {REGENERADOR} nao e fail-closed: sem `fail`, um censo "
            "que nao fecha deixa o deploy publicar assim mesmo")
    return problemas


class RegraDoCenso(unittest.TestCase):
    """A regra: censo atrás de qualquer shard reprova."""

    def test_shard_mais_novo_que_o_censo_reprova(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            monta_raiz(raiz, censo_mais_novo=False)
            saida = roda_check(raiz, CHECK)
            self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
            self.assertIn("CENSO ATRASADO", saida.stderr)
            self.assertIn("sem_linha_no_censo", saida.stderr)

    def test_censo_a_frente_de_todos_os_shards_aprova(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            monta_raiz(raiz, censo_mais_novo=True)
            saida = roda_check(raiz, CHECK)
            self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
            self.assertIn("censo em dia", saida.stdout)

    def test_mutante_que_nunca_ve_shard_atrasado_morre(self):
        """Mutante: a comparação de mtime some. O check passaria sempre."""
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            monta_raiz(raiz, censo_mais_novo=False)
            mutante = raiz / "check-mutante"
            fonte = CHECK.read_text(encoding="utf-8")
            alvo = "if os.path.getmtime(caminho) > censo_em:"
            self.assertIn(alvo, fonte, "a linha mutada nao existe mais no check")
            mutante.write_text(fonte.replace(alvo, "if False:"), encoding="utf-8")
            saida = roda_check(raiz, mutante)
            self.assertEqual(
                saida.returncode, 0,
                "o mutante deveria aprovar tudo; se ele reprova, o teste acima "
                "nao estava medindo a comparacao de mtime")
            # E o teste da regra, aplicado ao mutante, tem de falhar.
            self.assertNotIn("CENSO ATRASADO", saida.stderr)


class FiacaoDoDeploy(unittest.TestCase):
    """A fiação: o deploy põe o censo em dia antes de republicar."""

    def test_deploy_publico_poe_o_censo_em_dia_antes_de_publicar(self):
        problemas = problemas_de_fiacao(DEPLOY.read_text(encoding="utf-8"))
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_mutante_sem_o_passo_do_censo_morre(self):
        texto = DEPLOY.read_text(encoding="utf-8")
        mutado = "\n".join(
            linha for linha in texto.splitlines()
            if not (REGENERADOR in linha and not linha.lstrip().startswith("#")))
        self.assertNotEqual(mutado, texto, "a mutacao nao mudou nada")
        problemas = problemas_de_fiacao(mutado)
        self.assertTrue(problemas, "apagar o passo do censo passou despercebido")
        self.assertIn("nao chama", problemas[0])

    def test_mutante_com_o_censo_depois_da_publicacao_morre(self):
        linhas = DEPLOY.read_text(encoding="utf-8").splitlines()
        idx_censo = next(i for i, linha in enumerate(linhas)
                         if REGENERADOR in linha and not linha.lstrip().startswith("#"))
        idx_publica = next(i for i, linha in enumerate(linhas)
                           if PUBLICADOR in linha and not linha.lstrip().startswith("#"))
        movida = linhas.pop(idx_censo)
        linhas.insert(idx_publica + 1, movida)
        problemas = problemas_de_fiacao("\n".join(linhas))
        self.assertTrue(problemas, "censo depois da publicacao passou despercebido")
        self.assertIn("DEPOIS", problemas[0])

    def test_mutante_que_engole_a_falha_do_censo_morre(self):
        texto = DEPLOY.read_text(encoding="utf-8")
        linhas = texto.splitlines()
        idx = next(i for i, linha in enumerate(linhas)
                   if REGENERADOR in linha and not linha.lstrip().startswith("#"))
        # Mutante: a chamada vira best-effort e o `fail` do bloco some.
        linhas[idx] = "\tnice -n 19 ./tools/generate-censo-acompanha-estoque || true"
        for deslocamento in range(1, 4):
            if idx + deslocamento < len(linhas) and "fail " in linhas[idx + deslocamento]:
                linhas[idx + deslocamento] = "\t\t:"
        problemas = problemas_de_fiacao("\n".join(linhas))
        self.assertTrue(problemas, "censo best-effort passou despercebido")
        self.assertIn("fail-closed", problemas[0])


class DonoUnicoDaRegra(unittest.TestCase):
    """Uma regra, um dono: quem precisa dela CONSULTA, não reimplementa.

    Até 2026-09-16 a mesma comparação de mtime vivia em três estados:
    `check-censo-acompanha-estoque` (o dono, com ZERO chamadores),
    `tools/publicar:110` (cópia própria) e `tools/deploy-publico` (nenhuma
    cópia — e por isso publicou 30 páginas a menos sem parar).
    """

    def test_o_regenerador_consulta_o_check(self):
        fonte = (RAIZ / "tools" / "generate-censo-acompanha-estoque").read_text(encoding="utf-8")
        self.assertIn("check-censo-acompanha-estoque", fonte)

    def test_publicar_consulta_o_check_em_vez_de_recalcular(self):
        fonte = (RAIZ / "tools" / "publicar").read_text(encoding="utf-8")
        self.assertIn("tools/check-censo-acompanha-estoque", fonte)
        corpo = fonte.split("def censo_em_dia", 1)[1].split("\ndef ", 1)[0]
        self.assertNotIn("os.path.getmtime", corpo,
                         "tools/publicar voltou a reimplementar a comparacao de mtime")

    def test_mutante_que_recalcula_em_publicar_morre(self):
        fonte = (RAIZ / "tools" / "publicar").read_text(encoding="utf-8")
        cabeca, corpo = fonte.split("def censo_em_dia", 1)
        mutado = cabeca + "def censo_em_dia" + corpo.replace(
            'conferencia = roda([sys.executable, "tools/check-censo-acompanha-estoque"])',
            "censo_em = os.path.getmtime(os.path.join(RAIZ, CENSO))", 1)
        self.assertNotEqual(mutado, fonte, "a mutacao nao mudou nada")
        corpo_mutado = mutado.split("def censo_em_dia", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("os.path.getmtime", corpo_mutado,
                      "o mutante deveria reintroduzir o calculo proprio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
