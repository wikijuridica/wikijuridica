#!/usr/bin/env python3
"""strip-heredoc-body — remove do payload o corpo de heredoc QUOTED, que não executa.

Auxiliar de três chamadores, todos em `.claude/hooks/`:
  * `block-heavy-go.sh`, sobre o envelope JSON cru do hook;
  * `lib/bloqueio.sh` (`le_payload`), sobre o valor de "command" ainda escapado — é por
    ele que passam `block-display-zero-social.sh` e os demais hooks que usam `le_payload`;
  * `block-git-add-com-commit.sh`, com `--so-shell` (ver abaixo).
Lê o texto na entrada padrão e devolve o mesmo texto sem o CORPO dos heredocs quoted,
para que a detecção não confunda DADO com EXECUÇÃO. Fora dos corpos removidos, a saída
é, byte a byte, a entrada.

★ POR QUE EXISTE (2026-08-19)

`block-heavy-go.sh` ancora a detecção em "posição de comando", e crase entra nessa
âncora porque crase é substituição de comando em shell. Só que markdown usa crase para
código inline — então documentar um comando pesado passou a ser bloqueado como se fosse
executá-lo. Aconteceu duas vezes na mesma sessão: primeiro ao escrever uma skill cujo
texto ensinava a NÃO rodar comando full-tree, depois ao escrever a própria correção do
hook. Um guarda que impede de escrever a regra que ele aplica trabalha contra si.

★ POR QUE ISTO NÃO AFROUXA O GUARDA

Num heredoc com delimitador entre aspas (`<<'FIM'` ou `<<"FIM"`), o shell não expande
nem executa nada: o corpo é dado a caminho de um arquivo. Removê-lo da análise não abre
buraco — o resto do payload segue avaliado exatamente como antes.

A exceção que fecha a evasão óbvia: se o heredoc alimenta um INTERPRETADOR (bash, sh,
python, node...), o corpo É executado. Nesses casos o corpo fica onde está e continua
sujeito à detecção. Com `--so-shell`, só o corpo que alimenta SHELL fica: o de python,
perl, node etc. é código de outra linguagem, onde "posição de comando de shell" não
existe — é o modo do guarda de `git add` + `git commit`, que só procura comando de shell.

★ DEFEITOS MEDIDOS EM 2026-09-23 (bancada: strip-heredoc-body.test.py)

1. FRONTEIRA À ESQUERDA. A regex do interpretador não tinha fronteira à esquerda e
   casava qualquer palavra TERMINADA em sh, bash, python3, node...: em
   `cat > /opt/wiki/ops/terminal/testa-terminal.sh <<'EOF'` o `sh` de `.sh` virou
   interpretador, o corpo (um script que só CITA o display :0) ficou sob análise e
   `block-display-zero-social.sh` barrou a escrita do arquivo (exit 2; com destino
   `/tmp/x`, exit 0). O mesmo acaso reconhecia `dash`, `ssh`, `fish`, `pwsh` e
   `ts-node` — agora eles estão na lista pelo nome. A fronteira sugerida no conserto,
   `(?<![\\w./-])`, teria aberto buraco: `/bin/bash` (barra antes) e o `bash` da linha
   de baixo (no JSON a quebra é `\\n`, e o `n` é letra) deixariam de ser reconhecidos, e
   o corpo executado sairia da análise. Por isso a fronteira é POSITIVA: início, espaço,
   operador, aspa, `/` de caminho, `=`, ou o `\\n`/`\\t` do JSON.
2. FECHAMENTO EM LINHA PRÓPRIA. `texto.find(delimitador)` não era ancorado em linha: um
   `EOF` dentro de `GEOFF` encerrava o corpo cedo e o resto do corpo voltava à análise.
   O fechamento agora é o delimitador sozinho na linha (com TABs à frente só em `<<-`),
   seguido de quebra de linha, fim do texto, fim da string JSON ou `)` — o bash 5.2
   aceita `EOF)` dentro de `$(...)`, e reconhecer fechamento a MAIS só corta menos.
3. O CORTE COMEÇA NO FIM DA LINHA DE ABERTURA, não logo depois de `<<'EOF'`. O resto
   daquela linha é comando: com o corte antigo, `cat > x <<'EOF' && DISPLAY=:0 xdotool
   key a` passava pelo guarda do display (exit 0) — falso NEGATIVO.
4. UMA PASSADA, SEM SOBREPOSIÇÃO. As aberturas eram cortadas por deslocamento sobre o
   texto original; uma abertura DENTRO de um corpo já cortado dava índice negativo e o
   Python fatiava a CAUDA do payload: `xdotool key a` virava `xdotooy a` (exit 0 no guarda
   do display, em 80 de 400 combinações de tamanho medidas). Agora a busca recomeça
   depois do fechamento.
5. JANELA DO INTERPRETADOR. A janela entre o nome e o `<<` parava em `&`, então
   `bash 2>&1 <<'EOF'` não era reconhecido (falso negativo); e atravessava a quebra de
   linha do JSON, então `python3 x.py` numa linha fazia o `cat > doc <<'EOF'` da linha
   seguinte parecer alimentar o python (falso positivo). Agora `>&`, `<&` e `&>` passam,
   e a janela para na quebra de linha — salvo na continuação `\\` + quebra.
6. ABERTURA DENTRO DE ASPAS OU DE COMENTÁRIO não abre heredoc: `echo "use <<'EOF'"`
   não tem corpo, e tratá-la como abertura escondia os comandos até o próximo `EOF`.
   `<<<` (here-string) também não é heredoc.
7. HEREDOC QUE VAI PARA SHELL PELA CAUDA DA LINHA. `cat <<'EOF' | bash`, `| sh -s`,
   `| sudo bash`, `cat <<'EOF' > s.sh && bash s.sh` e `tee s.sh <<'EOF'; bash s.sh`
   executam o corpo, mas o dono do `<<` é o `cat`/`tee`: o corpo saía da análise nos três
   chamadores (medido: exit 0 com `git add && git commit`, `go test ./...` e `xdotool` no
   `:0` dentro do corpo). Agora a cauda da linha lógica de abertura é lida: pipe para
   interpretador, ou arquivo escrito pelo heredoc e executado na mesma linha (por
   interpretador, `source`, `.` ou `./arquivo`; `bash -n`, que só confere a sintaxe, não
   conta), mantém o corpo. LIMITE DECLARADO:
   `cat > s.sh <<'EOF'` … `EOF` e `bash s.sh` numa linha SEGUINTE não é visto — é um script,
   e o auxiliar lê um comando, não a sequência.
8. TETO FAIL-SAFE DE CUSTO. A leitura de aspas refazia a linha inteira a cada abertura, e o
   fechamento varria as linhas a cada abertura: medido, 60 aberturas numa linha de 60 KB
   custavam 264 ms e 120 numa de 80 KB, 687 ms (a refutação mediu 56,5 s com 300 × 80 KB,
   além do timeout de 5 s do hook, que falha ABERTO). A leitura agora é incremental na
   linha e o fechamento sai de um índice montado uma vez; e acima de 32 aberturas na mesma
   linha, ou de 200 ms de trabalho, o texto volta INTACTO — barra a mais, nunca a menos.

Falha em silêncio (devolve o payload intacto) diante de qualquer erro: o hook é
fail-open por contrato, e um auxiliar que quebrasse a análise seria pior que o falso
positivo que ele corrige. Roda sob `python3 -I` e só usa a biblioteca padrão.
"""

from __future__ import annotations

import bisect
import re
import sys
import time

# ---------------------------------------------------------------------------
# QUEM EXECUTA O CORPO. Lista explícita (defeito 1): quem antes só era reconhecido por
# acaso de sufixo entra pelo nome.
_SHELLS = (
    r"bash|sh|dash|zsh|ksh|mksh|pdksh|ash|yash|fish|csh|tcsh|rbash|busybox|pwsh|tclsh"
    r"|ssh|rsh|autossh|source|eval|\.(?=\s)|\$\{?(?:SHELL|BASH)\}?"
)
_OUTROS = (
    r"python[0-9.]*|ipython[0-9.]*|pypy[0-9.]*|perl|ruby|jruby|node|nodejs|ts-node"
    r"|deno|bun|tsx|php|lua|luajit"
)
# Fronteira à esquerda, POSITIVA: início, espaço, operador, parêntese, chave, crase, aspa,
# `/` de caminho (`/usr/bin/python3`), `=` (`--shell=bash`) ou a quebra de linha e o TAB
# escritos como `\n` e `\t` no JSON. Letra, dígito, `.`, `-` e `_` não são fronteira:
# `notas.sh`, `gera-sh` e `mybash` não são interpretador.
_ESQUERDA = r"(?:^|(?<=[\s;&|(){}`!'\"/=])|(?<=\\[nt]))"
# Fronteira à direita: o nome termina a palavra (`python3.py`, `node-gyp` não são o dono).
_DIREITA = r"(?![\w.-])"
# Do nome ao `<<`, a mesma linha de comando. Continuação de linha (`\` + quebra: `\\\n`
# no JSON, `\` + quebra real no texto cru), redirecionamento com `&` e pares de escape
# do JSON passam; quebra de linha, `;`, `|` e `&` de controle encerram (defeito 5).
_JANELA = r"(?:\\\\\\n|\\\n|[<>]&|&>|\\[^n\n]|[^\\\n;&|])"
_ALCANCE = 1000  # caracteres antes do `<<` em que a busca pelo dono olha
_TETO_ABERTURAS_POR_LINHA = 32  # acima disto, o texto volta intacto (defeito 8)
_ORCAMENTO_S = 0.2  # idem para o tempo de trabalho (defeito 8)


def _dono(nomes: str) -> re.Pattern[str]:
    return re.compile(_ESQUERDA + "(?:" + nomes + ")" + _DIREITA + _JANELA + "{0,200}<<$")


INTERPRETADOR = _dono(_SHELLS + "|" + _OUTROS)
SHELL = _dono(_SHELLS)

# Abertura de heredoc QUOTED: `<<'FIM'`, `<<"FIM"` (no JSON, `<<\"FIM\"`), com ou sem `-`.
# A aspa de fechamento é a da abertura e a palavra acaba ali (`<<'FIM'x` teria delimitador
# `FIMx` no bash). `<<<` é here-string.
ABERTURA = re.compile(
    r"(?<!<)<<(-?)[ \t]*"
    r"""(?:'([A-Za-z_][A-Za-z0-9_]*)'|\\"([A-Za-z_][A-Za-z0-9_]*)\\"|"([A-Za-z_][A-Za-z0-9_]*)")"""
    r"""(?=$|[\s;&|)<>"]|\\[ntr])"""
)

_PAR_OU_ASPA = re.compile(r'\\(.)|"', re.S)
_BARRAS_E_QUEBRA = re.compile(r"(\\*)\n")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}
_PALAVRA_COMECA_DEPOIS = " \t\n;&|()<>`"
_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ESTADO_INICIAL = (("cmd",), " ", False, 0)

# DEFEITO 7: a cauda da linha de abertura entrega o corpo a um shell — por pipe
# (`cat <<'EOF' | bash`, `| tr -d '\r' | sudo bash -s`) ou gravando um arquivo que a mesma
# linha executa (`cat <<'EOF' > s.sh && bash s.sh`, `tee s.sh <<'EOF'; ./s.sh`).
_PREFIXOS_DO_PIPE = (
    r"(?:(?:sudo|doas|env|nohup|exec|command|stdbuf|nice|ionice|setsid|timeout|xargs|chronic|unbuffer)"
    r"(?:\s+(?:-\S+(?:\s+[^-\s|;&]\S*)?|\w+=\S*|\d\S*))*\s+)*"
)
_ALVO_DE_REDIRECIONAMENTO = re.compile(r"""(?:\d?>>?|&>>?)\|?\s*(['"]?)([^\s;&|<>'"()`]+)\1""")
_ALVOS_DO_TEE = re.compile(r"(?:^|[\s;&|(])tee\s+(?:-\S+\s+)*((?:[^\s;&|<>()`-][^\s;&|<>()`]*\s*)+)")
_PREFIXOS_DE_EXECUCAO = (
    r"(?:(?:sudo|doas|env|nohup|exec|command|time|nice|timeout)(?:\s+-\S+|\s+\w+=\S*|\s+\d\S*)*\s+)*"
)


def _pipe_para(nomes: str) -> re.Pattern[str]:
    return re.compile(r"(?<!\|)\|&?(?!\|)\s*" + _PREFIXOS_DO_PIPE + r"(?:\S*/)?(?:" + nomes + ")" + _DIREITA)


PIPE_INTERPRETADOR = _pipe_para(_SHELLS + "|" + _OUTROS)
PIPE_SHELL = _pipe_para(_SHELLS)


def _executa(cauda: str, alvo: str, so_shell: bool) -> bool:
    """`alvo` (o arquivo que o heredoc grava) é executado em `cauda`? Por interpretador
    (`bash s.sh`, `source s.sh`, `. ./s.sh`) ou direto (`./s.sh`, `/tmp/s.sh`). Depois de
    um SHELL, opção curta com `n` (`bash -n s.sh`, `sh -en`) só confere a sintaxe e não
    conta; depois de outro interpretador conta (`perl -n s.pl` executa)."""
    base = alvo[2:] if alvo.startswith("./") else alvo
    escapado = re.escape(base)
    absoluto = base.startswith("/")
    fim = r"(?=$|[\s;&|)`])"
    interpretes = r"(?:" + _SHELLS + ")" + _DIREITA + r"(?:\s+-(?![a-zA-Z]*n)\S+)*"
    if not so_shell:
        interpretes = r"(?:" + interpretes + r"|(?:" + _OUTROS + ")" + _DIREITA + r"(?:\s+-\S+)*)"
    por_interpretador = (r"(?:^|[\s;&|(`])(?:\S*/)?" + interpretes + r"\s+"
                         + (escapado if absoluto else r"(?:\./)?" + escapado) + fim)
    direto = r"[;&|(`]\s*" + _PREFIXOS_DE_EXECUCAO + (escapado if absoluto else r"\./" + escapado) + fim
    return bool(re.search(por_interpretador, cauda) or re.search(direto, cauda))


def _cauda_executa_o_corpo(antes: str, cauda: str, so_shell: bool) -> bool:
    """Defeito 7. `antes` é a linha até a abertura; `cauda`, dela até o fim da linha lógica."""
    if (PIPE_SHELL if so_shell else PIPE_INTERPRETADOR).search(cauda):
        return True
    linha = antes + " " + cauda
    alvos = {m.group(2) for m in _ALVO_DE_REDIRECIONAMENTO.finditer(linha)}
    for m in _ALVOS_DO_TEE.finditer(linha):
        alvos.update(m.group(1).split())
    return any(_executa(cauda, alvo, so_shell) for alvo in alvos)


def _desescapa(trecho: str) -> str:
    return re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), "x"), trecho, flags=re.S)


def _em_contexto_de_comando(linha: str) -> bool:
    """A abertura que vem depois de `linha` está em contexto de comando? Falso se ela cai
    dentro de aspa simples, aspa dupla ou comentário (defeito 6). Substituição de comando
    (`"$(cat <<'X'`) volta a ser contexto de comando, como no bash."""
    return _contexto_ok(_avanca_contexto(linha, _ESTADO_INICIAL))


def _contexto_ok(estado: tuple) -> bool:
    return not estado[2] and estado[0][-1] not in ("'", '"')


def _avanca_contexto(linha: str, estado: tuple) -> tuple:
    """Avança a leitura de aspas e comentário sobre `linha` a partir de `estado` (pilha,
    anterior, em_comentario, pular) e devolve o estado novo. É incremental de propósito
    (defeito 8): a abertura seguinte na mesma linha continua de onde a anterior parou."""
    if estado[2]:
        return estado
    pilha = list(estado[0])
    anterior = estado[1]
    i, n = estado[3], len(linha)
    while i < n:
        c = linha[i]
        topo = pilha[-1]
        if topo == "'":
            if c == "'":
                pilha.pop()
            anterior = c
            i += 1
            continue
        if c == "\\":
            anterior = "x"
            i += 2
            continue
        if topo == '"':
            if c == '"':
                pilha.pop()
            elif c == "$" and linha.startswith("$(", i):
                pilha.append("(")
                i += 1
            elif c == "`":
                pilha.append("`")
            anterior = c
            i += 1
            continue
        if c in "'\"":
            pilha.append(c)
        elif c == "#" and anterior in _PALAVRA_COMECA_DEPOIS:
            return (tuple(pilha), anterior, True, 0)
        elif c == "(":
            pilha.append("(")
        elif c == ")" and topo == "(":
            pilha.pop()
        elif c == "`":
            if topo == "`":
                pilha.pop()
            else:
                pilha.append("`")
        anterior = c
        i += 1
    return (tuple(pilha), anterior, False, i - n)


class _Texto:
    """Quebras de linha e limites de string do texto, na forma em que ele chegou.

    Os chamadores entregam o comando ESCAPADO de JSON, em que a quebra de linha é o par
    `\\n` e uma aspa nua encerra a string. JSON nunca contém quebra de linha real; texto
    que contém uma é tratado como shell cru, em que a quebra é o caractere de nova linha.
    """

    def __init__(self, texto: str) -> None:
        self.t = texto
        self.json = "\n" not in texto
        self.largura = 2 if self.json else 1
        self.quebras: list[int] = []
        self.continua: list[bool] = []
        self.fins: list[int] = []
        if self.json:
            barras = 0
            fim_anterior = -1
            for m in _PAR_OU_ASPA.finditer(texto):
                colado = m.start() == fim_anterior
                g = m.group(1)
                if g is None:
                    self.fins.append(m.start())
                    barras = 0
                elif g == "n":
                    self.quebras.append(m.start())
                    self.continua.append(colado and barras % 2 == 1)
                    barras = 0
                elif g == "\\":
                    barras = barras + 1 if colado else 1
                else:
                    barras = 0
                fim_anterior = m.end()
        else:
            for m in _BARRAS_E_QUEBRA.finditer(texto):
                self.quebras.append(m.end() - 1)
                self.continua.append(len(m.group(1)) % 2 == 1)
        # Índice de fechamento (defeito 8): para cada linha que É um delimitador possível,
        # a quebra que a antecede. Linha com TAB à frente só fecha `<<-`.
        self.fechos: dict[str, list[int]] = {}
        self.fechos_com_tab: dict[str, list[int]] = {}
        for q in self.quebras:
            j = q + self.largura
            com_tab = False
            while True:
                if texto.startswith("\t", j):
                    j += 1
                elif self.json and texto.startswith("\\t", j):
                    j += 2
                else:
                    break
                com_tab = True
            nome = _IDENTIFICADOR.match(texto, j)
            if nome is None or not self._fim_de_linha(nome.end()):
                continue
            if not com_tab:
                self.fechos.setdefault(nome.group(0), []).append(q)
            self.fechos_com_tab.setdefault(nome.group(0), []).append(q)
        self._ctx_linha = -1
        self._ctx_pos = -1
        self._ctx_estado = _ESTADO_INICIAL

    def _limite(self, pos: int) -> int:
        """Onde acaba a string JSON que contém `pos` (no texto cru, o fim do texto)."""
        if self.json:
            i = bisect.bisect_left(self.fins, pos)
            if i < len(self.fins):
                return self.fins[i]
        return len(self.t)

    def inicio_da_linha(self, pos: int) -> int:
        i = bisect.bisect_left(self.quebras, pos) - 1
        ini = self.quebras[i] + self.largura if i >= 0 else 0
        if self.json:
            j = bisect.bisect_left(self.fins, pos) - 1
            if j >= 0:
                ini = max(ini, self.fins[j] + 1)
        return ini

    def trecho(self, ini: int, fim: int) -> str:
        """O texto entre `ini` e `fim` como o shell o lê (desescapado, no modo JSON)."""
        return _desescapa(self.t[ini:fim]) if self.json else self.t[ini:fim]

    def em_contexto_de_comando(self, pos: int) -> bool:
        ini = self.inicio_da_linha(pos)
        if ini == self._ctx_linha and self._ctx_pos <= pos:
            de, estado = self._ctx_pos, self._ctx_estado
        else:
            de, estado = ini, _ESTADO_INICIAL
        estado = _avanca_contexto(self.trecho(de, pos), estado)
        self._ctx_linha, self._ctx_pos, self._ctx_estado = ini, pos, estado
        return _contexto_ok(estado)

    def fim_da_linha(self, pos: int) -> int | None:
        """A quebra que encerra a linha lógica da abertura (defeito 3); continuação não conta."""
        limite = self._limite(pos)
        i = bisect.bisect_left(self.quebras, pos)
        while i < len(self.quebras) and self.quebras[i] < limite:
            if not self.continua[i]:
                return self.quebras[i]
            i += 1
        return None

    def _fim_de_linha(self, k: int) -> bool:
        """Depois do delimitador: quebra de linha, fim do texto, fim da string JSON ou `)`."""
        t = self.t
        if k >= len(t) or t[k] in '")':
            return True
        if self.json:
            return t.startswith("\\n", k)
        return t[k] == "\n"

    def fechamento(self, corpo: int, delimitador: str, com_tabs: bool) -> int | None:
        """A quebra que ANTECEDE a linha do delimitador (defeito 2), ou None. Sai do índice
        montado uma vez por texto, não de uma varredura por abertura (defeito 8)."""
        lista = (self.fechos_com_tab if com_tabs else self.fechos).get(delimitador, [])
        i = bisect.bisect_left(lista, corpo)
        if i < len(lista) and lista[i] < self._limite(corpo):
            return lista[i]
        return None


def remover_corpos(texto: str, so_shell: bool = False, orcamento: float = _ORCAMENTO_S) -> str:
    inicio = time.monotonic()
    dono = SHELL if so_shell else INTERPRETADOR
    t = _Texto(texto)
    partes: list[str] = []
    emitido = 0
    busca = 0
    linha_anterior = -1
    na_linha = 0
    while True:
        achado = ABERTURA.search(texto, busca)
        if achado is None:
            break
        if time.monotonic() - inicio >= orcamento:
            return texto  # teto de tempo (defeito 8): intacto — barra a mais, nunca a menos
        linha = t.inicio_da_linha(achado.start())
        na_linha = na_linha + 1 if linha == linha_anterior else 1
        linha_anterior = linha
        if na_linha > _TETO_ABERTURAS_POR_LINHA:
            return texto  # teto de aberturas na mesma linha (defeito 8): intacto
        busca = achado.end()
        if not t.em_contexto_de_comando(achado.start()):
            continue  # dentro de aspas ou de comentário: não abre heredoc
        if dono.search(texto, max(0, achado.start() - _ALCANCE), achado.start() + 2):
            continue  # o corpo alimenta interpretador: é executado, fica sob análise
        corpo = t.fim_da_linha(achado.end())
        if corpo is None:
            continue  # sem quebra de linha depois da abertura: não há corpo neste texto
        antes = t.trecho(max(linha, achado.start() - _ALCANCE), achado.start())
        if _cauda_executa_o_corpo(antes, t.trecho(achado.end(), corpo), so_shell):
            continue  # a cauda da linha entrega o corpo a um shell (defeito 7): fica sob análise
        delimitador = achado.group(2) or achado.group(3) or achado.group(4)
        fecho = t.fechamento(corpo, delimitador, achado.group(1) == "-")
        if fecho is None:
            continue  # heredoc sem fechamento no payload: não mexe, para não cortar demais
        partes.append(texto[emitido:corpo])
        emitido = fecho
        busca = fecho
    partes.append(texto[emitido:])
    return "".join(partes)


def main(argv: list[str]) -> int:
    opcoes = argv[1:]
    try:
        dados = sys.stdin.buffer.read()
    except Exception:
        return 1
    if not dados:
        return 1
    bruto = dados.decode("utf-8", "surrogateescape")
    saida = bruto
    if all(o == "--so-shell" for o in opcoes):
        try:
            saida = remover_corpos(bruto, so_shell=bool(opcoes))
        except Exception:
            saida = bruto
    sys.stdout.buffer.write(saida.encode("utf-8", "surrogateescape"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
