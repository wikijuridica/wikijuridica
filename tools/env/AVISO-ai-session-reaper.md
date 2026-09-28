# ai-session-reaper — REARMADO em 2026-08-19 17:17, após o segundo passe adversarial

Linha do tempo: instalado às 16:03, **desativado às 16:16** (o relógio em que se apoiava estava
congelado), rearmado às 16:54, **desativado de novo às 17:10** — o segundo passe adversarial
demonstrou dois caminhos que matavam trabalho — e **rearmado às 17:17**, com os nove achados
corrigidos e a suíte em 18 casos verdes, inclusive sob concorrência real com o próprio timer.

Nenhuma sessão foi encerrada indevidamente em nenhum momento: os dois desarmes aconteceram
antes de qualquer execução sobre sessão detached real.

## Os dois caminhos que matavam trabalho (fechados em 17:11)

**Resíduo de crash virava série válida.** A gravação era append → truncate → regrava; morrer
entre os dois comandos deixava `[1, 1, 0]`, e a contagem por `grep -c ' 1$'` somava linhas NÃO
consecutivas — o red-team obteve `ENCERRARIA … cobrindo 117min` com 63s de evidência real,
atravessando uma observação em que o arquivo registrava a sessão VIVA. Escrita agora é atômica
(tmp + `mv`) e a contagem lê do fim para trás, parando na primeira linha que não seja parada.

**`claude -p` era invisível.** `e_claude_tui` isentava qualquer cmdline começando em `claude`,
em qualquer ponto da árvore — mas `claude -p 'tarefa' > saida.json` é como `ai-pane run` e os
subagentes se materializam. Sem filhos, CPU sob o limiar, tela quieta: demonstrado a 4,8
jiffies/s sendo encerrado. `-p`, `--print` e `--output-format` marcam trabalho headless.

## Os outros sete

- **`flock` global atravessava `--state-dir`**: suíte e timer disputavam o mesmo arquivo e o
  perdedor saía MUDO com exit 0, que a suíte lia como falha. Era a causa dos vermelhos
  intermitentes atribuídos a "variabilidade de startup" — uma explicação plausível e errada,
  que fez a investigação parar no lugar errado.
- **Sem espaçamento mínimo**: três observações em nove segundos formavam série. Agora 300s.
- **`pgrep -f 'claude daemon run'`** casava a frase em qualquer cmdline. Ancorado no executável
  mais o primeiro argumento.
- **Pré-kill revalidava só `attached`**, não vida. Agora refaz os três sinais e aborta.
- **`window_activity` lia só a janela ativa** — cego para `ai-pane grid`. Agora o máximo de
  todas as janelas.
- **Dump sem `-S -`**: perdia o scrollback, que era o ponto de guardá-lo.

## O furo que derrubou a primeira versão

Ela usava `session_activity` do tmux como medida de "quando esta sessão trabalhou
pela última vez", supondo que o pane de um processo ativo repinta e renova o campo.

**Medido** (`tools/check-tmux-activity-clock`), sessão detached imprimindo uma
linha por segundo:

```
após 40s de output contínuo:
  session_activity avançou 0s
  window_activity  avançou 40s
```

`session_activity` mede interação de cliente — teclado, attach. Numa sessão sem
cliente, que é a população-alvo inteira, fica congelado no instante do detach. A
"carência de 90 minutos" era um cronômetro de execução disparado quando o dono
fecha a janela, correndo enquanto o Claude trabalha.

Agravante que nenhum campo resolve: decidir por **uma amostra instantânea** é
roleta. Entre dois tool calls, os únicos filhos vivos de um Claude são servidores
de MCP — excluídos por desenho —, então a sessão parece parada justamente quando
está trabalhando.

## O que a segunda versão faz

Parou de ser stateless. Cada execução grava uma **observação** por sessão em
`~/.local/state/ai-session-reaper/`; só encerra quando `MIN_OBS` observações
consecutivas, cobrindo a carência inteira, todas disserem "parada". Quatro sinais,
e basta um acusar vida:

| sinal | detecta |
|---|---|
| hash do `capture-pane` | a tela mudou (streaming de resposta muda) |
| ΔCPU da árvore | `utime+stime` avançaram (tool calls acumulam) |
| filhos de trabalho | processo que não é MCP nem shell parado |
| `window_activity` | avança com output; fica em 0 por 120s com TUI ocioso (medido) |

Outras correções da mesma rodada, todas vindas da revisão adversarial:

- **MCP por parentesco e caminho, nunca por nome.** A v1 casava
  `convex|playwright|semgrep|lumen` como substring da linha inteira, então um
  `semgrep --config auto` de verdade virava "MCP" — e a sessão ainda era rebaixada
  para a carência curta. Hoje: filho direto do TUI, executado de `~/.npm/_npx/`,
  `~/.cache/uv/`, `~/.claude/plugins/` ou `docker run`, com a subárvore junto.
- **Daemon: falha fechado.** Exige `PPID==1` **e** criador declarado em
  `--spawned-by` comprovadamente morto. Sem a flag, protege. A v1 matou um
  daemon-isca do red-team na primeira execução real do timer.
- **`flock`** contra execuções sobrepostas.
- **Releitura de `session_attached` e `@ai_keep` imediatamente antes do kill** — a
  decisão pode ter minutos quando a ação chega.
- **Ledger** em `ledger.jsonl` e `tmux capture-pane` do tail de cada pane gravado
  **antes** de encerrar: a evidência do que a sessão fazia não morre com ela.
- **Teto de 3 encerramentos por execução** e invalidação da série em salto de
  relógio maior que 1 h — sem isso, um suspend/resume faria todas as sessões
  estourarem a carência no mesmo tick.
- **`show-options` sem o prefixo `=`**: com ele o tmux devolve vazio para
  user-options, e o `@ai_keep` do dono era silenciosamente ignorado.

## Furo aberto: subagente não aparece como processo

Medido em 2026-08-19 16:36, nesta mesma sessão, com um subagente crítico **ativo**:

```
filhos diretos do processo Claude: só servidores de MCP e shells de comando
                (nenhum processo corresponde ao subagente em execução)
taxa de CPU da árvore: 6 jiffies/s     <- ABAIXO do limiar de vida (8)
conexões estabelecidas com a API: 7
```

Um subagente do Claude Code **roda dentro do TUI**, não como processo separado. Logo:

- `trabalho_no_pane` devolve **zero** para uma sessão com cinco agentes trabalhando;
- o ΔCPU pode ficar **abaixo do limiar**, porque o trabalho é LLM-bound — a máquina
  espera a API, não calcula.

Sobram o hash da tela e o `window_activity`, e nenhum dos dois ajuda se a sessão está
detached e o Claude está aguardando uma resposta longa sem repintar.

**Consequência potencial**: o predicado poderia marcar como parada uma sessão com trabalho
real em voo — o mesmo mecanismo da falha original, por outro caminho.

**FECHADO em 2026-08-19 16:46, favoravelmente.** `tools/check-claude-working-repaint` mandou
uma pergunta a um Claude e observou o pane enquanto ele respondia:

```
  t=  5s  window_activity MUDOU (Δ35s)  hash MUDOU
  t= 30s  window_activity MUDOU (Δ60s)  hash MUDOU
  t= 60s  window_activity MUDOU (Δ86s)  hash MUDOU
```

Um Claude gerando resposta **repinta continuamente** — `window_activity` acompanha o relógio
de parede e o hash da tela muda em toda amostra. O TUI parado no prompt fica mudo por 120s.
Os dois estados são perfeitamente distinguíveis, e o repaint alcança justamente o caso que o
CPU e a contagem de processos não veem.

Ressalva registrada: a primeira execução desta medição concluiu o OPOSTO, e estava lendo
string vazia por causa do prefixo `=` no `capture-pane` (ver a seção da armadilha no
cabeçalho do script). O hash "constante" era o sha256 do vazio.

A pista da rede foi testada e **refutada, pelo inverso do esperado**:

```
Claude OCIOSO (sessão nova):      73 conexões  (76, 74, 73, 73, 72, 71)
Claude TRABALHANDO com subagente:  7 conexões
```

O ocioso mantém dez vezes mais. A contagem mede **idade da sessão** — uma recém-aberta
abre dezenas de conexões no startup, que vão se fechando — e não atividade. Porta fechada,
registrada em `tools/check-claude-idle-net`.

Baixar o limiar de CPU de 8 não resolve sozinho: o piso do ocioso é 1,50 jiffies/s e a
sessão trabalhando media 6, então a faixa útil é estreita e o ruído de qualquer hook
a atravessa.

## Gate de rearme — FECHADO

1. `tools/check-ai-session-reaper` verde nos 12 casos (inclui os 4 do red-team). **Feito** —
   mas a suíte não cobre o furo do subagente descrito acima; falta um caso para ele.
2. Teste de adoção com um daemon real — **não reproduzível**: depois de encerrar o daemon
   órfão às 16:00, nenhum outro nasceu, mesmo com subagentes rodando a tarde inteira e
   `/tmp/cc-daemon-1000/*/control.sock` vazio. O daemon parece existir só para servir os
   `bg-spare` pré-aquecidos, que não voltaram. O caminho do daemon no reaper fica, portanto,
   **não exercitado em condição real** — mas é conservador por construção: exige `PPID==1`,
   `--spawned-by` legível e criador provadamente morto, protegendo em qualquer dúvida.
3. Um passe de crítica adversarial sobre o predicado novo.
3b. **Corrigir o `ai-process-reaper` antigo**, que era o outro lado do mesmo bug: ele protegia
   TODA árvore de `claude daemon run` incondicionalmente. Feito, com a mesma regra do novo
   (PPID==1 + criador provadamente morto + falha fechado), e provado por
   `tools/check-ai-process-reaper-daemon`: isca com criador morto vira alvo, isca com criador
   vivo é protegida.
4. `systemctl --user enable --now ai-session-reaper.timer` — **feito às 16:54**.

Enquanto isso: `ai-orphan-reaper.timer` (o antigo, de PPID==1) segue ativo, o
script novo é utilizável em dry-run — que é o padrão dele — e o acúmulo recomeça
a uma sessão por janela fechada, o que dá folga de sobra para fechar o gate.
