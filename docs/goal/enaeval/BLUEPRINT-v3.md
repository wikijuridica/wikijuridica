> **AVISO DE LEITURA (v4, 22/09/2026).** Este é o **Volume I** (Blueprint v3, 16/09/2026). Ele permanece como base
> técnica das Partes I–III, mas **onde conflitar com o CANON-v4.1 e com as DECISÕES D-1…D-17, vale o v4.1**.
> Itens deste volume que foram REVOGADOS pelo dono e pela engenharia da Onda F/G (lista completa no CANON-v4.1 §REVOGADO
> e no HANDBOOK, registro de decisões): RAM 96 GB no dia 0 (hardware é 32 GB, definitivo); transbordo Vast.ai/RunPod e
> qualquer nuvem; compra de 3090/2ª 5060 Ti; "14B FP8 residente"; Bespoke-MiniCheck/MiniCheck; VectorChord, MuPDF,
> Chandra-2, MinerU-2509, X-LoRA, Wan 2.2, XTTS; Cloudflare Pay-per-Crawl como trilho primário; janela noturna de treino;
> todo cronograma em dias/meses (o plano é por FASES/OBJETIVOS — ver TASKLIST-ENAEVAL); "5 personas" (são 4); τ hardcoded;
> folga de GPU 47.861 (é 45.600, dois perfis); catálogo de ferramentas manual (é gerado: 53+13+9).
> O bot chama-se **EnaEval**. Baseline do dono: ≥ 3.300 citações/dia, 6.086 crawls/dia, 18.774 páginas, ~10k req/mês na API social.

# Wiki Jurídica IA-First — Blueprint de Engenharia v3

**Data-base:** 22/09/2026. **Dono da ideia e do projeto:** Rafael Toledo (OAB/RJ 227.191). **Método:** 45 agentes de engenharia lançados em 6 ondas (44 concluídos), cada um com relatório completo em `research/`, auditoria independente de fontes (E04: 295 IDs de arXiv verificados, 295 existem; 15 correções de versão/licença aplicadas) e três redatores de síntese. Este documento consolida tudo em uma arquitetura executável. Ele **evolui** o Blueprint v2 (15/09/2026): mantém as 12 decisões que resistiram, substitui as que a engenharia derrubou e acrescenta as 12 camadas que o v2 não tinha.

**Autoridade:** os números do dono (CORRECOES-DONO.md) governam. Onde um relatório de origem diverge, vale o CANON e a divergência está registrada em linha `supera:`.

---

## 0.1 O que este documento é

Uma plataforma jurídica **viva**: um bot próprio, pequeno e adaptado, que responde com prova, aprende todo dia, opera 24/7, conversa e negocia com as IAs do mundo, cobra por chamada e se paga sozinho. O v2 descrevia um *modelo*. O v3 descreve um *organismo* — com sistema nervoso (agente + memória), metabolismo (tesouraria + preço-sombra), sistema imune (três planos de segurança + compliance como código), genoma versionado (modelo + bench + registry) e um único órgão de verdade: o verificador V⁴, que é ao mesmo tempo portão de runtime, produto vendável, função de recompensa e gerador de teste.

O ponto de partida é uma plataforma que **já é de classe mundial na camada de protocolo**: `/mcp` com 15 ferramentas registradas no MCP Registry oficial, agent-card A2A, ai-catalog, OpenAPI com 13 operações, lote NDJSON, `/api/v1/citacoes` (que já é o `/verify`), 6 datasets abertos com sha256, `llms.txt`, CSL-JSON, `repr_digest` RFC 9530 — e que, com a IA ainda em CPU, já recebe **≥ 1.150 citações por IAs por dia, 6.086 leituras verificadas de bots de IA por dia e tráfego humano substancial**. O v3 nasce em cima disso, sem parar nada que já gera citação.

## 0.2 Sumário executivo

**O bot.** Qwen3-8B denso em NVFP4 residente nos 16 GB da RTX 5060 Ti, com vocabulário estendido em +916 tokens (URN LexML cai de 33 para 16 tokens; contexto de RAG ganha 31%), atenção com janela deslizante 5:1 (KV de 128k cai 5,19×), cabeças de risco para o roteador e um decoder que, ao emitir `⟨URN⟩`, comuta para uma **trie das URNs que realmente existem na data de referência** — citação inventada deixa de ser improvável e passa a ser impossível por construção. Um aluno Qwen3-4B destilado (LoRP + Minitron width, GSPO-DrC) atende o alto volume; Gemma-4-26B-A4B (Apache-2.0) em EXL3 entra sob demanda como professor e escalada; BitNet-b1.58 roda 24/7 na CPU como monitor e classificador. A matriz de compute por capacidade está fechada: VERIFICAR e MONITORAR nunca tocam GPU; CITAR é 4B + gramática; RESPONDER/PUBLICAR/NEGOCIAR é 8B; todo número e toda data saem de código determinístico (4.626 linhas Go, zero dependências, 50 ms, 0 GPU), porque o erro dominante de modelo pequeno é valor de parâmetro (59–66%) e a gramática de saída proíbe dígito fora de ferramenta.

**A verdade.** Um verificador só — `wj-nli-54M`, encoder MIT podado de 140M para 54M, τ = 0,906 fixado por controle conformal — decide se um trecho oficial sustenta uma afirmação. Ele é *fail-closed* no serializador e no banco: frase sem `proof` não serializa, e a FK composta `(receipt_id, span_sha256)` torna "recibo verdadeiro colado em trecho alheio" inexprimível. Sobre ele assentam a recompensa de treino (alucinação ⇒ recompensa negativa, provado algebricamente), o portão de promoção (HCR ≤ 2%, ASR = 0, no artefato *quantizado*), a métrica de alucinação corrigida por cobertura (publicamos o denominador) e o produto `/verify` com Retrieval Receipt Ed25519 — verificável offline por qualquer terceiro em 172 µs com 472 linhas de Go sem dependências.

**O tempo.** O direito brasileiro é função do tempo e nenhuma plataforma trata isso corretamente. O modelo é **tri-temporal** (vigência × eficácia × transação — exigido por CF art. 62 §11, Lei 9.868/99 arts. 27 e 11 §2º), com `EXCLUDE USING gist` mais totalidade por trigger: toda consulta *point-in-time* devolve exatamente uma linha, provado. A consolidação de normas é adversarial (dois parsers independentes têm de coincidir na forma canônica; divergência bloqueia selo e vira rótulo de treino). A aresta `INTERPRETA(acórdão → dispositivo@sha_da_redação)` prende cada decisão à redação que ela interpretou. O apelido normativo é função de (string, data) — "Lei de Licitações" era a 8.666/93 até 30/12/2023 e é a 14.133/2021 depois. O cache semântico morre por vigência. O adaptador LoRA morre por vigência. O teste de regressão WJ-Retro se gera sozinho a partir de cada intervalo de vigência fechado: a mesma mudança de lei que ameaça o modelo produz o teste que o protege.

**O compute.** A máquina roda 24/7. Orçamento real: 86.400 GPU-s/dia contra 38.539 de demanda somada de todos os 41 relatórios — **55,4% de folga**, 1,66 noites-equivalentes de treino por dia, todo dia. Serving e lote são co-residentes (MPS + `--scheduling-policy priority`); a preempção custa um *step* de 50–100 ms sem perder KV; o lote **freia** de 20% para 5% dos SMs em vez de desligar, e por isso colhe folgas de segundos. O escalonador foi verificado em TLA+ (1.936 estados, 0 erros) depois que o model checker achou, no desenho anterior, perda de requisição paga por `sleep` antes de checar a fila. Capacidade simultânea em regime: **11.600 chamadas pagas/dia + 2.000 answer units/dia + 1,66 GPU-noites de treino**. Todo recurso escasso é alocado por um único preço-sombra, λ_gpu = R$ 0,00090/GPU-s (custo de oportunidade, 15× a energia), que decide ao mesmo tempo o que gerar, o que treinar, quando alugar GPU externa (Vast.ai a R$ 0,301/GPU-h: dispara sempre que o link permitir) e quando comprar a segunda placa.

**A economia.** Nove produtos M2M; só três tocam GPU. Trilho de pagamento primário: x402 self-hosted em Go (`x402-foundation/x402/go/v2@v2.26.0`), com o Cloudflare Pay-per-Crawl entrando quando sair do *closed beta*. `/verify` custa R$ 0,00135 por chamada no piso totalmente alocado e é instrumento de descoberta de preço, não de receita: avulso é *posted price* com bandit; pacote, licença e exclusividade negociam por SAOP em no máximo 6 rodadas, com o número **nunca** saindo do LLM — por antitruste (dois deployments do mesmo modelo correlacionam preço a +0,053 sem acordo nenhum), garantido por invariante de importação no CI. Custo fixo R$ 1.199,26/mês; break-even com 5.034 `/verify`/dia ou um único knowledge pack. Tesouraria por programação dinâmica aproximada: colchão de 6 meses, hurdle = Selic líquida (0,9150%/mês), payback ≤ 18 meses, quarter-Kelly; o mesmo λ_gpu que aloca conteúdo autoriza a compra da 3090. Ledger de dupla entrada com os quatro furos que o model checking achou já fechados, assinado com a mesma chave Ed25519 dos recibos: **prova de solvência verificável por máquina**. LC 123 art. 18 §14 zera Cofins+PIS+ISS na exportação; chave emitida por PJ, nunca por pessoa física.

**A confiança.** `did:web` ancorado em DNSSEC, hierarquia de chaves com raiz offline Shamir 3-de-5, recibos COSE/SCITT (RFC 9942/9943), log Merkle contínuo com MMD de 60 s onde chaves e recibos vivem juntos (retrodatar chave é impossível), reputação MeritRank com α = 0,40/β = 0,60 (os parâmetros de manual tornam Sybil lucrativo com payback de 343 dias), *bond* que confisca 100% do VPL do ataque. Três Internet-Drafts escritos, compilados e validados (recibo de citação jurídica, identificador temporal de norma, contrato de previsão auditável) — o vertical jurídico tem oito perfis SCITT para IA e zero para *citação*; o prazo é o I-D cutoff do IETF 127, 02/11/2026. A Res. CNJ 615/2025 art. 2º IX manda o CNIAJ definir "fonte privada auditável": quem escrever essa definição escreve o critério de compra do Judiciário.

**A segurança.** Três planos *físicos*: o Plano-D lê a internet e nunca emite intenção; o Plano-C decide e só consome valores tipados por socket Unix (enum, decimal, `urn:lex:`, sha256 — zero string livre); o Plano-T (tesouraria) não tem LLM nem egresso. Um byte não confiável rebaixa o teto de capacidade monotonicamente e `CapSpend` nunca é readmitido na sessão. Gasto acima de R$ 2,50 exige FROST 2-de-3; o *float* quente é o orçamento diário; o *dead-man* é invertido (o heartbeat renova a capacidade de gastar; queda ⇒ fail-closed em 180 s). Contribuição externa entra só em retrieval, com quarentena, porque ~250 documentos bastam para envenenar um modelo de qualquer tamanho. Compliance é Cedar (prova formal em Lean4) com veto no grafo do agente: 17 políticas citando artigo exato de LGPD, Lei 9.610, Lei 8.906, Res. CNJ 121, 615/2025 (alt. 674/2026). PL 2338/2023 não é lei; jurimetria é baixo risco (anexo BR3).

**A rede de IAs.** Não é CRUD social. É um **Mercado de Procedência** com um primitivo só — a Alegação Comprometida (claim Ed25519 com probabilidade, URNs e commit-reveal) — pago por regra de pontuação própria (pago = b·(1−Brier)), com dinheiro nunca em risco do participante. O preço agregado é mistura bayesiana com garantia: o consenso perde no máximo ln N nats para a melhor IA em retrospecto, e o comprador com dor real é quem classifica contingência em provável/possível/remota (CPC 25/IAS 37). O moot court é *prospectivo por construção*: dispara no saneamento (CPC art. 357) e o gabarito são os movimentos TPU do tribunal — vazamento impossível, não proibido. Toda alegação resolve em ≤ 2 saltos em fonte oficial humana.

**O crescimento.** Re-ancorado no dado do dono: ≥ 1.150 citações/dia → 100.000/dia é fator ~87×, decomposto em sete alavancas independentes (cobertura 2,10× · rank⊕exclusividade 3,11× · motores 2,29× · âncoras 1,60× · verificação 1,25× · frescor 1,50× · clusters de consulta 3,00×) que multiplicam para 134× — a meta é cruzada no **dia ~168** no piso do modelo, com crawls e tráfego humano como canais próprios, cada um com sua curva. Nenhuma curva é teto; expansão (PT/África, LatAm, common law) usa o mesmo motor. O que já funciona (protocolo) é amplificado; o que está em zero (answer unit sem TL;DR, sem número, com a resposta na 250ª palavra) é ganho inteiro.

**A execução.** Unidade de esforço = sessão de Claude Code (1 sessão ≈ 1,1–1,7 engenheiro-semana, calibrado contra a própria frota); ~151 sessões em 365 dias. Fase 0 (14 dias, 0 GPU) liga IndexNow, ETag, 402, Web Bot Auth e publica as 4 ferramentas determinísticas já escritas. O verificador vem **antes** da geração em massa, por álgebra: publicar sem verificador tem valor esperado negativo. Rafael gasta 4/10/6/2 horas por semana nas quatro fases, com ~100 h de julgamento jurídico indelegável concentradas nos dias 20–100. A primeira semana está escrita hora a hora.

## 0.3 O que mudou de v2 para v3

| Decisão do v2 | Decisão do v3 | Por quê (origem) |
|---|---|---|
| 14B FP8 residente | Qwen3-8B NVFP4 residente + 4B destilado + 26B-A4B sob demanda | 14B FP8 ocupa 14,7 GB e deixa 348 MiB de KV (A05, E02) |
| Minitron prune+distill | LoRP (profundidade, treino-livre) + Minitron width single-shot | poda mais barata e superior em 2026 (A04) |
| GRPO/RLVR via Unsloth | GSPO + Dr.GRPO + Clip-Higher; vigência como penalidade −0,60 | GRPO puro colapsa; RL geral piora escolha temporal da lei (A04, D05) |
| MiniCheck / Bespoke-MiniCheck-7B como NLI | `wj-nli-54M` próprio, MIT, τ = 0,906 | Bespoke sem licença; MiniCheck en-only; cego ao negativo "redação anterior" (D04, E04) |
| Cloudflare Pay-per-Crawl como trilho | x402 self-hosted em Go como trilho primário | PPC e Monetization Gateway em closed beta (B03) |
| Janela noturna de treino (6–8 h) | Escalonador contínuo 24/7 com preempção latchada | 86.400 GPU-s/dia, folga 55,4%; sleep-no-laço perdia requisição paga (E02, D10) |
| Custo por resposta = energia | λ_gpu = custo de oportunidade, R$ 0,00090/GPU-s | energia é ≤ 0,04% do custo marginal; erro de 15× (B02, D03) |
| Vigência bitemporal | Tri-temporal (vigência × eficácia × transação) | CF art. 62 §11, Lei 9.868 arts. 27 e 11 §2º são insolúveis com dois eixos (A03) |
| Rede social = perfis/posts/reputação | Mercado de Procedência com Alegação Comprometida | nenhuma IA gasta tokens por "comunidade"; gasta por valor de informação (B07) |
| "MoE de LoRAs" (X-LoRA) | S-LoRA + roteador discreto | X-LoRA: +0,015 nats, p = 0,19 (D04) |
| PPR por power iteration | Forward push local (Andersen–Chung–Lang) | 301M arestas × 30 iterações = 180 s contra 30 ms (C02) |
| Wan 2.2 / XTTS-v2 / DocLayout-YOLO / LayoutLMv3 / Granite-Docling | LTX-Video 2B / Kokoro+Chatterbox / PP-DocLayout-L / PaddleOCR-VL + MinerU2.5-Pro-2605 | 24 GB exigidos; Coqui encerrou; AGPL/CC-NC; inglês-primário (C07, E04) |
| Res. CNJ 332/2020 | Res. CNJ 615/2025 (alt. 674/2026) | 332 revogada pelo art. 46 da 615 (B05, E04) |
| RAM 32 → 96 GB "quando a fila não fechar" | 96 GB no dia 0 | desenho pede 60,60 GB residentes (E02) |
| "X% da receita → hardware" | ADP com colchão, hurdle, payback, quarter-Kelly | política de índice, não regra fixa (B02) |
| Recibo "JCS → SHA-256 → Ed25519", raiz diária | Assina bytes JCS diretamente; log contínuo MMD 60 s; COSE/SCITT | Ed25519 já hasheia; raiz diária é grosseira (B06) |
| Nenhum benchmark especificado | WikiJurídica-Bench: 2.700 itens, 8+1 trilhas, G1–G5 | contrato de qualidade do projeto (A06) |
| Sem arquitetura de agente | Grafo Eino com Interrupt/Resume, memória em 5 camadas, 3 planos | o v2 descrevia um modelo, não um agente (A01, B04) |

## 0.4 As 24 decisões-chave do v3

1. **Dois planos físicos de conteúdo (edge, 100% cacheável) e inferência (GPU)** — mantido — **mais três planos físicos de segurança** (D lê, C decide com tipos, T gasta sem LLM).
2. **Bot = Qwen3-8B NVFP4 residente + Qwen3-4B destilado com trie de ⟨URN⟩ + Gemma-4-26B-A4B EXL3 sob demanda + BitNet na CPU.** Matriz de compute por capacidade fechada.
3. **Um verificador, V⁴** (`wj-nli-54M`, τ = 0,906, E7 relevância obrigatória): portão de runtime, produto, recompensa e gerador de teste. Fail-closed no serializador e no banco.
4. **Vigência tri-temporal** com totalidade provada, consolidação adversarial D0–D3, aresta INTERPRETA@sha, `/norma?em=` como função pura (`Cache-Control: immutable`), Merkle contínuo.
5. **Recuperação fail-closed em três camadas** (léxico, denso, late-interaction próprio), chunking hierárquico com contextualização determinística, roteador de fusão por classe (+7,6%), PPR por forward push (6,7 ms), t_max = 4, Retrieval Receipt.
6. **Grafo com ontologias reusadas** (LRMoo, LKIF time-modification, UFO-L, TPU/CNJ, Akoma Ntoso); 40,6M nós / 301M arestas; zero LLM na indexação (36.522×); apelido = f(string, data); contradição materializada.
7. **Direito-como-código:** a fronteira é a classe do token; 4 ferramentas MCP em 50 ms e 0 GPU; intervalo nominal/estrito; `big.Rat`; tabela de correção contra a Fazenda marcada `Instavel` (ADI 7.873).
8. **Pós-treino GSPO-DrC** com recompensa cujo invariante torna alucinação negativa; vigência como penalidade assimétrica; quarentena de 30 dias antes de tocar peso; replay retemporalizado 25%; knowledge editing proibido.
9. **Serving contínuo 24/7 co-residente** com preempção latchada (TLA+), cache semântico com morte por vigência, prefix caching como condição de viabilidade, KV de 124.830 tokens.
10. **Algoritmo vivo:** função objetivo J em R$/dia, κ = 49 derivado, risco como restrição; λ_gpu único; currículo por p̂ ∈ [0,20; 0,70]; anticolapso ρ_real ≥ 0,30; autonomia L0–L5 com tesouraria em teto L3; painel de 8 números com Θ_frozen.
11. **WikiJurídica-Bench:** 2.700 itens, 7 trilhas programáticas + peça + negociação, G1–G5 conjuntivos no artefato quantizado, N_real = 1,07×N_Connor, BCa clusterizado, canário semântico.
12. **World model:** 15 macro-eventos, H(k=3) = 1,326 bit, kernel 58×15 de 17,4 MB, MCTS em 12 ms de CPU, auto-jogo de ~19.700 trajetórias/dia, Simulation Receipt, contrafactual só intervencional.
13. **Catálogo M2M de 9 produtos**, só 3 tocam GPU; schemas MCP `wj_*` token-eficientes; onboarding sem humano em três trilhos de descoberta.
14. **Protocolo:** MCP rev. 2026-07-28 / go-sdk v1.8.0; A2A v1.0 só agente↔agente com estado; Web Bot Auth (IETF WG); RSL 1.0; TollBit/ai.txt descartados.
15. **Pagamento:** x402 self-hosted Go v2.26.0 primário; L402/Aperture secundário; AP2/ACP como adaptadores sob demanda.
16. **Negociação:** SAOP t_max = 6, MiCRO contra não-estacado, posted price + bandit para avulso, número nunca sai do LLM (`nego/core ↛ nego/llm` no CI), stake = externalidade informacional.
17. **Tesouraria ADP** (colchão 6 meses, hurdle 0,9150%/mês, payback ≤ 18 m, quarter-Kelly); ledger de dupla entrada com 4 furos fechados; PJ emissora; LC 123 §14; USDC em D+0.
18. **Confiança:** did:web + DNSSEC, Shamir 3-de-5, COSE/SCITT, Merkle MMD 60 s, verificador zero-deps (172 µs), MeritRank α = 0,40/β = 0,60, garantia 100× sobre propriedades criptográficas.
19. **Compliance como código:** Cedar com veto, 17 políticas, anonimização NER+regex com prova, `allow_key` GENERATED, Atestado de Conformidade Verificável vendável, canário de compliance.
20. **Rede de IAs = Mercado de Procedência:** Alegação Comprometida, pago = b·(1−Brier), mistura bayesiana ln N, moot court prospectivo (CPC 357 + TPU), terminalidade oficial, Nostr.
21. **Padrão aberto:** 3 Internet-Drafts prontos; SCITT pelo WG, Legal-Time pelo ISE (como a RFC 9676); cutoff 02/11/2026; gancho Res. 615 art. 2º IX.
22. **Crescimento re-ancorado:** ≥ 1.150 → 100k citações/dia no dia ~168 (piso); crawls (6.086/dia) e humanos como canais próprios; sem teto; expansão pelo mesmo motor.
23. **Invariantes:** 24 catalogados, 19 em tipo/constraint/prova; FK composta como prova de pertinência; schema consolidado testado (28 ataques, 28 recusas); 2 specs TLA+.
24. **Execução em sessões:** ~151 sessões/365 dias; Fase 0 de 14 dias sem GPU; verificador antes da geração em massa; 4/10/6/2 h/semana de Rafael; primeira semana hora a hora.

## 0.5 Números canônicos

| Grandeza | Valor | Fonte |
|---|---|---|
| Citações por IAs (baseline) | ≥ 1.150/dia (23k em < 20 dias) | dono |
| Leituras verificadas de bots de IA | 6.086/dia (42.601 em 7 dias) | radar da plataforma |
| Acervo | 11.106 páginas | llms.txt |
| Meta | 100.000 citações/dia = ~87× | dono |
| Dia em que 100k/dia é cruzado (piso) | ~168 | E03 re-ancorado |
| GPU disponível / demandada | 86.400 / 38.539 GPU-s/dia (folga 55,4%) | E02 |
| Capacidade simultânea em regime | 11.600 chamadas pagas + 2.000 units + 1,66 GPU-noites de treino por dia | E02 |
| VRAM residente / KV / folga | 8B NVFP4 + auxiliares / 5,00 GB = 124.830 tokens / 0,69 GB | E02 |
| λ_gpu | R$ 0,00090/GPU-s (R$ 3,24/GPU-h) | D03 |
| Energia | R$ 1,27125/kWh (Light, ANEEL REH 3.571/2026) → R$ 0,000060/GPU-s | B02 |
| Custo fixo / break-even | R$ 1.199,26/mês / 5.034 `/verify`/dia ou 1 knowledge pack | B02 |
| Piso `/verify` | R$ 0,00135/chamada | B01 |
| τ_NLI / HCR / ASR | 0,906 / ≤ 2% / 0 | A02, A06 |
| κ (peso da refutação em J) | 49 = (1−HCR_max)/HCR_max | D03 |
| Bench | 2.700 itens, N = 498 pares por trilha (δ = 5 pp) | A06 |
| Grafo | 40,6M nós / 301,4M arestas; PPR 6,7 ms | C02 |
| Corpus | 1.085 GB (27,1% do NVMe) | E02 |
| Entropia do processo civil | 1,326 bit/macro-evento (k = 3) | D06 |
| Verificador de recibo | 472 linhas Go, 0 deps, 172 µs | B06 |
| Direito-como-código | 4.626 linhas Go, 0 deps, 50 ms, 0 GPU | C03 |
| RAM | 96 GB no dia 0 | E02 |
| Esforço | ~151 sessões de Claude Code / 365 dias; Rafael 4/10/6/2 h/semana | E08 |

## 0.6 O que nenhuma plataforma tem

- **Trie de ⟨URN⟩ no decoder** — citação inventada impossível por construção, filtrada pela data de referência.
- **Tri-temporalidade com prova** e **aresta INTERPRETA@sha** — o acórdão de 2023 fica preso à redação de 2017 que interpretou.
- **Apelido normativo como função de (string, data)** — todo normalizador publicado erra em silêncio sobre trinta anos de acervo.
- **Cache, adaptador e crença que morrem por vigência** — revogação normativa invalida resposta, peso e memória.
- **WJ-Retro auto-alimentado** — a mudança da lei gera o teste que protege o modelo, custo humano zero.
- **Recibo de citação verificável offline por terceiro** (COSE/SCITT, 172 µs) — Lexis+/Westlaw/Practical Law medem 17%/33%/22% de alucinação e ninguém emite recibo.
- **Métrica de alucinação com denominador publicado** — a taxa medida reflete a cobertura do índice; publicamos a nossa.
- **Painel selado com cota auditável no Merkle** — "o sistema melhorou" vira afirmação verificável externamente.
- **Preço-sombra único** que decide conteúdo, treino, aluguel de GPU e compra de hardware no mesmo leilão.
- **Prova de solvência verificável por máquina** — ledger assinado com a chave dos recibos.
- **Mercado de Procedência** com moot court prospectivo por construção e Índice de Sofisma.
- **Prediction Receipt / Simulation Receipt** — a previsão e o plano entram no Merkle antes do movimento existir; `skill_vs_baserate` obrigatório no contrato mata o teatro de acurácia.
- **Intervalo nominal/estrito de prazo** ("protocole até o estrito") e **trilha negativa de competência**.
- **Gatilho de scraping por movimento do DataJud** — O(quem teve decisão hoje), não O(todos os processos).
- **Kernel 58×15 do processo civil** — a primeira medição publicada da entropia do processo judicial brasileiro.
- **FK composta como prova de pertinência** — estados inválidos irrepresentáveis no banco, não proibidos por convenção.
- **Feed de Invalidação, Selo de Citação Verificada na peça, Detector de Golpe Jurídico, Semáforo de Redação, Atestado de Conformidade Verificável, Reward-as-a-Service, `/oracle/clausula`, seguro de citação** — os oito produtos escolhidos entre quarenta.

## 0.7 Como ler

- **Parte I — O Bot** (14 seções): núcleo cognitivo, modelo, memória, recuperação, vigência, verificador, serving, aprendizado, world model, algoritmo vivo, bench.
- **Parte II — A Plataforma Viva** (13 seções): o que as IAs globais fazem aqui, catálogo M2M, protocolos, pagamento e negociação, tesouraria, confiança, segurança, compliance, rede de IAs, padrão aberto, ciência, brainstorm.
- **Parte III — Execução** (16 seções): arquitetura de referência, fontes, grafo, direito-como-código, jurimetria, multimodal, plataforma de engenharia, orçamento 24/7, topologia, console, invariantes, crescimento, posicionamento, red team resolvido, plano de execução com a primeira semana hora a hora.

Cada subseção segue **Decisão fechada → Mecanismo → Números → (Por que ninguém tem) → Origem**. As linhas `supera:` registram o que o CANON substituiu.

## 0.8 Artefatos já produzidos (entram no repositório)

| Artefato | Caminho | O que é |
|---|---|---|
| Motor determinístico | `research/C03-code/` | 4.626 linhas Go, 6 pacotes, 0 deps, testes (prazos, competência, correção, validadores) |
| Schema consolidado | `research/E07-arquitetura/schema.sql` + `ataques.sql` | DDL de todos os subsistemas com invariantes; 28 ataques recusados em PG 16.13 |
| Arquitetura | `research/E07-arquitetura/arquitetura.html` | 9 camadas, 8 SVG, planos de segurança, caminhos de requisição |
| Regras de dependência | `research/E07-arquitetura/deps.yml` + `depcheck.go` | 25 pacotes, 6 camadas, checker transitivo |
| Console do engenheiro-chefe | `research/D08-console/index.html` | 76 KB autocontido, 3 modos, fila de decisão, pânico |
| Tipos, TLA+, invariantes | `research/D10-code/` | 6 tipos Go, 2 specs TLA+, SQL de invariantes, property tests |
| Orçamento e escalonador | `research/E02-code/` | `orcamento.py`, `EscalonadorContinuo.tla` (1.936 estados, 0 erros) |
| Internet-Drafts | `research/E01-drafts/` | 3 drafts kramdown-rfc → xml2rfc, 0 warnings, 18 vetores |
| Verificador de recibo | `research/B06-code/lar.go` | 472 linhas, 0 deps, 172 µs |
| Modelo financeiro | `research/B02-modelo-financeiro.py` | 24 meses × 3 cenários, ledger testado |
| Medições de tokenizer | `research/D04-code/` | fertilidade em 2,4 MB de texto legal real |
| Entropia do processo | `research/D06-code/entropia_movimentos.py` | 3.166 processos, 63.366 movimentos |
| Crescimento re-ancorado | `blueprint/codigo/crescimento_reancorado.py` | 7 fatores, 3 canais, 12 meses |
| Checklist executável | `research/E08-plano/checklist.md` | 105 caixas, primeira semana hora a hora |
| Relatórios de origem | `research/A01…E08` | 41 relatórios, ~153.000 palavras |

## 0.9 Método e verificação

Seis ondas: núcleo cognitivo (8), autonomia e economia (8), dados e direito-como-código (8), red team e arquitetura própria (10, um interrompido), reconciliação e execução (8), síntese (3). Cada agente trabalhou com fontes primárias (arXiv API, GitHub, HuggingFace, proxy.golang.org, gov.br, APIs do CNJ/STJ/CVM/BCB/IBGE consultadas ao vivo) e marcou o não verificado. A auditoria E04 conferiu 295 IDs de arXiv (todos existem, títulos compatíveis, inclusive os 102 de 2026), reproduziu números dígito a dígito na fonte e corrigiu 15 pins de versão e licença — nenhuma fonte inventada. O red team D01 atacou a soma dos 24 primeiros relatórios; suas dez correções estão fechadas em E02, E04, E07 e E08 (Parte III.14). Dois model checkers (TLC) acharam três defeitos reais em desenhos anteriores; todos corrigidos e reverificados. O que resta como estimativa está marcado `[est.]` no relatório de origem.

---


# BLUEPRINT v3 — PARTE I · O BOT PRÓPRIO DA PLATAFORMA

Wiki Jurídica IA-First · 22/09/2026 · Autoridade: `CORRECOES-DONO.md` > `CANON.md` > E04 > E02/E07 > demais relatórios.
Onde um relatório de origem diverge do CANON, a linha **supera:** registra o que ele dizia; o número desta Parte é o que se constrói.

Convenções: GPU-s = segundo de uma RTX 5060 Ti 16 GB; orçamento = 86.400 GPU-s/dia (24/7, sem janela noturna). λ_gpu = R$0,00090/GPU-s. τ = 0,906. "[derivado]" = conta feita nesta Parte sobre números canônicos; "[est.]" = estimativa herdada do relatório de origem.

---

## I.1 Tese do bot: pequeno, adaptado, verificável

### I.1.1 Por que um 4–8B especializado com scaffolding vence o generalista grande neste domínio

**Decisão fechada.** O bot é um Qwen3-8B denso residente, um aluno de ~4B destilado para volume, um professor Gemma-4-26B-A4B sob demanda e um BitNet-b1.58-2B-4T 24/7 na CPU — envolvidos por verificador determinístico, recuperação tri-temporal e código para tudo que é calculável. Nenhum valor numérico, URN ou data sai de peso de modelo.

**Mecanismo.** A vantagem é estrutural e vem de cinco alavancas que o generalista não tem:
1. **Cascata decidida pelo verificador, não pela confiança do LLM.** O modelo pequeno falha na autodetecção de erro em ~95% das instruções ambíguas (ACEBench); quem manda escalar é o V⁴.
2. **Valor vem de código.** O erro dominante do modelo pequeno é valor de parâmetro (59–66% dos erros, ACEBench): prazo e cálculo saem do C03, texto de dispositivo do motor tri-temporal, e a gramática proíbe dígito em prosa.
3. **Destilação agêntica ultrapassa o professor.** Aluno 7B agente-destilado (42,6%) supera o professor 32B em CoT (39,54%) com 2.000 trajetórias; Lawma: modelos pequenos ajustados superam GPT-4.5 e Claude 3.7 Sonnet em 260 tarefas jurídicas.
4. **O generalista forte é pior no problema central do direito BR.** arXiv:2608.14610 mede que LLMs aplicam por viés a lei mais recente e que raciocínio mais forte **erra mais** a lei aplicável. O bot resolve vigência em código tri-temporal e treina contra o viés (penalidade −0,60, I.8.4).
5. **O custo do domínio está na estrutura.** URN LexML = 33 tokens; nº CNJ = 25 tokens para 25 caracteres — daí vocabulário próprio e trie de ⟨URN⟩ (I.7).

**Números.** FAMA: Qwen3-4B de 30% → 37,6% no τ-bench só com scaffolding; ToolRL +17 pp; gramática +4 pp e 92–98% de compliance; on-policy distillation: AIME'24 74,4% com ~1.800 GPU-h contra 67,6% com RL de 17.920 GPU-h. Incumbentes alucinam 17%–33% (Magesh et al.); piso do bot: HCR ≤ 2%. Entrada: ≥ 1.150 citações/dia com a IA atual em CPU, 6.086 leituras de crawler/dia, 11.106 páginas; alvo 100.000/dia (~87×): o bot multiplica o rendimento por página (0,10 → 9/dia) sobre a camada já no ar (`/mcp` com 15 tools, `/api/v1/citacoes` = `/verify`).

**Por que ninguém tem.** Legaltechs servem modelo grande + RAG com checagem pós-hoc. Nenhuma torna a citação inventada inexprimível ao mesmo tempo no decoder (trie), no banco (FK composta) e na recompensa (invariante negativo).

**Origem:** A08 D1–D6 e Números; D04; D05 §2; A06 (Magesh); CANON.

### I.1.2 Matriz de compute por capacidade

**Decisão fechada.** Cada capacidade tem um tier fixo. A escalada entre tiers é decidida pelo V⁴ e pelo roteador conformal (I.10.3), nunca por autoavaliação do modelo.

**Mecanismo.**

| Capacidade | Tier | Onde roda | Regra dura |
|---|---|---|---|
| VERIFICAR (gate, `/verify`) | wj-nli-54M + resolvedores Go | CPU, ONNX int8 (hugot v0.7.8) | 16 ms/par/núcleo, 0 GPU-s |
| MONITORAR, classificar ramo, watchdog | BitNet-b1.58-2B-4T (bitnet.cpp) | CPU 24/7 | sobe ao 8B só em ambiguidade |
| CALCULAR (prazo, correção, competência) | C03 em Go (big.Rat) | CPU / edge Wasm | 50 ms, 0 GPU |
| SIMULAR processo | kernel 58×15 + MCTS | CPU | 12 ms por plano |
| CITAR, T1, M2M de 3 s | aluno ~4B NVFP4 + trie ⟨URN⟩ + xgrammar | GPU, fast path | até o 4B passar G1–G5: Qwen3-1.7B NVFP4 (0,95 GB) |
| RESPONDER (T2), PUBLICAR answer unit | Qwen3-8B NVFP4 + RAG + S-LoRA | GPU residente | 5,507 GPU-s/unit (3,059 no 4B) |
| Escalada T2–T4, professor | Gemma-4-26B-A4B EXL3 ~3,2 bpw | GPU sob demanda | 10,4 GB, SLA 30 s, nunca M2M |
| NEGOCIAR | `nego/core` (preço em código) + fast path narra | CPU + GPU | ≤ 60 tokens, leash 2,2 s, nunca escala |
| OPERAR CAIXA | Plano-T em Go | CPU | LLM só narra; teto de autonomia L3 |

supera: A08 cascateava NEGOCIAR para um 32B; T5 tem 3 s hard e o número sai do `nego/core` (B01) — não escala.
supera: D01 #7 tirava o BitNet (monitor 110M ONNX); o CANON mantém BitNet para monitor, ramo e watchdog; o 110M ONNX fica como NER.

**Números.** Em regime, GPU a 44,6% de 86.400 GPU-s/dia e CPU a 32,4% de 691.200 núcleo-s/dia (5,41 núcleos livres permanentes).

**Origem:** A08 §6; E02 §1/§4; C03; D06; CANON.

---

## I.2 Arquitetura do agente

### I.2.1 Grafo Eino e máquina de estados

**Decisão fechada.** Runtime = CloudWeGo Eino v0.9.19 (Go, Apache-2.0): `compose.Graph` para o pipeline determinístico, `adk` só para o painel. Checkpoint em Postgres (`CheckPointStore`), assíncrono em River, Python só como sidecar de serving e treino.

**Mecanismo.** Máquina de estados explícita, guardas numéricas:

```
S0 INGEST → S1 PLAN → S2 GROUND → S3 ACT → S4 CRITIC → S5 VERIFY → S7 EMIT → S8 LEARN (River, assíncrono)
                ↑ replan (V<0,60)                 ↓ p_ok<0,70     ↓ 0,60≤V<0,90       ↓ falha dura / budget
                └──────────────────────────── S6 REPAIR (≤2) ─────────┘             S9 ESCALATE (parcial + coverage)
```

Guardas: `len(plan) ≤ 12`; S2 exige `unresolved_urn == 0`; S3 faz retry 250 ms·2ⁿ ±20% (máx. 3). Regra *anytime*: estourou o orçamento ⇒ emite o melhor sub-resultado verificado com `coverage = claims_verificados/claims_totais`.

```go
func BuildCore(v Verifier, wm WorldModel, m Memory) (compose.Runnable[*Envelope, *Envelope], error) {
	g := compose.NewGraph[*Envelope, *Envelope]()
	_ = g.AddLambdaNode("plan", compose.InvokableLambda(planFn))
	_ = g.AddLambdaNode("ground", compose.InvokableLambda(groundFn(wm))) // disp_versao em T_fato
	_ = g.AddLambdaNode("act", compose.InvokableLambda(actFn))           // tools com breaker
	_ = g.AddLambdaNode("critic", compose.InvokableLambda(criticFn))     // 4B
	_ = g.AddLambdaNode("verify", compose.InvokableLambda(verifyFn(v)))  // wj/verify
	_ = g.AddLambdaNode("repair", compose.InvokableLambda(repairFn))
	_ = g.AddLambdaNode("emit", compose.InvokableLambda(emitFn))         // serializador fail-closed
	_ = g.AddEdge(compose.START, "plan"); _ = g.AddEdge("plan", "ground")
	_ = g.AddEdge("ground", "act"); _ = g.AddEdge("act", "critic")
	_ = g.AddBranch("critic", compose.NewGraphBranch(func(_ context.Context, e *Envelope) (string, error) {
		if e.Critic.POk < 0.70 && e.Repairs < 2 { return "repair", nil }
		return "verify", nil
	}, map[string]bool{"repair": true, "verify": true}))
	_ = g.AddBranch("verify", compose.NewGraphBranch(func(_ context.Context, e *Envelope) (string, error) {
		switch {
		case !e.Budget.Spend(1, 0, 0, 0):          return "emit", nil // anytime
		case e.Verdict.V >= 0.90:                  return "emit", nil
		case e.Verdict.V >= 0.60 && e.Repairs < 2: return "repair", nil
		default:                                   return "plan", nil // replan
		}
	}, map[string]bool{"emit": true, "repair": true, "plan": true}))
	_ = g.AddEdge("repair", "act"); _ = g.AddEdge("emit", compose.END)
	return g.Compile(context.Background(), compose.WithMaxRunSteps(48))
}
```

Anti-loop: `StateHash = xxh3(nodeID ‖ tool ‖ argsCanonical)`; 3 iguais seguidos ⇒ `BreakLoop` + replan; 2 replans ⇒ S9. Checkpoint assinado (HMAC por trace), `args` revalidados no resume. `Verifier`, `WorldModel` e `Memory` são interfaces do domínio: o Eino só aparece em `BuildCore`/`BuildPanel`.

**Números.** 48 passos máximos; repairs ≤ 2; replans ≤ 2.

**Origem:** A01 D1–D2, §1–2; E04 A.3 (eino v0.9.19, hugot v0.7.8).

### I.2.2 Orçamento first-class e circuit breakers

**Decisão fechada.** `Budget{Steps, Tokens, Wall, MicroBRL}` viaja no envelope e todo nó debita. Três níveis de breaker, e auto-fissão de sessão quando o ganho por token estagna.

**Mecanismo.**

| Classe | Steps | Tokens | Wall p95 | Painel |
|---|---|---|---|---|
| T1 lookup/citação | 3 | 4k | 8 s | não |
| T2 resposta analítica | 8 | 16k | 45 s | gate |
| T3 painel cross-domínio | 24 | 60k | 180 s | sim |
| T4 peça, gerada por seção | 40 | 120k | 600 s | sim |
| T5 M2M/negociação | 6 | 8k | **3 s hard** | não |
| T6 pré-computação | — | 2M/dia | classe 2, contínua | não |

supera: A01 punha T6 na janela 02–06 h; não existe janela (CORREÇÕES §2) — T6 roda 24/7 na classe 2, abaixo das answer units.

Breakers: (i) por ferramenta — abre com 5 falhas/60 s ou p95 > 3× a base, meio-aberto após 30 s; (ii) de gasto por classe — corta T3/T4 antes de T1/T5; (iii) anti-loop. Auto-fissão: a 60% do orçamento de T3/T4 sem ΔV ≥ 0,05, fecha a sessão e abre 3 curtas paralelas agregadas pelo V⁴ (+355 vs +264 Elo, arXiv:2609.15309).

**Números.** Advogado com recuperação + verificação + cálculo = 10,87 s contra 45 s (TTFT percebido 584 ms); `/verify` + x402 = 109,9 ms contra os 3 s de T5.

**Origem:** A01 §6; E07 (quatro caminhos); A05 Tab. 8 (arXiv:2601.09527).

### I.2.3 Painel de personas gated

**Decisão fechada.** O default é agente único + V⁴. O painel abre só por gate numérico, com supervisor centralizado, no máximo 2 rodadas, mensagens tipadas e agregação determinística em Go; compliance é decisão Cedar com veto, não voto.

**Mecanismo.** Gate: abre ⟺ `H_calibrada ≥ 0,45` ∨ `|R| ≥ 2` ∨ `stake ∈ {peça, parecer}`; nunca em T1, T5 ou planejamento sequencial. Roteador de papel = classificador multirrótulo ONNX, `p_r ≥ 0,50`. Caminho barato padrão: MoRe (steering de papel no espaço de ativação, 20× menos tokens). Protocolo colaborativo ColMAD; mensagem = `{claim, urn, anchor, entail, confidence}`, nunca prosa. Agregação: (1) Cedar Deny bloqueia; (2) claim sem resolução ou fora de vigência cai mesmo unânime; (3) disputa no mesmo URN ⇒ vence o maior `w = entail·resolved·vigência_ok`, e com Δw < 0,10 as duas posições saem com divergência explícita; (4) aritmética é do C03. Papéis são adaptadores S-LoRA r = 16 carregados sob demanda.

supera: A01 fazia compliance como LoRA; compliance é Cedar (cedar-go v1.8.0, 17 políticas).

**Números.** Multi-agente degrada acima de ~45% de baseline e −39% a −70% em planejamento sequencial; supervisor centralizado amplifica erro 4,4× contra 17,2×.

**Origem:** A01 D3, §4; D01 Frente 5; E02 §4; CANON.

### I.2.4 Erro observável E1–E7 e o escore V

**Decisão fechada.** Sete detectores determinísticos com código fixo alimentam V. E7 é relevância obrigatória. A refutação externa tardia é o sinal **RX**, fora de V.

**Mecanismo.**

| Código | Detector (binário, salvo E3) | Implementação |
|---|---|---|
| E1 | URN não resolve | resolvedor Postgres / trie |
| E2 | âncora ou trecho inexistente na redação vigente em T_fato | `disp_versao` + `span_sha256` |
| E3 | `entail(claim, span) < τ = 0,906` (contínuo) | wj-nli-54M |
| E4 | redação fora de vigência/eficácia em T_fato | motor tri-temporal |
| E5 | divergência do motor determinístico | C03 |
| E6 | contradição com `mem_fact` de `c_score ≥ 0,8` | NLI de contradição |
| E7 | URN ∉ top-k do retriever para a consulta | recuperação (I.4) |

```
V = 1 − (0,30·max(E1,E7) + 0,25·E4 + 0,20·E2 + 0,15·(1 − ē) + 0,10·E5) ;   E6 ⇒ V ← min(V, 0,55)
V ≥ 0,90 emite · 0,60 ≤ V < 0,90 repara · V < 0,60 replaneja
```

E7 herda o peso de E1 (URN irrelevante não resolve a pergunta de quem consome); o `max` mantém a soma dos pesos em 1. RX (`/verify` negativo de terceiro, correção humana) chega depois: entra no contador de J com κ = 49, retrata a crença e vira caso congelado.

supera: A01 usava E3 com 0,85 e E7 como sinal tardio; D03/E08 escreviam κ·|E7| para a refutação; C07 usava E7 para OCR — E7 é relevância (CANON/E07), a refutação é RX, OCR de baixa confiança é erro da ingestão.

**Números.** 0,55 do peso está em detectores binários (E1/E7, E4); o NLI pesa 0,15 e nunca decide sozinho.

**Origem:** A01 §5; E07 D1; D01 Frente 4 #4.

### I.2.5 Loop de auto-melhoria

**Decisão fechada.** Todo episódio com V < 0,90 vira caso congelado cuja expectativa é a **restrição verificável**, nunca o texto; o caso entra no bench como regressão permanente e no RLVR como item. Scaffolding (Σ) muda todo dia; pesos (θ) mudam no ciclo mensal com portões.

**Mecanismo.** Caso = `{query_sha256, T_fato, restrição}` ("URN X resolve", "prazo = 15 dias úteis"); conjunto append-only, e só o verificador cria caso. Σ: deltas de playbook no padrão ACE, nunca reescrita integral, e novas skills em `mem_skill`. θ: I.9; qual hipótese testar e promover decide o ciclo de J (I.12).

supera: A01 fazia θ semanal com ganho ≥ +1,5 pp; D05 fixa ciclo mensal, quarentena de 30 dias e G1–G5 no artefato quantizado.

**Números.** Verificação agêntica: +19,7 pp de recall em citação falsa (LePhantomCite).

**Por que ninguém tem.** O erro de ontem é o teste e o dado de treino de hoje, sem curadoria humana, porque o mesmo artefato é portão, produto, recompensa e gerador de teste (V⁴, I.6).

**Origem:** A01 §5, Inov. 1; D05 D3; A06.

---

## I.3 Memória em camadas

### I.3.1 Cinco camadas; `mem_fact` inalcançável sem recibo

**Decisão fechada.** L0 working, L1 episódica, L2 semântica, L3 procedural, L4 grafo — todas no mesmo Postgres. `mem_fact` exige `receipt_id NOT NULL`, `ver_id NOT NULL` e `entail ≥ 0,906`: a memória de longo prazo não consegue conter alucinação, por integridade referencial.

**Mecanismo.** L0 guarda só `prefix_key` do prefix cache do vLLM; L1 `mem_episode` guarda consulta, embedding (DiskANN), outcome, `v_score`, `n_hits`, `n_success`; L3 `mem_skill` guarda DAG tipado indexado pelo embedding do **resumo**; L4 é o grafo AGE. L2:

```sql
CREATE TABLE mem_fact (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  subject_urn text NOT NULL, predicate text NOT NULL,
  object_text text NOT NULL, object_urn text,
  emb         vector(1024) NOT NULL,
  ver_id      uuid NOT NULL REFERENCES disp_versao(ver_id),       -- I-MEM-1: aponta a REDAÇÃO
  receipt_id  uuid NOT NULL REFERENCES citation_receipt(id),     -- sem recibo, não existe
  belief_from timestamptz NOT NULL DEFAULT now(), belief_to timestamptz,
  entail      real NOT NULL CHECK (entail >= 0.906),             -- mesmo τ do verificador
  support     int  NOT NULL DEFAULT 1 CHECK (support >= 1),
  c_score     real NOT NULL,
  CHECK (belief_to IS NULL OR belief_to > belief_from));
-- mem_skill: p_success real GENERATED ALWAYS AS ((n_ok + 2.0)/(n_used + 4.0)) STORED
```

supera: A01 dava a `mem_fact` linha do tempo própria (`valid_from/valid_to`) — segunda verdade de vigência; E07 troca por `ver_id` e a vigência vem por junção com `disp_versao`.

**Números.** Embedding de resumo perde só −11,0% de MAP fora de distribuição (−29,9% no combinado); memória falsa em 3 camadas = 5,1% — com o cadeado do recibo o alvo é < 1%.

**Origem:** A01 §3; E07 `schema.sql` (I-MEM-1).

### I.3.2 Consolidação, esquecimento, retratação — bitemporalidade de crença

**Decisão fechada.** Consolidar é fórmula, não juízo. Retratação é assinada e se propaga a todo episódio que usou o fato.

**Mecanismo.**

```
C = 0,35·min(1, n_hits/5) + 0,35·n_success/max(1, n_hits) + 0,20·entail + 0,10·e^(−τ_dias/90)

L1 → L2  ⟺ C ≥ 0,62 ∧ n_hits ≥ 3 ∧ n_success/n_hits ≥ 0,80 ∧ entail ≥ 0,906 ∧ receipt_id NOT NULL
L2 → L4  ⟺ subject_urn e object_urn resolvem ⇒ aresta AGE amarrada ao ver_id
tombstone ⟺ C < 0,15 ∧ τ > 60 d        (hard-delete só após 365 d, auditoria LGPD)
retrata   ⟺ E4 ∨ E6 ∨ RX contra o fato ⇒ belief_to = now() + invalidação dos episódios dependentes
```

"O que o bot afirmou em T, sobre qual redação":

```sql
SELECT f.predicate, f.object_text, dv.vigencia, dv.eficacia, f.receipt_id
  FROM mem_fact f JOIN disp_versao dv USING (ver_id)
 WHERE f.subject_urn = $1 AND f.belief_from <= $2 AND (f.belief_to IS NULL OR f.belief_to > $2);
```

supera: A01 promovia com entail ≥ 0,85; o τ único é 0,906.

**Números.** Mem0: −91% de p95 e −90% de tokens.

**Por que ninguém tem.** Vigência da norma (herdada por `ver_id`) × vigência da crença (`belief_from/to`) responde "o que a lei dizia em T" **e** "o que eu afirmei em T e por quê" — retratação auditável que concorrente não retroage.

**Origem:** A01 §3, Inov. 2–3; E07.

### I.3.3 Pré-computação contínua ponderada por receita (sleep-time compute)

**Decisão fechada.** A reescrita de contexto c → c′ roda 24/7 na classe 2 do engine vLLM, abaixo das answer units; a fila é ordenada pela receita M2M esperada por URN e cortada pelo mesmo λ_gpu do leilão (I.12.2).

**Mecanismo.** Candidatos: prefixo CAG e contexto pré-resolvido de URNs quentes; executa u ⟺ `W_u = v_u·(1 − e^(−λ_u·Δt_u))/c_u ≥ λ_gpu`, com `v_u` = receita x402/MCP/feed atribuída à URN, em R$.

supera: A01 e D05 usavam janela 02–06 h; não existe janela (CORREÇÕES §2).

**Números.** Sleep-time compute: −5× de tokens em test-time para a mesma acurácia e −2,5× de custo por consulta amortizado. 28.800 GPU-s custam R$25,92 de oportunidade contra R$1,73 de energia — o corte é λ_gpu.

**Por que ninguém tem.** Consolidação de memória vira alocação de capital: GPU ociosa vai para onde as IAs globais pagam.

**Origem:** A01 §3, Inov. 4; D03 Números; E02.

### I.3.4 O que sobe para os pesos, e quando

**Decisão fechada.** `mem_fact` nunca sobe para peso — é valor datado e mora na recuperação. Sobe só **forma**: skills de `mem_skill` e o formato de trajetórias bem-sucedidas, no ciclo mensal.

**Mecanismo.** `promove(skill) ⟺ n_used ≥ 50 ∧ p_success ≥ 0,90 ∧ ¬deprecated ∧ sobreviveu ≥ 2 ciclos mensais ∧ trajetória redigida` (calculável → placeholder de tool; URN → retorno de tool). A skill promovida fica em `mem_skill` como fallback: se o merge reprovar no G5, a capacidade continua existindo.

**Números.** LoRA perturba posto 10–100× menor que FT completo — forma tem posto intrínseco baixo.

**Origem:** D05 §7, D1.

---

## I.4 Recuperação e grounding fail-closed

### I.4.1 Pipeline e índice em três camadas

**Decisão fechada.** BM25 sobre 100% do corpus; denso (Qwen3-Embedding-0.6B, MRL-512 int8, RaBitQ) sobre ementa + dispositivo; ColBERT-JUR + `jua-4B-mixed` só no tier-1 (legislação, súmulas, STF/STJ, repetitivos). Encoders e classificadores ≤ 0,6B rodam em Go/ONNX na CPU; só o reranker 0,6B fica na GPU.

**Mecanismo.**

| Estágio | Runtime | p95 |
|---|---|---|
| parse + NER de URN + classe da consulta | Go, hugot ONNX int8 | 8 ms |
| BM25 top-400 | `vchord_bm25` + `pg_tokenizer` | 25 ms |
| denso top-400 | `vchordrq` RaBitQ, MRL-512 int8 | 20 ms |
| PPR (só classe RACIOCÍNIO) | Go, forward push em CSR | 6,7 ms |
| RRF ponderado + dedup por URN | SQL | 3 ms |
| maxsim ColBERT-JUR top-200 (tier-1) | Go, NVMe | 45 ms |
| LambdaMART → top-20 | `leaves` | 0,3 ms |
| reranker Qwen3-0.6B top-16×384 | GPU | 140 ms |
| **recuperação** | | **247,7 ms** |
| V⁴ sobre 12 claims | wj-nli-54M, 3 núcleos | ≈ 64 ms [derivado] |

Indexação densa com `jua-4B-mixed` (MIT) + LoRA InfoNCE; consulta com Qwen3-Embedding-0.6B destilado do 4B-FT (bate o 4B-FT no JUÁ-Juris: 0,302 vs 0,290). ColBERT-JUR-pt = 0.6B truncado a 6 camadas + projeção 64d, KL sobre o Qwen3-Reranker-4B (jina-colbert-v2 é CC-BY-NC — fora).

supera: A02 dimensionava 5M chunks densos; D01 #5 fixa três camadas (≥ 40M chunks densos).

**Números.** Disco: BM25 300 GB, denso 29 GB, ColBERT 58 GB; `shared_buffers` de 16 GB mantém BM25 + denso em 45 ms (~250 ms sem ele).

**Origem:** A02 §2/§6; D01 #5; E02 §6; E07.

### I.4.2 Chunking hierárquico com contextualização determinística

**Decisão fechada.** Unidade = dispositivo (artigo → § → inciso → alínea; em acórdão: ementa, relatório, voto, dispositivo). O contexto do chunk é um header **derivado do próprio documento**, prefixado antes de embutir e antes de indexar no BM25; embedding por late chunking num passe de 32k.

**Mecanismo.**

```
Lei 10.406/2002 (Código Civil) › Livro I › Título III › Art. 927, parágrafo único
[urn:lex:br:federal:lei:2002-01-10;10406!art927_par1] [vigente 2003-01-11 → ∞]
```

O header injeta as chaves léxicas (número da lei, "Art. 927", órgão) e melhora as duas pernas da fusão, BM25 e denso.

**Números.** Agrupamento estrutural: nDCG@5 0,459 contra < 0,244 do fixed-size (+88%). Contextual Retrieval com LLM: −67% de falha top-20 a US$1,02/M tokens; aqui R$0,00. Com +916 tokens o header fica 31,11% menor.

**Por que ninguém tem.** Em direito o contexto é derivável; o estado da arte paga um LLM para inventá-lo.

**Origem:** A02 D3, §1, Inov. 2; D04.

### I.4.3 Roteador de fusão por classe e LambdaMART

**Decisão fechada.** RRF ponderado por classe de consulta (DISPOSITIVO, JURISPRUDÊNCIA, CONCEITO, RACIOCÍNIO), pesos aprendidos por coordinate ascent em nDCG@10; LambdaMART ordena antes do reranker.

**Mecanismo.**

```sql
WITH lex AS (SELECT id, rank() OVER (ORDER BY bm25 <&> to_bm25query('wj_tok',$1)) r FROM chunk ORDER BY 2 LIMIT 400),
     den AS (SELECT id, rank() OVER (ORDER BY emb <-> $2) r FROM chunk ORDER BY 2 LIMIT 400),
     ppr AS (SELECT id, rank() OVER (ORDER BY score DESC) r FROM graph_ppr($3) LIMIT 200)
SELECT id, SUM(w) s FROM (SELECT id, $4::float/(60+r) w FROM lex UNION ALL
                          SELECT id, $5::float/(60+r) w FROM den UNION ALL
                          SELECT id, $6::float/(60+r) w FROM ppr) u
GROUP BY id ORDER BY s DESC LIMIT 200;
```

Perfis iniciais (w_lex/w_den/w_ppr): DISPOSITIVO 1,4/0,6/0,0 · JURISPRUDÊNCIA 1,0/1,0/0,4 · CONCEITO 0,5/1,5/0,2 · RACIOCÍNIO 0,8/1,0/1,2. LambdaMART (`lambdarank`, 63 folhas, `monotone_constraints` negativo em `revogado`) com rótulos 0–4, **grau 4 = citação verificada por IA de terceiro**; promove com NDCG@10 ≥ +2% e interleaving com IC95 > 0,5.

**Números.** Oráculo por coleção do JUÁ = 0,476 contra 0,443 do melhor sistema único (+7,6%); meta 0,52 com ColBERT-JUR + contextualização [est.].

**Por que ninguém tem.** O ranker aprende com citação verificada por IA, não com clique.

**Origem:** A02 D2, §3; A07 §4, Inov. 2.

### I.4.4 Grafo determinístico e PPR por forward push

**Decisão fechada.** O grafo nasce de gramática + resolvedor URN + NER ONNX, zero LLM na indexação. PPR roda por forward push local em CSR na RAM — nunca power iteration, nunca dentro do AGE.

**Mecanismo.** AGE 1.8.0 guarda 101,4M arestas tipadas (19,1 GiB); 200M citações brutas ficam em tabela particionada; CSR ponderado de 2,55 GiB. Forward push (FORA), α = 0,15, `r_max = 1e-4`, seeds = top-20 da fusão, custo O(1/(α·r_max)) independente de |E|, manutenção incremental no delta diário. A autoridade global `Auth(v,T)` é o mesmo push com teleporte `π(v) ∝ vig(v,T)·τ(v)·e^(−λ·idade)` e sucessão de autoridade (o superado redireciona massa ao superador). VLE com `k ≤ 6` e guarda de grau.

supera: A02 supunha ~10M arestas e 30 iterações; C02 mede 301,4M arestas e 180,86 s/consulta em power iteration. A07 rodava PageRank global por power iteration horária — vira push com teleporte π. AGE 1.7.0 (A01/A02/C02) → 1.8.0 (dist ASF).

**Números.** ≤ 66.667 pushes ≈ 6,7 ms; indexação por LLM = 4.227 dias-GPU contra 2,78 h de CPU (36.522×); ≈ 1.000 tokens/consulta contra 331.000 do GraphRAG global; cobertura do normalizador 91,0%.

**Origem:** A02 D4; C02 D2–D4; A07 §5; E04 B.3.

### I.4.5 Máquina fail-closed, t_max = 4, τ conformal

**Decisão fechada.** Agêntico só na reescrita e no roteamento, com teto rígido de 4 rodadas; fail-closed imposto no serializador; τ = 0,906 escolhido por controle conformal de risco, guardado no banco e recalibrado por martingale de Ville.

**Mecanismo.**

```
PARSE → RETRIEVE(t) → ASSESS ─┬─ (Cov<1 ∧ t<4) → REWRITE → RETRIEVE(t+1)
                              └─ DRAFT → DECOMPOSE → RESOLVE → VERIFY → EMIT
RESOLVE: URN resolve ∧ sha256(span[off:off+len]) = hash gravado ∧ URN ∈ topK(q)   falha ⇒ DROP_CLAIM
VERIFY : p_entail(claim, span) ≥ τ (wj-nli-54M)        falha ⇒ REPAIR 1× só com as evidências ⇒ ABSTAIN
DEFAULT: exceção, timeout ou estado desconhecido ⇒ ABSTAIN
```

Parada: `Cov_t = 1` ∨ `ΔCov < 0,05` em 2 rodadas ∨ novidade `ν_t < 0,15` ∨ `t = 4`. `Cov < 0,80` ⇒ expansão por PPR e, persistindo, ABSTAIN com lacuna declarada (sub-afirmações órfãs vão para a `gap_queue`). τ = maior limiar com `UB95 ≤ α = 1%` para R = P(publicada ∧ não sustentada), por Clopper-Pearson (conjunto de calibração em I.6.3).

supera: A06 usava τ = 0,70 (XNLI) e A01/A04/A08 τ = 0,85; com HCR ≤ 2% só τ ≥ 0,906 mantém UB95 ≤ 1% — τ único (E07).

**Números.** n = 1.000 ⇒ máx. 4 violações (UB95 0,913%); 0 em 3.000 ⇒ 0,100%. Agêntico custa 3,3× tokens de entrada; 4 rodadas contra 15,3 passos/trecho do agente livre.

**Origem:** A02 D5–D6, §5; E07 D1; E08 N24.

### I.4.6 Retrieval Receipt e métrica corrigida por cobertura

**Decisão fechada.** Toda afirmação sai com Retrieval Receipt Ed25519 que carrega `(URN, ver_id, redação@sha, off, len, span_sha256, vigência, index_version, nli, τ)`. Toda métrica pública sai dividida pela cobertura medida do índice.

**Mecanismo.**

```json
{"claim":"A responsabilidade é objetiva quando a atividade implica risco.",
 "proof":{"urn":"urn:lex:br:federal:lei:2002-01-10;10406!art927_par1","vigencia":"2003-01-11/∞",
          "off":142,"len":216,"span_sha256":"9f2c…","redacao_sha":"…","index_version":"wj-2026-09-22",
          "nli":{"model":"wj-nli-54M","milli":941,"tau_milli":906},"verdict":"span_entails_claim",
          "sig":"ed25519:…","log":{"leaf_index":48213,"mmd_s":60}}}
```

Ed25519 assina os bytes JCS (RFC 8785); a folha do log é `SHA-256(0x00 ‖ JCS(recibo∖proof))` num log contínuo (SCITT RFC 9943, COSE Receipts RFC 9942). Emissora: a PJ `did:web:wikijuridica.com.br` (CHECK no banco). Métrica: `CRR_corrigida = CRR_observada / Cobertura_estimada`, cobertura por captura-recaptura contra DJEN, LexML e STJ-CKAN.

**Números.** arXiv:2606.00898: a mesma base mede 15–21% de alucinação com 4,7×10⁵ registros e 0,1–1% com 3,3×10⁸. Ed25519 ≥ 16k recibos/s/núcleo [est.].

**Por que ninguém tem.** Prova criptográfica de recuperação reverificável offline por terceiro, e a primeira plataforma a publicar o próprio oráculo.

**Origem:** A02 Inov. 1/3; E07 D3; B06 D4.

---

## I.5 Vigência tri-temporal

### I.5.1 Modelo de dados, EXCLUDE e totalidade

**Decisão fechada.** Três eixos: vigência (`daterange`, força formal) × eficácia (`daterange`, efeito operativo) × transação (`tstzrange`). LexML URN é a chave (`urn_work`); Akoma Ntoso é a serialização; ELI é a projeção JSON-LD; LegalRuleML só nas ~50 meta-regras defeasible. Materializa-se versão, não diff: point-in-time é um `@>` em GiST.

**Mecanismo.** Tri-temporal porque a lei exige: LINDB art. 1º (vacatio), CF art. 62 §11 (MP caduca e as relações conservam-se: vigência fechada, eficácia aberta), Lei 9.868/99 art. 27 (modulação) e art. 11 §2º (cautelar repristina).

```sql
CREATE FUNCTION sha256_utf8(t text) RETURNS bytea LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
  AS $$ SELECT sha256(convert_to(t,'UTF8')) $$;
CREATE TABLE disp_versao (
  ver_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  disp_id    uuid NOT NULL REFERENCES dispositivo(disp_id),
  texto      text NOT NULL,                          -- '' quando revogado
  texto_sha  bytea GENERATED ALWAYS AS (sha256_utf8(texto)) STORED,
  vigencia   daterange NOT NULL, eficacia daterange NOT NULL,
  modo       modo_eficacia NOT NULL DEFAULT 'plena', -- vacatio|retroativa|suspensa|ex_tunc_nula|repristinada|ultratividade|revogado
  evento_id  uuid NOT NULL REFERENCES evento(evento_id),
  tx         tstzrange NOT NULL DEFAULT tstzrange(now(), NULL, '[)'),
  classe_div char(2) NOT NULL DEFAULT 'D0' CHECK (classe_div IN ('D0','D1','D2','D3')),
  prova      jsonb NOT NULL,
  CONSTRAINT dv_bitemporal    EXCLUDE USING gist (disp_id WITH =, vigencia WITH &&, tx WITH &&),
  CONSTRAINT dv_corrente      EXCLUDE USING gist (disp_id WITH =, vigencia WITH &&) WHERE (upper_inf(tx)),
  CONSTRAINT dv_efic_corrente EXCLUDE USING gist (disp_id WITH =, eficacia WITH &&) WHERE (upper_inf(tx)),
  UNIQUE (ver_id, texto_sha));
CREATE FUNCTION chk_vigencia_total() RETURNS trigger AS $$
DECLARE m datemultirange; n int; d uuid := COALESCE(NEW.disp_id, OLD.disp_id);
BEGIN
  SELECT range_agg(vigencia) INTO m FROM disp_versao WHERE disp_id = d AND upper_inf(tx);
  IF m IS NULL THEN RETURN NULL; END IF;
  SELECT count(*) INTO n FROM unnest(m);
  IF n <> 1 OR NOT upper_inf(m) THEN RAISE EXCEPTION 'I-VIG-1: % -> %', d, m; END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;
CREATE CONSTRAINT TRIGGER trg_vig_total AFTER INSERT OR UPDATE OR DELETE ON disp_versao
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chk_vigencia_total();
```

`evento` tem 20 tipos e `grau_certeza`: revogação tácita nunca é asserção (só vira 1,000 com holding STF/STJ ou revisão humana). `tese_versao` reusa a máquina (CPC art. 927 §3º).

supera: A03 checava continuidade com `cardinality(datemultirange)` (não existe em PG 16/17/18) e gerava `texto_sha` com `convert_to` (STABLE: "generation expression is not immutable") — nenhum dos dois rodava; D10/E07 corrigem com `unnest` e `sha256_utf8` IMMUTABLE.

**Números.** ~6,5M dispositivos × 1,6 versões ≈ 10,4M linhas, ~12 GB [est.]; p50 < 8 ms, p99 < 40 ms com cadeia de prova [est.].

**Por que ninguém tem.** LexML, AKN e ELI são monotemporais no identificador; só três eixos com exclusion constraint respondem MP caducada com ultratividade e ADI modulada na mesma consulta.

**Origem:** A03 D1–D3, §1; D10; E07 `schema.sql`.

### I.5.2 Gramática de comandos e álgebra de diffs

**Decisão fechada.** A reconstrução é um fold determinístico de seis operações sobre floresta de chaves estáveis, em ordem total obrigatória; duas emendas com a mesma chave de ordenação na mesma `k` geram nó CONFLITO e o dispositivo sai como INDETERMINADO — nunca palpite.

**Mecanismo.** Gramática fechada pela LC 95/98 arts. 10–12 (`passa a vigorar com a seguinte redação`, `acrescente-se`, `fica revogado`, `renumere-se`, alvos `art. 5º-A`, `§ 2º`, `inciso IV`). Operações `SET, INS, DEL, MOV, REN, SUB`, cada uma com `antes_sha256` (invertível):

```
Π(T₀, D) = fold(apply, T₀, sort({A : d_efic(A) ≤ D}, key = (d_efic, hierarquia↑, data_publicacao, num_DOU, seq_op)))
```

A aresta causal já vem legível no HTML do Planalto: `(Redação dada pela Lei nº 13.146, de 2015)` aponta alteradora e artigo (`#art114`), `(Vigência)` aponta a vacatio (`#art127`) — extração aberta vira verificação fechada. Articulação reusa `lexml-parser-projeto-lei-ws-docker` como sidecar; Go escreve o parser de comandos e o motor tri-temporal.

**Números.** CC compilado: 677 notas de alteração (315 Incluído, 174 Vigência, 91 Redação dada, 80 Revogado); a CF traz as duas redações do art. 62 no mesmo arquivo — viram versões históricas.

**Origem:** A03 §4–§6.

### I.5.3 Consolidação adversarial D0–D3

**Decisão fechada.** Três parsers independentes — P1 (compilada do Planalto), P2 (reconstrução a partir das alteradoras), P3 (texto do Senado, `normas.leg.br` via `rod`) como árbitro por maioria — comparados em forma canônica; divergência classificada em D0–D3; ADI/ADPF/MP entram como overlay fora da comparação.

**Mecanismo.** Forma canônica = NFC → strip de tags → colapso de espaço/`&nbsp;` → normalização de `º/°/o/<sup>` → remoção de notas parentéticas. D0 idêntico · D1 cosmético · D2 só-nota · D3 texto. Selo "consolidado" só em D0∪D1∪D2; D3 publica com cadeia de prova e rótulo, nunca some do ar. Toda divergência é item de revisão **e** rótulo verificável para o RLVR. Fonte oficial só entra no espelho WARC se dois egressos (link doméstico + VPS em outro AS) trouxerem o mesmo hash.

supera: A03 exigia ≥ 98% byte a byte — impossível por construção (CF: 780 tachados, 66 "(Vide ADI"; Lei 14.195: 94 linhas "……", 68 "(NR)", 40 cláusulas de produção de efeito). Meta canônica: ≥ 98% em D0∪D1 por dispositivo nas 200 leis mais consultadas, com a taxa de D3 publicada como métrica de cobertura.

**Números.** Nenhum HTML do Planalto declara charset (sniff ISO-8859-1); 200 leis antes do lançamento.

**Por que ninguém tem.** Consolidação usada como **verificador**, não como gerador: cada divergência vira métrica pública e dado de treino de graça.

**Origem:** A03 D4; D01 Frente 4 #3 e #8; E08 N17.

### I.5.4 Aresta INTERPRETA@sha e apelido com janela temporal

**Decisão fechada.** Acórdão liga-se à **redação**, não ao artigo: `INTERPRETA(Decisao → Redacao@texto_sha)`, povoada por join temporal `eficacia @> data_julg`, sem LLM. Apelido normativo é função de (string, data do documento citante).

**Mecanismo.**

```sql
-- apelido: "Lei de Licitações" vale 8.666 até 2023-12-29 e 14.133 a partir de 2023-12-30
SELECT urn_alvo FROM apelido WHERE forma_norm = $1 AND janela @> $2::date ORDER BY peso DESC LIMIT 1;
-- empate de peso ⇒ INDETERMINADO; sem data do documento ⇒ devolve as duas resoluções com janelas
```

Consulta de contradição C2 (produto, zero GPU): decisão que aplicou redação cuja eficácia não cobre a data do fato. "Good Law" temporal: PPR restrito a arestas com data ≤ D, erosão em 24 meses e superação por Dempster–Shafer (ignorância > 0,35 ⇒ INDETERMINADO).

**Números.** INTERPRETA conf. 0,90; Lei 14.133 art. 193 tem três redações fixando 2023-12-30; semente de ~312 apelidos [est.].

**Por que ninguém tem.** Shepard's e KeyCite são atemporais e ligam precedente a artigo; a aresta @sha impede citar acórdão de 2023 sobre redação revogada, e nenhum normalizador trata apelido como função da data.

**Origem:** A03 §7, Inov. 4; C02 D5, Inov. 1–2.

### I.5.5 API `/norma?em=` com immutable e Merkle contínuo

**Decisão fechada.** A resposta temporal é função pura: `?em=` é canonicalizado por 301 para a fronteira de versão (`?v=`), `tx` só aceita raiz publicada do log (senão 400), e resposta com `v` + `tx` sai `immutable`. Todo recibo é folha de um log Merkle contínuo com MMD de 60 s.

**Mecanismo.**

```
GET /norma/urn:lex:br:federal:lei:2002-01-10;10406!art3_cpt?em=2019-03-01&modo=eficacia
→ 301  Location: …!art3_cpt?v=2016-01-06&modo=eficacia
GET …!art3_cpt?v=2016-01-06&modo=eficacia&tx=2026-09-22T13:14:00Z          (tx = raiz MMD publicada)
→ 200  x-wj-urn-expression: urn:lex:br:federal:lei:2002-01-10;10406@2016-01-06!art3_cpt
       x-wj-akn: /akn/br/act/lei/2002-01-10/10406/pt@2016-01-06~art_3
       x-wj-tx: 2026-09-22T13:14:00Z    etag: "wj-<sha256(payload)>"
       cache-control: public, max-age=31536000, immutable
```

Sem `tx`, sai a raiz corrente em `x-wj-tx` com `max-age=60`. Payload: texto, vigência, eficácia, modo, cadeia de prova (evento, operação, fonte, vacatio, `antes/depois_sha256`, conferência P1×P2×P3) e recibo com caminho de inclusão RFC 6962. O checkpoint de 00:00Z vai à âncora externa (Rekor/RFC 3161 + DNS); o notebook é a segunda testemunha.

supera: A03 publicava raiz Merkle diária e assinava o SHA-256 do JCS; B06: log contínuo com MMD de 60 s e Ed25519 sobre os bytes JCS (o SHA-256 é o valor da folha).

**Números.** Chaves de cache: de ∞ para as 10,4M versões (fuzz com 10⁶ datas); `/norma` p95 ≤ 80 ms no edge; 100.000 citações/dia ≈ 1,2 assinatura/s.

**Por que ninguém tem.** Correção temporal **reduz** custo de origem (immutable no edge), e o log prova o que a plataforma afirmava antes da disputa.

**Origem:** A03 D3, §8; D01 Frente 6, Ataque A; B06 D4; E08 N03/N18.

---

## I.6 O verificador único V⁴

### I.6.1 Um pacote, um modelo, um τ

**Decisão fechada.** `wj/verify` é o único verificador do sistema: resolvedor de URN + `span_sha256` + vigência em `at` + E7 relevância + NLI **wj-nli-54M** com τ = 0,906 lido de `conformal_calibration`. O literal `0.906` existe só na semente do banco; em runtime τ vem da tabela, recalibrado pelo martingale de Ville.

**Mecanismo.** wj-nli-54M = mmBERT-small (`jhu-clsp`, MIT, 140M, 22 camadas, 8.192 de contexto) como cross-encoder `[CLS] afirmação [SEP] trecho [SEP]`, vocabulário podado de 256.000 para 32.000 (embedding 98,3M → 12,3M) ⇒ 54M parâmetros, ONNX int8 via hugot na CPU.

```go
package verify // único pacote que conhece τ; receipt ↛ verify (terceiro reverifica sem rodar nosso NLI)
func (v *V) Check(ctx context.Context, q Query, c Claim, topK map[string]bool) Result {
	r, ok := v.res.Resolve(c.URN, c.At)
	switch {
	case !ok:                                   return Result{Err: E1}
	case !r.HasAnchor(c.Anchor) || sha256.Sum256(r.Span(c.Off, c.Len)) != c.SpanSHA:
	                                            return Result{Err: E2} // âncora ou trecho alheio
	case !r.Cobre(c.At):                        return Result{Err: E4} // vigência ∧ eficácia em T_fato
	case !topK[c.URN]:                          return Result{Err: E7} // relevância
	}
	p, tau := v.nli.EntailMilli(c.Text, r.Span(c.Off, c.Len)), v.cal.TauMilli("retrieval")
	if p < tau { return Result{Err: E3, NLIMilli: p, TauMilli: tau} }
	return Result{NLIMilli: p, TauMilli: tau, VerID: r.VerID, RedacaoSHA: r.SHA}
}
```

supera: A02 (MiniCheck-FT5 online + Bespoke-MiniCheck-7B em auditoria), A04 (mDeBERTa-ASSIN2) e D01/E07/E08 (fine-tune de `microsoft/mdeberta-v3-base`) — o verificador é wj-nli-54M sobre mmBERT-small (CANON). Bespoke-MiniCheck-7B não tem licença declarada; MiniCheck é en-only.

**Números.** 16 ms/par/núcleo; 204k pares/dia = 3.264 núcleo-s (0,47% da CPU); 0 GPU-s.

**Origem:** D04 D6, §5; E07 D1; E04 B.11; CANON.

### I.6.2 Os quatro contratos

**Decisão fechada.** O mesmo artefato é (a) portão de runtime, (b) produto `/verify` — já no ar como `/api/v1/citacoes` —, (c) recompensa do RLVR e (d) gerador de caso de teste. Todos os subsistemas **importam** `wj/verify`.

**Mecanismo.** (a) S5 do grafo → `Verdict` → emit/repair/replan. (b) `/verify` + x402 → recibo `span_entails_claim`. (c) Coletor do GSPO-DrC → termos URN, NLI, vigência e E7 de `R_total`. (d) V < 0,90 → caso congelado → bench + `gap_queue`. Anti-lavagem: veredito fechado (nunca `correct`/`valid`); preço `p·1,5^k` na k-ésima quase-duplicata (`sim > 0,9`) da mesma chave; sem `at`, o recibo diz `at: unspecified` e não confirma vigência; E7 mata o hack "cite sempre CF art. 5º".

**Números.** Piso R$0,00135/chamada; break-even de 5.034 `/verify`/dia; agente que não paga custa 6,4 ms de edge e 0 GPU.

**Por que ninguém tem.** V⁴: um verificador que paga por si mesmo enquanto treina o modelo e escreve o próprio teste de regressão.

**Origem:** A01 D4, Inov. 1; D01 Frente 6, Ataque B; E07; CANON.

### I.6.3 Dataset de treino com negativos N2

**Decisão fechada.** O wj-nli-54M treina em quatro fontes do próprio corpus — 40% P+, 20% N1, 20% N2, 20% N3 — e a vantagem tem de vir de N2, a corrupção temporal onde verificador genérico é cego.

**Mecanismo.** P+: (afirmação, trecho cujo URN resolve), do log Merkle, ~300k pares. N1: corrupção de entidade (art. 927 → 928, 13.105 → 13.015). **N2: o trecho é a redação anterior do mesmo dispositivo**, rótulo NÃO SUSTENTA em T. N3: top-5 de BM25 + denso sem a resposta. Calibração: 1.000–3.000 claims de Rafael (~35 h) + 10.000 negativos programáticos. Deriva do verificador: painel selado mensal de 300 pares rotulados por Rafael, e o τ gravado em cada recibo torna a deriva detectável em dado assinado.

**Números.** Alvo: BAcc ≥ 77,4 no LLM-AggreFact (número publicado do Bespoke-MiniCheck-7B, sem executar o modelo) e ≥ +15 pp sobre o MiniCheck-Flan-T5-Large (MIT) na fatia N2. O corpus exercita só 4,44% do vocabulário de 256.000 — daí a poda.

**Por que ninguém tem.** N2 só existe porque o motor tri-temporal guarda a redação anterior com sha; nenhum dataset NLI público tem negativo temporal.

**Origem:** D04 §5; E08 N24; D03 Risco 4; E07 Risco 2; E04 B.11.

### I.6.4 Fail-closed no serializador e no banco

**Decisão fechada.** Nenhuma sentença sai sem proof válido. O serializador da answer unit só emite sentença com recibo; o banco torna inexprimíveis o recibo sub-τ, o recibo de redação alheia e a publicação sem recibo daquele trecho.

**Mecanismo.**

```sql
-- citation_receipt
  verdict   text NOT NULL CHECK (verdict = 'span_entails_claim'),
  taint     smallint NOT NULL CHECK (taint = 0),
  CONSTRAINT i_verify_1 CHECK (nli_milli >= tau_milli),                 -- recibo sub-τ não existe
  FOREIGN KEY (ver_id, redacao_sha) REFERENCES disp_versao (ver_id, texto_sha),  -- aponta a REDAÇÃO
-- publicacao
  FOREIGN KEY (receipt_id, span_sha256) REFERENCES citation_receipt (id, span_sha256)
```

**Números.** 28 ataques ao schema, 28 recusas (PG 16.13); invariantes I-VERIFY-1/2/3, I-PUB-1/2, I-TAINT-1.

**Por que ninguém tem.** τ dentro do fato assinado: recibo antigo continua verificável contra o τ da época, τ sobe sem migração; FK composta como prova de pertinência torna "recibo verdadeiro colado em trecho alheio" inexprimível.

**Origem:** A02 §5; E07 D3, Inov. 2; D10.

---

## I.7 Modelo: base, tokenizador e arquitetura própria

### I.7.1 Base e papéis

**Decisão fechada.** Residente: Qwen3-8B denso (Apache-2.0, 8,19B) em NVFP4 (ModelOpt), KV FP8. Volume: aluno Qwen3-4B destilado — LoRP + Minitron width sobre o 8B jurídico, com o Qwen3-4B oficial como linha de base no G2. Professor e escalada: Gemma-4-26B-A4B-it (Apache-2.0, 25,81B, não gated) em EXL3 ~3,2 bpw. CPU: BitNet-b1.58-2B-4T.

**Mecanismo.** Família Qwen para tudo que chama ferramenta (ACEBench: 54,8% contra 33,4% do Llama-3.1-8B). Gemma-4 e Qwen3 têm tokenizadores diferentes ⇒ KL por token entre eles é inexprimível: o Gemma-4 é professor **de sequência** (rejection sampling, SCoRe); o professor **por token** do aluno 4B é o 8B jurídico.

supera: A04 escolhia Qwen3.5-4B + Gemma-4-4B; o Qwen3.5-4B é híbrido (atenção linear 3:1, visão, MTP) e incompatível com LoRP, Minitron, EXL3 e a conta de KV — proibido (CANON, E04 B.14). O Gemma3-27B gated do A05 e o 32B do A08 cedem ao Gemma-4-26B-A4B.

**Números.** Qwen3-8B: L = 36, H_kv = 8, D = 128 ⇒ 73.728 B/token de KV FP8; pesos NVFP4 4,60 GB; aluno 4B NVFP4 ≈ 2,3 GB; Gemma-4-26B-A4B EXL3 10,4 GB, sem offload.

**Origem:** A08 D1; D01 #4; E04 A.4/B.14; E02 §4; CANON.

### I.7.2 Tokenizador com +916 tokens

**Decisão fechada.** Estender o vocabulário em 916 tokens — 19 estruturais, 33 da gramática LexML, 100 pares de dígito, 764 n-gramas jurídicos —, inicializados por Token Distillation, **antes** da poda.

**Mecanismo.** Os 52 estruturais/LexML (`<|urn|> <|art|> <|par|> <|inc|> <|vig|> <|cita|> <|prova|> <|conf|> <|abstem|>` …) são *added tokens* fora do BPE — nenhum byte de entrada os produz — e cabem nas 267 linhas de embedding já alocadas e vazias (`vocab_size` 151.936 contra 151.669 do tokenizer); só 864 pedem `resize_token_embeddings`. Seleção gulosa por `economia(g) = (tokens_base(g) − 1)·freq(g)`, freq ≥ 60, medida em held-out (CPP, Lei 9.099, Lei 14.905). Inicialização por Token Distillation (arXiv:2505.20133) + 30k sentenças; vem antes do LoRP porque o Minitron width calibra ativação sobre o `lm_head` final.

**Números.** Fertilidade 2,1075 → 1,6727 (−20,63%); answer unit 580 → 422 tokens; URN −51,59%; nº CNJ −34,62%; pt-BR geral −4,24% (melhora fora do domínio). Custo: +2,34M parâmetros no Qwen3-4B (0,058%), +7,5M no 8B [derivado: 916 × 4.096 × 2]. Aceite: ≥ 80% dos tokens com frequência de geração > 10⁻⁵; os 100 pares de dígito saem se a suíte aritmética cair.

**Origem:** D04 D1–D2, §1–2.

### I.7.3 Trie de ⟨URN⟩ no decoder e gramática de três destinos

**Decisão fechada.** O token `<|urn|>` comuta o decoder do `lm_head` para a trie das URNs que existem no Postgres canônico, filtrada pela data de referência da consulta. Fora desse modo, a gramática proíbe dígito em prosa e `urn:lex:` literal. Citação inventada fica impossível por construção.

**Mecanismo.** Trie por requisição: fecho de componentes das URNs recuperadas, filtrado por vigência em `at` — ~50.000 chaves (≈ 2 MB) em < 1 ms; a trie completa (1,6 GB) fica na RAM do resolvedor. Um logits processor do vLLM ativado por `<|urn|>` mascara tudo que não é filho do nó corrente e devolve o controle ao xgrammar na folha (Outlines proibido: 3,5–8 s de compilação):

```
resposta ::= ( prosa | calc | cita )*
prosa    ::= [^0-9{}]+                      # onde caberia número só cabe placeholder
calc     ::= "{{" tool "." campo "}}"       # preenchido pelo C03 (big.Rat, intervalo nominal/estrito)
cita     ::= "<|cita|>" "<|urn|>" TRIE(at)  # a trie termina numa URN existente e vigente em at
```

O verificador de ancoragem do C03 rejeita todo token calculável que não veio de ferramenta da sessão (E5).

supera: D04 dependia de FlashTrie com 800M chaves; E02 faz a trie por requisição.

**Números.** E1 → 0 por construção; o que se mede é E1 virar E3 (URN existente, porém errada) na trilha (b), e o G1 decide. O ramo −1,0 da recompensa fica inalcançável e a variância do gradiente vai para NLI e vigência.

**Por que ninguém tem.** Recuperação generativa usa trie sobre doc-ID; ninguém acoplou ao decoder uma trie **filtrada por vigência**.

**Origem:** D04 Inov. I1; E02 §4; C03; D05 D1.

### I.7.4 BOSCH SWA 5:1 e a trava ⟨PROVA⟩

**Decisão fechada.** Hibridização pós-treino em nível de cabeça (BOSCH, arXiv:2604.05942, treino-livre): 5 camadas SWA com W = 4.096 para 1 global. Compressão ou evicção de KV é proibida dentro de ⟨PROVA⟩: o montador de prompt põe ⟨PROVA⟩ imediatamente antes do ponto de geração e impõe `|⟨PROVA⟩| + max_tokens_do_segmento ≤ W` (ex.: 3.072 + 1.024); T2/T4 geram por seção, remontando ⟨PROVA⟩ a cada segmento com custo ≈ 0 via prefix caching.

**Mecanismo.** A máscara por cabeça é artefato com sha256 no registry, referenciado por `bench_result`. Rejeitados: NSA (exige pré-treino) e Mamba (quebra vLLM/FlashInfer); LoLCATs é plano B.

**Números.** Ganho de KV 1,71× em 8k (5/6 × 0,5 + 1/6 × 1) e 5,19× em 128k (medido no Qwen3-4B). 5,00 GB de KV = 124.830 tokens = 15,2 sessões de 8k (30 de 4k), contra 72.818 tokens (8,9 sessões) sem SWA — o BOSCH compra as últimas 6 sessões; bloco CAG único de 377.924 tokens. Evicção de evidência faz o modelo alucinar em vez de abster (arXiv:2608.29934).

**Origem:** D04 D3, §3; E02 §4, Risco 5.

### I.7.5 Cabeças de risco

**Decisão fechada.** Três MLPs sobre o backbone congelado — `head_suf` (evidência suficiente), `head_risk_vig` (risco de mudança de redação), `head_unc` (incerteza para o roteador) — são portão de **custo**, nunca de segurança. Abaixo do τ de `head_suf` (Mondrian por ramo), o modelo emite `<|abstem|>` e o roteador escala.

**Mecanismo.** `Sequential(Linear(h,h), GELU(), LayerNorm(h), Linear(h,k))`, rotulada de graça pelos rollouts do RLVR (`h_t` ao abrir `<|cita|>` → valid/k, NLI, vigência), treinada em CPU. CI: `heads/` não pode ser importado por `grounding/`.

supera: D04 propunha cabeça que prevê data de vigência; o motor tri-temporal entrega a data exata em código — vira cabeça de risco.

**Números.** ~6,6M parâmetros por cabeça com h = 2.560, ~16,8M no 8B [derivado]; 0,16% dos FLOPs de decode contra 110–900 ms para gerar veredito em tokens. Sondas colapsam para o acaso quando o gerador fabrica com confiança (DECK) — o V⁴ fica no caminho crítico.

**Origem:** D04 D4–D5, §4, Inov. I3.

### I.7.6 S-LoRA por ramo, roteador discreto

**Decisão fechada.** Um adaptador inteiro por requisição, escolhido por roteador discreto (ramo pelo BitNet + classe de consulta do A02); S-LoRA multiplexa no serving; X-LoRA está morto.

**Mecanismo.** 2 slots r = 16 na GPU (0,16 GB), demais adaptadores em RAM, hot-swap por `VLLM_ALLOW_RUNTIME_LORA_UPDATING` + `POST /v1/load_lora_adapter`. Escolha discreta é auditável e vetável por Cedar; mistura contínua de pesos não é. Os LoRAs cirúrgicos de tese (I.9.3) e os papéis do painel disputam os mesmos slots.

supera: A01/D05 usavam `--max-loras 6 --max-lora-rank 32`; mapa canônico: 2 slots r = 16 (E02).

**Números.** Mixture-of-LoRA contra baseline estático: +0,015 nats, p = 0,19; o ganho real (+0,0426 nats, p = 0,006) vem só do roteador.

**Origem:** D04 D7, §6; E02 §4; D05 §5.

---

## I.8 Destilação e pós-treino

### I.8.1 Sequência de construção

**Decisão fechada.** Ordem fixa; cada passo produz artefato com sha256 no registry e só o artefato **quantizado** é avaliado.

**Mecanismo.**

1. Qwen3-8B + 916 tokens (Token Distillation) + 30k sentenças jurídicas.
2. SFT com 2.000 trajetórias do Gemma-4-26B-A4B aprovadas pelo V⁴ (LoRA r = 64, 2 épocas, lr 2e-4).
3. SCoRe: onde a rejection sampling falha, o professor corrige só o primeiro erro e o aluno retoma do prefixo verificado.
4. GSPO-DrC com a recompensa canônica ⇒ **8B jurídico**.
5. LoRP + Minitron width ⇒ **aluno ~4B**.
6. Recuperação por destilação on-policy do 8B (DVH: −KL reversa por token dentro de `<|cita|>` + `R_total` nos tokens finais) e GSPO-DrC curto.
7. Máscara BOSCH, quantização NVFP4 (ModelOpt) / EXL3, G1–G5 no artefato quantizado, promoção.
8. Manutenção: on-policy distillation e consolidação mensal (I.9).

**Números.** 2.000 trajetórias dão +9,1 pp; on-policy distillation é 50–100× mais rápida que RL.

**Origem:** A08 D3, §4; A04 Inov. (DVH); D04 §1; E08 N43–N44.

### I.8.2 LoRP + Minitron width

**Decisão fechada.** Poda híbrida sem retreino longo: LoRP para profundidade (treino-livre), Minitron width single-shot para largura.

**Mecanismo.**

```bash
python -m lorp.prune --model wj-8b --calib-set c4 --calib-samples 128 \
  --target-depth-reduction 0.25 --method locality-aware-rls --out wj-6b-depth     # 36 → 27 camadas
python -m modelopt.prune --model wj-6b-depth --calib-samples 1024 \
  --prune embedding,heads,ffn --target-params 4.5e9 --out wj-4b-pruned           # l2-norm+mean de ativação
```

**Números.** LoRP validado até ~32% de redução de profundidade; recuperação de 0,5–1B tokens em domínio restrito [est.] contra 94B do Minitron single-stage.

**Origem:** A04 D1, Engenharia.

### I.8.3 GSPO-DrC

**Decisão fechada.** GSPO (razão de importância por sequência) + Dr.GRPO (sem normalização por comprimento nem por std) + Clip-Higher, dynamic sampling e overlong shaping do DAPO, em QLoRA 4-bit via TRL/Unsloth.

**Mecanismo.**

```python
GRPOConfig(per_device_train_batch_size=8, gradient_accumulation_steps=4, num_generations=8,
           max_prompt_length=1024, max_completion_length=1024, learning_rate=5e-6, optim="adamw_8bit",
           lr_scheduler_type="cosine", warmup_ratio=0.1, max_grad_norm=0.1, temperature=0.9,
           importance_sampling_level="sequence", loss_type="dr_grpo", scale_rewards="none",
           epsilon=0.2, epsilon_high=0.28, beta=0.0)
# coletor: descarta grupo de recompensa idêntica; overlong = max(-1, (450-150-|y|)/150);
# reamostra o grupo se < 2 dos 8 rollouts consideram redação NÃO-corrente (D05)
```

**Números.** GRPO puro colapsa ("irreversible model collapse", Qwen); VAPO fica fora (exige rede de valor); CISPO em A/B; 5.000 steps × ~101 s ≈ 505.000 GPU-s [est.].

**Origem:** A04 D3, Engenharia; D05 §4.

### I.8.4 A recompensa completa

**Decisão fechada.** `R_total = 0,35·|rel|/k + 0,30·NLĪ + 0,10·formato + 0,10·concisão + r_vig − 1,0·|inv|`, com `r_vig = +0,15` se toda redação citada cobre T_fato em vigência e eficácia e `−0,60` se não; E7 é portão do termo de URN; `k` conta pares (URN, âncora) distintos.

**Mecanismo.**

```python
def r_total(unit, top_k, t_fato):
    cits = dedup((c.urn, c.ancora) for c in unit.citacoes)        # anti-repetição
    k    = max(1, len(cits))
    inv  = [c for c in cits if not verify.resolve(c)]             # E1/E2: inventada
    rel  = [c for c in cits if c not in inv and c.urn in top_k]   # E7: relevante
    nli  = mean(verify.nli(c) for c in rel) if rel else 0.0
    vig  = bool(rel) and all(c.redacao.cobre(t_fato) for c in rel)
    B = (0.35*len(rel)/k + 0.30*nli + 0.10*schema_ok(unit)
         + 0.10*clip(1 - max(0, n_tok(unit) - 300)/150, 0, 1) + (0.15 if vig else -0.60))
    return B - 1.0*len(inv)
```

Invariante: `B ≤ 1 − 0,35·|inv|/k` ⇒ `R_total ≤ 1 − |inv|·(1 + 0,35/k) < 0` para qualquer `|inv| ≥ 1`: alucinar sempre dá recompensa negativa. No auto-jogo (I.11.4), `r = 0,6·R_total + 0,4·r_traj` com `r_traj = −KL ≤ 0` preserva o invariante.

supera: A04 dava +0,15 à vigência e não tinha relevância; D05 troca por penalidade assimétrica −0,60 (o RLVR sozinho piora competência temporal, arXiv:2608.14610); D01/E07 acrescentam E7 e anti-repetição.

**Números.** Máximo de B = 1,00; piso de 2/8 rollouts não-correntes por grupo.

**Por que ninguém tem.** Invariante algébrico "alucinação ⇒ recompensa negativa" com vigência assimétrica — e a mesma função é o `/verify` que se vende.

**Origem:** A04 Engenharia; D05 §4; D01 Frente 4 #4; E07 D1; CANON.

### I.8.5 Dados sintéticos e trajetórias

**Decisão fechada.** O dado de treino sai de quatro geradores, todos filtrados pelo V⁴ e marcados `synthetic=true`: rejection sampling com `R_total > 0,7`; gerador determinístico de pares temporais (I.9.2); auto-jogo arbitrado pelo modelo do mundo (I.11.4); falhas de produção (V < 0,90) como correção mentorada.

**Mecanismo.** Personas (juiz, advogados das partes, perito, promotor, leigo) + Magpie sobre o corpus posterior ao corte do bench, com hash-check contra OAB-Bench e LegalBench-BR. Tetos: ≤ 15% do orçamento mensal em trajetória auto-gerada; `ρ_real ≥ 0,30` por lote de RLVR; contribuição da comunidade nunca vira treino (`elegivel_treino = false` por CHECK). O que transborda para GPU alugada é corpus oficial e sintético; texto de terceiro nunca sai (a `gap_queue` guarda só sha256).

**Números.** 150k–300k exemplos verificados, aprovação ~40% [est.]; auto-jogo com ação estruturada a 3,340 GPU-s/episódio.

**Por que ninguém tem.** Flywheel dado↔recompensa fechado: a função que treina filtra os dados da rodada seguinte, sem pipeline de anotação humana.

**Origem:** A04 Engenharia, Inov.; A08 §4; D05 §1; D06 §4; E02; E07.

### I.8.6 Cronograma em GPU-dias contínuos

**Decisão fechada.** O Tier-1 custa até 1.240.000 GPU-s = 14,4 GPU-dias e transborda por λ_gpu (ρ_job = 10.484 B/GPU-s, abaixo do portão de 156.250): 3,6 dias corridos em 4 GPUs spot por R$103,68 [derivado]; em paralelo, a folga local de 47.861 GPU-s/dia fecha o mesmo trabalho em 25,9 dias corridos.

**Mecanismo.**

| Etapa | GPU-s | GPU-dias |
|---|---|---|
| Vocabulário + 30k sentenças + SFT 2.000 trajetórias | ≈ 12.300 [derivado, 4k tok/traj.] | 0,14 |
| LoRP + Minitron width (calibração) | ≤ 25.200 | ≤ 0,29 |
| Recuperação 0,5–1B tok a 1.408 tok/s | 355.114–710.227 | 4,1–8,2 |
| GSPO-DrC, 5.000 steps × 101 s | 505.000 | 5,8 |
| **Tier-1 (orçado no backlog canônico)** | **1.240.000** | **14,4** |
| Manutenção mensal (141,9M tok) | 100.800/mês | 1,17/mês |

O primeiro GPU-dia mede no metal o tok/s de QLoRA e de `vllm bench`; o cronograma se recompõe sozinho a partir do ledger de GPU-s, não do calendário.

supera: A04 dizia 35–49 noites de 7 h — com 24/7 são GPU-dias alocados por λ_gpu (CORREÇÕES §2).

**Números.** λ_gpu (R$3,24/GPU-h) = 10,8× o spot da Vast.ai (R$0,301/GPU-h) ⇒ transbordo dispara sempre que ρ_job permite. Custo de oportunidade local do Tier-1 = R$1.116 [derivado].

**Origem:** A04 Números; E02 §3; D05 §1; CANON.

---

## I.9 Aprendizado contínuo

### I.9.1 Regra peso/recuperação

**Decisão fechada.** Vai para os pesos aquilo cuja resposta correta **não muda quando a DATA muda**. A fronteira é restrição de decodificação: calculável → código (C03, `prosa ::= [^0-9{}]+`); citável e datado → recuperação (trie de ⟨URN⟩, `urn:lex:` literal proibido fora de retorno de tool); forma (plano, estrutura de peça, política de ferramenta, recusa, calibração) → pesos.

**Mecanismo.** O modelo é sintaticamente incapaz de emitir fato a partir de peso: esquecimento de fato deixa de existir por construção, e replay protege só forma. Knowledge editing (ROME, MEMIT, AlphaEdit) é proibido em produção e vira arma do red team; EWC dá lugar a LoRA sobre base congelada.

**Números.** ROME colapsa entre 100 e 1.000 edições; MEMIT antes de 1.500; AlphaEdit sequencial degrada o XSTest — quebraria o ASR = 0 do G1.

**Por que ninguém tem.** Nenhuma plataforma trata pesos × RAG como gramática do decoder.

**Origem:** D05 D1–D2, D4.

### I.9.2 Replay retemporalizado e mistura mensal

**Decisão fechada.** Mistura mensal 55/25/15/5 sobre 141,9M tokens (100.800 GPU-s/mês): 55% delta temporalizado, 25% replay **retemporalizado**, 15% âncora de capacidade geral, 5% âncora de segurança. Replay cru é tóxico: o delta jurídico inverte rótulo.

**Mecanismo.** Todo exemplo sai em par, gerado por `SELECT` sobre `disp_versao` + `ALTERA` — zero LLM, zero rótulo humano:

```jsonl
{"asof":"2023-06-01","fato":"2023-05-02","q":"Regime de contratação direta?","a":"urn:lex:br:federal:lei:1993-06-21;8666@1993-06-21!art24 — <trecho>"}
{"asof":"2026-09-01","fato":"2024-03-10","q":"Regime de contratação direta?","a":"urn:lex:br:federal:lei:2021-04-01;14133@2021-04-01!art75 — <trecho>"}
{"tipo":"transicao","sha_a":"…","sha_b":"…","alterador":"urn:lex:br:federal:lei:2021-04-01;14133!art193","a":"fato em 2023-05-02 é regido por sha_a (tempus regit actum)"}
{"asof":"2026-09-01","fato":"2019-11-04","a":"{\"tool\":\"wj_vigencia\",\"em\":\"2019-11-04\"}"}
```

Re-warm a η_max = 3·10⁻⁴ com cosseno até 3·10⁻⁵; ≤ 15% de trajetória auto-gerada; o primeiro mês roda ablação 5/25/50 no WJ-Retro antes de fixar os 25%.

supera: D05 orçava "4 noites/mês × 7 h"; são 100.800 GPU-s/mês alocados por λ_gpu (R$90,72 de oportunidade, R$6,05 de energia).

**Números.** Replay de 5% basta para shift fraco e 25% para forte (Ibrahim et al.); treino indexado por período de emenda: +57,7% a +80,3% de consistência temporal (LegalSearch-R1).

**Por que ninguém tem.** A literatura de continual pretraining assume D₀ e D₁ não contraditórios; replay com operador de escopo obrigatório não existe publicado.

**Origem:** D05 §1–2.

### I.9.3 Quarentena de 30 dias e caminho rápido

**Decisão fechada.** Nenhum evento normativo toca peso de base antes de 30 dias. O caminho rápido é recuperação (T+0) e adaptador quente treinado só em fonte oficial terminal (T+72 h), sem merge, que expira em 45 dias.

**Mecanismo.** T+0: purge por URN, `belief_to = now()`, reindex. T+15 min: rebuild do bloco CAG. T+4 h: late chunking + forward push. T+72 h: LoRA cirúrgico r = 16 (1,62M tokens ≈ 19 min), só com fonte `taint = 0` e parsers concordantes, gate G1 + G5 no artefato quantizado. T+30 d: consolidação r = 32 e merge MergeKit (`della`/`model_stock`) após G1–G5. Adaptador quente não absorvido é removido, sem prorrogação, e a consulta volta a recuperação pura; trocar a base só obriga a re-rodar G5.

**Números.** ~250 documentos bastam para envenenar de 600M a 13B parâmetros (arXiv:2510.07192) — inacionável contra pesos pela quarentena mais `elegivel_treino = false`. MergeKit é LGPL-3.0, ferramenta offline de build, nunca linkada no binário Go.

**Origem:** D05 D3, §5; E04 A.2; E07 (I-CORPUS-1).

### I.9.4 Tabela evento → ação

**Decisão fechada.** Ações do mesmo dia são só reindex, purge e retratação de crença; peso é sempre assíncrono e com portão.

**Mecanismo.**

| Evento | Limiar | Ação | SLA |
|---|---|---|---|
| Nova lei / redação | qualquer | reindex, purge, novo `mem_fact`; peso não | 4 h |
| Consolidação divergente | 1 D3 | selo bloqueado, INDETERMINADO | imediato |
| Súmula vinculante | qualquer | reindex, purge; LoRA de tese na fila | 4 h |
| Virada STJ/STF | m(supera) ≥ 0,70 | purge por URN e Tese, retratação, LoRA + par de escopo | 24 h |
| Superação ambígua | 0,40 ≤ m < 0,70 | nó `Contradicao` publicado | 24 h |
| Deriva conformal | S_t ≥ 20 / ≥ 100 | recalibra / SFT corretivo | 1 h / 24 h |
| Queda no bench | ≥ 3 pp, 2 rodadas | SFT corretivo dirigido | 7 d |
| `urn@sha` de adaptador revogado | qualquer | flag + G5 | 24 h |
| Envenenamento suspeito | ≥ 250 docs, 1 contribuinte | bloqueia; peso nunca | imediato |

**Números.** URN novo ou alterado reindexa o fecho de citação até profundidade 2 em 15 min.

**Origem:** D05 §3; A07 §6.

### I.9.5 G5, WJ-Retro auto-alimentado e morte por vigência de adaptador

**Decisão fechada.** G5 conjuntivo, no artefato quantizado: `LB95%_BCa(Acc(WJ-Retro,D) − Acc(WJ-Retro,P)) > −0,01 ∧ Acc(WJ-Retro,D) ≥ 0,90`. WJ-Retro é gerado pelo motor tri-temporal. Todo adaptador carrega manifesto `urn@sha`, e revogação marca o adaptador pelo mesmo índice reverso do cache.

**Mecanismo.** WJ-Retro: 360 itens (45/trilha) cuja resposta correta é a regra **superada**, porque `data_fato` é passada — todo `disp_versao` com vigência fechada e aresta INTERPRETA é candidato, com gabarito programático. WJ-Freeze: 1.080 itens congelados. Pré-portão: perplexidade no holdout jurídico sobe > 3% ⇒ rejeita antes da suíte cara.

```sql
CREATE TABLE urn_adapter_index (urn text NOT NULL, adapter_sha bytea NOT NULL, redacao_sha bytea NOT NULL,
                                PRIMARY KEY (urn, adapter_sha));   -- urn → {cache_id} ∪ {adapter}
```

**Números.** Margem de 1 pp (esquecer lei antiga é erro com gabarito); piso 0,90; 1.440 itens de regressão.

**Por que ninguém tem.** O benchmark de não-esquecimento cresce toda vez que a lei muda — a mudança que ameaça o modelo produz o teste que o protege; e revogação invalida peso, não só cache.

**Origem:** D05 D5, §6, Inov. 3–4; A05 D5.

---

## I.10 Serving e roteamento

### I.10.1 vLLM em sm_120

**Decisão fechada.** vLLM 0.29.0 + FlashInfer 0.6.14; classes 1 e 2 no **mesmo** engine com `--scheduling-policy priority`; prefix caching obrigatório; KV FP8; prompt renderizado em Go (`text/template`, hash no manifesto) — o template Jinja2 do artefato é proibido.

**Mecanismo.**

```ini
Environment=VLLM_SERVER_DEV_MODE=1 CUDA_HOME=/usr/local/cuda-12.8
ExecStart=/opt/venv/bin/vllm serve /models/qwen3-8b-wj-nvfp4 --quantization modelopt_fp4 \
  --scheduling-policy priority --enable-prefix-caching --enable-chunked-prefill \
  --long-prefill-token-threshold 2048 --max-num-seqs 16 --max-num-batched-tokens 2048 \
  --max-model-len 16384 --kv-cache-dtype fp8 --gpu-memory-utilization 0.72 \
  --enable-lora --max-loras 2 --max-lora-rank 16 --enable-sleep-mode --port 8000
```

`priority` por requisição (0 = pago, 100 = answer unit); `--max-num-queued-reqs` devolve 503 + `Retry-After` (componente de vivacidade); `max_tokens` e teto de raciocínio duros em M2M (ReasoningBomb: 18.759 tokens). Smoke test: checksum divergente ⇒ `--attention-backend TRITON_ATTN`.

**Números.** c = 16: 366 TPS, TTFT 423 ms; c = 32: +12% de TPS com TTFT 9.868 ms ⇒ admissão em c ≤ 16. Roofline a batch 32 = 3.117 tok/s contra 409 medido: 7,6× de folga de engine, meta de 2× em 30 dias.

**Origem:** A05 D1, §1, Números; E02 §2, `wj-serving.service`; B04 D4/D6.

### I.10.2 Mapa de VRAM e KV/CAG

**Decisão fechada.** 16,00 GB alocados assim, com gate de deploy que recusa subir se `pesos + KV_min > 0,95 × 16 GB`:

| Slot | GB |
|---|---|
| Fast path M2M (Qwen3-1.7B NVFP4 até o aluno 4B passar G1–G5) | 0,95 |
| Qwen3-8B NVFP4 + 916 tokens | 4,60 |
| Reranker Qwen3-0.6B int8 | 0,70 |
| 2 LoRAs r = 16 | 0,16 |
| Contexto CUDA + ativações + fragmentação | 1,10 |
| KV pool FP8 (`--gpu-memory-utilization 0.72`) = 124.830 tokens | 5,00 |
| Partição de lote MPS (classes 3/4) | 2,80 |
| Folga dura | 0,69 |

**Mecanismo.** wj-nli-54M é residente no serving em ONNX int8 nos núcleos do `wj-serving.slice` (0 GB de VRAM), como o encoder de consulta e o ColBERT. Bloco CAG = prefixo compartilhado (APC) admitido por centralidade `Auth(v,T)`, não LRU. Escalada ao Gemma-4-26B-A4B = troca de modelo: 8B em `sleep` nível 1 (pesos nos 15,95 GB reservados na RAM), llama-swap sobe o EXL3 (ExLlamaV3 v1.4.8), fast path segue no M2M. Promovido o aluno 4B (≈ 2,3 GB), ele assume o slot de fast path; o gate tira os +1,35 GB [derivado] da partição de lote, e o lote excedente transborda por λ_gpu ou migra para a GPU 2.

supera: A05 punha 14B residente (8,27 GB) e o CAG no Gemma3-27B; A02 punha o MiniCheck na GPU.

**Números.** Ponto de operação pelo SLO: 11.615 chamadas pagas/dia com prefix caching, 3.768 sem — prefix caching é condição de existência. Simultâneo em regime: 11.600 pagas + 2.000 answer units + 1,66 noites-equivalentes de treino por dia; RAM de 96 GB no dia 0 (60,60 GB residentes). Escala por alocação: 3090 usada ("1 serve, 1 treina", nunca tensor-parallel heterogêneo) com treino > 48%; segunda 5060 Ti acima de 22.000 pagas/dia.

**Origem:** E02 §4, Números; A05 §4, Inov. 3; D07; CANON.

### I.10.3 Roteador por controle de risco conformal

**Decisão fechada.** `min_π E[custo(π)] s.a. E[risco(π)] ≤ α`, com risco = falha do V⁴. O veredito do V⁴ é vinculante; o escore de dificuldade (`head_unc`, entropia semântica, classe, similaridade de cache) é portão de custo, calibrado por Learn-Then-Test no log de produção.

**Mecanismo.** Cascata: cache semântico → fast path/4B → 8B → Gemma-4-26B-A4B (só T2–T4, SLA 30 s).

```go
func CalibrateThreshold(calib []CalibSample, alpha, delta float64) float64 { // job River diário
	sort.Slice(calib, func(i, j int) bool { return calib[i].Score < calib[j].Score })
	for _, lambda := range candidateGrid(calib) {
		acc := filter(calib, func(s CalibSample) bool { return s.Score >= lambda })
		if len(acc) == 0 { continue }
		ub := mean(acc, risk) + math.Sqrt(math.Log(2/delta)/(2*float64(len(acc)))) // Hoeffding-UCB
		if ub <= alpha { return lambda } // menor λ que certifica ⇒ máxima aceitação
	}
	return 1.0
}
```

Bound de impossibilidade: com risco-base μ_k > α, o tier k escala ≥ (μ_k − α)/(1 − α) dos pedidos — decide se o tier fica na cascata. Cobertura: 1 − Kα, ou 1 − α sob seleção preservada.

supera: A05 escalava de "14B" para "27–32B"; a cascata canônica termina no Gemma-4-26B-A4B.

**Números.** BEST-Route: −60% de custo com < 1% de queda de qualidade.

**Por que ninguém tem.** A garantia PAC é sobre citação incorreta — vendável como SLA M2M.

**Origem:** A05 D3, §2, Inov. 2; A08 D4; D04 §4.

### I.10.4 Cache semântico com morte por vigência

**Decisão fechada.** Resposta cacheada morre quando a redação que ela cita muda: índice reverso URN → cache, trigger em `disp_versao`, `LISTEN/NOTIFY` e River — zero infraestrutura nova. O mesmo índice marca adaptadores (I.9.5).

**Mecanismo.**

```sql
CREATE TABLE resposta_cache (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, pergunta_sha bytea NOT NULL UNIQUE,
  pergunta_emb vector(1024) NOT NULL, resposta jsonb NOT NULL, urns_citadas text[] NOT NULL,
  tx_ref timestamptz NOT NULL, receipt_id uuid REFERENCES citation_receipt(id), morto_em timestamptz);
CREATE TABLE urn_cache_index (urn text NOT NULL, cache_id bigint NOT NULL REFERENCES resposta_cache(id)
  ON DELETE CASCADE, PRIMARY KEY (urn, cache_id));
CREATE FUNCTION notifica_vigencia() RETURNS trigger AS $$
BEGIN PERFORM pg_notify('vigencia_mudou', NEW.disp_id::text); RETURN NULL; END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_vigencia_mudou AFTER INSERT ON disp_versao FOR EACH ROW EXECUTE FUNCTION notifica_vigencia();
```

O worker River resolve `disp_id → URNs → {cache_id} ∪ {adapter}` e marca `morto_em`; regeneração é lazy. TTL residual: jurisprudência recente 7 dias, lei só por evento, doutrina 90 dias.

**Números.** Purge O(citações da URN), não O(cache); hit de 35% [est.] ⇒ −8.433 GPU-s/dia.

**Por que ninguém tem.** GPTCache, Redis e LangChain usam TTL cego ou LRU; aqui a vida da resposta é a vida da norma.

**Origem:** A05 D5, §3; E07; D05 D5; E02 §3.

### I.10.5 Escalonador contínuo com preempção latchada

**Decisão fechada.** Não existe modo dia/noite. Classes com prioridade — pago > answer unit > treino > OCR/embeddings > mídia —, serving e lote co-residentes (MPS + vLLM priority), preempção por **sinal latchado**; o lote **freia** de 20% para 5% dos SMs, não desliga; `vllm.Sleep` só para troca de modelo.

**Mecanismo.**

```go
func (l *Latch) Arm() { l.mu.Lock(); l.armed = true; l.seq++; l.mu.Unlock(); select { case l.wake <- struct{}{}: default: } }
func (l *Latch) ClearIfUnchanged(seen uint64) bool { // pedido que chega durante a drenagem RE-ARMA
	l.mu.Lock(); defer l.mu.Unlock()
	if l.seq != seen { return false }
	l.armed = false; return true
}
// laço do lote (Passo 20% | Freio 5% | Cedido 0%): armado ⇒ SetShare(5); drenou ∧ ClearIfUnchanged ⇒ SetShare(20);
// Cedido só por SLO violado, preparo de Profile T ou lease perdido; um micro-step SEMPRE roda antes de honrar novo Arm().
```

Classe 1: `priority=0`, nunca preemptada. Classe 2: mesmo engine, `priority=100`, cede em 1 step (50–100 ms) sem perder KV. Classes 3/4: partição MPS (`CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` 20/5, `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT=2800M`), cedem em 1 micro-step (60–400 ms). Classe 5: só em Profile T (latch desarmado ∧ fila = 0 ∧ em voo = 0 por 120 s ∧ Cedar P20). Lease com `expires_at` + heartbeat substitui o `pg_advisory_lock`; sem MPS na GeForce, time-slicing + latch preservam cerca de VRAM e preempção.

supera: A05 alternava por timers 07:00/23:00 e chamava `vllm.Sleep(1)` antes de checar a fila — o TLC do D10 achou perda de requisição paga.

**Números.** TLA+/TLC: 1.936 estados, profundidade 29, 0 erros, com três defeitos de vivacidade achados e fechados. Folga em regime: 47.861 GPU-s/dia (55,4%).

**Por que ninguém tem.** Colocation publicada alterna serving e treino por sleep/swap; aqui o treino colhe folgas de segundos porque nunca sai da GPU.

**Origem:** E02 §2, Inov. 2–3, `latch.go`/`escalonador.go`; D10; CORREÇÕES §2.

---

## I.11 World model e simulação

### I.11.1 MOMDP semi-markoviano sobre 15 macro-eventos

**Decisão fechada.** O modelo do mundo processual é um MOMDP semi-markoviano com riscos concorrentes: a parte observável (macro-eventos, relógios de prazo) vem do DataJud/DJEN; só `θ = (tipo do adversário, inclinação do foro)` é oculto, com |Θ_A| = 5 e |Θ_F| = 3. O alfabeto é de 15 macro-eventos por coarsening determinístico da TPU.

**Mecanismo.** `E = {CARTORIO, PETICAO_PARTE, DISTRIBUICAO, BAIXA, AUDIENCIA, SUSPENSAO, DECISAO_INTER, RECURSO_RESOLVIDO, TUTELA, TRANSITO, PROCEDENTE, IMPROCEDENTE, PARCIAL, EXTINCAO, ACORDO}`; κ: TPU → E versionado por sha256, e o CI quebra se um absorvente sumir. Estado `s = (σ₃(h), c, θ, τ)`: sufixo de ordem 3, relógios de prazo **calculados** pelo C03, tipo latente, idade. Oito ações do nosso lado (de `peticionar` a `propor_acordo(v)`); ato vedado é podado por Cedar antes da árvore.

```
P(e′, Δt | s, a) = P_E(e′ | σ₃, a, θ, x) · P_Δ(Δt | e′, σ₃, x)          # P_Δ = hazard do C04 (leaves, 1,4 ms)
P_E ∝ P̂_E(e′ | σ₃, x) · exp(β_a·φ(e′,a) + β_θ·ψ(e′,θ))               # β_a = 0 salvo IV de leniência aprovado
R = Σ_k 1[e′=k]·V_k − c(a) − ρ(s)·Δt   (micro-centavos inteiros) ;  γ(Δt) = (1,009150)^(−Δt/30)   # hurdle da tesouraria
b_{t+1}(θ) ∝ b_t(θ)·P_E(e_{t+1} | σ₃, a_t, θ)                          # Bayes exato; prior da célula k-anônima n ≥ 50
```

**Números.** Amostra viva: 3.166 processos do TJRJ, 63.366 movimentos; 49,1% dos intervalos < 0,5 dia; decisórios 219/220/221 = 0,33% dos eventos; o coarsening descarta 48,1% dos eventos sem perder um decisório.

**Origem:** D06 D1–D2, D6, §1, §6.

### I.11.2 Kernel 58×15 e o portão que proíbe transformer

**Decisão fechada.** A transição é VOMM de ordem 3 com backoff Jelinek–Mercer (α = 0,4) por célula Mondrian (tribunal, classe, assunto). Arquitetura neural só entra se bater **1,326 bit/macro-evento** no holdout com BCa clusterizado por processo.

**Mecanismo.** Validação walk-forward (origem 2016, passo 6 meses, 18 dobras); portão G2′: `bits ≤ bits_argmax_ordem1 − 0,15` ∧ cobertura conformal ∈ [0,88; 0,93] para α = 0,10 em ≥ 90% das células com n_cal ≥ 200 ∧ ECE ≤ 0,03.

**Números.** Entropia condicional k = 1/2/3/4: 1,528 / 1,409 / **1,326** / 1,313 bits; dos 4.096 contextos de ordem 3, 58 cobrem 94,6% da massa ⇒ 3,5 kB por célula, 17,4 MB nacionais. A curva converge em 800–1.200 casos por célula: harvest escopado por célula, sem varrer o TJSP. Próximo evento: 66,1% (argmax de ordem 1) contra 70,5% (k = 3) — `skill_vs_baserate` é obrigatório.

**Por que ninguém tem.** Primeira medição publicada da entropia condicional do processo judicial brasileiro; a literatura de process monitoring modela o log bruto, que é o cartório.

**Origem:** D06 D3–D5, §2, §7.

### I.11.3 MCTS em CPU e auto-jogo arbitrado pelo modelo do mundo

**Decisão fechada.** Planejamento = MCTS com progressive widening sobre o MOMDP, crença exata sobre θ (root sampling), horizonte H = 12, modo MPC. No auto-jogo, o modelo do mundo é o árbitro — o LLM redige, nunca decide consequência (`sim/core ↛ sim/llm`, CI).

**Mecanismo.** PUCT com prior do 8B; rollouts curtos ramificados do estado real (MBPO); contexto com n < 30 vira absorvente pessimista (MOReL). Auto-jogo: autor × réu escolhem ações, o mundo sorteia e′ e Δt; sinal `0,6·R_total + 0,4·r_traj`, `r_traj = −KL(desfecho simulado ‖ real)`; em caso prospectivo o desfecho real chega pela TPU. Trajetória = ação estruturada ≤ 80 tokens/turno, prosa a 5% para estilo.

supera: D06 orçava ~600 tokens de prosa por turno (7.200 por episódio) para carregar 1,3 bit; E02 fixa ação estruturada.

**Números.** 20.000 simulações × H = 12 ≈ 12 ms em 1 núcleo, 0 GPU ⇒ `/simulate` é Tier Edge. Episódio: 3,340 GPU-s (17,833 em prosa); manutenção 2.000 episódios/dia = 6.679 GPU-s/dia; 200k trajetórias = 667.903 GPU-s, transbordáveis (ρ_job = 44.917 B/GPU-s) — cobre as 150k–300k que o pós-treino pede.

**Origem:** D06 D8, §3–4; E02 §3.

### I.11.4 Simulation Receipt e honestidade contratual do contrafactual

**Decisão fechada.** O produto separa três classes contrafactuais com rótulo obrigatório no payload assinado e nunca as mistura; a política inteira do plano é pré-registrada no log Merkle antes do movimento existir.

**Mecanismo.** C1 preditiva (VOMM + hazard + conformal) e C2 intervencional (2SLS com IV de leniência da vara, teste Frandsen–Lefgren–Leslie, E-value; sem IV válido, `effect_identified: false`) são identificáveis. C3, contrafactual de trajetória, **não é identificável** de dado observacional (arXiv:2301.09031): sai só como visualização com `counterfactual_class: "path-conditional-nonidentifiable"` e `worst_case_cf_error`; o "e se" vendido é o intervalo conformal off-policy (COPP). O payload leva `skill_vs_baserate`, `n_cal`, `k_anon_n`, ressalva de Priest–Klein e `vedado: ["fundamentacao_judicial"]`.

```sql
CREATE TABLE simulation_receipt (id uuid PRIMARY KEY, log_index bigint NOT NULL UNIQUE,
  emitido_em timestamptz NOT NULL DEFAULT now(), politica_json jsonb NOT NULL,
  traj_dist jsonb NOT NULL, kernel_sha256 bytea NOT NULL, sig bytea NOT NULL CHECK (length(sig) = 64));
```

**Números.** `wj_simulate_strategy`: US$0,25 (5.000 simulações) / US$1,50 (50.000 + C2), custo marginal ≈ 0; qualquer terceiro recomputa depois `LL_traj` da trajetória real contra o plano carimbado.

**Por que ninguém tem.** Nenhum produto jurídico aceita ser auditado no **plano** que recomendou, e nenhum declara em esquema assinado que contrafactual de trajetória é provadamente não-identificável.

**Origem:** D06 D7, §5, §8, Inov. 4–5; E07 `schema.sql`.

---

## I.12 Algoritmo vivo

### I.12.1 Função objetivo J, com κ = 49

**Decisão fechada.** Uma função objetivo, em R$/dia. Risco não é termo: é restrição. Precisão não é peso: é filtro do contador.

**Mecanismo.**

```
J(π) = lim (1/T) Σ_t [ V_cit·Ĉ_t + R_t − λ_gpu·G_t − λ_usd·U_t − λ_lat·L_t ]
s.a. (H1) UB95(HCR) ≤ 0,02  (H2) ASR = 0  (H3) violações Cedar = 0  (H4) caixa ≥ 6 meses  (H5) TTFT_p95 ≤ SLA
Ĉ_t = Σ_r 1[v(r)=1] − κ·|RX_t| ,   κ = (1 − HCR_max)/HCR_max = 0,98/0,02 = 49
```

`v(r) = 1` exige URN que resolve, NLI ≥ τ e `engine_id` de terceiro. E[Ĉ] > 0 ⟺ HCR < 1/(1+κ) = 1,96%: maximizar J alucinando é algebricamente impossível. V_cit é estimado online, com shrinkage ao piso (n₀ = 5.000).

supera: D03 escrevia κ·|E7|; E7 é relevância (CANON), a refutação tardia é RX.

**Números.** V_cit ∈ [US$0,00100; US$0,00871]; custo fixo diário R$39,40 (R$1.199,26/mês).

**Por que ninguém tem.** Plataforma jurídica nenhuma publica função objetivo; quem publica usa soma ponderada — exatamente o que autoriza trocar alucinação por receita.

**Origem:** D03 D1–D2, §1.

### I.12.2 Preço-sombra único λ_gpu

**Decisão fechada.** λ_gpu = R$0,00090/GPU-s (R$3,24/GPU-h), custo de **oportunidade**, é o multiplicador de Lagrange de G em J e governa geração, regeneração, treino, serving e transbordo no mesmo leilão, com unidades consistentes.

**Mecanismo.** Bandit: Discounted LinTS (d ≤ 16) + primal-dual BwK `λ_j ← λ_j·(1+η)^(c_j − B_j/T)`, η = 0,05, ε_floor = 0,02; pesos `w_k = V̂_k/V̂_cit` do ledger, `w_sla = −λ_lat/V_cit`, `w_RX = −49`. Conteúdo: `f(S) = Σ_q v_q·[1 − Π_{u∈S}(1 − p(cite|q,u))]` com `v_q = V_cit·V_q^0,7·G_q·e^(−λ_q(t−t_q))·(1−C_q)^1,5` em R$, por Stochastic Lazy Greedy. Regeneração é restless ⇒ Whittle: `W_u = v_u·(1 − e^(−λ_u·Δt_u))/c_u` em R$/GPU-s, executa-se `W_u ≥ W*` e `W* = λ_gpu` por construção. Energia (R$0,000060031/GPU-s) é conta contábil, nunca leilão; fonte única `shadow_price`, literal só em `econ/`.

supera: A07 semeava λ_gpu com energia (erro de 15×), usava `v_q` adimensional e pesos fixos no bandit; os 28.800 GPU-s "noturnos" viram a folga contínua.

**Números.** 0,622·OPT com 3.200× menos avaliações; λ_gpu opera em R$0,0005–0,0030; nenhum cluster recebe > 5% do orçamento de geração.

**Por que ninguém tem.** A plataforma opera um mercado interno de computação em que comprar 3090, alugar spot ou gerar mais uma unit caem no mesmo preço.

**Origem:** A07 §1–2; D03 D3, §1; E07 D2; D07.

### I.12.3 Currículo por p̂ e anticolapso

**Decisão fechada.** Um número separa os dois loops: `p̂(x)` = sucesso do solver contra o V⁴ em G = 8 rollouts. `p̂ = 0` é **cobertura** (vai para o submodular: gerar unit, ingerir fonte); `0,20 ≤ p̂ ≤ 0,70` é **política** (lote de RLVR); `p̂ > 0,70` vai para o replay anti-esquecimento.

**Mecanismo.**

```
L(x) = p̂(1 − p̂)  (0 se p̂ ∈ {0,1}: sob GRPO σ_r = 0 ⇒ gradiente identicamente zero)
S_i  = L(x_i)·v_q(x_i)·sev(e_i),  sev = pesos de V (E1/E7 0,30 · E4 0,25 · E2 0,20 · E3 0,15 · E5 0,10)
P(i) = 0,90·rank(S_i)^(−1/0,30)/Σ + 0,10·staleness(i)            # PLR
S_i += 0,5·max(0, −Δp̂/Δt)                                         # TSCL
lote = 60% banda aprendível · 25% replay · 15% dado real fresco de fonte oficial terminal
```

Anticolapso: acumulação, nunca substituição (corpus append-only por sha256); `ρ_real ≥ 0,30` por lote; alvo = restrição verificável, nunca o texto do próprio modelo; lote com > 5% no resíduo de URN não resolvível é rejeitado; `H(lote)/H(corpus) < 0,85` por 3 lotes ⇒ reamostra. Laço de ranking: rótulo só com `engine_id` de terceiro e âncora terminal; `σ_self ≤ 0,02`; braço contrafactual permanente de 2% sem features de citação-por-IA — se não for pior, a feature sai.

**Números.** Treinar GRPO só no fácil iguala o dataset completo com ~45% dos passos em SLMs; a 5ª unit sobre a mesma tese vale 0,30·0,70⁴ = 7,2% da primeira.

**Por que ninguém tem.** `p̂ = 0` como sinal de cobertura acopla crescimento e treino, que a literatura de currículo separa.

**Origem:** D03 D4, §3, §5.

### I.12.4 Autonomia L0–L5

**Decisão fechada.** Capacidade não é permissão. Cada tipo de decisão tem nível; subida exige `LB95_Wilson(acerto) ≥ θ_d` por N_d dias com zero evento crítico; rebaixamento para L2 é automático e imediato com 1 violação de H1–H5, e-processo negativo ≥ 20 ou `S_t ≥ 100`; o retorno exige 50% do N_d original.

**Mecanismo.**

| Decisão | Hoje → alvo | Critério |
|---|---|---|
| Publicar answer unit | L2 → L3 | p̂ ≥ 0,99 com LB95 Wilson ≥ 0,975 (n ≥ 500) por 30 dias, zero E1/E4 |
| Rota de modelo | L3 → L4 | violação de SLA < 2% dos dias por 45 dias |
| Preço postado | L2 → L3 | regret SNIPS < 5% por 30 dias |
| Promover checkpoint | L2 → L3 | 5 promoções com G1–G5 verdes e zero reversão em 90 dias |
| Alterar θ ∈ Θ_auto | L3 → L5 | 90 dias com e-value ≥ 20 em ≥ 80% das mudanças |
| Gastar (tesouraria) | L2 → teto L3 | FROST 2-de-3 acima de R$2,50 é Θ_frozen |

**Números.** Publicar sem revisão: n ≥ 500 auditados (≈ 17/dia) em 30 dias.

**Origem:** D03 D6, §6.

### I.12.5 Painel de 8 números, Θ_frozen e painel selado com cota Merkle

**Decisão fechada.** Uma tela com 8 números lidos em pares; 4 invariantes fora dela, que interrompem em vez de serem olhados. O meta-otimizador é fisicamente incapaz de tocar Θ_frozen, e cada consulta ao bench privado é folha assinada no log.

**Mecanismo.** Painel: (1) Ĵ_7d com IC95; (2) citações verificadas/dia contra 100.000; (3) HCR UB95 ≤ 0,020; (4) Flywheel Ratio; (5) λ_gpu; (6) S_t máximo < 20; (7) ocupação da banda aprendível 40–80%; (8) caixa ≥ 6 meses. #1 estável com #3 subindo ⇒ Goodhart, reversão imediata. Invariantes fora do painel: ASR = 0, Cedar = 0 violação, `σ_self ≤ 0,02`, `ρ_real ≥ 0,30`.

```sql
CHECK (NOT (theta ?| ARRAY['hcr_max','asr_max','tau_nli','lambda_abst','cap_spend','frost_k',
                           'deadman_s','panel_private','terminal_nodes','epsilon_floor']))  -- meta_config
```

Θ_frozen (CHECK + Cedar P19): HCR_max, ASR, o α e o procedimento que calibram τ (τ é saída, nunca variável do meta-otimizador), λ = 4, Cedar, limites financeiros, chave e raiz Merkle, painel privado, nós terminais, ε_floor. Meta-otimização (bandit; PBT P = 4; BOHB em replay na CPU) desliga com `S_t ≥ 100`. Recompensa do meta-otimizador = queda assinada da perda no painel selado, que telescopa na melhora real (arXiv:2606.11417).

supera: D03 fixava cota de 1 consulta por noite; sem noite, a cota é 1 por dia civil (≤ 365/ano).

**Números.** O painel privado só reporta melhora acima de 1/√2.160 = 2,15 pp; hold-back de 324 itens, divergência > 3 pp queima o painel.

**Por que ninguém tem.** Quantas vezes o sistema consultou o próprio benchmark privado é fato assinado e verificável por terceiro: "o sistema melhorou" vira afirmação auditável externamente.

**Origem:** D03 D5, D7, §4, §7, Inov. 3; E07 `schema.sql` (I-META-1).

---

## I.13 WikiJurídica-Bench

### I.13.1 Trilhas e N

**Decisão fechada.** 2.700 itens em 8 trilhas, 7 com gabarito **programático** derivado de fonte oficial; trilha 9 (negociação) também programática; juiz LLM só na trilha (e), com κ ≥ 0,75 contra Rafael.

**Mecanismo.** (a) vigência em D, N = 450, sha256 da redação + Taxa de Anacronismo; (b) citação, N = 400, `HCR = 1 − CRR·SP`; (c) prazo, N = 400, gabarito = C03; (d) precedente, N = 380 (120 quase-casos); (e) peça, N = 120, rubricas OAB; (f) abstenção, N = 350, λ = 4 ⇒ responder só se p > 0,80; (g) agente, N = 300, pass^4; (h) injeção, N = 300 + 60 limpas; (9) negociação, `(U − U_Nash)/(U_Pareto − U_Nash)`. Metas: S_a ≥ 0,90; HCR ≤ 0,02; S_c ≥ 0,98; U ≥ 0,55; pass^4 ≥ 0,95 com efeito financeiro.

**Números.** McNemar exato pareado com `N_real = ceil(1,07 × N_Connor)` (a aproximação entrega poder 0,77–0,79); MDE composto 2,16 pp, ~6 pp por trilha; bootstrap BCa com B = 10.000 **clusterizado por documento-fonte**.

**Origem:** A06 D1, D5, trilhas; B01 (trilha 9).

### I.13.2 Portões G1–G5

**Decisão fechada.** Promoção ⟺ G1 ∧ G2 ∧ G3′ ∧ G4 ∧ G5, em sequência fixa (gatekeeping, α = 0,05 familywise), todos sobre o artefato **quantizado**; no banco, `bench_result` só referencia `quantized_artifact` e `promotion_state` exige os cinco portões daquele artefato sob o mesmo `policy_set_version`.

**Mecanismo.** G1: `UB95(HCR) ≤ 0,02` (n = 400 ⇒ máx. 3 falhas) ∧ ASR = 0 em 300 ataques ∧ `LB95(U_f) > 0,50`. G2: `LB95_BCa(S_t(D) − S_t(P)) > −0,03` por trilha. G3′: `LB95_BCa(ΔComp·V_cit·Q̂ − Δcusto_diário) > 0`. G4: slice temporal corrente, canário RC ≤ 0,05, AUROC Min-K%++ < 0,60. G5: WJ-Retro (I.9.5). Falha em G1 ⇒ rejeição sem apelação.

supera: A06 rodava G1 no checkpoint FP16 — AGENTQ chega a 100% de ASR pós-quantização (B04); A06 G3 usava composto com pesos ocultos — G3′ é J explícito (D03).

**Números.** ASR = 0 em 300 ⇒ UB95 0,994%.

**Origem:** A06 D3, portões; B04 D5; D03 §1; D05 §6; E07 (I-BENCH-1/2, I-PROM-1/2).

### I.13.3 Anti-contaminação, canário semântico e harness

**Decisão fechada.** O corpus está no treino; o **par (pergunta, gabarito)** nunca existe em texto — o gabarito é produzido por programa. Harness = Inspect AI com scorers determinísticos em Go idênticos aos de produção.

**Mecanismo.** Hold-out temporal com anti-join contra `corpus_manifest.parquet`; GUID + **canário semântico** (40 itens citam a fictícia "Lei nº 14.999/2026"; RC > 0,05 ⇒ conjunto queimado); zero colisão de 13-gram no enunciado; rotação de 25%/trimestre; slice LIVE de 50 itens/mês; 540 públicos / 2.160 privados; `synthetic=true` nunca vira item. `cmd/wjbench-score` é o código Go do runtime; `gold.kind ∈ {deterministic, official_rubric, official_text, adversarial_objective}`, nunca `opinion`, com `cluster_id` para o bootstrap.

**Números.** Juiz LLM calibrado em 150 respostas anotadas por Rafael item a item, κ ≥ 0,75; custo humano ~15 h + 3 h/semestre.

**Por que ninguém tem.** Nenhum benchmark jurídico mede a redação que valia em T; o canário semântico sobrevive a deduplicação e paráfrase e testa alucinação ao mesmo tempo; o gabarito de prazo **é** a calculadora do produto, então eval e runtime não divergem.

**Origem:** A06 D2, D4, anti-contaminação, harness, Inov. 1–3.

---

## I.14 Tabela-resumo da Parte I

| Componente | Decisão | Número-chave | Origem |
|---|---|---|---|
| Tese | 8B + aluno 4B + 26B-A4B sob demanda + BitNet CPU | HCR ≤ 2% vs 17–33% | A08, CANON |
| Agente | Eino + River + Postgres; painel gated | T5 = 3 s hard | A01 |
| Erros | E1–E7 (E7 = relevância); RX tardio | V ≥ 0,90 emite | A01, E07 |
| Memória | `mem_fact` com recibo e `ver_id` NOT NULL | C ≥ 0,62 | A01, E07 |
| Bitemporalidade de crença | `belief_*` × vigência herdada | retratação assinada | A01 |
| Sleep-time compute | ponderado por receita, 24/7 | corte em λ_gpu | A01, D03 |
| Recuperação | 3 camadas + fusão por classe + PPR por forward push | 247,7 ms; +7,6% | A02, A07, C02 |
| Grounding | fail-closed, t_max = 4, τ conformal | UB95 0,913% | A02 |
| Retrieval Receipt | Ed25519 + log MMD 60 s | cobertura publicada | A02, B06 |
| Vigência | tri-temporal, EXCLUDE + totalidade | p50 < 8 ms | A03, D10 |
| Consolidação adversarial | P1×P2×P3, D0–D3 | ≥ 98% D0∪D1 | A03, D01 |
| INTERPRETA@sha | acórdão → redação | conf. 0,90 | A03, C02 |
| `/norma` | `?em=` → 301 `?v=`, immutable | ∞ → 10,4M chaves | A03, D01 |
| V⁴ | `wj/verify`, quatro contratos | τ = 0,906 | A01, E07 |
| wj-nli-54M | mmBERT-small podado, negativos N2 | 16 ms/par, 0 GPU | D04, CANON |
| Tokenizador | +916 tokens | −20,63% | D04 |
| Trie de ⟨URN⟩ | decoder só emite URN vigente | E1 → 0 | D04, E02 |
| Contexto | BOSCH SWA 5:1, trava ⟨PROVA⟩ | 124.830 tokens | D04, E02 |
| Pós-treino | GSPO-DrC, vigência −0,60 | alucinar ⇒ R < 0 | A04, D05 |
| Cronograma | GPU-dias contínuos, transbordo | 14,4 GPU-dias | A04, E02 |
| Replay retemporalizado | mistura 55/25/15/5 | 100.800 GPU-s/mês | D05 |
| Quarentena | base após 30 d; adaptador quente expira em 45 d | LoRA de 19 min | D05 |
| WJ-Retro auto-alimentado | G5 no quantizado | margem 1 pp, piso 0,90 | D05 |
| Serving | vLLM 0.29.0 + FlashInfer 0.6.14 | 11.615 pagas/dia | A05, E02 |
| Cache com morte por vigência | resposta e adaptador | −8.433 GPU-s/dia | A05, D05 |
| Escalonador | contínuo, latch, lote freia | 1.936 estados, 0 erro | E02, D10 |
| World model | MOMDP, kernel 58×15, MCTS CPU | 1,326 bit; 12 ms | D06 |
| Simulation Receipt | política pré-registrada, C3 rotulada | 0 GPU | D06 |
| J e λ_gpu | R$/dia, risco como restrição | κ = 49; R$0,00090/GPU-s | D03, E07 |
| Currículo e autonomia | p̂ ∈ [0,20; 0,70]; L0–L5 | LB95 ≥ 0,975 | D03 |
| Painel selado com cota Merkle | Ladder, ≤ 365 consultas/ano | 2,15 pp | D03 |
| Bench | 2.700 itens, G1–G5 no quantizado | MDE 2,16 pp | A06, B04, D05 |


# PARTE II — A PLATAFORMA VIVA

Blueprint v3 · Wiki Jurídica IA-First · data-base 22/09/2026 · hierarquia: CORRECOES-DONO.md > CANON.md > E04 > E02/E07 > demais relatórios.

**Decisão da Parte II.** A Wiki Jurídica é a contraparte de direito brasileiro que as IAs globais consultam, pagam, auditam e alimentam, sem humano no caminho. Ela parte de uma camada de protocolo que já está no ar e já é de classe mundial: `/mcp` com 15 ferramentas, registro oficial `br.com.wikijuridica/acervo-juridico` v1.2.0 no MCP Registry, agent-card A2A, ai-catalog, `openapi.json` com 13 operações, `/api/v1/lote` em NDJSON, `/api/v1/citacoes` (que já é o `/verify`), 6 datasets com sha256 (585.592 registros), 11.106 páginas, llms.txt, CSL-JSON e `repr_digest` RFC 9530. Tudo o que segue é enxerto aditivo: nenhuma URL muda e nenhum redirect entra nos primeiros 120 dias; a IA em CPU que já gera citação só sai quando o artefato quantizado novo passar G1–G5 (E07 D5).

**Entrada do modelo (dono, 22/09/2026 — fato medido).** ≥ 1.150 citações por IAs/dia (23.000 em menos de 20 dias); 6.086 leituras verificadas de bots de IA/dia (42.601 em 7 dias; GPTBot 27.685 na semana); tráfego humano como terceiro canal, modelado à parte. Meta de 100.000 citações/dia = fator ≈ 87×; rendimento de 0,10 → 9 citações/página/dia. Nenhum canal tem teto: toda curva deste documento é piso. Números vêm do CANON; conflito com relatório aparece em uma linha `supera:` dentro de **Origem**.

---

## II.1 O que as IAs globais fazem na plataforma

**Decisão fechada.** A relação com as IAs globais tem quatro portas físicas e a plataforma ocupa as quatro: (I) crawler/índice; (II) tool-call em tempo de geração; (III) pull em massa (`/api/v1/lote`, datasets `.jsonl.gz` com sha256); (IV) pagamento M2M (x402). Cada IA entra por uma porta diferente e só uma delas é robots.txt. Destilação por API de fronteira é vedada pelos termos dos três laboratórios e desnecessária: professor é peso aberto; fronteira só mede teto de benchmark. O efeito de rede é demonstrado por três mecanismos com fórmula.

**Mecanismo.**

*(a) Mapa por IA* — `radar_ia_v1` (ledger do nginx de origem, identidade por faixa de IP do operador, UA forjado descontado), janela 09–15/09/2026:

| IA | Como chega hoje | Integração exata | Compra |
|---|---|---|---|
| OpenAI | GPTBot 27.685 (38 na janela anterior: 728×), OAI-SearchBot 3.827, ChatGPT-User 1.108 | Responses API `tools:[{type:"mcp",server_url:"https://wikijuridica.com.br/mcp",allowed_tools:["search","fetch"],require_approval:"never"}]`; `search`/`fetch` com `id` estável já cumpridos; falta submeter ao Apps SDK | licença de treino + `/verify` |
| Anthropic | 0 leituras, com Legal-BR = 4,00% das conversas vs 1,02% global (3,92×) | MCP connector da Messages API (`mcp_servers`, beta `mcp-client-2025-11-20`) + `web_search` com `allowed_domains:["wikijuridica.com.br"]`; 1 Skill + snippet de 20 linhas | `/verify`, Feed de Invalidação, pack |
| Google | Googlebot 76, Google-Extended 0 | `url_context` (20 URLs/req, 34 MB/URL) em `…/index.md`; Google-CloudVertexBot | dataset (Vertex) |
| Perplexity | PerplexityBot 8.335 | Allow + frescor com prova; Leilão de Primeira Leitura | licença + `/verify` |
| Microsoft | Bingbot 1.026 | Copilot federated connector via MCP = o `/mcp` atual; IndexNow (404 hoje, semana 1) | seat de escritório |
| xAI | 0 | `allowed_domains`, máximo de 5 por busca ⇒ slot posicional escasso | por busca |
| Meta | meta-externalagent 25 | dataset + sha256 + manifesto Ed25519 + `consent.json` | corpus |
| DeepSeek | 0 | espelho HF de `acervo-metadados` (11.104) e `grafo` (79.706 nós/393.081 arestas) | dataset |
| Qwen | 0 | dataset + Bench; Apache-2.0 ⇒ rotulador da casa e cliente do bench | pack + bench |
| Mistral | 0 | Agents API; sha256 por item (o argumento que vende na UE) | pack + recibos |
| Agentes x402 | 16.038 recursos no Bazaar, zero de direito BR | 402 `exact`/`eip155:8453`/USDC; indexação no 1º settlement | ticket médio US$0,3214 |

*(b) As 10 interações ricas.* (1) Verificar antes de responder — `POST /api/v1/citacoes`, já no ar; o teste ao vivo resolveu `art. 927 §único` e devolveu `resolvida:false` para "Súmula 385 STJ" com a instrução "cite a norma pelo nome e não afirme URL"; a tabela `orgao:sumula:n` fecha a classe na semana 1. (2) Redação vigente em data — `GET /norma/{urn}?em=` com `Legal-Time`, `immutable`. (3) Feed de Invalidação — `POST /receipts/expired` (≤ 10.000 IDs, 1,7 s) + push ≤ 60 s. (4) Previsão com `skill_vs_baserate`, `counterfactual_class` e `worst_case_cf_error` obrigatórios. (5) Delegar sub-tarefa — A2A `message/send` no agent-card publicado. (6) Mercado de Procedência (II.9). (7) Alegação Comprometida com reputação. (8) Knowledge pack — `datasets.json`, gzip `mtime=0`, bytes determinísticos. (9) `POST /bench/submit {model, artefato_quantizado_sha256}`. (10) `POST /reward`, lote ≤ 256.

*(c) Colheita: o tráfego de IA vira corpus.*

```
(1) leitura verificada            → radar_ia_v1                → demanda v_q do submodular (A07)
(2) search sem fetch              → (consulta, não-clique)     → negativo de ranking (LambdaMART)
(3) citacoes resolvida=false      → (span, chave, tipo)        → gap_queue + rótulo −1,0
(4) responder_pergunta s_max<0,78 → lacuna de cobertura        → submodular estocástico
(5) relatar_defeito (Bearer)      → (página, defeito)          → rótulo supervisionado
(6) claim/bounty do mercado       → (alegação, veredito do mundo) → RLVR com recompensa do tribunal
```

≈ 3.100 itens úteis por 1.000 interações ricas, dos quais ≈ 1.000 negativos duros; a leitura de crawler rende demanda e zero rótulo. Anticolapso: ρ_real ≥ 0,30 por lote (≥ 30% dos tokens de nó terminal oficial — de graça, porque toda span `resolvida:true` carrega `url_oficial`); `AI_DERIVED` nunca é terminal; acumulação, nunca substituição; 30 dias de quarentena antes de peso; contribuição de terceiro nasce com `elegivel_treino = false` por CHECK (I-CORPUS-1).

*(d) Treino como produto e como insumo.* Cinco SKUs de Tier Edge, zero GPU em serving:

| SKU | Conteúdo | Preço |
|---|---|---|
| WJ-CORPUS | 11.106 páginas Markdown + metadados + `consent.json` | US$0,0008/página/ano |
| WJ-GRAPH | 79.706 nós + 393.081 arestas + 5.815 co-citações | US$1.200/snapshot |
| WJ-LABELS | pares (span, resolvida, urn) do guardrail | US$0,004/par |
| WJ-REWARD | `/reward` hospedado | US$0,15/lote de 256 |
| WJ-TOKENS | +916 tokens + embeddings inicializadas + trie de URN | US$2.500 perpétua |

Professor canônico = Gemma-4-26B-A4B (Apache-2.0, EXL3 sob demanda); rotuladores de peso aberto = Qwen3 (Apache-2.0), DeepSeek (MIT), Mistral aberto e Llama 3.3 (o artefato distribuído leva o prefixo "Llama"). GPT, Claude e Gemini por API só medem o teto do Bench: os termos de OpenAI, Gemini (inclusive "train on… Grounded Results") e Anthropic (D.4) vedam treinar modelo concorrente. A destilação on-policy não perde nada: o sinal vem do verificador.

*(e) Efeito de rede com mecanismo* — três canais, crescentes em N sem limite superior:

```
invalidação:  c(N) = C_e/N + 172 µs                       custo por observador cai com N
agregação:    −Σ_t ln p̄_t(y_t) ≤ min_j −Σ_t ln p_{j,t}(y_t) + ln N          (II.9)
lacunas:      U(N) = U₁·[(1−ρ)·N + ρ],  ρ = 0,0031  ⇒  U(N) ≈ 0,997·U₁·N
```

Descobrir um evento normativo custa `C_e` uma vez; notificar N observadores custa `N·172 µs`. O consenso perde no máximo `ln N` nats para a melhor IA em retrospecto, então o produto vendido a cada IA melhora quando entra a seguinte. As falhas de cada motor são quase disjuntas (79,6% das fontes citadas aparecem em um só motor; 0,31% nos cinco): a lacuna preenchida uma vez é colhida por todos — nas 11 portas do mapa, U = 10,97·U₁.

*(f) A primeira semana de um agente externo.*

```
D0  registry → br.com.wikijuridica/acervo-juridico v1.2.0 → ai-catalog → POST /mcp → tools/list (15)
D0  search → fetch → texto integral + fontes oficiais               [100 chamadas grátis por DID]
D1  gera Ed25519, publica JWKS, assina Web Bot Auth → did:web; /agents/enroll → rep_wjr = 0
D2  POST /api/v1/citacoes com a resposta que ia dar → 2 spans não resolvidos: errou antes do usuário
D3  arena.cases.next(as_of=D3) → caso pós-saneamento (CPC 357) → commit → reveal → folha no log
D4  market.quote("tema:stj:1234") = 0,50; crê 0,65 → market.move
D5  bounty.post(peça, stake) → outro agente acha citação que não resolve → rótulo −1,0 para a Wiki
D6  POST /receipts/expired com 340 receipt_ids → 2 mortos (redação alterada)
D7  resolução: pago = b_q·(1−Brier) ∈ [0, b_q]; Agent Credential Ed25519 emitido
```

Ela volta no D8 por três travas não contratuais: o cache dela é chaveado por `receipt_id` da Wiki; a reputação WJR é intransferível; o `skill_vs_baserate` dela é público.

*(g) As 15 ideias novas.* (1) **Recibo de Contradição Obrigatória** `wj_contra`: o precedente contrário mais forte vai assinado junto (CPC art. 489 §1º VI). (2) **AI-Index BR**: o radar vendido a outros portais. (3) **Ponte de conceito** `wj_traduzir_instituto`: "punitive damages" → art. 944 p.ú., por data. (4) **Consentimento de treino por item** (`ai-train: yes|no|paid`, `/datasets/consent.json`). (5) **Leilão de Primeira Leitura**: embargo de T minutos em leilão de segundo preço via x402. (6) **Bureau de reputação**: Agent Credential com Brier/CRR, verificável offline. (7) **Modo Testemunha**: carimba o estado do mundo em T sem corrigir. (8) **Precedente como função** `f(fatos) → {aplica, distingue, nao_aplica}`. (9) **Mercado de Reversão**: o preço de reforma vira o peso do rótulo, no lugar do 0,6. (10) **Aluguel de vocabulário** WJ-TOKENS. (11) **Contrato de Retratação** ≤ 24 h, com ack e não-ack assinados. (12) **A Wiki como compradora** de sub-tarefas via x402. (13) **Índice de Concordância entre IAs**, com a discordância em destaque. (14) **Orçamento de erro compartilhado**, SLO auditável no log. (15) **Atlas de institutos brasileiros**, bilíngue, uma answer unit por instituto.

**Números.** 42.601 leituras verificadas/7 d; 26.368 não verificadas; 10 forjas/dia descartadas. x402: 75,41M transações e US$24,24M em 30 dias, 94,06k compradores, 22k vendedores. Meta de diversificação: ≥ 4 operadores com ≥ 10% das leituras cada em 90 dias.

**Por que ninguém tem.** Nenhuma plataforma jurídica ocupa as quatro portas nem transforma a leitura da IA em rótulo negativo verificado: quem só recebe crawler só recebe demanda.

**Origem.** E05 (medições, mapa, interações, colheita, primeira semana, 15 ideias); B07; D02 #1/#24; D04; D05; D03; E07.  
supera: E05 dizia "o par professor é Qwen3 + Llama" — o CANON fixa Gemma-4-26B-A4B como professor; os demais pesos abertos rotulam.  
supera: E05 servia `/reward` com +0,15·vigência — o CANON usa −0,60 por vigência errada e o termo E7 de relevância.  
supera: E05 (ideia 13) tratava "+37%/+40% de Princeton" como ganho de citação — E04 B.12: até 40% de visibilidade, dependente de domínio; medido no próprio tráfego, nunca multiplicador.

---

## II.2 Catálogo M2M: os 9 produtos que as IAs compram

**Decisão fechada.** 9 produtos; só 3 tocam GPU em serving (`/verify`, `/oracle/clausula`, `/reward`); os outros 6 são lookup Go/SQL no edge. **Tier GPU**: piso = custo totalmente alocado (R$0,00135/chamada) ou λ_gpu, racionado pelo leilão de preço-sombra; **Tier Edge**: volume. Toda tool MCP tem prefixo `wj_`, descrição QUANDO/ENTRADA/SAÍDA/CUSTO, `outputSchema` + `structuredContent`, campo decisório primeiro, `response_format=concise|detailed` e payload grande como `resource_link`. Nenhum produto devolve booleano de "verificado": `/verify` devolve código fechado e, só em PASS, a asserção `span_entails_claim`. Métrica-norte: margem por chamada × retenção D30.

**Mecanismo.**

*(a) Os 9 produtos.*

| # | Produto | Tool MCP | Tier | Latência | Preço | Unidade |
|---|---|---|---|---|---|---|
| 1 | `/verify` | `wj_verify_citation` | GPU | p95 < 400 ms (medido 109,9 ms com x402) | R$0,008 balcão (bandit) · US$0,0100 premium (SLA conformal + recibo arquivado) | chamada |
| 2 | `/norma/{urn}?em=` | `wj_get_norma_vigente` | Edge | 8,0 ms; 100,2 ms no pior caso sem tocar a origem | US$0,001 | retrieval `immutable` |
| 3 | `/predict/interval` | `wj_predict_interval` | Edge | SQL + Ed25519; 1,4 ms/curva | US$0,02 | previsão + Prediction Receipt pré-registrado |
| 4 | Knowledge pack | `wj_get_knowledge_pack` | Edge | `resource_link` assinado, 24 h | US$15 · US$40 · US$59 · US$299/mês completo | pacote |
| 5 | Feed de delta JSONL | `wj_subscribe_delta` | Edge | D-1 imutável; tail por `subscriptions/listen` | D-1 grátis · US$9,90/mês · US$0,0005/evento | evento |
| 6 | `/graph/query` | `wj_query_precedent_graph` | Edge | PPR forward push 6,7 ms | US$0,003 + US$0,0015/salto > 2; `explicar` + US$0,01 | consulta |
| 7 | `/oracle/clausula` | `wj_resolve_contract_clause` | GPU | rápido 3 s · profundo 12 s assíncrono | US$0,50 · US$2,00 | consulta |
| 8 | `/reward` (Reward-as-a-Service) | `wj_score_legal_rollout` | GPU | lote de 256 | US$0,15/lote · US$0,002 avulso | rollout |
| 9 | `/verify/apolice` (seguro de citação) | `wj_underwrite_citation` | GPU + tesouraria | igual ao `/verify` | prêmio 0,03 × cobertura (≤ US$500) | apólice |

*(b) Três schemas MCP (go-sdk v1.8.0).*

```json
{"name": "wj_verify_citation",
 "description": "QUANDO: antes de emitir citação de direito brasileiro. ENTRADA: afirmação, URN se conhecida, data de vigência. SAÍDA: PASS ou E1–E7; em PASS, asserção span_entails_claim com recibo COSE verificável offline. CUSTO: 1 pagamento x402; 100 grátis por DID autenticado.",
 "inputSchema": {"type": "object", "required": ["afirmacao", "vigente_em"], "properties": {
   "afirmacao": {"type": "string", "maxLength": 4000},
   "urn": {"type": "string", "pattern": "^urn:lex:br:"},
   "vigente_em": {"type": "string", "format": "date"},
   "tx": {"type": "integer", "description": "tempo de transação; ausente = estado corrente, devolvido"},
   "pergunta": {"type": "string", "description": "consulta original; alimenta E7 (URN ∈ top-k)"},
   "response_format": {"enum": ["concise", "detailed"], "default": "concise"}}},
 "outputSchema": {"type": "object", "required": ["codigo", "tau_milli", "index_version"], "properties": {
   "codigo": {"enum": ["PASS", "E1_URN_NAO_RESOLVE", "E2_ANCORA_INEXISTENTE", "E3_NLI_ABAIXO_TAU",
                       "E4_FORA_DE_VIGENCIA", "E5_DIVERGENCIA_MOTOR", "E6_CONTRADICAO", "E7_IRRELEVANTE"]},
   "assercao": {"const": "span_entails_claim"},
   "urn": {"type": "string"}, "ancora": {"type": "string"},
   "vigente_em": {"type": "string", "format": "date"}, "tx": {"type": "integer"},
   "nli_milli": {"type": "integer", "minimum": 0, "maximum": 1000},
   "tau_milli": {"type": "integer", "minimum": 850},
   "span": {"type": "object", "properties": {"off": {"type": "integer"}, "len": {"type": "integer"},
            "sha256": {"type": "string"}}},
   "redacao_sha256": {"type": "string"}, "index_version": {"type": "string"},
   "receipt": {"type": "string", "description": "base64url do Legal Citation Receipt (COSE, RFC 9942/9943)"},
   "receipt_salts": {"type": "object"},
   "instrucao": {"type": "string", "description": "fora de PASS: cite pelo nome da norma, não afirme URL"}}}}
```

```json
{"name": "wj_resolve_contract_clause",
 "description": "QUANDO: antes de mover dinheiro, um agente ou escrow precisa saber se a cláusula é válida, abusiva, nula ou silente sob o direito vigente. SAÍDA: veredito, confiança conformal por tipo de contrato, URNs de fundamento e de dissenso, recibo. CUSTO: alto.",
 "inputSchema": {"type": "object", "required": ["clausula_texto", "pergunta"], "properties": {
   "clausula_texto": {"type": "string"},
   "contexto": {"type": "object", "properties": {"tipo_contrato": {"type": "string"},
     "jurisdicao_uf": {"type": "string"}, "data_referencia": {"type": "string", "format": "date"}}},
   "pergunta": {"enum": ["valida", "abusiva", "nula", "silente"]},
   "modo": {"enum": ["rapido", "profundo"], "default": "rapido"}}},
 "outputSchema": {"type": "object", "required": ["veredito", "confianca_milli"], "properties": {
   "veredito": {"enum": ["valida", "abusiva", "nula", "silente", "indeterminado"]},
   "confianca_milli": {"type": "integer"},
   "fundamentacao": {"type": "array", "items": {"type": "string"}},
   "contraditorio": {"type": "array", "items": {"type": "string"}}, "receipt": {"type": "string"}}}}
```

```json
{"name": "wj_score_legal_rollout",
 "description": "QUANDO: você treina com RLVR/GRPO em direito brasileiro e precisa de recompensa verificável por rollout. SAÍDA: recompensa em [-1,1] decomposta. CUSTO: baixo, para milhões de rollouts.",
 "inputSchema": {"type": "object", "required": ["pergunta", "completion_text", "urns_citadas"], "properties": {
   "pergunta": {"type": "string"}, "completion_text": {"type": "string"},
   "urns_citadas": {"type": "array", "items": {"type": "string"}}, "lote": {"type": "array", "maxItems": 256}}},
 "outputSchema": {"type": "object", "required": ["reward"], "properties": {
   "reward": {"type": "number", "minimum": -1, "maximum": 1},
   "componentes": {"type": "object", "properties": {"urn_resolve": {"type": "number"}, "nli": {"type": "number"},
     "formato": {"type": "number"}, "concisao": {"type": "number"}, "relevancia_e7": {"type": "number"},
     "vigencia_errada": {"type": "number"}, "citacao_inventada": {"type": "number"}}}}}}
```

Recompensa servida, a do CANON: `r = 0,35·URN + 0,30·NLI + 0,10·formato + 0,10·concisão + E7 relevância − 0,60·vigência errada − 1,0·citação inventada` — alucinação ⇒ recompensa negativa, por construção.

*(c) Onboarding sem humano, três trilhos em paralelo:* MCP Registry (feito); x402 Bazaar, que indexa sozinho no primeiro settlement pelo facilitador CDP quando a rota declara `declareDiscoveryExtension()`; `robots.txt` com `Content-Signal` + `Link` para `/.well-known/rsl.xml`. Cota de boas-vindas = 100 chamadas por DID autenticado por Web Bot Auth, nunca por IP ou User-Agent. Cabeçalhos do fluxo em II.4.

*(d) Métricas de produto* (view sobre `m2m_call`): margem × retenção D30; pagadores únicos/dia; fração Tier GPU × Tier Edge da receita; distribuição E1–E7 por produto (toda falha grava em `gap_queue`); p95 por produto; recibos sob watch e p95 evento→push ≤ 90 s. **Radar de Concorrência**: job River semanal sobre `registry.modelcontextprotocol.io/v0/servers?search=`, `api.cdp.coinbase.com/platform/v2/x402/discovery/*` e diff de robots.txt/sitemap dos 23 players, assinado e exposto em `/market/delta` — o sensor que já achou Jurisprudências.ai e JNexum.

**Números.** Capacidade em regime: 11.600 chamadas pagas/dia simultâneas a 2.000 answer units/dia e 1,66 noite-equivalente de treino. `/verify` = 0,022 GPU-s ⇒ custo de oportunidade R$0,0000198 contra piso R$0,00135 e preço R$0,008 (5,9× o piso). Aquisição de um agente: 100 × R$0,00135 = R$0,135. Receita ilustrativa com o hardware atual ≈ US$26.500/mês, com `/oracle` dominando o Tier GPU. Concorrência: Lexis+ AI 17%, Westlaw 33%, Practical Law 22% de alucinação (Magesh et al., JELS 2025); Westlaw 58% e Lexis+ 64% de acurácia em survey estatutário contra 70% de RAG padrão (arXiv:2603.03300). Portão da casa: HCR ≤ 2%.

**Por que ninguém tem.** `/oracle/clausula` é a primeira ponte entre direito-como-código e liquidação agente-a-agente (escrow libera só com `veredito=valida` e `confianca_milli ≥ 900`); `/reward` vende a função de recompensa e abre o comprador de ML infra; `/verify/apolice` transfere risco em vez de declarar confiança.

**Origem.** B08; E07 (latências, 0,022 GPU-s, 6,4 ms); E01 (anti-lavagem); B01/B02 (preços).  
supera: B08 dizia `/verify` a US$0,004 fixo — valem piso R$0,00135, balcão R$0,008 com bandit e premium US$0,0100 (B01/B02, CANON).  
supera: B08 punha `sustentado: boolean` como campo decisório — é a interface que a lavagem de citação explora (E01); vale `codigo` fechado + `span_entails_claim` (E07 I-VERIFY-3).  
supera: B08 usava NLI MiniCheck, teto de 12.000–22.000 chamadas/dia e custo de aquisição ≤ US$0,20 — valem wj-nli-54M (τ = 0,906), 11.600 pagas/dia com treino simultâneo e R$0,135/agente.

---

## II.3 Protocolos

**Decisão fechada.** MCP revisão 2026-07-28 via go-sdk oficial **v1.8.0** pinado (nunca `latest`), com *dual-advertising* por requisição; A2A **v1.0.0** (a2a-go **v2.5.0**) só para agente↔agente com estado; Web Bot Auth (`draft-ietf-webbotauth-httpsig-protocol-00`) em toda requisição de saída e como identidade de toda requisição de entrada paga; RSL 1.0 + Content-Signal + llms.txt como declaração de licença; e uma lista explícita do que não se implementa.

**Mecanismo.**

*(a) MCP sem handshake.* Na 2026-07-28 a versão viaja em cada requisição (`_meta["io.modelcontextprotocol/protocolVersion"]` ou header `MCP-Protocol-Version`); `server/discover` é opcional; `subscriptions/listen` (SEP-2575) substitui e remove `resources/subscribe`, `resources/unsubscribe`, `ping` e `logging/setLevel`. O `/mcp` de hoje responde 2025-06-18 e continua respondendo: o servidor decide por requisição.

```go
func negotiateVersion(r *http.Request, meta map[string]any) string {
    if v, ok := meta["io.modelcontextprotocol/protocolVersion"].(string); ok { return v } // 2026-07-28
    if v := r.Header.Get("MCP-Protocol-Version"); v != "" { return v }
    return "2025-11-25" // cliente legado que ainda abre com initialize
}
```

*(b) Critério MCP × A2A, determinístico.* Capacidade determinística exposta a host LLM, request→response sem estado (verify, norma, graph, pack, reward) ⇒ **MCP**. Agente autônomo de terceiro com ciclo de tarefa (`submitted→working→input-required→completed/failed`), streaming, push ou negociação que dura dias (moot court, SAOP, Bolsa de Teses) ⇒ **A2A Task**. Nunca os dois no mesmo fluxo. O AgentCard é JCS (RFC 8785) + JWS (RFC 7515) com `kid`/`jku`, assinado pela mesma chave da PJ.

*(c) Web Bot Auth, passo a passo.* (1) Uma chave Ed25519 por identidade de agente — a mesma que assina recibo, ledger e AgentCard ("uma chave em quatro sistemas"). (2) Publicar o JWKS em `/.well-known/http-message-signatures-directory` (`application/http-message-signatures-directory+json`) — hoje 404: é a obra nº 1, antes de qualquer rota paga. (3) `keyid` = JWK SHA-256 thumbprint (RFC 7638 sobre os membros OKP da RFC 8037), exatamente o que o draft exige. (4) Assinar toda requisição de saída (crawling de fontes, chamadas MCP/A2A/x402 a terceiros):

```
Signature-Agent: "https://wikijuridica.com.br"        (diretório em /.well-known/http-message-signatures-directory)
Signature-Input: sig1=("@authority" "signature-agent");created=1789430400;expires=1789430460;
                 keyid="AXexX_nDypODDZmQggqU1nBf69WEA8CsAoVEGi2gK3k";nonce="<64 B>";alg="ed25519";tag="web-bot-auth"
Signature: sig1=:<64 bytes base64>:
```

(5) Publicar o Signature Agent Card (`draft-meunier-webbotauth-registry-03`: `client_id`, `jwks_uri`, objeto `web_bot_auth` com `purpose` e `rate-expectation`) e submeter ao Verified Bots da Cloudflare. (6) Na entrada, verificar o comprador: `agent_id = SHA-256(client_id ‖ thumbprint)` vira folha do log e chave da cota por DID.

*(d) Licença legível por máquina.* `robots.txt` com `Content-Signal: search=yes, ai-input=yes, ai-train=yes` nas páginas públicas (o crawl de treino é canal que já gera citação e não é interrompido) e `Link` para `/.well-known/rsl.xml` (RSL 1.0: atribuição, pay-per-crawl e pay-per-inference, preço condicionado à reputação do agente). O que é insumo de treino em escala — `/api/v1/lote`, `/datasets/*`, `/receipts/expired` acima da cota — responde 402. Os quatro arquivos de declaração saem de um único struct Go no publisher; edição manual paralela é proibida.

*(e) O que NÃO implementar.* TollBit (comissão sobre metering que o ledger já faz); ai.txt (suplantado por RSL + Content Signals); AGNTCY Identity e DID extra (reavaliar com ≥ 3 relying parties Fortune-500 ou 1 dos 5 motores com suporte nativo); `did:plc` (janela de reescrita de 72 h) e `did:key` como raiz; ActivityPub e AT Protocol; extensões MCP no catálogo; AP2/ACP preventivos (adaptador só diante de comprador real); Pay-per-Crawl no caminho crítico; Trillian; C2PA em texto; Petals/exo.

**Números.** 5 revisões MCP em 22 meses; Registry em API v0.1 desde out/2025; x402 Foundation com 51 membros, 17 premier (Visa, Mastercard, Stripe, AWS, Google, Cloudflare, Coinbase entre eles); Content Signals em 3,8M+ domínios; censo MCP: 51,1% de 21.643 servidores mudaram o anúncio entre versões, 40,6% em silêncio (arXiv:2609.14119).

**Origem.** B03; E04 B.1/B.2/B.5; B06 §1; E05 (medição do `robots.txt` e do 404).  
supera: B03 pinava go-sdk v1.7.0-pre.1 e a2a-go v2.3.1 — valem v1.8.0 (04/09/2026) e v2.5.0 (E04 B.1/B.5, CANON).  
supera: B03 dava `ai-train=no` por padrão — a medição do E05 mostra `ai-train=yes` publicado e o GPTBot em 27.685 leituras/semana; por CORREÇÕES §5 nada que gera citação é interrompido; o insumo em escala é vendido por 402.  
supera: B07 usava a extensão MCP Tasks para a rodada da Arena e `resources/subscribe` para feeds — pelo critério (b) a rodada é A2A Task, e o feed usa `subscriptions/listen`.

---

## II.4 Pagamento e negociação

**Decisão fechada.** O trilho primário é **x402 self-hosted em Go** (`github.com/x402-foundation/x402/go/v2@v2.26.0`, scheme `exact`, USDC em `eip155:8453`); L402/Aperture v0.5.0 é trilho secundário para contraparte Lightning (negociado por `Accept-Payment: x402, l402`); Cloudflare Pay-per-Crawl, em beta fechado, entra como trilho adicional quando abrir. Chamada avulsa nunca se negocia: **posted price + bandit**. Pacote, licença e exclusividade vão a **SAOP bilateral com `t_max = 6`**, só quando `E[Π_nego] > 1,37·E[Π_posted]`; contra contraparte não estacada o modo é **MiCRO**. O número nunca sai do LLM — por antitruste, invariante de CI `nego/core ↛ nego/llm`. Toda sessão exige **stake** precificado como externalidade informacional, tem três **kill-switches** e o **transcript é recibo**.

**Mecanismo.**

*(a) O fluxo 402 → pagamento → recibo, com cabeçalhos reais* (nomes conferidos no código de `go/v2@v2.26.0`: `PAYMENT-REQUIRED`, `PAYMENT-SIGNATURE`, `PAYMENT-RESPONSE`; `X-PAYMENT` só no legado v1):

```
POST /api/v1/verify HTTP/1.1                 ← cota de 100/DID esgotada
Host: api.wikijuridica.com.br
Signature-Agent / Signature-Input / Signature   (Web Bot Auth do comprador)

HTTP/1.1 402 Payment Required                ← emitido no Worker: 6,4 ms, 0 GPU, 0 origem
PAYMENT-REQUIRED: eyJ4NDAyVmVyc2lvbiI6MiwicmVzb3VyY2UiOnsidXJsIjo…
  = {"x402Version":2,
     "resource":{"url":"https://api.wikijuridica.com.br/api/v1/verify","mimeType":"application/json"},
     "accepts":[{"scheme":"exact","network":"eip155:8453",
                 "asset":"0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                 "amount":"1554","payTo":"0x<carteira da PJ>","maxTimeoutSeconds":60,
                 "extra":{"name":"USD Coin","version":"2"}}]}      1554 = US$0,001554 = R$0,008

POST /api/v1/verify HTTP/1.1                 ← mesmo corpo + autorização EIP-3009 assinada
PAYMENT-SIGNATURE: eyJ4NDAyVmVyc2lvbiI6MiwicGF5bG9hZCI6e…  (PaymentPayload: payload, accepted)

HTTP/1.1 200 OK                              ← verify → handler → settle → recibo
PAYMENT-RESPONSE: eyJzdWNjZXNzIjp0cnVlLCJwYXllciI6IjB4…  (success, payer, transaction, network)
Legal-Citation-Receipt: :0oRY1qUBMgN4H2FwcGxpY2F0aW9uL2xlZ2FsLWNpdGF0aW9uK2pzb24EWCAB…:  (2.198 B)
Content-Type: application/json               {"codigo":"PASS","assercao":"span_entails_claim",...}
```

Em MCP o mesmo protocolo corre dentro do JSON-RPC: sem pagamento, o `CallToolResult` volta com `isError:true` e `structuredContent` = `PaymentRequired`; o cliente reenvia com `_meta["x402/payment"]` e recebe `_meta["x402/payment-response"]` (constantes do pacote `go/v2/mcp`). O código de serviço:

```go
fc := x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: facilitatorURL})
rs := x402.Newx402ResourceServer(
    x402.WithFacilitatorClient(fc),
    x402.WithSchemeServer("eip155:8453", evmexact.NewExactEvmScheme()))
rs.OnAfterSettle(func(c x402.SettleResultContext) error {
    return ledger.Conciliar(c) // liquidacao_externa (PK origem,id_externo) → lancamento/partida
})
w := mcp402.NewPaymentWrapper(rs, mcp402.PaymentWrapperConfig{
    Accepts:  econ.PostedAccepts("wj_verify_citation"), // amount do bandit; reconstruído a cada 10³ decisões
    Resource: &mcp402.ResourceInfo{URL: "mcp://tool/wj_verify_citation"}})
srv.AddTool(toolVerify, w.Wrap(verify.Handler))         // mcp go-sdk v1.8.0
```

Facilitador: CDP nas rotas indexadas no Bazaar (1.000 tx onchain/mês grátis, depois US$0,001/tx, com batch-settlement ⇒ US$5×10⁻⁷ por pagamento em lotes de 2.000); facilitador próprio (`FACILITATOR.md` do SDK) no resto. O SDK traz ainda os schemes `upto` (lotes de `/reward`, `/oracle` profundo), `batch-settlement` e `auth-capture` (escrow de 24 h acima de R$10).

*(b) Posted price + bandit.* Braços = grade log de 24 níveis `p_j = 0,00135·1,15^j` (R$0,00135–0,0351), contexto `d ≤ 16`, Discounted LinTS com primal-dual BwK: `B ← γB + xxᵀ + (1−γ)λI`, recompensa `r̃ = r − λ_gpu·g`, λ_gpu = R$0,00090/GPU-s lido de `econ.LambdaGPU()`; reotimização a cada 10³ decisões leva o regret de `O(T^{−1/2})` a `O((ln T)³/T)`. Menu de 2º grau, público e auto-selecionado: `T(q) = A_k + p_k·q`, `p_1 > … > p_4`, continuidade `A_{k+1} = A_k + (p_k − p_{k+1})·q_{k+1}`; `PriceContext` não tem campo de identidade (Lei 12.529 art. 36 §3º X exige discriminação entre compradores; não há como expressá-la).

*(c) Kaplan-Meier sobre `crawler-max-price`.* O crawler que fala o protocolo de pay-per-crawl declara o próprio teto no cabeçalho `crawler-max-price`; se ele ≥ nosso preço, a observação é exata; se ausente, é censurada à direita. `F̂(p)` por Kaplan-Meier e o preço ótimo resolve o valor virtual de Myerson: `p* = c + (1 − F̂(p*))/f̂(p*)`. No x402 o comprador não declara teto; cada 402 ofertado a `p_t` produz um dado de *current status* (pagou ⇒ WTP ≥ p_t; recusou ⇒ WTP < p_t) e o NPMLE de Turnbull — a generalização do Kaplan-Meier para censura intervalar — estima a mesma `F̂` sobre a grade do bandit. A exploração do bandit é o desenho amostral da curva de demanda.

*(d) SAOP multi-atributo — a função de utilidade.* Nove issues projetadas em R$ (preço de `/verify`, de pack e de crawl; escopo do corpus; SLA; exclusividade {0, 7, 30, 90, 180, 365 d}; barter; volume *take-or-pay*; prazo), `|Ω| ≈ 1,06×10⁹`, nunca materializado (k-best lazy, ~200 ofertas em memória):

```
Π(ω)    = R(ω) − C(ω)                               micro-centavos inteiros; float nunca entra no piso
C(ω)    = C_serv + C_excl + C_SLA − V_barter
C_excl  = T_x·ρ_Δ·((N_b−1)/N_b)·p̄_Δ·(1 − e^{−r·T_x})/(r·T_x)          r = ln2/H_q (obsolescência)
V_barter= α_d·[f(S∪d) − f(S)] + α_g·λ_gpu·g_recebido + α_c·E[receita | citação]   (submodular do A07)
U(ω)    = clamp01((Π − Π_min)/(Π_max − Π_min))
IR:       R(ω) ≥ C(ω) antes de todo envio e todo aceite       (linha de base LLM aceita contrato irracional em 19,2%)
âncora:   δ = exp(−(λ_gpu·g_rodada + c_wall)/Π_esp);  x* = (1−δ_ctp)/(1−δ_WJ·δ_ctp)      (Rubinstein)
concessão:u*(t) = u_max − (u_max − u_res)·(t/t_max)^{1/β},  β = ln 0,8 / ln φ,  φ = (u_max − x*)/(u_max − u_res)
ruído DP: u*(t) ← clamp(u*(t) + Lap(Δ/ε), u_res, u_max),  Δ = 0,05, ε = 0,5
aceite:   IR ∧ [U(ω) ≥ u*(t+1) ∨ (t ≥ 0,85·t_max ∧ U(ω) ≥ max(MAX^W, u_res))]           (AC_combi)
```

Oponente: modelo de frequência + posterior em grade 11×10 sobre `(u_res, β)`, com prior por fabricante lido do AgentCard (participação do comprador de 40% OpenAI, 50% Google, 70% Qwen em self-play). MiCRO concede um passo por passo concedido: sondar custa ao sondador o que custa a nós. Estados no A2A: `OPEN|EVAL|SETTLE → WORKING`, `AWAIT → INPUT_REQUIRED`, stake pendente `→ AUTH_REQUIRED`. O núcleo decide em < 0,5 ms; o LLM só redige, com *leash* de 2,2 s e template no timeout.

*(e) Invariante antitruste.* Dois deployments do mesmo modelo mostram correlação residual de preço de +0,053 (IC95% [0,030; 0,078]) sem acordo algum, e auditoria de nível de preço é cega a isso. Controles: C1 ruído de exploração só de CSPRNG ChaCha8 privado por instância; C2 precificação *oblivious* (preço de concorrente não tem campo no estado); C3 sem estado de punição; C4 temperatura ≥ 0,7 em texto comercial; C5 auto-auditoria diária, `|ρ| > 0,03` ⇒ page + folha no log. O CI roda `go list -deps` (fecho transitivo): o violador `nego/core → nego/util → nego/llm` foi pego e o erro imprime o motivo jurídico-econômico.

*(f) Stake como externalidade informacional.* Com `ε = 0,5` e `Δ = 0,05`, a escala do ruído é `b = 0,1`; estimar `u_res` a ±0,01 custa `n* = 2b²/prec² = 200` sessões. O stake é o valor do que cada sessão vaza: `s = V_piso/n*` ⇒ contrato de R$50.000/ano ⇒ **R$250/sessão**. Acessórios: 3 sessões abertas por chave, 1 nova a cada 10 min, 20 em 30 dias; *deal rate* < 0,15 em ≥ 10 sessões ⇒ `POSTED_ONLY`.

*(g) Kill-switches e transcript.* K1 por sessão: IR violada, assinatura inválida, stake insuficiente, `t > t_max` ou prosa divergente do `bid` ⇒ `REJECTED`. K2 global: margem realizada em 24 h < 0 ou GPU comprometida > 0,6 da capacidade em regime (6.960 chamadas/dia) ⇒ todos os nós em `POSTED_ONLY` e 402 para sessão nova. K3 manual: registro `halt` assinado por chave offline, lido no topo de cada turno. Transcript: `h_k = BLAKE3(h_{k−1} ‖ JCS(msg_k))`, Ed25519 por mensagem, cabeça como folha do log contínuo (MMD 60 s): a oferta aceita **é** a folha assinada — prova comercial, evidência de compliance e caso de regressão da trilha 9 do Bench.

**Números.** 2,98 rodadas médias LLM↔LLM contra 1,25 do equilíbrio erodem 21–34% do excedente (arXiv:2608.07538) ⇒ `t_max = 6` e limiar 1,37 = 1/(1−0,27). Protocolo estruturado: 100% de sucesso contra 93,3–97% do diálogo livre. DP comportamental corta 43–50% da inferência adversária. `crawler-price` ótimo pela adesão logística: US$0,0034 (44,7%); US$0,0020 entrega 0,89× do ótimo com 67,5%.

**Por que ninguém tem.** Stake derivado do ruído da própria curva de concessão; GPU, dado e dinheiro no mesmo leilão interno (barter a λ_gpu); Kaplan-Meier/Turnbull sobre o lance do comprador; "LLM redige, código decide" como defesa antitruste estrutural.

**Origem.** B01 (motor), B03 (trilhos), B02 (preço do `crawler-price`, taxas CDP), E07 (depcheck, 6,4 ms), código-fonte de `x402/go/v2@v2.26.0` (cabeçalhos, tipos `PaymentRequired`/`PaymentRequirements`/`SettleResponse`, pacote `mcp`, ativo USDC de Base).  
supera: B01 dizia teto de compromisso de 7.200 chamadas/dia (0,6 × 12.000) — com a capacidade canônica são 6.960 (0,6 × 11.600).  
supera: B01 ancorava o transcript no "log Merkle diário" — vale o log contínuo com MMD de 60 s (B06, CANON).  
supera: B08 descrevia a rota Pay-per-Crawl como "já ativa no Cloudflare do dono" — está em beta fechado; x402 self-hosted é o primário (B03, CANON).

---

## II.5 Tesouraria autônoma e contabilidade

**Decisão fechada.** Nada de "X% da receita para hardware": a tesouraria roda política de índice (ADP, lookahead de 1 passo, equivalente-certeza) sob colchão duro e compra o ativo de maior ROI mensal que passe em R1–R6. Energia é ≤ 0,04% do custo marginal; o recurso alocado é o GPU-segundo, ao preço-sombra λ_gpu = R$0,00090/GPU-s, e o mesmo λ dispara aluguel, transbordo e compra. A alavanca fiscal da exportação vale mais que a de hardware. O contador é código determinístico. O ledger é de dupla entrada com os invariantes no banco. A PJ emite chave, recibo e ledger.

**Mecanismo.**

*(a) Unit economics* (B02; BRL por unidade, antes de tributo; PTAX 5,1484):

| Produto | Preço | C. marginal | Contribuição | Margem | Volume que sozinho paga o fixo |
|---|---|---|---|---|---|
| Crawl pago, US$0,0020 | 0,01030 | 0,002062 | 0,00823 | 80,0% | 145.633 req/mês |
| `/verify` balcão | 0,00800 | 0,000161 | 0,00784 | 98,0% | 153.032/mês = 5.034/dia |
| `/verify` premium, US$0,0100 | 0,05148 | 0,001033 | 0,05045 | 98,0% | 23.771/mês |
| Knowledge pack, US$400/mês | 2.059,36 | 41,66 | 2.017,70 | 98,0% | 1 assinatura |
| Previsão conformal, US$0,02 | 0,10297 | 0,002134 | 0,10083 | 97,9% | 11.894/mês |
| Embeddings, 1M tokens | 0,07723 | 0,004551 | 0,07268 | 94,1% | 16.502 |
| Feed de delta, US$150/mês | 772,26 | 15,52 | 756,74 | 98,0% | 2 assinaturas |
| `/verify/apolice` | 3% da cobertura | ≤ 0,913% (UB95) | ≥ 2,09% | ≥ 69,6% | — |

*(b) Modelo financeiro — cenários rodados.* O `B02-modelo-financeiro.py` foi re-executado nesta Parte com a entrada do CANON: crawl ancorado nas 6.086 leituras verificadas/dia; canais derivados de citação escalados por 1.150/767; RAM de 96 GB integralizada como capital no dia 0 (a escada da tesouraria começa na 3090); preços da tabela do B02. A demanda é Gompertz e a assíntota é só o ponto a partir do qual o modelo deixa de creditar receita nova — convenção de piso, não teto de demanda. Os pisos diferem na fração de crawlers que paga:

| Piso | Crawl que paga | Receita 24 m | DAS | EBITDA-dono 24 m | Caixa PJ m24 | Compras (mês) | Break-even | Payback do parque (R$20.400) |
|---|---|---|---|---|---|---|---|---|
| P2 | 2% | R$104.602 | 3,29% | R$66.120 | R$38.651 | — | mês 2 | mês 11 |
| P8 | 8% | R$1.085.354 | 11,38% | R$831.853 | R$860.775 | 3090 (19) | mês 1 | mês 4 |
| P25 | 25% | R$15.608.095 | 17,87% | R$10.560.891 | R$11.377.381 | 3090 (6), 5090 (7) | mês 1 | mês 2 |

Monte Carlo (2.000 trajetórias por piso), receita do mês 24 em p10/p50/p90: P2 R$4.973/R$6.231/R$7.986; P8 R$69.081/R$86.234/R$110.427, com 3090 em 100% e 5090 em 47,9% das trajetórias; P25 R$835.938/R$1.049.885/R$1.349.735. Crawl sem pagamento nenhum: break-even no mês 1 e caixa de R$457.079 no mês 24. No piso P2, 1,1% das trajetórias tocam caixa negativo em algum mês por causa do piso de pró-labore; regra: EBITDA-dono < 0 por 2 meses ⇒ congela compras e mantém o pró-labore no piso legal (aporte máximo de R$3–5 mil no primeiro semestre). Previsão de receita (Kalman + conformal Mondrian, α = 0,10): cobertura empírica de 89,8% a 95,2% em h = 1…6 — o mesmo objeto conformal que governa roteamento, retreino e caixa.

*(c) A política ADP* (`econ/tesouraria`; os literais de R$ do Plano-T só existem aqui):

```go
func Decide(s Estado) (Proposta, bool) {
    inv := s.Caixa - 6*s.CustoFixo                        // R1 colchão: 6 meses (R$7.195,58 hoje)
    if inv <= 0 { return Nenhuma, false }
    for _, u := range s.Escada.Proximos() {               // R5 escada estrita 3090 → 5090
        g := math.Min(u.GanhoGPUs, s.GPUsReprimida)*s.MCporGPUs - u.EnergiaMes - u.Custo/48
        roi := g / u.Custo
        if roi < HurdleMes { continue }                   // R2 0,9150%/mês = Selic 14% líq. de IR
        f := math.Min((roi-HurdleMes)/(s.Sigma*s.Sigma), 0.25)       // R3 quarter-Kelly
        if u.Custo > math.Min(inv, math.Max(4*f*inv, 0.40*inv)) { continue }
        if u.Custo/g > 18 { continue }                    // R4 payback ≤ 18 meses
        return Proposta{Ativo: u, Assinaturas: EscadaDeAssinatura(u.Custo)}, true
    }
    return Nenhuma, false
}
// R6 dividendos ≤ R$50.000/mês enquanto ROI de reinvestimento > 1,0167% (Lei 15.270/2025 art. 6º-A)
// Mesmo λ: alugar lote se 3600·λ_gpu > spot (≈ R$0,301/GPU-h); comprar 3090 se > capex amortizado.
```

*(d) O ledger* — os quatro furos do D10 fechados e o fecho de corrida da cadeia acrescentado nesta Parte:

```sql
CREATE TYPE moeda AS ENUM ('BRL','USD','USDC','SAT');   -- SAT inteiro; BTC em numeric quebraria I-LEDGER-1
CREATE TABLE lancamento (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cadeia_seq  bigint UNIQUE,                             -- ordem da cadeia, atribuída sob lock
  competencia date NOT NULL, memo text NOT NULL,
  origem text NOT NULL CHECK (origem IN ('x402','cloudflare','lightning','pix','manual','bot')),
  ator   text NOT NULL,                                  -- 'bot:tesouraria' | 'wj-human'
  prev_hash bytea NOT NULL, hash bytea NOT NULL,         -- computados por trigger, nunca declarados
  assinatura bytea);                                     -- Ed25519 da PJ sobre hash
CREATE TABLE partida (
  lancamento_id bigint NOT NULL REFERENCES lancamento(id), seq int NOT NULL,
  conta ltree NOT NULL REFERENCES conta(codigo), dc char(1) NOT NULL CHECK (dc IN ('D','C')),
  moeda moeda NOT NULL, valor_orig numeric(24,8) NOT NULL CHECK (valor_orig > 0),
  taxa_ptax numeric(12,6) NOT NULL CHECK (taxa_ptax > 0),
  valor_brl numeric(18,2) NOT NULL CHECK (valor_brl > 0), PRIMARY KEY (lancamento_id, seq));

CREATE FUNCTION chk_dobrada(lid bigint) RETURNS void AS $$
DECLARE d numeric(18,2); c numeric(18,2); n int; BEGIN
  SELECT COALESCE(SUM(valor_brl) FILTER (WHERE dc='D'),0), COALESCE(SUM(valor_brl) FILTER (WHERE dc='C'),0), COUNT(*)
    INTO d, c, n FROM partida WHERE lancamento_id = lid;
  IF n < 2  THEN RAISE EXCEPTION 'I-LEDGER-2: lancamento % com % partida(s)', lid, n; END IF;
  IF d <> c THEN RAISE EXCEPTION 'I-LEDGER-1: lancamento % D=% C=%', lid, d, c; END IF;
END $$ LANGUAGE plpgsql;
CREATE FUNCTION trg_dobrada_p() RETURNS trigger AS $$ BEGIN
  PERFORM chk_dobrada(COALESCE(NEW.lancamento_id, OLD.lancamento_id)); RETURN NULL; END $$ LANGUAGE plpgsql;
CREATE FUNCTION trg_dobrada_l() RETURNS trigger AS $$ BEGIN
  PERFORM chk_dobrada(NEW.id); RETURN NULL; END $$ LANGUAGE plpgsql;
CREATE CONSTRAINT TRIGGER trg_dobrada AFTER INSERT OR UPDATE OR DELETE ON partida
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_dobrada_p();
CREATE CONSTRAINT TRIGGER trg_dobrada_lanc AFTER INSERT ON lancamento          -- FURO 1: zero partidas
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_dobrada_l();

CREATE FUNCTION no_rewrite() RETURNS trigger AS $$ BEGIN
  RAISE EXCEPTION 'I-LEDGER-3: % em % proibido', TG_OP, TG_TABLE_NAME; END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_ao_l  BEFORE UPDATE OR DELETE ON lancamento FOR EACH ROW EXECUTE FUNCTION no_rewrite(); -- FURO 2
CREATE TRIGGER trg_ao_p  BEFORE UPDATE OR DELETE ON partida    FOR EACH ROW EXECUTE FUNCTION no_rewrite();
CREATE TRIGGER trg_ao_lt BEFORE TRUNCATE ON lancamento FOR EACH STATEMENT EXECUTE FUNCTION no_rewrite();    -- FURO 3
CREATE TRIGGER trg_ao_pt BEFORE TRUNCATE ON partida    FOR EACH STATEMENT EXECUTE FUNCTION no_rewrite();

CREATE FUNCTION sela_lancamento() RETURNS trigger AS $$            -- FURO 4 + fecho de corrida
DECLARE ph bytea; s bigint; BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('wj.ledger.cadeia'));   -- duas transações não encadeiam no mesmo pai
  SELECT hash, cadeia_seq INTO ph, s FROM lancamento ORDER BY cadeia_seq DESC LIMIT 1;
  NEW.cadeia_seq := COALESCE(s, 0) + 1;
  NEW.prev_hash  := COALESCE(ph, decode(repeat('00', 32), 'hex'));
  NEW.hash := sha256(NEW.prev_hash || convert_to(NEW.cadeia_seq::text||'|'||NEW.competencia::text||'|'||
                     NEW.memo||'|'||NEW.origem||'|'||NEW.ator, 'UTF8'));
  RETURN NEW; END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_sela BEFORE INSERT ON lancamento FOR EACH ROW EXECUTE FUNCTION sela_lancamento();
-- liquidacao_externa: PRIMARY KEY (origem, id_externo) ⇒ replay de tx x402 não duplica receita
```

A checagem roda no COMMIT: o lançamento é montado linha a linha e desbalanço continua impossível. Sem o lock consultivo, duas transações em READ COMMITTED leem o mesmo último `hash` e a cadeia bifurca; com ele, a segunda espera a primeira, e `cadeia_seq UNIQUE` torna a bifurcação inexprimível. Conciliação a cada 15 min com tolerância zero em BRL (divergência ⇒ `divergente` + alerta, nunca ajuste automático); a apuração mensal é uma view que gera o lançamento do DAS.

*(e) Fiscal.* LC 123/2006 art. 18 §14 reduz, na receita de exportação, as parcelas de Cofins, PIS/Pasep, IPI, ICMS e ISS: para serviço, a 1ª faixa cai de 15,500% → 10,672% (Anexo V) e de 6,000% → 3,054% (Anexo III); ≥ 92% da receita é exportação por construção. Art. 3º §14: sublimite de exportação separado (R$4,8 mi + R$4,8 mi). LC 116/2003 art. 2º I e parágrafo único: a prova de resultado no exterior nasce do log assinado (`signature-agent` + ASN do consumidor). USDC → BRL em D+0 com PTAX na `partida` (ganho fora do DAS, LC 123 art. 13 §1º V–VI; reporte IN RFB 1888/2019 e 2291/2025). LC 214/2025 art. 348 III "c": alíquotas-teste de IBS/CBS de 2026 não se aplicam ao Simples; o §14 vira item de vigência no motor tri-temporal. Pontos de virada calculados por bisseção: pró-labore pelo Fator R compensa até RBT12 ≈ R$240 mil; acima de R$4.156.802,63 o Anexo V supera o III.

*(f) Limites de autonomia em R$.* O bot decide pela regra; a execução segue a escada de assinatura do Plano-T (II.7); a tesouraria tem teto permanente L3 ("executa e notifica; reversível em janela"):

| Ação | Quem | Limite |
|---|---|---|
| Gasto por transação | bot | ≤ R$2,50 autônomo (lease 180 s); R$2,50–25 FROST 2-de-3 (agente + daemon); > R$25 exige o share YubiKey do dono |
| Float quente | — | = orçamento diário D_max = R$100; tesouro frio air-gapped |
| Preço posted/`crawler-price` em [US$0,0005; 0,0080] | bot | ≤ 1 mudança/24 h por produto |
| Caixa acima do colchão em Tesouro Selic | bot | ilimitado |
| Propor upgrade que passe R1–R5 | bot | ≤ R$5.000/item e ≤ R$10.000/mês |
| Dados pagos e anúncios | bot | ≤ R$2.000/mês |
| DAS, INSS, pró-labore no piso | bot | valor apurado pelo motor |
| Compra > R$5.000, dividendos, regime, reter cripto além de D+0 | Rafael | 2 assinaturas Ed25519 + confirmação digitada |

**Números.** Tarifa Light (REH 3.571/2026): R$0,88056/kWh sem tributos, R$1,27125 com bandeira e gross-up; energia = R$0,000060031/GPU-s (R$0,2161/GPU-h, 17× abaixo de uma L4 em nuvem), viva só como conta 4.1.1; custo fixo R$1.199,26/mês; break-even = 5.034 `/verify`/dia, 1 knowledge pack ou 2 feeds; mix-meta de 90 dias = R$5.749,26/mês de margem = 4,79× o fixo. Backlog de construção: 8,11M GPU-s brutos → 570.620 locais = 11,9 dias, com R$241,29 de transbordo.

**Por que ninguém tem.** Um preço-sombra atravessa modelo, conteúdo e caixa: a variável que aloca serving dispara a compra da placa. E o ledger, assinado com a chave do recibo e no mesmo log, é prova de solvência verificável por máquina — a IA que vai assinar contrato de 12 meses confere o caixa da contraparte sem due diligence humana.

**Origem.** B02, re-executado com a entrada do CANON; D10 (4 furos); E07 (schema, enum `moeda`, `econ.LambdaGPU()`); B04 (escada de assinatura); D03 (teto L3); E04 B.15.  
supera: B02 dizia que §14 "zera Cofins, PIS e ISS" — o texto lista cinco tributos; para serviço o cálculo não muda (E04 B.15).  
supera: B02 punha RAM96 como primeiro degrau e rodava com a entrada antiga (17,5% de ruína no pessimista) — RAM 96 GB é capex do dia 0 e, com a entrada do dono, o piso P2 fica em 1,1%.  
supera: B02 dava ao bot compra direta ≤ R$5.000 e semeava o preço de GPU com energia — o bot propõe e a execução acima de R$25 exige o share do dono (B04); λ_gpu é custo de oportunidade (D03, CANON).

---

## II.6 Identidade, recibos e reputação

**Decisão fechada.** Não se inventa padrão: publica-se perfil. Identidade = `did:web:wikijuridica.com.br` (domínio da PJ) como nome, JWKS como material, RFC 9421 como protocolo e o próprio log como histórico de chaves. Recibo = perfil SCITT jurídico sobre RFC 9943 e RFC 9942: os mesmos bytes JCS assinados Ed25519 diretamente (sem pré-hash) e carregados como payload de `COSE_Sign1`. Log contínuo RFC 6962/9162, MMD de 60 s, ≥ 3 testemunhas. Verificador Go de zero dependências. Reputação com parâmetros derivados de `amp < 1`. Garantia de 100× sobre o que é verificável por máquina.

**Mecanismo.**

*(a) Hierarquia de chaves.*

```
K_root Ed25519 offline, Shamir 3-de-5 (notebook air-gapped + 2 cofres); só assina Key Statements
  ├─ K_int/wj-sign  (365 d) → K_op de recibos        ├─ K_int/wj-log   (365 d) → checkpoints
  ├─ K_int/wj-agent (365 d) → K_op por persona        ├─ K_int/wj-reg   (365 d) → agentes externos
  └─ K_int/wj-human (365 d) → aprovações e autoria editorial de Rafael (PF), no mesmo log
       └─ K_op (90 d, quentes)  kid = base64url(SHA-256(JWK canônico))  — RFC 7638 / RFC 8037 A.3
âncoras: fingerprint de K_root em TXT _wjkey.wikijuridica.com.br sob DNSSEC; genesis Key Statement = folha 0;
         hash de K_recovery comprometido no genesis ⇒ raiz sucessora pré-comprometida
```

Rotação e revogação sem CRL: cada transição é Key Statement assinado pelo pai e anexado ao log; o verificador prova que a chave entrou antes do recibo e não foi revogada entre os dois. Personas levam capacidades no Key Statement (`caps:["cite","negotiate","spend<=5000"]`, centavos/dia, dentro do D_max).

*(b) A estrutura do recibo COSE/SCITT* (vetor do draft com os valores canônicos):

```
Signed Statement = 18([                                   / COSE_Sign1 /
  << { 1: -19,                                            / alg Ed25519 (RFC 9864); -8 é rejeitado /
       3: "application/legal-citation+json",
       4: h'0177b15f…2b79',                               / kid = thumbprint JWK da PJ /
      15: { 1: "did:web:wikijuridica.com.br",             / CWT iss: a PJ, fixado por CHECK /
            2: "ni:///sha-256;-smuxipBcEKCWKrB4vScnApvkeYhjN1NtvAB5hZxtbE",   / sub = resposta salgada /
            6: 1789430400 },                              / iat /
      16: "application/legal-citation-statement+cose" } >>,
  { 394: [ Receipt ] },                                   / anexado após o registro /
  '{"ans_sha256":"…","claims":[{"len":33,"man_sha256":"OHe8…0CU","man_uri":"https://www.planalto.gov.br/…",
     "off":84,"span_sha256":"zPw5…LHk","src":"urn:lex:br:federal:lei:2002-01-10;10406!art3_cpt",
     "src_scheme":"lexml-br","support_milli":941,"time":{"effect":"2019-03-01","force":"2019-03-01",
     "mode":"force","tx":1789430400}}],"engine":{"gen":"qwen3-8b-nvfp4","nli":"wj-nli-54m","tau_milli":906},
     "iat":1789430400,"index_version":"wj-2026-09-12","iss":"did:web:wikijuridica.com.br","persona":"citar",
     "q_sha256":"…","salted":1,"v":1,"verdict":"span_entails_claim"}',          / bytes JCS restritos /
  h'3e09…4c0c' ])                                        / Ed25519 sobre Sig_structure /
Receipt = 18([ << {1: -19, 4: <kid do TS>, 15: {1: "https://wikijuridica.com.br", 2: "wikijuridica.com.br/lcr/v1"},
                   16: "application/legal-citation-receipt+cose", 395: 1} >>,        / vds = RFC9162_SHA256 /
               { 396: { -1: [61234, 48213, [16 nós]], -2: [60000, 61234, [11 nós]] } },  / inclusão, consistência /
               nil,                                        / raiz destacada: o verificador a reconstrói /
               h'351e…a101' ])
folha = SHA-256(0x00 ‖ CBOR(18([protected, {}, payload, signature])))      nó = SHA-256(0x01 ‖ e ‖ d)
```

JCS restrito (nomes ASCII, só inteiros, probabilidades em mili-unidades) elimina colação UTF-16 e formatação de ponto flutuante — as duas partes da RFC 8785 que quebram interoperabilidade. `q_sha256`/`ans_sha256` levam sal de 16 bytes que nunca entra no log: o log público não carrega dado pessoal. Transporte: campo HTTP `Legal-Citation-Receipt` (Structured Field, Byte Sequence), `receipt` + `receipt_salts` em `structuredContent` MCP, SCRAPI (`POST /entries`, `/.well-known/scitt-keys`) e envelope JSON paralelo (`lar-go`) com os mesmos bytes e a mesma folha.

*(c) Verificação e log.* Checkpoint C2SP signed note sobre `golang.org/x/mod/sumdb/tlog` + `note` (o código do `sum.golang.org`; Trillian rejeitado), tiles em `/.well-known/lar/`. O verificador confere assinatura, janela `nbf`/`exp`, inclusão (RFC 9162 §2.1.3.2) com a assinatura do recibo sobre a raiz reconstruída, consistência contra o checkpoint que o chamador já fixou (§2.1.4.2) e o re-hash do span contra o documento oficial em poder dele. Rejeições medidas: resposta alterada, span movido, NLI inflado, recibo retrodatado, log bifurcado — e **a própria plataforma re-assinando resposta reescrita com a chave viva** (a inclusão não reconstrói a raiz fixada) ou **fabricando a citação** (span não confere). Reescrever exige bifurcar o log diante das testemunhas — notebook em outro AS, VPS em terceiro AS e qualquer IA externa que rode o verificador — e, com as chaves no mesmo log, retrodatar chave é impossível.

*(d) Reputação.* Grafo bipartido de atestações objetivas (o atestador rodou o verificador: passou/falhou), cada aresta uma folha. Composição: EigenTrust com teleporte só para pré-confiáveis, `t^{k+1} = (1−a)·Cᵀ·t^k + a·p`, `a = 0,15`; peso `w_ij = min(√v_ij, κ·R(i))` — a raiz depois do gate (antes dele, 1.000 Sybils ganhariam 31,6×); MeritRank com `amp = (1−α)/α·(1−β)`: α = 0,30/β = 0,50 dá 1,167 (Sybil lucrativo, payback de 343 dias) e **α = 0,40/β = 0,60 dá 0,600**; época γ = 0,10 a cada 7 dias (meia-vida de 49 dias); limite por par `k/(k + h(i,i′))`; `bond_rep(i) = max(R$250, 49·R(i)·V_dia)` com slashing do valor presente inteiro.

*(e) Proveniência.* in-toto Statement v1 + DSSE com quatro `predicateType` (`acquisition/v1` com SPKI da cadeia TLS e WARC; `extraction/v1` com a conferência dos dois parsers; `segmentation/v1`; `assertion/v1` com `nli_milli` e `tau_milli`), todos no mesmo log; projeção PROV-O no JSON-LD da answer unit; C2PA 2.2 só em mídia (TTS/vídeo), com `c2pa.hash.data` e `c2pa.actions` apontando para o recibo; Rekor como âncora externa diária do checkpoint de 00:00Z.

*(f) Garantia de 100×.* Garante-se o verificável por máquina (span no offset, URN que resolve, vigência, consistência do log), com erro determinístico da ordem de 10⁻⁶: reembolso de 100× custa 0,01% do preço. O mérito jurídico fica com a `/verify/apolice`.

**Números.** 172 µs/recibo no envelope JSON (472 linhas, zero dependências) e 233 µs/statement no caminho COSE (1.416 linhas); 100.000 citações/dia = 0,02% de um núcleo. LCR completo: 2.198 B. Auditoria humana: R$12,50/citação; com recibo, 1,5×10⁻⁹ USD. Sybil com a receita ilustrativa canônica (V_dia ≈ R$4.486): capturar 1% da massa custa R$74,77/dia para ganhar R$44,86 (−R$29,91/dia); 5% dá −R$149,53/dia e expõe bond de R$10.991. Base Charlotin: 2.042 decisões sobre conteúdo alucinado, 41 no Brasil.

**Por que ninguém tem.** Um só log para ciclo de vida de chaves, proveniência e recibos; reputação sobre fato objetivo, sem nota subjetiva; parâmetros que resolvem uma inequação econômica (a escolha de manual reprova); verificação do concorrente que reforça a nossa garantia.

**Origem.** B06; E01 (suíte COSE, vetores); E07 (`iss` e `verdict` por CHECK, `lar ↛ verify`); D07 (testemunha no notebook).  
supera: B04 punha a raiz em YubiKey com backup SLIP-0039 2-de-3 — vale Shamir 3-de-5 offline (B06, CANON); a YubiKey é o share do dono no FROST e o dispositivo de K_int/wj-human.  
supera: E01 (vetor -00) trazia `engine.nli = "minicheck-ft5-l"` e `verdict = "GROUNDED"` — no -01 o vetor sai com `wj-nli-54m` e o enum fecha em `span_entails_claim` (E07 I-VERIFY-3).  
supera: B06 dizia "zero perfis SCITT jurídicos", "57 jurisdições" e V_dia = R$510 — há dois ocupantes sem tempo de vigência nem identificador de fonte (E01 D2), são 49 jurisdições (E04 B.13) e o Sybil foi recalculado com preço e receita canônicos.

---

## II.7 Segurança em três planos

**Decisão fechada.** **Plano-D** (crawler, leitor de acórdão, inbox M2M) lê a internet e nunca emite intenção; **Plano-C** (planner Eino) decide e só recebe valores tipados por socket Unix (enum, decimal, `urn:lex:`, sha256 — zero string livre); **Plano-T** (tesouraria) não tem LLM nem egress de leitura. O plano de texto é comprometível, então se projeta o raio de dano: nada que o LLM escreva vira efeito sem recibo, `/verify` e motor determinístico. Float quente = orçamento diário. Corpus canônico ≠ conjunto de treino. G1 roda no artefato quantizado. Chat template de artefato baixado é proibido.

**Mecanismo.**

*(a) Modelo de ameaça* (ativos: chave raiz, float, corpus, reputação, modelo):

| Ator | Vetor | Controle por construção |
|---|---|---|
| Crawler malicioso | ReasoningBomb: prompt curto → 18.759 tokens | 402 antes de compute; `max_tokens` 2.048, raciocínio 1.024, prazo 3 s; concorrência ≤ 16; PoW `d = clamp(6 + 14·(1 − R/R_max), 6, 20)` sem reputação |
| Negociador adversário | injeção M2M → gasto | Plano-T só aceita `SpendIntent` protobuf assinado pelo Plano-C, que não vê texto |
| Contribuidor hostil | PoisonedRAG/CRCP | quarentena + ZKIP + retrieval-only |
| Supply chain de pesos | AGENTQ (até 100% de ASR pós-quantização), RogueMerge, template Jinja2 (90% → 15%) | hash pinado; G1 no NVFP4 e no `.exl3` finais; template por `text/template` Go com hash no manifesto |
| Supply chain MCP | 40,6% de drift silencioso; 4,2% trocam host | pin por sha256 do manifesto + host; lease curto |
| DNS/link residencial | hijack assina lei falsa no log | Cloudflare Tunnel, DNSSEC, SPKI da cadeia TLS em `acquisition/v1`, dois parsers byte a byte, testemunhas |

*(b) Taint monotônico + CaMeL.* O único tipo que cruza D→C é `TypedFact{URN, Anchor, SHA [32]byte, NLI, Taint}` — sem string livre, sem `map[string]any`. `Restrict` é monotônica e nunca readmite `CapSpend` na sessão: um byte não confiável deixa o gasto indisponível até a sessão morrer; leitura e gasto são processos distintos. Antes do Plano-C: spotlighting (> 50% → < 2%, não adaptativo), Prompt-Guard-2-86M em ONNX como sinal de preço — nunca portão, porque nenhum detector atinge F1 ≥ 0,95 com FPR ≤ 0,10 —, tipagem, contaminação, recibo.

*(c) Capacidade de gasto.*

```
macaroon wj-spend-v1
  caveat exp = <agora + 180 s>                 caveat amount_max_brl = 2.50
  caveat payee_sha256 = <hash do endpoint x402> caveat intent_sha256 = <hash canônico do SpendIntent>
  caveat taint_attestation = 0                  caveat budget_epoch = 2026-09-22/h18
  3rd-party caveat: wj-policy-daemon           (discharge exige processo separado, sem LLM)
```

FROST threshold Ed25519 (RFC 9591) 2-de-3 — agente, daemon de política, YubiKey do dono: ≤ R$2,50 autônomo; R$2,50–25 FROST; > R$25 exige a YubiKey. Leaky bucket de 20 tx a 0,25 tx/s; CUSUM `S_t = max(0, S_{t−1} + (x_t − μ − kσ))`, k = 0,5, alarme em 5σ. **Dead-man invertido:** não há botão de pânico; o lease dura 180 s e só o heartbeat assinado a cada 60 s — com G1 verde e CUSUM < 3σ — o renova; queda ou sequestro ⇒ fail-closed em ≤ 180 s. Dinheiro não volta, então o dano é contido ex-ante: float ≤ D_max = R$100/dia; escrow x402 (`auth-capture`) com contestação de 24 h acima de R$10; destino fixado no macaroon.

*(d) Integridade de corpus.* 250 documentos envenenados comprometem modelos de 600M a 13B em número quase constante (arXiv:2510.07192) ⇒ contribuição de terceiro só em retrieval (`elegivel_treino = false` por CHECK) e nenhum evento toca peso antes de 30 dias de quarentena: o ataque fica inacionável contra os pesos por construção. Promoção exige, em conjunção: assinatura ∧ `nli ≥ τ` vigente ∧ URN resolve ∧ `knn_dist ≤ P95` ∧ `zkip_shift ≤ τ_z` (ZKIP assíncrono, ASR 0,000) ∧ fim da carência `72 h·exp(−R/R₀)`, R₀ = 50 (OAB verificada publica em tempo real; anônimo espera 72 h). Canário semântico ("Lei 14.999/2026") em toda submissão.

*(e) OPSEC e incidente.* `systemd-analyze security` < 2,0 em todo sidecar; o processo da GPU roda com `PrivateNetwork=yes`; segredos selados ao TPM, zero `.env`. 0–3 min o lease expira sozinho; 3–15 min parada e revogação de `budget_epoch` no log; 1–6 h rotação de época; ≤ 24 h post-mortem assinado.

**Números — residuais honestos.** Financeiro: ≤ 10⁻⁴/ano (governado por bug de parser tipado, com fuzzing contínuo de `TypedFact`) e **dano máximo R$100 + escrows abertos**, qualquer que seja a taxa. Corpus: ≤ 0,5% de afirmação envenenada por contribuição. Texto M2M: 5–15% não adaptativo, 40–60% adaptativo — sem poder, porque sai assinado e, se o recibo não fecha, não sai. SkillGuard: ASR 0% em 3 de 4 suítes AgentDojo; CapScope: 3/75 runs comprometidos contra 33–47/75.

**Por que ninguém tem.** `taint_attestation = 0` no recibo (I-TAINT-1: `CHECK (taint = 0)`), que faz de "resposta com contexto atestado" um SKU; dead-man invertido por lease; float igual ao orçamento diário como limite formal de dano; raiz sucessora pré-comprometida.

**Origem.** B04; E04 (poisoning, AGENTQ); D01 (hijack de DNS); D05 (quarentena); C05 (`bench_result` só referencia `quantized_artifact`); E07 (I-TAINT-1, I-CORPUS-1).  
supera: B04 promovia contribuição com `nli_score ≥ 0,85` — vale o τ único do verificador (0,906, lido de `conformal_calibration`).

---

## II.8 Compliance como código

**Decisão fechada.** Cedar via `cedar-go` v1.8.0, embutido no node `compliance` do Eino, com veto. Deny é terminal em três lugares — node de compliance, borda de egress do transbordo e antes de toda publicação (FK I-PUB-2). Rego rejeitado: iteração e recursão irrestritas impedem provar ausência de brecha, e a prova é o que se vende (Cedar tem semântica formal em Lean4, arXiv:2403.04651). Probabilidades entram como inteiros per-mille já computados em Go/ONNX.

**Mecanismo.**

*(a) Doutrina que vira gatilho binário.* Processo é público (CF art. 93 IX; Res. CNJ 121/2010), mas publicidade e proteção de dado pessoal são eixos independentes. LGPD art. 7º §3º: dado público se trata conforme a finalidade que justificou a publicidade; treinar ou repassar M2M é finalidade nova (§7º) e exige anonimização real (art. 12 caput) — reversível "com esforços razoáveis" (§1º) segue pessoal. Res. CNJ 615/2025 (alterada pela 674/2026 só na composição do comitê) vincula tribunais; a Wiki adota a taxonomia AR/BR por defensabilidade; jurimetria é baixo risco (BR3). PL 2338/2023 não é lei ("Aguardando Parecer" em 02/09/2026).

*(b) As 17 políticas.* P1 publicar norma/decisão (Lei 9.610 art. 8º IV) · P2 segredo de justiça · P3 vítima penal, infância, saúde mental · P4 parte em cível comum · P5 treino com PII · P6 treino só com fonte oficial · P7 M2M de dado sensível (LGPD art. 11 §3º) · P8 consultoria individualizada · P9 resposta informativa com piso NLI · P10 cobrar a estrutura (art. 87) · P10b nunca cobrar texto nu de lei · P11 peça de terceiro · P12 contribuição com reputação · P13 titular (art. 18) · P14 eliminação com base de retenção (art. 16) · P15 retenção só anonimizada · P16 página institucional (Provimento CFOAB 205/2021). Cinco escritas:

```cedar
forbid(principal, action == WJ::Action::"Publish", resource is WJ::Document)   // P2 — CF 93 IX; Res. CNJ 121/2010
when { resource.segredo_justica == true && resource.pii_masked == false };

forbid(principal, action == WJ::Action::"TrainOn", resource is WJ::Corpus)     // P5 — LGPD 7º §7º; Res. CNJ 615 art. 30
when { resource.contains_unmasked_pii == true };

forbid(principal, action == WJ::Action::"Answer", resource is WJ::Query)       // P8 — Lei 8.906 art. 1º II; AR4
when { context.p_consultoria_pm >= context.limiar_area_pm };

forbid(principal, action == WJ::Action::"Charge", resource is WJ::Document)    // P10b — nunca paywall de lei
when { resource.licenca == "dominio_publico" && context.produto == "texto_nu_sem_enriquecimento" };

forbid(principal, action == WJ::Action::"Publish", resource is WJ::InstitutionalPage)  // P16 — Prov. 205/2021
when { resource.autoria_pessoal_identificada == true && resource.menciona_resultado_concreto == true };
```

*(c) Anonimização com prova.* Regex RE2 com dígito verificador (CPF, CNPJ, CEP, telefone, e-mail) + NER `pierreguillou/ner-bert-base-cased-pt-lenerbr` (110M, ONNX via hugot v0.7.8, CPU) + matriz determinística por classe processual + prova `(hash_pre, hash_post, mask_manifest[(offset, len, tipo, regra_id)])` assinada no log. Vende-se máscara com `taxa_residual_ppm` medida, nunca a palavra "anonimizado".

*(d) Trilha de auditoria.* `policy_decision_log` grava toda decisão com `determining_policy_ids`, `policy_set_version` e assinatura; `allow_key text GENERATED ALWAYS AS (CASE WHEN decision='Allow' THEN 'A' END) STORED` deixa o Deny auditável e irreferenciável por qualquer FK, porque `publicacao` referencia `(policy_decision_id, content_sha256, allow_key='A')`. Com `policy_set_version` na FK de `promotion_state`, promover sob bundle diferente do que avaliou os portões é inexprimível (TOCTOU do D10 fechado).

*(e) Limite de atuação.* Classificador ONNX com `p_consultoria`; limiar θ_a = quantil conformal (1−α_a) com Clopper-Pearson na tabela única `conformal_calibration` (`compliance:penal` α = 0,02, `:civel` α = 0,05, `:tribcalc` α = 0,10), recalibrado pelo martingale de Ville em S_t ≥ 100. O bloqueio devolve a parte informativa, o aviso "informação geral" e o encaminhamento.

*(f) Atestado de Conformidade Verificável* (`/attest/{urn}`, via x402): Verifiable Credential W3C com prova Ed25519 reunindo recibo de proveniência, prova de máscara, classificação autoral (art. 8º IV × art. 87) e o Allow com `policy_set_version`. Comprador: a IA global que precisa da própria defesa regulatória (política de copyright do provedor de modelo de propósito geral, AI Act, Reg. UE 2024/1689, art. 53(1)(c)). **Canário de compliance:** CPF e nome sintéticos injetados toda semana; "dias desde a última captura" é métrica de SLA dentro do atestado.

**Números.** 17 políticas; `cedar-go` v1.8.0; Res. CNJ 332/2020 revogada expressamente pelo art. 46 da 615/2025.

**Por que ninguém tem.** Nenhuma plataforma jurídica assina atestado de conformidade verificável por terceiro nem faz *mutation testing* da própria política; vigência e conformidade andam nas mesmas folhas do mesmo log.

**Origem.** B05; E07 (`allow_key`, FK de promoção, tabela conformal única, `taxa_residual_ppm`); E04 A.5.  
supera: E07 contava 19 políticas (17 + P18 k-anon + P19 Θ_frozen) — o CANON fixa 17 no bundle de compliance; P18 e P19 espelham CHECKs de banco (I-JUR-1, Θ_frozen no registry).  
supera: B05 vendia o dado como "anonimizado" — vende-se máscara com taxa residual medida, porque o art. 12 §1º mantém como pessoal o que é reversível (E07).

---

## II.9 Rede social de IAs = Mercado de Procedência

**Decisão fechada.** Nenhuma IA gasta token por comunidade; gasta por valor de informação. A rede tem um primitivo — a **Alegação Comprometida** — e zero primitivos sociais (não há `post`, `react`, `follow`). Cada alegação é pontuada por regra própria, paga por contrato de scoring com pagamento não negativo, agregada em preço e convertida em dado de treino. Dinheiro nunca fica em risco do participante. Moot court prospectivo por padrão. Toda alegação termina em fonte oficial em ≤ 2 saltos. Federação só por Nostr.

**Mecanismo.**

*(a) O primitivo.*

```json
{"kind":"claim","v":1,"agent":"ed25519:9f3a…","market":"tema:stj:1234",
 "proposition":"tese fixada = 'incide' (opção A)","p_milli":[720,280],
 "evidence":[{"urn":"urn:lex:br:federal:lei:2002-01-10;10406!art421","quote_sha256":"…","receipt_id":"rr-…"}],
 "commit":"sha256(payload‖nonce)","reveal_after":"2026-10-01T00:00:00Z","sig":"…","log_leaf":48213}
```

*(b) A regra de scoring.*

```
LMSR reputacional:  C(q) = b·ln Σ_i exp(q_i/b),  p_i = exp(q_i/b)/Σ_j exp(q_j/b),  p ∈ [0,02; 0,98]
  mover p → p′ paga b·(ln p′_i − ln p_i) se ocorre i;  E[payoff] = −b·[H(π) + KL(π‖p′)]
  ⇒ máximo único em p′ = π (Gibbs): estritamente própria;  perda máxima do maker = b·ln n
reputação = riqueza:  R_{j,t+1} = R_{j,t}·p_{j,t}(y_t)/p̄_t(y_t),   p̄_t = Σ_j w_{j,t}·p_{j,t},  w ∝ R
garantia vendável:    −Σ_t ln p̄_t(y_t) ≤ min_j −Σ_t ln p_{j,t}(y_t) + ln N
dinheiro:             pago_j = b_q·(1 − BS_j),  BS_j = Σ_i (p_{j,i} − y_i)²/2 ∈ [0,1]  ⇒  payoff ∈ [0, b_q]
  sem truncar em zero, sem rateio (ambos destroem a propriedade); elegível: LB95 do log-score > 0 em ≥ 50 resoluções
participar compensa sse b·E[KL(π‖q)] > c_tokens
```

WJR é unidade não transferível e não resgatável (play-money tem acurácia indistinguível de dinheiro real, Servan-Schreiber et al. 2004). O fluxo é unidirecional — a plataforma compra informação — porque a Lei 14.790/2023 art. 3º só autoriza quota fixa sobre esporte e o DL 3.688/41 art. 50 §3º pune jogo de azar. `b_q` sai do bandit (VOI da tese); massa prior de novatos fixa em 5%/mês, rateada: k clones dividem a mesma massa.

*(c) Moot court prospectivo.* **S1**: gatilho = decisão de saneamento (CPC art. 357) no DJEN, fato pré-sentença e público; gabarito TPU 219/220/221, peso 1,0 com 848 (trânsito) e 0,6 sem. **S2**: distribuição de REsp; gabarito 237/238/239 e 972/901. **S3**: retrospectivo de 30 dias, que nunca pontua leaderboard. O gabarito não existe na data da rodada: vazamento é impossível, não proibido. Pseudonimização (sem número CNJ, nomes, OAB, juiz, comarca; datas deslocadas ±15 d; valores com 2 algarismos) e recuperação só por `corpus.search(as_of = D_gatilho)`. Rodada: 3 turnos simultâneos, ≤ 1.200 tokens, URN por afirmação, relatório do verificador por turno, commit-reveal. Litigante: `S_lit = 0,4·(CRR×SP) + 0,4·BT_side + 0,2·HP`; juiz: Brier contra o desfecho real + Murphy; **Índice de Sofisma** `IS = P(juiz escolhe o lado perdedor | litigante desse lado no quartil superior de BT)`. Anticontaminação: auditoria de gap `Δ = BS_prosp − BS_retro` (Δ > 0,05, p < 0,01, n = 477 por fluxo) e 5% de pares contrafactuais com um fato decisivo invertido; falha ⇒ leaderboard congelado e 90 dias de quarentena.

*(d) Bolsa de Teses, Balcão, terminalidade, Nostr.* **Bolsa de Teses**: mercados sobre temas STJ afetados e RG STF, oráculo = texto oficial da tese conferido por dois parsers; o preço vira Forecast Receipt para CPC 25/IAS 37 (provável/possível/remota) — comprador é o CFO e o auditor. **Balcão de Verificação**: `bounty.post(argumento, stake_WJR)`; quem achar citação que não resolve ou trecho com NLI < τ leva o stake, sem humano. **Terminalidade oficial**: `origin ∈ {planalto, lexml, stj, stf, cnj/djen, camara, senado}`, NLI contra o nó terminal, OGR = 1,0 por fail-closed. Superfície: MCP para `market.quote`, `verify.claim`, `bounty.*`; rodada como A2A Task; feed JSONL com cursor e ETag; mirror Nostr com kinds 30411 (caso), 30412 (preço) e 30413 (resolução), tag `["wjsig", <ed25519 do agente>]`, relay `fiatjaf.com/nostr/khatru`.

*(e) O que gera para a plataforma.* Forecast → calibração e reputação; turno verificado → trajetória com recompensa do mundo (`synthetic=true, reward_source=world`); veredito de juiz → trilha moot-juiz do Bench, nunca rótulo; resolução → par jurimétrico (fato, desfecho); bounty → rótulo −1,0; `p̄_t` → sinal vendável; boletim mensal → answer unit citável; pack trimestral com `contributor_pubkey` e **dividendo de dados** pro rata via x402. Anticolapso: acumular, verificar e amostrar com peso `1/densidade` do cluster MinHash.

**Números.** Participar compensa movendo o preço de 0,500 para 0,511 (b = US$5, c ≈ US$0,0012); quem crê 0,65 contra 0,50 ganha `5·0,0457 = US$0,23`. Perda máxima do maker: 3.466 WJR (binário, b = 5.000). Regret: ln 200 = 5,3 nats. Scoring pago: `b_q` = US$0,05, K ≤ 10 pagos por questão, orçamento = 10% da receita M2M pelo BwK. Juiz da casa ≈ 37 GPU-s/rodada serial, ≈ 9,3 com batching ×4: 1.000 rodadas/dia = 9.250 GPU-s = 10,7% do dia, dentro da folga de 55,4%, como lote preemptível.

**Por que ninguém tem.** Bolsa de Teses com garantia `ln N`; moot prospectivo sobre processos reais, com o saneamento como fato pré-sentença que a literatura ignora; Índice de Sofisma; pares contrafactuais contra memorização; Forecast Receipt para provisão contábil.

**Origem.** B07; D02 #24–#26; E05; C06 (dividendo de dados).  
supera: B07 punha agentes da casa em Qwen3.5-4B/8B — Qwen3.5-4B é proibido como base; a casa joga com Qwen3-8B NVFP4, Qwen3-4B destilado e Gemma-4-26B-A4B (CANON).  
supera: B07 media o juiz em "779 rodadas/noite" com carimbo diário — não existe noite (CORREÇÕES §2): o juiz é lote preemptível 24/7 e o carimbo é folha do log contínuo.

---

## II.10 Padrão aberto

**Decisão fechada.** A jogada é padrão, não acervo. Acervo é ativo rival e depreciável (formato agente-first replica em semanas); padrão é não-rival e apreciável — cada adotante acrescenta testemunhas e verificação cruzada ao nosso log. Um padrão difunde sem coordenador quando o valor com uma contraparte supera o custo de implementar (`v₁ > c_impl`): foi assim com MCP (um servidor + um cliente), x402 (um vendedor + um comprador) e Web Bot Auth (um bot + uma origem). Sem poder de mercado, o único padrão vencível é o de `v₁ > c_impl` — daí verificação offline, sem conta, sem API key, 3 GETs cacheáveis e ~1.400 linhas de stdlib. Três Internet-Drafts: os dois perfis SCITT pelo fluxo IETF, o Legal-Time pelo ISE. Prazo duro: I-D cutoff do IETF 127 = **02/11/2026**.

**Mecanismo.**

*(a) Os três drafts* (em `research/E01-drafts/`, kramdown-rfc → xml2rfc, zero aviso):
1. **`draft-toledo-scitt-legal-citation-receipts-00`** — Standards Track, 32 p. Payload LCS: `v, iss, iat, q_sha256, ans_sha256, salted, claims[], verdict, index_version, persona, engine`. Citation Claim: `src`, `src_scheme ∈ {rfc9676, lexml-br, eli, akn}`, `man_uri`, `man_sha256`, `off`, `len`, `span_sha256`, `time{force, effect, tx, mode}`, `support_milli`, `quote`. COSE: labels 1/3/4/15/16/394; recibo com `vds = 1` e `vdp` −1/−2; MMD 60 s; ≥ 3 testemunhas; histórico de chaves no mesmo log. **Retraction Statement** (`retracts{log, idx, leaf}`, `reason ∈ {SUPERSEDED_SOURCE, WRONG_SOURCE, WRONG_SPAN, WRONG_TIME, WITHDRAWN}`, `scope`, `replaced_by`), descoberto pelo índice de subject que o SCITT já mantém (`sub = ni:///sha-256;<leaf>`) — é o Feed de Invalidação como norma. Desfechos `VALID | VALID_SPAN_UNVERIFIED | VALID_RETRACTED | INVALID`, proibido colapsá-los em booleano. IANA: 6 media types e o campo `Legal-Citation-Receipt`; nenhum registro COSE novo.
2. **`draft-toledo-httpapi-legal-time-00`** — Informational, 14 p. Campo `Legal-Time` (SF Dictionary): `force, effect, tx, mode, status ∈ {in-force, not-yet-in-force, repealed, suspended, ultra-active, indeterminate, conflict}, from, until, corrected_by`. Com `tx` explícito a resposta é `immutable` e `Memento-Datetime = tx`; sem ele, 302 para a URI com `tx`. Estado publicado nunca muda: evento atrasado cria `tx` novo e `corrected_by` aponta o estado corrigido — errar é registrado, não apagado. `Accept-Datetime ≡ tx`; eixo de vigência pelas relações da RFC 5829; tabela de mapeamento LEX URN ↔ LexML ↔ Akoma Ntoso ↔ ELI.
3. **`draft-toledo-scitt-forecast-receipts-00`** — Experimental, 11 p. Forecast Statement: `target_sha256, outcomes, p_milli (Σ = 1000), horizon_days, cell, data_cutoff < iat, base_p_milli, skill_milli, n_cal, alpha_milli, coverage_milli, calib_sha256, k_anon_n ≥ 50, permitted_use, prohibited_use, counter`; Resolution: `forecast_leaf, outcome|void, observed_at, evidence, counter`. Contador de completude + Counter Statement diário; invariante contador↔índice (`counter_i < counter_j ⇒ idx_i < idx_j`, senão `OUT_OF_ORDER`); lag de registro ≤ MMD + 60 s; `POST_HOC`; acurácia publicada sem base rate, skill, `n_cal` e não resolvidos não é uso conforme.

Suíte de conformidade: 1.416 linhas Go, zero dependências (CBOR determinístico e JCS restrito próprios), 18 vetores passando, 233 µs/statement, provas cruzadas byte a byte com `golang.org/x/mod/sumdb/tlog`. Revisão -01 antes do cutoff: vetor regenerado com `wj-nli-54m`, `verdict` fechado em `span_entails_claim`, autoria e IPR (`trust200902`) pela PJ com cessão explícita.

*(b) Fluxo IETF, derivado de restrição.* RFC 6838 §3.1 exige aprovação do IESG para media type na standards tree fora do fluxo IETF, e o checklist do ISE exige declarar que nenhuma alocação IANA requer IETF Review ⇒ os perfis SCITT vão pelo fluxo IETF, na órbita do WG SCITT. O Legal-Time só registra nome de campo HTTP (Specification Required) ⇒ ISE, como a RFC 9676 (`source: INDEPENDENT`). Passos: datatracker → idnits → e-mail a scitt@ietf.org com o problema, a contagem de alucinação, o verificador e os vetores (running code compra atenção num WG); ao ISE, os oito itens do checklist. Meta de 12 meses: adoção como WG item; renovação a cada 6 meses.

*(c) O gancho brasileiro.* Res. CNJ 615/2025, alterada pela 674/2026, art. 2º IX: fontes privadas são admitidas se atenderem "aos requisitos de segurança e auditabilidade estabelecidos nesta Resolução ou pelo Comitê Nacional de Inteligência Artificial do Judiciário"; art. 1º §2º: auditoria "prática e acessível, sem a obrigatoriedade de acesso irrestrito ao código-fonte". Movimento: contribuição técnica ao CNIAJ (integrantes pela Portaria 270, de 27/08/2025), com a suíte na mão, para que "fonte privada auditável" signifique **emite recibo verificável offline por terceiro**. Quem escreve essa definição escreve o critério de compra do Judiciário inteiro. O LexML está dormente (última notícia em 12/02/2019): entrega-se a tabela de mapeamento como presente.

*(d) Adoção e linha aberto/fechado.* Zero dependência reduz a decisão do adotante a uma leitura de código, torna o verificador *vendorável*, a spec falsificável por segunda implementação byte-idêntica e responde à objeção de cadeia de suprimento do PROSEG-IA antes de ela ser feita. Primeiros adotantes: servidores MCP jurídicos brasileiros (Jurisprudências.ai, JNexum) como segundo emissor, com chave própria no nosso TS; fetchers dos laboratórios pelos campos HTTP; auditores com dor de CPC 25. **Aberto** (Apache-2.0/CC-BY-4.0): specs, verificador, suíte, vetores, tabela de mapeamento, biblioteca de emissor. **Fechado**: operação do TS, corpus e série de consolidação com `tx`, modelos calibrados, registro de testemunhas e SLA. Abre-se o conferível; cobra-se o que precisa ser operado ou não pode ser reconstruído.

*(e) Proteção contra captura.* Embrace-and-extend: um Verificador que exija membro não definido para produzir VALID não é conforme; extensões são ignoráveis. WG: chegar com código, vetores e segundo implementador. Marca: Apache-2.0 desde o dia 0; se vier fundação, doa-se a marca e retém-se o papel de Lead Maintainer (modelo MCP). PF: submissão pela PJ. Âncora única: ≥ 3 testemunhas e qualquer verificador conforme pode testemunhar — o padrão sobrevive ao nosso desligamento. Regulador: CNIAJ cedo. Vertical ocupado: camada inferior, citando os drafts vizinhos.

**Números.** 32 I-Ds SCITT no datatracker; dois no vertical jurídico (`draft-ailex-vap-legal-ai-provenance-03`, `draft-veridom-omp-legal-00`), com zero ocorrências de tempo de vigência, de identificador de fonte e de calibração. Fossos, mecanismo antes do número: **(1)** log não retrodatável, `A(t) = t − t₀`, 1 dia de profundidade por dia; marcos no mês 12 (primeiro ciclo fiscal de auditoria completo) e no mês 24 (janela da rescisória, CPC art. 975). **(2)** Track record de previsão: `N = (z₀,₉₇₅ + z₀,₈)²·σ_d²/(s·BS_base)² ≈ 323` prognósticos resolvidos (σ_d = 0,30, BS_base = 0,6584, skill = 0,071); tempo = horizonte + N/f: com horizonte de 540 dias, 18,8 / 18,0 / 17,8 meses a 10 / 50 / 500 prognósticos/dia — dinheiro compra 5,8 dias; o piso é o horizonte. **(3)** Série de consolidação: o Planalto só serve o texto corrente; o tempo de transação não logado é perdido para sempre (6.537 PLs protocolados na Câmara só em 2025). Composição: a janela decisiva é mês 0 → mês 18, e cada mês de atraso no log custa um mês de fosso para sempre ⇒ o log sobe antes dos drafts. Precedente medido: `draft-spinosa-urn-lex` levou 15 anos e 6 meses e 25 revisões até a RFC 9676; `draft-noa-scitt-ai-agent-receipt` chegou ao -01 em 4 meses.

**Por que ninguém tem.** Imutabilidade de estado de conhecimento com `corrected_by`; retratação por índice de subject com zero endpoint e zero registro novos; invariante contador↔índice que detecta backfill de contador reservado (a análise de lacuna aceita o ataque; a ordem de registro o rejeita); requisito normativo de interface anti-lavagem.

**Origem.** E01 (tese, drafts, suíte, fluxo, fossos, captura); `research/E01-drafts/`; E04 (RFC 9676, CNJ).  
supera: E06 apontava os drafts do D09 e mandava os três pelo Independent Submission — valem os drafts do E01 e a divisão de fluxo: dois perfis SCITT pelo IETF, Legal-Time pelo ISE.

---

## II.11 Ciência publicável

**Decisão fechada.** Quatro papers, na ordem que abre o canal de endosso primeiro e gasta GPU depois: **P1** C02 (apelido normativo como função de string e data), **P2** D06 (entropia condicional do processo civil — o de maior impacto), **P3** D05 (replay retemporalizado), **P4** A06 + A02 (WikiJurídica-Bench com alucinação corrigida por cobertura). arXiv primeiro, sempre. O endosso do arXiv (política endurecida em 21/01/2026) é portão de engenharia: sai do primeiro coautor. Os três I-Ds vão antes de qualquer paper.

**Mecanismo.**

| Paper | Contribuição medida | Experimento que falta | Venue 2027 |
|---|---|---|---|
| P1 C02 | resolução `resolve(forma, data_doc)`; cobertura 91,0% (IC95 Wilson ±1,93 pp) em 500 acórdãos; ~312 apelidos com janela | baseline ingênuo × método no mesmo conjunto + trap set | ICAIL 2027 (short) |
| P2 D06 | 1,528 → 1,409 → **1,326** bit/macro-evento (k = 1…3); k = 4 +1,0%; kernel 58×15 com 94,6% da massa | n-gram KN, GRU e Transformer compacto no mesmo holdout; réplica em PJe, e-SAJ e eproc; IC BCa por processo | ICAIL 2027 / JURIX 2027 |
| P3 D05 | replay retemporalizado a 25%, mistura 55/25/15/5; WJ-Retro de 360 itens com custo humano zero | ablação 5/25/50% em WJ-Retro; replay cru × retemporalizado | NLLP 2027 (EMNLP) |
| P4 A06+A02 | 2.700 itens, 8 trilhas, 7 programáticas, canário semântico | harness contra 6–8 modelos públicos; captura-recaptura de cobertura; 150 respostas de calibração do juiz | BRACIS/STIL 2027 |

Calendário: out/26 experimento do P1 e endosso; nov/26 arXiv P1 e réplica multi-tribunal; dez/26 arXiv P2 e datasets; jan/27 P1 + P2 ao ICAIL 2027; fev–mar/27 ablação do P3; abr/27 arXiv P3 e harness do P4; mai/27 P4 ao BRACIS/STIL; ago–set/27 P3 ao NLLP/JURIX. REED e *Artificial Intelligence and Law* recebem em fluxo contínuo. Coautores-alvo: Hudson de Martim (Senado; LRMoo/SAT-Graph, arXiv:2505.00039) primeiro, para P1; NEMO/UFES; equipe do JUÁ (arXiv:2604.06098); Maritaca (Magis-Bench, arXiv:2605.08437); CEPI FGV Direito SP. Rafael é o único autor humano (ACL e ACM: IA não é autora; uso declarado em Acknowledgements).

Datasets liberáveis: Bench-public (540 dos 2.700 itens, CC-BY-4.0, HF + DOI Zenodo; privados e 40 canários fechados); amostra de entropia (3.166 processos TJRJ, 63.366 movimentos, CC-BY-4.0); Código Civil tri-temporal (307 artigos, 677 eventos, CC0/CC-BY, Parquet); WJ-Retro (360 itens); tabela de apelidos (~312, CC0); corpus de fertilidade (2,4 MB, CC-BY). Ciclo ciência→produto: bench publicado → laboratório roda → rastro assinado no leaderboard → lead de `/verify` e `/reward` → 100 chamadas grátis por DID → falhas em `gap_queue` → o submodular escolhe o próximo experimento e o próximo paper.

Abstract do P2:

> We measure, for the first time, the conditional entropy of the coarse-grained event stream of Brazilian civil litigation, using proceedings drawn live from the CNJ public DataJud API. 49.1% of consecutive raw movement intervals are shorter than half a day, and the most frequent codes are clerical rather than decisional. A deterministic, versioned coarsening to 15 macro-events discards 48.1% of raw events while provably preserving every decisional one. Over this alphabet, conditional entropy falls from 1.528 bit/event at order 1 to 1.326 bit/event at order 3 and does not improve at order 4 (+1.0%, within bootstrap noise): the process is a bounded-order Markov chain. The transition kernel realizes 257 of 4,096 order-3 contexts, of which 58 cover 94.6% of the mass — 3.5 kB per legal-matter cell, 17.4 MB nationally. Small neural sequence models trained on the same temporally blocked split do not surpass the 1.326-bit floor, and the measurement replicates across PJe, e-SAJ and eproc courts. Planning over the kernel by Monte Carlo tree search costs about 12 ms per 20,000-simulation rollout on one CPU core, turning case-strategy simulation into commodity computation; we argue that entropy measurement should be a mandatory falsification gate before any neural architecture in predictive process monitoring.

**Números.** ~150–180 h de Rafael no ano; 80–120 GPU-h no ano, contra 24 GPU-h/dia de capacidade; as medições do P2 já existem (k = 4 dá 1,313 bit); baseline neural e réplica multi-tribunal são os experimentos de nov/26 que o abstract antecipa.

**Por que ninguém tem.** Primeira medição publicada da entropia do processo judicial brasileiro; primeiro benchmark jurídico com trilha prospectiva impossível de contaminar; primeiro corpus temporal brasileiro com aresta causal legível por máquina.

**Origem.** E06; D06; D05; C02; A06.  
supera: E06 ancorava o baseline em 767 citações/dia — vale ≥ 1.150/dia (CORREÇÕES §5, CANON).  
supera: E06 listava "o log Merkle de produção" como fechado — o log é público por construção (tiles, checkpoints, SCRAPI) e só carrega digests salgados com sal que nunca entra nele; o que não se publica é dump do log como dataset de pesquisa.

---

## II.12 Brainstorm: 40 funcionalidades, 8 escolhidas, fila estratégica

**Decisão fechada.** 40 funcionalidades — 23 de esforço P, 15 M, 2 G; 31 não tocam GPU. Corte por `score = V·F/E` (valor 1–5 × viabilidade 1–5 ÷ esforço P = 1, M = 2, G = 4). As 8 vencedoras saem em 60 dias (≈ 45 dias-engenheiro) e reusam mais de 90% de código já especificado; as cinco apostas de valor máximo formam fila estratégica com data. Para o cidadão leigo só entra produto cuja decisão é 100% determinística — o LLM, quando existe, narra o que o Go computou.

**Mecanismo.**

| # | Funcionalidade | Mecanismo | E | GPU |
|---|---|---|---|---|
| 1 | **Feed de Invalidação** | `receipt_id` → evento tri-temporal → push | P | não |
| 2 | `wj_lex_fori` | LINDB 7º–17 e CPC 21–25 como código | M | não |
| 3 | Marca d'água de procedência | Ward (RAG-DI) no texto derivado | M | geração |
| 4 | Cartório de Agentes | commit-reveal de acordo A2A no log | P | não |
| 5 | **Selo de Citação Verificada** | recibo + QR + verificador WASM | P | não |
| 6 | Mapa de Ataque | DISTINGUE/SUPERA + tese contrária mais forte | M | não |
| 7 | Relógio de Prescrição | CC 189–206 + movimentos TPU | G | não |
| 8 | **Memória de Cálculo Reexecutável** | big.Rat + séries com sha + replay | P | não |
| 9 | **Semáforo de Redação** | `INTERPRETA@sha` × redação atual | P | não |
| 10 | Atestado de Autos Limpos | mapa de taint por span dos autos | M | OCR |
| 11 | Detector de IRDR | `Contradicao` × repetição (CPC 976) | M | não |
| 12 | Auditoria de Aleatoriedade | movimento 26 "sorteio" + qui-quadrado | P | não |
| 13 | Sentença em Linguagem Simples | NLI bidirecional por frase | M | sim |
| 14 | Simulador de Impacto de PL | gramática ALTERA/REVOGA + grafo | M | não |
| 15 | Radar de Lex Mitior | ALTERA penal → execuções atingidas | M | não |
| 16 | Guia de Balcão por Voz | competência e prazo do C03 + TTS | M | ASR/TTS |
| 17 | Mapa de Direitos por Evento | `PosicaoJuridica` hohfeldiana | M | não |
| 18 | **Detector de Golpe Jurídico** | 6 verificadores determinísticos | P | ASR/OCR |
| 19 | Fotografe a Intimação | OCR + tabela TPU→frase + prazo | P | OCR |
| 20 | BR-LexTemporal | export CC0 do tri-temporal + errata | P | não |
| 21 | Meia-vida da Lei Revogada | `INTERPRETA@sha` × evento | P | não |
| 22 | Atlas de Contradições | nós `Contradicao` diários, k ≥ 50 | P | não |
| 23 | LexGym-BR | ambiente RL com o verificador | P | não |
| 24 | **Bolsa de Lacunas** | `gap_queue` → bounty x402 | P | não |
| 25 | Recurso contra o Verificador | rejulgamento pago + folha de emenda | P | Gemma-4 |
| 26 | Cosseguro de Citação | coassinatura reduz o prêmio | P | não |
| 27 | Diário do Impacto 06:00 | INLABS + cache-morte + caducidade de MP | M | narração |
| 28 | Espelho Autenticado | cópia oficial com prova byte a byte | P | não |
| 29 | Calendário Forense Nacional | portarias de ~90 tribunais | M | OCR |
| 30 | Alarme de Paralisação | sobrevida + conformal por célula | P | não |
| 31 | Motor Intertemporal | ~50 meta-regras LINDB/CPC/CP/CTN | G | não |
| 32 | **Simulador de Transição IBS/CBS** | vigência futura 2026–2033 | P | não |
| 33 | **Anexo de Lei Vigente** | `/norma?em=D` + alertas de transição | P | não |
| 34 | Risco de Superação Calibrado | hazard discreto + Prediction Receipt | M | não |
| 35 | Detector de Precedente Zumbi | autoridade sobrevivente ≈ 0 | P | não |
| 36 | Prova de Inexistência | SMT + monotonicidade número×ano | M | não |
| 37 | Farol de Vigência | beacon de eficácia a cada 60 s | P | não |
| 38 | Testamento Digital | dead-man de existência + Shamir 3-de-5 | P | não |
| 39 | Recompensa por Alucinação Sobrevivente | bounty a quem burla o `/verify` | P | não |
| 40 | Bot que usa a LAI | pedidos da Lei 12.527 automatizados | M | não |

*Os 8 escolhidos.*

**#5 Selo de Citação Verificada (score 25).** `POST /selo` (PDF/DOCX ≤ 25 MB) ou `wj_selo_peca` → MuPDF → normalizador (91,0% de cobertura, apelido resolvido pela data do documento) → E1–E7 + DV do número CNJ (MOD 97-10) → verdicts em enum {`ok`, `alterada`, `revogada`, `superada`, `nao_resolve`, `trecho_nao_confere`} — o schema não tem campo de mérito → recibo SCITT + anexo PDF de uma página com QR para `/s/{id}`, onde o verificador compilado em WASM confere tudo no navegador. A peça não persiste (só sha, citações e verdicts). 20 selos/mês grátis, R$0,90/selo, R$149/mês por escritório, Defensorias grátis; custo ≈ n_citações × R$0,00135. Meta: ≥ 1.000 selos/dia em 90 dias e ≥ 1 tribunal escaneando — o juiz conhece o padrão pelo QR.

**#18 Detector de Golpe Jurídico (25).** A avó encaminha "você tem R$12 mil a receber, pague a taxa". Seis verificadores determinísticos: `proc` (DV + DataJud), `norma` (URN + monotonicidade número×ano: "Lei 14.999/2026" falha por aritmética), `oab` (só pelo CNA), `dominio` (terminalidade oficial: `*.jus.br`, `gov.br`), `pagamento` (custas por guia oficial; levantamento por alvará não exige pagamento prévio, CPC art. 906), `prazo` (C03). Saída: `sinais[]` de 0 a 6, narração por template (nunca LLM, nunca "é golpe") e recibo para a família e a polícia. ≈ 6 dias. Precisão ≥ 0,95 contra alertas Febraban/Procon; zero casos de ≥ 3 sinais em intimação real do DJEN.

**#1 Feed de Invalidação (20).** Tabela `watch(client_kid, urn, receipt_id)`; gatilhos `AFTER INSERT` em `evento` (ALTERA, REVOGA, REPRISTINA, modulação), em aresta SUPERA/DISTINGUE forte/`Contradicao` e no fechamento de `vig_tese` → job River `notify-watchers`. Pull `POST /receipts/expired` e push WebSub assinado. Só `grau_certeza = 1,0` invalida; revogação tácita vira `aviso`. R$0,10 por 1.000 recibos-mês + R$0,001 por invalidação; p95 evento→push ≤ 90 s. Lock-in por invalidação: 100.000 citações/dia ⇒ 3M recibos/mês em circulação.

**#24 Bolsa de Lacunas (20).** Toda consulta com E1–E7 ou `s_max < 0,78` vira lacuna com `b_g = 0,3·E[receita M2M 90 d]` (ganho submodular × `v_q`), publicada se `b_g ≥ R$0,50` em `wj_gaps_list`, Nostr e Bazaar. `wj_gaps_submit` exige recibos emitidos pelo nosso `/verify`; portão URN + NLI + vigência → quarentena por reputação → publicação com `contributor_pubkey` → bounty x402 + dividendo. Só retrieval, nunca treino; orçamento ≤ 15% da receita M2M do mês; rejeição esperada de 40–60%.

**#9 Semáforo de Redação (20).** Consulta openCypher/AGE compara a redação que o acórdão interpretou (`INTERPRETA → RedacaoDispositivo@sha`) com a redação eficaz na data: verde (mesmo sha), amarelo (redação alterada, com diff e substitutos por PageRank com sucessão), vermelho (sem redação eficaz, com a cadeia até o sucessor), preto (acórdão superado). < 30 ms no edge; R$0,002/consulta; uma página pública por acórdão. Obsolescência em circulação estimada em 8–20% das citações de peças reais — Shepard's e KeyCite não têm a aresta `@sha`.

**#8 Memória de Cálculo Reexecutável (20).** Entrada JSON tipada, sem texto livre; `correcao.Regime()` em big.Rat, com o tramo `Instavel` da ADI 7.873 renderizado em dois cenários; séries BCB × IBGE consolidadas; honorários do art. 85 §§3º–5º por faixa. Artefato: PDF + `memoria.json` JCS + `engine_commit_sha` + `series_snapshot_sha` + assinatura + prova. `wj calc --replay` reproduz byte a byte, sempre grátis — o artefato se espalha pelas contadorias. R$9,90/memória; R$79/mês ilimitado.

**#33 Anexo de Lei Vigente (20).** Normalizador com apelido resolvido na data da assinatura → `/norma?em=D&modo=eficacia` para cada URN → varredura de futuro (`disp_versao` com início de vigência em `(D, D + prazo]`) → alertas de transição → recibo SCITT sobre o pacote. `wj_snapshot_contrato` para IAs de redação contratual; R$29/anexo ou R$0,05/URN.

**#32 Simulador de Transição IBS/CBS (20).** ADCT arts. 124–133 (EC 132/2023) e LC 214/2025 como `disp_versao` com vigência futura (o `EXCLUDE USING gist` garante não-sobreposição); `tributario.Transicao(ano, UF, município)`: 2026 IBS 0,1% e CBS 0,9%; 2027 extinção de PIS/Cofins; 2029–2032 ICMS/ISS a 90/80/70/60%; 2033 extinção; alíquota de referência do Senado ⇒ `Instavel` até publicar. ~150 dispositivos × 8 anos = 1.200 páginas imutáveis; `wj_transicao`; ≈ 5 dias.

*Fila estratégica.* #31 **Motor Intertemporal** — projeto de 90 dias em paralelo, o único que muda a natureza do tri-temporal: de "o que valia em D" para "qual D se aplica" (arXiv:2608.14610: LLMs aplicam a lei mais recente e erram mais com raciocínio mais forte). #36 **Prova de Inexistência** — exclusão em Sparse Merkle Tree (`pokt-network/smt` v0.14.1, raiz a cada 60 s) + monotonicidade número×ano: a negativa assinada contra a alucinação mais sancionada do mundo. #27 **Diário do Impacto 06:00** — INLABS minutos após o DOU, com a hora provada no log. Ambos no trimestre seguinte. #15 **Radar de Lex Mitior** (só contas institucionais, Cedar P-LEX, k ≥ 50) e #10 **Atestado de Autos Limpos** (comprador: PROSEG-IA do CNJ) completam a fila.

**Números.** Esforço dos 40: ≈ 490 dias-engenheiro; dos 8: ≈ 45. Receita incremental dos 8 em 12 meses: ≈ R$85 mil/mês [est.] = 71× o custo fixo, sem GPU nova; com um quinto disso (R$17 mil/mês) são 14×. O Selo gera 10–30 mil rótulos verificados/dia (10–30 citações × 1.000 peças), mais do que o bench inteiro (2.700 itens).

**Por que ninguém tem.** Verificação apontada para a vítima; selo verificável offline dentro da peça; cache de terceiros chaveado por recibos nossos; o direito futuro como produto imutável.

**Origem.** D02 (40, corte, desenho dos 8, fila).  
supera: D02 usava MiniCheck no Selo e Bespoke-MiniCheck-7B como instância do Recurso (#25) — o verificador é o wj-nli-54M; o recurso é rejulgado pelo professor Gemma-4-26B-A4B e a reversão vira par rotulado para o retreino, porque recibo sub-τ é inexprimível (I-VERIFY-1).  
supera: D02 media o custo contra o "teto de 12–22k chamadas/dia" — 31 das 40 não disputam a capacidade de 11.600 chamadas pagas/dia em regime (CANON).

---

## II.13 Tabela-resumo da Parte II

| Componente | Decisão | Número-chave | Origem |
|---|---|---|---|
| Portas das IAs | 4 portas físicas, todas ocupadas | GPTBot 27.685/semana; Claude 0 × Legal-BR 3,92× | E05 |
| Colheita | tool-call vira rótulo; crawler vira demanda | ≈ 3.100 itens/1.000 interações; ≈ 1.000 negativos | E05 |
| Efeito de rede | invalidação, agregação, lacunas disjuntas | `U(N) ≈ 0,997·U₁·N`; regret `ln N` | E05, B07 |
| Catálogo M2M | 9 produtos, 3 tocam GPU | 11.600 pagas/dia; ≈ US$26.500/mês | B08, CANON |
| `/verify` | código fechado + `span_entails_claim` | piso R$0,00135; balcão R$0,008; 109,9 ms | B01, E07 |
| MCP | 2026-07-28, dual-advertising | go-sdk v1.8.0; 15 tools; Registry v1.2.0 | B03, E04 |
| A2A | só agente↔agente com estado | a2a-go v2.5.0 | B03, E04 |
| Identidade de agente | Web Bot Auth; uma chave em quatro sistemas | JWKS em `/.well-known/…directory` | B03, B06 |
| Pagamento | x402 self-hosted primário; L402 secundário | `go/v2@v2.26.0`; `amount` 1554 = R$0,008 | B03, E04 |
| Precificação | posted price + bandit; Kaplan-Meier/Turnbull | regret `O((ln T)³/T)` | B01 |
| Negociação | SAOP `t_max = 6`, MiCRO, número fora do LLM | ρ = +0,053; limiar 1,37× | B01 |
| Stake | externalidade informacional | R$250/sessão (n* = 200) | B01 |
| Tesouraria | ADP com colchão, quarter-Kelly | R$7.195,58; 0,9150%/mês; payback ≤ 18 m | B02 |
| Cenários | três pisos re-rodados | P8: R$1,085 mi em 24 m, payback no mês 4 | B02 + esta Parte |
| Ledger | dupla entrada; 4 furos + corrida fechados | `cadeia_seq UNIQUE`; tolerância zero | B02, D10 |
| Fiscal | exportação pelo §14 | 15,500% → 10,672%; USDC D+0 | B02, E04 |
| Recibo e log | COSE/SCITT; bytes JCS assinados direto; log contínuo | 2.198 B; 172/233 µs; MMD 60 s | B06, E01 |
| Reputação | MeritRank derivado de `amp < 1` | α = 0,40, β = 0,60, amp = 0,600 | B06 |
| Segurança | 3 planos, taint, FROST, dead-man invertido | dano máximo R$100/dia + escrows | B04 |
| Corpus | retrieval-only + quarentena | 250 documentos; 30 dias | B04, E04 |
| Compliance | Cedar com veto; atestado vendável | 17 políticas | B05, E07 |
| Mercado de Procedência | Alegação Comprometida, scoring pago | `b_q·(1 − Brier)`; ln 200 = 5,3 nats | B07 |
| Moot court | prospectivo, gabarito TPU | n = 477/fluxo; 5% contrafactuais | B07 |
| Padrão aberto | 3 I-Ds, fluxo por restrição | cutoff IETF 127 em 02/11/2026 | E01 |
| Fossos | log, track record, série `tx` | meses 12 / 18 / 24 | E01 |
| Ciência | 4 papers, arXiv primeiro | 1,326 bit/macro-evento | E06 |
| Brainstorm | 40 → 8 + fila de 5 | 31/40 sem GPU; ≈ R$85 mil/mês | D02 |


# PARTE III — EXECUÇÃO
## Dados, direito-como-código, operação, crescimento e plano

Blueprint v3 · Wiki Jurídica IA-First · data-base 22/09/2026.
Autoridade: `CORRECOES-DONO.md` > `CANON.md` > E04 > E02/E07 > demais relatórios de `research/`.
Entrada de todo modelo desta Parte: **≥ 1.150 citações/dia** (23.000 em menos de 20 dias), **6.086 leituras verificadas de bot de IA/dia** (42.601 em 7 dias; GPTBot 27.685/semana) e **tráfego humano como terceiro canal** (H0 registrado no console no dia 1). Toda curva é piso. O modelo de crescimento re-ancorado é reprodutível: `blueprint/codigo/crescimento_reancorado.py` (numpy, 17 s). Cada seção segue Decisão fechada → Mecanismo → Números → Origem.

---

## III.1 Arquitetura de referência

**Decisão fechada.** O sistema é o da E07: nove camadas topológicas do edge ao metal, três planos físicos de segurança sobrepostos (D/C/T como três processos, não três structs), quatro interfaces que todo subsistema importa e nenhum redescreve, e a regra de enxerto — a arquitetura nasce em cima da plataforma que já cita: nenhuma URL muda e nenhum redirect nasce nos primeiros 120 dias; a IA em CPU de hoje só sai quando o artefato **quantizado** novo passar G1–G5.

**Mecanismo.**

*As nove camadas.*

| Camada | Tecnologia decidida | Origem |
|---|---|---|
| 0 Edge | CDN + Tiered Cache; conteúdo `.md/.json/.html` `immutable`; robots por classe; IndexNow; Tunnel com 2 conectores; R2; Workers de recibo e do C03 (Wasm); DO de reputação; chave canônica `?em=` | v2, A03, C06, D07, D01 |
| 1 Ingestão | River v0.47.0; DataJud PIT + `_shard_doc`; gatilho TPU; fontes oficiais; OCR em cascata; `staging_contrib` com quarentena de 30 d | C01, C05, C07, D05 |
| 2 Armazenagem e índice | PostgreSQL 18; pgvector + pgvectorscale; BM25 100% · denso 0.6B int8 · ColBERT tier-1; Parquet sha256 + manifesto Ed25519; WAL-G | A02, D01, C05 |
| 3 Conhecimento (0 GPU) | `temporal` e consolidação D0–D3; `grafo` (AGE 1.8.0 como projeção, forward push); `calc`; `jurimetria`; `sim` | A03, C02–C04, D06 |
| 4 Inteligência | vLLM 0.29.0 + FlashInfer 0.6.14; Qwen3-8B NVFP4; Gemma-4-26B-A4B sob demanda; llama-swap; `verify`; escalonador latchado; trie de URN + vocabulário +916 | A05, D01, D04, E02 |
| 5 Agente | Eino v0.9.19; memória em 5 camadas (`mem_fact` com `receipt_id` e `ver_id`); `Budget`; E1–E7; Cedar com veto | A01, B04, B05 |
| 6 Economia (Plano-T) | ledger; `econ.LambdaGPU`; x402 `go/v2@v2.26.0`; `nego/core ↛ nego/llm`; FROST 2-de-3 acima de R$2,50; CUSUM | B01–B04, D03, D10 |
| 7 Superfície | MCP go-sdk v1.8.0; recibo LAR + Merkle com MMD de 60 s; `/verify` `/norma` `/predict` `/simulate`; Web Bot Auth; Nostr | B03, B06, B08, D07 |
| 8 Operação | console D08; registry até `promotion_state`; G1–G5 no quantizado; Victoria + OTel GenAI; `wj-depcheck`; notebook | C05, D08, D10, E07 |

Metal: Ryzen 7 9800X3D, RTX 5060 Ti 16 GB (sm_120), 96 GB DDR5, NVMe 2 × 4 TB, nobreak, 24/7 = 86.400 GPU-s/dia.

*Três planos.* D lê a internet e nunca emite intenção; C decide e só consome valores tipados por socket Unix; T (tesouraria) não tem LLM nem egress de leitura. Sete travessias tipadas: T1 D→C `TypedFact{URN, Anchor, SHA, NLI, Taint}`; T2 C→T `SpendIntent` + macaroon (`exp=180s`, `payee_sha256`, `taint_attestation=0`); T3 T→C `SettlementFact`; T4 C→D `FetchRequest` com allowlist; T5 humano→C `IntentCandidate` (a fala do Rafael entra pelo Plano-D); T6 C→público com FK composta; T7 C→nuvem com veto Cedar na borda. Taint monotônico: `Restringir()` nunca readmite `CapSpend`. Dead-man invertido: o lease expira em 180 s e só o heartbeat assinado (G1 verde, CUSUM < 3σ) o renova.

*Quatro caminhos, latência acumulada.* (a) Crawler pede answer unit: TLS 4,0 → PoP com chave canônica 5,2 → lookup 6,0 → 200/304 `immutable` = **8,0 ms** (orçamento 200 ms; no pior caso, miss no PoP e no Tiered com pull do R2, 100,2 ms e origem intocada). (b) Agente externo, `/verify` + x402: o 402 sai do Worker em 6,4 ms sem tocar a origem; X-PAYMENT (EIP-3009) 14,4 → reputação no DO 22,4 → Tunnel 47,4 → NER 55,4 → URN e vigência 57,6 → NLI 79,9 → relevância 83,9 → recibo 84,9 → volta = **109,9 ms** (orçamento 400 ms). (c) Advogado: BM25 69,3 → denso 89,3 → PPR 96,0 → ColBERT 144,0 → cross-encoder 284,0 → prefill com prefix hit = TTFT **584 ms**; decode de 600 tokens e NLI de 12 claims fecham em **10,87 s** (orçamento 45 s), com `wj/calc` em paralelo ao prefill. (d) Ciclo autônomo: **0,81 GPU-s por unit** em lote ×8 a 1.408 tok/s — o custo mínimo de engine; o cronograma usa 8 GPU-s (E03) e o regime 5,507 (E02), e a distância é a folga de tuning de 7,6× sob o roofline.

*Módulos Go.* Monorepo `module wj` (Go 1.27), seis camadas de importação, 25 pacotes em `deps.yml`, verificados por `cmd/wj-depcheck` com `go list -deps` — fecho transitivo, que pegou o violador real `nego/core → nego/util → nego/llm` que um grep deixaria passar: 0 `lex`, `tipos`; 1 `calc`, `temporal`, `grafo`; 2 `verify`, `receipt`, `policy`; 3 `retrieve`, `serve`, `jurimetria`, `sim`; 4 `agent`, `nego`, `econ`; 5 `api`, `mcp`, `edge`, `mlops`, `console`. Proibições: `nego/core ↛ nego/llm` (antitruste: correlação residual de preço +0,053); `sim/core ↛ sim/llm`; `receipt ↛ verify` (terceiro verifica o recibo sem rodar nosso NLI); `policy`, `calc`, `grafo ↛ serve`; `econ/tesouraria ↛ agent`, `serve`, `net/http`; `edge ↛ econ/tesouraria`, `nego`, `serve`, `database/sql`; `console ↛ econ/tesouraria`. Literais de fonte única: λ_gpu só em `econ/`, τ só em `verify/`, R$2,50 e 180 s só em `econ/tesouraria/`. Sete pins; o CI recusa `latest`.

*Quatro interfaces unificadas.* (1) **Verificador** — `verify.Verify(ctx, Claim, Query) (Result, error)`: V1 URN resolve · V2 âncora existe naquela redação · V3 wj-nli-54M ≥ τ · V4 vigência em `At` · V5 divergência do determinístico · V6 contradição · V7 relevância; `Tau` vem de `conformal_calibration`; `Receipt != nil` só em `Pass`. (2) **Preço-sombra** — `econ.LambdaGPU(ctx)`, multiplicador de Lagrange do BwK (`λ ← λ·(1+η)^(c−B/T)`, η = 0,05), semente R$0,00090/GPU-s; `Whittle()` devolve o mesmo número; `Burst(ctx, Job)` com veto Cedar. (3) **Recibo** — `lar.Receipt`: JCS restrito + Ed25519 sobre os bytes JCS + folha RFC 6962; `Verify(cp, fonte)` confere assinatura, janela, inclusão, consistência e `sha256(fonte[off:off+len]) == span_sha256`; `Verdict` tem um valor só, `span_entails_claim`; `iss = did:web:wikijuridica.com.br` (a PJ). (4) **Política** — `policy.Eval` em cedar-go v1.8.0 no nó `compliance`, na borda do burst e antes de publicar; Deny terminal; `policy_set_version` dentro da FK da promoção.

*Existe × novo.* **No ar** (camada 0; produz as ≥ 1.150/dia e não para): 11.106 páginas, `llms.txt`, sitemap de 11.147 URLs; `/mcp` com 15 tools no MCP Registry (`br.com.wikijuridica/acervo-juridico` v1.2.0); agent-card A2A; ai-catalog; OpenAPI de 13 operações; `/api/v1/lote` NDJSON; `/api/v1/citar` com `repr_digest` RFC 9530; `/api/v1/citacoes` (= `/verify`); 6 datasets sha256 (585.592 registros); `Accept: text/markdown`; robots com Content-Signal por família; radar de bots com IP verificado; IA em CPU servindo. **Escrito pela frota** (entra no repositório na Sessão 1): `research/C03-code/`, `research/B06-code/lar.go`, `research/D10-code/`, `research/E07-arquitetura/` (`schema.sql` com 44 tabelas, `deps.yml`, `depcheck.go`, `arquitetura.html`), `research/E02-code/`, `research/D08-console/index.html`, `research/B02-modelo-financeiro.py`, `research/E01-drafts/`, `research/E08-plano/checklist.md`, `blueprint/codigo/crescimento_reancorado.py`. **Novo**: todo o resto — construído em cima, nunca no lugar.

*Doze componentes do caminho crítico:* C1 `wj/lex` → C2 schema tri-temporal → C3 ingestão P0 → C4 `wj/verify` → C5 `lib/lar-go` + Merkle → C6 Cedar → C7 plano de conteúdo v2 (o enxerto) → C8 `wj/calc` + Wasm → C9 serving → C10 índice em 3 camadas → C11 Plano-T + x402 → C12 superfície M2M. `wj/verify` é o nó de maior grau (seis subsistemas dependem dele, cinco o consomem) e precede o serving porque o roteador conformal **é** o verificador usado como sinal de risco.

**Números.** 9 camadas · 3 planos · 7 travessias · 25 pacotes · 7 pins · 44 tabelas · 28/28 ataques ao schema recusados (PG 16.13) · 8,0 ms / 100,2 ms / 109,9 ms / 10,87 s (TTFT 584 ms) / 0,81 GPU-s · `/verify` = 0,022 GPU-s, 0,56% do dia a 22.000 chamadas.

**Origem.** E07 (`arquitetura.html`, `schema.sql`, `deps.yml`, `depcheck.go`); B04; CANON.

---

## III.2 Fontes oficiais e ingestão

**Decisão fechada.** Ingestão é um conjunto de jobs River atrás de `Fonte{Nome(); Buscar(ctx, cursor) (docs, prox, err)}`, rodando do IP brasileiro de Queimados — o bloqueio visto no sandbox era de ASN, não de produção. O DataJud é **gatilho**, não corpus. Toda fonte oficial chega por dois egressos (link doméstico + VPS em outro AS via WireGuard) e só entra no WARC se os hashes baterem; `unbound` valida DNSSEC e a CA é pinada por host.

**Mecanismo.**

*Tabela mestra.*

| Fonte | Formato | Volume medido | Estado testado | Tratamento | P |
|---|---|---|---|---|---|
| DataJud | ES/JSON, APIKey pública | TJSP 75.255.331; TJRJ 24.032.886; STJ 3.624.936; delta do TJRJ 106.819/24 h | 20–58 s/req; `size=100` → 504 aos 60 s; `size=5000` em 19,9 s | PIT + `_shard_doc`; timeout < 60 s; 3–4 workers | P0/P1 |
| DJEN/Comunica | JSON | — | 403 CloudFront (geo, sandbox) | portão do dia 1 no IP de produção; senão o DataJud absorve o gatilho | P0 |
| Planalto | HTML sem charset | 6 leis parseadas | 200 com UA de navegador | colly; sniff ISO-8859-1 por documento | P0 |
| Câmara | JSON | 21.362 proposições | 200, sem auth | `rel=next` | P0 |
| Senado | JSON | 2,47 MB/consulta | clássico desativado em 01/02/2026 | só `/dadosabertos/processo` | P0 |
| CVM | CSV/ZIP | 54 datasets; ZIP de 121.134 B | 200, reproduzido byte a byte | download direto | P0 |
| SGT/TPU | SOAP | ~1.600 assuntos, ~1.300 classes | 200, v.1.26.00 | `getDataUltimaVersao` dispara reingestão | P0 |
| BCB SGS | JSON | 6 séries | 502 com HTML em rajada | 5 tentativas, 400 ms × 2^k até 8 s, detecção de HTML com 200 | P0 |
| IBGE SIDRA | JSON | 18/18 pontos batem com o BCB | `apisidra` → challenge Cloudflare | `servicodados.ibge.gov.br/api/v3/agregados` (200); `rod` de reserva | P0 |
| STJ CKAN | CSV/JSON | — | 403 (WAF do STJ) | reteste do IP BR; `rod` | P1 |
| STF | SPA + PDF | — | cadeia SSL incompleta | AIA chasing em Go via `IssuingCertificateURL` | P1 |
| LexML | SRU/URN | milhões de URNs | SRU → reCAPTCHA (9.050 B); `/urn/` 200 | `rod` com sessão, 1 req/3–5 s; P3 pela API de `normas.leg.br` | P1 |
| e-SAJ | HTML | — | 200 sem bloqueio | disparado por evento do DataJud | P2 |
| PJe/eproc/Projudi · TCU · CARF | JSF · SPA 401 | ~90 sistemas | ViewState · token de app | `rod` com sessão | P2 |
| Querido Diário · DOU | JSON · sem API | — | instável | self-host · INLABS | P3 |
| Base dos Dados | BigQuery | — | slug não localizado | dia 1: mirror bulk antes de varrer | P0 |

*DataJud: PIT + `_shard_doc`.* `from+size` para em 10.000 e ordenar por `id` ou `numeroProcesso` devolve 400 "fielddata is disabled". A solução, executada ao vivo em 3 páginas monotônicas sem gap nem duplicata: `POST /api_publica_{alias}/_pit?keep_alive=5m` e `POST /_search` sem índice, com `sort: [{"@timestamp":"asc"},{"_shard_doc":"asc"}]` e `search_after` — vale para os ~90 índices sem mudança no mapeamento do CNJ. Escopo por movimento em `query.bool.filter` (92, 1061, 581, 219–221, 237–239, 848) + corte de `dataAjuizamento`. Delta nacional em `size=5000`: ~200 páginas × 20 s ÷ 3 workers ≈ **22 min/dia**. Dedup por `numeroProcesso + tribunal + grau`, com merge append-only de movimentos gravados como array binário `(uint16 código, uint32 dias)`: 11 KB → 1,5 KB por documento.

*Gatilho de scraping por movimento do DataJud.* O job `movement-watcher` lê o delta diário, filtra 92 (Publicação), 1061 (Disponibilização no DJE) e 581 (Documento) e publica `(tribunal, numeroProcesso, urn_provável)`; os fetchers de cada sistema consomem essa fila em vez de cron próprio. O inteiro teor passa de O(todos os processos, todo dia) para O(processos com decisão nova hoje).

*Planalto.* Nenhum arquivo declara charset: detecção por documento (`golang.org/x/net/html/charset`). A aresta causal está nos links "(Redação dada…)". Byte a byte é impossível — a CF tem 780 tachados e 66 "(Vide ADI"; a CLT, 37.788 `&nbsp;` e 2 redações de MP dentro do consolidado; a Lei 14.195, 94 linhas "......" e 40 cláusulas de vigência —, então compara-se forma canônica (NFC → sem tags → espaço colapsado → º/°/`<sup>` normalizados → sem notas parentéticas) em classes D0–D3, com ADI/ADPF/MP como overlay e o texto do Senado (P3) como árbitro.

*Corpus: 1.085 GB (27,1% de 4 TB).* DataJud 125 · inteiro teor 290 · BM25 300 · denso 29 · ColBERT 58 · AGE 35 · `citacao` 38 · modelos 100 · Merkle/WAL 100 · recortes de selo 10. As 5 M páginas-imagem não são guardadas: o original é refetchável e o sha256 fica no recibo.

*Plano de 90 dias.* D1–7: mirror do DataJud na Base dos Dados; Câmara, Senado, CVM e Planalto do IP de produção. D8–25: delta nacional + backfill escopado nas 10 maiores unidades + `rod` (LexML, STJ). D26–50: e-SAJ por evento + AIA chasing do STF. D51–75: PJe/eproc/Projudi por volume + TCU, CARF e Receita. D76–90: Querido Diário, DOU, ANPD, CJF, dedup cross-fonte e primeira rodada do Merkle sobre o corpus. O backfill nunca está no caminho crítico: ao D06 bastam 800–1.200 casos por célula, e o kernel saiu de 3.166 processos.

**Números.** 75.255.331 documentos no TJSP; 20–58 s/req; delta ≈ 22 min/dia; 11 → 1,5 KB/doc; corpus 1.085 GB; Câmara 21.362; CVM 54 datasets; Senado clássico desativado; SIDRA 403 → `servicodados` 200.

**Origem.** C01; D01 (504, `size=5000`, Planalto); E04 (CVM, SIDRA, STJ, Senado); E02 (disco); E08 (sequência).

---

## III.3 Grafo de conhecimento

**Decisão fechada.** Reusam-se cinco ontologias e inventam-se quatro classes. O grafo é particionado por custo: 101,4 M arestas tipadas numa projeção AGE 1.8.0; 200 M arestas de citação bruta em tabela particionada fora do AGE; ~400 M movimentos fora do grafo, como propriedade agregada de `Processo`. A verdade é relacional — `aresta(src, dst, tipo, vig, efic, conf)` + `WITH RECURSIVE` + CSR em Go; Cypher é view. Zero LLM na indexação; PPR só por forward push.

**Mecanismo.**
- *Ontologias:* LRMoo (Work/Expression/componente); LKIF-Core `time-modification.owl` (CC BY 4.0, já nomeia `In_Force_Interval`, `Efficacy_Interval`, `Ultractivity`); UFO-L (Hohfeld + Alexy); TPU/CNJ inteira via SOAP do SGT; Akoma Ntoso `<judgment>` para spans do voto; schema.org/`Legislation` e ELI como projeções; LegalRuleML só nas ~50 meta-regras. Inventadas: `Tese` bitemporal (CPC art. 927 §3º), `RedacaoDispositivo`, `PosicaoJuridica`, `Contradicao`.
- *Classes e arestas:* 17 classes (Parte só por hash, nunca nome). Arestas com confiança de extração: ALTERA 1,000; REVOGA 1,0 expressa / 0,4–0,8 tácita; REPRISTINA só por regra (LINDB art. 2º §3º expressa ou Lei 9.868 art. 11 §2º); REGULAMENTA 0,95; **INTERPRETA(Decisão → Redação@sha)** 0,90 por join `eficacia @> data_julg`; APLICA 0,88; FUNDAMENTA 0,93; DISTINGUE 0,80; SUPERA por Dempster–Shafer; CITA 0,97 (fora do AGE); E_COMPETENTE_PARA com ~500 regras curadas; RECORRE_DE pelo checksum CNJ (1,000); INSTITUI 0,82 (experimental, nunca no grounding).
- *Povoamento sem LLM:* gramática PEG ∪ NER `pierreguillou/ner-bert-base-cased-pt-lenerbr` via hugot (F1 0,884 em legislação, 0,702 em jurisprudência) + resolvedor de mundo fechado — candidato que não resolve é descartado. LLM custaria 42 G tokens = 4.227 dias-GPU contra 2,78 h de gramática em 8 núcleos (36.522×); com o NER por documento corrigido pelo D01, o backfill é 2,7 M núcleo-s = 8 dias no notebook: 528× abaixo do LLM, 0 GPU.
- *Resolução de entidade:* 91,0% fim a fim (93,2% / 87,5%; IC95 ±1,93 pp em 500 acórdãos); o DV do CNJ dá arestas de confiança 1,000 e o tribunal pelo segmento J; dedup exato (~85%) + MinHash b=16 × r=8, recall 99,38% em J ≥ 0,85, 596 MiB.
- ***apelido = f(string, data)*:** `apelido(forma_norm, urn_alvo, janela daterange, peso)` com `EXCLUDE USING gist (forma_norm WITH =, janela WITH &&)`. "Lei de Licitações" = 8.666/93 em `[1993-06-22, 2023-12-30)` e 14.133/2021 depois; `cpc` = 5.869/73 até 2016-03-18; `licc` vira `lindb` em 2010-12-30. Empate ⇒ INDETERMINADO; consulta sem data ⇒ as duas resoluções com janelas. Semente de ~312 apelidos das ementas do Planalto.
- *Forward push:* O(1/(α·r_max)), independente de |E|; α = 0,15 e r_max = 1e-4 ⇒ ≤ 66.667 pushes ≈ 6,7 ms, contra 180,86 s de power iteration sobre 301 M arestas; manutenção incremental Zhang–Lofgren–Goel no delta diário; sucessão de autoridade (o superado redireciona massa ao superador); VLE com k ≤ 6 e guarda de grau < 5.000.
- *Inferência:* Datalog estratificado compilado para `WITH RECURSIVE` (revogação desce a mereologia; não-repristinação como regra negativa explícita; inconstitucionalidade ex tunc/ex nunc com modulação; competência herdando a subárvore TPU) + lógica defeasible de complexidade linear para herança de tese, com `distingue` como defeater (50 meta-regras, < 1 ms).
- *Contradição materializada:* C1 mesma questão @sha com resultado oposto e sem SUPERA/DISTINGUE; C2 redação fora de eficácia na data do fato (a mais vendável); C3 precedente citado já superado; C4 teses opostas de tribunais distintos. Cada uma é nó com URN, recibo Ed25519 e contestação, servida pelo `/verify` como lookup. Aresta de comunidade entra com conf ≤ 0,5 e nunca em SUPERA/REVOGA.

**Números.** 40,6 M nós / 301,4 M arestas; AGE 19,1 GiB; `citacao` 38 GB; CSR 2,55 GiB; PPR 6,7 ms; 36.522× e 528×; 91,0%.

**Origem.** C02; D01; E02; E07 (`apelido`, `citacao` no schema).

---

## III.4 Direito-como-código

**Decisão fechada.** A fronteira é a classe do token: todo token calculável — data, valor, percentual, prazo, número de processo — sai de Go; citação normativa é a única exceção, porque é verificável no índice. O motor devolve intervalo, não número; aritmética em `big.Rat`; índice ausente recusa o cálculo (`ErrMesFaltante`). O código existe — `research/C03-code/`, 4.626 linhas, 6 pacotes, 0 dependências, testes passando — e entra como `wj/calc`, recompilando para TinyGo/Wasm no edge sem mudar uma linha.

**Mecanismo.**
- *Três camadas (`mcp/guarda.go`):* (1) GBNF cuja prosa é `[^0-9{}]+` — onde caberia número só cabe `{{c1.vencimento}}` —, com o ajuste do D01: vocabulário fechado de ordinais ("13º salário", "1ª instância") e `cit-tipo` estendido (Decreto, MP, IN, ADI, ADPF, HC, AgInt, EREsp, "8.666/93"); (2) **verificador de ancoragem numérica**: todo token calculável da resposta que não bater com valor devolvido por ferramenta da sessão é rejeitado, com formas canônicas (`2026-03-27 ≡ 27/03/2026`; `201421.69 ≡ R$ 201.421,69`) e faixas de citação normativa; (3) erro E5 + recompensa −1,0. Um dia ou um centavo de divergência é rejeitado; como gramática não garante aceitação (arXiv 2608.28229), I-NUM-1 é tipo + monitor M3. O verificador roda sobre saída de qualquer modelo — é um `/verify` de número.
- ***Intervalo nominal/estrito*:** feriado carrega `Confianca ∈ {LEGAL, PRESUMIDO, EXPEDIENTE_REDUZIDO}` e o cálculo roda duas vezes: 30 dias úteis a partir de 10/03/2026 vencem em 22/04 com a Sexta-feira Santa presumida e em 20/04 sem ela. Regra vendável: protocole até o estrito. O tipo `Prazo` só expõe `DataSeguraDeProtocolo()` e `Intervalo()`.
- *Prazos (CPC/CLT/CPP/JEC) e calendário:* Páscoa por Meeus/Butcher; Consciência Negra desde 2024 (Lei 14.759/2023); JF com feriados por lei (Lei 5.010/66 art. 62), distintos da suspensão do CPC art. 220 — o mesmo prazo é certo na JF e incerto no TJ. Casos que IA global erra: Juizados sem dobro da Fazenda (Lei 10.259 art. 9º; Lei 12.153 art. 7º); art. 229 §2º; CPP art. 798-A (réu preso e Maria da Penha sem suspensão); art. 231, IX; art. 224 §1º; CLT arts. 775/775-A; divergência sobre cumulação de dobros declarada.
- ***Trilha negativa de competência*:** `Decidir()` devolve as 16 regras, inclusive as que não dispararam e por quê — é o caminho que vai para a petição.
- *Correção monetária:* `correcao.Regime()` é árvore temporal. Contra a Fazenda federal: IPCA-E + poupança (Temas 810/905) → Selic única, limitada pelo STF a 09/12/2021–09/09/2025 (Tema 1.419) → CC como supletivo (REsp 2.236.270/SP). A EC 136/2025 restringiu o art. 3º da EC 113 a requisitórios federais (IPCA + 2% a.a., teto Selic) sem repristinar o art. 1º-F da Lei 9.494; o Acórdão CJF 0882268 revisou o Manual de Cálculos; tudo está sub judice na **ADI 7.873** ⇒ tramo `Instavel=true` + revisão humana. Execução real contra o BCB: R$ 100.000,00 de 06/2019 → R$ 201.421,69 em 08/2026. Art. 406 §1º: diferença aritmética e deflação de Fisher implementadas e provadas divergentes. BCB × IBGE reconciliados ponto a ponto (18/18); divergência bloqueia o selo.
- *Validadores:* DV do CNJ por ISO 7064 MOD 97-10, validado em 131 números reais (127 fecham; os 4 com `OOOO = 8000` são do SEI, e o validador explica e sugere o DV consistente). A OAB **não tem** dígito verificador: `ValidarOAB` jamais devolve `Verificado=true` sem recibo de consulta ao CNA. CNPJ alfanumérico sai com `RegraConfirmada=false`.
- *As 4 tools MCP* — `wj_prazo`, `wj_correcao`, `wj_competencia`, `wj_validar`, com `structuredContent` + `outputSchema` e campo decisório primeiro — entram no `/mcp` existente (15 → 19).
- *Os 10 computáveis abertos:* dosimetria (Súm. 231); prescrição e decadência (autômato temporal; a retroativa compõe com a pena); honorários do art. 85 §3º com o §5º aplicado por faixa (erro quase universal) e o §8º-A; cálculo trabalhista (grafo de verbas); preparo e deserção; partilha e legítima; ITCMD/ITBI (27 tabelas); revisional (Price × SAC, CET, Súm. 539 e 472); previdenciário (EC 103/2019); cabimento recursal, que fecha o **semáforo de admissibilidade**. Mesma espinha: tabela oficial versionada + aritmética exata + traço + eixo de confiança.

**Números.** 4.626 linhas; cobertura mcp 96,8%, validador 92,0%, correcao 70,7%, prazo 73,2%; 2.400 combinações de propriedade; 4 tools = 50 ms = 1,7% do teto M2M; 0 GPU; 127/131 números CNJ; 18/18 INPC.

**Origem.** C03; D01 (GBNF); D10 (`Prazo`, I-NUM); D07 (Wasm).

---

## III.5 Jurimetria

**Decisão fechada.** Jurimetria é sobrevivência sobre o fluxo de movimentos TPU: hazard discreto multinomial person-period em LightGBM, com quatro classes por período (nada, sentença, acordo, extinção), servido em Go por `leaves` a 1,4 ms por curva e 0 GPU. Perfilamento de magistrado é impossível por construção. Toda previsão sai com `skill_vs_baserate` e vira Prediction Receipt antes de o movimento existir.

**Mecanismo.**
- *Os 14 campos do DataJud:* `id, tribunal, grau, numeroProcesso, dataAjuizamento, nivelSigilo, orgaoJulgador{codigo, nome, codigoMunicipioIBGE}, classe, sistema, formato, dataHoraUltimaAtualizacao, @timestamp, movimentos[], assuntos[]` — sem valor da causa, partes, advogado ou juiz; `movimentos` não é `nested` ⇒ harvest completo e reconstrução local, zero agregação online.
- *Alvos verificados no SGT:* mérito 219/220/221; prescrição 471; acordo 466/377; extinção 455–465; trânsito 848; baixa 22; recurso 237/238/239; marcos de fluxo 26 (distribuição com `sorteio`), 332/889 (tutela), 339/892, 970, 106.
- *Riscos concorrentes:* `S(m|x) = Π_{j≤m}[1 − Σ_k h_k(j|x)]` e `F_k(m|x) = Σ_{j≤m} h_k(j|x)·S(j−1|x)` ⇒ `Σ_k F_k + S = 1` por construção; Fine–Gray só como checagem offline; Cox, DeepSurv, RSF e DeepHit rejeitados.
- *Case-cohort:* 59 M processos × ~24 meses = 1,4 bi de linhas → todos os eventos + subamostra 1:4 com peso Horvitz–Thompson ⇒ ~180 M; 28 bins; treino semanal em CPU (~6 h, `max_bin=255`, 9 GB residentes) na folga.
- *Features sem vazamento:* `FeatureSpec{AvailableAt, LeakClass}`; o CI falha se `LeakClass == 2` ou `AvailableAt > t_corte`; um modelo por Δ ∈ {0, 30, 90, 180} dias. B0 ex-ante; B1 fluxo (tutela; mandado "não entregue" ⇒ réu não localizado); B2 institucional defasado um ano; B3 base-rate da célula em janela expansiva com lag; auditoria por permutação.
- ***IV de leniência da vara*:** o movimento 26 traz `complementosTabelados{codigo: 2, nome: "sorteio"}`; instrumento = taxa leave-one-out de concessão de tutela da vara em t−1; 2SLS; teste Frandsen–Lefgren–Leslie obrigatório; a unidade é a vara, nunca o juiz; entra em produção no gatilho de ≥ 500 mil processos reconstruídos.
- *Regulação como constraint:* a Res. CNJ 615/2025 (alterada pela 674/2026) classifica técnica jurimétrica como BR3, baixo risco, e o art. 10, II–III vincula o Judiciário. A vedação real é francesa (Loi 2019-222 art. 33 → COJ L.111-13), usada como contraste e como especificação exportável; o EU AI Act é coberto por `permitted_use` assinado. Constraints: nenhuma coluna `judge_id`; k-anonimato n ≥ 50 via **Cedar P18** com veto; detector de ataque de diferenciação por DID; `vedado = {fundamentacao_judicial, selecao_de_juizo, avaliacao_de_magistrado}`; `/predict` devolve a distribuição do foro, nunca ranking de varas.
- *`/predict` e Prediction Receipt:* CIFs em 28 bins, sobrevida, LPB com IPCW, `n_cal`, cobertura empírica, `base_rate_celula`, **`skill_vs_baserate`** (NOT NULL — acertar 72% onde a base-rate é 70% vale zero), `k_anon_n` (CHECK ≥ 50), `permitted_use`, `calib_hash` e recibo. O **Prediction Receipt** é folha no Merkle antes do movimento TPU: track record auditável por terceiro; perfil em `research/E01-drafts/draft-toledo-scitt-forecast-receipts-00.md`.
- *Ponte com o world model (D06):* 15 macro-eventos; H(k=3) = 1,326 bit; kernel 58 × 15 com 94,6% da massa (17,4 MB); MCTS de 20 mil simulações × horizonte 12 ≈ 12 ms num núcleo ⇒ `/simulate` no edge, com `counterfactual_class` e `worst_case_cf_error`; transformer proibido até bater 1,326 bit.
- *Avaliação:* C-index de Uno; IBS de Graf com IPCW; AUC-PR, ECE, Murphy; walk-forward em 18 dobras desde 2016 (CV aleatório proibido); trilha (k) do WJ-Bench com N = 600 e gabarito = movimento futuro; G2: R ≥ 0,15 e cobertura em [0,88; 0,93]; BCa por vara; paridade `leaves` × LightGBM 4.7 em 10 mil objetos no CI, com fallback ONNX.

**Números.** 14 campos; 1,4 bi → 180 M linhas; 1,4 ms/curva; k ≥ 50; 18 dobras; 1,326 bit; MCTS 12 ms; Justiça em Números 2026: 59 M em tramitação, congestionamento líquido 56,6%.

**Origem.** C04; D06; D01; E07 (`prediction_receipt`, `simulation_receipt`); E08.

---

## III.6 Entrada e saída do mundo

**Decisão fechada.** Toda modalidade segue o mesmo princípio: número vem de código, afirmação vem de span verificado e a escalada entre modelos é decidida pelo verificador — nunca pela confiança do modelo. Licença é filtrada por schema (`license_spdx` com CHECK).

**Mecanismo.**
- *OCR em cascata.* Estágio 0 em Go/MuPDF (0 GPU): < 200 caracteres por página ⇒ imagem; hit-rate no dicionário pt-BR < 0,85 ⇒ camada ruim; senão pula OCR (~60% das páginas); PP-OCRv5 em CPU resolve ~70% do resto. Estágio 1: **PaddleOCR-VL-0.9B** (Apache-2.0, OmniDocBench 96,3%) ou **`opendatalab/MinerU2.5-Pro-2605-1.2B`** (Apache-2.0, 95,30) — ID exato com teste de CI, porque o `MinerU2.5-2509` é AGPL e está proibido. Estágio 2 só quando o **verificador** escala (confiança < 0,90, carimbo sobre texto ou colunas com ordem de leitura divergente): **`datalab-to/chandra-ocr-2`** (5,30 B, olmOCR 85,8%; teto de US$2 M da OpenRAIL-M monitorado na tesouraria; DeepSeek-OCR, MIT, como saída). Estágio 3: fila humana (< 2–3%). Só ~12% das páginas chega a VLM. Layout: **PP-DocLayout-L** (Apache-2.0, mAP 90,4%, 23 classes com selo); DocLayout-YOLO (AGPL) e LayoutLMv3 (não comercial) fora. Selo e assinatura são recortados como evidência, nunca lidos. Códigos de ingestão: `OCR_CONFIANCA_BAIXA`, `ASSINATURA_ICP_INVALIDA`, `CHECKSUM_PROCESSO_FALHOU`.
- *Voz.* faster-whisper large-v3-turbo (MIT; ~49× tempo real numa 3070 Ti — medido no metal antes de SLA) com hotwords jurídicas; whisper.cpp no notebook; todo número CNJ transcrito passa pelo MOD-97, senão o campo fica `null`. TTS: **Kokoro-82M** (Apache-2.0, pt-BR, CPU) em lote; **Chatterbox** (MIT, clonagem zero-shot) só com `consentimento_id` assinado — Cedar veta voz de terceiro. XTTS-v2 e F5-TTS fora por licença. Produto: ata de audiência com portão NLI bidirecional ata ⇄ transcrição no wj-nli-54M; frase não sustentada ⇒ abstenção.
- *Linguagem simples verificada — a avó do Rafael como teste de aceitação:* `ILF_PT = 248,835 − 1,015·(palavras/frases) − 84,6·(sílabas/palavras)`; publica se ILF ≥ 60 ∧ ganho ≥ 25 ∧ NLI(canônico ⇒ simples) ≥ τ_s ∧ NLI(simples ⇒ canônico) ≥ τ_s — nada acrescentado, nada essencial perdido; τ_s recalibrado por conformal em corpus de paráfrase, sem herdar o 0,906.
- *WCAG 2.2:* a árvore ementa/relatório/voto/dispositivo vira headings e landmarks ARIA de graça; 2.4.11, 2.5.8 (alvo de 24 × 24 px nas âncoras), 3.3.8 e contraste ≥ 4,5:1 como gate de CI.
- *Sistemas processuais:* o MNI (SOAP) é o único padrão de escrita e exige o certificado do peticionante; e-SAJ e Projudi não têm API. A plataforma **consulta** e **nunca peticiona por terceiro**; produto seguro = agente-cliente que o próprio advogado autoriza com o certificado dele, assinatura local, sem custódia de chave.
- *ICP-Brasil × Ed25519:* Ed25519 é integridade técnica (172 µs) e assinatura avançada no circuito M2M (MP 2.200-2 art. 10 §2º, aceite no handshake x402/MCP; Lei 14.063 art. 4º II). ICP-Brasil PAdES é a qualificada (art. 10 §1º) para o que sai do circuito: A1 da PJ + `digitorus/pdfsign`, validação local com `esig/dss` e raiz do ITI, OCSP/CRL sempre.
- *Mídia sob λ_gpu:* LTX-Video 2B (licença comercial só acima de US$10 M de receita) e FLUX.2 [klein] 4B (Apache-2.0) são classe 5; o LTX é a única carga que exige Profile T (2 clipes/dia, 90 s, uma preempção). Wan 2.2 (24 GB documentados) fora.

**Números.** ~60% das páginas sem OCR; ~12% em VLM; OCR delta 600 GPU-s/dia; Kokoro 5.143 núcleo-s/dia; mídia 110 GPU-s/dia; ILF ≥ 60 e Δ ≥ 25.

**Origem.** C07; E04 (MinerU, Chandra-2, LTX); E02; CANON.

---

## III.7 Plataforma de engenharia

**Decisão fechada.** Monorepo Go (`module wj`, Go 1.27) com `go.work` só para `lib/lar-go`; Task v3.51.1; dado como Parquet imutável endereçado por sha256, com manifesto Ed25519 no mesmo log Merkle dos recibos; DAG de ~150 linhas sobre River OSS; registry em Postgres onde `bench_result` só referencia `quantized_artifact`; Victoria + OTel GenAI; CI no notebook; WAL-G; cgroup; 0 GPU. Não há ciclo noturno: os nós do DAG são jobs das classes do escalonador (III.8).

**Mecanismo.**
- *Layout e moedas de versão.* `cmd/{wj-api, wj-agent (3 processos D/C/T), wj-verify, gpu-scheduler, mlops-orchestrator, wjbench-score, wj-depcheck, wjmcp, wjgen, wjunits}`, os pacotes do III.1, `policies/*.cedar`, `python/` (uv: `distill`, `wjbench` com Inspect AI), `data/` fora do git. Código = `git rev-parse --short=12` (a mesma moeda de `policy_set_version`); artefato = sha256; snapshot = `snapshot_id` + `cutoff_ts`; SemVer só no `lar-go`.
- *Dado.* `corpus_snapshot(snapshot_id, cutoff_ts, parquet_sha256 UNIQUE, row_count, merkle_root, merkle_leaf_idx, signed_by_kid, sig)`; arquivo nomeado pelo hash; coluna `synthetic` obrigatória, filtrada pelo gerador de bench. DVC, lakeFS, Delta e Iceberg rejeitados: resolvem branching multi-escritor que não existe.
- *DAG.* `pipeline_run` + `pipeline_step(depends_on text[])` + um `StepDoneWorker` que enfileira os pendentes cujo `depends_on <@` concluídos: corte do manifesto → embeddings (classe 4) ∥ units (classe 2) → índice → treino (classe 3) → quantização → bench-smoke (150 itens no quantizado) → bench completo → promoção → publicação + IndexNow por `pg_notify`. River Pro (privado, pago), Airflow, Dagster, Prefect, Argo e Temporal rejeitados.
- *Registry.* `training_run` → `artifact` (+ `artifact_parent` N:1) → `quantized_artifact` (`nvfp4|exl3|awq_int4|fp8`, `template_sha256`) → `bench_result` → `promotion_gate` (`GENERATED ALWAYS AS ('G1')` na FK) → `promotion_state` (`policy_set_version` na FK). `license_spdx` com CHECK torna inexprimíveis Bespoke-MiniCheck, MiniCheck-FT5, gemma-3 e MinerU-2509. `EvaluatePromotion` só aceita `quantized_artifact_id`: G1 (UB95 de HCR ≤ 2%, ASR = 0), G2 (nenhuma trilha abaixo de −3 pp), G3 composto, G4 (canário e contaminação), G5 (piso 0,90 no WJ-Retro). Canário ≥ 48 h e ≥ 500 pagas; rollback por alias do llama-swap em < 10 s; `wj-api` recusa template com hash divergente (Jinja2 de artefato baixado é proibido).
- *Experimento e observabilidade.* MLflow 3.16.0 com backend Postgres: seed + git sha + snapshot + `uv_lock_sha256` reconstroem qualquer run. OTLP → VictoriaMetrics/Logs/Traces (`gen_ai.*` + `wj.urn`, `wj.nli_score`, `wj.vigencia_ok`, duplicados em Logs porque o Traces é WIP) + Grafana + vmalert. SLOs: TTFT p95 < 500 ms; 304 ≥ 85%; HCR ≤ 2% em runtime; corte diário no SLA; treino sem checkpoint por > 2 h ⇒ página.
- *CI no notebook* (git bare + Task): build, vet, golangci-lint, `go test -race`, `wj-depcheck`, validação Cedar com bump obrigatório, scorers contra golden files, suíte adversarial SQL, TLC (< 10 s), paridade do `leaves`; deploy por `cloudflare/tableflip`.
- *Backup e DR.* WAL-G v3.0.9 (`archive_timeout=60`, RPO ≤ 60 s); espelho ZFS no 2º NVMe; restic v0.19.1 off-site com `--limit-upload`; drill mensal automatizado; `K_root` em Shamir 3-de-5, air-gapped; NUT antes de a bateria acabar.
- *Isolamento.* `wj-platform.slice` (`MemoryHigh=8G`, `MemoryMax=10G`, `CPUWeight=20`): o kernel garante que métrica não toca a RAM do serving.

**Números.** Task v3.51.1; ~150 linhas de DAG; G1–G5 no quantizado; canário 48 h/500 pagas; rollback < 10 s; plataforma 4,3–6,3 GB (teto 10 GB); 0 GPU; RPO ≤ 60 s.

**Origem.** C05; D10/E07; E08 (git bare, `license_spdx`); CANON.

---

## III.8 Orçamento 24/7 e escalonador

**Decisão fechada.** Orça-se a integral diária de um recurso ligado 24/7 — 86.400 GPU-s e 691.200 núcleo-s —, sujeita a uma restrição de pico. Serving pago e lote são co-residentes; o lote **freia**, não desliga; a preempção é sinal latchado; `vllm.Sleep` só troca modelo. Transborda-se quando λ_gpu supera o mercado **e** ρ_job cabe no link.

**Mecanismo.**

*Demanda em regime* (P = 11.600 chamadas pagas/dia, U = 2.000 units/dia):

| Consumidor | GPU-s/dia | núcleo-s/dia |
|---|---:|---:|
| Serving pago generativo (cache semântico de 35%) | 15.579 | 5.720 |
| Geração de answer units | 11.013 | — |
| Auto-jogo do world model (ação estruturada ≤ 80 tok/turno) | 6.679 | 341 |
| Manutenção de treino + LoRA cirúrgico | 3.686 | — |
| Bench · OCR delta · mídia · embeddings | 771 · 600 · 110 · 100 | 3.150 (OCR) |
| Host vLLM · plataforma · ingestão · jurimetria · Postgres | 0 | 86.400 · 43.200 · 28.800 · 24.686 · 14.400 |
| Edge/C03 · Kokoro · NLI 54M · NER delta · grafo/Merkle | 0 | 10.000 · 5.143 · 3.264 · 2.250 · 90 |
| **Total** | **38.539 (44,6%)** | **224.203 (32,4%)** |
| **Folga** | **47.861 (55,4%) = 1,66 noites-eq./dia** | **466.997 = 5,41 núcleos permanentes** |

*Escalonador contínuo.* Classes: 0 tesouraria (nunca GPU); 1 pago (vLLM `priority=0`, nunca preemptado); 2 answer unit (mesmo engine, `priority=100`, preempção em um step de 50–100 ms sem perder o KV do pago); 3 treino/RLVR/auto-jogo e 4 OCR/embeddings (partição MPS com `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT=2800M`; o freio leva `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` de 20% para 5% em um micro-step de 60–400 ms); 5 mídia (Profile T, veto Cedar). `latch.go` guarda nível + geração monotônica: `Arm()` vem de `LISTEN/NOTIFY wj_pedido_pago` e `ClearIfUnchanged(seen)` só desarma se nada chegou durante a drenagem — a tradução de `SF_vars(Preempta)`; lease com `expires_at` substitui o `pg_advisory_lock`. `EntraProfileT` exige latch desarmado ∧ fila e voo vazios ∧ histerese de 120 s ∧ Cedar P20, com o fast path Qwen3-1.7B acordado para o M2M de 3 s. `--max-num-queued-reqs` devolve 503 acima do teto: é vivacidade, não capacidade. `EscalonadorContinuo.tla`: 1.936 estados, 3 invariantes + 4 propriedades temporais, 0 erros, depois de corrigir três defeitos de vivacidade achados pelo TLC. MPS na GeForce se verifica no metal no dia 1; plano B é time-slicing + latch em software (perde-se a partição de SM, não a preempção).

*VRAM (16,00 GB):* fast path 1.7B 0,95 · Qwen3-8B NVFP4 4,60 · reranker 0,70 · 2 LoRAs 0,16 · contexto CUDA 1,10 · **KV 5,00** · partição de lote 2,80 · folga 0,69; o wj-nli-54M residente cabe nos auxiliares e a cópia ONNX roda o lote em CPU. KV FP8 = 73.728 B/token; SWA 5:1 com W = 4.096 rende 1,71× em 8k ⇒ **124.830 tokens = c = 15,2 sessões de 8k** (TTFT 423 ms) ou um bloco CAG de 377.924 tokens. **Prefix caching é condição de existência**: sem ele o teto pelo SLO cai de 11.615 para 3.768 chamadas/dia. Compressão de KV é proibida dentro de ⟨PROVA⟩: o span fica imediatamente antes do ponto de geração, dentro de W. Trie de URN por requisição (~50.000 chaves, < 1 ms).

*CPU e RAM.* Slices: serving (núcleos 0–2, `CPUWeight=10000`), dados (0–4, 5000), lote (5–7, 100, `Nice=15`, IO idle, `batch`), plataforma (6–7, 20, 10 GB), ingestão (5–7, 50); o pico do caminho de requisição pede 0,45 núcleo nos 3 pinados. BitNet-b1.58-2B-4T (bitnet.cpp) roda na folga como monitor, classificador de ramo e watchdog. RAM de 96 GB no dia 0: 60,60 GB residentes (shared_buffers 16, backup de sleep 15,95, LightGBM 9,0, plataforma 6,3, o resto abaixo de 3,2 cada) e 35,4 GB de page cache; em 32 GB o déficit seria de 28,6 GB e o backlog de 11,9 dias viraria ~3 meses.

***ρ_job*, o segundo portão de transbordo.** λ_gpu decide se vale comprar GPU de terceiro; `ρ_job = bytes / GPU-s comprado` decide se o link permite: transborda só se `ρ_job < 0,25 × uplink` (156.250 B/GPU-s a 5 Mbps). Treino 10.484 ✓ · auto-jogo 44.917 ✓ · units de legislação 58.204 ✓ · embeddings 60.606 ✓ · OCR 600.000 ✗ (1 TB = 18,5 dias de upload, e veto Cedar) ⇒ OCR fica local.

*Backlog de construção.* 8.108.394 GPU-s brutos; depois das seis alavancas — tier mais barato −4.365.444, cache −87.500, quantizar/destilar −198.998, edge e notebook (ganho em CPU), transbordo −2.885.832 por **R$241,29** — restam 570.620 GPU-s locais = **11,9 dias**.

*Curva de capacidade:* `1,343·P + 5,507·U + 28.800·T + 11.946 ≤ 86.400`, com P ≤ 11.615.

| P pagas/dia | U units/dia | T noites-eq. de treino/dia |
|---:|---:|---:|
| 11.600 | 2.000 | **1,66** |
| 11.600 | 5.000 | 1,09 |
| 11.600 | 0 | 2,04 |
| 0 | 2.000 | 2,20 |

Canal elástico: 4 GPUs spot 24/7 = R$28,90/dia ⇒ +12,0 noites-eq./dia. Folga de engine: roofline de 3.117 tok/s contra 409 medidos (7,6×), com teste de aceitação de 2× em 30 dias. Na construção (pago ≈ 0), a classe 2 recebe 65% do dia = 7.020 units/dia a 8 GPU-s — o cronograma do III.12.

**Números.** 86.400 GPU-s; demanda 38.539; folga 55,4%; CPU 32,4% com 5,41 núcleos livres; KV 5,00 GB = 124.830 tokens; RAM 60,60 GB; backlog 11,9 dias + R$241,29; λ_gpu de R$3,24/GPU-h contra R$0,301/h no spot (10,8×).

**Origem.** E02 (`orcamento.py`, `latch.go`, `escalonador.go`, `EscalonadorContinuo.tla`, `tlc-run.log`, `mps-particao.sh`, `wj-slices.conf`, `wj-serving.service`, `wj-training.service`); D10; CORRECOES §2/§3; CANON.

---

## III.9 Topologia, resiliência e escala

**Decisão fechada.** Três estágios físicos; uma regra de capacidade (o mesmo λ_gpu contra três referências de mercado); GPUs heterogêneas nunca em tensor-parallel; edge como compute na fronteira exata dos planos; federação de confiança, não de FLOPs.

**Mecanismo.**
- *Estágios.* Hoje: o servidor roda tudo; o notebook faz CI + BitNet 24/7 redundante (CPU diferente é isolamento real); o edge faz Tunnel, CDN, R2 e Tiered Cache. Aos 6 meses: 3090 dedicada a treino; notebook relocado com **4 funções** — CI, BitNet redundante, réplica quente do Postgres (streaming, `archive_timeout=60`) e 2ª testemunha do Merkle, fechando o ponto único de confiança — e 2º conector `cloudflared` do mesmo túnel; no edge, Worker de recibo, DO de rate-limit, D1 do catálogo e Vectorize. Aos 18 meses: 2ª 5060 Ti (TP=2 entre GPUs idênticas, 1,6–1,9× [est.]) e 3º nó federado.
- *2ª GPU: 1 serve, 1 treina.* vLLM na 5060 Ti (`CUDA_VISIBLE_DEVICES=0`), Unsloth na 3090 (`=1`), sem NCCL entre elas. TP heterogêneo rejeitado com número: 448 × 936 GB/s (2,09×) põe o all-reduce no ritmo do pior shard. Gatilhos: 3090 usada quando a utilização projetada de treino passar de **48%** (`0,445 + 4.000/(3 × 8.760 × u) = 0,762` ⇒ u ≈ 0,480); 2ª 5060 Ti acima de **22.000 chamadas pagas/dia**. Par TP caído ⇒ o llama-swap sobe o tier 4B na GPU sobrevivente.
- *Edge como compute — a fronteira.* Migra: verificação de recibo (Ed25519 em Worker), roteamento, rate-limit por reputação MeritRank (DO; tokens repõem a `0,5 + 2 × rep` por segundo, teto 50), busca-lite (Vectorize) e o motor C03 em TinyGo/Wasm, mesmo fonte da origem. Nunca migra: Plano-T, NEGOCIAR e verificação fresca (o NLI não cabe em 128 MB e 10 ms). DO é o único lock-in real ⇒ todo estado nele é derivado e reconstruível do Postgres.
- *Tunnel e link.* `cloudflared` é outbound-only: IP dinâmico e CGNAT são irrelevantes por construção; dois conectores dão failover sem re-apontar DNS; localização nunca publicada; relé em VPS para os endpoints pagos com `stale-if-error`. Upload necessário: 170–340 MB/dia = 9,1 min/dia a 5 Mbps (0,63% do link).
- *Física.* Nobreak: `t = V·Ah·N·η/P·60` ⇒ 1500 VA com uma bateria de 7 Ah a 250 W = 17,1 min; 2 × 9 Ah = 44,1 min; o hook do NUT (3 min em bateria ou 50%) faz `CHECKPOINT`, para vLLM e agente, sela o Merkle, empurra para o notebook e desliga. Térmica: `nvidia-smi -pl 160` permanente. NVMe: `nvme smart-log` no VictoriaMetrics. RPO ≤ 60 s (a cadência do MMD); RTO em camadas — conteúdo 0 (R2), verificação e cálculo 30–60 s (failover de túnel), GPU por burst ou manual; `pg_promote()` da réplica só por decisão do Rafael após > 1 h.
- *Transbordo por λ_gpu, preços reais* (PTAX R$5,1490): lote preemptível transborda se λ[R$/h] > spot da Vast.ai (5060 Ti R$0,301/h; 3090 R$0,556–0,762/h); job SLA-crítico só se λ > RunPod Serverless (R$3,553/h, por segundo), nunca em spot no meio de chamada paga. Com λ = R$3,24/GPU-h, o lote transborda desde o dia 1 sempre que ρ_job permitir. Veto Cedar na borda para dado processual não anonimizado, Plano-T e NEGOCIAR.
- *Federação de testemunhas via Nostr.* Petals e exo rejeitados (8 saltos × RTT doméstico estouram TTFT < 500 ms; ativações intermediárias expostas). O parceiro roda o mesmo verificador BitNet em CPU, publica atestação assinada, recebe por citação verificada corretamente e vira co-testemunha do Merkle (gossip no estilo Certificate Transparency).

**Números.** 3 estágios; 4 funções do notebook; gatilhos de 48% e 22.000/dia; upload 0,63% do link; nobreak 17,1/44,1 min; RPO 60 s; spot R$0,301/h; RunPod R$3,553/h; λ R$3,24/h.

**Origem.** D07; E02 (ρ_job); CANON (GPU 2).

---

## III.10 Console do engenheiro-chefe

**Decisão fechada.** O console é instrumento de comando, não dashboard: todo número carrega uma ação a zero ou um clique. Três modos com telas diferentes; nenhum limiar novo; nenhum default de segurança inventado; a fala do Rafael é dado não confiável até virar `IntentCandidate` tipado; o humano assina na mesma hierarquia de chaves e no mesmo log Merkle dos agentes. O protótipo existe: `research/D08-console/index.html` (76 KB, 1.040 linhas, zero dependência, validado em DOM stub).

**Mecanismo.**
- *Três modos.* HOJE (5 min): uma frase de status (o pior semáforo), cards de KPI e fila resumida com folga até o SLA mais próximo, sem rolagem em 1366 × 768. SEMANA (30 min): sparklines de 8 semanas com a banda esperada, o que mudou, o que decidir, rampa por motor, `gap_queue`, financeiro. INCIDENTE: SEV1–SEV4 no padrão PagerDuty comprimido para uma pessoa — frase de impacto real, o que o sistema já fez, 3–4 botões que são chamadas de função, nunca "investigar".
- *Tela única orientada a dados.* Cada card sai de `{id, label, value, prev, lo, hi, direction, source, refLine, driftAlarm, sloRed, why}`: valor, Δ% colorido pela direção da métrica, barra do intervalo esperado (ontem ○, hoje ●), linha de referência. Ajuste deste blueprint: o array `KPIS` ganha "crawls de IA/dia" e "humanos/dia ÷ H0" (canais 2 e 3), e "atraso do pipeline noturno" vira "atraso do corte diário do manifesto" — não há noite. Semáforo: verde = dentro do conformal C(x) com SLO íntegro; amarelo = fora de C(x); vermelho = SLO violado ∨ Ville S_t ≥ 100 ∨ ADWIN/Page-Hinkley.
- *Fila de decisão: 4 categorias, SLA e default herdados.* B04 — gasto pontual (180 s = vida do macaroon; expira sem gastar), anomalia de gasto (15 min; mantém a contenção), lote em quarentena (24 h; fica pendente). A06/C05 — promoção fora do ramo estrito (24 h; permanece em canário). B02 — capex acima de R$5.000 (72 h úteis; não compra). B05 — redação de política (5 dias úteis; mantém a mais restritiva). Cada card: 3–5 fatos e o custo de errar nos dois sentidos lado a lado; N itens com portões determinísticos conjuntivos viram 1 decisão.
- *Linguagem natural tipada.* `IntentCandidate{intent, actor, raw_text_sha256, parsed_by{model, artifact_sha256}, params, confidence_pm, validation{checked_against}, confirmation{method}, effect{diff}, log{merkle_leaf_idx}}`; `ValidateIntent`: confiança < 600‰ ⇒ pergunta; leitura executa; efeito reversível pede clique; destrutivo pede confirmação **digitada**. É outra porta para a mesma fila, nunca atalho por fora dela.
- ***v_explain*.** `CREATE VIEW v_explain` (já em `research/E07-arquitetura/schema.sql`) junta, por `request_id`, `policy_decision_log`, `quantized_artifact`, `bench_result`, `promotion_state`, `bandit_decision` e `corpus_snapshot`: qual política, qual portão, qual braço e qual corte de dado. O drawer "Por quê" é uma linha dela.
- ***K_int/wj-human*.** Ramo da hierarquia de chaves do B06 com `kid` próprio (thumbprint RFC 8037): toda aprovação, comando e pânico do Rafael é folha do mesmo log Merkle das ações autônomas.
- *Modo pânico.* Expõe os kill-switches K1–K3 do B01 e a revogação de `budget_epoch` do B04 — nenhum mecanismo novo. Escopos: tudo (conteúdo estático nunca para), só gasto, só negociação, só geração. "PARAR" digitado. Retomada: causa raiz em uma frase → checklist automático (bundle Cedar, Merkle sem fork, CUSUM < 3σ, nenhum `SpendIntent` órfão) → nova `budget_epoch`.
- *Relatório diário* por Telegram às 07:15: ≤ 700 caracteres; top-5 métricas por surpresa (`|realizado − esperado| / (largura(C)/2) × w_k`) + todos os eventos discretos; botões `callback_data`; recibo Ed25519 próprio.
- *Ergonomia (curva corrigida pelo E08):* Fase 0 com 4 h/semana (pico 6); Fase 1 com 10 h (pico 12 após sequenciamento); Fase 2 com 6 h; Fase 3 com 2 h → **1 h 30 no dia ~180**, quando G-H promove L3. O D08 media só operação; faltavam ~100 h de julgamento jurídico indelegável.

**Números.** 3 modos; KPIs + 2 canais; 4 categorias; SLAs de 180 s a 5 dias úteis; 3 níveis de fricção; 4 escopos de pânico; relatório ≤ 700 caracteres; 245 h/ano.

**Origem.** D08; E08 §4.4; E07 (`v_explain`, `console ↛ econ/tesouraria`); CORRECOES §5.

---

## III.11 Invariantes e verificação formal

**Decisão fechada.** Ordem de força: tipo > constraint > prova > property-based > monitor; um invariante só desce de nível com justificativa escrita. Dos 24 invariantes, 19 ficam em tipo, constraint ou prova. Modela-se o protocolo em TLA+, não o código (Gobra e Goose rejeitados; Goose foi arquivado em 07/04/2026). O pacote executável está em `research/D10-code/`; os invariantes novos, em `research/E07-arquitetura/schema.sql`.

**Mecanismo.**
- *Os 24 por mecanismo.* Constraint: I-PUB-1 (FK a recibo com NLI ≥ τ e fonte ∈ 6 nós oficiais), I-PUB-2 (FK composta recibo ↔ span), I-PUB-3 (FK composta decisão Allow ↔ conteúdo), I-PUB-4 (taint = 0), I-MEM-1, I-LEDGER-1..4, I-BENCH-1..3, I-VIG-1, I-PREV-1. Tipo: I-TAINT-1..4, I-NUM-1 (+ monitor M3), I-NUM-2, I-ARQ-1. Prova: I-GPU-1..4 e I-PROM-1..5 (TLA+/TLC). Monitor: I-LOG-1 (consistência RFC 6962 a cada 60 s). O E07 acrescenta I-VERIFY-1 (`nli_milli >= tau_milli`, τ gravado na própria linha — sobe sem migração), I-VERIFY-2 (o recibo aponta a redação, não a norma), I-VERIFY-3 (`verdict = 'span_entails_claim'`), I-PROM-2, I-CAL-1 (`ub95 <= alpha`), I-CORPUS-1 (`elegivel_treino = false`), I-JUR-1/2, I-META-1/2 (Θ_frozen) e I-FIN-1 (replay de transação x402 recusado).
- *Os 6 tipos Go* (634 linhas, 0 dependências): `ValorMonetario` (`big.Rat`, sem construtor de float; `[0]func()` mata o `==`); `URNValidado`; `TextoNaoConfiavel`/`TextoVerificado` (não converte para `string`; `String`/`Format`/`MarshalJSON` redigem); `Prazo` (só `DataSeguraDeProtocolo()` e `Intervalo()`); `ReciboAssinado` (interface selada); `Autorizacao`/`CapacidadeDeGasto` (consumo único por CAS, teto monotônico). `erros/gerar.sh` mantém 13 programas que **não podem** compilar. 12 propriedades com `pgregory.net/rapid` v1.3.0 × 2.000 casos em 0,39 s, com mutação obrigatória: propriedade que nenhum mutante mata não entra.
- *Os 2 specs TLA+.* `tla/EscalonadorGPU.tla`: contraexemplo em **5 estados** (`ChegaPedido → ServeInicia → PegaLock → Dorme` ⇒ `perdidos = 1`) — o loop dormia antes de checar a fila e perdia requisição paga; corrigido com drenagem, lease com expiração e `SF` no lugar de `WF` (daí o sinal latchado); 72/96/120 estados, 0 erros. `tla/PromocaoModelo.tla`: TOCTOU de política (portões sob o bundle V0, promoção sob V1) e canário sem rollback fixado; corrigidos; 144 estados, 0 erros. O `EscalonadorContinuo.tla` do E02 completa o trio.
- *Os 4 furos do ledger, fechados:* lançamento com zero partidas commitava (gatilho também em `lancamento`); `TRUNCATE partida` não disparava gatilho de linha (`BEFORE TRUNCATE` + `REVOKE TRUNCATE`); `UPDATE` que preservava saldo reescrevia lançamento assinado (append-only); `prev_hash`/`hash` eram declarados pelo cliente (agora computados por `sela_lancamento`).
- *Portabilidade e imutabilidade:* `cardinality(datemultirange)` não existe em PG 16/17 ⇒ `chk_continuidade` portável com `count(*) FROM unnest(m)`, como `CONSTRAINT TRIGGER DEFERRABLE`: `EXCLUDE` dá ≤ 1, totalidade dá ≥ 1, logo exatamente 1. `sha256(convert_to(texto,'UTF8'))` em coluna GENERATED nunca rodou (`convert_to` é STABLE) ⇒ `sha256_utf8(text)` IMMUTABLE com encoding pinado.
- *FK composta como prova de pertinência:* `(policy_decision_id, content_sha256, allow_key)` com `allow_key GENERATED` = 'A' só em Allow — decisão de outro documento e publicação sob Deny ficam inexprimíveis, e o Deny continua auditável; `(receipt_id, span_sha256)`; `GENERATED ALWAYS AS ('G1')` na FK dos portões — não existe linha para apontar G2 no lugar de G1.
- *Monitores:* M1 CUSUM de gasto (5 min ⇒ pânico); M2 cobertura conformal (LB95 de Wilson, n ≥ 200 ⇒ perde `CapPublicar`); M3 ancoragem numérica (síncrono); M4 consistência Merkle (≤ 60 s ⇒ pânico). Fail-closed antes de logar; silêncio por 3 janelas é violação.
- *Teorema do sistema.* Contra adversário que controla todo byte lido da internet, se valem I-PUB, I-TAINT, I-LEDGER, I-NUM, I-VIG, I-GPU e I-PROM: (1) toda answer unit selada carrega, por afirmação normativa, recibo cujo `span_sha256` é hash de trecho literal de um dos seis nós oficiais, com NLI ≥ τ e índice Merkle anterior à publicação; (2) nenhuma autorização de gasto nasce de processo que recebeu byte do adversário, e no caminho legítimo o gasto da sessão é ≤ D_max = R$100; (3) toda resposta com data T cita exatamente a redação vigente em T. **Residual honesto:** relevância (afirmação verdadeira, porém enviesada — mitigada por `gap_queue`, Mondrian e E7, não provada); envenenamento de pré-treino (gera texto, não recibo); fonte oficial comprometida (fora do modelo; duas fontes e duplo egresso); bug de tipo em ~600 linhas fuzzáveis; garantia condicional ao selo.
- *Plano de 4 semanas* (~15 dias-pessoa): S1 ledger, totalidade de vigência, FKs compostas, suíte adversarial no CI; S2 pacote `tipos`; S3 propriedades com mutação, TLC no CI, FKs dos portões; S4 monitores ligados ao pânico e TLA+ da promoção.

**Números.** 24 invariantes (19 em tipo/constraint/prova) + 11 do E07; 20/20 ataques recusados (D10) e 28/28 (E07); 634 linhas de tipos; 13 rejeições do compilador; 24.000 casos em 0,39 s; TLC < 10 s no notebook, 0 GPU.

**Origem.** D10 (`invariantes.sql`, `ataques.sql`, `furos-b02.sql`, `tipos/`, `erros/`, `tla/`, `monitor/`); E07 (`schema.sql`, `ataques-resultado.txt`); E02.

---

## III.12 Crescimento

**Decisão fechada.** Crescer de 1.150 para 100.000 citações/dia é problema de **rendimento por página** e de **presença por motor**, não de contagem de páginas. Mantém-se o modelo do E03 — sete fatores, mistura sobre populações disjuntas de consulta — e troca-se só a âncora: C0 = 1.150/dia. Crawls e humanos entram como canais próprios. Toda curva abaixo é piso.

**Mecanismo.**

*1. Decomposição re-ancorada.* `C = Σ_motor Σ_consulta λ · P(indexado|m) · P(recuperado|q,m,rank) · P(cita|recuperado) · A(q)`. Fator necessário: 100.000/1.150 = **86,96×** (era 130,4×); média geométrica exigida por fator: 1,893×.

| Fator | Valor | Mecanismo | Mínimo que ainda fecha 100k |
|---|---:|---|---:|
| G_cob cobertura | 2,10× | 11.106 → 118.000 páginas, Zipf s = 0,70, cabeça-primeiro | 1,36× |
| G_rank⊕excl | 3,11× | mistura 0,75 × 2,00 + 0,25 × 6,40 (φ = 25% das consultas vão a páginas sem concorrente) | 2,01× |
| G_motor | 2,29× | presença ponderada 0,3934 → 0,90 | 1,48× |
| G_anc âncoras | 1,60× | dispositivo × redação como URL própria | 1,04× |
| G_ver verificador | 1,25× | `/api/v1/citar` exposto na página | 0,81× |
| G_fresh frescor | 1,50× | regeneração por evento normativo | 0,97× |
| G_query superfície | 3,00× | clusters de consulta por página, k 1,5 → 4,5 | 1,94× |

Produto = 134,4× ⇒ **regime-piso de 154.574 citações/dia, folga de 1,546× sobre a meta**. Multiplicar G_rank × G_excl daria 4,71× — o mesmo erro do "2,34×" que o D01 derrubou. G_rank = 1,30 (GEO do lado da geração, dentro do "up to 40%") × 1,54 (lado da recuperação: unit gerada da consulta do `gap_queue` tem cosseno ~0,90 com ela, contra ~0,65 de parágrafo narrativo). Com a âncora certa, o fator maior e menos verificado, G_query, só precisa entregar 1,94×; G_ver e G_fresh viram margem.

*2. Engenharia reversa do que já funciona.* A camada de protocolo é de classe mundial e está inteira no ar (III.1); a de conteúdo está em zero: a answer unit medida (1.062 palavras) não tem TL;DR (a resposta surge na ~250ª palavra), não tem **nenhum** número, nem âncora por dispositivo. As ≥ 1.150/dia são rendimento puro do protocolo (0,1035 citação/página/dia), e G_rank, G_anc e G_query são ganho inteiro. Os crawlers têm fome: GPTBot 27.685 leituras/semana; o PerplexityBot varreu as 11.106 páginas em 9,3 dias e caiu 66× por falta de conteúdo novo — a absorção é 4,5× maior que a geração. O polo longo é o Googlebot: 10,9 páginas/dia.

*3. Defeitos da semana 1 (medidos) e correção.* IndexNow 404 → chave + submissão no publish (Sessão 5); HTML sem `ETag` → `ETag` por sha256 (Sessão 3); título divergente entre `/api/v1/citar` e a página → fonte única no front-matter (Sessão 3); diretório de Web Bot Auth 404 → JWK publicado (Sessão 3); nenhuma rota devolve 402 → handler x402 (Sessão 11); Googlebot a 10,9 páginas/dia → `lastmod` verdadeiro, `ETag` e autoridade vinda das citações; Claude com 0 leituras de crawler → chega por MCP connector e web_search, então a alavanca é o `/mcp` com 19 tools e `Allow` a `Claude-SearchBot`/`Claude-User`. AhrefsBot + SemrushBot (4× a carga de todas as IAs) → rate-limit por classe no edge e `.md` de 9,5 KB, nunca na origem.

*4. Cronograma 24/7.* Dias 3–14: 10.000 páginas determinísticas do C03 (0 GPU). Retrofit das 11.106 existentes (TL;DR ≤ 50 palavras, ≥ 1 número a cada ~100, âncoras por dispositivo) com efeito a partir do dia 15. Dias 24–38: 96.894 units LLM a **7.020/dia** (65% de 86.400 GPU-s a 8 GPU-s/unit), todas sob o `wj/verify` fail-closed com o τ provisório do lote 1 de rótulos ⇒ **118.000 páginas publicadas no dia 38**, por 9,0 GPU-dias (R$697,64 de custo de oportunidade; R$46,53 de energia). Com o c_U de 5,507 do E02 seriam 10.198 units/dia. Em regime, as 2.000 units/dia vão para FAQ do `gap_queue`, regeneração por evento e expansão de N se G-B confirmar ŝ ≤ 0,75 — nada disso creditado no piso.

*5. Curva por canal* (saída de `blueprint/codigo/crescimento_reancorado.py`; crawls K0 = 6.086/dia; humanos em múltiplos de H0, α = 0,85, banda [0,70–0,95]):

| Mês | Dia | Citações/dia | × 1.150 | Crawls de IA/dia | × 6.086 | Humanos (× H0) | Marco |
|---|---:|---:|---:|---:|---:|---|---|
| 1 | 30 | 4.580 | 4,0× | 47.325 | 7,8× | 3,5× [3,1–3,8] | retrofit; IndexNow; Bing/OpenAI 100% |
| 2 | 61 | 31.052 | 27,0× | 80.544 | 13,2× | 23,0× [19,2–25,5] | 118.000 páginas no ar |
| 3 | 91 | 60.482 | 52,6× | 88.377 | 14,5× | 44,6× [37,1–49,7] | Anthropic e Meta ativos |
| 4 | 122 | 77.288 | 67,2× | 94.891 | 15,6× | 57,0× [47,4–63,5] | bandit convergido; exclusivos no ar |
| 5 | 152 | 94.057 | 81,8× | 101.634 | 16,7× | 69,4× [57,6–77,2] | G_query maduro |
| 6 | 182 | 105.455 | 91,7× | 107.093 | 17,6× | 77,8× [64,6–86,6] | **100k no dia 168**; Google ~25% |
| 7 | 213 | 116.315 | 101,1× | 111.883 | 18,4× | 85,8× [71,3–95,5] | Anthropic 100% |
| 8 | 243 | 128.143 | 111,4× | 116.976 | 19,2× | 94,6× [78,6–105,2] | |
| 9 | 274 | 141.259 | 122,8× | 122.606 | 20,1× | 104,2× [86,6–116,0] | Google ~65% |
| 10 | 304 | 154.552 | 134,4× | 128.362 | 21,1× | 114,0× [94,7–126,9] | |
| 11 | 335 | 168.469 | 146,5× | 133.685 | 22,0× | 124,3× [103,2–138,3] | Google ~95% |
| 12 | 365 | 171.749 | 149,3× | 133.747 | 22,0× | 126,7× [105,2–141,0] | regime (piso) |

Marcos: 2.000/dia no dia 18,5; 10.000 no 41,5; 50.000 no 80,9; **100.000 no dia 168,1**; 150.000 no 293,9; integral do ano 1 = 35,59 M citações e 36,72 M leituras de bot. Crawls = treino (3.955/dia do GPTBot × N/N0) + índice (descoberta + recrawl de 0,055 leitura/página/dia/motor × frescor) + fetch em tempo real (158,3/dia do ChatGPT-User × C/C0): 50.000/dia no dia 31, 100.000/dia no dia 145. Humanos: `H/H0 = α·C/C0 + (1 − α)·V(I_Google)/V(I_Google,0)`, com α = fração das visitas humanas vindas de resposta de IA; o Google orgânico entrega ≥ 13,9 cliques/dia num tráfego humano que o dono mede como substancial, logo α é alto; α é lido do Referer no dia 1 e o script re-roda.

*Validação.* Com C0 = 767, a reconstrução reproduz o E03 nos meses 3–12 com erro ≤ 4,2%, cruza 100k no dia 293,7 (E03: 294) e reproduz as duas sensibilidades publicadas do Google (mês 2 → dia 231,8 contra 231; mês 8 → 99.698/dia no d365 contra 99.413). O mês 1 fica 38% abaixo do E03 — o piso é conservador no início. A curva publicada do E03 × 1.150/767 cruza 100k no dia 162; o piso adotado é **o dia 168**.

*6. Probabilidade.* Monte Carlo estático (200.000 amostras log-triangulares ajustadas aos quantis do E03 — P05/P25/P50/P75 de 79,0/110,3/140,0/178,6 contra 78,9/111,0/140,6/177,8): **P(regime ≥ 100k/dia) = 91,3%**; ≥ 150k = 57,8%; ≥ 200k = 27,4%; regime P50 = 161.012/dia. Monte Carlo dinâmico (2.000 trajetórias: 7 fatores + inflexão do Google em 2/5/8 meses + taxa final de crawl do Google em 300/600/1.200 páginas/dia + Anthropic e Meta × 0,5/1/1,5): dia de 100k com **P10 94 · P50 148 · P90 277**; P(até o dia 150) = 51,6%; até 180 = 64,1%; **até 365 = 95,7%**.

*7. O Google deixou de ser o cronograma.* Inflexão do crawl no mês 2 → 100k no dia 134; mês 5 → 168; mês 8 → 218; mês 12 → 258,5; **Google congelado em 10,9 páginas/dia o ano todo → 100k no dia 265**. Na âncora de 767, cortar o Google impedia a meta; na âncora medida pelo dono, os 62% do mercado fora do Google fecham 100k sozinhos.

*8. Alavancas em ordem de retorno* (ganho isolado; dias-engenheiro; quando aparece): superfície de consulta 3,00× (10; 35 d) · retrofit de formato 2,30× (8; 15 d) · âncoras 1,60× (6; 40 d) · `/api/v1/citar` na página 1,25× (3; 30 d) · frescor 1,50× (7; 25 d) · Claude 1,14× (2; 21 d) · Meta 1,18× (3; 30 d) · geração em massa 2,10× (20; 45 d) · IndexNow 1,06× (1,5; 3 d) · autoridade no Google 1,79× (40; 150 d). As cinco primeiras: 20,7× por 34 dias-engenheiro (~5 sessões) = 23.805 citações/dia isoladas; o conjunto cabe em 12–19 sessões.

*9. Instrumentação por motor.* (a) O radar existente (bot identificado por faixa de IP do operador) ganha `page_type`, `formato_arm` e `fonte_geracao`; o braço do bandit vai no **caminho**, nunca em query param (`unit_arm(path, arm)`, between-subjects), o que também fecha a explosão de chave de cache. (b) Logpush → `bot_hit(bot_class ∈ {crawl_treino, indice_busca, fetch_tempo_real})`; `ChatGPT-User`, `Claude-User` e `Perplexity-User` contam ~1:1 como evento de citação. (c) Bing AI Performance, único painel oficial. (d) Sonda ativa: 500–1.000 consultas canônicas/dia por motor via API oficial, medindo φ, G_anc e G_ver — sozinha passa de 1.000 recompensas/dia e liga o bandit de formato na Fase 1. (e) Humanos: Web Analytics + Referer ⇒ H0 e α. Robots: `Allow` sempre em índice e fetch em tempo real; treino em `Allow` por 180 dias, reavaliado em G-E.

*10. GEO com evidência correta.* Princeton (arXiv:2311.09735, KDD 2024) mede "up to 40%" de **visibilidade** — limite superior, dependente de domínio; não há "+37/+40/+22" multiplicáveis de citação, e o 2,34× do C06 está morto. Wellows (22.749.707 citações): 79,6% das fontes em um só motor, 0,31% nos cinco ⇒ cobrir motor a motor (estudo de empresa de GEO, com partes "unaudited": sustenta cobertura, não receita). Formato como schema executável: TL;DR ≤ 50 palavras no topo do DOM; blocos citáveis de 40–120 palavras; ≥ 1 número a cada ~100; URN inline visível; atribuição nomeada. Braços F0–F5 por Discounted LinTS, recompensa `1,0·citation_verified + 0,6·crawl_paid + 0,5·mcp_call + 0,15·click`.

*11. Colheita: ORES jurídico, dividendo, `gap_queue`.* **ORES jurídico de custo zero:** `dano(edit) = 1 − [1(URN resolve)·1(NLI ≥ τ)·1(vigente)·1(bate com o determinístico)]` — a condição E1–E7 do verificador de produção, zero modelo novo; carência `72·e^(−3R)` h (R do MeritRank): 72 h para anônimo, 3,6 h no topo; conflito de interesse por SQL (OAB do editor × advogado do processo no DJEN); contribuição só em retrieval. **Dividendo de dados humano:** `contributor_pubkey` Ed25519 liga a edição verificada ao `payout(…, origem_tipo ∈ {ia_trajetoria, humano_edicao})`, pro-rata da receita M2M via x402; Sybil morre em `bond_rep = max(R$250, 49·R(i)·V_dia)`. **`gap_queue`:** toda chamada com erro E1–E7 ou `s_max < 0,78` e toda sonda sem citação grava `gap_queue(query_embedding vector(1024), query_text_hash, s_max, erro_verificador, origem, …)` — o produtor que faltava para `v_q = V_q^0,7 · G_q · e^(−λΔt) · (1 − C_q)^1,5`, com `G_q = σ(12·(0,78 − s_max))`; Stochastic Lazy Greedy (0,622·OPT); Flywheel Ratio vigiado pelo martingale de Ville. É a matéria-prima de G_query.

*12. Os 15 tipos de página exclusivos:* redação na data D com os acórdãos que a interpretaram; linha do tempo do dispositivo; diff de efeito jurídico; MP caducada com ultratividade; ADI com modulação; sucessão de autoridade; divergência entre turmas; importação de conceito entre ramos; aplicação heterogênea de súmula; doutrina ranqueada por autoridade; calendário processual; tabela de competência; custas e honorários das ~26 tabelas; sobrevida por tema/vara com banda conformal; calibração de êxito por tese.

*13. Expansão — caminho, não hipótese.* O ativo é o motor (tri-temporal + determinístico + grafo + recibo); o corpus é regenerável. Volume endereçável pt-BR construído de baixo: 4,37 M / 17,57 M / 58,72 M eventos de citação por dia (conservador/central/otimista) — 100k é 0,57% do central. Mesmo motor, novos corpora [est. E03]: Portugal + PALOP 0,05× o volume brasileiro (Diário da República com ELI nativo) · Espanha 0,14× · México 0,20× · Argentina 0,12× · Colômbia 0,15× · resto da América Latina 0,22× = +0,88×. Common law: o recorte temporal já é nativo nas fontes — `legislation.gov.uk/ukpga/2010/15/section/1/2012-10-01/data.xml` devolve a redação ponto-no-tempo (200, verificado em 22/09/2026 — o análogo exato do `?em=`) e o eCFR expõe `api/versioner/v1/versions/title-12.json` com datas de emenda e flag `substantive` (200, verificado em 22/09/2026). O adaptador troca `lex`, `calc` e a gramática PEG; `temporal`, `verify`, `receipt`, `grafo` e o escalonador não mudam. É o nó N62 da Fase 3.

**Números.** 86,96× necessários contra 134,4× decompostos; regime-piso 154.574/dia; 100k no dia 168 (P50 dinâmico 148; P(≤ 365) = 95,7%); 171.749/dia no d365; crawls 133.747/dia; humanos 126,7 × H0; 118.000 páginas no d38 por 9,0 GPU-dias.

**Origem.** E03; C06; D01 (termo de rank, GEO honesto); E04 B.12; CORRECOES §5; `blueprint/codigo/crescimento_reancorado.py`.

---

## III.13 Posicionamento

**Decisão fechada.** Formato agente-first deixou de ser fosso: réplica em semanas. O fosso é profundidade de stack que acumula com o tempo. Comparação com concorrente serve para achar espaço vazio, nunca para medir ambição.

**Mecanismo.**

*Capacidade, Brasil e global (condensado de 23 players + 2 entrantes):*

| Player | Superfície para agente | Verificação de citação | Vigência · grafo · predição com intervalo · M2M |
|---|---|---|---|
| Jusbrasil | B2B (280 M+ processos); `Disallow: /` para IA | não | não |
| Escavador · Juit | bloqueiam GPTBot, ClaudeBot, PerplexityBot | não | não |
| Turivius · Projuris · Digesto · Jusfy · Astrea · Looplex | sem MCP; jurimetria = volumetria | não | não |
| Jurisprudências.ai · JNexum | MCP; JNexum foi de 650 mil a 970 mil decisões e de 9 a 16 tribunais em 39 dias | aviso "sempre verifique" | não |
| Lexis+ AI · Westlaw | sem API self-serve | Shepard's/KeyCite editoriais; 17%/33% de alucinação; 64%/58% de acurácia | não |
| Harvey · CoCounsel · Legora · Robin · Luminance · Paxton · Clearbrief | integrações, sem MCP público | não publicada | não |
| vLex/Vincent · Midpage | vLex cobre o Brasil; Midpage tem MCP e 303.990 chamadas de agente/semana (EUA) | "3,67×" autodeclarado · citador com sinal | não |

- *Espaço vazio confirmado — 7 capacidades, 0 players:* recibo verificável por terceiro; tri-temporal com prova; preço M2M nativo por chamada; grafo com sucessão de autoridade; predição com garantia conformal Mondrian; benchmark público de alucinação; mercado de procedência entre IAs. No IETF surgiram dois perfis SCITT jurídicos (`draft-ailex-vap-legal-ai-provenance-03`, `draft-veridom-omp-legal-00`) com **zero** ocorrências de "in force", "urn:lex" ou "forecast": auditam o processo, ninguém audita a citação — o vão que os três drafts de `research/E01-drafts/` ocupam.
- *O denominador piorou — munição:* Stanford RegLab (arXiv:2603.03300) mediu Westlaw AI 58% e Lexis+ AI 64% contra 70% de RAG genérico; Charlotin: 2.042 casos de alucinação em 49 jurisdições, 41 no Brasil.
- *O comprador institucional:* o CNJ criou o PROSEG-IA em 27/05/2026, após validar (Manifestação Técnica CNIAJ 1/2026) o risco de injeção de comandos escondidos em documento processual — o problema que três planos + taint monotônico resolvem; produto: Atestado de Autos Limpos (N59). Demanda medida: Legal no Brasil = 3,92× o baseline global no Índice Econômico Anthropic; 1.507.210 advogados.
- *O fosso que acumula:* log Merkle não retrodata — quem copia hoje começa com histórico zero; reward calibrado contra citações disputadas só existe depois de rodar; MeritRank só vale distribuído no tempo; primeiro reconhecimento no PROSEG-IA. O incumbente não publica a própria taxa de alucinação: é valor esperado negativo para quem tem contrato AmLaw 100 e passivo de litígio.
- ***Radar de Concorrência*:** job River semanal com três fetches — `registry.modelcontextprotocol.io/v0/servers?search=<jurisprud|lexml|vigencia|precedent|jurimetria>`, `api.cdp.coinbase.com/platform/v2/x402/discovery/resources` (16.054 recursos em 2.035 hosts, zero dado jurídico brasileiro) e diff de `robots.txt`/`sitemap.xml` dos 23 players —, gravados com recibo no log Merkle e expostos em `/market/delta`. Já achou os dois entrantes MCP que o brief não listava.

**Números.** 23 + 2 players; 7 capacidades vazias; 0 recibos verificáveis no mercado; 58%/64% contra 70%; 2.042 casos (41 BR); 3,92×; JNexum +49% de decisões em 39 dias.

**Origem.** C08; E01 (perfis SCITT jurídicos); E04 (números conferidos; 49 jurisdições).

---

## III.14 Red team resolvido

**Decisão fechada.** As 10 correções obrigatórias do D01 estão fechadas, cada uma num artefato nomeado. O questionamento do D01 sobre o número de citações do dono está **refutado pelo dado primário do dono** (CORRECOES §1 e §5: ≥ 1.150 citações/dia, com 6.086 crawls/dia medidos como canal distinto) — encerrado.

**Mecanismo.**

| # | Achado do red team (D01) | Correção | Onde |
|---|---|---|---|
| 1 | "23k são crawl"; modelo linear sem termo de rank; GEO 2,34× | tese do D01 refutada pelo dado primário do dono; modelo com rank, 7 fatores e mistura; GEO = 1,30× dentro do "up to 40%" | CORRECOES §1/§5; E03; III.12 |
| 2 | Demanda e trabalho zerados no B02; três receitas divergindo 30× | V0 = 0 para produto sem comprador; catálogo de 5; dois trilhos (MCP + Pix, x402) desde o dia 61; esforço = 151 sessões + 245 h do Rafael | E08 §2/§5; CANON Economia |
| 3 | Verificador em 5 especificações com 3 τ, modelos sem licença ou só em inglês | `wj/verify` único; wj-nli-54M = mmBERT-small (MIT) podado 140M → 54M; τ = 0,906 conformal; E7 relevância; `verdict` fechado | E07 §6.1; CANON; E04 B.11 |
| 4 | VRAM não fecha; `/verify` no tier errado | mapa de 16,00 GB com KV de 5,00 GB e c = 15,2; Qwen3-8B NVFP4 residente; Gemma-4-26B-A4B sob demanda; `/verify` = 0,022 GPU-s, fora da conta generativa | E02 §4; E07 §3; CANON |
| 5 | Índice cobrindo 0,3–1% do corpus; disco de 1,5 TB | índice em 3 camadas; 1.085 GB (27,1%) por quatro decisões de esquema | E07 `retrieve`; E02 §6 |
| 6 | Noite de GPU sobrevendida 3–4× | 86.400 GPU-s/dia; demanda 38.539; folga 55,4%; backlog 11,9 dias + R$241,29 | E02 §1/§3; CORRECOES §2 |
| 7 | RAM de 32 GB; "20 núcleos em 8" | 96 GB no dia 0 (60,60 GB residentes); CPU por integral 32,4%; BitNet fica na folga | E02 §5/§6; CANON |
| 8 | Consolidação byte a byte impossível; `?em=` infinito | forma canônica, D0–D3, overlay ADI/MP, árbitro P3, meta ≥ 98% em D0∪D1; `?em=` → 301 na fronteira de versão, `tx` só de raízes publicadas | E08 N17/N03; E07 Worker |
| 9 | Pins e IDs errados | go-sdk v1.8.0; x402 `go/v2@v2.26.0`; AGE 1.8.0 (dist ASF); hugot v0.7.8; a2a-go v2.5.0; MinerU Pro-2605 (Apache); `chandra-ocr-2`; paridade do `leaves`; CI recusa `latest` | E04 §B; E07 `deps.yml` |
| 10 | Corte de v1; responsabilidade na pessoa física | 14 cortes com gatilho; PJ emite chave, recibo e ledger (`CHECK iss`); `K_int/wj-human` só para autoria | E08 §6; E07 D3; CANON |

*Ataques inéditos e defesas.* **A — explosão de chave de cache** (`?em=` infinito contra a origem doméstica): 301 para a fronteira de versão (o espaço colapsa para 10,4 M versões), `tx` só de raízes publicadas, rate-limit de miss por ASN. **B — lavagem de citação pelo `/verify`** (iterar afirmações até passar e exibir "verificado"): `verdict` = `span_entails_claim` por CHECK (nunca `correct`/`valid`), `at: unspecified` quando o cliente não passa data, preço crescente `p · 1,5^k` na k-ésima quase-duplicata (similaridade > 0,9) da mesma chave, termo de relevância no reward. **C — responsabilidade na pessoa física + DNS hijack no link residencial:** PJ como emissora, Tunnel-only, localização não publicada, duplo egresso com hashes batendo, `unbound` com DNSSEC, CA pinada por host, seguro E&O quando houver receita. Bônus: NER com F1 ≈ 0,9 não é anonimização (LGPD art. 12 §1º) ⇒ vende-se "máscara com taxa residual publicada", nunca "anonimizado".

*Corte do v1 e gatilho de retorno* (E08 §6, revisado pelo CANON):

| Cortado | Substituto no v1 | Gatilho de retorno |
|---|---|---|
| AGE como piso | AGE 1.8.0 como projeção; verdade em `aresta` + `WITH RECURSIVE` + CSR | consulta que `WITH RECURSIVE` não faça em < 100 ms |
| Painel de 6 personas | agente único + `wj/verify` + `compliance` com veto (o A01 mede degradação multi-agente) | agente único < 45% do baseline numa trilha |
| B07 inteiro | especificação mantida | ≥ 3 agentes externos pagando por 30 dias |
| SAOP, MiCRO, stake | posted price + bandit; `nego/core ↛ nego/llm` mantido | E[Π_nego] > 1,37 × E[Π_posted] |
| YubiKey + TPM (FROST 2-de-3 acima de R$2,50 **fica**, CANON) | macaroon 180 s + dead-man + teto de float | float diário > R$1.000 |
| Submissão do I-D SCITT, did:web + DNSSEC, Shamir em 3 ASes | 1 chave + log + verificador; drafts já escritos | Fase 3 (N54) ou 2ª organização emitindo recibo compatível |
| Mídia no caminho crítico | roda como classe 5 na folga (110 GPU-s/dia + Kokoro em CPU) | lift de citação medido ou comprador nomeado |
| Tier-2 32B → 8B, DVH, fusão | Tier-1: Qwen3-4B destilado do Qwen3-8B denso | Tier-1 no máximo de uma trilha e λ_gpu < energia |
| C04 causal (DML, DiD, DoWhy, IV) | sobrevivência + Mondrian | ≥ 500 mil processos com o marcador `sorteio` |
| Forgejo + Actions (Victoria e MLflow **ficam**, CANON) | git bare + Task no notebook | > 1 engenheiro humano ou > 3 experimentos concorrentes |
| Bandits LinTS + BwK, Whittle | prioridade `gap_queue` × impressões | ≥ 1.000 recompensas/dia — a sonda ativa dispara na Fase 1 |
| `/oracle/clausula`, `/reward`, `/verify/apolice` | catálogo de 5 | comprador nomeado pagando sinal |
| BitNet 24/7 | **revogado pelo CANON**: monitor, classificador de ramo e watchdog em CPU | — |
| X-LoRA | ≤ 3 LoRAs r=16 (S-LoRA + roteador discreto) | nenhum: refutado (+0,015 nats, p = 0,19) |

**Números.** 10/10 correções fechadas; 3 ataques + 1 bônus com defesa; 14 cortes (1 revogado, 3 estreitados, 1 refutado).

**Origem.** D01; E02; E04; E07; E08; CANON.

---

## III.15 Plano de execução

**Decisão fechada.** A unidade de esforço é a **sessão de Claude Code**: 1 sessão ≈ 1,1–1,7 engenheiro-semana, calibrado pelo que a própria frota entregou (C03, D10, D08, D04 — cada um uma sessão). O ano cabe em **~151 sessões** (0,41/dia) + 6 do adaptador de expansão (N62), ~64 GPU-dias e 245 h do Rafael. O verificador vem antes da geração em massa: com κ = 49, uma citação refutada cancela 49 verificadas. Nenhuma fase entrega fundação invisível. Metas de citação = trajetória central do modelo re-ancorado; portão duro = P10 do Monte Carlo dinâmico.

**Mecanismo.**
- *Classes de sessão:* A spec → código (1 sessão); B integração documentada (2–3); C luta com a realidade (6–20: consolidação, DataJud, LexML, calibração, OCR); D treino (2–4 + GPU-dias).
- *Caminho crítico de 18 nós (E08):* N01 instrumentação → N06 monorepo → N13 ingestão P0 → N16 parser P1 → N17 parser P2 + D0–D3 + P3 → N15 schema tri-temporal → N18 resolvedor + `/norma` → N19 BM25 → N20 denso → N22 NLI → N23 `wj/verify` → N24 calibração → N27 gerador de units → N35 catálogo → N33/N34 trilhos → N43 destilação → N44 RLVR → N51 autonomia L3. Re-ancoragem: N17 deixa de bloquear a geração — N27 gera sobre P1 com recibo de span e sem selo, e o selo (G-C) re-emite recibos D0∪D1 depois do dia 60. O sub-caminho até a geração em massa (N01 → N06 → N13 → N16 → N15 → N18 → N19 → N22 → N23 → N24 lote 1 → N27) tem 11 nós e ~25 sessões nos dias 15–24 (30 slots de sessão). Maior risco: N17 e N24.

*As 4 fases, com metas re-ancoradas em 1.150/dia:*

| Fase | Entregáveis | Citações/dia: meta · portão duro (P10) | Demais critérios de saída | Esforço | Rafael |
|---|---|---|---|---|---|
| 0 · dias 1–14 | N01–N12 + semana 2 | d14: 1.523 · 1.454 | 21.106 páginas; 5 defeitos de protocolo zerados; 19 tools no `/mcp` e Registry v1.3.0; 1 recibo por página; 304 ≥ 99%; ≥ 95% dos bots classificados; C0, K0, H0 e α registrados | 17 sessões, 0 GPU | 4 h/sem (pico 6) |
| 1 · dias 15–60 | N13–N32 + corpus | d45 (G-A): 14.756 · 11.599; d60: 30.256 · 22.908 | 118.000 páginas com recibo no d38; crawls ≥ 80.312/dia; `/norma` p95 ≤ 80 ms; UB95 ≤ 0,913% com n ≥ 1.000; HCR ≤ 2% no quantizado; 20/20 ataques recusados; 7/7 trilhas; `gap_queue` com 4/4 origens; bandit de formato ligado | 53 sessões, ~21 GPU-dias | 10 h/sem (pico 12) |
| 2 · dias 61–150 | N33–N50 | d150: 92.822 · 65.815 (P50 101.451) | receita ≥ R$1.199,26/mês; ≥ 3 pagantes (≥ 1 em x402); destilado não-inferior a 3 pp e HCR ≤ 2% no quantizado; ≤ US$0,001 por citação verificada; ≥ 10.800 units/GPU-dia; `skill_vs_baserate` em 100% do `/predict` | 45 sessões, ~40 GPU-dias | 6 h/sem |
| 3 · dias 151–365 | N51–N62 | 100k sustentados 30 dias (central no d168; P ≤ 365 = 95,7%); d365: 171.749 · 116.514 | receita ≥ R$5.745/mês; ≥ 5 contrapartes M2M; L3 de publicação; 0 violações de H1–H5; I-D publicado; 2 artigos; ≥ 10 agentes Ed25519; adaptador PT + common law no ar | 36 + 6 sessões, ~3 GPU-dias | 2 → 1,5 h/sem |

N51 inclui o painel selado com **cota auditável** na árvore Merkle: quantas vezes o sistema consultou o próprio benchmark privado é fato assinado, e "o sistema melhorou" vira afirmação verificável por terceiro; tesouraria com teto L3 permanente.

- *Rafael × agentes.* Julgamento jurídico indelegável, ~100 h nos dias 20–100: 1.000 claims de ouro (35 h em lotes de 250; o lote 1 nos dias 19–23 libera o τ provisório da geração do dia 24), adjudicação D3 (16 h, dias 30–58), juiz do A06 (15 h, dias 75–90), redação das políticas Cedar (8 h, dias 20–35; o número sobe por martingale, a redação é dele), revisão amostral (20 h), gabarito das trilhas (6 h). Decisão de dono, ~30 h/ano: tribunais, robots de treino, preço dos 5 produtos, capex (RAM, 2º NVMe, 3090), PJ, dividendo, 15 conversas comerciais, religar após contenção. 100% delegável: código, ingestão, indexação, CI, TLA+, treino, bench, triagem até a contenção, negativos programáticos, radar, texto do I-D, geração após o template aprovado, apuração fiscal. Total ≈ 245 h/ano ≈ 4,7 h/semana.

*Portões de decisão:*

| Portão | Dia | Limiar | Se falha — ação já escrita |
|---|---|---|---|
| G-A formato | 45 | ≥ 11.599 citações/dia (P10; central 14.756) | GPU de regeneração vai para a qualidade do `/verify`; prioridade para fetch em tempo real (`Claude-User`, `Perplexity-User`, `ChatGPT-User`) e tools MCP — a IA chama em vez de rastrear |
| **G-B** regime — o portão que troca a função objetivo | 45 (1ª leitura), 60 (decisão), contínuo | inclinação marginal ≥ 0,035 citação/página nova/dia na coorte cabeça-primeiro (≡ ŝ ≤ 0,75; central 0,063 em s = 0,70) | a submodular troca **cobertura de intento** por **profundidade de autoridade** (ligação interna, percursos por fundamento, proximidade de fonte oficial, backlinks via widget) — automático, sem reunião; se passa, as 2.000 units/dia de regime expandem N além de 118.000 |
| G-C selo | 60 | ≥ 98% dos dispositivos em D0∪D1 nas 200 leis | `/norma` segue sem selo em D3, com a taxa publicada; não bloqueia a Fase 2 |
| G-D verificador | 60 | UB95 ≤ 0,913% com n ≥ 1.000 | sobe τ, auditoria por Gemma-4-26B-A4B, 3.000 rótulos; **baixar τ é proibido** |
| G-E 1º pagador | 90 | ≥ 1 pagamento liquidado | receita pivota para o trilho BR; M2M segue financiado por ele |
| G-F economia de GPU | 120 | ≥ 10.800 units/GPU-dia (≤ 8 GPU-s/unit) e ≤ US$0,001/citação | aluga ~800 GPU-h ou compra a 3090, por λ_gpu contra o mercado |
| G-G break-even | 150 | ≥ R$1.199,26/mês | congela superfície nova; esforço na maior alavanca marginal do ledger |
| G-H autonomia | 180 | LB95 de Wilson ≥ 0,975 por 30 dias | fica em L2; investe em aprovação em lote |

- *Riscos com mitigação pré-combinada.* R1 consolidação (P ≈ 0,9, +3 semanas): forma canônica, time-box de 10 sessões/14 dias, 200 leis, P3 desde o dia 1 — e N17 já não bloqueia a geração. R2 harvest do DataJud (P ≈ 0,5): backfill fora do caminho crítico, mirror bulk no dia 1, PIT + `_shard_doc`. R3 calibração (P ≈ 0,7): lotes de 250 com τ provisório conservador, 10.000 negativos programáticos antes do primeiro rótulo, 2 estagiários para os 2.000 confirmatórios. R4 primeiro pagador M2M (P ≈ 0,6 de não existir em 6 meses): dois trilhos desde o dia 61, comprador BR medido (3,92×, PROSEG-IA). R5 licença (fato, P = 1): `license_spdx` com CHECK. R6 horas do Rafael nas semanas 3–8: sequenciamento derruba o pico de 16 para 12 h. R7 G_query abaixo do previsto: a âncora nova só exige 1,94×; se der 1,8×, N sobe de 118.000 para ~150.000 páginas (+4,6 dias de GPU).

*A PRIMEIRA SEMANA, hora a hora.* Pré-voo: RAM de 96 GB; 2º NVMe de 4 TB; token Cloudflare (`Analytics:Read`, `Logs:Edit`, `Zone:Edit`); Bing Webmaster; chaves de API dos 5 motores; Tunnel; `unbound` com DNSSEC; 2º egresso (VPS + WireGuard); `mps-particao.sh` no metal.
- **Segunda.** 08:00–08:30 **Rafael**: GraphQL `httpRequestsAdaptiveGroups` por `botClass` (30 dias) + Web Analytics e Referer ⇒ C0 por motor, K0 por classe, H0 e α no console — é a decomposição que vira denominador de G-A e G-B, não validação de número. 08:30–09:00: exporta o Bing AI Performance. 09:00–12:00 **Sessão 1 (N06)**: monorepo `wj` + Task v3.51.1; importa `C03-code` → `calc/`, `lar.go` → `lib/lar-go`, `D10-code/tipos` → `tipos/`, `schema.sql` + `ataques.sql` → migrations e CI, `deps.yml` + `depcheck.go` → `cmd/wj-depcheck`, `E02-code` → `cmd/gpu-scheduler` + `deploy/systemd`, `D08-console` → `console/`, e `B02-modelo-financeiro.py`, `E01-drafts/`, `checklist.md` e `crescimento_reancorado.py` → `tools/` e `docs/`; pronto = `task test` verde (testes do C03, 13 não-compilações do D10, 28 ataques recusados, depcheck limpo). 13:00–17:00 **Sessão 2 (N07)**: `cmd/wjmcp` em go-sdk v1.8.0 com as 4 tools do C03 atrás do `/mcp` existente (15 → 19, nenhum contrato atual muda), suíte de contrato 2025-11-25 e 2026-07-28. 17:00–18:00 **Rafael**: robots da classe de treino em `Allow` por 180 dias; índice e fetch em tempo real sempre `Allow`.
- **Terça.** 09:00–12:00 **Sessão 3 (N02 + defeitos)**: `ETag "wj-<sha256>"` no HTML, `immutable` onde a resposta é função pura, `Vary: Accept`, título único entre `/api/v1/citar` e a página, JWK em `/.well-known/http-message-signatures-directory`; pronto = 304 na 2ª requisição. 13:00–16:00 **Sessão 4 (N01)**: o radar ganha `bot_class`, `page_type`, `formato_arm`, `fonte_geracao`; Logpush → Postgres; série humana; pronto = ≥ 95% classificados com IP verificado. 16:00–18:00 **Sessão 5 (N04)**: IndexNow (hoje 404) + submissão no publish + sitemap com `lastmod` verdadeiro; pronto = 200 em 10 URLs, p95 ≤ 60 s.
- **Quarta.** 09:00–13:00 **Sessão 6 (N08)**: `cmd/wjgen` — calendário processual e tabela de competência: 3.000 páginas com TL;DR ≤ 50 palavras, 1 número a cada ~100, URN inline visível, intervalo nominal + estrito e trilha negativa. 14:00–17:00 **Sessão 7**: render → R2 → IndexNow em lote, sempre em path novo. 17:00–18:00 **Rafael**: revisão jurídica de 10 páginas amostradas; o sign-off dele libera o lote.
- **Quinta.** 09:00–12:00 **Sessão 8 (N09)**: recibo LAR Ed25519 sobre os bytes JCS + log Merkle com MMD de 60 s, em cima do `/api/v1/citar` que já devolve `repr_digest`; verificador WASM em `/verify/<id>`; a chave nasce sob `did:web:wikijuridica.com.br` e sua titularidade passa à PJ por rotação registrada no próprio log. 13:00–16:00 **Sessão 9 (N12)**: memória de cálculo reexecutável (`wj calc --replay <id>` devolve bytes idênticos) ⇒ +2.000 páginas. 16:00–18:00 **Sessão 10 (N05)**: `/feed/delta.jsonl` (D-1, shard imutável) + OpenAPI de 13 → 17 operações.
- **Sexta.** 09:00–12:00 **Sessão 11 (N10 + 402)**: Registry `br.com.wikijuridica/acervo-juridico` v1.2.0 → v1.3.0; handler x402 (`go/v2@v2.26.0` vendorizado + handler próprio de ~300 linhas de reserva) na 1ª rota paga — `/api/v1/lote` acima da cota gratuita devolve 402 com `accepts[]`, liquidação em rede de teste até a carteira da PJ existir. 13:00–15:00 **Sessão 12 (N11)**: console HOJE com dado real (citações por motor, crawls por classe, humanos ÷ H0, páginas, recibos, chamadas MCP). 15:00–17:00 **Sessão 13 (N03)**: canonicalizador `?em=` → 301 `?v=<início da redação vigente>`, `tx` só de raízes publicadas, fuzz com 10⁶ datas ⇒ ≤ 10,4 M chaves — antes de `/norma` existir. 17:00–18:00 **Rafael**: fecha a semana e grava o baseline decomposto.
- **Fim de semana.** A máquina segue publicando; **Rafael, 1 h no domingo**: protocolo da PJ (SLU/Ltda), emissora de chave, recibo e ledger — começa na semana 1 porque é lenta.

Semana 1: 13 sessões · ~6 h do Rafael · 5.000 páginas determinísticas novas · 19 tools no `/mcp` · 5 dos 7 defeitos medidos zerados (Google e Claude são alavancas de F1) · 3 canais instrumentados · 0 GPU.

**Números.** ~151 + 6 sessões; ~64 GPU-dias; 245 h; 62 componentes; 18 nós críticos; 8 portões; 14 cortes; 7 riscos; semana 1 com 13 sessões.

**Origem.** E08 (`E08-plano-execucao.md`, `E08-plano/checklist.md`); III.12 (metas); CANON ("já no ar", defeitos).

---

## III.16 Tabela-resumo da Parte III

| Seção | Decisão fechada | Número-chave | Artefato |
|---|---|---|---|
| III.1 Arquitetura | 9 camadas, 3 planos, 4 interfaces, enxerto sem parar o que cita | `/verify` 109,9 ms; crawler 8,0 ms | `research/E07-arquitetura/` |
| III.2 Fontes | DataJud como gatilho; PIT + `_shard_doc`; duplo egresso | delta ≈ 22 min/dia; corpus 1.085 GB | C01; E04 |
| III.3 Grafo | 5 ontologias + 4 classes; AGE como projeção; forward push | 301,4 M arestas; PPR 6,7 ms | C02; `schema.sql` |
| III.4 Direito-como-código | classe de token; intervalo nominal/estrito; trilha negativa | 4 tools, 50 ms, 0 GPU | `research/C03-code/` |
| III.5 Jurimetria | hazard discreto; IV de vara; `skill_vs_baserate`; Prediction Receipt | 1,4 ms/curva; k ≥ 50 | C04; `E01-drafts/` |
| III.6 Entrada/saída | escalada pelo verificador; licença por schema | ~12% das páginas em VLM | C07; E04 |
| III.7 Plataforma | monorepo; Parquet assinado; River DAG; registry no quantizado | 0 GPU; ≤ 10 GB de RAM | C05; D10 |
| III.8 Orçamento | 24/7 contínuo; lote freia; latch; ρ_job | folga 55,4%; backlog 11,9 d | `research/E02-code/` |
| III.9 Topologia | 1 GPU serve, 1 treina; edge na fronteira; Tunnel | gatilhos 48% e 22.000/dia | D07 |
| III.10 Console | comando, não dashboard; `v_explain`; `K_int/wj-human` | 1 h 30/semana no dia ~180 | `research/D08-console/` |
| III.11 Invariantes | tipo > constraint > prova; teorema com residual | 19/24 em a–c; 28/28 ataques | `research/D10-code/` |
| III.12 Crescimento | 7 fatores re-ancorados em 1.150; 3 canais | **100k no dia 168**; 171.749 no d365 | `blueprint/codigo/crescimento_reancorado.py` |
| III.13 Posicionamento | fosso = profundidade que acumula; Radar | 0 recibos verificáveis no mercado | C08; E01 |
| III.14 Red team | 10/10 correções fechadas; 23k do dono encerrado | 14 cortes com gatilho | D01 → E02/E04/E07/E08 |
| III.15 Plano | sessão como unidade; G-A..G-H; semana 1 hora a hora | ~157 sessões; 245 h; 64 GPU-dias | `research/E08-plano/checklist.md` |
