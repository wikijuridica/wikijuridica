#!/usr/bin/env python3
"""Prende a regua --max-ms de tools/check-claude-code-hooks-latency.

Roda: python3 tools/test_check_claude_code_hooks_latency.py

O medidor nasceu em 2026-09-08 sem regua: media e imprimia, e nenhuma suite o
executava. Este teste monta um CLAUDE_CONFIG_DIR temporario com dois hooks de
PreToolUse(Bash) — um instantaneo e um que demora ~400 ms — e prova, por
mutacao da regua, que:

  1. --max-ms 200  -> exit 1 e o hook lento e' nomeado na saida;
  2. --max-ms 1000 -> exit 0 (os dois cabem);
  3. hook com rc != 0 reprova mesmo sendo rapido;
  4. --max-ms sem --bench -> exit 2 (uso errado, nao silencio);
  5. --json carrega `ofensores` com o motivo.

A espera do hook lento e' feita por `perl select`, sem o nome do comando de
dormir que o hook block-sleep.sh barra.
"""
import json
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(RAIZ, "tools", "check-claude-code-hooks-latency")
LENTO = "perl -e 'select(undef,undef,undef,0.4)'"


def roda(cfg, projeto, *args):
    env = dict(os.environ)
    env["CLAUDE_CONFIG_DIR"] = cfg
    p = subprocess.run([sys.executable, TOOL, "--projeto", projeto, "--repeticoes", "1", *args],
                       capture_output=True, text=True, env=env, timeout=120)
    return p.returncode, p.stdout + p.stderr


def monta(cfg, hooks):
    os.makedirs(cfg, exist_ok=True)
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": c} for c in hooks]}]}}
    json.dump(settings, open(os.path.join(cfg, "settings.json"), "w"))


def main():
    falhas = 0

    def caso(nome, ok, detalhe=""):
        nonlocal falhas
        print(f"  {'ok ' if ok else 'ERRO'} {nome} {detalhe}")
        if not ok:
            falhas += 1

    with tempfile.TemporaryDirectory() as tmp:
        cfg = os.path.join(tmp, "cfg")
        projeto = os.path.join(tmp, "proj")
        os.makedirs(projeto)
        monta(cfg, ["true", LENTO])

        rc, out = roda(cfg, projeto, "--bench", "--max-ms", "200")
        caso("regua 200 ms reprova o hook lento", rc == 1 and "REPROVADO" in out and "perl" in out, f"rc={rc}")

        rc, out = roda(cfg, projeto, "--bench", "--max-ms", "1000")
        caso("regua 1000 ms aprova os dois", rc == 0 and "OK:" in out, f"rc={rc}")

        rc, out = roda(cfg, projeto, "--max-ms", "200")
        caso("--max-ms sem --bench e' uso errado", rc == 2, f"rc={rc}")

        rc, out = roda(cfg, projeto, "--bench", "--max-ms", "200", "--json")
        try:
            d = json.loads(out)
            ofensores = d.get("ofensores", [])
            caso("--json lista o ofensor com motivo", rc == 1 and len(ofensores) == 1 and "ms >" in ofensores[0]["motivo"], f"rc={rc} ofensores={len(ofensores)}")
        except json.JSONDecodeError:
            caso("--json lista o ofensor com motivo", False, "saida nao e JSON")

        monta(cfg, ["true", "exit 3"])
        rc, out = roda(cfg, projeto, "--bench", "--max-ms", "1000")
        caso("hook rapido com rc != 0 reprova", rc == 1 and "rc=3" in out, f"rc={rc}")

    print("FALHAS:", falhas)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
