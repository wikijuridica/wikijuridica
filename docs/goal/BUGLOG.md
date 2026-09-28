# BUGLOG.md — Registro de bugs e defeitos estruturais encontrados

Formato: cada entrada tem ID, data, sintoma, causa raiz, correção e status.

## BUG-001 — Deadlock de promoção: gate final sem produtor
- **Data:** 2026-07-05 (Fase 0)
- **Sintoma:** `published_manifest=0` após ~400 ciclos; toda tentativa de promoção retorna `public_release_promotion_blocked_by_default` ou `public_release_promotion_manifest_blocks_public_write`.
- **Causa raiz:** `ExecutePromotionSwapPlanWithOptions` (`internal/publicrelease/publicrelease.go:2719`) exige `.release-staging/promotion_manifest.json` com `Status="promotion_public_write_approved"` e 4 flags abertas. O único escritor desse manifesto (`promotionManifestForPlan`, `publicrelease.go:1242`) grava **sempre** `promotion_prepared_blocked_by_default` com flags fechadas. Nenhum código em `internal/`, `cmd/` ou `tools/` produz o status aprovado. A porta de publicação não tem chave no código shipado.
- **Correção:** criar o produtor legítimo do manifesto aprovado, acionado somente após todos os gates de qualidade passarem (decisão DEC-003).
- **Status:** corrigido no código. `internal/publicrelease/approval.go` implementa o produtor fail-closed e `cmd/promote-authorial-mass-public-release` o aciona pela transação autenticada via `ExecutePromotionSwapPlanWithOptions`. Validado em 2026-07-15 pelos testes focais de aprovação/promoção de `internal/publicrelease`. A ausência atual de verdict/manifest v2 vivo é um bloqueio de entrada da cadeia, não reabertura deste deadlock.

## BUG-002 — Reversão de produto por gate: 8.263 páginas publicadas zeradas
- **Data do evento:** 2026-06-29; registrado 2026-07-05.
- **Sintoma:** `data/audits/published_manifest_publication_zero_correction_2026-06-29.jsonl` mostra `manifest_records_before=8263` → `manifest_records_after=0`.
- **Causa raiz:** em 25/06 um ciclo materializou 8.263 registros `published` com `index_policy=index` no manifest, mas a cadeia transacional (`transaction_flag_counts`) permanecia toda `false`. Um gate de auditoria posterior classificou o estado como `unsafe_public_manifest_closed` e truncou o manifest para zero, em vez de abrir a transação para os registros aprovados. Padrão do loop: um gate novo apaga o produto do ciclo anterior porque a cadeia de flags nunca tem caminho de abertura (ver BUG-001).
- **Correção:** com o produtor do BUG-001 criado, a promoção passa a abrir a cadeia inteira de forma coerente (manifest + transação + verdict + flags), eliminando o estado híbrido que o gate corretamente reprovou.
- **Status:** causa de abertura corrigida com BUG-001. A prevenção de nova perda permanece dependente de promover apenas o conjunto v2 aprovado pela cadeia completa e de preservar a transação/manifesto coerentes; não zerar produto para compensar estado híbrido.

## BUG-003 — Governança processual mais cara que o produto
- **Data:** 2026-07-05 (Fase 0)
- **Sintoma:** `.agents/runtime/command-ledger.jsonl` com 1,76 GB (4.038 registros, ~435 KB/linha), commitado repetidamente → `.git` com 17 GB. Pré-commit exige registro novo de "leitura viva" a cada commit (o registro anterior é invalidado pelo próprio commit — esteira infinita). 277 scripts `check-*` vs. 0 páginas publicadas; ~52% dos commits do repo tocam maquinário de guarda, não produto.
- **Causa raiz:** contratos autorreferenciais (AGENTS.md/GOAL.md) que convertem cada falha em novo gate sobre o processo (não sobre o produto) e exigem prova burocrática de leitura/não-publicação a cada ciclo. O validador do ledger (`internal/workreuseledger/ledger.go`, 7.289 linhas) inclui polícia de linguagem (`work_reuse_git_dead_history_language` etc.).
- **Correção:** governança substituída por gates de produto (DEC-002): ledger congelado (sem novos appends gigantes), pré-commit leve focado em build/testes/gates de conteúdo.
- **Status:** **FECHADO em 2026-08-19**, verificado por medição, não por plano.
  O ledger está em **159.983.168 bytes** (não mais 1,76 GB) e com **mtime de 2026-07-12** —
  congelado há mais de um mês. O produtor (`tools/run-heavy-throttled`) declara o
  `artifact_claim` mas só escreve com `WIKI_HEAVY_FORCE_LEDGER=1`, e nenhum gate lê os
  appends (DEC-002). Ou seja: **não cresce mais**, que era o dano contínuo.
  O que sobrou é histórico, e sobre ele não há ação com retorno: o blob já está no pack do
  git (`size-pack` 3,04 GiB), então tirá-lo do índice hoje **não devolve um byte** — só
  reescrita de história faria isso, e reescrever história é destrutivo e proibido neste repo.
  Fechar aqui é registrar o que a medição diz, em vez de manter aberto um item cuja única
  ação possível é proibida.

## BUG-006 — Cadeia de release rígida em 10.000 e cartesiana (raiz do loop + trava de escala)
- **Data:** 2026-07-07 (Fase B)
- **Sintoma:** a fatia vertical n=34 não regenera: `generate-authorial-mass-editorial-quality-vectors` reprova com `refinement_quality_source_fingerprint_mismatch`, `..._artifact_stale`, `..._unexpected: context-*` e `..._missing_record: area-glossario`. O gerador de refinement quality (`internal/authorialmassrefinementquality/refinement_quality.go:381,394,395`) exige `SourceContentCount == authorialmassstock.TargetTotalContents` (=10000) e `ExpectedPairCount >= 1000000`.
- **Causa raiz:** a cadeia authorial_mass foi construída para o estoque v1 — exatamente 10.000 registros, agrupados por `scenario_id × context_id` cartesianos, com prova de escala por ≥1M pares intra-grupo. `TargetTotalContents = 10000` é constante hardcoded referenciada em ~15 pacotes (public_prose_candidate, scale_shards, contextcompat, refinement_quality, oráculos com `DefaultMinRecords=10000`). O estoque v2 é não-cartesiano (scenario/context vazios, agrupado por area/família, page_type variável) e testável em qualquer N. **Esta rigidez é a raiz mecânica do loop do Codex**: não se pode iterar/provar com amostra, só com 10.000 perfeitos de uma vez — e a publicação estava soldada (BUG-001), então cada ciclo só podia re-rodar o gerador pesado como detector de falha.
- **Correção (DEC-014):** desacoplar a cadeia do número mágico — total esperado vem do `stock_manifest.json` (fallback 10000, produção idêntica); agrupamento e gate de pares proporcionais à estrutura real do estoque (v2 agrupa por area/família); prova de escala (P3, ≥1M / milhões) migra para benchmark sintético dedicado (`internal/scaleindex`/`parallelbatch` já têm `SyntheticProbeRecords`), separada da validação de conteúdo.
- **Status:** aberto — próximo grande bloco de engenharia; especificado em DEC-014.

## BUG-005 — CTA aponta para página inexistente
- **Data:** 2026-07-06 (Fase B)
- **Sintoma:** `renderWhatsAppCTA` (`internal/render/render.go`) gera link para `/contato/advogado/?origem=...`, mas `content/pages.json` só tem `/`, `/fontes/planalto/` e `/buscar/` — todo clique no CTA daria 404.
- **Causa raiz:** a página de contato/triagem nunca foi criada; o CTA foi desenhado contra uma rota planejada e nenhum gate valida o destino do CTA.
- **Correção:** criar a página institucional `/contato/advogado/` (triagem digital: o que enviar, como funciona o atendimento remoto, aviso OAB; noindex — página utilitária, fora da contagem P0) + gate que valida que todo destino de CTA existe e responde 200.
- **Status:** **FECHADO** — medido em 2026-08-29: `/contato/advogado/` responde **200** na borda, com a sonda oficial. A página institucional existe. O status "aberto" era documentação que mentia, e comentário/registro que mente é bug pela R1 — foi assim que este item apareceu no reconhecimento da caça (M6). Fica registrado que a segunda metade do item original — *gate que valida que todo destino de CTA existe e responde 200* — continua sem implementação; ela é o resíduo real, e não a página.

## BUG-004 — RunAll sem cache para ~276 de 294 checks
- **Data:** 2026-07-05 (Fase 0)
- **Sintoma:** suíte de checks pesada; cada check recarrega repositório e relê JSONLs de 10k linhas do zero.
- **Causa raiz:** `internal/checks/checks.go` (10.277 linhas): `runWithContext` só injeta o `RunContext` cacheado em ~18 checks (switch nas linhas ~966–1019); os demais caem no default sem cache. `p0-cycle-close-indexable-10k` roda 28 checks-dependência via `Run` (sem contexto), cada um relendo tudo.
- **Correção:** propagar `RunContext` (ou cache tipado equivalente) a todos os checks que leem repositório/manifest/verdict; medir antes/depois.
- **Status:** aberto (correção planejada em PLAN.md, fase C).

## BUG-007 — Auditor global não detectava `intent_id` repetido entre shards
- **Data:** 2026-07-11 (Fase B/P0).
- **Sintoma:** 17 intents imobiliários tinham duas páginas ativas em shards finalizados; a contagem somava ambas, enquanto `audit_v2_pages.py --global` só verificava title/meta/H1/heading/12-gram. O validador Go detectava duplicata apenas depois de fundir o lote, tarde demais para o censo e a revisão editorial por shard.
- **Causa raiz:** a unicidade prevista no `INGEST_SPEC` não tinha gate global no produtor pré-ingestão. Tombstones existentes também não possuíam semântica autenticada de consolidação, de modo que simplesmente pular uma linha no merge perderia o original ou aceitaria retirada arbitrária.
- **Correção:** `intent_id_dup_global` simétrico em todos os shards; consolidação CAS dos 17 perdedores; archive integral com hashes/flags públicas falsas; verificação de vencedor, origem, conteúdo e archive no auditor Python e em `cmd/ingest-v2-stock`; regressões de duplicata exata, whitespace, destino ausente, autoalvo e archive ausente.
- **Status:** corrigido. O estoque vivo ficou sem intent ativo duplicado; publicação permaneceu zero.

## BUG-008 — Supervisor de checks girava indefinidamente após EACCES
- **Data:** 2026-07-20 (P0).
- **Sintoma:** `tools/check-authorial-mass-drafts` ficou mais de 30 s sem saída nem progresso; o processo repetia `mkdir(build.lock)` em loop.
- **Causa raiz:** cache `/tmp/opt-wiki-check-bin` `root:root`; o usuário `rafael` recebia EACCES. O `while` tratava qualquer falha de `mkdir` como contenção e fazia `continue` antes de orçamento, sleep ou diagnóstico. Cache HOME/tmp também podia reutilizar binário de outra worktree.
- **Correção:** `run-check` diferencia EEXIST de erro real, recusa cache/lock/symlink/owner alheio, publica metadata atomicamente, limita handshake, valida holder/PID e usa cache por worktree em `$ROOT/.cache/check-bin`; testes de loop, metadata parcial, mismatch e symlink.
- **Status:** `run-check` corrigido e commitado em `f8067928`; 6 testes focados em
  0,366 s, sintaxe/shellcheck/diff verdes. A família maior `run-go-cmd-cached` recebeu
  revisão adversarial e foi commitada em `dad121a3`; descritores autenticados fecham
  FIFO/symlink/TOCTOU, e 54/54 testes passaram em 42,2 s. Resta otimizar a varredura
  linear da árvore Go por closure/Merkle incremental quando o custo de código exigir;
  `data/content/public` não participa desse hash.

## BUG-009 — Déficit V2 calculado por subtração de linhas incompatíveis
- **Data:** 2026-07-20 (P0).
- **Sintoma:** o número 2.107 (`10.041−7.934`) era tratado como páginas faltantes.
- **Causa raiz:** 7.934 mistura partials, tombstones/skips, supersessões, 6 duplicatas ativas e 156 corpos fora do portfólio; contagem de linhas não prova uma relação canônica intent→corpo.
- **Correção:** contar interseção entre intent único do portfólio vivo e corpo ativo finalizado após supersessão; gate de título duplicado e checks de body agora falham fechado com journal ativo.
- **Status:** contador corrigido: 7.661 intents têm corpo; faltam 2.380 (2.341 sem registro +39 apenas skipped). A produção/correção desses corpos e o finish-forward do journal continuam P0.

## BUG-010 — Gate de aparência pública não detectava PT-BR mecânico
- **Data:** 2026-07-20 (P0).
- **Sintoma:** ensaio marcava `search_appearance_language_issues=[]` para títulos como “Indenização trabalhista: com acordo descumprido 7 dias”.
- **Causa raiz:** composição cartesiana de cenário/contexto e detector superficial aceitam fragmentos nominais/preposicionais sem relação natural.
- **Correção:** RCA sistêmico no produtor de title/meta/focus sentence e testes adversariais; não promover nem regenerar os 360 registros até correção.
- **Status:** aberto, agente corretivo em execução; todas as 360 páginas permanecem bloqueadas/noindex.

## BUG-011 — 401/403 DataJud contava como conector saudável
- **Data:** 2026-07-20 (P0).
- **Sintoma:** dois pares recentes com HTTP 401/403 zeravam mensagens de saúde apesar de nenhuma observação agregada válida.
- **Causa raiz:** fallback confundia alcance de servidor com autenticação, consulta e uso real da API oficial.
- **Correção:** 401/403 agora gera `datajud_connector_authentication_failed` e matriz sem live observado continua `planned_only`; reconciliação histórica e receipt transacional passam por preflight adversarial antes da rede.
- **Status:** correção em worktree/teste focal verde; operação real ainda não executada.

## BUG-012 — Capacidade de agentes confundida com configuração local e `CODEX_HOME` stale
- **Data:** 2026-07-20 (P0).
- **Sintoma:** após reinício, a ferramenta desta sessão expôs somente quatro agentes
  ativos no total, embora o dono já tenha operado mais de dez; tentativas anteriores
  também introduziram configuração não oficial e dificultaram retomar o Codex como
  usuário `rafael`.
- **Causa raiz:** a auditoria não encontrou teto persistente em
  `/home/rafael/.codex/config.toml` nem no repo: não há `agents.max_threads`, `workers`
  ou `agents.v2`, e o recurso oficial estável `multi_agent` está ativo. Havia, porém,
  um `CODEX_HOME` global stale no ambiente tmux; a sessão corrente já possuía override
  isolado correto. A documentação oficial viva acrescenta a distinção que faltava:
  `agents.max_threads` ausente usa o padrão Codex de 6, e a chave aceita somente um
  número; não existe valor oficial `adaptive`/`unlimited`. Portanto, o teto de quatro
  observado nesta ferramenta não é explicado pelo repo/config, não pode ser atribuído a
  eles sem evidência e não pode virar constante de arquitetura.
- **Correção:** removido somente o `CODEX_HOME` global stale do tmux; preservados config,
  autenticação e home isolado da sessão do usuário `rafael`; launchers global/repo
  comparados byte a byte; `codex doctor --json` e
  `codex --strict-config doctor --json` verdes. O launcher mantém
  `agents.max_threads` fora das camadas persistentes e aceita
  `--max-agents=N`/`AI_CODEX_MAX_THREADS=N`, traduzidos exclusivamente para
  `-c agents.max_threads=N` no processo novo; assim o dono/orquestrador escolhe a
  capacidade proporcional sem `workers=2`, `agents.v2` ou número congelado no projeto.
  Em 2026-07-20, o doctor estrito foi reexecutado em 1,04 s (`17 ok`, `1 idle`, zero
  warning/falha), com bancos íntegros e `multi_agent` ativo.
- **Status:** configuração local oficial e retomada auditadas/corrigidas; a capacidade
  efetiva da ferramenta corrente continua observada em quatro ativos totais e será
  reavaliada por sessão, sem hardcode nem falsa atribuição.

---

# Lote da CAÇA AOS BUGS — 2026-08-29

137 defeitos catalogados por 27 agentes (3 exploradores + 2 ondas de workflow,
cada frente com verificador adversarial), mais crítica Fable sobre o plano
inteiro e duas passadas de `advisor`. Plano operacional com evidência e comando
de cada item: `docs/goal/PLANO_CACA_BUGS_20260829.md`. Tasks:
`.agents/runtime/p0_frontboard.jsonl`, prefixo `caca-`.

Distribuição medida por script: **20 críticos · 53 graves · 37 médios · 27
leves**. Nenhum item foi cortado por severidade — a ordem da fila é a
severidade, não o critério de inclusão.

**18 suspeitas foram REFUTADAS e ficam registradas no plano.** Dado de agente
não se descarta, nem o derrubado: cada linha ali evita uma reinvestigação.

**FAMÍLIA-A (sistêmica, sem número próprio):** 42 arquivos leem
`public/sitemaps/` do disco (62 `*.xml` + 58 `.br`) em vez de derivar do índice
(34 shards, 10.336 URLs). Causa comum de BUG-013, BUG-014 e BUG-039 — a correção
é uma função única de "universo público", não três remendos.

**Três críticos caíram durante a própria redação do plano** (commits `9053fe77`,
`63ed4b2d`+`a8f1d824`, `42c6ea40`), o que fixou o PASSO ZERO: reproduzir a
medição antes de corrigir, sempre.

## BUG-013 — `wikijuridica-edge-warm.service` em falha crônica, e a causa é um glob
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `systemctl show` → `Result=timeout ExecMainStatus=15 ActiveState=failed`; duas execuções consecutivas mortas por SIGTERM (28/08 22:13 e 29/08 02:11) contra `TimeoutStartSec=45min`. Causa medida: `tools/warm-edge-cache:49` e `tools/check-edge-cache-coverage:78` leem `public/sitemaps/*.xml` do disco (62 arquivos, 18.772 `<loc>`) em vez do índice `public/sitemap.xml` (34 shards, 10.336 URLs únicas) — universo inflado em +81,6%. Com `--so-frios` cada URL fria custa HEAD+GET, e o trabalho deixa de caber na janela. Correção: derivar o universo do índice, não do disco. Verificação: a unit completa dentro da janela e `edge_cache_warm.jsonl` volta a receber linha.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-013) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — unit ja Result=success apos 42c6ea40; a FONTE tambem foi corrigida: paginas vem do indice, shards em carencia seguem aquecidos por desenho; 10.465 entradas, 0 duplicata (commit 32313dfd).

## BUG-014 — O alerta crítico que a mesma inflação produz está 81% errado
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `edge_cache_coverage.jsonl` publica `universo_urls: 18.726` e o alerta afirma que "~18.726 páginas devolveriam 530 se o túnel cair". O número real é 10.336. Alerta crítico com número errado dessensibiliza para o alerta verdadeiro.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-014) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — universo do check-edge-cache-coverage de 18.731 para 10.302, derivado do indice (commit 32313dfd).

## BUG-015 — 3 rotas anunciadas na superfície de máquina respondem 404
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `/.well-known/agent-skills/index.json` anuncia 13 skills; os bundles `conversar-com-o-agente-a2a.tar.gz`, `obter-credencial-de-agente.tar.gz` e `usar-o-servidor-mcp.tar.gz` respondem 404 na origem e na borda. Causa-raiz que eu mesmo isolei: os três arquivos existem em `content/agent-skills/dist/` (medido) e não são copiados para `public/.well-known/agent-skills/` — `find public -name '.tar.gz'` devolve 0. Correção: o build/deploy passa a publicar os archives. Verificação: os 3 respondem 200 e `check-agent-surface-live` passa.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-015) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — causa-raiz entre camadas: Go 8089 servia os 3 com 200, nginx 8088 devolvia 404 text/html porque a allowlist de extensao nao conhece .gz; corrigido com location ^~ /.well-known/agent-skills/ (proxy ao Go), que vence regex em nginx; nginx -t ok + reload; depois: 13 de 13 URLs anunciadas -> 200 na origem e a versionada -> 200 na borda; check-paridade-go-nginx pass; check-http-smoke pass (commit 2910e73e).

## BUG-016 — Falso verde: o gate de disco aprova o que a produção reprova
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `./tools/check-agent-skills-discovery` → exit 0 ("pass") com os 3 bundles 404 no ar, porque confere o manifesto contra `content/`. `./tools/check-agent-surface-live` → exit 1, "10 de 13 conferem — divergem: ['conversar-com-o-agente-a2a','obter-credencial-de-agente','usar-o-servidor-mcp']". O gate que enxerga a verdade não está no gatilho da onda diária. Correção: o gate de disco passa a exigir o artefato publicado, e o gate de produção entra no gatilho. Esta é uma família, não um caso: procurar todo par "gate de disco verde × gate de produção vermelho".
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-016) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — o par 'gate de disco verde x producao vermelha' fechado nas duas pontas: check-agent-surface-live (que enxergava a verdade e nao estava em gatilho nenhum) entrou na onda de qualidade diaria, e internal/httpserver ganhou teste que percorre CADA URL anunciada no indice exigindo 200 com corpo gzip real (commit 2910e73e).

## BUG-017 — A onda diária termina "success" com o pipeline quebrado
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `daily-content` de 28/08 registrou `ONDA DIÁRIA PARCIAL — falhou em: check-frescor-canal-diario check-derived-authorial-floor check-lastmod-causalidade` e as etapas seguintes não rodaram; a unit terminou `Result=success` por desenho. Medido por mim agora: `check-frescor-canal-diario` exit 1 ("2 canais estagnados além da tolerância") e `check-derived-authorial-floor` exit 1; `check-lastmod-causalidade` já passa (exit 0) — corrigido desde então. Correção: os dois defeitos de conteúdo + o systemd deixar de reportar verde sobre pipeline parcial.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-017) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-017` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-018 — Alerta crítico falso-aberto há 37 h, por falta de reconciliador
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `borda-origem` (severidade crítica, "/healthz devolveu 503") segue aberta com a condição comprovadamente resolvida: `/healthz` = 200 na borda e na origem, `edge_live` 6× `ok:true`, `portal_health` `"problems": []`, `tunnel_health_state` `degradado: false`. A chave só fecha por `tools/notify-owner --resolvido` manual. Correção: reconciliador que fecha por evidência da série viva, com registro de quem fechou e por quê.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-018) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — reconciliador por evidencia acoplado a unit horaria; primeira execucao fechou 3 chaves (borda-origem critica de 38h inclusa), manteve 2 com problema real e nao tocou 4 sem criterio (commit 2093fc95).

## BUG-019 — `./tools/check-http-smoke` estoura 90 s
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Medido: exit 124 no timeout de 90 s enquanto `contrato-vs-medicao`, `arquitetura-fiel`, `v2-portfolio-pairing`, `portal-health`, `public-sem-lixo` e `paridade-go-nginx` passam em segundos. Última linha antes de morrer: `run-check: built cached check binary bin=/opt/wiki/.cache/check-bin/check`. Lentidão é bug — proibido "corrigir" aumentando o timeout.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-019) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `2046adb4`). Não era travamento: o gate custava 67.567 ms e o ledger declarava 3.000 ms. A correção foi ALGORITMO, não orçamento — as 10.116 rotas eram exercitadas em série num núcleo (43,22 s dos 67,57 s no laço, 39,85 s em `ondemand.RenderPath`) e viraram pool limitado a `GOMAXPROCS`, com ordem e cobertura idênticas byte a byte, provadas por teste com respostas terminando em ordem inversa. Medido depois: **49.212 ms**. O ganho parou em 1,7x porque sobram ~20 s SERIAIS de boot (`httpserver.New` 11,4 s pelo índice bleve, `publishedmanifest.Validate` 10,0 s dos quais 8,4 s são SHA-256 de 10 mil HTMLs) — trabalho do boot, não do laço, e explicado no código em vez de virar orçamento inflado. Ledger corrigido para `medium/100000`.

## BUG-020 — `check-untracked-product-inventory` reprova: produto untracked
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `exit 1` — `untracked_produto=70 untracked_produto_stale=4 max_age_hours=24`. Entre os untracked: `data/research/daily//2026-08-28.jsonl` (pesquisa do dia), `data/ops/access/access-2026-08-{28,29}.jsonl`, receipts de ingest, e backups `.pre-` de config de produção que são única cópia. O contrato manda commitar por pathspec ou classificar como efêmero — nunca deletar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-020) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — check-untracked-product-inventory: exit 1 (70 produtos, 4 stale) -> exit 0 (0 stale) (commit b24db0f3).

## BUG-021 — BUG-004 continua aberto e a superfície cresceu
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Medido hoje em `internal/checks/checks.go`: `Names` tem 322 gates; só 68 alcançam caminho ctx-aware (26 no switch `runWithContext:1346-1414`, 16 no `contextCheckRegistry:1421-1451`, 26 pelo ramo P0), e desses apenas 42 consomem artefato cacheado. 254 de 322 (78,9%) caem em `run()` sem cache. O BUGLOG registra "~276 de 294" e "checks.go (10.277 linhas)" — números de julho; hoje o arquivo tem 12.254 linhas. Pior: `run_context_parallel.go:118` chama `setFrozen(true)` antes das 6 goroutines, então na fase paralela (264 gates `parallel_safe`) o cache computa e não grava — só os 17 artefatos do `prewarmParallelSharedState:167-188` são HIT.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-021) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-021` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-022 — Gate registrado em `run()` mas fora de `Names` — nunca executado
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `case "bigcache-byte-cache-evidence"` existe em `run()` e não está em `Names` nem no `check_performance_ledger.jsonl`, logo `RunAll` nunca o roda — apesar de existirem `tools/check-bigcache-byte-cache-evidence`, `cmd/generate/gen_b_bigcache_byte_cache_evidence.go` e referências de cobertura em `internal/ossscaleintegration/coverage.go:1607,1613`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-022) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — gate estava em run() e fora de Names (RunAll nunca o rodava) E vermelho por fonte impossivel (7.959 registros para alvo de 10.000). Fonte trocada para o published_manifest, teto de 10.000 virou PISO derivado, e teste por AST impede novo case orfao (commit 6797e467).

## BUG-023 — 10 `tools/check-*` escrevem em disco — violação do contrato
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `CLAUDE.md:208-209` diz que `check-*` é read-only. Medido: `check-crawler-error-budget:315` e `check-edge-traffic:713` fazem append em `data/ops/`; `check-network-health:152-159` faz `os.replace` de estado; `check-invalidated-layer-recovery:132` faz `os.rename` na árvore de trabalho (o mais grave); mais 6 que escrevem sob flag.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-023) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `976f0b0c`), junto com BUG-075 e BUG-123 — os três eram a mesma família contada com critérios diferentes. Contagem republicada COM o critério: escreve = a execução altera bytes persistentes do projeto (`data/`, `public/`, worktree versionada, estado do systemd), sem contar `/tmp`, `mktemp`, `var/`, `.cache/` nem sandbox de selftest. Por esse critério eram **20 antes e 18 depois** — e a DEC-040, decidida no mesmo dia, isenta o canal de alerta ao dono, o que leva a **8**. A causa-raiz não é "gate que escreve": é papel misturado num arquivo só. `check-brotli-e-recomprimir` (que invocava o gerador e reescrevia as gêmeas `.br` do acervo SERVIDO, de hora em hora, por timer) virou `repair-brotli-cobertura`, com a unit repontada NO MESMO COMMIT — o timer horário tem de continuar chamando quem recomprime, senão as gêmeas apodrecem em silêncio. `check-invalidated-layer-recovery` (que fazia `os.rename` na árvore de trabalho) perdeu o `--recover`, e a restauração foi para `repair-invalidated-layer`, que **importa** a varredura do próprio check em vez de duplicá-la. Cada lado ganhou selftest que prova o read-only por dois instrumentos independentes: digital da árvore (caminho, tamanho, `mtime_ns`, sha256) e diretório em modo `0500` — a digital sozinha não distingue "não escreveu" de "escreveu e restaurou".

## BUG-024 — `internal/lexml/parse.go:224-243` descarta erro em data de norma
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Seis `strconv` com `, _ :=` em dia/mês/ano: data de vigência de lei federal vira `0` em silêncio. Mesma classe em `cmd/collect-stf-informativo/main.go:444` e `cmd/collect-stj-precedentes/main.go:257` (`_ = json.Unmarshal` — JSON corrompido vira struct zerada sem ninguém saber).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-024) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** parcialmente resolvido — REFUTADO em lexml (regex garante digitos + atribuiData valida com time.Parse: erro inalcancavel); CONFIRMADO e corrigido em procfs_linux.go, onde /proc e lido em corrida e PPID=0 falsearia a arvore de processos (commit a7d5b43f).

## BUG-025 — `panic` em pipeline que alimenta três gates
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `internal/quality/quality.go:600` faz `panic` apoiado num comentário que afirma que a função é pura. `quality` alimenta `no-duplicate-content`, `mechanical-content` e `canonicals` — os três ctx-aware, logo rodam na região onde `run_context_parallel.go:140` (`runCheckRecovered`) converte panic em "gate reprovou". Falha de código fica indistinguível de achado de conteúdo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-025) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `c2fe3257`). Era o caso INALCANÇÁVEL — e o comentário que o justificava provava só metade. Ele creditava a inalcançabilidade à pureza do callback e ignorava que `pipeline.MapIndexed` tem OUTRA fonte de erro: `groupCtx.Err()` e `group.Wait()`. Lido o fonte do `errgroup` na versão fixada em `go.mod`, `cancel` só ocorre (a) pelo pai, (b) em `Go` quando `f()` devolve erro não-nil, (c) em `Wait` depois de todos os workers retornarem — e com pai `context.Background()` e callback puro nenhuma das três alcança. O `panic` virou asserção documentada com a prova das duas pernas e a instrução do que fazer no dia em que a invariante cair: propagar erro, **nunca** reativar o panic, porque na região paralela `runCheckRecovered` o converte em "gate reprovou" e uma falha de código fica indistinguível de achado de conteúdo. O teste do gatilho real está um nível abaixo, em `internal/pipeline`.

## BUG-026 — 114 testes ficam verdes quando o corpus vivo está ausente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** De 291 `t.Skip`, 114 pulam por dado ausente (ex.: `internal/textotruncado/textotruncado_test.go:114` "estoque v2 ausente neste checkout", `internal/crawl/crawl_test.go:607` `public/robots.txt` não gerado). Verde silencioso é pior que vermelho.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-026) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `14152a0f`). A medição do catálogo (114 de 291) contava cópia morta: a mesma varredura sem escopo devolve 7.213 sites, incluindo `.agents/runtime/tmp_rescue/`, `.cache/gate-build/` e o próprio `gomodcache`. Restrita a `internal/` e `cmd/`, a conta real era 279 sites, 56 por dado ausente; depois desta passada, 268 e 45. O critério de corte é único e verificável, não opinião: `git ls-files` devolve o dado → ausência é defeito do checkout e o teste FALHA; dado gerado em runtime (`public/` está no `.gitignore`) → skip honesto. **O achado que justifica a passada inteira**: ao trocar o skip por Fatal, o teste da guarda de promessa de resultado (Provimento OAB 205/2021, o BUG-117) ficou VERMELHO — `legalmarketingpolicy.LoadPolicy` e `content.LoadRepository` resolvem a raiz por `findProjectRoot`, que sobe até achar `go.mod`, e um `t.TempDir()` em `/tmp` não tem esse marcador em nenhum ancestral. O gate **nunca era executado**. Atrás desse, um segundo defeito: a fixture escrevia `content/pages.json` como `{"pages": […]}` e o arquivo real é um ARRAY. Só agora está provado que a guarda acusa a promessa afirmada e não acusa a negada.

## BUG-027 — Documentação que mente (R1 é explícita: isso é bug)
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `docs/goal/BUGLOG.md:47` marca BUG-005 como "aberto" ("CTA aponta para página inexistente") — medido: `/contato/advogado/` existe e responde 200. `CLAUDE.md:154,156` declara 10.107 páginas; medido 10.111 (`time_to_first_crawl_daily.jsonl` também carrega `rotas_publicadas: 10107`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-027) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `58c158a3`)

## BUG-028 — 28 shards de sitemap órfãos servidos com 200
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** 62 arquivos em `public/sitemaps/`, 34 no índice. Estão em carência legítima (mtime 28/08, `check-sitemap-shard-grace` exit 0 os reconhece) — não é o defeito; o defeito é o consumidor lendo o disco (BUG-013). Mas falta série periódica medindo "disco × índice": `sitemap_shard_grace.jsonl` tem 1 linha, de 28/08 20:39, obsoleta 45 min depois.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-028) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `2346019b`)

## BUG-029 — Taxa de 304 na borda é 0,02% e ninguém a mede por bot
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** Com `etag off` (`ops/nginx/standalone/nginx.conf:703`) a revalidação depende só de `Last-Modified`. Em 7 dias: 55.256 requisições de bot, 9 respostas 304. O log já instrumenta `inm=`/`ims=` e nenhum consumidor agrega. HIT de borda 18,3% ⇒ cada MISS transfere ~28 KB inteiros.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-029) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-030 — Bots recebendo erro sem nenhum alerta
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `facebookexternalhit` 1.291× 404 (28% do tráfego dele); `cloudflare-agentreadiness` 396× 404; `amazonbot` 356× 404, 18× 503 e 9.343× 301 (45% do tráfego dele gasto em redirect). `crawler_error_budget` reporta `errors_total: 0` porque só conta bot verificado — o dado existe na borda e ninguém o lê.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-030) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `e55d2b0b`)

## BUG-031 — Queda de revisita de −99% em cinco bots
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `claudebot` 43.065 (07/08) → `[25,34,3]`; `gptbot` 16.456 → `[1,1,136]`; `meta-externalagent` 10.606 → `[6281,128,0]`; `yandexbot` −99,4%; `googlebot` 4.297 → `[19,88,7]`. Cobertura acumulada segue 99,7% — o acervo foi rastreado; o que caiu foi a revisita. Pela R6, isso é defeito de engenharia até prova medida em contrário.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-031) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-031` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-032 — Config morta que parece viva (armadilha ativa)
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `ops/nginx/wikijuridica.conf` (78 KB) diverge da config viva em 413 linhas e se auto-declara `# ═══ NAO-CARREGADO-EM-PRODUCAO ═══`. Idem `ops/nginx/standalone/server.conf` e `bot-policy.conf` — nenhum `include` os alcança. Editar o arquivo errado regride produção.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-032) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `3db1a3e5`)

## BUG-033 — `internal/agentsurface` e `internal/pageinline` sem nenhum teste
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** São, respectivamente, a fonte única das rotas de máquina e a constante do único script inline cujo hash a CSP autoriza. Um byte errado ali mata o analytics em 10 mil páginas em silêncio. 278 de 760 pacotes (36,6%) não têm teste — estes dois são os que mais doem.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-033) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-033` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-034 — 169 `Lock()` sem `defer Unlock()` adjacente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** Candidatos concentrados em `internal/v2ingest/`, `internal/sitemapstream/`, `internal/batchdrafts/`, `internal/search/manager.go`. Não é veredito: é a lista que `go vet -copylocks` + leitura de caminho de retorno tem de triar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-034) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-034` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-035 — 1,34 GB de binários de build soltos na raiz do repositório
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** 63 executáveis ELF em `/opt/wiki/` (`check` com 241 MB, `checks.test` com 178 MB, `promote-authorial-mass-public-release` com 57 MB…). Todos gitignored exceto `seed-sitemap-registry` (8,8 MB, untracked e não ignorado). Sintoma de `go build` sem `-o`: o binário cai no cwd.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-035) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — carimbado com o sha do commit que o fechou (commit 2f5eb413).

## BUG-036 — Arquivos de 0 byte com nome de módulo Python na raiz
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** `./shutil`, `./os`, `./time`, `./re`, `./8`, `./9` — resíduo de redirecionamento de shell mal formado (`2>9`, `> os`). Classificar e limpar com registro.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-036) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — carimbado com o sha do commit que o fechou (commit 2f5eb413).

## BUG-037 — 65 `tools/_tmp_fix_*.py` untracked
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** Zero rastreados. São correções pontuais de páginas de imobiliário/consumidor/ previdenciário. O contrato proíbe deletar: classificar (produto → commit, efêmero → `.gitignore` com o porquê).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-037) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO (investigado e derrubado por medição — não era defeito) — carimbado com o sha do commit que o fechou (commit 2f5eb413).

## BUG-038 — `.claude/settings.json` com 53 linhas removidas, não commitado
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** O bloco `enabledPlugins` inteiro sumiu do arquivo. Apurar a origem antes de qualquer commit — pode ser mudança deliberada do dono ou perda acidental.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-038) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-038` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-039 — `./tools/check-internal-link-floor` está QUEBRADO, não reprovando
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1 in position 0` em `tools/check-internal-link-floor:63`. O gate do piso de links internos — SEO puro — não mede nada há tempo indeterminado, e devolve exit 1, que qualquer runner lê como "reprovou por conteúdo". Membro da Classe A da FAMÍLIA-A.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-039) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — check-internal-link-floor saiu de UnicodeDecodeError para analise real (e acusou /jurisprudencia/stf-adi-5502/ abaixo do piso) (commit 32313dfd).

## BUG-040 — 1.707 páginas publicadas só têm link de hub, sem spokes
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `./tools/check-v2-internal-link-graph` (exit 0): `content_pages=10111 area_hubs=32 pages_with_area_hub=10111 pages_with_spokes=8404 pages_hub_only=1707`. O gate passa verde porque o piso é o hub; 16,9% do acervo tem malha interna mínima, que é o pior sinal de autoridade que se pode dar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-040) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-040` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-041 — Os dois defeitos de conteúdo que derrubam a onda diária, medidos
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `check-frescor-canal-diario` (exit 1): coleta OK, publicação não avançou — `diarios` máx. publicado 26/08 vs coletado 28/08 (gap 3 d > 1 d); `noticias` publicado 27/08 vs coletado 28/08 (gap 2 d). O coletor roda, o publicador não. `check-derived-authorial-floor` (exit 1): (a) `/jurisprudencia/stf-re-1037396/` com 74,6% de texto oficial citado (corpo 2.050 palavras, citado 1.530, maior bloco 1.443) contra o teto de 70% da DEC-032; (b) 3 pares acima de 0,70 de similaridade em `stj-tema-derivado` (0,7572 / 0,7563 / 0,7042) — molde repetido com número trocado. O próprio gate prescreve: correção no gerador (`cmd/generate-stj-tema-pages` etc.), nunca no JSONL à mão, nunca baixando o limiar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-041) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-041` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-042 — 103 rotas servem PT-BR sem acento em texto VISÍVEL
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** 180 ocorrências em `official_sources[].name` / `.anchor_claim`, que o `internal/render` imprime no bloco de fontes. Confirmei no HTML servido: `grep 'Codigo de Defesa do Consumidor' public/leis/cdc-art-22/index.html` casa 2×. Outras: "Convencao da Apostila da Haia", "regulamentos tecnicos e programas de certificacao", "impoe boa-fe e lealdade também na execucao" (o "também" acentuado ao lado de quatro palavras sem acento denuncia texto de duas procedências). Palavras mais frequentes: `nao`(39), `servico`(12), `contribuicao`(11), `remuneracao`(10). O `PROJECT_GAPS.md:42` já previa este gate ("acento em `official_sources[].name` — `render.go:180`") e ele nunca foi construído. Falha P0 do contrato de conteúdo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-042) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — 170 rotas e 355 correcoes em official_sources[].name e .anchor_claim, os dois campos que internal/render imprime no bloco de proveniencia. BUG-042 (acento) e BUG-055 (tipografia 'Lei no' e 'art. 4o') eram o MESMO defeito na mesma string. Dicionario so de palavras inequivocas: a primeira medicao usou lista maior e teve falso positivo em massa -- 'processo' aparece 1.673 vezes e esta CORRETO sem acento. Teste com 8 frases corretas do acervo que nao podem ser tocadas. Conferido campo a campo contra o HEAD: ZERO campos fora dos dois alvo. Diff de 170/170 apos o comando passar a preservar byte a byte a linha intocada (a 1a versao produzia 978, com 808 de ruido por reordenacao de chaves). Idempotente (commit 5958c532).

## BUG-043 — 19 colisões de `intent_id` no estoque, cada uma com uma cópia VAZIA — confirmado por medição própria (`uniq -d` → 19). Em cada par, uma
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** cópia completa (600–820 palavras, 3–5 fontes) e uma totalmente vazia (`opening:""`, `sections:[]`, `faq:[]`, `word_count:null`). Hoje o ar está correto (19/19 renderizam a cópia boa, verificado no HTML), mas o que impede 19 rotas de virarem páginas vazias é a ordenação de shard — e em 2 casos (`codex-educacao-portfolio-aereo-r03`) a vazia ordena antes. Nenhum gate detecta: `critical_reasons` só conhece `intencao_pulada_deliberadamente`, nunca `sem_corpo` nem `rota_colidente`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-043) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO (investigado e derrubado por medição — não era defeito) — as 19 copias vazias sao TOMBSTONES deliberados de consolidacao datada 2026-07-11: skipped=true, skip_reason=duplicate_intent_consolidated, superseded_by, superseded_record_sha256, supersession_archive, e publication/render/sitemap_allowed=false com index_policy=noindex. Medido: 0 de 19 sem protecao completa, e as 19 estao no manifesto pela copia BOA. O gate v2-cross-shard-collision ja existe e ja trata tombstone (criterio de ativo: !Skipped && superseded_by vazio) -- nao e ordenacao de shard que protege, como o catalogo dizia. A lacuna fina que era real (tombstone com flag de publicacao ligada seria invisivel ao gate e visivel ao publicador) foi fechada por teste: 119 tombstones, 0 incoerentes (commit ff5c06b7).

## BUG-044 — 136 páginas acima do limiar anti-template, e o gate nunca rodou sobre elas — medição própria de Jaccard 3-grama/5-grama em 103.873
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** pares intra-família: 363 pares ≥ 0,70 (3g) e 62 ≥ 0,70 (5g), pico 0,8767 / 0,8172 (`dia-pr-20260825` × `dia-pr-20260821`). Pior que o caso documentado no CLAUDE.md (0,775 / 0,696). Todas em `lane: derivada_de_fonte_oficial` (`diarios-municipais`, `stj-tema-derivado`, `stj-sumula-derivada`), e nenhuma carrega motivo de similaridade no ledger de severidade — o universo B "não tem varredura de risco" por definição do gerador. Correção no gerador de cada canal, nunca baixando o limiar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-044) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** parcialmente resolvido — os 363 pares >=0,70 que o catalogo media NAO existem mais: medicao independente em Python sobre a familia diarios-municipais devolve ZERO, com pico de 0,5719 no par que o proprio gerador reporta como 62% igual. O que RESTA sao 2 pares reais, achados pelo auditor novo (BUG-045) na familia stj-tema-derivado: jur-stj-tema-41x40 (3g=0,7496) e 329x327 (3g=0,7440). Ambos com 5-grama ABAIXO do limiar, isto e, invisiveis ao criterio antigo. A correcao deles e no gerador cmd/generate-stj-tema-pages, nunca baixando o limiar -- por isso fica PARCIAL: a medicao esta feita e vigiada por gate, o conserto do gerador nao.

## BUG-045 — O auditor de similaridade global é vazio por construção
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `authorial_mass_global_similarity_audit.jsonl`: `expected_pairs: 31.668.861`, `compared_pairs: 123` (0,0004%), `global_all_pairs_compared: false`, `max_similarity: 0`. E aponta para a camada antiga (`authorial_mass_drafts`), não para `data/editorial/v2_pages/`. É exatamente isso que os 5.600 registros com `batch_global_similarity_refutado_por_medicao` significam.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-045) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — auditor novo para o ACERVO (o antigo media a esteira morta: compared_pairs 123 de 31.668.861, source_layers=authorial_mass_drafts). Cap declarado no relatorio: 1.040.544 pares intra-familia de 51.222.381 globais. Metrica 3g E 5g, reprovando pelo pior caso -- e os 2 achados reais provam: jur-stj-tema-41x40 (3g=0,7496 5g=0,6645) e 329x327 (3g=0,7440 5g=0,6750), ambos invisiveis a um auditor de 5-grama. Pre-filtro MinHash bottom-k: 1.603 pares chegam ao Jaccard exato. A primeira formula da estimativa estava errada (dividia pelo menor sketch) e descartava 99,1%; corrigida para bottom-k por uniao, com teste medindo fidelidade (exato 0,8000 = estimativa 0,8000). Conferencia independente em Python sobre diarios-municipais: 0 pares >=0,70, pico 0,5719 -- as duas implementacoes concordam (commit 193b904b).

## BUG-046 — O corpus de conferência legal erra nos dois sentidos e se declara confiável
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** confirmei: `data/legal-corpus/clt.json` não tem os arts. 189 e 195 (que existem na CLT), tem 1.012 artigos, e traz `"confiavel_para_acusar_divergencia": true`. `cpc.json` tem chaves até o art. 2027 (o CPC termina no 1.072). Consequência medida: das 13 "atribuições inexistentes" encontradas, 11 são lacunas do corpus e 2 são falso-positivo de regex — zero erros reais de atribuição em 9.741 citações verificadas. Ou seja: o instrumento que deveria proteger a classe P1 permanente hoje só produz falso positivo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-046) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — as duas metades fechadas. CONTAMINACAO (): 4 artigos de outra lei movidos para articles_fora_do_diploma (cpc art.2027 = art. 2.027 do Codigo Civil; lei_12653 art.135-A = do Codigo Penal; lei_8245 arts.167 e 169 = pontilhado de omissao), detectados por salto >=25 -- limiar calibrado sobre os 28 diplomas, onde o maior salto legitimo e 12 e os contaminados sao 77/131/955, sem nada entre 12 e 77. LACUNA (070bd125): o Planalto escreve 'Art. . 189' com ponto duplicado em 13 dispositivos da CLT, e esses 13 eram exatamente as 13 lacunas do corpus -- correspondencia de 100%. Depois: CLT com 922 artigos e ZERO lacunas, arts. 189 e 195 integros. Gate novo legal-corpus-integrity: pass (commit 070bd125).

## BUG-047 — `data/ops/refinement_queue.jsonl` é fila sem consumidor, com produtor não idempotente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `grep -rn refinement_queue` devolve uma única referência em todo o repo, e é a de escrita (`tools/run-daily-content:603`). A linha de 2026-08-26 aparece 4× idêntica porque o produtor faz `open(…,"a")` sempre que o log do dia contém "achado MÉDIO". 259 achados de `source_url_not_official_nor_registered` enfileirados em 28/08 que ninguém lê.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-047) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — fila com produtor idempotente (a linha do dia passa a ser substituida; a fila existente foi desduplicada de 7 para 4 linhas, com 2026-08-26 aparecendo 4x identicas) e CONSUMIDOR novo tools/check-refinamento-tendencia ligado a onda de qualidade diaria. Ele reprova duplicata e crescimento sustentado por 3 leituras, e NAO reprova a divida existir -- medio publica por decisao do dono, e gate vermelho permanente contra politica deliberada seria desligado. Serie impressa: 82, 205, 205, 261; 259 dos 261 sao source_url_not_official_nor_registered, corrigido hoje pelo source_id curado (commit c2349b7f).

## BUG-048 — `word_count` declarado diverge do real em 8.358 de 10.130
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Tokenizador divergente (p50 = 3 palavras, máx. 96), concentrado em `trabalhista-w3-07` e `trabalhista-36`. Não é fabricação — mas o efeito é real: 52 páginas estão do lado errado do limiar 250–400 que decide severidade média (1.429 pela medição × 1.377 pelo campo).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-048) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `47db4fb1`)

## BUG-049 — Zero páginas têm o tripé fonte = URL + data + hash
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `official_sources` em `v2_pages` não tem campo de hash de conteúdo. Os `sha256` em `v2_source_provenance.jsonl` são de registro/shard, com `"verification_scope": "upstream_metadata_only_not_network_rechecked_by_ingest"` e `ingest_live_recheck_performed: false`. Verificação de fonte hoje é propagação de metadado, não fato de rede. Somando: 135 fontes sem `verified_at` (69 páginas), 648 com status ≠ 200 (520 páginas), 748 páginas com URL de fonte em `.jsp/.asp/.aspx`, 159 em `temas_repetitivos`, 131 em `portal.stf …asp?` — exatamente o gate que `PROJECT_GAPS.md:36` pedia.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-049) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-049` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-050 — Zero `publication_allowed: true` em 10.230 registros do estoque, com 10.111 rotas `index` no ar — confirmado por contagem própria.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `public_path` vazio ou ausente em 10.230/10.230. Os campos de gate do estoque canônico são decorativos: a autorização real vive só no manifesto. Ou o publicador não os consulta (e então são teatro), ou consulta e há um caminho de bypass — nos dois casos é defeito de contrato a fechar.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-050) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-050` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-051 — Três ledgers discordam sobre a mesma partição
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** crítico 100 (`v2_publication_severity.jsonl`, vivo) × 119 (`data/ops/v2_publication_severity_summary.json`, estagnado em 06/08) × universo B 2.377 / 2.390 / 1.763 (o terceiro na docstring do gerador). O summary defasado em 22 dias é o artefato legível por humano.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-051) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-051` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-052 — 9.385 páginas publicadas (92,8%) carregam erro médio pendente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `fonte_insuficiente` 1.378 · `corpo_entre_250_e_400_palavras` 1.372 · `reprovada_por_agente_sem_justificativa` 131 · `sem_fonte_oficial` 100 · `blocker_pipeline` 2.359 · `batch_global_similarity_refutado_por_medicao` 5.600. Publicar e refinar é a ordem do dono — mas a fila de refino é a que não tem consumidor (BUG-047). A dívida está contabilizada e parada.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-052) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-052` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-053 — 7 produtos untracked (~75 MB), um deles citado por sha em arquivo versionado — `data/ops/access/access-2026-08-{28,29}.jsonl`,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `data/research/daily/{diarios-municipais,normas-federais,noticias-oficiais}/2026-08-28.jsonl` e dois recibos em `data/ops/v2_ingest_terminal_receipts/`. Todos têm irmãos rastreados. `stock_manifest.json` (versionado) referencia `transaction=v2-rewrite-v5-9cf36d95…`, cujo recibo não está no repositório — o manifesto aponta para uma prova ausente.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-053) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — 7 produtos commitados por pathspec; o recibo v2-rewrite-v5-9cf36d95 que o stock_manifest.json citava por sha agora existe no repo (commit 8049936a).

## BUG-054 — ~585 MB de ruído sem regra no `.gitignore`
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `.agents/runtime/pages.json.antes-` e `.pre-` (73 MB cada), `tmp_rescue/20260828/` (439 MB), backups de config de produção. O `.gitignore` tem 312+ linhas e não cobre o padrão `.pre-` / `.antes-`, que é a convenção mais usada do próprio projeto. Classificar — nunca deletar: alguns são única cópia de config de produção.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-054) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — classificacao item a item no .gitignore (nunca padrao cego .pre-*): backup de dado com original versionado + log de ingest; config unica copia PRESERVADA fora do ignore (commit b24db0f3).

## BUG-055 — Tipografia PT-BR quebrada em 47 rotas servidas — achado meu
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** ao dimensionar o BUG-042, medindo o HTML servido: 45 rotas trazem "Decreto-Lei no 2.848/1940" (falta o `nº`) e 3 trazem "art. 4o" (falta o `º`). Aparece no bloco "Proveniência", visível ao visitante. Minha varredura independente do HTML servido, com lista restrita de palavras, achou 57 rotas / 73 ocorrências de falta de acento — recorte menor que as 103 do estoque, e por isso os dois números convivem: um mede o dado, o outro mede o que o leitor vê. A correção é no gerador da camada de fonte, e fecha os dois.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-055) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — 170 rotas e 355 correcoes em official_sources[].name e .anchor_claim, os dois campos que internal/render imprime no bloco de proveniencia. BUG-042 (acento) e BUG-055 (tipografia 'Lei no' e 'art. 4o') eram o MESMO defeito na mesma string. Dicionario so de palavras inequivocas: a primeira medicao usou lista maior e teve falso positivo em massa -- 'processo' aparece 1.673 vezes e esta CORRETO sem acento. Teste com 8 frases corretas do acervo que nao podem ser tocadas. Conferido campo a campo contra o HEAD: ZERO campos fora dos dois alvo. Diff de 170/170 apos o comando passar a preservar byte a byte a linha intocada (a 1a versao produzia 978, com 808 de ruido por reordenacao de chaves). Idempotente (commit 5958c532).

## BUG-056 — CVE VIVA no `go.mod` raiz, vermelha e invisível desde 28/07
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `osv-scanner` acusa GO-2026-5932 em `golang.org/x/crypto v0.55.0` (confirmei: `go.mod:103`, `// indirect`). O gate `sca-osv-scan` está `fail` desde 2026-07-28 e ninguém o executa. Correção: subir a versão corrigida, `go mod tidy`, re-rodar o gate — commit Go, serializado com `flock`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-056) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — a correcao prescrita no catalogo (subir a versao) NAO era executavel: go list -m -versions termina em v0.55.0, a propria versao afetada. Tres defeitos empilhados impediam de tratar: (1) o runner chamava sca-osv-scan, gate inexistente; (2) o scan do produto rodava SEM --config, entao excecao fundamentada era impossivel no root -- ganhou config propria, separada da de tools/sca para nao herdar as 5 excecoes do Docker; (3) a politica so aceitava razao com 'tools/sca'+'transitive', o que obrigaria a mentir numa CVE do produto -- ampliada com classe 'codigo nao alcancado' MAIS dura, exigindo tripe verificavel (nao importado + comando + situacao da correcao). Depois: sca_osv_root_failed AUSENTE e GO-2026-5932 fora do log (commit 80565954).

## BUG-057 — `go vet` não roda em lugar nenhum — o runner existe e está quebrado pela armadilha que o próprio CLAUDE.md documenta
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `tools/go-build-check:46` faz `"$GO" vet ./...` — e `./...` não expande neste repo (confirmei lendo a linha). O vet aborta em `var/nginx` e o gate nunca type-checa nada. Correção: `./internal/... ./cmd/...` (medido pelo verificador: 481 pacotes, exit 0) + gate `go-vet-closure` novo. Zero `-race` em todo o repo — o `grep -rln -- '-race'` só acha wrappers e um comentário `# Hardlink-or-lose-the-race`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-057) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — tools/go-build-check:46 usava ./... (nao expande); corrigido p/ ./internal/... ./cmd/...; go-build-check agora EXIT 0 com cache frio (commit 5a60637d).

## BUG-058 — Duas ferramentas destrutivas estão ARMADAS — a tag `devcmds` não é guarda, e a pior já rodou de verdade
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `./tools/go-modern list -tags devcmds ./cmd/close-unsafe-public-surface` → `main` (exit 0); sem a tag → "build constraints exclude all Go files". E `tools/go-modern:108-109` injeta `-tags devcmds` em todo `run`; `tools/run-go-cmd-cached:3561` também. Ou seja: `close-unsafe-public-surface` (injeta `noindex` em massa e reescreve sitemaps) e `quarantine-public-mass-surface` estão a um comando de distância. Correção: guarda positiva no `main` das duas (conferir volume publicado antes de agir), não nos wrappers.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-058) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — guarda positiva em internal/superficieguarda: a tag devcmds nao protege (o wrapper a injeta) e dry-run tem default false. Rodado contra o acervo vivo: 'destruiria a superficie publica de 10116 rota(s) ... NAO foi confirmada', exit 2. 6 testes (commit 106bb7c8).

## BUG-059 — A borda está 100% fria e um piscar do túnel derruba o acervo em 530
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** Quatro amostragens consecutivas com cobertura 0,0% e `{'MISS': 40}`. É o efeito composto de BUG-013 + FAMÍLIA-A.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-059) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `983b9c0d`), com verificação de ponta. A causa NÃO era evicção nem inflação de universo: a Cache Rule da borda declara `vary.headers.accept` em modo `normalize` com allowlist `["text/markdown"]`, e **"Accept ausente" é um valor normalizado DISTINTO de "Accept presente sem text/markdown"** — são três variantes por URL, não duas. A varredura de HTML do `warm-edge-cache` chamava `varre(..., accept=None)`, sem mandar `Accept` nenhum, e esquentava a variante que nenhum cliente real pede. Medido em nove rotas sorteadas do índice, três por variante, mesmo UA, mesmo instante: `Accept` ausente → HIT com age ~26.000 s; `Accept: */*` → MISS; `Accept` de navegador → MISS. Prova cruzada na mesma URL e no mesmo segundo: `curl -sS -I` (que manda `*/*`) devolveu MISS em 6 de 6 rotas enquanto um HEAD sem `Accept` devolveu HIT nas mesmas 6. Isso reconcilia os dois números que se contradiziam: o gate de cobertura sondava com curl e via 0%, o aquecedor media a própria variante e via 100% — **ambos certos, sobre variantes diferentes**. Depois da correção, o aquecimento completo pulou apenas **478 de 10.465** URLs por já estarem quentes, isto é, 9.987 estavam frias para o mundo. Verificação de ponta: 30 rotas sorteadas com `Accept` de navegador → **30/30 quentes**, e `check-edge-cache-coverage --amostra 40` saiu de `cobertura 0.0%, ~10.302 exporiam 530` para **`cobertura 100.0%, 40 HIT de 40, ~0 exporiam 530`, exit 0**.

## BUG-060 — `check-edge-live` tem o ramo de resolução INALCANÇÁVEL por construção — a linha 208 grava o evento no `edge_live.jsonl` e só a 211
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** chama `ler_estado_anterior()`, que lê a última linha do mesmo arquivo: o "anterior" é sempre o evento recém-gravado. Resultado histórico: 63 alertas, 0 resoluções. É a causa-raiz do BUG-018 (alerta crítico falso-aberto). Correção: mover a leitura para antes da gravação — ordem que `check-portal-health:225/248` já usa certo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-060) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — leitura movida para antes da gravacao; prova lado a lado: versao antiga emite 0 resolucoes (ramo morto), corrigida emite 1 e fecha a chave certa; 4 testes (commit 2ab3bc64).

## BUG-061 — `check-contrato-vs-medicao` tem folga de 505 páginas, e o CLAUDE.md descreve o gate ao contrário — `folga = max(200, publicadas * 0,05)`. Ele
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** imprime "declara 10107 / mede 10111" e conclui OK. Só reprovaria acima de ~10.612. O CLAUDE.md afirma que o gate "reprova o commit se esta linha divergir". Correção: igualdade exata (o manifesto é lido no mesmo instante — não há ruído estatístico a absorver) ou a folga aparece na frase impressa.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-061) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — gate estendido a GOAL.md/AGENTS.md e a contador chave=valor: de 5 acusacoes para EXIT 0; paragrafos preservados e datados; 5 testes provam que registro datado nao e acusado e rotulo sem data nao escapa (commit fd829fad).

## BUG-062 — `internal-link-mesh-integrity` está VERMELHO em produção
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `exit=1`, 25,3 s, 419 MB de RSS: 28 âncoras da malha mentem o título do destino (a malha foi gerada sobre um estoque com 22 dias de defasagem). Correção: regenerar a malha sobre o estoque corrente e reconferir.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-062) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — malha regenerada sobre o estoque atual (5e4e0c7b); gate de 28 ancoras reprovadas para pass; 6.282 registros, 0 grupo de molde (commit 54a18e05).

## BUG-063 — O acervo perde 304 a cada publicação — causa-raiz isolada em `internal/build/build.go:311`
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `Last-Modified` do acervo é o mtime da escrita: `find public -name index.html -printf '%TY-%Tm-%Td %TH\n' | sort | uniq -c` → 10.339 arquivos numa única janela (28/08 21h), enquanto só 407 rotas tiveram revisão de conteúdo medida. Sem ETag (`etag off`), não há segunda alavanca. Correção: escrita idempotente em `build.go:311`, `:344`, `:425` — ler o alvo, `bytes.Equal`, só gravar se diferir. Não retrodata nada, não muda HTML, não dispara `--ressemear`. Esta é a explicação mecânica mais provável do BUG-031 (queda de revisita de −99%).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-063) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — 6 pontos de escrita do internal/build convertidos para internal/writeifchanged (paginas, hubs, shards, sitemaps, indice, robots). Pacote novo e nao o jsonlwrite porque a API de la parte de arquivo TEMPORARIO (a cadeia editorial usa CreateTemp+Rename) e o gerador tem os bytes em memoria -- criar temp por pagina seria pagar duas escritas para evitar uma; os dois se referenciam. 4 testes, incluindo o caso central (conteudo identico nao avanca mtime, com mtime recuado para tornar observavel sem sleep) e o inverso (diferenca de 1 byte e gravada). LIMITE DECLARADO: sem prova end-to-end nesta sessao, porque cmd/build valida ANTES de gravar (build.go:174 vs escritas em :311) e hoje reprova com os 289 achados; a medicao de 304 por bot fica para depois do primeiro build verde (commit 38243443).

## BUG-064 — 28 shards em carência anunciam `lastmod` PRÉ-ressemear que contradiz o índice vivo em 8.383 URLs — e o GPTBot está consumindo
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** A carência é legítima e não se apaga; o defeito são as datas. Correção: quando `build.go:425` regrava shard aposentado, derivar o `<lastmod>` do plano vivo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-064) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `2346019b`)

## BUG-065 — O canal Markdown ficou 42 minutos fora do ar dentro da janela de deploy — 855 respostas 502, todas ao próprio aquecedor
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** (`wikijuridica-cache-warm/1.0`), em 21:59/22:00/22:07. O Go ficou parado de 21:59:38 a 22:41:26. Correção: serializar em `tools/deploy-publico` — reiniciar o Go antes de aquecer, com espera ativa em `/readyz`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-065) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-065` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-066 — Zero timers e zero hooks de qualidade
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** 23 timers systemd; nenhum invoca gate de qualidade. O único arquivo que menciona `cmd/check` o faz num comentário. Correção: uma unit `wikijuridica-qualidade-diaria` com `nice -19`, `ionice -c3` e `flock`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-066) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `baac5072`)

## BUG-067 — DEZ gates vermelhos agora, cada um por evidência congelada
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Reproduzidos ao vivo: `sca-staticcheck` (exit 1, 416 s, 7 achados, vermelho há 32 dias), `sca-gosec` (32 dias, G404 real e vivo no HNSW), `sca-osv-scan`, `sca-sbom`, `sca-toolchain-freshness`, `http-load-vegeta-evidence`, `muffet-local-crawl`, `html-nu-validation`, `htmltest-release-evidence`, `zizmor-workflow-security` — e a mensagem do zizmor mente sobre a própria causa (`files=2 want=2`). `python-quality-sca` cobre 10 de 228 arquivos Python. `shell-script-quality` termina em 238 s com exit 1 (o `shfmt` nem está no PATH). Correção: uma resolução por gate — e para 3 achados do staticcheck a correção óbvia quebraria `TestValidateDoesNotFanOutToDedicatedHeavyValidators`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-067) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `4dcedf86`)

## BUG-068 — `muffet` e `htmltest` auditaram um espelho de 363 URLs — as 10.340 páginas do acervo NUNCA passaram por link-check
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `target_base_url: http://127.0.0.1:23103`, `crawled_local_url_count: 363`, `content_pages_touched: False`, evidência de 2026-06-28. Correção: apontar para o `public/` servido em `127.0.0.1:8088`, com amostragem estratificada.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-068) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-068` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-069 — Três gates ficam VERDES por ausência de dado *(anti-fraude com
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** porta dos fundos) — `check-served-vs-manifest` aprova com manifesto vazio (ausente reprova, vazio passa: assimetria confirmada em `:203-209`); `check-owner-alerts-abertos` retorna 0 se o ledger não existe — apagar o arquivo silencia todo o canal de alerta; `check-access-log-bots` retorna 0 se o log some, com a hipótese "o site pode não ter recebido tráfego ainda", que deixou de ser possível. Correção: nos três, ausência é anomalia → `exit 2` com mensagem que descreve o defeito.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-069) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — manifesto vazio com paginas servidas -> exit 2; ledger ausente -> exit 2; log ausente -> exit 2; teste automatizado dos dois ramos; caminho normal intacto (commit 65dc7d80).

## BUG-070 — O log de origem é 97,2% ferramenta interna — todo denominador de rastreio está contaminado — `linhas=13362 ferramenta_interna=12987`
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** (=97,2%; 74% são 304). Nenhum consumidor grava o denominador líquido. Correção: todo consumidor imprime o par (bruto, líquido) com o critério de desconto na própria linha.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-070) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `e55d2b0b`)

## BUG-071 — `maxSitePagesBytes = 128 MiB` já está a 56,95% e morde em ~17.772 páginas — `content/pages.json` tem 76.434.768 B / 10.121 registros (7.552 B por
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** registro). O caminho legado está ativo hoje, e o desenho de saída (`publicReleaseContentStoreThresholdPages = 2000`) existe em código e nunca foi materializado.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-071) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `0b1e4fb6`)

## BUG-072 — A origem não autentica 49,3% do tráfego de bot — 15 dos 33 tokens
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** do `robots.txt` têm faixa de IP verificável; 3 das 4 fontes faltantes já usam o schema que o coletor entende (correção barata: 4 entradas em `DefaultBotIPRangeSources`, `internal/crawl/crawl.go:530+`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-072) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `b11627d6`)

## BUG-073 — A cobertura de borda mede um universo 81% inflado, e a docstring afirma o contrário — e o alerta derivado tem amostra de 0,21% (40 de
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** 18.726) com IC95 de 0 a 8,76%. Correção (refinada pelo verificador): manter `--amostra 40` (a razão documentada é correta) e trocar a fonte: derivar `(hit + revalidated) / urls` do `edge_cache_warm.jsonl`, que já é censo completo e custa zero.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-073) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-074 — `check-edge-cache-coverage-honesty` está vermelho com 8 problemas e nenhum timer o executa — o gate que vigia a auto-medição acusa que "a segunda
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** medição caiu sobre o rastro que a primeira acabou de aquecer, a mesma causa-raiz do 100% falso de 2026-08-19".
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-074) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-074` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-075 — 20 `tools/check-` escrevem e 32 têm padrão de mutação (o número
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** 60 do primeiro agente não se reproduziu; a contagem rigorosa é esta) — o pior: `check-brotli-e-recomprimir:44-46` invoca o gerador e reescreve as gêmeas `.br` do acervo servido, de hora em hora, por timer; `check-network-health` chega a dar `sudo systemctl restart`. Correção: separar por papel sem perder o comportamento operacional (o miolo vira `check-` puro; a ação vira `repair-*`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-075) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `976f0b0c`) — mesma família do BUG-023. A união pré-fix de **20 gates que escrevem** reconcilia exatamente com o número deste item, e foi este o critério publicado. Ver o desfecho do BUG-023 para a correção.

## BUG-076 — 4 séries vivas sem consumidor *(não 6 — duas foram refutadas: o
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** filtro do primeiro agente excluía onde os consumidores moram)*: `time_to_first_crawl_daily`, `bing_webmaster_daily`, `clarity_insights_daily`, `edge_bot_status_daily`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-076) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-076` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-077 — 77 arquivos em `data/ops` (11,1 MB) sem uma única referência em código — maior: `v2_corpus_coverage_map_20260721.jsonl` (2,4 MB).
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** Correção: movimentação, nunca descarte — `data/ops/arquivo/AAAA-MM/` com `INDICE.md` dizendo o que cada campanha mediu e qual decisão sustentou.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-077) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-077` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-078 — 13 binários ELF RASTREADOS no git, ~448 MB — confirmei:
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `data/ops/rollback-20260806/wikijuridica-server` (31 MB, versionado, não ignorado), `.agents/runtime/binarios-aposentados/20260826/` (53 MB + 51 MB), 3× `wikijuridica-server.rollback-` (36 MB cada). Correção: o `RESTORE.md` passa a reconstruir a partir de commit fixado, com o SHA do commit no `SHA256SUMS`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-078) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Re-medido em 2026-08-30, e o número era outro:** `git ls-files | xargs file --mime-type | grep x-executable` devolve **21** executáveis ELF rastreados, somando **696 MB** — não 13 e 448 MB. O enunciado envelheceu e o problema cresceu enquanto ninguém olhava.
- **Correção aplicada:** os padrões entraram no `.gitignore` para impedir que ENTREM NOVOS, e os 21 já rastreados saíram do índice por `git rm --cached` — que **não apaga nada do disco**. O binário de rollback continua onde estava, com o mtime original, pronto para uso: é essa a razão de esta ser a rota segura em vez de deletar. Verificado depois: `git ls-files` devolve **zero** ELF rastreado, e o maior deles mostra os 36 MB intactos.
- **Status:** fechado — o peso histórico permanece nos commits antigos, e reescrever histórico é outra decisão, do dono.
- **Lição:** ruído se classifica, não se deleta — e `--cached` é a diferença entre parar de rastrear e destruir a cópia de rollback que existe justamente para o dia ruim.

## BUG-079 — A CSP concede `style-src 'unsafe-inline'` — o hash fecha o
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `script-src`, mas o CSS crítico inline continua aberto. Correção: 12 hashes derivados das constantes Go de `internal/render` (nunca raspando `public/`, que cristalizaria página velha). Não dispara `--ressemear` (é header).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-079) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `1d9b0a94`)

## BUG-080 — `open_file_cache_valid 5s` é diretiva MORTA — `nginx -T` mostra a
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** linha sem nenhum `open_file_cache` declarado; o default é `off`, e 15 linhas de comentário descrevem uma revalidação que não existe.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-080) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `3db1a3e5`)

## BUG-081 — Quatro comentários de código que mentem *(R1: comentário que mente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** é bug)* — `nginx.conf:98` afirma que o ETag sobrevive (desligado 15 dias depois); `internal/crawl/crawl.go:137-143` diz que o canal Content-Signal está FECHADO e que há gate exigindo isso, quando o gate exige o contrário hoje; `internal/v2ingest/v2ingest.go:38-57` descreve um merger materializado em memória que já é streaming desde 2026-07-28 (o comentário nasceu obsoleto no mesmo commit); `internal/content/content.go:441` é impreciso (vale para as rotas do Go, não para o acervo estático).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-081) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-081` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-082 — Decisão × produção divergem sobre o `llms.txt` — o repo documenta
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** "llms.txt NÃO é padrão real / NÃO implementar" em `docs/goal/cowork/SEO_INDEXACAO_2026_DOSSIE.md:41`, e a produção serve 35 arquivos (raiz + 33 de área + `llms-full.txt` de 1,4 MB). Correção: alinhar o documento ao medido — não remover (custa zero e serve auditoria de agente).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-082) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-082` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-083 — Cerimônia de ~2 s por invocação de gate × 322 = minutos de puro overhead — e o modo multi-gate que resolveria isso já existe: `--checks
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** a,b,c` com `--timings`. Correção: usar, não construir.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-083) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `2046adb4`), e o defeito real não era o que o catálogo supunha. Não é a cerimônia de ~2 s por invocação: `tools/run-qualidade-diaria` validava nome de gate chamando `cmd/check <gate> --lista-nomes` — e **a flag não existia**. O parse devolvia exit 2, o `if` caía no fallback, e o fallback rodava `cmd/check <gate>` **INTEIRO** só para ler a mensagem de erro. Os quatro gates de SCA, que custam até 900 s cada, eram **executados duas vezes por dia**, escondidos atrás de um comentário que afirmava que a conferência era barata e não rodava o gate. A flag agora existe de verdade (327 nomes, uma linha cada, exit 0, sem executar nada) e o runner pede a lista UMA vez para os quatro. Nenhum outro runner do repo invoca gate a gate: `check-all` e `lab-cycle` já usam o modo em lote.

## BUG-084 — `internal/agentsurface` não é o inventário que se diz ser — 11
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** rotas de máquina vivem fora dele (`/a2a/v1`, `/api.md`, `/auth.md`, `/changes.json`, `/.well-known/api-catalog`, `/.well-known/mcp/server-card.json`, metadata OAuth…). Correção: corrigir o doc do pacote e trazer o metadata OAuth para o inventário (recorte de segurança real).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-084) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-084` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-085 — `datePublished`/`dateModified` sem hora nem fuso em 590/590
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** valores; `<lastmod>` só com data (o Bing pede ISO 8601 com hora).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-085) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-085` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-086 — `Article` sem `image` (295/295), sem `wordCount`,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** `articleSection`, `isPartOf`; `about` em 11 de 295. `og:image` existe em 10.339.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-086) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-086` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-087 — `max-image-preview:large` ausente nas 10.339 páginas.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** (085/086/087 mudam HTML → uma única publicação com `--ressemear` + purga.)
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-087) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-087` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-088 — 10.436 arquivos `.br` expostos como URL própria, servidos
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** `application/octet-stream`, por causa da allowlist de extensão em `nginx.conf:1249`. Demanda real medida: 2 acessos, ambos da auditoria.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-088) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `d21e26d7`)

## BUG-089 — `/caminho/index.html` e `//caminho/` respondem 200 e duplicam
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** cada URL. Demanda real: só sondas e um scanner.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-089) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `d45e14d7`)

## BUG-090 — Gêmea `.md` sem `Vary` na origem (a borda emite e serve certo) —
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** emitir `Vary: Accept-Encoding` somente, nunca `, Accept`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-090) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO — o codigo faz isto de proposito; executar o enunciado REVERTERIA trabalho

## BUG-091 — Zero gêmeas `.gz` (10.436 `.br`, 0 `.gz`) — risco de escala
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** refutado; falta o instrumento (`ae=$http_accept_encoding` no `log_format`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-091) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `d21e26d7`)

## BUG-092 — Cinco tetos de `1_000_000` iguais à meta declarada de arquitetura, sem folga; `maxPortfolioFiles = 4.096` ficou para trás enquanto
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** o irmão `maxPageFiles` subiu a 200.000.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-092) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-092` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-093 — Índice de busca custa 11,4 KB/página (118 MB hoje) e `/buscar/` é
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** a única rota em dezenas de ms — projeta ~11,4 GB em 1M de páginas.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-093) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `aa019b59`)

## BUG-094 — HSTS sem `preload` — e a submissão não é o passo
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** irreversível: assim que `preload` entra no header, qualquer pessoa pode submeter, e a remoção leva meses.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-094) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO — o codigo faz isto de proposito; executar o enunciado REVERTERIA trabalho

## BUG-095 — Registro de bots sem campo de conformidade com robots nem de
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** método de verificação; 3 agentes documentados ausentes (`meta-externalads`, `Google-CloudVertexBot`, `GoogleOther`); o IETF aipref tem milestone de 31/08/2026 e o repo não menciona `aipref` em lugar nenhum.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-095) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-095` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-096 — `deadcode` custa zero (já em `golang.org/x/tools v0.49.0` no
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** cache) e `errcheck` quase zero — nenhum dos dois está ligado.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-096) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-096` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-097 — `vale-public-prose-lint-release` está vermelho com 140 erros
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** de prosa e alimenta o verdict de release. O trabalho é resolver os 140.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-097) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-097` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-098 — `htmltest` e o venv de qualidade Python só existiam em `/tmp` —
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** sumiram. O precedente certo já está ao lado (`.toolchains/` do LanguageTool e do `vnu.jar`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-098) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-099 — `PROMPT_GOAL_4K.txt` cita dois tetos já elevados 6× e
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** 12,2× — quem seguir o doc investiga o limite errado. (Fica resolvido pela reescrita da §12.)
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-099) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-100 — Nada reprova a introdução de `nosnippet`/`data-nosnippet` no
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** corpo de uma página — única lacuna que sobreviveu à medição do snippet.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-100) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO — o codigo faz isto de proposito; executar o enunciado REVERTERIA trabalho

## BUG-101 — `cmd/build public` REPROVA — o portal não regenera seus artefatos
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `./tools/go-modern run ./cmd/build <dir>` → exit 1, com 261 achados em 29 rotas: 259 `source_url_not_official_nor_registered`, 1 `repeated_sentence`, 1 `repeated_phrase`. `build.go:173-181` falha fechado de propósito — o comportamento do gate está certo; o que falta é corrigir a causa. Leva dois gates junto.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-101) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **PARCIAL** (commit `c2fe3257`): de **289 achados em 31 rotas para 4**. A causa dos 285 era o detector consultar o registro curado só por `SourceID` — e os registros de proveniência do canal de diários não trazem esse campo (medido: as 24.694 fontes de `official_sources` nos shards v2 têm exatamente cinco chaves, e `source_id` não é uma delas), enquanto a fonte `querido-diario-arquivos` estava registrada e `approved`. `Registry.ByURL` reconhece pela base registrada, comparando host por igualdade e caminho por fronteira de segmento, com teste para cada uma das três armadilhas do casamento por prefixo. Os 4 restantes são outra causa, já isolada: `content/pages.json` guarda `http://www.cjf.jus.br/...` enquanto o shard v2 da mesma rota já traz `https://` nas cinco fontes — é regeneração por `publish-v2-direct`, que embarca no trem de publicação.

## BUG-102 — A atestação do grafo do validador está quebrada — e o hash se moveu de novo durante a sessão
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `TestPrepareTransactionPlanSnapshotsModuleIdentityWithProjectReader` falha: `generated validator attestation does not match authenticated source graph`. Consequência: `cmd/ingest-v2-stock` não ingere estoque v2 novo — a fábrica de conteúdo está travada na entrada. Correção: `go generate ./internal/v2ingest` e commitar, depois de commitar as mudanças em Go, senão quebra na hora.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-102) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — go generate ./internal/v2ingest rodado DEPOIS de commitar as mudancas em Go (a ordem importa: antes disso o hash se move no mesmo instante). attestation=sha256:d05513a7 bate com a fonte; TestPrepareTransactionPlanSnapshots ok; cmd/ingest-v2-stock responde -- a entrada da fabrica esta aberta (commit cd182220).

## BUG-103 — Contraste 1,81:1 no rodapé de 10.339 páginas — WCAG 1.4.3 AA reprovada em todo o acervo — `./tools/go-modern run ./cmd/check
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** accessibility-html` → exit 1 em 6m20, `20.650 achados de gravidade ≥ IMPORTANTE em 10.326 documentos`, todos com um único código: `a11y_text_contrast_below_aa [BLOQUEIA-LANÇAMENTO]` — o link "Privacidade e cookies" do rodapé não tem regra de cor. Achado do verificador que o primeiro agente não viu: a correção óbvia cria uma reprovação na folha de impressão, que o auditor não enxerga (`internal/accessibilityaudit/css.go:202` pula `@media print` de propósito). Correção: regra base e regra em `baseCSSPrint` (`render.go:2069`), mais `TestPrintPalettePassesWCAGAA` para fechar o buraco estrutural. ★ MUDA O HTML DE TODAS AS PÁGINAS — publicação agrupada + `--ressemear` + purga ampla. (Uma frente concorrente já corrigiu parte disso na worktree — verificar o disco antes de editar.)
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-103) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — re-triado: a regra base existe em internal/render/render.go:2060 (.site-footer a{color:#D9B96A}) E a da folha de impressao em :2114 (.site-footer a{color:#000}), que era o buraco que o plano previa. Ja estava corrigido e no ar antes desta sessao (commit 9053fe77).

## BUG-104 — `googlebot-smoke` valida o próprio cache — falso positivo provado por experimento controlado — mesmo binário, mesmo minuto: com cache velho,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** exit 1 (`googlebot_smoke_forbidden`); com cache vazio, exit 0. Causa: `checks.go:6788` usa `filepath.Join(os.TempDir(), "portaljuridico-googlebot-smoke-cache")` — caminho fixo em `/tmp`. Correção: `os.MkdirTemp` + `defer os.RemoveAll`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-104) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — cache fixo /tmp trocado por MkdirTemp+RemoveAll em googlebot-smoke E runtime-observability (familia); TestSmokeGatesNaoDeixamCacheFixoEmTmp verde em 69s (commit 5a60637d).

## BUG-105 — `public-release-transaction` reprova com 59.388 erros — e são DOIS campos que o produtor nunca escreveu — `omitted_failures=59188 max_errors=200`.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** Classificação das 200 exibidas: só três códigos, todos da mesma família (`public_release_missing_source_type`, `..._use_in_content`, …). O validador está certo e o produtor está incompleto: `source_type` (lei/súmula/tese/órgão) e `use_in_content` (fundamenta/ilustra/cita) nunca são emitidos.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-105) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commits `cf9a0ffe` e `f466fa3b`). Os dois campos passam a ser DERIVADOS de dado já versionado, nunca constantes: `source_type` de uma tabela de 30 regras (host, caminho, nome) em que a ordem faz parte da especificação, e `use_in_content` de dois fatos medidos por registro. A distribuição é o que prova que não é hardcode disfarçado: **19 classes de `source_type` sobre 24.636 fontes, zero vazias e zero em balde de sobra** (lei_federal 13.761, orientacao_institucional_oficial 2.802, decreto_lei_federal 1.723, constituicao_federal 1.282, …, medida_provisoria 24), e 8 valores de `use_in_content`. As 17 fontes que a primeira medição deixou sem classificação foram lidas uma a uma e viraram linha de tabela. Gate: **59.442 → 10.170 falhas**, com os dois códigos em zero — redução de 49.272, exatamente 24.636 × 2. NÃO muda o HTML servido (verificado: os campos não existem em `content.SourceProvenance` e `internal/render` não os imprime), logo não entra no trem de publicação. Achado caro registrado junto: a redação longa levou a rota `not-stj-20260818` a 8.417 bytes contra o teto de 8.192 de `maxLineBytes` — e `published_manifest_scan_failed` aborta o manifesto INTEIRO, no boot do servidor. O valor foi compactado (maior linha 7.972 bytes) e o gerador passou a abortar em vez de gravar linha grande; o teto NÃO foi elevado.

## BUG-106 — `GOAL.md` — primeiro na cadeia de precedência
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** declara `published_manifest=0` e `deficit_to_10000=10000` como "atualização viva que prevalece sobre qualquer parágrafo histórico" — `grep -c 'published_manifest=0' GOAL.md` = 5. E `check-contrato-vs-medicao` não olha o GOAL.md: as `FRASES_ZERO` e o regex `DECLARACAO` passam batido. Um agente que obedeça à precedência conclui que o portal não publicou nada.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-106) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — gate estendido a GOAL.md/AGENTS.md e a contador chave=valor: de 5 acusacoes para EXIT 0; paragrafos preservados e datados; 5 testes provam que registro datado nao e acusado e rotulo sem data nao escapa (commit fd829fad).

## BUG-107 — `go vet` dá FALSO-VERDE por envenenamento de cache (`VetxOnly`) — provado empiricamente e no fonte do `cmd/go` — controle reproduzido 3×, mesmos
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** arquivos: `vet ./internal/termpromotion/` → exit 0, saída vazia; `vet -tags vetfrioZZZ ./internal/termpromotion/` (tag que nenhum arquivo declara, seleção de arquivos idêntica, só a chave de cache muda) → exit 1 com 2 diagnósticos. Em escala: o comando documentado acha 1 diagnóstico; com cache frio, 3. 67% dos diagnósticos reais são suprimidos pelo comando que qualquer um rodaria. Correção: nunca `go vet` sem cache-buster (`GOCACHE` dedicado ou tag-nonce) + gate `go-vet` com `scaMemoAround` por hash de fonte (padrão que já existe em `internal/checks/sca_memo.go`). Os 3 diagnósticos reais: 2× `non-constant format string in fmt.Errorf` (`internal/termpromotion/termpromotion.go:52,105` — corrompe justamente a mensagem que diz qual linha do dado quebrou) e 1× `unreachable code` (`internal/v2supersessionintegrity/forward_evidence.go:572`). […]
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-107) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — falso-verde reproduzido 3x (exit 0 com cache compartilhado, exit 1 com -tags nonce); cache-buster embutido no go-build-check; 3 diagnosticos reais corrigidos (commit 5a60637d).

## BUG-108 — Nenhum gate de teste no caminho do commit, e o runner de suíte testa ZERO pacotes — `grep -cE '\bgo-modern +test\b|\bgo +test\b' .githooks/pre-commit`
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** → 0; e `tools/check-all:51` usa `go test ./...`, que não expande. Correção: `./internal/... ./cmd/...` no `check-all` + passo de teste focado no pre-commit por caminho tocado.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-108) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — tools/check-all:63 ja usa 'go test ./internal/... ./cmd/...' em vez do padrao que nao expandia; e a causa-raiz comum (BUG-182/DEC-039) foi fechada com a diretiva ignore ./var no go.mod (commit 56d1b34b).

## BUG-109 — Bateria completa: de 450 `tools/check-`, 391 medidos → 218 verdes, 157 VERMELHOS, 4 timeouts, 12 erros de execução (59 não medidos: heavy,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** daemons de janela fixa e os que escrevem — todos nomeados, sem cap silencioso)*. Este é o mapa que faltava.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-109) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `afdda2b4`)

## BUG-110 — `check-architecture` inutilizado pelo cache do Chrome do publicador social — exit 1 com 586 reprovações, 200 exibidas e `omitted_failures=386`;
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** 200 de 200 são `publicador-social`. Excluir só `.perfil-navegador` e `Cache_Data` não resolve — sobram 10 hits de `node_modules` e 2 de prosa.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-110) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `8eb34afd`)

## BUG-111 — O ledger de custo mente sobre os dois gates mais caros
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `http-smoke` custa 75 s e `accessibility-html` 129 s (medidos), e ambos estão rotulados `fast / budget 3000 ms / always_run=true` em `check_performance_ledger.jsonl`. (Isto explica meu `EXIT=124` no `check-http-smoke` com timeout de 90 s — não era travamento.)
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-111) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `2046adb4`). O ledger mentia sobre `accessibility-html` e `http-smoke`, mas a correção não foi reetiquetar: `RenderInternalTargets` renderizava 10.331 documentos EM SÉRIE e `AuditRepository` auditava em série, com CPU_USER 164 s contra WALL 158 s — **1,03 núcleo de 8**. Os dois viraram pool com resultado por índice, devolvendo o erro de MENOR índice, que é o que o laço sequencial devolvia. Medido por mim no disco depois: **137.449 → 35.235 ms (3,9x)**, e a suíte do pacote caiu de 106,4 s para 38,3 s junto. Sete gates rotulados `fast/3000` foram remedidos e reclassificados (`oab-policy` 107.830 ms — 36x o declarado; `sitemaps` 99.440; `superseded-absent-from-sitemap` 59.066; `runtime-observability` 13.887; `internal-link-block-integrity` 5.549), cinco gates que estavam em `checks.Names` **sem nenhuma linha de orçamento** ganharam uma (entre eles `v2-acervo-similaridade`, 78.599 ms), e nove gates `fast` foram medidos e CONTINUAM `fast`, porque a medição os absolveu. O ledger foi de 322 para 327 linhas. Os orçamentos ficaram acima do medido de propósito, e isso está declarado: a carga da máquina oscilou entre 8 e 22 durante o lote e o `RunContext` compartilha corpus entre checks do mesmo processo — os números do lote são TETO, não piso.

## BUG-112 — `scaled_content_release_verdict.jsonl` foi renomeado em 2026-07-09 e nunca regerado — derruba 11 gates de uma vez — no disco só existem
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `.jsonl.stale-20260709T155727Z` (4,7 MB) e `.jsonl.stale-v1-132157Z` (156 MB). Não é decisão a devolver ao dono: o produtor existe (`tools/generate-scaled-content-release-verdict`).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-112) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-112` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-113 — `p0-cycle-close-indexable-10k` anuncia déficit fictício de 10.000 páginas — porque o insumo ausente (BUG-112) faz `count=0` cair no default.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `current_public_indexable_count=0 required=10000 deficit_to_10000=10000` — enquanto o `http-smoke` do mesmo dia mede `manifest_routes=10116 public_indexable_legal_pages=10116 deficit_to_10000=0`. Correção: separar "não consegui medir" de "medi e deu baixo".
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-113) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `c1635b99`)

## BUG-114 — Os 259 achados que travam `cmd/build`: TRÊS causas, não uma
- **Data:** 2026-08-29 (diagnóstico reescrito no mesmo dia, após crítica adversarial)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `cmd/build` reprova com 261 achados em 29 rotas. A leitura inicial — "o gerador de /diarios/ cunha um `source_id` por gazeta e ignora o ID curado" — estava certa no fato e **errada na conclusão**. Um crítico adversarial reproduziu o detector e mediu: **255 ocorrências em `/diarios/` + 4 em `/noticias/cjf-20260820/`** (worktree hoje: 285 + 4, porque a coleta de 26-28/08 acrescentou 30). As 4 do CJF são outra causa: `http://` onde `isOfficialSourceURL` exige `https` — **corrigidas** no commit 564d2354.
- **O que a crítica DERRUBOU da minha proposta:** (a) trocar o `source_id` pelo curado **não** destrava o build — `internal/quality/quality.go` tem uma segunda regra no mesmo laço, `if registrada && source.IngestionEnabled && source.AuditStatus != "approved"` → `source_ingestion_enabled_without_audit`; a entrada `querido-diario-arquivos` tem `ingestion_enabled: true` e `audit_status` ≠ `"approved"`, então as mesmas 285 voltariam sob outro código. (b) O ponto de implementação **não é o gerador**: o schema do shard fecha `official_sources` em 5 chaves (`internal/v2ingest/adjudicate_shard.go:80,711`) e o id é cunhado a jusante, em `internal/v2publish/v2publish.go:303` (`SourceID: publicpath.Slug(source.Name)`). (c) A premissa "trava qualquer publicação" é **falsa**: `publish-v2-direct` só barra por códigos críticos, e este é MÉDIO — foi assim que as páginas de `/diarios/` foram ao ar. Só `cmd/build` trava.
- **O que a crítica NÃO conseguiu derrubar (e por isso está verificado):** o comentário de `cmd/generate-diario-pages/main.go:1072-1086` — que afirma que silenciar o gate "exigiria liberar `.org.br` inteiro" — **está errado**, e a história prova: o commit `d08958cb` (2026-08-20 13:45) criou a entrada `querido-diario-arquivos` **expressamente para estas ocorrências**, com robots medido e base legal (Lei 9.610/98 art. 8º); o comentário foi escrito **40 minutos depois** (`30fa630b`, 14:25) contradizendo o commit anterior do mesmo dia. O detector casa por `source_id`, e as páginas carregam slug cunhado: é **lacuna de binding, não decisão**. E não há re-datação: o slug não existe no HTML servido (`grep -rl "di-rio-de" public/diarios/` → 0), e `generate-page-content-revision` hasheia o HTML, não o `pages.json`.
- **Correção (nesta ordem, nenhuma delas é silenciar gate):** (1) resolver honestamente a regra 2 — `./cmd/check content-quality` **já reprova hoje** por `missing_terms_audit` e `missing_terms_checked_at` em querido-diario, stj-feed, stj-portal e trf6-feed; a auditoria de termos que falta é trabalho real, e carimbar `"approved"` sem fazê-la é a fraude que o contrato proíbe; (2) só então o binding, por `base_url` no `Registry` (que hoje só tem `ByID`) ou por schema + `v2publish`; (3) nomear os 2 achados restantes dos 261, que ainda não foram classificados.
- **Status:** FECHADO — causa-raiz no LEITOR, nao no gerador: internal/v2publish/v2publish.go:303 montava SourceID com publicpath.Slug(source.Name), e a struct Source do pacote NAO TINHA o campo source_id -- o JSONL trazia e o leitor ignorava. Medido no content/pages.json: source_id valendo 'anadia-al-di-rio-de-19-08-2026-no-acervo-do-querido-di-rio', um ID por gazeta e por dia; registry.ByID nao acha nada com isso e o quality acusa 289 source_url_not_official_nor_registered. E o MESMO padrao que o comentario da propria struct ja descrevia para VerifiedAt/HTTPStatus ('sempre estiveram no JSONL -- o leitor e que os ignorava'). Corrigido com identificadorDaFonte, que da precedencia ao ID curado e mantem o slug como ultimo recurso (commit cbcbf6f1).

## BUG-115 — Autolinker publica href e JSON-LD apontando para OUTRO dispositivo — 219 ocorrências em 199 páginas, 219 de 219 erradas — toda citação de artigo
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** com sufixo (`art. 543-C`, `art. 475-J`, `art. 1.240-A`) é partida pelo autolinker: o `<a>` fecha antes do sufixo e o `href` aponta para o artigo-base. Consequência medida: 10 páginas de jurisprudência emitem, na camada de máquina, uma URN do CPC/2015 para dispositivo do CPC/1973 (arts. 543-C e 475-J, revogados). Armadilha registrada: `grep -rl '543-C' public/` devolve 0 — o literal não existe no HTML porque o autolinker o parte.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-115) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — 219 ocorrencias em 199 paginas; regex casava so art. N — corrigidas as 3 (cluster, fallback e captura de ancora) com constante unica; milhar tambem estava quebrado (art. 1.240-A casava art. 1); 16 casos de teste + regressao em 7 pacotes (commit 88fb7bc9).

## BUG-116 — `/glossario/qualidade-de-segurado/` cita a Lei 8.213 "art. 24-A", que não existe — é o art. 27-A — erro jurídico servido ao público.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Correção: gerador datado com lease + CAS, nunca editando o shard à mão.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-116) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — art. 24-A nao existe na Lei 8.213 (corpus: ha 24 e 27-A, nao ha 24-A); 3 ocorrencias em 2 paginas corrigidas por gerador datado com CAS; pairing e preservacao verdes (commit 5b561d51).

## BUG-117 — `ValidateEditorialBody` — a guarda de ética OAB sobre o corpo publicado — é CÓDIGO MORTO
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** existe, está testada, e não tem um único chamador de produção. O gate de promessa valida os 7.959 registros da esteira de candidatos, não as 10.111 páginas publicadas.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-117) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — ValidateEditorialBody ligada ao corpo das 10.116 rotas publicadas via checkLegalMarketingPolicy; zero acusacoes (as 30 ocorrencias do acervo sao negacoes legitimas) e teste com duas paginas prova que nao e no-op (commit c6b78855).

## BUG-118 — Três diplomas do corpus legal contaminados com artigo de OUTRA lei
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `cpc.json` (n=1075, fim denso 1072, suspeito 2027), `lei_12653_2012.json` (n=5, suspeito 135), `lei_8245_1991.json` (n=93, suspeitos 167 e 169) — cabeçalhos de artigo colhidos dentro de bloco de alteração de outra norma. E `confiavel_para_acusar_divergencia` mede atualidade, não completude: 8 diplomas com o flag `True` têm lacuna de numeração.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-118) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — causa-raiz no extrator, não no dado: `e_cabecalho` só descartava referência cruzada, e cabeçalho de artigo TRANSCRITO dentro de bloco de alteração virava chave própria. `tools/generate-legal-corpus` passou a delimitar o bloco (`blocos_de_transcricao`, aplicado em `indexar_artigos`) em vez de medir distância — a tentativa por janela de 60/400 caracteres apagava os arts. 83, 84 e 87 da Lei 8.245/1991, que são próprios. Removidos os alheios: 216-A (Lei 6.015) do CPC — que o `articles_fora_do_diploma` nunca viu, por não haver salto —, 167 e 169 (Lei 6.015) da Lei 8.245, 135-A (CP) da Lei 12.653, 61/129 (CP), 152 (LEP) e 313 (CPP) da Lei 11.340, 94 (Lei 8.213) da LC 123 e 13-A/14-A/17-A/18-A (Lei 5.768) e 35-A (Lei 13.756) da Lei 14.790. Os três diplomas que o `cmd/repair-legal-corpus` havia rebaixado voltaram a `confiavel_para_acusar_divergencia=true` (16/29 → 19/29) sem relaxar nada: `check-legal-corpus-extractor` APROVADO e provado FALSIFICÁVEL (contra o extrator de HEAD ele acusa 4 FALHA e sai 1); `cmd/check legal-corpus-integrity` e `legal-citation-attribution` pass; re-executar o extrator sobre o texto oficial do Planalto reproduz o disco nos 29 diplomas, zero artigo a mais ou a menos. Risco OAB medido: nenhuma das 11.638 citações com diploma nomeado das 10.116 páginas publicadas aponta artigo removido. Residual registrado (outra família, não o BUG-118): a LC 123/2006 chega do Planalto com espaçamento quebrado (`Art. 18- C .`) e o corpus não indexa os arts. 18-C e 49-B dela — o inverso do BUG-118, corpus que NEGA artigo existente. Commit desta frente pelo maestro.

## BUG-119 — 124 refinamentos pagos órfãos derrubam o carregador canônico do estoque autoral — 124 de 2.520 (4,9%), com integridade referencial quebrada e
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** commitada nos ledgers.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-119) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-119` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-120 — Migração da variante de URL do Planalto feita pela metade — o dado
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** migrou, 51 constantes de produção em 8 arquivos não, derrubando 27 testes.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-120) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `269a6a9a`)

## BUG-121 — O digest congelado do shard `aereo-08` divergiu há 25 dias — a
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** guarda de imutabilidade está morta desde 2026-08-04, com o commit culpado identificado.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-121) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — go-modern test -run Aereo08 ./internal/v2ingest/ ok exit 0; python3 -m unittest tools.test_audit_v2_pages_aereo08 20 testes OK; divergencia auditada campo a campo: faq 0->2 e word_count 436->527 em aer-internacional-montreal-ou-cdc, official_sources e ordem intactos (commit e943a83f).

## BUG-122 — `legal-citation-attribution` acusa 184 páginas (97 `diploma_sem_fonte`,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** 66 `sumula_sem_fonte`, 35 `tema_sem_fonte`) — reenquadrado pelo verificador: é defeito real, o vermelho é proposital, e a correção é acrescentar a fonte que falta, nunca remover a citação. O autoteste do gate passa 13/13 em regressão de falso positivo.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-122) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-122` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-123 — 12 `tools/check-*` escrevem no repo — além dos 10 já conhecidos
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `grep -ln 'notify-owner' tools/check-*` → 11 arquivos; e `check-brotli-e-recomprimir` roda gerador e reescreve as gêmeas `.br` do acervo servido, de hora em hora, por timer. O nome já confessa.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-123) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** **FECHADO** (commit `976f0b0c`) — mesma família do BUG-023/075, contada com um terceiro critério. O caso concreto deste item (`check-brotli-e-recomprimir` rodando o gerador e reescrevendo as gêmeas `.br` do acervo servido, de hora em hora, por timer) foi o primeiro a ser separado, com a unit systemd repontada no mesmo commit. Ver o desfecho do BUG-023.

## BUG-124 — 24 gates vermelhos por evidência derivada estagnada — e pelo menos um esconde defeito REAL de conteúdo — Correção: não rodar os 24
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** geradores em lote; um a um, re-executando o gate: quem ficar verde era bookkeeping, quem ficar vermelho é defeito.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-124) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-124` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-125 — O BUGLOG tem status falso em 4 de 12 entradas — todas na direção
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** "segura", todas produzindo trabalho fantasma. `BUG-011` (DataJud) é a única cujo "aberto" resistiu à verificação — e o bloqueio não é credencial: a série existe em `data/research/`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-125) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `2fb2a61a`)

## BUG-126 — A busca imprime a consulta do visitante com `%q` do Go: `\"`,
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `\t` e `\\` vazam no resumo visível e na meta description (8 chamadas).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-126) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — oito call sites migrados de %q para aspa curva com neutralizacao; 6 testes incluindo balanceamento do marcador de citacao; regressao do render ok 11,2s (commit a7d5b43f).

## BUG-127 — A página 404 é a única superfície servida sem o script de medição — e a CSP dela já autoriza o hash. Tráfego que bate em URL
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** inexistente é invisível no GA4 e no Clarity.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-127) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-127` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-128 — `AuditRepository` custa 978 MB de RSS no gate PADRÃO e o
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** teste da vitrine paga dois `AuditRepository` a 38,3 s cada — memoizar no `RunContext` com o `cachedTypedLoad` que já existe.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-128) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — AuditRepositoryCached memoiza por (root,limite,impressao do insumo); 3 chamadas com entrada em cache disparam ZERO audits (prova por contagem); escopo de processo, erro nao cacheado (commit e7eecc8c).

## BUG-129 — A única sonda de corrida sobre `RunAll` está desligada por
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `WIKI_CHECKS_FULL_RACE`, variável que ninguém define (4 ocorrências, todas no próprio arquivo de teste).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-129) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-129` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-130 — `search.Manager` não tem `Close` — `New()` não expõe encerramento
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** e o teste vaza. (A atribuição ao access log foi refutada: em teste o logger é `nil` por guarda deliberada.)
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-130) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-131 — 8 testes stale em 4 pacotes, por mudança deliberada não refletida
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** na asserção; 4 perfis de seleção de gate derivaram do ledger validado — inclusive o `p0-release`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-131) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-131` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-132 — `AGENTS.md`, primeiro na cadeia de precedência, é integralmente
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** endereçado ao Codex, desativado por ordem do dono em 2026-07-21 — e condiciona o fim do P0 a um déficit que o próprio gate do repo mede em 0. `CHECKPOINT.md` (terceiro na cadeia) congelou há 37 dias com nota de precedência ainda ativa.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-132) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-132` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-133 — O inventário de citações — instrumento do P1 — está 16 dias atrás do acervo e não tem contrato de frescor.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** Descrição integral no título; evidência e comando em docs/goal/PLANO_CACA_BUGS_20260829.md.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-133) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-133` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-134 — A lista de termos de promessa OAB é fechada em 11 needles com
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** busca contígua, e o acervo já escreve formas fora dela ("aprovação garantida" em 10 páginas — todas legítimas, mas a lacuna de detecção é real).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-134) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `47db4fb1`)

## BUG-135 — `tools/check-go-compile-closure:134` usa `./...` como default —
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** o segundo detector cego pela mesma armadilha; e dois gates Python morrem em `UnicodeDecodeError` (em lugares diferentes dos que o primeiro agente disse).
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-135) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — check-go-compile-closure de exit 1 (pattern var/nginx permission denied) para PASS (commit 65dc7d80).

## BUG-136 — `//nolint:govet` é no-op para o `go vet` — não silencia nada.
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** Descrição integral no título; evidência e comando em docs/goal/PLANO_CACA_BUGS_20260829.md.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-136) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — //nolint:govet confirmado no-op; decoder extraido p/ decodeLegacyForwardApprovalManifest com 4 casos de teste; vet do pacote EXIT 0 (commit 5a60637d).

## BUG-137 — O `repeated_phrase` que trava o build é falso positivo: a
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** normalização colapsa `n 2 204 santa` / `n 2 205 santa` em 6-gramas idênticos (três edições distintas de diário). E o `repeated_sentence` que o primeiro agente chamou de "real" também é texto oficial citado.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-137) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — NormalizeText passa a preservar separador de milhar; 3 edicoes do diario da BA deixam de colidir; 6 casos de borda + regressao do pacote (65,6s) verdes (commit 17f96f1e).

## BUG-138 — Quatro formas da mesma URL servem 200 sem redirecionar
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** (`/rota/`, `//rota/`, `/rota/index.html`, `/rota`), e a premissa que sustenta não corrigir não tem sentinela.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-138) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `d45e14d7`)

## BUG-139 — O comando de build documentado no CLAUDE.md cobre 481 de 760
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** pacotes; nenhum gate linka os 279 dev-mains. O comentário do pre-commit fala em "504 pacotes" e subestima o custo real em ~4×.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-139) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-139` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-140 — `run-check` re-deriva o grafo de dependências do Go a cada
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** invocação: 3.161 ms contra 703 ms do binário direto — 2.458 ms de overhead por gate × 322.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-140) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-140` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-141 — `docs/audits/` tem cinco arquivos de 2026-06-28 declarando
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** `published_manifest=0`, 62 dias depois; o `PLANO_RASTREIO` lista cinco defeitos como "ainda não corrigidos" que foram corrigidos no mesmo dia; e o placar "check all: 42 pass, 83 fail" cobre 39% do registro sem dizer isso.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-141) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-141` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-142 — Comentário que mente em `css_contrast_test.go:170-172` — afirma
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** que o auditor não alcança media query, e ele alcança desde `darkThemeFindings`.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-142) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-142` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-143 — §4e-bis de `DADOS_CONFIAVEIS` está desatualizada: existe canal
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** local de enunciado de súmula, cobrindo 23 das 48 do STF citadas — mas prova texto, não vigência.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-143) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** aberto — task `caca-BUG-143` no frontboard. PASSO ZERO: reproduzir a medição antes de corrigir.

## BUG-144 — Um único teste consome 5 minutos fazendo dois renders
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** completos do site — lentidão é bug P0 por contrato.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-144) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — o teste da vitrine deixou de pagar dois AuditRepository (~38s cada); a duplicacao era a causa do custo, nao o volume (commit e7eecc8c).

## BUG-145 — Os 5 "daemons que nunca retornam" são sondas de janela fixa
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** LEVE
- **Sintoma e causa raiz, medidos:** (refutado) — o que falta é `expected_duration_ms` real no ledger.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-145) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-146 — Não existe backup de nenhum dado sole-copy
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `systemctl list-timers | grep -i backup` → só `dpkg-db-backup`, do sistema. `data/` tem 12 GB e nenhuma rota de backup. O `BUG-053` já prova o caso concreto: um manifesto versionado aponta por sha para um recibo que não existe em lugar nenhum. Perda de dado aqui é irreversível e nenhum item do catálogo a cobria.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-146) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** FECHADO — espelho git incremental em /dev/sda1 (disco fisico distinto do NVMe do repo) + segredos 0600; verificacao por fsck e HEAD; timer 02:20 UTC; 2691 commits, 6642 MB, incremental em 12s (commit 316cf42e).

## BUG-147 — Espaço em disco sem gate
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `df -h /opt` → 78% usado, com ~585 MB de ruído e 448 MB de binários rastreados crescendo. `ls tools/ | grep -iE 'disk|disco'` → nada. Disco cheio mata a transação de publicação no meio — e a publicação é transacional justamente para não deixar o portal em estado híbrido.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-147) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** corrigido e commitado (commit `a2d63d0e`)

## BUG-148 — DNS/DNSSEC sem sonda de saúde
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Existe `check-dns-aid` (descoberta de IA), não saúde de resolução. O precedente do DS órfão do Registro.br é dependência externa que já quase derrubou o domínio, e nada a vigia.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-148) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-149 — Os alertas dispararam e ambos os canais registram "silenciado"
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** Na janela dos 502 de 28/08 (BUG-065), `portal-fora` e `portal-degradado` dispararam — e ficaram silenciados. A lógica de silenciamento de `tools/notify-owner` precisa ser lida: alerta que não chega é pior que alerta que não existe, porque cria a sensação de cobertura.
- **Correção:** em `docs/goal/PLANO_CACA_BUGS_20260829.md` (BUG-149) — com o comando da medição, a correção executável e, onde a correção óbvia faria dano, a alternativa segura.
- **Status:** REFUTADO — o codigo faz isto de proposito; executar o enunciado REVERTERIA trabalho

## BUG-150 — `/jurisprudencia/stf-adi-5502/` está abaixo do piso de links internos
- **Data:** 2026-08-29 (achado ao consertar o BUG-039 — o gate cego voltou a enxergar)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `./tools/check-internal-link-floor` → exit 1: "1 página(s) indexável(is) abaixo do piso de entrada: /jurisprudencia/stf-adi-5502/ tem 2, piso 3". O defeito não é novo — estava escondido atrás do `UnicodeDecodeError` que derrubava o gate antes de ele medir qualquer coisa (FAMÍLIA-A). Página com malha de entrada abaixo do piso recebe menos autoridade interna e é candidata a não ser rastreada com a mesma frequência.
- **Correção:** republicar com o piso de entradas (`cmd/publish-v2-direct` aplica `v2publish.EnforceInboundFloor`); se persistir, é órfã de afinidade — enriquecer `internal_link_topics` por gerador datado. **Proibido relaxar o critério de afinidade**, que é o que o piso existe para cobrar.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-151 — Teste stale cobrava do wrapper um `artifact_claim` que ele corretamente recusava emitir
- **Data:** 2026-08-29 (achado ao remedir o custo dos gates; ordem do dono: pré-existente também se corrige)
- **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `TestRunGoCmdCachedArtifactClaimFingerprintsAreSHA256BeforeGenerateBuild` reprovava com "preflight did not emit artifact_claim before build/run failure". Investigado até o fim: **quem estava certo era o wrapper.** `validate_cached_generate_command_contract` (`tools/run-go-cmd-cached:266`, chamado em `:328`) exige supervisão real do `run-heavy-throttled`, e `heavy_supervisor_ancestry_is_verified` (`:131`) **não se contenta com a variável de ambiente**: verifica a ancestralidade do processo. É anti-fraude legítimo — declarar supervisão não é estar supervisionado. O teste declarava `WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY=1` e invocava o `run-go-cmd-cached` direto; o preflight reprovava na linha 328, antes de o claim ser emitido na 1271, e a asserção cobrava um claim que nunca chegou a existir. Classe do BUG-131 (teste stale por mudança deliberada não refletida na asserção).
- **Correção:** invocar sob `run-heavy-throttled`, que é quem estabelece a ancestralidade. As variáveis `WIKI_RUN_GO_CMD_CACHED_UNDER_*` saíram do teste — quem as define é o supervisor, e declará-las à mão era exatamente a simulação que o wrapper passou a recusar. O orçamento é **apertado**, não folgado: `WIKI_HEAVY_TIMEOUT_SECONDS=5` faz o wrapper abortar pelo próprio limite em ~1,5 s **depois** de emitir o claim, que é o objeto do teste. Subir o timeout do contexto seria o erro que o contrato veda.
- **Status:** FECHADO — teste de 1,486 s, verde; pacote `internal/checkperformance` verde.

---

# Lote CANAL DIÁRIO VIVO — 2026-08-29

Onda de 6 agentes (3 frentes + 3 críticos adversariais) sobre a ordem do dono:
*"tudo que tem nos tribunais são públicos... isso não é trava, ache solução... para
criar um portal de notícia na wiki e de conteúdo diário VIVO e não morto"*.

**A conclusão que reorienta a frente:** o canal não está magro por decisão
jurídica. Está magro por um **struct de parser que não declara `content:encoded`**
— e por um comentário em produção que afirma, errado, que não há corpo nos feeds.

## BUG-152 — `content-quality` está cego para 10.344 páginas por um early-return
- **Data:** 2026-08-29 · **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `internal/checks/checks.go:7110-7113` faz `sourceReport := registry.ValidateForP0(); if !sourceReport.Passed() { return sourceReport.Messages() }` **antes** de `quality.ValidatePagesWithSources(repo.Pages, registry)`. Como o registro está vermelho, a validação de PÁGINA nunca roda. Medido: `cmd/check content-quality` → exit 1 com exatamente **13 linhas**, 12 de higiene de registro e 1 de `exit status 1`. **Zero achado de página, sobre 10.344 `index.html` no ar.** É o R2 do contrato: gate vermelho pelo motivo errado escondendo todos os outros. O mesmo padrão em `internal/build/build.go:177` e `cmd/publish-v2-direct/qualitygate.go:74` **não** mascara, porque chamam `ValidatePagesWithSources` direto — o gate nomeado que o operador roda à mão é que engole.
- **Correção:** concatenar em vez de retornar cedo. **O crítico corrigiu o oráculo proposto:** "passar de 13 para >13 linhas" não serve, e a previsão de volume estava errada nos dois sentidos. Medido de verdade: `content/pages.json` tem 10.126 páginas e 24.708 registros de proveniência, e **nenhum `source_id` casa com id do registro** (são slugs por item), então `source_ingestion_enabled_without_audit` nunca dispara — o que roda é `source_url_not_official_nor_registered`, com **295 registros em 39 páginas** fora da allowlist (285 em `data.queridodiario.ok.org.br`, 4 em `www.oab.org.br`). Destravar sem decidir esses dois hosts abre o gate vermelho e trava a onda.
- **Status:** FECHADO — gate saiu de 13 linhas (12 de registro, 0 de pagina) para 202 com 188 achados de pagina em 20 rotas e 101 omitidos = 289 no total; teste separa as duas familias de mensagem (commit a5b84508).

## BUG-153 — Comentário em produção afirma que os feeds não têm corpo; têm
- **Data:** 2026-08-29 · **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** `cmd/collect-noticias-oficiais/main.go:133-142` declara no struct do parser apenas `title`, `link`, `pubDate` e `category`. `description` e `content:encoded` **nunca são lidos**. Os comentários de `main.go:40-44` e `cmd/generate-noticia-pages/main.go:5-9` justificam: *"Medido em 2026-08-20 nos quatro feeds: o description do STJ é IDÊNTICO ao title, então não existe corpo a copiar"*.
- **O que a medição de hoje mostra, por feed** (texto **limpo**, tags removidas — a primeira contagem da onda media HTML bruto e o crítico corrigiu): **STJ** `content:encoded` em **120/120**, mediana 2.702 caracteres, máx 20.153 (3.020 palavras); **TRF6** 10/10, mediana limpa 3.160; **TST** `content:encoded` em **0/10** — o corpo está em `<description>`, bruto médio 8.140; **CJF** 0/30 e `description` com média de **118 caracteres**, que é chamada, não corpo.
- **A nuance que importa (e que o crítico salvou):** o comentário **não é simplesmente falso**. Hoje o `description` do STJ é idêntico ao `title` em **91 de 120** itens (75,8%) — a *medição* de 2026-08-20 estava **certa**. Errada foi a **inferência**: concluiu-se "o feed não tem corpo" sem nunca olhar `content:encoded`.
- **Correção:** o parser passa a ler **por feed** — `content:encoded` (STJ, TRF6) **e** `description` (TST) —, e o registro anota que o CJF não fornece corpo, senão o gerador trata 118 caracteres de chamada como "corpo coletado". O campo do namespace exige a forma `xml:"http://purl.org/rss/1.0/modules/content/ encoded"`, senão o Go não casa a tag.
- **Status:** FECHADO — parser passou a ler content:encoded (http E https, que o STJ usa) e description por feed; STJ de 29 para 119/119 com corpo; extracao de 3/1/0 para 25/7/42 Temas/Sumulas/processos; 3 testes com fixture commitada (commit 78e1ee67).

## BUG-154 — O diferencial declarado do canal não acontece: ligação ao acervo = 0 em 31 de 31
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** o gerador documenta (`main.go:32-35`) que *"O VALOR AUTORAL vem da ligação com o acervo"*. O ensaio de hoje imprime `com ligação ao acervo: 0` em 31 páginas montadas. Causa exata: a coleta chama `extrai(temaCitado|sumulaCitada|processoCitado, TÍTULO)` em `main.go:267-269` — **o corpo não existia para varrer**. Sobre 1.688 registros o extrator achou 22 Temas, 0 Súmulas, 0 processos, e mesmo os 22 não viraram link, contra 409 rotas de acervo carregadas.
- **Por que é a alavanca de maior retorno:** número de processo, Tema e Súmula estão **no corpo**, não no título — e são exatamente a chave para buscar o ato oficial **citável** (ementa/tese, domínio público pelo art. 8º IV) que dá corpo lícito à página.
- **Status:** FECHADO — parser passou a ler content:encoded (http E https, que o STJ usa) e description por feed; STJ de 29 para 119/119 com corpo; extracao de 3/1/0 para 25/7/42 Temas/Sumulas/processos; 3 testes com fixture commitada (commit 78e1ee67).

## BUG-155 — Similaridade O(n²) no shard: 18 mil páginas/ano dariam 162 milhões de comparações por execução diária
- **Data:** 2026-08-29 · **Severidade:** GRAVE (bug de escala, ainda latente)
- **Sintoma e causa raiz, medidos:** `cmd/generate-noticia-pages/main.go:324,358` compara cada página montada contra todas as aceitas do run, e o gerador **regenera o shard inteiro** a cada execução (`:298-314` reinsere publicadas, `:418` grava tudo). Hoje n=32 → ~500 comparações, 0,95 s. Com 10 fontes novas × 50 matérias/dia (~18k/ano) num shard único: **~162 milhões de comparações de conjuntos de shingles por execução diária**. Lentidão em escala é P0 neste repo e é **proibido** resolver aumentando timeout.
- **Correção:** shard **mensal** (`noticias-oficiais-AAAAMM.jsonl`), que limita n a ~800 e mantém a comparação dentro da janela em que molde repetido de fato acontece. **Fazer antes de aumentar o volume** — depois de 2.000 páginas num shard único o custo de corrigir cresce.
- **Status:** aberto — task `caca-BUG-155`.

## BUG-156 — A DEC-032 atribui o texto de lei ao art. 8º, I, e o inciso I não sustenta isso
- **Data:** 2026-08-29 · **Severidade:** GRAVE (erro jurídico no documento que governa a política de citação)
- **Sintoma e causa raiz:** a DEC-032 fundamenta a citação de texto de lei em "art. 8º, I e IV" da Lei 9.610/98. O inciso que exclui lei, decreto, regulamento, decisão judicial e demais atos oficiais da proteção é o **IV**. O inciso I trata de outra coisa. Citação legal mal atribuída é a classe que o contrato deste projeto chama de **P1 permanente**, e ela está no documento que autoriza as citações de todas as páginas derivadas.
- **Correção:** corrigir a DEC-032 para art. 8º, IV, e acrescentar o **art. 46, I, "a"** — o dispositivo que de fato decide o caso da notícia institucional e que nem o material nem a DEC-032 enfrentavam.
- **Status:** aberto — task `caca-BUG-156`.

## BUG-157 — O coletor não usa o coletor robusto que o próprio repo já tem
- **Data:** 2026-08-29 · **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `internal/sourcecollect` existe e implementa GET condicional, robots (com cache e TTL de 24 h), teto diário, limitador por host, classificação de erro e cap de bytes. `cmd/collect-noticias-oficiais` não o usava: `grep -c "sourcecollect\." → 0`, um `&http.Client{}` cru em `main.go:284`, sem `If-Modified-Since`/ETag e sem consultar robots.txt uma única vez.
- **CORREÇÃO DO PRÓPRIO ENUNCIADO (2026-08-29):** a linha acima dizia "implementa GET condicional, robots **e retry**" e "601 KB do STJ". Duas imprecisões medidas: (a) **não há retry, backoff nem circuit breaker** no pacote — `grep -niE "retry|backoff|circuit" sourcecollect.go` devolve 3 linhas, todas a LEITURA do header `Retry-After` para compor a mensagem de erro do 429; quem migrasse contando com retry receberia falha na primeira instabilidade de tribunal, e a resiliência real é o laço de fontes do chamador; (b) o feed do STJ mediu **534.000 bytes** em 2026-08-29 — o tamanho varia por dia, e a substância (rebaixar o feed inteiro todo dia) se confirma.
- **Banda medida, 2026-08-29, os quatro feeds numa execução:** stj 534.000 B (ETag) · tst 90.630 B (sem validador) · cjf 16.394 B (sem validador) · trf6 83.038 B (ETag + Last-Modified) = **724.062 B/dia**.
- **A primeira estimativa de economia (85,2%) estava OTIMISTA, e a execução dupla real a corrigiu.** Reconsultar no mesmo minuto deu 304 em STJ e TRF6, donde "617.038 B, 85,2%". Medindo direito: **TRF6 recupera** (ETag forte + Last-Modified, 304 com 0 byte na 2ª execução, 83.038 B); **o STJ recupera só às vezes porque `res.stj.jus.br` tem vários backends** — ETags DIFERENTES (`1788006794168_534000` e `1788006817645_534000`) para o corpo **byte a byte idêntico** (mesmo sha256 `b0da897d…`) —, e 5 GETs condicionais com o mesmo validador deram **2× 304 / 3× 200 (40%)**. Mandar os dois ETags em lista, permitido pela RFC 9110 §13.1.2, foi **testado e é pior: 0 de 6** — o servidor compara o cabeçalho inteiro e a lista não casa com nada, então o coletor manda um validador só. **CJF e TST não emitem validador algum.** Economia real num dia sem mudança na origem: **piso 83.038 B (11,5%), expectativa medida ~296.600 B (41%), teto 617.038 B (85,2%)**. E o 304 exige origem inalterada: num feed de 117 notícias com uma execução por dia, quem colhe o 304 é a reexecução no mesmo dia e o fim de semana. O ganho garantido todo dia é o outro: robots.txt consultado (nunca era), teto diário, limitador por host, guarda de SSRF, classificação de erro e proveniência em disco.
- **Bloqueio real encontrado na migração, e que não era o RSS:** `www.cjf.jus.br` **recusa servir `/robots.txt`** — connection reset, HTTP 000, 8/8 tentativas com dois User-Agents — enquanto serve o feed em 200 no mesmo minuto. `sourcecollect` trata robots inalcançável como erro duro (por desenho), então a migração ingênua mataria a fonte CJF todo dia. Resolvido com `Options.RobotsInalcancavelPorHost`, exceção **nominal por host com justificativa medida**, no mesmo desenho fechado do `UserAgentPorHost` e com fundamento na RFC 9309 §2.3.1.4 (*Unreachable Status*) — nunca afrouxamento global: host que RESPONDE com robots.txt negando o caminho continua bloqueado.
- **Correção:** `cmd/collect-noticias-oficiais` migrado; `_estado.json` por fonte guarda ETag, Last-Modified, SHA-256 do corpo, bytes, status, itens e datas — a proveniência que o pacote mede e **não** persiste. Semântica de saída ajustada: 304 em todas as fontes é **sucesso** (o dia normal de um canal com GET condicional), e não a falha que o `len(todas)==0` antigo produzia; 200 sem item extraído continua falhando.
- **Status:** corrigido e commitado (commit `ae05001b`)

## BUG-158 — `isPendingAudit` é cego a "nao_conferido", e ingerir exclui ser aprovado por construção
- **Data:** 2026-08-29 · **Severidade:** MÉDIO
- **Sintoma e causa raiz:** `internal/sources/sources.go:144-146` — `isPendingAudit` só reconhece string vazia ou contendo "pendente"; o valor real usado em 4 fontes é `nao_conferido`, que passa batido. E `sources.go:148-150` — `ApprovedForIndexableLegalContent()` exige `AuditStatus == "approved" && !IngestionEnabled`: **ingerir e ser aprovado são mutuamente exclusivos por construção**, e **nenhuma das 58 fontes** tem `approved`. Com a autorização do dono para raspar, essa exclusão vira contradição de contrato.
- **Status:** aberto — task `caca-BUG-158`.

## BUG-159 — Trabalho pago descartado: 25 textos de diário anonimizados por dia, zero consumidores
- **Data:** 2026-08-29 · **Severidade:** MÉDIO
- **Sintoma:** a coleta produz 25 textos de diário anonimizados por dia e **nenhum consumidor os lê**. O contrato é explícito: texto redigido foi pago pelo dono e não se descarta.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao

## BUG-160 — A licença CC BY 4.0 declarada no ar colide com o primeiro corpo raspado
- **Data:** 2026-08-29 · **Severidade:** GRAVE (achado do crítico, não enfrentado pela frente)
- **Sintoma e causa raiz:** a DEC-031 fez o portal declarar **CC BY 4.0** sobre o acervo. Licenciar sob CC BY exige ser titular do que se licencia. No dia em que uma página publicar corpo de terceiro (notícia institucional, que é redação protegida pelo art. 7º), a declaração passa a licenciar obra alheia. Ato oficial (art. 8º IV) não tem o problema — não é objeto de proteção.
- **Correção:** recortar a licença por bloco (o acervo autoral sob CC BY; o bloco citado com atribuição e sem sublicenciamento) **antes** do primeiro corpo de Nível B ir ao ar.
- **Status:** aberto — task `caca-BUG-160`.

## BUG-161 — Planalto inacessível deste host, e o gate de proveniência não sabe disso
- **Data:** 2026-08-29 · **Severidade:** MÉDIO
- **Sintoma e causa raiz, medidos:** `curl` a `planalto.gov.br` deste host → `curl (56) Recv failure: Connection reset by peer`, HTTP **000**, em HEAD **e** em GET com range de 1 byte. `portal.stf.jus.br` idem. O canal oficial que responde é **`normas.leg.br`** (API pública LexML/Congresso, HTTP 206), já integrado em `cmd/collect-normas-federais`. Um gate que exigir `planalto.gov.br` alcançável reprovaria fonte válida — e `planalto.gov.br` é **70,5%** de todas as fontes do portal.
- **Ressalva registrada:** o encoding do normas.leg.br declara `legislationLegalValue = UnofficialLegalValue` — o texto juridicamente autêntico é o do DOU. Serve para fundamentar gate editorial; para peça que vá a juízo, confere-se contra o DOU.
- **Status:** FECHADO — carimbado com o sha do commit que o fechou (commit 60db827d).

## BUG-162 — normas-federais gravava ementa e link, e nunca baixava o texto integral da norma
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** 60 de 60 registros de `data/research/daily/normas-federais/2026-08-29.jsonl` tinham apenas `ementa` (só 6 acima de 400 caracteres) e um campo `texto_url` que **nenhum código buscava**. `cmd/collect-normas-federais` derivava a URL do articulado em `textoConsolidado()` e parava ali. O canal existia, custava requisição diária e não produzia corpo — é o "canal morto" no sentido literal. Junto, dois defeitos menores: `sha256_fonte` hasheia o **JSON-LD de metadados**, não o texto, e o nome enganava quem o lesse como prova de integridade do texto; e o texto da fonte **não é texto** — `…/texto` responde `text/html` com HTML do Aspose.Words, cujo cabeçalho traz `<!--[if gte mso 9]><o:Author>NOME DO SERVIDOR</o:Author>`, que uma extração por regex traria para dentro do dado público (provado: regex ingênuo vaza o autor; o tokenizador não).
- **Correção:** download do articulado com `-com-texto N`, extração por `planaltochannel.ExtractPlainTextChecked` (tokenizador real, reuso — não pacote novo), e o tripé fonte fechado com `texto_sha256` (do texto extraído, detecta mudança de redação) separado de `texto_origem_sha256` (do HTML como veio). Ligado em `tools/run-daily-content` com orçamento de cota declarado no comentário.
- **Status:** **FECHADO** — task `caca-BUG-162`.


## BUG-163 — so 49 municipios ja receberam texto de diario: o break no 25o item sempre pega o mesmo comeco da lista
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `cmd/collect-diarios-municipais` recebe `-com-texto 25` de `tools/run-daily-content:288` e o bloco de download (`main.go:349-378`) percorre a lista em ordem, com `break` ao atingir o teto. A lista chega ordenada, então os mesmos municípios ganham texto todo dia. Varredura de todo o histórico de `data/research/daily/diarios-municipais/*.jsonl`: 220 diários coletados por dia, ~24 com texto, e apenas **49 municípios distintos** já receberam texto — Andradina 8×, Aparecida 7×, Arapongas 7×, Araçariguama 7×, Banzaê 7×. Municípios fora do começo da ordenação **nunca** recebem. O portal só consegue escrever sobre uma fatia fixa do país. Agravante: o download é estritamente sequencial (um GET por vez), e é por isso que o teto é 25.
- **Correção:** seleção por menor cobertura histórica (determinística, lendo o próprio acervo) e download com pool limitado de workers, preservando a ordem do slice, as contagens e a dupla verificação de PII.
- **Status:** MORTO POR MEDICAO — a afirmacao nao se sustentava no dado; nao houve correcao


## BUG-164 — o venv da extracao de HTML aponta para o python3 do sistema, que nao tem trafilatura
- **Data:** 2026-08-29 · **Severidade:** MEDIO
- **Sintoma e causa raiz, medidos:** `internal/demandtextextractor.DefaultPythonBinary = "python3"` e `python3 -c 'import trafilatura'` falha neste host. O venv que deveria resolver, `.cache/demand-extraction-venv/bin/python`, é um **symlink para `python3`** (medido: `-> python3`, de 01/07) — aponta de volta para o interpretador sem a biblioteca. O extrator de HTML do canal de demanda está inoperante desde então; `demand_content_samples.jsonl` está parado em 29/06 com 28 KB. Não há timer de produção chamando, então é capacidade parada, não pipeline quebrado — mas é capacidade paga.
- **Correção:** adotar `go-trafilatura` (Apache-2.0), que o próprio repositório já mediu como superior neste caso — F1 0,904 vs 0,908 e **4,25 s vs 10,38 s** em 960 documentos (`docs/goal/PLANO_FRESCOR_DIARIO.md:912`) — eliminando o subprocesso Python deste caminho. Decisão coberta pela DEC-036.
- **Status:** aberto — task `caca-BUG-164`.

## BUG-165 — o anonimizador suprimia o nome do agente publico e tornava o ato oficial ilegivel
- **Data:** 2026-08-29 · **Severidade:** CRITICO
- **Sintoma e causa raiz, medidos:** varredura do acervo de diarios achou **88 ocorrencias de `[nome removido]`** em trechos como *"Exonerar a Sra. [nome removido] de Enfermeira, lotada na Secretaria de Saude"*. `internal/pii.Mascarar` mascarava o nome em ato de pessoal (`atoDePessoal`, o detector central do pacote) e `pii.Contem` REPROVAVA o texto por conter nome — o coletor entao descartava o texto que acabara de baixar e anonimizar. O canal parecia morto porque o proprio anonimizador o matava: nao se entende uma exoneracao sem saber quem foi exonerado, e um texto assim nao sustenta pagina nenhuma. O desenho estava invertido em relacao ao ordenamento: no Brasil a publicidade e a REGRA e o sigilo a EXCECAO.
- **Correção:** por ordem expressa do dono (advogado responsavel, 2026-08-29): nome de pessoa publica e nome em processo publico PODEM constar. `Mascarar` deixou de suprimir nome em ato de pessoal e passou a **registra-lo** como achado auditavel (`nome_agente_publico`); `Contem` so reprova por IDENTIFICADOR (CPF, CNPJ, RG — Res. CNJ 121/2010 art. 4o). Fundamentacao verificada em `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md`; gate novo `publicidade-nome-fonte-oficial` cobra os dois lados (identificador exposto E nome suprimido).
- **Status:** FECHADO — commit e200edfa; go-modern test ./internal/pii/ 16 testes ok; ./internal/publicidadenome/ 8 testes ok; cmd/check publicidade-nome-fonte-oficial pass; repii-acervo-diarios idempotente na 2a passada (commit e200edfa).


## BUG-166 — o campo nomes_mascarados passou a contar justamente o que NAO e mascarado
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz:** com o BUG-165 corrigido, `pii.Mascarar` passou a devolver achados de dois tipos — documento REMOVIDO e nome PRESERVADO —, e `cmd/collect-diarios-municipais` gravava `len(achados)` inteiro no campo `nomes_mascarados`. O campo passaria a contar como "mascarado" exatamente o que permanece no texto. Campo cujo nome nao corresponde ao conteudo e bug (R1), e este alimentaria toda auditoria de privacidade do canal com numero invertido.
- **Correção:** campo desmembrado em `documentos_mascarados` (o que saiu) e `nomes_publicos_preservados` (o que a publicidade manda manter, mantido como serie de auditoria). O merge-on-write preserva os dois.
- **Status:** FECHADO — commit e200edfa; go-modern test ./internal/pii/ 16 testes ok; ./internal/publicidadenome/ 8 testes ok; cmd/check publicidade-nome-fonte-oficial pass; repii-acervo-diarios idempotente na 2a passada (commit e200edfa).


## BUG-167 — TetoDiario=50 no coletor de diarios e o teto real do -com-texto, e nada avisa
- **Data:** 2026-08-29 · **Severidade:** MEDIO
- **Sintoma e causa raiz:** `novoColetor` em `cmd/collect-diarios-municipais/main.go` fixa `TetoDiario: 50` no `sourcecollect`. A cota e por host e por processo, e `data.queridodiario.ok.org.br` e host proprio: `-com-texto` acima de ~50 morre no meio com `ErrDailyQuotaExhausted`, sem que nada no invocador diga isso. Achado do agente de engenharia durante a correcao do BUG-163.
- **Correção:** elevar o teto com criterio de polidez explicito (a fonte e servidor de uma ONG) e fazer o coletor recusar de entrada `-com-texto` maior que a cota disponivel, em vez de falhar no meio.
- **Status:** corrigido e commitado (commit `d16aadde`)


## BUG-168 — thundering herd de robots.txt no sourcecollect atinge os quatro coletores
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz:** `internal/sourcecollect.robotsPermite` (~linha 417) busca o `robots.txt` FORA do limitador de taxa e sem `singleflight`. Qualquer coletor que passe a baixar em paralelo dispara N GETs simultaneos de robots.txt no mesmo host — no caso do Querido Dirario, servidor de uma ONG. Mitigado localmente no coletor de diarios por uma primeira coleta sequencial que aquece o cache, mas a causa e do pacote e alcanca os quatro coletores.
- **Correção:** `singleflight` ou lock por host em `internal/sourcecollect`, e a busca de robots passando pelo mesmo limitador das demais requisicoes.
- **Status:** corrigido e commitado (commit `ae05001b`)


## BUG-169 — sort.Slice nao estavel deixa indefinida a ordem entre duas edicoes do mesmo municipio
- **Data:** 2026-08-29 · **Severidade:** LEVE
- **Sintoma:** `cmd/collect-diarios-municipais/main.go:339` usa `sort.Slice`, que nao e estavel. Para a mesma entrada a saida e deterministica, mas a ordem relativa entre duas edicoes do mesmo municipio no mesmo dia e indefinida — e e ela que decide qual edicao representa o municipio na selecao de texto. Pre-existente ao BUG-163.
- **Correção:** trocar por `sort.SliceStable` com criterio de desempate explicito (numero da edicao).
- **Status:** corrigido e commitado (commit `d16aadde`)


## BUG-170 — normas-federais rebaixa os mesmos 60 textos todo dia, com o condicional HTTP parado
- **Data:** 2026-08-29 · **Severidade:** MEDIO
- **Sintoma e causa raiz:** `cmd/collect-normas-federais` chama `coletor.Buscar(ctx, alvo, nil)` — o terceiro parametro e o `*sourcecollect.Condicional`, e passar `nil` desliga o `If-None-Match`/`If-Modified-Since`. Como a janela do sitemap e de 180 dias e o teto e 60, sao em boa parte as MESMAS normas todo dia: o coletor re-baixa integralmente conteudo que nao mudou, gastando cota e banda de uma fonte publica. O `sourcecollect` ja trata 304 (`Resultado.NaoModificado`) — a capacidade existe e nao esta ligada. Achado do critico adversarial.
- **Correção:** guardar ETag/Last-Modified por URL (o registro ja tem `texto_origem_sha256` como chave natural) e passar o condicional; no 304, preservar o texto ja gravado em vez de rebaixar.
- **Status:** aberto — task `caca-BUG-170`.


## BUG-171 — teste de governanca vermelho porque o CLAUDE.md perdeu a secao que ele exige
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos pelo critico:** `internal/contract/misc/peer_governance_test.go:55` (`TestLiveAgentGovernanceTreatsClaudeAndCodexAsPeerLeads`) esta VERMELHO, e `git show HEAD:CLAUDE.md | grep -c 'Governanca entre pares'` devolve **0** — a secao que o teste cobra nao esta no arquivo, e nao saiu no diff desta sessao. E pre-existente, alcancado pela suite diaria (`./internal/...`), e portanto vermelho cronico que dessensibiliza a bateria.
- **Correção:** decidir entre restaurar a secao no CLAUDE.md ou atualizar o teste ao contrato vigente (o Codex esta desativado por ordem de 2026-07-21, o que sugere que o teste e que envelheceu) — lendo o historico do arquivo antes.
- **Status:** FECHADO — carimbado com o sha do commit que o fechou (commit e200edfa).

## BUG-172 — o CNPJ da contratada era mascarado, apagando justamente o que a LAI manda publicar
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `internal/pii` mascarava CNPJ junto com CPF e RG. Amostragem de 5 diarios reais em 2026-08-29 mostrou 44 CPF, 0 RG e 1 CNPJ — e o contexto do unico CNPJ era *"EXTRATO DE CONTRATO ADMINISTRATIVO No 0625014/2026. CONTRATADO(A): F & J REPRESENTACAO LTDA, inscrito no CNPJ no 57.080.860/0001-08. Objeto: REGISTRO DE PRECOS"*. Ou seja: o mascaramento apagava a informacao mais util que um diario municipal oferece a um portal juridico — quem contratou com o municipio e para que —, e que a LAI (Lei 12.527/2011, art. 8o, §1o, IV) obriga a publicar. A LGPD protege a pessoa NATURAL (art. 1o); CNPJ identifica pessoa juridica, cuja situacao cadastral a Receita disponibiliza em consulta publica aberta. Nao ha dado pessoal ali.
- **Correção:** CNPJ sai do `Mascarar` e do predicado `Contem`, e nao entra no gate `publicidade-nome-fonte-oficial`. CPF e RG continuam. Ha teste provando que no MESMO texto o CPF sai e o CNPJ fica.
- **Status:** FECHADO — commit e200edfa; go-modern test ./internal/pii/ 16 testes ok; ./internal/publicidadenome/ 8 testes ok; cmd/check publicidade-nome-fonte-oficial pass; repii-acervo-diarios idempotente na 2a passada (commit e200edfa).


## BUG-173 — a janela de edicoes andou e 24 textos ja baixados sumiram do arquivo do dia
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** o arquivo do canal tem nome de data de COLETA, e a janela de EDICOES anda: a rodada da manha de 2026-08-29 trouxe edicoes de 27 e 28/08, a da tarde trouxe 28 e 29/08. O merge-on-write recem-criado fundia campo a campo por chave territorio+edicao+data — nenhuma chave bateu, a fusao preservou ZERO, e os 24 textos ja baixados e anonimizados da manha sumiram do arquivo (recuperaveis so por `git show`). Regressao introduzida na mesma sessao, apanhada por medicao propria antes de ir para producao.
- **Correção:** a fusao passou a preservar o REGISTRO INTEIRO: registro antigo com texto que a rodada atual nao contem e anexado em ordem deterministica. Os 24 textos foram recuperados de `git show HEAD:` e fundidos ao arquivo do dia (49 com texto no total). Teste `TestFusaoPreservaRegistroInteiroQuandoAJanelaDeEdicoesAnda` fixa o caso, inclusive o determinismo da ordem.
- **Status:** FECHADO — commit e200edfa; go-modern test ./internal/pii/ 16 testes ok; ./internal/publicidadenome/ 8 testes ok; cmd/check publicidade-nome-fonte-oficial pass; repii-acervo-diarios idempotente na 2a passada (commit e200edfa).

## BUG-174 — o texto do diario e coletado, anonimizado e nunca vira pagina: o gerador so monta indice
- **Data:** 2026-08-29 · **Severidade:** CRITICO
- **Sintoma e causa raiz, medidos:** `cmd/generate-diario-pages/main.go` NAO le `texto_anonimo` (grep = 0 ocorrencias) e o proprio doc do pacote declara *"NAO PUBLICA — o texto do diario"*. O resultado e que as paginas de `/diarios/` sao indices-molde: *"Em 26 de agosto de 2026, 26 municipios de Sao Paulo publicaram diario oficial, em 26 edicoes"* seguido da lista de edicoes. E exatamente essa forma que produz os pares de similaridade de 0,87 do BUG-044 (molde identico com numeros trocados) e o thin content do canal. Enquanto isso o texto integral e baixado, passa pelo anonimizador e fica parado no JSONL — 49 edicoes com texto no acervo de 2026-08-29, zero consumidoras.
- **Correção:** o gerador passa a produzir conteudo real por edicao sob a **regra das duas camadas da DEC-032**: bloco de texto oficial CITADO (com URL, data e hash, que o coletor ja grava) em bloco distinto do COMENTARIO AUTORAL, com piso medido de comentario proprio. Publicar o texto oficial sozinho seria espelho e thin content; e o indice sozinho, que e o que existe hoje, e molde. Exige tambem anti-template por edicao (similaridade < 0,70) e passar pelo pipeline sancionado de publicacao.
- **★ BLOQUEADO POR BUG-177.** O que hoje segura o caso Capela (adolescente de 15 anos, *"diabetes mellitus tipo 1 — CID 10: E10"*, mãe nomeada por extenso) fora de página pública é **justamente o defeito descrito aqui**: o gerador não publica o texto. Implementar este bug sem o detector de exceções do BUG-177 publica esse registro. A ordem é BUG-177 primeiro.
- **Status:** corrigido e commitado (commit `0714ae30 7937c979 0e88652c`)

## BUG-175 — quatro fontes declaram guardar texto oficial bruto e o teste de contrato proibe, ha tempo indeterminado
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `TestSourceRegistryV2CarriesBlockedPoliciesForScale` reprova com *"source camara-legin stores raw official text"*. O campo `raw_official_text_stored` e derivado por `snapshotPolicyFields(snapshotChannels)` em `internal/sourceregistryv2/registry.go:439`, e **4 registros do artefato JA COMMITADO** o trazem `true` — logo o teste ja estava vermelho antes de qualquer mudanca desta sessao. Ficava ESCONDIDO atras de outro erro: a validacao abortava mais cedo, em `source_registry_v2_evidence_after_checked_at`, e o `t.Fatalf` daquela linha nunca deixava a execucao chegar na assercao de `raw_official_text_stored`. Um erro tapando o outro.
- **Correção:** decidir entre as duas leituras, com medicao: ou o repositorio de fato guarda texto oficial bruto dessas 4 fontes (e entao o teste esta certo e o armazenamento e que precisa sair), ou `snapshotPolicyFields` deriva o campo de canal de snapshot que nao guarda texto (e entao o derivador e que mente). `data/source-snapshots/` nao tem nada de camara-legin, o que aponta para a segunda hipotese.
- **Status:** aberto — task `caca-BUG-175`.


## BUG-176 — o checked_at global do registry v2 saia da PRIMEIRA fonte da lista, nao da evidencia mais recente
- **Data:** 2026-08-29 · **Severidade:** MEDIO
- **Sintoma e causa raiz:** `generationCheckedAt` (`internal/sourceregistryv2/registry.go:834`) percorre as fontes e devolve o PRIMEIRO `checked_at` nao vazio que encontrar — uma escolha arbitraria, que depende da ordem da lista. Consequencia medida em 2026-08-29: ao registrar auditoria de termos com data corrente, a validacao acusou `source_registry_v2_evidence_after_checked_at` em 8 campos, porque o artefato carregava `checked_at=2026-07-22` e as evidencias novas eram "do futuro". Auditoria mais recente REPROVANDO por ser mais recente e o oposto do que o gate quer.
- **Correção:** derivar o `checked_at` da geracao do MAXIMO das datas de evidencia, ou da data explicita passada ao gerador, nunca da posicao na lista. Contornado nesta sessao regerando o artefato com `--checked-at 2026-08-29`, o que fecha o sintoma mas nao a causa.
- **Status:** aberto — task `caca-BUG-176`.

## BUG-177 — as excecoes da politica de publicidade nao tem mecanismo nenhum, e ha casos reais no acervo
- **Data:** 2026-08-29 · **Severidade:** CRITICO
- **Sintoma e causa raiz, medidos pelo critico adversarial:** `internal/pii` promete que material de excecao *"ou nao e coletado, ou o caso e revisado"* e aponta `Suspeitas()` como instrumento — mas `Suspeitas()` tem **ZERO consumidores** fora do proprio pacote (grep em cmd/ e internal/), e o gate `publicidade-nome-fonte-oficial` nao testa nenhuma classe de excecao. Dois casos REAIS ja no acervo, ambos com `texto_publicavel=true` e gate verde: **Capela** (2026-08-28.jsonl:13) — sentenca integral com adolescente de 15 anos, diagnostico *"diabetes mellitus tipo 1 - CID 10: E10"*, mae nomeada por extenso e numero unico do processo, o que reune menor identificavel E dado sensivel de saude (LGPD art. 5o II c/c art. 11); **Campinas** (2026-08-21.jsonl:19) — desligamento NOMINAL de beneficiarios de Auxilio Moradia, que e programa de assistencia social. **Mitigacao que segura hoje:** `cmd/generate-diario-pages` nao publica o texto do diario (so existencia, numero e link), entao nao ha vazamento em pagina publica AGORA — o risco e o dado versionado e o dia em que a citacao DEC-032 tocar esse texto (BUG-174).
- **Correção:** detectores de excecao no gate, sobre marcadores literais que a propria lei fornece: CID/diagnostico ao lado de nome (LGPD art. 11), 'ato infracional'/'adolescente'/'conselho tutelar' (ECA 143 e 247), 'medida protetiva'/'violencia domestica' (Lei 11.340 art. 17-A), 'adocao' (ECA 47 §4o), 'segredo de justica' (CPC 189), e nome ao lado de beneficio assistencial. Achado da excecao NAO deve mascarar automaticamente: deve BLOQUEAR a promocao daquele registro a corpo de pagina e mandar para revisao — a excecao nao se resolve por regex, e e por isso que o piso e bloquear, nao limpar.
- **Status:** FECHADO — detector de excecoes com 8 classes, cada uma com dispositivo; trava sobre o CORPO PUBLICADO (varre os shards v2 e reprova); API PodeVirarCorpoDePagina para o gerador. Medido: 21 de 172 registros com texto trazem marcador de excecao (14 crianca/adolescente, 9 dado sensivel de saude, 2 violencia domestica, 2 ato infracional, 1 segredo de justica). 28 casos de teste, incluindo falso positivo sobre 6 atos administrativos comuns (commit b866d15d).


## BUG-178 — a regua que separa acervo velho de novo no gate e um campo que o proprio produtor controla
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz:** `internal/publicidadenome` decide se cobra a politica nova olhando se o registro traz `nomes_mascarados` (marca do coletor antigo). O campo vem do JSONL que o gate policia, entao um produtor futuro que grave `nomes_mascarados: 1` classifica a propria supressao como "heranca" e **nunca reprova**. A regua e melhor que a de data — que ja errou, acusando 7 municipios de descumprir uma ordem que ainda nao existia —, mas continua sendo autodeclaracao do fiscalizado. Achado do critico adversarial.
- **Correção:** derivar a epoca do registro de algo que o produtor nao escolhe: a data de commit do arquivo no git, ou um campo de versao de esquema assinado pelo proprio coletor e verificado contra a constante do binario.
- **Status:** aberto — task `caca-BUG-178`.

## BUG-179 — o gate aceita qualquer URL sob um source_id curado: o vinculo id<->dominio nao e verificado
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, apontados pelo critico adversarial:** `internal/quality/quality.go:258` decide se a citacao e legitima com `!registrada && !isOfficialSourceURL(url)` — basta a pagina declarar um `source_id` que exista no registro para o primeiro ramo ser satisfeito, **sem que ninguem confira se a URL citada pertence aquela fonte**. No caso corrigido em 2026-08-29 (paginas de /diarios/) a URL de fato pertence ao dominio da fonte curada, mas o gate teria aceitado qualquer endereco sob aquele ID. E uma porta aberta para lavagem de citacao: apontar um blog e carimba-lo com o ID de uma fonte oficial auditada.
- **Correção:** conferir o host da URL citada contra `OfficialDomains`/`CanonicalBaseURLs` do registro da fonte (o `sourceregistryv2` ja deriva os dois por `hostsOf(canonicalBaseURLs)`), e acusar quando o ID nao cobre o dominio.
- **Status:** aberto — task `caca-BUG-179`.

## FAMILIA-A — 42 leitores confundiam o depósito de sitemaps com o índice que anuncia
- **Data:** 2026-08-29 · **Severidade:** CRÍTICO
- **Sintoma e causa raiz, medidos:** o universo público do portal é o que `public/sitemap.xml` **anuncia** (34 shards), não o que `public/sitemaps/` **guarda** (62 `.xml` + 58 `.br`). Os 28 a mais são shards aposentados em carência — servidos por compatibilidade, fora do índice. Consumidores que globavam o diretório trabalhavam com universo inflado em **81,6%**: o aquecedor de borda estourava a janela de 45 min e a unit morria por SIGTERM; `check-edge-cache-coverage` publicava `universo_urls: 18731` e derivava dele um alerta crítico 81% errado; `check-internal-link-floor` morria com `UnicodeDecodeError` ao abrir o primeiro `.br` como UTF-8.
- **Correção:** função única `tools/wikiuniverso` derivando o universo do ÍNDICE, com `UniversoIndisponivel` quando o índice anuncia shard que não existe no disco — silenciar isso seria trocar um erro alto por um número errado. Migração em duas levas (`32313dfd` e `ae35be43`), com triagem por critério e não por contagem: dos 43 arquivos que mencionam o caminho, 8 migrados, 6 geradores que legitimamente escrevem o diretório, 6 testes, 31 menções em comentário ou caminho de escrita, e **2 leitores reais** — `check-contagens-publicas-reconciliam` (que reconciliava manifesto × sitemap contra o depósito) e `check-edge-live` (que sorteava a URL de sonda dali, podendo alertar apagão sobre rota não mais anunciada).
- **Status:** **FECHADO** — task `caca-FAMILIA-A`, commit `ae35be43`.

## BUG-180 — quatro dos cinco coletores apagavam a coleta do dia ao rodar de novo
- **Data:** 2026-08-29 · **Severidade:** CRITICO
- **Sintoma e causa raiz, medidos:** quatro dos cinco coletores gravam o arquivo do dia com `os.WriteFile` puro e substituem o conteudo inteiro. O defeito se mostrou no meio de outra tarefa: `collect-noticias-oficiais -limite 5`, rodado so para verificar o parser de feed apos um `go mod tidy`, reduziu `data/research/daily/noticias-oficiais/2026-08-29.jsonl` de **169 registros para 5**. Os 164 estavam commitados e voltaram por `git show HEAD:` -- sem commit, teriam sumido, e cada um custou uma requisicao a servidor publico. E a familia do BUG-173, que foi corrigido caso a caso so no coletor de diarios.
- **Correção:** `internal/coletafusao` funde por chave declarada, operando sobre as LINHAS do JSONL. Ligado nos tres coletores que faltavam. ★ E o pacote quase virou o mecanismo da perda: ao liga-lo em noticias, declarei `chave` como identificador -- o campo se chama assim, parece identificador, e e o identificador da FONTE ('stj' em 119 de 169 registros); 5 novos 'substituiram' 119 antigos e o arquivo caiu para 55. Dai a guarda que ficou: chave cujas ocorrencias distintas cobrem menos da metade dos registros ABORTA com erro que explica a causa, em vez de apagar. Verificado end-to-end: 169 -> 169, com 164 preservados.
- **Status:** **FECHADO** — task `caca-BUG-180`, commit `dc20bf83`.

## BUG-181 — cinco CVEs novas em tools/sca sem excecao registrada, e o gate nao distingue produto de ferramenta
- **Data:** 2026-08-29 · **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** depois de limpar o scan do produto (BUG-056), `cmd/check sca-osv` continua vermelho com `sca_osv_tools_failed` e `sca_osv_scorecard_failed`. As CVEs sao **GO-2026-6213, GO-2026-6214, GO-2026-5064, GO-2026-5338 e GO-2026-5378**, nenhuma registrada em `tools/sca/osv-scanner.toml` -- apareceram depois das cinco ja documentadas (todas do cliente Docker que o osv-scanner traz). Sao dependencias de FERRAMENTA, nao do produto: nao entram em binario que vai ao ar. Mas o gate agrega os tres scans num veredito so, entao um vermelho de ferramenta e indistinguivel de um vermelho do produto -- e foi exatamente essa confusao que deixou a CVE do produto sem tratamento por semanas.
- **Correção:** cada uma das cinco precisa de fundamento proprio (qual ferramenta a traz, se o codigo vulneravel e alcancado pelo uso que se faz dela, se ha versao corrigida) e de `ignoreUntil`. E o gate deveria reportar produto e ferramenta em linhas separadas, para que vermelho de ferramenta nunca mais mascare vermelho de produto.
- **Status:** corrigido e commitado

## BUG-182 — a armadilha numero um do repo era uma linha de go.mod que faltava
- **Data:** 2026-08-29 · **Severidade:** CRITICO
- **Sintoma e causa raiz:** o padrao de pacotes do Go nao expandia porque `var/nginx/{body,fastcgi,proxy,scgi,uwsgi}` pertence ao runtime do nginx com modo 0700, e o caminhador do Go abortava o padrao INTEIRO (`go: pattern all: open /opt/wiki/var/nginx/fastcgi: permission denied`). Era a causa COMUM de tres bugs ja catalogados -- BUG-107 (`go vet` nunca verificou nada), BUG-108 (`check-all` testava zero pacotes), BUG-135 (`check-go-compile-closure` cego) -- e de um quarto que ninguem tinha nomeado: **`go mod tidy` NUNCA pode rodar**, deixando dependencia orfa no go.mod sem que ninguem pudesse remove-la.
- **Correção:** diretiva `ignore ./var` no go.mod raiz (Go 1.25+). Uma linha RASTREADA. Medido: `go list` do padrao passa a sair exit 0 com 488 pacotes, os mesmos de `./internal/... ./cmd/...`, e `go mod tidy` sai exit 0. Duas alternativas foram testadas e descartadas: `var/go.mod` sentinela (inutil -- `/var/` esta no .gitignore e `!/var/go.mod` nao resgata, porque git nao re-inclui arquivo sob diretorio excluido; viveria num disco so) e mover `var/nginx` (mexeria em caminho de producao). A PROIBICAO do padrao permanece, com fundamento novo: agora expande e e full-tree pesado. DEC-039.
- **Status:** **FECHADO** — task `caca-BUG-182`, commit `56d1b34b`.

## BUG-183 — `performance-budget` reprovava as 10.116 páginas por três defeitos em cascata, nenhum deles de conteúdo
- **Data:** 2026-08-29 (caça aos bugs — ordem do dono)
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** o gate acusava script de runtime em TODAS as páginas publicadas. Três defeitos empilhados, e nenhum no acervo. (1) A isenção do script autorizado recebia o texto já minusculizado, então o `strings.Replace` byte a byte nunca casava — `htmlcontract` e `htmlpolicy` isentavam certo; era este gate que tinha a cópia quebrada. (2) O marcador de runtime era substring sobre o texto inteiro e casava `r.json()` DENTRO do próprio script autorizado; passou a usar a checagem estrutural por árvore que o repositório já tinha. (3) `.js` casava `.jsp`, e o STJ publica em `.jsp` — a fronteira de extensão passou a exigir um terminador de um conjunto fechado (`? # / ; & " '` e espaço em branco), com o `;` incluído de propósito por causa do path parameter de servlet (`;jsessionid=`).
- **Correção:** `internal/checks/checks.go` (a cópia da isenção e o desconto duplo), `internal/htmlpolicy/htmlpolicy.go` (fronteira de extensão), com sete casos de fronteira travados em teste.
- **Status:** corrigido e commitado (commit `65de0a2b`)
- **Achado por:** crítica adversarial da CSP; reproduzido com `./tools/go-modern run ./cmd/check performance-budget`.
- **Lição:** um gate que reprova em MASSA quase nunca está vendo conteúdo ruim. Antes de tocar no dado, provar que o detector está certo — cinco vezes nesta sessão o vermelho era do detector.

## BUG-C4 — `go vet` daria falso-verde por VetxOnly, e `go-build-check` usaria o padrão full-tree
- **Data:** 2026-08-29 (crítico nº 4 do goal)
- **Severidade:** GRAVE (enunciado) — REFUTADO por medição
- **Sintoma e causa raiz, medidos:** a segunda metade do enunciado está MORTA. `grep -n ignore go.mod` → linha 31, `ignore ./var` (DEC-039, commit `56d1b34b`), que foi o que fez o padrão full-tree voltar a expandir. E `tools/go-build-check:72`, re-grepado, usa escopo EXPLÍCITO com nonce — `go vet -tags "devcmds,${VET_NONCE}"` sobre `internal` e `cmd` —, não o padrão que o enunciado acusava. A âncora do catálogo (linha 46) derivou.
- **Status:** refutado
- **Lição:** âncora de catálogo envelhece em horas neste repositório; re-grepar antes de abrir frente economiza a frente inteira.

## BUG-C5 — googlebot-smoke validaria o próprio cache
- **Data:** 2026-08-29 (crítico nº 5 do goal)
- **Severidade:** GRAVE (enunciado) — REFUTADO por experimento
- **Sintoma e causa raiz, medidos:** experimento controlado, mesmo binário, dois minutos consecutivos. Envenenei o caminho FIXO do cache (`/tmp/portaljuridico-googlebot-smoke-cache/index.json` com lixo) e o gate saiu **exit=0** em 50,9 s, com `manifest_routes=10116` — ou seja, ele NÃO valida o próprio cache. O defeito já havia sido corrigido antes desta sessão.
- **Status:** refutado
- **Lição:** "gate valida o próprio cache" se derruba envenenando o cache e medindo o exit — não se conclui lendo o código.

## BUG-C6 — public-release-transaction acusaria 59.388 erros de dois campos ausentes
- **Data:** 2026-08-29 (crítico nº 6 do goal)
- **Severidade:** GRAVE — REESCOPADO, segue aberto
- **Sintoma e causa raiz, medidos:** o enunciado dizia "DOIS campos que o produtor nunca escreve: `source_type` e `use_in_content`". Medido sem cap de erros: são **10.140 achados, dos quais 10.116 são `public_release_manifest_sitemap_sha256_mismatch`** — divergência entre o SHA do sitemap no manifesto e o do disco. Isso é o estado NORMAL entre um build e a publicação seguinte, não defeito de produtor: é o acervo reconstruído esperando o manifesto ser reescrito.
- **★ REABERTO em 2026-08-30, e o fecho anterior estava errado.** Eu havia declarado o C6 fechado citando `check-http-smoke` — que é outro gate. Rodado o gate que de fato reprovava, DEPOIS da publicação: `./tools/go-modern run ./cmd/check public-release-transaction` continua em `exit 1`, com `omitted_failures=9918`. A publicação **não fecha** este achado, e a razão é a causa-raiz que só apareceu ao rastrear uma página até o arquivo:
  - `sitemapShardPathByPagePath` (`internal/publicrelease/publicrelease.go:6406`) **RECALCULA** o plano de shards com `sitemap.PlanShards` e compara o hash desse plano novo com o `sitemap_sha256` que o manifesto gravou no momento da publicação. São dois artefatos de momentos diferentes; a comparação nunca coincide de forma estável.
  - E o mapa é `map[path]shard`, um shard por página — o que **não descreve o disco**. Rastreada a página `aer-overbooking-voluntarios-negociacao`: a URL dela aparece em **DOIS** arquivos, `pages-0005.xml` (hash `e88ddda4…`, exatamente o que o manifesto grava) e `pages-0050.xml`. O segundo é shard **em carência** — retirado do índice e servindo 200 por oito dias, que é comportamento deliberado deste repositório.
- **O que foi medido e está SÃO, para não confundir bookkeeping com defeito servido:** o índice `public/sitemap.xml` referencia 44 shards, **todos presentes no disco** (zero ausentes); há 28 shards no disco fora do índice, que são exatamente os em carência; e os 42 hashes de sitemap gravados no manifesto **existem todos** no disco. Nenhum 404, nenhum órfão anunciado.
- **Status:** FECHADO em 2026-08-30, e a correção foi a que a medição indicava — mudar a TESTEMUNHA, não a exigência.
  - `TransactionPlan` ganhou o campo **opcional** `SitemapShardByPagePath`. No caminho READ-ONLY (`ValidateWorkspace`, que é o que `cmd/check public-release-transaction` roda) ele é preenchido a partir de `public/sitemap.xml` e dos shards que o índice referencia: a pergunta ali é "o manifesto descreve o que está SERVIDO?". No caminho da **transação de publicação** o campo fica vazio de propósito e a régua segue sendo o plano — ali o plano é o artefato que será instalado, e comparar contra ele é a guarda fail-closed que impede publicar manifesto incoerente. A guarda da transação não foi tocada, e `TestParidadeDeSitemapUsaOArtefatoSERVIDOQuandoEleEDeclarado` trava isso com um veredito próprio.
  - Os três motivos de reprovação continuam de pé nos dois caminhos: hash que não corresponde a shard nenhum, shard que não carrega a rota, e rota sem shard. A fixture do teste é o caso que derrubava o detector — a mesma URL em dois shards, um deles fora do índice por carência.
  - **Medido depois:** `public_release_manifest_sitemap_sha256_mismatch` caiu de **9.918+ para ZERO**, e `public_release_*` sumiu por completo da saída. As 33 issues restantes são `v2_stock_freshness_*`, consequência direta da migração da LGPD feita na mesma sessão — o recibo aponta para o estoque anterior, e o próximo re-ingest as fecha. `internal/publicrelease`: suíte inteira verde.

## BUG-C7 — GOAL.md declararia published_manifest=0 como regra vigente
- **Data:** 2026-08-29 (crítico nº 7 do goal)
- **Severidade:** GRAVE (enunciado) — REFUTADO por medição
- **Sintoma e causa raiz, medidos:** `./tools/check-contrato-vs-medicao` → `published_manifest: 10116 linhas, 10116 unique_intent_id / CLAUDE.md declara: 10116 páginas / OK`, EXIT=0. As seis ocorrências de `published_manifest = 0` no `GOAL.md` estão TODAS escudadas por rótulo "CONTADORES VENCIDOS", bloco de citação ou marcação datada — nenhuma se apresenta como regra vigente.
- **Status:** refutado
- **Lição:** o enunciado já trazia a restrição certa ("NÃO exija igualdade exata: quebra o pre-commit a cada publicação") — e a medição mostrou que nem a correção era necessária.


## BUG-184 — a fábrica parava três horas por dia porque o recibo tinha dois calendários
- **Data:** 2026-08-30
- **Severidade:** CRÍTICO — travava toda publicação numa faixa diária
- **Sintoma e causa raiz, medidos:** o recibo do ingest carrega `validation_as_of` (dia UTC) e `legal_as_of` (dia de São Paulo), e `stock_freshness.go:361-364` exige que as duas batam com o relógio de agora. `TestNenhumMinutoDoDiaTemCalendarioDivergente` varre o dia minuto a minuto e acusava **180 minutos**, das 21:00 às 24:00 BRT. Às 00:48Z, `check-v2-stock-epoch` devolvia `v2_stock_freshness_validation_as_of_stale: receipt=2026-08-29 required=2026-08-30` sobre um ingest bem-sucedido de sete horas antes, com o estoque intocado. A guarda 00-03Z de `tools/ingest-v2-stock` cobria só a outra boca do buraco.
- **Correção:** `NormalizeValidationAsOf` trunca no dia civil brasileiro (DEC-040); três parses de data pura foram para `time.ParseInLocation`; `directValidatorSnapshotAsOf` declarada no fuso legal; a guarda saiu com a razão registrada; quatro testes que travavam o design antigo foram reescritos.
- **Status:** FECHADO

## BUG-185 — 19 testes de internal/v2ingest vermelhos e invisíveis, por três portas do gate
- **Data:** 2026-08-30
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** a família `TestCurrentLegalFacts*`/`TestTema987*` falha em `internal/v2ingest`. Medido em worktree isolada sobre `c01f0685` — antes do commit da OAB e dos dois renames de dado desta sessão —, eles **já falhavam**: não são regressão de commit nenhum de hoje. Refletem dívida visível no ingest do acervo: `data/ops/v2_ingest_report.jsonl` traz **140 ocorrências** de `current_legal_fact_source_missing`, dentro de 2.388 rejeições sobre 10.225 linhas. Ninguém os via por três portas, todas usadas em 29/08: o commit `1ee69ce8` tocou **sete** pacotes e o teto de seis faz o teste focado **pular em silêncio**; `03ac4e8e` e `745720c1` são commits de dado, que não rodam teste Go.
- **Correção parcial:** `data/ops/testes_vermelhos_conhecidos.json` nomeia os 19 com commit e data, e `tools/check-baseline-testes-vermelhos` (ligado ao pre-commit) passa a reprovar por REGRESSÃO — falha fora do baseline —, por baseline inflado (teste que voltou a passar) e por estouro de tempo. O gate deixou de recusar commit correto por dívida alheia sem anistiar nada.
- **Status:** a fatia da LGPD FECHOU em 2026-08-30, e a correção era o OPOSTO da que o gate prescrevia. Baixados os dois documentos do Planalto com os cabeçalhos que `tools/generate-legal-corpus` já usa — e o WAF, que eu havia registrado como bloqueio, responde 200 sem dificuldade: `l13709.htm` tem **357 âncoras, 351 de artigo**; `l13709compilado.htm` tem **2, nenhuma de artigo**. Migrar em bloco jogaria as 175 citações com deep-link no topo de um documento de 230 KB. A régua passou a ser por caso — com âncora fica no original, sem âncora vai para o compilado —, **91 das 96 páginas destravaram só com isso** e as outras 5 foram migradas por `tools/generate-lgpd-diploma-source-migration-20260830`, com o documento baixado de verdade e o sha256 na evidência. Restam ZERO citações ao diploma sem âncora. Os 19 testes vermelhos de `TestCurrentLegalFacts*` continuam abertos e nomeados no baseline.
- **A anatomia das 197 páginas rejeitadas, medida em 2026-08-30:** 61 razões distintas, e a maior sozinha responde por metade —
  `current_legal_fact_source_stale:lgpd_legacy_uncompiled_statute_path`, **98 páginas** de LGPD.
  A regra (`internal/v2ingest/current_legal_facts_lgpd.go:25`) recusa quem cita a LGPD pela URL
  **não compilada** (`l13709.htm`) em vez da compilada (`l13709compilado.htm`), e o estoque está
  com a migração literalmente pela metade: `grep -ho 'l13709[a-z]*\.htm' data/editorial/v2_pages/*.jsonl`
  → **236 legadas × 179 compiladas**.
- **Por que a troca NÃO é mecânica, e isto foi medido antes de eu tocar em nada:**
  `data/ops/v2_official_source_verify_url_cache.jsonl` mostra que a legada **não redireciona** —
  `final_url` é ela mesma, HTTP 200, checada em 2026-08-04 —, e a compilada também responde 200 por
  conta própria. São dois documentos vivos e diferentes: a legada é o texto ORIGINAL, a compilada
  traz as alterações posteriores. Trocar a URL é trocar de FONTE, e cada `anchor_claim` foi conferido
  contra o texto da não compilada. Fazer a troca sem reverificar a âncora seria gravar proveniência
  que ninguém verificou — exatamente o que o contrato chama de fraude. A reverificação depende do
  Planalto, que hoje devolve `Connection reset by peer` (WAF).
- **Próximo passo nomeado:** (a) reverificar as 236 âncoras contra `l13709compilado.htm` por
  `cmd/generate-v2-official-source-verify`, numa janela em que o WAF do Planalto responda, e só então
  migrar — 98 páginas escritas e pagas voltam ao estoque publicável; (b) o resto por família
  (tema_987 com 46+28+28 ocorrências, lgpd art. 19 com 11, aereo02/03/05/06, imobiliario05-09,
  familia13, criminal13, telecom03, trabalhista-p1), conferindo cada regra de fato jurídico contra a
  fonte oficial antes de mexer na fixture — é matéria de vigência de norma, não de teste.

## BUG-186 — o teto do teste focado foi calibrado sobre a suíte errada
- **Data:** 2026-08-30
- **Severidade:** GRAVE — nenhum commit em `internal/v2ingest` passava
- **Sintoma e causa raiz, medidos:** o teto de 420 s veio de `internal/checks` (283 s), tomado por "a suíte mais lenta" sem ter medido a maior. `internal/v2ingest` leva **611 s**: 855 funções de teste, **nenhuma** com `t.Parallel()`, cada uma materializando o grafo do validador num tempdir. O gate matava por relógio, com stack de goroutines — indistinguível de teste quebrado.
- **Correção:** a lentidão foi atacada antes de o número subir. `materializeStockFreshnessValidatorGraph` era chamada 55 vezes e cada chamada repercorria o grafo e relia cada arquivo do disco; memoizada, a suíte caiu de **692 s para 611 s**. O teto foi para 780 s (611 s + 28%, mesmo critério da calibração anterior).
- **Segunda correção, 2026-08-30: `t.Parallel()` nos 29 testes que montam a própria raiz.** A auditoria que ela exigia foi feita e é curta: `planFixtureRoot` monta a raiz por `t.TempDir()`, e `grep` nos dois arquivos devolve **ZERO** ocorrências de `Setenv` ou `Chdir` — as duas coisas que de fato compartilham estado de processo. As variáveis de pacote em volta são tabelas de fatos jurídicos inicializadas uma vez e só lidas.
- **Medido:** **692 s → 611 s → 497,8 s**, com as mesmas 19 falhas conhecidas em cada passada — zero regressão. São **28%** a menos, e a suíte volta a caber com folga no teto de 780 s do teste focado.
- **Status:** parcial — 497,8 s ainda é caro para um pacote que se toca com frequência, e o que resta está nomeado: as outras ~800 funções de teste seguem seriais, e a família `PrepareTransactionPlan*` recomputa o fingerprint do grafo duas vezes por teste (`plan.go:185` e `:251`). A segunda chamada é guarda de TOCTOU deliberada — "o grafo mudou durante o plano?" — e memoizá-la seria afrouxar a verificação, então ela fica.

## BUG-187 — quem mexe no grafo do validador não era cobrado a reatestar
- **Data:** 2026-08-30
- **Severidade:** GRAVE — travava TODO deploy
- **Sintoma e causa raiz, medidos:** `ingest-v2-stock` recusa publicar quando o atestado do grafo não descreve a fonte, e a cobrança só acontecia dentro do `deploy-publico`, no passo 0a. Cinco incidentes (`eedb3edf`, `896d83ae`, `612b687c`, `63ed4b2d` e o deploy das 21:34 de 29/08), e dos dez commits que tocaram `internal/v2ingest` naquele dia, **seis eram unicamente re-atestação**. A armadilha que faz reincidir: o grafo é a **closure transitiva de import** (96 pacotes), não o diretório — o deploy de 21:34 morreu por um commit em `structureddata`, `legalfacts` e `legalcorpusindex`.
- **Correção:** `tools/check-atestacao-grafo-no-commit`, ligado ao pre-commit, lê só o índice do commit e cobra o atestado junto. Custo zero quando não há Go de produção no commit. `-selftest` com 10 vereditos, detector visto vermelho e verde, e provado contra o caso real de `1ee69ce8`.
- **Status:** FECHADO

## BUG-C8 — 21 ocorrências-página atribuíam artigo a norma que não o tem
- **Data:** 2026-08-29 (crítico nº 8 do goal)
- **Severidade:** CRÍTICO — é a única classe que o CLAUDE.md marca como P1 permanente sob a ética da OAB
- **Sintoma e causa raiz, medidos:** nada conferia se o artigo que uma página atribui a uma norma EXISTE naquela norma. `internal/legalfacts` pareia o dispositivo com a referência de norma mais próxima dentro de 30 bytes, `lexml.BuildURNComponent` monta a URN com o que vier, e o resultado sai no `legislationIdentifier` do JSON-LD e no href do corpo. Varredura dos 10.345 HTMLs: 7.444 emissões de componente de artigo caem em diploma coberto pelo corpus e **14 pares distintos (21 ocorrências-página)** afirmam artigo que o diploma não tem — nenhum é lacuna do corpus. Entre eles, `urn:lex:...13105!art543c` em 8 páginas de `/jurisprudencia/` (o art. 543-C é do CPC/1973, atribuído ao CPC/2015) e `1988!art459` (o art. 459 é da CLT, atribuído à Constituição).
- **Correção:** `internal/legalcorpusindex` liga `data/legal-corpus/` à URN de componente e responde `ArtigoInexistente(chave)`; a tabela é gerada por `cmd/generate-legal-corpus-article-index` porque `structureddata` não faz E/S e o render não pode abrir 29 arquivos por página em 10.000 páginas; `TestIndiceBateComOCorpusReal` reconstrói o índice a partir do corpus e compara, para a tabela não envelhecer em silêncio. `structured_data.go:813` e `:979` suprimem a atribuição inexistente em vez de emitir URN errada.
- **Status:** fechado (commit `1ee69ce8`), **verificado em produção**: varredura dos 10.344 HTMLs servidos após o deploy de 2026-08-30T02:37Z devolve 20.418 emissões de URN e **zero** nas oito famílias erradas; `./tools/go-modern run ./cmd/check legal-citation-attribution` → `pass`.
- **Lição:** citação legal mal atribuída não tinha detector porque ninguém tinha ligado o corpus à URN — a medição não faltava por ser difícil, faltava por não existir a ponte entre dois artefatos que já estavam no repositório.

## BUG-188 — 27 testes de contrato vermelhos e nunca vistos, no pacote que guarda o próprio contrato
- **Data:** 2026-08-30
- **Severidade:** GRAVE
- **Sintoma e causa raiz, medidos:** `internal/contract/misc` (26) e `internal/contract/public` (1) falham. São contratos textuais e de artefato que envelheceram sem ninguém executar: portfólio de aéreo/seguros/telecom contra shards finalizados, autenticadores de host da esteira de escrita, inventário de lotes, oráculo morfossintático PT-BR, isolamento de `CODEX_HOME` no launcher, `ionice -c2 -n7` em `run-heavy-throttled`. A mesma invisibilidade do BUG-185: commit acima de seis pacotes pula o teste focado em silêncio, e commit de dado não roda teste Go.
- **Três consertados nesta passada, e os três eram o TESTE, não o documento:**
  1. `TestGoalContractsFirstLineForGoalModeDoesNotAllowStopping` exigia a ordem na PRIMEIRA linha; o `GOAL.md` ganhou acima dela o cabeçalho da ordem mais recente do dono — o mecanismo que o próprio documento declara para se atualizar. O teste passou a exigir a ordem NO DOCUMENTO e a abertura a não autorizar parar.
  2. `TestWhatsAppCTAContractExistsButDoesNotBypassLegalQuality` exigia `{unique_intent_id}` na mensagem que o VISITANTE envia pelo WhatsApp. O commit `460de09b` tirou o token de propósito ao trocar o template robótico por "PT-BR de gente": slug interno na mensagem do cliente é falha P0. O teste passa a exigir `{path}` e `{title}` e a REPROVAR se o jargão voltar.
  3. `TestCheckpointCarriesNextExecutionPlanInsteadOfStopping` cobrava um checkpoint com plano de continuidade, e o mais recente era de 2026-07-23. O checkpoint desta sessão foi escrito com o plano em ordem de valor.
- **E um consertado no código:** `internal/goalbaseline` tratava a ausência de `data/editorial/scaled_content_release_verdict.jsonl` como falha de leitura. O artefato é produzido pela promoção de release, que a publicação transacional bloqueia por padrão — ele não existe no HEAD nem no disco. Dois leitores precisavam da correção, e o segundo só apareceu depois de o primeiro ser corrigido. Ausência agora é zero, que é a verdade.
- **O que a correção do `goalbaseline` revelou, e é o melhor argumento a favor do gate:** com a ausência tratada como erro, `collectPostCommitScaleGateLayers` retornava cedo e as validações de coerência de contagem **nunca rodavam**. Corrigida a leitura, elas rodaram e acusaram seis divergências reais de dados — `openai_batch_request_count_bad: requests=10000 total=7891`, `release_evidence_count_bad: release_evidence=590 release_transaction=209 total=7891`, `scale_content_count_bad: public_prose=7959 scaled_verdict=0`, `p0_blocker_delta_counts_bad`, `quality_counts_bad: quality=7959 total=7891 batch=0` e `public_flags_open: goal-baseline-20260618`. Um erro de leitura estava escondendo divergência de contagem: dois testes de `internal/goalbaseline` passaram a reprovar, e o gate de baseline me obrigou a olhar em vez de deixar passar.
- **Três fechados em 2026-08-30, e um deles era REGRESSÃO de verdade:**
  1. **`run-heavy-throttled` tinha perdido a despriorização de I/O por padrão.** Ao parametrizar classe e nível do `ionice`, o default da CLASSE ficou VAZIO — e o bloco de aplicação é `if [ -n "$ionice_class" ]`. Comando pesado voltou a disputar disco em pé de igualdade com quem trabalha ao lado, que é exatamente o que o wrapper existe para impedir. Default de volta em `-c2 -n7`, parametrização mantida. O gate cobrava esse literal desde que nasceu, e ninguém o executava.
  2. `profile-contract-tests` exigia `go run ./cmd/profile-tests`; o wrapper passou a usar `run-go-cmd-cached`, e a forma direta é RECUSADA no repositório com `missing: cached_runner`. O teste prescrevia voltar ao caminho que o projeto bloqueia.
  3. `start-ai-terminal` renomeou a variável de alvo de `$session` para `$tmux_session_target`; o teste casava o literal antigo. Passou a exigir a semântica por expressão.
  E a guarda do `exec` no mesmo teste tinha um **falso positivo**: procurava `exec "$@"` no arquivo inteiro e acusava a supervisão, que lança o filho como `/bin/sh -c '…; exec "$@"' &` — subshell em background, onde o pai segue com `trap cleanup_lock EXIT` intacto. Agora olha linha a linha e só reprova quando `exec` abre a linha.
- **Status:** parcial — 26 continuam vermelhos (23 em `contract/misc`, 1 em `contract/public`, 2 em `goalbaseline`), nomeados em `data/ops/testes_vermelhos_conhecidos.json`. O gate reprova regressão nova **e baseline inflado**: foi ele que exigiu tirar estes três da lista assim que passaram a passar.
- **Próximo passo nomeado:** reconciliar os contadores do baseline do goal — o denominador `total=7891` não bate com `public_prose=7959` nem com `quality=7959`, e `requests=10000` é um número redondo demais para ser medição.

## BUG-189 — re-triagem dos 9 CRÍTICOS VIVOS do briefing, com o comando de cada veredito
- **Data:** 2026-08-30
- **Severidade:** meta — nenhum sobreviveu à medição
- **Por que existe:** o briefing da caça lista nove críticos medidos em 2026-08-29 e o repositório se moveu desde então. O passo zero do método manda re-triar antes de corrigir, e "o que cair vai para os refutados com o commit que fechou". Os nove foram medidos um a um:

| # | enunciado de 29/08 | comando | veredito |
|---|---|---|---|
| 1 | `cmd/build public` reprova: 261 achados em 29 rotas | `./tools/go-modern run ./cmd/build public` | **MORTO** — `EXIT=0`, `generated_pages=10126 indexable_pages=10341`, zero achados |
| 2 | FAMÍLIA-A: cobertura publica `universo_urls=18731` | última linha de `data/ops/edge_cache_coverage.jsonl` | **MORTO** — `universo_urls=10302`, `cobertura_pct=100.0` |
| 3 | CVE GO-2026-5932 viva em x/crypto v0.55.0 | `go list -m -versions golang.org/x/crypto` + evidência de govulncheck | **REFUTADO** — `reachable_call: false`, `upstream_has_no_fix: true`, `fixed_version: ""`, e a lista de versões **termina em v0.55.0**: a prescrição "subir a versão" é inexecutável. A exceção em `tools/sca/osv-scanner.toml:26` carrega o fundamento medido ponto a ponto, e o `go_mod_sha256` da evidência bate com o `go.mod` de hoje |
| 4 | `go vet` falso-verde por VetxOnly; `go-build-check:46` usa `./...` | leitura de `tools/go-build-check:46-58` | **FECHADO** — escopo explícito e cache-buster por nonce (BUG-057/BUG-107) |
| 5 | googlebot-smoke valida o próprio cache | experimento controlado com cache envenenado | **REFUTADO** (BUG-C5) — `exit=0` em 50,9 s com o cache adulterado |
| 6 | public-release-transaction: 59.388 erros de dois campos | `./tools/go-modern run ./cmd/check public-release-transaction` | **FECHADO nesta sessão** — devolve `pass`. Não eram os dois campos: eram 9.918 `sitemap_sha256_mismatch`, e a causa era o detector (BUG-C6) |
| 7 | `GOAL.md` declara `published_manifest=0` como regra vigente | `./tools/check-contrato-vs-medicao` | **REFUTADO** (BUG-C7) — as seis ocorrências estão escudadas por rótulo de contador vencido |
| 8 | autolinker parte citação com sufixo: 225 href em ~199 páginas | varredura dos 10.344 HTMLs servidos | **CORRIGIDO e verificado em produção** (BUG-C8) — 20.418 emissões de URN, **zero** nas oito famílias erradas |
| 9 | `ValidateEditorialBody` é código morto | `grep -rn ValidateEditorialBody` | **FECHADO** — ligado por `validaCorpoPublicadoContraPromessa` (`internal/checks/checks.go:6630`, BUG-117) |

- **Status:** fechado — a lista de críticos do briefing não tem sobrevivente medido. O trabalho aberto do repositório está nos BUG-185/186/188, cada um com a fatia fechada e a fatia restante nomeada no baseline de vermelhos conhecidos.
- **A lista "DEPOIS" do mesmo briefing, triada na sequência:**

| enunciado | comando | veredito |
|---|---|---|
| 103 rotas sem acento visível | varredura do `<main>` dos 10.344 HTMLs servidos, procurando qualquer caractere acentuado em corpo com ≥400 caracteres | **MORTO** — **zero** páginas sem acento |
| 13 binários ELF rastreados, ~448 MB | `git ls-files \| xargs file --mime-type \| grep x-executable` | **VIVO e PIOR: 21 arquivos, 696 MB** — corrigido no BUG-078 desta mesma passada |
| `Last-Modified` = mtime do build mata o 304 | `internal/build/build.go:313` e `internal/httpserver/conditional.go` | tratado — o comentário do código descreve a correção do validador condicional |

- **Lição:** âncora de briefing envelhece em horas neste repositório, e re-triar custa minutos contra a delegação inteira que um enunciado morto consome. Foi a mesma lição do BUG-C4, e agora com nove casos em vez de um. E o inverso também aconteceu: um item da lista secundária estava **pior** do que o enunciado dizia, e só a re-medição mostrou.

## BUG-190 — `"al."` de "et al." fundia toda frase terminada em palavra com "-al", e a negação seguinte vazava para trás
- **Data:** 2026-08-30
- **Severidade:** CRÍTICO — corrompia o veredito de fato jurídico do acervo inteiro
- **Sintoma:** 19 testes de `TestCurrentLegalFacts*` vermelhos, com fixturas **derivadas da própria regra** sendo rejeitadas — o que é logicamente impossível se o detector estiver certo. Foi essa impossibilidade que apontou o caminho.
- **Causa raiz, isolada em quatro medições:**
  1. `aereo02CurrentVisible` monta uma frase por grupo da regra, então a fixture satisfaz todos os grupos por construção. Ainda assim, dois grupos não casavam: `"chargeback e contestacao contratual"` e `"abatimento proporcional"`.
  2. Isoladas, as duas frases casavam (`true`). No texto completo, não.
  3. `semanticDeclarativeLegalFactClauses("Abatimento proporcional. Nao fixa uma porcentagem nacional automatica.")` devolvia **UMA** cláusula, com os tokens das duas frases juntos — e os detectores avaliam negação POR CLÁUSULA, então a negação da segunda frase **negava a afirmação da primeira**.
  4. `ptbrtext.Sentences` era a origem: separava `"Primeira frase completa aqui. Segunda frase completa aqui."` em duas, mas **não** separava quando a frase anterior terminava em `-al`.
- **A causa exata:** `shouldJoinNextSentence` decidia por `strings.HasSuffix` puro contra a lista de abreviaturas, e a lista tem **`"al."`**, de "et al.". `HasSuffix` não conhece fronteira de palavra, então `proporcional.`, `contratual.`, `judicial.`, `legal.`, `social.` e `processual.` casavam também. Em português jurídico, palavras em "-al" são onipresentes.
- **Correção:** a abreviatura só junta quando **é a palavra** que fecha o trecho — o caractere imediatamente anterior tem de ser separador, não letra nem dígito. `et al.`, `art.`, `n.`, `Dr.` continuam juntando; `proporcional.` não.
- **Medido:** `internal/v2ingest` de **19 para 11** falhas — oito testes de fato jurídico passaram a passar, entre eles `TestCurrentLegalFactsAereo02/03/05`, `TestTema987GoPythonParity` e `TestTema987SemanticMatrix` —, **zero regressão**: o gate de baseline só acusou lista inflada, que é o sinal de dívida paga. `ptbrtext`, `quality`, `render` e `seo` verdes.
- **★ O QUE ELA NÃO FEZ, medido no re-ingest logo depois:** o acervo saiu com **7.968 aceitas e 2.258 rejeitadas — exatamente o mesmo de antes**. A correção destravou oito testes, que operam sobre fixturas sintéticas, e **não** mudou o veredito de uma única página real. As 2.258 rejeições vêm de outras razões — fonte ausente, campo obrigatório, `official_sources_insufficient` —, não da contaminação de negação. Registrar isso importa: seria fácil, e falso, atribuir a esta correção um ganho de produto que ela não produziu.
- **O ganho real é de outra natureza, e continua valendo:** o detector deixou de dar falso negativo sobre prosa correta, o que previne a rejeição de texto que ainda vai ser escrito, e oito guardas de fato jurídico voltaram a valer — elas estavam vermelhas, logo não guardavam nada.
- **Status:** fechado quanto à causa. Os 11 restantes são outras famílias, e seguem no baseline.
- **Lição:** fixture derivada da própria regra sendo rejeitada é impossibilidade lógica, não teste chato — e é o sinal mais barato que existe de que o defeito está no detector. Foram quatro medições do sintoma até a linha, e nenhuma delas exigiu adivinhar.

## BUG-191 — 30 requisitos de fonte exigiam deep-link que NÃO RESOLVE, e o repositório recusava páginas corretas por isso
- **Data:** 2026-08-30
- **Severidade:** CRÍTICO — `current_legal_fact_source_missing` sobre página que citava a fonte certa
- **Como apareceu:** dos 19 testes de fato jurídico vermelhos, dez acusavam fonte ausente. Ao ler o estoque, as páginas **tinham** a fonte — na outra grafia do Planalto. O gate exigia `l10406compilada.htm#art207`; a página citava `l10406.htm#art207`.
- **A medição que decidiu, feita nos documentos vivos:** `l10406compilada.htm` traz **11 âncoras, 5 de artigo**, e `art207`, `art932` e `art1245` **não estão lá**; `l10406.htm` traz **6.421 âncoras, 3.940 de artigo**, e as três estão. Seguir o gate produziria link para uma âncora que não existe — o oposto do que a exigência protege.
- **A varredura sistêmica, feita depois:** extraí do código de produção todos os pares (documento, fragmento) exigidos, baixei os **14** documentos e conferi âncora a âncora. **Cinco documentos** exigiam fragmento inexistente, somando **24 requisitos**: `del2848compilado.htm` (12 de 12), `del3689compilado.htm` (8 de 17), `l8078compilado.htm` (2 de 2), `l11340.htm` (1, e o documento tem **zero** âncoras) e `l9430.htm` (1).
- **Correção, por caso e não em bloco:** 30 requisitos foram reapontados para a grafia que **tem** a âncora — medido: `del2848.htm` resolve 12/12, `del3689.htm` 8/8, `l8078.htm` 2/2 — e o fragmento de `l11340.htm#art16` saiu, porque a Lei Maria da Penha não tem âncora em grafia nenhuma. O auditor Python (`tools/audit_v2_pages.py`) foi alinhado no mesmo commit, e `TestTelecomCrossRuntimeSemanticContract` provou que os dois runtimes voltaram a concordar.
- **★ Uma correção minha foi refutada pela própria medição:** eu havia removido `#art44` de `l9430.htm` por não achar a âncora. Re-medindo com mais cuidado, ela existe como **`art44.`** — com ponto final. Restaurada. Ausência de âncora se afirma depois de olhar as variantes de grafia, não na primeira busca exata.
- **E `telecomSourceForKind` comparava URL por igualdade de BYTES** em produção — caminho que a correção do BUG-120 não alcançou. Passou a aceitar a outra grafia do mesmo arquivo, com uma equivalência **estreita**: as duas URLs têm de ser idênticas exceto pelo nome do arquivo. Duas versões mais largas foram refutadas pelos **366 decoys** dos testes adversariais de identidade, cada uma na primeira execução — `planaltoPartMatchesSource` deixou passar fragmento e query, e `mesmoAtoEDispositivoNoPlanalto` deixou passar `?decoy=1` e host em maiúsculas.
- **Medido:** `internal/v2ingest` de **19 para 7** falhas ao longo da frente (com BUG-190 junto), zero regressão sobrevivente.
- **★ E o gate apanhou um FLAKY no caminho:** `TestCanonicalStockReadLeaseExecFilesSurviveAbruptOwnerExit` entrou no baseline numa execução e passou na seguinte, e foi o veredito "baseline inflado" que denunciou. Ele fica registrado como intermitente — teste que ora passa ora falha polui qualquer baseline e merece frente própria.
- **★ E o efeito no ACERVO só apareceu depois de corrigir o DEPLOY.** Na primeira publicação depois desta correção o deploy imprimiu `ingest dispensado (contentstore mais novo que os shards)`: ele decidia reingerir só pelo mtime do shard, e o estoque não tinha mudado — o acervo seguiu servindo o veredito do validador **antigo**. Com o gatilho corrigido para olhar também o atestado do validador, o re-ingest rodou e mediu: **7.968 → 7.971 aceitas**, e `current_legal_fact_source_missing` caiu de ~140 para **75** ocorrências.
- **Status:** fechado quanto à causa. Os **6** restantes são testes "Live" que leem o estoque real e cobram fonte que a página de fato não tem — dado editorial, não detector.

## BUG-192 — a identidade do responsável técnico estava escrita no código, em 13 arquivos
- **Data:** 2026-08-30
- **Severidade:** GRAVE — é regra explícita do contrato ("sempre via `content/site.json`, nunca hardcoded")
- **Sintoma e causa raiz, medidos:** `TestEditorialIdentityComesFromSiteConfigNotRuntimeHardcode` estava vermelho e denunciava um arquivo por execução. Varrido o repositório: **13 arquivos de produção** traziam o nome do responsável técnico e/ou a inscrição por extenso — seis com **valor real** (`internal/factorymetrics` com três constantes, `internal/gatescalebench`, `cmd/fiscalize` com três constantes, `cmd/preview-v2-page`, `cmd/report-cta-coverage`, `cmd/generate-agent-skill-archives`, este último injetando o valor **dentro de um artefato distribuído**, o plugin público) e sete apenas em comentários — que o gate também lê, com razão: comentário que soletra a identidade é a mesma fonte de divergência.
- **Correção:** `content.LoadEditorialIdentity` lê **só** os três campos de `content/site.json`. Ela existe em vez de `LoadRepository` porque carregar o repositório inteiro para pegar três campos custa caro e **falha onde o repositório completo não existe** — a fixture de `internal/factorymetrics` monta um tempdir com meia dúzia de arquivos, e `LoadRepository` recusava com "file does not exist". Identidade incompleta vira **erro**, nunca string vazia: página assinada por ninguém é pior que build quebrado.
- **Os comentários foram reescritos preservando o sentido** — "OAB/UF NNNN" no lugar da inscrição, "responsável técnico" no lugar do nome — e o corpus sintético do benchmark ganhou um autor sintético, que é o que ele sempre deveria ter tido.
- **★ E a primeira tentativa continuou vermelha por causa do meu próprio comentário:** eu havia escrito o nome dentro da explicação da correção. O detector varre o ARQUIVO. É a terceira vez nesta sessão que um comentário derruba o gate que ele explica.
- **Medido:** `internal/contract/misc` de **23 para 22** falhas; `factorymetrics`, `content`, `accessibilityaudit`, `render`, `structureddata`, `pagemarkdown`, `httpserver` e `gatescalebench` verdes. `grep -rl 'Rafael Toledo\|227191' --include=*.go internal/ cmd/` (fora de teste) → **zero**.
- **Status:** fechado

## BUG-193 — o veredito dos nove críticos do briefing existia só em prosa
- **Data:** 2026-08-30
- **Severidade:** MÉDIO — não quebra nada, e obriga cada leitor a acreditar no relato
- **Sintoma:** o BUG-189 registrou a re-triagem dos nove "CRÍTICOS VIVOS" do briefing com o comando de cada veredito, e nenhum sobreviveu à medição. Mas o registro é **texto**: quem quisesse conferir teria de repetir as nove medições à mão, e cada sessão nova recomeçaria a discussão do zero. O próprio contrato manda que todo número venha com o comando — e o placar da caça era a única coisa que não vinha.
- **Correção:** `tools/check-criticos-do-briefing-20260829` re-mede os nove e devolve, para cada um, **verde/vermelho com o número de agora**. Ligado ao `tools/pre-voo` no modo leitura (~5 s); `--completo` acrescenta `cmd/build public` e `public-release-transaction`, de ~1 min cada.
- **Medido no modo completo, em 2026-08-30:**

| # | enunciado | medição de agora |
|---|---|---|
| 1 | `cmd/build public` reprova, 261 achados | `exit=0 achados=0` |
| 2 | `universo_urls=18731` | `universo_urls=10312` |
| 3 | CVE alcançável em x/crypto | `alcancaveis=0`, sem correção upstream, evidência cobre o `go.mod` atual |
| 4 | `go vet` falso-verde por `./...` | `padrao_full_tree=False cache_buster=True` |
| 5 | googlebot-smoke valida o próprio cache | caminho fixo ausente; refutado por experimento (BUG-C5) |
| 6 | public-release-transaction, 59.388 erros | `exit=0 sitemap_mismatch=0 campos_do_enunciado=0` |
| 7 | contrato × medição divergem | `exit=0`, o contrato bate com o manifesto |
| 8 | autolinker emite URN inexistente, 225 href | **10.354 páginas varridas, 0 emissões erradas** |
| 9 | guarda de ética no corpo é código morto | `chamadores_de_producao=1` |

- **Status:** fechado
- **Lição:** placar que só existe em prosa não é verificável, e por isso volta. O mesmo padrão que o repositório usa para dado (`check-contrato-vs-medicao`) faltava para o próprio catálogo de bugs.

## BUG-201 — o baseline do /goal exigia que o projeto NÃO tivesse saído da linha de partida
- **Data:** 2026-08-30
- **Severidade:** GRAVE — cinco testes vermelhos, e o vermelho significava "a missão está indo bem"
- **Sintoma:** `TestGenerateCapturesCurrentOperationalBaselineLayers`, `TestGenerateCapturesPostCommitScaleGateBaselineLayers`, `TestGoalBaselineCapturesLiveGoalStartingState`, `TestGoalBaselineValidationRejectsMissingRunID` e `TestGoalBaselineCapturesOperationalMachineReadableLayers` — os cinco na mesma lista de cinco issues.
- **Causa raiz:** `goalbaseline.Validate` codificava o mundo **pré-publicação** como invariante, e os testes rodam `Generate()` contra o repositório VIVO. `TestGoalBaselineCapturesLiveGoalStartingState` é o caso puro: exigia `current=0`, `deficit=10000`, `drafts=300`, `expansion=9700`. Medido hoje: **10.126 páginas indexáveis, déficit ZERO — a meta P0 foi batida**. O teste só podia passar enquanto a missão falhasse.
- **★ E o registro que sustentava as igualdades NUNCA foi uma medição.** O único registro commitado em `data/ops/goal_baseline.jsonl` (`goal-baseline-20260702`) traz **10.000 em todos os campos**. No MESMO commit que o gravou (`34d6df3d`, 2026-07-02), `authorial_mass_drafts.jsonl` tinha **300 linhas**. O 10.000 veio de `data/ai/openai_review_batch_requests.jsonl`, um lote histórico one-shot de 10.000 linhas fixas, e o resto foi ajustado para satisfazer o validador. Igualdade entre ledger congelado e corpus vivo só vale em registro fabricado.
- **E uma das igualdades contradizia o coletor do PRÓPRIO pacote:** `collectScaledContentReleaseVerdictLayer` documenta que o veredito "só existe depois de uma promoção que a publicação transacional bloqueia por padrão — ausência é zero, não erro", e `Validate` exigia que esse zero fosse 7.971. Metade do pacote chamava zero de normal, a outra metade reprovava.
- **Correção — bem-formação fica, estado-do-mundo sai:** requisição do lote OpenAI passa a exigir `> 0` e `resultados <= requisições`; evidência de release vira a cadeia de continência `transação <= evidência <= corpus` (209 <= 590 <= 7.971); prosa e veredito viram `candidato <= corpus` e `veredito <= candidato`; vetor de qualidade vira `<= corpus`. E "nenhuma flag pública aberta" dá lugar à **coerência de artefato**: nenhuma rota se declara publicável sem linha no `published_manifest` (10.126 <= 10.126 hoje). Quem abre as flags é `authorial_mass_manifest_transaction_rehearsal.jsonl`, com 10.126 registros — as páginas que o portal serve. Os outros nove ledgers varridos por `addPublicFlags` seguem todos em zero.
- **E o teste do resíduo anti-molde media o universo errado:** comparava `total de drafts − prontos`, misturando o ledger de drafts (7.971) com o de vetores (7.959) e produzindo 2.102 onde o real é **2.090**. A igualdade com UM gate também era forte demais: os 2.090 em revisão se distribuem em 2.082 de ngram boilerplate, 3 de boilerplate público conhecido e **5 de refinamento de title/meta — estes com a razão em `required_fixes`, não em `template_issue_codes`**, e por isso invisíveis à regra antiga. Verificado um a um: nenhum dos 2.090 ficou sem razão declarada, que era o defeito que valia guardar.
- **E o helper do teste morria em I/O onde o coletor declara ausência legítima:** `assertBaselineJSONCountForTest` abria `scaled_content_release_verdict.jsonl` e reprovava com "no such file or directory" — o estado NORMAL do repositório. Nasceu `assertBaselineJSONCountAllowingAbsentForTest`, usado só onde o coletor documenta a ausência.
- **Dívida nomeada que ficou visível:** o join por `unique_intent_id` entre drafts e vetores de qualidade mostra **234 drafts sem vetor e 222 vetores sem draft vivo**. É lag real de esteira, não invariante de estrutura.
- **Status:** os cinco testes ficaram verdes; a divergência 234/222 fica aberta com número.

## BUG-202 — a crase de markdown reprovava contrato intacto, e a redação melhorada era cobrada de volta
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — vermelho permanente sem defeito por trás
- **Sintoma:** `TestOperationalContractsRequireParallelCodexCoordinationWithoutPassiveWaiting`: `AGENTS.md missing parallel Codex coordination token "analise_comando_ativo exige pid, …"`.
- **Causa raiz, dupla:**
  1. **Markup lido como contrato.** O token cita identificadores (`analise_comando_ativo`, `lock_scope`, `budget_ms`) e escrevê-los como código é a formatação CERTA em markdown. Medido: **três dos quatro documentos** usam a crase (AGENTS.md, `docs/P0_OPERATIONAL_RUNBOOK.md`, o contrato do ledger) e só o GOAL.md ficou em texto plano. O requisito está intacto nos quatro. Consertado o detector, com normalização estreita (remove a crase e nada mais) e só nessa varredura — a segunda cobra a frase do check COM crase, porque ali a formatação é parte da exigência.
  2. **Redação melhorada cobrada de volta.** O token exigia "sem budget, sem stop_condition"; `bb9b33db` (2026-07-04) tornou a regra mais precisa — "sem artifact_claim com budget_ms/stop_condition" — porque o mesmo parágrafo passou a dizer que esses campos pertencem ao `artifact_claim`. De novo três dos quatro documentos já tinham a redação nova, e o **GOAL.md é que alcançou os outros**, não o contrário.
- **Status:** fechado — o teste ficou verde e os quatro documentos passaram a dizer a mesma coisa.

## BUG-203 — a camada de evidência de fonte oficial estava 26 dias e um schema atrás
- **Data:** 2026-08-30
- **Severidade:** GRAVE — 325 erros de forma sobre 64 registros; a camada inteira ilegível
- **Sintoma:** `TestOfficialSourceURLLiveEvidenceStaysBlockedMetadataOnly`: `LoadRecords failed: official_source_url_live_evidence_schema_drift: … 325 mensagens de forma colapsadas … sobre 64 registros`.
- **Causa raiz:** `data/source-registry/official_source_url_live_evidence.jsonl` estava numa geração anterior do schema — **34 campos que o loader não conhece** (`live_recheck_id`, `match_method`, `reference_keys`…) e **15 que ele exige e não estavam lá** (`etag_hash`, `x_robots_tag`, `run_date`, `freshness_ttl_days`…). E a cadeia toda estava velha: o inventário tinha `run_date` de **2026-08-04** com 563 URLs, enquanto o acervo já é de 10.126 páginas.
- **Correção pela rota que a própria mensagem de erro prescreve**, sem rede e sem credencial: `generate-official-source-url-inventory` (563 → **6.421** URLs), `generate-official-source-url-live-metadata-attempts` (6.421, `live=false`) e `generate-official-source-url-live-evidence` (6.421). Os registros de tentativa nascem declarando que **não houve sondagem**, que é a verdade — não é dado fabricado, e `publication=false` em todas as três camadas.
- **Pendência honesta que fica:** as 6.421 tentativas de metadata ao vivo (`--live`, HEAD sem corpo) não foram executadas nesta sessão. A camada declara isso; nenhuma linha afirma sondagem que não houve.
- **Status:** fechado — o teste ficou verde.

## BUG-204 — o oráculo PT-BR era cobrado numa versão anterior à DEC-018, e um gate exigia a palavra que outro proíbe
- **Data:** 2026-08-30
- **Severidade:** GRAVE — dois gates do mesmo repositório em contradição direta
- **Sintoma:** `TestPTBRMorphsyntaxOracleUsesRealSpacyAndStanzaModels`: `missing contract marker "deterministic_stride_plus_diagnostics"`.
- **Causa raiz:** três marcadores congelados antes de mudanças que **fortaleceram** o contrato. `2c7be1b4` (2026-07-11) trocou a amostragem por stride pela **cobertura integral** do corpus com spaCy, mantendo o stride só para o diagnóstico do Stanza. `a3af2796` (2026-07-09, **DEC-018**) tirou o oráculo de sample-grade e a razão da indisponibilidade do NER deixou de ser genérica para nomear versão e fato — o catálogo oficial de modelos pt do Stanza 1.13.0 não traz processador de NER.
- **★ E o pior marcador estava ATIVAMENTE CONTRADITÓRIO:** o teste exigia `blocked_sample_oracle_with_stanza_ner_gap_no_publication`, com a palavra "sample" — e `internal/ptbrmorphsyntaxoracle/oracle.go:250` **REPROVA** qualquer `coverage_status` que contenha esse token (`ptbr_morphsyntax_release_sample_status`). Foi por isso que `2c7be1b4` trocou `stanza_sample_cross_check` por `stanza_diagnostic_cross_check`, e o script documenta o motivo no próprio corpo. Um gate exigia a palavra que o outro proibia.
- **Status:** fechado.

## BUG-205 — três contagens congeladas transformavam acervo crescendo em regressão, e um filtro de nome cegava o teste para página escrita
- **Data:** 2026-08-30
- **Severidade:** GRAVE — o teste acusava ausência de páginas que existem
- **Sintoma:** `TestTelecomPortfolioCurrentRGCCompletion` e `TestInsuranceAreaSourcesAndRunnableQueueExcludeRevokedCivilCodeChapter`.
- **Causa raiz, três camadas:**
  1. **Igualdade onde o vizinho já era piso.** `currentHintCount != 69` reprovava as 86 intenções que hoje citam a Resolução Anatel 765/2023 — a norma **vigente**; a linha imediatamente abaixo (`completedCurrentHintCount < 25`) já era piso. O mesmo em seguros: `assertCompletedDPVATMigrationShard` exigia 13 exatos enquanto o bloco 150 linhas acima, sobre a MESMA família, já dizia "perder uma delas é o defeito; ganhar vizinhas novas, não".
  2. **O nome do lote guarda a CAMPANHA, não a área.** O leitor globava `telecom_energia-*.jsonl` e por isso acusava `tel-golpe-falsa-central-operadora`, `tel-instalacao-danos-imovel` e `tel-venda-loja-terceirizada-responsabilidade` de não terem página. As três existem — em `telecom_energia-r01`, `telecom-r03` e `telecom-r04` —, e o acervo ainda tem `energia-r02`/`energia-r03` escrevendo na mesma área. A régua deixou de ser o nome e passou a ser a **pertinência**: é página de telecom o registro cuja intenção está no portfólio de telecom_energia. A checagem de duplicata continuou de pé e agora vale sobre o acervo inteiro.
  3. **Página pendente confundida com regressão.** O shard DPVAT tem 13 linhas e o portfólio 15: `seg-dpvat-diferenca-invalidez-judicial` e `seg-dpvat-negado-administrativo-judicial` estão a redigir (BUG-200). Exigir igualdade transformava trabalho A FAZER em regressão do trabalho JÁ FEITO.
- **Status:** fechado.

## BUG-206 — 20 intenções de telecom citavam o diploma inteiro onde a regra está num artigo determinado
- **Data:** 2026-08-30
- **Severidade:** GRAVE — a página cita a fonte que a dica aponta
- **Sintoma:** `tel-multa-fidelidade-quando-vale: corrected Telecom-02 source map is missing "cdc-art-46"`.
- **Causa raiz:** as 11 intenções do mapa Telecom-02 somavam **20 dicas ausentes**. Não é formalidade: `cdc-8078-1990` manda o leitor ao código inteiro; `cdc-art-46` o manda à regra de que cláusula que ele não teve chance de conhecer não o obriga — que é o fundamento para contestar a multa de fidelidade. Mesma coisa em seguros: `cdc-lei-8078-1990-art-39` é a lista de treze práticas abusivas, `cdc-art-39-i-venda-casada` é a venda casada, que é o assunto da página.
- **★ E três nomes exigidos NUNCA existiram no catálogo:** `cc-art-6`, `cc-art-1792` e `cdc-art-49`. Não se criou entrada nova para casar com a tabela — dica que não resolve some do espelho em `ops/relaunch-writing.sh` e derruba o lote inteiro no emit-clean, em silêncio (BUG-196 por outra porta). A tabela é que passou a apontar para as chaves reais: `cc-2002-art-6`, `cc-2002-art-1792` e `cdc-art-49-direito-arrependimento`.
- **Correção:** `tools/generate-portfolio-hint-especifico-20260830`, que confere cada chave nova contra o catálogo antes de escrever, nunca remove a dica genérica, nunca acrescenta dica que a tabela de proibidos veda, e escreve linha a linha para não gerar churn no portfólio.
- **Medição colateral que fica registrada:** o portfólio usa **5.928 dicas distintas e 2.304 delas não são chave do catálogo**, alcançando 3.642 intenções. Boa parte é rótulo de fonte ("Polícia Federal", "meu.inss.gov.br"), não identificador resolvível — mas o número merece apuração própria.
- **Status:** fechado.

## BUG-207 — o recibo da política de termos estava 46 dias velho contra um TTL de 30
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — o gate de demanda reprovava por frescor, não por conteúdo
- **Sintoma:** `TestGeneratePortfolioWave3RejectsSourceHintsWithoutDurableDemandEvidence`: `demand_terms_decision_source_receipt_stale: … age=1106h45m18s max=720h0m0s`, em três recibos.
- **Causa raiz:** `MaxSourceReceiptAge` é de 30 dias (`internal/demandtermsdecision/evidence.go:21`) e a captura da página de termos do CKAN do STJ era de 2026-07-15. A **decisão** em si não venceu (`expires_at: 2026-10-15`); o que venceu foi a cópia datada da política que a sustenta.
- **Correção:** `./tools/capture-demand-terms-policy-evidence --timeout 20s` — 3 recibos, `checked_at=2026-08-30T12:53:09Z`, `publication=false`. Rede só contra a fonte oficial, com o UA próprio do capturador (`PortalJuridico-DemandTermsEvidence/1.0 (+internal-policy-audit; no-publication)`), sem cópia de corpo. A impressão digital da evidência mudou (`62248ffc` → `a9082b8a`): a página de termos foi de fato reeditada no período, e o ledger foi reancorado no que ela diz **hoje**.
- **Status:** fechado.

## BUG-208 — esquema DUPLICADO com decodificação estrita rejeitava o ledger vivo inteiro
- **Data:** 2026-08-30
- **Severidade:** GRAVE — a mensagem culpava o dado, e o desatualizado era o leitor
- **Sintoma:** só apareceu depois do BUG-207: `data/research/demand_expansion_opportunities.jsonl:1: strict decode: json: unknown field "semantic_compatibility_family"`.
- **Causa raiz:** `internal/portfoliowave3.demandOpportunityJSON` é uma **cópia** do esquema de `internal/demandexpansion.Record`, lida com `UnmarshalStrict`. O registro canônico ganhou a camada de compatibilidade semântica — `semantic_compatibility_family`, `semantic_compatibility_policy_version`, `semantic_compatibility_policy_fingerprint_sha256` — e a cópia não. Medido: 30 campos no wire local contra 33 no canônico e 33 no dado vivo; os três que faltavam são exatamente os três que quebravam.
- **Correção:** os três campos entraram no wire, **a estritude ficou** (é ela que pega campo inventado), e nasceu `TestDemandOpportunityWireCobreORegistroCanonico`, que compara as tags JSON dos dois structs por reflexão e **nomeia o campo faltante**. Visto vermelho antes de verde: removido `semantic_compatibility_family` de propósito, o teste acusou `nao cobre 1 campo(s) … [semantic_compatibility_family]`.
- **A direção do teste é de um lado só, de propósito:** o wire local tem de cobrir tudo o que o canônico emite; o contrário não se cobra, porque este pacote mantém campo próprio de validação — os `*bool` das flags públicas, que existem para distinguir "false" de "ausente".
- **Status:** fechado — `internal/contract/misc` fica com **1** vermelho conhecido, o BUG-200.

## BUG-209 — o ensaio de página final dizia que ZERO páginas renderizam CTA; hoje são 246
- **Data:** 2026-08-30
- **Severidade:** GRAVE — o ensaio é o que atesta a página final antes do release
- **Sintoma:** `TestPublicFinalPageRehearsalCheckPassLineIsReleaseGradeBlocked` reprovava com dezenas de `public_final_page_rehearsal_stale_or_mismatch`, um por registro.
- **Causa raiz:** o ledger `data/editorial/public_final_page_rehearsal.jsonl` estava congelado em 2026-08-29 com `cta_rendered=true` em **zero** dos 360 registros, enquanto o gerador, recalculando sobre o render de hoje, encontra **246**. É o efeito direto de `b5aef374` — "o marcador do CTA era apagado pelo sanitizador, e isso travaria a release no dia em que uma página publicasse CTA": com o marcador preservado, as páginas passaram a renderizar CTA de verdade, e o ensaio ficou descrevendo o mundo anterior ao conserto.
- **Correção:** `./tools/go-modern run -tags devcmds ./cmd/generate-public-final-page-rehearsal .` — 360 registros, `cta_rendered=246`, `final_html_ready=0`, `public_flags=0`, `publication=false`. O ensaio volta a descrever o que o renderizador FAZ, que é a única coisa que ele serve para atestar. Nenhuma flag pública abriu.
- **Status:** fechado — `internal/contract/public` saiu inteiro da lista de vermelhos conhecidos.

## BUG-210 — quatro fechos do placar apontavam para commits que nunca existiram, e a lição estava só em prosa
- **Data:** 2026-08-30
- **Severidade:** GRAVE — cadeia de prova quebrada de forma permanente
- **Sintoma:** auditoria própria do `p0_frontboard.jsonl`: `BUG-048 → 47db4fb1`, `BUG-079 → 1d9b0a94`, `BUG-134 → 47db4fb1`, `BUG-147 → a2d63d0e` — nenhum dos três SHAs existe no repositório.
- **Causa raiz:** o SHA foi **digitado**, não lido de `git rev-parse` depois do commit. E a lição já existia: o commit `54cb3856` (2026-08-29) corrigiu quatro fechos apontando para nada e escreveu o aprendizado no próprio corpo. Entre 13:24 e 14:33 do **mesmo dia** foram escritos mais quatro. Prosa não segurou — é exatamente o caso que o plano complementar chama de regra-mãe: "lição que fica em prosa volta no mesmo dia".
- **Correção em duas partes.** (a) **O gate:** `tools/check-frontboard-fecho-real`, ligado ao `pre-commit` e disparado só quando o placar entra no commit. Ele trata o campo como **lista separada por espaço** — foi essa forma que fez uma verificação anterior acusar o BUG-174 de fantasma sendo que os três SHAs dele existem. Visto vermelho antes de verde: acusou os quatro, com linha e identificador. (b) **A recuperação:** os quatro fechos foram reancorados no commit que de fato fez o trabalho, achado por busca no log, e cada registro passou a carregar `commit_recuperado_de` dizendo qual era o valor inexistente e como o novo foi encontrado — a procedência do conserto não pode ficar implícita.
  - `BUG-048` → `08e31141` "944 word_count convergidos"
  - `BUG-079` → `a72a94e9` "style-src fecha por hash"
  - `BUG-134` → `c6b78855` "a guarda de ética sobre o corpo publicado existia, estava testada e nunca rodou"
  - `BUG-147` → `aecd6475` "coleta de lixo do .cache por POLÍTICA"
- **Medição:** 535 registros, **137 SHAs de fecho, todos existem**.
- **Status:** fechado.

## BUG-211 — o detector exigia, para a Resolução CMN 4.949, uma URL que NENHUMA página do acervo usa
- **Data:** 2026-08-30
- **Severidade:** GRAVE — e ele estava classificado como "falta de dado editorial", que era o diagnóstico errado
- **Sintoma:** `TestCurrentLegalFactsAereo06RealShardHasZeroReasons`: `aer-pontos-cartao-nao-transferidos rejected: [current_legal_fact_source_missing:cmn_resolution_4949_financial_customer_relationship_duties]`.
- **★ O veredito herdado dizia que estes seis testes de `internal/v2ingest` acusavam páginas que "genuinamente carecem de fontes — dado editorial, não detector". Medido do zero, o primeiro deles refuta isso.** A página cita a norma certa: `https://www.in.gov.br/web/dou/-/resolucao-cmn-n-4.949-de-30-de-setembro-de-2021-350015767`, a publicação oficial do ato na Imprensa Nacional.
- **Causa raiz:** o detector exigia `https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4949&tipo=RESOLUÇÃO+CMN` — um endpoint de **consulta com query string**. Varrendo o acervo inteiro, as oito páginas que citam essa resolução usam duas superfícies, e nenhuma é essa: 4 usam o DOU da Imprensa Nacional e 4 usam `normativos.bcb.gov.br/…/Res_4949_v2_L.pdf`, o texto consolidado do BCB. As duas são citações **melhores** que a exigida. Quem estava fora do acervo era o detector.
- **Correção:** `aereo06SourceURLAlternates` — a mesma norma provada por qualquer uma das superfícies oficiais em que ela existe, com a lista fechada e nomeada uma a uma. A âncora exigida da fonte continua valendo igual; nada foi afrouxado. É o mesmo princípio que o repositório já aplicou às variantes do Planalto.
- **Consequência para os outros cinco:** eles falham pela mesma classe (`current_legal_fact_source_missing`, nove casos ao todo) e **não podem mais ser aceitos como dívida editorial sem medição própria caso a caso** — a classificação herdada foi refutada no primeiro que se mediu.
- **Status:** fechado o de aéreo; os outros cinco seguem abertos, agora com a classificação corrigida.

## BUG-212 — rodada parcial do registro de âncoras APAGAVA os documentos das rodadas anteriores
- **Data:** 2026-08-30
- **Severidade:** GRAVE — destruição silenciosa, com saída que parecia sucesso
- **Sintoma:** eu mesmo provoquei, medindo as âncoras do CPP. Rodei `tools/generate-planalto-anchor-registry-20260826 --relatorio <dois documentos>` e a evidência caiu de **11 documentos para 2**; `internal/structureddata/planalto_anchors_generated.go` perdeu **708 linhas**. Entre os apagados estava `l10406.htm`, com **4.346 ocorrências no acervo** — o documento mais citado de todos.
- **Causa raiz:** `atomic_write(EVIDENCIA, …)` gravava só os registros DA RODADA, e `escreve_tabela` derivava da mesma lista. Uma conferência dirigida a dois documentos tinha semântica de "substitua tudo".
- **★ Por que passaria despercebido:** a saída dizia `documentos com ancora de artigo: 2/2`, que lê como sucesso. E o renderizador só emite o fragmento **quando a âncora está provada na tabela** — apagar a tabela não quebra nada visível; ele simplesmente para de ancorar milhares de links, que é exatamente o defeito que a ferramenta existe para corrigir. `--so-tabela` não salvava: ele regenera a partir da evidência, que já estava truncada.
- **Correção:** a rodada parcial passa a **fundir** — a medição nova prevalece para a mesma URL (reconferir é o propósito) e o que não foi conferido permanece intacto, com a linha `N documento(s) de rodadas anteriores preservados` na saída. Os 11 apagados foram restaurados de `git show HEAD:` e fundidos com os 2 novos. Provado re-rodando os mesmos dois alvos: **13/13 documentos, 17.338 links inline em documento ancorável**.
- **Status:** fechado.

## BUG-213 — a página cita a variante do CPP que NÃO TEM âncora para o artigo que ela discute
- **Data:** 2026-08-30
- **Severidade:** GRAVE — dado editorial, e desta vez o detector estava certo
- **Sintoma:** `TestCurrentLegalFactsCriminal13LiveSnapshotWhenPresent`: `crim-representar-prazo-decadencial failed: [current_legal_fact_source_missing:cpp_article_38_six_month_decadence]`.
- **Medição, com o instrumento do próprio repositório** (o `curl` direto é recusado pelo WAF do Planalto; `generate-planalto-anchor-registry-20260826` passa):
  - `del3689.htm` — **798** âncoras de artigo, e `art38` e `art30` **existem**
  - `del3689compilado.htm` — **722** âncoras, e `art38` e `art30` **NÃO existem** (mas `art5`, `art24` e `art25` existem)
- **Veredito:** a página cita `del3689compilado.htm` sem fragmento, e essa superfície **não pode provar o art. 38** — não há âncora para ele lá. O detector exige `del3689.htm#art38`, que resolve. E a "mistura" da tabela do detector (12 usos da compilada contra 7 da simples) **não é arbitrária**: cada linha escolheu a variante cuja âncora existe, artigo por artigo. Normalizar a tabela em massa teria quebrado os 12 casos corretos — é a armadilha dos 366 decoys da família de âncoras.
- **★ E isso refuta a leitura fácil da contagem bruta:** o acervo cita a compilada 276 vezes contra 12 da simples, e `data/legal-corpus/cpp.json` registra a regra medida `regra_citacao: mais âncoras normativas medidas: 2790 contra 1932`. Nem a maioria nem a política decidem sozinhas — decide a âncora do artigo em questão.
- **Status:** ABERTO com a causa medida. A correção é na página (acrescentar a fonte ancorada `del3689.htm#art38`), pelo gerador datado com CAS, não no detector.

## BUG-214 — 1.311 citações do acervo apontam para variantes do Planalto que NÃO TÊM âncora de artigo
- **Data:** 2026-08-30
- **Severidade:** GRAVE — o deep link não resolve para o leitor, e a regra o exige de um documento que não pode carregá-lo
- **Sintoma:** `TestCurrentImobiliario09LegalFactsLiveShard` (5 intenções), `TestCurrentLegalFactsLiveImobiliario05` e `TestSampleReviewCurrentLegalFactsAcceptLiveCorrectedShards`, todos com `current_legal_fact_source_missing`.
- **Medição, com o instrumento do repositório** (o `curl` direto é recusado pelo WAF do Planalto):

  | documento | âncoras de artigo | citações no acervo | artigos exigidos |
  |---|---|---|---|
  | `l10406.htm` | 2.048 | 4.346 | todos presentes |
  | `l10406compilada.htm` | **3** | 928 | nenhum |
  | `l6015compilada.htm` | **0** | 243 | nenhum |
  | `l6015consolidado.htm` | 304 | 10 | presentes |
  | `l5172compilado.htm` | **0** | 140 | nenhum |
  | `l5172.htm` | 218 | 138 | presentes |

- **As duas metades do defeito, e elas são independentes:**
  1. **A regra nomeia o documento errado.** `sourceParts` pede `l6015compilada.htm#art213` e `l5172compilado.htm#art185` — fragmentos que **não existem** na variante nomeada. É o mesmo defeito que o comentário de `l11340.htm`, já no arquivo, registra: "exigir âncora que não existe no documento é pedir link que não resolve". A variante irmã carrega os mesmos artigos (`l6015consolidado.htm`, `l5172.htm`), e como `planaltoPartMatchesSource` compara **família + fragmento**, nomear a variante ancorável faz a regra passar a ser satisfazível.
  2. ~~A página estaria errada por citar sem fragmento.~~ **Medi e é o contrário.** Contando o acervo inteiro: das citações a esses documentos, **2.360 são cruas e apenas 7 trazem `#artN`** (2 em `l10406compilada`, 5 em `l8078compilado`, zero nas outras duas). As páginas citam sem fragmento **porque o documento não tem fragmento a citar** — que é exatamente o comportamento certo, e o mesmo que o precedente do `l11340.htm` registra. O acervo não está cheio de deep link quebrado: são 7 no total.
- **Correção, portanto, é só da regra**, na forma do precedente já no arquivo: para variante com ZERO âncora de artigo, o requisito perde o fragmento e o dispositivo continua cobrado — os `outcomes` da mesma regra já exigem "art 213"/"artigo 213" no corpo do texto. Nada afrouxa: a exigência do artigo migra do fragmento de URL, onde é impossível, para o corpo, onde é verificável.
- **★ Por que isso NÃO é o mesmo caso do BUG-211, e a diferença importa:** lá o detector exigia um endpoint de consulta que nenhuma página usava. Aqui ele exige uma âncora que o documento não tem. Os dois são defeito de detector, mas por razões diferentes — e o veredito herdado ("é tudo dado editorial") errou nos dois. Foi preciso medir cada um: o de criminal (BUG-213) **é** editorial, e é o único.
- **Status:** ABERTO, com a causa medida e a correção definida. Fica para a próxima leva de `internal/v2ingest`, que sai num commit só por causa da atestação do grafo.

## BUG-215 — o baseline de vermelhos anistiaria 75 testes por causa de um artefato gerado stale
- **Data:** 2026-08-30
- **Severidade:** CRÍTICA — baseline inflado é ANISTIA: o próximo commit que quebrasse esses testes de verdade passaria
- **Sintoma:** rodei `generate-baseline-testes-vermelhos ./internal/v2ingest/` e ele registrou **81 vermelhos em 145,9 s**, contra os **6 reais** de uma suíte que leva ~500 s.
- **Causa raiz, e ela foi minha:** eu havia mexido em `internal/structureddata` — que está no fecho de importação do validador — **depois** do último `go generate`, então `validator_fingerprint_attestation_generated.go` estava stale e 75 testes de atestação falhavam em bloco. O gerador de baseline não distingue "o repositório tem dívida" de "falta rodar um comando de duas linhas": grava o que estiver vermelho.
- **★ Por que é crítico e não cosmético:** a lista de vermelhos conhecidos é o que o pre-commit TOLERA. Setenta e cinco testes de atestação entrando nela significa que a próxima quebra real deles não reprova nada — e são justamente os testes que impedem o pino do estoque de divergir e travar o deploy de todas as frentes.
- **Correção:** o gerador passa a **recusar** a gravação quando a execução contém a assinatura de artefato gerado stale (`does not match authenticated source graph`, `run go generate`), imprimindo o comando de conserto. A falha diz de si mesma o que é; não há adivinhação. É a terceira guarda desta família no mesmo arquivo — já havia a recusa de log truncado com saída de hook (BUG-194) e a reprovação por baseline inflado.
- **Nota de método:** o número errado só apareceu porque conferi `81 contra 6` antes de commitar. Baseline é dado que o gate consome sem questionar — número que entra ali tem de ser medido, não aceito.
- **Status:** fechado.

## BUG-216 — o comentário jurava paridade entre os dois reapers, e o código não tinha
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — comentário que mente é bug, e este escondia uma divergência real entre duas ferramentas que matam processo
- **Sintoma:** achado ao investigar um `pgrep` auto-referente meu. `tools/env/ai-process-reaper:52` usava `pgrep -f 'claude daemon run'` com o filtro `case "$dcmd" in *'daemon run'*` — substring em **qualquer lugar** da linha de comando — enquanto o comentário logo acima afirma: *"Mesma regra do `ai-session-reaper`, para os dois não divergirem sobre o que é um daemon abandonado."*
- **Causa raiz:** o irmão `ai-session-reaper` foi ancorado no **executável** depois de o red-team tropeçar duas vezes na forma solta — `tools/env/AVISO-ai-session-reaper.md` registra: *"um pgrep devolveu o próprio shell dele, e um pkill análogo matou o shell com exit 144"*. A correção nunca foi propagada, e o comentário passou a descrever uma paridade inexistente.
- **Direção do dano, medida:** aqui o efeito é **proteger demais**, não matar demais — `add_tree` protege a árvore casada. Mas há um caminho estreito de dano real: um processo casado por engano, com `PPID==1` e um `"pid":N` morto na linha de comando, cai no `continue` e **sai da proteção**.
- **Prova, antes e depois** (mesma lógica de shell, cinco linhas de comando sintéticas):

  | linha de comando | regra antiga | regra nova |
  |---|---|---|
  | `…/claude daemon run --origin transient` | casa | casa |
  | `…/share/claude/versions/1.2.3/claude daemon run …` | casa | casa |
  | `bash -c pgrep -f claude daemon run` | **casa** | não casa |
  | `grep -rn claude daemon run tools/` | **casa** | não casa |
  | `vim /var/log/claude daemon run.log` | **casa** | não casa |

- **Correção:** a mesma âncora do irmão — primeiro token é o executável do Claude e o segundo é literalmente `daemon`. `./tools/check-ai-process-reaper-daemon` continua passando (criador morto vira alvo, criador vivo fica protegido).
- **Status:** fechado.

## BUG-217 — mudar o portfólio sem reancorar o estoque trava a publicação de TODAS as frentes
- **Data:** 2026-08-30
- **Severidade:** CRÍTICA — `public-release-transaction` reprova e sem ele não há deploy
- **Sintoma:** o crítico 6 do briefing é o único dos nove que ainda se reproduzia — mas **não pela causa do enunciado**. `check-criticos-do-briefing-20260829 --completo` mediu `exit=1` com `sitemap_mismatch=0` e `campos_do_enunciado=0`: os 59.388 erros e os dois campos `source_type`/`use_in_content` não existem mais. O gate reprovava por outra coisa:
  ```
  v2_stock_freshness_source_changed: portfolio_v2/seguros.jsonl
  v2_stock_freshness_source_changed: portfolio_v2/telecom_energia.jsonl
  v2_stock_freshness_source_changed: portfolio_v2/aereo-w3.jsonl
  v2_stock_freshness_terminal_evidence_invalid
  ```
- **Causa raiz, e metade dela foi minha:** `seguros.jsonl` e `telecom_energia.jsonl` mudaram no commit `7e6735fb` desta sessão — as 21 dicas de fonte do BUG-206 — e eu **não reancorei o recibo de frescor**. Mudar portfólio invalida o recibo, e o recibo é o que a publicação transacional exige.
- **★ E a outra metade é anterior e mais grave que a minha:** `aereo-w3.jsonl` está dessincronizado desde `4b06e544`, de 2026-08-29. **O recibo estava stale desde ontem e nenhum gate de rotina acusou** — só o `--completo`, que ninguém roda por padrão porque custa ~1 min. A publicação esteve travada por um dia inteiro sem sinal.
- **Correção:** `./tools/ingest-v2-stock` reancorou o estoque — `status=pass duration_ms=456108` sobre 10.354 páginas. Verificado o efeito colateral que o gate de atestação cobra: o `validator_fingerprint_sha256` do recibo (`sha256:1bb75215…`) bate com a atestação do grafo, então a re-ingestão não deixou o commit seguinte com pino divergente. `public-release-transaction: pass`, `GATE_EXIT=0`.
- **Regra que fica:** mexer em `data/editorial/portfolio_v2/` sem re-ingerir na mesma onda deixa o repositório com a publicação travada e ninguém vê — o `deploy-publico` re-ingere sozinho, mas só quando alguém roda um deploy.
- **Status:** fechado.

## BUG-218 — o gerador da tabela de âncoras confundia "medi e é zero" com "não medi"
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — regressão minha, pega pelo gate antes de pousar
- **Sintoma:** o commit do fecho atestado reprovou com `TestInlineLinkLevaAoDispositivoQuandoAAncoraExiste`: *"documento sem âncora de artigo ficou no registro e não deveria receber fragmento nenhum: l5172compilado.htm, l6015compilada.htm"*. **Não estava no baseline — era regressão do próprio commit**, e o gate disse isso com essas palavras.
- **Causa raiz:** `escreve_tabela` filtrava por `ancoras_de_artigo is not None`, o que deixa passar **lista vazia**. Ao medir `l6015compilada.htm` (243 citações, zero âncoras) e `l5172compilado.htm` (140, zero), eu os coloquei na tabela Go — que é a lista de documentos que **podem** receber fragmento. O renderizador só ancora o que a tabela prova; um documento de lista vazia ali é contradição.
- **A distinção que faltava, e ela importa nos dois sentidos:** `nil` é documento **inacessível na coleta** — não se mediu nada. Lista vazia é documento **medido com zero âncora**. Nenhum dos dois entra na tabela, mas pelo motivo oposto, e o zero **fica na evidência**: é ele que prova, no BUG-214, que a regra do detector pedia `#art213` de um documento onde essa âncora não existe. Apagar o zero destruiria a medição que sustenta o achado.
- **Correção:** o filtro passou a exigir lista não-vazia, e `TestRegistroDeAncorasBateComEvidencia` aprendeu a mesma distinção. Resultado medido: **tabela com 16 documentos, evidência com 18**, e os dois de zero âncora presentes só na segunda. `./tools/go-modern test ./internal/structureddata/` verde.
- **Status:** fechado.

## BUG-219 — teste de lease falha sob carga concorrente e envenena o baseline, e a minha primeira correção foi REFUTADA pela medição
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — o dano não é o vermelho, é o baseline gravá-lo como dívida e anistiá-lo
- **Sintoma:** `TestCanonicalStockReadLeaseExecFilesSurviveAbruptOwnerExit` entrou no baseline como vermelho conhecido, gerado enquanto `cmd/build public` e `public-release-transaction` rodavam concorrentes. No commit seguinte ele **passou**, e o gate reprovou por "dívida paga, lista inflada" — corretamente.
- **Medição isolada:** **0 falhas em 11 execuções** com a máquina calma. O teste não é quebrado; ele cede sob carga.
- **★ E a minha primeira correção estava errada — a própria medição a derrubou.** Diagnostiquei que a janela de 3 s para o holder sumir da tabela de processos era curta, e tornei o deadline proporcional ao `/proc/loadavg`, no mesmo padrão do `COMMIT_GATE_LOAD_FACTOR` do pre-commit. Resultado: **1 falha em 4 execuções**, contra 0 em 11 do original — e a falha migrou para outra asserção, `writer remained busy after abrupt owner's inherited holder exited`. Ou seja, o gargalo não é a janela: é a liberação do lease pelo kernel depois que o holder sai. Desfiz a edição por reescrita (nunca `git checkout`), e confirmei o retorno a 0/6.
- **O que fica sabido, e o que não:** sabe-se que o teste é estável isolado, que falha sob carga pesada concorrente, e que alargar a janela **não** conserta — a asserção que cede é a do lease, não a do processo. Não se sabe ainda o mecanismo exato da corrida entre a morte do holder e a liberação do `flock` herdado.
- **Mitigação imediata:** gerar o baseline com a máquina calma, nunca concorrente com build ou release. Um teste instável no baseline é pior que vermelho: vira anistia.
- **Status:** ABERTO, com a causa parcialmente medida e uma hipótese explicitamente refutada.

## RE-TRIAGEM DOS NOVE CRÍTICOS — 2026-08-30, depois do BUG-217
- **Comando:** `./tools/check-criticos-do-briefing-20260829 --completo` (executa os comandos de verdade; não lê enunciado)
- **Resultado: nenhum dos nove se reproduz.** Um deles, o 6, estava vivo nesta sessão e foi fechado hoje pelo BUG-217; os outros oito já não se reproduziam.

  | # | enunciado (2026-08-29) | medição de 2026-08-30 |
  |---|---|---|
  | 1 | `cmd/build public` reprova com 261 achados em 29 rotas | `exit=0 achados=0` |
  | 2 | `universo_urls=18731` inflado | `universo_urls=10312` |
  | 3 | CVE alcançável no x/crypto | `achados=1 alcancaveis=0 sem_correcao_upstream=1` |
  | 4 | `go vet` falso-verde por VetxOnly | `padrao_full_tree=False cache_buster=True` |
  | 5 | googlebot-smoke valida o próprio cache | caminho fixo ausente; refutado por experimento |
  | 6 | 59.388 erros por `source_type`/`use_in_content` | `exit=0 sitemap_mismatch=0 campos_do_enunciado=0` |
  | 7 | contrato × medição divergem | `exit=0`, o contrato bate com o manifesto |
  | 8 | 225 URN erradas em ~199 páginas | 10.354 páginas, **0** emissões erradas |
  | 9 | `ValidateEditorialBody` é código morto | 1 chamador de produção |

- **★ O crítico 3 merece nota: a prescrição do enunciado é INEXECUTÁVEL, e isso foi medido, não suposto.** Ele manda subir `golang.org/x/crypto` de `v0.55.0`. Medição própria de hoje: `./tools/go-modern list -m -versions golang.org/x/crypto` termina em **v0.55.0** — é a versão mais alta que existe. O `fixed_version` vazio na evidência do govulncheck diz o mesmo, e `reachable_call: False` mostra que o código vulnerável não é alcançável a partir do nosso. Não há para onde subir. É a classe que o plano complementar chama de "prescrição nunca executada"; desta vez foi tentada.
- **★ AUDITORIA COMPLETA DOS NOVE EM `arquivo:linha` (2026-08-30, segunda passada).** A primeira auditoria cobriu 2 e 9. Esta fecha os sete restantes com evidência no código ou na página servida — não no veredito do gate:

  | # | evidência independente do gate |
  |---|---|
  | 1 | `cmd/build public` rodado hoje isolado: `generated_pages=10136 achados=0`, e o deploy que se seguiu pousou `NO AR — 10136 paginas` |
  | 2 | `tools/wikiuniverso.py:urls_publicas()` deriva de `shards_declarados()`; **zero** leituras diretas de `public/sitemaps` em Go fora de teste; 7 consumidores |
  | 3 | `go list -m -versions golang.org/x/crypto` termina em **v0.55.0**, a versão instalada — a prescrição "suba a versão" é inexecutável; `fixed_version` vazio e `reachable_call: False` |
  | 4 | `tools/go-build-check:7` — *"ESCOPO (corrigido em 2026-08-29, BUG-057): o padrão `./...` NÃO…"*; `:71` imprime `escopo=./internal/... ./cmd/... cache-buster=-tags ${VET_NONCE}` (BUG-107). As 6 ocorrências de `./...` no arquivo são comentários explicando por que não se usa |
  | 5 | **nenhum `/tmp` fixo** em contexto de googlebot/smoke em `internal/checks/checks.go` |
  | 6 | fechado nesta sessão pelo **BUG-217**; `campos_do_enunciado=0` — `source_type`/`use_in_content` não aparecem mais |
  | 7 | `tools/check-contrato-vs-medicao:71` — *"AMPLIADO EM 2026-08-29 (BUG-106): o GOAL.md e o AGENTS.md registram estado"*; `:116` nomeia `published_manifest=0` |
  | 8 | a página servida `/glossario/qualidade-de-segurado/` emite `urn:lex:br:federal:lei:1991-07-24;8213!art27a` — **art. 27-A**, o correto; o enunciado dizia 24-A. O acervo emite 56.253 URNs LexML em 8.322 páginas, com 0 erradas |
  | 9 | `ValidateEditorialBody` chamada em `checks.go:6678` sobre `repo.Pages` filtrando `published`+`index`; gate nomeado `legal-marketing-policy` roda com `exit=0` |

- **★ AUDITORIA DO PRÓPRIO GATE — porque "gate verde não é prova" (2026-08-30).** Refutar os nove pelo gate é fraco se o gate medir a coisa errada. Auditei, com comando independente, os dois enunciados cuja medição do gate NÃO cobre o texto do briefing:

  **Crítico 2** — o enunciado diz "42 arquivos leem `public/sitemaps/` do DISCO em vez do índice" e pede "UMA função universo público vinda do índice". O gate só mede `universo_urls` no ledger. Medição independente: **zero** leituras diretas (`Glob`/`ReadDir`/`ReadFile`/`os.Open`) de `public/sitemaps` em Go fora de teste; e a função pedida **existe** — `tools/wikiuniverso.py:urls_publicas()`, que deriva de `shards_declarados` (o índice), levanta `UniversoIndisponivel` se o índice anunciar shard inexistente, tem teste próprio (`test_wikiuniverso.py`) e **sete consumidores**, incluindo o aquecedor `warm-edge-cache` que o enunciado dizia estar "remendado por dedup". Corrigido na raiz, como o enunciado prescrevia.

  **Crítico 9** — o enunciado diz que `ValidateEditorialBody` é código morto e que o gate de promessa "valida os 7.959 candidatos, não as 10.116 no ar". Medição independente: a função **é chamada de produção** em `checks.go:6678`, pelo `validaCorpoPublicadoContraPromessa`, que itera `repo.Pages` filtrando `Status == "published" && IndexPolicy == "index"` — as rotas publicadas e indexáveis, não a esteira de candidatos. Está registrada como gate nomeado (`legal-marketing-policy`, `checks.go:427` e `:1675`) e roda: `exit=0`. E o comentário preserva a DEC-024, para o falso positivo de prosa que NEGA a promessa não voltar.

- **Erro de execução meu, registrado para não enganar quem ler o log:** ao medir o crítico 1 eu disparei `cmd/build public` em paralelo com o próprio gate, e os dois disputaram o lease do estado público — deu `build: lease exclusivo do estado público indisponível` e `exit=1`. Não era defeito do build; era contenção que eu criei. A medição limpa, serializada, deu `exit=0 achados=0`.

## BUG-220 — o manifesto versionado voltou a citar prova ausente, e desta vez fui EU
- **Data:** 2026-08-30
- **Severidade:** GRAVE — quem clonar o repositório recebe a afirmação sem a prova
- **Sintoma:** medindo os itens "DEPOIS" do briefing, achei o BUG-053 **reincidente**: `data/editorial/stock_manifest.json` e `data/ops/v2_ingest_transaction_receipt.json` — os dois versionados, os dois commitados por mim em `9ac7ff75` — citam a transação `v2-rewrite-v5-7099acf50a2c098a9a6e2b6a558a5fe7`, cujo recibo terminal estava **untracked**.
- **Causa raiz, e é minha:** a re-ingestão do BUG-217 gerou o recibo em `data/ops/v2_ingest_terminal_receipts/`; eu incluí o manifesto e o recibo de transação no pathspec do commit e **deixei o recibo terminal de fora**. O plano registrou este mesmo defeito em 2026-08-29 ("o manifesto aponta para uma prova ausente") e a lição ficou só em prosa — reincidiu em um dia.
- **★ E ele era o ÚNICO arquivo untracked não-ignorado do repositório inteiro** (`git status --porcelain --untracked-files=all` → 1). Depois do conserto: **zero**.
- **Correção em duas partes.** (a) O recibo entrou no git. (b) O gate: `tools/check-recibo-de-transacao-versionado`, ligado ao `pre-commit` e disparado só quando um dos dois citantes entra no commit — ele extrai todo `transaction_id` dos arquivos versionados e exige o recibo correspondente **rastreado**, imprimindo o `git add` pronto. Visto vermelho antes de verde, nomeando a transação e os dois arquivos que a citam.
- **Por que gate e não anotação:** é a segunda vez que este defeito aparece, e a primeira lição ficou em texto. O plano complementar chama isso de regra-mãe — lição que fica em prosa volta no mesmo dia; esta voltou em um.
- **Status:** fechado.

## BUG-221 — anti-molde caiu de 363 pares para 2, e os 2 que sobram são molde de verdade
- **Data:** 2026-08-30
- **Severidade:** MÉDIA — dívida editorial nomeada, pequena e localizada
- **Medição própria** (Jaccard 3-grama e 5-grama sobre o corpo, por lane, ignorando tombstone e corpo < 200 caracteres):

  | | enunciado (2026-08-29) | medição de 2026-08-30 |
  |---|---|---|
  | pares comparados | 103.873 | 85.491 |
  | pares ≥ 0,70 (3g) | **363** | **2** |
  | pares ≥ 0,70 (5g) | 62 | **0** |
  | pico 3g | 0,8767 (`dia-pr-20260825` × `dia-pr-20260821`) | 0,7243 |

- **Os 2 que sobram são molde de verdade, e estão nomeados:** `jur-stj-tema-329` × `jur-stj-tema-327`, ambos em `stj-tema-derivado-01.jsonl`. A abertura é idêntica salvo o número do tema e a área — *"O Tema **329** … responde a uma questão concreta de direito **administrativo** e vale para todos os processos que discutam a mesma controvérsia"* contra *"O Tema **327** … de direito **ambiental** …"*. É a permutação de palavra-chave que o contrato proíbe, e o pico de 0,7243 está acima do limiar de 0,70.
- **A correção é no gerador do canal `stj-tema-derivado`, nunca baixando o limiar** — o contrato é explícito, e os `diarios-municipais` que davam o pico anterior já não aparecem.
- **Status:** ABERTO com número e par nomeado. Soma-se à frente editorial do BUG-200.

## BUG-222 — a bateria de gates confirma o item "157 de 391 vermelhos": hoje são 152 de 428
- **Data:** 2026-08-30
- **Severidade:** GRAVE — é o único item "DEPOIS" do briefing que se confirma vivo em escala
- **Medição:** `./tools/generate-varredura-bateria-gates a .agents/runtime/caca/varredura-20260830-a.jsonl` — a ferramenta do próprio repositório, que mede o **exit code real** de cada `tools/check-*` e não a impressão de quem lê.

  | | enunciado (2026-08-29) | medição de 2026-08-30 |
  |---|---|---|
  | gates medidos | 391 | **428** |
  | vermelhos | 157 | **152** (35,5%) |
  | `exit=1` | — | 138 |
  | `exit=124` (timeout) | — | 8 |
  | `exit=2` | — | 6 |

- **★ Os 8 timeouts batem TODOS em 90 s exatos** — `check-agent-friendly-html` 90.152 ms, `check-priority-controlled-promotion` 90.119 ms, `check-v2-body-semantic-duplicates` 90.084 ms, `check-claude-idle-cpu` 90.012 ms, `check-claude-idle-repaint.sh` 90.006 ms. Noventa segundos é o teto do **tier A**, e a varredura separa tier pelo orçamento **declarado** pelo gate. Bater no teto redondo não é o gate travando: é ele estar no tier errado. Um `exit=124` assim é vermelho por relógio, indistinguível de defeito — a mesma classe do BUG-219.
- **Status:** ABERTO com o número medido. A triagem por família (defeito real × dívida nomeada × falso-positivo de detector × ambiente) está em curso com refutação adversarial, e é ela que diz quantos dos 152 são defeito de verdade — número bruto de gate vermelho não é veredito, e este repositório já pagou por tratá-lo como tal.

## BUG-223 — 385 dicas do catálogo não resolvem contra o registro de fontes, e o gate só mostra a primeira
- **Data:** 2026-08-30
- **Severidade:** GRAVE — dica que não resolve some do espelho e derruba o lote no emit-clean, em silêncio (a mesma perda do BUG-196)
- **Sintoma:** `./tools/check-v2-portfolio-source-hints` → `exit 2`, `source hint catalog entry is not resolved: anac-dicas-documentos-embarque`. O gate aborta na **primeira** entrada que falha, então o número real nunca aparece.
- **Medição própria, com o RegistryMatcher do próprio gate** carregado sobre o catálogo inteiro: **385 de 3.734 dicas (10,3%) não resolvem**. Todas apontam para host oficial — o que falta é o caminho estar nos `canonical_base_urls` da autoridade:

  | host | dicas sem resolução |
  |---|---|
  | `www.gov.br` | 105 |
  | `www.tst.jus.br` | 68 |
  | `arquivocidadao.stj.jus.br` | 41 |
  | `conteudo.cvm.gov.br` | 31 |
  | `processo.stj.jus.br` | 26 |
  | `www.bcb.gov.br` | 18 |
  | `www.in.gov.br` | 16 |
  | `www.cnj.jus.br` | 14 |
  | Anatel, ANS, ANAC, STF | 28 |

- **Primeira fatia corrigida, e ela mostra a forma do conserto:** a autoridade `anac-govbr` **já existia**, com `official_domains: ["www.anac.gov.br"]` e dois caminhos das Resoluções 280 e 400. Faltava o **portal institucional** em `www.gov.br/anac`, que cinco dicas usam em três caminhos — os três sondados hoje com 200. `tools/generate-source-registry-anac-20260830` estendeu a entrada existente (domínios `www.anac.gov.br` + `www.gov.br`, 5 caminhos canônicos).
- **★ A primeira versão dessa ferramenta ia CRIAR uma entrada nova, e ela mesma me barrou:** `anac-govbr já está no registro`. Duplicar autoridade teria sido o defeito. Reescrevi para ESTENDER, e a versão final se recusa a rodar se a autoridade não existir.
- **★ E por que estender não afrouxa:** `official_domains` não autoriza sozinho — em `check_v2_portfolio_source_hints.py:88` ele só valida que cada `canonical_base_urls` pertence a um domínio declarado; o casamento real é por **prefixo de caminho exato** (`:91`). Acrescentar `www.gov.br` aos domínios da ANAC libera apenas os três caminhos declarados, todos sob `/anac/pt-br/assuntos/passageiros/`. O gerador ainda compara as flags de publicação antes e depois e aborta se qualquer uma mudar.
- **Status:** ABERTO com o número e a distribuição por host. A ANAC fechou; faltam 380, e a rota é a mesma — estender a autoridade existente com o caminho medido, nunca criar autoridade nova.

## RELEASE 2026-08-30 — build, deploy e produção conferida depois da caça
- **Autorização:** ordem do dono nesta sessão ("pode rodar build e deploy, ver se a produção fica saudável, esperando o aquecimento terminal").
- **Pré-voo:** `public-release-transaction: pass`, `check-v2-portfolio-pairing` OK (10.458 intents 1:1), worktree limpa em `internal/`, `cmd/`, `content/`, load 1,46.
- **★ Crítico 1 do briefing, medido SEM contenção:** `cmd/build public` → `generated_pages=10136 indexable_pages=10351`, **achados=0**. O enunciado dizia "261 achados em 29 rotas". E o `exit=1` que apareceu antes nesta sessão era contenção de lease que **eu** criei ao disparar o build em paralelo com a bateria de gates — não defeito.
- **Escrita idempotente confirmada: 0 HTMLs reescritos** pelo build. É a prova prática de que o item "Last-Modified = mtime do build mata o 304" está morto — o build rodou inteiro e não re-datou uma página.
- **Deploy nos 7 passos**, sem `--ressemear` por decisão medida (mexi em portfólio, detector, registro de fontes e ferramentas; nada de markup). O deploy detectou mudança de camada sozinho — `purgando tudo: mudanca de camada afeta TODA rota, nao so as 2 que mudaram de conteudo` — purgou e reaqueceu **10.486 URLs em 874 s a 12 r/s**, terminando em `NO AR — 10136 paginas`. Nenhuma purga manual depois: numa sessão anterior isso jogou fora 872 s de aquecimento.
- **Produção conferida, e idêntica à linha de base medida antes do deploy:**

  | verificação | resultado |
  |---|---|
  | 30 rotas do acervo (passo determinístico) | **30/30** em 200 com corpo |
  | superfície de máquina | **7/7** em 200, tamanhos byte a byte iguais aos de antes |
  | consistência HTML × Markdown, 12 rotas reais sorteadas com semente fixa | **12/12** — html e gêmea `.md` em 200, content-type certo, 12 áreas distintas |
  | contrato de indexação | 10.354 páginas, **0 acima de 50 KB**, maior 41,9 KB, mediana 29,5 KB |
  | `check-portal-health` | `acervo=200 pagina=200 sitemap=200 · go=200 busca=200 · restarts=0` |
  | borda | `cf-cache-status: HIT` |
  | 304 depois do deploy | `If-Modified-Since` igual → **304**; data anterior → **200** |
  | `last-modified` | **26 Aug 2026 preservado** — o deploy não re-datou o acervo |

- **★ Dois erros meus de método, registrados porque número errado no log vira enunciado da próxima sessão:** (a) sondei três rotas que eu mesmo INVENTEI e obtive 404 — o dado útil ali foi html e md concordarem; refiz com rotas do manifesto e deu 12/12. (b) o meu script inline leu `public_path` quando a chave do manifesto é `path`; a ferramenta commitada (`tools/check-producao-pos-deploy`) já trata as duas, por isso passou.
- **Superfície de máquina pela FONTE ÚNICA, não por chute:** os caminhos que `internal/agentsurface` declara são `/.well-known/agent-card.json` (200, 3.281 b), `/.well-known/ai-catalog.json` (200, 3.773 b) e `/mcp` — que dá **405 em GET e 200 em POST** (3.683 b com `tools/list`), como deve. O `/sitemaps/sitemap-index.xml` responde **410 deliberado**, com o motivo escrito na config: *"404 é 'não achei, talvez volte' e mantém a URL na fila de recrawl; 410 é 'foi embora'"*.

## BUG-195 — três workflows de escrita executáveis com fila morta e o redator que DELETAVA página boa
- **Data:** 2026-08-30
- **Severidade:** CRÍTICA — arquivo runnable com defeito de perda permanente de trabalho
- **Sintoma:** `TestEveryWritingMassWorkflowHasClosedExecutionContract` acusava `unregistered derived writing-mass workflow writing-mass-todo-part{1,2,3}.js`.
- **Causa raiz, medida:** os três não eram arquivo de fila. Tinham `agent(`, `parallel(`, `phase(` e bloco de resultado — qualquer um podia rodar. E rodar significava (a) **215 de 242 pinos CAS mortos** contra o shard vivo (part1 40/48, part2 124/141, part3 51/53), todos dropados pela partição por lote de `7eacdd98`; e (b) o **executor congelado sha `028217ed…`**, diferente do canônico `c820b7a6…` e anterior a `f6149aaf` — sem a regra que separa "sem fonte real no mundo" de "defeito de sistema", o redator grava tombstone quando o CAS recusa por catálogo furado, o que **descarta a página já escrita e marca a intenção como resolvida**. Faltam também `a43e24ee`, `62af7d94` e `0c41367d`.
- **Correção:** `tools/generate-writing-mass-inventory-only` converte executor em inventário preservado — os 242 lotes ficam byte a byte, sai só a cópia velha do executor, cujo original vive em `writing-mass-todo.js`. É a forma que os cinco inventários legados já tinham. 1.203 lotes preservados nos oito arquivos convertidos.
- **Status:** fechado em `8944ce2c`.

## BUG-196 — o regenerador da fila recusava âncora de artigo, sozinho contra o produtor e os três consumidores
- **Data:** 2026-08-30
- **Severidade:** GRAVE — perda silenciosa, sem mensagem de erro
- **Sintoma:** `TestWritingSourceAuthenticators…/relaunch-writing` divergia dos outros três workflows no caso `#ato`.
- **Causa raiz:** `ops/relaunch-writing.sh:247` tinha `not parsed.fragment` — a régua anterior a `0c41367d`. Quem PRODUZ a fila (`tools/generate_v2_review_queue.py:320`, `fragment_allowed`) emite deep link ancorado em artigo, e os três consumidores JS já o aceitavam. A recusa do regenerador não aparece como erro: o `source_hint` some do espelho e os lotes dependentes caem no manifesto emit-clean — a mesma perda de 4 em 109 lotes medida em 2026-07-31, pelo outro lado.
- **Medição:** catálogo vivo com **3.734 URLs, 0 com âncora hoje** — nada muda agora, e por isso o conserto foi barato. O que ele impede é a próxima entrada ancorada desaparecer sem ninguém ver.
- **Correção:** régua alinhada ao produtor, incluindo o que continua reprovando — fragmento vazio, escape inválido, controle/U+FFFD/U+2028/U+2029.
- **Status:** fechado em `8944ce2c`.

## BUG-197 — `writing_mass_workflow_test.go` era uma FOTO de 2026-07-21, e cobrava de volta duas formas medidamente piores
- **Data:** 2026-08-30
- **Severidade:** GRAVE — 11 testes vermelhos por drift de teste, escondendo os defeitos reais atrás deles
- **Sintoma:** 27 linhas de falha na família `writing-mass`.
- **Causa raiz:** o arquivo não é tocado desde `eecffb2f` (2026-07-21), enquanto os scripts que ele congela receberam **oito commits** até 2026-08-12. Ele exigia de volta, fragmento por fragmento, o que esses commits corrigiram.
- **Dois casos em que a forma antiga era MEDIDAMENTE pior, e restaurá-la seria a regressão:**
  1. `const attemptedBatches = results.length` — o próprio script explica que isso **inflava `failed_claims` com lotes nunca lançados e ZERAVA `unattempted` mesmo com halt**, porque todo thunk resolve. As duas linhas viraram **proibidas**.
  2. `{Name: "exact fragment", Want: false}` — congelava a regex que dropou os 4 lotes. Foi o **próprio `:519` do teste**, rodando o produtor Python, que se contradisse (`got=true want=false`). Entraram dois casos novos que seguem em `false`: fragmento vazio e escape inválido.
- **E cinco fragmentos exigiam o que não existe ou nunca existiu:** `maximalConflictFreeEpoch` **nunca esteve no script** (medido em `7eacdd98^`); `MAX_DRAFTS_PER_EPOCH = 24` virou 31 com o motivo escrito no código e confirmado por `relaunch-review.sh:669`; `selected_resources = set()` foi **promovido** para `generate_v2_review_queue.py:5338`, com teste próprio; `with _lock_set(task["slug"]):` ganhou um segundo argumento e quebra de linha; `"enfileira"` era o **detector lendo PROSA** — duas linhas `//` que explicam o relaunch. Consertado o detector (`semComentariosDeLinha`), não o comentário.
- **E o harness Node do próprio teste estava incompleto:** `hasOwn is not defined` — o predicado extraído usa o helper que `writing-mass.js:121` define fora da fatia. Reprovava por preâmbulo, não por contrato.
- **Status:** fechado em `8944ce2c`.

## BUG-198 — dois tetos diferentes confundidos num só, e um prefixo de slug que reprovava 29 lotes entregues
- **Data:** 2026-08-30
- **Severidade:** GRAVE — o verificador de fechamento abortava no lote 42 e **nunca chegava** à checagem que importa
- **Sintoma:** `ValueError: inventário lote 42: lote-base não canônico`.
- **Causa raiz, duas:**
  1. **22 é o teto da FATIA, não do lote.** Lote pinado carrega a lista exata de intents e seu `n` é o tamanho do pino; o teto dele é o hard max de epoch (31). `bancario-07` e `aereo-09` têm 23 pinos cada, com shards vivos de exatamente 23 linhas — o inventário estava certo.
  2. **`slug.startswith(area + "-")` era convenção, não integridade.** Reprovava **29 lotes, todos os 29 com shard escrito e contagem batendo**: campanhas cruzadas (`codex-sucessoes-transito-r14` → `transito`, `administrativo-r01` → `servidor`, `sucessoes-r01` → `sucessoes2`). Verificado cláusula a cláusula que a integridade tem três guardas independentes: `rel_path == portfolio_v2/{area}.jsonl`, unicidade global de slug, e pertencimento em `_expected_intents:458-468`. Nenhuma variante estreita sobrevive aos 29 — `sucessoes-r01` em `sucessoes2` com `sucessoes.jsonl` existente mata qualquer regra por prefixo.
- **Correção:** teto condicional nas duas réguas (Go e Python) e prefixo removido. O caso de teste do prefixo **não foi deletado, foi movido para a camada certa**: passa a exercitar `_expected_intents` levantando "intent_id pinado fora do portfolio" e "family do intent_id pinado diverge".
- **★ O QUE O ABORT ESCONDIA:** com o lote 42 fora do caminho, o verificador alcançou a checagem de completude e acusou **39 lotes pinados com 204 intents sem página** (`criminal-w3-05` 22, `tributario-w3-03` 22, `familia-w3-05` 18, `bancario-w3-06` 14…). É trabalho editorial pendente, real e agora visível — ver BUG-200.

## BUG-199 — o teste cobrava o resultado de uma migração que foi preparada e NUNCA aplicada
- **Data:** 2026-08-30
- **Severidade:** GRAVE — executá-la como escrita contradiria produção (armadilha BUG-090)
- **Sintoma:** `TestWritingMassInventoryAdoptsPreservedDBatchesAsExactPins` exigia que `seguros-17`, `consumidor-23/24`, `tributario-27/28` e `glossario2-22..33` tivessem sumido, sete slices residuais existissem, e `seguros-04` tivesse 20 páginas.
- **Três provas no disco de que a migração de 2026-07-15 não rodou:** o recibo `data/editorial/v2_writing_inventory_pin_migration_20260715.json` **não existe**; o manifesto de preimagem traz `"approval": false`; e a preimagem arquivada de `writing-mass-full.js` (`9ff9cce0…`) já não bate com o arquivo vivo (`bc0a96c9…`).
- **E aplicá-la hoje contradiria os artefatos:** `seguros-17` tem 14 páginas escritas e **zero interseção** com `seguros-d01`; o shard de `seguros-04` tem 15 linhas, não 20; `consumidor-21`, `tributario-26` e `tributario-29` não existem nem no inventário nem no disco.
- **E havia drift real de pino, em duas direções opostas — foi isso que permitiu decidir:** em `consumidor-d01`, `glossario2-d01/d02/d04` o inventário batia com o shard e a tabela do teste é que estava fora; em `glossario2-d03/d05`, `seguros-d01`, `tributario-d02` a tabela batia e o **pino** é que estava fora. O CONJUNTO de intents era idêntico nos oito — só a ordem divergia, e ordem é propriedade do artefato, não escolha editorial. Ela importa porque `wellFormedBatchClaim` compara `JSON.stringify(result.intent_ids)` com o do lote: pino fora de ordem faz o redator reescrever o shard só para reordenar linhas.
- **Correção:** `tools/generate-writing-mass-d-pins-20260830` re-pinou os quatro na ordem do shard, por **edição pontual** (o re-dump do array normalizaria duas junções `}},{{` sem espaço — churn em 798 lotes que ninguém pediu). A tabela do teste seguiu a mesma ordem, e o **membership continua congelado**: um intent a mais ou a menos reprova. O bloco da migração abandonada deu lugar à guarda que ela queria: nenhum dos 802 lotes disputa intent com um lote D — cobertura maior que os 17 nomes da lista fixa.
- **Status:** fechado — o teste ficou verde.

## BUG-200 — 204 intenções pinadas sem página, invisíveis atrás de um abort
- **Data:** 2026-08-30
- **Severidade:** GRAVE — lacuna editorial real, e ninguém podia vê-la
- **Sintoma:** só apareceu depois do BUG-198: `tools/verify_v2_writing_queue_closure.py` abortava no lote 42 e nunca chegava à checagem de completude.
- **Medição própria:** **39 lotes pinados com 204 intenções sem página**. Os maiores: `criminal-w3-05` (22, shard ausente), `tributario-w3-03` (22), `familia-w3-05` (18), `bancario-w3-06` (14), `consumidor-w3-11` (14), `servidor-w3-04` (13), `saude-w3-05` (9), `transito-09` (9). Há também shards parciais: `seguros-09` pina 19 e tem 17, `seguros-10` faltam 5, `imobiliario-29` faltam 5, `procedimentos-17` faltam 5.
- **E não confundir com os 912:** esses outros são intents de portfólio **já escritos fora deste inventário** (ondas `-w3`, `*-derivada-01`, `diarios-municipais-01`, `noticias-oficiais-01`). O empacotador canônico confirma: `orfaos_ja_escritos_fora_do_inventario: 912`, `novos_lotes: 0`, "nada a empacotar: todo intent de portfólio tem dono ou página". Por isso a régua de cobertura passou a ser a dele — **dono no inventário OU página escrita**, com o intent presente no shard, não só o arquivo existindo.
- **Status:** ABERTO, com número. `TestWritingMassTodoClosesCanonicalInventoryAgainstLiveShards` fica vermelho por razão VERDADEIRA e entra na baseline como dívida nomeada: são 204 páginas a redigir pelo pipeline sancionado (`ops/relaunch-writing.sh` → `writing-mass-todo.js`), não um defeito de detector.

## BUG-194 — três testes de portfólio congelavam um NÚMERO, e o número escondia o defeito
- **Data:** 2026-08-30
- **Severidade:** GRAVE — o vermelho era do teste, e ele mascarava dado editorial errado
- **Sintoma:** `TestAereoPortfolioCompletionMatchesFinalizedShards` (`expected 138, got 196`), `TestInsurancePortfolioUsesCurrentInsuranceLaw` (`got=242 want=160`) e `TestTelecomPortfolioCurrentRGCCompletion` (`expected 202, got 243`).
- **Causa raiz, e ela é dupla:**
  1. **Escopo errado.** O de aéreo lia **um** portfólio (`aereo.jsonl`) contra **nove** shards (`aereo-01..09`). Medido: a área tem **três** portfólios (219 registros) e **28** shards (203 páginas). O teste enxergava um terço do assunto.
  2. **Igualdade exata onde cabia piso.** O acervo cresce por construção; um número congelado transforma todo crescimento legítimo em vermelho. O que o teste precisa proteger é PERDA.
- **Correção:** escopo por glob, contagem vira piso, e a régua passa a ser a invariante que o nome do teste promete — página ATIVA e registro de portfólio se correspondem 1:1. Registro marcado `needs_source_research` é pendência declarada; registro cuja página foi PULADA com razão no shard também não exige página (a intenção foi processada e desduplicada).
- **E o dado estava mentindo em 16 registros:** medido com a régua nova, 4 registros de aéreo, 5 de seguros e 7 de telecom **se diziam prontos e não tinham página em shard nenhum** — nem ativa, nem pulada. `tools/generate-portfolio-pendencia-declarada-20260830` marcou os 16 como `needs_source_research`, que é o que eles de fato são. O gerador **não escreve página nem inventa fonte**: corrige a afirmação.
- **★ O QUE O NÚMERO ESCONDIA, e só apareceu depois:** com as contagens fora do caminho, os testes de seguros e telecom passaram a acusar o defeito real — `seg-prestamista-venda-casada` sem a dica `cdc-art-39-i-venda-casada`, `tel-multa-fidelidade-quando-vale` sem `cdc-art-46`, e a família DPVAT com 15 intenções contra as 13 nomeadas. São dados editoriais faltando, e agora estão visíveis em vez de somidos atrás de um "got=242 want=160".
- **★ E o próprio gerador de baseline tinha um buraco, achado aqui:** eu passei a ele o log do COMMIT, que o pre-commit imprime com `tail -n 25`. Ele aceitou o log truncado e gravou **4** dos **21** vermelhos reais de `internal/contract/misc` — e o commit seguinte reprovou 17 testes como "regressão" que sempre estiveram vermelhos. Baseline incompleto é pior que baseline nenhum: ele acusa quem não errou. `--do-log` passou a **recusar** log que contenha saída de hook (`pre-commit:`, `REPROVADO:`, `go-index-compile-closure:`), dizendo para rodar `go test` direto.
- **Nota de rastreabilidade:** os três shards com as 16 pendências declaradas entraram em `4b06e544`, cuja mensagem diz "os ledgers do período" — eu não os incluí no pathspec do commit da correção e eles caíram no seguinte. Reescrever histórico é pior que a imprecisão; fica o ponteiro.
- **Status:** parcial — o de aéreo ficou verde; os de seguros e telecom seguem abertos, agora acusando o defeito editorial real em vez da contagem.

## BUG-224 — a evidência de forma de texto é INGRAVÁVEL por desenho: o gerador valida antes de persistir, e a régua compara duas populações diferentes

- **Data:** 2026-08-30
- **Severidade:** GRAVE — três gates de release reprovam de forma permanente e o número piora a cada rascunho novo. A prescrição impressa pelo próprio gate é inexecutável, que é a classe de defeito do BUG-056.
- **Sintoma:** `./tools/go-modern run ./cmd/check ptbr-text-shape-release` → `EXIT=1`, `ptbr_text_shape_release_live_metrics_stale: total_sentence_count live=198280 evidencia=197037; corrigir com ./tools/generate-ptbr-text-shape-release`. Rodar o conserto que a mensagem manda rodar **não altera um byte**: `git diff --stat -- data/ops/ptbr_text_shape_release_evidence.jsonl` volta vazio e a evidência segue em 197037.

- **Mecanismo, provado linha a linha:**
  1. `internal/ptbrtextshaperelease/release.go:504` — `record.ReleaseShapeReady = record.InputRecords >= effectiveMinimumRecords(root) && …`
  2. `record.InputRecords` conta o corpus **`refined_public_prose.jsonl`** (7.959).
  3. `effectiveMinimumRecords(root)` → `authorialmassstock.EffectiveReleaseMinimum` → `stock_manifest.drafts_expected`, que conta **`authorial_mass_drafts.jsonl`** (7.972).
  4. `7959 >= 7972` é falso ⇒ `ReleaseShapeReady=false` ⇒ `GenerateEvidence` devolve report reprovado (`ptbr_text_shape_release_not_ready: records=7959 issues=0` — repare em **issues=0**: não há defeito de forma nenhum).
  5. `cmd/generate-ptbr-text-shape-release/main.go:59` — `os.Exit(1)` no report reprovado, **antes** do `WriteEvidence` da linha 67. A evidência nova, já calculada em memória, é descartada.
  6. Logo a evidência de 2026-08-05 nunca é substituída, e o gate reprova por `live_metrics_stale` para sempre.

- **A régua compara duas populações distintas, e a coincidência aritmética esconde isso.** 7972 − 7959 = 13 parece "faltam 13 registros a gerar". Medido por `unique_intent_id`, os conjuntos divergem em **455 elementos**:

  | conjunto | tamanho |
  |---|---|
  | `drafts` (a régua) | 7.972 |
  | `refined` (o que é contado) | 7.959 |
  | `drafts \ refined` | **234** (todos publicados, todos `authorial_mass_draft_blocked`) |
  | `refined \ drafts` | **221** |
  | `drafts ∩ refined` | 7.738 |
  | `refined` que está publicado | 7.959 / 7.959 (100%) |

  `refined` não é subconjunto nem superconjunto de `drafts`. Gerar 13 registros deixaria o gate verde **sem que a medição passasse a significar coisa alguma** — verde por coincidência é a fraude operacional que o contrato proíbe.

- **É a terceira ocorrência do elo insatisfazível herdado da DEC-017**, e as duas anteriores estão registradas com este nome: a DEC-024 (“Causa raiz — elo insatisfazível herdado da DEC-017”, detector de promessa de resultado) e a DEC-018 (“elo insatisfazível, não gate”). O padrão é sempre o mesmo — a DEC-017 desligou a reescrita mecânica do `refined` **corretamente**, e o consumidor a jusante não foi recalibrado junto. Aqui o consumidor é a régua de prontidão de três gates de release.

- **Mesma régua, mesmo defeito, em dois outros pontos:** `internal/ptbrwordfreqquality/quality.go:46` (`ptbr-wordfreq-quality: ptbr_wordfreq_minimum_records_missing: records=7959 minimum=7972`) e `languagetool-quality-release`, cujo `fail_closed` alcança 3.627 registros. Os oito artefatos-oráculo congelados em 7.959 saem todos da mesma data de geração (`refined_public_prose_generation_witness.json`: `generated_at=2026-08-05T22:39:42Z`, `records=7959`).

- **O que NÃO é defeito, medido para não virar correção por zelo:** `ptbr-lexical-diversity`, `ptbr-ftfy-unicode-oracle`, `languagetool-quality` e `simplemma-ptbr-lemma-audit` passam (`EXIT=0`) com a mesma evidência de 7.959 — cada um tem régua própria e nenhum cruza as duas populações. Regenerá-los seria churn.

- **Reprodução:**
  ```bash
  ./tools/go-modern run ./cmd/check ptbr-text-shape-release   # EXIT=1, live=198280 evidencia=197037
  ./tools/generate-ptbr-text-shape-release                    # EXIT=1, not_ready records=7959 issues=0
  git diff --stat -- data/ops/ptbr_text_shape_release_evidence.jsonl   # vazio: nada foi gravado
  ```

- **Status:** fechado (commit `8b35ac6e42fa484c4105e4a76caf8d9bd380b54d`) — a causa-raiz estava em `release.go:504` (régua cruzada) e `main.go:59` (o exit antes do `WriteEvidence`). Passou pela refutação adversarial antes da edição, e ela derrubou o escopo original de dois consumidores para os oito medidos; o fecho completo está mais abaixo.

### BUG-224 — medições complementares de 2026-08-30 (não alteram a causa-raiz; ampliam o alcance)

- **São QUATRO gates vermelhos pela mesma régua, não dois.** O quarto se identifica sozinho, porque a mensagem dele nomeia a camada que conta: `vale-public-prose-lint: vale_public_prose_lint_input_invalid: records=7959 minimum=7972 layer=data/editorial/refined_public_prose.jsonl` (`internal/valepublicproselint/valepublicproselint.go:641`). Os outros três: `ptbr-text-shape-release`, e os dois códigos de `ptbr-wordfreq-quality`.

- **Os dois códigos do `ptbr-wordfreq-quality` têm a MESMA causa**, contra a hipótese de que fossem defeitos irmãos. `quality.go:165` recomputa o registro com `MinimumReleaseRecords: effectiveMinimumRecords(projectRoot)` = 7972; `:208` compara e emite `minimum_records_missing`; `:207` chama `ValidateEvidenceRecord` sobre **esse mesmo registro recomputado**, e a linha 295 emite `metrics_invalid` pela primeira das cinco condições. Sobre o registro GRAVADO (`min=7959`, `text_fields_scanned=98875`, `record_with_tokens=7959`, 38 de 38 campos presentes) nenhuma das cinco condições dispara — conferido campo a campo.

- **Os CINCO consumidores de `authorialmassstock.EffectiveReleaseMinimum` contam o mesmo corpus refined**, e nenhum conta os drafts de onde sai o piso: `internal/jsonlstream/stream.go:223`, `internal/sqlitefts5corpus/fts5.go:142`, `internal/valepublicproselint/…:641`, `internal/ptbrwordfreqquality/quality.go:46`, `internal/ptbrtextshaperelease/release.go:504`. A fórmula é idêntica nos três primeiros que a encapsulam: base `DefaultMinimumRecords = 10000`, rebaixada pelo efetivo. A DEC-014 criou esse rebaixamento para destravar o piloto v2 "sem afrouxar produção", sob a premissa de que o manifesto descreve o MESMO conjunto que os gates contam. **A premissa quebrou quando `drafts` (7.972) passou `refined` (7.959).**

- **Hipótese própria levantada e REFUTADA pela medição — fica registrada porque custou investigação e porque a refutação vale por si.** O único commit a tocar `internal/ptbrtextshaperelease/` desde a evidência (`3f621e06`, de 2026-08-26) trocou o decoder JSON em três pontos: `jsoncodec.UnmarshalIterator` (json-iterator, arquivado no upstream desde 2024) → `jsoncodec.Unmarshal` (goccy). Como o corpus é byte-idêntico e a contagem mudou em 1.243 sentenças, o decoder era o suspeito natural. Construí `cmd/diag-jsoncodec-parity` (commit `4f868138`) e medi:

  | arquivo | linhas | divergentes |
  |---|---|---|
  | `refined_public_prose.jsonl` | 7.959 | **0** |
  | `authorial_mass_drafts.jsonl` | 7.972 | **0** |
  | `authorial_mass_legal_editorial_reviews.jsonl` | 7.959 | **0** |
  | `authorial_mass_legal_signatures.jsonl` | 7.959 | **0** |
  | `authorial_mass_candidate_selection.jsonl` | 10.000 | **0** |

  **35.890 linhas, zero divergências, zero erros nos dois decoders.** A migração dos 18 call sites está provada segura sobre o acervo real, e a causa das 1.243 sentenças não é o parser. A hipótese sobrevivente é que a evidência de 2026-08-05 foi medida sobre um checkpoint intermediário — o witness registra `checkpoint_flushes=7` e `checkpoint_durable_records=7959`, e o corpus só ficou completo no flush final.

- **Nono artefato da família, achado ao completar a varredura:** `data/ops/vale_public_prose_lint_evidence.jsonl` (`input_records=7959`). A varredura anterior lia `git ls-files … | head -400` sobre **420** arquivos e perdia 20 em silêncio — o truncamento em si é a lição.

- **Achado lateral, aberto como BUG-225:** `sqlite-fts5-corpus-evidence` passa **verde** com `input_records=590` e `checked_at=2026-07-10`, sobre um corpus de 7.959. Mesma fórmula de mínimo dos outros três; o verde não vem de o corpus estar coberto.

## BUG-225 — o gate do índice FTS5 está verde com uma evidência de 590 registros sobre um corpus de 7.959

- **Data:** 2026-08-30
- **Severidade:** MÉDIA a apurar — não bloqueia release; o risco é conforto falso, que é a R2 do contrato do dado real ("gate verde não é prova").
- **Sintoma:** `./tools/go-modern run ./cmd/check sqlite-fts5-corpus-evidence` → `EXIT=0, pass`. A evidência que ele valida (`data/ops/sqlite_fts5_corpus_evidence.jsonl`) traz `evidence_id=sqlite-fts5-corpus-evidence-2026-07-10`, `input_records=590`, `checked_at=2026-07-10`, enquanto `data/editorial/refined_public_prose.jsonl` — a `SourceRelPath` do próprio pacote — tem **7.959** registros.
- **Por que chamou atenção:** o pacote usa a MESMA fórmula de mínimo dos três gates vermelhos do BUG-224 (`fts5.go:142`, base `DefaultMinimum` rebaixada por `EffectiveReleaseMinimum`). Se a régua fosse aplicada ao que a evidência declara, 590 < 7.972 reprovaria. O verde indica que a validação não alcança essa comparação.
- **O que falta medir antes de corrigir:** se os 590 são amostra deliberada (e então o defeito é o gate se dizer cobertura) ou congelamento (e então é a mesma família do BUG-224). **Não se conclui sem ler `Validate` do pacote** — e não se "corrige" elevando o número sem entender qual das duas é.
- **Status:** fechado (commit `4fb203b9`) — o sintoma media aqui era real e maior do que parecia: o indice FTS5 cobria 590 de 7.959 registros. A causa era a validacao auto-referente, e a decisao que faltava (amostra deliberada ou congelamento) foi respondida pela regeneracao: congelamento. O fecho completo esta mais abaixo.

### BUG-225 — causa provada em 2026-08-30: a validação do registro gravado é AUTO-REFERENTE

`internal/sqlitefts5corpus/fts5.go:305` é a mesma linha que `internal/ptbrwordfreqquality/quality.go:295`:

```go
if record.InputRecords < record.MinimumReleaseRecords ||
   record.MinimumReleaseRecords < authorialmassstock.EffectiveMinimumForTotal(record.InputRecords) { … }
```

`EffectiveMinimumForTotal` é a variante **pura**, e ela é alimentada com `record.InputRecords` — o próprio campo que se quer validar. Com o registro gravado (`input=590`, `minimum=590`), `EffectiveMinimumForTotal(590)` devolve 590 (porque 590 < `TargetTotalContents`), e a aritmética fica:

- `590 < 590` → falso
- `590 < 590` → falso

**Nenhuma condição dispara, e nenhuma disparia com qualquer outro número** — 590, 59 ou 5 passam igual, desde que `minimum == input`. A cobertura não é medida: o registro atesta a si mesmo.

Por que o `ptbr-wordfreq-quality` reprova com a MESMA linha: ele não valida só o registro gravado. `quality.go:165` **recomputa** o registro contra o corpus vivo, gravando `MinimumReleaseRecords = effectiveMinimumRecords(projectRoot)` = 7.972 (dos drafts), e é sobre esse registro recomputado que a validação roda. O FTS5 não recomputa — por isso fica verde com a evidência de 2026-07-10.

**Isto fixa o critério de desenho para a correção do BUG-224:** a régua não pode ser a população cruzada (os drafts, o defeito de hoje) **nem** o próprio campo do registro (circular, o defeito daqui). Tem de ser uma atestação **independente** da mesma população que o gate conta.

- **Status:** causa provada. A correção entra junto com a do BUG-224, porque é o mesmo critério de desenho.

### Achado registrado para não se perder: `vale-public-prose-lint-release` tem DOIS defeitos, não um

O gate emite dois códigos, e só o primeiro é o BUG-224:

1. `vale_public_prose_lint_input_invalid: records=7959 minimum=7972 layer=data/editorial/refined_public_prose.jsonl` — a régua cruzada.
2. `vale_public_prose_lint_alerts_present: alerts=140 errors=140` — **140 erros de prosa pública**, vindos de uma evidência com `checked_at=2026-06-25`, de dois meses atrás. A evidência guarda só a contagem (`alert_count`, `error_count`), não a lista, então saber o que são exige rodar o Vale sobre o corpus.

Corrigir a régua **não** fecha o item 2, e dizer que fecha seria a "família fechada" prematura que o contrato proíbe. Fica nomeado como frente própria.

### BUG-224 — CORREÇÃO DE ATRIBUIÇÃO: as 1.243 sentenças vieram do BUG-190, não de checkpoint intermediário

A hipótese registrada acima — "a evidência de 2026-08-05 foi medida sobre um checkpoint intermediário" — está **ERRADA**, e a refutação adversarial a derrubou com dois campos do próprio artefato: o `input_fingerprint_sha256` da evidência é o hash do corpus vivo, e `checkpoint_durable_records == records == 7959`. A evidência foi medida sobre o corpus FINAL.

A causa real é o commit **`8ed85a27`, de hoje 2026-08-30 04:38** — o fecho do **BUG-190**, desta mesma caçada: `ptbrtext.shouldJoinNextSentence` decidia por `strings.HasSuffix` contra a lista de abreviaturas, e a lista traz **`"al."`**, de *et al.* Como `HasSuffix` não conhece fronteira de palavra, toda frase terminada em `-al` era fundida com a seguinte — e o português jurídico vive disso: *proporcional.*, *contratual.*, *judicial.*, *legal.*, *social.* A correção passou a exigir separador antes da abreviatura, o segmentador voltou a reconhecer essas fronteiras, e a contagem subiu de 197.037 para 198.280.

**A evidência não está errada: está obsoleta.** Ela é correta para o segmentador antigo e inválida para o novo. Isto reforça o diagnóstico em vez de enfraquecê-lo — o `live_metrics_stale` está certo em acusar, e o defeito continua sendo que o artefato **não pode ser regravado** enquanto a régua cruzada bloquear o gerador.

**Lição de método, registrada porque foi paga:** a hipótese do checkpoint era plausível e eu já a tinha commitado. O que a derrubou não foi releitura do meu raciocínio, e sim `git log` do período entre a evidência e a medição. Série congelada se lê cruzada com o log de commits, do mesmo jeito que série temporal se lê cruzada com o ledger de eventos.

### BUG-224 e BUG-225 — CORRIGIDOS em 2026-08-30: o piso passa a vir da população que o oráculo conta

**A correção, em uma frase:** oito oráculos que medem `data/editorial/refined_public_prose.jsonl` deixaram de tirar o piso de registros do `stock_manifest.drafts_expected` — que conta outra população — e passaram a tirá-lo da atestação que o produtor do corpus grava, conferida contra o corpus em disco.

**Por que não bastava trocar por qualquer coisa.** As duas saídas óbvias estão erradas, e cada uma é um dos dois bugs:

- o piso dos **rascunhos** é população cruzada (BUG-224): 455 elementos de divergência, e o número cresce a cada rascunho novo enquanto o corpus está congelado pela DEC-017;
- o piso do **próprio corpus** é circular (BUG-225): `records >= records` nunca reprova, que é como `sqlite-fts5-corpus-evidence` passava verde com uma evidência de 590 registros.

Por isso o piso vem de `internal/refinedcorpusfloor`, que lê a atestação do produtor e **falha fechada** — devolvendo o piso de produção, que reprova — em seis situações, cada uma com teste nomeado: testemunho ausente; testemunho malformado; contagem atestada não positiva; corpus truncado depois de testemunhado; corpus inflado depois de testemunhado; e corpus editado in place com o mesmo tamanho, que só o digest apanha. A comparação de registros é por **igualdade estrita**, nunca `>=`: acréscimo não atestado é tão desconhecido quanto truncamento.

O digest usa a fórmula do **produtor** (soma sobre os bytes do arquivo), não a do fingerprint interno do gate (hash de linhas normalizadas). São fórmulas diferentes sobre os mesmos bytes, e compará-las divergiria sempre — um controle que nunca casa é um controle desligado.

**Escopo: oito consumidores, medidos, não os dois que eu ia corrigir.** A refutação adversarial derrubou o escopo original. Trocados os que medem o refined **exclusivamente**: `ptbrtextshaperelease`, `ptbrwordfreqquality`, `valepublicproselint` (os três vermelhos), mais `sqlitefts5corpus`, `ptbrconfusables`, `ptbrftfyoracle`, `ptbrlexicaldiversity`, `ptbrunicodequality` (cinco vermelhos latentes — reprovariam na primeira regeneração).

**Ficaram de fora, e isto não é adiamento:** `jsonlstream` (4 camadas), `publicproselanguagepatterns` (2) e `scaledcontentreleaseverdict` (13 camadas, e ali a função é **gatilho de exigência de oráculo**, não piso — trocá-la poderia PULAR oráculo exigido, que é falso-verde). Nesses três o piso derivado dos rascunhos pode estar certo para as outras camadas, e trocar sem medir seria repetir o erro que este bug documenta.

**Resultado medido:**

| gate | antes | depois |
|---|---|---|
| `ptbr-text-shape-release` | EXIT=1 `live_metrics_stale` | **EXIT=0 pass** |
| `ptbr-wordfreq-quality` | EXIT=1 (2 códigos) | **EXIT=0 pass** |
| `vale-public-prose-lint` | EXIT=1 `input_invalid` | **EXIT=0 pass** |
| `ptbr-lexical-diversity` | EXIT=0 | EXIT=0 (sem regressão) |
| `ptbr-ftfy-unicode-oracle` | EXIT=0 | EXIT=0 (sem regressão) |
| `sqlite-fts5-corpus-evidence` | EXIT=0 | EXIT=0 (sem regressão) |
| `languagetool-quality` | EXIT=0 | EXIT=0 (sem regressão) |
| `simplemma-ptbr-lemma-audit` | EXIT=0 | EXIT=0 (sem regressão) |

**A prova de que o deadlock morreu:** `./tools/generate-ptbr-text-shape-release` — o conserto que a mensagem do gate mandava rodar e que saía com exit 1 sem gravar um byte — agora sai `status=pass` e **grava**. A evidência passou de `ptbr-text-shape-release-2026-08-05` (197.037 sentenças, do segmentador anterior ao BUG-190) para `ptbr-text-shape-release-2026-08-30` com **198.280** e `release_shape_ready=true`.

**Custo medido:** o piso lê o corpus inteiro uma vez para somar digest e contar registros — 0,90 s para os 86 MB, com cache por processo indexado em tamanho e mtime, invalidado por qualquer escrita (há teste para isso).

**Os oito pacotes estão FORA do grafo do validador de `internal/v2ingest`** — conferido antes de commitar, porque re-atestação por engano já custou 452 s e 524 s de suíte nesta caçada.

**★ O QUE ESTA CORREÇÃO NÃO FEZ, e a primeira redação deste fecho afirmava que sim.** Escrevi aqui que "o piso circular sumiu do `sqlitefts5corpus`". É falso, e a revisão apanhou antes do commit. A troca alcançou o piso de **geração** — a linha que decide quanto exigir ao PRODUZIR a evidência. A linha **auto-referente da validação** continua exatamente onde estava, em três lugares:

- `internal/sqlitefts5corpus/fts5.go:309`
- `internal/ptbrwordfreqquality/quality.go:299`
- `internal/ptbrtextshaperelease/release.go:578`

Todas ainda alimentam `authorialmassstock.EffectiveMinimumForTotal` com `record.InputRecords`, o próprio campo que deveriam validar. Logo a evidência de 590 registros do FTS5 **continua validando verde pela mesma circularidade**, e o `EXIT=0` que a tabela acima registra como "sem regressão" é, nesse gate, o mesmo verde de conforto falso do BUG-225. A correção do BUG-224 não fica menor por isso; a frase é que estava grande demais.

Fechar a circularidade de verdade exige levar a raiz do projeto até uma função hoje **pura** (`ValidateEvidenceRecord` recebe só o registro), o que muda assinatura pública e é escopo próprio — não embarca de carona nesta correção.

- **Status:** BUG-224 **corrigido**. BUG-225 **parcial**: o piso de geração deixou de ser circular, a linha de validação permanece e está nomeada acima, e segue por decidir na medição se os 590 registros de 2026-07-10 são amostra deliberada ou congelamento.

### Achado nomeado: `languagetool-quality-release` — o `fail_closed` é por registro, e são 45,6% do corpus

Medido em 2026-08-30 sobre `data/ops/languagetool_quality_evidence.jsonl`: **7.959 registros de evidência** (um por página do corpus refinado), dos quais **3.627 com `fail_closed=true`** — e o conjunto com `blocker_count > 0` é **exatamente o mesmo 3.627**. Os dois códigos que o gate emite (`languagetool_quality_release_fail_closed` e `..._blockers_present`, `internal/languagetoolquality/batch.go:2077` e `:2080`) percorrem `records` e acusam registro a registro, então o "3.627" não é uma contagem de páginas defeituosas apurada agora: é o número de páginas cuja verificação ficou **fechada por segurança** quando a evidência foi gerada.

Isso **não** é a régua do BUG-224 — a correção do piso não toca nisso, e o gate `languagetool-quality` (sem `-release`) já passava e continua passando. Fica registrado com o mecanismo localizado para que a frente seja aberta sabendo que o alvo é *por que 45,6% do corpus ficou fail-closed*, e não "corrigir 3.627 páginas".

### Contraexemplo do BUG-224, achado ao procurar a quarta instância: o gerador do spellcheck faz certo

Ao fechar o BUG-224 ficou a suspeita de que "validar antes de persistir" fosse padrão do repositório. Procurei a quarta instância em `cmd/generate-ptbr-spellcheck-evidence/main.go` e **não é** — ele resolve o mesmo problema pelo caminho certo, e vale registrar porque é o modelo a copiar:

```go
if !report.Passed() {
    printMessages(stderr, report.Messages())
    if !*dryRun && shouldWriteFreshBlockedEvidence(record) {
        if err := ptbrspell.WriteRecords(*root, record); err != nil { … }
    }
    return 1
}
```

A evidência **é gravada mesmo com o report reprovado**, desde que seja fresca, e o comando ainda assim sai com `1`. Isso separa as duas coisas que o gerador do text-shape confundia: a evidência é um **fato medido** (quantos registros, quantas sentenças, quantos erros) e a prontidão é um **juízo sobre esse fato**. Recusar a gravação do fato porque o juízo é negativo congela o artefato exatamente quando ele mais precisa ser atualizado — e foi assim que a evidência de forma de texto ficou 25 dias presa, com o gate mandando rodar um gerador que não podia gravar.

### Spellcheck — evidência regenerada (869 → 824), e uma correção do meu próprio método

A evidência de `ptbr-spellcheck` estava em `checked_at=2026-06-26`. Regenerada hoje com a allowlist estendida: **`misspellings` caiu de 869 para 824**. O gerador gravou sem drama — `cmd/generate-ptbr-spellcheck-evidence` persiste a evidência fresca mesmo com o report reprovado, que é o contraexemplo registrado acima.

**★ E a regeneração provou que uma afirmação minha, já commitada, estava errada.** Eu escrevi que seis tokens do top — `ATPV`, `Adm`, `Apart`, `Bras`, `opt`, `munck` — tinham **zero ocorrência** no corpo público, e por isso não entraram na allowlist. A evidência nova traz os seis de volta no topo, com contagem 1–2. A medição que os dava como zero era minha, em Python, e estava errada por dois motivos:

1. **Campos a menos.** `internal/ptbrspell/ptbrspell.go:694` varre `PublicTitle`, `PublicMetaDescription`, `PublicH1`, `PublicSummary` e as seções. Eu medi título, resumo e seções — faltaram **meta description e H1**. Remedindo pelos campos certos, `munck` aparece em `public_meta_description`.
2. **Tokenização diferente.** Meu regex tratava o hífen como parte do token, então `"opt-in"` era um token só; o detector separa, e daí sai o `opt` que eu não via.

**A lição é a regra que o próprio plano desta caçada já registrava, e que eu não segui:** *a medição que origina a decisão tem de usar a MESMA função que o código usa, não uma reimplementação.* Custou uma afirmação errada em commit. Fica corrigida aqui, que é o que se pode fazer — a mensagem de commit não se reescreve.

**O que a regeneração revelou sobre o caminho certo, e por que a frente continua aberta:** o novo topo é `CAC`, `CDAs`, `CDBs`, `CIDs`, `CNAEs`, `CNDs`, `CG`, `Business` — Certidão de Dívida Ativa, CDB, CID, CNAE, Certidão Negativa de Débito. São **siglas em maiúsculas**, e o hunspell pt-BR não traz sigla nenhuma. Estender a allowlist termo a termo não escala para 824: a correção estrutural é o detector deixar de tratar sigla maiúscula como erro ortográfico, com teste de falso positivo sobre amostra real — e isso é calibração de detector, que merece a frente própria em vez de carona nesta.

### BUG-225 — FECHADO em 2026-08-30, e o falso verde escondia perda de cobertura REAL

A correção do BUG-224 tinha trocado apenas o piso de **geração** do `sqlitefts5corpus`; a linha auto-referente da **validação** ficou, e este fecho a resolve.

**Onde a conferência cabia, e por que não exigiu mudar assinatura pública.** `ValidateEvidenceRecord` é função pura e não enxerga o disco — por isso comparava `MinimumReleaseRecords` com `EffectiveMinimumForTotal(record.InputRecords)`, alimentada pelo próprio campo que deveria validar. Mas `Validate(root)` **tem** a raiz do projeto, e é lá que a cobertura passou a ser medida, contra `refinedcorpusfloor.Piso`. A função pura continua pura; nenhuma assinatura pública mudou.

**O que o falso verde escondia não era só conforto — era o índice de busca cobrindo 7,4% do acervo.** Com a conferência ligada, o gate acusou na hora:

```
sqlite_fts5_minimum_records_missing: input=590 piso=7959 layer=data/editorial/refined_public_prose.jsonl
```

A evidência era `sqlite-fts5-corpus-evidence-2026-07-10`, com `input_records=590` e `fts5_row_count=590`. O índice FTS5 do corpus estava construído sobre **590 de 7.959 registros** desde 10 de julho, e nenhum gate dizia nada porque o registro atestava a si mesmo. Regenerado: `sqlite-fts5-corpus-evidence-2026-08-30`, `input_records=7959`, `fts5_row_count=7959`, `build_ms=2973`, `rps=2677`, gate `pass`.

**Prova em par, como no BUG-224:** o teste RED (`TestValidateReprovaEvidenciaQueCobreMenosQueOCorpus`) foi visto vermelho com a mensagem "evidência de 10000 registros foi aceita sobre corpus de 20000", e o controle (`TestValidateAceitaEvidenciaQueCobreOCorpusInteiro`) garante que evidência que cobre o corpus inteiro continua passando — sem ele, a correção seria indistinguível de fazer o gate reprovar sempre.

**Quarta instância do padrão "valida antes de persistir", localizada:** `cmd/generate-sqlite-fts5-corpus-evidence/main.go:45-47` sai com `os.Exit(1)` antes do `Write` da linha 55. Aqui ela **não** travou, porque com o piso corrigido o `Generate` passa — mas o padrão está lá e é o mesmo do BUG-224. Fica nomeado com arquivo:linha.

- **Status:** fechado (`sqlite-fts5-corpus-evidence` EXIT=0, cobertura 7.959/7.959).

## BUG-226 — a régua de promessa de resultado existe DUAS vezes, e a cópia do Vale ficou na versão que a DEC-024 substituiu

- **Data:** 2026-08-30
- **Severidade:** GRAVE — é a divergência silenciosa entre dois detectores da MESMA regra de ética da OAB, e a cópia desatualizada é a que reprova o gate de release.
- **Medição:** `tools/vale-public-prose/styles/PortalJuridico/OABCTA.yml` é `extends: existence`, com 25 tokens literais (`resultado garantido`, `resultado certo`, `êxito garantido`, `ganho certo`…) e `level: error`. Substring cego sobre o texto inteiro.
- **E é exatamente o detector que a DEC-024 aposentou.** A decisão diz, com todas as letras, que "o detector de promessa de resultado do `internal/publicprosecandidate` **deixa de ser substring cego** sobre o campo inteiro e passa a classificar **por frase**, em três regras" — R1 (voz própria), R1b (primeira pessoa por colocação) e R2 (escape estreito por adjacência de negação ou atribuição a terceiro), com 9 entradas de allowlist por intent em código versionado e bateria adversarial de 10 frases que devem reprovar e 7 escapes legítimos.
- **O caso que a própria DEC-024 usou para fechar a questão seria acusado pela cópia do Vale:** `cons-clinica-prometeu-resultado-garantido`, página sobre o **art. 30 do CDC**, cujo tema É que publicidade de resultado garantido OBRIGA o fornecedor. Slug, H1 e abertura precisam nomear a promessa; o detector Go a libera pela R2, o `existence` do Vale não tem como.
- **Por que não se conserta escrevendo a exceção no Vale:** as regras do Vale compilam com o `regexp` do Go, que é RE2 e **não tem lookbehind**. A régua da DEC-024 depende de adjacência à esquerda (`sem resultado garantido`, `prometeu resultado garantido`) — não é expressável ali. Duas cópias com critérios diferentes divergiriam na primeira mudança, que é o defeito que a DEC-025 já nomeou ao recusar duplicar a fórmula das hubs.
- **Correção que a evidência aponta, e o que ela NÃO pode ser:** a fonte única da regra ética é `internal/publicprosecandidate/outcome_promise.go`, que já varre o corpus e tem os testes. O `OABCTA.yml` não pode simplesmente sumir — isso seria afrouxar ética, que o contrato proíbe sem exceção. A rota é ele deixar de ser `level: error` no gate de release (virando sinal, não veto) **enquanto** o detector canônico permanece fatal por R1/R1b sobre o lote inteiro. Como isto mexe em gate de ética OAB, vai a revisão antes da edição.
- **Status:** **refutado** — a rota descrita acima foi derrubada pela crítica adversarial antes da edição. A causa medida e localizada continua valendo como registro; o que caiu foi a conclusão de que havia duplicação nociva a resolver. A refutação completa, com os três erros de medição corrigidos, está mais abaixo.

### `languagetool-quality-release` — os 3.627 são blockers REAIS, e a maioria é do mesmo dicionário sem léxico jurídico

Correção de leitura: `fail_closed` **não** significa "não conseguiu verificar". `internal/languagetoolquality/batch.go:2365` define `FailClosed: evidence.FailClosed || evidence.BlockerCount > 0`, então os 3.627 registros `fail_closed` são, por construção, os mesmos 3.627 com blocker. A amostra confirma: `service_available=true`, `service_required=true`, `blocker_count=2`. Meu registro anterior dizia "verificação ficou fechada por segurança" — estava errado.

Medido sobre a evidência: **3.627 registros com blocker, 7.019 blockers somados.** Por regra:

| regra | ocorrências | o que é |
|---|---|---|
| `MORFOLOGIK_RULE_PT_BR` | 8.627 | "possível erro de ortografia" — **o mesmo dicionário sem léxico jurídico do `ptbr-spellcheck`** |
| `POR_QUE_PORQUE` | 3.521 | "por que" × "porque" |
| `PORTUGUESE_WORD_REPEAT_BEGINNING_RULE` | 1.618 | três frases seguidas começando igual |
| `DEPOIS_DE_APÓS` | 1.267 | sugestão de concisão |
| `VERB_COMMA_CONJUNCTION` | 783 | vírgula em locução |
| `NUMBER_ABREVIATION` | 782 | "n.º" em vez de "nº" |
| `ALTERNATIVE_CONJUNCTIONS_COMMA` | 656 | vírgula em conjunção alternativa |
| `PT_REDUNDANCY_REPLACE_AVISO_PRÉVIO` | 370 | **falso positivo certo:** chama "aviso prévio" de pleonasmo, e é o instituto do art. 487 da CLT e da Lei 12.506/2011 |
| `COLOCAÇÃO_ADVÉRBIO` | 360 | sugestão de estilo |

**Três classes distintas, e tratá-las como uma só é o erro:** falso positivo sobre léxico jurídico (`MORFOLOGIK`, `AVISO_PRÉVIO`), sugestão de **estilo** que não é erro (`DEPOIS_DE_APÓS`, `COLOCAÇÃO_ADVÉRBIO`, `PORTUGUESE_WORD_REPEAT_BEGINNING_RULE`) e erro gramatical de fato (`POR_QUE_PORQUE`, `VERB_COMMA_CONJUNCTION`, `GENERAL_NUMBER_AGREEMENT_ERRORS`). Só a terceira classe deveria bloquear release. O mecanismo de supressão por allowlist já existe (`batch.go:729`), então a correção é política de regra, não código novo.

### BUG-226 — a medição INVERTEU a rota: o problema não é o Vale duplicar, é o detector canônico ser mais curto

A primeira leitura deste bug dizia que a correção era "o `OABCTA.yml` deixar de ser `error`, porque o detector Go é a fonte única". **A medição derrubou isso**, e o registro fica porque a rota errada quase foi executada.

**Diff das duas listas**, normalizando acento e caixa:

| | tokens | 
|---|---|
| `OABCTA.yml` (Vale) | **44** |
| `outcomePromiseTerms` (Go, `public_prose_candidate.go:2371`) | **13** |
| cobertos pelo canônico | **9** |
| **só no Vale** | **35** |

E os 35 não são variantes: são **classes inteiras que o detector canônico não cobre**, e que o Provimento 205/2021 veda tanto quanto a promessa de resultado —

- **preço como chamariz** (CED art. 40): `honorários promocionais`, `honorários facilitados`, `honorários parcelados`, `parcelamento de honorários`, `desconto nos honorários`;
- **quota litis / captação**: `só paga se ganhar`, `paga se ganhar`, `pague se ganhar`;
- **promessa não coberta**: `indenização garantida`, `liminar garantida`, `vitória garantida`, `benefício garantido`, `ganho garantido`, `ganho certo`, `resultado certo`, `decisão favorável garantida`, `ressarcimento garantido`, `prazo garantido`, `atendimento garantido`, `advogado especialista garante`, `sem risco jurídico`;
- **urgência enganosa**: `liminar rápida`, `liminar urgente garantida`.

**Demover o `OABCTA.yml` removeria a única detecção automatizada dessas classes** — seria afrouxar ética, que o contrato proíbe sem exceção. A rota certa é a oposta: **levar os 35 termos ao detector canônico**, que os classificará por frase, e só então demover a cópia cega.

**O custo da ampliação foi medido antes de propô-la, e é baixo.** Os 35 termos produzem **7 hits** no corpus inteiro, em 3 termos — e os três são exatamente as construções que a R2 da DEC-024 libera:

| termo | intent | trecho | por que a R2 libera |
|---|---|---|---|
| `resultado certo` (3) | `cons-clinica-prometeu-resultado-garantido` | "publicidade de clínica **anunciou** resultado certo em tratamento e não cumpriu" | atribuição a terceiro — e é a página do **art. 30 do CDC**, o caso que a própria DEC-024 usou para fechar a questão |
| `prazo garantido` (3) | `dig-whatsapp-clonado-golpe-contatos` | "**não há** prazo garantido nem recuperação automática" | negação com elo da lista fechada |
| `ganho garantido` (1) | `inv-o-que-e-cvm` | "publicidade que **promete** ganho garantido em produto de risco" | verbo de atribuição a terceiro |

Nenhum é promessa em voz própria, então R1/R1b não disparam e o lote não reprova. **Os 7 hits são a prova do defeito, não obstáculo à correção:** é o substring cego do Vale acusando páginas que nomeiam a promessa para desmenti-la.

**E a rota "demover para warning" não funcionaria nem se fosse desejável:** `internal/valepublicproselint/valepublicproselint.go:670` reprova com `AlertCount > 0`, e `:730` exige `ErrorCount == AlertCount`. Rebaixar o nível trocaria o código de reprovação para `corpus_scan_invalid` sem mudar o exit.

- **Status:** aberto, rota invertida e custo medido; em refutação adversarial antes da edição, por ser gate de ética OAB.

## BUG-227 — o gerador do LanguageTool sobrescrevia a evidência completa por uma amostra de 200, em silêncio

- **Data:** 2026-08-30
- **Severidade:** CRÍTICA — perda silenciosa de artefato versionado. Não foi hipótese: aconteceu nesta sessão e exigiu restauração.
- **Como apareceu.** Depois de corrigir a regra `POR_QUE_PORQUE`, rodei `./tools/run-generate-supervised ./cmd/generate-languagetool-quality` para a evidência refletir a correção. O comando terminou com **EXIT 0** e imprimiu:

  ```
  languagetool-quality: records=200 persistent_cache_hits=0 live_check_budget=0
  live_check_miss_count=200 live_checks=200 live_budget_exceeded=0 require_service=false
  ```

  O `git diff --stat` contou o estrago: **`200 insertions(+), 7959 deletions(-)`**. A evidência de 7.959 registros — um por página do corpus — virou uma amostra de 200.

- **Causa.** `BatchOptions.RequireService` é **falso por padrão** (`batch.go:64`, usado em `:366` e `:477`). Com o serviço LanguageTool fora do ar, a ausência dele não interrompe nada: apenas encolhe a amostra viva. E `WriteEvidenceRecords` gravava o que recebesse, sem olhar o que já havia em disco. Fail-open num artefato de release.
- **O que salvou:** notei a redução no `git diff` antes do commit e restaurei com `git show HEAD:` — a forma sancionada, sem `checkout`. Commitada, a cobertura de **97,5% do corpus** teria sumido do repositório sem nenhum gate acusar, porque nenhum gate compara a evidência com a versão anterior.
- **Correção:** `WriteEvidenceRecords` passa a **recusar** gravar menos registros do que a evidência em disco já tem, com mensagem que diz os dois números e o que fazer. A redução continua possível quando é deliberada, por `PermitirReducaoDeCobertura` — o corpus pode legitimamente encolher; o que não pode é isso acontecer sozinho.
- **Prova empírica, o mesmo comando, depois da correção:**

  ```
  EXIT_REAL=1
  languagetool-quality: recusa de reducao de cobertura: a evidencia gravada tem 7959
  registros e a nova traz 200; rode com o servico LanguageTool disponivel, ou declare
  a reducao se o corpus encolheu de fato
  ```

  `git status` do arquivo: vazio. A evidência ficou intacta.

- **Três testes, um RED e dois controles:** o RED grava 3 sobre 12 e exige recusa **mais** a preservação das 12 linhas; o primeiro controle garante que cobertura igual ou maior grava normalmente (senão a guarda impediria toda regeneração legítima); o segundo garante que a redução declarada funciona.
- **A classe é a mesma do BUG-224, pelo avesso.** Lá o gerador se recusava a persistir um fato medido porque o juízo era negativo. Aqui ele persistia um fato pior sem perguntar. Os dois erram no mesmo ponto — a relação entre medir e gravar —, em direções opostas.
- **Status:** corrigido, com prova empírica do antes e do depois.

### BUG-226 — REFUTADO pela crítica adversarial, e com três erros meus de medição a corrigir

A rota que eu ia executar — levar os 35 termos ao detector canônico e depois demover o `OABCTA.yml` — **não sobrevive**. A refutação a derrubou com evidência do disco, e três números que escrevi acima estão errados. Ficam corrigidos aqui, porque comentário que mente é bug.

**Erro meu nº 1 — eram 20 hits, não 7, e a atribuição por página estava colapsada.** Meu script contava ocorrências do termo no corpo inteiro de cada registro e imprimia apenas o primeiro exemplo, então "`resultado certo` 3x em `cons-clinica-…`" era na verdade **três páginas diferentes**. O ledger vivo confirma 20: `vale_public_prose_lint_evidence.jsonl` traz `alert_check_counts["PortalJuridico.OABCTA"] = 20`. Eu tinha o número certo à mão, no artefato, e medi por fora.

**Erro meu nº 2 — duas das frases não escapariam pela R2, e uma delas é termo de arte.** As que eu não li:

- `emp-diferenca-empreitada-prestacao-servicos`: *"A empreitada é voltada a **um resultado certo** e delimitado"* — o token anterior é "um"; não há negação nem atribuição. É **obrigação de resultado na empreitada**, vocabulário doutrinário correto.
- `imob-sublocacao-valor-maior`: *"…eventual compensação **sem anunciar resultado certo**"* — o infinitivo "anunciar" **não está** em `outcomePromiseAttributionVerbs` (`outcome_promise.go:158-176`, só formas conjugadas), e "sem" a dois tokens não casa a R2a, que exige negação colada ou negação mais elo da lista fechada. Uma frase literalmente **anti**-promessa reprovaria.

E a consequência que eu não tinha visto: o classificador tem três consumidores (`outcome_promise.go:389-393`), um deles `publicproselanguagepatterns` sobre o mesmo corpus, cuja cadeia (`patterns.go:4959` → `:3458` → `:1300` → `:2074`) termina em `release_blockers_present` — e `public-prose-language-patterns-release` está no fan-in P0 (`internal/p0checkaliases/aliases.go`). **A minha rota introduziria 2 ReleaseBlockers num gate hoje limpo.**

**Erro meu nº 3 — "garantia de êxito" não é coberta pelo canônico.** Eu a contei entre os 9 cobertos. A lista tem **11** termos, não 13, e o comentário em `public_prose_candidate.go:2379` registra que "garantia de exito" **não entrou**, deliberadamente, pelas mesmas ocorrências legítimas. Pós-demoção ela ficaria com zero cobertura de corpo.

**E o que derruba a rota inteira: existe uma TERCEIRA cópia da lista.** `oabCTABlockedTokens` está hardcoded em `internal/valepublicproselint/valepublicproselint.go:62-107` e alimenta o scan **nativo** full-corpus. O ledger prova a proporção: **138 dos 140 alertas vêm do scan nativo**; o binário Vale só enxerga um shard-sentinela de 250 registros. Demover só o YAML não reduziria o `AlertCount` em nada — e **quebraria a geração da evidência**, porque o oráculo de estilo (`:842-846`) exige que todo token alerte como *error* na fixture, e `valeStyleOracleTokens()` (`:1213-1230`) inclui a lista Go.

**A rota também não atingiria o próprio objetivo.** `AlertCount = 140` é **120 `Boilerplate` + 20 `OABCTA`**. Zerar o OABCTA deixaria 120, e o gate reprova com `AlertCount > 0`. O vermelho do `vale-public-prose-lint-release` é RCA de outra frente (BUG-097/BUG-134), já documentada em `internal/legalmarketingpolicy/falso_positivo_acervo_test.go:9-40` — que mediu 44 páginas e 64 ocorrências no HTML servido, todas legítimas, e **avisa explicitamente contra "corrigir" as páginas**.

**E a cobertura que eu procurava já existe.** Desde o BUG-117 (2026-08-29), `checkLegalMarketingPolicy` roda `ValidateEditorialBody` sobre **todas** as páginas publicadas e indexáveis (`checks.go:6625-6685`), com janelas de contexto de 90/60 bytes (`legalmarketingpolicy/policy.go:530-571`), cobrindo 12 dos termos "só-Vale" (`editorialPromisePhrases`, `:491-507`) — num universo **maior** que o dos candidatos: as 10.116 servidas. E preço/quota-litis tem casa canônica própria em `containsMercantileCopy` + `ForbiddenPhrases` (`:613-702`), na superfície de CTA, onde o chamariz de fato vive; no corpo do corpus refinado esses termos dão **0 hits**.

**Conclusão: não há duplicação nociva a resolver — há três camadas com escopos distintos** (CTA, corpo servido, esteira de candidatos), e a leitura de "cópia desatualizada" era minha, não do repositório. O que sobra de real, e fica nomeado com o método:

1. Paridade na esteira de candidatos, se desejada, entra **termo a termo** com censo frase-a-frase de zero falso positivo — o método que o próprio comentário da DEC-024 descreve — e `resultado certo` provavelmente **não** entra, pela mesma razão registrada para "garantia de êxito": é termo de arte.
2. Preço e quota litis ficam em `legalmarketingpolicy`, nunca em `outcomePromiseTerms`.
3. Qualquer mudança no Vale move as **três** cópias juntas, com controle negativo nomeado.

- **Status:** **refutado.** A crítica adversarial impediu uma mudança que introduziria 2 ReleaseBlockers num gate P0 limpo, quebraria a geração da evidência e não fecharia o vermelho que motivou a investigação. O dado desta refutação não se descarta: é ele que documenta por que as três camadas existem.

## BUG-228 — o instalador do oráculo montava o LanguageTool na versão errada, na porta errada

- **Data:** 2026-08-30
- **Severidade:** MÉDIA, com efeito grave a jusante: é a razão pela qual a evidência do `languagetool-quality` estava congelada desde 2026-08-05 e pela qual o BUG-227 pôde acontecer.
- **Três defeitos no mesmo bloco de `ops/setup-oracle-tools.sh`:**

  1. **Versão errada.** O script baixava `https://languagetool.org/download/LanguageTool-stable.zip`, e o site publica **até a 6.6** — foi a 6.6 que ficou em `.toolchains/languagetool/LanguageTool-6.6/`. Mas `internal/languagetoolquality/batch.go:46` fixa `DefaultServiceVersion = "6.8"`, e a evidência gravada registra `service_version = 6.8`. A **6.8 é distribuída pelo Maven Central**, não pelo zip — e já estava baixada em `.toolchains/m2/org/languagetool/`, com `languagetool-server-6.8.jar` e `language-pt-6.8.jar`. Quem seguisse o script subiria a 6.6 e geraria evidência que não casa com o contrato, com o gate reprovando sem dizer que a causa era a versão.
  2. **Porta errada.** O script documentava `--port 8081`; `internal/languagetoolquality/languagetoolquality.go:108` procura `http://localhost:8082/v2/check`. O serviço subia e o gerador nunca o encontrava.
  3. **O silêncio que amarra tudo.** Sem o serviço, `generate-languagetool-quality` **não falha** — `RequireService` é falso por padrão. É o BUG-227: ele grava uma amostra reduzida por cima da evidência boa. O script não avisava disso.

- **Correção:** o bloco passa a montar o classpath a partir do `.toolchains/m2` (versão 6.8, a que o código exige), documentar a porta **8082**, avisar quando o jar 6.8 estiver ausente, e dizer explicitamente que sem `--require-service` o gerador grava amostra reduzida em silêncio. Comando que funciona, verificado nesta sessão:

  ```bash
  CP=$(find .toolchains/m2 -name '*.jar' | tr '\n' ':')
  java -cp "$CP" org.languagetool.server.HTTPServer --port 8082
  ```

  223 jars no classpath, servidor de pé em ~20 s, `HTTP 200` em `/v2/languages` e resposta em `/v2/check`.

- **Uma suspeita minha que a verificação derrubou antes de virar registro errado:** ao ver 404 em `LanguageTool-6.8.zip` e a listagem do site parando na 6.6, ia registrar que a constante apontava para uma versão inexistente — a classe "prescrição inexecutável" do BUG-056. O Maven Central desmente: a 6.8 existe, está publicada e **já estava no disco**. O defeito era o canal de instalação, não a constante.
- **Status:** corrigido no script; a regeneração da evidência com o serviço 6.8 de pé é a verificação final.

## Re-triagem dos NOVE críticos do plano — medida em 2026-08-30, com o comando de cada veredito

O plano lista nove críticos "vivos", medidos em 2026-08-29. Remedidos hoje, **oito caíram** e o nono é inexequível pelo caminho que a prescrição indica. O Passo Zero existe para isto: reproduzir antes de corrigir, e mandar para os refutados o que já morreu.

| # | crítico | veredito | comando / evidência |
|---|---|---|---|
| 1 | `cmd/build public` reprova com 261 achados em 29 rotas | **morto** | build isolado desta sessão: `generated_pages=10136 indexable_pages=10351`, **`achados=0`**, e o deploy passou nos 7 passos |
| 2 | FAMÍLIA-A: `check-edge-cache-coverage` publica `universo_urls=18731` | **morto** | `data/ops/edge_cache_coverage.jsonl` → **`universo_urls = 10312`** |
| 3 | CVE `GO-2026-5932` em `x/crypto v0.55.0` | **vivo, prescrição inexequível** | `go list -m -versions golang.org/x/crypto` termina em **v0.55.0** — a versão instalada. Não há release corrigida publicada; "subir a versão" não tem para onde subir |
| 4 | `tools/go-build-check:46` usa `./...` e nunca verificou nada | **morto** | as três ocorrências de `./...` no arquivo (linhas 5, 8, 16) são **comentário** explicando por que ele NÃO usa o padrão |
| 5 | `googlebot-smoke` valida o próprio cache em `/tmp` fixo | **morto** | `checks.go:6892` → **`os.MkdirTemp("", "portaljuridico-googlebot-smoke-cache-")`**, diretório único por execução; o comentário de `:6890` documenta o defeito antigo |
| 6 | `public-release-transaction`: 59.388 erros de `source_type`/`use_in_content` | **morto** | `./tools/go-modern run ./cmd/check public-release-transaction` → **EXIT=0, `pass`** |
| 7 | `GOAL.md` declara `published_manifest=0` como regra que prevalece | **morto no essencial** | os seis parágrafos carregam `CONTADORES VENCIDOS` com a medição de 2026-08-29 **no próprio parágrafo**. Restava a referência de linha do aviso, que apontava para 77/81/83/85 quando os parágrafos já estavam em 106–118 — corrigida hoje |
| 8 | autolinker: URN do art. 24-A inexistente em `/glossario/qualidade-de-segurado/` | **morto** | a página servida emite `urn:lex:br:federal:lei:1991-07-24;8213!art27a` — art. 27-A, o correto |
| 9 | `ValidateEditorialBody` é código morto | **morto** | `checks.go:6678` a **chama**, dentro de `checkLegalMarketingPolicy`, sobre as páginas publicadas e indexáveis; `:6633-6634` documenta que era código morto e deixou de ser (BUG-117) |

**Sobre o nº 3, o único que resiste.** A prescrição do plano é "subir a versão do `x/crypto`", e a listagem do próprio módulo termina na versão afetada. É a classe de defeito que o plano nomeia no BUG-056 — prescrição inexecutável que ninguém tentou executar. O que cabe aqui é medir se o repositório alcança o caminho vulnerável, não fingir um bump que não existe; fica registrado com o comando que o comprova, e não como "pendência a fazer depois".

### Crítico 3 (CVE `GO-2026-5932` em `x/crypto`) — medido até o fim: não alcançável, e sem correção upstream

O plano manda "subir a versão do `x/crypto`". Medido hoje, **não há para onde subir**: `./tools/go-modern list -m -versions golang.org/x/crypto` termina em **v0.55.0**, que é a versão instalada (`go.mod:128`, `// indirect`).

Mas a pergunta que importa não é a versão — é o **alcance**. E o próprio repositório já a respondeu, com execução ao vivo. `data/ops/sca_govulncheck_evidence.jsonl`, registro `sca-govulncheck-2026-08-29T14:36:05Z` (`executed_live: true`, 18,4 s, base `vuln.go.dev` atualizada em 2026-08-28):

```json
{"osv": "GO-2026-5932", "module": "golang.org/x/crypto", "found_version": "v0.55.0",
 "fixed_version": "", "reachable_call": false, "upstream_has_no_fix": true}
```

com `reachable_findings_count: 0`, `module_graph_only_findings_count: 1` e `scan_scope: ["./internal/...", "./cmd/..."]` — o escopo correto, não `./...`.

**Como o módulo entra**, medido com `go mod why -m`: nenhum arquivo Go do wiki importa `x/crypto`; a cadeia é `internal/officialpdfprobe` → `pdfcpu/pkg/api` → `pdfcpu/pkg/pdfcpu/sign` → `golang.org/x/crypto/ocsp`. É dependência transitiva do verificador de assinatura de PDF, e o símbolo vulnerável **não é chamado**.

**Veredito:** não é "CVE viva ignorada". É risco **medido**, **não alcançável** (`reachable_call: false`), **sem correção publicada** (`upstream_has_no_fix: true`) e já registrado em `data/ops/sca_ignore_risk_register.jsonl`. Fingir um bump inexistente seria pior que inútil: mudaria o `go.sum` sem reduzir risco nenhum. O que muda o quadro é o upstream publicar a correção — e aí o bump é mecânico.

### `languagetool-quality` — o custo real da regeneração, medido, e por que ela não cabe numa passada

Ao mudar a política de regras advisory (a correção do `POR_QUE_PORQUE`, commit `fb58ae5b`), o `cache_policy_sha256` da evidência deixou de bater — `disabledAdvisoryRulesParam()` entra no fingerprint (`batch.go:1420`). O gate passou a acusar `languagetool_quality_cache_policy_bad`, **corretamente**: é o mecanismo desenhado para detectar que a política mudou e a evidência precisa ser refeita.

**Quanto custa refazer, medido com `--dry-run` e o serviço 6.8 local de pé:**

| registros | tempo | throughput |
|---|---|---|
| 100 | **46 s** | ~2,2 registros/s com `--concurrency 12` |

Extrapolado para os 7.959 do corpus: **~61 minutos**. O teto duro do envelope é **1800 s (30 min)**, e a mensagem do próprio wrapper diz o que fazer — *"shard/cache/optimize instead of increasing the timeout"*. Então a passada única não cabe **por medição**, não por suposição.

**E `persistent_cache_hits=0` em toda passada não é defeito: é consequência legítima da mudança.** A chave do cache inclui o fingerprint da política; mudar a lista advisory invalida o cache inteiro, de propósito. A primeira passada depois de uma mudança de política sempre refaz tudo.

**A rota que o próprio gerador prevê** é `--max-live-checks`, descrito em `main.go:192` como *"maximum live LanguageTool cache misses to check before writing fail-closed budget evidence"*: cada passada resolve N misses, popula o cache persistente e grava a evidência completa com budget fail-closed para o restante; a passada seguinte aproveita o cache e avança. É o shard que o envelope pede, e não exige código novo.

**Três armadilhas medidas no caminho, que ficam registradas porque cada uma custou uma passada:**

1. `WIKI_HEAVY_TIMEOUT_SECONDS` sozinho **não vale** — vence o menor entre ele e `WIKI_HEAVY_BUDGET_MS`, e o segundo estava em 120 s. Documentado em `docs/OPERACAO_COMANDOS_E_CAMINHOS.md`.
2. `--timeout` do gerador tem default de **2 s** por requisição (`main.go:186`), e o LanguageTool leva ~1 s por texto depois de aquecido — mas mais na primeira chamada, quando carrega os modelos. Com 2 s, o gerador conclui `service_required_unavailable` **com o serviço de pé e respondendo HTTP 200**.
3. `--dry-run` **não popula o cache**, então medir com ele não adianta o trabalho da passada real.

E a guarda do BUG-227 provou o valor em campo: **cada uma dessas passadas incompletas tentou gravar 200 registros sobre os 7.959**, e todas foram recusadas. Sem ela, a primeira tentativa teria destruído a evidência e as seguintes estariam medindo contra um artefato mutilado.

### `check-access-ledger-contamination` — fechado em 2026-08-30: uma sonda de agente que não se declarou

Achado pela varredura da bateria (`tools/generate-varredura-bateria-gates`), entre os primeiros 13 gates medidos — 8 verdes e 5 vermelhos, taxa coerente com os ~40% que o plano registra.

**A linha, uma só, lida no ledger:**

```json
{"ts":"2026-08-26T10:48:41Z","method":"GET","path":"/metrics","status":200,
 "bytes":86800,"route_class":"metrics","bot_class":"unknown_or_standard_user_agent",
 "user_agent":"wiki-audit-roteamento/1.0 (auditoria interna read-only)",
 "warming":false,"bot_simulation":false}
```

**O defeito é o par de flags em falso.** A sonda tinha UA próprio e honesto — declara-se auditoria interna read-only —, mas **não marcou `warming` nem `bot_simulation`**, que é o que o contrato exige de toda requisição interna. Sem a marca, a linha atravessa `tools/check-bot-traffic`, que descarta apenas quem se declara, e conta como tráfego real.

E ela nem poderia vir de fora: `/metrics` recebe 404 do nginx antes de chegar ao Go (`ops/nginx/wikijuridica.conf:384`). O 200 com 86.800 bytes só se explica por acesso direto ao processo em `127.0.0.1`.

**Não há código a corrigir, e isso foi verificado antes de concluir:** `grep` pelo UA em todo o repositório devolve **uma única ocorrência fora do ledger** — o journal da onda de agentes de 2026-08-26 (`data/ops/agent_reports/onda_bots_20260826/`). Foi sonda ad-hoc de um agente daquela onda, não ferramenta versionada; não existe mais nada a marcar.

**A correção é a quarentena declarada**, que é o mecanismo já previsto e cuja regra o próprio gerador enuncia: *"quarentenar é ato deliberado de quem revisou as linhas, não efeito colateral de rodar um check"* — por isso o `check-*` é read-only e quem grava é `tools/generate-access-ledger-quarantine`. A linha **fica onde está**, visível e auditável, e o ledger paralelo registra por que não entra em conta nenhuma. Lotes em quarentena: 7 → **8**; linhas neutralizadas: 28.942 → **28.943**. O access log original não foi tocado.

- **Resultado:** `check-access-ledger-contamination` EXIT=1 → **EXIT=0**.
- **Precedente que fica:** sonda ad-hoc de agente sem `X-Warming-Request` contamina o ledger de tráfego e só aparece semanas depois, num gate que ninguém rodava. Quem instrumenta produção numa onda precisa marcar a requisição na hora — depois, o conserto é quarentena com revisor, não apagar linha.

## BUG-229 — a auditoria de dependências abortava em pseudo-versão, e por isso estava congelada desde junho

- **Data:** 2026-08-30
- **Severidade:** GRAVE — a auditoria de licença e proveniência das dependências diretas cobria **39 de 76** e datava de 2026-06-30, sem que nada acusasse a lacuna além do gate que ninguém rodava.
- **Sintoma:** `check-pkgsite-module-audit` → `record_count_mismatch: records=39 direct_requirements=76` e `api_base_unofficial: https://pkg.go.dev/v1beta`. O segundo é revelador: a evidência ainda trazia a base antiga, então a correção do BUG-067 (que trocou `/v1beta` por `/v1` porque a pkg.go.dev promoveu a API a GA e o 301 perdia a query) **nunca chegou ao dado** — o gerador não rodava desde antes dela.
- **Causa-raiz, medida com a URL que o próprio adaptador monta:**

  | módulo | versão | HTTP |
  |---|---|---|
  | `github.com/PuerkitoBio/goquery` | `v1.11.0` | **200** |
  | `github.com/sourcegraph/zoekt` | `v0.0.0-20260622122048-f80c7e09ab9d` | **404** |
  | `golang.org/x/perf` | `v0.0.0-20260615155930-9e4b9ddef5b6` | **404** |

  Os mesmos módulos **sem** a versão respondem 200 nos três casos: o 404 é da **pseudo-versão**, não do módulo. A pkg.go.dev indexa *releases*, não commits — e pseudo-versão é pin legítimo, que `go get` gera para dependência fixada em commit sem tag. O repositório tem duas.

  O adaptador tratava esse 404 como defeito fatal e **abortava antes de gravar** — quinta ocorrência do padrão do BUG-224 nesta caçada: validar antes de persistir.

- **Correção, em quatro camadas, todas com o mesmo critério:** `pseudoVersao()` reconhece o formato canônico (`vX.Y.Z-<14 dígitos>-<12 hex>`); `statusAPIAceitavel()` aceita 404 **só** em pseudo-versão; e as quatro validações que dependem do corpo da resposta — caminho resolvido, `go.mod`, contrato de licença e metadados de origem — passam a ser exigidas apenas de registro efetivamente indexado. Um registro sem corpo não tem esses campos, e cobrá-los transformava resposta esperada em defeito.
- **Mais dois obstáculos reais, achados um a um ao destravar:**
  - **Timeout de rede.** `DefaultHTTPTimeoutSeconds` era **15**, e a passada falhou duas vezes com `context deadline exceeded` (`go.etcd.io/bbolt`, `github.com/aafeher/go-sitemap-parser`) — e a falha de **uma** requisição aborta as 76. Subiu para 45 s: não é lentidão a corrigir, é chamada a serviço externo público que legitimamente varia. A concorrência caiu de 8 para 2 na execução, pelo mesmo motivo que no LanguageTool.
  - **Módulo legado sem `go.mod`.** `github.com/mfonda/simhash`, pseudo-versão de **2015**, anterior aos módulos do Go. Conferido na API: licença **MIT**, `has_go_mod` ausente; em uso de produção em `internal/dedupeexternaloracle` e `internal/ossscaleintegration`. Entrou na allowlist de legado ao lado do `dgryski/go-minhash`, que é da mesma família — e a allowlist ganhou a nota de que **módulo novo sem `go.mod` continua reprovando**, porque hoje isso é escolha, não herança.
- **Resultado:** `records=39 → 76`, `api_base` de `/v1beta` para `/v1`, `redistributable=73`, e o gate `check-pkgsite-module-audit` **EXIT=1 → EXIT=0**.
- **Prova em par:** o RED cobre o reconhecimento da pseudo-versão em 7 formatos e a aceitação do 404; o controle exige que **404 em versão semântica continue reprovando** (ali o módulo deveria estar indexado) e que **500 não passe nem em pseudo-versão** — erro de servidor é falha, não ausência de índice.

## BUG-230 — o gate de abandono de bot escondia o número que motiva o próprio veredito

- **Data:** 2026-08-30
- **Severidade:** MÉDIA como defeito, ALTA pelo efeito: a linha levava o leitor a concluir que o detector estava errado, e o achado real ficava para trás. Foi o que aconteceu comigo.
- **Sintoma.** O gate imprimia:

  ```
  yandexbot   esfriando   última visita 2026-08-30 (0 dias atrás; limite do próprio ritmo: 3 dias; mediana 1.0)
  ```

  Um bot que visitou **hoje**, com limite de 3 dias, classificado como esfriando. Lido assim, parece detector quebrado.

- **Não estava quebrado.** `esfriando` é veredito de **volume**, não de intervalo — o cabeçalho do próprio arquivo diz "volume despencou", e o alarme cita `queda_desde_o_pico_pct` como evidência. Só que a linha impressa mostrava exclusivamente campos de **dias**. O número que decide o veredito não aparecia na linha que o anuncia.
- **Correção:** a queda entra na linha. Agora:

  ```
  meta-externalagent  abandonou  queda 98.8% desde o pico; última visita 2026-08-23 (7 dias atrás; …)
  yandexbot           esfriando  queda 99.4% desde o pico; última visita 2026-08-30 (0 dias atrás; …)
  ```

### E o achado que a linha escondia é grave: dois bots valiosos com queda de ~99%

| agente | veredito | queda desde o pico | última visita |
|---|---|---|---|
| `meta-externalagent` | abandonou | **98,8%** | 2026-08-23 (7 dias) |
| `yandexbot` | esfriando | **99,4%** | 2026-08-30 (hoje) |

O `yandexbot` é o caso que a mensagem antiga tornava invisível: **continua passando todo dia e praticamente não busca nada**. Um detector que olhasse só intervalo o daria como saudável.

Pelo contrato — *"queda de rastreio, indexação ou citação é DEFEITO DE ENGENHARIA até prova medida em contrário; 'depende do bot' é desculpa proibida"* — isto é frente de investigação com causa a medir, não observação. Fica registrado com o número e a data, e **não** com a explicação fácil: o abandono do `meta-externalagent` começou em **23/08**, antes do deploy de 29–30/08, então a reescrita do acervo desta sessão não o explica.

### `languagetool-quality` — FECHADO em 2026-08-30, com a prova de efeito

A evidência foi regenerada contra o serviço LanguageTool 6.8 local, numa fatia de **1.376 s**, e o gate voltou ao verde:

```
languagetool-quality: pass records=7959 service_available=7959 service_required=7959
```

**A prova de efeito da reclassificação do `POR_QUE_PORQUE`** (commit `fb58ae5b`), medida na evidência nova:

| | antes | depois |
|---|---|---|
| `POR_QUE_PORQUE` como **blocker** | 3.521 | **0** |
| `POR_QUE_PORQUE` **suprimido** (advisory) | 0 | **1.095** |

A regra saiu inteira dos blockers e continua **contada e visível** na evidência como suprimida — que era exatamente o desenho: o match não some, deixa de bloquear release. Os blockers restantes são outra família: `NUMBER_ABREVIATION` (398), `COLOCAÇÃO_ADVÉRBIO` (115), `REDUNDANCY_JUNTO_COM` (82), `COLOCACAO_PRONOMINAL_COM_ATRATOR_SIMPLES` (59).

**O caminho até aqui custou seis passadas, e cada uma ensinou uma coisa que ficou em código ou em documento:** o serviço não estava de pé e o instalador montava a versão errada (BUG-228); o gerador sobrescrevia a evidência boa por uma amostra de 200 (BUG-227); eram **três** relógios e vencia o menor; `exit 75` e `exit 124` curto são contenção de lock, não trabalho perdido; e **concorrência 12 era quase cinco vezes mais lenta que 4**, porque o LanguageTool é CPU-bound e as requisições disputavam entre si. Nenhuma dessas foi suposta — todas saíram de medição, e a ferramenta `tools/regenerate-languagetool-evidence` carrega as cinco.

## BUG-231 — a meta description de uma notícia começava com a contagem colada na frase

- **Data:** 2026-08-30
- **Severidade:** P0 de conteúdo — meta description é o texto que o buscador mostra abaixo do título; um número solto no começo é a primeira coisa que o leitor humano lê no resultado de busca.
- **Achado por** `check-noticias-conformidade`, na varredura da bateria: `meta com contagem colada em frase: 1 de 32`.
- **A página servida**, conferida no disco:

  ```html
  <meta name="description" content="8 As decisões que o TST divulgou em 25 de agosto de 2026, com link para cada matéria oficial.">
  ```

- **O produtor já estava certo.** `cmd/generate-noticia-pages/main.go:669` usa `concordanciaDeDecisao(len(ordenados))`, e o comentário ali registra a medição que motivou a troca: `plural` prefixa a contagem, o que é correto na abertura do corpo, mas aqui o argumento é uma frase que já começa em maiúscula. Em 2026-08-26 eram **20 de 20** páginas no ar com a marca. Sobrou **uma**, publicada antes da correção.
- **Por que não regenerei o shard.** Medido: o gerador monta **31** páginas e o shard tem **32**. Regerar tiraria uma página **publicada** — e o contrato é explícito em que gerador não apaga publicada, porque URL que existe tem de ter conteúdo. O gate `check-shard-preservation` barraria, e com razão.
- **Correção:** `tools/generate-noticia-meta-contagem-20260830`, gerador datado e pontual — um campo, de um registro, com escrita atômica (`tmp` + `os.replace`), e um padrão ancorado no início da string e exigindo a frase conhecida, para não alcançar meta legítima que comece com número.
- **Verificado depois de gravar:** `git diff --numstat` = **1 linha**; `check-shard-preservation` OK sobre **944 shards**, nenhum registro ativo desaparecido; `check-v2-portfolio-pairing` OK.
- **O que falta, e é honesto dizer:** `check-noticias-conformidade` lê `public/`, então ele só fica verde depois que a página for republicada. O dado está corrigido e commitado; o HTML no ar ainda traz o "8 " até a próxima publicação — que é exatamente o que a mensagem do gate antecipa: *"corrigir o produtor não conserta o estoque já publicado"*.

## BUG-232 — três bots do Google tinham pista ilimitada no nginx e não existiam na política

- **Data:** 2026-08-30
- **Severidade:** GRAVE de governança — pista ilimitada é **chave de rate limit vazia**, não etiqueta: os três atravessavam o nginx sem limite nenhum, sem nada na política que autorizasse.
- **Achado por dois gates que se completam**, na varredura da bateria:
  - `check-bot-allowlist-derivada`: `24 com pista ilimitada` nos dois `nginx.conf` contra `21` na classe `valuable_search_or_user_bot` do registry — `google-inspectiontool`, `googleother` e `storebot-google` **NÃO EXISTEM no registry**.
  - `check-bot-identity-fonte-unica`: os mesmos três estavam em `DIVERGENCIA_CONHECIDA`, declarados como pendência desde 2026-08-26.
- **A correção que o próprio gate manda fazer**, e que é o oposto da fácil: *"Resolva CLASSIFICANDO no registry, não removendo do nginx sem medir: parte deles faz tráfego real e útil, e cortar a pista trocaria um defeito de governança por um defeito de rastreio."* Os três foram classificados em `content/crawl_policy.json` com `class: valuable_search_or_user_bot` e `rate_tier: unlimited_no_rate_limit` — que é exatamente o que os dois nginx já praticavam.
- **A cadeia cobrou três camadas, e cada gate apanhou a seguinte** — o sistema funcionando:
  1. `bot_registry` → `crawlability` acusou `crawl_policy_registry_missing_access_rule`;
  2. `access_rules` → acusou `..._missing_robots_rule`;
  3. `rules` → acusou `..._unknown_purpose`, porque eu havia **inventado** dois valores (`search_console_inspection`, `shopping_product_discovery`) em vez de usar o vocabulário existente. Corrigidos para `user_triggered_fetch` (o InspectionTool é disparado pelo operador no Search Console) e `search_discovery`.
- **Resultado:** `crawlability`, `public-robots-drift`, `openai-bot-policy` e `check-bot-allowlist-derivada` todos **EXIT=0**; `check-bot-identity-fonte-unica` também, depois de os três saírem da lista de divergência — declaração de divergência já resolvida é ruído que reprova o gate por nada. O `robots.txt` servido passou de 33 para **36 grupos**.
- **Conferido que o build NÃO re-datou o acervo:** `git status -- public/` = **0 arquivos**, e `find public -name '*.html' -newermt '-5 minutes'` = **0**. A escrita idempotente do BUG-063 fez o trabalho.

**★ E a armadilha que ficou documentada em vez de apagada.** A entrada do `yandexbot` na mesma lista carregava um conhecimento caro: a doc oficial do Yandex diz, verbatim, que o robô procura *"the substring Yandex (the case doesn't matter) or *"* e que, achando `Yandex`, *"the User-agent: * string is ignored"*. Criar um grupo com "Yandex" no nome do `robots.txt` **desliga o curinga para a família inteira**. O `yandexbot` saiu da lista porque já entrou no registry, mas a armadilha foi movida para comentário no mesmo arquivo — remover a entrada não podia levar junto o motivo pelo qual ela existia.

### Achado registrado, não commitado: o build normaliza `content_revised_at`

Rodando `cmd/build public` para regenerar o robots, `content/pages.json` mudou em 3 linhas — `"content_revised_at": "2026-08-30"` virou `"2026-08-30T10:26:21Z"`. É normalização de formato do build, não mudança minha, e mexe justamente no campo de **re-datação**. Ficou fora do commit de propósito, e fica registrado aqui: quem rodar o build encontra esse churn e precisa decidir se o formato canônico é a data ou o timestamp — decidir por acidente de quem rodou o build por último é como o `reviewed_at` já se perdeu uma vez.

### BUG-233 — a varredura da bateria contava como vermelho o gate que só pede argumento

Medido em 2026-08-30, durante a própria varredura: `check-baseline-testes-vermelhos` saiu com `exit=2` em **83 ms** e `check-server-binary-smoke` com `exit=1` em **6 ms**, e o que os dois imprimiram foi só isto:

```
uso: check-baseline-testes-vermelhos <log-do-go-test>
./tools/check-server-binary-smoke: line 9: 1: uso: smoke.sh <caminho-do-binario>
```

Não estão reprovando. Estão dizendo que **a chamada** é que faltou. `tools/generate-varredura-bateria-gates` invoca todo `tools/check-*` sem argumento — o que é correto para a esmagadora maioria, que roda sozinha —, mas os que pedem parâmetro entram na conta como se fossem defeito.

**Isso infla exatamente o número que a varredura existe para apurar**, e manda o leitor investigar defeito inexistente — eu mesmo fui investigar os dois antes de perceber. O registro ganhou o campo `aplicavel_sem_argumento`, marcado pela primeira linha da saída, e os dois casos já medidos ficam nomeados aqui.

O `exit=2` do `check-baseline-testes-vermelhos` era particularmente enganoso porque a convenção do repositório (documentada em `docs/OPERACAO_COMANDOS_E_CAMINHOS.md` §14) é que **1 é veredito e ≥2 é instrumento quebrado** — e ali o 2 significava só "faltou o argumento".

## BUG-234 — o scanner de segredos estava CEGO: não compilava desde o bump da Fase 9

- **Data:** 2026-08-30
- **Severidade:** CRÍTICA de segurança — não é gate reprovando por achado, é gate **incapaz de rodar**. Enquanto durou, nenhum segredo commitado seria detectado, e o vermelho parecia dívida conhecida.
- **Como apareceu.** `check-sca-gitleaks-secrets` reprovava com `sca_gitleaks_bulk_editorial_allowlist_missing`. Corrigi isso primeiro (abaixo) — e aí o erro **mudou**, revelando o defeito real:

  ```
  sca_gitleaks_secrets_failed: exit status 1 output=# github.com/mholt/archives
  .../archives@v0.1.2/rar.go:105:9: cannot use or (variable of type *rardecode.ReadCloser)
  as rarReader value in assignment: *rardecode.ReadCloser does not implement rarReader
  (missing method WriteTo)
  ```

  O binário do gitleaks **não compilava**. Quatro alvos de varredura falharam com o mesmo erro de build.

- **Causa-raiz, medida na fonte de cada módulo:** `tools/sca/go.mod` tinha `github.com/mholt/archives v0.1.2` e `github.com/nwaples/rardecode/v2 v2.2.0`. Mas o `go.mod` do **próprio archives v0.1.2** exige `rardecode/v2 v2.1.0` — a API mudou entre as duas, e o `rarReader` de `v2.2.0` não satisfaz o que a v0.1.2 espera. O bump de dependências da Fase 9 subiu o `rardecode` além do que o `archives` pinado suportava.
- **A correção é subir, não descer.** Baixar o `rardecode` para v2.1.0 reintroduziria o que o bump corrigiu. Conferido na fonte: o `go.mod` de **`archives v0.1.5`** exige exatamente `rardecode/v2 v2.2.0` — a versão já pinada. `go get github.com/mholt/archives@v0.1.5` (nunca `go mod tidy`, pela regra do repositório) resolveu com o `rardecode` intacto, arrastando `xz`, `minlz` e `lzip-go` junto.
- **E o achado que veio antes dele, e que o escondia:** a primeira allowlist do `.gitleaks.toml` tinha, desde sempre, a descrição *"public, release-staging, ops, research, source-registry and editorial corpus…"* — mas `^data/editorial/` **nunca esteve na lista de paths**. O corpus editorial é o texto das páginas públicas, milhões de linhas de prosa jurídica, sem credencial por construção e com falso positivo em massa sobre hash e identificador de norma.

  O escopo entrou **estreito de propósito**, e o contrato está pinado em `internal/checks/sca_gitleaks_test.go`: `data/ops`, `data/research`, `data/source-registry` e `data/audits` continuam **varridos**, porque ali cabe credencial de verdade — acrescentar qualquer um deles reprova o gate.

## BUG-235 — alterar UM campo de um shard v2 trava a publicação de todas as frentes, e quem destravaria se recusa pelo mesmo motivo

- **Data:** 2026-08-30
- **Severidade:** CRÍTICA — enquanto dura, `public-release-transaction` reprova e **nenhuma frente publica**. É o mesmo dano do BUG-217, por outra porta.
- **Como cheguei nele:** corrigi a meta description de uma notícia (BUG-231), um campo de um registro, com escrita atômica e as guardas verdes na hora (`check-shard-preservation` sobre 944 shards, `check-v2-portfolio-pairing`, `v2-index-product-gates`). O que eu **não** fiz foi refazer o recibo de frescor do estoque.
- **A cadeia, medida:**

  ```
  public-release-transaction:
    v2_stock_freshness_source_unreadable: .../noticias-oficiais-01.jsonl: source record changed
    v2_stock_freshness_terminal_evidence_invalid: reconstructed terminal guards differ from receipt source snapshot
  ```

  `data/ops/v2_ingest_transaction_receipt.json` guarda `source_snapshot_fingerprint_sha256` e a lista `source_files` com o fingerprint de **cada shard**. Mudou uma linha do shard, mudou o fingerprint, e o recibo passou a atestar um estado que não existe mais.

- **★ E o deadlock: quem refaria o recibo faz o mesmo preflight.** `cmd/generate-authorial-mass-manifest-transaction` chama `canonicalStockPreflight` → `v2ingest.ValidateInstalledCanonicalStockSnapshot` **antes** de qualquer trabalho (`main.go:71-83`), e reprova pelo mesmo motivo. Rodado com `--rewrite-storage-only`, que existe justamente para "reescrever os registros da transação sem regenerar conteúdo", ele sai com `exit_code=1` nas mesmas duas linhas.

  É a **terceira aparição** do padrão que esta caçada já nomeou duas vezes: validar antes de agir, e por isso não poder agir. No BUG-224 o gerador validava antes de persistir; no BUG-227 persistia sem validar; aqui o reparador exige que o estado já esteja reparado.

- **Rotas descartadas, com o motivo:** `cmd/plan-source-snapshot-repair` não serve — repara `data/source-snapshots`, o corpus de fontes, não o snapshot de frescor do estoque. E `tools/run-generate-supervised` recusa o `ingest-v2-stock` (`only ./cmd/generate <subcommand> or ./cmd/generate-* packages are allowed`), então o envelope tem de ser montado à mão com `run-heavy-throttled` + `run-go-cmd-cached`.
- **Rota em curso:** `cmd/ingest-v2-stock --prepare-only` — "validate and build the guarded transaction plan without installing artifacts". É o pipeline sancionado, e o `--prepare-only` permite ver se o plano se constrói sobre os shards atuais antes de instalar qualquer coisa.
- **A lição que fica, independente do desfecho:** no regime v2, **corrigir um campo de um shard publicado não é uma edição — é uma transação**. As guardas que rodei (preservação, pareamento, índice) são necessárias e não suficientes: nenhuma delas olha o recibo de frescor. Quem editar shard precisa rodar `./tools/go-modern run ./cmd/check public-release-transaction` **antes de commitar**, que é onde a cadeia aparece.

### BUG-234 — o que o scanner encontrou depois de voltar a enxergar

Com o `archives` corrigido, o gitleaks varreu `internal/` de verdade — **42,01 MB em 28 s** — e acusou **5 leaks**. Lidos um a um, os cinco são falso positivo, e o exercício vale registrar porque prova que o scanner voltou a funcionar:

| arquivo | match | por que não é segredo |
|---|---|---|
| `internal/indexnow/provision_test.go:121` | `key":"abcdef1234567890"` | placeholder trivial de teste |
| `internal/indexnow/indexnow_test.go:492`, `:600`, `:695` | `key := "abcdef1234567890"` | idem — hex sequencial, entropia 4 |
| `internal/v2ingest/imobiliario09_current_legal_fact_rules.json:512` | `key": "itbi_assignment_tema_1124_pending"` | identificador **semântico** de regra jurídica: nomeia o Tema 1124 do STF sobre ITBI |

A chave real do IndexNow **não vive no repositório**: vem do ambiente, e o arquivo de chave publicado é gerado no deploy.

**As exceções entraram estreitas, por VALOR e não por diretório** — assim qualquer outro segredo nesses mesmos arquivos continua sendo apanhado. E duas armadilhas do gitleaks foram medidas no caminho, cada uma custando uma rodada de 30 s:

1. **`paths` casa o caminho relativo ao diretório varrido.** `gitleaks dir internal` reporta `v2ingest/....json`, e `gitleaks dir .` reporta `internal/v2ingest/....json` — um padrão preso ao início (`^internal/...`) casa numa varredura e falha na outra. Ancorado em `(^|/)` funciona nas duas.
2. **`regexes` casa o SEGREDO capturado, não a linha.** O padrão escrito como `"key":\s*"..."` não casou nada; o que casa é o valor sozinho, `^[a-z0-9]+(_[a-z0-9]+)+$` — snake_case minúsculo, forma que credencial de verdade não costuma ter.

Resultado: `no leaks found`, EXIT=0, com `TestSCAGitleaksConfigScope…` verde — o contrato que proíbe alargar a allowlist para `data/ops`, `data/research`, `data/source-registry` e `data/audits` continua valendo.

## O mapa da bateria: 472 dos 473 gates medidos com exit code REAL

Instrumento: `tools/generate-varredura-bateria-gates`, nos dois tiers, com o resultado em `.agents/runtime/caca/varredura-{a,b}.jsonl`. É o que o BUG-109 pedia — não a estimativa do plano ("157 de 391"), mas a medição.

```
472 gates | exit 0: 288 (61%) | exit 1: 165 | exit 124: 12 | exit 2: 6 | exit 75: 1
```

**184 não-verdes, e eles não são 184 defeitos.** A separação importa mais que o total:

| classe | quantos | o que é |
|---|---|---|
| `exit 1` | 165 | **veredito** — o gate rodou e reprovou |
| `exit 124` | 12 | **timeout** — não terminou no orçamento; não disse nada sobre o conteúdo |
| `exit 2` | 6 | instrumento — e **3 destes** só pediam argumento (BUG-233) |
| `exit 75` | 1 | corrida de lock, não defeito |

Por família, o vermelho se concentra: `authorial` 24, `public` 11, `priority` 8, `ptbr` 6, `codex2` 6, `source` 6, `v2` 5, `commercial` 5, `sca` 5.

**O que esta sessão fechou dessa lista**, cada um com causa medida e commit: `access-ledger-contamination` (sonda de agente não declarada), `recibo-de-transacao-versionado` (recibo untracked citado pelo manifesto), `pkgsite-module-audit` (39→76 requisitos), `bot-identity-fonte-unica` e `bot-allowlist-derivada` (três bots do Google sem entrada na política), `crawlability`, `public-robots-drift`, `openai-bot-policy` (a mesma cadeia), `languagetool-quality` (evidência regenerada) e `sca-gitleaks-secrets` (o scanner que não compilava).

**A concentração em `authorial` é o próximo alvo óbvio**, e a varredura agora dá o nome de cada um em vez de um número agregado — que era exatamente o ponto do BUG-109.

## `check-rollback-retention` — fechado em 2026-08-30, com a prova de que apagar não perdia nada

- **Situação:** 115 snapshots de publicação ocupando **7,66 GB**, com o disco em **89%**. A política (os 10 últimos mais o último de cada dia nos últimos 14 dias) preservava 19 e dispensava **96 (6,91 GB)**.
- **Por que não executei sozinho:** apagar dados é irreversível, e snapshots de rollback são a rede de segurança da publicação. O próprio gate se recusa a remover — só **imprime** o comando. Levei a decisão ao dono, que autorizou depois da análise.

**A prova de que o git cobre o que os snapshots guardam**, e é ela que torna a remoção segura:

1. Os snapshots **não estão no git** — `.gitignore:331` traz `data/ops/publish-rollback-*/`, e `git ls-files` devolve **zero** arquivos em cada um dos 96.
2. O que eles guardam **está versionado**: `content/pages.json` e `data/editorial/published_manifest.jsonl` são ambos rastreados.
3. E o conteúdo bate. Peguei o snapshot mais antigo (`20260806-174354`) e o commit da época:

   ```
   git rev-list -1 --before="2026-08-06 17:43" main   → ef07adf9
   published_manifest naquele commit                  → 9.400 linhas
   published_manifest no snapshot                     → 9.400 linhas
   ```

O `RESTORE.md` de cada snapshot diz *"restaure por cópia (o contrato proíbe retorno de estado do git)"* — e isso continua valendo: a proibição é de `checkout`/`reset`, que destroem a worktree. `git show <commit>:arquivo > destino` é a forma que o próprio CLAUDE.md manda usar para ler estado antigo, e reproduz byte a byte o mesmo conteúdo.

**Conferência antes de executar**, com o comando de cada item:

| verificação | resultado |
|---|---|
| alvos fora do padrão `publish-rollback-AAAAMMDD-HHMMSS` | **0** |
| diretórios com arquivo versionado | **0** |
| preservados que estavam na lista de remoção | **0** (os 19 ficaram fora) |
| espaço a liberar | **7,0 GB** |

**Ordem seguida:** atualizar o backup de produção **antes** de apagar. O backup já era saudável — ensaio de restauração com **16.827 arquivos e 2,79 GiB conferidos byte a byte** — mas estava 110 commits atrás. Depois da sincronia incremental: `espelho em 73f47be5`, **origem 0 commits à frente**.

**Resultado:** 96 removidos, disco de **74G para 81G livres** (89% → 87%), 19 snapshots preservados (o mais recente de hoje às 16:58), `check-rollback-retention` **EXIT=0**, `check-backup-restauravel` **EXIT=0** e `public-release-transaction` **pass** — a rede de segurança da publicação continua de pé.

## BUG-236 — o check da cobertura de borda ESCREVIA no ledger, e por isso a série media a si mesma

- **Data:** 2026-08-30
- **Severidade:** GRAVE — contamina a métrica que decide se o acervo está cacheado, e já produziu um **100% falso** em 2026-08-19.
- **Violação direta de contrato.** `AGENTS.md:371`: *"Wrapper `check-*` deve ser read-only para artefatos rastreados."* O `data/ops/edge_cache_coverage.jsonl` **é rastreado** (`git ls-files` confirma), e `tools/check-edge-cache-coverage:238-239` abria em modo append e escrevia a cada execução. Não existia `generate-` correspondente.
- **E não é formalidade.** A sonda **aquece o que mede** — o próprio evento gravado carrega `"sonda_aquece_o_que_mede": true`. Com a gravação acoplada ao check, duas execuções na mesma hora deixavam duas linhas na série, e **a segunda media o rastro que a primeira acabou de aquecer**. O `check-edge-cache-coverage-honesty` apanha isso em **oito pares consecutivos** (linhas 93 a 100, de 26 e 27 de agosto), todos com a mesma `chave_amostra`.
- **Correção — separação de papéis, sem duplicar código:** a gravação virou **opt-in** (`--gravar`), e `tools/generate-edge-cache-coverage` é o único que a passa. O check pode agora ser rodado à vontade para diagnóstico — depois de uma purga, ao investigar um alerta — sem deixar ponto novo na série.

  **Prova dos dois lados, medida:**

  ```
  ./tools/check-edge-cache-coverage --sem-alerta      → 153 linhas antes, 153 depois
  ./tools/generate-edge-cache-coverage --amostra 5    → 153 linhas antes, 154 depois
  ```

- **★ E o detalhe que faria a correção quebrar a coleta.** `ops/systemd/wikijuridica-edge-cache-coverage.service:40` chamava o **check** para alimentar a série. Deixá-lo read-only sem mais nada mataria a medição de produção em silêncio — o serviço rodaria a cada duas horas sem gravar nada, e ninguém notaria até a série secar. O `ExecStart` passou a apontar para o gerador. O unit em `/etc/systemd/system/` é **symlink para o repositório**, então a edição já vale; `systemctl daemon-reload` confirmou: `ExecStart=/opt/wiki/tools/generate-edge-cache-coverage --amostra 40`.
- **Uma linha de teste minha foi removida do ledger**, e vale dizer por quê: ao provar que o gerador grava, usei `--amostra 5`, e o resultado (cobertura 100% sobre 5 URLs) entrou na série versionada. Cinco URLs não estimam nada — o serviço usa 40 justamente porque a sonda aquece o que mede, e 40 de ~9.890 é 0,4% do acervo. Removi a linha que eu mesmo acabara de criar; o ledger voltou ao estado anterior. Isso é diferente de apagar histórico: é não introduzir ruído próprio num artefato de medição.
- **O que a correção NÃO faz:** os oito pares históricos continuam lá, e o `check-edge-cache-coverage-honesty` continua reprovando por eles — a série é append-only e nada se apaga. A causa está fechada; o passado fica visível, que é o desenho.
