# CONTRATO DO DADO REAL — ordem do dono, 2026-08-12, VINCULANTE E PERMANENTE

Este documento é o contrato de trabalho que o dono ditou em 2026-08-12, no comando
`/batch` em modo ultracode. Ele **não expira com a sessão**: vale para toda sessão de
Claude Code, todo subagente e todo workflow que tocar `/opt/wiki`, até que o próprio
dono o revogue por escrito.

Precedência: em conflito com qualquer outro documento do repo, **vence a regra mais
restritiva para qualidade jurídica, publicação, fonte, integridade de métrica e
segurança**. Este contrato nunca é usado para afrouxar `AGENTS.md` ou `CLAUDE.md` —
só para endurecer o método.

---

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

## 1. O texto da ordem (transcrição fiel, 2026-08-12)

> Continue sendo engenheiro-chefe deste projeto em modo ultracode e batch, usando
> vários agentes/subagentes especializados em engenharia e conteúdo jurídico. Faça
> uma grande revisão como engenheiro e criador de conteúdo.
>
> **Antes de lançar qualquer agente e workflow, explore o projeto**: leia contexto,
> histórico, código, arquivos, conteúdos, para entender os bugs e corrigi-los.
>
> **Foque nos bugs de maior ROI**, como os que afetam o rastreio de bots valiosos e
> caros — Googlebot, ChatGPT-User, OAI-SearchBot, Applebot, Bingbot e os demais bots
> de citação e indexação.
>
> **Explore a engenharia e os conteúdos sem confiar em comentários nem nos gates**,
> que podem ser falso-positivo ou falso-negativo: leia antes, ou lance agentes de
> exploração para trazer contexto.
>
> **Crie a tasklist depois de explorar** — do repo/HEAD, de wikijuridica.com.br, do
> localhost, do túnel, da infraestrutura e de tudo que possa afetar `/opt/wiki` —
> para melhorar, otimizar, criar o que falta, achar gaps por implementar, melhorar e
> corrigir código, corrigir e criar algoritmo.
>
> **Investigue até o que eu não mencionei**, porque quem é o engenheiro-chefe e o
> advogado redator é você, e sua missão é orquestrar agentes especializados em cada
> tema de engenharia e/ou conteúdo, e agentes críticos e adversariais.
>
> Use Opus 5 para a maioria das tarefas e **Fable 5 para o crítico e o adversarial** —
> inclusive para ajudar a decidir e para criticar os dados achados e as alterações
> feitas.
>
> **Nada de alterar coisa pequena para descobrir o erro depois.** Colete dados antes,
> dados verdadeiros, para ter 100% de certeza. **Nada de deixar para depois.** Colha
> dado do repo, de fonte oficial, da web, do GitHub, de open source.
>
> **Se está difícil, procure outra solução — não fique "documentando para
> honestidade".** Seja honesto, mas não apenas documente: ache a solução.
>
> **Não me venha com desculpa de que "o Googlebot rastreia quando quer".** Isso é
> papo furado. Nos primeiros dias o Googlebot passou de 4 mil rastreios e do nada
> parou. Foi bug de engenharia do projeto, de código e de infraestrutura. Eu tentei
> corrigir e parece que não deu efeito. **Não depende do bot.** Depende do projeto, da
> engenharia, das formas de achar o projeto, de navegar, de citar, de indexar, dos
> algoritmos. Seu papel é resolver com engenharia e dado.
>
> **Tudo que for achado deve ser implementado, não deixado para depois**, começando
> pelo ROI alto — inclusive o rastreio dos bots valiosos, que não desperdiçam token e
> CPU com página pesada, com bug, inconsistente ou que os confunde.
>
> Se não souber quais são os bots valiosos, **pesquise em fonte oficial com data de
> hoje (2026-08-12); nada de dado defasado.**
>
> **NÃO ARRUME DESCULPAS. NÃO ME MANDE ME INSCREVER EM API DE TERCEIROS OU SAAS, NÃO
> ME MANDE CRIAR CREDENCIAL, NÃO ME MANDE FAZER NADA. VOCÊ QUE TEM QUE FAZER. EU PAGO
> PARA VOCÊ FAZER.** Você é engenheiro autônomo e redator jurídico no Brasil, então
> não fique fazendo pergunta idiota: busque a solução, respeitando os contratos
> mínimos de qualidade e **sem confiar nos dados que temos, nos comentários, no
> README ou em qualquer documento** — baseie-se em dado real, e para isso **verifique
> antes de declarar, de alterar ou de criar**.
>
> Você está em xhigh, ultracode, com workflow: **nada de tentar fazer tudo sozinho.**
> Trabalhe para arrecadar contexto antes e/ou lance exploradores para lhe dar
> contexto, em vez de sair alterando confiando em dado.
>
> **Mesmo sem dado 100%** — por falta de integração, ou porque o gate ou a API está
> incompleta — **corrija ou integre. Nada de travar trabalho por falta de dado:
> corra atrás e busque o dado. Se falta algo, crie: eu estou mandando.** É criar,
> melhorar, otimizar, ver gaps e implementar, corrigir bugs.

---

## 2. As regras que essa ordem cria (operacionais, verificáveis)

### R1 — Ler antes de tocar. Sempre.
Antes de modificar qualquer código, dado, conteúdo, config ou artefato público, é
**obrigatório** ter lido a coisa real: o arquivo (`arquivo:linha`), o dado vivo
(amostra do JSONL, `git status`/`git diff`, log de produção) e o contrato aplicável.
Editar com base em memória, resumo, checkpoint, README ou comentário é **proibido**.
Comentário que mente sobre o código é **achado a reportar e corrigir**, não fonte.

### R2 — Gate verde não é prova; gate vermelho não é veredito.
Check, gate, auditor e detector deste repo já produziram falso-verde e falso-vermelho
documentados. Antes de usar a saída de um gate como base de decisão, **leia a
implementação dele** e confira contra o dado bruto. Detector novo nasce com teste de
falso-positivo sobre amostra real.

### R3 — Medição própria, reprodutível, com hash determinístico.
Afirmação numérica exige script que qualquer um possa re-executar, gravado no repo ou
no scratchpad e citado na entrega. Hashing usa `blake2b`/`sha256` — **nunca `hash()`
do Python**, que é randomizado por processo. Estimativa (MinHash, amostragem) não
afirma: confirma-se pelo cálculo exato antes de declarar.

### R4 — Falta de dado nunca trava trabalho.
Se o dado não existe, a integração está incompleta, o gate é parcial ou a API não
cobre o caso: **cria-se a medição, integra-se a fonte, escreve-se a ferramenta**.
"Não dá para saber" é resposta proibida enquanto houver caminho de engenharia — e
quase sempre há: log bruto, fonte oficial pública, projeto open source, especificação.

### R5 — Nunca terceirizar trabalho para o dono.
É proibido pedir ao dono que se cadastre em serviço, crie credencial, gere token,
rode comando, aprove o óbvio ou escolha entre duas rotas que o engenheiro sabe
decidir. Quando houver trava genuinamente exclusiva dele (ética/negócio irreversível,
credencial que só ele possui), **diga qual é em uma linha e siga trabalhando outra
frente**. Continua valendo o self-hosted first: nada de SaaS/API proprietária.

### R6 — "Depende do bot" é desculpa proibida.
Queda de rastreio, de indexação ou de citação é tratada como **defeito de engenharia
até prova em contrário obtida por medição**: disponibilidade, status HTTP, latência,
peso, coerência de artefato, malha de links, sitemap, canonical, dado estruturado,
qualidade e unicidade do conteúdo. O mesmo vale para os demais agentes de busca e de
IA. Explicação comportamental sobre um crawler só entra na entrega acompanhada de
fonte oficial **e** depois de as causas de engenharia terem sido medidas e excluídas.

### R7 — Achado vira correção na mesma sessão.
Relatório sem patch é trabalho pela metade. Achou bug → corrige agora, na ordem de
ROI. O que estiver genuinamente bloqueado é dito com o motivo, e todo o resto do
escopo é entregue completo. **Documentar não substitui resolver.**

### R8 — Orquestrar em escala, com crítico adversarial.
Trabalho substancial nasce em ondas de agentes/workflows dirigidas pelo
orquestrador-chefe, nunca em rajada cega: investigar → delegar com contexto apurado →
verificar o output com leitura própria → integrar. **Opus 5** executa a maioria;
**Fable 5** é o crítico adversarial e o fiscal de workflow, acionado antes de decisão
cara e sobre os dados achados e as alterações feitas. Output de subagente é
**alegação** até o chefe verificar no disco.

### R9 — Fonte oficial e atual, com data.
Afirmação sobre lei, prazo, órgão, procedimento, especificação técnica ou
comportamento de crawler exige fonte primária consultada **agora**, com URL e data.
Conhecimento de memória e blog de SEO não são fonte. Sem fonte oficial, escreve-se
"sem fonte oficial" em vez de afirmar.

### R10 — O que já vale continua valendo, e nada aqui afrouxa.
Anti-fraude (métrica só de tráfego real; requisição interna com UA próprio e header
de aquecimento/simulação), zero stub, coerência de artefato público
(HTML + sitemap + `published_manifest` + índice de release com SHA-256 batendo),
ética OAB (Provimento 205/2021), proibição de `reset/checkout/restore/revert/stash/
clean/cherry-pick`, produto nunca em `/tmp`, e página escrita nunca descartada —
tudo permanece integralmente em vigor.

### R11 — Tráfego, alcance e retorno de bot medem-se na BORDA; a origem é piso.
*(ordem do dono, 2026-09-15 — entra nesta família como regra 15 do §P0 de
`docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`)*

O log de origem só enxerga a requisição que chegou até ele. `HIT` na borda, citação sem
clique, resposta dada pela memória do modelo e `Referer` suprimido não deixam linha alguma
na origem. Por isso **nenhum número de origem é volume**: é piso, e diz-se piso.

Medido em 2026-09-15, na mesma janela de 24 h: a origem mostrava **943 requisições**, e foi
esse número que a sessão apresentou como volume de bot; a borda tinha **17.325 bots em
88.033 requisições**. Erro de 4,6× no recorte de bot, e 88 mil requisições que a origem
nunca vê. A ressalva que corrigia o erro estava escrita dentro do próprio arquivo lido — o
campo `edge_reconciliation` de `data/ops/ai_citation_signal_daily.jsonl` diz
`"origem <= borda SEMPRE, mesmo racional de cache."` — e foi **transcrita** um parágrafo
antes de o número errado ser publicado. Transcrever a ressalva não é aplicá-la.

Comando canônico, com a credencial que o projeto já tem: `./tools/check-edge-traffic`. A
série fica em `data/ops/edge_bot_agents_daily.jsonl`, escrita por
`tools/generate-bot-agents-daily`, e é **cumulativa** — lê-se por
`tools/edgetelemetry.py:270` (`serie_saneada`), nunca somando linhas. A armadilha está
detalhada em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`.

### R12 — Não estreitar o projeto com número pessimista.
*(ordem do dono, 2026-09-15 — regra 16 do §P0 do mesmo plano)*

Antes de afirmar que uma frente é pequena, marginal, arriscada ou que "não vale a pena",
mede-se na fonte que tem autoridade sobre aquela grandeza. Quando o instrumento disponível
alcança menos que o fenômeno, **usa-se o que ele alcança e declara-se o alcance** — não se
publica o número curto como se fosse o número. Estágio de produto ("preview", "beta")
qualifica a maturidade de uma API, **não** a confiabilidade do dado que ela devolve: em
2026-09-15 as ~23.000 citações que o painel da Microsoft exibe foram descontadas com o
argumento de que a API está em preview, o que não é um argumento sobre o dado.

Ordem do dono, 2026-09-15: *"você tá limitando meu trabalho que tá dando certo a números
mentirosos… excluindo negócios valiosos, que é inadmissível"*. Risco jurídico entra na mesma
proibição: inventar uma vedação que a norma não impõe estreita o projeto do mesmo jeito que
um número curto. O caso completo está em `docs/PRECEDENTES_DAS_ORDENS.md`.

### R13 — Contrato e comentário são alegação datada; a medição é o fato.
*(ordem do dono, 2026-09-15 — regra 19 do §P0 do mesmo plano; endurece a R1)*

A R1 manda ler o real antes de tocar. A R13 diz **o que** do texto é mais suspeito: tudo o
que ele afirma sobre **capacidade, volume ou limite**. O contrato diz *onde* olhar; nunca
diz *quanto* é. Antes de agir sobre um número que está escrito num documento, num comentário
ou numa unit, mede-se — e divergência encontrada vira correção na mesma sessão, com a
medição anexada.

O plano de 2026-09-15 contou **oito** divergências de documento contra dado real numa única
sessão. **Sete** sobrevivem à conferência de 2026-09-16 — a oitava era erro meu e está
refutada logo abaixo. Três delas, pela capacidade declarada:
`internal/cerebro/semantica.go:12-14` diz 10.141 vetores / 41,5 MB contra **11.248 / 46 MB**;
a unit do grafo diz 9,7 s e 13.575 nós contra **43,1 s e 79.706**; e
`tools/generate-grafo-juridico` diz que a aresta `aplica` não é populada quando há **22.789**.

> **Correção de 2026-09-16 (tarde), e ela é a própria R13 aplicada a esta seção.** A redação
> da manhã listava uma quarta divergência — *"`internal/cerebro/coleta.go:29` afirma 360.619
> bytes e o real é 26.704.470 (74×, e a folga do teto de 64 MiB caiu de 178× para 2,5×)"* —
> e ela **está errada em duas camadas**, o que a torna melhor exemplo do que era antes.
>
> **O caminho não existe:** não há `internal/cerebro/coleta.go`; o símbolo mora em
> `internal/stjacordaos/coleta.go:38` (`LimiteArquivoMensal = 64 << 20`). Citar arquivo:linha
> sem `grep` é o defeito que a R1 nomeia, e ele atravessou a sessão inteira porque o número
> ao lado parecia plausível.
>
> **E a grandeza está trocada:** `LimiteArquivoMensal` limita **um corpo HTTP** — um dataset,
> uma competência —, não o JSONL agregado do corpus. Os 26.704.470 bytes são de
> `data/corpus/jurisprudencia/stj-espelhos/registros-2026-06.jsonl`, que **agrega todos os
> datasets do mês** e é maior por construção. O próprio comentário do código avisa:
> *"NAO confunda com os registros-AAAA-MM.jsonl do corpus […] comparar um deles com este teto
> compara coisas diferentes."*
>
> **Medido em 2026-09-16** sobre as 391 linhas `"tipo":"mensal"` de
> `data/corpus/jurisprudencia/stj-espelhos/censo-20260915/sizes.jsonl`: o maior corpo mensal
> real é **14.442.367 bytes** (competência 20260630), e a folga sobre 64 MiB é **4,65×**.
> **O teto fica.** Não havia folga de 2,5× e não havia o que corrigir no código — havia um
> número meu comparando duas coisas diferentes, que é exatamente o que a R13 manda medir antes
> de publicar.

```bash
python3 -c "
import json
mensais=[json.loads(l) for l in open('data/corpus/jurisprudencia/stj-espelhos/censo-20260915/sizes.jsonl')]
mx=max(d['bytes'] for d in mensais if d.get('tipo')=='mensal')
print('maior corpo mensal', mx, '| folga sobre 64 MiB: %.2fx' % ((64<<20)/mx))
"
```

E o corolário que fecha a regra: **nunca calibrar um instrumento contra a própria
expectativa.** Mede-se, e o controle vem de fora. Replicação que bate com o número esperado é
motivo para desconfiar dela, não para publicá-la — o caso que originou isto (número **5,3×**
inflado, com dois agentes reproduzindo o mesmo filtro errado) está em
`docs/PRECEDENTES_DAS_ORDENS.md`.

> **Nota de cobertura — aberta e FECHADA em 2026-09-16.** Pela manhã, R11, R12 e R13 foram
> escritas aqui e **não** entraram em `contratoDadoRealRegras`: o gate cobrava dez de treze, e
> apagar qualquer uma das três não reprovava nada. À tarde a lacuna foi fechada — as três
> estão na slice, o comentário do arquivo diz treze, e
> `internal/checks/contrato_dado_real_gate_test.go` passou a **derivar o conjunto esperado
> deste documento**, de modo que regra nova que não entre na slice fica vermelha na primeira
> execução. Provado por mutação: tirar R11 da slice ⇒ `regra_sem_executor: … enuncia R11 e
> contratoDadoRealRegras não cobra`.
>
> **E a nota da manhã tinha um defeito que o teste de mutação revelou.** Ela citava os rótulos
> de R1 e de R10 na forma literal, entre crases. O gate procurava o rótulo com
> `strings.Contains` sobre o arquivo inteiro, então **a citação em prosa satisfazia a busca**:
> com esta nota no documento, apagar o título de R1 deixava o gate **verde**. A causa foi
> corrigida onde ela mora — `enunciaRegraComoTitulo` agora exige o rótulo no **começo da
> linha**, como título de verdade, e prosa nenhuma responde por regra. Documento que explica o
> gate não pode, ao explicá-lo, satisfazê-lo.

---

## 3. Como este contrato é lembrado (mecanismo, não boa vontade)

1. **`CLAUDE.md`** — o bloco de leitura obrigatória do topo cita este arquivo pelo
   nome; nenhuma sessão começa a agir em `/goal` sem passar por ele.
2. **Memória persistente** — `~/.claude/projects/-opt-wiki/memory/contrato-dado-real.md`
   com ponteiro em `MEMORY.md`, carregada em toda sessão nova.
3. **Check executável** — `./tools/go-modern run ./cmd/check contrato-dado-real`
   (implementado em `internal/checks/`) reprova se este arquivo sumir, se o ponteiro
   do `CLAUDE.md` for removido ou se a transcrição da ordem for esvaziada. Um contrato
   que só existe na boa vontade do agente não é contrato — este falha o gate quando é
   esquecido.

---

## 4. Registro de execução

| data | o que foi feito sob este contrato |
|---|---|
| 2026-08-12 | Contrato gravado. Onda de investigação lançada sobre: causa-raiz da queda de rastreio, HTML público (9.838 páginas), sitemap/robots/feed/llms.txt, código Go de serving e SEO, malha de links internos, fontes oficiais 2026 de crawl e IA, infraestrutura (nginx/túnel/systemd) e qualidade do conteúdo jurídico. |
| 2026-09-15/16 | Auditoria do cérebro de IA local. A família ganha **R11** (borda é a autoridade de volume), **R12** (não estreitar o projeto com número pessimista) e **R13** (contrato e comentário são alegação datada) — as regras 15, 16 e 19 do §P0 de `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`. Os casos, com data, número e prejuízo, ficam em `docs/PRECEDENTES_DAS_ORDENS.md`; as armadilhas por arquivo, em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`. |
