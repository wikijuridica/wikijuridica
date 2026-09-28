#!/usr/bin/env python3
"""guarda_de_escrita.py — o juiz de .claude/hooks/block-write-fora-de-contexto.sh.

ORDEM DO DONO, 2026-09-22: o Sonnet 5 entra neste projeto "somente para ganhar contexto de forma
eficiente, sem editar". Os agentes do roster que rodam em Sonnet 5 escrevem apenas em:

  - .agents/runtime/contexto/             o mapa que a onda seguinte lê em vez de reinvestigar;
  - .claude/agent-memory[-local]/<nome>/  a memória do próprio agente. Com `memory: project` o
                                          harness habilita Read, Write e Edit por conta própria
                                          (https://code.claude.com/docs/en/sub-agents#enable-persistent-memory),
                                          então barrar a memória quebraria o agente, não a regra;
  - o scratchpad da sessão (`scratchpad_dir` do payload), que o harness declara temporário.

POR QUE O BASH TAMBÉM É JULGADO. Uma guarda que só olha Write e Edit deixa `echo > arquivo`,
`sed -i`, `git commit` e `python3 -c "open(p, 'w')"` passarem, e a regra passaria a existir só no
papel — que é exatamente o defeito que a ordem de 2026-09-22 corrige no roster. Para os agentes
restritos o Bash é leitura e medição, julgado por LISTA DE PERMISSÃO: comando fora da lista é
barrado com a explicação. O lado seguro segue a regra que block-display-zero-social.sh já
escreveu: falso positivo é visível e corrigível; falso negativo é silencioso.

RASCUNHO NÃO VERSIONADO: o agente de contexto pode escrever em /tmp e ${TMPDIR:-/tmp} (a skill
`estado-real`, que ele declara, grava lá); dentro do repositório continua só .agents/runtime/
contexto/ e a memória. `realpath` mantém a proteção: symlink de /tmp para dentro do repo continua
barrado. A casa só AVISA produto em /tmp (tools/hook-warn-tmp-product-write).

INTERPRETADOR (python/node/perl/ruby -c/-e/-p e heredoc): a guarda só lê código LITERAL entre
aspas simples. Código montado na execução — `$VAR`, `$(...)`, crase, heredoc com delimitador SEM
aspas contendo `$`/crase — é OPACO e barra (igual a `bash -c "$c"`), com mensagem que ensina a
forma aceita.

LIMITES CONHECIDOS, declarados em vez de maquiados:
  - código Python/Node/Perl/Ruby LITERAL é lido por padrões de escrita (write_text, os.remove,
    shutil, subprocess, fs.write*, child_process...) e, no caso de open()/File.open()/open de
    Perl, por LISTA DE PERMISSÃO do modo: só passa modo literal de leitura. Escrita escondida
    atrás de getattr com nome montado, importação dinâmica, método `.open(modo)` de objeto de
    classe desconhecida com modo em variável, ou sqlite3.connect() num caminho que ainda não
    existe (a biblioteca cria o arquivo vazio) não é vista;
  - awk e sed são lidos por analisador próprio (strings, regex, colchetes, endereços GNU), não
    pelo interpretador de verdade: construção que ele não reconhece como leitura, ele barra;
  - sqlite3: comentário SQL (/* */ e --) sai antes do juízo; dot-command que executa ou grava
    (.shell/.system/.output/.once/.import/.backup/.save/.load/.read/.clone/.excel…, por PREFIXO)
    barra; só SELECT e dot-command de leitura conhecido passam;
  - `case` com padrão `x)` dentro de uma substituição `$(...)` confunde a contagem de
    parênteses; a guarda, sem conseguir ler, barra.
  - MEDIDO, e por isso fora da lista de falsos positivos: `sort -o -` cria um ARQUIVO chamado
    `-` (GNU coreutils 9.4), então é escrita; `uniq f -` e `iconv -o -` escrevem na saída padrão.

Uso: python3 -I guarda_de_escrita.py <sempre|roster> <raiz> [agente-restrito ...] < payload.json
Saída (uma linha): PASSA | ILEGIVEL | BLOQUEIA<TAB><agente><TAB><motivo>
"""

from __future__ import annotations

import json
import os
import re
import sys

FERRAMENTAS_DE_ARQUIVO = ("Write", "Edit", "MultiEdit", "NotebookEdit")
DISPOSITIVOS_LIVRES = ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty")
PROFUNDIDADE_MAXIMA = 8


class ErroDeAnalise(Exception):
    """O comando não pôde ser lido com segurança; para agente restrito, isso barra."""


# ---------------------------------------------------------------------------------------------
# Destinos permitidos
# ---------------------------------------------------------------------------------------------


class Contexto:
    def __init__(self, raiz: str, agente: str, cwd: str | None, scratchpad: str | None):
        self.raiz = os.path.realpath(raiz)
        self.agente = agente
        self.cwd = cwd
        # Comando que roda em OUTRA máquina (o remoto de um `ssh`): lá nenhum destino é
        # permitido — o colhedor lê a torre, não escreve nela (2026-09-24).
        self.remoto = False
        bases = [os.path.join(self.raiz, ".agents", "runtime", "contexto")]
        if agente and re.fullmatch(r"[A-Za-z0-9_.-]+", agente):
            bases.append(os.path.join(self.raiz, ".claude", "agent-memory", agente))
            bases.append(os.path.join(self.raiz, ".claude", "agent-memory-local", agente))
        if scratchpad and os.path.isabs(scratchpad):
            bases.append(scratchpad)
        self.bases = [os.path.realpath(b) for b in bases]
        # Rascunho não versionado: /tmp e ${TMPDIR:-/tmp}, mas SÓ FORA do repositório. A ordem proíbe
        # EDITAR arquivo versionado, não usar scratch — e a skill `estado-real`, que os dois agentes de
        # contexto declaram, grava em /tmp no Passo 3. Dentro do repositório continua só
        # .agents/runtime/contexto/ e a memória, mesmo que a raiz esteja sob /tmp (o caso das
        # bancadas). O realpath mantém a proteção: symlink de /tmp para dentro do repo resolve para o
        # caminho versionado e continua barrado. A casa já só AVISA produto em /tmp
        # (tools/hook-warn-tmp-product-write), não barra.
        rascunho = ["/tmp", os.environ["TMPDIR"]] if os.environ.get("TMPDIR") else ["/tmp"]
        self.scratch = [os.path.realpath(b) for b in rascunho]

    def copia(self) -> "Contexto":
        outro = Contexto.__new__(Contexto)
        outro.__dict__.update(self.__dict__)
        return outro


def caminho_permitido(valor: str, ctx: Contexto, aceita_a_base: bool = False) -> bool:
    """Resolve como o shell resolveria (cwd, `~`, `..`, symlink) e confere se cai num destino
    permitido. O diretório-base em si só vale para mkdir."""
    if not valor or ctx.remoto:
        return False
    valor = os.path.expanduser(valor)
    if not os.path.isabs(valor):
        if ctx.cwd is None:
            return False
        valor = os.path.join(ctx.cwd, valor)
    real = os.path.realpath(valor)
    for base in ctx.bases:
        if real == base:
            return aceita_a_base
        if real.startswith(base.rstrip(os.sep) + os.sep):
            return True
    # Rascunho em /tmp/${TMPDIR}: permitido só FORA do repositório (a raiz pode estar sob /tmp nas
    # bancadas; ali a regra de arquivo versionado continua valendo).
    dentro_do_repo = real == ctx.raiz or real.startswith(ctx.raiz.rstrip(os.sep) + os.sep)
    if not dentro_do_repo:
        for base in ctx.scratch:
            if real == base:
                return aceita_a_base
            if real.startswith(base.rstrip(os.sep) + os.sep):
                return True
    return False


def _trava_aceitavel(palavra: dict, ctx: Contexto) -> bool:
    """O flock abre (e cria, se faltar) o arquivo de trava. Trava que já existe não muda de
    conteúdo; trava nova só vale em diretório de trava do sistema ou num destino permitido."""
    if palavra["dyn"]:
        return False
    valor = palavra["v"]
    if valor.isdigit():
        return True  # descritor já aberto
    caminho = os.path.expanduser(valor)
    if not os.path.isabs(caminho):
        if ctx.cwd is None:
            return False
        caminho = os.path.join(ctx.cwd, caminho)
    real = os.path.realpath(caminho)
    if os.path.exists(real):
        return True
    return real.startswith(("/tmp/", "/var/lock/", "/run/lock/", "/dev/shm/")) or caminho_permitido(valor, ctx)


def alvo_permitido(palavra: dict | None, ctx: Contexto, aceita_a_base: bool = False) -> bool:
    if palavra is None:
        return False
    valor = palavra["v"]
    if valor in DISPOSITIVOS_LIVRES or valor.startswith("/dev/fd/"):
        return True
    if palavra["dyn"]:
        return False  # variável ou substituição no destino: o valor só existe na execução
    return caminho_permitido(valor, ctx, aceita_a_base)


def _palavra(valor: str, origem: dict) -> dict:
    return {"t": "w", "v": valor, "dyn": origem["dyn"], "q": origem["q"]}


# ---------------------------------------------------------------------------------------------
# Tokenizador de shell: posição de comando, redirecionamento, substituição e heredoc,
# respeitando aspas. Não é um shell completo; o que ele não lê com segurança, ele recusa.
# ---------------------------------------------------------------------------------------------

REDIRECIONAMENTOS = ("&>>", "<<<", "<<-", "&>", ">>", ">|", "<<", "<>", ">&", "<&", ">", "<")
CONTROLE = (";;&", ";;", ";&", "&&", "||", "|&", ";", "|", "&", "(", ")", "\n")


def _fim_de_parenteses(s: str, i: int) -> int:
    """s[i] == '('. Índice logo depois do ')' que fecha, respeitando aspas e aninhamento."""
    profundidade = 0
    j, n = i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "'":
            k = s.find("'", j + 1)
            if k < 0:
                raise ErroDeAnalise("aspas simples sem fechamento")
            j = k + 1
            continue
        if c == '"':
            k = j + 1
            while k < n and s[k] != '"':
                k += 2 if s[k] == "\\" else 1
            if k >= n:
                raise ErroDeAnalise("aspas duplas sem fechamento")
            j = k + 1
            continue
        if c == "(":
            profundidade += 1
        elif c == ")":
            profundidade -= 1
            if profundidade == 0:
                return j + 1
        j += 1
    raise ErroDeAnalise("parêntese sem fechamento")


def _substituicao(s: str, i: int) -> tuple[int, str | None]:
    """s[i:i+2] == '$('. Devolve (fim, texto interno), ou (fim, None) para aritmética $((...))."""
    fim = _fim_de_parenteses(s, i + 1)
    if s.startswith("((", i + 1):
        return fim, None
    return fim, s[i + 2 : fim - 1]


def substituicoes_em_texto_cru(texto: str) -> list[str]:
    """$(...) e `...` num corpo de heredoc com delimitador SEM aspas: ali o shell executa."""
    achadas = []
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if c == "\\":
            i += 2
            continue
        if c == "$" and i + 1 < n and texto[i + 1] == "(":
            fim, interno = _substituicao(texto, i)
            if interno is not None:
                achadas.append(interno)
            i = fim
            continue
        if c == "`":
            k = texto.find("`", i + 1)
            if k < 0:
                raise ErroDeAnalise("crase sem fechamento no heredoc")
            achadas.append(texto[i + 1 : k])
            i = k + 1
            continue
        i += 1
    return achadas


def tokeniza(s: str) -> tuple[list[dict], list[str]]:
    """Devolve (tokens, substituições).

    Palavra ('w'): valor sem aspas, 'dyn' (tem $ ou substituição fora de aspas simples) e 'q'
    (teve aspas ou escape — decide se o corpo de heredoc expande). Redirecionamento ('r'):
    operador, descritor colado ('fd') e, no heredoc, delimitador e corpo, lidos depois da quebra
    de linha como o shell faz. Controle ('op'): ; && || | & ( ) quebra de linha e os de case."""
    toks: list[dict] = []
    subs: list[str] = []
    pendentes: list[dict] = []
    atual: list[str] = []
    estado = {"ativo": False, "dyn": False, "q": False}
    i, n = 0, len(s)

    def fecha() -> None:
        if estado["ativo"]:
            palavra = {"t": "w", "v": "".join(atual), "dyn": estado["dyn"], "q": estado["q"]}
            ultimo = toks[-1] if toks else None
            if ultimo is not None and ultimo["t"] == "r" and ultimo["v"] in ("<<", "<<-") and "delim" not in ultimo:
                ultimo["delim"] = palavra["v"]
                ultimo["delim_q"] = palavra["q"]
                pendentes.append(ultimo)
            toks.append(palavra)
        atual.clear()
        estado.update(ativo=False, dyn=False, q=False)

    def consome_heredocs(pos: int) -> int:
        for r in pendentes:
            linhas = []
            while pos < n:
                quebra = s.find("\n", pos)
                linha = s[pos:] if quebra < 0 else s[pos:quebra]
                pos = n if quebra < 0 else quebra + 1
                if (linha.lstrip("\t") if r["v"] == "<<-" else linha) == r["delim"]:
                    break
                linhas.append(linha)
            r["corpo"] = "\n".join(linhas)
            if not r["delim_q"]:
                subs.extend(substituicoes_em_texto_cru(r["corpo"]))
        pendentes.clear()
        return pos

    while i < n:
        c = s[i]
        if c in " \t":
            fecha()
            i += 1
            continue
        if c == "\\":
            if i + 1 < n and s[i + 1] == "\n":
                i += 2
                continue
            if i + 1 < n:
                atual.append(s[i + 1])
            estado.update(ativo=True, q=True)
            i += 2
            continue
        if c == "#" and not estado["ativo"]:
            quebra = s.find("\n", i)
            i = n if quebra < 0 else quebra
            continue
        if c == "'":
            k = s.find("'", i + 1)
            if k < 0:
                raise ErroDeAnalise("aspas simples sem fechamento")
            atual.append(s[i + 1 : k])
            estado.update(ativo=True, q=True)
            i = k + 1
            continue
        if c == '"':
            j = i + 1
            trecho = []
            while j < n and s[j] != '"':
                if s[j] == "\\" and j + 1 < n and s[j + 1] in '$`"\\\n':
                    trecho.append(s[j + 1])
                    j += 2
                    continue
                if s[j] == "$" and j + 1 < n and s[j + 1] == "(":
                    fim, interno = _substituicao(s, j)
                    if interno is not None:
                        subs.append(interno)
                    estado["dyn"] = True
                    trecho.append(s[j:fim])
                    j = fim
                    continue
                if s[j] == "`":
                    k = s.find("`", j + 1)
                    if k < 0:
                        raise ErroDeAnalise("crase sem fechamento")
                    subs.append(s[j + 1 : k])
                    estado["dyn"] = True
                    trecho.append(s[j : k + 1])
                    j = k + 1
                    continue
                if s[j] == "$":
                    estado["dyn"] = True
                trecho.append(s[j])
                j += 1
            if j >= n:
                raise ErroDeAnalise("aspas duplas sem fechamento")
            atual.append("".join(trecho))
            estado.update(ativo=True, q=True)
            i = j + 1
            continue
        if c == "$":
            if i + 1 < n and s[i + 1] == "(":
                fim, interno = _substituicao(s, i)
                if interno is not None:
                    subs.append(interno)
                atual.append(s[i:fim])
                estado.update(ativo=True, dyn=True)
                i = fim
                continue
            if i + 1 < n and s[i + 1] == "'":
                k = i + 2
                while k < n and s[k] != "'":
                    k += 2 if s[k] == "\\" else 1
                if k >= n:
                    raise ErroDeAnalise("aspas $'...' sem fechamento")
                atual.append(s[i + 2 : k])
                estado.update(ativo=True, q=True)
                i = k + 1
                continue
            atual.append(c)
            estado.update(ativo=True, dyn=True)
            i += 1
            continue
        if c == "`":
            k = s.find("`", i + 1)
            if k < 0:
                raise ErroDeAnalise("crase sem fechamento")
            subs.append(s[i + 1 : k])
            atual.append(s[i : k + 1])
            estado.update(ativo=True, dyn=True)
            i = k + 1
            continue
        if c in "<>" and i + 1 < n and s[i + 1] == "(":
            fim = _fim_de_parenteses(s, i + 1)  # substituição de processo: o interno roda
            subs.append(s[i + 2 : fim - 1])
            atual.append(s[i:fim])
            estado.update(ativo=True, dyn=True)
            i = fim
            continue
        if c == "(" and not estado["ativo"] and s.startswith("((", i) and (not toks or toks[-1]["t"] == "op"):
            fim = _fim_de_parenteses(s, i)  # comando aritmético (( ... )): não escreve nada
            toks.append({"t": "w", "v": "((aritmetica))", "dyn": False, "q": False})
            i = fim
            continue
        if c in "<>" or (c == "&" and s.startswith("&>", i)):
            descritor = ""
            valor_atual = "".join(atual)
            if estado["ativo"] and valor_atual.isdigit() and not estado["dyn"] and not estado["q"]:
                descritor = valor_atual
                atual.clear()
                estado.update(ativo=False, dyn=False, q=False)
            else:
                fecha()
            operador = next(o for o in REDIRECIONAMENTOS if s.startswith(o, i))
            toks.append({"t": "r", "v": operador, "fd": descritor})
            i += len(operador)
            continue
        if c in ";&|()\n":
            fecha()
            operador = next(o for o in CONTROLE if s.startswith(o, i))
            toks.append({"t": "op", "v": operador})
            i += len(operador)
            if operador == "\n" and pendentes:
                i = consome_heredocs(i)
            continue
        atual.append(c)
        estado["ativo"] = True
        i += 1
    fecha()
    if pendentes:
        consome_heredocs(n)
    return toks, subs


def comandos_simples(toks: list[dict]) -> list[dict]:
    """Parte os tokens em comandos simples: palavras, redirecionamentos e o operador que o fechou."""
    comandos = []
    atual = {"palavras": [], "redirs": [], "fim": None}
    k = 0
    while k < len(toks):
        t = toks[k]
        if t["t"] == "op":
            if atual["palavras"] or atual["redirs"]:
                atual["fim"] = t["v"]
                comandos.append(atual)
            atual = {"palavras": [], "redirs": [], "fim": None}
            k += 1
            continue
        if t["t"] == "r":
            alvo = toks[k + 1] if k + 1 < len(toks) and toks[k + 1]["t"] == "w" else None
            atual["redirs"].append((t, alvo))
            k += 2 if alvo is not None else 1
            continue
        atual["palavras"].append(t)
        k += 1
    if atual["palavras"] or atual["redirs"]:
        comandos.append(atual)
    return comandos


# ---------------------------------------------------------------------------------------------
# Código embutido (python/node/perl/ruby) e SQL
# ---------------------------------------------------------------------------------------------

PADROES_POR_LINGUAGEM = {
    "python": [
        ("arquivo de log", re.compile(r"FileHandler\s*\(|\bbasicConfig\s*\([^)]*\bfilename\s*=")),
        ("escrita por pathlib", re.compile(r"\.(write_text|write_bytes|unlink|rmdir|mkdir|touch|rename|replace|symlink_to|hardlink_to|link_to|chmod|lchmod)\s*\(")),
        ("escrita por os.*", re.compile(r"\bos\.(remove|unlink|rmdir|removedirs|rename|renames|replace|mkdir|makedirs|symlink|link|chmod|chown|lchown|truncate|ftruncate|write|system|popen|posix_spawn\w*|spawn\w*|exec\w*|mkfifo|mknod|utime)\s*\(")),
        ("shutil", re.compile(r"\bshutil\b")),
        ("subprocesso", re.compile(r"\b(subprocess|pty|pexpect)\b")),
        ("código dinâmico", re.compile(r"\b(exec|eval|compile)\s*\(|__import__\s*\(|\bimportlib\b|__builtins__")),
        ("arquivo temporário", re.compile(r"\btempfile\b")),
        # Apelido e importação direta escondem o receptor `os.` dos padrões acima — medido: os três
        # passavam antes deste bloco (import os as o; from os import remove; getattr(os, 'remove')).
        ("módulo de sistema com apelido", re.compile(r"\bimport\s+(os|io|codecs|pathlib|posix|nt)\s+as\b")),
        ("função de escrita importada direto", re.compile(
            r"\bfrom\s+(os|posix|nt)\s+import\s+[^\n;]*\b(remove|unlink|rmdir|removedirs|rename|renames|replace|mkdir|makedirs|symlink|link|chmod|chown|lchown|truncate|ftruncate|system|popen|write|open|fdopen|spawn\w*|exec\w*|posix_spawn\w*|mkfifo|mknod|utime)\b"
            r"|\bfrom\s+(os|io|codecs|pathlib|posix|nt)\s+import\s+\*")),
        ("acesso indireto a função de sistema", re.compile(
            r"\bgetattr\s*\(\s*(os|io|codecs|posix|nt|pathlib|Path|builtins)\b|\b(os|posix|nt|builtins)\.__dict__|\bvars\s*\(\s*(os|posix|nt|builtins)\s*\)")),
        ("escrita por pandas/matplotlib", re.compile(r"\.(to_csv|to_json|to_parquet|to_excel|to_pickle|savefig)\s*\(")),
        ("download para arquivo", re.compile(r"\burlretrieve\s*\(")),
    ],
    "node": [
        ("escrita por fs", re.compile(r"\bfs(?:\.promises)?\.(write\w*|append\w*|unlink\w*|rm\w*|mkdir\w*|rename\w*|copyFile\w*|cp\w*|symlink\w*|link\w*|chmod\w*|chown\w*|truncate\w*|createWriteStream|utimes\w*|mkdtemp\w*)\s*\(")),
        # Pelo nome, com qualquer receptor ou nenhum: require('fs').writeFileSync(...) e a
        # desestruturação `const {writeFileSync} = require('fs')` passavam pelo padrão acima.
        ("função de escrita do fs", re.compile(
            r"\b(writeFile|writeFileSync|appendFile|appendFileSync|unlink|unlinkSync|rmSync|rmdir|rmdirSync|mkdir|mkdirSync"
            r"|rename|renameSync|copyFile|copyFileSync|cpSync|symlink|symlinkSync|chmod|chmodSync|chown|chownSync"
            r"|truncate|truncateSync|createWriteStream|utimes|utimesSync|mkdtemp|mkdtempSync)\s*\(")),
        ("processo filho", re.compile(r"\bchild_process\b|\b(execSync|execFileSync|spawnSync)\b")),
        ("código dinâmico", re.compile(r"\beval\s*\(|\bnew\s+Function\b|\bprocess\.binding\b")),
    ],
    "perl": [
        ("open de escrita", re.compile(r"\bopen\s*\(?[^;]*?['\"]\s*(\+?>|\||\+<)")),
        ("escrita por função de arquivo", re.compile(r"\b(unlink|rename|mkdir|rmdir|chmod|chown|truncate|symlink|link|utime|sysopen)\b")),
        # File::Copy, File::Path, File::Slurp(er): copiar, mover, criar e apagar árvore, gravar arquivo.
        ("escrita por módulo de arquivo", re.compile(
            r"\b(copy|move|cp|mv|mkpath|make_path|remove_tree|rmtree|write_file|write_text|write_binary|append_file|edit_file\w*)\s*\(")),
        ("execução de comando", re.compile(r"\b(system|exec|fork)\b|`|\bqx\s*[\W]")),
    ],
    "ruby": [
        ("escrita por File/Dir/IO", re.compile(r"\b(File|IO)\.(write|binwrite|delete|unlink|rename|symlink|chmod)|\bDir\.(mkdir|rmdir|delete|unlink)|\bFileUtils\b")),
        # f.write/f.puts em handle, Pathname#write — qualquer receptor, menos a saída padrão.
        ("escrita por método de arquivo", re.compile(
            r"(?<!\$stdout)(?<!STDOUT)(?<!\$stderr)(?<!STDERR)\.(write|binwrite|syswrite)\b"
            r"|\bPathname\b[^;\n]*\.(write|binwrite|delete|unlink|rename|mkpath|rmtree|rmdir|mkdir|make_symlink|make_link|truncate)\b")),
        ("execução de comando", re.compile(r"\b(system|exec|spawn|fork)\b|`|%x[\[{(]|\bIO\.popen\b")),
    ],
}

# Pragmas que só leem, mesmo com argumento entre parênteses; qualquer outro `pragma x(...)` grava.
PRAGMAS_DE_LEITURA = {"table_info", "table_xinfo", "table_list", "index_list", "index_info", "index_xinfo",
                      "foreign_key_list", "foreign_key_check", "integrity_check", "quick_check", "function_list",
                      "pragma_list", "module_list", "collation_list", "database_list", "compile_options"}
SQL_DE_ESCRITA = re.compile(
    r"(?is)\b(insert\s+(or\s+\w+\s+)?into|update\s+\S+\s+set|delete\s+from|replace\s+into"
    r"|create\s+(temp\w*\s+|unique\s+|virtual\s+)?(table|index|view|trigger)"
    r"|drop\s+(table|index|view|trigger)|alter\s+table|vacuum|reindex|attach\s+(database\s+)?['\"]|detach\s+)"
    r"|\bpragma\s+[\w.]+\s*="
    # pragmas que gravam sem `=`: checkpoint do WAL, optimize (roda ANALYZE), vácuo incremental
    r"|\bpragma\s+(\w+\.)?(wal_checkpoint|optimize|incremental_vacuum)\b"
    # funções da shell do sqlite que gravam arquivo, abrem editor ou carregam código nativo
    r"|\b(writefile|edit|load_extension|fts3_tokenizer)\s*\("
    r"|(^|[\n;(])\s*analyze\b"
    r"|(^|[\n;])\s*\.(import|save|backup|restore|output|once|shell|system|load|excel|clone|recover"
    r"|log|trace|iotrace|open|read|archive|ar)\b"
)
_PRAGMA_COM_PARENTESES = re.compile(r"(?i)\bpragma\s+(?:\w+\.)?(\w+)\s*\(")

# Dot-commands da shell do sqlite. A shell casa por PREFIXO (strncmp), então `.sh`, `.sys`, `.out`,
# `.imp`, `.sav`, `.bac`, `.res` valem pelos nomes inteiros — por isso o teste é por prefixo, não por
# igualdade (RT-B2 M6). Escrita/execução barram; o resto é leitura conhecida. Comentário SQL sai
# antes (INSERT/**/INTO, insert--c\ninto).
_DOT_ESCRITA = ("shell", "system", "output", "once", "import", "backup", "restore", "save", "load",
                "excel", "clone", "read", "log", "trace", "iotrace", "open", "archive", "recover",
                "ar", "cd", "edit", "expert", "lint", "dbconfig", "www")
_DOT_LEITURA = ("tables", "schema", "mode", "headers", "header", "indexes", "indices", "dbinfo",
                "databases", "help", "print", "show", "timer", "width", "nullvalue", "separator",
                "echo", "bail", "changes", "eqp", "explain", "stats", "dump", "fullschema", "quit",
                "exit", "parameter", "limit", "sha3sum", "selftest", "vfsinfo", "vfslist", "vfsname",
                "connection", "prompt", "binary", "scanstats", "version", "databases")
_DOT_INICIO = re.compile(r"(?im)^[ \t]*\.([A-Za-z]+)")


def _remove_comentarios_sql(sql: str) -> str:
    """Tira comentário de bloco (/* */) e de linha (--), trocando por espaço para não colar tokens
    (INSERT/**/INTO → INSERT INTO). Conservador de propósito: comentar não pode esconder escrita."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _sqlite_dot_escreve(sql: str) -> str | None:
    """Um dot-command que executa ou grava barra. Como a shell casa por prefixo, o token é comparado
    por prefixo contra as duas listas: se puder resolver para um dot de escrita, barra; se não
    resolver para nenhum dot de leitura conhecido, barra (lado seguro)."""
    for m in _DOT_INICIO.finditer(sql):
        t = m.group(1).lower()
        if any(nome.startswith(t) or t.startswith(nome) for nome in _DOT_ESCRITA):
            return f"sqlite dot-command .{t} executa ou grava"
        if not any(nome.startswith(t) for nome in _DOT_LEITURA):
            return f"sqlite dot-command .{t} não é leitura conhecida"
    return None


def sql_escreve(sql: str) -> bool:
    sql = _remove_comentarios_sql(sql)
    if SQL_DE_ESCRITA.search(sql):
        return True
    if _sqlite_dot_escreve(sql):
        return True
    return any(m.group(1).lower() not in PRAGMAS_DE_LEITURA for m in _PRAGMA_COM_PARENTESES.finditer(sql))


# ---------------------------------------------------------------------------------------------
# open() por lista de permissão do modo (Python, Ruby e Perl)
#
# Padrão de escrita não vê `m = 'w'; open(p, m)`, `open(p, chr(119))` nem `open(p, **kw)` — os três
# medidos pelo red team de 2026-09-22 saíam com exit 0. A regra invertida fecha a família: open
# com modo que não é LITERAL de leitura é barrado, seja qual for a forma de montar o modo.
# ---------------------------------------------------------------------------------------------

_LITERAL = re.compile(r"""[rRuUbBfF]{0,2}(['"])((?:(?!\1)[^\\\n])*)\1""")
LEITURA_PY = re.compile(r"[rbtU]+")
LEITURA_RUBY = re.compile(r"r[bt]?(:[\w|:-]+)?")


def _pula_texto(codigo: str, j: int) -> int:
    """codigo[j] é aspa; devolve o índice depois da aspa que fecha."""
    aspa, k, n = codigo[j], j + 1, len(codigo)
    while k < n and codigo[k] != aspa:
        k += 2 if codigo[k] == "\\" else 1
    return k + 1


def _fim_do_grupo(codigo: str, i: int) -> int:
    """codigo[i] abre '(', '[' ou '{'. Índice do fechamento correspondente, ou -1."""
    profundidade, j, n = 0, i, len(codigo)
    while j < n:
        c = codigo[j]
        if c in "'\"":
            j = _pula_texto(codigo, j)
            continue
        if c in "([{":
            profundidade += 1
        elif c in ")]}":
            profundidade -= 1
            if profundidade == 0:
                return j
        j += 1
    return -1


def _argumentos(texto: str) -> list[str]:
    """Parte uma lista de argumentos nas vírgulas de primeiro nível (fora de strings e grupos)."""
    partes, atual, profundidade, j, n = [], [], 0, 0, len(texto)
    while j < n:
        c = texto[j]
        if c in "'\"":
            fim = _pula_texto(texto, j)
            atual.append(texto[j:fim])
            j = fim
            continue
        if c in "([{":
            profundidade += 1
        elif c in ")]}":
            profundidade -= 1
        elif c == "," and profundidade == 0:
            partes.append("".join(atual).strip())
            atual = []
            j += 1
            continue
        atual.append(c)
        j += 1
    if "".join(atual).strip():
        partes.append("".join(atual).strip())
    return partes


def _literal(valor: str) -> str | None:
    m = _LITERAL.fullmatch(valor.strip())
    return m.group(2) if m else None


def _classifica(partes: list[str], separador: str) -> tuple[list[str], dict, bool]:
    """(posicionais, nomeados, tem_expansao). `separador` é '=' (Python) ou ':' (Ruby)."""
    posicionais, nomeados, expansao = [], {}, False
    for parte in partes:
        if parte.startswith("*") or parte.startswith("&"):
            expansao = True
            continue
        m = re.match(r"([A-Za-z_]\w*)\s*" + re.escape(separador) + r"(?!=)\s*(.*)$", parte, re.S)
        if m:
            nomeados[m.group(1)] = m.group(2)
        else:
            posicionais.append(parte)
    return posicionais, nomeados, expansao


def _modo_prova_leitura(valor: str | None, leitura: re.Pattern) -> bool:
    if valor is None:
        return True
    texto = _literal(valor)
    return texto is not None and leitura.fullmatch(texto) is not None


# (regex do nome chamado, posição do modo, nome do argumento de modo, o padrão grava?)
_ABERTURAS_PY = [
    (re.compile(r"(?<![\w.])open\s*\("), 1, "mode", False),
    (re.compile(r"\b(?:io|codecs|gzip|bz2|lzma|builtins|tarfile)\s*\.\s*open\s*\("), 1, "mode", False),
    (re.compile(r"\bos\s*\.\s*fdopen\s*\("), 1, "mode", False),
    (re.compile(r"\b(?:zipfile\s*\.\s*)?ZipFile\s*\(|\b(?:tarfile\s*\.\s*)?TarFile\s*\("), 1, "mode", False),
    (re.compile(r"\bdbm(?:\s*\.\s*\w+)?\s*\.\s*open\s*\("), 1, "flag", False),
    (re.compile(r"\bshelve\s*\.\s*open\s*\("), 1, "flag", True),
]
_METODO_OPEN_PY = re.compile(r"(?<!\bos)(?<!\bio)(?<!codecs)(?<!gzip)(?<!\bbz2)(?<!lzma)(?<!tarfile)(?<!builtins)(?<!\bdbm)(?<!shelve)"
                             r"\s*\.\s*open\s*\(")
_OS_OPEN = re.compile(r"\bos\s*\.\s*open\s*\(")


def _python_abre_para_escrever(codigo: str) -> str | None:
    for padrao, posicao, chave, padrao_grava in _ABERTURAS_PY:
        for m in padrao.finditer(codigo):
            fim = _fim_do_grupo(codigo, m.end() - 1)
            if fim < 0:
                return "chamada open() que a guarda não consegue ler"
            posicionais, nomeados, expansao = _classifica(_argumentos(codigo[m.end():fim]), "=")
            if expansao:
                return "open() com argumentos expandidos (*args/**kw): o modo não se prova leitura"
            if "opener" in nomeados:
                return "open() com opener próprio"
            modo = nomeados.get(chave, posicionais[posicao] if len(posicionais) > posicao else None)
            if modo is None and padrao_grava:
                return f"{m.group(0).strip()} cria ou grava por padrão"
            leitura = re.compile(r"r") if chave == "flag" else LEITURA_PY
            if not _modo_prova_leitura(modo, leitura):
                return f"{m.group(0).strip()}...) com modo que não é literal de leitura ({modo})"
    for m in _METODO_OPEN_PY.finditer(codigo):
        # método .open() de objeto desconhecido (Path, Image...): a assinatura varia, então só o
        # modo explícito decide — literal de escrita ou modo em variável nomeada barram.
        fim = _fim_do_grupo(codigo, m.end() - 1)
        if fim < 0:
            return "chamada .open() que a guarda não consegue ler"
        posicionais, nomeados, expansao = _classifica(_argumentos(codigo[m.end():fim]), "=")
        if expansao:
            return ".open() com argumentos expandidos (*args/**kw)"
        if "mode" in nomeados and not _modo_prova_leitura(nomeados["mode"], LEITURA_PY):
            return f".open(mode={nomeados['mode']})"
        for p in posicionais:
            texto = _literal(p)
            if texto is not None and re.fullmatch(r"[rwaxbtU+]{1,4}", texto) and not LEITURA_PY.fullmatch(texto):
                return f".open('{texto}')"
    for m in _OS_OPEN.finditer(codigo):
        fim = _fim_do_grupo(codigo, m.end() - 1)
        partes = _argumentos(codigo[m.end():fim]) if fim >= 0 else []
        bandeiras = partes[1] if len(partes) > 1 else ""
        if fim < 0 or not re.fullmatch(r"\s*os\s*\.\s*O_RDONLY(\s*\|\s*os\s*\.\s*O_(CLOEXEC|NOFOLLOW|DIRECTORY|NONBLOCK|NOCTTY))*\s*", bandeiras):
            return f"os.open com bandeiras que não são só de leitura ({bandeiras or '?'})"
    return None


def _ruby_abre_para_escrever(codigo: str) -> str | None:
    for m in re.finditer(r"(?:\b(?:File|Kernel|IO)\s*\.\s*(?:open|new|sysopen)|(?<![\w.])open)(\s*\(|\s+(?=[\"'\w$@:]))", codigo):
        if m.group(1).strip() == "(":
            fim = _fim_do_grupo(codigo, m.end() - 1)
            if fim < 0:
                return "open do Ruby que a guarda não consegue ler"
            partes = _argumentos(codigo[m.end():fim])
        else:  # sem parênteses: até ; quebra de linha, `do` ou `{`
            partes = _argumentos(re.split(r";|\n|\bdo\b|\{", codigo[m.end():], maxsplit=1)[0])
        posicionais, nomeados, expansao = _classifica(partes, ":")
        if expansao:
            return "open do Ruby com argumentos expandidos"
        primeiro = _literal(posicionais[0]) if posicionais else None
        if primeiro is not None and primeiro.startswith("|"):
            return "open do Ruby com pipe executa comando"
        modo = nomeados.get("mode", posicionais[1] if len(posicionais) > 1 else None)
        if not _modo_prova_leitura(modo, LEITURA_RUBY):
            return f"open do Ruby com modo que não é literal de leitura ({modo})"
    return None


def _perl_abre_para_escrever(codigo: str) -> str | None:
    for m in re.finditer(r"\bopen\s*(?:(\()|(?=(?:my\s+)?[$\w]+\s*,))", codigo):
        if m.group(1):
            fim = _fim_do_grupo(codigo, m.end() - 1)
            if fim < 0:
                return "open do Perl que a guarda não consegue ler"
            partes = _argumentos(codigo[m.end():fim])
        else:
            trecho = re.split(r";|\bor\b|\|\||\bdie\b", codigo[m.end():], maxsplit=1)[0]
            partes = _argumentos(trecho)
        modo = _literal(partes[1]) if len(partes) > 1 else None
        if modo is None or not re.match(r"\s*<", modo) or re.search(r"[>|]", modo):
            return f"open do Perl sem modo literal de leitura ({partes[1] if len(partes) > 1 else '?'})"
    return None


def codigo_escreve(codigo: str, familia: str) -> str | None:
    for nome, padrao in PADROES_POR_LINGUAGEM.get(familia, []):
        if padrao.search(codigo):
            return nome
    abre = {"python": _python_abre_para_escrever, "ruby": _ruby_abre_para_escrever,
            "perl": _perl_abre_para_escrever}.get(familia)
    motivo = abre(codigo) if abre else None
    if motivo:
        return motivo
    if re.search(r"\bsqlite3?\b", codigo) and sql_escreve(codigo):
        return "SQL de escrita"
    return None


# ---------------------------------------------------------------------------------------------
# Julgamento de um comando simples
# ---------------------------------------------------------------------------------------------

# Leitura pura: não escreve arquivo por conta própria (o redirecionamento é julgado à parte).
# O que não está aqui nem tem juiz próprio abaixo é barrado — lista de permissão.
LEITURA_PURA = {
    "cat", "tac", "head", "tail", "less", "more", "wc", "ls", "stat", "file", "grep", "egrep", "fgrep",
    "rg", "ag", "cut", "tr", "jq", "column", "nl", "od", "xxd", "hexdump", "strings", "diff", "cmp",
    "comm", "join", "paste", "fold", "fmt", "expand", "unexpand", "rev", "basename", "dirname",
    "realpath", "readlink", "pwd", "echo", "printf", "uptime", "nproc", "free", "df", "du", "ps",
    "pgrep", "pstree", "id", "whoami", "groups", "uname", "which", "whereis", "type", "sha256sum",
    "sha1sum", "sha512sum", "sha224sum", "sha384sum", "md5sum", "b2sum", "cksum", "sum", "base64",
    "base32", "true", "false", "test", "[", "[[", "sleep", "seq", "tree", "lsof", "ss", "netstat",
    "getent", "locale", "printenv", "zcat", "zgrep", "zless", "zdiff", "bzcat", "xzcat", "zstdcat",
    "numfmt", "bc", "expr", "shuf", "envsubst", "lscpu", "lsblk", "lsmem", "vmstat", "iostat",
    "mpstat", "top", "nvidia-smi", "man", "help", "info", "apropos", "whatis", "dig", "host",
    "nslookup", "ping", "getconf", "tput", "yes", "fd", "fdfind", "let", ":", "return", "exit",
    "break", "continue", "shift", "getopts", "hash", "ulimit", "umask", "read", "wait", "export",
    "set", "unset", "shopt", "local", "declare", "typeset", "readonly", "((aritmetica))",
    # `date` (sem -s/--set) e `hostname` (sem argumento e sem -b/-F/--file) são leitura: a prova 12
    # do S1 e o nome de arquivo <AAAA-MM-DD> do documentador dependem de `date +%F`. Os ramos que
    # ESCREVEM (date -s, hostname <nome>, hostname -F arquivo) barram antes, em julga_palavras.
    "date", "hostname",
    # 2026-09-24, auditoria da migração: montagens, pacotes e contêineres LXC são lidos, não
    # alterados, por estes. `ss -K` (mata socket) barra à parte, em julga_palavras.
    "findmnt", "dpkg-query", "lxc-ls", "lxc-info", "lsusb", "lspci", "lsmod", "blkid",
}

# Comando de leitura chamado por caminho absoluto (/bin/cat, /usr/bin/grep) vale como o de nome
# curto só nestas pastas: um `cat` em pasta que o agente escreve seria outro programa.
DIRETORIOS_DO_SISTEMA = {"/bin", "/usr/bin", "/usr/local/bin", "/sbin", "/usr/sbin", "/usr/local/sbin"}

PREFIXOS = {"sudo", "doas", "nohup", "time", "command", "builtin", "exec", "nice", "ionice", "timeout",
            "stdbuf", "setsid", "chrt", "taskset", "unbuffer", "env", "flock", "run-heavy-throttled"}
RESERVADAS_QUE_ABREM = {"if", "then", "else", "elif", "do", "while", "until", "!", "{"}
RESERVADAS_QUE_FECHAM = {"fi", "done", "esac", "}", "for", "select", "case", "function", "in"}

GIT_LEITURA = {"status", "log", "show", "diff", "blame", "grep", "ls-files", "ls-tree", "rev-parse",
               "cat-file", "describe", "shortlog", "for-each-ref", "rev-list", "whatchanged", "name-rev",
               "merge-base", "count-objects", "var", "check-ignore", "check-attr", "show-ref",
               "show-branch", "cherry", "range-diff", "annotate", "help", "version"}
SYSTEMCTL_LEITURA = {"status", "show", "is-active", "is-enabled", "is-failed", "list-units", "list-timers",
                     "list-unit-files", "cat", "list-dependencies", "list-sockets", "list-jobs"}
GO_LEITURA = {"list", "env", "version", "doc", "help"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
MOTIVO_OK = ""  # descasca_prefixos devolve isto quando um prefixo já julgou o comando inteiro


def _base(nome: str) -> str:
    return nome.rsplit("/", 1)[-1]


def _eh_atribuicao(valor: str) -> bool:
    return re.match(r"[A-Za-z_][A-Za-z0-9_]*=", valor) is not None


def descasca_prefixos(palavras: list[dict], ctx: Contexto, prof: int) -> tuple[list[dict], str | None]:
    """Tira atribuições (VAR=x) e prefixos que só mudam COMO o comando roda. Se um prefixo traz
    comando próprio (env -S, flock -c), julga-o e devolve ([], motivo-ou-MOTIVO_OK)."""
    resto = list(palavras)
    while resto:
        v = resto[0]["v"]
        if _eh_atribuicao(v):
            resto = resto[1:]
            continue
        base = _base(v)
        if base not in PREFIXOS:
            break
        resto = resto[1:]

        def opcoes(com_argumento: set, para_em=()) -> None:
            nonlocal resto
            while resto and resto[0]["v"].startswith("-") and resto[0]["v"] != "-":
                opcao = resto[0]["v"]
                if opcao in para_em:
                    return
                resto = resto[1:]
                if opcao == "--":
                    return
                if opcao in com_argumento and resto:
                    resto = resto[1:]

        if base in ("sudo", "doas"):
            for p in resto:
                if not p["v"].startswith("-"):
                    break
                if p["v"] in ("-i", "-s", "--login", "--shell"):
                    return [], f"{base} {p['v']} abre um shell"
            opcoes({"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "-T"})
        elif base == "env":
            # -S/--split-string monta um comando a partir de TEXTO, em todas as grafias: `-S x`,
            # `-Sx`, `-S=x`, `-iS x`, `--split-string=x`. Medido: `--split-string=` e `-S=` passavam.
            while resto:
                v2 = resto[0]["v"]
                seguinte = resto[1]["v"] if len(resto) > 1 else ""
                if v2.startswith("--split-string"):
                    texto = v2.split("=", 1)[1] if "=" in v2 else seguinte
                    return [], julga_texto(texto, ctx, prof + 1) or MOTIVO_OK
                if v2.startswith("-") and not v2.startswith("--") and len(v2) > 1:
                    letras = v2[1:]
                    consome = False
                    for pos, letra in enumerate(letras):
                        if letra == "S":
                            texto = letras[pos + 1:] or seguinte
                            return [], julga_texto(texto, ctx, prof + 1) or MOTIVO_OK
                        if letra in ("u", "C"):  # -u NOME, -C DIR: o resto (ou o próximo) é o argumento
                            if letra == "C":
                                ctx.cwd = None
                            consome = pos == len(letras) - 1
                            break
                    resto = resto[2:] if consome else resto[1:]
                    continue
                if v2 in ("--unset", "--chdir") and len(resto) > 1:
                    if v2 == "--chdir":
                        ctx.cwd = None
                    resto = resto[2:]
                    continue
                if v2.startswith("--chdir="):
                    ctx.cwd = None
                if (v2.startswith("-") and v2 != "-") or _eh_atribuicao(v2):
                    resto = resto[1:]
                    continue
                break
        elif base == "nice":
            opcoes({"-n", "--adjustment"})
        elif base == "ionice":
            opcoes({"-c", "-n", "-p", "-P", "-u", "--class", "--classdata"})
        elif base == "timeout":
            opcoes({"-s", "--signal", "-k", "--kill-after"})
            resto = resto[1:]  # a duração
        elif base == "stdbuf":
            opcoes({"-i", "-o", "-e"})
        elif base in ("chrt", "taskset"):
            opcoes(set())
            resto = resto[1:]  # prioridade ou máscara
        elif base == "flock":
            # flock [opções] <trava> -c 'cmd' | flock [opções] <trava> cmd args — a forma que o
            # AGENTS.md manda usar (flock -w 600 /tmp/opt-wiki-agent-heavy.lock ...). A leitura
            # anterior parava no valor de -w e nunca achava o -c: falso positivo medido.
            com_valor = {"-w", "--wait", "--timeout", "-E", "--conflict-exit-code"}
            k = 0
            while k < len(resto) and resto[k]["v"].startswith("-") and resto[k]["v"] != "-":
                if resto[k]["v"] in ("-c", "--command"):
                    return [], "flock -c sem arquivo de trava"
                k += 2 if resto[k]["v"] in com_valor else 1
            if k >= len(resto):
                return [], "flock sem arquivo de trava"
            if not _trava_aceitavel(resto[k], ctx):
                return [], f"flock cria o arquivo de trava {resto[k]['v']} fora de /tmp"
            k += 1
            while k < len(resto) and resto[k]["v"].startswith("-") and resto[k]["v"] != "-":
                if resto[k]["v"] in ("-c", "--command"):
                    if k + 1 >= len(resto):
                        return [], "flock -c sem comando"
                    return [], julga_texto(resto[k + 1]["v"], ctx, prof + 1) or MOTIVO_OK
                k += 2 if resto[k]["v"] in com_valor else 1
            resto = resto[k:]
        elif base == "command":
            if resto and resto[0]["v"] in ("-v", "-V"):
                return [], MOTIVO_OK  # consulta, não execução
            opcoes(set())
        elif base == "exec":
            opcoes({"-a"})
        else:  # nohup, time, builtin, setsid, unbuffer, run-heavy-throttled
            opcoes(set())
    return resto, None


def _julga_curl(args: list[dict], ctx: Contexto) -> str | None:
    saidas_longas = ("--output", "--dump-header", "--cookie-jar", "--trace", "--trace-ascii", "--stderr",
                     "--libcurl", "--etag-save", "--hsts", "--alt-svc", "--output-dir")
    com_argumento = set("oDcXdFTHAeuxKmrwEYyzbCPQtUh")
    i = 0
    while i < len(args):
        v = args[i]["v"]
        proximo = args[i + 1] if i + 1 < len(args) else None
        if v.startswith("--"):
            chave, tem_igual, valor = v.partition("=")
            alvo = _palavra(valor, args[i]) if tem_igual else proximo
            if chave in saidas_longas:
                if alvo is None or (alvo["v"] != "-" and not alvo_permitido(alvo, ctx, chave == "--output-dir")):
                    return f"curl {chave} grava {alvo['v'] if alvo else '(sem alvo)'}"
            elif chave in ("--remote-name", "--remote-name-all", "--remote-header-name"):
                return f"curl {chave} grava arquivo no diretório corrente"
            elif chave == "--request":
                if alvo is None or alvo["v"].upper() not in ("GET", "HEAD", "OPTIONS"):
                    return f"curl --request {alvo['v'] if alvo else '?'} não é leitura"
            elif chave.startswith("--data") or chave in ("--json", "--form", "--form-string", "--upload-file",
                                                         "--config", "--post301", "--post302", "--post303"):
                return f"curl {chave} envia dado ou lê configuração arbitrária"
            i += 1
            continue
        if v.startswith("-") and len(v) > 1:
            letras = v[1:]
            for pos, letra in enumerate(letras):
                if letra in ("O", "J"):
                    return "curl -O/-J grava arquivo no diretório corrente"
                if letra in com_argumento:
                    resto_do_bloco = letras[pos + 1 :]
                    alvo = _palavra(resto_do_bloco, args[i]) if resto_do_bloco else proximo
                    if letra in ("o", "D", "c"):
                        if alvo is None or (alvo["v"] != "-" and not alvo_permitido(alvo, ctx)):
                            return f"curl -{letra} grava {alvo['v'] if alvo else '(sem alvo)'}"
                    elif letra == "X":
                        if alvo is None or alvo["v"].upper() not in ("GET", "HEAD", "OPTIONS"):
                            return f"curl -X {alvo['v'] if alvo else '?'} não é leitura"
                    elif letra in ("d", "F", "T", "K"):
                        return f"curl -{letra} envia dado ou lê configuração arbitrária"
                    if not resto_do_bloco:
                        i += 1
                    break
        i += 1
    return None


def _julga_git(args: list[dict]) -> str | None:
    i = 0
    while i < len(args) and args[i]["v"].startswith("-"):
        opcao = args[i]["v"]
        if opcao == "-c" or opcao.startswith("--config-env") or opcao.startswith("--exec-path"):
            return f"git {opcao} muda configuração em tempo de execução, e configuração pode executar comando"
        i += 1
        if opcao in ("-C", "--git-dir", "--work-tree", "--namespace") and i < len(args):
            i += 1
    if i >= len(args):
        return None
    sub = args[i]["v"]
    resto = [a["v"] for a in args[i + 1 :]]
    perigosos = [r for r in resto if r.startswith("--output") or r in ("-O", "--open-files-in-pager")]
    if perigosos:
        return f"git {sub} {perigosos[0]} grava arquivo ou abre programa"
    if sub in GIT_LEITURA:
        return None
    if sub in ("branch", "tag"):
        return _julga_git_lista(sub, resto)
    if sub == "remote" and (not resto or resto[0] in ("-v", "--verbose", "show", "get-url")):
        return None
    if sub == "config":
        leitura = {"--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin", "--show-scope", "--name-only"}
        escrita = {"--unset", "--unset-all", "--add", "--replace-all", "--rename-section", "--remove-section", "--edit", "-e"}
        if any(r in leitura for r in resto) and not any(r in escrita for r in resto):
            return None
    if sub in ("stash", "notes") and resto and resto[0] in ("list", "show"):
        return None
    if sub == "worktree" and resto and resto[0] == "list":
        return None
    if sub == "reflog" and (not resto or resto[0] == "show"):
        return None
    return f"git {sub} não é leitura — commit, índice e ramo são do orquestrador"


# git branch / git tag por lista de permissão. Um nome posicional CRIA ramo/etiqueta, a menos que
# o modo de LISTA esteja ligado. Medido em git 2.43.0 (RT-B2 M2): só `-l`/`--list`, os filtros e —
# em tag — `-n<N>` ligam a lista. `-v`/`-vv`/`--verbose`/`--sort=`/`--format=` são MODIFICADORES:
# com um nome posicional, `git branch -v b3` e `git tag --sort=x v1` CRIAM a ref. A ordem do dono
# de 2026-09-23 fixou os conjuntos abaixo.
_GIT_IMPLICA_LISTA = {
    "branch": {"-l", "--list", "--contains", "--no-contains", "--points-at", "--merged", "--no-merged"},
    "tag": {"-l", "--list", "--contains", "--points-at"},
}
# Opções aceitas (não escrevem por si), mas que NÃO ligam a lista: com posicional, a ref é criada.
_GIT_LISTA_SEM_VALOR = {
    "branch": {"-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "-q", "--quiet", "--show-current",
               "-l", "--list", "-i", "--ignore-case", "--no-abbrev", "--omit-empty", "--no-color", "--no-column"},
    "tag": {"-l", "--list", "-i", "--ignore-case", "-v", "--verify", "--omit-empty", "--no-color", "--no-column"},
}
_GIT_LISTA_LETRAS = {"branch": set("arvqli"), "tag": set("liv")}
_GIT_FILTROS = {"--contains", "--no-contains", "--merged", "--no-merged", "--points-at"}  # valor opcional
_GIT_COM_VALOR = {"--sort", "--format"}  # consomem valor, mas NÃO ligam a lista
_GIT_VALOR_OPCIONAL_COM_IGUAL = {"--abbrev", "--color", "--column"}


def _julga_git_lista(sub: str, resto: list[str]) -> str | None:
    lista, posicionais, i = False, [], 0
    while i < len(resto):
        v = resto[i]
        if v == "--":
            posicionais.extend(resto[i + 1:])
            break
        if not v.startswith("-") or v == "-":
            posicionais.append(v)
            i += 1
            continue
        chave, tem_igual, _ = v.partition("=")
        if chave in _GIT_IMPLICA_LISTA[sub]:
            lista = True  # -l/--list e os filtros (--contains/--points-at/--merged…) ligam a lista
        elif sub == "tag" and re.fullmatch(r"-n\d*", v):
            lista = True
        elif chave in _GIT_COM_VALOR:
            i += 0 if tem_igual else 1  # --sort/--format consomem o valor; NÃO ligam a lista
        elif v in _GIT_LISTA_SEM_VALOR[sub] or chave in _GIT_VALOR_OPCIONAL_COM_IGUAL:
            pass  # modificador aceito, sem ligar a lista
        elif not v.startswith("--") and set(v[1:]) <= _GIT_LISTA_LETRAS[sub]:
            lista = lista or "l" in set(v[1:])  # só -l liga a lista; -v/-a/-q são modificadores
        else:
            return f"git {sub} {v} altera {'ramo' if sub == 'branch' else 'etiqueta'}"
        i += 1
    if posicionais and not lista:
        return f"git {sub} {posicionais[0]} cria {'ramo' if sub == 'branch' else 'etiqueta'}"
    return None


def _julga_go(args: list[dict]) -> str | None:
    if not args:
        return None
    sub = args[0]["v"]
    if sub not in GO_LEITURA:
        return f"go {sub} compila, testa ou escreve — é da onda de execução (Opus 5.5)"
    if sub == "env" and any(a["v"] in ("-w", "-u") for a in args[1:]):
        return "go env -w/-u grava configuração"
    return None


def _julga_sed(args: list[dict]) -> str | None:
    scripts: list[str] = []
    tem_e = False
    posicionais: list[str] = []
    i = 0
    while i < len(args):
        v = args[i]["v"]
        if v == "--":
            posicionais.extend(a["v"] for a in args[i + 1 :])
            break
        if v.startswith("--"):
            if v.startswith("--in-place") or v.startswith("--file"):
                return f"sed {v.split('=')[0]} edita arquivo ou lê script não conferido"
            if v.startswith("--expression"):
                tem_e = True
                if "=" in v:
                    scripts.append(v.split("=", 1)[1])
                elif i + 1 < len(args):
                    scripts.append(args[i + 1]["v"])
                    i += 1
            i += 1
            continue
        if v.startswith("-") and len(v) > 1:
            letras = v[1:]
            for pos, letra in enumerate(letras):
                if letra == "i":
                    return "sed -i edita arquivo no lugar"
                if letra == "f":
                    return "sed -f lê script não conferido"
                if letra in ("e", "l"):
                    resto_do_bloco = letras[pos + 1 :]
                    if letra == "e":
                        tem_e = True
                        if resto_do_bloco:
                            scripts.append(resto_do_bloco)
                        elif i + 1 < len(args):
                            scripts.append(args[i + 1]["v"])
                            i += 1
                    elif not resto_do_bloco and i + 1 < len(args):
                        i += 1
                    break
            i += 1
            continue
        posicionais.append(v)
        i += 1
    if not tem_e and posicionais:
        scripts.append(posicionais[0])
    if any(a["v"] == "--sandbox" for a in args):
        return None  # --sandbox desliga w, e e r do próprio sed
    for script in scripts:
        if _script_sed_escreve(script):
            return "sed com comando w/W/e (ou bandeira w/e de s///) grava arquivo ou executa"
    return None


def _script_sed_escreve(script: str) -> bool:
    """Lê o script comando a comando, como o GNU sed: endereços N, $, /re/, \\cREc, N~M, e o segundo
    endereço também em +N e ~N; `[...]` dentro de regex protege o delimitador (s/[/]/x/w y grava).
    Medido: `1~2w x`, `/a/,+2w x`, `/a/,~2w x` e `s/[/]/x/w y` passavam pela leitura por regex."""
    i, n = 0, len(script)

    def regex_ate(delimitador: str) -> None:
        nonlocal i
        while i < n:
            c = script[i]
            if c == "\\":
                i += 2
                continue
            if c == "[":
                j = i + 1
                if j < n and script[j] == "^":
                    j += 1
                if j < n and script[j] == "]":
                    j += 1
                while j < n and script[j] != "]":
                    if script[j] == "[" and j + 1 < n and script[j + 1] in ":.=":
                        fecha = script.find(script[j + 1] + "]", j + 2)
                        j = n if fecha < 0 else fecha + 2
                        continue
                    j += 1
                i = j + 1
                continue
            i += 1
            if c == delimitador:
                return
        raise ErroDeAnalise("expressão do sed sem fechamento")

    def texto_ate(delimitador: str) -> None:
        nonlocal i
        while i < n:
            c = script[i]
            i += 2 if c == "\\" else 1
            if c == delimitador:
                return
        raise ErroDeAnalise("substituição do sed sem fechamento")

    def endereco() -> bool:
        nonlocal i
        if i < n and script[i].isdigit():
            while i < n and script[i].isdigit():
                i += 1
            if i < n and script[i] == "~":
                i += 1
                while i < n and script[i].isdigit():
                    i += 1
            return True
        if i < n and script[i] == "$":
            i += 1
            return True
        if i < n and script[i] == "/":
            i += 1
            regex_ate("/")
        elif i + 1 < n and script[i] == "\\":
            delimitador = script[i + 1]
            i += 2
            regex_ate(delimitador)
        else:
            return False
        while i < n and script[i] in "IM":
            i += 1
        return True

    def pula(caracteres: str) -> None:
        nonlocal i
        while i < n and script[i] in caracteres:
            i += 1

    while i < n:
        pula(" \t\n;")
        if i >= n:
            break
        if script[i] == "#":
            quebra = script.find("\n", i)
            i = n if quebra < 0 else quebra
            continue
        if script[i] in "{}":
            i += 1
            continue
        if endereco():
            pula(" \t")
            if i < n and script[i] == ",":
                i += 1
                pula(" \t")
                if i < n and script[i] in "+~":
                    i += 1
                    pula("0123456789")
                else:
                    endereco()
            pula(" \t")
        if i < n and script[i] == "!":
            i += 1
            pula(" \t")
        if i >= n:
            break
        comando = script[i]
        i += 1
        if comando in "wWe":
            return True
        if comando == "s":
            if i >= n:
                raise ErroDeAnalise("s do sed sem delimitador")
            delimitador = script[i]
            i += 1
            regex_ate(delimitador)
            texto_ate(delimitador)
            while i < n and script[i] not in ";\n}":
                if script[i] in "we":
                    return True
                i += 1
            continue
        if comando == "y":
            if i >= n:
                raise ErroDeAnalise("y do sed sem delimitador")
            delimitador = script[i]
            i += 1
            texto_ate(delimitador)
            texto_ate(delimitador)
            continue
        if comando in "aicrR":  # texto (GNU, uma linha) ou arquivo LIDO: vai até o fim da linha
            quebra = script.find("\n", i)
            i = n if quebra < 0 else quebra
            continue
        if comando in "btT:":  # rótulo: até ; ou quebra de linha
            while i < n and script[i] not in ";\n":
                i += 1
            continue
        pula(" \t0123456789")  # comandos de uma letra, com número opcional (q, Q, l, L)
    return False


def _julga_awk(args: list[dict], ctx: Contexto) -> str | None:
    """Opções que gravam (perfil, variáveis, extensão, biblioteca, inplace) barram; o programa —
    posicional, -e/--source, -W source= — passa pelo analisador léxico abaixo."""
    programas: list[str] = []
    posicional = False
    i = 0
    while i < len(args):
        v = args[i]["v"]
        seguinte = args[i + 1]["v"] if i + 1 < len(args) else None
        if v == "--":
            if not programas and not posicional and seguinte is not None:
                programas.append(seguinte)
            break
        # --sandbox/-S/-W sandbox NÃO dispensam a análise do programa: só o gawk os honra. Medido
        # em 2026-09-22 no mawk 1.3.4, `-W sandbox` é "vacuous option" e o programa roda gravando
        # com print > e system(); o awk de Kernighan ignora opção desconhecida com um aviso.
        if v.startswith("--"):
            chave, tem_igual, valor = v.partition("=")
            if chave in ("--file", "--exec", "--include", "--load", "--debug", "--profile", "--pretty-print",
                         "--dump-variables"):
                return f"awk {chave} lê programa não conferido ou grava arquivo"
            if chave == "--source":
                programas.append(valor if tem_igual else (seguinte or ""))
                i += 1 if tem_igual else 2
                continue
            if chave in ("--field-separator", "--assign") and not tem_igual:
                i += 2
                continue
            i += 1
            continue
        if v.startswith("-") and v != "-":
            letra, colado = v[1], v[2:]
            if letra in "fEilopdD":
                return f"awk -{letra} lê programa ou biblioteca não conferidos, ou grava arquivo de perfil"
            if letra == "e":
                programas.append(colado or (seguinte or ""))
                i += 1 if colado else 2
                continue
            if letra == "W":
                opcao = colado or (seguinte or "")
                if opcao.startswith(("source=", "s=")):
                    programas.append(opcao.split("=", 1)[1])
                elif opcao.startswith(("dump", "profile", "pretty", "load", "include", "file", "exec", "debug",
                                       "sprintf", "interactive")):
                    return f"awk -W {opcao} grava arquivo ou lê programa não conferido"
                i += 1 if colado else 2
                continue
            if letra in "Fv":
                i += 1 if colado else 2
                continue
            i += 1
            continue
        if not programas and not posicional:
            programas.append(v)
            posicional = True
        i += 1
    for programa in programas:
        motivo = _programa_awk_escreve(programa, ctx)
        if motivo:
            return motivo
    return None


_AWK_OPERADORES = ("|&", "||", "&&", ">>", ">=", "<=", "==", "!=", "!~", "++", "--", "+=", "-=", "*=", "/=",
                   "%=", "^=", "**")
_AWK_ABREM_REGEX = {"print", "printf", "return", "in", "case", "if", "while", "for", "do", "else", "getline"}


def _tokens_awk(programa: str) -> list[tuple[str, str]]:
    """Tokens: s (string), re (regex), id, num, op, nl, dir (@load/@include)."""
    toks: list[tuple[str, str]] = []
    i, n = 0, len(programa)

    def regex_cabe() -> bool:
        if not toks:
            return True
        tipo, valor = toks[-1]
        if tipo in ("s", "re", "num"):
            return False
        if tipo == "id":
            return valor in _AWK_ABREM_REGEX
        if tipo == "op":
            return valor not in (")", "]", "$", "++", "--")
        return True

    while i < n:
        c = programa[i]
        if c in " \t\r":
            i += 1
            continue
        if c == "\\" and i + 1 < n and programa[i + 1] == "\n":
            i += 2
            continue
        if c == "\n":
            toks.append(("nl", "\n"))
            i += 1
            continue
        if c == "#":
            quebra = programa.find("\n", i)
            i = n if quebra < 0 else quebra
            continue
        if c == '"':
            j, pedacos = i + 1, []
            while j < n and programa[j] != '"':
                if programa[j] == "\\" and j + 1 < n:
                    pedacos.append(programa[j:j + 2])
                    j += 2
                    continue
                pedacos.append(programa[j])
                j += 1
            if j >= n:
                raise ErroDeAnalise("string do awk sem fechamento")
            toks.append(("s", "".join(pedacos)))
            i = j + 1
            continue
        if c == "/" and regex_cabe():
            j = i + 1
            while j < n and programa[j] != "/":
                if programa[j] == "\\":
                    j += 2
                    continue
                if programa[j] == "[":
                    k = j + 1
                    if k < n and programa[k] == "^":
                        k += 1
                    if k < n and programa[k] == "]":
                        k += 1
                    while k < n and programa[k] != "]":
                        k += 1
                    j = k + 1
                    continue
                if programa[j] == "\n":
                    raise ErroDeAnalise("regex do awk sem fechamento")
                j += 1
            if j >= n:
                raise ErroDeAnalise("regex do awk sem fechamento")
            toks.append(("re", programa[i + 1:j]))
            i = j + 1
            continue
        if c == "@":
            m = re.match(r"@\w*", programa[i:])
            toks.append(("dir", m.group(0)))
            i += len(m.group(0))
            continue
        if c.isalpha() or c == "_":
            m = re.match(r"[A-Za-z_]\w*", programa[i:])
            toks.append(("id", m.group(0)))
            i += len(m.group(0))
            continue
        if c.isdigit() or (c == "." and i + 1 < n and programa[i + 1].isdigit()):
            m = re.match(r"[0-9.]+(?:[eE][-+]?\d+)?", programa[i:])
            toks.append(("num", m.group(0)))
            i += len(m.group(0))
            continue
        operador = next((o for o in _AWK_OPERADORES if programa.startswith(o, i)), c)
        toks.append(("op", operador))
        i += len(operador)
    return toks


def _programa_awk_escreve(programa: str, ctx: Contexto) -> str | None:
    """No awk, `>`, `>>`, `|` e `|&` só redirecionam dentro de print/printf, fora de parênteses;
    `>=` e `||` são sempre operadores; `|` antes de getline executa o comando. Medido em
    2026-09-22: `print($1) > "x"` passava, e `print "a|b"`, `print a || b`, `print /a|b/` e
    `print > "/dev/stderr"` eram barrados — a leitura por regex errava para os dois lados."""
    toks = _tokens_awk(programa)
    for k, (tipo, valor) in enumerate(toks):
        if tipo == "dir":
            return f"awk {valor} carrega código"
        if tipo == "id" and valor == "system" and k + 1 < len(toks) and toks[k + 1] == ("op", "("):
            return "awk system() executa comando"
        if tipo == "id" and valor == "getline" and k > 0 and toks[k - 1] in (("op", "|"), ("op", "|&")):
            return "awk comando | getline executa comando"
    k = 0
    while k < len(toks):
        if toks[k] not in (("id", "print"), ("id", "printf")):
            k += 1
            continue
        profundidade, j = 0, k + 1
        while j < len(toks):
            tipo, valor = toks[j]
            if tipo == "nl" or (tipo == "op" and valor in (";", "}") and profundidade == 0):
                break
            if tipo == "op" and valor in ("(", "["):
                profundidade += 1
            elif tipo == "op" and valor in (")", "]"):
                profundidade -= 1
            elif tipo == "op" and valor in (">", ">>", "|", "|&") and profundidade == 0:
                if valor in ("|", "|&"):
                    return "awk print | comando executa comando"
                alvo = toks[j + 1:j + 2]
                depois = toks[j + 2] if j + 2 < len(toks) else ("nl", "\n")
                termina = depois[0] == "nl" or depois in (("op", ";"), ("op", "}"))
                if alvo and alvo[0][0] == "s" and termina:
                    destino = alvo[0][1]
                    if destino in DISPOSITIVOS_LIVRES or destino.startswith("/dev/fd/") \
                            or caminho_permitido(destino, ctx):
                        j += 2
                        break
                    return f"awk print > \"{destino}\""
                return "awk print > destino calculado na execução"
            j += 1
        k = j + 1
    return None


def _julga_sqlite(args: list[dict], heredoc: str | None) -> str | None:
    posicionais = []
    i = 0
    while i < len(args):
        v = args[i]["v"]
        if v == "-init":
            return "sqlite3 -init executa script não conferido"
        if v == "-cmd" and i + 1 < len(args):
            if sql_escreve(args[i + 1]["v"]):
                return "sqlite3 -cmd com comando de escrita"
            i += 2
            continue
        if v in ("-separator", "-newline", "-nullvalue", "-maxsize") and i + 1 < len(args):
            i += 2
            continue
        if v.startswith("-"):
            if v in ("-version", "--version", "-help", "--help"):
                return None
            i += 1
            continue
        posicionais.append(v)
        i += 1
    # Cada ARGUMENTO SQL é uma linha de entrada para a shell do sqlite: junto por \n para que um
    # dot-command num argumento posterior fique no início da linha (o classificador casa por linha).
    sql = "\n".join(posicionais[1:])
    if not sql and heredoc is not None:
        sql = heredoc
    if not sql:
        return "sqlite3 sem SQL na linha de comando lê stdin que a guarda não vê"
    if sql_escreve(sql):
        return "sqlite3 com SQL de escrita"
    return None


# A forma aceita para o agente de contexto: código LITERAL entre aspas simples, só de leitura.
# Código montado na execução — `$VAR`, `$(...)`, crase, heredoc com delimitador SEM aspas — é
# OPACO: a guarda lê o texto literal, mas o shell entrega ao interpretador o valor expandido
# (RT-B2 M1). Como `bash -c "$c"` já é barrado ("nome dinâmico"), iguala-se aqui.
_INTERPRETADOR_DINAMICO = ("com código montado na execução (variável, substituição ou heredoc sem "
                           "aspas) — a guarda só lê código LITERAL entre aspas simples e de leitura")


def _julga_interpretador(nome: str, args: list[dict], heredoc: str | None, ctx: Contexto,
                         heredoc_dyn: bool = False) -> str | None:
    base = _base(nome)
    familia = "python" if base.startswith("python") else ("node" if base in ("node", "nodejs", "deno", "bun") else base)
    codigo = None
    codigo_dyn = False
    i = 0
    while i < len(args) and codigo is None:
        v = args[i]["v"]
        if v == "-" or not v.startswith("-"):
            break
        if v == "--":
            i += 1
            break
        if familia == "python":
            if v in ("-W", "-X"):
                i += 2
                continue
            letras = v[1:] if not v.startswith("--") else ""
            achou = False
            for pos, letra in enumerate(letras):
                if letra == "i":
                    return "python3 -i é interativo"
                if letra in ("c", "m"):
                    colado = letras[pos + 1 :]
                    valor = colado or (args[i + 1]["v"] if i + 1 < len(args) else "")
                    dyn = args[i]["dyn"] if colado else (args[i + 1]["dyn"] if i + 1 < len(args) else False)
                    if letra == "m":
                        return None if valor in ("json.tool", "pydoc", "tokenize", "tabnanny") else f"python3 -m {valor} não é leitura conferida"
                    codigo, codigo_dyn = valor, dyn
                    achou = True
                    break
            if achou:
                break
            i += 1
            continue
        if familia == "node":
            if v in ("-e", "--eval", "-p", "--print") and i + 1 < len(args):
                codigo, codigo_dyn = args[i + 1]["v"], args[i + 1]["dyn"]
                break
            i += 1
            continue
        # perl e ruby: aglomerados como -lne, -pi, -MList::Util=sum
        if v.startswith("--"):
            i += 1
            continue
        letras = v[1:]
        for pos, letra in enumerate(letras):
            if letra == "i":
                return f"{base} -i edita arquivo no lugar"
            if letra == "x":
                return f"{base} -x lê programa embutido em arquivo"
            if letra in ("e", "E"):
                colado = letras[pos + 1 :]
                codigo = colado or (args[i + 1]["v"] if i + 1 < len(args) else "")
                codigo_dyn = args[i]["dyn"] if colado else (args[i + 1]["dyn"] if i + 1 < len(args) else False)
                break
            if letra in "MmIF0lCdDVrW":
                break  # o resto do aglomerado é argumento da opção
        i += 1
    if codigo is not None and codigo_dyn:
        return f"{base} {_INTERPRETADOR_DINAMICO}"
    if codigo is None:
        posicionais = [a["v"] for a in args[i:]]
        if not posicionais or posicionais[0] == "-":
            if heredoc is None:
                return f"{base} lendo código do stdin que a guarda não vê — use -c/-e ou heredoc"
            if heredoc_dyn:
                return f"{base} {_INTERPRETADOR_DINAMICO}"
            codigo = heredoc
        else:
            script = os.path.expanduser(posicionais[0])
            if ctx.cwd is not None and not os.path.isabs(script):
                script = os.path.join(ctx.cwd, script)
            real = os.path.realpath(script)
            ferramentas = os.path.join(ctx.raiz, "tools") + os.sep
            if familia == "python" and real.startswith(ferramentas) and re.match(r"check[-_]", os.path.basename(real)):
                return None
            return f"{base} {posicionais[0]} executa script — a guarda só lê código embutido; tools/check-* é a exceção"
    motivo = codigo_escreve(codigo, familia)
    return f"{base} com {motivo}" if motivo else None


def _julga_saida_em_argumento(base: str, args: list[dict], ctx: Contexto) -> str | None:
    """tee, mkdir e touch escrevem nos argumentos: todos têm de cair num destino permitido."""
    com_argumento = {"mkdir": {"-m", "--mode", "--context"},
                     "touch": {"-d", "--date", "-r", "--reference", "-t", "--time"},
                     "tee": set()}[base]
    alvos = []
    i = 0
    while i < len(args):
        v = args[i]["v"]
        if v == "--":
            alvos.extend(args[i + 1 :])
            break
        if v.startswith("-") and v != "-":
            i += 2 if v in com_argumento else 1
            continue
        alvos.append(args[i])
        i += 1
    for alvo in alvos:
        if base == "tee" and alvo["v"] == "-":
            continue
        if not alvo_permitido(alvo, ctx, aceita_a_base=(base == "mkdir")):
            return f"{base} grava {alvo['v']}"
    return None


# Opções curtas que levam valor, por comando: o valor colado ou o próximo argumento não é arquivo.
_SAIDA_EM_OPCAO = {
    "sort": {"curtas_com_valor": set("ktST"), "longas_com_valor": {"--key", "--field-separator", "--buffer-size",
             "--temporary-directory", "--parallel", "--files0-from", "--random-source", "--batch-size", "--sort"}},
    "iconv": {"curtas_com_valor": set("ft"), "longas_com_valor": {"--from-code", "--to-code"}},
}


def _julga_saida_em_opcao(base: str, args: list[dict], ctx: Contexto) -> str | None:
    """sort -o/--output e iconv -o/--output, em todas as grafias (-o x, -ox, -o=x, -uo x,
    --output=x). MEDIDO: `sort -o -` cria um arquivo chamado `-`; `iconv -o -` escreve na saída
    padrão. sort --compress-program executa um programa."""
    regras = _SAIDA_EM_OPCAO[base]
    alvos: list[dict | None] = []
    i = 0
    while i < len(args):
        v = args[i]["v"]
        seguinte = args[i + 1] if i + 1 < len(args) else None
        if v == "--":
            break
        if v.startswith("--"):
            chave, tem_igual, valor = v.partition("=")
            if chave == "--compress-program":
                return f"{base} --compress-program executa programa"
            if chave == "--output":
                alvos.append(_palavra(valor, args[i]) if tem_igual else seguinte)
                i += 1 if tem_igual else 2
                continue
            i += 1 if (tem_igual or chave not in regras["longas_com_valor"]) else 2
            continue
        if v.startswith("-") and v != "-":
            letras, consome = v[1:], False
            for pos, letra in enumerate(letras):
                if letra == "o":
                    resto = letras[pos + 1:]
                    alvos.append(_palavra(resto, args[i]) if resto else seguinte)
                    consome = not resto
                    break
                if letra in regras["curtas_com_valor"]:
                    consome = pos == len(letras) - 1
                    break
            i += 2 if consome else 1
            continue
        i += 1
    for alvo in alvos:
        if alvo is None:
            return f"{base} -o sem destino"
        if base == "iconv" and alvo["v"] == "-" and not alvo["dyn"]:
            continue
        if not alvo_permitido(alvo, ctx):
            return f"{base} -o grava {alvo['v']}"
    return None


def _julga_uniq(args: list[dict], ctx: Contexto) -> str | None:
    """uniq [OPÇÃO] [ENTRADA [SAÍDA]]: -f/-s/-w levam número (medido: o número virava "saída").
    SAÍDA `-` é a saída padrão (medido)."""
    com_valor_longo = {"--skip-fields", "--skip-chars", "--check-chars"}
    posicionais: list[dict] = []
    i = 0
    while i < len(args):
        v = args[i]["v"]
        if v == "--":
            posicionais.extend(args[i + 1:])
            break
        if v.startswith("--"):
            i += 2 if v in com_valor_longo else 1
            continue
        if v.startswith("-") and v != "-":
            letras, consome = v[1:], False
            for pos, letra in enumerate(letras):
                if letra in "fsw":
                    consome = pos == len(letras) - 1
                    break
            i += 2 if consome else 1
            continue
        posicionais.append(args[i])
        i += 1
    if len(posicionais) >= 2:
        saida = posicionais[1]
        if not (saida["v"] == "-" and not saida["dyn"]) and not alvo_permitido(saida, ctx):
            return f"uniq grava {saida['v']}"
    return None


def _julga_find(args: list[dict], ctx: Contexto, prof: int) -> str | None:
    i = 0
    while i < len(args):
        v = args[i]["v"]
        if v in ("-delete", "-fprint", "-fprint0", "-fprintf", "-fls"):
            return f"find {v} apaga ou grava arquivo"
        if v in ("-exec", "-execdir", "-ok", "-okdir"):
            j = i + 1
            interno = []
            while j < len(args) and args[j]["v"] not in (";", "+"):
                interno.append(args[j])
                j += 1
            motivo = julga_palavras(interno, [], ctx, prof + 1)
            if motivo:
                return f"find {v}: {motivo}"
            i = j + 1
            continue
        i += 1
    return None


def _julga_xargs(args: list[dict], ctx: Contexto, prof: int) -> str | None:
    com_argumento = {"-n", "-L", "-l", "-P", "-s", "-d", "-E", "-e", "-I", "-a", "--max-args", "--max-lines",
                     "--max-procs", "--max-chars", "--delimiter", "--eof", "--replace", "--arg-file"}
    i = 0
    while i < len(args) and args[i]["v"].startswith("-"):
        i += 2 if args[i]["v"] in com_argumento else 1
    return julga_palavras(args[i:], [], ctx, prof + 1) if i < len(args) else None


def _julga_shell(nome: str, args: list[dict], heredoc: str | None, ctx: Contexto, prof: int) -> str | None:
    for i, a in enumerate(args):
        v = a["v"]
        if v.startswith("-") and not v.startswith("--") and "c" in v[1:] and i + 1 < len(args):
            return julga_texto(args[i + 1]["v"], ctx.copia(), prof + 1)
        if v == "-n":
            return None  # só confere sintaxe
        if v.startswith("-"):
            continue
        return f"{_base(nome)} {v} executa script — rode o comando de leitura diretamente"
    if heredoc is not None:
        return julga_texto(heredoc, ctx.copia(), prof + 1)
    return f"{_base(nome)} lendo comandos do stdin que a guarda não vê"


def _atualiza_cwd(nome: str, args: list[dict], ctx: Contexto) -> None:
    if nome == "popd":
        ctx.cwd = None
        return
    posicionais = [a for a in args if not a["v"].startswith("-") or a["v"] == "-"]
    if not posicionais:
        ctx.cwd = os.path.expanduser("~") if nome == "cd" else ctx.cwd
        return
    destino = posicionais[0]
    if destino["dyn"] or destino["v"] == "-":
        ctx.cwd = None
        return
    alvo = os.path.expanduser(destino["v"])
    if os.path.isabs(alvo):
        ctx.cwd = os.path.normpath(alvo)
    elif ctx.cwd is not None:
        ctx.cwd = os.path.normpath(os.path.join(ctx.cwd, alvo))


def julga_palavras(palavras: list[dict], redirs: list, ctx: Contexto, prof: int) -> str | None:
    if prof > PROFUNDIDADE_MAXIMA:
        return "aninhamento de comandos fundo demais para conferir"
    resto, motivo = descasca_prefixos(palavras, ctx, prof)
    if motivo is not None:
        return motivo or None
    while resto and resto[0]["v"] in RESERVADAS_QUE_ABREM and not resto[0]["q"]:
        resto = resto[1:]
    heredoc = None
    heredoc_dyn = False
    for r, _ in redirs:
        if r["v"] in ("<<", "<<-") and "corpo" in r:
            heredoc = r["corpo"]
            # Delimitador SEM aspas e corpo com $ ou crase: o shell expande antes de alimentar o
            # interpretador — código opaco (RT-B2 M1).
            heredoc_dyn = (not r.get("delim_q", False)) and bool(re.search(r"[$`]", r["corpo"]))
            break

    # `>` dentro de [[ ]] é comparação de texto, não redirecionamento.
    if not (resto and resto[0]["v"] == "[["):
        for r, alvo in redirs:
            operador = r["v"]
            if operador in ("<", "<<", "<<-", "<<<", "<&"):
                continue
            if operador == ">&" and alvo is not None and (alvo["v"].isdigit() or alvo["v"] == "-"):
                continue
            if not alvo_permitido(alvo, ctx):
                return f"redirecionamento {r['fd']}{operador} para {alvo['v'] if alvo else '(sem alvo)'}"

    if not resto:
        return None
    nome = resto[0]["v"]
    args = resto[1:]
    base = _base(nome)
    if resto[0]["dyn"]:
        return f"nome de comando dinâmico ({nome})"
    if nome in RESERVADAS_QUE_FECHAM:
        return None
    if nome in ("cd", "pushd", "popd"):
        _atualiza_cwd(nome, args, ctx)
        return None
    if nome in ("source", ".", "alias"):
        return f"{nome} executa ou redefine comando que a guarda não vê"
    if nome == "eval":
        return julga_texto(" ".join(a["v"] for a in args), ctx, prof + 1)
    if nome == "trap":
        if args and not args[0]["v"].startswith("-") and args[0]["v"] not in ("", "-"):
            return julga_texto(args[0]["v"], ctx.copia(), prof + 1)
        return None
    if nome == "date" and any(a["v"] in ("-s", "--set") or a["v"].startswith("--set=") for a in args):
        return "date -s altera o relógio"
    if nome == "hostname" and any(not a["v"].startswith("-") or a["v"] in ("-b", "-F", "--file")
                                  or a["v"].startswith("--file=") for a in args):
        return "hostname com argumento (ou -b/-F/--file) altera o nome da máquina"
    if base == "ss" and any(a["v"] in ("-K", "--kill") or (a["v"].startswith("-") and not a["v"].startswith("--")
                                                          and "K" in a["v"]) for a in args):
        return "ss -K derruba conexão"
    if nome in LEITURA_PURA or (base in LEITURA_PURA and os.path.dirname(os.path.normpath(nome)) in DIRETORIOS_DO_SISTEMA):
        return None
    if base == "ssh":
        return _julga_ssh(args, ctx, prof)
    if base in SUBCOMANDOS_DE_LEITURA or base in ("dpkg", "crontab", "ip"):
        return _julga_leitura_de_sistema(base, args)
    if base in ("sort", "iconv"):
        return _julga_saida_em_opcao(base, args, ctx)
    if base == "uniq":
        return _julga_uniq(args, ctx)
    if base in ("tee", "mkdir", "touch"):
        return _julga_saida_em_argumento(base, args, ctx)
    if base in ("awk", "gawk", "mawk", "nawk"):
        return _julga_awk(args, ctx)
    if base == "sed":
        return _julga_sed(args)
    if base == "find":
        return _julga_find(args, ctx, prof)
    if base == "xargs":
        return _julga_xargs(args, ctx, prof)
    if base == "watch":
        k = 0
        while k < len(args) and args[k]["v"].startswith("-"):
            k += 2 if args[k]["v"] in ("-n", "--interval") else 1
        return julga_texto(" ".join(a["v"] for a in args[k:]), ctx.copia(), prof + 1) if k < len(args) else None
    if base == "git":
        return _julga_git(args)
    if base in ("go", "go-modern"):
        return _julga_go(args)
    if base.startswith("check-") and "tools/" in nome:
        return None  # convenção da casa: tools/check-* é somente leitura; tools/generate-* escreve
    if base == "curl":
        return _julga_curl(args, ctx)
    if base == "sqlite3":
        return _julga_sqlite(args, heredoc)
    if base == "systemctl":
        subcomandos = [a["v"] for a in args if not a["v"].startswith("-")]
        if not subcomandos or subcomandos[0] in SYSTEMCTL_LEITURA:
            return None
        return f"systemctl {subcomandos[0]} altera serviço"
    if base == "journalctl":
        for a in args:
            chave = a["v"].split("=", 1)[0]
            if chave in ("--vacuum-size", "--vacuum-time", "--vacuum-files", "--rotate", "--flush", "--sync",
                         "--relinquish-var", "--smart-relinquish-var", "--setup-keys", "--update-catalog"):
                return f"journalctl {chave} altera o journal"
        return None
    if base == "ollama":
        if not args or args[0]["v"] in ("list", "ls", "ps", "show", "-v", "--version", "help", "--help"):
            return None
        return f"ollama {args[0]['v']} altera ou roda modelo"
    if base in SHELLS:
        return _julga_shell(nome, args, heredoc, ctx, prof)
    if base.startswith("python") or base in ("node", "nodejs", "deno", "bun", "perl", "ruby"):
        return _julga_interpretador(nome, args, heredoc, ctx, heredoc_dyn)
    return f"{nome} não está na lista de leitura do colhedor de contexto"


# ---------------------------------------------------------------------------------------------
# ssh e as leituras de sistema da auditoria da migração (2026-09-24).
# ---------------------------------------------------------------------------------------------
# O colhedor precisa MEDIR a outra máquina (a torre, desde o cutover de 2026-09-24), e barrar
# `ssh` inteiro o deixava cego do lado que mais importa: seis agentes de uma onda devolveram mapas
# só com o lado do notebook. A regra: o COMANDO REMOTO passa pela mesma lista de leitura, num
# contexto remoto em que nenhum destino de escrita é permitido; túnel, sessão sem comando, comando
# LOCAL disparado pelo ssh (ProxyCommand, LocalCommand...) e arquivo local de log barram.
SSH_OPCOES_COM_VALOR = set("BbcDEeFIiJLlmOoPpQRSWw")
SSH_LETRAS_PROIBIDAS = {
    "L": "encaminha porta", "R": "encaminha porta", "D": "abre proxy", "W": "encaminha stdio",
    "w": "abre túnel de rede", "O": "controla sessão mestre", "M": "abre sessão mestre",
    "N": "não roda comando (só túnel)", "f": "vai para o fundo", "S": "usa socket de controle",
}
SSH_CHAVES_PROIBIDAS = {
    "proxycommand", "localcommand", "permitlocalcommand", "knownhostscommand", "localforward",
    "remoteforward", "dynamicforward", "controlmaster", "controlpath", "controlpersist", "tunnel",
    "tunneldevice", "proxyjump", "stdioforward", "sessiontype", "remotecommand",
}


def _julga_ssh(args: list[dict], ctx: Contexto, prof: int) -> str | None:
    k = 0
    while k < len(args):
        palavra = args[k]
        v = palavra["v"]
        if v == "--":
            k += 1
            break
        if not v.startswith("-") or v == "-":
            break
        if palavra["dyn"]:
            return f"opção dinâmica no ssh ({v})"
        letras = v[1:]
        pula_valor = False
        for idx, letra in enumerate(letras):
            if letra in SSH_LETRAS_PROIBIDAS:
                return f"ssh -{letra} {SSH_LETRAS_PROIBIDAS[letra]}"
            if letra in SSH_OPCOES_COM_VALOR:
                valor_colado = letras[idx + 1:]
                valor = valor_colado if valor_colado else (args[k + 1]["v"] if k + 1 < len(args) else "")
                if not valor_colado:
                    if k + 1 >= len(args) or args[k + 1]["dyn"]:
                        return f"ssh -{letra} sem valor fixo"
                    pula_valor = True
                if letra == "o":
                    chave = re.split(r"[=\s]", valor.strip(), maxsplit=1)[0].lower()
                    if chave in SSH_CHAVES_PROIBIDAS:
                        return f"ssh -o {chave} dispara comando local, túnel ou sessão mestre"
                if letra == "E":
                    return "ssh -E grava log em arquivo local"
                break
        k += 2 if pula_valor else 1
    if k >= len(args):
        return "ssh sem destino"
    if args[k]["dyn"]:
        return f"destino dinâmico no ssh ({args[k]['v']})"
    remoto = args[k + 1:]
    if not remoto:
        return "ssh sem comando remoto abre shell interativo"
    ctx_remoto = ctx.copia()
    ctx_remoto.remoto = True
    ctx_remoto.cwd = None
    motivo = julga_texto(" ".join(a["v"] for a in remoto), ctx_remoto, prof + 1)
    return f"no comando remoto do ssh: {motivo}" if motivo else None


def _primeiro_nao_opcao(args: list[dict], com_valor: set[str] = frozenset()) -> tuple[str | None, int]:
    """Primeira palavra que não é opção (pulando o valor das opções de `com_valor`)."""
    k = 0
    while k < len(args):
        v = args[k]["v"]
        if v.startswith("-") and v != "-":
            k += 2 if v in com_valor else 1
            continue
        return v, k
    return None, k


# Subcomando de leitura por ferramenta: o primeiro argumento que não é opção tem de estar aqui.
SUBCOMANDOS_DE_LEITURA = {
    "virsh": ({"list", "net-list", "pool-list", "vol-list", "dominfo", "domblklist", "domiflist",
               "domstate", "net-info", "net-dumpxml", "dumpxml", "nodeinfo", "version", "capabilities",
               "pool-info", "vol-info", "snapshot-list", "uri", "hostname", "net-dhcp-leases"},
              {"-c", "--connect", "-l", "--log", "-k", "--keepalive-interval", "-K", "--keepalive-count"}),
    "docker": ({"ps", "images", "volume", "network", "inspect", "info", "version", "compose",
                "container", "image", "system", "logs", "stats"}, {"-H", "--host", "--context", "-c"}),
    "podman": ({"ps", "images", "volume", "network", "inspect", "info", "version", "container",
                "image", "system", "logs"}, set()),
    "snap": ({"list", "info", "version", "services", "connections", "changes"}, set()),
    "flatpak": ({"list", "info", "remotes", "remote-ls", "history"}, set()),
    "npm": ({"ls", "list", "view", "info", "root", "prefix", "config", "outdated", "explain"}, set()),
    "pipx": ({"list", "environment"}, set()),
    "apt-mark": ({"showmanual", "showauto", "showhold", "showinstall", "showremove", "showpurge"}, set()),
    "apt-cache": ({"policy", "show", "showpkg", "depends", "rdepends", "search", "madison", "pkgnames",
                   "stats", "showsrc"}, set()),
    "apt": ({"list", "show", "policy", "search", "depends", "rdepends"}, set()),
    "loginctl": ({"list-sessions", "list-users", "list-seats", "show-session", "show-user", "show-seat",
                  "session-status", "user-status", "seat-status"}, set()),
}
# Segundo nível para quem agrupa: `docker volume ls`, `npm config get`, `docker compose ps`.
SEGUNDO_NIVEL_DE_LEITURA = {"ls", "list", "inspect", "get", "ps", "df", "info", "images", "top", "config"}
DPKG_ACOES_DE_LEITURA = {"-l", "--list", "-L", "--listfiles", "-S", "--search", "-s", "--status",
                         "-p", "--print-avail", "-V", "--verify", "--get-selections", "--print-architecture",
                         "--print-foreign-architectures", "--audit", "-C", "--compare-versions",
                         "--version", "--help", "--robot"}
IP_VERBOS_DE_ESCRITA = {"add", "del", "delete", "set", "change", "replace", "flush", "append", "prepend",
                        "exec", "save", "restore", "update", "attach", "detach"}


def _julga_leitura_de_sistema(base: str, args: list[dict]) -> str | None:
    if base == "dpkg":
        acoes = [a["v"] for a in args if a["v"].startswith("-")]
        if acoes and all(v.split("=", 1)[0] in DPKG_ACOES_DE_LEITURA or v in ("-W",) for v in acoes[:1]):
            return None
        return f"dpkg {acoes[0] if acoes else '(sem ação)'} altera pacote"
    if base == "crontab":
        valores = [a["v"] for a in args]
        if "-l" in valores and not any(v in ("-r", "-e", "-i") for v in valores):
            return None
        return "crontab sem -l substitui ou edita a tabela"
    if base == "ip":
        if any(a["v"] in IP_VERBOS_DE_ESCRITA for a in args):
            return "ip com verbo de escrita altera a rede"
        return None
    permitidos, com_valor = SUBCOMANDOS_DE_LEITURA[base]
    sub, k = _primeiro_nao_opcao(args, com_valor)
    if sub is None:
        if all(a["v"] in ("--version", "-v", "-V", "--help", "-h") for a in args):
            return None
        return f"{base} sem subcomando de leitura"
    if sub not in permitidos:
        return f"{base} {sub} não é leitura"
    if base in ("docker", "podman", "npm") and sub in ("volume", "network", "container", "image", "system",
                                                      "compose", "config"):
        segundo, _ = _primeiro_nao_opcao(args[k + 1:])
        if segundo not in SEGUNDO_NIVEL_DE_LEITURA:
            return f"{base} {sub} {segundo or ''} não é leitura".rstrip()
    return None


def julga_texto(texto: str, ctx: Contexto, prof: int) -> str | None:
    """Julga uma linha de comando inteira: substituições primeiro (rodam antes), depois cada
    comando simples na ordem, acompanhando `cd`."""
    if prof > PROFUNDIDADE_MAXIMA:
        return "aninhamento de comandos fundo demais para conferir"
    toks, subs = tokeniza(texto)
    for interno in subs:
        motivo = julga_texto(interno, ctx.copia(), prof + 1)
        if motivo:
            return motivo
    esperando_padrao = False
    for comando in comandos_simples(toks):
        palavras = comando["palavras"]
        if esperando_padrao and comando["fim"] == ")":
            esperando_padrao = False
            continue  # padrão de `case`: não executa
        primeira = palavras[0]["v"] if palavras else ""
        if primeira == "case":
            esperando_padrao = comando["fim"] != ")"
            continue
        if primeira == "esac":
            esperando_padrao = False
        motivo = julga_palavras(palavras, comando["redirs"], ctx, prof)
        if motivo:
            return motivo
        if comando["fim"] in (";;", ";&", ";;&"):
            esperando_padrao = True
    return None


# ---------------------------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------------------------


def julga_payload(dados: dict, modo: str, raiz: str, restritos: set) -> tuple[str, str | None]:
    agente = dados.get("agent_type") if isinstance(dados.get("agent_type"), str) else ""
    if modo != "sempre" and agente not in restritos:
        return agente, None
    agente = agente or "documentador-de-contexto"
    ferramenta = dados.get("tool_name") or ""
    entrada = dados.get("tool_input") if isinstance(dados.get("tool_input"), dict) else {}
    cwd = dados.get("cwd")
    cwd = cwd if isinstance(cwd, str) and os.path.isabs(cwd) else raiz
    scratchpad = dados.get("scratchpad_dir") if isinstance(dados.get("scratchpad_dir"), str) else None
    ctx = Contexto(raiz, agente, cwd, scratchpad)
    if ferramenta in FERRAMENTAS_DE_ARQUIVO:
        caminho = (entrada.get("notebook_path") if ferramenta == "NotebookEdit" else None) or entrada.get("file_path")
        if not isinstance(caminho, str) or not caminho.strip():
            return agente, f"{ferramenta} sem caminho de arquivo — o destino não pode ser conferido"
        return agente, None if caminho_permitido(caminho, ctx) else f"{ferramenta} em {caminho}"
    if ferramenta in ("Bash", "PowerShell"):
        comando = entrada.get("command")
        if not isinstance(comando, str):
            return agente, "Bash sem comando legível"
        try:
            return agente, julga_texto(comando, ctx, 0)
        except ErroDeAnalise as erro:
            return agente, f"comando que a guarda não consegue ler com segurança ({erro})"
    return agente, None


def main(argv: list) -> int:
    if len(argv) < 3:
        print("ILEGIVEL")
        return 0
    modo, raiz, restritos = argv[1], argv[2], set(argv[3:])
    try:
        dados = json.loads(sys.stdin.read())
    except (ValueError, UnicodeDecodeError):
        print("ILEGIVEL")
        return 0
    if not isinstance(dados, dict):
        print("ILEGIVEL")
        return 0
    agente, motivo = julga_payload(dados, modo, raiz, restritos)
    print("BLOQUEIA\t" + agente + "\t" + " ".join(motivo.split()) if motivo else "PASSA")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
