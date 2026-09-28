# Prompt de goal para a próxima sessão

> Escrito em 2026-07-28. Cole o bloco da §2 como primeira mensagem da sessão nova.
> A §1 explica as escolhas do prompt — leia se for editá-lo.
>
> **2026-07-28 (tarde): SUPERADO por `PROMPT_GOAL_4K.txt`**, versão verificada contra o código
> por revisão adversarial (3 agentes): corrige a atribuição de doc (15x-108x, 241MB, deadlock
> futex e load 106-125 estão em FABRICA_ESCALA_ARQUITETURA.md, não no perf doc), o caminho do
> CHECKPOINT.md (fica na RAIZ do repo), o diagnóstico do MURO C (MaxPairs conta pares
> CONFIRMADOS; caminho vivo não é all-pairs), remove `ai-brief` (não existe no repo) e o item
> "roaring/semanticcluster/legalsignature ociosos" (estão LIGADOS aos gates — checks.go:377,
> :1398, :1529). Detalhe em MAESTRO_CODEX_LOG.md, entrada 2026-07-28.

---

## 1. Por que o prompt é assim

Três armadilhas específicas deste repositório fizeram sessões anteriores perderem dias.
O prompt da §2 desarma cada uma explicitamente:

1. **"Recuperar trabalho perdido" que não estava perdido.** 11 worktrees e 24 branches
   pareciam conter ~1000 commits de trabalho órfão. Revisão com 25 agentes: **zero** a
   integrar — tudo já estava no `main`, por outra rota. Sem o aviso, a próxima sessão
   refaz essa investigação.
2. **Confundir v2 com v1.** `authorial_mass_drafts.jsonl` tem nome de v1 e **é v2**
   (7.178/7.178 títulos byte-idênticos). "Limpar" apagaria produto.
3. **Otimizar a coisa errada.** O instinto diz "o JSONL não escala"; a medição diz que
   varrer tudo custa 0,26 s. O gargalo real é outro e está medido.

---

## 2. O prompt — copie daqui para baixo

```
/goal

OBJETIVO ÚNICO: entregar 10.000 páginas jurídicas APROVADAS e remover as três paredes que
hoje fazem a fábrica FALHAR (não apenas ficar lenta) muito antes de 1 milhão. Hoje há 7.675
páginas ativas e ZERO aprovadas — o número que importa é aprovadas, não escritas.

O ENQUADRAMENTO CORRETO, medido em 2026-07-28: a fábrica não fica lenta em escala — ela
QUEBRA em ~200-300 mil páginas, por três limites duros. Acelerar comando sem mover esses
limites entrega uma fábrica que produz mais rápido e bate no mesmo muro na mesma página.

LEIA PRIMEIRO (nesta ordem, são curtos e evitam refazer trabalho já feito):
1. docs/goal/FABRICA_ESCALA_ARQUITETURA.md — AS TRÊS PAREDES e o plano por fases. É o mais
   importante. Tem convenção de confiança por achado: [V] verificado, [C] confirmado por
   refutação, [D] direção certa e magnitude contestada, [R] refutado, [NM] não medido.
   Respeite as marcas: use intervalos, nunca o extremo.
2. docs/goal/FABRICA_PERFORMANCE_DIAGNOSTICO.md — o overhead de invocação, medido
3. docs/goal/V1_RECUPERACAO_VEREDITO.md — por que não há nada a recuperar do v1
4. docs/goal/WORKTREE_BRANCH_INTEGRATION_HANDOFF.md — worktrees/branches: nada a integrar, e os 2 bugs achados
5. docs/goal/V1_CONDENADO_PLANO_LIMPEZA.md — o que é v1 de verdade e o discriminador
Depois: AGENTS.md (contrato) e docs/goal/CHECKPOINT_DIGEST.md (NÃO leia CHECKPOINT.md
inteiro — são 2,4 MB / ~616k tokens; as entradas novas ficam no TOPO, nunca use tail).

AS TRÊS PAREDES (o que faz a fábrica falhar, não só demorar):
- MURO A — internal/v2readguard/guard.go:38: `maxDirectoryEntries = 20_000`, constante de
  compilação usada em :83, :98-99 e :1080. A 11,38 páginas por shard, 20.000 shards =
  ~227.600 páginas. Passou disso, o guard REJEITA a leitura do diretório: o pipeline não
  desacelera, ele para com erro.
- MURO B — internal/v2bodyneardup/neardup.go:184 (`candidatePairsExactPrefix`): monta três
  estruturas dimensionadas pelos shingles distintos do CORPUS INTEIRO (frequencies, ordered,
  rank). Medido por três frentes independentes: 66,0 KB de RAM por página (RSS 427-507 MB
  para 7.675 páginas). Em 19 GB isso é ~290.000 páginas → OOM.
- MURO C — JÁ ESTÁ BATIDO HOJE: internal/v2bodysemanticdedup estoura
  `confirmed pair budget exceeded: pairs>250000` numa amostra aleatória de 772 páginas
  (10% do corpus). Não é custo quadrático, é SAÍDA quadrática: o gate não fica lento, ele
  não termina. Acontece agora, não é projeção.
As três convergem na faixa de 200-300k. É lá que a fábrica quebra.

FATOS MEDIDOS EM 2026-07-28 — não reinvestigue, parta daqui:
- Estoque: 680 shards, 7.739 linhas, 7.675 páginas ativas, 64 skipped, ZERO aprovadas.
- Backlog: portfolio_v2 tem 10.041 intents distintos e 0 com corpo → 2.366 por escrever.
  Teto do pipeline atual = 10.041 páginas, margem de 0,4% sobre a meta. Qualquer atrito de
  gate derruba abaixo de 10.000.
- Lentidão: `go run ./cmd/check X` custa 18 s com a máquina calma; o MESMO check com
  binário pré-compilado custa 4,77 s. São 13 s de link de um binário de 230 MB, refeitos a
  cada invocação (em 303 checks, ~66 min só de link).
- SOB CARGA o número explode: com ~10 agentes trabalhando junto, a mesma invocação levou
  1.422 s (23,7 min) na primeira vez e 445 s (7,4 min) na segunda, JÁ COM CACHE QUENTE.
  O GOCACHE tem 5,3 GB e não resolve, porque o que custa é o LINK, que não é cacheado.
  Efeito perverso: hoje quanto mais agentes em paralelo, mais lento fica cada um. Um
  binário pré-compilado e COMPARTILHADO inverte isso — o custo é pago uma vez, por todos.
- NÃO é o dado: varrer os 680 shards custa 0,03 s; parsear as 7.739 páginas, 0,26 s.
- data/ops/check_performance_ledger.jsonl tem 303 orçamentos e ZERO durações reais: a
  fábrica não é instrumentada.
- 3 dos 4 checks mais caros (~18 min de orçamento) validam a linhagem v1 morta.
- Bug aberto: data/research/demand_expansion_opportunities.jsonl (18.228 linhas) não tem
  semantic_compatibility_family em nenhuma linha; o campo virou obrigatório em 87f07e13
  (21/07) e o dado é de 02/07. Reprova o gate codex2-source-frontier.

ORDEM DE TRABALHO (faça nesta sequência; cada passo destrava o seguinte):

PASSO 0 — regra de medição, vale para tudo que você medir
As medições originais foram colhidas com load average entre 106 e 125 numa caixa de 8 cores.
Wall-time sob essa carga é ficção. Toda medição de performance neste repo deve reportar o
/proc/loadavg do instante, fazer no mínimo 3 repetições, e usar CPU-time (user+sys) como
número primário. Sem isso você vai "otimizar" ruído.

PASSO 1 — o gate que JÁ falha hoje (MURO C), antes de qualquer otimização
internal/v2bodysemanticdedup estoura o budget de pares com 772 páginas. Enquanto isso não
for resolvido, não existe caminho para 10k aprovadas — o gate não termina. A saída é
arquitetural: substituir a enumeração de pares por indexação (LSH por bandas sobre MinHash,
ou buckets de Hamming sobre SimHash), de modo que só pares CANDIDATOS sejam materializados.
O repositório JÁ TEM internal/roaringpostings, internal/semanticclusterindex e
internal/legalsignature. Descubra se estão ligados ao gate ou se estão prontos e ociosos —
se for o segundo caso, é o maior ganho com o menor esforço da fábrica inteira.
NÃO resolva isso subindo o budget: elevar o teto de pares é esconder o problema, e o
contrato proíbe corrigir lentidão afrouxando limite.

PASSO 2 — matar a cerimônia de invocação (overhead medido de 15x a 108x)
Cada chamada de `go run ./cmd/check` paga entre 2,6 e 8,5 s de cerimônia para 0,08-0,25 s de
trabalho útil. Componente isolado e reprodutível: o `sha256sum` de um binário de 241 MB
custa 2,4-3,0 s POR INVOCAÇÃO; some go env, um python3 de build-identity, 7 comandos git de
repo_awareness, stat e um re-exec sob timeout. Volume medido: ~70 chamadas/dia.
Crie um caminho rápido: binário compilado uma vez em cache e COMPARTILHADO, revalidado por
mtime das fontes (nunca por hash do binário inteiro). Código novo jamais pode rodar com
binário velho — a revalidação tem que comparar o mtime do binário com o .go mais recente de
que ele depende.

PASSO 3 — investigar o bloqueio do `check all`
Numa rodada, `check all` NÃO terminou em 411 s tendo consumido só 35,4 s de CPU (8,6% de um
core), com 12/12 threads em S e /proc/PID/wchan = futex_wait_queue. Isso é BLOQUEIO, não
contenção — e o contador é interno ao processo, imune a load externo. Há um deadlock ou uma
espera mal dimensionada no runner. Ache antes de otimizar throughput: um runner que trava
não fica mais rápido com paralelismo.
Contexto: 304 checks (internal/checks/checks.go:277), 112 de 157 medidos rodam em <1 s — os
gates individualmente NÃO são o gargalo. O paralelismo efetivo medido foi 2,01x numa caixa
de 8 cores, com MAXRSS de 7,85 GB.

PASSO 4 — mover as paredes A e B
MURO A: maxDirectoryEntries=20_000 é constante de compilação. A correção não é aumentar o
número: é particionar (subdiretórios por vertical/faixa) para que nenhum diretório precise
de mais de 20k entradas. Aumentar a constante só empurra o muro.
MURO B: o near-dup dimensiona estruturas pelo corpus inteiro. Precisa passar a trabalhar por
janela/bloco, com estado limitado — o custo por página não pode depender de N.
Valide com um corpus sintético de 50k e depois 200k registros antes de declarar resolvido.

PASSO 5 — medir o atrito real de aprovação
Levar UM lote pequeno (50-100 páginas) até aprovação completa, com todos os gates. O objetivo
não é volume: é descobrir a taxa de aprovação real, hoje desconhecida (zero aprovadas). Sem
esse número não dá para dimensionar o backlog.

PASSO 6 — dimensionar o backlog com o número do passo 5
Se a taxa de aprovação for X%, para 10.000 aprovadas são 10.000/X escritas. Com o teto atual
de 10.041 e margem de 0,4%, quase certamente será preciso especificar +1.000 a +1.500
intents novos — derivados de demanda real (problema/documento/risco/etapa/cenário), NUNCA
permutação de palavra-chave, que é exatamente o que condenou o v1 (DEC-004).

CADÊNCIA MEDIDA, para calibrar expectativa: 162 páginas por hora ativa de produção (379
commits entre 07/07 e 22/07, somando só intervalos < 60 min = 47,64 h ativas). Nesse ritmo,
as 2.261 páginas que faltam para 10.000 são ~14 h de produção; 1M seriam 6.125 h (255 dias
ininterruptos). Ou seja: 10k é alcançável esta semana; 1M exige mudar a arquitetura, não
apertar o passo.

RESTRIÇÕES DURAS — violá-las é pior do que não entregar:
- PROIBIDO afrouxar, pular ou amostrar gate para ganhar velocidade. Performance se resolve
  por algoritmo, índice, cache honesto e paralelismo. Cache que devolve veredito velho é
  fraude: a chave do cache tem que incluir TODO input que afeta o veredito (conteúdo +
  versão da regra).
- PROIBIDO merge, cherry-pick, rebase, reset, checkout, restore, stash. Correção é sempre
  para frente, por edição pontual. (Há hook que bloqueia.)
- PROIBIDO tratar authorial_mass_* como estoque. É v1 condenado — exceto
  authorial_mass_drafts.jsonl, que é v2 disfarçado. O discriminador está no
  V1_CONDENADO_PLANO_LIMPEZA.md; rode-o antes de tocar em qualquer camada com esse nome.
- PROIBIDO `go build ./...` sem envelope: use ./tools/run-heavy-throttled. Teste focado no
  pacote tocado, nunca suíte global por hábito.
- Conteúdo público em português do Brasil com acentuação correta; fonte oficial específica
  registrada com URL, data e hash; nada de inventar lei, artigo, prazo ou decisão.

O QUE NÃO FAZER (já investigado, com evidência nos documentos):
- Não tente integrar worktrees ou branches órfãos: 25 agentes verificaram, 0 a integrar.
- Não tente recuperar texto do v1: 0 de 9.700 páginas passam nos gates determinísticos, e
  os 9.700 ids são só 27 temas, todos já cobertos no v2.
- Não otimize o formato dos dados: medido, não é gargalo.
- Não regenere demand_expansion_opportunities.jsonl sem antes confirmar que o gerador
  preenche o trio semântico e que os consumidores aceitam o formato novo.

DEFINIÇÃO DE PRONTO desta sessão:
(a) um comando de check custa segundos, não dezenas de segundos, com o mesmo exit code;
(b) o ledger tem duração REAL por check e os 15 mais caros estão publicados;
(c) está respondido, com evidência, se o gate de similaridade é O(n²) ou usa índice;
(d) existe um número medido de taxa de aprovação, obtido de um lote real levado até o fim.

Trabalhe de forma autônoma e contínua, em escala: lance agentes e workflows para as frentes
independentes em vez de fazer tudo em série, e não pare para pedir confirmação do que os
contratos já autorizam. Commit por frente, com escopo por pathspec, lendo os arquivos antes.
```

---

## 3. Comandos úteis para a sessão nova

```bash
ai-brief                       # estado do terminal: sessões, agentes, recursos, tokens, repo
./tools/wiki-brief             # estado da fábrica (criado em 2026-07-28)
ai-tokens --today              # consumo por modelo
ai-top                         # saturação ao vivo, antes de lançar onda pesada

# medir o overhead de link você mesmo (reproduz o achado principal)
time ./tools/go-modern build -o /tmp/check ./cmd/check
time /tmp/check seo-title-meta
time ./tools/go-modern run ./cmd/check seo-title-meta
```
