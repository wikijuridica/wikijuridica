# Footprint de MCP no Claude Code — medição de 2026-08-19

Investigação aberta pelo dono: *"ELe tá consumindo muita RAM no terminal e quando eu dou ESC
ou saio do claude code ele tá deixando MCP órfão aberto deixando o servidor pesado"* e, no meio
da apuração: *"começou a ter RAM alta, depois que eu instalei vários MCPs hoje"*.

Tudo abaixo é medição própria reproduzível (`/proc`, `ps`, `docker ps`, `~/.claude.json`),
conforme R3 do `CONTRATO_DADO_REAL.md`.

## 1. O tamanho do problema

| grandeza | valor medido |
|---|---|
| processos de MCP vivos | **193** |
| RSS somado | **2.778 MB** |
| swap somado | **4.395 MB** |
| containers Docker de MCP | **9** (`hashicorp/terraform-mcp-server:0.4.0`) |
| RAM total da máquina | 19.879 MB (13.802 em uso, 6.485 em swap) |

Ou seja: os servidores MCP respondem por **~7,2 GB de footprint** (residente + paginado) numa
máquina de 19,9 GB que já opera com 6,5 GB em swap.

## 2. A causa — datada e ancorada no git

Antes de hoje, `/opt/wiki/.claude/settings.json` habilitava **2 plugins** (`gopls-lsp`,
`session-report`). O `git diff HEAD` do arquivo mostra **+49 plugins** acrescentados hoje,
e o `~/.claude/settings.json` global foi a 30. No cache dos plugins, **83 diretórios** têm
mtime de 2026-08-19, entre 11:15 e 15:18.

O relato do dono está literalmente correto: o consumo começou hoje, com a instalação.

## 3. O mecanismo — não é órfão, é custo por sessão multiplicado

Hipótese do relato testada e **refutada**. `tools/measure-mcp-session-footprint` sobe um TUI
real em tmux, espera a stack estabilizar, fecha a janela e conta sobreviventes:

```
[estabilizou] 22s  arvore=24 processos  RSS=1883 MB  docker=8 (+1)
[RESULTADO CLOSE] arvore=24 ORFAOS_MCP=0 | docker antes=7 durante=8 depois=7
```

**Zero órfãos.** O Claude Code encerra os filhos corretamente, inclusive o container Docker.
O mesmo vale para `SIGKILL`: 14 descendentes, 0 sobreviventes. Nenhum processo MCP da máquina
tem `PPID == 1` por abandono.

O número que importa é o outro: **uma única janela do Claude Code custa 1.883 MB só de MCP**,
em 24 processos. O que o dono percebe como "servidor pesado" não é lixo deixado para trás —
é esse preço, cobrado tantas vezes quantas sessões existirem. E existem mais sessões do que
janelas. Agrupando os 193 processos pela sessão Claude raiz:

| sessão raiz | processos MCP | RSS | swap |
|---|---|---|---|
| 692624 (hospeda o `claude daemon run`) | **98** | 899 MB | 2.537 MB |
| 933341 | 23 | 1.442 MB | 0 |
| 695886 | 23 | 93 MB | 764 MB |
| 710537 | 22 | 90 MB | 722 MB |
| 800344 | 18 | 231 MB | 372 MB |

A sessão 692624 hospeda `claude daemon run --origin transient`, que mantém `bg-pty-host` →
**sessões `bg-spare` pré-aquecidas** e subagentes. Cada uma carrega a stack de 10 servidores
outra vez. São 5 janelas de terminal, mas ~9 stacks de MCP — e os spares nem estão sendo usados.

A stack por sessão, medida nos filhos diretos do processo desta própria sessão, é:
`lumen`, `data-agent-kit(notebook)`, `convex`, `playwright`, `semgrep(hook)`,
`chrome-devtools`, `terraform(docker run)`, `desktop-commander`, `browser-use`, `aikido`.

### O caso do Docker

O container `hashicorp/terraform-mcp-server` roda ancorado em `containerd-shim → init`, fora
da árvore de processos do Claude — mas o `docker run` que o controla **é** filho da sessão, e
o `--rm` recolhe o container quando ele morre. Não é órfão. O que se mediu ali foi **churn**:
em 2 horas, 27 `create`, 27 `start`, 23 `die`, 33 `kill`. Um container ficou preso no estado
`Created` desde as 11:28, sem nunca iniciar. O plugin sobe e cai repetidamente — provavelmente
por falta de `TFE_TOKEN`, que este projeto não tem nem deve ter.

## 4. Custo por servidor

| servidor | processos | RSS | swap | RSS/proc |
|---|---|---|---|---|
| chrome-devtools | 33 | 688 MB | 1.141 MB | 20,9 MB |
| aikido | 27 | 406 MB | 396 MB | 15,1 MB |
| convex | 27 | 367 MB | 776 MB | 13,6 MB |
| playwright | 27 | 365 MB | 728 MB | 13,5 MB |
| desktop-commander | 15 | 348 MB | 403 MB | 23,2 MB |
| browser-use | 18 | 308 MB | 529 MB | 17,1 MB |
| data-agent-kit | 10 | 154 MB | 342 MB | 15,4 MB |
| terraform | 18 | 96 MB | 41 MB | 5,4 MB |
| lumen | 9 | 26 MB | 17 MB | 2,9 MB |

## 5. Uso real — e o instrumento que mentia

A primeira versão desta seção afirmava que **nenhuma ferramenta MCP local foi chamada desde
2026-02-25**, com base no `toolUsage` de `~/.claude.json`. A afirmação estava errada, e o erro
é instrutivo: o `toolUsage` **parou de gravar há 174 dias, para todas as ferramentas**.

```
Read    usageCount=5914  lastUsedAt=2026-02-26 15:20
Bash    usageCount=3365  lastUsedAt=2026-02-26 15:22
Grep    usageCount=4045  lastUsedAt=2026-02-26 15:20
lastUsedAt mais recente de TODO o toolUsage: 2026-02-26 15:24
agora: 2026-08-19
```

`Read` e `Bash` foram chamados dezenas de vezes hoje, nesta mesma investigação. Se o contador
estivesse vivo, marcariam hoje. O silêncio das ferramentas MCP naquele registro não é prova de
não-uso — é telemetria morta, e as 4 chamadas de playwright de fevereiro são só o último
instante em que o arquivo ainda era escrito. Ler ausência de linha como ausência do fato é a
armadilha catalogada em `DADOS_CONFIAVEIS_E_ARMADILHAS.md`, e ela mordeu aqui.

O `pluginUsage`, por outro lado, **está vivo** (última escrita às 15:32 de hoje) — mas conta
outra coisa. `data-agent-kit` marca 631 "usos" tendo sido instalado hoje às 12:27: são três
horas para 631 usos deliberados de um plugin de GCP que ninguém tocou. O contador incrementa
por carregamento e por hook, não por decisão de usar. Serve para saber o que **é carregado**;
não serve para saber o que **é usado**.

Sobra a evidência que não depende de contador, e ela é mais forte:

- **Varredura dos transcripts.** São 101 arquivos e 2,1 GB em `~/.claude/projects/-opt-wiki/`,
  cobrindo de **2026-07-05 até hoje** — a janela honesta de retenção, ~6,5 semanas, não seis
  meses. Procurando o campo `"name":"mcp__plugin_…"`, que é como um bloco `tool_use` real
  aparece: **zero ocorrências**. O parser tem controle positivo — a mesma busca por `"Bash"`
  acha os arquivos. Nenhuma ferramenta MCP de plugin foi chamada em seis semanas e meia.
- **CPU acumulado.** O processo MCP mais "trabalhado" da máquina somou **6 segundos** de CPU em
  quase duas horas de vida. Um servidor que atendesse chamadas de verdade não ficaria nesse
  patamar. Eles não trabalham — ocupam.
- **Data de instalação.** Dos onze cortados, oito foram instalados **hoje**, entre 11:15 e
  12:30. Não havia hábito de uso a proteger, porque não houve tempo de existir.
- **Contrato do repositório.** GCP, BaaS e SaaS proprietário são proibição explícita do
  `CLAUDE.md`. Um plugin cujo único propósito é operá-los não tem como ser usado aqui.

## 6. Critérios de corte

Quatro eixos, aplicados nesta ordem:

1. **Transporte.** Só MCP `stdio` sobe processo local. MCP `http`/remoto custa **contexto**
   (tokens do system prompt), nunca RAM. Não se misturam os dois eixos.
2. **Contrato do repositório.** `CLAUDE.md` proíbe SaaS proprietário e nuvem de terceiros
   (AWS, GCP, Vercel). Plugin cujo único propósito é operar esses serviços tem perda **zero**
   por definição — não haveria como usá-lo aqui.
3. **Redundância.** Capacidade já coberta por ferramenta nativa ou por outro plugin.
4. **Uso medido — mas pelo instrumento certo.** A varredura dos transcripts retidos e o CPU
   acumulado. Os contadores de `~/.claude.json` **não servem**: o `toolUsage` parou de gravar
   em 2026-02-26 e o `pluginUsage` conta carregamento, não decisão de usar (seção 5).

## 7. Decisão

### Cortados — stdio (recuperam RAM)

| plugin | RAM | por quê |
|---|---|---|
| `chrome-devtools-mcp` | 688 MB | é a 4ª pilha de browser da máquina; `claude-in-chrome` é nativo — verificado, não há processo standalone dele |
| `aikido` | 406 MB | SaaS de segurança (eixo 2); `semgrep` local já faz SAST |
| `convex` | 367 MB | BaaS proprietário; o portal serve de arquivo estático com banco JSONL — não há backend Convex |
| `playwright` | 365 MB | redundante com `claude-in-chrome`, que é nativo; as únicas 4 chamadas já registradas são de fev/2026, quando o `toolUsage` ainda gravava |
| `desktop-commander` | 348 MB | duplica Bash/Read/Write/Edit nativos, com risco de caminho divergente |
| `browser-use` | 308 MB | 3ª pilha de browser |
| `data-agent-kit-starter-pack` | 154 MB | declara **13 servidores stdio, todos GCP** (BigQuery, Spanner, AlloyDB, Cloud SQL, Dataplex, Dataproc, Spark, Bigtable, Cloud Storage) — GCP é proibição explícita |
| `terraform` | 96 MB + 7 containers | IaC de nuvem que este projeto não usa; sem `TFE_TOKEN` entra em churn — 27 containers criados e 23 mortos em 2 h |

Três saíram sem recuperar RAM, e é honesto separá-los dos oito acima:

| plugin | por quê sai | RAM recuperada |
|---|---|---|
| `codspeed` | benchmark SaaS — e o `.mcp.json` dele declara `url`, não `command`: é **remoto**, nunca subiu processo | **0 MB** |
| `fakechat` | plugin de demonstração; já constava em `disabledMcpServers` e não tinha processo vivo | **0 MB** |
| `laravel-boost` | roda `php artisan` num repositório Go; idem, já desligado | **0 MB** |

O `codspeed` chegou a ser listado como `stdio` na primeira versão desta tabela — erro que
violava o próprio eixo 1, apanhado na revisão adversarial. O corte continua correto por ser um
SaaS que o contrato proíbe; o que estava errado era o rótulo e o ganho atribuído.

### Mantidos — com justificativa

> **Superado, medido em 2026-09-23:** as linhas de plugin desta tabela (`gopls-lsp`, `lumen`, `semgrep` e a das skills, `hookify` … `plugin-dev`) não descrevem mais a máquina — `enabledPlugins` dos dois settings só tem `caveman@caveman`: `python3 -c 'import json;print(json.load(open(P)).get("enabledPlugins"))'` sobre `~/.claude/settings.json` e `/opt/wiki/.claude/settings.json` devolve `{'caveman@caveman': True}` nos dois (2026-09-23 08:16:50 -03). A limpeza de 2026-09-08 tirou os demais; decisão e motivo em [`CLAUDE_CODE_PLUGINS_2026-09-08.md`](CLAUDE_CODE_PLUGINS_2026-09-08.md) §5. A linha dos MCPs `http` não é coberta por esta nota (não foi medida aqui). A tabela fica como registro da decisão daquela data.

| plugin | por quê fica |
|---|---|
| `gopls-lsp` | Go é a linguagem do caminho de serving (DEC-036); é a ferramenta de linguagem do projeto |
| `lumen` | busca semântica **local**, com hook ativo, e **26 MB** — o mais barato da lista (os "541 usos" do `pluginUsage` contam carregamento, não decisão de usar) |
| `semgrep` | SAST **local**, 15 MB; roda por hook em `Write`/`Edit`/`Bash` |
| `hookify`, `remember`, `superpowers`, `code-review`, `commit-commands`, `claude-md-management`, `session-report`, `security-guidance`, `plugin-dev` | skills/agents apenas — **não sobem processo algum** |
| MCPs `http` de SEO/jurídico (GSC, Ahrefs, DirectCase, Legal Data Hunter, Exa, Parallel) | zero RAM; alimentam a frente de indexação e de fonte oficial do portal |

## 8. Duas coisas que a revisão adversarial mudou

### O bisturi que não corta neste arquivo

Existe uma chave `disabledMcpServers` que desliga **só o servidor MCP** e preserva as skills do
plugin — útil para o `chrome-devtools-mcp`, cujas 6 skills incluem duas de Core Web Vitals.
Testei: reabilitei o plugin e declarei `"plugin:chrome-devtools-mcp:chrome-devtools"` em
`disabledMcpServers` dentro de `.claude/settings.json`. A medição respondeu:

```
[estabilizou] 11s  arvore=6 processos  RSS=460 MB
     987056    129MB  npm exec chrome-devtools-mcp@1.7.0
     987106    153MB  chrome-devtools-mcp
```

**Não funciona ali.** A chave só é lida de `~/.claude.json`, sob `projects["/opt/wiki"]` — é
onde as 184 entradas existentes moram, `plugin:greptile:greptile` e `plugin:dak:visualization`
entre elas. Revertido, e a chave morta foi removida em vez de deixada no arquivo: config que
não é lida engana quem vier depois.

Ficou por fazer de propósito. Editar `~/.claude.json` significa reescrever um arquivo que as
sessões vivas atualizam (OAuth, caches, histórico) — um read-modify-write concorrente pode
apagar escrita alheia. Não vale o risco por skills de depuração de browser num portal que serve
HTML estático sem JavaScript, onde o LCP é dominado por TTFB e não há memória de JS a vazar.

### Os mantidos também cobram — só que em CPU e contexto, não em RSS

O `ps` mede RSS e por isso não vê o preço dos dois que ficaram:

- **`lumen`** registra `PreToolUse` com matcher `Grep|Bash`: dispara a cada chamada dessas, e
  injeta uma linha de recomendação no contexto junto do resultado. Uma sessão com milhares de
  `Bash` paga isso milhares de vezes.
- **`semgrep`** registra hook em `Write`, `Edit` e `Bash`, e um `SessionStart` assíncrono.

São 26 MB e 15 MB de RSS — mas o custo real deles é latência por chamada e tokens por chamada.
Ficam porque são locais e servem ao repositório; medir esse custo em CPU e em tokens é trabalho
que este documento não fez.

## 9. A outra metade: as sessões que ninguém abriu

O corte reduz o preço de cada stack. Falta dizer quantas stacks existem, e por quê.

`claude daemon run --origin transient` mantém sessões **`bg-spare` pré-aquecidas** — sessões
prontas para receber um subagente ou uma Task sem pagar o tempo de boot. Elas são invisíveis
na interface e completas por dentro:

| processo | descendentes | RSS da árvore |
|---|---|---|
| daemon (712424) | 50 | 1.099 MB (+1.675 MB em swap) |
| `bg-pty-host` 712448 | 21 | 486 MB |
| `bg-spare` 712487 | 20 | 431 MB |
| `bg-pty-host` 813095 | 1 | 177 MB |
| `bg-spare` 813196 | 0 | 99 MB |

A sessão que hospeda o daemon (692624) somava 75 descendentes, 1.304 MB residentes e 2.493 MB
em swap — mais do que qualquer janela real do dono.

Isso não é defeito: é o que faz um subagente começar a trabalhar em segundos. Mas o preço do
pré-aquecimento é proporcional ao tamanho da stack, e era justamente a stack que estava
inflada. Com 10 servidores stdio, cada spare guardava ~430 MB à toa; com a stack enxuta, o
mesmo mecanismo custa uma fração. **Reduzir a stack corrige o spare sem desligar o spare** —
que é o que se quer, porque a sessão trabalha com muitos agentes.

Vale um ajuste de escala à parte: `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=512` e
`MAX_SUBAGENTS_PER_SESSION=20000` no `~/.claude/settings.json` são tetos altos por decisão do
dono (não há teto de agentes neste projeto). Eles não criam spares sozinhos, mas definem até
onde a multiplicação pode ir quando uma onda grande roda — mais uma razão para a stack por
sessão ser barata.

## 10. Resultado medido

Mesma ferramenta, mesma máquina, sessão nova antes e depois do corte:

| | antes | depois |
|---|---|---|
| processos na árvore da sessão | 24 | **2** |
| RSS da sessão | 1.883 MB | **28 MB** |
| órfãos ao fechar a janela | 0 | 0 |
| containers Docker criados | +1 | **0** |

Os dois processos que restam são `lumen` (14 MB) e o hook do `semgrep` (15 MB) — os dois que
o critério mandou manter, e que juntos custam menos que 2% do que a stack custava.

**Uma janela do Claude Code passou de 1,88 GB para 28 MB — 98,5% a menos.** Com cinco janelas
e os spares do daemon, é da ordem de 2,4 GB de RSS e boa parte dos 4,4 GB de swap que deixam
de ser cobrados, à medida que as sessões reciclam. Config não encolhe sessão viva: as que já
estavam abertas mantêm o que subiram até serem reiniciadas.

## 11. Segunda fase: o que o tmux guardava

Depois do corte, o dono observou que só tinha **uma** janela aberta e que o resto devia ser
órfão. Estava certo, e a medição explicou por quê.

### O que se mediu

`tmux list-clients` devolvia **um único cliente**, na sessão em que ele estava. E
`tmux list-sessions` devolvia **18 sessões**, 17 delas sem cliente nenhum — quatro segurando
Claude Code inteiro, com 2h a 3h de vida e paradas desde 13:25–14:19.

Nenhuma era órfã no sentido do sistema operacional: todas tinham pane vivo e PPID válido. Elas
eram órfãs no sentido que importa — **ninguém do outro lado**.

### A causa: dois comportamentos corretos que se somam mal

1. **O tmux sobrevive ao fechamento do terminal.** É o propósito dele: você fecha a janela,
   a sessão continua, você reata depois. Fechar o WezTerm não encerra nada lá dentro.
2. **O launcher cria uma sessão nova por janela.** `~/start-ai-terminal-claude.sh` monta o nome
   como `ai-$(date +%Y%m%d-%H%M%S)-$$` — único por abertura. Nunca reaproveita.

Cada janela aberta e fechada deixa, portanto, uma sessão viva e completa para trás. Em quatro
dias: 18 sessões, e o Claude Code de cada uma com sua pilha de MCP.

### O reaper que existia e não via isso

Já havia um `ai-orphan-reaper.timer` rodando a cada 15 minutos. Às **15:36 ele reportou
"nenhum órfão"** — com as quatro sessões penduradas. Três motivos, no código:

- só considera órfão processo com **`PPID == 1`**, e nenhuma delas estava assim;
- **protege qualquer processo em pane de sessão tmux "viva"** — sem distinguir *attached* de
  *detached*, que é exatamente a diferença entre "o dono está aqui" e "o dono foi embora";
- **protege incondicionalmente toda a árvore de `claude daemon run`**.

Essa última virou o achado mais caro. Ao encerrar as quatro sessões, o `claude daemon run`
criado por uma delas **sobreviveu ao pai e reparentou para o init**: 50 descendentes, 1.242 MB.
E ao receber `SIGTERM`, o daemon morreu mas seus `bg-pty-host` e `bg-spare` **não** — ficaram
vivos, com PPID 1, e um deles só cedeu a `SIGKILL`. Encerrar a raiz não basta; é preciso
percorrer a subárvore com escalada.

### Resultado

| | antes | depois |
|---|---|---|
| sessões tmux | 18 | **1** |
| processos Claude Code | 10 | **1** |
| RAM em uso | 13.802 MB | **7.720 MB** |
| RAM disponível | 6.077 MB | **12.159 MB** |
| containers Docker | 9 | 1 |

Cada encerramento foi verificado antes: CPU ociosa, nenhum processo de trabalho na árvore, e —
no caso do daemon — a prova de que ele não servia a sessão do dono, já que só os próprios
filhos tinham o `control.sock` aberto e a sessão viva usa socket próprio.

### `ai-session-reaper`, e por que não um hook de tmux

A correção estrutural é `~/.local/bin/ai-session-reaper`, que cobre o caso que o outro não vê:
sessão **detached e parada**. Ele encerra sessão `ai-*` sem cliente, sem `@ai_keep`, sem
processo de trabalho em voo e sem atividade há mais de 90 min (15 min se for casca vazia); e
encerra `claude daemon run` cujo pid criador — extraído do JSON em `--spawned-by` — não existe
mais.

### O relógio que não era relógio

A primeira versão decidia por `session_activity` do tmux, com o raciocínio de que o CPU não
serve — um Claude esperando resposta da API fica em ~0% e pareceria ocioso — e de que o pane de
um processo ativo repinta, renovando o campo.

A segunda metade estava errada. `tools/check-tmux-activity-clock` põe uma sessão **detached**
imprimindo uma linha por segundo e compara:

```
após 40s de output contínuo numa sessão DETACHED:
  session_activity avançou 0s
  window_activity  avançou 40s
```

`session_activity` mede **interação de cliente** — teclado, attach. Numa sessão sem cliente,
que é a população-alvo inteira do reaper, ele fica congelado no instante do detach. A "carência
de 90 minutos" nunca foi carência: era um cronômetro de execução disparado quando o dono fecha
a janela, correndo enquanto o Claude trabalha.

E há um agravante que nenhum campo resolve: **decidir por uma amostra instantânea é roleta**.
Entre dois tool calls, os únicos filhos vivos de um Claude são servidores de MCP — todos
excluídos por desenho —, então a sessão parece parada justamente quando está trabalhando. Bastava
a varredura de 15 em 15 minutos cair nesse intervalo.

Isso mataria exatamente o hábito que o `CLAUDE.md` manda ter: Claude trabalhando continuamente
com a janela fechada. O timer foi **desarmado 13 minutos depois de instalado**, antes de encerrar
qualquer sessão real.

### O desenho que substituiu: observações, não relógio

A correção não é trocar de campo — é parar de ser stateless. Cada execução grava uma
**observação** por sessão em `~/.local/state/ai-session-reaper/`, e só se encerra quando N
observações consecutivas, cobrindo a carência inteira, todas disserem "parada". Quatro sinais
independentes, e basta um acusar vida:

| sinal | o que detecta | calibração medida |
|---|---|---|
| hash do `capture-pane` | a tela mudou — streaming de resposta muda | binário |
| ΔCPU da árvore | trabalho de verdade, por **taxa** | piso do ocioso: **1,50 jiffies/s**; limiar em 8 |
| filhos de trabalho | processo que não é MCP nem shell parado | binário |
| `window_activity` | output no pane | avança 40s em 40s de output; **0 em 120s** com TUI ocioso |

A linha do CPU custou uma iteração e é a mais instrutiva. O limiar começou absoluto — "mais de
2 jiffies entre observações é vida" — e acusava vida em **todas** as amostras, então a sessão
nunca era encerrada. `tools/check-claude-idle-cpu` mediu o piso de um Claude parado no prompt:

```
  t= 15s  Δjiffies=17   taxa=1.13 jiffies/s
  t= 30s  Δjiffies=45   taxa=1.50 jiffies/s
  t= 45s  Δjiffies=68   taxa=1.51 jiffies/s
  t= 60s  Δjiffies=90   taxa=1.50 jiffies/s
```

**1,5% de um núcleo, continuamente, sem fazer nada** — event loop, timers, hooks. Um limiar
absoluto nunca poderia funcionar contra um piso desses; o que discrimina é a taxa. O corte
ficou em 8 jiffies/s, mais de cinco vezes acima do ruído de fundo.

Um Claude trabalhando escapa em qualquer observação. Um parado só é encerrado depois de três
delas concordarem, ao longo de mais de uma hora.

A carência de 90 minutos continua, e não é arredondamento: o `ScheduleWakeup` do `/loop` é
limitado a 3600 s, então uma sessão em loop pode ficar legitimamente muda por uma hora.

Um hook `client-detached` foi considerado e descartado: marcar a hora do detach seria a mesma
armadilha do `session_activity`, com outro nome.

### A pergunta que decidia tudo, e as duas vezes que a medi

Com o desenho por observações de pé, restava um caso que nenhum sinal parecia alcançar. Um
**subagente do Claude Code não é um processo** — roda dentro do TUI. Medido nesta própria
sessão, com um agente crítico ativo:

```
processos de trabalho detectados:   0
taxa de CPU da árvore:              6 jiffies/s   <- ABAIXO do limiar de vida (8)
```

Uma sessão com cinco agentes trabalhando seria lida como parada. Tentei a rede como sinal e
ela foi **refutada pelo inverso**: Claude ocioso mantinha **73** conexões estabelecidas e o
trabalhando, **7** — a contagem mede idade da sessão, não atividade.

Sobrava perguntar se o TUI **com o spinner rodando** repinta a tela. Eu havia medido o TUI
*parado no prompt* (fica mudo por 120s), nunca o *aguardando resposta* — dois estados que,
para o sistema operacional, são quase idênticos.

A primeira execução dessa medição respondeu **não**, e eu quase publiquei a conclusão de que
nenhum sinal local serve. Estava lendo string vazia: usei `-t "=$sessao"` no `capture-pane`,
que devolve nada, e o "hash que nunca muda" era `e3b0c442…` — o sha256 do vazio.

Corrigido, o resultado inverteu:

```
  t=  5s  window_activity MUDOU (Δ35s)  hash MUDOU
  t= 30s  window_activity MUDOU (Δ60s)  hash MUDOU
  t= 60s  window_activity MUDOU (Δ86s)  hash MUDOU
```

**Um Claude gerando resposta repinta continuamente.** `window_activity` acompanha o relógio de
parede e o hash muda em toda amostra, enquanto o TUI parado fica mudo. Os dois estados são
distinguíveis, e o repaint alcança exatamente o caso que o CPU e a contagem de processos não
veem.

### A armadilha que causou três bugs no mesmo dia

O prefixo `=` no target do tmux pede match exato de nome e parece a escolha segura em qualquer
comando. Metade deles não o entende — e não devolve erro, devolve **string vazia**:

| funciona | quebra em silêncio |
|---|---|
| `list-panes`, `has-session`, `kill-session` | `show-options`, `capture-pane`, `display-message` |

Custou o `@ai_keep` do dono ser lido como inexistente (opt-out ignorado sem aviso), o hash da
tela do reaper ser sempre o do vazio, e a medição acima concluir o oposto do real. Os três
falharam para um valor perfeitamente utilizável — "opção não definida", "hash válido" — e por
isso nenhum acusou.

### O filtro que apagava trabalho

A classificação de "isto é só um MCP" começou como lista de nomes de produto
(`convex|playwright|semgrep|lumen`…), casada como substring na linha de comando inteira. O
red-team plantou três iscas e o dry-run as engoliu:

```
ENCERRARIA probe-w-semgrep — casca detached   (pane: python3 … semgrep scan /opt/wiki, VIVO)
ENCERRARIA probe-w-play    — casca detached   (pane: python3 … suite playwright, VIVO)
ENCERRARIA probe-w-docker  — casca detached   (pane: python3 … convex export, VIVO)
```

Um `semgrep --config auto` de verdade, um `npx playwright test`, qualquer comando com essas
palavras no argumento — tudo virava "MCP". E o agravante: sem trabalho detectado, a sessão era
rebaixada de "claude" para "casca", trocando a carência de 90 min pela de 15.

Hoje a classificação é por **parentesco e caminho**: um MCP é filho direto do TUI do Claude,
executado de `~/.npm/_npx/`, `~/.cache/uv/`, `~/.claude/plugins/` ou por `docker run` — e a
subárvore dele inteira segue junto. Nome de produto no argv não classifica nada.

### O que o teste pegou antes do `--apply`

`tools/check-ai-session-reaper` monta sessões sintéticas para os seis casos que importam. Na
primeira execução, **dois falharam** — e um deles teria destruído trabalho:

- uma sessão rodando `sleep 300` foi marcada para encerrar. `tmux new-session "comando"` executa
  o comando **como o próprio pane**, sem filho algum, e a varredura só olhava descendentes;
- a sessão com Claude parado *não* foi marcada, porque o filtro de MCP por nome deixava escapar
  dois processos — o python do `browser-use` e o watchdog do `chrome-devtools` —, e eles eram
  lidos como trabalho em voo.

O segundo consertou-se trocando a lista de nomes por classificação pelo **caminho** de onde o
processo é executado (`~/.npm/_npx/`, `~/.cache/uv/`, `~/.claude/plugins/`, `docker run`).
Nome de pacote muda a cada versão; o diretório, não.

## 12. O que o corte **não** resolve

- **`gopls` é o maior processo da máquina**: 980 MB residentes + 274 MB em swap, ~10% da RAM
  total. Fica, porque o projeto é Go — mas é honesto dizer que ele pesa mais que qualquer MCP.
- **O Chrome do dono** ocupa ~2 GB em renderers. Não é do Claude Code e não se toca.
- **Config não encolhe sessão viva.** O ganho aparece em sessão nova; as atuais liberam quando
  reciclarem.

## 13. A terceira frente: o orçamento de descrições de agentes (2026-09-08)

O mesmo excesso de plugins cobra num segundo lugar, e este não aparece em RSS nenhum: o bloco
`Available agent types` do system prompt. O CLI avisou:

```
Agent descriptions are over the 15.0k-token limit (~21.4k tokens)
 · ask Claude to trim agent descriptions in .claude/agents/
```

### A segunda metade do aviso aponta para o lugar errado

`ask Claude to trim agent descriptions in .claude/agents/` é **string fixa** do binário, não
diagnóstico. A conta real está em `Dfe` (Claude Code 2.1.263, extraído do bundle):

```js
Dfe(x) {
  if (!x) return 0;
  return x.activeAgents
    .filter(a => a.source !== "built-in")
    .reduce((soma, a) => soma + tokens(`${a.agentType}: ${a.whenToUse}`), 0);
}
Efe = 15000
```

Ela soma **todo** agente não built-in — os de plugin junto com os do repo. Medido no momento do
aviso: 288 agentes, 80.307 chars, ~21,4k tokens. Os cinco de `.claude/agents/` respondiam por
2.019 chars, ~538 tokens: **2,5% do total**. Cortar as descrições deles não removeria o aviso;
faltariam 12x. É a mesma classe de erro que a seção 5 catalogou — o instrumento mostrando a
coisa ao lado.

### A alavanca, e por que ela cabe no settings do projeto

O binário documenta a precedência: `user < project < local`, merge por `Object.assign`. Então
`"enabledPlugins": {"<nome>@<marketplace>": false}` em `.claude/settings.json` **sobrepõe** o
`true` de `~/.claude/settings.json` sem tocar nos outros projetos da máquina. Nenhum plugin
instalado declara `dependencies`, então o `false` pega em todos — a cláusula "a plugin required
by an enabled dependent is enabled regardless of this value" não se aplica aqui.

Não existe desligar agente **individual**: o settings tem `skillOverrides`, não tem
`agentOverrides`. Plugin inteiro é a única granularidade — e é por isso que o critério de corte
não pode olhar só para os agentes.

### Critério de corte

`false` desliga o plugin **inteiro**: hooks, skills, commands e MCP junto com os agentes. Só
sai plugin cujo conteúdo inteiro é irrelevante a este repo, ou cujo único conteúdo são agentes.

| saiu (51) | por quê |
|---|---|
| `ruflo-*` (36 plugins) | swarm, trading, IoT, neural, market data — nada toca o portal; o MCP já falhava com `CONNECT_TIMEOUT` |
| `taskplane`, `taskmaster`, `holocron`, `catalyst-dev`, `handbook*` | metodologias de task/planejamento que o repo não usa; o contrato daqui é o `CLAUDE.md` |
| `fable-agents` (só agentes), `full-stack-orchestration`, `api-scaffolding`, `agent-teams` | cloud, k8s, Terraform — o CLAUDE.md proíbe nuvem de terceiros |
| `honeycomb` | observabilidade SaaS proprietária, mesma proibição da seção 6 |
| `activecampaign`, `nimble`, `pixeltable`, `storm`, `claude-obsidian`, `academic-research-skills`, `probe` | CRM, pesquisa de mercado, vault, papers — fora do escopo jurídico |

| ficou | por quê |
|---|---|
| `ecc` | maior contribuinte isolado (3,9k tokens), mas carrega o GateGuard e os guardas de escrita **vivos nesta máquina**, e `go-reviewer`/`go-build-resolver`/`python-reviewer` servem ao repo |
| `oh-my-claudecode`, `context-mode`, `mem0` | MCP ativo |
| `ringmaster`, `caveman`, `superpowers-optimized`, `agent-skills`, `stem` | hooks ativos |
| `claude-seo` | SEO é o negócio do portal |

### Resultado medido

| | agentes | chars | tokens |
|---|---|---|---|
| antes | 288 | 80.307 | ~21.415 |
| depois | 136 | 31.672 | ~8.446 |

Folga de ~6,5k tokens contra o teto. A razão 3,75 chars/token foi **calibrada**, não estimada:
80.307 ÷ 3,75 = 21.415, que é exatamente o "~21.4k" que o CLI reportou.

### O instrumento

`tools/check-agent-description-budget` fixa a medição — reproduz o merge dos três settings, soma
`name: description` do frontmatter de cada agente e reprova acima do teto. É read-only, irmão de
`tools/generate-claude-mcp-trim` (que corta por RAM e escreve). Provado por mutação: com o teto
em 100 ele sai 1 e imprime `ACIMA DO TETO`.

Ele deduplica por `name` entre `.claude/agents/` e `~/.claude/agents/`, porque o projeto sombreia
o usuário — `investigador` existe nos dois e o CLI carrega um só. Sem isso o instrumento contaria
137 onde o CLI vê 136.

### Duas ressalvas

As 50 remoções de `enabledPlugins` que já estavam na worktree quando esta frente começou são
**no-op**: os 50 continuam `true` em `~/.claude/settings.json`, conferido chave a chave contra
`HEAD:.claude/settings.json`. `gopls-lsp`, `superpowers` e `semgrep` seguem ativos pelo settings
do usuário — não foram desligados por acidente.

> **Superado, medido em 2026-09-23:** `enabledPlugins` dos dois settings só tem `caveman@caveman` — `python3 -c 'import json;print(json.load(open(P)).get("enabledPlugins"))'` sobre `~/.claude/settings.json` e `/opt/wiki/.claude/settings.json` devolve `{'caveman@caveman': True}` nos dois (2026-09-23 08:16:50 -03). `gopls-lsp`, `superpowers` e `semgrep` saíram na limpeza de 2026-09-08 (decisão e motivo em [`CLAUDE_CODE_PLUGINS_2026-09-08.md`](CLAUDE_CODE_PLUGINS_2026-09-08.md) §5). `claude plugin list --json` confirma: às 08:17 -03, `caveman@caveman` é o único plugin de escopo `user` e o único de escopo `project`; as outras 93 entradas da lista são de escopo `synced` — sincronização de plugins do claude.ai, que não passa por `enabledPlugins` e se fecha com `syncClaudeAiPlugins: false` (`docs/ops/IDE_VSCODIUM_20260923.md` §6).

E vale aqui o mesmo da seção 12: **config não encolhe sessão viva**. O orçamento é lido no boot
do CLI; a confirmação de que o aviso sumiu depende de sessão nova.
