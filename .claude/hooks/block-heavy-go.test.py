import json, os, subprocess, sys

# O hook mora ao lado deste teste. Antes (ate 2026-09-23) o caminho era fixo em /opt/wiki e, fora do
# host (VM da ponte, arvore de validacao), o bash nao achava o hook e 13 dos 25 casos reprovavam como
# "passa" — a bancada media o ambiente, nao o hook.
HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-heavy-go.sh")
LC = "lab" + "-cycle"
CA = "check" + "-all"
FT = "./" + "..."
RC = "run-" + "check"
GM = "./tools/go-" + "modern"

# Os tokens pesados são montados por concatenação de propósito: este arquivo é lido e
# escrito por agentes cujo payload passa pelo próprio hook, e um literal aqui bloquearia
# a edição do teste — o mesmo falso positivo que o caso "doc em heredoc" cobre.

# (nome, comando, esperado)  esperado: True = deve BLOQUEAR
casos = [
    # --- devem PASSAR: prosa/mencao, nao invocacao ---
    ("commit citando invocacao",   f'git commit -m "roda ./tools/{LC} depois"',                 False),
    ("commit citando full-tree",   f'git commit -m "nao rode {GM} build {FT}"',                 False),
    ("doc mencionando suite",      f'echo "veja tools/{LC} no runbook" >> notas.md',             False),
    ("arquivo homonimo",           f'cat docs/{LC}-notes.md',                                   False),
    ("grep pelo nome",             f'grep -rn "{LC}" docs/',                                    False),
    ("teste focado legitimo",      f'{GM} test -count=1 ./internal/seo/',                       False),
    ("go list full-tree",          f'{GM} list {FT}',                                           False),
    ("comando leve",               'ls -la /tmp',                                               False),
    ("envelopado",                 f'./tools/run-heavy-throttled {GM} build {FT}',              False),
    # --- heredoc quoted e DADO, nao execucao (fix 2026-08-19) ---
    # Caso real: escrever documentacao que CITA o comando pesado entre crases. A crase e
    # posicao de comando em shell, mas em markdown e codigo inline — sem este caso, o
    # hook impedia de documentar a propria regra que ele aplica.
    ("doc em heredoc citando full-tree",
     f"cat > skill.md <<'FIM'\nRegra: nao rode `{GM} build {FT}` aqui.\nFIM",                   False),
    ("doc em heredoc citando suite",
     f"cat > runbook.md <<'FIM'\nA suite `./tools/{LC}` so em mudanca critica.\nFIM",            False),
    ("heredoc com aspas duplas no delimitador",
     f'cat > nota.md <<"FIM"\ncitando {GM} test -count=1 {FT}\nFIM',                            False),
    # --- evasao: heredoc que ALIMENTA interpretador E execucao, continua barrado ---
    ("heredoc alimentando bash",
     f"bash <<'FIM'\n{GM} build {FT}\nFIM",                                                     True),
    # LIMITE CONHECIDO, declarado em vez de maquiado: comando pesado embrulhado numa
    # string de outra linguagem (os.system('...')) nao esta em posicao de comando de
    # SHELL, que e o que este hook analisa. O strip corretamente NAO remove o corpo (o
    # heredoc alimenta interpretador), mas a deteccao nao alcanca la dentro. Fechar isso
    # exigiria interpretar Python/Perl/Ruby — fora do escopo de um guarda de recurso.
    # O caso que importa na pratica (heredoc alimentando bash) esta coberto acima.
    # --- comando pesado FORA do heredoc, com heredoc no mesmo payload ---
    ("pesado fora, doc dentro",
     f"cat > nota.md <<'FIM'\ntexto inofensivo\nFIM\n{GM} build {FT}",                          True),
    # --- devem BLOQUEAR: invocacao real ---
    ("invocacao suite",            f'./tools/{LC}',                                             True),
    ("invocacao check-all",        f'./tools/{CA}',                                             True),
    ("full-tree real",             f'{GM} build {FT}',                                          True),
    ("full-tree test",             f'{GM} test -count=1 {FT}',                                  True),
    ("com nice",                   f'nice -n 19 ./tools/{LC}',                                  True),
    ("encadeado apos &&",          f'cd /opt/wiki && ./tools/{LC}',                             True),
    ("encadeado apos ;",           f'echo oi; ./tools/{CA}',                                    True),
    ("run-check all",              f'./tools/{RC} all',                                         True),
    ("cmd/check all",              f'{GM} run ./cmd/check all',                                 True),
    ("go list + build encadeado",  f'{GM} list {FT} && {GM} build {FT}',                        True),
    ("auditoria global",           'python3 tools/audit_v2_pages.py --global',                  True),
]

falhas = 0
for nome, cmd, esperado in casos:
    p = subprocess.run(
        ["bash", HOOK],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd, "description": nome}}),
        capture_output=True, text=True,
    )
    bloqueou = p.returncode == 2
    ok = bloqueou == esperado
    if not ok:
        falhas += 1
    marca = "ok  " if ok else "FALHA"
    acao = "BLOQUEIA" if bloqueou else "passa   "
    print(f"  [{marca}] {acao}  {nome}")

print()
print(f"  {len(casos)-falhas}/{len(casos)} corretos" + ("" if falhas == 0 else f"  <<< {falhas} FALHA(S)"))
sys.exit(1 if falhas else 0)
