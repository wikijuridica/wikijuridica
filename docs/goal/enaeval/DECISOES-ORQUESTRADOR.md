# DECISÕES DO ORQUESTRADOR (Fable 5.1, engenheiro-chefe) — 22/09/2026
Palavra final sobre os conflitos que subiram das ondas F e G. Hierarquia: CORRECOES-DONO > estas decisões >
CANON-v4 > LEDGER > relatórios. O crítico (Onda 9) pode atacar estas decisões; se derrubar com evidência, eu reviso.

## D-1 Base de serving: Qwen3-8B denso PERMANECE; Qwen3.5 (4B/9B) vira Experimento E1 com portão
Evidência a favor do Qwen3.5 (G05, config.json lido ao vivo): KV/token 4,5× menor (16,0 KiB vs 72,0 KiB),
MTP nativo, 262k ctx, Apache-2.0, BFCL-V4 66,1 / TAU2 79,1 (4B empata com 9B em TAU2). É grande demais para
ignorar. Contra: (a) prefix caching — condição de viabilidade do CANON — não se aplica ao estado recorrente GDN
sem Tail-Replay (arXiv:2608.30310); (b) F11 provou que o pipeline LoRP/Minitron/EXL3/ModelOpt-NVFP4 foi
validado em denso, não em híbrido; (c) vocabulário 248.320 obriga refazer a cirurgia do D04.
DECISÃO: o EnaEval nasce em Qwen3-8B denso (pipeline provado). E1 = Qwen3.5-9B/4B entra como candidato de
promoção pelo registry (C05/G06) com três portões: (1) Tail-Replay ou equivalente mantendo TTFT p95 < 500 ms
com cache quente em vLLM ≥ 0.30 em sm_120; (2) QLoRA/FP8 e quantização W4A4 NVFP4 funcionando no híbrido
com KL de calibração jurídica ≤ a do 8B denso; (3) não-inferioridade G2 no WikiJurídica-Bench + G1 no artefato
quantizado. Se passar, substitui o residente e o KV liberado vai para concorrência. A proibição do CANON
"Qwen3.5-4B como base" fica restrita ao VERIFICADOR (encoder é mmBERT) e ao pipeline de poda até E1 fechar.

## D-2 Reprodutibilidade R2 sob prefix caching (F08 × G05 arXiv:2609.04748)
DECISÃO: (a) o caminho de VERIFICAÇÃO (V⁴, extração para claims, votação 3-run) roda com prefix caching
DESLIGADO por requisição (vLLM permite por request); custa < 3% do orçamento (F01: verificação é CPU/54M;
só a extração 8B é afetada). (b) Todo citation_receipt e prediction_receipt carrega `cache_state_digest`
(hash do estado de cache usado, ou "none"). (c) Serving comum mantém prefix caching. Sem isso, R2 é falso.

## D-3 KV em ⟨PROVA⟩: reescrever a regra
"Compressão de KV proibida em ⟨PROVA⟩" → "EVICTION de token proibida em ⟨PROVA⟩; quantização preservadora de
cobertura permitida sob certificado (WitCert, arXiv:2607.28699), com fingerprint no recibo". Ganho: 1,88×
tokens na mesma memória sem perder o suporte da cadeia (arXiv:2608.01631).

## D-4 Pós-treino: OPD → RLVR em duas etapas sequenciais
CANON dizia "on-policy distillation de manutenção". Passa a: etapa 1 = OPD (com IER, arXiv:2609.24432),
etapa 2 = RLVR GSPO-DrC com penalidade de vigência −0,60 (D05) elevada a INVARIANTE (arXiv:2608.14610: RL
geral piora raciocínio temporal — o portão G5/WJ-Retro é obrigatório entre as etapas). GrowMTP entra como
experimento. Scale-QLoRA (arXiv:2609.04526) é obrigatório para merge sobre NVFP4 (merge ingênuo perde até 39 pp).

## D-5 Catálogo de ferramentas: o GERADOR do G04 é canônico
Dois catálogos nasceram (G06 tools/catalog.json manual: 37 + 20 reservados; G04 cmd/enaeval-catalog gerado:
45 + 3 aliases com 4 invariantes fail-closed). Código vence prosa. DECISÃO: `cmd/enaeval-catalog` passa a
ingerir também os schemas REAIS de G01 (6 tools) e G02 (11 tools) e os nomes reservados do G06 que não
tenham spec; o catálogo único resultante vive em research-v4/tools/catalog.json (sobrescreve o do G06) e
o G06 fica como fonte dos nomes reservados. Regra permanente: tool sem schema autocontido + title não entra.

## D-6 `dialog` na camada 4 (agente), não na 5 (superfície) — regra de CI `wj/agent/dialog ⊬ wj/serve`
Aceito o G04: a pergunta de esclarecimento fixa o insumo do cálculo; se fosse gerada por LLM na superfície,
seria induzível por injeção. Elicitation por servidor está proibida na rev. 2026-07-28 (SEP-2322/2575);
o multi round-trip com `requestState` HMAC é o mecanismo.

## D-7 K_root é o objetivo nº 1 de qualquer fase de execução
Sem chave raiz (Shamir 3-de-5, B06) não há recibo real, cota por DID, 402 que liquide, Web Bot Auth, nem
crawler assinado (G03). Todo artefato hoje usa chave de EXEMPLO e está marcado. A tasklist começa por isso.

## D-8 Armazenamento: o plano do G03 (1.847 GiB = 49,6%) substitui os três números anteriores
Correção ao F04 §6 (cota pg duplicada) aceita. O 1 TB não é espelho: é arquivo do insubstituível (chaves,
Merkle, WAL, corpus canônico) + do morno que a poda remove. Ordem de poda: WARC de diário municipal → PDF
de tese acadêmica. λ_tbw ≈ 0 no regime atual (G05): tiering pode ser agressivo.

## D-9 λ_gpu por classe e por hora
arXiv:2608.23986 (G05): sob congestão, rotear ao 4B pode aumentar o gasto por citação verificada. O preço-
sombra deixa de ser escalar único: λ_gpu[classe][hora]. Fonte única continua `econ.LambdaGPU()` (E07),
agora com assinatura (classe, hora).

## D-10 Rede social e arena: números do G01/G02 entram no CANON
599 threads/dia (20,6% da folga), 120 rodadas de arena/dia (10,8%), prognóstico em 11.600 chamadas/dia (7,6%),
semente fria 36.571 GPU-s (1,64 dia), submercados de horizonte ≤ 24 h obrigatórios, promotor só onde a lei
prevê (tabela de decisão CPC 178 / LACP 5º §1º / LIA 17 / CF 129 I), juiz-IA nunca vê o p do caso.

## D-11 Sem dias, semanas ou meses em NENHUM documento v4
Toda referência temporal de execução é FASE/OBJETIVO com critério de pronto. Onde um cálculo precisa de
duração (backlog de GPU em dias de máquina), é medida física do sistema, não cronograma — escrever
"X GPU-dias de máquina", nunca "em X dias".

## D-12 Planalto: regra de normalização `wj-norm/f5-cspm-tail-v1` (F06) é canônica; NFC obrigatório (F08)

# ADENDO — ARBITRAGEM DOS 19 ACHADOS DO CRÍTICO (H01), 22/09/2026
Li o H01. Aceito 19/19 como graves. Veredito sobre as minhas decisões: D-5 e D-10 DERRUBADAS e reescritas;
D-2, D-6, D-11, D-12 AJUSTADAS conforme H01; D-1, D-3, D-4, D-7, D-8, D-9 MANTIDAS.

## D-5' Catálogo: o gerador do G04 passa a ler as specs REAIS de G01 e G02
Fontes do `cmd/enaeval-catalog`: C03 (tipos Go), F02, F03, F05, F07, **G01-code/schemas/mcp-g01.json**,
**G02-code/mcp-social-tools.json**; os nomes reservados do G06 sem spec entram como `reserved` (não como stub
inventado); `wj_arena_settle` e `wj_social_reputation` são REMOVIDOS. Resultado esperado: 53 ferramentas
com schema + 8 reservadas. O `research-v4/tools/catalog.json` manual do G06 é sobrescrito pela saída do gerador.

## D-10' Debate é UM produto com dois perfis de custo
Thread (G02) e rodada de arena (G01) são o mesmo objeto (`debate`) com perfil `leve` (18,29 GPU-s, lote ×4,
sem os 4 papéis assimétricos) ou `arena` (41,0 GPU-s; 46,9 com parecer do MP). Meta de regime:
599 debates/dia dos quais 120 em perfil arena ⇒ 479×18,29 + 120×41,0 = 13.681 GPU-s/dia (30,0% da folga).
Orçamento de regime consolidado (GPU-s/dia): F01 fluxo 10.622 + F03 922 + F02 580 + G01 prognóstico 3.480 +
debates 13.681 + F07 serviços 2.900 + G03 OCR 4.000 = 36.185 = 79,4% da folga de 45.600 ⇒ 9.415 GPU-s/dia
para treino em regime. O backlog de construção (3,05 M GPU-s) NÃO cabe em regime ⇒ existem DOIS PERFIS DO
ESCALONADOR: `construcao` (treino/indexação prioritários; semeadura a 25% = 150 debates/dia; OCR a 50%)
até o backlog fechar (≈ 35,7 GPU-dias de máquina — medida física), depois `regime`. A transição é objetivo
com critério de pronto (backlog = 0), não data. G03 fase B: 1,2 M núcleo-s/dia é ERRO de unidade (1,74× a CPU
inteira) — reescrever como total de fase espalhado pela folga de 5,05 núcleos. RAM nova (3.030 MiB) > margem
(2.818 MiB) ⇒ entra no envelope rotativo de 6.656 MiB (F04), não como residente.

## D-2' cache_state_digest e cache_salt
`citation_receipt` e `prediction_receipt` ganham `cache_state_digest TEXT NOT NULL DEFAULT 'none'`;
o caminho de verificação usa `cache_salt` por requisição (é o mecanismo real do vLLM) e registra o digest.
lar.go valida a presença do campo (v1.1 do recibo).

## D-6' e G04 stateless
HMAC do `requestState` com chave DERIVADA de K_op (HKDF, rotação junto com K_op), não por processo;
cota por DID em Postgres (tabela `quota_did`), não em memória. Só assim N réplicas do servidor são equivalentes.

## D-11' Varredura obrigatória de cronograma
Arquivos com violação (H01 §4): F04 §4.2 (tabela "Etapa | Dia" → "Etapa | GPU-dias de máquina acumulados"),
F11 roadmap por trimestre (→ por FASE de soberania S0–S4 com critério de pronto), CANON-v4 §4:185
(→ mesma reescrita), G02 "em 180 dias" (→ "ao atingir 126.594 páginas"), G04 "180 d" (→ "expiração = fase
de rotação de K_op"). Durações físicas (GPU-dias de máquina, TTFT, latência) permanecem.

## D-12' Nome da regra de normalização
`G03-code/canon/canon.go` usa `wj-norm/f5-cspm@1` → trocar por `wj-norm/f5-cspm-tail-v1`; regex do SCHEMA-v4
passa a aceitar SÓ o canônico.

## D-13 Verdade para a IA: cinco correções estruturais obrigatórias (H01 G4, G9, G11, G13, G14)
1. `F01-code/knowledge-claim.schema.json` recebe TODAS as extensões que o CANON §7 declara: forca927 += III_A_resp_relevancia,
   administrativa_vinculante; 15 estados de tese; mode condicional; oficial_tpu; assertion_es; perfil cp1;
   `origin` no envelope; ProcedureClaim.kind += prognostico; fonte.kind += {tcu_bulk, carf_solr, ckan, oai,
   eurlex, hudoc, ccidx, lexml, senado}. Um GERADOR ÚNICO de enums (`enums.yaml` → JSON Schema + SQL + Go)
   passa a ser a fonte; divergência quebra o CI.
2. `lar.go` (B06/F06) implementa a checagem estrutural (man_norm + locator + rejeição de redação tachada
   `<strike>/<s>/line-through` + cache_state_digest) — ~40 linhas — com vetores novos; C20 do F06 passa a
   apontar o novo SHA.
3. `resolution.oracle_receipt` vira NOT NULL com FK composta para `capture` (fonte datajud, nível ≥ C1);
   tabela `tpu_outcome`; payout só via Plano-T (FROST) e `≤ b`. Texto da internet NUNCA chega a dinheiro
   sem captura atestada.
4. G02: segmentos `text` de post NÃO saem assinados como `v4: pass` sem verificação; texto livre é `opinion`
   (não assinado como verificado) e só claims com recibo recebem `v4: pass`.
5. τ é COLUNA/CONFIG (fonte única `verify.Tau()`), nunca const/CHECK hardcoded — corrigir G01 (CHECK + const)
   e G02 (const + schema const). SCHEMA-v4: `tau_milli` na linha do recibo (E07 I-VERIFY-1) permanece.

## D-14 Tabelas duplicadas G01/G02 × SCHEMA-v4
`prediction`/`arena_round` (G01) e `prediction_receipt`/`market` (SCHEMA-v4) se fundem: `prediction_receipt`
ganha `processo_hash NULLABLE` (wj_predict_case não tem processo) + `celula`/`counter` UNIQUE mantidos;
`arena_round` referencia `market`. `social_post` ganha as colunas que tornam o Post do G02 exprimível
(claims[] minItems 1 via tabela `social_post_claim` NOT NULL-checked por trigger). SCHEMA-v4.1 resulta.

## D-15 Unidades, receita e identidades
"6,41 GiB" → "6,41 GB (5,97 GiB)" em todo lugar. Receita do 8B parte do artefato `nvidia/Qwen3-8B-NVFP4`
(hash no BOM) + cirurgia de vocabulário → 4,90 GB; o fallback BF16→NVFP4 local (5,23 GB) só se o artefato
sumir e obriga reduzir KV. Personas: exatamente 4 papéis (advogado, juiz, promotor, jurista) — o "advogado"
tem sub-papel autor/réu com a MESMA identidade; 4 pubkeys, não 5. Assinaturas placeholder recebem prefixo
`EXEMPLO-` e kid `example` para nunca parecerem reais.

## D-16 Toolchain
Monorepo `wj` com `go 1.25` no go.mod (go-sdk exige ≥ 1.25) e `toolchain go1.25.x` pinado; os módulos de
pesquisa mantêm seus go.mod até a migração (objetivo da tasklist).

## D-17 Ordem dos 12 objetivos: ACEITA a do H01 §7
K_root → enums/τ únicos → recibo v1.1 (lar.go) → SCHEMA-v4.1 → catálogo único (D-5') → MCP v0 em /mcp2 →
monorepo wj → 8B servido + verificador calibrado (perfil construção) → wj/serve → conteúdo vivo F01+G03 →
premeditação → rede social + arena unificadas. A tasklist obrigatória segue esta espinha.
