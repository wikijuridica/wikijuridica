# CAÇA AOS BUGS — /opt/wiki — plano operacional de engenharia

> **Status:** DOCUMENTO VIVO, aprovado pelo dono em 2026-08-29 e commitado na
> mesma sessão. Cada bug novo entra aqui, cada task fechada é marcada aqui, o
> contador de restantes fica aqui. O registro canônico de defeito continua sendo
> `docs/goal/BUGLOG.md` (BUG-013 em diante); as tasks vivem em
> `.agents/runtime/p0_frontboard.jsonl` com o prefixo `caca-`.

---

## 1. Contexto — por que esta caça, e o que já foi medido antes de escrevê-la

O `/opt/wiki` é um portal jurídico brasileiro cujo caminho de serving é Go (DEC-036) e que serve **10.111
páginas públicas** (`published_manifest.jsonl`, chave `unique_intent_id`,
medida hoje) atrás de 20 réplicas de Cloudflare Tunnel → nginx `127.0.0.1:8088`
→ Go `127.0.0.1:8089`. O acervo sai estático do disco; o Go só atende rota
dinâmica.

O repositório cresceu muito rápido: **2.327 arquivos `.go`** em 760 diretórios,
**1.162 scripts** em `tools/`, **322 gates** registrados em
`internal/checks/checks.go` (12.254 linhas), 20 timers systemd em produção,
12 GB em `data/`, 7,7 GB em `.agents/`. Nessa escala, defeito não se encontra
por leitura casual: encontra-se por **caça dirigida, medida e adversarial**.

O pedido do dono é explícito e não admite recorte: caçar bugs de **qualquer
engenharia do projeto** — código, conteúdo, SEO, GEO, rastreio de bots,
infraestrutura, servidor, dados, segurança, performance — **inclusive os
pré-existentes**, **sem ignorar nada**, **documentando e corrigindo na mesma
sessão**.

### O que eu já medi antes de escrever este plano (não é suposição)

| # | Medição | Resultado | Veredito preliminar |
|---|---|---|---|
| M1 | `public/*.html` × `published_manifest` | 10.340 HTML × 10.111 rotas; **0 rotas do manifesto sem HTML** | coerência de artefato OK neste eixo |
| M2 | Os 229 do delta | hubs de área, paginação de hub, institucionais (`/`, `/buscar/`, `/aviso-legal/`, `/contato/advogado/`) | legítimos, **não são órfãos** |
| M3 | Sitemap índice × disco | 34 shards no índice, **62 no disco**, 28 fora | os 28 têm mtime de 28/08 → carência de 8 dias, esperado |
| M4 | URLs anunciadas × disco | 10.336 anunciadas, **0 anunciam 404**, **0 publicada fora do índice** | OK |
| M5 | HTML fora do sitemap | 4: `50x.html`, `/buscar/`, `/contato/advogado/`, `/fontes/planalto/` — os 3 últimos com `noindex,follow` | correto por desenho |
| M6 | BUG-005 do BUGLOG ("CTA aponta para página inexistente", status *aberto*) | `/contato/advogado/` existe e responde **200** em produção | **BUGLOG mente — R1 violada** |
| M7 | `published_manifest` integridade | 10.111 linhas, 10.111 `unique_intent_id` distintos, **0 JSON inválido** | OK |
| M8 | `CLAUDE.md` declara 10.107 páginas | medido 10.111 | dentro da tolerância do gate, mas **desatualizado** |
| M9 | `./tools/check-untracked-product-inventory` | **EXIT 1 — REPROVADO**: 70 produtos untracked, 4 com mais de 24 h | gate vermelho vivo |
| M10 | `.claude/settings.json` | 53 linhas de `enabledPlugins` removidas, não commitadas | origem a apurar antes de qualquer commit |

*(as demais medições — código Go, gates, infra, conteúdo, segurança, padrões
externos — estão sendo produzidas por ondas de reconhecimento e entram na
seção 6 antes da aprovação)*

---

## 2. REGRAS VINCULANTES DE EXECUÇÃO — valem para mim e para todo agente

Estas regras vão **coladas no prompt de cada agente** desta caça. Violá-las
invalida o trabalho do agente e o resultado é refeito, não aproveitado como
está.

### 2.1 O que fundamenta a decisão

1. **Comentário, README, doc e nome de arquivo NÃO são fonte.** Só o código
   executado, o dado vivo e a medição própria. Comentário que mente é **bug a
   corrigir**, não contexto a respeitar (R1). *M6 acima é exatamente isso.*
2. **Gate verde não é prova; gate vermelho não é veredito.** Antes de acreditar
   num gate, lê-se a implementação do detector (R2).
3. **Toda afirmação numérica vem de medição própria reprodutível**, com o
   comando junto. Hash determinístico — nunca `hash()` do Python (R3).
4. **Ler → medir → entender o contexto → testar → só então alterar.** E depois
   de alterar, **testar de novo** (regressão) até ter 100% de confiança de que
   nada regrediu.
5. **Refutação tentada e falhada é verificação; concordância entre agentes não
   é.** Todo achado caro passa por crítico adversarial (Fable) que tenta
   derrubá-lo (R8).
6. **Relatório de agente é ALEGAÇÃO** até verificação própria no disco: diff
   real, amostra do dado, exit code (R8).

### 2.2 O que é proibido

7. **PROIBIDO deixar para depois.** Nada de "próxima sessão", "futuro", "fica
   documentado para tratar", "fora de escopo desta onda". Achado vira correção
   **na mesma sessão** (R7). Documentar **não substitui** resolver.
8. **PROIBIDO arrumar desculpa.** "Depende do bot", "é do outro time", "falta
   dado", "não existe ferramenta" não são respostas. Falta dado → **cria-se a
   medição**. Falta ferramenta → **constrói-se** (R4, R6).
9. **PROIBIDO relaxar gate para passar.** Reprovou? Corrige-se o elo que
   reprovou. Afrouxar gate é fraude operacional.
10. **PROIBIDO descartar dado de agente.** Todo relatório, medição, achado
    refutado e falso positivo é **arquivado e triado** — inclusive o que foi
    REFUTADO, porque saber que algo não é bug tem valor e evita re-investigação.
    Nada de "o agente errou, joguei fora": vira registro com o motivo.
11. **PROIBIDO stub, placeholder, mock, TODO ou fake** em produção. **PROIBIDO**
    inflar métrica ou sondar com User-Agent de bot real (fraude com consequência
    legal) — sonda só com
    `-A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true'`.
12. **PROIBIDO reverter ou descartar trabalho:** nada de `git reset`,
    `checkout`, `restore`, `revert`, `stash`, `clean`, `cherry-pick`. Para ler
    estado antigo, `git show HEAD:arquivo`. Para escopar commit, pathspec.
13. **PROIBIDO** ler ou tocar `/opt/divorcio`. **PROIBIDO** `./...` em comando
    Go (não expande — `var/nginx` tem modo 0700). **PROIBIDO** `cmd/check` sem
    argumento (roda 322 gates). **PROIBIDO** `--no-verify`.
14. **PROIBIDO terceirizar ao dono** cadastro, credencial, token, comando ou
    aprovação do óbvio (R5). Nada de SaaS, API key ou serviço pago —
    **self-hosted first**; OSS (MIT/BSD/Apache) é para instalar e integrar, com
    ADR + licença + versão fixada + benchmark 10k/100k.

### 2.3 O que é obrigatório

15. **Todo achado vira entrada numerada no BUGLOG** (`BUG-013` em diante,
    mesmo formato: ID, data, sintoma, causa raiz, correção, status) **e** uma
    task neste plano. Um achado sem ID não existe.
16. **Toda correção vira teste**: teste focado que reproduz o defeito (vermelho
    antes, verde depois) e teste de regressão do que estava certo. Sem teste, a
    correção não fecha.
17. **Commit por frente, na mesma sessão em que a correção nasce.**
    `git add` separado de `git commit`, mensagem por `-F arquivo` (nunca
    capturar log no mesmo arquivo da mensagem — sobrescreve). Commit de
    conteúdo/dado/doc é leve; commit que toca Go/go.mod/go.sum builda (~5 min) e
    é serializado com `flock /tmp/opt-wiki-agent-heavy.lock`.
18. **Antes de declarar pronto: `advisor`.** Cadência mínima — antes de cada
    frente, ao mudar de abordagem, quando a medição contraria o esperado, e
    antes do "pronto", com o entregável já durável em disco.
19. **Escala por engenharia sistêmica**, nunca página a página. Sem teto de
    agentes; o limite do harness é por workflow, então escala vem de **muitos
    workflows**.
20. **Coordenação entre sessões.** Medido agora: `./tools/check-coord-status`
    lista várias presenças, **todas `[STALE]`** (a mais recente com 12.799 min),
    e o `ai-brief` mostrou um workflow `wf_49ef78f9` que **não é meu** — pode
    haver outra sessão viva. Antes de tocar arquivo compartilhado: registrar
    presença (`tools/generate-coord-presence`), ler o inbox
    (`tools/check-coord-inbox`), consultar `tools/check-load-headroom --max 12`.
    Em arquivo com mtime recente de outra frente, **edição pontual** que preserva
    o não-commitado — nunca rewrite que apague.
21. **Atacar a família, não o caso.** Terceira correção no mesmo subsistema =
    parar e corrigir a classe inteira (é o que a FAMÍLIA-A da §11 já exige).
22. **NADA FICA FORA DO ESCOPO — ordem expressa do dono (2026-08-29).**
    Eu sou o engenheiro-chefe de **todo** o repositório, da produção e da
    infraestrutura. Bug é para corrigir sendo de frente minha ou não; sessão
    concorrente termina, o defeito não. **É PROIBIDO recortar escopo alegando
    "é território de outra sessão"** — isso é a desculpa que o contrato veda.
    Medido durante o planejamento: o `CLAUDE.md` mudou no disco enquanto eu
    escrevia (bloco de analytics reescrito, `docs/MEDICAO_DE_AUDIENCIA.md`
    novo, `target="_blank"` com aviso WCAG 3.2.5, `internal/htmlpolicy`
    aceitando o token `^_blank$`), e o `ai-brief` mostrou um workflow que não é
    meu. Isso muda o **método**, nunca o **escopo**: antes de tocar um arquivo,
    `git status` + `stat` do alvo; em arquivo com mtime recente, **edição
    pontual** que preserva o não-commitado; **nunca** rewrite que apague; e a
    leitura do estado é sempre a do disco no instante da edição, não a que eu
    tinha em contexto. Trabalho alheio se **preserva e se integra** — nunca se
    exclui nem se reverte.

### 2.4 As minas deste repositório (custaram sessão real — não pisar de novo)

| Mina | Regra de execução |
|---|---|
| Mexer no HTML de **todas** as páginas (render/seo/pageinline/meta nova) | agrupar numa **única** publicação; **`tools/deploy-publico --ressemear`** (⚠ mudou hoje — commits `0c165d36`/`205820ff`: a flag passou a ser alcançável de dentro do deploy, `deploy-publico:127`; a instrução antiga de "rodar entre gerar `public/` e o deploy" está **superada** — ler o script antes de seguir doc velho); **purga ampla manual** (`./tools/purge-edge-cache`) depois; medir taxa de 304 |
| Purga por conteúdo é **cega** a mudança de script | por isso a purga ampla é obrigatória — senão a borda serve dois acervos por dias (`s-maxage=604800`) |
| Página v2 | **dois commits**: `portfolio_v2/` primeiro, `v2_pages/` depois; `./tools/check-v2-portfolio-pairing` antes (< 1 s) |
| Chaves que enganam | manifesto usa `unique_intent_id`; registro v2 **não tem** `path`; corpo = `opening` + `sections[].text` + `faq[].q/a`; `word_count` **inclui headings** (`internal/v2ingest/validate.go:1011`, tolerância 10%) |
| `check-portal-health` | sonda só `127.0.0.1` — passa verde com o túnel caído |
| `check-http-smoke` / `check-googlebot-smoke` | montam handler em memória (`httptest`) — **não tocam a rede**, não provam o servidor vivo |
| Ledger de borda | cumulativo intradiário; leitor canônico é `serie_saneada`; somar linhas dá número absurdo |
| Ausência de linha | **não é** ausência do fato — `git log --diff-filter=A` diz quando o produtor nasceu |
| `cmd \| tail` | o `$?` é do `tail` — sempre `${PIPESTATUS[0]}` |
| Sondar fonte oficial | HEAD primeiro; **GET com range de 1 byte** quando vier 403/405 (o WAF do gov.br recusa o método, não o agente) |
| `public/` é gitignored | não há backup; antes de remover qualquer coisa de lá, **arquivar** em `.agents/runtime/archives/` com data |
| Gate órfão | **órfão ≠ morto**: rode-o antes de aposentar. Já quase se desligaram 10 gates saudáveis em bloco |
| Untracked | **todo `??` é investigado**, nunca presumido ruído (`uta.json` parecia lixo e era o mapa de IPs do Google) |
| `\b` do Go é ASCII | corta palavra em português — detector com `\b` produz falso positivo/negativo em acentuada |

---

## 3. Governança da documentação — onde escrever, sem duplicar nada

O repositório já tem 21 documentos que registram bug, achado ou pendência.
**Não se cria um vigésimo segundo.** A caça usa a estrutura existente:

| Documento | Papel nesta caça |
|---|---|
| `docs/goal/BUGLOG.md` (123 linhas, BUG-001..BUG-012) | **Registro canônico de defeito.** Todo bug novo entra como `BUG-013`, `BUG-014`… no mesmo formato (ID, data, sintoma, causa raiz, correção, status). Bug pré-existente cujo status mudou é **atualizado ali**, não reescrito em outro lugar. |
| `docs/goal/PLANO_CACA_BUGS_20260829.md` **(criar)** | **Este plano.** Tasklist viva, contador de restantes, registro de onda, decisões da caça. É onde se consulta "quantas faltam". |
| `.agents/runtime/p0_frontboard.jsonl` (existe, 290 linhas) | **Frontboard.** Uma linha por task, com `id`, `frente`, `front`, `status`, `note`. Estendido — nunca reescrito. |
| `docs/goal/DECISIONS.md` (DEC-035 é a última) | Decisão de arquitetura/política que a caça tomar entra como `DEC-036`+. |
| `docs/ACHADOS_ABERTOS_20260806.md`, `docs/goal/PROJECT_GAPS.md`, `docs/goal/STATUS.md`, `docs/goal/TASKLIST_PLANO_20260819.md` | **Fonte de bugs pré-existentes a ingerir**, e onde marcar o item como fechado quando a caça o fechar. |
| `docs/OPERACAO_COMANDOS_E_CAMINHOS.md`, `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`, `docs/ARQUITETURA_FIEL.md` | **Onde entra a armadilha nova** que a caça descobrir — o formato "isto custou uma sessão" já existe. |
| `docs/goal/PROMPT_GOAL_4K.txt` (3.997 chars, **stale** — fala de "0 aprovadas") | Reescrito **no mesmo arquivo**, ≤ 4.000 caracteres medidos com `wc -m`. |
| `CLAUDE.md` | Atualizar a linha de contagem medida (10.107 → medição do dia) no commit que a mudar. |

**Regra anti-duplicação:** antes de criar qualquer arquivo `.md`, procura-se o
documento que já cobre o assunto. Documento novo só nasce se nenhum dos 21
couber — e, nesse caso, é linkado a partir deste plano.

---

## 4. Frontboard — como o acompanhamento funciona na prática

`.agents/runtime/p0_frontboard.jsonl` recebe, por task:

```json
{"id":"caca-B013.1","fase":"caca-bugs-20260829","frente":"<domínio>",
 "front":"<o que é>","status":"todo|doing|done|refutado",
 "bug":"BUG-013","evidencia":"<comando/arquivo:linha>",
 "verificacao":"<teste que prova>","note":"<o que mudou e por quê>"}
```

- `status: refutado` é **status de sucesso**: significa que a suspeita foi
  investigada e derrubada por medição. Fica registrada para ninguém
  re-investigar. **Nenhuma linha é apagada.**
- O contador de restantes deste plano (§9) é derivado do frontboard:
  `grep -c '"status": *"todo"'`.

---

## 5. Método operacional — o ciclo de cada bug, sem atalho

Todo item, do crítico ao warning, percorre os **oito passos**. Pular um passo é
falha de processo, não economia:

1. **LER** — o código, o dado vivo e o contrato aplicável. Arquivo:linha na mão.
   Nunca confiar em comentário, README ou nome de arquivo.
2. **MEDIR** — reproduzir o defeito com comando próprio, guardando a saída. Se
   não reproduz, não é bug ainda: é suspeita.
3. **ENTENDER O CONTEXTO** — por que o código está assim? Ler o histórico
   (`git log -S`, `git show HEAD:`), a decisão (DEC-*), o precedente
   (`docs/PRECEDENTES_DAS_ORDENS.md`). Muita coisa que parece bug é desenho.
4. **TESTE QUE FALHA** — escrever o teste que reproduz o defeito e vê-lo
   **vermelho**. Sem isso, não há prova de que a correção corrigiu algo.
5. **CRÍTICA ADVERSARIAL** — antes de editar algo caro de reverter, um agente
   Fable tenta **REFUTAR** o diagnóstico com evidência. Se ele derruba, o achado
   vira registro de falso positivo (não se descarta).
6. **CORRIGIR A CAUSA RAIZ** — nunca o sintoma, nunca relaxando o gate, nunca
   com stub. Se a correção toca o HTML de todas as páginas, aplica-se o
   protocolo de publicação agrupada da §2.4.
7. **REGRESSÃO** — o teste novo fica verde **e** a suíte focada do pacote
   continua verde **e** os gates que cobrem a área continuam verdes. Medição
   antes/depois registrada.
8. **REGISTRAR E COMMITAR** — BUGLOG atualizado, frontboard atualizado,
   contador deste plano decrementado, commit por frente na mesma sessão.

**Triagem por severidade** (a régua do projeto, não invenção nova):

| Nível | Critério | Prazo |
|---|---|---|
| **P0 crítico** | fora do ar, dado errado servido, fraude, risco OAB, perda de produto, regressão de indexação | corrigir **antes** de qualquer outra coisa |
| **P1 grave** | gate vermelho vivo, timer em falha, rota anunciada com 404, alerta falso, teste vermelho | corrigir na sessão |
| **P2 médio** | detector desatualizado, doc que mente, série sem consumidor, performance degradada | corrigir na sessão |
| **P3 warning** | lint, ferramenta ausente, cobertura de teste, higiene de repositório | corrigir na sessão — o dono pediu **até os warnings** |

Nenhum nível autoriza adiamento. A severidade ordena a **fila**, não decide o
que fica de fora.

---

## 6. Como o reconhecimento foi feito — e por que o backlog é confiável

O backlog da §11 não veio de leitura casual. Veio de **cinco frentes
independentes**, cada achado passando por confronto:

| Frente | O que cobriu | Estado |
|---|---|---|
| Explore A | código Go, 322 gates, testes, `tools/`, docs de bug | entregue e verificado |
| Explore B | timers, ledgers de ops, nginx/CSP, sitemap, robots, bots, segurança | entregue e verificado |
| Explore C | estoque v2, severidade, qualidade textual, fontes, citação legal, ledgers, git | entregue e verificado |
| Workflow 1 | padrões oficiais externos (SEO/GEO/bots), ferramental ausente, performance, segurança, observabilidade — cada um com verificador + 3 críticos Fable sobre os seeds | em curso |
| Workflow 2 | compilação/vet, testes vermelhos, bateria dos ~450 `check-*`, docs gigantes, HTML servido, citação legal/OAB — cada um com verificador adversarial | em curso |

**Três coisas tornam este backlog diferente de uma lista de suspeitas:**

1. **Eu reproduzi pessoalmente todo achado que virou P0/P1.** Exemplos: rodei o
   `systemctl show` do `edge-warm`, sondei os 3 `.tar.gz`, contei os
   `unique_intent_id`, cruzei manifesto × disco × sitemap, li o
   `UnicodeDecodeError` no traceback, contei `58 br + 62 xml`, achei o
   "Codigo de Defesa do Consumidor" **dentro do HTML servido**, confirmei que a
   CLT do corpus não tem os arts. 189 e 195.
2. **Dezoito suspeitas foram REFUTADAS e ficam registradas** (tabela ao fim da
   §11) — nenhuma descartada. Duas eram minhas, e a crítica adversarial derrubou
   mais uma dentro do próprio plano (a distribuição de severidade estimada à
   mão).
3. **Os achados que ainda não reproduzi estão marcados como tal** e o primeiro
   passo da task é reproduzir, não corrigir.

**Três itens exigem o passo 3 do método (entender o contexto) antes de qualquer
correção — porque podem ser desenho, não defeito:**

- **BUG-017** — `Result=success` sobre onda parcial é declarado "para não
  relançar em laço". Mudar a semântica da unit pode criar restart loop. A
  correção provavelmente é o canal de alerta, não a unit. **Ler a intenção
  antes.**
- **BUG-029** — `etag off` é mudança **deliberada de 28/08** (existe
  `.agents/runtime/nginx.conf.pre-etagoff-20260828`). A task é *medir 304 por
  bot*, **nunca religar ETag** — isso reverteria trabalho de ontem.
- **BUG-031** — a queda de revisita pode ser o efeito **documentado** de
  republicação em massa (reseed de 28/08 re-datou o acervo; já foi medido
  acontecer 2× com o `meta-externalagent`). A task nasce como *"atribuir causa
  cruzando `efeito-nos-bots` e `efeito-deploy` com o ledger de deploy"*, não
  como "consertar a queda".

E **BUG-040** (1.707 páginas hub-only) fica em **P2**, não P1: o gate passa
verde porque hub-only é o piso desenhado. É melhoria de malha interna, e entra
no backlog porque o dono pediu até o nível de warning — a severidade ordena a
fila, não decide o que fica de fora.

---

## 7. Ondas de execução — como a equipe é dirigida

Eu sou o chefe: investigo pessoalmente antes de delegar, dirijo as ondas, tria,
verifico no disco, corrijo o que é caro e commito. Subagentes são executores;
o resultado deles é **alegação** até eu conferir.

**Papéis fixos:**
- **Opus 5** — investigadores, corretores e engenheiros de cada domínio.
- **Fable 5** — crítico adversarial, sempre com prompt de **REFUTAÇÃO** ("tente
  derrubar isto com evidência"), nunca "o que você acha?". Entra antes de toda
  edição cara de reverter.
- **`advisor`** — conselheiro de engenharia, na cadência mínima da §2.3.

**Onda 0 — reconhecimento: CONCLUÍDA.** 3 exploradores + 2 workflows (27
agentes ao todo, cada frente com verificador adversarial) cobriram
código/gates, infra/SEO/bots, conteúdo/dados, padrões oficiais externos,
ferramental, compilação/testes, bateria dos 450 `check-*`, docs gigantes, HTML
servido e citação legal. Resultado: as §11 e §12.

**Commit 1 (primeiro ato da execução, antes de qualquer correção):**
1. Este plano copiado para `docs/goal/PLANO_CACA_BUGS_20260829.md`.
2. As 133 entradas gravadas em `docs/goal/BUGLOG.md` (relendo o disco antes —
   §7.2) e as 133 linhas `"status":"todo"` + FAMÍLIA-A semeadas no
   `.agents/runtime/p0_frontboard.jsonl`, para que o contador passe a ser
   derivado e não digitado.
3. `docs/goal/PROMPT_GOAL_4K.txt` reescrito e re-medido com `wc -m`.
4. `CLAUDE.md` com a contagem do dia (medida no instante do commit).
5. Os 7 produtos untracked de `BUG-053` commitados por pathspec, e o ruído de
   `BUG-054` classificado no `.gitignore` — **nada deletado**.

**Ondas 1..N — correção, uma por família de defeito.** Cada onda:
`pipeline(defeitos, corrigir → verificar adversarialmente)`, com o número de
agentes fixado **por mim** a partir da triagem (nunca `findings.map()` cego, que
entrega a cardinalidade ao subagente). Após cada onda: verificação própria no
disco, gates focados, commit.

**Onda de ferramental.** O que o reconhecimento apontar como ferramenta ausente
vira instalação e integração real (gate ou timer), com ADR, licença, versão
fixada e benchmark 10k/100k. Self-hosted, sem cadastro em terceiro.

**Onda final — regressão ampla e fechamento.** Gates focados dos domínios
tocados, smoke HTTP, sondas de produção, `advisor` antes de declarar pronto, e
o `PROMPT_GOAL_4K.txt` reescrito.

### 7.1 Ordem de execução dos críticos — a cadeia que não pode ser invertida

Três dependências duras. Executar fora desta ordem produz retrabalho ou dois
deploys onde cabia um:

1. **Destravar a entrada primeiro.** `BUG-102` (atestação do validador) bloqueia
   `cmd/ingest-v2-stock`: enquanto ele estiver quebrado, nenhum estoque v2 novo
   entra. E o `go generate ./internal/v2ingest` tem de rodar **depois** de
   commitar as mudanças em Go — senão o hash se move e quebra de novo (foi o que
   se mediu acontecer durante o próprio planejamento).
2. **Build verde antes de qualquer publicação.** `BUG-101` (`cmd/build` reprova
   com 261 achados) é **pré-requisito duro** de toda a frente de HTML: não existe
   `--ressemear` + deploy com o build vermelho. A cadeia é
   `BUG-114` (os 259 do `source_id` do `/diarios/`) + `BUG-137` (os 2 falsos
   positivos de texto, corrigidos **no detector**, nunca relaxando) → build verde
   → só então a publicação.
3. **UMA publicação agrupada para todo o HTML.** `BUG-103` (contraste WCAG),
   `BUG-085` (datas ISO), `BUG-086` (`image`/`wordCount`/`articleSection`),
   `BUG-087` (`max-image-preview`) e `BUG-127` (script de medição na 404) **mudam
   o HTML das 10.339 páginas**. Vão numa **única** publicação, com `--ressemear`
   entre gerar `public/` e `tools/deploy-publico`, `./tools/purge-edge-cache`
   depois, e a taxa de 304 medida em seguida. Fazer em duas levas re-data o
   acervo duas vezes e rebaixa os bots duas vezes.

Fora da cadeia, e por isso podem correr em paralelo desde o primeiro momento:
`BUG-056` (CVE), `BUG-107` (falso-verde do `vet`), `BUG-104` (cache do
`googlebot-smoke`), `FAMÍLIA-A` (universo do sitemap), `BUG-060` (ramo morto do
`check-edge-live`) e toda a higiene P3.

### 7.2 Antes de gravar no BUGLOG: reler o disco

Há sessão concorrente commitando. O plano reserva `BUG-013+`, mas **o BUGLOG é
relido no instante da gravação**: se `BUG-013` já estiver tomado, renumera-se o
lote inteiro — e, nesse caso, o `PROMPT_GOAL_4K.txt` (que cita "BUG-013..145")
é reescrito e **re-medido com `wc -m`** no mesmo commit.

---

## 8. Verificação — como se prova que a caça funcionou

Para cada correção, e no fecho de cada onda:

| Camada | Comando | O que prova |
|---|---|---|
| Compilação | `./tools/go-modern build ./internal/... ./cmd/...` | o módulo compila (nunca `./...`) |
| Análise | `./tools/go-modern vet ./internal/... ./cmd/...` | classes que o grep não pega (copylocks, printf, lostcancel) |
| Teste focado | `./tools/go-modern test -count=1 ./internal/<pkg>/` | o defeito não volta |
| Corrida | `./tools/go-modern test -race -count=1 ./internal/checks/` | data race na região paralela |
| Gate nomeado | `./tools/go-modern run ./cmd/check <nome>` | o contrato do domínio |
| Gate de bancada | `./tools/check-<nome>` | leitura read-only do estado vivo |
| Smoke | `./tools/check-http-smoke` | handler em memória (**não** prova o servidor vivo) |
| Origem | `curl -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' http://127.0.0.1:8088/...` | o que o nginx entrega |
| Borda | mesma sonda contra `https://wikijuridica.com.br/...` | o que o mundo recebe (é a única que prova produção) |
| Paridade | `./tools/check-paridade-go-nginx` | o Go e o nginx concordam |

**Antes/depois obrigatório** em qualquer correção de performance ou de volume:
o número medido antes, o número medido depois, e o comando dos dois.

---

## 9. Tasklist e contador

A tasklist definitiva é montada ao fim do reconhecimento (§11) e espelhada no
frontboard. Formato de cada linha:

```
[ ] BUG-0NN · P<n> · <domínio> · <título>
    medição: <comando que prova o defeito>
    correção: <arquivo/ação>
    verificação: <teste ou gate que fecha>
```

**Contador** (atualizado a cada fechamento, no topo da §11):
`ABERTAS: N · EM CURSO: N · FECHADAS: N · REFUTADAS: N`

---

## 10. Prompt `/goal` da próxima sessão

Última task da caça: reescrever `docs/goal/PROMPT_GOAL_4K.txt` em modo
operacional, **medido com `wc -m` para ficar ≤ 4.000 caracteres**, dizendo
explicitamente que todos os bugs — inclusive os pré-existentes — são para
corrigir, sem margem para adiamento nem desculpa. O texto proposto está na §12.

---

## 11. Backlog medido

> ## ⚠ RE-TRIAGEM É O PASSO ZERO — o repo se moveu durante o planejamento
>
> A crítica adversarial Fable derrubou uma premissa estrutural, e eu **confirmei
> por medição própria**: **15 commits pousaram no repo durante a redação deste
> plano**, e três dos itens críticos **já estão corrigidos**.
>
> | Item | Estado real, medido por mim agora | Commit |
> |---|---|---|
> | **BUG-103** (contraste 1,81:1) | **FECHADO E NO AR.** `.site-footer a{color:#D9B96A;}` em `render.go:2032` **e** `.site-footer a{color:#000;}` na folha de impressão em `:2086` — o buraco do `@media print` que o plano previu **já está fechado**. 12/12 páginas servidas amostradas trazem a regra. | `9053fe77` |
> | **BUG-102** (atestação do validador) | **FECHADO.** `test -run TestPrepareTransactionPlanSnapshots…` → **ok, exit 0, 1,96 s**. A fábrica não está travada. Residual: o detector novo monitora; agir só quando ficar vermelho. | `63ed4b2d` + `a8f1d824` |
> | **BUG-013** (edge-warm em falha) | **PARCIAL.** A unit agora sai `Result=success ExecMainStatus=0` — mas o fix foi por **deduplicação** (`dict.fromkeys`, `warm-edge-cache:156`), **não** por trocar a fonte: o glob ainda lê `public/sitemaps/*.xml` (`:49,131,139`). **A FAMÍLIA-A continua viva.** | `42c6ea40` |
> | **BUG-014** (alerta 81% inflado) | **VIVO.** Última linha do ledger, **pós-fix**: `universo_urls: 18731`, `cobertura_pct: 0.0`. `check-edge-cache-coverage:78` segue globando o disco. | — |
>
> **Executar o BUG-103 agora SERIA o dano** — re-publicação redundante do acervo
> inteiro, exatamente o que a §2.4 existe para impedir. Por isso:
>
> **Nenhuma onda parte antes de re-triar os 133 contra o `HEAD` do momento.**
> A re-triagem é barata (reproduzir a medição de cada item é o passo 2 do método
> de qualquer forma) e é o que impede a caça de gastar uma onda inteira
> consertando o que outra frente já consertou. Itens que caírem vão para a
> tabela de refutados **com o commit que os fechou**, nunca apagados.

**CONTADOR.** O comando que eu tinha declarado
(`grep -oE 'BUG-[0-9]{3}' | sort -u | wc -l`) devolve **138**, não 133 — ele
apanha as referências a `BUG-001/004/005/011/012` do BUGLOG antigo. O comando
correto, que produz o número declarado:

```bash
grep -oE 'BUG-(0[2-9][0-9]|1[0-4][0-9])' PLANO.md | sort -u | \
  awk -F- '$2+0>=13 && $2+0<=145' | wc -l   # → 133
```

Com as **4 lacunas** que a crítica adversarial abriu (`BUG-146..149`), o
catálogo vai a **137**:

`ABERTAS: 134 · FECHADAS DURANTE O PLANEJAMENTO: 2 · PARCIAIS: 1 ·
FAMÍLIAS SISTÊMICAS: 1 · REFUTADAS: 18`

Os 133 vão de `BUG-013` a `BUG-145` (o BUGLOG já usa 001–012). Distribuição
**contada por script sobre este próprio arquivo**, não estimada:
**19 críticos · 50 graves · 37 médios · 27 leves/melhoria** (soma = 133).
Nenhum item foi cortado por severidade — o dono pediu **até os warnings**, e a
severidade ordena a fila, não decide o que fica de fora.

> **Registro de autocorreção.** A primeira versão desta linha dizia
> "11 · 41 · 47 · 34". Era estimativa à mão, e o `advisor` a derrubou. Recontei
> por script e o número mudou em todas as quatro faixas. Fica registrado porque
> é exatamente a R1 que este plano cobra dos outros — e porque prova que a
> cadeia medir → refutar → corrigir funciona inclusive contra mim.

**Como este número se mantém honesto na execução:** passa a ser derivado do
frontboard (`grep -c '"status": *"todo"'`). Para isso valer, o **commit 1**
precisa semear as 133 linhas `todo` (+ FAMÍLIA-A) no
`.agents/runtime/p0_frontboard.jsonl` — senão o contrato do contador nasce
falso.

**Sobre os números serem snapshots:** as contagens deste plano são do instante
da medição, e o repositório **se moveu durante o planejamento** — o manifesto
saiu de 10.111 para 10.116 (deploy às 04:55 + `daily-content`), e o
`static-freshness` que estava vermelho às 04:47 ficou verde às 04:55. Isso não é
divergência a "corrigir": é a razão pela qual **cada task começa reproduzindo a
medição** antes de tocar em qualquer coisa.

### P0 — crítico

**BUG-013 · `wikijuridica-edge-warm.service` em falha crônica, e a causa é um glob**
`systemctl show` → `Result=timeout ExecMainStatus=15 ActiveState=failed`; duas
execuções consecutivas mortas por SIGTERM (28/08 22:13 e 29/08 02:11) contra
`TimeoutStartSec=45min`. Causa medida: `tools/warm-edge-cache:49` e
`tools/check-edge-cache-coverage:78` leem `public/sitemaps/*.xml` **do disco**
(62 arquivos, 18.772 `<loc>`) em vez do índice `public/sitemap.xml` (34 shards,
10.336 URLs únicas) — universo inflado em **+81,6%**. Com `--so-frios` cada URL
fria custa HEAD+GET, e o trabalho deixa de caber na janela.
*Correção:* derivar o universo do **índice**, não do disco. *Verificação:* a
unit completa dentro da janela e `edge_cache_warm.jsonl` volta a receber linha.

**BUG-014 · O alerta crítico que a mesma inflação produz está 81% errado**
`edge_cache_coverage.jsonl` publica `universo_urls: 18.726` e o alerta afirma
que "~18.726 páginas devolveriam 530 se o túnel cair". O número real é 10.336.
Alerta crítico com número errado dessensibiliza para o alerta verdadeiro.

**BUG-015 · 3 rotas anunciadas na superfície de máquina respondem 404**
`/.well-known/agent-skills/index.json` anuncia 13 skills; os bundles
`conversar-com-o-agente-a2a.tar.gz`, `obter-credencial-de-agente.tar.gz` e
`usar-o-servidor-mcp.tar.gz` respondem **404** na origem e na borda.
**Causa-raiz que eu mesmo isolei:** os três arquivos **existem** em
`content/agent-skills/dist/` (medido) e **não são copiados** para
`public/.well-known/agent-skills/` — `find public -name '*.tar.gz'` devolve 0.
*Correção:* o build/deploy passa a publicar os archives. *Verificação:* os 3
respondem 200 e `check-agent-surface-live` passa.

**BUG-016 · Falso verde: o gate de disco aprova o que a produção reprova**
`./tools/check-agent-skills-discovery` → **exit 0** ("pass") com os 3 bundles
404 no ar, porque confere o manifesto contra `content/`.
`./tools/check-agent-surface-live` → **exit 1**, "10 de 13 conferem — divergem:
['conversar-com-o-agente-a2a','obter-credencial-de-agente','usar-o-servidor-mcp']".
O gate que enxerga a verdade **não está no gatilho da onda diária**.
*Correção:* o gate de disco passa a exigir o artefato publicado, **e** o gate de
produção entra no gatilho. Esta é uma **família**, não um caso: procurar todo
par "gate de disco verde × gate de produção vermelho".

**FAMÍLIA-A · `public/sitemaps/` é lido do disco por 20 consumidores — e o
diretório tem 58 `.br` além dos 62 `.xml`**
Esta não é uma correção pontual: é a **causa comum** de BUG-013, BUG-014 e
BUG-039. `ls public/sitemaps/ | sed 's/.*\.//' | sort | uniq -c` → `58 br`,
`62 xml`. `grep -rln "public/sitemaps"` → **20 consumidores** em `tools/`,
`cmd/` e `internal/`. Duas classes de defeito:
- **Classe A — lista sem filtrar extensão** → estoura no primeiro `.br`
  (`tools/check-internal-link-floor:62` faz `os.listdir` + `open(encoding="utf-8")`).
- **Classe B — filtra `*.xml` mas usa o disco (62) em vez do índice (34)** →
  universo inflado em 81,6% (`tools/warm-edge-cache:49`,
  `tools/check-edge-cache-coverage:78`).
*Correção sistêmica:* uma função única "universo público" que **deriva do
`public/sitemap.xml`**, adotada pelos 20 consumidores, com teste que planta um
`.br` e um shard órfão no diretório e prova que o universo não muda. O contrato
manda atacar a família, não o caso.

### P1 — grave

**BUG-039 · `./tools/check-internal-link-floor` está QUEBRADO, não reprovando**
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1 in position 0` em
`tools/check-internal-link-floor:63`. O gate do **piso de links internos** — SEO
puro — não mede nada há tempo indeterminado, e devolve exit 1, que qualquer
runner lê como "reprovou por conteúdo". Membro da Classe A da FAMÍLIA-A.

**BUG-040 · P2 · 1.707 páginas publicadas só têm link de hub, sem spokes**
`./tools/check-v2-internal-link-graph` (exit 0): `content_pages=10111
area_hubs=32 pages_with_area_hub=10111 pages_with_spokes=8404
pages_hub_only=1707`. O gate passa verde porque o piso é o hub; 16,9% do acervo
tem malha interna mínima, que é o pior sinal de autoridade que se pode dar.

**BUG-041 · Os dois defeitos de conteúdo que derrubam a onda diária, medidos**
`check-frescor-canal-diario` (exit 1): *coleta OK, publicação não avançou* —
`diarios` máx. publicado 26/08 vs coletado 28/08 (gap 3 d > 1 d);
`noticias` publicado 27/08 vs coletado 28/08 (gap 2 d). O coletor roda, o
publicador não.
`check-derived-authorial-floor` (exit 1): (a) `/jurisprudencia/stf-re-1037396/`
com **74,6% de texto oficial citado** (corpo 2.050 palavras, citado 1.530, maior
bloco 1.443) contra o teto de 70% da DEC-032; (b) **3 pares acima de 0,70** de
similaridade em `stj-tema-derivado` (0,7572 / 0,7563 / 0,7042) — molde repetido
com número trocado. O próprio gate prescreve: correção **no gerador**
(`cmd/generate-stj-tema-pages` etc.), nunca no JSONL à mão, nunca baixando o
limiar.

**BUG-017 · A onda diária termina "success" com o pipeline quebrado**
`daily-content` de 28/08 registrou `ONDA DIÁRIA PARCIAL — falhou em:
check-frescor-canal-diario check-derived-authorial-floor check-lastmod-causalidade`
e as etapas seguintes **não rodaram**; a unit terminou `Result=success` por
desenho. Medido por mim agora: `check-frescor-canal-diario` **exit 1** ("2
canais estagnados além da tolerância") e `check-derived-authorial-floor`
**exit 1**; `check-lastmod-causalidade` já passa (**exit 0**) — corrigido desde
então. *Correção:* os dois defeitos de conteúdo + o systemd deixar de reportar
verde sobre pipeline parcial.

**BUG-018 · Alerta crítico falso-aberto há 37 h, por falta de reconciliador**
`borda-origem` (severidade crítica, "/healthz devolveu 503") segue aberta com a
condição comprovadamente resolvida: `/healthz` = 200 na borda e na origem,
`edge_live` 6× `ok:true`, `portal_health` `"problems": []`,
`tunnel_health_state` `degradado: false`. A chave só fecha por
`tools/notify-owner --resolvido` **manual**. *Correção:* reconciliador que fecha
por evidência da série viva, com registro de quem fechou e por quê.

**BUG-019 · `./tools/check-http-smoke` estoura 90 s**
Medido: exit 124 no timeout de 90 s enquanto `contrato-vs-medicao`,
`arquitetura-fiel`, `v2-portfolio-pairing`, `portal-health`, `public-sem-lixo` e
`paridade-go-nginx` passam em segundos. Última linha antes de morrer:
`run-check: built cached check binary bin=/opt/wiki/.cache/check-bin/check`.
Lentidão é bug — **proibido "corrigir" aumentando o timeout**.

**BUG-020 · `check-untracked-product-inventory` reprova: produto untracked**
`exit 1` — `untracked_produto=70 untracked_produto_stale=4 max_age_hours=24`.
Entre os untracked: `data/research/daily/*/2026-08-28.jsonl` (pesquisa do dia),
`data/ops/access/access-2026-08-{28,29}.jsonl`, receipts de ingest, e backups
`.pre-*` de config de produção que são **única cópia**. O contrato manda
commitar por pathspec ou classificar como efêmero — **nunca deletar**.

**BUG-021 · BUG-004 continua aberto e a superfície cresceu**
Medido hoje em `internal/checks/checks.go`: `Names` tem **322** gates; só **68**
alcançam caminho ctx-aware (26 no switch `runWithContext:1346-1414`, 16 no
`contextCheckRegistry:1421-1451`, 26 pelo ramo P0), e desses apenas **42**
consomem artefato cacheado. **254 de 322 (78,9%) caem em `run()` sem cache.**
O BUGLOG registra "~276 de 294" e "checks.go (10.277 linhas)" — números de
julho; hoje o arquivo tem 12.254 linhas. Pior: `run_context_parallel.go:118`
chama `setFrozen(true)` antes das 6 goroutines, então na fase paralela
(264 gates `parallel_safe`) o cache **computa e não grava** — só os 17
artefatos do `prewarmParallelSharedState:167-188` são HIT.

**BUG-022 · Gate registrado em `run()` mas fora de `Names` — nunca executado**
`case "bigcache-byte-cache-evidence"` existe em `run()` e **não** está em
`Names` nem no `check_performance_ledger.jsonl`, logo `RunAll` nunca o roda —
apesar de existirem `tools/check-bigcache-byte-cache-evidence`,
`cmd/generate/gen_b_bigcache_byte_cache_evidence.go` e referências de cobertura
em `internal/ossscaleintegration/coverage.go:1607,1613`.

**BUG-023 · 10 `tools/check-*` escrevem em disco — violação do contrato**
`CLAUDE.md:208-209` diz que `check-*` é read-only. Medido: `check-crawler-error-budget:315`
e `check-edge-traffic:713` fazem append em `data/ops/`; `check-network-health:152-159`
faz `os.replace` de estado; **`check-invalidated-layer-recovery:132` faz
`os.rename` na árvore de trabalho** (o mais grave); mais 6 que escrevem sob flag.

**BUG-024 · `internal/lexml/parse.go:224-243` descarta erro em data de norma**
Seis `strconv` com `, _ :=` em dia/mês/ano: data de vigência de lei federal vira
`0` em silêncio. Mesma classe em `cmd/collect-stf-informativo/main.go:444` e
`cmd/collect-stj-precedentes/main.go:257` (`_ = json.Unmarshal` — JSON corrompido
vira struct zerada sem ninguém saber).

**BUG-025 · `panic` em pipeline que alimenta três gates**
`internal/quality/quality.go:600` faz `panic` apoiado num comentário que afirma
que a função é pura. `quality` alimenta `no-duplicate-content`,
`mechanical-content` e `canonicals` — os três ctx-aware, logo rodam na região
onde `run_context_parallel.go:140` (`runCheckRecovered`) **converte panic em
"gate reprovou"**. Falha de código fica indistinguível de achado de conteúdo.

**BUG-026 · 114 testes ficam verdes quando o corpus vivo está ausente**
De 291 `t.Skip`, 114 pulam por dado ausente (ex.: `internal/textotruncado/textotruncado_test.go:114`
"estoque v2 ausente neste checkout", `internal/crawl/crawl_test.go:607`
`public/robots.txt` não gerado). Verde silencioso é pior que vermelho.

### P2 — médio

**BUG-027 · Documentação que mente (R1 é explícita: isso é bug)**
`docs/goal/BUGLOG.md:47` marca **BUG-005 como "aberto"** ("CTA aponta para
página inexistente") — medido: `/contato/advogado/` existe e responde **200**.
`CLAUDE.md:154,156` declara 10.107 páginas; medido **10.111**
(`time_to_first_crawl_daily.jsonl` também carrega `rotas_publicadas: 10107`).

**BUG-028 · 28 shards de sitemap órfãos servidos com 200**
62 arquivos em `public/sitemaps/`, 34 no índice. Estão em carência legítima
(mtime 28/08, `check-sitemap-shard-grace` exit 0 os reconhece) — **não é o
defeito**; o defeito é o consumidor lendo o disco (BUG-013). Mas falta série
periódica medindo "disco × índice": `sitemap_shard_grace.jsonl` tem **1 linha**,
de 28/08 20:39, obsoleta 45 min depois.

**BUG-029 · Taxa de 304 na borda é 0,02% e ninguém a mede por bot**
Com `etag off` (`ops/nginx/standalone/nginx.conf:703`) a revalidação depende só
de `Last-Modified`. Em 7 dias: 55.256 requisições de bot, **9 respostas 304**.
O log já instrumenta `inm=`/`ims=` e **nenhum consumidor agrega**. HIT de borda
18,3% ⇒ cada MISS transfere ~28 KB inteiros.

**BUG-030 · Bots recebendo erro sem nenhum alerta**
`facebookexternalhit` 1.291× 404 (28% do tráfego dele);
`cloudflare-agentreadiness` 396× 404; `amazonbot` 356× 404, 18× 503 e
**9.343× 301** (45% do tráfego dele gasto em redirect). `crawler_error_budget`
reporta `errors_total: 0` porque só conta bot verificado — o dado existe na
borda e ninguém o lê.

**BUG-031 · Queda de revisita de −99% em cinco bots**
`claudebot` 43.065 (07/08) → `[25,34,3]`; `gptbot` 16.456 → `[1,1,136]`;
`meta-externalagent` 10.606 → `[6281,128,0]`; `yandexbot` −99,4%;
`googlebot` 4.297 → `[19,88,7]`. Cobertura acumulada segue 99,7% — **o acervo
foi rastreado; o que caiu foi a revisita**. Pela R6, isso é defeito de
engenharia até prova medida em contrário.

**BUG-032 · Config morta que parece viva (armadilha ativa)**
`ops/nginx/wikijuridica.conf` (78 KB) diverge da config viva em 413 linhas e se
auto-declara `# ═══ NAO-CARREGADO-EM-PRODUCAO ═══`. Idem
`ops/nginx/standalone/server.conf` e `bot-policy.conf` — nenhum `include` os
alcança. Editar o arquivo errado regride produção.

**BUG-033 · `internal/agentsurface` e `internal/pageinline` sem nenhum teste**
São, respectivamente, a fonte única das rotas de máquina e a constante do
**único script inline** cujo hash a CSP autoriza. Um byte errado ali mata o
analytics em 10 mil páginas em silêncio. 278 de 760 pacotes (36,6%) não têm
teste — estes dois são os que mais doem.

**BUG-034 · 169 `Lock()` sem `defer Unlock()` adjacente**
Candidatos concentrados em `internal/v2ingest/`, `internal/sitemapstream/`,
`internal/batchdrafts/`, `internal/search/manager.go`. Não é veredito: é a lista
que `go vet -copylocks` + leitura de caminho de retorno tem de triar.

### Conteúdo editorial e dados — medido sobre as 10.111 páginas no ar

**BUG-042 · P0 · 103 rotas servem PT-BR sem acento em texto VISÍVEL**
180 ocorrências em `official_sources[].name` / `.anchor_claim`, que o
`internal/render` imprime no bloco de fontes. **Confirmei no HTML servido:**
`grep 'Codigo de Defesa do Consumidor' public/leis/cdc-art-22/index.html` casa
**2×**. Outras: *"Convencao da Apostila da Haia"*, *"regulamentos tecnicos e
programas de certificacao"*, *"impoe boa-fe e lealdade também na execucao"*
(o "também" acentuado ao lado de quatro palavras sem acento denuncia texto de
duas procedências). Palavras mais frequentes: `nao`(39), `servico`(12),
`contribuicao`(11), `remuneracao`(10). O `PROJECT_GAPS.md:42` já previa este
gate ("acento em `official_sources[].name` — `render.go:180`") e ele **nunca foi
construído**. Falha P0 do contrato de conteúdo.

**BUG-055 · P1 · Tipografia PT-BR quebrada em 47 rotas servidas** — achado meu
ao dimensionar o BUG-042, medindo o **HTML servido**: 45 rotas trazem
*"Decreto-Lei **no** 2.848/1940"* (falta o `nº`) e 3 trazem *"art. **4o**"*
(falta o `º`). Aparece no bloco "Proveniência", visível ao visitante. Minha
varredura independente do HTML servido, com lista restrita de palavras, achou
**57 rotas / 73 ocorrências** de falta de acento — recorte menor que as 103 do
estoque, e por isso os dois números convivem: um mede o dado, o outro mede o
que o leitor vê. **A correção é no gerador da camada de fonte, e fecha os dois.**

**BUG-043 · P0 · 19 colisões de `intent_id` no estoque, cada uma com uma cópia
VAZIA** — confirmado por medição própria (`uniq -d` → 19). Em cada par, uma
cópia completa (600–820 palavras, 3–5 fontes) e uma totalmente vazia
(`opening:""`, `sections:[]`, `faq:[]`, `word_count:null`). Hoje o ar está
correto (19/19 renderizam a cópia boa, verificado no HTML), **mas o que impede
19 rotas de virarem páginas vazias é a ordenação de shard** — e em 2 casos
(`codex-educacao-portfolio-aereo-r03`) a vazia ordena **antes**. Nenhum gate
detecta: `critical_reasons` só conhece `intencao_pulada_deliberadamente`, nunca
`sem_corpo` nem `rota_colidente`.

**BUG-044 · P0 · 136 páginas acima do limiar anti-template, e o gate nunca
rodou sobre elas** — medição própria de Jaccard 3-grama/5-grama em 103.873
pares intra-família: **363 pares ≥ 0,70 (3g)** e **62 ≥ 0,70 (5g)**, pico
**0,8767 / 0,8172** (`dia-pr-20260825` × `dia-pr-20260821`). Pior que o caso
documentado no CLAUDE.md (0,775 / 0,696). Todas em
`lane: derivada_de_fonte_oficial` (`diarios-municipais`, `stj-tema-derivado`,
`stj-sumula-derivada`), e **nenhuma carrega motivo de similaridade** no ledger
de severidade — o universo B "não tem varredura de risco" por definição do
gerador. Correção **no gerador** de cada canal, nunca baixando o limiar.

**BUG-045 · P0 · O auditor de similaridade global é vazio por construção**
`authorial_mass_global_similarity_audit.jsonl`: `expected_pairs: 31.668.861`,
`compared_pairs: 123` (**0,0004%**), `global_all_pairs_compared: false`,
`max_similarity: 0`. E aponta para a camada **antiga** (`authorial_mass_drafts`),
não para `data/editorial/v2_pages/`. É exatamente isso que os **5.600**
registros com `batch_global_similarity_refutado_por_medicao` significam.

**BUG-046 · P0 · O corpus de conferência legal erra nos dois sentidos e se
declara confiável** — confirmei: `data/legal-corpus/clt.json` **não tem os arts.
189 e 195** (que existem na CLT), tem 1.012 artigos, e traz
`"confiavel_para_acusar_divergencia": true`. `cpc.json` tem chaves até o **art.
2027** (o CPC termina no 1.072). Consequência medida: das 13 "atribuições
inexistentes" encontradas, **11 são lacunas do corpus** e 2 são falso-positivo
de regex — **zero erros reais de atribuição em 9.741 citações verificadas**. Ou
seja: o instrumento que deveria proteger a classe P1 permanente hoje só produz
falso positivo.

**BUG-047 · P1 · `data/ops/refinement_queue.jsonl` é fila sem consumidor, com
produtor não idempotente** — `grep -rn refinement_queue` devolve **uma única
referência em todo o repo**, e é a de escrita (`tools/run-daily-content:603`).
A linha de 2026-08-26 aparece **4× idêntica** porque o produtor faz `open(…,"a")`
sempre que o log **do dia** contém "achado MÉDIO". 259 achados de
`source_url_not_official_nor_registered` enfileirados em 28/08 que ninguém lê.

**BUG-048 · P1 · `word_count` declarado diverge do real em 8.358 de 10.130**
Tokenizador divergente (p50 = 3 palavras, máx. 96), concentrado em
`trabalhista-w3-07` e `trabalhista-36`. Não é fabricação — mas o efeito é real:
**52 páginas estão do lado errado do limiar 250–400** que decide severidade
média (1.429 pela medição × 1.377 pelo campo).

**BUG-049 · P1 · Zero páginas têm o tripé fonte = URL + data + hash**
`official_sources` em `v2_pages` **não tem campo de hash de conteúdo**. Os
`sha256` em `v2_source_provenance.jsonl` são de registro/shard, com
`"verification_scope": "upstream_metadata_only_not_network_rechecked_by_ingest"`
e `ingest_live_recheck_performed: false`. Verificação de fonte hoje é
propagação de metadado, não fato de rede. Somando: **135 fontes sem
`verified_at`** (69 páginas), **648 com status ≠ 200** (520 páginas), **748
páginas com URL de fonte em `.jsp/.asp/.aspx`**, 159 em `temas_repetitivos`,
131 em `portal.stf …asp?` — exatamente o gate que `PROJECT_GAPS.md:36` pedia.

**BUG-050 · P1 · Zero `publication_allowed: true` em 10.230 registros do
estoque, com 10.111 rotas `index` no ar** — confirmado por contagem própria.
`public_path` vazio ou ausente em 10.230/10.230. Os campos de gate do estoque
canônico são **decorativos**: a autorização real vive só no manifesto. Ou o
publicador não os consulta (e então são teatro), ou consulta e há um caminho de
bypass — nos dois casos é defeito de contrato a fechar.

**BUG-051 · P2 · Três ledgers discordam sobre a mesma partição**
crítico **100** (`v2_publication_severity.jsonl`, vivo) × **119**
(`data/ops/v2_publication_severity_summary.json`, estagnado em 06/08) ×
universo B **2.377 / 2.390 / 1.763** (o terceiro na docstring do gerador). O
summary defasado em 22 dias é o artefato legível por humano.

**BUG-052 · P2 · 9.385 páginas publicadas (92,8%) carregam erro médio pendente**
`fonte_insuficiente` 1.378 · `corpo_entre_250_e_400_palavras` 1.372 ·
`reprovada_por_agente_sem_justificativa` 131 · `sem_fonte_oficial` 100 ·
`blocker_pipeline` 2.359 · `batch_global_similarity_refutado_por_medicao` 5.600.
Publicar e refinar é a ordem do dono — mas **a fila de refino é a que não tem
consumidor** (BUG-047). A dívida está contabilizada e parada.

**BUG-053 · P1 · 7 produtos untracked (~75 MB), um deles citado por sha em
arquivo versionado** — `data/ops/access/access-2026-08-{28,29}.jsonl`,
`data/research/daily/{diarios-municipais,normas-federais,noticias-oficiais}/2026-08-28.jsonl`
e dois recibos em `data/ops/v2_ingest_terminal_receipts/`. Todos têm irmãos
rastreados. **`stock_manifest.json` (versionado) referencia
`transaction=v2-rewrite-v5-9cf36d95…`, cujo recibo não está no repositório** —
o manifesto aponta para uma prova ausente.

**BUG-054 · P2 · ~585 MB de ruído sem regra no `.gitignore`**
`.agents/runtime/pages.json.antes-*` e `.pre-*` (73 MB cada),
`tmp_rescue/20260828/` (439 MB), backups de config de produção. O `.gitignore`
tem 312+ linhas e **não cobre o padrão `.pre-*` / `.antes-*`**, que é a
convenção mais usada do próprio projeto. Classificar — nunca deletar: alguns são
**única cópia** de config de produção.

### P3 — warning / higiene *(o dono pediu explicitamente até este nível)*

**BUG-035 · 1,34 GB de binários de build soltos na raiz do repositório**
63 executáveis ELF em `/opt/wiki/` (`check` com 241 MB, `checks.test` com
178 MB, `promote-authorial-mass-public-release` com 57 MB…). Todos gitignored
**exceto `seed-sitemap-registry`** (8,8 MB, untracked e não ignorado). Sintoma
de `go build` sem `-o`: o binário cai no cwd.

**BUG-036 · Arquivos de 0 byte com nome de módulo Python na raiz**
`./shutil`, `./os`, `./time`, `./re`, `./8`, `./9` — resíduo de redirecionamento
de shell mal formado (`2>9`, `> os`). Classificar e limpar com registro.

**BUG-037 · 65 `tools/_tmp_fix_*.py` untracked**
Zero rastreados. São correções pontuais de páginas de imobiliário/consumidor/
previdenciário. O contrato proíbe deletar: classificar (produto → commit,
efêmero → `.gitignore` com o porquê).

**BUG-038 · `.claude/settings.json` com 53 linhas removidas, não commitado**
O bloco `enabledPlugins` inteiro sumiu do arquivo. Apurar a origem **antes** de
qualquer commit — pode ser mudança deliberada do dono ou perda acidental.

### Onda 1 — segurança, ferramental, escala, GEO e observabilidade
*(15 agentes; cada achado já passou por um verificador que tentou derrubá-lo)*

#### P0 crítico

**BUG-056 · CVE VIVA no `go.mod` raiz, vermelha e invisível desde 28/07**
`osv-scanner` acusa **GO-2026-5932 em `golang.org/x/crypto v0.55.0`**
(confirmei: `go.mod:103`, `// indirect`). O gate `sca-osv-scan` está `fail`
desde 2026-07-28 e **ninguém o executa**. *Correção:* subir a versão corrigida,
`go mod tidy`, re-rodar o gate — commit Go, serializado com `flock`.

**BUG-057 · `go vet` não roda em lugar nenhum — o runner existe e está quebrado
pela armadilha que o próprio CLAUDE.md documenta**
`tools/go-build-check:46` faz `"$GO" vet ./...` — e `./...` **não expande** neste
repo (confirmei lendo a linha). O vet aborta em `var/nginx` e o gate nunca
type-checa nada. *Correção:* `./internal/... ./cmd/...` (medido pelo verificador:
481 pacotes, exit 0) + gate `go-vet-closure` novo. **Zero `-race` em todo o
repo** — o `grep -rln -- '-race'` só acha wrappers e um comentário
`# Hardlink-or-lose-the-race`.

**BUG-058 · Duas ferramentas destrutivas estão ARMADAS — a tag `devcmds` não é
guarda, e a pior já rodou de verdade**
`./tools/go-modern list -tags devcmds ./cmd/close-unsafe-public-surface` → `main`
(exit 0); sem a tag → "build constraints exclude all Go files". E
`tools/go-modern:108-109` **injeta `-tags devcmds` em todo `run`**;
`tools/run-go-cmd-cached:3561` também. Ou seja: `close-unsafe-public-surface`
(injeta `noindex` em massa e reescreve sitemaps) e `quarantine-public-mass-surface`
estão a um comando de distância. *Correção:* guarda **positiva** no `main` das
duas (conferir volume publicado antes de agir), não nos wrappers.

**BUG-059 · A borda está 100% fria e um piscar do túnel derruba o acervo em 530**
Quatro amostragens consecutivas com cobertura 0,0% e `{'MISS': 40}`. É o efeito
composto de BUG-013 + FAMÍLIA-A.

#### P1 grave

**BUG-060 · `check-edge-live` tem o ramo de resolução INALCANÇÁVEL por
construção** — a linha 208 **grava** o evento no `edge_live.jsonl` e só a 211
chama `ler_estado_anterior()`, que lê a **última linha do mesmo arquivo**: o
"anterior" é sempre o evento recém-gravado. Resultado histórico: **63 alertas, 0
resoluções**. É a causa-raiz do BUG-018 (alerta crítico falso-aberto).
*Correção:* mover a leitura para antes da gravação — ordem que
`check-portal-health:225/248` já usa certo.

**BUG-061 · `check-contrato-vs-medicao` tem folga de 505 páginas, e o CLAUDE.md
descreve o gate ao contrário** — `folga = max(200, publicadas * 0,05)`. Ele
imprime "declara 10107 / mede 10111" e conclui **OK**. Só reprovaria acima de
~10.612. O CLAUDE.md afirma que o gate "reprova o commit se esta linha divergir".
*Correção:* igualdade exata (o manifesto é lido no mesmo instante — não há ruído
estatístico a absorver) ou a folga aparece na frase impressa.

**BUG-062 · `internal-link-mesh-integrity` está VERMELHO em produção**
`exit=1`, 25,3 s, 419 MB de RSS: **28 âncoras da malha mentem o título do
destino** (a malha foi gerada sobre um estoque com 22 dias de defasagem).
*Correção:* regenerar a malha sobre o estoque corrente e reconferir.

**BUG-063 · O acervo perde 304 a cada publicação — causa-raiz isolada em
`internal/build/build.go:311`** — `Last-Modified` do acervo é o **mtime da
escrita**: `find public -name index.html -printf '%TY-%Tm-%Td %TH\n' | sort |
uniq -c` → **10.339 arquivos numa única janela** (28/08 21h), enquanto só 407
rotas tiveram revisão de conteúdo medida. Sem ETag (`etag off`), não há segunda
alavanca. *Correção:* **escrita idempotente** em `build.go:311`, `:344`, `:425` —
ler o alvo, `bytes.Equal`, só gravar se diferir. Não retrodata nada, não muda
HTML, não dispara `--ressemear`. **Esta é a explicação mecânica mais provável do
BUG-031** (queda de revisita de −99%).

**BUG-064 · 28 shards em carência anunciam `lastmod` PRÉ-ressemear que
contradiz o índice vivo em 8.383 URLs — e o GPTBot está consumindo**
A carência é legítima e **não se apaga**; o defeito são as **datas**.
*Correção:* quando `build.go:425` regrava shard aposentado, derivar o `<lastmod>`
do plano vivo.

**BUG-065 · O canal Markdown ficou 42 minutos fora do ar dentro da janela de
deploy** — 855 respostas **502**, todas ao próprio aquecedor
(`wikijuridica-cache-warm/1.0`), em 21:59/22:00/22:07. O Go ficou parado de
21:59:38 a 22:41:26. *Correção:* serializar em `tools/deploy-publico` — reiniciar
o Go **antes** de aquecer, com espera ativa em `/readyz`.

**BUG-066 · Zero timers e zero hooks de qualidade**
23 timers systemd; **nenhum** invoca gate de qualidade. O único arquivo que
menciona `cmd/check` o faz **num comentário**. *Correção:* uma unit
`wikijuridica-qualidade-diaria` com `nice -19`, `ionice -c3` e `flock`.

**BUG-067 · DEZ gates vermelhos agora, cada um por evidência congelada**
Reproduzidos ao vivo: `sca-staticcheck` (exit 1, 416 s, 7 achados, vermelho há
32 dias), `sca-gosec` (32 dias, G404 real e vivo no HNSW), `sca-osv-scan`,
`sca-sbom`, `sca-toolchain-freshness`, `http-load-vegeta-evidence`,
`muffet-local-crawl`, `html-nu-validation`, `htmltest-release-evidence`,
`zizmor-workflow-security` — e **a mensagem do zizmor mente sobre a própria
causa** (`files=2 want=2`). `python-quality-sca` cobre **10 de 228** arquivos
Python. `shell-script-quality` termina em 238 s com exit 1 (o `shfmt` **nem está
no PATH**). *Correção:* uma resolução por gate — e para 3 achados do staticcheck
a correção óbvia **quebraria** `TestValidateDoesNotFanOutToDedicatedHeavyValidators`.

**BUG-068 · `muffet` e `htmltest` auditaram um espelho de 363 URLs — as 10.340
páginas do acervo NUNCA passaram por link-check**
`target_base_url: http://127.0.0.1:23103`, `crawled_local_url_count: 363`,
`content_pages_touched: False`, evidência de 2026-06-28. *Correção:* apontar
para o `public/` servido em `127.0.0.1:8088`, com amostragem estratificada.

**BUG-069 · Três gates ficam VERDES por ausência de dado** *(anti-fraude com
porta dos fundos)* — `check-served-vs-manifest` aprova com manifesto **vazio**
(ausente reprova, vazio passa: assimetria confirmada em `:203-209`);
`check-owner-alerts-abertos` retorna 0 se o ledger **não existe** — apagar o
arquivo silencia todo o canal de alerta; `check-access-log-bots` retorna 0 se o
log some, com a hipótese "o site pode não ter recebido tráfego ainda", que
deixou de ser possível. *Correção:* nos três, ausência é **anomalia** → `exit 2`
com mensagem que descreve o defeito.

**BUG-070 · O log de origem é 97,2% ferramenta interna — todo denominador de
rastreio está contaminado** — `linhas=13362 ferramenta_interna=12987`
(=97,2%; 74% são 304). Nenhum consumidor grava o denominador líquido.
*Correção:* todo consumidor imprime o par (bruto, líquido) com o critério de
desconto na própria linha.

**BUG-071 · `maxSitePagesBytes = 128 MiB` já está a 56,95% e morde em ~17.772
páginas** — `content/pages.json` tem 76.434.768 B / 10.121 registros (7.552 B por
registro). O caminho legado está **ativo hoje**, e o desenho de saída
(`publicReleaseContentStoreThresholdPages = 2000`) existe em código e **nunca foi
materializado**.

**BUG-072 · A origem não autentica 49,3% do tráfego de bot** — 15 dos 33 tokens
do `robots.txt` têm faixa de IP verificável; **3 das 4 fontes faltantes já usam o
schema que o coletor entende** (correção barata: 4 entradas em
`DefaultBotIPRangeSources`, `internal/crawl/crawl.go:530+`).

#### P2 médio

**BUG-073 · A cobertura de borda mede um universo 81% inflado, e a docstring
afirma o contrário** — e o alerta derivado tem amostra de **0,21%** (40 de
18.726) com IC95 de 0 a 8,76%. *Correção (refinada pelo verificador):* **manter**
`--amostra 40` (a razão documentada é correta) e trocar a **fonte**: derivar
`(hit + revalidated) / urls` do `edge_cache_warm.jsonl`, que já é censo completo
e custa zero.

**BUG-074 · `check-edge-cache-coverage-honesty` está vermelho com 8 problemas e
nenhum timer o executa** — o gate que vigia a auto-medição acusa que "a segunda
medição caiu sobre o rastro que a primeira acabou de aquecer, a mesma causa-raiz
do 100% falso de 2026-08-19".

**BUG-075 · 20 `tools/check-*` escrevem e 32 têm padrão de mutação** *(o número
60 do primeiro agente não se reproduziu; a contagem rigorosa é esta)* — o pior:
`check-brotli-e-recomprimir:44-46` **invoca o gerador e reescreve as gêmeas `.br`
do acervo servido**, de hora em hora, por timer; `check-network-health` chega a
dar `sudo systemctl restart`. *Correção:* separar por papel sem perder o
comportamento operacional (o miolo vira `check-*` puro; a ação vira `repair-*`).

**BUG-076 · 4 séries vivas sem consumidor** *(não 6 — duas foram refutadas: o
filtro do primeiro agente excluía onde os consumidores moram)*:
`time_to_first_crawl_daily`, `bing_webmaster_daily`, `clarity_insights_daily`,
`edge_bot_status_daily`.

**BUG-077 · 77 arquivos em `data/ops` (11,1 MB) sem uma única referência em
código** — maior: `v2_corpus_coverage_map_20260721.jsonl` (2,4 MB).
*Correção:* **movimentação, nunca descarte** — `data/ops/arquivo/AAAA-MM/` com
`INDICE.md` dizendo o que cada campanha mediu e qual decisão sustentou.

**BUG-078 · 13 binários ELF RASTREADOS no git, ~448 MB** — confirmei:
`data/ops/rollback-20260806/wikijuridica-server` (31 MB, versionado, **não**
ignorado), `.agents/runtime/binarios-aposentados/20260826/*` (53 MB + 51 MB),
3× `wikijuridica-server.rollback-*` (36 MB cada). *Correção:* o `RESTORE.md`
passa a reconstruir a partir de commit fixado, com o SHA do commit no
`SHA256SUMS`.

**BUG-079 · A CSP concede `style-src 'unsafe-inline'`** — o hash fecha o
`script-src`, mas o CSS crítico inline continua aberto. *Correção:* 12 hashes
derivados das **constantes Go** de `internal/render` (nunca raspando `public/`,
que cristalizaria página velha). **Não dispara `--ressemear`** (é header).

**BUG-080 · `open_file_cache_valid 5s` é diretiva MORTA** — `nginx -T` mostra a
linha sem nenhum `open_file_cache` declarado; o default é `off`, e 15 linhas de
comentário descrevem uma revalidação que não existe.

**BUG-081 · Quatro comentários de código que mentem** *(R1: comentário que mente
é bug)* — `nginx.conf:98` afirma que o ETag sobrevive (desligado 15 dias depois);
`internal/crawl/crawl.go:137-143` diz que o canal Content-Signal está FECHADO e
que há gate exigindo isso, quando **o gate exige o contrário** hoje;
`internal/v2ingest/v2ingest.go:38-57` descreve um merger materializado em memória
que **já é streaming desde 2026-07-28** (o comentário nasceu obsoleto no mesmo
commit); `internal/content/content.go:441` é impreciso (vale para as rotas do Go,
não para o acervo estático).

**BUG-082 · Decisão × produção divergem sobre o `llms.txt`** — o repo documenta
"llms.txt NÃO é padrão real / NÃO implementar" em
`docs/goal/cowork/SEO_INDEXACAO_2026_DOSSIE.md:41`, e a produção serve **35
arquivos** (raiz + 33 de área + `llms-full.txt` de 1,4 MB). *Correção:* alinhar
o documento ao medido — **não remover** (custa zero e serve auditoria de agente).

**BUG-083 · Cerimônia de ~2 s por invocação de gate × 322 = minutos de puro
overhead** — e o modo multi-gate que resolveria isso **já existe**: `--checks
a,b,c` com `--timings`. *Correção:* usar, não construir.

**BUG-084 · `internal/agentsurface` não é o inventário que se diz ser** — 11
rotas de máquina vivem fora dele (`/a2a/v1`, `/api.md`, `/auth.md`,
`/changes.json`, `/.well-known/api-catalog`, `/.well-known/mcp/server-card.json`,
metadata OAuth…). *Correção:* corrigir o doc do pacote **e** trazer o metadata
OAuth para o inventário (recorte de segurança real).

#### P3 leve / melhoria — *nenhum descartado*

- **BUG-085** · `datePublished`/`dateModified` sem hora nem fuso em 590/590
  valores; `<lastmod>` só com data (o Bing pede ISO 8601 com hora).
- **BUG-086** · `Article` sem `image` (295/295), sem `wordCount`,
  `articleSection`, `isPartOf`; `about` em 11 de 295. `og:image` existe em 10.339.
- **BUG-087** · `max-image-preview:large` ausente nas 10.339 páginas.
  *(085/086/087 mudam HTML → uma única publicação com `--ressemear` + purga.)*
- **BUG-088** · 10.436 arquivos `.br` expostos como URL própria, servidos
  `application/octet-stream`, por causa da allowlist de extensão em
  `nginx.conf:1249`. Demanda real medida: **2 acessos, ambos da auditoria**.
- **BUG-089** · `/caminho/index.html` e `//caminho/` respondem 200 e duplicam
  cada URL. Demanda real: só sondas e um scanner.
- **BUG-090** · Gêmea `.md` sem `Vary` na origem (a borda emite e serve certo) —
  emitir `Vary: Accept-Encoding` **somente**, nunca `, Accept`.
- **BUG-091** · Zero gêmeas `.gz` (10.436 `.br`, 0 `.gz`) — risco de escala
  refutado; falta o instrumento (`ae=$http_accept_encoding` no `log_format`).
- **BUG-092** · Cinco tetos de `1_000_000` **iguais à meta declarada de
  arquitetura**, sem folga; `maxPortfolioFiles = 4.096` ficou para trás enquanto
  o irmão `maxPageFiles` subiu a 200.000.
- **BUG-093** · Índice de busca custa 11,4 KB/página (118 MB hoje) e `/buscar/` é
  a única rota em dezenas de ms — projeta ~11,4 GB em 1M de páginas.
- **BUG-094** · HSTS sem `preload` — e a submissão **não** é o passo
  irreversível: assim que `preload` entra no header, qualquer pessoa pode
  submeter, e a remoção leva meses.
- **BUG-095** · Registro de bots sem campo de conformidade com robots nem de
  método de verificação; 3 agentes documentados ausentes (`meta-externalads`,
  `Google-CloudVertexBot`, `GoogleOther`); o IETF **aipref** tem milestone de
  31/08/2026 e o repo **não menciona `aipref` em lugar nenhum**.
- **BUG-096** · `deadcode` custa zero (já em `golang.org/x/tools v0.49.0` no
  cache) e `errcheck` quase zero — nenhum dos dois está ligado.
- **BUG-097** · `vale-public-prose-lint-release` está **vermelho com 140 erros**
  de prosa e alimenta o verdict de release. O trabalho é resolver os 140.
- **BUG-098** · `htmltest` e o venv de qualidade Python só existiam em `/tmp` —
  **sumiram**. O precedente certo já está ao lado (`.toolchains/` do LanguageTool
  e do `vnu.jar`).
- **BUG-099** · `PROMPT_GOAL_4K.txt` cita dois tetos já elevados **6×** e
  **12,2×** — quem seguir o doc investiga o limite errado. *(Fica resolvido pela
  reescrita da §12.)*
- **BUG-100** · Nada reprova a introdução de `nosnippet`/`data-nosnippet` no
  corpo de uma página — única lacuna que sobreviveu à medição do snippet.

### Onda 2 — compilação, testes, bateria de gates, docs, HTML servido e citação legal
*(12 agentes; tudo abaixo passou por um verificador que tentou derrubar)*

**O fato de fundo, medido:** o repositório **compila limpo** — `build
./internal/... ./cmd/...` exit 0 em 53 s; com `-tags devcmds`, exit 0 em 5m27
(760 pacotes). Não há exit 0 mentiroso. **O que está quebrado é tudo o que roda
depois do compilador.**

#### P0 crítico

**BUG-101 · `cmd/build public` REPROVA — o portal não regenera seus artefatos**
`./tools/go-modern run ./cmd/build <dir>` → **exit 1**, com **261 achados em 29
rotas**: 259 `source_url_not_official_nor_registered`, 1 `repeated_sentence`,
1 `repeated_phrase`. `build.go:173-181` falha fechado **de propósito** — o
comportamento do gate está certo; o que falta é corrigir a causa. Leva dois
gates junto.

**BUG-102 · A atestação do grafo do validador está quebrada — e o hash se moveu
de novo durante a sessão** — `TestPrepareTransactionPlanSnapshotsModuleIdentityWithProjectReader`
falha: `generated validator attestation does not match authenticated source
graph`. Consequência: **`cmd/ingest-v2-stock` não ingere estoque v2 novo** — a
fábrica de conteúdo está travada na entrada. *Correção:* `go generate
./internal/v2ingest` e commitar, **depois** de commitar as mudanças em Go, senão
quebra na hora.

**BUG-103 · Contraste 1,81:1 no rodapé de 10.339 páginas — WCAG 1.4.3 AA
reprovada em todo o acervo** — `./tools/go-modern run ./cmd/check
accessibility-html` → **exit 1 em 6m20**, `20.650 achados de gravidade ≥
IMPORTANTE em 10.326 documentos`, todos com um único código:
`a11y_text_contrast_below_aa [BLOQUEIA-LANÇAMENTO]` — o link "Privacidade e
cookies" do rodapé não tem regra de cor. **Achado do verificador que o primeiro
agente não viu:** a correção óbvia cria uma reprovação **na folha de impressão**,
que o auditor não enxerga (`internal/accessibilityaudit/css.go:202` pula
`@media print` de propósito). *Correção:* regra base **e** regra em
`baseCSSPrint` (`render.go:2069`), mais `TestPrintPalettePassesWCAGAA` para
fechar o buraco estrutural. **★ MUDA O HTML DE TODAS AS PÁGINAS** — publicação
agrupada + `--ressemear` + purga ampla. *(Uma frente concorrente já corrigiu
parte disso na worktree — verificar o disco antes de editar.)*

**BUG-104 · `googlebot-smoke` valida o próprio cache — falso positivo provado
por experimento controlado** — mesmo binário, mesmo minuto: com cache velho,
**exit 1** (`googlebot_smoke_forbidden`); com cache vazio, **exit 0**. Causa:
`checks.go:6788` usa `filepath.Join(os.TempDir(), "portaljuridico-googlebot-smoke-cache")`
— caminho **fixo** em `/tmp`. *Correção:* `os.MkdirTemp` + `defer os.RemoveAll`.

**BUG-105 · `public-release-transaction` reprova com 59.388 erros — e são DOIS
campos que o produtor nunca escreveu** — `omitted_failures=59188 max_errors=200`.
Classificação das 200 exibidas: só **três** códigos, todos da mesma família
(`public_release_missing_source_type`, `..._use_in_content`, …). **O validador
está certo e o produtor está incompleto**: `source_type` (lei/súmula/tese/órgão)
e `use_in_content` (fundamenta/ilustra/cita) nunca são emitidos.

**BUG-106 · `GOAL.md` — primeiro na cadeia de precedência — declara
`published_manifest=0` e `deficit_to_10000=10000` como "atualização viva que
prevalece sobre qualquer parágrafo histórico"** — `grep -c 'published_manifest=0'
GOAL.md` = **5**. E `check-contrato-vs-medicao` **não olha o GOAL.md**: as
`FRASES_ZERO` e o regex `DECLARACAO` passam batido. Um agente que obedeça à
precedência conclui que o portal não publicou nada.

#### P1 grave

**BUG-107 · `go vet` dá FALSO-VERDE por envenenamento de cache (`VetxOnly`) —
provado empiricamente e no fonte do `cmd/go`** — controle reproduzido 3×, mesmos
arquivos: `vet ./internal/termpromotion/` → exit 0, saída vazia;
`vet -tags vetfrioZZZ ./internal/termpromotion/` (tag que nenhum arquivo declara,
seleção de arquivos **idêntica**, só a chave de cache muda) → **exit 1 com 2
diagnósticos**. Em escala: o comando documentado acha **1** diagnóstico; com
cache frio, **3**. **67% dos diagnósticos reais são suprimidos pelo comando que
qualquer um rodaria.** *Correção:* nunca `go vet` sem cache-buster (`GOCACHE`
dedicado ou tag-nonce) + gate `go-vet` com `scaMemoAround` por hash de fonte
(padrão que já existe em `internal/checks/sca_memo.go`).
*Os 3 diagnósticos reais:* 2× `non-constant format string in fmt.Errorf`
(`internal/termpromotion/termpromotion.go:52,105` — corrompe justamente a
mensagem que diz **qual linha do dado** quebrou) e 1× `unreachable code`
(`internal/v2supersessionintegrity/forward_evidence.go:572`). **Zero
`copylocks`** — a classe "Mutex copiado por valor" **não existe hoje**.

**BUG-108 · Nenhum gate de teste no caminho do commit, e o runner de suíte testa
ZERO pacotes** — `grep -cE '\bgo-modern +test\b|\bgo +test\b' .githooks/pre-commit`
→ **0**; e `tools/check-all:51` usa `go test ./...`, que **não expande**.
*Correção:* `./internal/... ./cmd/...` no `check-all` + passo de teste focado no
pre-commit por caminho tocado.

**BUG-109 · Bateria completa: de 450 `tools/check-*`, 391 medidos → 218 verdes,
157 VERMELHOS, 4 timeouts, 12 erros de execução** *(59 não medidos: heavy,
daemons de janela fixa e os que escrevem — todos nomeados, sem cap silencioso)*.
Este é o mapa que faltava.

**BUG-110 · `check-architecture` inutilizado pelo cache do Chrome do publicador
social** — exit 1 com **586 reprovações**, 200 exibidas e `omitted_failures=386`;
**200 de 200 são `publicador-social`**. Excluir só `.perfil-navegador` e
`Cache_Data` **não resolve** — sobram 10 hits de `node_modules` e 2 de prosa.

**BUG-111 · O ledger de custo mente sobre os dois gates mais caros**
`http-smoke` custa **75 s** e `accessibility-html` **129 s** (medidos), e ambos
estão rotulados `fast / budget 3000 ms / always_run=true` em
`check_performance_ledger.jsonl`. *(Isto explica meu `EXIT=124` no
`check-http-smoke` com timeout de 90 s — não era travamento.)*

**BUG-112 · `scaled_content_release_verdict.jsonl` foi renomeado em 2026-07-09 e
nunca regerado — derruba 11 gates de uma vez** — no disco só existem
`.jsonl.stale-20260709T155727Z` (4,7 MB) e `.jsonl.stale-v1-132157Z` (156 MB).
Não é decisão a devolver ao dono: o produtor existe
(`tools/generate-scaled-content-release-verdict`).

**BUG-113 · `p0-cycle-close-indexable-10k` anuncia déficit fictício de 10.000
páginas** — porque o insumo ausente (BUG-112) faz `count=0` cair no default.
`current_public_indexable_count=0 required=10000 deficit_to_10000=10000` —
enquanto o `http-smoke` do mesmo dia mede `manifest_routes=10116
public_indexable_legal_pages=10116 deficit_to_10000=0`. *Correção:* separar
"não consegui medir" de "medi e deu baixo".

**BUG-114 · `seo` e `sitemaps` reprovam com 289 acusações em 31 páginas, com
DUAS causas-raiz** — 285 em `/diarios/` porque o gerador **cunha um `source_id`
por gazeta** (`anadia-al-di-rio-de-19-08-2026-...`) quando o host **já tem ID
curado** no `content/source_registry.json`; o resto é outra causa.

**BUG-115 · Autolinker publica href e JSON-LD apontando para OUTRO dispositivo —
219 ocorrências em 199 páginas, 219 de 219 erradas** — toda citação de artigo
**com sufixo** (`art. 543-C`, `art. 475-J`, `art. 1.240-A`) é partida pelo
autolinker: o `<a>` fecha antes do sufixo e o `href` aponta para o artigo-base.
*Consequência medida:* **10 páginas** de jurisprudência emitem, na camada de
máquina, uma **URN do CPC/2015 para dispositivo do CPC/1973** (arts. 543-C e
475-J, revogados). *Armadilha registrada:* `grep -rl '543-C' public/` devolve
**0** — o literal não existe no HTML porque o autolinker o parte.

**BUG-116 · `/glossario/qualidade-de-segurado/` cita a Lei 8.213 "art. 24-A",
que não existe — é o art. 27-A** — erro jurídico servido ao público.
*Correção:* gerador datado com lease + CAS, **nunca** editando o shard à mão.

**BUG-117 · `ValidateEditorialBody` — a guarda de ética OAB sobre o corpo
publicado — é CÓDIGO MORTO** — existe, está testada, e **não tem um único
chamador de produção**. O gate de promessa valida os **7.959 registros da esteira
de candidatos**, não as **10.111 páginas publicadas**.

**BUG-118 · Três diplomas do corpus legal contaminados com artigo de OUTRA lei**
`cpc.json` (n=1075, fim denso 1072, suspeito 2027), `lei_12653_2012.json` (n=5,
suspeito 135), `lei_8245_1991.json` (n=93, suspeitos 167 e 169) — cabeçalhos de
artigo colhidos **dentro de bloco de alteração de outra norma**. E
`confiavel_para_acusar_divergencia` mede **atualidade**, não **completude**: 8
diplomas com o flag `True` têm lacuna de numeração.

**BUG-119 · 124 refinamentos pagos órfãos derrubam o carregador canônico do
estoque autoral** — 124 de 2.520 (4,9%), com integridade referencial quebrada e
**commitada** nos ledgers.

**BUG-120 · Migração da variante de URL do Planalto feita pela metade** — o dado
migrou, **51 constantes de produção** em 8 arquivos não, derrubando 27 testes.

**BUG-121 · O digest congelado do shard `aereo-08` divergiu há 25 dias** — a
guarda de imutabilidade está morta desde 2026-08-04, com o commit culpado
identificado.

**BUG-122 · `legal-citation-attribution` acusa 184 páginas** (97 `diploma_sem_fonte`,
66 `sumula_sem_fonte`, 35 `tema_sem_fonte`) — **reenquadrado pelo verificador:**
é defeito real, o vermelho é **proposital**, e a correção é **acrescentar a fonte
que falta, nunca remover a citação**. O autoteste do gate passa 13/13 em
regressão de falso positivo.

**BUG-123 · 12 `tools/check-*` escrevem no repo — além dos 10 já conhecidos**
`grep -ln 'notify-owner' tools/check-*` → 11 arquivos; e
`check-brotli-e-recomprimir` **roda gerador e reescreve as gêmeas `.br` do acervo
servido**, de hora em hora, por timer. O nome já confessa.

**BUG-124 · 24 gates vermelhos por evidência derivada estagnada — e pelo menos
um esconde defeito REAL de conteúdo** — *Correção:* **não** rodar os 24
geradores em lote; um a um, re-executando o gate: quem ficar verde era
bookkeeping, quem ficar vermelho é defeito.

**BUG-125 · O BUGLOG tem status falso em 4 de 12 entradas** — todas na direção
"segura", todas produzindo trabalho fantasma. `BUG-011` (DataJud) é a única cujo
"aberto" resistiu à verificação — e o bloqueio **não é credencial**: a série
existe em `data/research/`.

#### P2 médio

- **BUG-126** · A busca imprime a consulta do visitante com `%q` do Go: `\"`,
  `\t` e `\\` vazam no resumo visível **e na meta description** (8 chamadas).
- **BUG-127** · A página **404 é a única superfície servida sem o script de
  medição** — e a CSP dela **já autoriza o hash**. Tráfego que bate em URL
  inexistente é invisível no GA4 e no Clarity.
- **BUG-128** · `AuditRepository` custa **978 MB de RSS no gate PADRÃO** e o
  teste da vitrine paga **dois** `AuditRepository` a 38,3 s cada — memoizar no
  `RunContext` com o `cachedTypedLoad` que já existe.
- **BUG-129** · A única sonda de corrida sobre `RunAll` está desligada por
  `WIKI_CHECKS_FULL_RACE`, variável que **ninguém define** (4 ocorrências, todas
  no próprio arquivo de teste).
- **BUG-130** · `search.Manager` não tem `Close` — `New()` não expõe encerramento
  e o teste vaza. *(A atribuição ao access log foi **refutada**: em teste o
  logger é `nil` por guarda deliberada.)*
- **BUG-131** · 8 testes stale em 4 pacotes, por mudança deliberada não refletida
  na asserção; 4 perfis de seleção de gate derivaram do ledger validado —
  inclusive o `p0-release`.
- **BUG-132** · `AGENTS.md`, **primeiro na cadeia de precedência**, é integralmente
  endereçado ao **Codex**, desativado por ordem do dono em 2026-07-21 — e
  condiciona o fim do P0 a um déficit que o próprio gate do repo mede em **0**.
  `CHECKPOINT.md` (terceiro na cadeia) congelou há **37 dias** com nota de
  precedência ainda ativa.
- **BUG-133** · O inventário de citações — instrumento do P1 — está **16 dias
  atrás do acervo** e não tem contrato de frescor.
- **BUG-134** · A lista de termos de promessa OAB é fechada em **11 needles** com
  busca contígua, e o acervo já escreve formas fora dela ("aprovação garantida"
  em 10 páginas — todas legítimas, mas a **lacuna de detecção** é real).
- **BUG-135** · `tools/check-go-compile-closure:134` usa `./...` como default —
  o segundo detector cego pela mesma armadilha; e dois gates Python morrem em
  `UnicodeDecodeError` (em lugares diferentes dos que o primeiro agente disse).
- **BUG-136** · `//nolint:govet` é **no-op** para o `go vet` — não silencia nada.
- **BUG-137** · O `repeated_phrase` que trava o build é **falso positivo**: a
  normalização colapsa `n 2 204 santa` / `n 2 205 santa` em 6-gramas idênticos
  (três edições distintas de diário). E o `repeated_sentence` que o primeiro
  agente chamou de "real" **também** é texto oficial citado.
- **BUG-138** · Quatro formas da mesma URL servem 200 sem redirecionar
  (`/rota/`, `//rota/`, `/rota/index.html`, `/rota`), e a premissa que sustenta
  não corrigir **não tem sentinela**.

#### P3 leve / melhoria

- **BUG-139** · O comando de build documentado no CLAUDE.md cobre **481 de 760**
  pacotes; nenhum gate **linka** os 279 dev-mains. O comentário do pre-commit
  fala em "504 pacotes" e subestima o custo real em ~4×.
- **BUG-140** · `run-check` re-deriva o grafo de dependências do Go a cada
  invocação: **3.161 ms** contra **703 ms** do binário direto — 2.458 ms de
  overhead por gate × 322.
- **BUG-141** · `docs/audits/` tem cinco arquivos de 2026-06-28 declarando
  `published_manifest=0`, 62 dias depois; o `PLANO_RASTREIO` lista cinco defeitos
  como "ainda não corrigidos" que **foram corrigidos no mesmo dia**; e o placar
  "check all: 42 pass, 83 fail" cobre **39% do registro** sem dizer isso.
- **BUG-142** · Comentário que mente em `css_contrast_test.go:170-172` — afirma
  que o auditor não alcança media query, e ele alcança desde `darkThemeFindings`.
- **BUG-143** · §4e-bis de `DADOS_CONFIAVEIS` está desatualizada: **existe** canal
  local de enunciado de súmula, cobrindo 23 das 48 do STF citadas — mas prova
  **texto**, não **vigência**.
- **BUG-144** · Um único teste consome **5 minutos** fazendo dois renders
  completos do site — lentidão é bug P0 por contrato.
- **BUG-145** · Os 5 "daemons que nunca retornam" são **sondas de janela fixa**
  (refutado) — o que falta é `expected_duration_ms` real no ledger.

### Lacunas que a crítica adversarial abriu — riscos que o catálogo não cobria

**BUG-146 · P0 · Não existe backup de nenhum dado sole-copy**
`systemctl list-timers | grep -i backup` → só `dpkg-db-backup`, do sistema.
`data/` tem **12 GB** e nenhuma rota de backup. O `BUG-053` já prova o caso
concreto: um manifesto **versionado** aponta por sha para um recibo que não
existe em lugar nenhum. Perda de dado aqui é irreversível e nenhum item do
catálogo a cobria.

**BUG-147 · P1 · Espaço em disco sem gate**
`df -h /opt` → **78% usado**, com ~585 MB de ruído e 448 MB de binários
**rastreados** crescendo. `ls tools/ | grep -iE 'disk|disco'` → nada. Disco cheio
mata a transação de publicação no meio — e a publicação é transacional
justamente para não deixar o portal em estado híbrido.

**BUG-148 · P1 · DNS/DNSSEC sem sonda de saúde**
Existe `check-dns-aid` (descoberta de IA), não saúde de resolução. O precedente
do DS órfão do Registro.br é dependência externa que já quase derrubou o
domínio, e nada a vigia.

**BUG-149 · P1 · Os alertas dispararam e ambos os canais registram "silenciado"**
Na janela dos 502 de 28/08 (BUG-065), `portal-fora` e `portal-degradado`
dispararam — e ficaram silenciados. A lógica de silenciamento de
`tools/notify-owner` precisa ser lida: alerta que não chega é pior que alerta
que não existe, porque cria a sensação de cobertura.

### Correções que NÃO devem ser executadas como escritas

A crítica adversarial apanhou sete propostas cujo remédio faria dano. **Vale a
alternativa, não a proposta original:**

| Item | Por que a proposta original é perigosa | O que fazer |
|---|---|---|
| **BUG-061** (folga de 505) | Igualdade exata **quebraria todo pre-commit** do repo após cada publicação diária — o manifesto foi de 10.111 a 10.116 durante a redação deste plano. Bloquearia frentes concorrentes. | Imprimir a folga na frase (`declara N, mede M, folga F`) e estender o gate ao `GOAL.md` e a `docs/audits/*`. |
| **BUG-077** (77 séries "sem consumidor") | O método ausência-por-grep **já falhou duas vezes** neste plano (as "6 séries" que eram 4; o near-miss do `refinement_queue` vs fila de *signature*). Mover série viva quebra produtor em silêncio. | Provar por padrão de `open()` dinâmico **e** mover em duas fases, observando os timers entre elas. |
| **BUG-054** (`.gitignore` `.pre-*`) | Padrão cego colide com **BUG-020/053**: alguns `.pre-*` são **única cópia** de config de produção, e ignorá-los os esconde do gate de untracked para sempre. | Classificação **item a item**, nunca por padrão. |
| **BUG-078** (13 ELF rastreados) | Se lido como "apagar", perde o único artefato de rollback **byte-exato** (rebuild não garante bytes idênticos) e exigiria reescrever história — proibido. | Correção **aditiva**: SHA do commit no `RESTORE.md` e no `SHA256SUMS`. |
| **BUG-075 / BUG-123** (split `check-*`/`repair-*`) | O timer horário **tem de continuar** chamando o lado que recomprime, senão as gêmeas `.br` apodrecem servindo corpo velho em silêncio. | Separar os papéis **e** repontar a unit para o `repair-*` no mesmo commit. |
| **BUG-069** (ausência → `exit 2`) | Nasce uma classe nova de vermelho falso nas units que declaram `SuccessExitStatus=0 1`. | Coordenar o exit code com as units no mesmo commit. |
| **BUG-103** (contraste) | **Executá-lo agora É o dano**: já está corrigido e no ar; refazer re-publica o acervo inteiro à toa. | Só o residual: criar `TestPrintPalettePassesWCAGAA` (não existe — `grep -rn TestPrintPalette internal/` vazio). |

### Reconciliação de três números que o plano dava em duplicidade

`BUG-023` dizia **10** `check-*` que escrevem; `BUG-075` mediu **20** (com 32 de
padrão de mutação); `BUG-123` disse "**12 além dos 10**". São a mesma família
contada com critérios diferentes. **O número a usar na execução é o medido com
critério declarado — 20 que escrevem — e o primeiro passo da task é republicar a
contagem com o critério junto.** Os três IDs ficam, apontando para a mesma
correção, porque cada um traz um caso concreto que os outros não trazem.

### O trem de publicação — quem embarca no PRÓXIMO deploy de acervo

Todo item abaixo muda o HTML das ~10.339 páginas. **Vão juntos, numa
publicação só**, ou o acervo é re-datado uma vez por item e os bots que
revalidam são rebaixados uma vez por item:

`BUG-085` (datas ISO com fuso) · `BUG-086` (`image`, `wordCount`,
`articleSection`, `isPartOf`) · `BUG-087` (`max-image-preview:large`) ·
`BUG-127` (script de medição na 404) · `BUG-042`/`BUG-055` (acento e tipografia
na camada de fonte) · `BUG-115`/`BUG-116` (autolinker e a citação errada).

**Pré-requisito duro:** `BUG-101` (build verde) — que depende de `BUG-114` (o
`source_id` do `/diarios/`) e `BUG-137` (os dois falsos positivos do detector de
texto, corrigidos **no detector**). E **`BUG-063`** (escrita idempotente em
`build.go:311`) entra **antes** do trem, senão o ciclo seguinte volta a re-datar
tudo e a medição de 304 fica cega mais um ciclo.

### REFUTADOS — investigados e derrubados por medição *(ficam registrados)*

Dado de agente **vale dinheiro e não se descarta** — inclusive o que foi
derrubado. Cada linha aqui evita uma re-investigação futura.

| Suspeita | Por que caiu |
|---|---|
| "229 páginas órfãs no disco" | 186 paginações de hub + 27 hubs + 12 institucionais + home + `50x.html`. `0` rotas do manifesto sem HTML. Coerência de artefato **íntegra**. |
| "225 URLs indexáveis fora da cadeia de publicação" | Têm lastro de SHA-256 em **manifesto paralelo** (`publishedmanifest.go:192-198`). O detector proposto **já existe**, e a correção proposta **reprovaria** o gate. |
| "`edge-traffic.timer` morreu (11 h sem rodar)" | `OnCalendar` é **2×/dia** (03:20 e 15:20). Disparou normal. |
| "`medicao-externa.timer` nunca rodou" | Habilitado **hoje às 03:03**; primeira janela é 06:10. O serviço já rodou com exit 0 e alimentou dois ledgers. Timer novo, não morto. |
| "`alertas-abertos` e `edge-cache-coverage` falham" | As units declaram `SuccessExitStatus=0 1`; exit 1 significa "achei alerta". |
| "`static-freshness`: 62/62 arquivos obsoletos" | Era **verdadeiro às 04:47** e foi resolvido por um deploy às 04:55. Às 05:30, 62/62 batem na origem **e** na borda. |
| "O merger materializa o corpus em memória" | É **streaming desde 2026-07-28**. O agente leu um comentário que nasceu obsoleto **no mesmo commit** que fez o streaming. |
| "`cite-as` (RFC 8574) ausente" | **Já implementado e no ar** — o agente sondou só a superfície HTML; o header sai na gêmea `.md`. |
| "`Disallow: /*?` nos bots de treino é erro" | Decisão **deliberada, medida e comentada** (`crawl.go:706-757`). Erro de categoria do agente. |
| "Bytespider sem fonte oficial é omissão" | O repo **já declara** a ausência; a correção proposta seria **reprovada** pelo validador. |
| "`max-snippet:-1` é convenção frágil" | É **constante única pinada por teste**, exigida por match exato no `htmlcontract` e no smoke. |
| "`headline` diverge do `<h1>` em 9.841 páginas" | **Por desenho** — segue o `<title>`, e `headline` nunca está fora do title. Corrigir custaria bytes em 10.100 páginas por ganho nulo. |
| "`httpserver` vaza a goroutine do access log" | Em teste o logger é **`nil`** por guarda deliberada (`access_log.go:139-141`). Quem não tem `Close` é o `search.Manager` (virou BUG-130). |
| "5 `check-*` são daemons que nunca retornam" | São **sondas de janela fixa** — `check-claude-idle-cpu` sai 0 em 108 s. O exit 137 foi o timeout do próprio auditor. |
| "`sync.Mutex` copiado por valor" | `vet` com cache frio nos 760 pacotes: **zero `copylocks`**. A classe **não existe hoje**. |
| "60 `check-*` escrevem em disco" | Contagem rigorosa: **20 escrevem**, 32 têm padrão de mutação. Os casos concretos citados eram reais. |
| "6 séries vivas sem consumidor" | São **4** — o filtro `grep -vE 'generate-|measure-|collect-'` do agente excluía exatamente onde os consumidores moram neste repo. |
| "O wrapper devolve exit 0 por cima do `./...`" | **Não se reproduziu** em duas medições independentes: `${PIPESTATUS[0]}` = 1. A armadilha do `./...` é real; esta metade da frase do CLAUDE.md, não. |

---

## 12. Prompt `/goal` da próxima sessão — **medido: 3.989 caracteres**

Teto 4.000, **folga de 11** — medido com `wc -m` sobre o texto exato abaixo.
Vai para `docs/goal/PROMPT_GOAL_4K.txt`, substituindo o conteúdo atual, que está
stale em dois eixos: fala de "7.675 páginas v2 / 0 aprovadas" (há 10.116 no ar)
e cita dois tetos já elevados 6× e 12,2× (BUG-099).

**Esta é a segunda versão.** A primeira (3.996 chars) listava como críticos o
BUG-102 e o BUG-103 — que a crítica adversarial mostrou **já corrigidos**. Se
tivesse sido gravada, mandaria a próxima sessão re-investigar o que estava
pronto e, no caso do contraste, **re-publicar o acervo inteiro à toa**. É o
dano que a §2.4 existe para impedir, e ele quase entrou pelo documento que
deveria preveni-lo.

```
/goal
MISSÃO: CAÇA AOS BUGS do /opt/wiki — todos, do crítico ao warning, INCLUSIVE pré-existentes e de outra frente. Você é o engenheiro-chefe do repo, da produção e da infra: bug se corrige sendo seu ou não. Documentar NÃO substitui corrigir — achado vira correção COMMITADA nesta sessão. "Depois", "fora de escopo", "é de outra sessão" são PROIBIDOS.

PASSO ZERO — RE-TRIAR: o repo se move enquanto você lê (15 commits durante a redação do plano, 3 críticos já caídos). Reproduza a medição ANTES de corrigir; o que cair vai para os refutados com o commit que fechou.

PLANO VIVO (consulte e ATUALIZE a cada task): docs/goal/PLANO_CACA_BUGS_20260829.md — 137 bugs (BUG-013..149), 18 refutados, trem de publicação e as correções que NÃO devem ser feitas como escritas. Defeito → BUGLOG.md. Tasks → .agents/runtime/p0_frontboard.jsonl. NÃO crie doc novo: 21 já registram bug.

MÉTODO (8 passos, nenhum se pula): ler código+dado real → medir com comando próprio → entender o contexto (git log -S, DEC-*) → teste VERMELHO → Fable REFUTA → corrigir a CAUSA RAIZ → regressão verde → BUGLOG+frontboard+commit.

NÃO CONFIE: comentário/README não são fonte — comentário que mente é BUG. Gate verde não é prova (4 falsos verdes); vermelho não é veredito. Relatório de agente é ALEGAÇÃO até conferir no disco. Todo número vem com o comando. DADO DE AGENTE NUNCA SE DESCARTA, nem o refutado.

CRÍTICOS VIVOS (medidos 2026-08-29):
1. cmd/build public REPROVA: 261 achados em 29 rotas (259 = o gerador de /diarios cunha source_id por gazeta, ignorando o ID curado). Sem build verde, não há deploy.
2. FAMÍLIA-A: 42 arquivos leem public/sitemaps/ do DISCO (62 xml + 58 br) em vez do índice (34 shards, 10.336 URLs). O aquecedor foi remendado por dedup, a fonte segue errada e check-edge-cache-coverage publica universo_urls=18731. UMA função "universo público" vinda do índice.
3. CVE viva: GO-2026-5932 em x/crypto v0.55.0 (go.mod:103); sca-osv-scan vermelho desde 28/07 e a evidência nem cobre o bump de roaring/gofeed.
4. go vet dá FALSO-VERDE por VetxOnly: o comando documentado esconde 2 de 3 diagnósticos. Use GOCACHE dedicado ou -tags nonce. tools/go-build-check:46 usa ./... e nunca verificou nada.
5. googlebot-smoke valida o próprio cache (/tmp fixo, checks.go:6777): exit 1 com cache velho, 0 com vazio.
6. public-release-transaction: 59.388 erros = DOIS campos que o produtor nunca escreve: source_type e use_in_content.
7. GOAL.md, 1º na precedência, declara published_manifest=0 e deficit=10000 como regra que "prevalece"; check-contrato-vs-medicao nem o lê e tolera 505 páginas. NÃO exija igualdade exata: quebra o pre-commit a cada publicação.
8. Autolinker parte citação com sufixo: 225 href/JSON-LD em ~199 páginas apontam para OUTRO dispositivo, 10 com URN do CPC/2015 para artigo do CPC/1973. Acoplado ao art. 24-A inexistente em /glossario/qualidade-de-segurado/ (é 27-A).
9. ValidateEditorialBody (ética OAB no corpo) é CÓDIGO MORTO: valida 7.959 candidatos, não as 10.116 no ar.

DEPOIS: zero backup sole-copy (data/ 12 GB, /opt a 78%, manifesto apontando por sha para recibo inexistente); 3 .tar.gz de /.well-known/agent-skills/ dão 404; 157 de 391 check-* vermelhos; zero gate de teste no commit; 103 rotas sem acento visível; 19 intent_id colididos com cópia vazia; 363 pares ≥0,70 anti-molde; corpus legal contaminado; Last-Modified = mtime do build (build.go:311) mata o 304 — antes do trem de publicação.

PROIBIDO: relaxar/pular gate; stub/mock; reset/checkout/restore/stash/revert/clean; ./... em Go; cmd/check sem argumento; --no-verify; UA de bot real; SaaS/API key.
CUIDADO: mudar o HTML de todas as páginas = UM deploy só, com deploy-publico --ressemear + purga ampla + medir 304; v2 = 2 commits; commit Go com flock; add separado do commit, mensagem por -F. Sessão concorrente: leia o disco antes de editar.
advisor antes de cada frente e do pronto; Fable REFUTA antes de editar caro. Ondas paralelas, sem teto.
PROGRESSO = bug fechado com teste, gate verde, commit.
```

---

## 13. Execução — registro vivo

**Placar agora:** `caça aos bugs: 139 tasks | todo=126 fechado=13`

**Commits da caça, em ordem:**
- `6c3261fe docs(caca): 137 bugs catalogados com evidencia, e o passo zero que tres deles ensinaram`
- `8049936a chore(dado): o produto de 28/08 entra no repo, e o recibo que o manifesto ja citava`
- `b24db0f3 chore(higiene): os untracked classificados um a um, e por que o padrao cego seria pior`
- `b91d3b6f feat(caca): a transicao de estado dos 137 bugs vira ferramenta, e ela exige prova`
- `f418e713 fix(sca): a varredura de vulnerabilidade descrevia uma arvore que nao existia mais`
- `5a60637d fix(vet): o unico script que roda go vet nunca verificou um pacote, e o cache mentia`
- `32313dfd fix(sitemap): 42 leitores confundiam o deposito com o anuncio, e um deles morria nisso`
- `38c227a7 feat(qualidade): a suite do projeto ganha executor, porque nao tinha nenhum`
- `2ab3bc64 fix(alerta): 63 alertas, zero resolucoes — o ramo que fecha lia o proprio evento`
- `2093fc95 feat(alerta): condicao curada passa a fechar sozinha, com evidencia da serie viva`

**O que a execução já ensinou, e que o plano não previa:**

1. **O PASSO ZERO se pagou no primeiro crítico.** O BUG-056 mandava "subir
   x/crypto". Lendo a evidência antes de agir: `fixed_version: ""`,
   `upstream_has_no_fix: true`, `reachable_call: false`. Não existe versão
   corrigida e o código não é alcançável — `go get` teria falhado e não
   resolveria risco algum. O defeito real era o **drift da evidência**, sem
   acoplamento a `go.mod`. A correção mudou de alvo por causa da leitura.

2. **Corrigir um gate cego revela o que ele escondia.** O
   `check-internal-link-floor` morria em `UnicodeDecodeError` antes de medir.
   Consertado, acusou na primeira execução `/jurisprudencia/stf-adi-5502/` com 2
   links de entrada contra piso 3 — um defeito de SEO que estava invisível
   atrás do crash. Virou BUG-150.

3. **Consertar o mecanismo não conserta o passado.** A ordem invertida do
   `check-edge-live` (BUG-060) deixou o ramo de resolução morto: 63 alertas, 0
   resoluções. Corrigi a ordem — e o alerta crítico de 38 h **continuou aberto**,
   porque o ledger já registrara `ok=true` e não havia mais transição a
   observar. Só o reconciliador por evidência (BUG-018) fechou o passado. Dois
   bugs que pareciam um.

4. **A família aparece quando se varre a classe, não o caso.** Ao corrigir o
   cache fixo do `googlebot-smoke` (BUG-104), a varredura de `os.TempDir()` em
   `internal/checks` achou o **mesmo defeito** em `runtime-observability` — e o
   irmão já corrigido, com o comentário certo, estava 60 linhas adiante desde
   2026-08-04. A correção existia e nunca fora propagada.

---

## 14. Canal diário vivo — a base legal, as fontes e o que a onda derrubou

Ordem do dono (2026-08-29): *"tudo que tem nos tribunais são públicos... isso não
é trava, ache solução... para criar um portal de notícia na wiki e de conteúdo
diário VIVO e não morto"*, com autorização expressa para **mudar a arquitetura e
raspar**, com qualidade de engenharia.

### 14.1 A base legal, por camada — com o que o crítico corrigiu

| Base | O que autoriza | Limite |
|---|---|---|
| **CF art. 37 caput, art. 5º XXXIII e LX, art. 93 IX** | Publicidade é a **regra**; todo julgamento do Judiciário é público | Sigilo precisa de **lei** (segredo de justiça), não de conveniência |
| **Lei 9.610/98 art. 8º, IV** | *"os textos de tratados ou convenções, leis, decretos, regulamentos, decisões judiciais e demais atos oficiais"* **não são objeto de proteção**. Reprodução **integral** lícita, sem licença e sem limite | Alcança diário oficial de **qualquer ente**, edital, portaria, IN, resolução, acórdão, ementa, súmula e **tese** de repetitivo. **Não** alcança notícia institucional nem resumo editorial |
| **Lei 9.610/98 art. 7º §2º** | *"A proteção concedida no inciso XIII não abarca os dados ou materiais em si mesmos"* — o ato individual é livre mesmo extraído de uma base | Não espelhar a **edição inteira** como coletânea alheia |
| **Lei 9.610/98 art. 46, I, "a"** | Reprodução de notícia/artigo informativo com menção à publicação de origem | **Duas qualificações** que a frente não enfrentou (crítico); a condição de "imprensa periódica" do portal é contestável — o default seguro é trecho + comentário |
| **Lei 9.610/98 art. 33** | — | **O limite que protege o projeto**: comentar **não** autoriza reproduzir integralmente obra protegida. É o que impede a regra das duas camadas de virar lavagem |
| **LAI art. 8º §3º III** | Obriga o Estado a permitir *"acesso automatizado por sistemas externos em formatos abertos, estruturados e legíveis por máquina"* — coleta automatizada é o uso **previsto** | Município pequeno tem dispensa parcial (crítico) |
| **Lei 14.129/2021 art. 29 + Decreto 8.777/2016** | Reuso livre, sem restrição comercial | **REFUTADO pelo crítico:** as duas normas **não alcançam município, estado nem tribunal** — só a esfera federal |
| **LGPD art. 7º IX e §§3º/7º** | Base para dado pessoal em ato oficial | Art. 11 §1º: ato de pessoal pode revelar **dado sensível**, e a lista do art. 11 é **exaustiva** (crítico) |
| **STF Tema 786 / RE 1.010.606** | Direito ao esquecimento amplo é incompatível com a Constituição — decide **a favor** | **NÃO VERIFICADO** nesta sessão: a sonda do STF não respondeu (crítico). Confirmar antes de citar |
| **Prov. OAB 205/2021 art. 2º II** | Reconhece expressamente *"marketing de conteúdos jurídicos"* | Sobriedade; veda promessa de resultado — não a republicação |

**O risco remanescente não é autoral: é contratual** (robots.txt e termos por
fonte), e se resolve escolhendo a fonte certa. Medido: **não há licença expressa
de reuso** nos rodapés de STJ, CJF e TRF6 — e "HTTP 000 em robots.txt" **não é
"sem robots"**, é inversão de risco (crítico).

### 14.2 Os três níveis de fonte — o que decide o molde de página

- **Nível A — corpo integral citável:** decisão, ementa, súmula, tese, texto de
  lei (art. 8º IV) e Informativo do STF (licença expressa). O bloco citado é
  legítimo; o comentário autoral é o que dá valor.
- **Nível B — notícia institucional:** a **redação** é protegida; livre é o
  **fato**. O `content:encoded` **não vira corpo publicado** — vira **insumo**:
  extraem-se processo, Tema, Súmula, órgão e relator (fatos), reescreve-se com
  palavras próprias, cita-se o **título** (art. 8º VI: títulos isolados não são
  objeto de proteção) e usa-se o número extraído para buscar a **ementa/tese** no
  Nível A, que sim pode ir em bloco. O bruto fica no raw store como prova, nunca
  em `public/`.
- **Nível C — bloqueado:** portal privado; DOU/`in.gov.br` (robots `Disallow`);
  texto do DJEN.

### 14.3 Fontes novas, sondadas e com veredito do crítico

| Fonte | Canal | Medido |
|---|---|---|
| **STF** | `noticias.stf.jus.br/feed/` | **10 corpos numa requisição** (`content:encoded` de 1.829 a 25.485 car.). O crítico **refutou** a recomendação de usar `wp-json`: o número que a frente atribuiu à API saiu do próprio feed |
| **TJBA** | `tjba.jus.br/portal/feed/` | 15 blocos `content:encoded`, primeiro com 3.522 car. Único TJ testado que entrega corpo |
| **CNJ** | `wp-json/wp/v2/posts` | `content.rendered` = 6.635 car. O `/feed/` é **301** para a home — armadilha |
| **Câmara** | `dadosabertos.camara.leg.br` | 80 proposições num dia, com ementa oficial |
| **TJPR** | RSS Liferay | 20 itens, descriptions de 56–164 car. — **canal de descoberta, não de corpo** (crítico) |
| **Receita** | RSS Plone gov.br | 206 com Range; robots não bloqueia |
| **DJEN/Comunica (CNJ)** | API | `count=10000` é **teto da API, não volume** (crítico). 24 campos, com superfície LGPD que a frente não nomeou |
| **Senado** | `legis.senado.leg.br` | **já passou da data de desligamento**; o sucessor está nomeado no próprio payload e funciona (crítico) |
| **TST** | RSS Liferay | **já é coletado hoje**, e pela URL que a frente disse não servir (crítico) |
| **TJRS** | `/novo/feed/` | **VAZIO**, não "feed de resumo" (crítico) |

### 14.4 O plano de execução — 8 passos, cada um com o teste que o prova

`P1` parar a perda de página publicada · `P2` destravar o early-return do
`content-quality` · `P3` ler o corpo **por feed** · `P4` extrair processo/Tema/
Súmula do corpo · `P5` raw store append-only com hash · `P6` formalizar
`legal_basis` por nível no registro · `P7` fontes novas (STF e TJBA primeiro) ·
`P8` shard mensal antes de escalar.

**Nenhum passo espera a madrugada:** cada um tem teste isolado e roda na sessão.

---

## 11. ESTADO AO FIM DA ONDA DE 2026-08-29 — o que fica para a próxima sessão

Escrito no fim da sessão, com o placar medido do frontboard, não estimado:

```
python3 -c "conta .agents/runtime/p0_frontboard.jsonl por status"
  172 bugs registrados
  119 fechados  (97 corrigidos, 10 mortos por medição, 6 refutados, 3 parciais, 3 outros)
   53 abertos   (16 graves, 21 médios, 13 leves, 3 sem severidade)
```

**Três dos nove "críticos vivos" do goal já estavam mortos**, e cada um
economizou uma frente inteira — a lição é sempre a mesma, e vale para quem pegar
esta lista amanhã: **re-triar antes de corrigir**.

| crítico | como caiu |
|---|---|
| `cmd/build public` reprova, 261 achados | `./tools/go-modern run ./cmd/build public` → `generated_pages=10126 indexable_pages=10341`, zero achados |
| CVE viva GO-2026-5932 | `govulncheck ./internal/... ./cmd/...` → *"Your code is affected by 0 vulnerabilities"*; a exceção já estava registrada com fundamento medido |
| universo inflado 18.731 | hoje 10.302, cobertura 100% (BUG-073) |

### Como ler esta lista sem repetir o trabalho de hoje

1. **A âncora do catálogo derivou.** Um símbolo dado como linha 439 estava na
   483; uma contagem de 339 virou 358; um bug apontava
   `collect-diarios-municipais` e o defeito estava em `collect-normas-federais`.
   Re-grepe tudo.
2. **Vermelho em massa quase nunca é conteúdo.** Cinco vezes hoje o errado era o
   detector: `.js` casando `.jsp` (o STJ publica em `.jsp`), cache do Chrome
   contado como código do projeto, prosa acusada como material, e um censo de
   catálogo pinado a um seed de 73 entradas contra 3.737 de hoje.
3. **Verde também não é prova.** O gate de citação legal respondia `pass` porque
   13 de 29 diplomas estavam marcados inconfiáveis e ele não podia acusar.
4. **O enunciado pode estar errado e ainda assim haver defeito.** O BUG-169
   dizia "ordenação instável muda a saída"; `sort.Slice` é pdqsort,
   determinístico — mas o empate por município decidia *qual edição* recebe
   texto, e 29 de 237 territórios trocavam de vencedor.

### GRAVES — atacar primeiro (16)

- **BUG-021** — BUG-004 continua aberto e a superfície cresceu Medido hoje em `internal/checks/checks.go`: `Names` tem 322 gates; só 68 alcançam caminho ctx-aware (26
- **BUG-041** — Os dois defeitos de conteúdo que derrubam a onda diária, medidos `check-frescor-canal-diario` (exit 1): *coleta OK, publicação não avançou* — `diarios
- **BUG-049** — Zero páginas têm o tripé fonte = URL + data + hash `official_sources` em `v2_pages` não tem campo de hash de conteúdo. Os `sha256` em `v2_source_prove
- **BUG-050** — Zero `publication_allowed: true` em 10.230 registros do
- **BUG-065** — O canal Markdown ficou 42 minutos fora do ar dentro da janela de
- **BUG-068** — `muffet` e `htmltest` auditaram um espelho de 363 URLs — as 10.340
- **BUG-118** — Três diplomas do corpus legal contaminados com artigo de OUTRA lei `cpc.json` (n=1075, fim denso 1072, suspeito 2027), `lei_12653_2012.json` (n=5, sus
- **BUG-119** — 124 refinamentos pagos órfãos derrubam o carregador canônico do
- **BUG-122** — `legal-citation-attribution` acusa 184 páginas (97 `diploma_sem_fonte`, 66 `sumula_sem_fonte`, 35 `tema_sem_fonte`) — reenquadrado pelo verificador: é
- **BUG-124** — 24 gates vermelhos por evidência derivada estagnada — e pelo menos
- **BUG-155** — similaridade O(n2) no shard: 18k/ano = 162 milhoes de comparacoes por execucao diaria
- **BUG-156** — DEC-032 atribui texto de lei ao art. 8o I; o inciso e o IV
- **BUG-160** — CC BY 4.0 declarada no ar colide com o primeiro corpo de terceiro publicado
- **BUG-175** — quatro fontes declaram guardar texto oficial bruto e o teste de contrato proibe, ha tempo indeterminado
- **BUG-178** — a regua que separa acervo velho de novo no gate e um campo que o proprio produtor controla
- **BUG-179** — o gate aceita qualquer URL sob um source_id curado: o vinculo id<->dominio nao e verificado

### MÉDIOS (21)

- **BUG-031** — — a queda de revisita pode ser o efeito documentado de republicação em massa (reseed de 28/08 re-datou o acervo; já foi medido acontecer 2× com o `met
- **BUG-033** — `internal/agentsurface` e `internal/pageinline` sem nenhum teste São, respectivamente, a fonte única das rotas de máquina e a constante do único scrip
- **BUG-034** — 169 `Lock()` sem `defer Unlock()` adjacente Candidatos concentrados em `internal/v2ingest/`, `internal/sitemapstream/`, `internal/batchdrafts/`, `inte
- **BUG-040** — 1.707 páginas publicadas só têm link de hub, sem spokes `./tools/check-v2-internal-link-graph` (exit 0): `content_pages=10111 area_hubs=32 pages_with_
- **BUG-051** — Três ledgers discordam sobre a mesma partição crítico 100 (`v2_publication_severity.jsonl`, vivo) × 119 (`data/ops/v2_publication_severity_summary.jso
- **BUG-052** — 9.385 páginas publicadas (92,8%) carregam erro médio pendente `fonte_insuficiente` 1.378 · `corpo_entre_250_e_400_palavras` 1.372 · `reprovada_por_age
- **BUG-074** — `check-edge-cache-coverage-honesty` está vermelho com 8 problemas e
- **BUG-076** — 4 séries vivas sem consumidor *(não 6 — duas foram refutadas: o filtro do primeiro agente excluía onde os consumidores moram)*: `time_to_first_crawl_d
- **BUG-077** — 77 arquivos em `data/ops` (11,1 MB) sem uma única referência em
- **BUG-078** — 13 binários ELF RASTREADOS no git, ~448 MB — confirmei: `data/ops/rollback-20260806/wikijuridica-server` (31 MB, versionado, não ignorado), `.agents/r
- **BUG-081** — Quatro comentários de código que mentem *(R1: comentário que mente é bug)* — `nginx.conf:98` afirma que o ETag sobrevive (desligado 15 dias depois); `
- **BUG-082** — Decisão × produção divergem sobre o `llms.txt` — o repo documenta "llms.txt NÃO é padrão real / NÃO implementar" em `docs/goal/cowork/SEO_INDEXACAO_20
- **BUG-084** — `internal/agentsurface` não é o inventário que se diz ser — 11 rotas de máquina vivem fora dele (`/a2a/v1`, `/api.md`, `/auth.md`, `/changes.json`, `/
- **BUG-127** — · A página 404 é a única superfície servida sem o script de
- **BUG-129** — · A única sonda de corrida sobre `RunAll` está desligada por `WIKI_CHECKS_FULL_RACE`, variável que ninguém define (4 ocorrências, todas no próprio arq
- **BUG-131** — · 8 testes stale em 4 pacotes, por mudança deliberada não refletida na asserção; 4 perfis de seleção de gate derivaram do ledger validado — inclusive 
- **BUG-132** — · `AGENTS.md`, primeiro na cadeia de precedência, é integralmente endereçado ao Codex, desativado por ordem do dono em 2026-07-21 — e condiciona o fim
- **BUG-133** — · O inventário de citações — instrumento do P1 — está 16 dias
- **BUG-158** — isPendingAudit cego a nao_conferido; ingerir exclui ser aprovado por construcao
- **BUG-164** — o venv da extracao de HTML aponta para o python3 do sistema, que nao tem trafilatura
- **BUG-176** — o checked_at global do registry v2 saia da PRIMEIRA fonte da lista, nao da evidencia mais recente

### LEVES (13)

- **BUG-038** — `.claude/settings.json` com 53 linhas removidas, não commitado O bloco `enabledPlugins` inteiro sumiu do arquivo. Apurar a origem antes de qualquer co
- **BUG-085** — · `datePublished`/`dateModified` sem hora nem fuso em 590/590 valores; `<lastmod>` só com data (o Bing pede ISO 8601 com hora). - BUG-086 · `Article` 
- **BUG-086** — · `Article` sem `image` (295/295), sem `wordCount`, `articleSection`, `isPartOf`; `about` em 11 de 295. `og:image` existe em 10.339. - BUG-087 · `max-
- **BUG-087** — · `max-image-preview:large` ausente nas 10.339 páginas. *(085/086/087 mudam HTML → uma única publicação com `--ressemear` + purga.)* - BUG-088 · 10.43
- **BUG-092** — · Cinco tetos de `1_000_000` iguais à meta declarada de
- **BUG-095** — · Registro de bots sem campo de conformidade com robots nem de método de verificação; 3 agentes documentados ausentes (`meta-externalads`, `Google-Clo
- **BUG-096** — · `deadcode` custa zero (já em `golang.org/x/tools v0.49.0` no cache) e `errcheck` quase zero — nenhum dos dois está ligado. - BUG-097 · `vale-public-
- **BUG-097** — · `vale-public-prose-lint-release` está vermelho com 140 erros de prosa e alimenta o verdict de release. O trabalho é resolver os 140. - BUG-098 · `ht
- **BUG-139** — · O comando de build documentado no CLAUDE.md cobre 481 de 760 pacotes; nenhum gate linka os 279 dev-mains. O comentário do pre-commit fala em "504 pa
- **BUG-140** — · `run-check` re-deriva o grafo de dependências do Go a cada invocação: 3.161 ms contra 703 ms do binário direto — 2.458 ms de overhead por gate × 322
- **BUG-141** — · `docs/audits/` tem cinco arquivos de 2026-06-28 declarando `published_manifest=0`, 62 dias depois; o `PLANO_RASTREIO` lista cinco defeitos como "ain
- **BUG-142** — · Comentário que mente em `css_contrast_test.go:170-172` — afirma que o auditor não alcança media query, e ele alcança desde `darkThemeFindings`. - BU
- **BUG-143** — · §4e-bis de `DADOS_CONFIAVEIS` está desatualizada: existe canal local de enunciado de súmula, cobrindo 23 das 48 do STF citadas — mas prova texto, nã

### SEM SEVERIDADE ATRIBUÍDA — reescopados ou com causa-raiz já identificada (3)

- **BUG-017** — BUG-017 REESCOPADO: a metade acidental morreu; o que resta e construir o canal de alerta para veredito exit-1
- **BUG-112** — BUG-112 CAUSA-RAIZ: o verdict nao esta 'ausente' -- foi DELETADO por engano no commit 3f36df9c, em 2026-07-09
- **BUG-170** — BUG-170 REATRIBUIDO: o alvo e cmd/collect-normas-federais

### Ferramentas novas que a próxima sessão herda

Todas com gatilho declarado — gate sem gatilho é gate cego, e 408 dos 461
`check-*` não tinham nenhum:

| ferramenta | o que faz | gatilho |
|---|---|---|
| `tools/pre-voo` | a sequência canônica antes de commitar, em ordem de custo, parando no primeiro erro e imprimindo o conserto | manual |
| `tools/check-git-guard-regressao` | 41 vereditos sobre o guard de git destrutivo | `pre-voo` |
| `tools/check-git-invocacao-saneada` | nenhuma invocação de git herda `GIT_DIR` do chamador | `pre-commit` (se toca `.go`) + `pre-voo` |
| `tools/check-buglog-status-coerente` | o BUGLOG não pode contradizer o frontboard, nem faltar seção | `pre-commit` (se toca os dois) + `pre-voo` |
| `tools/check-sca-alcancabilidade` | exceção de CVE sustentada por medição dispensa prazo; a sustentada por argumento não | `pre-commit` + `pre-voo` |
| `tools/generate-buglog-status` | reconcilia o status do BUGLOG a partir do frontboard | manual, com `--seco` |
| `tools/recuperar-do-autosave` | lê o snapshot que o hook grava antes de cada escrita | manual |
| `internal/gitenv` / `internal/gittestenv` | ambiente saneado para invocar git em produção e em teste | pacotes |
| `internal/gobincache` | a decisão de cache de binário, testável por comportamento | pacote (ADR em `docs/adr/`) |

---

## 15. ESTADO AO FIM DA ONDA DE 2026-08-30 — o que a re-triagem derrubou e o que se corrigiu

### Os nove críticos: oito estavam mortos

O Passo Zero deu o resultado mais valioso da onda. Remedidos com comando próprio, **oito dos nove críticos listados como "vivos" já não existiam** — a tabela com o comando de cada veredito está em `docs/goal/BUGLOG.md`, seção *Re-triagem dos NOVE críticos*. Resumo: build público `achados=0`; `universo_urls` em **10.312** e não 18.731; `go-build-check` cita `./...` só em comentário explicando por que não usa; googlebot-smoke usa `os.MkdirTemp`; `public-release-transaction` passa; o GOAL.md tem `CONTADORES VENCIDOS` in loco nos seis parágrafos; o autolinker emite `art27a`, correto; e `ValidateEditorialBody` é chamada em `checks.go:6678`.

O nono, a CVE `GO-2026-5932`, é o único que resiste — e a medição o fecha em vez de deixá-lo aberto: `go list -m -versions` termina na própria v0.55.0 (**não há para onde subir**) e o govulncheck do repositório já registrou `reachable_call: false`, `reachable_findings_count: 0`, `upstream_has_no_fix: true`. Entra na cadeia por `officialpdfprobe → pdfcpu/sign → x/crypto/ocsp`, sem chamar o símbolo.

### Bugs novos, achados e corrigidos nesta onda

| bug | o que era | commit |
|---|---|---|
| **BUG-224** | oito oráculos tiravam o piso de registros de uma população (`drafts`, 7.972) e o aplicavam a outra (`refined`, 7.959) — 455 elementos de divergência —, e o gerador saía antes do `WriteEvidence`, tornando a evidência **ingravável** | `8b35ac6e`, `a3d0552c` |
| **BUG-225** | validação auto-referente deixava o gate do índice FTS5 **verde com 590 de 7.959 registros** desde 10/07 — 7,4% do acervo indexado | `4fb203b9`, `2ff19bcc` |
| **BUG-226** | **refutado**: a suspeita de que o `OABCTA.yml` duplicava nocivamente o detector canônico caiu — são três camadas com escopos distintos, e a rota teria criado 2 ReleaseBlockers num gate P0 limpo | `f81bc28e` |
| **BUG-227** | o gerador do LanguageTool trocava 7.959 registros por uma amostra de 200 **com EXIT 0**; aconteceu nesta sessão e exigiu restauração | `2547bc1b`, `4a6cac9d` |
| **BUG-228** | o instalador montava o LanguageTool na versão errada (6.6 do zip, quando o código exige a 6.8 do Maven) e na porta errada (8081 × 8082) | `a2f0e321` |

Mais: `POR_QUE_PORQUE` — metade dos 7.019 blockers do corpus — reclassificada como advisory, com a amostra real provando que as 3.932 ocorrências de "por que" estão em interrogativa indireta, onde a forma separada é a correta (`fb58ae5b`); 44 termos jurídicos legítimos no léxico do spellcheck, medidos um a um (`ebd964d8`); e `cmd/diag-jsoncodec-parity`, que refutou a própria hipótese que motivou sua construção (`4f868138`).

### Três erros meus de medição, corrigidos no registro

Ficam aqui porque a lição é de método, não de conteúdo: contei **7 hits onde havia 20** (o script colapsava páginas distintas, e o número certo estava no ledger que eu já tinha); dei **zero ocorrência a seis tokens que existiam** (medi 3 dos 5 campos que o detector varre, e com tokenização diferente de hífen); e afirmei que **"garantia de êxito" era coberta** pelo detector canônico quando o próprio código registra que ela não entrou de propósito. As três vieram de reimplementar a fórmula em vez de usar a do código — que é exatamente a regra nº 1 deste plano.

### O que fica em execução, com a ferramenta que a torna repetível

A evidência do `languagetool-quality` precisa ser regenerada para refletir a política nova (o `cache_policy_sha256` mudou de propósito). Medido: **~2,2 registros/s**, logo ~61 min para os 7.959 — contra o teto duro de 1800 s do envelope. `tools/regenerate-languagetool-evidence` (`5211bb86`, `7870de25`, `10ebcf04`) faz o fatiamento que o próprio wrapper manda fazer, tratando `exit 75` como corrida e não como fatia gasta.

---

## 16. OS NOVE CRÍTICOS, RE-MEDIDOS AO VIVO EM 2026-08-30 — a lista da seção anterior está VENCIDA

Esta seção substitui a lista "CRÍTICOS VIVOS (medidos 2026-08-29)". Cada linha traz o comando que produziu o veredito, rodado nesta data. **Oito dos nove já não existiam**, e o nono está medido até o fim.

| # | o que o plano afirmava | veredito em 2026-08-30 | comando |
|---|---|---|---|
| 1 | `cmd/build public` reprova: 261 achados em 29 rotas | **MORTO** | `./tools/go-modern run ./cmd/build public` → `generated_pages=10136 indexable_pages=10351`, **EXIT=0**, zero achados |
| 2 | `check-edge-cache-coverage` publica `universo_urls=18731` | **MORTO** | última linha de `data/ops/edge_cache_coverage.jsonl` → `universo_urls = 10312` |
| 3 | CVE `GO-2026-5932` viva em `x/crypto v0.55.0` | **medido até o fim** | `go list -m -versions` termina na própria v0.55.0 (**não há para onde subir**); `sca_govulncheck_evidence` → `reachable_call: false`, `upstream_has_no_fix: true`, `reachable_findings_count: 0`; `go mod why -m` mostra a cadeia `officialpdfprobe → pdfcpu/sign → x/crypto/ocsp`, sem chamar o símbolo |
| 4 | `tools/go-build-check:46` usa `./...` e nunca verificou nada | **MORTO** | `grep` por `./...` em linha de código → **0**; as três ocorrências são comentário explicando por que ele NÃO usa |
| 5 | `googlebot-smoke` valida o próprio cache em `/tmp` fixo | **MORTO** | `checks.go:6892` → `os.MkdirTemp("", "portaljuridico-googlebot-smoke-cache-")`, diretório único por execução |
| 6 | `public-release-transaction`: 59.388 erros de `source_type`/`use_in_content` | **MORTO na causa original**, e a nova apareceu e foi fechada | o gate reprovava por `v2_stock_freshness_*`, não pelos dois campos — virou o **BUG-235**, resolvido pelo `ingest-v2-stock` (commit `73f47be5`). Estado atual: `public-release-transaction: pass`, **EXIT=0** |
| 7 | `GOAL.md` declara `published_manifest=0` como regra que prevalece | **MORTO** | `grep -c "CONTADORES VENCIDOS" GOAL.md` → **4** parágrafos ressalvados in loco, com a medição de 2026-08-29 |
| 8 | autolinker: URN do art. 24-A inexistente em `/glossario/qualidade-de-segurado/` | **MORTO** | a página servida tem **0** ocorrências de `24-A` e **1** de `8213!art27a`, que é o artigo correto |
| 9 | `ValidateEditorialBody` é código morto | **MORTO** | `checks.go:6678` a **chama**, dentro de `checkLegalMarketingPolicy`, sobre as publicadas e indexáveis (BUG-117) |

**Sobre o nº 3, que é o único que resiste:** não há correção a commitar porque não há versão para onde subir — a listagem do módulo termina na versão afetada — e o símbolo não é alcançado. Fingir um bump inexistente mudaria o `go.sum` sem reduzir risco nenhum. O que muda o quadro é o upstream publicar a correção, e aí o bump é mecânico. Está registrado em `data/ops/sca_ignore_risk_register.jsonl` com a medição que o sustenta.

**Por que oito caíram sem ninguém "consertar" nesta sessão:** foram corrigidos entre 29 e 30 de agosto, por esta e por outras passadas, e a lista do plano é de 29/08 pela manhã. É exatamente o que o PASSO ZERO antecipa — *"o repo se move enquanto você lê"*. O que esta sessão fez foi **reproduzir a medição antes de corrigir**, e o que caiu foi para os refutados com o comando que o derrubou.

### O que esta rodada fechou, além dos críticos

`BUG-227` (gerador trocava 7.959 registros por 200 com exit 0) · `BUG-228` (instalador do LanguageTool na versão e porta erradas) · `BUG-229` (auditoria de dependências 39→76) · `BUG-230` (gate de bots escondia a queda que motiva o veredito) · `BUG-231` (meta description com contagem colada) · `BUG-232` (três bots do Google com pista ilimitada sem entrada na política) · `BUG-233` (varredura contava como vermelho gate que só pede argumento) · `BUG-234` (**o scanner de segredos não compilava**) · `BUG-235` (edição de shard travava publicação de todas as frentes) · `BUG-236` (**o check da cobertura de borda escrevia no ledger e a série media a si mesma**), mais a quarentena da sonda no access ledger, a transação v2 com recibo versionado e a limpeza de 96 snapshots (7 GB) com autorização do dono.

**O mapa da bateria** está em `.agents/runtime/caca/varredura-{a,b}.jsonl`: **472 dos 473 gates** medidos com exit code real — 288 verdes, 165 vermelhos de veredito, 12 timeout, 6 instrumento, 1 corrida de lock.

### 16.1 Crítico 2 (FAMÍLIA-A), medido na CAUSA e não no sintoma

Na seção 16 eu havia verificado só o sintoma — `universo_urls = 10312`. O plano descreve a **causa**: "42 arquivos leem `public/sitemaps/` do DISCO (62 xml + 58 br) em vez do índice", e pede "UMA função 'universo público' vinda do índice". Medido agora:

- **A função única existe e está adotada:** `tools/wikiuniverso.py`, usada por `warm-edge-cache`, `check-edge-live`, `check-url-variantes-canonical`, `measure-edge-retention` e o próprio `check-edge-cache-coverage`.
- **A correção está registrada no código, com a medição que a motivou.** `tools/check-edge-cache-coverage:78-95` traz, no docstring da `urls_do_sitemap()`: *"FAMILIA-A (corrigido em 2026-08-29, BUG-014 da caça): esta função fazia glob de `public/sitemaps/*.xml` e somava os 62 arquivos do disco — os 34 anunciados MAIS os 28 em carência, que existem de propósito para servir 200 a quem tem o índice anterior e NÃO são anunciados a ninguém."* E o efeito: o universo inflou de 10.336 para 18.726 (**+81,6%**), fazendo o alerta dizer ao dono que "~18.726 páginas devolveriam 530 se o túnel cair". A duplicação era pura — as URLs exclusivas dos shards retirados eram **zero**.
- **As menções caíram de 42 para 26**, e sobraram **dois** globs do diretório, ambos legítimos e documentados no próprio arquivo:
  - `internal/checks/superseded_sitemap_gate.go` — **precisa** do shard ao vivo, porque "a marca de carência vive só no shard AO VIVO em `public/sitemaps/`, que um build temporário (a partir do `content/pages.json` atual) nunca reconstrói";
  - `cmd/publish-v2-direct/main.go` — é o **publicador**: ele escreve os sitemaps, e lê o diretório para remover órfãos do padrão que ele mesmo cria, com remoção "ESTREITA de propósito".

**Veredito: MORTO na causa**, não só no sintoma. Ler o disco continua certo para quem precisa do estado ao vivo; o que era defeito — derivar o *universo de medição* somando arquivos do disco — deixou de existir.
