---
name: provar-instalador-com-bwrap-home-falso
description: Como auditar instalador de home (aplicar/--seco/idempotência) sem tocar o home do dono — bwrap com / ro-bind, /home em tmpfs, HOME falso bindado do scratchpad, md5 antes/depois
metadata:
  type: feedback
---

Para provar "não escreve fora de X", "backup é mv, não rm" e "2ª rodada zero ações" de um instalador que mexe no home, rode-o dentro de `bwrap` em vez de confiar no relato do worker ou no `--seco` textual.

**Why:** 2026-09-23 (goal IDE, `ops/terminal/instalar-terminal.sh`): o worker alegou prova por strace/bwrap; a alegação só virou evidência quando eu repeti no meu contexto — `--seco` deixou o HOME falso byte a byte igual (md5 de 9 arquivos), `aplicar` moveu os 4 originais para `.bak-<ts>` com md5 idêntico ao de antes, e a 2ª rodada deu `acoes=0`.

**How to apply:** receita que funcionou (kitty em `~/.local/kitty.app` precisa continuar visível, por isso /home vira tmpfs e o home real volta ro):
`bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --bind $SP/fake-tmpclaude /tmp/claude-1000 --tmpfs /home --ro-bind /home/rafael /home/rafael --bind $SP/fakehome /home/fake --ro-bind /home/rafael/.local/share/fonts /home/fake/.local/share/fonts --setenv HOME /home/fake --unsetenv DISPLAY --unsetenv DBUS_SESSION_BUS_ADDRESS --unshare-net --die-with-parent -- bash <script> [--seco]`.
Antes: popular o fakehome com cópias (`cp -p`/`cp -P`) dos arquivos reais que o script toca e gravar `md5sum` de tudo; depois: `diff` dos md5, `ls` dos `.bak-*`, e rodar 2ª vez. Declare o que NÃO exercitou (ramo de download com `--unshare-net`, flags não passadas).
