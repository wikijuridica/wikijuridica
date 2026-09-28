#!/usr/bin/env python3
"""Bancada de strip-heredoc-body.py — o auxiliar que tira da análise o corpo de heredoc
QUOTED (dado a caminho de um arquivo) e mantém o corpo que alimenta interpretador
(código que executa).

    python3 .claude/hooks/strip-heredoc-body.test.py

Os dois lados pesam igual:
  * DESPE o que é dado — o falso positivo de 2026-09-23 (`testa-terminal.sh` barrado pelo
    guarda do display porque o `.sh` do nome virou "interpretador") e o delimitador dentro
    de palavra (`GEOFF`), que encerrava o corpo cedo;
  * NÃO DESPE o que executa — heredoc de bash, python, ssh, inclusive `/bin/bash`, o `bash`
    da linha de baixo (no JSON, `\\n` + `bash`), `bash 2>&1` e a continuação de linha — e
    nunca apaga comando FORA do corpo (o resto da linha de abertura, a cauda do payload).

PROVA POR MUTAÇÃO (classe ProvaPorMutacao, roda junto com o resto): cada mutante é uma
cópia do auxiliar com UMA correção desfeita, gravada em diretório temporário, e a bancada
exige que o teste que cobre aquela correção fique VERMELHO contra ela — e que a cópia
intacta, pelo mesmo caminho, fique verde. Mutante que não aplica (o trecho mudou de forma)
reprova: é hora de atualizar o mutante, não de apagá-lo. m10 é a fronteira à esquerda
sugerida no briefing do conserto, `(?<![\\w./-])`: ela está aqui para provar o buraco
que teria aberto.

STRIP_HEREDOC_ALVO aponta a bancada para outra cópia do auxiliar; é por onde a prova por
mutação roda sem tocar o arquivo vivo.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # nada de __pycache__ ao lado do hook vivo

AQUI = Path(__file__).resolve().parent
ALVO = Path(os.environ.get("STRIP_HEREDOC_ALVO", str(AQUI / "strip-heredoc-body.py")))


def _carrega():
    spec = importlib.util.spec_from_file_location("strip_heredoc_body_sob_teste", ALVO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


MOD = _carrega()

# Montados por concatenação: este arquivo é lido e escrito por agentes cujo payload passa
# pelos hooks que usam o auxiliar.
ADD = "git " + "add"
COMMIT = "git " + "commit"
X = "DISPLAY=:" + "0 xdotool key a"


def esc(comando: str, ascii_: bool = True) -> str:
    """O comando como os chamadores o entregam: escapado de JSON, sem as aspas de fora."""
    return json.dumps(comando, ensure_ascii=ascii_)[1:-1]


def despe(comando: str, so_shell: bool = False) -> str:
    """Roda o auxiliar sobre o comando escapado e devolve o resultado DESESCAPADO. Se o
    corte partisse um par de escape, o json.loads daqui reprovaria."""
    return json.loads('"' + MOD.remover_corpos(esc(comando), so_shell) + '"')


class Despe(unittest.TestCase):
    """Corpo de heredoc quoted que é DADO sai da análise."""

    def test_nome_de_arquivo_terminado_em_sh_nao_e_interpretador(self):
        """FALSO POSITIVO MEDIDO (2026-09-23), forma reduzida do payload real.

        `cat > .../testa-terminal.sh <<'EOF'`: o `sh` de `.sh` casava como interpretador,
        o corpo ficava sob análise e block-display-zero-social.sh saía 2 (com destino
        `/tmp/x`, 0). O corpo real tem um `<<'PY'` aninhado, que vai junto.
        """
        comando = (
            "cat > /opt/wiki/ops/terminal/testa-terminal.sh <<'EOF'\n"
            "#!/usr/bin/env bash\n"
            "# nunca fala com o display :0 — todo programa X passa por x99()\n"
            "x99() { DISPLAY=:99 \"$@\"; }\n"
            f"x99 xdotool key shift+Return  # e nunca {X}\n"
            "python3 - \"$1\" <<'PY'\nimport struct\nPY\n"
            "EOF\n"
            "chmod 755 /opt/wiki/ops/terminal/testa-terminal.sh; bash -n ops/terminal/testa-terminal.sh"
        )
        self.assertEqual(
            despe(comando),
            "cat > /opt/wiki/ops/terminal/testa-terminal.sh <<'EOF'\nEOF\n"
            "chmod 755 /opt/wiki/ops/terminal/testa-terminal.sh; bash -n ops/terminal/testa-terminal.sh",
        )

    def test_extensao_ou_sufixo_nao_e_interpretador(self):
        for destino in ("notas.sh", "relatorio.python3", "x.bash", "gera-sh", "App.tsx",
                        "build_node", "lib.perl", "~/.zsh"):
            with self.subTest(destino=destino):
                self.assertEqual(despe(f"cat > {destino} <<'EOF'\n{X}\nEOF"),
                                 f"cat > {destino} <<'EOF'\nEOF")

    def test_formas_da_abertura(self):
        for abertura in ("<<'EOF'", '<<"EOF"', "<< 'EOF'", "<<-'EOF'"):
            with self.subTest(abertura=abertura):
                self.assertEqual(despe(f"cat > x {abertura}\n{X}\nEOF\necho fim"),
                                 f"cat > x {abertura}\nEOF\necho fim")

    def test_delimitador_dentro_de_palavra_nao_fecha(self):
        """m2. `find` sem âncora cortava no `EOF` de `GEOFF` e devolvia o resto à análise.
        `EOF ` (espaço depois) também não fecha: o bash 5.2 exige a linha exata (medido)."""
        corpo = f"GEOFF diz {X}\nEOF_OUTRO {X}\nxEOF {X}\nEOF \n{X}"
        self.assertEqual(despe(f"cat > nota.md <<'EOF'\n{corpo}\nEOF\necho fim"),
                         "cat > nota.md <<'EOF'\nEOF\necho fim")

    def test_tab_antes_do_delimitador_so_fecha_com_hifen(self):
        self.assertEqual(despe(f"cat > a <<-'EOF'\n\t{X}\n\tEOF\necho fim"),
                         "cat > a <<-'EOF'\n\tEOF\necho fim")
        sem_hifen = f"cat > a <<'EOF'\n{X}\n\tEOF\necho fim"  # `\tEOF` não fecha: sem fechamento
        self.assertEqual(despe(sem_hifen), sem_hifen)

    def test_cauda_que_nao_executa_o_corpo(self):
        """Controle do defeito 7: gravar e LER o arquivo, ou filtrar sem shell, é dado."""
        for abertura in (
            "cat <<'EOF' > doc.md && cat doc.md",
            "cat <<'EOF' | grep -c x",
            "cat > doc.md <<'EOF' && wc -l doc.md",
            "cat > notas.md <<'EOF' && bash tools/outro.sh",
            "cat > s.sh <<'EOF' && chmod +x s.sh",
            "cat > s.sh <<'EOF' && shellcheck s.sh",
            "cat > s.sh <<'EOF' && bash -n s.sh",   # m15: `-n` só confere a sintaxe
            "cat > s.sh <<'EOF' && sh -en s.sh",
            "cat <<'EOF' || bash",
        ):
            with self.subTest(abertura=abertura):
                self.assertEqual(despe(f"{abertura}\n{X}\nEOF"), f"{abertura}\nEOF")

    def test_delimitador_com_parentese_de_substituicao_fecha(self):
        """O bash 5.2 aceita `EOF)` dentro de `$(...)` (medido). Reconhecer fechamento a
        mais só encurta o corte; reconhecer a menos o alongaria sobre comando."""
        self.assertEqual(despe(f"x=$(cat <<'EOF'\n{X}\nEOF)\necho \"$x\""),
                         "x=$(cat <<'EOF'\nEOF)\necho \"$x\"")

    def test_substituicao_de_comando_entre_aspas_duplas(self):
        """`"$(cat <<'EOF'` é heredoc de verdade: a aspa dupla não o transforma em texto."""
        self.assertEqual(despe(f"x=\"$(cat <<'EOF'\n{X}\nEOF\n)\""), "x=\"$(cat <<'EOF'\nEOF\n)\"")


class NaoDespe(unittest.TestCase):
    """Corpo que EXECUTA fica sob análise — o fecho do guarda."""

    def assertIntacto(self, comando: str, so_shell: bool = False):
        self.assertEqual(despe(comando, so_shell), comando)

    def test_interpretadores_com_corpo_executado(self):
        for dono in (
            "python3 -", "env FOO=1 python3", "bash -s", "/bin/bash", "/usr/bin/python3 -",
            "cd /tmp\nbash",            # no JSON a quebra é `\n`: o `bash` vem depois de uma letra
            "cd /tmp\n\tbash",          # indentado com TAB: `\t` no JSON
            "echo x | sh", "true; bash", "y=$(bash", "bash 2>&1", "python3 - &>/dev/null",
            "python3 \\\n  -",          # continuação de linha entre o nome e o `<<`
            "sudo -u rafael bash", "\"$SHELL\"", "python3.11 -", "node", "ruby", "perl",
        ):
            with self.subTest(dono=dono):
                fecho = "\nEOF\n)" if dono.endswith("$(bash") else "\nEOF"
                self.assertIntacto(f"{dono} <<'EOF'\n{X}{fecho}")

    def test_aspas_duplas_no_delimitador(self):
        self.assertIntacto(f'bash -s <<"X"\n{X}\nX')

    def test_nomes_que_so_casavam_por_acaso_de_sufixo(self):
        """Sem fronteira à esquerda, `dash`, `ssh`, `fish`, `pwsh`, `ts-node`... casavam por
        terminarem em `sh`/`node`. Com a fronteira, eles têm de estar na lista pelo nome."""
        for dono in ("dash", "ssh localhost", "fish", "pwsh", "ts-node", "ksh", "zsh",
                     "mksh", "rbash", "tclsh", "busybox sh"):
            with self.subTest(dono=dono):
                self.assertIntacto(f"{dono} <<'EOF'\n{X}\nEOF")

    def test_corpo_que_vai_para_shell_pela_cauda_da_linha(self):
        """Defeito 7. O dono do `<<` é o `cat`/`tee`, mas a cauda da linha entrega o corpo a
        um shell: por pipe, ou gravando um arquivo que a MESMA linha executa. Medido em
        2026-09-23: estas formas saíam 0 nos três chamadores (git, heavy-go, display)."""
        for abertura in (
            "cat <<'EOF' | bash",
            "cat <<'EOF' | sh -s",
            "cat <<'EOF' | sudo bash",
            "cat <<'EOF' | sudo -u rafael bash -s",
            "cat <<'EOF' | tr -d '\\r' | bash",
            "cat <<'EOF' |& bash",
            "cat <<'EOF' > s.sh && bash s.sh",
            "cat > s.sh <<'EOF' && bash s.sh",
            "tee s.sh <<'EOF'; bash s.sh",
            "cat > /tmp/r.sh <<'EOF' && chmod +x /tmp/r.sh && /tmp/r.sh",
            "cat > r.sh <<'EOF' && chmod +x r.sh && ./r.sh",
            "cat > s.sh <<'EOF'; source s.sh",
            "cat > s.sh <<'EOF' && . ./s.sh",
            "cat > s.sh <<'EOF' && bash -x s.sh",   # opção que não é `-n` executa
        ):
            for so_shell in (False, True):
                with self.subTest(abertura=abertura, so_shell=so_shell):
                    self.assertIntacto(f"{abertura}\n{X}\nEOF", so_shell=so_shell)

    def test_pipe_para_python_so_fica_sem_so_shell(self):
        comando = f"cat <<'EOF' | python3 -\n{X}\nEOF"
        self.assertIntacto(comando)
        self.assertEqual(despe(comando, so_shell=True), "cat <<'EOF' | python3 -\nEOF")

    # LIMITE DECLARADO (docstring do auxiliar, defeito 7): `cat > s.sh <<'EOF'` … `EOF` e
    # `bash s.sh` numa linha SEGUINTE não é visto — é um script, e o auxiliar lê um comando.
    # Não há caso que trave esse comportamento: quem fechar a lacuna acrescenta o caso aqui.

    def test_heredoc_sem_fechamento_fica_intacto(self):
        self.assertIntacto(f"cat > x <<'EOF'\n{X}\nsem fechamento")
        self.assertIntacto("cat > x <<'EOF'")

    def test_payload_sem_heredoc_volta_byte_a_byte(self):
        for comando in ("ls -la /tmp", f"echo 'a\\nb' && {X}", "printf '%s\\n' \"—\" <<< x",
                        "echo $(( 1 << 2 ))", "cat <<EOF\nsem aspas: $(date)\nEOF"):
            for ascii_ in (True, False):
                with self.subTest(comando=comando, ascii_=ascii_):
                    texto = esc(comando, ascii_)
                    self.assertEqual(MOD.remover_corpos(texto), texto)


class NaoApagaComando(unittest.TestCase):
    """O corte nunca alcança comando fora do corpo. Os dois primeiros eram FALSO NEGATIVO
    medido no guarda do display em 2026-09-23 (exit 0 com xdotool no :0)."""

    def test_resto_da_linha_de_abertura_continua_sob_analise(self):
        """m4. O corte começava logo depois de `<<'EOF'` e engolia o `&& ...` da linha."""
        self.assertEqual(despe(f"cat > /tmp/x <<'EOF' && {X}\ntexto\nEOF"),
                         f"cat > /tmp/x <<'EOF' && {X}\nEOF")

    def test_abertura_dentro_de_corpo_nao_mutila_a_cauda(self):
        """m5. Abertura dentro de um corpo já cortado dava índice negativo, e o Python
        fatiava a CAUDA: `xdotool key a` virava `xdotooy a`."""
        comando = "cat > /tmp/a <<'EOF'\nfoo <<'Q'\n\nQ\n" + "c" * 18 + f"\nEOF\n{X}"
        self.assertEqual(despe(comando), f"cat > /tmp/a <<'EOF'\nEOF\n{X}")

    def test_abertura_entre_aspas_ou_em_comentario_nao_abre_heredoc(self):
        """m6. Tratada como abertura, ela escondia os comandos até o próximo `EOF` em
        linha própria."""
        for falsa in ("echo \"use cat <<'EOF' para escrever\"",
                      "echo 'use cat <<\"EOF\" para escrever'",
                      "true # cat <<'EOF' comentado"):
            with self.subTest(falsa=falsa):
                comando = f"{falsa}\n{X}\ncat > /tmp/b <<'EOF'\ndoc\nEOF"
                self.assertEqual(despe(comando), f"{falsa}\n{X}\ncat > /tmp/b <<'EOF'\nEOF")

    def test_here_string_nao_e_heredoc(self):
        comando = f"grep x <<<'EOF'\n{X}\ncat > /tmp/b <<'EOF'\ndoc\nEOF"
        self.assertEqual(despe(comando), f"grep x <<<'EOF'\n{X}\ncat > /tmp/b <<'EOF'\nEOF")

    def test_continuacao_na_linha_de_abertura(self):
        self.assertEqual(despe(f"cat > /tmp/x <<'EOF' \\\n  && {X}\ntexto\nEOF"),
                         f"cat > /tmp/x <<'EOF' \\\n  && {X}\nEOF")

    def test_barra_escapada_nao_e_quebra_de_linha(self):
        """`printf 'a\\nb'` chega como `a\\\\nb`: o par `\\\\` seguido de `n` não é quebra, e
        o corte não pode começar ali."""
        self.assertEqual(despe(f"cat > /tmp/x <<'EOF' && printf 'a\\nb' && {X}\ntexto\nEOF"),
                         f"cat > /tmp/x <<'EOF' && printf 'a\\nb' && {X}\nEOF")

    def test_janela_do_interpretador_para_na_quebra_de_linha(self):
        """`python3 x.py` na linha de cima não é dono do heredoc da linha de baixo."""
        self.assertEqual(despe(f"python3 x.py\ncat > doc.md <<'EOF'\n{X}\nEOF"),
                         "python3 x.py\ncat > doc.md <<'EOF'\nEOF")

    def test_leitura_incremental_da_linha_equivale_a_releitura(self):
        """m14. Várias aberturas na mesma linha: a leitura de aspas continua de onde a
        anterior parou (defeito 8) e tem de dar o veredito de quem relê a linha inteira."""
        linha = "echo \"a <<'Q' b\" ; cat > x <<'EOF' ; echo 'c <<\"R\" d'"
        self.assertEqual(despe(f"{linha}\n{X}\nEOF"), f"{linha}\nEOF")

    def test_dois_heredocs_seguidos(self):
        comando = f"cat > a <<'A'\ndoc a\nA\n{X}\ncat > b <<'B'\ndoc b\nB"
        self.assertEqual(despe(comando), f"cat > a <<'A'\nA\n{X}\ncat > b <<'B'\nB")


class Teto(unittest.TestCase):
    """Defeito 8: custo linear, e teto fail-safe que devolve o texto INTACTO."""

    def test_mais_de_32_aberturas_na_mesma_linha_devolve_intacto(self):
        """m12. 39 aberturas sem fechamento e, depois delas, uma de verdade: sem o teto, a
        quadragésima seria despida; com ele, o texto volta como chegou."""
        linha = " ".join(f"cat <<'Z{i}' ;" for i in range(39)) + " cat > a <<'EOF'"
        texto = esc(f"{linha}\n{X}\nEOF")
        self.assertEqual(MOD.remover_corpos(texto), texto)
        uma = esc(f"cat > a <<'EOF'\n{X}\nEOF")
        self.assertNotEqual(MOD.remover_corpos(uma), uma)  # a mesma abertura sozinha é despida

    def test_orcamento_de_tempo_esgotado_devolve_intacto(self):
        """m13. Orçamento esgotado = texto intacto (barra a mais, nunca a menos)."""
        texto = esc(f"cat > notas.sh <<'EOF'\n{X}\nEOF")
        self.assertEqual(MOD.remover_corpos(texto, orcamento=0.0), texto)
        self.assertNotEqual(MOD.remover_corpos(texto), texto)

    def test_linha_longa_com_muitas_aberturas_nao_custa_segundos(self):
        """Medido em 2026-09-23 antes do conserto: 60 aberturas numa linha de 60 KB, 264 ms;
        120 numa de 80 KB, 687 ms (a refutação mediu 300 × 80 KB em 56,5 s)."""
        texto = esc(("echo " + "a" * 2700 + " <<'EOF' ") * 300 + "\n" + "texto\n" * 50)
        inicio = time.perf_counter()
        saida = MOD.remover_corpos(texto)
        self.assertLess(time.perf_counter() - inicio, 1.0)
        self.assertEqual(saida, texto)  # acima do teto de aberturas por linha: intacto

    def test_muitas_aberturas_sem_fechamento_em_linhas_separadas(self):
        """O fechamento sai de um índice: 400 aberturas sem fechamento, uma por linha, num
        texto de 20 mil linhas, não varrem o texto 400 vezes."""
        linhas = ["python3 - <<'PY'"] + [f"print(`cat <<'X{i}'`)" for i in range(400)]
        texto = esc("\n".join(linhas + ["texto"] * 20000 + ["PY"]))
        inicio = time.perf_counter()
        saida = MOD.remover_corpos(texto)
        self.assertLess(time.perf_counter() - inicio, 1.0)
        self.assertEqual(saida, texto)


class SoShell(unittest.TestCase):
    """`--so-shell`: só o corpo que alimenta SHELL fica; o de python/node/perl sai."""

    def test_corpo_de_python_sai(self):
        comando = f"python3 - <<'EOF'\ndoc = '`{ADD} x` e `{COMMIT} -F m`'\nEOF"
        self.assertEqual(despe(comando, so_shell=True), "python3 - <<'EOF'\nEOF")
        self.assertEqual(despe(comando), comando)  # sem a opção, o corpo do python fica

    def test_corpo_de_shell_fica(self):
        for dono in ("bash", "sh -s", "ssh host", "/bin/bash", "sudo -u x bash", "source /dev/stdin"):
            with self.subTest(dono=dono):
                comando = f"{dono} <<'EOF'\n{ADD} x\n{COMMIT} -F m\nEOF"
                self.assertEqual(despe(comando, so_shell=True), comando)


class FormaDoTexto(unittest.TestCase):
    """O veredito não depende do serializador: envelope compacto ou espaçado, UTF-8 cru ou
    `\\uXXXX`, e texto cru com quebra de linha real."""

    def test_envelope_json_continua_json_e_despido(self):
        comando = f"cat > /opt/wiki/ops/terminal/testa-terminal.sh <<'EOF'\n{X}\nEOF\nchmod 755 x — ok"
        esperado = "cat > /opt/wiki/ops/terminal/testa-terminal.sh <<'EOF'\nEOF\nchmod 755 x — ok"
        for separadores in ((",", ":"), None):
            for ascii_ in (True, False):
                with self.subTest(separadores=separadores, ascii_=ascii_):
                    envelope = json.dumps(
                        {"tool_name": "Bash",
                         "tool_input": {"command": comando, "description": "Escreve com cat <<'EOF'"}},
                        separators=separadores, ensure_ascii=ascii_)
                    saida = json.loads(MOD.remover_corpos(envelope))
                    self.assertEqual(saida["tool_input"]["command"], esperado)
                    self.assertEqual(saida["tool_input"]["description"], "Escreve com cat <<'EOF'")

    def test_texto_cru_com_quebra_real(self):
        self.assertEqual(MOD.remover_corpos(f"cat > notas.sh <<'EOF'\n{X}\nEOF\necho fim"),
                         "cat > notas.sh <<'EOF'\nEOF\necho fim")
        self.assertEqual(MOD.remover_corpos(f"bash <<'EOF'\n{X}\nEOF"), f"bash <<'EOF'\n{X}\nEOF")


class LinhaDeComando(unittest.TestCase):
    """O contrato com os chamadores: `python3 -I`, falha em silêncio devolve o payload."""

    def roda(self, dados: bytes, *opcoes: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-B", str(ALVO), *opcoes],
                              input=dados, capture_output=True)

    def test_despe_pela_linha_de_comando(self):
        comando = f"cat > notas.sh <<'EOF'\n{X}\nEOF"
        r = self.roda(esc(comando).encode())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode(), esc("cat > notas.sh <<'EOF'\nEOF"))

    def test_so_shell_pela_linha_de_comando(self):
        comando = f"python3 - <<'EOF'\n{ADD} x\nEOF"
        self.assertEqual(self.roda(esc(comando).encode()).stdout.decode(), esc(comando))
        self.assertEqual(self.roda(esc(comando).encode(), "--so-shell").stdout.decode(),
                         esc("python3 - <<'EOF'\nEOF"))

    def test_sem_heredoc_volta_byte_a_byte_mesmo_com_utf8_invalido(self):
        dados = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo ação —"}},
                           ensure_ascii=False).encode() + b"\xff\xfe"
        r = self.roda(dados)
        self.assertEqual((r.returncode, r.stdout), (0, dados))

    def test_opcao_desconhecida_devolve_intacto(self):
        dados = esc(f"cat > notas.sh <<'EOF'\n{X}\nEOF").encode()
        self.assertEqual(self.roda(dados, "--outra").stdout, dados)

    def test_entrada_vazia_sai_1_sem_saida(self):
        r = self.roda(b"")
        self.assertEqual((r.returncode, r.stdout), (1, b""))


# (nome, o que desfaz, [(trecho, troca)], testes que TÊM de reprovar contra o mutante)
MUTANTES = [
    ("m1", "regex antiga do interpretador, sem fronteira à esquerda",
     [('INTERPRETADOR = _dono(_SHELLS + "|" + _OUTROS)',
       r'INTERPRETADOR = re.compile(r"(?:bash|sh|zsh|ksh|python3?|perl|ruby|node)\b[^\n;&|]{0,40}<<\s*$")')],
     ["Despe.test_nome_de_arquivo_terminado_em_sh_nao_e_interpretador",
      "Despe.test_extensao_ou_sufixo_nao_e_interpretador"]),
    # m2 recua a largura da quebra para que, no caso comum (delimitador em linha própria),
    # a saída tenha a mesma forma da versão ancorada: só o `EOF` dentro de palavra diverge.
    ("m2", "fechamento por find sem âncora de linha",
     [('fecho = t.fechamento(corpo, delimitador, achado.group(1) == "-")',
       "fecho = (lambda p: None if p < 0 else p - t.largura)(texto.find(delimitador, corpo))")],
     ["Despe.test_delimitador_dentro_de_palavra_nao_fecha"]),
    ("m4", "corte começando logo depois da abertura",
     [("corpo = t.fim_da_linha(achado.end())", "corpo = achado.end()")],
     ["NaoApagaComando.test_resto_da_linha_de_abertura_continua_sob_analise"]),
    ("m5", "abertura dentro de corpo já cortado volta a ser processada",
     [("busca = fecho", "busca = corpo")],
     ["NaoApagaComando.test_abertura_dentro_de_corpo_nao_mutila_a_cauda"]),
    ("m6", "abertura entre aspas ou em comentário tratada como heredoc",
     [("if not t.em_contexto_de_comando(achado.start()):", "if False:")],
     ["NaoApagaComando.test_abertura_entre_aspas_ou_em_comentario_nao_abre_heredoc"]),
    ("m7", "janela do interpretador parando no & de 2>&1",
     [("[<>]&|&>|", "")],
     ["NaoDespe.test_interpretadores_com_corpo_executado"]),
    ("m8", "janela do interpretador atravessando a quebra de linha do JSON",
     [(r"\\[^n\n]|", r"\\[^\n]|")],
     ["NaoApagaComando.test_janela_do_interpretador_para_na_quebra_de_linha"]),
    ("m9", "--so-shell ignorado",
     [("dono = SHELL if so_shell else INTERPRETADOR", "dono = INTERPRETADOR")],
     ["SoShell.test_corpo_de_python_sai"]),
    ("m10", "fronteira NEGATIVA (?<![\\w./-]) sugerida no briefing do conserto",
     [('_ESQUERDA = r"(?:^|(?<=[\\s;&|(){}`!\'\\"/=])|(?<=\\\\[nt]))"',
       '_ESQUERDA = r"(?<![\\w./-])"')],
     ["NaoDespe.test_interpretadores_com_corpo_executado"]),
    ("m11", "cauda da linha ignorada (pipe para shell, arquivo executado na mesma linha)",
     [("if _cauda_executa_o_corpo(antes, t.trecho(achado.end(), corpo), so_shell):", "if False:")],
     ["NaoDespe.test_corpo_que_vai_para_shell_pela_cauda_da_linha"]),
    ("m12", "sem o teto de aberturas por linha",
     [("if na_linha > _TETO_ABERTURAS_POR_LINHA:", "if False:")],
     ["Teto.test_mais_de_32_aberturas_na_mesma_linha_devolve_intacto"]),
    ("m13", "sem o orçamento de tempo",
     [("if time.monotonic() - inicio >= orcamento:", "if False:")],
     ["Teto.test_orcamento_de_tempo_esgotado_devolve_intacto"]),
    ("m14", "leitura incremental recomeçando do estado inicial",
     [("de, estado = self._ctx_pos, self._ctx_estado", "de, estado = self._ctx_pos, _ESTADO_INICIAL")],
     ["NaoApagaComando.test_leitura_incremental_da_linha_equivale_a_releitura"]),
    ("m15", "`bash -n s.sh` (só sintaxe) contado como execução",
     [(r"(?:\s+-(?![a-zA-Z]*n)\S+)*", r"(?:\s+-\S+)*")],
     ["Despe.test_cauda_que_nao_executa_o_corpo"]),
]


@unittest.skipIf(os.environ.get("STRIP_HEREDOC_ALVO"),
                 "rodada contra outra cópia: a prova por mutação não se repete dentro dela")
class ProvaPorMutacao(unittest.TestCase):

    def _roda_contra(self, fonte: str, testes: list[str]) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="strip-heredoc-mut-") as tmp:
            alvo = Path(tmp) / "strip-heredoc-body.py"
            alvo.write_text(fonte, encoding="utf-8")
            env = dict(os.environ, STRIP_HEREDOC_ALVO=str(alvo))
            return subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), *testes],
                                  capture_output=True, text=True, env=env)

    def test_controle_a_copia_intacta_passa_pelo_mesmo_caminho(self):
        testes = sorted({t for mutante in MUTANTES for t in mutante[-1]})
        r = self._roda_contra(ALVO.read_text(encoding="utf-8"), testes)
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])

    def test_cada_mutante_e_morto_pelo_teste_que_cobre_a_correcao(self):
        fonte = ALVO.read_text(encoding="utf-8")
        for nome, descricao, trocas, testes in MUTANTES:
            with self.subTest(mutante=nome):
                mutada = fonte
                for trecho, troca in trocas:
                    self.assertEqual(mutada.count(trecho), 1,
                                     f"{nome}: o trecho mudou de forma — atualize o mutante: {trecho!r}")
                    mutada = mutada.replace(trecho, troca)
                r = self._roda_contra(mutada, testes)
                # Morto = CADA teste listado reprovou por asserção (FAIL, não ERROR).
                morto = r.returncode != 0 and all(
                    f"FAIL: {t.split('.')[-1]} (__main__.{t})" in r.stderr for t in testes)
                print(f"\n  mutante {nome} ({descricao}): {'MORTO' if morto else 'VIVO'}"
                      f" por {', '.join(testes)}", file=sys.stderr)
                self.assertTrue(morto, f"{nome} sobreviveu:\n{r.stderr[-3000:]}")


if __name__ == "__main__":
    if not ALVO.is_file():
        print(f"auxiliar ausente: {ALVO}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
