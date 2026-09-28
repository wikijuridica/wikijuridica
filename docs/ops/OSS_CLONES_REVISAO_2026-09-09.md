# Revisão dos clones OSS relevantes — 2026-09-09 (frente I do plano de cache/cérebro)

Os 289 clones que moravam na raiz do repositório (96 GB, untracked) foram movidos
por `rename(2)` para `/opt/oss-clones/` em 2026-09-09 (inventário em
`data/ops/oss_clones_inventory.jsonl`; nada foi apagado). Dos 289, 15 tinham uso
plausível para o portal. Um agente de leitura (read-only) leu README e LICENSE de
cada um; a licença dos cinco candidatos a adoção foi conferida em seguida no
próprio arquivo `LICENSE` pelo chefe da sessão (cabeçalho lido no disco). O
veredito abaixo é do chefe, não do agente — em dois casos ele diverge do
relatório do agente, com o motivo.

Regra do contrato que governa tudo aqui (`CLAUDE.md` §3 e §12): dependência
nova que afete runtime exige **ADR, licença revisada, versão fixada e benchmark
10k/100k**; serviço externo ou proprietário é proibido; GPL/AGPL não entram em
código de produção (só ideias, reescritas do zero). Nenhum clone foi adotado
nesta data — esta página é o insumo do ADR de quem for adotar.

| clone | licença (lida no LICENSE) | versão vista | veredito | próximo passo, se houver |
|---|---|---|---|---|
| chromem-go | MPL-2.0 | v0.7.0 (+~30 commits) | **LER-COMO-MOLDE hoje; ADOTAR só acima de 200k vetores** | a busca semântica do cérebro faz força bruta em 3 ms sobre ~10k vetores; medir latência/RAM em 10k, 100k e 1M antes de qualquer ADR |
| go-sdk (MCP oficial) | Apache-2.0 (transição de MIT) | v1.8.0-pre.2; `go.mod` usa v1.7.0 | **JÁ EM USO** — verificar compatibilidade ao sair a v1.8.0 estável | nenhum upgrade por pré-release; a v1.7.0 cobre a spec em uso |
| servers (MCP de referência) | Apache-2.0/MIT | typescript-servers-0.6.2 | **LER-COMO-MOLDE** | padrões de descrição de tool e schema de resposta para `internal/httpserver/mcp*.go`; sem código copiado |
| TrendRadar | GPL-3.0 | v6.10.0 | **DESCARTAR** (só ideias) | o digest diário de audiência/notícias (B6 `analisar_audiencia`) nasce do zero em Python/Go |
| abnt-citation | MIT (CiteMe, 2024–2025) | v0.1.0+ | **LER-COMO-MOLDE** (o agente disse ADOTAR; o chefe diverge) | é TypeScript e o serving é Go: serve como **referência das regras NBR 10520:2023 e NBR 6023:2025** para conferir `/api/v1/citar` (`internal/httpserver/api_citar.go`), nunca como runtime |
| MaxKB | GPL-3.0 | v2.10.6-lts | **DESCARTAR** (só ideias) | pipeline ingest→split→index como desenho para B5 (chunking), reescrito |
| memsearch | MIT (Zilliz, 2025) | dsh-v0.1.4 | **LER-COMO-MOLDE** (o agente disse ADOTAR condicional; o chefe diverge) | depende de Milvus como índice — serviço a mais que o contrato não quer; a ideia útil é a memória em Markdown com dedup por SHA-256 e busca híbrida BM25+densa, que o cérebro pode fazer sobre `data/ai/` e SQLite FTS5 já existentes |
| hivemind | Apache-2.0 | v0.7.150 | **LER-COMO-MOLDE** | cloud-first (Deeplake); só o desenho de sumarização de sessão interessa |
| Scrapling | BSD-3-Clause (Karim Shoair, 2024) | v0.4.15 | **CANDIDATO A ADR** para coleta de fonte oficial | benchmark: 10k normas de `normas.leg.br`, 5 conexões, throughput e taxa de erro. **Ressalva do contrato**: os fetchers "stealth"/anti-bot do projeto NÃO se usam — o portal sai sempre como `WikijuridicaBot` (`internal/wikijuridicabot`), honra `robots.txt` e taxa; o que se aproveita é o parser adaptativo e o spider com fila |
| markitdown | MIT (Microsoft) | v0.1.8b1 | **CANDIDATO A ADR** para PDF/HTML→Markdown de acórdãos e atos | benchmark: 1k PDFs oficiais, s/PDF, % sem erro, amostra manual de 50 (H1/H2/tabelas/links); conversão entra como sinal interno com proveniência (URL, data, hash), nunca como corpo |
| tf-idf-similarity | MIT/BSD-3 | v0.3.0 (Ruby, 2012) | **LER-COMO-MOLDE** | a métrica anti-molde continua Jaccard 5-gramas (medido: deixa passar molde com número intercalado — §8); BM25/TF-IDF como segunda métrica se reescreve em Python |
| api-umbrella | MIT | v1.8.0 (Ruby/Node legado) | **DESCARTAR** | cotas por agente já existem na borda e em `bot-operators.conf`/tiers do nginx |
| ai-gateway | Apache-2.0 (Go) | v1.5.4 | **LER-COMO-MOLDE** | roteador multi-provedor; o portal tem UM Ollama local por ordem do dono (§12) |
| netdata | GPL-3.0 | v2.11.0 | **DESCARTAR** (só ideias) | o painel `/painel/` é HTML estático sem JS sob CSP por hash (8765fe82); ideias de layout apenas |
| grafana | AGPL-3.0 | v10+ | **DESCARTAR** | AGPL; ideias apenas |

## O que muda de imediato

Nada em runtime. Dois ADRs ficam abertos como próximos passos, ambos na camada
de inteligência (Python, fora do caminho de serving, DEC-036): **Scrapling** para
a coleta educada de fonte oficial e **markitdown** para PDF→Markdown com
proveniência. Cada um só entra com benchmark 10k/100k medido e versão fixada em
`pyproject`. `chromem-go` volta a ser avaliado quando `data/ai/embeddings/` passar
de 200k vetores — hoje são ~11k páginas.
