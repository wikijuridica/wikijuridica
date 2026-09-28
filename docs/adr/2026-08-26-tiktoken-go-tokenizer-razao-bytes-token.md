# ADR 2026-08-26: `tiktoken-go/tokenizer` em módulo isolado para medir a razão bytes/token do corpus PT-BR

Status: **aceito e aplicado nesta data.** A dependência entra em `tools/tokenmeter/go.mod`, um módulo Go próprio, e **não** no `go.mod` da raiz.

## Contexto — dois divisores chutados, e um deles cobrando

Dois lugares deste repositório estimavam contagem de token dividindo bytes por 4. Um deles é decorativo. O outro cobra:

```go
func estimateInputTokens(request BatchRequestRecord) int {
	data, _ := json.Marshal(request.Body.Input)
	return len(data) / 4
}
```

`internal/openaireview/review.go:981` (antes desta mudança). O retorno é somado em `estimatedInputTokens` e entra em `buildLedger(...)` — o `PrivacyCostLedgerRecord`, isto é, **um ledger de custo**.

O divisor 4 é a regra de bolso que a própria OpenAI publica **para texto em inglês**. O corpus deste portal é português do Brasil, jurídico e acentuado: cada acento ocupa dois bytes em UTF-8, e o vocabulário BPE das famílias GPT foi treinado predominantemente em inglês, de modo que palavra portuguesa se parte em mais tokens do que a equivalente inglesa. Usar o divisor de outro idioma é chute com aparência de número — e alimentar um ledger de custo com ele é pior do que não medir, porque produz uma cifra que ninguém questiona.

## Decisão

1. Adotar **`github.com/tiktoken-go/tokenizer` v0.8.1** (MIT) como instrumento de medição.
2. Colocá-lo em **`tools/tokenmeter/`, módulo Go isolado com `go.mod` próprio** — nunca no `go.mod` da raiz.
3. Consumir da medição a **constante**, não a biblioteca: `internal/openaireview.BytesPerTokenPTBRLegal`.

O ponto 2 é o que faz a restrição valer. A exigência era "restrito a gerador OFFLINE, nunca no caminho de resposta HTTP". Num módulo isolado isso deixa de ser disciplina e vira estrutura: o binário público não consegue importar o que não está no grafo de módulos dele. Nenhuma revisão futura pode "esquecer" a regra, porque não há como quebrá-la sem editar o `go.mod` da raiz de propósito.

## Alternativa descartada

**`github.com/pkoukk/tiktoken-go` — desqualificado.** Ele baixa o vocabulário BPE em *runtime*. Isso significa chamada de rede dentro de uma ferramenta de medição, resultado que muda conforme a rede e conforme o que estiver hospedado do outro lado, e uma medição não reprodutível offline. O `tiktoken-go/tokenizer` embute o vocabulário no binário.

## Versões fixadas e licenças (lidas no disco, não presumidas)

| Módulo | Versão | Licença | Onde foi lida |
|---|---|---|---|
| `github.com/tiktoken-go/tokenizer` | `v0.8.1` | **MIT** | `$GOMODCACHE/github.com/tiktoken-go/tokenizer@v0.8.1/LICENSE` — "MIT License / Copyright (c) 2023 tiktoken-go" |
| `github.com/dlclark/regexp2/v2` (transitiva) | `v2.5.1` | **MIT** | `$GOMODCACHE/github.com/dlclark/regexp2/v2@v2.5.1/LICENSE` — "The MIT License (MIT) / Copyright (c) Doug Clark" |

`v0.8.1` é a versão mais recente publicada (conferido com `go list -m -versions`, 16 versões listadas, `v0.8.1` a última).

## Benchmark — a medição que substitui o chute

Ferramenta: `tools/tokenmeter`. Codificação: **`o200k_base`**, que é a da família GPT-4o/GPT-5 — a mesma família do `ModelCandidate = "gpt-5.5"` declarado em `internal/openaireview/review.go:30`. Medir com a codificação errada daria outro número e o resultado não valeria nada.

Corpus: o corpo autoral das páginas v2 (`data/editorial/v2_pages/*.jsonl`), montado como `opening + sections + faq` — o corpo **não** tem chave `text`, armadilha catalogada em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`.

| Métrica | Valor medido |
|---|---|
| Documentos | 10.085 |
| Bytes | 39.120.257 |
| Tokens (`o200k_base`) | 8.259.223 |
| **Razão** | **4,7366 bytes/token** |
| Erro de `len(json)/4` | **superestima a contagem em 18,4%** |

Evidência reproduzível: `data/ops/token_ratio_evidence.jsonl`.

**Atenção ao sinal, porque eu mesmo o inverti na primeira leitura e a correção veio de reler o cálculo.** A razão medida ser *maior* que 4 significa que dividir por 4 devolve tokens **a mais**, não a menos: o erro da contagem é `razão/4 − 1 = +18,4%`, e não `(4 − razão)/razão`. Num ledger de custo essa inversão é a diferença entre superfaturar e subfaturar. O campo da evidência que carrega o número diz por extenso o que ele significa (`legacy_divisor_token_count_error_meaning`), justamente para o próximo leitor não repetir o erro.

Uma amostra secundária — Markdown público — foi tentada e **não** produziu medição: não há `.md` em disco sob `public/`, porque a superfície Markdown é gerada sob demanda. O gerador registra isso como aviso em vez de omitir a amostra em silêncio.

## Consequência aplicada

`estimateInputTokens` passa a dividir por `BytesPerTokenPTBRLegal = 4.7366`. O ledger de custo vinha declarando cerca de um quinto de consumo a mais do que o texto realmente custa.

Dois testes sustentam a mudança (`internal/openaireview/token_ratio_test.go`):

- `TestBytesPerTokenConstantVemDaMedicaoCommitada` — ancora a constante na evidência commitada (tolerância 0,05) e reprova se a evidência declarar tokenizador no caminho de requisição, uso de rede em runtime, ou codificação vazia. Constante de custo sem âncora vira chute de novo assim que ninguém lembrar de onde ela saiu.
- `TestEstimateInputTokensNaoUsaMaisODivisorChutado` — fixa a **direção** do erro: a contagem nova tem de ser menor que a antiga.

## Efeito colateral que vale registrar

Criar `tools/tokenmeter/go.mod` fez o gate `dependabot-config` reprovar sozinho, no mesmo dia, com `dependabot_config_missing_gomod_directory: /tools/tokenmeter` — sem ninguém editar lista alguma. Esse gate carregava uma lista literal de quatro diretórios até horas antes (commit `4a21896c`) e teria aprovado o módulo novo em silêncio, como já aprovava `/tools/perf` e `/tools/duckdbolap`. É a primeira confirmação em uso real de que a derivação funciona.

## Limite honesto

A razão de 4,7366 vale para **este corpus, com esta codificação**. Ela não é uma constante universal do português: corpus com mais tabela, mais citação de lei ou mais número teria outra. Por isso a evidência guarda a amostra, a contagem e a codificação — e o teste compara com o que está gravado, não com um número decorado. Refazer a medição é rodar `tools/tokenmeter`.
