# CLAUDE.md — contrato do `/opt/wiki`

Aqui fica **o que é fato do projeto** e **o veredito de cada ordem**. O argumento, o caso e o
número ficam fora: procedimento é skill, armadilha por arquivo é `.claude/rules/`, proibição é
hook, invariante é gate. Este arquivo entra em **toda** sessão, e arquivo longo reduz aderência —
por isso ele é curto de propósito.

O que vale em qualquer repositório desta máquina está em `~/.claude/CLAUDE.md` e não se repete.
Precedência: `AGENTS.md` → `GOAL.md` → `CHECKPOINT.md` → `docs/`. **Vence a regra mais
restritiva**, e nenhum documento vence o código vivo nem o dado no disco.

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: inicio — replicado palavra por palavra; internal/contract/misc/regras_do_dono_test.go reprova cópia ausente ou divergente -->

## Regras do dono — bloco canônico (2026-09-15)

Sete vereditos adotados, um por linha, em vigor desde 2026-09-15. O argumento, o caso medido e
o prejuízo de cada um ficam em `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` §P0, nos blocos
*"Texto do item N"*, e em `docs/PRECEDENTES_DAS_ORDENS.md`; aqui fica só a ordem. Este bloco é
replicado palavra por palavra em `CLAUDE.md`, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`,
`docs/CONTRATO_DADO_REAL.md`, `docs/MEDICAO_DE_AUDIENCIA.md`, `docs/CRAWLERS_E_BOTS.md`,
`docs/CONTENT_QUALITY.md`, `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` e
`docs/DATA_SOURCES.md` — cópia divergente ou ausente reprova
`./tools/go-modern test -count=1 ./internal/contract/misc/`. Nenhuma linha daqui carrega número
de estado: o contrato diz onde medir, e quanto é se mede na hora.

**Regra 8 — nenhuma decisão volta para o dono (2026-09-15).** Decida e execute a decisão técnica, inclusive a ambígua, pela rota mais conservadora que ainda entrega e com a suposição escrita no commit; é vedado devolver decisão ao dono, desenhar revisão humana como etapa de esteira de conteúdo ou travar frente à espera de aprovação.

**Regra 9 — dado público vai até o fim da cadeia, e o DataJud está destravado (2026-09-15).** DataJud, API Pública do CNJ, DJEN, LexML, `normas.leg.br`, Planalto, diários oficiais e portais da transparência entram em página publicada com número, classe, órgão, relator, andamento e nome das partes, retirado o identificador (CPF, RG); a linha que fica é `nivelSigilo > 0`, ECA, Maria da Penha, adoção e o art. 5º, II da LGPD, e quem propuser trava, gate, allowlist ou regime de "só sinal interno" cita a norma e o dispositivo — sem dispositivo citado, a rota segue aberta.

**Regra 13 — a ética da OAB tem três regimes, e o deste portal é o do conteúdo informativo (2026-09-15, precisada em 2026-09-16).** Regime A, publicidade profissional — anúncio, oferta, perfil, captação —, é o que CED arts. 39, 40, 44, 45 e 46 e Provimento 205/2021 arts. 3º, 5º e 6º disciplinam, e esses gates ficam como estão; regime B, conteúdo informativo, é permitido com deveres de forma — CED art. 41 (não induzir a litigar), art. 42, I (não responder consulta de caso concreto em canal público), art. 42, IV e art. 43 (sem sensacionalismo), Provimento art. 4º e Anexo Único — e é o regime de página, verbete, comentário de acórdão e dataset deste portal; regime C, a exatidão técnica da informação jurídica, está fora da disciplina, então erro de conteúdo se trata como defeito de qualidade: conserta-se o produtor, mede-se antes e depois, e a página publica e refina. O canal de contato tem autorização expressa no Provimento art. 4º, §3º, que equipara ao e-mail os aplicativos de mensagens instantâneas; jurisprudência pública de terceiro fica, e resultado obtido pelo próprio autor em causa que patrocina sai, mesmo anonimizado (Provimento art. 4º, §2º). Quem invocar risco disciplinar contra conteúdo informativo cita o dispositivo, e o texto literal conferido em fonte primária está em `docs/goal/JURIDICO_BASE.md` §1.1; sem dispositivo citado, a rota segue aberta.

**Regra 15 — tráfego, alcance e retorno de bot medem-se na borda (2026-09-15).** Com `s-maxage=604800` na Cloudflare o `HIT` não toca o Go, então `data/ops/access/*.jsonl` é piso e só tem autoridade sobre o que existe apenas na origem (rota dinâmica, gêmea Markdown, `/api/v1`, MCP, descritores); volume se lê por `tools/cloudflare_auth.py` — `cf.zona_id("wikijuridica.com.br")` e `cf.graphql(...)` sobre `httpRequestsAdaptiveGroups` com dimensão `userAgent`, fatiando a janela em um dia por chamada no plano Free (`JANELA_MAXIMA_DIAS_FREE = 1`) —, toda afirmação de volume declara a camada medida, e série cumulativa como `edge_bot_agents_daily` se lê por último-por-dia, sem somar linhas.

**Regra 16 — não estreitar o projeto com número curto (2026-09-15).** Antes de escrever que uma frente é pequena, marginal, não escala ou não vale a pena, meça na fonte com autoridade sobre aquela grandeza; instrumento que declara a própria limitação é ordem de trocar de instrumento, e volume baixo confirmado entra com a camada declarada e com a hipótese do que o aumentaria, não como veredito de encerramento.

**Regra 18 — é proibido limitar este projeto (2026-09-15).** A plataforma cresce, é indexada e é citada, e o papel da engenharia é acelerar: todo teto nomeia a causa física externa e medida — `Crawl-Delay` publicado pelo operador remoto, tok/s do modelo, cota de requisições da API —, toda recusa de frente vem com a medição que a sustenta e com a hipótese do que a reverteria, e margem de prudência própria não é teto, é atraso.

**Regra 20 — bug anterior não trava trabalho, e não se contorna (2026-09-15).** Defeito encontrado no caminho se conserta no caminho, com agentes, na mesma sessão: "já estava quebrado antes" não é licença para parar, contorno vira a próxima peça quebrada, e medição que não caiu na rodada é passo de runbook — item que chegue ao fim da execução sem medição é falha de execução.

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: fim -->

---

## Antes de agir: o gatilho é o ATO, não o tema

Quem vai afirmar um volume não pensa "vou ler sobre medição". Por isso a tabela é por ato.

| Antes de… | Leia / use |
|---|---|
| rodar gate, check ou teste Go | skill **rodar-gate** — `cmd/check` sem argumento roda TODOS e já levou o load a 52 |
| publicar o acervo | skill **deploy-publico** — ela decide `--ressemear` e purga pelo que mudou |
| subir binário Go | skill **deploy-binario-go** — a ordem dos passos é o produto |
| purgar ou aquecer a borda | skill **purgar-e-aquecer-borda** |
| regenerar derivado de `data/editorial/` | skill **ordem-derivados-editoriais** — a fábrica já ficou 31 dias parada por ordem errada, e o erro diz `fingerprint mismatch`, nunca "ordem errada" |
| commitar Go, `go.mod` ou `go.sum` | skill **commit-go** |
| commitar página ou portfólio v2 | skill **commit-v2** |
| conferir se o portal está no ar | skill **verificar-producao-viva** — sondar `127.0.0.1` passa verde com o túnel caído |
| afirmar volume, alcance ou citação | **Regra 15** · `docs/MEDICAO_DE_AUDIENCIA.md` · `docs/CRAWLERS_E_BOTS.md` |
| dizer que uma frente é pequena ou não vale a pena | **Regra 16** |
| propor trava, gate ou recusa contra fonte pública | **Regra 9** · `docs/DATA_SOURCES.md` |
| invocar risco da OAB | **Regra 13** · `docs/goal/JURIDICO_BASE.md` (fonte primária, com URL e hash) |
| recusar conteúdo por similaridade, molde ou piso | `docs/CONTENT_QUALITY.md` — o produtor usa a régua do gate, ou a divergência é medida e escrita |
| **corrigir o produtor porque um gate reclamou** | `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` §18 — meça a ASSINATURA das ocorrências antes: concentração de 100% num padrão sintático é defeito do instrumento, não do conteúdo. Um gate já reprovou 1.425 vezes um artefato correto |
| **gravar página em `data/editorial/v2_pages/`** | `./tools/oraculo-de-admissibilidade --pagina <arquivo>` — ele roda os decisores REAIS num ensaio e devolve os `reasons` deles · mapa da cadeia em `docs/CADEIA_DE_ADMISSIBILIDADE_DA_PAGINA.md` |
| publicar número derivado de replicação | `docs/PRECEDENTES_DAS_ORDENS.md` — replicação que bate com o esperado é motivo para desconfiar; o binário é a autoridade |
| tocar um arquivo de dado | `.claude/rules/` carrega a armadilha sozinho · `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` |
| afirmar qualquer número | `docs/CONTRATO_DADO_REAL.md` (R1–R13) · gate `contrato-dado-real` |
| lançar agente, escolher modelo ou montar onda | `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` §3–§4 · roster em `.claude/agents/` · Haiku, e Sonnet em agente que edita, barrados por `.claude/hooks/block-agent-haiku.sh` |
| **abrir onda de agentes** (qualquer fan-out, de 2 agentes em diante) | **Protocolo do barramento**, na seção *Governança entre pares*: roster com `agentId`, arquivo de achados só com acréscimo, `SendMessage` direto ao par a cada achado, releitura antes de fechar. Permissão que falta é bug de ferramenta, e o chefe a corrige |
| instalar, atualizar ou abrir o editor (VSCodium) ou o terminal (kitty) | `docs/ops/IDE_VSCODIUM_20260923.md` · `.claude/rules/ide-e-editor.md` — nunca em `:0`; o perfil do editor é merge, não symlink |

---

## O que é o projeto

Portal jurídico brasileiro (`https://wikijuridica.com.br`, URL em `content/site.json`), sem
framework, sem CMS, sem SaaS. Fábrica de páginas jurídicas informativas com CTA quando os gates
de intenção e ética permitirem. **Meta P0: 10.000 páginas públicas aprovadas, únicas e
indexáveis**, com arquitetura que suporte centenas de milhares. O estado medido vive em
`CHECKPOINT.md` e em `./tools/check-contrato-vs-medicao` — **nenhum número de estado mora neste
arquivo**, porque número de estado envelhece por construção.

**O produto é o contexto jurídico de alta densidade, e a métrica que vale é retorno e citação por
agente de IA, medidos na borda** (DEC-058). O HTML humano é uma das serializações, ao lado da
gêmea Markdown, do MCP, do A2A e do `/api/v1`. **Mesmo conteúdo para bot e humano, sempre**:
serialização muda por URL e por `Accept`, nunca por User-Agent — o contrário é cloaking.

### Topologia

```
Cloudflare Tunnel → nginx 127.0.0.1:8088 → Go 127.0.0.1:8089
  (5 instâncias)     (root public/,          (socket do systemd,
                      proxy_cache wj_dyn)     só rota dinâmica)
```

**O acervo NÃO passa pelo Go** — sai estático do disco. Por isso o ledger do processo Go não
registra o rastreio do acervo. O nginx tem cache de origem com `use_stale`, enchido por
`tools/warm-origin-cache`.

`cmd/build` gera `public/` · `cmd/server` serve `:8089` · `cmd/check` é o runner de gates (hub em
`internal/checks`) · `internal/render` monta HTML por string builder, **não há templates** ·
`internal/agentsurface` é a fonte única das rotas de máquina. Configs em `content/*.json`, dado em
`data/`, ledgers em `.agents/`. **Publicação é transacional** e bloqueada por padrão. Estoque
canônico é o **v2**; o v1 cartesiano está morto (DEC-004).

**Linguagem é escolha por camada** (DEC-036): o que gera e serve HTML é Go, e trocar isso exige ADR
com benchmark 10k/100k. Fora do serving entra a linguagem que resolver melhor, com testes
alcançados por `tools/run-qualidade-diaria` — linguagem cujos testes ninguém roda não está aqui.

---

## A regra de ouro da publicação

Nenhuma URL vira pública sem a cadeia: **intenção única → fonte oficial auditada → texto autoral
útil → revisão jurídico-editorial → paid-intent classificado ou lane informativa → anti-template
→ title/meta/H1 únicos → HTML leve → canonical/robots/sitemap coerentes → smoke →
`published_manifest` → release transacional.**

**PUBLICAR E CORRIGIR** (ordem do dono, 2026-08-06): a régua é **partição por severidade**, não
gate binário. Sem páginas no ar não se observa bot nem se decide SEO.

- **Coerência de artefato é inegociável**: HTML em `public/`, sitemap, `published_manifest` e
  índice de release, com os SHA-256 batendo — `publishedmanifest.Validate` exige no boot. É o que
  impede 404 e página órfã no índice.
- **Crítico não publica.** Os motivos vivos estão em `tools/generate-v2-publication-severity`, a
  lista é **aberta**, e acrescentar motivo crítico é correção, não violação.
- **Médio publica e refina depois.** **Gate estatístico refutado por medição é pulado, com a
  evidência gravada** — e refutar exige medir, nunca opinar.
- **FATO é terminal; DIVERGÊNCIA entre dois instrumentos é BUG e se fecha por paridade; JUÍZO
  nunca mata conteúdo** — rebaixa para refino, com o `intent_id` no ledger.
- **Anti-fraude não se flexibiliza nunca.**

Check verde não substitui ler as amostras, e **gate verde não é "não quebrei nada"**: rode a
bancada do pacote. Detector novo nasce com teste de falso positivo sobre amostra real.

---

## Conteúdo, fonte e ética

**PT-BR natural e acentuado** em tudo visível ao público; código e slugs em ASCII. **Proibido
inventar** decisão, ementa, artigo, citação, data ou resultado.

**Fonte oficial é proveniência.** Texto oficial vira corpo **como citação identificada**, com URL,
data e hash (DEC-032), em **duas camadas** — citação e comentário autoral em blocos distintos, com
piso medido de comentário próprio. Decisão, súmula, tese e lei pela Lei 9.610/98 art. 8º; notícia
institucional **não** é coberta. Texto oficial sozinho é espelho.

**Publicidade é a REGRA, sigilo é a EXCEÇÃO.** Nome de parte e de agente público em ato oficial
PODE constar; o que sai é identificador (CPF, RG). Exceções taxativas em
`docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md`. **Suprimir demais destrói o ato**: 88 ocorrências de
"[nome removido]" já tornaram ilegível o canal diário.

**Ética da OAB: ver Regra 13.** O fundamento conferido em fonte primária, com URL e hash de cada
dispositivo, está em `docs/goal/JURIDICO_BASE.md` — leia-o antes de escrever qualquer regra de
conteúdo.

**Autoria é do advogado da plataforma, e nada publicado menciona ferramenta** (2026-09-09).
Nenhum artefato público menciona IA, modelo ou assistência; a nota de rodapé é
`editorial.MethodDisclosure(autor)` — função, não constante. A inscrição aparece **exatamente duas
vezes** por página, e uma terceira reprova. **Nenhum commit leva co-autoria de modelo.**

Escala editorial é **lote + validação massiva + reescrita automática**, nunca redação manual
página a página. **Página escrita nunca é descartada**: reprovada significa consertar, e antes de
tocar em texto redigido preserve o anterior em `.agents/runtime/` com data.

---

## Governança entre pares

**Nenhum modelo é superior ou inferior por identidade.** A DEC-019 fixou:
**Claude Code e Codex/GPT-5.6 são engenheiros-chefes autônomos** de suas frentes,
**sem presunção de superioridade ou inferioridade entre modelos**, com fiscalização cruzada. O dono
desativou o Codex em 2026-07-21 e todo o trabalho passou ao Claude Code: é proibido deferir,
enfileirar ou aguardar frente "do Codex", e onde um contrato disser "exclusivo do Codex" leia-se
"exclusivo do pipeline sancionado".

A regra **não caducou com a desativação** — vale entre as sessões e os agentes do próprio Claude
Code. **Divergência técnica se resolve por evidência, nunca por autoridade de modelo**, e fica em
`docs/goal/MAESTRO_CODEX_LOG.md`.

**Alocação de carga, que é outra coisa** (ordem do dono, 2026-09-22): **Fable 5.1 orquestra** a
sessão — no Claude Code e no Cowork —, **refuta** (`auditor-adversarial`) e cuida dos itens
graves (`especialista-critico`); **Opus 5.5 é o padrão de execução** (código, dado, gate, hook,
teste, conteúdo por gerador); **Sonnet 5 só colhe contexto** e escreve apenas em
`.agents/runtime/contexto/`; **Haiku é proibido**. O hook `block-agent-haiku.sh` barra Haiku e
Sonnet em agente que edita, e o `.claude/settings.json` fixa a versão de cada modelo. O `advisor`
segue como consulta e não substitui a refutação. *Superado nesta data o regime de 2026-09-15
(Opus 5 orquestrava, `advisor` obrigatório, Sonnet fora; texto no "Texto do item 14" do plano do
cérebro): o dono fixou o orquestrador e o papel de cada modelo.*
**Concordância entre agentes não é verificação; refutação tentada e falhada é.**

**O chefe fica em comunicação com os agentes e cobra entrega completa.** Cada agente mantém seu
contexto entre mensagens: reabrir custa uma fração de relançar, e evita que ele redescubra o que
já sabia. Comunica-se quando o alinhamento muda o que ele vai escrever — medição que derruba a
premissa do briefing, outra frente tocando o mesmo arquivo, decisão devolvida que é do chefe, e
**sempre que a entrega vier pela metade**. **Entrega parcial não se aceita**: ou o chefe implementa
o que falta, ou reabre o mesmo agente. **Relato sem evidência não fecha item.**

*Este parágrafo é cobrado por `internal/contract/misc/peer_governance_test.go` em quatro
documentos. A condensação de `64832bdd` o apagou e deixou o teste vermelho (BUG-171). Ao editar
esta seção, rode o teste.*

**Protocolo do barramento: obrigatório em toda onda de agentes** (ordem do dono, 2026-09-24:
"tudo está conectado"). Vale para o orquestrador e para cada agente.

1. **Investigar e abrir o barramento.** O chefe investiga antes de delegar. Depois, abre o arquivo
   `.agents/runtime/contexto/<data>-<onda>-achados-compartilhados.md`. O arquivo recebe só
   acréscimos. Leva o roster (o `agentId` de cada agente e a fatia dele) e os achados que o chefe
   já mediu.
2. **Todo achado que toca outra fatia sai por dois canais, no mesmo minuto.** Vai como linha no
   barramento e como `SendMessage` direto ao `agentId` afetado. O subagente só alcança o par pelo
   id que o chefe lhe passou. O chefe repassa o que chegar só a ele.
3. **Antes de fechar, cada agente relê o barramento.** Achado de outra fatia pode mudar o veredito.
4. **Permissão que falta é bug de ferramenta, não lacuna do mapa.** O chefe corrige a guarda, com
   teste, ou mede e publica o dado no barramento. Mapa pela metade não se aceita.
5. **Dado de agente não se perde.** Mapa, barramento e memória acompanham a máquina de produção.
   Memória que envelheceu ganha nota datada no topo e não é apagada.

O canal vivo é o `SendMessage`/`ListAgents` do Claude Code. Entre sessões, o bus de
`.agents/runtime/coordination/` continua valendo.

---

## Escala, autonomia e coordenação

**Alta escala**, por engenharia sistêmica — config, gerador, índice, gate proporcional, lote —,
nunca página a página. **Lentidão em 10k é bug P0**; proibido "corrigir" aumentando timeout.

**Você PODE e DEVE** ampliar documentação, contratos, políticas, gates, registries e código
quando isso destrava o projeto, **editando para frente** e preservando trabalho concorrente.
**Parágrafo superado ganha data e motivo; não se apaga.** Nunca afrouxando anti-fraude nem
qualidade, que se preservam por engenharia melhor.

**O projeto vizinho não é fonte.** Proibido importar código, config, script, unit ou padrão de
`/opt/divorcio`, nem "adaptando". Ler para diagnosticar é permitido; copiar dali, não.

**Coordenação entre sessões** pelo bus em `.agents/runtime/coordination/`. Em arquivo que outra
frente edita, **edição pontual** que preserva o não-commitado — nunca rewrite. **Não mate processo
de outra sessão**: load alto não autoriza `pkill`; lock ativo significa trabalhar outra frente.

**Ao SAIR para a rede, o portal é o WikijuridicaBot**, sempre por
`wikijuridicabot.Aplica(req, proposito)` — nunca User-Agent escrito à mão, nesta forma:

```
Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; <proposito>)
```

O prefixo `Mozilla/5.0 (compatible;` **não é disfarce e não é opcional**: medido em 2026-09-05
contra `planalto.gov.br`, todo UA sem ele levou `Recv failure` do WAF (F5 BIG-IP), e com ele veio
200. A URL `/bot/` **tem de responder** — agente cuja documentação dá 404 é tão opaco quanto
agente sem URL. Sonda do próprio portal usa `AplicaSondaInterna`, que escreve
`X-Warming-Request`; **sem ele a sonda entra na métrica e o portal mede o próprio eco**
(`tools/check-sonda-interna-declarada` mede isso no log de acesso, por fluxo). Sair como navegador
ou sob identidade de terceiro é proibido e cobrado por `TestNenhumPontoDeSaidaSaiDisfarcado`;
continua **legítimo** simular Googlebot com `httptest.NewRequest` contra o nosso próprio handler —
aquilo nunca sai da memória e é como se prova a paridade de conteúdo. Exceção de navegador real
com a sessão do titular entra **nomeada** em `wikijuridicabot.NavegadorRealDoTitular`, nunca por
omissão.

*(Os três parágrafos acima foram restaurados em 2026-09-16: a condensação de `9977c8ed` apagou o
prefixo de compatibilidade, a isenção do `httptest` e a URL `/bot/`, e deixou
`TestContratoDaSessaoCarregaAIdentidade` vermelho — o mesmo padrão do BUG-171. Regra travada por
teste só muda junto com o teste.)*

---

## A IA local

**O cérebro trabalha 24/7 e publica pela cadeia** (DEC-059): comentário, notícia e página passam
por gate de conteúdo, saem sob a assinatura do advogado e deixam proveniência em
`data/ai/publicacoes_cerebro.jsonl`. **Ele julga onde há texto a ler — atribuição de citação —,
nunca onde há limiar a comparar**: estatístico é juízo, e quem o classifica é o censo, como
MÉDIO, que publica.

*Precisão medida em 2026-09-16, porque a frase acima junta três rotas que no código são
diferentes, e a leitura errada faz procurar publicação de página dentro do processo do cérebro.*
**Comentário** sai pelo socket Unix assinado de `cmd/social` — `internal/cerebro/publicacao.go`,
único tipo implementado lá (`TipoSocketComentarioDeAutoridade`). **Página** NÃO sai por ali e não
poderia: a unit declara `ReadWritePaths=/opt/wiki/data/ai /opt/wiki/data/ops`, então o processo do
cérebro não escreve em `data/editorial/` **por desenho** — ela sai pela cadeia v2, de um gerador
privilegiado que lê o que o cérebro extraiu (§P6 do plano). **Notícia autoral** está em
construção nesta data. A cadeia da página, com `arquivo:linha` de cada elo e o que cada um
recusa, está em `docs/CADEIA_DE_ADMISSIBILIDADE_DA_PAGINA.md`; o parágrafo acima fica, porque o
regime que ele fixa não mudou — o que se acrescenta é por onde cada rota passa.

Ollama local, CPU-only por enquanto. **Custo do cérebro se corta em tokens processados, nunca em
inteligência** (2026-09-09): a extração é dominada pelo *prefill*, então prefixo reaproveitado,
esquema curto e `num_ctx` por tarefa valem mais que trocar de modelo. Parâmetros vivos, física
medida e o que muda com GPU: `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` e
`.claude/rules/fila-do-cerebro.md`.

**Coleta: o máximo, de forma educada e com proveniência.** Fonte oficial e API pública se
coletam, armazenam, indexam e servem (Regra 9). Notícias, portais privados e blogs entram como
**sinal interno** — metadado e trecho com URL, data e hash, `robots.txt` e taxa honrados — e
nunca como corpo. Análise de atores públicos só sobre atos públicos, em agregado, com redação
sóbria: "índice de reforma", nunca "chance de êxito".
