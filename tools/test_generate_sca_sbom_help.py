#!/usr/bin/env python3
"""Testes de tools/generate-sca-sbom: a guarda de flag e o `--` do dirname.

O caso medido: em 2026-06-30 13:28, `tools/generate-sca-sbom --help` fez
OUTPUT="--help"; o `dirname --help` imprimiu a ajuda no stdout e o
`mkdir -p "$(dirname "$OUTPUT")"` criou na raiz do repositório uma cadeia de
19 diretórios cujos nomes são o texto da ajuda partido em `/`. Os 19 nomes
batem byte a byte com `LC_ALL=C dirname --help` do coreutils 9.1 desta máquina.

Todo teste roda numa CÓPIA do script em <tmp>/tools/: o ROOT do script vira
<tmp> e nada toca /opt/wiki. O ambiente não é herdado: PATH é
<tmp>/tools:/usr/bin:/bin, LC_ALL=C (a máquina fala pt_BR e o dirname
traduziria a ajuda) e HOME fica fora de <tmp>. O `go-modern` que o script
alcança é um dublê em <tmp>/tools/ que anota os argumentos num arquivo FORA de
<tmp> e sai 0: nenhum cyclonedx real sobe.

O que fica travado, e por quê:

  1. `--help` e `-h`: exit 0, uso no stderr, stdout vazio, dublê NÃO chamado e
     <tmp> contendo só `tools/`. Roda também sem o marcador
     WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY e sem run-heavy-throttled na cópia: se
     a guarda descer para baixo do reexec, o exec do wrapper ausente dá 127 e
     o teste fica vermelho. Uso errado responde antes do lock do SBOM.
  2. `-x` (flag desconhecida): exit 2, "flag desconhecida" + uso no stderr; o
     resto igual ao item 1.
  3. O que a guarda NÃO pode mudar: um caminho de saída real passa pelo
     run-heavy-throttled (dublê que só exporta o marcador e reexecuta), cria
     <tmp>/saida/ e chega ao go-modern com exatamente os argumentos de antes;
     `--scope=root` e `--root-only`, numa raiz falsa com git e `go.mod`
     rastreado, passam pela guarda e pelo wrapper e chegam ao go-modern com
     `-output data/ops/sca_cyclonedx_bom.json`; sem argumento, na mesma raiz,
     o script faz o inventário `go-modern list` e o SBOM do módulo raiz.
  4. PROVA POR MUTAÇÃO, o original: o teste apaga o bloco entre as sentinelas
     `# >>> guarda-de-flag` e `# <<< guarda-de-flag` e tira o `--` do
     `mkdir`/`dirname`, voltando ao comportamento de 2026-06-30. Com ele,
     `--help` CRIA o diretório `Usage:*` (a cadeia inteira bate com a ajuda do
     dirname) e o dublê recebe `-output --help`. O veredito é IMPRESSO.
  5. PROVA POR MUTAÇÃO, camada a camada: sem a guarda e com o `--`, `--help` e
     `-x` NÃO criam diretório (o `--` segura sozinho) e o dublê é chamado com
     `-output <flag>` (é a guarda que impede a chamada e dá o exit 0/2). O
     mutante inverso, guarda sem `--`, é equivalente para toda entrada: a
     guarda barra todo argumento que começa com `-`, e só um argumento assim
     faria o dirname ler opção. O `--` é defesa em profundidade, e o item 5
     prova que ela funciona quando a guarda falta.

A descoberta de módulos (conserto de 2026-09-23, no mesmo script):

  6. Raiz SEM repositório git: sem argumento e com `--scope=root`, o script sai
     75 (infra) com `git ls-files falhou (rc=N) em <raiz>: <erro do git>` no
     stderr, nunca "escopo desconhecido", sem chamar o go-modern e sem escrever
     nada. Antes do conserto a falha do git se perdia dentro de `< <(...)`.
  7. Repositório SEM go.mod rastreado: lista vazia também sai 75, com a causa.
  8. PROVA POR MUTAÇÃO, duas vezes. O mutante que apaga o bloco entre
     `# >>> guarda-de-descoberta` e `# <<< guarda-de-descoberta` volta ao falso
     verde (rc 0, só o `go-modern list`, nenhum cyclonedx) nos casos 6 e 7, e o
     `--scope=root` volta a culpar o escopo. E o script como estava em HEAD
     antes do conserto (revisão b36aaf5b, lida do histórico git) reproduz o
     defeito medido: rc 0 sem SBOM e rc 128 com "escopo desconhecido". Sem o
     histórico, esse caso é pulado com o motivo impresso.

Rodar:
    python3 tools/test_generate_sca_sbom_help.py -v
"""
from __future__ import annotations

import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "tools" / "generate-sca-sbom"

PATH_BASE = "/usr/bin:/bin"
MARCADOR_WRAPPER = "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY"
FIM_DA_CHAMADA = "__fim_da_chamada__"
BLOCO_DA_GUARDA = re.compile(
    r"^# >>> guarda-de-flag[^\n]*\n.*?^# <<< guarda-de-flag[^\n]*\n",
    re.S | re.M,
)
BLOCO_DA_DESCOBERTA = re.compile(
    r"^[ \t]*# >>> guarda-de-descoberta[^\n]*\n.*?^[ \t]*# <<< guarda-de-descoberta[^\n]*\n",
    re.S | re.M,
)
# A última revisão que tocou o script antes do conserto da descoberta; o
# conteúdo é byte a byte o de HEAD em 2026-09-23 (conferido com sha256sum).
REVISAO_ANTES_DO_CONSERTO = "b36aaf5bd83ac6bfa4cf8d0e9b798d54f5692655"
CHAMADA_DO_INVENTARIO = ["list", "-modfile=tools/sca/go.mod", "-m", "all"]
MKDIR_COM_DUPLO_HIFEN = 'mkdir -p -- "$(dirname -- "$OUTPUT")"'
MKDIR_ORIGINAL = 'mkdir -p "$(dirname "$OUTPUT")"'
ARGS_DO_CYCLONEDX = [
    "tool",
    "-modfile=tools/sca/go.mod",
    "cyclonedx-gomod",
    "mod",
    "-test",
    "-json",
    "-licenses",
]
FORMAS_NO_USO = (
    "Uso: tools/generate-sca-sbom",
    "--scope=<nome>",
    "--<nome>-only",
    "<caminho-de-saida>",
)


def sem_guarda(fonte: str) -> str:
    """Apaga o bloco entre as sentinelas; falha alto se ele não estiver lá."""
    blocos = BLOCO_DA_GUARDA.findall(fonte)
    if len(blocos) != 1:
        raise AssertionError(
            f"esperava 1 bloco entre as sentinelas guarda-de-flag em {SCRIPT}, "
            f"achei {len(blocos)}: o teste precisa acompanhar o script"
        )
    return BLOCO_DA_GUARDA.sub("", fonte, count=1)


def sem_duplo_hifen(fonte: str) -> str:
    """Volta o mkdir/dirname à forma de 2026-06-30; falha alto se não achar."""
    if fonte.count(MKDIR_COM_DUPLO_HIFEN) != 1:
        raise AssertionError(
            f"esperava 1 ocorrência de {MKDIR_COM_DUPLO_HIFEN!r} em {SCRIPT}: "
            "o teste precisa acompanhar o script"
        )
    return fonte.replace(MKDIR_COM_DUPLO_HIFEN, MKDIR_ORIGINAL, 1)


def sem_guarda_de_descoberta(fonte: str) -> str:
    """Apaga a guarda da descoberta; falha alto se o bloco não estiver lá."""
    blocos = BLOCO_DA_DESCOBERTA.findall(fonte)
    if len(blocos) != 1:
        raise AssertionError(
            f"esperava 1 bloco entre as sentinelas guarda-de-descoberta em {SCRIPT}, "
            f"achei {len(blocos)}: o teste precisa acompanhar o script"
        )
    return BLOCO_DA_DESCOBERTA.sub("", fonte, count=1)


def script_antes_do_conserto() -> str | None:
    """O script de HEAD antes do conserto da descoberta, lido do histórico git."""
    git = shutil.which("git", path=PATH_BASE)
    if not git:
        return None
    r = subprocess.run(
        [git, "-C", str(RAIZ), "show", f"{REVISAO_ANTES_DO_CONSERTO}:tools/generate-sca-sbom"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return r.stdout if r.returncode == 0 and r.stdout else None


def ajuda_do_dirname_em_c() -> tuple[int, str]:
    """(rc, stdout) de `LC_ALL=C dirname --help`, sem as quebras finais que $(...) come."""
    r = subprocess.run(
        ["dirname", "--help"],
        env={"PATH": PATH_BASE, "LC_ALL": "C"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return r.returncode, r.stdout.rstrip("\n")


def escreve_executavel(caminho: pathlib.Path, corpo: str) -> None:
    caminho.write_text(corpo, encoding="utf-8")
    caminho.chmod(0o755)


def chamadas(anotacao: pathlib.Path) -> list[list[str]]:
    """Cada chamada de um dublê vira a lista dos argumentos que ele recebeu."""
    if not anotacao.exists():
        return []
    resultado: list[list[str]] = []
    atual: list[str] = []
    for linha in anotacao.read_text(encoding="utf-8").split("\n"):
        if linha == FIM_DA_CHAMADA:
            resultado.append(atual)
            atual = []
        else:
            atual.append(linha)
    # o que sobra depois do último marcador é só o "" da quebra de linha final
    return resultado


def cadeia_de_diretorios(topo: pathlib.Path) -> list[str]:
    """Nomes de uma cadeia linear de diretórios, do topo até a folha."""
    nomes = [topo.name]
    atual = topo
    while True:
        filhos = os.listdir(atual)
        if not filhos:
            return nomes
        if len(filhos) != 1 or not (atual / filhos[0]).is_dir():
            raise AssertionError(f"esperava cadeia linear de diretórios, achei {filhos!r}")
        nomes.append(filhos[0])
        atual = atual / filhos[0]


class RaizFalsa:
    """Raiz de repositório descartável com a cópia (ou o mutante) do script."""

    def __init__(self, caso: unittest.TestCase, fonte: str, *, com_wrapper: bool) -> None:
        raiz = tempfile.TemporaryDirectory(prefix="sca-sbom-raiz-")
        fora = tempfile.TemporaryDirectory(prefix="sca-sbom-fora-")
        caso.addCleanup(raiz.cleanup)
        caso.addCleanup(fora.cleanup)
        self.raiz = pathlib.Path(raiz.name)
        self.fora = pathlib.Path(fora.name)
        self.tools = self.raiz / "tools"
        self.tools.mkdir()
        self.script = self.tools / "generate-sca-sbom"
        escreve_executavel(self.script, fonte)
        self.anotacao_go_modern = self.fora / "go-modern.args"
        escreve_executavel(
            self.tools / "go-modern",
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$@\" {FIM_DA_CHAMADA} >>{shlex.quote(str(self.anotacao_go_modern))}\n"
            "exit 0\n",
        )
        self.anotacao_wrapper = self.fora / "run-heavy-throttled.args"
        self.nomes_em_tools = ["generate-sca-sbom", "go-modern"]
        if com_wrapper:
            escreve_executavel(
                self.tools / "run-heavy-throttled",
                "#!/bin/sh\n"
                f"printf '%s\\n' \"$@\" {FIM_DA_CHAMADA} >>{shlex.quote(str(self.anotacao_wrapper))}\n"
                f"{MARCADOR_WRAPPER}=1\n"
                f"export {MARCADOR_WRAPPER}\n"
                'exec "$@"\n',
            )
            self.nomes_em_tools.append("run-heavy-throttled")

    def git(self, caso: unittest.TestCase, *comando: str) -> None:
        git = shutil.which("git", path=PATH_BASE)
        if not git:
            caso.skipTest(f"git fora de {PATH_BASE}: a descoberta de módulos do script depende dele")
        env_git = {"PATH": PATH_BASE, "HOME": str(self.fora), "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run([git, "-C", str(self.raiz), *comando], env=env_git, check=True, timeout=30)

    def versiona_go_mod(self, caso: unittest.TestCase) -> None:
        """Põe um go.mod no índice git da raiz falsa.

        A descoberta de módulos do script é `git ls-files`: sem repositório ela
        sai 75 (item 6). Um go.mod no índice basta para o módulo raiz existir.
        """
        self.git(caso, "init", "-q")
        (self.raiz / "go.mod").write_text("module wikijuridica.local/raizfalsa\n", encoding="utf-8")
        self.git(caso, "add", "go.mod")

    def roda(self, *args: str, marcador: bool) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": f"{self.tools}:{PATH_BASE}",
            "HOME": str(self.fora),
            "LC_ALL": "C",
            "LANG": "C",
            # o git não sobe acima da raiz falsa: um TMPDIR dentro de outro
            # repositório não pode emprestar um .git ao caso "sem git"
            "GIT_CEILING_DIRECTORIES": str(self.raiz.parent),
        }
        if marcador:
            env[MARCADOR_WRAPPER] = "1"
        return subprocess.run(
            [BASH, str(self.script), *args],
            cwd=str(self.fora),
            env=env,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

    def entradas(self) -> list[str]:
        return sorted(os.listdir(self.raiz))

    def chamadas_go_modern(self) -> list[list[str]]:
        return chamadas(self.anotacao_go_modern)

    def chamadas_wrapper(self) -> list[list[str]]:
        return chamadas(self.anotacao_wrapper)


BASH = shutil.which("bash", path=PATH_BASE) or ""


class GuardaDeFlagTest(unittest.TestCase):
    fonte = ""

    @classmethod
    def setUpClass(cls) -> None:
        if not SCRIPT.is_file():
            raise AssertionError(f"script ausente: {SCRIPT}")
        if not BASH:
            raise AssertionError(f"bash fora de {PATH_BASE}")
        # O PATH-base não pode alcançar ferramenta real do repositório: só o
        # dublê em <tmp>/tools responde por go-modern e run-heavy-throttled.
        for nome in ("go-modern", "run-heavy-throttled"):
            if shutil.which(nome, path=PATH_BASE):
                raise AssertionError(f"{nome} real alcançável por {PATH_BASE}")
        cls.fonte = SCRIPT.read_text(encoding="utf-8")

    def assert_nada_criado(self, raiz: RaizFalsa, rotulo: str) -> None:
        entradas = raiz.entradas()
        self.assertEqual(entradas, ["tools"], f"{rotulo}: a raiz ganhou entrada nova: {entradas!r}")
        self.assertEqual(
            [e for e in entradas if e.startswith(("Usage:", "Uso:"))], [], f"{rotulo}: diretório da ajuda"
        )
        self.assertEqual(sorted(os.listdir(raiz.tools)), sorted(raiz.nomes_em_tools), rotulo)

    def test_help_sai_zero_com_uso_no_stderr_e_nao_cria_nada(self) -> None:
        for flag in ("--help", "-h"):
            for marcador in (False, True):
                with self.subTest(flag=flag, marcador=marcador):
                    raiz = RaizFalsa(self, self.fonte, com_wrapper=False)
                    r = raiz.roda(flag, marcador=marcador)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(r.stdout, "")
                    for forma in FORMAS_NO_USO:
                        self.assertIn(forma, r.stderr)
                    self.assertNotIn("flag desconhecida", r.stderr)
                    self.assertEqual(raiz.chamadas_go_modern(), [], "go-modern não pode ser chamado")
                    self.assert_nada_criado(raiz, flag)
        print("\n[consertado] --help/-h: rc=0, uso no stderr, raiz só com tools/, go-modern não chamado")

    def test_flag_desconhecida_sai_dois(self) -> None:
        for marcador in (False, True):
            with self.subTest(marcador=marcador):
                raiz = RaizFalsa(self, self.fonte, com_wrapper=False)
                r = raiz.roda("-x", marcador=marcador)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertEqual(r.stdout, "")
                self.assertIn("generate-sca-sbom: flag desconhecida: -x", r.stderr)
                for forma in FORMAS_NO_USO:
                    self.assertIn(forma, r.stderr)
                self.assertEqual(raiz.chamadas_go_modern(), [], "go-modern não pode ser chamado")
                self.assert_nada_criado(raiz, "-x")
        print("\n[consertado] -x: rc=2, 'flag desconhecida' + uso no stderr, nada criado, go-modern não chamado")

    def test_caminho_de_saida_real_passa_pelo_wrapper_e_chega_ao_go_modern(self) -> None:
        raiz = RaizFalsa(self, self.fonte, com_wrapper=True)
        saida = raiz.raiz / "saida" / "sbom.json"
        r = raiz.roda(str(saida), marcador=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((raiz.raiz / "saida").is_dir(), "o mkdir da saída tem de acontecer")
        self.assertEqual(raiz.entradas(), ["saida", "tools"])
        self.assertEqual(raiz.chamadas_wrapper(), [[str(raiz.script), str(saida)]])
        self.assertEqual(raiz.chamadas_go_modern(), [ARGS_DO_CYCLONEDX + ["-output", str(saida), "."]])

    def test_formas_de_escopo_descem_pela_guarda(self) -> None:
        for arg in ("--scope=root", "--root-only"):
            with self.subTest(arg=arg):
                raiz = RaizFalsa(self, self.fonte, com_wrapper=True)
                raiz.versiona_go_mod(self)
                r = raiz.roda(arg, marcador=False)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("flag desconhecida", r.stderr)
                self.assertEqual(raiz.chamadas_wrapper(), [[str(raiz.script), arg]])
                self.assertEqual(
                    raiz.chamadas_go_modern(),
                    [ARGS_DO_CYCLONEDX + ["-output", "data/ops/sca_cyclonedx_bom.json", "."]],
                )

    def test_sem_argumento_faz_inventario_e_sbom_do_modulo_raiz(self) -> None:
        raiz = RaizFalsa(self, self.fonte, com_wrapper=True)
        raiz.versiona_go_mod(self)
        r = raiz.roda(marcador=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(raiz.chamadas_wrapper(), [[str(raiz.script)]])
        self.assertEqual(
            raiz.chamadas_go_modern(),
            [
                ["list", "-modfile=tools/sca/go.mod", "-m", "all"],
                ARGS_DO_CYCLONEDX + ["-output", "data/ops/sca_cyclonedx_bom.json", "."],
            ],
        )
        self.assertTrue((raiz.raiz / "data" / "ops" / "sca_tools_module_inventory.txt").is_file())

    def test_mutante_original_cria_o_diretorio_da_ajuda(self) -> None:
        mutante = sem_duplo_hifen(sem_guarda(self.fonte))
        self.assertNotEqual(mutante, self.fonte)
        self.assertNotIn("guarda-de-flag", mutante)
        self.assertIn(MKDIR_ORIGINAL, mutante)
        raiz = RaizFalsa(self, mutante, com_wrapper=False)
        r = raiz.roda("--help", marcador=True)
        rc_ajuda, ajuda = ajuda_do_dirname_em_c()
        if not ajuda.startswith("Usage:"):
            # dirname que não imprime a ajuda no stdout: o mkdir recebe "" e
            # falha, e a prova cai para o rc (o consertado sai 0 no --help).
            self.assertNotEqual(r.returncode, 0, r.stderr)
            print(
                f"\n[mutante original] dirname local sem ajuda no stdout (rc={rc_ajuda}); "
                f"prova pelo rc do mutante={r.returncode}"
            )
            return
        criados = [e for e in raiz.entradas() if e.startswith("Usage:")]
        self.assertEqual(len(criados), 1, f"o mutante devia criar o diretório da ajuda: {raiz.entradas()!r}")
        cadeia = cadeia_de_diretorios(raiz.raiz / criados[0])
        self.assertEqual(cadeia, [c for c in ajuda.split("/") if c], "a cadeia é a ajuda partida em '/'")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(raiz.chamadas_go_modern(), [ARGS_DO_CYCLONEDX + ["-output", "--help", "."]])
        print(
            f"\n[mutante original] --help: rc={r.returncode}; criou {criados[0].splitlines()[0]!r} "
            f"com {len(cadeia)} níveis; go-modern chamado com -output --help"
        )

    def test_mutante_sem_guarda_com_duplo_hifen(self) -> None:
        mutante = sem_guarda(self.fonte)
        self.assertNotEqual(mutante, self.fonte)
        self.assertIn(MKDIR_COM_DUPLO_HIFEN, mutante)
        vereditos = []
        for flag in ("--help", "-x"):
            with self.subTest(flag=flag):
                raiz = RaizFalsa(self, mutante, com_wrapper=False)
                r = raiz.roda(flag, marcador=True)
                self.assertEqual(r.returncode, 0, r.stderr)  # quem sai é o dublê
                self.assert_nada_criado(raiz, f"mutante sem guarda {flag}")
                self.assertEqual(raiz.chamadas_go_modern(), [ARGS_DO_CYCLONEDX + ["-output", flag, "."]])
                vereditos.append(f"{flag}: rc={r.returncode}, nada criado, go-modern chamado com -output {flag}")
        print("\n[mutante sem guarda, com --] " + "; ".join(vereditos))

    def test_descoberta_sem_git_sai_75_com_a_causa(self) -> None:
        for args in ((), ("--scope=root",)):
            with self.subTest(args=args):
                raiz = RaizFalsa(self, self.fonte, com_wrapper=True)
                r = raiz.roda(*args, marcador=False)
                self.assertEqual(r.returncode, 75, r.stderr)
                self.assertRegex(r.stderr, r"generate-sca-sbom: git ls-files falhou \(rc=\d+\) em .*: fatal: not a git repository")
                self.assertNotIn("escopo desconhecido", r.stderr)
                self.assertEqual(raiz.chamadas_wrapper(), [[str(raiz.script), *args]])
                self.assertEqual(raiz.chamadas_go_modern(), [], "sem lista de módulos o go-modern não roda")
                self.assertEqual(raiz.entradas(), ["tools"], "a falha vem antes de qualquer escrita")
        print("\n[consertado] raiz sem git: rc=75, 'git ls-files falhou' com o erro do git no stderr, go-modern não chamado")

    def test_descoberta_vazia_sai_75(self) -> None:
        raiz = RaizFalsa(self, self.fonte, com_wrapper=False)
        raiz.git(self, "init", "-q")
        r = raiz.roda(marcador=True)
        self.assertEqual(r.returncode, 75, r.stderr)
        self.assertIn("git ls-files não listou nenhum go.mod rastreado", r.stderr)
        self.assertEqual(raiz.chamadas_go_modern(), [])
        self.assertEqual(raiz.entradas(), [".git", "tools"])

    def test_mutante_sem_guarda_de_descoberta_volta_ao_falso_verde(self) -> None:
        mutante = sem_guarda_de_descoberta(self.fonte)
        self.assertNotEqual(mutante, self.fonte)
        self.assertNotIn("guarda-de-descoberta", mutante)
        vereditos = []
        sem_git = RaizFalsa(self, mutante, com_wrapper=False)
        r = sem_git.roda(marcador=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sem_git.chamadas_go_modern(), [CHAMADA_DO_INVENTARIO], "só o inventário, nenhum SBOM")
        vereditos.append(f"sem git: rc={r.returncode}, {len(sem_git.chamadas_go_modern()) - 1} cyclonedx")
        vazio = RaizFalsa(self, mutante, com_wrapper=False)
        vazio.git(self, "init", "-q")
        r = vazio.roda(marcador=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(vazio.chamadas_go_modern(), [CHAMADA_DO_INVENTARIO])
        vereditos.append(f"lista vazia: rc={r.returncode}, {len(vazio.chamadas_go_modern()) - 1} cyclonedx")
        escopo = RaizFalsa(self, mutante, com_wrapper=False)
        r = escopo.roda("--scope=root", marcador=True)
        self.assertEqual(r.returncode, 64, r.stderr)
        self.assertIn("escopo desconhecido", r.stderr)
        vereditos.append(f"--scope=root sem git: rc={r.returncode}, 'escopo desconhecido'")
        print("\n[mutante sem guarda de descoberta] " + "; ".join(vereditos))

    def test_script_de_head_antes_do_conserto_reproduz_o_defeito(self) -> None:
        original = script_antes_do_conserto()
        if original is None:
            print(f"\n[HEAD antes do conserto] revisão {REVISAO_ANTES_DO_CONSERTO[:8]} fora do alcance: caso pulado")
            self.skipTest(f"histórico git sem {REVISAO_ANTES_DO_CONSERTO}")
        self.assertNotEqual(original, self.fonte)
        raiz = RaizFalsa(self, original, com_wrapper=False)
        r = raiz.roda(marcador=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(raiz.chamadas_go_modern(), [CHAMADA_DO_INVENTARIO], "o falso verde: nenhum SBOM")
        escopo = RaizFalsa(self, original, com_wrapper=False)
        r_escopo = escopo.roda("--scope=root", marcador=True)
        self.assertNotEqual(r_escopo.returncode, 0)
        self.assertIn("escopo desconhecido", r_escopo.stderr)
        self.assertNotIn("git ls-files falhou", r_escopo.stderr)
        print(
            f"\n[HEAD antes do conserto, {REVISAO_ANTES_DO_CONSERTO[:8]}] sem git: rc={r.returncode} e 0 cyclonedx; "
            f"--scope=root: rc={r_escopo.returncode} com 'escopo desconhecido'"
        )


if __name__ == "__main__":
    unittest.main()
