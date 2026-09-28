# Fila do cérebro — casos medidos e parágrafos superados

> Movido de `.claude/rules/fila-do-cerebro.md` em 2026-09-23. A rule passou do teto de 6.000
> caracteres que `tools/check-modo-operacional` cobra (T1) e foi condensada para
> veredito, ordem dos passos e comando de medição (plano
> `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8, frente 4, item 6). **Nada foi
> apagado:** a seção "Texto integral" abaixo é a rule exatamente como estava no commit
> `06fe635b`, sem o frontmatter `paths:` (que continua na rule). Os casos medidos, as
> tabelas de tempo e os parágrafos marcados SUPERADO ficam aqui como evidência; o que
> vale como ordem é a rule.
>
> Este arquivo não carrega em sessão nenhuma: é lido quando a rule manda ou quando
> alguém precisa do número que sustentou o veredito.

## O que só está aqui

- **2026-09-16** — esquema v3: as 5 `embed_pagina` em `erro` eram 5 de 5 lápides.
- **2026-09-16** — o caso que originou a cura por causa: `cerebro reabrir --tipo embed_pagina` reabriu 5 lápides, que falharam em < 60 s; as "lápides ambulantes" travaram por seis dias a ativação do índice que já cobria 11.161 de 11.161 páginas.
- **2026-09-16** (`aadbb67d`) — a órfã em `executando`: contenção de banco passou a virar pausa, e o reinício que devolvia o trabalho deixou de acontecer (14 tarefas com `recuperacoes > 0` na fila viva).
- **2026-09-16** — travamento permanente do índice por texto que volta a uma versão anterior (`/noticias/tst-20260901/`).
- **2026-09-16** (`197ea62b`) — 40 `extrair_dispositivos` curadas voltaram com prioridade −5/−6 e passaram na frente de 7 notícias; 37 linhas violaram a invariante entre faixas.
- **2026-09-16** — escala: `estado<>'erro'` 1,439 s (SCAN) contra `estado IN (...)` 0,116 s sobre 65.249 linhas; `SELECT DISTINCT modelo` 38,279 s → 0,017 s; contagens por estado 1,624 s → 0,017 s.
- **2026-09-09** — custo da troca de modelo: `load_duration` de 21.121, 48.621 e 37.221 ms, maior que o prefill em duas de três chamadas.
- **2026-09-16** — faixas: as prioridades −5…−11 ficam SUPERADAS (`medir_modelo` em −10 parado atrás de 8.961 extrações).
- **2026-09-16, SUPERADO em parte em 2026-09-17** — `CargaMaxPadrao` 12 → 0 (7 min de redação perdidos às 16:42 com 13 pendentes) e "o `LockPesado` FICA"; em 2026-09-17 o `LockPesado` também saiu do padrão (134 min de produção parada em 22,5 h, nenhum ganho de bancada).
- **2026-09-17** — reivindicação: `idx_tarefa_elegivel` de 113-125 ms para 0,05 ms; o pior caso O(P) por transição de faixa ficou nomeado e não fechado (rota O(k) medida: 0,31 ms).
- **2026-09-16** — prazo por tipo: lote de `redigir_noticia` cortado em `15m0.01s` = 3 × 300 s, no meio de um prefill de 5.950 tokens.
- **2026-09-08** — o par 14b + 9b = 16 GB que motivou a guarda de bytes residentes.

## Texto integral da rule até 2026-09-23 (commit `06fe635b`)

# Fila do cerebro — a identidade inclui o modelo, e trocar de modelo custa load

Memoria de origem: `ollama-troca-de-modelo-custa-load.md` (a secao do custo de
load). A fisica do host e o tuning vivo ficam em `ollama-e-earlyoom.md`.

`internal/cerebro/fila.go`. A identidade da tarefa inclui o **modelo**, e pagina
ou acordao com o mesmo `texto_sha256` nunca e' recomputado. Colunas de `tarefa`:
`tipo`, `chave`, `impressao`, `prioridade`, `modelo`, `payload`,
`custo_estimado_tokens`, `keep_alive`, `estado`
(`pendente|executando|concluida|erro`), `tentativas`, `worker`,
`superada_em`, `recuperacoes`, `falhou_com`.

## Esquema v3 (2026-09-16): duas colunas, e o `CHECK(estado IN ...)` intacto

- **`superada_em`** e a LAPIDE: tarefa em `erro` cujo trabalho ja foi feito por
  uma irma que concluiu ANTES do erro ser gravado. Medido: as 5 `embed_pagina`
  em erro sao 5 de 5 lapides. Sem ela o gate nasce com 5 vermelhos permanentes.
  `Fotografia().Erros` ja desconta as lapides; `UltimosErros` as exclui.
- **`recuperacoes`** conta as voltas de `executando` por MORTE DO WORKER.
  `Recuperar` RESTITUI a tentativa (kill -9 nao e culpa do trabalho), mas so ate
  `TetoDeRecuperacoesSemCulpa` = 6 — acima disso a tarefa e a suspeita e volta a
  caminhar para o `erro`.
- Nenhum estado novo, de proposito: por um valor em `estado` que o `CHECK` nao
  lista exigiria recriar a tabela, e um binario revertido passaria a falhar em
  toda escrita. `ALTER TABLE ADD COLUMN` nao tem esse problema.

## Esquema v4 (2026-09-16): `falhou_com`, e a cura que decide por CAUSA

O `superada_em` e o `recuperacoes` acima continuam valendo. A v4 acrescenta
**uma** coluna, pela mesma via (`ALTER TABLE ADD COLUMN`, `CHECK(estado IN ...)`
intacto):

- **`falhou_com`** e a identidade do BINARIO que gravou o `erro` — SHA-256 de
  `/proc/self/exe`, cacheado uma vez por processo (`CarimboDoBinario`).
  `os.Executable()` **nao serve**: o deploy troca o binario por `mv`, entao o
  caminho passa a apontar para o binario novo enquanto o processo roda o antigo.
  `debug.ReadBuildInfo()` **tambem nao**: a worktree e permanentemente suja, e
  dois binarios com codigo diferente trazem a mesma
  `v0.0.0-…-498ece3708e4+dirty`.

### O predicado da cura, e por que ele TERMINA

```
curavel  <=>  estado='erro'  E  superada_em=''  E  falhou_com <> carimbo atual
```

Reexecutar so pode mudar o resultado se a ENTRADA ou o CODIGO mudarem. A entrada
e congelada em `impressao` por construcao (insumo novo = LINHA nova). Sobra o
codigo. Uma linha reaberta que torne a falhar sai carimbada com o binario atual
e **nao volta a ser reaberta ate o codigo mudar** — que e exatamente quando a
cura pode funcionar.

**`tentativas=0` nao e freio**: zerar um contador e uma cura aplicavel infinitas
vezes. Era o que `Reabrir` fazia.

### Quem executa a cura: o BOOT de `cerebro servir`, nao um timer

`ReabrirCuraveis` roda em `servir`, logo depois de `Recuperar` e
`MarcaLapidesDeIrmaConcluida`. O boot e **o unico instante em que o predicado
pode mudar**, porque o carimbo so muda quando o binario troca, e trocar o
binario reinicia o processo. Um timer de 15 min faria a mesma pergunta 96 vezes
por dia para ouvir a mesma resposta 95 vezes. `cerebro reabrir --curaveis` chama
**a mesma funcao** — um predicado, dois acionadores.

### O caso medido que originou tudo (2026-09-16)

`cerebro reabrir --tipo embed_pagina` devolveu **"reabertas: 5"** e as cinco
falharam em **menos de 60 s**, com `parede=0s` e `modelo=` vazio — sem tocar o
Ollama. As cinco eram **lapides**: cada uma com irma `concluida` carregando
exatamente a impressao que o worker calcula hoje, concluida entre 02:37 e 04:40
de 2026-09-10, ANTES de o erro ser gravado as 08:24.

E como o `UPDATE` de `Reabrir` **nao limpava `superada_em`**, o que ficou foram
cinco **LAPIDES AMBULANTES** — `pendente` com carimbo de lapide. Elas contam em
`Pendentes`, que e a condicao de `AtivaIndiceSeCompleto`: o indice ja cobria as
**11.161 de 11.161** paginas do acervo e a ativacao ficou travada por trabalho
pronto havia seis dias. **Uma causa, tres sintomas.**

Correcoes: `Reabrir` ganhou `AND superada_em=''` (sem flag que desligue);
`LapidesAmbulantes`/`SanaLapidesAmbulantes` acham e desfazem a contradicao no
boot; e obsolescencia deixou de ser `Falhar`.

### `ErrTrabalhoSuperado` — obsolescencia e lapide, nao defeito

Insumo que mudou ou saiu do acervo (`tarefas.go`, `noticia.go`) leva
`ErrTrabalhoSuperado`; o worker chama `Fila.Superar`, que vai de `executando`
direto a `erro` **ja com a lapide**, sem gastar as tentativas seguintes e sem
continuar contando em `Pendentes`. A checagem vem **antes** de `naturezaDaFalha`
— que classifica erro desconhecido como `NaturezaConteudo` e mandaria a linha
para o moinho de tres ciclos.

### A ORFA EM `executando` — e por que `Recuperar` no boot nao bastava

`Recuperar` tem **um** chamador em todo o repositorio: o boot de
`cmd/cerebro/main.go`. Isso bastava enquanto contencao de banco **matava** o
daemon — o processo caia, `Restart=always` levantava, o boot devolvia o
trabalho. A prova de que aquele caminho funcionava esta na fila viva: **14
tarefas com `recuperacoes > 0`**.

Desde que a contencao passou a virar **pausa** (`aadbb67d`), o processo fica de
pe e a tarefa presa em `executando` **espera um reinicio que ninguem vai dar**.
Oito reinicios visiveis viraram uma orfa invisivel. A correcao daquele commit
continua **certa** onde nasceu — em `Reivindicar`, morrer na porta nao acelera
nada —; o defeito era so no ramo da **escrituracao**, que pausava sem devolver.

Duas correcoes, e as duas sao necessarias:

1. **As oito escritas de escrituracao** (`Falhar`, `Concluir`, `Devolver`,
   `Superar`) passam por `Worker.escritura`, que e `EsperaSeOcupado`. Ela nomeia
   as duas coisas que **toda espera de cura tem de nomear**: a CLASSE em que
   insiste (contencao transitoria do SQLite — 5, 6, 261, 262, 517, por
   `bancoOcupado`) e o TETO medido em que desiste (`TetoDeEsperaPorBanco`,
   180 s). **Espera sem teto e mascaramento com outro nome.**
2. **`RecuperarVencidas` roda no laco**, a cada `IntervaloDaVarreduraDeLease`
   (5 min). Ela **nao** e `Recuperar`: aquele devolve TUDO o que esta
   `executando`, o que so e correto no boot, quando nenhum worker trabalha. Aqui
   ha **lease**, derivado das proprias flags do worker
   (`prazoDoLote(maxLote) + MargemDaEscrituracao + MargemDoBatimento`) — lease
   curto roubaria o lote da mao do worker, e ha teste de controle para isso.
   Lease `<= 0` e **recusado**, nao tratado como "sem filtro".

A restituicao de tentativa segue a regra C4: lease vencido nao diz nada sobre o
trabalho, entao a tentativa volta — ate `TetoDeRecuperacoesSemCulpa` = 6.

### O TRAVAMENTO PERMANENTE DO INDICE: texto que VOLTA a uma versao anterior

O sintoma que abriu a frente nao era so a lapide. Medido em
`/noticias/tst-20260901/`, com o journal repetindo *"nao cobre 1 pagina(s) do
acervo com o texto atual"*:

1. a pagina e embutida com o texto **H1**; a linha fica `concluida` e o vetor
   entra no indice;
2. o texto muda para **H2**; nova linha, novo vetor. O indice e **append-only** e
   `semantica.Indice.Tem` resolve por **ultimo registro de cada caminho**, entao
   ele passa a responder H2;
3. o texto **volta a H1**. `Tem(path, H1)` e **falso** (o ultimo e H2), o
   enfileirador tenta criar a tarefa de H1 — e bate na linha `concluida` do passo
   1. `INSERT OR IGNORE` ignora.

A partir dai a pagina **nunca** volta ao indice, `AtivaIndiceSeCompleto` recusa
(corretamente) ativar indice parcial, e a busca semantica de **11.161 paginas
fica desligada por uma**. O enfileirador ainda contava isso como `ja_na_fila`,
que e falso: nao ha nada na fila.

A correcao e no enfileirador: **"nao e nova" nao quer dizer "esta na fila"**. Ele
consulta `EstadoDaTarefa` e, se a linha existente esta `concluida`, chama
`ReabreConcluidaSemResultado`. A condicao e estreita de proposito — chegar
aquele ponto do laco **ja e a prova** de que o resultado nao esta disponivel,
porque o `indice.Tem` logo acima disse que nao.

### Reabrir reaplica a FAIXA VIGENTE do tipo

Medido em producao no primeiro boot depois da cura entrar (2026-09-16, commit
`197ea62b`): as **40** `extrair_dispositivos` curadas voltaram com prioridade
**-5 e -6** — os numeros do regime em que a extracao valia -5. A faixa vigente
da extracao e **-200**; a de `redigir_noticia` e **-100**. As curadas passaram
**na frente das 7 noticias pendentes**, e o primeiro lote depois do boot foi de
extracao. A invariante `min(D_n) > max(D_{n+1})` ficou violada por 37 linhas.

E a **mesma classe** do defeito que a cura veio fechar: estado carimbado por um
regime anterior, ressuscitado como se fosse corrente. `falhou_com` resolve isso
para o CODIGO; `prioridadeAoReabrir` resolve para a PRIORIDADE.

A regra, em `Reabrir` **e** em `ReabrirCuraveis`:

- prioridade **ja dentro** da faixa vigente fica intacta — o deslocamento interno
  e informacao boa (`PrioridadePorAno` ordena a extracao por ano do acordao, ate
  9 pontos), e achatar isso jogaria fora a ordem util;
- prioridade **fora** da faixa vai para a **base** da faixa — nao da para deduzir
  o deslocamento pretendido de um numero de regime extinto, e a base e o unico
  valor canonico. Favorece levemente a linha curada *dentro da propria faixa*, o
  que nao toca a invariante, que e ENTRE faixas;
- tipo **sem faixa declarada** fica intacto.

`cerebro reprioritizar-faixas --aplicar` continua sendo a migracao do estoque
legado; o que mudou e que **a cura nao reintroduz o estado que ele corrige**.

### A FRONTEIRA: o que NUNCA se auto-cura

A cura reexecuta trabalho **cujo insumo nao mudou e cujo codigo mudou**. Tudo o
que e afirmacao sobre o SUBSTRATO para e alerta — nenhum destes tem reexecucao
que possa dar certo:

| nao se auto-cura | criterio aplicavel | quem alerta |
|---|---|---|
| fila corrompida | `erroDeIntegridade` no `PRAGMA quick_check` | preserva `.corrompida-<ts>`, recria, transicao `fila_recriada` no gate |
| erro de disco, permissao ou esquema | erro de SQLite que **nao** esta em `bancoOcupado` (5, 6, 261, 262, 517) | mata o worker; `check-cerebro-vivo` |
| lapide | `superada_em <> ''` | ninguem: o trabalho ja foi feito. Nao e defeito |
| falha sob o carimbo atual | `falhou_com = carimbo` | `Erros` no batimento; so muda com codigo novo |
| carimbo indeterminado | `CarimboDoBinario() == CarimboIndeterminado` | `ReabrirCuraveis` RECUSA e nomeia; falha fechada |
| tarefa que derruba o worker | `recuperacoes >= TetoDeRecuperacoesSemCulpa` (6) | a tentativa para de ser restituida |
| pausa manual vencida | `ate` passou em `cerebro_pausa_manual.json` | `pausado_por_defeito`. **Nunca se auto-limpa** |
| contencao que passa do teto | `bancoOcupado` verdadeiro alem de `TetoDeEsperaPorBanco` | o erro sobe; `executando_vencida` pega a linha presa |
| lease nao declarado | `RecuperarVencidas` com `idadeMinima <= 0` | RECUSA com motivo: devolveria o lote em curso |
| concluida COM resultado no indice | `indice.Tem(path, hash)` verdadeiro | ninguem: refazer seria moer agua |

O limite geral: **auto-cura que engole erro e mascaramento**. Se a regra nova nao
nomeia um controle que ela continua reprovando, e falso-verde — os controles
aqui sao a falha de CONTEUDO (que continua indo a `erro`) e a `concluida` com
lapide (que **nao** e ambulante, e cujo teste de falso positivo esta em
`cura_por_causa_test.go`).

### O que o batimento publica, e o que o gate reprova

`lapides_ambulantes`, `curaveis_paradas` e `carimbo_binario` entram em
`cerebro_batimento.json`. O gate **nao recalcula o carimbo** — segunda
implementacao do mesmo hash e divergencia esperando acontecer.

- `lapide_ambulante` reprova por **presenca**: e invariante, nao limiar.
- `executando_vencida` reprova por **DURACAO** (o lease que o worker declara),
  nunca pelo total de `executando`, que e trabalho normal em curso.
- `cura_nao_rodou` reprova por **FLUXO**: `curaveis_paradas > 0`, nunca o total
  de `erro`. Com o daemon de pe o numero e zero por construcao. As 40 linhas em
  `erro` carimbadas com o binario atual saem **VERDES**, e ha teste de controle
  para isso — vermelho de estoque e vermelho que se aprende a ignorar.

### Escala: os estados vivos vao NOMEADOS

`WHERE estado<>'erro'` faz **SCAN** e paga a ementa de cada linha. Medido em
2026-09-16 sobre as 65.249 linhas reais:

| consulta | plano | tempo |
|---|---|---|
| `estado<>'erro' AND superada_em<>''` | `SCAN tarefa` | **1,439 s** |
| `estado IN ('pendente','executando') AND superada_em<>''` | `SEARCH … idx_tarefa_estado_modelo` | **0,116 s** |

Doze vezes, **sem indice novo**, e a consulta roda duas vezes por lote. Nomear
os estados tambem e mais CORRETO: `concluida` com lapide nao e contradicao, e
varrer por `<>'erro'` mandaria trabalho concluido de volta para `erro`.

## `Devolver` x `Falhar` — quem paga a tentativa

`Reivindicar` incrementa `tentativas` ao entregar a tarefa. Isso e uma APOSTA:
a de que, se falhar, a culpa e do trabalho.

- **INFRA / AMBIENTE** (`ollama.ErrIndisponivel`, `ErrServidor`,
  `ErrModeloAusente`, prazo do lote estourado, cancelamento) refutam a aposta =>
  `Fila.Devolver`, que volta a `pendente` **sem consumir tentativa**, com jitter
  de ±20% no `disponivel_em`.
- **CONTEUDO** (`ErrRecusado`, `ErrRespostaIlegivel`) => `Fila.Falhar`, como
  sempre.

O disjuntor e do **WORKER**, nao da tarefa: backoff global 30 s -> 15 min, e ele
so FECHA depois do laco por tarefa e apenas se `devolvidas == 0`. Fechar antes
anula a escada inteira, porque a extracao reporta erro POR TAREFA.

## O caminho quente: duas consultas que ja foram P0

Medido em 2026-09-16 sobre as 65.249 linhas reais (`Fotografia` roda 2x por
lote; a sonda de modelo, a cada 60 s):

| consulta | sem indice/forma certa | com |
|---|---|---|
| `SELECT DISTINCT modelo` (sonda de modelo ausente) | **38,279 s** | 0,017 s |
| contagens por estado | 1,624 s (`SUM(condicao)`) | 0,017 s (`GROUP BY`) |

O que resolveu: `idx_tarefa_estado_modelo (estado, modelo)` e trocar
`SUM(condicao)` por `GROUP BY estado` + `COUNT(*)` dos elegiveis. **Consulta nova
no caminho de cada Passo tem de sair de indice**, senao ela paga a ementa inteira
de cada linha (~2,5 KB no payload).

## O custo que nao aparece em tok/s

Medido em 2026-09-09 (sonda de prefixo, `qwen3.5:4b` alternando com
`qwen3-embedding:0.6b`): cada alternancia custou `load_duration` de **21.121,
48.621 e 37.221 ms** — maior que o proprio prefill (23-50 s) em duas das tres
chamadas. No 4b o prefill roda a ~16 tok/s e o decode a ~4,7 tok/s, entao a troca
de modelo custa mais que boa parte do trabalho util. O reivindicador de lote so
evita isso porque puxa tarefas do **mesmo `tipo`+`modelo`** e a prioridade agrupa
embeddings (0) antes das extracoes (ver as FAIXAS abaixo; ate 2026-09-16 eram
−5…−11).

Enfileirar tipo novo (comentario, noticia) com prioridade que **nao** forme
bloco espalha trocas de modelo pela fila inteira. Pelo mesmo motivo, **sonda de
geracao nao roda durante a fila de embeddings**: ou fora do horario dela, ou com
o daemon pausado. E custo de modelo se mede por `load_duration`, nao so por
tok/s — o tok/s nao mostra o que a troca cobrou.

## Faixas de prioridade (2026-09-16) — nao ha mais numero solto

As prioridades `−5…−11` que esta regra listava **ficam superadas nesta data**. O
defeito: `medir_modelo` estava em −10, DENTRO da faixa da extracao (−5 a −14), e
as 3 medicoes ficaram paradas atras de 8.961 extracoes.

Faixas de 100 pontos, declaradas em `internal/cerebro/tarefas.go`
(`FaixasDeclaradas`), com invariante testavel `min(faixa_n) > max(faixa_{n+1})`:

| faixa | base | por que nesta ordem |
|---|---|---|
| `FaixaEmbeddings` | 0 | pagina sem vetor e pagina fora da busca semantica |
| `FaixaComentarios` | −100 | a peca social tem janela; a extracao nao |
| `FaixaExtracao` | −200 | lote de fundo; espalha ate 9 pontos por ano |
| `FaixaMedicao` | −300 | comparar modelos e trabalho de janela ociosa |

**Faixa nova se declara ali, nunca por um numero no `flag.Int` de um subcomando**
— foi assim que o −10 entrou. As linhas ANTIGAS da fila viva continuam com os
numeros velhos ate alguem rodar `cerebro reprioritizar-faixas --aplicar`
(ensaio e o padrao).

## A POLITICA DE 2026-09-16: o cerebro nao para por saturacao, e o prazo e por tipo

Ordem do dono, literal: *"Sobre a saturacao, nao tem problema. A producao e
servida para os bots via cloudflare, aqui dentro e mais a inteligencia e forca
bruta. Ate a migracao para servidor maior. Entao, nao travar por saturacao."* E,
no mesmo dia: *"Pode aumentar a politica do cerebro."*

### SUPERADO em 2026-09-17: o `LockPesado` tambem saiu do padrao

Ordem do dono de 2026-09-17: *"Nao tem problema se CPU ficar alta, a
inteligencia deve funcionar e nao travar por CPU."* `LockPesadoPadrao` e **vazio**
desde esta data (`internal/cerebro/saude.go`). A sonda e a flag `--lock-pesado`
continuam; o padrao, que e o que a unit usa, desliga.

A medicao que fechou, em 22,5 h (09-16 11:56 -> 09-17 10:23):

- quem segura `/tmp/opt-wiki-agent-heavy.lock` sao as **bancadas**
  (`qualidade-diaria`, `qualidade-longa`), nao o commit de Go, que usa
  `/tmp/opt-wiki-commit.lock`;
- **134 min** de producao parada por essa pausa — a maior causa da janela, mais
  que os dois SQLITE_BUSY somados (58 min);
- **nenhum ganho**: diaria 59m13s com o cerebro produzindo contra 60m38s com ele
  pausado; longa 33m25s contra 44m09s.

A arbitragem de CPU e o peso de cgroup (`wikijuridica_alimentacao.slice`,
`CPUWeight=20`). Se a disputa voltar a ser medida, ajusta-se o peso — nunca se
para a inteligencia. **Nenhuma ferramenta toma o flock esperando o cerebro
pausar** (procurado em `tools/` e `ops/`); o roteiro de provas negativas liga a
sonda com `--lock-pesado` explicito.

O subtitulo e o paragrafo abaixo ficam como registro do regime de 2026-09-16.

### `CargaMaxPadrao` e ZERO — e o `LockPesado` FICA

`internal/cerebro/saude.go`. O teto de `loadavg` era **12,0** e virou **0**
(sonda desligada). O fundamento nao e' tolerancia a lentidao: o acervo sai
estatico de `public/` com `s-maxage=604800` atras da Cloudflare, e **HIT na borda
nao toca esta maquina** — o `loadavg` daqui nao e' latencia de visitante nenhum.

O caso medido, no journal de 2026-09-16:

```
16:42:24 pausa [ocupacao_carga/loadavg]: loadavg de 1 min em 14.49, acima do teto de 12.00
16:49:24 retomado depois de 7m0s de pausa [ocupacao_carga/loadavg]
```

**Sete minutos de redacao de noticia perdidos, com 13 tarefas pendentes**, e a
unica carga que aquele numero media era o trabalho do proprio cerebro.

**A guarda que FICA e outra, e nao e' saturacao: `LockPesado`.** Ela serializa
contra compilacao e commit de Go, com numero medido (pre-commit a 75 s com o
cerebro competindo contra 29 s com ele parado, 2026-09-09). Saturacao e' decisao
do dono; contencao de commit e' defeito. Quem for "simplificar" as duas sondas
numa so esta desfazendo esta distincao.

**Efeito de segunda ordem a vigiar, nomeado e nao fechado:** `CargaMax = 12`
funcionava tambem como **governador do host** — load acima de 12 fazia o cerebro
ceder, o load caia, e `tools/check-load-headroom --max 12` liberava comando
pesado. Agora o cerebro nunca cede. Se o headroom passar a recusar comando
pesado, **o conserto e' do lado do comando pesado** (tomar o flock primeiro, o
que faz o cerebro pausar, e so entao checar headroom) — **nunca** devolver o teto
ao cerebro, porque a ordem do dono e' literal.

*SUPERADO em 2026-09-17:* "tomar o flock primeiro, o que faz o cerebro pausar"
deixou de ser verdade — o flock nao pausa mais o cerebro (ver o topo desta
secao). Se o headroom recusar comando pesado, o conserto continua do lado do
comando pesado, agora pela **fila de CPU**: rodar o comando pesado sob uma slice
de peso maior que `wikijuridica_alimentacao.slice` (`CPUWeight=20`), nunca pausar
a inteligencia.

## A REIVINDICACAO (2026-09-17): indice na ordem do `ORDER BY`, espera antes de pausar

Com `_txlock=immediate` (3f7609e5) o `SELECT` da reivindicacao roda **dentro** do
lock de escrita, e o custo dele virou tempo de lock para todo mundo.

- `idx_tarefa_elegivel` e **(estado, prioridade DESC, id, disponivel_em)**. Com
  `disponivel_em` antes do id, o indice nao entregava `ORDER BY prioridade DESC,
  id` e o plano ordenava o GRUPO de prioridade inteiro em TEMP B-TREE, com
  payload: 113-125 ms na fila viva (grupo de 2.757 linhas), 0,05 ms depois.
  Banco antigo e redefinido no `Abrir` (`redefineIndiceElegivel`) — `CREATE INDEX
  IF NOT EXISTS` nunca redefine nome existente.
- `sqlReivindicaLote` usa `+tipo`/`+modelo`: sem ANALYZE o planejador preferia
  `idx_tarefa_estado_modelo` e lia as ~56 mil pendentes do modelo. **Pior caso
  nomeado e nao fechado:** quando a primeira tarefa e a ultima do seu tipo no
  topo, o lote anda o indice ate achar outra do mesmo tipo/modelo (O(P) uma vez
  por transicao de faixa). A rota O(k) medida pelo critico e redefinir
  `idx_tarefa_estado_modelo` como (estado, tipo, modelo, prioridade DESC, id,
  disponivel_em): 0,31 ms.
- `Passo` envolve `Reivindicar` em `EsperaSeOcupadoAte(TetoDaReivindicacaoOcupada)`
  = `MargemDoBatimento/2` (60 s) — derivado para o batimento ocioso nao vencer
  durante a espera. Esgotada, a pausa sai `infra/fila_ocupada`, **sem** o texto de
  `ErrPausado` ("portal ou ollama fora do health"), que mandava olhar o lugar
  errado.
- `EnfileirarLote` repete o lote de escrita em BUSY (`EsperaSeOcupado`) e so funde
  as marcas de reprioritizacao depois do commit.
- O batimento declara `tipo_lote`, `modelo_lote` e `ultimo_lote_em`, este
  carimbado **so** depois de `Concluir` — `Passo` devolve `len(lote)` tambem para
  lote devolvido, superado ou sem executor.

**Regra que sai disto:** toda consulta no caminho quente tem **um** caminho
inequivoco (rowid, indice cujo prefixo seja igualdades + `ORDER BY`, ou `+coluna`
tirando do jogo o indice de baixa cardinalidade) e um teste de `EXPLAIN QUERY
PLAN` sobre a **constante** que a producao executa. **Nao** usar ANALYZE como
correcao: numa copia ele consertou dois planos e transformou tres em `SCAN`.

### O prazo do lote sai do TIPO, e o lease acompanha o PIOR caso

`internal/cerebro/worker.go`. `PrazoPorTarefaPadrao = 300 s` foi calibrado para
**extracao** (90-105 s por tarefa) e **embedding** (~40 s por lote).
`redigir_noticia` **nao existia** quando esse numero foi escrito, e o tipo novo
custa 3-6x mais — porque o custo e' dominado pelo **prefill**, nao pela geracao.

Medido nesta CPU em 2026-09-16, lote de 3:

| hora | prompt | eval | parede |
|---|---|---|---|
| 16:15:17 | 2.964 tok (4,7 tok/s) | 786 tok (1,91 tok/s) | 10m30s |
| 16:42:24 | 5.950 tok (6,6 tok/s) | 631 tok (3,20 tok/s) | **15m00,01s** |
| 16:49:24 | 4.534 tok (12,7 tok/s) | 880 tok (4,34 tok/s) | 5m58s |

**A linha do meio nao e' medida de trabalho.** `15m0.01s` e' exatamente
`3 x 300 s`: o teto cortando no meio de um prefill de 5.950 tokens, que a 6,6
tok/s consome 901 s sozinho. O lote devolveu 1 das 3 tarefas como "falha de
infraestrutura", e a peca se perdeu com o contexto.

`prazosPorTipo` carrega **so** o tipo cujo custo diverge do padrao:
`TipoRedigirNoticia: 900 s`. Tipo ausente do mapa usa os 300 s, que continuam
medidos e vigentes. `w.PrazoPorTarefa`, quando declarado, vence todos os tipos.

**A armadilha, e ela e a que custa trabalho:** `leaseDeExecucao` usa
`prazoMaximoDoLote`, o **pior caso entre todos os tipos** — nunca o prazo do tipo
do lote. A varredura de lease nao sabe que tipo o outro lote esta executando;
lease menor que o prazo real de ALGUM tipo faz `varreLeaseVencido` devolver a
`pendente` um lote que o worker esta executando agora, e a tarefa roda duas
vezes. Acrescentar tipo lento ao mapa **sem** conferir esta conta e' o modo de
quebrar isso em silencio.

**Se aparecer `parede=45m0` com tarefa devolvida, o alvo e o PROMPT**, nao o
teto: 5.950 tokens de prefill e o custo real, e subir teto de novo so adia.

## O que nao mudar sem medir

- `OLLAMA_MAX_LOADED_MODELS` e' **2**, e a guarda real nao conta modelos: ela
  pesa bytes residentes (teto de 9 GiB) em `internal/cerebro/saude.go`. O par do
  incidente de 2026-09-08 (14b + 9b = 16 GB) continua barrado.
- **Nao ha `DELETE` livre.** `Fila.Podar` apaga SO `concluida`, e so de tipo com
  artefato append-only correspondente (`PodavelPorTipo`). A linha em `erro` e a
  unica evidencia que existe do defeito.
- `MemoryMax=12G` no drop-in `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`.
- Trabalho em massa (embeddings, extracao, classificacao) vai em modelos de 0,6
  a 4B; o 14b so em lote noturno com entrada curta.
- Custo se corta em **tokens processados**, nunca em inteligencia: a extracao e'
  dominada pelo prefill (700–1.100 tokens a 15–19 tok/s contra ~100 de saida a
  5 tok/s), entao prefixo de sistema reaproveitado, esquema curto e `num_ctx` por
  tarefa valem mais que trocar de modelo.
- Parser antes de modelo: meca a cobertura do parser sobre o conjunto ja
  rotulado, sem chamada nova.
