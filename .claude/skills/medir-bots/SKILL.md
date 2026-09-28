---
name: medir-bots
description: Use quando a pergunta for quanto um crawler ou bot de IA rastreou o portal.
---

# Medir rastreio de bot

## 0. ANTES DE TUDO: existem DOIS ledgers, com semânticas OPOSTAS

Ler um com a regra do outro é o erro mais caro deste subsistema. Em 2026-08-20 ele
produziu **7 requisições do Googlebot onde havia 269** — fator de 38× — e a
conclusão errada quase virou premissa de um plano inteiro.

| ledger | arquivo | semântica | como ler |
|---|---|---|---|
| **BORDA** | `data/ops/edge_bot_agents_daily.jsonl` | **cumulativo** — cada linha é um retrato desde a meia-noite | **dedup** por `(date, agent_key)`, ficando com a **última**. Somar multiplica |
| **ORIGEM** | `data/ops/origin_bot_traffic_daily.jsonl` | **incremental** — uma linha por janela de cursor (~30 min; medido: **35 linhas/dia** só de googlebot), com `"summable": true` | **SOME** por `(date, agent_key)`. Pegar a última subconta |

O produtor da origem declara a regra em `tools/generate-bot-traffic-origin:70-85`:
*"as linhas do ledger são INCREMENTOS. Quem consome SOMA por (date, agent_key), não
pega a última."* O campo `summable: true` está em cada linha — se ele existe, some.

**Escolha o ledger pela PERGUNTA, não pelo que estiver à mão:**

- **quantas requisições / qual a cobertura** → **borda**. A origem só vê o que o
  cache não absorveu (`s-maxage=604800`): ela é piso, não contador.
- **autenticidade, forjado, PerplexityBot, referer** → **origem**. É lá que existe
  verificação por faixa de IP e rDNS, e o plano Free da Cloudflare não expõe referer.

**Sempre declare a camada ao reportar um número.** Origem e borda medem coisas
diferentes e divergem por ordens de grandeza — em 19/08, Googlebot deu 77 na borda
e 1 na origem, e **nenhum dos dois está errado**.

## 1. Na BORDA, leia pelo leitor canônico, nunca somando linhas

`serie_saneada()` vive em `tools/edgetelemetry.py:236`. Ela faz as duas coisas
que ninguém deve reimplementar: descarta a linha fisicamente impossível e
**deduplica por `(date, agent_key)` mantendo a última** — a convenção do produtor.

```bash
python3 -c "
import sys, collections; sys.path.insert(0,'tools')
import edgetelemetry as et
por_chave, descartadas = et.serie_saneada('.')
K = 'requests_estimated'
san = collections.Counter()
for (dia, agente), r in por_chave.items(): san[agente] += r.get(K,0) or 0
print('descartadas:', len(descartadas))
for k, v in san.most_common(12): print(f'  {k}: {v}')
"
```

## 2. A chave é `requests_estimated` — `requests` não existe

Registro real do ledger: `agent_key`, `date`, `requests_estimated`,
`requests_sampled`, `requests_local_verification`, `verified_bot_categories`.
Ler `.get('requests')` devolve **0 para todo mundo** e parece "nenhum bot passou".
Confirme o esquema antes de somar:

```bash
cd /opt/wiki && head -1 data/ops/edge_bot_agents_daily.jsonl | python3 -m json.tool
```

## 3. Cru mentira, saneado verdade — medido em 2026-08-19

| agente | cru (soma bruta) | saneado |
|---|---|---|
| yandexbot | 1.000.002.631.724 | 10.018 |
| googlebot | 115.644.073 | 9.404 |
| claudebot | 2.487.663 | 43.482 |
| gptbot | 992.095 | 19.030 |
| **perplexitybot** | **2.008** | **0** |

O Perplexity é o caso didático: **2.008 no agregado cru e 0 no saneado**. As 10
linhas descartadas traziam fator de extrapolação de até 1.000.000x e valores
acima do teto físico (`9.926 URLs x 20 req/URL/dia = 198.520`).

## 4. Cobertura por crawler: `crawlers_verified`, nunca `crawlers`

`data/ops/crawl_coverage_state.json` tem **dois** baldes. `crawlers` está
CONGELADO (`identity: user_agent_unverified`, contaminado por sonda própria) e o
válido é `crawlers_verified`. O denominador canônico é `acervo_urls()` = 9.926.

```bash
cd /opt/wiki && python3 -c "
import json, sys; sys.path.insert(0,'tools')
import edgetelemetry as et
acervo = et.acervo_urls('.')
cv = json.load(open('data/ops/crawl_coverage_state.json',encoding='utf-8'))['crawlers_verified']
for k, v in sorted(cv.items(), key=lambda x: -x[1].get('paths_seen_count',0)):
    n = v.get('paths_seen_count',0)
    print(f'{k:<22}{n:>7}{100*n/acervo:>8.1f}%   {v.get(\"last_updated\",\"\")[:10]}')
"
```

Medido em 2026-08-19 (denominador 9.926): amazonbot 99,2% · yandexbot 95,6% ·
googlebot 73,5% · gptbot 51,9% · googleother 33,3% · claudebot 23,8% ·
oai-searchbot 4,0% · chatgpt-user 1,0% · bingbot 0,7% · perplexitybot 0,0%.

## 5. O instrumento de identidade

É `cloudflare_verified_bot_category` (`tools/measure-crawl-coverage:101`), tomado
como **dimensão**, não como filtro — filtrar por uma categoria apagaria os outros
crawlers sem aviso. String de User-Agent não é identidade: qualquer um a forja.

## 6. Retenção de 8 dias

`RETENCAO_DIAS = 8` (`tools/measure-crawl-coverage:110`), medido contra a API:
pedir dia mais velho devolve `code: quota`. Por isso a cobertura é **acumulada**
em estado — recalcular do zero perde o que a janela já não alcança. A ferramenta
mede os 10 crawlers de `CRAWLERS` (`:120`). Ela **escreve** estado e consulta a
API; rode-a só quando a coleta for o objetivo, e leia o estado quando não for.

## 7. Armadilhas que já produziram conclusão errada

- **Aquecimento interno já foi 93,2% do tráfego da borda** (29.552 de ~31.708;
  audiência real 2.156). `httpRequests1dGroups` **não filtra por UA**, então
  qualquer total tirado dele mistura aquecimento com bot real.
- **Log de origem NÃO prova ausência.** Cache de borda serve sem tocar a origem,
  o log tem rotação diária e existe camada de quarentena. "Não achei no log"
  significa "não achei no log", nunca "o bot não veio".
- **Ausência de linha ≠ ausência do fato.** O ledger só tem o que foi coletado.
- **Ler a ORIGEM com a regra da BORDA subconta 38×** (2026-08-20). Pegar a última
  linha por `(date, agent_key)` no `origin_bot_traffic_daily.jsonl` deu Googlebot=7
  em 7 dias; somando — que é o que o produtor manda — são **269**. A coluna de
  forjadas coincidiu pelos dois métodos (concentra-se numa janela só), o que fez o
  número errado **parecer conferido**. Ver seção 0.
- **`status` do ledger de origem NÃO é segregável por autenticidade.** O campo
  agrega a janela inteira. Em 2026-08-20 isso produziu o alarme "GPTBot leva 90% de
  404": no log cru, **100% dos 404 vinham de dois IPs de scanner** e os bots
  autênticos recebiam 200. Para status por bot, vá ao log do nginx.
- **`requests_estimated` só é extrapolado às vezes.** O fator real medido é ≤ 4,46
  (linhas com fator de 1.000.000 ficam em quarentena), e em 13–19/08 o fator era
  **1,00** — estimado = amostrado. Não descarte o número da borda supondo inflação
  sem calcular `estimated/sampled`.
- Escopo: o access log do wiki é `wikijuridica/access.log`. `access-bots.log` é
  de outro projeto e não entra em medição deste portal.

---

*Verificado em 2026-08-19: esta skill pode ser **pré-carregada** num subagente pelo campo
`skills:` do frontmatter do agente (`.claude/agents/*.md`) — testado, o conteúdo chega no
startup sem o subagente precisar invocá-la. Útil para agente que mede bots por padrão.*
