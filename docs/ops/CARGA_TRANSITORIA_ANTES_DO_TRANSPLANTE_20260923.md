# Carga transitória antes do transplante — o que foi pausado, o que ficou, e por quê

**2026-09-23** · Ordem do dono: *"diminuir a carga do projeto e deixar somente o que for importante para o servidor continuar no ar (…) a carga de agora é transitória: o servidor vai para outra máquina mais potente"*. Sessão Claude Code (Fable 5.1 orquestrando; Sonnet 5 no mapa de contexto; Opus 5.5 na ferramenta; `advisor` antes de tocar e antes de fechar).

**Estado ao fim da sessão, em uma linha:** o cérebro de IA local está em **pausa declarada** até `2026-10-07T23:59:59-03:00`; o `ollama.service` continua de pé e **ocioso**; nada do caminho de serving foi tocado; nenhum timer foi desligado. Retomar é `tools/cerebro-pausar retirar`.

## 1. O que a medição disse antes de tocar em qualquer coisa

Camada declarada de cada número (Regra 15/16): `systemctl show -p CPUUsageNSec`, o journal do systemd (`Consumed … CPU time`, por vida de processo) e a série `data/ops/energia_cpu.jsonl` (uma amostra a cada 5 min: `load1`, watts RAPL, temperatura do pacote, contador de throttle).

| consumidor | CPU medida | memória | camada |
|---|---|---|---|
| `ollama.service` (`llama-server` com `qwen3.5:4b`) | **21h04 + 15h52 + 23h06 de CPU** nas três vidas do processo entre 2026-09-22 e 2026-09-23 02:41 (≈ 60 h de CPU por 24 h de parede = 2,5 núcleos em média; 383 % no instante da medição) | **9,2 GB residentes** (MemoryCurrent) | journal `Consumed`, `systemctl show` |
| `wikijuridica-qualidade-longa.service` (02:10, Nice=19) | 4h11 de CPU em 1 execução | — | journal `Consumed` |
| `wikijuridica-qualidade-diaria.service` (04:40, Nice=19) | 2h05 de CPU em 1 execução | — | journal `Consumed` |
| todos os outros timers `wikijuridica-*` somados (60 units) | ≈ 1 h de CPU por dia (`bot-telemetry` 808 s, `origin-access-ledger` 674 s, `cerebro-saude` 466 s, `alertas-abertos` 417 s…) | — | journal `Consumed`, 24 h |
| `wikijuridica-server` (Go) | 1.510 s de CPU em 20 h (2 % de um núcleo) | 1,5 GB | `systemctl show` |
| `wikijuridica-nginx` / `wikijuridica-social` / 5× `cloudflared` | 285 s / 170 s / 58 s em ~28 h | 367 / 266 / 23 MB | `systemctl show` |
| `docker`+`containerd` (todos os contêineres parados), `libvirtd` (VM desligada), `lxc-*`, `snapd`, `packagekit`, `glances` | 20 s + 147 s / 1 s / 0 / 0 / 0 / 1,5 s em ~28 h | — | `systemctl show` |
| `xfce4-taskmanager` (janela do dono) | 11.585 s de CPU em 28 h (11 % de um núcleo, contínuo) | 28 MB | `ps -o cputimes` |
| `kswapd0` + `kcompactd0` (kernel reclamando memória) | 996 s + 786 s desde o boot | — | `ps -o cputimes` — **consequência** dos 9,2 GB do Ollama, não causa |

**Série de energia, 24 h antes da pausa (2026-09-22 06:30 → 2026-09-23 06:30, 284 amostras):** `load1` mediana **6,17**, p90 12,34, máximo 31,93 · 12,80 W medianos · pacote a 79 °C medianos e **95 °C** no máximo · **+420.727 eventos de throttle** no dia · NVMe a 83,8 °C (o mesmo NVMe que `docs/ops/MIGRACAO_SERVIDOR_20260922.md` mede em 49 % de TBW e 1.684 min acima do crítico).

**Comparação com os dias em que a fila estava vazia** (mesma série): 2026-09-19 a 2026-09-21 tiveram `load1` mediana **1,38–1,44** e 8,6–13,8 W. A diferença entre esses dias e 22–23/09 é o enfileiramento de 18–19/09, que levou `extrair_dispositivos` a **105.524 pendentes** (`sqlite3 -readonly data/ai/fila.sqlite`).

**O que a fila estava fazendo, e a que custo:** lotes de 3 acórdãos em `qwen3.5:4b`, 1 a 7 min por lote, 4,9 tok/s de eval e 8–16 tok/s de prefill (journal do cérebro e `data/ops/ia_local_daily.jsonl`); 467 concluídas em 22/09 e 658 em 23/09 até 06:27. **Nesse ritmo os 105.524 pendentes levam ~50 dias de CPU** — e a máquina nova, pela razão medida no relatório de hardware (RTX 5060 Ti a 32,9 tok/s contra 1,85 tok/s no mesmo 14B Q4 = 17,8×; PROJETADO para o 4B, não medido), faz o mesmo em cerca de três dias. Continuar aqui compra ~3 % da fila ao preço de 2,5 núcleos, 9,2 GB e um chassi a 95 °C.

## 2. A decisão: pausa declarada, não desligamento

O código já tinha o desligamento intencional desenhado — `internal/cerebro/pausa.go:104-163` (`PausaManualDeclarada`, `LePausaManual`) e `internal/cerebro/saude.go:210-229`, que lê a pausa **antes** de qualquer sonda. A pausa é um arquivo, `data/ops/cerebro_pausa_manual.json`, com exatamente quatro campos (`motivo`, `ate`, `declarada_por`, `declarada_em`; `DisallowUnknownFields` recusa qualquer outro, e arquivo ilegível vira `PausaInfra` com alerta em 25 min).

Por que isto e não `systemctl stop`:

- **O gate lê a pausa como VERDE.** `internal/checks/cerebro_batimento_gate.go:218-222`: estado `pausado_a_pedido` devolve `nil`. Parar a unit à força deixaria `cerebro-saude.timer` (a cada 15 min, `OnFailure=wikijuridica-alerta@`) sem batimento e acordaria o dono a cada rodada.
- **`buscar_semantico` sobrevive.** `internal/httpserver/mcp_semantico.go:74-86`: a ferramenta só é anunciada se o Ollama respondeu no boot do servidor; Ollama parado depois do boot vira erro por chamada, sem fallback lexical. Com `ollama.service` de pé e sem modelo residente, a pergunta carrega o `qwen3-embedding:0.6b` (0,64 GB) sob demanda. Nenhuma outra rota HTTP/MCP chama o Ollama ao vivo (mapa em `.agents/runtime/contexto/20260923-dependentes-do-cerebro-e-ollama.md`, §3.4).
- **Vencida, a pausa vira lembrete, não silêncio.** `cerebrobatimento.go:261-264`: a classe manual não tem limiar de duração; o prazo é o campo `ate`. Passado o prazo o cérebro **continua parado** e `check-cerebro-batimento` reprova com `pausa_manual_vencida` — de propósito, para que "esqueci desligado" seja visível.
- **Os dois gates diários não exigem entrada nova.** `tools/check-writeback-do-cerebro-nao-atrasa` cobra promoção de extração com URN há mais de 26 h (`--idade-maxima-horas`), e a onda diária promove o que já saiu; `check-extracao-do-cerebro` mede âncora, promoção e manifesto do grafo, não fluxo.
- **Não se fez pausa por tipo de tarefa.** A fila tem 23 `redigir_noticia` e 5 `gerar_comentario_autoridade` concluídas na vida inteira; o período é transitório; construir seletor de tipo agora seria engenharia para um caso que não existe.

## 3. O que foi feito, na ordem, com a evidência

1. `06:30:07 -03` — escrito `data/ops/cerebro_pausa_manual.json` (temp + `os.replace`), `ate = 2026-10-07T23:59:59-03:00`, motivo e autoria no arquivo. Confirmado antes: `cmd/cerebro/main.go:139` preenche `Saude.Root`; `sha256sum bin/cerebro` = `sha256sum /proc/511591/exe` (`311e0845…`), então o binário em execução conhece a pausa.
2. `06:37:16` — o lote em voo terminou (6m58s, 3 acórdãos); `06:37:18` — journal: `cerebro: pausa [manual/pausa_manual]: … pausa declarada em data/ops/cerebro_pausa_manual.json ate 2026-10-07T23:59:59-03:00`. `data/ops/cerebro_batimento.jsonl` registrou a transição `trabalhando → pausado_a_pedido` (linha de `2026-09-23T09:37:18Z`, `pendentes: 105512`).
3. `06:37:40` — `ollama stop qwen3.5:4b`: descarga imediata em vez de esperar os 15 min de `OLLAMA_KEEP_ALIVE`. `ollama ps` vazio. `free -m` no mesmo minuto: **5.844 MB usados / 14.035 MB disponíveis** (antes: 14 GB usados / 5,3 GB disponíveis).
4. Gates sob a pausa, todos com exit 0: `check-cerebro-batimento` (`pass`, 1 ms), `check-cerebro-vivo` (`estavel ha 69887 s`, 0 restarts), `check-cerebro-enfileiramento` (última execução 78 s, limiar 300), `check-writeback-do-cerebro-nao-atrasa` (109 pendentes com URN, mais antigo 2,0 h — dentro das 26 h; a onda diária promove), `check-extracao-do-cerebro` (`pass`, 795 ms).
5. `buscar_semantico` real pelo MCP ("posso ser demitida enquanto estou grávida?"): 8 páginas, 18.786 indexadas, `qwen3-embedding:0.6b` carregado sob demanda; `ollama ps` passou a mostrar só o 0.6b.
6. Produção viva nas três camadas: `check-portal-health` OK (acervo/página/sitemap 200, Go 200, busca 200, rede social 200/200/200, `restarts=591(+0)`); `check-agent-surface-live` "todas as sondas obrigatorias passaram"; borda `https://wikijuridica.com.br/` **HTTP/2 200, `cf-cache-status: HIT`, `age: 75075`** com UA de sonda e `X-Warming-Request: true`; `/readyz` 200 em 0,9 ms; nginx home 200 em 0,7 ms.
7. Aviso no bus de coordenação (`tools/generate-coord-message … --to all`) para que nenhuma outra sessão trate a pausa como defeito.

## 4. O que NÃO foi tocado, e por quê (cada item com a medição)

- **Bancadas `qualidade-longa` e `qualidade-diaria`** (6h16 de CPU por dia somadas, `Nice=19`, slice `wikijuridica_lote` com `CPUWeight=30`, entre 02:10 e ~05:00): são a guarda de regressão dos commits das sessões vivas — havia duas outras sessões Claude Code em `/opt/wiki` e um pacote da sessão Cowork pendente de commit no momento da medição. Rodam de madrugada e ficam mais rápidas com 9 GB livres.
- **Os 60 timers `wikijuridica-*`**: somados, ≈ 1 h de CPU por dia. Classificação por `ExecStart` (12 SERVING, 23 MEDIÇÃO, 27 FÁBRICA, 10 OUTRO) no mapa do Sonnet, §3.6. Desligar medição contraria a Regra 15/16 (série que para deixa buraco); desligar fábrica não compra carga mensurável.
- **`docker`/`containerd`, `libvirtd`, `lxc`, `snapd`, `packagekit`, `glances`, `yggdrasil`, ProtonVPN**: desprezíveis (tabela §1) e fora do projeto.
- **`xfce4-taskmanager`, Chrome, `pjeoffice-pro`, `claude-desktop-update.timer` (horário)**: janelas e serviços do dono. O taskmanager é o único com custo visível (11 % de um núcleo, contínuo) — é fechar a janela quando não estiver olhando.
- **`ops/provisionamento/`**: intocado — `git diff --stat 73ff537d..HEAD -- ops/provisionamento/` continua vazio, então a mídia de instalação continua válida.

## 5. Como retomar, renovar ou conferir

```
tools/cerebro-pausar status                      # vigente / vencida / ausente, e o batimento do worker
tools/cerebro-pausar renovar --ate 2026-10-21T23:59:59-03:00
tools/cerebro-pausar retirar                     # o worker retoma no próximo ciclo de saúde (≤ 60 s)
tools/check-cerebro-batimento                    # prova
```

**A pausa atravessa no `rsync` para a máquina nova** (`data/ops/` vai inteiro): ela nasce com o cérebro pausado, de propósito. A retirada é o passo que abre a drenagem da fila na GPU, depois dos itens 1–3 de "Depois do cutover" em `docs/ops/MIGRACAO_SERVIDOR_20260922.md`.

## 6. Custo declarado enquanto a pausa vale

- Página publicada até a retomada **não entra no índice semântico** (fica só na busca lexical); a `embed_pagina` reenfileirada pelo `cerebro-enfileirar` diário espera na fila.
- Notícia autoral e comentário de autoridade do cérebro não são redigidos — custo nominal, não real: a última `redigir_noticia` concluída é de 2026-09-16T21:05Z e o último `gerar_comentario_autoridade` de 2026-09-16T21:20Z (`sqlite3 -readonly data/ai/fila.sqlite`); a fila não recebia trabalho desses tipos havia uma semana.
- Os 109 acórdãos extraídos hoje com URN e ainda não promovidos (2,0 h no gate das 06:44) são promovidos pela onda `wikijuridica-daily-content` de 2026-09-24 ~04:31 (`tools/run-daily-content:915`, `generate-writeback-extracoes`, independente do worker), com idade ≈ 24 h < 26 h — o gate `writeback-do-cerebro-nao-atrasa` não fica vermelho por causa da pausa.
- `wikijuridica-cerebro-enfileirar.timer` continua enfileirando (78 s por dia): `pendentes` cresce, e é esse número que a máquina nova drena.
- O painel `tools/cerebro-aviso` mostraria AMARELO ("pausado a pedido") — mas ele **não está instalado** neste host (`tools/cerebro-aviso` está `100644`, sem bit de execução, e nenhum `genmon-*.rc` o referencia; não há unit de `transicao` em `ops/systemd/`). Lacuna anterior a esta frente; registrada, não corrigida aqui, porque instalar plugin no painel do dono enquanto ele trabalha não é decisão desta sessão.

## 7. Depois — a série pós-pausa (mesma camada, mesma série)

Janela de 06:42 a 07:07 (6 amostras de `data/ops/energia_cpu.jsonl`, depois da descarga das 06:37:40), contra as 24 h anteriores (§1):

| grandeza | antes (24 h, 284 amostras) | depois (25 min, 6 amostras) |
|---|---|---|
| `load1` mediana | **6,17** (p90 12,34) | **0,84** (máximo 1,34) |
| potência do pacote (RAPL) mediana | 12,80 W | **6,64 W** |
| temperatura do pacote mediana | 79 °C (máx. 95) | **61–63 °C** (máx. 90, no minuto do timer diário `grafo-juridico` das 06:52) |
| eventos de throttle | +420.727/dia (≈ 1.460 por 5 min) | +4.658 em 25 min (≈ 930 por 5 min, com o pico das 06:52 dentro) |
| RAM usada / disponível (`free -m`) | 14 GB / 5,3 GB | **5,8 GB / 14,1 GB** |
| swap em uso | 2.005 MB | 1.460 MB e caindo |
| `ollama.service` residente (`MemoryCurrent`) | 9.227 MB | **428 MB** |
| modelos residentes (`ollama ps`) | `qwen3.5:4b` a 100 % de CPU | nenhum (o 0.6b entrou por 2 min na consulta de prova e saiu) |
| `check-http-smoke` (in-process, 18.774 rotas) | estourou 120 s (morto por `timeout`) | **71,5 s de parede, exit 0** (`orçamento 100 s`) |

Vigia paralelo (`/proc/loadavg` + `free -m` a cada 5 min, 06:38→07:03): `load1` 3,19 → 0,84 → 0,93 → 3,02 (06:53, timer diário) → 1,04 → 0,93; `load15` de 6,60 para 2,24. O sensor `nvme_sensor2_c` devolveu 83,8 em todas as amostras, antes e depois — valor que não varia é leitura a conferir no dia do transplante, não evidência de temperatura.

O que a série NÃO diz: 25 minutos não medem a bancada noturna (02:10–05:00) nem a onda de conteúdo das 04:20; a comparação justa dessas janelas é a de amanhã, na mesma série, e a hipótese é que elas encurtem com 9 GB livres e sem disputa pelos 4 núcleos.

## 8. Ferramenta e prova

- `tools/cerebro-pausar` (`declarar | renovar | retirar | status`, stdlib) escreve exatamente o que `LePausaManual` lê e recusa o que ele recusa; o leitor segue o Go medido (chave ausente vira `""`, casamento de chave ASCII sem caixa, lixo depois do objeto passa), o escritor grava sempre as 4 chaves. Bancada `tools/test_cerebro_pausar.py`: 34 casos, 16 mutantes mortos.
- `internal/cerebro/pausa_ferramenta_test.go`: paridade de ponta a ponta — executa a ferramenta e lê com o daemon; 8 formatos de `ate` recusados dos dois lados; mutações (5ª chave, hora sem segundos, queda em vez de recusa) derrubam o teste.
- Declaração desta sessão em `data/ops/cerebro_pausa_manual.json` (rastreado a partir deste commit, porque é decisão com data, autor e prazo) e a transição `trabalhando → pausado_a_pedido` em `data/ops/cerebro_batimento.jsonl`.

## 9. Alertas e units `failed` durante a janela — atribuição

Os timers reais rodaram sob a pausa com `Result=success`: `cerebro-saude` (06:50 e 07:05), `cerebro-publicar-noticias` (06:43), `grafo-juridico` (06:52). `data/ops/owner_alerts.jsonl` não recebeu linha do cérebro. Três units `wikijuridica-*` estavam `failed` às 07:10, **nenhuma causada pela pausa**, lidas no journal de cada uma:

- `wikijuridica-edge-frescor` (06:40:05, exit 2, **alerta ao dono enviado** por `OnFailure`): `rotas: 0 mudadas` nas 24 h — a publicação está travada esperando commit de portfólio e estoque de outra frente (`publicar-estoque` às 06:43: *"destrava: o Claude Code commita portfolio e estoque"*; `data/editorial/portfolio_v2/*.jsonl` e `v2_pages/*.jsonl` modificados no disco). Sem rota mudada o check não tem o que medir e sai 2. Primeira ocorrência em 7 dias; janela 09:40Z→09:40Z, anterior ao flip da pausa (09:37Z) em tudo menos 3 min.
- `wikijuridica-djen-coleta` (06:22:30→06:27:39, exit 124): `progress_monitor_alert status=io_without_progress_risk` repetido e morte pelo orçamento do `run-heavy-throttled` — coleta do DJEN sem progresso de E/S, com o Ollama ainda a 4 núcleos (o flip foi às 06:37). Primeira falha em 7 dias; o timer repete amanhã às 06:22.
- `wikijuridica-edge-warm` (01:24→02:09, `timeout` de 45 min, `SIGTERM`): recorrente — também em 2026-09-22 14:08 —, anterior a tudo desta sessão.

Nenhum `reset-failed` foi feito: o estado é honesto e pertence às frentes donas de cada unit.

## 10. Autocrítica

Resolveu o que a ordem pedia — 90 % da carga saiu com um arquivo, sem tocar no serving — e a medição sustenta o número na mesma camada antes e depois. O que ficou sem resposta: (a) as 25 amostras não cobrem a madrugada, então o efeito sobre as bancadas é hipótese; (b) `internal/cerebro/saude.go` e `internal/cerebrobatimento/cerebrobatimento.go` estão modificados no disco desde 2026-09-17 11:17 por outra frente (pausa por estrato de modelos ausentes, +76 linhas), **quatro minutos depois** do `bin/cerebro` em execução ter sido compilado — o daemon vivo não tem esse código, e ninguém commitou em seis dias; (c) o painel `cerebro-aviso` nunca foi instalado; (d) o custo real da pausa é o índice semântico congelado em 18.786 páginas até a retomada. Nada disso é motivo para retomar a extração aqui: cada item tem dono nomeado acima e nenhum depende de CPU desta máquina.
