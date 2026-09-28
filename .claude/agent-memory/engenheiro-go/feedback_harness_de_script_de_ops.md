---
name: harness-de-script-de-ops
description: Ensaiar script de ops (provisionar/restaurar/migrar) exige diretorio proprio e isolamento que cubra o $HOME; unshare -Ur nao cobre
metadata:
  type: feedback
---

Ao ensaiar script de `ops/provisionamento/` (ou qualquer script que rode como root e escreva
fora do repo), duas coisas se decidem ANTES de rodar:

**1. O harness mora em subdiretório com nome próprio, nunca em `tmp/harness`.**
**Why:** `/home/rafael/.claude/jobs/<id>/tmp/` é compartilhado por todos os agentes do mesmo
job. Em 2026-09-22 outro agente apagou `tmp/harness/` (com `log/`, `wiki/`, os `.sh` preparados)
no meio da minha bateria: os testes passaram a falhar com "Arquivo ou diretório inexistente", e
um `diff` de process substitution sobre arquivos inexistentes devolveu **exit 0**, ou seja,
"(idênticas)" falso.
**How to apply:** nomeie `tmp/hg-<sua-frente>/`. E desconfie de `diff <(...) <(...)` quando o
insumo pode não existir — cheque o exit do produtor, não só o do `diff`.

**2. `unshare -Ur` protege `/etc`, `/usr`, `/var` — NÃO protege `/home/$DONO`.**
**Why:** com `-r` o uid 0 de dentro é o SEU uid de fora. Tudo que o script escreve em caminho
de root dá EPERM (medido: `/etc/locale.conf`, keyrings, `/var/lib/apt/lists/lock`,
`/usr/local/lib/systemd`), mas `> /home/rafael/.config/...` **passa e sobrescreve**. Em
2026-09-22 uma execução acidental em modo não-seco reescreveu
`~/.config/environment.d/20-locale-ptbr.conf` (mesmo conteúdo, mtime novo) e disparou dois
`curl` reais para `dl.google.com` e `packages.microsoft.com` com UA padrão do curl, a partir do
servidor de produção.
**How to apply:** ensaio de script de ops roda **sempre com o modo seco do próprio script**;
o userns é a segunda barreira, não a primeira. Se o script tem passo de rede não-seco, ele não
se ensaia nesta máquina de jeito nenhum — veja `[[feedback_parar_em_arquivo_concorrente]]` para
a outra armadilha de ambiente compartilhado.

**3. O buraco do `/home` FECHA com namespace de montagem (2026-09-22, medido).** Com
`unshare -Urm` há CAP_SYS_ADMIN no namespace e as montagens são privadas do processo:
`mount --bind X X && mount -o remount,bind,ro X` deixa `/opt/wiki` e `/home/$DONO` somente
leitura só para o ensaio; `mount -t tmpfs tmpfs /root` dá `/root` gravável sem root de verdade;
`mount -t tmpfs` sobre um diretório versionado faz um caminho **desaparecer** sem apagar nada
(é como se exercita guarda que exige ausência), e `mount --bind arquivo-real ponto` põe o
arquivo REAL de volta dentro do tmpfs — confira pelo inode, senão você testou uma cópia.
Para PROVAR que o modo seco não escreve, overlayfs não-privilegiado (`lowerdir` = o real,
`upperdir` em tmpfs) vira **detector**: toda escrita cai no upperdir e se conta, e o disco não
é tocado. Trava obrigatória no bloco interno: `awk 'NR==1{print $2}' /proc/self/uid_map` — vale
`0` no namespace inicial. NÃO use `readlink /proc/1/ns/user` como trava: para usuário comum ele
devolve **vazio**, nunca é igual ao seu, e a trava passa sempre. Exemplo completo em
`ops/provisionamento/testa-restauradores.sh`.
