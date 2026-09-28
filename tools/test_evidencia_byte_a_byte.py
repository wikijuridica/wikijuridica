#!/usr/bin/env python3
"""Bancada de tools/check-evidencia-byte-a-byte.

A guarda existe porque core.autocrlf DESTRUIU evidencia duas vezes em
2026-09-16, por caminhos independentes. O teste tem de provar tres coisas:
que ela pega a corrupcao, que NAO acusa trabalho em curso, e que arquivo em
edicao legitima e pulado -- foi esse falso positivo que a primeira versao
produziu contra data/source-audit/v2_source_provenance.jsonl.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "check-evidencia-byte-a-byte"

spec = importlib.util.spec_from_loader(
    "check_evidencia",
    importlib.machinery.SourceFileLoader("check_evidencia", str(FERRAMENTA)),
)
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)


def repo_falso() -> Path:
    """Repo git de verdade, com autocrlf=input, como a maquina real."""
    base = Path(tempfile.mkdtemp(prefix="evidencia-"))
    sh = lambda *a: subprocess.run(["git", "-C", str(base), *a], capture_output=True, check=True)
    subprocess.run(["git", "init", "-q", str(base)], capture_output=True, check=True)
    sh("config", "core.autocrlf", "input")
    sh("config", "user.email", "t@t")
    sh("config", "user.name", "t")
    (base / "internal" / "pkg" / "testdata").mkdir(parents=True)
    return base


def roda_em(base: Path) -> subprocess.CompletedProcess:
    """Aponta a ferramenta para outro repo trocando RAIZ."""
    codigo = FERRAMENTA.read_text(encoding="utf-8").replace(
        "RAIZ = Path(__file__).resolve().parent.parent", f'RAIZ = Path({str(base)!r})'
    )
    alvo = base / "guarda.py"
    alvo.write_text(codigo, encoding="utf-8")
    return subprocess.run([sys.executable, str(alvo)], capture_output=True, text=True)


class TesteDeteccao(unittest.TestCase):
    def test_pega_crlf_convertido_no_blob(self):
        base = repo_falso()
        f = base / "internal" / "pkg" / "testdata" / "fonte.html"
        f.write_bytes(b"<html>\r\n<body>\r\n</body>\r\n</html>\r\n")
        subprocess.run(["git", "-C", str(base), "add", "--", str(f.relative_to(base))], check=True, capture_output=True)
        proc = roda_em(base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("fonte.html", proc.stderr)
        self.assertIn("blob", proc.stderr)

    def test_com_gitattributes_escopado_fica_verde(self):
        """O conserto que a mensagem da guarda ensina tem de funcionar."""
        base = repo_falso()
        d = base / "internal" / "pkg" / "testdata"
        f = d / "fonte.html"
        f.write_bytes(b"<html>\r\n<body>\r\n</body>\r\n</html>\r\n")
        (d / ".gitattributes").write_text("* -text\n", encoding="utf-8")
        rel = lambda x: str(x.relative_to(base))
        subprocess.run(["git", "-C", str(base), "add", "--", rel(d / ".gitattributes")], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(base), "add", "--renormalize", "--", rel(f)], check=True, capture_output=True)
        proc = roda_em(base)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TesteControleNegativo(unittest.TestCase):
    def test_arquivo_em_edicao_nao_e_acusado(self):
        """O falso positivo real da primeira versao, virado teste.

        Arquivo rastreado, commitado e DEPOIS modificado na worktree diverge do
        indice por desenho -- e trabalho em curso, nao corrupcao. Sem este
        controle a guarda acusa toda frente que esteja editando um fixture.
        """
        base = repo_falso()
        f = base / "internal" / "pkg" / "testdata" / "dado.json"
        f.write_bytes(b'{"a":1}\n')
        rel = str(f.relative_to(base))
        subprocess.run(["git", "-C", str(base), "add", "--", rel], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(base), "commit", "-q", "-m", "x"], check=True, capture_output=True)
        f.write_bytes(b'{"a":2,"b":3}\n')          # edicao legitima, sem add
        proc = roda_em(base)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("em edicao", proc.stdout)

    def test_arquivo_so_com_LF_nao_e_acusado(self):
        base = repo_falso()
        f = base / "internal" / "pkg" / "testdata" / "limpo.json"
        f.write_bytes(b'{"a":1}\n')
        subprocess.run(["git", "-C", str(base), "add", "--", str(f.relative_to(base))], check=True, capture_output=True)
        self.assertEqual(roda_em(base).returncode, 0)

    def test_fora_de_diretorio_de_evidencia_nao_e_conferido(self):
        """CRLF em codigo comum nao e evidencia, e converter ali e correto."""
        base = repo_falso()
        (base / "internal" / "pkg" / "codigo.go").write_bytes(b"package pkg\r\n")
        subprocess.run(["git", "-C", str(base), "add", "--", "internal/pkg/codigo.go"], check=True, capture_output=True)
        proc = roda_em(base)
        self.assertEqual(proc.returncode, 2, "sem alvo de evidencia, o veredito e 'nao medi'")
        self.assertIn("NAO MEDIDO", proc.stderr)


class TesteEstadoReal(unittest.TestCase):
    def test_repo_esta_verde(self):
        proc = subprocess.run([str(FERRAMENTA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_fixture_do_stj_bate_byte_a_byte(self):
        """As duas que a guarda salvou ficam travadas por nome."""
        for rel, tam in (
            ("internal/stjacordaos/testdata/espelhos-segunda-secao-20240229-malformado.json", 599),
            ("internal/stjacordaos/testdata/dataset-espelhos-primeira-turma.html", 115986),
        ):
            blob = subprocess.run(["git", "-C", str(RAIZ), "cat-file", "-p", f":{rel}"], capture_output=True).stdout
            disco = (RAIZ / rel).read_bytes()
            self.assertEqual(len(blob), tam, f"{rel}: blob tem {len(blob)} bytes, esperado {tam}")
            self.assertEqual(blob, disco, f"{rel}: blob difere do disco")

    def test_ferramenta_e_read_only(self):
        fonte = FERRAMENTA.read_text(encoding="utf-8")
        for proibido in ("write_text(", "write_bytes(", "os.remove", "shutil.rmtree"):
            self.assertNotIn(proibido, fonte, f"a guarda nao pode escrever: achei {proibido}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
