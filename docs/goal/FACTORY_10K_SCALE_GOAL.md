# Prompt `/goal` — Destravamento da fábrica jurídica 10K e arquitetura para 10M

## Revisão operacional vigente — 2026-07-20

Esta revisão materializa o plano P0–P5 investigado pelo Codex e **prevalece sobre números, limites fixos e sequências conflitantes do baseline de 15/07 preservado abaixo**. O texto anterior continua como histórico e fonte de testes/hipóteses; não é autorização para confiar em `accepted`, checkpoint, comentário de IA, benchmark declarado ou contador hardcoded.

### Objetivo e decisões fechadas

1. Manter **10.000 páginas jurídicas públicas aprovadas, únicas, úteis, indexáveis e verificadas** como piso P0. A meta não legitima o corpus antigo nem vira teto da fábrica.
2. Aposentar V1 como corpus textual. V1 só fornece hipótese de demanda ou referência depois de revalidação; corpo, hash, aprovação e release não são transplantados.
3. Usar V2 como única linhagem candidata, submetendo cada revisão a nova adjudicação. `accepted` de ingest não significa aprovação jurídica/editorial, release-ready ou público.
4. Promover exatamente o déficit vivo até 10.000; manter estoque excedente interno/noindex. As últimas páginas que fecham o déficit são o P0 mais crítico.
5. Usar DataJud de modo não comercial, agregado, minimizado e auditável para demanda/jurisprudência/proveniência. DataJud não vira prosa pública nem prova sozinho que uma tese está correta.
6. Coleta/scraping permitido por termos serve somente a pesquisa bloqueada. Não copiar, colar, espelhar ou montar prosa pública a partir de texto externo.
7. O gargalo é código/arquitetura, não o servidor: serialização global, scans O(N), all-pairs, mtime, cópias cumulativas, cache desconectado, `workers=2` e tetos fixos são bugs.
8. O Codex principal é o orquestrador dos subagentes GPT-5.6 disponíveis e usa toda capacidade útil em frentes disjuntas. Resultado de agente é hipótese até virar diff/dado/check/teste reproduzível integrado.
9. Commit/checkpoint não encerra o `/goal`. P0 continua até 10K; P1, P2, P3, P4 e P5 continuam na mesma sessão lógica. `update_goal complete` só depois do objetivo inteiro.
10. Integração Git é exclusivamente para frente: sem merge, cherry-pick, reset, checkout, restore, revert, stash ou clean. Commit sempre parcial por pathspec e após releitura do arquivo vivo.

### Baseline investigado — recalcular antes de cada onda

| Camada | Fotografia encontrada | Significado |
|---|---:|---|
| portfólio comercial | 10.041 | intents candidatas, não páginas |
| V2 bruto | 7.934 registros / 7.862 IDs | há supersessões/inconsistências |
| V2 ativo | ~7.817 IDs únicos | revisões candidatas |
| ingest V2 | 6.846 aceitos + 1.023 rejeitados | aceite técnico, não aprovação |
| portfólio ausente do bruto | 2.341 | escrita/cobertura pendente |
| sem revisão ativa elegível | ~2.380 | censar causa por família |
| lacuna mínima até 10K aceitos | 3.154 | cresce se gates corrigidos acharem falsos-verdes |
| público jurídico comprovado | 0 | déficit público inicial 10.000 |
| referências V2 | 18.342 ocorrências / 5.927 URLs | ocorrência não prova vigência/entailment |
| V1 histórico | 10.000 corpos; 27 seeds; 24.138 ocorrências / 46 URLs | corpus cartesiano/doorway aposentado |
| DataJud | 216 planejadas + 2 HTTP 401; 0 live | integração não operada; 401 nunca é observação |
| revisão OpenAI | 10.000 requests; 0 resultados | ensaio não é revisão |

A amostra estratificada indicou A≈44,55% e A+B≈76,49%. Por isso o estoque inicial deve chegar a **pelo menos 13.500 candidatos governados**, recalculado pelo limite inferior de 95% do yield; publicar apenas o déficit aprovado.

Antes de qualquer onda, calcular do filesystem e dos produtores atuais:

- `current_public_indexable_count` coerente em `published_manifest`, contentstore e HTML;
- `deficit_to_10000=max(0,10000-current_public_indexable_count)`;
- portfólio, V2 bruto, revisões ativas/supersedidas, aceitos/rejeitados/órfãos;
- cobertura de corpo, source bundle, claims, revisão, gates, release candidate e público;
- blockers por família, severidade, idade e páginas destraváveis;
- cold/warm/delta, throughput, cache hit, RSS, CPU, I/O e unidades reexecutadas.

Nenhum fallback silencioso `ExpectedTotalContents=10000`, downstream antigo ou texto de IA substitui esse censo.

### Espinha autoritativa do P0

O cutover é um **strangler por sujeito**, não big-bang:

- `factoryinventoryindex.Update/OpenSnapshot/IterateIDs`: descoberta incremental autoritativa;
- `factorygraph.Plan/Execute`: DAG content-addressed;
- novo `internal/factoryworkqueue` sobre `factorygraph.ExecutionStore`: `pending|leased|succeeded|blocked|deferred|quarantined`, tentativas, leases, circuitos e prioridade;
- `v2ingest.ApplyTransactionWithDurableEvidence`: ingest transacional;
- `v2pagedistinctness.UpdateWithOptions/QueryImmutableShard`: dedupe incremental/particionado;
- `publicrelease`: único escritor público e único atuador de manifest/content/HTML/robots/sitemap;
- `cmd/factory runShadow`, os oito estágios globais de `factorypipeline` e os 42 passos legados permanecem **legacy shadow** até paridade/cutover; não são autoridade;
- `publicsnapshot.Run` permanece fora do caminho autoritativo até corrigir self-lock e provar custo O(delta);
- `pagefactory`, `grounding`, `corpus`, `fiscalization`, `factorybatch` e `fiscalizationtiers` presentes apenas na worktree/staging são candidatos sob revisão, não componentes maduros por declaração.

`contentstore.WriteRecords` e CAS arquivo-a-arquivo são transição P0 sob SLO. Antes de 100K, migrar para segmentos/packs com offsets Pebble e release imutável O(delta). Nenhum grafo global, all-pairs ou carregamento integral do corpus é aceito para milhões.

### Bug de agentes: sem teto baixo hardcoded

- `max_agents=0` significa sem teto imposto pela aplicação; admitir enquanto houver unidades independentes prontas e o runtime aceitar.
- Sondar capacidade por ondas 1→2→4→8→16→…; recusa observada vira `external_agent_capacity_cap` temporário, nunca constante do repo.
- Remover `agents.max_threads=4`, 5/8/10/12 históricos e qualquer limite equivalente como autoridade. A capacidade efetiva é descoberta por runtime, DAG, memória, CPU, I/O, quota e throughput.
- Quando o harness expuser menos slots, o orquestrador fecha/integrar agentes concluídos e continua em ondas; não reduz escopo nem cria argumento de indisponibilidade.
- GPT-5.6 é o modelo pedido para os subagentes. Se a plataforma não expuser seleção, registrar o modelo/tier real sem fingir conformidade ou fazer downgrade voluntário.
- O agente raiz continua executando e integrando enquanto os subagentes trabalham; um revisor independente cobre riscos jurídico, release, storage e contrato central.

### Bug de workers: auto/adaptativo

- `max_workers=0`, `max_cpu_workers=0`, `max_network_workers=0` e `max_model_workers=0` significam **auto**, não zero.
- Remover defaults autoritativos `workers=2`, CPU=2, rede=1, modelo=1, `GOMAXPROCS=2` e semáforo global equivalente.
- Pools por classe são dimensionados pela largura pronta do DAG e feedback de CPU/RAM/I/O/latência/quota/erro; backpressure reduz somente a classe saturada.
- Overrides positivos continuam disponíveis. O modo auto publica os valores escolhidos e a razão.
- Testes repository-wide falham se literal baixo voltar ao caminho produtivo ou se auto não usar capacidade segura disponível.

### Máquina anti-loop executável

Promover FactoryGraph/Pebble como supervisor durável; não criar outro ledger textual de atividade.

```text
WorkUnitKey = hash(
  goal_epoch, node, subject/family/shard/url,
  producer_version, input_content_digests,
  gate_config_digest, official_source_revision,
  required_output_contract
)
```

HEAD, commit, timestamp, mtime, run id, comentário, hipótese livre e nome do agente não entram na identidade. Microcommit não reinicia retry, circuito ou orçamento.

Persistir `WorkUnitSpec`, `Attempt` (lease/heartbeat/deadline), `ProductDelta`, blocker signature e `CircuitState`. Resultado pequeno fica em Pebble; payload imutável grande fica no CAS. O avaliador independente ordena progresso por:

1. páginas públicas aprovadas/indexáveis;
2. páginas release-ready;
3. candidatas únicas com fonte/claims/revisão aprovados;
4. redução de blockers sem regressão nova;
5. throughput, duração e custo.

Commit, diff, arquivo tocado, log, tokens e CPU sem mudança desse vetor valem zero.

| Falha | Política |
|---|---|
| jurídico/editorial determinístico | zero rerun até mudar entrada/evidência/gate/implementação |
| gate/teste determinístico | uma tentativa |
| timeout/crash | probe mínimo + patch de causa raiz + uma verificação |
| HTTP 429/5xx/rede | até três tentativas em uma única camada, `Retry-After`, jitter, limite por host |
| transporte de modelo | até duas tentativas |
| conteúdo reprovado | geração inicial + uma reparação estruturada; segunda falha quarentena/circuito |
| conflito CAS/lease | recarregar uma vez e reutilizar resultado existente |
| lock ocupado | work stealing para frente independente; sem espera passiva |

- `loop_key=hash(node,subject,input_digest,implementation_digest,policy_version,blocker_code)` terminal não reentra.
- Duas falhas iguais na família criam `FamilyRCA`; três unidades sem ganho, dois ciclos sem progresso ou A→B→A abrem circuito.
- Cluster `min(10,ceil(5% da coorte))` obriga correção sistêmica do produtor/gate antes de novos patches por página.
- Unidade material tem deadline inferior a 10 minutos; trabalho maior é shardado, retomável e tem throughput/stop condition.
- Heartbeat mede processados/aprovados/bloqueados/throughput, não log/mtime.
- Só cancelar process group filho autenticado por PID + start ticks + `WorkUnitKey`; nunca matar por nome `codex`.

### Ondas P0

**W0 — verdade/worktree:** censo canônico, recuperação forward de journal/lease/CAS, auditoria de literais, correção de fallback silencioso e commits por pathspec após releitura viva.

**W1 — scheduler/performance:** fila por sujeito autoritativa, leases/circuitos/ProductDelta, workers auto, digest/write-if-changed, remoção de scans/mtime/O(N) no caminho quente, release O(delta) e testes crash/no-op/delta.

**W2 — fonte/claims/revisão/conectores:** fonte versionada por URN/URL/hash/vigência; corrigir `putVersioned`/`ResolveAsOf` e datas erradas; claims para toda página; gerador ≠ verificador ≠ revisor; provider real sem modelo hardcoded; DataJud TPU/agregado com timeout/rate/checkpoint/DLQ/circuit; operar CNJ, STF, STJ/TST por canal permitido, Câmara, Senado, DOU/INLABS, LexML, ANPD, ANS, BCB, SUSEP, Receita, PGFN, INPI, Anatel e Consumidor.gov.br conforme demanda.

**W3 — re-adjudicação/estoque:** reprocessar V2 por clusters; censar famílias; gerar novas candidatas autorais em ondas ≤1.000; atingir ≥13.500 governadas ou o estoque requerido pelo yield; falha individual vai para quarentena e não reinicia o lote.

**W4 — qualidade/linguagem/dedupe/search:** gates baratos primeiro; PT-BR natural via adapters vivos (`refined-public-prose`, `public-prose-language-patterns`, `languagegate`, `ptbrspell`, Vale, LanguageTool, simplemma); calibração FP/FN com positivos/negativos; Bloom→MinHash-LSH→SimHash→verificação exata; nenhum all-pairs; backend de busca só é declarado após benchmark real.

**W5 — release/runtime/security/privacidade:** coortes autenticadas e transação única; bundle/CURRENT atômico e rollback forward; HTTP humano/Googlebot, canonical/robots/sitemap shardado e HTML ≤50KB; corrigir vulnerabilidades alcançáveis TLS/`x/image`/XPath, pin de ferramentas, CORS/readiness/portas, minimização de contato/PII e isolamento da pesquisa.

**W6 — promoção exata:** recalcular déficit antes da coorte; promover somente gate completo; 50→+200→coortes ≤250; parar em exatamente 10.000; provar `p0-cycle-close-indexable-10k`, manifest/contentstore/HTML, sitemap/canonical/robots, smoke e leitura contextual estratificada. Falha preserva snapshot anterior.

### Famílias jurídicas sentinelas

Censar e corrigir a família inteira, confirmando os números vivos: CC art. 1.641/Tema 1.236 (9); LGPD recrutamento (10); consentimento/eliminação (17); Tema 987 (25 + 19 rejeitados); Rol ANS (47); Tema 1.389 (13); Montreal (32); Lei 4.591 art. 44 (4); testamentos excepcionais (5); reincidência em embriaguez ao volante (2); órfãos (162); `duplicate_phrase` (536); vigência/lei atual (31); outros blockers jurídicos (21). Incluir súmulas/temas numerados, artigos sólidos/pontuados, prazos, valores, competência, exceções e afirmações absolutas.

### Cutover verificável

1. Paridade crua de wiring em 300 páginas estratificadas + sentinelas.
2. Toda divergência pós-correção ganha teste regressivo e fonte oficial; `legacy fail → new pass` sem adjudicação é proibido.
3. Controles negativos duros reprovam 100%; positivos evitam gate que reprova tudo.
4. Duas execuções iguais produzem hashes iguais; a segunda é no-op.
5. Alterar uma página reexecuta só seu subgrafo/partição; alterar uma fonte invalida só dependentes.
6. Blocker injetado não interrompe sujeitos independentes; crash retoma sem duplicar rede/modelo.
7. Depois de 300, operar canário real de 2.000 e reconciliação real de 10.000 dentro dos SLOs.

### Continuidade P1–P5

- **P0:** exatamente 10.000 páginas públicas aprovadas e coerentes por gate completo.
- **P1:** ≥100.000 candidatos governados/únicos, com intenção, revisão, fonte esperada, demanda e anti-doorway; packs/segmentos, índice e release O(delta) antes de cruzar 100K.
- **P2:** conectores oficiais realmente operados com termos/robots/licença, rate limit, proveniência, vigência, minimização e diagnóstico de falha. DataJud agregado/não comercial.
- **P3:** benchmark reproduzível real de 1M em cold/warm/delta 1%/crash/skew, sem backend fake, número hardcoded ou O(n²).
- **P4:** bundle imutável único (manifest/content/HTML/busca/sitemap/robots/evidência), release ID, `CURRENT` atômico, crash injection, rollback <30s e GC por reachability.
- **P5:** runtime loopback/socket, readiness ligada ao release/índices, segurança, rate/real-IP/segredos/SBOM/DR/observabilidade e smoke pelo caminho real; sem ativar DNS/credencial/launch externo por inferência.

### SLOs e testes mínimos

| Operação | SLO inicial |
|---|---:|
| warm no-op determinístico | ≤10s |
| check focado | ≤30s |
| reconciliação determinística 10K | ≤120s e ≤4GiB RSS |
| 100K governado | ≤8min, shardado |
| inventário/índice 1M | ≤180s |
| ativação de release preparado | ≤5s |
| rollback forward | ≤30s |
| lookup p95 local | ≤50ms |

Etapa de 10K em minutos sem throughput/budget/stop condition é bug: profile/probe, cache, índice, shard, batch, paralelismo ou algoritmo incremental; nunca timeout maior como correção.

Testes obrigatórios cobrem identidade sem HEAD/mtime, invalidação real, reuse de blocker, limites exatos de retry, circuito/RCA, regressão de blocker, crash após CAS, recuperação de leases, processo externo intocado, aging/anti-starvation, warm/delta, isolamento de sujeito, FP/FN jurídico/editorial, fronteira não renderizável da pesquisa, escritor público único, contador público monotônico e promoção sem ultrapassar déficit.

### Ordem imediata

1. Versionar esta revisão por commit parcial e continuar imediatamente.
2. Recalcular baseline viva com produtor reproduzível e teste contra contador mentiroso.
3. Priorizar o blocker com maior `approved_pages_unlockable / critical_path_time`.
4. Implementar o primeiro corte autoritativo de `factoryworkqueue`: identidade, attempt/lease, circuito, ProductDelta e workers auto.
5. Validar 300 → 2.000 → 10.000, corrigindo famílias e construindo estoque excedente.
6. Promover coortes aprovadas até exatamente 10.000 e seguir P1–P5 sem encerrar o `/goal`.

## Mandato e diagnóstico

Você é o engenheiro-chefe, arquiteto, jurista brasileiro e orquestrador do projeto `/opt/wiki`. Grave este plano em `docs/goal/FACTORY_10K_SCALE_GOAL.md` e vincule-o ao `GOAL.md` por edição para frente, preservando o contrato vigente.

Mantenha o `/goal` ativo até existirem exatamente 10.000 páginas jurídicas aprovadas, materializadas, públicas/indexáveis e verificadas. Não use checkpoint, comentário, commit, relatório de agente ou contador histórico como prova. Não chame `update_goal complete` antes da evidência final.

Conclusão da investigação: o modelo não é o gargalo dominante. A fábrica já produziu milhares de páginas, mas a arquitetura transforma essa produção em zero páginas públicas. O GPT‑5.6 é oficialmente indicado para trabalho agente complexo, multietapas, com ferramentas e validação; use `gpt-5.6` no maior esforço efetivamente suportado. Na Responses API, o valor oficial é `reasoning.effort="max"`; “Ultra” pode nomear a modalidade da sessão, mas não deve ser inventado como valor de parâmetro da API. [Documentação oficial do GPT‑5.6](https://developers.openai.com/api/docs/models/gpt-5.6-sol)

Recalcule estes números no início porque a worktree é concorrente, mas use a fotografia de 15/07/2026 como baseline:

| Medida | Baseline |
|---|---:|
| Portfólio v2 único | 7.600 intents |
| Páginas v2 finalizadas ativas | 6.685 |
| Tombstones, excluídos da contagem | 55 |
| Páginas aparentemente limpas no auditor determinístico | 5.803 |
| Páginas com ao menos um blocker determinístico | 882 |
| Intents existentes ainda sem página | 915 |
| Gap de intents até 10K | 2.400 |
| Intents ainda com pesquisa de fonte pendente | 1.523 |
| Estoque derivado downstream | 590, stale |
| Páginas públicas/indexáveis | 0 |

As causas-raiz provadas são:

- A fila de escrita está bloqueada: o relaunch exige `intent_ids`, mas os inventários ainda contêm lotes dinâmicos sem pins; a migração one-shot não aceita o portfólio vivo porque depende de um hash global stale.
- `bootstrap-chain` executa 42 etapas seriais, stop-on-first-error, com reinício manual e recomputação global.
- Existem 246 checks `always_run`; o custo declarado soma cerca de 67,8 minutos e ainda inclui burocracia aposentada pela DEC-002.
- A promoção pública está codificada como big-bang de exatamente 10.000 páginas, mantendo `published_manifest=0` e adiando todo feedback de release.
- A fila atual tem 1.241 slots, mas cerca de 461 já estão preenchidos: cada agente entrega apenas ~3,1 páginas líquidas após pagar prompt, pesquisa, CAS e auditoria globais.
- O auditor reprova qualquer repetição de 12 tokens. Isso mistura prosa realmente templated com formulações normativas inevitáveis e afeta 653 páginas.
- O direito vivo está representado por aproximadamente 34 mil linhas de regexes verticais em dezenas de arquivos. Ausência de match não prova correção jurídica.
- Um rollout `/goal` acumulou mais de 2,2 bilhões de tokens, 10 mil execuções e cerca de 13,8% de comandos exatamente repetidos. O objetivo deve continuar, mas o estado operacional precisa sair do contexto conversacional e entrar numa máquina persistente.

## Arquitetura obrigatória

Implemente uma migração strangler: continue produzindo conteúdo enquanto o novo motor substitui progressivamente a cadeia antiga. Não faça uma reescrita big-bang e não adicione novos gates ao monólito legado.

### Modelo de dados

Introduza revisões imutáveis e content-addressed:

- `IntentRevision`: `intent_id`, `revision_hash`, área, família, tipo, lane, problema humano, delta contrafactual, evidências de demanda, claims esperados e política aplicável.
- `PageRevision`: `page_id`, `page_revision_hash`, `intent_revision_hash`, conteúdo estruturado, lane, autor, revisores, `material_claim_ids`, source pack, versões dos gates e estado público.
- `LegalClaim`: `claim_id`, proposição autoral estruturada, tipo da afirmação, jurisdição, autoridade, URL oficial, locator/artigo/tema, vigência, exceções, risco, supersessão, digest da evidência e revisão semântica.
- `GateResult`: sujeito, gate, versão, input hash, `passed|blocked|warning`, códigos de causa, evidências, métricas e revisor.
- `TaskKey`: `(node_id, subject_id, input_hash, gate_version)`.
- `ReleaseSnapshot`: snapshot anterior, delta aprovado, snapshot posterior, hashes de manifest/content/HTML/sitemap, smoke humano/Googlebot e receipt transacional.

Mudança de um intent deve criar nova `IntentRevision` e invalidar automaticamente apenas suas páginas dependentes. Nenhuma página pode continuar “ativa” depois que o significado do intent mudou silenciosamente.

### Motor único da fábrica

Crie um único comando Go, `cmd/factory`, exposto por `tools/factory`, com subcomandos:

- `plan --scope changed|all`
- `run --scope changed|all`
- `status`
- `explain <intent_id>`
- `release --target-count 10000 --cohort-size 250`
- `benchmark --records 10000|100000|1000000|10000000`

Não crie um wrapper ou comando novo para cada gate.

O grafo terá estes nós conceituais:

1. importação e normalização da revisão;
2. pesquisa de demanda, fonte e claim bundle;
3. redação estruturada;
4. gates determinísticos PT-BR/OAB/estrutura;
5. unicidade lexical e semântica;
6. adjudicação jurídico-editorial;
7. render/SEO/HTTP;
8. promoção transacional.

Cada nó declara inputs, outputs, versão, escopo e recursos. Use CAS no filesystem e índice Pebble, reaproveitando dependências já presentes. Uma alteração deve executar somente o subgrafo afetado. A abordagem de hash de ação, cache e armazenamento endereçado por conteúdo segue um padrão industrial semelhante ao cache remoto do Bazel, sem introduzir Bazel no projeto. [Bazel Remote Caching](https://bazel.build/remote/caching)

Regras de execução:

- Um erro determinístico com o mesmo `TaskKey` não pode ser repetido. Torne-o blocker estável até mudar input, evidência ou versão do gate.
- Tarefas de modelo têm uma tentativa inicial e no máximo uma correção orientada por feedback estruturado.
- Rede admite no máximo três tentativas com backoff; depois bloqueia somente as páginas dependentes.
- Use lease por página/shard; o único lock global permitido é o swap final do snapshot público.
- Locks ocupados provocam work stealing para outra tarefa, nunca polling ou espera passiva.
- Telemetria real deve medir duração, CPU, RSS, cache hit, páginas/hora, first-pass yield, tentativas e caminho crítico. Declarações de budget não contam como medição.
- O auditor deve ser puro por padrão. `audit_v2_pages.py --global` não pode escrever no repo; persistência passa a exigir flag/subcomando explícito e transacional.

### Direito vivo, fontes e unicidade

Congele a criação de regexes jurídicas específicas por página. Preserve as existentes como guardas legadas até a migração, mas novos fatos entram no claim graph declarativo.

- Armazene somente metadados, digest e resumo autoral da evidência oficial; não copie nem espelhe a fonte.
- Revalide cada URL oficial uma vez por snapshot, compartilhando o resultado entre páginas.
- TTL: 7 dias para precedentes, políticas OAB e matérias de alto risco; 30 dias para diplomas estáveis. Mudança de digest invalida todos os claims dependentes.
- Fonte viva prova disponibilidade, não entailment. Cada claim material precisa de locator, vigência, jurisdição e veredicto `supported`; `ambiguous` ou `contradicted` bloqueia.
- Páginas comuns exigem um revisor independente do redator. Criminal, tributário, previdenciário, família, saúde, LGPD e precedentes recentes exigem dois veredictos independentes; divergência escala ao engenheiro-chefe.
- Centralize hosts, exceções, OAB, CTA e políticas de fonte num catálogo versionado consumido diretamente por Go, Python e prompts. Não mantenha allowlists divergentes.

Substitua o gate “qualquer 12-grama bloqueia” por:

- 12-grama apenas como geração de candidato;
- bloqueio de near-duplicate quando Jaccard do corpo normalizado for `>=0,70`;
- bloqueio de span editorial idêntico com `>=40` tokens ou densidade repetida `>=15%`;
- títulos, metas e H1 idênticos continuam bloqueados;
- átomos normativos compartilhados só são tratados separadamente quando ligados ao mesmo `claim_id`/locator; a explicação pública continua autoral;
- escritor recebe vizinhos lexicais/semânticos antes de escrever.

Calibre o gate em corpus rotulado, não por exceções ad hoc. O Google considera doorway e scaled-content abuse a produção em massa sem valor, independentemente de IA ou autoria humana; também reprova scraping e stitching. [Políticas antispam do Google](https://developers.google.com/search/docs/essentials/spam-policies), [orientação oficial sobre conteúdo com IA](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content)

## Ordem de execução

### Marco 0 — Integrar a worktree e reabrir a escrita

Não lance novas tarefas que colidam com owners ativos. Não mate processos. Enquanto aguarda um hotspot, trabalhe numa frente independente.

1. Releia os arquivos imediatamente antes de integrar e faça commits parciais por pathspec. Nunca use `add -A`, reset, restore, checkout, stash, clean, revert, merge ou cherry-pick amplo.
2. Atualize a visão remota com `git fetch origin`, apenas para comparação. `origin/main` local estava parado desde 10/06; “ahead 1057” não prova o remoto atual.
3. Integre nesta ordem:
   - integridade de supersessão/quarentena e transação de ingest;
   - migração semântica dos pins e seus produtores/consumidores;
   - source registry, provenance e sourcewatch;
   - distinctness do portfólio;
   - 99 páginas novas pendentes, após auditoria de fonte e amostra jurídica;
   - perfis de checks, removendo os gates aposentados antes de incluir distinctness;
   - workflow de segurança, isoladamente.
4. Preserve `.claude/settings.local.json` como configuração local, sem commit.
5. Não rode a migração stale atual. Refaça-a contra o estado vivo:
   - elimine `skip/take` como identidade;
   - grave listas explícitas de `intent_ids`;
   - use hashes por registro e Merkle root por lote;
   - alterações não relacionadas do portfólio não invalidam o lote;
   - teste dry-run, concorrência, crash e retomada.
6. Reabra imediatamente os ~780 slots líquidos da fila existente em lotes econômicos, sem esperar o FactoryGraph completo.
7. Faça inventário comportamental das worktrees antigas de 26 GB. Porte apenas comportamento ou teste ainda ausente; não faça merge nem apague worktrees neste ciclo.

### Marco 1 — FactoryGraph incremental

Implemente o motor novo, adaptando inicialmente os gates existentes. Mapeie as 42 etapas legadas para os oito nós do grafo e rode shadow comparison.

Perfis obrigatórios:

- `focused`: pacote/shard tocado;
- `delta-release`: páginas afetadas e seus índices;
- `full-reconciliation`: milestone ou execução agendada, nunca a cada agente.

Remova dos perfis de produto os gates processuais aposentados pela DEC-002. Não reduza PT-BR, fonte, OAB, unicidade, HTML, SEO ou publicação.

### Marco 2 — Recuperar o estoque atual

Trate blockers por causa-raiz, não por arquivo:

- 653 páginas com n-grama: classificar template editorial versus átomo normativo e reescrever somente prosa repetida real.
- 225 páginas com metadados de fonte inválidos: corrigir por URL/claim compartilhado.
- 28 páginas de direito vivo: revisar claims e vigência.
- Zerar oito títulos duplicados, cinco fontes não verificadas, duas páginas thin e uma lane inválida.
- Extrair e adjudicar claims das 5.803 páginas aparentemente limpas; “sem regex detectada” não significa aprovação jurídica.
- Materializar continuamente snapshots internos completos com flags públicas fechadas. O downstream nunca mais pode ficar em 590 quando a fonte tem 6.685.

### Marco 3 — Fechar 10K com folga editorial

Expanda o portfólio para pelo menos 11.500 intents qualificados, mantendo o excedente interno/noindex. O buffer absorve rejeições sem forçar relaxamento de gate.

Sequência:

1. Resolver os 1.523 intents com `needs_source_research=true`.
2. Escrever os 915 intents existentes sem página.
3. Criar novos intents até 11.500.
4. Escrever e revisar até haver 10.000 páginas aprovadas.

Cada novo intent deve ter:

- duas observações independentes de demanda em superfícies permitidas, ou um dado oficial de necessidade pública mais uma observação independente;
- fonte jurídica oficial específica;
- claim bundle pronto antes da redação;
- teste contrafactual explícito: qual regra, prazo, documento, procedimento, risco, resultado ou fonte muda se esta página for removida ou mesclada;
- zero distinção baseada apenas em localidade, canal, modalidade online, preço, adjetivo ou sinônimo.

Batches:

- pesquisa de fonte/claims: até 50 intents relacionados;
- redação normal: 20 páginas líquidas;
- redação de alto risco: 8 páginas;
- revisão normal: até 25 páginas por claim cluster;
- revisão de alto risco: 8 páginas.

O redator recebe intent revision, claim bundle, fontes, páginas vizinhas e restrições. Ele não pesquisa a web, escolhe fontes e escreve tudo no mesmo turno. Agentes produzem candidate packages em workspace isolado; somente o coordenador valida e promove para o JSONL canônico.

### Marco 4 — Promoção progressiva até exatamente 10K

Crie uma nova decisão que resolva o conflito atual: o requisito exato de 10.000 é gate de encerramento, não pré-condição de cada promoção.

Substitua o big-bang de [publicrelease.go](/opt/wiki/internal/publicrelease/publicrelease.go:5873) por cohorts transacionais:

- `before_count + approved_delta = after_count`;
- `0 <= before_count < after_count <= 10000`;
- delta sem URL duplicada e integralmente aprovado;
- cohort padrão de 250, ou todas as páginas disponíveis quando faltarem menos;
- swap atômico e coerente de manifest, contentstore, HTML, canonical, robots e sitemap;
- receipt com hashes before/delta/after;
- rollback ensaiado como nova transação forward, preservando evidência.

Promova o primeiro cohort assim que ele fechar o release completo; não espere 10K. Página bloqueada permanece noindex sem bloquear páginas independentes.

No snapshot final, prove exatamente 10.000 URLs e não publique o backlog excedente. Para a arquitetura futura, use sitemap index com shards de até 40 mil URLs, abaixo do limite oficial de 50 mil. [Documentação oficial de sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)

Não use a Indexing API para páginas jurídicas; ela é destinada a `JobPosting` e eventos de transmissão. [Google Indexing API](https://developers.google.com/search/apis/indexing-api/v3/using-api)

## Orquestração GPT‑5.6 no esforço máximo

Crie agentes customizados para `factory_engineer`, `legal_researcher`, `legal_writer`, `legal_reviewer` e `release_auditor`, todos com `model="gpt-5.6"`. Em adapters da Responses API, use `reasoning.effort="max"`; no Codex CLI, use o maior esforço aceito pela versão instalada e registre o valor real, sem confundir o rótulo de produto “Ultra” com parâmetro de API.

Não fixe `agents.max_threads`, `agents.max_depth` nem quantidade de subagentes no
repositório. O orquestrador admite todas as frentes independentes justificadas
que o runtime liberar e mede CPU, RAM, I/O, latência e throughput por onda. Pressão
de recurso reduz leases da classe saturada por backpressure temporário e
observável; nunca vira teto global persistente. O pool de quatro slots injetado
na sessão de 2026-07-20 é `external_agent_capacity_cap` reproduzido, não política,
recomendação ou valor a copiar para configuração.

Regras:

- Um implementador e um revisor no máximo por hotspot.
- Agentes não commitam nem escrevem o mesmo artefato canônico.
- Comentário de agente é hipótese; só código, diff, dado e teste reproduzível contam.
- O engenheiro-chefe continua trabalhando enquanto agentes rodam.
- Não faça polling repetitivo de status. Espere evento ou timeout e mude para outra frente.
- O `/goal` permanece ativo, mas use epochs curtas com estado persistido no FactoryGraph. Compactação ou retomada não autoriza repetir comandos nem encerrar.
- Fast mode ou uso pago adicional não é pressuposto; a arquitetura deve atingir os SLOs em modo padrão.

A orientação oficial da OpenAI recomenda planos autocontidos, milestones verificáveis, registro de decisões e progresso baseado em resultados. [Codex Exec Plans](https://developers.openai.com/cookbook/articles/codex_exec_plans)

## Testes, SLOs e aceite

### Testes obrigatórios

- Testes de pureza: checks read-only não alteram `git status` nem artefatos rastreados.
- Property/fuzz tests: determinismo do DAG, invalidação mínima, cache, Merkle roots, concorrência, leases e crash recovery.
- Corpus rotulado com no mínimo 300 casos: 100 páginas boas, 100 defeitos reais e 100 bordas jurídicas/linguísticas.
- Gate jurídico: 100% de recall para fonte falsa/stale, vigência errada, jurisdição errada, claim contradito, promessa de resultado e infrações OAB; precisão mínima de 98%.
- Gate de duplicidade: recall de 100% no corpus adversarial e precisão mínima de 98%.
- Shadow comparison da cadeia antiga com 300 páginas e justificativa para toda divergência.
- Release crash-injection antes/durante/depois do swap; manifest, content, HTML e sitemap nunca podem divergir.
- Smoke HTTP como humano e Googlebot, canonical, robots, links internos e HTML menor ou igual a 50 KB sem runtime cliente.
- Amostra independente de 2% de cada cohort, mínimo 20 páginas, estratificada por área, tipo e lane; alto risco recebe revisão integral.

### SLOs no host atual

- `focused`: até 30 segundos.
- `delta-release` de 250 páginas: até 2 minutos, excluindo nova chamada de modelo ou rede.
- Full deterministic reconciliation de 10K: até 120 segundos e RSS máximo de 4 GiB.
- Warm no-op: até 10 segundos.
- Delta de 1.000 páginas: até 15 segundos.
- 100K full metadata/dedupe: até 10 minutos.
- 1M inventory/index: até 3 minutos e 4 GiB RSS; a evidência existente já mediu ~100 segundos e ~2 GiB.
- 10M inventory/dedupe sintético: até 30 minutos, RSS máximo de 8 GiB e nenhuma etapa O(n²).
- First-pass yield editorial `>=90%`; `>=99%` após uma correção clusterizada.
- Média máxima de 1,2 tentativa de modelo por página.
- Durante backlog disponível: pelo menos 60 candidatas/hora e 30 aprovadas/hora. Queda persistente exige profile e correção da causa, não aumento cego de agentes.

### Definição final de concluído

O `/goal` só termina quando uma única fotografia imutável provar:

- 10.000 `intent_id` ativos e materialmente distintos;
- 10.000 `PageRevision` aprovadas e pinadas à revisão exata do intent, claims, fontes e políticas;
- 100% dos claims materiais com fonte oficial, locator, jurisdição, vigência e entailment aprovado;
- zero fonte stale, claim contradito, repetição editorial bloqueante, conteúdo thin, doorway ou CTA incompatível com a OAB;
- 10.000 registros coerentes em `published_manifest`, contentstore e HTML público;
- canonical, robots e sitemap coerentes;
- smoke humano e Googlebot verde;
- release e rollback transacionais comprovados;
- `p0-cycle-close-indexable-10k` verde por evidência viva e leitura contextual.

O Provimento 205/2021 exige publicidade objetiva, verdadeira, sóbria e informativa e veda promessa de resultado, captação indevida, preços/descontos promocionais, persuasão e autoengrandecimento. Versione esse policy pack e revalide-o antes de cada release. [OAB — Provimento 205/2021](https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021)

Capacidade para 10 milhões significa storage, índices, DAG e sitemap escaláveis; não autoriza publicar 10 milhões de paráfrases. O Google recomenda gerenciamento específico de crawl budget a partir de inventários muito grandes e continua condicionando indexação a qualidade, unicidade e capacidade de servir. [Google Crawl Budget](https://developers.google.com/crawling/docs/crawl-budget)

## Assumptions

- A fonte canônica continua sendo v2; não ressuscitar v1.
- Publicação significa os artefatos públicos/indexáveis do produto e seus smokes isolados; DNS, TLS e lançamento externo permanecem fora deste P0.
- Não há `OPENAI_API_KEY` nem `ANTHROPIC_API_KEY` no ambiente atual. Use as sessões autenticadas do Codex/Claude; um futuro adapter de API não pode ser requisito para concluir 10K.
- O backlog acima de 10K permanece interno/noindex.
- Este arquivo é o prompt executável solicitado, versionado no repositório e vinculado ao objetivo vivo por edição para frente.
