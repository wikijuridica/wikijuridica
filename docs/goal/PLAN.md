# PLAN.md — Plano da fábrica jurídica escalável (P0 → P5)

Escrito na Fase 0 (2026-07-05), antes de qualquer implementação, com base em leitura direta de código, dados vivos e histórico (ver BUGLOG.md e DECISIONS.md). Este arquivo é o plano de execução; STATUS.md registra o progresso.

> **Leitura viva em 2026-07-20:** os números originais desta seção são o diagnóstico
> histórico da Fase 0 e não são contadores operacionais atuais. O estado verificado é:
> `published_manifest=0`; portfólio V2 com 10.041 intenções únicas; 7.661 intenções
> possuem corpo ativo pertencente ao portfólio; déficit real de corpo=2.380; estoque
> aceito downstream=6.846; release transacional antigo=209; páginas públicas jurídicas
> indexáveis=0. Antes de qualquer P1–P5 vale o gate D4 de revisão integral da worktree.
> P0 segue até 10.000 páginas aprovadas, públicas/indexáveis e verificadas — intenções,
> linhas brutas, partials, tombstones, rascunhos ou páginas noindex não contam.

## 1. Estado real encontrado (resumo verificado)

- **Publicação:** `published_manifest` = 0 páginas. Houve 8.263 publicadas em 25/06, zeradas por gate em 29/06 (BUG-002).
- **Porta de publicação soldada:** o gate final exige um manifesto de aprovação que nenhum código gera (BUG-001).
- **Conteúdo:** 10.000 textos bloqueados (300 drafts + 9.700 expansão). Ortografia PT-BR impecável; estrutura reprovada — molde permutado, 14.327 pares near-duplicate, headings idênticos ×4.599 (DEC-004).
- **Aproveitável do estoque:** taxonomia de intenções (área × problema × cenário × contexto), 23.366 URLs de fonte oficial específicas (deep-link com âncora de artigo), metadados de demanda, infraestrutura Go de render/sitemap/robots/servidor.
- **Suíte:** 294 checks, ~276 sem cache de contexto (BUG-004); governança processual dominante (BUG-003).
- **Servidor:** `cmd/server` on-demand com cache em disco + `cmd/build` estático; ambos condicionados ao `published_manifest`.

## 2. Princípios da nova engenharia

1. **Gates medem o produto** (texto, HTML, SEO, fonte, unicidade), não o processo. Governança mínima (DEC-002).
2. **Publicação tem caminho de abertura** objetivo, com dono e trilha de auditoria (DEC-003). Aprovado promove; reprovado vira correção do elo específico. Nunca mais zerar produto aprovado.
3. **Substância única por página**: a unidade de autoria é a célula tema×cenário, escrita de verdade, não permutada. Variação estrutural (ordem, profundidade, vocabulário de headings) é obrigatória e verificada.
4. **Escala O(n·log n) ou melhor**: dedupe por SimHash/LSH e embeddings aproximados (infra já existe: `external_dedupe_oracle` usa simhash+hnsw); validação incremental por shard com fingerprint de entrada; nada de all-pairs.
5. **Incremental por padrão**: todo gate caro roda apenas sobre o delta (registros com fingerprint de corpo alterado), com reconciliação periódica barata.

## 3. Fases de execução

### Fase A — Governança e destravamento (imediata)
- A1. Pré-commit leve: build + vet; remoção dos checks processuais do hook (DEC-002).
- A2. Adendo de regime nos contratos (`AGENTS.md`, `GOAL.md`) apontando para `docs/goal/` como estado vivo; sem reescrever o histórico.
- A3. Congelar o ledger de 1,76 GB (sem novos appends; `.gitignore` de novos artefatos de runtime volumosos).
- A4. **Concluído por integração transacional equivalente**: `internal/publicrelease/approval.go` prepara, persiste e revalida o manifesto `promotion_public_write_approved`; `cmd/promote-authorial-mass-public-release` fornece verdict e subjects ao executor, que só abre a aprovação dentro da transação pública autenticada. Não criar um segundo comando de aprovação independente. O bloqueio vivo é produzir o verdict/manifest transacional atual a partir do estoque v2 aprovado.
- A5. **Configuração oficial do Codex e capacidade proporcional:** usar somente chaves
  documentadas pelo Codex (`features.multi_agent` e, quando o dono escolher um valor
  explícito, `agents.max_threads`); manter `agents.max_threads` ausente por padrão e não
  criar `agents.v2`, `workers=2` ou teto do projeto. Isolar `CODEX_HOME` por sessão tmux,
  sem herdar valor global stale, preservar config/autenticação oficial do usuário
  `rafael` e exigir `codex --strict-config doctor --json` verde. Capacidade observada da
  ferramenta em uma sessão é evidência transitória: usar todos os slots disponíveis e
  ondas de subagentes, mas nunca converter esse número em constante ou alegar que ele
  veio da configuração local sem prova. A documentação oficial viva explicita que a
  ausência de `agents.max_threads` usa o padrão Codex de 6 threads abertas — não significa
  “ilimitado”. Para uma operação que peça mais capacidade, o launcher deve receber o valor
  proporcional escolhido pelo dono/orquestrador em `--max-agents=N` ou
  `AI_CODEX_MAX_THREADS=N` e traduzi-lo apenas para o override oficial
  `-c agents.max_threads=N` daquele processo; não existe sentinel oficial
  `adaptive`/`unlimited`, e não se deve inventá-lo nem persistir um número como política do
  repositório.

### Fase B — Fábrica de conteúdo v2 (o coração do P0)
Unidade de conteúdo: **célula editorial** = (área, tema, cenário, contexto de urgência/documento). O estoque atual fornece a taxonomia (~10 áreas, 27 seeds → reorganizar em ~300–500 temas × 20–35 cenários).

- B1. **Base de conhecimento jurídico** (`data/knowledge/*.jsonl`): módulos autorais por tema com: fundamento legal específico (lei+artigo, súmula, resolução, com URL da fonte já auditada), prazos reais, documentos, etapas do procedimento (judicial e extrajudicial), órgão/canal digital, erros comuns, quando o caso NÃO se sustenta. Autoria: subagentes-redatores com revisão jurídica (eu, como advogado responsável pelo conteúdo, defino o padrão e reviso amostras estratificadas).
- B2. **Redação por célula em lote**: subagentes escrevem o corpo de cada página em PT-BR natural, com brief = módulo de conhecimento + intenção + persona da busca. Regras duras: nada de frase-molde global, estrutura sorteada de pools amplos, profundidade variável (600–1400 palavras), title/meta/H1 únicos, paid-intent no corpo quando a lane for comercial, lane informativa sem CTA (BPC/LOAS etc.).
- B3. **Gates de produto por lote** (reaproveitando os oráculos existentes): dedupe SimHash/HNSW (par >0.70 reprova e re-escreve), frases mecânicas (n-gram repetido entre páginas reprova), ortografia (ptbrspell/LanguageTool), fonte oficial viva (HEAD 2xx/3xx), OAB/CTA, HTML ≤50 KB. Reprovado → fila de reescrita automática com diagnóstico do elo.
- B4. **Throughput planejado**: lotes de 50–200 páginas por rodada de agentes; contadores em STATUS.md a cada marco. O pipeline aceita substituição gradual: células aprovadas entram no estoque publicável; o estoque velho permanece bloqueado como matéria-prima.
- B5. **Recuperação antes de nova ingestão:** finish-forward autenticado do journal
  V2 efetivo `committing/0` concluído em 2026-07-20, sem apagar os 2.082 temporários
  nem reconstruir estado manualmente; falta revisar/commitar os artefatos finais por
  pathspec e manter a inspeção read-only como gate anti-loop. Em seguida corrigir 6 IDs ativos duplicados, 156 corpos fora do
  portfólio, 39 intents apenas skipped e produzir os 2.380 corpos faltantes pela
  fábrica autoral; recontar sempre pela interseção portfólio×corpo ativo canônico.

### Fase C — Suíte leve e escalável
- C1. Propagar `RunContext` cacheado a todos os checks que leem repositório/manifest/verdict (BUG-004).
- C2. Perfis de validação: `dev` (build+vet+testes do pacote tocado), `release` (gates de produto sobre o delta), `full` (reconciliação completa, sob demanda). Medir e registrar tempos.
- C3. Gates incrementais por fingerprint de corpo: reprocessar só o que mudou.

### Fase D — P0: publicar as 10.000
- D1. Selecionar deterministicamente 10.000 células aprovadas (nem mais, nem menos — `p0-cycle-close-indexable-10k` exige exatamente 10.000).
- D2. Rodar a cadeia: readiness → revisão → release evidence → manifest transaction → verdict → staging → `approve-public-release` → `promote-authorial-mass-public-release --allow-public-write`.
- D3. Verificar: `published_manifest`=10.000, HTML real em `public/`, sitemap/canonical/robots coerentes, smoke HTTP/Googlebot, check de fechamento verde, leitura contextual de amostras estratificadas.
- D4. **Fronteira obrigatória de integração da worktree antes de P1–P5.** Esta tasklist
  bloqueia o avanço para P1, P2, P3, P4 e P5 até todos os itens abaixo terem evidência:
  - D4.1. Capturar o inventário vivo de todos os arquivos staged, unstaged e untracked,
    inclusive divergências `MM`/`AM`, e classificá-los por família, produtor,
    consumidor, integração, dependência, risco e autoria concorrente.
  - D4.2. Ler cada arquivo vivo, seus diffs staged/unstaged, histórico relevante e o
    fluxo produtor→artefato→consumidor antes de decidir; status staged, checkpoint,
    comentário de IA ou autoria Claude/Codex nunca provam correção.
  - D4.3. Revisar adversarialmente código, conteúdo jurídico, dados, conectores,
    ferramentas e configuração; integrar o que for útil e corrigir para frente todo
    falso-verde, falso-vermelho, obsolescência, lacuna de consumidor ou incompatibilidade.
  - D4.4. Validar proporcionalmente cada família, incluindo segurança, performance,
    fonte/OAB/PT-BR, anti-duplicidade e prova de publicação zero quando aplicável;
    comando pesado só roda após leitura da causa e com orçamento/stop condition.
  - D4.5. Reler os paths imediatamente antes de cada commit, usar somente pathspec
    explícito e repetir o inventário até não restar arquivo versionável sem
    classificação, decisão e evidência. É proibido merge/cherry-pick, `reset`,
    `restore`, `stash`, `clean`, descarte ou commit cego da worktree concorrente.
  - D4.6. Tratar explicitamente como **worktree pendente — revisão antes de P1–P5**
    as famílias DataJud/TPU: importer+catálogo oficial, planner agregado,
    executor/CAS/privacidade/termo CNJ, receipt reproduzível da TPU e adaptador
    consumidor downstream. Os 14 IDs estáveis e os 3 IDs corrigidos por semântica
    exigem migração declarada; TRT não pode herdar TST/CSJT por suposição; teste focal
    verde não autoriza commit enquanto a evidência continuar órfã da fábrica viva.
  - D4.7. Revisar e integrar também as famílias que desbloqueiam a confiança da
    fábrica: 4.993 snapshots staged (atualmente NO-GO, nunca commit em massa), auditor
    e quarentena do corpus, fechamento `collect-oracle` com estado não verificado,
    `legalfacts`/grounding e seus consumidores `fiscalization`/sidecars, além do
    registro seletivo nos checks/perfis/performance centrais. Cada produtor precisa
    de consumidor real, gate contra falso verde e custo medido; artefato órfão,
    índice O(N) por claim ou integração central concorrente permanece bloqueador.
  - D4.8. Fazer RCA forense do **loop grave de 2026-07-21, da madrugada até a manhã
    (`America/Sao_Paulo`)**, reconstruindo por rollout, processos, comandos, durações,
    CPU/RSS/I/O, caminhos de cache, arquivos alterados, commits e vetor de produto o
    que foi repetido e por que o supervisor/anti-loop permitiu a repetição. O resultado
    deve virar correção executável antes de encerrar o P0: identidade semântica estável
    da unidade de trabalho (sem timestamp, mtime, path temporário ou microcommit),
    orçamento e stop condition, medição de throughput/delta, proibição de rerun com
    entrada+implementação+blocker iguais, circuito por estratégia/família e teste
    regressivo que reproduza o falso cache observado no gate Go. Log, tempo consumido,
    CPU, arquivo tocado ou check executado não contam como progresso. Nenhum Codex pode
    repetir a estratégia terminal sem mudança causal comprovada; após a primeira falha
    determinística deve ler produtor/consumidor e aplicar patch, e após a segunda deve
    abrir o circuito e mudar de frente. O gate precisa provar warm no-op em segundos e
    delta proporcional; aumentar timeout não satisfaz esta task.
- D5. **Dados externos e fontes não são texto publicável:** operar DataJud como matriz
  agregada canônica (387 pares atuais) somente depois de reconciliação transacional,
  sem processos/partes/corpos; corrigir fontes por matcher mais específico e rechecagem
  viva. Sinal externo prioriza autoria, mas nunca substitui fonte jurídica específica,
  texto próprio, revisão, anti-duplicidade e release completo.

### Fase E — P1: 100.000 candidatos governados
- Expandir a taxonomia (temas × cenários × contextos) para ≥100k intenções com lineage, status explícito e gates computáveis; tudo bloqueado/noindex. Sem exigência de corpo completo: candidato governado = intenção + fonte esperada + módulo de conhecimento associado + score de demanda.

### Fase F — P2: cobertura de fontes oficiais
- Registrar conectores/políticas para INPI, Receita, PGFN, ANPD, SUSEP, ANS, BCB, Consumidor.gov.br, Anatel, DataJud, tribunais, Câmara, Senado — proveniência metadata-only, nunca cópia.

### Fase G — P3: benchmark de 1M
- Benchmark reproduzível (ingestão, leitura, indexação, dedupe, seleção, release subset, memória, CPU, tempo) provando capacidade de inventário de 1M de URLs sem O(n²). Documentar arquitetura para milhões em `docs/goal/SCALE.md`.

### Fase H — P4: operação de produção
- Release estático versionado `releases/<id>/public`, promoção atômica por ponteiro, rollback drill executado de verdade, monitoramento, runbook.

### Fase I — P5: pronto para tráfego (DEC-005)
- Cloudflare Tunnel: config completa versionada (`ops/`), serviço systemd preparado, sem token/credencial (dono conecta quando tiver a chave).
- Proxy: avaliar nginx vs Caddy vs servir direto do binário Go atrás do tunnel; decidir com justificativa técnica (DECISIONS.md). Nada baseado em /opt/divorcio.
- Domínio NÃO publicado. Checklist final de launch documentado.

## 4. Critérios de conclusão (espelho do /goal)
1. P0–P5 completos conforme contratos (com as redefinições da DEC-005).
2. 10k páginas build/serve sem gargalo; arquitetura para milhões documentada.
3. Suíte leve verde após revisão real de código.
4. Conteúdo auditado: único, natural, PT-BR correto, zero spam.
5. Tunnel + proxy preparados; domínio não publicado.
6. Worktree pendente integralmente revisada e integrada antes de P1–P5; commits parciais explícitos, sem absorver ou descartar evolução concorrente.
7. Commits limpos; docs/goal consistentes.
