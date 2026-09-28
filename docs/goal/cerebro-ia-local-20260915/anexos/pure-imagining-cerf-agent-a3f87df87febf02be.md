# Medição: volume real upstream dos espelhos de acórdãos do STJ

MODO SOMENTE LEITURA. Nada foi editado, gravado no repo, nem commitado.

## 0. Correções ao contexto recebido (medidas)

| Afirmação recebida | Medido | Fonte |
|---|---|---|
| host `dados.stj.jus.br` | **`dadosabertos.web.stj.jus.br`** | `internal/stjacordaos/fonte.go:10` (`HostCanonico`) |
| "leia o índice CKAN" | **API do CKAN é `Disallow: /api/`** no robots.txt do host | robots.txt medido nesta sessão |
| CKAN declara `size` | **não declara** na rota permitida (página HTML do dataset) | fetch medido: só `size:` de CSS |
| corte-especial = 44 recursos | **52** competências únicas `.json` | página HTML medida |

Diagnóstico do parent **confirmado por leitura**: `internal/stjacordaos/coleta.go:105`
itera `cfg.Datasets` em ordem e `:176` faz `return rel, fmt.Errorf(...)` no erro de
`ParseEspelhos` — aborta a `Coleta` inteira, não só o recurso. Um mensal malformado
mata todos os datasets seguintes da lista de
`ops/systemd/wikijuridica-stj-acordaos-coleta.service:60`.

## 1. Corpus atual — MEDIDO (duas contagens independentes)

- `cat registros-*.jsonl | wc -l` = **60.221**
- soma de `registros` no `cursor.json` = **60.221**
- bytes upstream correspondentes (`bytes_baixados`, manifest dedup) = **180,40 MiB**

| dataset | janelas | período | registros | MiB upstream | reg/MiB | reg/mês |
|---|---|---|---|---|---|---|
| terceira-turma | 52 | 20220531..20260831 | 30.786 | 88,53 | 347,76 | 592,0 |
| quarta-turma | 52 | 20220531..20260831 | 27.845 | 86,83 | 320,70 | 535,5 |
| segunda-secao | 21 | 20220531..20240131 | 728 | 2,30 | 317,05 | 34,7 |
| primeira-turma | 3 | 20220531..20220731 | 862 | 2,75 | 313,62 | 287,3 |

Aproveitamento medido: 60.221 de 60.271 brutos = **99,92%**
(sigilo excluído: 1; sem ementa: 49). Ou seja, bruto→corpus é praticamente 1:1.

## 2. Razão acórdãos/MiB — MEDIDA, e a premissa do parent REFUTADA

| tipo de órgão | n recursos | pooled reg/MiB | média/recurso | desvio | CV | min–max |
|---|---|---|---|---|---|---|
| TURMA | 107 | **334,04** | 346,8 | 33,1 | 9,6% | 247–444 |
| SEÇÃO | 21 | **317,05** | 325,1 | 42,5 | 13,1% | 221–395 |
| global | 128 | **333,82** | — | — | 10,4% | — |

**A premissa "Seções têm ementas mais longas, logo razão menor" não se sustenta
na medição**: 317,05 vs 334,04 é 5,1% de diferença, dentro da dispersão medida
(CV 9,6–13,1%). O que difere entre seção e turma **não é a densidade de bytes, é o
volume**: 34,7 acórdãos/mês numa Seção contra 535–592 numa Turma — **17× menos**.
É esse fator, e não a razão, que decide a projeção.

Mesmo assim a projeção abaixo usa a **razão por tipo de órgão** (334,04 turma /
317,05 seção), como pedido. Base da seção é n=21 e 2,30 MiB — declarado.

## 3. Por que NÃO usei amostragem por stride — calibração MEDIDA

Calibrei o estimador contra as duas populações cujos 52 tamanhos upstream eu já
tenho no disco (terceira-turma, quarta-turma), aplicando o stride em todos os
offsets e comparando `estimado/real`:

| stride | n amostra | pior \|erro\| 3ª Turma | pior \|erro\| 4ª Turma |
|---|---|---|---|
| 2 (50%) | 26 | 9,2% | 9,9% |
| 3 | 18 | 28,5% | 37,8% |
| 4 | 13 | 20,6% | 18,7% |
| 5 | 11 | 27,9% | 28,6% |
| 6 | 9 | 58,5% | 54,2% |
| 8 | 7 | 70,8% | 58,2% |

A variância mês a mês é grande demais: mesmo amostrando **metade** dos meses o erro
chega a ±9,9%, e stride 8 chega a ±70%. Uma banda assim não seria melhor que o
±30% chutado que eu deveria fechar. **Decisão: enumeração HEAD completa** dos
recursos faltantes — erro de amostragem zero, restando só a dispersão da razão.

Custo: HEAD não baixa corpo. Pacing por `curl --rate 6/m` (uma requisição por 10 s,
= `Crawl-Delay: 10`), numa única invocação serial.

## 4. Identidade de rede usada

`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; coleta-oficial)`

Derivada de `internal/wikijuridicabot/bot.go:82,122` (`UserAgentComProposito`,
`PropositoColetaOficial`). Nenhuma requisição a `/api/`, `/revision/`,
`/dataset/rate/` ou `/dataset/*/history`.

HEAD verificado numa URL: HTTP 200, **0 redirects**, `content-length` presente e
corroborado pelo `etag` (que embute o tamanho).

## 5. Enumeração das páginas — MEDIDO (8 de 8 páginas, HTTP 200)

| dataset | href | competências únicas | dup | já coletado | falta | período |
|---|---|---|---|---|---|---|
| corte-especial | 52 | 52 | 0 | 0 | 52 | 20220531..20260831 |
| primeira-secao | 52 | 52 | 0 | 0 | 52 | 20220531..20260831 |
| segunda-secao | 52 | 52 | 0 | 21 | 31 | 20220531..20260831 |
| terceira-secao | 52 | 52 | 0 | 0 | 52 | 20220531..20260831 |
| primeira-turma | 52 | 52 | 0 | 3 | 49 | 20220531..20260831 |
| segunda-turma | **51** | **51** | 0 | 0 | 51 | 20220531..20260831 |
| quinta-turma | 53 | 52 | **1** | 0 | 52 | 20220531..20260831 |
| sexta-turma | 52 | 52 | 0 | 0 | 52 | 20220531..20260831 |

**Total a medir por HEAD: 391 recursos.**

Todas as contagens de recurso do contexto recebido estão erradas — nenhuma bateu:

| dataset | parent disse | medido |
|---|---|---|
| quinta-turma | 48 | 52 |
| corte-especial | 44 | 52 |
| primeira-secao | 51 | 52 |
| terceira-secao | 51 | 52 |
| segunda-turma | 62 | **51** |
| sexta-turma | 48 | 52 |

A série é uniforme: **52 competências mensais, 2022-05 a 2026-08**, para nove dos
dez datasets. **segunda-turma tem 51** — falta um mês na própria fonte.
**quinta-turma publica 53 links para 52 competências** (uma republicada); o regex
do coletor (`dataset.go:31`) fica com a primeira ocorrência.

## 6. Controle positivo do método (grátis, medido)

O `etag` que a fonte serve embute o tamanho do arquivo
(`W/"<mtime>-<bytes>-<hash>"`). Comparei o número embutido no ETag de cada uma
das **128** competências já coletadas contra o `bytes_baixados` realmente
transferido: **128 conferem, 0 divergem, 0 sem padrão**. Logo o `content-length`
de um HEAD é proxy **exato** do tamanho do arquivo, não aproximação.

## 7. Custo de recuperação — MEDIDO

- Tempo por recurso, mediana real de 138 coletas: **9,98 s** (já inclui o
  Crawl-Delay 10). p90 = 12,12 s.
- 391 recursos → **65,0 min** de parede numa execução sem teto.
- Mas a unit passa `--max-recursos 100` e `rel.RecursosLidos` é contador
  **global** (`coleta.go:150`), e o timer é diário
  (`OnCalendar=*-*-* 09:40:00`). Logo, do jeito que está instalado hoje:
  **391 ÷ 100 = 4 execuções = 4 dias**, não 65 minutos.

## 8. Incidente de medição, declarado

A primeira passada de 391 HEADs (17:00:30–18:11, 66 min, Crawl-Delay respeitado)
**foi perdida por defeito meu de parsing**: usei
`curl -I -w '@@@R %{url_effective} %{http_code}'` e, com `-I`, **o `-w` não é
emitido** — nenhum par URL→tamanho casou e os 391 vieram `SEM_RESPOSTA`.
Diagnostiquei com um teste de 2 URLs que imprimiu a saída crua.

Correção: parear pela **ordem** dos blocos de cabeçalho, com o
`content-disposition: attachment; filename=<AAAAMMDD>.json` servindo de
**verificação de alinhamento** por recurso, e emitir os cabeçalhos **crus e em
streaming**, para que bug de parsing não custe a rede de novo.

Custo honesto disso: a fonte recebeu ~800 HEADs em vez de ~400. Nenhum corpo de
arquivo mensal foi baixado nas duas passadas.

## 9. Resultado da enumeração HEAD

(preenchido abaixo)
