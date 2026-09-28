# Experimentação A/B do acervo — como rodar e como ler o resultado

Frente **F5** do plano de 2026-09-09. Ferramentas:
`tools/generate-experimento`, `tools/measure-experimento`, núcleo em
`tools/experimentos.py`, estado em `data/ai/experimentos.jsonl`.
Bancadas: `tools/test_generate_experimento.py` (17 testes) e
`tools/test_measure_experimento.py` (15 testes).

---

## 1. O desenho, e as três coisas que ele NÃO faz

**A unidade de aleatorização é a PÁGINA, não o visitante.** O acervo sai
estático do disco (`root public/`) atrás de uma CDN com `s-maxage=604800`.
Variar a resposta por visitante na mesma URL exigiria `Vary`/cookie — o que
multiplica a chave de cache e mata os 7 dias de borda — ou decisão por
User-Agent, que é **cloaking** e o Google trata como spam (CLAUDE.md §12:
"mesmo conteúdo para bot e humano, sempre"). Cada página fica num braço só; a
URL continua servindo uma resposta única; a borda continua cacheando.

**A máquina não escreve prosa.** DEC-017. O texto da variante ou já é autoral e
está no estoque v2 — o `h1` publicado virando `<title>`, frases **inteiras** do
`opening` virando meta description — ou é permutação de conteúdo já aprovado (a
ordem do FAQ). O fator "resumo em 3 linhas" nasce em `aguardando_prosa`,
contando quantas páginas esperam texto humano, e **não é preenchido por
ninguém automático**. `tools/test_generate_experimento.py` trava isso: toda
variante gravada tem de ser recorte *verbatim* do registro de origem.

**Nada é aplicado por estas ferramentas.** `generate-experimento` declara a
coorte; a escrita no estoque é do gerador datado com CAS do pipeline v2. O
comando exato sai impresso e fica gravado em `comando_de_aplicacao`.

---

## 2. Rodar

```bash
# 1. ENSAIO (padrão): mostra coorte, censo de recusa e teto. Não escreve nada.
python3 tools/generate-experimento --fator titulo --area familia

# 2. Registrar de verdade (ocupa o teto de 5% e bloqueia as páginas)
python3 tools/generate-experimento --fator titulo --area familia --aplicar

# 3. Medir (ensaio) e depois gravar a medição
python3 tools/measure-experimento --experimento exp-20260910-titulo-familia
python3 tools/measure-experimento --experimento exp-20260910-titulo-familia --gravar
```

```bash
# 4. Fechar o ciclo: registrar que a variante foi ao ar, e depois encerrar
python3 tools/generate-experimento --marcar-aplicado exp-... --aplicado-em 2026-09-15 --aplicar
python3 tools/generate-experimento --encerrar exp-... --estado encerrado_adotado --aplicar
```

Fatores: `titulo` · `meta_description` · `ordem_faq` · `resumo_tres_linhas`.
Escopo: `--area <slug>` (primeiro segmento do path) ou o acervo inteiro.
Tamanho: `--paginas N` ou `--fracao F`; o teto global vale sempre.

**Saídas.** `generate-experimento`: 0 ok · 2 fonte ausente · 3 nada elegível ou
teto esgotado · 4 id repetido. `measure-experimento`: 0 medição concluída ·
2 fonte de desfecho ausente · 3 experimento inexistente · **4 medição A/A**
(variante ainda não aplicada — a medição vale, o veredito não).

---

## 3. O teto de 5% é global, e a interferência é recusada

`int(0,05 × páginas publicadas)` — em 2026-09-10, **551 páginas**, contadas no
`published_manifest.jsonl`. O teto soma **todos** os experimentos ativos
(`aguardando_prosa`, `aguardando_revisao_autoral`, `aguardando_aplicacao`,
`aplicado`). Página que já está em experimento ativo é recusada por
`interferencia:` — duas variantes ao mesmo tempo na mesma página tornam o
desfecho ininterpretável.

---

## 4. Antes de aplicar: confira o A/A e, se preciso, re-sorteie

Enquanto `aplicado_em` for nulo os dois braços servem o mesmo conteúdo. Rodar
`measure-experimento` nessa fase é um **A/A**: mede se o sorteio deixou os
braços equilibrados na linha de base.

Medido em 2026-09-10 no ensaio de `familia`: os braços saíram em 0,102 e 0,087
leituras por página-dia, com P(variante melhor) = 0,0515 — **em conteúdo
idêntico**. Não é defeito do sorteio: 40 sais diferentes sobre a mesma coorte
deram valores de P compatíveis com a uniforme (mediana 0,463; teste de
Kolmogorov–Smirnov p = 0,54), que é o que se espera de uma aleatorização
honesta. Foi sorte ruim daquele sal.

**Procedimento:** se o A/A der P < 0,05 ou P > 0,95, troque `--sal` e refaça a
coorte **antes** de aplicar. Isso é aleatorização restrita, prática padrão em
ensaio por conglomerado — e só é legítimo **antes** da intervenção. Depois de
`aplicado_em`, trocar o sal é fraude: seria escolher a amostra depois de ver o
resultado.

---

## 5. Os desfechos são as séries que existem no disco — com as ressalvas delas

| desfecho | fonte | papel |
|---|---|---|
| `bot_ia_leituras` | `data/ops/origin_bot_routes_daily.jsonl` | **primário** por padrão |
| `bing_impressoes`, `bing_cliques` | `data/ops/bing_webmaster_daily.jsonl` | secundário |
| `clarity_sessoes` | `data/ops/clarity_insights_daily.jsonl` | secundário |

Não há desfecho de conversão: **o portal não mede conversão por página**, e
inventar uma seria número sem medição.

- **Leitura de bot de IA** conta só agente cuja função é `search` ou `user`
  na tabela de `tools/botagents.py`. Treino (GPTBot, Amazonbot, ClaudeBot) fica
  de fora: são 58.246 das 126.480 requisições da série e varrem o acervo
  inteiro, afogando qualquer efeito. É medição de **origem**: com a borda
  servindo `HIT`, o número é **piso**, nunca total. `top_routes` tem teto de
  200 rotas por janela e a medição conta quantas janelas vieram truncadas — o
  truncamento atinge os dois braços por igual, então a **razão** entre eles
  continua interpretável.
- **Bing**: a linha `pagina_diaria` é o total do dia; a quebra por consulta é
  truncada (medido: 277 contra 152 na mesma página-dia). Somar as duas
  famílias duplicaria a contagem — o leitor usa o total e só cai na quebra
  quando não existe total, marcando a página-dia como parcial. A coleta é
  esparsa (três datas em agosto/setembro de 2026, não uma por dia).
- **Clarity**: só linhas com `dimensoes: ["URL"]` (havia **duas** em
  2026-09-10, de janelas 1 e 3 dias). `sessionsCount` vem nulo em parte das
  métricas da mesma URL; vale o maior valor não nulo. As janelas se sobrepõem,
  então as observações são correlacionadas e o intervalo sai otimista — por
  isso este desfecho **informa e não decide**.

**Só o desfecho primário declarado no registro decide.** Medir outro é
legítimo e sai impresso, mas o veredito vira `sem_decisao` com o motivo — é o
que impede escolher a régua depois de ver o número.

---

## 6. A estatística, e o que ela consegue detectar

O desfecho é **contagem por página-dia**, então o modelo é Poisson com prior
Gama (α₀ = 0,5, Jeffreys):

```
λ_braço | dados ~ Gama(α₀ + Σ eventos, taxa = Σ páginas × dias com série)
```

A exposição usa **dias com série**, nunca dias de calendário: dia em que a
coleta não rodou é dia ausente, não zero observado.

Com dois braços, a razão de taxas tem forma fechada — `λv/λc =
(bc/bv)·(av/ac)·F(2av, 2ac)` — logo `P(variante melhor)` e o IC95 saem de
`scipy.stats.f`, **sem Monte Carlo**: o número é reprodutível bit a bit
(R3). Conferido contra 400 mil sorteios semeados na bancada, e contra 2
milhões fora dela: P exato 0,95282 contra 0,95300 do sorteio.

**Thompson sampling** entra como peso de alocação da **próxima** coorte: uma
página não pode trocar de braço no meio da janela, porque isso reescreveria o
HTML, re-dataria o registro e reanunciaria a URL ao buscador — o desfecho
viraria mistura das duas variantes. O peso é P(braço ser o melhor); com três
braços ou mais, ele vem de sorteio com semente fixa, gravada na linha.

**Veredito** (regra fixada no registro **antes** da medição):

| veredito | quando |
|---|---|
| `sem_decisao` | variante não aplicada, ou eventos/páginas-dia abaixo do piso, **com o N que falta** |
| `adotar` | P(variante melhor) ≥ 0,95 **e** IC95 da razão exclui 1 |
| `descartar` | P(variante melhor) ≤ 0,05 **e** IC95 da razão exclui 1 |
| `continuar` | o resto |

O "**e**" é o ponto. Caso real medido: 93 contra 71 eventos dá P = 0,953 —
acima do limiar — com IC95 da razão em [0,956; 1,774], que ainda contém 1. O
veredito correto é `continuar`, e trocar esse "e" por "ou" seria trocar o
título de 5% do acervo por sorte.

**O que este desenho detecta.** Taxa medida no ensaio de 2026-09-10: **0,0942
leitura de bot de IA por página-dia** (418 leituras sobre 4.438 páginas-dia).
Daí, em 14 dias:

| coorte | eventos por braço | menor efeito detectável |
|---|---|---|
| 551 páginas (teto) | ~363 | **+15,1%** |
| 317 páginas (familia) | ~209 | +20,1% |
| 200 páginas | ~132 | +25,6% |

Efeito menor que isso **não se decide em 14 dias** — prolongue a janela ou
amplie a coorte, nunca afrouxe o limiar.

---

## 7. Aplicar a variante (fora destas ferramentas)

1. Revisão autoral das variantes (`aguardando_revisao_autoral` → o autor
   confirma o texto, que já é dele).
2. Gerador datado com CAS, o caminho sancionado para escrever no estoque:
   `canonical_stock_write_lease` + lock exclusivo + CAS por sha256 da linha
   viva em `data/editorial/v2_pages/<shard>.jsonl` (padrão de
   `tools/generate-v2-acento-provisoria-repair-20260813`). O comando nomeado
   está em `comando_de_aplicacao`.
3. `./tools/deploy-publico` **sem `--ressemear`**: título, meta description e
   ordem de FAQ mudam o texto servido, e a re-datação é verdadeira (CLAUDE.md
   §6, matriz "mudei X, então faço Y").
4. Registrar a aplicação — **é isto que tira a medição do modo A/A**:

```bash
python3 tools/generate-experimento --marcar-aplicado exp-20260910-titulo-familia \
        --aplicado-em 2026-09-15 --aplicar
```

5. Ao fim, encerrar — **é isto que devolve as páginas ao teto de 5%**:

```bash
python3 tools/generate-experimento --encerrar exp-20260910-titulo-familia \
        --estado encerrado_adotado --motivo "razão de taxas 1,21, IC95 [1,06; 1,38]" --aplicar
```

Estados terminais: `encerrado_adotado`, `encerrado_descartado`, `cancelado`.
As duas transições entram como linha `tipo: "estado"`, também em ensaio por
padrão. Marcar como aplicado um experimento com prosa pendente é **recusado**:
não se declara no ar um texto que ninguém escreveu.

**Duas conferências do lado da aplicação, que não são destas ferramentas.** A
variante de meta description é prefixo *verbatim* do `opening`, então quem
escrever o gerador de aplicação confere antes se `internal/seo` impõe alguma
regra de meta diferente do corpo; e o `published_manifest.jsonl` também carrega
`title`, de modo que a transação de republicação tem de manter o manifesto
coerente com a mudança no estoque — coerência de artefato é inegociável
(CLAUDE.md §5).

`resumo_tres_linhas` está **bloqueado por construção**: o estoque v2 não tem
campo `resumo` e o `internal/render` não emite bloco de resumo. Aplicá-lo
exige mudança em Go, que é outra frente — o registro diz isso em `bloqueios`.

---

## 8. O ledger

`data/ai/experimentos.jsonl`, append-only, `schema_version: experimentos_v1`,
três espécies de linha (`tipo: "experimento"`, `tipo: "medicao"` e
`tipo: "estado"`, a transição), todas com
`date` e `gerado_em` no topo — é o que `tools/generate-painel` precisa para
mostrar linhas por dia. Linha antiga **nunca** se reescreve: a regra de
veredito de cada experimento fica registrada no dia em que ele nasceu, e é ela
que a medição aplica.

**O estado de hoje se lê DOBRANDO o ledger**, nunca só na linha de criação:
`experimentos.dobra_experimentos()` aplica as linhas `tipo: "estado"` na ordem
e é daí que saem `estado` e `aplicado_em` vigentes. Ler só a criação devolveria
"nunca aplicado" para sempre — toda medição sairia como A/A e o teto de 5%
ficaria preso em experimentos já encerrados.

O registro do experimento carrega a coorte inteira (path, intent, shard,
braço, `u_selecao`, `u_braco`, texto atual e texto da variante). Conferir a
pertinência de uma página não exige rodar nada: ela está na coorte se é
elegível e `sha256(sal + domínio + path)` normalizado ≤ `limiar_selecao`.
