#!/usr/bin/env python3
"""Bancada de tools/check-modo-operacional e tools/check-ops-unit-hardcode.

POR QUE EXISTE. Um gate cujo unico executor e' a sessao que o escreveu nao e'
um gate: e' um script. `tools/run-qualidade-diaria` descobre os testes de
ferramenta por glob de `tools/test_*.py`, entao e' este arquivo que coloca os
dois gates do modo operacional na bancada diaria.

Ele nao reimplementa o que os gates fazem -- teste que refaz o pipeline a mao
fica verde com a regra desligada no codigo real. Ele EXECUTA os gates e,
alem disso, prova por mutacao que a guarda de unit enxerga divergencia, usando
uma copia em diretorio temporario (nunca as units vivas, que sao symlink de
/etc/systemd/system para este repositorio).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))


def roda(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, cwd=RAIZ)


class ModoOperacional(unittest.TestCase):
    def test_mecanismos_existem_disparam_e_custam_o_prometido(self):
        """T1-T5: inventario, disparo, falso-positivo, custo e registro."""
        r = roda(os.path.join(RAIZ, "tools", "check-modo-operacional"),
                 "--repeticoes", "5", "--max-ms", "300")
        self.assertEqual(r.returncode, 0,
                         f"check-modo-operacional reprovou:\n{r.stdout}\n{r.stderr}")
        self.assertIn("VERDE", r.stdout)

    def test_desligar_um_hook_deixa_a_bancada_vermelha(self):
        """Prova por mutacao: o T2 tem de NOMEAR o hook desligado."""
        r = roda(os.path.join(RAIZ, "tools", "check-modo-operacional"),
                 "--repeticoes", "3", "--provar-mutacao")
        self.assertEqual(r.returncode, 0,
                         f"prova por mutacao reprovou:\n{r.stdout}\n{r.stderr}")
        self.assertIn("prova por mutação", r.stdout)

    def test_hooks_estao_registrados_no_settings(self):
        """Mecanismo no disco sem entrada no settings.json nao impoe nada."""
        import json
        with open(os.path.join(RAIZ, ".claude", "settings.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        registrados = {
            c for bloco in cfg["hooks"]["PreToolUse"]
            for h in bloco["hooks"]
            for c in [h["command"]]
        }
        texto = " ".join(registrados)
        for nome in ("block-check-runner-sem-alvo.sh", "block-sudo-nginx-t.sh",
                     "block-git-add-por-diretorio.sh", "block-git-add-com-commit.sh",
                     "block-commit-sem-arquivo-de-mensagem.sh", "block-display-zero-social.sh",
                     "avisa-deploy-publico.sh", "avisa-derivado-editorial.sh"):
            self.assertIn(nome, texto, f"hook fora do settings.json: {nome}")


class UnitsDeOps(unittest.TestCase):
    def test_nenhuma_copia_de_caminho_divergiu(self):
        r = roda(os.path.join(RAIZ, "tools", "check-ops-unit-hardcode"))
        self.assertEqual(r.returncode, 0,
                         f"check-ops-unit-hardcode reprovou:\n{r.stdout}\n{r.stderr}")

    def test_guarda_enxerga_divergencia_de_path(self):
        """Mutacao numa COPIA: PATH divergente tem de reprovar.

        A mutacao escolhida e' exatamente a 'limpeza' que se evitou em
        2026-09-16: trocar /home/rafael/go/bin por um caminho sob /root, que e'
        para onde `%h` expande em unit de SISTEMA no systemd 252.
        """
        origem = os.path.join(RAIZ, "ops", "systemd")
        with tempfile.TemporaryDirectory(prefix="ops-unit-mut-") as tmp:
            for nome in os.listdir(origem):
                if nome.endswith((".service", ".timer")):
                    shutil.copy(os.path.join(origem, nome), os.path.join(tmp, nome))
            alvo = os.path.join(tmp, "wikijuridica-qualidade-diaria.service")
            with open(alvo, encoding="utf-8") as fh:
                texto = fh.read()
            mutado = texto.replace("Environment=PATH=/home/rafael/go/bin",
                                   "Environment=PATH=/root/go/bin", 1)
            self.assertNotEqual(texto, mutado, "a unit alvo perdeu a linha de PATH esperada")
            with open(alvo, "w", encoding="utf-8") as fh:
                fh.write(mutado)
            r = roda(os.path.join(RAIZ, "tools", "check-ops-unit-hardcode"), "--units", tmp)
            self.assertEqual(r.returncode, 1,
                             f"mutante SOBREVIVEU — a guarda nao ve divergencia de PATH:\n{r.stdout}")
            self.assertIn("divergiram entre si", r.stdout)


class PredicadoDoGitAdd(unittest.TestCase):
    """O predicado e "o git RECEBE um diretorio", nao "o comando MENCIONA um".

    Caso escrito (regra 22). Em 2026-09-16 o hook barrou
    `git add $(find .claude/hooks -type f)`: o word splitting parte a
    substituicao e um pedaco (`.claude/hooks`) parece um diretorio literal que o
    git NUNCA recebe -- a substituicao entrega arquivo a arquivo.

    ATENCAO AO REPRODUTOR CERTO: a forma `find ... | xargs git add --`, relatada
    como o gatilho, NAO reproduz -- ela sempre passou (exit 0), porque ali a
    cauda do `git add` e vazia ou so `--`. Quem falhava era a SUBSTITUICAO. Um
    teste cujo docstring nomeia o reprodutor errado e comentario que mente. O falso positivo encarecia a
    forma CERTA e empurrava para `git add <dir>`, que e o defeito real: guarda
    que torna o caminho certo mais caro que o errado inverte o incentivo que ela
    existe para criar.
    """

    def _t3_do_hook(self, dir_hooks=None):
        import importlib.machinery
        import importlib.util
        caminho = os.path.join(RAIZ, "tools", "check-modo-operacional")
        spec = importlib.util.spec_from_loader(
            "cmo", importlib.machinery.SourceFileLoader("cmo", caminho))
        cmo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cmo)
        falhas: list[str] = []
        kwargs = {"so": "block-git-add-por-diretorio.sh"}
        if dir_hooks:
            kwargs["dir_hooks"] = dir_hooks
        cmo.t2_t3_disparo(falhas, {}, **kwargs)
        return falhas

    def test_lista_derivada_passa_e_diretorio_reprova(self):
        """Na arvore real: nenhum falso positivo e nenhum falso negativo."""
        self.assertEqual([], self._t3_do_hook(),
                         "o hook de git add tem falha de fixture na arvore real")

    def test_predicado_antigo_deixa_o_t3_vermelho(self):
        """Mutacao dirigida: sem a guarda de lista derivada, o T3 acusa."""
        origem = os.path.join(RAIZ, ".claude", "hooks")
        with tempfile.TemporaryDirectory(prefix="mut-predicado-") as tmp:
            destino = os.path.join(tmp, "hooks")
            shutil.copytree(origem, destino)
            alvo = os.path.join(destino, "block-git-add-por-diretorio.sh")
            with open(alvo, encoding="utf-8") as fh:
                texto = fh.read()
            guarda = '\t\t[ "$derivada" = 1 ] && continue\n'
            self.assertIn(guarda, texto, "a guarda de lista derivada sumiu do hook")
            with open(alvo, "w", encoding="utf-8") as fh:
                fh.write(texto.replace(guarda, "", 1))
            falhas = self._t3_do_hook(dir_hooks=destino)
            t3 = [f for f in falhas if f.startswith("T3")]
            self.assertTrue(t3, "MUTANTE SOBREVIVEU: o T3 nao cobre a lista derivada")
            self.assertTrue(any("$(find" in f for f in t3),
                            f"o T3 acusou, mas nao a forma derivada: {t3}")


class GlobDaRule(unittest.TestCase):
    """T1: cada glob do `paths:` de uma rule tem de casar ARQUIVO real.

    Caso escrito em 2026-09-23. O T1 contava como casamento qualquer item que o
    `glob.glob(..., recursive=True)` devolvesse, e `**` devolve o PROPRIO
    diretorio-base: no Python 3.11.2 deste host,
    `glob.glob('/opt/wiki/naoexiste-xyz/**', recursive=True)` e
    `['/opt/wiki/naoexiste-xyz/']` com o diretorio AUSENTE -- todo glob terminado
    em `/**` passava. Diretorio que so tem subdiretorio "casa" tambem, e esse
    caso vale em qualquer versao (o 3.12.13 devolve `[]` para a base ausente, mas
    devolve os subdiretorios da base que existe). A rule so carrega quando um
    arquivo casado e lido: glob sem arquivo e rule que nunca entra no contexto.

    A bancada roda o `t1_inventario` REAL sobre uma arvore sintetica -- as
    globais RAIZ/CLAUDE do modulo carregado apontam para ela --, sem refazer o
    predicado a mao.
    """

    CHECK = os.path.join(RAIZ, "tools", "check-modo-operacional")
    # Clausula que a prova por mutacao apaga. Se o T1 mudar de forma, este teste
    # reprova pedindo a ancora nova -- a prova nao pode ficar para tras em silencio.
    FILTRO = " if os.path.isfile(p)"
    VEREDITO = "glob não casa nenhum arquivo real"

    def _carrega(self, caminho: str):
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "cmo_glob", importlib.machinery.SourceFileLoader("cmo_glob", caminho))
        cmo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cmo)
        return cmo

    def _arvore(self, raiz: str) -> None:
        claude = os.path.join(raiz, ".claude")
        os.makedirs(os.path.join(claude, "rules"))
        # Sem settings.json o T1 retorna antes de olhar as rules.
        with open(os.path.join(claude, "settings.json"), "w", encoding="utf-8") as fh:
            fh.write('{"hooks": {}}\n')
        regras = {
            "inexistente.md": ["naoexiste-xyz/**"],
            "diretorio-sem-arquivo.md": ["so-diretorios/**"],
            "arquivo-real.md": ["com-arquivo/**", "com-arquivo/**/*.go"],
        }
        for nome, globs in regras.items():
            itens = "".join(f'  - "{g}"\n' for g in globs)
            with open(os.path.join(claude, "rules", nome), "w", encoding="utf-8") as fh:
                fh.write(f"---\npaths:\n{itens}---\n\n# fixture {nome}\n")
        os.makedirs(os.path.join(raiz, "so-diretorios", "sub", "neto"))
        os.makedirs(os.path.join(raiz, "com-arquivo", "sub"))
        with open(os.path.join(raiz, "com-arquivo", "sub", "a.go"), "w", encoding="utf-8") as fh:
            fh.write("package sub\n")

    def _falhas_de_glob(self, caminho_do_check: str) -> list[str]:
        cmo = self._carrega(caminho_do_check)
        falhas: list[str] = []
        with tempfile.TemporaryDirectory(prefix="t1-glob-") as tmp:
            self._arvore(tmp)
            cmo.RAIZ = tmp
            cmo.CLAUDE = os.path.join(tmp, ".claude")
            cmo.HOOKS = os.path.join(cmo.CLAUDE, "hooks")
            cmo.t1_inventario(falhas, {})
        # As outras falhas do T1 na arvore sintetica (>= 6 rules, >= 13 skills)
        # sao ruido esperado: a assercao e so sobre o veredito de glob.
        return [f for f in falhas if self.VEREDITO in f]

    def test_glob_de_diretorio_inexistente_reprova(self):
        falhas = self._falhas_de_glob(self.CHECK)
        self.assertIn(f"T1 rule inexistente.md: {self.VEREDITO}: naoexiste-xyz/**", falhas,
                      f"o T1 aceitou glob de diretorio que nao existe: {falhas}")

    def test_glob_que_so_casa_diretorio_reprova(self):
        falhas = self._falhas_de_glob(self.CHECK)
        self.assertIn(f"T1 rule diretorio-sem-arquivo.md: {self.VEREDITO}: so-diretorios/**", falhas,
                      f"o T1 aceitou glob que so casa diretorio, sem arquivo: {falhas}")

    def test_glob_que_casa_arquivo_real_passa(self):
        falhas = self._falhas_de_glob(self.CHECK)
        self.assertEqual([], [f for f in falhas if "arquivo-real.md" in f],
                         "falso positivo: o T1 reprovou glob que casa arquivo real")

    def test_sem_o_filtro_isfile_o_t1_aceitaria_diretorio_sem_arquivo(self):
        """Prova por mutacao: sem o filtro, a fixture tem de mudar de veredito.

        O mutante e o predicado de antes do conserto. O caso que o separa em
        qualquer versao de Python e o diretorio que so tem subdiretorio; o da base
        inexistente so separa no 3.11, entao nao entra nesta assercao.
        """
        with open(self.CHECK, encoding="utf-8") as fh:
            texto = fh.read()
        self.assertEqual(1, texto.count(self.FILTRO),
                         "a ancora do filtro isfile sumiu do T1 (ou repetiu): atualize a prova por mutacao")
        with tempfile.TemporaryDirectory(prefix="t1-glob-mut-") as tmp:
            mutante = os.path.join(tmp, "check-modo-operacional")
            with open(mutante, "w", encoding="utf-8") as fh:
                fh.write(texto.replace(self.FILTRO, "", 1))
            falhas = self._falhas_de_glob(mutante)
        self.assertNotIn(f"T1 rule diretorio-sem-arquivo.md: {self.VEREDITO}: so-diretorios/**", falhas,
                         "sem o filtro isfile o T1 AINDA reprova o diretorio sem arquivo: a fixture "
                         "nao exercita o filtro, e o teste direto passaria com o mutante")


class TamanhoDaRule(unittest.TestCase):
    """T1: o teto de 6000 da rule e em CARACTERES, e a mensagem diz isso.

    Caso escrito em 2026-09-23. A mensagem dizia "bytes", mas o T1 mede
    `len(texto)`: caracteres. Com acento os dois divergem (antes do corte de
    2026-09-23, fila-do-cerebro.md tinha 25206 B e 25087 caracteres), e quem
    corta a rule mede com `wc -m`.
    Fixture acentuada: `cabe-em-caracteres.md` fica abaixo do teto em
    caracteres e acima em bytes (separa a UNIDADE da medida); `longa.md` passa
    do teto em caracteres (fixa o numero e o rotulo da mensagem).
    """

    CHECK = os.path.join(RAIZ, "tools", "check-modo-operacional")

    def test_teto_e_medido_e_rotulado_em_caracteres(self):
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "cmo_tamanho", importlib.machinery.SourceFileLoader("cmo_tamanho", self.CHECK))
        cmo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cmo)
        fm = '---\npaths:\n  - "alvo.txt"\n---\n\n'
        cabe = fm + "ação " * 990
        longa = fm + "ação " * 1300
        self.assertTrue(len(cabe) <= 6000 < len(cabe.encode("utf-8")),
                        "fixture: cabe-em-caracteres.md tem de caber em caracteres e estourar em bytes")
        self.assertGreater(len(longa), 6000, "fixture: longa.md tem de passar do teto em caracteres")
        falhas: list[str] = []
        with tempfile.TemporaryDirectory(prefix="t1-tamanho-") as tmp:
            regras = os.path.join(tmp, ".claude", "rules")
            os.makedirs(regras)
            with open(os.path.join(tmp, ".claude", "settings.json"), "w", encoding="utf-8") as fh:
                fh.write('{"hooks": {}}\n')
            for nome, conteudo in (("cabe-em-caracteres.md", cabe), ("longa.md", longa)):
                with open(os.path.join(regras, nome), "w", encoding="utf-8") as fh:
                    fh.write(conteudo)
            with open(os.path.join(tmp, "alvo.txt"), "w", encoding="utf-8") as fh:
                fh.write("x\n")
            cmo.RAIZ = tmp
            cmo.CLAUDE = os.path.join(tmp, ".claude")
            cmo.HOOKS = os.path.join(cmo.CLAUDE, "hooks")
            cmo.t1_inventario(falhas, {})
        longas = [f for f in falhas if "longa demais" in f]
        self.assertEqual([f"T1 rule longa demais ({len(longa)} caracteres, teto 6000): longa.md"], longas,
                         "o T1 tem de medir e rotular em caracteres: so longa.md passa do teto")


if __name__ == "__main__":
    unittest.main()
