#!/usr/bin/env python3
"""Contrato das configs do terminal do Claude Code versionadas em ops/terminal/.

Frente 10 do plano docs/plans/IDE_TERMINAL_20260923_PLANO.md (2026-09-23).
O kitty.conf ja perdeu, numa reescrita sem teste (2026-09-04), a linha
`map shift+enter send_text all \\e\\r` — "regressao de config sem teste". Este
arquivo e o teste que faltava: cada verificacao e uma funcao pura que devolve a
lista de problemas, e cada uma tem MUTANTES que ela tem de matar (memoria "teste e
aprendizado sao par": asserção que nao reprova um mutante nao testa nada).

O que e conferido:
  * kitty.conf: parser proprio `chave valor` + o parser do PROPRIO kitty
    (`kitty +runpy`, sem display, HOME/XDG no temporario); chaves obrigatorias;
  * tmux.conf: texto + servidor tmux ISOLADO (socket e HOME no temporario, config
    sem a linha do TPM, erro de config reportado por `source-file` — medido: o
    `-f arquivo start-server` engole o erro e sai 0) + um cliente num pty com
    TERM=xterm-kitty que responde DA1/DA2/XTVERSION como o kitty 0.47.4: o
    #{client_termfeatures} tem de conter `extkeys` (o gate que faltava);
  * nenhum segredo nos arquivos de ops/terminal;
  * nenhum caractere de controle (um `\\r` cru ja entrou no kitty.conf por escape
    de Python mal feito, medido nesta mesma frente);
  * ai-terminal.desktop valido (`desktop-file-validate`) e chamando o ai-terminal
    por caminho absoluto;
  * ai-terminal: kitty primeiro, WezTerm so no ramo --wezterm, nunca o launcher do
    Codex, fallback `exec bash -l` — por texto e por COMPORTAMENTO, com dubles no
    PATH que gravam o argv.

Rodar: python3 tools/test_terminal_conf.py   (saida 0 = verde)
Apontar para outra copia (prova por mutacao externa): TERMINAL_CONF_DIR=<dir>.
"""

from __future__ import annotations

import os
import pathlib
import pty
import re
import select
import shutil
import stat
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = pathlib.Path(os.environ.get("TERMINAL_CONF_DIR", ROOT / "ops" / "terminal"))
KITTY_CONF = DIR / "kitty.conf"
TMUX_CONF = DIR / "tmux.conf"
AI_TERMINAL = DIR / "ai-terminal"
DESKTOP = DIR / "ai-terminal.desktop"
LAUNCHER = DIR / "start-ai-terminal-claude.sh"
LINHA_TPM = "run '~/.tmux/plugins/tpm/tpm'"
LINHA_MAP = "map shift+enter send_text all \\e\\r"
BASE_TMP = "/tmp/claude-1000" if pathlib.Path("/tmp/claude-1000").is_dir() else None
HOME_ANTIGO_AI_TERMINAL = pathlib.Path.home() / ".local" / "bin" / "ai-terminal"


def achar_kitty() -> str | None:
    """O mesmo kitty que o ai-terminal resolve: ~/.local/bin na frente do PATH."""
    caminho = os.pathsep.join([str(pathlib.Path.home() / ".local" / "bin"), os.environ.get("PATH", "")])
    return shutil.which("kitty", path=caminho)


# --------------------------------------------------------------------- kitty.conf
def parse_kitty(texto: str) -> dict[str, list[str]]:
    """Parser proprio `chave valor`: ignora comentario e linha vazia; chave repetida acumula."""
    chaves: dict[str, list[str]] = {}
    for linha in texto.splitlines():
        crua = linha.strip()
        if not crua or crua.startswith("#"):
            continue
        partes = crua.split(None, 1)
        chaves.setdefault(partes[0], []).append(partes[1] if len(partes) > 1 else "")
    return chaves


def problemas_kitty(texto: str) -> list[str]:
    p: list[str] = []
    c = parse_kitty(texto)
    if c.get("linux_display_server") != ["x11"]:
        p.append(f"linux_display_server deveria ser x11, e {c.get('linux_display_server')}")
    if c.get("allow_remote_control") != ["socket-only"]:
        p.append(f"allow_remote_control deveria ser socket-only, e {c.get('allow_remote_control')}")
    clip = c.get("clipboard_control", [])
    if len(clip) != 1 or clip[0].split() != ["write-clipboard", "write-primary", "read-clipboard-ask", "read-primary-ask"]:
        p.append(f"clipboard_control deveria ser o default explicito, e {clip}")
    listen = c.get("listen_on", [])
    if len(listen) != 1 or not listen[0].startswith("unix:${XDG_RUNTIME_DIR}/") or "@" in listen[0]:
        p.append(f"listen_on deveria ser socket de arquivo em XDG_RUNTIME_DIR (nunca abstrato @), e {listen}")
    maps = [f"map {v}" for v in c.get("map", [])]
    if LINHA_MAP not in maps:
        p.append("map shift+enter send_text all \\e\\r ausente (decidido pela bancada; so sai com medicao)")
    for obrigatoria in ("font_family", "scrollback_lines", "repaint_delay", "input_delay"):
        if obrigatoria not in c:
            p.append(f"chave {obrigatoria} sumiu (reescrita sem teste?)")
    return p


def problemas_kitty_pelo_kitty(caminho: pathlib.Path) -> list[str]:
    """O parser do proprio kitty, sem display; linha ruim vira problema."""
    kitty = achar_kitty()
    if kitty is None:
        return []
    with tempfile.TemporaryDirectory(prefix="kitty-parse-", dir=BASE_TMP) as t:
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
        env.update(HOME=t, XDG_CONFIG_HOME=f"{t}/config", XDG_CACHE_HOME=f"{t}/cache")
        codigo = (
            "import sys\n"
            "from kitty.config import load_config\n"
            "ruins = []\n"
            "try:\n"
            "    load_config(sys.argv[-1], accumulate_bad_lines=ruins)\n"
            "except Exception as e:\n"
            "    print('EXCECAO', type(e).__name__, e)\n"
            "for r in ruins:\n"
            "    print('RUIM', r.number, r.line)\n"
        )
        r = subprocess.run([kitty, "+runpy", codigo, str(caminho)], capture_output=True,
                           text=True, env=env, timeout=60, check=False)
    saida = (r.stdout + r.stderr).strip()
    p = [linha for linha in saida.splitlines() if linha.startswith(("RUIM", "EXCECAO")) or "Ignoring" in linha]
    if r.returncode != 0 and not p:
        p.append(f"kitty +runpy saiu {r.returncode}: {saida[:300]}")
    return p


# ---------------------------------------------------------------------- tmux.conf
def problemas_tmux_texto(texto: str) -> list[str]:
    p: list[str] = []
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip() and not linha.strip().startswith("#")]

    def tem(regex: str) -> bool:
        return any(re.fullmatch(regex, linha) for linha in linhas)

    if not tem(r"set\s+-g\s+allow-passthrough\s+on"):
        p.append("set -g allow-passthrough on ausente")
    if not tem(r"set\s+-s\s+extended-keys\s+on"):
        p.append("set -s extended-keys on ausente")
    if not tem(r"set\s+-g\s+set-clipboard\s+on"):
        p.append("set -g set-clipboard on ausente")
    if not tem(r"set\s+-as\s+terminal-features\s+(['\"])xterm\*:extkeys\1"):
        p.append("set -as terminal-features 'xterm*:extkeys' ausente (doc do Claude Code, 'Configure tmux')")
    if tem(r"set\s+-as\s+terminal-features\s+(['\"]),xterm-256color:extkeys\1"):
        p.append("a linha antiga ',xterm-256color:extkeys' voltou: o kitty entra como xterm-kitty e fica sem extkeys")
    if linhas.count(LINHA_TPM) != 1:
        p.append("a linha do TPM tem de existir UMA vez: a bancada e este teste tiram exatamente ela")
    return p


def sem_tpm(texto: str) -> str:
    return "".join(linha for linha in texto.splitlines(keepends=True) if linha.strip() != LINHA_TPM)


def carrega_tmux(texto: str) -> tuple[int, str]:
    """Servidor tmux isolado (TMUX_TMPDIR e HOME no temporario), config sem TPM.

    `-f /dev/null start-server ; source-file cfg`: o `source-file` devolve o
    erro da config ao cliente (rc 1 + mensagem); o `-f cfg start-server` engole o
    erro e sai 0 — medido em 2026-09-23 com uma opcao inexistente.
    """
    with tempfile.TemporaryDirectory(prefix="tmux-conf-", dir=BASE_TMP) as t:
        cfg = pathlib.Path(t) / "tmux.conf"
        cfg.write_text(sem_tpm(texto), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
        env.update(HOME=t, TMUX_TMPDIR=t)
        r = subprocess.run(
            ["tmux", "-L", f"teste-{os.getpid()}", "-f", os.devnull, "start-server", ";",
             "source-file", str(cfg), ";",
             "show", "-gv", "allow-passthrough", ";", "show", "-sv", "extended-keys", ";",
             "show", "-gv", "set-clipboard", ";", "show", "-sv", "terminal-features"],
            capture_output=True, text=True, env=env, timeout=30, check=False)
        subprocess.run(["tmux", "-L", f"teste-{os.getpid()}", "kill-server"], env=env,
                       capture_output=True, timeout=10, check=False)
    return r.returncode, r.stdout + r.stderr


def problemas_tmux_carga(texto: str) -> list[str]:
    rc, saida = carrega_tmux(texto)
    linhas = saida.splitlines()
    p: list[str] = []
    if rc != 0:
        p.append(f"tmux recusou a config (rc={rc}): {saida.strip()[:300]}")
    if linhas[:3] != ["on", "on", "on"]:
        p.append(f"allow-passthrough/extended-keys/set-clipboard carregados = {linhas[:3]}")
    if "xterm*:extkeys" not in linhas:
        p.append("terminal-features carregado sem xterm*:extkeys")
    return p


RESPOSTAS_KITTY = {
    b"\x1b[c": b"\x1b[?62;c",
    b"\x1b[>c": b"\x1b[>1;4000;29c",
    b"\x1b[>q": b"\x1bP>|kitty(0.47.4)\x1b\\",
}


def termfeatures_de_cliente_kitty(texto: str) -> tuple[str, bool]:
    """Cliente tmux num pty com TERM=xterm-kitty; devolve (#{client_termfeatures}, Eneks enviado?)."""
    with tempfile.TemporaryDirectory(prefix="tmux-cliente-", dir=BASE_TMP) as t:
        cfg = pathlib.Path(t) / "tmux.conf"
        cfg.write_text(sem_tpm(texto), encoding="utf-8")
        sock = str(pathlib.Path(t) / "s")
        env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
        env.update(HOME=t, TERM="xterm-kitty")
        pid, fd = pty.fork()
        if pid == 0:  # pragma: no cover - processo filho
            os.execvpe("tmux", ["tmux", "-S", sock, "-f", str(cfg), "new-session", "-s", "t",
                                "-x", "100", "-y", "30", "cat"], env)
        recebido = bytearray()
        respondidas: set[bytes] = set()
        fim = time.monotonic() + 3.0
        while time.monotonic() < fim:
            pronto, _, _ = select.select([fd], [], [], 0.05)
            if not pronto:
                continue
            try:
                bloco = os.read(fd, 65536)
            except OSError:
                break
            if not bloco:
                break
            recebido.extend(bloco)
            for consulta, resposta in RESPOSTAS_KITTY.items():
                if consulta in recebido and consulta not in respondidas:
                    os.write(fd, resposta)
                    respondidas.add(consulta)
        r = subprocess.run(["tmux", "-S", sock, "list-clients", "-F", "#{client_termfeatures}"],
                           capture_output=True, text=True, env=env, timeout=10, check=False)
        subprocess.run(["tmux", "-S", sock, "kill-server"], env=env, capture_output=True,
                       timeout=10, check=False)
        fim = time.monotonic() + 1.0
        while time.monotonic() < fim:
            pronto, _, _ = select.select([fd], [], [], 0.05)
            if pronto:
                try:
                    if not os.read(fd, 65536):
                        break
                except OSError:
                    break
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        os.close(fd)
    return r.stdout.strip(), b"\x1b[>4;2m" in recebido


def problemas_tmux_cliente_kitty(texto: str) -> list[str]:
    features, eneks = termfeatures_de_cliente_kitty(texto)
    p: list[str] = []
    if "extkeys" not in features.split(","):
        p.append(f"cliente TERM=xterm-kitty sem extkeys em #{{client_termfeatures}}: {features!r}")
    if not eneks:
        p.append("o tmux nao pediu teclas estendidas (Eneks \\e[>4;2m) ao cliente kitty")
    return p


# ------------------------------------------------------------- segredo e controle
# A grep literal `token|senha|password|secret` acusou, MEDIDO em 2026-09-23, quatro
# ocorrencias e todas eram prosa ou nome de opcao: "token desperdicado" e "token de
# assinatura" (comentarios), "saturacao e tokens" (comentario do tmux.conf do dono)
# e a flag `--no-ask-password` do systemctl. Assinatura 100% num padrao sintatico e
# defeito do instrumento, nao do conteudo. A regua aqui e mais estrita onde importa:
# fora de comentario, qualquer uma dessas palavras reprova (salvo a flag nominada);
# e valor com cara de segredo reprova em QUALQUER linha, comentario inclusive.
PALAVRA_SEGREDO = re.compile(r"token|senha|password|secret", re.IGNORECASE)
PERMITIDAS_FORA_DE_COMENTARIO = ("--no-ask-password",)
VALOR_SEGREDO = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
# Sem `/`, `+` e `.` na classe: o primeiro corte acusou QUATRO caminhos de arquivo
# (docs/plans/IDE_TERMINAL_20260923_PLANO.md) e nenhum segredo — medido.
LONGO_MISTO = re.compile(r"[A-Za-z0-9_-]{32,}")


def problemas_segredo(nome: str, texto: str) -> list[str]:
    """Documentacao (.md) e prosa inteira: nela vale so a regua de VALOR."""
    p: list[str] = []
    prosa = nome.endswith(".md")
    for n, linha in enumerate(texto.splitlines(), 1):
        codigo = linha.strip()
        if codigo and not codigo.startswith("#") and not prosa:
            limpa = codigo
            for permitida in PERMITIDAS_FORA_DE_COMENTARIO:
                limpa = limpa.replace(permitida, "")
            if PALAVRA_SEGREDO.search(limpa):
                p.append(f"{nome}:{n}: palavra de segredo fora de comentario: {codigo[:120]}")
        if VALOR_SEGREDO.search(linha):
            p.append(f"{nome}:{n}: valor com formato de credencial")
        for bloco in LONGO_MISTO.findall(linha):
            if re.search(r"[A-Z]", bloco) and re.search(r"[a-z]", bloco) and re.search(r"[0-9]", bloco):
                p.append(f"{nome}:{n}: sequencia longa de alta entropia: {bloco[:12]}...")
    return p


def problemas_controle(nome: str, dados: bytes) -> list[str]:
    ruins = sorted({b for b in dados if b < 0x20 and b not in (0x09, 0x0A)} | ({0x7F} & set(dados)))
    return [f"{nome}: caracteres de controle {[hex(b) for b in ruins]}"] if ruins else []


# ------------------------------------------------------------------ .desktop
def problemas_desktop_texto(texto: str) -> list[str]:
    p: list[str] = []
    campos = dict(linha.split("=", 1) for linha in texto.splitlines() if "=" in linha and not linha.startswith("#"))
    esperado = "/home/rafael/.local/bin/ai-terminal"
    if campos.get("Exec") != esperado:
        p.append(f"Exec deveria ser {esperado} (o PATH da sessao grafica acharia o kitty 0.26.5 do apt), e {campos.get('Exec')!r}")
    if campos.get("TryExec") != esperado:
        p.append(f"TryExec deveria ser {esperado}, e {campos.get('TryExec')!r}")
    if "wezterm" in texto.lower():
        p.append("o .desktop ainda cita wezterm")
    if campos.get("Terminal") != "false" or campos.get("Type") != "Application":
        p.append("Type=Application e Terminal=false obrigatorios")
    return p


def problemas_desktop_validador(caminho: pathlib.Path) -> list[str]:
    validador = shutil.which("desktop-file-validate")
    if validador is None:
        return []
    r = subprocess.run([validador, str(caminho)], capture_output=True, text=True, timeout=30, check=False)
    return [] if r.returncode == 0 else [f"desktop-file-validate: {(r.stdout + r.stderr).strip()[:300]}"]


# -------------------------------------------------------------- ai-terminal
def linhas_de_codigo(texto: str) -> list[str]:
    return [linha for linha in texto.splitlines() if linha.strip() and not linha.strip().startswith("#")]


def problemas_ai_terminal(texto: str) -> list[str]:
    p: list[str] = []
    codigo = linhas_de_codigo(texto)
    corpo = "\n".join(codigo)
    if re.search(r"start-ai-terminal\.sh", corpo):
        p.append("o ai-terminal chama o launcher do Codex (start-ai-terminal.sh)")
    if "start-ai-terminal-claude.sh" not in corpo:
        p.append("o ai-terminal nao usa o launcher Claude-first")
    # WezTerm so dentro do ramo --wezterm: o bloco `if [ "$usar_wezterm" -eq 1 ]` e o
    # braco `--wezterm)` do case sao os unicos lugares permitidos.
    dentro = False
    for linha in codigo:
        s = linha.strip()
        if s.startswith('if [ "$usar_wezterm" -eq 1 ]'):
            dentro = True
            continue
        if dentro and s == "fi" and linha.startswith("fi"):
            dentro = False
            continue
        if not dentro and "wezterm" in s.lower() and not s.startswith("--wezterm)"):
            if s == "usar_wezterm=0" or s.startswith("--wezterm) usar_wezterm=1"):
                continue
            p.append(f"wezterm fora do ramo --wezterm: {s[:100]}")
    if not codigo or codigo[-1].strip() != "exec bash -l":
        p.append("o fallback final `exec bash -l` sumiu")
    if not re.search(r'exec "\$kitty_bin" --title "AI Terminal" -- "\$\{programa\[@\]\}"', corpo):
        p.append('a linha `exec "$kitty_bin" --title "AI Terminal" -- "${programa[@]}"` sumiu')
    posicao_path = corpo.find('export PATH="$HOME/.local/bin:')
    posicao_kitty = corpo.find("command -v kitty")
    if posicao_path < 0 or posicao_kitty < 0 or posicao_path > posicao_kitty:
        p.append("~/.local/bin tem de entrar na frente do PATH ANTES de procurar o kitty")
    return p


class TerminalConfContratoTest(unittest.TestCase):
    """As configs entregues passam."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.kitty = KITTY_CONF.read_text(encoding="utf-8")
        cls.tmux = TMUX_CONF.read_text(encoding="utf-8")
        cls.desktop = DESKTOP.read_text(encoding="utf-8")
        cls.ai_terminal = AI_TERMINAL.read_text(encoding="utf-8")

    def test_kitty_conf_parser_proprio(self) -> None:
        self.assertEqual(problemas_kitty(self.kitty), [])

    @unittest.skipIf(achar_kitty() is None, "kitty ausente: so o parser proprio")
    def test_kitty_conf_parser_do_kitty(self) -> None:
        self.assertEqual(problemas_kitty_pelo_kitty(KITTY_CONF), [])

    def test_tmux_conf_texto(self) -> None:
        self.assertEqual(problemas_tmux_texto(self.tmux), [])

    @unittest.skipIf(shutil.which("tmux") is None, "tmux ausente: so a analise textual")
    def test_tmux_conf_carrega_em_servidor_isolado(self) -> None:
        self.assertEqual(problemas_tmux_carga(self.tmux), [])

    @unittest.skipIf(shutil.which("tmux") is None, "tmux ausente")
    def test_cliente_kitty_tem_extkeys_e_recebe_eneks(self) -> None:
        self.assertEqual(problemas_tmux_cliente_kitty(self.tmux), [])

    def test_nenhum_segredo_em_ops_terminal(self) -> None:
        achados: list[str] = []
        for caminho in sorted(DIR.rglob("*")):
            if caminho.is_file() and "__pycache__" not in caminho.parts:
                achados += problemas_segredo(caminho.name, caminho.read_text(encoding="utf-8", errors="replace"))
        self.assertEqual(achados, [])

    def test_nenhum_caractere_de_controle(self) -> None:
        achados: list[str] = []
        for caminho in sorted(DIR.rglob("*")):
            if caminho.is_file() and "__pycache__" not in caminho.parts:
                achados += problemas_controle(caminho.name, caminho.read_bytes())
        self.assertEqual(achados, [])

    def test_desktop_texto(self) -> None:
        self.assertEqual(problemas_desktop_texto(self.desktop), [])

    @unittest.skipIf(shutil.which("desktop-file-validate") is None, "desktop-file-validate ausente")
    def test_desktop_valido(self) -> None:
        self.assertEqual(problemas_desktop_validador(DESKTOP), [])

    def test_ai_terminal_texto(self) -> None:
        self.assertEqual(problemas_ai_terminal(self.ai_terminal), [])

    def test_modos_de_arquivo(self) -> None:
        for nome in ("ai-terminal", "start-ai-terminal-claude.sh", "instalar-terminal.sh", "testa-terminal.sh"):
            modo = stat.S_IMODE((DIR / nome).stat().st_mode)
            self.assertEqual(modo & 0o755, 0o755, f"{nome} sem permissao de execucao ({oct(modo)})")
        for nome in ("kitty.conf", "tmux.conf", "ai-terminal.desktop"):
            modo = stat.S_IMODE((DIR / nome).stat().st_mode)
            self.assertFalse(modo & 0o111, f"{nome} nao deveria ser executavel ({oct(modo)})")

    def test_scripts_passam_bash_n(self) -> None:
        for nome in ("ai-terminal", "start-ai-terminal-claude.sh", "instalar-terminal.sh", "testa-terminal.sh"):
            r = subprocess.run(["bash", "-n", str(DIR / nome)], capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 0, f"{nome}: {r.stderr}")

    @unittest.skipIf(shutil.which("shellcheck") is None, "shellcheck ausente")
    def test_scripts_passam_shellcheck(self) -> None:
        nomes = [str(DIR / n) for n in ("ai-terminal", "start-ai-terminal-claude.sh", "instalar-terminal.sh", "testa-terminal.sh")]
        r = subprocess.run(["shellcheck", "-S", "warning", "-x", *nomes], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])


class TerminalConfMutantesTest(unittest.TestCase):
    """Cada verificacao mata os mutantes que existem para ela."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.kitty = KITTY_CONF.read_text(encoding="utf-8")
        cls.tmux = TMUX_CONF.read_text(encoding="utf-8")
        cls.desktop = DESKTOP.read_text(encoding="utf-8")
        cls.ai_terminal = AI_TERMINAL.read_text(encoding="utf-8")

    def _troca(self, texto: str, velho: str, novo: str) -> str:
        self.assertEqual(texto.count(velho), 1, f"ancora do mutante nao e unica: {velho!r}")
        return texto.replace(velho, novo)

    def test_mutantes_do_kitty_conf(self) -> None:
        mutantes = {
            "k1 sem linux_display_server": self._troca(self.kitty, "linux_display_server x11\n", ""),
            "k2 remote control aberto": self._troca(self.kitty, "allow_remote_control socket-only", "allow_remote_control yes"),
            "k3 sem clipboard_control": self._troca(
                self.kitty, "clipboard_control write-clipboard write-primary read-clipboard-ask read-primary-ask\n", ""),
            "k4 socket abstrato": self._troca(
                self.kitty, "listen_on unix:${XDG_RUNTIME_DIR}/kitty-{kitty_pid}.sock", "listen_on unix:@kitty"),
            "k5 sem o map de Shift+Enter (a regressao de 2026-09-04)": self._troca(self.kitty, LINHA_MAP + "\n", ""),
            "k6 leitura do clipboard sem perguntar": self._troca(
                self.kitty, "read-clipboard-ask read-primary-ask", "read-clipboard read-primary"),
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_kitty(texto), [], f"mutante sobreviveu: {nome}")

    @unittest.skipIf(achar_kitty() is None, "kitty ausente")
    def test_mutante_linha_ruim_no_parser_do_kitty(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kitty-mutante-", dir=BASE_TMP) as t:
            caminho = pathlib.Path(t) / "kitty.conf"
            caminho.write_text(self.kitty + "\nchave_que_o_kitty_nao_conhece 1\n", encoding="utf-8")
            self.assertNotEqual(problemas_kitty_pelo_kitty(caminho), [], "linha desconhecida passou")
            caminho.write_text(self.kitty.replace("font_size        15.0", "font_size        quinze"), encoding="utf-8")
            self.assertNotEqual(problemas_kitty_pelo_kitty(caminho), [], "valor invalido passou")

    def test_mutantes_do_tmux_conf_texto(self) -> None:
        antiga = "set -as terminal-features ',xterm-256color:extkeys'"
        mutantes = {
            "t1 linha antiga de volta": self._troca(self.tmux, "set -as terminal-features 'xterm*:extkeys'", antiga),
            "t2 passthrough desligado": self._troca(self.tmux, "set -g allow-passthrough on", "set -g allow-passthrough off"),
            "t3 sem extended-keys": self._troca(self.tmux, "set -s extended-keys on\n", ""),
            "t4 clipboard externo": self._troca(self.tmux, "set -g set-clipboard on", "set -g set-clipboard external"),
            "t5 TPM duplicado": self.tmux + "\n" + LINHA_TPM + "\n",
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_tmux_texto(texto), [], f"mutante sobreviveu: {nome}")

    @unittest.skipIf(shutil.which("tmux") is None, "tmux ausente")
    def test_mutantes_do_tmux_conf_carregado(self) -> None:
        mutantes = {
            "c1 opcao inexistente": self.tmux + "\nset -g opcao-que-nao-existe on\n",
            "c2 passthrough desligado no fim": self.tmux + "\nset -g allow-passthrough off\n",
            "c3 extkeys removido": self._troca(self.tmux, "set -as terminal-features 'xterm*:extkeys'",
                                               "set -as terminal-features ',xterm-256color:extkeys'"),
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_tmux_carga(texto), [], f"mutante sobreviveu: {nome}")

    @unittest.skipIf(shutil.which("tmux") is None, "tmux ausente")
    def test_mutante_do_cliente_kitty_sem_extkeys(self) -> None:
        # O MESMO texto do ~/.tmux.conf de 2026-09-04: o cliente kitty fica sem extkeys.
        antigo = self._troca(self.tmux, "set -as terminal-features 'xterm*:extkeys'",
                             "set -as terminal-features ',xterm-256color:extkeys'")
        self.assertNotEqual(problemas_tmux_cliente_kitty(antigo), [], "a linha antiga passou no cliente kitty")

    def test_mutantes_de_segredo_e_controle(self) -> None:
        self.assertNotEqual(problemas_segredo("k", self.kitty + '\nremote_control_password "hunter2hunter2" ls\n'), [])
        self.assertNotEqual(problemas_segredo("l", "export ANTHROPIC_API_KEY=sk-ant-api03-AbCdEfGh0123456789\n"), [])
        self.assertNotEqual(problemas_segredo("c", "# chave antiga: ghp_AbCdEfGhIjKlMnOpQrStUvWxYz0123\n"), [])
        self.assertNotEqual(problemas_segredo("g", 'api_key = "Zx9Qw8Er7Ty6Ui5Op4As3Df2Gh1Jk0LmNb"\n'), [])
        self.assertNotEqual(problemas_segredo("LEIA.md", "use a chave sk-ant-api03-AbCdEfGh0123456789 aqui\n"), [])
        # controle negativo: prosa, caminho, pino sha256 e nome de variavel passam.
        self.assertEqual(problemas_segredo("n", "# token de assinatura\n"
                                                "# docs/plans/IDE_TERMINAL_20260923_PLANO.md\n"
                                                "  [x.ttf]=1c680e8cde9fcf8b88a5605ce8d1fb94dd3fb15841f7ca7bf4c55664855e5611\n"
                                                "export CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=512\n"
                                                "systemctl --no-ask-password start x\n"), [])
        self.assertNotEqual(problemas_controle("k", self.kitty.replace("`\\r`", "`\r`", 1).encode()), [])

    def test_mutantes_do_desktop(self) -> None:
        mutantes = {
            "d1 Exec=kitty puro (resolve o 0.26.5 do apt)": self._troca(
                self.desktop, "\nExec=/home/rafael/.local/bin/ai-terminal",
                '\nExec=kitty --title "AI Terminal" -- /home/rafael/start-ai-terminal-claude.sh'),
            "d2 icone do wezterm": self._troca(self.desktop, "Icon=kitty", "Icon=org.wezfurlong.wezterm"),
            "d3 Terminal=true": self._troca(self.desktop, "Terminal=false", "Terminal=true"),
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_desktop_texto(texto), [], f"mutante sobreviveu: {nome}")

    @unittest.skipIf(shutil.which("desktop-file-validate") is None, "desktop-file-validate ausente")
    def test_mutante_desktop_invalido(self) -> None:
        with tempfile.TemporaryDirectory(prefix="desktop-mutante-", dir=BASE_TMP) as t:
            caminho = pathlib.Path(t) / "ai-terminal.desktop"
            caminho.write_text(self.desktop.replace("Type=Application\n", ""), encoding="utf-8")
            self.assertNotEqual(problemas_desktop_validador(caminho), [], "desktop sem Type passou")

    def test_mutantes_do_ai_terminal(self) -> None:
        mutantes = {
            "a1 launcher do Codex": self._troca(
                self.ai_terminal, 'launcher="${AI_TERMINAL_LAUNCHER:-$HOME/start-ai-terminal-claude.sh}"',
                'launcher="${AI_TERMINAL_LAUNCHER:-$HOME/start-ai-terminal.sh}"'),
            "a2 sem o fallback final": self.ai_terminal.rstrip("\n").rsplit("\n", 1)[0] + "\n",
            "a3 wezterm sempre primeiro": self._troca(
                self.ai_terminal, 'if [ "$usar_wezterm" -eq 1 ]; then', 'if [ "$usar_wezterm" -eq 0 ] || true; then'),
            "a4 kitty sem titulo e sem --": self._troca(
                self.ai_terminal, 'exec "$kitty_bin" --title "AI Terminal" -- "${programa[@]}"',
                'exec "$kitty_bin" "${programa[@]}"'),
            "a5 PATH depois de achar o kitty": self._troca(
                self.ai_terminal,
                'export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/bin:$HOME/go/bin:$HOME/.cargo/bin:/usr/local/go/bin:/snap/bin:$PATH"\n',
                "") + 'export PATH="$HOME/.local/bin:$PATH"\n',
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_ai_terminal(texto), [], f"mutante sobreviveu: {nome}")

    @unittest.skipUnless(HOME_ANTIGO_AI_TERMINAL.is_file() and not HOME_ANTIGO_AI_TERMINAL.is_symlink(),
                         "o ai-terminal antigo do home ja foi trocado pelo symlink")
    def test_o_ai_terminal_antigo_do_home_reprova(self) -> None:
        # O arquivo que existia em 2026-07-14: WezTerm primeiro e launcher do Codex.
        self.assertNotEqual(problemas_ai_terminal(HOME_ANTIGO_AI_TERMINAL.read_text(encoding="utf-8")), [])


class AiTerminalComportamentoTest(unittest.TestCase):
    """O ai-terminal de verdade, com dubles no PATH que gravam o argv."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-terminal-", dir=BASE_TMP)
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.home = base / "home"
        self.bin = base / "bin"
        self.registro = base / "argv.txt"
        self.home.mkdir()
        self.bin.mkdir()
        self.launcher = self.home / "start-ai-terminal-claude.sh"
        self.launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.launcher.chmod(0o755)

    def _duble(self, nome: str) -> None:
        caminho = self.bin / nome
        caminho.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"{nome}\" > '{self.registro}'\n"
            f"for a in \"$@\"; do printf '%s\\n' \"$a\" >> '{self.registro}'; done\n",
            encoding="utf-8")
        caminho.chmod(0o755)

    def _roda(self, *args: str) -> list[str]:
        env = {"HOME": str(self.home), "PATH": str(self.bin), "LANG": "C.UTF-8"}
        r = subprocess.run(["/bin/bash", str(AI_TERMINAL), *args], env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.registro.exists(), f"nenhum duble chamado; stderr={r.stderr}")
        return self.registro.read_text(encoding="utf-8").splitlines()

    def test_kitty_primeiro_com_o_launcher_claude_first(self) -> None:
        self._duble("kitty")
        self._duble("wezterm")
        self.assertEqual(self._roda("--claude"),
                         ["kitty", "--title", "AI Terminal", "--", str(self.launcher), "--claude"])

    def test_wezterm_so_com_a_bandeira(self) -> None:
        self._duble("kitty")
        self._duble("wezterm")
        argv = self._roda("--wezterm", "--claude")
        self.assertEqual(argv[0], "wezterm")
        self.assertEqual(argv[-2:], [str(self.launcher), "--claude"])
        self.assertNotIn("--wezterm", argv)
        self.assertNotIn(str(self.home / "start-ai-terminal.sh"), argv)

    def test_bandeira_wezterm_sem_wezterm_cai_no_kitty(self) -> None:
        self._duble("kitty")
        self.assertEqual(self._roda("--wezterm")[:4], ["kitty", "--title", "AI Terminal", "--"])

    def test_launcher_ausente_abre_bash_de_login_no_kitty(self) -> None:
        self._duble("kitty")
        self.launcher.chmod(0o644)
        self.assertEqual(self._roda(), ["kitty", "--title", "AI Terminal", "--", "bash", "-l"])

    def test_sem_kitty_e_sem_tty_abre_o_terminal_do_xfce(self) -> None:
        self._duble("xfce4-terminal")
        self.assertEqual(self._roda(), ["xfce4-terminal"])

    def test_sem_terminal_nenhum_cai_em_bash_de_login(self) -> None:
        self._duble("bash")
        self.assertEqual(self._roda(), ["bash", "-l"])


INSTALADOR = DIR / "instalar-terminal.sh"
ARQUIVOS_DO_KIT = ("kitty.conf", "tmux.conf", "start-ai-terminal-claude.sh", "ai-terminal",
                   "ai-terminal.desktop", "instalar-terminal.sh")
LINKS = {
    ".config/kitty/kitty.conf": "kitty.conf",
    ".tmux.conf": "tmux.conf",
    "start-ai-terminal-claude.sh": "start-ai-terminal-claude.sh",
    ".local/bin/ai-terminal": "ai-terminal",
    ".local/share/applications/ai-terminal.desktop": "ai-terminal.desktop",
}


@unittest.skipIf(shutil.which("tmux") is None or achar_kitty() is None, "instalador exige tmux e kitty")
class InstaladorComportamentoTest(unittest.TestCase):
    """O instalar-terminal.sh de verdade num HOME falso, com dubles de xfconf-query,
    curl e fc-cache no PATH (recusam com 99: nada de rede nem de xfconf real).
    Uma copia do kit num diretorio proprio permite rodar os MUTANTES do instalador."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="instalador-", dir=BASE_TMP)
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.home = base / "home"
        self.kit = base / "kit"
        self.bin = base / "bin"
        self.chamadas = base / "chamadas.txt"
        for d in (self.home, self.kit, self.bin):
            d.mkdir()
        for nome in ARQUIVOS_DO_KIT:
            shutil.copy2(DIR / nome, self.kit / nome)
        # O home que o dono tem hoje, em miniatura (conteudo marcado para provar o mv).
        self.originais = {
            ".config/kitty/kitty.conf": "# kitty do dono\nfont_size 15.0\n",
            ".tmux.conf": "# tmux do dono\nset -g mouse on\n",
            "start-ai-terminal-claude.sh": "#!/bin/sh\n# launcher do dono\n",
            ".local/bin/ai-terminal": "#!/bin/sh\n# ai-terminal do dono (wezterm)\n",
            ".local/share/applications/ai-terminal.desktop": "[Desktop Entry]\nName=AI Terminal\n",
            ".local/share/applications/claude-code.desktop": "[Desktop Entry]\nName=Claude Code\n",
            ".local/share/applications/codex-terminal.desktop": "[Desktop Entry]\nName=Codex\n",
            ".config/xfce4/helpers.rc": "TerminalEmulator=xfce4-terminal\n\nWebBrowser=google-chrome\n",
        }
        for rel, conteudo in self.originais.items():
            alvo = self.home / rel
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(conteudo, encoding="utf-8")
        fontes = pathlib.Path.home() / ".local/share/fonts/JetBrainsMonoNF"
        if fontes.is_dir():
            (self.home / ".local/share/fonts").mkdir(parents=True, exist_ok=True)
            (self.home / ".local/share/fonts/JetBrainsMonoNF").symlink_to(fontes)
        for nome, saida in (("xfconf-query", "Canais:\n  xfce4-panel\n"), ("curl", ""), ("fc-cache", "")):
            duble = self.bin / nome
            duble.write_text(
                "#!/bin/sh\n"
                f"printf '%s %s\\n' '{nome}' \"$*\" >> '{self.chamadas}'\n"
                + (f"[ \"$1\" = -l ] && printf '{saida}' && exit 0\n" if nome == "xfconf-query" else "")
                + "exit 99\n", encoding="utf-8")
            duble.chmod(0o755)

    def _roda(self, *args: str, instalador: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env.update(HOME=str(self.home), TERMINAL_KIT_TMP=str(pathlib.Path(self.tmp.name) / "t"),
                   PATH=os.pathsep.join([str(self.bin), str(pathlib.Path.home() / ".local/bin"), env.get("PATH", "")]))
        env.pop("DISPLAY", None)
        return subprocess.run(["/bin/bash", str(instalador or self.kit / "instalar-terminal.sh"), *args],
                              env=env, capture_output=True, text=True, timeout=120, check=False)

    def _foto(self) -> dict[str, str]:
        foto = {}
        for caminho in sorted(self.home.rglob("*")):
            rel = str(caminho.relative_to(self.home))
            if caminho.is_symlink():
                foto[rel] = "->" + os.readlink(caminho)
            elif caminho.is_file():
                foto[rel] = caminho.read_text(encoding="utf-8", errors="replace")
        return foto

    def test_seco_nao_muda_nada_no_home(self) -> None:
        antes = self._foto()
        r = self._roda("--seco")
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr)
        self.assertIn("[seco] mv --", r.stdout)
        self.assertEqual(self._foto(), antes)

    def test_aplica_liga_arquiva_preserva_e_e_idempotente(self) -> None:
        r = self._roda()
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr)
        for rel, nome in LINKS.items():
            with self.subTest(link=rel):
                self.assertTrue((self.home / rel).is_symlink())
                self.assertEqual((self.home / rel).resolve(), (self.kit / nome).resolve())
        # o conteudo antigo foi MOVIDO, byte a byte, nunca apagado
        for rel in (".config/kitty/kitty.conf", ".tmux.conf", "start-ai-terminal-claude.sh", ".local/bin/ai-terminal"):
            with self.subTest(backup=rel):
                backups = list((self.home / rel).parent.glob(pathlib.Path(rel).name + ".bak-*"))
                self.assertEqual(len(backups), 1, backups)
                self.assertEqual(backups[0].read_text(encoding="utf-8"), self.originais[rel])
        arquivo = list(self.home.glob(".local/share/archive-vscode-*/desktop"))
        self.assertEqual(len(arquivo), 1)
        for nome in ("ai-terminal.desktop", "claude-code.desktop", "codex-terminal.desktop"):
            with self.subTest(desktop=nome):
                self.assertEqual((arquivo[0] / nome).read_text(encoding="utf-8"),
                                 self.originais[".local/share/applications/" + nome])
        for nome in ("claude-code.desktop", "codex-terminal.desktop"):
            self.assertFalse((self.home / ".local/share/applications" / nome).exists())
        rc = (self.home / ".config/xfce4/helpers.rc").read_text(encoding="utf-8").splitlines()
        self.assertIn("TerminalEmulator=kitty", rc)
        self.assertIn("WebBrowser=google-chrome", rc)
        self.assertNotIn("TerminalEmulator=xfce4-terminal", rc)
        chamadas = self.chamadas.read_text(encoding="utf-8") if self.chamadas.exists() else ""
        self.assertNotIn("curl", chamadas, "nao podia baixar nada: a fonte ja existe")
        self.assertNotRegex(chamadas, r"xfconf-query -c", "canal inexistente: nao podia gravar no xfconf")
        # segunda rodada: nada a fazer
        antes = self._foto()
        r2 = self._roda()
        self.assertEqual(r2.returncode, 0, r2.stdout[-3000:])
        self.assertNotIn("  faz    ", r2.stdout)
        self.assertEqual(self._foto(), antes)
        self.assertEqual(self._roda("--verificar").returncode, 0)

    def test_pre_requisito_reprovado_nao_muda_o_home(self) -> None:
        (self.kit / "kitty.conf").write_text((self.kit / "kitty.conf").read_text(encoding="utf-8")
                                             + "\nchave_que_o_kitty_nao_conhece 1\n", encoding="utf-8")
        antes = self._foto()
        r = self._roda()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("NADA foi alterado", r.stdout)
        self.assertEqual(self._foto(), antes)

    def _mutante(self, velho: str, novo: str) -> pathlib.Path:
        texto = (self.kit / "instalar-terminal.sh").read_text(encoding="utf-8")
        self.assertIn(velho, texto, f"ancora do mutante sumiu: {velho!r}")
        mutante = self.kit / "instalar-mutante.sh"
        mutante.write_text(texto.replace(velho, novo), encoding="utf-8")
        mutante.chmod(0o755)
        return mutante

    def test_mutante_cp_no_lugar_de_mv_e_pego(self) -> None:
        r = self._roda(instalador=self._mutante('faz mv -- "$f"', 'faz cp -p -- "$f"'))
        self.assertNotEqual(r.returncode, 0, "cp deixou o atalho antigo no menu e passou")

    def test_mutante_sem_backup_e_pego(self) -> None:
        self._roda(instalador=self._mutante('    faz mv -- "$link" "$backup" || { falha "mv $link"; return 0; }\n',
                                            '    faz ln -sfn -- "$alvo" "$link"; return 0\n'))
        backups = list(self.home.rglob("*.bak-*"))
        self.assertLess(len([b for b in backups if "helpers" not in b.name]), 4,
                        "sem o mv os backups nao existem — o mutante tem de ser visivel aqui")

    def test_mutante_que_perde_as_outras_chaves_do_helpers_e_pego(self) -> None:
        self._roda(instalador=self._mutante('grep -v \'^TerminalEmulator=\' "$rc" > "$TMPD/helpers.rc"', ': > "$TMPD/helpers.rc"'))
        rc = (self.home / ".config/xfce4/helpers.rc").read_text(encoding="utf-8").splitlines()
        self.assertNotIn("WebBrowser=google-chrome", rc, "o mutante tinha de apagar a outra chave")


if __name__ == "__main__":
    unittest.main(verbosity=2)
