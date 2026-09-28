# ADR — Xvfb: display virtual para o agente operar navegador

**Data:** 2026-08-27 · **Estado:** aceito · **Decisor:** dono do projeto

## Contexto

O agente precisa operar um navegador para publicar nos perfis oficiais. Até
hoje o Chrome do publicador subia em `DISPLAY=:0.0` — **a tela do dono** —, com
janela visível. Medido: o processo estava vivo em `:0.0` enquanto ele
trabalhava, disputando o cursor.

Nessa tela há uma VM Windows anexada por `virt-viewer --attach escritorio-win11`
com **PJe/e-SAJ e o token de assinatura** do titular. `virt-viewer --attach`
encaminha teclado e mouse para dentro do guest: input mal localizado ali não
erra um post, **assina em processo judicial**. Somam-se terminais com shell que
roda como o mesmo usuário de `nginx` e `cloudflared`, e outras sessões de agente.

## Decisão

Todo navegador dirigido por agente roda em **`Xvfb :99`**, display virtual
separado. Nunca em `:0`.

```
Xvfb :99 -screen 0 1440x1000x24 -nolisten tcp
```

**Isso resolve o risco por CONSTRUÇÃO, não por cuidado.** Um processo em `:99`
não tem como alcançar janela de `:0`: são servidores X distintos, com sockets
distintos. A VM do PJe, os terminais e as sessões de agente ficam fora de alcance
— não porque o código evita, mas porque não existe caminho.

Única exceção: `--login`, que precisa de `:0` com janela porque **o titular**
digita credencial vendo a tela. Isso é ação dele, não do agente.

## Alternativas rejeitadas

**Headless (`--headless`)** — rejeitado como padrão pelo motivo que originou a
frente: headless **não renderiza diálogo nativo do sistema**, e foi exatamente
um seletor de arquivo nativo do Instagram que travou tudo. Sem tela, não há onde
o diálogo apareça. Fica disponível como opção para quem quiser o modo barato.

**Xephyr** — desenha o display virtual **dentro de uma janela em `:0`**. Isola o
input, mas ocupa a tela do dono e morre com `:0`. Metade do ganho, todo o
incômodo.

**Segundo X em outro VT** — rouba o console, briga com o display manager e
`chvt` mexe no que o dono está usando. Risco alto, ganho zero sobre Xvfb.

**Não separar (seguir em `:0`)** — é o estado que esta ADR corrige.

## Consequências

**A favor:** o agente deixa de aparecer e de disputar cursor; a tela pode estar
bloqueada; a VM e os terminais ficam inalcançáveis; a sessão autenticada
continua valendo, porque **cookies vivem no perfil em disco, não no display**.

**Contra, e dito:** o dono deixa de ver o agente trabalhar. Compensa-se por
engenharia — captura antes/depois de cada ação e registro auditável — que é
melhor que olhar, porque fica. Se quiser espelho ao vivo, `x11vnc` (GPL-2,
disponível no apt) em `:99` resolve, com ADR própria; ninguém pediu.

## Pacote

`xvfb 2:21.1.7-3+deb12u12` (bookworm/main), **licença MIT/X11** (X.Org).
~4 MB em disco, 40-60 MB de RAM por display, CPU ~0 ocioso. Não toca o runtime
do portal: é ferramenta de operação.

Ferramentas já presentes que a camada usa: `tesseract` 5.3.0 (Apache-2.0) com
`por`/`eng`, `ImageMagick` 6.9.11.60, `xdotool`, `wmctrl`, `scrot`.
