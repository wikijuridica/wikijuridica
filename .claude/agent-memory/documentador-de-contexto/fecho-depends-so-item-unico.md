---
name: fecho-depends-so-item-unico
description: ao resolver fecho de Depends transitivo em índice apt, só grupo Depends sem "|" é garantia real; seguir a 1ª alternativa produz cadeia falsa
metadata:
  type: feedback
---

Medido em 2026-09-23, colheita "torre nova / desktop 26.04". Um `Packages.gz` tem
`Depends: A | B | C` (alternativas — qualquer uma satisfaz) e `Depends: X, Y, Z`
(itens obrigatórios, cada um dos quais pode por sua vez ter alternativas). Um
fecho por BFS que segue "a primeira alternativa resolvível de cada grupo"
produz cadeias plausíveis mas **falsas**: no caso real,
`network-manager-gnome → network-manager-applet → gnome-shell → ... → pipewire`
sugeria que `pipewire` era garantido, mas `network-manager-gnome` tem
`Depends: network-manager-applet | nm-connection-editor` — a segunda
alternativa (bem mais leve) também satisfaz e não passa por `gnome-shell`.

**Como aplicar**: para afirmar "pacote X chega por Depends garantido", só conte
grupos de alternativa com **um único item** (`len(altgroup) == 1`, sem `|`
nenhum no `Depends:`/`Pre-Depends:` daquele grupo). Grupo com `|` não é
garantia — é possibilidade — mesmo que hoje a primeira opção pareça óbvia.
Isso reduziu um fecho de "3.558 alcançáveis por qualquer alternativa" para
"1.585 realmente garantidos" no mesmo conjunto-base de 428 pacotes.

Ver também [[hook-so-permite-leitura-listada]] (a mesma sessão bateu na
allowlist ~8 vezes: `xorriso`, `dpkg-query`, `fc-list` todos fora; `curl` com
redirect `>` só passa com caminho LITERAL, nunca `$variavel` no nome do
arquivo — um loop `for c in main universe; do curl ... > "Packages-$c.gz"`
é barrado mesmo escrevendo em `/tmp`, porque a guarda lê o texto do comando
antes de expandir; e `open(caminho, 'w')` em Python heredoc é barrado mesmo
com caminho para `/tmp` — só `sys.stdout.write(...)` + redirect `>` do shell
com caminho literal produz um arquivo).
