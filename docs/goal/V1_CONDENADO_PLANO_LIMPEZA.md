# Plano — v1 condenado: parar de confundir agentes sem quebrar o build

> Levantado em 2026-07-28 sobre `main` `42e29f88`. Escrito para o próximo Claude Code.
>
> **Resumo em uma linha:** apagar o v1 hoje quebraria checks ativos e 159 arquivos de
> produção; o que resolve o problema real (agente trabalhar na linhagem errada) é
> **sinalização + guarda automática**, e isso pode ser feito agora, sem risco.

---

## ⛔ CORREÇÃO CRÍTICA (2026-07-28, depois da investigação com 9 agentes)

**Este documento continha um erro perigoso, corrigido aqui.** A versão original tratava
`data/editorial/authorial_mass_drafts.jsonl` (41 MB, 7.178 linhas) como conteúdo v1
condenado. **Ele não é v1 — é o próprio v2, reprojetado no schema de draft.**

Medido: 7.178 de 7.178 `unique_intent_id` estão contidos nos `intent_id` do `v2_pages`, e
7.178 de 7.178 `title` e `opening` são **byte-idênticos** à página v2 correspondente.
Divergência genuína de prosa: **zero**.

**Se alguém "limpar" esse arquivo achando que é v1, estará apagando dado do v2.**

### Discriminador — rode antes de tocar em qualquer camada `authorial_mass_*`

| campo | v1 de verdade | v2 disfarçado de draft |
|---|---|---|
| id | contém `::` (`seed::cenário::contexto`) | plano, sem `::` |
| `scenario_id` / `context_id` | preenchidos | `""` |
| `page_type` | ausente | presente (`guia_problema`, `pergunta`, `verbete`, `procedimento`) |
| onde vive | **só no git** (`git show 34d6df3d:`) | no worktree |

```bash
head -1 data/editorial/authorial_mass_drafts.jsonl | python3 -c \
"import sys,json;d=json.loads(sys.stdin.read());print('V2' if d.get('page_type') and not d.get('scenario_id') else 'V1')"
```

### O v1 real não está no disco

Ele só existe no histórico do git e **nenhum byte dele está vivo no worktree**:

```
git show 34d6df3d:data/editorial/authorial_mass_content_expansion.jsonl | wc -l   → 9700
git show 34d6df3d:data/editorial/authorial_mass_drafts.jsonl            | wc -l   →  300
```

O que sobra no disco são **cascas sem corpo**: `authorial_mass_candidate_selection.jsonl`
(10.000 ids cartesianos, 0 registros com texto) e `authorial_mass_signature_applied_rewrites.jsonl`
(8.248 registros com `raw_text_stored: false`).

**Consequência para a §5 (plano faseado):** ela continua válida quanto ao acoplamento de
código (159 arquivos, 90 testes, checks ativos), mas a motivação "recuperar 100 MB" cai:
boa parte desses bytes é v2 ou casca vazia. Veja
[`V1_RECUPERACAO_VEREDITO.md`](V1_RECUPERACAO_VEREDITO.md) antes de agir.

---

## 1. O problema que o dono pediu para resolver

O estoque **v1 cartesiano** foi condenado pela DEC-004 (doorway/duplicado) e substituído em
2026-07-09 pelo **v2** (`data/editorial/v2_pages/`, 680 shards, 42 MB). Mas os arquivos v1
continuam no repositório, maiores que o v2, e **agentes tropeçam neles**: leem
`authorial_mass_drafts.jsonl`, acham que é o estoque, e trabalham na linhagem morta.

Custo real: token gasto em conteúdo condenado e — pior — risco de um agente *gerar* mais v1.

## 2. Por que NÃO apagar agora (medido, não opinião)

```bash
# comandos que produziram os números abaixo, reproduzíveis
grep -rl 'authorial_mass' --include='*.go' internal/ | wc -l     # 159
grep -rl 'authorial_mass' --include='*_test.go' . | wc -l        #  90
grep -n  'authorial_mass' internal/checks/checks.go | head       # checks ATIVOS
git ls-files | grep -cE 'authorial_mass|content_expansion'       #  63 arquivos rastreados
```

| camada | acoplamento ao v1 |
|---|---|
| `internal/` (produção) | **159 arquivos** |
| testes | **90 arquivos** |
| `internal/checks/checks.go` | checks **ativos** leem `authorial_mass_legal_signatures`, `authorial_mass_signature_candidate_pairs`, `authorial_mass_signature_refinement_queue` (linhas 4778, 4787, 10093, 10101, 10111) |

Remover os JSONL faria esses checks falharem por arquivo ausente — ou seja, **o gate de
qualidade quebra**, que é exatamente o que não pode acontecer. Isso não é limpeza: é uma
refatoração de grande porte, e refatoração grande sem necessidade é risco sem retorno.

### Onde estão os 100 MB

| arquivo | tamanho | linhas |
|---|---|---|
| `authorial_mass_drafts.jsonl` | 41,2 MB | 7.178 |
| `authorial_mass_candidate_selection.jsonl` | 26,1 MB | 10.000 |
| `authorial_mass_signature_applied_rewrites.jsonl` | 15,8 MB | — |
| `authorial_mass_legal_editorial_reviews.jsonl` | 3,1 MB | — |
| `authorial_mass_content_expansion.jsonl` | **0** | **0** — já esvaziado |

O `content_expansion` (a expansão de 9.700 páginas condenada) **já foi zerado**. O que
resta é a camada de rascunho/seleção/assinatura, ainda lida por checks.

---

## 3. O que fazer AGORA — resolve a confusão, risco zero

Três ações independentes, todas reversíveis, nenhuma toca em código de produção.

### 3.1 Marcador de linhagem morta no diretório

Criar `data/editorial/LEIA-ANTES-v1-CONDENADO.md` com, no máximo, uma tela:

```markdown
# ATENÇÃO — arquivos `authorial_mass_*` são a linhagem V1 CONDENADA

O estoque canônico é o **v2**: `data/editorial/v2_pages/*.jsonl` (680 shards).

Os arquivos `authorial_mass_*` e `content_expansion*` deste diretório são o v1 cartesiano,
condenado pela DEC-004 em 2026-07-09 (doorway/duplicado). Eles permanecem no repositório
apenas porque checks ativos ainda os leem (ver docs/goal/V1_CONDENADO_PLANO_LIMPEZA.md).

- **NÃO gere** conteúdo novo nessas camadas.
- **NÃO use** como fonte de estoque, contagem ou amostra.
- **NÃO conte** essas páginas na meta P0 — a meta é sobre v2.

Ver docs/goal/V1_V2_CONTENT_LINEAGE.md.
```

Ganho: qualquer agente que liste o diretório vê o aviso antes de abrir um JSONL de 41 MB.

### 3.2 Guarda automática contra gerar v1 novo

Criar `tools/check-v1-nao-cresce` (read-only, barato) que:

1. lê as contagens de linha atuais das camadas v1 e as compara com um baseline gravado em
   `data/ops/v1_condenado_baseline.jsonl`;
2. **falha** se qualquer camada v1 cresceu;
3. passa se ficou igual ou diminuiu.

Isso transforma "não mexa no v1" de recomendação em **fato verificável**. Registrar o check
em `internal/checks/checks.go` (case + `Names` + `_test.go`) só depois que ele estiver
estável como script.

### 3.3 Deixar os arquivos gigantes fora do diff

Os três monstros (`drafts`, `candidate_selection`, `signature_applied_rewrites` = 83 MB)
devem estar no `.gitattributes` com `-diff`, para que um `git diff` acidental não despeje
dezenas de MB no contexto de um agente. **Confira se já estão** — o `.gitattributes` foi
criado em 2026-07-28 e pode já cobri-los:

```bash
grep -n 'authorial_mass' /opt/wiki/.gitattributes
```

Se faltar, acrescente **apenas** `-diff` (nunca `binary`, `-text` ou `eol=`, que alteram o
conteúdo no checkout).

---

## 4. Backup — o que fazer antes de qualquer remoção futura

O git já é o backup: todo o conteúdo v1 está no histórico e é recuperável com
`git show <commit>:<caminho>`. Um arquivo removido em commit futuro **não se perde**.

Ainda assim, para remoção em lote vale um arquivo físico fora do repositório:

```bash
# arquivo compactado das camadas v1 (≈100 MB → ≈10-30 MB)
DEST=~/.config/ai-terminal-backups/v1-condenado-$(date +%Y%m%d)
mkdir -p "$DEST"
cd /opt/wiki
git ls-files | grep -E 'authorial_mass|content_expansion' \
  | tar -I 'zstd -T2 -12' -cf "$DEST/v1-camadas.tar.zst" -T -
# conferir antes de qualquer remoção
tar -I zstd -tf "$DEST/v1-camadas.tar.zst" | wc -l
```

Regra: **o arquivo de backup é conferido antes**, nunca depois.

---

## 5. Plano faseado de desacoplamento (só quando houver motivo)

Não execute isto sem necessidade concreta (espaço em disco não é motivo: são 100 MB num
disco com 297 GB livres). Se um dia o v1 atrapalhar de verdade, a ordem segura é:

| fase | o quê | como validar |
|---|---|---|
| 1 | Mapear os **checks** que leem v1 e decidir, um a um: o check ainda faz sentido? Se a camada é morta, o check dela também é. | `grep -n 'authorial_mass' internal/checks/checks.go` |
| 2 | Remover **primeiro os checks** obsoletos (case + `Names` + teste), não os dados. Código sai antes do dado — o inverso quebra o gate. | `./tools/go-modern test -count=1 ./internal/checks/` |
| 3 | Remover os **geradores** `cmd/generate/gen_b_authorial_mass_*.go` que não são mais chamados. | `./tools/go-modern build ./cmd/...` (envelopado em `run-heavy-throttled`) |
| 4 | Só então remover os **JSONL**, com backup da §4 conferido. | `./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./...` |
| 5 | Por último, os 90 testes que referenciam v1 — muitos morrem junto com o código da fase 2. | idem |

Cada fase é um commit próprio, com escopo por pathspec. Nunca as cinco de uma vez.

---

## 6. Branches órfãos do v1 — o que fazer

Dez branches locais mexem exclusivamente em camadas v1 (lista em
`WORKTREE_BRANCH_INTEGRATION_HANDOFF.md` §2.1). Eles **não devem ser integrados**, mas
também não precisam ser apagados: um branch custa alguns bytes e o commit é a evidência de
que aquilo existiu.

O que reduz confusão sem destruir nada é **renomear com prefixo**, o que os agrupa no fim de
qualquer listagem e deixa o veredito explícito no próprio nome:

```bash
# reversível: renomear preserva o commit; nada é descartado
cd /opt/wiki
git branch -m codex1-p0-algorithmic-approval zz-v1-condenado/codex1-p0-algorithmic-approval
# ... idem para os outros nove
```

> `git branch -m` **não** é comando destrutivo (não é `-D`/`-d`): move a ref, preserva o
> commit e é desfeito renomeando de volta. Ainda assim, faça um branch por vez e confira
> com `git log --oneline -1 <novo-nome>`.

---

## 7. Recomendação

Faça **§3.1, §3.2 e §3.3 agora** — resolvem o problema que o dono descreveu (agente
confundido) em minutos, sem tocar em código de produção.

Deixe **§5 parado** até existir motivo concreto. Hoje o v1 custa 100 MB de disco e alguma
confusão; a confusão é resolvida por sinalização, e 100 MB não justificam mexer em 159
arquivos de produção e 90 testes.

Se o dono autorizar a limpeza profunda, siga §5 **na ordem**, uma fase por commit, com o
backup da §4 conferido antes da fase 4.
