---
name: etc-falso-por-bind-mata-o-awk
description: Bancada em unshare que monta um /etc falso por bind-mount perde o awk (e todo binário de /etc/alternatives) — copie alternatives com cp -rP e autoteste as ferramentas antes da primeira asserção
metadata:
  type: feedback
---

Um `/etc` de mentira montado por `mount --bind` sobre `/etc` dentro de `unshare -Urm` precisa
levar `/etc/alternatives` junto (`cp -rP`, nunca `cp -a`), e a montagem tem de terminar com um
autoteste das ferramentas de que a bancada depende (`awk`, `sed`, `grep`, `find`, `stat`,
`readlink`, `date`) antes da primeira asserção.

**Why:** em Debian e Ubuntu `/usr/bin/awk` é symlink para `/etc/alternatives/awk`; com o `/etc`
falso sem esse diretório o `awk` some ("comando não encontrado") e toda expectativa calculada por
ele vira **zero**. Na primeira rodada da `testa-symlinks-etc.sh` (2026-09-23) isso fez o caso m3
escrever a fixture em `""`, rodar sem fixture e declarar o mutante morto sem tê-lo exercitado —
a mesma classe de [[fixture-que-nao-alcanca-a-guarda]]. A função de produção não usava `awk` e
por isso os 5 links nasceram, mascarando ainda mais. E `cp -a` falhou entrada a entrada (2.824
linhas de "falha ao preservar o dono"): o dono real dos links não está mapeado no namespace.

**How to apply:** ao montar `/etc` falso, copie `passwd`, `group`, `nsswitch.conf`, `localtime`
E `alternatives/` (com `cp -rP`); confira `[ ! -e /etc/sysctl.d ]` para provar que o bind
pegou; rode `command -v` de cada ferramenta e um `awk '{print $2}'` de verdade; destino de
fixture vazio é sandbox reprovado (exit 9), nunca asserção. Relacionado:
[[bancada-nao-escreve-em-producao]], [[ajudante-ausente-deixa-bancada-verde]].
