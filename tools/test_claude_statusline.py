#!/usr/bin/env python3
"""Prende ops/claude-code/statusline.sh (status line do Claude Code).

Roda: python3 tools/test_claude_statusline.py

O que prova, contra o script real:
  1. fixtura = o "Full JSON schema" de https://code.claude.com/docs/en/statusline.md
     (copiado da doc em 2026-09-23), com workspace.current_dir apontando para um repo
     de mentira: modelo, dir, ramo, ctx com cor, US$, cache e 5h saem certos;
  2. fixtura minima (so' modelo e diretorio) e fixtura sem rate_limits/prompt_cache
     (os dois que a doc diz poderem faltar): sem erro, segmento omitido, "ctx --";
  3. cores nas fronteiras da doc: 69 verde, 70 amarelo, 89 amarelo, 90 vermelho;
  4. ramo por leitura de .git/HEAD: subindo de subdiretorio, HEAD destacado (sha de 7),
     `.git` arquivo de worktree ("gitdir: ...") e fora de repo (sem parenteses);
  5. custo de processo: com PATH contendo SO um `git` e um `jq` que contam as proprias
     invocacoes, o script chama `git` 0 vez e `jq` 1 vez — e qualquer outro comando
     externo nao existe nesse PATH, entao um fork a mais vira erro visivel; com strace,
     conta exatamente 2 execve (o bash e o jq);
  6. custo: 20 execucoes do SCRIPT intercaladas com 20 do `jq` sozinho, cronometradas
     por $EPOCHREALTIME num bash (sem o spawn do Python). SEMPRE: p50(script) -
     p50(jq) < 15 ms — os dois sob a mesma carga, entao a diferenca e' o que o script
     acrescenta. p50 absoluto < 50 ms so' com loadavg de 1 min abaixo de 1,0 (maquina
     ociosa); acima disso ele sai impresso, sem veredito. A bancada diaria roda sob
     `nice`/`ionice -c3` com load de 9 a 22 documentado, o jq sozinho foi de 26 a 57 ms
     com o gopls a 439% de CPU, e em 2026-09-23 o absoluto asserido a partir de "load
     abaixo da metade das CPUs" piscou: load 2,82, p50 52,8 ms com o jq sozinho a 45,2 ms
     (a diferenca, 7,6 ms, passou). Relogio sob carga alheia nao e' defeito do script, e o
     runner so' perdoa relogio em timeout.
Depois, a prova por mutacao: cada mutante (cor removida, campo trocado, faixa movida,
`git` chamado, fork a mais, cache sem x100, sem subir diretorio, sem worktree, custo sem
dois digitos, janela de 7 dias no lugar da de 5 h, volta ao @tsv com IFS tab, laco
caro sem fork — que so' a medicao de custo apanha) tem de reprovar a suite.
"""
from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(RAIZ, "ops", "claude-code", "statusline.sh")
BASH = "/bin/bash"
VERDE, AMARELO, VERMELHO, RESET = "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[0m"
MARGEM_SOBRE_JQ_MS = 15  # bash + leitura do HEAD + formatacao; medido: 4-7,6 ms
CARGA_OCIOSA = 1.0  # abaixo disto o p50 absoluto e' asserido; acima, so' impresso


def carga_1min() -> float | None:
    try:
        with open("/proc/loadavg") as fh:
            return float(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None

# "Full JSON schema" da doc (statusline.md), literal exceto os caminhos, que o teste troca.
ESQUEMA_DOC = {
    "cwd": "/current/working/directory",
    "session_id": "abc123...",
    "session_name": "my-session",
    "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
    "transcript_path": "/path/to/transcript.jsonl",
    "model": {"id": "claude-opus-5-5", "display_name": "Opus"},
    "workspace": {"current_dir": "/current/working/directory", "project_dir": "/original/project/directory",
                  "added_dirs": [], "git_worktree": "feature-xyz",
                  "repo": {"host": "github.com", "owner": "anthropics", "name": "claude-code"}},
    "version": "2.1.90",
    "output_style": {"name": "default"},
    "cost": {"total_cost_usd": 0.01234, "total_duration_ms": 45000, "total_api_duration_ms": 2300,
             "total_lines_added": 156, "total_lines_removed": 23},
    "context_window": {"total_input_tokens": 15500, "total_output_tokens": 1200, "context_window_size": 200000,
                       "used_percentage": 8, "remaining_percentage": 92,
                       "current_usage": {"input_tokens": 8500, "output_tokens": 1200,
                                         "cache_creation_input_tokens": 5000, "cache_read_input_tokens": 2000}},
    "exceeds_200k_tokens": False,
    "prompt_cache": {"warm": True, "caching_observed": True, "ttl": "1h", "expires_at": 1738429200, "requests": 14,
                     "misses": 2, "expected_rebuilds": 1, "hit_ratio": 0.91, "cache_write_tokens": 352000,
                     "miss_recache_tokens": 310200, "last_miss_at": 1738425230,
                     "last_miss_cause": {"causes": ["tools_changed"], "tools_added": 2, "tools_removed": 0},
                     "miss_causes": {"tools_changed": 2}, "recache_tokens_if_cold": 45000},
    "fast_mode": False,
    "effort": {"level": "high"},
    "thinking": {"enabled": True},
    "rate_limits": {"five_hour": {"used_percentage": 23.5, "resets_at": 1738425600},
                    "seven_day": {"used_percentage": 41.2, "resets_at": 1738857600},
                    "spend_limit": {"used_percentage": 62.8, "resets_at": 1740787200}},
    "vim": {"mode": "NORMAL"},
    "agent": {"name": "security-reviewer"},
    "pr": {"number": 1234, "url": "https://github.com/anthropics/claude-code/pull/1234", "review_state": "pending"},
    "worktree": {"name": "my-feature", "path": "/path/to/.claude/worktrees/my-feature", "branch": "worktree-my-feature",
                 "original_cwd": "/path/to/project", "original_branch": "main"},
}


def com_dir(base: dict, diretorio: str, **mudancas) -> dict:
    d = json.loads(json.dumps(base))
    d["cwd"] = diretorio
    d["workspace"]["current_dir"] = diretorio
    for chave, valor in mudancas.items():
        alvo = d
        partes = chave.split("__")
        for p in partes[:-1]:
            alvo = alvo.setdefault(p, {})
        if valor is None:
            alvo.pop(partes[-1], None)
        else:
            alvo[partes[-1]] = valor
    return d


def roda(script: str, entrada: dict, path: str | None = None, prefixo: list[str] | None = None):
    env = dict(os.environ)
    if path is not None:
        env["PATH"] = path
    p = subprocess.run([*(prefixo or []), BASH, script], input=json.dumps(entrada), capture_output=True,
                       text=True, env=env, timeout=30)
    return p.returncode, p.stdout, p.stderr


def mede_ms(script: str, entrada: dict, n: int) -> tuple[list[float], list[float]]:
    """(jq sozinho, script) em ms, INTERCALADOS, cronometrados por um bash com
    $EPOCHREALTIME: o que o Claude Code paga por atualizacao, sem o spawn do Python
    (medido em 2026-09-23: p50 63,9 ms cronometrando em volta do subprocess.run contra
    31-33 ms do script; o jq 1.6 sozinho custa ~26-28 ms e ate 57 ms com o gopls a 439%
    de CPU). Intercalar poe os dois sob a MESMA carga: a diferenca e' o custo do script."""
    jq = shutil.which("jq")
    programa = ('for ((i=0; i<%d; i++)); do s=$EPOCHREALTIME; %s -r . <<<"$2" >/dev/null; '
                'm=$EPOCHREALTIME; %s "$1" <<<"$2" >/dev/null 2>&1; e=$EPOCHREALTIME; '
                'echo "$(( ${m/./} - ${s/./} )) $(( ${e/./} - ${m/./} ))"; done') % (n, jq, BASH)
    p = subprocess.run([BASH, "-c", programa, "_", script, json.dumps(entrada)],
                       capture_output=True, text=True, timeout=300)
    pares = [linha.split() for linha in p.stdout.splitlines() if linha.strip()]
    return [int(a) / 1000 for a, _ in pares], [int(b) / 1000 for _, b in pares]


def monta_repos(tmp: str) -> dict:
    """Tres repos de mentira: ramo normal, HEAD destacado, worktree com .git arquivo."""
    normal = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(normal, ".git"))
    os.makedirs(os.path.join(normal, "sub", "fundo"))
    with open(os.path.join(normal, ".git", "HEAD"), "w") as fh:
        fh.write("ref: refs/heads/ramo-de-teste\n")
    destacado = os.path.join(tmp, "destacado")
    os.makedirs(os.path.join(destacado, ".git"))
    with open(os.path.join(destacado, ".git", "HEAD"), "w") as fh:
        fh.write("0123456789abcdef0123456789abcdef01234567\n")
    arvore = os.path.join(tmp, "arvore")
    gitdir = os.path.join(normal, ".git", "worktrees", "arvore")
    os.makedirs(gitdir)
    os.makedirs(arvore)
    with open(os.path.join(gitdir, "HEAD"), "w") as fh:
        fh.write("ref: refs/heads/ramo-da-arvore\n")
    with open(os.path.join(arvore, ".git"), "w") as fh:
        fh.write(f"gitdir: {gitdir}\n")
    fora = os.path.join(tmp, "fora", "de", "repo")
    os.makedirs(fora)
    return {"normal": normal, "sub": os.path.join(normal, "sub", "fundo"), "destacado": destacado,
            "arvore": arvore, "fora": fora}


def monta_path_contador(tmp: str) -> tuple[str, str]:
    """PATH com SO dois comandos: `git` (conta e falha) e `jq` (conta e executa o real)."""
    binario = os.path.join(tmp, "bin")
    os.makedirs(binario)
    contador = os.path.join(tmp, "contador")
    jq_real = shutil.which("jq")
    assert jq_real, "jq ausente no PATH real"
    with open(os.path.join(binario, "git"), "w") as fh:
        fh.write(f"#!{BASH}\necho git >> {contador}\nexit 1\n")
    with open(os.path.join(binario, "jq"), "w") as fh:
        fh.write(f"#!{BASH}\necho jq >> {contador}\nexec {jq_real} \"$@\"\n")
    for nome in ("git", "jq"):
        os.chmod(os.path.join(binario, nome), 0o755)
    return binario, contador


def suite(script: str, verboso: bool, medir_tempo: bool) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="statusline-") as tmp:
        return _suite(script, verboso, medir_tempo, tmp)


def _suite(script: str, verboso: bool, medir_tempo: bool, tmp: str) -> list[str]:
    falhas: list[str] = []

    def caso(nome: str, ok: bool, detalhe: str = ""):
        if verboso:
            print(f"  {'ok ' if ok else 'ERRO'} {nome} {detalhe}")
        if not ok:
            falhas.append(nome)

    repos = monta_repos(tmp)

    # 1. esquema completo da doc
    rc, out, err = roda(script, com_dir(ESQUEMA_DOC, repos["normal"]))
    esperado = f"[Opus] repo (ramo-de-teste) | {VERDE}ctx 8%{RESET} | US$ 0.01 | cache 91% | 5h 24%\n"
    caso("esquema da doc: linha completa", rc == 0 and out == esperado and err == "", repr(out))

    # 2. minima e sem rate_limits/prompt_cache
    rc, out, err = roda(script, {"model": {"display_name": "Opus"}, "workspace": {"current_dir": repos["fora"]}})
    caso("fixtura minima: sem erro e ctx --", rc == 0 and out == "[Opus] repo | ctx --\n" and err == "", repr(out))
    rc, out, err = roda(script, com_dir(ESQUEMA_DOC, repos["normal"], rate_limits=None, prompt_cache=None))
    caso("sem rate_limits/prompt_cache: segmentos omitidos",
         rc == 0 and "cache" not in out and "5h" not in out and "US$ 0.01" in out and err == "", repr(out))
    rc, out, _ = roda(script, com_dir(ESQUEMA_DOC, repos["normal"], context_window__used_percentage=None))
    caso("used_percentage null: ctx --", rc == 0 and "| ctx -- |" in out, repr(out))

    # 3. cores nas fronteiras
    for pct, cor, rotulo in ((69, VERDE, "verde"), (70, AMARELO, "amarelo"), (89, AMARELO, "amarelo"),
                             (90, VERMELHO, "vermelho")):
        rc, out, _ = roda(script, com_dir(ESQUEMA_DOC, repos["normal"], context_window__used_percentage=pct))
        caso(f"ctx {pct}% {rotulo}", rc == 0 and f"{cor}ctx {pct}%{RESET}" in out, repr(out))
    rc, out, _ = roda(script, com_dir(ESQUEMA_DOC, repos["normal"], context_window__used_percentage=72.9))
    caso("ctx fracionario trunca (72.9 -> 72)", f"{AMARELO}ctx 72%{RESET}" in out, repr(out))

    # 4. ramo
    for nome, chave, ramo in (("subdiretorio sobe ate .git", "sub", "(ramo-de-teste)"),
                              ("HEAD destacado mostra sha de 7", "destacado", "(0123456)"),
                              ("worktree com .git arquivo", "arvore", "(ramo-da-arvore)")):
        rc, out, _ = roda(script, com_dir(ESQUEMA_DOC, repos[chave]))
        caso(nome, rc == 0 and ramo in out, repr(out))
    rc, out, _ = roda(script, com_dir(ESQUEMA_DOC, repos["fora"]))
    caso("fora de repo: sem parenteses", rc == 0 and "(" not in out.split("|")[0], repr(out))

    # 5. custo de processo
    binario, contador = monta_path_contador(tmp)
    rc, out, err = roda(script, com_dir(ESQUEMA_DOC, repos["sub"]), path=binario)
    try:
        chamadas = open(contador).read().split()
    except FileNotFoundError:
        chamadas = []
    caso("PATH so com git/jq contadores: 0 git, 1 jq, sem erro",
         rc == 0 and chamadas.count("git") == 0 and chamadas.count("jq") == 1 and err == "" and "(ramo-de-teste)" in out,
         f"chamadas={chamadas} err={err.strip()[:80]!r}")
    strace = shutil.which("strace")
    if strace:
        log = os.path.join(tmp, "strace.log")
        rc, out, err = roda(script, com_dir(ESQUEMA_DOC, repos["sub"]),
                            prefixo=[strace, "-f", "-qq", "-e", "trace=execve", "-e", "signal=none", "-o", log])
        execs = [ln for ln in open(log) if "execve(" in ln and "= 0" in ln]
        alvos = [ln.split('"')[1] for ln in execs if '"' in ln]
        caso("strace: exatamente 2 execve (bash e jq)",
             len(execs) == 2 and alvos[0].endswith("bash") and alvos[1].endswith("jq"), str(alvos))
    elif verboso:
        print("  --  strace ausente: contagem por execve pulada (a do PATH restrito vale)")

    # 6. latencia: o script custa o jq e pouco mais (SEMPRE asserido); p50 absoluto so' com
    #    a maquina ociosa (loadavg1 < 1,0), senao impresso sem veredito
    if medir_tempo:
        jq_ms, tempos = mede_ms(script, com_dir(ESQUEMA_DOC, repos["sub"]), 20)
        p50, p50_jq = statistics.median(tempos), statistics.median(jq_ms)
        carga = carga_1min()
        detalhe = (f"p50={p50:.1f} ms (jq sozinho {p50_jq:.1f} ms) max={max(tempos):.1f} ms "
                   f"loadavg1={carga} n={len(tempos)}")
        caso(f"script custa o jq + < {MARGEM_SOBRE_JQ_MS} ms", len(tempos) == 20 and p50 - p50_jq < MARGEM_SOBRE_JQ_MS,
             detalhe)
        if carga is not None and carga < CARGA_OCIOSA:
            caso("p50 de 20 execucoes < 50 ms (maquina ociosa)", p50 < 50, detalhe)
        elif verboso:
            print(f"  --  p50 absoluto informativo (loadavg1 >= {CARGA_OCIOSA:g}): {detalhe}")
    return falhas


MUTANTES = [
    ("S1 sem cor", "\t\tcor=$'\\e[31m'\n", "\t\tcor=''\n"),
    ("S2 campo trocado", ".context_window.used_percentage", ".context_window.remaining_percentage"),
    ("S3 faixa vermelha em 95", "((ctx >= 90))", "((ctx >= 95))"),
    ("S4 faixa amarela estrita", "((ctx >= 70))", "((ctx > 70))"),
    ("S5 chama git", "ramo=\"\"\nif [[ -n $cabeca", "ramo=$(git branch --show-current 2>/dev/null)\nif [[ -n $cabeca"),
    ("S6 fork a mais", "nome=${dir##*/}", "nome=$(basename \"$dir\")"),
    ("S7 cache sem x100", "(.prompt_cache.hit_ratio | if . == null then \"\" else (. * 100 | round) end)",
     "(.prompt_cache.hit_ratio | if . == null then \"\" else round end)"),
    ("S8 nao sobe diretorio", "\td=${d%/*}\n", "\tbreak\n"),
    ("S9 ignora .git arquivo", "\tif [[ -f $d/.git ]]; then", "\tif false; then"),
    ("S10 custo sem dois digitos", "'US$ %d.%02d'", "'US$ %d.%d'"),
    ("S11 janela de 7 dias", ".rate_limits.five_hour.used_percentage", ".rate_limits.seven_day.used_percentage"),
    # regressao do defeito que este teste achou em 2026-09-23: tab no IFS funde campo vazio
    ("S13 custo escondido (laco de ~0,2 s, sem fork)", "\nLC_ALL=C\n",
     "\nLC_ALL=C\nfor ((k = 0; k < 300000; k++)); do :; done\n"),
    ("S12 volta ao @tsv com IFS tab",
     "] | map(tostring | gsub(\"[\\n\\u001f]\"; \" \")) | join(\"\\u001f\")' 2>/dev/null)\n"
     "IFS=$'\\x1f' read -r modelo dir ctx cents cache cinco <<<\"$vals\"",
     "] | map(tostring) | @tsv' 2>/dev/null)\n"
     "IFS=$'\\t' read -r modelo dir ctx cents cache cinco <<<\"$vals\""),
]


def main() -> int:
    if not os.access(SCRIPT, os.X_OK):
        print(f"FALHOU: {SCRIPT} ausente ou sem bit de execucao")
        return 1
    print("suite contra o script real:")
    falhas = suite(SCRIPT, verboso=True, medir_tempo=True)
    if falhas:
        print(f"FALHOU: {len(falhas)} caso(s): {falhas}")
        return 1
    fonte = open(SCRIPT, encoding="utf-8").read()
    vivos = []
    print("prova por mutacao:")
    with tempfile.TemporaryDirectory(prefix="statusline-mut-") as tmp:
        for nome, antigo, novo in MUTANTES:
            if fonte.count(antigo) != 1:
                print(f"  ERRO {nome}: trecho alvo aparece {fonte.count(antigo)} vez(es) — mutante nao aplicado")
                vivos.append(nome)
                continue
            caminho = os.path.join(tmp, "mutante.sh")
            with open(caminho, "w", encoding="utf-8") as fh:
                fh.write(fonte.replace(antigo, novo))
            mortos_por = suite(caminho, verboso=False, medir_tempo=nome.startswith("S13"))
            print(f"  {'ok ' if mortos_por else 'VIVO'} {nome}: {len(mortos_por)} caso(s) reprovaram"
                  + (f" (ex. {mortos_por[0]})" if mortos_por else ""))
            if not mortos_por:
                vivos.append(nome)
    if vivos:
        print(f"FALHOU: mutante(s) vivo(s): {vivos}")
        return 1
    print(f"OK: suite verde e {len(MUTANTES)} mutantes mortos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
