#!/usr/bin/env python3
"""Bancada de block-write-fora-de-contexto.sh (e do juiz lib/guarda_de_escrita.py).

Ordem do dono, 2026-09-22: Sonnet 5 colhe contexto, "sem editar". A guarda só vale enquanto for
CRÍVEL nos dois sentidos, então a bancada pesa igual:

  - o que ela TEM de barrar: escrita fora de .agents/runtime/contexto/ por Write/Edit e pelos
    caminhos do Bash que uma guarda só-de-Write deixaria abertos (redirecionamento, sed -i,
    git commit, python que abre em modo de escrita, heredoc sem aspas com $(...));
  - o que ela NÃO pode barrar: a leitura e a medição que são o trabalho do colhedor, e —
    principalmente — qualquer chamada da sessão principal e dos agentes de execução, porque no
    settings.json este hook roda em TODA chamada Bash do repositório.

Rodar:  python3 .claude/hooks/block-write-fora-de-contexto.test.py
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block-write-fora-de-contexto.sh"
JUIZ = Path(__file__).resolve().parent / "lib" / "guarda_de_escrita.py"


class Bancada(unittest.TestCase):
    """Raiz de repositório descartável: o hook nunca é exercitado contra o /opt/wiki real."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="guarda-escrita-")
        cls.raiz = Path(cls._tmp.name) / "wiki"
        (cls.raiz / ".agents" / "runtime" / "contexto").mkdir(parents=True)
        (cls.raiz / "internal" / "seo").mkdir(parents=True)
        (cls.raiz / "tools").mkdir()
        (cls.raiz / "CLAUDE.md").write_text("contrato\n", encoding="utf-8")
        (cls.raiz / "tools" / "check-exemplo").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        # Symlink DENTRO do diretório permitido apontando para FORA: realpath tem de pegar.
        os.symlink(cls.raiz / "CLAUDE.md", cls.raiz / ".agents" / "runtime" / "contexto" / "atalho.md")
        cls.home = Path(cls._tmp.name) / "home"
        cls.home.mkdir()
        cls.scratch = Path(cls._tmp.name) / "scratchpad"
        cls.scratch.mkdir()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def roda(self, ferramenta: str, entrada: dict, agente: str | None = "documentador-de-contexto",
             sempre: bool = True, bruto: str | None = None, path: str = "/usr/bin:/bin",
             cwd: Path | None = None) -> subprocess.CompletedProcess:
        payload: dict = {
            "session_id": "bancada",
            "cwd": str(cwd or self.raiz),
            "hook_event_name": "PreToolUse",
            "tool_name": ferramenta,
            "tool_input": entrada,
            "scratchpad_dir": str(self.scratch),
        }
        if agente is not None:
            payload["agent_type"] = agente
            payload["agent_id"] = "a0000000000000001"
        argumentos = ["bash", str(HOOK)] + (["--sempre"] if sempre else [])
        return subprocess.run(
            argumentos,
            input=bruto if bruto is not None else json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(self.raiz),
            env={"PATH": path, "HOME": str(self.home), "CLAUDE_PROJECT_DIR": str(self.raiz)},
            timeout=20,
        )

    def barra(self, ferramenta: str, entrada: dict, **kw) -> subprocess.CompletedProcess:
        p = self.roda(ferramenta, entrada, **kw)
        self.assertEqual(p.returncode, 2, f"deveria barrar e passou: {entrada}\nstderr={p.stderr}")
        return p

    def passa(self, ferramenta: str, entrada: dict, **kw) -> subprocess.CompletedProcess:
        p = self.roda(ferramenta, entrada, **kw)
        self.assertEqual(p.returncode, 0, f"deveria passar e barrou: {entrada}\nstderr={p.stderr}")
        return p

    def bash_barra(self, comando: str, **kw) -> subprocess.CompletedProcess:
        return self.barra("Bash", {"command": comando}, **kw)

    def bash_passa(self, comando: str, **kw) -> subprocess.CompletedProcess:
        return self.passa("Bash", {"command": comando}, **kw)


class TesteFerramentasDeArquivo(Bancada):
    def test_write_no_contrato_barra(self):
        self.barra("Write", {"file_path": str(self.raiz / "CLAUDE.md"), "content": "x"})

    def test_write_em_codigo_go_barra(self):
        self.barra("Write", {"file_path": str(self.raiz / "internal/seo/meta.go"), "content": "package seo"})

    def test_edit_em_dado_editorial_barra(self):
        self.barra("Edit", {"file_path": str(self.raiz / "data/editorial/v2_pages/a.jsonl"),
                            "old_string": "a", "new_string": "b"})

    def test_multiedit_e_notebookedit_barram(self):
        self.barra("MultiEdit", {"file_path": str(self.raiz / "docs/x.md"), "edits": []})
        self.barra("NotebookEdit", {"notebook_path": str(self.raiz / "n.ipynb"), "new_source": "x"})

    def test_travessia_por_ponto_ponto_barra(self):
        """O harness entrega caminho absoluto, mas `..` continua possível dentro dele."""
        self.barra("Write", {"file_path": str(self.raiz / ".agents/runtime/contexto/../../../CLAUDE.md"),
                             "content": "x"})

    def test_symlink_dentro_de_contexto_apontando_para_fora_barra(self):
        self.barra("Write", {"file_path": str(self.raiz / ".agents/runtime/contexto/atalho.md"), "content": "x"})

    def test_prefixo_parecido_nao_e_o_diretorio(self):
        """`contexto-falso/` começa com o mesmo texto de `contexto/`, e não é ele."""
        self.barra("Write", {"file_path": str(self.raiz / ".agents/runtime/contexto-falso/x.md"), "content": "x"})

    def test_write_sem_caminho_barra(self):
        self.barra("Write", {"content": "x"})

    def test_write_do_mapa_passa(self):
        self.passa("Write", {"file_path": str(self.raiz / ".agents/runtime/contexto/2026-09-22-roster-modelos.md"),
                             "content": "# mapa\n"})

    def test_subdiretorio_de_contexto_passa(self):
        self.passa("Write", {"file_path": str(self.raiz / ".agents/runtime/contexto/frente-x/achados.jsonl"),
                             "content": "{}\n"})

    def test_memoria_do_proprio_agente_passa(self):
        self.passa("Write", {"file_path": str(self.raiz / ".claude/agent-memory/documentador-de-contexto/MEMORY.md"),
                             "content": "- padrão\n"})

    def test_memoria_de_outro_agente_barra(self):
        self.barra("Write", {"file_path": str(self.raiz / ".claude/agent-memory/engenheiro-go/MEMORY.md"),
                             "content": "x"})

    def test_scratchpad_da_sessao_passa(self):
        self.passa("Write", {"file_path": str(self.scratch / "rascunho.txt"), "content": "x"})


class TesteBashBarra(Bancada):
    def test_redirecionamento_para_o_contrato(self):
        self.bash_barra("echo x > CLAUDE.md")

    def test_acrescimo_em_documento(self):
        self.bash_barra(f"echo linha >> {self.raiz}/docs/goal/ESTADO.md")

    def test_redirecionamento_com_descritor(self):
        self.bash_barra("ls 2> erros.log")

    def test_destino_em_variavel(self):
        self.bash_barra('echo x > "$HOME/y"')

    def test_variavel_dentro_do_prefixo_pode_sair_dele(self):
        """O texto parece estar em contexto/, mas o valor só existe na execução — e pode ser `../`.
        Um juiz que resolvesse o texto literal aprovaria; este mutante já sobreviveu uma vez."""
        self.bash_barra("ARQ=../../../CLAUDE.md; echo x > .agents/runtime/contexto/$ARQ")
        self.bash_barra("echo x > .agents/runtime/contexto/$(printf ../../../CLAUDE.md)")

    def test_segundo_comando_da_linha(self):
        self.bash_barra("echo ok; mv a.md b.md")

    def test_sed_in_place(self):
        self.bash_barra("sed -i 's/haiku/sonnet/' .claude/agents/investigador.md")

    def test_sed_in_place_em_aglomerado(self):
        self.bash_barra("sed -ni 's/a/b/p' CLAUDE.md")

    def test_sed_com_comando_w(self):
        self.bash_barra("sed -n '/x/w saida.txt' CLAUDE.md")

    def test_copiar_mover_apagar(self):
        for comando in ("cp CLAUDE.md /tmp/c.md", "rm -f CLAUDE.md", "ln -s CLAUDE.md x", "chmod +x tools/x"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_git_que_escreve(self):
        for comando in ("git add CLAUDE.md", "git commit -F /tmp/msg", "git checkout -- CLAUDE.md",
                        "git stash", "git branch novo", "git -c core.pager=cat log", "git diff --output=x.diff"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_tee_fora_de_contexto(self):
        self.bash_barra("git log -1 | tee docs/x.md")

    def test_python_abrindo_para_escrita(self):
        self.bash_barra("python3 -c \"open('CLAUDE.md', 'w').write('x')\"")

    def test_python_abrindo_caminho_composto_para_escrita(self):
        """`open(os.path.join(a, b), 'w')` — o parêntese interno não pode esconder o modo."""
        self.bash_barra("python3 -c \"import os; open(os.path.join('a', 'b'), 'w')\"")

    def test_python_em_heredoc_que_grava(self):
        self.bash_barra("python3 - <<'PY'\nfrom pathlib import Path\nPath('CLAUDE.md').write_text('x')\nPY")

    def test_python_com_subprocess(self):
        self.bash_barra("python3 -c \"import subprocess; subprocess.run(['rm','-rf','data'])\"")

    def test_escrita_escondida_por_apelido_ou_importacao_direta(self):
        """Quatro desvios MEDIDOS em 2026-09-22, antes do conserto: todos saíam com exit 0."""
        for comando in (
            "python3 -c \"import os as o; o.remove('CLAUDE.md')\"",
            "python3 -c \"from os import remove; remove('CLAUDE.md')\"",
            "python3 -c \"import os; getattr(os, 'remove')('CLAUDE.md')\"",
            "node -e \"require('fs').writeFileSync('CLAUDE.md','x')\"",
            "node -e \"const {appendFileSync} = require('fs'); appendFileSync('CLAUDE.md','x')\"",
            "python3 -c \"from tempfile import mkstemp; mkstemp()\"",
            "python3 -c \"from os import *; remove('CLAUDE.md')\"",
            "ruby -e \"IO.write('CLAUDE.md', 'x')\"",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_redirecionamento_leitura_e_escrita_e_exec(self):
        self.bash_barra("cat CLAUDE.md 1<>CLAUDE.md")
        self.bash_barra("exec 3>CLAUDE.md")

    def test_python_lendo_stdin_de_pipe(self):
        self.bash_barra("cat script.py | python3")

    def test_python_rodando_script_do_repositorio(self):
        self.bash_barra("python3 tools/generate_algo.py")

    def test_heredoc_sem_aspas_executa_substituicao(self):
        self.bash_barra("cat <<EOF > .agents/runtime/contexto/x.md\n$(rm -rf data)\nEOF")

    def test_find_que_apaga_ou_executa_escrita(self):
        self.bash_barra("find . -name '*.tmp' -delete")
        self.bash_barra("find . -name '*.bak' -exec rm {} \\;")

    def test_xargs_com_comando_de_escrita(self):
        self.bash_barra("cat lista.txt | xargs rm")

    def test_bash_c_com_escrita(self):
        self.bash_barra("bash -c 'echo x > CLAUDE.md'")

    def test_eval_com_escrita(self):
        self.bash_barra("eval 'echo x > CLAUDE.md'")

    def test_substituicao_de_comando_com_escrita(self):
        self.bash_barra("echo $(touch CLAUDE.md)")

    def test_curl_grava_ou_envia(self):
        for comando in ("curl -o pagina.html https://example.org", "curl -sSLO https://example.org/x.tar",
                        "curl -X POST http://127.0.0.1:8089/api", "curl -d '{}' http://127.0.0.1:11434/api/generate"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_gerador_e_build(self):
        for comando in ("./tools/generate-v2-publication-severity", "./tools/go-modern test -count=1 ./internal/seo/",
                        "./tools/run-heavy-throttled ./tools/go-modern build ./cmd/server", "go generate ./internal/x/"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_awk_que_grava(self):
        self.bash_barra("awk '{print > \"saida.txt\"}' dados.txt")

    def test_sqlite_de_escrita(self):
        self.bash_barra('sqlite3 data/ai/cerebro.sqlite "DELETE FROM itens"')

    def test_systemctl_que_altera_servico(self):
        self.bash_barra("sudo -n systemctl restart wikijuridica-server")

    def test_cd_para_dentro_do_repo_e_escreve_relativo(self):
        # cd muda onde um caminho relativo cai; escrever num arquivo do repo continua barrado
        # (/tmp virou rascunho na onda 5, mas o repositório, não).
        self.bash_barra("cd internal && echo x > seo/vazou.go")

    def test_comando_fora_da_lista(self):
        self.bash_barra("make build")

    def test_comando_ilegivel_barra(self):
        self.bash_barra("echo 'aspas sem fim")

    def test_payload_ilegivel_no_frontmatter_barra(self):
        """Dentro do documentador (frontmatter), não conseguir ler é barrar."""
        p = self.roda("Bash", {}, bruto="{isto não é json")
        self.assertEqual(p.returncode, 2)


class TesteBashPassa(Bancada):
    """A leitura e a medição que são o trabalho do colhedor."""

    def test_leituras_de_git(self):
        for comando in ("git log --oneline -20 -- internal/checks/", "git show HEAD:CLAUDE.md | head -40",
                        "git diff --stat HEAD~3 -- .claude/", "git blame -L 170,190 CLAUDE.md",
                        "git -C /opt/wiki status --short", "git branch --show-current", "git config --get user.name"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_busca_e_contagem(self):
        for comando in ('grep -rn "model:" .claude/agents/ | wc -l', "rg -n 'haiku' -g '*.md' .",
                        "wc -m docs/goal/PROMPT_OPERACIONAL_4K.txt", "sha256sum CLAUDE.md AGENTS.md",
                        "ls -la .claude/hooks 2>/dev/null || true", "stat -c '%y %n' CLAUDE.md",
                        "find internal -name '*_test.go' | xargs grep -l RepoRoot | head",
                        "find . -name '*.md' -newer CLAUDE.md -print",
                        "jq '.[] | select(.path==\"/bot/\")' content/pages.json"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_gravar_o_mapa_pelo_bash(self):
        for comando in ("mkdir -p .agents/runtime/contexto",
                        "echo '# mapa' > .agents/runtime/contexto/2026-09-22-x.md",
                        "sha256sum CLAUDE.md | tee -a .agents/runtime/contexto/hashes.txt",
                        "cd .agents/runtime/contexto && echo ok > nota.md",
                        "cat > .agents/runtime/contexto/2026-09-22-y.md <<'EOF'\ntexto com > e < e | e $(nada) dentro\nEOF"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_python_que_so_le(self):
        self.bash_passa("python3 -c \"import json; print(len(json.load(open('content/pages.json', encoding='utf-8'))))\"")
        self.bash_passa("python3 - <<'PY'\nimport json\nd = json.load(open('x.json'))\nprint(d['a'] > 3, 'a|b'.split('|'))\nPY")
        # controle dos padrões de apelido: importação só de leitura e apelido de outro módulo passam
        self.bash_passa("python3 -c \"import os.path; from os import listdir, walk; import json as j; print(listdir('.'), j.dumps(os.path.getsize('CLAUDE.md')))\"")
        self.bash_passa("node -e \"const fs = require('fs'); process.stdout.write(fs.readFileSync('CLAUDE.md', 'utf8').slice(0, 80))\"")

    def test_ferramenta_check_do_repositorio(self):
        self.bash_passa("./tools/check-load-headroom --max 12")
        self.bash_passa("python3 tools/check-exemplo --json")

    def test_awk_sed_leitura(self):
        self.bash_passa("awk -F: '$3 > 100 {print $1}' /etc/passwd")
        self.bash_passa("sed -n '1,40p' CLAUDE.md")

    def test_estruturas_de_shell(self):
        for comando in ("for f in .claude/agents/*.md; do grep -H '^model:' \"$f\"; done",
                        "while read -r l; do echo \"$l\"; done < lista.txt",
                        "if [ -f CLAUDE.md ]; then head -5 CLAUDE.md; fi",
                        "[[ -f CLAUDE.md ]] && echo sim",
                        "case x in a) echo um;; *) echo outro;; esac",
                        "(( 3 > 2 )) && echo maior",
                        "echo \"a > b\" | wc -c",
                        "diff <(git show HEAD:CLAUDE.md) CLAUDE.md",
                        "cmd_inexistente_em_comentario=1 # rm -rf tudo"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_medicao_de_host(self):
        for comando in ("uptime; free -h; nproc", "ps aux | grep ollama | grep -v grep",
                        "systemctl status wikijuridica-server --no-pager",
                        "journalctl -u ollama --since '1 hour ago' --no-pager | tail -30",
                        "curl -s http://127.0.0.1:11434/api/tags | jq '.models[].name'",
                        "curl -sS -o /dev/null -w '%{http_code}' https://code.claude.com/docs/en/hooks.md",
                        "sqlite3 -readonly data/ai/cerebro.sqlite 'select count(*) from itens'",
                        "timeout 10 nice -n 19 ./tools/check-load-headroom"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)


class TesteSoAgentesRestritos(Bancada):
    """No settings.json o hook roda em toda chamada: fora dos agentes restritos, nunca barra."""

    def test_sessao_principal_escreve_livre(self):
        self.passa("Write", {"file_path": str(self.raiz / "CLAUDE.md"), "content": "x"}, agente=None, sempre=False)
        self.passa("Bash", {"command": "echo x > CLAUDE.md && git add CLAUDE.md"}, agente=None, sempre=False)

    def test_agente_de_execucao_escreve_livre(self):
        self.passa("Write", {"file_path": str(self.raiz / "internal/seo/meta.go"), "content": "package seo"},
                   agente="engenheiro-go", sempre=False)

    def test_investigador_e_restrito_pelo_settings(self):
        self.barra("Write", {"file_path": str(self.raiz / "CLAUDE.md"), "content": "x"},
                   agente="investigador", sempre=False)
        self.barra("Bash", {"command": "git commit -m x"}, agente="investigador", sempre=False)

    def test_documentador_e_restrito_tambem_pelo_settings(self):
        """Cobre a sessão -p, onde o hook do frontmatter não roda."""
        self.barra("Write", {"file_path": str(self.raiz / "CLAUDE.md"), "content": "x"},
                   agente="documentador-de-contexto", sempre=False)

    def test_nome_do_agente_no_texto_do_comando_nao_engana(self):
        """A sessão principal pode falar do investigador sem virar investigador — e escreve num
        arquivo do repositório à vontade (destino de repo, não /tmp, para o mutante "julga todo
        agente" morrer: se o juiz passasse a julgar a sessão principal, esta escrita barraria)."""
        self.passa("Bash", {"command": "grep -n 'investigador' WORKFLOWS.md > resumo-investigador.md"},
                   agente=None, sempre=False)

    def test_json_ilegivel_na_sessao_principal_passa(self):
        p = self.roda("Bash", {}, agente=None, sempre=False, bruto="{nao e json")
        self.assertEqual(p.returncode, 0)

    def test_caminho_rapido_nao_cria_processo(self):
        """Mutação do caminho rápido: com um python3 falso que deixa rastro no PATH, a chamada da
        sessão principal não pode invocá-lo. Se o filtro por nome for apagado, o rastro aparece."""
        falso = Path(self._tmp.name) / "bin-falso"
        falso.mkdir(exist_ok=True)
        rastro = Path(self._tmp.name) / "python-foi-chamado"
        script = falso / "python3"
        script.write_text(f"#!/bin/sh\ntouch '{rastro}'\nexit 1\n", encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        self.roda("Bash", {"command": "ls -la"}, agente=None, sempre=False, path=f"{falso}:/usr/bin:/bin")
        self.assertFalse(rastro.exists(), "a chamada da sessão principal criou processo python3")


class TesteContratoDaMensagem(Bancada):
    def test_bloqueio_sai_em_json_valido_com_deny_e_cita_a_ordem(self):
        p = self.bash_barra("echo x > CLAUDE.md")
        saida = json.loads(p.stdout)
        especifico = saida["hookSpecificOutput"]
        self.assertEqual(especifico["permissionDecision"], "deny")
        self.assertIn("2026-09-22", especifico["permissionDecisionReason"])
        self.assertIn(".agents/runtime/contexto/", especifico["additionalContext"])
        self.assertIn("Opus 5.5", especifico["additionalContext"])
        self.assertIn("2026-09-22", p.stderr)

    def test_python_ausente_barra_agente_restrito(self):
        """Sem o juiz, o agente restrito é barrado pelo agent_type lido em bash puro."""
        vazio = Path(self._tmp.name) / "bin-vazio"
        vazio.mkdir(exist_ok=True)
        for ferramenta in ("cat", "bash"):
            destino = vazio / ferramenta
            if not destino.exists():
                destino.symlink_to(Path("/bin") / ferramenta if (Path("/bin") / ferramenta).exists() else Path("/usr/bin") / ferramenta)
        p = self.roda("Bash", {"command": "ls"}, agente="investigador", sempre=False, path=str(vazio))
        self.assertEqual(p.returncode, 2)


class TesteHarnessRedTeam(Bancada):
    """Cada falso positivo e falso negativo do red team de 2026-09-22 (redteam/ataque_guarda.py)
    vira um caso fixo aqui, para não voltar. O que o harness esperava e a medição refutou fica com
    o veredito medido, não com o do harness — Regra 16: instrumento que se engana troca-se, e a
    grandeza mede-se na fonte (o próprio sistema de arquivos)."""

    # --- escritas escondidas que passavam (falsos negativos), agora barradas ---
    def test_python_open_com_modo_calculado(self):
        for comando in (
            "python3 -c \"m='w'; open('CLAUDE.md', m).write('x')\"",
            "python3 -c \"open('CLAUDE.md', chr(119)).write('x')\"",
            "python3 -c \"k={'mode':'w'}; open('CLAUDE.md', **k)\"",
            "python3 -c \"import io; io.open('CLAUDE.md','w')\"",
            "python3 -c \"import logging; logging.FileHandler('x.log')\"",
            "python3 -c \"import zipfile; zipfile.ZipFile('x.zip','w')\"",
            "python3 -c \"import tarfile; tarfile.open('x.tar','w')\"",
            "python3 -c \"import shelve; shelve.open('x')['a']=1\"",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_perl_e_ruby_escrita_por_modulo(self):
        for comando in (
            "perl -MFile::Copy -e 'copy(\"a\",\"b\")'",
            "perl -MFile::Path -e 'make_path(\"d/e\")'",
            "ruby -e 'Kernel.open(\"|rm x\", \"r\")'",
            "ruby -e 'm=\"w\"; File.open(\"CLAUDE.md\", m)'",
            "ruby -e 'require \"pathname\"; Pathname.new(\"x\").write(\"y\")'",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_git_branch_upstream_altera(self):
        self.bash_barra("git branch --set-upstream-to=origin/main")

    def test_sqlite_funcoes_e_pragmas_de_escrita(self):
        for comando in (
            "sqlite3 x.db 'pragma wal_checkpoint'",
            "sqlite3 x.db 'pragma optimize'",
            "sqlite3 x.db \"select writefile('o','dados')\"",
            "sqlite3 x.db \"select load_extension('e')\"",
            "sqlite3 x.db 'analyze'",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_env_split_string_monta_comando(self):
        for comando in ("env --split-string='rm x'", "env -S='rm x'", "env -S 'rm x'"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_awk_opcoes_que_gravam(self):
        for comando in (
            "awk --source='{print > \"x\"}' f",
            "awk -o '{print}' f",
            "awk -p '{print}' f",
            "awk --dump-variables '{print}' f",
            "awk -d '{print}' f",
            "awk -l filefuncs 'BEGIN{unlink(\"x\")}'",
            "awk '@load \"filefuncs\"; BEGIN{unlink(\"x\")}'",
            "awk -e 'BEGIN{}' -e '{print > \"x\"}' f",
            "awk '{printf(\"%s\\n\", $1) > \"x\"}' f",
            "awk '{print($1) > \"x\"}' f",
            "awk 'BEGIN{c=\"date\"; c | getline d}'",
            "awk '{print ($1, $2) > \"x\"}' f",
            "awk '{print $1 |& \"cat\"}' f",
            "awk --sandbox '{print > \"x\"}' f",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_sed_enderecos_gnu_que_gravam(self):
        for comando in (
            "sed -n '1~2w y' f",
            "sed -n '/a/,+2w y' f",
            "sed -n '/a/,~2w y' f",
            "sed -n 's/[/]/x/w y' f",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_pipeline_de_saida_para_arquivo(self):
        for comando in (
            "awk '{print}' f | uniq - y",
            "awk '{print}' f | iconv -f utf8 -t ascii -ox",
            "sort --compress-program=rm f",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    # --- MEDIDO: sort -o - cria arquivo chamado '-' (GNU coreutils 9.4); é escrita, barra ---
    def test_sort_o_traco_e_arquivo_medido(self):
        self.bash_barra("sort -o - f")

    # --- leituras que barravam (falsos positivos), agora liberadas ---
    def test_git_lista_de_ramos_e_etiquetas_le(self):
        for comando in (
            "git tag --list", "git tag -n1", "git tag --contains HEAD",
            "git branch --list", "git branch --contains HEAD", "git branch --points-at HEAD",
        ):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_binario_por_caminho_absoluto_do_sistema(self):
        self.bash_passa("/bin/cat CLAUDE.md")

    def test_flock_com_timeout_le(self):
        self.bash_passa("flock -w 600 /tmp/opt-wiki-agent-heavy.lock -c 'git log -1'")

    def test_awk_comparacao_e_redirecao_para_dispositivo(self):
        for comando in (
            "awk '{print $1 >= $2}' f",
            "awk '{print > \"/dev/stderr\"}' f",
            "awk '{print > \".agents/runtime/contexto/x\"}' f",
            "awk '{print \"# > x\"}' f",
            "awk '{print /a|b/}' f",
            "awk '{print $1 ~ /a|b/}' f",
            "awk '{print $1 || $2}' f",
            "awk '{print $1 ||\"cat\"}' f",
        ):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    # --- MEDIDO: uniq f - e iconv -o - escrevem na saída padrão; passam ---
    def test_uniq_e_iconv_traco_sao_stdout_medido(self):
        self.bash_passa("uniq f -")
        self.bash_passa("iconv -f utf8 -t ascii -o - f")

    def test_uniq_com_opcao_de_campo_le(self):
        for comando in ("uniq -f 1 f", "uniq -s 1 f", "uniq -w 1 f", "uniq --skip-fields=1 f"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)


class TesteOnda5(Bancada):
    """Os seis MÉDIOS do RT-B2 de 2026-09-23, cada um com o comando que reproduz."""

    # M1 — código de interpretador montado na execução é opaco: barra. Literal só de leitura passa.
    def test_m1_codigo_dinamico_de_interpretador_barra(self):
        for comando in (
            "P='open(\"CLAUDE.md\",\"w\")'; python3 -c \"$P\"",
            "python3 -c \"$(cat evil.py)\"",
            "node -e \"$(cat evil.js)\"",
            "perl -e \"$P\"",
            "ruby -e \"$P\"",
            "python3 -c \"$CODIGO\"",
            "python3 - <<EOF\n$CODIGO\nEOF",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_m1_codigo_literal_de_leitura_passa(self):
        for comando in (
            "python3 -c 'print(1)'",
            "python3 -c \"print(1)\"",
            "node -e 'console.log(1)'",
            "python3 - <<'PY'\nimport json\nprint(json.load(open('x')))\nPY",
        ):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    # M2 — git branch/tag: nome posicional só passa após --list/-l/filtros; modificador não libera.
    def test_m2_git_ref_com_nome_posicional_barra(self):
        for comando in (
            "git branch -v b3", "git branch -vv b4", "git branch --verbose b5",
            "git branch --sort=-committerdate b1", "git branch --format='%(refname)' b2",
            "git branch -av b6", "git tag --sort=-creatordate v1", "git tag --format='%(refname)' v2",
            "git branch novo", "git tag v1", "git branch --set-upstream-to=origin/main x",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_m2_git_ref_listando_passa(self):
        for comando in (
            "git branch -v", "git branch --sort=x", "git tag --sort=x", "git branch -l x",
            "git branch -v --list x", "git branch --merged HEAD", "git tag --points-at HEAD",
        ):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    # M3 — date (sem -s) e hostname (sem argumento) são leitura; a prova 12 do S1 usa date +%F.
    def test_m3_date_e_hostname_de_leitura_passam(self):
        for comando in ("date +%F", "date -u +%Y-%m-%dT%H:%M:%SZ", "hostname",
                        "grep -ci haiku .agents/runtime/contexto/modelos-$(date +%F).jsonl"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_m3_date_set_e_hostname_com_argumento_barram(self):
        for comando in ("date -s '2020-01-01'", "hostname novonome", "hostname -F /etc/hostname"):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    # M4 — /tmp e ${TMPDIR} (rascunho fora do repositório) são graváveis; dentro do repo, não.
    def test_m4_escrita_em_tmp_fora_do_repo_passa(self):
        # Bash escrevendo em /tmp (rascunho fora do repo) passa. O analisador de interpretador julga
        # open() por MODO, não por destino, então `python3 -c open('/tmp/x','w')` segue barrado — é
        # limite declarado, não M4.
        for comando in ("sort -u a > /tmp/sitemap_paths.txt", "echo x > /tmp/wj-rascunho.txt",
                        "tee /tmp/log.txt < f", "mkdir -p /tmp/wj-work"):
            with self.subTest(comando=comando):
                self.bash_passa(comando)

    def test_m4_tmp_apontando_para_o_repo_barra(self):
        # symlink de /tmp para dentro do repo resolve para o caminho versionado e continua barrado.
        alvo = self.raiz / "CLAUDE.md"
        self.bash_barra(f"echo x > /tmp/../{str(alvo).lstrip('/')}")

    # M6 — sqlite3: comentário SQL sai antes; dot-command que executa/grava barra (por prefixo).
    def test_m6_sqlite_dot_e_comentario_barram(self):
        for comando in (
            "sqlite3 x.db '.shell rm x'", "sqlite3 x.db '.sh rm x'", "sqlite3 x.db '.out y'",
            "sqlite3 x.db '.import a b'", "sqlite3 x.db '.save o'", "sqlite3 x.db '.read evil.sql'",
            "sqlite3 x.db '.backup b'", "sqlite3 x.db 'INSERT/**/INTO t VALUES(1)'",
            "sqlite3 x.db 'insert--c\ninto t values(1)'", "sqlite3 x.db 'create/**/table t(a)'",
        ):
            with self.subTest(comando=comando):
                self.bash_barra(comando)

    def test_m6_sqlite_select_puro_passa(self):
        for comando in (
            "sqlite3 x.db 'select count(*) from t'", "sqlite3 -readonly x.db 'select 1'",
            "sqlite3 x.db '.tables'", "sqlite3 x.db '.schema t'", "sqlite3 x.db 'select 1 -- c'",
        ):
            with self.subTest(comando=comando):
                self.bash_passa(comando)


class TesteSshELeiturasDeSistema(Bancada):
    """2026-09-24: seis colhedores de uma onda de auditoria da migração devolveram mapas cegos do lado
    da torre, porque `ssh` inteiro era barrado. O comando REMOTO passa pela mesma lista de leitura,
    num contexto em que nenhum destino de escrita vale; túnel, sessão sem comando e comando local
    disparado pelo ssh continuam barrados."""

    TORRE = "ssh -o BatchMode=yes -o UserKnownHostsFile=/home/rafael/.ssh/known_hosts-torre rafael@192.168.1.10"

    def test_ssh_com_comando_remoto_de_leitura_passa(self):
        for remoto in ("'systemctl list-unit-files --no-legend | head; df -h'",
                       "'sudo -n cat /etc/fstab'",
                       '"find /etc -maxdepth 1 -type f | wc -l"',
                       "'ls -la ~/.config/systemd/user/; crontab -l'",
                       "'for p in 20243 20251; do curl -s 127.0.0.1:$p/ready; done'"):
            self.bash_passa(f"{self.TORRE} {remoto}")

    def test_ssh_com_escrita_remota_barra(self):
        for remoto in ("'rm -rf /opt/wiki'", "'echo x > /etc/passwd'",
                       "'sudo systemctl restart wikijuridica-nginx'", "'git -C /opt/wiki commit -m x'",
                       "'sed -i s/a/b/ /opt/wiki/CLAUDE.md'",
                       # mesmo o caminho que o colhedor escreve LOCALMENTE é escrita na outra máquina
                       f"'echo x > {self.raiz}/.agents/runtime/contexto/a.md'",
                       "'cat /etc/hostname | tee /tmp/x'"):
            self.bash_barra(f"{self.TORRE} {remoto}")

    def test_ssh_tunel_sessao_e_comando_local_barram(self):
        for comando in ("ssh rafael@192.168.1.10",
                        "ssh -L 8080:localhost:80 rafael@192.168.1.10 'cat /etc/hostname'",
                        "ssh -NT rafael@192.168.1.10",
                        "ssh -o ProxyCommand='nc %h %p' rafael@192.168.1.10 'ls'",
                        "ssh -oLocalCommand=touch\\ x -oPermitLocalCommand=yes rafael@192.168.1.10 'ls'",
                        f"ssh -E {self.raiz}/CLAUDE.md rafael@192.168.1.10 'ls'",
                        "ssh -S /tmp/ctl rafael@192.168.1.10 'ls'",
                        "ssh $DESTINO 'ls'"):
            self.bash_barra(comando)

    def test_leituras_de_sistema_passam(self):
        for comando in ("findmnt -rn -o TARGET,SOURCE", "dpkg-query -W -f='${Package}\\n'", "dpkg -l | grep nginx",
                        "dpkg --verify", "dpkg -S /usr/bin/ls", "apt-mark showmanual", "apt-cache policy nginx",
                        "crontab -l", "crontab -l -u rafael", "virsh -c qemu:///system list --all",
                        "virsh net-list --all", "docker ps -a", "docker volume ls", "docker compose ps",
                        "snap list", "flatpak list", "npm ls -g --depth=0", "pipx list --short", "lxc-ls -f",
                        "ip -br addr", "ip route show", "ss -ltnp", "loginctl show-user rafael"):
            self.bash_passa(comando)

    def test_escritas_de_sistema_barram(self):
        for comando in ("dpkg -i x.deb", "dpkg --purge nginx", "apt-mark hold nginx", "crontab -r",
                        "crontab arquivo", "virsh start escritorio-win11", "virsh net-destroy default",
                        "docker rm x", "docker run alpine", "docker volume rm x", "snap install x",
                        "npm install -g x", "npm config set a b", "pipx install x",
                        "ip link set enp10s0 down", "ss -K dst 1.2.3.4", "loginctl terminate-user rafael",
                        "apt install x"):
            self.bash_barra(comando)

    def test_sessao_principal_nao_e_afetada(self):
        # sem --sempre e sem agente restrito, a sessão principal segue livre para o ssh que escreve
        self.passa("Bash", {"command": f"{self.TORRE} 'sudo -n systemctl restart wikijuridica-nginx'"},
                   agente=None, sempre=False)


if __name__ == "__main__":
    for arquivo in (HOOK, JUIZ):
        if not arquivo.is_file():
            print(f"ausente: {arquivo}", file=sys.stderr)
            sys.exit(2)
    sintaxe = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True)
    if sintaxe.returncode != 0:
        print(f"erro de sintaxe em {HOOK}:\n{sintaxe.stderr}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
