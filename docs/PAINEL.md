# PAINEL.md — o painel local do dono

**O que é.** Um HTML estático — sem JavaScript, sem fonte, folha ou script
externo — que reúne, numa página só, o que os ledgers de `data/ops/` já dizem
sobre a borda, os bots de IA, o Bing, o Clarity, o cérebro local e a rede
social. É para o dono ler e para o Claude Code analisar: os mesmos números
saem em JSON (`data/ops/painel/*.json`, `schema_version: painel_v1`), então
uma sessão responde "quanto o GPTBot leu ontem?" lendo um arquivo de 25 KB em
vez de reprocessar 20 MB de ledger.

**O que não é.** Não é analytics de visitante (isso é o Clarity/GA4, seção
"Humanos"), não é gate, não sonda a rede, não escreve em `public/` e não
publica nada. É leitura de disco, local, `noindex`.

## Gerar e abrir

```bash
./tools/generate-painel                 # 30 dias → var/painel/index.html + data/ops/painel/*.json
./tools/generate-painel --dias 90       # janela maior (o HTML tem teto de 400 KB; exit 2 se passar)
python3 tools/test_generate_painel.py   # bancada: fixtures pequenas, ~0,3 s
```

Hoje abre-se **o arquivo**: `xdg-open var/painel/index.html` (ou o caminho
`file:///opt/wiki/var/painel/index.html` no navegador). A URL
`http://127.0.0.1:8088/painel/` ainda **não existe** — o nginx do wiki não tem
a `location`; quando a tiver, apontará para `var/painel/` e o painel continua
fora do acervo público. `var/` não é rastreado pelo git; `data/ops/painel/` é,
e o gerador só regrava um JSON quando o conteúdo mudou (ignora `gerado_em`,
`mtime` e `commit`), para o timer não sujar a árvore: `gerado_em` e `commit`
de um JSON são os da última mudança de conteúdo, enquanto o cabeçalho do HTML
leva sempre o HEAD corrente.

Timer: `ops/systemd/wikijuridica-painel.{service,timer}`, a cada 3 h
(instalação nos comentários da unit). Medido em 2026-09-09: 3,3 s, 140 MB de
RSS, HTML de 161 KB.

O tema segue o sistema (`prefers-color-scheme`); `data-theme="dark"|"light"`
no `<html>` força. Cada gráfico tem um `Tabela` dobrável com os mesmos
valores — é a versão legível por leitor de tela e o alívio de contraste dos
tons claros da paleta — e o cabeçalho traz `gerado_em`, o commit
(`git rev-parse --short HEAD`) e a janela.

## O que cada número é — e não é

| Seção | Número | É | Não é |
|---|---|---|---|
| Borda | `requests`, `page_views`, `uniques` | Contagem bruta da zona em `edge_traffic_daily.jsonl` (última linha do dia vence) | Audiência: inclui aquecedor e sondas. `organic_requests` = bruto − `self_warming_requests` |
| Borda | ponto oco / `provisorio` | Dia em curso; a linha final de D nasce em D+1 06:20 UTC | Queda de tráfego |
| Borda | HIT/MISS por dia | `cache_baseline_daily.jsonl`, GraphQL, todo o tráfego (o bloco "sem tráfego próprio" é o que vem de fora) | Série longa: a linha de base existe desde 2026-09-08 |
| Borda | "quente antes do aquecedor" | `cobertura_pre_head` da última execução do dia em `edge_cache_warm.jsonl`: HEAD antes do GET | O HIT que o aquecedor relata (esse mede o que ele mesmo acabou de aquecer) |
| Borda | purgas por escopo | Execuções em `edge_cache_purge.jsonl`: `tudo` / por URL / por tag, com URLs e tags declaradas ao lado; `success ≠ true` conta em falhas | Objetos realmente removidos da borda |
| Bots | leituras por agente | `requests_sampled` de `edge_bot_agents_daily.jsonl` via `tools/edgetelemetry.serie_saneada` (linhas impossíveis descartadas, contagem na ressalva); v1 antigo cai em `requests_estimated`; os 6 maiores agentes com `function` ∈ {training, search, user} + `outros` | Todo o tráfego de bot: SEO (SemrushBot, MJ12), social, diagnóstico e scanner ficam em `outros`; a tabela de travessia e o JSON (`funcoes_por_agente`) trazem todos, com a função |
| Bots | travessia | origem ÷ borda no último dia completo, mesma fórmula de `generate-cache-baseline` (origem = Σ `requests_authentic` das janelas `summable`); a coluna "linha de base" é o valor gravado por ele — os dois batem (0 diferenças em 29 agentes, 2026-09-08) | Taxa de MISS: acima de 1 é bot que chegou à origem mais do que a borda contou (Markdown dinâmico, identidade não verificada) |
| Bots | Radar IA | `radar_ia_daily.jsonl`: leituras verificadas na origem, forjadas descontadas | A mesma grandeza da borda |
| Bots | retorno | `bot_return_daily.jsonl`: veio hoje, dias desde a visita, cobertura acumulada; `clique_de_volta` é limite inferior de interesse | Contagem de citação |
| Bing | impressões, cliques, InIndex, CrawledPages, 5xx | `bing_webmaster_daily.jsonl`, `busca_diaria`/`rastreio_diario`, última coleta por `Date` | Dado do dia: o Bing publica com atraso; os últimos dias vêm zerados até serem computados |
| Bing | top consultas/páginas | Último `Date` presente na janela, ordenado por impressões; posição −1 = sem dado | Série |
| Humanos | sessões, dead/rage/quickback | Clarity, dimensão Device, **janela de `janela_dias` dias coletada no dia D** | Sessões por dia; não se soma entre coletas |
| Humanos | top URLs | Última linha com dimensão URL | Ranking do mês |
| Cérebro | fila | `select tipo, estado, count(*)` em `data/ai/fila.sqlite` (mode=ro), no instante da geração | Série |
| Cérebro | itens, segundos-máquina, tok/s | `ia_local_daily.jsonl`: Σ `lote`, Σ `custo_segundos_maquina`; tok/s = Σ tokens ÷ Σ segundos por (tipo, modelo), lotes com erro fora | Média das taxas por lote; embeddings têm `eval_tokens` = 0 por natureza |
| Social | contagens | `count(*)` de perfis, dúvidas, respostas, posts_blog, follows em `var/social/social.db` (mode=ro) | Nenhuma coluna é lida; nunca PII |
| Frescor / experimentos | — | `edge_frescor_daily.jsonl` e `data/ai/experimentos.jsonl` quando existem: linhas por dia e escalares da última linha; senão "sem série ainda" | Interpretação: o esquema deles ainda não é conhecido do painel |
| Previsão | taxa semanal com IC80/IC95, projeções de 30/90/180 d por série, top áreas por valor esperado | `data/ops/painel/previsao.json`, escrito por `tools/generate-previsao-audiencia --gravar` (unit `wikijuridica-previsao`, 07:10 UTC); o painel só lê e mostra texto e tabela por série | Medição: é extrapolação log-linear com sazonalidade semanal sobre 60 dias, ponto = mediana condicional; ausente = "ainda sem previsão" com o motivo, nunca zero. Regras e leitura em `docs/MEDICAO_DE_AUDIENCIA.md` |

Cada valor no HTML tem o arquivo de origem ao lado, e cada JSON traz
`fontes` e `ressalvas`. `resumo.json` lista todos os arquivos lidos com
`existe`, `linhas` e `mtime` — ausência de arquivo aparece como ausência,
nunca como zero.
