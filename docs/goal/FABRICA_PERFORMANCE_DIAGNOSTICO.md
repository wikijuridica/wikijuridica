# Diagnóstico de performance da fábrica — medido em 2026-07-28

> Medições feitas diretamente em `/opt/wiki`, `main` `14267ca6`, máquina de 8 cores.
> Cada número tem o comando que o produziu. Onde não medi, está escrito "não medido".


> **CORREÇÃO (2026-07-28, após a medição com 21 agentes):** dois números deste documento
> estavam errados, herdados de documentação desatualizada do repositório. São **424 pacotes**
> (não 504) e **25 main packages** (não 303 binários) — 278 diretórios de `cmd/` estão atrás
> da build tag `devcmds` e não entram no build padrão. O diagnóstico do overhead de link
> permanece válido; a magnitude do custo de link é menor do que "303 binários" sugeria.
> O achado que MUDA a prioridade está em `FABRICA_ESCALA_ARQUITETURA.md`: a fábrica não fica
> lenta em escala, ela **falha** em ~200-300 mil páginas, por três limites duros.

---

## 1. A pergunta do dono

> *"Os comandos demoram, mesmo com cache. O mínimo que eu peço são 10k páginas, e tá muito
> lento. No futuro quero milhões. Ou tem código burro, ou engenharia fraca, ou computação
> desnecessária."*

**É computação desnecessária, e está medida.** O diagnóstico abaixo mostra onde.

---

## 2. O achado principal — o link não é cacheado, e sob carga ele explode

### 2.0 O número que explica a queixa do dono

O mesmo comando, medido em dois regimes de carga:

| `./tools/go-modern run ./cmd/check` | tempo |
|---|---|
| 1ª execução, com ~10 agentes compilando junto (load 67) | **1.422 s = 23,7 min** |
| 2ª execução, **cache quente**, mesma carga | **445 s = 7,4 min** |
| mesma invocação com a máquina calma | **18 s** |

**Com o cache quente ainda leva 7,4 minutos.** É por isso que "mesmo com cache" está lento:
o GOCACHE (5,3 GB) guarda a *compilação dos pacotes*, mas **o link do binário final não é
cacheado** — e é ele que custa. Pior: sob paralelismo, cada agente relinca os mesmos 230 MB
ao mesmo tempo, e os processos disputam CPU (`compile`, `link` de 900 MB de RSS ocuparam o
topo do `ps` durante a medição).

**Consequência para escala de agentes:** hoje, quanto mais agentes trabalham em paralelo,
mais lento fica *cada um* — o oposto do que se espera de paralelismo. Um binário
pré-compilado e compartilhado inverte isso: o custo é pago uma vez, por todos.

### 2.1 O overhead isolado, com a máquina calma

| forma de invocar o mesmo check | tempo |
|---|---|
| binário já compilado: `check seo-title-meta` | **4,77 s** |
| `./tools/go-modern run ./cmd/check seo-title-meta` | **18 s** |

**O Go cacheia a compilação dos pacotes, mas `go run` refaz o LINK a cada chamada.** O
binário resultante tem **230 MB**, e linká-lo custa ~13 s. Esse tempo é pago **antes de
qualquer trabalho útil**, em toda invocação de qualquer check.

```bash
# reproduzir
time ./tools/go-modern build -o /tmp/check ./cmd/check   # 47 s (uma vez)
time /tmp/check seo-title-meta                            # 4,77 s
time ./tools/go-modern run ./cmd/check seo-title-meta     # 18 s
```

### Por que o binário tem 230 MB

```bash
./tools/go-modern list -deps ./cmd/check | wc -l                    # 1.350 dependências
./tools/go-modern list -deps ./cmd/check | grep -c '^portaljuridico' #   293 do projeto
wc -l internal/checks/checks.go                                      # 11.526 linhas
ls -d cmd/*/ | wc -l   # 303 dirs em cmd/ (só 25 main ativos; 278 atrás de //go:build devcmds — ver ⛔ topo)
```

`cmd/check` arrasta **293 pacotes do próprio projeto**. Não é debug symbol: compilar com
`-ldflags="-s -w"` só reduz de 230 MB para 202 MB (−12%) — o peso é código real.

**Consequência em escala (corrigida 2026-07-28):** a conta original "303 × 13 s ≈ 66 min só de
link" superestimava — são **25 main ativos** (ver ⛔ topo). O custo real é o link/cerimônia pago
A CADA invocação `go run`; o fix é o mesmo: binário pré-compilado + cache de veredito com chave completa.

---

## 3. O que NÃO é o gargalo (hipóteses refutadas por medição)

Importante registrar, para ninguém otimizar a coisa errada:

| hipótese | medição | veredito |
|---|---|---|
| "o formato JSONL não escala" | varrer os 680 shards: **0,03 s**; parse JSON de todas as 7.739 páginas: **0,26 s** | **REFUTADA.** Extrapolando linear para 1M: ~34 s. O dado não é o problema |
| "falta cache do Go" | o GOCACHE funciona — o que não é cacheado é o **link**, que `go run` refaz sempre | **REFUTADA** (o cache existe; o link é que não se aproveita) |
| "os arquivos são grandes demais" | 42 MB para 7.739 páginas = ~5,4 KB por página | **REFUTADA** |

---

## 4. Custo dos checks — orçado, não medido

`data/ops/check_performance_ledger.jsonl` tem **303 registros**, mas os campos são
`expected_duration_ms` e `budget_ms` — **orçamento, não medição**. Nenhum registro tem
duração real.

```
soma dos orçamentos: 14.420 s = 240 minutos
distribuição: 146 fast | 106 medium | 51 heavy
always_run: 247 de 303
```

**Isto é um achado em si: a fábrica não é instrumentada.** Não se otimiza o que não se mede;
hoje não há como saber qual check consumiu o tempo de um ciclo real.

Os 10 mais caros por orçamento (todos `heavy`, 300–420 s cada): `languagetool-quality-release`,
`authorial-mass-legal-reviews`, `authorial-mass-release-evidence`,
`authorial-mass-release-transaction`, `python-quality-sca`, `sca-actionlint`,
`sca-gitleaks-secrets`, `sca-gosec`, `sca-govulncheck`, `sca-licenses`.

> Note que 3 dos 4 mais caros são da linhagem **v1 condenada** (`authorial-mass-*`) —
> 18 minutos de orçamento gastos em camada morta. Ver `V1_RECUPERACAO_VEREDITO.md`.

---

## 5. Correções de rota (ordem por ganho/esforço)

### 5.1 Binário pré-compilado em vez de `go run` — ganho medido 3,8×

**Esforço: baixo. Ganho: 18 s → 4,8 s por invocação.**

Criar `tools/wiki-check` que garante um binário compilado em cache e o executa:

- compila para um caminho estável (ex.: `.cache/bin/check`) apenas se o binário for mais
  antigo que qualquer `.go` de que ele depende;
- caso contrário, executa direto.

Invalidação correta (**não pode devolver binário velho**): comparar o mtime do binário com o
mtime mais recente de `internal/**/*.go` e `cmd/check/**`. Se qualquer fonte for mais nova,
recompila. Isso mantém honestidade: código novo nunca roda com binário antigo.

### 5.2 Instrumentar de verdade — pré-requisito para tudo

**Esforço: baixo. Ganho: torna o resto mensurável.**

Passar a gravar `actual_duration_ms` por check no ledger, ao lado do orçamento. Sem isso,
qualquer priorização futura é chute. Hoje há 303 orçamentos e zero medições.

### 5.3 Não gastar 18 min de orçamento em linhagem morta

Três dos checks `heavy` mais caros validam camadas `authorial_mass_*`. Antes de otimizar
qualquer coisa, decidir se ainda devem rodar — ver `V1_CONDENADO_PLANO_LIMPEZA.md` §5, que
manda **remover o check antes do dado** (código sai antes, senão o gate quebra).

### 5.4 Reduzir o acoplamento de `cmd/check` — arquitetural

**Esforço: alto. Ganho: ataca a raiz dos 230 MB.**

Um binário que arrasta 293 pacotes é o motivo de o link custar 13 s. Caminhos possíveis (não
medidos, precisam de prova antes de adotar): separar checks por grupo em binários menores;
ou carregar o hub por registro em vez de importar tudo. **Não faça isso antes de 5.1 e 5.2** —
o ganho de 5.1 é imediato e barato, e 5.2 é o que permite provar se 5.4 vale.

---

## 6. O que ainda falta medir

- **Tempo real de um ciclo completo** de gates (hoje só há orçamento).
- **Complexidade dos gates relacionais**: se o check de similaridade compara par a par
  (O(n²)), ele é o teto de escala — com 7.739 páginas são ~30 milhões de pares; com 1M
  seriam 5×10¹¹. O repositório já tem `internal/roaringpostings`,
  `internal/semanticclusterindex` e `internal/legalsignature` (MinHash/SimHash); **falta
  confirmar se o gate os usa ou se ainda faz varredura completa**. Se a estrutura existe e
  não está ligada, esse é o maior ganho de menor esforço da fábrica.
- **Throughput real de produção**: páginas/hora do pipeline de escrita.

---

## 7. Números de referência do estoque (medidos hoje)

```
data/editorial/v2_pages/: 680 shards, 7.739 linhas, 42 MB
                          7.675 páginas ativas | 64 skipped
portfolio_v2:             10.041 intents distintos, 0 com corpo
backlog por escrever:     10.041 − 7.675 = 2.366
teto do pipeline atual:   10.041  (margem de 0,4% sobre a meta de 10.000)
páginas aprovadas hoje:   0
```

**O teto do pipeline atual é 10.041 páginas — 41 acima do piso.** Qualquer atrito de gate
derruba abaixo da meta. E como há **zero páginas aprovadas**, o atrito real ainda é
desconhecido. Detalhe em `V1_RECUPERACAO_VEREDITO.md`.
