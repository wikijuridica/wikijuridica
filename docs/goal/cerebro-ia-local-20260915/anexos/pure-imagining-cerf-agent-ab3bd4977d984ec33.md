# REFUTAÇÃO ADVERSARIAL — RUNBOOK P6 + P8 + P7

Repositório: /opt/wiki · 2026-09-15 · sessão em PLAN MODE (só leitura)
Veredito: **QUEBRA_PRODUCAO**

O runbook tem diagnóstico honesto e retratações corretas (F8 é exemplar). O que ele
faz de errado é **reimplementar à mão a sequência de `tools/deploy-publico` e
descartar três passos**, dois dos quais têm incidente medido nos últimos 5 dias.
Abaixo, na ordem de dano.

---

## A. QUEBRA PRODUÇÃO / DANO MEDIDO

### A1 — Passos 9 e 12 omitem o passo 2.7 do deploy: 2.488 âncoras para 404

`tools/deploy-publico:713-715`:
```
step "2.7/7 espelhando os temas da rede social"
if temas_saida=$(./tools/go-modern run ./cmd/generate-social-temas --aplicar 2>&1); then
```
e o comentário de `:687-699`, literal:

> Toda pagina publicada sai com a ancora do seu tema (`/redesocial/tema/{area}/{slug}/`,
> cobrada por check-ancora-redesocial), e o link e derivado da ROTA. O tema so passa a
> existir quando este comando espelha o published_manifest no banco social. Publicar sem
> semear anuncia ao crawler uma URL que devolve 404.
> MEDIDO EM 2026-09-10: o banco tinha 10.141 temas para 11.039 paginas publicadas. As 898
> paginas sem tema geraram **1.161 requisicoes 404 de bots valiosos em 10 dias (GPTBot 817,
> PerplexityBot 339, em 817 caminhos distintos de /redesocial/tema/jurisprudencia/)**.

O runbook publica 2.488 páginas **de /jurisprudencia/** — a mesma área do incidente — e
nunca chama `generate-social-temas --aplicar` nem `check-social-temas-espelhados`. Escala:
2.488 contra 898, **2,77×**, no mesmo caminho, com os mesmos dois bots.

**E não há outro executor.** Medido: `grep -rn 'social-temas|PlanejaEspelho'` em
`cmd/publish-v2-direct/`, `ops/systemd/` e `tools/run-daily-content` devolve **zero**;
`systemctl list-timers '*social*' '*tema*' --all` lista **um** timer, e é
`wikijuridica-sitemap-shard-grace.timer`, que roda
`tools/generate-sitemap-shard-grace-series` (inventário de disco × índice). O único chamador
de `generate-social-temas --aplicar` em todo o repositório é `tools/deploy-publico:715`.
Publicar por fora do `deploy-publico`, como este runbook faz, **garante** o defeito.

Agravante menor: o passo 7 do runbook nunca mede 404 em `/redesocial/tema/`, e sua linha
"'zero 404 no lote' não limita a publicação" (que é sobre latência de descoberta) faz o
operador passar por cima do único sinal que denunciaria isso.

**Emenda**: etapa obrigatória entre publicar e reiniciar, com PARA:
`./tools/go-modern run ./cmd/generate-social-temas --aplicar` e em seguida
`./tools/check-social-temas-espelhados` (exit 0). No oneshot, entre a etapa 13 e a 17.
E o passo 7 passa a exigir **zero 404 em `/redesocial/tema/jurisprudencia/`** nos
`data/ops/access/nginx-*.jsonl` da coorte.

### A2 — Passos 9 e 12 omitem o passo 2.6: 2.488 páginas sem Percursos nos 4 canais

`tools/deploy-publico:652-684`, comentário literal: *"o indice deriva de
content/pages.json, que o passo 1 acabou de reescrever, e e lido UMA vez no BOOT do
servidor. Entao ele tem de nascer DEPOIS da republicacao e ANTES de o servico voltar a
atender."* Comando: `./tools/go-modern run ./cmd/generate-legal-cocitation`. Custo medido
ali: ~16 s ociosa, ~29 s sob carga, linear no acervo.

O runbook faz `publicar → sweep → reload-wiki-server`. A janela única é justamente entre
esses dois, e ele não a usa. Consequência (CLAUDE.md §7, e o próprio comentário do
deploy): artefato VELHO ⇒ `filtraPercursosServiveis` descarta o que o processo não serve,
logo **não há link morto** — mas as 2.488 páginas novas saem sem a seção `## Percursos por
fundamento legal` na gêmea, no MCP, no A2A e no `/api/v1/lote`. É a seção de maior
densidade do canal de máquina (76,7% de links cross-área contra 11,4% da malha base,
`deploy-publico:662-664`), no bloco cujo produto declarado é exatamente o canal de máquina
(§12). Nenhum passo do runbook mede isso, e existe gate para medir:
`tools/check-percursos-fundamento-legal`.

**Emenda**: etapa `cmd/generate-legal-cocitation` **depois** de `publish-v2-direct` e
**antes** de `reload-wiki-server` (não aborta: degradação honesta), seguida de
`./tools/check-percursos-fundamento-legal`. Sem ela, `reload` congela o índice velho por
todo o intervalo até o próximo restart.

### A3 — Passos 9 e 12 omitem o passo 4/7: o cache de origem serve texto velho

`tools/deploy-publico:748-768`, comentário literal: *"var/nginx/cache guarda a ultima
resposta boa de cada rota dinamica (proxy_cache wj_dyn em @markdown/@fallback) (…)
Depois de republicar, o objeto guardado e a versao ANTERIOR do texto — precisa sair junto
com o cache do Go, senao a gemea Markdown serviria texto velho ate o TTL."* O passo também
faz `rm -rf "$CACHE_DIR"` do cache de respostas do Go.

TTL **medido agora** por mim, pelo nginx em 127.0.0.1:8088 com a sonda interna:

| rota | Cache-Control medido |
|---|---|
| `/jurisprudencia/stf-aco-1560/index.md` | `public, max-age=600, s-maxage=604800` |
| `/jurisprudencia/index.md` | `public, max-age=600, s-maxage=604800` |
| `/api/v1/lote?limite=1` | `public, max-age=600, s-maxage=3600` |

**Verificado por grep, não suposto**: `grep -rn 'nginx/cache|purge-origin|CACHE_DIR|var/nginx'`
em `cmd/publish-v2-direct/main.go` e `tools/reload-wiki-server` devolve **zero linhas** —
nem o publicador nem o recarregador tocam o cache de origem. Só `deploy-publico` o faz.

O runbook não limpa nem `var/nginx/cache` nem o `CACHE_DIR` do Go. Para as 2.488 rotas
**novas** isso é inócuo (nunca foram cacheadas). Para o passo 13, que reescreve
`body_sections` de **até 3.481 páginas existentes**, é grave: a gêmea Markdown dessas
páginas fica **7 dias** servindo o texto anterior no cache de origem enquanto o HTML,
purgado pelo publicador, serve o novo. É divergência entre os quatro canais — a classe que
o §7 diz que "nenhum teste de paridade enxerga" — e o runbook a cria por omissão.

**Emenda**: replicar o passo 4/7 (descartar `var/nginx/cache` e o `CACHE_DIR` do Go)
imediatamente após a publicação e **antes** de qualquer verificação, seguido de
`warm-origin-cache`. E o passo 13 passa a rodar `check-publicado-no-ar` sobre a população
**alterada**, não só sobre as novas (ver A4).

### A4 — I3 LEITURA 0: veredito com a causa errada e a remediação proibida

Desenho do runbook: `/api/v1/lote?limite=1` → `fim.total` contra `wc -l` do manifesto ⇒
classe `go_desatualizado`, veredito literal **"reinicie pela cadeia; NÃO republique, NÃO
purgue"**.

Medido: `/api/v1/lote` sai com `s-maxage=3600` e `/api/v1/*` está na zona `wj_dyn`
(`ops/nginx/wikijuridica.conf:1606-1617`, comentário literal: *"Mesmo cache de origem da
@markdown: /x/index.md, /api/v1/lote, /api/v1/novidades, /openapi.json e os descritores
/.well-known passam"*). Logo, por até **1 hora** depois de publicar, `fim.total` pode vir
do cache de origem com o número velho **mesmo com o Go já reiniciado e correto**. A
remediação prescrita (reiniciar) não muda a resposta cacheada, e a que resolve (purgar a
origem) está **explicitamente proibida no texto do veredito**. Isso não é risco teórico: é
o loop que o operador vai executar.

**Emenda**: LEITURA 0 pergunta ao Go direto (`http://127.0.0.1:8089`, que é o default de
`WIKI_ORIGEM` em `tools/reload-wiki-server:57`) — essa é a pergunta "o processo carregou".
Uma leitura **separada** pelo nginx (`:8088`) responde a pergunta "a origem serve o que o
processo carregou", e a divergência entre as duas é uma **terceira classe**,
`origem_cacheada`, cuja remediação é `./tools/purge-origin-cache --rota /api/v1/lote …`.
Sem separar as duas leituras, a ferramenta atribui à unit um defeito de cache.

### A5 — Passo 13 é exatamente o evento que a guarda de churn recusa; medido: teto 15

`cmd/publish-v2-direct/main.go:3667-3683`:
```go
fora := registry.ChavesForaDoPlano(plan)
teto := atribuidasAntesDoPlano / 4
if teto < 6 { teto = 6 }
if len(fora) > teto && !opts.permitirChurnDeShard { return fmt.Errorf("RECUSADO: …") }
```
e o comentário de `:3652-3658`, literal: *"a chave da coorte e `<data de revisão>|<área>`,
e a data de revisão e MUTÁVEL. Uma re-datação em massa (…) trocaria TODAS as chaves de uma
vez."*

Medido agora em `data/ops/sitemap_shard_registry.json`: `assigned` = **63**,
`retired` = 6, `tombstones` = 35 ⇒ **teto = max(6, 63/4) = 15**.

Medido também: `atribuidasAntesDoPlano = len(registryDeShard.Assigned)` (`main.go:828-830`).

**Como `fora` é contado de verdade** (`internal/sitemap/shard_registry.go:254-262`):
```go
vivas[ShardKeyFor(shard.CohortKey, posicao[shard.CohortKey])] = true
posicao[shard.CohortKey]++
```
A chave do registry é o par **(chave de coorte, ordinal dentro da coorte)** — não a coorte
inteira. Logo uma coorte **não precisa esvaziar** para produzir `fora`: basta **encolher**.
Uma coorte que ocupava 7 shards e passa a ocupar 3 vaga **4** ordinais.

O passo 13 muda `body_sections` (que está em `CAMPOS_DE_CONTEUDO`,
`tools/generate-page-content-revision:185-186` — confirmado) de até **3.481** páginas, que
migram para a coorte de hoje. A ~32 URLs por shard (medido: `grep -c '<loc>'
public/sitemaps/pages-0001.xml` = 32), isso encolhe as coortes de origem em algo da ordem de
**109 ordinais** — contra um teto de **15**. O número exato depende de como as 3.481 se
distribuem pelas coortes atuais e **eu não o medi**; o que é medido é o teto (15) e o
mecanismo (ordinal, não coorte inteira), e não existe distribuição plausível de 3.481
páginas que mantenha `fora <= 15`.

E o runbook **mandata** a pior forma: *"Agrupe todas as mudanças de corpo numa publicação
só"*. Isso maximiza `len(fora)` numa única transação. O precedente da memória
("guarda-de-churn-nao-desfaz-a-publicacao") diz que a recusa cai no passo 7, com o acervo
**já no ar** — e o runbook responde a exit != 0 com "PARE E NÃO REINICIE", deixando
`public/` e sitemap adiante do processo servido.

**Emenda, e ela vale para o bloco inteiro**: `conciliaRegistryDeShard` é chamado em
`main.go:837` **independentemente** de `-allow-public-write`. Logo uma passada **sem** essa
flag já imprime `registry de shard : N aposentada(s)` ou devolve o RECUSADO — de graça,
sem escrever nada. **O runbook não faz publicação seca em passo nenhum**, e é a leitura mais
barata que ele deixou na mesa: ela responderia, antes de qualquer escrita, se a transação
vai ser recusada no passo 7 com o acervo já no disco. Se `fora > max(6, assigned/4)`,
**fatiar a mudança de corpo em publicações dimensionadas pelo teto** — nunca passar
`--permitir-churn-de-shard`, que aposenta shards para carência e depois 4xx. O agrupamento
que o runbook mandata é certo para `lastmod`/304 e errado para o registry; o critério que
resolve os dois é "a maior fatia que mantém `fora <= teto`".

---

## B. PERDE DADO / CORROMPE ESTADO COMPARTILHADO

### B1 — `--rotulo` do `check-onda-avanca` NÃO isola o baseline; colide com a onda diária

`tools/check-onda-avanca:36-37`:
```bash
ESTADO_DIR=".agents/runtime/onda-avanca"
ESTADO="$ESTADO_DIR/antes.txt"
```
`--rotulo` (`:63-66`) só alimenta o `echo` e o ledger. **O baseline é um arquivo único
global.** E `git status` no início desta sessão mostra `M .agents/runtime/onda-avanca/antes.txt`
e `M …/depois.txt`: a onda diária usa o MESMO arquivo, e o timer dispara 07:31:33Z.

Três consequências concretas:
1. O passo 9 (`--depois --minimo 1 --rotulo "lote-acordaos"`) **não tem `--antes`
   correspondente** em lugar nenhum do runbook. Ele não falha com exit 2 apenas porque
   reutiliza, por acidente, o baseline da travessia — e então `novas` = 5 + N, não N. O
   DEPOIS do passo 9 ("`novas: N`") não confere.
2. Se a onda diária rodar `--antes` entre o passo 5h e o passo 9, o runbook mede contra o
   baseline dela (que já inclui as 5) e `novas` vem errado.
3. Pior, na direção oposta: o `--antes` do runbook **sobrescreve** o baseline da onda, e o
   `--depois` dela passa a reportar `novas: 0` — o falso negativo exato que o pacote
   `internal/tetodelote` foi criado para tornar visível.

**Emenda mínima (1 linha, na ferramenta)**: `ESTADO="$ESTADO_DIR/antes-${ROTULO}.txt"`, com
fallback de leitura em `antes.txt` para não quebrar a onda em voo. Enquanto isso não for
feito, o runbook **tem** de (a) tomar `--antes` próprio imediatamente antes de cada
publicação, (b) declarar o `novas` esperado como acumulado, e (c) registrar presença no bus
`.agents/runtime/coordination/` por `tools/generate-coord-presence`, porque o arquivo é
estado compartilhado com outra frente.

### B2 — O pathspec do passo 10b está incompleto: são 6-7 arquivos, não 3

O runbook: *"Pathspec MEDIDO: os três saem juntos nos commits de deploy (315ac61b,
b8c5fc65, 09f40536)"*. Medido por `git show --name-only` nos três commits que ele cita —
**todos os três carregam pelo menos seis**:

| arquivo | 315ac61b | b8c5fc65 | 09f40536 | no passo 10b? |
|---|---|---|---|---|
| `content/legal_cocitation_index.jsonl` | sim | sim | sim | **NÃO** |
| `content/pages.json` | sim | sim | sim | sim |
| `data/editorial/published_manifest.jsonl` | sim | sim | sim | sim |
| `data/editorial/stock_manifest.json` | sim | sim | sim | **NÃO** |
| `data/ops/edge_cache_purge.jsonl` | sim | sim | sim | **NÃO** |
| `data/ops/edge_cache_warm.jsonl` | sim | sim | sim | **NÃO** |
| `data/ops/page_content_revision.jsonl` | sim | sim | sim | sim |

Consequências: `stock_manifest.json` é reescrito pelo publicador, então o próprio DEPOIS do
passo 10 — "`git status --porcelain data/editorial` **vazio**" — é **inalcançável como o
runbook está escrito**, e o operador vai concluir falha onde houve sucesso. E os ledgers
`edge_cache_purge.jsonl` / `edge_cache_warm.jsonl`, que o passo 11 escreve e cujo conteúdo
o runbook usa como prova, ficam untracked — contra "Produto não fica untracked".

**Emenda**: o pathspec do passo 10b é o dos sete arquivos acima. `legal_cocitation_index`
só existe no commit se A2 for corrigido (é ele que o regenera).

### B3 — `content/pages.json` NÃO está marcado `-diff`; o runbook afirma que está

Medido: `git check-attr diff -- content/pages.json` ⇒ `diff: unspecified`. O
`.gitattributes` lista 16 caminhos e **pages.json não é um deles** — e ele tem
**84.122.261 bytes**, o maior do repo, maior que os quatro monstros somados que motivaram o
arquivo (155 MB de 157 MB, cabeçalho do `.gitattributes`).

O runbook diz o contrário ("marcado `-diff` no .gitattributes") e o operador vai confiar.
Qualquer `git diff` na janela em que ele está staged despeja 84 MB no contexto do agente.

**Emenda**: acrescentar `content/pages.json  -diff` ao `.gitattributes` **antes** do
`git add` (é mudança de renderização, não de conteúdo — o próprio arquivo autoriza só
`-diff`), e nunca rodar `git diff` sem pathspec nessa janela.

### B4 — Passo 11b: lista vazia purga o acervo inteiro, em silêncio

```bash
python3 - > .agents/runtime/purga-descoberta-acordaos.txt <<'PY' …
TETO="$(( $(wc -l < "$LISTA") + 1 ))"
```
O `>` trunca o arquivo **antes** do heredoc rodar. Se o Python levantar exceção antes do
`print()` (raiz diferente, `glob` indisponível, interpretador errado — `glob` vazio **não**
basta, porque os 9 caminhos fixos continuariam), `$LISTA` fica com 0 linhas, `TETO=1`, e em
`tools/purge-edge-cache:191`
`seletivo = bool(caminhos) and …` é **False** com `caminhos` vazio ⇒ `lotes` vazio ⇒
`:205` `lotes = [{"purge_everything": True}]` e `descricao = "tudo"`. **Purga total.** Joga
fora os ~870 s de aquecimento de 11.106 páginas, com o timer de reaquecimento só às 04:20
e 16:20 UTC, e o passo 11c reaquece apenas os ~72 itens de descoberta.

O `--dry-run` imprimiria `purgando : tudo`, mas o runbook não manda **asserir** nada sobre
essa saída — só a lê. E a checagem que ele coloca ("scope nunca 'tudo'") é *post mortem*.

**Emenda**: entre a geração e a purga, duas linhas duras:
`test -s "$LISTA" || { echo "lista vazia — ABORTE"; exit 2; }` e
`./tools/purge-edge-cache --de-arquivo "$LISTA" --teto-por-url "$TETO" --dry-run | grep -q 'URL(s) em' || exit 2`.

---

## C. NÃO EXECUTA / NÚMERO ERRADO

### C1 — A afirmação sobre o NameError está errada, e o modo real de falha é pior

O runbook: *"purga só por `--tag` quebra com NameError no caminho de SUCESSO (`:249` usa
`alvos`) — (…) **e a lista acima do teto cai nele também**"*.

`tools/purge-edge-cache:245-247`:
```python
purga_total = any("purge_everything" in lote for lote in lotes)
if purga_total or len(alvos) >= 1000:
```
`or` faz curto-circuito. Lista acima do teto **sem** `--tag` ⇒ `lotes` vazio ⇒
`purge_everything` ⇒ `purga_total` True ⇒ `len(alvos)` **nunca é avaliado** ⇒ **não há
NameError**: há purga total silenciosa e exit 0. O NameError só ocorre quando há `--tag`
(sozinha, ou junto de uma lista acima do teto).

Isso importa porque o runbook vende o crash como a rede de segurança do caso "lista grande".
Não é: o caso "lista grande" passa sem ruído. (Ver B4.)
**Emenda**: corrigir a frase, e a correção de uma linha na ferramenta é `alvos = []` antes
do `if seletivo:` — com teste que exercite `--tag` sem `--url`.

### C2 — `tools/generate-writeback-extracoes` não existe

Medido: `ls tools/generate-writeback-extracoes` ⇒ ausente. O real é **`cmd/generate-writeback-extracoes`**,
e a invocação viva (`tools/run-daily-content:456`) é:
`timeout 600 nice -n 10 $GO run ./cmd/generate-writeback-extracoes -raiz "$RAIZ"` — com a
flag `-raiz`, que o runbook nunca menciona. O teto 600 s do runbook confere com o da onda.
**Emenda**: a etapa 2 do oneshot é essa linha, literal. Enquanto as 24 etapas forem
**nomes** e não **comandos**, o oneshot não é implementável sem redescoberta.

### C3 — O patch do passo 2 não compila como está escrito

O runbook: *"trocar o `break` por `if !teto.Admite(jaNoShard) { continue }`"*. O `break`
está em `cmd/generate-acordao-pages/main.go:271` (o runbook diz **:265**), e
`intentID := intentDoAcordao(registro)` vem na linha **seguinte**. `jaNoShard` deriva de
`previas[intentID]`, que não existe ainda naquele ponto. **Erro de compilação.**

E há um detalhe que muda o comportamento: `shinglesDoProprioShard` (`main.go:694-717`)
**descarta** páginas com `contaPalavras(corpo) < 50`. Uma linha do shard abaixo disso não
entra em `previas`, seria tratada como inédita e **consumiria cota** ao ser remontada. Hoje
inócuo (corpo min medido 487), mas é a fronteira implícita que faz a regra divergir depois.

**Emenda**: a guarda entra **depois** do `switch` de `:272-290` (após `protegidos` e
`emitidos`), como `jaNoShard := previas[intentID] != nil`; e `teto.Conta(jaNoShard)` depois
do anti-molde. Corrigir também a citação de linha (:271) e a de `tetoPalavras`, que está em
**main.go:83**, não :96. A API de `internal/tetodelote` que o runbook usa está correta e
verificada: `Novo(limite)`, `Admite(jaNoAr)`, `Conta(jaNoAr)`, `Acrescentadas()`.
E `shardpreserve.Completa` (`main.go:2240`) de fato preserva o que não foi reproduzido —
logo a travessia de 5 não é apagada pelo lote cheio. Esse pedaço do runbook sobrevive.

### C4 — O `wc -l` esperado do passo 11b está errado, nas duas direções

Medido: `ls public/sitemaps/pages-*.xml | wc -l` = **63**; `grep -c '<loc>' public/sitemap.xml`
= **57**. O glob do runbook varre o **disco**, então devolve 63 (inclui os 6 em carência que
o próprio `sweep` acabou de listar), não 57. Lista = 63 + 9 = **72**, não "~66".

E o erro maior é temporal: o passo 11 roda **depois** do passo 9. A 32 URLs por shard, 2.488
páginas acrescentam ~78 shards: a lista real será da ordem de **150**. Os dois números que o
runbook manda conferir ("~66" e "`<loc>` = 57") são medições **pré-publicação** apresentadas
como expectativa **pós-publicação**.

**Emenda**: derivar a lista dos `<loc>` de `public/sitemap.xml` (shards que o índice
realmente anuncia), não do glob; e expressar o esperado como `wc -l "$LISTA" == $(grep -c
'<loc>' public/sitemap.xml) + 9`, que é verdade antes e depois.

### C5 — O DEPOIS do passo 9 pede um estado que a publicação não produz

O runbook exige, depois de publicar: "`sweep --seco` **0 vencido(s) e 0 vencendo**".
Medido agora:
```
carencia: 6 shard(s) fora do indice | 0 vencido(s) | 2 vencendo em menos de 48h
exit=0
```
`cmd/publish-v2-direct/main.go:1242` remove apenas `carencia_vencida`. `pages-0094` e
`pages-0095` vencem **2026-09-16T07:50Z** — amanhã: publicar hoje **não** os remove, e
"0 vencendo" fica inalcançável hoje e amanhã. Exit é **0 nos dois casos**, então quem
automatizar pelo exit code não distingue nada.

Risco real: a etapa 16 do oneshot ("sweep `--seco`, exige 0 vencidos") está **correta**; se
alguém a implementar copiando o critério do passo 9, o publicador autônomo **PARA em toda
execução** pelos próximos dois dias. A pré-condição verdadeira de reiniciar o Go é
`0 vencido(s)` — e só.

### C6 — I6 fecha o buraco pequeno e deixa o grande: o coringa `cmd/`

`internal/codex2policyenforcement/policy.go:4506-4516` (íntegro):
```go
return strings.HasPrefix(rel, "internal/datajud") ||
    strings.HasPrefix(rel, "internal/codex2datajud") ||
    strings.HasPrefix(rel, "cmd/social/") ||
    strings.HasPrefix(rel, "internal/consultapublica/") ||
    (strings.HasPrefix(rel, "cmd/") && strings.Contains(rel, "datajud"))
```
O runbook acerta o diagnóstico dos dois prefixos sem barra, e acerta que
`TestTravaDoDatajudPermiteConsumidorLegitimo` (`datajud_trava_estrutural_test.go:96-101`)
nomeia `datajudtpubatch`, `codex2datajudobservations` e
`codex2datajudfrontiersignalreport` e **esquece `internal/datajudfila`** (que só aparece em
`:137`, dentro de outro teste). Tudo confirmado.

Mas a **última cláusula** autoriza qualquer arquivo sob `cmd/` cujo caminho contenha a
substring "datajud" — inclusive um `cmd/build-datajud-pages` ou `cmd/publish-datajud`,
isto é, **dentro do caminho de publicação**, que é a única propriedade que a trava existe
para garantir (comentário de `:840-847`). Os três controles negativos que o runbook propõe
(`internal/datajudrender`, `internal/datajudpublicador`, `internal/codex2datajudhtml`) **não
exercitam essa cláusula**. Resultado: I6 entrega gate verde com o buraco maior intacto.

Segundo ponto, menor mas real: a detecção é
`strings.HasPrefix(imported, "portaljuridico/internal/datajud")` (`:847`) — importar
`internal/codex2datajudobservations` **não é sequer verificado**, então a dependência
transitiva ao DataJud por aquele pacote passa fora do detector.

**Emenda**: as quatro barras que o runbook propõe, **mais** trocar o coringa por
diretórios `cmd/` nomeados, **mais** um controle negativo que prove que
`cmd/build-datajud-pages` é recusado. A prova por mutação de
`internal/datajudfila/cliente.go:106-108` que o runbook propõe é boa e fica.

### C7 — F5: a margem do contrato é 514 páginas, e o teto é 11.620

`tools/check-contrato-vs-medicao:192-193`:
```python
folga = max(200, int(publicadas * 0.05))
if abs(declarado - publicadas) > folga:
```
A folga é calculada sobre **`publicadas`**, que cresce. Com `declarado` = 11.039 fixo,
reprova quando `publicadas - 11039 > publicadas*0,05`, isto é `publicadas > 11.620`.
O runbook diz **11.594** e margem **488**; o correto é **11.620** e **514**. Erro na direção
segura, e a conclusão do runbook (o passo 10a é obrigatório antes do primeiro commit
pós-lote) continua certa. Confirmei o resto: o gate lê a worktree, hoje sai exit 0 com
"11106 linhas, 11106 unique_intent_id / CLAUDE.md declara 11039", o regex é
`r"Estado atual[^:]*:\s*\*{0,2}([\d.  ]+)\s*páginas? públicas?"` (`:52-54`, não :53-55), e a
linha viva é `CLAUDE.md:128`. `CONTRATOS_EXTRA = ("GOAL.md","AGENTS.md")` (`:134`) hoje passa
porque os contadores lá são protegidos por `_e_registro_historico` — não é risco para este
bloco.

### C8 — O runbook prescreve o `timeout` que ele próprio declara inseguro

A LACUNA 6 dele diz: zero `signal.Notify` em `cmd/publish-v2-direct`,
`internal/publicrelease` e `cmd/build`. **Confirmei por grep próprio** — o `grep -rn
'signal.Notify'` nos três caminhos devolve zero linhas; não estou herdando a alegação dele.
E então o passo 9 e a etapa 13 envolvem o
publicador em `timeout 3600`. `timeout` manda **SIGTERM**. Se a transação passar de 3600 s,
o próprio runbook derruba o publicador no meio, sem defers, com o lock órfão e
`public/`+sitemap parciais — e `writeRollbackSnapshot` não cobre `public/`.

E o número 3600 **não é medido**: o runbook mediu 747,9 s do *gerador* (`-seco -limite 5000`)
e nunca mediu o publicador sobre 11.106 páginas. Não há linha de duração no
`data/ops/` que eu tenha encontrado.

**Emenda**: rodar o publicador **sem** `timeout` (o teto da unit, único, é suficiente e
observável), ou tratar `signal.Notify` no publicador como **pré-requisito** do oneshot. E
medir a duração real na travessia e no lote cheio antes de escolher qualquer teto — o número
do oneshot tem de derivar dessa medição, não de um palpite.

### C9 — O oneshot: 8 das 24 etapas sem teto, e a soma declarada não fecha

Somando os tetos que o runbook nomeia por etapa (2:600, 3:2400, 10:900, 11:900, 13:3600,
15:900, 17:90, 19:300, 20:600, 22:300, 23:2400) dá **12.990 s**, não os 13.590 que ele
declara; os dois `300` extras da conta dele não correspondem a etapa nenhuma. E ficam **sem
teto 13 das 24**: o flock (1), os cinco gates (4,5,6,8,16), os três commits (7,9,21),
`onda-avanca` (12,14), `check-publicado-no-ar` (18) e `measure-coorte` (24). Justamente os que podem pendurar —
um commit bloqueado no `.git/index.lock` de outra sessão, ou o 18, que faz leitura de rede
contra a borda. Com `TimeoutStartSec=18000`, a unit pendura 5 h segurando o próprio flock e
morre por SIGTERM.

**Emenda**: teto explícito em **todas** as 24, e `TimeoutStartSec` derivado da soma real
com margem — não o contrário.

### C10 — O oneshot não tem etapa que atualize a linha do contrato: a etapa 21 trava sozinha

O passo 10a existe porque o gate do contrato é incondicional no pre-commit. As 24 etapas do
oneshot **não incluem** essa atualização. A cada execução o oneshot publica N páginas e a
deriva cresce; quando `publicadas > 11.620` (C7), a **etapa 21** (`git add published_manifest`)
passa a reprovar **para sempre**. E o passo 10c do próprio runbook explica a consequência:
`generate-first-published-at` percorre `git log --reverse -- published_manifest.jsonl`, logo
rota que nunca entrou em commit **não tem estreia recuperável** e recebe
`datePublished = hoje` na publicação seguinte. Isto é **o P1b se reproduzindo
autonomamente** — o defeito que o bloco anterior existe para estancar.

**Emenda**: etapa 20-bis no oneshot que reescreva a linha `Estado atual (medido em …)` do
`CLAUDE.md` pelo número medido e a commite **antes** da etapa 21, com
`check-contrato-vs-medicao` exit 0 como pré-condição da 21.

### C11 — O gatilho `.path` está praticamente morto; o `.timer` é que vai trabalhar

Medido: `data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl` existe, 85.557 bytes,
mtime **set 10 09:52** — **5 dias** sem mudar. O runbook justifica o `.path` com "o estoque
é consequência da coleta, não do relógio". Na medição, a coleta não move esse arquivo há 5
dias, então o publicador autônomo roda de fato pelo `.timer`. Não é defeito fatal — é
expectativa errada sobre qual gatilho governa, e o runbook não declara a guarda contra
laço (se alguma etapa tocar o arquivo observado, `PathModified` re-dispara).

### C12 — Passo 5c/5e: `git commit -- <diretório>` varre trabalho de outra sessão

```bash
git commit -F …/msg-portfolio-travessia.txt -- data/editorial/portfolio_v2
```
O `git add` é por caminho exato (correto), mas o **pathspec do `git commit` é o
diretório**. `git commit <pathspec>` não commita o índice: commita o conteúdo da
**árvore de trabalho** de todos os arquivos que casam. Entre a conferência limpa do passo 1
e o 5c passam a geração (`timeout 1800`) e os cinco gates; o timer da onda dispara
07:31:33Z. Qualquer arquivo de portfólio que outra frente tenha deixado modificado no
intervalo entra neste commit. É exatamente o precedente que o contrato registra
("`git add` por diretório já varreu trabalho de outra sessão 3×") — e passar caminho exato
só no `add` **não** fecha, porque o `commit` refaz a seleção por conta própria.
Vale igual para o 5e (`-- data/editorial/v2_pages`) e para o 8c.

**Emenda**: o pathspec do `commit` é o **mesmo caminho exato** do `add`:
`-- data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl`.

---

## FRENTES DE ATAQUE QUE NÃO PRODUZIRAM ACHADO (declaro, não omito)

- **Frente 3 (quebra de produção pelos alvos nomeados)**: verificado que este bloco não
  toca a URL do CSS na CSP (`ops/nginx/security-headers.conf`), nem o hash do script inline
  (`internal/pageinline.Script`), nem unit `Type=notify`/socket, nem o `log.Fatalf` de
  `cmd/social` com `Restart=always`, nem `content/social_policy.json`, nem o namespace do
  cérebro (226/NAMESPACE). Medi a CSP servida em `/api/v1/lote` e ela traz a URL
  `/assets/wj-5b082578c84d2407.css` e o hash `sha256-AxM6ZsiaBmAZXu850m0njvH67GmpJW4q1BXHvVH+PUY=`
  intactos. **Não aplicável** — os riscos deste bloco são A1-A5, que são de canal de máquina,
  cache e registry de sitemap, não de CSP.
- **Frente 7 (decisão devolvida ao dono / espera de horas)**: nenhum passo devolve decisão,
  cadastro, credencial ou aprovação ao dono, e nenhuma espera é por calendário. As esperas
  que ele admite têm número medido e atalho declarado. **Sem achado.** Ressalva única: o
  passo 13 manda medir `check-efeito-nos-bots` com janela de 14+14 dias e propõe o atalho
  certo (`WIKI_EFEITO_NOS_BOTS_LOG=<fixture>`); isso está correto.
- **Frente 8 (rollback impossível)**: o runbook nunca propõe `git reset/checkout/stash/
  clean/revert` — todos os rollbacks são "para frente", e `tools/retirar-pagina-do-ar`
  existe. **Sem achado**, com uma ressalva que já está em A5/C8: o rollback declarado
  ("`writeRollbackSnapshot` cobre 3 arquivos, não cobre `public/`") é honesto, mas o passo 9
  combina isso com `timeout 3600` sobre um binário sem `signal.Notify` — ou seja, ele
  descreve corretamente um rollback que não existe e depois cria a condição que o exigiria.

---

## O QUE O ADVISOR MUDOU

Chamei o advisor com o arquivo já durável. Ele mudou quatro coisas, e nenhuma delas foi
concessão minha sem verificação:

1. **Corrigiu aritmética minha em C9.** Eu havia somado 13.990 s; a soma correta dos 11
   tetos nomeados é **12.990 s**. E eu escrevi "8 das 24 etapas sem teto" quando a minha
   própria enumeração lista 13 (flock, 5 gates, 3 commits, 2 onda-avanca,
   check-publicado-no-ar, measure-coorte). Corrigido. Num documento cuja tese é "os números
   do runbook estão errados", errar os meus seria o pior defeito possível.
2. **Reformulou A5, e a verificação fortaleceu o achado.** Ele apontou que eu confundia
   shard com chave de coorte. Fui ao `internal/sitemap/shard_registry.go:254-262` e o
   mecanismo real é `ShardKeyFor(CohortKey, ordinal)`: a coorte **não precisa esvaziar**,
   basta encolher, e cada shard a menos vaga um ordinal. A ordem de grandeza que eu derivei
   (~109) continua defensável, agora com o mecanismo explícito e a incerteza declarada. E
   daí saiu a emenda mais barata do documento: `conciliaRegistryDeShard` roda **sem**
   `-allow-public-write` (`main.go:837`), então a publicação seca já responde se a transação
   vai ser recusada — e **o runbook não faz publicação seca em passo nenhum**.
3. **Mandou verificar quatro coisas que eu estava supondo.** Resultado:
   - `generate-social-temas` não tem executor nenhum além de `deploy-publico:715` (zero em
     `cmd/publish-v2-direct/`, `ops/systemd/`, `run-daily-content`; nenhum timer social).
     **A1 sobe de "risco" para "garantido", e sozinha carrega o veredito.**
   - `cmd/publish-v2-direct` e `tools/reload-wiki-server` não tocam `var/nginx/cache`
     (grep: zero linhas). **A3 e A4 sobrevivem** — eu tinha lido só o recarregador.
   - `signal.Notify` é zero nos três caminhos. **C8 deixa de ser alegação herdada do
     runbook e passa a ser medição minha.**
   - `wikijuridica-grafo-juridico.service` roda `generate-grafo-juridico` e, em
     `ExecStartPost`, `generate-datasets-publicos` — ele **lê** o índice de co-citação, não o
     regenera. **A2 sobrevive.**
4. **Apontou um ataque que eu não tinha feito**: `git commit -- <diretório>` commita a
   árvore de trabalho, não o índice, então o caminho exato no `add` não protege nada. É o
   C12 acima.

Ele também corrigiu duas imprecisões menores minhas (a citação de linha do comentário do
passo 2.7, e a afirmação de que `glob` vazio esvaziaria a lista do passo 11b — não esvazia;
só uma exceção antes do `print()` esvazia). Não contradisse nenhuma medição minha, então não
houve necessidade de reconciliar.

---

## O QUE SOBREVIVEU AO ATAQUE (verificado, não concedido)

- Todos os comandos e flags que citei checar existem com a grafia do runbook:
  `check-onda-avanca --antes/--depois/--minimo/--alvo/--rotulo`; `purge-edge-cache
  --url/--tag/--de-arquivo/--teto-por-url/--dry-run` (default 3000 confirmado, `:137`);
  `warm-edge-cache --de-arquivo/--rps/--concorrencia`; `warm-origin-cache --rps/--concorrencia`;
  `purge-origin-cache --rota/--seco`; `reload-wiki-server --check`; `generate-brotli-static
  --jobs`; `sweep-sitemap-carencia-expirada --seco`; `generate-first-published-at --dry-run`;
  `check-load-headroom --max`; `publish-v2-direct -reviewed-at/-published-at/-allow-public-write/-limit`.
  Existem também `check-served-vs-manifest`, `check-public-sem-lixo`, `check-csp-style-hashes`,
  `check-shard-preservation`, `check-derived-authorial-floor`, `check-v2-portfolio-pairing`,
  `check-units-alarme`, `check-units-instaladas`, `check-lastmod-causalidade`,
  `check-efeito-nos-bots`, `measure-crawl-coverage`. Os gates `v2-cross-shard-collision`,
  `text-truncation`, `derived-body-repetition`, `http-smoke`, `csp-style-hashes` existem em
  `internal/checks/checks.go` (:449-452, :784, :808).
- **F3 confere**: `-limit` com `-allow-public-write` é recusado com a mensagem literal do
  runbook (`main.go:351-358`).
- **F1 confere**: nenhum shard `*acordao*` em `v2_pages/`.
- **F6 confere** e é a melhor parte do runbook: o publicador varre (`:1242`) e
  `publishedmanifest` recusa no boot (o `return nil, fmt.Errorf("public sitemap shard %s is
  not listed…")` está no caminho chamado por `New()`). A ordem `publicar → varrer →
  reiniciar` **não se inverte**, exatamente como ele diz.
- **O lock do publicador não é contornado**: `cmd/publish-v2-direct` toma
  `data/ops/.publish-v2-direct.lock` ele mesmo (`:95`, `:3972-3979`) e recusa se existir.
  Chamar o `cmd` direto em vez de `tools/publicar` não abre janela de dois publicadores.
- `reload-wiki-server --check` devolve **1** em divergência (`:241`) e 0 sem divergência
  (`:235`) — o passo 6 está certo. `WIKI_ORIGEM` é convenção real do repo (`:57`).
- `httpserver.go:1071` chama `buildAPIPublishedPages` dentro de `New()` — "retrato do boot"
  confere.
- `CAMPOS_DE_CONTEUDO` inclui `body_sections` (`generate-page-content-revision:185-186`) —
  a re-datação do passo 13 é **verdadeira**, e a proibição de `--ressemear` ali está certa.
- A medição que o runbook não fez e que reforça o bloco: **100** intents estão em
  `v2_pages` e **não** no manifesto (11.206 contra 11.106), e **0** no manifesto fora do
  estoque. Casa com os "100 críticos" do §5. Isto significa que o `11.111` esperado do
  passo 5 só vale se o censo do 5f mantiver os 100 críticos barrados — o runbook não declara
  essa dependência, e `--minimo 5` não a detectaria.
- Um ponto em que o runbook é mais cuidadoso que o deploy: purgar
  `/jurisprudencia/index.md` na origem (passo 11a) é necessário e correto — medi
  `s-maxage=604800` nessa rota, e o §7 diz que o índice de área lista **todos** os membros.

---

## RESSALVAS DE HONESTIDADE

- Não executei nada que mute estado. As leituras de rede foram três `curl` contra
  `127.0.0.1:8088` com `Mozilla/5.0 (compatible; WikijuridicaBot/1.0;
  +https://wikijuridica.com.br/bot/; sonda-interna)` e `X-Warming-Request: true`.
- "~109 chaves-coorte" em A5 é **derivado** (3.481 ÷ 32 URLs por shard), não medido: eu não
  rodei o publicador para ver `ChavesForaDoPlano`. O que é medido é `assigned=63` ⇒
  `teto=15`, e 15 é pequeno o bastante para que qualquer estimativa razoável o exceda.
- "~78 shards novos" em C4 é derivado do mesmo jeito (2.488 ÷ 32).
- Não verifiquei os números de bot do passo 7 (p50 1,6 h, 97% em 01h–02h UTC, 686 rotas de
  gptbot na borda), nem os 747,9 s do gerador, nem os 2.488 de F8-bis: não rodei o gerador
  nem os medidores. **Não medido.**
- Não conferi o cabeçalho `A2A-Version: 1.0` nem o `SendMessage` do A2A/MCP contra o
  servidor vivo.
