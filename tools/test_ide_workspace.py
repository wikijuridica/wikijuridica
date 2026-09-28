#!/usr/bin/env python3
"""Prende o workspace do VSCodium no /opt/wiki: .vscode/settings.json,
.vscode/extensions.json, .vscode/tasks.json, pyrightconfig.json e o perfil
global do kit (ops/ide/perfil/settings.json).

Roda: python3 tools/test_ide_workspace.py        (sai 0 só com tudo verde)
Entra na qualidade diária pelo glob tools/test_*.py de tools/run-qualidade-diaria.

Contrato: docs/plans/IDE_TERMINAL_20260923_PLANO.md, §8 frente 3 (3.1 a 3.5),
princípios 5 e 6 do §6, §11.4 (F20) e §12.1. As 13 asserções (a 13ª, ordem do
orquestrador em 2026-09-23, prende o binário do gopls):
   1. os quatro JSON do workspace parseiam como JSON puro, sem chave duplicada;
   2. formatação automática só em [go] (gofmt via gopls, gofumpt desligado):
      global desligada, nenhum codeActionsOnSave "explicit"/"always", nenhuma
      reescrita de fim de linha, e todo default de linguagem que uma extensão do
      kit liga (o basedpyright liga formatOnType em [python]) desligado no workspace;
   3. -tags=devcmds no gopls (build.buildFlags) e em go.buildTags/go.testTags;
   4. go.goroot e go.alternateTools.go citam exatamente o `toolchain` do go.mod;
      gopls do .toolchains/bin; GOTOOLCHAIN=local no ambiente do gopls;
   5. nada roda sozinho no save: vetOnSave/lintOnSave "off", sem testOnSave/coverOnSave;
   6. nenhuma task com '...', ' all', lab-cycle, check-all, --global ou
      runOn folderOpen, e o provedor padrão de tasks do golang.go (que põe
      "test workspace" com ./... no seletor) desligado;
   7. exclusões exigidas presentes (watcher, busca, gopls), raízes de código
      nunca excluídas, files.exclude sem esconder data/, public/, .agents/, e a
      régua F20 MEDIDA NO DISCO: raiz de 1º nível fora das raízes de código com
      mais de 1.000 subdiretórios não excluídos pelo files.watcherExclude reprova;
   8. *.jsonl abre como plaintext;
   9. recomendações == ids do kit (ops/ide/extensoes*.txt, ou a lista fechada do
      plano §8 1.2 enquanto o kit não existir) + anthropic.claude-code, em
      minúsculas, sem interseção com as indesejadas, e o formatador de cada
      linguagem é extensão recomendada;
  10. perfil global do kit: sem auto-update, update.mode none, sem
      initialPermissionMode nem claudeProcessWrapper, usePythonEnvironment false,
      terminal bash -l, nenhuma menção a start-ai-terminal, watcherExclude absoluto;
  11. pyrightconfig: sem venv/venvPath (o .venv da raiz é 3.12 com só numpy),
      pythonVersion 3.11, typeCheckingMode off, extraPaths com o user site 3.11 e
      o .venv-tools311 da máquina nova, excludes pesados; e o settings não aponta
      interpretador para o .venv;
  12. contra chave inventada: toda chave não nativa do settings existe no
      contributes.configuration de uma extensão instalada (~/.vscode-oss/extensions,
      ou IDE_EXTENSIONS_DIR), com tipo, enum e subchaves conferidos; sem extensões
      instaladas, confere contra o snapshot dos manifestos fixados no kit;
  13. o gopls que o editor roda (.toolchains/bin/gopls) foi compilado com o
      toolchain do go.mod (`go version -m`); sem o binário, pulada com o motivo.

Depois, a prova por mutação: a bancada copia os arquivos para um diretório
temporário em /tmp/claude-1000, aplica cada mutante na CÓPIA e exige que a
asserção-alvo reprove PELO MOTIVO CERTO (cada mutante declara o trecho que a
mensagem de reprovação tem de conter). Mutante que sobrevive, ou que morre por
outro motivo, é defeito da asserção, não do arquivo.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent
# Os JSON citam o caminho canônico: o repositório mora em /opt/wiki nas duas
# máquinas (notebook e servidor novo). Cópia em outro lugar não é o workspace.
CANONICA = "/opt/wiki"
BASE_TEMP = "/tmp/claude-1000"

REL_SETTINGS = ".vscode/settings.json"
REL_EXTENSIONS = ".vscode/extensions.json"
REL_TASKS = ".vscode/tasks.json"
REL_PYRIGHT = "pyrightconfig.json"
REL_PERFIL = "ops/ide/perfil/settings.json"
REL_KIT = "ops/ide"
DIR_EXT_PADRAO = "~/.vscode-oss/extensions"
# Extensões embutidas do VSCodium (git, linguagens): lidas quando o editor existe.
DIRS_EMBUTIDAS = ("/usr/share/codium/resources/app/extensions",)


class Reprova(Exception):
    """A asserção reprovou; a mensagem diz o quê e onde."""


class Pulada(Exception):
    """Não há o que conferir neste host: o arquivo é de outra frente e ainda não existe."""


class Ctx:
    """Onde cada asserção lê. A bancada troca os caminhos por cópias mutadas."""

    def __init__(self, *, settings: Path, extensions: Path, tasks: Path, pyright: Path,
                 gomod: Path, perfil: Path, kit: Path, disco: Path,
                 dir_ext: Path | None, dirs_embutidas: list[Path],
                 gopls_bin: Path | None, gopls_modulo: str | None) -> None:
        self.settings = settings
        self.extensions = extensions
        self.tasks = tasks
        self.pyright = pyright
        self.gomod = gomod
        self.perfil = perfil
        self.kit = kit
        self.disco = disco
        self.dir_ext = dir_ext
        self.dirs_embutidas = dirs_embutidas
        self.gopls_bin = gopls_bin
        self.gopls_modulo = gopls_modulo
        self._manifestos: tuple[dict[str, dict], str] | None = None


# --------------------------------------------------------------------------
# Leitura

def _sem_duplicata(pares: list[tuple[str, object]]) -> dict:
    saida: dict = {}
    for chave, valor in pares:
        if chave in saida:
            raise Reprova(f"chave duplicada {chave!r} — o json do Python guarda só a última e esconde a primeira")
        saida[chave] = valor
    return saida


def ler_json(caminho: Path):
    try:
        texto = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise Reprova(f"{caminho.name}: arquivo ausente ({caminho})") from None
    try:
        return json.loads(texto, object_pairs_hook=_sem_duplicata)
    except json.JSONDecodeError as erro:
        raise Reprova(f"{caminho.name}: JSON inválido ({erro.msg}, linha {erro.lineno}) — o contrato é JSON puro, "
                      "sem comentário nem vírgula final, para qualquer ferramenta ler com json") from None
    except Reprova as erro:
        raise Reprova(f"{caminho.name}: {erro}") from None


def _objeto(dado: dict, chave: str) -> dict:
    valor = dado.get(chave, {})
    if not isinstance(valor, dict):
        raise Reprova(f"{chave} tem de ser objeto JSON, veio {type(valor).__name__}")
    return valor


def _linguagens(settings: dict) -> dict[str, dict]:
    """Blocos por linguagem ('[go]', '[a][b]') -> {id da linguagem: chaves do bloco}."""
    saida: dict[str, dict] = {}
    for chave, valor in settings.items():
        if not chave.startswith("[") or not isinstance(valor, dict):
            continue
        for linguagem in re.findall(r"\[([^\]]+)\]", chave):
            saida.setdefault(linguagem, {}).update(valor)
    return saida


# --------------------------------------------------------------------------
# Glob no dialeto dos excludes do editor. Semântica (a mesma do check-ide-host):
# padrão com '/' inicial casa caminho absoluto, os demais são relativos à raiz do
# workspace; '**' casa zero ou mais segmentos; 'X/**' casa o próprio X e tudo
# abaixo; '*' e '?' não atravessam '/'; '{a,b}' expande.
#
# Caminho absoluto só vale no files.watcherExclude. No search.exclude e no
# files.exclude o padrão é "always evaluated relative to the path of the workspace
# folder" (vscode-docs docs/editor/glob-patterns.md:45): o VS Code 1.136.1 passa a
# chave intacta ao ripgrep (th() em extensionHostProcess.js, cwd = pasta do
# workspace), e o rg ancora a '/' inicial na raiz da busca. Medido em 2026-09-23 com
# o rg embutido (15.0.0): -g '!<abs>/.venv*/**' não excluiu nada; '!/.venv*/**' e
# '!**/.venv*/**' excluíram. Por isso essas duas chaves se avaliam com so_relativo.

def _expandir_chaves(padrao: str) -> list[str]:
    achado = re.search(r"\{([^{}]*)\}", padrao)
    if achado is None:
        return [padrao]
    saida: list[str] = []
    for alternativa in achado.group(1).split(","):
        saida.extend(_expandir_chaves(padrao[:achado.start()] + alternativa + padrao[achado.end():]))
    return saida


def _glob_para_regex(padrao: str) -> re.Pattern[str]:
    partes: list[str] = []
    i = 0
    while i < len(padrao):
        if padrao.startswith("**/", i):
            partes.append(r"(?:[^/]*/)*")
            i += 3
        elif padrao.startswith("/**", i) and i + 3 == len(padrao):
            partes.append(r"(?:/.*)?")
            i += 3
        elif padrao.startswith("**", i):
            partes.append(r".*")
            i += 2
        elif padrao[i] == "*":
            partes.append(r"[^/]*")
            i += 1
        elif padrao[i] == "?":
            partes.append(r"[^/]")
            i += 1
        else:
            partes.append(re.escape(padrao[i]))
            i += 1
    return re.compile(r"\A" + "".join(partes) + r"\Z", re.DOTALL)


def compilar_exclusoes(mapa: dict) -> list[tuple[bool, str, re.Pattern[str]]]:
    """(absoluto?, padrão, regex) de cada padrão ligado (valor true) de um mapa de exclusão."""
    regras = []
    for padrao, ligado in mapa.items():
        if ligado is not True:
            continue
        for expandido in _expandir_chaves(padrao):
            regras.append((expandido.startswith("/"), padrao, _glob_para_regex(expandido)))
    return regras


def casa_exclusao(rel: str, absoluto: str, regras, so_relativo: bool = False) -> str | None:
    for eh_absoluto, padrao, regex in regras:
        if eh_absoluto and so_relativo:
            continue
        if regex.match(absoluto if eh_absoluto else rel):
            return padrao
    return None


# --------------------------------------------------------------------------
# Régua F20 (plano §11.4): pasta pesada nova fora da exclusão do watcher.

LIMITE_F20 = 1000
RAIZES_DE_CODIGO = frozenset({"internal", "cmd", "tools", "ops", "docs", "scripts", ".claude", "content"})


def _e_diretorio(entrada: os.DirEntry) -> bool:
    try:
        return entrada.is_dir(follow_symlinks=False)
    except OSError:
        return False


def subdirs_nao_excluidos(disco: Path, nome: str, regras) -> int:
    """Subdiretórios de disco/nome que o watcher vigiaria, com parada em LIMITE_F20 + 1."""
    base = str(disco)
    if casa_exclusao(nome, f"{base}/{nome}", regras):
        return 0
    contagem = 0
    pilha = [(os.path.join(base, nome), nome)]
    while pilha:
        caminho, rel = pilha.pop()
        try:
            with os.scandir(caminho) as entradas:
                filhos = [(e.path, e.name) for e in entradas if _e_diretorio(e)]
        except OSError:
            continue
        for caminho_filho, nome_filho in filhos:
            rel_filho = f"{rel}/{nome_filho}"
            if casa_exclusao(rel_filho, caminho_filho, regras):
                continue
            contagem += 1
            if contagem > LIMITE_F20:
                return contagem
            pilha.append((caminho_filho, rel_filho))
    return contagem


def raizes_pesadas_descobertas(disco: Path, regras) -> list[str]:
    try:
        entradas = sorted((e for e in os.scandir(disco) if _e_diretorio(e)), key=lambda e: e.name)
    except OSError as erro:
        raise Reprova(f"régua F20: não consegui listar {disco}: {erro}") from None
    return [e.name for e in entradas
            if e.name not in RAIZES_DE_CODIGO and subdirs_nao_excluidos(disco, e.name, regras) > LIMITE_F20]


# --------------------------------------------------------------------------
# Manifestos das extensões (asserções 2 e 12)

# Recorte dos package.json das versões fixadas no kit (ops/ide/extensoes.txt),
# baixados do Open VSX em 2026-09-23 (URL em "fonte"): todos os NOMES de chave
# contribuídos; tipo e enum só das chaves que o settings usa; configurationDefaults
# de linguagem. Serve a dois fins: é a base NÃO circular dos mutantes da asserção
# 12 e o fallback dela quando nenhuma extensão está instalada. Com extensões
# instaladas, vale o manifesto instalado.
SNAPSHOT_MANIFESTOS: dict[str, dict] = {
    "golang.go@0.56.1": {
        "fonte": "https://open-vsx.org/api/golang/Go/0.56.1",
        "defaults": {"[go]": {"editor.insertSpaces": False, "editor.formatOnSave": True, "editor.formatOnSaveMode": "file", "editor.codeActionsOnSave": {"source.organizeImports": "explicit"}}},
        "chaves": (
            "go.addTags go.alternateTools go.buildFlags go.buildOnSave go.buildTags go.coverMode "
            "go.coverOnSave go.coverOnSingleTest go.coverOnSingleTestFile go.coverOnTestPackage "
            "go.coverShowCounts go.coverageDecorator go.coverageOptions go.delveConfig "
            "go.diagnostic.vulncheck go.disableConcurrentTests go.editorContextMenuCommands go.enableCodeLens "
            "go.experiments go.formatFlags go.formatTool go.generateTestsFlags go.gopath go.goroot "
            "go.inferGopath go.inlayHints.assignVariableTypes go.inlayHints.compositeLiteralFields "
            "go.inlayHints.compositeLiteralTypes go.inlayHints.constantValues "
            "go.inlayHints.functionTypeParameters go.inlayHints.ignoredError go.inlayHints.parameterNames "
            "go.inlayHints.rangeVariableTypes go.installDependenciesWhenBuilding go.languageServerFlags "
            "go.lintFlags go.lintOnSave go.lintTool go.logging.level go.playground go.removeTags "
            "go.showWelcome go.survey.prompt go.tasks.provideDefault go.terminal.activateEnvironment "
            "go.testEnvFile go.testEnvVars go.testExplorer.alwaysRunBenchmarks "
            "go.testExplorer.concatenateMessages go.testExplorer.enable go.testExplorer.packageDisplayMode "
            "go.testExplorer.showDynamicSubtestsInEditor go.testExplorer.showOutput go.testFlags "
            "go.testOnSave go.testTags go.testTimeout go.toolsEnvVars go.toolsGopath "
            "go.toolsManagement.autoUpdate go.toolsManagement.checkForUpdates go.toolsManagement.go "
            "go.trace.server go.useLanguageServer go.vetFlags go.vetOnSave gopls "
        ),
        "esquemas": {
            "go.alternateTools": {"type": "object"},
            "go.buildTags": {"type": "string"},
            "go.diagnostic.vulncheck": {"type": "string", "enum": ["Imports", "Off", "Prompt"]},
            "go.formatTool": {"type": "string", "enum": ["default", "gofmt", "goimports", "goformat", "gofumpt", "custom"]},
            "go.goroot": {"type": ["string", "null"]},
            "go.lintOnSave": {"type": "string", "enum": ["file", "package", "workspace", "off"]},
            "go.survey.prompt": {"type": "boolean"},
            "go.tasks.provideDefault": {"type": "boolean"},
            "go.terminal.activateEnvironment": {"type": "boolean"},
            "go.testFlags": {"type": ["array", "null"]},
            "go.testTimeout": {"type": "string"},
            "go.toolsManagement.autoUpdate": {"type": "boolean"},
            "go.toolsManagement.checkForUpdates": {"type": "string", "enum": ["proxy", "local", "off"]},
            "go.vetOnSave": {"type": "string", "enum": ["package", "workspace", "off"]},
            "gopls": {"type": "object"},
        },
        "aninhadas": {
            "gopls": {
                "chaves": (
                    "build.buildFlags build.directoryFilters build.env build.expandWorkspaceToModule build.memoryMode "
                    "build.standaloneTags build.templateExtensions build.workspaceFiles fileWatcher "
                    "formatting.gofumpt formatting.local maxFileCacheBytes ui.codelenses "
                    "ui.completion.completeFunctionCalls ui.completion.completionBudget "
                    "ui.completion.experimentalPostfixCompletions ui.completion.matcher ui.completion.usePlaceholders "
                    "ui.diagnostic.analyses ui.diagnostic.analysisProgressReporting ui.diagnostic.annotations "
                    "ui.diagnostic.diagnosticsDelay ui.diagnostic.diagnosticsTrigger ui.diagnostic.staticcheck "
                    "ui.diagnostic.staticcheckProvided ui.documentation.hoverKind ui.documentation.linkTarget "
                    "ui.documentation.linksInHover ui.moveType ui.navigation.importShortcut "
                    "ui.navigation.symbolMatcher ui.navigation.symbolScope ui.navigation.symbolStyle "
                    "ui.newGoFileHeader ui.noSemanticNumber ui.noSemanticString ui.renameMovesSubpackages "
                    "ui.semanticTokenModifiers ui.semanticTokenTypes ui.semanticTokens verboseOutput "
                ),
                "esquemas": {
                    "build.buildFlags": {"type": "array"},
                    "build.directoryFilters": {"type": "array"},
                    "build.env": {"type": "object"},
                    "formatting.gofumpt": {"type": "boolean"},
                    "ui.diagnostic.staticcheck": {"type": "boolean"},
                },
            },
            "go.alternateTools": {
                "chaves": "customFormatter dlv go gopls",
                "esquemas": {
                    "go": {"type": "string"},
                    "gopls": {"type": "string"},
                },
            },
        },
    },
    "charliermarsh.ruff@2026.82.0": {
        "fonte": "https://open-vsx.org/api/charliermarsh/ruff/2026.82.0",
        "defaults": {},
        "chaves": (
            "ruff.args ruff.codeAction.disableRuleComment ruff.codeAction.fixViolation ruff.configuration "
            "ruff.configurationPreference ruff.enable ruff.enableExperimentalFormatter ruff.exclude "
            "ruff.fixAll ruff.format.args ruff.format.backend ruff.format.preview ruff.ignoreStandardLibrary "
            "ruff.importStrategy ruff.interpreter ruff.lineLength ruff.lint.args ruff.lint.enable "
            "ruff.lint.extendSelect ruff.lint.ignore ruff.lint.preview ruff.lint.run ruff.lint.select "
            "ruff.logFile ruff.logLevel ruff.nativeServer ruff.organizeImports ruff.path ruff.run "
            "ruff.showNotifications ruff.showSyntaxErrors ruff.trace.server "
        ),
        "esquemas": {
            "ruff.fixAll": {"type": "boolean"},
            "ruff.lint.select": {"type": "array"},
            "ruff.organizeImports": {"type": "boolean"},
            "ruff.path": {"type": "array"},
        },
    },
    "timonwong.shellcheck@0.40.1": {
        "fonte": "https://open-vsx.org/api/timonwong/shellcheck/0.40.1",
        "defaults": {},
        "chaves": (
            "shellcheck.customArgs shellcheck.disableVersionCheck shellcheck.enable shellcheck.enableQuickFix "
            "shellcheck.exclude shellcheck.executablePath shellcheck.ignoreFileSchemes "
            "shellcheck.ignorePatterns shellcheck.logLevel shellcheck.run shellcheck.useWorkspaceRootAsCwd "
        ),
        "esquemas": {
            "shellcheck.customArgs": {"type": "array"},
            "shellcheck.executablePath": {"type": "string"},
            "shellcheck.run": {"type": "string", "enum": ["onSave", "onType", "manual"]},
            "shellcheck.useWorkspaceRootAsCwd": {"type": "boolean"},
        },
    },
    "mads-hartmann.bash-ide-vscode@1.43.2": {
        "fonte": "https://open-vsx.org/api/mads-hartmann/bash-ide-vscode/1.43.2",
        "defaults": {},
        "chaves": (
            "bashIde.backgroundAnalysisIgnore bashIde.backgroundAnalysisMaxFiles "
            "bashIde.enableSourceErrorDiagnostics bashIde.explainshellEndpoint bashIde.globPattern "
            "bashIde.includeAllWorkspaceSymbols bashIde.logLevel bashIde.shellcheckArguments "
            "bashIde.shellcheckExternalSources bashIde.shellcheckPath bashIde.shfmt.additionalArguments "
            "bashIde.shfmt.binaryNextLine bashIde.shfmt.caseIndent bashIde.shfmt.funcNextLine "
            "bashIde.shfmt.ignoreEditorconfig bashIde.shfmt.keepPadding bashIde.shfmt.languageDialect "
            "bashIde.shfmt.path bashIde.shfmt.simplifyCode bashIde.shfmt.spaceRedirects "
        ),
        "esquemas": {
            "bashIde.backgroundAnalysisIgnore": {"type": "array"},
            "bashIde.shellcheckPath": {"type": "string"},
            "bashIde.shfmt.path": {"type": "string"},
        },
    },
    "detachhead.basedpyright@1.40.1": {
        "fonte": "https://open-vsx.org/api/detachhead/basedpyright/1.40.1",
        "defaults": {"[python]": {"editor.formatOnType": True, "editor.quickSuggestions": {"strings": True}, "editor.wordBasedSuggestions": "off"}},
        "chaves": (
            "basedpyright.analysis.autoFormatStrings basedpyright.analysis.autoImportCompletions "
            "basedpyright.analysis.autoSearchPaths basedpyright.analysis.baselineFile "
            "basedpyright.analysis.baselineMode basedpyright.analysis.configFilePath "
            "basedpyright.analysis.diagnosticMode basedpyright.analysis.diagnosticSeverityOverrides "
            "basedpyright.analysis.exclude basedpyright.analysis.extraPaths "
            "basedpyright.analysis.fileEnumerationTimeout basedpyright.analysis.ignore "
            "basedpyright.analysis.include basedpyright.analysis.inlayHints.callArgumentNames "
            "basedpyright.analysis.inlayHints.callArgumentNamesMatching "
            "basedpyright.analysis.inlayHints.functionReturnTypes "
            "basedpyright.analysis.inlayHints.genericTypes basedpyright.analysis.inlayHints.variableTypes "
            "basedpyright.analysis.logLevel basedpyright.analysis.stubPath "
            "basedpyright.analysis.typeCheckingMode basedpyright.analysis.typeshedPaths "
            "basedpyright.analysis.useLibraryCodeForTypes basedpyright.analysis.useTypingExtensions "
            "basedpyright.disableLanguageServices basedpyright.disableOrganizeImports "
            "basedpyright.disablePullDiagnostics basedpyright.disableTaggedHints basedpyright.importStrategy "
            "python.pythonPath python.venvPath "
        ),
        "esquemas": {},
    },
}


def manifestos_do_snapshot() -> dict[str, dict]:
    saida: dict[str, dict] = {}
    for ident, recorte in SNAPSHOT_MANIFESTOS.items():
        propriedades = {chave: dict(recorte["esquemas"].get(chave, {})) for chave in recorte["chaves"].split()}
        for chave, aninhada in recorte.get("aninhadas", {}).items():
            propriedades[chave]["properties"] = {
                nome: dict(aninhada["esquemas"].get(nome, {})) for nome in aninhada["chaves"].split()}
        saida[ident] = {"propriedades": propriedades, "defaults": recorte["defaults"]}
    return saida


def ler_manifestos(diretorios: list[Path]) -> dict[str, dict]:
    saida: dict[str, dict] = {}
    for diretorio in diretorios:
        for pacote in sorted(diretorio.glob("*/package.json")):
            try:
                manifesto = json.loads(pacote.read_text(encoding="utf-8"))
            except (OSError, ValueError) as erro:
                raise Reprova(f"manifesto ilegível {pacote}: {erro}") from None
            contribui = manifesto.get("contributes") or {}
            configuracao = contribui.get("configuration") or []
            if isinstance(configuracao, dict):
                configuracao = [configuracao]
            propriedades: dict = {}
            for bloco in configuracao:
                if isinstance(bloco, dict):
                    propriedades.update(bloco.get("properties") or {})
            ident = f"{str(manifesto.get('publisher', '?')).lower()}.{str(manifesto.get('name', '?')).lower()}"
            saida[f"{ident}@{manifesto.get('version', '?')}"] = {
                "propriedades": propriedades,
                "defaults": {k: v for k, v in (contribui.get("configurationDefaults") or {}).items() if k.startswith("[")},
            }
    return saida


def manifestos(ctx: Ctx) -> tuple[dict[str, dict], str]:
    if ctx._manifestos is None:
        if ctx.dir_ext is None:
            fixados = ", ".join(SNAPSHOT_MANIFESTOS)
            ctx._manifestos = (manifestos_do_snapshot(),
                               f"snapshot dos manifestos fixados no kit ({fixados}) — {DIR_EXT_PADRAO} ausente")
        else:
            lidos = ler_manifestos([ctx.dir_ext] + list(ctx.dirs_embutidas))
            ctx._manifestos = (lidos, f"{len(lidos)} manifestos instalados em {ctx.dir_ext}"
                               + (f" + embutidos {', '.join(map(str, ctx.dirs_embutidas))}" if ctx.dirs_embutidas else ""))
    return ctx._manifestos


# --------------------------------------------------------------------------
# Asserções

def a1_json(ctx: Ctx) -> str:
    for caminho in (ctx.settings, ctx.extensions, ctx.tasks, ctx.pyright):
        if not isinstance(ler_json(caminho), dict):
            raise Reprova(f"{caminho.name}: a raiz tem de ser um objeto JSON")
    return "settings, extensions, tasks e pyrightconfig em JSON puro, sem chave duplicada"


LIGA_FORMATACAO = ("editor.formatOnSave", "editor.formatOnType", "editor.formatOnPaste")
REESCREVE_BYTES = ("files.trimTrailingWhitespace", "files.insertFinalNewline", "files.trimFinalNewlines")
ACOES_QUE_RODAM = ("explicit", "always")


def _defaults_que_ligam(ctx: Ctx):
    """(extensão, linguagem, chave, valor) de todo configurationDefaults de linguagem que liga
    formatação ou ação no save. Default de linguagem contribuído por extensão vence a chave
    global do workspace: na lista de precedência da doc ("later scopes override earlier
    scopes", vscode-docs docs/configure/settings.md §Settings precedence) "Language-specific
    default settings" vem depois de "Workspace settings". Só o bloco [linguagem] do
    workspace, que vem depois dos dois, desliga."""
    lidos, _ = manifestos(ctx)
    for ident, manifesto in sorted(lidos.items()):
        for bloco, valores in manifesto["defaults"].items():
            if not isinstance(valores, dict):
                continue
            for linguagem in re.findall(r"\[([^\]]+)\]", bloco):
                for chave in LIGA_FORMATACAO:
                    if valores.get(chave) is True:
                        yield ident, linguagem, chave, True
                acoes = valores.get("editor.codeActionsOnSave")
                if isinstance(acoes, dict):
                    ligadas = {a: m for a, m in acoes.items() if m in ACOES_QUE_RODAM or m is True}
                    if ligadas:
                        yield ident, linguagem, "editor.codeActionsOnSave", ligadas


def a2_formatacao(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    for chave in LIGA_FORMATACAO:
        if s.get(chave) is not False:
            raise Reprova(f"{chave} global = {s.get(chave)!r} — o workspace fixa false "
                          "(princípio 5: formatação automática só em [go])")
    for chave in REESCREVE_BYTES:
        if s.get(chave) is True:
            raise Reprova(f"{chave} = true reescreve bytes de arquivo cujo SHA-256 vai ao published_manifest (§12.1)")
    linguagens = _linguagens(s)
    bloco_go = linguagens.get("go", {})
    if bloco_go.get("editor.formatOnSave") is not True or bloco_go.get("editor.defaultFormatter") != "golang.go":
        raise Reprova("[go] tem de formatar no save pelo golang.go (gofmt via gopls) — o pre-commit exige .go formatado")
    for linguagem, bloco in linguagens.items():
        for chave in LIGA_FORMATACAO:
            if linguagem != "go" and bloco.get(chave) is True:
                raise Reprova(f"[{linguagem}] {chave} = true — fora de [go] não há formatação automática "
                              "(memória 'formatador desfaz correção')")
        for chave in REESCREVE_BYTES:
            if bloco.get(chave) is True:
                raise Reprova(f"[{linguagem}] {chave} = true reescreve bytes (§12.1)")
    for onde, bloco in [("global", s)] + [(f"[{nome}]", b) for nome, b in linguagens.items()]:
        acoes = bloco.get("editor.codeActionsOnSave")
        if isinstance(acoes, dict):
            for acao, modo in acoes.items():
                if modo in ACOES_QUE_RODAM or modo is True:
                    raise Reprova(f"{onde} editor.codeActionsOnSave.{acao} = {modo!r} — ação automática no save")
        elif acoes:
            raise Reprova(f"{onde} editor.codeActionsOnSave em lista: nesse formato toda ação da lista roda no save")
    origens = []
    for ident, linguagem, chave, valor in _defaults_que_ligam(ctx):
        bloco = linguagens.get(linguagem, {})
        if chave == "editor.codeActionsOnSave":
            acoes = bloco.get(chave) if isinstance(bloco.get(chave), dict) else {}
            for acao, modo in valor.items():
                if acoes.get(acao) not in ("never", False):
                    raise Reprova(f"{ident} liga [{linguagem}] editor.codeActionsOnSave.{acao} = {modo!r} por default "
                                  "e o workspace não põe 'never'")
            origens.append(f"{ident} [{linguagem}] codeActionsOnSave")
        elif linguagem != "go":
            if bloco.get(chave) is not False:
                raise Reprova(f"{ident} liga [{linguagem}] {chave} por default (configurationDefaults) e o workspace "
                              "não desliga — default de linguagem vence a chave global")
            origens.append(f"{ident} [{linguagem}] {chave}")
    gopls = _objeto(s, "gopls")
    if s.get("go.formatTool", "default") != "default":
        raise Reprova(f"go.formatTool = {s.get('go.formatTool')!r} — 'default' é o gopls, que formata como o gofmt")
    if gopls.get("formatting.gofumpt") is not False:
        raise Reprova("gopls formatting.gofumpt ≠ false — o repositório formata com gofmt, não gofumpt")
    if s.get("bashIde.shfmt.path") != "":
        raise Reprova("bashIde.shfmt.path ≠ \"\" — o bash-ide registraria o shfmt como formatador de shell "
                      "(o shfmt só roda no check dedicado, com os parâmetros dele)")
    for chave in ("ruff.organizeImports", "ruff.fixAll"):
        if s.get(chave) is not False:
            raise Reprova(f"{chave} ≠ false — o ruff registraria ação de reescrita para Python")
    return ("só [go] formata (gofmt via gopls, sem organizeImports); defaults desligados no workspace: "
            + ("; ".join(origens) or "nenhum"))


def _tags(flags: list) -> set[str]:
    tags: set[str] = set()
    i = 0
    while i < len(flags):
        achado = re.match(r"\A--?tags(?:=(.*))?\Z", str(flags[i]), re.DOTALL)
        if achado:
            valor = achado.group(1)
            if valor is None and i + 1 < len(flags):
                i += 1
                valor = str(flags[i])
            tags.update(t for t in re.split(r"[,\s]+", valor or "") if t)
        i += 1
    return tags


def a3_devcmds(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    flags = _objeto(s, "gopls").get("build.buildFlags")
    if not isinstance(flags, list) or "devcmds" not in _tags(flags):
        raise Reprova(f"gopls build.buildFlags sem -tags=devcmds ({flags!r}) — os arquivos //go:build devcmds "
                      "de cmd/* sairiam 'build constraints exclude all Go files'")
    if "devcmds" not in re.split(r"[,\s]+", str(s.get("go.buildTags", ""))):
        raise Reprova(f"go.buildTags sem devcmds ({s.get('go.buildTags')!r}) — a lente 'run test' do golang.go "
                      "não compilaria os testes de cmd/*")
    if "go.testTags" in s and "devcmds" not in re.split(r"[,\s]+", str(s.get("go.testTags") or "")):
        raise Reprova(f"go.testTags sem devcmds ({s.get('go.testTags')!r}) — nos testes ele substitui go.buildTags")
    return "gopls -tags=devcmds; go.buildTags devcmds"


def versao_toolchain(gomod: Path) -> str:
    try:
        texto = gomod.read_text(encoding="utf-8")
    except OSError as erro:
        raise Reprova(f"go.mod ilegível: {erro}") from None
    achado = re.search(r"(?m)^[ \t]*toolchain[ \t]+(go\S+)", texto)
    if achado is None:
        raise Reprova("go.mod sem linha 'toolchain goX' — nada contra o que conferir go.goroot")
    return achado.group(1)


# [nc -> E2E em :99] Estas chaves só valem com o workspace CONFIÁVEL: o golang.go 0.56.1
# declara untrustedWorkspaces.supported=false (não ativa em Restricted Mode) e lê
# go.alternateTools/go.goroot por workspace.getConfiguration puro (goMain.js,
# getBinPathWithExplanation) — o aviso "Toggle Workspace Trust Flag" do settings.md é de
# 2021 e não existe mais no código; ruff.path e shellcheck.executablePath estão nas
# restrictedConfigurations dos manifestos. O dono confia em /opt/wiki uma vez; a prova de
# que o gopls EM EXECUÇÃO é o de .toolchains/bin (e não o ~/go/bin/gopls go1.25.6) é da E2E:
# `ps -C gopls -o args=` com o codium aberto em /opt/wiki. Esta bancada prova o JSON e o binário.
def a4_toolchain(ctx: Ctx) -> str:
    versao = versao_toolchain(ctx.gomod)
    s = ler_json(ctx.settings)
    goroot = f"{CANONICA}/.toolchains/{versao}"
    if s.get("go.goroot") != goroot:
        raise Reprova(f"go.goroot = {s.get('go.goroot')!r}, esperado {goroot!r} (toolchain {versao} do go.mod)")
    alternativas = _objeto(s, "go.alternateTools")
    if alternativas.get("go") != f"{goroot}/bin/go":
        raise Reprova(f"go.alternateTools.go = {alternativas.get('go')!r}, esperado {goroot + '/bin/go'!r}")
    gopls_bin = f"{CANONICA}/.toolchains/bin/gopls"
    if alternativas.get("gopls") != gopls_bin:
        raise Reprova(f"go.alternateTools.gopls = {alternativas.get('gopls')!r}, esperado {gopls_bin!r} "
                      "(o gopls compilado com o toolchain do repositório)")
    if _objeto(_objeto(s, "gopls"), "build.env").get("GOTOOLCHAIN") != "local":
        raise Reprova("gopls build.env.GOTOOLCHAIN ≠ local — o go do gopls poderia baixar outro toolchain em silêncio")
    return f"go.goroot e go.alternateTools.go = {versao} do go.mod; gopls de .toolchains/bin; GOTOOLCHAIN=local"


def a5_no_save(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    for chave in ("go.vetOnSave", "go.lintOnSave"):
        if s.get(chave) != "off":
            raise Reprova(f"{chave} = {s.get(chave)!r} — tem de ser \"off\": o diagnóstico é o do gopls, e "
                          "'workspace' rodaria full-tree por fora do block-heavy-go.sh")
    for chave in ("go.testOnSave", "go.coverOnSave"):
        if s.get(chave) is True:
            raise Reprova(f"{chave} = true — roda go test a cada save")
    if s.get("go.buildOnSave", "off") != "off":
        raise Reprova(f"go.buildOnSave = {s.get('go.buildOnSave')!r} — compila a cada save")
    return "vet, lint, test, cover e build fora do save"


TASK_PROIBIDO = (
    (re.compile(r"\.\.\."), "padrão recursivo '...' (./..., ./internal/...)"),
    (re.compile(r"(?:\A|[\s\"'])all(?=\Z|[\s\"'])"), "argumento ' all' (cmd/check all, run-check all)"),
    (re.compile(r"lab-cycle"), "lab-cycle"),
    (re.compile(r"check-all"), "tools/check-all"),
    (re.compile(r"--global(?![\w-])"), "--global"),
)


def _textos(no) -> list[str]:
    if isinstance(no, str):
        return [no]
    if isinstance(no, dict):
        return [t for v in no.values() for t in _textos(v)]
    if isinstance(no, list):
        return [t for v in no for t in _textos(v)]
    return []


def a6_tasks(ctx: Ctx) -> str:
    dado = ler_json(ctx.tasks)
    tarefas = dado.get("tasks")
    if dado.get("version") != "2.0.0" or not isinstance(tarefas, list) or not tarefas:
        raise Reprova("tasks.json sem version 2.0.0 ou sem lista de tasks")
    for tarefa in tarefas:
        if not isinstance(tarefa, dict):
            raise Reprova(f"task que não é objeto: {tarefa!r}")
        rotulo = tarefa.get("label", "?")
        for alvo in [tarefa] + [tarefa[p] for p in ("linux", "osx", "windows") if isinstance(tarefa.get(p), dict)]:
            for texto in _textos(alvo.get("command")) + _textos(alvo.get("args")):
                for regex, nome in TASK_PROIBIDO:
                    if regex.search(texto):
                        raise Reprova(f"task {rotulo!r}: {nome} em {texto!r} — full-tree/pesado fica no terminal, "
                                      "envelopado (block-heavy-go.sh)")
            opcoes = alvo.get("runOptions")
            if isinstance(opcoes, dict) and opcoes.get("runOn") == "folderOpen":
                raise Reprova(f"task {rotulo!r} com runOptions.runOn = folderOpen — rodaria sozinha ao abrir o repo")
    s = ler_json(ctx.settings)
    if s.get("go.tasks.provideDefault") is not False:
        raise Reprova("go.tasks.provideDefault ≠ false — o provedor padrão do golang.go põe 'go: build workspace' e "
                      "'go: test workspace' (args ./...) no seletor de tasks")
    return f"{len(tarefas)} tasks sem full-tree nem folderOpen; provedor padrão do golang.go desligado"


# [nc] ".git/**" no watcher: a prova de que o SCM continua vendo /opt/wiki com o .git
# fora do watcher recursivo é da E2E em :99 (o Git.log do editor abre só /opt/wiki —
# ops/ide/testa-ide-ponta-a-ponta.sh), não desta bancada; aqui se confere só a presença.
# Evidência lida em 2026-09-23: a extensão git do VS Code 1.136.1 (o núcleo que o
# VSCodium compila) vigia o .git com RelativePattern(dotGit, "*"), não recursivo, e o
# vscode.d.ts diz que o files.watcherExclude só filtra watcher recursivo.
WATCHER_EXIGIDO = (
    "**/.git/objects/**", "**/.git/subtree-cache/**", "**/node_modules/*/**", ".git/**",
    ".cache/**", ".toolchains/**", ".venv*/**", ".agents/runtime/**", ".artifact-quarantine/**",
    "data/**", "public/**", "robots/**", "bin/**", "deer-flow/**", "var/**", "agent-skills/**",
)
BUSCA_EXIGIDA = (
    "**/node_modules", "**/*.code-search", "**/.git", ".cache/**", ".toolchains/**", ".venv*/**",
    ".artifact-quarantine/**", "public/**", "robots/**", "bin/**", "data/**/*.jsonl", "data/source-snapshots/**",
    ".agents/runtime/**/*.jsonl", ".agents/runtime/tmp_rescue/**", "deer-flow/**", "var/**", "agent-skills/**",
)
GOPLS_FORA = (".git", ".cache", ".toolchains", ".venv", ".agents", ".artifact-quarantine", "data", "public",
              "robots", "bin", "deer-flow", "var", "agent-skills", "qualquer/node_modules")
VISIVEIS_NO_EXPLORER = ("data", "public", ".agents")
CODIGO_VIGIADO = ("internal", "cmd", "tools", "ops", "docs")


def gopls_inclui(filtros: list, caminho: str) -> bool:
    """Semântica do build.directoryFilters do gopls: o último filtro que se aplica decide."""
    incluido = True
    for filtro in filtros:
        filtro = str(filtro)
        if not filtro or filtro[0] not in "+-":
            continue
        prefixo = filtro[1:]
        if prefixo == "" or _glob_para_regex(prefixo + "/**").match(caminho):
            incluido = filtro[0] == "+"
    return incluido


def a7_exclusoes(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    vigia = _objeto(s, "files.watcherExclude")
    faltam = [p for p in WATCHER_EXIGIDO if vigia.get(p) is not True]
    if faltam:
        raise Reprova(f"files.watcherExclude sem {faltam}")
    busca = _objeto(s, "search.exclude")
    faltam = [p for p in BUSCA_EXIGIDA if busca.get(p) is not True]
    if faltam:
        raise Reprova(f"search.exclude sem {faltam}")
    regras_vigia = compilar_exclusoes(vigia)
    regras_busca = compilar_exclusoes(busca)
    for raiz in CODIGO_VIGIADO:
        for nome, regras, so_relativo in (("files.watcherExclude", regras_vigia, False),
                                          ("search.exclude", regras_busca, True)):
            padrao = casa_exclusao(f"{raiz}/x.go", f"{CANONICA}/{raiz}/x.go", regras, so_relativo)
            if padrao:
                raise Reprova(f"{nome} exclui a raiz de código {raiz!r} (padrão {padrao!r})")
    regras_explorer = compilar_exclusoes(_objeto(s, "files.exclude"))
    for raiz in VISIVEIS_NO_EXPLORER:
        for alvo in (raiz, f"{raiz}/x"):
            padrao = casa_exclusao(alvo, f"{CANONICA}/{alvo}", regras_explorer, so_relativo=True)
            if padrao:
                raise Reprova(f"files.exclude esconde {raiz}/ do explorer (padrão {padrao!r}) — só caches saem do explorer")
    filtros = _objeto(s, "gopls").get("build.directoryFilters")
    if not isinstance(filtros, list):
        raise Reprova("gopls build.directoryFilters ausente")
    for raiz in GOPLS_FORA:
        if gopls_inclui(filtros, raiz):
            raise Reprova(f"gopls build.directoryFilters deixa {raiz!r} no workspace do gopls")
    for raiz in ("internal", "cmd", "tools"):
        if not gopls_inclui(filtros, raiz):
            raise Reprova(f"gopls build.directoryFilters exclui a raiz de código {raiz!r}")
    pesadas = raizes_pesadas_descobertas(ctx.disco, regras_vigia)
    if pesadas:
        raise Reprova(f"régua F20: raiz de 1º nível {', '.join(map(repr, pesadas))} com mais de {LIMITE_F20} "
                      f"subdiretórios fora do files.watcherExclude em {ctx.disco} — incluir a raiz (plano §11.4 F20)")
    return (f"watcher {len(WATCHER_EXIGIDO)}, busca {len(BUSCA_EXIGIDA)}, gopls {len(GOPLS_FORA)} exclusões; "
            f"F20 medido em {ctx.disco}: nenhuma raiz com mais de {LIMITE_F20} dirs vigiados fora das de código")


def a8_jsonl(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    valor = _objeto(s, "files.associations").get("*.jsonl")
    if valor != "plaintext":
        raise Reprova(f"files.associations['*.jsonl'] = {valor!r}, esperado 'plaintext' — JSONL de até 157 MB "
                      "não passa por validação de JSON")
    return "*.jsonl -> plaintext"


EXTENSOES_DO_PLANO = ("golang.go", "detachhead.basedpyright", "charliermarsh.ruff", "timonwong.shellcheck",
                      "mads-hartmann.bash-ide-vscode", "usernamehw.errorlens", "continue.continue")
CLAUDE_CODE = "anthropic.claude-code"
# Só fallback: a fonte é ops/ide/extensoes-proibidas.txt (espelho dele em 2026-09-23).
INDESEJADAS = (
    "ms-python.python", "ms-python.debugpy", "ms-python.vscode-pylance", "ms-python.vscode-python-envs",
    "eamodio.gitlens", "mhutchie.git-graph", "gruntfuggly.todo-tree", "yzhang.markdown-all-in-one",
    "editorconfig.editorconfig", "tamasfe.even-better-toml", "redhat.vscode-yaml",
    "davidanson.vscode-markdownlint", "github.copilot", "github.copilot-chat", "saoudrizwan.claude-dev",
    "rooveterinaryinc.roo-cline", "dbaeumer.vscode-eslint", "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss", "christian-kohler.path-intellisense", "dsznajder.es7-react-js-snippets",
    "formulahendry.auto-close-tag", "formulahendry.auto-rename-tag", "ms-vscode.vscode-typescript-next",
    "naumovs.color-highlight",
)
ID_EXTENSAO = re.compile(r"\A[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9-]*\Z")


# Os arquivos do kit se leem POR NOME. Um glob extensoes*.txt absorveu o
# extensoes-proibidas.txt (criado às 09:01 de 2026-09-23) como kit recomendado e deixou
# a asserção 9 vermelha por 25 ids que eram justamente os proibidos; o controle c09a trava.
KIT_RECOMENDADO = ("extensoes.txt", "extensoes-gpu.txt")
KIT_PROIBIDO = "extensoes-proibidas.txt"


def _ids_do_arquivo(arquivo: Path) -> list[str]:
    ids: list[str] = []
    for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
        linha = linha.split("#", 1)[0].strip()
        if not linha:
            continue
        ident = linha.split()[0].split("@", 1)[0].lower()
        if not ID_EXTENSAO.match(ident):
            raise Reprova(f"{arquivo.name}:{numero}: linha fora do formato 'publisher.nome[@versão]': {linha!r}")
        ids.append(ident)
    return ids


def ids_do_kit(kit: Path) -> tuple[list[str], str]:
    arquivos = [kit / nome for nome in KIT_RECOMENDADO if (kit / nome).is_file()]
    if not arquivos:
        return list(EXTENSOES_DO_PLANO), "lista fechada do plano §8 1.2 (ops/ide/extensoes.txt e extensoes-gpu.txt ausentes)"
    return [i for a in arquivos for i in _ids_do_arquivo(a)], " + ".join(a.name for a in arquivos)


def ids_proibidos(kit: Path) -> tuple[list[str], str]:
    arquivo = kit / KIT_PROIBIDO
    if not arquivo.is_file():
        return list(INDESEJADAS), f"AVISO: {REL_KIT}/{KIT_PROIBIDO} ausente — conferido contra a lista embutida"
    return _ids_do_arquivo(arquivo), KIT_PROIBIDO


def a9_recomendacoes(ctx: Ctx) -> str:
    dado = ler_json(ctx.extensions)
    recomendadas = dado.get("recommendations")
    indesejadas = dado.get("unwantedRecommendations")
    if not isinstance(recomendadas, list) or not isinstance(indesejadas, list):
        raise Reprova("extensions.json sem as listas recommendations e unwantedRecommendations")
    fora = [x for x in recomendadas + indesejadas if not isinstance(x, str) or x != x.lower()]
    if fora:
        raise Reprova(f"ids fora de minúsculas: {fora}")
    if len(set(recomendadas)) != len(recomendadas):
        raise Reprova("recomendação duplicada")
    kit, origem = ids_do_kit(ctx.kit)
    esperado = set(kit) | {CLAUDE_CODE}
    if set(recomendadas) != esperado:
        raise Reprova(f"recomendações ≠ kit + {CLAUDE_CODE} ({origem}): faltam {sorted(esperado - set(recomendadas))}, "
                      f"sobram {sorted(set(recomendadas) - esperado)}")
    comuns = sorted(set(recomendadas) & set(indesejadas))
    if comuns:
        raise Reprova(f"recomendação também está nas indesejadas: {comuns}")
    proibidas, origem_proibidas = ids_proibidos(ctx.kit)
    comuns = sorted(set(recomendadas) & set(proibidas))
    if comuns:
        raise Reprova(f"recomendação proibida pelo kit ({origem_proibidas}): {comuns}")
    faltam = [x for x in proibidas if x not in indesejadas]
    if faltam:
        raise Reprova(f"unwantedRecommendations sem {faltam} (fonte: {origem_proibidas})")
    for linguagem, bloco in _linguagens(ler_json(ctx.settings)).items():
        formatador = bloco.get("editor.defaultFormatter")
        if formatador is not None and formatador not in recomendadas:
            raise Reprova(f"[{linguagem}] editor.defaultFormatter = {formatador!r} não é extensão recomendada")
    return (f"{len(recomendadas)} recomendações == {origem} + claude-code; {len(indesejadas)} indesejadas ⊇ "
            f"{len(proibidas)} de {origem_proibidas}, sem interseção")


PERFIL_WATCHER_EXIGIDO = tuple(f"{CANONICA}/{r}/**" for r in (
    ".agents", "public", ".cache", "var", ".toolchains", "data", ".venv*", ".git", "robots", ".artifact-quarantine"))
# Perfil de referência (plano §8 1.3 + raízes medidas em 2026-09-23): base dos mutantes
# da asserção 10 enquanto ops/ide/perfil/settings.json não existir.
# Caminhos (relativos ao workspace) que o search.exclude do perfil tem de excluir DE FATO:
# o .venv de hoje e o .venv-tools311 que o provisionar.sh cria na máquina nova.
PERFIL_BUSCA_VENV = (".venv/lib/x.py", ".venv-tools311/lib/x.py")
PERFIL_REFERENCIA = {
    "telemetry.telemetryLevel": "off",
    "update.mode": "none",
    "extensions.autoUpdate": False,
    "extensions.autoCheckUpdates": False,
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.profiles.linux": {"bash": {"path": "/usr/bin/bash", "args": ["-l"]}},
    "claudeCode.useTerminal": False,
    "claudeCode.continueAfterReload": False,
    "claudeCode.usePythonEnvironment": False,
    "files.watcherExclude": {**{p: True for p in PERFIL_WATCHER_EXIGIDO},
                             "**/.git/objects/**": True, "**/node_modules/*/**": True},
    "search.exclude": {"**/.venv*/**": True},
}


def a10_perfil(ctx: Ctx) -> str:
    if not ctx.perfil.exists():
        raise Pulada(f"{REL_PERFIL} ainda não existe (arquivo do kit, frente 1/6)")
    texto = ctx.perfil.read_text(encoding="utf-8")
    p = ler_json(ctx.perfil)
    for chave, esperado in (("extensions.autoUpdate", False), ("extensions.autoCheckUpdates", False),
                            ("update.mode", "none"), ("claudeCode.usePythonEnvironment", False)):
        if p.get(chave) != esperado or type(p.get(chave)) is not type(esperado):
            raise Reprova(f"perfil: {chave} = {p.get(chave)!r}, esperado {esperado!r}")
    for chave, motivo in (("claudeCode.initialPermissionMode", "não aceita 'auto'; ausente, a extensão herda o 'auto' do usuário"),
                          ("claudeCode.claudeProcessWrapper", "o binário embutido seria passado como prompt ao wrapper ~/bin/claude")):
        if chave in p:
            raise Reprova(f"perfil define {chave} — {motivo}")
    perfis = _objeto(p, "terminal.integrated.profiles.linux")
    padrao = p.get("terminal.integrated.defaultProfile.linux")
    escolhido = perfis.get(padrao) if isinstance(padrao, str) else None
    argumentos = escolhido.get("args") if isinstance(escolhido, dict) else None
    if (not isinstance(escolhido, dict) or os.path.basename(str(escolhido.get("path", ""))) != "bash"
            or not isinstance(argumentos, list) or not ({"-l", "--login"} & set(argumentos))):
        raise Reprova(f"perfil: terminal padrão não é bash -l ({padrao!r}: {escolhido!r})")
    if "start-ai-terminal" in texto:
        raise Reprova("perfil menciona start-ai-terminal — o terminal integrado é bash -l; o launcher anexaria "
                      "a sessão tmux do ai-pane e um segundo cliente a redimensiona")
    vigia = _objeto(p, "files.watcherExclude")
    faltam = [x for x in PERFIL_WATCHER_EXIGIDO if vigia.get(x) is not True]
    if faltam:
        raise Reprova(f"perfil: files.watcherExclude sem {faltam}")
    busca = _objeto(p, "search.exclude")
    regras = compilar_exclusoes(busca)
    for alvo in PERFIL_BUSCA_VENV:
        if casa_exclusao(alvo, f"{CANONICA}/{alvo}", regras, so_relativo=True) is None:
            mortas = sorted(k for k, v in busca.items() if v is True and k.startswith("/"))
            raise Reprova(f"perfil: search.exclude não exclui {alvo!r} na busca"
                          + (f" — a(s) chave(s) {mortas} é(são) caminho absoluto, e o VS Code avalia search.exclude "
                             "relativo à pasta do workspace (glob-patterns.md:45; rg do VS Code medido): "
                             "use '**/.venv*/**'" if mortas else " — falta '**/.venv*/**' (rule ide-e-editor.md:24)"))
    return ("sem auto-update, update.mode none, sem initialPermissionMode/claudeProcessWrapper, bash -l, "
            "watcherExclude absoluto, .venv* fora da busca")


USER_SITE_311 = "/home/rafael/.local/lib/python3.11/site-packages"
VENV_TOOLS_311 = ".venv-tools311/lib/python3.11/site-packages"
PYRIGHT_EXCLUDE = ("data", "public", "robots", "bin", "deer-flow", "var", "agent-skills", ".artifact-quarantine")
APONTA_VENV_DA_RAIZ = re.compile(r"(?:\A|/)\.venv(?:/|\Z)")


def a11_pyright(ctx: Ctx) -> str:
    c = ler_json(ctx.pyright)
    for chave in ("venv", "venvPath"):
        if chave in c:
            raise Reprova(f"pyrightconfig.json define {chave!r} — o .venv da raiz é CPython 3.12 só com numpy; "
                          "as tools rodam no python3 3.11 com o user site")
    if c.get("pythonVersion") != "3.11":
        raise Reprova(f"pyrightconfig.json pythonVersion = {c.get('pythonVersion')!r}, esperado '3.11'")
    if c.get("typeCheckingMode") != "off":
        raise Reprova(f"pyrightconfig.json typeCheckingMode = {c.get('typeCheckingMode')!r}, esperado 'off' "
                      "(o gate de tipos é o mypy do repo)")
    extras = c.get("extraPaths") if isinstance(c.get("extraPaths"), list) else []
    faltam = [x for x in (USER_SITE_311, VENV_TOOLS_311) if x not in extras]
    if faltam:
        raise Reprova(f"pyrightconfig.json extraPaths sem {faltam}")
    inclui = c.get("include") if isinstance(c.get("include"), list) else []
    if not inclui or any(str(x).strip() in ("", ".", "./", "**", "*") for x in inclui):
        raise Reprova(f"pyrightconfig.json include = {inclui!r} — analisar a raiz inteira varreria data/ e public/")
    exclui = c.get("exclude") if isinstance(c.get("exclude"), list) else []
    faltam = [x for x in PYRIGHT_EXCLUDE if x not in exclui]
    if faltam:
        raise Reprova(f"pyrightconfig.json exclude sem {faltam}")
    s = ler_json(ctx.settings)
    for chave in ("python.defaultInterpreterPath", "python.pythonPath", "python.venvPath"):
        if chave in s and APONTA_VENV_DA_RAIZ.search(str(s[chave])):
            raise Reprova(f"settings.json aponta {chave} para o .venv da raiz ({s[chave]!r})")
    return "sem venv; pythonVersion 3.11; typeCheckingMode off; extraPaths user site 3.11 + .venv-tools311"


DOC_NUCLEO = "https://code.visualstudio.com/docs/reference/default-settings"  # 'Open Default Settings (JSON)'
DOC_GIT = "https://github.com/microsoft/vscode/blob/main/extensions/git/package.json"
NATIVAS: dict[str, tuple[str, dict]] = {
    "files.watcherExclude": (DOC_NUCLEO, {"type": "object"}),
    "search.exclude": (DOC_NUCLEO, {"type": "object"}),
    "files.exclude": (DOC_NUCLEO, {"type": "object"}),
    "files.associations": (DOC_NUCLEO, {"type": "object"}),
    "editor.largeFileOptimizations": (DOC_NUCLEO, {"type": "boolean"}),
    "editor.formatOnSave": (DOC_NUCLEO, {"type": "boolean"}),
    "editor.formatOnPaste": (DOC_NUCLEO, {"type": "boolean"}),
    "editor.formatOnType": (DOC_NUCLEO, {"type": "boolean"}),
    "editor.defaultFormatter": (DOC_NUCLEO, {"type": ["string", "null"]}),
    "editor.codeActionsOnSave": (DOC_NUCLEO, {"type": ["object", "array"]}),
    "files.trimTrailingWhitespace": (DOC_NUCLEO, {"type": "boolean"}),
    "files.insertFinalNewline": (DOC_NUCLEO, {"type": "boolean"}),
    "files.trimFinalNewlines": (DOC_NUCLEO, {"type": "boolean"}),
    "git.autoRepositoryDetection": (DOC_GIT, {"type": ["boolean", "string"],
                                              "enum": [True, False, "subFolders", "openEditors"]}),
}
# Ids de linguagem embutidos, conferidos nas extensões do VS Code 1.136.1 (o núcleo que o
# VSCodium compila); 'plaintext' é do núcleo.
LINGUAGENS_CONHECIDAS = frozenset({
    "go", "python", "shellscript", "markdown", "json", "jsonc", "yaml", "html", "css", "javascript",
    "typescript", "plaintext", "makefile", "dockerfile", "ini", "xml", "sql", "properties", "log",
    "diff", "git-commit", "ignore"})
# Chaves que entraram no workspace fora do §8 3.1, cada uma confirmada em fonte primária
# (manifesto da versão fixada, ou o núcleo do editor): a saída mostra de onde cada uma veio.
CHAVES_DO_DESVIO = ("go.tasks.provideDefault", "shellcheck.customArgs", "shellcheck.useWorkspaceRootAsCwd",
                    "bashIde.shfmt.path", "bashIde.backgroundAnalysisIgnore", "[python] editor.formatOnType")
TIPOS_JSON = {"string": (str,), "boolean": (bool,), "array": (list,), "object": (dict,), "null": (type(None),)}


def confere_valor(valor, esquema: dict) -> str | None:
    if "enum" in esquema and not any(type(valor) is type(e) and valor == e for e in esquema["enum"]):
        return f"fora do enum {esquema['enum']}"
    tipos = esquema.get("type")
    if tipos:
        tipos = [tipos] if isinstance(tipos, str) else list(tipos)
        for tipo in tipos:
            if tipo in ("number", "integer"):
                if isinstance(valor, (int, float)) and not isinstance(valor, bool) and (tipo == "number" or isinstance(valor, int)):
                    return None
            elif tipo in TIPOS_JSON and isinstance(valor, TIPOS_JSON[tipo]):
                return None
        return f"tipo {type(valor).__name__} fora de {tipos}"
    return None


def a12_chaves(ctx: Ctx) -> str:
    s = ler_json(ctx.settings)
    lidos, origem = manifestos(ctx)
    contribuidas: dict[str, tuple[str, dict]] = {}
    for ident, manifesto in sorted(lidos.items()):
        for chave, esquema in manifesto["propriedades"].items():
            contribuidas.setdefault(chave, (ident, esquema if isinstance(esquema, dict) else {}))
    problemas: list[str] = []
    donos: dict[str, str] = {}

    def conferir(chave: str, valor, onde: str) -> None:
        if chave in NATIVAS:
            dono, esquema = NATIVAS[chave]
        elif chave in contribuidas:
            dono, esquema = contribuidas[chave]
        else:
            problemas.append(f"{onde}{chave}: não existe em nenhuma extensão ({origem}) nem na lista de nativas")
            return
        donos[f"{onde}{chave}"] = dono
        erro = confere_valor(valor, esquema)
        if erro:
            problemas.append(f"{onde}{chave} = {valor!r}: {erro} ({dono})")
        filhos = esquema.get("properties")
        if (isinstance(valor, dict) and isinstance(filhos, dict)
                and esquema.get("additionalProperties") is not True and "patternProperties" not in esquema):
            for subchave, subvalor in valor.items():
                if subchave not in filhos:
                    problemas.append(f"{onde}{chave}.{subchave}: não existe no esquema de {chave} ({dono})")
                    continue
                erro = confere_valor(subvalor, filhos[subchave] if isinstance(filhos[subchave], dict) else {})
                if erro:
                    problemas.append(f"{onde}{chave}.{subchave} = {subvalor!r}: {erro} ({dono})")

    for chave, valor in s.items():
        if chave.startswith("["):
            for linguagem in re.findall(r"\[([^\]]+)\]", chave):
                if linguagem not in LINGUAGENS_CONHECIDAS:
                    problemas.append(f"{chave}: linguagem {linguagem!r} desconhecida")
            if isinstance(valor, dict):
                for subchave, subvalor in valor.items():
                    conferir(subchave, subvalor, f"{chave} ")
            continue
        conferir(chave, valor, "")
    if problemas:
        raise Reprova("; ".join(problemas))
    total = sum(1 for k in s if not k.startswith("["))
    novas = "; ".join(f"{k} <- {donos[k]}" for k in CHAVES_DO_DESVIO if k in donos)
    return f"{total} chaves de topo + blocos de linguagem conferidos contra {origem}; chaves novas do desvio: {novas}"


def go_para_ler_buildinfo(versao: str) -> str | None:
    """Qualquer go >= 1.18 lê o buildinfo; prefere o do toolchain do go.mod."""
    candidatos = [RAIZ / ".toolchains" / versao / "bin" / "go"]
    candidatos += sorted((RAIZ / ".toolchains").glob("go*/bin/go"), reverse=True)
    for candidato in candidatos:
        if candidato.is_file() and os.access(candidato, os.X_OK):
            return str(candidato)
    return shutil.which("go")


def buildinfo(binario: Path, versao: str) -> tuple[str, str, str]:
    """(versão do Go, caminho do pacote main, versão do módulo) por `go version -m`."""
    go = go_para_ler_buildinfo(versao)
    if go is None:
        raise Pulada("nenhum binário go neste host para rodar `go version -m`")
    try:
        processo = subprocess.run([go, "version", "-m", str(binario)], capture_output=True, text=True, timeout=60,
                                  cwd="/", env={**os.environ, "GOTOOLCHAIN": "local"})
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise Reprova(f"`go version -m {binario}` não rodou: {erro}") from None
    linhas = processo.stdout.splitlines()
    achado = re.search(r":\s+(go\S+)\s*\Z", linhas[0]) if processo.returncode == 0 and linhas else None
    if achado is None:
        raise Reprova(f"`{go} version -m {binario}` saiu {processo.returncode} sem versão do Go: "
                      f"{(processo.stdout + processo.stderr).strip()[:300]!r}")
    campos = [linha.split("\t") for linha in linhas[1:]]
    caminho = next((c[2] for c in campos if len(c) > 2 and c[1] == "path"), "")
    modulo = next((c[3] for c in campos if len(c) > 3 and c[1] == "mod"), "")
    return achado.group(1), caminho, modulo


def a13_gopls_binario(ctx: Ctx) -> str:
    versao = versao_toolchain(ctx.gomod)
    if ctx.gopls_bin is None or not ctx.gopls_bin.is_file():
        raise Pulada(f"{ctx.gopls_bin} ausente — o kit o compila com GOBIN={CANONICA}/.toolchains/bin "
                     "(frente 3, pré-passo)")
    go_do_binario, caminho, modulo = buildinfo(ctx.gopls_bin, versao)
    if go_do_binario != versao:
        raise Reprova(f"{ctx.gopls_bin} compilado com {go_do_binario}, o go.mod pede {versao} — recompilar com "
                      f"GOBIN={CANONICA}/.toolchains/bin GOTOOLCHAIN=local {CANONICA}/.toolchains/{versao}/bin/go "
                      "install golang.org/x/tools/gopls@<versão>")
    if ctx.gopls_modulo and caminho != ctx.gopls_modulo:
        raise Reprova(f"{ctx.gopls_bin} é o pacote {caminho!r}, não {ctx.gopls_modulo}")
    return f"`go version -m {ctx.gopls_bin}`: {go_do_binario} == toolchain do go.mod; {caminho} {modulo}".rstrip()


ASSERCOES: list[tuple[int, str, Callable[[Ctx], str]]] = [
    (1, "os JSON do workspace parseiam", a1_json),
    (2, "formatação automática só em [go]", a2_formatacao),
    (3, "-tags=devcmds no gopls", a3_devcmds),
    (4, "toolchain do go.mod no go.goroot/alternateTools", a4_toolchain),
    (5, "vet e lint fora do save", a5_no_save),
    (6, "nenhuma task full-tree nem automática", a6_tasks),
    (7, "exclusões exigidas e régua F20 no disco", a7_exclusoes),
    (8, "*.jsonl como plaintext", a8_jsonl),
    (9, "recomendações == kit + claude-code", a9_recomendacoes),
    (10, "perfil global do kit", a10_perfil),
    (11, "pyrightconfig sem .venv, Python 3.11", a11_pyright),
    (12, "nenhuma chave inventada", a12_chaves),
    (13, "gopls compilado com o toolchain do go.mod", a13_gopls_binario),
]


def rodar(ctx: Ctx) -> list[tuple[int, str, str, str]]:
    resultados = []
    for numero, titulo, funcao in ASSERCOES:
        try:
            resultados.append((numero, "ok", titulo, funcao(ctx)))
        except Pulada as erro:
            resultados.append((numero, "pulada", titulo, str(erro)))
        except Reprova as erro:
            resultados.append((numero, "FALHOU", titulo, str(erro)))
    return resultados


GOPLS_MODULO = "golang.org/x/tools/gopls"


def ctx_real() -> Ctx:
    variavel = os.environ.get("IDE_EXTENSIONS_DIR")
    dir_ext = Path(variavel or DIR_EXT_PADRAO).expanduser()
    if variavel and not dir_ext.is_dir():
        raise SystemExit(f"IDE_EXTENSIONS_DIR={variavel} não é diretório")
    return Ctx(settings=RAIZ / REL_SETTINGS, extensions=RAIZ / REL_EXTENSIONS, tasks=RAIZ / REL_TASKS,
               pyright=RAIZ / REL_PYRIGHT, gomod=RAIZ / "go.mod", perfil=RAIZ / REL_PERFIL, kit=RAIZ / REL_KIT,
               disco=RAIZ, dir_ext=dir_ext if dir_ext.is_dir() else None,
               dirs_embutidas=[Path(d) for d in DIRS_EMBUTIDAS if Path(d).is_dir()],
               gopls_bin=Path(CANONICA) / ".toolchains/bin/gopls", gopls_modulo=GOPLS_MODULO)


# --------------------------------------------------------------------------
# Bancada de mutação

class Mutante:
    def __init__(self, ident: str, alvo: int, descricao: str, aplicar: Callable[[Path, Ctx], None],
                 espera: tuple[str, ...]) -> None:
        self.ident = ident
        self.alvo = alvo
        self.descricao = descricao
        self.aplicar = aplicar
        self.espera = espera


def _jmut(rel: str, funcao: Callable[[dict], object]) -> Callable[[Path, Ctx], None]:
    """Muta o JSON NO LUGAR. O retorno da função é ignorado de propósito: com lambda,
    `d.pop(k)` devolve o valor retirado, e usá-lo como documento gravava o valor no
    lugar do arquivo inteiro (m07k e m10k morriam pelo motivo errado)."""
    def aplicar(d: Path, ctx: Ctx) -> None:
        caminho = d / rel
        antes = caminho.read_text(encoding="utf-8")
        dado = json.loads(antes)
        funcao(dado)
        texto = json.dumps(dado, indent=2, ensure_ascii=False) + "\n"
        if json.loads(texto) == json.loads(antes):
            raise RuntimeError(f"mutante nulo: {rel} ficou igual")
        caminho.write_text(texto, encoding="utf-8")
    return aplicar


def _tmut(rel: str, funcao: Callable[[str], str]) -> Callable[[Path, Ctx], None]:
    def aplicar(d: Path, ctx: Ctx) -> None:
        caminho = d / rel
        antes = caminho.read_text(encoding="utf-8")
        depois = funcao(antes)
        if depois == antes:
            raise RuntimeError(f"mutante nulo: {rel} ficou igual")
        caminho.write_text(depois, encoding="utf-8")
    return aplicar


def _pondo(caminho: tuple[str, ...], valor) -> Callable[[dict], None]:
    def funcao(dado: dict) -> None:
        alvo = dado
        for passo in caminho[:-1]:
            alvo = alvo[passo]
        alvo[caminho[-1]] = valor
    return funcao


def _tirando(caminho: tuple[str, ...]) -> Callable[[dict], None]:
    def funcao(dado: dict) -> None:
        alvo = dado
        for passo in caminho[:-1]:
            alvo = alvo[passo]
        del alvo[caminho[-1]]
    return funcao


def _versao_vizinha(versao: str, passo: int) -> str:
    achado = re.fullmatch(r"go(\d+)\.(\d+)\.(\d+)", versao)
    if achado is None:
        return versao + "-outra"
    maior, menor, patch = map(int, achado.groups())
    patch = patch + passo if patch + passo >= 0 else patch + 1
    return f"go{maior}.{menor}.{patch}"


def _nova_task(comando: str, **extra) -> Callable[[dict], None]:
    def funcao(dado: dict) -> None:
        dado["tasks"].append({"label": "mutante", "type": "shell", "command": comando, **extra})
    return funcao


def _lista_sem(chave: str, item: str) -> Callable[[dict], None]:
    def funcao(dado: dict) -> None:
        dado[chave].remove(item)
    return funcao


def _criar_arvore(raiz: Path, rel: str, quantos: int) -> None:
    base = raiz / rel
    for i in range(quantos):
        (base / f"d{i:04d}").mkdir(parents=True, exist_ok=True)


def _disco_novo(nome: str, arvores: list[tuple[str, int]]) -> Callable[[Path, Ctx], None]:
    def aplicar(d: Path, ctx: Ctx) -> None:
        disco = d / nome
        for rel, quantos in arvores:
            _criar_arvore(disco, rel, quantos)
        ctx.disco = disco
    return aplicar


def _kit_cresce(d: Path, ctx: Ctx) -> None:
    arquivo = ctx.kit / "extensoes.txt"
    ctx.kit.mkdir(parents=True, exist_ok=True)
    base = arquivo.read_text(encoding="utf-8") if arquivo.exists() else "".join(f"{x}@0\n" for x in EXTENSOES_DO_PLANO)
    arquivo.write_text(base.rstrip("\n") + "\npublisher.nova@1.0.0\n", encoding="utf-8")


def _kit_e_recomendacao_indesejada(d: Path, ctx: Ctx) -> None:
    arquivo = ctx.kit / "extensoes.txt"
    ctx.kit.mkdir(parents=True, exist_ok=True)
    base = arquivo.read_text(encoding="utf-8") if arquivo.exists() else "".join(f"{x}@0\n" for x in EXTENSOES_DO_PLANO)
    arquivo.write_text(base.rstrip("\n") + "\nms-python.python@2026.4.0\n", encoding="utf-8")
    _jmut(REL_EXTENSIONS, lambda e: e["recommendations"].append("ms-python.python"))(d, ctx)


def _sem_manifesto_do_go(d: Path, ctx: Ctx) -> None:
    alvos = [p for p in (d / "ext").iterdir() if p.name.startswith("golang.go-")]
    if not alvos:
        raise RuntimeError("mutante nulo: fixture sem golang.go")
    for alvo in alvos:
        shutil.rmtree(alvo)


def _sobe_toolchain(texto: str) -> str:
    versao = re.search(r"(?m)^[ \t]*toolchain[ \t]+(go\S+)", texto).group(1)
    return re.sub(r"(?m)^([ \t]*toolchain[ \t]+)go\S+", lambda m: m.group(1) + _versao_vizinha(versao, +1), texto)


def binario_go_de_outra_versao(versao: str) -> tuple[Path, str] | None:
    """Um binário Go real deste host compilado com OUTRA versão do Go — o gopls velho do
    ~/go/bin (go1.25.6 em 2026-09-23) ou o gofmt de outro toolchain em .toolchains/."""
    candidatos = [Path.home() / "go/bin/gopls"] + sorted((RAIZ / ".toolchains").glob("go*/bin/gofmt"))
    for candidato in candidatos:
        if not candidato.is_file():
            continue
        try:
            outra = buildinfo(candidato, versao)[0]
        except (Reprova, Pulada):
            continue
        if outra != versao:
            return candidato, outra
    return None


def _usando_gopls(binario: Path, modulo: str | None) -> Callable[[Path, Ctx], None]:
    def aplicar(d: Path, ctx: Ctx) -> None:
        if ctx.gopls_bin == binario:
            raise RuntimeError("mutante nulo: o binário já é esse")
        ctx.gopls_bin = binario
        ctx.gopls_modulo = modulo
    return aplicar


def mutantes_do_gopls(versao: str, bancada: "Bancada") -> list[Mutante]:
    if bancada.gopls_bin is None:
        return []
    lista = [Mutante("m13a", 13, "go.mod sobe o toolchain e o gopls fica", _tmut("go.mod", _sobe_toolchain),
                     ("compilado com", f"o go.mod pede {_versao_vizinha(versao, +1)}"))]
    outro = binario_go_de_outra_versao(versao)
    if outro is not None:
        binario, outra = outro
        lista.append(Mutante("m13b", 13, f"binário real de outra versão do Go ({binario}, {outra})",
                             _usando_gopls(binario, bancada.gopls_modulo), (f"compilado com {outra}",)))
    go_do_toolchain = RAIZ / ".toolchains" / versao / "bin" / "go"
    if bancada.gopls_modulo and go_do_toolchain.is_file():
        lista.append(Mutante("m13c", 13, "binário da mesma versão que não é o gopls (o go do toolchain)",
                             _usando_gopls(go_do_toolchain, bancada.gopls_modulo), ("é o pacote 'cmd/go'",)))
    return lista


def mutantes(versao: str, bancada: "Bancada") -> list[Mutante]:
    S, E, T, P, F = REL_SETTINGS, REL_EXTENSIONS, REL_TASKS, REL_PYRIGHT, "perfil.json"
    goroot_velho = f"{CANONICA}/.toolchains/{_versao_vizinha(versao, -1)}"
    return mutantes_do_gopls(versao, bancada) + [
        Mutante("m01a", 1, "comentário JSONC em settings.json", _tmut(S, lambda t: t.replace("{\n", "{\n  // comentário\n", 1)), ("JSON inválido",)),
        Mutante("m01b", 1, "vírgula final em extensions.json", _tmut(E, lambda t: t.rstrip().rstrip("}").rstrip() + ",\n}\n"), ("JSON inválido",)),
        Mutante("m01c", 1, "chave duplicada em settings.json", _tmut(S, lambda t: t.replace("{\n", '{\n  "files.associations": {"*.jsonl": "json"},\n', 1)), ("chave duplicada",)),
        Mutante("m02a", 2, "formatOnSave global ligado", _jmut(S, _pondo(("editor.formatOnSave",), True)), ("editor.formatOnSave global",)),
        Mutante("m02b", 2, "[python] formatOnSave ligado", _jmut(S, _pondo(("[python]", "editor.formatOnSave"), True)), ("[python] editor.formatOnSave = true",)),
        Mutante("m02c", 2, "[go] organizeImports explicit", _jmut(S, _pondo(("[go]", "editor.codeActionsOnSave", "source.organizeImports"), "explicit")), ("[go] editor.codeActionsOnSave.source.organizeImports = 'explicit'",)),
        Mutante("m02d", 2, "trimTrailingWhitespace ligado", _jmut(S, _pondo(("files.trimTrailingWhitespace",), True)), ("files.trimTrailingWhitespace = true",)),
        Mutante("m02e", 2, "[go] sem gofmt no save", _jmut(S, _pondo(("[go]", "editor.formatOnSave"), False)), ("[go] tem de formatar",)),
        Mutante("m02f", 2, "gofumpt ligado", _jmut(S, _pondo(("gopls", "formatting.gofumpt"), True)), ("formatting.gofumpt",)),
        Mutante("m02g", 2, "shfmt do bash-ide ligado", _jmut(S, _pondo(("bashIde.shfmt.path",), "shfmt")), ("bashIde.shfmt.path",)),
        Mutante("m02h", 2, "[python] sem desligar o formatOnType do basedpyright", _jmut(S, _tirando(("[python]", "editor.formatOnType"))), ("liga [python] editor.formatOnType por default",)),
        Mutante("m02i", 2, "[markdown] formatOnSave ligado", _jmut(S, _pondo(("[markdown]",), {"editor.formatOnSave": True})), ("[markdown] editor.formatOnSave = true",)),
        Mutante("m02j", 2, "[go] sem desligar o organizeImports do golang.go", _jmut(S, _tirando(("[go]", "editor.codeActionsOnSave"))), ("liga [go] editor.codeActionsOnSave.source.organizeImports",)),
        Mutante("m02k", 2, "ruff.fixAll ligado", _jmut(S, _pondo(("ruff.fixAll",), True)), ("ruff.fixAll",)),
        Mutante("m03a", 3, "buildFlags vazio", _jmut(S, _pondo(("gopls", "build.buildFlags"), [])), ("build.buildFlags sem -tags=devcmds",)),
        Mutante("m03b", 3, "tag com erro de digitação", _jmut(S, _pondo(("gopls", "build.buildFlags"), ["-tags=devcmd"])), ("build.buildFlags sem -tags=devcmds",)),
        Mutante("m03c", 3, "go.buildTags vazio", _jmut(S, _pondo(("go.buildTags",), "")), ("go.buildTags sem devcmds",)),
        Mutante("m03d", 3, "go.testTags sem devcmds", _jmut(S, _pondo(("go.testTags",), "integration")), ("go.testTags sem devcmds",)),
        Mutante("m04a", 4, "go.goroot no toolchain vizinho", _jmut(S, _pondo(("go.goroot",), goroot_velho)), ("go.goroot = ",)),
        Mutante("m04b", 4, "go.alternateTools.go do sistema", _jmut(S, _pondo(("go.alternateTools", "go"), "/usr/bin/go")), ("go.alternateTools.go = '/usr/bin/go'",)),
        Mutante("m04c", 4, "go.mod sobe o toolchain e o settings fica", _tmut("go.mod", _sobe_toolchain), ("go.goroot = ", _versao_vizinha(versao, +1))),
        Mutante("m04d", 4, "sem GOTOOLCHAIN=local", _jmut(S, _tirando(("gopls", "build.env", "GOTOOLCHAIN"))), ("GOTOOLCHAIN",)),
        Mutante("m04e", 4, "gopls do PATH", _jmut(S, _pondo(("go.alternateTools", "gopls"), "gopls")), ("go.alternateTools.gopls = 'gopls'",)),
        Mutante("m05a", 5, "vetOnSave workspace", _jmut(S, _pondo(("go.vetOnSave",), "workspace")), ("go.vetOnSave = 'workspace'",)),
        Mutante("m05b", 5, "lintOnSave package", _jmut(S, _pondo(("go.lintOnSave",), "package")), ("go.lintOnSave = 'package'",)),
        Mutante("m05c", 5, "testOnSave ligado", _jmut(S, _pondo(("go.testOnSave",), True)), ("go.testOnSave = true",)),
        Mutante("m06a", 6, "task go test ./...", _jmut(T, _nova_task("./tools/go-modern test -count=1 ./...")), ("padrão recursivo",)),
        Mutante("m06b", 6, "task com runOn folderOpen", _jmut(T, lambda d: d["tasks"][0].update({"runOptions": {"runOn": "folderOpen"}})), ("runOn = folderOpen",)),
        Mutante("m06c", 6, "task cmd/check all", _jmut(T, _nova_task("./tools/go-modern run ./cmd/check all")), ("argumento ' all'",)),
        Mutante("m06d", 6, "task lab-cycle", _jmut(T, _nova_task("./tools/lab-cycle")), ("lab-cycle",)),
        Mutante("m06e", 6, "task auditoria --global", _jmut(T, _nova_task("python3 tools/audit_v2_pages.py --global")), ("--global",)),
        Mutante("m06f", 6, "provedor padrão do golang.go ligado", _jmut(S, _pondo(("go.tasks.provideDefault",), True)), ("go.tasks.provideDefault",)),
        Mutante("m06g", 6, "task tipo go com args ./internal/...", _jmut(T, lambda d: d["tasks"].append({"label": "mutante", "type": "go", "command": "test", "args": ["./internal/..."]})), ("padrão recursivo",)),
        Mutante("m07a", 7, "watcher sem data/**", _jmut(S, _tirando(("files.watcherExclude", "data/**"))), ("files.watcherExclude sem", "data/**")),
        Mutante("m07b", 7, "busca sem .agents/runtime/**/*.jsonl", _jmut(S, _tirando(("search.exclude", ".agents/runtime/**/*.jsonl"))), ("search.exclude sem", ".agents/runtime/**/*.jsonl")),
        Mutante("m07c", 7, "explorer esconde data", _jmut(S, _pondo(("files.exclude", "data"), True)), ("files.exclude esconde data/",)),
        Mutante("m07d", 7, "explorer esconde **/public", _jmut(S, _pondo(("files.exclude", "**/public"), True)), ("files.exclude esconde public/",)),
        Mutante("m07e", 7, "gopls sem -.agents", _jmut(S, lambda d: d["gopls"]["build.directoryFilters"].remove("-.agents")), ("directoryFilters deixa '.agents'",)),
        Mutante("m07f", 7, "raiz pesada nova fora do watcher (disco sintético)", _disco_novo("disco-f20", [("pesada", LIMITE_F20 + 1), ("internal", LIMITE_F20 + 1)]), ("régua F20", "'pesada'")),
        Mutante("m07g", 7, "gopls reinclui data com +data", _jmut(S, lambda d: d["gopls"]["build.directoryFilters"].append("+data")), ("directoryFilters deixa 'data'",)),
        Mutante("m07h", 7, ".agents pesado fora de runtime (disco sintético)", _disco_novo("disco-agents", [(".agents/runtime", 5), (".agents/outra", LIMITE_F20 + 1)]), ("régua F20", "'.agents'")),
        Mutante("m07i", 7, "gopls exclui tudo com '-' inicial", _jmut(S, lambda d: d["gopls"]["build.directoryFilters"].insert(0, "-")), ("exclui a raiz de código 'internal'",)),
        Mutante("m07j", 7, "watcher exclui internal/**", _jmut(S, _pondo(("files.watcherExclude", "internal/**"), True)), ("files.watcherExclude exclui a raiz de código 'internal'",)),
        Mutante("m07k", 7, "watcher volta a .venv/** (perde o .venv-tools311)", _jmut(S, lambda d: d["files.watcherExclude"].update({".venv/**": d["files.watcherExclude"].pop(".venv*/**")})), ("files.watcherExclude sem", ".venv*/**")),
        Mutante("m07l", 7, "busca sem .venv*/**", _jmut(S, _tirando(("search.exclude", ".venv*/**"))), ("search.exclude sem", ".venv*/**")),
        Mutante("m08a", 8, "*.jsonl como json", _jmut(S, _pondo(("files.associations", "*.jsonl"), "json")), ("*.jsonl",)),
        Mutante("m08b", 8, "sem files.associations", _jmut(S, _tirando(("files.associations",))), ("*.jsonl",)),
        Mutante("m09a", 9, "recomendação sem golang.go", _jmut(E, _lista_sem("recommendations", "golang.go")), ("faltam ['golang.go']",)),
        Mutante("m09b", 9, "recomenda ms-python.python", _jmut(E, lambda d: d["recommendations"].append("ms-python.python")), ("sobram ['ms-python.python']",)),
        Mutante("m09c", 9, "id com maiúscula", _jmut(E, lambda d: d.update(recommendations=[("Golang.Go" if x == "golang.go" else x) for x in d["recommendations"]])), ("fora de minúsculas",)),
        Mutante("m09d", 9, "Pylance fora das indesejadas", _jmut(E, _lista_sem("unwantedRecommendations", "ms-python.vscode-pylance")), ("unwantedRecommendations sem", "ms-python.vscode-pylance")),
        Mutante("m09e", 9, "kit ganha extensão e o workspace não", _kit_cresce, ("faltam ['publisher.nova']",)),
        Mutante("m09f", 9, "indesejada no kit e nas recomendações", _kit_e_recomendacao_indesejada, ("também está nas indesejadas",)),
        Mutante("m09g", 9, "id só do extensoes-proibidas.txt retirado das indesejadas", _jmut(E, _lista_sem("unwantedRecommendations", "redhat.vscode-yaml")), ("unwantedRecommendations sem ['redhat.vscode-yaml']",)),
        Mutante("m09h", 9, "extensoes-proibidas.txt ganha id e o workspace não", _proibidas_cresce, ("unwantedRecommendations sem ['publisher.proibida']",)),
        Mutante("m10a", 10, "perfil com initialPermissionMode", _jmut(F, _pondo(("claudeCode.initialPermissionMode",), "acceptEdits")), ("claudeCode.initialPermissionMode",)),
        Mutante("m10b", 10, "perfil com claudeProcessWrapper", _jmut(F, _pondo(("claudeCode.claudeProcessWrapper",), "/home/rafael/bin/claude")), ("claudeCode.claudeProcessWrapper",)),
        Mutante("m10c", 10, "perfil com autoUpdate", _jmut(F, _pondo(("extensions.autoUpdate",), True)), ("extensions.autoUpdate",)),
        Mutante("m10d", 10, "perfil com update.mode default", _jmut(F, _pondo(("update.mode",), "default")), ("update.mode",)),
        Mutante("m10e", 10, "perfil com bash sem -l", _jmut(F, _pondo(("terminal.integrated.profiles.linux", "bash", "args"), [])), ("bash -l",)),
        Mutante("m10f", 10, "perfil chama start-ai-terminal", _jmut(F, _pondo(("terminal.integrated.profiles.linux", "bash", "args"), ["-l", "-c", "start-ai-terminal-claude.sh --shell-only"])), ("start-ai-terminal",)),
        Mutante("m10g", 10, "perfil com usePythonEnvironment", _jmut(F, _pondo(("claudeCode.usePythonEnvironment",), True)), ("claudeCode.usePythonEnvironment",)),
        Mutante("m10h", 10, "perfil sem /opt/wiki/data/**", _jmut(F, _tirando(("files.watcherExclude", f"{CANONICA}/data/**"))), ("perfil: files.watcherExclude sem", f"{CANONICA}/data/**")),
        Mutante("m10i", 10, "perfil com autoCheckUpdates", _jmut(F, _pondo(("extensions.autoCheckUpdates",), True)), ("extensions.autoCheckUpdates",)),
        Mutante("m10j", 10, "perfil exclui .venv* da busca só por caminho absoluto (chave morta)", _jmut(F, _pondo(("search.exclude",), {f"{CANONICA}/.venv*/**": True})), ("search.exclude não exclui", "caminho absoluto")),
        Mutante("m10k", 10, "perfil sem search.exclude", _jmut(F, lambda d: d.pop("search.exclude")), ("search.exclude não exclui", "falta '**/.venv*/**'")),
        Mutante("m10l", 10, "perfil exclui só .venv/** da busca (perde o .venv-tools311)", _jmut(F, _pondo(("search.exclude",), {".venv/**": True})), ("search.exclude não exclui '.venv-tools311/lib/x.py'",)),
        Mutante("m11a", 11, "pyright aponta o .venv", _jmut(P, lambda d: d.update(venvPath=".", venv=".venv")), ("define 'venv",)),
        Mutante("m11b", 11, "typeCheckingMode standard", _jmut(P, _pondo(("typeCheckingMode",), "standard")), ("typeCheckingMode = 'standard'",)),
        Mutante("m11c", 11, "extraPaths sem o user site", _jmut(P, _lista_sem("extraPaths", USER_SITE_311)), ("extraPaths sem", USER_SITE_311)),
        Mutante("m11d", 11, "pythonVersion 3.12", _jmut(P, _pondo(("pythonVersion",), "3.12")), ("pythonVersion = '3.12'",)),
        Mutante("m11e", 11, "settings aponta o interpretador para o .venv", _jmut(S, _pondo(("python.defaultInterpreterPath",), "${workspaceFolder}/.venv/bin/python")), ("python.defaultInterpreterPath para o .venv",)),
        Mutante("m11f", 11, "exclude sem robots", _jmut(P, _lista_sem("exclude", "robots")), ("exclude sem", "robots")),
        Mutante("m12a", 12, "chave inventada do ruff", _jmut(S, _pondo(("ruff.lint.inventada",), True)), ("ruff.lint.inventada: não existe",)),
        Mutante("m12b", 12, "subchave do gopls fora do esquema", _jmut(S, _pondo(("gopls", "ui.diagnostic.vulncheck"), "Off")), ("gopls.ui.diagnostic.vulncheck: não existe no esquema",)),
        Mutante("m12c", 12, "chave nativa inventada", _jmut(S, _pondo(("editor.inventada",), True)), ("editor.inventada: não existe",)),
        Mutante("m12d", 12, "valor fora do enum", _jmut(S, _pondo(("go.vetOnSave",), "of")), ("go.vetOnSave = 'of'", "fora do enum")),
        Mutante("m12e", 12, "golang.go não instalado", _sem_manifesto_do_go, ("go.goroot: não existe",)),
        Mutante("m12f", 12, "bloco de linguagem com erro de digitação", _jmut(S, _pondo(("[pyhton]",), {"editor.formatOnSave": False})), ("linguagem 'pyhton' desconhecida",)),
        Mutante("m12g", 12, "chave nova com erro de digitação (shellcheck.customArg)", _jmut(S, _pondo(("shellcheck.customArg",), ["-x"])), ("shellcheck.customArg: não existe",)),
        Mutante("m12h", 12, "backgroundAnalysisIgnore como texto", _jmut(S, _pondo(("bashIde.backgroundAnalysisIgnore",), "data/**")), ("bashIde.backgroundAnalysisIgnore = 'data/**'", "tipo str")),
        Mutante("m12i", 12, "[python] editor.formatOnTyp (digitação)", _jmut(S, _pondo(("[python]", "editor.formatOnTyp"), False)), ("[python] editor.formatOnTyp: não existe",)),
        Mutante("m12j", 12, "go.tasks.provideDefault como texto", _jmut(S, _pondo(("go.tasks.provideDefault",), "false")), ("go.tasks.provideDefault = 'false'", "tipo str")),
    ]


class Controle:
    """O contrário do mutante: uma mudança que a asserção-alvo TEM de aceitar."""

    def __init__(self, ident: str, alvo: int, descricao: str, aplicar: Callable[[Path, Ctx], None]) -> None:
        self.ident = ident
        self.alvo = alvo
        self.descricao = descricao
        self.aplicar = aplicar


def _kit_intruso(d: Path, ctx: Ctx) -> None:
    ctx.kit.mkdir(parents=True, exist_ok=True)
    (ctx.kit / "extensoes-rascunho.txt").write_text("publisher.rascunho@1.0.0\nms-python.python\n", encoding="utf-8")


def _proibidas_cresce(d: Path, ctx: Ctx) -> None:
    arquivo = ctx.kit / KIT_PROIBIDO
    ctx.kit.mkdir(parents=True, exist_ok=True)
    base = arquivo.read_text(encoding="utf-8") if arquivo.exists() else "".join(f"{x}\n" for x in INDESEJADAS)
    arquivo.write_text(base.rstrip("\n") + "\npublisher.proibida   # mutante\n", encoding="utf-8")


def controles() -> list[Controle]:
    S = REL_SETTINGS
    return [
        Controle("c07a", 7, "chave absoluta no search.exclude é inerte e não conta como excluir código",
                 _jmut(S, _pondo(("search.exclude", f"{CANONICA}/internal/**"), True))),
        Controle("c07b", 7, "chave absoluta no files.exclude é inerte e não esconde data/",
                 _jmut(S, _pondo(("files.exclude", f"{CANONICA}/data"), True))),
        Controle("c09a", 9, "arquivo extensoes-*.txt estranho no kit não vira recomendação", _kit_intruso),
    ]


class Bancada:
    """Cópia dos arquivos num diretório temporário; cada mutante ganha a sua cópia."""

    def __init__(self) -> None:
        pai = BASE_TEMP
        try:
            os.makedirs(pai, exist_ok=True)
        except OSError:
            pai = tempfile.gettempdir()
        self.dir = Path(tempfile.mkdtemp(prefix="bancada-ide-workspace-", dir=pai))
        self.base = self.dir / "base"
        self.origem_perfil = ""
        self.gopls_bin: Path | None = None
        self.gopls_modulo: str | None = None
        self.origem_gopls = ""

    def preparar(self) -> None:
        b = self.base
        (b / ".vscode").mkdir(parents=True)
        for rel in (REL_SETTINGS, REL_EXTENSIONS, REL_TASKS, REL_PYRIGHT):
            shutil.copyfile(RAIZ / rel, b / rel)
        shutil.copyfile(RAIZ / "go.mod", b / "go.mod")
        # Base dos mutantes da 10: o perfil do kit se ele passa na 10; senão o de referência
        # (a 10 já reprovou na árvore real, com o motivo, e os mutantes dela seguem provados).
        perfil_real = RAIZ / REL_PERFIL
        referencia = json.dumps(PERFIL_REFERENCIA, indent=2) + "\n"
        if perfil_real.exists():
            teste = self.ctx(b)
            teste.perfil = perfil_real
            try:
                a10_perfil(teste)
                shutil.copyfile(perfil_real, b / "perfil.json")
                self.origem_perfil = f"cópia de {REL_PERFIL}"
            except Reprova as erro:
                (b / "perfil.json").write_text(referencia, encoding="utf-8")
                self.origem_perfil = f"perfil de referência (o de {REL_PERFIL} reprova na 10: {str(erro)[:120]}…)"
        else:
            (b / "perfil.json").write_text(referencia, encoding="utf-8")
            self.origem_perfil = "perfil de referência do plano §8 1.3 (o do kit ainda não existe)"
        (b / "kit").mkdir()
        for nome in KIT_RECOMENDADO + (KIT_PROIBIDO,):
            if (RAIZ / REL_KIT / nome).is_file():
                shutil.copyfile(RAIZ / REL_KIT / nome, b / "kit" / nome)
        for ident, manifesto in manifestos_do_snapshot().items():
            nome, versao = ident.split("@", 1)
            publicador, extensao = nome.split(".", 1)
            pasta = b / "ext" / f"{nome}-{versao}"
            pasta.mkdir(parents=True)
            (pasta / "package.json").write_text(json.dumps({
                "publisher": publicador, "name": extensao, "version": versao,
                "contributes": {"configuration": {"properties": manifesto["propriedades"]},
                                "configurationDefaults": manifesto["defaults"]}}, indent=1), encoding="utf-8")
        # Disco sintético da régua F20: raízes pesadas que o watcher cobre (data/**,
        # .agents/runtime/**, **/node_modules/*/**) e uma raiz de código pesada (liberada).
        for rel in ("data", ".agents/runtime", "app/node_modules", "internal"):
            _criar_arvore(b / "disco", rel, LIMITE_F20 + 1)
        _criar_arvore(b / "disco", "leve", 3)
        # Asserção 13: o gopls real, só leitura; sem ele, o go do toolchain faz as vezes de binário
        # da mesma versão (sem conferir o pacote), para a bancada ainda provar a comparação.
        versao = versao_toolchain(RAIZ / "go.mod")
        real = Path(CANONICA) / ".toolchains/bin/gopls"
        go_do_toolchain = RAIZ / ".toolchains" / versao / "bin" / "go"
        if real.is_file():
            self.gopls_bin, self.gopls_modulo, self.origem_gopls = real, GOPLS_MODULO, f"{real} (real, só leitura)"
        elif go_do_toolchain.is_file():
            self.gopls_bin, self.origem_gopls = go_do_toolchain, f"{go_do_toolchain} no lugar do gopls ausente"
        else:
            self.origem_gopls = "nenhum binário Go neste host: a asserção 13 fica sem mutante"

    def ctx(self, d: Path, disco: Path | None = None) -> Ctx:
        return Ctx(settings=d / REL_SETTINGS, extensions=d / REL_EXTENSIONS, tasks=d / REL_TASKS,
                   pyright=d / REL_PYRIGHT, gomod=d / "go.mod", perfil=d / "perfil.json", kit=d / "kit",
                   disco=disco or (self.base / "disco"), dir_ext=d / "ext", dirs_embutidas=[],
                   gopls_bin=self.gopls_bin, gopls_modulo=self.gopls_modulo)

    def rodar_mutante(self, mutante: Mutante) -> tuple[bool, str]:
        d = self.dir / mutante.ident
        shutil.copytree(self.base, d, ignore=shutil.ignore_patterns("disco"))
        ctx = self.ctx(d)
        try:
            mutante.aplicar(d, ctx)
            ASSERCOES[mutante.alvo - 1][2](ctx)
        except Reprova as erro:
            mensagem = str(erro)
            faltam = [trecho for trecho in mutante.espera if trecho not in mensagem]
            if faltam:
                return False, f"reprovou por outro motivo (sem {faltam}): {mensagem}"
            return True, mensagem
        except Pulada as erro:
            return False, f"asserção pulou: {erro}"
        except Exception:  # erro da própria bancada: não é veredito, conta como sobrevivente
            return False, "erro inesperado na bancada:\n" + traceback.format_exc()
        return False, "a asserção passou com o mutante"

    def rodar_controle(self, controle: "Controle") -> tuple[bool, str]:
        d = self.dir / controle.ident
        shutil.copytree(self.base, d, ignore=shutil.ignore_patterns("disco"))
        ctx = self.ctx(d)
        try:
            controle.aplicar(d, ctx)
            return True, ASSERCOES[controle.alvo - 1][2](ctx)
        except (Reprova, Pulada) as erro:
            return False, f"a asserção deveria passar e deu: {erro}"
        except Exception:
            return False, "erro inesperado na bancada:\n" + traceback.format_exc()

    def limpar(self) -> None:
        try:
            shutil.rmtree(self.dir)
        except OSError as erro:
            print(f"aviso: não consegui remover {self.dir}: {erro}")


def main() -> int:
    ctx = ctx_real()
    resultados = rodar(ctx)
    for numero, estado, titulo, detalhe in resultados:
        print(f"[{estado}] {numero:2d} {titulo} — {detalhe}")
    reprovadas = [r for r in resultados if r[1] == "FALHOU"]
    puladas = [r for r in resultados if r[1] == "pulada"]

    bancada = Bancada()
    mortos: list[str] = []
    vivos: list[str] = []
    controles_ok: list[str] = []
    controles_ruins: list[str] = []
    try:
        bancada.preparar()
        base = rodar(bancada.ctx(bancada.base))
        # Asserção cuja cópia sem mutação não passa não prova nada com mutante: os mutantes dela
        # não rodam e contam como sobreviventes; os das outras seguem.
        base_ruim = {r[0]: r for r in base
                     if r[1] == "FALHOU" or (r[1] == "pulada" and not (r[0] == 13 and bancada.gopls_bin is None))}
        print(f"bancada em {bancada.dir} — perfil: {bancada.origem_perfil}; gopls: {bancada.origem_gopls}")
        for numero, estado, titulo, detalhe in base_ruim.values():
            print(f"  BASE [{estado}] {numero:2d} {titulo} — {detalhe} (mutantes da {numero} não rodam)")
        versao = versao_toolchain(RAIZ / "go.mod")
        por_alvo: dict[int, list[str]] = {}
        for mutante in mutantes(versao, bancada):
            linha = f"{mutante.ident} ({mutante.alvo}) {mutante.descricao}"
            if mutante.alvo in base_ruim:
                vivos.append(linha)
                print(f"  NÃO RODOU {linha} → base vermelha na asserção {mutante.alvo}")
                continue
            morto, motivo = bancada.rodar_mutante(mutante)
            if morto:
                mortos.append(linha)
                por_alvo.setdefault(mutante.alvo, []).append(mutante.ident)
                print(f"  morto {linha} → {motivo[:160]}")
            else:
                vivos.append(linha)
                print(f"  SOBREVIVEU {linha} → {motivo}")
        for controle in controles():
            linha = f"{controle.ident} ({controle.alvo}) {controle.descricao}"
            ok, detalhe = (False, f"base vermelha na asserção {controle.alvo}") if controle.alvo in base_ruim \
                else bancada.rodar_controle(controle)
            if ok:
                controles_ok.append(linha)
                print(f"  controle ok {linha}")
            else:
                controles_ruins.append(linha)
                print(f"  CONTROLE FALHOU {linha} → {detalhe}")
        print("mutantes mortos por asserção: "
              + "; ".join(f"{n}: {' '.join(ids)}" for n, ids in sorted(por_alvo.items())))
        sem_mutante = sorted({n for n, _, _ in ASSERCOES} - set(por_alvo))
        if sem_mutante:
            vivos.append(f"asserções sem mutante morto: {sem_mutante}")
            print(f"  asserções sem mutante morto: {sem_mutante}")
    finally:
        bancada.limpar()

    resumo = (f"{len(ASSERCOES)} asserções, {len(mortos)} mutantes mortos — verdes {len(resultados) - len(reprovadas) - len(puladas)}, "
              f"puladas {len(puladas)}{' (' + ', '.join(str(r[0]) for r in puladas) + ')' if puladas else ''}, "
              f"reprovadas {len(reprovadas)}{' (' + ', '.join(str(r[0]) for r in reprovadas) + ')' if reprovadas else ''}; "
              f"sobreviventes {len(vivos)}; controles {len(controles_ok)}/{len(controles_ok) + len(controles_ruins)}")
    print(resumo)
    return 1 if reprovadas or vivos or controles_ruins or not mortos else 0


if __name__ == "__main__":
    sys.exit(main())
