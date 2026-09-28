#!/usr/bin/env python3
"""Bancada de tools/generate-rascunhos-perdidos-recuperaveis.

O indice existe para o §8 ("pagina escrita nunca e descartada"), entao os casos
que importam sao os de FRONTEIRA do conjunto, e nao a contagem: rascunho que
saiu e cuja pagina continua publicada ENTRA; rascunho que saiu e cuja pagina nao
esta publicada FICA DE FORA; rascunho que continua no arquivo nunca entra.

Cada caso monta um repositorio git de verdade, com historico de verdade, porque
a ferramenta le `git show` — um dublê de arquivo nao exercitaria o caminho real.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-rascunhos-perdidos-recuperaveis"
RASCUNHOS = "data/editorial/authorial_mass_drafts.jsonl"
MANIFESTO = "data/editorial/published_manifest.jsonl"
SAIDA = "data/editorial/rascunhos_perdidos_recuperaveis.jsonl"


def rascunho(intent: str, palavras: int = 10) -> str:
    return json.dumps({
        "unique_intent_id": intent,
        "draft_id": "authorial-mass-draft-v2-" + intent,
        "public_path": "",   # em producao o rascunho nasce bloqueado e sem rota
        "page_type": "verbete",
        "practice_area": "x",
        "body_sections": [{"heading": "h", "text": " ".join(["palavra"] * palavras)}],
    }, ensure_ascii=False, separators=(",", ":"))


class Repositorio:
    def __init__(self, base: Path):
        self.raiz = base
        (self.raiz / "data" / "editorial").mkdir(parents=True)
        self.git("init", "-q")
        self.git("config", "user.email", "bancada@local")
        self.git("config", "user.name", "bancada")

    def git(self, *argumentos: str) -> None:
        subprocess.run(["git", "-C", str(self.raiz), *argumentos],
                       check=True, capture_output=True, text=True)

    def grava_rascunhos(self, intents: list[str], mensagem: str) -> None:
        caminho = self.raiz / RASCUNHOS
        caminho.write_text("".join(rascunho(i) + "\n" for i in intents),
                           encoding="utf-8")
        self.git("add", RASCUNHOS)
        self.git("commit", "-q", "-m", mensagem)

    def grava_manifesto(self, intents: list[str]) -> None:
        caminho = self.raiz / MANIFESTO
        caminho.write_text(
            "".join(json.dumps({"unique_intent_id": i,
                                "public_path": "/area/" + i + "/"}) + "\n"
                    for i in intents),
            encoding="utf-8")


def roda(raiz: Path, *extra: str) -> subprocess.CompletedProcess:
    ambiente = dict(os.environ)
    return subprocess.run([sys.executable, str(FERRAMENTA), *extra],
                          cwd=str(raiz), capture_output=True, text=True,
                          env=ambiente)


def executa_com_raiz(raiz: Path, *extra: str) -> subprocess.CompletedProcess:
    """A ferramenta deriva RAIZ do proprio caminho, entao a copia vai junto."""
    destino = raiz / "tools"
    destino.mkdir(exist_ok=True)
    copia = destino / FERRAMENTA.name
    copia.write_text(FERRAMENTA.read_text(encoding="utf-8"), encoding="utf-8")
    copia.chmod(0o755)
    return subprocess.run([sys.executable, str(copia), *extra],
                          capture_output=True, text=True)


def indice(raiz: Path) -> list[dict]:
    caminho = raiz / SAIDA
    if not caminho.exists():
        return []
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines() if l.strip()]


class TesteIndiceDeRascunhosPerdidos(unittest.TestCase):
    def monta(self, base: Path) -> Repositorio:
        repo = Repositorio(base)
        # historico: os tres existiam
        repo.grava_rascunhos(["a-saiu-publicado", "b-saiu-despublicado", "c-ficou"],
                             "estado inicial")
        # hoje: so c-ficou permanece no arquivo
        repo.grava_rascunhos(["c-ficou"], "rewrite descartou dois")
        # publicado: a-saiu-publicado e c-ficou
        repo.grava_manifesto(["a-saiu-publicado", "c-ficou"])
        return repo

    def test_rascunho_que_saiu_com_pagina_publicada_entra_no_indice(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            self.monta(base)
            resultado = executa_com_raiz(base)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            chaves = {linha["unique_intent_id"] for linha in indice(base)}
            self.assertIn("a-saiu-publicado", chaves)

    def test_rascunho_que_saiu_sem_pagina_publicada_fica_de_fora(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            self.monta(base)
            executa_com_raiz(base)
            chaves = {linha["unique_intent_id"] for linha in indice(base)}
            self.assertNotIn("b-saiu-despublicado", chaves)

    def test_rascunho_que_continua_no_arquivo_nunca_entra(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            self.monta(base)
            executa_com_raiz(base)
            chaves = {linha["unique_intent_id"] for linha in indice(base)}
            self.assertNotIn("c-ficou", chaves)

    def test_o_indice_carrega_a_revisao_de_onde_o_texto_volta(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            repo = self.monta(base)
            executa_com_raiz(base)
            linhas = [l for l in indice(base) if l["unique_intent_id"] == "a-saiu-publicado"]
            self.assertEqual(len(linhas), 1)
            revisao = linhas[0]["revisao_git"]
            saida = subprocess.run(
                ["git", "-C", str(base), "show", f"{revisao}:{RASCUNHOS}"],
                capture_output=True, text=True, check=True).stdout
            self.assertIn('"a-saiu-publicado"', saida,
                          "a revisao gravada no indice tem de conter o rascunho")
            self.assertEqual(linhas[0]["palavras_do_corpo"], 10)

    def test_a_rota_vem_do_manifesto_e_nao_do_rascunho(self):
        """O rascunho tem public_path "" por construcao (nasce bloqueado).

        Se o indice copiasse a rota do rascunho, as 231 paginas que ESTAO no ar
        sairiam apontando para lugar nenhum — e o campo vazio nao levanta erro
        nenhum, entao o defeito seria silencioso.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            self.monta(base)
            executa_com_raiz(base)
            linhas = [l for l in indice(base)
                      if l["unique_intent_id"] == "a-saiu-publicado"]
            self.assertEqual(len(linhas), 1)
            self.assertEqual(linhas[0]["public_path"], "/area/a-saiu-publicado/")

    def test_resumo_nao_grava(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            self.monta(base)
            resultado = executa_com_raiz(base, "--resumo")
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertFalse((base / SAIDA).exists(),
                             "--resumo nao pode gravar o indice")

    def test_arquivo_sem_historico_aborta_em_vez_de_devolver_vazio(self):
        """Ausencia de historico nao e ausencia de perda — tem de gritar.

        O caso real e o arquivo que existe no disco e nunca foi commitado: o
        repositorio TEM historico, o caminho nao. Sem esta guarda a uniao sairia
        vazia, `perdidos` sairia vazio e o indice diria "nada se perdeu" — que e
        o falso-verde que este projeto ja pagou para aprender a nao aceitar.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "repo"
            base.mkdir()
            repo = Repositorio(base)
            (base / "OUTRO.md").write_text("historico existe\n", encoding="utf-8")
            repo.git("add", "OUTRO.md")
            repo.git("commit", "-q", "-m", "historico do repositorio")
            (base / RASCUNHOS).write_text(rascunho("z") + "\n", encoding="utf-8")
            repo.grava_manifesto(["z"])
            resultado = executa_com_raiz(base)
            self.assertNotEqual(resultado.returncode, 0,
                                "sem historico o indice sairia vazio e mentiria")
            self.assertIn("nao tem historico", resultado.stderr + resultado.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
