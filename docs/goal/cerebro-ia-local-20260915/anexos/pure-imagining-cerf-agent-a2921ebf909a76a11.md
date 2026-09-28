# Crítico de completude — o que falta às três arquiteturas (2026-09-15)

Sessão read-only. Toda medição abaixo é própria, com população declarada.

## Aproximações declaradas
- Réplica Python de `shinglesNeutralizados`: `[^\w\s]`+strip de `_` contra o Go `[^\p{L}\p{N}\s]`;
  contagem de palavras `[0-9A-Za-zÀ-ÿ]+` contra `ptbrtext.BodyWords` (que dobra PT-BR).
  Daí meu 4.498 contra os 4.500 do Go.
- Contagem de 12-gramas NÃO aplica a isenção `maxLegalCitationSpanWords=40` (validate.go:41).
- Volume na FONTE dos 6 datasets ausentes: **não medido** (exigiria buscar o STJ).
- `-limite 4763`: **não medido** (O(n²); main_test.go:583-589 registra n=1.569 sem terminar em 10 min).

## Q1 — pontos de recusa que NENHUMA das três cobre
1. `internal/stjacordaos/coleta.go:176-178` — coleta aborta inteira em 1 arquivo mensal ruim.
   Unit `ops/systemd/wikijuridica-stj-acordaos-coleta.service:60` lista os 10 datasets de
   `fonte.go:22-32`; rodou 2026-09-15 09:58:12 e FALHOU 09:59:17:
   `segunda-secao competencia 20240229: invalid character '}' after array element`.
   Disco: 4 de 10 datasets (3ª turma 52 comps, 4ª turma 52, 2ª seção 21 parando em 2024-01,
   1ª turma 3). ZERO: corte-especial, 1ª seção, 3ª seção, 2ª turma, 5ª turma, 6ª turma.
   Taxa medida no disco: 3ª turma 30.786/52 ≈ 592 por competência.
2. `cmd/generate-acordao-pages/main.go:74` `pageType="verbete"` → `:84-85` teto 700.
   `internal/v2ingest/validate.go:54-59` tem `guia_problema {700,1400}`. Causa 21+123=144
   de 760 recusas (18,9%) na passada -seco 500. Segundo aperto: `tetoCitado=0.42` (main.go:89)
   contra `TETO_CITADO=0.55` do gate (check-derived-authorial-floor:262).
3. `shinglesPublicados` (main.go:770-802) compara CROSS-família; o gate compara intra-família
   (check-derived-authorial-floor:279-286). MEDIDO E INÓCUO: 64.440 pares cross,
   mediana 0,0079, max 0,0313, zero ≥0,70.
4. `duplicatePhraseNgramSize=12` (validate.go:24) morto no caminho de publicação
   (publish-v2-direct não importa v2ingest: 0 ocorrências). Medido nas 1.134 vivas:
   1.134 de 1.134 (100%) compartilham ≥1 frase idêntica de 12 palavras; mediana 88 por par, max 422.
5. `sem_duas_fontes_oficiais_verificaveis` (main.go:1560) dispara ZERO (limites 30, 120, 500).

## Q2 — conteúdo bom que continua morrendo
- 49.807 procedimentais: nenhuma das três alcança. Medido: 2.902 passam TODO o resto de
  `elegivel`; 4.792 têm dispositivo anunciando mérito no REsp; 270 nos dois conjuntos.
  `procedimental` (main.go:316-324) é Contains, varre `AREsp` puro (11.553; 505 nos 2.902).
  Amostra lida por stride: 3 de 5 são mérito real (CDC 18§1º, CC 205, CPC 628§2º).
  Rota existente e não proposta: `generate-lei-artigo-pages:485-500` JÁ agrega procedimental
  por URN (contadores), e nem ele nem o de acórdão estão em `run-daily-content:368-373`.
- 4.498 ementa curta: só 1.225 com âncora substantiva (SEVERIDADE afirma 2.477; testei 3
  definições — 1.225 / 1.238 / 1.518 — nenhuma chega lá). Estrato honesto: 805 (≥150 palavras
  E âncora). Rota do dispositivo TESTADA E DESCARTADA POR MIM: 4.447 de 4.498 têm
  `dispositivo` ≥25 palavras, mas 3 de 3 lidos são a fórmula de votação ("Vistos, relatados
  e discutidos... acordam os Ministros da TERCEIRA TURMA... por unanimidade, dar provimento...").
  Não é camada citada de substância. `parteOperativa` (:1279-1294) já isola a cláusula que
  decide e descarta os votantes — e essa cláusula é fórmula forense fechada.

## Q3 — afirmação central não verificada
População inteira (1.134 páginas vivas de /jurisprudencia/, 642.411 pares, régua exata do gerador):
- eixo do gerador HOJE: **135 pares, 124 páginas (10,9%), max 0,7701** — e as 124 estão no
  `published_manifest.jsonl`. CAMADAS (stride 5, n=200) mediu 4 pares / 7 páginas / max 0,7258.
- Viés de amostragem de PAR: só se observa o par quando os DOIS membros caem na amostra (~1/25
  no stride 5). Todo número "pares ≥0,70" das três e das duas refutações está subestimado.
- 532 é CURVA, não número: molde por página montada = 15/30=0,50 · 109/120=0,91 · 532/500=1,06
  (medido rodando -seco nos três limites). `aceitas` cresce dentro da passada (main.go:299).

## Q4 — interação perigosa (medida)
| régua (mesmas 1.134, mesmo 0,70) | shingles/pág | max | pares ≥0,70 | páginas |
|---|---|---|---|---|
| 1 corpo inteiro = gerador hoje | 389 | 0,7701 | 135 | 124 (10,9%) |
| 2 CAMADAS VEREDITO §4.3 (s/heading, s/citação, dígito PRESERVADO) | 268 | 0,8605 | 1.069 | 523 (46,1%) |
| 2b CAMADAS eixo D (mesmo corpo, dígito neutralizado; §5 diz MÉDIO) | 264 | 0,9867 | 62.751 | 1.081 (95,3%) |
| 3 aprox. CEREBRO s_residual (menos citação e FAQ inteiro, neutralizado) | 192 | 1,0000 | 52.761 | 1.066 (94,0%) |
CAMADAS mediu por stride 5 (n=200): 18 pares / 19 páginas no eixo C e 160 de 200 no eixo D.
População: 1.069 pares / 523 páginas e 1.081 de 1.134. CAMADAS preserva dígito no veredito;
CEREBRO neutraliza no s_residual — combinar as duas exige escolher, e nenhuma diz qual vence.
Cada partição está certa sozinha; juntas cortam o texto medido pela metade com o limiar parado.
Segunda interação: as três removem molde bloqueante em pontos diferentes; a união deixa ZERO
detector bloqueante de molde no trajeto.

## Q5 — precedentes que contradizem
1. `internal/cerebro/triagem.go:126-148` — mesmo corpus, medido 2026-09-10: classe acessória
   "GOVERNA PRIORIDADE, e nunca exclusao... descartar o estrato jogaria fora esses casos".
   `main.go:516` descarta 49.807. Definições divergentes: `triagem.go:137` ancora `^`;
   `main.go:316` é Contains. Diferença medida: 11.642 registros.
2. `internal/stjacordaos/sigilo.go:53-66` — mesmo pacote recusa supressão por assunto/classe
   ("super-supressao que o contrato proibe"); `:36-46` registra falso positivo corrigido.
3. `tools/check-derived-authorial-floor:271-278` — "FAMÍLIA NOVA ENTRA AQUI OU NASCE FORA DO GATE".
4. `docs/PRECEDENTES_DAS_ORDENS.md:273-277`, `:146` — o caso das 46.
5. `docs/goal/MAESTRO_CODEX_LOG.md:3404` — v2bodyneardup nasceu MinHash-LSH "escala a 1M";
   o produtor usa laço duplo nu.
