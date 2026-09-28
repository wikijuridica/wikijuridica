#!/usr/bin/env python3
"""Bancada de block-git-add-com-commit.sh — `git add` e `git commit` EXECUTADOS no mesmo
payload de Bash.

    python3 .claude/hooks/block-git-add-com-commit.test.py

Roda o hook REAL por subprocess, com o payload JSON como o harness o entrega, nas quatro
formas do serializador (compacto ou espaçado, UTF-8 cru ou `\\uXXXX`): veredito que muda
com a forma já é falha.

Os casos que LIBERAM pesam igual aos que barram. Três são reais, de 2026-09-23, e estão
aqui literais: o `python3 - <<'EOF'` que só gravava num documento a rota
"`git add <caminho>` → `git commit -F <msg>`" entre crases de markdown; o `grep` que
procurava a mensagem deste hook; e a escrita do próprio hook por `cat > ...sh <<'EOF'`.

PROVA POR MUTAÇÃO (classe ProvaPorMutacao, roda junto): cada mutante é uma cópia do hook,
numa CÓPIA da árvore de hooks em diretório temporário (o hook acha `lib/` e o auxiliar ao
lado de si), e a bancada exige que o teste que cobre a correção fique VERMELHO contra ele —
e que a cópia intacta, pelo mesmo caminho, fique verde. m3 é o hook de antes do conserto
(substring crua), guardado aqui LITERAL: `git show HEAD:` deixaria de apontar para ele no
primeiro commit.

HOOK_GIT_ALVO aponta a bancada para outra cópia do hook; é por onde a mutação roda.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

AQUI = Path(__file__).resolve().parent
HOOK = Path(os.environ.get("HOOK_GIT_ALVO", str(AQUI / "block-git-add-com-commit.sh")))
RAIZ = AQUI.parent.parent

# Montados por concatenação, como em block-git-add-por-diretorio-test.sh: este arquivo é
# lido e escrito por agentes cujo payload passa pelo hook que ele testa.
ADD = "git " + "add"
COMMIT = "git " + "commit"

FORMAS = [((",", ":"), False), ((",", ":"), True), (None, False), (None, True)]


def roda(comando: str, separadores=None, ascii_: bool = False,
         descricao: str = "bancada do hook") -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando, "description": descricao}},
                         separators=separadores, ensure_ascii=ascii_)
    return subprocess.run(["bash", str(HOOK)], input=payload.encode(), capture_output=True, cwd=str(RAIZ))


def veredito(comando: str, descricao: str = "bancada do hook") -> int:
    """Exit do hook; se ele muda com a forma do JSON, falha aqui mesmo."""
    vistos = {forma: roda(comando, forma[0], forma[1], descricao).returncode for forma in FORMAS}
    if len(set(vistos.values())) != 1:
        raise AssertionError(f"veredito depende da forma do JSON {vistos}: {comando!r}")
    return next(iter(vistos.values()))


# Payload real, ide-docs, 2026-09-23 (extraído do transcrito; só `git add`/`git commit`
# trocados por marcador e remontados).
FP2_REAL = (
    "python3 - <<'EOF'\n"
    "p = 'docs/goal/ESTADO_PROMPT_OPERACIONAL_20260922.md'\n"
    "t = open(p, encoding='utf-8').read()\n"
    'old = ("| 8 | Commit A (docs/config/hooks/agentes/workflows/tools, 34 arquivos) e commit B (o teste Go) | bloqueado-com-rota | "\n'
    '       "mensagem pronta em `.agents/runtime/20260923-prompt-operacional/commit-A.msg`; causa física medida: a VM da ponte não pode `unlink` no repositório (todo `git status` deixa `.git/index.lock` que só se move) e não compila a árvore dentro do teto de 90 s do gate | "\n'
    '       "primeira ação da próxima sessão Claude Code no host: `§ADD§ <cada caminho da lista em RELATORIO_PACOTE.md §10>` (um a um, nunca diretório) → `§COMMIT§ -F .agents/runtime/20260923-prompt-operacional/commit-A.msg` → depois `§ADD§ internal/contract/misc/alocacao_de_modelos_test.go` → `§COMMIT§ -F <msg>` (o pre-commit roda o pacote misc) |")\n'
    'assert t.count(old) == 1, t.count(old)\n'
    'new = ("| 8 | Commit A (docs/config/hooks/agentes/workflows/tools, 34 arquivos) e commit B (o teste Go) | feito | "\n'
    '       "2026-09-23, no host: commit A = `5779c105` (42 arquivos, 08:11:08 -03) · commit B = `6c96b80b` (`internal/contract/misc/alocacao_de_modelos_test.go`, 949 linhas, 08:11:42 -03) — conferidos por `git show --stat --format=\'%h %ci %s\' <hash>` às 08:15. "\n'
    '       "*Até 2026-09-23 08:11 este item era `bloqueado-com-rota`, com esta evidência: mensagem pronta em `.agents/runtime/20260923-prompt-operacional/commit-A.msg`; causa física medida: a VM da ponte não pode `unlink` no repositório (todo `git status` deixa `.git/index.lock` que só se move) e não compila a árvore dentro do teto de 90 s do gate.* | "\n'
    '       "— *(superado em 2026-09-23: a rota que ficava aqui foi a executada no host — primeira ação da próxima sessão Claude Code no host: `§ADD§ <cada caminho da lista em RELATORIO_PACOTE.md §10>` (um a um, nunca diretório) → `§COMMIT§ -F .agents/runtime/20260923-prompt-operacional/commit-A.msg` → depois `§ADD§ internal/contract/misc/alocacao_de_modelos_test.go` → `§COMMIT§ -F <msg>` (o pre-commit roda o pacote misc))* |")\n'
    't = t.replace(old, new)\n'
    "open(p, 'w', encoding='utf-8').write(t)\n"
    "print('ok')\n"
    'EOF\n'
    "sed -n '14p' docs/goal/ESTADO_PROMPT_OPERACIONAL_20260922.md | cut -c1-400; git diff --stat -- docs/goal/ESTADO_PROMPT_OPERACIONAL_20260922.md"
).replace("§ADD§", ADD).replace("§COMMIT§", COMMIT)

# O hook como estava no HEAD antes do conserto (commit 9977c8ed), byte a byte.
HOOK_ANTIGO = (
    '#!/usr/bin/env bash\n'
    '# block-git-add-com-commit.sh — PreToolUse:Bash (projeto /opt/wiki)\n'
    '#\n'
    '# BARRA: `§ADD§` e `§COMMIT§` no MESMO payload de Bash.\n'
    '# O pre-commit deste repositorio compila o INDICE. Com os dois no mesmo comando\n'
    '# o indice ainda esta sendo escrito quando a compilacao comeca, e o hook reprova\n'
    '# com "indice mudou durante compilacao" — reprovacao que nao diz o que fazer.\n'
    '#\n'
    '# NAO barra: `§ADD§` sozinho; `§COMMIT§ -F` sozinho; `§COMMIT§` precedido\n'
    '# apenas de leitura (`git status`, `git diff`).\n'
    'set -uo pipefail\n'
    "trap 'exit 0' ERR\n"
    '. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0\n'
    '\n'
    'INPUT="$(le_payload)"\n'
    '[ -z "$INPUT" ] && exit 0\n'
    '[[ "$INPUT" != *"§ADD§"* ]] && exit 0\n'
    '[[ "$INPUT" != *"§COMMIT§"* ]] && exit 0\n'
    '\n'
    'bloqueia \\\n'
    '\t"§ADD§ e §COMMIT§ no mesmo comando: o pre-commit deste repo compila o INDICE e reprova com \'indice mudou durante compilacao\'." \\\n'
    '\t"Separe em DUAS chamadas Bash:\n'
    '  1)  §ADD§ caminho/exato/do/arquivo\n'
    '  2)  §COMMIT§ -F /caminho/da/mensagem.txt\n'
    'A mensagem vai por -F sempre, nunca por -m com heredoc, e a saida do hook nunca\n'
    'e capturada no MESMO arquivo passado a -F (isso sobrescreve a mensagem).\n'
    'Commit que toca Go/go.mod/go.sum serializa com flock /tmp/opt-wiki-commit.lock."\n'
    'exit 0\n'
).replace("§ADD§", ADD).replace("§COMMIT§", COMMIT)


class Barra(unittest.TestCase):
    """Os dois EXECUTADOS no mesmo payload."""

    CASOS = [
        f"{ADD} x.go && {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go; {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go\n{COMMIT} -F /tmp/m.txt",                       # duas linhas: `\n` no JSON
        f"cd /opt/wiki\n\t{ADD} x.go\n\t{COMMIT} -F /tmp/m.txt",     # indentado com TAB
        "git -C /opt/wiki add x.go && git -c user.name=x commit -F /tmp/m.txt",
        f"command {ADD} x.go && sudo -u rafael {COMMIT} -F /tmp/m.txt",
        f"/usr/bin/{ADD} x.go && env GIT_EDITOR=true {COMMIT} -F /tmp/m.txt",
        "git --no-pager add x.go && git --git-dir=.git commit -F /tmp/m.txt",
        f"x=$({ADD} x.go) && {COMMIT} -F /tmp/m.txt",
        f"r=`{ADD}`; {COMMIT} -F /tmp/m.txt",                        # crase fecha o comando
        f"if true; then {ADD} x.go; {COMMIT} -F /tmp/m.txt; fi",
        f"git ls-files -m | xargs {ADD} && {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go || true; nice -n 19 timeout 60 {COMMIT} -F /tmp/m.txt",
        f"GIT_AUTHOR_NAME=x {COMMIT} -F /tmp/m.txt && {ADD} y.go",
        f"bash <<'EOF'\n{ADD} x.go\n{COMMIT} -F /tmp/m.txt\nEOF",     # heredoc que alimenta SHELL
        f"cat > /tmp/m.txt <<'EOF'\nmensagem\nEOF\n{ADD} x.go && {COMMIT} -F /tmp/m.txt",
        # A string de `bash -c`/`sh -c`/`eval` é comando. Sem a âncora SHELL_C, estes
        # saíam 0 no hook novo e 2 no antigo (medido em 2026-09-23; mutante m3g).
        f"bash -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"sh -c \"{ADD} x.go; {COMMIT} -F /tmp/m.txt\"",
        f"bash -lc '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"/bin/bash -e -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"eval \"{ADD} x.go && {COMMIT} -F /tmp/m.txt\"",
        f"cd /tmp\nbash -c '{ADD} x.go; {COMMIT} -F /tmp/m.txt'",
        f"find . -name x.go -exec sh -c '{ADD} \"$1\" && {COMMIT} -F /tmp/m.txt' _ {{}} \\;",
        f"sudo sh -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        # O comando de `ssh host '...'` e de `su -c '...'`: o hook antigo barrava por
        # substring, e sem a âncora REMOTO o novo deixava passar (mutante m3h).
        f"ssh localhost '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"ssh -p 22 -i ~/.ssh/k rafael@host \"{ADD} x.go; {COMMIT} -F /tmp/m.txt\"",
        f"ssh -t host '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"su -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt' rafael",
        f"su - rafael -c \"{ADD} x.go; {COMMIT} -F /tmp/m.txt\"",
        # A forma DOCUMENTADA do commit deste repo (docs/OPERACAO_COMANDOS_E_CAMINHOS.md) e a
        # família de wrappers com opção e posicional antes do comando. Com a do flock, o hook
        # novo saía 0 e o antigo 2 (refutação de 2026-09-23; mutante m3i).
        f"{ADD} x && flock /tmp/opt-wiki-agent-heavy.lock {COMMIT} -F m",
        f"{ADD} internal/v2ingest/validator_fingerprint_attestation_generated.go\n"
        f"flock /tmp/opt-wiki-agent-heavy.lock {COMMIT} -F /tmp/msg.txt",
        f"{ADD} x.go && flock -w 60 /tmp/opt-wiki-commit.lock {COMMIT} -F /tmp/m.txt",
        f"flock /tmp/l -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt'",
        f"{ADD} x.go && setsid {COMMIT} -F /tmp/m.txt",
        f"stdbuf -oL {ADD} x.go && {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go && ionice -c 3 -n 7 {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go && systemd-run --scope --user -p MemoryMax=1G {COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go && timeout -k 5 60 {COMMIT} -F /tmp/m.txt",
        f"script -q -c '{ADD} x.go && {COMMIT} -F /tmp/m.txt' /dev/null",
        # Heredoc que vai para shell pela cauda da linha (defeito 7 do auxiliar; m3j).
        f"cat <<'EOF' | bash\n{ADD} x.go && {COMMIT} -F /tmp/m.txt\nEOF",
        f"cat <<'EOF' > /tmp/c.sh && bash /tmp/c.sh\n{ADD} x.go\n{COMMIT} -F /tmp/m.txt\nEOF",
    ]

    def test_barra_os_dois_executados(self):
        for comando in self.CASOS:
            with self.subTest(comando=comando):
                self.assertEqual(veredito(comando), 2)

    def test_mensagem_ensina_o_caminho_certo(self):
        """O que o tools/check-modo-operacional cobra do ensino, pelas duas rotas."""
        r = roda(f"{ADD} x.go && {COMMIT} -F /tmp/m.txt")
        saida = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(saida["permissionDecision"], "deny")
        for trecho in (f"{ADD} caminho/exato", f"{COMMIT} -F"):
            self.assertIn(trecho, saida["additionalContext"])
            self.assertIn(trecho, r.stderr.decode())


class Libera(unittest.TestCase):
    """O que o hook NÃO pode barrar."""

    CASOS = [
        f"{ADD} internal/render/page.go",
        f"{COMMIT} -F /tmp/m.txt",
        f"git status && {COMMIT} -F /tmp/m.txt",
        f"git diff --stat && {ADD} x.go",
        f"{COMMIT} -F /tmp/m.txt -- .claude/hooks/block-git-add-com-commit.sh",
        f"echo \"rode {ADD} x e depois {COMMIT} -F m\" >> notas.md",
        f"git log --grep='{ADD}' && {COMMIT} -F /tmp/m.txt",
        f"cat > /tmp/m.txt <<'EOF'\nfix: separa {ADD} de {COMMIT}\nEOF\n{COMMIT} -F /tmp/m.txt",
        f"{ADD} x.go && git commit-tree HEAD^{{tree}}",
        f"grep -c '{ADD}' notas.md; {COMMIT} -F /tmp/m.txt",          # `-c` de grep não é shell
        f"bash -c 'echo {ADD} feito'; {COMMIT} -F /tmp/m.txt",
        f"python3 -c \"print('{ADD}')\"; {COMMIT} -F /tmp/m.txt",
        f"./gera.sh -c '{ADD}' && {COMMIT} -F /tmp/m.txt",
        f"ssh-add ~/.ssh/k; {COMMIT} -F /tmp/m.txt",                  # `ssh-add` não é ssh
        f"ssh host echo '{ADD} x'; {COMMIT} -F /tmp/m.txt",
        f"ssh-keygen -c -f k; {ADD} x.go",
        f"rsync -e ssh a b; {COMMIT} -F /tmp/m.txt",
        f"echo 'veja su -c' e {ADD} depois; {COMMIT} -F /tmp/m.txt",
        f"flock /tmp/opt-wiki-agent-heavy.lock {COMMIT} -F /tmp/m.txt",   # a forma certa, sozinha
        f"{ADD} x.go && flock /tmp/l echo {COMMIT}",
        f"flock /tmp/l -c 'echo {ADD}'; {COMMIT} -F /tmp/m.txt",
        f"cat <<'EOF' | python3 -\nprint('{ADD} x && {COMMIT} -F m')\nEOF",  # corpo de python: texto
    ]

    # LIMITE CONHECIDO, declarado em vez de maquiado (o mesmo de block-heavy-go.test.py):
    # python/node que executa git por `os.system("git add x && git commit -F m")` ou por
    # `subprocess` não é visto — o corpo de python sai pelo `--so-shell`, e dentro dele não
    # há posição de comando de shell. Medido em 2026-09-23 com o heredoc
    # `python3 - <<'EOF'\nimport os\nos.system("<add> x && <commit> -F m")\nEOF`:
    # hook antigo exit 2 (por acaso de substring), hook novo exit 0; a forma de LISTA do
    # subprocess passava nos dois (exit 0). Não há caso aqui que trave esse comportamento:
    # quem fechar a lacuna acrescenta o caso em Barra.

    def test_libera(self):
        for comando in self.CASOS:
            with self.subTest(comando=comando):
                self.assertEqual(veredito(comando), 0)

    def test_heredoc_de_python_que_so_cita_caso_real(self):
        """FALSO POSITIVO MEDIDO (2026-09-23). Corpo de python com os dois entre crases de
        markdown: sem `--so-shell` o corpo fica, e a crase vira posição de comando."""
        self.assertEqual(veredito(FP2_REAL), 0)

    def test_grep_pela_mensagem_do_hook_caso_real(self):
        """FALSO POSITIVO MEDIDO (2026-09-23): a busca pela própria mensagem deste hook."""
        comando = ("cd /home/rafael/.claude/projects/-opt-wiki/ 2>/dev/null && ls -t | head -5; "
                   "find /home/rafael/.claude/projects/-opt-wiki/ -name '*.jsonl' -newermt '2026-09-23 00:00' "
                   f"-size -200M 2>/dev/null | head -50 | xargs -r grep -l '{ADD} e {COMMIT} no mesmo comando' "
                   "2>/dev/null | head -10")
        self.assertEqual(veredito(comando), 0)

    def test_escrever_o_hook_por_heredoc_caso_real(self):
        """FALSO POSITIVO MEDIDO (2026-09-23): escrever ESTE hook por `cat > ...sh <<'X'`."""
        # O cabeçalho real cita os dois entre crases — e crase é posição de comando: se o
        # corpo não sair da análise (o `.sh` do nome tomado por interpretador), barra.
        comando = (
            "cat > /tmp/x/block-git-add-com-commit.sh <<'FIMDOARQUIVO'\n#!/usr/bin/env bash\n"
            f"# BARRA: `{ADD}` e `{COMMIT}` no MESMO payload de Bash.\n"
            f"[[ \"$INPUT\" != *\"{ADD}\"* ]] && exit 0\n"
            f"  1)  {ADD} caminho/exato/do/arquivo\n  2)  {COMMIT} -F /caminho/da/mensagem.txt\n"
            "FIMDOARQUIVO\nbash -n /tmp/x/block-git-add-com-commit.sh")
        self.assertEqual(veredito(comando), 0)

    def test_heredoc_de_python_com_bloco_de_codigo(self):
        """No começo da linha, mas dentro de string do python: não é comando de shell."""
        comando = (f"python3 - <<'EOF'\ndoc = '''\n```bash\n{ADD} caminho\n{COMMIT} -F msg\n```\n'''\n"
                   "open('d.md', 'w').write(doc)\nEOF")
        self.assertEqual(veredito(comando), 0)

    def test_descricao_fica_fora_da_analise(self):
        self.assertEqual(veredito(f"{ADD} x.go", descricao=f"x; {ADD} y; {COMMIT} -F m"), 0)
        self.assertEqual(veredito(f"{ADD} x.go && {COMMIT} -F m", descricao="só lê"), 2)


# (nome, o que desfaz, fonte do mutante a partir da fonte viva, testes que TÊM de reprovar)
def _troca(trecho: str, novo: str):
    def aplica(fonte: str) -> str:
        if fonte.count(trecho) != 1:
            raise AssertionError(f"o trecho mudou de forma — atualize o mutante: {trecho!r}")
        return fonte.replace(trecho, novo)
    return aplica


def _mesma(fonte: str) -> str:
    return fonte


# (nome, o que desfaz, hook do mutante — texto pronto ou troca sobre a fonte viva —, troca no
# auxiliar, testes que TÊM de reprovar)
MUTANTES = [
    # Medido contra ele em 2026-09-23 (com o auxiliar novo ao lado): barra TODA a prosa
    # que só cita — os dois casos reais abaixo, aspas, `git log --grep`, `grep -c`,
    # `bash -c 'echo ...'`, `python3 -c print`, `commit-tree`, bloco de código em python,
    # a descrição — e deixa PASSAR `git -C dir add` + `git -c k=v commit` e
    # `git --no-pager add` + `git --git-dir=.git commit` (falso negativo: a substring
    # "git add" não aparece). A escrita do hook por
    # `cat > ...sh` passa contra ele: esse caso é do auxiliar, e tem o mutante m3f.
    ("m3", "hook de antes do conserto: substring crua sobre o payload",
     HOOK_ANTIGO, _mesma,
     ["Libera.test_heredoc_de_python_que_so_cita_caso_real",
      "Libera.test_grep_pela_mensagem_do_hook_caso_real"]),
    ("m3b", "sem --so-shell: o corpo de python fica e a crase vira posição de comando",
     _troca(' --so-shell 2>/dev/null)', ' 2>/dev/null)'), _mesma,
     ["Libera.test_heredoc_de_python_que_so_cita_caso_real"]),
    ("m3c", "âncora sem a quebra de linha do JSON",
     _troca("|\\\\n|'\"$NL\"'|", "|'\"$NL\"'|"), _mesma,
     ["Barra.test_barra_os_dois_executados"]),
    ("m3g", "sem a âncora da string de `bash -c`/`sh -c`/`eval`",
     _troca("'|'\"$SHELL_C\"'|", "'|"), _mesma,
     ["Barra.test_barra_os_dois_executados"]),
    ("m3h", "sem a âncora do comando de `ssh host '...'`/`su -c '...'`",
     _troca("'|'\"$REMOTO\"')'", "')'"), _mesma,
     ["Barra.test_barra_os_dois_executados"]),
    ("m3d", "sem prefixos transparentes (sudo, command, env, xargs...)",
     _troca('re_commit="$ANCORA$ESP*($PREFIXO$ESP+)*$GIT', 're_commit="$ANCORA$ESP*$GIT'), _mesma,
     ["Barra.test_barra_os_dois_executados"]),
    ("m3e", "sem o recorte do valor de \"command\": a descrição entra na análise",
     _troca("re_valor='\"command\":", "re_valor='NUNCA\"command\":"), _mesma,
     ["Libera.test_descricao_fica_fora_da_analise"]),
    ("m3f", "auxiliar com a regex antiga do shell, sem fronteira à esquerda (o `.sh` do nome)",
     _mesma,
     _troca("SHELL = _dono(_SHELLS)",
            r'SHELL = re.compile(r"(?:bash|sh|zsh|ksh|python3?|perl|ruby|node)\b[^\n;&|]{0,40}<<\s*$")'),
     ["Libera.test_escrever_o_hook_por_heredoc_caso_real"]),
    ("m3i", "sem o `flock` nos prefixos transparentes",
     _troca("(flock|taskset|script)", "(taskset|script)"), _mesma,
     ["Barra.test_barra_os_dois_executados"]),
    ("m3j", "auxiliar sem a leitura da cauda da linha (`cat <<'EOF' | bash`)",
     _mesma,
     _troca("if _cauda_executa_o_corpo(antes, t.trecho(achado.end(), corpo), so_shell):", "if False:"),
     ["Barra.test_barra_os_dois_executados"]),
]


@unittest.skipIf(os.environ.get("HOOK_GIT_ALVO"),
                 "rodada contra outra cópia: a prova por mutação não se repete dentro dela")
class ProvaPorMutacao(unittest.TestCase):

    AUXILIAR = HOOK.parent / "strip-heredoc-body.py"

    def _roda_contra(self, fonte: str, auxiliar: str, testes: list[str]) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="hook-git-mut-") as tmp:
            arvore = Path(tmp) / "hooks"
            shutil.copytree(HOOK.parent, arvore, ignore=shutil.ignore_patterns("__pycache__"))
            (arvore / "strip-heredoc-body.py").write_text(auxiliar, encoding="utf-8")
            alvo = arvore / "block-git-add-com-commit.sh"
            alvo.write_text(fonte, encoding="utf-8")
            env = dict(os.environ, HOOK_GIT_ALVO=str(alvo))
            return subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), *testes],
                                  capture_output=True, text=True, env=env)

    def test_controle_a_copia_intacta_passa_pelo_mesmo_caminho(self):
        testes = sorted({t for mutante in MUTANTES for t in mutante[-1]})
        r = self._roda_contra(HOOK.read_text(encoding="utf-8"),
                              self.AUXILIAR.read_text(encoding="utf-8"), testes)
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])

    def test_cada_mutante_e_morto_pelo_teste_que_cobre_a_correcao(self):
        fonte = HOOK.read_text(encoding="utf-8")
        auxiliar = self.AUXILIAR.read_text(encoding="utf-8")
        for nome, descricao, monta_hook, monta_auxiliar, testes in MUTANTES:
            with self.subTest(mutante=nome):
                # m3 traz o hook pronto (texto); os demais, a troca aplicada sobre a fonte viva.
                hook_mutante = monta_hook if isinstance(monta_hook, str) else monta_hook(fonte)
                r = self._roda_contra(hook_mutante, monta_auxiliar(auxiliar), testes)
                # Morto = CADA teste listado reprovou por asserção (FAIL, não ERROR).
                morto = r.returncode != 0 and all(
                    f"FAIL: {t.split('.')[-1]} (__main__.{t})" in r.stderr for t in testes)
                print(f"\n  mutante {nome} ({descricao}): {'MORTO' if morto else 'VIVO'}"
                      f" por {', '.join(testes)}", file=sys.stderr)
                self.assertTrue(morto, f"{nome} sobreviveu:\n{r.stderr[-3000:]}")


if __name__ == "__main__":
    if not HOOK.is_file():
        print(f"hook ausente: {HOOK}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
