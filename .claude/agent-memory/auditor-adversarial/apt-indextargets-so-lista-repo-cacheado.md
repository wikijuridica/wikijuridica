---
name: apt-indextargets-so-lista-repo-cacheado
description: Ao auditar `apt-get update` restrito (Dir::Etc::sourcelist + sourceparts=-), `apt-get indextargets` só enumera repositório cujo Release já está em /var/lib/apt/lists — vazio para repo novo não prova defeito do kit
metadata:
  type: feedback
---

Não conclua "a fonte não parseia" quando `apt-get indextargets -o Dir::Etc::sourcelist=<arquivo> -o Dir::Etc::sourceparts=-` devolve vazio: ele só lista alvos de repositório já cacheado. Prove a restrição com um repo cacheado (um host por arquivo) e declare que o repo novo não é pré-testável sem root; o veredito da fase é pelo RESULTADO (`apt-cache policy` com candidato do host certo), não pelo rc.

**Why:** 2026-09-23 (kit `ops/ide/`): o `.list` do VSCodium deu vazio em todas as variantes (com/sem `signed-by`, com/sem `arch=`), e `deb https://example.invalid/debs foo main` também — enquanto `wezterm.list`, `nodesource.list` e o `vscode.sources` (cacheados) listaram exatamente um host cada. Quase virou CONFIRMED falso contra a fase 1.

**How to apply:** em kit que escreve fonte apt nova, separe três provas: (1) restrição honrada — `indextargets` sobre um arquivo cacheado → um host; (2) `APT::Get::List-Cleanup=0` presente — sem ele o `update` restrito apaga os índices alheios (`apt-config dump` sem a chave = default true); (3) chave/versão do repo novo por `curl` direto ao `Packages`/`InRelease` (ou o modo `--conferir-chave-upstream` do próprio kit). Segunda armadilha da mesma sessão: diretório de arquivo (`archive-vscode-<data>`) já existente no home real veio de OUTRO kit (`ops/terminal/instalar-terminal.sh`) que compartilha o destino — antes de acusar vazamento da bancada `unshare`, `grep -rn <destino> ops/*/` e `stat` do horário contra o log do outro kit.
