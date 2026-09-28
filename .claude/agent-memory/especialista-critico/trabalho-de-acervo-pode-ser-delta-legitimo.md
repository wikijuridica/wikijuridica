---
name: trabalho-de-acervo-pode-ser-delta-legitimo
description: Etapa que processa o acervo inteiro não prova guarda de delta ausente — leia o contador de mudança do PRODUTOR antes de acusar
metadata:
  type: feedback
---

Quando uma etapa a jusante faz trabalho proporcional ao ACERVO e você suspeita
que falta guarda de delta, **leia primeiro o contador de mudança do produtor a
montante**. O trabalho de acervo pode ser delta legítimo: o delta era o acervo.

**Why:** medido em 2026-09-16. O passo `1/7` do `deploy-publico` passou de
1.044 s e o `generate-brotli-static` recomprimiu **18.093** arquivos, com todos
os 19.091 `.html` e seus `.br` carregando mtime das últimas 45 min. A hipótese
óbvia — "o publicador reescreve arquivo idêntico e destrói o sinal de mtime de
que o brotli depende" — é **falsa**, e duas evidências a derrubaram:

1. `cmd/publish-v2-direct` já tem a guarda: `escritorPublico.grava` faz
   `os.ReadFile(target)` + `bytes.Equal` e devolve sem escrever quando os bytes
   batem. Ela é a razão de o passo LER mais do que escreve (1,6 GB lidos contra
   900 MB escritos) — ler para comparar é o desenho certo.
2. O produtor publica o próprio contador, e ele é a autoridade:
   `HTML escrito : 18687 páginas (17909 reescritas, 778 inalteradas com mtime
   preservado, 26 com mtime alinhado à data editorial)`.

Com 17.909 reescritas de verdade, os 18.093 `.br` do brotli eram trabalho
**correto**, e "consertar a seleção de alvo do brotli" teria sido conserto de
sintoma no lugar errado. A pergunta certa move-se para montante: por que 95,8%
das páginas mudaram de bytes quando o lote novo era muito menor.

Diagnóstico de mtime tem ainda um detalhe que engana no sentido oposto: o mesmo
publicador chama `os.Chtimes` para alinhar o mtime à data editorial (data no
PASSADO), então em parte do acervo o mtime **não** é o instante da escrita.

**How to apply:** antes de propor guarda de delta em qualquer etapa deste deploy
(brotli, sitemap, purga de borda, aquecimento), procure a linha de contador do
produtor no log do `deploy-publico` — ela distingue "reescritas" de
"inalteradas". Sem essa linha lida, a acusação é inferência. Ver
[[campo-proxy-nao-e-campo-fato]] e
[[invalidar-cache-por-formula-nao-mede-ausencia]].
