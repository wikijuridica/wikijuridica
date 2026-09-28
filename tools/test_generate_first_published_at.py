#!/usr/bin/env python3
"""Bancada de tools/generate-first-published-at.

POR QUE ELA EXISTE (P1b, 2026-09-16). O gerador era ORFAO — nenhum runner, timer
ou hook o chamava — e tambem nao tinha teste. Quando a onda passou a executa-lo
(`tools/run-daily-content`, etapa 7.95/9), ele deixou de ser uma ferramenta que
alguem roda a mao e virou produtor automatico de dado permanente: a partir dai,
uma data errada que ele grave e congelada por "primeiro vence" e servida no
`publicado_em` de `/api/v1` e no `datePublished` do JSON-LD.

As quatro regras que estas asserções travam, cada uma com o caso real que a
originou:

  1. a estreia sai da evidencia datada MAIS ANTIGA, e nao de uma fonte so;
  2. o registro de revisao de conteudo e TETO (rota datada ali ja estava no ar),
     nunca piso — foi ele que fechou 67 das 75 rotas que o git nao alcancava;
  3. entrada existente cede para TRAS e nunca para frente;
  4. commit ilegivel e linha corrompida nao podem interromper a recuperacao.

O gerador e um script sem extensao `.py`, entao se carrega por caminho.
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_DO_GERADOR = os.path.join(RAIZ, "tools", "generate-first-published-at")


def carrega_gerador():
    especificacao = importlib.util.spec_from_loader(
        "gerador_first_published",
        importlib.machinery.SourceFileLoader("gerador_first_published", CAMINHO_DO_GERADOR),
    )
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


GERADOR = carrega_gerador()


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def escreve(repo: str, relativo: str, conteudo: str) -> None:
    caminho = os.path.join(repo, relativo)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)


def linha_do_manifesto(uid: str, rota: str) -> str:
    return json.dumps({"unique_intent_id": uid, "path": rota}, ensure_ascii=False)


def linha_de_revisao(rota: str, carimbo: str) -> str:
    return json.dumps({"path": rota, "content_sha256": "0" * 64, "revised_on": carimbo},
                      ensure_ascii=False)


class RepoDeTeste:
    """Repositorio git real e minusculo: o gerador le `git log` e `git show`, e
    um dublê de git nao provaria que ele le o historico de verdade.

    O diretorio se apaga no fim do caso (`addCleanup` do chamador): dez repos
    por passada, deixados para tras, viram lixo em /tmp que ninguem atribui a
    esta bancada.
    """

    def __init__(self, caso: unittest.TestCase) -> None:
        self.temporario = tempfile.TemporaryDirectory(prefix="estreia-teste-")
        caso.addCleanup(self.temporario.cleanup)
        self.dir = self.temporario.name
        git(self.dir, "init", "-q", "-b", "main")
        git(self.dir, "config", "user.email", "bancada@wikijuridica.local")
        git(self.dir, "config", "user.name", "bancada")

    def commita_manifesto(self, linhas: list[str], data: str) -> None:
        escreve(self.dir, GERADOR.MANIFESTO, "\n".join(linhas) + "\n")
        git(self.dir, "add", GERADOR.MANIFESTO)
        env = os.environ.copy()
        instante = f"{data}T12:00:00-03:00"
        env["GIT_AUTHOR_DATE"] = instante
        env["GIT_COMMITTER_DATE"] = instante
        # `--allow-empty`: a republicacao que nao muda um byte do manifesto e
        # justamente o caso que o teste da idempotencia precisa exercer, e o git
        # recusaria o commit sem isto.
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", f"manifesto {data}"],
                       cwd=self.dir, check=True, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def grava_revisoes(self, linhas: list[str]) -> None:
        escreve(self.dir, GERADOR.REVISOES, "\n".join(linhas) + "\n")

    def grava_manifesto_sem_commitar(self, linhas: list[str]) -> None:
        escreve(self.dir, GERADOR.MANIFESTO, "\n".join(linhas) + "\n")

    def gera(self, argv: list[str] | None = None) -> dict:
        saida = os.path.join(self.dir, GERADOR.SAIDA)
        anterior = sys.argv
        cwd = os.getcwd()
        relatorio = io.StringIO()
        try:
            os.chdir(self.dir)
            sys.argv = ["generate-first-published-at", *(argv or [])]
            # O relatorio do gerador vai para um buffer: a bancada mede o
            # ARQUIVO, e dez relatorios completos no stdout escondem a falha.
            with contextlib.redirect_stdout(relatorio):
                codigo = GERADOR.main()
        finally:
            sys.argv = anterior
            os.chdir(cwd)
        if codigo != 0:
            raise AssertionError(f"gerador saiu com {codigo}")
        with open(saida, encoding="utf-8") as arquivo:
            return json.load(arquivo)["first_published_at"]


class TestEstreiaPelaEvidenciaMaisAntiga(unittest.TestCase):
    def test_data_do_commit_recupera_a_estreia(self):
        """A metade que ja existia: sem ela, um gerador que nao lesse o git
        passaria pelas assercoes de teto."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-08-06")
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/"),
                                linha_do_manifesto("b", "/leis/b/")], "2026-08-20")
        estreias = repo.gera()
        self.assertEqual(estreias["a"], "2026-08-06")
        self.assertEqual(estreias["b"], "2026-08-20")

    def test_republicacao_nao_reescreve_a_estreia(self):
        """`a` aparece nos dois commits; a PRIMEIRA vez vence."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-08-06")
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-09-16")
        self.assertEqual(repo.gera()["a"], "2026-08-06")

    def test_revisao_fecha_rota_que_o_git_nao_alcanca(self):
        """As 67 de 2026-09-16: publicadas, mas o manifesto nao foi commitado
        desde 09-10, entao o git nao tem evidencia nenhuma delas."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-09-10")
        repo.grava_manifesto_sem_commitar([linha_do_manifesto("a", "/leis/a/"),
                                           linha_do_manifesto("nova", "/leis/nova/")])
        repo.grava_revisoes([linha_de_revisao("/leis/nova/", "2026-09-12")])
        estreias = repo.gera()
        self.assertEqual(estreias["nova"], "2026-09-12",
                         "rota sem commit tem de entrar pela revisao de conteudo")

    def test_revisao_anterior_corrige_registro_tarde_demais(self):
        """As 7 medidas em 2026-09-16: o commit do manifesto e posterior a data
        em que a rota ja estava em content/pages.json."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/jurisprudencia/a/")], "2026-09-05")
        repo.grava_revisoes([linha_de_revisao("/jurisprudencia/a/", "2026-09-02")])
        self.assertEqual(repo.gera()["a"], "2026-09-02")

    def test_revisao_posterior_nao_empurra_a_estreia_para_frente(self):
        """A garantia que impede o registro de virar o novo carimbo mentiroso:
        pagina publicada em agosto e revisada em setembro estreia em AGOSTO."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-08-06")
        repo.grava_revisoes([linha_de_revisao("/leis/a/", "2026-09-10T15:57:56Z")])
        self.assertEqual(repo.gera()["a"], "2026-08-06")

    def test_carimbo_com_instante_vira_dia(self):
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-09-16")
        repo.grava_revisoes([linha_de_revisao("/leis/a/", "2026-09-13T15:25:13Z")])
        self.assertEqual(repo.gera()["a"], "2026-09-13")

    def test_entrada_ja_registrada_so_cede_para_tras(self):
        """Idempotencia com uma direcao: 2026-08-06 no disco nao vira 09-16."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/"),
                                linha_do_manifesto("b", "/leis/b/")], "2026-09-16")
        escreve(repo.dir, GERADOR.SAIDA, json.dumps({
            "schema_version": "first_published_at_v1",
            "first_published_at": {"a": "2026-08-06", "b": "2026-09-16"},
        }, ensure_ascii=False))
        repo.grava_revisoes([linha_de_revisao("/leis/b/", "2026-09-11")])
        estreias = repo.gera()
        self.assertEqual(estreias["a"], "2026-08-06", "nao se empurra estreia para frente")
        self.assertEqual(estreias["b"], "2026-09-11", "evidencia mais antiga corrige para tras")

    def test_linha_corrompida_no_ledger_de_revisao_nao_derruba_a_passada(self):
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-09-10")
        repo.grava_revisoes(["{isto nao e json}",
                             linha_de_revisao("/leis/a/", "2026-09-08")])
        self.assertEqual(repo.gera()["a"], "2026-09-08")

    def test_ausencia_do_ledger_de_revisao_devolve_o_comportamento_anterior(self):
        """Falta de artefato nunca trava: sem o ledger, vale a data do commit."""
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-08-13")
        self.assertEqual(repo.gera()["a"], "2026-08-13")

    def test_dry_run_nao_grava(self):
        repo = RepoDeTeste(self)
        repo.commita_manifesto([linha_do_manifesto("a", "/leis/a/")], "2026-08-06")
        cwd = os.getcwd()
        anterior = sys.argv
        try:
            os.chdir(repo.dir)
            sys.argv = ["generate-first-published-at", "--dry-run"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(GERADOR.main(), 0)
        finally:
            sys.argv = anterior
            os.chdir(cwd)
        self.assertFalse(os.path.exists(os.path.join(repo.dir, GERADOR.SAIDA)),
                         "--dry-run nao pode gravar")


if __name__ == "__main__":
    unittest.main(verbosity=2)
