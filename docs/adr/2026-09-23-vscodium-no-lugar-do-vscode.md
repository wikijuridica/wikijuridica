# ADR — VSCodium no lugar do VS Code, com a extensão Claude Code do Open VSX; kitty como terminal

**Data:** 2026-09-23 · **Estado:** aceito · **Decisor:** dono do projeto (ordem de 2026-09-23)

## Contexto

O dono mandou apagar o VS Code e pôr no lugar uma ferramenta gratuita, potente, que converse
com o Claude Code, sem plano pago, dimensionada para a máquina nova e não para o notebook. No
mesmo dia mandou também o terminal: "os que eu tenho no servidor, a maioria tem bugs; terminal
bom para o Claude Code trabalhar sem problemas e com máxima eficiência".

O VS Code do notebook é o build da Microsoft (`code 1.136.1-1788413865`, repositório
`packages.microsoft.com`), com telemetria ligada por padrão e o perfil inteiro voltado ao projeto
arquivado `/opt/divorcio`. Três extensões falham na ativação em 100 % das quatro últimas sessões
com janela, porque as pastas delas não têm `node_modules`; o `formatOnSave` aponta para o prettier
quebrado, então salvar um `.go` não roda nem o gofmt; a extensão Claude Code é a 2.0.75 contra o
CLI 2.1.280, e `~/.claude/ide/` está vazio desde abril — a integração nunca foi usada. O que está
quebrado é a camada de extensões e configuração, não o binário: zero crash dump em `Crashpad/`.

Duas restrições separam os candidatos, e elas vêm do jeito como este projeto trabalha:

- **(a)** as sessões `claude` que rodam no tmux do terminal de agentes (`ai-pane`) têm de se
  ligar ao editor pelo `/ide` — diff, seleção e plano em Markdown no editor, sem abrir outra sessão;
- **(b)** o editor tem de honrar `~/.claude/settings.json` e `/opt/wiki/.claude/settings.json` —
  hooks, `model: fable`, MCP, roster de agentes.

Na máquina nova a RTX 5060 Ti usa o driver `-server-open` headless (sem GL nem driver X para ela),
então o desktop desenha na iGPU do Ryzen.

## Decisão

**Editor: VSCodium, com a extensão oficial `Anthropic.claude-code` publicada pela Anthropic no
Open VSX, na mesma versão do CLI.** Livre é o **editor** (build MIT do VS Code, sem telemetria);
a extensão e o CLI são proprietários, como sempre foram — a refutação 1 corrigiu a primeira
redação, que chamava tudo de livre.

A extensão **é** o Claude Code: grava `~/.claude/ide/<porta>.lock` a cada ativação, autentica a
ponte pelo cabeçalho `X-Claude-Code-Ide-Authorization` e compartilha settings, hooks, MCP e
histórico com o CLI. Por isso cumpre (a) e (b). O VS Code da Microsoft cumpriria as duas, e está
vetado.

A ponte no VSCodium é **gate pré-registrado, não fato provado** (plano §5.4). Três provas, no
notebook e depois na máquina nova: (1) `codium --install-extension anthropic.claude-code@<versão>`
instala a mesma versão de `claude --version`; (2) com o editor aberto em `DISPLAY=:99` sobre
`/opt/wiki`, um `claude` no tmux conecta por `/ide` — com um lock e com dois; (3) o painel responde
sem tela de login, reaproveitando `~/.claude/.credentials.json`, e um `/plan` abre o Markdown no
editor. Falha de qualquer uma por defeito do VSCodium ou do Open VSX — e não por configuração
corrigível em até duas tentativas — faz a mesma sessão instalar Zed com o adaptador ACP e
registrar a troca aqui. O resultado das provas fica em `docs/ops/IDE_VSCODIUM_20260923.md` §8.

*(2026-09-23, 13:14: no notebook, as três provas passaram — extensão 2.1.280 = CLI; lock em `:99`, `claude --ide` interativo conectado e turnos respondidos; `loggedIn: true` sem tela de login — e o principal fica o VSCodium, sem fallback. Às 13:41–13:47 a variante com dois locks foi provada à mão (`/ide` manual → `Connected to VSCodium.`, `ss`); o `/plan` na sessão do CLI abre a prévia na TUI (ctrl+g/Micro), não no editor — esse fluxo é do painel da extensão, não exercitado; detalhe no §8 do doc.)*

**Terminal: kitty**, o do archive do Ubuntu na máquina nova (`kitty 0.45.0-1build1`, universe, já
em `pacotes.txt:152`) e o 0.47.4 do instalador oficial no notebook, que já é o terminal padrão do
Xfce ali. É o único candidato que soma pacote no archive, "works without setup" na documentação
do Claude Code nos dois eixos — Shift+Enter **e** notificação de desktop —, protocolo de teclado
kitty, gráficos, OSC 52 e remote control, que deixa a bancada apertar tecla sem tocar `:0`.
Rubrica do plano §8 frente 10.4: kitty 9,5 · ghostty 9,1 · alacritty 0.16 7,2 · WezTerm 6,6 ·
xfce4-terminal 6,6. **Ghostty 1.3.0** (archive, MIT) fica como fallback documentado.

## Alternativas rejeitadas

**Zed + ACP** — editor GPL-3.0; adaptador `@agentclientprotocol/claude-agent-acp`, Apache-2.0,
canal estável (`latest 0.81.0`, 2026-09-22). A refutação 1 derrubou três objeções da primeira
redação: o adaptador carrega `settingSources: ["user","project","local"]`
(`src/acp-agent.ts:8236`), então hooks, CLAUDE.md, MCP e plan mode valem; não está em `@preview`;
teve 4 releases estáveis em 8 dias. **Cumpre (b). Não cumpre (a):** não existe ponte `/ide` para
uma sessão do CLI num terminal externo, e o terminal de agentes é o centro do trabalho do dono.
Fica como fallback, atrás do gate acima. Exige Vulkan e traz telemetria ligada por padrão
(desligável).

**Neovim + `claudecode.nvim`** — implementa o mesmo protocolo WebSocket do `/ide`. Rejeitado como
principal pela ergonomia modal para o dono; fica documentado como opção dentro do tmux, sem
instalação por padrão.

**Eclipse Theia** — EPL, usa Open VSX, tem provedor Anthropic genérico e nenhuma integração com o
Claude Code. Nenhum ganho sobre o VSCodium.

**VS Code da Microsoft** — veto do dono, telemetria ligada por padrão e o perfil descrito acima.
O pacote sai só **depois** de o VSCodium passar na verificação, para o dono nunca ficar sem
editor; o perfil é arquivado por `mv` com data, nunca apagado.

**Cursor, Windsurf, GoLand, Copilot, Pylance** — proprietários ou pagos (Cursor Pro e Windsurf
US$ 20, GoLand sem edição Community, Copilot US$ 10; o Pylance nem está no Open VSX — 404). Saem
pela regra self-hosted e sem pagamento do `~/.claude/CLAUDE.md`. O Python do editor fica com
`basedpyright` e `ruff`.

**Terminais.** **WezTerm** sai da máquina nova: repositório de terceiro (`apt.fury.io/wez/`),
stable de fevereiro de 2024, ausente do archive do 26.04; no notebook nada se remove. **Alacritty**
0.11 do notebook tem config dividida entre TOML ignorado e YAML efetivo, sete backups e dois
incidentes; o 0.16 do 26.04 cruza o corte da documentação só para Shift+Enter. **xfce4-terminal**
(VTE) não está na lista "works without setup" para nenhum dos dois eixos.

## Consequências

**A favor:** telemetria desligada; nenhum plano pago; a ponte `/ide` serve as sessões do tmux; o
Claude Code do painel e o do terminal são o mesmo, com os mesmos hooks e settings; a versão da
extensão anda junto com a do CLI por um comando só; o gofmt roda ao salvar `.go` e nada mais
formata sozinho; o watcher exclui as raízes pesadas, e isso também impede o Claude de receber o
conteúdo de JSONL gigante selecionado no editor; a RTX fica inteira para CUDA. O terminal vem do
archive e aceita automação para bancada.

**Contra, e dito:** a extensão é proprietária e presa à versão do CLI — se o Open VSX atrasar, o
CLI espera (o `atualizar-claude-code.sh` consulta o Open VSX **antes** de tocar o CLI). O VSCodium
anda um minor atrás do VS Code. O `hold` congela correção de segurança até a atualização
explícita; o `--verificar` avisa quando `apt-cache policy codium` mostra Installed ≠ Candidate.
Não há Pylance. O deep link `vscode://` no VSCodium não está provado — o login não depende dele.
A bancada em Xvfb `:99` prova instalação, ativação, lock, `/ide` e login; aceleração de GPU, nunca
— essa só se mede na máquina nova, sem tocar o display. A iGPU toma uma parcela da RAM como UMA.

## Pacote

- **`codium`** — licença **MIT**. Repositório `https://download.vscodium.com/debs vscodium main`,
  com a chave pública versionada em `ops/ide/vscodium-archive-keyring.asc` e pinada pelo
  fingerprint **`1302DE60231889FE1EBACADC54678CF75A278D9C`** (RSA, 2018-10-09; arquivo publicado
  com 3.135 B e sha256 `dbdfd9af3b83b72a24c89160ce7638418142e2cf4736ab53e5061e10070f13c1`,
  conferido pela refutação 2; o `InRelease` do repositório é assinado pelo mesmo fingerprint). A
  instalação não baixa chave. **`apt-mark hold codium`**: o repositório publica uma versão por vez
  (`codium 1.135.06055` em 2026-09-23, `InRelease` de 2026-09-09), e subir é ato explícito —
  `unhold` → `install` → `hold` → bancada. A versão instalada fica registrada em
  `docs/ops/IDE_VSCODIUM_20260923.md` §3.
- **`Anthropic.claude-code`** — **proprietária**. No Open VSX, `2.1.280`, publicada em
  2026-09-22T16:40:47Z, `engines.vscode ^1.94.0`; presa à versão do CLI (`claude --version` →
  `2.1.280 (Claude Code)`, medido às 08:18:21 de 2026-09-23). `extensions.autoUpdate` e
  `extensions.autoCheckUpdates` desligados no perfil, `autoUpdates: false` no CLI: atualizar é ato
  do kit, nos dois ao mesmo tempo.
- **`kitty`** — licença GPL-3+ (`/usr/share/doc/kitty/copyright:8`, do pacote `kitty 0.26.5-5` do apt, lido às 08:46 de 2026-09-23). `0.45.0-1build1` do archive na máquina nova; `0.47.4` do
  instalador oficial no notebook, onde fica.
