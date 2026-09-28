---
name: tela-preta-e-x-novo-do-lock-nao-dpms
description: Tela preta "que não volta" na torre (amdgpu iGPU + AOC HDMI + lightdm/light-locker) era o X NOVO do greeter nascendo com o monitor em DPMS — a prova está em Xorg.<N>.log do greeter e em lightdm.log "Seat seat0: Locking", não no journal
metadata:
  type: project
---

Tela preta que teclado/mouse não acendem, na torre (2026-09-24), NÃO era DPMS nem
suspend: o light-locker tranca pedindo ao lightdm um greeter em OUTRO VT com um X
novo (`lightdm.log: "Seat seat0: Locking" → "Using VT 8" → /usr/bin/X :1 vt8`);
esse X nasce 5 s depois de o monitor AOC entrar em standby e o amdgpu responde
`Output HDMI-A-0 disconnected` → `Unable to find connected outputs - setting
1024x768` (Xorg.1.log). O EDID volta 1,1 s depois, mas X nunca liga saída em
hotplug — é papel do xfsettingsd, que só existe dentro da sessão.

**Why:** o journal não registra nada disso (nem "PM: suspend", nem hotplug do
amdgpu); a assinatura fica em `/var/log/Xorg.<N>.log` do greeter (N ≠ 0) e em
`/var/log/lightdm/lightdm.log`. `lightdm/x-N.log` é append-only
(`backup-logs=false`): erros antigos ali parecem do boot atual. DPMS em sessão
foi medido OK (force off/on: conector `enabled=disabled→enabled`, `dpms=Off→On`,
EDID 256 B, modo `1920x1080*`).

**How to apply:** antes de culpar amdgpu/DPMS por tela preta com lightdm, leia
`lightdm.log` por "Locking"/"Using VT" e o `Xorg.<N>.log` do X mais novo. A
mitigação de sistema ficou em `/usr/local/sbin/lightdm-ativar-saida-conectada`
(display-setup-script + RUN do udev em `DEVTYPE=drm_minor`); a política de tela do
dono é `tools/vigilia` (escolha salva `on` = tela nunca apaga), e o caffeine
re-arma o screensaver de 600 s por baixo dela. Em janela de migração do home,
proteja a sessão só com `xset` em runtime (nada gravado no home). O classificador
barra `kill` no daemon de lock da sessão do dono — não tente por outra via.
