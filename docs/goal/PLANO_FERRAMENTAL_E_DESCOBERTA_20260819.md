# Ferramental do Claude Code e descoberta por agentes de IA — /opt/wiki

## Context

Você pediu investigação ampla do repo (produção, arquitetura, conteúdo, gaps), com foco em
**descoberta e citação por agentes de IA**, em **plugins que ajudem o Claude Code e os subagentes**
(o projeto está sem marketplace) e em **quais MCPs manter, desativar ou criar** — exigindo dados
verdadeiros, colhidos com agentes Opus e críticos adversariais, sem confiar em comentário do repo.
Depois acrescentou: **skills importam** (não restaurar as antigas; desenhar novas, ou aproveitar as
velhas só se não tiverem bug), **tudo tem que ser testado**, e **um agente deve reler o plano para
pegar inconsistência**.

Executado: 9 frentes com agentes Opus, 3 críticos adversariais Fable e 1 revisor de consistência.
Evidências commitadas em `.agents/runtime/investigacao-20260819/`; versão longa em
`docs/goal/PLANO_FERRAMENTAL_E_DESCOBERTA_20260819.md` (commit `b10a14a4`).

**O que se descobriu, em uma linha:** o *artefato público* está excepcionalmente saudável, mas a
*camada que descreve o projeto* mente (CLAUDE.md diz "publicação zero" com 9.710 páginas no ar) e a
*instrumentação de bots de IA* está congelada desde 12/08 — justamente o que você quer acompanhar.

**A revisão derrubou três afirmações minhas** durante a redação; todas corrigidas abaixo e
registradas, porque o modo como caíram é o próprio argumento de que os dados foram checados:
(1) propus criar um timer de IndexNow que teria feito o Bing ignorar o canal; (2) descrevi o
mecanismo do IndexNow pelo script errado; (3) chamei de "104 páginas prontas fora do ar" o que são
tombstones deliberados sem corpo.

## Estado real medido (contra o que a doc afirma)

| Doc afirma | Medição |
|---|---|
| "publicação zero", "nenhuma página pública" | **9.710 publicadas**, 9.930 HTMLs, sitemap 9.926 URLs, 15/15 HTTP 200 |
| "~6.584 páginas em 445 shards" | **9.833 registros em 871 shards** = 9.710 publicados + 19 supersedidos + **104 tombstones sem corpo**. Estoque real de páginas: **9.712** (a lane 6 chamou 9.814 de "ativos"; 102 deles são registros de skip) |
| "domínio só vai ao ar em P5" | no ar: nginx dedicado + 10 réplicas de túnel |
| "`httpserver.go:243` → `log.Fatal`" | `grep -c log.Fatal internal/httpserver/httpserver.go` = **0**; real é `httpserver.go:479-482` + `cmd/server/main.go:36` |
| frontboard = "plano vivo" | congelado em **04/08**; **72 de 73** tasks sem nenhum campo de data (valor da lane 7) |

Qualidade do artefato (varredura integral de 9.930 HTMLs): 0 título duplicado · 0 description
duplicada · 0 mojibake · 0 link quebrado · 0 falha de JSON-LD · H1 único em 9.930/9.930 ·
0 página > 50 KB · 0 defeito real de OAB (6.968 "hits" brutos, todos falsos positivos verificados
um a um). As únicas violações de contrato no `<head>`: **2 titles de 69 chars e 1 description de
167** — item 9 do Bloco B.

---

## Bloco 0 — PERECÍVEL: fazer primeiro, hoje

`tools/measure-crawl-coverage:110` tem `RETENCAO_DIAS = 8`, e o comentário do código explica:
pedir dia mais velho devolve `code: quota` — *"cannot request data older than 1w1d"*. A cobertura
dos 9 bots (todos os de IA) está congelada em **2026-08-12**; hoje é 19/08 = **7 dias**. A janela
para recuperar esse dado fecha em cerca de um dia, e depois ele é **irrecuperável**.
**Ação**: rodar `tools/measure-crawl-coverage` para os 10 crawlers agora, antes de qualquer outra
coisa do plano, e só então estender o `ExecStart` do unit (Bloco B item 1).
**Teste**: `crawl_coverage_daily.jsonl` passa a ter linhas de 13/08 a 19/08 para os 10 crawlers.
⚠️ Este item **não pode ser executado em plan mode** (escreve em `data/ops/`), então a janela
depende da aprovação: aprovar hoje ainda recupera 12/08; amanhã, não.

**Junto com ele, dois acertos de coerência do próprio trabalho desta sessão:**
- ✅ **FEITO**: este arquivo era a v1 (commit `b10a14a4`) e afirmava coisas que a revisão derrubou
  — "publicar as ~104 páginas prontas", o mecanismo do IndexNow pelo script errado, o `hookify`
  aprovado e "Legal Data Hunter: cobertura EUA/UE" como fato. Foi substituído pela versão final
  aprovada; a v1 permanece no histórico do git. Deixá-lo como estava seria criar exatamente o
  contrato que mente que o Bloco E existe para corrigir.
- **lane8 (red-team do plano) e lane9 (revisão de consistência) só existem fora do repo** — o
  laudo do red-team está em `~/.claude/plans/recursive-churning-sutherland-agent-*.md` e o da
  revisão só no transcript, porque o plan mode bloqueou a escrita. É trabalho pago vivendo fora do
  versionamento, a mesma falha que a lane 4a reportou em 2.103 arquivos: materializar os dois em
  `.agents/runtime/investigacao-20260819/` e commitar.

## Bloco A — ferramental (barato, destrava o resto)

**Marketplace**: `claude plugin marketplace add anthropics/claude-plugins-official`.
Ordem imposta por teste próprio (`claude plugin details` responde "not found" sem marketplace):
add → `details` → **ler o código do plugin** → `validate --strict` → `install --scope project` →
`/reload-plugins` → smoke.

| Plugin | Custo | Por quê | Teste de aceite |
|---|---|---|---|
| `gopls-lsp` | **0/0 tokens** | 504 pacotes Go; `gopls` já em `/home/rafael/go/bin/gopls` | resolver a definição de `publishedmanifest.Validate` e cair em `internal/publishedmanifest/publishedmanifest.go` |
| `session-report` | 75/1.144 | aponta qual prompt custou caro (o `ai-tokens` só dá total) | gerar relatório e cruzar com `ai-tokens --today` |

**`hookify` CORTADO** (estava aprovado na primeira versão; o red-team derrubou). A justificativa que
eu tinha dado — "regra barrando git destrutivo passa a valer para todo subagente" — **já é verdade
sem plugin nenhum**: `~/.claude/hooks/git-guard.sh` é `PreToolUse` global de Bash e sua lista já
cobre `reset --hard`, `checkout --`, `restore`, etc., para todo subagente em todo projeto (ele
chegou a bloquear um comando meu nesta sessão). Pagar 297 tokens sempre + 11.928 por invocação por
capacidade existente é desperdício. Some-se que `--scope local` **não é sandbox**: ativaria os
hooks para toda sessão concorrente em `/opt/wiki`.

Recusados: `code-simplifier` (duplica `simplify` e colide com ZERO REGRESSÃO) · `commit-commands`
(atropela o padrão `add` separado + `-F`) · `data-engineering` (**alias de `astronomer-data`**,
Airflow, 6.060 tokens) · `claude-md-management` (editaria contrato) · `context7` (**o conector MCP
homônimo já está no keep do Bloco A/MCP — o plugin duplicaria a mesma capacidade pagando contexto**)
· `github`/`greptile`/`semgrep`/`sonarqube` (SaaS ou conta) · `serena` (redundante com gopls-lsp).
Condicionais: `duckdb-skills` (binário ausente — exige ADR + benchmark que responda uma consulta
sobre os 871 shards e bata com o resultado do python3 atual) · `playwright` (decidir pelo teste
nomeado sobre `.agents/runtime/staging/render-audit-html/`).
Pendência: o catálogo **não tem campo de licença** — sai do repositório de origem antes do install.

**MCPs — manter 5, desativar 75.** Medição: **zero chamada MCP em 1,66 GB de transcript**
(6.669 arquivos — recontagem da lane 3b) contra **42 conectores injetando bloco de instruções em
toda sessão**. O red-team tentou 5 hipóteses de refutação (a mais forte: regex truncando nomes
> 80 chars, testada com re-varredura sem teto) e só emendou o alcance para "zero em toda a
evidência local observável".
Manter: `Advanced GSC` · `Ahrefs` · `Keyword Tool` · `Context7` (já conectado, sem cadastro novo —
diferente de instalar o plugin homônimo) · `MDN`.
**`Legal Data Hunter` cortado com o motivo certo**: a primeira versão dizia "cobertura EUA/UE" como
se fosse medido; a lane 3 declara textualmente que **não houve chamada-teste**. O motivo honesto é
**falta de prova de cobertura brasileira + custo de contexto**, e o corte é reversível — se ele
fizer falta, uma chamada com norma brasileira decide.
Aritmética conferida: **80 = 5 manter + 75 desativar**; desses 75, **3 já constam** em
`disabledMcpServers` (Gmail, Calendar, Drive) → **72 conectores novos**, em 2 formatos = 144
entradas a acrescentar às 7 existentes. **A lista nominal executável é a tabela de 80 linhas de
`lane3-mcp-medicao.md`, coluna de veredito** — os grupos (jurisdição, cadastro, redundância,
incompatível, memórias, raciocínio, mídia) são só o racional e cobrem 45 dos 75.
**Teste**: sessão nova em `/opt/wiki`; os blocos dos 72 somem do system prompt, os 5 mantidos
respondem a uma consulta real. Abrir a sessão de verificação **também a partir de um subdiretório**
— a chave `projects` parece ser resolvida por cwd exato, e uma sessão iniciada em subpasta pode não
herdar o disable (ponta que o red-team levantou e ninguém fechou). Reversível — é uma linha em JSON.
**MCP que falta**: só um caso — busca semântica no acervo v2, servidor local em Go com índice e
embeddings **quentes entre chamadas**. **Teste de decisão** antes de virar ADR: medir a latência do
fluxo atual de anti-template sobre 500 páginas; só promove se o custo medido justificar.

---

## Bloco B — descoberta e citação por agentes de IA (maior alavanca)

**Quem cita quase não rastreia** — com o `as_of` de cada linha, porque eles diferem:

| bot | função | cobertura | as_of |
|---|---|---|---|
| googlebot | busca | 73,1% | **19/08** |
| gptbot | treino (não cita) | 50,75% | 12/08 |
| claudebot | treino | 21,77% | 12/08 |
| oai-searchbot | busca/cita | 1,00% | 12/08 |
| chatgpt-user | usuário/cita | 0,33% | 12/08 |
| bingbot | busca/cita (Copilot) | 0,16% | 12/08 |
| perplexitybot | busca/cita | 0,00% | 12/08 |

Os percentuais de IA são **piso congelado em 12/08** — não citar como número corrente até o Bloco 0
rodar. O que **está fresco** (série saneada até 19/08) e sustenta a direção são as requisições:
bingbot 472 contra googlebot 9.400, perplexitybot 0. 3.793 URLs (38%) sem IA é da mesma leitura
congelada. robots.txt **não** é o gargalo (todos os que citam estão permitidos; 9 UAs recebem
SHA-256 idêntico — zero cloaking).

1. **Descongelar o instrumento — antes de qualquer conclusão numérica.** `tools/measure-crawl-coverage`
   suporta os 10 crawlers (`CRAWLERS`, linha 120), mas `wikijuridica-crawl-coverage.service` roda
   `--crawler googlebot` (linha 33 do unit). Estender o `ExecStart` aos 10 — o código já protege a
   lista com MERGE, não substituição. **Teste**: `crawl_coverage_daily.jsonl` com linha de hoje para
   os 10, não só googlebot.
2. **Citação real não tem instrumento — e isso precisa ser dito.** `ai_citation_signal` é
   `is_citation_count:false`, `is_lower_bound:true`: rastreio é **proxy**, não citação. O produtor
   `tools/measure-ai-citation` existe (48 KB) mas **não há unit systemd** — rodou uma vez em 12/08 e
   parou. **Ação**: criar `wikijuridica-ai-citation.{service,timer}` espelhando o de cobertura; e
   construir a medição de citação correlacionando as consultas/páginas do `Advanced GSC` (mantido no
   Bloco A) com os fetches `is_citation_interest` de `chatgpt-user`/`oai-searchbot` por URL e data.
   **Teste**: `systemctl start wikijuridica-ai-citation.service` → exit 0 e última linha de
   `ai_citation_signal_daily.jsonl` com a data de hoje. Se citação direta não for mensurável,
   registrar **"sem instrumento"** explicitamente, em vez de deixar o proxy passar por medida.
3. **IndexNow e WebSub não estão quebrados — e o incremental está dormente.** O WebSub se recusa a
   pingar porque o feed tem o mesmo SHA-256 desde 13/08 (comportamento correto: repingar
   descredencia o publicador). O IndexNow é disparado pelo deploy em `tools/deploy-publico:689` via
   **`generate-indexnow-direct-submit --de-arquivo`**, sobre os alvos de purga daquele deploy — ou
   seja, já é o delta do deploy e **não precisa de timer**. Mas o
   `generate-indexnow-incremental-submit`, escrito em 12/08 com a lógica de `content_sha256`
   justamente para não reenviar URL que não mudou, **não tem nenhum caller de produção**: trabalho
   pago e dormente. **Ação**: ligá-lo ao deploy ou registrar por que fica dormente.
   **Teste**: um deploy real produz linha nova em `indexnow_direct_submissions.jsonl` com HTTP 200,
   e nenhuma URL não modificada é reenviada.
4. **As "104 páginas fora do ar" não existem — o que existe é gargalo de catálogo de fontes.**
   Medido registro a registro: as 104 são **tombstones deliberados** (`skipped: true` com
   `skip_reason` escrito) e **só 2 têm corpo**. As razões são o anti-fraude funcionando ("melhor
   pular do que inventar proveniência", "WAF do STJ bloqueou 403"). Distribuição: **57 catálogo/gate
   strict** · **21 allowlist estrangeira** · **7 fonte inacessível/WAF** · 19 outros.
   A causa dominante é `v2_source_hint_catalog.json` não ter entrada exata para os `source_hints` —
   em dezenas de casos a fonte oficial **foi verificada ao vivo** e o gate recusou por falta da chave.
   **A ferramenta já existe**: `tools/generate_source_hint_catalog_normas_legbr.py` resolve o slug na
   API pública do LexML/Senado **sem credencial**, verifica ao vivo (HTTP 200 + corpo com o número do
   ato), grava no catálogo, metadata-only e idempotente; `tools/reconcile_v2_strict_source_stock.py`
   aplica ao estoque (conservador: nunca adiciona URL ausente). **Ação**: rodar sobre a fila de hints
   não resolvidos. Uma heurística de texto sugere ~21 dos 57 como candidatos diretos — **isso é
   estimativa, não medição**: o número exato sai lendo os `source_hints` no `portfolio_v2`, e é o
   primeiro passo. **Teste**: tombstones por `skip_reason` antes/depois; nenhuma entrada nova de
   catálogo sem HTTP 200 verificado ao vivo.
5. **Vertical cidadania travada por critério de allowlist.** Os 21 são todos `cid-*` e os domínios
   recusados — `normattiva.it`, `gazzettaufficiale.it`, `giustizia.it`, `esteri.it`, `dre.pt`,
   `boe.es` — são **o equivalente estrangeiro do planalto.gov.br**. A allowlist só admite
   `gov.br/jus.br/leg.br/mp.br`, então norma italiana não tem como ser citada e o pipeline prefere
   pular. **Ação**: estender a allowlist ao diário oficial e ao portal legislativo oficial **do país
   de origem da norma**, com ADR, mantendo verificação viva e a proibição de copiar o corpo.
   **Teste**: páginas de cidadania saem com fonte oficial estrangeira (URL + data) e o gate continua
   reprovando agregador ou escritório estrangeiro — amplia-se "oficial de outro país", não "site de fora".
6. **Grafo interno é a alavanca de descoberta que sobra.** Links no `<main>`: mediana 7 e
   **p10 = p90 = 7** — módulo de "relacionados" idêntico em todas, quase nenhum link contextual no
   parágrafo; é assim que 3.793 URLs ficam sem nunca ser tocadas. Diferente do IndexNow, aqui não há
   contraindicação de protocolo: link interno é o canal que o próprio site controla.
   **Ação**: linkagem por entidade jurídica no corpo, em `internal/render`. **Teste**: distribuição
   de links no `<main>` (hoje p10=p90=7) e URLs alcançáveis em N saltos da home, antes/depois; nenhuma
   página acima de 50 KB nem link quebrado novo.
7. **`lastmod` defasado**: 28 dos 31 shards declaram `2026-08-06` com publicação de 13/08.
   **Teste**: `lastmod` de cada shard bate com a publicação mais recente que ele contém.
8. **JSON-LD**: 1.863 artigos sem `FAQPage` (lane 4b) e 3.995 sem `Legislation` (lane 5).
   ⚠️ Reconciliar antes de agir — lane 4b mediu 1.863, lane 5 mediu 1.641 com critério diferente.
9. **3 violações de comprimento no `<head>`**: 2 titles de 69 chars
   (`/sucessoes/holding-imovel-rural-georreferenciamento/`, `/tributario/aduana-drawback-isencao-reposicao-estoque/`)
   e 1 description de 167. **Teste**: varredura dos 9.930 com `html.unescape` devolve 0 fora de
   20–65 (title) e 0 fora de 70–160 (description).
10. `llms.txt` / `.well-known`: **continuam rejeitados** — sem evidência nova de consumidor declarado.

---

## Bloco C — engenharia

1. **CRÍTICO: uma issue no manifest derruba o servidor inteiro.** Verificado por leitura direta:
   `publishedmanifest.go:982-984` gera issue para HTML ausente → `httpserver.go:479-482` `New()`
   retorna erro → `cmd/server/main.go:36` `log.Fatal`. Um defeito em 9.710 registros aborta o boot,
   sem degradação parcial. **Onde editar**: `publishedmanifest.Validate` passa a distinguir issue
   global de issue por-registro e devolver as rotas a excluir; `httpserver.New` (linha 479) só
   devolve erro para issue global.
   **Três condições inegociáveis** (o red-team mostrou que sem elas a partição vira defeito pior):
   (i) a rota excluída sai **também do sitemap servido** — senão o sitemap anuncia URL que o
   servidor não tem, e 404 ao Googlebot é a incoerência que o contrato mais proíbe; (ii) enquanto
   houver issue por-registro, um **check fica vermelho** — trocar gate barulhento por log silencioso
   é exatamente como o instrumento de bots ficou 7 dias congelado sem ninguém notar; (iii) **teto
   de issues**, acima do qual aborta como hoje. **Teste**: remover um HTML → servidor sobe com 9.709,
   a rota some do sitemap servido, e o check acusa vermelho.
2. **`check-untracked-product-inventory` reprova agora** (exit 1, `untracked_produto=2103`).
   **Teste**: exit 0 e `ignored_sensitive_failures=0`.
3. **Teste vermelho pré-existente**: `TestRunContextFrozenAccessorsAreConcurrencySafe`
   (`internal/checks/run_context_parallel_test.go:19`) morre por `signal: terminated` aos 532 s,
   idêntico no HEAD anterior; varre o repo real com 64 goroutines. **Ação**: fixture bounded e
   identificar quem envia o SIGTERM. **Teste**: o teste passa em < 60 s.
4. **7 dependências de runtime sem ADR** (`meilisearch-go`, `typesense-go/v3`, `opensearch-go/v4`,
   `bluge`, `miekg/dns`, `simdjson-go`, `jsonschema/v6`). **Teste**: `grep -rlE` dos 7 em
   `docs/adr/` devolve os 7, cada um com licença e versão fixada.
5. **CSS inline de 7.911 B/página** (35% do HTML; ~78 MB por crawl). **Teste**: bytes de `<style>`
   antes/depois em 200 HTMLs; aprovado se a mediana cair abaixo de 2.000 B, nenhuma página passar de
   50 KB e `./tools/check-http-smoke` seguir verde.
6. **20 publicações vivas só na worktree** e `command-ledger.jsonl` com 160 MB. **Ação**: commit por
   pathspec do manifest; classificar o ledger no `.gitignore` (nunca deletar).
   **Teste**: `git show HEAD:data/editorial/published_manifest.jsonl | wc -l` = 9710.

---

## Bloco D — skills próprias (hoje: zero)

`~/.claude/skills/` e `.claude/skills/` **não existem**. As antigas (`verify-agents` 9 usos,
`ai-bots-status` 4, `server-stats`, `code-quality`, `type-check`, `delegate`, `post-session`,
`restart-safe`, `doctor`) sumiram do disco — **não serão restauradas**, conforme sua orientação.

**As duas que sobraram** (`~/Claude/Scheduled/`), auditadas adversarialmente:
- `cowork-opus-fleet-factory` → **reescrever do zero**: `/sessions` não existe aqui e `cd ""` retorna
  exit 0 sem mudar de diretório (todo comando roda no lugar errado); regras da VM Cowork ("não usar
  git add/commit") invertem ordens vinculantes suas; o gatilho `ls v2_pages/*.jsonl | wc -l` conta
  **shards (871), não páginas** — "< 10.000" é sempre verdadeiro; fonte de escopo morta desde 04/08.
- `cowork-fable-goal-loop` → **aproveitar após 5 correções** (cd absoluto; fila hardcoded já executada
  em 22/07 → fonte viva; threshold do lock 30 × 90 min; guarda de staleness; remover a rota da VM).

**Skills novas**, em `.claude/skills/<nome>/SKILL.md` versionado, com `description` em forma de
**condição de uso** (não de cadência — o defeito apontado na auditoria):
`medir-bots` (leitor canônico `serie_saneada`) · `publicar-lote` (coerência manifest ⊆ sitemap ⊆
public) · `ler-gigante` (CHECKPOINT.md de 2,4 MB por índice/awk/sed, **nunca `tail`**) ·
`estado-real` (mede antes de confiar em contrato) · `verificar-citacao-legal` (a classe P1
permanente, ~8%).
**Teste por skill** (modelo): `claude plugin validate --strict .claude` exit 0 **e**
`claude -p "quanto o Perplexity rastreou esta semana?"` escolhe `medir-bots` e devolve **0**
(saneado), nunca 2.008 (cru). `claude plugin eval` está **indisponível** ("early access", testado),
então o `claude -p` é o teste comportamental. A verificar antes de depender: o campo `skills:` de
pré-carga em agente é documentação não testada.

---

## Bloco E — contratos que mentem (comentário que mente é bug)

Corrigir `CLAUDE.md` (4 frases + a referência fictícia `httpserver.go:243`),
`docs/goal/PROJECT_GAPS.md:11`, e dar campo de data obrigatório ao frontboard.
**Criar `tools/check-contrato-vs-medicao`**: compara o volume publicado afirmado no CLAUDE.md com o
`published_manifest` medido e sai com **exit 1** na divergência; ancorar no pre-commit — mesmo
princípio do `tools/check-arquitetura-fiel`, que já existe e funciona.

## Bloco F — retomar publicação (o que religa tudo)

Nenhum canal de descoberta volta a falar sem conteúdo novo: o WebSub só pinga com feed diferente e
o IndexNow só dispara em deploy. A meta declarada é 10.000 e há 9.710 publicadas — faltam ~290, e
**as 104 não publicadas não são estoque** (são tombstones; só 2 têm corpo). Portanto o caminho é
geração nova pelo pipeline sancionado, destravada pelos itens 4 e 5 do Bloco B (catálogo de fontes
e allowlist), não "promover o que está parado".
**Ação**: recuperar os 2 corpos redigidos que estão em tombstone — inclusive o de
`amb-direito-de-superficie`, descartado por colisão de slug (`seedTermIDFromIntentID`,
`internal/v2ingest/validate.go:788`) e cujo próprio registro diz que o corpo é recuperável no
histórico do shard; depois gerar em lote sobre os intents que o catálogo destravar.
**Teste**: `published_manifest` cresce, coerência manifest ⊆ sitemap ⊆ public permanece limpa,
`indexnow_direct_submissions.jsonl` ganha linha com HTTP 200 e o WebSub volta a pingar sozinho.

## Arquivos a criar (lista fechada)

`.claude/skills/{medir-bots,publicar-lote,ler-gigante,estado-real,verificar-citacao-legal}/SKILL.md` ·
`/etc/systemd/system/wikijuridica-ai-citation.{service,timer}` · `tools/check-contrato-vs-medicao` ·
`docs/adr/` (7 ADRs de dependência + 1 da allowlist estrangeira + 1 do duckdb, se adotado) ·
`.agents/runtime/investigacao-20260819/lane8-redteam-do-plano.md` e `lane9-revisao-consistencia-plano.md`
(materializar o que o plan mode impediu de gravar) · reescrita de `cowork-opus-fleet-factory` e
correção de `cowork-fable-goal-loop`.

## Verificação end-to-end

1. `claude plugin validate --strict .claude` → exit 0.
2. Sessão nova em `/opt/wiki`: os 72 conectores sumiram do system prompt, os 5 mantidos respondem.
3. `./tools/go-modern run ./cmd/check <nome>` nos checks tocados; teste focado do pacote alterado
   (nunca `./...`).
4. `./tools/check-http-smoke` + amostra `curl` com status, tamanho e `lastmod`.
5. `crawl_coverage_daily.jsonl` e `ai_citation_signal_daily.jsonl` com linha de hoje.
6. `./tools/check-untracked-product-inventory` → exit 0.

## Ordem

**0** perecível (rodar a cobertura dos 10 hoje — a janela de 8 dias fecha amanhã) ·
**A** ferramental (marketplace, gopls-lsp, session-report, 72 MCPs) ·
**B** instrumento (unit da cobertura, ai-citation), depois catálogo de fontes, allowlist, grafo
interno, lastmod, head · **F** retomar publicação — *a promoção é transacional; se um lote gerar
issue de manifest, antecipar C1* · **C** engenharia · **D** skills · **E** contratos + check.

## O que a revisão mudou (registro honesto)

Quatro afirmações minhas caíram na revisão, três delas em itens que eu ia executar:
o timer de IndexNow (teria feito o Bing ignorar o canal) · o mecanismo do IndexNow descrito pelo
script errado · "104 páginas prontas" que são tombstones sem corpo · o `hookify`, cujo benefício já
é entregue por um hook global que existe. Um achado perecível só apareceu no red-team: a janela de
retenção de 8 dias. Nenhum item deste plano depende de você executar nada, de cadastro ou de SaaS.

---

## RESULTADO DO BLOCO 0 (executado 2026-08-19 11:00 UTC)

O dado perecível foi recuperado dentro da janela. `tools/measure-crawl-coverage --dias 8` rodou
para os 10 crawlers; 80 registros gravados, `last_updated` de todos em 2026-08-19T11:00Z.
**Os números frescos mudam o quadro** — a tabela do Bloco B acima é a leitura congelada de 12/08 e
fica superada por esta:

| bot | função | 12/08 (congelado) | **19/08 (medido)** | delta |
|---|---|---|---|---|
| amazonbot | treino | 47,71% | **99,2%** | +7.702 URLs |
| yandexbot | busca | 15,21% | **95,5%** | +8.115 URLs |
| googlebot | busca | 73,1% | **73,1%** | +81 |
| gptbot | treino | 50,75% | **51,6%** | +129 |
| googleother | diag | 33,55% | **33,3%** | −1 |
| claudebot | treino | 21,77% | **23,4%** | +185 |
| **oai-searchbot** | busca/cita | 1,00% | **3,9%** | **+291** |
| **chatgpt-user** | usuário/cita | 0,33% | **1,0%** | **+68** |
| **bingbot** | busca/cita | 0,16% | **0,2%** (20 de 9.926) | — |
| **perplexitybot** | busca/cita | 0,00% | **0,0%** (0 de 9.926) | — |

**O que muda na leitura:**
1. **A tese central se confirma e fica mais nítida.** Bing (20 URLs) e Perplexity (0) continuam
   sendo o buraco real, agora com dado fresco e verificado pela Cloudflare — não é artefato de
   instrumento congelado.
2. **A OpenAI está acelerando**: `oai-searchbot` quase quadruplicou (1,0% → 3,9%, +291 URLs) e
   `chatgpt-user` triplicou. É o único canal de citação com tendência positiva.
3. **Achado novo que ninguém previu**: `amazonbot` 99,2% e `yandexbot` 95,5% — praticamente o
   acervo inteiro. O Yandex é buscador que cita; o Amazonbot é treino. Vale investigar por que o
   Yandex cobre 95,5% e o Bing 0,2%, sendo ambos buscadores com acesso liberado no robots.
4. Os 3.793 "sem IA" do plano vinham da leitura de 12/08 e precisam ser recontados.

Nenhum outro item do plano muda: a prioridade de descoberta segue sendo Bing/Perplexity, e a causa
continua não sendo o robots.txt.
