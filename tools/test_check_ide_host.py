#!/usr/bin/env python3
"""Prende as invariantes de tools/check-ide-host num host de mentira.

Roda: python3 tools/test_check_ide_host.py

O check le o disco do dono (~/.vscode-oss, ~/.config/VSCodium, ~/.claude), o
/etc/apt, o keyring do VSCodium e o repositorio, e pergunta ao dpkg, ao apt, ao
gpg e ao go. Aqui tudo isso e de MENTIRA: cada caso monta um host verde num
diretorio temporario, estraga UMA coisa e confere o veredito. Os binarios sao
dubles num PATH que contem SO eles -- o check nunca alcanca o dpkg de verdade --,
e cada duble recusa com 99, deixando linha em `recusas`, qualquer chamada fora do
vocabulario que o check declarou. Recusa nenhuma no fim e a prova de que o check
nao passou a perguntar coisa que esta bancada nao ve.

MUTANTES: cada assercao que importa tem um mutante do PROPRIO check ao lado -- o
fonte real lido do disco, com UMA linha trocada, executado sobre o mesmo host.
Mutante que nao muda o veredito denuncia assercao que nao morde (memoria "teste e
aprendizado sao par"). A troca exige exatamente uma ocorrencia do trecho: se o
check for reescrito e o trecho sumir, esta bancada reprova em vez de testar nada.

O limiar do F20 desce para 10 pelo --limiar-f20: a regra e a mesma do padrao de
1.000, e o host de mentira nao precisa de 3.000 diretorios para prova-la.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from importlib.machinery import SourceFileLoader

sys.dont_write_bytecode = True  # o check nao tem .py: sem isto, .pyc de nome degenerado

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(RAIZ_REPO, "tools", "check-ide-host")
PINO = "1302DE60231889FE1EBACADC54678CF75A278D9C"
OUTRA_CHAVE = "0123456789ABCDEF0123456789ABCDEF01234567"
LIMIAR = 10
CLI = "2.1.280"
OBRIGATORIAS = [
    ("golang.go", "0.56.1"),
    ("detachhead.basedpyright", "1.40.1"),
    ("charliermarsh.ruff", "2026.82.0"),
    ("timonwong.shellcheck", "0.40.1"),
    ("mads-hartmann.bash-ide-vscode", "1.43.2"),
    ("usernamehw.errorlens", "3.28.0"),
]

FALHAS = []


def caso(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'ERRO'} {nome}" + ("" if cond or not detalhe else f"\n         {detalhe}"))
    if not cond:
        FALHAS.append(nome)


STUB = {
    # dpkg-query -W -f=${Status}|${Version} <pacote>
    "dpkg-query": r"""
fmt=""; pkg=""
for a in "$@"; do case "$a" in -W) ;; -f=*) fmt="${a#-f=}" ;; -*) recusa "$@" ;; *) pkg="$a" ;; esac; done
[ -f "$ZZ_ESTADO/dpkg-$pkg.status" ] || { echo "dpkg-query: no packages found matching $pkg" >&2; exit 1; }
case "$fmt" in
  '${Status}') cat "$ZZ_ESTADO/dpkg-$pkg.status" ;;
  '${Version}') cat "$ZZ_ESTADO/dpkg-$pkg.version" 2>/dev/null ;;
  *) recusa "$@" ;;
esac
""",
    "apt-mark": r"""
[ "$*" = showhold ] || recusa "$@"
cat "$ZZ_ESTADO/holds" 2>/dev/null
exit 0
""",
    "apt-cache": r"""
[ "$*" = "policy codium" ] || recusa "$@"
cat "$ZZ_ESTADO/policy-codium"
""",
    # gpg --homedir D --batch --show-keys --with-colons <keyring>: uma chave
    # primaria (com uma subchave, para provar que o fpr da subchave nao conta)
    # por linha de $ZZ_ESTADO/fprs.
    "gpg": r"""
case " $* " in *" --show-keys "*) ;; *) recusa "$@" ;; esac
case " $* " in *" --with-colons "*) ;; *) recusa "$@" ;; esac
while read -r f; do
  [ -n "$f" ] || continue
  printf 'pub:-:3072:1:%s:1539043200:::-:::scSC::::::23::0:\n' "${f:24}"
  printf 'fpr:::::::::%s:\n' "$f"
  printf 'uid:-::::1539043200::0::Chave da bancada::::::::::0:\n'
  printf 'sub:-:3072:1:%s:1539043200::::::e::::::23:\n' "FEDCBA9876543210"
  printf 'fpr:::::::::%s:\n' "FEDCBA9876543210FEDCBA9876543210FEDCBA98"
done < "$ZZ_ESTADO/fprs"
""",
    # O go de verdade grava telemetria em $XDG_CONFIG_HOME/go/telemetry (sem ela,
    # em ~/.config): o duble RECUSA rodar quando isso cairia no home do dono.
    "go": r"""
case "${XDG_CONFIG_HOME:-}" in ""|"$HOME"*) echo "go: gravaria telemetria no home (${XDG_CONFIG_HOME:-$HOME/.config})" >&2; exit 3 ;; esac
[ "$1 $2" = "version -m" ] || recusa "$@"
printf '%s: %s\n\tpath\tgolang.org/x/tools/gopls\n\tmod\tgolang.org/x/tools/gopls\t%s\th1:bancada=\n' \
  "$3" "$(cat "$ZZ_ESTADO/gover")" "$(cat "$ZZ_ESTADO/goplsver")"
""",
}
# O gopls de mentira: `gopls check <arquivo>` imprime o que o estado mandar e sai
# com o rc do estado. E, como o de verdade, sem -tags=devcmds em GOFLAGS ou sem
# GOTOOLCHAIN=local ele acusa o erro de tag: e o que torna mutavel a linha do
# check que monta esse ambiente.
# (o texto do gopls de mentira, GOPLS_STUB, fica logo abaixo do CABECALHO_STUB)
CABECALHO_STUB = """#!/bin/bash
export PATH=/usr/bin:/bin
recusa() { echo "VOCABULARIO $(basename "$0") $*" >> "$ZZ_ESTADO/recusas"; exit 99; }
"""
GOPLS_STUB = r"""
case "${XDG_CONFIG_HOME:-}" in ""|"$HOME"*) echo "gopls: gravaria telemetria no home" >&2; exit 3 ;; esac
[ "${1:-}" = check ] && [ "${2:-}" = cmd/build/main.go ] || recusa "$@"
[ "$(pwd)" = "$ZZ_RAIZ" ] || { echo "gopls: rodou fora da raiz ($(pwd))"; exit 3; }
if [ "${GOFLAGS:-}" != -tags=devcmds ] || [ "${GOTOOLCHAIN:-}" != local ]; then
  echo "$ZZ_RAIZ/cmd/build/main.go:1:1: build constraints exclude all Go files in $ZZ_RAIZ/cmd/build"
  exit 0
fi
cat "$ZZ_ESTADO/gopls-saida" 2>/dev/null
exit "$(cat "$ZZ_ESTADO/gopls-rc" 2>/dev/null || echo 0)"
"""


ENGINES = {"usernamehw.errorlens": "^1.107.0", "anthropic.claude-code": "^1.94.0"}  # os demais: ^1.90.0


def perfil_repo(raiz):
    return {
        "telemetry.telemetryLevel": "off",
        "update.mode": "none",
        "extensions.autoUpdate": False,
        "extensions.autoCheckUpdates": False,
        "editor.formatOnSave": False,
        "editor.formatOnPaste": False,
        "editor.formatOnType": False,
        "files.trimTrailingWhitespace": False,
        "files.insertFinalNewline": False,
        "editor.minimap.enabled": False,
        "claudeCode.useTerminal": False,
        "terminal.integrated.profiles.linux": {"bash": {"path": "/usr/bin/bash", "args": ["-l"]}},
        "files.watcherExclude": {f"{raiz}/pesada/**": True, "**/.git/objects/**": True, "**/node_modules/*/**": True},
        "search.exclude": {"**/.venv*/**": True},
    }


def perfil_disco_jsonc(raiz, sem_chave=None, troca=None, watcher_extra=True, watcher_sem=None):
    """O perfil como a interface do editor grava: comentario, virgula final, e
    padrao de glob com `/**` e `*/` DENTRO de string -- o que uma regex de
    comentario comeria. O http.proxy tem `//` dentro de string pelo mesmo motivo."""
    repo = perfil_repo(raiz)
    watcher = dict(repo["files.watcherExclude"])
    if watcher_extra:
        watcher[f"{raiz}/extra-do-dono/**"] = True
    if watcher_sem:
        watcher.pop(watcher_sem)
    repo["files.watcherExclude"] = watcher
    if troca:
        repo.update(troca)
    if sem_chave:
        repo.pop(sem_chave)
    linhas = ["// perfil de mentira da bancada: preferencia do dono fica", "{",
              '  "workbench.colorTheme": "Dracula", // tema do dono',
              '  "http.proxy": "http://127.0.0.1:3128",',
              "  /* chaves do repositorio */"]
    for chave, valor in repo.items():
        if chave == "files.watcherExclude":
            linhas.append('  "files.watcherExclude": {')
            for padrao, ligado in valor.items():
                linhas.append(f"    {json.dumps(padrao)}: {json.dumps(ligado)},")
            linhas.append("  },")
        elif chave == "terminal.integrated.profiles.linux":
            linhas.append('  "terminal.integrated.profiles.linux": {"bash": {"path": "/usr/bin/bash", "args": ["-l"],},},')
        else:
            linhas.append(f"  {json.dumps(chave)}: {json.dumps(valor)},")
    linhas.append("}")
    return "\n".join(linhas) + "\n"


class Host:
    def __init__(self, base):
        self.base = base
        self.home = os.path.join(base, "home")
        self.raiz = os.path.join(base, "raiz")
        self.etc_apt = os.path.join(base, "etc-apt")
        self.bin = os.path.join(base, "bin")
        self.estado = os.path.join(base, "estado")
        self.keyring = os.path.join(base, "keyrings", "vscodium-archive-keyring.gpg")
        self.proc = os.path.join(base, "proc")
        self.gopls = os.path.join(base, "gopls")
        self.verde()

    def escreve(self, caminho, texto):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)

    def grava_json(self, caminho, obj):
        self.escreve(caminho, json.dumps(obj, indent=2) + "\n")

    def e(self, *partes):  # caminho no estado dos dubles
        return os.path.join(self.estado, *partes)

    def manifesto(self, pares, engines=None):
        """O manifesto e a pasta de cada extensao, com o package.json que diz o
        engines.vscode — e dele que sai o piso do codium."""
        base = os.path.join(self.home, ".vscode-oss/extensions")
        motores = dict(ENGINES, **(engines or {}))
        for i, v in pares:
            publisher, nome = i.split(".", 1)
            self.grava_json(os.path.join(base, f"{i}-{v}", "package.json"),
                            {"publisher": publisher, "name": nome, "version": v,
                             "engines": {"vscode": motores.get(i.lower(), "^1.90.0")}})
        self.grava_json(os.path.join(base, "extensions.json"),
                        [{"identifier": {"id": i}, "version": v, "relativeLocation": f"{i}-{v}"} for i, v in pares])

    def verde(self):
        for nome, corpo in STUB.items():
            caminho = os.path.join(self.bin, nome)
            self.escreve(caminho, CABECALHO_STUB + corpo)
            os.chmod(caminho, 0o755)
        os.makedirs(self.estado, exist_ok=True)
        # "hold ok installed": o estado do codium DEPOIS do kit, que o poe em hold
        self.escreve(self.e("dpkg-codium.status"), "hold ok installed")
        self.escreve(self.e("dpkg-codium.version"), "1.135.06055")
        self.escreve(self.e("holds"), "codium\n")
        self.escreve(self.e("policy-codium"),
                     "codium:\n  Installed: 1.135.06055\n  Candidate: 1.135.06055\n  Version table:\n")
        self.escreve(self.e("fprs"), PINO + "\n")
        self.escreve(self.e("gover"), "go1.26.6")
        self.escreve(self.keyring, "keyring de mentira: o gpg e duble\n")
        self.escreve(self.gopls, CABECALHO_STUB + GOPLS_STUB)
        os.chmod(self.gopls, 0o755)
        self.escreve(self.e("goplsver"), "v0.23.0")
        self.escreve(os.path.join(self.proc, "sys/fs/inotify/max_user_watches"), "65536\n")
        # home
        self.escreve(os.path.join(self.home, ".config/VSCodium/.kit-ide"), "kit 2026-09-23\n")
        self.escreve(os.path.join(self.home, ".config/VSCodium/User/settings.json"), perfil_disco_jsonc(self.raiz))
        self.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI)])
        versoes = os.path.join(self.home, ".local/share/claude/versions")
        self.escreve(os.path.join(versoes, CLI), "binario de mentira\n")
        os.makedirs(os.path.join(self.home, ".local/bin"), exist_ok=True)
        os.symlink(os.path.join(versoes, CLI), os.path.join(self.home, ".local/bin/claude"))
        self.escreve(os.path.join(self.home, ".local/share/archive-vscode-20260923/MANIFESTO.sha256"),
                     "0" * 64 + "  config-Code/settings.json\n")
        self.grava_json(os.path.join(self.home, ".claude/settings.json"),
                        {"env": {"CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL": "1"}, "model": "opus"})
        # raiz
        self.escreve(os.path.join(self.raiz, "ops/ide/extensoes.txt"),
                     "# lista fechada, id@versao\n\n" + "".join(f"{i}@{v}\n" for i, v in OBRIGATORIAS)
                     + "anthropic.claude-code@CLI\n")
        self.escreve(os.path.join(self.raiz, "ops/ide/extensoes-gpu.txt"), "continue.continue@2.0.0\n")
        self.grava_json(os.path.join(self.raiz, "ops/ide/perfil/settings.json"), perfil_repo(self.raiz))
        self.escreve(os.path.join(self.raiz, ".vscode/settings.json"),
                     '{\n  // workspace\n  "files.watcherExclude": {"pesada/**": true,},\n}\n')
        self.escreve(os.path.join(self.raiz, "go.mod"), "module x\n\ngo 1.26.0\n\ntoolchain go1.26.6\n")
        for n in range(LIMIAR + 1):
            os.makedirs(os.path.join(self.raiz, "pesada", f"d{n:02d}"))
            os.makedirs(os.path.join(self.raiz, "internal", f"d{n:02d}"))
            os.makedirs(os.path.join(self.raiz, "mc", "node_modules", f"p{n:02d}"))
        for n in range(3):
            os.makedirs(os.path.join(self.raiz, "leve", f"d{n}"))
        # /etc/apt de mentira: so o repositorio do VSCodium
        self.escreve(os.path.join(self.etc_apt, "sources.list.d/vscodium.list"),
                     "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/vscodium-archive-keyring.gpg] "
                     "https://download.vscodium.com/debs vscodium main\n")

    def roda(self, *args, check=CHECK):
        env = {"PATH": self.bin, "HOME": self.home, "ZZ_ESTADO": self.estado, "ZZ_RAIZ": self.raiz,
               "PYTHONIOENCODING": "utf-8"}
        cmd = [sys.executable, check, "--home", self.home, "--raiz", self.raiz, "--etc-apt", self.etc_apt,
               "--keyring", self.keyring, "--proc", self.proc,
               "--go", os.path.join(self.bin, "go"), "--gopls", self.gopls, "--limiar-f20", str(LIMIAR), *args]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr


# ── o que cada caso estraga ────────────────────────────────────────────────
def sem_marcador_sem_codium(h):
    os.remove(os.path.join(h.home, ".config/VSCodium/.kit-ide"))
    os.remove(h.e("dpkg-codium.status"))


def marcador_sem_codium(h):
    os.remove(h.e("dpkg-codium.status"))


def sem_golang(h):
    h.manifesto(OBRIGATORIAS[1:] + [("anthropic.claude-code", CLI)])


def golang_velho(h):
    h.manifesto([("golang.go", "0.55.0")] + OBRIGATORIAS[1:] + [("anthropic.claude-code", CLI)])


def com_copilot(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI), ("GitHub.copilot", "1.0.0")])


def com_tema(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI), ("dracula-theme.theme-dracula", "2.25.1")])


def maiusculas(h):
    h.manifesto([(i.upper() if i.startswith("golang") else i.title(), v) for i, v in OBRIGATORIAS]
                 + [("Anthropic.claude-code", CLI)])


def paridade_quebrada(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", "2.1.279")])


def code_instalado(h):
    h.escreve(h.e("dpkg-code.status"), "install ok installed")


def remocao_pendente(h):  # --sem-remover: VS Code de pe, por ordem, e o marcador diz
    code_instalado(h)
    fonte_microsoft(h)
    sem_arquivo_datado(h)
    h.escreve(os.path.join(h.home, ".config/VSCodium/.kit-ide"), "data=2026-09-23\nremocao_vscode=pendente\n")


def remocao_sem_marca(h):  # o mesmo estado SEM o campo no marcador: e falha
    code_instalado(h)
    fonte_microsoft(h)
    sem_arquivo_datado(h)


def fonte_microsoft(h):
    h.escreve(os.path.join(h.etc_apt, "sources.list.d/vscode.sources"),
              "Types: deb\nURIs: https://packages.microsoft.com/repos/code\nSuites: stable\n")


def sem_arquivo_datado(h):
    os.remove(os.path.join(h.home, ".local/share/archive-vscode-20260923/MANIFESTO.sha256"))
    os.rmdir(os.path.join(h.home, ".local/share/archive-vscode-20260923"))


def manifesto_vazio(h):
    h.escreve(os.path.join(h.home, ".local/share/archive-vscode-20260923/MANIFESTO.sha256"), "")


def perfil_sem_chave(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, sem_chave="update.mode"))


def perfil_valor_trocado(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"editor.formatOnSave": True}))


def perfil_tipo_trocado(h):  # false no repo, 0 no disco: em Python, False == 0
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"extensions.autoUpdate": 0}))


def perfil_sem_padrao_aninhado(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, watcher_sem="**/.git/objects/**"))


def perfil_symlink(h):
    alvo = os.path.join(h.home, ".config/VSCodium/User/settings.json")
    os.remove(alvo)
    os.symlink(os.path.join(h.raiz, "ops/ide/perfil/settings.json"), alvo)


def sem_hold(h):
    h.escreve(h.e("holds"), "")


def candidato_novo(h):
    h.escreve(h.e("policy-codium"), "codium:\n  Installed: 1.135.06055\n  Candidate: 1.136.00001\n")


def sem_skip(h):
    h.grava_json(os.path.join(h.home, ".claude/settings.json"), {"env": {}, "model": "opus"})


def com_agents_md(h):
    h.grava_json(os.path.join(h.home, ".claude/settings.json"),
                 {"env": {"CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL": "1"},
                  "pluginConfigs": {"agents-md@builtin": {"options": {"instructionFiles": "claude-md-and-agents-md"}}}})


def workspace_sem_pesada(h):
    h.escreve(os.path.join(h.raiz, ".vscode/settings.json"), '{"files.watcherExclude": {"outra/**": true}}\n')


def workspace_ausente(h):
    os.remove(os.path.join(h.raiz, ".vscode/settings.json"))


def perfil_sem_pesada(h):
    # Tira dos DOIS perfis, para o subconjunto do perfil seguir verde e so o F20
    # poder reprovar.
    repo = perfil_repo(h.raiz)
    repo["files.watcherExclude"].pop(f"{h.raiz}/pesada/**")
    h.grava_json(os.path.join(h.raiz, "ops/ide/perfil/settings.json"), repo)
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, watcher_sem=f"{h.raiz}/pesada/**"))
    # o perfil_disco_jsonc parte do repo NORMAL; regrava sem a chave do repo tambem
    texto = open(os.path.join(h.home, ".config/VSCodium/User/settings.json"), encoding="utf-8").read()
    assert f"{h.raiz}/pesada/**" not in texto


def sem_gopls(h):
    os.remove(h.gopls)


def gopls_de_outro_go(h):
    h.escreve(h.e("gover"), "go1.25.6")


def gopls_de_outra_versao(h):
    h.escreve(h.e("goplsver"), "v0.21.0")


def gopls_com_erro_de_tag(h):  # mesmo com a tag certa, o pacote nao carrega
    h.escreve(h.e("gopls-saida"), f"{h.raiz}/cmd/build/main.go:1:1: build constraints exclude all Go files in {h.raiz}/cmd/build\n")


def gopls_check_quebrado(h):
    h.escreve(h.e("gopls-saida"), "gopls: failed to load view\n")
    h.escreve(h.e("gopls-rc"), "2")


def pino_do_instalador_diverge(h):  # o pino vem da constante do instalador
    h.escreve(os.path.join(h.raiz, "ops/ide/instalar-ide.sh"),
              "#!/usr/bin/env bash\nGOPLS_VERSAO=v0.24.0\ngo install \"golang.org/x/tools/gopls@$GOPLS_VERSAO\"\n")


def pino_do_instalador_confere(h):
    h.escreve(os.path.join(h.raiz, "ops/ide/instalar-ide.sh"), "#!/usr/bin/env bash\nGOPLS_VERSAO=v0.23.0\n")


def codium_sem_hold_no_dpkg(h):  # antes do hold: tambem conta como instalado
    h.escreve(h.e("dpkg-codium.status"), "install ok installed")


def codium_so_config(h):  # removido, com config: NAO esta instalado
    h.escreve(h.e("dpkg-codium.status"), "deinstall ok config-files")


def chave_errada(h):
    h.escreve(h.e("fprs"), OUTRA_CHAVE + "\n")


def duas_chaves(h):
    h.escreve(h.e("fprs"), PINO + "\n" + OUTRA_CHAVE + "\n")


def sem_keyring(h):
    os.remove(h.keyring)


def linha_sem_arroba(h):
    h.escreve(os.path.join(h.raiz, "ops/ide/extensoes.txt"),
              "golang.go\n" + "".join(f"{i}@{v}\n" for i, v in OBRIGATORIAS[1:]))


def continue_fora_do_pino(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI), ("Continue.continue", "2.1.0")])


def continue_no_pino(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI), ("Continue.continue", "2.0.0")])


def extensao_exige_codium_novo(h):
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI)], engines={"usernamehw.errorlens": "^1.140.0"})


def codium_velho_sem_extensao(h):
    h.manifesto([])
    h.escreve(h.e("dpkg-codium.version"), "1.100.0")


def preferencia_do_dono(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"editor.minimap.enabled": True}))


def claudecode_trocado(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"claudeCode.useTerminal": True}))


def search_exclude_sem_venv(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"search.exclude": {}}))


def repo_com_search_exclude_absoluto(h):
    repo = perfil_repo(h.raiz)
    repo["search.exclude"] = {f"{h.raiz}/.venv*/**": True}
    h.grava_json(os.path.join(h.raiz, "ops/ide/perfil/settings.json"), repo)
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"search.exclude": {f"{h.raiz}/.venv*/**": True}}))


def wrapper_no_disco(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"claudeCode.claudeProcessWrapper": "/home/rafael/.local/bin/claude"}))


def trim_ligado(h):
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, troca={"files.trimTrailingWhitespace": True}))


def repo_sem_invariante(h):
    repo = perfil_repo(h.raiz)
    repo.pop("update.mode")
    h.grava_json(os.path.join(h.raiz, "ops/ide/perfil/settings.json"), repo)
    h.escreve(os.path.join(h.home, ".config/VSCodium/User/settings.json"),
              perfil_disco_jsonc(h.raiz, sem_chave="update.mode"))


def pino_no_literal_do_instalador(h):  # sem a constante, o literal UNICO do instalador
    h.escreve(os.path.join(h.raiz, "ops/ide/instalar-ide.sh"),
              "#!/usr/bin/env bash\ngo install golang.org/x/tools/gopls@v0.24.0\n")


def sem_marcador_sem_gopls(h):
    os.remove(os.path.join(h.home, ".config/VSCodium/.kit-ide"))
    os.remove(h.gopls)


def proibidas_do_arquivo(h):
    h.escreve(os.path.join(h.raiz, "ops/ide/extensoes-proibidas.txt"), "# da fixture\ndracula-theme.theme-dracula  # tema\n")
    h.manifesto(OBRIGATORIAS + [("anthropic.claude-code", CLI), ("dracula-theme.theme-dracula", "2.25.1")])


def sem_lista(h):
    os.remove(os.path.join(h.raiz, "ops/ide/extensoes.txt"))


# (nome, estraga, args, rc esperado, trechos que a saida tem de ter)
CASOS = [
    ("C01 sem codium e sem marcador: pulada, 75", sem_marcador_sem_codium, [], 75, ["pulada"]),
    ("C02 marcador sem codium: falha", marcador_sem_codium, [], 1, ["marcador do kit presente"]),
    ("C03 host verde (perfil JSONC, extra do dono, node_modules podado, raiz isenta)", None, [], 0,
     ["check-ide-host: VERDE", "F20: 2 raiz(es)", "mc, pesada"]),
    ("C04 obrigatoria ausente", sem_golang, [], 1, ["extensao obrigatoria ausente: golang.go@0.56.1"]),
    ("C05 obrigatoria em outra versao", golang_velho, [], 1, ["golang.go: instalada 0.55.0, exigida 0.56.1"]),
    ("C06 proibida instalada (com maiuscula no manifesto)", com_copilot, [], 1,
     ["extensao proibida instalada: github.copilot"]),
    ("C07 extra permitida nao reprova (gate de subconjunto)", com_tema, [], 0,
     ["extras permitidas", "dracula-theme.theme-dracula"]),
    ("C08 ids em maiusculas no manifesto casam com a lista", maiusculas, [], 0, ["check-ide-host: VERDE"]),
    ("C09 extensao != CLI", paridade_quebrada, [], 1, ["paridade: extensao anthropic.claude-code 2.1.279, CLI 2.1.280"]),
    ("C10 code instalado reprova", code_instalado, [], 1, ["pacote code (VS Code) ainda instalado"]),
    ("C10b code instalado com --antes-da-remocao passa", code_instalado, ["--antes-da-remocao"], 0,
     ["--antes-da-remocao: code"]),
    ("C11 packages.microsoft.com em /etc/apt", fonte_microsoft, [], 1, ["packages.microsoft.com ainda em", "vscode.sources"]),
    ("C31 remocao pendente pelo marcador (--sem-remover) e aviso, com o comando", remocao_pendente, [], 0,
     ["remocao do VS Code PENDENTE", "--so-remover-vscode", "AVISO  pacote code (VS Code) ainda instalado"]),
    ("C31b o mesmo estado sem a marca no marcador reprova", remocao_sem_marca, [], 1,
     ["FALHA  pacote code (VS Code) ainda instalado", "FALHA  nenhum arquivo datado"]),
    ("C12 sem arquivo datado", sem_arquivo_datado, [], 1, ["nenhum arquivo datado"]),
    ("C12b MANIFESTO vazio", manifesto_vazio, [], 1, ["sem MANIFESTO.sha256 nao vazio"]),
    ("C13 perfil sem chave do repo", perfil_sem_chave, [], 1, ["chave 'update.mode' ausente"]),
    ("C13b perfil com valor trocado", perfil_valor_trocado, [], 1, ["chave 'editor.formatOnSave' diverge"]),
    ("C13c perfil com 0 no lugar de false", perfil_tipo_trocado, [], 1, ["chave 'extensions.autoUpdate' diverge"]),
    ("C13d preferencia do dono fora das invariantes e aviso", preferencia_do_dono, [], 0,
     ["AVISO", "fora das invariantes: editor.minimap.enabled"]),
    ("C13e claudeCode.* e invariante", claudecode_trocado, [], 1, ["chave 'claudeCode.useTerminal' diverge"]),
    ("C13f perfil do repo sem uma invariante", repo_sem_invariante, [], 1, ["sem a invariante 'update.mode'"]),
    ("C13i search.exclude sem o padrao absoluto do repo reprova", search_exclude_sem_venv, [], 1,
     ["chave 'search.exclude' diverge"]),
    ("C13j search.exclude absoluto no perfil do repo e defeito", repo_com_search_exclude_absoluto, [], 1,
     ["search.exclude com chave absoluta"]),
    ("C13g claudeCode.claudeProcessWrapper no disco reprova", wrapper_no_disco, [], 1,
     ["claudeCode.claudeProcessWrapper definido no disco"]),
    ("C13h trimTrailingWhitespace ligado reprova (reescreve bytes)", trim_ligado, [], 1,
     ["chave 'files.trimTrailingWhitespace' diverge"]),
    ("C15 padrao aninhado do repo faltando no disco", perfil_sem_padrao_aninhado, [], 1,
     ["chave 'files.watcherExclude' diverge"]),
    ("C16 perfil do disco e symlink", perfil_symlink, [], 1, ["e symlink"]),
    ("C17 codium sem hold", sem_hold, [], 1, ["codium sem hold"]),
    ("C18 candidato novo e aviso, nao falha", candidato_novo, [], 0,
     ["AVISO", "Installed 1.135.06055 != Candidate 1.136.00001"]),
    ("C19 sem CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL", sem_skip, [], 1, ["CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL != \"1\""]),
    ("C19b agents-md@builtin ainda presente e aviso", com_agents_md, [], 0, ["AVISO", "agents-md@builtin"]),
    ("C20 F20: workspace sem a raiz pesada", workspace_sem_pesada, [], 1,
     ["fora do files.watcherExclude do workspace", ": pesada"]),
    ("C20b F20: perfil do disco sem a raiz pesada", perfil_sem_pesada, [], 1,
     ["fora do files.watcherExclude do perfil do disco"]),
    ("C20c F20: workspace ausente", workspace_ausente, [], 1, ["workspace ilegivel ou ausente"]),
    ("C21 gopls ausente e falha nomeada", sem_gopls, [], 1, ["gopls ausente em"]),
    ("C21b gopls de outro Go", gopls_de_outro_go, [], 1, ["compilado com go1.25.6, esperado go1.26.6 (go.mod)"]),
    ("C21c gopls de outra versao", gopls_de_outra_versao, [], 1, ["modulo golang.org/x/tools/gopls@v0.21.0, esperado @v0.23.0"]),
    ("C21d gopls check com erro de tag", gopls_com_erro_de_tag, [], 1, ["o par gopls x toolchain x -tags=devcmds"]),
    ("C21e gopls check que sai != 0", gopls_check_quebrado, [], 1, ["gopls check cmd/build/main.go saiu 2"]),
    ("C21f o pino vem do GOPLS_VERSAO do instalador", pino_do_instalador_diverge, [], 1,
     ["esperado @v0.24.0 (GOPLS_VERSAO de"]),
    ("C21g com o GOPLS_VERSAO certo, sem aviso de pino embutido", pino_do_instalador_confere, [], 0,
     ["gopls v0.23.0 compilado com go1.26.6 (GOPLS_VERSAO de", "check-ide-host: VERDE — "]),
    ("C21h --sem-gopls-funcional pula so o check", gopls_com_erro_de_tag, ["--sem-gopls-funcional"], 0,
     ["gopls check funcional pulado"]),
    ("C21i sem a constante, o pino e o literal unico do instalador", pino_no_literal_do_instalador, [], 1,
     ["esperado @v0.24.0", "instalar-ide.sh"]),
    ("C28 codium antes do hold (install ok installed) conta como instalado", codium_sem_hold_no_dpkg, [], 0,
     ["codium instalado: 1.135.06055"]),
    ("C29 codium so com config (deinstall ok config-files) nao esta instalado", codium_so_config, [], 1,
     ["codium NAO instalado (dpkg: deinstall ok config-files)"]),
    ("C21j sem o marcador do kit, gopls ausente e aviso", sem_marcador_sem_gopls, [], 0,
     ["AVISO  gopls-do-toolchain: gopls ausente"]),
    ("C22 keyring com outra chave", chave_errada, [], 1, [OUTRA_CHAVE]),
    ("C22b keyring com a pinada E outra", duas_chaves, [], 1, ["esperado so " + PINO]),
    ("C22c keyring ausente", sem_keyring, [], 1, ["keyring do VSCodium ausente"]),
    ("C23 linha sem @ na lista", linha_sem_arroba, [], 1, ["sem @ ('golang.go')"]),
    ("C24 --com-gpu exige o Continue instalado", None, ["--com-gpu"], 1,
     ["extensao obrigatoria ausente: continue.continue@2.0.0"]),
    ("C24b sem a flag, Continue fora do pino reprova", continue_fora_do_pino, [], 1,
     ["extensao continue.continue: instalada 2.1.0, pino 2.0.0"]),
    ("C24c sem a flag, Continue ausente nao e exigido", None, [], 0, ["continue.continue nao instalada"]),
    ("C24d sem a flag, Continue no pino passa", continue_no_pino, [], 0, ["continue.continue instalada no pino 2.0.0"]),
    ("C26 codium abaixo do engines.vscode de uma extensao da lista", extensao_exige_codium_novo, [], 1,
     ["codium 1.135.06055 abaixo de 1.140.0 (engines.vscode ^1.140.0 de usernamehw.errorlens@3.28.0)"]),
    ("C26b sem extensao da lista, o piso embutido 1.107.0", codium_velho_sem_extensao, [], 1,
     ["codium 1.100.0 abaixo de 1.107.0 (piso embutido"]),
    ("C27 a lista de proibidas vem de ops/ide/extensoes-proibidas.txt", proibidas_do_arquivo, [], 1,
     ["extensao proibida instalada: dracula-theme.theme-dracula"]),
    ("C25 sem ops/ide/extensoes.txt: lista embutida", sem_lista, [], 0, ["AVISO", "lista embutida"]),
    ("C30 --json no host verde: so o objeto, com veredito e medidas", None, ["--json"], 0,
     ['{"avisos": ', '"veredito": "verde"', '"f20_raizes_pesadas": ["mc", "pesada"]']),
    ("C30b --json no host reprovado", sem_golang, ["--json"], 1,
     ['"veredito": "reprovado"', "extensao obrigatoria ausente: golang.go@0.56.1"]),
]


def roda_caso(tmp, estraga, args, check=CHECK):
    base = tempfile.mkdtemp(dir=tmp)
    h = Host(base)
    if estraga:
        estraga(h)
    rc, saida = h.roda(*args, check=check)
    recusas = ""
    if os.path.exists(h.e("recusas")):
        recusas = open(h.e("recusas"), encoding="utf-8").read()
    return rc, saida, recusas


# ── mutantes: (nome, trecho original, trecho mutante, caso que tem de virar,
#    rc sob o mutante, trecho que a saida do mutante TEM de ter). O ultimo campo
#    existe porque rc sozinho aceita mutante que morre pela razao errada: o M3,
#    por exemplo, tem de reprovar por perfil ilegivel, e nao por outra coisa que
#    a troca tenha quebrado de passagem.
MUTANTES = [
    ("M1 sem .lower() no manifesto", 'ident = str(entrada["identifier"]["id"]).lower()',
     'ident = str(entrada["identifier"]["id"])', "C08", 1, "extensao obrigatoria ausente: golang.go@0.56.1"),
    ("M2 interseccao com as proibidas desligada", "presentes = sorted(set(instaladas) & proibidas)",
     "presentes = []", "C06", 0, "check-ide-host: VERDE"),
    ("M3 JSONC por regex em vez de tokenizador", "return json.loads(_sem_virgula_final(_sem_comentarios(texto)))",
     'return json.loads(_sem_virgula_final(re.sub(r"/\\*.*?\\*/|//[^\\n]*", "", texto, flags=re.S)))', "C03", 1,
     "nao e JSON/JSONC valido"),
    ("M4 subconjunto aninhado trocado por igualdade",
     "return isinstance(disco, dict) and all(k in disco and subconjunto(v, disco[k]) for k, v in repo.items())",
     "return igual(repo, disco)", "C03", 1, "chave 'files.watcherExclude' diverge"),
    ("M5 sem a saida 75", "if not tem_codium and not marcador.exists():", "if False:", "C01", 1,
     "codium NAO instalado"),
    ("M6 sem raizes isentas no F20",
     'RAIZES_ISENTAS_F20 = {"internal", "cmd", "tools", "ops", "docs", "scripts", ".claude", "content"}',
     "RAIZES_ISENTAS_F20 = set()", "C03", 1, "fora do files.watcherExclude do workspace"),
    ("M7 F20 sem poda pelos padroes", "n = conta_subdiretorios(e.path, podar, limiar)",
     "n = conta_subdiretorios(e.path, lambda _p: False, limiar)", "C03", 1, ": mc — cada uma"),
    ("M8 sem a paridade extensao ⇄ CLI", "elif vers != [cli]:", "elif False:", "C09", 0, "check-ide-host: VERDE"),
    ("M9 igualdade sem tipo (False == 0)", "return type(a) is type(b) and a == b", "return a == b", "C13c", 0,
     "check-ide-host: VERDE"),
    ("M10 F20 sem o escopo do workspace",
     '("workspace", workspace_obj if isinstance(workspace_obj, dict) else None, workspace),', "", "C20", 0,
     "check-ide-host: VERDE"),
    ("M11 keyring aceita qualquer lista que contenha o pino", "elif primarios == [PINO_VSCODIUM]:",
     "elif PINO_VSCODIUM in primarios:", "C22b", 0, "check-ide-host: VERDE"),
    ("M12 gopls check sem -tags=devcmds", '"GOFLAGS": "-tags=devcmds", "GOTOOLCHAIN": "local"',
     '"GOTOOLCHAIN": "local"', "C03", 1, "o par gopls x toolchain x -tags=devcmds"),
    ("M13 sem a leitura do erro de tag", "if ERRO_DE_TAG in saida:", "if False:", "C21d", 0, "check-ide-host: VERDE"),
    ("M14 sem a comparacao com o pino do gopls", "elif modulo.group(1) != pino:", "elif False:", "C21c", 0,
     "check-ide-host: VERDE"),
    ("M15 piso do codium sem o engines das extensoes", "if len(versao) == 3 and (not achou or versao > piso):",
     "if False:", "C26", 0, "check-ide-host: VERDE"),
    ("M16 claudeCode.* fora das invariantes",
     "invariantes = [k for k in perfil_repo if k in PERFIL_INVARIANTES or k.startswith(PREFIXO_INVARIANTE)]",
     "invariantes = [k for k in perfil_repo if k in PERFIL_INVARIANTES]", "C13e", 0, "fora das invariantes: claudeCode.useTerminal"),
    ("M17 gopls sempre falha, com ou sem marcador", "grave = r.falha if marcador.exists() else r.aviso",
     "grave = r.falha", "C21j", 1, "FALHA  gopls-do-toolchain: gopls ausente"),
    ("M18 Continue instalado sem conferir o pino", "elif instaladas[ident] == {versao}:", "elif True:", "C24b", 0,
     "check-ide-host: VERDE"),
    ("M19 proibidas ignorando o arquivo", "    if caminho.is_file():\n        linhas = ",
     "    if False:\n        linhas = ", "C27", 0, "check-ide-host: VERDE"),
    ("M20 instalado so com a frase 'install ok installed' (o codium em hold some)",
     'return len(partes) == 3 and partes[2] == "installed"', 'return status == "install ok installed"',
     "C03", 1, "codium NAO instalado (dpkg: hold ok installed)"),
    ("M22 sem a conferencia das chaves AUSENTES", "        for chave in PERFIL_AUSENTES:\n            if chave in perfil_disco:",
     "        for chave in PERFIL_AUSENTES:\n            if False:", "C13g", 0, "check-ide-host: VERDE"),
    ("M23 go version -m com a config do go no home (telemetria no home do dono)",
     '**ambiente_go_sem_telemetria(str(home), config_go)})\n        compilador', '})\n        compilador',
     "C03", 1, "go version -m"),
    ("M24 sem a regua de chave absoluta em search.exclude", "                if padrao.startswith(\"/\"):",
     "                if False:", "C13j", 0, "check-ide-host: VERDE"),
    ("M25 sem ler a remocao pendente do marcador",
     'remocao_pendente = campos_do_marcador(marcador).get("remocao_vscode") == "pendente"', "remocao_pendente = False",
     "C31", 1, "FALHA  pacote code (VS Code) ainda instalado"),
    ("M21 pino do gopls sem a constante do instalador",
     r"""constantes = set(re.findall(r"^\s*GOPLS_VERSAO=[\"']?(v\d+\.\d+\.\d+)", texto, re.M))""",
     "constantes = set()", "C21f", 0, "sem GOPLS_VERSAO legivel"),
]


def unidades():
    """O glob e o JSONC direto, sem processo: sao o miolo do F20 e do perfil."""
    carregador = SourceFileLoader("check_ide_host", CHECK)
    m = importlib.util.module_from_spec(importlib.util.spec_from_loader("check_ide_host", carregador))
    carregador.exec_module(m)
    g = m.glob_para_regex
    for padrao, alvo, esperado in [
        ("**/node_modules/*/**", "mc/node_modules/p1", True),
        ("**/node_modules/*/**", "mc/node_modules/p1/lib/x", True),
        ("**/node_modules/*/**", "mc/node_modules", False),
        ("/r/pesada/**", "/r/pesada", True),
        ("/r/pesada/**", "/r/pesada/a/b", True),
        ("/r/pesada/**", "/r/pesadao", False),
        ("/opt/wiki/.venv*/**", "/opt/wiki/.venv-sca/lib", True),
        ("{a,b}/**", "b/x", True),
        ("{a,b}/**", "c/x", False),
        ("a/**/b", "a/b", True),
        ("a/**/b", "a/x/y/b", True),
        ("**", "qualquer/coisa", True),
        (".git/**", ".git/codex-private-go-cache/ab", True),
        ("**/.git/objects/**", ".git/codex-private-go-cache/ab", False),
    ]:
        caso(f"glob {padrao!r} ~ {alvo!r} -> {esperado}", bool(g(padrao).match(alvo)) is esperado)
    j = m.carrega_jsonc
    caso("JSONC: // dentro de string fica", j('{"u": "http://x//y"} // fim') == {"u": "http://x//y"})
    caso("JSONC: /* e */ dentro de string ficam",
         j('{"a": "**/node_modules/*/**", /* c */ "b": "**/x/**"}') == {"a": "**/node_modules/*/**", "b": "**/x/**"})
    caso("JSONC: aspa escapada nao fecha a string", j('{"a": "x\\"//y"}') == {"a": 'x"//y'})
    caso("JSONC: virgula final some", j('{"a": [1, 2,], "b": {"c": 1,},}') == {"a": [1, 2], "b": {"c": 1}})
    caso("igual: False != 0 e True != 1", not m.igual(False, 0) and not m.igual(True, 1) and m.igual(1, 1.0))
    arquivo = os.path.join(RAIZ_REPO, "ops/ide/extensoes-proibidas.txt")
    if os.path.exists(arquivo):
        do_arquivo, _ = m.le_proibidas(m.Path(arquivo))
        caso("ops/ide/extensoes-proibidas.txt e a lista embutida do check nao divergem",
             do_arquivo == {p.lower() for p in m.PROIBIDAS_EMBUTIDAS},
             f"so no arquivo: {sorted(do_arquivo - set(m.PROIBIDAS_EMBUTIDAS))}; so na embutida: {sorted(set(m.PROIBIDAS_EMBUTIDAS) - do_arquivo)}")
    caso("subconjunto: o disco pode ter a mais, nunca a menos",
         m.subconjunto({"a": {"x": 1}}, {"a": {"x": 1, "y": 2}}) and not m.subconjunto({"a": {"x": 1}}, {"a": {"y": 2}}))


def main():
    fonte = open(CHECK, encoding="utf-8").read()
    with tempfile.TemporaryDirectory(prefix="test-check-ide-host.") as tmp:
        print("── unidades (glob e JSONC)")
        unidades()

        print("── casos")
        todas_recusas = []
        por_nome = {}
        for nome, estraga, args, rc_esperado, trechos in CASOS:
            rc, saida, recusas = roda_caso(tmp, estraga, args)
            faltando = [t for t in trechos if t not in saida]
            caso(nome, rc == rc_esperado and not faltando,
                 f"rc={rc} (esperado {rc_esperado}); faltando {faltando}\n" + saida[-1500:])
            if recusas:
                todas_recusas.append(f"{nome}: {recusas.strip()}")
            por_nome[nome.split()[0]] = (estraga, args, rc_esperado)
        caso("nenhum duble recusou chamada: o check fala so o vocabulario conhecido", not todas_recusas,
             "\n".join(todas_recusas))

        print("── mutantes (o check real com uma linha trocada)")
        for nome, original, mutante, alvo, rc_sob_mutante, razao in MUTANTES:
            ocorrencias = fonte.count(original)
            if ocorrencias != 1:
                caso(nome, False, f"o trecho original aparece {ocorrencias} vez(es) no check: mutante nao aplicavel")
                continue
            codigo = fonte.replace(original, mutante)
            if codigo == fonte:
                caso(nome, False, "mutante identico ao original")
                continue
            caminho = os.path.join(tmp, "mutante-" + nome.split()[0])
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(codigo)
            estraga, args, rc_original = por_nome[alvo]
            rc, saida, _ = roda_caso(tmp, estraga, args, check=caminho)
            caso(f"{nome}: {alvo} vira de {rc_original} para {rc_sob_mutante}, pela razao certa",
                 rc == rc_sob_mutante and rc != rc_original and razao in saida,
                 f"rc sob o mutante = {rc}; razao {razao!r} {'presente' if razao in saida else 'AUSENTE'}\n" + saida[-800:])

    print()
    if FALHAS:
        print(f"test_check_ide_host: {len(FALHAS)} falha(s): {', '.join(FALHAS)}")
        return 1
    total = len(CASOS) + len(MUTANTES)
    print(f"test_check_ide_host: VERDE — {len(CASOS)} casos, {len(MUTANTES)} mutantes mortos ({total} vereditos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
