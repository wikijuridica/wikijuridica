#!/usr/bin/env python3
"""Bancada de tools/check-produto-nao-some-do-worktree.

O gate separa duas coisas que `git status` mostra igual: arquivo de produto que
sumiu COM copia preservada ao lado (preservacao-antes-de-mutacao, correto) e
arquivo que sumiu SEM copia (perda pendente, que um `git add` por diretorio vira
commit). Os casos abaixo montam repositorios git de verdade, porque o gate le
`git status --porcelain` — um duble de arquivo nao exercitaria o caminho real.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-produto-nao-some-do-worktree"


def git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(raiz), *args], check=True, capture_output=True)


def repo(base: Path) -> None:
    (base / "data" / "editorial").mkdir(parents=True)
    git(base, "init", "-q")
    git(base, "config", "user.email", "bancada@local")
    git(base, "config", "user.name", "bancada")


def roda(base: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), "--raiz", str(base), *extra],
                          capture_output=True, text=True)


def produto_apagado_com_copia(base: Path, conteudo_da_copia: str) -> Path:
    """Commita `data/editorial/corpus.jsonl`, apaga o canonico, deixa a copia."""
    alvo = base / "data" / "editorial" / "corpus.jsonl"
    alvo.write_text("linha do HEAD\n", encoding="utf-8")
    git(base, "add", "data/editorial/corpus.jsonl")
    git(base, "commit", "-q", "-m", "produto")
    copia = alvo.parent / "corpus.jsonl.stale-resume-01-abc-def"
    copia.write_text(conteudo_da_copia, encoding="utf-8")
    alvo.unlink()
    return copia


class Bancada(unittest.TestCase):
    def test_sumiu_sem_copia_reprova_e_nomeia_o_caminho(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            alvo = base / "data" / "editorial" / "corpus.jsonl"
            alvo.write_text("linha\n", encoding="utf-8")
            git(base, "add", "data/editorial/corpus.jsonl")
            git(base, "commit", "-q", "-m", "produto")
            alvo.unlink()
            r = roda(base)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("data/editorial/corpus.jsonl", r.stdout)

    def test_sumiu_COM_copia_preservada_nao_reprova(self):
        """Preservar-antes-de-mutar é o comportamento CORRETO da cadeia.

        Acusá-lo faria o gate ter saída inteira em falso positivo — o dano que
        faz gate deixar de ser lido na terceira vez.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            alvo = base / "data" / "editorial" / "corpus.jsonl"
            alvo.write_text("linha\n", encoding="utf-8")
            git(base, "add", "data/editorial/corpus.jsonl")
            git(base, "commit", "-q", "-m", "produto")
            (alvo.parent / "corpus.jsonl.stale-resume-01-abc-def").write_text(
                "linha\n", encoding="utf-8")
            alvo.unlink()
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("com copia preservada: 1", r.stdout)

    def test_copia_com_sufixo_qualquer_nao_conta_como_preservacao(self):
        """`corpus.jsonl.novo` não é preservação — é outro arquivo.

        Sem esta distinção, qualquer vizinho de mesmo prefixo silenciaria a
        perda, e o gate viraria decoração.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            alvo = base / "data" / "editorial" / "corpus.jsonl"
            alvo.write_text("linha\n", encoding="utf-8")
            git(base, "add", "data/editorial/corpus.jsonl")
            git(base, "commit", "-q", "-m", "produto")
            (alvo.parent / "corpus.jsonl.novo").write_text("x\n", encoding="utf-8")
            alvo.unlink()
            r = roda(base)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_delecao_ja_estagiada_fica_fora(self):
        """`D ` já é decisão tomada: discute-se na revisão do commit."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            alvo = base / "data" / "editorial" / "corpus.jsonl"
            alvo.write_text("linha\n", encoding="utf-8")
            git(base, "add", "data/editorial/corpus.jsonl")
            git(base, "commit", "-q", "-m", "produto")
            alvo.unlink()
            git(base, "add", "data/editorial/corpus.jsonl")
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_arvore_fora_de_produto_nao_reprova(self):
        """`.agents/runtime/` é scratch declarado — sumir ali não é perda."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            (base / ".agents" / "runtime").mkdir(parents=True)
            alvo = base / ".agents" / "runtime" / "efemero.log"
            alvo.write_text("x\n", encoding="utf-8")
            git(base, "add", ".agents/runtime/efemero.log")
            git(base, "commit", "-q", "-m", "scratch")
            alvo.unlink()
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cardinalidade_vem_antes_da_lista(self):
        """A lista pode ser cortada; o total, nunca."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            for i in range(3):
                a = base / "data" / "editorial" / f"c{i}.jsonl"
                a.write_text("x\n", encoding="utf-8")
                git(base, "add", f"data/editorial/c{i}.jsonl")
            git(base, "commit", "-q", "-m", "produto")
            for i in range(3):
                (base / "data" / "editorial" / f"c{i}.jsonl").unlink()
            r = roda(base)
            primeira = r.stdout.splitlines()[0]
            self.assertIn("ausente da worktree: 3", primeira)
            self.assertIn("SEM copia: 3", primeira)

    # -- idade da preservacao e identidade com o HEAD (2026-09-10) --------------
    #
    # O relogio NAO e' falsificado nestes casos, e isso e' deliberado: `ctime` nao
    # se escreve por `os.utime` (que so mexe em atime/mtime), e fabricar um ctime
    # exigiria truque de filesystem que nao prova nada sobre a decisao. Quem varia
    # e' o LIMIAR, pelo argumento que o proprio gate expoe — o mesmo eixo, do lado
    # de ca da comparacao. Com `--idade-maxima-horas 0` toda copia recem-criada ja
    # esta "acima do teto"; com 9999, nenhuma esta. Trocar `>` por `<` na decisao
    # derruba os dois casos.

    def test_preservacao_recente_nao_e_abandono(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do HEAD\n")
            r = roda(base, "--idade-maxima-horas", "9999")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("preservacao-antes-de-mutacao em curso", r.stdout)
            self.assertNotIn("ABANDONADA", r.stdout)

    def test_preservacao_velha_reprova_como_abandono_e_ensina_o_HEAD(self):
        """"48 de 48 tem copia" e' o numero certo com a conclusao errada.

        Copia mais nova acima do teto com o canonico ainda ausente nao e'
        transacao em curso: e' passo morto, e o buraco fica exposto ao `git add`
        por diretorio de qualquer sessao.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do HEAD\n")
            r = roda(base, "--idade-maxima-horas", "0")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("ABANDONADA", r.stdout)
            self.assertIn("git show HEAD:data/editorial/corpus.jsonl", r.stdout)

    def test_copia_identica_ao_HEAD_e_contada_como_identica(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do HEAD\n")
            r = roda(base, "--idade-maxima-horas", "9999")
            self.assertIn("copias identicas ao HEAD: 1 de 1", r.stdout)

    def test_copia_que_difere_do_HEAD_nao_e_contada_como_identica(self):
        """Mesmo TAMANHO, conteudo diferente — o pre-filtro de tamanho nao decide.

        E' o caso que separa "existir copia" de "existir A copia": restaurar esta
        copia devolveria outro conteudo, e o gate tem de dizer isso.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do head\n")   # so a caixa muda
            r = roda(base, "--idade-maxima-horas", "9999")
            self.assertIn("copias identicas ao HEAD: 0 de 1", r.stdout)
            self.assertIn("restaurar a copia NAO devolve o HEAD", r.stdout)

    def test_a_idade_sai_antes_de_qualquer_caminho(self):
        """Cardinalidade e idade sao cabecalho; caminho e' amostra."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do HEAD\n")
            r = roda(base, "--idade-maxima-horas", "0")
            linhas = r.stdout.splitlines()
            self.assertIn("preservacao mais recente", linhas[1])
            posicao_do_caminho = next(
                i for i, l in enumerate(linhas) if "git show HEAD:" in l)
            self.assertGreater(posicao_do_caminho, 1)

    def test_idade_e_por_ctime_nao_por_mtime(self):
        """Um passo VIVO pode mover arquivo cujo conteudo e' de semanas atras.

        `rename(2)` preserva o mtime do canonico — a data em que o PRODUTOR
        escreveu. Julgar abandono por mtime reprovaria transacao legitima; ctime
        responde a pergunta certa: quando o buraco foi aberto. Aqui o mtime e' de
        1970 e o ctime e' de agora, e o gate tem de PASSAR.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            copia = produto_apagado_com_copia(base, "linha do HEAD\n")
            os.utime(copia, (0, 0))
            r = roda(base, "--idade-maxima-horas", "1")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn("ABANDONADA", r.stdout)

    def test_copia_de_tamanho_diferente_nao_e_identica(self):
        """Pre-filtro de tamanho decide sozinho, sem hashear 86 MB a toa."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); repo(base)
            produto_apagado_com_copia(base, "linha do HEAD com sobra\n")
            r = roda(base, "--idade-maxima-horas", "9999")
            self.assertIn("copias identicas ao HEAD: 0 de 1", r.stdout)

class LigadoAoPreCommit(unittest.TestCase):
    """Gate sem runner é o 312º órfão — o repositório já catalogou 311.

    `tools/check-*` não é descoberto por glob por nenhum runner (medido em
    2026-09-10: `run-qualidade-diaria` não faz glob de `tools/check-*`, e
    `generate-varredura-bateria-gates`, que faz, não está sob timer nenhum).
    A alcançabilidade deste gate vem de estar no pre-commit, e é isso que este
    caso protege.
    """

    def test_o_pre_commit_chama_o_gate(self):
        texto = (RAIZ / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("tools/check-produto-nao-some-do-worktree", texto,
                      "o gate ficou orfao: nenhum caminho o executa")

    def test_a_mensagem_diz_como_sair_do_caminho(self):
        """Gate que barra sem dizer a saída vira contorno com --no-verify."""
        texto = (RAIZ / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("estague-a (git add <caminho>)", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
